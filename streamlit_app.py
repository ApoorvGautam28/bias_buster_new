import io
import pandas as pd
import numpy as np
import streamlit as st

from bias.metrics import compute_bias_report
from bias.mitigate import reweigh_dataset, resample_dataset

st.set_page_config(
    page_title="Bias Buster (Streamlit)",
    page_icon="🛡️",
    layout="wide",
)

st.markdown(
    """
    <style>
    .main {
      padding-top: 1rem;
    }
    .metric-card {
      background: rgba(255,255,255,0.05);
      border: 1px solid rgba(255,255,255,0.08);
      border-radius: 12px;
      padding: 12px 16px;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

st.title("🛡️ Bias Buster")
st.write("Upload a CSV, set columns, analyze fairness metrics, and export a mitigated dataset.")

with st.sidebar:
    st.header("Steps")
    st.write("1) Upload CSV")
    st.write("2) Configure Sensitive / Target / Positive Label")
    st.write("3) Analyze Bias")
    st.write("4) Mitigate & Download")

# --- Upload ---
uploaded = st.file_uploader("Upload CSV", type=["csv"], accept_multiple_files=False)

if uploaded is not None:
    try:
        df = pd.read_csv(uploaded)
    except Exception as e:
        st.error(f"Failed to read CSV: {e}")
        st.stop()

    st.success(f"Loaded: {uploaded.name} — {df.shape[0]} rows x {df.shape[1]} columns")

    # --- Configure columns ---
    with st.expander("Configure Columns", expanded=True):
        cols = list(map(str, df.columns))
        sensitive_col = st.selectbox("Sensitive Attribute", cols, index=0 if cols else None)
        target_col_opt = st.selectbox("Target (optional)", [""] + cols)
        target_col = target_col_opt if target_col_opt else None
        positive_label_text = st.text_input("Positive Label (optional)", placeholder="e.g., 1 or hired")

        positive_label = None
        if positive_label_text:
            try:
                # Attempt to coerce to numeric if appropriate
                if positive_label_text.strip().isdigit() or (
                    positive_label_text.strip().replace('.', '', 1).isdigit() and positive_label_text.count('.') < 2
                ):
                    positive_label = float(positive_label_text)
                    if positive_label.is_integer():
                        positive_label = int(positive_label)
                else:
                    positive_label = positive_label_text
            except Exception:
                positive_label = positive_label_text

    # --- Analyze ---
    analyze = st.button("Analyze Bias", use_container_width=True, type="primary")
    if analyze:
        if not sensitive_col:
            st.error("Select a sensitive attribute.")
            st.stop()
        with st.spinner("Computing bias report..."):
            report = compute_bias_report(df, sensitive_col=sensitive_col, target_col=target_col, positive_label=positive_label)
        if 'error' in report:
            st.error(report['error'])
        else:
            if report.get('warnings'):
                for w in report['warnings']:
                    st.warning(w)
            # Summary metrics
            if report.get('summary'):
                s = report['summary']
                c1, c2, c3, c4 = st.columns(4)
                with c1:
                    st.metric("Overall Positive Rate", s.get('overall_positive_rate', '—'))
                with c2:
                    st.metric("DP Diff", s.get('demographic_parity_diff', '—'))
                with c3:
                    st.metric("Disparate Impact", s.get('disparate_impact', '—'))
                with c4:
                    st.metric("Imbalance Ratio", s.get('imbalance_ratio', '—'))
            # Per-group table
            if report.get('groups'):
                g_rows = []
                for g, m in report['groups'].items():
                    g_rows.append({
                        'group': g,
                        'n': m.get('n'),
                        'share': m.get('share'),
                        'positive_rate': m.get('positive_rate'),
                        'statistical_parity_diff': m.get('statistical_parity_diff'),
                    })
                st.dataframe(pd.DataFrame(g_rows))

    # --- Mitigation ---
    st.divider()
    st.subheader("Mitigation")
    method = st.selectbox("Method", ["reweigh", "resample"])
    do_mitigate = st.button("Mitigate & Prepare Download", use_container_width=True)

    if do_mitigate:
        if not sensitive_col:
            st.error("Select a sensitive attribute.")
            st.stop()
        with st.spinner("Mitigating dataset..."):
            if method == 'reweigh':
                mitigated = reweigh_dataset(df, sensitive_col=sensitive_col, target_col=target_col, positive_label=positive_label)
            else:
                mitigated = resample_dataset(df, sensitive_col=sensitive_col, target_col=target_col, positive_label=positive_label)
        st.success(f"Mitigation complete using {method}.")
        # Prepare download
        buf = io.StringIO()
        mitigated.to_csv(buf, index=False)
        st.download_button(
            label="Download Mitigated CSV",
            data=buf.getvalue(),
            file_name=f"mitigated_{method}.csv",
            mime="text/csv",
            use_container_width=True,
        )
else:
    st.info("Upload a CSV file to begin.")
