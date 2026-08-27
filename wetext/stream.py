"""Stateful streaming text normalization."""

from wetext.config import NormalizerConfig
from wetext.constants import get_prefix_fst
from wetext.fst_utils import compose_input
from wetext.utils import normalize

_ASCII_TOKEN_EXTRA = frozenset(("'", "-", "_"))
_PREFIX_PROBE_CHARS = 8
_PENDING_RENDER_CHARS = 64
_HARD_COMMIT_BOUNDARIES = frozenset("。；！？")


def _is_ascii_token_char(char):
    return char.isascii() and (char.isalnum() or char in _ASCII_TOKEN_EXTRA)


def _match_prefix_position(text, lang, operator, enable_0_to_9):
    """Return the earliest suffix that may grow into a semantic rule.

    ``None`` means that the installed model bundle predates streaming support.
    """

    graph = get_prefix_fst(lang, operator, enable_0_to_9)
    if graph is None:
        return None
    for index in range(len(text)):
        if compose_input(text[index:], graph).start != -1:
            return index
    return len(text)


class StreamNormalizer:
    """Incrementally normalize a stream of text chunks.

    A stream instance owns its pending input and must not be shared between
    utterances or threads.  Call :meth:`reset` before reusing it.
    """

    def __init__(self, **kwargs):
        kwargs.setdefault("operator", "itn")
        self.config = NormalizerConfig(**kwargs)
        if self.config.operator not in ("tn", "itn"):
            raise ValueError("StreamNormalizer requires operator='tn' or operator='itn'")
        if self.config.lang == "auto":
            raise ValueError("StreamNormalizer requires an explicit lang")
        self.reset()

    def reset(self):
        """Start a new, empty utterance."""

        self._pending = ""
        self._committed_text = ""
        self._closed = False

    def _normalize_piece(self, text):
        stripped = text.strip()
        if not stripped:
            return ""
        leading = ""
        if self._committed_text:
            leading = text[: len(text) - len(text.lstrip())]
            if leading and self.config.lang == "en":
                # The English normalization graphs canonicalize every internal
                # whitespace run to one space.
                leading = " "
        return leading + normalize(stripped, config=self.config)

    def _render_pending(self):
        if len(self._pending) <= _PENDING_RENDER_CHARS:
            return self._normalize_piece(self._pending)
        raw_head = self._pending[:-_PENDING_RENDER_CHARS]
        tail = self._pending[-_PENDING_RENDER_CHARS:]
        return raw_head + self._normalize_piece(tail)

    def _safe_position(self, text):
        if text and text[-1] in _HARD_COMMIT_BOUNDARIES:
            return len(text)

        # An unfinished ASCII token cannot be committed safely, and scanning
        # every suffix of it would make character-by-character input quadratic.
        token = text.lstrip()
        if token and all(_is_ascii_token_char(char) for char in token):
            return 0

        # Long semantic prefixes (numbers, dates, model names) often remain at
        # position zero for many frames. Probe a fixed-size head on most calls;
        # a zero match is conservative, because retaining extra input is safe.
        # Explicit sentence boundaries above commit completed rules. Otherwise
        # retaining a long prefix is preferable to an unbounded suffix scan.
        if len(text) > _PREFIX_PROBE_CHARS:
            head_position = _match_prefix_position(
                text[:_PREFIX_PROBE_CHARS],
                self.config.lang,
                self.config.operator,
                self.config.enable_0_to_9,
            )
            if head_position is None or head_position == 0:
                return 0

        safe_position = _match_prefix_position(
            text,
            self.config.lang,
            self.config.operator,
            self.config.enable_0_to_9,
        )
        if safe_position is None:
            return 0

        # A prefix can begin before a provisional cut found on the complete
        # buffer (for example, each level of a nested fraction). Roll back to
        # a fixed point so an already committed delta cannot be invalidated by
        # a future chunk. The position decreases monotonically, so this loop
        # always terminates.
        while 0 < safe_position < len(text):
            candidate = text[:safe_position]
            rollback = _match_prefix_position(
                candidate,
                self.config.lang,
                self.config.operator,
                self.config.enable_0_to_9,
            )
            if rollback is None or rollback >= len(candidate):
                break
            safe_position = rollback

        # Never split or prematurely commit a trailing ASCII token. A fixed
        # ASR chunk is not necessarily a lexical boundary ("don" + "'t"), and
        # neither the semantic prefix graph nor the normalizer's catch-all word
        # rule can prove that such a token is complete.
        while (
            0 < safe_position < len(text)
            and _is_ascii_token_char(text[safe_position - 1])
            and _is_ascii_token_char(text[safe_position])
        ):
            safe_position -= 1
        if safe_position == len(text) and safe_position > 0 and _is_ascii_token_char(text[-1]):
            while safe_position > 0 and _is_ascii_token_char(text[safe_position - 1]):
                safe_position -= 1

        # Keeping boundary whitespace in pending preserves it when the next
        # semantic rule arrives; batch normalization only trims outer space.
        while safe_position > 0 and text[safe_position - 1].isspace():
            safe_position -= 1
        return safe_position

    def feed(self, text):
        """Consume a new text chunk and return the complete current output.

        Args:
            text: New input since the previous call.
        """

        if self._closed:
            raise RuntimeError("stream is already flushed; call reset() before feed()")
        if not isinstance(text, str):
            raise TypeError("text must be a string")

        combined = self._pending + text
        safe_position = self._safe_position(combined)
        committed_input = combined[:safe_position]
        self._pending = combined[safe_position:]

        committed = self._normalize_piece(committed_input)
        self._committed_text += committed
        return self._committed_text + self._render_pending()

    def flush(self):
        """Commit the remaining input and return the final output."""

        if self._closed:
            return self._committed_text

        committed = self._normalize_piece(self._pending)
        self._committed_text += committed
        self._pending = ""
        self._closed = True
        return self._committed_text
