from __future__ import annotations

import re


class TextProcessor:
    @staticmethod
    def preprocess_text(text: str) -> str:
        text = text.replace("\r\n", "\n").replace("\r", "\n")
        text = re.sub(r"\n{3,}", "\n\n", text)
        lines = [line.strip() for line in text.split("\n")]
        return "\n".join(lines).strip()

    @staticmethod
    def split_text(text: str, *, chunk_size: int, overlap: int) -> list[str]:
        cleaned = TextProcessor.preprocess_text(text)
        if not cleaned:
            return []

        if chunk_size <= 0:
            return [cleaned]

        chunks: list[str] = []
        start = 0
        text_length = len(cleaned)
        overlap = max(0, min(overlap, chunk_size - 1)) if chunk_size > 1 else 0

        while start < text_length:
            end = min(text_length, start + chunk_size)
            if end < text_length:
                paragraph_break = cleaned.rfind("\n\n", start, end)
                line_break = cleaned.rfind("\n", start, end)
                split_at = paragraph_break if paragraph_break > start else line_break
                if split_at > start + int(chunk_size * 0.5):
                    end = split_at

            chunk = cleaned[start:end].strip()
            if chunk:
                chunks.append(chunk)

            if end >= text_length:
                break

            start = max(start + 1, end - overlap)

        return chunks
