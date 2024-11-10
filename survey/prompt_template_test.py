from langchain_core.prompts import PromptTemplate

# プロンプトテンプレートの準備
prompt_template = PromptTemplate(
    input_variables=["product"],
    template="{product}を作る日本語の新会社名をを1つ提案してください",
)

# プロンプトテンプレートの実行
output = prompt_template.invoke({"product": "家庭用ロボット"})
print(type(output))
print(output.text)