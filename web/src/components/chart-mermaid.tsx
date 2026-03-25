'use client';

import { cn } from '@/lib/utils';
import { RotateCcw, ZoomIn, ZoomOut } from 'lucide-react';
import mermaid from 'mermaid';
import { useTranslations } from 'next-intl';
import { useTheme } from 'next-themes';
import panzoom from 'panzoom';
import { useCallback, useEffect, useRef, useState } from 'react';
import './chart-mermaid.css';
import { Card } from './ui/card';
import { Tabs, TabsContent, TabsList, TabsTrigger } from './ui/tabs';

export const ChartMermaid = ({ children }: { children: string }) => {
  const [svg, setSvg] = useState('');
  const [error, setError] = useState(false);
  const [tab, setTab] = useState('graph');
  const [id, setId] = useState<string>();
  const [scale, setScale] = useState(1);
  const stageRef = useRef<HTMLDivElement>(null);
  const viewportRef = useRef<HTMLDivElement>(null);
  const panzoomRef = useRef<ReturnType<typeof panzoom> | null>(null);
  const { resolvedTheme } = useTheme();
  const t = useTranslations('components.dmermaid');

  const renderMermaid = useCallback(async () => {
    if (!id) {
      return;
    }

    const isDark = resolvedTheme === 'dark';

    try {
      mermaid.initialize({
        startOnLoad: true,
        theme: 'base',
        securityLevel: 'loose',
        themeVariables: {
          background: 'transparent',
          primaryColor: isDark ? '#17212b' : '#fff4ec',
          primaryBorderColor: isDark ? '#fb923c' : '#ff6b35',
          primaryTextColor: isDark ? '#f8fafc' : '#0f172a',
          secondaryColor: isDark ? '#132b3b' : '#eef6ff',
          secondaryBorderColor: isDark ? '#38bdf8' : '#004e89',
          tertiaryColor: isDark ? '#133126' : '#eefbf6',
          tertiaryBorderColor: isDark ? '#34d399' : '#1a936f',
          fontFamily: 'inherit',
          fontSize: '16px',
          lineColor: isDark ? '#64748b' : '#475569',
          nodeTextColor: isDark ? '#f8fafc' : '#0f172a',
          clusterBkg: isDark ? '#0f172a' : '#f8fafc',
          clusterBorder: isDark ? '#334155' : '#cbd5e1',
          clusterTextColor: isDark ? '#e2e8f0' : '#334155',
          edgeLabelBackground: 'transparent',
        },
        themeCSS: `
          .labelBkg { background: none !important; }
          .edgeLabel, .edgeLabel p {
            background: transparent !important;
            color: ${isDark ? '#cbd5e1' : '#334155'} !important;
            font-weight: 600;
          }
          .nodeLabel, .label, .cluster-label {
            color: ${isDark ? '#f8fafc' : '#0f172a'} !important;
            font-weight: 600;
          }
        `,
        flowchart: {
          curve: 'basis',
          nodeSpacing: 36,
          rankSpacing: 48,
          padding: 18,
          htmlLabels: true,
        },
      });
      const rendered = await mermaid.render(
        `mermaid-container-${id}`,
        children,
      );
      setSvg(rendered.svg);
      setError(false);
    } catch (err) {
      console.log(err);
      setError(true);
    }
  }, [children, id, resolvedTheme]);

  useEffect(() => {
    setId(String((Math.random() * 100000).toFixed(0)));
  }, []);

  useEffect(() => {
    void renderMermaid();
  }, [renderMermaid]);

  useEffect(() => {
    const viewport = viewportRef.current;
    if (!viewport || !svg) {
      return;
    }

    panzoomRef.current?.dispose();

    const instance = panzoom(viewport, {
      minZoom: 0.75,
      maxZoom: 3.5,
      smoothScroll: false,
      zoomDoubleClickSpeed: 1,
    });
    panzoomRef.current = instance;

    const syncScale = () => {
      setScale(instance.getTransform().scale);
    };

    instance.on('transform', syncScale);
    instance.moveTo(0, 0);
    instance.zoomAbs(0, 0, 1);
    syncScale();

    return () => {
      instance.off('transform', syncScale);
      instance.dispose();
      panzoomRef.current = null;
    };
  }, [svg]);

  const zoomBy = useCallback((factor: number) => {
    const instance = panzoomRef.current;
    const stage = stageRef.current;
    if (!instance || !stage) {
      return;
    }
    instance.smoothZoom(stage.clientWidth / 2, stage.clientHeight / 2, factor);
  }, []);

  const resetViewport = useCallback(() => {
    const instance = panzoomRef.current;
    if (!instance) {
      return;
    }
    instance.moveTo(0, 0);
    instance.zoomAbs(0, 0, 1);
    setScale(1);
  }, []);

  return (
    <Tabs value={tab} className="font-sans" onValueChange={setTab}>
      <div className="mb-3 flex flex-wrap items-center justify-between gap-3">
        <TabsList className="h-9 rounded-full border border-stone-200/80 bg-stone-100/90 p-1">
          <TabsTrigger value="graph" className="rounded-full px-4">
            {t('graph')}
          </TabsTrigger>
          <TabsTrigger value="data" className="rounded-full px-4">
            {t('data')}
          </TabsTrigger>
        </TabsList>

        <div className="flex items-center gap-2">
          <div className="text-muted-foreground rounded-full border border-stone-200 bg-white px-3 py-1 text-xs font-medium">
            {Math.round(scale * 100)}%
          </div>
          <div className="flex items-center gap-1 rounded-full border border-stone-200 bg-white/95 p-1 shadow-sm">
            <button
              type="button"
              className="mermaid-board__tool"
              onClick={() => zoomBy(0.9)}
              aria-label="Zoom out"
            >
              <ZoomOut className="size-4" />
            </button>
            <button
              type="button"
              className="mermaid-board__tool"
              onClick={resetViewport}
              aria-label="Reset view"
            >
              <RotateCcw className="size-4" />
            </button>
            <button
              type="button"
              className="mermaid-board__tool"
              onClick={() => zoomBy(1.1)}
              aria-label="Zoom in"
            >
              <ZoomIn className="size-4" />
            </button>
          </div>
        </div>
      </div>

      <TabsContent
        value="graph"
        forceMount
        className={tab === 'graph' ? 'block' : 'hidden'}
      >
        <Card className="mermaid-board my-2 overflow-hidden border-stone-200/80 bg-stone-50/95 p-0 shadow-[0_18px_50px_rgba(15,23,42,0.08)]">
          <div className="mermaid-stage">
            <div className="mermaid-stage__toolbar">
              <div className="mermaid-stage__hint">
                Drag to pan. Scroll to zoom.
              </div>
            </div>
            <div
              ref={stageRef}
              className="mermaid-stage__viewport rounded-[24px] border border-white/80 bg-white/90 shadow-[inset_0_1px_0_rgba(255,255,255,0.95),0_16px_40px_rgba(15,23,42,0.08)]"
            >
              {error ? (
                <div className="mermaid-stage__error">
                  <div className="text-sm font-semibold text-slate-900">
                    Mermaid render failed.
                  </div>
                  <div className="mt-1 text-sm text-slate-500">
                    Switch to the data tab to inspect the source.
                  </div>
                </div>
              ) : (
                <div
                  ref={viewportRef}
                  className={cn('mermaid-viewport', `mermaid-container-${id}`)}
                  dangerouslySetInnerHTML={{ __html: svg }}
                />
              )}
            </div>
          </div>
        </Card>
      </TabsContent>

      <TabsContent value="data">
        <Card className="my-2 rounded-[24px] border-stone-200/80 bg-stone-950/95 p-0 text-stone-100 shadow-[0_18px_40px_rgba(15,23,42,0.12)]">
          <div className="border-b border-white/10 px-4 py-3 text-xs font-semibold tracking-[0.18em] text-stone-400 uppercase">
            Mermaid
          </div>
          <code
            className={cn(
              'hljs language-mermaid block overflow-x-auto px-4 py-4 text-sm leading-6',
            )}
          >
            {children}
          </code>
        </Card>
      </TabsContent>
    </Tabs>
  );
};
