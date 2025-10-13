from typing import Any, Dict, Optional
import pandas as pd
import numpy as np


def _infer_positive_label(series: pd.Series) -> Any:
    # Try infer for binary targets
    vals = series.dropna().unique()
    if len(vals) == 2:
        # Prefer 1 over 0 for numeric; else the lexicographically larger
        if set(vals) == {0, 1}:
            return 1
        try:
            # Sort for comparables
            return sorted(vals)[-1]
        except Exception:
            return vals[0]
    # Fallback: assume majority class is positive
    try:
        return series.mode().iloc[0]
    except Exception:
        return vals[0] if len(vals) else None


def compute_bias_report(
    df: pd.DataFrame,
    sensitive_col: str,
    target_col: Optional[str] = None,
    positive_label: Optional[Any] = None,
) -> Dict[str, Any]:
    report: Dict[str, Any] = {
        'sensitive': sensitive_col,
        'target': target_col,
        'groups': {},
        'summary': {},
        'warnings': [],
    }

    if sensitive_col not in df.columns:
        return {'error': f'sensitive column {sensitive_col} missing'}

    # Clean columns
    dfx = df.copy()
    # Cast sensitive to string-ish for grouping display
    sens = dfx[sensitive_col]
    total_n = int(len(dfx))

    # Setup target if provided
    has_target = target_col is not None and target_col in dfx.columns
    if has_target:
        y = dfx[target_col]
        pos = positive_label if positive_label is not None else _infer_positive_label(y)
        report['inferred_positive_label'] = pos
        # Boolean mask for positive outcome
        pos_mask = (y == pos)
        if pos is None:
            has_target = False
            report['warnings'].append('Could not infer positive_label; treating as no-target analysis.')
    else:
        pos = None
        pos_mask = pd.Series(False, index=dfx.index)

    # Per-group stats
    group_stats = []
    for g, idx in sens.groupby(sens).groups.items():
        g_n = int(len(idx))
        g_share = g_n / total_n if total_n else 0.0
        entry = {
            'n': g_n,
            'share': round(float(g_share), 6),
        }
        if has_target:
            g_pos_rate = float(pos_mask.loc[idx].mean()) if g_n else 0.0
            entry['positive_rate'] = round(g_pos_rate, 6)
        group_stats.append((g, entry))

    # Summary metrics
    if has_target:
        overall_pos_rate = float(pos_mask.mean()) if total_n else 0.0
        rates = [e[1]['positive_rate'] for e in group_stats]
        if rates:
            max_rate = max(rates)
            min_rate = min(rates)
            dp_diff = max_rate - min_rate  # demographic parity difference
            disp_impact = (min_rate / max_rate) if max_rate > 0 else np.nan
        else:
            max_rate = min_rate = dp_diff = disp_impact = np.nan
        report['summary'] = {
            'overall_positive_rate': round(overall_pos_rate, 6),
            'demographic_parity_diff': round(float(dp_diff), 6) if pd.notna(dp_diff) else None,
            'disparate_impact': round(float(disp_impact), 6) if pd.notna(disp_impact) else None,
            'max_group_positive_rate': round(float(max_rate), 6) if pd.notna(max_rate) else None,
            'min_group_positive_rate': round(float(min_rate), 6) if pd.notna(min_rate) else None,
        }
        # Statistical parity difference per group: group - overall
        for g, entry in group_stats:
            pr = entry.get('positive_rate', np.nan)
            entry['statistical_parity_diff'] = round(float(pr - overall_pos_rate), 6) if pd.notna(pr) else None
            report['groups'][str(g)] = entry
    else:
        # No-target analysis: just distributional imbalance
        for g, entry in group_stats:
            report['groups'][str(g)] = entry
        report['summary'] = {
            'imbalance_ratio': round(float(max([e[1]['share'] for e in group_stats]) / min([e[1]['share'] for e in group_stats])) , 6) if len(group_stats) > 1 and min([e[1]['share'] for e in group_stats]) > 0 else None
        }

    return report
