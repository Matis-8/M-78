/* ─────────────────────────────────────────────────────────────
   M-78 Premium Dashboard — app.js
───────────────────────────────────────────────────────────── */

const API = 'http://127.0.0.1:8000';

// ── NAVIGATION ────────────────────────────────────────────────
document.querySelectorAll('#sidebarNav .nav-item, .sidebar-footer .nav-item').forEach(link => {
  link.addEventListener('click', (e) => {
    e.preventDefault();
    document.querySelectorAll('.nav-item').forEach(n => n.classList.remove('active'));
    link.classList.add('active');
    
    const target = link.getAttribute('data-page');
    document.querySelectorAll('.page').forEach(p => p.classList.remove('active'));
    document.getElementById('page-' + target)?.classList.add('active');
    
    // Launch button visibility
    const launchBtn = document.getElementById('btnLaunchWidget');
    if (launchBtn) {
      if (target === 'home') launchBtn.style.display = 'flex';
      else launchBtn.style.display = 'none';
    }
  });
});

document.getElementById('btnLaunchWidget')?.addEventListener('click', async () => {
  try {
    await fetch(`${API}/launch-widget`, { method: 'POST' });
  } catch (e) {
    console.error("Failed to launch widget:", e);
  }
});

document.querySelectorAll('.tab').forEach(tab => {
  tab.addEventListener('click', (e) => {
    document.querySelectorAll('.tab').forEach(t => t.classList.remove('active'));
    tab.classList.add('active');
    if(tab.getAttribute('data-tab') === 'usage') {
       document.getElementById('tabContentUsage').style.display = 'grid';
       document.getElementById('tabContentVoice').style.display = 'none';
    } else if(tab.getAttribute('data-tab') === 'voice') {
       document.getElementById('tabContentUsage').style.display = 'none';
       document.getElementById('tabContentVoice').style.display = 'grid';
    }
  });
});

// ── CORE DATA ─────────────────────────────────────────────────
async function fetchDashboard() {
  try {
    const res = await fetch(`${API}/stats`);
    const stats = await res.json();
    
    document.getElementById('totalWordsVal').textContent = (stats.total_words || 0).toLocaleString();
    document.getElementById('todayWordsVal').textContent = (stats.today_words || 0).toLocaleString();
    document.getElementById('statsWPM').textContent = (stats.avg_wpm || 0);
    document.getElementById('statsTotalSessionsVal').textContent = (stats.total_sessions || 0).toLocaleString();
    
    document.getElementById('booksWritten').textContent = Math.max(0, Math.floor((stats.total_words || 0) / 90000)).toLocaleString();
    document.getElementById('streakHeaderTitle').textContent = `${stats.streak_days || 0} day streak`;
    document.getElementById('longestStreakLabel').textContent = `LONGEST STREAK | ${stats.longest_streak || 0} DAYS`;

    renderHeatmap(stats.words_per_session || []);
    renderDesktopUsage(stats.desktop_usage || {usage: []});
  } catch (err) {
    console.warn("Could not load backend stats:", err);
  }
}

async function fetchSessions() {
  try {
    const res = await fetch(`${API}/sessions`);
    const sessions = await res.json();
    
    const container = document.getElementById('homeSessionsList');
    if (!container) return;
    
    if (sessions.length === 0) {
      container.innerHTML = '<p style="color:var(--text-3);">No dictation sessions yet. Start speaking!</p>';
      return;
    }
    
    let html = '';
    sessions.forEach(s => {
      let d = new Date(s.timestamp).toLocaleString();
      let appName = s.app_name || "Unknown App";
      
      // Escape text safely for JS injection
      let rawSafe = s.text.replace(/'/g, "\\'").replace(/"/g, '&quot;');
      
      html += `
        <div style="padding:16px; border:1px solid var(--border); border-radius:8px; display:flex; flex-direction:column; gap:8px;">
          <div style="display:flex; justify-content:space-between; font-size:12px; color:var(--text-2);">
            <strong style="color:var(--accent);">${appName}</strong>
            <span>${d}</span>
          </div>
          <div style="color:var(--text-1); font-size:14px; line-height:1.5;">"${s.text}"</div>
          
          <div style="display:flex; justify-content:space-between; align-items:center; margin-top:8px;">
            <div style="font-size:11px; color:var(--text-3); font-weight:600;">${s.word_count} WORDS | ${(s.duration||0).toFixed(1)}s</div>
            <div style="display:flex; gap:8px;">
               <button onclick="saveSessionToScratchpad('${rawSafe}')" style="background:var(--bg-hover); border:1px solid var(--border); padding:4px 8px; border-radius:4px; font-size:12px; font-weight:500; cursor:pointer;">Save as Note</button>
               <button onclick="saveSessionToSnippets('${rawSafe}')" style="background:var(--bg-hover); border:1px solid var(--border); padding:4px 8px; border-radius:4px; font-size:12px; font-weight:500; cursor:pointer;">Add to Snippets</button>
               <button onclick="navigator.clipboard.writeText('${rawSafe}')" style="background:var(--bg-hover); border:1px solid var(--border); padding:4px 8px; border-radius:4px; font-size:12px; font-weight:500; cursor:pointer;">Copy</button>
               <button onclick="deleteResource('sessions', ${s.id})" style="background:#fef2f2; border:1px solid #fca5a5; color:#b91c1c; padding:4px 8px; border-radius:4px; font-size:12px; font-weight:500; cursor:pointer;">Delete</button>
            </div>
          </div>
        </div>
      `;
    });
    container.innerHTML = html;
    
    // Voice insights injection
    renderVoiceInsights(sessions);
  } catch (err) { }
}

window.saveSessionToScratchpad = async (text) => {
  const area = document.getElementById('scratchpadArea');
  if(area) {
     area.value = area.value ? area.value + '\n\n' + text : text;
     await fetch(`${API}/scratchpad`, {
       method:'POST', headers:{'Content-Type':'application/json'},
       body: JSON.stringify({content: area.value})
     });
     alert('Saved to Scratchpad');
  }
};

window.saveSessionToSnippets = async (text) => {
  const t = prompt('Snippet Title for: "' + text.substring(0,20) + '..."'); 
  if(!t) return;
  await fetch(`${API}/snippets`, {
    method:'POST', headers:{'Content-Type':'application/json'},
    body: JSON.stringify({title:t, content:text})
  });
  fetchSnippets();
  alert('Saved to Snippets');
};

// ── RENDERERS ─────────────────────────────────────────────────

function renderHeatmap(wps) {
  const container = document.getElementById('heatmapContainer');
  if (!container) return;
  
  const wordMap = {};
  wps.forEach(item => { wordMap[item.date] = (wordMap[item.date] || 0) + item.words; });
  const maxWords = Math.max(1, ...Object.values(wordMap));

  const weeks = 28;
  const totalDays = weeks * 7;
  const today = new Date();
  
  const daysData = [];
  for (let i = totalDays - 1; i >= 0; i--) {
    let d = new Date();
    d.setDate(today.getDate() - i);
    let key = d.toISOString().slice(0, 10);
    daysData.push({ date: key, words: wordMap[key] || 0 });
  }

  let html = '';
  for (let col = 0; col < weeks; col++) {
    html += '<div class="h-col">';
    for (let row = 0; row < 7; row++) {
      let idx = col * 7 + row;
      let w = daysData[idx].words;
      let lvl = 0;
      if (w > 0) {
        let pct = w / maxWords;
        if (pct < 0.25) lvl = 1;
        else if (pct < 0.5) lvl = 2;
        else if (pct < 0.75) lvl = 3;
        else lvl = 4;
      }
      html += `<div class="h-cell" data-level="${lvl}" title="${daysData[idx].date}: ${w} words"></div>`;
    }
    html += '</div>';
  }
  container.innerHTML = html;
}

function renderDesktopUsage(usageData) {
  const container = document.getElementById('desktopUsageList');
  if (!container) return;
  
  document.getElementById('totalAppsUsed').textContent = `TOTAL APPS USED | ${usageData.total_apps || 0}`;
  
  if (usageData.usage.length === 0) {
    container.innerHTML = '<p style="color:var(--text-3); font-size:12px;">No app usage data yet.</p>';
    return;
  }
  
  let html = '';
  usageData.usage.slice(0, 6).forEach(u => {
    html += `
      <div class="usage-item">
        <svg class="u-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor"><rect x="3" y="11" width="18" height="10" rx="2"/><path d="M12 5v6"/><path d="M8 5h8"/><circle cx="12" cy="7" r="2"/></svg>
        <div class="u-bar-wrap">
          <div class="u-bar" style="width: ${Math.max(2, u.percentage)}%;">${u.percentage}%</div>
        </div>
        <div class="u-label">${u.count} SESSIONS IN ${u.name.toUpperCase()}</div>
      </div>
    `;
  });
  container.innerHTML = html;
}

function renderVoiceInsights(sessions) {
  let text = sessions.map(s => s.text.toLowerCase()).join(" ");
  let words = text.replace(/[^a-z0-9\s]/g, "").split(/\s+/).filter(w => w.length > 3);
  let counts = {};
  words.forEach(w => counts[w] = (counts[w] || 0) + 1);
  let sorted = Object.keys(counts).sort((a, b) => counts[b] - counts[a]).slice(0, 10);
  
  const container = document.getElementById('voiceInsightsList');
  if(!container) return;
  if(sorted.length === 0) {
     container.innerHTML = "<p style='color:var(--text-3); font-size:13px;'>Not enough data yet to analyze your voice patterns.</p>";
     return;
  }
  
  let html = '';
  sorted.forEach(w => {
    html += `
      <div class="usage-item" style="border-bottom: 1px solid var(--border); padding-bottom: 8px;">
        <svg class="u-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor"><path d="M12 2v20M17 5H9.5a3.5 3.5 0 0 0 0 7h5a3.5 3.5 0 0 1 0 7H6"/></svg>
        <div class="u-label" style="font-size: 15px; color:var(--text-1); font-weight:600; text-transform: capitalize;">"${w}"</div>
        <div style="margin-left:auto; font-size:12px; font-weight:600; color:var(--text-3); background:var(--bg); padding:4px 10px; border-radius:12px;">${counts[w]} mentions</div>
      </div>
    `;
  });
  container.innerHTML = html;
}

// ── AUX PAGES CRUD ──────────────────────────────────────────────

async function fetchDictionary() {
  const res = await fetch(`${API}/dictionary`);
  const data = await res.json();
  const c = document.getElementById('dictList');
  if(data.length===0) c.innerHTML = '<p style="padding:16px;">Dictionary is empty.</p>';
  else c.innerHTML = data.map(d => `<div style="padding:12px; border-bottom:1px solid var(--border); display:flex; justify-content:space-between;"><span><strong>${d.word}</strong> → ${d.replacement}</span> <button onclick="deleteResource('dictionary', ${d.id})" style="color:#b91c1c; font-size:12px; font-weight:600; cursor:pointer; background:none; border:none;">Delete</button></div>`).join('');
}

async function fetchSnippets() {
  const res = await fetch(`${API}/snippets`);
  const data = await res.json();
  const c = document.getElementById('snippetList');
  if(data.length===0) c.innerHTML = '<p style="padding:16px;">No snippets found.</p>';
  else c.innerHTML = data.map(d => `<div style="padding:12px; border-bottom:1px solid var(--border); display:flex; justify-content:space-between;"><div><strong>${d.title}</strong><br><span style="color:var(--text-2); font-size:13px;">${d.content}</span></div> <button onclick="deleteResource('snippets', ${d.id})" style="color:#b91c1c; font-size:12px; font-weight:600; cursor:pointer; background:none; border:none;">Delete</button></div>`).join('');
}

async function fetchScratchpad() {
  const res = await fetch(`${API}/scratchpad`);
  const data = await res.json();
  document.getElementById('scratchpadArea').value = data.content || '';
}

async function loadSettings() {
  const res = await fetch(`${API}/settings`);
  const data = await res.json();
  
  const name = data['profile_name'] || '';
  document.getElementById('settingDisplayName').value = name;
  updateGreeting(name || 'there');
  
  document.getElementById('settingLaunchStartup').checked = data['launch_widget_startup'] === 'true';
  document.getElementById('settingStartMin').checked = data['start_minimized'] === 'true';
  document.getElementById('settingWindowsStartup').checked = data['start_with_windows'] === 'true';
}

document.getElementById('btnSaveSettings')?.addEventListener('click', async () => {
  const name = document.getElementById('settingDisplayName').value;
  const startup = document.getElementById('settingLaunchStartup').checked ? 'true' : 'false';
  const min = document.getElementById('settingStartMin').checked ? 'true' : 'false';
  const winStartup = document.getElementById('settingWindowsStartup').checked ? 'true' : 'false';
  
  await fetch(`${API}/settings`, { method:'POST', headers:{'Content-Type':'application/json'}, body: JSON.stringify({key:'profile_name', value:name})});
  await fetch(`${API}/settings`, { method:'POST', headers:{'Content-Type':'application/json'}, body: JSON.stringify({key:'launch_widget_startup', value:startup})});
  await fetch(`${API}/settings`, { method:'POST', headers:{'Content-Type':'application/json'}, body: JSON.stringify({key:'start_minimized', value:min})});
  await fetch(`${API}/settings`, { method:'POST', headers:{'Content-Type':'application/json'}, body: JSON.stringify({key:'start_with_windows', value:winStartup})});
  
  // Settings Saving
  if(name) updateGreeting(name);
  alert("Settings saved locally");
});

function updateGreeting(name) {
  const hour = new Date().getHours();
  let greeting = "Good morning";
  if (hour >= 12 && hour < 17) greeting = "Good afternoon";
  else if (hour >= 17 && hour < 21) greeting = "Good evening";
  else if (hour >= 21 || hour < 5) greeting = "Good night";
  
  const el = document.getElementById('homeGreeting');
  if (el) el.textContent = `${greeting}, ${name}`;
}

// ── RESET ACTIONS ──────────────────────────────────────────────
document.getElementById('btnClearHistory')?.addEventListener('click', async () => {
  console.log("Clear history clicked");
  if(!confirm("Clear all dictation history? This cannot be undone.")) return;
  await fetch(`${API}/history`, { method: 'DELETE' });
  alert("History cleared.");
  fetchDashboard();
  fetchSessions();
});

document.getElementById('btnResetAnalytics')?.addEventListener('click', async () => {
  console.log("Reset analytics clicked");
  if(!confirm("Reset all analytics? This will clear sessions to recalculate statistics.")) return;
  await fetch(`${API}/analytics`, { method: 'DELETE' });
  alert("Analytics reset.");
  fetchDashboard();
  fetchSessions();
});

document.querySelectorAll('.reset-act-btn').forEach(btn => {
  btn.addEventListener('click', async () => {
    if(!confirm("Are you sure? This deletes ALL dictations and permanently sets stats back to zero.")) return;
    await fetch(`${API}/stats/reset`, { method: 'DELETE' });
    alert("History and Analytics have been fully cleared.");
    fetchDashboard();
    fetchSessions();
  });
});

document.querySelector('.btn-share')?.addEventListener('click', () => {
  const words = document.getElementById('totalWordsVal').textContent;
  const streak = document.getElementById('streakHeaderTitle').textContent;
  const wpm = document.getElementById('statsWPM').textContent;
  const text = `🎙️ I just dictated ${words} total words using M-78 at an average speed of ${wpm} WPM! I'm on a ${streak}!`;
  try {
    const dummy = document.createElement("textarea");
    document.body.appendChild(dummy);
    dummy.value = text;
    dummy.select();
    document.execCommand("copy");
    document.body.removeChild(dummy);
    alert("Copied shareable progress to clipboard!");
  } catch(e) {
    alert("Error copying: " + text);
  }
});

// Global actions
window.deleteResource = async (type, id) => {
  if(!confirm("Are you sure?")) return;
  await fetch(`${API}/${type}/${id}`, {method: 'DELETE'});
  if(type==='dictionary') fetchDictionary();
  if(type==='snippets') fetchSnippets();
  if(type==='sessions') fetchSessions();
};

document.getElementById('btnAddDict')?.addEventListener('click', async () => {
  const w = prompt('Original word:'); if(!w) return;
  const r = prompt('Replacement:'); if(!r) return;
  await fetch(`${API}/dictionary`, {
    method:'POST', headers:{'Content-Type':'application/json'},
    body: JSON.stringify({word:w, replacement:r})
  });
  fetchDictionary();
});

document.getElementById('btnAddSnippet')?.addEventListener('click', async () => {
  const t = prompt('Snippet Title:'); if(!t) return;
  const c = prompt('Snippet Content:'); if(!c) return;
  await fetch(`${API}/snippets`, {
    method:'POST', headers:{'Content-Type':'application/json'},
    body: JSON.stringify({title:t, content:c})
  });
  fetchSnippets();
});

let scratchTimer;
document.getElementById('scratchpadArea')?.addEventListener('input', (e) => {
  clearTimeout(scratchTimer);
  scratchTimer = setTimeout(async () => {
    await fetch(`${API}/scratchpad`, {
      method:'POST', headers:{'Content-Type':'application/json'},
      body: JSON.stringify({content: e.target.value})
    });
  }, 1000);
});

// ── Widget Launch ─────────────────────────────────────────────
document.getElementById('btnLaunchWidget')?.addEventListener('click', async (e) => {
  const btn = e.currentTarget;
  const originalHtml = btn.innerHTML;
  btn.style.opacity = '0.7';
  btn.innerHTML = 'Pushing...';
  try {
    await fetch(`${API}/launch-widget`, { method: 'POST' });
  } catch(err) {
    console.warn('[M-78] Widget launch failed:', err);
  } finally {
    setTimeout(() => {
      btn.innerHTML = originalHtml;
      btn.style.opacity = '1';
    }, 800);
  }
});

// ── BOOTSTRAP ─────────────────────────────────────────────────
async function boot() {
  loadSettings();
  fetchDashboard();
  fetchSessions();
  fetchDictionary();
  fetchSnippets();
  fetchScratchpad();
  
  // By default we start on Insights unless specified, so Launch shouldn't show initially unless clicked
}

boot();
setInterval(fetchDashboard, 10_000);
setInterval(fetchSessions, 10_000);
