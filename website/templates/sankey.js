/**
 * 繪製桑基圖
 * @param {string} containerSelector - 桑基圖容器的 CSS 選擇器
 * @param {Object} customData - 可選的自訂數據，如果未提供則使用預設數據
 */
function drawSankey(containerSelector, customData) {
  // 檢查容器是否存在
  const container = d3.select(containerSelector);
  
  // 設置圖表尺寸和邊距
  const margin = {top: 20, right: 30, bottom: 20, left: 30};
  const width = Math.min(700, window.innerWidth - 50) - margin.left - margin.right;
  const height = 400 - margin.top - margin.bottom;
  
  // 清除容器內容
  container.html("");
  
  // 建立 SVG 畫布
  const svg = container.append("svg")
      .attr("width", width + margin.left + margin.right)
      .attr("height", height + margin.top + margin.bottom)
      .style("display", "block")
      .style("margin", "0 auto")
      .append("g")
      .attr("transform", `translate(${margin.left},${margin.top})`);
  
  // 建立 tooltip 元素
  let tooltip = d3.select("body").select(".sankey-tooltip");
  if (tooltip.empty()) {
      tooltip = d3.select("body").append("div")
          .attr("class", "sankey-tooltip")
          .style("position", "absolute")
          .style("padding", "6px")
          .style("background", "rgba(0, 0, 0, 0.7)")
          .style("color", "white")
          .style("border-radius", "3px")
          .style("pointer-events", "none")
          .style("font-size", "12px")
          .style("opacity", "0")
          .style("z-index", "1000");
  }
  
  // 使用自訂數據或預設範例數據
  const graph = customData || {
      nodes: [
          { node: 0, name: "來源 A" },
          { node: 1, name: "來源 B" },
          { node: 2, name: "來源 C" },
          { node: 3, name: "目標 D" },
          { node: 4, name: "目標 E" },
          { node: 5, name: "目標 F" }
      ],
      links: [
          { source: 0, target: 3, value: 5 },
          { source: 0, target: 4, value: 3 },
          { source: 1, target: 3, value: 2 },
          { source: 1, target: 4, value: 4 },
          { source: 1, target: 5, value: 2 },
          { source: 2, target: 5, value: 5 }
      ]
  };
  
  // 設定桑基圖參數
  const sankey = d3.sankey()
      .nodeWidth(20)
      .nodePadding(10)
      .extent([[0, 0], [width, height]]);
  
  // 計算桑基圖的佈局
  const sankeyData = sankey({
      nodes: graph.nodes.map(d => Object.assign({}, d)),
      links: graph.links.map(d => Object.assign({}, d))
  });
  
  // 定義顏色比例尺 - 根據節點 ID 分配顏色
  const colorScale = d3.scaleOrdinal()
      .domain(sankeyData.nodes.map(d => d.index))
      .range(d3.schemeCategory10);
  
  // 繪製連結（曲線）
  const links = svg.append("g")
      .selectAll(".sankey-link")
      .data(sankeyData.links)
      .join("path")
      .attr("class", "sankey-link")
      .attr("d", d3.sankeyLinkHorizontal())
      .attr("stroke", d => colorScale(d.source.index)) // 使用源節點的顏色
      .attr("stroke-width", d => Math.max(1, d.width))
      .attr("stroke-opacity", 0.5)
      .attr("fill", "none")
      .style("cursor", "pointer")
      .on("mouseover", handleLinkMouseOver)
      .on("mousemove", handleMouseMove)
      .on("mouseout", handleMouseOut);
  
  // 繪製節點（矩形）
  const nodes = svg.append("g")
      .selectAll(".sankey-node")
      .data(sankeyData.nodes)
      .join("rect")
      .attr("class", "sankey-node")
      .attr("x", d => d.x0)
      .attr("y", d => d.y0)
      .attr("height", d => d.y1 - d.y0)
      .attr("width", d => d.x1 - d.x0)
      .attr("fill", d => colorScale(d.index)) // 使用節點自己的顏色
      .attr("stroke", "#000")
      .style("cursor", "pointer")
      .on("mouseover", handleNodeMouseOver)
      .on("mousemove", handleMouseMove)
      .on("mouseout", handleMouseOut);
  
  // 添加節點標籤
  svg.append("g")
      .selectAll(".sankey-label")
      .data(sankeyData.nodes)
      .join("text")
      .attr("class", "sankey-label")
      .attr("x", d => d.x0 < width / 2 ? d.x1 + 6 : d.x0 - 6)
      .attr("y", d => (d.y1 + d.y0) / 2)
      .attr("dy", "0.35em")
      .attr("text-anchor", d => d.x0 < width / 2 ? "start" : "end")
      .text(d => d.name)
      .style("font-size", "10px")
      .style("fill", "#333")
      .style("pointer-events", "none");
  
  // 事件處理函數 - 連結懸停
  function handleLinkMouseOver(event, d) {
      // 突出顯示當前連結
      d3.select(this)
          .attr("stroke-opacity", 0.8)
          .attr("stroke-width", d => Math.max(2, d.width));
      
      // 顯示 tooltip
      tooltip.transition()
          .duration(200)
          .style("opacity", 0.9);
      
      tooltip.html(`
          <div style="font-weight: bold;">從 ${d.source.name} 到 ${d.target.name}</div>
          <div>數值: ${d.value}</div>
      `)
      .style("left", (event.pageX + 10) + "px")
      .style("top", (event.pageY - 28) + "px");
  }
  
  // 事件處理函數 - 節點懸停
  function handleNodeMouseOver(event, d) {
      // 突出顯示當前節點
      d3.select(this)
          .attr("stroke-width", 2);
      
      // 計算節點總流入和流出值
      const inflow = d3.sum(d.targetLinks || [], link => link.value) || 0;
      const outflow = d3.sum(d.sourceLinks || [], link => link.value) || 0;
      
      // 顯示 tooltip
      tooltip.transition()
          .duration(200)
          .style("opacity", 0.9);
      
      tooltip.html(`
          <div style="font-weight: bold;">${d.name}</div>
          <div>總流入: ${inflow}</div>
          <div>總流出: ${outflow}</div>
      `)
      .style("left", (event.pageX + 10) + "px")
      .style("top", (event.pageY - 28) + "px");
  }
  
  // 事件處理函數 - 鼠標移動
  function handleMouseMove(event) {
      tooltip
          .style("left", (event.pageX + 10) + "px")
          .style("top", (event.pageY - 28) + "px");
  }
  
  // 事件處理函數 - 鼠標離開
  function handleMouseOut() {
      // 恢復連結樣式
      links
          .attr("stroke-opacity", 0.5)
          .attr("stroke-width", d => Math.max(1, d.width));
      
      // 恢復節點樣式
      nodes
          .attr("stroke-width", 1);
      
      // 隱藏 tooltip
      tooltip.transition()
          .duration(500)
          .style("opacity", 0);
  }
}

/**
 * 使用新數據更新桑基圖
 * @param {string} containerSelector - 桑基圖容器的 CSS 選擇器
 * @param {Object} newData - 新的數據對象
 */
function updateSankeyData(containerSelector, newData) {
  if (!newData) {
      console.error("錯誤: 未提供更新數據");
      return;
  }
  
  // 使用新數據重新繪製桑基圖
  drawSankey(containerSelector, newData);
}