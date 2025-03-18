# import anthropic

# client = anthropic.Anthropic()
# models = client.models.list()

# # 所有可用模型
# for model in models.data:
#     print(f"ID: {model.id}, Created: {model.created_at}")
# """
# ID: claude-3-7-sonnet-20250219, Created: 2025-02-24 00:00:00+00:00
# ID: claude-3-5-sonnet-20241022, Created: 2024-10-22 00:00:00+00:00
# ID: claude-3-5-haiku-20241022, Created: 2024-10-22 00:00:00+00:00
# ID: claude-3-5-sonnet-20240620, Created: 2024-06-20 00:00:00+00:00
# ID: claude-3-haiku-20240307, Created: 2024-03-07 00:00:00+00:00
# ID: claude-3-opus-20240229, Created: 2024-02-29 00:00:00+00:00
# """

from langchain_anthropic import ChatAnthropic
from langchain.chains import ConversationChain
from langchain.memory import ConversationBufferMemory

# 初始化模型與記憶
memory = ConversationBufferMemory()
conversation = ConversationChain(
    llm=ChatAnthropic(model="claude-3-7-sonnet-20250219",
    system="你是一個專業的繁體中文新聞記者，你的立場客觀公正。"),
    memory=memory,
    verbose=True
)

# 進行對話
response1 = conversation.predict(input="你好！我叫小明。")
print(response1)

response2 = conversation.predict(input="你記得我的名字嗎？")
print(response2)

