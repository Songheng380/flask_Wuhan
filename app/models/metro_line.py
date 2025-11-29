# app/models/metro_line.py
from app import db
from geoalchemy2 import Geometry  # 处理PostGIS空间类型


class MetroLine(db.Model):
    """武汉地铁线路模型（对应表：武汉地铁线路，线要素）"""
    __tablename__ = '武汉地铁线路'
    __table_args__ = {'schema': 'wuhan_sum'}  # 与现有模型统一绑定wuhan_sum schema

    # 与数据库表字段严格对应，用 db_column 映射关键字字段
    ogc_fid = db.Column(db.Integer, primary_key=True, autoincrement=True)  # 自增主键
    geometry = db.Column(Geometry(geometry_type='LINESTRING', srid=900915))  # 线要素（WGS84坐标系）
    name = db.Column(db.String(80))  # 线路名称（如：2号线、4号线）
    layer = db.Column(db.String(80))  # 图层信息
    origin = db.Column(db.String(50), name='form')  # 始发站（映射数据库form字段）
    destination = db.Column(db.String(50), name='to')  # 终点站（映射数据库to字段）
