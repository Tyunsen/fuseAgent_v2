'use client';

import { Badge } from '@/components/ui/badge';
import { cn } from '@/lib/utils';
import type { ReactNode } from 'react';

export const GRAPH_DETAIL_KEYS = new Set([
  'entity_id',
  'entity_name',
  'entity_type',
  'description',
  'summary',
  'aliases',
  'chunk_ids',
  'created_at',
  'inbound_count',
  'outbound_count',
  'degree_count',
  'source_id',
  'file_path',
  'source_chunk_id',
  'confidence',
  'evidence',
]);

export const toStringArray = (value: unknown) => {
  if (!Array.isArray(value)) {
    return [];
  }

  return value
    .map((item) => String(item ?? '').trim())
    .filter((item) => item.length > 0);
};

export const toNumber = (value: unknown) => {
  if (typeof value === 'number' && Number.isFinite(value)) {
    return value;
  }
  if (typeof value === 'string' && value.trim() !== '') {
    const parsed = Number(value);
    return Number.isFinite(parsed) ? parsed : undefined;
  }
  return undefined;
};

export const formatTimestamp = (value: unknown, locale = 'zh-CN') => {
  if (!value) {
    return null;
  }

  const date = new Date(String(value));
  if (Number.isNaN(date.getTime())) {
    return String(value);
  }

  return new Intl.DateTimeFormat(locale, {
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit',
  }).format(date);
};

export const formatValue = (value: unknown) => {
  if (Array.isArray(value)) {
    return value.join(', ');
  }
  if (value === null || value === undefined || value === '') {
    return 'N/A';
  }
  if (typeof value === 'object') {
    return JSON.stringify(value, null, 2);
  }
  return String(value);
};

export const hasRenderableDetailValue = (value: unknown) => {
  if (value === null || value === undefined) {
    return false;
  }
  if (Array.isArray(value) && value.length === 0) {
    return false;
  }
  if (typeof value === 'string' && value.trim() === '') {
    return false;
  }
  return true;
};

export const getRenderableDetailEntries = (
  properties: Record<string, unknown>,
  ignoredKeys: Set<string>,
  extraIgnoredKeys: string[] = [],
) =>
  Object.entries(properties).filter(([key, value]) => {
    if (ignoredKeys.has(key) || extraIgnoredKeys.includes(key)) {
      return false;
    }
    return hasRenderableDetailValue(value);
  });

export const DetailSection = ({
  title,
  description,
  children,
}: {
  title: string;
  description?: string;
  children: ReactNode;
}) => (
  <section className="space-y-3">
    <div className="space-y-1">
      <div className="text-[11px] font-semibold tracking-[0.24em] uppercase">
        {title}
      </div>
      {description ? (
        <div className="text-muted-foreground text-xs leading-5">
          {description}
        </div>
      ) : null}
    </div>
    {children}
  </section>
);

export const StatCard = ({
  label,
  value,
}: {
  label: string;
  value: string | number;
}) => (
  <div className="bg-muted/35 min-w-0 rounded-2xl border p-3">
    <div className="text-muted-foreground text-[10px] leading-4 tracking-[0.16em] uppercase break-words">
      {label}
    </div>
    <div className="mt-1 truncate text-lg font-semibold tabular-nums sm:text-xl">
      {value}
    </div>
  </div>
);

export const FieldRow = ({
  label,
  value,
  mono = false,
}: {
  label: string;
  value: ReactNode;
  mono?: boolean;
}) => (
  <div className="grid min-w-0 gap-2 rounded-2xl border p-3 lg:grid-cols-[96px_minmax(0,1fr)] 2xl:grid-cols-[112px_minmax(0,1fr)] lg:items-start">
    <div className="text-muted-foreground text-[11px] font-medium leading-5 tracking-[0.14em] uppercase break-words">
      {label}
    </div>
    <div
      className={cn(
        'min-w-0 overflow-hidden text-sm leading-6 break-words',
        mono && 'font-mono whitespace-pre-wrap break-all',
      )}
    >
      {value}
    </div>
  </div>
);

export const BadgeListField = ({
  items,
  emptyLabel = 'N/A',
}: {
  items: string[];
  emptyLabel?: string;
}) => {
  if (!items.length) {
    return <span>{emptyLabel}</span>;
  }

  return (
    <div className="flex min-w-0 flex-wrap gap-2">
      {items.map((item) => (
        <Badge
          key={item}
          variant="outline"
          className="max-w-full whitespace-normal break-all text-left"
        >
          {item}
        </Badge>
      ))}
    </div>
  );
};
