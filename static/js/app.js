// TV Home Media Automation PWA JS
const form = document.getElementById('nlpForm');
const input = document.getElementById('commandInput');
const resultDiv = document.getElementById('result');
const torrentResultsDiv = document.getElementById('torrentResults');
const micBtn = document.getElementById('micBtn');
const wolBtn = document.getElementById('wolBtn');

form.addEventListener('submit', async (e) => {
  e.preventDefault();
  const command = input.value.trim();
  if (!command) return;
  resultDiv.textContent = 'Processing...';
  try {
    const res = await fetch('/nlp_command', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ command })
    });
    const data = await res.json();
    
    // Check if this is a series download response with episode data
    if (data.result && data.result.episodes && Array.isArray(data.result.episodes)) {
      displayEpisodeSelection(data.result);
    } else if (data.result && data.result.status === 'search_results' && data.result.torrents) {
      renderTorrentCandidates(data.result);
      resultDiv.textContent = data.result.message;
    } else if (data.result && data.result.status === 'record_candidates') {
      renderRecordCandidates(data.result);
      // Don't overwrite the rendered candidates table with just the message
    } else if (data.result && data.result.status === 'download_started') {
      resultDiv.textContent = data.result.message;
    } else {
      resultDiv.textContent = JSON.stringify(data, null, 2);
    }
  } catch (err) {
    resultDiv.textContent = 'Error: ' + err;
  }
});

// Speech recognition (Web Speech API)
let recognition;
if ('webkitSpeechRecognition' in window) {
  recognition = new webkitSpeechRecognition();
  recognition.lang = 'en-US';
  recognition.continuous = false;
  recognition.interimResults = false;
  micBtn.style.display = '';
  micBtn.addEventListener('click', () => {
    recognition.start();
    micBtn.classList.add('active');
  });
  recognition.onresult = (event) => {
    const transcript = event.results[0][0].transcript;
    input.value = transcript;
    micBtn.classList.remove('active');
  };
  recognition.onend = () => {
    micBtn.classList.remove('active');
  };
  recognition.onerror = () => {
    micBtn.classList.remove('active');
  };
} else {
  micBtn.style.display = 'none';
}

// Display episode selection interface for series downloads
function displayEpisodeSelection(data) {
  const episodes = data.episodes;
  const seriesName = data.series || 'Unknown Series';
  const seasonNumber = data.season || '';
  
  let html = `
    <div class="episode-selection">
      <h4>📺 ${seriesName}${seasonNumber ? ` - Season ${seasonNumber}` : ''}</h4>
      <p class="text-muted mb-3">Found ${episodes.length} episodes. Select episodes to download:</p>
      
      <div class="mb-3">
        <button class="btn btn-sm btn-outline-primary" onclick="toggleAllEpisodes(true)">Select All</button>
        <button class="btn btn-sm btn-outline-secondary ms-2" onclick="toggleAllEpisodes(false)">Deselect All</button>
        <button class="btn btn-sm btn-primary ms-3" onclick="bulkDownloadSelected()">Download Selected</button>
      </div>
      
      <div class="episode-list" style="max-height: 400px; overflow-y: auto;">
  `;
  
  episodes.forEach((episode, index) => {
    const qualityBadge = episode.quality === '1080p' ? 'bg-success' : 
                        episode.quality === '720p' ? 'bg-info' : 'bg-secondary';
    // Parse size - handle both "1.3 GB" format and raw bytes
    let sizeMB;
    if (typeof episode.size === 'string' && episode.size.includes('GB')) {
      sizeMB = Math.round(parseFloat(episode.size) * 1024);
    } else if (typeof episode.size === 'number') {
      sizeMB = Math.round(episode.size / 1024 / 1024);
    } else {
      sizeMB = 'Unknown';
    }
    
    html += `
      <div class="card mb-2 episode-card">
        <div class="card-body p-3">
          <div class="form-check">
            <input class="form-check-input episode-checkbox" type="checkbox" 
                   id="episode_${index}" ${episode.selected ? 'checked' : ''} 
                   data-index="${index}">
            <label class="form-check-label w-100" for="episode_${index}">
              <div class="d-flex justify-content-between align-items-start">
                <div class="flex-grow-1">
                  <div class="fw-bold">${episode.title}</div>
                  <div class="text-muted small">${episode.name}</div>
                </div>
                <div class="text-end">
                  <span class="badge ${qualityBadge}">${episode.quality}</span>
                  <div class="text-muted small mt-1">${sizeMB}${typeof sizeMB === 'number' ? ' MB' : ''}</div>
                  <div class="text-success small">🌱 ${episode.seeders}</div>
                </div>
              </div>
            </label>
          </div>
        </div>
      </div>
    `;
  });
  
  html += `
      </div>
    </div>
  `;
  
  resultDiv.innerHTML = html;
  
  // Store episode data globally for bulk download
  window.episodeData = episodes;
}

// Toggle all episode selections
function toggleAllEpisodes(selected) {
  const checkboxes = document.querySelectorAll('.episode-checkbox');
  checkboxes.forEach(checkbox => {
    checkbox.checked = selected;
  });
}

// Download selected episodes
async function bulkDownloadSelected() {
  const checkboxes = document.querySelectorAll('.episode-checkbox');
  const selectedEpisodes = [];
  
  checkboxes.forEach((checkbox, index) => {
    if (checkbox.checked && window.episodeData[index]) {
      selectedEpisodes.push({
        ...window.episodeData[index],
        selected: true
      });
    }
  });
  
  if (selectedEpisodes.length === 0) {
    alert('Please select at least one episode to download.');
    return;
  }
  
  const downloadBtn = document.querySelector('button[onclick="bulkDownloadSelected()"]');
  const originalText = downloadBtn.textContent;
  downloadBtn.textContent = 'Downloading...';
  downloadBtn.disabled = true;
  
  try {
    const res = await fetch('/bulk_download', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ episodes: selectedEpisodes })
    });
    
    const result = await res.json();
    
    if (result.success) {
      alert(result.message);
      // Update the display with download results
      displayDownloadResults(result.results);
    } else {
      alert('Download failed: ' + result.message);
    }
  } catch (err) {
    alert('Download error: ' + err.message);
  } finally {
    downloadBtn.textContent = originalText;
    downloadBtn.disabled = false;
  }
}

// Display download results
function displayDownloadResults(results) {
  let html = '<div class="download-results mt-3"><h5>Download Results:</h5>';
  
  results.forEach(result => {
    const statusClass = result.success ? 'text-success' : 'text-danger';
    const icon = result.success ? '✅' : '❌';
    
    html += `
      <div class="border-start border-3 ps-2 mb-1 ${statusClass}">
        ${icon} <strong>${result.title}</strong><br>
        <small>${result.message}</small>
      </div>
    `;
  });
  
  html += '</div>';
  resultDiv.innerHTML += html;
}

// --- Torrent Candidate Rendering ---
function humanSize(bytesOrNumber) {
  if (bytesOrNumber == null) return '—';
  let n = bytesOrNumber;
  if (typeof n !== 'number') {
    n = parseFloat(n);
    if (isNaN(n)) return '—';
  }
  const units = ['B','KB','MB','GB','TB'];
  let i = 0;
  while (n >= 1024 && i < units.length - 1) { n /= 1024; i++; }
  return n.toFixed(n >= 10 ? 0 : 1) + ' ' + units[i];
}

function renderTorrentCandidates(resultObj) {
  const torrents = resultObj.torrents || [];
  if (!torrents.length) {
    torrentResultsDiv.innerHTML = '<p class="text-muted">No torrent candidates.</p>';
    return;
  }
  let html = `
    <h3 style="margin-top:0;">Torrent Candidates</h3>
    <div style="margin-bottom:0.5rem;">
      <button class="btn btn-sm btn-outline-secondary" onclick="toggleAllTorrents(true)">Select All</button>
      <button class="btn btn-sm btn-outline-secondary ms-2" onclick="toggleAllTorrents(false)">Deselect All</button>
      <button class="btn btn-sm btn-primary ms-3" onclick="bulkAddSelectedTorrents()">Add Selected</button>
    </div>
  <table class="torrent-table two-row-mode">
      <thead>
        <tr style="text-align:left; border-bottom:1px solid #444;">
          <th style="width:32px;">#</th>
          <th>Torrent Details</th>
          <th></th>
          <th><input type="checkbox" id="torrentMasterChk" onclick="toggleAllTorrents(this.checked)"></th>
        </tr>
      </thead>
      <tbody>
  `;
  const now = Date.now();
  torrents.forEach(t => {
    const option = t.option || '?';
    const seeds = t.seeders || t.seeds || 0;
    const leeches = t.leechers || t.leeches || 0;
    const size = humanSize(t.size_bytes || t.size || t.raw?.size);
    let age = '—';
    if (t.time) {
      try {
        const dt = new Date(t.time);
        const diffH = Math.round((now - dt.getTime()) / 3600000);
        age = diffH < 24 ? diffH + 'h' : Math.round(diffH/24) + 'd';
      } catch(e) {}
    }
    const safeTitle = (t.title || '').replace(/`/g,'\`');
    const uploader = t.uploader || t.raw?.uploader || '';
    const category = t.category || t.raw?.category || '';
    const subcat = t.subcat || t.subcategory || t.raw?.subcat || '';
    const magnet = t.magnet || t.raw?.magnet || '';
    let hashSnippet = '';
    if (magnet.includes('btih:')) {
      const m = magnet.match(/btih:([A-Fa-f0-9]+)/);
      if (m) hashSnippet = m[1].slice(0,12) + '…';
    }
    
    html += `
      <!-- Title row -->
      <tr class="torrent-row-title">
        <td rowspan="2">${option}</td>
        <td class="title-span">
          <span class="full-title">${safeTitle}</span>
        </td>
        <td rowspan="2"><button class="btn btn-sm btn-outline-primary" data-opt="${option}" onclick="selectTorrentOption(${option})">Get</button></td>
        <td rowspan="2"><input type="checkbox" class="torrent-select" data-option="${option}"></td>
      </tr>
      <!-- Meta row -->
      <tr class="torrent-row-meta">
        <td>
          <span class="torrent-badge">Seeds: ${seeds}</span>
          <span class="torrent-badge">Size: ${size}</span>
          <span class="torrent-badge">Uploader: ${uploader || 'Unknown'}</span>
          ${age !== '—' ? `<span class="torrent-badge">Age: ${age}</span>` : ''}
        </td>
      </tr>
    `;
  });
  html += '</tbody></table>';
  torrentResultsDiv.innerHTML = html;

  // Detail panel toggle buttons (new layout)
  torrentResultsDiv.querySelectorAll('.torrent-expand-btn').forEach(btn => {
    btn.addEventListener('click', (e) => {
      e.stopPropagation();
      const opt = btn.getAttribute('data-opt');
      const panel = document.getElementById('torrent-details-' + opt);
      const expanded = btn.getAttribute('aria-expanded') === 'true';
      if (panel) {
        if (expanded) {
          panel.hidden = true;
          btn.setAttribute('aria-expanded','false');
          btn.textContent = 'Details ▸';
        } else {
          panel.hidden = false;
          btn.setAttribute('aria-expanded','true');
          btn.textContent = 'Details ▾';
        }
      }
    });
    // Keyboard support
    btn.addEventListener('keydown', (ev) => {
      if (ev.key === 'Enter' || ev.key === ' ') {
        ev.preventDefault();
        btn.click();
      }
    });
  });
}

// --- Recording Candidate Rendering ---
function renderRecordCandidates(resultObj) {
  const candidates = resultObj.candidates || [];
  if (!candidates.length) {
    resultDiv.innerHTML = '<p class="text-muted">No recording candidates.</p>';
    return;
  }
  let html = `
    <h3 style="margin-top:0;">Recording Candidates</h3>
    <p class="small text-muted">${resultObj.message || 'Use the buttons or type commands like: record option 1  /  record recurring option 1'}</p>
    <table class="torrent-table two-row-mode"> 
      <thead>
        <tr style="text-align:left; border-bottom:1px solid #444;">
          <th style="width:32px;">#</th>
          <th>Show Details</th>
          <th></th>
        </tr>
      </thead>
      <tbody>
  `;
  candidates.forEach(c => {
    html += `
      <!-- Title row -->
      <tr class="torrent-row-title">
        <td rowspan="2">${c.option || '?'}</td>
        <td class="title-span">
          <span class="full-title">${c.title || 'Unknown Show'}</span>
        </td>
        <td rowspan="2" style="white-space:nowrap;">
          <button class="btn btn-sm btn-outline-primary" onclick="recordOnce(${c.option})">Once</button>
          <button class="btn btn-sm btn-outline-success ms-1" onclick="recordRecurring(${c.option})">Recurring</button>
        </td>
      </tr>
      <!-- Meta row -->
      <tr class="torrent-row-meta">
        <td>
          <span class="torrent-badge">Date: ${c.date || 'Unknown'}</span>
          <span class="torrent-badge">Time: ${c.time || 'Unknown'}</span>
          <span class="torrent-badge">Channel: ${c.channel || 'Unknown'}</span>
          <span class="torrent-badge">Duration: ${c.duration || 'Unknown'}</span>
        </td>
      </tr>
    `;
  });
  html += '</tbody></table>';
  resultDiv.innerHTML = html;
}

async function recordOnce(optionNum) {
  if (!optionNum) return;
  resultDiv.textContent = 'Scheduling single recording option ' + optionNum + '...';
  try {
    const res = await fetch('/nlp_command', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ command: 'record option ' + optionNum })
    });
    const data = await res.json();
    if (data.result && data.result.status === 'record_scheduled') {
      resultDiv.textContent = data.result.message;
    } else {
      resultDiv.textContent = JSON.stringify(data, null, 2);
    }
  } catch (e) {
    resultDiv.textContent = 'Error scheduling recording: ' + e;
  }
}

async function recordRecurring(optionNum) {
  if (!optionNum) return;
  resultDiv.textContent = 'Creating recurring rule from option ' + optionNum + '...';
  try {
    const res = await fetch('/nlp_command', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ command: 'record recurring option ' + optionNum })
    });
    const data = await res.json();
    if (data.result && data.result.status === 'recurring_rule_created') {
      resultDiv.textContent = data.result.message;
    } else {
      resultDiv.textContent = JSON.stringify(data, null, 2);
    }
  } catch (e) {
    resultDiv.textContent = 'Error creating recurring rule: ' + e;
  }
}

async function selectTorrentOption(optionNumber) {
  resultDiv.textContent = 'Adding torrent option ' + optionNumber + '...';
  try {
    const res = await fetch('/nlp_command', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ command: 'download option ' + optionNumber })
    });
    const data = await res.json();
    if (data.result && data.result.status === 'download_started') {
      resultDiv.textContent = data.result.message;
    } else {
      resultDiv.textContent = JSON.stringify(data, null, 2);
    }
  } catch (e) {
    resultDiv.textContent = 'Error selecting torrent: ' + e;
  }
}

function toggleAllTorrents(checked) {
  document.querySelectorAll('.torrent-select').forEach(cb => { cb.checked = checked; });
  const master = document.getElementById('torrentMasterChk');
  if (master) master.checked = checked;
}

async function bulkAddSelectedTorrents() {
  const selected = Array.from(document.querySelectorAll('.torrent-select:checked'))
    .map(cb => cb.getAttribute('data-option'));
  if (!selected.length) {
    alert('Select at least one torrent to add.');
    return;
  }
  resultDiv.textContent = 'Adding ' + selected.length + ' torrent(s)...';
  try {
    const cmd = 'download options ' + selected.join(',');
    const res = await fetch('/nlp_command', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ command: cmd })
    });
    const data = await res.json();
    if (data.result && data.result.status === 'bulk_download_result') {
      let msg = data.result.message + '\nAdded: ' + data.result.added.map(a => a.option).join(', ');
      if (data.result.errors && data.result.errors.length) {
        msg += '\nErrors: ' + data.result.errors.join('; ');
      }
      resultDiv.textContent = msg;
    } else {
      resultDiv.textContent = JSON.stringify(data, null, 2);
    }
  } catch (e) {
    resultDiv.textContent = 'Bulk add error: ' + e;
  }
}

wolBtn.addEventListener('click', async () => {
  const mac = prompt('Enter MAC address to wake (format: 00:11:22:33:44:55):');
  if (!mac) return;
  resultDiv.textContent = 'Sending WOL...';
  try {
    const res = await fetch('/wol', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ mac })
    });
    const data = await res.json();
    resultDiv.textContent = JSON.stringify(data, null, 2);
  } catch (err) {
    resultDiv.textContent = 'Error: ' + err;
  }
});

// Manual recording functions
function startRecording() {
  const channel = document.getElementById('channel').value;
  const duration = document.getElementById('duration').value;
  const format = document.getElementById('format').value;
  const crf = document.getElementById('crf').value;
  const preset = document.getElementById('preset').value;
  
  if (!channel) {
    alert('Please select a channel');
    return;
  }
  
  fetch('/record_now', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      channel: channel,
      duration: parseInt(duration),
      format: format,
      crf: parseInt(crf),
      preset: preset
    })
  })
  .then(res => res.json())
  .then(data => {
    alert(data.message || 'Recording started');
    updateProgress();
  })
  .catch(err => {
    alert('Error starting recording: ' + err);
  });
}

function stopRecording() {
  fetch('/stop_recording', {
    method: 'POST'
  })
  .then(res => res.json())
  .then(data => {
    alert(data.message || 'Recording stopped');
    updateProgress();
  })
  .catch(err => {
    alert('Error stopping recording: ' + err);
  });
}

function scheduleRecording() {
  const channel = document.getElementById('channel').value;
  const duration = document.getElementById('duration').value;
  const format = document.getElementById('format').value;
  const crf = document.getElementById('crf').value;
  const preset = document.getElementById('preset').value;
  const time = document.getElementById('time').value;
  
  // Get selected days
  const dayCheckboxes = document.querySelectorAll('input[name="days"]:checked');
  const days = Array.from(dayCheckboxes).map(cb => cb.value);
  
  if (!channel) {
    alert('Please select a channel');
    return;
  }
  
  if (!time) {
    alert('Please select a time');
    return;
  }
  
  if (days.length === 0) {
    alert('Please select at least one day');
    return;
  }
  
  fetch('/schedule', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      channel: channel,
      duration: parseInt(duration),
      format: format,
      crf: parseInt(crf),
      preset: preset,
      time: time,
      days: days
    })
  })
  .then(res => res.json())
  .then(data => {
    alert(data.message || 'Recording scheduled');
    location.reload(); // Refresh to show new scheduled recording
  })
  .catch(err => {
    alert('Error scheduling recording: ' + err);
  });
}

function updateProgress() {
  fetch('/progress')
    .then(res => res.json())
    .then(data => {
      document.getElementById('progress').innerHTML = data.html || '';
    })
    .catch(err => {
      console.error('Error updating progress:', err);
    });
}

// Auto-categorize torrents
document.getElementById('autoCategorizeBtn')?.addEventListener('click', function() {
  this.textContent = '⏳ Categorizing...';
  this.disabled = true;
  
  fetch('/auto_categorize', {
    method: 'POST'
  })
  .then(res => res.json())
  .then(data => {
    if (data.success) {
      alert(`✅ ${data.message}`);
    } else {
      alert(`❌ ${data.message}`);
    }
  })
  .catch(err => {
    alert('❌ Error: ' + err);
  })
  .finally(() => {
    this.textContent = '📋 Auto-Categorize Torrents';
    this.disabled = false;
  });
});

// Register service worker for PWA
if ('serviceWorker' in navigator) {
  window.addEventListener('load', () => {
    navigator.serviceWorker.register('/static/sw.js');
  });
}
