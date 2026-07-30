# 架构设计

> Inspector（03-07-02）功能域的架构设计文档，补录已有实现。本域聚焦组件树序列化（JSON 转储）与 `@ohos.arkui.inspector` 公共能力；DFX Dump 管线（03-08-04）与无障碍能力（03-07-01）为独立功能域，本文仅在边界处交叉引用。

## 设计元数据

| 字段 | 内容 |
|------|------|
| Design ID | DESIGN-Func-03-07-02 |
| 关联需求 | 已有能力补录（无独立 requirement.md） |
| 关联 Epic | 无 |
| 目标 Feature | Feat-01 同步树转储与属性过滤、Feat-02 公共 API(NAPI/ANI)与异步采集 |
| 复杂度 | 复杂 |
| 目标版本 | API 10 起（getInspectorTree/getInspectorByKey/sendEventByKey），ANI 富 API 随静态前端落地 |
| Owner | ArkUI SIG / 引擎框架 |
| 状态 | Baselined（已有实现补录；Feat-01/02 已补） |

## 需求基线

| 项 | 内容 |
|----|------|
| 问题陈述 | DevEco Studio Inspector、自动化测试（UiSession）等下游需要一份稳定的运行时组件树 JSON 视图，并能按 key 查询单节点、向指定节点注入事件 |
| 核心目标 | 提供 `NG::Inspector` 静态方法集做同步树转储/单节点查询/事件注入；`InspectorFilter` 做逐属性过滤（固定属性位 + 扩展属性 + 深度/ID 过滤）；`SimplifiedInspector` 做异步树采集与 UICommand 执行；`LayoutInspector` 做平台（OHOS/Preview）调度入口 |
| P0 AC | （骨架）`GetInspector(isLayoutInspector, filter, needThrow)` 正确遍历树并按 filter 序列化；`GetInspectorByKey`/`GetRectangleById`/`SendEventByKey` 按 key 命中；异步路径经 `PipelineContext::GetInspectorTree` → `UiSessionManager::ReportInspectorTreeValue` 回报；InspectorFilter 的 FixedAttrBit 位掩码按需裁剪属性 |

## 上下文和现状

### 涉及仓和模块

| 仓库 | 模块/路径 | 当前职责 | 本 Feature 影响 |
|------|-----------|----------|-----------------|
| ace_engine | `frameworks/core/components_ng/base/inspector.h/.cpp` | `NG::Inspector` 静态方法集：`GetInspector`、`GetInspectorNodeByKey`、`GetRectangleById`、`GetInspectorTree`、`SendEventByKey`、`GetFreeNodesInspector` | 核心实现 |
| ace_engine | `frameworks/core/components_ng/base/simplified_inspector.h/.cpp` | `SimplifiedInspector`：异步树采集、UICommand 执行、`TestScrollToTarget` | 异步/UiSession 路径 |
| ace_engine | `interfaces/inner_api/ace_kit/include/ui/base/inspector_filter.h` | `InspectorFilter` + `FixedAttrBit` 枚举 + `TreeKey` 命名空间 + `InspectorConfig`（AceKit inner-API 权威声明；`components_ng/base/inspector_filter.h` 为 21 行 shim） | 属性过滤 |
| ace_engine | `frameworks/core/components_ng/base/inspector_filter.cpp` | `InspectorFilter` 实现 | 属性过滤 |
| ace_engine | `frameworks/core/common/layout_inspector.h` | `LayoutInspector` 跨平台头：`SupportInspector`、`GetInspectorTreeJsonStr`、`CreateLayoutInfo`、`ProcessMessages`、3D 快照/RS profiler 钩子 | 平台调度 |
| ace_engine | `adapter/ohos/osal/layout_inspector.cpp` | OHOS 实现：调用 `NG::Inspector::GetInspector(true)`、解析 `{windowId, method}` 消息、connect-server 通信 | 平台调度 |
| ace_engine | `frameworks/core/common/recorder/inspector_tree_collector.h/.cpp` | `InspectorTreeCollector`：异步 JSON 聚合，供 `SimplifiedInspector::GetInspectorAsync` | 异步聚合 |
| ace_engine | `frameworks/core/pipeline_ng/pipeline_context.h/.cpp` | `GetInspectorTree`（后台线程构建 JSON → UiSessionManager 回报）、`DumpInspector`（DFX Dump 桥）、持有 `InspectorOffscreenNodesMgr` | 管线集成 |
| ace_engine | `interfaces/napi/kits/inspector/js_inspector.h/.cpp` | NAPI 模块 `arkui.inspector`；仅导出 `createComponentObserver`（组件观察者/布局回调入口，详见 04-11-03） | NAPI 桥接 |
| ace_engine | `interfaces/ets/ani/inspector/src/inspector.cpp` | ANI 富 API 绑定：`getInspectorTree`/`getInspectorByKey`/`sendEventByKey`/`getFilteredInspectorTree*` | ANI 桥接 |
| ace_engine | `interfaces/ets/ani/inspector/ets/@ohos.arkui.inspector.ets` | ArkTS 定义：`getInspectorTree`、`createComponentObserver`、`InspectorTreeSerializeTool` | ANI ArkTS 层 |
| ace_engine | `frameworks/core/components_v2/inspector/*` | Legacy V2 Inspector（历史路径，新代码用 NG） | 仅兼容 |
| sdk-js | `interface/sdk-js/api/@ohos.arkui.inspector.d.ts` | 动态 SDK 声明 | SDK 类型定义 |
| sdk-js | `interface/sdk-js/api/arkui/inspector.static.d.ets` | 静态 SDK 声明 | SDK 类型定义 |

### 调用链层级分析

| 层 | 模块 | 职责 | 修改类型 |
|----|------|------|----------|
| SDK d.ts/d.ets | `@ohos.arkui.inspector.d.ts` / `inspector.static.d.ets` | 定义 getInspectorTree/getInspectorByKey/sendEventByKey/getFilteredInspectorTree* 与 createComponentObserver 签名 | 存量分析 |
| ANI 桥接 | `interfaces/ets/ani/inspector/src/inspector.cpp` | 原生方法绑定：AniGetInspectorTree→`NG::Inspector::GetInspector(false)`、AniGetFilteredInspectorTree(ById)、AniGetInspectorByKey、AniSendEventByKey；`@ohos.arkui.inspector.ets` 的 InspectorTreeSerializeTool 做 JSON 序列化 | 存量分析 |
| 动态 bridge | `frameworks/bridge/declarative_frontend/engine/jsi/jsi_view_register.cpp` | `NG::Inspector::GetInspector/GetInspectorNodeByKey/SendEventByKey`（含 V2 fallback） | 存量分析 |
| Framework 核心 | `frameworks/core/components_ng/base/inspector.cpp` | 静态方法集；主入口 `GetInspector(isLayoutInspector, filter, needThrow)` 逐节点 `DumpInfo(json, filter)` | 存量分析 |
| 属性过滤 | `InspectorFilter`（AceKit 头） | `CheckFixedAttr`/`CheckExtAttr`/`IsFastFilter`/`AddFilterAttr`/`SetFilterDepth`/`EnableFreeNodes` | 存量分析 |
| 异步采集 | `SimplifiedInspector` + `InspectorTreeCollector` | GetInspectorAsync/GetInspectorBackgroundAsync；UICommand 执行；TestScrollToTarget | 存量分析 |
| 平台调度 | `adapter/ohos/osal/layout_inspector.cpp` | `ProcessMessages` 解析 {windowId, method}；调用 `NG::Inspector::GetInspector(true)`；3D 快照与 RS profiler 钩子 | 存量分析 |
| 管线层 | `pipeline_context.cpp` | `GetInspectorTree` 后台线程构建 JSON → `UiSessionManager::ReportInspectorTreeValue`；`DumpInspector`→`OnDumpInfoNG`（DFX 桥） | 存量分析 |

检查项：
- [x] 调用链每层覆盖（SDK → ANI/动态 bridge → Framework 核心 → 过滤 → 异步采集 → 平台调度 → 管线）
- [x] 与 03-08-04 DFX Dump、03-07-01 无障碍的边界已标注（共用 InspectorFilter，入口不同）

### 适用架构规则

| Rule ID | 适用原因 | 设计结论 | 验证方式 |
|---------|----------|----------|----------|
| OH-ARCH-LAYERING | Inspector 涉及 SDK → Bridge → Framework → 平台调度单向 | 严格单向；下游消费（DevEco/UiSession）经不同入口接入 | 代码评审 |
| OH-ARCH-API-LEVEL | getInspectorTree 等为 Public/系统 API | @since 标注；filter/异步 API 随版本扩展 | API 评审/XTS |
| OH-ARCH-COMPONENT-BUILD | inspector ANI 模块 `inspector_ani`；NAPI 模块 `arkui.inspector` | 无新增 BUILD target | 构建验证 |
| OH-ARCH-ERROR-LOG | 非法 key/action 由 needThrow 回传错误 | needThrow 出参指示是否需抛异常 | 单测 |

## 不涉及项承接

| 维度 | 设计结论 |
|------|----------|
| DFX Dump 管线 | 不涉及 — 03-08-04 独立域；本域仅在 `PipelineContext::DumpInspector` 边界交叉 |
| 无障碍语义属性 | 不涉及 — 03-07-01 独立域；InspectorFilter 的 `TreeKey` 常量（clickable/scrollable/checked…）被无障碍复用，但语义归 03-07-01 |
| 跨进程 IPC | 不涉及 — Inspector 进程内同步/异步，平台调度经 connect-server（OSAL 边界外） |
| 数据持久化 | 不涉及 — 树 JSON 为运行时快照 |

## 关键设计决策

| 决策 ID | 问题 | 推荐方案 | 探索过的替代方案 | 取舍理由 | 影响 |
|---------|------|----------|------------------|----------|------|
| ADR-1 | 树转储属性裁剪：全量 vs 逐属性过滤 | `InspectorFilter` 固定属性位（FixedAttrBit 位掩码）+ 扩展属性 + 深度/ID 过滤；逐节点 `DumpInfo(json, filter)` 查询位掩码 | A: 全量序列化后裁剪；B: 逐属性过滤 | 全量裁剪产生大量无效中间数据；逐属性过滤在序列化期按位裁剪，性能与体积双优 | 核心骨架 |
| ADR-2 | InspectorFilter 归属：engine 内 vs AceKit inner-API | AceKit inner-API（`interfaces/inner_api/ace_kit/include/ui/base/inspector_filter.h`），engine 内 `inspector_filter.h` 为 shim | A: 纯 engine 内 | InspectorFilter 需对 out-of-tree 客户端（无障碍/hidumper）暴露稳定 inner-API；AceKit 头为权威 | 边界与兼容 |
| ADR-3 | 树转储触发模式：同步 vs 异步 | 双模共存：同步 `Inspector::GetInspector`（JS/ANI 推）/异步 `PipelineContext::GetInspectorTree`（后台线程 → UiSessionManager 回报） | A: 仅同步；B: 仅异步 | 同步供应用直接取值；异步供 DevEco/自动化避免阻塞 UI 线程 | 骨架与 Feat 拆分 |
| ADR-4 | NAPI vs ANI 富 API 对称性 | NAPI 模块仅导出 `createComponentObserver`；富树 API（getInspectorTree 等）走 ANI/动态 bridge | A: NAPI 也导出富 API | 历史/运行时差异：动态前端经 jsi bridge，静态前端经 ANI；NAPI 模块定位为观察者入口 | API 矩阵 |
| ADR-5 | 离屏/游离节点处理 | `InspectorOffscreenNodesMgr` 登记离屏节点，`GetFreeNodesInspector`/`ParseNeedFreeNodes` 支持游离节点查询 | A: 忽略离屏节点 | DevEco 需观察挂起/缓存节点，忽略会导致视图缺失 | 骨架 |

## 设计骨架

### 骨架范围

| 骨架项 | 目标 | 不包含 | 验证方式 |
|--------|------|--------|----------|
| 同步树转储 + 过滤 | `GetInspector(isLayoutInspector, filter, needThrow)` 逐节点序列化 | 各属性字段完整清单 | 代码评审/单测 |
| 单节点查询/事件注入 | `GetInspectorByKey`/`GetRectangleById`/`SendEventByKey` | componentUtils 几何语义（见 04-11-01） | 单测 |
| 异步采集与回报 | `SimplifiedInspector` + `PipelineContext::GetInspectorTree` → UiSessionManager | DevEco connect-server 协议细节 | 集成测试 |
| 平台调度入口 | `LayoutInspector::ProcessMessages`/`SupportInspector` | 3D 快照/profiler 全量字段 | 代码评审 |

### 骨架 Spec 拆分（候选）

| Task ID | 目标 | 受影响文件 | AC |
|---------|------|------------|----|
| TASK-SKELETON-1 | Feat-01 组件树序列化核心 | inspector.h/.cpp, inspector_filter.*, pipeline_context | AC-1.x（待 Feat 补齐） |
| TASK-SKELETON-2 | Feat-02 公共 API 与过滤 | @ohos.arkui.inspector.*, ani inspector.cpp, simplified_inspector | AC-2.x（待 Feat 补齐） |
| TASK-SKELETON-3 | Feat-03 异步采集与 UiSession | simplified_inspector, inspector_tree_collector, ui_session_manager | AC-3.x（待 Feat 补齐） |

## 风险和开放问题

| 项 | 类型 | 影响 | 处理方式 | Owner |
|----|------|------|----------|-------|
| 富 API 在 NAPI/ANI 不对称 | 架构/API | 中 — 开发者跨范式预期不一致 | 设计标注；后续版本评估对齐 | ArkUI SIG |
| InspectorFilter AceKit 头与 engine shim 双声明 | 维护 | 低 — shim 仅 re-include | 文档标注权威位置 | ArkUI SIG |
| 离屏节点登记遗漏 | 功能 | 中 — DevEco 视图缺节点 | InspectorOffscreenNodesMgr 注册点审计 | ArkUI SIG |
| 与 DFX Dump（03-08-04）/无障碍（03-07-01）边界 | 架构 | 低 — 共用 InspectorFilter 易混淆 | 本设计明确边界交叉点 | ArkUI SIG |

## 设计审批

- [x] 需求基线已确认，设计覆盖 P0 骨架 AC
- [x] 不涉及项已承接（DFX Dump/无障碍/IPC/持久化）
- [x] 涉及仓和模块职责清楚
- [x] 调用链层级分析完整，每层覆盖到位
- [x] 适用架构规则已识别并形成设计结论
- [x] 关键设计决策有理由和影响说明
- [x] 风险和开放问题有 Owner
- [x] Feat 规格已补齐（Feat-01/02 已 Baselined）

**结论:** Baselined（已有实现补录，Feat-01/02 已补）
