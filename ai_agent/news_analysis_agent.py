import json
import os
import logging
import time
from typing import List, Dict, Any, Optional
from datetime import datetime

# Langchain 核心導入
from langchain.schema import HumanMessage, SystemMessage
from langchain.chains import LLMChain
from langchain.prompts import ChatPromptTemplate, HumanMessagePromptTemplate, SystemMessagePromptTemplate
from langchain.output_parsers import PydanticOutputParser, OutputFixingParser
from langchain.tools import BaseTool
from langchain.agents import initialize_agent, AgentType
from langchain.memory import ConversationBufferMemory
from pydantic import BaseModel, Field
from typing import List, Optional
from prompt_library.prompts import analysis_system_template, analysis_human_template, \
    visualization_system_template, visualization_human_template, \
    report_system_template, report_human_template
from prompt_library.utils import read_html_template
# 創建logs目錄（如果不存在）
log_dir = "logs"
if not os.path.exists(log_dir):
    os.makedirs(log_dir)

# 生成日誌文件名（包含時間戳）
log_filename = os.path.join(log_dir, f"news_analysis_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log")

# 設定日誌
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        # 輸出到控制台
        logging.StreamHandler(),
        # 輸出到文件
        logging.FileHandler(log_filename, encoding='utf-8')
    ]
)
logger = logging.getLogger(__name__)

# Pydantic 模型定義
class AnalysisResult(BaseModel):
    """分析結果的 Pydantic 模型"""
    main_topic: str = Field(description="新聞的主要主題")
    key_points: List[str] = Field(description="關鍵數據點或趨勢")
    required_tools: List[str] = Field(description="需要使用的分析工具列表")
    rationale: Dict[str, str] = Field(description="選擇這些工具的理由，工具名為 key，理由為 value")

class Visualization(BaseModel):
    """可視化圖表的 Pydantic 模型"""
    tool: str = Field(description="使用的分析工具名稱")
    html: str = Field(description="生成的 HTML 代碼")
    
class NewsAnalysisAgent:
    def __init__(self, 
                 api_key: Optional[str] = None, 
                 model_name: str = "claude-3-7-sonnet-20250219",
                 temperature: float = 0.3,
                 templates_dir: str = "../website/templates"):
        """
        初始化新聞分析 Agent
        
        Args:
            api_key: LLM API 金鑰，如果是 None 則從環境變量獲取
            model_name: 要使用的模型名稱
            temperature: 模型溫度
            templates_dir: HTML 模板所在目錄
        """
        # 導入 Anthropic 相關模組
        from langchain_anthropic import ChatAnthropic
        
        self.api_key = api_key or os.environ.get("ANTHROPIC_API_KEY")
        if not self.api_key:
            raise ValueError("API 金鑰未提供，請通過參數或環境變量 ANTHROPIC_API_KEY 設置")
            
        self.templates_dir = templates_dir
        self.temperature = temperature
        self.model_name = model_name
        
        # 初始化 Claude LLM
        self.visualization_llm = ChatAnthropic(
            model=model_name,
            temperature=temperature,
            anthropic_api_key=self.api_key,
            max_tokens=4000  # 設置適合 Claude 的 output token 限制
        )
        self.report_llm = ChatAnthropic(
            model=model_name,
            temperature=temperature,
            anthropic_api_key=self.api_key,
            max_tokens=40000  # 設置適合 Claude 的 output token 限制
        )  
        # 可用的分析工具列表
        self.analysis_tools = [
            "時間變化趨勢圖",
            "數值分類排序",
            "台灣地理環境區域分布圖",
            "重大時間線軸圖",
            "比例圓餅圖",
            "財務報表分析",
            "新聞媒體立場分析比較表",
            "爭議立場比較分析表"
        ]
        
        # 檢查模板目錄是否存在
        if not os.path.exists(templates_dir):
            os.makedirs(templates_dir)
            logger.warning(f"模板目錄 {templates_dir} 不存在，已自動創建")
            
        # 初始化輸出解析器
        self.analysis_parser = PydanticOutputParser(pydantic_object=AnalysisResult)
        
        # 創建更可靠的解析器（自動修復輸出）
        self.analysis_fixing_parser = OutputFixingParser.from_llm(
            parser=self.analysis_parser,
            llm=ChatAnthropic(
                model=model_name,
                temperature=0.0,
                anthropic_api_key=self.api_key,
                max_tokens=1000
            )
        )
        
        # 初始化工具鏈
        self._initialize_chains()
    
    def _initialize_chains(self):
        """初始化 Langchain 鏈"""
        # 分析新聞數據的鏈        
        analysis_prompt = ChatPromptTemplate(
            messages=[
                SystemMessagePromptTemplate.from_template(analysis_system_template),
                HumanMessagePromptTemplate.from_template(analysis_human_template)
            ],
            input_variables=["tools", "news_data"],
            partial_variables={"format_instructions": self.analysis_parser.get_format_instructions()}
        )
        
        self.analysis_chain = LLMChain(
            llm=self.visualization_llm,
            prompt=analysis_prompt,
            output_key="analysis_result",
            verbose=True
        )
        
        # 可視化生成鏈（這個將在運行時針對特定工具創建）       
        self.visualization_prompt = ChatPromptTemplate(
            messages=[
                SystemMessagePromptTemplate.from_template(visualization_system_template),
                HumanMessagePromptTemplate.from_template(visualization_human_template)
            ],
            input_variables=["tool", "news_data", "template"]
        )
        
        # 最終報告生成鏈
        self.report_prompt = ChatPromptTemplate(
            messages=[
                SystemMessagePromptTemplate.from_template(report_system_template),
                HumanMessagePromptTemplate.from_template(report_human_template)
            ],
            input_variables=["news_data", "analysis_summary", "visualizations", "report_template"]
        )
        
        self.report_chain = LLMChain(
            llm=self.report_llm,
            prompt=self.report_prompt,
            verbose=True
        )
    
    def analyze_news_data(self, news_data: List[Dict[str, Any]]) -> AnalysisResult:
        """
        第一步：分析新聞資料並確定需要使用哪些分析工具
        
        Args:
            news_data: 爬蟲獲取的新聞資料列表
            
        Returns:
            分析結果物件
        """
        tools_str = "\n".join([f"{i+1}. {tool}" for i, tool in enumerate(self.analysis_tools)])
        
        try:
            # 執行分析鏈
            result = self.analysis_chain.run(
                tools=tools_str,
                news_data=json.dumps(news_data, ensure_ascii=False, indent=2)
            )
            
            # 解析和修復輸出
            parsed_result = self.analysis_fixing_parser.parse(result)
            logger.info(f"新聞分析完成，需要使用工具: {parsed_result.required_tools}")
            
            return parsed_result
            
        except Exception as e:
            logger.error(f"分析新聞數據時出錯: {str(e)}")
            # 回傳一個預設的分析結果
            return AnalysisResult(
                main_topic="無法確定",
                key_points=["分析過程中出現錯誤"],
                required_tools=[],
                rationale={}
            )
    
    def generate_visualizations(self, 
                              news_data: List[Dict[str, Any]], 
                              required_tools: List[str]) -> List[Visualization]:
        """
        第二步：根據分析結果為每種所需工具生成可視化圖表
        
        Args:
            news_data: 爬蟲獲取的新聞資料列表
            required_tools: 需要使用的分析工具列表
            
        Returns:
            生成的可視化圖表列表
        """
        visualizations = []
        
        for tool in required_tools:
            try:
                # 讀取對應的 HTML 模板
                template_path = os.path.join(self.templates_dir, f"{tool}_template.html")
                if not os.path.exists(template_path):
                    logger.warning(f"模板文件 {template_path} 不存在，將使用默認模板")
                    template = self._get_default_template(tool)
                else:
                    with open(template_path, "r", encoding="utf-8") as f:
                        template = f.read()
                
                # 創建針對特定工具的視覺化生成鏈
                visualization_chain = LLMChain(
                    llm=self.visualization_llm,
                    prompt=self.visualization_prompt
                )
                
                # 生成可視化
                visualization_html = visualization_chain.run(
                    tool=tool,
                    news_data=json.dumps(news_data, ensure_ascii=False, indent=2),
                    template=template
                )
                
                visualizations.append(Visualization(
                    tool=tool,
                    html=visualization_html
                ))
                
                logger.info(f"已為 {tool} 生成可視化圖表")
                
                # 避免 API 請求過於頻繁
                time.sleep(1)
                
            except Exception as e:
                logger.error(f"為工具 {tool} 生成可視化時出錯: {str(e)}")
        
        return visualizations
    
    def create_final_report(self, 
                           news_data: List[Dict[str, Any]], 
                           analysis_result: AnalysisResult,
                           visualizations: List[Visualization]) -> str:
        """
        第三步：整合所有可視化並生成最終的分析報告
        
        Args:
            news_data: 爬蟲獲取的新聞資料
            analysis_result: 分析結果
            visualizations: 生成的可視化圖表列表
            
        Returns:
            完整的 HTML 報告
        """
        # 讀取報告模板
        report_template_path = os.path.join(self.templates_dir, "report_template.html")
        if not os.path.exists(report_template_path):
            logger.warning(f"報告模板 {report_template_path} 不存在，將使用默認報告模板")
            report_template = self._get_default_report_template()
        else:
            with open(report_template_path, "r", encoding="utf-8") as f:
                report_template = f.read()
        
        # 視覺化 HTML 代碼的準備
        visualizations_str = "\n\n".join([
            f"--- {vis.tool} 視覺化代碼 ---\n{vis.html}" 
            for vis in visualizations
        ])
        
        # 執行報告生成鏈
        try:
            final_report = self.report_chain.run(
                news_data=json.dumps(news_data, ensure_ascii=False, indent=2),
                analysis_summary=json.dumps(analysis_result.dict(), ensure_ascii=False, indent=2),
                visualizations=visualizations_str,
                report_template=report_template
            )
            
            logger.info("最終報告生成完成")
            return final_report
            
        except Exception as e:
            logger.error(f"生成最終報告時出錯: {str(e)}")
            # 返回一個簡單的錯誤報告
            return f"""<!DOCTYPE html>
<html>
<head><title>報告生成錯誤</title></head>
<body>
    <h1>報告生成過程中出現錯誤</h1>
    <p>錯誤信息: {str(e)}</p>
    <p>時間: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
</body>
</html>"""
    
    def save_report(self, report: str, output_path: str = "report.html") -> None:
        """
        保存生成的報告到文件
        
        Args:
            report: 完整的 HTML 報告
            output_path: 輸出文件路徑
        """
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(report)
        
        logger.info(f"報告已保存到 {output_path}")
    
    def run_full_analysis(self, news_data: List[Dict[str, Any]], output_path: str = "report.html") -> str:
        """
        執行完整的分析流程
        
        Args:
            news_data: 爬蟲獲取的新聞資料
            output_path: 輸出報告的文件路徑
            
        Returns:
            生成的 HTML 報告
        """
        logger.info("1. 開始分析新聞資料...")
        analysis_result = self.analyze_news_data(news_data)
        
        logger.info(f"2. 生成可視化圖表 (需要工具: {', '.join(analysis_result.required_tools)})...")
        visualizations = self.generate_visualizations(news_data, analysis_result.required_tools)
        
        logger.info("3. 創建最終報告...")
        final_report = self.create_final_report(news_data, analysis_result, visualizations)
        
        self.save_report(final_report, output_path)
        
        return final_report
    
    def _get_default_template(self, tool: str) -> str:
        """
        獲取默認的工具模板
        """
        # 這裡為各種工具提供默認模板
        templates = {
            "時間變化趨勢圖": read_html_template(os.path.join(self.templates_dir, "time_trend.html")),
            "比例圓餅圖": read_html_template(os.path.join(self.templates_dir, "pie_chart.html")),
            
        }
        
        # 為其他工具添加默認模板
        
        return templates.get(tool, """<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>可視化圖表</title>
    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
</head>
<body>
    <div style="width: 80%; margin: 0 auto;">
        <canvas id="chart"></canvas>
    </div>
    
    <script>
        // 在這裡添加 Chart.js 代碼
        const ctx = document.getElementById('chart').getContext('2d');
        const chart = new Chart(ctx, {
            type: 'bar',
            data: {
                labels: ['項目1', '項目2', '項目3'],
                datasets: [{
                    label: '數據',
                    data: [12, 19, 3],
                    backgroundColor: 'rgba(54, 162, 235, 0.2)',
                    borderColor: 'rgb(54, 162, 235)',
                    borderWidth: 1
                }]
            },
            options: {
                responsive: true,
                plugins: {
                    title: {
                        display: true,
                        text: '數據可視化'
                    }
                }
            }
        });
    </script>
</body>
</html>""")
    
    def _get_default_report_template(self) -> str:
        """
        獲取默認的報告模板
        """
        return """<!DOCTYPE html>
<html lang="zh-TW">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>新聞分析報告</title>
    <style>
        body {
            font-family: 'Microsoft JhengHei', 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            line-height: 1.6;
            color: #333;
            max-width: 1200px;
            margin: 0 auto;
            padding: 20px;
        }
        header {
            text-align: center;
            margin-bottom: 40px;
        }
        h1 {
            color: #1a5276;
            margin-bottom: 10px;
        }
        .date {
            color: #7f8c8d;
            font-size: 0.9em;
        }
        .summary {
            background-color: #f9f9f9;
            padding: 20px;
            border-left: 4px solid #3498db;
            margin-bottom: 30px;
        }
        .visualization-container {
            margin: 40px 0;
            padding: 20px;
            background-color: #fff;
            box-shadow: 0 0 10px rgba(0, 0, 0, 0.1);
        }
        .visualization-title {
            color: #2c3e50;
            border-bottom: 2px solid #ecf0f1;
            padding-bottom: 10px;
            margin-bottom: 20px;
        }
        .analysis-section {
            margin: 30px 0;
        }
        .conclusion {
            background-color: #f2f4f4;
            padding: 20px;
            border-radius: 5px;
            margin-top: 40px;
        }
        footer {
            margin-top: 50px;
            text-align: center;
            color: #7f8c8d;
            font-size: 0.9em;
            border-top: 1px solid #ecf0f1;
            padding-top: 20px;
        }
    </style>
    <!-- 添加任何你需要的 JavaScript 庫 -->
    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
</head>
<body>
    <header>
        <h1>新聞分析報告</h1>
        <div class="date">生成日期：<span id="current-date"></span></div>
    </header>
    
    <section class="summary">
        <h2>摘要</h2>
        <p>
            <!-- 這裡將插入新聞分析摘要 -->
        </p>
    </section>
    
    <section class="analysis-section">
        <h2>主要發現</h2>
        <!-- 這裡將插入主要發現的內容 -->
    </section>
    
    <!-- 可視化圖表將插入到這裡 -->
    
    <section class="conclusion">
        <h2>結論與展望</h2>
        <!-- 這裡將插入結論和展望 -->
    </section>
    
    <footer>
        <p>本報告由 AI 新聞分析系統自動生成，僅供參考。</p>
    </footer>
    
    <script>
        // 設置當前日期
        document.getElementById('current-date').textContent = new Date().toLocaleDateString('zh-TW');
    </script>
</body>
</html>"""


# ----- 工具類定義 -----

class NewsAnalysisTool(BaseTool):
    """用於新聞分析的 Langchain 工具"""
    name: str = "news_analysis_tool"  # 添加類型註解
    description: str = "分析新聞數據並確定需要使用哪些分析工具"  # 添加類型註解
    
    def __init__(self, agent: NewsAnalysisAgent):
        """初始化工具"""
        super().__init__()
        self.agent = agent
    
    def _run(self, news_data_json: str) -> str:
        """運行工具"""
        try:
            news_data = json.loads(news_data_json)
            result = self.agent.analyze_news_data(news_data)
            return json.dumps(result.dict(), ensure_ascii=False, indent=2)
        except Exception as e:
            return f"分析新聞時出錯: {str(e)}"
    
    def _arun(self, news_data_json: str):
        """異步運行工具"""
        raise NotImplementedError("NewsAnalysisTool 不支持異步操作")


class VisualizationTool(BaseTool):
    """用於生成可視化的 Langchain 工具"""
    name: str = "visualization_tool"  # 添加類型註解
    description: str = "為指定的分析工具和新聞數據生成可視化圖表"  # 添加類型註解
    
    def __init__(self, agent: NewsAnalysisAgent):
        """初始化工具"""
        super().__init__()
        self.agent = agent
    
    def _run(self, input_str: str) -> str:
        """運行工具"""
        try:
            input_data = json.loads(input_str)
            news_data = input_data.get("news_data", [])
            tools = input_data.get("tools", [])
            
            visualizations = self.agent.generate_visualizations(news_data, tools)
            return json.dumps([v.dict() for v in visualizations], ensure_ascii=False, indent=2)
        except Exception as e:
            return f"生成可視化時出錯: {str(e)}"
    
    def _arun(self, input_str: str):
        """異步運行工具"""
        raise NotImplementedError("VisualizationTool 不支持異步操作")


class ReportGenerationTool(BaseTool):
    """用於生成最終報告的 Langchain 工具"""
    name: str = "report_generation_tool"  # 添加類型註解
    description: str = "整合分析結果和可視化圖表，生成最終的新聞分析報告"  # 添加類型註解
    
    def __init__(self, agent: NewsAnalysisAgent):
        """初始化工具"""
        super().__init__()
        self.agent = agent
    
    def _run(self, input_str: str) -> str:
        """運行工具"""
        try:
            input_data = json.loads(input_str)
            news_data = input_data.get("news_data", [])
            analysis_result_dict = input_data.get("analysis_result", {})
            visualizations_dict = input_data.get("visualizations", [])
            
            # 轉換為 Pydantic 模型
            analysis_result = AnalysisResult(**analysis_result_dict)
            visualizations = [Visualization(**v) for v in visualizations_dict]
            
            final_report = self.agent.create_final_report(news_data, analysis_result, visualizations)
            
            # 保存報告（如果指定了輸出路徑）
            output_path = input_data.get("output_path")
            if output_path:
                self.agent.save_report(final_report, output_path)
            
            return "報告生成成功。" + (f"已保存到 {output_path}" if output_path else "")
        except Exception as e:
            return f"生成報告時出錯: {str(e)}"
    
    def _arun(self, input_str: str):
        """異步運行工具"""
        raise NotImplementedError("ReportGenerationTool 不支持異步操作")

# ----- 主函數 -----

def create_news_analysis_agent(api_key: Optional[str] = None, 
                             model_name: str = "claude-3-7-sonnet-20250219",  # 預設使用 Claude 模型
                             temperature: float = 0.2,
                             templates_dir: str = "templates") -> Any:
    """
    創建一個基於 Langchain 的新聞分析 Agent，使用 Anthropic Claude 模型
    
    Args:
        api_key: Anthropic API 金鑰
        model_name: Claude 模型名稱 (如 'claude-3-opus-20240229', 'claude-3-sonnet-20240229')
        temperature: 模型溫度
        templates_dir: 模板目錄
        
    Returns:
        初始化好的 Langchain Agent
    """
    # 導入 Anthropic 相關模組
    from langchain_anthropic import ChatAnthropic
    
    # 檢查 API 金鑰
    anthropic_api_key = api_key or os.environ.get("ANTHROPIC_API_KEY")
    if not anthropic_api_key:
        raise ValueError("未提供 Anthropic API 金鑰。請通過參數傳遞或設置 ANTHROPIC_API_KEY 環境變數。")
    
    # 初始化基本的新聞分析 Agent
    news_agent = NewsAnalysisAgent(
        api_key=anthropic_api_key,
        model_name=model_name,
        temperature=temperature,
        templates_dir=templates_dir
    )
    
    # 創建工具
    tools = [
        NewsAnalysisTool(agent=news_agent),
        VisualizationTool(agent=news_agent),
        ReportGenerationTool(agent=news_agent)
    ]
    
    # 初始化 Claude LLM
    llm = ChatAnthropic(
        temperature=temperature,
        model=model_name,
        anthropic_api_key=anthropic_api_key,
        max_tokens=4000  # 設置適合 Claude 的 token 限制
    )
    
    # 創建記憶
    memory = ConversationBufferMemory(memory_key="chat_history", return_messages=True)
    
    # 初始化 Agent - 使用較新的 Agent 格式
    agent_kwargs = {
        "extra_prompt_messages": [
            SystemMessage(content="你是一個專業的新聞分析 AI 助手，負責分析新聞數據並生成報告。你應該保持客觀公正，基於事實和數據進行分析。")
        ]
    }
    
    agent = initialize_agent(
        tools=tools,
        llm=llm,
        agent=AgentType.CHAT_CONVERSATIONAL_REACT_DESCRIPTION,
        memory=memory,
        verbose=True,
        agent_kwargs=agent_kwargs
    )
    
    return agent


def main():
    """主程序入口"""
    # 從環境變量或配置文件中加載 API 密鑰
    api_key = os.environ.get("OPENAI_API_KEY")
    
    # 從文件加載新聞數據
    with open("news_data.json", "r", encoding="utf-8") as f:
        news_data = json.load(f)
    
    # 創建基本的分析 Agent
    agent = NewsAnalysisAgent(api_key=api_key)
    
    # 運行完整分析
    output_path = "news_analysis_report.html"
    agent.run_full_analysis(news_data, output_path)
    logger.info(f"分析完成，報告已保存至 {output_path}")


# 創建基於 Langchain 的 Agent 進行交互式分析的範例
def interactive_analysis():
    """使用 Langchain Agent 進行交互式新聞分析"""
    agent = create_news_analysis_agent()
    
    # 運行 Agent
    agent.run("我想分析 news_data.json 中的新聞資料，請幫我創建一份專業的分析報告。")


if __name__ == "__main__":
    main()
    # 或者使用交互式分析
    # interactive_analysis()