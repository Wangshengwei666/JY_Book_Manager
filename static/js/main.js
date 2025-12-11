// JY图书管理系统 - 主JavaScript文件

$(document).ready(function() {
    // 自动隐藏Flash消息（只隐藏Flash消息，不隐藏批量操作栏）
    setTimeout(function() {
        $('#flash-messages .alert').fadeOut('slow', function() {
            $(this).remove();
        });
    }, 5000);
    
    // 表单验证增强
    $('form').on('submit', function(e) {
        const form = $(this)[0];
        if (!form.checkValidity()) {
            e.preventDefault();
            e.stopPropagation();
        }
        $(this).addClass('was-validated');
    });
    
    // 主题切换
    initTheme();
    $('#themeToggle').on('click', function() {
        toggleTheme();
    });
});

// Toast通知函数
function showToast(message, type = 'info') {
    const toastContainer = $('.toast-container');
    const toastId = 'toast-' + Date.now();
    
    const bgClass = {
        'success': 'bg-success',
        'error': 'bg-danger',
        'warning': 'bg-warning',
        'info': 'bg-info'
    }[type] || 'bg-info';
    
    const icon = {
        'success': 'bi-check-circle',
        'error': 'bi-x-circle',
        'warning': 'bi-exclamation-triangle',
        'info': 'bi-info-circle'
    }[type] || 'bi-info-circle';
    
    const toastHtml = `
        <div id="${toastId}" class="toast" role="alert" aria-live="assertive" aria-atomic="true">
            <div class="toast-header ${bgClass} text-white">
                <i class="bi ${icon} me-2"></i>
                <strong class="me-auto">通知</strong>
                <button type="button" class="btn-close btn-close-white" data-bs-dismiss="toast"></button>
            </div>
            <div class="toast-body">
                ${message}
            </div>
        </div>
    `;
    
    toastContainer.append(toastHtml);
    const toastElement = document.getElementById(toastId);
    const toast = new bootstrap.Toast(toastElement, {
        autohide: true,
        delay: 3000
    });
    toast.show();
    
    // 自动移除
    toastElement.addEventListener('hidden.bs.toast', function() {
        $(this).remove();
    });
}

// 主题切换
function initTheme() {
    const theme = localStorage.getItem('theme') || 'light';
    applyTheme(theme);
}

function toggleTheme() {
    const currentTheme = $('body').hasClass('dark-theme') ? 'dark' : 'light';
    const newTheme = currentTheme === 'light' ? 'dark' : 'light';
    applyTheme(newTheme);
    localStorage.setItem('theme', newTheme);
}

function applyTheme(theme) {
    if (theme === 'dark') {
        $('body').removeClass('light-theme').addClass('dark-theme');
        $('#themeToggle i').removeClass('bi-moon-stars').addClass('bi-sun');
    } else {
        $('body').removeClass('dark-theme').addClass('light-theme');
        $('#themeToggle i').removeClass('bi-sun').addClass('bi-moon-stars');
    }
}

