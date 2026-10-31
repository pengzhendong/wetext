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

from collections.abc import Mapping
from functools import lru_cache
from itertools import product
from importlib.resources import files
from pathlib import Path

from wetext.languages import LANGUAGES

import kaldifst
from kaldifst import TextNormalizer as normalizer


@lru_cache(maxsize=None)
def load_fst(fst_path) -> normalizer:
    """
    Load a FST from the fsts directory.

    Args:
        fst_path: The path to the FST file.
    Returns:
        The loaded FST.
    """
    fst_path = files("wetext").joinpath("fsts", fst_path)
    return normalizer(str(fst_path))


def fst_path(fst_path):
    return str(files("wetext").joinpath("fsts", fst_path))


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
KO_TN_ORDERS = {
    "date": ["era", "year", "month", "day", "weekday", "range_start"],
    "fraction": ["negative", "integer_part", "denominator", "numerator", "particle"],
    "measure": [
        "negative",
        "integer_part",
        "denominator",
        "numerator",
        "particle",
        "integer",
        "fractional_part",
        "units",
    ],
    "money": ["integer_part", "currency_maj", "minor_part"],
    "time": ["suffix", "hours", "minutes", "seconds"],
}
KO_ITN_ORDERS = {
    "cardinal": ["negative", "integer"],
    "date": ["year", "month", "day"],
    "decimal": ["negative", "integer_part", "fractional_part", "quantity"],
    "fraction": ["negative", "integer_part", "numerator", "denominator", "suffix"],
    "measure": ["negative", "numerator", "denominator", "value", "units"],
    "money": ["currency", "value"],
    "ordinal": ["integer", "counter", "suffix"],
    "telephone": ["number_part"],
    "time": ["prefix", "hours", "minutes", "seconds", "suffix"],
    "whitelist": ["value"],
    "word": ["value"],
}
DE_TN_ORDERS = {
    "date": ["day", "month", "year"],
    "measure": [
        "kind",
        "prefix",
        "negative",
        "integer",
        "integer_part",
        "fractional_part",
        "quantity",
        "numerator",
        "denominator",
        "units",
    ],
    "money": ["kind", "negative", "integer_part", "fractional_part", "quantity", "currency"],
    "time": ["hours", "minutes", "seconds", "zone"],
}
DE_ITN_ORDERS = {
    "date": ["day", "month", "year"],
    "electronic": ["protocol", "username", "domain"],
    "measure": [
        "prefix",
        "negative",
        "fraction_negative",
        "integer",
        "integer_part",
        "conjunction",
        "numerator",
        "denominator",
        "fractional_part",
        "quantity",
        "units",
    ],
    "money": ["currency", "integer_part", "fractional_part", "quantity", "conjunction", "minor_part", "currency_minor"],
    "time": ["kind", "hours", "minutes", "seconds", "zone"],
}
EN_ITN_ORDERS = ITN_ORDERS
FST_PATHS = {
    "preprocess": {
        "traditional_to_simple": fst_path("traditional_to_simple.fst"),
    },
    "en": {
        "tn": {
            "tagger": fst_path("en/tn/tagger.fst"),
            "verbalizer": fst_path("en/tn/verbalizer.fst"),
        },
        "itn": {
            "tagger": fst_path("en/itn/tagger.fst"),
            "verbalizer": fst_path("en/itn/verbalizer.fst"),
        },
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
            "verbalizer_enable_0_to_9": fst_path("zh/itn/verbalizer_enable_0_to_9.fst"),
            "verbalizer": fst_path("zh/itn/verbalizer.fst"),
        },
    },
    "ja": {
        "tn": {
            "tagger": fst_path("ja/tn/tagger.fst"),
            "verbalizer": fst_path("ja/tn/verbalizer.fst"),
        },
        "itn": {
            "tagger": fst_path("ja/itn/tagger.fst"),
            "tagger_enable_0_to_9": fst_path("ja/itn/tagger_enable_0_to_9.fst"),
            "verbalizer_enable_0_to_9": fst_path("ja/itn/verbalizer_enable_0_to_9.fst"),
            "verbalizer": fst_path("ja/itn/verbalizer.fst"),
        },
    },
    "de": {
        "tn": {
            name: fst_path(f"de/tn/{name}.fst")
            for name in ("tagger", "verbalizer", "tagger_nondeterministic", "verbalizer_nondeterministic")
        },
        "itn": {name: fst_path(f"de/itn/{name}.fst") for name in ("tagger", "verbalizer")},
    },
    "processors": {
        "".join(flags): fst_path("processors/{}.fst".format("".join(flags)))
        for flags in product("01", repeat=5)
        if "1" in flags
    },
    "ko": {
        operator: {name: fst_path("ko/{}/{}.fst".format(operator, name)) for name in ("tagger", "verbalizer")}
        for operator in ("tn", "itn")
    },
    "postprocess": {
        "full_to_half": fst_path("full_to_half.fst"),
        "remove_interjections": fst_path("remove_interjections.fst"),
        "remove_puncts": fst_path("remove_puncts.fst"),
        "tag_oov": fst_path("tag_oov.fst"),
    },
}


for _lang, _pipeline in LANGUAGES.items():
    if _lang in FST_PATHS:
        continue
    FST_PATHS[_lang] = {}
    for _operator in ("tn", "itn"):
        _suffixes = [""]
        if _operator == "tn" and _pipeline["tn_deterministic"]:
            _suffixes.append("_nondeterministic")
        if _operator == "itn" and _pipeline["itn_cased"]:
            _suffixes.append("_cased")
        FST_PATHS[_lang][_operator] = {
            name + suffix: fst_path(f"{_lang}/{_operator}/{name}{suffix}.fst")
            for name in ("tagger", "verbalizer")
            for suffix in _suffixes
        }


class _LazyFsts(Mapping):
    """Resolve model handles only on first use of each graph."""

    def __init__(self, paths):
        self.paths = paths
        self.groups = {key: _LazyFsts(value) for key, value in paths.items() if isinstance(value, dict)}

    def __getitem__(self, key):
        if key in self.groups:
            return self.groups[key]
        return load_fst(self.paths[key])

    def __iter__(self):
        return iter(self.paths)

    def __len__(self):
        return len(self.paths)


FSTS = _LazyFsts(FST_PATHS)


@lru_cache(maxsize=None)
def get_prefix_fst(lang, operator, enable_0_to_9=False):
    """Load the optional semantic prefix graph for streaming normalization.

    Older model bundles do not contain these graphs.  Returning ``None`` lets
    the streaming API degrade safely by buffering until ``flush()``.
    """

    use_digit_graph = operator == "itn" and enable_0_to_9 and lang in ("zh", "ja")
    filename = "prefix_enable_0_to_9.fst" if use_digit_graph else "prefix.fst"
    path = Path(fst_path(f"{lang}/{operator}/{filename}"))
    if not path.is_file():
        return None
    graph = kaldifst.StdVectorFst.read(str(path))
    for state in kaldifst.StateIterator(graph):
        graph.set_final(state, 0.0)
    return graph


@lru_cache(maxsize=None)
def get_prefix_matcher_fst(lang, operator, enable_0_to_9=False):
    """Load the optional input-only graph for batched suffix search."""

    use_digit_graph = operator == "itn" and enable_0_to_9 and lang in ("zh", "ja")
    filename = "prefix_matcher_enable_0_to_9.fst" if use_digit_graph else "prefix_matcher.fst"
    path = Path(fst_path(f"{lang}/{operator}/{filename}"))
    if not path.is_file():
        return None
    return kaldifst.StdVectorFst.read(str(path))


PROCESSOR_OPTIONS = ("traditional_to_simple", "remove_interjections", "remove_puncts", "full_to_half", "tag_oov")


def processor_key(options):
    return "".join("1" if options.get(name, False) else "0" for name in PROCESSOR_OPTIONS)


@lru_cache(maxsize=None)
def get_token_orders(lang, operator):
    path = files("wetext").joinpath("fsts", lang, operator, "token_orders.json")
    import json

    return json.loads(path.read_text(encoding="utf-8"))
