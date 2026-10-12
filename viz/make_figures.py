"""
Redraw the thesis charts as clean, colour-blind-safe figures.

Every number comes from the thesis itself (Thesis_Final.docx):
  - data/ahp_criteria_weights.csv  <- Table 4-4
  - data/ahp_final_ranking.csv     <- Table 4-14
  - data/survey_charts.csv         <- data stored inside the thesis's Word charts

All figures use the thesis values unchanged (only sums of Table 4-14 rows).

Run from this folder:   python make_figures.py
Output PNGs are written to ../images/
"""
from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd

HERE = Path(__file__).parent
DATA = HERE / "data"
OUT = HERE.parent / "images"
OUT.mkdir(exist_ok=True)

# Okabe-Ito palette (readable with all common colour-vision deficiencies)
OI = {"orange": "#E69F00", "sky": "#56B4E9", "green": "#009E73", "yellow": "#F0E442",
      "blue": "#0072B2", "vermillion": "#D55E00", "purple": "#CC79A7", "grey": "#7F7F7F"}
GROUP_COL = {"Experts": OI["blue"], "General public": OI["orange"]}

plt.rcParams.update({
    "font.family": "DejaVu Sans", "font.size": 9, "axes.titlesize": 10,
    "axes.titleweight": "bold", "axes.labelsize": 9, "xtick.labelsize": 8,
    "ytick.labelsize": 8, "axes.spines.top": False, "axes.spines.right": False,
    "savefig.dpi": 200, "savefig.bbox": "tight", "figure.facecolor": "white",
})

SOURCE_NOTE = "Redrawn from Thesis_Final (C. G. Shuvo, KUET, 2025); values as reported in the thesis."


def panel_label(ax, letter):
    ax.text(-0.02, 1.06, letter, transform=ax.transAxes, fontsize=11,
            fontweight="bold", ha="right", va="bottom")


def read_csv(name):
    return pd.read_csv(DATA / name, comment="#")


# --------------------------------------------------------------------------
# Figure 1: AHP criteria weights + final priority of each energy source
# --------------------------------------------------------------------------
def fig_ahp():
    w = read_csv("ahp_criteria_weights.csv")
    r = read_csv("ahp_final_ranking.csv").set_index("criterion")
    names = {"SE": "Solar", "BE": "Biomass", "WE": "Wind", "TE": "Tidal"}
    crit_col = [OI["blue"], OI["orange"], OI["green"], OI["purple"]]

    fig, (a, b) = plt.subplots(1, 2, figsize=(9, 3.4),
                               gridspec_kw={"width_ratios": [1, 1.35], "wspace": 0.55})

    # (a) criteria weights
    w = w.iloc[::-1]
    a.barh(w["criterion"], w["weight"], color=crit_col[::-1], height=0.6)
    for y, v in enumerate(w["weight"]):
        a.text(v + 0.01, y, f"{v:.3f}", va="center", fontsize=8)
    a.set_xlim(0, 0.7)
    a.set_xlabel("Criterion weight")
    a.set_title("Criteria weights (thesis)", loc="left")
    panel_label(a, "a")

    # (b) stacked contribution of each criterion to each source's final score
    order = r.sum().sort_values().index  # lowest at bottom -> highest on top
    left = pd.Series(0.0, index=order)
    for c, col in zip(r.index, crit_col):
        vals = r.loc[c, order]
        b.barh([names[s] for s in order], vals, left=left, color=col, height=0.6,
               label=c.split(" (")[0])
        left += vals
    for y, s in enumerate(order):
        b.text(left[s] + 0.008, y, f"{left[s]:.3f}", va="center", fontsize=8, fontweight="bold")
    b.set_xlim(0, 0.56)
    b.set_xlabel("Final AHP priority (sum of weighted scores)")
    b.set_title("Final ranking of renewable sources", loc="left")
    b.legend(frameon=False, fontsize=7.5, loc="lower right", title="Contribution from",
             title_fontsize=7.5)
    panel_label(b, "b")

    fig.text(0.0, -0.06, SOURCE_NOTE + " (a) Table 4-4; (b) Table 4-14.", fontsize=7, color="#555")
    fig.savefig(OUT / "ahp-criteria-weights-and-final-ranking.png")
    plt.close(fig)


# --------------------------------------------------------------------------
# Figure 2: experts vs general public on three shared questions
# --------------------------------------------------------------------------
def grouped_barh(ax, df, question, order=None):
    d = df[df["question"] == question].pivot(index="category", columns="group", values="percent")
    if order is None:
        order = d.mean(axis=1).sort_values().index
    d = d.loc[order]
    y = range(len(d))
    h = 0.38
    for i, g in enumerate(["General public", "Experts"]):
        if g in d:
            ys = [v + (i - 0.5) * h for v in y]
            ax.barh(ys, d[g], height=h, color=GROUP_COL[g], label=g)
            for yy, v in zip(ys, d[g]):
                ax.text(v + 0.8, yy, f"{v:.0f}", va="center", fontsize=7)
    ax.set_yticks(list(y))
    ax.set_yticklabels(d.index)
    ax.set_xlim(0, 50)
    ax.set_xlabel("Share of responses (%)")


def fig_experts_vs_public():
    s = read_csv("survey_charts.csv")
    fig, axes = plt.subplots(1, 3, figsize=(11, 3.3), gridspec_kw={"wspace": 0.95})
    specs = [("Most efficient / preferred source", "Preferred energy source"),
             ("Biggest barrier to adoption", "Biggest barrier to adoption"),
             ("Ways to encourage use", "How to encourage adoption")]
    for ax, (q, title), letter in zip(axes, specs, "abc"):
        grouped_barh(ax, s, q)
        ax.set_title(title, loc="left")
        panel_label(ax, letter)
    h, l = axes[0].get_legend_handles_labels()
    fig.legend(h[::-1], l[::-1], loc="upper center", ncol=2, frameon=False,
               bbox_to_anchor=(0.5, 1.08))
    fig.text(0.0, -0.08, SOURCE_NOTE + " Data from thesis Figs 4-7/16, 4-8/4-9, 4-10/4-11.",
             fontsize=7, color="#555")
    fig.savefig(OUT / "survey-experts-vs-public.png")
    plt.close(fig)


# --------------------------------------------------------------------------
# Figure 3: survey context (single-group questions)
# --------------------------------------------------------------------------
def simple_barh(ax, df, question, color, order=None):
    d = df[df["question"] == question].set_index("category")["percent"]
    d = d.loc[order] if order else d.sort_values()
    ax.barh(d.index, d.values, color=color, height=0.6)
    for yy, v in enumerate(d.values):
        ax.text(v + 0.8, yy, f"{v:.1f}", va="center", fontsize=7)
    ax.set_xlim(0, 65)
    ax.set_xlabel("Share of responses (%)")


def fig_survey_context():
    s = read_csv("survey_charts.csv")
    fig, axes = plt.subplots(2, 2, figsize=(9.5, 5.6), gridspec_kw={"wspace": 0.9, "hspace": 0.7})
    simple_barh(axes[0, 0], s, "Familiarity with renewable energy", GROUP_COL["General public"],
                order=["Not at all", "Somewhat familiar", "Moderate", "Well familiar", "Very familiar"])
    axes[0, 0].set_title("Public: familiarity with renewables", loc="left")
    simple_barh(axes[0, 1], s, "Factors influencing decision to use", GROUP_COL["General public"])
    axes[0, 1].set_title("Public: what drives the decision", loc="left")
    simple_barh(axes[1, 0], s, "Current state of renewable energy", GROUP_COL["Experts"],
                order=["Limited", "Developing", "Developed"])
    axes[1, 0].set_title("Experts: current state of the sector", loc="left")
    simple_barh(axes[1, 1], s, "Challenges to household adoption", GROUP_COL["Experts"])
    axes[1, 1].set_title("Experts: household-level challenges", loc="left")
    for ax, letter in zip(axes.flat, "abcd"):
        panel_label(ax, letter)
    fig.text(0.0, 0.0, SOURCE_NOTE + " Data from thesis Figs 4-3 to 4-6.", fontsize=7, color="#555")
    fig.savefig(OUT / "survey-context.png")
    plt.close(fig)


if __name__ == "__main__":
    fig_ahp()
    fig_experts_vs_public()
    fig_survey_context()
    print("Figures written to", OUT.resolve())
