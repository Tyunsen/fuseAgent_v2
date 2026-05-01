'use client';

import { CollectionConfig, GraphEdge, GraphNode } from '@/api';
import { ScrollArea } from '@/components/ui/scroll-area';
import { Separator } from '@/components/ui/separator';
import { useTranslations } from 'next-intl';
import { getCollectionGraphStatusCopy } from '../../tools';
import {
  DetailSection,
  FieldRow,
  StatCard,
} from './collection-graph-detail-shared';
import { CollectionGraphEdgeDetailPanel } from './collection-graph-edge-detail';
import { CollectionGraphNodeDetailPanel } from './collection-graph-node-detail';

type Selection =
  | { type: 'node'; node: GraphNode }
  | { type: 'edge'; edge: GraphEdge }
  | null;

export const CollectionGraphInspector = ({
  selection,
  graphData,
  collectionConfig,
  locale,
  selectedEdgeNodes,
}: {
  selection: Selection;
  graphData?: { nodes: GraphNode[]; links: GraphEdge[] };
  collectionConfig?: CollectionConfig | null;
  locale: string;
  selectedEdgeNodes?: { sourceNode?: GraphNode; targetNode?: GraphNode };
}) => {
  const rawPageGraph = useTranslations('page_graph');
  const pageGraph = (key: string) => rawPageGraph(key as never);
  const graphStatusCopy = getCollectionGraphStatusCopy(collectionConfig, locale);
  const nodeCount = graphData?.nodes.length || 0;
  const edgeCount = graphData?.links.length || 0;
  const entityTypeCount = new Set(
    (graphData?.nodes || [])
      .map((node) => node.properties?.entity_type)
      .filter(Boolean),
  ).size;
  const collectionConfigWithOntology =
    collectionConfig as (CollectionConfig & {
      graph_ontology_summary?: string;
    }) | null;
  const ontologySummary = String(
    collectionConfigWithOntology?.graph_ontology_summary || '',
  ).trim();

  return (
    <aside className="bg-background/96 flex min-h-[420px] min-w-0 flex-col rounded-[28px] border shadow-sm backdrop-blur xl:max-w-[340px] 2xl:max-w-[380px]">
      <div className="space-y-3 border-b px-5 py-5">
        <div className="text-[11px] font-semibold tracking-[0.24em] uppercase text-foreground/70">
          {pageGraph('inspector_eyebrow')}
        </div>
        <div className="text-2xl font-semibold leading-tight">
          {selection?.type === 'node'
            ? pageGraph('inspector_title_node')
            : selection?.type === 'edge'
              ? pageGraph('inspector_title_edge')
              : pageGraph('inspector_title_graph')}
        </div>
        <div className="text-muted-foreground text-sm leading-6">
          {selection?.type === 'node'
            ? pageGraph('inspector_description_node')
            : selection?.type === 'edge'
              ? pageGraph('inspector_description_edge')
              : pageGraph('inspector_description_graph')}
        </div>
      </div>

      <ScrollArea className="min-h-0 flex-1">
        <div className="space-y-6 p-5">
          {!selection ? (
            <>
              <div className="grid grid-cols-3 gap-2 2xl:gap-3">
                <StatCard label={pageGraph('discover_nodes')} value={nodeCount} />
                <StatCard label={pageGraph('discover_edges')} value={edgeCount} />
                <StatCard label={pageGraph('discover_types')} value={entityTypeCount} />
              </div>

              <DetailSection
                title={pageGraph('inspector_selection_title')}
                description={pageGraph('inspector_selection_description')}
              >
                <div className="text-muted-foreground rounded-2xl border border-dashed p-4 text-sm leading-6">
                  {pageGraph('inspector_selection_empty')}
                </div>
              </DetailSection>

              <Separator />

              <DetailSection
                title={pageGraph('inspector_context_title')}
                description={pageGraph('inspector_context_description')}
              >
                <div className="space-y-3">
                  <FieldRow
                    label={pageGraph('inspector_status_label')}
                    value={
                      graphStatusCopy?.badge || pageGraph('inspector_unavailable')
                    }
                  />
                  <FieldRow
                    label={pageGraph('inspector_summary_label')}
                    value={
                      graphStatusCopy?.description ||
                      pageGraph('inspector_no_summary')
                    }
                  />
                  <FieldRow
                    label={pageGraph('inspector_ontology_label')}
                    value={
                      ontologySummary ||
                      pageGraph('inspector_no_ontology')
                    }
                  />
                </div>
              </DetailSection>
            </>
          ) : selection.type === 'node' ? (
            <CollectionGraphNodeDetailPanel
              node={selection.node}
              locale={locale}
            />
          ) : (
            <CollectionGraphEdgeDetailPanel
              edge={selection.edge}
              sourceNode={selectedEdgeNodes?.sourceNode}
              targetNode={selectedEdgeNodes?.targetNode}
              locale={locale}
            />
          )}
        </div>
      </ScrollArea>
    </aside>
  );
};
