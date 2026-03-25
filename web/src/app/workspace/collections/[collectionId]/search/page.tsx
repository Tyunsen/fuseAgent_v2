import type { Document, SearchResult } from '@/api';
import {
  PageContainer,
  PageContent,
  PageHeader,
} from '@/components/page-container';
import { getServerApi } from '@/lib/api/server';
import { toJson } from '@/lib/utils';
import { getTranslations } from 'next-intl/server';
import { getCollectionQueryAccess } from '../../tools';
import { CollectionHeader } from '../collection-header';
import { SearchTable } from './search-table';

export default async function Page({
  params,
}: Readonly<{
  params: Promise<{ collectionId: string }>;
}>) {
  const page_collections = await getTranslations('page_collections');
  const page_search = await getTranslations('page_search');
  const { collectionId } = await params;
  const serverApi = await getServerApi();
  type ListPayload<T> = { items?: T[] };

  const [collectionRes, documentsRes, searchRes] = await Promise.all([
    serverApi.defaultApi.collectionsCollectionIdGet({
      collectionId,
    }),
    serverApi.defaultApi.collectionsCollectionIdDocumentsGet({
      collectionId,
      page: 1,
      pageSize: 100,
      sortBy: 'created',
      sortOrder: 'desc',
    }),
    serverApi.defaultApi.collectionsCollectionIdSearchesGet({
      collectionId,
    }),
  ]);

  const documents = ((documentsRes.data as ListPayload<Document>).items ||
    []) as Document[];
  const searches = ((searchRes.data as ListPayload<SearchResult>).items ||
    []) as SearchResult[];
  const queryAccess = getCollectionQueryAccess({
    collectionStatus: collectionRes.data.status,
    collectionConfig: collectionRes.data.config,
    documents,
  });

  return (
    <PageContainer>
      <PageHeader
        breadcrumbs={[
          {
            title: page_collections('metadata.title'),
            href: '/workspace/collections',
          },
          {
            title: page_search('metadata.title'),
          },
        ]}
      />
      <CollectionHeader />
      <PageContent>
        <SearchTable data={searches} queryAccess={toJson(queryAccess)} />
      </PageContent>
    </PageContainer>
  );
}
