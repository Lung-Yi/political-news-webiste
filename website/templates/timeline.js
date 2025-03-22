// timeline.js

// 事件資料 - 在此處修改您的事件內容
const events = [
  {
    date: "【時間/階段1】",
    title: "【事件標題1】",
    description: "【簡短描述1】這裡填寫事件的簡短描述，一到兩句話即可。",
    details: "【詳細內容1】這裡可以填寫事件的詳細說明，可以包含多個句子，描述事件的背景、過程和結果等。這部分內容只有在用戶點擊「查看詳情」後才會顯示。"
  },
  {
    date: "【時間/階段2】",
    title: "【事件標題2】",
    description: "【簡短描述2】這裡填寫事件的簡短描述，說明這個階段的主要工作。",
    details: "【詳細內容2】這裡是事件的詳細說明，可以補充更多相關資訊。您可以描述這個階段的具體工作項目、達成的目標或面臨的挑戰等。"
  },
  {
    date: "【時間/階段3】",
    title: "【事件標題3】",
    description: "【簡短描述3】第三個事件的簡要說明，概述這一階段的關鍵點。",
    details: "【詳細內容3】第三個事件的詳細資訊。您可以在此處添加具體細節，例如參與人員、重要決策、關鍵成果等。這部分內容可以幫助讀者更全面地了解此事件。"
  },
  {
    date: "【時間/階段4】",
    title: "【事件標題4】",
    description: "【簡短描述4】第四個事件的簡要介紹，表明此階段的重點。",
    details: "【詳細內容4】這裡詳細描述第四個事件的完整內容。可以包括事件的前因後果、影響範圍、關聯事件等更深入的信息。您可以根據需要調整詳情的長度。"
  },
  {
    date: "【時間/階段5】",
    title: "【事件標題5】",
    description: "【簡短描述5】第五個事件的概述，簡明扼要地說明此階段的特點。",
    details: "【詳細內容5】在這裡展開描述第五個事件的細節。這部分內容應該對前面的簡短描述進行擴展，提供更多有價值的信息，幫助讀者深入理解事件的各個方面。"
  }
  // 您可以按照相同的格式添加更多事件，或刪減現有事件
];

// 創建時間線
function createTimeline() {
  const timelineEl = document.getElementById('timeline');
  
  events.forEach((event, index) => {
    const eventEl = document.createElement('div');
    eventEl.className = `event ${index % 2 === 0 ? 'left' : 'right'}`;
    
    const contentEl = document.createElement('div');
    contentEl.className = 'content';
    
    const dateEl = document.createElement('div');
    dateEl.className = 'date';
    dateEl.textContent = event.date;
    
    const titleEl = document.createElement('div');
    titleEl.className = 'title';
    titleEl.textContent = event.title;
    
    const descriptionEl = document.createElement('div');
    descriptionEl.className = 'description';
    descriptionEl.textContent = event.description;
    
    const detailsEl = document.createElement('div');
    detailsEl.className = 'details';
    detailsEl.textContent = event.details;
    
    // 添加「查看詳情」按鈕
    const expandBtn = document.createElement('span');
    expandBtn.className = 'expand-btn';
    expandBtn.textContent = '查看詳情 +';
    expandBtn.onclick = function() {
      if (detailsEl.style.display === 'block') {
        detailsEl.style.display = 'none';
        expandBtn.textContent = '查看詳情 +';
      } else {
        detailsEl.style.display = 'block';
        expandBtn.textContent = '收起 -';
      }
    };
    
    contentEl.appendChild(dateEl);
    contentEl.appendChild(titleEl);
    contentEl.appendChild(descriptionEl);
    contentEl.appendChild(detailsEl);
    contentEl.appendChild(expandBtn);
    
    eventEl.appendChild(contentEl);
    timelineEl.appendChild(eventEl);
  });
}

// 自定義函數 - 可以通過JavaScript動態添加新事件
// 使用方法: addNewEvent("您的日期", "您的標題", "您的描述", "您的詳細內容");
function addNewEvent(date, title, description, details) {
  const event = {
    date: date,
    title: title,
    description: description,
    details: details || ""
  };
  
  events.push(event);
  document.getElementById('timeline').innerHTML = "";
  createTimeline();
}

// 當整個頁面載入完畢後初始化時間線
window.addEventListener('load', function() {
  createTimeline();
});
