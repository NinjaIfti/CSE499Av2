import requests
from flask import current_app

HEALTH_CHECK_TIMEOUT = 5

def _strip_trailing_slash(url):
    return url.rstrip('/') if url else url

def check_service(name, base_url, path="/"):
    """Ping a service; returns (status, message). status is 'up' or 'down'."""
    url = _strip_trailing_slash(base_url) + path
    try:
        r = requests.get(url, timeout=HEALTH_CHECK_TIMEOUT)
        r.raise_for_status()
        return ("up", "Running")
    except requests.exceptions.Timeout:
        return ("down", "Timeout")
    except requests.exceptions.ConnectionError:
        return ("down", "Unreachable")
    except requests.exceptions.HTTPError as e:
        return ("down", str(e)[:80])
    except Exception as e:
        return ("down", str(e)[:80])

def check_all_services():
    """Check OCR, Whisper, LLM. Returns dict with status and message per service."""
    cfg = current_app.config
    ocr_url = cfg.get("OCR_SERVICE_URL") or ""
    whisper_url = cfg.get("WHISPER_SERVICE_URL") or ""
    llm_url = cfg.get("LLM_SERVICE_URL") or ""

    ocr_status, ocr_msg = check_service("OCR", ocr_url) if ocr_url else ("down", "No URL set")
    whisper_status, whisper_msg = check_service("Whisper", whisper_url) if whisper_url else ("down", "No URL set")
    llm_status, llm_msg = check_service("LLM", llm_url) if llm_url else ("down", "No URL set")

    return {
        "ocr": {"status": ocr_status, "message": ocr_msg, "url": _strip_trailing_slash(ocr_url) or None},
        "whisper": {"status": whisper_status, "message": whisper_msg, "url": _strip_trailing_slash(whisper_url) or None},
        "llm": {"status": llm_status, "message": llm_msg, "url": _strip_trailing_slash(llm_url) or None},
        "all_up": ocr_status == "up" and whisper_status == "up" and llm_status == "up",
    }
