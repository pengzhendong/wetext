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

from pathlib import Path

from itn.chinese.inverse_normalizer import InverseNormalizer as ZhInverseNormalizer
from itn.english.inverse_normalizer import InverseNormalizer as EnInverseNormalizer
from itn.japanese.inverse_normalizer import InverseNormalizer as JaInverseNormalizer
from tn.chinese.normalizer import Normalizer as ZhNormalizer
from tn.chinese.rules.postprocessor import PostProcessor
from tn.english.normalizer import Normalizer as EnNormalizer
from tn.japanese.normalizer import Normalizer as JaNormalizer

FST_DIR = Path("wetext/fsts")


class _StreamingPrefixMixin:
    """Capture the semantic classifier graph used by streaming ITN.

    The normal tagger contains catch-all character/word rules, so every input
    is accepted and it cannot tell the runtime whether a trailing fragment may
    grow into a normalization rule.  The prefix graph excludes those fallback
    rules while keeping its inventory in sync with the official normalizer.
    """

    _stream_fallback_rules = frozenset(("char", "punctuation", "word"))

    def tagger_union(self, rule_specs):
        rule_specs = tuple(rule_specs)
        semantic_rules = tuple(
            spec for spec in rule_specs if spec.rule.name not in self._stream_fallback_rules
        )
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


def write_graph(graph, path):
    path = FST_DIR / path
    path.parent.mkdir(parents=True, exist_ok=True)
    graph.optimize().write(str(path))


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
        write_graph(PostProcessor(**options).processor.star, filename)


def build_zh_tn():
    options = {
        "cache_dir": False,
        "traditional_to_simple": False,
        "remove_interjections": False,
        "remove_puncts": False,
        "full_to_half": False,
        "tag_oov": False,
    }
    normalizer = ZhNormalizer(remove_erhua=False, **options)
    write_graph(normalizer.tagger, "zh/tn/tagger.fst")
    write_graph(normalizer.verbalizer, "zh/tn/verbalizer.fst")

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
    write_graph(normalizer.stream_prefix_tagger, "zh/itn/prefix.fst")

    enable_0_to_9 = StreamingZhInverseNormalizer(enable_0_to_9=True, **options)
    write_graph(enable_0_to_9.tagger, "zh/itn/tagger_enable_0_to_9.fst")
    write_graph(enable_0_to_9.stream_prefix_tagger, "zh/itn/prefix_enable_0_to_9.fst")


def build_en():
    normalizer = EnNormalizer(cache_dir=False)
    write_graph(normalizer.tagger, "en/tn/tagger.fst")
    write_graph(normalizer.verbalizer, "en/tn/verbalizer.fst")

    inverse_normalizer = StreamingEnInverseNormalizer(cache_dir=False)
    write_graph(inverse_normalizer.tagger, "en/itn/tagger.fst")
    write_graph(inverse_normalizer.verbalizer, "en/itn/verbalizer.fst")
    write_graph(inverse_normalizer.stream_prefix_tagger, "en/itn/prefix.fst")


def build_ja_tn():
    normalizer = JaNormalizer(
        cache_dir=False,
        transliterate=False,
        remove_interjections=False,
        remove_puncts=False,
        full_to_half=False,
        tag_oov=False,
    )
    write_graph(normalizer.tagger, "ja/tn/tagger.fst")
    write_graph(normalizer.verbalizer, "ja/tn/verbalizer.fst")


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
    write_graph(normalizer.stream_prefix_tagger, "ja/itn/prefix.fst")

    enable_0_to_9 = StreamingJaInverseNormalizer(enable_0_to_9=True, **options)
    write_graph(enable_0_to_9.tagger, "ja/itn/tagger_enable_0_to_9.fst")
    write_graph(enable_0_to_9.stream_prefix_tagger, "ja/itn/prefix_enable_0_to_9.fst")


def main():
    build_processors()
    build_zh_tn()
    build_zh_itn()
    build_en()
    build_ja_tn()
    build_ja_itn()


if __name__ == "__main__":
    main()
