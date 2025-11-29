# app/models/metro_10min_wait_circle.py
from app import db
from geoalchemy2 import Geometry  # 处理PostGIS空间类型


class Metro10minWaitCircle(db.Model):
    """地铁十分钟等时圈模型（对应表：地铁十分钟等时圈，面要素）"""
    __tablename__ = '地铁十分钟等时圈'
    __table_args__ = {'schema': 'wuhan_sum'}  # 与现有模型统一绑定wuhan_sum schema

    # 与数据库表字段严格对应（无关键字冲突，直接命名）
    fid = db.Column(db.Integer, primary_key=True, autoincrement=True)  # 自增主键
    id = db.Column(db.String(254))  # 标识ID
    center_lon = db.Column(db.String(254))  # 中心经度
    center_lat = db.Column(db.String(254))  # 中心纬度
    aa_mins = db.Column(db.String(254))  # 等时时间（10分钟）
    aa_mode = db.Column(db.String(254))  # 交通方式
    total_pop = db.Column(db.String(254))  # 覆盖人口
    name = db.Column(db.String(254))  # 等时圈名称（如：洪山广场站10分钟等时圈）
    geometry = db.Column(Geometry(geometry_type='POLYGON', srid=4326))  # 面要素（WGS84坐标系）
