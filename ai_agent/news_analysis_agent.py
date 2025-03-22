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
from prompt_library.utils import read_html_template, read_js_file
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
    js: str = Field(description="生成的 .js 代碼")
    reason: str = Field(description="分析此圖表的原因")
    file_name: str = Field(description="存檔的.js檔名")
    
class NewsAnalysisAgent:
    def __init__(self, 
                 api_key: Optional[str] = None, 
                 model_name: str = "claude-3-7-sonnet-20250219",
                 temperature: float = 0.3,
                 templates_dir: Optional[str] = None):
        """
        初始化新聞分析 Agent
        
        Args:
            api_key: LLM API 金鑰，如果是 None 則從環境變量獲取
            model_name: 要使用的模型名稱
            temperature: 模型溫度
            templates_dir: HTML 模板所在目錄，如果是 None 則使用預設路徑
        """
        # 獲取當前檔案的目錄
        current_dir = os.path.dirname(os.path.abspath(__file__))
        # 如果沒有指定 templates_dir，使用預設路徑
        if templates_dir is None:
            # 構建預設的模板目錄路徑（上一層目錄的 website/templates）
            self.templates_dir = os.path.abspath(os.path.join(current_dir, "..", "website", "templates"))
        else:
            # 如果指定了路徑，轉換為絕對路徑
            self.templates_dir = os.path.abspath(templates_dir)
            
        logger.info(f"使用模板目錄：{self.templates_dir}")
        
        self.temperature = temperature
        self.model_name = model_name
        
        # 導入 Anthropic 相關模組
        from langchain_anthropic import ChatAnthropic
        
        self.api_key = api_key or os.environ.get("ANTHROPIC_API_KEY")
        if not self.api_key:
            raise ValueError("API 金鑰未提供，請通過參數或環境變量 ANTHROPIC_API_KEY 設置")
            
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
            "台灣地理區域數值分布圖",
            "重大時間線軸圖",
            "比例圓餅圖",
            # "財務報表分析",
            "新聞媒體立場分析比較表",
            "爭議立場比較分析表",
            "桑基圖"
        ]
        
        # 檢查模板目錄是否存在
        if not os.path.exists(self.templates_dir):
            error_msg = f"錯誤：模板目錄不存在：{self.templates_dir}"
            logger.error(error_msg)
            raise FileNotFoundError(error_msg)
            
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
        """初始化所有的 Langchain 鏈"""
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
        
        # 可視化生成鏈 - 修改這裡，只使用必要的輸入變數     
        self.visualization_prompt = ChatPromptTemplate(
            messages=[
                SystemMessagePromptTemplate.from_template(visualization_system_template),
                HumanMessagePromptTemplate.from_template(visualization_human_template)
            ],
            input_variables=["tool", "reason", "template", "news_data"],  # 添加 news_data
        )
        
        # 最終報告生成鏈
        self.report_prompt = ChatPromptTemplate(
            messages=[
                SystemMessagePromptTemplate.from_template(report_system_template),
                HumanMessagePromptTemplate.from_template(report_human_template)
            ],
            input_variables=["analysis_summary", "visualizations", "report_template", "news_data"]  # 添加 news_data
        )
        
        self.report_chain = LLMChain(
            llm=self.report_llm,
            prompt=self.report_prompt,
            output_key="report_result",
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
        news_data_str = json.dumps(news_data, ensure_ascii=False, indent=2)
        tools_str = "\n".join([f"{i+1}. {tool}" for i, tool in enumerate(self.analysis_tools)])
        
        try:
            # 執行分析鏈，使用字典方式傳遞參數
            result = self.analysis_chain({
                "news_data": news_data_str,
                "tools": tools_str
            })
            
            # 修改這裡，使用正確的鍵名獲取結果
            parsed_result = self.analysis_fixing_parser.parse(result["analysis_result"])
            logger.info(f"新聞分析完成，主要主題: {parsed_result.main_topic}")
            logger.info(f"需要使用工具: {parsed_result.required_tools}")
            logger.info(f"選擇這些工具的理由: {parsed_result.rationale}")
                        
            return parsed_result
            
        except Exception as e:
            error_msg = f"分析新聞數據時出錯: {str(e)}"
            logger.error(error_msg)
            raise Exception(error_msg)
    
    def generate_visualizations(self, required_tools: List[str], rationale: Dict[str, str], news_data: str) -> List[Visualization]:
        """
        第二步：根據分析結果為每種所需工具生成可視化圖表
        """
        visualizations = []
        self.visualization_file_names = dict()
        
        # 創建可視化輸出目錄
        output_dir = "outputs"
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        for tool in required_tools:
            try:
                # 讀取對應的 js 模板
                template = self._get_default_template(tool)
                if not template:
                    logger.warning(f"模板文件 {tool} 不存在，將使用空白模板")

                # 創建視覺化生成鏈
                visualization_chain = LLMChain(
                    llm=self.visualization_llm,
                    prompt=self.visualization_prompt,
                    output_key="visualization_result",
                    verbose=True
                )
                # 直接傳入所有需要的參數
                visualization_js = visualization_chain.run({
                    "tool": tool,
                    "reason": rationale[tool],
                    "template": template,
                    "news_data": news_data  # 添加 news_data
                })
                
                # 生成文件名
                safe_tool_name = tool.replace("/", "_").replace(" ", "_")
                file_name = f"{safe_tool_name}_{timestamp}.js"
                self.visualization_file_names.update({tool: file_name})
                file_path = os.path.join(output_dir, file_name)
                
                with open(file_path, "w", encoding="utf-8") as f:
                    f.write(visualization_js)
                
                visualizations.append(Visualization(
                    tool=tool,
                    js=visualization_js,
                    reason=rationale[tool],
                    file_name=file_name
                ))
                
                logger.info(f"已為 {tool} 生成可視化圖表")
                time.sleep(1)
                
            except Exception as e:
                error_msg = f"為工具 {tool} 生成可視化時出錯: {str(e)}"
                logger.error(error_msg)
                raise Exception(error_msg)
        
        return visualizations
    
    def create_final_report(self, 
                           analysis_result: AnalysisResult,
                           visualizations: List[Visualization],
                           news_data: str) -> str:  # 添加 news_data 參數
        """
        第三步：整合所有可視化並生成最終的分析報告
        
        Args:
            analysis_result: 分析結果
            visualizations: 生成的可視化圖表列表
            
        Returns:
            完整的 HTML 報告
        """
        # 讀取報告模板
        report_template = self._get_default_report_template()
        if not report_template:
            logger.warning("報告模板不存在，將使用空白模板")
        
        # 視覺化 HTML 代碼的準備
        visualizations_str = "\n\n".join([
            f"({i+1}) {vis.tool}, 檔名:{vis.file_name}, 分析原因:{vis.reason}" 
            for i, vis in enumerate(visualizations)
        ])
        
        # 執行報告生成鏈
        try:
            final_report = self.report_chain.run({
                "analysis_summary": json.dumps(analysis_result.dict(), ensure_ascii=False, indent=2),
                "visualizations": visualizations_str,
                "report_template": report_template,
                "news_data": news_data  # 添加 news_data
            })
            
            logger.info("最終報告生成完成")
            return final_report
            
        except Exception as e:
            error_msg = f"生成最終報告時出錯: {str(e)}"
            logger.error(error_msg)
            raise Exception(error_msg)
    
    def save_report(self, report: str, output_path: str = "outputs/report.html") -> None:
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
        """執行完整的分析流程"""
        news_data_str = json.dumps(news_data, ensure_ascii=False, indent=2)
        
        logger.info("1. 開始分析新聞資料...")
        analysis_result = self.analyze_news_data(news_data)
        
        logger.info(f"2. 生成可視化圖表 (需要工具: {', '.join(analysis_result.required_tools)})...")
        visualizations = self.generate_visualizations(
            analysis_result.required_tools,
            analysis_result.rationale,
            news_data_str  # 傳入 news_data
        )
        
        logger.info("3. 創建最終報告...")
        final_report = self.create_final_report(
            analysis_result,
            visualizations,
            news_data_str  # 傳入 news_data
        )
        
        self.save_report(final_report, output_path)
        
        return final_report
    
    def _get_default_template(self, tool: str) -> str:
        """
        獲取默認的工具模板
        """
        # 這裡為各種工具提供默認模板
        templates = {
            "時間變化趨勢圖": read_js_file(os.path.join(self.templates_dir, "time_trend.js")),
            "比例圓餅圖": read_js_file(os.path.join(self.templates_dir, "piechart.js")),
            "數值分類排序": read_js_file(os.path.join(self.templates_dir, "sorted-chart.js")),
            "台灣地理區域數值分布圖": read_js_file(os.path.join(self.templates_dir, "taiwan-map.js")),
            "重大時間線軸圖": read_js_file(os.path.join(self.templates_dir, "timeline.js")),
            # "財務報表分析": read_js_file(os.path.join(self.templates_dir, "financial_report_analysis.html")),
            "新聞媒體立場分析比較表": read_js_file(os.path.join(self.templates_dir, "media.js")),
            "爭議立場比較分析表": read_js_file(os.path.join(self.templates_dir, "controversial_standpoint_comparison.js")),
            "桑基圖": read_js_file(os.path.join(self.templates_dir, "sankey.js"))
        }
        
        # 為其他工具添加默認模板
        return templates.get(tool, "")
    
    def _get_default_report_template(self) -> str:
        """
        獲取默認的報告模板
        """
        return read_html_template(os.path.join(self.templates_dir, "report_template.html"))


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
            rationale = input_data.get("rationale")
            
            visualizations = self.agent.generate_visualizations(tools, rationale, json.dumps(news_data, ensure_ascii=False, indent=2))
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
            
            final_report = self.agent.create_final_report(
                analysis_result,
                visualizations,
                json.dumps(news_data, ensure_ascii=False, indent=2)  # 傳入 news_data
            )
            
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
                             templates_dir: Optional[str] = None) -> Any:
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