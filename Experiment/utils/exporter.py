"""Persistence layer for the evaluation pipeline.

Three responsibilities live here:

1. :func:`export_results`   – write the per-image metric DataFrame to
   ``results.csv`` and ``results.xlsx``.
2. :func:`export_summary`   – aggregate the per-image metrics by model and
   write to ``summary.csv`` and ``summary.xlsx``.
3. :func:`generate_plots`   – produce boxplots, bar charts, a ranking table
   and a correlation matrix into ``results/plots/`` using only matplotlib.

All functions take the output directory as an explicit argument so they can
be reused from tests or alternate entry points.
"""

from __future__ import annotations

from pathlib import Path
from typing import Dict, List, Sequence

import matplotlib
import numpy as np
import pandas as pd

matplotlib.use("Agg")  # Non-interactive backend, safe for headless servers.
import matplotlib.pyplot as plt

from utils.logger import get_logger

logger = get_logger(__name__)


# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

#: Metrics that should be **maximised** (higher = better).
_HIGH_BETTER_METRICS: tuple[str, ...] = ("PSNR", "SSIM", "MS-SSIM", "FSIM")
#: Metrics that should be **minimised** (lower = better).
_LOW_BETTER_METRICS: tuple[str, ...] = ("LPIPS", "DeltaE")
#: Order in which the metric columns appear in the exported files.
_METRIC_COLUMN_ORDER: tuple[str, ...] = (
    "PSNR", "SSIM", "MS-SSIM", "LPIPS", "FSIM", "DeltaE",
)
#: Colour palette used for the three models in every plot.
_MODEL_COLORS: Dict[str, str] = {
    "Zhang": "#4C72B0",
    "DeOldify": "#DD8452",
    "FLUX": "#55A868",
}
#: Default matplotlib figure DPI.
_DPI: int = 150


# ---------------------------------------------------------------------------
# CSV / XLSX exporters
# ---------------------------------------------------------------------------

def _order_columns(df: pd.DataFrame) -> pd.DataFrame:
    """Return ``df`` with metric columns ordered consistently."""
    cols: List[str] = ["Image Name", "Model"] + [
        c for c in _METRIC_COLUMN_ORDER if c in df.columns
    ]
    extras = [c for c in df.columns if c not in cols]
    return df[cols + extras]


def export_results(df: pd.DataFrame, out_dir: Path) -> None:
    """Save the per-image results DataFrame to CSV and XLSX.

    Parameters
    ----------
    df:
        DataFrame produced by :func:`evaluate_folder` calls accumulated by
        the main script.  Must contain at least the ``Image Name`` and
        ``Model`` columns plus the metric columns.
    out_dir:
        Directory where ``results.csv`` and ``results.xlsx`` will be
        written.  Created if it does not exist.
    """
    out_dir.mkdir(parents=True, exist_ok=True)
    df = _order_columns(df.copy())

    csv_path = out_dir / "results.csv"
    xlsx_path = out_dir / "results.xlsx"

    df.to_csv(csv_path, index=False, encoding="utf-8")
    try:
        with pd.ExcelWriter(xlsx_path, engine="openpyxl") as writer:
            df.to_excel(writer, sheet_name="results", index=False)
            # Auto-size columns where possible.
            ws = writer.sheets["results"]
            for i, col in enumerate(df.columns, start=1):
                max_len = max(
                    df[col].astype(str).map(len).max() if len(df) else 0,
                    len(str(col)),
                )
                ws.column_dimensions[ws.cell(row=1, column=i).column_letter].width = (
                    min(max_len + 2, 40)
                )
    except Exception as exc:  # pragma: no cover - openpyxl rarely fails
        logger.error("Failed to write XLSX results: %s", exc)

    logger.info("Saved per-image results → %s", csv_path)
    logger.info("Saved per-image results → %s", xlsx_path)


def export_summary(df: pd.DataFrame, out_dir: Path) -> pd.DataFrame:
    """Aggregate metrics per model and save to CSV / XLSX.

    The returned DataFrame has one row per model with the columns:

    ``Model, Mean PSNR, Mean SSIM, Mean MS-SSIM, Mean LPIPS, Mean FSIM,
    Mean DeltaE``.

    Parameters
    ----------
    df:
        Per-image results DataFrame.
    out_dir:
        Directory where ``summary.csv`` and ``summary.xlsx`` will be written.

    Returns
    -------
    pd.DataFrame
        The summary DataFrame that was written to disk.
    """
    out_dir.mkdir(parents=True, exist_ok=True)

    metric_cols = [c for c in _METRIC_COLUMN_ORDER if c in df.columns]
    summary = (
        df.groupby("Model")[metric_cols]
        .mean()
        .reset_index()
        .rename(columns={c: f"Mean {c}" for c in metric_cols})
    )
    # Order columns: Model first, then metrics in canonical order.
    summary = summary[["Model"] + [f"Mean {c}" for c in metric_cols]]
    summary = summary.sort_values("Model").reset_index(drop=True)

    csv_path = out_dir / "summary.csv"
    xlsx_path = out_dir / "summary.xlsx"

    summary.to_csv(csv_path, index=False, encoding="utf-8")
    try:
        with pd.ExcelWriter(xlsx_path, engine="openpyxl") as writer:
            summary.to_excel(writer, sheet_name="summary", index=False)
            ws = writer.sheets["summary"]
            for i, col in enumerate(summary.columns, start=1):
                max_len = max(
                    summary[col].astype(str).map(len).max() if len(summary) else 0,
                    len(str(col)),
                )
                ws.column_dimensions[ws.cell(row=1, column=i).column_letter].width = (
                    min(max_len + 2, 40)
                )
    except Exception as exc:  # pragma: no cover
        logger.error("Failed to write XLSX summary: %s", exc)

    logger.info("Saved per-model summary   → %s", csv_path)
    logger.info("Saved per-model summary   → %s", xlsx_path)
    return summary


# ---------------------------------------------------------------------------
# Plotting
# ---------------------------------------------------------------------------

def _plot_boxplots(df: pd.DataFrame, out_dir: Path) -> None:
    """One boxplot per metric, three boxes (one per model)."""
    metrics = [c for c in _METRIC_COLUMN_ORDER if c in df.columns]
    if not metrics:
        return

    models = sorted(df["Model"].unique())
    n = len(metrics)
    cols = 3
    rows = int(np.ceil(n / cols))
    fig, axes = plt.subplots(
        rows, cols, figsize=(5 * cols, 4 * rows), constrained_layout=True
    )
    axes = np.atleast_1d(axes).ravel()

    for ax, metric in zip(axes, metrics):
        data = [
            df.loc[df["Model"] == m, metric].dropna().values for m in models
        ]
        # ``tick_labels`` replaces the deprecated ``labels`` argument in
        # matplotlib 3.9+.  We try the new name first and fall back for
        # older matplotlib installs.
        try:
            bp = ax.boxplot(
                data, tick_labels=models,
                patch_artist=True, showmeans=True,
            )
        except TypeError:  # pragma: no cover - matplotlib < 3.9
            bp = ax.boxplot(
                data, labels=models,
                patch_artist=True, showmeans=True,
            )
        for patch, m in zip(bp["boxes"], models):
            patch.set_facecolor(_MODEL_COLORS.get(m, "#888888"))
            patch.set_alpha(0.6)
        ax.set_title(metric)
        ax.grid(axis="y", linestyle="--", alpha=0.4)
        ax.tick_params(axis="x", rotation=15)

    # Hide unused axes.
    for ax in axes[len(metrics):]:
        ax.axis("off")

    fig.suptitle("Metric distribution per model", fontsize=14)
    out_path = out_dir / "boxplots.png"
    fig.savefig(out_path, dpi=_DPI)
    plt.close(fig)
    logger.info("Saved boxplots             → %s", out_path)


def _plot_bar_means(summary: pd.DataFrame, out_dir: Path) -> None:
    """Bar chart of the mean value for every metric, grouped by model."""
    mean_cols = [c for c in summary.columns if c.startswith("Mean ")]
    if not mean_cols:
        return

    metrics = [c.replace("Mean ", "") for c in mean_cols]
    models = summary["Model"].tolist()
    n = len(metrics)
    cols = 3
    rows = int(np.ceil(n / cols))
    fig, axes = plt.subplots(
        rows, cols, figsize=(5 * cols, 4 * rows), constrained_layout=True
    )
    axes = np.atleast_1d(axes).ravel()

    x = np.arange(len(models))
    for ax, metric in zip(axes, metrics):
        values = summary[f"Mean {metric}"].values
        bars = ax.bar(
            x,
            values,
            color=[_MODEL_COLORS.get(m, "#888888") for m in models],
            alpha=0.85,
            edgecolor="black",
            linewidth=0.5,
        )
        ax.set_title(f"Mean {metric}")
        ax.set_xticks(x)
        ax.set_xticklabels(models, rotation=15)
        ax.grid(axis="y", linestyle="--", alpha=0.4)
        for bar, v in zip(bars, values):
            ax.text(
                bar.get_x() + bar.get_width() / 2,
                bar.get_height(),
                f"{v:.3f}",
                ha="center",
                va="bottom",
                fontsize=8,
            )

    for ax in axes[len(metrics):]:
        ax.axis("off")

    fig.suptitle("Mean metric per model", fontsize=14)
    out_path = out_dir / "bar_means.png"
    fig.savefig(out_path, dpi=_DPI)
    plt.close(fig)
    logger.info("Saved bar chart            → %s", out_path)


def _plot_ranking(summary: pd.DataFrame, out_dir: Path) -> None:
    """Compute a per-metric rank (1 = best) and save as a CSV + heatmap PNG.

    Higher-is-better metrics are ranked descending; lower-is-better metrics
    are ranked ascending.  The average rank decides the overall winner.
    """
    metric_cols = [c for c in summary.columns if c.startswith("Mean ")]
    if not metric_cols:
        return

    rank_df = summary[["Model"]].copy()
    for col in metric_cols:
        metric = col.replace("Mean ", "")
        ascending = metric in _LOW_BETTER_METRICS
        rank_df[col] = summary[col].rank(
            method="min", ascending=ascending
        ).astype(int)

    rank_df["Avg Rank"] = rank_df[metric_cols].mean(axis=1)
    rank_df = rank_df.sort_values("Avg Rank").reset_index(drop=True)

    # CSV
    rank_csv = out_dir / "ranking.csv"
    rank_df.to_csv(rank_csv, index=False, encoding="utf-8")
    logger.info("Saved ranking table        → %s", rank_csv)

    # Heatmap PNG
    numeric = rank_df.set_index("Model")[metric_cols + ["Avg Rank"]]
    fig, ax = plt.subplots(
        figsize=(2.2 + 1.2 * numeric.shape[1], 0.8 + 0.6 * numeric.shape[0]),
        constrained_layout=True,
    )
    im = ax.imshow(numeric.values, cmap="RdYlGn_r", aspect="auto")
    ax.set_xticks(range(numeric.shape[1]))
    ax.set_xticklabels(numeric.columns, rotation=30, ha="right")
    ax.set_yticks(range(numeric.shape[0]))
    ax.set_yticklabels(numeric.index)
    for i in range(numeric.shape[0]):
        for j in range(numeric.shape[1]):
            ax.text(
                j, i, f"{numeric.values[i, j]:.1f}",
                ha="center", va="center", fontsize=9,
            )
    fig.colorbar(im, ax=ax, fraction=0.046, pad=0.04)
    ax.set_title("Model ranking (1 = best)")
    out_path = out_dir / "ranking.png"
    fig.savefig(out_path, dpi=_DPI)
    plt.close(fig)
    logger.info("Saved ranking heatmap      → %s", out_path)


def _plot_correlation_matrix(df: pd.DataFrame, out_dir: Path) -> None:
    """Pearson correlation matrix across all per-image metric samples."""
    metric_cols = [c for c in _METRIC_COLUMN_ORDER if c in df.columns]
    if len(metric_cols) < 2:
        return

    corr = df[metric_cols].corr(method="pearson")
    fig, ax = plt.subplots(
        figsize=(2.0 + 0.9 * len(metric_cols), 2.0 + 0.9 * len(metric_cols)),
        constrained_layout=True,
    )
    im = ax.imshow(corr.values, cmap="coolwarm", vmin=-1, vmax=1, aspect="auto")
    ax.set_xticks(range(len(metric_cols)))
    ax.set_xticklabels(metric_cols, rotation=30, ha="right")
    ax.set_yticks(range(len(metric_cols)))
    ax.set_yticklabels(metric_cols)
    for i in range(len(metric_cols)):
        for j in range(len(metric_cols)):
            ax.text(
                j, i, f"{corr.values[i, j]:.2f}",
                ha="center", va="center", fontsize=9,
            )
    fig.colorbar(im, ax=ax, fraction=0.046, pad=0.04)
    ax.set_title("Metric correlation matrix")
    out_path = out_dir / "correlation_matrix.png"
    fig.savefig(out_path, dpi=_DPI)
    plt.close(fig)
    logger.info("Saved correlation matrix   → %s", out_path)


def generate_plots(df: pd.DataFrame, out_dir: Path) -> None:
    """Generate every plot (boxplots, bars, ranking, correlation).

    Parameters
    ----------
    df:
        Per-image results DataFrame.
    out_dir:
        Directory where ``plots/`` will be created.  Plots are written
        directly inside ``out_dir`` (the caller is expected to pass
        ``results/plots``).
    """
    out_dir.mkdir(parents=True, exist_ok=True)

    if df.empty:
        logger.warning("No data to plot – skipping plot generation.")
        return

    try:
        _plot_boxplots(df, out_dir)
    except Exception as exc:
        logger.error("Boxplot generation failed: %s", exc, exc_info=True)

    # Summary is needed for bar chart and ranking.
    metric_cols = [c for c in _METRIC_COLUMN_ORDER if c in df.columns]
    summary = (
        df.groupby("Model")[metric_cols]
        .mean()
        .reset_index()
        .rename(columns={c: f"Mean {c}" for c in metric_cols})
    )

    try:
        _plot_bar_means(summary, out_dir)
    except Exception as exc:
        logger.error("Bar chart generation failed: %s", exc, exc_info=True)

    try:
        _plot_ranking(summary, out_dir)
    except Exception as exc:
        logger.error("Ranking generation failed: %s", exc, exc_info=True)

    try:
        _plot_correlation_matrix(df, out_dir)
    except Exception as exc:
        logger.error("Correlation matrix generation failed: %s", exc, exc_info=True)
