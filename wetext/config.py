# Copyright (c) 2025 Zhendong Peng (pzd17@tsinghua.org.cn)
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

from dataclasses import dataclass
from typing import Literal


@dataclass
class NormalizerConfig:
    """Configuration for text normalization."""

    lang: Literal["auto", "en", "zh"] = "auto"
    """Language of the input text ('auto' for automatic detection)."""

    operator: Literal["tn", "itn"] = "tn"
    """Normalization operator: 'tn' (text normalization) or 'itn' (inverse text normalization)."""

    fix_contractions: bool = False
    """Whether to fix English contractions (e.g., "don't" -> "do not")."""

    traditional_to_simple: bool = False
    """Convert traditional Chinese characters to simplified Chinese."""

    full_to_half: bool = False
    """Convert full-width characters (e.g., "Ａ") to half-width (e.g., "A")."""

    remove_interjections: bool = False
    """Remove interjections (e.g., "um", "ah")."""

    remove_puncts: bool = False
    """Remove all punctuation marks."""

    tag_oov: bool = False
    """Tag out-of-vocabulary words with a special marker."""

    enable_0_to_9: bool = False
    """Convert numbers to words (e.g., "1" -> "one") during ITN."""

    remove_erhua: bool = False
    """Remove 'erhua' suffixes in Chinese (e.g., "哪儿" -> "哪")."""
