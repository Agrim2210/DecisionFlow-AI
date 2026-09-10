   
from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field


@dataclass
class AIResponse:
                                                   
    content: str
    input_tokens: int = 0
    output_tokens: int = 0
    model: str = ""
    latency_ms: float = 0.0
    raw: dict = field(default_factory=dict)

    @property
    def total_tokens(self) -> int:
        return self.input_tokens + self.output_tokens


@dataclass
class EmbeddingResponse:
                                        
    embeddings: list[list[float]]
    input_tokens: int = 0
    dimensions: int | None = None
    latency_ms: float = 0.0
    model: str = ""


class BaseAIClient(ABC):

    @abstractmethod
    async def complete(
        self,
        system_prompt: str,
        user_prompt: str,
        max_tokens: int = 4096,
        temperature: float = 0.1,
        json_mode: bool = True,
    ) -> AIResponse:
           
        ...

    @abstractmethod
    async def embed(self, texts: list[str]) -> EmbeddingResponse:
                                                             
        ...
