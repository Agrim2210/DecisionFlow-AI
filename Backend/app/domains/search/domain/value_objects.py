from __future__ import annotations

from dataclasses import dataclass


_VALID_MODES = frozenset({"semantic", "keyword", "hybrid"})
_VALID_SOURCE_TYPES = frozenset({"decision", "action_item", "transcript"})


@dataclass(frozen=True)
class SearchMode:
    value: str

    def __post_init__(self) -> None:
        if self.value not in _VALID_MODES:
            raise ValueError(f"Invalid search mode '{self.value}'. Valid: {sorted(_VALID_MODES)}")

    @property
    def is_semantic(self) -> bool:
        return self.value == "semantic"

    @property
    def is_keyword(self) -> bool:
        return self.value == "keyword"

    @property
    def is_hybrid(self) -> bool:
        return self.value == "hybrid"

    @property
    def uses_embeddings(self) -> bool:
        return self.value in ("semantic", "hybrid")

    @property
    def uses_keyword(self) -> bool:
        return self.value in ("keyword", "hybrid")

    def __str__(self) -> str:
        return self.value

    SEMANTIC = "semantic"
    KEYWORD  = "keyword"
    HYBRID   = "hybrid"

    @classmethod
    def safe(cls, value: str) -> "SearchMode":
        return cls(value if value in _VALID_MODES else "hybrid")


@dataclass(frozen=True)
class SourceType:
    value: str

    def __post_init__(self) -> None:
        if self.value not in _VALID_SOURCE_TYPES:
            raise ValueError(
                f"Invalid source type '{self.value}'. Valid: {sorted(_VALID_SOURCE_TYPES)}"
            )

    @property
    def is_decision(self) -> bool:
        return self.value == "decision"

    @property
    def is_action_item(self) -> bool:
        return self.value == "action_item"

    @property
    def is_transcript(self) -> bool:
        return self.value == "transcript"

    def __str__(self) -> str:
        return self.value

    DECISION    = "decision"
    ACTION_ITEM = "action_item"
    TRANSCRIPT  = "transcript"

    @classmethod
    def safe(cls, value: str | None) -> "SourceType | None":
        if value is None:
            return None
        return cls(value if value in _VALID_SOURCE_TYPES else "decision")


@dataclass(frozen=True)
class RelevanceScore:
       
    value: float

    def __post_init__(self) -> None:
        clamped = max(0.0, min(1.0, float(self.value)))
        object.__setattr__(self, "value", round(clamped, 6))

    @property
    def is_high(self) -> bool:
        return self.value >= 0.8

    @property
    def is_medium(self) -> bool:
        return 0.4 <= self.value < 0.8

    @property
    def is_low(self) -> bool:
        return self.value < 0.4

    @property
    def label(self) -> str:
        if self.is_high:
            return "high"
        elif self.is_medium:
            return "medium"
        return "low"

    def __float__(self) -> float:
        return self.value

    def __str__(self) -> str:
        return str(self.value)

    @classmethod
    def safe(cls, value: float | None) -> "RelevanceScore":
        return cls(value if value is not None else 0.0)


@dataclass(frozen=True)
class SearchQuery:
       
    value: str

    def __post_init__(self) -> None:
        stripped = self.value.strip()
        object.__setattr__(self, "value", stripped)
        if len(stripped) < 1:
            raise ValueError("Search query cannot be empty")
        if len(stripped) > 500:
            raise ValueError("Search query cannot exceed 500 characters")

    @property
    def word_count(self) -> int:
        return len(self.value.split())

    @property
    def is_single_word(self) -> bool:
        return self.word_count == 1

    @property
    def is_phrase(self) -> bool:
        return self.word_count > 1

    def __str__(self) -> str:
        return self.value

    @classmethod
    def safe(cls, value: str) -> "SearchQuery":
        truncated = value.strip()[:500] or "search"
        return cls(truncated)


@dataclass(frozen=True)
class EmbeddingVector:
       
    values: tuple[float, ...]
    expected_dims: int = settings.AI_EMBEDDING_DIMS

    def __post_init__(self) -> None:
        if len(self.values) != self.expected_dims:
            raise ValueError(
                f"Embedding must have {self.expected_dims} dimensions, "
                f"got {len(self.values)}"
            )

    @property
    def dims(self) -> int:
        return len(self.values)

    def to_list(self) -> list[float]:
        return list(self.values)

    @classmethod
    def from_list(cls, values: list[float], expected_dims: int | None = None) -> "EmbeddingVector":
        if expected_dims is None:
            expected_dims = settings.AI_EMBEDDING_DIMS
        return cls(values=tuple(values), expected_dims=expected_dims)

    @classmethod
    def safe(cls, values: list[float]) -> "EmbeddingVector | None":
        try:
            return cls.from_list(values)
        except ValueError:
            return None
