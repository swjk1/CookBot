// chat.js — WebSocket chat + step management

import { speak } from "./tts.js";
import { startTimer } from "./timer.js";
import { highlightStep } from "./recipe.js";

let _ws = null;
let _sessionId = null;
let _recipe = null;

function el(id) { return document.getElementById(id); }

function esc(s) {
  return String(s).replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;");
}

function appendBubble(text, role) {
  const msgs = el("chat-messages");
  const div = document.createElement("div");
  div.className = `chat-bubble bubble-${role}`;
  div.textContent = text;
  msgs.appendChild(div);
  msgs.scrollTop = msgs.scrollHeight;
}

function updateStepUI(payload) {
  const { step_index, step_number, total_steps, instruction, tips = [], ingredients_used = [], duration_seconds } = payload;

  // Progress bar
  el("step-label").textContent = `Step ${step_number} of ${total_steps}`;
  el("progress-fill").style.width = `${(step_number / total_steps) * 100}%`;

  // Step card
  el("step-instruction").textContent = instruction;

  const tipsEl = el("step-tips");
  tipsEl.innerHTML = tips.length ? tips.map(t => `<span>${esc(t)}</span>`).join("<br>") : "";

  const ingEl = el("step-ingredients");
  ingEl.innerHTML = ingredients_used.map(i => `<span class="ingredient-chip">${esc(i)}</span>`).join("");

  // Sidebar highlight
  highlightStep(step_index);
}

function handleEvent(event) {
  const { type, payload } = event;

  if (type === "step_change") {
    updateStepUI(payload);
    speak(payload.instruction);
    if (payload.duration_seconds) {
      startTimer(payload.duration_seconds);
    }
  } else if (type === "bot_message") {
    appendBubble(payload.content, "bot");
    speak(payload.content);
  } else if (type === "timer_start") {
    startTimer(payload.duration_seconds);
  } else if (type === "error") {
    appendBubble(`⚠️ ${payload.message}`, "bot");
  }
}

export async function startCookingSession(recipe, sessionId) {
  _recipe = recipe;
  _sessionId = sessionId;

  // Show chat UI
  el("chat-empty").classList.add("hidden");
  el("chat-active").classList.remove("hidden");
  el("chat-messages").innerHTML = "";
  el("timer-widget").classList.add("hidden");

  // Connect WebSocket
  if (_ws) { _ws.close(); }
  const proto = location.protocol === "https:" ? "wss" : "ws";
  _ws = new WebSocket(`${proto}://${location.host}/ws/chat/${sessionId}`);

  _ws.onmessage = (e) => {
    try {
      const event = JSON.parse(e.data);
      handleEvent(event);
    } catch (err) {
      console.error("WS parse error:", err);
    }
  };

  _ws.onerror = (e) => {
    appendBubble("Connection error. Please refresh.", "bot");
  };

  _ws.onclose = () => {
    console.log("WebSocket closed");
  };
}

export function sendMessage(text) {
  if (!_ws || _ws.readyState !== WebSocket.OPEN) {
    console.warn("WebSocket not connected");
    return;
  }
  appendBubble(text, "user");
  _ws.send(JSON.stringify({ text }));
}

// Wire up input
document.addEventListener("DOMContentLoaded", () => {
  const input = el("chat-input");
  const btn = el("btn-send");

  function submit() {
    const text = input.value.trim();
    if (!text) return;
    input.value = "";
    sendMessage(text);
  }

  btn?.addEventListener("click", submit);
  input?.addEventListener("keydown", (e) => {
    if (e.key === "Enter" && !e.shiftKey) { e.preventDefault(); submit(); }
  });
});

// Jump to step from sidebar click
document.addEventListener("jumpToStep", (e) => {
  if (_ws && _ws.readyState === WebSocket.OPEN) {
    // We can't directly set step_index via WS message without backend support.
    // For now, send "next" repeatedly or just send the step request as a message.
    // Simple approach: tell the bot to go to that step via text.
    // TODO: add a dedicated WS message type for step jump
  }
});
