# app/utils/image.py
import easyocr
from pathlib import Path

# Initialize EasyOCR reader (supports English by default)
reader = easyocr.Reader(['en'])

def extract_text_from_image(image_path: str) -> str:
    try:
        # EasyOCR can handle most image formats natively
        results = reader.readtext(image_path)
        
        # Extract text from results
        extracted_text = []
        for (bbox, text, confidence) in results:
            if confidence > 0.5:  # Filter low-confidence results
                extracted_text.append(text)
        
        combined_text = ' '.join(extracted_text).strip()
        
        # Check if meaningful text was found
        if len(combined_text) < 10 or not any(c.isalpha() for c in combined_text):
            return "[Image contains no readable text - may be screenshot or purely visual content]"
        
        return combined_text
        
    except Exception as e:
        print(f"Error extracting text from image: {e}")
        return "[Error during OCR processing]"