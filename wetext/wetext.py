# Copyright (c) 2024 Zhendong Peng (pzd17@tsinghua.org.cn)
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import re

from kaldifst import TextNormalizer as normalizer
from modelscope import snapshot_download

from .token_parser import TokenParser


class Normalizer:
    def __init__(
        self,
        tagger_path=None,
        verbalizer_path=None,
        lang="auto",
        operator="tn",
        remove_erhua=False,
        enable_0_to_9=False,
    ):
        self.lang = lang
        self.operator = operator
        self.taggers = {}
        self.verbalizers = {}
        if tagger_path is None or verbalizer_path is None:
            repo_dir = snapshot_download("pengzhendong/wetext")
            assert lang in ("auto", "en", "zh") and operator in ("tn", "itn")

            taggers = {"en": "tagger.fst", "zh": "tagger.fst"}
            verbalizers = {"en": "verbalizer.fst", "zh": "verbalizer.fst"}
            if operator == "itn" and enable_0_to_9:
                taggers["zh"] = "tagger_enable_0_to_9.fst"
            if operator == "tn" and remove_erhua:
                verbalizers["zh"] = "verbalizer_remove_erhua.fst"

            for lang in ("en", "zh"):
                if self.lang in ("auto", lang):
                    self.taggers[lang] = normalizer(f"{repo_dir}/{lang}/{operator}/{taggers[lang]}")
                    self.verbalizers[lang] = normalizer(f"{repo_dir}/{lang}/{operator}/{verbalizers[lang]}")
        else:
            assert lang in ("en", "zh"), "Language must be 'en' or 'zh' when using custom tagger and verbalizer."
            self.taggers[lang] = normalizer(tagger_path)
            self.verbalizers[lang] = normalizer(verbalizer_path)

    def tag(self, text, lang=None):
        lang = lang or self.lang
        return self.taggers[lang](text)

    def verbalize(self, text, lang=None):
        lang = lang or self.lang
        text = TokenParser(lang, self.operator).reorder(text)
        return self.verbalizers[lang](text)

    @staticmethod
    def contains_chinese(string):
        for ch in string:
            if "\u4e00" <= ch <= "\u9fff":
                return True
        return False

    def normalize(self, text):
        if self.operator == "itn" or bool(re.search(r"\d", text)):
            lang = self.lang
            if lang == "auto":
                lang = "zh" if Normalizer.contains_chinese(text) else "en"
            return self.verbalize(self.tag(text, lang), lang)
        return text
