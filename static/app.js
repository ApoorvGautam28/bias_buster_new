let state = { file_id: null, columns: [] };

const uploadForm = document.getElementById('uploadForm');
const fileInput = document.getElementById('fileInput');
const fileMeta = document.getElementById('fileMeta');
const configPanel = document.getElementById('configPanel');
const sensitiveSelect = document.getElementById('sensitiveSelect');
const targetSelect = document.getElementById('targetSelect');
const positiveLabelInput = document.getElementById('positiveLabel');
const analyzeBtn = document.getElementById('analyzeBtn');
const methodSelect = document.getElementById('methodSelect');
const mitigateBtn = document.getElementById('mitigateBtn');
const resultsDiv = document.getElementById('results');
const downloadPanel = document.getElementById('downloadPanel');
const downloadLink = document.getElementById('downloadLink');

function setResults(html) {
  resultsDiv.innerHTML = html;
}

function optionHtml(v) { return `<option value="${v}">${v}</option>`; }

uploadForm.addEventListener('submit', async (e) => {
  e.preventDefault();
  const file = fileInput.files[0];
  if (!file) { alert('Select a CSV file'); return; }
  const form = new FormData();
  form.append('file', file);
  setResults('<p class="text-sm">Uploading...</p>');
  try {
    const resp = await fetch('/upload', { method: 'POST', body: form });
    const data = await resp.json();
    if (!resp.ok) throw new Error(data.error || 'Upload failed');
    state.file_id = data.file_id;
    fileMeta.textContent = `${data.filename} — ${data.n_rows} rows, ${data.n_cols} cols`;
    const colResp = await fetch(`/columns?file_id=${state.file_id}`);
    const colData = await colResp.json();
    state.columns = colData.columns || [];
    sensitiveSelect.innerHTML = state.columns.map(optionHtml).join('');
    targetSelect.innerHTML = '<option value="">None</option>' + state.columns.map(optionHtml).join('');
    configPanel.classList.remove('hidden');
    setResults('<p class="text-sm">File uploaded. Configure columns, then Analyze.</p>');
    downloadPanel.classList.add('hidden');
  } catch (err) {
    setResults(`<p class='text-red-300 text-sm'>${err.message}</p>`);
  }
});

analyzeBtn.addEventListener('click', async () => {
  if (!state.file_id) { alert('Upload a file first'); return; }
  const sensitive = sensitiveSelect.value;
  const target = targetSelect.value || null;
  const positive_label_raw = positiveLabelInput.value;
  let positive_label = positive_label_raw || null;
  // Try to parse numbers
  if (positive_label !== null && !isNaN(Number(positive_label))) {
    positive_label = Number(positive_label);
  }

  setResults('<p class="text-sm">Analyzing...</p>');
  try {
    const resp = await fetch('/analyze', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ file_id: state.file_id, sensitive, target, positive_label })
    });
    const data = await resp.json();
    if (!resp.ok) throw new Error(data.error || 'Analysis failed');
    renderReport(data);
  } catch (err) {
    setResults(`<p class='text-red-300 text-sm'>${err.message}</p>`);
  }
});

mitigateBtn.addEventListener('click', async () => {
  if (!state.file_id) { alert('Upload a file first'); return; }
  const sensitive = sensitiveSelect.value;
  const target = targetSelect.value || null;
  const method = methodSelect.value;
  const positive_label_raw = positiveLabelInput.value;
  let positive_label = positive_label_raw || null;
  if (positive_label !== null && !isNaN(Number(positive_label))) {
    positive_label = Number(positive_label);
  }

  setResults('<p class="text-sm">Mitigating...</p>');
  downloadPanel.classList.add('hidden');
  try {
    const resp = await fetch('/mitigate', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ file_id: state.file_id, sensitive, target, method, positive_label })
    });
    const data = await resp.json();
    if (!resp.ok) throw new Error(data.error || 'Mitigation failed');
    setResults(`<p class='text-sm'>Mitigation complete using <b>${data.method}</b>.</p>`);
    downloadLink.href = data.download;
    downloadPanel.classList.remove('hidden');
  } catch (err) {
    setResults(`<p class='text-red-300 text-sm'>${err.message}</p>`);
  }
});

function renderReport(rep) {
  const parts = [];
  if (rep.warnings && rep.warnings.length) {
    parts.push(`<div class='text-amber-300 text-xs'>${rep.warnings.join('<br/>')}</div>`);
  }
  if (rep.summary) {
    parts.push(`
      <div class='rounded-lg border border-white/10 p-3 bg-white/5'>
        <div class='font-semibold mb-1'>Summary</div>
        <div class='grid grid-cols-2 gap-2 text-sm'>
          ${rep.summary.overall_positive_rate !== undefined ? `<div>Overall Positive Rate: <b>${rep.summary.overall_positive_rate}</b></div>` : ''}
          ${rep.summary.demographic_parity_diff !== undefined && rep.summary.demographic_parity_diff !== null ? `<div>DP Diff: <b>${rep.summary.demographic_parity_diff}</b></div>` : ''}
          ${rep.summary.disparate_impact !== undefined && rep.summary.disparate_impact !== null ? `<div>Disparate Impact: <b>${rep.summary.disparate_impact}</b></div>` : ''}
          ${rep.summary.imbalance_ratio !== undefined && rep.summary.imbalance_ratio !== null ? `<div>Imbalance Ratio: <b>${rep.summary.imbalance_ratio}</b></div>` : ''}
        </div>
      </div>
    `);
  }
  if (rep.groups) {
    const rows = Object.entries(rep.groups).map(([g, m]) => `
      <tr>
        <td class='py-1 pr-3 text-slate-200'>${g}</td>
        <td class='py-1 pr-3 text-slate-300'>${m.n}</td>
        <td class='py-1 pr-3 text-slate-300'>${m.share ?? ''}</td>
        <td class='py-1 pr-3 text-slate-300'>${m.positive_rate ?? ''}</td>
        <td class='py-1 pr-3 text-slate-300'>${m.statistical_parity_diff ?? ''}</td>
      </tr>
    `).join('');
    parts.push(`
      <div class='mt-3'>
        <div class='font-semibold mb-2'>Per-group metrics</div>
        <div class='overflow-auto'>
          <table class='min-w-full text-sm'>
            <thead class='text-slate-300'>
              <tr>
                <th class='text-left pr-3'>Group</th>
                <th class='text-left pr-3'>N</th>
                <th class='text-left pr-3'>Share</th>
                <th class='text-left pr-3'>Positive Rate</th>
                <th class='text-left pr-3'>Statistical Parity Diff</th>
              </tr>
            </thead>
            <tbody>${rows}</tbody>
          </table>
        </div>
      </div>
    `);
  }
  setResults(parts.join(''));
}
