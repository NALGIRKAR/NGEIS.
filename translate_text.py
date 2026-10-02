# translate_text.py
"""
Chinese-to-English text translation.

Architecture:
  PRIMARY:  SeamlessM4T running inside WSL2 on port 5001
            (T2TT mode — best quality, no rate limits)
  FALLBACK: argostranslate (fully offline, no rate limits)
  LAST:     deep-translator / Google Translate API
"""

import logging
import time

logger = logging.getLogger(__name__)

# SeamlessM4T backend URL (running inside WSL2)
SEAMLESS_URL = "http://localhost:5001"


# ── SeamlessM4T backend (WSL2) ─────────────────────────────────────────────

def _seamless_available() -> bool:
    try:
        import requests as http_requests
        r = http_requests.get(f"{SEAMLESS_URL}/health", timeout=2)
        return r.status_code == 200
    except Exception:
        return False


def _translate_via_seamless(text: str) -> str:
    import requests as http_requests
    r = http_requests.post(
        f"{SEAMLESS_URL}/translate_text",
        json={"text": text},
        timeout=60,
    )
    data = r.json()
    if "error" in data:
        raise RuntimeError(f"SeamlessM4T error: {data['error']}")
    return data["translation"]


# ── Argostranslate fallback (offline) ───────────────────────────────────────

_argo_translator = None


def _load_argos():
    global _argo_translator
    if _argo_translator is not None:
        return _argo_translator

    import argostranslate.package
    import argostranslate.translate

    logger.info("Setting up argostranslate zh→en…")
    argostranslate.package.update_package_index()
    available = argostranslate.package.get_available_packages()

    pkg = next(
        (p for p in available if p.from_code == "zh" and p.to_code == "en"),
        None,
    )
    if pkg is None:
        raise RuntimeError("Could not find argostranslate zh→en package.")

    installed = argostranslate.package.get_installed_packages()
    installed_codes = {(p.from_code, p.to_code) for p in installed}
    if ("zh", "en") not in installed_codes:
        logger.info("Installing zh→en language pack…")
        argostranslate.package.install_from_path(pkg.download())

    _argo_translator = argostranslate.translate.get_translation_from_codes("zh", "en")
    logger.info("argostranslate ready.")
    return _argo_translator


# ── Last resort: deep-translator ────────────────────────────────────────────

def _deep_translate(text: str) -> str:
    from deep_translator import GoogleTranslator
    time.sleep(1)
    return GoogleTranslator(source="zh-CN", target="en").translate(text)


# ── Public API ──────────────────────────────────────────────────────────────

def translate_text(text: str) -> str:
    """Translate Chinese text to English.

    Priority:
      1. SeamlessM4T (WSL2 backend) — best quality
      2. argostranslate (offline) — no rate limits
      3. Google Translate API — last resort

    Args:
        text: Chinese string to translate.
    Returns:
        English translation.
    """
    if not isinstance(text, str) or not text.strip():
        raise ValueError("text must be a non-empty string")

    # 1. Try SeamlessM4T
    if _seamless_available():
        logger.info("Using SeamlessM4T backend (WSL2)")
        try:
            return _translate_via_seamless(text)
        except Exception as exc:
            logger.warning(f"SeamlessM4T failed ({exc}), falling back…")

    # 2. Try argostranslate (offline)
    try:
        translator = _load_argos()
        result = translator.translate(text)
        if result and result.strip():
            logger.info("Using argostranslate (offline)")
            return result.strip()
    except Exception as exc:
        logger.warning(f"argostranslate failed ({exc}), falling back to Google API…")

    # 3. Last resort: Google Translate
    logger.info("Using Google Translate API (last resort)")
    return _deep_translate(text)
