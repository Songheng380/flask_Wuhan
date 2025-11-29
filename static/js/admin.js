// 当前页码与选中的POI类型
let currentPage = 1;
let currentPoiType = 'wuhanmetro';
let currentEditId = null;
let currentDeleteId = null;

// 所有POI类型配置
const POI_CONFIG = {
    publicservices: {
        label: "公共服务",
        apiPrefix: "/admin/publicservices",
        primaryKey: "fid",
        tableColumns: [
            { key: "fid", label: "ID" },
            { key: "name", label: "名称" },
            { key: "type", label: "类型" },
            { key: "district", label: "区域" },
            { key: "address", label: "地址" },
            { key: "operate", label: "操作" }
        ],
        formFields: [
            { key: "name", label: "名称", type: "text", required: true },
            { key: "type", label: "类型", type: "text", required: true },
            { key: "district", label: "区域", type: "text" },
            { key: "address", label: "地址", type: "text" },
            { key: "longitude", label: "经度", type: "number", step: "0.000001", required: true },
            { key: "latitude", label: "纬度", type: "number", step: "0.000001", required: true }
        ]
    },
    wuhanmetro: {
        label: "武汉市地铁站点",
        apiPrefix: "/admin/wuhanmetro",
        primaryKey: "ogc_fid",
        tableColumns: [
            { key: "ogc_fid", label: "ID" },
            { key: "name", label: "站点名称" },
            { key: "line", label: "线路" },
            { key: "color", label: "线路颜色" },
            { key: "transfer", label: "换乘信息" },
            { key: "operate", label: "操作" }
        ],
        formFields: [
            { key: "name", label: "站点名称", type: "text", required: true },
            { key: "line", label: "线路", type: "text", required: true },
            { key: "color", label: "线路颜色", type: "text" },
            { key: "transfer", label: "换乘信息", type: "text" },
            { key: "longitude", label: "经度", type: "number", step: "0.000001", required: true },
            { key: "latitude", label: "纬度", type: "number", step: "0.000001", required: true }
        ]
    },
    wuhanmiddleschool: {
        label: "武汉市中学",
        apiPrefix: "/admin/wuhanmiddleschool",
        primaryKey: "ogc_fid",
        tableColumns: [
            { key: "ogc_fid", label: "ID" },
            { key: "name", label: "学校名称" },
            { key: "related_address", label: "地址" },
            { key: "longitude", label: "经度" },
            { key: "latitude", label: "纬度" },
            { key: "operate", label: "操作" }
        ],
        formFields: [
            { key: "name", label: "学校名称", type: "text", required: true },
            { key: "related_address", label: "地址", type: "text" },
            { key: "longitude", label: "经度", type: "number", step: "0.000001", required: true },
            { key: "latitude", label: "纬度", type: "number", step: "0.000001", required: true }
        ]
    },
    wuhanprimaryschool: {
        label: "武汉市小学",
        apiPrefix: "/admin/wuhanprimaryschool",
        primaryKey: "ogc_fid",
        tableColumns: [
            { key: "ogc_fid", label: "ID" },
            { key: "name", label: "学校名称" },
            { key: "related_address", label: "地址" },
            { key: "longitude", label: "经度" },
            { key: "latitude", label: "纬度" },
            { key: "operate", label: "操作" }
        ],
        formFields: [
            { key: "name", label: "学校名称", type: "text", required: true },
            { key: "related_address", label: "地址", type: "text" },
            { key: "longitude", label: "经度", type: "number", step: "0.000001", required: true },
            { key: "latitude", label: "纬度", type: "number", step: "0.000001", required: true }
        ]
    },
    wuhanmetroline: {
        label: "武汉市地铁线路",
        apiPrefix: "/admin/wuhanmetroline",
        primaryKey: "ogc_fid",
        tableColumns: [
            { key: "ogc_fid", label: "ID" },
            { key: "name", label: "线路名称" },
            { key: "layer", label: "图层信息" },
            { key: "origin", label: "始发站" },
            { key: "destination", label: "终点站" },
            { key: "operate", label: "操作" }
        ],
        formFields: [
            { key: "name", label: "线路名称", type: "text", required: true },
            { key: "layer", label: "图层信息", type: "text" },
            { key: "origin", label: "始发站", type: "text" },
            { key: "destination", label: "终点站", type: "text" },
            { key: "coordinates", label: "线路坐标", type: "textarea", required: true,
              placeholder: "格式: [[x1,y1], [x2,y2], ...]（至少2个点，英文逗号分隔）" }
        ]
    },
    metro10mincircle: {
        label: "地铁十分钟等时圈",
        apiPrefix: "/admin/metro10mincircle",
        primaryKey: "fid",
        tableColumns: [
            { key: "fid", label: "ID" },
            { key: "name", label: "等时圈名称" },
            { key: "id", label: "标识ID" },
            { key: "center_lon", label: "中心经度" },
            { key: "center_lat", label: "中心纬度" },
            { key: "aa_mins", label: "等时时间" },
            { key: "aa_mode", label: "交通方式" },
            { key: "total_pop", label: "覆盖人口" },
            { key: "operate", label: "操作" }
        ],
        formFields: [
            { key: "name", label: "等时圈名称", type: "text", required: true },
            { key: "id", label: "标识ID", type: "text" },
            { key: "center_lon", label: "中心经度", type: "number", step: "0.000001", required: true },
            { key: "center_lat", label: "中心纬度", type: "number", step: "0.000001", required: true },
            { key: "aa_mins", label: "等时时间", type: "text", defaultValue: "10" },
            { key: "aa_mode", label: "交通方式", type: "text", defaultValue: "地铁" },
            { key: "total_pop", label: "覆盖人口", type: "text" },
            { key: "coordinates", label: "面要素坐标", type: "textarea", required: true,
              placeholder: "格式: [[[x1,y1], [x2,y2], ..., [x1,y1]]]（闭合多边形，至少3个点）" }
        ]
    }
};

// 初始化页面
document.addEventListener('DOMContentLoaded', () => {
    // 绑定POI类型切换事件
    document.getElementById('poiType').addEventListener('change', (e) => {
        currentPoiType = e.target.value;
        currentPage = 1;
        // 切换类型时先渲染表头
        renderTableHeader();
        loadData(currentPage);
    });

    // 绑定搜索按钮事件
    document.getElementById('searchBtn').addEventListener('click', () => {
        currentPage = 1;
        loadData(currentPage);
    });

    // 绑定新增按钮事件
    document.getElementById('addBtn').addEventListener('click', openAddModal);

    // 绑定测试数据库连接按钮事件
    document.getElementById('testDbBtn').addEventListener('click', async () => {
        const btn = document.getElementById('testDbBtn');
        btn.disabled = true;
        btn.innerHTML = '<i class="bi bi-hourglass-split"></i> 测试中...';

        try {
            const response = await fetch('http://127.0.0.1:5000/api/test_db');
            const result = await response.json();

            if (result.code === 200) {
                alert('数据库连接成功！');
            } else {
                alert('数据库连接失败：' + result.msg);
            }
        } catch (error) {
            alert('请求失败：' + error.message);
        } finally {
            btn.disabled = false;
            btn.innerHTML = '<i class="bi bi-database-check"></i> 测试数据库连接';
        }
    });

    // 初始化时先渲染表头
    renderTableHeader();

    // 初始化加载数据
    loadData(currentPage);
});

// 渲染表格表头
function renderTableHeader() {
    const config = POI_CONFIG[currentPoiType];
    const tableHeader = document.getElementById('tableHeader');
    tableHeader.innerHTML = ''; // 清空原有表头

    // 根据配置渲染表头列
    config.tableColumns.forEach(col => {
        const th = document.createElement('th');
        th.textContent = col.label;
        tableHeader.appendChild(th);
    });
}

// 加载数据列表
async function loadData(page) {
    const config = POI_CONFIG[currentPoiType];
    const keyword = document.getElementById('searchInput').value.trim();
    const tableBody = document.getElementById('dataTableBody');
    const pageNumberContainer = document.getElementById('pageNumberContainer');
    const prevPageBtn = document.getElementById('prevPageBtn');
    const nextPageBtn = document.getElementById('nextPageBtn');

    try {
        // 构建请求URL
        const url = new URL(`${config.apiPrefix}/search`, window.location.origin);
        url.searchParams.set('page', page);
        url.searchParams.set('pageSize', 15);
        url.searchParams.set('q', keyword);

        const response = await fetch(url);
        const result = await response.json();

        if (result.data) {
            // 渲染表格（保持不变）
            tableBody.innerHTML = '';
            result.data.forEach(item => {
                const row = document.createElement('tr');
                config.tableColumns.forEach(col => {
                    const td = document.createElement('td');
                    if (col.key === 'operate') {
                        td.innerHTML = `
                            <button class="btn btn-sm btn-primary" onclick="openEditModal(${item[config.primaryKey]})">编辑</button>
                            <button class="btn btn-sm btn-danger" onclick="openDeleteModal(${item[config.primaryKey]})">删除</button>
                        `;
                    } else {
                        td.textContent = col.format ? col.format(item[col.key]) : item[col.key] || '';
                    }
                    row.appendChild(td);
                });
                tableBody.appendChild(row);
            });

            // 渲染分页
            const totalPages = Math.ceil(result.total / 15);
            pageNumberContainer.innerHTML = '';

            // 上一页按钮状态
            prevPageBtn.disabled = page <= 1;
            prevPageBtn.onclick = () => page > 1 && loadData(page - 1);

            // 下一页按钮状态
            nextPageBtn.disabled = page >= totalPages;
            nextPageBtn.onclick = () => page < totalPages && loadData(page + 1);

            // 首页按钮
            const firstPageBtn = document.createElement('button');
            firstPageBtn.className = 'btn btn-sm btn-outline-secondary';
            firstPageBtn.textContent = '首页';
            firstPageBtn.disabled = page === 1;
            firstPageBtn.onclick = () => loadData(1);
            pageNumberContainer.appendChild(firstPageBtn);

            // 计算显示的页码范围（当前页±2，且不小于1、不大于总页数）
            const startPage = Math.max(1, page - 2);
            const endPage = Math.min(totalPages, page + 2);

            // 显示中间页码
            for (let i = startPage; i <= endPage; i++) {
                const pageBtn = document.createElement('button');
                pageBtn.className = `btn btn-sm ${i === page ? 'btn-secondary' : 'btn-outline-secondary'}`;
                pageBtn.textContent = i;
                pageBtn.style.minWidth = '30px';
                pageBtn.onclick = () => loadData(i);
                pageNumberContainer.appendChild(pageBtn);
            }

            // 尾页按钮
            const lastPageBtn = document.createElement('button');
            lastPageBtn.className = 'btn btn-sm btn-outline-secondary';
            lastPageBtn.textContent = '尾页';
            lastPageBtn.disabled = page === totalPages;
            lastPageBtn.onclick = () => loadData(totalPages);
            pageNumberContainer.appendChild(lastPageBtn);

            // 显示/隐藏空数据提示
            document.getElementById('emptyTip').classList.add('d-none');
        } else {
            tableBody.innerHTML = '';
            document.getElementById('emptyTip').classList.remove('d-none');
            pageNumberContainer.innerHTML = '';
            prevPageBtn.disabled = true;
            nextPageBtn.disabled = true;
        }
    } catch (error) {
        console.error('加载数据失败:', error);
        tableBody.innerHTML = '';
        document.getElementById('emptyTip').classList.remove('d-none');
        document.getElementById('emptyTip').innerHTML = `
            <i class="bi bi-exclamation-circle text-danger fs-3"></i>
            <p class="text-danger mt-2">加载失败，请重试</p>
        `;
    }
}

// 初始化页面（调整分页按钮绑定）
document.addEventListener('DOMContentLoaded', () => {
    // 原绑定逻辑保持不变...

    // 分页按钮初始禁用
    document.getElementById('prevPageBtn').disabled = true;
    document.getElementById('nextPageBtn').disabled = true;
});

// 打开新增模态框
function openAddModal() {
    currentEditId = null;
    const config = POI_CONFIG[currentPoiType];
    const modalTitle = document.getElementById('editModalLabel');
    const formEl = document.getElementById('editForm');

    modalTitle.textContent = `新增${config.label}`;
    formEl.innerHTML = '';

    // 渲染表单字段
    config.formFields.forEach(field => {
        formEl.innerHTML += `
            <div class="mb-3">
                <label for="form-${field.key}" class="form-label">
                    ${field.label} ${field.required ? '<span class="text-danger">*</span>' : ''}
                </label>
                ${field.type === 'textarea' ? 
                    `<textarea class="form-control" id="form-${field.key}" 
                              ${field.required ? 'required' : ''}
                              placeholder="${field.placeholder || ''}"
                              rows="4"></textarea>` : 
                    `<input type="${field.type}" class="form-control" id="form-${field.key}" 
                           ${field.required ? 'required' : ''}
                           placeholder="${field.placeholder || ''}"
                           value="${field.defaultValue || ''}">`
                }
            </div>
        `;
    });

    $('#editModal').modal('show');
}

// 打开编辑模态框
async function openEditModal(id) {
    currentEditId = id;
    const config = POI_CONFIG[currentPoiType];
    const modalTitle = document.getElementById('editModalLabel');
    const formEl = document.getElementById('editForm');

    modalTitle.textContent = `编辑${config.label}`;
    formEl.innerHTML = '';

    try {
        const response = await fetch(`${config.apiPrefix}/get?id=${id}`);
        const result = await response.json();

        if (result.code === 200 && result.data) {
            const data = result.data;

            // 渲染表单字段
            config.formFields.forEach(field => {
                const value = data[field.key] !== undefined ? data[field.key] : field.defaultValue || '';
                // 坐标字段特殊处理（转为JSON字符串显示）
                const displayValue = field.key === 'coordinates' ? JSON.stringify(value) : value;

                formEl.innerHTML += `
                    <div class="mb-3">
                        <label for="form-${field.key}" class="form-label">
                            ${field.label} ${field.required ? '<span class="text-danger">*</span>' : ''}
                        </label>
                        ${field.type === 'textarea' ? 
                            `<textarea class="form-control" id="form-${field.key}" 
                                      ${field.required ? 'required' : ''}
                                      placeholder="${field.placeholder || ''}"
                                      rows="4">${displayValue}</textarea>` : 
                            `<input type="${field.type}" class="form-control" id="form-${field.key}" 
                                   ${field.required ? 'required' : ''}
                                   placeholder="${field.placeholder || ''}"
                                   value="${displayValue}">`
                        }
                    </div>
                `;
            });

            $('#editModal').modal('show');
        } else {
            alert(result.msg || '获取数据失败');
        }
    } catch (error) {
        console.error('获取数据失败:', error);
        alert('获取数据失败，请重试');
    }
}

// 提交表单（新增/编辑）
async function submitForm() {
    const config = POI_CONFIG[currentPoiType];
    const formData = {};
    let isValid = true;

    // 收集表单数据并验证必填项
    config.formFields.forEach(field => {
        const el = document.getElementById(`form-${field.key}`);
        const value = el.value.trim();

        if (field.required && !value) {
            isValid = false;
            el.classList.add('is-invalid');
            return;
        }
        el.classList.remove('is-invalid');

        // 处理数据类型
        if (value !== '') {
            if (field.type === 'number') {
                formData[field.key] = parseFloat(value);
            } else if (field.key === 'coordinates') {
                // 解析坐标JSON（修复空间数据提交问题）
                try {
                    formData[field.key] = JSON.parse(value);
                } catch (e) {
                    isValid = false;
                    el.classList.add('is-invalid');
                    alert(`坐标格式错误：${e.message}`);
                }
            } else {
                formData[field.key] = value;
            }
        }
    });

    if (!isValid) return;

    // 添加主键（编辑时）
    if (currentEditId) {
        formData[config.primaryKey] = currentEditId;
    }

    try {
        const url = currentEditId 
            ? `${config.apiPrefix}/update` 
            : `${config.apiPrefix}/add`;

        const response = await fetch(url, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(formData)
        });

        const result = await response.json();
        if (result.code === 200) {
            alert(currentEditId ? '更新成功' : '新增成功');
            $('#editModal').modal('hide');
            loadData(currentPage);
        } else {
            alert(result.msg || '操作失败');
        }
    } catch (error) {
        console.error('提交失败:', error);
        alert('提交失败，请重试');
    }
}

// 打开删除模态框
function openDeleteModal(id) {
    currentDeleteId = id;
    const config = POI_CONFIG[currentPoiType];
    document.getElementById('deleteConfirmText').textContent = 
        `确定要删除ID为${id}的${config.label}数据吗？`;
    $('#deleteModal').modal('show');
}

// 确认删除
async function confirmDelete() {
    if (!currentDeleteId) return;

    const config = POI_CONFIG[currentPoiType];
    try {
        const response = await fetch(`${config.apiPrefix}/delete`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ [config.primaryKey]: currentDeleteId })
        });

        const result = await response.json();
        if (result.code === 200) {
            alert('删除成功');
            $('#deleteModal').modal('hide');
            loadData(currentPage);
        } else {
            alert(result.msg || '删除失败');
        }
    } catch (error) {
        console.error('删除失败:', error);
        alert('删除失败，请重试');
    }
}