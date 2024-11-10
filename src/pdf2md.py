import os
import cv2
import yaml
import base64
import argparse
import tempfile
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from langchain_core.messages import SystemMessage, HumanMessage
from langchain_community.callbacks.manager import get_openai_callback

from datetime import datetime
from docling_core.types.doc import ImageRefMode, PictureItem, TableItem

from src.modules.utils import split_pdf, setup_pdf_converter

# .envファイルから環境変数を読み込み
load_dotenv()


def main(configs):

    print(f"=============== 実行開始 ===============")

    # 設定値を取得
    output_dir = configs["output_dir"]
    pdf_path = configs["pdf_path"]
    ans_pdf_path = configs["ans_pdf_path"]
    split_page = configs["split_page"]


    # ＜入力ファイル名からタイムスタンプ付きディレクトリの作成＞
    exam_id = os.path.splitext(os.path.basename(pdf_path))[0]
    file_name = f"{exam_id}_{datetime.now().strftime('%Y%m%d%H%M%S')}"
    output_dir = os.path.join(output_dir, file_name)
    os.makedirs(output_dir, exist_ok=True)


    # PDFを問題ごとに分割
    split_pdf_path_list = []
    for i, (start_page, end_page) in enumerate(split_page):
        split_output_dir = os.path.join(output_dir, f"mon{i+1}")
        os.makedirs(split_output_dir, exist_ok=True)
        split_pdf_path = split_pdf(pdf_path, split_output_dir, start_page, end_page)
        if split_pdf_path == None:
            continue
        split_pdf_path_list.append((split_output_dir, split_pdf_path))

    print(f"=============== 分割完了 ===============")

    # PDFコンバーターを生成
    pdf_converter = setup_pdf_converter()
    # OpenAIのLLMインスタンス作成
    chat_model = ChatOpenAI(model="gpt-4o", temperature=0)
    # システムプロンプト
    system_prompt0 = SystemMessage(
        content=\
"""
あなたは天才的な文書作成者です。
画像から文章を読み取り、テキスト形式にまとめてください。

なお、画像最下部に記載されているページ番号やコピーライト情報は含めないでください。

出力は、必ずテキスト文章のみで、余計な文章は含めないでください。
"""
    )

    system_prompt1 = SystemMessage(
        content=\
"""
あなたは天才的な文書作成者です。
画像から文章を読み取り、テキスト形式にまとめてください。

画像中における図の部分は、`![Local Image](picture-$.png)\n`($は図番号)としてください。
（例えば図1であれば`![Local Image](picture-1.png)\n`とする）
なお、図や表の番号およびキャプションは、文章内に記載してください。

また、虫食い部分は、必ず`「」`という形式にしてください。（表内も適用すること）
（例えば、`「ア」`, `「a」`とする）

また、下線部分の先頭の文字は、間違えないように重点的に確認してください。

また、画像最下部に記載されているページ番号は含めないでください。

出力は、必ずテキスト文章のみで、余計な文章は含めないでください。
"""
    )

    system_prompt2 = SystemMessage(
        content=\
"""
あなたは天才的な文書編集者です。
与えられたテキスト文章を、文章は絶対に変えずに、マークダウンの見出しや段落を付与して見やすくしてください。
与えられた元の文章は絶対に変えないでください！
出力には、余計な文章は含めないでください。
"""
    )

    # 解答例に対して、処理を実施
    print(f"=============== 解答例 解析開始 ===============")

    # ＜PDFを画像に変換＞
    conv_res = pdf_converter.convert(ans_pdf_path)

    # ページ画像を保存
    ans_output_dir = os.path.join(output_dir, "ans")
    os.makedirs(ans_output_dir, exist_ok=True)
    ans_files = []
    for page_no, page in conv_res.document.pages.items():
        page_no = page.page_no
        page_image_filename = os.path.join(ans_output_dir, f"ans-{page_no}.png")
        with open(page_image_filename, "wb") as fp:
            page.image.pil_image.save(fp, format="PNG")
        ans_files.append(page_image_filename)

    # ＜GPT-4oでOCR＞
    ans_files.sort()
    ans_all_text = ""
    for image_path in ans_files:
        # 画像をbase64形式のデータに変換
        with open(image_path, "rb") as image_file:
            # base64エンコード
            encoded_string = base64.b64encode(image_file.read())
            # バイト列を文字列にデコードして返す
            image_data = encoded_string.decode('utf-8')

        image_message = HumanMessage(
            content=[
                {
                    "type": "image_url",
                    "image_url": {"url": f"data:image/jpeg;base64,{image_data}"},
                },
            ],
        )
        messages = [system_prompt0, image_message]
        result = chat_model.invoke(messages)

        result_text = result.content
        result_text = result_text.replace("```plaintext", "").replace("```", "")

        ans_all_text += f"\n\n{result_text}"
    
    output_path = os.path.join(
        ans_output_dir, os.path.basename(ans_pdf_path).replace(".pdf", ".txt"))
    with open(output_path, mode="w", encoding="utf-8") as f:
        f.write(ans_all_text)

    # マークダウン形式に整形する

    format_message = HumanMessage(content=ans_all_text)
    messages = [system_prompt2, format_message]

    ans_result = chat_model.invoke(messages)
    ans_md = ans_result.content
    ans_md = ans_md.replace("```plaintext", "").replace("```", "")

    output_path = os.path.join(
        ans_output_dir, os.path.basename(ans_pdf_path).replace(".pdf", ".md"))
    with open(output_path, mode="w", encoding="utf-8") as f:
        f.write(ans_md)

    # exit()

    # 各問題で、処理を実施
    for i, (split_output_dir, split_pdf_path) in enumerate(split_pdf_path_list):

        # if i != 1:
        #     continue

        print(f"=============== {i+1}問目 処理中 ===============")

        # ＜PDFを画像に変換＆PDFから図や表を抽出する＞
        conv_res = pdf_converter.convert(split_pdf_path)

        # ページ画像を保存
        for page_no, page in conv_res.document.pages.items():
            page_no = page.page_no
            page_image_filename = os.path.join(split_output_dir, f"page-{page_no}.png")
            with open(page_image_filename, "wb") as fp:
                page.image.pil_image.save(fp, format="PNG")

        # 図と表を保存
        table_counter = 0
        picture_counter = 0
        for element, _level in conv_res.document.iterate_items():
            if isinstance(element, TableItem):
                table_counter += 1
                element_image_filename = \
                    os.path.join(split_output_dir, f"table-{table_counter}.png")
                
                with open(element_image_filename, "wb") as fp:
                    element.image.pil_image.save(fp, "PNG")

            if isinstance(element, PictureItem):
                picture_counter += 1
                element_image_filename = \
                    os.path.join(split_output_dir, f"picture-{picture_counter}.png")
                with open(element_image_filename, "wb") as fp:
                    element.image.pil_image.save(fp, "PNG")
        
        print("図と表、抽出完了")

        # ＜GPT-4oでOCR＞
        with get_openai_callback() as cb:

            # ページ画像のファイルパスを全て取得
            page_files = []
            for filename in os.listdir(split_output_dir):
                if filename.startswith("page-"):
                    file_path = os.path.join(split_output_dir, filename)
                    page_files.append(file_path)
            page_files.sort()

            # 画像をGPTに投げる
            mon_all_text = ""
            for image_path in page_files:

                with tempfile.TemporaryDirectory() as dname:

                    # 画像を2値化
                    image = cv2.imread(image_path)
                    gray_image = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
                    threshold_value = 128
                    _, binary_image = cv2.threshold(gray_image, threshold_value, 255, cv2.THRESH_BINARY)
                    temp_img_path = os.path.join(dname, 'temp.png')
                    cv2.imwrite(temp_img_path, binary_image)
 
                    # 画像をbase64形式のデータに変換
                    with open(temp_img_path, "rb") as image_file:
                        # base64エンコード
                        encoded_string = base64.b64encode(image_file.read())
                        # バイト列を文字列にデコードして返す
                        image_data = encoded_string.decode('utf-8')
            
                    image_message = HumanMessage(
                        content=[
                            {
                                "type": "image_url",
                                "image_url": {"url": f"data:image/jpeg;base64,{image_data}"},
                            },
                        ],
                    )
                    messages = [system_prompt1, image_message]
                    result = chat_model.invoke(messages)

                    result_text = result.content
                    result_text = result_text.replace("```plaintext", "").replace("```", "")

                    mon_all_text += f"\n\n{result_text}"

            output_path = os.path.join(split_output_dir, f"{exam_id}_mon{i+1}.md")
            with open(output_path, mode="w", encoding="utf-8") as f:
                f.write(mon_all_text)
            
            print("GPT4oによる画像OCR、完了")
            
            # マークダウン形式に整形する

            format_message = HumanMessage(content=mon_all_text)
            messages = [system_prompt2, format_message]

            final_result = chat_model.invoke(messages)
            final_text = final_result.content
            final_text = final_text.replace("```plaintext", "").replace("```", "")

            output_path = os.path.join(split_output_dir, f"{exam_id}_mon{i+1}_md.md")
            with open(output_path, mode="w", encoding="utf-8") as f:
                f.write(final_text)

            print("GPT4oによるマークダウン形式変換、完了")

            print(f"\nTotal Tokens: {cb.total_tokens}")
            print(f"Prompt Tokens: {cb.prompt_tokens}")
            print(f"Completion Tokens: {cb.completion_tokens}")
            print(f"Total Cost (USD): ${cb.total_cost}\n")
        

    print(f"=============== 実行終了 ===============")


if __name__=="__main__":

    # コマンドライン引数の取得
    parser = argparse.ArgumentParser(description="モデル作成")
    parser.add_argument("-c", "--config", help="設定ファイルのパスを指定してください。")

    args = parser.parse_args()
    config_path = args.config

    # 設定ファイル読み込み
    with open(config_path) as file:
        configs = yaml.safe_load(file)

    main(configs)