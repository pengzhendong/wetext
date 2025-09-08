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
from typing import Literal

from wetext.constants import FSTS
from wetext.token_parser import TokenParser


def get_lang(text: str) -> Literal["en", "zh"]:
    """
    Get the language of the text.

    Args:
        text: The text to get the language of.
    Returns:
        The language of the text.
    """
    contains_chinese = False
    for ch in text:
        if "\u4e00" <= ch <= "\u9fff":
            contains_chinese = True
    return "zh" if contains_chinese or text.isdigit() else "en"


def preprocess(text: str, traditional_to_simple: bool = False) -> str:
    """
    Preprocess the text before normalization.

    Args:
        text: The text to preprocess.
        traditional_to_simple: Whether to convert traditional Chinese to simplified Chinese.
    Returns:
        The preprocessed text.
    """
    if traditional_to_simple:
        text = FSTS["preprocess"]["traditional_to_simple"](text)
    return text.strip()


def postprocess(
    text: str,
    full_to_half: bool = False,
    remove_interjections: bool = False,
    remove_puncts: bool = False,
    tag_oov: bool = False,
) -> str:
    """
    Postprocess the text after normalization.

    Args:
        text: The text to postprocess.
        full_to_half: Whether to convert full-width characters to half-width characters.
        remove_interjections: Whether to remove interjections.
        remove_puncts: Whether to remove punctuation.
        tag_oov: Whether to tag out-of-vocabulary words.
    Returns:
        The postprocessed text.
    """
    if full_to_half:
        text = FSTS["postprocess"]["full_to_half"](text)
    if remove_interjections:
        text = FSTS["postprocess"]["remove_interjections"](text)
    if remove_puncts:
        text = FSTS["postprocess"]["remove_puncts"](text)
    if tag_oov:
        text = FSTS["postprocess"]["tag_oov"](text)
    return text.strip()


def should_normalize(text: str, operator: Literal["tn", "itn"], remove_erhua: bool = False) -> bool:
    """
    Check if the text should be normalized.

    Args:
        text: The text to check.
        operator: The operator to use.
        remove_erhua: Whether to remove erhua for TN.
    Returns:
        True if the text should be normalized, False otherwise.
    """
    if operator == "tn":
        if bool(re.search(r"\d", text)):
            return True
        if remove_erhua and re.search(r"儿|兒", text):
            return True
        return False
    return len(text) > 0


def reorder(text: str, lang: Literal["en", "zh"], operator: Literal["tn", "itn"]) -> str:
    """
    Reorder the text.

    Args:
        text: The text to reorder.
        lang: The language of the text.
    Returns:
        The reordered text.
    """
    return TokenParser(lang, operator).reorder(text)


def tag(text: str, lang: Literal["en", "zh"], operator: Literal["tn", "itn"], enable_0_to_9: bool = False) -> str:
    """
    Tag the text.

    Args:
        text: The text to tag.
        lang: The language of the text.
        operator: The operator to use.
        enable_0_to_9: Whether to enable 0-to-9 conversion for ITN.
    Returns:
        The tagged text.
    """
    tagger = FSTS[lang][operator]["tagger"]
    if enable_0_to_9 and lang == "zh" and operator == "itn":
        tagger = FSTS["zh"]["itn"]["tagger_enable_0_to_9"]
    return tagger(text).strip()


def verbalize(text: str, lang: Literal["en", "zh"], operator: Literal["tn", "itn"], remove_erhua: bool = False) -> str:
    """
    Verbalize the text.

    Args:
        text: The text to verbalize.
        lang: The language of the text.
        operator: The operator to use.
        remove_erhua: Whether to remove erhua for TN.
    Returns:
        The verbalized text.
    """
    verbalizer = FSTS[lang][operator]["verbalizer"]
    if remove_erhua and lang == "zh" and operator == "tn":
        verbalizer = FSTS["zh"]["tn"]["verbalizer_remove_erhua"]
    return verbalizer(text).strip()


def normalize(
    text: str,
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
    Normalize the text.

    Args:
        text: The text to normalize.
        lang: The language of the text.
        operator: The operator to use.
        traditional_to_simple: Whether to convert traditional Chinese to simplified Chinese.
        full_to_half: Whether to convert full-width characters to half-width characters.
        remove_interjections: Whether to remove interjections.
        remove_puncts: Whether to remove punctuation.
        tag_oov: Whether to tag out-of-vocabulary words.
        remove_erhua: Whether to remove erhua for TN.
        enable_0_to_9: Whether to enable 0-to-9 conversion for ITN.
    Returns:
        The normalized text.
    """
    text = preprocess(text, traditional_to_simple)
    if should_normalize(text, operator, remove_erhua):
        if lang == "auto":
            lang = get_lang(text)
        if lang == "en" and operator == "itn":
            # ITN for English is not supported now, using ITN for Chinese instead.
            lang = "zh"
        text = tag(text, lang, operator, enable_0_to_9)
        text = reorder(text, lang, operator)
        text = verbalize(text, lang, operator, remove_erhua)
    text = postprocess(text, full_to_half, remove_interjections, remove_puncts, tag_oov)
    return text
