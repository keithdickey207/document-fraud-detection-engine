#!/usr/bin/env python3
"""
Simple Example Usage for Document Fraud Detection Engine v2

Run this script with any document image or PDF to see the full analysis.
"""

import sys
from document_fraud_detection_engine_v2 import DocumentFraudDetectorV2


def main():
    if len(sys.argv) < 2:
        print("Usage: python example_usage.py <path_to_document.jpg_or.pdf>")
        print("Example: python example_usage.py my_contract.pdf")
        sys.exit(1)

    file_path = sys.argv[1]

    print("\n" + "="*60)
    print("DOCUMENT FRAUD DETECTION - EXAMPLE RUN")
    print("="*60)

    detector = DocumentFraudDetectorV2()
    result = detector.analyze(file_path, output_dir="./forensics_report")

    print("\n" + "="*60)
    print("FINAL RESULT")
    print("="*60)
    print(f"Fraud Probability : {result['fraud_probability']}%")
    print(f"Risk Level        : {result['risk_level']}")
    print(f"Recommendation    : {result['recommendation']}")
    print("\nBreakdown:")
    for module, score in result['breakdown'].items():
        print(f"  {module:20} : {score:6.1f}")
    print("="*60)
    print("\nFull report + visualizations saved in: ./forensics_report/")


if __name__ == "__main__":
    main()