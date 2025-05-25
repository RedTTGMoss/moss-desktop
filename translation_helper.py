import json
import os

from box import Box

from gui.i18n import split_keys


class TranslationTree:
    def __init__(self, lang):
        self.lang = lang
        self.file = os.path.join('assets', 'translations', f'{lang}.json')
        with open(self.file, encoding="utf-8") as _:
            self._translations = Box(json.load(_), default_box=True)

    @property
    def translations(self):
        return self._translations

    @translations.setter
    def translations(self, value):  # Autosave
        self._translations = value
        self.save()

    def save(self):
        with open(self.file, 'w', encoding="utf-8") as _:
            json.dump(self._translations, _, indent=4, ensure_ascii=False, sort_keys=True)

    def __getitem__(self, item):
        return eval(f'self._translations.{item}')

    def __setitem__(self, key, value):
        return eval(f'self._translations.{key} = value')

    @property
    def keys(self):
        def allocator(base: str, d: dict):
            for k, v in d.items():
                if isinstance(v, dict):
                    yield from allocator(f'{base}{k}.', v)
                else:
                    yield f'{base}{k}'

        return allocator('', self._translations)

    def join(self, other: 'TranslationTree', keep_old):
        keys_from_other = set(other.keys)
        keys_from_self = set(self.keys)
        old_keys: set
        if keep_old:
            old_keys = keys_from_self
        else:
            old_keys = keys_from_self & keys_from_other
        new = Box(default_box=True)
        for key in old_keys:
            exec(f'new{split_keys(key)} = self._translations{split_keys(key)}')

        new_keys = keys_from_other - old_keys
        for key in new_keys:
            exec(f'new{split_keys(key)} = key')
        self.translations = new


if __name__ == '__main__':
    en = TranslationTree('en')
    langs = []
    for file in os.listdir(os.path.join('assets', 'translations')):
        if file.endswith('.json') and file != 'en.json':
            langs.append(TranslationTree(file[:-5]))

    print("Joining all languages with English...")
    for lang in langs:
        lang.join(en, keep_old=False)
    en.save()
