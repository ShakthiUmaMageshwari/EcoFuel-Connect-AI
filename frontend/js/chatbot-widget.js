/**
 * EcoFuel Connect AI — Floating Chatbot Widget
 * Include this script on any page to add the bottom-right chatbot.
 * Usage: <script src="js/chatbot-widget.js"></script>
 */
(function() {
  'use strict';

  // Inject styles
  const style = document.createElement('style');
  style.textContent = `
    /* ── Chatbot Widget ── */
    #ecob-fab {
      position: fixed; bottom: 28px; right: 28px; z-index: 9999;
      width: 60px; height: 60px; border-radius: 50%;
      background: linear-gradient(135deg, #16a34a, #0d9488);
      box-shadow: 0 6px 24px rgba(22,163,74,0.45);
      cursor: pointer; border: none;
      display: flex; align-items: center; justify-content: center;
      transition: transform 0.25s, box-shadow 0.25s;
      animation: ecob-pulse 3s infinite;
    }
    #ecob-fab:hover { transform: scale(1.12); box-shadow: 0 8px 32px rgba(22,163,74,0.55); }
    @keyframes ecob-pulse {
      0%,100% { box-shadow: 0 6px 24px rgba(22,163,74,0.45); }
      50%      { box-shadow: 0 6px 24px rgba(22,163,74,0.7),  0 0 0 8px rgba(22,163,74,0.12); }
    }
    #ecob-badge {
      position: absolute; top: -3px; right: -3px;
      background: #ef4444; color: #fff; font-size: 0.65rem; font-weight: 800;
      width: 20px; height: 20px; border-radius: 50%;
      display: flex; align-items: center; justify-content: center;
      border: 2px solid #fff;
    }
    #ecob-panel {
      position: fixed; bottom: 104px; right: 28px; z-index: 9998;
      width: 368px; max-width: calc(100vw - 32px);
      background: #fff; border: 1.5px solid #e2e8f0;
      border-radius: 20px; box-shadow: 0 20px 60px rgba(0,0,0,0.18);
      display: none; flex-direction: column; overflow: hidden;
      animation: ecob-slide 0.28s cubic-bezier(.34,1.56,.64,1);
      max-height: 560px;
    }
    @keyframes ecob-slide {
      from { transform: translateY(20px) scale(0.95); opacity: 0; }
      to   { transform: translateY(0) scale(1);       opacity: 1; }
    }
    #ecob-panel.open { display: flex; }
    /* Header */
    .ecob-header {
      background: linear-gradient(135deg, #166534, #0d9488);
      padding: 16px 18px; display: flex; align-items: center; gap: 12px;
    }
    .ecob-avatar {
      width: 40px; height: 40px; background: rgba(255,255,255,0.2);
      border-radius: 50%; display: flex; align-items: center; justify-content: center;
      flex-shrink: 0;
    }
    .ecob-header-text h4 { color: #fff; font-size: 0.97rem; font-weight: 700; margin: 0; }
    .ecob-header-text p  { color: rgba(255,255,255,0.75); font-size: 0.75rem; margin: 2px 0 0; }
    .ecob-close {
      margin-left: auto; background: none; border: none; color: rgba(255,255,255,0.8);
      cursor: pointer; font-size: 1.3rem; line-height: 1; padding: 4px;
      border-radius: 6px; transition: background 0.15s;
    }
    .ecob-close:hover { background: rgba(255,255,255,0.15); color: #fff; }
    /* Messages */
    #ecob-messages {
      flex: 1; overflow-y: auto; padding: 16px; display: flex; flex-direction: column; gap: 12px;
      scroll-behavior: smooth;
    }
    .ecob-msg { display: flex; gap: 8px; max-width: 88%; }
    .ecob-msg.user { flex-direction: row-reverse; align-self: flex-end; }
    .ecob-msg.bot  { align-self: flex-start; }
    .ecob-bubble {
      padding: 10px 14px; border-radius: 16px;
      font-size: 0.875rem; line-height: 1.55; white-space: pre-wrap; word-break: break-word;
    }
    .ecob-msg.bot  .ecob-bubble { background: #f0fdf4; color: #14532d; border: 1px solid #bbf7d0; border-bottom-left-radius: 4px; }
    .ecob-msg.user .ecob-bubble { background: linear-gradient(135deg,#16a34a,#0d9488); color: #fff; border-bottom-right-radius: 4px; }
    .ecob-bot-icon { width: 30px; height: 30px; background: #dcfce7; border-radius: 50%; flex-shrink: 0; display: flex; align-items: center; justify-content: center; margin-top: 2px; }
    /* Typing indicator */
    .ecob-typing { display: flex; gap: 5px; padding: 12px 14px; background: #f0fdf4; border: 1px solid #bbf7d0; border-radius: 16px; border-bottom-left-radius: 4px; }
    .ecob-dot { width: 7px; height: 7px; background: #16a34a; border-radius: 50%; animation: ecob-bounce 1.2s infinite; }
    .ecob-dot:nth-child(2) { animation-delay: 0.2s; }
    .ecob-dot:nth-child(3) { animation-delay: 0.4s; }
    @keyframes ecob-bounce { 0%,60%,100%{transform:translateY(0)} 30%{transform:translateY(-6px)} }
    /* Quick suggestions */
    #ecob-suggestions {
      padding: 8px 16px 4px; display: flex; gap: 7px; overflow-x: auto; flex-wrap: nowrap;
      scrollbar-width: none; border-top: 1px solid #f1f5f9;
    }
    #ecob-suggestions::-webkit-scrollbar { display: none; }
    .ecob-chip {
      flex-shrink: 0; background: #f0fdf4; border: 1px solid #86efac;
      border-radius: 999px; padding: 5px 12px;
      font-size: 0.76rem; font-weight: 600; color: #166534;
      cursor: pointer; white-space: nowrap; transition: background 0.15s;
    }
    .ecob-chip:hover { background: #dcfce7; }
    /* Input */
    .ecob-input-row {
      display: flex; gap: 8px; padding: 12px 14px;
      border-top: 1px solid #f1f5f9; background: #fafafa;
    }
    #ecob-input {
      flex: 1; border: 1.5px solid #e2e8f0; border-radius: 999px;
      padding: 9px 16px; font-size: 0.88rem; outline: none;
      transition: border-color 0.2s; background: #fff;
    }
    #ecob-input:focus { border-color: #16a34a; }
    #ecob-send {
      width: 40px; height: 40px; border-radius: 50%;
      background: linear-gradient(135deg,#16a34a,#0d9488);
      border: none; cursor: pointer; display: flex; align-items: center; justify-content: center;
      flex-shrink: 0; transition: transform 0.15s, opacity 0.15s;
    }
    #ecob-send:hover { transform: scale(1.08); }
    #ecob-send:disabled { opacity: 0.5; cursor: not-allowed; }
    @media(max-width:480px){
      #ecob-panel { width: calc(100vw - 20px); right: 10px; bottom: 90px; }
      #ecob-fab   { bottom: 18px; right: 18px; width: 52px; height: 52px; }
    }
  `;
  document.head.appendChild(style);

  // ── Build Widget HTML ──────────────────────────────────────────────────
  const panelHTML = `
    <div id="ecob-panel">
      <div class="ecob-header">
        <div class="ecob-avatar">
          <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="#fff" stroke-width="2.5"><polygon points="13 2 3 14 12 14 11 22 21 10 12 10 13 2"/></svg>
        </div>
        <div class="ecob-header-text">
          <h4>EcoBot AI</h4>
          <p>&#127807; EcoFuel Connect Assistant</p>
        </div>
        <button class="ecob-close" id="ecob-close-btn" aria-label="Close chat">&#10005;</button>
      </div>
      <div id="ecob-messages"></div>
      <div id="ecob-suggestions"></div>
      <div class="ecob-input-row">
        <input id="ecob-input" type="text" placeholder="Ask me about eco-fuels..." autocomplete="off" maxlength="300">
        <button id="ecob-send" aria-label="Send message">
          <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="#fff" stroke-width="2.5"><line x1="22" y1="2" x2="11" y2="13"/><polygon points="22 2 15 22 11 13 2 9 22 2"/></svg>
        </button>
      </div>
    </div>
    <button id="ecob-fab" aria-label="Open EcoBot AI Chat">
      <svg width="28" height="28" viewBox="0 0 24 24" fill="none" stroke="#fff" stroke-width="2.5"><path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"/></svg>
      <div id="ecob-badge">AI</div>
    </button>
  `;
  const wrapper = document.createElement('div');
  wrapper.innerHTML = panelHTML;
  document.body.appendChild(wrapper);

  // ── State ──────────────────────────────────────────────────────────────
  let isOpen        = false;
  let conversation  = [];
  let isTyping      = false;

  const panel    = document.getElementById('ecob-panel');
  const fab      = document.getElementById('ecob-fab');
  const closeBtn = document.getElementById('ecob-close-btn');
  const input    = document.getElementById('ecob-input');
  const sendBtn  = document.getElementById('ecob-send');
  const messages = document.getElementById('ecob-messages');
  const sugg     = document.getElementById('ecob-suggestions');
  const badge    = document.getElementById('ecob-badge');

  // ── Open/Close ─────────────────────────────────────────────────────────
  function togglePanel() {
    isOpen = !isOpen;
    panel.classList.toggle('open', isOpen);
    badge.style.display = isOpen ? 'none' : 'flex';
    fab.querySelector('svg path') && void(0);
    if (isOpen && !conversation.length) {
      addBotMessage("Hello! 👋 I'm **EcoBot**, your AI assistant for sustainable fuels.\n\nAsk me about Biogas, Bio-CNG, cost savings, carbon footprint, government schemes, or how to install alternative fuels at home!", [
        'What is Biogas?', 'Best fuel for my car?', 'Cost vs petrol', 'Carbon savings'
      ]);
    }
    if (isOpen) setTimeout(() => input.focus(), 50);
  }
  fab.addEventListener('click', togglePanel);
  closeBtn.addEventListener('click', togglePanel);

  // ── Messages ────────────────────────────────────────────────────────────
  function addBotMessage(text, suggestions) {
    const msgDiv = document.createElement('div');
    msgDiv.className = 'ecob-msg bot';
    msgDiv.innerHTML = `
      <div class="ecob-bot-icon">
        <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="#16a34a" stroke-width="2.5"><polygon points="13 2 3 14 12 14 11 22 21 10 12 10 13 2"/></svg>
      </div>
      <div class="ecob-bubble">${text.replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>').replace(/`(.*?)`/g, '<code>$1</code>')}</div>`;
    messages.appendChild(msgDiv);
    messages.scrollTop = messages.scrollHeight;

    if (suggestions && suggestions.length) {
      setSuggestions(suggestions);
    }
  }

  function addUserMessage(text) {
    const msgDiv = document.createElement('div');
    msgDiv.className = 'ecob-msg user';
    msgDiv.innerHTML = `<div class="ecob-bubble">${escapeHtml(text)}</div>`;
    messages.appendChild(msgDiv);
    messages.scrollTop = messages.scrollHeight;
  }

  function showTyping() {
    const t = document.createElement('div');
    t.className = 'ecob-msg bot'; t.id = 'ecob-typing-row';
    t.innerHTML = `<div class="ecob-bot-icon"><svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="#16a34a" stroke-width="2.5"><polygon points="13 2 3 14 12 14 11 22 21 10 12 10 13 2"/></svg></div><div class="ecob-typing"><div class="ecob-dot"></div><div class="ecob-dot"></div><div class="ecob-dot"></div></div>`;
    messages.appendChild(t);
    messages.scrollTop = messages.scrollHeight;
  }

  function hideTyping() {
    const t = document.getElementById('ecob-typing-row');
    if (t) t.remove();
  }

  function setSuggestions(chips) {
    sugg.innerHTML = '';
    chips.forEach(c => {
      const chip = document.createElement('button');
      chip.className = 'ecob-chip';
      chip.textContent = c;
      chip.addEventListener('click', () => sendMessage(c));
      sugg.appendChild(chip);
    });
  }

  function escapeHtml(str) {
    return str.replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;');
  }

  // ── Send ────────────────────────────────────────────────────────────────
  async function sendMessage(text) {
    if (!text || isTyping) return;
    text = text.trim();
    if (!text) return;

    addUserMessage(text);
    input.value = '';
    sugg.innerHTML = '';
    sendBtn.disabled = true;
    isTyping = true;

    showTyping();

    try {
      const res = await fetch('/api/chatbot/message', {
        method: 'POST',
        headers: {'Content-Type':'application/json'},
        body: JSON.stringify({ message: text, conversation: conversation.slice(-5) })
      });
      const data = await res.json();
      conversation = data.conversation || conversation;

      await new Promise(r => setTimeout(r, 600)); // Simulate natural delay
      hideTyping();
      addBotMessage(data.response, data.suggestions);
    } catch(e) {
      await new Promise(r => setTimeout(r, 400));
      hideTyping();
      addBotMessage("Sorry, I can't connect to the server right now. Please ensure the EcoFuel backend is running on port 5000. Meanwhile, check our [AI Features page](/ai-features.html) for interactive tools!", ['Try again', 'View AI Features']);
    } finally {
      isTyping = false;
      sendBtn.disabled = false;
      setTimeout(() => input.focus(), 50);
    }
  }

  sendBtn.addEventListener('click', () => sendMessage(input.value));
  input.addEventListener('keydown', e => { if (e.key === 'Enter' && !e.shiftKey) sendMessage(input.value); });

  // ── Auto-show badge after 3s if not yet opened ──────────────────────────
  setTimeout(() => {
    if (!isOpen) badge.style.display = 'flex';
  }, 3000);

  console.log('[EcoBot] Chatbot widget loaded — ready to chat!');
})();
