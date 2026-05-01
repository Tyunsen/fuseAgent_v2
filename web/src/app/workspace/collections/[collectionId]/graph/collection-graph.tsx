'use client';

import {
  GraphEdge,
  GraphNode,
  KnowledgeGraph,
  MergeSuggestionsResponse,
} from '@/api';
import { useCollectionContext } from '@/components/providers/collection-provider';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Card } from '@/components/ui/card';
import {
  Command,
  CommandEmpty,
  CommandGroup,
  CommandInput,
  CommandItem,
  CommandList,
} from '@/components/ui/command';
import {
  Popover,
  PopoverContent,
  PopoverTrigger,
} from '@/components/ui/popover';
import { ScrollArea } from '@/components/ui/scroll-area';
import { Tooltip, TooltipContent } from '@/components/ui/tooltip';
import {
  createKnowledgeGraphColorScale,
  getKnowledgeGraphLinkColor,
  getKnowledgeGraphLinkDirectionalParticleWidth,
  getKnowledgeGraphLinkWidth,
  getKnowledgeGraphNodeDisplayName,
  paintKnowledgeGraphNodePointerArea,
  renderKnowledgeGraphNode,
  resolveKnowledgeGraphNodeId,
} from '@/components/knowledge-graph/force-graph-renderer';
import { apiClient } from '@/lib/api/client';
import { cn } from '@/lib/utils';
import { TooltipTrigger } from '@radix-ui/react-tooltip';
import Color from 'color';
import _ from 'lodash';
import {
  Check,
  ChevronDown,
  Focus,
  LoaderCircle,
  Maximize,
  Minimize,
  Network,
  RefreshCw,
  ScanSearch,
  Sparkles,
  Unplug,
} from 'lucide-react';
import { useLocale, useTranslations } from 'next-intl';
import { useTheme } from 'next-themes';
import dynamic from 'next/dynamic';
import { useParams } from 'next/navigation';
import { useCallback, useEffect, useMemo, useRef, useState } from 'react';
import {
  getCollectionGraphStatusCopy,
  isMirofishCollection,
} from '../../tools';
import { CollectionGraphInspector } from './collection-graph-inspector';
import { CollectionGraphNodeMerge } from './collection-graph-node-merge';

const ForceGraph2D = dynamic(
  () => import('react-force-graph-2d').then((r) => r),
  {
    ssr: false,
  },
);

type SelectedElement =
  | { type: 'node'; node: GraphNode }
  | { type: 'edge'; edge: GraphEdge }
  | null;

const getNodeDisplayName = getKnowledgeGraphNodeDisplayName;

export const CollectionGraph = ({
  marketplace = false,
}: {
  marketplace: boolean;
}) => {
  const params = useParams();
  const locale = useLocale();
  const rawPageGraph = useTranslations('page_graph');
  const { collection } = useCollectionContext();
  const { resolvedTheme } = useTheme();
  const pageGraphMessages = rawPageGraph as typeof rawPageGraph & {
    has: (key: string) => boolean;
  };
  const pageGraph = useCallback(
    (key: string, values?: Record<string, string | number>) =>
      rawPageGraph(key as never, values as never),
    [rawPageGraph],
  );
  const hasPageGraphKey = useCallback(
    (key: string) => pageGraphMessages.has(key as never),
    [pageGraphMessages],
  );
  const isMirofish = isMirofishCollection(collection.config);
  const graphStatusCopy = getCollectionGraphStatusCopy(collection.config, locale);

  const viewportRef = useRef<HTMLDivElement>(null);
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  const graphRef = useRef<any>(null);

  const [fullscreen, setFullscreen] = useState(false);
  const [loading, setLoading] = useState(false);
  const [graphData, setGraphData] = useState<{
    nodes: GraphNode[];
    links: GraphEdge[];
  }>();
  const [mergeSuggestion, setMergeSuggestion] =
    useState<MergeSuggestionsResponse>();
  const [mergeSuggestionOpen, setMergeSuggestionOpen] = useState(false);
  const [dimensions, setDimensions] = useState({ width: 0, height: 0 });
  const [activeEntities, setActiveEntities] = useState<string[]>([]);
  const [selected, setSelected] = useState<SelectedElement>(null);
  const [highlightNodes, setHighlightNodes] = useState<Set<GraphNode>>(new Set());
  const [highlightLinks, setHighlightLinks] = useState<Set<GraphEdge>>(new Set());
  const [hoverNodeId, setHoverNodeId] = useState<string>();
  const color = useMemo(() => createKnowledgeGraphColorScale(), []);
  const { NODE_MIN, NODE_MAX, NODE_FONT_MIN, NODE_FONT_MAX } = useMemo(
    () => ({
      NODE_MIN: 10,
      NODE_MAX: 30,
      NODE_FONT_MIN: 7,
      NODE_FONT_MAX: 13,
    }),
    [],
  );

  const getGraphData = useCallback(async () => {
    if (typeof params.collectionId !== 'string') {
      return;
    }

    setLoading(true);

    try {
      let data: KnowledgeGraph;

      if (!marketplace) {
        const res = await apiClient.graphApi.collectionsCollectionIdGraphsGet(
          {
            collectionId: params.collectionId,
          },
          {
            timeout: 1000 * 20,
          },
        );
        data = res.data;
      } else {
        const res =
          await apiClient.defaultApi.marketplaceCollectionsCollectionIdGraphGet(
            {
              collectionId: params.collectionId,
            },
            {
              timeout: 1000 * 20,
            },
          );
        data = res.data as KnowledgeGraph;
      }

      const inboundCounts = new Map<string, number>();
      const outboundCounts = new Map<string, number>();

      (data.edges || []).forEach((edge) => {
        inboundCounts.set(
          edge.target,
          (inboundCounts.get(edge.target) || 0) + 1,
        );
        outboundCounts.set(
          edge.source,
          (outboundCounts.get(edge.source) || 0) + 1,
        );
      });

      const nodes =
        data.nodes?.map((node) => {
          const inboundCount = inboundCounts.get(node.id) || 0;
          const outboundCount = outboundCounts.get(node.id) || 0;
          const degreeCount = inboundCount + outboundCount;

          return {
            ...node,
            properties: {
              ...node.properties,
              inbound_count: inboundCount,
              outbound_count: outboundCount,
              degree_count: degreeCount,
            },
            value: Math.max(inboundCount, outboundCount, 10),
          };
        }) || [];

      setGraphData({ nodes, links: data.edges || [] });
    } finally {
      setLoading(false);
    }
  }, [marketplace, params.collectionId]);

  const getMergeSuggestions = useCallback(async () => {
    if (typeof params.collectionId !== 'string' || marketplace || isMirofish) {
      setMergeSuggestion(undefined);
      return;
    }

    const suggestionRes =
      await apiClient.graphApi.collectionsCollectionIdGraphsMergeSuggestionsPost(
        {
          collectionId: params.collectionId,
        },
        {
          timeout: 1000 * 20,
        },
      );
    setMergeSuggestion(suggestionRes.data);
  }, [isMirofish, marketplace, params.collectionId]);

  const allEntities = useMemo(
    () => _.groupBy(graphData?.nodes || [], (node) => node.properties.entity_type),
    [graphData?.nodes],
  );
  const nodeById = useMemo(
    () => new Map((graphData?.nodes || []).map((node) => [node.id, node])),
    [graphData?.nodes],
  );
  const linksByNode = useMemo(() => {
    const adjacency = new Map<string, GraphEdge[]>();

    (graphData?.links || []).forEach((link) => {
      const sourceId = resolveKnowledgeGraphNodeId(link.source);
      const targetId = resolveKnowledgeGraphNodeId(link.target);

      if (sourceId) {
        adjacency.set(sourceId, [...(adjacency.get(sourceId) || []), link]);
      }
      if (targetId) {
        adjacency.set(targetId, [...(adjacency.get(targetId) || []), link]);
      }
    });

    return adjacency;
  }, [graphData?.links]);

  useEffect(() => {
    if (!graphData?.nodes?.length) {
      setActiveEntities([]);
      return;
    }

    setActiveEntities((previous) => {
      if (!previous.length) {
        return Object.keys(allEntities);
      }

      const valid = previous.filter((item) => item in allEntities);
      return valid.length ? valid : Object.keys(allEntities);
    });
  }, [allEntities, graphData?.nodes]);

  useEffect(() => {
    if (!selected || !graphData) {
      return;
    }

    if (selected.type === 'node') {
      const nextNode = graphData.nodes.find((node) => node.id === selected.node.id);
      if (!nextNode) {
        setSelected(null);
        return;
      }
      if (nextNode !== selected.node) {
        setSelected({ type: 'node', node: nextNode });
      }
      return;
    }

    const nextEdge = graphData.links.find((edge) => edge.id === selected.edge.id);
    if (!nextEdge) {
      setSelected(null);
      return;
    }
    if (nextEdge !== selected.edge) {
      setSelected({ type: 'edge', edge: nextEdge });
    }
  }, [graphData, selected]);

  const selectedNode =
    selected?.type === 'node'
      ? selected.node
      : undefined;
  const selectedEdge =
    selected?.type === 'edge'
      ? selected.edge
      : undefined;

  const selectedEdgeNodes = useMemo(() => {
    if (!selectedEdge) {
      return {};
    }

    const sourceId = resolveKnowledgeGraphNodeId(selectedEdge.source);
    const targetId = resolveKnowledgeGraphNodeId(selectedEdge.target);

    return {
      sourceNode: sourceId ? nodeById.get(sourceId) : undefined,
      targetNode: targetId ? nodeById.get(targetId) : undefined,
    };
  }, [nodeById, selectedEdge]);

  const visibleNodeIds = useMemo(
    () =>
      new Set(
        (graphData?.nodes || [])
          .filter((node) => {
            const entityType = node.properties?.entity_type;
            return !entityType || activeEntities.includes(entityType);
          })
          .map((node) => node.id),
      ),
    [activeEntities, graphData?.nodes],
  );

  const visibleLinksCount = useMemo(
    () =>
      (graphData?.links || []).filter((link) => {
        const sourceId = resolveKnowledgeGraphNodeId(link.source);
        const targetId = resolveKnowledgeGraphNodeId(link.target);
        return (
          (sourceId ? visibleNodeIds.has(sourceId) : false) &&
          (targetId ? visibleNodeIds.has(targetId) : false)
        );
      }).length,
    [graphData?.links, visibleNodeIds],
  );

  useEffect(() => {
    if (!selected) {
      return;
    }

    if (selected.type === 'node') {
      const entityType = selected.node.properties?.entity_type;
      if (entityType && !activeEntities.includes(entityType)) {
        setSelected(null);
      }
      return;
    }

    const sourceType = selectedEdgeNodes.sourceNode?.properties?.entity_type;
    const targetType = selectedEdgeNodes.targetNode?.properties?.entity_type;
    const hidesSource = sourceType && !activeEntities.includes(sourceType);
    const hidesTarget = targetType && !activeEntities.includes(targetType);

    if (hidesSource || hidesTarget) {
      setSelected(null);
    }
  }, [activeEntities, selected, selectedEdgeNodes.sourceNode, selectedEdgeNodes.targetNode]);

  const selectedSummary = useMemo(() => {
    if (!selected) {
      return pageGraph('selection_none');
    }

    if (selected.type === 'node') {
      return getKnowledgeGraphNodeDisplayName(selected.node);
    }

    const sourceName = getKnowledgeGraphNodeDisplayName(selectedEdgeNodes.sourceNode);
    const targetName = getKnowledgeGraphNodeDisplayName(selectedEdgeNodes.targetNode);
    return `${sourceName} → ${targetName}`;
  }, [pageGraph, selected, selectedEdgeNodes.sourceNode, selectedEdgeNodes.targetNode]);

  const overviewCards = useMemo(
    () => [
      {
        icon: Network,
        label: pageGraph('discover_nodes'),
        value: graphData?.nodes.length || 0,
      },
      {
        icon: Focus,
        label: pageGraph('discover_edges'),
        value: graphData?.links.length || 0,
      },
      {
        icon: ScanSearch,
        label: pageGraph('discover_types'),
        value: Object.keys(allEntities).length,
      },
      {
        icon: Sparkles,
        label: pageGraph('discover_visible_edges'),
        value: visibleLinksCount,
      },
    ],
    [allEntities, graphData?.links.length, graphData?.nodes.length, pageGraph, visibleLinksCount],
  );

  const handleResizeContainer = useCallback(() => {
    const viewport = viewportRef.current;
    if (!viewport) {
      return;
    }
    setDimensions({
      width: Math.max(viewport.offsetWidth - 2, 0),
      height: Math.max(viewport.offsetHeight - 2, 0),
    });
  }, []);

  useEffect(() => {
    handleResizeContainer();
  }, [handleResizeContainer]);

  useEffect(() => {
    const viewport = viewportRef.current;
    if (!viewport) {
      return;
    }

    handleResizeContainer();
    window.addEventListener('resize', handleResizeContainer);
    return () => window.removeEventListener('resize', handleResizeContainer);
  }, [fullscreen, handleResizeContainer]);

  useEffect(() => {
    void getGraphData();
    void getMergeSuggestions();
  }, [getGraphData, getMergeSuggestions]);

  useEffect(() => {
    if (!selected || !graphData) {
      return;
    }

    if (selected.type === 'node') {
      const latestNode = graphData.nodes.find((node) => node.id === selected.node.id);
      if (latestNode && latestNode !== selected.node) {
        setSelected({ type: 'node', node: latestNode });
      }
      return;
    }

    const latestEdge = graphData.links.find((edge) => edge.id === selected.edge.id);
    if (latestEdge && latestEdge !== selected.edge) {
      setSelected({ type: 'edge', edge: latestEdge });
    }
  }, [graphData, selected]);

  useEffect(() => {
    const nextHighlightNodes = new Set<GraphNode>();
    const nextHighlightLinks = new Set<GraphEdge>();

    if (selectedNode) {
      const nodeLinks = linksByNode.get(selectedNode.id) || [];

      nodeLinks.forEach((link) => {
        nextHighlightLinks.add(link);
        const sourceId = resolveKnowledgeGraphNodeId(link.source);
        const targetId = resolveKnowledgeGraphNodeId(link.target);
        const sourceNode = sourceId ? nodeById.get(sourceId) : undefined;
        const targetNode = targetId ? nodeById.get(targetId) : undefined;
        if (sourceNode) {
          nextHighlightNodes.add(sourceNode);
        }
        if (targetNode) {
          nextHighlightNodes.add(targetNode);
        }
      });

      nextHighlightNodes.add(selectedNode);
      // @ts-expect-error x y are attached by the force-graph runtime
      graphRef.current?.centerAt(selectedNode.x, selectedNode.y, 500);
      graphRef.current?.zoom(2.4, 650);
    } else if (selectedEdge) {
      nextHighlightLinks.add(selectedEdge);
      if (selectedEdgeNodes.sourceNode) {
        nextHighlightNodes.add(selectedEdgeNodes.sourceNode);
      }
      if (selectedEdgeNodes.targetNode) {
        nextHighlightNodes.add(selectedEdgeNodes.targetNode);
      }

      const source = selectedEdgeNodes.sourceNode;
      const target = selectedEdgeNodes.targetNode;
      if (source && target) {
        // @ts-expect-error x y are attached by the force-graph runtime
        graphRef.current?.centerAt((source.x + target.x) / 2, (source.y + target.y) / 2, 500);
        graphRef.current?.zoom(2, 650);
      }
    } else {
      graphRef.current?.centerAt(0, 0, 500);
      graphRef.current?.zoom(1.35, 650);
    }

    setHighlightNodes(nextHighlightNodes);
    setHighlightLinks(nextHighlightLinks);
  }, [linksByNode, nodeById, selectedEdge, selectedEdgeNodes.sourceNode, selectedEdgeNodes.targetNode, selectedNode]);

  const clearSelection = useCallback(() => {
    setSelected(null);
    setHoverNodeId(undefined);
    setHighlightNodes(new Set());
    setHighlightLinks(new Set());
  }, []);

  return (
    <div
      className={cn('mt-4 flex min-h-0 flex-1 flex-col gap-4', {
        fixed: fullscreen,
        'inset-0 z-49 bg-background px-4 py-4': fullscreen,
      })}
    >
      <div className="flex flex-wrap items-start justify-between gap-3">
        <div className="space-y-1">
          <div className="text-[11px] font-semibold tracking-[0.24em] uppercase text-foreground/70">
            {pageGraph('workbench_eyebrow')}
          </div>
          <div className="text-2xl font-semibold leading-tight">
            {pageGraph('workbench_title')}
          </div>
          <div className="text-muted-foreground max-w-3xl text-sm leading-6">
            {pageGraph('workbench_description')}
          </div>
        </div>

        <div className="flex flex-wrap items-center gap-2">
          {!marketplace &&
            !isMirofish &&
            !_.isEmpty(mergeSuggestion?.suggestions) && (
              <Tooltip>
                <TooltipTrigger asChild>
                  <Badge
                    variant="destructive"
                    className="h-8 cursor-pointer rounded-full px-3 font-mono tabular-nums"
                    onClick={() => setMergeSuggestionOpen(true)}
                  >
                    {mergeSuggestion?.suggestions?.length &&
                    mergeSuggestion?.suggestions?.length > 10
                      ? '10+'
                      : mergeSuggestion?.suggestions?.length}
                  </Badge>
                </TooltipTrigger>
                <TooltipContent>
                  {pageGraph('merge_infomation', {
                    count: String(mergeSuggestion?.pending_count || 0),
                  })}
                </TooltipContent>
              </Tooltip>
            )}

          <Button
            variant="outline"
            onClick={() => clearSelection()}
            disabled={!selected}
          >
            <Unplug />
            {pageGraph('clear_selection')}
          </Button>

          <Button
            variant="outline"
            onClick={() => {
              void getGraphData();
              if (!isMirofish) {
                void getMergeSuggestions();
              }
            }}
          >
            {loading ? <LoaderCircle className="animate-spin" /> : <RefreshCw />}
            {pageGraph('refresh')}
          </Button>

          <Button
            variant="outline"
            onClick={() => setFullscreen((current) => !current)}
          >
            {fullscreen ? <Minimize /> : <Maximize />}
            {fullscreen
              ? pageGraph('fullscreen_exit')
              : pageGraph('fullscreen_enter')}
          </Button>
        </div>
      </div>

      <div className="grid min-h-0 flex-1 gap-4 xl:grid-cols-[240px_minmax(0,1fr)_320px] 2xl:grid-cols-[280px_minmax(0,1fr)_380px]">
        <Card className="min-h-[320px] rounded-[28px] border shadow-sm">
          <div className="space-y-5 p-5">
            <div className="space-y-2">
              <div className="text-[11px] font-semibold tracking-[0.24em] uppercase text-foreground/70">
                {pageGraph('discover_title')}
              </div>
              <div className="text-xl font-semibold">
                {pageGraph('discover_title')}
              </div>
              <div className="text-muted-foreground text-sm leading-6">
                {pageGraph('discover_description')}
              </div>
            </div>

            <div className="grid grid-cols-2 gap-3">
              {overviewCards.map(({ icon: Icon, label, value }) => (
                <div
                  key={label}
                  className="bg-muted/35 rounded-2xl border p-3"
                >
                  <div className="flex items-center gap-2 text-[11px] font-medium uppercase tracking-[0.18em] text-foreground/70">
                    <Icon className="size-3.5" />
                    {label}
                  </div>
                  <div className="mt-2 text-2xl font-semibold tabular-nums">
                    {value}
                  </div>
                </div>
              ))}
            </div>

            <div className="space-y-2">
              <div className="text-xs font-medium uppercase tracking-[0.18em] text-foreground/70">
                {pageGraph('node_search')}
              </div>
              <Popover>
                <PopoverTrigger asChild>
                  <Button variant="outline" className="w-full justify-between">
                    {pageGraph('node_search')}
                    <ChevronDown />
                  </Button>
                </PopoverTrigger>
                <PopoverContent className="w-[260px] p-0" align="start">
                  <Command>
                    <CommandInput
                      placeholder={pageGraph('node_search')}
                      className="h-9"
                    />
                    <CommandList className="max-h-60">
                      <CommandEmpty>
                        {pageGraph('no_nodes_found')}
                      </CommandEmpty>
                      <CommandGroup>
                        {_.map(graphData?.nodes, (node, key) => {
                          const isActive =
                            selected?.type === 'node' &&
                            selected.node.id === node.id;
                          return (
                            <CommandItem
                              key={key}
                              className="capitalize"
                              value={getKnowledgeGraphNodeDisplayName(node)}
                              onSelect={() => {
                                const entityType = node.properties?.entity_type;
                                if (entityType) {
                                  setActiveEntities((current) =>
                                    current.includes(entityType)
                                      ? current
                                      : _.uniq(current.concat(entityType)),
                                  );
                                }
                                setSelected(
                                  isActive ? null : { type: 'node', node },
                                );
                              }}
                            >
                              <div className="truncate">
                                {getKnowledgeGraphNodeDisplayName(node)}
                              </div>
                              <Check
                                className={cn(
                                  'ml-auto',
                                  isActive ? 'opacity-100' : 'opacity-0',
                                )}
                              />
                            </CommandItem>
                          );
                        })}
                      </CommandGroup>
                    </CommandList>
                  </Command>
                </PopoverContent>
              </Popover>
            </div>

            <div className="space-y-2">
              <div className="text-xs font-medium uppercase tracking-[0.18em] text-foreground/70">
                {pageGraph('entity_types_title')}
              </div>
              <ScrollArea className="max-h-64">
                <div className="flex flex-wrap gap-2 pr-3">
                  {_.map(allEntities, (items, key) => {
                    const isActive = activeEntities.includes(key);
                    const titleKey = `entity_${key}`;
                    const title = hasPageGraphKey(titleKey)
                      ? pageGraph(titleKey)
                      : key;

                    return (
                      <Badge
                        key={key}
                        className={cn(
                          'cursor-pointer border-transparent capitalize transition-opacity',
                          !isActive && 'opacity-55',
                        )}
                        style={{
                          backgroundColor: color(key),
                        }}
                        onClick={() =>
                          setActiveEntities((current) => {
                            if (isActive) {
                              return current.filter((item) => item !== key);
                            }
                            return _.uniq(current.concat(key));
                          })
                        }
                      >
                        {title} ({items.length})
                      </Badge>
                    );
                  })}
                </div>
              </ScrollArea>
            </div>

            <div className="bg-muted/25 rounded-2xl border p-4">
              <div className="text-xs font-medium uppercase tracking-[0.18em] text-foreground/70">
                {pageGraph('current_context_title')}
              </div>
              <div className="mt-2 text-sm font-medium">{selectedSummary}</div>
              <div className="text-muted-foreground mt-2 text-sm leading-6">
                {graphStatusCopy?.description ||
                  pageGraph('graph_ready_prompt')}
              </div>
            </div>
          </div>
        </Card>

        <Card className="min-h-[560px] rounded-[28px] border shadow-sm">
          <div className="flex h-full min-h-[560px] flex-col">
            <div className="flex flex-wrap items-center justify-between gap-3 border-b px-5 py-4">
              <div className="space-y-1">
                <div className="text-[11px] font-semibold tracking-[0.24em] uppercase text-foreground/70">
                  {pageGraph('canvas_title')}
                </div>
                <div className="text-lg font-semibold">
                  {pageGraph('canvas_title')}
                </div>
              </div>

              <div className="flex flex-wrap items-center gap-2">
                {graphStatusCopy ? (
                  <Badge variant={graphStatusCopy.variant}>
                    {graphStatusCopy.badge}
                  </Badge>
                ) : null}
                <Badge variant="secondary">
                  {selected
                    ? selected.type === 'node'
                      ? pageGraph('selection_node')
                      : pageGraph('selection_edge')
                    : pageGraph('selection_browse')}
                </Badge>
              </div>
            </div>

            <div ref={viewportRef} className="relative min-h-0 flex-1">
              {!graphData && (
                <div className="absolute inset-0 grid place-items-center">
                  <div className="flex flex-col items-center gap-3 text-sm text-muted-foreground">
                    <LoaderCircle className="size-5 animate-spin" />
                    {pageGraph('loading_graph')}
                  </div>
                </div>
              )}

              {graphData && _.isEmpty(graphData.nodes) && (
                <div className="absolute inset-0 grid place-items-center px-8 text-center">
                  <div className="space-y-3">
                    <div className="text-lg font-semibold">
                      {pageGraph('no_nodes_found')}
                    </div>
                    <div className="text-muted-foreground text-sm leading-6">
                      {pageGraph('empty_graph_description')}
                    </div>
                  </div>
                </div>
              )}

              <ForceGraph2D
                graphData={graphData}
                width={dimensions.width}
                height={dimensions.height}
                ref={graphRef}
                nodeLabel={(node) =>
                  getKnowledgeGraphNodeDisplayName(node as GraphNode)
                }
                linkLabel={(link) =>
                  String(
                    (link as GraphEdge).type ||
                      (link as GraphEdge).properties?.description ||
                      (link as GraphEdge).id,
                  )
                }
                nodeVisibility={(node) => {
                  const entityType = node.properties?.entity_type;
                  return !entityType || activeEntities.includes(entityType);
                }}
                linkVisibility={(link) => {
                  const sourceId = resolveKnowledgeGraphNodeId(
                    link.source as string | GraphNode,
                  );
                  const targetId = resolveKnowledgeGraphNodeId(
                    link.target as string | GraphNode,
                  );
                  return (
                    (sourceId ? visibleNodeIds.has(sourceId) : false) &&
                    (targetId ? visibleNodeIds.has(targetId) : false)
                  );
                }}
                onNodeClick={(node) => {
                  if (selected?.type === 'node' && selected.node.id === node.id) {
                    clearSelection();
                    return;
                  }
                  const nextNode = node as GraphNode;
                  const entityType = nextNode.properties?.entity_type;
                  if (entityType) {
                    setActiveEntities((current) =>
                      current.includes(entityType)
                        ? current
                        : _.uniq(current.concat(entityType)),
                    );
                  }
                  setHoverNodeId(undefined);
                  setSelected({ type: 'node', node: nextNode });
                }}
                onLinkClick={(link) => {
                  const nextLink = link as GraphEdge;
                  if (selected?.type === 'edge' && selected.edge.id === nextLink.id) {
                    clearSelection();
                    return;
                  }
                  const sourceId = resolveKnowledgeGraphNodeId(nextLink.source);
                  const targetId = resolveKnowledgeGraphNodeId(nextLink.target);
                  const sourceType = sourceId
                    ? nodeById.get(sourceId)?.properties?.entity_type
                    : undefined;
                  const targetType = targetId
                    ? nodeById.get(targetId)?.properties?.entity_type
                    : undefined;
                  const nextTypes = [sourceType, targetType].filter(Boolean) as string[];
                  if (nextTypes.length) {
                    setActiveEntities((current) => _.uniq(current.concat(nextTypes)));
                  }
                  setHoverNodeId(undefined);
                  setSelected({ type: 'edge', edge: nextLink });
                }}
                onNodeHover={(node) => {
                  if (selected) {
                    return;
                  }

                  const nextHighlightNodes = new Set<GraphNode>();
                  const nextHighlightLinks = new Set<GraphEdge>();

                  if (node) {
                    const hoveredNodeId = String(node.id);
                    setHoverNodeId(hoveredNodeId);

                    const hoveredNode = nodeById.get(hoveredNodeId);
                    if (hoveredNode) {
                      nextHighlightNodes.add(hoveredNode);
                    }

                    (linksByNode.get(hoveredNodeId) || []).forEach((link) => {
                      const sourceId = resolveKnowledgeGraphNodeId(link.source);
                      const targetId = resolveKnowledgeGraphNodeId(link.target);
                      nextHighlightLinks.add(link);
                      if (sourceId && nodeById.get(sourceId)) {
                        nextHighlightNodes.add(nodeById.get(sourceId)!);
                      }
                      if (targetId && nodeById.get(targetId)) {
                        nextHighlightNodes.add(nodeById.get(targetId)!);
                      }
                    });
                  } else {
                    setHoverNodeId(undefined);
                  }

                  setHighlightNodes(nextHighlightNodes);
                  setHighlightLinks(nextHighlightLinks);
                }}
                onLinkHover={(link) => {
                  if (selected) {
                    return;
                  }

                  const nextHighlightNodes = new Set<GraphNode>();
                  const nextHighlightLinks = new Set<GraphEdge>();
                  setHoverNodeId(undefined);

                  if (link) {
                    const hoveredEdge = link as GraphEdge;
                    nextHighlightLinks.add(hoveredEdge);

                    const sourceId = resolveKnowledgeGraphNodeId(
                      hoveredEdge.source,
                    );
                    const targetId = resolveKnowledgeGraphNodeId(
                      hoveredEdge.target,
                    );
                    const sourceNode = sourceId ? nodeById.get(sourceId) : undefined;
                    const targetNode = targetId ? nodeById.get(targetId) : undefined;

                    if (sourceNode) {
                      nextHighlightNodes.add(sourceNode);
                    }
                    if (targetNode) {
                      nextHighlightNodes.add(targetNode);
                    }
                  }

                  setHighlightNodes(nextHighlightNodes);
                  setHighlightLinks(nextHighlightLinks);
                }}
                nodeCanvasObject={(node, ctx) => {
                  renderKnowledgeGraphNode({
                    node: node as GraphNode,
                    ctx,
                    colorScale: color,
                    resolvedTheme,
                    isNodeHighlighted: (currentNode) =>
                      highlightNodes.size === 0 ||
                      highlightNodes.has(currentNode as GraphNode),
                    isNodeHovered: (currentNode) =>
                      hoverNodeId === String(currentNode.id),
                  });
                  return;
                  const x = node.x || 0;
                  const y = node.y || 0;
                  const nodeSize = Math.min(node.value || NODE_MIN, NODE_MAX);
                  const isHovered = hoverNodeId === String(node.id);
                  const size = isHovered ? nodeSize + 1.25 : nodeSize;

                  ctx.beginPath();
                  ctx.arc(x, y, size, 0, 2 * Math.PI, false);

                  const tone = color(node.properties.entity_type || '');
                  const mutedTone =
                    resolvedTheme === 'dark'
                      ? Color(tone).desaturate(0.45).lighten(0.05)
                      : Color(tone).desaturate(0.55).darken(0.12);

                  ctx.fillStyle =
                    highlightNodes.size === 0 || highlightNodes.has(node as GraphNode)
                      ? tone
                      : mutedTone.string();
                  ctx.fill();

                  ctx.beginPath();
                  ctx.arc(x, y, size, 0, 2 * Math.PI, false);
                  ctx.lineWidth = highlightNodes.has(node as GraphNode) ? 2 : 1;
                  ctx.strokeStyle =
                    resolvedTheme === 'dark'
                      ? highlightNodes.has(node as GraphNode)
                        ? 'rgba(250, 250, 250, 0.92)'
                        : 'rgba(24, 24, 27, 0.88)'
                      : highlightNodes.has(node as GraphNode)
                        ? 'rgba(24, 24, 27, 0.88)'
                        : 'rgba(113, 113, 122, 0.72)';
                  ctx.stroke();

                  const nodeLabel = getNodeDisplayName(node as GraphNode);
                  let fontSize = Math.max(
                    NODE_FONT_MIN,
                    Math.min(NODE_FONT_MAX, Math.floor(size * 0.72)),
                  );
                  const offset = 2;
                  ctx.font = `600 ${fontSize}px Arial`;
                  let textWidth = ctx.measureText(nodeLabel).width - offset;
                  const maxLabelWidth = size * 1.55;
                  let truncatedLabel = nodeLabel;
                  while (textWidth > maxLabelWidth && truncatedLabel.length > 3) {
                    truncatedLabel = `${truncatedLabel.slice(0, -2)}…`;
                    textWidth = ctx.measureText(truncatedLabel).width - offset;
                  }
                  while (textWidth > maxLabelWidth && fontSize > NODE_FONT_MIN) {
                    fontSize -= 1;
                    ctx.font = `600 ${fontSize}px Arial`;
                    textWidth = ctx.measureText(truncatedLabel).width - offset;
                  }
                  ctx.fillStyle = '#fff';
                  ctx.fillText(
                    truncatedLabel,
                    x - (textWidth + offset) / 2,
                    y + fontSize / 2.8,
                  );
                }}
                nodePointerAreaPaint={(node, paintColor, ctx) => {
                  paintKnowledgeGraphNodePointerArea({
                    node: node as GraphNode,
                    paintColor,
                    ctx,
                  });
                  return;
                  const x = node.x || 0;
                  const y = node.y || 0;
                  const size = Math.min(node.value || NODE_MIN, NODE_MAX);
                  ctx.fillStyle = paintColor;
                  ctx.beginPath();
                  ctx.arc(x, y, size, 0, 2 * Math.PI, false);
                  ctx.fill();
                }}
                linkColor={(link) => {
                  return getKnowledgeGraphLinkColor({
                    link: link as GraphEdge,
                    resolvedTheme,
                    isLinkHighlighted: (currentLink) =>
                      highlightLinks.has(currentLink as GraphEdge),
                  });
                  const isActive = highlightLinks.has(link as GraphEdge);
                  if (resolvedTheme === 'dark') {
                    return isActive ? '#A3A3A3' : '#3F3F46';
                  }
                  return isActive ? '#737373' : '#D4D4D8';
                }}
                linkWidth={(link) =>
                  getKnowledgeGraphLinkWidth(
                    link as GraphEdge,
                    (currentLink) =>
                      highlightLinks.has(currentLink as GraphEdge),
                  )
                }
                linkDirectionalParticleWidth={(link) =>
                  getKnowledgeGraphLinkDirectionalParticleWidth(
                    link as GraphEdge,
                    (currentLink) =>
                      highlightLinks.has(currentLink as GraphEdge),
                  )
                }
                linkDirectionalParticles={2}
              />
            </div>
          </div>
        </Card>

        <CollectionGraphInspector
          selection={selected}
          graphData={graphData}
          collectionConfig={collection.config}
          locale={locale}
          selectedEdgeNodes={selectedEdgeNodes}
        />
      </div>

      {!isMirofish && mergeSuggestion && (
        <CollectionGraphNodeMerge
          dataSource={mergeSuggestion}
          open={mergeSuggestionOpen}
          onRefresh={getMergeSuggestions}
          onClose={() => {
            setSelected(null);
            setMergeSuggestionOpen(false);
          }}
          onSelectNode={(id: string) => {
            const node = graphData?.nodes.find(
              (item) => item.id === id || item.properties?.entity_name === id,
            );
            if (node) {
              const entityType = node.properties?.entity_type;
              if (entityType) {
                setActiveEntities((current) =>
                  current.includes(entityType)
                    ? current
                    : _.uniq(current.concat(entityType)),
                );
              }
              setSelected({ type: 'node', node });
            }
          }}
        />
      )}
    </div>
  );
};
