#!/usr/bin/env python3
"""
Document Fraud Detection Engine v2 - Enterprise Grade
Upgraded with:
- Copy-Move Forgery Detection (ORB + RANSAC-style spatial filtering)
- Radial Frequency Profiling for robust Moire/Halftone detection
- Updated 5-vector arbitration matrix
- Enhanced visualizations for duplication lines
"""

import os
import json
import tempfile
from pathlib import Path
from typing import Dict, Tuple, Optional, List, Any

import cv2
import numpy as np
from PIL import Image, ExifTags
from pypdf import PdfReader
from pdf2image import convert_from_path
import matplotlib.pyplot as plt
from scipy.signal import find_peaks
import warnings
warnings.filterwarnings('ignore')


class DocumentFraudDetectorV2:
    """
    Enterprise-grade document forensics engine.
    Now detects advanced evasion vectors: intra-image cloning and halftone moiré.
    """

    def __init__(self, 
                 weights: Optional[Dict[str, float]] = None,
                 ela_quality: int = 90,
                 ela_scale: int = 30,
                 moire_peak_threshold: float = 1.8,
                 copy_move_min_matches: int = 8,
                 copy_move_spatial_dist: int = 60):
        self.weights = weights or {
            "metadata": 0.15,
            "layout": 0.15,
            "moire_radial": 0.15,
            "copy_move": 0.25,
            "pixel_ela": 0.30
        }
        self.ela_quality = ela_quality
        self.ela_scale = ela_scale
        self.moire_peak_threshold = moire_peak_threshold
        self.copy_move_min_matches = copy_move_min_matches
        self.copy_move_spatial_dist = copy_move_spatial_dist
        self.temp_dir = Path(tempfile.mkdtemp(prefix="doc_forensics_v2_"))

    def _is_pdf(self, file_path: str) -> bool:
        return str(file_path).lower().endswith('.pdf')

    def analyze(self, file_path: str, output_dir: Optional[str] = None) -> Dict[str, Any]:
        file_path = Path(file_path)
        if not file_path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")

        output_dir = Path(output_dir) if output_dir else self.temp_dir / "output"
        output_dir.mkdir(parents=True, exist_ok=True)

        print(f"[INFO] Analyzing v2: {file_path.name}")

        # Compute stem early for consistent artifact naming (fixes report path bug)
        stem = file_path.stem

        # Metadata
        metadata_result = self._analyze_metadata(file_path)

        # Image prep
        if self._is_pdf(file_path):
            images = convert_from_path(str(file_path), first_page=1, last_page=1, dpi=200)
            pil_image = images[0]
            image = cv2.cvtColor(np.array(pil_image), cv2.COLOR_RGB2BGR)
        else:
            image = cv2.imread(str(file_path))
            if image is None:
                raise ValueError("Could not load image")

        # Layout
        layout_result = self._analyze_layout_anomalies(image)

        # Upgraded Moire (Radial Profiling)
        moire_result = self._detect_moire_radial(image)

        # ELA
        ela_result = self._compute_error_level_analysis(image, output_dir)

        # NEW: Copy-Move Forgery
        copy_move_result = self._detect_copy_move(image, output_dir)

        # Arbitration
        final_report = self._arbitrate_and_score(
            metadata_result, layout_result, moire_result, 
            ela_result, copy_move_result, output_dir, stem
        )

        report_path = output_dir / f"{stem}_fraud_report_v2.json"
        with open(report_path, 'w') as f:
            json.dump(final_report, f, indent=2, default=str)

        print(f"[INFO] v2 Report saved: {report_path}")
        print(f"[RESULT] Fraud Probability: {final_report['fraud_probability']:.1f}% | Risk: {final_report['risk_level']}")

        return final_report

    # ==================== MODULE 1: METADATA (unchanged) ====================
    def _analyze_metadata(self, file_path: Path) -> Dict[str, Any]:
        result = {"score": 0.0, "indicators": [], "metadata": {}}
        if self._is_pdf(file_path):
            try:
                reader = PdfReader(str(file_path))
                meta = reader.metadata or {}
                result['metadata'] = {k: str(v) for k, v in meta.items()}
                producer = str(meta.get('/Producer', '')).lower()
                if any(s in producer for s in ['photoshop', 'acrobat', 'illustrator']):
                    result['indicators'].append(f"Suspicious producer: {producer}")
                    result['score'] += 40
                for page in reader.pages:
                    if '/Annots' in page:
                        result['indicators'].append("Contains annotations/form fields")
                        result['score'] += 25
                        break
            except Exception as e:
                result['indicators'].append(f"PDF error: {e}")
                result['score'] += 10
        else:
            try:
                with Image.open(file_path) as img:
                    exif = img.getexif()
                    if exif:
                        exif_data = {ExifTags.TAGS.get(k, k): str(v)[:80] for k, v in exif.items()}
                        result['metadata'] = exif_data
                        if any(s in str(exif_data.get('Software', '')).lower() for s in ['photoshop', 'gimp']):
                            result['indicators'].append("Editing software in EXIF")
                            result['score'] += 45
                    else:
                        result['indicators'].append("No EXIF metadata")
                        result['score'] += 25
            except Exception:
                pass
        result['score'] = min(result['score'], 100)
        return result

    # ==================== MODULE 2: LAYOUT (unchanged) ====================
    def _analyze_layout_anomalies(self, image: np.ndarray) -> Dict[str, Any]:
        result = {"score": 0.0, "indicators": [], "details": {}}
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        h, w = gray.shape
        edges = cv2.Canny(gray, 50, 150)
        lines = cv2.HoughLinesP(edges, 1, np.pi/180, 80, minLineLength=w*0.25, maxLineGap=15)
        angles = []
        if lines is not None:
            for line in lines:
                coords = np.asarray(line).reshape(-1)
                x1, y1, x2, y2 = coords[:4]
                angle = np.arctan2(y2-y1, x2-x1) * 180 / np.pi
                if abs(angle) < 8:
                    angles.append(angle)
        if angles:
            std = np.std(angles)
            result['details']['baseline_std'] = round(std, 2)
            if std > 1.8:
                result['indicators'].append(f"Baseline tilt variation (std={std:.2f}°)")
                result['score'] += 40
        result['score'] = min(result['score'], 100)
        return result

    # ... rest of file unchanged - WAIT I can't truncate with ...
