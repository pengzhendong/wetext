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
from wetext.utils import normalize


class Normalizer:
    def __init__(self, **kwargs):
        self.config = NormalizerConfig(**kwargs)

    def normalize(self, text: str, **kwargs) -> str:
        """
        Normalize the text.

        Args:
            text: The text to normalize.
            **kwargs: The keyword arguments to override the config.
        """
        config = replace(self.config, **kwargs)
        return normalize(text, **asdict(config))
