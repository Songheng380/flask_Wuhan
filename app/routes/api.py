# app/routes/api.py
from flask import Blueprint, request, jsonify, current_app
from app.models.metro_station import MetroStation
from app import db
from sqlalchemy.exc import OperationalError
import json

api = Blueprint('api', __name__)


# # 属性关键词查询（如“学校”）,现在是只查名字，而且只能查一次，还要改
# @api.route('/api/search')
# def search_poi():
#     keyword = request.args.get('q', '').strip()
#     if not keyword:
#         return jsonify([])
#
#     results = [
#         item for item in POI_DATA
#         if keyword.lower() in item['name'].lower() or keyword.lower() in item['type'].lower()
#     ]
#     return jsonify(results)
#
#
# # 矩形范围查询，还未实现，有误
# @api.route('/api/bbox')
# def bbox_query():
#     try:
#         min_lon = float(request.args.get('min_lon'))
#         min_lat = float(request.args.get('min_lat'))
#         max_lon = float(request.args.get('max_lon'))
#         max_lat = float(request.args.get('max_lat'))
#     except (TypeError, ValueError):
#         return jsonify([])
#
#     results = [
#         item for item in POI_DATA
#         if min_lon <= item['lon'] <= max_lon and min_lat <= item['lat'] <= max_lat
#     ]
#     return jsonify(results)

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

# 根据 gid 查询单个地铁站详情
@api.route('/metro/<int:gid>', methods=['GET'])
def get_metro_by_gid(gid):
    """根据 gid 查询单个地铁站点详情"""
    # 按 gid 查询（主键查询，效率最高）
    station = db.session.query(
        MetroStation.gid,
        MetroStation.name,
        MetroStation.layer,
        db.func.ST_X(MetroStation.geom).label('lon'),
        db.func.ST_Y(MetroStation.geom).label('lat'),
        MetroStation.desc_,  # 站点描述
        MetroStation.style    # 样式字段（如果有用）
    ).filter(MetroStation.gid == gid).first()

    # 处理查询结果：不存在返回 404
    if not station:
        return jsonify({
            "code": 404,
            "msg": f"未找到 gid 为 {gid} 的地铁站点"
        }), 404

    # 转换为 JSON 格式返回（字段更完整）
    return jsonify({
        "code": 200,
        "data": {
            "gid": station.gid,
            "name": station.name,
            "line": station.layer,  # 线路名称（如“轨道交通2号线”）
            "lon": round(station.lon, 6),  # 经度（保留6位小数，更精确）
            "lat": round(station.lat, 6),  # 纬度
            "description": station.desc_ or "无描述",  # 描述（为空时显示默认值）
            "style": station.style or "无"  # 样式字段（可选）
        }
    }), 200