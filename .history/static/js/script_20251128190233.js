// 全局变量
let map = null;
let infoWindow = null;
let currentMarkers = []; 
let rectangleTool = null;
let currentRectangle = null; // 保存矩形对象

// 初始化地图
function initMap() {
    try {
        // 确保 AMap 已加载
        if (typeof AMap === 'undefined') {
            console.error("高德地图 JS API 未加载，请检查 Key 是否有效或网络是否通畅。");
            return;
        }

        map = new AMap.Map('container', {
            zoom: 11,
            center: [114.3, 30.58], // 武汉中心
            viewMode: '2D'
        });

        infoWindow = new AMap.InfoWindow({ offset: new AMap.Pixel(0, -10) });

        // 绑定回车键搜索功能
        document.getElementById('keyword').addEventListener('keypress', function (e) {
            if (e.key === 'Enter') {
                searchByKeyword();
            }
        });

        // 页面加载完成后，自动加载一次全部数据
        //fetchData('');

    } catch (error) {
        console.error("地图初始化失败:", error);
    }
}

// 页面加载完毕后执行初始化
document.addEventListener('DOMContentLoaded', initMap);


// 搜索
function searchByKeyword() {
    const keywordInput = document.getElementById('keyword');
    const q = keywordInput.value.trim();

    console.log(`正在搜索: "${q}"`);

    // 禁用输入框防止重复提交
    keywordInput.disabled = true;

    fetchData(q).finally(() => {
        keywordInput.disabled = false;
        keywordInput.focus();
    });
}

// 通用数据请求函数
function fetchData(query) {
    const url = `/api/search?q=${encodeURIComponent(query)}`;

    return fetch(url)
        .then(response => {
            if (!response.ok) {
                throw new Error(`网络请求失败，状态码: ${response.status}`);
            }
            return response.json();
        })
        .then(data => {
            console.log("后端返回的数据数量:", data.length);
            
            // 注意这里只清除标记，不清除矩形
            clearMarkersOnly();

            addMarkers(data);
            showResults(data, query ? `"${query}" 的搜索结果` : '全部数据');
        })
        .catch(error => {
            console.error("❌ 错误:", error);
            alert("发生错误: " + error.message);
        });
}

// 只清除标记，不清除矩形或工具
function clearMarkersOnly() {
    currentMarkers.forEach(marker => marker.setMap(null));
    currentMarkers = [];
}

// 添加标记
function addMarkers(pois) {
    if (!map) return;

    const newMarkers = [];
    const validBounds = new AMap.Bounds();
    let hasValidData = false;

    pois.forEach((poi, index) => {
        const lon = parseFloat(poi.lon || poi.lng || poi.x || poi.longitude);
        const lat = parseFloat(poi.lat || poi.y || poi.latitude);

        if (isNaN(lon) || isNaN(lat)) {
            console.warn(`第 ${index} 条数据坐标无效，跳过:`, poi);
            return;  // 彻底过滤
        }

        const marker = new AMap.Marker({
            position: [lon, lat],
            title: poi.name,
            map: map
        });

        const content = `
            <div style="padding:5px;">
                <strong>${poi.name || "无名称"}</strong><br>
                <span style="color:#666;font-size:12px;">${poi.type || "未知类型"} | ${poi.district || ""}</span>
            </div>`;

        marker.on('click', () => {
            const pos = marker.getPosition();
            if (!pos || isNaN(pos.lng) || isNaN(pos.lat)) return; // ✅ 关键检查
            infoWindow.setContent(content);
            infoWindow.open(map, pos);
        });

        newMarkers.push(marker);
    });

    currentMarkers = newMarkers;

    if (hasValidData) {
        map.setBounds(validBounds);
    }
}

function startRangeQuery() {
    if (!map) return;

    if (rectangleTool) {
        rectangleTool.close();
        rectangleTool = null;
    }

    rectangleTool = new AMap.MouseTool(map);

    rectangleTool.rectangle({
        strokeColor: "#0099FF",
        strokeWeight: 2,
        fillColor: "#02c3f4",
        fillOpacity: 0.15
    });

    rectangleTool.on('draw', function (event) {
        currentRectangle = event.obj;  // 保留矩形对象
        document.getElementById('rangeHint').style.display = 'none';

        const bounds = currentRectangle.getBounds();
        const southwest = bounds.getSouthWest();
        const northeast = bounds.getNorthEast();

        const coords = {
            min_lon: southwest.lng,
            min_lat: southwest.lat,
            max_lon: northeast.lng,
            max_lat: northeast.lat
        };

        console.log("矩形坐标:", coords);

        // 获取当前关键字
        const keyword = document.getElementById('keyword').value.trim();

        // 发请求
        const url = `api/search?min_lon=${coords.min_lon}&min_lat=${coords.min_lat}&max_lon=${coords.max_lon}&max_lat=${coords.max_lat}&q=${encodeURIComponent(keyword)}`;
        fetch(url)
            .then(res => {
                if (!res.ok) throw new Error(`HTTP error! status: ${res.status}`);
                // 不做任何数据处理，只是保证请求发送成功
                console.log("搜索请求已发送");
            })
            .catch(err => console.error("搜索请求失败:", err));
    });
}



window.startRangeQuery = startRangeQuery;

function clearMarkers() {
    // 清除标记
    currentMarkers.forEach(marker => marker.setMap(null));
    currentMarkers = [];

    // 清除矩形
    if (currentRectangle) {
        currentRectangle.setMap(null);
        currentRectangle = null;
    }
    // 关闭绘制工具
    if (rectangleTool) {
        rectangleTool.close();
        rectangleTool = null;
    }

    document.getElementById('rangeHint').style.display = 'none';
}



// 列表展示
function showResults(items, title) {
    const resultsDiv = document.getElementById('results');
    let html = `<h5>${title} <span class="badge bg-secondary">${items.length}</span></h5>`;
    
    if (items.length === 0) {
        html += '<div class="alert alert-warning">未找到相关数据</div>';
    } else {
        html += '<div class="list-group list-group-flush" style="max-height: 400px; overflow-y: auto;">';
        items.forEach(item => {
            html += `
                <div class="list-group-item list-group-item-action result-item">
                    <div class="d-flex w-100 justify-content-between">
                        <h6 class="mb-1">${item.name}</h6>
                        <small class="text-muted">${item.district}</small>
                    </div>
                    <small class="text-muted">${item.type}</small>
                </div>`;
        });
        html += '</div>';
    }
    resultsDiv.innerHTML = html;
}


// 暴露函数给全局（防止 HTML onclick 找不到）
window.searchByKeyword = searchByKeyword;
window.clearMarkers = clearMarkers;
window.startRangeQuery = startRangeQuery;