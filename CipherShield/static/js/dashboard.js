/* CipherShield — Dashboard JS */

async function loadDashboard() {
  try {
    const res = await fetch('/api/stats').then(r => r.json());

    // Model warning
    if (res.model && !res.model.loaded) {
      document.getElementById('modelWarning').style.display = 'flex';
    }

    // Session stats
    const s = res.session || {};
    setVal('statTotal',    s.total_analysed || 0);
    setVal('statHam',      s.ham_count      || 0);
    setVal('statSpam',     s.spam_count     || 0);
    setVal('statPhishing', s.phishing_count || 0);
    setVal('statUrls',     s.url_count_total || 0);

    // Dataset distribution
    const d = res.dataset || {};
    if (d.available) {
      const total = d.total_records || 1;
      const distHtml = buildDistBar([
        { label: 'HAM',      count: d.ham,      fill: 'var(--green)', pct: (d.ham/total*100).toFixed(1) },
        { label: 'SPAM',     count: d.spam,     fill: 'var(--amber)', pct: (d.spam/total*100).toFixed(1) },
        { label: 'PHISHING', count: d.phishing, fill: 'var(--red)',   pct: (d.phishing/total*100).toFixed(1) },
      ], total);
      document.getElementById('datasetDist').innerHTML = distHtml;
    } else {
      document.getElementById('datasetDist').innerHTML =
        `<p style="font-size:13px;color:var(--red)">${d.error || 'Dataset not found. Place SMSSpamCollection in datasets/'}</p>`;
    }

    // Model status card
    const m = res.model || {};
    const statusHtml = m.loaded
      ? `<div style="display:flex;flex-direction:column;gap:8px">
           <div class="badge badge-green" style="width:fit-content"><i class="bi bi-check-circle"></i> Loaded</div>
           <div style="font-size:13px"><strong>Algorithm:</strong> ${m.best_model || '—'}</div>
           <div style="font-size:13px"><strong>Accuracy:</strong> ${m.accuracy ? (m.accuracy*100).toFixed(1)+'%' : '—'}</div>
           <div style="font-size:13px"><strong>Macro F1:</strong> ${m.macro_f1 ? m.macro_f1.toFixed(4) : '—'}</div>
           <div style="font-size:13px"><strong>Phishing class:</strong> ${m.phishing_class_supported ? '✅ Supported' : '⚠️ Not supported'}</div>
         </div>`
      : `<div>
           <div class="badge badge-amber" style="width:fit-content;margin-bottom:10px"><i class="bi bi-exclamation-triangle"></i> Not Trained</div>
           <p style="font-size:13px;color:var(--text-muted)">Run <code>python retrain.py</code> to train the model.</p>
         </div>`;
    document.getElementById('modelStatusCard').innerHTML = statusHtml;

  } catch(e) {
    console.error('Dashboard load error:', e);
  }

  // Recent activity
  loadRecentActivity();
}

async function loadRecentActivity() {
  try {
    const res = await fetch('/api/history').then(r => r.json());
    const records = (res.records || []).slice(0, 5);
    const el = document.getElementById('recentActivity');

    if (!records.length) return; // keep empty state

    const rows = records.map(r => {
      const cls = r.label;
      const icon = cls === 'ham' ? 'check-circle' : cls === 'spam' ? 'exclamation-circle' : 'shield-exclamation';
      const badgeClass = cls === 'ham' ? 'badge-green' : cls === 'spam' ? 'badge-amber' : 'badge-red';
      const conf = r.confidence != null ? (r.confidence * 100).toFixed(0) + '%' : '';
      return `<div class="activity-row">
        <div class="activity-dot ${cls}"></div>
        <div class="activity-info">
          <div class="activity-label">
            <span class="badge ${badgeClass}">
              <i class="bi bi-${icon}"></i> ${cls.toUpperCase()}
            </span>
            ${conf ? `<span style="font-size:12px;color:var(--text-muted);margin-left:6px">${conf}</span>` : ''}
            ${r.has_url ? `<span class="badge badge-gray" style="font-size:10px;margin-left:4px"><i class="bi bi-link-45deg"></i></span>` : ''}
          </div>
          <div class="activity-time">${r.timestamp || ''}</div>
        </div>
      </div>`;
    }).join('');

    el.innerHTML = `<div class="activity-list">${rows}</div>`;
  } catch(e) {}
}

function buildDistBar(items, total) {
  return items.map(item => `
    <div class="dist-row">
      <span class="dist-label">${item.label}</span>
      <div class="dist-track">
        <div class="dist-fill" style="width:${item.pct}%;background:${item.fill}"></div>
      </div>
      <span class="dist-count">${item.count || 0} (${item.pct}%)</span>
    </div>
  `).join('');
}

function setVal(id, val) {
  const el = document.getElementById(id);
  if (el) el.textContent = val;
}

loadDashboard();
