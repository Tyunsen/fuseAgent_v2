import {
  PageContainer,
  PageContent,
  PageHeader,
} from '@/components/page-container';
import { getServerApi } from '@/lib/api/server';
import { toJson } from '@/lib/utils';
import _ from 'lodash';
import { CollectionHeader } from '../../collection-header';
import { DocumentDetail, DocumentSourceFocus } from './document-detail';

const toSingleValue = (
  value: string | string[] | undefined,
): string | undefined => {
  if (Array.isArray(value)) {
    return value[0];
  }
  return value;
};

const toOptionalNumber = (
  value: string | string[] | undefined,
): number | undefined => {
  const singleValue = toSingleValue(value);
  if (!singleValue) {
    return undefined;
  }
  const parsed = Number(singleValue);
  return Number.isFinite(parsed) ? parsed : undefined;
};

const parseSourceFocus = (
  searchParams: Record<string, string | string[] | undefined>,
): DocumentSourceFocus | undefined => {
  const lineStart = toOptionalNumber(searchParams.lineStart);
  const lineEnd = toOptionalNumber(searchParams.lineEnd);
  const pageIdx = toOptionalNumber(searchParams.page);
  const sectionLabel = toSingleValue(searchParams.section);
  const requestedFromAnswer = toSingleValue(searchParams.from) === 'answer-source';

  if (
    lineStart === undefined &&
    lineEnd === undefined &&
    pageIdx === undefined &&
    !sectionLabel &&
    !requestedFromAnswer
  ) {
    return undefined;
  }

  return {
    lineStart,
    lineEnd,
    pageIdx,
    sectionLabel,
    requestedFromAnswer,
    preferredTab:
      lineStart !== undefined || lineEnd !== undefined
        ? 'markdown'
        : pageIdx !== undefined
          ? 'pdf'
          : 'markdown',
  };
};

export default async function Page({
  params,
  searchParams,
}: {
  params: Promise<{ collectionId: string; documentId: string }>;
  searchParams: Promise<Record<string, string | string[] | undefined>>;
}) {
  const { collectionId, documentId } = await params;
  const resolvedSearchParams = await searchParams;
  const serverApi = await getServerApi();
  const sourceFocus = parseSourceFocus(resolvedSearchParams);

  const [documentRes, documentPreviewRes] = await Promise.all([
    serverApi.defaultApi.collectionsCollectionIdDocumentsDocumentIdGet({
      collectionId,
      documentId,
    }),
    serverApi.defaultApi.getDocumentPreview({
      collectionId,
      documentId,
    }),
  ]);

  const document = toJson(documentRes.data);
  const documentPreview = toJson(documentPreviewRes.data);

  return (
    <PageContainer>
      <PageHeader
        breadcrumbs={[
          {
            title: 'Collections',
            href: '/workspace/collections',
          },
          {
            title: 'Documents',
            href: `/workspace/collections/${collectionId}/documents`,
          },
          {
            title: _.truncate(document.name || '', { length: 30 }),
          },
        ]}
      />
      <CollectionHeader />
      <PageContent className="h-[100%]">
        <DocumentDetail
          document={document}
          documentPreview={documentPreview}
          sourceFocus={sourceFocus}
        />
      </PageContent>
    </PageContainer>
  );
}
