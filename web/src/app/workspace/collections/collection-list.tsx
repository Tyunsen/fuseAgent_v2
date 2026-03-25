'use client';

import { FormatDate } from '@/components/format-date';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import {
  Card,
  CardAction,
  CardDescription,
  CardFooter,
  CardHeader,
  CardTitle,
} from '@/components/ui/card';
import { Input } from '@/components/ui/input';
import { cn } from '@/lib/utils';
import _ from 'lodash';
import { Calendar, Files, MessageSquareText, Plus } from 'lucide-react';
import { useLocale, useTranslations } from 'next-intl';
import Link from 'next/link';
import { useMemo, useState } from 'react';
import {
  getQaEntryLabel,
  getQueryAccessCopy,
  type CollectionListItem,
} from './tools';

export const CollectionList = ({
  collections,
}: {
  collections: CollectionListItem[];
}) => {
  const locale = useLocale();
  const [searchValue, setSearchValue] = useState('');
  const page_collections = useTranslations('page_collections');
  const page_collection_new = useTranslations('page_collection_new');
  const page_documents = useTranslations('page_documents');

  const filteredCollections = useMemo(() => {
    const keyword = searchValue.trim().toLowerCase();
    if (!keyword) {
      return collections;
    }

    return collections.filter((collection) => {
      const haystack = `${collection.title || ''} ${collection.description || ''}`;
      return haystack.toLowerCase().includes(keyword);
    });
  }, [collections, searchValue]);
  const singleCollection = filteredCollections.length === 1;

  const emptyStateText =
    locale === 'zh-CN'
      ? '未找到匹配的知识库。'
      : 'No matching knowledge bases.';

  return (
    <>
      <div className="mb-6 flex flex-col gap-3 lg:flex-row lg:items-center">
        <div className="w-full min-[1920px]:max-w-[720px] lg:max-w-[640px]">
          <Input
            placeholder={page_collections('search')}
            value={searchValue}
            onChange={(e) => setSearchValue(e.currentTarget.value)}
          />
        </div>
        <div className="flex items-center gap-2">
          <Button asChild>
            <Link href="/workspace/collections/new">
              <Plus /> {page_collection_new('metadata.title')}
            </Link>
          </Button>
        </div>
      </div>

      {collections.length === 0 ? (
        <div className="bg-accent/50 text-muted-foreground rounded-lg py-40 text-center">
          {page_collections('no_collections_found')}
        </div>
      ) : filteredCollections.length === 0 ? (
        <div className="bg-accent/50 text-muted-foreground rounded-lg py-40 text-center">
          {emptyStateText}
        </div>
      ) : (
        <div className="flex flex-wrap gap-4">
          {filteredCollections.map((collection) => {
            const queryAccessCopy = getQueryAccessCopy(
              collection.queryAccess,
              locale,
            );
            const qaHref = `/workspace/collections/${collection.id}/search`;
            const documentsHref = `/workspace/collections/${collection.id}/documents`;

            return (
              <div
                key={collection.id}
                className={cn(
                  'w-full',
                  singleCollection
                    ? 'max-w-full min-[900px]:w-[760px]'
                    : 'min-[900px]:max-w-[520px] min-[900px]:flex-[1_1_420px]',
                )}
              >
                <Card className="h-full gap-3 rounded-md">
                  <CardHeader className="px-4">
                    <CardTitle className="line-clamp-1">
                      {collection.title}
                    </CardTitle>
                    <CardAction className="flex flex-wrap items-center justify-end gap-2">
                      <Badge
                        variant={
                          collection.is_published ? 'default' : 'secondary'
                        }
                      >
                        {collection.is_published
                          ? page_collections('public')
                          : page_collections('private')}
                      </Badge>
                      <Badge
                        variant={
                          collection.queryAccess.state === 'blocked'
                            ? 'destructive'
                            : collection.queryAccess.state === 'warning'
                              ? 'secondary'
                              : 'outline'
                        }
                      >
                        {queryAccessCopy.badge}
                      </Badge>
                    </CardAction>
                  </CardHeader>

                  <CardDescription className="space-y-2 px-4">
                    <p className="line-clamp-2">
                      {collection.description ||
                        page_collections('no_description_available')}
                    </p>
                    <p className="text-xs">{queryAccessCopy.description}</p>
                  </CardDescription>

                  <div className="flex gap-2 px-4">
                    <Button variant="outline" asChild className="flex-1">
                      <Link href={documentsHref}>
                        <Files />
                        {page_documents('metadata.title')}
                      </Link>
                    </Button>

                    {collection.queryAccess.state === 'blocked' ? (
                      <Button disabled className="flex-1">
                        <MessageSquareText />
                        {getQaEntryLabel(locale)}
                      </Button>
                    ) : (
                      <Button asChild className="flex-1">
                        <Link href={qaHref}>
                          <MessageSquareText />
                          {getQaEntryLabel(locale)}
                        </Link>
                      </Button>
                    )}
                  </div>

                  <CardFooter className="justify-between px-4 text-xs">
                    <div className="text-muted-foreground">
                      {collection.created && (
                        <div className="flex items-center gap-2">
                          <Calendar className="size-3" />
                          <FormatDate datetime={new Date(collection.created)} />
                        </div>
                      )}
                    </div>
                    <div className="flex items-center gap-1">
                      <div
                        data-status={collection.status}
                        className={cn(
                          'size-2 rounded-lg',
                          'data-[status=ACTIVE]:bg-green-700',
                          'data-[status=INACTIVE]:bg-red-500',
                          'data-[status=DELETED]:bg-gray-500',
                        )}
                      />
                      <div className="text-muted-foreground">
                        {_.upperFirst(_.lowerCase(collection.status))}
                      </div>
                    </div>
                  </CardFooter>
                </Card>
              </div>
            );
          })}
        </div>
      )}
    </>
  );
};
