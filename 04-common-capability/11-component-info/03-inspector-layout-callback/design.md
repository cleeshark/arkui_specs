# 架构设计

> 布局回调（inspector）（04-11-03）功能域的架构设计文档，补录已有实现。本域聚焦 `createComponentObserver(id).on("layout"\|"draw"\|...)` 的逐组件布局/绘制回调；组件树 Inspector（03-07-02）与无感监听（04-11-02）为独立功能域。

## 设计元数据

| 字段 | 内容 |
|------|------|
| Design ID | DESIGN-Func-04-11-03 |
| 关联需求 | 已有能力补录（无独立 requirement.md） |
| 关联 Epic | 无 |
| 目标 Feature | 待拆分（Feat-01 ComponentObserver 注册与分发为候选方向，本设计仅给出骨架） |
| 复杂度 | 一般 |
| 目标版本 | API 10 起（createComponentObserver，layout/draw 回调） |
| Owner | ArkUI SIG / 通用能力 |
| 状态 | Draft（design 补录；Feat 规格待补） |

## 需求基线

| 项 | 内容 |
|----|------|
| 问题陈述 | 开发者/工具需要针对单个组件（按 id 或 uniqueId）监听其布局完成、绘制完成、子节点布局/绘制等逐组件事件，用于 Inspector 高亮、自动化断言、自定义绘制同步 |
| 核心目标 | 经 `@ohos.arkui.inspector` 的 `createComponentObserver(id)` 返回 `ComponentObserver`，对其 `on/off` 注册 layout/draw/drawChildren/layoutDraw/layoutChildren 等回调；注册经 NAPI → `JsEngine::RegisterLayoutInspectorCallback`（componentId/uniqueId 两路），在声明式/NG 前端布局/绘制完成时触发 |
| P0 AC | （骨架）`on("layout", cb)` 注册后在该组件布局完成时触发；`off` 正确清理；componentId 与 uniqueId 两路注册均生效；静态 ArkTS 前端（`arkts_frontend`）的 `layoutCallbacks_/uniqueIdLayoutCallbacks_` map 分发正确 |

## 上下文和现状

### 涉及仓和模块

| 仓库 | 模块/路径 | 当前职责 | 本 Feature 影响 |
|------|-----------|----------|-----------------|
| ace_engine | `interfaces/napi/kits/inspector/js_inspector.cpp/.h` | NAPI `arkui.inspector`：`createComponentObserver` 创建 `ComponentObserver` 并 `RegisterLayoutInspectorCallback`（componentId/uniqueId）；`Destroy` 注销 | NAPI 注册入口 |
| ace_engine | `frameworks/bridge/js_frontend/engine/common/js_engine.h/.cpp` | `JsEngine` 抽象/实现：`Register/UnregisterLayoutInspectorCallback`（id 与 uniqueId）、`LayoutInspectorCallback(uniqueId)` 分发 | 引擎分发 |
| ace_engine | `frameworks/bridge/declarative_frontend/declarative_frontend.cpp` | 声明式触发点：`jsEngine->LayoutInspectorCallback(componentId/uniqueId)` | 触发源 |
| ace_engine | `frameworks/bridge/declarative_frontend/ng/declarative_frontend_ng.cpp` | NG 触发 + `delegate_->SetLayoutInspectorCallback(...)` | 触发源（NG） |
| ace_engine | `frameworks/bridge/declarative_frontend/ng/frontend_delegate_declarative_ng.h/.cpp` | NG 委托存储 `layoutInspectorCallback_` | 委托存储 |
| ace_engine | `frameworks/bridge/js_frontend/frontend_delegate_impl.h` | `LayoutInspectorCallback`/`LayoutInspectorUniqueIdCallback` 类型定义 | 类型定义 |
| ace_engine | `frameworks/bridge/arkts_frontend/arkts_frontend.h/.cpp` | 静态 ArkTS 前端：`Register/Unregister`（id/uniqueId）、`layoutCallbacks_/uniqueIdLayoutCallbacks_` map | 静态前端 |
| ace_engine | `interfaces/ets/ani/inspector/src/inspector.cpp` | ANI `CreateComponentObserverForAni`/`DeleteComponentObserver` | ANI 生命周期 |
| ace_engine | `interfaces/ets/ani/inspector/ets/@ohos.arkui.inspector.ets` | `ComponentObserver` 类 onLayout/offLayout/onDraw/... 声明 | ANI ArkTS 层 |
| sdk-js | `interface/sdk-js/api/@ohos.arkui.inspector.d.ts` | createComponentObserver/ComponentObserver.on 声明 | SDK 类型定义 |

### 调用链层级分析

| 层 | 模块 | 职责 | 修改类型 |
|----|------|------|----------|
| SDK d.ts/d.ets | `@ohos.arkui.inspector.*` | createComponentObserver(id) 与 ComponentObserver.on/off(type, cb) 签名 | 存量分析 |
| NAPI 桥接 | `js_inspector.cpp` | `JSCreateComponentObserver` 建 ComponentObserver，按 CalloutType 维护 cbLayoutList_/cbDrawList_/... napi_ref；`jsEngine->RegisterLayoutInspectorCallback` 按 componentId 或 uniqueId 注册 | 存量分析 |
| ANI 桥接 | `inspector.cpp`（ANI 段） | `CreateComponentObserverForAni`/`DeleteComponentObserver` 生命周期 | 存量分析 |
| 引擎分发 | `js_engine.cpp` | `LayoutInspectorCallback(uniqueId)`、`Register/UnregisterLayoutInspectorCallback` | 存量分析 |
| 触发源 | `declarative_frontend.cpp` / `declarative_frontend_ng.cpp` | 布局/绘制完成时 `jsEngine->LayoutInspectorCallback(...)` | 存量分析 |
| 静态前端 | `arkts_frontend.cpp` | `layoutCallbacks_/uniqueIdLayoutCallbacks_` map 注册与分发 | 存量分析 |

检查项：
- [x] 调用链每层覆盖（SDK → NAPI/ANI → 引擎分发 → 触发源 / 静态前端 map）
- [x] 与 04-11-02 observer、03-07-02 Inspector、NDK 节点布局回调的边界已标注

### 适用架构规则

| Rule ID | 适用原因 | 设计结论 | 验证方式 |
|---------|----------|----------|----------|
| OH-ARCH-LAYERING | 回调经 SDK → Bridge → 引擎 → 触发源 | 注册正向、回调反向（经 napi_ref/ani_ref） | 代码评审 |
| OH-ARCH-API-LEVEL | createComponentObserver/on/off 为 Public API | @since 标注；CalloutType 枚举稳定 | API 评审/XTS |
| OH-ARCH-COMPONENT-BUILD | 复用 `arkui.inspector` NAPI/ANI 模块 | 无新增 BUILD target | 构建验证 |
| OH-ARCH-ERROR-LOG | 非法 id/未知 type 行为 | 按 SDK 约定（静默无匹配或 401） | 单测 |

## 不涉及项承接

| 维度 | 设计结论 |
|------|----------|
| 全局无感监听 | 不涉及 — 04-11-02 独立域（UIObserver 全局 on/off） |
| 组件树 Inspector | 不涉及 — 03-07-02 独立域（共享 `arkui.inspector` 模块但语义不同） |
| NDK 节点布局回调 | 不涉及 — `OH_ArkUI_RegisterLayoutCallbackOnNodeHandle`→`EventHub::SetNDKLayoutCallback` 为另一套 |
| DFX LayoutInspector | 不涉及 — `frameworks/core/common/layout_inspector.h` 为 DevEco 状态/profiler 工具 |
| 跨进程/持久化 | 不涉及 |

## 关键设计决策

| 决策 ID | 问题 | 推荐方案 | 探索过的替代方案 | 取舍理由 | 影响 |
|---------|------|----------|------------------|----------|------|
| ADR-1 | 注册粒度：per-component vs 全局 | per-component：`createComponentObserver(id)` 返回独立 ComponentObserver，按 componentId 或 uniqueId 注册 | A: 全局监听器 | 逐组件回调避免无关事件；与全局 UIObserver（04-11-02）分工 | 骨架 |
| ADR-2 | 注册 key：componentId vs uniqueId | 双路支持：componentId（string）与 uniqueId（int）均可注册 | A: 仅 componentId；B: 仅 uniqueId | uniqueId 稳定（不随重渲染变），componentId 易用；双路覆盖工具与开发场景 | 骨架 |
| ADR-3 | 回调类型组织 | `CalloutType` 枚举（LAYOUT/DRAW/DRAWCHILDREN/DRAWCHILDRENWITHPARAMETER/LAYOUTCHILDREN）+ 各 cb*List_ napi_ref 列表 | A: 单一回调 + type 参数 | 分类型存储避免每次分发遍历全部 | 骨架 |
| ADR-4 | 静态前端分发 | `arkts_frontend` 维护 `layoutCallbacks_/uniqueIdLayoutCallbacks_` map 独立分发 | A: 复用 JsEngine | 静态前端无 JsEngine，需独立 map | 静态前端 |

## 设计骨架

### 骨架范围

| 骨架项 | 目标 | 不包含 | 验证方式 |
|--------|------|--------|----------|
| ComponentObserver 注册/注销 | createComponentObserver + on/off，CalloutType 分类型存储 | 各 CalloutType 触发时机的完整矩阵 | 代码评审 |
| componentId/uniqueId 双路 | 两路注册与分发 | uniqueId 稳定性保证（归渲染层） | 单测 |
| 静态前端 map 分发 | arks_frontend 双 map 注册/分发 | — | 代码评审 |

### 骨架 Spec 拆分（候选）

| Task ID | 目标 | 受影响文件 | AC |
|---------|------|------------|----|
| TASK-SKELETON-1 | Feat-01 ComponentObserver 注册与分发 | js_inspector.cpp/.h, js_engine.cpp/.h, declarative_frontend*.cpp, arkts_frontend.cpp | AC-1.x（待 Feat 补齐） |

## 风险和开放问题

| 项 | 类型 | 影响 | 处理方式 | Owner |
|----|------|------|----------|-------|
| NAPI 注册路径无专属单测 | 质量 | 中 — 回调注册/分发缺回归 | 建议补 `js_inspector` ComponentObserver 用例 | ArkUI SIG |
| CalloutType 与 SDK type 字符串映射 | 文档 | 低 | Feat 规格补齐映射表 | ArkUI SIG |
| 与 UIObserver/NDK 布局回调易混淆 | 文档 | 低 | 本设计明确边界 | ArkUI SIG |
| off 后回调残留风险 | 功能 | 低 | Unregister 从 map 移除 + cb*List_ 清理 | ArkUI SIG |

## 设计审批

- [x] 需求基线已确认，设计覆盖 P0 骨架 AC
- [x] 不涉及项已承接（observer/Inspector/NDK 回调/DFX LayoutInspector）
- [x] 涉及仓和模块职责清楚
- [x] 调用链层级分析完整
- [x] 适用架构规则已识别并形成设计结论
- [x] 关键设计决策有理由和影响说明
- [x] 风险和开放问题有 Owner
- [ ] Feat 规格已补齐（本设计为 Draft，Feat 补齐后升 Baselined）

**结论:** Draft（design 已补录，Feat 规格待补）
