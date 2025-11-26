// script.js

// 全局变量
let map = null;
let currentMarkers = [];
let infoWindow = null;
let currentRectangle = null; // 用于存储绘制的矩形
let isDrawing = false; // 是否处于绘制模式
let startLngLat = null; // 绘制起始点
const resultsDiv = document.getElementById('results');

// 监听页面加载完成，执行初始化
window.onload = function() {
    // 初始化地图
    map = new AMap.Map('container', {
        zoom: 11,
        center: [114.3, 30.58], // 武汉中心
        viewMode: '2D'
    });

    infoWindow = new AMap.InfoWindow({ offset: new AMap.Pixel(0, -10) });

    // 默认加载一些初始 POI 数据 (这里使用一个假接口)
    // 实际项目中需要替换为真实的后端 API
    // fetch('/api/search?q=')
    //     .then(res => res.json())
    //     .then(data => addMarkers(data));

    // 假设的初始化数据，用于演示
    const initialData = [
        { name: '武汉大学', type: '高等院校', district: '武昌区', lon: 114.36, lat: 30.54 },
        { name: '华中科技大学', type: '高等院校', district: '洪山区', lon: 114.41, lat: 30.51 }
    ];
    addMarkers(initialData);

    // 范围查询的鼠标事件监听
    map.on('mousedown', handleMapMousedown);
    map.on('mousemove', handleMapMousemove);
    map.on('mouseup', handleMapMouseup);
};


// ====== 核心功能函数 ======

// 添加标记到地图
function addMarkers(pois) {
    clearMarkers();
    if (!map) return;

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

    // 缩放到所有点
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

    // 假装调用后端 API 获取数据
    const mockData = mockSearchApi(q);
    addMarkers(mockData);
    showResults(mockData, `属性查询结果：${q}`);
}

// 🔘 范围查询：点击按钮后进入绘制模式
function startRangeQuery() {
    // 清除上一次的矩形和标记
    clearMapDrawing(); 
    document.getElementById('rangeHint').style.display = 'block';
    isDrawing = true;
    map.setStatus({ dragEnable: false }); // 禁用地图拖拽，方便框选
    alert('请在地图上按住鼠标左键拖拽绘制区域！'); // 提示用户
}

// 清除所有标记和绘制的矩形
function clearAll() {
    clearMarkers();
    clearMapDrawing();
    resultsDiv.innerHTML = '';
}

// 清除地图上的绘制物 (矩形)
function clearMapDrawing() {
    currentMarkers.forEach(m => m.setMap(null)); // 清除标记
    currentMarkers = [];
    if (currentRectangle) {
        map.remove(currentRectangle);
        currentRectangle = null;
    }
    isDrawing = false;
    startLngLat = null;
    document.getElementById('rangeHint').style.display = 'none';
    map.setStatus({ dragEnable: true }); // 启用地图拖拽
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
    resultsDiv.innerHTML = html;
}

// ====== 范围查询的鼠标事件处理 ======

function handleMapMousedown(e) {
    if (!isDrawing) return;
    startLngLat = e.lnglat;
    if (currentRectangle) {
        map.remove(currentRectangle); // 清除旧矩形
    }
}

function handleMapMousemove(e) {
    if (!isDrawing || !startLngLat) return;

    // 实时绘制矩形
    const endLngLat = e.lnglat;
    const bounds = new AMap.Bounds(startLngLat, endLngLat);
    
    if (!currentRectangle) {
        currentRectangle = new AMap.Rectangle({
            bounds: bounds,
            strokeColor: "#FF33FF",
            strokeWeight: 2,
            strokeOpacity: 0.8,
            fillColor: '#1791fc',
            fillOpacity: 0.35,
            map: map
        });
    } else {
        currentRectangle.setBounds(bounds);
    }
}

function handleMapMouseup(e) {
    if (!isDrawing || !startLngLat) return;
    
    isDrawing = false;
    document.getElementById('rangeHint').style.display = 'none';
    map.setStatus({ dragEnable: true }); // 重新启用地图拖拽

    // 最终的矩形范围
    const bounds = new AMap.Bounds(startLngLat, e.lnglat);
    const southwest = bounds.getSouthWest();
    const northeast = bounds.getNorthEast();

    // 假设的范围查询 API 调用
    const mockData = mockRangeApi(southwest, northeast);
    addMarkers(mockData);
    showResults(mockData, `范围查询结果`);
}


// ====== 模拟 API (替换为您真实的后端接口) ======

// 模拟属性查询结果
function mockSearchApi(query) {
    const allData = [
        { name: '武汉大学', type: '高等院校', district: '武昌区', lon: 114.36, lat: 30.54 },
        { name: '华中科技大学', type: '高等院校', district: '洪山区', lon: 114.41, lat: 30.51 },
        { name: '湖北省博物馆', type: '博物馆', district: '武昌区', lon: 114.35, lat: 30.58 },
        { name: '黄鹤楼', type: '风景名胜', district: '武昌区', lon: 114.31, lat: 30.54 }
    ];
    
    if (query === '学校') {
        return allData.filter(item => item.type === '高等院校');
    }
    return allData.filter(item => item.name.includes(query) || item.type.includes(query));
}

// 模拟范围查询结果
function mockRangeApi(sw, ne) {
    const allData = [
        { name: '武汉大学', type: '高等院校', district: '武昌区', lon: 114.36, lat: 30.54 },
        { name: '华中科技大学', type: '高等院校', district: '洪山区', lon: 114.41, lat: 30.51 },
        { name: '湖北省博物馆', type: '博物馆', district: '武昌区', lon: 114.35, lat: 30.58 },
        { name: '黄鹤楼', type: '风景名胜', district: '武昌区', lon: 114.31, lat: 30.54 }
    ];

    // 简单判断点是否在矩形内
    return allData.filter(item => {
        const lng = item.lon;
        const lat = item.lat;
        return (lng >= sw.lng && lng <= ne.lng && lat >= sw.lat && lat <= ne.lat) ||
               (lng >= ne.lng && lng <= sw.lng && lat >= ne.lat && lat <= sw.lat);
    });
}


// 暴露函数给全局 (供 HTML 中的 onclick 调用)
window.searchByKeyword = searchByKeyword;
window.startRangeQuery = startRangeQuery;
window.clearAll = clearAll;