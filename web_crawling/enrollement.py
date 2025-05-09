from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
import pandas as pd
from bs4 import BeautifulSoup
from io import StringIO
import time
import os

def scrape_webpage(url, output_folder="scraped_data"):
    # 創建輸出文件夾
    if not os.path.exists(output_folder):
        os.makedirs(output_folder)
    
    # 設置Chrome選項
    chrome_options = Options()
    chrome_options.add_argument("--headless")  # 無頭模式
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")

    # 初始化WebDriver
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=chrome_options)

    try:
        # 訪問URL
        print(f"正在訪問 {url}...")
        driver.get(url)
        
        # 等待頁面加載 (視情況調整)
        time.sleep(5)
        
        # 獲取頁面內容
        html_content = driver.page_source
        
        # 使用BeautifulSoup解析HTML以抓取文本
        soup = BeautifulSoup(html_content, 'html.parser')
        
        # 1. 抓取表格數據
        try:
            tables = pd.read_html(StringIO(html_content))
            for i, table in enumerate(tables):
                csv_path = os.path.join(output_folder, f'table_{i+1}.csv')
                table.to_csv(csv_path, index=False)
                print(f"已保存表格 {i+1}/{len(tables)} 至 {csv_path}")
        except Exception as e:
            print(f"抓取表格時發生錯誤: {e}")
            tables = []
        
        # 2. 抓取標題
        title = soup.title.string if soup.title else "無標題"
        with open(os.path.join(output_folder, "title.txt"), "w", encoding="utf-8") as f:
            f.write(title)
        print(f"已保存標題至 {os.path.join(output_folder, 'title.txt')}")
        
        # 3. 抓取主要文本內容
        # 定義可能包含主要內容的元素
        main_elements = [
            soup.find('article'),
            soup.find('main'),
            soup.find('div', {'class': 'content'}),
            soup.find('div', {'class': 'article'}),
            soup.find('div', {'id': 'content'}),
            soup.find('div', {'id': 'article'})
        ]
        
        # 選擇第一個非None的元素作為主要內容區
        main_content = None
        for element in main_elements:
            if element:
                main_content = element
                break
        
        # 如果找不到特定區域，使用整個body
        if not main_content:
            main_content = soup.body
        
        # 抓取所有段落、標題和列表項
        text_elements = main_content.find_all(['p', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'li'])
        
        # 提取文本
        extracted_text = []
        for element in text_elements:
            text = element.get_text().strip()
            if text:  # 只保留非空文本
                tag_name = element.name
                
                # 根據HTML標籤添加適當的格式
                if tag_name.startswith('h'):
                    heading_level = int(tag_name[1])
                    extracted_text.append(f"\n{'#' * heading_level} {text}\n")
                elif tag_name == 'li':
                    extracted_text.append(f"- {text}")
                else:
                    extracted_text.append(text)
        
        # 將所有文本寫入文件
        with open(os.path.join(output_folder, "content.txt"), "w", encoding="utf-8") as f:
            f.write("\n\n".join(extracted_text))
        print(f"已保存文本內容至 {os.path.join(output_folder, 'content.txt')}")
        
        # 4. 抓取所有鏈接
        links = soup.find_all('a', href=True)
        link_data = []
        
        for link in links:
            link_text = link.get_text().strip()
            link_href = link['href']
            
            # 處理相對URL
            if link_href.startswith('/'):
                # 從當前URL構建完整URL
                base_url = '/'.join(url.split('/')[:3])  # 提取 http(s)://domain.com
                link_href = f"{base_url}{link_href}"
            
            if link_text and link_href:  # 只保留有文本和href的鏈接
                link_data.append(f"{link_text} - {link_href}")
        
        # 保存鏈接
        with open(os.path.join(output_folder, "links.txt"), "w", encoding="utf-8") as f:
            f.write("\n".join(link_data))
        print(f"已保存鏈接至 {os.path.join(output_folder, 'links.txt')}")
        
        return {
            "tables_count": len(tables),
            "text_elements_count": len(text_elements),
            "links_count": len(links),
            "output_folder": output_folder
        }
        
    except Exception as e:
        print(f"發生錯誤: {e}")
        return None
        
    finally:
        # 關閉瀏覽器
        driver.quit()

# 如果作為主程序運行
if __name__ == "__main__":
    url = input("請輸入要抓取的網頁URL: ")
    output_folder = input("請輸入保存數據的文件夾名稱 (默認為'scraped_data'): ")
    
    if not output_folder:
        output_folder = "scraped_data"
    
    result = scrape_webpage(url, output_folder)
    
    if result:
        print("\n抓取完成!")
        print(f"抓取了 {result['tables_count']} 個表格")
        print(f"抓取了 {result['text_elements_count']} 個文本元素")
        print(f"抓取了 {result['links_count']} 個鏈接")
        print(f"所有數據已保存到 '{result['output_folder']}' 文件夾")
    else:
        print("抓取失敗。")