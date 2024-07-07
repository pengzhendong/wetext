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
@click.option("--lang", "-l", default="zh", type=click.Choice(["zh", "en"]))
@click.option("--operator", "-o", default="tn", type=click.Choice(["tn", "itn"]))
@click.option("--remove-erhua/--no-remove-erhua", default=False)
@click.option("--enable-0-to-9/--disable-0-to-9", default=True)
def main(text, lang, operator, remove_erhua, enable_0_to_9):
    normalizer = Normalizer(
        lang=lang,
        operator=operator,
        remove_erhua=remove_erhua,  # only works for zh-tn
        enable_0_to_9=enable_0_to_9,  # only works for zh-itn
    )
    text = normalizer.normalize(text)
    print(text)


if __name__ == "__main__":
    main()
