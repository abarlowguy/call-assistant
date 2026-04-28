let ws = null;
let timer = null;
let seconds = 0;
let currentProjectFile = null;

const statusDot = document.getElementById('status-dot');
const btnStart = document.getElementById('btn-start');
const btnStop = document.getElementById('btn-stop');
const btnLoad = document.getElementById('btn-load');
const projectLabel = document.getElementById('project-label');
const transcriptPanel = document.getElementById('transcript-panel');
const intelligencePanel = document.getElementById('intelligence-panel');
const sessionTimer = document.getElementById('session-timer');

function connectWS() {
  ws = new WebSocket('ws://127.0.0.1:8765/ws');
  ws.onmessage = (e) => {
    const msg = JSON.parse(e.data);
    if (msg.type === 'transcript') addTranscript(msg.text);
    if (msg.type === 'insight') addInsight(msg.text);
    if (msg.type === 'search') addSearch(msg.query, msg.result);
  };
}

function addTranscript(text) {
  const div = document.createElement('div');
  div.className = 'transcript-line new';
  div.textContent = text;
  transcriptPanel.appendChild(div);
  transcriptPanel.scrollTop = transcriptPanel.scrollHeight;
  setTimeout(() => div.classList.remove('new'), 2000);
}

function addInsight(text) {
  const card = document.createElement('div');
  card.className = 'insight-card';
  card.innerHTML = text.replace(/\n/g, '<br>');
  intelligencePanel.prepend(card);
}

function addSearch(query, result) {
  const card = document.createElement('div');
  card.className = 'search-card';
  card.innerHTML = `<div class="query">Web: ${query}</div><div class="result">${result.replace(/\n/g, '<br>')}</div>`;
  intelligencePanel.prepend(card);
}

btnLoad.addEventListener('click', () => {
  const query = prompt('Search your vault (type a project name):');
  if (!query) return;
  fetch('/vault/search', { method: 'POST', headers: {'Content-Type':'application/json'}, body: JSON.stringify({query}) })
    .then(r => r.json())
    .then(results => {
      if (!results.length) { alert('No vault notes found for: ' + query); return; }
      const names = results.map((r,i) => `${i+1}. ${r.name}`).join('\n');
      const choice = prompt(`Select a note:\n${names}\nEnter number:`);
      const idx = parseInt(choice) - 1;
      if (idx >= 0 && idx < results.length) {
        currentProjectFile = results[idx].path;
        projectLabel.textContent = `Project: ${results[idx].name}`;
        projectLabel.className = '';
      }
    });
});

btnStart.addEventListener('click', () => {
  fetch('/start', {
    method: 'POST',
    headers: {'Content-Type':'application/json'},
    body: JSON.stringify({ project_file: currentProjectFile })
  }).then(r => r.json()).then(data => {
    if (data.error) { alert(data.error); return; }
    statusDot.classList.add('active');
    btnStart.disabled = true;
    btnStop.disabled = false;
    seconds = 0;
    timer = setInterval(() => {
      seconds++;
      const m = Math.floor(seconds/60).toString().padStart(2,'0');
      const s = (seconds%60).toString().padStart(2,'0');
      sessionTimer.textContent = m + ':' + s;
    }, 1000);
    connectWS();
  });
});

btnStop.addEventListener('click', () => {
  fetch('/stop', {method:'POST'}).then(() => {
    statusDot.classList.remove('active');
    btnStart.disabled = false;
    btnStop.disabled = true;
    clearInterval(timer);
    sessionTimer.textContent = '';
    if (ws) { ws.close(); ws = null; }
  });
});
