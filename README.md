# 🔍 Document Fraud Detection Engine v2

**Enterprise-grade, fully local-first document forensics system**

Detects advanced forgery vectors:
- Metadata & structural tampering
- Layout / physical surface anomalies
- **Radial-frequency halftone profiling** (re-photographed printed documents)
- Error Level Analysis (ELA) for digital edits
- **Copy-Move forgery detection** (cloned signatures, stamps, numbers, fields)

## Quick Start (Super Easy)

```bash
# 1. Clone the repo
git clone https://github.com/keithdickey207/document-fraud-detection-engine.git
cd document-fraud-detection-engine

# 2. Install dependencies
pip install -r requirements.txt

# 3. Run the example (no file needed - it creates a test document!)
python example_usage.py
```

That's it! The script will automatically create a sample tampered invoice and analyze it.

### Analyze your own document

```bash
python example_usage.py /path/to/suspicious_invoice.pdf
# Reports saved to ./forensics_report/
```

> **Penguin / ChromeOS:** Use a venv — `python3 -m venv .venv && .venv/bin/pip install -r requirements.txt`

Part of the **WQSH / Dickey.OS** sovereign stack — fully offline, no cloud APIs. Complements [dickey-sovereign-core](https://github.com/keithdickey207/dickey-sovereign-core) CTI and threat-intel pipelines for document verification workflows.

## Detection Modules

| Module | Method |
|--------|--------|
| Metadata | EXIF / structural tampering |
| Layout | Baseline tilt, edge anomalies |
| Moiré / Halftone | Radial-frequency profiling (re-photographed prints) |
| ELA | Error Level Analysis (digital edits) |
| Copy-Move | Cloned signatures, stamps, fields |

## What's a Fair Royalty? (My Recommendation)

For a specialized, production-ready forensic tool like this, a **fair and balanced royalty** is:

- **5% of gross revenue** directly attributable to this engine, **or**
- **$2,500 USD one-time flat fee** per commercial product or deployment

This rate is industry-standard for high-value IP while remaining attractive for adoption.

## Commercial Royalty Terms

### Free Use (No Royalty)
- Personal, hobby, or educational use
- Academic research and non-profit projects
- Open-source contributions and forks
- Internal non-revenue tools

### Commercial Use (Royalty Required)
If you use this engine (or any derivative) in any revenue-generating product, service, SaaS, or business process, you must pay a royalty **before** commercial deployment.

**Royalty Options** (choose one):
- **5% of attributable gross revenue** (ongoing)
- **$2,500 USD one-time flat fee** per product/deployment
- Custom negotiated rate

**Accepted Payment Methods**:
- **Cash App**: $KeithDickey7 (fastest & preferred)
- **Email**: keithdickey207@gmail.com (for invoices and alternative payment arrangements)

**How to Get Licensed & Pay**:
1. Contact the author **before** launching commercially
2. Describe your use case
3. Receive invoice + commercial license
4. Pay via Cash App ($KeithDickey7) or arrange via email

**Important**:
- This royalty applies to this engine + all forks and derivatives
- Non-payment for commercial use violates the license
- Rates may be updated with 30 days notice

## Author & Contact
**Keith Alan Dickey** ([@keithdickey207](https://github.com/keithdickey207))  
Waterville Software Development Services — Waterville, ME 04901

**Primary Payment**: Cash App $KeithDickey7
**Email**: keithdickey207@gmail.com

All commercial rights reserved.
