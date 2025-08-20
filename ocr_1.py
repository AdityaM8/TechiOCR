import os
import sys
from PIL import Image
import pytesseract



# Set the path to your installed Tesseract
pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'


import cv2
import numpy as np
import os
import pytesseract
from PIL import Image    #These import essential tools:
                         # os: For file/folder handling
                         # pytesseract: Python wrapper for the Tesseract OCR engine
                         # PIL.Image: To open and read images

# Optional: Set tesseract path manually
pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'

def run_ocr_on_folder(folder_path):
    if not os.path.isdir(folder_path):
        print("Invalid folder path.")
        return   
# Check if Folder Path is Valid

    output_combined = ""
#This will collect all OCR results into one big string to be saved at the end.

    for filename in os.listdir(folder_path):
        if filename.lower().endswith((".png", ".jpg", ".jpeg", ".tif", ".tiff")):
            try:
#Loop Over Files in the Folder

                image_path = os.path.join(folder_path, filename)
                text = pytesseract.image_to_string(Image.open(image_path))
#Process Each Image
#image_path: full path to the current image
#pytesseract.image_to_string(...): extracts text from the image

                # ✅ Preprocessing
                image = cv2.imread(image_path)
                gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
                thresh = cv2.threshold(gray, 150, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)[1]
            
            
            # ✅ OCR
                custom_config = r'--oem 3 --psm 6'
                text = pytesseract.image_to_string(thresh, config=custom_config)
            
            # (optional) print debug
                print(f"OCR result for {filename}:\n{text[:200]}\n{'-'*40}")
                print(f"Text length: {len(text)}")

                txt_path = os.path.splitext(image_path)[0] + ".txt"
                with open(txt_path, "w", encoding="utf-8") as f:
                    f.write(text)
# Save to a text file

                output_combined += f"\n--- {filename} ---\n{text}\n"
                print(f"Processed {filename}")
        
#Add Result to Combined Output

            except Exception as e:
                print(f"Failed to process {filename}: {e}")
#If anything fails (e.g. corrupted image), it prints the error but keeps processing the rest.

    # Save combined output
    with open(os.path.join(folder_path, "output_combined.txt"), "w", encoding="utf-8") as f:
        f.write(output_combined)

    print("✅ OCR completed for all images.")

# Example usage:
folder_path = input("Enter the path to the folder with images: ").strip('"')
run_ocr_on_folder(folder_path)
