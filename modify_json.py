import json

# 1. 讀取 JSON 檔案
with open('updated_news_data.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

# 2. 移除指定的 keys (以列表指定要刪除的 keys)
keys_to_remove = ['網址', '關鍵字', '抓取時間', '搜索批次', '_id']  

# # 如果 JSON 結構是字典：
# for key in keys_to_remove:
#     data.pop(key, None)

# 如果 JSON 是列表且每個元素是字典：
for item in data:
    for key in keys_to_remove:
        item.pop(key, None)

# 3. 儲存成新的 JSON 檔案
with open('updated_news_data_2.json', 'w', encoding='utf-8') as f:
    json.dump(data, f, ensure_ascii=False, indent=4)