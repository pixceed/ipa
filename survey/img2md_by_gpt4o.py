'''
画像をマークダウンに変換
'''

from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from langchain_core.messages import SystemMessage, HumanMessage
from langchain_community.callbacks.manager import get_openai_callback

import base64

# .envファイルから環境変数を読み込み
load_dotenv()

image_path = "output/2021r03h_nw_pm1_qs_20241108151450/mon0/page-6.png"
output_path = image_path.replace(".png", ".txt")

# OpenAIのLLMインスタンス作成
chat_model = ChatOpenAI(model="gpt-4o-mini", temperature=1)

# 画像をbase64形式のデータに変換
with open(image_path, "rb") as image_file:
    # base64エンコード
    encoded_string = base64.b64encode(image_file.read())
    # バイト列を文字列にデコードして返す
    image_data = encoded_string.decode('utf-8')


# システムプロンプト
# system_prompt = SystemMessage(
#     content=\
# """
# あなたは天才的な文書作成者です。
# 画像から文章を読み取り、テキスト形式にまとめることができます。
# 画像中における図の部分は、例えば図1であれば`![Local Image](picture-1.png)\n`としてください。
# 画像中における表の部分は、例えば表1であれば`![Local Image](table-1.png)\n`としてください。
# なお、図や表の番号およびキャプションは、文章内に記載してください。
# 出力は、必ずテキスト文章のみで、余計な文章は含めないでください。
# テキストに変換できない場合は、その理由を必ず出力してください。
# """
# )
system_prompt = SystemMessage(
    content=\
"""
あなたは天才的な文書作成者です。
画像から文章を読み取り、テキスト形式にまとめてください。
画像中における図の部分は、例えば図1であれば`![Local Image](picture-1.png)\n`としてください。
画像中における表の部分は、例えば表1であれば`![Local Image](table-1.png)\n`としてください。
なお、図や表の番号およびキャプションは、文章内に記載してください。
出力は、必ずテキスト文章のみで、余計な文章は含めないでください。
テキストに変換できない場合は、その理由を必ず出力してください。
"""
)


image_message = HumanMessage(
    content=[
        {
            "type": "image_url",
            "image_url": {"url": f"data:image/jpeg;base64,{image_data}"},
        },
    ],
)
messages = [system_prompt, image_message]


with get_openai_callback() as cb:
    result = chat_model.invoke(messages)

    md_text = result.content
    md_text = md_text.replace("```markdown", "").replace("```", "")

    with open(output_path, mode="w", encoding="utf-8") as f:
        f.write(md_text)
    
    print(md_text)

    print(f"Total Tokens: {cb.total_tokens}")
    print(f"Prompt Tokens: {cb.prompt_tokens}")
    print(f"Completion Tokens: {cb.completion_tokens}")
    print(f"Total Cost (USD): ${cb.total_cost}")

