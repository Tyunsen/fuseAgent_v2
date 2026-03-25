'use client';

import { Reference } from '@/api';
import { useTranslations } from 'next-intl';
import { useEffect, useMemo, useState } from 'react';
import { MessageAnswerGraph } from './message-answer-graph';
import {
  AnswerGraphPayload,
  buildAnswerGraphReferences,
  getLinkedRowIds,
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

export const MessageAnswerSupport = ({
  references,
}: {
  references: Reference[];
}) => {
  const t = useTranslations('page_chat.answer_support');
  const rows = useMemo(() => prepareReferenceRows(references), [references]);
  const collectionId = useMemo(
    () => rows.find((row) => row.collectionId)?.collectionId,
    [rows],
  );
  const graphRequest = useMemo(() => buildAnswerGraphReferences(rows), [rows]);
  const requestKey = useMemo(
    () => JSON.stringify(graphRequest),
    [graphRequest],
  );

  const [graph, setGraph] = useState<AnswerGraphPayload | null>(null);
  const [graphLoading, setGraphLoading] = useState(false);
  const [activeRowIds, setActiveRowIds] = useState<string[]>([]);
  const [activeNodeIds, setActiveNodeIds] = useState<string[]>([]);
  const [activeEdgeIds, setActiveEdgeIds] = useState<string[]>([]);
  const [expandedRowIds, setExpandedRowIds] = useState<string[]>([]);

  useEffect(() => {
    setActiveRowIds([]);
    setActiveNodeIds([]);
    setActiveEdgeIds([]);
    setExpandedRowIds([]);
  }, [requestKey]);

  useEffect(() => {
    if (!rows.length) {
      setGraph(null);
      return;
    }

    if (!collectionId) {
      setGraph({
        nodes: [],
        edges: [],
        linked_row_ids: [],
        is_empty: true,
        empty_reason: 'graph_linking_unavailable',
      });
      return;
    }

    const controller = new AbortController();

    const loadGraph = async () => {
      setGraphLoading(true);
      try {
        const response = await fetch(
          `${process.env.NEXT_PUBLIC_BASE_PATH || ''}/api/v1/collections/${collectionId}/answer-graph`,
          {
            method: 'POST',
            headers: {
              'Content-Type': 'application/json',
            },
            body: JSON.stringify({
              references: graphRequest,
              max_nodes: 18,
            }),
            signal: controller.signal,
          },
        );

        if (!response.ok) {
          setGraph({
            nodes: [],
            edges: [],
            linked_row_ids: [],
            is_empty: true,
            empty_reason: 'graph_unavailable',
          });
          return;
        }

        const data = (await response.json()) as AnswerGraphPayload;
        setGraph(data);
      } catch {
        if (!controller.signal.aborted) {
          setGraph({
            nodes: [],
            edges: [],
            linked_row_ids: [],
            is_empty: true,
            empty_reason: 'graph_unavailable',
          });
        }
      } finally {
        if (!controller.signal.aborted) {
          setGraphLoading(false);
        }
      }
    };

    void loadGraph();
    return () => controller.abort();
  }, [collectionId, graphRequest, requestKey, rows.length]);

  const handleActivateRow = (rowId: string) => {
    setActiveRowIds([rowId]);

    if (!graph || graph.is_empty) {
      setActiveNodeIds([]);
      setActiveEdgeIds([]);
      return;
    }

    setActiveNodeIds(
      graph.nodes
        .filter((node) => getLinkedRowIds(node.properties).includes(rowId))
        .map((node) => node.id),
    );
    setActiveEdgeIds(
      graph.edges
        .filter((edge) => getLinkedRowIds(edge.properties).includes(rowId))
        .map((edge) => edge.id),
    );
  };

  const handleToggleRow = (rowId: string) => {
    setExpandedRowIds((current) =>
      current.includes(rowId)
        ? current.filter((id) => id !== rowId)
        : [...current, rowId],
    );
  };

  const handleSelectGraphElements = ({
    rowIds,
    nodeIds,
    edgeIds,
  }: {
    rowIds: string[];
    nodeIds: string[];
    edgeIds: string[];
  }) => {
    setActiveRowIds(rowIds);
    setActiveNodeIds(nodeIds);
    setActiveEdgeIds(edgeIds);

    if (rowIds.length) {
      setExpandedRowIds((current) =>
        Array.from(new Set([...current, ...rowIds])),
      );
    }
  };

  if (!rows.length) {
    return null;
  }

  const emptyGraphMessage = isEmptyGraphReason(graph?.empty_reason)
    ? t(EMPTY_GRAPH_MESSAGE_KEYS[graph.empty_reason])
    : t('graph_empty');

  return (
    <div className="mt-5 space-y-4 border-t border-slate-200/80 pt-5">
      <MessageAnswerGraph
        graph={graph}
        loading={graphLoading}
        emptyMessage={emptyGraphMessage}
        activeNodeIds={activeNodeIds}
        activeEdgeIds={activeEdgeIds}
        onSelectGraphElements={handleSelectGraphElements}
      />
      <MessageReferenceCard
        rows={rows}
        activeRowIds={activeRowIds}
        expandedRowIds={expandedRowIds}
        onActivateRow={handleActivateRow}
        onToggleRow={handleToggleRow}
      />
    </div>
  );
};
