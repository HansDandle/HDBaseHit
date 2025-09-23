// TV Home Media Automation PWA JS
const form = document.getElementById('nlpForm');
const input = document.getElementById('commandInput');
const resultDiv = document.getElementById('result');
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
    resultDiv.textContent = JSON.stringify(data, null, 2);
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

// Register service worker for PWA
if ('serviceWorker' in navigator) {
  window.addEventListener('load', () => {
    navigator.serviceWorker.register('/static/sw.js');
  });
}
