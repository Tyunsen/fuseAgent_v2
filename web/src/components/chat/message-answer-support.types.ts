import {
  GraphEdge,
  GraphEdgeProperties,
  GraphNode,
  GraphNodeProperties,
  Reference,
} from '@/api';

const SOURCE_ID_SPLIT_REGEX = /(?:<SEP>|\|)/;

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
}

export interface AnswerGraphReferenceInput {
  source_row_id: string;
  text?: string;
  document_id?: string;
  document_name?: string;
  chunk_ids: string[];
}

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
  maxRows = 5,
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
