// 等待 DOM 加載完成
document.addEventListener('DOMContentLoaded', function() {
    // 初始化圖表
    initializeBarChart();
});

/**
 * 初始化長條圖
 */
function initializeBarChart() {
    // 獲取圖表的 canvas 元素
    const ctx = document.getElementById('chart').getContext('2d');
    
    // 圖表資料
    const chartData = {
        labels: ['項目1', '項目2', '項目3'],
        datasets: [{
            label: '數據',
            data: [12, 19, 3],
            backgroundColor: 'rgba(54, 162, 235, 0.2)',
            borderColor: 'rgb(54, 162, 235)',
            borderWidth: 1
        }]
    };
    
    // 圖表配置選項
    const chartOptions = {
        responsive: true,
        maintainAspectRatio: true,
        plugins: {
            title: {
                display: true,
                text: '數據可視化',
                font: {
                    size: 18
                }
            },
            legend: {
                position: 'top'
            },
            tooltip: {
                mode: 'index',
                intersect: false
            }
        },
        scales: {
            y: {
                beginAtZero: true
            }
        }
    };
    
    // 創建圖表
    const chart = new Chart(ctx, {
        type: 'bar',
        data: chartData,
        options: chartOptions
    });
}

/**
 * 更新圖表數據
 * @param {Array} labels - 標籤數組
 * @param {Array} data - 數據數組
 * @param {string} title - 圖表標題
 */
function updateChartData(labels, data, title) {
    const ctx = document.getElementById('chart').getContext('2d');
    
    // 銷毀現有圖表
    if (window.myChart) {
        window.myChart.destroy();
    }
    
    // 更新數據
    const chartData = {
        labels: labels || ['項目1', '項目2', '項目3'],
        datasets: [{
            label: '數據',
            data: data || [12, 19, 3],
            backgroundColor: 'rgba(54, 162, 235, 0.2)',
            borderColor: 'rgb(54, 162, 235)',
            borderWidth: 1
        }]
    };
    
    // 更新標題
    const chartOptions = {
        responsive: true,
        plugins: {
            title: {
                display: true,
                text: title || '數據可視化',
                font: {
                    size: 18
                }
            },
            legend: {
                position: 'top'
            },
            tooltip: {
                mode: 'index',
                intersect: false
            }
        },
        scales: {
            y: {
                beginAtZero: true
            }
        }
    };
    
    // 創建新圖表
    window.myChart = new Chart(ctx, {
        type: 'bar',
        data: chartData,
        options: chartOptions
    });
}