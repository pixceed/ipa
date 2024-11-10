'''
PDFから、図や表を抽出する
'''

import os
from docling_core.types.doc import ImageRefMode, PictureItem, TableItem
from docling.datamodel.base_models import FigureElement, InputFormat, Table
from docling.datamodel.pipeline_options import (
    PdfPipelineOptions,
    EasyOcrOptions,
    TableFormerMode,
)
from docling.document_converter import DocumentConverter, PdfFormatOption

IMAGE_RESOLUTION_SCALE = 2.0

input_pdf_path = "output/2021r03h_nw_pm1_qs_20241108151450/mon0/pages_2_to_7.pdf"
output_dir = "output/2021r03h_nw_pm1_qs_20241108151450/mon0"


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
conv_res = doc_converter.convert(input_pdf_path)

# ページ画像を保存
doc_filename = conv_res.input.file.stem
for page_no, page in conv_res.document.pages.items():
    page_no = page.page_no
    page_image_filename = os.path.join(output_dir, f"page-{page_no}.png")
    with open(page_image_filename, "wb") as fp:
        page.image.pil_image.save(fp, format="PNG")

# 図と表を保存
table_counter = 0
picture_counter = 0
for element, _level in conv_res.document.iterate_items():
    if isinstance(element, TableItem):
        table_counter += 1
        element_image_filename = \
            os.path.join(output_dir, f"table-{table_counter}.png")
        
        with open(element_image_filename, "wb") as fp:
            element.image.pil_image.save(fp, "PNG")

    if isinstance(element, PictureItem):
        picture_counter += 1
        element_image_filename = \
            os.path.join(output_dir, f"picture-{picture_counter}.png")
        with open(element_image_filename, "wb") as fp:
            element.image.pil_image.save(fp, "PNG")