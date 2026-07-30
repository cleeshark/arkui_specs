# 特性规格

## 概述

| 字段 | 内容 |
|------|------|
| 特性名称 | Inspector 同步树转储与属性过滤 |
| 特性编号 | Func-03-07-02-Feat-01 |
| 所属 Epic | 无 |
| 优先级 | P1 |
| 目标版本 | API 10 起（getInspectorTree/getInspectorByKey/sendEventByKey） |
| SIG 归属 | ArkUI SIG |
| 状态 | Baselined |
| 复杂度 | 一般 |

本特性补录 `NG::Inspector` 的同步组件树 JSON 转储与逐属性过滤能力。核心是 `GetInspector(isLayoutInspector, filter, needThrow)` 主入口逐节点 `DumpInfo(json, filter)`，配合 `InspectorFilter`（AceKit inner-API：`FixedAttrBit` 位掩码 + 扩展属性 + 深度/ID 过滤）按需裁剪属性，供 DevEco Inspector、自动化消费。与 03-08-04 DFX Dump 共用 InspectorFilter 但入口不同。本文档只描述当前实现。

## 本次变更范围（Delta）

| 类型 | 内容 | 说明 |
|------|------|------|
| ADDED | `specs/03-engine-framework/07-accessibility-mechanism/02-inspector/design.md` | 新增功能域基线设计。 |
| ADDED | `specs/03-engine-framework/07-accessibility-mechanism/02-inspector/Feat-01-sync-tree-dump-filter-spec.md` | 新增同步树转储与过滤规格。 |
| MODIFIED | `specs/index.md` | 链接 design.md，注册 Feat-01。 |
| REMOVED | 无 | — |

## 输入文档

- 规格索引：`specs/index.md`
- 设计文档：`specs/03-engine-framework/07-accessibility-mechanism/02-inspector/design.md`
- 知识库：`docs/kb/capabilities/inspector.md`
- 主要源码定位：
  - `frameworks/core/components_ng/base/inspector.cpp` / `.h`（`NG::Inspector` 静态方法集）
  - `interfaces/inner_api/ace_kit/include/ui/base/inspector_filter.h`（`InspectorFilter`/`FixedAttrBit`/`TreeKey`/`InspectorConfig` 权威声明）
  - `frameworks/core/components_ng/base/inspector_filter.cpp`（filter 实现；`inspector_filter.h` 为 shim）
  - `frameworks/bridge/declarative_frontend/engine/jsi/jsi_view_register.cpp`（动态 bridge 入口）

## 用户故事

### US-1: 同步获取组件树 JSON

**作为** 工具/自动化,
**我想要** 同步获取运行时组件树的 JSON 视图（含/不含布局信息）,
**以便** DevEco Inspector、自动化测试消费。

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-1.1 | WHEN 调用 `GetInspector(isLayoutInspector, filter, needThrow)` THEN 逐节点 `DumpInfo(json, filter)` 序列化整树 | 正常 |
| AC-1.2 | WHEN `isLayoutInspector=true` THEN 输出含布局信息（供 DevEco 布局视图）；false 为通用树 | 正常 |
| AC-1.3 | WHEN filter 启用 `FixedAttrBit` 位掩码 THEN 仅序列化对应固定属性位 | 正常 |
| AC-1.4 | WHEN filter 设 `SetFilterDepth`/`SetFilterID` THEN 按深度/ID 裁剪 | 正常 |
| AC-1.5 | WHEN filter `IsFastFilter()` 命中 THEN 走快速过滤路径 | 边界 |

### US-2: 单节点查询与事件注入

**作为** 工具/自动化,
**我想要** 按 key 查询单节点 JSON 或向指定节点注入事件,
**以便** 对运行时组件树做精准诊断与交互。

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-2.1 | WHEN `GetInspectorNodeByKey(key, filter)` 且 key 命中 THEN 返回单节点 JSON | 正常 |
| AC-2.2 | WHEN key 未命中或已 detach THEN 返回空/无匹配 | 边界 |
| AC-2.3 | WHEN `SendEventByKey(key, action, params)` 命中 THEN 向目标节点注入事件 | 正常 |
| AC-2.4 | WHEN `needThrow` 为真且发生错误 THEN 回传需抛异常的指示 | 边界 |

### US-3: 离屏/游离节点

**作为** 工具/自动化,
**我想要** 查询已登记离屏/游离节点的 JSON,
**以便** 观察挂起/缓存组件的状态。

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-3.1 | WHEN 节点登记于 `InspectorOffscreenNodesMgr` THEN 可经 `GetFreeNodesInspector` 查询 | 正常 |
| AC-3.2 | WHEN `ParseNeedFreeNodes(message)` THEN 按消息解析游离节点请求 | 正常 |

---

## 验收追溯

| AC | 关联规则 | 关联 Task | 验证方式 | 证据 |
|----|----------|-----------|----------|------|
| AC-1.1~1.5 | R-1~R-4 | 已有实现 | 单测 + 代码评审 | `inspector.cpp`、`inspector_filter.cpp`、`inspector_test_ng.cpp` |
| AC-2.1~2.4 | R-5~R-7 | 已有实现 | 单测 | `inspector_test_ng.cpp` GetInspectorNodeByKey/SendEventByKey |
| AC-3.1~3.2 | R-8 | 已有实现 | 代码评审 | `inspector.cpp`/`inspector.h` InspectorOffscreenNodesMgr |

---

## 规则定义

| 规则ID | 类型 | 触发条件 | 预期行为 | 边界/约束 | 关联AC |
|--------|------|----------|----------|-----------|--------|
| R-1 | 行为 | GetInspector(isLayoutInspector, filter, needThrow) | 逐节点 DumpInfo(json, filter) | — | AC-1.1 |
| R-2 | 行为 | isLayoutInspector=true/false | true 含布局信息 | — | AC-1.2 |
| R-3 | 行为 | filter FixedAttrBit 位掩码 | 仅序列化命中位属性 | 位掩码定义在 AceKit 头 | AC-1.3 |
| R-4 | 行为 | SetFilterDepth/SetFilterID/IsFastFilter | 按深度/ID 裁剪；快速路径 | — | AC-1.4, AC-1.5 |
| R-5 | 行为 | GetInspectorNodeByKey(key, filter) 命中 | 返回单节点 JSON | — | AC-2.1 |
| R-6 | 边界 | key 未命中/已 detach | 空/无匹配 | — | AC-2.2 |
| R-7 | 行为 | SendEventByKey(key, action, params) | 注入事件到命中节点 | needThrow 回传异常指示 | AC-2.3, AC-2.4 |
| R-8 | 行为 | InspectorOffscreenNodesMgr | 离屏节点登记/查询 | GetFreeNodesInspector/ParseNeedFreeNodes | AC-3.1, AC-3.2 |

---

## 验证映射

| 编号 | 对应规格项 | 验证方式 | 验证重点 |
|------|------------|----------|----------|
| VM-1 | AC-1.1~1.5, R-1~R-4 | 单测（inspector_test_ng.cpp）+ 代码评审 | 树转储、isLayoutInspector、FixedAttrBit/Depth/ID 过滤 |
| VM-2 | AC-2.1~2.4, R-5~R-7 | 单测 | 单节点查询、事件注入、needThrow |
| VM-3 | AC-3.1~3.2, R-8 | 代码评审 | 离屏/游离节点 |

---

## API 变更分析

### 新增 API

无新增。补录已有 inner-API/bridge。

### 变更/废弃 API

无。

## 接口规格

### 接口定义

| 接口 | 签名 | 说明 |
|------|------|------|
| inner-API | `NG::Inspector::GetInspector(bool isLayoutInspector, const InspectorFilter& filter, bool& needThrow)` | 主同步转储入口 |
| inner-API | `NG::Inspector::GetInspectorNodeByKey(key, filter)` | 单节点 |
| inner-API | `NG::Inspector::SendEventByKey(key, action, params)` | 事件注入 |
| inner-API | `InspectorFilter`（AceKit） | FixedAttrBit/CheckFixedAttr/CheckExtAttr/SetFilterDepth/SetFilterID/IsFastFilter |

## 兼容性声明

| 维度 | 声明 |
|------|------|
| 向后兼容 | 完全兼容（补录） |
| 与 03-08-04 | 共用 InspectorFilter，但 DFX Dump 经 PipelineContext::DumpInspector→OnDumpInfoNG，入口不同 |

## 架构约束

| 约束 | 说明 |
|------|------|
| 分层 | SDK → bridge → NG::Inspector 单向；下游（DevEco/UiSession）经不同入口 |
| inner-API 边界 | InspectorFilter 权威声明在 AceKit 头，engine 内为 shim |

## 非功能性需求

| 项 | 要求 |
|----|------|
| 性能 | 逐属性位掩码裁剪，避免全量中间 JSON |
| 线程安全 | UI 线程同步转储 |

## 多设备适配声明

通用，无设备差异。

## 全局特性影响

无全局影响。

## Spec 自审清单

- [x] 用户故事与 AC 覆盖正常/边界
- [x] AC 可追溯到源码证据
- [x] 与 DFX Dump/无障碍边界明确
- [x] 无占位符

## context-references

```yaml
context-queries:
  - repo: "openharmony/ace_engine"
    query: "NG::Inspector GetInspector isLayoutInspector InspectorFilter DumpInfo 树转储"
  - repo: "openharmony/ace_engine"
    query: "InspectorFilter FixedAttrBit SetFilterDepth SetFilterID AceKit inspector_filter"
```

**关键文档：** `inspector.cpp/.h`、`inspector_filter.cpp`、AceKit `inspector_filter.h`
