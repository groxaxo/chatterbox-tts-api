'''
Multilingual support for the TTS model

Updated to support all 23 languages from the official Chatterbox multilingual model.
This includes full Chinese (zh) support with the latest version.
'''

# Supported languages for the multilingual model (23 languages)
# Updated from official ResembleAI/chatterbox repository
SUPPORTED_LANGUAGES = {
  "ar": "Arabic",
  "da": "Danish",
  "de": "German",
  "el": "Greek",
  "en": "English",
  "es": "Spanish",
  "fi": "Finnish",
  "fr": "French",
  "he": "Hebrew",
  "hi": "Hindi",
  "it": "Italian",
  "ja": "Japanese",
  "ko": "Korean",
  "ms": "Malay",
  "nl": "Dutch",
  "no": "Norwegian",
  "pl": "Polish",
  "pt": "Portuguese",
  "ru": "Russian",
  "sv": "Swedish",
  "sw": "Swahili",
  "tr": "Turkish",
  "zh": "Chinese",  # Now fully supported in official release
}