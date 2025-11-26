import json
from flask import Flask, render_template, request, jsonify
from pathlib import Path

app = Flask(__name__)

# 加载本地数据（仅启动时加载一次）
DATA_DIR = Path(__file__).parent / "data"
with open(DATA_DIR / "poi_sample.json", encoding='utf-8') as f:
    POI_DATA = json.load(f)

@app.route('/')
def index():
    return render_template('index.html')

# 属性关键词查询（如“学校”）,现在是只查名字，而且只能查一次，还要改
@app.route('/api/search')
def search_poi():
    keyword = request.args.get('q', '').strip()
    if not keyword:
        return jsonify([])
    
    results = [
        item for item in POI_DATA
        if keyword.lower() in item['name'].lower() or keyword.lower() in item['type'].lower()
    ]
    return jsonify(results)

# 矩形范围查询，还未实现，有误
@app.route('/api/bbox')
def bbox_query():
    try:
        min_lon = float(request.args.get('min_lon'))
        min_lat = float(request.args.get('min_lat'))
        max_lon = float(request.args.get('max_lon'))
        max_lat = float(request.args.get('max_lat'))
    except (TypeError, ValueError):
        return jsonify([])

    results = [
        item for item in POI_DATA
        if min_lon <= item['lon'] <= max_lon and min_lat <= item['lat'] <= max_lat
    ]
    return jsonify(results)

if __name__ == '__main__':
    app.run(debug=True)