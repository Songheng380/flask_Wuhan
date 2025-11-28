# app/models/public_services.py
from app import db
from geoalchemy2 import Geometry  # 处理PostGIS空间类型

class PublicServices(db.Model):
    # 指定schema和数据库表名（表名保持中文，与数据库一致）
    __tablename__ = '公共服务'
    __table_args__ = {'schema': 'wuhan_sum'}  # 绑定到wuhan_sum schema

    # 匹配数据库表字段
    fid = db.Column(db.Numeric(10, 0), primary_key=True)
    geometry = db.Column(Geometry(geometry_type='POINT', srid=4326))  # 空间点（WGS84）
    type = db.Column(db.String(254))
    gridcode = db.Column(db.Float)
    typecode = db.Column(db.String(254))
    poiweight = db.Column(db.String(254))
    adname = db.Column(db.String(254))
    id = db.Column(db.String(254))
    address = db.Column(db.String(254))
    adcode = db.Column(db.Numeric(10, 0))
    name = db.Column(db.String(254))
    longitude = db.Column(db.Numeric(23, 15))
    latitude = db.Column(db.Numeric(23, 15))
    category = db.Column(db.String(254))
    longitude_wgs84 = db.Column(db.Numeric(23, 15), name='longitude_')
    latitude_wgs84 = db.Column(db.Numeric(23, 15), name='latitude_w')