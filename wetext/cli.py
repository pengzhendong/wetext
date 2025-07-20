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

import click

from wetext import Normalizer


@click.command()
@click.argument("text")
@click.option("--lang", "-l", default="auto", type=click.Choice(["auto", "en", "zh"]))
@click.option("--operator", "-o", default="tn", type=click.Choice(["tn", "itn"]))
@click.option("--traditional-to-simple", is_flag=True, help="Convert traditional Chinese to simplified Chinese.")
@click.option("--full-to-half", is_flag=True, help="Convert full-width characters to half-width characters.")
@click.option("--remove-interjections", is_flag=True, help="Remove interjections.")
@click.option("--remove-puncts", is_flag=True, help="Remove punctuation.")
@click.option("--tag-oov", is_flag=True, help="Tag out-of-vocabulary words.")
@click.option("--enable-0-to-9", is_flag=True, help="Enable 0-to-9 conversion.")
@click.option("--remove-erhua", is_flag=True, help="Remove erhua.")
def main(
    text,
    lang,
    operator,
    traditional_to_simple,
    full_to_half,
    remove_interjections,
    remove_puncts,
    tag_oov,
    enable_0_to_9,
    remove_erhua,
):
    normalizer = Normalizer(
        lang,
        operator,
        traditional_to_simple,
        full_to_half,
        remove_interjections,
        remove_puncts,
        tag_oov,
        enable_0_to_9,
        remove_erhua,
    )
    text = normalizer.normalize(text)
    print(text)


if __name__ == "__main__":
    main()
