import json
import os
from functools import lru_cache
from typing import Dict, List, Optional, Any, TYPE_CHECKING

from box import Box

if TYPE_CHECKING:
    from gui import GUI


def split_keys(keys):
    final = []
    for key in keys.split('.'):
        final.append(f'["{key}"]')
    return ''.join(final)


class I18nManager:
    instance = None
    _translations: Dict[str, Dict[str, Any]]
    _lang: str

    def __init__(self, gui: 'GUI'):
        self.__class__.instance = self  # Assign as singleton
        # Load the current language until loader handles the rest
        self._translations = {}
        self.load_translations(gui.config.language)
        self._lang = gui.config.language

    def load_translations(self, lang: str):
        """Load a translation file from the translations directory"""
        from gui.defaults import Defaults
        with open(os.path.join(Defaults.TRANSLATIONS_DIR, f'{lang}.json'), 'r', encoding='utf-8') as f:
            self._translations[lang] = Box(json.load(f))

    @property
    def language(self) -> str:
        """Get the current language"""
        return self._lang

    @language.setter
    def language(self, lang: str):
        """Set the current language and load its translations"""
        if lang not in self._translations:
            raise ValueError(f"Language '{lang}' not available. Available languages: {self.available_languages}")
        self._lang = lang

    @property
    def available_languages(self) -> List[str]:
        """Get the available languages"""
        return list(self._translations.keys())

    def _get_nested_value(self, key_path: str) -> Optional[str]:
        """Get a value from a nested dictionary using a dot-separated key path"""
        box = self._translations[self._lang]
        try:
            return eval(f'box{split_keys(key_path)}')
        except (KeyError, TypeError, AttributeError):
            return None

    def t(self, key: str, default: Optional[str] = None) -> str:
        """Translate a key to the current language and format it with the given parameters"""
        if self._lang in self._translations:
            translation = self._get_nested_value(key)
            if translation is not None:
                return translation
        return default or key


@lru_cache(maxsize=500)  # Cache translations for performance
def _t(key: str, default: Optional[str] = None) -> str:
    """Translate a key to the current language and format it with the given parameters"""
    return I18nManager.instance.t(key, default)


def t(key: str, default: Optional[str] = None, **kwargs):
    """Helper function to translate a key with optional formatting parameters"""
    return _t(key, default).format(**kwargs)
