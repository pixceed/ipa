import os
import PyPDF2


from docling.datamodel.base_models import FigureElement, InputFormat, Table
from docling.datamodel.pipeline_options import (
    PdfPipelineOptions,
    EasyOcrOptions,
    TableFormerMode,
)
from docling.document_converter import DocumentConverter, PdfFormatOption


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

def setup_pdf_converter():

    IMAGE_RESOLUTION_SCALE = 2.0

    # パイプラインの設定
    pipeline_options = PdfPipelineOptions()
    pipeline_options.do_ocr = False
    pipeline_options.do_table_structure = True
    pipeline_options.table_structure_options.do_cell_matching = True
    pipeline_options.table_structure_options.mode = TableFormerMode.ACCURATE
    pipeline_options.images_scale = IMAGE_RESOLUTION_SCALE
    pipeline_options.generate_page_images = True
    pipeline_options.generate_table_images = True
    pipeline_options.generate_picture_images = True

    # PDFを解析
    doc_converter = DocumentConverter(
        format_options={
            InputFormat.PDF: PdfFormatOption(pipeline_options=pipeline_options)
        }
    )

    return doc_converter