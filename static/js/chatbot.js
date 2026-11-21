(function () {
  "use strict";

  const win = document.getElementById("chat-window");
  if (!win) return;

  const toggleBtn = document.getElementById("chat-toggle");
  const closeBtn = document.getElementById("chat-close");
  const clearBtn = document.getElementById("chat-clear");
  const body = document.getElementById("chat-messages");
  const form = document.getElementById("chat-form");
  const input = document.getElementById("chat-input");
  const sendBtn = form.querySelector("button[type=submit]");
  const URLS = {
    message: win.dataset.messageUrl,
    history: win.dataset.historyUrl,
    clear: win.dataset.clearUrl,
  };
  const WELCOME = "Hi there! 👋 I'm Spice Bot. I can help with orders, payments, refunds, delivery and our menu.";

  let busy = false;
  let loaded = false;
  let lastText = "";

  function csrfToken() {
    const match = document.cookie.match(/(?:^|;\s*)csrftoken=([^;]+)/);
    return match ? decodeURIComponent(match[1]) : "";
  }

  function timeLabel(iso) {
    const date = iso ? new Date(iso) : new Date();
    return date.toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" });
  }

  function scrollDown() {
    body.scrollTop = body.scrollHeight;
  }

  // textContent is used everywhere so user input can never inject HTML.
  function bubble(role, text, when) {
    const wrap = document.createElement("div");
    wrap.className = "msg " + role;
    wrap.textContent = text;
    const time = document.createElement("div");
    time.className = "msg-time";
    time.textContent = timeLabel(when);
    wrap.appendChild(time);
    body.appendChild(wrap);
    scrollDown();
    return wrap;
  }

  function addQuickReplies(wrap, options) {
    if (!options || !options.length) return;
    const row = document.createElement("div");
    row.className = "msg-quick";
    options.forEach(function (label) {
      const button = document.createElement("button");
      button.type = "button";
      button.textContent = label;
      button.addEventListener("click", function () {
        row.remove();
        send(label === "Retry" ? lastText : label);
      });
      row.appendChild(button);
    });
    wrap.appendChild(row);
  }

  function showTyping() {
    const el = document.createElement("div");
    el.className = "msg bot typing";
    el.innerHTML = "<span></span><span></span><span></span>";
    body.appendChild(el);
    scrollDown();
    return el;
  }

  async function send(raw) {
    const text = (raw || "").trim();
    if (!text || busy) return;
    busy = true;
    sendBtn.disabled = true;
    lastText = text;
    input.value = "";
    bubble("user", text, null);
    const dots = showTyping();

    try {
      const res = await fetch(URLS.message, {
        method: "POST",
        credentials: "same-origin",
        headers: { "Content-Type": "application/json", "X-CSRFToken": csrfToken() },
        body: JSON.stringify({ message: text }),
      });
      const data = await res.json().catch(function () { return {}; });
      dots.remove();
      if (!res.ok) throw new Error(data.error || "Server error");
      addQuickReplies(bubble("bot", data.reply, null), data.quick_replies);
    } catch (err) {
      dots.remove();
      addQuickReplies(
        bubble("bot", "Sorry, I couldn't reach the server. Please check your connection and try again.", null),
        ["Retry"]
      );
    } finally {
      busy = false;
      sendBtn.disabled = false;
      input.focus();
    }
  }

  async function loadHistory() {
    if (loaded) return;
    loaded = true;
    try {
      const res = await fetch(URLS.history, { credentials: "same-origin" });
      const data = await res.json();
      if (!data.messages.length) {
        bubble("bot", WELCOME, null);
        return;
      }
      data.messages.forEach(function (m) {
        bubble(m.role === "user" ? "user" : "bot", m.text, m.created_at);
      });
    } catch (err) {
      bubble("bot", WELCOME, null);
    }
  }

  function openChat() {
    win.hidden = false;
    toggleBtn.setAttribute("aria-expanded", "true");
    loadHistory();
    input.focus();
  }

  function closeChat() {
    win.hidden = true;
    toggleBtn.setAttribute("aria-expanded", "false");
    toggleBtn.focus();
  }

  toggleBtn.addEventListener("click", function () {
    if (win.hidden) openChat(); else closeChat();
  });
  closeBtn.addEventListener("click", closeChat);

  form.addEventListener("submit", function (event) {
    event.preventDefault();
    send(input.value);
  });

  document.querySelectorAll("[data-quick]").forEach(function (button) {
    button.addEventListener("click", function () {
      if (win.hidden) openChat();
      send(button.dataset.quick);
    });
  });

  clearBtn.addEventListener("click", async function () {
    if (!window.confirm("Clear this conversation?")) return;
    await fetch(URLS.clear, {
      method: "POST",
      credentials: "same-origin",
      headers: { "X-CSRFToken": csrfToken() },
    });
    body.innerHTML = "";
    bubble("bot", WELCOME, null);
  });

  document.addEventListener("keydown", function (event) {
    if (event.key === "Escape" && !win.hidden) closeChat();
  });
})();
