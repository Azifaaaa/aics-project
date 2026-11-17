/* CipherShield — Dataset Insights Charts JS */

async function loadInsights() {
  try {
    const [statsRes, evalRes] = await Promise.all([
      fetch('/api/stats').then(r => r.json()).catch(() => ({})),
      fetch('/api/eval').then(r => r.json()).catch(() => ({})),
    ]);

    const d = statsRes.dataset || {};

    if (d.available) {
      // Key stats
      setVal('iTotal',    d.total_records || 0);
      setVal('iHam',      d.ham           || 0);
      setVal('iSpam',     d.spam          || 0);
      setVal('iPhishing', d.phishing      || 0);
      setVal('iUrls',     d.url_containing|| 0);

      // Class distribution pie chart
      buildClassChart(d.ham || 0, d.spam || 0, d.phishing || 0);

      // Source pie chart
      buildSourceChart(d.original_records || 0, d.supplementary_records || 0);

      // Original dataset bar
      document.getElementById('origDist').innerHTML = buildDistBar([
        { label: 'HAM',  count: d.original_ham  || 0, fill: 'var(--green)', total: d.original_records || 1 },
        { label: 'SPAM', count: d.original_spam || 0, fill: 'var(--amber)', total: d.original_records || 1 },
      ]);

      // Supplementary dataset bar
      document.getElementById('suppDist').innerHTML = buildDistBar([
        { label: 'HAM',      count: d.supplementary_ham      || 0, fill: 'var(--green)', total: d.supplementary_records || 1 },
        { label: 'SPAM',     count: d.supplementary_spam     || 0, fill: 'var(--amber)', total: d.supplementary_records || 1 },
        { label: 'PHISHING', count: d.supplementary_phishing || 0, fill: 'var(--red)',   total: d.supplementary_records || 1 },
      ]);
    } else {
      const errMsg = d.error || 'Dataset not available. Place SMSSpamCollection in datasets/.';
      ['iTotal','iHam','iSpam','iPhishing','iUrls'].forEach(id => setVal(id, '—'));
      document.getElementById('origDist').innerHTML = `<p style="color:var(--red);font-size:13px">${errMsg}</p>`;
      document.getElementById('suppDist').innerHTML = `<p style="color:var(--text-muted);font-size:13px">Supplementary dataset loading depends on original dataset.</p>`;
    }

    // Model evaluation summary
    buildEvalSummary(evalRes);

  } catch(e) {
    console.error('Insights load error:', e);
  }
}

function buildClassChart(ham, spam, phishing) {
  const ctx = document.getElementById('classChart');
  if (!ctx) return;
  new Chart(ctx, {
    type: 'doughnut',
    data: {
      labels: ['HAM', 'SPAM', 'PHISHING'],
      datasets: [{
        data: [ham, spam, phishing],
        backgroundColor: ['#16A34A', '#D97706', '#DC2626'],
        borderColor: ['#fff','#fff','#fff'],
        borderWidth: 2,
      }]
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      plugins: {
        legend: { position: 'bottom', labels: { font: { size: 12 }, padding: 16 } },
        tooltip: { callbacks: { label: ctx => `${ctx.label}: ${ctx.raw.toLocaleString()}` } },
      },
    }
  });
}

function buildSourceChart(original, supplementary) {
  const ctx = document.getElementById('sourceChart');
  if (!ctx) return;
  new Chart(ctx, {
    type: 'doughnut',
    data: {
      labels: ['Original UCI', 'Supplementary'],
      datasets: [{
        data: [original, supplementary],
        backgroundColor: ['#2563EB', '#7C5CD8'],
        borderColor: ['#fff','#fff'],
        borderWidth: 2,
      }]
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      plugins: {
        legend: { position: 'bottom', labels: { font: { size: 12 }, padding: 16 } },
        tooltip: { callbacks: { label: ctx => `${ctx.label}: ${ctx.raw.toLocaleString()}` } },
      },
    }
  });
}

function buildDistBar(items) {
  return items.map(item => {
    const pct = item.total > 0 ? ((item.count / item.total) * 100).toFixed(1) : 0;
    return `<div class="dist-row">
      <span class="dist-label">${item.label}</span>
      <div class="dist-track"><div class="dist-fill" style="width:${pct}%;background:${item.fill}"></div></div>
      <span class="dist-count">${item.count.toLocaleString()} (${pct}%)</span>
    </div>`;
  }).join('');
}

function buildEvalSummary(evalRes) {
  const el = document.getElementById('evalSummary');
  if (!el) return;

  if (evalRes.error || !evalRes.best_model) {
    el.innerHTML = `<p style="font-size:13px;color:var(--text-muted)">
      Evaluation report not available. Run <code>python retrain.py</code> to generate it.
    </p>`;
    return;
  }

  const e = evalRes.best_model_evaluation || {};
  const rpt = e.classification_report || {};
  const labels = evalRes.label_names || ['ham','spam'];
  const colorMap = { ham: 'var(--green)', spam: 'var(--amber)', phishing: 'var(--red)' };

  const perClass = labels.map(label => {
    const r = rpt[label] || {};
    const f1 = r['f1-score'] != null ? (r['f1-score'] * 100).toFixed(1) + '%' : '—';
    const prec = r['precision'] != null ? (r['precision'] * 100).toFixed(1) + '%' : '—';
    const rec = r['recall'] != null ? (r['recall'] * 100).toFixed(1) + '%' : '—';
    const support = r['support'] || 0;
    const color = colorMap[label] || 'var(--primary)';
    return `<div style="background:var(--bg);border:1px solid var(--border);border-radius:var(--radius-sm);padding:14px;text-align:center">
      <div style="font-weight:700;color:${color};margin-bottom:6px;font-size:14px">${label.toUpperCase()}</div>
      <div style="font-size:13px;line-height:1.9;color:var(--text-muted)">
        <div>Precision: <strong style="color:var(--text)">${prec}</strong></div>
        <div>Recall: <strong style="color:var(--text)">${rec}</strong></div>
        <div>F1: <strong style="color:var(--text)">${f1}</strong></div>
        <div>Support: <strong style="color:var(--text)">${support}</strong></div>
      </div>
    </div>`;
  }).join('');

  const cm = e.confusion_matrix || [];
  const cmHtml = cm.length ? `
    <div style="margin-top:16px">
      <div style="font-size:12px;font-weight:600;text-transform:uppercase;letter-spacing:0.05em;color:var(--text-muted);margin-bottom:8px">
        Confusion Matrix (rows=actual, cols=predicted) — Labels: ${labels.join(', ')}
      </div>
      <div style="overflow-x:auto">
        <table style="border-collapse:collapse;font-size:13px">
          ${cm.map((row, i) => `<tr>${row.map((v, j) => `
            <td style="padding:8px 14px;border:1px solid var(--border);text-align:center;
              background:${i===j ? 'var(--primary-light)' : 'var(--surface)'};
              font-weight:${i===j ? '700' : '400'};color:${i===j ? 'var(--primary)' : 'var(--text)'}">
              ${v}
            </td>`).join('')}</tr>`).join('')}
        </table>
      </div>
    </div>` : '';

  el.innerHTML = `
    <div style="display:flex;gap:16px;flex-wrap:wrap;margin-bottom:16px">
      <div style="background:var(--primary-light);border:1px solid var(--primary-border);border-radius:var(--radius-sm);padding:12px 20px;text-align:center">
        <div style="font-size:22px;font-weight:700;color:var(--primary)">${e.accuracy ? (e.accuracy*100).toFixed(1)+'%' : '—'}</div>
        <div style="font-size:11.5px;color:var(--text-muted)">Accuracy</div>
      </div>
      <div style="background:var(--primary-light);border:1px solid var(--primary-border);border-radius:var(--radius-sm);padding:12px 20px;text-align:center">
        <div style="font-size:22px;font-weight:700;color:var(--primary)">${e.macro_f1 ? e.macro_f1.toFixed(4) : '—'}</div>
        <div style="font-size:11.5px;color:var(--text-muted)">Macro F1</div>
      </div>
      <div style="background:var(--primary-light);border:1px solid var(--primary-border);border-radius:var(--radius-sm);padding:12px 20px;text-align:center">
        <div style="font-size:22px;font-weight:700;color:var(--primary)">${evalRes.best_model || '—'}</div>
        <div style="font-size:11.5px;color:var(--text-muted)">Best Model</div>
      </div>
    </div>
    <div style="display:grid;grid-template-columns:repeat(auto-fit,minmax(150px,1fr));gap:12px;margin-bottom:16px">
      ${perClass}
    </div>
    ${cmHtml}
  `;
}

function setVal(id, val) {
  const el = document.getElementById(id);
  if (el) el.textContent = typeof val === 'number' ? val.toLocaleString() : val;
}

loadInsights();
