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

from typing import Literal, Optional

from wetext.utils import normalize


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
            remove_erhua: Whether to remove erhua for TN.
            enable_0_to_9: Whether to enable 0-to-9 conversion for ITN.
        """
        self.lang = lang
        self.operator = operator
        self.traditional_to_simple = traditional_to_simple
        self.full_to_half = full_to_half
        self.remove_interjections = remove_interjections
        self.remove_puncts = remove_puncts
        self.tag_oov = tag_oov
        self.enable_0_to_9 = enable_0_to_9
        self.remove_erhua = remove_erhua

    def normalize(
        self,
        text: str,
        lang: Optional[Literal["auto", "en", "zh"]] = None,
        operator: Optional[Literal["tn", "itn"]] = None,
        traditional_to_simple: bool = False,
        full_to_half: bool = False,
        remove_interjections: bool = False,
        remove_puncts: bool = False,
        tag_oov: bool = False,
        enable_0_to_9: bool = False,
        remove_erhua: bool = False,
    ) -> str:
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
        text = normalize(
            text,
            lang or self.lang,
            operator or self.operator,
            traditional_to_simple or self.traditional_to_simple,
            full_to_half or self.full_to_half,
            remove_interjections or self.remove_interjections,
            remove_puncts or self.remove_puncts,
            tag_oov or self.remove_puncts,
            enable_0_to_9 or self.enable_0_to_9,
            remove_erhua or self.remove_erhua,
        )
        return text
