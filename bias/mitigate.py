from typing import Any, Optional
import pandas as pd
import numpy as np


def _infer_positive_label(series: pd.Series) -> Any:
    vals = series.dropna().unique()
    if len(vals) == 2:
        if set(vals) == {0, 1}:
            return 1
        try:
            return sorted(vals)[-1]
        except Exception:
            return vals[0]
    try:
        return series.mode().iloc[0]
    except Exception:
        return vals[0] if len(vals) else None


def reweigh_dataset(
    df: pd.DataFrame,
    sensitive_col: str,
    target_col: Optional[str] = None,
    positive_label: Optional[Any] = None,
) -> pd.DataFrame:
    dfx = df.copy()
    n = len(dfx)
    if n == 0:
        dfx['sample_weight'] = []
        return dfx

    A = dfx[sensitive_col]
    if target_col is not None and target_col in dfx.columns:
        Y = dfx[target_col]
        pos = positive_label if positive_label is not None else _infer_positive_label(Y)
        # Reweighing: w(a,y) = P(A=a) P(Y=y) / P(A=a, Y=y)
        pA = A.value_counts(normalize=True)
        pY = Y.value_counts(normalize=True)
        pAY = dfx.groupby([sensitive_col, target_col]).size() / n
        weights = []
        for a_val, y_val in zip(A, Y):
            num = pA.get(a_val, 0) * pY.get(y_val, 0)
            den = pAY.get((a_val, y_val), 0)
            w = (num / den) if den > 0 else 1.0
            weights.append(w)
        dfx['sample_weight'] = weights
        # Normalize weights to mean 1 for stability
        mean_w = float(np.mean(dfx['sample_weight']))
        if mean_w > 0:
            dfx['sample_weight'] = dfx['sample_weight'] / mean_w
        return dfx
    else:
        # No target: balance sensitive groups by inverse frequency
        counts = A.value_counts()
        inv_freq = counts.max() / counts
        w_map = inv_freq.to_dict()
        dfx['sample_weight'] = A.map(w_map).astype(float)
        mean_w = float(np.mean(dfx['sample_weight']))
        if mean_w > 0:
            dfx['sample_weight'] = dfx['sample_weight'] / mean_w
        return dfx


def resample_dataset(
    df: pd.DataFrame,
    sensitive_col: str,
    target_col: Optional[str] = None,
    positive_label: Optional[Any] = None,
) -> pd.DataFrame:
    dfx = df.copy()
    n = len(dfx)
    if n == 0:
        return dfx

    if target_col is not None and target_col in dfx.columns:
        # Upsample strata (A=a, Y=y) to reduce disparity without downsampling
        strata = dfx.groupby([sensitive_col, target_col])
        sizes = strata.size()
        max_size = sizes.max()
        samples = []
        rng = np.random.default_rng(42)
        for key, grp in strata:
            k = len(grp)
            if k < max_size:
                need = max_size - k
                add_idx = rng.integers(low=0, high=k, size=need)
                add_rows = grp.iloc[add_idx]
                samples.append(pd.concat([grp, add_rows], axis=0))
            else:
                samples.append(grp)
        return pd.concat(samples, axis=0, ignore_index=True)
    else:
        # No target: balance sensitive groups by upsampling to max group size
        groups = dfx.groupby(sensitive_col)
        sizes = groups.size()
        max_size = sizes.max()
        rng = np.random.default_rng(42)
        outs = []
        for g, grp in groups:
            k = len(grp)
            if k < max_size and k > 0:
                need = max_size - k
                add_idx = rng.integers(low=0, high=k, size=need)
                add_rows = grp.iloc[add_idx]
                outs.append(pd.concat([grp, add_rows], axis=0))
            else:
                outs.append(grp)
        return pd.concat(outs, axis=0, ignore_index=True)
