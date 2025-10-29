import os
import uuid
from flask import Flask, request, jsonify, send_from_directory, render_template
from werkzeug.utils import secure_filename
import pandas as pd

from bias.metrics import compute_bias_report
from bias.mitigate import reweigh_dataset, resample_dataset, adjust_values

APP_ROOT = os.path.dirname(os.path.abspath(__file__))
# Use writable /tmp on Vercel; otherwise default to project directory
if os.environ.get('VERCEL'):
    BASE_DIR = "/tmp/bias-buster"
else:
    BASE_DIR = APP_ROOT
UPLOAD_DIR = os.path.join(BASE_DIR, 'uploads')
OUTPUT_DIR = os.path.join(BASE_DIR, 'outputs')
ALLOWED_EXTENSIONS = {'.csv'}

os.makedirs(UPLOAD_DIR, exist_ok=True)
os.makedirs(OUTPUT_DIR, exist_ok=True)

app = Flask(__name__, template_folder='templates', static_folder='static')

# In-memory registry of uploaded files for this server session
REGISTRY = {}


def allowed_file(filename: str):
    return os.path.splitext(filename)[1].lower() in ALLOWED_EXTENSIONS


@app.route('/')
def index():
    return render_template('index.html')


@app.route('/upload', methods=['POST'])
def upload():
    if 'file' not in request.files:
        return jsonify({'error': 'No file part'}), 400
    f = request.files['file']
    if f.filename == '':
        return jsonify({'error': 'No selected file'}), 400
    if not allowed_file(f.filename):
        return jsonify({'error': 'Only .csv files are supported'}), 400

    filename = secure_filename(f.filename)
    file_id = str(uuid.uuid4())
    save_name = f"{file_id}_{filename}"
    save_path = os.path.join(UPLOAD_DIR, save_name)
    f.save(save_path)

    # Try reading once to validate CSV
    try:
        df = pd.read_csv(save_path)
    except Exception as e:
        os.remove(save_path)
        return jsonify({'error': f'Failed to read CSV: {e}'}), 400

    # Save metadata
    REGISTRY[file_id] = {
        'path': save_path,
        'filename': filename,
        'n_rows': int(df.shape[0]),
        'n_cols': int(df.shape[1]),
        'columns': list(df.columns.astype(str)),
    }

    return jsonify({'file_id': file_id, **REGISTRY[file_id]}), 200


@app.route('/columns', methods=['GET'])
def columns():
    file_id = request.args.get('file_id')
    if not file_id or file_id not in REGISTRY:
        return jsonify({'error': 'Invalid file_id'}), 400
    meta = REGISTRY[file_id]
    return jsonify({'columns': meta['columns'], 'n_rows': meta['n_rows'], 'n_cols': meta['n_cols'], 'filename': meta['filename']}), 200


@app.route('/analyze', methods=['POST'])
def analyze():
    data = request.get_json(force=True)
    file_id = data.get('file_id')
    sens_col = data.get('sensitive')
    target_col = data.get('target')  # optional
    positive_label = data.get('positive_label')  # optional, for classification datasets

    if not file_id or file_id not in REGISTRY:
        return jsonify({'error': 'Invalid file_id'}), 400
    if not sens_col:
        return jsonify({'error': 'Missing sensitive attribute column'}), 400

    df = pd.read_csv(REGISTRY[file_id]['path'])
    if sens_col not in df.columns:
        return jsonify({'error': f'Column {sens_col} not in dataset'}), 400
    if target_col and target_col not in df.columns:
        return jsonify({'error': f'Target column {target_col} not in dataset'}), 400

    report = compute_bias_report(df, sensitive_col=sens_col, target_col=target_col, positive_label=positive_label)
    return jsonify(report), 200


@app.route('/mitigate', methods=['POST'])
def mitigate():
    data = request.get_json(force=True)
    file_id = data.get('file_id')
    sens_col = data.get('sensitive')
    target_col = data.get('target')
    positive_label = data.get('positive_label')
    method = (data.get('method') or 'reweigh').lower()

    if not file_id or file_id not in REGISTRY:
        return jsonify({'error': 'Invalid file_id'}), 400
    if not sens_col:
        return jsonify({'error': 'Missing sensitive attribute column'}), 400

    df = pd.read_csv(REGISTRY[file_id]['path'])

    if method == 'reweigh':
        mitigated = reweigh_dataset(df, sensitive_col=sens_col, target_col=target_col, positive_label=positive_label)
        out_name = f"{file_id}_mitigated_reweigh.csv"
        out_path = os.path.join(OUTPUT_DIR, out_name)
        mitigated.to_csv(out_path, index=False)
        return jsonify({'download': f"/download/{out_name}", 'method': 'reweigh'}), 200
    elif method == 'resample':
        mitigated = resample_dataset(df, sensitive_col=sens_col, target_col=target_col, positive_label=positive_label)
        out_name = f"{file_id}_mitigated_resample.csv"
        out_path = os.path.join(OUTPUT_DIR, out_name)
        mitigated.to_csv(out_path, index=False)
        return jsonify({'download': f"/download/{out_name}", 'method': 'resample'}), 200
    elif method == 'adjust':
        if not target_col:
            return jsonify({'error': 'Target column is required for adjust method'}), 400
        adjustment_method = data.get('adjustment_method', 'multiply')
        try:
            mitigated = adjust_values(
                df, 
                sensitive_col=sens_col, 
                target_col=target_col,
                method=adjustment_method
            )
            out_name = f"{file_id}_adjusted_{adjustment_method}.csv"
            out_path = os.path.join(OUTPUT_DIR, out_name)
            mitigated.to_csv(out_path, index=False)
            return jsonify({
                'download': f"/download/{out_name}", 
                'method': f'adjust_{adjustment_method}'
            }), 200
        except Exception as e:
            return jsonify({'error': f'Adjustment failed: {str(e)}'}), 400
    else:
        return jsonify({'error': 'Unknown method. Use reweigh, resample, or adjust.'}), 400


@app.route('/download/<path:filename>', methods=['GET'])
def download(filename):
    return send_from_directory(OUTPUT_DIR, filename, as_attachment=True)


if __name__ == '__main__':
    app.run(host='127.0.0.1', port=5000, debug=True)
