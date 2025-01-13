import os
import fitz  # PyMuPDF for PDF handling
import pandas as pd
import re
import pytesseract
from langdetect import detect, DetectorFactory
from collections import defaultdict
from PIL import Image
from datetime import datetime
import signal
from icecream import ic

# Configuration and Initialization
checkpoint_file = "checkpoint.xlsx"  # Temporary file for checkpointing

class DocAnalyzer:
    def __init__(self, input_folder=None, csv_file=None, output_dir=None, num_processes=4):
        self.input_folder = input_folder
        self.csv_file = csv_file
        self.output_dir = output_dir
        self.num_processes = num_processes
        self.checkpoint_file = checkpoint_file
        self.results = []

    # Text Extraction from PDF
    def extract_text_from_pdf(self, pdf_path):
        pdf_document = fitz.open(pdf_path)
        text_chunks = []
        is_scanned = False
        
        for page_num, page in enumerate(pdf_document):
            text = page.get_text("text")
            
            if not text:  # If no text, it's likely a scanned image
                is_scanned = True
                # Use OCR to extract text from scanned image
                pix = page.get_pixmap()
                img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
                text = pytesseract.image_to_string(img)
            
            text_cleaned = re.sub(r'[^\x00-\x7F]+', ' ', text)  # Clean non-ASCII characters
            text_chunks.append(text_cleaned)
        
        pdf_document.close()
        return text_chunks, is_scanned

    # Language Detection
    def detect_languages(self, text_chunks):
        language_counts = defaultdict(int)
        for text_chunk in text_chunks:
            try:
                detected_lang = detect(text_chunk)  # Detect language of the chunk
                language_counts[detected_lang] += 1
            except:
                continue
        
        total_chunks = len(text_chunks)
        language_percentages = {lang: (count / total_chunks) * 100 for lang, count in language_counts.items()}
        dominant_language = max(language_percentages, key=language_percentages.get) if language_percentages else None
        
        return dominant_language, language_percentages

    # PDF Analysis (analyze_pdf)
    def analyze_pdf(self, pdf_path):
        try:
            # Extract text and determine if it's scanned
            text_chunks, is_scanned = self.extract_text_from_pdf(pdf_path)
            
            # Detect languages and calculate percentages
            dominant_language, language_percentages = self.detect_languages(text_chunks)
            
            return {
                'Is Scanned': is_scanned,
                'Dominant Language': dominant_language,
                'Language Distribution': language_percentages
            }
        except FileNotFoundError as e:
            print(e)
        except Exception as e:
            print(f"An error occurred: {e}")
        return None

    # Batch PDF Analysis (analyze_pdfs)
    def analyze_pdfs(self):
        filenames_df = pd.read_csv(self.csv_file)
        pdf_infos = [(index, row['filename'], os.path.join(self.input_folder, f"{row['filename']}.pdf")) for index, row in filenames_df.iterrows()]

        for index, filename, pdf_path in pdf_infos:
            print(f"Processing Document {index + 1}: {pdf_path}")
            result = self.analyze_pdf(pdf_path)
            if result:
                print(f"Result for {filename}:")
                print(f"  Is Scanned: {result['Is Scanned']}")
                print(f"  Dominant Language: {result['Dominant Language']}")
                print(f"  Language Distribution: {result['Language Distribution']}")
                
                output_path = os.path.join(self.output_dir, f"{filename}_result.json")
                with open(output_path, 'w') as f:
                    f.write(str(result))

                self.results.append({
                    'Filename': filename,
                    'Document Number': index + 1,
                    'Dominant Language': result['Dominant Language'],
                    'Language Distribution': result['Language Distribution'],
                    'Is Scanned': result['Is Scanned']
                })
        
        if self.results:
            result_df = pd.DataFrame(self.results)
            result_df.to_excel(self.checkpoint_file, index=False)
            print(f"Results saved to {self.checkpoint_file}")
