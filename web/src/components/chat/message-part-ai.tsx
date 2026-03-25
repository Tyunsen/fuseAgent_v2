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

export const sanitizeAssistantMessageContent = (content: string): string => {
  let cleaned = content
    .replace(THINK_BLOCK_PATTERN, '')
    .replace(TRAILING_SOURCE_SECTION_PATTERN, '');

  const markerIndexes = TRAILING_SOURCE_MARKERS.map((marker) =>
    cleaned.indexOf(marker),
  ).filter((index) => index >= 0);
  if (markerIndexes.length > 0) {
    cleaned = cleaned.slice(0, Math.min(...markerIndexes));
  }

  return cleaned.replace(/\n{3,}/g, '\n\n').trim();
};

export const MessagePartAi = ({
  part,
}: {
  part: ChatMessage;
  loading: boolean;
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
      return <Markdown>{sanitizeAssistantMessageContent(part.data || '')}</Markdown>;
    case 'stop':
      return '';
    default:
      return part.data;
  }
};
