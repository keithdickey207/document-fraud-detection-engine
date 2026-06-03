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
            ela_result, copy_move_result, output_dir
        )

        report_path = output_dir / f"{file_path.stem}_fraud_report_v2.json"
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
                x1, y1, x2, y2 = line[0]
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

    # ==================== UPGRADE 2: RADIAL FREQUENCY PROFILING ====================
    def _detect_moire_radial(self, image: np.ndarray) -> Dict[str, Any]:
        """
        Advanced Moire detection using 1D radial frequency profile + peak finding.
        Detects sharp halftone spikes that distinguish re-photographed prints.
        """
        result = {"score": 0.0, "indicators": [], "details": {}}

        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY).astype(np.float32)
        f = np.fft.fft2(gray)
        fshift = np.fft.fftshift(f)
        magnitude = np.abs(fshift)

        h, w = gray.shape
        cy, cx = h // 2, w // 2
        y, x = np.ogrid[:h, :w]
        r = np.sqrt((x - cx)**2 + (y - cy)**2).astype(int)

        max_r = min(cy, cx) - 5
        radial_profile = np.zeros(max_r)
        counts = np.zeros(max_r)

        for i in range(max_r):
            mask = (r == i)
            if np.any(mask):
                radial_profile[i] = np.mean(magnitude[mask])
                counts[i] = np.sum(mask)

        # Log scale for better dynamic range
        radial_profile = np.log(radial_profile + 1e-6)

        # Find significant peaks (halftone signatures)
        mean_energy = np.mean(radial_profile)
        peaks, properties = find_peaks(
            radial_profile,
            height=mean_energy * self.moire_peak_threshold,
            distance=8,
            prominence=0.8
        )

        num_peaks = len(peaks)
        peak_prominences = properties.get('prominences', np.array([]))

        result['details'] = {
            "num_halftone_peaks": int(num_peaks),
            "peak_radii": [int(p) for p in peaks[:5]],
            "max_prominence": float(np.max(peak_prominences)) if len(peak_prominences) > 0 else 0.0
        }

        if num_peaks >= 2:
            result['indicators'].append(f"Multiple halftone frequency spikes detected ({num_peaks} peaks)")
            result['score'] = min(55 + num_peaks * 12, 100)
        elif num_peaks == 1 and np.max(peak_prominences) > 2.5:
            result['indicators'].append("Strong single halftone peak (re-photographed document)")
            result['score'] = 65
        else:
            result['score'] = max(0, (num_peaks * 15) + (np.max(peak_prominences, initial=0) * 8))

        return result

    # ==================== UPGRADE 1: COPY-MOVE FORGERY DETECTION ====================
    def _detect_copy_move(self, image: np.ndarray, output_dir: Path) -> Dict[str, Any]:
        """
        Detects intra-image cloning using ORB + spatial filtering.
        Returns score + visualization of duplication lines.
        """
        result = {"score": 0.0, "matches_found": 0, "status": "NORMAL", "visualization_path": None}

        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        orb = cv2.ORB_create(nfeatures=4000)
        keypoints, descriptors = orb.detectAndCompute(gray, None)

        if descriptors is None or len(descriptors) < 15:
            return result

        bf = cv2.BFMatcher(cv2.NORM_HAMMING, crossCheck=False)
        matches = bf.knnMatch(descriptors, descriptors, k=3)

        valid_matches = []
        for match_set in matches:
            if len(match_set) < 3:
                continue
            m, n, o = match_set  # m = closest (often self), n = 2nd, o = 3rd

            # Lowe's ratio test (more robust than original)
            if n.distance < 0.72 * o.distance:
                pt1 = keypoints[m.queryIdx].pt
                pt2 = keypoints[n.trainIdx].pt  # use 2nd best to avoid self-match

                spatial_dist = np.hypot(pt1[0] - pt2[0], pt1[1] - pt2[1])
                if spatial_dist > self.copy_move_spatial_dist:
                    valid_matches.append((pt1, pt2))

        num_matches = len(valid_matches)
        result["matches_found"] = num_matches

        if num_matches >= self.copy_move_min_matches:
            result["score"] = min(100.0, float(num_matches * 6.5))
            result["status"] = "SUSPICIOUS_DUPLICATION"
            result["indicators"] = [f"Copy-Move forgery detected: {num_matches} duplicated regions"]

            # Generate visualization
            vis_path = output_dir / "copy_move_duplication_lines.png"
            self._visualize_copy_move(image, valid_matches, vis_path)
            result["visualization_path"] = str(vis_path)
        else:
            result["score"] = max(0, num_matches * 3)

        return result

    def _visualize_copy_move(self, image: np.ndarray, matches: List[Tuple], output_path: Path):
        """Draws red lines connecting duplicated regions."""
        vis = image.copy()
        for pt1, pt2 in matches:
            cv2.line(vis, (int(pt1[0]), int(pt1[1])), (int(pt2[0]), int(pt2[0])), (0, 0, 255), 2)
            cv2.circle(vis, (int(pt1[0]), int(pt1[1])), 5, (0, 255, 0), -1)
            cv2.circle(vis, (int(pt2[0]), int(pt2[0])), 5, (255, 0, 0), -1)
        cv2.imwrite(str(output_path), vis)

    # ==================== MODULE 4: ELA (enhanced) ====================
    def _compute_error_level_analysis(self, image: np.ndarray, output_dir: Path) -> Dict[str, Any]:
        result = {"score": 0.0, "indicators": [], "ela_stats": {}, "visualization_path": None}
        original = image.copy()
        encode_param = [int(cv2.IMWRITE_JPEG_QUALITY), self.ela_quality]
        _, encoded = cv2.imencode('.jpg', original, encode_param)
        compressed = cv2.imdecode(encoded, 1)
        ela_diff = cv2.absdiff(original, compressed)
        ela_scaled = cv2.multiply(ela_diff, np.array([self.ela_scale]*3, dtype=np.uint8))
        ela_scaled = np.clip(ela_scaled, 0, 255).astype(np.uint8)

        ela_gray = cv2.cvtColor(ela_scaled, cv2.COLOR_BGR2GRAY)
        std_diff = float(np.std(ela_gray))
        max_diff = int(np.max(ela_gray))

        result['ela_stats'] = {"std_error": round(std_diff, 2), "max_error": max_diff}

        if std_diff > 20 or max_diff > 160:
            result['indicators'].append(f"High ELA variance (std={std_diff:.1f})")
            result['score'] = min(55 + (std_diff / 1.8), 100)
        else:
            result['score'] = max(0, (std_diff - 8) * 2.5)

        ela_path = output_dir / "ela_analysis.png"
        cv2.imwrite(str(ela_path), ela_scaled)
        result['visualization_path'] = str(ela_path)
        return result

    # ==================== UPDATED ARBITRATION ====================
    def _arbitrate_and_score(self, metadata, layout, moire, ela, copy_move, output_dir):
        total = (
            metadata['score'] * self.weights['metadata'] +
            layout['score'] * self.weights['layout'] +
            moire['score'] * self.weights['moire_radial'] +
            ela['score'] * self.weights['pixel_ela'] +
            copy_move['score'] * self.weights['copy_move']
        )
        fraud_prob = min(max(total, 0), 100)

        if fraud_prob >= 75:
            risk = "HIGH - Likely Forged"
            rec = "Strong evidence of tampering. Recommend manual + secondary tools."
        elif fraud_prob >= 50:
            risk = "MEDIUM - Suspicious"
            rec = "Multiple indicators. Prioritize review of highlighted regions."
        elif fraud_prob >= 25:
            risk = "LOW - Minor Anomalies"
            rec = "Probably authentic. Verify any flagged areas."
        else:
            risk = "VERY LOW - Likely Authentic"
            rec = "No significant forgery signals detected."

        all_indicators = (
            metadata.get('indicators', []) +
            layout.get('indicators', []) +
            moire.get('indicators', []) +
            ela.get('indicators', []) +
            copy_move.get('indicators', [])
        )

        report = {
            "fraud_probability": round(fraud_prob, 1),
            "risk_level": risk,
            "recommendation": rec,
            "breakdown": {
                "metadata": round(metadata['score'], 1),
                "layout": round(layout['score'], 1),
                "moire_radial": round(moire['score'], 1),
                "copy_move": round(copy_move['score'], 1),
                "pixel_ela": round(ela['score'], 1)
            },
            "weights": self.weights,
            "all_indicators": all_indicators,
            "copy_move_details": {
                "matches_found": copy_move.get("matches_found", 0),
                "status": copy_move.get("status", "NORMAL")
            },
            "artifacts": {
                "ela": ela.get("visualization_path"),
                "copy_move_lines": copy_move.get("visualization_path"),
                "report": str(output_dir / "fraud_report_v2.json")
            }
        }

        self._generate_summary_plot_v2(report, output_dir)
        return report

    def _generate_summary_plot_v2(self, report, output_dir):
        try:
            cats = ['Metadata', 'Layout', 'Moire\n(Radial)', 'Copy-Move', 'ELA\n(Pixel)']
            vals = [
                report['breakdown']['metadata'],
                report['breakdown']['layout'],
                report['breakdown']['moire_radial'],
                report['breakdown']['copy_move'],
                report['breakdown']['pixel_ela']
            ]
            colors = ['#e74c3c' if v > 50 else '#f39c12' if v > 25 else '#27ae60' for v in vals]

            fig, ax = plt.subplots(figsize=(11, 5.5))
            bars = ax.bar(cats, vals, color=colors, edgecolor='black', linewidth=1.3)
            ax.set_ylabel('Anomaly Score (0-100)', fontsize=12)
            ax.set_title(f"v2 Fraud Analysis — {report['fraud_probability']}% | {report['risk_level']}", 
                         fontsize=13, fontweight='bold', pad=12)
            ax.set_ylim(0, 115)
            ax.axhline(y=50, color='#c0392b', linestyle='--', alpha=0.7, linewidth=1.5, label='Medium threshold')

            for bar, val in zip(bars, vals):
                ax.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 2.5, 
                        f'{val:.0f}', ha='center', va='bottom', fontsize=11, fontweight='bold')

            ax.legend(loc='upper right')
            plt.tight_layout()
            plt.savefig(output_dir / "fraud_breakdown_v2.png", dpi=160, bbox_inches='tight')
            plt.close()
        except Exception as e:
            print(f"[WARN] Plot error: {e}")


# ==================== CLI ====================
if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Document Fraud Detection Engine v2")
    parser.add_argument("input", help="Image or PDF path")
    parser.add_argument("--output", "-o", default="artifacts/forensics_v2_output")
    parser.add_argument("--weights", type=json.loads, default=None)
    args = parser.parse_args()

    detector = DocumentFraudDetectorV2(weights=args.weights)
    result = detector.analyze(args.input, output_dir=args.output)
    print("\n" + "="*65)
    print("v2 FINAL ASSESSMENT")
    print("="*65)
    print(json.dumps(result, indent=2, default=str))
