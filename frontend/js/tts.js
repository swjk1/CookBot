// tts.js — text-to-speech playback

let _enabled = true;
let _currentAudio = null;

export function isTTSEnabled() { return _enabled; }

export function toggleTTS() {
  _enabled = !_enabled;
  document.getElementById("btn-tts-toggle").textContent = _enabled ? "🔊" : "🔇";
  if (!_enabled && _currentAudio) {
    _currentAudio.pause();
    _currentAudio = null;
  }
}

export async function speak(text) {
  if (!_enabled || !text) return;

  // Stop any playing audio
  if (_currentAudio) {
    _currentAudio.pause();
    _currentAudio = null;
  }

  try {
    const res = await fetch("/tts", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ text }),
    });

    if (!res.ok) {
      console.warn("TTS request failed:", res.status);
      return;
    }

    const blob = await res.blob();
    const url = URL.createObjectURL(blob);
    _currentAudio = new Audio(url);
    _currentAudio.onended = () => URL.revokeObjectURL(url);
    await _currentAudio.play();
  } catch (e) {
    console.warn("TTS error:", e);
  }
}

document.addEventListener("DOMContentLoaded", () => {
  document.getElementById("btn-tts-toggle")?.addEventListener("click", toggleTTS);
});
