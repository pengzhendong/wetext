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

from importlib.resources import files

from kaldifst import TextNormalizer as normalizer


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


EOS = "<EOS>"
TN_ORDERS = {
    "date": ["year", "month", "day"],
    "fraction": ["denominator", "numerator"],
    "measure": ["denominator", "numerator", "value"],
    "money": ["value", "currency"],
    "time": ["noon", "hour", "minute", "second"],
}
EN_TN_ORDERS = {
    "date": ["preserve_order", "text", "day", "month", "year"],
    "money": ["integer_part", "fractional_part", "quantity", "currency_maj"],
}
ITN_ORDERS = {
    "date": ["year", "month", "day"],
    "fraction": ["sign", "numerator", "denominator"],
    "measure": ["numerator", "denominator", "value"],
    "money": ["currency", "value", "decimal"],
    "time": ["hour", "minute", "second", "noon"],
}
FSTS = {
    "preprocess": {
        "traditional_to_simple": load_fst("traditional_to_simple.fst"),
    },
    "en": {
        "tn": {
            "tagger": load_fst("en/tn/tagger.fst"),
            "verbalizer": load_fst("en/tn/verbalizer.fst"),
        }
    },
    "zh": {
        "tn": {
            "tagger": load_fst("zh/tn/tagger.fst"),
            "verbalizer": load_fst("zh/tn/verbalizer.fst"),
            "verbalizer_remove_erhua": load_fst("zh/tn/verbalizer_remove_erhua.fst"),
        },
        "itn": {
            "tagger": load_fst("zh/itn/tagger.fst"),
            "tagger_enable_0_to_9": load_fst("zh/itn/tagger_enable_0_to_9.fst"),
            "verbalizer": load_fst("zh/itn/verbalizer.fst"),
        },
    },
    "postprocess": {
        "full_to_half": load_fst("full_to_half.fst"),
        "remove_interjections": load_fst("remove_interjections.fst"),
        "remove_puncts": load_fst("remove_puncts.fst"),
        "tag_oov": load_fst("tag_oov.fst"),
    },
}
