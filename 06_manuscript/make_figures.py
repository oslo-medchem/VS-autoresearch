#!/usr/bin/env python3
"""Generate publication-quality figures for the Digital Discovery manuscript.

Two-target study: FPR2 (GPCR) + CDK2 (kinase) autoresearch campaigns.
"""

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import numpy as np
from pathlib import Path

OUTDIR = Path(__file__).parent / "figures"
OUTDIR.mkdir(exist_ok=True)

# RSC style: clean, minimal, publication-ready
plt.rcParams.update({
    "font.family": "sans-serif",
    "font.sans-serif": ["Arial", "Helvetica", "DejaVu Sans"],
    "font.size": 9,
    "axes.labelsize": 10,
    "axes.titlesize": 10,
    "xtick.labelsize": 8,
    "ytick.labelsize": 8,
    "legend.fontsize": 8,
    "figure.dpi": 300,
    "savefig.dpi": 300,
    "savefig.bbox": "tight",
    "axes.linewidth": 0.8,
    "xtick.major.width": 0.6,
    "ytick.major.width": 0.6,
    "lines.linewidth": 1.2,
})

# Colour palette (colourblind-safe, RSC-appropriate)
C_KEPT = "#2166AC"       # strong blue for kept
C_REVERTED = "#B2182B"   # muted red for reverted
C_BASELINE = "#4DAF4A"   # green for baseline
C_LIGHT = "#D1E5F0"      # light blue bg
C_GREY = "#878787"       # grey for annotations
C_FPR2 = "#2166AC"       # blue for FPR2
C_CDK2 = "#D6604D"       # warm red for CDK2


# ============================================================================
# FIGURE 1: Autoresearch workflow schematic
# ============================================================================

def make_figure1():
    fig, ax = plt.subplots(figsize=(7.0, 3.2))
    ax.set_xlim(0, 10)
    ax.set_ylim(0, 4.0)
    ax.axis("off")

    # Title
    ax.text(5.0, 3.7, "Autoresearch experiment loop", fontsize=11,
            fontweight="bold", ha="center", va="center")

    # Box positions (circular loop)
    boxes = [
        (1.0, 2.2, "1. Hypothesise\nsingle change"),
        (3.0, 2.2, "2. Modify\nexperiment.py"),
        (5.0, 2.2, "3. Git commit\none change"),
        (7.0, 2.2, "4. Dock library\n(dual-GPU)"),
        (9.0, 2.2, "5. Evaluate\nROC AUC"),
    ]

    box_w, box_h = 1.6, 0.9
    box_colors = ["#E8F4FD", "#E8F4FD", "#FFF3E0", "#E8F4FD", "#E8F8E8"]

    for i, (x, y, txt) in enumerate(boxes):
        rect = mpatches.FancyBboxPatch(
            (x - box_w/2, y - box_h/2), box_w, box_h,
            boxstyle="round,pad=0.08", facecolor=box_colors[i],
            edgecolor="#333333", linewidth=0.8
        )
        ax.add_patch(rect)
        ax.text(x, y, txt, ha="center", va="center", fontsize=7.5,
                fontweight="medium")

    # Arrows between boxes
    arrow_kw = dict(arrowstyle="->,head_width=0.12,head_length=0.08",
                    color="#333333", linewidth=1.0)
    for i in range(len(boxes) - 1):
        x1 = boxes[i][0] + box_w/2 + 0.02
        x2 = boxes[i+1][0] - box_w/2 - 0.02
        y = 2.2
        ax.annotate("", xy=(x2, y), xytext=(x1, y), arrowprops=arrow_kw)

    # Decision diamond below step 5
    diamond_x, diamond_y = 7.0, 0.7
    diamond = plt.Polygon(
        [(diamond_x, diamond_y + 0.5), (diamond_x + 0.7, diamond_y),
         (diamond_x, diamond_y - 0.5), (diamond_x - 0.7, diamond_y)],
        facecolor="#FFF9C4", edgecolor="#333333", linewidth=0.8
    )
    ax.add_patch(diamond)
    ax.text(diamond_x, diamond_y, "AUC\nimproved?", ha="center", va="center",
            fontsize=7, fontweight="medium")

    # Arrow from step 5 down to diamond
    ax.annotate("", xy=(7.0, diamond_y + 0.5), xytext=(7.0, 2.2 - box_h/2 - 0.02),
                arrowprops=arrow_kw)

    # YES arrow (right) -> Keep box
    keep_x, keep_y = 9.0, 0.7
    rect_keep = mpatches.FancyBboxPatch(
        (keep_x - 0.6, keep_y - 0.3), 1.2, 0.6,
        boxstyle="round,pad=0.06", facecolor="#C8E6C9",
        edgecolor="#2E7D32", linewidth=0.8
    )
    ax.add_patch(rect_keep)
    ax.text(keep_x, keep_y, "Keep\ncommit", ha="center", va="center",
            fontsize=7.5, fontweight="bold", color="#2E7D32")
    ax.annotate("", xy=(keep_x - 0.6, keep_y), xytext=(diamond_x + 0.7, diamond_y),
                arrowprops=arrow_kw)
    ax.text(8.0, 0.95, "Yes", fontsize=7, color=C_GREY, fontstyle="italic")

    # NO arrow (left) -> Revert box
    revert_x, revert_y = 5.0, 0.7
    rect_revert = mpatches.FancyBboxPatch(
        (revert_x - 0.6, revert_y - 0.3), 1.2, 0.6,
        boxstyle="round,pad=0.06", facecolor="#FFCDD2",
        edgecolor="#C62828", linewidth=0.8
    )
    ax.add_patch(rect_revert)
    ax.text(revert_x, revert_y, "Revert\n(git)", ha="center", va="center",
            fontsize=7.5, fontweight="bold", color="#C62828")
    ax.annotate("", xy=(revert_x + 0.6, revert_y), xytext=(diamond_x - 0.7, diamond_y),
                arrowprops=arrow_kw)
    ax.text(5.95, 0.95, "No", fontsize=7, color=C_GREY, fontstyle="italic")

    # Loop-back arrow from Revert/Keep back to step 1
    ax.annotate(
        "", xy=(1.0, 2.2 - box_h/2 - 0.02), xytext=(3.0, 0.7),
        arrowprops=dict(arrowstyle="->,head_width=0.12,head_length=0.08",
                        color="#333333", linewidth=1.0,
                        connectionstyle="arc3,rad=0.3")
    )
    ax.text(1.5, 1.15, "Next\nexperiment", fontsize=6.5, color=C_GREY,
            fontstyle="italic", ha="center")

    # Agent label
    ax.text(5.0, 3.2, "LLM Agent (Claude Code)", fontsize=8,
            ha="center", va="center", color=C_GREY, fontstyle="italic")

    for fmt in ("png", "svg"):
        fig.savefig(OUTDIR / f"figure1_workflow.{fmt}", transparent=False,
                    facecolor="white")
    plt.close(fig)
    print("Figure 1 saved.")


# ============================================================================
# ============================================================================
# FIGURE 2: Multi-metric divergence — baseline vs optimised
# ============================================================================

def make_figure2():
    """Percentage change from baseline for AUC, BEDROC, and EF 1%.

    Reveals that FPR2 AUC gain comes at the cost of early enrichment,
    while CDK2 improvement is robust across all three metrics.
    """
    metric_labels = ["EF 1%", "BEDROC (α = 80.5)", "ROC AUC"]  # bottom to top

    # FPR2: baseline → optimised (Vinardo scoring)
    fpr2_bl  = [1.93,   0.2765, 0.7359]
    fpr2_opt = [1.05,   0.2382, 0.7480]

    # CDK2: baseline → optimised (naive library + Vina scoring)
    cdk2_bl  = [1.71,   0.4428, 0.6767]
    cdk2_opt = [3.50,   0.7660, 0.7347]

    fpr2_pct = [(o - b) / b * 100 for b, o in zip(fpr2_bl, fpr2_opt)]
    cdk2_pct = [(o - b) / b * 100 for b, o in zip(cdk2_bl, cdk2_opt)]

    # Formatting helpers
    def fmt_abs(bl, opt, is_ef=False):
        if is_ef:
            return f"{bl:.2f} → {opt:.2f}"
        return f"{bl:.3f} → {opt:.3f}"

    C_POS = "#2E7D32"   # dark green for improvement
    C_NEG = C_REVERTED  # red for worsening

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(7.5, 3.2), sharey=True,
                                    gridspec_kw={"wspace": 0.15})
    y = np.arange(len(metric_labels))
    bar_h = 0.50

    # Shared x-axis range so panels are directly comparable
    xlim = (-60, 140)

    for ax, pcts, bl, opt, title, panel_lbl in [
        (ax1, fpr2_pct, fpr2_bl, fpr2_opt,
         "FPR2 (GPCR, 3.0 \u00c5 cryo-EM)", "A"),
        (ax2, cdk2_pct, cdk2_bl, cdk2_opt,
         "CDK2 (kinase, 1.74 \u00c5 X-ray)", "B"),
    ]:
        colors = [C_POS if p > 0 else C_NEG for p in pcts]
        ax.barh(y, pcts, height=bar_h, color=colors, edgecolor="white",
                linewidth=0.5, alpha=0.85)

        # Zero line
        ax.axvline(x=0, color="#333333", linewidth=0.6)

        # Annotate each bar — always place text to the right of the bar
        for i, (p, b_val, o_val) in enumerate(zip(pcts, bl, opt)):
            is_ef = (i == 0)  # EF 1% is index 0
            sign = "+" if p > 0 else ""
            color = C_POS if p > 0 else C_NEG

            if p >= 0:
                text_x = p + 3
            else:
                # Negative bars: place annotations right of zero to avoid
                # colliding with y-axis labels
                text_x = 3

            ax.text(text_x, i + 0.12, f"{sign}{p:.1f}%",
                    va="center", ha="left", fontsize=8, fontweight="bold",
                    color=color)
            ax.text(text_x, i - 0.18, fmt_abs(b_val, o_val, is_ef),
                    va="center", ha="left", fontsize=6.5, color=C_GREY)

        ax.set_xlim(xlim)
        ax.set_xlabel("Change from baseline (%)")
        ax.spines["top"].set_visible(False)
        ax.spines["right"].set_visible(False)
        ax.set_title(title, fontsize=9, fontweight="bold", loc="left")
        ax.text(-0.08 if panel_lbl == "A" else -0.04, 1.10, panel_lbl,
                transform=ax.transAxes, fontsize=13, fontweight="bold",
                va="top")

    ax1.set_yticks(y)
    ax1.set_yticklabels(metric_labels, fontsize=9)

    # Light shading to separate improving vs worsening regions
    for ax in (ax1, ax2):
        ax.axvspan(xlim[0], 0, color=C_NEG, alpha=0.03, zorder=0)
        ax.axvspan(0, xlim[1], color=C_POS, alpha=0.03, zorder=0)

    fig.tight_layout()
    for fmt in ("png", "svg"):
        fig.savefig(OUTDIR / f"figure2_auc_comparison.{fmt}", transparent=False,
                    facecolor="white")
    plt.close(fig)
    print("Figure 2 saved.")


# FIGURE 3: Cross-target parameter sensitivity
# ============================================================================

def make_figure3():
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(7.5, 3.5),
                                    gridspec_kw={"wspace": 0.35})

    bar_width = 0.35
    x = np.arange(2)  # FPR2, CDK2

    # --- Panel A: Scoring function effect ---
    # FPR2: Vina 0.736, Vinardo 0.748 (both with skill library)
    # CDK2: Vina 0.735, Vinardo 0.716 (both with naive library, comparable configs)
    vina_aucs = [0.736, 0.735]
    vinardo_aucs = [0.748, 0.716]

    b1 = ax1.bar(x - bar_width/2, vina_aucs, bar_width, label="Vina",
                 color="#92C5DE", edgecolor="white")
    b2 = ax1.bar(x + bar_width/2, vinardo_aucs, bar_width, label="Vinardo",
                 color="#F4A582", edgecolor="white")

    for bars in [b1, b2]:
        for bar in bars:
            h = bar.get_height()
            ax1.text(bar.get_x() + bar.get_width()/2, h + 0.003,
                     f"{h:.3f}", ha="center", va="bottom", fontsize=7.5,
                     fontweight="medium")

    # Delta annotations
    ax1.annotate("+0.012", xy=(0, 0.748), xytext=(0, 0.765),
                 ha="center", fontsize=7, color="#2E7D32", fontweight="bold",
                 arrowprops=dict(arrowstyle="-", color="#2E7D32", linewidth=0.8))
    ax1.annotate("\u22120.019", xy=(1, 0.716), xytext=(1, 0.765),
                 ha="center", fontsize=7, color=C_REVERTED, fontweight="bold",
                 arrowprops=dict(arrowstyle="-", color=C_REVERTED, linewidth=0.8))

    ax1.set_xticks(x)
    ax1.set_xticklabels(["FPR2\n(GPCR)", "CDK2\n(kinase)"], fontsize=9)
    ax1.set_ylabel("ROC AUC")
    ax1.set_ylim(0.68, 0.79)
    ax1.legend(loc="upper center", ncol=2, framealpha=0.9, edgecolor="#CCCCCC")
    ax1.spines["top"].set_visible(False)
    ax1.spines["right"].set_visible(False)
    ax1.set_title("Scoring function", fontsize=10, fontweight="bold")
    ax1.text(-0.12, 1.08, "A", transform=ax1.transAxes, fontsize=13,
             fontweight="bold", va="top")

    # --- Panel B: Library preparation effect ---
    # FPR2: skill 0.748, naive NaN (crashed)
    # CDK2: skill 0.677, naive 0.735
    skill_aucs = [0.748, 0.677]
    naive_aucs = [0.0, 0.735]  # FPR2 naive = 0 (crashed)

    b3 = ax2.bar(x - bar_width/2, skill_aucs, bar_width, label="Skill (Meeko)",
                 color="#92C5DE", edgecolor="white")
    b4 = ax2.bar(x + bar_width/2, naive_aucs, bar_width, label="Naive (OpenBabel)",
                 color="#F4A582", edgecolor="white")

    # Hatch the failed FPR2 naive bar
    b4[0].set_hatch("///")
    b4[0].set_facecolor("#DDDDDD")
    b4[0].set_edgecolor(C_REVERTED)

    for bar in b3:
        h = bar.get_height()
        ax2.text(bar.get_x() + bar.get_width()/2, h + 0.003,
                 f"{h:.3f}", ha="center", va="bottom", fontsize=7.5,
                 fontweight="medium")
    # CDK2 naive label
    ax2.text(b4[1].get_x() + b4[1].get_width()/2, 0.735 + 0.003,
             "0.735", ha="center", va="bottom", fontsize=7.5, fontweight="medium")
    # FPR2 naive - failed label
    ax2.text(b4[0].get_x() + b4[0].get_width()/2, 0.52,
             "Crashed", ha="center", va="bottom", fontsize=7,
             color=C_REVERTED, fontweight="bold", rotation=90)

    # Delta annotations
    ax2.annotate("+0.058", xy=(1, 0.735), xytext=(1, 0.765),
                 ha="center", fontsize=7, color="#2E7D32", fontweight="bold",
                 arrowprops=dict(arrowstyle="-", color="#2E7D32", linewidth=0.8))

    ax2.set_xticks(x)
    ax2.set_xticklabels(["FPR2\n(GPCR)", "CDK2\n(kinase)"], fontsize=9)
    ax2.set_ylabel("ROC AUC")
    ax2.set_ylim(0.48, 0.79)
    ax2.legend(loc="upper center", ncol=2, framealpha=0.9, edgecolor="#CCCCCC")
    ax2.spines["top"].set_visible(False)
    ax2.spines["right"].set_visible(False)
    ax2.set_title("Library preparation", fontsize=10, fontweight="bold")
    ax2.text(-0.12, 1.08, "B", transform=ax2.transAxes, fontsize=13,
             fontweight="bold", va="top")

    for fmt in ("png", "svg"):
        fig.savefig(OUTDIR / f"figure3_cross_target.{fmt}", transparent=False,
                    facecolor="white")
    plt.close(fig)
    print("Figure 3 saved.")


# ============================================================================
# FIGURE S1: FPR2 delta AUC waterfall
# ============================================================================

def make_figure_s1():
    labels = ["Vinardo\nscoring", "Box\n20 \u00c5", "Naive\nlibrary",
              "Rank\ntransform", "Exh.\n16", "Naive\nreceptor",
              "MW\ncorrection", "Multi-pose\nmean top-3", "Multi-pose\nBoltzmann"]
    deltas = [+0.012, -0.003, None, 0.000, -0.004, -0.016, -0.046, -0.033, -0.018]

    fig, ax = plt.subplots(figsize=(6.0, 3.5))
    y = np.arange(len(labels))[::-1]

    colors = []
    vals = []
    for d in deltas:
        if d is None:
            colors.append("#DDDDDD")
            vals.append(0)
        elif d > 0:
            colors.append(C_KEPT)
            vals.append(d)
        elif d == 0:
            colors.append(C_GREY)
            vals.append(d)
        else:
            colors.append(C_REVERTED)
            vals.append(d)

    bars = ax.barh(y, vals, color=colors, edgecolor="white",
                   linewidth=0.5, height=0.6)

    # Hatch for NaN
    idx_nan = 2
    ax.barh(y[idx_nan], 0, color="#DDDDDD", edgecolor=C_REVERTED,
            hatch="///", height=0.6)

    ax.axvline(x=0, color="#333333", linewidth=0.5)
    ax.set_yticks(y)
    ax.set_yticklabels(labels, fontsize=7.5)
    ax.set_xlabel("\u0394 AUC (vs. baseline)")
    ax.set_xlim(-0.055, 0.025)
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    ax.set_title("FPR2: change in AUC per experiment", fontsize=10, fontweight="bold")

    for i, d in enumerate(deltas):
        if d is None:
            ax.text(0.002, y[i], "N/A", va="center", fontsize=6.5, color=C_GREY)
        elif d != 0:
            offset = 0.002 if d > 0 else -0.002
            ha = "left" if d > 0 else "right"
            ax.text(d + offset, y[i], f"{d:+.3f}", va="center", ha=ha,
                    fontsize=6.5, fontweight="medium")
        else:
            ax.text(0.002, y[i], "0.000", va="center", fontsize=6.5, color=C_GREY)

    fig.tight_layout()
    for fmt in ("png", "svg"):
        fig.savefig(OUTDIR / f"figure_s1_fpr2_waterfall.{fmt}", transparent=False,
                    facecolor="white")
    plt.close(fig)
    print("Figure S1 saved.")


# ============================================================================
# FIGURE S2: CDK2 delta AUC waterfall
# ============================================================================

def make_figure_s2():
    labels = [
        "Vinardo scoring", "Box 20 \u00c5", "Box 18 \u00c5", "Box 30 \u00c5",
        "Exh. 16", "Exh. 32",
        "Naive lib (Vinardo)", "Naive rec+lib",
        "Naive lib (Vina)", "Energy range 5",
        "Batch size 50", "Batch size 20", "Exh. 4",
        "Box 22 \u00c5", "Num modes 20",
    ]
    # Deltas vs. the best-at-that-point baseline
    # CDK2 baseline = 0.6767
    # After vinardo kept (0.6947): new baseline
    # After naive lib vinardo kept (0.7155): new baseline
    # After naive lib vina kept (0.7347): new baseline
    # After batch50 kept (0.7325): used as best reference
    raw_aucs = [0.695, 0.692, 0.694, 0.685, 0.686, 0.693,
                0.716, 0.706, 0.735, 0.735,
                0.733, 0.730, 0.729, 0.729, 0.727]
    baseline = 0.677
    deltas = [a - baseline for a in raw_aucs]

    fig, ax = plt.subplots(figsize=(6.0, 5.0))
    y = np.arange(len(labels))[::-1]

    colors = []
    decisions = [
        "kept", "reverted", "reverted", "reverted", "reverted", "reverted",
        "kept", "reverted", "kept", "reverted",
        "kept", "reverted", "reverted", "reverted", "reverted",
    ]
    for dec in decisions:
        if dec == "kept":
            colors.append(C_KEPT)
        else:
            colors.append(C_REVERTED)

    ax.barh(y, deltas, color=colors, edgecolor="white",
            linewidth=0.5, height=0.6)

    ax.axvline(x=0, color="#333333", linewidth=0.5)
    ax.set_yticks(y)
    ax.set_yticklabels(labels, fontsize=7)
    ax.set_xlabel("\u0394 AUC (vs. baseline 0.677)")
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    ax.set_title("CDK2: change in AUC per experiment", fontsize=10, fontweight="bold")

    for i, d in enumerate(deltas):
        offset = 0.001 if d >= 0 else -0.001
        ha = "left" if d >= 0 else "right"
        ax.text(d + offset, y[i], f"{d:+.3f}", va="center", ha=ha,
                fontsize=6.5, fontweight="medium")

    # Legend
    legend_patches = [
        mpatches.Patch(facecolor=C_KEPT, label="Kept"),
        mpatches.Patch(facecolor=C_REVERTED, label="Reverted"),
    ]
    ax.legend(handles=legend_patches, loc="lower right", framealpha=0.9,
              edgecolor="#CCCCCC")

    fig.tight_layout()
    for fmt in ("png", "svg"):
        fig.savefig(OUTDIR / f"figure_s2_cdk2_waterfall.{fmt}", transparent=False,
                    facecolor="white")
    plt.close(fig)
    print("Figure S2 saved.")


# ============================================================================
# FIGURE S3: GPU compute timeline — both campaigns
# ============================================================================

def make_figure_s3():
    # FPR2 data
    fpr2_exps = [
        "Baseline", "Vinardo", "Box 20\u00c5", "Naive lib",
        "Rank transform", "Exh. 16", "Naive receptor",
        "MW correction", "Multi-pose (5x)"
    ]
    fpr2_hours = [6.1, 6.2, 6.5, 0.1, 0.0, 6.9, 6.2, 6.2, 0.0]
    fpr2_cumul = np.cumsum(fpr2_hours)

    # CDK2 data (convert seconds to hours)
    cdk2_exps = [
        "Baseline", "Vinardo", "Box 20\u00c5", "Box 18\u00c5", "Box 30\u00c5",
        "Exh. 16", "Exh. 32", "Naive lib\n(Vinardo)", "Naive\nrec+lib",
        "Naive lib\n(Vina)", "Energy\nrange", "Batch 50",
        "Batch 20", "Exh. 4", "Box 22\u00c5", "Num\nmodes 20",
    ]
    cdk2_secs = [1342, 1351, 1449, 1394, 1402, 1622, 2152,
                 625, 674, 578, 582, 1381, 3174, 1190, 1454, 1410]
    cdk2_hours = [s / 3600 for s in cdk2_secs]
    cdk2_cumul = np.cumsum(cdk2_hours)

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(7.5, 3.5),
                                    gridspec_kw={"wspace": 0.35})

    # Panel A: FPR2 cumulative
    ax1.step(range(len(fpr2_cumul)), fpr2_cumul, where="mid",
             color=C_FPR2, linewidth=1.5)
    ax1.fill_between(range(len(fpr2_cumul)), fpr2_cumul, alpha=0.15,
                     step="mid", color=C_FPR2)
    ax1.scatter(range(len(fpr2_cumul)), fpr2_cumul, s=20, color=C_FPR2,
                zorder=5, edgecolors="white", linewidths=0.5)
    ax1.set_xlabel("Experiment number")
    ax1.set_ylabel("Cumulative GPU-hours")
    ax1.set_xticks(range(len(fpr2_cumul)))
    ax1.spines["top"].set_visible(False)
    ax1.spines["right"].set_visible(False)
    ax1.set_title("FPR2 (1 GPU)", fontsize=10, fontweight="bold")
    ax1.text(len(fpr2_cumul) - 1.5, fpr2_cumul[-1] + 1.5,
             f"Total: {fpr2_cumul[-1]:.0f} h", fontsize=7,
             fontweight="bold", color=C_FPR2)
    ax1.text(-0.15, 1.08, "A", transform=ax1.transAxes, fontsize=13,
             fontweight="bold", va="top")

    # Panel B: CDK2 cumulative
    ax2.step(range(len(cdk2_cumul)), cdk2_cumul, where="mid",
             color=C_CDK2, linewidth=1.5)
    ax2.fill_between(range(len(cdk2_cumul)), cdk2_cumul, alpha=0.15,
                     step="mid", color=C_CDK2)
    ax2.scatter(range(len(cdk2_cumul)), cdk2_cumul, s=20, color=C_CDK2,
                zorder=5, edgecolors="white", linewidths=0.5)
    ax2.set_xlabel("Experiment number")
    ax2.set_ylabel("Cumulative GPU-hours")
    ax2.set_xticks(range(0, len(cdk2_cumul), 2))
    ax2.spines["top"].set_visible(False)
    ax2.spines["right"].set_visible(False)
    ax2.set_title("CDK2 (2 GPUs)", fontsize=10, fontweight="bold")
    ax2.text(len(cdk2_cumul) - 2, cdk2_cumul[-1] + 0.5,
             f"Total: {cdk2_cumul[-1]:.1f} h", fontsize=7,
             fontweight="bold", color=C_CDK2)
    ax2.text(-0.15, 1.08, "B", transform=ax2.transAxes, fontsize=13,
             fontweight="bold", va="top")

    fig.tight_layout()
    for fmt in ("png", "svg"):
        fig.savefig(OUTDIR / f"figure_s3_gpu_hours.{fmt}", transparent=False,
                    facecolor="white")
    plt.close(fig)
    print("Figure S3 saved.")


if __name__ == "__main__":
    make_figure1()
    make_figure2()
    make_figure3()
    make_figure_s1()
    make_figure_s2()
    make_figure_s3()
    print("\nAll figures generated in:", OUTDIR)
