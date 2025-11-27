# app/models/metro_station.py
from app import db
from geoalchemy2 import Geometry  # 处理PostGIS空间类型

class MetroStation(db.Model):
    # 指定表所属的schema和表名
    __tablename__ = 'wuhanmetrostation'
    __table_args__ = {'schema': 'wuhan_shp'}  # 绑定到wuhan_shp schema

    # 匹配数据库表字段
    gid = db.Column(db.Integer, primary_key=True)  # 主键
    name = db.Column(db.String(80), nullable=False)  # 站点名称
    layer = db.Column(db.String(80), nullable=False)  # 线路（如轨道交通1号线）
    desc_ = db.Column(db.String)  # 描述（对应表中desc_字段）
    style = db.Column(db.String)  # 样式字段
    geom = db.Column(Geometry('POINT', srid=4326))  # 空间类型：POINT（点），坐标系SRID4326（WGS84）