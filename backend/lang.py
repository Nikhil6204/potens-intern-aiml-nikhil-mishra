"""
Language detection for the multilingual flow.

We use `langdetect` (local, free, no API call) to identify the query
language. This drives two things:
  1. Which language we instruct the LLM to answer in.
  2. Whether we mark the response as machine-translated at the boundary,
     which the UI surfaces to the user (translation quality != source
     document quality, and we don't want to blur that line).

langdetect is unreliable on very short strings (e.g. a 2-word query), so we
fall back to English if detection fails or the input is too short to trust.
"""
from langdetect import detect, DetectorFactory, LangDetectException

DetectorFactory.seed = 0  # deterministic detection

LANGUAGE_NAMES = {
    "en": "English", "es": "Spanish", "fr": "French", "de": "German",
    "it": "Italian", "pt": "Portuguese", "nl": "Dutch", "ru": "Russian",
    "zh-cn": "Chinese", "zh-tw": "Chinese (Traditional)", "ja": "Japanese",
    "ko": "Korean", "ar": "Arabic", "hi": "Hindi", "bn": "Bengali",
    "ur": "Urdu", "tr": "Turkish", "vi": "Vietnamese", "th": "Thai",
    "pl": "Polish", "sv": "Swedish", "fi": "Finnish", "el": "Greek",
    "he": "Hebrew", "id": "Indonesian", "ta": "Tamil", "te": "Telugu",
    "mr": "Marathi", "gu": "Gujarati", "kn": "Kannada", "ml": "Malayalam",
    "pa": "Punjabi",
}


def detect_language(text: str) -> dict:
    text = (text or "").strip()
    if len(text) < 3:
        return {"code": "en", "name": "English", "confident": False}
    try:
        code = detect(text)
    except LangDetectException:
        return {"code": "en", "name": "English", "confident": False}

    name = LANGUAGE_NAMES.get(code, code)
    return {"code": code, "name": name, "confident": True}
