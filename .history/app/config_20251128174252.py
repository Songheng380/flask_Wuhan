import os

class Config:
    # 数据库配置
    SQLALCHEMY_DATABASE_URI = "postgresql://123:123123@ye11ts688906.vicp.fun:25354/test_2"
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    DEBUG = True

class SearchConfig:
    FIELDS = ["name", "type", "district"]
    sample = True # 是否使用样本数据进行测试
    DEBUG = True # 是否开启调试模式