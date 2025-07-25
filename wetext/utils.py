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

from importlib.resources import files

from kaldifst import TextNormalizer as normalizer


def contains_chinese(text: str) -> bool:
    """
    Check if the text contains Chinese characters.
    Args:
        text: The text to check.
    Returns:
        True if the text contains Chinese characters, False otherwise.
    """
    for ch in text:
        if "\u4e00" <= ch <= "\u9fff":
            return True
    return False


def load_fst(fst_path) -> normalizer:
    """
    Load a FST from the fsts directory.
    Args:
        fst_path: The path to the FST file.
    Returns:
        The loaded FST.
    """
    fst_path = files("wetext.fsts").joinpath(fst_path)
    return normalizer(str(fst_path))
