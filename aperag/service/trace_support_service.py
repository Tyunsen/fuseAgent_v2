from __future__ import annotations

import re
from difflib import SequenceMatcher
from typing import Iterable

from aperag.schema import view_models
from aperag.service.trace_answer_service import trace_answer_service

SENTENCE_SPLIT_PATTERN = re.compile(r"(?<=[。！？!?])\s+|\n+")
TOKEN_PATTERN = re.compile(r"[A-Za-z][A-Za-z0-9._-]*|[\u4e00-\u9fff]{2,}")
ROW_HEADING_PATTERN = re.compile(r"^\s*#{1,6}\s*(.+?)\s*$")
SENTENCE_SPLIT_PATTERN = re.compile(r"(?<=[。！？!?])\s*|\n+")
FULL_DATE_RANGE_PATTERN = re.compile(
    r"(?P<year>\d{4})[年/-](?P<start_month>\d{1,2})(?:月|-)(?P<start_day>\d{1,2})(?:日)?"
    r"\s*(?:至|到|~|～|—|–|-)\s*(?:(?P<end_month>\d{1,2})(?:月|-))?(?P<end_day>\d{1,2})(?:日)?"
)
PARTIAL_DATE_RANGE_PATTERN = re.compile(
    r"(?P<start_month>\d{1,2})月(?P<start_day>\d{1,2})(?:日)?"
    r"\s*(?:至|到|~|～|—|–|-)\s*(?:(?P<end_month>\d{1,2})月)?(?P<end_day>\d{1,2})(?:日)?"
)
FULL_DATE_PATTERN = re.compile(
    r"(?P<year>\d{4})[年/-](?P<month>\d{1,2})(?:月|-)(?P<day>\d{1,2})(?:日)?"
)
PARTIAL_MONTH_DAY_PATTERN = re.compile(r"(?P<month>\d{1,2})月(?P<day>\d{1,2})(?:日)?")
YEAR_MONTH_PATTERN = re.compile(r"(?P<year>\d{4})[年/-](?P<month>\d{1,2})(?!\d)")
YEAR_PATTERN = re.compile(r"(?P<year>\d{4})年?")

GENERIC_TITLE_PREFIXES = (
    "根据",
    "基于",
    "围绕",
    "关于",
    "以下按时间顺序梳理",
    "以下按时间脉络梳理",
    "以下是",
    "时间脉络",
    "实体脉络",
    "空间脉络",
)
GENERIC_TITLE_VALUES = {
    "时间结论",
    "空间结论",
    "实体结论",
    "重点结论",
    "相关事件",
}


def _normalize_text(value: str) -> str:
    return " ".join((value or "").strip().lower().split())


def _tokenize(value: str) -> list[str]:
    return [token.strip().lower() for token in TOKEN_PATTERN.findall(value or "") if token.strip()]


def _dedupe_preserve_order(values: Iterable[str]) -> list[str]:
    result: list[str] = []
    seen: set[str] = set()
    for value in values:
        if value and value not in seen:
            seen.add(value)
            result.append(value)
    return result


class TraceSupportService:
    def __init__(self) -> None:
        from aperag.service.answer_graph_service import answer_graph_service

        self.answer_graph_service = answer_graph_service

    async def build_trace_support(
        self,
        *,
        user_id: str,
        collection_id: str,
        request: view_models.TraceSupportRequest,
    ) -> view_models.TraceSupportResponse:
        trace_mode = trace_answer_service.normalize_trace_mode(request.trace_mode)
        normalized_focus = trace_answer_service.infer_normalized_focus(trace_mode, request.question)
        rows = request.references or []

        conclusions = self._build_conclusions(
            answer=request.answer,
            rows=rows,
            trace_mode=trace_mode,
            normalized_focus=normalized_focus,
            max_conclusions=request.max_conclusions or 8,
        )
        fallback_used = any(conclusion.locator_quality == "approximate" for conclusion in conclusions)

        graph = await self.answer_graph_service.get_trace_graph(
            user_id=user_id,
            collection_id=collection_id,
            references=[
                view_models.AnswerGraphReferenceInput(
                    source_row_id=row.source_row_id,
                    text=row.text,
                    document_id=row.document_id,
                    document_name=row.document_name,
                    chunk_ids=row.chunk_ids,
                )
                for row in rows
            ],
            trace_mode=trace_mode,
            normalized_focus=normalized_focus,
            max_nodes=request.max_nodes or 36,
            row_contexts=rows,
            conclusions=conclusions,
        )
        fallback_used = fallback_used or graph.is_empty or bool(graph.empty_reason)

        return view_models.TraceSupportResponse(
            trace_mode=trace_mode,
            normalized_focus=normalized_focus,
            conclusions=conclusions,
            graph=graph,
            evidence_summary=trace_answer_service.build_evidence_summary(
                trace_mode,
                len(conclusions),
                fallback_used,
            ),
            fallback_used=fallback_used,
        )

    def _build_conclusions(
        self,
        *,
        answer: str,
        rows: list[view_models.TraceSupportReferenceInput],
        trace_mode: str,
        normalized_focus: str | None,
        max_conclusions: int,
    ) -> list[view_models.TraceConclusion]:
        statements = self._extract_candidate_statements(
            answer,
            max_conclusions=max_conclusions,
        )
        if trace_mode == "time":
            fallback_statements = self._extract_fallback_statements(
                rows,
                max_conclusions=max_conclusions,
                require_explicit_time=True,
            )
            statements = _dedupe_preserve_order(
                [*statements, *fallback_statements]
            )[:max_conclusions]
        elif not statements:
            statements = self._extract_fallback_statements(
                rows,
                max_conclusions=max_conclusions,
            )

        conclusions: list[view_models.TraceConclusion] = []
        for index, statement in enumerate(statements, start=1):
            bound_rows = self._bind_rows(statement, rows)
            if not bound_rows and rows:
                bound_rows = rows[:1]
            locator_quality = (
                "precise"
                if bound_rows and all(row.paragraph_precise for row in bound_rows)
                else "approximate"
            )
            source_row_ids = [row.source_row_id for row in bound_rows[:2]]
            conclusion = view_models.TraceConclusion(
                id=f"conclusion_{index}",
                title=self._build_conclusion_title(statement, trace_mode, bound_rows, index),
                statement=statement,
                source_row_ids=source_row_ids,
                locator_quality=locator_quality,
                time_label=self._pick_time_label(trace_mode, normalized_focus, bound_rows, statement),
                place_label=self._pick_place_label(trace_mode, normalized_focus, bound_rows),
                focus_entity=self._pick_focus_entity(trace_mode, normalized_focus, bound_rows, statement),
            )
            conclusions.append(conclusion)

        if trace_mode == "time":
            conclusions = self._filter_time_conclusions(
                conclusions,
                normalized_focus=normalized_focus,
                max_conclusions=max_conclusions,
            )
        return conclusions

    def _extract_candidate_statements(self, answer: str, *, max_conclusions: int) -> list[str]:
        lines: list[str] = []
        for raw_part in SENTENCE_SPLIT_PATTERN.split(answer or ""):
            cleaned = re.sub(r"^\s*(?:[-*•]|\d+[.)、])\s*", "", raw_part.strip())
            cleaned = self._clean_event_title_refined(cleaned)
            if len(cleaned) < 10:
                continue
            if cleaned.startswith("```") or cleaned.startswith("##"):
                continue
            lines.append(cleaned)
        return _dedupe_preserve_order(lines)[:max_conclusions]

    def _extract_fallback_statements(
        self,
        rows: list[view_models.TraceSupportReferenceInput],
        *,
        max_conclusions: int,
        require_explicit_time: bool = False,
    ) -> list[str]:
        results: list[str] = []
        for row in rows:
            candidate = self._extract_row_statement(
                row,
                require_explicit_time=require_explicit_time,
            )
            if len(candidate) >= 10:
                results.append(candidate)
            if len(results) >= max_conclusions:
                break
        return _dedupe_preserve_order(results)

    def _extract_row_statement(
        self,
        row: view_models.TraceSupportReferenceInput,
        *,
        require_explicit_time: bool = False,
    ) -> str:
        text = (row.text or row.snippet or "").strip()
        section = (row.section_label or "").strip()

        timed_line_candidates = [
            self._clean_event_title_refined(line)
            for line in text.splitlines()
            if self._has_explicit_time(line)
        ]
        line_candidates = [self._clean_event_title_refined(line) for line in text.splitlines()]

        preferred_candidates = timed_line_candidates if require_explicit_time else []
        fallback_candidates = [
            *line_candidates,
            self._clean_event_title_refined(row.snippet or ""),
            self._clean_event_title_refined(text),
            self._clean_event_title_refined(section),
            self._clean_event_title_refined(row.preview_title or ""),
        ]

        for candidate in (*preferred_candidates, *fallback_candidates):
            if candidate:
                return candidate

        return self._clean_event_title_refined(text)

    @staticmethod
    def _clean_row_line(value: str) -> str:
        candidate = (value or "").strip()
        if not candidate:
            return ""

        heading_match = ROW_HEADING_PATTERN.match(candidate)
        if heading_match:
            candidate = heading_match.group(1).strip()

        candidate = re.sub(r"^文档\d+[:：\s]*", "", candidate)
        candidate = re.sub(r"https?://\S+", "", candidate)
        candidate = re.sub(r"\[!\[[^\]]*\]\([^)]+\)\]", "", candidate)
        candidate = re.sub(r"\[[^\]]+\]\([^)]+\)", "", candidate)
        candidate = re.sub(r"\s+", " ", candidate).strip(" -:：，。；;[](){}<>")

        if not candidate:
            return ""

        lowered = candidate.lower()
        blocked_prefixes = (
            "imported from",
            "source:",
            "url:",
            "url source:",
            "entry count",
            "page count",
            "published",
            "title:",
            "markdown content",
            "hierarchy:",
        )
        if lowered.startswith(blocked_prefixes):
            return ""
        if candidate.startswith("# Imported from"):
            return ""
        if "http" in lowered:
            return ""
        if ".html" in lowered or "retryafter" in lowered or "data null" in lowered:
            return ""
        if "status" in lowered and "retry" in lowered:
            return ""
        if len(candidate) < 4:
            return ""

        sentence = re.split(r"[。；;\n]", candidate, maxsplit=1)[0].strip()
        return sentence[:48].strip()

    def _clean_event_title(self, value: str) -> str:
        candidate = self._clean_row_line(value)
        if not candidate:
            return ""

        for prefix in GENERIC_TITLE_PREFIXES:
            if candidate.startswith(prefix):
                candidate = candidate[len(prefix) :].lstrip("：:，, ")

        candidate = re.sub(
            r"^(?:\d{4}[年/-]\d{1,2}(?:月|-)?(?:\d{1,2}(?:日)?)?(?:\s*(?:至|到|~|～|—|–|-)\s*(?:\d{1,2}月)?\d{1,2}(?:日)?)?)\s*[，,、:：-]*",
            "",
            candidate,
        )
        candidate = re.sub(
            r"^(?:\d{1,2}月(?:\d{1,2}日?)?)\s*[，,、:：-]*",
            "",
            candidate,
        )
        candidate = re.sub(r"^(?:时间|空间|实体)结论\d*[:：]?\s*", "", candidate)
        candidate = candidate.split("：", maxsplit=1)[-1].strip() if "：" in candidate[:10] else candidate
        candidate = re.split(r"[，。；;:\n]", candidate, maxsplit=1)[0].strip()
        candidate = candidate.strip(" -:：，。；;[](){}<>")
        if candidate in GENERIC_TITLE_VALUES or len(candidate) < 2:
            return ""
        return candidate[:32].strip()

    def _clean_event_title_refined(self, value: str) -> str:
        candidate = self._clean_event_title(value)
        if not candidate:
            return ""

        candidate = re.sub(r"^(?:\d{4}|month:\d{2})\s*", "", candidate).strip()
        candidate = candidate.strip("：:，, ")
        if self._is_low_quality_time_title(candidate):
            return ""
        return candidate

    @staticmethod
    def _has_explicit_time(value: str) -> bool:
        return bool(
            FULL_DATE_RANGE_PATTERN.search(value or "")
            or FULL_DATE_PATTERN.search(value or "")
            or PARTIAL_DATE_RANGE_PATTERN.search(value or "")
            or PARTIAL_MONTH_DAY_PATTERN.search(value or "")
            or YEAR_MONTH_PATTERN.search(value or "")
        )

    @staticmethod
    def _is_low_quality_time_title(value: str) -> bool:
        lowered = (value or "").strip().lower()
        if not lowered:
            return True
        blocked_parts = (
            "imported from",
            "triple trace acceptance",
            "条目列表",
            "hierarchy",
            "来源",
            "文档",
            "http",
            "www.",
            "法广中文中国",
        )
        return any(part in lowered for part in blocked_parts)

    def _filter_time_conclusions(
        self,
        conclusions: list[view_models.TraceConclusion],
        *,
        normalized_focus: str | None,
        max_conclusions: int,
    ) -> list[view_models.TraceConclusion]:
        ranked: list[tuple[int, view_models.TraceConclusion]] = []
        for conclusion in conclusions:
            if self._is_low_quality_time_title(conclusion.title or ""):
                continue
            time_label = conclusion.time_label or ""
            if not time_label:
                continue
            score = 0
            if "/" in time_label:
                score += 4
            elif re.match(r"^\d{4}-\d{2}-\d{2}$", time_label):
                score += 3
            elif re.match(r"^\d{4}-\d{2}$", time_label):
                score += 2
            elif re.match(r"^month:\d{2}$", time_label):
                score += 1
            elif re.match(r"^\d{4}$", time_label):
                score -= 3
            if normalized_focus and normalized_focus in time_label:
                score += 1
            ranked.append((score, conclusion))

        if not ranked:
            return []

        has_better_than_year = any(score >= 1 for score, _ in ranked)
        filtered = [
            conclusion
            for score, conclusion in ranked
            if not (has_better_than_year and re.match(r"^\d{4}$", conclusion.time_label or ""))
        ]
        return filtered[:max_conclusions]

    def _bind_rows(
        self,
        statement: str,
        rows: list[view_models.TraceSupportReferenceInput],
    ) -> list[view_models.TraceSupportReferenceInput]:
        statement_norm = _normalize_text(statement)
        statement_tokens = set(_tokenize(statement))
        scored_rows = []
        for row in rows:
            row_text = " ".join(
                filter(
                    None,
                    [
                        row.text or "",
                        row.snippet or "",
                        row.preview_title or "",
                        row.section_label or "",
                        row.document_name or "",
                    ],
                )
            )
            row_norm = _normalize_text(row_text)
            row_tokens = set(_tokenize(row_text))
            overlap = len(statement_tokens & row_tokens)
            similarity = SequenceMatcher(None, statement_norm, row_norm).ratio()
            title_bonus = 5 if row.preview_title and _normalize_text(row.preview_title) in statement_norm else 0
            score = overlap * 10 + similarity + title_bonus
            if score <= 0:
                continue
            scored_rows.append((score, row))
        scored_rows.sort(key=lambda item: item[0], reverse=True)
        return [row for _, row in scored_rows[:2]]

    def _build_conclusion_title(
        self,
        statement: str,
        trace_mode: str,
        rows: list[view_models.TraceSupportReferenceInput],
        index: int,
    ) -> str:
        for candidate in (
            self._clean_event_title_refined(statement),
            *[self._clean_event_title_refined(row.preview_title or "") for row in rows],
            *[self._clean_event_title_refined(row.section_label or "") for row in rows],
            *[self._clean_event_title_refined(row.snippet or "") for row in rows],
        ):
            if candidate:
                return candidate

        fallback_prefix = {
            "time": "时间事件",
            "space": "空间线索",
            "entity": "实体关系",
        }.get(trace_mode, "重点结论")
        return f"{fallback_prefix}{index}"

    def _pick_time_label(
        self,
        trace_mode: str,
        normalized_focus: str | None,
        rows: list[view_models.TraceSupportReferenceInput],
        statement: str,
    ) -> str | None:
        if trace_mode not in {"time", "space"}:
            return None

        for candidate in (
            statement,
            *[row.text or "" for row in rows],
            *[row.snippet or "" for row in rows],
            *[row.preview_title or "" for row in rows],
        ):
            extracted = self._extract_time_value_refined(candidate, normalized_focus)
            if not extracted:
                extracted = self._extract_time_value(candidate, normalized_focus)
            if extracted:
                return extracted

        return normalized_focus if trace_mode == "time" else None

    @staticmethod
    def _pick_place_label(
        trace_mode: str,
        normalized_focus: str | None,
        rows: list[view_models.TraceSupportReferenceInput],
    ) -> str | None:
        if trace_mode != "space":
            return None
        if normalized_focus:
            return normalized_focus
        for row in rows:
            if row.section_label:
                return row.section_label
        return None

    def _pick_focus_entity(
        self,
        trace_mode: str,
        normalized_focus: str | None,
        rows: list[view_models.TraceSupportReferenceInput],
        statement: str,
    ) -> str | None:
        if trace_mode != "entity":
            return None
        if normalized_focus:
            return normalized_focus
        for candidate in (
            *[row.preview_title or "" for row in rows],
            statement,
            *[row.section_label or "" for row in rows],
        ):
            cleaned = self._clean_event_title_refined(candidate)
            if cleaned:
                return cleaned
        return None

    def _extract_time_value_refined(self, text: str, normalized_focus: str | None) -> str | None:
        candidate = (text or "").strip()
        if not candidate:
            return None

        full_range_match = re.search(
            r"(?P<year>\d{4})\D+(?P<start_month>\d{1,2})\D+(?P<start_day>\d{1,2})\D*(?:至|到|~|～|—|–|-)\D*(?:(?P<end_month>\d{1,2})\D+)?(?P<end_day>\d{1,2})",
            candidate,
        )
        if full_range_match:
            start = self._format_date(
                full_range_match.group("year"),
                full_range_match.group("start_month"),
                full_range_match.group("start_day"),
            )
            end = self._format_date(
                full_range_match.group("year"),
                full_range_match.group("end_month") or full_range_match.group("start_month"),
                full_range_match.group("end_day"),
            )
            return f"{start}/{end}"

        full_date_match = re.search(
            r"(?P<year>\d{4})\D+(?P<month>\d{1,2})\D+(?P<day>\d{1,2})",
            candidate,
        )
        if full_date_match:
            return self._format_date(
                full_date_match.group("year"),
                full_date_match.group("month"),
                full_date_match.group("day"),
            )

        inferred_year = self._extract_year_hint_refined(candidate, normalized_focus)
        partial_range_match = re.search(
            r"(?<!\d)(?P<start_month>\d{1,2})\D+(?P<start_day>\d{1,2})\D*(?:至|到|~|～|—|–|-)\D*(?:(?P<end_month>\d{1,2})\D+)?(?P<end_day>\d{1,2})",
            candidate,
        )
        if partial_range_match and inferred_year:
            start = self._format_date(
                str(inferred_year),
                partial_range_match.group("start_month"),
                partial_range_match.group("start_day"),
            )
            end = self._format_date(
                str(inferred_year),
                partial_range_match.group("end_month") or partial_range_match.group("start_month"),
                partial_range_match.group("end_day"),
            )
            return f"{start}/{end}"

        partial_date_match = re.search(
            r"(?<!\d)(?P<month>\d{1,2})\D+(?P<day>\d{1,2})(?!\d)",
            candidate,
        )
        if partial_date_match and inferred_year:
            return self._format_date(
                str(inferred_year),
                partial_date_match.group("month"),
                partial_date_match.group("day"),
            )

        year_month_match = re.search(
            r"(?P<year>\d{4})\D{0,3}(?P<month>\d{1,2})(?!\d)",
            candidate,
        )
        if year_month_match:
            return f"{int(year_month_match.group('year')):04d}-{int(year_month_match.group('month')):02d}"

        if normalized_focus and re.match(r"^\d{4}-\d{2}$", normalized_focus):
            month_match = re.search(r"(?<!\d)(\d{1,2})(?!\d)", candidate)
            if month_match:
                return f"{normalized_focus[:4]}-{int(month_match.group(1)):02d}"

        year_match = re.search(r"(?P<year>\d{4})", candidate)
        if year_match:
            return f"{int(year_match.group('year')):04d}"

        return None

    @staticmethod
    def _extract_year_hint_refined(text: str, normalized_focus: str | None) -> int | None:
        year_match = re.search(r"(?P<year>\d{4})", text or "")
        if year_match:
            return int(year_match.group("year"))
        if normalized_focus:
            focus_match = re.match(r"^(?P<year>\d{4})", normalized_focus)
            if focus_match:
                return int(focus_match.group("year"))
        return None

    def _extract_time_value(self, text: str, normalized_focus: str | None) -> str | None:
        candidate = (text or "").strip()
        if not candidate:
            return None

        full_range_match = FULL_DATE_RANGE_PATTERN.search(candidate)
        if full_range_match:
            start = self._format_date(
                full_range_match.group("year"),
                full_range_match.group("start_month"),
                full_range_match.group("start_day"),
            )
            end = self._format_date(
                full_range_match.group("year"),
                full_range_match.group("end_month") or full_range_match.group("start_month"),
                full_range_match.group("end_day"),
            )
            return f"{start}/{end}"

        full_date_match = FULL_DATE_PATTERN.search(candidate)
        if full_date_match:
            return self._format_date(
                full_date_match.group("year"),
                full_date_match.group("month"),
                full_date_match.group("day"),
            )

        inferred_year = self._extract_year_hint(candidate, normalized_focus)
        partial_range_match = PARTIAL_DATE_RANGE_PATTERN.search(candidate)
        if partial_range_match and inferred_year:
            start_month = partial_range_match.group("start_month")
            end_month = partial_range_match.group("end_month") or start_month
            start = self._format_date(
                str(inferred_year),
                start_month,
                partial_range_match.group("start_day"),
            )
            end = self._format_date(
                str(inferred_year),
                end_month,
                partial_range_match.group("end_day"),
            )
            return f"{start}/{end}"

        partial_date_match = PARTIAL_MONTH_DAY_PATTERN.search(candidate)
        if partial_date_match and inferred_year:
            return self._format_date(
                str(inferred_year),
                partial_date_match.group("month"),
                partial_date_match.group("day"),
            )

        year_month_match = YEAR_MONTH_PATTERN.search(candidate)
        if year_month_match:
            return f"{int(year_month_match.group('year')):04d}-{int(year_month_match.group('month')):02d}"

        if normalized_focus and re.match(r"^\d{4}-\d{2}$", normalized_focus):
            month_match = re.search(r"(?<!\d)(\d{1,2})月(?!\d)", candidate)
            if month_match:
                return f"{normalized_focus[:4]}-{int(month_match.group(1)):02d}"

        year_match = YEAR_PATTERN.search(candidate)
        if year_match:
            return f"{int(year_match.group('year')):04d}"

        return None

    @staticmethod
    def _extract_year_hint(text: str, normalized_focus: str | None) -> int | None:
        year_match = YEAR_PATTERN.search(text or "")
        if year_match:
            return int(year_match.group("year"))
        if normalized_focus:
            focus_match = re.match(r"^(?P<year>\d{4})", normalized_focus)
            if focus_match:
                return int(focus_match.group("year"))
        return None

    @staticmethod
    def _format_date(year: str, month: str, day: str) -> str:
        return f"{int(year):04d}-{int(month):02d}-{int(day):02d}"


trace_support_service = TraceSupportService()
