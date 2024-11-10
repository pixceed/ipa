'''
画像を分析
'''

from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from langchain_core.messages import SystemMessage, HumanMessage
from langchain_community.callbacks.manager import get_openai_callback

import base64

# .envファイルから環境変数を読み込み
load_dotenv()

# OpenAIのLLMインスタンス作成
chat_model = ChatOpenAI(model="gpt-4o-mini", temperature=1)


# 画像をbase64形式のデータに変換
image_path = "output/2021r03h_nw_pm1_qs_20241110070344/mon1/picture-1.png"
with open(image_path, "rb") as image_file:
    # base64エンコード
    encoded_string = base64.b64encode(image_file.read())
    # バイト列を文字列にデコードして返す
    image_data1 = encoded_string.decode('utf-8')


image_path = "output/2021r03h_nw_pm1_qs_20241110070344/mon1/picture-2.png"
# 画像をbase64形式のデータに変換
with open(image_path, "rb") as image_file:
    # base64エンコード
    encoded_string = base64.b64encode(image_file.read())
    # バイト列を文字列にデコードして返す
    image_data2 = encoded_string.decode('utf-8')


# システムプロンプト
system_prompt = SystemMessage(
    content=\
"""
図2のみ説明してください。
"""
)


image_message = HumanMessage(
    content=[
        {
        "type": "text",
        "text": "1つ目の画像:図1、2つ目の画像:図2"
        },
        {
            "type": "image_url",
            "image_url": {"url": f"data:image/jpeg;base64,{image_data1}"},
        },
        {
            "type": "image_url",
            "image_url": {"url": f"data:image/jpeg;base64,{image_data2}"},
        },
    ],
)
messages = [system_prompt, image_message]


with get_openai_callback() as cb:
    result = chat_model.invoke(messages)

    md_text = result.content
    md_text = md_text.replace("```markdown", "").replace("```", "")
    
    print(md_text)

    print(f"Total Tokens: {cb.total_tokens}")
    print(f"Prompt Tokens: {cb.prompt_tokens}")
    print(f"Completion Tokens: {cb.completion_tokens}")
    print(f"Total Cost (USD): ${cb.total_cost}")

