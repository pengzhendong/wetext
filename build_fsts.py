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
        measure = add_weight(Measure(enable_0_to_9=True).tagger, 1.05)
        money = add_weight(Money(enable_0_to_9=True).tagger, 1.04)
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
    from tn.english.rules.serial import Serial
    from tn.english.rules.telephone import Telephone
    from tn.english.rules.time import Time
    from tn.english.rules.whitelist import WhiteList
    from tn.english.rules.word import Word
    from tn.processor import Processor

    os.makedirs("wetext/fsts/en/tn", exist_ok=True)

    p = Processor("_")

    cardinal = Cardinal()
    ordinal = Ordinal(cardinal=cardinal)
    decimal = Decimal(cardinal=cardinal)
    fraction = Fraction(cardinal=cardinal, ordinal=ordinal)
    punctuation = Punctuation()
    date = Date(cardinal=cardinal, ordinal=ordinal)
    time = Time(cardinal=cardinal)
    measure = Measure(cardinal=cardinal, decimal=decimal, fraction=fraction, ordinal=ordinal)
    money = Money(cardinal=cardinal, decimal=decimal)
    telephone = Telephone()
    electronic = Electronic(cardinal=cardinal)
    serial = Serial(cardinal=cardinal, ordinal=ordinal)
    word = Word(punctuation=punctuation)
    whitelist = WhiteList()
    rang = Range(date=date, time=time)

    tagger = (
        add_weight(cardinal.tagger, 1.0)
        | add_weight(ordinal.tagger, 1.0)
        | add_weight(word.tagger, 100)
        | add_weight(date.tagger, 0.99)
        | add_weight(decimal.tagger, 1.0)
        | add_weight(fraction.tagger, 1.0)
        | add_weight(time.tagger, 1.00)
        | add_weight(measure.tagger, 1.00)
        | add_weight(money.tagger, 1.00)
        | add_weight(telephone.tagger, 1.00)
        | add_weight(electronic.tagger, 1.00)
        | add_weight(serial.tagger, 1.01)
        | add_weight(whitelist.tagger, 1.00)
        | add_weight(rang.tagger, 1.01)
        | add_weight(punctuation.tagger, 2.00)
    ).optimize() + (add_weight(punctuation.tagger, 2.00).plus | p.DELETE_SPACE)
    tagger = (delete(" ").star + tagger.star) @ p.build_rule(delete(" "), r="[EOS]")
    tagger.optimize().write("wetext/fsts/en/tn/tagger.fst")

    verbalizer = (
        cardinal.verbalizer
        | ordinal.verbalizer
        | word.verbalizer
        | date.verbalizer
        | decimal.verbalizer
        | fraction.verbalizer
        | time.verbalizer
        | measure.verbalizer
        | money.verbalizer
        | telephone.verbalizer
        | electronic.verbalizer
        | serial.verbalizer
        | whitelist.verbalizer
        | punctuation.verbalizer
        | rang.verbalizer
    ).optimize() + (punctuation.verbalizer.plus | p.INSERT_SPACE)
    verbalizer = verbalizer.star @ p.build_rule(delete(" "), r="[EOS]")
    verbalizer.optimize().write("wetext/fsts/en/tn/verbalizer.fst")


def build_en_itn():
    from itn.english.rules.cardinal import Cardinal
    from itn.english.rules.char import Char
    from itn.english.rules.date import Date
    from itn.english.rules.decimal import Decimal
    from itn.english.rules.electronic import Electronic
    from itn.english.rules.measure import Measure
    from itn.english.rules.money import Money
    from itn.english.rules.ordinal import Ordinal
    from itn.english.rules.punctuation import Punctuation
    from itn.english.rules.telephone import Telephone
    from itn.english.rules.time import Time
    from itn.english.rules.whitelist import Whitelist
    from itn.english.rules.word import Word
    from pynini import closure

    os.makedirs("wetext/fsts/en/itn", exist_ok=True)

    cardinal = Cardinal()
    ordinal = Ordinal(cardinal=cardinal)
    decimal = Decimal(cardinal=cardinal)
    date = Date(cardinal=cardinal, ordinal=ordinal)
    time = Time(cardinal=cardinal)
    measure = Measure(cardinal=cardinal, decimal=decimal)
    money = Money(cardinal=cardinal, decimal=decimal)
    telephone = Telephone(cardinal=cardinal)
    electronic = Electronic()
    whitelist = Whitelist()
    word = Word()
    char = Char()
    punctuation = Punctuation()

    DELETE_EXTRA_SPACE = delete(byte.SPACE.plus | " ")
    classify = (
        add_weight(date.tagger, 1.09)
        | add_weight(time.tagger, 1.1)
        | add_weight(measure.tagger, 1.1)
        | add_weight(money.tagger, 1.08)
        | add_weight(whitelist.tagger, 1.01)
        | add_weight(telephone.tagger, 1.1)
        | add_weight(electronic.tagger, 1.1)
        | add_weight(ordinal.tagger, 1.09)
        | add_weight(decimal.tagger, 1.1)
        | add_weight(cardinal.tagger, 1.1)
        | add_weight(word.tagger, 50)
        | add_weight(char.tagger, 100)
    ).optimize()

    punct = add_weight(punctuation.tagger, 1.1)
    token = closure(punct + delete(" ").ques) + classify + closure(delete(" ").ques + punct)
    graph = token + closure(DELETE_EXTRA_SPACE + token)
    tagger = delete(" ").star + graph + delete(" ").star
    tagger.optimize().write("wetext/fsts/en/itn/tagger.fst")

    verbalizer = (
        cardinal.verbalizer
        | ordinal.verbalizer
        | decimal.verbalizer
        | date.verbalizer
        | time.verbalizer
        | measure.verbalizer
        | money.verbalizer
        | telephone.verbalizer
        | electronic.verbalizer
        | whitelist.verbalizer
        | word.verbalizer
        | char.verbalizer
        | punctuation.verbalizer
    ).optimize()
    verbalizer = (verbalizer + insert(" ")).star
    verbalizer.optimize().write("wetext/fsts/en/itn/verbalizer.fst")


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
    build_en_itn()
    build_ja_tn()
    build_ja_itn()


if __name__ == "__main__":
    main()
