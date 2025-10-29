// Initialize AOS (Animate On Scroll)
if (typeof AOS !== 'undefined') {
  AOS.init({
    duration: 800,
    easing: 'ease-out-cubic',
    once: true,
    offset: 50
  });
}

// State management
let state = { 
  file_id: null, 
  columns: [],
  isAnalyzing: false,
  analysisComplete: false
};

// DOM Elements
const uploadForm = document.getElementById('uploadForm');
const fileInput = document.getElementById('fileInput');
const fileMeta = document.getElementById('fileMeta');
const configPanel = document.getElementById('configPanel');
const sensitiveSelect = document.getElementById('sensitiveSelect');
const targetSelect = document.getElementById('targetSelect');
const positiveLabelInput = document.getElementById('positiveLabel');
const analyzeBtn = document.getElementById('analyzeBtn');
const methodSelect = document.getElementById('methodSelect');
const positiveLabelContainer = document.getElementById('positiveLabelContainer');
const resultsContent = document.getElementById('resultsContent');
const downloadPanel = document.getElementById('downloadPanel');
const downloadLink = document.getElementById('downloadLink');

// Initialize GSAP animations
gsap.registerPlugin(ScrollTrigger);

// Initialize page animations
function initAnimations() {
  // Animate hero section
  gsap.from('.hero-content', {
    y: 50,
    opacity: 0,
    duration: 1,
    delay: 0.3,
    ease: 'power3.out'
  });

  // Animate upload section
  gsap.from('.upload-section', {
    y: 30,
    opacity: 0,
    duration: 0.8,
    delay: 0.6,
    ease: 'back.out(1.7)'
  });
}

// Initialize tooltips
function initTooltips() {
  const tooltips = document.querySelectorAll('[data-tooltip]');
  tooltips.forEach(tooltip => {
    const tooltipText = tooltip.getAttribute('data-tooltip');
    const tooltipElement = document.createElement('div');
    tooltipElement.className = 'tooltip';
    tooltipElement.textContent = tooltipText;
    tooltip.appendChild(tooltipElement);
  });
}

// File input handling
function setupFileInput() {
  if (fileInput) {
    fileInput.addEventListener('change', (e) => {
      const file = e.target.files[0];
      if (file) {
        fileMeta.innerHTML = `
          <svg xmlns="http://www.w3.org/2000/svg" class="h-4 w-4 text-emerald-400" viewBox="0 0 20 20" fill="currentColor">
            <path fill-rule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clip-rule="evenodd" />
          </svg>
          <span>${file.name} (${(file.size / 1024 / 1024).toFixed(2)} MB)</span>
        `;
        
        // Show config panel
        gsap.to(configPanel, {
          opacity: 1,
          height: 'auto',
          duration: 0.5,
          onComplete: () => {
            configPanel.classList.remove('hidden');
            loadFileData(file);
          }
        });
      }
    });
  }
}

// Load file data and populate selects
function loadFileData(file) {
  // In a real app, you would parse the file and get column names
  // For now, we'll simulate this with a timeout
  setTimeout(() => {
    // Simulate getting columns from the file
    const columns = ['Gender', 'Age', 'Experience', 'Salary', 'Hired'];
    
    // Populate sensitive attribute and target column selects
    populateSelect(sensitiveSelect, columns);
    populateSelect(targetSelect, ['', ...columns]);
    
    // Show the config panel with animation
    gsap.to(configPanel, {
      opacity: 1,
      y: 0,
      duration: 0.5
    });
  }, 500);
}

// Populate select element with options
function populateSelect(selectElement, options) {
  selectElement.innerHTML = '';
  options.forEach(option => {
    const optionElement = document.createElement('option');
    optionElement.value = option;
    optionElement.textContent = option || '-- Select --';
    selectElement.appendChild(optionElement);
  });
}

// Toggle positive label input based on target selection
function setupTargetSelect() {
  if (targetSelect) {
    targetSelect.addEventListener('change', (e) => {
      if (e.target.value) {
        positiveLabelContainer.style.display = 'block';
        gsap.from(positiveLabelContainer, {
          opacity: 0,
          y: 10,
          duration: 0.3
        });
      } else {
        gsap.to(positiveLabelContainer, {
          opacity: 0,
          y: -10,
          duration: 0.2,
          onComplete: () => {
            positiveLabelContainer.style.display = 'none';
          }
        });
      }
    });
  }
}

// Smooth scroll for anchor links
document.querySelectorAll('a[href^="#"]').forEach(anchor => {
  anchor.addEventListener('click', function (e) {
    e.preventDefault();
    const target = document.querySelector(this.getAttribute('href'));
    if (target) {
      target.scrollIntoView({
        behavior: 'smooth',
        block: 'start'
      });
    }
  });
});

// Add hover effect to glass cards
document.querySelectorAll('.glass').forEach(card => {
  card.addEventListener('mousemove', (e) => {
    const rect = card.getBoundingClientRect();
    const x = e.clientX - rect.left;
    const y = e.clientY - rect.top;
    
    card.style.setProperty('--mouse-x', `${x}px`);
    card.style.setProperty('--mouse-y', `${y}px`);
  });
});

// Additional DOM Elements
const mitigateBtn = document.getElementById('mitigateBtn');
const resultsDiv = document.getElementById('results');
const adjustOptions = document.getElementById('adjustOptions');
const modifyOriginal = document.getElementById('modifyOriginal');
const thresholdContainer = document.getElementById('thresholdContainer');
const thresholdInput = document.getElementById('threshold');

// Toggle adjust options based on method selection
function setupMethodSelect() {
  if (methodSelect) {
    methodSelect.addEventListener('change', () => {
      if (methodSelect.value === 'adjust') {
        adjustOptions.classList.remove('hidden');
      } else {
        adjustOptions.classList.add('hidden');
      }
    });
  }
}

// Initialize everything when the DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
  initAnimations();
  initTooltips();
  setupFileInput();
  setupTargetSelect();
  setupMethodSelect();
  
  // Debug log
  console.log('DOM elements initialized');
});

// Toggle threshold input based on modifyOriginal checkbox
modifyOriginal.addEventListener('change', () => {
  if (modifyOriginal.checked) {
    thresholdContainer.classList.remove('hidden');
  } else {
    thresholdContainer.classList.add('hidden');
  }
});

function setResults(html) {
  resultsDiv.innerHTML = html;
}

function optionHtml(v) { return `<option value="${v}">${v}</option>`; }

uploadForm.addEventListener('submit', async (e) => {
  e.preventDefault();
  console.log('Form submitted');
  
  const file = fileInput.files[0];
  if (!file) { 
    console.log('No file selected');
    alert('Please select a CSV file first'); 
    return; 
  }
  
  console.log('Selected file:', file.name, 'Size:', file.size, 'bytes');
  
  const form = new FormData();
  form.append('file', file);
  
  console.log('FormData created, sending request...');
  setResults('<p class="text-sm">Uploading file...</p>');
  
  try {
    const response = await fetch('/upload', { 
      method: 'POST', 
      body: form,
      // Don't set Content-Type header - let the browser set it with the correct boundary
    });
    
    console.log('Response status:', response.status);
    
    if (!response.ok) {
      const errorData = await response.json().catch(() => ({}));
      console.error('Upload failed:', errorData);
      throw new Error(errorData.error || `Upload failed with status ${response.status}`);
    }
    
    const data = await response.json();
    console.log('Upload successful:', data);
    
    state.file_id = data.file_id;
    fileMeta.textContent = `${data.filename} — ${data.n_rows} rows, ${data.n_cols} cols`;
    
    // Load columns
    console.log('Fetching columns...');
    const colResp = await fetch(`/columns?file_id=${state.file_id}`);
    if (!colResp.ok) throw new Error('Failed to load columns');
    
    const colData = await colResp.json();
    state.columns = colData.columns || [];
    console.log('Loaded columns:', state.columns);
    
    // Update UI
    sensitiveSelect.innerHTML = state.columns.map(optionHtml).join('');
    targetSelect.innerHTML = '<option value="">None</option>' + state.columns.map(optionHtml).join('');
    
    configPanel.classList.remove('hidden');
    setResults('<p class="text-sm text-green-400">✓ File uploaded successfully</p>');
    downloadPanel.classList.add('hidden');
    
  } catch (err) {
    console.error('Upload error:', err);
    setResults(`
      <div class="bg-red-900/50 border border-red-700 rounded-lg p-4">
        <p class="font-medium text-red-200">Upload failed</p>
        <p class="text-sm text-red-300 mt-1">${err.message}</p>
        <p class="text-xs text-red-400 mt-2">Check the console for more details</p>
      </div>
    `);
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

  // Get bias correction options
  const modify_original = method === 'adjust' ? modifyOriginal.checked : false;
  const threshold = method === 'adjust' && modify_original ? parseFloat(thresholdInput.value) : 0.5;

  setResults('<p class="text-sm">Mitigating...</p>');
  downloadPanel.classList.add('hidden');
  
  try {
    const payload = {
      file_id: state.file_id,
      sensitive,
      target,
      method,
      positive_label,
      modify_original,
      threshold
    };

    if (method === 'adjust') {
      payload.adjustment_method = 'multiply';
    }

    const resp = await fetch('/mitigate', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload)
    });
    
    const data = await resp.json();
    if (!resp.ok) throw new Error(data.error || 'Mitigation failed');
    
    // Show results with statistics if available
    let resultsHtml = `<p class='text-sm'>Mitigation complete using <b>${data.method}</b>.</p>`;
    if (data.stats) {
      resultsHtml += `
        <div class="mt-2 p-3 bg-white/5 rounded-lg text-sm">
          <p>Original dataset: ${data.stats.original_size} rows, ${data.stats.original_positive} positive</p>
          <p>Mitigated dataset: ${data.stats.mitigated_size} rows, ${data.stats.mitigated_positive} positive</p>
        </div>
      `;
    }
    setResults(resultsHtml);
    
    downloadLink.href = data.download;
    downloadPanel.classList.remove('hidden');
  } catch (err) {
    console.error('Mitigation error:', err);
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
