'use client';

import { GraphEdge, GraphNode } from '@/api';
import { Badge } from '@/components/ui/badge';
import { Separator } from '@/components/ui/separator';
import { useTranslations } from 'next-intl';
import {
  DetailSection,
  FieldRow,
  GRAPH_DETAIL_KEYS,
  StatCard,
  formatTimestamp,
  formatValue,
  getRenderableDetailEntries,
  toNumber,
  toStringArray,
} from './collection-graph-detail-shared';

const getNodeLabel = (node?: GraphNode) =>
  String(node?.properties?.entity_name || node?.id || 'Unknown');

const getNodeType = (node?: GraphNode) =>
  String(node?.properties?.entity_type || node?.labels?.[1] || 'Unknown');

export const CollectionGraphEdgeDetailPanel = ({
  edge,
  sourceNode,
  targetNode,
  locale = 'zh-CN',
}: {
  edge: GraphEdge;
  sourceNode?: GraphNode;
  targetNode?: GraphNode;
  locale?: string;
}) => {
  const rawPageGraph = useTranslations('page_graph');
  const pageGraph = (key: string) => rawPageGraph(key as never);
  const properties = edge.properties || {};
  const relationType = String(edge.type || 'DIRECTED');
  const fact = String(properties.description || '').trim();
  const evidence = String(properties.evidence || '').trim();
  const confidence = toNumber(properties.confidence);
  const chunkIds = toStringArray(
    properties.chunk_ids ||
      (properties.source_chunk_id ? [properties.source_chunk_id] : []),
  );
  const createdAt = formatTimestamp(properties.created_at, locale);
  const attributeEntries = getRenderableDetailEntries(properties, GRAPH_DETAIL_KEYS, [
    'chunk_ids',
  ]);

  return (
    <div className="space-y-6">
      <div className="space-y-4">
        <div className="space-y-2">
          <div className="flex flex-wrap items-center gap-2">
            <Badge variant="outline">{relationType}</Badge>
            <Badge variant="secondary">{pageGraph('edge_badge')}</Badge>
          </div>
          <div className="break-words text-xl leading-tight font-semibold 2xl:text-2xl">
            {relationType}
          </div>
          <div className="text-muted-foreground text-sm leading-6">
            {pageGraph('edge_description')}
          </div>
        </div>

        <div className="grid grid-cols-3 gap-2 2xl:gap-3">
          <StatCard label={pageGraph('label_evidence')} value={evidence ? 1 : 0} />
          <StatCard label={pageGraph('label_chunk_ids')} value={chunkIds.length} />
          <StatCard
            label={pageGraph('label_confidence')}
            value={confidence !== undefined ? confidence.toFixed(2) : 'N/A'}
          />
        </div>
      </div>

      <DetailSection
        title={pageGraph('edge_relationship_title')}
        description={pageGraph('edge_relationship_description')}
      >
        <div className="space-y-3">
          <FieldRow label={pageGraph('label_type')} value={relationType} />
          <FieldRow label={pageGraph('label_edge_id')} value={edge.id} mono={true} />
          <FieldRow label={pageGraph('label_fact')} value={fact || 'N/A'} />
          <FieldRow label={pageGraph('label_evidence')} value={evidence || 'N/A'} />
          <FieldRow
            label={pageGraph('label_confidence')}
            value={
              confidence !== undefined ? confidence.toFixed(2) : 'Unspecified'
            }
          />
        </div>
      </DetailSection>

      <Separator />
      <DetailSection
        title={pageGraph('edge_endpoints_title')}
        description={pageGraph('edge_endpoints_description')}
      >
        <div className="space-y-3">
          <FieldRow
            label={pageGraph('label_source')}
            value={`${getNodeLabel(sourceNode)} (${getNodeType(sourceNode)})`}
          />
          <FieldRow
            label={pageGraph('label_target')}
            value={`${getNodeLabel(targetNode)} (${getNodeType(targetNode)})`}
          />
        </div>
      </DetailSection>

      <Separator />
      <DetailSection
        title={pageGraph('edge_attributes_title')}
        description={pageGraph('edge_attributes_description')}
      >
        {attributeEntries.length ? (
          <div className="space-y-3">
            {attributeEntries.map(([key, value]) => (
              <FieldRow
                key={key}
                label={key}
                value={formatValue(value)}
                mono={typeof value === 'object'}
              />
            ))}
          </div>
        ) : (
          <div className="text-muted-foreground rounded-2xl border border-dashed p-4 text-sm">
            {pageGraph('edge_attributes_empty')}
          </div>
        )}
      </DetailSection>

      <Separator />
      <DetailSection
        title={pageGraph('edge_graph_metadata_title')}
        description={pageGraph('edge_graph_metadata_description')}
      >
        <div className="space-y-3">
          <FieldRow
            label={pageGraph('label_created')}
            value={createdAt || 'N/A'}
            mono={true}
          />
          <FieldRow
            label={pageGraph('label_chunk_ids')}
            value={
              chunkIds.length ? (
                <div className="space-y-2">
                  {chunkIds.map((chunkId) => (
                    <div
                      key={chunkId}
                      className="bg-muted/30 rounded-lg px-2 py-1 font-mono text-xs"
                    >
                      {chunkId}
                    </div>
                  ))}
                </div>
              ) : (
                'N/A'
              )
            }
            mono={true}
          />
          <FieldRow
            label={pageGraph('label_source_chunk')}
            value={String(properties.source_chunk_id || 'N/A')}
            mono={true}
          />
        </div>
      </DetailSection>
    </div>
  );
};
