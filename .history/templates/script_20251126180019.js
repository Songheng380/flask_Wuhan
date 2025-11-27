// ====== 初始化地图 ======
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
// 注意：如果您的本地环境没有搭建后端 /api/search 接口，这行代码可能会报错
fetch('/api/search?q=')
    .then(res => res.json())
    .then(data => addMarkers(data))
    .catch(err => console.log('初始化数据加载失败或无接口:', err));

// 添加标记到地图
function addMarkers(pois) {
    clearMarkers();
    let markers = [];
    if (!pois) return; // 防止数据为空时报错

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
        .catch(err => alert('查询接口调用失败'));
}

// 🔘 范围查询：点击按钮后进入绘制模式
function startRangeQuery() {
    if (rectangleTool) {
        map.remove(rectangleTool);
        rectangleTool = null;
    }
    isSelecting = true;
    document.getElementById('rangeHint').style.display = 'block';
}