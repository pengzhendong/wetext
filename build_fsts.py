# Copyright (c) 2025 Zhendong Peng (pzd17@tsinghua.org.cn)
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""Build the runtime FSTs from the official WeTextProcessing pipelines.

Run this script with the WeTextProcessing source tree on ``PYTHONPATH``.  The
official Normalizer classes own the rule inventory, weights, and graph
composition; keeping those details there prevents this runtime build from
drifting whenever upstream adds or restructures a rule.
"""

import argparse
import json
from importlib import import_module
from itertools import product
from pathlib import Path

import pynini

from itn.chinese.inverse_normalizer import InverseNormalizer as ZhInverseNormalizer
from itn.english.inverse_normalizer import InverseNormalizer as EnInverseNormalizer
from itn.german.inverse_normalizer import InverseNormalizer as DeInverseNormalizer
from itn.japanese.inverse_normalizer import InverseNormalizer as JaInverseNormalizer
from tn.chinese.normalizer import Normalizer as ZhNormalizer
from tn.chinese.rules.postprocessor import PostProcessor
from tn.english.normalizer import Normalizer as EnNormalizer
from tn.german.normalizer import Normalizer as DeNormalizer
from tn.japanese.normalizer import Normalizer as JaNormalizer

from itn.korean.inverse_normalizer import InverseNormalizer as KoInverseNormalizer
from tn.korean.normalizer import Normalizer as KoNormalizer

FST_DIR = Path("wetext/fsts")
LANGUAGES = json.loads((Path(__file__).parent / "wetext/language_registry.json").read_text(encoding="utf-8"))


class _StreamingPrefixMixin:
    """Capture the semantic classifier graph used by streaming normalization.

    The normal tagger contains catch-all character/word rules, so every input
    is accepted and it cannot tell the runtime whether a trailing fragment may
    grow into a normalization rule.  The prefix graph excludes those fallback
    rules while keeping its inventory in sync with the official normalizer.
    """

    _stream_fallback_rules = frozenset(("char", "punctuation", "word"))

    def tagger_union(self, rule_specs):
        rule_specs = tuple(rule_specs)
        semantic_rules = tuple(spec for spec in rule_specs if spec.rule.name not in self._stream_fallback_rules)
        if not semantic_rules:
            raise RuntimeError("streaming prefix graph has no semantic rules")
        self.stream_prefix_tagger = super().tagger_union(semantic_rules).star
        return super().tagger_union(rule_specs)


class StreamingZhInverseNormalizer(_StreamingPrefixMixin, ZhInverseNormalizer):
    pass


class StreamingEnInverseNormalizer(_StreamingPrefixMixin, EnInverseNormalizer):
    pass


class StreamingJaInverseNormalizer(_StreamingPrefixMixin, JaInverseNormalizer):
    pass


class StreamingZhNormalizer(_StreamingPrefixMixin, ZhNormalizer):
    pass


class StreamingEnNormalizer(_StreamingPrefixMixin, EnNormalizer):
    pass


class StreamingJaNormalizer(_StreamingPrefixMixin, JaNormalizer):
    pass


def write_graph(graph, path):
    path = FST_DIR / path
    path.parent.mkdir(parents=True, exist_ok=True)
    graph.optimize().write(str(path))


def write_prefix_graph(graph, path):
    """Write the semantic prefix graph and its stream-search matcher.

    The matcher keeps only the input language and removes weights because
    streaming boundary detection needs reachability, not normalization output
    or rule ranking. Every state is final so the graph accepts prefixes of
    semantic rules that may be completed by future input.
    """

    write_graph(graph, path)
    matcher = pynini.arcmap(pynini.project(graph, "input"), map_type="rmweight")
    for state in matcher.states():
        matcher.set_final(state)
    matcher_path = Path(path).with_name(Path(path).name.replace("prefix", "prefix_matcher", 1))
    matcher_path = FST_DIR / matcher_path
    matcher.write(str(matcher_path))


def build_processors():
    configs = {
        "traditional_to_simple.fst": {"traditional_to_simple": True},
        "remove_interjections.fst": {"remove_interjections": True},
        "remove_puncts.fst": {"remove_puncts": True},
        "full_to_half.fst": {"full_to_half": True},
        "tag_oov.fst": {"tag_oov": True},
    }
    disabled = {
        "traditional_to_simple": False,
        "remove_interjections": False,
        "remove_puncts": False,
        "full_to_half": False,
        "tag_oov": False,
    }
    for filename, enabled in configs.items():
        options = disabled.copy()
        options.update(enabled)
        write_graph(PostProcessor(**options).processor, filename)
    # Export fused single-character rewrites, rather than multiplying several
    # whole-string FSTs at runtime. Option order matches upstream PostProcessor.
    names = ("traditional_to_simple", "remove_interjections", "remove_puncts", "full_to_half", "tag_oov")
    for flags in product((False, True), repeat=len(names)):
        if not any(flags):
            continue
        key = "".join("1" if flag else "0" for flag in flags)
        write_graph(PostProcessor(**dict(zip(names, flags))).processor, f"processors/{key}.fst")


def build_zh_tn():
    options = {
        "cache_dir": False,
        "traditional_to_simple": False,
        "remove_interjections": False,
        "remove_puncts": False,
        "full_to_half": False,
        "tag_oov": False,
    }
    normalizer = StreamingZhNormalizer(remove_erhua=False, **options)
    write_graph(normalizer.tagger, "zh/tn/tagger.fst")
    write_graph(normalizer.verbalizer, "zh/tn/verbalizer.fst")
    write_prefix_graph(normalizer.stream_prefix_tagger, "zh/tn/prefix.fst")

    remove_erhua = ZhNormalizer(remove_erhua=True, **options)
    write_graph(remove_erhua.verbalizer, "zh/tn/verbalizer_remove_erhua.fst")


def build_zh_itn():
    options = {
        "cache_dir": False,
        "remove_interjections": False,
        "enable_standalone_number": True,
        "enable_million": False,
    }
    normalizer = StreamingZhInverseNormalizer(enable_0_to_9=False, **options)
    write_graph(normalizer.tagger, "zh/itn/tagger.fst")
    write_graph(normalizer.verbalizer, "zh/itn/verbalizer.fst")
    write_prefix_graph(normalizer.stream_prefix_tagger, "zh/itn/prefix.fst")

    enable_0_to_9 = StreamingZhInverseNormalizer(enable_0_to_9=True, **options)
    write_graph(enable_0_to_9.tagger, "zh/itn/tagger_enable_0_to_9.fst")
    write_graph(enable_0_to_9.verbalizer, "zh/itn/verbalizer_enable_0_to_9.fst")
    write_prefix_graph(enable_0_to_9.stream_prefix_tagger, "zh/itn/prefix_enable_0_to_9.fst")


def build_en():
    normalizer = StreamingEnNormalizer(cache_dir=False)
    write_graph(normalizer.tagger, "en/tn/tagger.fst")
    write_graph(normalizer.verbalizer, "en/tn/verbalizer.fst")
    write_prefix_graph(normalizer.stream_prefix_tagger, "en/tn/prefix.fst")

    inverse_normalizer = StreamingEnInverseNormalizer(cache_dir=False)
    write_graph(inverse_normalizer.tagger, "en/itn/tagger.fst")
    write_graph(inverse_normalizer.verbalizer, "en/itn/verbalizer.fst")
    write_prefix_graph(inverse_normalizer.stream_prefix_tagger, "en/itn/prefix.fst")


def build_ja_tn():
    normalizer = StreamingJaNormalizer(
        cache_dir=False,
        transliterate=False,
        remove_interjections=False,
        remove_puncts=False,
        full_to_half=False,
        tag_oov=False,
    )
    write_graph(normalizer.tagger, "ja/tn/tagger.fst")
    write_graph(normalizer.verbalizer, "ja/tn/verbalizer.fst")
    write_prefix_graph(normalizer.stream_prefix_tagger, "ja/tn/prefix.fst")


def build_ja_itn():
    options = {
        "cache_dir": False,
        "full_to_half": False,
        "enable_standalone_number": True,
        "enable_million": False,
    }
    normalizer = StreamingJaInverseNormalizer(enable_0_to_9=False, **options)
    write_graph(normalizer.tagger, "ja/itn/tagger.fst")
    write_graph(normalizer.verbalizer, "ja/itn/verbalizer.fst")
    write_prefix_graph(normalizer.stream_prefix_tagger, "ja/itn/prefix.fst")

    enable_0_to_9 = StreamingJaInverseNormalizer(enable_0_to_9=True, **options)
    write_graph(enable_0_to_9.tagger, "ja/itn/tagger_enable_0_to_9.fst")
    write_graph(enable_0_to_9.verbalizer, "ja/itn/verbalizer_enable_0_to_9.fst")
    write_prefix_graph(enable_0_to_9.stream_prefix_tagger, "ja/itn/prefix_enable_0_to_9.fst")


def build_ko():
    # Without a proven lexical boundary Korean streaming conservatively buffers
    # until flush(), using the existing optional-prefix fallback.
    for operator, cls in (("tn", KoNormalizer), ("itn", KoInverseNormalizer)):
        normalizer = cls(cache_dir=False)
        write_graph(normalizer.tagger, "ko/{}/tagger.fst".format(operator))
        write_graph(normalizer.verbalizer, "ko/{}/verbalizer.fst".format(operator))


def build_de():
    for deterministic in (True, False):
        normalizer = DeNormalizer(cache_dir=False, deterministic=deterministic)
        suffix = "" if deterministic else "_nondeterministic"
        write_graph(normalizer.tagger, f"de/tn/tagger{suffix}.fst")
        write_graph(normalizer.verbalizer, f"de/tn/verbalizer{suffix}.fst")
    inverse = DeInverseNormalizer(cache_dir=False)
    write_graph(inverse.tagger, "de/itn/tagger.fst")
    write_graph(inverse.verbalizer, "de/itn/verbalizer.fst")


def build_registered(lang):
    pipeline = LANGUAGES[lang]
    for operator in ("tn", "itn"):
        filename = "normalizer" if operator == "tn" else "inverse_normalizer"
        cls_name = "Normalizer" if operator == "tn" else "InverseNormalizer"
        cls = getattr(import_module(f"{operator}.{pipeline['module']}.{filename}"), cls_name)
        modes = [({}, "")]
        if operator == "tn" and pipeline["tn_deterministic"]:
            modes += [({"deterministic": False}, "_nondeterministic")]
        if operator == "itn" and pipeline["itn_cased"]:
            modes += [({"cased": True}, "_cased")]
        for options, suffix in modes:
            normalizer = cls(cache_dir=False, **options)
            write_graph(normalizer.tagger, f"{lang}/{operator}/tagger{suffix}.fst")
            write_graph(normalizer.verbalizer, f"{lang}/{operator}/verbalizer{suffix}.fst")
            schema = FST_DIR / lang / operator / "token_orders.json"
            schema.write_text(
                json.dumps(normalizer.token_orders, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
            )


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--lang", choices=("all", *LANGUAGES, "processors"), default="all")
    args = parser.parse_args()
    builders = {
        "zh": (build_zh_tn, build_zh_itn),
        "en": (build_en,),
        "ja": (build_ja_tn, build_ja_itn),
        "ko": (build_ko,),
        "de": (build_de,),
    }
    if args.lang == "processors":
        build_processors()
        return
    if args.lang == "all":
        build_processors()
    for lang in LANGUAGES if args.lang == "all" else (args.lang,):
        if lang in builders:
            for build in builders[lang]:
                build()
        else:
            build_registered(lang)


if __name__ == "__main__":
    main()
