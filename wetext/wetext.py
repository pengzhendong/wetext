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

from kaldifst import TextNormalizer as normalizer
from modelscope import snapshot_download

from .token_parser import TokenParser


class Normalizer:
    def __init__(
        self,
        tagger_path=None,
        verbalizer_path=None,
        lang="zh",
        operator="tn",
        remove_erhua=False,
        enable_0_to_9=False,
    ):
        if tagger_path is None or verbalizer_path is None:
            repo_dir = snapshot_download("pengzhendong/wetext")
            assert lang in ["zh", "en"] and operator in ["tn", "itn"]
            tagger_path = f"{repo_dir}/{lang}/{operator}/tagger.fst"
            if lang == "zh" and operator == "itn" and enable_0_to_9:
                tagger_path = f"{repo_dir}/zh/itn/tagger_enable_0_to_9.fst"

            verbalizer_path = f"{repo_dir}/{lang}/{operator}/verbalizer.fst"
            if lang == "zh" and operator == "tn" and remove_erhua:
                verbalizer_path = f"{repo_dir}/zh/tn/verbalizer_remove_erhua.fst"

        self.operator = operator
        self.tagger = normalizer(tagger_path)
        self.verbalizer = normalizer(verbalizer_path)

    def tag(self, text):
        return self.tagger(text)

    def verbalize(self, text):
        text = TokenParser(self.operator).reorder(text)
        return self.verbalizer(text)

    def normalize(self, text):
        return self.verbalize(self.tag(text))
