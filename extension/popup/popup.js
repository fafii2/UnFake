const API_BASE = 'http://127.0.0.1:8001';
const statusDot = document.getElementById('statusDot');
const statusText = document.getElementById('statusText');
const manualClaim = document.getElementById('manualClaim');
const verifyBtn = document.getElementById('verifyBtn');
const actionStatus = document.getElementById('actionStatus');
const checkLiveBtn = document.getElementById('checkLiveBtn');

function setStatus(message, state) {
  statusDot.className = `status-dot ${state}`;
  statusText.textContent = message;
}

function showLiveStatus(check) {
  if (check.ready) {
    setStatus('Live search and evaluation verified', 'online');
  } else {
    const failed = Object.entries(check.checks).filter(([, value]) => value.status !== 'ok')
      .map(([name, value]) => `${name}: ${value.status.replaceAll('_', ' ')}${value.http_status ? ` (${value.http_status})` : ''}`);
    setStatus(`Live check failed — ${failed.join('; ')}`, 'offline');
  }
}

async function checkBackendStatus() {
  try {
    const response = await fetch(`${API_BASE}/api/v1/health`, {signal: AbortSignal.timeout(3000)});
    if (!response.ok) throw new Error('Backend returned an error');
    const data = await response.json();
    if (data.live_check && Date.now() / 1000 - data.live_check.checked_at < 300) {
      showLiveStatus(data.live_check);
    } else if (data.live_search_configured && data.evaluation_configured) {
      setStatus('Backend online · live services configured', 'pending');
    } else {
      setStatus('Backend online · live API keys missing', 'offline');
    }
  } catch {
    setStatus('Backend offline · run Start-UnFake.cmd', 'offline');
  }
}

checkLiveBtn.addEventListener('click', async () => {
  checkLiveBtn.disabled = true;
  setStatus('Testing live search and evaluation...', 'pending');
  try {
    const response = await fetch(`${API_BASE}/api/v1/readiness`, {
      method: 'POST', signal: AbortSignal.timeout(25000),
    });
    if (!response.ok) throw new Error('Live check failed. Try again.');
    showLiveStatus(await response.json());
  } catch (err) {
    setStatus(err.name === 'TimeoutError' ? 'Live check timed out · try again' : err.message, 'offline');
  } finally { checkLiveBtn.disabled = false; }
});

manualClaim.addEventListener('input', () => {
  verifyBtn.disabled = !manualClaim.value.trim();
});

verifyBtn.addEventListener('click', async () => {
  const claim = manualClaim.value.trim();
  if (!claim) return;
  verifyBtn.disabled = true;
  verifyBtn.textContent = 'Verifying...';
  actionStatus.textContent = '';
  try {
    const [tab] = await chrome.tabs.query({active: true, currentWindow: true});
    const response = await chrome.runtime.sendMessage({action: 'verify_claim', claim, inputType: 'text', tabId: tab?.id});
    if (!response?.success) throw new Error(response?.error || 'Verification failed. Please try again.');
    actionStatus.textContent = 'Result shown on the page. Close this popup to read it.';
  } catch (err) { actionStatus.textContent = err.message; }
  finally {
    verifyBtn.textContent = 'Verify Text Claim';
    verifyBtn.disabled = !manualClaim.value.trim();
  }
});

document.getElementById('cropBtn').addEventListener('click', async () => {
  try {
    const response = await chrome.runtime.sendMessage({action: 'trigger_crop_from_popup'});
    if (!response?.success) throw new Error(response?.error || 'Cannot crop this page.');
    window.close();
  } catch (err) { actionStatus.textContent = err.message; }
});

document.getElementById('screenshotFile').addEventListener('change', async event => {
  const file = event.target.files[0];
  if (!file) return;
  actionStatus.textContent = '';
  try {
    if (!['image/png', 'image/jpeg', 'image/webp'].includes(file.type) || file.size > 5 * 1024 * 1024) {
      throw new Error('Choose a PNG, JPEG, or WebP screenshot under 5 MB.');
    }
    const [tab] = await chrome.tabs.query({active: true, currentWindow: true});
    const imageUrl = await new Promise((resolve, reject) => {
      const reader = new FileReader();
      reader.onload = () => resolve(reader.result);
      reader.onerror = () => reject(new Error('Could not read this screenshot.'));
      reader.readAsDataURL(file);
    });
    actionStatus.textContent = 'Reading screenshot locally...';
    const response = await chrome.runtime.sendMessage({action: 'upload_screenshot', imageUrl, tabId: tab?.id});
    if (!response?.success) throw new Error(response?.error || 'Could not read the screenshot.');
    window.close();
  } catch (err) { actionStatus.textContent = err.message; }
  finally { event.target.value = ''; }
});

checkBackendStatus();
