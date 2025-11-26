// ====== 全局变量定义 ======
let map = null;
let infoWindow = null;
let currentMarkers = []; 
let rectangleTool = null;
let isSelecting = false;

// ====== 初始化地图 ======
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
        fetchData('');

    } catch (error) {
        console.error("地图初始化失败:", error);
    }
}

// 页面加载完毕后执行初始化
document.addEventListener('DOMContentLoaded', initMap);


// ====== 核心功能：搜索 ======
function searchByKeyword() {
    const keywordInput = document.getElementById('keyword');
    const q = keywordInput.value.trim();
    
    console.log(`正在搜索: "${q}"`); // Debug日志

    // 禁用输入框防止重复提交，直到请求结束
    keywordInput.disabled = true;
    
    fetchData(q).finally(() => {
        // 请求结束后（无论成功失败），恢复输入框
        keywordInput.disabled = false;
        keywordInput.focus();
    });
}

// ====== 通用数据请求函数 ======
function fetchData(query) {
    // 这里的 url 需要和你后端 app.py 定义的路由一致
    const url = `/api/search?q=${encodeURIComponent(query)}`;

    return fetch(url)
        .then(response => {
            if (!response.ok) {
                throw new Error(`网络请求失败，状态码: ${response.status}`);
            }
            return response.json();
        })
        .then(data => {
            console.log("获取数据成功，数量:", data.length);
            // 1. 清除旧标记
            clearMarkers();
            // 2. 添加新标记
            addMarkers(data);
            // 3. 更新右侧/下方列表
            showResults(data, query ? `"${query}" 的搜索结果` : '全部数据');
        })
        .catch(error => {
            console.error("搜索出错:", error);
            alert("搜索失败，请检查后端服务是否启动，或按 F12 查看控制台错误信息。");
        });
}


// ====== 地图标记操作 ======
function addMarkers(pois) {
    if (!map) return;

    let newMarkers = [];
    
    pois.forEach(poi => {
        // 防止脏数据导致报错 (例如经纬度缺失)
        if (!poi.lon || !poi.lat) return;

        const marker = new AMap.Marker({
            position: [poi.lon, poi.lat],
            title: poi.name,
            map: map // 直接添加到地图
        });

        const content = `
            <div style="padding:5px;">
                <strong>${poi.name}</strong><br>
                <span style="color:#666;font-size:12px;">${poi.type} | ${poi.district}</span>
            </div>`;

        marker.on('click', () => {
            infoWindow.setContent(content);
            infoWindow.open(map, marker.getPosition());
        });

        newMarkers.push(marker);
    });

    currentMarkers = newMarkers;

    // 自动调整地图视野以包含所有点
    if (pois.length > 0) {
        const bounds = new AMap.Bounds();
        pois.forEach(p => {
            if(p.lon && p.lat) bounds.extend([p.lon, p.lat]);
        });
        map.setBounds(bounds);
    }
}

// 清除当前所有标记
function clearMarkers() {
    if (currentMarkers.length > 0) {
        map.remove(currentMarkers);
        currentMarkers = [];
    }
    // 同时清除可能存在的框选工具
    if (rectangleTool) {
        map.remove(rectangleTool);
        rectangleTool = null;
    }
    document.getElementById('rangeHint').style.display = 'none';
}


// ====== 列表展示 ======
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


// ====== 范围查询(占位) ======
function startRangeQuery() {
    alert("范围查询功能开发中...请确保引入了高德 MouseTool 插件");
    // 如果需要实现，需要在 HTML head 中引入 plugin=AMap.MouseTool
}

// 暴露函数给全局（防止 HTML onclick 找不到）
window.searchByKeyword = searchByKeyword;
window.clearMarkers = clearMarkers;
window.startRangeQuery = startRangeQuery;