from flask import Blueprint, request, jsonify, current_app
from app import db
from sqlalchemy.exc import OperationalError
import json
import os
from pathlib import Path
from geoalchemy2 import Geometry
from sqlalchemy import func, String, or_

# 数据模型
from app.models.metro_station import MetroStation
from app.models.metro_line import MetroLine
from app.models.metro_10min_wait_circle import Metro10minWaitCircle
from app.models.public_services import PublicServices
from app.models.wuhan_middle_school import WuhanMiddleSchool
from app.models.wuhan_primary_school import WuhanPrimarySchool

# 数据库矢量图层配置：模型 -> 前端显示名 -> 属性字段 -> 坐标回退字段
DB_LAYERS_CONFIG = {
    '武汉市地铁站点': {
        'model': MetroStation,
        'fields': ['name', 'line', 'color', 'transfer'],
        'coords': ('lon_wgs84', 'lat_wgs84')
    },
        '武汉地铁线路': {  
        'model': MetroLine,
        'fields': ['name', 'layer', 'origin', 'destination'],  
        'coords': None,  
    },
    '地铁十分钟等时圈': {
        'model': Metro10minWaitCircle,
        'fields': ['name', 'aa_mins', 'aa_mode', 'total_pop', 'center_lon', 'center_lat'],
        'coords': None  
    },
    '公共服务': {
        'model': PublicServices,
        'fields': ['name', 'type', 'address', 'category'],
        'coords': ('longitude', 'latitude')
    },
    '武汉市中学': {
        'model': WuhanMiddleSchool,
        'fields': ['name', 'related_address'],
        'coords': ('longitude', 'latitude')
    },
    '武汉市小学': {
        'model': WuhanPrimarySchool,
        'fields': ['name', 'related_address'],
        'coords': ('longitude', 'latitude')
    }

}

api = Blueprint('api', __name__)

# api配置
from app.config import SearchConfig

# 初始化wordvec配置
from app.routes.wordvec import load_chinese_vectors, cosine_similarity, vectorize_text
if SearchConfig.ifWordVec:
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))
    WORD_VECTORS = load_chinese_vectors(os.path.join(BASE_DIR, "./src/sgns.target.word-word.dynwin5.thr10.neg5.dim300.iter5"), max_words=500000)
else:
    WORD_VECTORS = None

# ========================== 矢量与栅格数据处理 ==========================


# 如果 shapefile 缺失 .shx，尝试让 GDAL 自动恢复（优先使用 osgeo.gdal）
try:
    from osgeo import gdal
    gdal.SetConfigOption('SHAPE_RESTORE_SHX', 'YES')
except Exception:
    # 如果没有安装 GDAL Python 绑定，设置环境变量作为备用
    os.environ.setdefault('SHAPE_RESTORE_SHX', 'YES')

def load_db_layer_as_geojson(layer_name):
    """从数据库查询矢量图层并返回 GeoJSON FeatureCollection。
    优先使用 PostGIS 的 ST_AsGeoJSON(ST_Transform(...))，若失败则回退到数值坐标字段（如 lon/lat）。
    """
    if layer_name not in DB_LAYERS_CONFIG:
        return None

    cfg = DB_LAYERS_CONFIG[layer_name]
    model_class = cfg['model']
    fields = cfg.get('fields', [])

    try:
        geom_col = getattr(model_class, 'geometry')
        # 检查表中存在的 SRID
        try:
            srid_rows = db.session.query(func.ST_SRID(geom_col)).distinct().all()
            srids = {r[0] for r in srid_rows if r and r[0] is not None}
        except Exception:
            srids = set()

        # 处理历史遗留 SRID：部分数据在入库时错误使用了 900913/900915，但坐标实际为经纬度（WGS84）
        if 900913 in srids or 900915 in srids:
            # 这些表中的几何看起来已是经纬度（示例 WKT 中为 lon lat），因此直接设置为 4326
            geom_json_expr = func.ST_AsGeoJSON(func.ST_SetSRID(geom_col, 4326)).label('geom_json')
        else:
            # 常规：将几何投影到 4326 再转为 GeoJSON
            geom_json_expr = func.ST_AsGeoJSON(func.ST_Transform(geom_col, 4326)).label('geom_json')

        cols = [geom_json_expr] + [getattr(model_class, f) for f in fields]
        rows = db.session.query(*cols).all()

        features = []
        for row in rows:
            try:
                geom_json_str = row[0]
                if not geom_json_str:
                    continue
                geom_dict = json.loads(geom_json_str)
                properties = {}
                for i, field in enumerate(fields):
                    val = row[i + 1]
                    if val is not None:
                        properties[field] = str(val)
                features.append({'type': 'Feature', 'geometry': geom_dict, 'properties': properties})
            except Exception:
                continue

        return {'type': 'FeatureCollection', 'features': features}

    except Exception as e:
        try:
            db.session.rollback()
        except Exception:
            pass
        # 回退：如果配置了数值坐标字段，则使用这些字段构造 Point
        coord_fields = cfg.get('coords')
        if coord_fields:
            lon_field, lat_field = coord_fields
            try:
                cols2 = [getattr(model_class, f) for f in fields] + [getattr(model_class, lon_field), getattr(model_class, lat_field)]
                rows2 = db.session.query(*cols2).all()
                features = []
                for row in rows2:
                    try:
                        properties = {}
                        for i, field in enumerate(fields):
                            val = row[i]
                            if val is not None:
                                properties[field] = str(val)
                        lon = row[len(fields)]
                        lat = row[len(fields) + 1]
                        if lon is None or lat is None:
                            continue
                        features.append({'type': 'Feature', 'geometry': {'type': 'Point', 'coordinates': [float(lon), float(lat)]}, 'properties': properties})
                    except Exception:
                        continue
                return {'type': 'FeatureCollection', 'features': features}
            except Exception:
                try:
                    db.session.rollback()
                except Exception:
                    pass
                return None
        return None


# ========================== 图层管理 API ==========================
@api.route('/layers', methods=['GET'])
def list_layers():
    """返回所有可用图层的元信息"""
    out = []
    # 仅返回数据库中的矢量图层（不再暴露本地文件图层）
    for layer_name, cfg in DB_LAYERS_CONFIG.items():
        out.append({"name": layer_name, "type": "vector"})
    return jsonify(out)


@api.route('/debug/db-samples', methods=['GET'])
def debug_db_samples():
    """返回每个 DB_LAYERS_CONFIG 表的样例记录：ogc_fid, srid, wkt, 以及回退坐标字段的值（LIMIT 10）。"""
    out = {}
    for layer_name, cfg in DB_LAYERS_CONFIG.items():
        model = cfg.get('model')
        fields = cfg.get('fields', [])
        coord_fields = cfg.get('coords', [])
        try:
            tablename = getattr(model, '__tablename__', None)
            table_args = getattr(model, '__table_args__', {}) or {}
            schema = table_args.get('schema') if isinstance(table_args, dict) else None
            if schema:
                full = f"{schema}.\"{tablename}\""
            else:
                full = f"\"{tablename}\""

            select_cols = ['ogc_fid', 'ST_SRID(geometry) as srid', 'ST_AsText(geometry) as wkt']
            for cf in coord_fields:
                select_cols.append(cf)
            for f in fields:
                # include some property fields for inspection
                select_cols.append(f)

            sql = f"SELECT {', '.join(select_cols)} FROM {full} LIMIT 10;"
            try:
                rows = db.session.execute(db.text(sql)).fetchall()
            except Exception as e:
                try:
                    db.session.rollback()
                except Exception:
                    pass
                out[layer_name] = {'error': str(e)}
                continue

            recs = []
            for r in rows:
                rec = {}
                # columns order: ogc_fid, srid, wkt, coord_fields..., property fields...
                rec['ogc_fid'] = r[0]
                rec['srid'] = r[1]
                rec['wkt'] = r[2]
                idx = 3
                for cf in coord_fields:
                    rec[cf] = r[idx]
                    idx += 1
                for f in fields:
                    try:
                        rec[f] = r[idx]
                    except Exception:
                        rec[f] = None
                    idx += 1
                recs.append(rec)

            out[layer_name] = {'table': f'{schema}.{tablename}' if schema else tablename, 'samples': recs}
        except Exception as e:
            try:
                db.session.rollback()
            except Exception:
                pass
            out[layer_name] = {'error': str(e)}

    return jsonify(out)
@api.route('/geojson/<layer_name>', methods=['GET'])
def get_geojson(layer_name):
    """获取指定矢量图层的 GeoJSON"""
    # 优先从数据库查询矢量图层
    if layer_name in DB_LAYERS_CONFIG:
        geojson = load_db_layer_as_geojson(layer_name)
        if geojson is None:
            return jsonify({}), 500
        return jsonify(geojson)
    return jsonify({}), 404


@api.route('/imagery/<layer_name>', methods=['GET'])
def get_imagery(layer_name):
    """获取指定栅格图层的 URL 和 bounds"""
    
    return jsonify({}), 404


# ========================== POI 数据查询 ==========================

def load_poi_data():
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))
    poi_path = os.path.join(BASE_DIR, "../../data/poi_sample.json")
    poi_path = os.path.normpath(poi_path)
    with open(poi_path, "r", encoding="utf-8") as f:
        return json.load(f)

    
def search_poi(POI_DATA=None, keyword=None, FIELDS=SearchConfig.FIELDS):
    """
    支持三种查询模式：
    1. 精确查询 exact=true
    2. 模糊查询 exact=false
    3. 语义查询 mode=semantic,没继续做
    """
    if SearchConfig.DEBUG_POI_SEARCH:
        POI_DATA = load_poi_data()

    keyword = request.args.get("q", "").strip().lower()
    if not keyword:
        return jsonify([])

    exact = request.args.get("exact", "false").lower() == "true"
    mode = request.args.get("mode", "text").lower()  # text / semantic

    if mode == "semantic":
        print("✅ 进行语义查询")
        query_vector = vectorize_text(keyword, word_vectors=WORD_VECTORS)
        if query_vector is None:
            return jsonify([])

        results = []
        for item in POI_DATA:
            # 简单将POI名字拼成字符列表进行平均向量
            item_text = "".join([str(item.get(field, "")) for field in FIELDS])
            item_vector = vectorize_text(item_text, word_vectors=WORD_VECTORS)
            if item_vector is None:
                continue
            sim = cosine_similarity(query_vector, item_vector)
            results.append((sim, item))
        # 按相似度排序
        results.sort(key=lambda x: x[0], reverse=True)
        results = [x[1] for x in results[:SearchConfig.searchListNum]]  # 可选：返回前10条
    else:
        if exact:
            print("✅ 进行精确查询")
            results = [
                item for item in POI_DATA
                if any(keyword == str(item.get(field, "")).lower() for field in FIELDS)
            ]
        else:
            print("✅ 进行模糊查询")
            results = [
                item for item in POI_DATA
                if any(keyword in str(item.get(field, "")).lower() for field in FIELDS)
            ]

    return jsonify(results)


# ========================== 矢量图层中的查询接口 ==========================
@api.route('/search-layer', methods=['GET'])
def search_layer():
    """
    在指定矢量图层中查询
    参数：
    - layer: 图层名称
    - q: 关键词
    - exact: 是否精确查询（默认模糊）
    """
    layer_name = request.args.get('layer', '').strip()
    keyword = request.args.get('q', '').strip().lower()
    exact = request.args.get('exact', 'false').lower() == 'true'
    
    if not layer_name or not keyword:
        return jsonify([]), 400
    
    # 如果是数据库矢量图层，通过 SQLAlchemy 在数据库中过滤查询
    if layer_name in DB_LAYERS_CONFIG:
        cfg = DB_LAYERS_CONFIG[layer_name]
        model_class = cfg['model']
        fields = cfg.get('fields', [])

        # 构建几何 JSON 表达式（尝试投影到 4326）
        # 在 search 时也先检测 SRID，避免对错误 SRID 做不当 Transform
        try:
            geom_col = getattr(model_class, 'geometry')
            try:
                srid_rows = db.session.query(func.ST_SRID(geom_col)).distinct().all()
                srids = {r[0] for r in srid_rows if r and r[0] is not None}
            except Exception:
                srids = set()

            if 900913 in srids or 900915 in srids:
                geom_expr = func.ST_AsGeoJSON(func.ST_SetSRID(geom_col, 4326)).label('geom_json')
            else:
                geom_expr = func.ST_AsGeoJSON(func.ST_Transform(geom_col, 4326)).label('geom_json')
        except Exception:
            geom_expr = func.ST_AsGeoJSON(getattr(model_class, 'geometry')).label('geom_json')

        cols = [geom_expr] + [getattr(model_class, f) for f in fields]

        # 构建关键词过滤条件（对任意字段做 ilike / 相等匹配）
        kw = keyword.lower()
        conds = []
        for f in fields:
            col = getattr(model_class, f)
            try:
                if exact:
                    conds.append(func.lower(col.cast(String)) == kw)
                else:
                    conds.append(func.lower(col.cast(String)).like(f"%{kw}%"))
            except Exception:
                # 忽略无法 cast/比较的字段
                continue

        if not conds:
            return jsonify([])

        try:
            q = db.session.query(*cols).filter(or_(*conds)).limit(500)
            rows = q.all()
            features = []
            for row in rows:
                try:
                    geom_json_str = row[0]
                    if not geom_json_str:
                        continue
                    geom_dict = json.loads(geom_json_str)
                    props = {}
                    for i, f in enumerate(fields):
                        v = row[i + 1]
                        if v is not None:
                            props[f] = str(v)
                    features.append({'type': 'Feature', 'geometry': geom_dict, 'properties': props})
                except Exception:
                    continue
            return jsonify(features)
        except Exception as e:
            try:
                db.session.rollback()
            except Exception:
                pass
            # 回退到使用数值坐标字段（如果配置了 coords）
            coord_fields = cfg.get('coords')
            if coord_fields:
                lon_field, lat_field = coord_fields
                try:
                    cols2 = [getattr(model_class, f) for f in fields] + [getattr(model_class, lon_field), getattr(model_class, lat_field)]
                    rows2 = db.session.query(*cols2).filter(or_(*conds)).limit(500).all()
                    features = []
                    for row in rows2:
                        try:
                            props = {}
                            for i, f in enumerate(fields):
                                v = row[i]
                                if v is not None:
                                    props[f] = str(v)
                            lon = row[len(fields)]
                            lat = row[len(fields) + 1]
                            if lon is None or lat is None:
                                continue
                            features.append({'type': 'Feature', 'geometry': {'type': 'Point', 'coordinates': [float(lon), float(lat)]}, 'properties': props})
                        except Exception:
                            continue
                    return jsonify(features)
                except Exception:
                    try:
                        db.session.rollback()
                    except Exception:
                        pass
                    return jsonify([]), 500
            return jsonify([]), 500

    return jsonify({"error": "Layer not found or not a vector layer"}), 404
    
# 接收矩形框参数
def get_bbox_params():
    """
    从请求中接收矩形框四个坐标
    返回:
        min_lon, min_lat, max_lon, max_lat (float)
        如果参数缺失或错误，返回 None
    """
    try:
        min_lon = float(request.args.get('min_lon'))
        min_lat = float(request.args.get('min_lat'))
        max_lon = float(request.args.get('max_lon'))
        max_lat = float(request.args.get('max_lat'))
        print(f"✅ 收到矩形坐标: min_lon={min_lon}, min_lat={min_lat}, max_lon={max_lon}, max_lat={max_lat}")
        return min_lon, min_lat, max_lon, max_lat
    except (TypeError, ValueError):
        return None
    

# 矩形范围查询
@api.route('/search')
def bbox_query():
    # 加载 POI 测试数据
    POI_DATA = load_poi_data() if SearchConfig.DEBUG else []

    # 获取矩形范围
    coords = get_bbox_params()
    print(coords)
    if coords:
        print("✅ 进行矩形范围过滤")
        min_lon, min_lat, max_lon, max_lat = coords
        filtered = [
            item for item in POI_DATA
            if min_lon <= item.get("lon", 9999) <= max_lon
            and min_lat <= item.get("lat", 9999) <= max_lat
        ]
    else:
        filtered = POI_DATA

    # 关键字搜索
    keyword = request.args.get("q", "").strip().lower()
    result = search_poi(POI_DATA=filtered, keyword=keyword, FIELDS=SearchConfig.FIELDS)

    return result


@api.route('/test_db', methods=['GET'])
def test_db_connection():
    """测试数据库连接状态（显示原始错误+中文提示）"""
    try:
        # 轻量查询验证连接
        db.session.execute(db.text("SELECT 1"))
        db.session.commit()

        response_data = {
            "code": 200,
            "msg": "数据库连接成功！",
            "raw_error": None
        }
        response = current_app.response_class(
            response=json.dumps(response_data, ensure_ascii=False, indent=2),
            status=200,
            mimetype='application/json; charset=utf-8'
        )
        return response

    except OperationalError as e:
        raw_error = str(e)  # 原始错误信息（未转义，保留完整上下文）
        # 中文提示
        if "could not translate host name" in raw_error:
            detail = "主机名无法解析（域名错误/网络不通）"
        elif "connection refused" in raw_error:
            detail = "端口未开放（防火墙/PostgreSQL未启动）"
        elif "password authentication failed" in raw_error:
            detail = "用户名/密码错误"
        elif "database does not exist" in raw_error:
            detail = "数据库不存在"
        else:
            detail = "数据库连接失败"

        response_data = {
            "code": 500,
            "msg": detail,
            "raw_error": raw_error,  # 显示原始错误（如主机名解析失败的完整信息）
            "detail": "请检查：1. 数据库URL中的主机名是否正确 2. 网络是否能访问该主机 3. 服务器防火墙是否开放端口"
        }
        response = current_app.response_class(
            response=json.dumps(response_data, ensure_ascii=False, indent=2),
            status=500,
            mimetype='application/json; charset=utf-8'
        )
        return response

    except Exception as e:
        raw_error = str(e)
        response_data = {
            "code": 500,
            "msg": "未知错误",
            "raw_error": raw_error,
            "detail": "请检查代码或服务器环境"
        }
        response = current_app.response_class(
            response=json.dumps(response_data, ensure_ascii=False, indent=2),
            status=500,
            mimetype='application/json; charset=utf-8'
        )
        return response