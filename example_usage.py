#!/usr/bin/env python3
"""
Simple Example Usage for Document Fraud Detection Engine v2

This script now automatically creates a test document if you don't provide one
and can generate a professional PDF report.
"""

import sys
import os
from PIL import Image, ImageDraw, ImageFont
from document_fraud_detection_engine_v2 import DocumentFraudDetectorV2
from generate_pdf_report import create_pdf_report


def create_test_document():
    """Creates a simple test document with a deliberate edit (tampered amount)."""
    img = Image.new('RGB', (900, 650), color='white')
    draw = ImageDraw.Draw(img)
    
    try:
        font_large = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 32)
        font_normal = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 24)
    except:
        font_large = ImageFont.load_default()
        font_normal = ImageFont.load_default()

    draw.text((50, 40), "OFFICIAL INVOICE", fill='black', font=font_large)
    draw.text((50, 120), "Customer: John Smith", fill='black', font=font_normal)
    draw.text((50, 170), "Invoice #: INV-2026-0847", fill='black', font=font_normal)
    draw.text((50, 220), "Original Amount: $1,234.56", fill='black', font=font_normal)
    
    # This is the tampered part (simulates fraud)
    draw.rectangle([50, 260, 420, 310], fill='white')
    draw.text((50, 270), "Amount Due: $9,999.99", fill='red', font=font_normal)
    
    draw.text((50, 380), "Thank you for your business.", fill='black', font=font_normal)
    
    test_path = "test_invoice_tampered.png"
    img.save(test_path)
    print(f"\n[INFO] Created test document: {test_path}")
    return test_path


def main():
    if len(sys.argv) > 1:
        file_path = sys.argv[1]
        if not os.path.exists(file_path):
            print(f"[ERROR] File not found: {file_path}")
            print("Creating a test document instead...")
            file_path = create_test_document()
    else:
        print("[INFO] No file provided. Creating a test document with deliberate tampering...")
        file_path = create_test_document()

    print("\n" + "="*65)
    print("DOCUMENT FRAUD DETECTION - EXAMPLE RUN")
    print("="*65)

    detector = DocumentFraudDetectorV2()
    result = detector.analyze(file_path, output_dir="./forensics_report")

    print("\n" + "="*65)
    print("FINAL RESULT")
    print("="*65)
    print(f"Fraud Probability : {result['fraud_probability']}%")
    print(f"Risk Level        : {result['risk_level']}")
    print(f"Recommendation    : {result['recommendation']}")
    print("\nBreakdown:")
    for module, score in result['breakdown'].items():
        print(f"  {module:22} : {score:6.1f}")
    print("="*65)

    # Generate nice PDF report
    report_json = f"./forensics_report/{Path(file_path).stem}_fraud_report_v2.json"
    if os.path.exists(report_json):
        create_pdf_report(report_json)

    print("\nFull report + visualizations + PDF saved in: ./forensics_report/")


if __name__ == "__main__":
    from pathlib import Path
    main()