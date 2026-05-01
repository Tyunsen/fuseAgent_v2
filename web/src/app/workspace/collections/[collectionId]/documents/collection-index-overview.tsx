'use client';

import {
  Document,
  DocumentVectorIndexStatusEnum,
} from '@/api';
import { useCollectionContext } from '@/components/providers/collection-provider';
import { Badge } from '@/components/ui/badge';
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from '@/components/ui/card';
import { useLocale, useTranslations } from 'next-intl';
import {
  getCollectionGraphStatusCopy,
  getDocumentIndexStatusLabel,
  getDocumentIndexStatusVariant,
  isMirofishCollection,
  sortDocumentIndexStatuses,
} from '../../tools';

type IndexAccessorKey =
  | 'vector_index_status'
  | 'fulltext_index_status'
  | 'graph_index_status';

const getStatusCounts = (documents: Document[], accessorKey: IndexAccessorKey) =>
  documents.reduce<Record<string, number>>((counts, document) => {
    const status = document[accessorKey];
    if (!status) {
      return counts;
    }
    counts[status] = (counts[status] || 0) + 1;
    return counts;
  }, {});

const renderStatusBadges = ({
  counts,
  locale,
}: {
  counts: Record<string, number>;
  locale: string;
}) => {
  const statuses = sortDocumentIndexStatuses(
    Object.keys(counts) as DocumentVectorIndexStatusEnum[],
  );

  return statuses.map((status) => (
    <Badge key={status} variant={getDocumentIndexStatusVariant(status)}>
      {counts[status]} {getDocumentIndexStatusLabel(status, locale)}
    </Badge>
  ));
};

export const CollectionIndexOverview = ({
  documents,
}: {
  documents: Document[];
}) => {
  const { collection } = useCollectionContext();
  const locale = useLocale();
  const pageCollections = useTranslations('page_collections');
  const pageDocuments = useTranslations('page_documents');
  const graphStatusCopy = getCollectionGraphStatusCopy(collection.config, locale);
  const documentCount = documents.length;
  const vectorCounts = getStatusCounts(documents, 'vector_index_status');
  const fulltextCounts = getStatusCounts(documents, 'fulltext_index_status');
  const mirofishCollection = isMirofishCollection(collection.config);
  const showExpectationCopy = mirofishCollection && documentCount > 0;
  const overviewTitle =
    locale === 'zh-CN' ? '索引构建状态' : 'Index Build Status';
  const overviewDescription =
    locale === 'zh-CN'
      ? '展示当前知识库内文档的索引状态。'
      : 'Current indexing status for the documents in this knowledge base.';
  const waitingForDocuments =
    locale === 'zh-CN' ? '等待文档' : 'Waiting for documents';
  const documentsTotal =
    locale === 'zh-CN'
      ? `文档数：${documentCount}`
      : `Documents: ${documentCount}`;

  return (
    <Card>
      <CardHeader className="pb-4">
        <CardTitle>{overviewTitle}</CardTitle>
        <CardDescription>{overviewDescription}</CardDescription>
        {showExpectationCopy ? (
          <div className="text-muted-foreground text-xs">
            {pageDocuments('index_expectation_hint')}
          </div>
        ) : null}
      </CardHeader>
      <CardContent className="grid gap-3 lg:grid-cols-3">
        <div className="rounded-xl border p-4">
          <div className="mb-3 flex items-center justify-between gap-3">
            <div className="font-medium">
              {pageCollections('index_type_VECTOR.title')}
            </div>
            <div className="text-muted-foreground text-xs">{documentsTotal}</div>
          </div>
          <div className="flex flex-wrap gap-2">
            {documentCount === 0 ? (
              <Badge variant="secondary">{waitingForDocuments}</Badge>
            ) : (
              renderStatusBadges({ counts: vectorCounts, locale })
            )}
          </div>
        </div>

        <div className="rounded-xl border p-4">
          <div className="mb-3 flex items-center justify-between gap-3">
            <div className="font-medium">
              {pageCollections('index_type_FULLTEXT.title')}
            </div>
            <div className="text-muted-foreground text-xs">{documentsTotal}</div>
          </div>
          <div className="flex flex-wrap gap-2">
            {documentCount === 0 ? (
              <Badge variant="secondary">{waitingForDocuments}</Badge>
            ) : (
              renderStatusBadges({ counts: fulltextCounts, locale })
            )}
          </div>
        </div>

        {mirofishCollection && graphStatusCopy ? (
          <div className="rounded-xl border p-4">
            <div className="mb-3 flex items-center justify-between gap-3">
              <div className="flex items-center gap-2 font-medium">
                <span>{pageCollections('index_type_GRAPH.title')}</span>
                <Badge variant="secondary">MiroFish</Badge>
              </div>
              <div className="text-muted-foreground text-xs">{documentsTotal}</div>
            </div>
            <div className="mb-3 flex flex-wrap items-center gap-2">
              <Badge variant={graphStatusCopy.variant}>
                {graphStatusCopy.badge}
              </Badge>
              <span className="text-muted-foreground text-xs">
                {graphStatusCopy.description}
              </span>
            </div>
            <div className="text-muted-foreground text-xs">
              {documentCount === 0
                ? waitingForDocuments
                : locale === 'zh-CN'
                  ? '文档列表会同步显示图索引状态；这里展示的是当前知识库整体的 MiroFish 图状态。'
                  : 'The document list also mirrors graph index status; this card shows the overall MiroFish graph state for the collection.'}
            </div>
          </div>
        ) : null}
      </CardContent>
    </Card>
  );
};
