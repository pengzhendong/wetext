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

from functools import lru_cache
from importlib.resources import files
from pathlib import Path

import kaldifst
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


def fst_path(fst_path):
    return str(files("wetext.fsts").joinpath(fst_path))


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
    "date": ["year", "month", "day", "preserve_order"],
    "fraction": ["sign", "numerator", "denominator"],
    "measure": ["numerator", "denominator", "value", "units"],
    "money": ["currency", "value", "decimal", "quantity"],
    "time": ["hour", "minute", "second", "noon", "zone"],
    "telephone": ["country_code", "number_part"],
    "electronic": ["username", "domain", "protocol"],
}
EN_ITN_ORDERS = ITN_ORDERS
FSTS = {
    "preprocess": {
        "traditional_to_simple": load_fst("traditional_to_simple.fst"),
    },
    "en": {
        "tn": {
            "tagger": load_fst("en/tn/tagger.fst"),
            "verbalizer": load_fst("en/tn/verbalizer.fst"),
        },
        "itn": {
            "tagger": load_fst("en/itn/tagger.fst"),
            "verbalizer": load_fst("en/itn/verbalizer.fst"),
        },
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
    "ja": {
        "tn": {
            "tagger": load_fst("ja/tn/tagger.fst"),
            "verbalizer": load_fst("ja/tn/verbalizer.fst"),
        },
        "itn": {
            "tagger": load_fst("ja/itn/tagger.fst"),
            "tagger_enable_0_to_9": load_fst("ja/itn/tagger_enable_0_to_9.fst"),
            "verbalizer": load_fst("ja/itn/verbalizer.fst"),
        },
    },
    "postprocess": {
        "full_to_half": load_fst("full_to_half.fst"),
        "remove_interjections": load_fst("remove_interjections.fst"),
        "remove_puncts": load_fst("remove_puncts.fst"),
        "tag_oov": load_fst("tag_oov.fst"),
    },
}

FST_PATHS = {
    "preprocess": {"traditional_to_simple": fst_path("traditional_to_simple.fst")},
    "postprocess": {
        "full_to_half": fst_path("full_to_half.fst"),
        "remove_interjections": fst_path("remove_interjections.fst"),
        "remove_puncts": fst_path("remove_puncts.fst"),
        "tag_oov": fst_path("tag_oov.fst"),
    },
    "en": {
        "tn": {"tagger": fst_path("en/tn/tagger.fst"), "verbalizer": fst_path("en/tn/verbalizer.fst")},
        "itn": {"tagger": fst_path("en/itn/tagger.fst"), "verbalizer": fst_path("en/itn/verbalizer.fst")},
    },
    "zh": {
        "tn": {
            "tagger": fst_path("zh/tn/tagger.fst"),
            "verbalizer": fst_path("zh/tn/verbalizer.fst"),
            "verbalizer_remove_erhua": fst_path("zh/tn/verbalizer_remove_erhua.fst"),
        },
        "itn": {
            "tagger": fst_path("zh/itn/tagger.fst"),
            "tagger_enable_0_to_9": fst_path("zh/itn/tagger_enable_0_to_9.fst"),
            "verbalizer": fst_path("zh/itn/verbalizer.fst"),
        },
    },
    "ja": {
        "tn": {"tagger": fst_path("ja/tn/tagger.fst"), "verbalizer": fst_path("ja/tn/verbalizer.fst")},
        "itn": {
            "tagger": fst_path("ja/itn/tagger.fst"),
            "tagger_enable_0_to_9": fst_path("ja/itn/tagger_enable_0_to_9.fst"),
            "verbalizer": fst_path("ja/itn/verbalizer.fst"),
        },
    },
}


@lru_cache(maxsize=None)
def get_prefix_fst(lang, operator, enable_0_to_9=False):
    """Load the optional semantic prefix graph for streaming normalization.

    Older model bundles do not contain these graphs.  Returning ``None`` lets
    the streaming API degrade safely by buffering until ``flush()``.
    """

    use_digit_graph = operator == "itn" and enable_0_to_9 and lang != "en"
    filename = "prefix_enable_0_to_9.fst" if use_digit_graph else "prefix.fst"
    path = Path(fst_path(f"{lang}/{operator}/{filename}"))
    if not path.is_file():
        return None
    graph = kaldifst.StdVectorFst.read(str(path))
    for state in kaldifst.StateIterator(graph):
        graph.set_final(state, 0.0)
    return graph
