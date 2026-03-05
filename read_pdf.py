import pdfplumber
import pytesseract
from pdf2image import convert_from_path
import os

from PIL import Image
import cv2
import numpy as np

def extract_text_from_pdf(pdf_path):
    text = ""

    # Try normal extraction first
    with pdfplumber.open(pdf_path) as pdf:
        for page in pdf.pages:
            page_text = page.extract_text()
            if page_text:
                text += page_text + "\n"

    # If empty, use OCR
    if len(text.strip()) < 50:
        print("Using OCR...")
        images = convert_from_path(pdf_path)
        for img in images:
            text += pytesseract.image_to_string(img)

    return text

def main():
    current_dir = os.path.dirname(os.path.abspath(__file__))
    
    pdf_folder = os.path.join(current_dir, "clean_pdfs")
    output_folder = os.path.join(current_dir, "cleaned_texts")

    os.makedirs(output_folder, exist_ok=True)

    for filename in os.listdir(pdf_folder):
        if filename.endswith(".pdf"):
            pdf_path = os.path.join(pdf_folder, filename)
            

            output_path = os.path.join(output_folder, f"{os.path.splitext(filename)[0]}.txt")
            if os.path.exists(output_path):
                print(f"Text already extracted for: {filename}")
                continue
            else:
                text = extract_text_from_pdf(pdf_path)
                print(f"Extracting text from: {filename}")
                with open(output_path, "w", encoding="utf-8") as f:
                    f.write(text)

            print(f"Extracted text saved to: {output_path}")
            
if __name__ == "__main__":
    main()