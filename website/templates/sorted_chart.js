// 數值排序分析圖表腳本

// 數據配置
const chartData = {
    // 圖表基本信息
    title: '數值分類排序分析',
    subtitle: '[分析主題]',
    description: '本視覺化呈現了[數據主題]的分類與排序分析，幫助理解[主題]的結構和分布特徵。',
    notes: '[在此補充關於數據來源、分析方法或結果解讀的詳細說明]',
    dataSource: '[資料來源]',
    
    // 圖表數據
    labels: ['類別A', '類別B', '類別C', '類別D', '類別E', '類別F', '類別G', '類別H'],
    values: [320, 420, 290, 380, 490, 230, 180, 150],
    
    // 圖表設置
    chartTitle: '[數據標題]（單位：[單位]）',
    xAxisTitle: '[x軸標題]（[單位]）',
    yAxisTitle: '[y軸標題]',
    unit: '[單位]',
    
    // 圖表高度設定
    chartHeight: 600  // 請根據資料的數量調整高度
};

// 初始化應用
function initSortedChartApp() {
    // 創建HTML結構
    createAppStructure();
    
    // 設置當前日期
    document.getElementById('update-date').textContent = new Date().toLocaleDateString('zh-TW');
    
    // 創建圖表
    createSortedChart();
}

// 創建應用HTML結構
function createAppStructure() {
    const appContainer = document.getElementById('sortedChartApp');
    
    appContainer.innerHTML = `
        <div class="sorted-chart-container">
            <h2 class="sorted-chart-title">${chartData.title}</h2>
            <h3 class="sorted-chart-subtitle">${chartData.subtitle}</h3>
            
            <div class="sorted-chart-description">
                ${chartData.description}
            </div>
            
            <div class="sorted-chart-canvas" style="height: ${chartData.chartHeight}px;">
                <canvas id="sortedBarChart"></canvas>
            </div>
            
            <div class="sorted-chart-notes">
                <strong>分析說明：</strong>
                ${chartData.notes}
            </div>
            
            <div class="sorted-chart-source">
                數據來源：${chartData.dataSource} | 最後更新：<span id="update-date"></span>
            </div>
        </div>
    `;
}

// 生成棕色漸變色彩
function generateBrownColors(values) {
    const sortedValues = [...values].sort((a, b) => a - b);
    
    return values.map(value => {
        const index = sortedValues.indexOf(value);
        const intensity = 0.4 + (index / (values.length - 1)) * 0.5;
        return `rgba(101, 67, 33, ${intensity})`;
    });
}

// 數據排序處理
function prepareSortedData(labels, values) {
    const combinedData = labels.map((label, index) => ({ 
        label, 
        value: values[index] 
    }));
    
    combinedData.sort((a, b) => b.value - a.value);
    
    return {
        sortedLabels: combinedData.map(item => item.label),
        sortedValues: combinedData.map(item => item.value)
    };
}

// 創建排序圖表
function createSortedChart() {
    // 排序數據
    const { sortedLabels, sortedValues } = prepareSortedData(
        chartData.labels, 
        chartData.values
    );
    
    // 生成顏色
    const colors = generateBrownColors(sortedValues);
    
    // 獲取畫布上下文
    const ctx = document.getElementById('sortedBarChart').getContext('2d');
    
    // 創建圖表
    new Chart(ctx, {
        type: 'bar',
        data: {
            labels: sortedLabels,
            datasets: [{
                label: chartData.chartTitle,
                data: sortedValues,
                backgroundColor: colors,
                borderColor: colors.map(color => color.replace(/, [\d\.]+\)/, ', 1)')),
                borderWidth: 1
            }]
        },
        options: {
            indexAxis: 'y',  // 水平條形圖
            responsive: true,
            maintainAspectRatio: true,
            plugins: {
                title: {
                    display: true,
                    text: chartData.chartTitle,
                    color: '#5d4037',
                    font: { size: 16, weight: 'bold' },
                    padding: { bottom: 20 }
                },
                legend: { display: false },
                tooltip: {
                    callbacks: {
                        label: function(context) {
                            return `${context.parsed.x} ${chartData.unit}`;
                        }
                    }
                }
            },
            scales: {
                x: {
                    beginAtZero: true,
                    title: {
                        display: true,
                        text: chartData.xAxisTitle,
                        color: '#6d4c41',
                        font: { weight: 'bold' }
                    },
                    grid: { color: 'rgba(137, 116, 107, 0.1)' },
                    ticks: { color: '#6d4c41' }
                },
                y: {
                    title: {
                        display: true,
                        text: chartData.yAxisTitle,
                        color: '#6d4c41',
                        font: { weight: 'bold' }
                    },
                    grid: { display: false },
                    ticks: {
                        color: '#6d4c41',
                        font: { weight: 'bold' }
                    },
                    // 增加條形圖間距設定
                    barPercentage: 0.9,
                    categoryPercentage: 0.8
                }
            },
            animation: {
                duration: 1500,
                easing: 'easeOutQuart'
            }
        }
    });
}

// 更新應用數據
function updateSortedChartApp(newData) {
    // 更新配置
    Object.assign(chartData, newData);
    
    // 重新初始化應用
    initSortedChartApp();
}

// 頁面載入時初始化應用
document.addEventListener('DOMContentLoaded', initSortedChartApp);