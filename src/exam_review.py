import os

from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from langchain_core.messages import SystemMessage, HumanMessage
from langchain_core.prompts import PromptTemplate
from langchain_core.output_parsers import MarkdownListOutputParser
from langchain_core.output_parsers import StrOutputParser
from langchain_community.callbacks.manager import get_openai_callback

# .envファイルから環境変数を読み込み
load_dotenv()

def main():
    input_dir = "output/2021r03h_nw_pm1_qs_20241110070344"

    # 情報取得
    exam_id = "_".join(input_dir.split("/")[-1].split("_")[0:-1])
    exam_id = exam_id.replace('_qs', '')

    ans_md_path = os.path.join(input_dir, "ans", f"{exam_id}_ans.md")

    mon_md_path_list = []
    for dir in os.listdir(input_dir):
        if dir.startswith("mon"):
            mon_dir_path = os.path.join(input_dir, dir)
            mon_md_path = os.path.join(
                input_dir, dir, f"{exam_id}_mon{dir.replace('mon', '')}_md.md"
            )
            mon_md_path_list.append((mon_dir_path, mon_md_path))
    mon_md_path_list.sort()

    # OpenAIのLLMインスタンス作成
    chat_model = ChatOpenAI(model="gpt-4o", temperature=0)

    # プロンプトテンプレートの準備
    prompt_template = PromptTemplate(
        input_variables=["exam_content", "exam_ans"],
        template=\
"""

あなたは天才的な試験解説者です。

まずは、<試験問題></試験問題>をよく理解し、
<試験解答例></試験解答例>の該当問題の解答例部分を抽出してください。
その後、各問題に対して、解答例の根拠となる解説を行ってください。
最後に、各問題に対する解答例と解説を整理して、出力してください。

<試験問題>
{exam_content}
</試験問題>

<試験解答例>
{exam_ans}
</試験解答例>

出力には、必ず解答例と解説のみで、余計な文章は含めないでください。
""",
    )

    # OutputParserの準備
    output_parser = StrOutputParser()

    chain = prompt_template | chat_model | output_parser

    with open(ans_md_path, mode="r") as f:
        exam_ans_text = f.read()

    for i, (mon_dir_path, mon_md_path) in enumerate(mon_md_path_list):

        # if i != 1:
        #     continue

        with get_openai_callback() as cb:
            with open(mon_md_path, mode="r") as f:
                exam_mon_text = f.read()

            output = chain.invoke(
                {   
                    "exam_content": exam_mon_text,
                    "exam_ans": exam_ans_text,
                })
            
            output_path = os.path.join(mon_dir_path, f"{exam_id}_mon{i+1}_review.md")
            with open(output_path, mode="w") as f:
                f.write(output)
            
            
            print(f"\nTotal Tokens: {cb.total_tokens}")
            print(f"Prompt Tokens: {cb.prompt_tokens}")
            print(f"Completion Tokens: {cb.completion_tokens}")
            print(f"Total Cost (USD): ${cb.total_cost}\n")
            
        


if __name__=="__main__":
    main()