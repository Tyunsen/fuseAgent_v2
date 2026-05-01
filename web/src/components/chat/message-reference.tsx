'use client';

import { Reference } from '@/api';
import { Button } from '@/components/ui/button';
import {
  Drawer,
  DrawerContent,
  DrawerHeader,
  DrawerTitle,
  DrawerTrigger,
} from '@/components/ui/drawer';
import { useTranslations } from 'next-intl';
import { useEffect, useMemo, useState } from 'react';
import {
  TraceConclusion,
  prepareReferenceRows,
} from './message-answer-support.types';
import { MessageReferenceCard } from './message-reference-card';

export const MessageReference = ({
  references,
  conclusionMap = {},
}: {
  references: Reference[];
  conclusionMap?: Record<string, TraceConclusion[]>;
}) => {
  const t = useTranslations('page_chat.answer_support');
  const rows = useMemo(() => prepareReferenceRows(references), [references]);
  const [activeRowIds, setActiveRowIds] = useState<string[]>([]);
  const [expandedRowIds, setExpandedRowIds] = useState<string[]>([]);

  useEffect(() => {
    setActiveRowIds([]);
    setExpandedRowIds([]);
  }, [rows]);

  return (
    <Drawer direction="right" handleOnly={true}>
      <DrawerTrigger asChild>
        <Button
          variant="ghost"
          size="sm"
          className="text-muted-foreground h-8 cursor-pointer px-2"
        >
          {t('evidence_title')}
        </Button>
      </DrawerTrigger>
      <DrawerContent className="flex sm:min-w-xl md:min-w-2xl">
        <DrawerHeader>
          <DrawerTitle className="font-bold">{t('evidence_title')}</DrawerTitle>
        </DrawerHeader>
        <div className="overflow-auto px-4 pb-4 select-text">
          <MessageReferenceCard
            rows={rows}
            activeRowIds={activeRowIds}
            expandedRowIds={expandedRowIds}
            onActivateRow={(rowId) => setActiveRowIds([rowId])}
            onToggleRow={(rowId) =>
              setExpandedRowIds((current) =>
                current.includes(rowId)
                  ? current.filter((id) => id !== rowId)
                  : [...current, rowId],
              )
            }
            conclusionMap={conclusionMap}
          />
        </div>
      </DrawerContent>
    </Drawer>
  );
};
