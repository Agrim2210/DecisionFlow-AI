   
from __future__ import annotations

import re
import time
import uuid
from dataclasses import dataclass, field


@dataclass
class NormalizedTranscript:
    raw_text: str
    cleaned_text: str
    speaker_map: dict[str, str]                                       
    detected_speakers: list[str]
    word_count: int
    estimated_duration_minutes: float
    chunks: list[str] = field(default_factory=list)                         


class S1Normalizer:
       

                                        
    _SPEAKER_PATTERNS = [
        re.compile(r"^([A-Z][a-zA-Z\s]{1,30}):\s*", re.MULTILINE),                         
        re.compile(r"^\[([A-Z][a-zA-Z\s]{1,30})\]\s*", re.MULTILINE),                       
        re.compile(r"^<([A-Z][a-zA-Z\s]{1,30})>\s*", re.MULTILINE),                         
        re.compile(r"^(Speaker\s+\d+):\s*", re.MULTILINE),                                 
        re.compile(r"^\d{1,2}:\d{2}:\d{2}\s+([A-Z][a-zA-Z\s]{1,30}):\s*",                    
                   re.MULTILINE),
    ]

    _FILLER_PATTERNS = [
        re.compile(r"\b(um|uh|hmm|mhm|ah|er|like,?\s+you\s+know)\b", re.IGNORECASE),
        re.compile(r"\[inaudible\]", re.IGNORECASE),
        re.compile(r"\[crosstalk\]", re.IGNORECASE),
        re.compile(r"\[laughter\]", re.IGNORECASE),
    ]

    def run(self, raw_text: str, known_users: list[dict] | None = None) -> NormalizedTranscript:
           
        t0 = time.perf_counter()

                           
        cleaned = self._clean(raw_text)

                            
        speakers = self._detect_speakers(cleaned)

                                   
        speaker_map = self._build_speaker_map(speakers, known_users or [])

                                                                                    
        word_count = len(cleaned.split())
        chunks = self._chunk(cleaned, max_words=2000) if word_count > 6000 else [cleaned]

                                                               
        duration_min = round(word_count / 130, 1)

        elapsed = round(time.perf_counter() - t0, 3)

        return NormalizedTranscript(
            raw_text=raw_text,
            cleaned_text=cleaned,
            speaker_map=speaker_map,
            detected_speakers=speakers,
            word_count=word_count,
            estimated_duration_minutes=duration_min,
            chunks=chunks,
        )

    def _clean(self, text: str) -> str:
                                
        text = text.replace("\r\n", "\n").replace("\r", "\n")
                                      
        text = re.sub(r"\n{3,}", "\n\n", text)
                                                       
        text = re.sub(r"^\d{1,2}:\d{2}:\d{2}\s*$", "", text, flags=re.MULTILINE)
                             
        for pattern in self._FILLER_PATTERNS:
            text = pattern.sub("", text)
                            
        text = re.sub(r" {2,}", " ", text)
        return text.strip()

    def _detect_speakers(self, text: str) -> list[str]:
        speakers: set[str] = set()
        for pattern in self._SPEAKER_PATTERNS:
            for match in pattern.finditer(text):
                name = match.group(1).strip()
                if 2 <= len(name) <= 40:
                    speakers.add(name)
        return sorted(speakers)

    def _build_speaker_map(
        self, speakers: list[str], known_users: list[dict]
    ) -> dict[str, str]:
           
        mapping: dict[str, str] = {}
        for speaker in speakers:
            speaker_lower = speaker.lower()
            for user in known_users:
                user_name_lower = user.get("name", "").lower()
                if speaker_lower in user_name_lower or user_name_lower in speaker_lower:
                    mapping[speaker] = user.get("id", speaker)
                    break
            if speaker not in mapping:
                mapping[speaker] = speaker                                    
        return mapping

    def _chunk(self, text: str, max_words: int = 2000) -> list[str]:
                                                                               
        words = text.split()
        chunks: list[str] = []
        overlap = 100                                                       

        i = 0
        while i < len(words):
            chunk_words = words[i : i + max_words]
            chunks.append(" ".join(chunk_words))
            i += max_words - overlap

        return chunks
