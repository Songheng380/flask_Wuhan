// 全局变量
let map = null;
let currentLayerGroup = L.layerGroup();
let currentImageOverlay = null;
let currentLayerName = null;
let currentLayerData = null;  // 当前图层的 GeoJSON
let resultMarkers = [];

// 统一更新“查询结果”右上角的统计信息
function updateStats(sourceLabel, data) {
    const statEl = document.getElementById('resultStats');
    if (!statEl) return;  // 防止页面上没有该元素时报错

    const count = (data && typeof data.count === 'number')
        ? data.count
        : (data && typeof data.length === 'number'
            ? data.length
            : 0);

    const elapsed = (data && typeof data.elapsed_ms === 'number')
        ? data.elapsed_ms.toFixed(2)
        : '—';

    statEl.textContent = `${sourceLabel} | ${count} 条 | ${elapsed} ms`;
}

// 查询开始时的提示
function showQueryLoading(label) {
    const statEl = document.getElementById('resultStats');
    if (!statEl) return;
    statEl.textContent = `${label}中...`;
}

// 初始化 Leaflet 地图
function initMap() {
    map = L.map('map');

    // 添加 OpenStreetMap 底图
    L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
        attribution: '© OpenStreetMap contributors',
        maxZoom: 19
    }).addTo(map);

    // 初始视图：武汉近似范围
    const wuhanBounds = [[29.9, 113.8], [31.0, 114.7]];
    map.fitBounds(wuhanBounds, {padding: [20, 20]});

    // 添加图层组
    currentLayerGroup.addTo(map);

    // 加载图层列表
    loadLayerList();
    
    // 绑定回车键搜索
    document.getElementById('keyword').addEventListener('keypress', function(e){
        if(e.key === 'Enter') searchByKeyword();
    });
}

// 加载图层列表到下拉菜单
function loadLayerList(){
    fetch('/api/layers')
        .then(r => r.json())
        .then(data => {
            const sel = document.getElementById('layerSelect');
            data.forEach(item => {
                const opt = document.createElement('option');
                opt.value = item.name;
                opt.text = `${item.name} [${item.type}]`;
                sel.appendChild(opt);
            });
        })
        .catch(err => console.error('Failed to load layers:', err));
}

// 图层选择改变
document.addEventListener('DOMContentLoaded', function(){
    initMap();
    
    document.getElementById('layerSelect').addEventListener('change', function(){
        const name = this.value;
        currentLayerName = name;
        currentLayerData = null;
        
        if(name === '__none__'){
            clearMapLayers();
            return;
        }
        
        clearMapLayers();
        clearResults();
        
        // 尝试作为矢量
        fetch(`/api/geojson/${name}`)
            .then(r => {
                if(r.status === 200) return r.json();
                throw new Error('not vector');
            })
            .then(geojson => {
                currentLayerData = geojson;
                const gj = L.geoJSON(geojson, {
                    style: function(feature){
                        return {color: '#3388ff', weight: 2, fillOpacity: 0.2};
                    },
                    pointToLayer: function(feature, latlng){
                        return L.circleMarker(latlng, {
                            radius: 6,
                            fillColor: '#ff5722',
                            color: '#fff',
                            weight: 1,
                            fillOpacity: 0.9
                        });
                    },
                    onEachFeature: function(feature, layer){
                        let popupContent = '<div style="max-width: 200px;">';
                        if(feature.properties){
                            const props = feature.properties;
                            let name = props.name || props.Name || props.NAME || props['名称'] || '(无名称)';
                            popupContent += `<b>${name}</b><br>`;
                            for(let key in props){
                                if(key.toLowerCase() !== 'name' && props[key]){
                                    const val = String(props[key]);
                                    if(val.length < 100){
                                        popupContent += `<small><b>${key}:</b> ${val}</small><br>`;
                                    }
                                }
                            }
                        }
                        popupContent += '</div>';
                        layer.bindPopup(popupContent);
                        layer.on('click', function(){
                            this.openPopup();
                        });
                    }
                }).addTo(currentLayerGroup);
                
                try {
                    map.fitBounds(gj.getBounds(), {padding: [20, 20]});
                } catch(e){}
            })
            .catch(() => {
                // 尝试作为栅格
                fetch(`/api/imagery/${name}`)
                    .then(r => r.json())
                    .then(info => {
                        if(info && info.url && info.bounds){
                            const bounds = [[info.bounds[0][0], info.bounds[0][1]], 
                                          [info.bounds[1][0], info.bounds[1][1]]];
                            currentImageOverlay = L.imageOverlay(info.url, bounds).addTo(map);
                            map.fitBounds(bounds, {padding: [20, 20]});
                        }
                    })
                    .catch(err => console.error('Failed to load imagery:', err));
            });
    });
});

// 清除地图图层
function clearMapLayers(){
    currentLayerGroup.clearLayers();
    if(currentImageOverlay){
        map.removeLayer(currentImageOverlay);
        currentImageOverlay = null;
    }
}

// 按关键词搜索
function searchByKeyword(){
    const kw = document.getElementById('keyword').value.trim();
    if(!kw) {
        alert('请输入关键词');
        return;
    }
    
    // 如果选中了矢量图层，从该图层中查询
    if(currentLayerData && currentLayerData.features){
        const mode = document.querySelector('input[name="queryMode"]:checked').value;

        // 查询开始提示
        showQueryLoading('属性查询');

        const t0 = performance.now();

        const results = currentLayerData.features.filter(feature => {
            if(!feature.properties) return false;
            const props = feature.properties;

            if(mode === 'exact'){
                return Object.values(props).some(v => String(v).toLowerCase() === kw.toLowerCase());
            } else {
                return Object.values(props).some(v => String(v).toLowerCase().includes(kw.toLowerCase()));
            }
        });

        const elapsed = performance.now() - t0;

        // 更新耗时和条数（前端统计）
        updateStats('属性查询', {
            count: results.length,
            elapsed_ms: elapsed
        });

        displayLayerSearchResults(results, kw);
    } else if(currentLayerName && currentLayerName !== '__none__'){
        alert('当前图层不支持查询或未完全加载，请选择矢量图层');
    }
}

// 显示图层查询结果
function displayLayerSearchResults(features, keyword){
    clearResults();
    clearMapLayers();
    
    if(features.length === 0){
        document.getElementById('results').innerHTML = '<div style="color: red;">未找到匹配的要素</div>';
        return;
    }
    
    // 重新绘制，高亮搜索结果
    const gj = L.geoJSON(currentLayerData, {
        style: function(feature){
            const isResult = features.includes(feature);
            if(isResult){
                return {color: '#ff0000', weight: 3, fillOpacity: 0.5};
            } else {
                return {color: '#3388ff', weight: 1, fillOpacity: 0.1};
            }
        },
        pointToLayer: function(feature, latlng){
            const isResult = features.includes(feature);
            if(isResult){
                return L.circleMarker(latlng, {radius: 8, fillColor: '#ff0000', color: '#fff', weight: 2, fillOpacity: 1.0});
            } else {
                return L.circleMarker(latlng, {radius: 5, fillColor: '#999', color: '#fff', weight: 1, fillOpacity: 0.5});
            }
        },
        onEachFeature: function(feature, layer){
            let popupContent = '<div style="max-width: 200px;">';
            if(feature.properties){
                const props = feature.properties;
                let name = props.name || props.Name || props.NAME || props['名称'] || '(无名称)';
                popupContent += `<b>${name}</b><br>`;
                for(let key in props){
                    if(key.toLowerCase() !== 'name' && props[key]){
                        const val = String(props[key]);
                        if(val.length < 100){
                            popupContent += `<small><b>${key}:</b> ${val}</small><br>`;
                        }
                    }
                }
            }
            popupContent += '</div>';
            layer.bindPopup(popupContent);
            layer.on('click', function(){
                this.openPopup();
            });
        }
    }).addTo(currentLayerGroup);
    
    // 缩放到结果
    try {
        const bounds = gj.getBounds();
        if(bounds.isValid()){
            map.fitBounds(bounds, {padding: [20, 20]});
        }
    } catch(e){}
    
    // 显示结果列表
    const html = features.map(f => {
        let name = '(无名称)';
        if(f.properties){
            name = f.properties.name || f.properties.Name || f.properties.NAME || f.properties['名称'] || '(无名称)';
        }
        return `<div class="result-item" style="background: #ffe6e6; padding: 4px; border-radius: 3px;">
                    <b>${name}</b>
                </div>`;
    }).join('');
    document.getElementById('results').innerHTML = `<div style="font-weight: bold; margin-bottom: 8px;">找到 ${features.length} 个结果:</div>${html}`;
}

// 清除结果
function clearResults(){
    document.getElementById('results').innerHTML = '<div class="text-muted">未执行查询</div>';

    const statEl = document.getElementById('resultStats');
    if (statEl) {
        statEl.textContent = '未执行查询';
    }
}

// 框选查询
let boxStart = null;
let boxRect = null;
function startBoxSelect(){
    if(!currentLayerName || currentLayerName === '__none__'){
        alert('请先选择一个图层');
        return;
    }
    
    document.getElementById('boxHint').style.display = 'block';
    map.dragging.disable();  // 禁用地图拖拽
    map.getContainer().style.cursor = 'crosshair';
    
    function onMouseDown(e){
        boxStart = e.latlng;
        if(boxRect) map.removeLayer(boxRect);
        boxRect = null;
        map.on('mousemove', onMouseMove);
    }
    
    function onMouseMove(e){
        if(!boxStart) return;
        
        if(boxRect) {
            map.removeLayer(boxRect);
        }
        
        boxRect = L.rectangle([boxStart, e.latlng], {
            color: '#ffaa00',
            weight: 2,
            fillColor: '#ffbb33',
            fillOpacity: 0.2
        }).addTo(map);
    }
    
    function onMouseUp(e){
        map.off('mousemove', onMouseMove);
        map.off('mousedown', onMouseDown);
        map.off('mouseup', onMouseUp);
        map.dragging.enable();  // 恢复地图拖拽
        map.getContainer().style.cursor = '';
        document.getElementById('boxHint').style.display = 'none';
        
        if(!boxStart || !boxRect) return;
        
        const b = boxRect.getBounds();
        const min_lon = b.getWest();
        const min_lat = b.getSouth();
        const max_lon = b.getEast();
        const max_lat = b.getNorth();
        
        // 移除矩形
        if(boxRect) {
            map.removeLayer(boxRect);
            boxRect = null;
        }
        
        // 在当前图层中执行范围查询
        if(currentLayerData && currentLayerData.features){

            showQueryLoading('范围查询');

            const t0 = performance.now();

            const results = currentLayerData.features.filter(feature => {
                if(!feature.geometry) return false;

                const geomType = feature.geometry.type;
                const coords = feature.geometry.coordinates;

                if(geomType === 'Point'){
                    // Point: [lon, lat]
                    const lon = coords[0];
                    const lat = coords[1];
                    return lon >= min_lon && lon <= max_lon && lat >= min_lat && lat <= max_lat;
                } else if(geomType === 'LineString' || geomType === 'Polygon'){
                    // 检查是否与矩形相交
                    return checkGeometryInBounds(coords, geomType, min_lon, min_lat, max_lon, max_lat);
                } else if(geomType === 'MultiPoint' || geomType === 'MultiLineString' || geomType === 'MultiPolygon'){
                    // 检查任意一部分是否在范围内
                    return coords.some(c => checkGeometryInBounds(c, geomType.replace('Multi', ''), min_lon, min_lat, max_lon, max_lat));
                }
                return false;
            });

            const elapsed = performance.now() - t0;

            // 更新耗时和条数（前端统计）
            updateStats('范围查询', {
                count: results.length,
                elapsed_ms: elapsed
            });

            displayLayerSearchResults(results, '矩形范围内');
        }
        
        boxStart = null;
    }
    
    map.on('mousedown', onMouseDown);
    map.on('mouseup', onMouseUp);
}

// 全局函数暴露
window.searchByKeyword = searchByKeyword;
window.startBoxSelect = startBoxSelect;
window.clearResults = clearResults;

// 辅助函数：检查几何图形是否与矩形范围相交
function checkGeometryInBounds(coords, geomType, min_lon, min_lat, max_lon, max_lat){
    if(geomType === 'LineString'){
        // LineString: [[lon, lat], [lon, lat], ...]
        return coords.some(point => {
            const lon = point[0];
            const lat = point[1];
            return lon >= min_lon && lon <= max_lon && lat >= min_lat && lat <= max_lat;
        });
    } else if(geomType === 'Polygon'){
        // Polygon: [[[lon, lat], [lon, lat], ...]]
        return coords[0].some(point => {
            const lon = point[0];
            const lat = point[1];
            return lon >= min_lon && lon <= max_lon && lat >= min_lat && lat <= max_lat;
        });
    }
    return false;
}
