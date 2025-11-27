document.addEventListener('DOMContentLoaded', function() {
    // POI配置：适配四个类型的接口和字段
    const POI_CONFIG = {
        publicservices: {
            label: "公共服务",
            apiPrefix: "/api/publicservices",
            primaryKey: "fid",
            fields: [
                { name: "name", label: "名称", required: true, type: "text" },
                { name: "type", label: "类型", required: true, type: "text" },
                { name: "address", label: "地址", required: false, type: "text" },
                { name: "longitude", label: "经度", required: true, type: "number", step: "0.000001" },
                { name: "latitude", label: "纬度", required: true, type: "number", step: "0.000001" },
                { name: "category", label: "分类", required: false, type: "text" }
            ],
            tableColumns: [
                { key: "fid", label: "ID" },
                { key: "name", label: "名称" },
                { key: "type", label: "类型" },
                { key: "address", label: "地址" },
                { key: "longitude", label: "经度", format: (val) => val.toFixed(6) },
                { key: "latitude", label: "纬度", format: (val) => val.toFixed(6) },
                { key: "category", label: "分类" },
                { key: "operate", label: "操作" }
            ]
        },
        wuhanmetro: {
            label: "武汉市地铁站点",
            apiPrefix: "/api/wuhanmetro",
            primaryKey: "ogc_fid",
            fields: [
                { name: "name", label: "站点名称", required: true, type: "text" },
                { name: "line", label: "线路", required: true, type: "text" },
                { name: "color", label: "线路颜色", required: false, type: "text" },
                { name: "lon_wgs84", label: "经度(WGS84)", required: true, type: "number", step: "0.000001" },
                { name: "lat_wgs84", label: "纬度(WGS84)", required: true, type: "number", step: "0.000001" },
                { name: "transfer", label: "换乘站", required: false, type: "text" }
            ],
            tableColumns: [
                { key: "ogc_fid", label: "ID" },
                { key: "name", label: "站点名称" },
                { key: "line", label: "线路" },
                { key: "color", label: "线路颜色" },
                { key: "lon_wgs84", label: "经度", format: (val) => val.toFixed(6) },
                { key: "lat_wgs84", label: "纬度", format: (val) => val.toFixed(6) },
                { key: "transfer", label: "换乘站" },
                { key: "operate", label: "操作" }
            ]
        },
        wuhanmiddleschool: {
            label: "武汉市中学",
            apiPrefix: "/api/wuhanmiddleschool",
            primaryKey: "ogc_fid",
            fields: [
                { name: "name", label: "学校名称", required: true, type: "text" },
                { name: "related_address", label: "相关地址", required: false, type: "text" },
                { name: "x_transfer", label: "X坐标", required: true, type: "number", step: "0.000001" },
                { name: "y_transfer", label: "Y坐标", required: true, type: "number", step: "0.000001" }
            ],
            tableColumns: [
                { key: "ogc_fid", label: "ID" },
                { key: "name", label: "学校名称" },
                { key: "related_address", label: "相关地址" },
                { key: "x_transfer", label: "X坐标", format: (val) => val.toFixed(6) },
                { key: "y_transfer", label: "Y坐标", format: (val) => val.toFixed(6) },
                { key: "operate", label: "操作" }
            ]
        },
        wuhanprimaryschool: {
            label: "武汉市小学",
            apiPrefix: "/api/wuhanprimaryschool",
            primaryKey: "ogc_fid",
            fields: [
                { name: "name", label: "学校名称", required: true, type: "text" },
                { name: "related_address", label: "相关地址", required: false, type: "text" },
                { name: "x_transfer", label: "X坐标", required: true, type: "number", step: "0.000001" },
                { name: "y_transfer", label: "Y坐标", required: true, type: "number", step: "0.000001" }
            ],
            tableColumns: [
                { key: "ogc_fid", label: "ID" },
                { key: "name", label: "学校名称" },
                { key: "related_address", label: "相关地址" },
                { key: "x_transfer", label: "X坐标", format: (val) => val.toFixed(6) },
                { key: "y_transfer", label: "Y坐标", format: (val) => val.toFixed(6) },
                { key: "operate", label: "操作" }
            ]
        }
    };

    // 全局变量
    let currentPoiType = "publicservices";
    let currentEditId = null;
    let dataModal = new bootstrap.Modal(document.getElementById('dataModal'));
    let deleteModal = new bootstrap.Modal(document.getElementById('deleteModal'));
    let currentPage = 1;
    const pageSize = 15;
    let totalCount = 0;

    // 初始化
    initTableHeader();
    loadData(currentPage, pageSize);
    bindEvents();

    /**
     * 初始化表头（适配CSS中table-dark样式）
     */
    function initTableHeader() {
        const columns = POI_CONFIG[currentPoiType].tableColumns;
        const headerEl = document.getElementById('tableHeader');
        headerEl.innerHTML = columns.map(col => `<th>${col.label}</th>`).join('');
    }

    /**
     * 加载数据（适配CSS中空数据/加载提示样式）
     */
    async function loadData(page = 1, pageSize = 15, keyword = "") {
        currentPage = page;
        const config = POI_CONFIG[currentPoiType];
        const loadingTip = document.getElementById('loadingTip');
        const emptyTip = document.getElementById('emptyTip');
        const tableBody = document.getElementById('tableBody');

        // 显示加载状态
        loadingTip.classList.remove('d-none');
        emptyTip.classList.add('d-none');
        tableBody.innerHTML = '';

        try {
            const apiUrl = new URL(`${config.apiPrefix}/search`, window.location.origin);
            apiUrl.searchParams.append('q', encodeURIComponent(keyword));
            apiUrl.searchParams.append('page', page);
            apiUrl.searchParams.append('pageSize', pageSize);

            const response = await fetch(apiUrl.toString());
            const result = await response.json();
            const dataList = result.data || [];
            totalCount = result.total || 0;

            // 渲染表格数据（适配CSS中table-hover样式）
            renderTableBody(dataList, config.tableColumns, config.primaryKey);
            // 渲染分页（适配CSS中pagination样式）
            renderPagination();
            // 显示空数据提示
            emptyTip.classList.toggle('d-none', dataList.length > 0);
        } catch (error) {
            console.error("加载数据失败：", error);
            alert("加载数据失败，请刷新重试");
        } finally {
            loadingTip.classList.add('d-none');
        }
    }

    /**
     * 渲染表格内容（适配CSS中表格单元格padding和hover效果）
     */
    function renderTableBody(dataList, columns, primaryKey) {
        const tableBody = document.getElementById('tableBody');
        if (dataList.length === 0) {
            tableBody.innerHTML = '<tr><td colspan="100%" class="text-center text-muted">暂无数据</td></tr>';
            return;
        }

        tableBody.innerHTML = dataList.map(item => {
            const cells = columns.map(col => {
                if (col.key === 'operate') {
                    // 操作按钮使用btn-sm适配CSS中.btn-sm样式
                    return `
                        <td>
                            <button class="btn btn-primary btn-sm me-2" onclick="openEditModal(${item[primaryKey]})">编辑</button>
                            <button class="btn btn-danger btn-sm" onclick="openDeleteModal(${item[primaryKey]})">删除</button>
                        </td>
                    `;
                }
                const value = item[col.key] || '-';
                return `<td>${col.format ? col.format(value) : value}</td>`;
            }).join('');
            return `<tr>${cells}</tr>`;
        }).join('');
    }

    /**
     * 渲染分页（完全适配CSS中pagination相关样式）
     */
    function renderPagination() {
        const paginationEl = document.getElementById('pagination');
        if (!paginationEl) return;

        const totalPages = Math.ceil(totalCount / pageSize);
        if (totalCount === 0 || totalPages <= 1) {
            paginationEl.innerHTML = "";
            return;
        }

        let paginationHtml = `
            <nav aria-label="分页导航">
                <ul class="pagination">
                    <li class="page-item ${currentPage === 1 ? 'disabled' : ''}">
                        <a class="page-link" href="javascript:;" onclick="changePage(${currentPage - 1})">上一页</a>
                    </li>
        `;

        const startPage = Math.max(1, currentPage - 2);
        const endPage = Math.min(totalPages, currentPage + 2);

        if (startPage > 1) {
            paginationHtml += `
                <li class="page-item ${currentPage === 1 ? 'active' : ''}">
                    <a class="page-link" href="javascript:;" onclick="changePage(1)">1</a>
                </li>
                ${startPage > 2 ? '<li class="page-item disabled"><a class="page-link">...</a></li>' : ''}
            `;
        }

        for (let i = startPage; i <= endPage; i++) {
            paginationHtml += `
                <li class="page-item ${currentPage === i ? 'active' : ''}">
                    <a class="page-link" href="javascript:;" onclick="changePage(${i})">${i}</a>
                </li>
            `;
        }

        if (endPage < totalPages) {
            paginationHtml += `
                ${endPage < totalPages - 1 ? '<li class="page-item disabled"><a class="page-link">...</a></li>' : ''}
                <li class="page-item ${currentPage === totalPages ? 'active' : ''}">
                    <a class="page-link" href="javascript:;" onclick="changePage(${totalPages})">${totalPages}</a>
                </li>
            `;
        }

        paginationHtml += `
                    <li class="page-item disabled">
                        <a class="page-link" href="javascript:;">共 ${totalCount} 条 / ${totalPages} 页</a>
                    </li>
                    <li class="page-item ${currentPage === totalPages ? 'disabled' : ''}">
                        <a class="page-link" href="javascript:;" onclick="changePage(${currentPage + 1})">下一页</a>
                    </li>
                </ul>
            </nav>
        `;

        paginationEl.innerHTML = paginationHtml;
    }

    /**
     * 绑定事件
     */
    function bindEvents() {
        // 切换POI类型
        document.getElementById('poiType').addEventListener('change', function() {
            currentPoiType = this.value;
            currentPage = 1;
            initTableHeader();
            loadData(1, pageSize);
        });

        // 搜索框回车事件
        document.getElementById('searchInput').addEventListener('keydown', function(e) {
            if (e.key === 'Enter') searchData();
        });
    }

    /**
     * 切换页码
     */
    window.changePage = function(page) {
        const totalPages = Math.ceil(totalCount / pageSize);
        if (page < 1 || page > totalPages) return;
        const keyword = document.getElementById('searchInput').value.trim();
        loadData(page, pageSize, keyword);
    };

    /**
     * 搜索数据
     */
    window.searchData = function() {
        const keyword = document.getElementById('searchInput').value.trim();
        loadData(1, pageSize, keyword);
    };

    /**
     * 打开新增模态框（适配CSS中form和modal样式）
     */
    window.openAddModal = function() {
        currentEditId = null;
        const config = POI_CONFIG[currentPoiType];
        const formEl = document.getElementById('dataForm');
        const modalTitle = document.getElementById('modalTitle');

        modalTitle.textContent = `新增${config.label}`;
        formEl.reset();
        // 渲染表单字段（适配CSS中form-label和form-control样式）
        formEl.innerHTML = config.fields.map(field => `
            <div class="mb-3">
                <label for="${field.name}" class="form-label">${field.label}${field.required ? '<span class="text-danger">*</span>' : ''}</label>
                <input type="${field.type}" class="form-control" id="${field.name}" name="${field.name}" 
                    ${field.step ? `step="${field.step}"` : ''} 
                    ${field.required ? 'required' : ''}>
            </div>
        `).join('');

        dataModal.show();
    };

    /**
     * 打开编辑模态框
     */
    window.openEditModal = async function(id) {
        currentEditId = id;
        const config = POI_CONFIG[currentPoiType];
        const formEl = document.getElementById('dataForm');
        const modalTitle = document.getElementById('modalTitle');

        try {
            const response = await fetch(`${config.apiPrefix}/${id}`);
            const result = await response.json();
            if (result.code !== 200) throw new Error(result.msg);
            const data = result.data;

            modalTitle.textContent = `编辑${config.label}`;
            // 渲染表单并填充数据
            formEl.innerHTML = config.fields.map(field => {
                const value = data[field.name] || '';
                return `
                    <div class="mb-3">
                        <label for="${field.name}" class="form-label">${field.label}${field.required ? '<span class="text-danger">*</span>' : ''}</label>
                        <input type="${field.type}" class="form-control" id="${field.name}" name="${field.name}" 
                            value="${value}" ${field.step ? `step="${field.step}"` : ''} 
                            ${field.required ? 'required' : ''}>
                    </div>
                `;
            }).join('');

            dataModal.show();
        } catch (error) {
            console.error("加载编辑数据失败：", error);
            alert("加载数据失败，请重试");
        }
    };

    /**
     * 提交表单（新增/编辑）
     */
    window.submitForm = async function() {
        const formEl = document.getElementById('dataForm');
        if (!formEl.checkValidity()) {
            formEl.reportValidity();
            return;
        }

        const formData = new FormData(formEl);
        const data = Object.fromEntries(formData.entries());
        const config = POI_CONFIG[currentPoiType];

        try {
            let response;
            if (currentEditId) {
                // 编辑
                response = await fetch(`${config.apiPrefix}/${currentEditId}`, {
                    method: 'PUT',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify(data)
                });
            } else {
                // 新增
                response = await fetch(`${config.apiPrefix}`, {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify(data)
                });
            }

            const result = await response.json();
            if (result.code !== 200) throw new Error(result.msg);

            alert(result.msg);
            dataModal.hide();
            // 刷新数据
            const keyword = document.getElementById('searchInput').value.trim();
            loadData(currentPage, pageSize, keyword);
        } catch (error) {
            console.error("提交失败：", error);
            alert("提交失败：" + error.message);
        }
    };

    /**
     * 打开删除模态框
     */
    window.openDeleteModal = function(id) {
        currentEditId = id;
        deleteModal.show();
    };

    /**
     * 确认删除
     */
    window.confirmDelete = async function() {
        const config = POI_CONFIG[currentPoiType];
        try {
            const response = await fetch(`${config.apiPrefix}/${currentEditId}`, {
                method: 'DELETE'
            });
            const result = await response.json();
            if (result.code !== 200) throw new Error(result.msg);

            alert(result.msg);
            deleteModal.hide();
            // 刷新数据
            const keyword = document.getElementById('searchInput').value.trim();
            const totalPages = Math.ceil(totalCount / pageSize);
            if (currentPage > 1 && document.querySelectorAll('#tableBody tr').length === 1) {
                loadData(currentPage - 1, pageSize, keyword);
            } else {
                loadData(currentPage, pageSize, keyword);
            }
        } catch (error) {
            console.error("删除失败：", error);
            alert("删除失败：" + error.message);
        }
    };
});