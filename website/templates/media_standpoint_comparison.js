// media.js

// 定義媒體資料陣列 (請根據需要修改或擴充)
const mediaData = [
  {
    name: "[媒體名稱1]",
    angle: "[報導主要立場/觀點]",
    source: "[主要引述的消息來源]",
    focus: "[該媒體報導的重點和側重面向]"
  },
  {
    name: "[媒體名稱2]",
    angle: "[報導主要立場/觀點]",
    source: "[主要引述的消息來源]",
    focus: "[該媒體報導的重點和側重面向]"
  },
  {
    name: "[媒體名稱3]",
    angle: "[報導主要立場/觀點]",
    source: "[主要引述的消息來源]",
    focus: "[該媒體報導的重點和側重面向]"
  },
  {
    name: "[媒體名稱4]",
    angle: "[報導主要立場/觀點]",
    source: "[主要引述的消息來源]",
    focus: "[該媒體報導的重點和側重面向]"
  },
  {
    name: "[媒體名稱5]",
    angle: "[報導主要立場/觀點]",
    source: "[主要引述的消息來源]",
    focus: "[該媒體報導的重點和側重面向]"
  }
];

// 動態生成表格資料列
function populateTable() {
  const tableBody = document.querySelector("#mediaTable tbody");
  
  mediaData.forEach(item => {
    const tr = document.createElement("tr");

    const tdName = document.createElement("td");
    tdName.textContent = item.name;

    const tdAngle = document.createElement("td");
    tdAngle.textContent = item.angle;

    const tdSource = document.createElement("td");
    tdSource.textContent = item.source;

    const tdFocus = document.createElement("td");
    tdFocus.textContent = item.focus;

    tr.appendChild(tdName);
    tr.appendChild(tdAngle);
    tr.appendChild(tdSource);
    tr.appendChild(tdFocus);

    tableBody.appendChild(tr);
  });
}

// 動態生成「分析說明」與「資料來源」區塊
function createNotesAndSource() {
  const container = document.getElementById("mediaContainer");
  
  // 建立 Notes 區塊
  const notesDiv = document.createElement("div");
  notesDiv.className = "notes";
  const notesTitle = document.createElement("strong");
  notesTitle.textContent = "分析說明：";
  notesDiv.appendChild(notesTitle);
  const notesContent = document.createTextNode(" [在此補充對媒體立場差異的分析與解讀，可包含媒體政治傾向、報導視角差異原因、以及讀者應如何綜合各方報導獲取平衡視角等說明。]");
  notesDiv.appendChild(notesContent);

  // 建立 Source 區塊
  const sourceDiv = document.createElement("div");
  sourceDiv.className = "source";
  sourceDiv.textContent = "資料來源：[資料收集時間範圍] 各媒體報導綜合整理";

  // 將 Notes 與 Source 區塊添加到 container 最後
  container.appendChild(notesDiv);
  container.appendChild(sourceDiv);
}

// 頁面載入時呼叫初始化函數
window.addEventListener('load', function() {
  populateTable();
  createNotesAndSource();
});
