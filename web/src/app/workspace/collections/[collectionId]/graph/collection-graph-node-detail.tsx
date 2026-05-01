'use client';

import { GraphNode } from '@/api';
import { Markdown } from '@/components/markdown';
import { Badge } from '@/components/ui/badge';
import { Separator } from '@/components/ui/separator';
import { useTranslations } from 'next-intl';
import {
  BadgeListField,
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

export const CollectionGraphNodeDetailPanel = ({
  node,
  locale = 'zh-CN',
}: {
  node: GraphNode;
  locale?: string;
}) => {
  const rawPageGraph = useTranslations('page_graph');
  const pageGraph = (key: string) => rawPageGraph(key as never);
  const properties = node.properties || {};
  const entityName = String(properties.entity_name || node.id || '');
  const entityType = String(properties.entity_type || node.labels?.[1] || '');
  const labels = (node.labels || []).filter(Boolean);
  const aliases = toStringArray(properties.aliases);
  const chunkIds = toStringArray(properties.chunk_ids);
  const summary = String(
    properties.description || properties.summary || '',
  ).trim();
  const degreeCount =
    toNumber(properties.degree_count) ??
    (toNumber(properties.inbound_count) || 0) +
      (toNumber(properties.outbound_count) || 0);
  const inboundCount = toNumber(properties.inbound_count) || 0;
  const outboundCount = toNumber(properties.outbound_count) || 0;
  const createdAt = formatTimestamp(properties.created_at, locale);
  const attributeEntries = getRenderableDetailEntries(properties, GRAPH_DETAIL_KEYS);

  return (
    <div className="space-y-6">
      <div className="space-y-4">
        <div className="space-y-2">
          <div className="flex flex-wrap items-center gap-2">
            {entityType ? <Badge variant="outline">{entityType}</Badge> : null}
            <Badge variant="secondary">{pageGraph('node_badge')}</Badge>
            {labels
              .filter((label) => label !== entityType && label !== 'Entity')
              .map((label) => (
                <Badge key={label} variant="secondary">
                  {label}
                </Badge>
              ))}
          </div>
          <div className="break-words text-xl leading-tight font-semibold 2xl:text-2xl">
            {entityName}
          </div>
          <div className="text-muted-foreground text-sm leading-6">
            {pageGraph('node_description')}
          </div>
        </div>

        <div className="grid grid-cols-3 gap-2 2xl:gap-3">
          <StatCard label={pageGraph('label_aliases')} value={aliases.length} />
          <StatCard label={pageGraph('label_mentions')} value={chunkIds.length} />
          <StatCard label={pageGraph('label_relations')} value={degreeCount} />
        </div>
      </div>

      <DetailSection
        title={pageGraph('node_identity_title')}
        description={pageGraph('node_identity_description')}
      >
        <div className="space-y-3">
          <FieldRow label={pageGraph('label_name')} value={entityName || 'N/A'} />
          <FieldRow label={pageGraph('label_type')} value={entityType || 'N/A'} />
          <FieldRow
            label={pageGraph('label_entity_id')}
            value={String(properties.entity_id || node.id || 'N/A')}
            mono={true}
          />
          <FieldRow
            label={pageGraph('label_aliases')}
            value={
              <BadgeListField
                items={aliases}
                emptyLabel={pageGraph('label_no_aliases')}
              />
            }
          />
        </div>
      </DetailSection>

      {summary ? (
        <>
          <Separator />
          <DetailSection
            title={pageGraph('node_summary_title')}
            description={pageGraph('node_summary_description')}
          >
            <div className="bg-muted/25 rounded-2xl border p-4 text-sm leading-7">
              <Markdown>{summary}</Markdown>
            </div>
          </DetailSection>
        </>
      ) : null}

      <Separator />
      <DetailSection
        title={pageGraph('node_attributes_title')}
        description={pageGraph('node_attributes_description')}
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
            {pageGraph('node_attributes_empty')}
          </div>
        )}
      </DetailSection>

      <Separator />
      <DetailSection
        title={pageGraph('node_graph_metadata_title')}
        description={pageGraph('node_graph_metadata_description')}
      >
        <div className="space-y-3">
          <FieldRow
            label={pageGraph('label_created')}
            value={createdAt || 'N/A'}
            mono={true}
          />
          <FieldRow label={pageGraph('label_inbound')} value={String(inboundCount)} />
          <FieldRow
            label={pageGraph('label_outbound')}
            value={String(outboundCount)}
          />
          <FieldRow
            label={pageGraph('label_relations')}
            value={String(degreeCount)}
          />
          <FieldRow label={pageGraph('label_labels')} value={labels.join(', ') || 'N/A'} />
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
        </div>
      </DetailSection>
    </div>
  );
};
