\# Colorization Evaluation Pipeline



> A production-quality, modular Python pipeline for benchmarking AI image-colorization models against ground-truth colour images using six widely-accepted image-quality metrics.



\*\*Built for\*\*: Bachelor Thesis — Comparative Evaluation of AI Image Colorization Models (Zhang CNN, DeOldify, FLUX)



\---



\## Table of Contents



1\. \[Overview](#1-overview)

2\. \[Metrics](#2-metrics)

3\. \[Project Structure](#3-project-structure)

4\. \[Installation](#4-installation)

5\. \[Input Data Format](#5-input-data-format)

6\. \[Usage](#6-usage)

7\. \[Output Files](#7-output-files)

8\. \[How It Works](#8-how-it-works)

9\. \[Error Handling](#9-error-handling)

10\. \[Reproducibility Notes](#10-reproducibility-notes)

11\. \[Troubleshooting](#11-troubleshooting)

12\. \[Citations](#12-citations)

13\. \[License](#13-license)



\---



\## 1. Overview



This project quantitatively compares three AI-based image colorization models — \*\*Zhang CNN\*\*, \*\*DeOldify\*\*, and \*\*FLUX\*\* — against original colour ground-truth images. For every model output it computes six image-quality metrics covering pixel-level, structural, perceptual, and colour-fidelity aspects, then exports the results as CSV / Excel files and generates comparative plots.



\### Key features



\- \*\*Fully automatic\*\* — no filenames hardcoded; images are detected by keyword matching.

\- \*\*Modular\*\* — every metric is a self-contained module; every utility is reusable.

\- \*\*Robust\*\* — single-image or single-metric failures never abort the whole run.

\- \*\*Research-grade\*\* — uses only official, peer-reviewed implementations of every metric.

\- \*\*Reproducible\*\* — fixed parameters, deterministic SSIM/MS-SSIM, cached LPIPS weights.



\---



\## 2. Metrics



| # | Metric    | Library            | Range / Unit            | Direction | What it measures |

|---|-----------|--------------------|-------------------------|-----------|------------------|

| 1 | PSNR      | scikit-image       | dB (≥ 0, ∞ = identical) | higher ↑  | Pixel-level error |

| 2 | SSIM      | scikit-image       | \[-1, 1]                 | higher ↑  | Structural similarity |

| 3 | MS-SSIM   | pytorch-msssim     | \[0, 1]                  | higher ↑  | Multi-scale structural similarity |

| 4 | LPIPS     | lpips (AlexNet)    | \[0, ∞)                  | lower ↓   | Learned perceptual distance |

| 5 | FSIM      | piq                | \[0, 1]                  | higher ↑  | Feature similarity (phase + gradient) |

| 6 | Delta E   | colour-science     | CIEDE2000, ≥ 0          | lower ↓   | Perceptual colour difference |



Together these six metrics cover every dimension a thesis reviewer would expect:



\- \*\*Pixel fidelity\*\* → PSNR

\- \*\*Structural fidelity\*\* → SSIM, MS-SSIM, FSIM

\- \*\*Perceptual fidelity\*\* → LPIPS

\- \*\*Colour fidelity\*\* → Delta E (CIEDE2000)



\---



\## 3. Project Structure



```

colorization\_eval/

├── Measurement.py              # Single entry point — orchestrates the whole pipeline

├── requirements.txt            # Pinned dependencies

├── README.md                   # This file

│

├── metrics/                    # One module per metric

│   ├── \_\_init\_\_.py

│   ├── psnr.py                 # PSNR  (scikit-image)

│   ├── ssim.py                 # SSIM  (scikit-image, Gaussian-weighted Wang 2004)

│   ├── msssim.py               # MS-SSIM (pytorch-msssim, 5 levels, 11×11 window)

│   ├── lpips\_metric.py         # LPIPS (AlexNet backbone, cached singleton)

│   ├── fsim.py                 # FSIM (piq)

│   └── deltaE.py               # Delta E CIEDE2000 (colour-science, mean over pixels)

│

├── utils/                      # Cross-cutting helpers

│   ├── \_\_init\_\_.py

│   ├── logger.py               # Rotating-file + console logger shared by all modules

│   ├── image\_loader.py         # WEBP/JPG/PNG loading, RGB conversion, aspect-preserving resize

│   ├── file\_detector.py        # Keyword-based role detection (original/grayscale/zhang/...)

│   └── exporter.py             # CSV / XLSX export + matplotlib plots

│

├── logs/                       # Auto-created on first run

│   └── pipeline.log            # Full debug trail with tracebacks

│

├── results/                    # Auto-created on every run

│   ├── results.csv             # Per-image metrics

│   ├── results.xlsx

│   ├── summary.csv             # Per-model mean of every metric

│   ├── summary.xlsx

│   └── plots/

│       ├── boxplots.png            # Distribution of every metric per model

│       ├── bar\_means.png           # Mean of every metric per model

│       ├── ranking.png             # Per-metric rank heatmap (1 = best)

│       ├── ranking.csv             # Ranking table with average rank

│       └── correlation\_matrix.png  # Pearson correlation between metrics

│

└── Test Results/               # INPUT — provided by the user

&#x20;   ├── Autochrome by an unknown artist(1913)/

&#x20;   │   ├── image-original.jpg

&#x20;   │   ├── image-grayscale.jpg

&#x20;   │   ├── image-zhang.webp

&#x20;   │   ├── image-deoldify.webp

&#x20;   │   └── image-flux.png

&#x20;   ├── Lavender field/

&#x20;   │   └── ...

&#x20;   └── ...

```



\---



\## 4. Installation



\### 4.1 Requirements



\- \*\*Python 3.11 or newer\*\* (tested on 3.12)

\- \*\*pip\*\* ≥ 21

\- Optional: NVIDIA GPU + CUDA for faster LPIPS/MS-SSIM/FSIM (CPU works fine)



\### 4.2 Steps



```bash

\# 1) (Recommended) Create and activate a virtual environment

python -m venv .venv



\# Linux / macOS

source .venv/bin/activate



\# Windows (PowerShell)

.venv\\Scripts\\Activate.ps1



\# 2) Install dependencies

pip install -r requirements.txt

```



\### 4.3 GPU users (optional, faster)



Install the PyTorch build that matches your CUDA version \*\*before\*\* running `pip install -r requirements.txt`:



```bash

\# Example: CUDA 12.1

pip install torch torchvision --index-url https://download.pytorch.org/whl/cu121

```



The pipeline auto-detects CUDA and falls back to CPU if unavailable.



\### 4.4 Verify



```bash

python -c "import numpy, pandas, cv2, PIL, skimage, matplotlib, openpyxl, torch, torchvision, lpips, pytorch\_msssim, piq, colour; print('All imports OK')"

```



Expected output: `All imports OK`



\---



\## 5. Input Data Format



Place your test folders under `Test Results/` next to `Measurement.py`. Each folder must contain at least:



| File                  | Role                          | Required? |

|-----------------------|-------------------------------|-----------|

| `image-original.\*`    | Ground-truth colour image     | ✅ Yes    |

| `image-grayscale.\*`   | Grayscale version             | ❌ Optional (never evaluated) |

| `image-zhang.\*`       | Zhang CNN output              | ✅ At least one model output |

| `image-deoldify.\*`    | DeOldify output               | ✅        |

| `image-flux.\*`        | FLUX output                   | ✅        |



\### Filename detection rules



The detector matches on \*\*lower-cased filename substrings\*\* (no hardcoding). Any of the following naming styles work:



```

image-original.jpg

mosque\_original.png

Original\_GT.jpeg

img-zhang-out.webp

deoldify\_v3.png

flux\_result.png

```



\### Supported image formats



`.jpg`, `.jpeg`, `.png`, `.webp`



\### Size handling



If a generated image has a different resolution than the original, the pipeline \*\*centre-crops it to the target aspect ratio and then resizes\*\* it to the exact target resolution. This guarantees that all pixel-wise metrics are computed on aligned arrays without stretching.



\---



\## 6. Usage



From the project root (the folder containing `Measurement.py`):



```bash

python Measurement.py

```



That's it — no command-line arguments, no configuration files.



\### Expected console output (abridged)



```

========================================================================

Colorization Evaluation Pipeline

========================================================================

Device: CPU

Test results directory: .../Test Results

Output directory:       .../Test Results/results

\------------------------------------------------------------------------

Discovered 6 test folder(s).

\------------------------------------------------------------------------

Processing folder 1/6: Autochrome by an unknown artist(1913)

&#x20;   Evaluating Zhang ...

&#x20;   Evaluating DeOldify ...

&#x20;   Evaluating FLUX ...

Processing folder 2/6: Autochrome by Mervyn O'Gorman (1913)

&#x20;   ...

Processing folder 6/6: thuringia in germany

&#x20;   Evaluating Zhang ...

&#x20;   Evaluating DeOldify ...

&#x20;   Evaluating FLUX ...

Saved per-image results → .../results/results.csv

Saved per-image results → .../results/results.xlsx

Saved per-model summary   → .../results/summary.csv

Saved per-model summary   → .../results/summary.xlsx

Saved boxplots             → .../results/plots/boxplots.png

Saved bar chart            → .../results/plots/bar\_means.png

Saved ranking table        → .../results/plots/ranking.csv

Saved ranking heatmap      → .../results/plots/ranking.png

Saved correlation matrix   → .../results/plots/correlation\_matrix.png

\------------------------------------------------------------------------

Finished.

Number of images:           6

Number of evaluated models: 18

Execution time:             62.50 seconds

Output folder:              .../Test Results/results

\------------------------------------------------------------------------

Per-model summary:

&#x20; DeOldify   PSNR= 20.62  SSIM=0.8492  MS-SSIM=0.8760  LPIPS=0.3193  FSIM=0.9536  ΔE= 13.20

&#x20; FLUX       PSNR= 13.10  SSIM=0.4113  MS-SSIM=0.5921  LPIPS=0.5699  FSIM=0.7934  ΔE= 24.55

&#x20; Zhang      PSNR= 20.75  SSIM=0.8404  MS-SSIM=0.8665  LPIPS=0.3507  FSIM=0.9577  ΔE= 13.41

========================================================================

```



\---



\## 7. Output Files



All outputs are written under `results/` next to `Measurement.py`.



\### 7.1 `results.csv` / `results.xlsx`



One row per (image, model) pair — the raw measurements.



| Image Name                              | Model    | PSNR  | SSIM  | MS-SSIM | LPIPS | FSIM  | DeltaE |

|-----------------------------------------|----------|-------|-------|---------|-------|-------|--------|

| Autochrome by an unknown artist(1913)   | Zhang    | ...   | ...   | ...     | ...   | ...   | ...    |

| Autochrome by an unknown artist(1913)   | DeOldify | ...   | ...   | ...     | ...   | ...   | ...    |

| Autochrome by an unknown artist(1913)   | FLUX     | ...   | ...   | ...     | ...   | ...   | ...    |

| ...                                     | ...      | ...   | ...   | ...     | ...   | ...   | ...    |



\### 7.2 `summary.csv` / `summary.xlsx`



One row per model with the \*\*mean\*\* of every metric — the table you'll put in your thesis results section.



| Model    | Mean PSNR | Mean SSIM | Mean MS-SSIM | Mean LPIPS | Mean FSIM | Mean DeltaE |

|----------|-----------|-----------|--------------|------------|-----------|-------------|

| DeOldify | 20.62     | 0.8492    | 0.8760       | 0.3193     | 0.9536    | 13.20       |

| FLUX     | 13.10     | 0.4113    | 0.5921       | 0.5699     | 0.7934    | 24.55       |

| Zhang    | 20.75     | 0.8404    | 0.8665       | 0.3507     | 0.9577    | 13.41       |



\### 7.3 Plots (`results/plots/`)



| File                      | Description |

|---------------------------|-------------|

| `boxplots.png`            | Boxplot of every metric, three boxes per chart (one per model). Shows distribution + outliers. |

| `bar\_means.png`           | Bar chart of mean values per metric. Good for quick visual comparison. |

| `ranking.png`             | Heatmap of per-metric ranks (1 = best). The "Avg Rank" column decides the overall winner. |

| `ranking.csv`             | Same data as the heatmap, in CSV form for inclusion in tables. |

| `correlation\_matrix.png`  | Pearson correlation between metrics across all (image, model) samples. Useful to verify metrics agree. |



\### 7.4 `logs/pipeline.log`



Full rotating log file with timestamps and tracebacks. Open this if a reviewer asks "did you skip any image?" or "why is this metric NaN?".



\---



\## 8. How It Works



\### 8.1 Pipeline flow



```

discover\_test\_folders()

&#x20;       │

&#x20;       ▼

For each folder:

&#x20;   detect\_files()              ← keyword-based role detection

&#x20;       │

&#x20;       ▼

&#x20;   load\_image(original)

&#x20;       │

&#x20;       ▼

&#x20;   For each model in (Zhang, DeOldify, FLUX):

&#x20;       load\_image(model\_output)

&#x20;       resize\_if\_needed()      ← aspect-ratio-preserving centre crop + resize

&#x20;       calculate\_psnr()

&#x20;       calculate\_ssim()

&#x20;       calculate\_msssim()

&#x20;       calculate\_lpips()       ← cached AlexNet model

&#x20;       calculate\_fsim()

&#x20;       calculate\_deltaE()      ← sRGB → XYZ → Lab → CIEDE2000

&#x20;       │

&#x20;       ▼

&#x20;   Append row to results list

&#x20;       │

&#x20;       ▼

export\_results()    → results.csv / results.xlsx

export\_summary()    → summary.csv / summary.xlsx

generate\_plots()    → results/plots/\*.png

```



\### 8.2 Image normalisation per metric



Different metrics expect different tensor ranges. The pipeline handles this automatically in `utils/image\_loader.to\_tensor()`:



| Metric  | Input format                  | Value range |

|---------|-------------------------------|-------------|

| PSNR    | NumPy uint8 HWC               | \[0, 255]    |

| SSIM    | NumPy uint8 HWC               | \[0, 255]    |

| Delta E | NumPy uint8 HWC → float Lab   | \[0, 100] L  |

| MS-SSIM | PyTorch NCHW float            | \[0, 1]      |

| FSIM    | PyTorch NCHW float            | \[0, 1]      |

| LPIPS   | PyTorch NCHW float            | \[-1, 1]     |



\### 8.3 LPIPS model caching



The AlexNet-based LPIPS model is created \*\*once\*\* and reused across all evaluations via `@lru\_cache` on `get\_lpips\_model()`. On the first call it downloads \~250 MB of pretrained weights to `\~/.cache/torch/hub/`. Subsequent runs reuse the cached weights.



\---



\## 9. Error Handling



The pipeline is designed so that \*\*no single failure can abort the whole run\*\*.



| Failure mode                       | Behaviour |

|------------------------------------|-----------|

| `Test Results/` does not exist     | Log error, exit with code 1 |

| Folder missing original image      | Skip folder, log error |

| Folder missing one model output    | Skip that model, log warning |

| Image file cannot be opened        | Skip that model, log error + traceback |

| Metric raises an exception         | Store `NaN` for that metric, log error + traceback, continue |

| Unsupported file extension         | Silently ignored (debug-logged) |

| Duplicate role in same folder      | Keep first, warn about second |

| Plot generation fails              | Log error, continue with remaining plots |



All errors are written to both the console and `logs/pipeline.log` with full tracebacks at `DEBUG` level.



\---



\## 10. Reproducibility Notes



These are the deliberate implementation choices that affect the metric values. Document them in your thesis methodology section.



| Metric    | Choice                                                                                       | Reference |

|-----------|----------------------------------------------------------------------------------------------|-----------|

| PSNR      | `data\_range=255` (8-bit)                                                                     | Huynh-Thu \& Ghanbari (2008) |

| SSIM      | `gaussian\_weights=True`, `sigma=1.5`, `use\_sample\_covariance=False`, `channel\_axis=2`       | Wang et al. (2004) |

| MS-SSIM   | 5 levels, 11×11 Gaussian window, weights from the original paper                            | Wang et al. (2003) |

| LPIPS     | AlexNet backbone (matches Zhang et al. 2018 recommended speed/accuracy default)              | Zhang et al. (2018) |

| FSIM      | RGB input, Y-channel phase congruency, default piq parameters                                | Zhang et al. (2011) |

| Delta E   | CIEDE2000 formula, mean over all pixels                                                      | Sharma et al. (2005), ISO/CIE 11664-6:2014 |

| Resize    | Centre-crop to target aspect ratio → `cv2.INTER\_AREA` (downscale) or `cv2.INTER\_LINEAR` (upscale) | OpenCV docs |



\### Switching LPIPS backbone



If your supervisor asks for VGG instead of AlexNet, edit one line in `metrics/lpips\_metric.py`:



```python

\_DEFAULT\_NETWORK: NetworkName = "vgg"   # was "alex"

```



\---



\## 11. Troubleshooting



\### 11.1 `pip install` shows a numpy conflict



```

ERROR: opencv-python-headless 4.12.0.88 requires numpy<2.3.0, ...

```



This is a benign warning about a duplicate OpenCV variant on your system. Fix:



```bash

pip uninstall opencv-python-headless -y

pip install "numpy>=1.24,<2.3"

```



\### 11.2 LPIPS download fails (offline machine)



Pre-download the AlexNet weights and place them at:



```

\~/.cache/torch/hub/checkpoints/alexnet-owt-7be5be79.pth        # Linux / macOS

C:\\Users\\<you>\\.cache\\torch\\hub\\checkpoints\\alexnet-owt-7be5be79.pth   # Windows

```



Download URL: <https://download.pytorch.org/models/alexnet-owt-7be5be79.pth>



\### 11.3 `UserWarning: The parameter 'pretrained' is deprecated`



Harmless warning from the `lpips` library using an older torchvision API. Does not affect results.



\### 11.4 Slow on CPU



Expected \~3 s per (image, model) pair on CPU. For 6 images × 3 models that's \~55–65 s. To speed up:



\- Install PyTorch with CUDA support (see \[Installation](#43-gpu-users-optional-faster)).

\- Reduce LPIPS backbone from `alex` to `squeeze`.



\### 11.5 MS-SSIM warning about image size



```

Image is smaller than 161px on the shortest side (NxN); MS-SSIM may be inaccurate.

```



MS-SSIM needs at least 161 px on the shortest side for 5-level downsampling. Either upsample your images before evaluation or report the metric with a caveat in your thesis.



\### 11.6 Excel files do not open



Make sure `openpyxl>=3.1` is installed:



```bash

pip install openpyxl

```



\### 11.7 Filepath with spaces or non-ASCII characters



The pipeline uses `pathlib.Path` throughout and reads images via `np.fromfile` + `cv2.imdecode`, so paths with spaces, parentheses, or Unicode characters (e.g. `Autochrome by an unknown artist(1913)/`) work without issue.



\---



\## 12. Citations



If you use this pipeline in your thesis, please cite the original metric papers:



\- \*\*PSNR / SSIM\*\* — Wang, Z., Bovik, A. C., Sheikh, H. R., \& Simoncelli, E. P. (2004). \*Image quality assessment: from error visibility to structural similarity.\* IEEE Transactions on Image Processing, 13(4), 600–612.

\- \*\*MS-SSIM\*\* — Wang, Z., Simoncelli, E. P., \& Bovik, A. C. (2003). \*Multiscale structural similarity for image quality assessment.\* In Asilomar Conference on Signals, Systems \& Computers.

\- \*\*LPIPS\*\* — Zhang, R., Isola, P., Efros, A. A., Shechtman, E., \& Wang, O. (2018). \*The Unreasonable Effectiveness of Deep Features as a Perceptual Metric.\* In CVPR.

\- \*\*FSIM\*\* — Zhang, L., Zhang, L., Mou, X., \& Zhang, D. (2011). \*FSIM: A Feature Similarity Index for Image Quality Assessment.\* IEEE Transactions on Image Processing, 20(8), 2378–2386.

\- \*\*CIEDE2000\*\* — Sharma, G., Wu, W., \& Dalal, E. N. (2005). \*The CIEDE2000 color-difference formula: Implementation notes, supplementary test data, and mathematical observations.\* Color Research \& Application, 30(1), 21–30.



\### Library citations



\- \*\*scikit-image\*\* — van der Walt, S. et al. (2014). \*scikit-image: image processing in Python.\* PeerJ 2:e453.

\- \*\*PyTorch\*\* — Paszke, A. et al. (2019). \*PyTorch: An Imperative Style, High-Performance Deep Learning Library.\* NeurIPS.

\- \*\*pytorch-msssim\*\* — Vadim, P. (2020). \*pytorch-msssim.\* GitHub repository.

\- \*\*piq\*\* — Kastryulin, S. et al. (2019). \*PyTorch Image Quality: Metrics for Image Quality Assessment.\* GitHub repository.

\- \*\*lpips\*\* — Zhang, R. (2018). \*lpips.\* GitHub repository.

\- \*\*colour-science\*\* — Colour Developers (2015). \*Colour: An open-source Python package for colour science.\* GitHub repository.

\- \*\*OpenCV\*\* — Bradski, G. (2000). \*The OpenCV Library.\* Dr. Dobb's Journal.



\---



\## 13. License



This project is released under the MIT License. The metric implementations belong to their respective authors and retain their original licenses.



\---

