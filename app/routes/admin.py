# app/routes/admin.py
from flask import Blueprint, request, jsonify
from app import db
from app.models.wuhan_middle_school import WuhanMiddleSchool
from sqlalchemy import func

# 数据模型导入
from app.models.public_services import PublicServices
from app.models.metro_station import MetroStation
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
        WuhanMiddleSchool.related_address, WuhanMiddleSchool.x_transfer,
        WuhanMiddleSchool.y_transfer
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
            "x_transfer": round(float(item.x_transfer), 6) if item.x_transfer else None,
            "y_transfer": round(float(item.y_transfer), 6) if item.y_transfer else None
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
            "x_transfer": float(item.x_transfer) if item.x_transfer else None,
            "y_transfer": float(item.y_transfer) if item.y_transfer else None
        }
    })


@admin.route('/wuhanmiddleschool/add', methods=['POST'])
def wuhanmiddleschool_add():
    """新增中学数据"""
    data = request.get_json()
    required_fields = ['name', 'x_transfer', 'y_transfer']
    if not all(field in data for field in required_fields):
        return jsonify({"code": 400, "msg": "缺少必填字段：name/x_transfer/y_transfer"}), 400

    try:
        # 解析坐标
        x = float(data['x_transfer'])
        y = float(data['y_transfer'])
        # 创建空间几何对象
        geometry = func.ST_SetSRID(func.ST_MakePoint(x, y), 4326)

        # 实例化新数据
        new_item = WuhanMiddleSchool(
            name=data['name'],
            related_address=data.get('related_address'),
            x_transfer=x,
            y_transfer=y,
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
        if 'x_transfer' in data and 'y_transfer' in data:
            x = float(data['x_transfer'])
            y = float(data['y_transfer'])
            item.x_transfer = x
            item.y_transfer = y
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
        WuhanPrimarySchool.related_address, WuhanPrimarySchool.x_transfer,
        WuhanPrimarySchool.y_transfer
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
            "x_transfer": round(float(item.x_transfer), 6) if item.x_transfer else None,
            "y_transfer": round(float(item.y_transfer), 6) if item.y_transfer else None
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
            "x_transfer": float(item.x_transfer) if item.x_transfer else None,
            "y_transfer": float(item.y_transfer) if item.y_transfer else None
        }
    })


@admin.route('/wuhanprimaryschool/add', methods=['POST'])
def wuhanprimaryschool_add():
    """新增小学数据"""
    data = request.get_json()
    required_fields = ['name', 'x_transfer', 'y_transfer']
    if not all(field in data for field in required_fields):
        return jsonify({"code": 400, "msg": "缺少必填字段：name/x_transfer/y_transfer"}), 400

    try:
        # 解析坐标
        x = float(data['x_transfer'])
        y = float(data['y_transfer'])
        # 创建空间几何对象
        geometry = func.ST_SetSRID(func.ST_MakePoint(x, y), 4326)

        # 实例化新数据
        new_item = WuhanPrimarySchool(
            name=data['name'],
            related_address=data.get('related_address'),
            x_transfer=x,
            y_transfer=y,
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
        if 'x_transfer' in data and 'y_transfer' in data:
            x = float(data['x_transfer'])
            y = float(data['y_transfer'])
            item.x_transfer = x
            item.y_transfer = y
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