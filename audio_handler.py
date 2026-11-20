import os
import io
import json
import base64
import urllib.request
import soundfile as sf
from dotenv import load_dotenv

load_dotenv()


def direct_google_speech_transcribe(audio_bytes: bytes) -> str:
    """Direct, robust FLAC-based transcription using Google's Speech API.
    Does not rely on broken 32-bit flac binaries or OS subprocesses."""
    try:
        # Read audio with soundfile
        data, samplerate = sf.read(io.BytesIO(audio_bytes))
        
        # If stereo, average to mono
        if len(data.shape) > 1 and data.shape[1] > 1:
            data = data.mean(axis=1)

        # Write clean in-memory FLAC
        flac_stream = io.BytesIO()
        sf.write(flac_stream, data, samplerate, format="FLAC")
        flac_bytes = flac_stream.getvalue()

        # Call Google Speech API directly
        url = "https://www.google.com/speech-api/v2/recognize?client=chromium&lang=en-US&key=AIzaSyBOti4mM-6x9WDnZIjIeyEU21OpBXqWBgw"
        headers = {
            "Content-Type": f"audio/x-flac; rate={samplerate}",
            "User-Agent": "Mozilla/5.0"
        }

        req = urllib.request.Request(url, data=flac_bytes, headers=headers)
        with urllib.request.urlopen(req, timeout=12) as response:
            body = response.read().decode("utf-8")

        for line in body.split("\n"):
            line = line.strip()
            if not line:
                continue
            try:
                parsed = json.loads(line)
                res_list = parsed.get("result", [])
                if res_list and "alternative" in res_list[0]:
                    transcript = res_list[0]["alternative"][0].get("transcript", "")
                    if transcript:
                        print(f"[Speech Success] Transcribed: '{transcript}'")
                        return transcript.strip()
            except Exception:
                continue

        print("[Speech Warning] No speech detected in Google API response")
        return ""
    except Exception as exc:
        print(f"[Speech Error] Direct Google Speech transcription error: {exc}")
        return f"[Speech Error] {exc}"


def transcribe_with_gemini(audio_bytes: bytes, mime_type: str = "audio/wav") -> str:
    """Transcribes audio using Google Gemini multimodal REST API if configured."""
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        return ""

    try:
        model_name = os.getenv("GEMINI_MODEL", "gemini-2.5-flash")
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{model_name}:generateContent?key={api_key}"

        b64_audio = base64.b64encode(audio_bytes).decode("utf-8")
        payload = {
            "contents": [
                {
                    "parts": [
                        {
                            "inline_data": {
                                "mime_type": mime_type,
                                "data": b64_audio
                            }
                        },
                        {
                            "text": "Transcribe this spoken interview answer word for word. Return ONLY the plain transcribed text."
                        }
                    ]
                }
            ]
        }

        data_bytes = json.dumps(payload).encode("utf-8")
        headers = {"Content-Type": "application/json"}
        req = urllib.request.Request(url, data=data_bytes, headers=headers)

        with urllib.request.urlopen(req, timeout=20) as resp:
            res_json = json.loads(resp.read().decode("utf-8"))
            candidates = res_json.get("candidates", [])
            if candidates:
                parts = candidates[0].get("content", {}).get("parts", [])
                if parts:
                    text = parts[0].get("text", "").strip()
                    print(f"[Gemini Speech Success] Transcribed: '{text}'")
                    return text
        return ""
    except Exception as exc:
        print(f"[Gemini Speech Error] {exc}")
        return ""


def transcribe_audio(audio_input) -> str:
    """Master transcription function. Accepts UploadedFile, BytesIO, or bytes."""
    if audio_input is None:
        return ""

    # Extract bytes safely
    if hasattr(audio_input, "getvalue"):
        audio_bytes = audio_input.getvalue()
    elif hasattr(audio_input, "read"):
        if hasattr(audio_input, "seek"):
            audio_input.seek(0)
        audio_bytes = audio_input.read()
        if hasattr(audio_input, "seek"):
            audio_input.seek(0)
    elif isinstance(audio_input, bytes):
        audio_bytes = audio_input
    else:
        return ""

    if not audio_bytes or len(audio_bytes) < 300:
        print(f"[Speech Info] Audio too short: {len(audio_bytes) if audio_bytes else 0} bytes")
        return ""

    # Attempt 1: Gemini REST if API key is active
    if os.getenv("GEMINI_API_KEY"):
        gemini_text = transcribe_with_gemini(audio_bytes)
        if gemini_text and not gemini_text.startswith("["):
            return gemini_text

    # Attempt 2: Direct Google Speech FLAC Pipeline
    return direct_google_speech_transcribe(audio_bytes)
