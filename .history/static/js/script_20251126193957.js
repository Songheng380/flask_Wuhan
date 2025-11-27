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

// ====== 通用数据请求函数 (调试版) ======
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
            console.log("🔥 后端返回的原始数据 (前1条):", data[0]); // 关键：看这里！
            
            // 1. 清除旧标记
            clearMarkers();
            // 2. 添加新标记 (这一步最容易报错)
            addMarkers(data);
            // 3. 更新列表
            showResults(data, query ? `"${query}" 的搜索结果` : '全部数据');
        })
        .catch(error => {
            // 只有真正的严重错误才弹窗
            console.error("❌ 严重错误:", error);
            alert("发生错误: " + error.message);
        });
}

// ====== 地图标记操作 (防崩溃版) ======
function addMarkers(pois) {
    if (!map) return;

    let newMarkers = [];
    let validBounds = new AMap.Bounds();
    let hasValidData = false;

    pois.forEach((poi, index) => {
        try {
            // === 关键修改：自动尝试多种字段名 ===
            // 有的数据库叫 lon，有的叫 lng，有的叫 x
            let rawLon = poi.lon || poi.lng || poi.x || poi.longitude;
            let rawLat = poi.lat || poi.y || poi.latitude;

            let lon = parseFloat(rawLon);
            let lat = parseFloat(rawLat);

            // 检查转换后是否还是 NaN
            if (isNaN(lon) || isNaN(lat)) {
                // 只有遇到坏数据时才在控制台警告，不中断程序
                console.warn(`⚠️ 第 ${index} 条数据坐标无效 (lon:${rawLon}, lat:${rawLat})，已跳过。`);
                return; 
            }

            const marker = new AMap.Marker({
                position: [lon, lat],
                title: poi.name,
                map: map
            });

            // 内容展示防空判断
            const name = poi.name || "无名称";
            const type = poi.type || "未知类型";
            const district = poi.district || "";

            const content = `
                <div style="padding:5px;">
                    <strong>${name}</strong><br>
                    <span style="color:#666;font-size:12px;">${type} | ${district}</span>
                </div>`;

            marker.on('click', () => {
                infoWindow.setContent(content);
                infoWindow.open(map, marker.getPosition());
            });

            newMarkers.push(marker);
            validBounds.extend([lon, lat]);
            hasValidData = true;

        } catch (err) {
            console.error(`第 ${index} 条数据创建标记失败:`, err);
            // 捕获错误，保证循环继续执行，不会触发外部的 catch
        }
    });

    currentMarkers = newMarkers;

    if (hasValidData) {
        map.setBounds(validBounds);
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