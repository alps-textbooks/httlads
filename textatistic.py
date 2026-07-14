"""In-browser compatibility shim for ``textatistic``.

``textatistic`` ships no pure-Python wheel that installs in the Pyodide
(in-browser) runtime, so ``import textatistic`` cannot resolve via micropip.
The notebooks use it for standard readability metrics, so provide a light
implementation of the common surface — the ``Textatistic`` object with word /
sentence / syllable counts and the Flesch Reading Ease and Flesch-Kincaid
grade scores. Syllable counting uses a vowel-group heuristic, so the scores
are close to but not identical to the upstream library (which uses PyHyphen).
"""

import re

_WORD_RE = re.compile(r"[A-Za-z']+")
_VOWEL_GROUP_RE = re.compile(r"[aeiouy]+")


def _syllables(word):
    word = word.lower().strip("'")
    groups = _VOWEL_GROUP_RE.findall(word)
    n = len(groups)
    # A trailing silent 'e' usually doesn't add a syllable.
    if word.endswith("e") and n > 1:
        n -= 1
    return max(1, n)


class Textatistic:
    """Compute readability statistics for ``text``. Mirrors the attributes the
    upstream package exposes: the ``*_count`` fields, ``flesch_score``,
    ``fleschkincaid_score``, and the ``counts`` / ``scores`` / ``dict`` views."""

    def __init__(self, text):
        self.text = text
        words = _WORD_RE.findall(text)
        sentences = [s for s in re.split(r"[.!?]+", text) if s.strip()]

        self.word_count = len(words)
        self.sent_count = max(1, len(sentences))
        self.sybl_count = sum(_syllables(w) for w in words)
        self.char_count = sum(len(w) for w in words)
        self.notdalechall_count = 0  # upstream field; not computed here
        self.polysyblword_count = sum(1 for w in words if _syllables(w) >= 3)

        words_per_sent = self.word_count / self.sent_count
        sybls_per_word = self.sybl_count / max(1, self.word_count)
        self.flesch_score = 206.835 - 1.015 * words_per_sent - 84.6 * sybls_per_word
        self.fleschkincaid_score = 0.39 * words_per_sent + 11.8 * sybls_per_word - 15.59
        self.gunningfog_score = 0.4 * (words_per_sent + 100 * self.polysyblword_count / max(1, self.word_count))

    @property
    def counts(self):
        return {
            "char_count": self.char_count,
            "word_count": self.word_count,
            "sent_count": self.sent_count,
            "sybl_count": self.sybl_count,
            "notdalechall_count": self.notdalechall_count,
            "polysyblword_count": self.polysyblword_count,
        }

    @property
    def scores(self):
        return {
            "flesch_score": self.flesch_score,
            "fleschkincaid_score": self.fleschkincaid_score,
            "gunningfog_score": self.gunningfog_score,
        }

    def dict(self):
        merged = dict(self.counts)
        merged.update(self.scores)
        return merged
