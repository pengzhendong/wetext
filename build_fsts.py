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

import os

from pynini.lib import byte
from pynini.lib.pynutil import add_weight, delete, insert


def build_zh_processors():
    from tn.chinese.rules.postprocessor import PostProcessor
    from tn.chinese.rules.preprocessor import PreProcessor

    os.makedirs("wetext/fsts", exist_ok=True)

    preprocessor = PreProcessor().processor
    preprocessor.optimize().star.optimize().write("wetext/fsts/traditional_to_simple.fst")

    postprocessor = PostProcessor(
        remove_interjections=True,
        remove_puncts=False,
        full_to_half=False,
        tag_oov=False,
    ).processor
    postprocessor.optimize().star.optimize().write("wetext/fsts/remove_interjections.fst")
    postprocessor = PostProcessor(
        remove_interjections=False,
        remove_puncts=True,
        full_to_half=False,
        tag_oov=False,
    ).processor
    postprocessor.optimize().star.optimize().write("wetext/fsts/remove_puncts.fst")
    postprocessor = PostProcessor(
        remove_interjections=False,
        remove_puncts=False,
        full_to_half=True,
        tag_oov=False,
    ).processor
    postprocessor.optimize().star.optimize().write("wetext/fsts/full_to_half.fst")
    postprocessor = PostProcessor(
        remove_interjections=False,
        remove_puncts=False,
        full_to_half=False,
        tag_oov=True,
    ).processor
    postprocessor.optimize().star.optimize().write("wetext/fsts/tag_oov.fst")


def build_zh_tn():
    from tn.chinese.rules.cardinal import Cardinal
    from tn.chinese.rules.char import Char
    from tn.chinese.rules.date import Date
    from tn.chinese.rules.fraction import Fraction
    from tn.chinese.rules.math import Math
    from tn.chinese.rules.measure import Measure
    from tn.chinese.rules.money import Money
    from tn.chinese.rules.sport import Sport
    from tn.chinese.rules.time import Time
    from tn.chinese.rules.whitelist import Whitelist

    os.makedirs("wetext/fsts/zh/tn", exist_ok=True)

    date = add_weight(Date().tagger, 1.02)
    whitelist = add_weight(Whitelist().tagger, 1.03)
    sport = add_weight(Sport().tagger, 1.04)
    fraction = add_weight(Fraction().tagger, 1.05)
    measure = add_weight(Measure().tagger, 1.05)
    money = add_weight(Money().tagger, 1.05)
    time = add_weight(Time().tagger, 1.05)
    cardinal = add_weight(Cardinal().tagger, 1.06)
    math = add_weight(Math().tagger, 90)
    char = add_weight(Char().tagger, 100)
    tagger = date | whitelist | sport | fraction | measure | money | time | cardinal | math | char
    tagger.optimize().star.optimize().write("wetext/fsts/zh/tn/tagger.fst")

    cardinal = Cardinal().verbalizer
    char = Char().verbalizer
    date = Date().verbalizer
    fraction = Fraction().verbalizer
    math = Math().verbalizer
    measure = Measure().verbalizer
    money = Money().verbalizer
    sport = Sport().verbalizer
    time = Time().verbalizer
    verbalizer = cardinal | char | date | fraction | math | measure | money | sport | time
    whitelist = Whitelist(remove_erhua=False).verbalizer
    (verbalizer | whitelist).optimize().star.optimize().write("wetext/fsts/zh/tn/verbalizer.fst")
    whitelist = Whitelist(remove_erhua=True).verbalizer
    (verbalizer | whitelist).optimize().star.optimize().write("wetext/fsts/zh/tn/verbalizer_remove_erhua.fst")


def build_zh_itn():
    from itn.chinese.rules.cardinal import Cardinal
    from itn.chinese.rules.char import Char
    from itn.chinese.rules.date import Date
    from itn.chinese.rules.fraction import Fraction
    from itn.chinese.rules.license_plate import LicensePlate
    from itn.chinese.rules.math import Math
    from itn.chinese.rules.measure import Measure
    from itn.chinese.rules.money import Money
    from itn.chinese.rules.time import Time
    from itn.chinese.rules.whitelist import Whitelist

    os.makedirs("wetext/fsts/zh/itn", exist_ok=True)

    for enable_0_to_9 in [True, False]:
        date = add_weight(Date().tagger, 1.02)
        whitelist = add_weight(Whitelist().tagger, 1.01)
        fraction = add_weight(Fraction().tagger, 1.05)
        time = add_weight(Time().tagger, 1.05)
        math = add_weight(Math().tagger, 1.10)
        char = add_weight(Char().tagger, 100)
        measure = add_weight(Measure(enable_0_to_9=enable_0_to_9).tagger, 1.05)
        money = add_weight(Money(enable_0_to_9=enable_0_to_9).tagger, 1.04)
        cardinal = add_weight(Cardinal(True, enable_0_to_9, False).tagger, 1.06)
        tagger = date | whitelist | fraction | measure | money | time | cardinal | math | char
        tagger.optimize().star.optimize().write(
            "wetext/fsts/zh/itn/tagger_enable_0_to_9.fst" if enable_0_to_9 else "wetext/fsts/zh/itn/tagger.fst"
        )

    cardinal = Cardinal().verbalizer
    char = Char().verbalizer
    date = Date().verbalizer
    fraction = Fraction().verbalizer
    math = Math().verbalizer
    measure = Measure().verbalizer
    money = Money().verbalizer
    time = Time().verbalizer
    license_plate = LicensePlate().verbalizer
    whitelist = Whitelist().verbalizer
    verbalizer = cardinal | char | date | fraction | math | measure | money | time | license_plate | whitelist
    verbalizer.optimize().star.optimize().write("wetext/fsts/zh/itn/verbalizer.fst")


def build_en_tn():
    from tn.english.rules.cardinal import Cardinal
    from tn.english.rules.date import Date
    from tn.english.rules.decimal import Decimal
    from tn.english.rules.electronic import Electronic
    from tn.english.rules.fraction import Fraction
    from tn.english.rules.measure import Measure
    from tn.english.rules.money import Money
    from tn.english.rules.ordinal import Ordinal
    from tn.english.rules.punctuation import Punctuation
    from tn.english.rules.range import Range
    from tn.english.rules.telephone import Telephone
    from tn.english.rules.time import Time
    from tn.english.rules.whitelist import WhiteList
    from tn.english.rules.word import Word

    os.makedirs("wetext/fsts/en/tn", exist_ok=True)

    cardinal = add_weight(Cardinal().tagger, 1.0)
    ordinal = add_weight(Ordinal().tagger, 1.0)
    decimal = add_weight(Decimal().tagger, 1.0)
    fraction = add_weight(Fraction().tagger, 1.0)
    date = add_weight(Date().tagger, 0.99)
    time = add_weight(Time().tagger, 1.00)
    measure = add_weight(Measure().tagger, 1.00)
    money = add_weight(Money().tagger, 1.00)
    telephone = add_weight(Telephone().tagger, 1.00)
    electronic = add_weight(Electronic().tagger, 1.00)
    word = add_weight(Word().tagger, 100)
    whitelist = add_weight(WhiteList().tagger, 1.00)
    punct = add_weight(Punctuation().tagger, 2.00)
    rang = add_weight(Range().tagger, 1.01)
    tagger = (
        cardinal
        | ordinal
        | word
        | date
        | decimal
        | fraction
        | time
        | measure
        | money
        | telephone
        | electronic
        | whitelist
        | rang
        | punct
    ) + delete(byte.SPACE | "\u00a0").star
    tagger.optimize().star.optimize().write("wetext/fsts/en/tn/tagger.fst")

    cardinal = Cardinal().verbalizer
    ordinal = Ordinal().verbalizer
    decimal = Decimal().verbalizer
    fraction = Fraction().verbalizer
    word = Word().verbalizer
    date = Date().verbalizer
    time = Time().verbalizer
    measure = Measure().verbalizer
    money = Money().verbalizer
    telephone = Telephone().verbalizer
    electronic = Electronic().verbalizer
    whitelist = WhiteList().verbalizer
    punct = Punctuation().verbalizer
    rang = Range().verbalizer
    verbalizer = (
        cardinal
        | ordinal
        | word
        | date
        | decimal
        | fraction
        | time
        | measure
        | money
        | telephone
        | electronic
        | whitelist
        | punct
        | rang
    ) + insert(" ")
    verbalizer.optimize().star.optimize().write("wetext/fsts/en/tn/verbalizer.fst")


def build_ja_tn():
    from tn.japanese.rules.cardinal import Cardinal
    from tn.japanese.rules.char import Char
    from tn.japanese.rules.date import Date
    from tn.japanese.rules.fraction import Fraction
    from tn.japanese.rules.math import Math
    from tn.japanese.rules.measure import Measure
    from tn.japanese.rules.money import Money
    from tn.japanese.rules.sport import Sport
    from tn.japanese.rules.time import Time

    # from tn.japanese.rules.transliteration import Transliteration
    from tn.japanese.rules.whitelist import Whitelist

    os.makedirs("wetext/fsts/ja/tn", exist_ok=True)

    cardinal = add_weight(Cardinal().tagger, 1.06)
    char = add_weight(Char().tagger, 100)
    date = add_weight(Date().tagger, 1.02)
    fraction = add_weight(Fraction().tagger, 1.05)
    math = add_weight(Math().tagger, 90)
    measure = add_weight(Measure().tagger, 1.05)
    money = add_weight(Money().tagger, 1.05)
    sport = add_weight(Sport().tagger, 1.06)
    time = add_weight(Time().tagger, 1.05)
    whitelist = add_weight(Whitelist().tagger, 1.03)
    tagger = cardinal | char | date | fraction | math | measure | money | sport | time | whitelist
    # if self.transliterate:
    #     transliteration = add_weight(Transliteration().tagger, 1.04)
    #     tagger = (tagger | transliteration)
    tagger.optimize().star.optimize().write("wetext/fsts/ja/tn/tagger.fst")

    cardinal = Cardinal().verbalizer
    char = Char().verbalizer
    date = Date().verbalizer
    fraction = Fraction().verbalizer
    math = Math().verbalizer
    measure = Measure().verbalizer
    money = Money().verbalizer
    sport = Sport().verbalizer
    time = Time().verbalizer
    whitelist = Whitelist().verbalizer
    verbalizer = cardinal | char | date | fraction | math | measure | money | sport | time | whitelist
    # if self.transliterate:
    #     transliteration = Transliteration().verbalizer
    #     verbalizer = (verbalizer | transliteration)
    verbalizer.optimize().star.optimize().write("wetext/fsts/ja/tn/verbalizer.fst")


def build_ja_itn():
    from itn.japanese.rules.cardinal import Cardinal
    from itn.japanese.rules.char import Char
    from itn.japanese.rules.date import Date
    from itn.japanese.rules.fraction import Fraction
    from itn.japanese.rules.math import Math
    from itn.japanese.rules.measure import Measure
    from itn.japanese.rules.money import Money
    from itn.japanese.rules.ordinal import Ordinal
    from itn.japanese.rules.time import Time
    from itn.japanese.rules.whitelist import Whitelist

    os.makedirs("wetext/fsts/ja/itn", exist_ok=True)

    for enable_0_to_9 in [True, False]:
        cardinal = add_weight(Cardinal(True, enable_0_to_9, False).tagger, 1.06)
        measure = add_weight(Measure(enable_0_to_9).tagger, 1.05)
        money = add_weight(Money(enable_0_to_9).tagger, 1.04)
        char = add_weight(Char().tagger, 100)
        date = add_weight(Date().tagger, 1.02)
        fraction = add_weight(Fraction().tagger, 1.05)
        math = add_weight(Math().tagger, 90)
        ordinal = add_weight(Ordinal().tagger, 1.04)
        time = add_weight(Time().tagger, 1.04)
        whitelist = add_weight(Whitelist().tagger, 1.01)

        tagger = cardinal | char | date | fraction | math | measure | money | ordinal | time | whitelist
        tagger.optimize().star.optimize().write(
            "wetext/fsts/ja/itn/tagger_enable_0_to_9.fst" if enable_0_to_9 else "wetext/fsts/ja/itn/tagger.fst"
        )

    cardinal = Cardinal().verbalizer
    char = Char().verbalizer
    date = Date().verbalizer
    fraction = Fraction().verbalizer
    math = Math().verbalizer
    measure = Measure().verbalizer
    money = Money().verbalizer
    ordinal = Ordinal().verbalizer
    time = Time().verbalizer
    whitelist = Whitelist().verbalizer

    verbalizer = cardinal | char | date | fraction | math | measure | money | ordinal | time | whitelist
    verbalizer.optimize().star.optimize().write("wetext/fsts/ja/itn/verbalizer.fst")


def main():
    build_zh_processors()
    build_zh_tn()
    build_zh_itn()
    build_en_tn()
    build_ja_tn()
    build_ja_itn()


if __name__ == "__main__":
    main()
