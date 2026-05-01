'use client';

import { Reference } from '@/api';
import { ChartMermaid } from '@/components/chart-mermaid';
import { Badge } from '@/components/ui/badge';
import {
  Drawer,
  DrawerContent,
  DrawerDescription,
  DrawerHeader,
  DrawerTitle,
} from '@/components/ui/drawer';
import { useTranslations } from 'next-intl';
import { useEffect, useMemo, useState } from 'react';
import {
  buildGanttMermaid,
  extractRenderableTimeLabel,
  MessageAnswerGraph,
} from './message-answer-graph';
import {
  TraceMode,
  TraceConclusion,
  TraceSupportPayload,
  buildConclusionMapByRowId,
  buildTraceSupportRequest,
  prepareReferenceRows,
} from './message-answer-support.types';
import { MessageReferenceCard } from './message-reference-card';

const EMPTY_GRAPH_MESSAGE_KEYS = {
  no_references: 'empty_reasons.no_references',
  graph_unavailable: 'empty_reasons.graph_unavailable',
  graph_linking_unavailable: 'empty_reasons.graph_linking_unavailable',
  no_matching_graph_elements: 'empty_reasons.no_matching_graph_elements',
} as const;

type EmptyGraphReason = keyof typeof EMPTY_GRAPH_MESSAGE_KEYS;

const isEmptyGraphReason = (
  value: string | null | undefined,
): value is EmptyGraphReason =>
  Boolean(value && value in EMPTY_GRAPH_MESSAGE_KEYS);

const getFallbackLayout = (traceMode: TraceMode) =>
  traceMode === 'default'
    ? 'force'
    : traceMode === 'time'
      ? 'timeline'
      : traceMode === 'space'
        ? 'location'
        : 'force';

const normalizeTimelineTimeLabel = (value?: string | null) => {
  const label = (value || '').trim();
  if (!label) {
    return '';
  }
  return label.replace('/', ' 至 ');
};

const getTimelineSortValue = (value?: string | null) => {
  const label = (value || '').trim();
  if (!label) {
    return '9999-99-99';
  }
  if (label.includes('/')) {
    return label.split('/', 1)[0];
  }
  if (/^\d{4}-\d{2}-\d{2}$/.test(label)) {
    return label;
  }
  if (/^\d{4}-\d{2}$/.test(label)) {
    return `${label}-01`;
  }
  return `9999-${label}`;
};

const buildTimelineItems = (conclusions: TraceConclusion[]) =>
  [...conclusions]
    .map((item) => ({
      ...item,
      rendered_time_label: extractRenderableTimeLabel(item),
    }))
    .filter((item) => item.rendered_time_label && item.title)
    .sort((left, right) =>
      getTimelineSortValue(left.rendered_time_label).localeCompare(
        getTimelineSortValue(right.rendered_time_label),
      ),
    );

export const MessageAnswerSupport = ({
  references,
  answer,
  question,
  traceMode,
  embeddedMermaid,
  requestedRowId,
  requestVersion,
  sourcesOpen,
  onSourcesOpenChange,
  onSupportChange,
}: {
  references: Reference[];
  answer: string;
  question: string;
  traceMode: TraceMode;
  embeddedMermaid?: string | null;
  requestedRowId?: string | null;
  requestVersion?: number;
  sourcesOpen: boolean;
  onSourcesOpenChange: (open: boolean) => void;
  onSupportChange?: (support: TraceSupportPayload | null) => void;
}) => {
  const t = useTranslations('page_chat.answer_support');
  const rows = useMemo(() => prepareReferenceRows(references), [references]);
  const collectionId = useMemo(
    () => rows.find((row) => row.collectionId)?.collectionId,
    [rows],
  );
  const shouldLoadTraceSupport = Boolean(rows.length);
  const shouldLoadStructuredTraceGraph =
    traceMode === 'time' || traceMode === 'entity';
  const traceRequest = useMemo(
    () =>
      buildTraceSupportRequest({
        rows,
        question,
        answer,
        traceMode,
      }),
    [answer, question, rows, traceMode],
  );
  const requestKey = useMemo(() => JSON.stringify(traceRequest), [traceRequest]);

  const [support, setSupport] = useState<TraceSupportPayload | null>(null);
  const [supportLoading, setSupportLoading] = useState(false);
  const [activeRowIds, setActiveRowIds] = useState<string[]>([]);
  const [activeNodeIds, setActiveNodeIds] = useState<string[]>([]);
  const [activeEdgeIds, setActiveEdgeIds] = useState<string[]>([]);
  const [expandedRowIds, setExpandedRowIds] = useState<string[]>([]);
  useEffect(() => {
    setSupport(null);
    setSupportLoading(false);
    setActiveRowIds([]);
    setActiveNodeIds([]);
    setActiveEdgeIds([]);
    setExpandedRowIds([]);
    onSourcesOpenChange(false);
    onSupportChange?.(null);
  }, [onSourcesOpenChange, onSupportChange, requestKey]);

  useEffect(() => {
    if (!shouldLoadTraceSupport) {
      setSupport(null);
      setSupportLoading(false);
      return;
    }

    if (!rows.length) {
      setSupport(null);
      setSupportLoading(false);
      return;
    }

    if (!collectionId) {
      setSupport({
        trace_mode: traceMode,
        conclusions: [],
        evidence_summary: '',
        fallback_used: true,
        graph: {
          nodes: [],
          edges: [],
          linked_row_ids: [],
          is_empty: true,
          empty_reason: 'graph_linking_unavailable',
          trace_mode: traceMode,
          layout: getFallbackLayout(traceMode),
          groups: [],
        },
      });
      setSupportLoading(false);
      return;
    }

    const controller = new AbortController();

    const loadSupport = async () => {
      setSupportLoading(true);
      try {
        const response = await fetch(
          `${process.env.NEXT_PUBLIC_BASE_PATH || ''}/api/v1/collections/${collectionId}/trace-support`,
          {
            method: 'POST',
            headers: {
              'Content-Type': 'application/json',
            },
            body: JSON.stringify(traceRequest),
            signal: controller.signal,
          },
        );

        if (!response.ok) {
          setSupport({
            trace_mode: traceMode,
            conclusions: [],
            evidence_summary: '',
            fallback_used: true,
            graph: {
              nodes: [],
              edges: [],
              linked_row_ids: [],
              is_empty: true,
              empty_reason: 'graph_unavailable',
              trace_mode: traceMode,
              layout: getFallbackLayout(traceMode),
              groups: [],
            },
          });
          return;
        }

        const data = (await response.json()) as TraceSupportPayload;
        setSupport(data);
      } catch {
        if (!controller.signal.aborted) {
          setSupport({
            trace_mode: traceMode,
            conclusions: [],
            evidence_summary: '',
            fallback_used: true,
            graph: {
              nodes: [],
              edges: [],
              linked_row_ids: [],
              is_empty: true,
              empty_reason: 'graph_unavailable',
              trace_mode: traceMode,
              layout: getFallbackLayout(traceMode),
              groups: [],
            },
          });
        }
      } finally {
        if (!controller.signal.aborted) {
          setSupportLoading(false);
        }
      }
    };

    void loadSupport();
    return () => controller.abort();
  }, [
    collectionId,
    requestKey,
    rows.length,
    shouldLoadTraceSupport,
    traceMode,
    traceRequest,
  ]);

  useEffect(() => {
    onSupportChange?.(support);
  }, [onSupportChange, support]);

  useEffect(() => {
    if (!requestedRowId || !requestVersion) {
      return;
    }

    onSourcesOpenChange(true);
    setActiveRowIds([requestedRowId]);
    setExpandedRowIds((current) =>
      current.includes(requestedRowId) ? current : [...current, requestedRowId],
    );
  }, [onSourcesOpenChange, requestedRowId, requestVersion]);

  const graph = support?.graph || null;
  const conclusionMap = useMemo(
    () => buildConclusionMapByRowId(support?.conclusions || []),
    [support?.conclusions],
  );

  const selectRows = (rowIds: string[]) => {
    setActiveRowIds(rowIds);

    if (!graph) {
      setActiveNodeIds([]);
      setActiveEdgeIds([]);
      return;
    }

    setActiveNodeIds(
      graph.nodes
        .filter((node) =>
          (node.properties?.linked_row_ids || []).some((rowId) =>
            rowIds.includes(rowId),
          ),
        )
        .map((node) => node.id),
    );
    setActiveEdgeIds(
      graph.edges
        .filter((edge) =>
          (edge.properties?.linked_row_ids || []).some((rowId) =>
            rowIds.includes(rowId),
          ),
        )
        .map((edge) => edge.id),
    );

    if (rowIds.length) {
      setExpandedRowIds((current) => Array.from(new Set([...current, ...rowIds])));
    }
  };

  const graphReason = support?.graph?.empty_reason;
  const emptyGraphMessage = isEmptyGraphReason(graphReason)
    ? t(EMPTY_GRAPH_MESSAGE_KEYS[graphReason])
    : t('graph_empty');
  const shouldRenderStructuredGraph = shouldLoadStructuredTraceGraph && Boolean(graph);
  const shouldRenderMermaidGraph =
    !shouldLoadStructuredTraceGraph && Boolean(embeddedMermaid);
  const timeTimelineItems = useMemo(
    () => buildTimelineItems(support?.conclusions || []),
    [support?.conclusions],
  );
  const timeGanttMermaid = useMemo(
    () =>
      traceMode === 'time' && graph
        ? buildGanttMermaid({
            graph,
            conclusions: support?.conclusions || [],
            graphTitle: t('event_gantt_title'),
            focusLabel: t('focus_label'),
          })
        : null,
    [graph, support?.conclusions, t, traceMode],
  );

  return (
    <div className="mt-5 space-y-4 border-t border-slate-200/80 pt-5">
      {shouldRenderMermaidGraph ? (
        <section className="rounded-2xl border border-slate-200 bg-[linear-gradient(135deg,rgba(255,246,239,0.8),rgba(248,250,252,0.98))] p-4 shadow-sm">
          <div className="mb-3 text-[11px] font-semibold tracking-[0.18em] text-slate-500 uppercase">
            {t('graph_title')}
          </div>
          <div className="rounded-2xl border border-white/90 bg-white/90 p-5">
            <ChartMermaid>{embeddedMermaid!}</ChartMermaid>
          </div>
        </section>
      ) : null}

      {traceMode === 'time' ? (
        <>
          <section className="space-y-3">
            <div className="text-lg font-semibold text-slate-900">
              {t('event_table_title')}
            </div>
            {supportLoading && !timeTimelineItems.length ? (
              <div className="text-sm text-slate-500">{t('graph_loading')}</div>
            ) : timeTimelineItems.length ? (
              <div className="space-y-0">
                {timeTimelineItems.map((item) => (
                  <button
                    key={item.id}
                    type="button"
                    onClick={() => {
                      if (!item.source_row_ids.length) {
                        return;
                      }
                      onSourcesOpenChange(true);
                      selectRows(item.source_row_ids);
                    }}
                    className="grid w-full grid-cols-[150px_minmax(0,220px)_1fr] gap-4 border-b border-slate-200/80 px-2 py-4 text-left transition-colors last:border-b-0 hover:bg-slate-50/70"
                  >
                    <div className="text-xs font-semibold tracking-[0.08em] text-slate-500 uppercase">
                      {normalizeTimelineTimeLabel(item.rendered_time_label)}
                    </div>
                    <div className="text-sm font-semibold text-slate-900">
                      {item.title}
                    </div>
                    <p className="text-sm leading-6 text-slate-600">
                      {item.statement}
                    </p>
                  </button>
                ))}
              </div>
            ) : (
              <div className="text-sm text-slate-500">{t('graph_empty')}</div>
            )}
          </section>

          <section className="space-y-3">
            <div className="text-lg font-semibold text-slate-900">
              {t('event_gantt_title')}
            </div>
            {timeGanttMermaid ? (
              <ChartMermaid>{timeGanttMermaid}</ChartMermaid>
            ) : (
              <div className="text-sm text-slate-500">{emptyGraphMessage}</div>
            )}
          </section>
        </>
      ) : shouldRenderStructuredGraph ? (
        <MessageAnswerGraph
          graph={graph}
          conclusions={support?.conclusions || []}
          loading={supportLoading}
          emptyMessage={emptyGraphMessage}
          activeNodeIds={activeNodeIds}
          activeEdgeIds={activeEdgeIds}
          onSelectGraphElements={({ rowIds, nodeIds, edgeIds }) => {
            onSourcesOpenChange(true);
            setActiveRowIds(rowIds);
            setActiveNodeIds(nodeIds);
            setActiveEdgeIds(edgeIds);
            if (rowIds.length) {
              setExpandedRowIds((current) =>
                Array.from(new Set([...current, ...rowIds])),
              );
            }
          }}
          title={t('entity_graph_title')}
        />
      ) : null}

      {rows.length ? (
        <Drawer
          direction="right"
          handleOnly={true}
          open={sourcesOpen}
          onOpenChange={onSourcesOpenChange}
        >
          <DrawerContent className="flex sm:min-w-xl md:min-w-2xl lg:min-w-3xl">
            <DrawerHeader className="border-b">
              <div className="flex items-center gap-2">
                <DrawerTitle className="font-bold">
                  {t('evidence_title')}
                </DrawerTitle>
                <Badge variant="secondary" className="rounded-full">
                  {rows.length}
                </Badge>
              </div>
              <DrawerDescription>{t('source_list_hint')}</DrawerDescription>
            </DrawerHeader>
            <div className="overflow-auto px-4 pb-4 select-text">
            <MessageReferenceCard
              rows={rows}
              activeRowIds={activeRowIds}
              expandedRowIds={expandedRowIds}
              onActivateRow={(rowId) => {
                onSourcesOpenChange(true);
                selectRows([rowId]);
              }}
              onToggleRow={(rowId) =>
                setExpandedRowIds((current) =>
                  current.includes(rowId)
                    ? current.filter((id) => id !== rowId)
                    : [...current, rowId],
                )
              }
              conclusionMap={conclusionMap}
              showHeader={false}
            />
            </div>
          </DrawerContent>
        </Drawer>
      ) : null}
    </div>
  );
};
