import os

class Config:
    # 数据库配置
    SQLALCHEMY_DATABASE_URI = "postgresql://postgres:2025POST@ye11ts688906.vicp.fun:17162/test_2"
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    DEBUG = True

class SearchConfig:
    FIELDS = ["name", "type", "district"]
    DEBUG = True # 是否开启调试模式
    DEBUG_POI_SEARCH = False # 单独调试POI搜索功能
    searchListNum = 10
    ifWordVec = False  # 是否启用词向量进行语义搜索