// ====== 初始化地图 ======
// 此时 AMap 对象已经在 HTML 中通过外部链接加载完毕，可以直接使用
let map = new AMap.Map('container', {
    zoom: 11,
    center: [114.3, 30.58], // 武汉中心
    viewMode: '2D'
});

let currentMarkers = [];
let infoWindow = new AMap.InfoWindow({ offset: new AMap.Pixel(0, -10) });
let rectangleTool = null;
let isSelecting = false;
let startPoint = null;

// ====== 加载初始POI数据 ======
// 页面加载时自动请求一次空查询
document.addEventListener('DOMContentLoaded', function() {
    fetch('/api/search?q=')
        .then(res => res.json())
        .then(data => addMarkers(data))
        .catch(err => console.error("初始化数据加载失败:", err));
});

// 添加标记到地图
function addMarkers(pois) {
    clearMarkers();
    let markers = [];
    pois.forEach(poi => {
        const marker = new AMap.Marker({
            position: [poi.lon, poi.lat],
            title: poi.name
        });

        const content = `<div><strong>${poi.name}</strong><br>${poi.type} | ${poi.district}</div>`;

        marker.on('click', () => {
            infoWindow.setContent(content);
            infoWindow.open(map, marker.getPosition());
        });

        marker.setMap(map);
        markers.push(marker);
    });
    currentMarkers = markers;

    if (pois.length > 0) {
        const bounds = new AMap.Bounds();
        pois.forEach(p => bounds.extend([p.lon, p.lat]));
        map.setBounds(bounds, 50);
    }
}

// 属性查询
function searchByKeyword() {
    const q = document.getElementById('keyword').value.trim();
    if (!q) return;
    fetch(`/api/search?q=${encodeURIComponent(q)}`)
        .then(res => res.json())
        .then(data => {
            addMarkers(data);
            showResults(data, '属性查询结果');
        })
        .catch(err => console.error("查询失败:", err));
}

// 🔘 范围查询：点击按钮后进入绘制模式
function startRangeQuery() {
    if (rectangleTool) {
        map.remove(rectangleTool);
        rectangleTool = null;
    }
    isSelecting = true;
    document.getElementById('rangeHint').style.display = 'block';
    // 注意：你原始代码中缺少实际的鼠标拖拽(MouseTool)逻辑，
    // 这里仅保留了你原始的状态切换代码。
}

// 清除标记
function clearMarkers() {
    currentMarkers.forEach(m => m.setMap(null));
    currentMarkers = [];
    if (rectangleTool) {
        map.remove(rectangleTool);
        rectangleTool = null;
    }
    isSelecting = false;
    startPoint = null;
    document.getElementById('rangeHint').style.display = 'none';
}

// 显示属性查询结果
function showResults(items, title) {
    let html = `<h5>${title} (${items.length} 条)</h5>`;
    if (items.length === 0) {
        html += '<p>未找到匹配结果。</p>';
    } else {
        html += '<div class="list-group">';
        items.forEach(item => {
            html += `
                <div class="result-item">
                    <strong>${item.name}</strong><br>
                    <small>${item.type} · ${item.district}</small>
                </div>`;
        });
        html += '</div>';
    }
    document.getElementById('results').innerHTML = html;
}

// 暴露函数给全局（供 HTML 中的 onclick 调用）
window.searchByKeyword = searchByKeyword;
window.clearMarkers = clearMarkers;
window.startRangeQuery = startRangeQuery;