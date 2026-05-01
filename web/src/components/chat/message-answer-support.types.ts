import {
  GraphEdge,
  GraphEdgeProperties,
  GraphNode,
  GraphNodeProperties,
  Reference,
} from '@/api';

const SOURCE_ID_SPLIT_REGEX = /(?:<SEP>|\|)/;
export type TraceMode = 'default' | 'time' | 'space' | 'entity';

export interface PreparedReferenceRow {
  id: string;
  text: string;
  snippet: string;
  score?: number;
  collectionId?: string;
  documentId?: string;
  documentName: string;
  pageIdx?: number;
  recallType?: string;
  chunkIds: string[];
  paragraphPrecise: boolean;
  previewTitle: string;
  sectionLabel?: string;
  mdSourceMap?: [number, number];
  pdfSourceMap: Array<{
    pageIdx?: number;
    bbox?: number[];
    paraType?: string;
  }>;
  sourceHref?: string;
}

export interface AnswerGraphNodeProperties extends GraphNodeProperties {
  chunk_ids?: string[];
  linked_row_ids?: string[];
}

export interface AnswerGraphEdgeProperties extends GraphEdgeProperties {
  chunk_ids?: string[];
  linked_row_ids?: string[];
  source_chunk_id?: string;
}

export interface AnswerGraphNode extends GraphNode {
  properties: AnswerGraphNodeProperties;
}

export interface AnswerGraphEdge extends GraphEdge {
  properties: AnswerGraphEdgeProperties;
}

export interface AnswerGraphPayload {
  nodes: AnswerGraphNode[];
  edges: AnswerGraphEdge[];
  linked_row_ids: string[];
  is_empty: boolean;
  empty_reason?: string | null;
  trace_mode?: TraceMode;
  layout?: 'force' | 'timeline' | 'location' | 'focus';
  focus_label?: string | null;
  groups?: TraceGraphGroup[];
}

export interface AnswerGraphReferenceInput {
  source_row_id: string;
  text?: string;
  document_id?: string;
  document_name?: string;
  chunk_ids: string[];
}

export interface TraceGraphGroup {
  id: string;
  label: string;
  kind?: 'default' | 'time' | 'space' | 'entity' | 'fallback';
  node_ids: string[];
  row_ids: string[];
}

export interface TraceConclusion {
  id: string;
  title: string;
  statement: string;
  source_row_ids: string[];
  locator_quality: 'precise' | 'approximate';
  time_label?: string | null;
  place_label?: string | null;
  focus_entity?: string | null;
}

export interface TraceSupportReferenceInput {
  source_row_id: string;
  text?: string;
  snippet?: string;
  document_id?: string;
  document_name?: string;
  preview_title?: string;
  page_idx?: number;
  section_label?: string;
  chunk_ids: string[];
  paragraph_precise: boolean;
  md_source_map?: number[];
  pdf_source_map?: Array<{
    page_idx?: number;
    bbox?: number[];
    para_type?: string;
  }>;
}

export interface TraceSupportRequestInput {
  trace_mode: TraceMode;
  question: string;
  answer: string;
  references: TraceSupportReferenceInput[];
  max_conclusions?: number;
  max_nodes?: number;
}

export interface TraceSupportPayload {
  trace_mode: TraceMode;
  normalized_focus?: string | null;
  conclusions: TraceConclusion[];
  graph: AnswerGraphPayload;
  evidence_summary?: string | null;
  fallback_used: boolean;
}

const CITATION_TOKEN_PATTERN = /\[(\d+)\]/g;
const CITATION_TEXT_TOKEN_PATTERN = /[A-Za-z][A-Za-z0-9._-]*|[\u4e00-\u9fff]{2,}/g;

const normalizeCitationText = (value: string): string =>
  (value || '')
    .toLowerCase()
    .replace(/\[(\d+)\]/g, ' ')
    .replace(/[^\p{L}\p{N}\s]/gu, ' ')
    .replace(/\s+/g, ' ')
    .trim();

const tokenizeCitationText = (value: string): string[] =>
  normalizeCitationText(value).match(CITATION_TEXT_TOKEN_PATTERN) || [];

const buildCitationToken = (indices: number[]): string =>
  indices.map((index) => `[${index}]`).join('');

const buildCitationAnchor = (index: number, rowId: string): string =>
  `<a href="citation://${encodeURIComponent(rowId)}" data-citation-index="${index}" data-citation-row-id="${encodeURIComponent(rowId)}">[${index}]</a>`;

const collectCitationNumbers = (line: string): number[] => {
  const seen = new Set<number>();
  const matches = line.matchAll(CITATION_TOKEN_PATTERN);
  for (const match of matches) {
    const index = Number(match[1]);
    if (Number.isFinite(index)) {
      seen.add(index);
    }
  }
  return Array.from(seen).sort((a, b) => a - b);
};

const buildReferenceIndexMap = (rows: PreparedReferenceRow[]): Record<string, number> =>
  rows.reduce<Record<string, number>>((result, row, index) => {
    result[row.id] = index + 1;
    return result;
  }, {});

const scoreConclusionForLine = (
  line: string,
  conclusion: TraceConclusion,
): number => {
  const lineText = normalizeCitationText(line);
  const conclusionText = normalizeCitationText(conclusion.statement);
  if (!lineText || !conclusionText) {
    return 0;
  }
  if (lineText.includes(conclusionText) || conclusionText.includes(lineText)) {
    return 1000 + Math.min(lineText.length, conclusionText.length);
  }

  const lineTokens = new Set(tokenizeCitationText(line));
  const conclusionTokens = new Set(tokenizeCitationText(conclusion.statement));
  if (!lineTokens.size || !conclusionTokens.size) {
    return 0;
  }

  let overlap = 0;
  conclusionTokens.forEach((token) => {
    if (lineTokens.has(token)) {
      overlap += 1;
    }
  });

  if (!overlap) {
    return 0;
  }

  return overlap * 100 + Math.min(lineTokens.size, conclusionTokens.size);
};

export const annotateAnswerWithCitations = (
  answer: string,
  conclusions: TraceConclusion[],
  rows: PreparedReferenceRow[],
): string => {
  if (!answer.trim() || !conclusions.length || !rows.length) {
    return answer;
  }

  const referenceIndexMap = buildReferenceIndexMap(rows);
  const referenceRowByIndex = rows.reduce<Record<number, PreparedReferenceRow>>(
    (result, row, index) => {
      result[index + 1] = row;
      return result;
    },
    {},
  );
  const lines = answer.split('\n');
  const markersByLine = new Map<number, Set<number>>();

  conclusions.forEach((conclusion) => {
    const citationIndexes = Array.from(
      new Set(
        conclusion.source_row_ids
          .map((rowId) => referenceIndexMap[rowId])
          .filter((value): value is number => Number.isFinite(value)),
      ),
    ).sort((a, b) => a - b);

    if (!citationIndexes.length) {
      return;
    }

    let bestLineIndex = -1;
    let bestScore = 0;

    lines.forEach((line, index) => {
      const trimmed = line.trim();
      if (!trimmed || trimmed.startsWith('#')) {
        return;
      }
      const score = scoreConclusionForLine(line, conclusion);
      if (score > bestScore) {
        bestScore = score;
        bestLineIndex = index;
      }
    });

    if (bestLineIndex < 0 || bestScore <= 0) {
      return;
    }

    const markerSet = markersByLine.get(bestLineIndex) || new Set<number>();
    citationIndexes.forEach((index) => markerSet.add(index));
    markersByLine.set(bestLineIndex, markerSet);
  });

  const annotated = lines
    .map((line, index) => {
      const markerSet = markersByLine.get(index);
      if (!markerSet || !markerSet.size) {
        return line;
      }
      const existing = new Set(collectCitationNumbers(line));
      const merged = Array.from(new Set([...existing, ...markerSet])).sort(
        (a, b) => a - b,
      );
      if (!merged.length) {
        return line;
      }
      return `${line}${buildCitationToken(merged.filter((value) => !existing.has(value)))}`
        .replace(/\s+\[/g, '[')
        .trimEnd();
    })
    .join('\n');

  return annotated.replace(CITATION_TOKEN_PATTERN, (match, rawIndex) => {
    const index = Number(rawIndex);
    const row = referenceRowByIndex[index];
    if (!row) {
      return match;
    }
    return buildCitationAnchor(index, row.id);
  });
};

export const splitSourceIds = (value: unknown): string[] => {
  if (Array.isArray(value)) {
    return value.flatMap((item) => splitSourceIds(item));
  }
  if (typeof value !== 'string') {
    return [];
  }
  return value
    .split(SOURCE_ID_SPLIT_REGEX)
    .map((item) => item.trim())
    .filter(Boolean);
};

export const dedupePreserveOrder = (values: string[]): string[] => {
  const seen = new Set<string>();
  return values.filter((value) => {
    if (!value || seen.has(value)) {
      return false;
    }
    seen.add(value);
    return true;
  });
};

const toOptionalString = (value: unknown): string | undefined => {
  if (typeof value !== 'string') {
    return undefined;
  }
  const trimmed = value.trim();
  return trimmed || undefined;
};

const toOptionalNumber = (value: unknown): number | undefined => {
  if (typeof value === 'number' && Number.isFinite(value)) {
    return value;
  }
  if (typeof value === 'string' && value.trim()) {
    const parsed = Number(value);
    if (Number.isFinite(parsed)) {
      return parsed;
    }
  }
  return undefined;
};

const toOptionalStringArray = (value: unknown): string[] => {
  if (!Array.isArray(value)) {
    return [];
  }
  return value
    .map((item) => (typeof item === 'string' ? item.trim() : ''))
    .filter(Boolean);
};

const toMdSourceMap = (value: unknown): [number, number] | undefined => {
  if (!Array.isArray(value) || value.length < 2) {
    return undefined;
  }
  const start = toOptionalNumber(value[0]);
  const end = toOptionalNumber(value[1]);
  if (start === undefined || end === undefined) {
    return undefined;
  }
  return start <= end ? [start, end] : [end, start];
};

const toPdfSourceMap = (
  value: unknown,
): PreparedReferenceRow['pdfSourceMap'] => {
  if (!Array.isArray(value)) {
    return [];
  }

  const seen = new Set<string>();
  return value
    .map((item) => {
      if (!item || typeof item !== 'object') {
        return undefined;
      }
      const record = item as Record<string, unknown>;
      const pageIdx = toOptionalNumber(record.page_idx);
      const bbox = Array.isArray(record.bbox)
        ? record.bbox.filter(
            (point): point is number =>
              typeof point === 'number' && Number.isFinite(point),
          )
        : undefined;
      const paraType = toOptionalString(record.para_type);
      if (pageIdx === undefined && !bbox?.length && !paraType) {
        return undefined;
      }
      return { pageIdx, bbox, paraType };
    })
    .filter((item): item is NonNullable<typeof item> => Boolean(item))
    .filter((item) => {
      const key = JSON.stringify(item);
      if (seen.has(key)) {
        return false;
      }
      seen.add(key);
      return true;
    });
};

const normalizeWhitespace = (value: string): string =>
  value
    .replace(/\r\n?/g, '\n')
    .replace(/[ \t]+\n/g, '\n')
    .replace(/\n{3,}/g, '\n\n')
    .replace(/[ \t]{2,}/g, ' ')
    .trim();

const stripReferenceEnvelope = (value: string): string => {
  if (!value.trim()) {
    return '';
  }

  let cleaned = normalizeWhitespace(value);
  const contentMatch = cleaned.match(
    /(?:^|\n)(?:Content|Passage|Excerpt)\s*:\s*([\s\S]+)/i,
  );
  if (contentMatch?.[1]) {
    cleaned = contentMatch[1];
  }

  cleaned = cleaned
    .split('\n')
    .map((line) => line.replace(/^>\s?/, '').trimEnd())
    .filter((line) => {
      const normalized = line.trim();
      if (!normalized) {
        return true;
      }
      if (/^#{1,6}\s+/.test(normalized)) {
        return false;
      }
      if (/^\*\s*\[\]\(/.test(normalized)) {
        return false;
      }
      return !/^(document|source|file|recall[\s_-]?type|score|chunk[\s_-]?ids?|hierarchy|time|date|captured\s+at|fetched\s+at|published\s+time|url\s+source|url|title|时间|来源|地址|抓取时间|发布时间|链接|摘要)\s*[:：]/i.test(
        normalized,
      );
    })
    .join('\n');

  return normalizeWhitespace(cleaned);
};

const firstNonEmptyLine = (value: string): string | undefined =>
  value
    .split('\n')
    .map((line) => line.trim())
    .find(Boolean);

const extractSectionLabel = (
  value: string,
  titles: string[] = [],
): string | undefined => {
  if (titles.length > 0) {
    return titles.join(' > ');
  }

  const hierarchyMatch = value.match(/(?:^|\n)Hierarchy\s*:\s*([^\n]+)/i);
  if (hierarchyMatch?.[1]) {
    return normalizeWhitespace(hierarchyMatch[1]);
  }

  const headingMatch = value.match(/(?:^|\n)#{1,6}\s+([^\n]+)/);
  if (headingMatch?.[1]) {
    return normalizeWhitespace(headingMatch[1]);
  }

  const numberedMatch = value.match(
    /(?:^|\n)((?:section|chapter|part)\s+\d+[:.]?)\s*([^\n]{1,40})/i,
  );
  if (numberedMatch) {
    return normalizeWhitespace(
      `${numberedMatch[1]} ${numberedMatch[2]}`.trim(),
    );
  }

  const leadLine = firstNonEmptyLine(value);
  if (!leadLine) {
    return undefined;
  }
  if (leadLine.length <= 40 && !/[.!?。！？]/.test(leadLine)) {
    return leadLine;
  }
  return undefined;
};

const ellipsize = (value: string, limit: number): string => {
  if (value.length <= limit) {
    return value;
  }
  return `${value.slice(0, Math.max(limit - 3, 1)).trim()}...`;
};

export const getLinkedRowIds = (
  properties: AnswerGraphNodeProperties | AnswerGraphEdgeProperties | undefined,
): string[] => {
  const linkedRowIds = properties?.linked_row_ids;
  if (!Array.isArray(linkedRowIds)) {
    return [];
  }
  return linkedRowIds
    .map((item) => (typeof item === 'string' ? item.trim() : ''))
    .filter(Boolean);
};

export const getNodeDisplayName = (node: AnswerGraphNode): string => {
  return String(
    node.properties?.entity_name || node.properties?.entity_id || node.id || '',
  );
};

export const getEntityType = (node: AnswerGraphNode): string => {
  return String(node.properties?.entity_type || node.labels?.[0] || 'Entity');
};

const formatPageLabel = (pageIdx: number): string => `P.${pageIdx + 1}`;

const formatLineLabel = (mdSourceMap?: [number, number]): string | undefined => {
  if (!mdSourceMap) {
    return undefined;
  }
  const [start, end] = mdSourceMap;
  const startLine = start + 1;
  const endLine = Math.max(end, startLine);
  if (startLine === endLine) {
    return `L.${startLine}`;
  }
  return `L.${startLine}-${endLine}`;
};

export const buildReferenceLocationLabel = (
  row: Pick<
    PreparedReferenceRow,
    'pageIdx' | 'sectionLabel' | 'paragraphPrecise' | 'mdSourceMap' | 'pdfSourceMap'
  >,
  fallbackText: string,
): string => {
  const parts: string[] = [];
  const lineLabel = formatLineLabel(row.mdSourceMap);
  const pageCandidates = [
    row.pageIdx,
    ...row.pdfSourceMap
      .map((item) => item.pageIdx)
      .filter((item): item is number => typeof item === 'number'),
  ];
  const uniquePages = dedupePreserveOrder(pageCandidates.map((item) => String(item)))
    .map((item) => Number(item))
    .filter((item) => Number.isFinite(item));

  if (uniquePages.length === 1) {
    parts.push(formatPageLabel(uniquePages[0]));
  } else if (uniquePages.length > 1) {
    parts.push(
      `${formatPageLabel(uniquePages[0])}-${formatPageLabel(uniquePages[uniquePages.length - 1]).replace('P.', '')}`,
    );
  }

  if (lineLabel) {
    parts.push(lineLabel);
  }

  if (row.sectionLabel) {
    parts.push(row.sectionLabel);
  }

  if (!parts.length && !row.paragraphPrecise) {
    parts.push(fallbackText);
  }

  return parts.join(' · ');
};

const buildDocumentSourceHref = ({
  collectionId,
  documentId,
  mdSourceMap,
  pageIdx,
  pdfSourceMap,
  sectionLabel,
}: Pick<
  PreparedReferenceRow,
  | 'collectionId'
  | 'documentId'
  | 'mdSourceMap'
  | 'pageIdx'
  | 'pdfSourceMap'
  | 'sectionLabel'
>): string | undefined => {
  if (!collectionId || !documentId) {
    return undefined;
  }

  const params = new URLSearchParams();
  if (mdSourceMap) {
    params.set('lineStart', String(mdSourceMap[0]));
    params.set('lineEnd', String(mdSourceMap[1]));
  }

  const pageCandidate =
    pageIdx ??
    pdfSourceMap.find((item) => typeof item.pageIdx === 'number')?.pageIdx;
  if (typeof pageCandidate === 'number') {
    params.set('page', String(pageCandidate));
  }
  if (sectionLabel) {
    params.set('section', sectionLabel);
  }
  params.set('from', 'answer-source');

  return `/workspace/collections/${collectionId}/documents/${documentId}?${params.toString()}`;
};

const limitPreparedReferenceRows = (
  rows: PreparedReferenceRow[],
  maxRows: number,
): PreparedReferenceRow[] => {
  if (rows.length <= maxRows) {
    return rows;
  }

  const selected: PreparedReferenceRow[] = [];
  const selectedRowIds = new Set<string>();
  const seenDocuments = new Set<string>();

  for (const row of rows) {
    const documentKey = row.documentId || row.documentName;
    if (seenDocuments.has(documentKey)) {
      continue;
    }
    selected.push(row);
    selectedRowIds.add(row.id);
    seenDocuments.add(documentKey);
    if (selected.length >= maxRows) {
      return selected;
    }
  }

  for (const row of rows) {
    if (selectedRowIds.has(row.id)) {
      continue;
    }
    selected.push(row);
    selectedRowIds.add(row.id);
    if (selected.length >= maxRows) {
      break;
    }
  }

  return selected;
};

export const prepareReferenceRows = (
  references: Reference[],
  maxRows = 15,
): PreparedReferenceRow[] => {
  const rows = new Map<string, PreparedReferenceRow>();

  references.forEach((reference, index) => {
    const metadata = reference.metadata || {};
    const documentName =
      toOptionalString(metadata.document_name) ||
      toOptionalString(metadata.source) ||
      toOptionalString(metadata.file_path) ||
      'Untitled document';
    const documentId =
      toOptionalString(metadata.document_id) ||
      toOptionalString(metadata.doc_id) ||
      toOptionalString(metadata.full_doc_id);
    const collectionId = toOptionalString(metadata.collection_id);
    const pageIdx = toOptionalNumber(metadata.page_idx);
    const recallType =
      toOptionalString(metadata.recall_type) || toOptionalString(metadata.type);
    const chunkIds = dedupePreserveOrder([
      ...splitSourceIds(metadata.chunk_ids),
      ...splitSourceIds(metadata.chunk_id),
      ...splitSourceIds(metadata.source_chunk_id),
      ...splitSourceIds(metadata.source_id),
    ]);
    const mdSourceMap = toMdSourceMap(metadata.md_source_map);
    const pdfSourceMap = toPdfSourceMap(metadata.pdf_source_map);
    const titles = toOptionalStringArray(metadata.titles);
    const paragraphPrecise =
      typeof metadata.paragraph_precise === 'boolean'
        ? metadata.paragraph_precise
        : (Boolean(reference.text?.trim()) || Boolean(mdSourceMap)) &&
          recallType !== 'graph_search';
    const cleanedText =
      stripReferenceEnvelope(reference.text || '') ||
      normalizeWhitespace(reference.text || '');
    if (!cleanedText) {
      return;
    }
    if (
      recallType === 'graph_search' &&
      !documentId &&
      !mdSourceMap &&
      pdfSourceMap.length === 0 &&
      /^Entities\(KG\):/i.test(cleanedText)
    ) {
      return;
    }
    const snippet = cleanedText.replace(/\n+/g, ' ').trim();
    const sectionLabel = extractSectionLabel(
      reference.text || cleanedText,
      titles,
    );
    const previewTitle =
      toOptionalString(metadata.preview_title) || documentName;
    const fallbackId = [
      'source-row',
      documentId || documentName,
      pageIdx ?? 'na',
      index,
      (reference.text || '').slice(0, 24),
    ].join(':');
    const id = toOptionalString(metadata.source_row_id) || fallbackId;
    const dedupeKey = [
      documentId || documentName,
      pageIdx ?? 'na',
      sectionLabel || 'no-section',
      snippet || cleanedText.slice(0, 160),
    ].join('::');

    if (!rows.has(dedupeKey)) {
      const nextRow: PreparedReferenceRow = {
        id,
        text: cleanedText,
        snippet: snippet ? ellipsize(snippet, 180) : '',
        score: reference.score,
        collectionId,
        documentId,
        documentName,
        pageIdx,
        recallType,
        chunkIds,
        paragraphPrecise,
        previewTitle,
        sectionLabel,
        mdSourceMap,
        pdfSourceMap,
      };
      nextRow.sourceHref = buildDocumentSourceHref(nextRow);
      rows.set(dedupeKey, nextRow);
    }
  });

  return limitPreparedReferenceRows(Array.from(rows.values()), maxRows);
};

export const buildAnswerGraphReferences = (
  rows: PreparedReferenceRow[],
): AnswerGraphReferenceInput[] =>
  rows.map((row) => ({
    source_row_id: row.id,
    text: row.text,
    document_id: row.documentId,
    document_name: row.documentName,
    chunk_ids: row.chunkIds,
  }));

export const buildTraceSupportRequest = ({
  rows,
  question,
  answer,
  traceMode,
}: {
  rows: PreparedReferenceRow[];
  question: string;
  answer: string;
  traceMode: TraceMode;
}): TraceSupportRequestInput => ({
  trace_mode: traceMode,
  question,
  answer,
  max_conclusions: 8,
  max_nodes: 36,
  references: rows.map((row) => ({
    source_row_id: row.id,
    text: row.text,
    snippet: row.snippet,
    document_id: row.documentId,
    document_name: row.documentName,
    preview_title: row.previewTitle,
    page_idx: row.pageIdx,
    section_label: row.sectionLabel,
    chunk_ids: row.chunkIds,
    paragraph_precise: row.paragraphPrecise,
    md_source_map: row.mdSourceMap,
    pdf_source_map: row.pdfSourceMap.map((item) => ({
      page_idx: item.pageIdx,
      bbox: item.bbox,
      para_type: item.paraType,
    })),
  })),
});

export const buildConclusionMapByRowId = (
  conclusions: TraceConclusion[],
): Record<string, TraceConclusion[]> =>
  conclusions.reduce<Record<string, TraceConclusion[]>>((result, conclusion) => {
    conclusion.source_row_ids.forEach((rowId) => {
      if (!result[rowId]) {
        result[rowId] = [];
      }
      result[rowId]?.push(conclusion);
    });
    return result;
  }, {});
