// timer.js — countdown timer widget

let _totalSeconds = 0;
let _remaining = 0;
let _intervalId = null;
let _paused = false;
let _lastTick = null;

function el(id) { return document.getElementById(id); }

function format(seconds) {
  const h = Math.floor(seconds / 3600);
  const m = Math.floor((seconds % 3600) / 60);
  const s = seconds % 60;
  if (h > 0) return `${h}:${String(m).padStart(2, "0")}:${String(s).padStart(2, "0")}`;
  return `${String(m).padStart(2, "0")}:${String(s).padStart(2, "0")}`;
}

function updateDisplay() {
  el("timer-display").textContent = format(Math.max(0, Math.ceil(_remaining)));
}

function tick() {
  const now = performance.now();
  if (_lastTick !== null && !_paused) {
    const delta = (now - _lastTick) / 1000;
    _remaining -= delta;
  }
  _lastTick = now;

  updateDisplay();

  if (_remaining <= 0) {
    stopTimer();
    el("timer-display").textContent = "Done! ⏰";
    document.dispatchEvent(new CustomEvent("timerDone"));
  }
}

export function startTimer(seconds) {
  stopTimer();
  _totalSeconds = seconds;
  _remaining = seconds;
  _paused = false;
  _lastTick = performance.now();
  el("timer-widget").classList.remove("hidden");
  updateDisplay();
  _intervalId = setInterval(tick, 250);
}

export function stopTimer() {
  if (_intervalId) { clearInterval(_intervalId); _intervalId = null; }
  _lastTick = null;
}

export function pauseTimer() {
  _paused = !_paused;
  el("btn-timer-pause").textContent = _paused ? "Resume" : "Pause";
  if (!_paused) _lastTick = performance.now();
}

export function resetTimer() {
  _remaining = _totalSeconds;
  _paused = false;
  el("btn-timer-pause").textContent = "Pause";
  _lastTick = performance.now();
  updateDisplay();
}

// Recalc on tab focus to avoid drift
document.addEventListener("visibilitychange", () => {
  if (!document.hidden && _intervalId && !_paused) {
    _lastTick = performance.now();
  }
});

// Wire up buttons
document.addEventListener("DOMContentLoaded", () => {
  el("btn-timer-pause")?.addEventListener("click", pauseTimer);
  el("btn-timer-reset")?.addEventListener("click", resetTimer);
});
