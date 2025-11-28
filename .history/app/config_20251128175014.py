import os

class Config:
    # 数据库配置
    SQLALCHEMY_DATABASE_URI = "postgresql://123:123123@ye11ts688906.vicp.fun:25354/test_2"
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    DEBUG = True

class SearchConfig:
    FIELDS = ["name", "type", "district"]
    DEBUG = False # 是否开启调试模式