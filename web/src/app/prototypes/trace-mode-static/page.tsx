'use client';

import { ChartMermaid } from '@/components/chart-mermaid';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from '@/components/ui/card';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Copy, ThumbsDown, ThumbsUp } from 'lucide-react';
import Link from 'next/link';

const query = '@col16b4b2eee2ce593f 伊朗发生了什么';

const defaultFlowchart = `graph TD
  A["2026年伊朗战争"] --> B["战争开局"]
  A --> C["核设施受损"]
  A --> D["霍尔木兹海峡博弈"]
  A --> E["地区外溢"]
  D --> F["能源价格冲击"]
`;

const spaceFlowchart = `graph TD
  A["伊朗"] --> B["德黑兰空袭"]
  A --> C["纳坦兹核设施受损"]
  A --> D["霍尔木兹海峡管控"]
  D --> E["迪拜/巴林/巴士拉受波及"]
`;

const timeGantt = `gantt
dateFormat YYYY-MM-DD
axisFormat %m-%d
title 事件甘特图
section 2026年3月
美以发动联合突袭 : task_1, 2026-02-28, 1d
纳坦兹核设施受损 : task_2, 2026-03-02, 1d
德黑兰再遭密集空袭 : task_3, 2026-03-06, 1d
莫杰塔巴继任最高领袖 : task_4, 2026-03-08, 1d
霍尔木兹海峡局势紧张 : task_5, 2026-03-10, 1d
海湾商业基础设施遭袭 : task_6, 2026-03-11, 1d
伊朗提出停战条件 : task_7, 2026-03-12, 1d
多战场持续交火 : task_8, 2026-03-13, 1d
`;

const timeTableRows = [
  {
    date: '2026年2月28日',
    title: '美以发动联合突袭',
    detail:
      '美国与以色列对伊朗发动大规模联合打击，目标包括导弹基础设施、军事设施、德黑兰周边领导层目标以及与核计划有关的节点。[1][5]',
  },
  {
    date: '2026年3月2日',
    title: '纳坦兹核设施受损',
    detail:
      '卫星图像显示纳坦兹园区多处建筑受损，国际原子能机构随后确认设施出现新损伤。[1][11]',
  },
  {
    date: '2026年3月6日',
    title: '德黑兰再遭密集空袭',
    detail:
      '战争持续约 10 天后，德黑兰再次遭遇密集空袭，伊朗同步扩大对以色列与海湾目标的反击。',
  },
  {
    date: '2026年3月8日',
    title: '莫杰塔巴·哈梅内伊继任最高领袖',
    detail:
      '阿里·哈梅内伊死亡后，莫杰塔巴·哈梅内伊成为新最高领袖，并释放更强硬的战争信号。',
  },
  {
    date: '2026年3月10日',
    title: '霍尔木兹海峡局势紧张',
    detail:
      '伊朗把霍尔木兹海峡作为战争杠杆，美方则称摧毁伊朗布雷船只，全球油价迅速飙升。',
  },
  {
    date: '2026年3月11日',
    title: '海湾商业基础设施遭袭',
    detail:
      '迪拜国际机场周边、巴林穆哈拉格岛、巴士拉港等商业和民用设施受到波及。',
  },
  {
    date: '2026年3月12日',
    title: '伊朗提出停战条件',
    detail:
      '伊朗总统提出停战条件，要求承认伊朗合法权利、支付赔偿并提供不再攻击的国际保证。',
  },
  {
    date: '2026年3月13日',
    title: '多战场持续交火',
    detail:
      '真主党继续对以色列加大火箭弹和导弹发射，以色列同步扩大对黎巴嫩南部的打击。',
  },
];

function UserBubble() {
  return (
    <div className="flex justify-end">
      <div className="max-w-3xl rounded-2xl bg-sky-600 px-4 py-3 text-sm font-medium text-white shadow-sm">
        {query}
      </div>
    </div>
  );
}

function MetaRow() {
  return (
    <div className="flex items-center gap-3 text-xs text-slate-500">
      <span>2026年4月5日 19:43:55</span>
      <ThumbsUp className="size-4" />
      <ThumbsDown className="size-4" />
      <Copy className="size-4" />
      <button
        type="button"
        className="font-medium text-slate-700 transition-colors hover:text-slate-900"
      >
        参考文档来源
      </button>
    </div>
  );
}

function TimelineTable() {
  return (
    <section className="space-y-3">
      <div className="text-lg font-semibold text-slate-900">关键事件时间表</div>
      <div className="space-y-0">
        {timeTableRows.map((row) => (
          <div
            key={`${row.date}-${row.title}`}
            className="grid grid-cols-[150px_minmax(0,220px)_1fr] gap-4 border-b border-slate-200/80 px-2 py-4 last:border-b-0"
          >
            <div className="text-xs font-semibold tracking-[0.08em] text-slate-500 uppercase">
              {row.date}
            </div>
            <div className="text-sm font-semibold text-slate-900">
              {row.title}
            </div>
            <p className="text-sm leading-6 text-slate-600">{row.detail}</p>
          </div>
        ))}
      </div>
    </section>
  );
}

function EntityGraphMock() {
  return (
    <div className="rounded-2xl border border-white/90 bg-white/90 p-5">
      <svg viewBox="0 0 760 340" className="w-full">
        <line x1="180" y1="160" x2="320" y2="120" stroke="#94a3b8" strokeWidth="2" />
        <line x1="180" y1="160" x2="320" y2="210" stroke="#94a3b8" strokeWidth="2" />
        <line x1="320" y1="120" x2="500" y2="90" stroke="#94a3b8" strokeWidth="2" />
        <line x1="320" y1="210" x2="500" y2="250" stroke="#94a3b8" strokeWidth="2" />
        <line x1="500" y1="90" x2="610" y2="150" stroke="#94a3b8" strokeWidth="2" />
        <line x1="500" y1="250" x2="610" y2="150" stroke="#94a3b8" strokeWidth="2" />

        {[
          { x: 180, y: 160, label: '伊朗', fill: '#fde68a' },
          { x: 320, y: 120, label: '美国', fill: '#bfdbfe' },
          { x: 320, y: 210, label: '以色列', fill: '#fecaca' },
          { x: 500, y: 90, label: '霍尔木兹海峡', fill: '#fed7aa' },
          { x: 500, y: 250, label: '革命卫队', fill: '#ddd6fe' },
          { x: 610, y: 150, label: '海湾国家', fill: '#bbf7d0' },
        ].map((node) => (
          <g key={node.label}>
            <circle cx={node.x} cy={node.y} r="34" fill={node.fill} stroke="#334155" strokeWidth="2" />
            <text
              x={node.x}
              y={node.y + 5}
              textAnchor="middle"
              fontSize="14"
              fontWeight="700"
              fill="#0f172a"
            >
              {node.label}
            </text>
          </g>
        ))}
      </svg>
    </div>
  );
}

function AnswerCard({
  modeLabel,
  title,
  summary,
  children,
}: {
  modeLabel: string;
  title: string;
  summary: string;
  children: React.ReactNode;
}) {
  return (
    <Card className="rounded-[28px] border-stone-200/80 bg-[linear-gradient(180deg,rgba(255,255,255,0.96),rgba(248,250,252,0.98))] shadow-[0_24px_60px_rgba(15,23,42,0.08)]">
      <CardHeader className="gap-3 border-b border-stone-200/70 pb-5">
        <div className="flex items-center gap-2">
          <span className="text-xs font-semibold tracking-[0.14em] text-slate-500 uppercase">
            模式
          </span>
          <Badge variant="secondary" className="rounded-full">
            {modeLabel}
          </Badge>
        </div>
        <CardTitle className="text-4xl font-semibold text-slate-950">
          {title}
        </CardTitle>
        <CardDescription className="max-w-3xl text-sm leading-6 text-slate-600">
          {summary}
        </CardDescription>
      </CardHeader>
      <CardContent className="space-y-6">{children}</CardContent>
    </Card>
  );
}

export default function TraceModeStaticPrototypePage() {
  return (
    <main className="min-h-screen bg-[radial-gradient(circle_at_top,rgba(14,165,233,0.08),transparent_35%),linear-gradient(180deg,#f8fafc,#eef2ff)] px-6 py-10">
      <div className="mx-auto max-w-6xl space-y-8">
        <div className="space-y-3">
          <Badge variant="outline" className="rounded-full border-sky-200 bg-white/80 px-3 py-1">
            静态原型
          </Badge>
          <h1 className="text-4xl font-semibold tracking-tight text-slate-950">
            Trace Mode UI Prototype
          </h1>
          <p className="max-w-4xl text-sm leading-6 text-slate-600">
            这是一张纯静态页面，只用于确认 4 个模式的 UI 结构，不连接后端，不依赖真实问答结果。
            问题固定为 <span className="font-medium text-slate-900">{query}</span>。
          </p>
        </div>

        <Tabs defaultValue="time" className="gap-6">
          <TabsList className="h-11 rounded-full border border-stone-200 bg-white/85 p-1 shadow-sm">
            <TabsTrigger value="default" className="rounded-full px-5">
              默认模式
            </TabsTrigger>
            <TabsTrigger value="time" className="rounded-full px-5">
              时间脉络
            </TabsTrigger>
            <TabsTrigger value="space" className="rounded-full px-5">
              空间脉络
            </TabsTrigger>
            <TabsTrigger value="entity" className="rounded-full px-5">
              实体脉络
            </TabsTrigger>
          </TabsList>

          <TabsContent value="default" className="space-y-6">
            <UserBubble />
            <AnswerCard
              modeLabel="默认模式"
              title="伊朗发生了什么"
              summary="默认模式下，回答以综合摘要为主，主图使用流程拓扑图，底部保留时间戳和来源入口。"
            >
              <div className="space-y-4 text-sm leading-7 text-slate-700">
                <p>
                  根据当前知识库，伊朗当前处在 2026 年与美国、以色列持续升级的军事冲突中心，
                  关键变化集中在战争开局、核设施受损、霍尔木兹海峡博弈和地区外溢四个方面。[1][3]
                </p>
              </div>
              <section className="space-y-3">
                <div className="text-lg font-semibold text-slate-900">回答关联图谱</div>
                <ChartMermaid>{defaultFlowchart}</ChartMermaid>
              </section>
              <MetaRow />
            </AnswerCard>
          </TabsContent>

          <TabsContent value="time" className="space-y-6">
            <UserBubble />
            <AnswerCard
              modeLabel="时间脉络"
              title="伊朗发生了什么"
              summary="时间脉络原型里，回答大卡片内部只保留两个固定区块：关键事件时间表和事件甘特图。其他时间模式图卡全部删除。"
            >
              <TimelineTable />
              <section className="space-y-3">
                <div className="text-lg font-semibold text-slate-900">事件甘特图</div>
                <ChartMermaid>{timeGantt}</ChartMermaid>
              </section>
              <MetaRow />
            </AnswerCard>
          </TabsContent>

          <TabsContent value="space" className="space-y-6">
            <UserBubble />
            <AnswerCard
              modeLabel="空间脉络"
              title="伊朗发生了什么"
              summary="空间脉络沿用默认模式壳层，只在正文里突出地点线索，主图仍然是流程拓扑图。"
            >
              <div className="space-y-4 text-sm leading-7 text-slate-700">
                <p>
                  这场冲突已经从伊朗本土外溢到纳坦兹、德黑兰、霍尔木兹海峡以及多个海湾商业节点，
                  地理扩散速度极快。[2][4]
                </p>
              </div>
              <section className="space-y-3">
                <div className="text-lg font-semibold text-slate-900">地点关联流程图</div>
                <ChartMermaid>{spaceFlowchart}</ChartMermaid>
              </section>
              <MetaRow />
            </AnswerCard>
          </TabsContent>

          <TabsContent value="entity" className="space-y-6">
            <UserBubble />
            <AnswerCard
              modeLabel="实体脉络"
              title="伊朗发生了什么"
              summary="实体脉络保留回答摘要和一个知识图谱子图主区，不展示时间模式那套时间表/甘特图。"
            >
              <div className="space-y-4 text-sm leading-7 text-slate-700">
                <p>
                  本轮回答会围绕伊朗、美国、以色列、革命卫队、霍尔木兹海峡和海湾国家等核心实体展开，
                  并把它们之间的关键边和关系一起展示出来。[1][5]
                </p>
              </div>
              <section className="space-y-3">
                <div className="text-lg font-semibold text-slate-900">知识图谱子图</div>
                <EntityGraphMock />
              </section>
              <MetaRow />
            </AnswerCard>
          </TabsContent>
        </Tabs>

        <div className="flex gap-3">
          <Button asChild>
            <Link href="/workspace/bots/bot433e730ee62fb944/chats/chat82fcbb6854b16311">
              回到真实时间模式页
            </Link>
          </Button>
          <Button asChild variant="outline">
            <Link href="/workspace">返回工作区</Link>
          </Button>
        </div>
      </div>
    </main>
  );
}
