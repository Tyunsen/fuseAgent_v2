import { ChatMessage } from '@/api';
import { Markdown } from '@/components/markdown';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { AlertCircleIcon } from 'lucide-react';

const THINK_BLOCK_PATTERN = /<think\b[^>]*>[\s\S]*?<\/think>/gi;
const TRAILING_SOURCE_SECTION_PATTERN =
  /(?:^|\n)(?:#{1,3}\s*|\*\*)?(?:Sources?|Source Documents?|来源(?:文档)?|参考来源|参考资料)(?:\*\*)?\s*(?:\n+|[:：]\s*\n?)[\s\S]*$/i;
const TRAILING_SOURCE_MARKERS = [
  '\n**来源文档**',
  '\n来源文档',
  '\n**来源**',
  '\n来源：',
  '\n来源:',
  '\n## 来源',
  '\n**Source Documents**',
  '\nSource Documents',
  '\n**Sources**',
  '\nSources',
  '\n## Sources',
];

const MERMAID_BLOCK_PATTERN = /```mermaid[\s\S]*?```/gi;
const GRAPH_SECTION_HEADING_PATTERN =
  /(?:^|\n)#{1,3}\s*(?:知识图可视化|Knowledge Graph Visualization)\s*\n?/gi;
const ANALYSIS_SECTION_PATTERN =
  /(?:^|\n)#{1,3}\s*(?:分析|Analysis)\s*[\s\S]*$/i;

export const extractAssistantMermaidBlocks = (content: string): string[] => {
  const matches = content.match(MERMAID_BLOCK_PATTERN) || [];
  return matches.map((match) =>
    match
      .replace(/^```mermaid\s*/i, '')
      .replace(/\s*```$/i, '')
      .trim(),
  );
};

const DIRECT_ANSWER_SECTION_PATTERN =
  /(?:^|\n)#{1,3}\s*(?:直接答案|Direct Answer)\s*([\s\S]*?)(?=\n#{1,3}\s+|$)/i;
const HORIZONTAL_RULE_PATTERN = /(?:^|\n)\s*(?:---+|\*\*\*+)\s*(?=\n|$)/;

export const sanitizeAssistantMessageContent = (content: string): string => {
  return sanitizeAssistantMessageContentByMode(content, 'default');
};

export const sanitizeAssistantMessageContentByMode = (
  content: string,
  traceMode: string,
): string => {
  let cleaned = content
    .replace(THINK_BLOCK_PATTERN, '')
    .replace(TRAILING_SOURCE_SECTION_PATTERN, '');

  const markerIndexes = TRAILING_SOURCE_MARKERS.map((marker) =>
    cleaned.indexOf(marker),
  ).filter((index) => index >= 0);
  if (markerIndexes.length > 0) {
    cleaned = cleaned.slice(0, Math.min(...markerIndexes));
  }

  cleaned = cleaned.replace(GRAPH_SECTION_HEADING_PATTERN, '\n');
  if (traceMode === 'time') {
    cleaned = cleaned.replace(MERMAID_BLOCK_PATTERN, '');
  }
  cleaned = cleaned.replace(ANALYSIS_SECTION_PATTERN, '');

  const directAnswerMatch = cleaned.match(DIRECT_ANSWER_SECTION_PATTERN);
  if (directAnswerMatch?.[1]) {
    cleaned = directAnswerMatch[1];
  }

  const separatorMatch = cleaned.search(HORIZONTAL_RULE_PATTERN);
  if (separatorMatch > 0) {
    cleaned = cleaned.slice(0, separatorMatch);
  }

  return cleaned.replace(/\n{3,}/g, '\n\n').trim();
};

export const MessagePartAi = ({
  part,
  onCitationClick,
}: {
  part: ChatMessage;
  loading: boolean;
  onCitationClick?: (rowId: string) => void;
}) => {
  switch (part.type) {
    case 'error':
      return (
        <Alert variant="destructive">
          <AlertCircleIcon />
          <AlertDescription>{part.data}</AlertDescription>
        </Alert>
      );
    case 'thinking':
      return null;
    case 'tool_call_result':
      return null;
    case 'message':
      return (
        <Markdown
          onCitationClick={({ rowId }) => onCitationClick?.(rowId)}
        >
          {sanitizeAssistantMessageContentByMode(
            part.data || '',
            part.trace_mode || 'default',
          )}
        </Markdown>
      );
    case 'stop':
      return '';
    default:
      return part.data;
  }
};
