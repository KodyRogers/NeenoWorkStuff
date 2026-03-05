import os
import cv2
import numpy as np
from pdf2image import convert_from_path
from PIL import Image

# ==============================
# SETTINGS
# ==============================
dpi = 300

def clean_pdf(input_pdf, output_pdf):
    # Threshold strength:
    # Increase toward 230 to remove more gray
    THRESH_VALUE = 210

    # ==============================
    # STEP 1: Convert PDF to images
    # ==============================

    print("Converting PDF to images...")
    pages = convert_from_path(input_pdf, dpi=dpi)

    processed_images = []

    for i, page in enumerate(pages):
        print(f"Processing page {i+1}...")

        # Convert PIL image to OpenCV format
        img = np.array(page)
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

        # ==============================
        # STEP 2: Slight blur (reduces speckle sensitivity)
        # ==============================
        gray = cv2.GaussianBlur(gray, (3,3), 0)

        # ==============================
        # STEP 3: Keep only strong blacks
        # ==============================
        BLACK_THRESHOLD = 120   # Lower = stricter (try 100–140)

        # Invert threshold so dark pixels become white (255)
        _, mask = cv2.threshold(
            gray,
            BLACK_THRESHOLD,
            255,
            cv2.THRESH_BINARY_INV
        )

        # Convert mask to pure black text on white background
        cleaned = 255 - mask

        # ==============================
        # STEP 4: Remove speckles
        # ==============================
        kernel = np.ones((2,2), np.uint8)
        cleaned = cv2.morphologyEx(mask, cv2.MORPH_OPEN, kernel)

        # Convert back to PIL
        final_img = Image.fromarray(cleaned)
        processed_images.append(final_img)

    # ==============================
    # STEP 5: Save back to PDF
    # ==============================

    print("Saving cleaned PDF...")
    processed_images[0].save(
        output_pdf,
        save_all=True,
        append_images=processed_images[1:]
    )

    print("Done.")
    print(f"Cleaned file saved as: {output_pdf}")
    
def main():
    
    for file in os.listdir(os.path.join(os.path.dirname(os.path.abspath(__file__)), "pdfs")):
        if file.endswith(".pdf"):
            print(f"Cleaning: {file}")
            input_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "pdfs", file)
            output_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "clean_pdfs", file)
            clean_pdf(input_path, output_path)
    
if __name__ == "__main__":
    main()