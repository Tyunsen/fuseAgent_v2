'use client';

import { isMirofishCollection } from '@/app/workspace/collections/tools';
import { useCollectionContext } from '@/components/providers/collection-provider';
import { Alert, AlertDescription, AlertTitle } from '@/components/ui/alert';
import { Info } from 'lucide-react';
import { useTranslations } from 'next-intl';

export const UploadCompletionAlert = ({
  showUploadHandoff,
}: {
  showUploadHandoff: boolean;
}) => {
  const { collection } = useCollectionContext();
  const pageDocuments = useTranslations('page_documents');

  const showAlert =
    isMirofishCollection(collection.config) && showUploadHandoff;

  if (!showAlert) {
    return null;
  }

  return (
    <Alert>
      <Info />
      <AlertTitle>{pageDocuments('upload_completion_alert_title')}</AlertTitle>
      <AlertDescription>
        <p>{pageDocuments('upload_completion_alert_description')}</p>
        <p>{pageDocuments('upload_completion_alert_graph_hint')}</p>
      </AlertDescription>
    </Alert>
  );
};
