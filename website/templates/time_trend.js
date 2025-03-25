// 等待 DOM 加載完成
document.addEventListener('DOMContentLoaded', function() {
    // 初始化圖表
    initializeTimeChart();
});

function initializeTimeChart() {
    // 獲取 canvas 元素
    const ctx = document.getElementById('trendChart').getContext('2d');
    
    // 圖表配置
    const chartConfig = {
        type: 'line',
        data: {
            labels: ['日期1', '日期2', '日期3'],
            datasets: [{
                label: '數值變化',
                data: [10, 20, 15],
                borderColor: 'rgb(75, 192, 192)',
                tension: 0.1
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: true,
            plugins: {
                title: {
                    display: true,
                    text: '時間變化趨勢'
                },
                legend: {
                    position: 'top',
                    labels: {
                        font: {
                            size: 14
                        }
                    }
                }
            },
            scales: {
                x: {
                    grid: {
                        display: false
                    }
                },
                y: {
                    beginAtZero: true,
                    grid: {
                        color: 'rgba(0, 0, 0, 0.1)'
                    }
                }
            }
        }
    };

    // 創建圖表
    const chart = new Chart(ctx, chartConfig);
}

// 如果需要更新數據的函數
function updateChartData(newData) {
    const chart = Chart.getChart('trendChart');
    if (chart) {
        chart.data.datasets[0].data = newData;
        chart.update();
    }
}