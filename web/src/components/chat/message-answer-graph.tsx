'use client';

import { Badge } from '@/components/ui/badge';
import { useTranslations } from 'next-intl';
import dynamic from 'next/dynamic';
import { useEffect, useMemo, useRef, useState } from 'react';
import type {
  ForceGraphMethods,
  LinkObject,
  NodeObject,
} from 'react-force-graph-2d';
import {
  AnswerGraphEdge,
  AnswerGraphNode,
  AnswerGraphPayload,
  getEntityType,
  getLinkedRowIds,
  getNodeDisplayName,
} from './message-answer-support.types';

type GraphNodeRender = AnswerGraphNode &
  NodeObject<AnswerGraphNode> & { value?: number };
type GraphEdgeRender = AnswerGraphEdge &
  LinkObject<AnswerGraphNode, AnswerGraphEdge>;

const ForceGraph2D = dynamic(
  () => import('react-force-graph-2d').then((mod) => mod.default),
  { ssr: false },
);

const ENTITY_COLORS = [
  '#FF6B35',
  '#004E89',
  '#1A936F',
  '#C5283D',
  '#E9724C',
  '#277DA1',
  '#7B2CBF',
  '#3A86FF',
];

const isNodeEndpoint = (
  endpoint: unknown,
): endpoint is { id?: string | number } =>
  Boolean(
    endpoint &&
      typeof endpoint === 'object' &&
      'id' in endpoint &&
      (typeof endpoint.id === 'string' || typeof endpoint.id === 'number'),
  );

const getLinkEndpointId = (endpoint: unknown): string => {
  if (typeof endpoint === 'string') {
    return endpoint;
  }
  if (typeof endpoint === 'number') {
    return String(endpoint);
  }
  if (isNodeEndpoint(endpoint)) {
    return String(endpoint.id || '');
  }
  return '';
};

export const MessageAnswerGraph = ({
  graph,
  loading,
  emptyMessage,
  activeNodeIds,
  activeEdgeIds,
  onSelectGraphElements,
}: {
  graph: AnswerGraphPayload | null;
  loading: boolean;
  emptyMessage: string;
  activeNodeIds: string[];
  activeEdgeIds: string[];
  onSelectGraphElements: (selection: {
    rowIds: string[];
    nodeIds: string[];
    edgeIds: string[];
  }) => void;
}) => {
  const t = useTranslations('page_chat.answer_support');
  const containerRef = useRef<HTMLDivElement>(null);
  const graphRef = useRef<ForceGraphMethods | undefined>(undefined);
  const [dimensions, setDimensions] = useState({ width: 0, height: 0 });

  const activeNodeSet = useMemo(() => new Set(activeNodeIds), [activeNodeIds]);
  const activeEdgeSet = useMemo(() => new Set(activeEdgeIds), [activeEdgeIds]);

  const graphData = useMemo(() => {
    if (!graph || graph.is_empty) {
      return undefined;
    }

    const degreeById = new Map<string, number>();
    graph.edges.forEach((edge) => {
      degreeById.set(edge.source, (degreeById.get(edge.source) || 0) + 1);
      degreeById.set(edge.target, (degreeById.get(edge.target) || 0) + 1);
    });

    return {
      nodes: graph.nodes.map((node) => ({
        ...node,
        value: Math.max(7, Math.min(18, (degreeById.get(node.id) || 0) + 7)),
      })),
      links: graph.edges,
    };
  }, [graph]);

  const entityColorMap = useMemo(() => {
    const result = new Map<string, string>();
    (graphData?.nodes || []).forEach((node, index) => {
      const entityType = getEntityType(node);
      if (!result.has(entityType)) {
        result.set(
          entityType,
          ENTITY_COLORS[index % ENTITY_COLORS.length] || ENTITY_COLORS[0],
        );
      }
    });
    return result;
  }, [graphData?.nodes]);

  const legendItems = useMemo(
    () =>
      Array.from(entityColorMap.entries()).map(([name, color]) => ({
        name,
        color,
      })),
    [entityColorMap],
  );

  useEffect(() => {
    const resize = () => {
      const container = containerRef.current;
      if (!container) {
        return;
      }
      setDimensions({
        width: Math.max(container.offsetWidth - 2, 0),
        height: 320,
      });
    };

    resize();
    const observer = new ResizeObserver(resize);
    if (containerRef.current) {
      observer.observe(containerRef.current);
    }
    window.addEventListener('resize', resize);
    return () => {
      observer.disconnect();
      window.removeEventListener('resize', resize);
    };
  }, []);

  if (loading) {
    return (
      <section className="rounded-2xl border border-slate-200 bg-[linear-gradient(135deg,rgba(255,246,239,0.75),rgba(248,250,252,0.95))] p-4 shadow-sm">
        <div className="text-[11px] font-semibold tracking-[0.18em] text-slate-500 uppercase">
          {t('graph_label')}
        </div>
        <div className="mt-3 animate-pulse rounded-2xl border border-dashed border-slate-200 bg-white/70 px-4 py-12 text-center text-sm text-slate-500">
          {t('graph_loading')}
        </div>
      </section>
    );
  }

  if (!graph || graph.is_empty || !graphData) {
    return (
      <section className="rounded-2xl border border-slate-200 bg-[linear-gradient(135deg,rgba(255,246,239,0.75),rgba(248,250,252,0.95))] p-4 shadow-sm">
        <div className="text-[11px] font-semibold tracking-[0.18em] text-slate-500 uppercase">
          {t('graph_label')}
        </div>
        <div className="mt-3 rounded-2xl border border-dashed border-slate-200 bg-white/80 px-4 py-10 text-center text-sm text-slate-500">
          {emptyMessage}
        </div>
      </section>
    );
  }

  return (
    <section className="rounded-2xl border border-slate-200 bg-[linear-gradient(135deg,rgba(255,246,239,0.8),rgba(248,250,252,0.98))] p-4 shadow-sm">
      <div className="mb-3 flex items-start justify-between gap-3">
        <div>
          <div className="text-[11px] font-semibold tracking-[0.18em] text-slate-500 uppercase">
            {t('graph_label')}
          </div>
          <div className="mt-1 text-sm font-semibold text-slate-900">
            {t('graph_title')}
          </div>
        </div>
        <div className="flex flex-wrap justify-end gap-1.5">
          {legendItems.map((item) => (
            <Badge
              key={item.name}
              variant="secondary"
              className="rounded-full bg-white/90 text-slate-700"
            >
              <span
                className="mr-1 inline-block size-2 rounded-full"
                style={{ backgroundColor: item.color }}
              />
              {item.name}
            </Badge>
          ))}
        </div>
      </div>

      <div
        ref={containerRef}
        className="relative overflow-hidden rounded-2xl border border-white/90 bg-white/90"
      >
        <ForceGraph2D
          ref={graphRef}
          graphData={graphData}
          width={dimensions.width}
          height={dimensions.height}
          nodeLabel={(node) => getNodeDisplayName(node as AnswerGraphNode)}
          onNodeClick={(node) => {
            const answerNode = node as GraphNodeRender;
            onSelectGraphElements({
              rowIds: getLinkedRowIds(answerNode.properties),
              nodeIds: [answerNode.id],
              edgeIds: [],
            });

            if (
              typeof answerNode.x === 'number' &&
              typeof answerNode.y === 'number'
            ) {
              graphRef.current?.centerAt(answerNode.x, answerNode.y, 400);
              graphRef.current?.zoom(2.2, 400);
            }
          }}
          onLinkClick={(link) => {
            const answerEdge = link as GraphEdgeRender;
            onSelectGraphElements({
              rowIds: getLinkedRowIds(answerEdge.properties),
              nodeIds: [
                getLinkEndpointId(answerEdge.source),
                getLinkEndpointId(answerEdge.target),
              ].filter(Boolean),
              edgeIds: [answerEdge.id],
            });
          }}
          nodeCanvasObject={(node, ctx) => {
            const answerNode = node as GraphNodeRender;
            const x = answerNode.x || 0;
            const y = answerNode.y || 0;
            const radius = Number(answerNode.value || 8);
            const entityType = getEntityType(answerNode);
            const fillColor =
              entityColorMap.get(entityType) || ENTITY_COLORS[0];
            const isVisible =
              activeNodeSet.size === 0 || activeNodeSet.has(answerNode.id);
            const label = getNodeDisplayName(answerNode);
            const displayLabel =
              label.length > 10 ? `${label.slice(0, 10)}...` : label;

            ctx.beginPath();
            ctx.arc(x, y, radius, 0, 2 * Math.PI, false);
            ctx.fillStyle = isVisible ? fillColor : 'rgba(203,213,225,0.78)';
            ctx.fill();

            ctx.beginPath();
            ctx.arc(x, y, radius, 0, 2 * Math.PI, false);
            ctx.lineWidth = activeNodeSet.has(answerNode.id) ? 2 : 1;
            ctx.strokeStyle = activeNodeSet.has(answerNode.id)
              ? '#111827'
              : '#ffffff';
            ctx.stroke();

            ctx.font = '12px ui-sans-serif, system-ui';
            const textWidth = ctx.measureText(displayLabel).width;
            ctx.fillStyle = 'rgba(255,255,255,0.92)';
            ctx.fillRect(
              x - textWidth / 2 - 5,
              y + radius + 6,
              textWidth + 10,
              18,
            );
            ctx.fillStyle = '#0f172a';
            ctx.fillText(displayLabel, x - textWidth / 2, y + radius + 19);
          }}
          nodePointerAreaPaint={(node, color, ctx) => {
            const answerNode = node as GraphNodeRender;
            ctx.fillStyle = color;
            ctx.beginPath();
            ctx.arc(
              answerNode.x || 0,
              answerNode.y || 0,
              Number(answerNode.value || 8) + 3,
              0,
              2 * Math.PI,
              false,
            );
            ctx.fill();
          }}
          linkColor={(link) => {
            const answerEdge = link as GraphEdgeRender;
            return activeEdgeSet.size === 0 || activeEdgeSet.has(answerEdge.id)
              ? '#334155'
              : 'rgba(203,213,225,0.9)';
          }}
          linkWidth={(link) => {
            const answerEdge = link as GraphEdgeRender;
            return activeEdgeSet.has(answerEdge.id) ? 2.8 : 1.2;
          }}
          linkDirectionalParticles={2}
          linkDirectionalParticleWidth={(link) => {
            const answerEdge = link as GraphEdgeRender;
            return activeEdgeSet.has(answerEdge.id) ? 2.8 : 0;
          }}
        />
      </div>
    </section>
  );
};
