"""ASR Word Error Rate (WER) filtering module for synthetic audio in ViTrueVoice.

Filters out defective, mumbled, or hallucinated spoofed speech before training.
Complies with Step 1.3 of PLAN.md.
"""

import argparse
import re
import string
from pathlib import Path
from typing import Tuple
import pandas as pd


def clean_text(text: str) -> str:
    """Normalize text by converting to lowercase and stripping punctuation."""
    if not isinstance(text, str):
        return ""
    text = text.lower()
    # Remove punctuation
    text = re.sub(f"[{re.escape(string.punctuation)}]", " ", text)
    # Collapse multiple whitespaces
    return " ".join(text.split())


def compute_word_error_rate(reference: str, hypothesis: str) -> float:
    """Compute Word Error Rate (WER) using Levenshtein distance on word tokens.

    WER = (Substitutions + Deletions + Insertions) / Total Reference Words
    """
    ref_words = clean_text(reference).split()
    hyp_words = clean_text(hypothesis).split()

    len_ref = len(ref_words)
    len_hyp = len(hyp_words)

    if len_ref == 0:
        return 0.0 if len_hyp == 0 else 1.0

    # Dynamic programming table
    dp = [[0] * (len_hyp + 1) for _ in range(len_ref + 1)]

    for i in range(len_ref + 1):
        dp[i][0] = i
    for j in range(len_hyp + 1):
        dp[0][j] = j

    for i in range(1, len_ref + 1):
        for j in range(1, len_hyp + 1):
            if ref_words[i - 1] == hyp_words[j - 1]:
                dp[i][j] = dp[i - 1][j - 1]
            else:
                substitution = dp[i - 1][j - 1] + 1
                insertion = dp[i][j - 1] + 1
                deletion = dp[i - 1][j] + 1
                dp[i][j] = min(substitution, insertion, deletion)

    wer = dp[len_ref][len_hyp] / float(len_ref)
    return round(float(wer), 4)


def filter_manifest_by_wer(
    manifest_df: pd.DataFrame, max_wer: float = 0.35
) -> Tuple[pd.DataFrame, pd.DataFrame]:
    """Filter out manifest rows whose WER exceeds the max_wer threshold.

    Args:
        manifest_df: DataFrame with 'ref_text' and 'hyp_text' columns.
        max_wer: Maximum allowed Word Error Rate (default: 0.35).

    Returns:
        Tuple of (kept_df, rejected_df).
    """
    if "ref_text" not in manifest_df.columns or "hyp_text" not in manifest_df.columns:
        raise ValueError("DataFrame must contain 'ref_text' and 'hyp_text' columns.")

    wers = []
    for _, row in manifest_df.iterrows():
        wer = compute_word_error_rate(str(row["ref_text"]), str(row["hyp_text"]))
        wers.append(wer)

    df_with_wer = manifest_df.copy()
    df_with_wer["wer"] = wers

    kept_df = df_with_wer[df_with_wer["wer"] <= max_wer].copy().reset_index(drop=True)
    rejected_df = df_with_wer[df_with_wer["wer"] > max_wer].copy().reset_index(drop=True)

    return kept_df, rejected_df


def main():
    parser = argparse.ArgumentParser(description="Filter synthetic audio by ASR WER.")
    parser.add_argument("--manifest_csv", type=str, required=True, help="Input CSV manifest")
    parser.add_argument("--output_csv", type=str, required=True, help="Filtered output CSV")
    parser.add_argument("--rejected_csv", type=str, default=None, help="Rejected output CSV")
    parser.add_argument("--max_wer", type=float, default=0.35, help="Maximum allowable WER")

    args = parser.parse_args()
    df = pd.read_csv(args.manifest_csv)

    kept_df, rejected_df = filter_manifest_by_wer(df, max_wer=args.max_wer)
    kept_df.to_csv(args.output_csv, index=False, encoding="utf-8")
    print(f"✅ Đã lọc thành công: Giữ lại {len(kept_df)} mẫu (WER <= {args.max_wer}). Lưu tại: {args.output_csv}")

    if args.rejected_csv:
        rejected_df.to_csv(args.rejected_csv, index=False, encoding="utf-8")
        print(f"🗑️ Đã lưu {len(rejected_df)} mẫu lỗi (WER > {args.max_wer}) tại: {args.rejected_csv}")


if __name__ == "__main__":
    main()
