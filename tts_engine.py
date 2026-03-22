"""
tts_engine.py
TTSEngine — wraps pyttsx3 for spatial audio guidance.
"""

import pyttsx3
import threading


class TTSEngine:
    """
    Initialises pyttsx3, sets voice properties, and exposes
    a thread-safe speak() method so the main app is never blocked.
    """

    def __init__(self, rate: int = 160, volume: float = 1.0, language: str = "en"):
        self.rate = rate
        self.volume = volume
        self.language = language
        self._lock = threading.Lock()
        self._engine = self._init_engine()

    # ------------------------------------------------------------------
    # Initialisation
    # ------------------------------------------------------------------
    def _init_engine(self) -> pyttsx3.Engine:
        engine = pyttsx3.init()
        engine.setProperty("rate", self.rate)
        engine.setProperty("volume", self.volume)

        # Pick a voice matching the requested language code
        voices = engine.getProperty("voices")
        for voice in voices:
            if self.language.lower() in voice.id.lower():
                engine.setProperty("voice", voice.id)
                break

        return engine

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------
    def speak(self, text: str) -> None:
        """
        Speak text in a background thread so the UI stays responsive.
        Concurrent calls are serialised via a lock.
        """
        thread = threading.Thread(target=self._speak_blocking, args=(text,), daemon=True)
        thread.start()

    def speak_blocking(self, text: str) -> None:
        """Speak text synchronously (blocks caller until done)."""
        self._speak_blocking(text)

    def stop(self) -> None:
        """Interrupt any in-progress speech."""
        with self._lock:
            try:
                self._engine.stop()
            except RuntimeError:
                pass

    def set_rate(self, rate: int) -> None:
        self.rate = rate
        self._engine.setProperty("rate", rate)

    def set_volume(self, volume: float) -> None:
        self.volume = volume
        self._engine.setProperty("volume", volume)

    # ------------------------------------------------------------------
    # Internal
    # ------------------------------------------------------------------
    def _speak_blocking(self, text: str) -> None:
        with self._lock:
            self._engine.say(text)
            self._engine.runAndWait()
