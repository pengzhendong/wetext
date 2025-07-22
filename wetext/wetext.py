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

import logging
import re
from typing import Literal, Optional

from wetext.token_parser import TokenParser
from wetext.utils import contains_chinese, load_fst

logging.basicConfig(level=logging.INFO)


class Normalizer:
    def __init__(
        self,
        lang: Literal["auto", "en", "zh"] = "auto",
        operator: Literal["tn", "itn"] = "tn",
        traditional_to_simple: bool = False,
        full_to_half: bool = False,
        remove_interjections: bool = False,
        remove_puncts: bool = False,
        tag_oov: bool = False,
        enable_0_to_9: bool = False,
        remove_erhua: bool = False,
    ):
        """
        Initialize the Normalizer.
        Args:
            lang: The language of the text.
            operator: The operator to use.
            traditional_to_simple: Whether to convert traditional Chinese to simplified Chinese.
            full_to_half: Whether to convert full-width characters to half-width characters.
            remove_interjections: Whether to remove interjections.
            remove_puncts: Whether to remove punctuation.
            tag_oov: Whether to tag out-of-vocabulary words.
            remove_erhua: Whether to remove erhua.
            enable_0_to_9: Whether to enable 0-to-9 conversion.
        """
        self.lang = lang
        self.operator = operator
        self.traditional_to_simple = load_fst("traditional_to_simple.fst") if traditional_to_simple else None
        self.full_to_half = load_fst("full_to_half.fst") if full_to_half else None
        self.remove_interjections = load_fst("remove_interjections.fst") if remove_interjections else None
        self.remove_puncts = load_fst("remove_puncts.fst") if remove_puncts else None
        self.tag_oov = load_fst("tag_oov.fst") if tag_oov else None
        self.enable_0_to_9 = enable_0_to_9
        self.remove_erhua = remove_erhua

        tagger = "tagger_enable_0_to_9.fst" if operator == "itn" and self.enable_0_to_9 else "tagger.fst"
        verbalizer = "verbalizer_remove_erhua.fst" if operator == "tn" and self.remove_erhua else "verbalizer.fst"
        self.taggers = {"zh": load_fst(f"zh/{operator}/{tagger}")}
        self.verbalizers = {"zh": load_fst(f"zh/{operator}/{verbalizer}")}
        if self.operator == "tn":
            self.taggers["en"] = load_fst("en/tn/tagger.fst")
            self.verbalizers["en"] = load_fst("en/tn/verbalizer.fst")

    def preprocess(self, text: str) -> str:
        """
        Preprocess the text before normalization.
        Args:
            text: The text to preprocess.
        Returns:
            The preprocessed text.
        """
        if self.traditional_to_simple is not None:
            text = self.traditional_to_simple(text)
        return text.strip()

    def postprocess(self, text: str) -> str:
        """
        Postprocess the text after normalization.
        Args:
            text: The text to postprocess.
        Returns:
            The postprocessed text.
        """
        if self.full_to_half is not None:
            text = self.full_to_half(text)
        if self.remove_interjections is not None:
            text = self.remove_interjections(text)
        if self.remove_puncts is not None:
            text = self.remove_puncts(text)
        if self.tag_oov is not None:
            text = self.tag_oov(text)
        return text.strip()

    def tag(self, text: str, lang: Literal["en", "zh"]) -> str:
        """
        Tag the text.
        Args:
            text: The text to tag.
            lang: The language of the text.
        Returns:
            The tagged text.
        """
        return self.taggers[lang](text).strip()

    def reorder(self, text: str, lang: Literal["en", "zh"]) -> str:
        """
        Reorder the text.
        Args:
            text: The text to reorder.
            lang: The language of the text.
        Returns:
            The reordered text.
        """
        return TokenParser(lang, self.operator).reorder(text)

    def verbalize(self, text: str, lang: Literal["en", "zh"]) -> str:
        """
        Verbalize the text.
        Args:
            text: The text to verbalize.
            lang: The language of the text.
        Returns:
            The verbalized text.
        """
        return self.verbalizers[lang](text).strip()

    def should_normalize(self, text: str) -> bool:
        """
        Check if the text should be normalized.
        Args:
            text: The text to check.
        Returns:
            True if the text should be normalized, False otherwise.
        """
        if self.operator == "tn":
            if bool(re.search(r"\d", text)):
                return True
            if self.remove_erhua and re.search(r"儿|兒", text):
                return True
            return False
        return len(text) > 0

    def get_lang(self, text: str) -> Literal["en", "zh"]:
        """
        Get the language of the text.
        Args:
            text: The text to get the language of.
        Returns:
            The language of the text.
        """
        return "zh" if contains_chinese(text) or text.isdigit() else "en"

    def normalize(self, text: str, lang: Optional[Literal["auto", "en", "zh"]] = None) -> str:
        """
        Normalize the text.
        Args:
            text: The text to normalize.
            lang: The language of the text.
        Returns:
            The normalized text.
        """
        text = self.preprocess(text)
        if self.should_normalize(text):
            lang = lang or self.lang
            if lang == "auto":
                lang = self.get_lang(text)
            if lang == "en" and self.operator == "itn":
                logging.warning("ITN for English is not supported now, using ITN for Chinese instead.")
                lang = "zh"
            text = self.tag(text, lang)
            text = self.reorder(text, lang)
            text = self.verbalize(text, lang)
        text = self.postprocess(text)
        return text
