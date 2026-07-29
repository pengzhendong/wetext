"""Low-level kaldifst helpers for n-best search and exact path tracing."""

import math
import bisect
from dataclasses import dataclass

import kaldifst

from wetext.alignment import AlignmentError


def acceptor(text):
    data = text.encode("utf-8")
    lines = ["{} {} {}".format(index, index + 1, label) for index, label in enumerate(data)]
    lines.append(str(len(data)))
    return kaldifst.compile("\n".join(lines), acceptor=True)


def compose_input(text, graph):
    return kaldifst.compose(acceptor(text), graph)


def constrain_output(lattice, text):
    output = acceptor(text)
    kaldifst.arcsort(lattice, "olabel")
    return kaldifst.compose(lattice, output)


def project_output(lattice):
    lines = []
    for state in kaldifst.StateIterator(lattice):
        for arc in kaldifst.ArcIterator(lattice, state):
            lines.append(
                "{} {} {} {} {}".format(
                    state,
                    arc.nextstate,
                    arc.olabel,
                    arc.olabel,
                    arc.weight.value,
                )
            )
        final_weight = lattice.final(state).value
        if not math.isinf(final_weight):
            lines.append("{} {}".format(state, final_weight))
    if not lines:
        return kaldifst.StdVectorFst()
    projected = kaldifst.compile("\n".join(lines))
    kaldifst.rmepsilon(projected)
    return kaldifst.determinize(projected)


def linear_path(path):
    succeeded, input_labels, output_labels, weight = kaldifst.get_linear_symbol_sequence(path)
    if not succeeded:
        raise AlignmentError("shortest WFST path is not linear")
    return (
        bytes(input_labels).decode("utf-8"),
        bytes(output_labels).decode("utf-8"),
        weight.value,
    )


def shortest_unique_paths(lattice, n):
    projected = project_output(lattice)
    if projected.start == -1:
        return []
    # OpenFst/Pynini breaks equal-weight paths lexicographically, while
    # kaldifst's one-best tie depends on state order.  Overgenerate a bounded
    # frontier and apply the official ordering explicitly.
    requested = max(64, n * 4)
    paths = kaldifst.convert_nbest_to_vector(kaldifst.shortest_path(projected, requested))
    results = []
    for path in paths:
        _, output, weight = linear_path(path)
        results.append((output, weight))
    results.sort(key=lambda item: (item[1], item[0].encode("utf-8")))
    return results[:n]


@dataclass(frozen=True)
class WeightedOutput:
    text: str
    weight: float
    rank: int


class UniqueOutputPathStream:
    def __init__(self, lattice):
        self.lattice = lattice
        self.items = []
        self.yielded = set()
        self.next_rank = 0
        self.limit = 0
        self.exhausted = False

    def _expand(self):
        if self.exhausted:
            return
        limit = 1 if self.limit == 0 else self.limit * 2
        paths = shortest_unique_paths(self.lattice, limit)
        self.items = [WeightedOutput(text, weight, -1) for text, weight in paths if text not in self.yielded]
        self.limit = limit
        if len(paths) < limit:
            self.exhausted = True

    def peek(self):
        while not self.items and not self.exhausted:
            self._expand()
        if not self.items:
            return None
        item = self.items[0]
        return WeightedOutput(item.text, item.weight, self.next_rank)

    def pop(self):
        item = self.peek()
        if item is not None:
            self.yielded.add(item.text)
            self.items.pop(0)
            self.next_rank += 1
        return item


def _linear_arcs(path):
    state = path.start
    if state == -1:
        raise AlignmentError("no WFST path for the requested input")
    visited = set()
    while state not in visited:
        visited.add(state)
        arcs = list(kaldifst.ArcIterator(path, state))
        if not arcs:
            return
        if len(arcs) != 1:
            raise AlignmentError("shortest WFST path is not linear")
        arc = arcs[0]
        yield arc
        state = arc.nextstate
    raise AlignmentError("shortest WFST path contains a cycle")


def exact_path(input_text, graph, output_text=None):
    lattice = compose_input(input_text, graph)
    if output_text is not None:
        lattice = constrain_output(lattice, output_text)
    if lattice.start == -1:
        raise AlignmentError("no WFST path for the requested input")
    return kaldifst.shortest_path(lattice, 1)


def _text_boundaries(text):
    character_to_byte = [0]
    byte_to_character = {0: 0}
    byte_is_whitespace = []
    offset = 0
    for index, char in enumerate(text, 1):
        size = len(char.encode("utf-8"))
        byte_is_whitespace.extend([char.isspace()] * size)
        offset += size
        character_to_byte.append(offset)
        byte_to_character[offset] = index
    return tuple(character_to_byte), byte_to_character, tuple(byte_is_whitespace)


def _snap_byte_span(character_to_byte, start, end):
    """Expands byte offsets to whole UTF-8 code points.

    kaldifst composes UTF-8 byte arcs independently, so an insertion may be
    scheduled across adjacent epsilon arcs even though it represents one
    Unicode character.
    """

    snapped_start = character_to_byte[bisect.bisect_right(character_to_byte, start) - 1]
    snapped_end = character_to_byte[bisect.bisect_left(character_to_byte, end)]
    return snapped_start, snapped_end


def _byte_spans(text, character_to_byte, spans, reject_empty=False):
    previous_end = 0
    normalized = []
    for start, end in spans:
        if start < previous_end or end < start or end > len(text):
            raise AlignmentError("token spans must be ordered, non-overlapping character ranges")
        if reject_empty and start == end:
            raise ValueError("input spans must be non-empty character ranges")
        normalized.append((character_to_byte[start], character_to_byte[end]))
        previous_end = end
    return tuple(normalized)


def trace_input_spans(input_text, output_text, graph, output_spans):
    path = exact_path(input_text, graph, output_text)
    _, input_byte_to_character, input_whitespace = _text_boundaries(input_text)
    output_character_to_byte, _, _ = _text_boundaries(output_text)
    output_byte_spans = _byte_spans(output_text, output_character_to_byte, output_spans)
    starts = [None] * len(output_byte_spans)
    ends = [None] * len(output_byte_spans)
    input_offset = output_offset = token_index = 0

    for arc in _linear_arcs(path):
        next_input = input_offset + bool(arc.ilabel)
        while token_index < len(output_byte_spans) and output_offset >= output_byte_spans[token_index][1]:
            token_index += 1
        owner = None
        if token_index < len(output_byte_spans):
            start, end = output_byte_spans[token_index]
            if arc.ilabel and start <= output_offset < end and (output_offset != start or arc.olabel):
                deleted_leading_space = (
                    not arc.olabel and input_whitespace[input_offset] and starts[token_index] is None
                )
                if not deleted_leading_space:
                    owner = token_index
            elif arc.ilabel and arc.olabel and output_offset + 1 == start and not input_whitespace[input_offset]:
                owner = token_index
        if owner is not None:
            if starts[owner] is None:
                starts[owner] = input_offset
            ends[owner] = next_input
        input_offset = next_input
        output_offset += bool(arc.olabel)

    spans = []
    for start, end in zip(starts, ends):
        if start is None:
            raise AlignmentError("tagged token did not consume any input")
        try:
            spans.append((input_byte_to_character[start], input_byte_to_character[end]))
        except KeyError as error:
            raise AlignmentError("WFST path split a Unicode code point") from error
    return tuple(spans)


def transduce_with_spans(input_text, graph, input_spans=(), output_text=None):
    character_spans = tuple(input_spans)
    input_character_to_byte, _, _ = _text_boundaries(input_text)
    byte_spans = _byte_spans(input_text, input_character_to_byte, character_spans, reject_empty=True)
    path = exact_path(input_text, graph, output_text)
    _, selected_output, _ = linear_path(path)
    output_character_to_byte, output_byte_to_character, output_whitespace = _text_boundaries(selected_output)
    starts = [None] * len(byte_spans)
    ends = [None] * len(byte_spans)
    boundaries = {}
    input_offset = output_offset = token_index = 0

    for arc in _linear_arcs(path):
        boundaries[input_offset] = output_offset
        while token_index < len(byte_spans) and input_offset >= byte_spans[token_index][1]:
            token_index += 1
        owner = None
        if arc.ilabel and token_index < len(byte_spans):
            start, end = byte_spans[token_index]
            if start <= input_offset < end:
                owner = token_index
        elif not arc.ilabel:
            if token_index < len(byte_spans):
                start, end = byte_spans[token_index]
                if start < input_offset < end or (token_index == 0 and input_offset == start):
                    owner = token_index
            boundary_whitespace = arc.olabel and output_whitespace[output_offset]
            if owner is None and arc.olabel and not boundary_whitespace:
                previous = token_index - 1
                if previous >= 0 and byte_spans[previous][1] <= input_offset:
                    owner = previous
        if arc.olabel and owner is not None:
            if starts[owner] is None:
                starts[owner] = output_offset
            ends[owner] = output_offset + 1
        input_offset += bool(arc.ilabel)
        output_offset += bool(arc.olabel)

    boundaries[input_offset] = output_offset
    if input_offset != input_character_to_byte[-1] or output_offset != output_character_to_byte[-1]:
        raise AlignmentError("WFST path offsets do not match its input/output strings")

    output_spans = []
    previous_end = 0
    for (input_start, _), emitted_start, emitted_end in zip(byte_spans, starts, ends):
        if emitted_start is None:
            output_start = output_end = max(boundaries.get(input_start, output_offset), previous_end)
        else:
            output_start, output_end = emitted_start, emitted_end
            output_start, output_end = _snap_byte_span(output_character_to_byte, output_start, output_end)
            output_start = max(output_start, previous_end)
            output_end = max(output_end, output_start)
        try:
            output_spans.append((output_byte_to_character[output_start], output_byte_to_character[output_end]))
        except KeyError as error:
            raise AlignmentError("WFST path split a Unicode code point") from error
        previous_end = output_end
    return selected_output, tuple(output_spans)
