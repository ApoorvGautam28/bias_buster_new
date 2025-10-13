# Bias Buster

A Streamlit app to analyze fairness metrics on a CSV dataset and optionally mitigate bias via reweighing or resampling.

## Run Locally

```bash
pip install -r requirements.txt
streamlit run streamlit_app.py
```

Then open the URL Streamlit prints (usually http://localhost:8501).

## Deploy on Streamlit Community Cloud

1. Push this repo to GitHub.
2. Go to https://share.streamlit.io/ and click "New app".
3. Select your repo/branch and set Main file path to `streamlit_app.py`.
4. (Optional) Python version is pinned via `runtime.txt` to Python 3.11.
5. Deploy.

## Notes

- Uploads and processing happen in-memory in `streamlit_app.py`.
- The Flask app in `app.py` is not used for Streamlit Cloud; it was for a separate Flask UI/server deployment.
