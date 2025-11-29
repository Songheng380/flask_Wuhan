# app/models/metro_station.py
from app import db
from geoalchemy2 import Geometry  # 处理PostGIS空间类型


class MetroStation(db.Model):
    # 指定表所属的schema和表名
    __tablename__ = '武汉市地铁站点'
    __table_args__ = {'schema': 'wuhan_sum'}  # 绑定到wuhan_sum schema

    # 匹配数据库表字段
    ogc_fid = db.Column(db.Integer, primary_key=True, autoincrement=True)  # 自增主键
    geometry = db.Column(Geometry(geometry_type='POINT', srid=900915))
    name = db.Column(db.String(80))
    line = db.Column(db.String(80))
    color = db.Column(db.String(80))
    lon_gcj02 = db.Column(db.Numeric(23, 15))
    lat_gcj02 = db.Column(db.Numeric(23, 15))
    lon_wgs84 = db.Column(db.Numeric(23, 15))
    lat_wgs84 = db.Column(db.Numeric(23, 15))
    transfer = db.Column(db.String(80))