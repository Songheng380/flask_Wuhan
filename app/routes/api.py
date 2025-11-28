from flask import Blueprint, request, jsonify, current_app
from app import db
from sqlalchemy.exc import OperationalError
import json
import os
from pathlib import Path
from geoalchemy2 import Geometry
from sqlalchemy import func

# 数据模型
from app.models.metro_station import MetroStation
from app.models.public_services import PublicServices
from app.models.wuhan_middle_school import WuhanMiddleSchool
from app.models.wuhan_primary_school import WuhanPrimarySchool

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
# 数据目录（指向项目根目录的 data 文件夹）
DATA_DIR = Path(__file__).parent.parent.parent / "data"

# 如果 shapefile 缺失 .shx，尝试让 GDAL 自动恢复（优先使用 osgeo.gdal）
try:
    from osgeo import gdal
    gdal.SetConfigOption('SHAPE_RESTORE_SHX', 'YES')
except Exception:
    # 如果没有安装 GDAL Python 绑定，设置环境变量作为备用
    os.environ.setdefault('SHAPE_RESTORE_SHX', 'YES')

# 扫描并加载矢量（shp 或 geojson）与栅格（tif）文件，启动时只加载一次并缓存
LAYERS = {}


def load_vector(path: Path, name: str):
    """加载矢量文件（shapefile 或 GeoJSON）"""
    try:
        import geopandas as gpd
    except Exception:
        print("geopandas not installed; can't load vector:", path)
        return
    
    # 尝试第一次：禁用 SHAPE_RESTORE_SHX 以避免写入权限问题
    os.environ['SHAPE_RESTORE_SHX'] = 'NO'
    try:
        gdf = gpd.read_file(path)
        # 转为 WGS84（经纬度）以便前端直接使用
        try:
            gdf = gdf.to_crs(epsg=4326)
        except Exception:
            pass
        geojson = json.loads(gdf.to_json())
        LAYERS[name] = {"type": "vector", "geojson": geojson}
        print(f"Loaded vector: {name}")
        os.environ.pop('SHAPE_RESTORE_SHX', None)
        return
    except Exception as e:
        print(f"Failed loading vector {path}: {e}")
        os.environ.pop('SHAPE_RESTORE_SHX', None)


def load_raster(path: Path, name: str):
    """加载栅格文件（GeoTIFF 等）"""
    try:
        import rasterio
        import numpy as np
        from PIL import Image
    except Exception:
        print("rasterio/pillow not installed; can't load raster:", path)
        return
    try:
        with rasterio.open(path) as src:
            bounds = src.bounds  # left, bottom, right, top
            arr = src.read()
            # convert to H x W x C uint8
            if arr.ndim == 3 and arr.shape[0] >= 3:
                img = np.dstack([arr[0], arr[1], arr[2]])
            else:
                # 单波段，做灰度渲染
                band = arr[0]
                # 归一化到 0-255
                mn, mx = band.min(), band.max()
                if mx == mn:
                    img = np.stack([band, band, band], axis=2)
                else:
                    norm = ((band - mn) / (mx - mn) * 255).astype('uint8')
                    img = np.stack([norm, norm, norm], axis=2)
            # 确保 uint8
            if img.dtype != 'uint8':
                img = (255 * (img.astype('float32') / img.max())).clip(0, 255).astype('uint8')

            out_dir = Path(__file__).parent.parent.parent / 'static' / 'imagery'
            out_dir.mkdir(parents=True, exist_ok=True)
            out_png = out_dir / f"{name}.png"
            Image.fromarray(img).save(out_png)

            LAYERS[name] = {
                "type": "raster",
                "url": f"/static/imagery/{name}.png",
                # Leaflet expects bounds as [[south, west],[north, east]]
                "bounds": [[bounds.bottom, bounds.left], [bounds.top, bounds.right]]
            }
            print(f"Loaded raster: {name}")
    except Exception as e:
        print(f"Failed loading raster {path}: {e}")


# 启动时扫描 data 目录下的 shp / geojson / tif 文件
if DATA_DIR.exists():
    for p in DATA_DIR.rglob('*'):
        if p.suffix.lower() in ('.shp', '.geojson', '.json'):
            name = p.stem
            load_vector(p, name)
        elif p.suffix.lower() in ('.tif', '.tiff'):
            name = p.stem
            load_raster(p, name)


# ========================== 图层管理 API ==========================
@api.route('/layers', methods=['GET'])
def list_layers():
    """返回所有可用图层的元信息"""
    out = []
    for name, info in LAYERS.items():
        entry = {"name": name, "type": info.get('type')}
        if info.get('type') == 'raster':
            entry['bounds'] = info.get('bounds')
            entry['url'] = info.get('url')
        out.append(entry)
    return jsonify(out)


@api.route('/geojson/<layer_name>', methods=['GET'])
def get_geojson(layer_name):
    """获取指定矢量图层的 GeoJSON"""
    info = LAYERS.get(layer_name)
    if not info or info.get('type') != 'vector':
        return jsonify({}), 404
    return jsonify(info.get('geojson'))


@api.route('/imagery/<layer_name>', methods=['GET'])
def get_imagery(layer_name):
    """获取指定栅格图层的 URL 和 bounds"""
    info = LAYERS.get(layer_name)
    if not info or info.get('type') != 'raster':
        return jsonify({}), 404
    return jsonify({
        'url': info.get('url'),
        'bounds': info.get('bounds')
    })


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
    3. 语义查询 mode=semantic
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
    
    # 获取图层数据
    info = LAYERS.get(layer_name)
    if not info or info.get('type') != 'vector':
        return jsonify({"error": "Layer not found or not a vector layer"}), 404
    
    geojson = info.get('geojson', {})
    features = geojson.get('features', [])
    
    # 执行查询
    results = []
    for feature in features:
        if not feature.get('properties'):
            continue
        props = feature.properties
        
        # 在所有属性中查找匹配
        matched = False
        if exact:
            matched = any(keyword == str(props.get(k, '')).lower() for k in props)
        else:
            matched = any(keyword in str(props.get(k, '')).lower() for k in props)
        
        if matched:
            results.append(feature)
    
    return jsonify(results)
    
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