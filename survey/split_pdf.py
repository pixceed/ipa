'''
PDFを指定のページで分割する
'''

import os
from datetime import datetime
import PyPDF2

output_dir = "output"
pdf_path = "input/2021r03h_nw_pm1_qs.pdf" 

split_config = [(2, 7), (8, 13), (14, 18)]


# 入力ファイル名からタイムスタンプ付きディレクトリの作成
file_name = os.path.splitext(os.path.basename(pdf_path))[0]
file_name += f"_{datetime.now().strftime('%Y%m%d%H%M%S')}"
output_dir = os.path.join(output_dir, file_name)
os.makedirs(output_dir, exist_ok=True)


# PDFを分割
def split_pdf(input_pdf, output_folder, start_page, end_page):
    # 入力PDFファイルを読み込む
    with open(input_pdf, "rb") as file:
        pdf_reader = PyPDF2.PdfReader(file)
        
        # 指定されたページ範囲が正しいか確認
        if start_page < 1 or end_page > len(pdf_reader.pages) or start_page > end_page:
            print("ページ範囲が無効です。")
            return None
        
        # 保存フォルダが存在しない場合は作成
        os.makedirs(output_folder, exist_ok=True)
        
        # 指定したページ範囲を含むPDFファイルを作成
        pdf_writer = PyPDF2.PdfWriter()
        for page_num in range(start_page - 1, end_page):  # ページ番号は0から始まるので、start_page - 1に調整
            pdf_writer.add_page(pdf_reader.pages[page_num])
        
        # 分割後のファイル名を指定
        output_pdf = f"{output_folder}/pages_{start_page}_to_{end_page}.pdf"
        with open(output_pdf, "wb") as output_file:
            pdf_writer.write(output_file)
        
        print(f"ページ {start_page} から {end_page} までを保存しました: {output_pdf}")

        return output_pdf


# start_page = 2  # 開始ページ
# end_page = 7  # 終了ページ
# split_pdf_path = split_pdf(pdf_path, output_dir, start_page, end_page)

# PDFを問題ごとに分割
split_pdf_path_list = []
for i, (start_page, end_page) in enumerate(split_config):
    split_output_dir = os.path.join(output_dir, f"mon{i}")
    os.makedirs(split_output_dir, exist_ok=True)
    split_pdf_path = split_pdf(pdf_path, split_output_dir, start_page, end_page)
    split_pdf_path_list.append((split_output_dir, split_pdf_path))


