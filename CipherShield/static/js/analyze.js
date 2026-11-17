/* CipherShield — Analyze Page JS */

const EXAMPLES = [
  // 0: Legitimate bank transaction
  "Amount Rs.5,000 debited from your HDFC account ending 1234 on 15-Oct-2024 at 14:32. Available balance: Rs.12,450. For queries call 18002726161.",

  // 1: Fake KYC phishing
  "URGENT: Your SBI account has been SUSPENDED due to incomplete KYC. Update immediately at http://sbi-kyc-verify.test/update or your account will be blocked within 24 hours. Click now!",

  // 2: UPI collect-request scam
  "ALERT: Someone has sent you a UPI collect request of Rs.10000. Approve it at http://upi-request.test to receive your money immediately.",

  // 3: Courier delivery phishing
  "Your India Post parcel could not be delivered due to incomplete address. Pay Rs.35 delivery reconfirmation fee at http://indiapost-redeliver.test",

  // 4: Normal college notification
  "Dear student, the internal exam schedule for November has been uploaded on the college portal. Please check https://example.com/portal for details. Regards, Exam Cell",

  // 5: Fake lottery spam
  "CONGRATULATIONS! You have WON Rs.50 Lakh in KBC Lottery 2024! To claim prize send your name, DOB and bank details to claim@kbc-lottery.test Limited time!",

  // 6: IP-based suspicious URL
  "Your SBI account requires urgent verification. Click the link to continue: http://203.0.113.45/sbi-verify?token=abc123 Do not delay or account will be blocked.",

  // 7: Legitimate message with URL
  "Your Flipkart order #OD112345678 has been shipped and is out for delivery. Track your order at https://flipkart.com/track. Expected delivery: tomorrow.",
];

function loadExample(index) {
  const msg = EXAMPLES[index];
  if (msg) {
    document.getElementById('messageInput').value = msg;
    updateCharCounter();
    // Scroll to textarea
    document.getElementById('messageInput').scrollIntoView({ behavior: 'smooth', block: 'center' });
    document.getElementById('messageInput').focus();
  }
}

function updateCharCounter() {
  const ta = document.getElementById('messageInput');
  const counter = document.getElementById('charCounter');
  const len = ta.value.length;
  counter.textContent = `${len} / 2000`;
  counter.className = 'char-counter' + (len > 1800 ? ' danger' : len > 1500 ? ' warning' : '');
}

function clearInput() {
  document.getElementById('messageInput').value = '';
  updateCharCounter();
  document.getElementById('resultPanel').className = 'result-panel';
  document.getElementById('resultPanel').innerHTML = '';
  document.getElementById('spinnerWrap').className = 'spinner-wrap';
}

async function analyzeMessage() {
  const message = document.getElementById('messageInput').value.trim();
  if (!message) {
    alert('Please enter a message to analyze.');
    return;
  }

  const btn = document.getElementById('analyzeBtn');
  btn.disabled = true;

  document.getElementById('resultPanel').className = 'result-panel';
  document.getElementById('resultPanel').innerHTML = '';
  document.getElementById('spinnerWrap').className = 'spinner-wrap visible';

  try {
    const res = await fetch('/predict', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ message }),
    });

    const data = await res.json();
    document.getElementById('spinnerWrap').className = 'spinner-wrap';

    if (!res.ok || data.error) {
      showError(data.error || 'Server error. Please try again.');
    } else {
      showResult(data, message);
    }
  } catch(e) {
    document.getElementById('spinnerWrap').className = 'spinner-wrap';
    showError('Network error. Is the Flask server running?');
  } finally {
    btn.disabled = false;
  }
}

function showError(msg) {
  const panel = document.getElementById('resultPanel');
  panel.innerHTML = `
    <div class="result-header error">
      <div class="result-icon error"><i class="bi bi-x-circle"></i></div>
      <div>
        <div class="result-label" style="color:var(--text-muted)">Error</div>
        <div style="font-size:13px;color:var(--text-muted)">${escHtml(msg)}</div>
      </div>
    </div>
    <div class="result-body">
      <p style="font-size:13.5px;color:var(--text-muted)">
        Make sure the model is trained by running <code>python retrain.py</code>.
      </p>
    </div>
  `;
  panel.className = 'result-panel visible';
}

function showResult(data, originalMessage) {
  const cls = data.prediction || 'ham';
  const iconMap = { ham: 'check-circle-fill', spam: 'exclamation-circle-fill', phishing: 'shield-exclamation-fill' };
  const labelMap = { ham: 'HAM — Legitimate', spam: 'SPAM', phishing: 'PHISHING' };
  const icon = iconMap[cls] || 'question-circle';
  const label = labelMap[cls] || cls.toUpperCase();

  const conf = data.confidence != null ? data.confidence : null;
  const confPct = conf != null ? (conf * 100).toFixed(1) : null;

  // URL indicators
  const urlIndicators = buildUrlIndicators(data);

  // Suspicious indicators
  const indList = (data.suspicious_indicators || []).map(s =>
    `<span class="url-indicator present"><i class="bi bi-exclamation-triangle-fill"></i>${escHtml(s)}</span>`
  ).join('');

  // Detected URLs
  const urlList = (data.detected_urls || []).map(u =>
    `<code style="font-size:11.5px;background:var(--gray-light);padding:2px 6px;border-radius:4px;word-break:break-all">${escHtml(u)}</code>`
  ).join('<br>');

  const html = `
    <div class="result-header ${cls}">
      <div class="result-icon ${cls}"><i class="bi bi-${icon}"></i></div>
      <div style="flex:1">
        <div class="result-label ${cls}">${label}</div>
        ${confPct ? `
        <div class="confidence-bar-wrap" style="margin-top:6px">
          <span style="font-size:12px;color:var(--text-muted);min-width:100px">Confidence: ${confPct}%</span>
          <div class="confidence-bar" style="max-width:200px">
            <div class="confidence-fill ${cls}" style="width:${confPct}%"></div>
          </div>
        </div>` : ''}
      </div>
    </div>
    <div class="result-body">

      <div class="result-section">
        <div class="result-section-title">Explanation</div>
        <p style="font-size:13.5px;line-height:1.75">${escHtml(data.explanation || '')}</p>
      </div>

      <div class="result-section">
        <div class="result-section-title">Message Analysed</div>
        <div style="background:var(--bg);border:1px solid var(--border);border-radius:var(--radius-sm);padding:12px;font-size:13px;line-height:1.65;color:var(--text-muted);max-height:120px;overflow-y:auto;word-break:break-word">
          ${escHtml(originalMessage)}
        </div>
      </div>

      <div class="result-section">
        <div class="result-section-title">URL Analysis</div>
        <div class="url-indicators">${urlIndicators}</div>
        ${urlList ? `<div style="margin-top:10px;display:flex;flex-direction:column;gap:4px">${urlList}</div>` : ''}
      </div>

      ${indList ? `
      <div class="result-section">
        <div class="result-section-title">Suspicious Indicators</div>
        <div class="url-indicators">${indList}</div>
      </div>` : ''}

      ${data.all_probabilities && Object.keys(data.all_probabilities).length ? `
      <div class="result-section">
        <div class="result-section-title">Class Probabilities</div>
        ${buildProbBars(data.all_probabilities)}
      </div>` : ''}

      <div class="disclaimer-box" style="margin-top:4px">
        <i class="bi bi-exclamation-triangle-fill" style="flex-shrink:0"></i>
        <span>${escHtml(data.disclaimer || '')}</span>
      </div>

      <div style="margin-top:16px">
        <button class="btn btn-outline" onclick="clearInput()">
          <i class="bi bi-arrow-left"></i> Analyze Another Message
        </button>
      </div>
    </div>
  `;

  const panel = document.getElementById('resultPanel');
  panel.innerHTML = html;
  panel.className = 'result-panel visible';
  panel.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
}

function buildUrlIndicators(data) {
  const indicators = [
    { key: 'has_url',               label: 'URL Present',          icon: 'link-45deg' },
    { key: 'url_has_ip',            label: 'IP-based URL',         icon: 'hdd-network',  warnIfTrue: true },
    { key: 'url_shortener',         label: 'URL Shortener',        icon: 'arrow-right-circle', warnIfTrue: true },
    { key: 'url_suspicious_chars',  label: 'Suspicious Chars',     icon: 'bug',           warnIfTrue: true },
    { key: 'suspicious_subdomain',  label: 'Suspicious Subdomain', icon: 'exclamation-triangle', warnIfTrue: true },
    { key: 'punycode_domain',       label: 'Punycode Domain',      icon: 'translate',     warnIfTrue: true },
    { key: 'multiple_urls',         label: 'Multiple URLs',        icon: 'collection',    warnIfTrue: false },
    { key: 'trusted_domain',        label: 'Recognised Domain',    icon: 'shield-check',  warnIfTrue: false },
    { key: 'suspicious_url_scheme', label: 'Unusual Scheme',       icon: 'exclamation-octagon', warnIfTrue: true },
  ];

  if (!data.has_url) {
    return `<span class="url-indicator absent"><i class="bi bi-link"></i> No URLs detected</span>`;
  }

  return indicators.map(ind => {
    const val = data[ind.key];
    if (ind.key === 'has_url' && !val) return '';
    if (!val && ind.key !== 'has_url') return '';

    let cls = 'neutral';
    if (ind.key === 'has_url') cls = 'neutral';
    else if (ind.warnIfTrue && val) cls = 'present';
    else if (!ind.warnIfTrue && val && ind.key === 'trusted_domain') cls = 'absent'; // green for trusted
    else cls = 'neutral';

    return `<span class="url-indicator ${cls}"><i class="bi bi-${ind.icon}"></i>${ind.label}</span>`;
  }).join('');
}

function buildProbBars(probs) {
  const colorMap = { ham: 'var(--green)', spam: 'var(--amber)', phishing: 'var(--red)' };
  return Object.entries(probs).map(([label, prob]) => {
    const pct = (prob * 100).toFixed(1);
    const color = colorMap[label] || 'var(--primary)';
    return `<div style="display:flex;align-items:center;gap:10px;margin-bottom:6px">
      <span style="width:70px;font-size:12.5px;font-weight:500">${label.toUpperCase()}</span>
      <div class="confidence-bar" style="flex:1"><div style="height:100%;width:${pct}%;background:${color};border-radius:999px"></div></div>
      <span style="width:45px;font-size:12px;text-align:right;color:var(--text-muted)">${pct}%</span>
    </div>`;
  }).join('');
}

function escHtml(str) {
  return String(str)
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')
    .replace(/'/g, '&#39;');
}

// Check model on load
fetch('/api/health').then(r => r.json()).then(d => {
  if (!d.model_loaded) {
    document.getElementById('modelWarning').style.display = 'flex';
  }
}).catch(() => {});
