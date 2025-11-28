# app/routes/api.py
from flask import Blueprint, request, jsonify, current_app
from app import db
from sqlalchemy.exc import OperationalError
import json
from geoalchemy2 import Geometry
from sqlalchemy import func
import json
import os


# 数据模型
from app.models.metro_station import MetroStation
from app.models.public_services import PublicServices
from app.models.wuhan_middle_school import WuhanMiddleSchool
from app.models.wuhan_primary_school import WuhanPrimarySchool

api = Blueprint('api', __name__)

# api配置
from app.config import SearchConfig

# 初始化wordvec配置
from app.routes.wordvec import load_chinese_vectors, cosine_similarity, vectorize_text
if SearchConfig.ifWordVec:
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))
    WORD_VECTORS = load_chinese_vectors(os.path.join(BASE_DIR, "./src/sgns.target.word-word.dynwin5.thr10.neg5.dim300.iter5"), max_words=500000)
else:
    WORD_VECTORS = None
# # 属性关键词查询（如“学校”、“商业”）

def load_poi_data():
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))
    poi_path = os.path.join(BASE_DIR, "../../data/poi_sample.json")
    poi_path = os.path.normpath(poi_path)
    with open(poi_path, "r", encoding="utf-8") as f:
        return json.load(f)
    
def search_poi(POI_DATA=None, keyword=None, FIELDS=SearchConfig.FIELDS):
    """
    支持三种查询模式：
    1. 精确查询 exact=true
    2. 模糊查询 exact=false
    3. 语义查询 mode=semantic
    """
    if SearchConfig.DEBUG_POI_SEARCH:
        POI_DATA = load_poi_data()

    keyword = request.args.get("q", "").strip().lower()
    if not keyword:
        return jsonify([])

    exact = request.args.get("exact", "false").lower() == "true"
    mode = request.args.get("mode", "text").lower()  # text / semantic

    if mode == "semantic":
        print("✅ 进行语义查询")
        query_vector = vectorize_text(keyword, word_vectors=WORD_VECTORS)
        if query_vector is None:
            return jsonify([])

        results = []
        for item in POI_DATA:
            # 简单将POI名字拼成字符列表进行平均向量
            item_text = "".join([str(item.get(field, "")) for field in FIELDS])
            item_vector = vectorize_text(item_text, word_vectors=WORD_VECTORS)
            if item_vector is None:
                continue
            sim = cosine_similarity(query_vector, item_vector)
            results.append((sim, item))
        # 按相似度排序
        results.sort(key=lambda x: x[0], reverse=True)
        results = [x[1] for x in results[:SearchConfig.searchListNum]]  # 可选：返回前10条
    else:
        if exact:
            print("✅ 进行精确查询")
            results = [
                item for item in POI_DATA
                if any(keyword == str(item.get(field, "")).lower() for field in FIELDS)
            ]
        else:
            print("✅ 进行模糊查询")
            results = [
                item for item in POI_DATA
                if any(keyword in str(item.get(field, "")).lower() for field in FIELDS)
            ]

    return jsonify(results)



    
# 接收矩形框参数
def get_bbox_params():
    """
    从请求中接收矩形框四个坐标
    返回:
        min_lon, min_lat, max_lon, max_lat (float)
        如果参数缺失或错误，返回 None
    """
    try:
        min_lon = float(request.args.get('min_lon'))
        min_lat = float(request.args.get('min_lat'))
        max_lon = float(request.args.get('max_lon'))
        max_lat = float(request.args.get('max_lat'))
        print(f"✅ 收到矩形坐标: min_lon={min_lon}, min_lat={min_lat}, max_lon={max_lon}, max_lat={max_lat}")
        return min_lon, min_lat, max_lon, max_lat
    except (TypeError, ValueError):
        return None
    

# 矩形范围查询
@api.route('/search')
def bbox_query():
    # 加载 POI 测试数据
    POI_DATA = load_poi_data() if SearchConfig.DEBUG else []

    # 获取矩形范围
    coords = get_bbox_params()
    print(coords)
    if coords:
        print("✅ 进行矩形范围过滤")
        min_lon, min_lat, max_lon, max_lat = coords
        filtered = [
            item for item in POI_DATA
            if min_lon <= item.get("lon", 9999) <= max_lon
            and min_lat <= item.get("lat", 9999) <= max_lat
        ]
    else:
        filtered = POI_DATA

    # 关键字搜索
    keyword = request.args.get("q", "").strip().lower()
    result = search_poi(POI_DATA=filtered, keyword=keyword, FIELDS=SearchConfig.FIELDS)

    return result

# @api.route('/search')
# def search_handler():
#     if SearchConfig.DEBUG_POI_SERACH:
#         return search_poi()
#     else:
#         return bbox_query()

# if SearchConfig.DEBUG_POI_SEARCH:
#     api.add_url_rule('/search', view_func=search_poi)
# else:
#     api.add_url_rule('/search', view_func=bbox_query)


@api.route('/test_db', methods=['GET'])
def test_db_connection():
    """测试数据库连接状态（显示原始错误+中文提示）"""
    try:
        # 轻量查询验证连接
        db.session.execute(db.text("SELECT 1"))
        db.session.commit()

        response_data = {
            "code": 200,
            "msg": "数据库连接成功！",
            "raw_error": None
        }
        response = current_app.response_class(
            response=json.dumps(response_data, ensure_ascii=False, indent=2),
            status=200,
            mimetype='application/json; charset=utf-8'
        )
        return response

    except OperationalError as e:
        raw_error = str(e)  # 原始错误信息（未转义，保留完整上下文）
        # 中文提示
        if "could not translate host name" in raw_error:
            detail = "主机名无法解析（域名错误/网络不通）"
        elif "connection refused" in raw_error:
            detail = "端口未开放（防火墙/PostgreSQL未启动）"
        elif "password authentication failed" in raw_error:
            detail = "用户名/密码错误"
        elif "database does not exist" in raw_error:
            detail = "数据库不存在"
        else:
            detail = "数据库连接失败"

        response_data = {
            "code": 500,
            "msg": detail,
            "raw_error": raw_error,  # 显示原始错误（如主机名解析失败的完整信息）
            "detail": "请检查：1. 数据库URL中的主机名是否正确 2. 网络是否能访问该主机 3. 服务器防火墙是否开放端口"
        }
        response = current_app.response_class(
            response=json.dumps(response_data, ensure_ascii=False, indent=2),
            status=500,
            mimetype='application/json; charset=utf-8'
        )
        return response

    except Exception as e:
        raw_error = str(e)
        response_data = {
            "code": 500,
            "msg": "未知错误",
            "raw_error": raw_error,
            "detail": "请检查代码或服务器环境"
        }
        response = current_app.response_class(
            response=json.dumps(response_data, ensure_ascii=False, indent=2),
            status=500,
            mimetype='application/json; charset=utf-8'
        )
        return response