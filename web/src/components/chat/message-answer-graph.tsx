'use client';

import { ChartMermaid } from '@/components/chart-mermaid';
import {
  createKnowledgeGraphColorScale,
  getKnowledgeGraphLinkColor,
  getKnowledgeGraphLinkDirectionalParticleWidth,
  getKnowledgeGraphLinkWidth,
  paintKnowledgeGraphNodePointerArea,
  renderKnowledgeGraphNode,
  resolveKnowledgeGraphNodeId,
} from '@/components/knowledge-graph/force-graph-renderer';
import { Badge } from '@/components/ui/badge';
import { useTranslations } from 'next-intl';
import { useTheme } from 'next-themes';
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
  TraceConclusion,
  TraceGraphGroup,
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

const getLinkEndpointId = (endpoint: unknown): string => {
  return resolveKnowledgeGraphNodeId(
    endpoint as string | number | { id?: string | number } | undefined,
  ) || '';
};

const getGroupEdgeIds = (
  graph: AnswerGraphPayload,
  group: TraceGraphGroup,
): string[] =>
  graph.edges
    .filter((edge) => {
      const linkedRows = getLinkedRowIds(edge.properties);
      if (linkedRows.some((rowId) => group.row_ids.includes(rowId))) {
        return true;
      }
      const sourceId = getLinkEndpointId(edge.source);
      const targetId = getLinkEndpointId(edge.target);
      return (
        group.node_ids.includes(sourceId) && group.node_ids.includes(targetId)
      );
    })
    .map((edge) => edge.id);

const getGroupNodeLabels = (
  group: TraceGraphGroup,
  nodeLookup: Map<string, AnswerGraphNode>,
): string[] =>
  group.node_ids
    .map((nodeId) => nodeLookup.get(nodeId))
    .filter((node): node is AnswerGraphNode => Boolean(node))
    .map((node) => getNodeDisplayName(node))
    .filter(Boolean)
    .slice(0, 6);

const parseTimeLabel = (label?: string | null) => {
  const value = (label || '').trim();
  if (!value) {
    return null;
  }
  const rangeMatch = value.match(
    /^(\d{4}-\d{2}-\d{2})\/(\d{4}-\d{2}-\d{2})$/,
  );
  if (rangeMatch) {
    return {
      iso: rangeMatch[1],
      endIso: rangeMatch[2],
      precision: 'range' as const,
    };
  }
  const fullMatch = value.match(/(\d{4})[-年/](\d{1,2})[-月/](\d{1,2})/);
  if (fullMatch) {
    const [, year, month, day] = fullMatch;
    return {
      iso: `${year}-${month.padStart(2, '0')}-${day.padStart(2, '0')}`,
      precision: 'day' as const,
    };
  }
  const monthMatch = value.match(/(\d{4})[-年/](\d{1,2})|month:(\d{2})/);
  if (monthMatch) {
    const year = monthMatch[1] || '2026';
    const month = (monthMatch[2] || monthMatch[3] || '01').padStart(2, '0');
    return {
      iso: `${year}-${month}-01`,
      precision: 'month' as const,
    };
  }
  const yearMatch = value.match(/(\d{4})/);
  if (yearMatch) {
    return {
      iso: `${yearMatch[1]}-01-01`,
      precision: 'year' as const,
    };
  }
  return null;
};

export const extractRenderableTimeLabel = (conclusion: {
  time_label?: string | null;
  statement?: string | null;
  title?: string | null;
}) => {
  const currentYear = new Date().getFullYear();
  const toValidIso = (year: string, month: string, day: string) => {
    const y = Number(year);
    const m = Number(month);
    const d = Number(day);
    if (!Number.isFinite(y) || !Number.isFinite(m) || !Number.isFinite(d)) {
      return null;
    }
    if (y < 2000 || y > 2100 || m < 1 || m > 12 || d < 1 || d > 31) {
      return null;
    }
    return `${y.toString().padStart(4, '0')}-${m.toString().padStart(2, '0')}-${d.toString().padStart(2, '0')}`;
  };
  const candidates = [
    conclusion.time_label || '',
    conclusion.statement || '',
    conclusion.title || '',
  ];

  for (const candidate of candidates) {
    const value = (candidate || '').trim();
    if (!value) {
      continue;
    }

    const rangeMatch = value.match(
      /(\d{4})\D+(\d{1,2})\D+(\d{1,2})\D*(?:至|到|~|～|—|–|-)\D*(?:(\d{1,2})\D+)?(\d{1,2})/,
    );
    if (rangeMatch) {
      const [, year, startMonth, startDay, endMonth, endDay] = rangeMatch;
      const startIso = toValidIso(year, startMonth, startDay);
      const endIso = toValidIso(year, endMonth || startMonth, endDay);
      if (startIso && endIso) {
        return `${startIso}/${endIso}`;
      }
    }

    const fullMatch = value.match(/(\d{4})\D+(\d{1,2})\D+(\d{1,2})/);
    if (fullMatch) {
      const [, year, month, day] = fullMatch;
      const iso = toValidIso(year, month, day);
      if (iso) {
        return iso;
      }
    }

    const yearMonthMatch = value.match(/(\d{4})\D+(\d{1,2})(?!\d)/);
    if (yearMonthMatch) {
      const [, year, month] = yearMonthMatch;
      const y = Number(year);
      const m = Number(month);
      if (y >= 2000 && y <= 2100 && m >= 1 && m <= 12) {
        return `${year}-${month.padStart(2, '0')}`;
      }
    }

    const partialRangeMatch = value.match(
      /(?<!\d)(\d{1,2})\D+(\d{1,2})\D*(?:至|到|~|～|—|–|-)\D*(?:(\d{1,2})\D+)?(\d{1,2})(?!\d)/,
    );
    if (partialRangeMatch) {
      const [, startMonth, startDay, endMonth, endDay] = partialRangeMatch;
      const startIso = toValidIso(String(currentYear), startMonth, startDay);
      const endIso = toValidIso(
        String(currentYear),
        endMonth || startMonth,
        endDay,
      );
      if (startIso && endIso) {
        return `${startIso}/${endIso}`;
      }
    }

    const partialDateMatch = value.match(/(?<!\d)(\d{1,2})\D+(\d{1,2})(?!\d)/);
    if (partialDateMatch) {
      const [, month, day] = partialDateMatch;
      const iso = toValidIso(String(currentYear), month, day);
      if (iso) {
        return iso;
      }
    }
  }

  return null;
};

const getDurationFromTimeLabel = (
  parsed: NonNullable<ReturnType<typeof parseTimeLabel>>,
) => {
  if (parsed.precision === 'range' && parsed.endIso) {
    const start = new Date(`${parsed.iso}T00:00:00Z`);
    const end = new Date(`${parsed.endIso}T00:00:00Z`);
    const diff = Math.max(
      1,
      Math.floor((end.getTime() - start.getTime()) / 86400000) + 1,
    );
    return `${diff}d`;
  }
  if (parsed.precision === 'day') {
    return '1d';
  }
  if (parsed.precision === 'month') {
    const [, year, month] = parsed.iso.split('-').map(Number);
    const daysInMonth = new Date(Date.UTC(year, month, 0)).getUTCDate();
    return `${daysInMonth}d`;
  }
  return '365d';
};

const getDurationDaysFromTimeLabel = (
  parsed: NonNullable<ReturnType<typeof parseTimeLabel>>,
) => {
  if (parsed.precision === 'range' && parsed.endIso) {
    const start = new Date(`${parsed.iso}T00:00:00Z`);
    const end = new Date(`${parsed.endIso}T00:00:00Z`);
    return Math.max(
      1,
      Math.floor((end.getTime() - start.getTime()) / 86400000) + 1,
    );
  }
  if (parsed.precision === 'day') {
    return 1;
  }
  if (parsed.precision === 'month') {
    return 31;
  }
  return 365;
};

const isRenderableGanttLabel = (value: string) => {
  const normalized = (value || '').trim().toLowerCase();
  if (!normalized) {
    return false;
  }
  const blocked = [
    'imported from',
    'triple trace acceptance',
    '条目列表',
    'hierarchy',
    'http',
    'www.',
    '文档',
    '来源',
    '法广中文中国',
  ];
  return !blocked.some((part) => normalized.includes(part));
};

const toMermaidTaskLabel = (value: string) =>
  value
    .replace(/https?:\/\/\S+/gi, ' ')
    .replace(/[*_`#[\]()<>{}|:;,.!?/\\'"“”‘’+-]+/g, ' ')
    .replace(/\s+/g, ' ')
    .trim()
    .slice(0, 36) || 'Task';

const getConclusionTaskLabel = (conclusion: TraceConclusion) => {
  const cleanedTitle = (conclusion.title || '').replace(/\*\*/g, '').trim();
  if (cleanedTitle) {
    return toMermaidTaskLabel(cleanedTitle);
  }

  const statement = (conclusion.statement || '')
    .replace(/\*\*/g, '')
    .replace(/^(?:根据|基于)[^，。:：]{0,40}[，。:：]\s*/u, '')
    .replace(/^以下按时间顺序梳理(?:关键)?事件[：:]\s*/u, '')
    .replace(/^.*?围绕/u, '')
    .replace(/展开.*$/u, '')
    .split(/[。；;\n]/u)[0]
    ?.trim();

  if (statement) {
    return toMermaidTaskLabel(statement);
  }

  return toMermaidTaskLabel(conclusion.title || 'Task');
};

export const buildGanttMermaid = ({
  graph,
  conclusions,
  graphTitle,
  focusLabel,
}: {
  graph: AnswerGraphPayload;
  conclusions: TraceConclusion[];
  graphTitle: string;
  focusLabel: string;
}) => {
  const relevantConclusions = conclusions.filter(
    (conclusion) => conclusion.time_label,
  );
  if (!relevantConclusions.length) {
    return null;
  }

  const tasks = relevantConclusions
    .map((conclusion, index) => {
      const normalizedTimeLabel = extractRenderableTimeLabel(conclusion);
      const parsed = parseTimeLabel(normalizedTimeLabel);
      if (!parsed) {
        return null;
      }
      const durationDays = getDurationDaysFromTimeLabel(parsed);
      const hasSpecificTime =
        parsed.precision === 'day' ||
        (parsed.precision === 'range' && durationDays <= 5);
      if (!hasSpecificTime) {
        return null;
      }
      const label = getConclusionTaskLabel(conclusion);
      if (!isRenderableGanttLabel(label)) {
        return null;
      }
      return {
        section:
          graph.layout === 'location'
            ? graph.focus_label || conclusion.place_label || focusLabel
            : graphTitle,
        label,
        id: `task_${index + 1}`,
        start: parsed.iso,
        duration: getDurationFromTimeLabel(parsed),
      };
    })
    .filter((item): item is NonNullable<typeof item> => Boolean(item))
    .sort((left, right) => left.start.localeCompare(right.start));

  if (!tasks.length) {
    return null;
  }

  const lines = [
    'gantt',
    'dateFormat YYYY-MM-DD',
    'axisFormat %Y-%m-%d',
    `title ${graphTitle}`,
  ];

  let currentSection = '';
  for (const task of tasks) {
    if (task.section !== currentSection) {
      currentSection = task.section;
      lines.push(`section ${task.section}`);
    }
    lines.push(`${task.label} : ${task.id}, ${task.start}, ${task.duration}`);
  }

  return lines.join('\n');
};

export const MessageAnswerGraph = ({
  graph,
  conclusions,
  loading,
  emptyMessage,
  activeNodeIds,
  activeEdgeIds,
  onSelectGraphElements,
  title,
}: {
  graph: AnswerGraphPayload | null;
  conclusions?: TraceConclusion[];
  loading: boolean;
  emptyMessage: string;
  activeNodeIds: string[];
  activeEdgeIds: string[];
  onSelectGraphElements: (selection: {
    rowIds: string[];
    nodeIds: string[];
    edgeIds: string[];
  }) => void;
  title?: string;
}) => {
  const t = useTranslations('page_chat.answer_support');
  const { resolvedTheme } = useTheme();
  const graphTitle = title || t('graph_title');
  const containerRef = useRef<HTMLDivElement>(null);
  const graphRef = useRef<ForceGraphMethods | undefined>(undefined);
  const [dimensions, setDimensions] = useState({ width: 0, height: 0 });

  const activeNodeSet = useMemo(() => new Set(activeNodeIds), [activeNodeIds]);
  const activeEdgeSet = useMemo(() => new Set(activeEdgeIds), [activeEdgeIds]);
  const colorScale = useMemo(() => createKnowledgeGraphColorScale(), []);
  const nodeLookup = useMemo(
    () =>
      new Map(
        (graph?.nodes || []).map((node) => [node.id, node] as const),
      ),
    [graph?.nodes],
  );
  const groupedLayout =
    Boolean(graph?.groups?.length) && graph?.layout && graph.layout !== 'force';
  const shouldShowFocusBadge = useMemo(() => {
    const focus = (graph?.focus_label || '').trim();
    if (!focus) {
      return false;
    }
    if (graph?.layout === 'timeline' && /^month:\d{2}$/i.test(focus)) {
      return false;
    }
    return true;
  }, [graph?.focus_label, graph?.layout]);
  const ganttMermaid = useMemo(
    () =>
      graph && groupedLayout && (graph.layout === 'timeline' || graph.layout === 'location')
        ? buildGanttMermaid({
            graph,
            conclusions: conclusions || [],
            graphTitle,
            focusLabel: t('focus_label'),
          })
        : null,
    [conclusions, graph, graphTitle, groupedLayout, t],
  );

  const graphData = useMemo(() => {
    if (!graph || graph.is_empty || groupedLayout) {
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
        value: Math.max(degreeById.get(node.id) || 0, 10),
      })),
      links: graph.edges,
    };
  }, [graph, groupedLayout]);

  const entityColorMap = useMemo(() => {
    const result = new Map<string, string>();
    (graphData?.nodes || []).forEach((node) => {
      const entityType = getEntityType(node);
      if (!result.has(entityType)) {
        result.set(entityType, colorScale(entityType));
      }
    });
    return result;
  }, [colorScale, graphData?.nodes]);

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

  if (!graph || (!groupedLayout && (graph.is_empty || !graphData))) {
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

  const renderGroupedLayout = () => {
    const groups = graph.groups || [];

    if (graph.layout === 'timeline' && ganttMermaid) {
      return (
        <div className="rounded-2xl border border-white/90 bg-white/90 p-5">
          <ChartMermaid>{ganttMermaid}</ChartMermaid>
        </div>
      );
    }

    if (graph.layout === 'location' && ganttMermaid) {
      return (
        <div className="space-y-4 rounded-2xl border border-white/90 bg-white/90 p-5">
          <ChartMermaid>{ganttMermaid}</ChartMermaid>
          <div className="grid gap-3 md:grid-cols-2">
            {groups.map((group) => {
              const nodeLabels = getGroupNodeLabels(group, nodeLookup);
              return (
                <button
                  key={group.id}
                  type="button"
                  onClick={() =>
                    onSelectGraphElements({
                      rowIds: group.row_ids,
                      nodeIds: group.node_ids,
                      edgeIds: getGroupEdgeIds(graph, group),
                    })
                  }
                  className="rounded-2xl border border-slate-200 px-4 py-4 text-left transition-colors hover:bg-slate-50"
                >
                  <div className="flex items-center justify-between gap-3">
                    <div className="text-sm font-semibold text-slate-900">
                      {group.label}
                    </div>
                    <Badge variant="secondary" className="rounded-full">
                      {group.row_ids.length}
                    </Badge>
                  </div>
                  {nodeLabels.length ? (
                    <div className="mt-3 flex flex-wrap gap-1.5">
                      {nodeLabels.map((label) => (
                        <Badge
                          key={`${group.id}-${label}`}
                          variant="outline"
                          className="rounded-full"
                        >
                          {label}
                        </Badge>
                      ))}
                    </div>
                  ) : null}
                </button>
              );
            })}
          </div>
        </div>
      );
    }

    return (
      <div className="rounded-2xl border border-white/90 bg-white/90 p-5">
        <div className="flex flex-col items-center justify-center rounded-2xl bg-[radial-gradient(circle_at_top,rgba(14,165,233,0.12),rgba(255,255,255,0.95))] px-6 py-8 text-center">
          <div className="text-[11px] font-semibold tracking-[0.18em] text-slate-500 uppercase">
            {t('focus_label')}
          </div>
          <div className="mt-2 text-lg font-semibold text-slate-900">
            {graph.focus_label || groups[0]?.label || graphTitle}
          </div>
          <div className="mt-5 flex flex-wrap justify-center gap-2">
            {groups.map((group) => (
              <button
                key={group.id}
                type="button"
                onClick={() =>
                  onSelectGraphElements({
                    rowIds: group.row_ids,
                    nodeIds: group.node_ids,
                    edgeIds: getGroupEdgeIds(graph, group),
                  })
                }
                className="rounded-full border border-slate-200 bg-white px-3 py-1.5 text-sm text-slate-700 transition-colors hover:bg-slate-50"
              >
                {group.label}
              </button>
            ))}
          </div>
        </div>
      </div>
    );
  };

  return (
    <section className="rounded-2xl border border-slate-200 bg-[linear-gradient(135deg,rgba(255,246,239,0.8),rgba(248,250,252,0.98))] p-4 shadow-sm">
      <div className="mb-3 flex items-start justify-between gap-3">
        <div>
          <div className="text-[11px] font-semibold tracking-[0.18em] text-slate-500 uppercase">
            {t('graph_label')}
          </div>
          <div className="mt-1 flex flex-wrap items-center gap-2 text-sm font-semibold text-slate-900">
            <span>{graphTitle}</span>
            {shouldShowFocusBadge ? (
              <Badge variant="outline" className="rounded-full">
                {graph.focus_label}
              </Badge>
            ) : null}
          </div>
        </div>
        {!groupedLayout ? (
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
        ) : null}
      </div>

      {groupedLayout ? (
        renderGroupedLayout()
      ) : (
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
              renderKnowledgeGraphNode({
                node: node as GraphNodeRender,
                ctx,
                colorScale,
                resolvedTheme,
                isNodeHighlighted: (currentNode) =>
                  activeNodeSet.size === 0 || activeNodeSet.has(currentNode.id),
              });
            }}
            nodePointerAreaPaint={(node, color, ctx) => {
              paintKnowledgeGraphNodePointerArea({
                node: node as GraphNodeRender,
                paintColor: color,
                ctx,
              });
            }}
            linkColor={(link) =>
              getKnowledgeGraphLinkColor({
                link: link as GraphEdgeRender,
                resolvedTheme,
                isLinkHighlighted: (currentLink) =>
                  activeEdgeSet.size === 0 || activeEdgeSet.has(currentLink.id),
              })
            }
            linkWidth={(link) =>
              getKnowledgeGraphLinkWidth(
                link as GraphEdgeRender,
                (currentLink) =>
                  activeEdgeSet.size === 0 || activeEdgeSet.has(currentLink.id),
              )
            }
            linkDirectionalParticles={2}
            linkDirectionalParticleWidth={(link) =>
              getKnowledgeGraphLinkDirectionalParticleWidth(
                link as GraphEdgeRender,
                (currentLink) =>
                  activeEdgeSet.size === 0 || activeEdgeSet.has(currentLink.id),
              )
            }
          />
        </div>
      )}
    </section>
  );
};
