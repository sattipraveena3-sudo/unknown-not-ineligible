from __future__ import annotations

import argparse
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns
from scipy.stats import binomtest


def paired_bootstrap(values: pd.DataFrame, metric: str, seed: int = 240901, draws: int = 5000) -> tuple[float, float]:
    grouped = values.groupby("base_case_id", sort=False)[metric].mean().to_numpy(float)
    rng = np.random.default_rng(seed)
    estimates = np.empty(draws)
    for i in range(draws):
        estimates[i] = rng.choice(grouped, size=len(grouped), replace=True).mean()
    return tuple(np.quantile(estimates, [0.025, 0.975]))


def mcnemar_exact(frame: pd.DataFrame, a: str, b: str, metric: str) -> dict:
    pivot = frame.pivot_table(index=["model", "protocol", "base_case_id", "masked_field"],
                              columns="condition", values=metric, aggfunc="max").dropna(subset=[a, b])
    n10 = int(((pivot[a] == 1) & (pivot[b] == 0)).sum())
    n01 = int(((pivot[a] == 0) & (pivot[b] == 1)).sum())
    discordant = n10 + n01
    p = 1.0 if discordant == 0 else binomtest(min(n10, n01), discordant, 0.5).pvalue
    return {"condition_a": a, "condition_b": b, "n10": n10, "n01": n01,
            "discordant": discordant, "exact_p": p}


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--scored", default=Path("results/tables/scored_cases.csv"), type=Path)
    parser.add_argument("--tables", default=Path("results/tables"), type=Path)
    parser.add_argument("--figures", default=Path("results/figures"), type=Path)
    args = parser.parse_args()
    frame = pd.read_csv(args.scored)
    args.tables.mkdir(parents=True, exist_ok=True)
    args.figures.mkdir(parents=True, exist_ok=True)

    rows = []
    for keys, group in frame.groupby(["model", "protocol", "condition"]):
        lo, hi = paired_bootstrap(group, "unknown_to_denial")
        rows.append(dict(zip(["model", "protocol", "condition"], keys)) |
                    {"unknown_to_denial_rate": group["unknown_to_denial"].mean(),
                     "ci_low": lo, "ci_high": hi, "n": len(group)})
    summary = pd.DataFrame(rows)
    summary.to_csv(args.tables / "udr_with_ci.csv", index=False)
    pd.DataFrame([mcnemar_exact(frame, "omitted", "explicit_unknown", "unknown_to_denial")]).to_csv(
        args.tables / "mcnemar_primary.csv", index=False)

    sns.set_theme(style="whitegrid")
    chart = sns.catplot(data=summary, x="condition", y="unknown_to_denial_rate",
                        hue="protocol", col="model", kind="bar", col_wrap=2, sharey=True)
    chart.set_axis_labels("Missingness presentation", "Unknown-to-denial rate")
    chart.set(ylim=(0, 1))
    chart.figure.savefig(args.figures / "unknown_to_denial_rate.png", dpi=300, bbox_inches="tight")
    plt.close(chart.figure)


if __name__ == "__main__":
    main()
