"""Quality-metrics harness for ClaimGuard AI (stdlib only).

Computes accuracy, a confusion matrix, and per-class precision/recall/F1 for a
categorical column (default: claim_status) by comparing predictions against a
labeled gold file. Writes a machine-readable results.json.

Usage:
    python metrics.py --gold ../dataset/sample_claims.csv \
                      --pred ../code/output.csv \
                      --column claim_status

Join key: (user_id, image_paths); falls back to row order if keys don't align.
No numbers are hard-coded — everything is computed from the files you pass.
"""

import argparse
import csv
import json
from collections import defaultdict


def load_rows(path):
    with open(path, newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def build_key(row):
    return (str(row.get("user_id", "")).strip(),
            str(row.get("image_paths", "")).strip())


def align(gold, pred, column):
    """Return list of (gold_value, pred_value) pairs."""
    pred_by_key = {}
    for r in pred:
        pred_by_key.setdefault(build_key(r), r)

    pairs = []
    used_key_join = all(build_key(g) in pred_by_key for g in gold) and len(pred) >= len(gold)

    if used_key_join:
        for g in gold:
            p = pred_by_key[build_key(g)]
            pairs.append((g.get(column, "").strip(), p.get(column, "").strip()))
    else:
        # Fall back to row order.
        for g, p in zip(gold, pred):
            pairs.append((g.get(column, "").strip(), p.get(column, "").strip()))

    return pairs, ("key(user_id,image_paths)" if used_key_join else "row-order")


def evaluate(pairs):
    labels = sorted({g for g, _ in pairs} | {p for _, p in pairs})
    idx = {l: i for i, l in enumerate(labels)}

    confusion = [[0] * len(labels) for _ in labels]
    correct = 0
    for g, p in pairs:
        confusion[idx[g]][idx[p]] += 1
        if g == p:
            correct += 1

    total = len(pairs)
    accuracy = correct / total if total else 0.0

    per_class = {}
    tp_sum = fp_sum = fn_sum = 0
    macro_f1 = 0.0
    weighted_f1 = 0.0
    support_total = 0

    for l in labels:
        i = idx[l]
        tp = confusion[i][i]
        fp = sum(confusion[r][i] for r in range(len(labels))) - tp
        fn = sum(confusion[i]) - tp
        support = sum(confusion[i])

        precision = tp / (tp + fp) if (tp + fp) else 0.0
        recall = tp / (tp + fn) if (tp + fn) else 0.0
        f1 = (2 * precision * recall / (precision + recall)
              if (precision + recall) else 0.0)

        per_class[l] = {
            "precision": round(precision, 4),
            "recall": round(recall, 4),
            "f1": round(f1, 4),
            "support": support,
        }
        macro_f1 += f1
        weighted_f1 += f1 * support
        support_total += support
        tp_sum += tp
        fp_sum += fp
        fn_sum += fn

    macro_f1 = macro_f1 / len(labels) if labels else 0.0
    weighted_f1 = weighted_f1 / support_total if support_total else 0.0

    return {
        "labels": labels,
        "confusion_matrix": confusion,
        "accuracy": round(accuracy, 4),
        "correct": correct,
        "total": total,
        "macro_f1": round(macro_f1, 4),
        "weighted_f1": round(weighted_f1, 4),
        "per_class": per_class,
    }


def print_report(res, join_mode, column):
    labels = res["labels"]
    print("=" * 64)
    print(f"ClaimGuard AI - metrics for '{column}'  (join: {join_mode})")
    print("=" * 64)
    print(f"Accuracy    : {res['accuracy']:.4f} "
          f"({res['correct']}/{res['total']})")
    print(f"Macro-F1    : {res['macro_f1']:.4f}")
    print(f"Weighted-F1 : {res['weighted_f1']:.4f}")

    print("\nConfusion matrix (rows = gold, cols = predicted):")
    width = max([len(l) for l in labels] + [5])
    header = " " * (width + 2) + "".join(f"{l[:width]:>{width+2}}" for l in labels)
    print(header)
    for i, l in enumerate(labels):
        row = "".join(f"{res['confusion_matrix'][i][j]:>{width+2}}"
                      for j in range(len(labels)))
        print(f"{l:>{width}}  {row}")

    print("\nPer-class:")
    print(f"{'label':>{width}}  {'prec':>6} {'rec':>6} {'f1':>6} {'support':>8}")
    for l in labels:
        m = res["per_class"][l]
        print(f"{l:>{width}}  {m['precision']:>6.3f} {m['recall']:>6.3f} "
              f"{m['f1']:>6.3f} {m['support']:>8}")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--gold", required=True, help="labeled CSV (e.g. sample_claims.csv)")
    ap.add_argument("--pred", required=True, help="predictions CSV (e.g. output.csv)")
    ap.add_argument("--column", default="claim_status", help="column to score")
    ap.add_argument("--out", default="results.json")
    args = ap.parse_args()

    gold = load_rows(args.gold)
    pred = load_rows(args.pred)

    if args.column not in (gold[0] if gold else {}):
        raise SystemExit(
            f"Gold file has no '{args.column}' column — it must be labeled. "
            f"Columns: {list(gold[0].keys()) if gold else []}"
        )

    pairs, join_mode = align(gold, pred, args.column)
    res = evaluate(pairs)
    res["join_mode"] = join_mode
    res["column"] = args.column

    print_report(res, join_mode, args.column)

    with open(args.out, "w", encoding="utf-8") as f:
        json.dump(res, f, indent=2)
    print(f"\nWrote {args.out}")


if __name__ == "__main__":
    main()
