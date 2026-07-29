# Copyright (c) 2022 Zhendong Peng (pzd17@tsinghua.org.cn)
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

import string

from wetext.constants import EN_ITN_ORDERS, EN_TN_ORDERS, EOS, ITN_ORDERS, TN_ORDERS


def escape_value(value):
    return value.replace("\\", "\\\\").replace('"', '\\"')


class Token:
    def __init__(self, name, start=None):
        self.name = name
        self.start = start
        self.end = None
        self.order = []
        self.members = {}

    def append(self, key, value):
        self.order.append(key)
        self.members[key] = value

    def string(self, orders):
        output = self.name + " {"
        order = self.order
        if self.name in orders.keys():
            if "preserve_order" not in self.members.keys() or self.members["preserve_order"] != "true":
                canonical_order = orders[self.name]
                order = canonical_order + [key for key in self.order if key not in canonical_order]

        for key in order:
            if key not in self.members.keys():
                continue
            output += ' {}: "{}"'.format(key, escape_value(self.members[key]))
        return output + " }"


class TokenParser:
    def __init__(self, lang, operator="tn"):
        assert lang in ("en", "zh", "ja")
        if lang == "en":
            if operator == "tn":
                self.orders = EN_TN_ORDERS
            elif operator == "itn":
                self.orders = EN_ITN_ORDERS
            else:
                raise NotImplementedError()
        else:
            if operator == "tn":
                self.orders = TN_ORDERS
            elif operator == "itn":
                self.orders = ITN_ORDERS

    def load(self, input):
        assert len(input) > 0
        self.index = 0
        self.text = input
        self.char = input[0]
        self.tokens = []

    def read(self):
        if self.index < len(self.text) - 1:
            self.index += 1
            self.char = self.text[self.index]
            return True
        self.char = EOS
        return False

    def parse_ws(self):
        not_eos = self.char != EOS
        while not_eos and self.char == " ":
            not_eos = self.read()
        return not_eos

    def parse_char(self, exp):
        if self.char == exp:
            self.read()
            return True
        return False

    def parse_chars(self, exp):
        ok = False
        for x in exp:
            ok |= self.parse_char(x)
        return ok

    def parse_key(self):
        assert self.char != EOS
        assert self.char not in string.whitespace

        key = ""
        while self.char in string.ascii_letters + "_":
            key += self.char
            self.read()
        return key

    def parse_value(self):
        assert self.char != EOS
        escape = False

        value = ""
        while self.char != '"':
            value += self.char
            escape = self.char == "\\"
            self.read()
            if escape:
                escape = False
                value += self.char
                self.read()
        return value

    def parse(self, input):
        self.load(input)
        while self.parse_ws():
            token_start = self.index
            name = self.parse_key()
            self.parse_chars(" { ")

            token = Token(name, token_start)
            while self.parse_ws():
                if self.char == "}":
                    self.parse_char("}")
                    break
                key = self.parse_key()
                self.parse_chars(': "')
                value = self.parse_value()
                self.parse_char('"')
                token.append(key, value)
            token.end = len(self.text) if self.char == EOS else self.index
            self.tokens.append(token)

    def reorder(self, input):
        output, _ = self.reorder_with_spans(input)
        return output

    def reorder_with_spans(self, input):
        self.parse(input)
        serialized = []
        spans = []
        offset = 0
        for token in self.tokens:
            value = token.string(self.orders)
            if serialized:
                offset += 1
            start = offset
            offset += len(value)
            spans.append((start, offset))
            serialized.append(value)
        return " ".join(serialized), tuple(spans)
