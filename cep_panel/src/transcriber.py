"""
LectureFlow Transcriber
Abstracts speech-to-text with word-level timestamps using Local Faster-Whisper,
ElevenLabs Scribe, or OpenAI Whisper.
"""

import os
import json
from typing import Dict, Any, List

class Transcriber:
    def __init__(self, provider: str = "local_whisper"):
        self.provider = provider.lower()

    def transcribe(self, audio_path: str, output_json: str = "transcript.json") -> Dict[str, Any]:
        if not os.path.exists(audio_path):
            raise FileNotFoundError(f"Audio file not found: {audio_path}")

        if self.provider == "local_whisper":
            return self._transcribe_local_whisper(audio_path, output_json)
        elif self.provider == "elevenlabs":
            return self._transcribe_elevenlabs(audio_path, output_json)
        elif self.provider == "openai":
            return self._transcribe_openai(audio_path, output_json)
        else:
            raise ValueError(f"Unsupported ASR provider: {self.provider}")

    def _transcribe_local_whisper(self, audio_path: str, output_json: str) -> Dict[str, Any]:
        try:
            from faster_whisper import WhisperModel
        except ImportError:
            raise ImportError(
                "faster-whisper is not installed. Run: pip install faster-whisper"
            )

        model_size = os.getenv("WHISPER_MODEL", "base")
        device = "cuda" if os.getenv("USE_CUDA", "true").lower() == "true" else "cpu"
        compute_type = "float16" if device == "cuda" else "int8"

        print(f"[ASR] Loading local Faster-Whisper model ({model_size}) on {device}...")
        model = WhisperModel(model_size, device=device, compute_type=compute_type)

        segments, info = model.transcribe(audio_path, word_timestamps=True)
        words: List[Dict[str, Any]] = []
        full_text = []

        for segment in segments:
            full_text.append(segment.text)
            if segment.words:
                for w in segment.words:
                    words.append({
                        "text": w.word,
                        "start": round(w.start, 3),
                        "end": round(w.end, 3),
                        "probability": round(w.probability, 3)
                    })

        result = {
            "language": info.language,
            "duration": round(info.duration, 2),
            "text": " ".join(full_text).strip(),
            "words": words
        }

        with open(output_json, "w", encoding="utf-8") as f:
            json.dump(result, f, indent=2, ensure_ascii=False)
        return result

    def _transcribe_elevenlabs(self, audio_path: str, output_json: str) -> Dict[str, Any]:
        import requests

        api_key = os.getenv("ELEVENLABS_API_KEY")
        if not api_key:
            raise ValueError("ELEVENLABS_API_KEY is not set in environment or .env")

        print(f"[ASR] Uploading {audio_path} to ElevenLabs Scribe API...")
        url = "https://api.elevenlabs.io/v1/speech-to-text"
        headers = {"xi-api-key": api_key}
        data = {
            "model_id": "scribe_v1",
            "timestamps_granularity": "word",
            "tag_audio_events": "true"
        }

        with open(audio_path, "rb") as f:
            files = {"file": (os.path.basename(audio_path), f, "audio/mpeg")}
            response = requests.post(url, headers=headers, data=data, files=files)

        if response.status_code != 200:
            raise RuntimeError(f"ElevenLabs Scribe failed ({response.status_code}): {response.text}")

        res_json = response.json()
        with open(output_json, "w", encoding="utf-8") as f:
            json.dump(res_json, f, indent=2, ensure_ascii=False)
        return res_json

    def _transcribe_openai(self, audio_path: str, output_json: str) -> Dict[str, Any]:
        import requests

        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise ValueError("OPENAI_API_KEY is not set in environment or .env")

        print(f"[ASR] Uploading {audio_path} to OpenAI Whisper API...")
        url = "https://api.openai.com/v1/audio/transcriptions"
        headers = {"Authorization": f"Bearer {api_key}"}
        data = {
            "model": "whisper-1",
            "response_format": "verbose_json",
            "timestamp_granularities[]": "word"
        }

        with open(audio_path, "rb") as f:
            files = {"file": (os.path.basename(audio_path), f, "audio/mpeg")}
            response = requests.post(url, headers=headers, data=data, files=files)

        if response.status_code != 200:
            raise RuntimeError(f"OpenAI Whisper failed ({response.status_code}): {response.text}")

        res_json = response.json()
        with open(output_json, "w", encoding="utf-8") as f:
            json.dump(res_json, f, indent=2, ensure_ascii=False)
        return res_json
