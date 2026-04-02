<!--
同步影响报告
版本变更：1.1.0 -> 1.2.0
已修改原则：
- 无重命名；工作流门禁已扩展，以便在可运行行为发生变化时强制要求 implement 后启动服务
新增章节：
- VII. 实现后服务可用性
移除章节：
- 无
需要更新的模板：
- .specify/templates/plan-template.md 已更新
- .specify/templates/spec-template.md 无需更新
- .specify/templates/tasks-template.md 已更新
- .specify/templates/commands/*.md 待处理（本仓库中不存在该目录）
- AGENTS.md 已更新
- README.md 无需更新
后续 TODO：
- 无
-->
# fuseAgent 宪章

## 核心原则

### I. 业务需求优先，默认采用增量交付
每一个 `/speckit.specify` feature 都 MUST 映射到当前被请求的业务增量，以及
`BUSINESS-REQUIREMENTS.md` 中对应的相关章节。plan、tasks 和 implementation
都 MUST 严格限制在这一增量切片之内；无关需求 MUST 明确标注为 out of scope，
而不能被打包进同一个 feature。
在 feature spec 已存在之后，`/speckit.plan`、`/speckit.tasks` 和 implement
可以自动化执行，但仅限于这个已经批准的增量，不得扩展到整个产品 backlog。

这样可以保持范围可审查，避免一次性过度建设，从而掩盖未完成或未获批准的工作。

### II. 先复用参考实现，再考虑新增代码
在引入新的架构、模块或 UI 之前，贡献者 MUST 先评估是否可以通过复用或改造
`E:\codes\fuseAgent_v2\LightRAG`、
`E:\codes\fuseAgent_v2\llm-graph-builder` 或
`E:\codes\fuseAgent_v2\MiroFish` 中的代码与模式来满足需求。
重要 plan MUST 写明候选复用来源，并明确说明将复制、封装或改造哪些部分。
只有当复用对当前增量确实不可行时，才允许新增代码；并且这个原因 MUST 记录在
plan 或 task 备注中。

这样可以加快交付速度，减少不必要的重复造轮子，并让实现建立在已经验证过的代码路径之上。

### III. 统一的答案、证据、图谱产品契约
fuseAgent MUST 作为一个面向内部用户的单一知识库问答产品交付，而不是一个底层引擎对比界面。
所有面向用户的 Q&A 增量都 MUST 保持 `BUSINESS-REQUIREMENTS.md` 中定义的产品契约：
答案文本、可追溯证据以及相关图谱必须构成一个连贯的整体结果。
当证据不足时，系统 MUST 明确输出 “current evidence insufficient” 或产品批准使用的中文等价表达，
并且 MUST NOT 编造支撑内容。
除非用户明确扩大范围，否则 v1 MUST 继续聚焦于单知识库问答、文档管理、
证据可追溯性，以及 PDF、Word、Markdown、TXT 文档的图谱查看。

这样可以守住产品的核心承诺，防止用户体验漂移成研究型控制台。

### IV. UI 变更必须获得明确授权
如果用户没有提供明确的 UI 要求，贡献者 MUST NOT 自行发明新的 UI 流程、
视觉概念或带猜测性质的交互模式。
获批的 UI 工作 MUST 与业务需求和已命名的参考实现保持一致：
整体产品 UI 参考 ApeRAG 和已提供的原型；图谱相关 UI 参考 MiroFish。
spec 和 plan MUST 记录该 feature 属于 `No UI change`、`UI parity/adaptation`
还是 `New approved UI work`；任何超出该声明范围的 UI task 都视为不合规。

这样可以避免不必要的设计漂移，并确保实现忠实于产品负责人的意图。

### V. 以真实服务器环境为准，不能凭假设设计
运维计划、脚本和部署步骤 MUST 以用户提供的服务器参考文件为事实来源，
除非用户明确覆盖它。
新的服务器相关工作 MUST 限制在 `/home/common/jyzhu/ucml` 目录下，优先使用当前空闲 GPU，
并且当远程服务需要访问时，MUST 包含到某个可用本地端口的 port-forwarding。
feature 的设计 MUST 基于真实服务器和实际资源边界，而不是基于想当然的基础设施假设。

这样可以保证交付方案扎根于最终真正运行系统的环境。

### VI. 默认中文优先沟通
所有与用户的交互沟通，包括澄清问题、选项展示、状态报告和决策提示，
默认都 MUST 使用中文。
这适用于 `/speckit.clarify` 的问题、`/speckit.plan` 的决策点、
`/speckit.tasks` 的检查点总结，以及任何其他需要用户输入或向用户提供引导的工作流步骤。
像代码名、文件路径和英文技术术语这类技术标识，在翻译会降低清晰度时 MAY 保持英文。

这样可以确保产品负责人能在偏好的工作语言下高效审阅和响应，而不需要额外翻译成本。

### VII. 实现后服务可用性
当完成任何较大的 `/speckit.implement` 增量，或任何会实质改变系统可运行行为的用户请求实现任务之后，
贡献者 MUST 启动或重启最新适用的服务栈，以便用户进行验证；
除非用户明确表示不需要，或者环境条件使启动不可行。
交付说明 MUST 写清楚：启动了什么服务或服务栈、使用了什么命令、用户如何访问，以及任何已知限制。
如果启动失败，贡献者 MUST 明确报告具体阻塞点和失败的启动命令，
而不能在只完成代码和测试后静默结束。

这样可以避免验证被卡住，并确保实现交付的终点是一个可用运行时，而不只是源码变更。

## 实现边界

- `BUSINESS-REQUIREMENTS.md` 是 fuseAgent 的产品范围总控文档。
- 默认技术方向是：检索与问答以 LightRAG 为中心；抽取与图构建以 MiroFish 为中心；
  `llm-graph-builder` 仅在图谱、摄取和产品模式上做选择性参考。
- 除非用户明确要求内部评估界面，否则最终产品 MUST 对终端用户隐藏底层引擎切换能力。
- v1 默认面向内部管理员使用、单知识库工作流，以及 `BUSINESS-REQUIREMENTS.md`
  中已经列出的文档格式。
- 多租户能力、复杂角色系统、图像优先理解，以及带猜测性质的平台化扩展，
  在用户明确提出之前都属于 out of scope。

## 开发工作流与质量门禁

- 每一个 feature spec MUST 包含业务需求可追溯性、已批准的增量、明确的 out-of-scope 项、
  候选复用来源，以及 UI 范围声明。
- 每一个 implementation plan MUST 通过 constitution check，明确回答：
  当前构建的是哪个增量、将复用哪些现有代码、允许的 UI 范围是什么、适用哪些服务器约束、
  用什么验证证明变更成立，以及当可运行行为发生变化时，用户验证需要采用什么运行时启动步骤。
- 每一个 task list MUST 按照能够在某个 user story 或 checkpoint 之后干净停止的方式排序；
  严禁夹带与当前增量无关的 backlog 扩张。
- 每个实现增量 MUST 包含证明已修改行为成立所需的最小可重复验证。
  任何涉及答案、证据、图谱关联或部署的变更，都 MUST 包含这些行为的显式验证。
- 每个会改变可运行行为的实现增量，都 MUST 包含启动或重启步骤，
  以保证最新服务对用户可验证；如果没有适用的可运行服务，则 MUST 记录原因。
- 合并或交付审查 MUST 确认是否符合本宪章，并在相关的 plan、task list 或 review note 中
  记录任何已批准的例外情况。

## 治理

本宪章覆盖本仓库中 spec、plan、tasks 和 implementation 决策的本地默认行为。
任何修订都需要用户明确批准，并同步更新受影响的模板后，才视为正式生效。
版本号遵循如下语义规则：
MAJOR 用于不兼容的原则变更或删除，
MINOR 用于新增原则或实质扩展的指导，
PATCH 用于不改变实际工作预期的澄清。
所有生成或手工修改的 spec、plan、tasks 文件以及 implementation review，
都必须经过合规性审查。

**Version**: 1.2.0 | **Ratified**: 2026-03-21 | **Last Amended**: 2026-04-02
