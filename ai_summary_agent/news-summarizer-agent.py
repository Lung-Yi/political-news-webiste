import json
import os
import argparse
from datetime import datetime
from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI
from langchain_anthropic import ChatAnthropic
from tqdm import tqdm
import logging

# 設定日誌
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("news_summarizer.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class NewsSummarizer:
    """針對新聞資料進行摘要整理的AI Agent，支援OpenAI和Claude模型"""
    
    def __init__(self, model_provider="openai", api_key=None):
        """初始化NewsSummarizer
        
        Args:
            model_provider: 語言模型提供者，可選 "openai" 或 "anthropic"
            api_key: API金鑰，若未提供，則從環境變數讀取
        """
        self.model_provider = model_provider.lower()
        
        # 設定語言模型
        if self.model_provider == "openai":
            # 如果未提供OpenAI API金鑰，嘗試從環境變數讀取
            if api_key is None:
                api_key = os.environ.get("OPENAI_API_KEY")
                if api_key is None:
                    raise ValueError("請提供OPENAI_API_KEY或設置環境變數")
            
            self.llm = ChatOpenAI(
                model="gpt-3.5-turbo",  # 可根據需求改為其他模型
                temperature=0.1,
                openai_api_key=api_key
            )
            logger.info("已初始化OpenAI模型")
            
        elif self.model_provider == "anthropic":
            # 如果未提供Anthropic API金鑰，嘗試從環境變數讀取
            if api_key is None:
                api_key = os.environ.get("ANTHROPIC_API_KEY")
                if api_key is None:
                    raise ValueError("請提供ANTHROPIC_API_KEY或設置環境變數")
            
            self.llm = ChatAnthropic(
                model="claude-3-7-sonnet-20250219",  # 可根據需求改為其他Claude模型
                temperature=0.1,
                anthropic_api_key=api_key
            )
            logger.info("已初始化Anthropic Claude模型")
            
        else:
            raise ValueError("不支援的模型提供者。請選擇 'openai' 或 'anthropic'")
        
        # 摘要提示模板
        self.summary_prompt = ChatPromptTemplate.from_template("""
        請為以下新聞內容撰寫一個簡潔但全面的列點式摘要，長度可依新聞長短彈性調整。
        摘要應涵蓋新聞的主要事實、核心觀點和重要細節。以及重要的事件時間還有相關數據必須保留。
        
        新聞標題: {title}
        發布時間: {date}
        出版社: {publisher}
        
        新聞內容:
        {content}
        
        摘要:
        """)
    
    def load_data(self, file_path):
        """從JSON文件載入新聞資料
        
        Args:
            file_path: JSON文件路徑
        
        Returns:
            data: 載入的新聞資料列表
        """
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            logger.info(f"成功載入 {len(data)} 篇新聞")
            return data
        except Exception as e:
            logger.error(f"載入資料時發生錯誤: {e}")
            return []
    
    def summarize_news(self, news_item):
        """生成單篇新聞的摘要
        
        Args:
            news_item: 包含新聞資訊的字典
        
        Returns:
            summary: 新聞摘要
        """
        # 如果新聞內容為空，嘗試返回原有的摘要
        if not news_item.get("內容"):
            logger.warning(f"新聞「{news_item.get('標題', '無標題')}」沒有內容，使用原有摘要")
            return news_item.get("摘要", "無內容可摘要")
        
        # 準備摘要
        try:
            # 使用語言模型生成摘要
            chain = self.summary_prompt | self.llm
            result = chain.invoke({
                "title": news_item.get("標題", ""),
                "date": news_item.get("發布時間", ""),
                "publisher": news_item.get("出版社", ""),
                "content": news_item.get("內容", "")
            })
            
            # 從回應中提取文本
            if self.model_provider == "openai":
                summary = result.content
            elif self.model_provider == "anthropic":
                summary = result.content
            
            return summary.strip()
            
        except Exception as e:
            logger.error(f"摘要生成錯誤: {e}")
            # 如果生成失敗，返回原有摘要或錯誤訊息
            return news_item.get("摘要", f"摘要生成失敗: {str(e)}")
    
    def process_batch(self, news_list, max_items=None):
        """批次處理新聞並生成摘要
        
        Args:
            news_list: 新聞列表
            max_items: 最大處理項目數，如果指定，只處理前N篇
        
        Returns:
            processed_news: 處理後的新聞列表，只包含標題、出版社、發布時間和摘要
        """
        # 如果指定了最大項目數，截取列表
        if max_items and max_items < len(news_list):
            news_list = news_list[:max_items]
            logger.info(f"將只處理前 {max_items} 篇新聞")
        
        processed_news = []
        total = len(news_list)
        
        # 使用tqdm顯示進度條
        for i, news in enumerate(tqdm(news_list, desc="處理新聞")):
            logger.info(f"正在處理第 {i+1}/{total} 篇新聞: {news.get('標題', '無標題')[:40]}...")
            
            # 生成摘要
            summary = self.summarize_news(news)
            
            # 僅保留所需的四個欄位
            processed_item = {
                "標題": news.get("標題", ""),
                "出版社": news.get("出版社", ""),
                "發布時間": news.get("發布時間", ""),
                "摘要": summary
            }
            
            processed_news.append(processed_item)
        
        logger.info(f"已完成 {len(processed_news)} 篇新聞的摘要處理")
        return processed_news
    
    def save_processed_data(self, processed_news, output_path):
        """保存處理後的資料
        
        Args:
            processed_news: 處理後的新聞列表
            output_path: 輸出文件路徑
        """
        try:
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(processed_news, f, ensure_ascii=False, indent=2)
            logger.info(f"已保存處理後的資料至: {output_path}")
        except Exception as e:
            logger.error(f"保存資料時發生錯誤: {e}")

def main():
    """主程序入口點"""
    # 設定命令行參數
    parser = argparse.ArgumentParser(description="新聞摘要生成工具")
    parser.add_argument("--input", "-i", required=True, help="輸入的JSON文件路徑")
    parser.add_argument("--output", "-o", default="summarized_news.json", help="輸出的JSON文件路徑")
    parser.add_argument("--model", "-m", choices=["openai", "anthropic"], default="anthropic", 
                        help="選擇語言模型提供者: openai 或 anthropic")
    parser.add_argument("--limit", "-l", type=int, help="限制處理的新聞篇數")
    parser.add_argument("--openai-key", help="OpenAI API金鑰")
    parser.add_argument("--anthropic-key", help="Anthropic API金鑰")
    
    args = parser.parse_args()
    
    # 根據選擇的模型提供者，設定API金鑰
    api_key = None
    if args.model == "openai":
        api_key = args.openai_key
    elif args.model == "anthropic":
        api_key = args.anthropic_key
    
    try:
        # 初始化摘要器
        logger.info(f"初始化新聞摘要器，使用: {args.model}")
        summarizer = NewsSummarizer(model_provider=args.model, api_key=api_key)
        
        # 載入資料
        logger.info(f"正在從 {args.input} 載入新聞資料...")
        news_data = summarizer.load_data(args.input)
        
        if not news_data:
            logger.error("沒有找到新聞資料，請確認檔案路徑正確。")
            return
        
        # 處理資料
        logger.info("開始處理新聞資料...")
        processed_news = summarizer.process_batch(news_data, args.limit)
        
        # 保存處理後的資料
        logger.info(f"正在保存摘要結果到 {args.output}...")
        summarizer.save_processed_data(processed_news, args.output)
        
        logger.info("處理完成!")
        
    except Exception as e:
        logger.error(f"執行過程中發生錯誤: {e}")

if __name__ == "__main__":
    main()
