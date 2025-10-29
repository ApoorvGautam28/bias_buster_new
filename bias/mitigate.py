from typing import Any, Optional, Dict, Union
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


def adjust_values(
    df: pd.DataFrame,
    sensitive_col: str,
    target_col: str,
    adjustment_factors: Optional[Dict[Any, float]] = None,
    method: str = 'multiply',
    inplace: bool = False,
    modify_original: bool = False,
    threshold: float = 0.5
) -> pd.DataFrame:
    """
    Adjust target values based on sensitive attribute to reduce bias.
    
    Args:
        df: Input DataFrame
        sensitive_col: Name of the sensitive attribute column
        target_col: Name of the target column to adjust
        adjustment_factors: Dictionary mapping sensitive attribute values to adjustment factors.
                          If None, will automatically calculate to equalize group means.
        method: 'multiply' or 'add' - how to apply the adjustment factors
        inplace: If True, modifies the input DataFrame directly
        
    Returns:
        DataFrame with adjusted target values
    """
    if not inplace:
        df = df.copy()
    
    if target_col not in df.columns:
        raise ValueError(f"Target column '{target_col}' not found in DataFrame")
    
    if sensitive_col not in df.columns:
        raise ValueError(f"Sensitive column '{sensitive_col}' not found in DataFrame")
    
    # Convert target to numeric if it's not already
    if not np.issubdtype(df[target_col].dtype, np.number):
        if not inplace:
            df = df.copy()

    # For binary classification with original modification, we'll use a different approach
    if modify_original and target_col == 'Hired':
        # Calculate the target number of hires per group for equal representation
        total_hires = df[target_col].sum()
        group_counts = df[sensitive_col].value_counts()
        target_hires = {}
        
        # Calculate target hires to balance the groups
        for group, count in group_counts.items():
            # Aim for proportional representation based on group size
            target_hires[group] = int(round((count / len(df)) * total_hires))
        
        # Sort candidates within each group by their scores (Technical_Score + Interview_Score)
        df['total_score'] = df['Technical_Score'] + df['Interview_Score']
        df_sorted = df.sort_values(by='total_score', ascending=False)
        
        # Reset the Hired column
        df[target_col] = 0
        
        # Select top candidates from each group to meet the target
        for group, target in target_hires.items():
            group_indices = df_sorted[df_sorted[sensitive_col] == group].index[:target]
            df.loc[group_indices, target_col] = 1
        
        # Clean up
        df = df.drop(columns=['total_score'])
        
        print(f"\nOriginal 'Hired' values have been updated to reduce bias.")
        print("Adjusted hiring counts by group:")
        print(df.groupby(sensitive_col)[target_col].value_counts().unstack())
        
        return df
    
    # Original adjustment logic for non-binary or non-Hired targets
    if adjustment_factors is None:
        group_means = df.groupby(sensitive_col)[target_col].mean()
        overall_mean = df[target_col].mean()
        adjustment_factors = (overall_mean / group_means).to_dict()

    # Apply adjustments
    adjusted = []
    for _, row in df.iterrows():
        val = row[target_col]
        factor = adjustment_factors.get(row[sensitive_col], 1.0)
        
        if method == 'multiply':
            adjusted_val = val * factor
        else:  # 'add'
            adjusted_val = val + factor
        adjusted.append(adjusted_val)

    if inplace:
        df[target_col] = adjusted
    else:
        df = df.copy()
        df[target_col + '_adjusted'] = adjusted
    
    return df
