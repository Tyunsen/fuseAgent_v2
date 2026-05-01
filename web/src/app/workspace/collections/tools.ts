import {
  CollectionConfigCreationModeEnum,
  CollectionConfigGraphEngineEnum,
  CollectionConfigGraphStatusEnum,
  CollectionViewStatusEnum,
  DocumentStatusEnum,
  DocumentVectorIndexStatusEnum,
  type CollectionConfig,
  type CollectionView,
  type Document,
} from '@/api';

export const getDocumentStatusColor = (status?: DocumentStatusEnum) => {
  const data: {
    [key in DocumentStatusEnum]: string;
  } = {
    [DocumentStatusEnum.PENDING]: 'text-muted-foreground',
    [DocumentStatusEnum.RUNNING]: 'text-muted-foreground',
    [DocumentStatusEnum.COMPLETE]: 'text-accent-foreground',
    [DocumentStatusEnum.UPLOADED]: 'text-muted-foreground',
    [DocumentStatusEnum.FAILED]: 'text-red-500',
    [DocumentStatusEnum.EXPIRED]: 'text-muted-foreground line-through',
    [DocumentStatusEnum.DELETED]: 'text-muted-foreground line-through',
    [DocumentStatusEnum.DELETING]: 'text-muted-foreground line-through',
  };
  return status ? data[status] : 'text-muted-foreground';
};

export type CollectionQueryAccessState = 'blocked' | 'warning' | 'ready';

export type CollectionQueryAccessReason =
  | 'collection_inactive'
  | 'no_documents'
  | 'initial_build'
  | 'updating'
  | 'graph_failed'
  | 'ready';

export type CollectionQueryAccess = {
  state: CollectionQueryAccessState;
  reason: CollectionQueryAccessReason;
  totalDocuments: number;
  completedDocuments: number;
  processingDocuments: number;
  failedDocuments: number;
  graphStatus?: CollectionConfigGraphStatusEnum;
};

export type CollectionGraphStatusCopy = {
  badge: string;
  description: string;
  variant: 'outline' | 'secondary' | 'destructive' | 'default';
};

export type CollectionListItem = CollectionView & {
  config?: CollectionConfig;
  queryAccess: CollectionQueryAccess;
};

const processingStatuses = new Set<DocumentStatusEnum>([
  DocumentStatusEnum.UPLOADED,
  DocumentStatusEnum.PENDING,
  DocumentStatusEnum.RUNNING,
  DocumentStatusEnum.DELETING,
]);

const isChineseLocale = (locale: string) => locale === 'zh-CN';

export const isMirofishCollection = (
  collectionConfig?: CollectionConfig | null,
) =>
  collectionConfig?.creation_mode ===
    CollectionConfigCreationModeEnum.mirofish_simple ||
  collectionConfig?.graph_engine === CollectionConfigGraphEngineEnum.mirofish;

export const shouldShowCollectionGraph = (
  collectionConfig?: CollectionConfig | null,
) =>
  isMirofishCollection(collectionConfig) ||
  Boolean(collectionConfig?.enable_knowledge_graph);

export type CollectionIndexStatusType =
  | 'VECTOR'
  | 'FULLTEXT'
  | 'GRAPH'
  | 'SUMMARY'
  | 'VISION';

export const isCollectionIndexStatusVisible = (
  collectionConfig: CollectionConfig | null | undefined,
  indexType: CollectionIndexStatusType,
) => {
  switch (indexType) {
    case 'VECTOR':
      return Boolean(collectionConfig?.enable_vector);
    case 'FULLTEXT':
      return Boolean(collectionConfig?.enable_fulltext);
    case 'GRAPH':
      return isMirofishCollection(collectionConfig);
    case 'SUMMARY':
      return Boolean(collectionConfig?.enable_summary);
    case 'VISION':
      return Boolean(collectionConfig?.enable_vision);
    default:
      return false;
  }
};

type DocumentIndexStatusValue = DocumentVectorIndexStatusEnum;

const indexStatusSortOrder: DocumentIndexStatusValue[] = [
  DocumentVectorIndexStatusEnum.ACTIVE,
  DocumentVectorIndexStatusEnum.CREATING,
  DocumentVectorIndexStatusEnum.PENDING,
  DocumentVectorIndexStatusEnum.FAILED,
  DocumentVectorIndexStatusEnum.DELETION_IN_PROGRESS,
  DocumentVectorIndexStatusEnum.DELETING,
  DocumentVectorIndexStatusEnum.SKIPPED,
];

export const sortDocumentIndexStatuses = (
  statuses: DocumentIndexStatusValue[],
) =>
  [...statuses].sort(
    (left, right) =>
      indexStatusSortOrder.indexOf(left) - indexStatusSortOrder.indexOf(right),
  );

export const getDocumentIndexStatusLabel = (
  status: DocumentIndexStatusValue | undefined,
  locale: string,
) => {
  const isChinese = isChineseLocale(locale);

  switch (status) {
    case DocumentVectorIndexStatusEnum.ACTIVE:
      return isChinese ? '已就绪' : 'Active';
    case DocumentVectorIndexStatusEnum.CREATING:
      return isChinese ? '构建中' : 'Building';
    case DocumentVectorIndexStatusEnum.PENDING:
      return isChinese ? '等待中' : 'Pending';
    case DocumentVectorIndexStatusEnum.FAILED:
      return isChinese ? '失败' : 'Failed';
    case DocumentVectorIndexStatusEnum.DELETING:
      return isChinese ? '删除中' : 'Deleting';
    case DocumentVectorIndexStatusEnum.DELETION_IN_PROGRESS:
      return isChinese ? '删除处理中' : 'Removing';
    case DocumentVectorIndexStatusEnum.SKIPPED:
    default:
      return isChinese ? '已跳过' : 'Skipped';
  }
};

export const getDocumentIndexStatusVariant = (
  status: DocumentIndexStatusValue | undefined,
): 'outline' | 'secondary' | 'destructive' | 'default' => {
  switch (status) {
    case DocumentVectorIndexStatusEnum.ACTIVE:
      return 'outline';
    case DocumentVectorIndexStatusEnum.FAILED:
      return 'destructive';
    case DocumentVectorIndexStatusEnum.CREATING:
    case DocumentVectorIndexStatusEnum.PENDING:
    case DocumentVectorIndexStatusEnum.DELETING:
    case DocumentVectorIndexStatusEnum.DELETION_IN_PROGRESS:
    case DocumentVectorIndexStatusEnum.SKIPPED:
    default:
      return 'secondary';
  }
};

export const getMirofishDocumentGraphStatus = (
  collectionConfig: CollectionConfig | null | undefined,
): DocumentIndexStatusValue => {
  const graphStatus =
    collectionConfig?.graph_status ||
    CollectionConfigGraphStatusEnum.waiting_for_documents;

  switch (graphStatus) {
    case CollectionConfigGraphStatusEnum.ready:
      return DocumentVectorIndexStatusEnum.ACTIVE;
    case CollectionConfigGraphStatusEnum.failed:
      return DocumentVectorIndexStatusEnum.FAILED;
    case CollectionConfigGraphStatusEnum.waiting_for_documents:
      return DocumentVectorIndexStatusEnum.PENDING;
    case CollectionConfigGraphStatusEnum.building:
    case CollectionConfigGraphStatusEnum.updating:
    default:
      return DocumentVectorIndexStatusEnum.CREATING;
  }
};

export const canUseLegacyGraphSearch = (
  collectionConfig?: CollectionConfig | null,
) =>
  Boolean(collectionConfig?.enable_knowledge_graph) &&
  !isMirofishCollection(collectionConfig);

const getMirofishQueryAccess = ({
  collectionConfig,
  totalDocuments,
  completedDocuments,
  processingDocuments,
  failedDocuments,
}: {
  collectionConfig?: CollectionConfig;
  totalDocuments: number;
  completedDocuments: number;
  processingDocuments: number;
  failedDocuments: number;
}): CollectionQueryAccess => {
  const graphStatus =
    collectionConfig?.graph_status ||
    CollectionConfigGraphStatusEnum.waiting_for_documents;
  const hasActiveGraph = Boolean(collectionConfig?.active_graph_id);

  if (totalDocuments === 0) {
    return {
      state: 'blocked',
      reason: 'no_documents',
      totalDocuments,
      completedDocuments,
      processingDocuments,
      failedDocuments,
      graphStatus,
    };
  }

  if (graphStatus === CollectionConfigGraphStatusEnum.ready) {
    return {
      state: 'ready',
      reason: 'ready',
      totalDocuments,
      completedDocuments,
      processingDocuments,
      failedDocuments,
      graphStatus,
    };
  }

  if (graphStatus === CollectionConfigGraphStatusEnum.updating) {
    return {
      state: hasActiveGraph ? 'warning' : 'blocked',
      reason: hasActiveGraph ? 'updating' : 'initial_build',
      totalDocuments,
      completedDocuments,
      processingDocuments,
      failedDocuments,
      graphStatus,
    };
  }

  if (graphStatus === CollectionConfigGraphStatusEnum.failed) {
    return {
      state: hasActiveGraph ? 'warning' : 'blocked',
      reason: 'graph_failed',
      totalDocuments,
      completedDocuments,
      processingDocuments,
      failedDocuments,
      graphStatus,
    };
  }

  if (
    graphStatus === CollectionConfigGraphStatusEnum.building ||
    graphStatus === CollectionConfigGraphStatusEnum.waiting_for_documents
  ) {
    return {
      state: 'blocked',
      reason: totalDocuments === 0 ? 'no_documents' : 'initial_build',
      totalDocuments,
      completedDocuments,
      processingDocuments,
      failedDocuments,
      graphStatus,
    };
  }

  return {
    state: 'blocked',
    reason: 'initial_build',
    totalDocuments,
    completedDocuments,
    processingDocuments,
    failedDocuments,
    graphStatus,
  };
};

export const getCollectionQueryAccess = ({
  collectionStatus,
  collectionConfig,
  documents,
}: {
  collectionStatus?: CollectionViewStatusEnum;
  collectionConfig?: CollectionConfig;
  documents?: Document[];
}): CollectionQueryAccess => {
  const safeDocuments = documents || [];
  const completedDocuments = safeDocuments.filter(
    (document) => document.status === DocumentStatusEnum.COMPLETE,
  ).length;
  const processingDocuments = safeDocuments.filter((document) =>
    processingStatuses.has(document.status as DocumentStatusEnum),
  ).length;
  const failedDocuments = safeDocuments.filter(
    (document) => document.status === DocumentStatusEnum.FAILED,
  ).length;

  if (collectionStatus !== CollectionViewStatusEnum.ACTIVE) {
    return {
      state: 'blocked',
      reason: 'collection_inactive',
      totalDocuments: safeDocuments.length,
      completedDocuments,
      processingDocuments,
      failedDocuments,
    };
  }

  if (isMirofishCollection(collectionConfig)) {
    return getMirofishQueryAccess({
      collectionConfig,
      totalDocuments: safeDocuments.length,
      completedDocuments,
      processingDocuments,
      failedDocuments,
    });
  }

  if (safeDocuments.length === 0) {
    return {
      state: 'blocked',
      reason: 'no_documents',
      totalDocuments: 0,
      completedDocuments: 0,
      processingDocuments: 0,
      failedDocuments: 0,
    };
  }

  if (completedDocuments === 0) {
    return {
      state: 'blocked',
      reason: 'initial_build',
      totalDocuments: safeDocuments.length,
      completedDocuments: 0,
      processingDocuments,
      failedDocuments,
    };
  }

  if (processingDocuments > 0) {
    return {
      state: 'warning',
      reason: 'updating',
      totalDocuments: safeDocuments.length,
      completedDocuments,
      processingDocuments,
      failedDocuments,
    };
  }

  return {
    state: 'ready',
    reason: 'ready',
    totalDocuments: safeDocuments.length,
    completedDocuments,
    processingDocuments,
    failedDocuments,
  };
};

export const getCollectionGraphStatusCopy = (
  collectionConfig: CollectionConfig | null | undefined,
  locale: string,
): CollectionGraphStatusCopy | null => {
  if (!isMirofishCollection(collectionConfig)) {
    return null;
  }

  const isChinese = isChineseLocale(locale);
  const graphStatus =
    collectionConfig?.graph_status ||
    CollectionConfigGraphStatusEnum.waiting_for_documents;
  const hasActiveGraph = Boolean(collectionConfig?.active_graph_id);

  switch (graphStatus) {
    case CollectionConfigGraphStatusEnum.waiting_for_documents:
      return {
        badge: isChinese ? '等待上传文档' : 'Waiting for Documents',
        description: isChinese
          ? '上传文档后，系统就会开始构建首版图谱。'
          : 'Upload documents to start the first graph build.',
        variant: 'secondary',
      };
    case CollectionConfigGraphStatusEnum.building:
      return {
        badge: isChinese ? '首次建图中' : 'Initial Build',
        description: isChinese
          ? '系统正在根据已加入知识库的文档生成首版图谱，完成前暂不开放问答。'
          : 'The first graph build is in progress, so Q&A remains blocked.',
        variant: 'secondary',
      };
    case CollectionConfigGraphStatusEnum.updating:
      return {
        badge: isChinese ? '图谱更新中' : 'Updating',
        description: isChinese
          ? hasActiveGraph
            ? '可以继续问答，但结果可能还没有包含刚上传的最新内容。'
            : '系统正在根据最新加入的文档构建首版图谱，完成后会开放问答。'
          : hasActiveGraph
            ? 'Q&A is available, but results may lag behind the latest uploads.'
            : 'The initial graph is being built with the latest documents, and Q&A will open afterward.',
        variant: 'secondary',
      };
    case CollectionConfigGraphStatusEnum.failed:
      return {
        badge: isChinese ? '图谱处理失败' : 'Graph Failed',
        description: isChinese
          ? hasActiveGraph
            ? '最近一次图谱更新失败，系统仍保留上一版可用图谱。'
            : '首次建图失败，请检查文档或模型配置后重试。'
          : hasActiveGraph
            ? 'The latest graph update failed, but the previous graph is still available.'
            : 'The initial graph build failed. Check the documents or model configuration and retry.',
        variant: 'destructive',
      };
    case CollectionConfigGraphStatusEnum.ready:
    default:
      return {
        badge: isChinese ? '图谱已就绪' : 'Graph Ready',
        description: isChinese
          ? '当前图谱和问答入口均可正常使用。'
          : 'The graph and Q&A entry are ready to use.',
        variant: 'outline',
      };
  }
};

export const getQueryAccessCopy = (
  access: CollectionQueryAccess,
  locale: string,
) => {
  const isChinese = isChineseLocale(locale);

  switch (access.reason) {
    case 'collection_inactive':
      return {
        badge: isChinese ? '暂不可用' : 'Unavailable',
        description: isChinese
          ? '知识库当前未激活，暂时不能进入问答。'
          : 'This knowledge base is inactive, so Q&A is currently unavailable.',
      };
    case 'no_documents':
      return {
        badge: isChinese ? '先上传文档' : 'Add Documents',
        description: isChinese
          ? '先上传至少一份文档，系统才会开始建图并开放问答。'
          : 'Add at least one document so the system can start building the graph and unlock Q&A.',
      };
    case 'initial_build':
      return {
        badge: isChinese ? '首次建图中' : 'First Build',
        description: isChinese
          ? '首版图谱完成前，暂不开放问答。'
          : 'Q&A stays blocked until the first graph build finishes.',
      };
    case 'updating':
      return {
        badge: isChinese ? '更新中' : 'Updating',
        description: isChinese
          ? '可以继续提问，但结果可能还没有包含最新上传的内容。'
          : 'Q&A is available, but results may lag behind the latest uploads.',
      };
    case 'graph_failed':
      return {
        badge: isChinese ? '图谱处理失败' : 'Graph Failed',
        description: isChinese
          ? access.state === 'warning'
            ? '最近一次图谱更新失败，当前问答仍基于上一版可用图谱。'
            : '首次建图失败，修复后才能开放问答。'
          : access.state === 'warning'
            ? 'The latest graph update failed, and Q&A is still using the previous graph.'
            : 'The first graph build failed, so Q&A remains blocked until it succeeds.',
      };
    case 'ready':
    default:
      return {
        badge: isChinese ? '可问答' : 'Ready',
        description: isChinese
          ? '当前知识库已可以直接问答。'
          : 'This knowledge base is ready for Q&A.',
      };
  }
};

export const getQaEntryLabel = (locale: string) =>
  isChineseLocale(locale) ? '问答' : 'Q&A';
