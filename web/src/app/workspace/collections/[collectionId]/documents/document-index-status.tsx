import { getDocumentIndexStatusLabel } from '../../tools';
import { Document, DocumentVectorIndexStatusEnum } from '@/api';
import { cn } from '@/lib/utils';
import _ from 'lodash';
import { useLocale } from 'next-intl';

const getIndexStatusBg = (status?: DocumentVectorIndexStatusEnum) => {
  const data = {
    ACTIVE: 'bg-green-500',
    CREATING: 'bg-sky-500',
    DELETING: 'bg-pink-500',
    DELETION_IN_PROGRESS: 'bg-cyan-500',
    FAILED: 'bg-red-500',
    PENDING: 'bg-amber-500',
    SKIPPED: 'bg-gray-500',
  };
  return status ? data[status] : 'bg-gray-500';
};

export const DocumentIndexStatus = ({
  document,
  accessorKey,
  statusOverride,
}: {
  document: Document;
  accessorKey: string;
  statusOverride?: DocumentVectorIndexStatusEnum;
}) => {
  const locale = useLocale();
  const status = statusOverride ?? _.get(document, accessorKey);
  const color = getIndexStatusBg(status);
  return (
    <div className="flex flex-row items-center gap-2">
      <div className={cn('size-1.5 rounded-4xl', color)}></div>
      <div className="text-xs">
        {getDocumentIndexStatusLabel(status, locale)}
      </div>
    </div>
  );
};
