import os
import base64

from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from typing import Annotated  # 型ヒント用のモジュール
from typing_extensions import TypedDict  # 型ヒント用の拡張モジュール
from langgraph.graph import StateGraph
from langgraph.graph.message import add_messages

from langchain_core.prompts import PromptTemplate

# .envファイルから環境変数を読み込み
load_dotenv()

def main():

    input_dir = "output/2021r03h_nw_pm1_qs_20241110070344/mon1"

    # 情報取得
    mon_id = input_dir.split("/")[-1]
    exam_id = "_".join(input_dir.split("/")[-2].split("_")[0:-1])
    exam_id = exam_id.replace('_qs', '')

    mon_md_path = os.path.join(input_dir, f"{exam_id}_{mon_id}.md")
    with open(mon_md_path, mode="r") as f:
        mon_md_text = f.read()
    review_md_path = os.path.join(input_dir, f"{exam_id}_{mon_id}_review.md")
    with open(review_md_path, mode="r") as f:
        review_md_text = f.read()
    
    # 状態の型定義。messagesにチャットのメッセージ履歴を保持する
    class State(TypedDict):
        messages: Annotated[list, add_messages]
    
    # グラフビルダーを作成し、チャットボットのフローを定義
    graph_builder = StateGraph(State)

    # OpenAIのLLMインスタンス作成
    chat_model = ChatOpenAI(model="gpt-4o-mini", temperature=1)

    # チャットボット関数。状態に応じてLLMが応答を生成
    def chatbot(state: State):
        return {"messages": [chat_model.invoke(state["messages"])]}
    
    # グラフを構築
    graph_builder.add_node("chatbot", chatbot)
    graph_builder.set_entry_point("chatbot")

    # グラフをコンパイル
    agent = graph_builder.compile()

    # チャットヒストリーを作成
    state = {"messages": []}

    # システムプロンプトを設定
    system_prompt = \
"""
あなたは、ネットワークのスペシャリストです。
ユーザーからの質問に、分かりやすく回答してください。
"""
    system_message = {
        "role": "system",
        "content": system_prompt
    }
    state["messages"].append(system_message)


    # 最初のユーザープロンプトを設定
    prompt_template1 = PromptTemplate(
        input_variables=["exam_content"],
        template=\
"""
以下の試験問題について、各問題に対して解説してください。

<試験問題>
{exam_content}
</試験問題>
""",
    )
    user_prompt = prompt_template1.invoke({
        "exam_content": mon_md_text
    })
    user_prompt_text = user_prompt.text
    user_content = []

    # 図の設定
    image_path_list = []
    for file_name in os.listdir(input_dir):
        if file_name.startswith("picture-"):
            image_path = os.path.join(input_dir, file_name)
            image_path_list.append(image_path)
    image_path_list.sort()
    
    user_prompt_text += f"\n\n<図の詳細>"
    for i in range(len(image_path_list)):
        user_prompt_text += f"\n{i+1}つ目の画像:図{i+1}"
    user_prompt_text += f"\n</図の詳細>"

    
    user_content.append(
        {
        "type": "text",
        "text": user_prompt_text
        }
    )

    for image_path in image_path_list:
        # 画像をbase64形式のデータに変換
        with open(image_path, "rb") as image_file:
            # base64エンコード
            encoded_string = base64.b64encode(image_file.read())
            # バイト列を文字列にデコードして返す
            image_data = encoded_string.decode('utf-8')

            user_content.append(
                {
                    "type": "image_url",
                    "image_url": {"url": f"data:image/jpeg;base64,{image_data}"},
                }
            )

    state["messages"].append({
            "role": "user", 
            "content": user_content
        },
    )

    # 最初のエージェントからの回答を設定
    # 最初のユーザープロンプトを設定
    prompt_template2 = PromptTemplate(
        input_variables=["exam_review"],
        template=\
"""
以下に、各問題に対する回答と解説を示します。

---

{exam_review}
""",
    )
    assistant_prompt = prompt_template2.invoke({
        "exam_review": review_md_text
    })

    state["messages"].append(
        {"role": "assistant", "content": assistant_prompt.text},
    )


    # ユーザーの入力に基づいてチャットボットが応答を生成し、その過程をリアルタイムでストリームする関数
    def stream_graph_updates(user_input: str):
        # ユーザーの入力をメッセージに追加
        state["messages"].append(("user", user_input))  
        
        # グラフのstreamメソッドを使用して、メッセージに応じたイベントを処理
        for event in agent.stream(state):
            for value in event.values():
                # チャットボットの応答をメッセージに追加
                response = value["messages"][-1].content
                state["messages"].append(("assistant", response))  # 応答もメッセージリストに追加
                print("Assistant:", response)

    # 無限ループを使用してユーザー入力を連続的に処理
    while True:
        try:
            # ユーザーからの入力を取得
            user_input = input("User: ")
            
            # "quit", "exit", "q"の入力でループを終了
            if user_input.lower() in ["quit", "exit", "q"]:
                print("Goodbye!")  # 終了メッセージを表示
                break  # ループを抜ける

            # ユーザーの入力を基にチャットボットが応答を生成し、リアルタイムで出力
            stream_graph_updates(user_input)

        except Exception as e:

            print(f"エラーが出ました\n{e}")  # 既定のユーザー入力を表示
            stream_graph_updates(user_input)  # その入力に対してチャットボットが応答を生成
            break  # エラーハンドリング後にループを終了


if __name__=="__main__":
    main()