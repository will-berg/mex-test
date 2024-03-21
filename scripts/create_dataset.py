import sys
import os
from pathlib import Path
from typing import Optional, List, Union
import io
import pypdfium2
import logging
import json

# pip install nougat-ocr needed for this import
# from nougat.dataset.rasterize import rasterize_paper

docxs_path = Path("../documents/docxs")
pdfs_path = Path("../documents/pdfs")
images_path = Path("../documents/images")
markdown_path = Path("../documents/markdown")

# Create output directories if they don't exist
pdfs_path.mkdir(parents=True, exist_ok=True)
images_path.mkdir(parents=True, exist_ok=True)
markdown_path.mkdir(parents=True, exist_ok=True)

# Use libreoffice to convert all docx files to pdf
# Seems to convert better than Pandoc
def docx_to_pdf():
    for docx in docxs_path.iterdir():
        if docx.suffix == ".docx":
            os.system(f"libreoffice --headless --convert-to pdf {docx} --outdir {pdfs_path}")

# Use pandoc to convert all docx files to markdown
# The files generated here will have to be manually checked and corrected
def docx_to_markdown():
	docx_pages = docxs_path / "final"
    for docx in docxs_path.iterdir():
        if docx.suffix == ".docx":
			"""
			# The document folders approach:
            # Split the current docx file into multiple docx files for each page (documentname/pagenumber.docx)
			# Create a directory for the document where its pages will be saved as docx files
			doc_dir = docxs_path / docx.stem
			os.mkdir(doc_dir)

            # Use pandoc to convert each page to its own markdown file (save to path markdown_path/documentname/pagenumber.mmd)
			# This means that we will have pairs of markdown and image files for each page of all docx documents
			for doc in doc_dir.iterdir():
				if doc.suffix == ".docx":
					markdown = markdown_path / doc_dir / (doc.stem + ".mmd")
					os.system(f"pandoc -f docx -t markdown_mmd --markdown-headings=atx {doc} -o {markdown}")

			# The final folder approach: split the docx files in docxs_path into multiple docx files for each page, place them in docx_pages with name: documentname_pagenumber.docx
			split_docx(docx, docx_pages)
			for doc in docx_pages.iterdir():
				if doc.suffix == ".docx":
					markdown = markdown_path / doc.stem + ".mmd"
					os.system(f"pandoc -f docx -t markdown_mmd --markdown-headings=atx {doc} -o {markdown}")
			"""

			# If we don't split the docx file into multiple docx files
            markdown = markdown_path / (docx.stem + ".mmd")
            os.system(f"pandoc -f docx -t markdown_mmd --markdown-headings=atx {docx} -o {markdown}")

# Use nougat's rasterize_paper to convert all pdf files to png
def rasterize_paper(
    pdf: Union[Path, bytes],
    outpath: Optional[Path] = None,
    dpi: int = 96,
    return_pil=False,
    pages=None,
) -> Optional[List[io.BytesIO]]:
    """
    Rasterize a PDF file to PNG images.

    Args:
        pdf (Path): The path to the PDF file.
        outpath (Optional[Path], optional): The output directory. If None, the PIL images will be returned instead. Defaults to None.
        dpi (int, optional): The output DPI. Defaults to 96.
        return_pil (bool, optional): Whether to return the PIL images instead of writing them to disk. Defaults to False.
        pages (Optional[List[int]], optional): The pages to rasterize. If None, all pages will be rasterized. Defaults to None.

    Returns:
        Optional[List[io.BytesIO]]: The PIL images if `return_pil` is True, otherwise None.
    """
    pils = []
    if outpath is None:
        return_pil = True
    try:
        if isinstance(pdf, (str, Path)):
            pdf = pypdfium2.PdfDocument(pdf)
        if pages is None:
            pages = range(len(pdf))
        renderer = pdf.render(
            pypdfium2.PdfBitmap.to_pil,
            page_indices=pages,
            scale=dpi / 72,
        )
        for i, image in zip(pages, renderer):
            if return_pil:
                page_bytes = io.BytesIO()
                image.save(page_bytes, "bmp")
                pils.append(page_bytes)
            else:
                image.save((outpath / ("%02d.png" % (i + 1))), "png")
    except Exception as e:
        logging.error(e)
    if return_pil:
        return pils

def pdf_to_png():
    for pdf in pdfs_path.iterdir():
        if pdf.suffix == ".pdf":
            outpath = images_path / pdf.stem
        if not outpath.exists():
            outpath.mkdir(parents=True, exist_ok=True)
            rasterize_paper(pdf=pdf, outpath=outpath, dpi=96)

def create_jsonl():
    # Combine the image paths and the corresponding markdown content into a jsonl file
    # (run after .mmd and .png files are created)
    # with the format {"image": "path/to/image.png", "markdown": "markdown content of the page", "meta": "[]"}
    # and save it in the output directory
	# Assumes the folder structure
    with open("../documents/dataset.jsonl", "w") as f:
        for image_folder, markdown_folder in zip(images_path.iterdir(), markdown_path.iterdir()):
            images = sorted(image_folder.iterdir())
            markdowns = sorted(markdown_folder.iterdir())
            for image, markdown in zip(images, markdowns):
                data_sample = {}
                md_path = Path(markdown)
                data_sample["image"] = f"{images_path}/{image_folder.name}/{image.name}"
                data_sample["markdown"] = md_path.read_text(encoding="utf8").strip()
                data_sample["meta"] = "[]"
                f.write(json.dumps(data_sample, ensure_ascii=False) + "\n")


if __name__ == "__main__":
    print("Converting docx files to pdf...")
    # docx_to_pdf()
    print("Converting docx files to markdown...")
    # docx_to_markdown()
    print("Converting pdf files to png...")
    # pdf_to_png()
	print("Creating jsonl file...")
    create_jsonl()
