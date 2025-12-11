// 图书列表页主要JavaScript逻辑

let currentPage = 1;
let currentView = 'card';
let priceChart = null;
let publisherChart = null;

let isAdvancedFilterActive = false;
let currentFilters = {};

// 保存选中的图书ID（用于批量操作）
let selectedBookIds = new Set();

$(document).ready(function() {
    // 加载统计数据
    loadStatistics();
    
    // 加载图表
    loadCharts();
    
    
    // 搜索功能
    let searchTimeout;
    $('#searchInput').on('keyup', function() {
        clearTimeout(searchTimeout);
        const value = $(this).val().trim();
        searchTimeout = setTimeout(() => {
            if (value) {
                filterBooks(value);
            } else {
                loadBooks();
            }
        }, 500);
    });
    
    // 排序和分页变化
    $('#sortBy, #sortOrder, #perPage').on('change', function() {
        currentPage = 1;
        if (isAdvancedFilterActive) {
            applyAdvancedFilter();
        } else {
            loadBooks();
        }
    });
    
    // 删除确认
    $('#confirmDeleteBtn').on('click', function() {
        const bookId = window.deleteBookId;
        if (bookId) {
            deleteBookRequest(bookId);
        }
        bootstrap.Modal.getInstance(document.getElementById('deleteModal')).hide();
    });
    
    // CSV文件选择
    $('#csvFile').on('change', function() {
        const file = this.files[0];
        if (file) {
            previewCSV(file);
        }
    });
});

// 加载统计数据
function loadStatistics() {
    $.ajax({
        url: '/api/statistics',
        type: 'GET',
        success: function(response) {
            if (response.success) {
                const data = response.data;
                $('#totalBooks').text(data.total);
                $('#avgPrice').text('¥' + data.avg_price.toFixed(2));
                $('#totalBorrows').text(data.total_borrows);
                $('#popularBook').text(data.popular_book + ' (' + data.popular_borrows + '次)');
            }
        },
        error: function() {
            showToast('加载统计数据失败', 'error');
        }
    });
}

// 加载图表
function loadCharts() {
    $.ajax({
        url: '/api/statistics',
        type: 'GET',
        success: function(response) {
            if (response.success) {
                const data = response.data;
                drawPriceChart(data);
                drawPublisherChart(data.publishers);
            }
        }
    });
}

// 绘制价格分布图
function drawPriceChart(data) {
    const ctx = document.getElementById('priceChart');
    if (!ctx) return;
    
    if (priceChart) {
        priceChart.destroy();
    }
    
    priceChart = new Chart(ctx, {
        type: 'bar',
        data: {
            labels: ['最低价格', '平均价格', '最高价格'],
            datasets: [{
                label: '价格 (¥)',
                data: [data.min_price, data.avg_price, data.max_price],
                backgroundColor: [
                    'rgba(54, 162, 235, 0.6)',
                    'rgba(75, 192, 192, 0.6)',
                    'rgba(255, 99, 132, 0.6)'
                ],
                borderColor: [
                    'rgba(54, 162, 235, 1)',
                    'rgba(75, 192, 192, 1)',
                    'rgba(255, 99, 132, 1)'
                ],
                borderWidth: 1
            }]
        },
        options: {
            responsive: true,
            scales: {
                y: {
                    beginAtZero: true
                }
            }
        }
    });
}

// 绘制出版社分布图
function drawPublisherChart(publishers) {
    const ctx = document.getElementById('publisherChart');
    if (!ctx) return;
    
    if (publisherChart) {
        publisherChart.destroy();
    }
    
    const labels = publishers.map(p => p.book_publisher);
    const data = publishers.map(p => p.count);
    
    publisherChart = new Chart(ctx, {
        type: 'pie',
        data: {
            labels: labels,
            datasets: [{
                data: data,
                backgroundColor: [
                    'rgba(255, 99, 132, 0.6)',
                    'rgba(54, 162, 235, 0.6)',
                    'rgba(255, 206, 86, 0.6)',
                    'rgba(75, 192, 192, 0.6)',
                    'rgba(153, 102, 255, 0.6)'
                ],
                borderColor: [
                    'rgba(255, 99, 132, 1)',
                    'rgba(54, 162, 235, 1)',
                    'rgba(255, 206, 86, 1)',
                    'rgba(75, 192, 192, 1)',
                    'rgba(153, 102, 255, 1)'
                ],
                borderWidth: 1
            }]
        },
        options: {
            responsive: true
        }
    });
}

// 加载图书列表
function loadBooks() {
    const search = $('#searchInput').val().trim();
    const sortBy = $('#sortBy').val();
    const sortOrder = $('#sortOrder').val();
    const perPage = $('#perPage').val();
    
    $.ajax({
        url: '/api/books/paginated',
        type: 'GET',
        data: {
            page: currentPage,
            per_page: perPage,
            search: search,
            sort_by: sortBy,
            sort_order: sortOrder
        },
        success: function(response) {
            if (response.success) {
                renderBooks(response.data);
                renderPagination(response.pagination);
            } else {
                showToast('加载图书列表失败', 'error');
            }
        },
        error: function() {
            showToast('加载图书列表失败', 'error');
        }
    });
}

// 渲染图书
function renderBooks(books) {
    if (currentView === 'card') {
        renderCardView(books);
    } else {
        renderTableView(books);
    }
    
    // 恢复之前选中的状态（使用全局变量）
    // 注意：不要删除不在当前列表中的选中项，因为可能是分页或筛选导致的
    // 只在用户明确取消选择时才删除
    selectedBookIds.forEach(id => {
        const cleanedId = String(id).trim();
        // 尝试精确匹配
        let checkbox = $(`.book-checkbox[value="${cleanedId}"]`);
        // 如果找不到，尝试带空格的匹配（兼容旧数据）
        if (checkbox.length === 0) {
            checkbox = $(`.book-checkbox[value="${cleanedId} "]`);
        }
        if (checkbox.length > 0) {
            checkbox.prop('checked', true);
        }
        // 不再自动删除不在当前列表中的项，保持选中状态
    });
    
    // 直接更新批量操作栏（基于全局变量，不依赖DOM）
    updateBatchActions();
}

// 渲染卡片视图
function renderCardView(books) {
    const grid = $('#booksGrid');
    grid.empty();
    
    if (books.length === 0) {
        grid.html(`
            <div class="col-12">
                <div class="text-center py-5">
                    <i class="bi bi-inbox" style="font-size: 3rem; color: #ccc;"></i>
                    <p class="text-muted mt-3">暂无图书数据</p>
                    <a href="/book/new" class="btn btn-primary">
                        <i class="bi bi-plus-circle"></i> 添加第一本图书
                    </a>
                </div>
            </div>
        `);
        return;
    }
    
    books.forEach(book => {
        const card = `
            <div class="col-md-4 col-lg-3 book-item" data-book-id="${book.book_id}">
                <div class="card book-card h-100 shadow-sm">
                    <div class="card-body">
                        <div class="d-flex justify-content-between align-items-start mb-3">
                            <div class="form-check mb-0">
                                <input class="form-check-input book-checkbox" type="checkbox" 
                                       value="${book.book_id}" 
                                       ${selectedBookIds.has(book.book_id) ? 'checked' : ''}
                                       onchange="handleCheckboxChange('${book.book_id}', this.checked)"
                                       id="checkbox-${book.book_id}">
                                <label class="form-check-label" for="checkbox-${book.book_id}" style="cursor: pointer;">
                                    <span class="badge bg-primary">${book.book_id}</span>
                                </label>
                            </div>
                            <h5 class="card-title mb-0 flex-grow-1 ms-2" style="cursor: pointer;" 
                                onclick="showBookDetail('${book.book_id}')">${book.book_name}</h5>
                        </div>
                        <div class="book-info mb-3">
                            <p class="text-muted mb-2 small">
                                <i class="bi bi-person"></i> <strong>作者：</strong>${book.book_author}
                            </p>
                            <p class="text-muted mb-2 small">
                                <i class="bi bi-building"></i> <strong>出版社：</strong>${book.book_publisher}
                            </p>
                            <p class="text-muted mb-2 small">
                                <i class="bi bi-upc"></i> <strong>ISBN：</strong>${book.book_isbn}
                            </p>
                        </div>
                        <div class="d-flex justify-content-between align-items-center mt-auto">
                            <div>
                                <span class="h5 text-primary mb-0">¥${book.book_price.toFixed(2)}</span>
                                <small class="text-muted d-block">
                                    <i class="bi bi-eye"></i> 借阅 ${book.interview_times} 次
                                </small>
                            </div>
                            <div class="btn-group btn-group-sm">
                                <a href="/book/edit/${book.book_id}" 
                                   class="btn btn-outline-primary" title="编辑">
                                    <i class="bi bi-pencil"></i>
                                </a>
                                <button type="button" 
                                        class="btn btn-outline-danger"
                                        onclick="deleteBook('${book.book_id}', '${book.book_name}')"
                                        title="删除">
                                    <i class="bi bi-trash"></i>
                                </button>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        `;
        grid.append(card);
    });
}

// 渲染表格视图
function renderTableView(books) {
    const tbody = $('#booksTable tbody');
    tbody.empty();
    
    if (books.length === 0) {
        tbody.html(`
            <tr>
                <td colspan="9" class="text-center py-5">
                    <i class="bi bi-inbox" style="font-size: 3rem; color: #ccc;"></i>
                    <p class="text-muted mt-3">暂无图书数据</p>
                    <a href="/book/new" class="btn btn-primary">
                        <i class="bi bi-plus-circle"></i> 添加第一本图书
                    </a>
                </td>
            </tr>
        `);
        return;
    }
    
    books.forEach(book => {
        const row = `
            <tr class="book-item" data-book-id="${book.book_id}">
                <td>
                    <input type="checkbox" class="book-checkbox" value="${book.book_id}" 
                           ${selectedBookIds.has(book.book_id) ? 'checked' : ''}
                           onchange="handleCheckboxChange('${book.book_id}', this.checked)">
                </td>
                <td>${book.book_id}</td>
                <td>${book.book_name}</td>
                <td>${book.book_isbn}</td>
                <td>${book.book_author}</td>
                <td>${book.book_publisher}</td>
                <td>¥${book.book_price.toFixed(2)}</td>
                <td>${book.interview_times}</td>
                <td>
                    <div class="btn-group btn-group-sm">
                        <a href="/book/edit/${book.book_id}" 
                           class="btn btn-outline-primary" title="编辑">
                            <i class="bi bi-pencil"></i>
                        </a>
                        <button type="button" 
                                class="btn btn-outline-danger"
                                onclick="deleteBook('${book.book_id}', '${book.book_name}')"
                                title="删除">
                            <i class="bi bi-trash"></i>
                        </button>
                    </div>
                </td>
            </tr>
        `;
        tbody.append(row);
    });
}

// 渲染分页
function renderPagination(pagination) {
    const nav = $('#paginationNav');
    const ul = $('#pagination');
    ul.empty();
    
    if (pagination.pages <= 1) {
        nav.hide();
        return;
    }
    
    nav.show();
    
    // 上一页
    const prevDisabled = pagination.page === 1 ? 'disabled' : '';
    ul.append(`
        <li class="page-item ${prevDisabled}">
            <a class="page-link" href="#" onclick="goToPage(${pagination.page - 1}); return false;">上一页</a>
        </li>
    `);
    
    // 页码
    const startPage = Math.max(1, pagination.page - 2);
    const endPage = Math.min(pagination.pages, pagination.page + 2);
    
    if (startPage > 1) {
        ul.append(`<li class="page-item"><a class="page-link" href="#" onclick="goToPage(1); return false;">1</a></li>`);
        if (startPage > 2) {
            ul.append(`<li class="page-item disabled"><span class="page-link">...</span></li>`);
        }
    }
    
    for (let i = startPage; i <= endPage; i++) {
        const active = i === pagination.page ? 'active' : '';
        ul.append(`
            <li class="page-item ${active}">
                <a class="page-link" href="#" onclick="goToPage(${i}); return false;">${i}</a>
            </li>
        `);
    }
    
    if (endPage < pagination.pages) {
        if (endPage < pagination.pages - 1) {
            ul.append(`<li class="page-item disabled"><span class="page-link">...</span></li>`);
        }
        ul.append(`<li class="page-item"><a class="page-link" href="#" onclick="goToPage(${pagination.pages}); return false;">${pagination.pages}</a></li>`);
    }
    
    // 下一页
    const nextDisabled = pagination.page === pagination.pages ? 'disabled' : '';
    ul.append(`
        <li class="page-item ${nextDisabled}">
            <a class="page-link" href="#" onclick="goToPage(${pagination.page + 1}); return false;">下一页</a>
        </li>
    `);
}

// 跳转页面
function goToPage(page) {
    currentPage = page;
    loadBooks();
    window.scrollTo({ top: 0, behavior: 'smooth' });
}

// 切换视图
function switchView(view) {
    currentView = view;
    if (view === 'card') {
        $('#cardView').show();
        $('#tableView').hide();
        $('#viewCard').addClass('active');
        $('#viewTable').removeClass('active');
    } else {
        $('#cardView').hide();
        $('#tableView').show();
        $('#viewCard').removeClass('active');
        $('#viewTable').addClass('active');
    }
    // 切换视图时，不需要重新加载数据，只需要切换显示方式
    // 这样可以保持选中状态
    updateBatchActions();
}

// 过滤图书
function filterBooks(keyword) {
    currentPage = 1;
    loadBooks();
}

// 清除筛选
function clearFilters() {
    $('#searchInput').val('');
    $('#sortBy').val('book_id');
    $('#sortOrder').val('ASC');
    $('#perPage').val('12');
    resetAdvancedFilter();
    $('#advancedFilterPanel').hide();
    currentPage = 1;
    loadBooks();
}

// 删除图书
function deleteBook(bookId, bookName) {
    window.deleteBookId = bookId;
    document.getElementById('deleteBookName').textContent = bookName;
    new bootstrap.Modal(document.getElementById('deleteModal')).show();
}

// 删除请求
function deleteBookRequest(bookId) {
    $.ajax({
        url: '/api/books/' + bookId,
        type: 'DELETE',
        success: function(response) {
            if (response.success) {
                showToast(response.message, 'success');
                // 重置批量操作状态
                selectedBookIds.clear();
                $('.book-checkbox').prop('checked', false);
                updateBatchActions();
                // 重新加载数据
                loadBooks();
                loadStatistics();
                loadCharts();
            } else {
                showToast('删除失败: ' + response.message, 'error');
            }
        },
        error: function(xhr) {
            const response = xhr.responseJSON || {};
            showToast('删除失败: ' + (response.message || '服务器错误'), 'error');
        }
    });
}

// 处理复选框变化
function handleCheckboxChange(bookId, isChecked) {
    // 确保ID没有空格
    bookId = String(bookId).trim();
    
    if (isChecked) {
        selectedBookIds.add(bookId);
    } else {
        selectedBookIds.delete(bookId);
    }
    updateBatchActions();
}

// 批量操作
function updateBatchActions() {
    // 完全基于全局变量来更新批量操作栏，不依赖DOM状态
    // 清理ID中的空格（防止之前添加的带空格的ID）
    // 但不要清空重建，而是逐步清理，避免竞态条件
    const idsToRemove = [];
    const cleanedIds = new Set();
    
    selectedBookIds.forEach(id => {
        const cleanedId = String(id).trim();
        if (cleanedId && cleanedId !== id) {
            // 如果ID有空格，需要替换
            idsToRemove.push(id);
            cleanedIds.add(cleanedId);
        } else if (cleanedId) {
            // ID已经是干净的，保留
            cleanedIds.add(cleanedId);
        }
    });
    
    // 移除带空格的ID，添加清理后的ID
    idsToRemove.forEach(id => selectedBookIds.delete(id));
    cleanedIds.forEach(id => {
        if (!selectedBookIds.has(id)) {
            selectedBookIds.add(id);
        }
    });
    
    const count = selectedBookIds.size;
    
    if (count > 0) {
        $('#batchActions').show();
        $('#selectedCount').text(count);
    } else {
        $('#batchActions').hide();
    }
}

// 全选/取消全选
function toggleSelectAll() {
    const checked = $('#selectAll').prop('checked');
    $('.book-checkbox').each(function() {
        const bookId = String($(this).val()).trim();
        $(this).prop('checked', checked);
        if (checked) {
            selectedBookIds.add(bookId);
        } else {
            selectedBookIds.delete(bookId);
        }
    });
    updateBatchActions();
}

// 批量删除
function batchDelete() {
    const checked = $('.book-checkbox:checked');
    const bookIds = checked.map(function() {
        return String($(this).val()).trim();
    }).get();
    
    if (bookIds.length === 0) {
        showToast('请选择要删除的图书', 'warning');
        return;
    }
    
    if (!confirm(`确定要删除选中的 ${bookIds.length} 本图书吗？此操作不可恢复！`)) {
        return;
    }
    
    $.ajax({
        url: '/api/books/batch',
        type: 'DELETE',
        contentType: 'application/json',
        data: JSON.stringify({ book_ids: bookIds }),
        success: function(response) {
            if (response.success) {
                showToast(response.message, 'success');
                // 从选中集合中移除已删除的图书
                bookIds.forEach(id => selectedBookIds.delete(id));
                // 重新加载数据
                loadBooks();
                loadStatistics();
                loadCharts();
                updateBatchActions();
            } else {
                showToast('批量删除失败: ' + response.message, 'error');
            }
        },
        error: function(xhr) {
            const response = xhr.responseJSON || {};
            showToast('批量删除失败: ' + (response.message || '服务器错误'), 'error');
        }
    });
}

// 导出CSV
function exportCSV() {
    window.location.href = '/api/export/csv';
    showToast('正在导出CSV文件...', 'info');
}

// 高级筛选功能
function toggleAdvancedFilter() {
    const panel = $('#advancedFilterPanel');
    if (panel.is(':visible')) {
        panel.slideUp();
    } else {
        panel.slideDown();
    }
}

function applyAdvancedFilter() {
    const filters = {};
    
    // 价格范围
    const priceMin = $('#filterPriceMin').val();
    const priceMax = $('#filterPriceMax').val();
    if (priceMin) filters.price_min = priceMin;
    if (priceMax) filters.price_max = priceMax;
    
    // 借阅次数范围
    const borrowMin = $('#filterBorrowMin').val();
    const borrowMax = $('#filterBorrowMax').val();
    if (borrowMin) filters.borrow_min = borrowMin;
    if (borrowMax) filters.borrow_max = borrowMax;
    
    // 出版社（关键词搜索）
    const publisher = $('#filterPublisher').val().trim();
    if (publisher) {
        filters.publisher = publisher;
    }
    
    // 作者（关键词搜索）
    const author = $('#filterAuthor').val().trim();
    if (author) {
        filters.author = author;
    }
    
    // 指定字段筛选
    const field = $('#filterField').val();
    const keyword = $('#filterKeyword').val().trim();
    if (field && keyword) {
        filters.field_search = {
            field: field,
            keyword: keyword
        };
    }
    
    currentFilters = filters;
    isAdvancedFilterActive = Object.keys(filters).length > 0;
    currentPage = 1;
    
    if (isAdvancedFilterActive) {
        loadFilteredBooks(filters);
    } else {
        loadBooks();
    }
}

function loadFilteredBooks(filters) {
    const sortBy = $('#sortBy').val();
    const sortOrder = $('#sortOrder').val();
    const perPage = $('#perPage').val();
    
    $.ajax({
        url: '/api/books/filter',
        type: 'POST',
        contentType: 'application/json',
        data: JSON.stringify({
            filters: filters,
            page: currentPage,
            per_page: perPage,
            sort_by: sortBy,
            sort_order: sortOrder
        }),
        success: function(response) {
            if (response.success) {
                renderBooks(response.data);
                renderPagination(response.pagination);
                showToast(`找到 ${response.pagination.total} 本图书`, 'success');
            } else {
                showToast('筛选失败: ' + response.message, 'error');
            }
        },
        error: function(xhr, status, error) {
            let errorMsg = '筛选失败';
            if (xhr.responseJSON && xhr.responseJSON.message) {
                errorMsg += ': ' + xhr.responseJSON.message;
            } else if (xhr.responseText) {
                try {
                    const response = JSON.parse(xhr.responseText);
                    if (response.message) {
                        errorMsg += ': ' + response.message;
                    }
                } catch (e) {
                    errorMsg += ': ' + error;
                }
            }
            showToast(errorMsg, 'error');
            console.error('筛选错误:', xhr, status, error);
        }
    });
}

function resetAdvancedFilter() {
    $('#filterPriceMin, #filterPriceMax').val('');
    $('#filterBorrowMin, #filterBorrowMax').val('');
    $('#filterPublisher').val('');
    $('#filterAuthor').val('');
    $('#filterField').val('');
    $('#filterKeyword').val('');
    currentFilters = {};
    isAdvancedFilterActive = false;
    currentPage = 1;
    loadBooks();
}

// 图书详情功能
function showBookDetail(bookId) {
    const modal = new bootstrap.Modal(document.getElementById('bookDetailModal'));
    const content = $('#bookDetailContent');
    const title = $('#detailModalTitle');
    const viewFullBtn = $('#detailViewFullBtn');
    
    // 显示加载状态
    content.html('<div class="text-center py-4"><div class="spinner-border text-primary" role="status"><span class="visually-hidden">加载中...</span></div></div>');
    viewFullBtn.hide();
    modal.show();
    
    // 加载图书详情
    $.ajax({
        url: '/api/books/' + bookId,
        type: 'GET',
        success: function(response) {
            if (response.success) {
                const book = response.data;
                title.html(`<i class="bi bi-book"></i> ${book.book_name}`);
                
                // 渲染详情内容
                const detailHtml = `
                    <div class="row g-3">
                        <div class="col-md-6">
                            <div class="detail-item">
                                <label class="detail-label"><i class="bi bi-tag"></i> 图书ID</label>
                                <div class="detail-value"><span class="badge bg-primary">${book.book_id}</span></div>
                            </div>
                        </div>
                        <div class="col-md-6">
                            <div class="detail-item">
                                <label class="detail-label"><i class="bi bi-upc"></i> ISBN</label>
                                <div class="detail-value">${book.book_isbn}</div>
                            </div>
                        </div>
                        <div class="col-md-6">
                            <div class="detail-item">
                                <label class="detail-label"><i class="bi bi-person"></i> 作者</label>
                                <div class="detail-value">${book.book_author}</div>
                            </div>
                        </div>
                        <div class="col-md-6">
                            <div class="detail-item">
                                <label class="detail-label"><i class="bi bi-building"></i> 出版社</label>
                                <div class="detail-value">${book.book_publisher}</div>
                            </div>
                        </div>
                        <div class="col-md-6">
                            <div class="detail-item">
                                <label class="detail-label"><i class="bi bi-currency-dollar"></i> 价格</label>
                                <div class="detail-value"><span class="h5 text-primary mb-0">¥${book.book_price.toFixed(2)}</span></div>
                            </div>
                        </div>
                        <div class="col-md-6">
                            <div class="detail-item">
                                <label class="detail-label"><i class="bi bi-eye"></i> 借阅次数</label>
                                <div class="detail-value"><span class="h5 text-info mb-0">${book.interview_times}</span> <small class="text-muted">次</small></div>
                            </div>
                        </div>
                    </div>
                `;
                content.html(detailHtml);
                viewFullBtn.attr('href', '/book/detail/' + bookId).show();
            } else {
                content.html('<div class="alert alert-danger">加载图书详情失败</div>');
            }
        },
        error: function() {
            content.html('<div class="alert alert-danger">加载图书详情失败</div>');
        }
    });
}

// 导入CSV功能
function showImportModal() {
    const modal = new bootstrap.Modal(document.getElementById('importModal'));
    $('#csvFile').val('');
    $('#importPreview').hide();
    $('#importResult').hide();
    // 清理之前的提示信息
    $('#fileSelectedInfo, #encodingWarning').remove();
    $('#importBtn').prop('disabled', true);
    modal.show();
}

function previewCSV(file) {
    const reader = new FileReader();
    
    reader.onload = function(e) {
        const text = e.target.result;
        
        // 检查是否包含预期的列名（验证编码是否正确）
        const hasValidHeaders = text.includes('图书ID') || 
                               text.includes('book_id') || 
                               text.includes('图书名称') || 
                               text.includes('book_name');
        
        // 检查是否包含乱码字符（常见的乱码模式）
        const hasGarbledChars = /[\uFFFD]/.test(text) || 
                               (text.includes('ISBN') && !hasValidHeaders);
        
        if (hasValidHeaders) {
            // 编码正确，正常显示预览
            showPreview(text, false);
            $('#importBtn').prop('disabled', false);
        } else {
            // 无法正确预览（可能是编码问题），隐藏预览，直接允许导入
            $('#importPreview').hide();
            // 移除之前的任何提示
            $('#importPreview').prev('.alert').remove();
            // 简单显示文件已选择（不提及编码问题）
            if ($('#fileSelectedInfo').length === 0) {
                $('#importPreview').before(
                    '<div class="alert alert-success mb-3" id="fileSelectedInfo">' +
                    '<i class="bi bi-check-circle"></i> 文件 <strong>' + file.name + '</strong> 已选择，可以开始导入。' +
                    '</div>'
                );
            }
            $('#importBtn').prop('disabled', false);
        }
    };
    
    reader.onerror = function() {
        showToast('读取文件失败', 'error');
    };
    
    // 尝试 UTF-8 读取（浏览器默认）
    reader.readAsText(file, 'UTF-8');
    
    function showPreview(text, hasWarning = false) {
        const lines = text.split(/\r?\n/).filter(line => line.trim());
        
        if (lines.length < 2) {
            showToast('CSV文件格式错误', 'error');
            return;
        }
        
        // 解析CSV（简单处理，假设是逗号分隔）
        const headers = lines[0].split(',').map(h => {
            let header = h.trim();
            // 移除首尾引号
            if (header.startsWith('"') && header.endsWith('"')) {
                header = header.slice(1, -1);
            }
            return header;
        });
        const previewRows = lines.slice(1, Math.min(6, lines.length));
        
        // 显示预览表格
        const thead = $('#previewTable thead tr');
        const tbody = $('#previewTable tbody');
        
        thead.empty();
        tbody.empty();
        
        headers.forEach(header => {
            thead.append(`<th>${header}</th>`);
        });
        
        previewRows.forEach(line => {
            // 处理可能包含引号的CSV单元格
            const cells = line.split(',').map(c => {
                let cell = c.trim();
                // 移除首尾引号
                if (cell.startsWith('"') && cell.endsWith('"')) {
                    cell = cell.slice(1, -1);
                }
                return cell;
            });
            const row = $('<tr></tr>');
            cells.forEach(cell => {
                row.append(`<td>${cell}</td>`);
            });
            tbody.append(row);
        });
        
        $('#importPreview').show();
    }
}

function importCSV() {
    const fileInput = document.getElementById('csvFile');
    const file = fileInput.files[0];
    
    if (!file) {
        showToast('请选择文件', 'warning');
        return;
    }
    
    const formData = new FormData();
    formData.append('file', file);
    
    const importBtn = $('#importBtn');
    importBtn.prop('disabled', true).html('<span class="spinner-border spinner-border-sm me-2"></span>导入中...');
    
    $.ajax({
        url: '/api/import/csv',
        type: 'POST',
        data: formData,
        processData: false,
        contentType: false,
        success: function(response) {
            if (response.success) {
                const result = response.data;
                let resultHtml = `
                    <div class="alert alert-success">
                        <h6><i class="bi bi-check-circle"></i> 导入完成</h6>
                        <p>成功导入: <strong>${result.success_count}</strong> 本图书</p>
                        ${result.error_count > 0 ? `<p>失败: <strong>${result.error_count}</strong> 条记录</p>` : ''}
                    </div>
                `;
                
                if (result.errors && result.errors.length > 0) {
                    resultHtml += '<div class="alert alert-warning"><h6>错误详情：</h6><ul class="mb-0">';
                    result.errors.slice(0, 10).forEach(error => {
                        resultHtml += `<li>${error}</li>`;
                    });
                    if (result.errors.length > 10) {
                        resultHtml += `<li>...还有 ${result.errors.length - 10} 个错误</li>`;
                    }
                    resultHtml += '</ul></div>';
                }
                
                $('#importResult').html(resultHtml).show();
                showToast(response.message, 'success');
                
                // 刷新列表
                setTimeout(() => {
                    location.reload();
                }, 2000);
            } else {
                showToast('导入失败: ' + response.message, 'error');
                importBtn.prop('disabled', false).html('<i class="bi bi-upload"></i> 开始导入');
            }
        },
        error: function(xhr) {
            const response = xhr.responseJSON || {};
            showToast('导入失败: ' + (response.message || '服务器错误'), 'error');
            importBtn.prop('disabled', false).html('<i class="bi bi-upload"></i> 开始导入');
        }
    });
}

