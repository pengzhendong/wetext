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

from dataclasses import asdict, replace

from wetext.config import NormalizerConfig
from wetext.utils import normalize, normalize_candidates, normalize_with_mapping


class Normalizer:
    def __init__(self, **kwargs):
        self.config = NormalizerConfig(**kwargs)

    def normalize(self, text: str, nbest: int = 1, **kwargs):
        """
        Normalize the text.

        Args:
            text: The text to normalize.
            **kwargs: The keyword arguments to override the config.
        """
        config = replace(self.config, **kwargs)
        return normalize(text, nbest=nbest, **asdict(config))

    def normalize_with_mapping(self, text: str, nbest: int = 1, include_identity: bool = False, **kwargs):
        config = replace(self.config, **kwargs)
        return normalize_with_mapping(
            text,
            nbest=nbest,
            include_identity=include_identity,
            **asdict(config),
        )

    def normalize_candidates(self, text: str, nbest: int = 1, **kwargs):
        config = replace(self.config, **kwargs)
        return normalize_candidates(text, nbest=nbest, **asdict(config))
