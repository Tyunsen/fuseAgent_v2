import type { Collection, CollectionView, Document } from '@/api';
import {
  PageContainer,
  PageContent,
  PageDescription,
  PageHeader,
  PageTitle,
} from '@/components/page-container';
import { getServerApi } from '@/lib/api/server';
import { toJson } from '@/lib/utils';
import type { Metadata } from 'next';
import { getTranslations } from 'next-intl/server';
import { CollectionList } from './collection-list';
import { getCollectionQueryAccess, type CollectionListItem } from './tools';

export const dynamic = 'force-dynamic';

export async function generateMetadata(): Promise<Metadata> {
  const page_collections = await getTranslations('page_collections');
  return {
    title: page_collections('metadata.title'),
    description: page_collections('metadata.description'),
  };
}

export default async function Page() {
  const serverApi = await getServerApi();
  const page_collections = await getTranslations('page_collections');

  let collections: CollectionListItem[] = [];
  type ListPayload<T> = { items?: T[] };

  try {
    const res = await serverApi.defaultApi.collectionsGet({
      page: 1,
      pageSize: 100,
      includeSubscribed: false,
    });

    const items = ((res.data as ListPayload<CollectionView>).items ||
      []) as CollectionView[];
    const collectionDetails = await Promise.all(
      items.map(async (collection) => {
        if (!collection.id) {
          return null;
        }

        try {
          const detailRes =
            await serverApi.defaultApi.collectionsCollectionIdGet({
              collectionId: collection.id,
            });
          return detailRes.data as Collection;
        } catch (error) {
          console.log(error);
          return null;
        }
      }),
    );

    const documentsByCollection = await Promise.all(
      items.map(async (collection) => {
        if (!collection.id) {
          return [] as Document[];
        }

        try {
          const documentsRes =
            await serverApi.defaultApi.collectionsCollectionIdDocumentsGet({
              collectionId: collection.id,
              page: 1,
              pageSize: 100,
              sortBy: 'created',
              sortOrder: 'desc',
            });

          return ((documentsRes.data as ListPayload<Document>).items ||
            []) as Document[];
        } catch (error) {
          console.log(error);
          return [] as Document[];
        }
      }),
    );

    collections = items.map((collection, index) => ({
      ...collection,
      config: collectionDetails[index]?.config,
      queryAccess: getCollectionQueryAccess({
        collectionStatus: collection.status,
        collectionConfig: collectionDetails[index]?.config,
        documents: documentsByCollection[index],
      }),
    }));
  } catch (error) {
    console.log(error);
  }

  return (
    <PageContainer>
      <PageHeader
        breadcrumbs={[{ title: page_collections('metadata.title') }]}
      />
      <PageContent className="mx-auto w-full max-w-[1040px] min-[1440px]:max-w-[1200px] min-[1920px]:max-w-[1440px] min-[2560px]:max-w-[1760px]">
        <PageTitle>{page_collections('metadata.title')}</PageTitle>
        <PageDescription>
          {page_collections('metadata.description')}
        </PageDescription>
        <CollectionList collections={toJson(collections)} />
      </PageContent>
    </PageContainer>
  );
}
