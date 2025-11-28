# app/routes/api.py
from flask import Blueprint, request, jsonify, current_app
from app import db
from sqlalchemy.exc import OperationalError
import json
from geoalchemy2 import Geometry
from sqlalchemy import func
import json
import os


# 数据模型
from app.models.metro_station import MetroStation
from app.models.public_services import PublicServices
from app.models.wuhan_middle_school import WuhanMiddleSchool
from app.models.wuhan_primary_school import WuhanPrimarySchool

api = Blueprint('api', __name__)

# api配置
from app.config import SearchConfig

# # 属性关键词查询（如“学校”、“商业”）

def load_poi_data():
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))
    poi_path = os.path.join(BASE_DIR, "../../data/poi_sample.json")
    poi_path = os.path.normpath(poi_path)
    with open(poi_path, "r", encoding="utf-8") as f:
        return json.load(f)


def search_poi(POI_DATA=None, keyword=None, FIELDS = SearchConfig.FIELDS):
    """
    POI查询接口，支持按名称和类型关键词搜索
    参数：
        sample: 是否加载示例数据（仅用于测试）
    输出：
        符合关键词的POI列表，JSON格式
    """
    if SearchConfig.DEBUG:
        POI_DATA = load_poi_data()
        keyword = request.args.get("q", "").strip()
    if not keyword:
        return jsonify([])

    results = [
        item for item in POI_DATA
        if any(keyword in item.get(field, "").lower() for field in FIELDS)
    ]
    
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

def bbox_query():
    # 加载 POI 测试数据
    POI_DATA = load_poi_data() if SearchConfig.DEBUG else []

    # 获取矩形范围
    coords = get_bbox_params()
    if coords:
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
    if keyword:
        filtered = [
            item for item in filtered
            if keyword in item.get("name", "").lower()
            or keyword in item.get("type", "").lower()
            or keyword in item.get("district", "").lower()
        ]

    return jsonify(filtered)

@api.route('/search')
def search_handler():
    if SearchConfig.DEBUG_POI_SERACH:
        return search_poi()
    else:
        return bbox_query()

@api.route('/test-db', methods=['GET'])
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

# -------------------------- Public Services 接口 --------------------------
@api.route('/publicservices/search', methods=['GET'])
def publicservices_search():
    keyword = request.args.get('q', '').strip().lower()
    page = request.args.get('page', 1, type=int)
    page_size = request.args.get('pageSize', 15, type=int)
    offset = (page - 1) * page_size

    query = db.session.query(
        PublicServices.fid, PublicServices.name, PublicServices.type,
        PublicServices.address, PublicServices.longitude, PublicServices.latitude,
        PublicServices.category
    )
    if keyword:
        query = query.filter(
            (func.lower(PublicServices.name).ilike(f'%{keyword}%')) |
            (func.lower(PublicServices.type).ilike(f'%{keyword}%')) |
            (func.lower(PublicServices.address).ilike(f'%{keyword}%'))
        )

    total = query.count()
    results = query.limit(page_size).offset(offset).all()

    data_list = [
        {
            "fid": item.fid,
            "name": item.name,
            "type": item.type,
            "address": item.address,
            "longitude": round(float(item.longitude), 6) if item.longitude else None,
            "latitude": round(float(item.latitude), 6) if item.latitude else None,
            "category": item.category
        } for item in results
    ]
    return jsonify({"data": data_list, "total": total, "page": page, "pageSize": page_size})


@api.route('/publicservices/<int:fid>', methods=['GET'])
def publicservices_get(fid):
    item = PublicServices.query.get(fid)
    if not item:
        return jsonify({"code": 404, "msg": f"Not found public service with fid={fid}"}), 404
    return jsonify({
        "code": 200,
        "data": {
            "fid": item.fid,
            "name": item.name,
            "type": item.type,
            "address": item.address,
            "longitude": float(item.longitude) if item.longitude else None,
            "latitude": float(item.latitude) if item.latitude else None,
            "category": item.category,
            "gridcode": item.gridcode,
            "typecode": item.typecode
        }
    })


@api.route('/publicservices', methods=['POST'])
def publicservices_add():
    data = request.get_json()
    required = ['name', 'type', 'longitude', 'latitude']
    if not all(k in data for k in required):
        return jsonify({"code": 400, "msg": "Missing required fields (name/type/longitude/latitude)"}), 400

    try:
        lon = float(data['longitude'])
        lat = float(data['latitude'])
        # 空间函数正常使用：func 从 sqlalchemy 导入，兼容 geoalchemy2 空间函数
        geometry = func.ST_SetSRID(func.ST_MakePoint(lon, lat), 4326)

        new_item = PublicServices(
            name=data['name'],
            type=data['type'],
            address=data.get('address'),
            longitude=lon,
            latitude=lat,
            category=data.get('category'),
            gridcode=data.get('gridcode'),
            typecode=data.get('typecode'),
            geometry=geometry
        )
        db.session.add(new_item)
        db.session.commit()
        return jsonify({"code": 200, "msg": "Add public service successfully", "data": {"fid": new_item.fid}})
    except Exception as e:
        db.session.rollback()
        return jsonify({"code": 500, "msg": f"Failed to add public service: {str(e)}"}), 500


@api.route('/publicservices/<int:fid>', methods=['PUT'])
def publicservices_update(fid):
    item = PublicServices.query.get(fid)
    if not item:
        return jsonify({"code": 404, "msg": "Public service not found"}), 404
    data = request.get_json()

    try:
        item.name = data.get('name', item.name)
        item.type = data.get('type', item.type)
        item.address = data.get('address', item.address)
        if 'longitude' in data and 'latitude' in data:
            lon = float(data['longitude'])
            lat = float(data['latitude'])
            item.longitude = lon
            item.latitude = lat
            item.geometry = func.ST_SetSRID(func.ST_MakePoint(lon, lat), 4326)
        db.session.commit()
        return jsonify({"code": 200, "msg": "Update public service successfully"})
    except Exception as e:
        db.session.rollback()
        return jsonify({"code": 500, "msg": f"Failed to update public service: {str(e)}"}), 500


@api.route('/publicservices/<int:fid>', methods=['DELETE'])
def publicservices_delete(fid):
    item = PublicServices.query.get(fid)
    if not item:
        return jsonify({"code": 404, "msg": "Public service not found"}), 404
    try:
        db.session.delete(item)
        db.session.commit()
        return jsonify({"code": 200, "msg": "Delete public service successfully"})
    except Exception as e:
        db.session.rollback()
        return jsonify({"code": 500, "msg": f"Failed to delete public service: {str(e)}"}), 500


# -------------------------- Wuhan Metro Stations 接口 --------------------------
@api.route('/wuhanmetro/search', methods=['GET'])
def wuhanmetro_search():
    keyword = request.args.get('q', '').strip().lower()
    page = request.args.get('page', 1, type=int)
    page_size = request.args.get('pageSize', 15, type=int)
    offset = (page - 1) * page_size

    query = db.session.query(
        MetroStation.ogc_fid, MetroStation.name, MetroStation.line,
        MetroStation.color, MetroStation.lon_wgs84, MetroStation.lat_wgs84,
        MetroStation.transfer
    )
    if keyword:
        query = query.filter(
            (func.lower(MetroStation.name).ilike(f'%{keyword}%')) |
            (func.lower(MetroStation.line).ilike(f'%{keyword}%'))
        )

    total = query.count()
    results = query.limit(page_size).offset(offset).all()

    data_list = [
        {
            "ogc_fid": item.ogc_fid,
            "name": item.name,
            "line": item.line,
            "color": item.color,
            "lon_wgs84": round(float(item.lon_wgs84), 6) if item.lon_wgs84 else None,
            "lat_wgs84": round(float(item.lat_wgs84), 6) if item.lat_wgs84 else None,
            "transfer": item.transfer
        } for item in results
    ]
    return jsonify({"data": data_list, "total": total, "page": page, "pageSize": page_size})


@api.route('/wuhanmetro/<int:ogc_fid>', methods=['GET'])
def wuhanmetro_get(ogc_fid):
    item = MetroStation.query.get(ogc_fid)
    if not item:
        return jsonify({"code": 404, "msg": f"Not found metro station with ID={ogc_fid}"}), 404
    return jsonify({
        "code": 200,
        "data": {
            "ogc_fid": item.ogc_fid,
            "name": item.name,
            "line": item.line,
            "color": item.color,
            "lon_wgs84": float(item.lon_wgs84) if item.lon_wgs84 else None,
            "lat_wgs84": float(item.lat_wgs84) if item.lat_wgs84 else None,
            "transfer": item.transfer
        }
    })


@api.route('/wuhanmetro', methods=['POST'])
def wuhanmetro_add():
    data = request.get_json()
    required = ['name', 'line', 'lon_wgs84', 'lat_wgs84']
    if not all(k in data for k in required):
        return jsonify({"code": 400, "msg": "Missing required fields (name/line/lon_wgs84/lat_wgs84)"}), 400

    try:
        lon = float(data['lon_wgs84'])
        lat = float(data['lat_wgs84'])
        geometry = func.ST_SetSRID(func.ST_MakePoint(lon, lat), 4326)

        new_item = MetroStation(
            name=data['name'],
            line=data['line'],
            color=data.get('color'),
            lon_wgs84=lon,
            lat_wgs84=lat,
            transfer=data.get('transfer'),
            geometry=geometry
        )
        db.session.add(new_item)
        db.session.commit()
        return jsonify({"code": 200, "msg": "Add metro station successfully", "data": {"ogc_fid": new_item.ogc_fid}})
    except Exception as e:
        db.session.rollback()
        return jsonify({"code": 500, "msg": f"Failed to add metro station: {str(e)}"}), 500


@api.route('/wuhanmetro/<int:ogc_fid>', methods=['PUT'])
def wuhanmetro_update(ogc_fid):
    item = MetroStation.query.get(ogc_fid)
    if not item:
        return jsonify({"code": 404, "msg": "Metro station not found"}), 404
    data = request.get_json()

    try:
        item.name = data.get('name', item.name)
        item.line = data.get('line', item.line)
        item.color = data.get('color', item.color)
        item.transfer = data.get('transfer', item.transfer)
        if 'lon_wgs84' in data and 'lat_wgs84' in data:
            lon = float(data['lon_wgs84'])
            lat = float(data['lat_wgs84'])
            item.lon_wgs84 = lon
            item.lat_wgs84 = lat
            item.geometry = func.ST_SetSRID(func.ST_MakePoint(lon, lat), 4326)
        db.session.commit()
        return jsonify({"code": 200, "msg": "Update metro station successfully"})
    except Exception as e:
        db.session.rollback()
        return jsonify({"code": 500, "msg": f"Failed to update metro station: {str(e)}"}), 500


@api.route('/wuhanmetro/<int:ogc_fid>', methods=['DELETE'])
def wuhanmetro_delete(ogc_fid):
    item = MetroStation.query.get(ogc_fid)
    if not item:
        return jsonify({"code": 404, "msg": "Metro station not found"}), 404
    try:
        db.session.delete(item)
        db.session.commit()
        return jsonify({"code": 200, "msg": "Delete metro station successfully"})
    except Exception as e:
        db.session.rollback()
        return jsonify({"code": 500, "msg": f"Failed to delete metro station: {str(e)}"}), 500


# -------------------------- Wuhan Middle Schools 接口 --------------------------
@api.route('/wuhanmiddleschool/search', methods=['GET'])
def wuhanmiddleschool_search():
    keyword = request.args.get('q', '').strip().lower()
    page = request.args.get('page', 1, type=int)
    page_size = request.args.get('pageSize', 15, type=int)
    offset = (page - 1) * page_size

    query = db.session.query(
        WuhanMiddleSchool.ogc_fid, WuhanMiddleSchool.name, WuhanMiddleSchool.related_address,
        WuhanMiddleSchool.x_transfer, WuhanMiddleSchool.y_transfer
    )
    if keyword:
        query = query.filter(
            (func.lower(WuhanMiddleSchool.name).ilike(f'%{keyword}%')) |
            (func.lower(WuhanMiddleSchool.related_address).ilike(f'%{keyword}%'))
        )

    total = query.count()
    results = query.limit(page_size).offset(offset).all()

    data_list = [
        {
            "ogc_fid": item.ogc_fid,
            "name": item.name,
            "related_address": item.related_address,
            "x_transfer": round(float(item.x_transfer), 6) if item.x_transfer else None,
            "y_transfer": round(float(item.y_transfer), 6) if item.y_transfer else None
        } for item in results
    ]
    return jsonify({"data": data_list, "total": total, "page": page, "pageSize": page_size})


@api.route('/wuhanmiddleschool/<int:ogc_fid>', methods=['GET'])
def wuhanmiddleschool_get(ogc_fid):
    item = WuhanMiddleSchool.query.get(ogc_fid)
    if not item:
        return jsonify({"code": 404, "msg": f"Not found middle school with ID={ogc_fid}"}), 404
    return jsonify({
        "code": 200,
        "data": {
            "ogc_fid": item.ogc_fid,
            "name": item.name,
            "related_address": item.related_address,
            "x_transfer": float(item.x_transfer) if item.x_transfer else None,
            "y_transfer": float(item.y_transfer) if item.y_transfer else None
        }
    })


@api.route('/wuhanmiddleschool', methods=['POST'])
def wuhanmiddleschool_add():
    data = request.get_json()
    required = ['name', 'x_transfer', 'y_transfer']
    if not all(k in data for k in required):
        return jsonify({"code": 400, "msg": "Missing required fields (name/x_transfer/y_transfer)"}), 400

    try:
        x = float(data['x_transfer'])
        y = float(data['y_transfer'])
        geometry = func.ST_SetSRID(func.ST_MakePoint(x, y), 4326)

        new_item = WuhanMiddleSchool(
            name=data['name'],
            related_address=data.get('related_address'),
            x_transfer=x,
            y_transfer=y,
            geometry=geometry
        )
        db.session.add(new_item)
        db.session.commit()
        return jsonify({"code": 200, "msg": "Add middle school successfully", "data": {"ogc_fid": new_item.ogc_fid}})
    except Exception as e:
        db.session.rollback()
        return jsonify({"code": 500, "msg": f"Failed to add middle school: {str(e)}"}), 500


@api.route('/wuhanmiddleschool/<int:ogc_fid>', methods=['PUT'])
def wuhanmiddleschool_update(ogc_fid):
    item = WuhanMiddleSchool.query.get(ogc_fid)
    if not item:
        return jsonify({"code": 404, "msg": "Middle school not found"}), 404
    data = request.get_json()

    try:
        item.name = data.get('name', item.name)
        item.related_address = data.get('related_address', item.related_address)
        if 'x_transfer' in data and 'y_transfer' in data:
            x = float(data['x_transfer'])
            y = float(data['y_transfer'])
            item.x_transfer = x
            item.y_transfer = y
            item.geometry = func.ST_SetSRID(func.ST_MakePoint(x, y), 4326)
        db.session.commit()
        return jsonify({"code": 200, "msg": "Update middle school successfully"})
    except Exception as e:
        db.session.rollback()
        return jsonify({"code": 500, "msg": f"Failed to update middle school: {str(e)}"}), 500


@api.route('/wuhanmiddleschool/<int:ogc_fid>', methods=['DELETE'])
def wuhanmiddleschool_delete(ogc_fid):
    item = WuhanMiddleSchool.query.get(ogc_fid)
    if not item:
        return jsonify({"code": 404, "msg": "Middle school not found"}), 404
    try:
        db.session.delete(item)
        db.session.commit()
        return jsonify({"code": 200, "msg": "Delete middle school successfully"})
    except Exception as e:
        db.session.rollback()
        return jsonify({"code": 500, "msg": f"Failed to delete middle school: {str(e)}"}), 500


# -------------------------- Wuhan Primary Schools 接口 --------------------------
@api.route('/wuhanprimaryschool/search', methods=['GET'])
def wuhanprimaryschool_search():
    keyword = request.args.get('q', '').strip().lower()
    page = request.args.get('page', 1, type=int)
    page_size = request.args.get('pageSize', 15, type=int)
    offset = (page - 1) * page_size

    query = db.session.query(
        WuhanPrimarySchool.ogc_fid, WuhanPrimarySchool.name, WuhanPrimarySchool.related_address,
        WuhanPrimarySchool.x_transfer, WuhanPrimarySchool.y_transfer
    )
    if keyword:
        query = query.filter(
            (func.lower(WuhanPrimarySchool.name).ilike(f'%{keyword}%')) |
            (func.lower(WuhanPrimarySchool.related_address).ilike(f'%{keyword}%'))
        )

    total = query.count()
    results = query.limit(page_size).offset(offset).all()

    data_list = [
        {
            "ogc_fid": item.ogc_fid,
            "name": item.name,
            "related_address": item.related_address,
            "x_transfer": round(float(item.x_transfer), 6) if item.x_transfer else None,
            "y_transfer": round(float(item.y_transfer), 6) if item.y_transfer else None
        } for item in results
    ]
    return jsonify({"data": data_list, "total": total, "page": page, "pageSize": page_size})


@api.route('/wuhanprimaryschool/<int:ogc_fid>', methods=['GET'])
def wuhanprimaryschool_get(ogc_fid):
    item = WuhanPrimarySchool.query.get(ogc_fid)
    if not item:
        return jsonify({"code": 404, "msg": f"Not found primary school with ID={ogc_fid}"}), 404
    return jsonify({
        "code": 200,
        "data": {
            "ogc_fid": item.ogc_fid,
            "name": item.name,
            "related_address": item.related_address,
            "x_transfer": float(item.x_transfer) if item.x_transfer else None,
            "y_transfer": float(item.y_transfer) if item.y_transfer else None
        }
    })


@api.route('/wuhanprimaryschool', methods=['POST'])
def wuhanprimaryschool_add():
    data = request.get_json()
    required = ['name', 'x_transfer', 'y_transfer']
    if not all(k in data for k in required):
        return jsonify({"code": 400, "msg": "Missing required fields (name/x_transfer/y_transfer)"}), 400

    try:
        x = float(data['x_transfer'])
        y = float(data['y_transfer'])
        geometry = func.ST_SetSRID(func.ST_MakePoint(x, y), 4326)

        new_item = WuhanPrimarySchool(
            name=data['name'],
            related_address=data.get('related_address'),
            x_transfer=x,
            y_transfer=y,
            geometry=geometry
        )
        db.session.add(new_item)
        db.session.commit()
        return jsonify({"code": 200, "msg": "Add primary school successfully", "data": {"ogc_fid": new_item.ogc_fid}})
    except Exception as e:
        db.session.rollback()
        return jsonify({"code": 500, "msg": f"Failed to add primary school: {str(e)}"}), 500


@api.route('/wuhanprimaryschool/<int:ogc_fid>', methods=['PUT'])
def wuhanprimaryschool_update(ogc_fid):
    item = WuhanPrimarySchool.query.get(ogc_fid)
    if not item:
        return jsonify({"code": 404, "msg": "Primary school not found"}), 404
    data = request.get_json()

    try:
        item.name = data.get('name', item.name)
        item.related_address = data.get('related_address', item.related_address)
        if 'x_transfer' in data and 'y_transfer' in data:
            x = float(data['x_transfer'])
            y = float(data['y_transfer'])
            item.x_transfer = x
            item.y_transfer = y
            item.geometry = func.ST_SetSRID(func.ST_MakePoint(x, y), 4326)
        db.session.commit()
        return jsonify({"code": 200, "msg": "Update primary school successfully"})
    except Exception as e:
        db.session.rollback()
        return jsonify({"code": 500, "msg": f"Failed to update primary school: {str(e)}"}), 500


@api.route('/wuhanprimaryschool/<int:ogc_fid>', methods=['DELETE'])
def wuhanprimaryschool_delete(ogc_fid):
    item = WuhanPrimarySchool.query.get(ogc_fid)
    if not item:
        return jsonify({"code": 404, "msg": "Primary school not found"}), 404
    try:
        db.session.delete(item)
        db.session.commit()
        return jsonify({"code": 200, "msg": "Delete primary school successfully"})
    except Exception as e:
        db.session.rollback()
        return jsonify({"code": 500, "msg": f"Failed to delete primary school: {str(e)}"}), 500
