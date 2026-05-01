from __future__ import annotations

import re
from dataclasses import dataclass
from datetime import date, timedelta
from typing import Optional


TRACE_MODE_DEFAULT = "default"
TRACE_MODE_TIME = "time"
TRACE_MODE_SPACE = "space"
TRACE_MODE_ENTITY = "entity"
TRACE_MODES = (
    TRACE_MODE_DEFAULT,
    TRACE_MODE_TIME,
    TRACE_MODE_SPACE,
    TRACE_MODE_ENTITY,
)

TOKEN_PATTERN = re.compile(r"[A-Za-z][A-Za-z0-9._-]*|[\u4e00-\u9fff]{2,}")
CAPITALIZED_PHRASE_PATTERN = re.compile(r"\b[A-Z][a-z]+(?:\s+[A-Z][a-z]+){0,3}\b")
QUOTED_TERM_PATTERN = re.compile(r"[\"“”'《](.+?)[\"“”'》]")
TIME_YEAR_MONTH_PATTERN = re.compile(r"(?P<year>\d{4})[年/-](?P<month>\d{1,2})")
TIME_MONTH_PATTERN = re.compile(r"(?<!\d)(?P<month>\d{1,2})月")
TIME_YEAR_PATTERN = re.compile(r"(?P<year>\d{4})年")
TIME_DAY_PATTERN = re.compile(
    r"(?P<year>\d{4})[年/-](?P<month>\d{1,2})[月/-](?P<day>\d{1,2})日?"
)

GENERIC_CN_TOKENS = {
    "发生",
    "事情",
    "什么",
    "哪些",
    "情况",
    "相关",
    "问题",
    "模式",
    "脉络",
    "时间",
    "地点",
    "空间",
    "实体",
    "事件",
    "资料",
    "文档",
    "结论",
    "回答",
    "知识库",
    "看看",
}
GENERIC_EN_TOKENS = {
    "what",
    "which",
    "when",
    "where",
    "about",
    "tell",
    "show",
    "happened",
    "happen",
    "event",
    "events",
    "time",
    "space",
    "entity",
    "knowledge",
    "base",
}


@dataclass
class TracePromptContext:
    trace_mode: str
    normalized_focus: Optional[str]
    query_keywords: list[str]
    channels: list[str]


class TraceAnswerService:
    def normalize_trace_mode(self, trace_mode: str | None) -> str:
        normalized = str(trace_mode or TRACE_MODE_DEFAULT).strip().lower()
        return normalized if normalized in TRACE_MODES else TRACE_MODE_DEFAULT

    def infer_normalized_focus(self, trace_mode: str, query: str) -> Optional[str]:
        normalized_mode = self.normalize_trace_mode(trace_mode)
        if normalized_mode == TRACE_MODE_TIME:
            return self._infer_time_focus(query)
        if normalized_mode == TRACE_MODE_SPACE:
            return self._infer_place_focus(query)
        if normalized_mode == TRACE_MODE_ENTITY:
            return self._infer_entity_focus(query)
        return None

    def build_prompt_context(
        self,
        *,
        trace_mode: str | None,
        query: str,
        query_keywords: list[str],
        channels: list[str],
    ) -> TracePromptContext:
        normalized_mode = self.normalize_trace_mode(trace_mode)
        return TracePromptContext(
            trace_mode=normalized_mode,
            normalized_focus=self.infer_normalized_focus(normalized_mode, query),
            query_keywords=query_keywords,
            channels=channels,
        )

    def build_prompt_appendix(self, context: TracePromptContext) -> str:
        channels = ", ".join(context.channels) if context.channels else "vector_search, fulltext_search, graph_search"
        keywords = ", ".join(context.query_keywords) if context.query_keywords else "none"

        if context.trace_mode == TRACE_MODE_DEFAULT:
            return (
                "Trace mode: default.\n"
                f"Keep the current answer style as the baseline experience. Use the normal mixed retrieval path ({channels}) and answer directly without forcing a trace structure.\n"
                "Use broad retrieval rather than overly narrow retrieval. Prefer enough evidence to support a solid answer rather than stopping after a tiny result set.\n"
                f"Preferred full-text keywords when useful: {keywords}.\n"
                "When graph evidence is available, keep the default topology/process Mermaid graph in the answer."
            )

        normalized_focus = context.normalized_focus or "not explicitly identified"
        if context.trace_mode == TRACE_MODE_TIME:
            return (
                "Trace mode: time.\n"
                f"Normalized time focus: {normalized_focus}.\n"
                f"Use the normal mixed retrieval path ({channels}). When search_collection is helpful, keep full-text keywords aligned with the time focus: {keywords}.\n"
                "Do not over-compress retrieval. Gather enough evidence to enumerate many concrete dated events before answering.\n"
                "Organize the answer chronologically or by time period. Prefer 6-10 concrete dated events when the evidence supports them, instead of collapsing the month into only one or two abstract summaries.\n"
                "If the source evidence only gives partial time information, keep the strongest available ordering and say where time precision is limited.\n"
                "If Mermaid is used, it must be a gantt chart only.\n"
                "Do not include a Mermaid graph TD topology/process graph or any other knowledge-graph diagram in time mode.\n"
                "Use day-level dates in the gantt chart when the source evidence supports exact days.\n"
                "Use real event names or short event phrases as gantt task labels. Never use generic labels like Time conclusion 1 or numbered placeholders.\n"
                "Each gantt bar should represent one concrete event or a short evidence-backed action window, not a broad abstract event spanning the whole period."
            )
        if context.trace_mode == TRACE_MODE_SPACE:
            return (
                "Trace mode: space.\n"
                f"Normalized place focus: {normalized_focus}.\n"
                f"Use the normal mixed retrieval path ({channels}). When search_collection is helpful, keep full-text keywords aligned with the place focus: {keywords}.\n"
                "Use broad retrieval rather than overly narrow retrieval so place-relevant evidence is not lost before organization.\n"
                "Keep the same answer shell as default mode. Emphasize place-relevant findings when the query clearly names a location, but do not introduce a separate trace summary or conclusion section.\n"
                "Include the same Mermaid graph TD topology/process graph used by default mode. Do not include a gantt chart for space mode."
            )
        return (
            "Trace mode: entity.\n"
            f"Normalized focal entity: {normalized_focus}.\n"
            f"Use the normal mixed retrieval path ({channels}). When search_collection is helpful, keep full-text keywords aligned with the focal entity: {keywords}.\n"
            "Use broad retrieval rather than overly narrow retrieval so the entity subgraph can preserve related edges as well as nodes.\n"
            "Organize the answer around the focal entity and its most relevant linked actions, relationships, and supporting facts. If entity disambiguation is weak, say which evidence is strongest.\n"
            "Ground the answer in retrieved evidence and keep visible source support.\n"
            "Do not include a Mermaid knowledge subgraph in the answer body. The interface will render the answer-scoped knowledge graph separately using the existing graph component."
        )

    def build_evidence_summary(self, trace_mode: str, conclusion_count: int, fallback_used: bool) -> str:
        if trace_mode == TRACE_MODE_TIME:
            summary = f"按时间整理出 {conclusion_count} 条重点结论。"
        elif trace_mode == TRACE_MODE_SPACE:
            summary = f"按地点整理出 {conclusion_count} 条重点结论。"
        elif trace_mode == TRACE_MODE_ENTITY:
            summary = f"按实体整理出 {conclusion_count} 条重点结论。"
        else:
            summary = f"保留默认模式并提炼出 {conclusion_count} 条重点结论。"
        if fallback_used:
            summary += " 部分结论使用了较弱的结构化证据排序。"
        return summary

    def _infer_time_focus(self, query: str) -> Optional[str]:
        query = (query or "").strip()
        if not query:
            return None

        day_match = TIME_DAY_PATTERN.search(query)
        if day_match:
            return f"{int(day_match.group('year')):04d}-{int(day_match.group('month')):02d}-{int(day_match.group('day')):02d}"

        year_month_match = TIME_YEAR_MONTH_PATTERN.search(query)
        if year_month_match:
            return f"{int(year_month_match.group('year')):04d}-{int(year_month_match.group('month')):02d}"

        year_match = TIME_YEAR_PATTERN.search(query)
        month_match = TIME_MONTH_PATTERN.search(query)
        if year_match and month_match:
            return f"{int(year_match.group('year')):04d}-{int(month_match.group('month')):02d}"
        if year_match:
            return f"{int(year_match.group('year')):04d}"
        if month_match:
            return f"month:{int(month_match.group('month')):02d}"

        today = date.today()
        if "本月" in query or "这个月" in query:
            return today.replace(day=1).isoformat()
        if "上月" in query or "上个月" in query:
            last_month = (today.replace(day=1) - timedelta(days=1)).replace(day=1)
            return last_month.isoformat()
        if "今年" in query:
            return f"{today.year:04d}"
        if "去年" in query:
            return f"{today.year - 1:04d}"
        if "近期" in query or "最近" in query:
            return "recent"
        return None

    def _infer_place_focus(self, query: str) -> Optional[str]:
        quoted = self._extract_quoted_term(query)
        if quoted:
            return quoted

        for pattern in (
            r"(?:在|于|围绕|聚焦|查看|看看)([\u4e00-\u9fffA-Za-z·\-\s]{2,24}?)(?:发生|出现|相关|情况|有哪些|周边|附近|$)",
            r"([\u4e00-\u9fffA-Za-z·\-\s]{2,24}?)(?:发生了什么|发生过什么|有哪些情况)",
        ):
            match = re.search(pattern, query)
            if match:
                candidate = self._clean_focus_term(match.group(1))
                if candidate:
                    return candidate

        capitalized = CAPITALIZED_PHRASE_PATTERN.search(query or "")
        if capitalized:
            return capitalized.group(0).strip()

        return self._pick_best_token(query)

    def _infer_entity_focus(self, query: str) -> Optional[str]:
        quoted = self._extract_quoted_term(query)
        if quoted:
            return quoted

        for pattern in (
            r"(?:关于|围绕|聚焦|查看|关注)([\u4e00-\u9fffA-Za-z·\-\s]{2,24}?)(?:的|相关|情况|有哪些|$)",
            r"([\u4e00-\u9fffA-Za-z·\-\s]{2,24}?)(?:相关的|有哪些动作|有哪些行动|做了什么|情况如何)",
        ):
            match = re.search(pattern, query)
            if match:
                candidate = self._clean_focus_term(match.group(1))
                if candidate:
                    return candidate

        capitalized = CAPITALIZED_PHRASE_PATTERN.search(query or "")
        if capitalized:
            return capitalized.group(0).strip()

        return self._pick_best_token(query)

    @staticmethod
    def _extract_quoted_term(query: str) -> Optional[str]:
        match = QUOTED_TERM_PATTERN.search(query or "")
        if not match:
            return None
        return TraceAnswerService._clean_focus_term(match.group(1))

    @staticmethod
    def _clean_focus_term(value: str) -> Optional[str]:
        cleaned = re.sub(r"\s+", " ", str(value or "").strip(" ，。；;:：\"'“”《》"))
        return cleaned or None

    def _pick_best_token(self, query: str) -> Optional[str]:
        tokens = []
        for token in TOKEN_PATTERN.findall(query or ""):
            cleaned = self._clean_focus_term(token)
            if not cleaned:
                continue
            lowered = cleaned.lower()
            if cleaned in GENERIC_CN_TOKENS or lowered in GENERIC_EN_TOKENS:
                continue
            tokens.append(cleaned)
        if not tokens:
            return None
        return sorted(tokens, key=lambda item: (len(item), item), reverse=True)[0]


trace_answer_service = TraceAnswerService()
