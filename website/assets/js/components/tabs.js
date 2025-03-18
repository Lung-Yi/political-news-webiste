/**
 * 分頁功能元件 - tabs.js
 * 實現分頁切換功能的 JavaScript 模組
 */

class Tabs {
    /**
     * 建立分頁元件
     * @param {string} containerSelector - 分頁容器選擇器
     * @param {string} tabSelector - 分頁按鈕選擇器
     * @param {string} contentSelector - 分頁內容選擇器
     * @param {Object} options - 其他選項
     */
    constructor(containerSelector, tabSelector, contentSelector, options = {}) {
        // 預設選項
        this.options = {
            activeClass: 'active',
            defaultTab: 0,
            onChange: null,
            ...options
        };
        
        // 取得 DOM 元素
        this.container = document.querySelector(containerSelector);
        
        // 如果容器不存在，則退出
        if (!this.container) return;
        
        this.tabs = this.container.querySelectorAll(tabSelector);
        this.contents = document.querySelectorAll(contentSelector);
        
        // 初始化
        this.init();
    }
    
    /**
     * 初始化分頁功能
     */
    init() {
        // 如果沒有分頁或內容，則退出
        if (!this.tabs.length || !this.contents.length) return;
        
        // 為每個分頁按鈕添加點擊事件
        this.tabs.forEach((tab, index) => {
            tab.addEventListener('click', () => {
                this.activateTab(index);
            });
            
            // 增加無障礙支援
            tab.setAttribute('role', 'tab');
            tab.setAttribute('aria-selected', index === this.options.defaultTab ? 'true' : 'false');
            tab.setAttribute('tabindex', index === this.options.defaultTab ? '0' : '-1');
            
            // 如果分頁按鈕沒有 id，添加一個
            if (!tab.id) {
                tab.id = `tab-${index}`;
            }
        });
        
        // 為每個內容區塊添加屬性
        this.contents.forEach((content, index) => {
            content.setAttribute('role', 'tabpanel');
            content.setAttribute('aria-labelledby', this.tabs[index].id);
            content.style.display = index === this.options.defaultTab ? 'block' : 'none';
        });
        
        // 設置默認分頁
        this.activateTab(this.options.defaultTab);
        
        // 添加鍵盤導航
        this.addKeyboardSupport();
    }
    
    /**
     * 激活指定索引的分頁
     * @param {number} index - 分頁索引
     */
    activateTab(index) {
        // 停用所有分頁
        this.tabs.forEach((tab, i) => {
            tab.classList.remove(this.options.activeClass);
            tab.setAttribute('aria-selected', 'false');
            tab.setAttribute('tabindex', '-1');
        });
        
        // 隱藏所有內容
        this.contents.forEach((content) => {
            content.style.display = 'none';
        });
        
        // 激活選定的分頁
        this.tabs[index].classList.add(this.options.activeClass);
        this.tabs[index].setAttribute('aria-selected', 'true');
        this.tabs[index].setAttribute('tabindex', '0');
        
        // 顯示選定的內容
        this.contents[index].style.display = 'block';
        
        // 如果有定義 onChange 回調，則執行它
        if (this.options.onChange && typeof this.options.onChange === 'function') {
            this.options.onChange(index, this.tabs[index], this.contents[index]);
        }
    }
    
    /**
     * 添加鍵盤導航支持
     */
    addKeyboardSupport() {
        // 獲取所有分頁的索引
        const tabsArray = Array.from(this.tabs);
        
        // 鍵盤事件
        this.container.addEventListener('keydown', (event) => {
            // 當前活動標籤的索引
            const currentIndex = tabsArray.findIndex(tab => tab.getAttribute('aria-selected') === 'true');
            
            let nextIndex;
            
            // 根據鍵盤輸入計算下一個索引
            switch (event.key) {
                case 'ArrowLeft':
                    nextIndex = currentIndex > 0 ? currentIndex - 1 : tabsArray.length - 1;
                    break;
                case 'ArrowRight':
                    nextIndex = currentIndex < tabsArray.length - 1 ? currentIndex + 1 : 0;
                    break;
                case 'Home':
                    nextIndex = 0;
                    break;
                case 'End':
                    nextIndex = tabsArray.length - 1;
                    break;
                default:
                    return; // 如果不是預期的鍵，則不執行任何操作
            }
            
            // 激活下一個分頁
            this.activateTab(nextIndex);
            
            // 焦點移到新的活動分頁
            this.tabs[nextIndex].focus();
            
            // 防止默認行為（例如，滾動）
            event.preventDefault();
        });
    }
}

// 當 DOM 加載完成後初始化分頁
document.addEventListener('DOMContentLoaded', function() {
    // 初始化新聞分類分頁
    const newsTabs = new Tabs('.category-tabs', '.tab', '.news-card', {
        onChange: function(index, tab, content) {
            // 獲取所有新聞卡片
            const allCards = document.querySelectorAll('.news-card');
            
            // 獲取當前分頁的類別
            const category = tab.dataset.category;
            
            // 過濾卡片
            allCards.forEach((card) => {
                if (category === 'all' || card.dataset.category === category) {
                    card.style.display = 'flex';
                } else {
                    card.style.display = 'none';
                }
            });
        }
    });
});

// 匯出 Tabs 類別以供其他檔案使用
export default Tabs;
