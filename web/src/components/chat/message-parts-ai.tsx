import { ChatMessage, Feedback } from '@/api';
import { CopyToClipboard } from '@/components/copy-to-clipboard';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Card } from '@/components/ui/card';
import { Separator } from '@/components/ui/separator';
import { cn } from '@/lib/utils';
import _ from 'lodash';
import { Bot, LoaderCircle } from 'lucide-react';
import { useCallback, useEffect, useMemo, useState } from 'react';
import { useTranslations } from 'next-intl';
import { MessageAnswerSupport } from './message-answer-support';
import { MessageFeedback } from './message-feedback';
import {
  extractAssistantMermaidBlocks,
  MessagePartAi,
  sanitizeAssistantMessageContentByMode,
} from './message-part-ai';
import {
  annotateAnswerWithCitations,
  prepareReferenceRows,
  TraceSupportPayload,
} from './message-answer-support.types';
import { MessageTimestamp } from './message-timestamp';

export const MessagePartsAi = ({
  pending,
  loading,
  parts,
  question,
  hanldeMessageFeedback,
}: {
  pending: boolean;
  loading: boolean;
  parts: ChatMessage[];
  question: string;
  hanldeMessageFeedback: (part: ChatMessage, feedback: Feedback) => void;
}) => {
  const t = useTranslations('page_chat');
  const references = useMemo(
    () => parts.findLast((part) => part.references)?.references || [],
    [parts],
  );
  const traceMode = useMemo(
    () => parts.findLast((part) => part.trace_mode)?.trace_mode || 'default',
    [parts],
  );
  const visibleParts = useMemo(
    () =>
      parts.filter(
        (part) => part.type === 'message' || part.type === 'error',
      ),
    [parts],
  );
  const messageContent = useMemo(
    () =>
      visibleParts
        .filter((part) => part.type === 'message')
        .map((part) => part.data || '')
        .join(''),
    [visibleParts],
  );
  const errorParts = useMemo(
    () => visibleParts.filter((part) => part.type === 'error'),
    [visibleParts],
  );
  const copyText = useMemo(
    () => sanitizeAssistantMessageContentByMode(messageContent, traceMode),
    [messageContent, traceMode],
  );
  const embeddedMermaid = useMemo(
    () => extractAssistantMermaidBlocks(messageContent)[0] || null,
    [messageContent],
  );
  const hasReferences = !_.isEmpty(references);
  const referenceRows = useMemo(() => prepareReferenceRows(references), [references]);
  const [requestedRowId, setRequestedRowId] = useState<string | null>(null);
  const [requestVersion, setRequestVersion] = useState(0);
  const [sourcesOpen, setSourcesOpen] = useState(false);
  const [support, setSupport] = useState<TraceSupportPayload | null>(null);
  const displayText = useMemo(
    () =>
      annotateAnswerWithCitations(
        copyText,
        support?.conclusions || [],
        referenceRows,
      ),
    [copyText, referenceRows, support?.conclusions],
  );
  const getPartKey = (part: ChatMessage, index: number) =>
    part.part_id ||
    part.id ||
    `${part.role}:${part.type}:${part.timestamp ?? 'na'}:${index}`;
  const handleCitationClick = useCallback((rowId: string) => {
    setRequestedRowId(rowId);
    setRequestVersion((current) => current + 1);
    setSourcesOpen(true);
  }, []);

  useEffect(() => {
    setRequestedRowId(null);
    setRequestVersion(0);
    setSourcesOpen(false);
    setSupport(null);
  }, [traceMode, references]);

  return (
    <div className="flex w-max flex-row gap-4">
      <div>
        <div className="bg-muted text-muted-foreground relative flex size-12 flex-col justify-center rounded-full">
          {loading && (
            <LoaderCircle className="absolute -left-1 size-14 animate-spin opacity-20" />
          )}
          <Bot className={cn('size-6 self-center')} />
        </div>
      </div>
      <div className="flex max-w-sm flex-col gap-1 sm:max-w-lg md:max-w-2xl lg:max-w-3xl xl:max-w-4xl">
        <Card className="dark:border-card/0 block gap-0 px-4 py-4 text-sm">
          <div className="mb-3 flex items-center gap-2">
            <div className="flex items-center gap-2">
              <span className="text-muted-foreground text-[11px] font-semibold tracking-[0.18em] uppercase">
                {t('trace_mode_label')}
              </span>
              <Badge variant="secondary" className="rounded-full">
                {t(`trace_modes.${traceMode}`)}
              </Badge>
            </div>
          </div>
          {messageContent ? (
            <MessagePartAi
              key="assistant-message"
              part={{
                ...(visibleParts.find((part) => part.type === 'message') || {}),
                type: 'message',
                data: displayText,
              }}
              loading={loading}
              onCitationClick={handleCitationClick}
            />
          ) : pending ? (
            <div className="flex flex-row gap-2 py-2">
              <div className="bg-muted-foreground animate-caret-blink size-2 rounded-full delay-0"></div>
              <div className="bg-muted-foreground animate-caret-blink size-2 rounded-full delay-200"></div>
              <div className="bg-muted-foreground animate-caret-blink size-2 rounded-full delay-400"></div>
            </div>
          ) : null}
          {errorParts.map((part, index) => (
            <MessagePartAi
              key={getPartKey(part, index)}
              part={part}
              loading={loading}
            />
          ))}
        </Card>
        <div className="flex flex-row items-center gap-2">
          <MessageTimestamp parts={parts} className="mr-2" />
          <Separator
            orientation="vertical"
            className="data-[orientation=vertical]:h-4"
          />
          <MessageFeedback
            parts={parts}
            hanldeMessageFeedback={hanldeMessageFeedback}
          />
          <Separator
            orientation="vertical"
            className="data-[orientation=vertical]:h-4"
          />
          <CopyToClipboard
            variant="ghost"
            className="text-muted-foreground"
            text={copyText}
          />
          {hasReferences ? (
            <>
              <Separator
                orientation="vertical"
                className="data-[orientation=vertical]:h-4"
              />
              <Button
                variant="ghost"
                size="sm"
                className="text-muted-foreground h-8 gap-1.5 px-2"
                onClick={() => setSourcesOpen(true)}
              >
                {t('answer_support.evidence_title')}
                <Badge variant="secondary" className="rounded-full px-1.5 py-0 text-[10px]">
                  {referenceRows.length}
                </Badge>
              </Button>
            </>
          ) : null}
        </div>
        {(copyText || embeddedMermaid || hasReferences) ? (
          <MessageAnswerSupport
            references={references}
            answer={copyText}
            question={question}
            traceMode={traceMode}
            embeddedMermaid={embeddedMermaid}
            requestedRowId={requestedRowId}
            requestVersion={requestVersion}
            sourcesOpen={sourcesOpen}
            onSourcesOpenChange={setSourcesOpen}
            onSupportChange={setSupport}
          />
        ) : null}
      </div>
    </div>
  );
};
