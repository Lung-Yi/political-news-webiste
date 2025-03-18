import asyncio
import datetime
import random
import re
import time
from urllib.parse import quote
import pandas as pd
import pymongo
from pymongo import MongoClient
from playwright.async_api import async_playwright
from bs4 import BeautifulSoup
import json
import os

class NewsSpiderPlaywright:
    def __init__(self, mongo_uri="mongodb://localhost:27017/", db_name="news_database", headless=True):
        """初始化爬蟲
        
        Args:
            mongo_uri: MongoDB 連接 URI
            db_name: 數據庫名稱
            headless: 是否使用無頭模式 (True表示不顯示瀏覽器界面)
        """
        self.mongo_uri = mongo_uri
        self.db_name = db_name
        self.headless = headless
        self.base_url = "https://www.google.com/search"
        self.today = datetime.datetime.now()
        self.results = []
        
        # 設置 MongoDB 連接
        self.client = MongoClient(mongo_uri)
        self.db = self.client[db_name]
        self.collection = self.db["news_articles"]
        
        # 確保索引存在（用於快速查詢和防止重複）
        self.collection.create_index([("網址", pymongo.ASCENDING)], unique=True)
        
        # 創建調試目錄
        os.makedirs("debug", exist_ok=True)
        
    async def initialize_browser(self):
        """初始化 Playwright 瀏覽器"""
        self.playwright = await async_playwright().start()
        
        # 使用 chromium 瀏覽器 (你也可以選擇 firefox 或 webkit)
        self.browser = await self.playwright.chromium.launch(
            headless=self.headless,
            args=['--disable-blink-features=AutomationControlled'],  # 避免被檢測為自動化
        )
        
        # 創建上下文與頁面
        self.context = await self.browser.new_context(
            viewport={'width': 1366, 'height': 768},
            user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/96.0.4664.110 Safari/537.36',
            locale='zh-TW',
            timezone_id='Asia/Taipei',
        )
        
        # 設置隱匿模式
        await self.context.add_init_script("""
            Object.defineProperty(navigator, 'webdriver', {
                get: () => undefined
            });
        """)
        
        # 創建頁面
        self.page = await self.context.new_page()
        
        # 設置請求攔截
        await self.page.route("**/*", lambda route: self._route_intercept(route))
    
    async def _route_intercept(self, route):
        """攔截請求並修改"""
        # 如果是圖片或字體等資源，可以考慮阻止加載以提高性能
        if route.request.resource_type in ["image", "font", "media"]:
            await route.abort()
        else:
            # 繼續其他請求
            await route.continue_()
    
    async def close(self):
        """關閉瀏覽器和 MongoDB 連接"""
        if hasattr(self, 'browser'):
            await self.browser.close()
        
        if hasattr(self, 'playwright'):
            await self.playwright.stop()
        
        if hasattr(self, 'client'):
            self.client.close()
            print("MongoDB 連接已關閉")
    
    async def search_news(self, keyword, days=10, max_pages=3):
        """搜索指定關鍵字的新聞
        
        Args:
            keyword: 搜索關鍵字
            days: 搜索的時間範圍（天數）
            max_pages: 最多抓取的頁數
            
        Returns:
            搜索結果列表
        """
        # 重置結果列表
        self.results = []
        
        # 計算日期範圍
        ten_days_ago = self.today - datetime.timedelta(days=days)
        date_str = ten_days_ago.strftime('%Y-%m-%d')
        
        # 構建查詢URL
        search_params = {
            'q': keyword,               # 搜索關鍵詞
            'tbm': 'nws',               # 切換到新聞搜索
            'hl': 'zh-TW',              # 語言設置為繁體中文
            'gl': 'tw',                 # 地理位置設置為台灣
            'tbs': f'qdr:d{days}',      # 時間範圍（最近X天）
            'lr': 'lang_zh-TW'          # 進一步指定語言篩選
        }
        
        # 構建查詢URL字符串
        query_parts = []
        for key, value in search_params.items():
            query_parts.append(f"{key}={quote(value) if key == 'q' else value}")
        
        search_url = f"{self.base_url}?{'&'.join(query_parts)}"
        print(f"搜索URL: {search_url}")
        
        try:
            # 訪問搜索頁面
            await self.page.goto(search_url, wait_until='networkidle')
            
            # 處理可能的 Cookie 同意對話框
            try:
                await self.page.wait_for_selector('button:has-text("同意")', timeout=3000)
                await self.page.click('button:has-text("同意")')
                await self.page.wait_for_timeout(1000)  # 等待對話框消失
            except:
                print("沒有出現 Cookie 同意對話框或已處理")
            
            # 循環處理多頁
            for page_num in range(max_pages):
                print(f"\n正在處理第 {page_num + 1} 頁")
                
                # 等待頁面完全加載
                await self.page.wait_for_load_state('networkidle')
                await self.page.wait_for_timeout(2000)  # 額外等待確保 JS 執行完畢
                
                # 保存當前頁面源碼，用於調試
                html_content = await self.page.content()
                debug_file = f"debug/google_news_page{page_num + 1}.html"
                with open(debug_file, "w", encoding="utf-8") as f:
                    f.write(html_content)
                print(f"已保存頁面源碼到 {debug_file}")
                
                # 截圖保存，用於視覺調試
                screenshot_file = f"debug/page{page_num + 1}_screenshot.png"
                await self.page.screenshot(path=screenshot_file, full_page=True)
                print(f"已保存頁面截圖到 {screenshot_file}")
                
                # 使用 BeautifulSoup 解析 HTML
                soup = BeautifulSoup(html_content, 'html.parser')
                
                # 尋找新聞元素 - 嘗試多種選擇器
                selectors = [
                    'div.SoaBEf', 'div.WlydOe', 'div.xuvV6b',         # 常見選擇器
                    'div.Gx5Zad', 'g-card.ftSUBd', 'div.v7W49e',      # 備用選擇器
                    'div.AxJnfb', 'div.gG0TJc', 'div.EBajQe',         # 2022-2023 選擇器
                    'g-card.NhGnPc', 'g-card.uCCJvd', 'div.AELFGd',   # 更多備用
                ]
                
                # 也嘗試使用 Playwright 選擇器定位新聞元素
                news_found = False
                for selector in selectors:
                    try:
                        news_elements = await self.page.query_selector_all(selector)
                        if news_elements and len(news_elements) > 0:
                            news_found = True
                            print(f"找到 {len(news_elements)} 條新聞，使用選擇器: {selector}")
                            
                            # 解析每個新聞元素
                            for i, elem in enumerate(news_elements):
                                print(f"  處理第 {i+1}/{len(news_elements)} 條新聞...")
                                
                                # 獲取元素的 HTML 並解析
                                elem_html = await elem.inner_html()
                                elem_soup = BeautifulSoup(f"<div>{elem_html}</div>", 'html.parser')
                                
                                await self._parse_news_element(elem_soup, keyword)
                                
                                # 隨機暫停一下，模擬人類行為
                                await self.page.wait_for_timeout(random.randint(500, 1500))
                            
                            break  # 找到並處理新聞後，無需嘗試其他選擇器
                    except Exception as e:
                        print(f"使用選擇器 {selector} 時出錯: {e}")
                
                # 如果上面的方法都失敗，嘗試直接分析結構
                if not news_found:
                    print("未能使用預定選擇器找到新聞，嘗試直接分析頁面...")
                    # 尋找所有包含標題特徵的元素
                    potential_news = []
                    
                    # 尋找所有可能的標題元素
                    headings = soup.find_all(['h3', 'h2'])
                    for heading in headings:
                        # 找到包含標題的父容器
                        parent = heading.find_parent('div')
                        if parent and parent not in potential_news:
                            potential_news.append(parent)
                    
                    print(f"找到 {len(potential_news)} 個可能的新聞元素")
                    
                    # 處理這些可能的新聞元素
                    for i, elem in enumerate(potential_news):
                        print(f"  處理可能的新聞 {i+1}/{len(potential_news)}...")
                        await self._parse_news_element(elem, keyword)
                
                # 總結當前頁的結果
                print(f"第 {page_num + 1} 頁處理完成，目前共找到 {len(self.results)} 條新聞")
                
                # 如果已經是最後一頁或沒有更多結果，則退出
                if page_num + 1 >= max_pages:
                    break
                
                # 點擊下一頁
                try:
                    # 等待下一頁按鈕出現
                    next_button = await self.page.query_selector('a#pnnext, a[aria-label="下一頁"]')
                    if next_button:
                        print("找到下一頁按鈕，正在點擊...")
                        await next_button.click()
                        # 等待頁面加載
                        await self.page.wait_for_timeout(3000)
                    else:
                        print("沒有找到下一頁按鈕，可能已到最後一頁")
                        break
                except Exception as e:
                    print(f"點擊下一頁時出錯: {e}")
                    break
            
            print(f"\n搜索完成，總共找到 {len(self.results)} 條新聞")
            return self.results
            
        except Exception as e:
            print(f"搜索過程中發生錯誤: {e}")
            import traceback
            traceback.print_exc()
            return self.results
    
    async def _parse_news_element(self, elem, keyword):
        """解析新聞元素
        
        Args:
            elem: BeautifulSoup 元素
            keyword: 搜索關鍵字
        """
        try:
            # 提取標題
            title_elem = elem.select_one('h3, h2, a[data-ved], a.WlydOe')
            if not title_elem:
                # 尋找任何看起來像標題的元素
                all_links = elem.find_all('a')
                for link in all_links:
                    if link.text and len(link.text.strip()) > 15:
                        title_elem = link
                        break
            
            if not title_elem:
                print("  無法找到標題元素，跳過")
                return
            
            title = title_elem.get_text().strip()
            if not title:
                print("  標題為空，跳過")
                return
            
            # 提取鏈接
            link = ""
            if title_elem.name == 'a' and 'href' in title_elem.attrs:
                link = title_elem['href']
            else:
                link_elem = title_elem.find('a') or elem.find('a')
                if link_elem and 'href' in link_elem.attrs:
                    link = link_elem['href']
            
            # 處理Google搜索結果中的鏈接重定向
            if link.startswith('/url?') or ('google.com/url' in link):
                try:
                    # 提取實際URL
                    import urllib.parse as urlparse
                    parsed = urlparse.urlparse(link)
                    link_params = urlparse.parse_qs(parsed.query)
                    if 'q' in link_params:
                        link = link_params['q'][0]
                    elif 'url' in link_params:
                        link = link_params['url'][0]
                except Exception as e:
                    print(f"  解析URL失敗: {e}")
            
            # 確保鏈接是完整的URL
            if link and not link.startswith('http'):
                if link.startswith('/'):
                    link = f"https://www.google.com{link}"
                else:
                    print(f"  鏈接格式不正確: {link}")
                    return
            
            if not link:
                print("  未找到有效鏈接，跳過")
                return
            
            # 提取發布商/來源
            publisher = "未知來源"
            publisher_selectors = [
                'div.UPmit', 'span.xQ82C', 'div.CEMjEf', 'div.csDOgf', 
                'div.NUnG9d', 'span.L8PZAb', 'div.BNeawe.UPmit.AP7Wnd'
            ]
            
            for selector in publisher_selectors:
                pub_elem = elem.select_one(selector)
                if pub_elem:
                    publisher = pub_elem.get_text().strip()
                    break
            
            # 提取時間
            publish_time_text = ""
            time_selectors = [
                'span.WG9SHc', 'div.OSrXXb', 'span[aria-label]', 
                'div.s3v9rd', 'span.r0bn4c', 'span.qXLe6d'
            ]
            
            for selector in time_selectors:
                time_elem = elem.select_one(selector)
                if time_elem:
                    publish_time_text = time_elem.get_text().strip()
                    break
            
            # 如果沒有找到明確的時間元素，嘗試從發布商資訊中提取
            if not publish_time_text:
                # 尋找常見的時間格式，如 "來源 - 3天前"
                time_match = re.search(r'[-–]\s*(\d+\s*[分鐘小時天週月年]前)', publisher)
                if time_match:
                    publish_time_text = time_match.group(1)
                    # 清理發布商名稱
                    publisher = publisher.split(time_match.group(0))[0].strip()
            
            publish_time = self._parse_relative_time(publish_time_text) if publish_time_text else datetime.datetime.now().isoformat()
            
            # 提取摘要
            summary = ""
            summary_selectors = [
                'div.GI74Re', 'div.VwiC3b', 'div.Y3v8qd', 
                'div.s3v9rd', 'div.LHPb5d', 'div.BNeawe.s3v9rd.AP7Wnd'
            ]
            
            for selector in summary_selectors:
                summary_elem = elem.select_one(selector)
                if summary_elem:
                    summary = summary_elem.get_text().strip()
                    break
            
            # 擷取文章内容
            print(f"  正在擷取文章: {title[:30]}...")
            try:
                article_content = await self._get_article_content(link)
            except Exception as e:
                print(f"  擷取內容出錯: {e}")
                article_content = summary if summary else "無法獲取內容"
            
            # 構建新聞數據
            news_data = {
                "標題": title,
                "出版社": publisher,
                "發布時間": publish_time,
                "網址": link,
                "內容": article_content,
                "摘要": summary,
                "關鍵字": keyword,
                "抓取時間": datetime.datetime.now().isoformat()
            }
            
            # 檢查是否已存在相同標題和來源的新聞
            duplicate = False
            for existing in self.results:
                if existing["標題"] == title and existing["出版社"] == publisher:
                    print(f"  跳過重複新聞: {title[:30]}...")
                    duplicate = True
                    break
            
            if not duplicate:
                self.results.append(news_data)
                print(f"  成功解析: {title[:30]}... | {publisher}")
            
        except Exception as e:
            print(f"  解析新聞元素時出錯: {e}")
    
    async def _get_article_content(self, url):
        """獲取文章詳細內容
        
        Args:
            url: 文章URL
            
        Returns:
            文章內容
        """
        try:
            print(f"  訪問文章頁面: {url}")
            # 創建新頁面來獲取文章，避免影響主搜索頁面
            article_page = await self.context.new_page()
            
            # 設置較寬鬆的超時
            article_page.set_default_timeout(30000)
            
            # 訪問文章頁面
            await article_page.goto(url, wait_until='domcontentloaded')
            
            # 等待一段時間讓頁面完全加載
            await article_page.wait_for_timeout(3000)
            
            # 獲取頁面源碼
            html_content = await article_page.content()
            
            # 解析HTML
            soup = BeautifulSoup(html_content, 'html.parser')
            
            # 移除不必要的元素
            for tag in soup(['script', 'style', 'iframe', 'aside', 'nav', 'footer', 'header', 'meta', 'noscript']):
                tag.decompose()
            
            # 嘗試多種常見的文章內容選擇器
            content_selectors = [
                'article', '.article-content', '.story-body', '.post-content',
                '.news-content', '.content-detail', '.article-body', '.story-content',
                '.article-text', '.story-text', '.news-article-content', '.article__content', 
                '#story_body_content', '.news-detail', '#article-content', '.newsContent',
                '.content', '#mainContent', '.main-content', '.entry-content',
                '.post-body', '.cms-body', '.news-body', '.news-text'
            ]
            
            content = ""
            for selector in content_selectors:
                content_elem = soup.select_one(selector)
                if content_elem:
                    # 獲取所有段落
                    paragraphs = content_elem.find_all('p')
                    if paragraphs:
                        content = '\n'.join([p.get_text().strip() for p in paragraphs])
                        break
            
            # 如果使用選擇器沒有找到內容，嘗試獲取所有段落
            if not content:
                # 找出所有段落
                paragraphs = soup.find_all('p')
                filtered_paragraphs = [p.get_text().strip() for p in paragraphs 
                                       if len(p.get_text().strip()) > 50  # 過濾過短的段落
                                       and not re.search(r'cookie|©|版權|關注我們|訂閱電子報|下載APP|廣告', p.get_text(), re.IGNORECASE)]  # 過濾不相關內容
                
                if filtered_paragraphs:
                    content = '\n'.join(filtered_paragraphs)
                else:
                    # 最後嘗試獲取頁面中的所有文本
                    content = soup.get_text().strip()
                    # 清理內容，移除多余空白行
                    content = re.sub(r'\n\s*\n', '\n\n', content)
            
            # 關閉文章頁面
            await article_page.close()
            
            # 清理編碼問題
            content = content.encode('utf-8', errors='replace').decode('utf-8')
            
            return content
            
        except Exception as e:
            print(f"  獲取文章內容時出錯: {e}")
            return f"無法獲取內容: {str(e)}"
    
    def _parse_relative_time(self, time_text):
        """解析相對時間字符串為ISO格式日期時間
        
        Args:
            time_text: 相對時間字符串，如"3小時前"
            
        Returns:
            ISO格式的時間字符串
        """
        now = datetime.datetime.now()
        
        # 處理空字符串
        if not time_text:
            return now.isoformat()
            
        # 解析相對時間
        try:
            # 匹配常見的相對時間格式
            if '分鐘前' in time_text:
                minutes = int(re.search(r'(\d+)\s*分鐘前', time_text).group(1))
                dt = now - datetime.timedelta(minutes=minutes)
            elif '小時前' in time_text:
                hours = int(re.search(r'(\d+)\s*小時前', time_text).group(1))
                dt = now - datetime.timedelta(hours=hours)
            elif '天前' in time_text:
                days = int(re.search(r'(\d+)\s*天前', time_text).group(1))
                dt = now - datetime.timedelta(days=days)
            elif '週前' in time_text or '周前' in time_text:
                weeks = int(re.search(r'(\d+)\s*[週周]前', time_text).group(1))
                dt = now - datetime.timedelta(weeks=weeks)
            elif '月前' in time_text:
                # 粗略計算，以30天為一個月
                months = int(re.search(r'(\d+)\s*月前', time_text).group(1))
                dt = now - datetime.timedelta(days=30*months)
            else:
                # 嘗試解析絕對時間（格式可能因地區而異）
                try:
                    # 處理年月日格式
                    match = re.search(r'(\d{4})[年/.-](\d{1,2})[月/.-](\d{1,2})[日號]?', time_text)
                    if match:
                        year, month, day = map(int, match.groups())
                        dt = datetime.datetime(year, month, day)
                    else:
                        # 默認為當前時間
                        dt = now
                except:
                    dt = now
            
            return dt.isoformat()
        except:
            # 無法解析時返回原始字符串
            return time_text
    
    def save_to_mongodb(self):
        """將結果保存到MongoDB
        
        Returns:
            保存成功的文檔數量
        """
        if not self.results:
            print("沒有數據可保存")
            return 0
            
        try:
            # 為每個結果添加唯一的時間戳標識符
            for news in self.results:
                news["搜索批次"] = datetime.datetime.now().isoformat()
                
            # 使用insert_many一次性插入所有記錄
            result = self.collection.insert_many(self.results)
            success_count = len(result.inserted_ids)
            
            print(f"成功保存到MongoDB: {success_count}條新數據")
            return success_count
            
        except Exception as e:
            print(f"保存到MongoDB時發生錯誤: {e}")
            import traceback
            traceback.print_exc()
            return 0
    
    def export_to_dataframe(self):
        """將結果轉換為DataFrame
        
        Returns:
            包含所有新聞的DataFrame
        """
        if not self.results:
            return pd.DataFrame()
        return pd.DataFrame(self.results)
    
    def export_to_csv(self, filename="news_data.csv"):
        """將結果導出為CSV文件
        
        Args:
            filename: 輸出文件名
        """
        if not self.results:
            print("沒有數據可保存")
            return
            
        try:
            # 創建DataFrame
            df = self.export_to_dataframe()
            
            # 使用 'utf-8-sig' 編碼 (帶BOM)，這在Excel中打開會更友好
            df.to_csv(filename, index=False, encoding='utf-8-sig', errors='replace')
            print(f"數據已導出至 {filename}")
        except Exception as e:
            print(f"導出CSV時發生錯誤: {e}")
            import traceback
            traceback.print_exc()
    
    def export_to_json(self, filename="news_data.json"):
        """將結果導出為JSON文件
        
        Args:
            filename: 輸出文件名
        """
        if not self.results:
            print("沒有數據可保存")
            return
            
        try:
            # 直接使用json模塊以避免編碼問題
            with open(filename, 'w', encoding='utf-8') as f:
                # 手動轉換不兼容的類型
                json_data = []
                for item in self.results:
                    clean_item = {}
                    for key, value in item.items():
                        if isinstance(value, datetime.datetime):
                            clean_item[key] = value.isoformat()
                        elif key == '_id' and hasattr(value, '__str__'):
                            # 將 ObjectId 轉換為字符串
                            clean_item[key] = str(value)
                        elif hasattr(value, 'to_json'):
                            # 處理可能有 to_json 方法的對象
                            clean_item[key] = value.to_json()
                        elif hasattr(value, '__str__') and not isinstance(value, (str, int, float, bool, list, dict, type(None))):
                            # 將其他自定義對象轉換為字符串
                            clean_item[key] = str(value)
                        else:
                            clean_item[key] = value
                    json_data.append(clean_item)
                
                # 使用自定義的 JSON 編碼器
                class CustomJSONEncoder(json.JSONEncoder):
                    def default(self, obj):
                        # 處理 ObjectId
                        if hasattr(obj, '__str__') and not isinstance(obj, (str, int, float, bool, list, dict, type(None))):
                            return str(obj)
                        return super().default(obj)
                
                json.dump(json_data, f, ensure_ascii=False, indent=4, cls=CustomJSONEncoder)
            
            print(f"數據已導出至 {filename}")
        except Exception as e:
            print(f"導出JSON時發生錯誤: {e}")
            import traceback
            traceback.print_exc()

async def main():
    # 設置MongoDB連接參數
    mongo_uri = input("請輸入MongoDB連接URI (留空使用默認localhost): ") or "mongodb://localhost:27017/"
    db_name = input("請輸入資料庫名稱 (留空使用默認news_database): ") or "news_database"
    
    # 是否顯示瀏覽器
    show_browser = input("是否顯示瀏覽器? (y/n, 默認n): ").lower() == 'y'
    
    # 創建爬蟲實例
    spider = NewsSpiderPlaywright(mongo_uri, db_name, headless=(not show_browser))
    
    try:
        # 初始化瀏覽器
        await spider.initialize_browser()
        
        # 獲取用戶輸入
        keyword = input("請輸入要搜索的新聞關鍵字: ")
        
        try:
            days = int(input("請輸入要搜索的天數 (預設10天): ") or 10)
        except ValueError:
            days = 10
            print("輸入無效，使用預設值10天")
        
        # 執行搜索
        max_pages = int(input("要搜索的最大頁數 (預設3頁): ") or 3)
        results = await spider.search_news(keyword, days, max_pages)
        
        # 顯示結果數量
        print(f"\n總共找到 {len(results)} 條相關新聞")
        
        # 保存到MongoDB
        if results:
            saved_count = spider.save_to_mongodb()
            print(f"已將 {saved_count} 條新聞存入MongoDB資料庫: {db_name}, 集合: news_articles")
            
            # 詢問是否還需要導出到CSV或JSON
            export_option = input("是否需要額外導出數據? (1: CSV, 2: JSON, 3: 兩者都要, 直接按Enter跳過): ")
            
            if export_option == "1" or export_option == "3":
                filename = input("請輸入CSV文件名 (預設: news_data.csv): ") or "news_data.csv"
                spider.export_to_csv(filename)
                
            if export_option == "2" or export_option == "3":
                filename = input("請輸入JSON文件名 (預設: news_data.json): ") or "news_data.json"
                spider.export_to_json(filename)
        
        # 顯示部分結果
        if results:
            print("\n部分搜索結果預覽:")
            for i, news in enumerate(results[:5], 1):
                print(f"\n新聞 {i}:")
                print(f"標題: {news['標題']}")
                print(f"出版社: {news['出版社']}")
                print(f"發布時間: {news['發布時間']}")
                print(f"網址: {news['網址']}")
                content_preview = news['內容'][:150] + "..." if len(news['內容']) > 150 else news['內容']
                print(f"內容預覽: {content_preview}")
    
    finally:
        # 確保關閉瀏覽器和MongoDB連接
        await spider.close()

# 運行主函數
if __name__ == "__main__":
    asyncio.run(main())