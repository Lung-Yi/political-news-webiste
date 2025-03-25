# 使用範例：從爬蟲資料生成新聞分析報告

import json
import os
from news_analysis_agent import NewsAnalysisAgent, create_news_analysis_agent

# 方法一：基本的流程化分析（適合批處理）
def basic_analysis(data_path):
    # 1. 加載爬蟲獲取的新聞資料
    with open(data_path, "r", encoding="utf-8") as f:
        news_data = json.load(f)
    
    # 2. 初始化分析 Agent
    agent = NewsAnalysisAgent(
        model_provider="openai",
        model_name="gpt-4o-2024-11-20",
        templates_dir="../website/templates"
    )
    
    # 3. 運行分析
    final_report = agent.run_full_analysis(news_data, "../website/outputs_3/news_analysis_report.html")
    print("分析報告已生成")
    
    # 如果需要查看分析的細節，可以使用下面的步驟
    
    # # 3.1 單獨執行分析步驟
    # analysis_result = agent.analyze_news_data(news_data)
    # print(f"主要主題: {analysis_result.main_topic}")
    # print(f"需要使用的工具: {analysis_result.required_tools}")
    
    # # 3.2 單獨生成可視化
    # visualizations = agent.generate_visualizations(analysis_result.required_tools)
    # print(f"生成了 {len(visualizations)} 個可視化圖表")
    
    # # 3.3 生成最終報告
    # report = agent.create_final_report(analysis_result, visualizations)
    # agent.save_report(report, "detailed_report.html")


# # 方法二：交互式 Agent（適合需要對話的情境）
# def interactive_analysis():
#     # 創建 Langchain Agent
#     agent = create_news_analysis_agent(
#         model_name="gpt-4",
#         temperature=0.3
#     )
    
#     # 運行初始查詢
#     agent.run("我想分析 news_data.json 中的新聞資料，生成一份關於台灣預算的分析報告。")
    
#     # 可以繼續與 agent 進行對話，如：
#     # agent.run("請特別關注資安預算的部分")
#     # agent.run("你能把折線圖改為柱狀圖嗎？")


# # 方法三：使用 API 進行綜合分析（適合作為服務）
# def api_based_analysis(news_data_json, output_path=None):
#     """提供 API 式的接口，方便整合到其他系統中"""
    
#     # 1. 解析輸入的 JSON 數據
#     try:
#         news_data = json.loads(news_data_json)
#     except json.JSONDecodeError:
#         return {"status": "error", "message": "無效的 JSON 數據"}
    
#     # 2. 初始化分析 Agent
#     try:
#         agent = NewsAnalysisAgent(
#             api_key=os.environ.get("OPENAI_API_KEY"),
#             model_name="gpt-4"
#         )
#     except Exception as e:
#         return {"status": "error", "message": f"初始化 Agent 失敗: {str(e)}"}
    
#     # 3. 進行分析
#     try:
#         # 分析新聞
#         analysis_result = agent.analyze_news_data(news_data)
        
#         # 生成可視化
#         visualizations = agent.generate_visualizations(news_data, analysis_result.required_tools)
        
#         # 生成報告
#         report = agent.create_final_report(news_data, analysis_result, visualizations)
        
#         # 如果指定了輸出路徑，保存報告
#         if output_path:
#             agent.save_report(report, output_path)
            
#         return {
#             "status": "success",
#             "analysis": analysis_result.dict(),
#             "visualization_count": len(visualizations),
#             "report": report,
#             "output_path": output_path
#         }
#     except Exception as e:
#         return {"status": "error", "message": f"分析過程中出錯: {str(e)}"}


if __name__ == "__main__":
    # 選擇要運行的分析方法
    file_path = "../updated_news_data_2.json"
    basic_analysis(file_path)
    # interactive_analysis()
    
    # API 式使用範例
    # with open("news_data.json", "r", encoding="utf-8") as f:
    #     result = api_based_analysis(f.read(), "api_report.html")
    #     print(f"API 分析結果: {result['status']}")