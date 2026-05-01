import type { Document } from '@/api';
import {
  PageContainer,
  PageContent,
  PageHeader,
} from '@/components/page-container';
import { getServerApi } from '@/lib/api/server';
import { parsePageParams, toJson } from '@/lib/utils';
import { getTranslations } from 'next-intl/server';
import { CollectionGraphStatusAlert } from '../collection-graph-status-alert';
import { CollectionHeader } from '../collection-header';
import { CollectionIndexOverview } from './collection-index-overview';
import { DocumentsTable } from './documents-table';
import { UploadCompletionAlert } from './upload-completion-alert';

const STATUS_OVERVIEW_PAGE_SIZE = 100;
type DocumentPagePayload = {
  items?: Document[];
  total_pages?: number;
};

const loadAllCollectionDocuments = async (
  serverApi: Awaited<ReturnType<typeof getServerApi>>,
  collectionId: string,
) => {
  const firstPageRes = await serverApi.defaultApi.collectionsCollectionIdDocumentsGet({
    collectionId,
    page: 1,
    pageSize: STATUS_OVERVIEW_PAGE_SIZE,
    sortBy: 'created',
    sortOrder: 'desc',
  });
  const firstPageData = firstPageRes.data as DocumentPagePayload;

  const allDocuments = [...(firstPageData.items || [])];
  const totalPages = firstPageData.total_pages || 1;

  if (totalPages > 1) {
    const remainingPages = await Promise.all(
      Array.from({ length: totalPages - 1 }, (_, index) =>
        serverApi.defaultApi.collectionsCollectionIdDocumentsGet({
          collectionId,
          page: index + 2,
          pageSize: STATUS_OVERVIEW_PAGE_SIZE,
          sortBy: 'created',
          sortOrder: 'desc',
        }),
      ),
    );

    remainingPages.forEach((response) => {
      const responseData = response.data as DocumentPagePayload;
      allDocuments.push(...(responseData.items || []));
    });
  }

  return allDocuments;
};

export default async function Page({
  params,
  searchParams,
}: Readonly<{
  params: Promise<{ collectionId: string }>;
  searchParams: Promise<{
    page?: string;
    pageSize?: string;
    search?: string;
    from?: string;
    processing?: string;
  }>;
}>) {
  const { collectionId } = await params;
  const { page, pageSize, search, from, processing } = await searchParams;
  const serverApi = await getServerApi();

  const page_collections = await getTranslations('page_collections');
  const page_documents = await getTranslations('page_documents');

  const [documentsRes, allDocuments] = await Promise.all([
    serverApi.defaultApi.collectionsCollectionIdDocumentsGet({
      collectionId,
      ...parsePageParams({ page, pageSize }),
      sortBy: 'created',
      sortOrder: 'desc',
      search,
    }),
    loadAllCollectionDocuments(serverApi, collectionId),
  ]);

  //@ts-expect-error api define has a bug
  const documents = toJson(documentsRes.data.items || []);
  const overviewDocuments = toJson(allDocuments);
  const showUploadHandoff = from === 'upload' && processing === 'started';

  return (
    <PageContainer>
      <PageHeader
        breadcrumbs={[
          {
            title: page_collections('metadata.title'),
            href: '/workspace/collections',
          },
          {
            title: page_documents('metadata.title'),
          },
        ]}
      />
      <CollectionHeader />
      <PageContent>
        <UploadCompletionAlert showUploadHandoff={showUploadHandoff} />
        <CollectionGraphStatusAlert />
        <CollectionIndexOverview documents={overviewDocuments} />
        <DocumentsTable
          data={documents}
          pageCount={documentsRes.data.total_pages}
        />
      </PageContent>
    </PageContainer>
  );
}
