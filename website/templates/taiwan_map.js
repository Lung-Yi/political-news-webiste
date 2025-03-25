/**
 * 台灣地理環境區域分布圖
 */

// 設置當前日期
document.getElementById('update-date').textContent = new Date().toLocaleDateString('zh-TW');

// 台灣縣市數據
const taiwanData = [
    { city: '臺北市', value: 95 }, { city: '新北市', value: 88 },
    { city: '基隆市', value: 45 }, { city: '桃園市', value: 78 },
    { city: '新竹市', value: 72 }, { city: '新竹縣', value: 65 },
    { city: '苗栗縣', value: 58 }, { city: '臺中市', value: 85 },
    { city: '彰化縣', value: 62 }, { city: '南投縣', value: 42 },
    { city: '雲林縣', value: 53 }, { city: '嘉義市', value: 57 },
    { city: '嘉義縣', value: 49 }, { city: '臺南市', value: 76 },
    { city: '高雄市', value: 82 }, { city: '屏東縣', value: 61 },
    { city: '宜蘭縣', value: 55 }, { city: '花蓮縣', value: 47 },
    { city: '臺東縣', value: 39 }, { city: '澎湖縣', value: 35 },
    { city: '金門縣', value: 32 }, { city: '連江縣', value: 28 }
];

// 地圖配置
const mapConfig = {
    title: '[數據標題]（單位：[單位]）',
    indicator: '[指標名稱]',
    unit: '[單位]'
};

// 定義棕色系顏色範圍
function getColor(value, min, max) {
    const normalized = (value - min) / (max - min);
    const r = Math.round(233 - normalized * 132);
    const g = Math.round(212 - normalized * 145);
    const b = Math.round(185 - normalized * 152);
    return `rgb(${r}, ${g}, ${b})`;
}

// 創建自定義圖例
function createCustomLegend(min, max) {
    const legendDiv = document.getElementById('customLegend');
    legendDiv.innerHTML = '';
    const steps = 5;
    
    for (let i = 0; i < steps; i++) {
        const value = min + (max - min) * i / (steps - 1);
        const color = getColor(value, min, max);
        
        const legendItem = document.createElement('div');
        legendItem.className = 'taiwan-map-legend-item';
        
        const colorBox = document.createElement('div');
        colorBox.className = 'taiwan-map-legend-color';
        colorBox.style.backgroundColor = color;
        
        const label = document.createElement('div');
        label.className = 'taiwan-map-legend-label';
        label.textContent = Math.round(value) + (i === steps - 1 ? '+' : '');
        
        legendItem.appendChild(colorBox);
        legendItem.appendChild(label);
        legendDiv.appendChild(legendItem);
    }
}

// 創建台灣地圖
async function createMap() {
    try {
        // 載入台灣縣市地圖數據
        const response = await fetch('https://raw.githubusercontent.com/Lung-Yi/data/refs/heads/main/taiwan_map.geo.json');
        const taiwanGeoJson = await response.json();
        document.getElementById('loading').style.display = 'none';
        
        // 計算數值範圍
        const values = taiwanData.map(d => d.value);
        const minValue = Math.min(...values);
        const maxValue = Math.max(...values);
        
        // 創建數據集
        const choroplethData = taiwanGeoJson.features.map(feature => {
            const countyName = feature.properties.COUNTYNAME;
            const dataItem = taiwanData.find(item => item.city === countyName);
            return {
                feature: feature,
                value: dataItem ? dataItem.value : 0
            };
        });
        
        // 創建Chart.js的Choropleth地圖
        new Chart(document.getElementById('taiwanMap').getContext('2d'), {
            type: 'choropleth',
            data: {
                labels: taiwanGeoJson.features.map(f => f.properties.COUNTYNAME),
                datasets: [{
                    label: mapConfig.indicator,
                    data: choroplethData,
                    borderColor: '#FFF',
                    borderWidth: 1,
                    backgroundColor: function(context) {
                        return getColor(context.raw?.value || 0, minValue, maxValue);
                    },
                    outline: taiwanGeoJson.features
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                showOutline: true,
                showGraticule: false,
                plugins: {
                    title: {
                        display: true,
                        text: mapConfig.title,
                        color: '#5d4037',
                        font: { size: 16, weight: 'bold' },
                        padding: { bottom: 20 }
                    },
                    legend: { display: false },
                    tooltip: {
                        callbacks: {
                            label: function(context) {
                                const countyName = context.label;
                                const dataItem = taiwanData.find(item => item.city === countyName);
                                return dataItem ? 
                                    `${countyName}: ${dataItem.value} ${mapConfig.unit}` : 
                                    `${countyName}: 無數據`;
                            }
                        }
                    }
                },
                scales: {
                    projection: {
                        axis: 'x',
                        projection: 'mercator'
                    }
                }
            }
        });
        
        // 創建圖例
        createCustomLegend(minValue, maxValue);
        
    } catch (error) {
        console.error('地圖載入失敗:', error);
        const loadingElement = document.getElementById('loading');
        loadingElement.classList.add('taiwan-map-error');
        loadingElement.innerHTML = `
            <div>地圖載入失敗。請確保已正確引入台灣地理數據和所有必要套件。<br>
            錯誤信息: ${error.message}</div>
        `;
    }
}

// 更新地圖數據的簡化函數
function updateMapData(newData, newConfig) {
    if (newData && Array.isArray(newData)) {
        taiwanData.length = 0;
        taiwanData.push(...newData);
    }
    if (newConfig) Object.assign(mapConfig, newConfig);
    createMap();
}

// 啟動地圖創建
document.addEventListener('DOMContentLoaded', createMap);