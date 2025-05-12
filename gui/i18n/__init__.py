import json
import os
from typing import Dict, List, Optional, Any
# from gui.defaults import Defaults
class I18nManager:
    _instance = None
    _translations: Dict[str, Dict[str, Any]] = {}
    _current_language: str = "en"
    
    def __new__(cls):
        if cls._instance is None:
            # Circular import...
            # config = json.load(open(Defaults.CONFIG_FILE_PATH))
            config = json.load(open("config.json"))
            cls._instance = super(I18nManager, cls).__new__(cls)
            cls._instance._load_translations()
            if config.get("language"):
                cls._instance.set_language(config.get("language"))
            else:
                cls._instance.set_language("en")
                
        return cls._instance
    
    def _load_translations(self):
        """Load all translation files from the translations directory"""
        translations_dir = os.path.join(os.path.dirname(__file__), "translations")
        for filename in os.listdir(translations_dir):
            if filename.endswith('.json'):
                lang = filename[:-5]  # Remove .json extension
                with open(os.path.join(translations_dir, filename), 'r', encoding='utf-8') as f:
                    self._translations[lang] = json.load(f)
    
    def set_language(self, lang: str):
        """Set the current language"""
        if lang in self._translations:
            self._current_language = lang
            return True
        return False
    
    def get_language(self) -> str:
        """Get the current language"""
        return self._current_language
    
    def get_locale(self) -> str:
        """Get the current locale"""
        return self._current_language
    
    def get_available_languages(self) -> List[str]:
        """Get the available languages"""
        return list(self._translations.keys())
    
    def _get_nested_value(self, data: Dict[str, Any], key_path: str) -> Optional[str]:
        """Get a value from a nested dictionary using a dot-separated key path"""
        keys = key_path.split('.')
        current = data
        
        for key in keys:
            if isinstance(current, dict) and key in current:
                current = current[key]
            else:
                return None
                
        return str(current) if current is not None else None
    
    def t(self, key: str, default: Optional[str] = None, **kwargs) -> str:
        """Translate a key to the current language and format it with the given parameters"""
        if self._current_language in self._translations:
            translation = self._get_nested_value(self._translations[self._current_language], key)
            if translation is not None:
                try:
                    return translation.format(**kwargs)
                except KeyError:
                    return translation
        return default or key
    
# Must be initialized before gui.
i18n = I18nManager()

def t(key: str, **kwargs):
    """Helper function to translate a key with optional formatting parameters"""
    return i18n.t(key, **kwargs)