# app/routes/admin.py
from flask import Blueprint, request, jsonify
from app import db
from app.models.wuhan_middle_school import WuhanMiddleSchool
from sqlalchemy import func

# 数据模型导入
from app.models.metro_station import MetroStation
from app.models.metro_line import MetroLine
from app.models.metro_10min_wait_circle import Metro10minWaitCircle
from app.models.public_services import PublicServices
from app.models.wuhan_middle_school import WuhanMiddleSchool
from app.models.wuhan_primary_school import WuhanPrimarySchool

# 创建蓝图
admin = Blueprint('admin', __name__)

"""
-------------------------- 公共服务POI接口 --------------------------
"""


@admin.route('/publicservices/search', methods=['GET'])
def publicservices_search():
    """搜索公共服务数据"""
    keyword = request.args.get('q', '').strip().lower()
    page = request.args.get('page', 1, type=int)
    page_size = request.args.get('pageSize', 15, type=int)
    offset = (page - 1) * page_size

    # 基础查询
    query = db.session.query(
        PublicServices.fid, PublicServices.name, PublicServices.type,
        PublicServices.address, PublicServices.longitude, PublicServices.latitude,
        PublicServices.category
    )

    # 关键词过滤
    if keyword:
        query = query.filter(
            (func.lower(PublicServices.name).ilike(f'%{keyword}%')) |
            (func.lower(PublicServices.type).ilike(f'%{keyword}%')) |
            (func.lower(PublicServices.address).ilike(f'%{keyword}%'))
        )

    # 分页查询
    total = query.count()
    results = query.limit(page_size).offset(offset).all()

    # 格式化返回数据
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

    return jsonify({
        "data": data_list,
        "total": total,
        "page": page,
        "pageSize": page_size
    })


@admin.route('/publicservices/get', methods=['GET'])
def publicservices_get():
    """获取单个公共服务数据"""
    fid = request.args.get('id', type=int)
    if not fid:
        return jsonify({"code": 400, "msg": "缺少参数：id"}), 400

    item = PublicServices.query.get(fid)
    if not item:
        return jsonify({"code": 404, "msg": f"未找到ID为{fid}的公共服务数据"}), 404

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


@admin.route('/publicservices/add', methods=['POST'])
def publicservices_add():
    """新增公共服务数据"""
    data = request.get_json()
    required_fields = ['name', 'type', 'longitude', 'latitude']
    if not all(field in data for field in required_fields):
        return jsonify({"code": 400, "msg": "缺少必填字段：name/type/longitude/latitude"}), 400

    try:
        # 解析经纬度
        longitude = float(data['longitude'])
        latitude = float(data['latitude'])
        # 创建空间几何对象（WGS84坐标系）
        geometry = func.ST_SetSRID(func.ST_MakePoint(longitude, latitude), 4326)

        # 实例化新数据
        new_item = PublicServices(
            name=data['name'],
            type=data['type'],
            address=data.get('address'),
            longitude=longitude,
            latitude=latitude,
            category=data.get('category'),
            gridcode=data.get('gridcode'),
            typecode=data.get('typecode'),
            geometry=geometry
        )

        # 提交数据库
        db.session.add(new_item)
        db.session.commit()
        return jsonify({
            "code": 200,
            "msg": "新增公共服务数据成功",
            "data": {"fid": new_item.fid}
        })

    except Exception as e:
        db.session.rollback()
        return jsonify({"code": 500, "msg": f"新增失败：{str(e)}"}), 500


@admin.route('/publicservices/update', methods=['POST'])
def publicservices_update():
    """更新公共服务数据"""
    data = request.get_json()
    fid = data.get('fid')
    if not fid:
        return jsonify({"code": 400, "msg": "缺少参数：fid"}), 400

    # 查询数据
    item = PublicServices.query.get(fid)
    if not item:
        return jsonify({"code": 404, "msg": "未找到公共服务数据"}), 404

    try:
        # 更新字段（只更新传入的字段，未传入的保持原数据）
        item.name = data.get('name', item.name)
        item.type = data.get('type', item.type)
        item.address = data.get('address', item.address)
        item.category = data.get('category', item.category)
        item.gridcode = data.get('gridcode', item.gridcode)
        item.typecode = data.get('typecode', item.typecode)

        # 处理经纬度更新（需同时更新geometry）
        if 'longitude' in data and 'latitude' in data:
            longitude = float(data['longitude'])
            latitude = float(data['latitude'])
            item.longitude = longitude
            item.latitude = latitude
            item.geometry = func.ST_SetSRID(func.ST_MakePoint(longitude, latitude), 4326)

        # 提交更新
        db.session.commit()
        return jsonify({"code": 200, "msg": "更新公共服务数据成功"})

    except Exception as e:
        db.session.rollback()
        return jsonify({"code": 500, "msg": f"更新失败：{str(e)}"}), 500


@admin.route('/publicservices/delete', methods=['POST'])
def publicservices_delete():
    """删除公共服务数据"""
    data = request.get_json()
    fid = data.get('fid')
    if not fid:
        return jsonify({"code": 400, "msg": "缺少参数：fid"}), 400

    # 查询数据
    item = PublicServices.query.get(fid)
    if not item:
        return jsonify({"code": 404, "msg": "未找到公共服务数据"}), 404

    try:
        # 删除数据
        db.session.delete(item)
        db.session.commit()
        return jsonify({"code": 200, "msg": "删除公共服务数据成功"})

    except Exception as e:
        db.session.rollback()
        return jsonify({"code": 500, "msg": f"删除失败：{str(e)}"}), 500


"""
-------------------------- 武汉市地铁站点接口 --------------------------
"""


@admin.route('/wuhanmetro/search', methods=['GET'])
def wuhanmetro_search():
    """搜索地铁站点数据"""
    keyword = request.args.get('q', '').strip().lower()
    page = request.args.get('page', 1, type=int)
    page_size = request.args.get('pageSize', 15, type=int)
    offset = (page - 1) * page_size

    # 基础查询
    query = db.session.query(
        MetroStation.ogc_fid, MetroStation.name, MetroStation.line,
        MetroStation.color, MetroStation.lon_wgs84, MetroStation.lat_wgs84,
        MetroStation.transfer
    )

    # 关键词过滤
    if keyword:
        query = query.filter(
            (func.lower(MetroStation.name).ilike(f'%{keyword}%')) |
            (func.lower(MetroStation.line).ilike(f'%{keyword}%'))
        )

    # 分页查询
    total = query.count()
    results = query.limit(page_size).offset(offset).all()

    # 格式化返回数据
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

    return jsonify({
        "data": data_list,
        "total": total,
        "page": page,
        "pageSize": page_size
    })


@admin.route('/wuhanmetro/get', methods=['GET'])
def wuhanmetro_get():
    """获取单个地铁站点数据"""
    ogc_fid = request.args.get('id', type=int)
    if not ogc_fid:
        return jsonify({"code": 400, "msg": "缺少参数：id"}), 400

    item = MetroStation.query.get(ogc_fid)
    if not item:
        return jsonify({"code": 404, "msg": f"未找到ID为{ogc_fid}的地铁站点数据"}), 404

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


@admin.route('/wuhanmetro/add', methods=['POST'])
def wuhanmetro_add():
    """新增地铁站点数据"""
    data = request.get_json()
    required_fields = ['name', 'line', 'lon_wgs84', 'lat_wgs84']
    if not all(field in data for field in required_fields):
        return jsonify({"code": 400, "msg": "缺少必填字段：name/line/lon_wgs84/lat_wgs84"}), 400

    try:
        # 解析经纬度
        lon = float(data['lon_wgs84'])
        lat = float(data['lat_wgs84'])
        # 创建空间几何对象（WGS84坐标系）
        geometry = func.ST_SetSRID(func.ST_MakePoint(lon, lat), 4326)

        # 实例化新数据
        new_item = MetroStation(
            name=data['name'],
            line=data['line'],
            color=data.get('color'),
            lon_wgs84=lon,
            lat_wgs84=lat,
            transfer=data.get('transfer'),
            geometry=geometry
        )

        # 提交数据库
        db.session.add(new_item)
        db.session.commit()
        return jsonify({
            "code": 200,
            "msg": "新增地铁站点数据成功",
            "data": {"ogc_fid": new_item.ogc_fid}
        })

    except Exception as e:
        db.session.rollback()
        return jsonify({"code": 500, "msg": f"新增失败：{str(e)}"}), 500


@admin.route('/wuhanmetro/update', methods=['POST'])
def wuhanmetro_update():
    """更新地铁站点数据"""
    data = request.get_json()
    ogc_fid = data.get('ogc_fid')
    if not ogc_fid:
        return jsonify({"code": 400, "msg": "缺少参数：ogc_fid"}), 400

    # 查询数据
    item = MetroStation.query.get(ogc_fid)
    if not item:
        return jsonify({"code": 404, "msg": "未找到地铁站点数据"}), 404

    try:
        # 更新字段
        item.name = data.get('name', item.name)
        item.line = data.get('line', item.line)
        item.color = data.get('color', item.color)
        item.transfer = data.get('transfer', item.transfer)

        # 处理经纬度更新
        if 'lon_wgs84' in data and 'lat_wgs84' in data:
            lon = float(data['lon_wgs84'])
            lat = float(data['lat_wgs84'])
            item.lon_wgs84 = lon
            item.lat_wgs84 = lat
            item.geometry = func.ST_SetSRID(func.ST_MakePoint(lon, lat), 4326)

        # 提交更新
        db.session.commit()
        return jsonify({"code": 200, "msg": "更新地铁站点数据成功"})

    except Exception as e:
        db.session.rollback()
        return jsonify({"code": 500, "msg": f"更新失败：{str(e)}"}), 500


@admin.route('/wuhanmetro/delete', methods=['POST'])
def wuhanmetro_delete():
    """删除地铁站点数据"""
    data = request.get_json()
    ogc_fid = data.get('ogc_fid')
    if not ogc_fid:
        return jsonify({"code": 400, "msg": "缺少参数：ogc_fid"}), 400

    # 查询数据
    item = MetroStation.query.get(ogc_fid)
    if not item:
        return jsonify({"code": 404, "msg": "未找到地铁站点数据"}), 404

    try:
        # 删除数据
        db.session.delete(item)
        db.session.commit()
        return jsonify({"code": 200, "msg": "删除地铁站点数据成功"})

    except Exception as e:
        db.session.rollback()
        return jsonify({"code": 500, "msg": f"删除失败：{str(e)}"}), 500


"""
-------------------------- 武汉市中学接口 --------------------------
"""


@admin.route('/wuhanmiddleschool/search', methods=['GET'])
def wuhanmiddleschool_search():
    """搜索中学数据"""
    keyword = request.args.get('q', '').strip().lower()
    page = request.args.get('page', 1, type=int)
    page_size = request.args.get('pageSize', 15, type=int)
    offset = (page - 1) * page_size

    # 基础查询
    query = db.session.query(
        WuhanMiddleSchool.ogc_fid, WuhanMiddleSchool.name,
        WuhanMiddleSchool.related_address, WuhanMiddleSchool.longitude,
        WuhanMiddleSchool.latitude
    )

    # 关键词过滤
    if keyword:
        query = query.filter(
            (func.lower(WuhanMiddleSchool.name).ilike(f'%{keyword}%')) |
            (func.lower(WuhanMiddleSchool.related_address).ilike(f'%{keyword}%'))
        )

    # 分页查询
    total = query.count()
    results = query.limit(page_size).offset(offset).all()

    # 格式化返回数据
    data_list = [
        {
            "ogc_fid": item.ogc_fid,
            "name": item.name,
            "related_address": item.related_address,
            "longitude": round(float(item.longitude), 6) if item.longitude else None,
            "latitude": round(float(item.latitude), 6) if item.latitude else None
        } for item in results
    ]

    return jsonify({
        "data": data_list,
        "total": total,
        "page": page,
        "pageSize": page_size
    })


@admin.route('/wuhanmiddleschool/get', methods=['GET'])
def wuhanmiddleschool_get():
    """获取单个中学数据"""
    ogc_fid = request.args.get('id', type=int)
    if not ogc_fid:
        return jsonify({"code": 400, "msg": "缺少参数：id"}), 400

    item = WuhanMiddleSchool.query.get(ogc_fid)
    if not item:
        return jsonify({"code": 404, "msg": f"未找到ID为{ogc_fid}的中学数据"}), 404

    return jsonify({
        "code": 200,
        "data": {
            "ogc_fid": item.ogc_fid,
            "name": item.name,
            "related_address": item.related_address,
            "longitude": float(item.longitude) if item.longitude else None,
            "latitude": float(item.latitude) if item.latitude else None
        }
    })


@admin.route('/wuhanmiddleschool/add', methods=['POST'])
def wuhanmiddleschool_add():
    """新增中学数据"""
    data = request.get_json()
    required_fields = ['name', 'longitude', 'latitude']
    if not all(field in data for field in required_fields):
        return jsonify({"code": 400, "msg": "缺少必填字段：name/longitude/latitude"}), 400

    try:
        # 解析坐标
        x = float(data['longitude'])
        y = float(data['latitude'])
        # 创建空间几何对象
        geometry = func.ST_SetSRID(func.ST_MakePoint(x, y), 4326)

        # 实例化新数据
        new_item = WuhanMiddleSchool(
            name=data['name'],
            related_address=data.get('related_address'),
            longitude=x,
            latitude=y,
            geometry=geometry
        )

        # 提交数据库
        db.session.add(new_item)
        db.session.commit()
        return jsonify({
            "code": 200,
            "msg": "新增中学数据成功",
            "data": {"ogc_fid": new_item.ogc_fid}
        })

    except Exception as e:
        db.session.rollback()
        return jsonify({"code": 500, "msg": f"新增失败：{str(e)}"}), 500


@admin.route('/wuhanmiddleschool/update', methods=['POST'])
def wuhanmiddleschool_update():
    """更新中学数据"""
    data = request.get_json()
    ogc_fid = data.get('ogc_fid')
    if not ogc_fid:
        return jsonify({"code": 400, "msg": "缺少参数：ogc_fid"}), 400

    # 查询数据
    item = WuhanMiddleSchool.query.get(ogc_fid)
    if not item:
        return jsonify({"code": 404, "msg": "未找到中学数据"}), 404

    try:
        # 更新字段
        item.name = data.get('name', item.name)
        item.related_address = data.get('related_address', item.related_address)

        # 处理坐标更新
        if 'longitude' in data and 'latitude' in data:
            x = float(data['longitude'])
            y = float(data['latitude'])
            item.longitude = x
            item.latitude = y
            item.geometry = func.ST_SetSRID(func.ST_MakePoint(x, y), 4326)

        # 提交更新
        db.session.commit()
        return jsonify({"code": 200, "msg": "更新中学数据成功"})

    except Exception as e:
        db.session.rollback()
        return jsonify({"code": 500, "msg": f"更新失败：{str(e)}"}), 500


@admin.route('/wuhanmiddleschool/delete', methods=['POST'])
def wuhanmiddleschool_delete():
    """删除中学数据"""
    data = request.get_json()
    ogc_fid = data.get('ogc_fid')
    if not ogc_fid:
        return jsonify({"code": 400, "msg": "缺少参数：ogc_fid"}), 400

    # 查询数据
    item = WuhanMiddleSchool.query.get(ogc_fid)
    if not item:
        return jsonify({"code": 404, "msg": "未找到中学数据"}), 404

    try:
        # 删除数据
        db.session.delete(item)
        db.session.commit()
        return jsonify({"code": 200, "msg": "删除中学数据成功"})

    except Exception as e:
        db.session.rollback()
        return jsonify({"code": 500, "msg": f"删除失败：{str(e)}"}), 500


"""
-------------------------- 武汉市小学接口 --------------------------
"""


@admin.route('/wuhanprimaryschool/search', methods=['GET'])
def wuhanprimaryschool_search():
    """搜索小学数据"""
    keyword = request.args.get('q', '').strip().lower()
    page = request.args.get('page', 1, type=int)
    page_size = request.args.get('pageSize', 15, type=int)
    offset = (page - 1) * page_size

    # 基础查询
    query = db.session.query(
        WuhanPrimarySchool.ogc_fid, WuhanPrimarySchool.name,
        WuhanPrimarySchool.related_address, WuhanPrimarySchool.longitude,
        WuhanPrimarySchool.latitude
    )

    # 关键词过滤
    if keyword:
        query = query.filter(
            (func.lower(WuhanPrimarySchool.name).ilike(f'%{keyword}%')) |
            (func.lower(WuhanPrimarySchool.related_address).ilike(f'%{keyword}%'))
        )

    # 分页查询
    total = query.count()
    results = query.limit(page_size).offset(offset).all()

    # 格式化返回数据
    data_list = [
        {
            "ogc_fid": item.ogc_fid,
            "name": item.name,
            "related_address": item.related_address,
            "longitude": round(float(item.longitude), 6) if item.longitude else None,
            "latitude": round(float(item.latitude), 6) if item.latitude else None
        } for item in results
    ]

    return jsonify({
        "data": data_list,
        "total": total,
        "page": page,
        "pageSize": page_size
    })


@admin.route('/wuhanprimaryschool/get', methods=['GET'])
def wuhanprimaryschool_get():
    """获取单个小学数据"""
    ogc_fid = request.args.get('id', type=int)
    if not ogc_fid:
        return jsonify({"code": 400, "msg": "缺少参数：id"}), 400

    item = WuhanPrimarySchool.query.get(ogc_fid)
    if not item:
        return jsonify({"code": 404, "msg": f"未找到ID为{ogc_fid}的小学数据"}), 404

    return jsonify({
        "code": 200,
        "data": {
            "ogc_fid": item.ogc_fid,
            "name": item.name,
            "related_address": item.related_address,
            "longitude": float(item.longitude) if item.longitude else None,
            "latitude": float(item.latitude) if item.latitude else None
        }
    })


@admin.route('/wuhanprimaryschool/add', methods=['POST'])
def wuhanprimaryschool_add():
    """新增小学数据"""
    data = request.get_json()
    required_fields = ['name', 'longitude', 'latitude']
    if not all(field in data for field in required_fields):
        return jsonify({"code": 400, "msg": "缺少必填字段：name/longitude/latitude"}), 400

    try:
        # 解析坐标
        x = float(data['longitude'])
        y = float(data['latitude'])
        # 创建空间几何对象
        geometry = func.ST_SetSRID(func.ST_MakePoint(x, y), 4326)

        # 实例化新数据
        new_item = WuhanPrimarySchool(
            name=data['name'],
            related_address=data.get('related_address'),
            longitude=x,
            latitude=y,
            geometry=geometry
        )

        # 提交数据库
        db.session.add(new_item)
        db.session.commit()
        return jsonify({
            "code": 200,
            "msg": "新增小学数据成功",
            "data": {"ogc_fid": new_item.ogc_fid}
        })

    except Exception as e:
        db.session.rollback()
        return jsonify({"code": 500, "msg": f"新增失败：{str(e)}"}), 500


@admin.route('/wuhanprimaryschool/update', methods=['POST'])
def wuhanprimaryschool_update():
    """更新小学数据"""
    data = request.get_json()
    ogc_fid = data.get('ogc_fid')
    if not ogc_fid:
        return jsonify({"code": 400, "msg": "缺少参数：ogc_fid"}), 400

    # 查询数据
    item = WuhanPrimarySchool.query.get(ogc_fid)
    if not item:
        return jsonify({"code": 404, "msg": "未找到小学数据"}), 404

    try:
        # 更新字段
        item.name = data.get('name', item.name)
        item.related_address = data.get('related_address', item.related_address)

        # 处理坐标更新
        if 'longitude' in data and 'latitude' in data:
            x = float(data['longitude'])
            y = float(data['latitude'])
            item.longitude = x
            item.latitude = y
            item.geometry = func.ST_SetSRID(func.ST_MakePoint(x, y), 4326)

        # 提交更新
        db.session.commit()
        return jsonify({"code": 200, "msg": "更新小学数据成功"})

    except Exception as e:
        db.session.rollback()
        return jsonify({"code": 500, "msg": f"更新失败：{str(e)}"}), 500


@admin.route('/wuhanprimaryschool/delete', methods=['POST'])
def wuhanprimaryschool_delete():
    """删除小学数据"""
    data = request.get_json()
    ogc_fid = data.get('ogc_fid')
    if not ogc_fid:
        return jsonify({"code": 400, "msg": "缺少参数：ogc_fid"}), 400

    # 查询数据
    item = WuhanPrimarySchool.query.get(ogc_fid)
    if not item:
        return jsonify({"code": 404, "msg": "未找到小学数据"}), 404

    try:
        # 删除数据
        db.session.delete(item)
        db.session.commit()
        return jsonify({"code": 200, "msg": "删除小学数据成功"})

    except Exception as e:
        db.session.rollback()
        return jsonify({"code": 500, "msg": f"删除失败：{str(e)}"}), 500


"""
-------------------------- 武汉市地铁线路接口 --------------------------
"""


@admin.route('/wuhanmetroline/search', methods=['GET'])
def wuhanmetroline_search():
    """搜索地铁线路数据"""
    keyword = request.args.get('q', '').strip().lower()
    page = request.args.get('page', 1, type=int)
    page_size = request.args.get('pageSize', 15, type=int)
    offset = (page - 1) * page_size

    # 基础查询
    query = db.session.query(
        MetroLine.ogc_fid, MetroLine.name, MetroLine.layer,
        MetroLine.origin, MetroLine.destination
    )

    # 关键词过滤
    if keyword:
        query = query.filter(
            (func.lower(MetroLine.name).ilike(f'%{keyword}%')) |
            (func.lower(MetroLine.layer).ilike(f'%{keyword}%')) |
            (func.lower(MetroLine.origin).ilike(f'%{keyword}%')) |
            (func.lower(MetroLine.destination).ilike(f'%{keyword}%'))
        )

    # 分页查询
    total = query.count()
    results = query.limit(page_size).offset(offset).all()

    # 格式化返回数据
    data_list = [
        {
            "ogc_fid": item.ogc_fid,
            "name": item.name,
            "layer": item.layer,
            "origin": item.origin,
            "destination": item.destination
        } for item in results
    ]

    return jsonify({
        "data": data_list,
        "total": total,
        "page": page,
        "pageSize": page_size
    })


@admin.route('/wuhanmetroline/get', methods=['GET'])
def wuhanmetroline_get():
    """获取单个地铁线路数据"""
    ogc_fid = request.args.get('id', type=int)
    if not ogc_fid:
        return jsonify({"code": 400, "msg": "缺少参数：id"}), 400

    item = MetroLine.query.get(ogc_fid)
    if not item:
        return jsonify({"code": 404, "msg": f"未找到ID为{ogc_fid}的地铁线路数据"}), 404

    return jsonify({
        "code": 200,
        "data": {
            "ogc_fid": item.ogc_fid,
            "name": item.name,
            "layer": item.layer,
            "origin": item.origin,
            "destination": item.destination
        }
    })


@admin.route('/wuhanmetroline/add', methods=['POST'])
def wuhanmetroline_add():
    """新增地铁线路数据"""
    data = request.get_json()
    required_fields = ['name', 'coordinates']  # coordinates为线要素坐标数组[[x1,y1], [x2,y2]...]
    if not all(field in data for field in required_fields):
        return jsonify({"code": 400, "msg": "缺少必填字段：name/coordinates"}), 400

    try:
        # 解析线要素坐标
        coordinates = data['coordinates']
        if len(coordinates) < 2:
            return jsonify({"code": 400, "msg": "线要素至少需要2个点坐标"}), 400

        # 构建LINESTRING字符串
        line_string = f"LINESTRING({','.join([f'{point[0]} {point[1]}' for point in coordinates])})"
        geometry = func.ST_SetSRID(func.ST_GeomFromText(line_string), 4326)

        # 实例化新数据
        new_item = MetroLine(
            name=data['name'],
            layer=data.get('layer'),
            origin=data.get('origin'),
            destination=data.get('destination'),
            geometry=geometry
        )

        # 提交数据库
        db.session.add(new_item)
        db.session.commit()
        return jsonify({
            "code": 200,
            "msg": "新增地铁线路数据成功",
            "data": {"ogc_fid": new_item.ogc_fid}
        })

    except Exception as e:
        db.session.rollback()
        return jsonify({"code": 500, "msg": f"新增失败：{str(e)}"}), 500


@admin.route('/wuhanmetroline/update', methods=['POST'])
def wuhanmetroline_update():
    """更新地铁线路数据"""
    data = request.get_json()
    ogc_fid = data.get('ogc_fid')
    if not ogc_fid:
        return jsonify({"code": 400, "msg": "缺少参数：ogc_fid"}), 400

    # 查询数据
    item = MetroLine.query.get(ogc_fid)
    if not item:
        return jsonify({"code": 404, "msg": "未找到地铁线路数据"}), 404

    try:
        # 更新属性字段
        item.name = data.get('name', item.name)
        item.layer = data.get('layer', item.layer)
        item.origin = data.get('origin', item.origin)
        item.destination = data.get('destination', item.destination)

        # 处理几何要素更新
        if 'coordinates' in data:
            coordinates = data['coordinates']
            if len(coordinates) < 2:
                return jsonify({"code": 400, "msg": "线要素至少需要2个点坐标"}), 400

            line_string = f"LINESTRING({','.join([f'{point[0]} {point[1]}' for point in coordinates])})"
            item.geometry = func.ST_SetSRID(func.ST_GeomFromText(line_string), 4326)

        # 提交更新
        db.session.commit()
        return jsonify({"code": 200, "msg": "更新地铁线路数据成功"})

    except Exception as e:
        db.session.rollback()
        return jsonify({"code": 500, "msg": f"更新失败：{str(e)}"}), 500


@admin.route('/wuhanmetroline/delete', methods=['POST'])
def wuhanmetroline_delete():
    """删除地铁线路数据"""
    data = request.get_json()
    ogc_fid = data.get('ogc_fid')
    if not ogc_fid:
        return jsonify({"code": 400, "msg": "缺少参数：ogc_fid"}), 400

    # 查询数据
    item = MetroLine.query.get(ogc_fid)
    if not item:
        return jsonify({"code": 404, "msg": "未找到地铁线路数据"}), 404

    try:
        # 删除数据
        db.session.delete(item)
        db.session.commit()
        return jsonify({"code": 200, "msg": "删除地铁线路数据成功"})

    except Exception as e:
        db.session.rollback()
        return jsonify({"code": 500, "msg": f"删除失败：{str(e)}"}), 500


"""
-------------------------- 地铁十分钟等时圈接口 --------------------------
"""


@admin.route('/metro10mincircle/search', methods=['GET'])
def metro10mincircle_search():
    """搜索地铁十分钟等时圈数据"""
    keyword = request.args.get('q', '').strip().lower()
    page = request.args.get('page', 1, type=int)
    page_size = request.args.get('pageSize', 15, type=int)
    offset = (page - 1) * page_size

    # 基础查询
    query = db.session.query(
        Metro10minWaitCircle.fid, Metro10minWaitCircle.id,
        Metro10minWaitCircle.center_lon, Metro10minWaitCircle.center_lat,
        Metro10minWaitCircle.aa_mins, Metro10minWaitCircle.aa_mode,
        Metro10minWaitCircle.total_pop, Metro10minWaitCircle.name
    )

    # 关键词过滤
    if keyword:
        query = query.filter(
            (func.lower(Metro10minWaitCircle.name).ilike(f'%{keyword}%')) |
            (func.lower(Metro10minWaitCircle.id).ilike(f'%{keyword}%')) |
            (func.lower(Metro10minWaitCircle.aa_mode).ilike(f'%{keyword}%'))
        )

    # 分页查询
    total = query.count()
    results = query.limit(page_size).offset(offset).all()

    # 格式化返回数据
    data_list = [
        {
            "fid": item.fid,
            "id": item.id,
            "center_lon": item.center_lon,
            "center_lat": item.center_lat,
            "aa_mins": item.aa_mins,
            "aa_mode": item.aa_mode,
            "total_pop": item.total_pop,
            "name": item.name
        } for item in results
    ]

    return jsonify({
        "data": data_list,
        "total": total,
        "page": page,
        "pageSize": page_size
    })


@admin.route('/metro10mincircle/get', methods=['GET'])
def metro10mincircle_get():
    """获取单个地铁十分钟等时圈数据"""
    fid = request.args.get('id', type=int)
    if not fid:
        return jsonify({"code": 400, "msg": "缺少参数：id"}), 400

    item = Metro10minWaitCircle.query.get(fid)
    if not item:
        return jsonify({"code": 404, "msg": f"未找到ID为{fid}的地铁十分钟等时圈数据"}), 404

    return jsonify({
        "code": 200,
        "data": {
            "fid": item.fid,
            "id": item.id,
            "center_lon": item.center_lon,
            "center_lat": item.center_lat,
            "aa_mins": item.aa_mins,
            "aa_mode": item.aa_mode,
            "total_pop": item.total_pop,
            "name": item.name
        }
    })


@admin.route('/metro10mincircle/add', methods=['POST'])
def metro10mincircle_add():
    """新增地铁十分钟等时圈数据"""
    data = request.get_json()
    required_fields = ['name', 'center_lon', 'center_lat', 'coordinates']  # coordinates为面要素坐标数组[[[x1,y1], [x2,y2]...]]
    if not all(field in data for field in required_fields):
        return jsonify({"code": 400, "msg": "缺少必填字段：name/center_lon/center_lat/coordinates"}), 400

    try:
        # 解析面要素坐标（多边形需闭合，至少3个点）
        coordinates = data['coordinates']
        if len(coordinates[0]) < 3 or coordinates[0][0] != coordinates[0][-1]:
            return jsonify({"code": 400, "msg": "面要素需为闭合多边形，至少3个点且首尾坐标一致"}), 400

        # 构建POLYGON字符串
        polygon_coords = [f'{point[0]} {point[1]}' for point in coordinates[0]]
        polygon_string = f"POLYGON(({','.join(polygon_coords)}))"
        geometry = func.ST_SetSRID(func.ST_GeomFromText(polygon_string), 4326)

        # 实例化新数据
        new_item = Metro10minWaitCircle(
            id=data.get('id'),
            center_lon=str(data['center_lon']),
            center_lat=str(data['center_lat']),
            aa_mins=data.get('aa_mins', '10'),  # 默认10分钟等时圈
            aa_mode=data.get('aa_mode', '地铁'),
            total_pop=data.get('total_pop'),
            name=data['name'],
            geometry=geometry
        )

        # 提交数据库
        db.session.add(new_item)
        db.session.commit()
        return jsonify({
            "code": 200,
            "msg": "新增地铁十分钟等时圈数据成功",
            "data": {"fid": new_item.fid}
        })

    except Exception as e:
        db.session.rollback()
        return jsonify({"code": 500, "msg": f"新增失败：{str(e)}"}), 500


@admin.route('/metro10mincircle/update', methods=['POST'])
def metro10mincircle_update():
    """更新地铁十分钟等时圈数据"""
    data = request.get_json()
    fid = data.get('fid')
    if not fid:
        return jsonify({"code": 400, "msg": "缺少参数：fid"}), 400

    # 查询数据
    item = Metro10minWaitCircle.query.get(fid)
    if not item:
        return jsonify({"code": 404, "msg": "未找到地铁十分钟等时圈数据"}), 404

    try:
        # 更新属性字段
        item.id = data.get('id', item.id)
        item.name = data.get('name', item.name)
        item.aa_mins = data.get('aa_mins', item.aa_mins)
        item.aa_mode = data.get('aa_mode', item.aa_mode)
        item.total_pop = data.get('total_pop', item.total_pop)

        # 处理中心经纬度更新
        if 'center_lon' in data:
            item.center_lon = str(data['center_lon'])
        if 'center_lat' in data:
            item.center_lat = str(data['center_lat'])

        # 处理几何要素更新
        if 'coordinates' in data:
            coordinates = data['coordinates']
            if len(coordinates[0]) < 3 or coordinates[0][0] != coordinates[0][-1]:
                return jsonify({"code": 400, "msg": "面要素需为闭合多边形，至少3个点且首尾坐标一致"}), 400

            polygon_coords = [f'{point[0]} {point[1]}' for point in coordinates[0]]
            polygon_string = f"POLYGON(({','.join(polygon_coords)}))"
            item.geometry = func.ST_SetSRID(func.ST_GeomFromText(polygon_string), 4326)

        # 提交更新
        db.session.commit()
        return jsonify({"code": 200, "msg": "更新地铁十分钟等时圈数据成功"})

    except Exception as e:
        db.session.rollback()
        return jsonify({"code": 500, "msg": f"更新失败：{str(e)}"}), 500


@admin.route('/metro10mincircle/delete', methods=['POST'])
def metro10mincircle_delete():
    """删除地铁十分钟等时圈数据"""
    data = request.get_json()
    fid = data.get('fid')
    if not fid:
        return jsonify({"code": 400, "msg": "缺少参数：fid"}), 400

    # 查询数据
    item = Metro10minWaitCircle.query.get(fid)
    if not item:
        return jsonify({"code": 404, "msg": "未找到地铁十分钟等时圈数据"}), 404

    try:
        # 删除数据
        db.session.delete(item)
        db.session.commit()
        return jsonify({"code": 200, "msg": "删除地铁十分钟等时圈数据成功"})

    except Exception as e:
        db.session.rollback()
        return jsonify({"code": 500, "msg": f"删除失败：{str(e)}"}), 500