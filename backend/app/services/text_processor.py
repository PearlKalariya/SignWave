from typing import List
from collections import deque


SPACE_GESTURE = "SPACE"
DELETE_GESTURE = "DELETE"
NOTHING_GESTURE = "NOTHING"
HOLD_FRAMES = 8  # frames a sign must hold to register


class TextProcessor:
    def __init__(self):
        self._current_word: List[str] = []
        self._words: List[str] = []
        self._last_label: str = ""
        self._hold_count: int = 0
        self._committed: deque = deque(maxlen=20)

    def process(self, label: str) -> dict:
        if label == NOTHING_GESTURE:
            self._hold_count = 0
            return self._state()

        if label == self._last_label:
            self._hold_count += 1
        else:
            self._last_label = label
            self._hold_count = 1
            return self._state()

        if self._hold_count != HOLD_FRAMES:
            return self._state()

        # commit action
        if label == SPACE_GESTURE:
            if self._current_word:
                self._words.append("".join(self._current_word))
                self._current_word = []
        elif label == DELETE_GESTURE:
            if self._current_word:
                self._current_word.pop()
            elif self._words:
                self._words.pop()
        else:
            self._current_word.append(label)

        self._hold_count = 0
        return self._state()

    def _state(self) -> dict:
        in_progress = "".join(self._current_word)
        sentence = " ".join(self._words)
        if in_progress:
            full = f"{sentence} {in_progress}".strip()
        else:
            full = sentence
        return {
            "current_letter": self._last_label,
            "current_word": in_progress,
            "sentence": full,
        }

    def reset(self):
        self._current_word = []
        self._words = []
        self._last_label = ""
        self._hold_count = 0

    def get_sentence(self) -> str:
        return " ".join(self._words)
