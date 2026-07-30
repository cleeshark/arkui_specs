# 特性规格

## 概述

| 字段 | 内容 |
|------|------|
| 特性名称 | Inspector 公共 API 与异步采集 |
| 特性编号 | Func-03-07-02-Feat-02 |
| 所属 Epic | 无 |
| 优先级 | P1 |
| 目标版本 | API 10 起；ANI 富 API 随静态前端 |
| SIG 归属 | ArkUI SIG |
| 状态 | Baselined |
| 复杂度 | 复杂 |

本特性补录 `@ohos.arkui.inspector` 公共 API 矩阵与异步树采集通道。NAPI 模块仅导出 `createComponentObserver`（布局回调入口归 04-11-03）；富树 API（`getInspectorTree`/`getInspectorByKey`/`sendEventByKey`/`getFilteredInspectorTree*`）经 ANI 与动态 bridge 暴露。异步路径由 `PipelineContext::GetInspectorTree` 后台线程构建 JSON，经 `SimplifiedInspector` + `InspectorTreeCollector` 聚合后由 `UiSessionManager::ReportInspectorTreeValue` 回报。本文档只描述当前实现。

## 本次变更范围（Delta）

| 类型 | 内容 | 说明 |
|------|------|------|
| ADDED | `specs/03-engine-framework/07-accessibility-mechanism/02-inspector/Feat-02-public-api-async-spec.md` | 新增公共 API 与异步采集规格。 |
| MODIFIED | `specs/index.md` | 注册 Feat-02。 |
| REMOVED | 无 | — |

## 输入文档

- 设计文档：`specs/03-engine-framework/07-accessibility-mechanism/02-inspector/design.md`
- 知识库：`docs/kb/capabilities/inspector.md`
- 主要源码定位：
  - `interfaces/napi/kits/inspector/js_inspector.cpp`（NAPI 模块 `arkui.inspector`，仅 `createComponentObserver`）
  - `interfaces/ets/ani/inspector/src/inspector.cpp`、`ets/@ohos.arkui.inspector.ets`（ANI 富 API + InspectorTreeSerializeTool）
  - `frameworks/bridge/declarative_frontend/engine/jsi/jsi_view_register.cpp`（动态 bridge）
  - `frameworks/core/components_ng/base/simplified_inspector.cpp` / `.h`（异步采集）
  - `frameworks/core/common/recorder/inspector_tree_collector.h` / `.cpp`（异步聚合）
  - `frameworks/core/pipeline_ng/pipeline_context.cpp`（`GetInspectorTree`→`UiSessionManager::ReportInspectorTreeValue`）

## 用户故事

### US-1: 富树 API（ANI/动态 bridge）

**作为** 应用开发者,
**我想要** 经 `@ohos.arkui.inspector` 获取树/单节点/过滤树/事件注入,
**以便** 运行时诊断与自动化。

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-1.1 | WHEN ANI `getInspectorTree()` THEN 经 `AniGetInspectorTree`→`NG::Inspector::GetInspector(false)` 返回树 | 正常 |
| AC-1.2 | WHEN `getFilteredInspectorTree(filters?)` / `getFilteredInspectorTreeById(id, depth, filters?)` THEN 按 filter 序列化 | 正常 |
| AC-1.3 | WHEN `getInspectorByKey(id)` THEN 返回单节点 JSON 字符串 | 正常 |
| AC-1.4 | WHEN `sendEventByKey(id, action, params)` THEN 注入事件，返回 boolean | 正常 |
| AC-1.5 | WHEN NAPI 模块 `arkui.inspector` THEN 仅导出 `createComponentObserver`（富树 API 非该模块导出） | 边界 |

### US-2: 异步树采集与 UiSession 回报

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-2.1 | WHEN `PipelineContext::GetInspectorTree(onlyNeedVisible, config)` THEN 后台线程构建 JSON 根 | 正常 |
| AC-2.2 | WHEN 构建完成 THEN 经 `UiSessionManager::ReportInspectorTreeValue` 回报 | 正常 |
| AC-2.3 | WHEN `SimplifiedInspector::GetInspectorAsync(collector)` THEN 经 `InspectorTreeCollector` 异步聚合 | 正常 |
| AC-2.4 | WHEN `onlyNeedVisible=true` THEN 走 `DumpVisibleInspectorTree`/`DumpSimplifyTreeWithParamConfig` | 边界 |

---

## 验收追溯

| AC | 关联规则 | 关联 Task | 验证方式 | 证据 |
|----|----------|-----------|----------|------|
| AC-1.1~1.5 | R-1~R-3 | 已有实现 | 代码评审 + 单测 | `inspector.cpp`(ANI)、`js_view_register.cpp`、`inspector_test_ng.cpp` |
| AC-2.1~2.4 | R-4~R-6 | 已有实现 | 单测 + 代码评审 | `pipeline_context.cpp`、`simplified_inspector_test_ng.cpp` |

---

## 规则定义

| 规则ID | 类型 | 触发条件 | 预期行为 | 边界/约束 | 关联AC |
|--------|------|----------|----------|-----------|--------|
| R-1 | 行为 | ANI getInspectorTree/Filtered* | 经原生绑定调 `NG::Inspector::GetInspector(false)` | filter 可选 | AC-1.1, AC-1.2 |
| R-2 | 行为 | getInspectorByKey/sendEventByKey | 单节点 JSON / 事件注入返回 boolean | — | AC-1.3, AC-1.4 |
| R-3 | 边界 | NAPI 模块导出面 | 仅 createComponentObserver；富 API 走 ANI/动态 bridge | 跨范式不对称 | AC-1.5 |
| R-4 | 行为 | PipelineContext::GetInspectorTree | 后台线程构建 JSON | onlyNeedVisible/config | AC-2.1, AC-2.4 |
| R-5 | 行为 | 构建完成 | ReportInspectorTreeValue 回报 | — | AC-2.2 |
| R-6 | 行为 | SimplifiedInspector::GetInspectorAsync | InspectorTreeCollector 异步聚合 | — | AC-2.3 |

---

## 验证映射

| 编号 | 对应规格项 | 验证方式 | 验证重点 |
|------|------------|----------|----------|
| VM-1 | AC-1.1~1.4, R-1~R-2 | 单测 + 代码评审 | ANI 富 API 绑定与返回 |
| VM-2 | AC-1.5, R-3 | 代码评审 | NAPI 导出面仅 createComponentObserver |
| VM-3 | AC-2.1~2.4, R-4~R-6 | 单测（simplified_inspector_test_ng.cpp）+ 代码评审 | 异步构建/回报/聚合 |

---

## API 变更分析

### 新增 API

无新增。补录已有。

### 变更/废弃 API

无。

## 接口规格

### 接口定义

| 接口 | 签名 | 说明 |
|------|------|------|
| ANI | `getInspectorTree(): RecordData` | 树 |
| ANI | `getFilteredInspectorTree(filters?): string`；`getFilteredInspectorTreeById(id, depth, filters?): string` | 过滤树 |
| ANI | `getInspectorByKey(id): string` | 单节点 |
| ANI | `sendEventByKey(id, action, params): boolean` | 事件注入 |
| ANI 工具 | `InspectorTreeSerializeTool.stringifyNoThrow/parseNoThrow` | 序列化 |
| NAPI | `createComponentObserver(id)` | 仅此导出 |

## 兼容性声明

| 维度 | 声明 |
|------|------|
| 向后兼容 | 完全兼容（补录） |
| NAPI/ANI 对称性 | 不对称（R-3），属已知设计 |

## 架构约束

| 约束 | 说明 |
|------|------|
| 分层 | SDK(ANI/动态 bridge) → NG::Inspector；异步经 PipelineContext → UiSessionManager |
| 线程 | 异步在后台线程构建 JSON |

## 非功能性需求

| 项 | 要求 |
|----|------|
| 性能 | 异步避免阻塞 UI 线程；序列化按 filter 裁剪 |
| 线程安全 | 异步构建跨后台线程 |

## 多设备适配声明

通用，无设备差异。

## 全局特性影响

无全局影响。

## Spec 自审清单

- [x] 用户故事与 AC 覆盖正常/边界
- [x] AC 可追溯到源码证据
- [x] NAPI/ANI 不对称已显式标注（R-3）
- [x] 无占位符

## context-references

```yaml
context-queries:
  - repo: "openharmony/ace_engine"
    query: "@ohos.arkui.inspector getInspectorTree getInspectorByKey sendEventByKey getFilteredInspectorTree ANI 绑定"
  - repo: "openharmony/ace_engine"
    query: "PipelineContext GetInspectorTree SimplifiedInspector UiSessionManager ReportInspectorTreeValue 异步"
```

**关键文档：** `inspector.cpp`(ANI)、`@ohos.arkui.inspector.ets`、`js_view_register.cpp`、`simplified_inspector.cpp`、`pipeline_context.cpp`
