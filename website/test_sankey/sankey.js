// 定義一個函式用來繪製桑基圖，並加入 tooltip 功能
function drawSankey(selector) {
    // 建立 tooltip 元素
    const tooltip = d3.select("body").append("div")
        .attr("class", "sankey-tooltip");
  
    // 範例資料：包含節點與連結資訊
    const graph = {
      nodes: [
        { node: 0, name: "來源 A" },
        { node: 1, name: "來源 B" },
        { node: 2, name: "目標 C" },
        { node: 3, name: "目標 D" }
      ],
      links: [
        { source: 0, target: 2, value: 5 },
        { source: 1, target: 2, value: 3 },
        { source: 1, target: 3, value: 2 }
      ]
    };
  
    const width = 700;
    const height = 400;
  
    // 建立 SVG 畫布
    const svg = d3.select(selector)
      .append("svg")
      .attr("width", width)
      .attr("height", height);
  
    // 設定桑基圖參數
    const sankey = d3.sankey()
      .nodeWidth(20)
      .nodePadding(10)
      .extent([[1, 1], [width - 1, height - 6]]);
  
    // 計算桑基圖的節點與連結位置（d3-sankey 會自動計算各節點的 value）
    const {nodes, links} = sankey({
      nodes: graph.nodes.map(d => Object.assign({}, d)),
      links: graph.links.map(d => Object.assign({}, d))
    });
  
    // 繪製連結（曲線）
    svg.append("g")
      .selectAll("path")
      .data(links)
      .enter()
      .append("path")
      .attr("class", "sankey-link")
      .attr("d", d3.sankeyLinkHorizontal())
      .attr("stroke-width", d => Math.max(1, d.width))
      .on("mouseover", function(event, d) {
        tooltip.transition().duration(200).style("opacity", 0.9);
        tooltip.html("連結數值: " + d.value)
               .style("left", (event.pageX + 10) + "px")
               .style("top", (event.pageY - 28) + "px");
      })
      .on("mousemove", function(event, d) {
        tooltip.style("left", (event.pageX + 10) + "px")
               .style("top", (event.pageY - 28) + "px");
      })
      .on("mouseout", function() {
        tooltip.transition().duration(500).style("opacity", 0);
      });
  
    // 繪製節點（矩形）
    svg.append("g")
      .selectAll("rect")
      .data(nodes)
      .enter()
      .append("rect")
      .attr("class", "sankey-node")
      .attr("x", d => d.x0)
      .attr("y", d => d.y0)
      .attr("height", d => d.y1 - d.y0)
      .attr("width", d => d.x1 - d.x0)
      .on("mouseover", function(event, d) {
        tooltip.transition().duration(200).style("opacity", 0.9);
        tooltip.html("節點: " + d.name + "<br/>數值: " + d.value)
               .style("left", (event.pageX + 10) + "px")
               .style("top", (event.pageY - 28) + "px");
      })
      .on("mousemove", function(event, d) {
        tooltip.style("left", (event.pageX + 10) + "px")
               .style("top", (event.pageY - 28) + "px");
      })
      .on("mouseout", function() {
        tooltip.transition().duration(500).style("opacity", 0);
      });
  
    // 加入節點文字標籤
    svg.append("g")
      .selectAll("text")
      .data(nodes)
      .enter()
      .append("text")
      .attr("class", "sankey-label")
      .attr("x", d => d.x0 - 6)
      .attr("y", d => (d.y1 + d.y0) / 2)
      .attr("dy", "0.35em")
      .attr("text-anchor", "end")
      .text(d => d.name)
      .filter(d => d.x0 < width / 2)
      .attr("x", d => d.x1 + 6)
      .attr("text-anchor", "start");
  }
  