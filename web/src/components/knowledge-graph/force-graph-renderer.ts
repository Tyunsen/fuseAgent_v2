'use client';

import Color from 'color';
import * as d3 from 'd3';

export const GRAPH_NODE_MIN = 10;
export const GRAPH_NODE_MAX = 30;
export const GRAPH_NODE_FONT_MIN = 7;
export const GRAPH_NODE_FONT_MAX = 13;

type GraphNodeEndpoint = string | number | { id?: string | number } | undefined;

export interface KnowledgeGraphNodeLike {
  id: string;
  properties?: {
    entity_name?: string;
    entity_type?: string;
    [key: string]: unknown;
  };
  value?: number;
  x?: number;
  y?: number;
}

export interface KnowledgeGraphEdgeLike {
  id: string;
  source: GraphNodeEndpoint;
  target: GraphNodeEndpoint;
  type?: string;
  properties?: {
    description?: string;
    [key: string]: unknown;
  };
}

export const createKnowledgeGraphColorScale = () =>
  d3.scaleOrdinal<string, string>(d3.schemeTableau10);

export const resolveKnowledgeGraphNodeId = (
  value: GraphNodeEndpoint,
): string | undefined => {
  if (typeof value === 'string') {
    return value;
  }
  if (typeof value === 'number') {
    return String(value);
  }
  if (value && typeof value === 'object' && 'id' in value) {
    const nodeId = value.id;
    if (typeof nodeId === 'string' || typeof nodeId === 'number') {
      return String(nodeId);
    }
  }
  return undefined;
};

export const getKnowledgeGraphNodeDisplayName = (
  node?: Partial<KnowledgeGraphNodeLike> | null,
) => String(node?.properties?.entity_name || node?.id || '');

export const getKnowledgeGraphEntityType = (
  node?: Partial<KnowledgeGraphNodeLike> | null,
) => String(node?.properties?.entity_type || 'Entity');

export const renderKnowledgeGraphNode = <TNode extends KnowledgeGraphNodeLike>({
  node,
  ctx,
  colorScale,
  resolvedTheme,
  isNodeHighlighted,
  isNodeHovered,
}: {
  node: TNode;
  ctx: CanvasRenderingContext2D;
  colorScale: d3.ScaleOrdinal<string, string>;
  resolvedTheme?: string;
  isNodeHighlighted?: (node: TNode) => boolean;
  isNodeHovered?: (node: TNode) => boolean;
}) => {
  const x = node.x || 0;
  const y = node.y || 0;
  const nodeSize = Math.min(node.value || GRAPH_NODE_MIN, GRAPH_NODE_MAX);
  const hovered = isNodeHovered?.(node) || false;
  const highlighted = isNodeHighlighted?.(node) ?? true;
  const size = hovered ? nodeSize + 1.25 : nodeSize;

  ctx.beginPath();
  ctx.arc(x, y, size, 0, 2 * Math.PI, false);

  const tone = colorScale(getKnowledgeGraphEntityType(node));
  const mutedTone =
    resolvedTheme === 'dark'
      ? Color(tone).desaturate(0.45).lighten(0.05)
      : Color(tone).desaturate(0.55).darken(0.12);

  ctx.fillStyle = highlighted ? tone : mutedTone.string();
  ctx.fill();

  ctx.beginPath();
  ctx.arc(x, y, size, 0, 2 * Math.PI, false);
  ctx.lineWidth = highlighted ? 2 : 1;
  ctx.strokeStyle =
    resolvedTheme === 'dark'
      ? highlighted
        ? 'rgba(250, 250, 250, 0.92)'
        : 'rgba(24, 24, 27, 0.88)'
      : highlighted
        ? 'rgba(24, 24, 27, 0.88)'
        : 'rgba(113, 113, 122, 0.72)';
  ctx.stroke();

  const nodeLabel = getKnowledgeGraphNodeDisplayName(node);
  let fontSize = Math.max(
    GRAPH_NODE_FONT_MIN,
    Math.min(GRAPH_NODE_FONT_MAX, Math.floor(size * 0.72)),
  );
  const offset = 2;
  ctx.font = `600 ${fontSize}px Arial`;
  let textWidth = ctx.measureText(nodeLabel).width - offset;
  const maxLabelWidth = size * 1.55;
  let truncatedLabel = nodeLabel;
  while (textWidth > maxLabelWidth && truncatedLabel.length > 3) {
    truncatedLabel = `${truncatedLabel.slice(0, -4)}...`;
    textWidth = ctx.measureText(truncatedLabel).width - offset;
  }
  while (textWidth > maxLabelWidth && fontSize > GRAPH_NODE_FONT_MIN) {
    fontSize -= 1;
    ctx.font = `600 ${fontSize}px Arial`;
    textWidth = ctx.measureText(truncatedLabel).width - offset;
  }
  ctx.fillStyle = '#fff';
  ctx.fillText(
    truncatedLabel,
    x - (textWidth + offset) / 2,
    y + fontSize / 2.8,
  );
};

export const paintKnowledgeGraphNodePointerArea = <
  TNode extends KnowledgeGraphNodeLike,
>({
  node,
  paintColor,
  ctx,
}: {
  node: TNode;
  paintColor: string;
  ctx: CanvasRenderingContext2D;
}) => {
  const x = node.x || 0;
  const y = node.y || 0;
  const size = Math.min(node.value || GRAPH_NODE_MIN, GRAPH_NODE_MAX);
  ctx.fillStyle = paintColor;
  ctx.beginPath();
  ctx.arc(x, y, size, 0, 2 * Math.PI, false);
  ctx.fill();
};

export const getKnowledgeGraphLinkColor = <TEdge extends KnowledgeGraphEdgeLike>({
  link,
  resolvedTheme,
  isLinkHighlighted,
}: {
  link: TEdge;
  resolvedTheme?: string;
  isLinkHighlighted?: (link: TEdge) => boolean;
}) => {
  const highlighted = isLinkHighlighted?.(link) ?? true;
  if (resolvedTheme === 'dark') {
    return highlighted ? '#A3A3A3' : '#3F3F46';
  }
  return highlighted ? '#737373' : '#D4D4D8';
};

export const getKnowledgeGraphLinkWidth = <TEdge extends KnowledgeGraphEdgeLike>(
  link: TEdge,
  isLinkHighlighted?: (link: TEdge) => boolean,
) => (isLinkHighlighted?.(link) ?? true ? 2.5 : 1);

export const getKnowledgeGraphLinkDirectionalParticleWidth = <
  TEdge extends KnowledgeGraphEdgeLike,
>(
  link: TEdge,
  isLinkHighlighted?: (link: TEdge) => boolean,
) => (isLinkHighlighted?.(link) ?? true ? 3.5 : 0);
