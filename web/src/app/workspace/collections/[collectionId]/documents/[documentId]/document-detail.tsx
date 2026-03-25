'use client';
import { Document, DocumentPreview } from '@/api';
import { getDocumentStatusColor } from '@/app/workspace/collections/tools';
import { buildReferenceLocationLabel } from '@/components/chat/message-answer-support.types';
import { FormatDate } from '@/components/format-date';
import { Markdown } from '@/components/markdown';
import { useCollectionContext } from '@/components/providers/collection-provider';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Card, CardContent } from '@/components/ui/card';
import { Separator } from '@/components/ui/separator';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { cn } from '@/lib/utils';
import _ from 'lodash';
import { ArrowLeft, LoaderCircle } from 'lucide-react';
import dynamic from 'next/dynamic';
import Link from 'next/link';
import { useTranslations } from 'next-intl';
import { useEffect, useMemo, useRef, useState } from 'react';
import 'react-pdf/dist/Page/AnnotationLayer.css';
import 'react-pdf/dist/Page/TextLayer.css';

const PDFDocument = dynamic(() => import('react-pdf').then((r) => r.Document), {
  ssr: false,
});
const PDFPage = dynamic(() => import('react-pdf').then((r) => r.Page), {
  ssr: false,
});

export interface DocumentSourceFocus {
  lineStart?: number;
  lineEnd?: number;
  pageIdx?: number;
  sectionLabel?: string;
  requestedFromAnswer?: boolean;
  preferredTab?: 'markdown' | 'pdf';
}

export const DocumentDetail = ({
  document,
  documentPreview,
  sourceFocus,
}: {
  document: Document;
  documentPreview: DocumentPreview;
  sourceFocus?: DocumentSourceFocus;
}) => {
  const t = useTranslations('page_chat.answer_support');
  const { collection } = useCollectionContext();
  const [numPages, setNumPages] = useState<number>(0);
  const [activeTab, setActiveTab] = useState<'markdown' | 'pdf'>(
    sourceFocus?.preferredTab || 'markdown',
  );
  const pdfPageRefs = useRef<Record<number, HTMLDivElement | null>>({});

  const isPdf = useMemo(() => {
    return Boolean(documentPreview.doc_filename?.match(/\.pdf/));
  }, [documentPreview.doc_filename]);

  const sourceExcerpt = useMemo(() => {
    if (
      sourceFocus?.lineStart === undefined &&
      sourceFocus?.lineEnd === undefined
    ) {
      return '';
    }

    const lines = (documentPreview.markdown_content || '').split(/\r?\n/);
    if (!lines.length) {
      return '';
    }

    const start = Math.max(sourceFocus?.lineStart ?? 0, 0);
    const endCandidate = sourceFocus?.lineEnd ?? start + 1;
    const end = Math.min(Math.max(endCandidate, start + 1), lines.length);
    return lines.slice(start, end).join('\n').trim();
  }, [
    documentPreview.markdown_content,
    sourceFocus?.lineEnd,
    sourceFocus?.lineStart,
  ]);

  const sourceLocationLabel = useMemo(
    () =>
      sourceFocus
        ? buildReferenceLocationLabel(
            {
              pageIdx: sourceFocus.pageIdx,
              sectionLabel: sourceFocus.sectionLabel,
              paragraphPrecise:
                sourceFocus.lineStart !== undefined ||
                sourceFocus.lineEnd !== undefined,
              mdSourceMap:
                sourceFocus.lineStart !== undefined ||
                sourceFocus.lineEnd !== undefined
                  ? [
                      sourceFocus.lineStart ?? 0,
                      sourceFocus.lineEnd ?? (sourceFocus.lineStart ?? 0) + 1,
                    ]
                  : undefined,
              pdfSourceMap:
                typeof sourceFocus.pageIdx === 'number'
                  ? [{ pageIdx: sourceFocus.pageIdx }]
                  : [],
            },
            t('paragraph_not_precise'),
          )
        : '',
    [
      sourceFocus,
      t,
    ],
  );

  useEffect(() => {
    const loadPDF = async () => {
      const { pdfjs } = await import('react-pdf');

      pdfjs.GlobalWorkerOptions.workerSrc = new URL(
        'pdfjs-dist/build/pdf.worker.min.mjs',
        import.meta.url,
      ).toString();
    };
    loadPDF();
  }, []);

  useEffect(() => {
    if (!sourceFocus?.preferredTab) {
      return;
    }
    if (sourceFocus.preferredTab === 'pdf' && !isPdf) {
      setActiveTab('markdown');
      return;
    }
    setActiveTab(sourceFocus.preferredTab);
  }, [isPdf, sourceFocus?.preferredTab]);

  useEffect(() => {
    if (
      activeTab !== 'pdf' ||
      sourceFocus?.pageIdx === undefined ||
      numPages === 0
    ) {
      return;
    }
    pdfPageRefs.current[sourceFocus.pageIdx]?.scrollIntoView({
      behavior: 'smooth',
      block: 'center',
    });
  }, [activeTab, numPages, sourceFocus?.pageIdx]);

  return (
    <>
      {sourceFocus?.requestedFromAnswer && (
        <Card className="mb-4 border-primary/25 bg-primary/5">
          <CardContent className="space-y-3 py-4">
            <div className="flex flex-wrap items-center gap-2">
              <div className="text-sm font-semibold">
                {t('source_focus_title')}
              </div>
              {sourceLocationLabel ? (
                <Badge variant="outline" className="rounded-full">
                  {sourceLocationLabel}
                </Badge>
              ) : null}
            </div>
            <p className="text-muted-foreground text-sm">
              {t('source_focus_description')}
            </p>
            {sourceExcerpt ? (
              <div className="rounded-lg border bg-background px-4 py-3">
                <div className="text-muted-foreground mb-2 text-[11px] font-semibold tracking-[0.16em] uppercase">
                  {t('passage_label')}
                </div>
                <div className="prose prose-sm max-w-none">
                  <Markdown>{sourceExcerpt}</Markdown>
                </div>
              </div>
            ) : (
              <p className="text-muted-foreground text-sm">
                {t('no_exact_excerpt')}
              </p>
            )}
          </CardContent>
        </Card>
      )}
      <Tabs value={activeTab} className="gap-4" onValueChange={(value) => setActiveTab(value as 'markdown' | 'pdf')}>
        <div className="flex flex-row items-center justify-between gap-2">
          <div className="flex flex-row items-center gap-4">
            <Button asChild variant="ghost" size="icon">
              <Link href={`/workspace/collections/${collection.id}/documents`}>
                <ArrowLeft />
              </Link>
            </Button>
            <div className={cn('max-w-80 truncate')}>
              {documentPreview.doc_filename}
            </div>
          </div>

          <div className="flex flex-row gap-6">
            <div className="text-muted-foreground flex flex-row items-center gap-4 text-sm">
              <div>{(Number(document.size || 0) / 1000).toFixed(2)} KB</div>
              <Separator
                orientation="vertical"
                className="data-[orientation=vertical]:h-6"
              />
              {document.updated ? (
                <>
                  <div>
                    <FormatDate datetime={new Date(document.updated)} />
                  </div>
                  <Separator
                    orientation="vertical"
                    className="data-[orientation=vertical]:h-6"
                  />
                </>
              ) : null}
              <div className={getDocumentStatusColor(document.status)}>
                {_.capitalize(document.status)}
              </div>
            </div>
            <TabsList>
              <TabsTrigger value="markdown">Markdown</TabsTrigger>
              {isPdf && <TabsTrigger value="pdf">PDF</TabsTrigger>}
            </TabsList>
          </div>
        </div>

        <TabsContent value="markdown">
          <Card>
            <CardContent>
              <Markdown>{documentPreview.markdown_content}</Markdown>
            </CardContent>
          </Card>
        </TabsContent>

        {isPdf && (
          <TabsContent value="pdf">
            <PDFDocument
              file={`${process.env.NEXT_PUBLIC_BASE_PATH || ''}/api/v1/collections/${collection.id}/documents/${document.id}/object?path=${documentPreview.converted_pdf_object_path}`}
              onLoadSuccess={({ numPages }: { numPages: number }) => {
                setNumPages(numPages);
              }}
              loading={
                <div className="flex flex-col py-8">
                  <LoaderCircle className="size-10 animate-spin self-center opacity-50" />
                </div>
              }
              className="flex flex-col justify-center gap-1"
            >
              {_.times(numPages).map((index) => {
                return (
                  <div
                    key={index}
                    ref={(element) => {
                      pdfPageRefs.current[index] = element;
                    }}
                    className="text-center"
                  >
                    <Card className="inline-block overflow-hidden p-0">
                      <PDFPage pageNumber={index + 1} className="bg-accent" />
                    </Card>
                  </div>
                );
              })}
            </PDFDocument>
          </TabsContent>
        )}
      </Tabs>
    </>
  );
};
