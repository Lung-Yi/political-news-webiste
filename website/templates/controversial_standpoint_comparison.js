/**
 * 爭議立場比較分析表 - JavaScript 控制檔案
 * 負責動態生成表格內容並套用數據
 */

// 等待 DOM 完全載入後執行
document.addEventListener('DOMContentLoaded', function() {
    // 載入比較資料
    loadComparisonData();
});

// 比較分析資料 - 包含示例數據
const comparisonData = {
    // === 基本信息區塊 ===
    title: "爭議立場比較分析表",
    topic: "【替換為您的議題】",
    positionA: "論點A",
    positionB: "論點B",
    description: "【替換為您的描述】",
    
    // === 議題比較區塊 ===
    issues: [
        // --- 議題1 ---
        {
            name: "爭議點1",
            aspects: [
                {
                    name: "核心論點",
                    positionA: "【替換為您的立場A論點】",
                    positionB: "【替換為您的立場B論點】"
                },
                {
                    name: "支持理據",
                    positionA: "【替換為您的支持數據】",
                    positionB: "【替換為您的支持數據】"
                },
                {
                    name: "代表人物/組織",
                    positionA: "【替換為您的代表人物或組織】",
                    positionB: "【替換為您的代表人物或組織】"
                },
                {
                    name: "潛在影響",
                    positionA: "【替換為您的潛在影響】",
                    positionB: "【替換為您的潛在影響】"
                }
            ]
        },
        
        // --- 議題2 ---
        {
            name: "爭議點2",
            aspects: [
                {
                    name: "核心論點",
                    positionA: "【替換為您的立場A論點】",
                    positionB: "【替換為您的立場B論點】"
                },
                {
                    name: "支持理據",
                    positionA: "【替換為您的支持數據】",
                    positionB: "【替換為您的支持數據】"
                },
                {
                    name: "代表人物/組織",
                    positionA: "【替換為您的代表人物或組織】",
                    positionB: "【替換為您的代表人物或組織】"
                },
                {
                    name: "潛在影響",
                    positionA: "【替換為您的潛在影響】",
                    positionB: "【替換為您的潛在影響】"
                }
            ]
        },
        
        // --- 歷史脈絡部分 ---
        {
            name: "爭議點3",
            aspects: [
                {
                    name: "起源/背景",
                    positionA: "【替換為您的歷史背景】",
                    positionB: "【替換為您的歷史背景】"
                },
                {
                    name: "演變過程",
                    positionA: "【替換為您的演變過程】",
                    positionB: "【替換為您的演變過程】"
                }
            ]
        }
    ],
    
    // === 總結與分析區塊 ===
    summary: "【替換為您的綜合比較分析】",
};

/**
 * 載入並顯示比較資料
 */
function loadComparisonData() {
    // 設置標題和描述
    document.getElementById('comparison-title').textContent = comparisonData.title;
    document.getElementById('analysis-description').textContent = comparisonData.description;
    
    // 設置立場標題
    document.querySelector('.position-a-header').textContent = comparisonData.positionA;
    document.querySelector('.position-b-header').textContent = comparisonData.positionB;
    
    // 生成表格內容
    generateTableContent();
    
    // 設置摘要和註釋
    document.querySelector('#comparison-summary p').textContent = comparisonData.summary;
    
}

/**
 * 生成表格內容
 */
function generateTableContent() {
    const tableBody = document.querySelector('#comparison-table tbody');
    tableBody.innerHTML = ''; // 清空現有內容
    
    // 遍歷每個議題
    comparisonData.issues.forEach(issue => {
        // 添加議題行
        const issueRow = document.createElement('tr');
        issueRow.className = 'issue-row';
        issueRow.innerHTML = `<td colspan="3">${issue.name}</td>`;
        tableBody.appendChild(issueRow);
        
        // 添加各方面比較行
        issue.aspects.forEach(aspect => {
            const aspectRow = document.createElement('tr');
            aspectRow.innerHTML = `
                <td>${aspect.name}</td>
                <td class="position-a-column">${aspect.positionA}</td>
                <td class="position-b-column">${aspect.positionB}</td>
            `;
            tableBody.appendChild(aspectRow);
        });
    });
}

/**
 * 更新比較資料
 * @param {Object} newData - 新的比較資料
 */
function updateComparisonData(newData) {
    // 合併新數據
    Object.assign(comparisonData, newData);
    
    // 重新載入數據到頁面
    loadComparisonData();
}

/**
 * 添加新議題
 * @param {Object} newIssue - 新議題對象
 */
function addNewIssue(newIssue) {
    // 添加新議題到數據中
    comparisonData.issues.push(newIssue);
    
    // 重新載入數據到頁面
    loadComparisonData();
}

/**
 * 移除議題
 * @param {number} issueIndex - 要移除的議題索引
 */
function removeIssue(issueIndex) {
    // 檢查索引是否有效
    if (issueIndex >= 0 && issueIndex < comparisonData.issues.length) {
        // 從數據中移除議題
        comparisonData.issues.splice(issueIndex, 1);
        
        // 重新載入數據到頁面
        loadComparisonData();
    }
}