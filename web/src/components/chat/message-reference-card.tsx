'use client';

import { Markdown } from '@/components/markdown';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { cn } from '@/lib/utils';
import { ArrowUpRight } from 'lucide-react';
import Link from 'next/link';
import { useTranslations } from 'next-intl';
import { useEffect, useRef } from 'react';
import {
  buildReferenceLocationLabel,
  PreparedReferenceRow,
  TraceConclusion,
} from './message-answer-support.types';

export const MessageReferenceCard = ({
  rows,
  activeRowIds,
  expandedRowIds,
  onActivateRow,
  onToggleRow,
  conclusionMap = {},
  showHeader = true,
}: {
  rows: PreparedReferenceRow[];
  activeRowIds: string[];
  expandedRowIds: string[];
  onActivateRow: (rowId: string) => void;
  onToggleRow: (rowId: string) => void;
  conclusionMap?: Record<string, TraceConclusion[]>;
  showHeader?: boolean;
}) => {
  const t = useTranslations('page_chat.answer_support');
  const rowRefs = useRef<Record<string, HTMLDivElement | null>>({});

  useEffect(() => {
    const firstActiveRow = activeRowIds[0];
    if (!firstActiveRow) {
      return;
    }
    rowRefs.current[firstActiveRow]?.scrollIntoView({
      block: 'nearest',
      behavior: 'smooth',
    });
  }, [activeRowIds]);

  return (
    <section className="bg-background rounded-xl border shadow-xs">
      {showHeader ? (
        <div className="flex items-center justify-between border-b px-4 py-3">
          <div className="text-sm font-medium">{t('evidence_title')}</div>
          <Badge variant="secondary" className="rounded-full">
            {rows.length}
          </Badge>
        </div>
      ) : null}

      <div className="space-y-2 p-3">
        {!rows.length ? (
          <div className="text-muted-foreground rounded-lg border border-dashed px-3 py-6 text-sm">
            {t('empty_reasons.no_references')}
          </div>
        ) : null}
        {rows.map((row, index) => {
          const active = activeRowIds.includes(row.id);
          const expanded = expandedRowIds.includes(row.id);
          const relatedConclusions = conclusionMap[row.id] || [];
          const locationLabel = buildReferenceLocationLabel(
            row,
            t('paragraph_not_precise'),
          );

          return (
            <div
              key={row.id}
              ref={(element) => {
                rowRefs.current[row.id] = element;
              }}
              className={cn(
                'bg-card overflow-hidden rounded-lg border transition-colors',
                active && 'border-primary/40 bg-muted/40',
              )}
            >
              <button
                type="button"
                className="w-full cursor-pointer px-3 py-3 text-left"
                onClick={() => {
                  onActivateRow(row.id);
                  onToggleRow(row.id);
                }}
              >
                <div className="flex items-start gap-3">
                  <div className="bg-muted text-muted-foreground mt-0.5 flex size-6 shrink-0 items-center justify-center rounded-full text-xs font-medium">
                    {index + 1}
                  </div>
                  <div className="min-w-0 flex-1">
                    <div className="flex flex-wrap items-center gap-2">
                      <span className="text-foreground truncate text-sm font-medium">
                        {row.previewTitle}
                      </span>
                      {locationLabel && (
                        <Badge variant="outline" className="rounded-full">
                          {locationLabel}
                        </Badge>
                      )}
                    </div>
                    {relatedConclusions.length ? (
                      <div className="mt-2 flex flex-wrap gap-1.5">
                        {relatedConclusions.map((conclusion) => (
                          <Badge
                            key={conclusion.id}
                            variant="secondary"
                            className="rounded-full bg-slate-100 text-slate-700"
                          >
                            {conclusion.title}
                          </Badge>
                        ))}
                      </div>
                    ) : null}
                    <p className="text-muted-foreground mt-2 line-clamp-2 text-sm leading-6">
                      {row.snippet || t('no_passage')}
                    </p>
                  </div>
                </div>
              </button>

              {expanded && (
                <div className="border-t px-3 py-3">
                  {locationLabel && (
                    <div className="mb-3">
                      <Badge variant="outline" className="rounded-full">
                        {locationLabel}
                      </Badge>
                    </div>
                  )}
                  <div className="text-muted-foreground mb-2 text-[11px] font-semibold tracking-[0.16em] uppercase">
                    {t('passage_label')}
                  </div>
                  {row.text ? (
                    <div className="prose prose-sm prose-p:leading-6 text-foreground max-w-none">
                      <Markdown>{row.text}</Markdown>
                    </div>
                  ) : (
                    <p className="text-muted-foreground text-sm">
                      {t('no_passage')}
                    </p>
                  )}
                  {row.sourceHref && (
                    <div className="mt-4 flex justify-end">
                      <Button asChild variant="outline" size="sm">
                        <Link href={row.sourceHref}>
                          {t('open_source')}
                          <ArrowUpRight className="size-4" />
                        </Link>
                      </Button>
                    </div>
                  )}
                </div>
              )}
            </div>
          );
        })}
      </div>
    </section>
  );
};
