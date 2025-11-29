# app/models/wuhan_primary_school.py
from app import db
from geoalchemy2 import Geometry  # 处理PostGIS空间类型


class WuhanPrimarySchool(db.Model):
    # 指定schema和数据库表名
    __tablename__ = '武汉市小学'
    __table_args__ = {'schema': 'wuhan_sum'}  # 绑定到wuhan_sum schema

    # 匹配数据库表字段
    ogc_fid = db.Column(db.Integer, primary_key=True, autoincrement=True)  # 自增主键
    geometry = db.Column(Geometry(geometry_type='POINT', srid=4326))
    longitude = db.Column(db.Numeric(18, 11), name='x_transfer')
    latitude = db.Column(db.Numeric(18, 11), name='y_transfer')
    name = db.Column(db.String(254), name='名称')  # 英文变量name → 映射数据库中文字段“名称”
    related_address = db.Column(db.String(254), name='相关地')  # 英文变量related_address → 映射数据库中文字段“相关地”
