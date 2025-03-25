TRANSLATION_DICT = {
    "時間變化趨勢圖": "time_trend",
    "數值分類排序": "sorted_chart",
    "台灣地理區域數值分布圖": "taiwan_map",
    "重大時間線軸圖": "timeline",
    "比例圓餅圖": "piechart",
    "新聞媒體立場分析比較表": "media_standpoint_comparison",
    "爭議立場比較分析表": "controversial_standpoint_comparison",
    "桑基圖": "sankey"
}

TOOL_TO_HTML_FRAGMENT_MAPPING = {
    "time_trend": 
    """
    <div class="chart-container">
        <canvas id="trendChart"></canvas>
    </div>
    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
    <script src="https://cdn.jsdelivr.net/npm/chartjs-plugin-annotation"></script>
    <script src="time_trend.js"></script>
    """,
    "sorted_chart": 
    """
    <div id="sortedChartApp"></div>
    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
    <script src="sorted_chart.js"></script>
    """,
    "taiwan_map": 
    """
    <div class="taiwan-map-container">
        <h2 class="taiwan-map-title">[分析主題]</h2>
        <h3 class="taiwan-map-subtitle">[分析時間或範圍]</h3>
        
        <div class="taiwan-map-description">
            <!-- 這裡填入數據描述 -->
        </div>
        
        <div class="taiwan-map-chart-container">
            <div class="taiwan-map-loading" id="loading">載入地圖中...</div>
            <canvas id="taiwanMap"></canvas>
        </div>
        
        <div class="taiwan-map-legend" id="customLegend"></div>
        
        <div class="taiwan-map-notes">
            <strong>分析說明：</strong>
            <!-- 這裡將由 AI 填入分析說明 -->
            地圖顏色深淺表示[指標名稱]的高低，顏色越深表示數值越高。[在此補充關於數據、分析方法或結果解讀的詳細說明]。
        </div>
        
        <div class="taiwan-map-data-source">
            數據來源：[資料來源] | 最後更新：<span id="update-date"></span>
        </div>
    </div>
    <script src="https://cdn.jsdelivr.net/npm/chartjs-chart-geo@4.2.2/build/index.umd.min.js"></script>
    <script src="https://d3js.org/d3-array.v2.min.js"></script>
    <script src="https://d3js.org/d3-geo.v2.min.js"></script>
    <script src="https://d3js.org/d3-format.v2.min.js"></script>
    <script src="https://d3js.org/d3-fetch.v2.min.js"></script>
    <script src="https://d3js.org/topojson-client.v3.min.js"></script>
    <script src="taiwan-map.js"></script>
    """,
    "timeline": 
    """
    <div class="container">
        <h2>【您的時間線標題】</h2>
        <div class="timeline" id="timeline">
            <!-- 事件會透過JavaScript動態添加 -->
        </div>
    </div>
    <script src="timeline.js"></script>
    """,
    "piechart": 
    """
    <div class="pie-chart-container">
        <canvas id="pieChart"></canvas>
    </div>
    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
    <script src="https://cdn.jsdelivr.net/npm/chartjs-plugin-datalabels"></script>
    <script src="piechart.js"></script>
    """,
    "media_standpoint_comparison": 
    """
    <div class="container" id="mediaContainer">
        <h2>媒體立場分析</h2>
        <div class="analysis-description">
        本表格分析[議題名稱]的報導角度、引述來源及關注焦點，
        </div>
        <table class="media-table" id="mediaTable">
        <thead>
            <tr>
            <th>媒體</th>
            <th>報導角度</th>
            <th>引述來源</th>
            <th>關注焦點</th>
            </tr>
        </thead>
        <tbody>
            <!-- 表格資料將由 JavaScript 動態產生 -->
        </tbody>
        </table>
    </div>
    <script src="media_standpoint_comparison.js"></script>
    """,
    "controversial_standpoint_comparison":
    """
    <h2 id="comparison-title"></h2>
    <div id="analysis-description" class="analysis-description"></div>
    <!-- 表格區域 -->
    <div class="position-comparison-table">
        <table id="comparison-table">
            <thead>
                <tr>
                    <th class="aspect-column">爭議面向</th>
                    <th class="position-header position-a-header"></th>
                    <th class="position-header position-b-header"></th>
                </tr>
            </thead>
            <tbody>
                <!-- 表格內容將由JavaScript動態生成 -->
            </tbody>
        </table>
    </div>
    <script src="controversial_standpoint_comparison.js"></script>
    """,
    "sankey":
    """
    <div class="sankey-container">
        <script src="sankey.js"></script>
        <script>
            // 頁面載入後呼叫 drawSankey() 繪製圖形
            drawSankey(".sankey-container");
        </script>
    </div>
    <script src="https://d3js.org/d3.v6.min.js"></script>
    <script src="https://unpkg.com/d3-sankey@0.12.3/dist/d3-sankey.min.js"></script>
    """
}
