# 特性规格

## 概述

| 字段 | 内容 |
|------|------|
| 特性名称 | Inspector 布局/绘制回调（ComponentObserver） |
| 特性编号 | Func-04-11-03-Feat-01 |
| 所属 Epic | 无 |
| 优先级 | P1 |
| 目标版本 | API 10 起（createComponentObserver，layout/draw 回调） |
| SIG 归属 | ArkUI SIG |
| 状态 | Baselined |
| 复杂度 | 一般 |

本特性补录 `@ohos.arkui.inspector.createComponentObserver(id)` 返回的 `ComponentObserver` 的逐组件布局/绘制回调能力。回调类型由 `CalloutType` 枚举定义（LAYOUT/DRAW/DRAWCHILDREN/DRAWCHILDRENWITHPARAMETER/LAYOUTCHILDREN），注册经 NAPI/ANI → `JsEngine::RegisterLayoutInspectorCallback`（componentId/uniqueId 双路），在声明式/NG/静态 ArkTS 前端布局或绘制完成时触发。区别于 04-11-02 全局无感监听与 NDK 节点布局回调。本文档只描述当前实现。

## 本次变更范围（Delta）

| 类型 | 内容 | 说明 |
|------|------|------|
| ADDED | `specs/04-common-capability/11-component-info/03-inspector-layout-callback/design.md` | 新增功能域基线设计。 |
| ADDED | `specs/04-common-capability/11-component-info/03-inspector-layout-callback/Feat-01-component-observer-callback-spec.md` | 新增 ComponentObserver 回调规格。 |
| MODIFIED | `specs/index.md` | 链接 design.md，注册 Feat-01。 |
| REMOVED | 无 | — |

## 输入文档

- 规格索引：`specs/index.md`
- 设计文档：`specs/04-common-capability/11-component-info/03-inspector-layout-callback/design.md`
- 知识库：`docs/kb/capabilities/inspector-layout-callback.md`
- 主要源码定位：
  - `interfaces/napi/kits/inspector/js_inspector.cpp` / `.h`（NAPI `arkui.inspector`，`createComponentObserver`、`ComponentObserver`、`CalloutType`）
  - `frameworks/bridge/js_frontend/engine/common/js_engine.cpp` / `.h`（`Register/UnregisterLayoutInspectorCallback`、`LayoutInspectorCallback`）
  - `frameworks/bridge/declarative_frontend/declarative_frontend.cpp`、`ng/declarative_frontend_ng.cpp`、`ng/frontend_delegate_declarative_ng.cpp`（触发点/委托存储）
  - `frameworks/bridge/arkts_frontend/arkts_frontend.cpp`（静态前端 `layoutCallbacks_/uniqueIdLayoutCallbacks_` map）
  - `interfaces/ets/ani/inspector/src/inspector.cpp`、`ets/@ohos.arkui.inspector.ets`（ANI ComponentObserver）

## 用户故事

### US-1: 注册逐组件布局/绘制回调

**作为** 应用开发者/工具,
**我想要** 对指定组件（按 id 或 uniqueId）注册 layout/draw 等回调,
**以便** 在该组件布局/绘制完成时得到通知（Inspector 高亮、自动化断言）。

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-1.1 | WHEN `createComponentObserver(id)` THEN 返回 ComponentObserver，并按 componentId 经 `RegisterLayoutInspectorCallback` 注册 | 正常 |
| AC-1.2 | WHEN 以 uniqueId（int）注册 THEN 走 `LayoutInspectorUniqueIdCallback` 独立分路 | 正常 |
| AC-1.3 | WHEN `on("layout", cb)` THEN cb 存入 `cbLayoutList_`（napi_ref），在该组件布局完成时触发 | 正常 |
| AC-1.4 | WHEN `on("draw"/"drawChildren"/"layoutDraw"/"layoutChildren", cb)` THEN 按 CalloutType 分类型存入对应 cb*List_ | 正常 |
| AC-1.5 | WHEN 静态 ArkTS 前端注册 THEN 经 `arkts_frontend` 的 `layoutCallbacks_/uniqueIdLayoutCallbacks_` map 分发 | 正常 |

### US-2: 注销与生命周期

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-2.1 | WHEN `off(type, cb?)` THEN 从对应 cb*List_/map 移除；不传 cb 则移除该 scope 全部 | 正常 |
| AC-2.2 | WHEN ComponentObserver `Destroy` THEN 经 `UnregisterLayoutInspectorCallback` 注销，避免回调残留 | 边界 |
| AC-2.3 | WHEN off 后状态变更 THEN 不再触发已注销回调 | 边界 |

---

## 验收追溯

| AC | 关联规则 | 关联 Task | 验证方式 | 证据 |
|----|----------|-----------|----------|------|
| AC-1.1~1.5 | R-1~R-4 | 已有实现 | 代码评审 | `js_inspector.cpp` JSCreateComponentObserver、`js_engine.cpp`、`arkts_frontend.cpp` |
| AC-2.1~2.3 | R-5, R-6 | 已有实现 | 代码评审 | `js_inspector.cpp` Destroy、`js_engine.cpp` Unregister |

---

## 规则定义

| 规则ID | 类型 | 触发条件 | 预期行为 | 边界/约束 | 关联AC |
|--------|------|----------|----------|-----------|--------|
| R-1 | 行为 | createComponentObserver(id) | 建 ComponentObserver，按 componentId 注册 `RegisterLayoutInspectorCallback` | — | AC-1.1 |
| R-2 | 行为 | 以 uniqueId 注册 | 走 uniqueId 独立分路（稳定 id） | — | AC-1.2 |
| R-3 | 行为 | on(type, cb) | 按 CalloutType 分类型存 cb*List_，对应阶段触发 | type 非法则不注册 | AC-1.3, AC-1.4 |
| R-4 | 行为 | 静态前端注册 | arks_frontend 双 map 分发 | 无 JsEngine | AC-1.5 |
| R-5 | 行为 | off(type, cb?) | 移除指定 cb 或该 scope 全部 | — | AC-2.1 |
| R-6 | 边界 | Destroy | Unregister 注销，防残留 | — | AC-2.2, AC-2.3 |

---

## 验证映射

| 编号 | 对应规格项 | 验证方式 | 验证重点 |
|------|------------|----------|----------|
| VM-1 | AC-1.1~1.4, R-1~R-3 | 代码评审 | componentId/uniqueId 双路注册、CalloutType 分类型存储与触发 |
| VM-2 | AC-1.5, R-4 | 代码评审 | 静态前端 map 分发 |
| VM-3 | AC-2.1~2.3, R-5, R-6 | 代码评审 | off/Destroy 注销与无残留 |

> 说明：仓内未见 `js_inspector` ComponentObserver 注册路径的专属单测，VM 以代码评审为主，建议补 NAPI 用例。

---

## API 变更分析

### 新增 API

无新增。补录已有 API。

### 变更/废弃 API

无。

## 接口规格

### 接口定义

| 接口 | 签名 | 说明 |
|------|------|------|
| NAPI/ANI | `inspector.createComponentObserver(id: string \| number): ComponentObserver` | 模块 `arkui.inspector` |
| 实例方法 | `on(type: 'layout'\|'draw'\|'drawChildren'\|'layoutDraw'\|'layoutChildren', cb): void` | CalloutType 分发 |
| 实例方法 | `off(type, cb?): void` | 注销 |

## 兼容性声明

| 维度 | 声明 |
|------|------|
| 向后兼容 | 完全兼容（补录） |
| 与 04-11-02 区别 | 本特性 per-component；UIObserver 为全局无感监听 |
| 与 NDK 区别 | NDK 走 `OH_ArkUI_RegisterLayoutCallbackOnNodeHandle`，非本路径 |

## 架构约束

| 约束 | 说明 |
|------|------|
| 分层 | SDK → Bridge(NAPI/ANI) → JsEngine/arkts_frontend → 触发源 |
| 共用模块 | 与 03-07-02 共用 `@ohos.arkui.inspector` 模块 |

## 非功能性需求

| 项 | 要求 |
|----|------|
| 线程安全 | UI 线程注册/触发 |
| 重入 | Notify 中不可 off（迭代删除风险） |

## 多设备适配声明

通用，无设备差异。

## 全局特性影响

无全局影响。

## Spec 自审清单

- [x] 用户故事与 AC 覆盖正常/边界
- [x] AC 可追溯到源码证据
- [x] 与 observer/NDK 回调边界明确
- [x] 无占位符

## context-references

```yaml
context-queries:
  - repo: "openharmony/ace_engine"
    query: "createComponentObserver ComponentObserver CalloutType on/off 注册与分发"
  - repo: "openharmony/ace_engine"
    query: "RegisterLayoutInspectorCallback componentId uniqueId 静态前端 layoutCallbacks map"
```

**关键文档：** `js_inspector.cpp/.h`、`js_engine.cpp/.h`、`declarative_frontend*.cpp`、`arkts_frontend.cpp`、`inspector.cpp`(ANI)
