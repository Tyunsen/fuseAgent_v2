'use client';

import { useCollectionContext } from '@/components/providers/collection-provider';
import { Alert, AlertDescription, AlertTitle } from '@/components/ui/alert';
import { AlertTriangle, Info } from 'lucide-react';
import { useLocale } from 'next-intl';
import { getCollectionGraphStatusCopy, isMirofishCollection } from '../tools';

export const CollectionGraphStatusAlert = () => {
  const locale = useLocale();
  const { collection } = useCollectionContext();
  const graphStatusCopy = getCollectionGraphStatusCopy(
    collection.config,
    locale,
  );

  if (!isMirofishCollection(collection.config) || !graphStatusCopy) {
    return null;
  }

  const destructive = graphStatusCopy.variant === 'destructive';

  return (
    <Alert variant={destructive ? 'destructive' : 'default'}>
      {destructive ? <AlertTriangle /> : <Info />}
      <AlertTitle>{graphStatusCopy.badge}</AlertTitle>
      <AlertDescription>{graphStatusCopy.description}</AlertDescription>
    </Alert>
  );
};
