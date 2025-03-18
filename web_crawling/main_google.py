import requests
from bs4 import BeautifulSoup
import datetime
import time
import random
from urllib.parse import quote
import pymongo
from pymongo import MongoClient
import pandas as pd
import re
from fake_useragent import UserAgent  # 添加此行以生成隨機User-Agent


class NewsSpider:
    def __init__(self, mongo_uri="mongodb://localhost:27017/", db_name="news_database"):
        # 創建隨機User-Agent生成器
        try:
            self.ua = UserAgent()
            self.headers = {
                'User-Agent': self.ua.random,
                'Accept-Language': 'zh-TW,zh;q=0.9,en-US;q=0.8,en;q=0.7',
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
                'Referer': 'https://www.google.com/',
                'DNT': '1',
                'Connection': 'keep-alive',
                'Upgrade-Insecure-Requests': '1',
            }
        except:
            # 備用User-Agent
            self.headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
                'Accept-Language': 'zh-TW,zh;q=0.9,en-US;q=0.8,en;q=0.7',
            }
        
        # 修改為Google搜索的基本URL
        self.base_url = "https://www.google.com/search"
        self.today = datetime.datetime.now()
        self.results = []
        
        # MongoDB連接設置
        self.client = MongoClient(mongo_uri)
        self.db = self.client[db_name]
        self.collection = self.db["news_articles"]
        
        # 確保索引存在（用於快速查詢和防止重複）
        self.collection.create_index([("網址", pymongo.ASCENDING)], unique=True)
        
    def search_news(self, keyword, days=10, max_pages=5):
        """搜索指定關鍵字的新聞，支持多頁抓取"""
        # 初始化結果列表
        self.results = []
        
        # 計算日期範圍
        ten_days_ago = self.today - datetime.timedelta(days=days)
        date_str = ten_days_ago.strftime('%Y-%m-%d')
        
        # 記錄訪問過的URL，避免重複
        visited_urls = set()
        
        # 用於獲取下一頁鏈接的變數
        next_page_url = None
        
        # 循環處理多頁
        for page in range(max_pages):
            try:
                # 第一頁和後續頁的URL構建方式不同
                if page == 0:
                    # 構建第一頁的URL參數
                    search_params = {
                                    'q': keyword,
                                    'tbm': 'nws',  # 新聞搜索
                                    'hl': 'zh-TW',
                                    'gl': 'tw',
                                    'tbs': f'qdr:d{days}',
                                    'ie': 'UTF-8',
                                    'lr': 'lang_zh-TW',  # 更明確指定語言
                                    'newwindow': '1',  # 新增參數
                                    'ijn': '0',  # 新增參數，表示第一頁
                                    'pz': '1',   # 新增參數，提高搜索質量
                                }
                    
                    # 構建查詢URL字符串
                    query_parts = []
                    for key, value in search_params.items():
                        query_parts.append(f"{key}={quote(value) if key == 'q' else value}")
                    
                    search_url = f"{self.base_url}?{'&'.join(query_parts)}"
                else:
                    # 使用從上一頁獲取的下一頁鏈接
                    if not next_page_url:
                        print(f"沒有找到下一頁鏈接，搜索結束於第 {page} 頁")
                        break
                    
                    search_url = next_page_url
                    
                    if search_url in visited_urls:
                        print(f"檢測到重複URL，搜索結束於第 {page} 頁")
                        break
                
                # 記錄當前URL
                visited_urls.add(search_url)
                
                print(f"\n正在搜索第 {page+1} 頁，關鍵字: {keyword}, 日期範圍: 最近{days}天")
                print(f"搜索URL: {search_url}")
                
                # 添加隨機延遲，遞增延遲時間以模擬人類行為
                delay_time = random.uniform(5 + page*2, 10 + page*3)
                print(f"等待 {delay_time:.2f} 秒...")
                time.sleep(delay_time)
                
                # 更新Headers，每頁使用不同的User-Agent
                try:
                    self.headers['User-Agent'] = self.ua.random if hasattr(self, 'ua') else \
                        f'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/{random.randint(90, 110)}.0.{random.randint(4000, 5000)}.{random.randint(10, 200)} Safari/537.36'
                except:
                    self.headers['User-Agent'] = f'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/{random.randint(90, 110)}.0.{random.randint(4000, 5000)}.{random.randint(10, 200)} Safari/537.36'
                
                # 添加更多隨機瀏覽器指紋
                self.headers['Accept-Language'] = 'zh-TW,zh;q=0.9,en-US;q=0.8,en;q=0.7'
                self.headers['Accept'] = 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8'
                self.headers['Referer'] = 'https://www.google.com/'
                self.headers['sec-ch-ua'] = f'"Chromium";v="{random.randint(100, 110)}", "Google Chrome";v="{random.randint(100, 110)}"'
                self.headers['sec-ch-ua-mobile'] = '?0'
                self.headers['sec-ch-ua-platform'] = '"Windows"'
                
                # 發送HTTP請求
                session = requests.Session()
                response = session.get(search_url, headers=self.headers, timeout=30)
                
                # 檢查是否成功
                if response.status_code != 200:
                    print(f"錯誤: 狀態碼 {response.status_code}")
                    # 保存頁面以便調試
                    with open(f"error_page_{page+1}.html", "w", encoding="utf-8") as f:
                        f.write(response.text)
                    break
                
                # 保存HTML以便調試
                debug_filename = f"google_search_page{page+1}.html"
                with open(debug_filename, "w", encoding="utf-8") as f:
                    f.write(response.text)
                print(f"已保存HTML到 {debug_filename} 用於調試")
                
                # 檢查是否有驗證碼或阻止
                if "unusual traffic" in response.text or "驗證" in response.text or "人機驗證" in response.text:
                    print(f"警告: 第 {page+1} 頁檢測到Google反爬蟲機制，請稍後再試")
                    break
                
                # 解析HTML
                soup = BeautifulSoup(response.text, 'html.parser')
                
                # 尋找下一頁鏈接
                next_page = soup.select_one('a#pnnext')
                if next_page and 'href' in next_page.attrs:
                    next_href = next_page['href']
                    if next_href.startswith('/'):
                        next_page_url = f"https://www.google.com{next_href}"
                    else:
                        next_page_url = next_href
                    print(f"找到下一頁鏈接: {next_page_url}")
                else:
                    print("沒有找到下一頁鏈接")
                    # 嘗試其他可能的下一頁選擇器
                    for selector in ['a[aria-label="下一頁"]', 'a:contains("下一頁")', 'a.nBDE1b']:
                        next_elem = None
                        if selector.startswith('a:contains'):
                            # 處理特殊的:contains選擇器
                            for a in soup.find_all('a'):
                                if "下一頁" in a.text:
                                    next_elem = a
                                    break
                        else:
                            next_elem = soup.select_one(selector)
                        
                        if next_elem and 'href' in next_elem.attrs:
                            next_href = next_elem['href']
                            if next_href.startswith('/'):
                                next_page_url = f"https://www.google.com{next_href}"
                            else:
                                next_page_url = next_href
                            print(f"使用備用選擇器找到下一頁鏈接: {next_page_url}")
                            break
                    
                    if not next_page_url:
                        next_page_url = None
                
                # 嘗試多種選擇器找新聞
                news_articles = []
                selectors = [
                            'div.SoaBEf, div.WlydOe, div.xuvV6b',
                            'div[data-hveid] div.A7IrWc',
                            'div.g, g-card, div.JheGif', 
                            'div.v7W49e div[data-hveid]',
                            'div.Gx5Zad, div.tF2Cxc',
                            'article',
                            'div.jtfYYd, div.y6IFtc, div.dbsr',
                            'div.MjjYud > div.cUnQKe',
                            'div.iRPxbe > div.mCBkyc',
                            'div.kCrYT',
                            'div.RlpDY',  
                            'div.UMOHqf',
                            'g-card.ftSUBd',
                            'div.lLyYWd',
                            'div.K7JcSb'
                        ]
                
                for selector in selectors:
                    articles = soup.select(selector)
                    if articles:
                        news_articles = articles
                        print(f"使用選擇器 '{selector}' 找到 {len(articles)} 條新聞")
                        break
                
                # 如果上面的選擇器都沒找到，嘗試更通用的方法
                if not news_articles:
                    # 尋找包含標題和鏈接的元素
                    all_headings = soup.find_all(['h3', 'h2'])
                    for heading in all_headings:
                        parent = heading.find_parent('div', class_=True)
                        if parent and parent not in news_articles:
                            news_articles.append(parent)
                    print(f"使用標題查找法找到 {len(news_articles)} 條新聞")
                
                # 如果還是沒找到，尋找所有可能的新聞容器
                if not news_articles:
                    # 找尋任何看起來像是新聞條目的div
                    potential_articles = soup.find_all('div', attrs={'data-hveid': True})
                    for div in potential_articles:
                        if (div.find('a') and div.find(['h3', 'h2', 'span'])) and div not in news_articles:
                            news_articles.append(div)
                    print(f"使用資料屬性查找法找到 {len(news_articles)} 條新聞")
                
                if not news_articles:
                    print(f"第 {page+1} 頁未找到新聞文章，可能已到達最後一頁或選擇器需要更新")
                    # 如果是第一頁就沒有結果，說明選擇器有問題
                    if page == 0:
                        print("警告：第一頁就沒有找到新聞，請檢查選擇器或HTML結構")
                    break
                
                # 解析當前頁的新聞
                print(f"正在解析第 {page+1} 頁的 {len(news_articles)} 條新聞...")
                for i, article in enumerate(news_articles):
                    print(f"  解析第 {i+1}/{len(news_articles)} 條新聞...")
                    self._parse_google_article(article, keyword)
                    # 每解析一篇文章後稍微停頓
                    time.sleep(random.uniform(1.5, 3))
                
                # 顯示當前進度
                total_found = len(self.results)
                print(f"目前共找到 {total_found} 條新聞")
                
            except Exception as e:
                print(f"搜索第 {page+1} 頁時發生錯誤: {e}")
                import traceback
                traceback.print_exc()
                break
        
        print(f"\n搜索完成，總共找到 {len(self.results)} 條新聞")
        return self.results
        
    def _parse_google_article(self, article, keyword):
        """解析Google搜索新聞文章元素"""
        try:
            # 顯示當前解析的文章HTML結構以便調試
            # print(f"正在解析文章: {article.prettify()[:300]}...(截斷)")
            
            # 提取標題 (嘗試多種可能的元素)
            title_elem = None
            for selector in ['h3 a', 'h3', 'a:has(h3)', 'a.RTNUJf', 'a[data-ved]', 'div.mCBkyc a', 'h2 a']:
                title_elem = article.select_one(selector)
                if title_elem:
                    break
            
            # 如果上面的選擇器都沒找到，嘗試直接查找
            if not title_elem:
                # 首先查找h3標籤
                h3_elems = article.find_all('h3')
                if h3_elems:
                    title_elem = h3_elems[0]
                else:
                    # 然後找a標籤
                    a_elems = article.find_all('a')
                    # 篩選出可能是標題的連結（通常文字較長）
                    long_text_links = [a for a in a_elems if a.text and len(a.text.strip()) > 20]
                    if long_text_links:
                        title_elem = long_text_links[0]
                        
            if not title_elem:
                print("警告：無法找到標題元素，跳過此文章")
                return
            
            # 提取標題文字
            title = title_elem.get_text().strip()
            if not title:
                print("警告：提取到空標題，跳過此文章")
                return
                
            print(f"找到標題: {title}")
            
            # 提取鏈接 (嘗試多種情況)
            link = ""
            if title_elem.name == 'a':
                link = title_elem.get('href', '')
            else:
                # 尋找標題內部或附近的連結
                link_elem = title_elem.find('a') or article.select_one('a')
                if link_elem:
                    link = link_elem.get('href', '')
            
            # 檢查並修正鏈接格式        
            if link.startswith('/url?'):
                # 提取實際URL
                try:
                    import urllib.parse as urlparse
                    parsed = urlparse.parse_qs(urlparse.urlparse(link).query)
                    if 'q' in parsed:
                        link = parsed['q'][0]
                    elif 'url' in parsed:
                        link = parsed['url'][0]
                except Exception as e:
                    print(f"解析URL失敗: {e}, 原始鏈接: {link}")
            
            # 確保鏈接是完整的URL
            if link and not link.startswith('http'):
                if link.startswith('/'):
                    link = f"https://www.google.com{link}"
                else:
                    print(f"警告：找到不完整的鏈接 '{link}'，跳過")
                    return
                    
            if not link:
                print(f"警告：未找到鏈接，跳過文章 '{title}'")
                return
                
            print(f"找到鏈接: {link}")
            
            # 提取新聞來源/出版社 (嘗試多種選擇器)
            publisher = "未知來源"
            publisher_selectors = [
                'div.UPmit', 'span.xQ82C', 'div.CEMjEf', 'div.csDOgf', 
                'div.lEXIrb span:first-child', 'div.NUnG9d', 'span.L8PZAb'
            ]
            
            for selector in publisher_selectors:
                publisher_elem = article.select_one(selector)
                if publisher_elem:
                    publisher = publisher_elem.get_text().strip()
                    break
                    
            if publisher == "未知來源":
                # 尋找任何看起來像發布商的元素
                for span in article.find_all(['span', 'div']):
                    text = span.get_text().strip()
                    # 出版社名稱通常較短且不包含特定符號
                    if text and 3 <= len(text) <= 30 and not any(c in text for c in ['/', '?', '#']):
                        publisher = text
                        break
            
            # 清理出版社字符串（移除時間信息等）
            publisher = re.sub(r'\s*[-–]\s*\d+.*$', '', publisher)
            publisher = re.sub(r'\s*\d+\s*(分鐘|小時|天|週).*$', '', publisher)
            
            print(f"找到來源: {publisher}")
            
            # 提取時間
            publish_time_text = ""
            time_selectors = [
                'span.WG9SHc', 'div.OSrXXb', 'span[aria-label]', 
                'div.s3v9rd', 'div.wqg8ad', 'span.ZE0LJd', 'span.qXLe6d'
            ]
            
            for selector in time_selectors:
                time_elem = article.select_one(selector)
                if time_elem:
                    publish_time_text = time_elem.get_text().strip()
                    break
            
            # 如果沒有找到明確的時間元素，嘗試從發布商資訊中提取
            if not publish_time_text:
                publisher_text = publisher
                # 尋找常見的時間格式，如 "來源 - 3天前"
                time_match = re.search(r'[-–]\s*(\d+\s*[分鐘小時天週月年]前)', publisher_text)
                if time_match:
                    publish_time_text = time_match.group(1)
                    # 清理發布商名稱
                    publisher = publisher_text.split(time_match.group(0))[0].strip()
            
            publish_time = self._parse_relative_time(publish_time_text) if publish_time_text else datetime.datetime.now().isoformat()
            print(f"找到時間: {publish_time}")
            
            # 獲取詳細內容之前先檢查是否是有效的URL
            if not link or len(link) < 10:
                print(f"無效的URL: {link}, 跳過獲取內容")
                content = "無法獲取詳細內容：無效URL"
            else:
                # 獲取詳細內容 (這部分可能會很耗時)
                try:
                    content = self._get_article_content(link)
                except Exception as e:
                    print(f"獲取內容失敗: {e}")
                    content = "獲取內容時出錯"
            
            # 擷取簡短摘要
            summary = ""
            summary_selectors = [
                'div.GI74Re', 'div.VwiC3b', 'div.Y3v8qd', 
                'div.s3v9rd', 'div.kb0PBd', 'div.LHPb5d'
            ]
            
            for selector in summary_selectors:
                summary_elem = article.select_one(selector)
                if summary_elem:
                    summary = summary_elem.get_text().strip()
                    break
            
            # 如果內容擷取失敗，至少使用摘要
            if (not content or content == "無法獲取詳細內容" or content == "獲取內容時出錯") and summary:
                content = summary
                print(f"使用摘要作為內容: {summary[:50]}...")
            
            # 構建新聞數據
            news_data = {
                "標題": title,
                "出版社": publisher,
                "發布時間": publish_time,
                "網址": link,
                "內容": content,
                "關鍵字": keyword,
                "抓取時間": datetime.datetime.now().isoformat()
            }
            
            # 檢查是否已有相同標題的新聞（避免重複）
            for existing in self.results:
                if existing["標題"] == title and existing["出版社"] == publisher:
                    print(f"跳過重複新聞: {title}")
                    return
                    
            self.results.append(news_data)
            print(f"已解析: {title[:30]}... | {publisher} | {publish_time}")
            
        except Exception as e:
            print(f"解析文章時發生錯誤: {e}")
            import traceback
            traceback.print_exc()  # 打印完整的錯誤堆疊
    
    def _parse_relative_time(self, time_text):
        """解析相對時間字符串為ISO格式日期時間"""
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
    
    def _get_article_content(self, url):
        """獲取新聞詳細內容，增強編碼處理和選擇器"""
        try:
            if not url:
                return "URL不可用"
                
            # 更新User-Agent
            if hasattr(self, 'ua'):
                self.headers['User-Agent'] = self.ua.random
                
            print(f"正在獲取文章內容: {url}")
            
            # 添加隨機延遲
            time.sleep(random.uniform(2, 4))
            
            # 增加超時和編碼處理
            response = requests.get(url, headers=self.headers, timeout=15)
            
            # 先檢查狀態碼
            if response.status_code != 200:
                return f"請求失敗，狀態碼: {response.status_code}"
                
            # 檢測並修正編碼問題
            if response.encoding.lower() == 'iso-8859-1':
                # 嘗試從內容檢測正確的編碼
                detected_encoding = response.apparent_encoding
                
                # 如果檢測到的編碼看起來合理，使用它
                if detected_encoding and detected_encoding.lower() != 'iso-8859-1':
                    response.encoding = detected_encoding
                else:
                    # 對於中文網站，嘗試常見的中文編碼
                    for encoding in ['utf-8', 'big5', 'gbk', 'gb2312', 'gb18030']:
                        try:
                            response.content.decode(encoding)
                            response.encoding = encoding
                            break
                        except UnicodeDecodeError:
                            continue
            
            # 獲取HTML文本，處理可能的編碼錯誤
            try:
                html_text = response.text
            except UnicodeDecodeError:
                # 如果普通解碼失敗，嘗試更寬容的解碼
                html_text = response.content.decode(response.encoding or 'utf-8', errors='replace')
            
            soup = BeautifulSoup(html_text, 'html.parser')
            
            # 移除不必要的元素
            for tag in soup(['script', 'style', 'iframe', 'aside', 'nav', 'footer', 'header']):
                tag.decompose()
            
            # 嘗試多種常見的新聞內容選擇器
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
                    # 獲取所有文本
                    paragraphs = content_elem.find_all('p')
                    if paragraphs:
                        content = '\n'.join([p.get_text().strip() for p in paragraphs])
                        break
            
            if not content:
                # 如果無法提取內容，嘗試獲取網頁中的所有段落
                paragraphs = soup.find_all('p')
                if paragraphs:
                    filtered_paragraphs = [p.get_text().strip() for p in paragraphs 
                                        if len(p.get_text().strip()) > 50 
                                        and not re.search(r'cookie|©|版權|關注我們|訂閱電子報|下載APP', p.get_text(), re.IGNORECASE)]
                    if filtered_paragraphs:
                        content = '\n'.join(filtered_paragraphs)
                    else:
                        content = "無法提取內容"
                else:
                    content = "無法提取內容"
            
            # 最終的清理步驟，移除任何可能的無效字符
            try:
                content = content.encode('utf-8', errors='replace').decode('utf-8')
            except Exception as e:
                # 如果仍然有問題，進行更激進的清理
                print(f"編碼清理時發生錯誤: {e}")
                clean_content = ""
                for char in content:
                    try:
                        char.encode('utf-8')
                        clean_content += char
                    except:
                        clean_content += " "
                content = clean_content
            
            return content
                
        except Exception as e:
            print(f"獲取內容時發生錯誤: {str(e)}")
            return f"獲取內容時發生錯誤: {str(e)}"
    
    def try_news_rss(self, keyword, days=10):
        """使用Google News RSS Feed作為備用方法"""
        rss_url = f"https://news.google.com/rss/search?q={quote(keyword)}&hl=zh-TW&gl=TW&ceid=TW:zh-Hant"
        try:
            response = requests.get(rss_url, headers=self.headers)
            if response.status_code == 200:
                soup = BeautifulSoup(response.text, 'xml')
                items = soup.find_all('item')
                
                results = []
                for item in items:
                    title = item.title.text if item.title else "未知標題"
                    link = item.link.text if item.link else ""
                    pubdate = item.pubDate.text if item.pubDate else ""
                    description = item.description.text if item.description else ""
                    source = item.source.text if hasattr(item, 'source') and item.source else "Google News"
                    
                    # 只保留規定天數內的新聞
                    try:
                        pub_datetime = datetime.datetime.strptime(pubdate, "%a, %d %b %Y %H:%M:%S %Z")
                        if (datetime.datetime.now() - pub_datetime).days > days:
                            continue
                    except:
                        pass  # 如果無法解析日期，保留該條目
                    
                    news_data = {
                        "標題": title,
                        "出版社": source,
                        "發布時間": pubdate,
                        "網址": link,
                        "內容": description,
                        "關鍵字": keyword,
                        "抓取時間": datetime.datetime.now().isoformat()
                    }
                    results.append(news_data)
                    
                print(f"從RSS Feed找到 {len(results)} 條新聞")
                return results
        except Exception as e:
            print(f"嘗試RSS Feed失敗: {e}")
        return []

    def save_to_mongodb(self):
        """將結果保存到MongoDB"""
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
            return 0
    
    def export_to_dataframe(self):
        """將結果轉換為DataFrame"""
        if not self.results:
            return pd.DataFrame()
        return pd.DataFrame(self.results)
    
    def close_connection(self):
        """關閉MongoDB連接"""
        if self.client:
            self.client.close()
            print("MongoDB連接已關閉")


def main():
    # 設置MongoDB連接參數
    mongo_uri = input("請輸入MongoDB連接URI (留空使用默認localhost): ") or "mongodb://localhost:27017/"
    db_name = input("請輸入資料庫名稱 (留空使用默認news_database): ") or "news_database"
    
    # 創建爬蟲實例
    spider = NewsSpider(mongo_uri, db_name)
    
    try:
        # 獲取用戶輸入
        keyword = input("請輸入要搜索的新聞關鍵字: ")
        
        try:
            days = int(input("請輸入要搜索的天數 (預設10天): ") or 10)
        except ValueError:
            days = 10
            print("輸入無效，使用預設值10天")
        
        # 執行搜索
        max_pages = int(input("要搜索的最大頁數 (預設3頁): ") or 3)
        results = spider.search_news(keyword, days, max_pages)
        
        # 顯示結果數量
        print(f"\n總共找到 {len(results)} 條相關新聞")
        if not results or len(results) == 0:
            print("常規搜索未找到結果，嘗試使用RSS方法...")
            results = spider.try_news_rss(keyword, days)
        
        # 保存到MongoDB
        if results:
            saved_count = spider.save_to_mongodb()
            print(f"已將 {saved_count} 條新聞存入MongoDB資料庫: {db_name}, 集合: news_articles")
            
            # 詢問是否還需要導出到CSV或JSON
            export_option = input("是否需要額外導出數據? (1: CSV, 2: JSON, 直接按Enter跳過): ")
            
            if export_option == "1":
                filename = input("請輸入CSV文件名 (預設: news_data.csv): ") or "news_data.csv"
                df = spider.export_to_dataframe()
                df.to_csv(filename, index=False, encoding='utf-8-sig')
                print(f"數據已導出至 {filename}")
                
            elif export_option == "2":
                filename = input("請輸入JSON文件名 (預設: news_data.json): ") or "news_data.json"
                df = spider.export_to_dataframe()
                df.to_json(filename, force_ascii=False, orient='records', indent=4)
                print(f"數據已導出至 {filename}")
        
        # 顯示部分結果
        if results:
            print("\n部分搜索結果預覽:")
            for i, news in enumerate(results[:5], 1):
                print(f"\n新聞 {i}:")
                print(f"標題: {news['標題']}")
                print(f"出版社: {news['出版社']}")
                print(f"發布時間: {news['發布時間']}")
                print(f"網址: {news['網址']}")
                print(f"內容預覽: {news['內容'][:150]}..." if len(news['內容']) > 150 else news['內容'])
        

    
    finally:
        # 確保關閉MongoDB連接
        spider.close_connection()


if __name__ == "__main__":
    main()