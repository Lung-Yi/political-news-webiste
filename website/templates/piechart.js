// piechart.js

// 定義圓餅圖的資料與顏色
const pieData = {
    labels: ['類別1', '類別2', '類別3'],
    datasets: [{
      data: [300, 50, 100],
      backgroundColor: [
        'rgb(255, 99, 132)',
        'rgb(54, 162, 235)',
        'rgb(255, 205, 86)'
      ]
    }]
  };
  
// 定義圓餅圖的選項設定
const pieOptions = {
  responsive: true,
  maintainAspectRatio: true,
  plugins: {
    title: {
      display: true,
      text: '比例分布',
      font: {
        size: 24  // 修改這裡的數值以設定標題字體大小
      }
    },
    legend: {
      labels: {
        font: {
          size: 14  // 修改這裡設定圖例文字大小
        }
      }
    }
  }
};

  
// 等待頁面完全載入後再初始化圓餅圖
window.addEventListener('load', function() {
    const ctx = document.getElementById('pieChart').getContext('2d');
    new Chart(ctx, {
      type: 'pie',
      data: pieData,
      options: pieOptions
    });
});
  