# 特性规格

> Func-04-10-01-Feat-02 固化 `UIContext.ComponentSnapshot` 的已挂载节点、uniqueId 和系统范围截图接口。

## 概述

| 属性 | 值 |
|------|-----|
| 特性名称 | UIContext 已挂载节点与范围截图 |
| 特性编号 | Func-04-10-01-Feat-02 |
| 所属 Epic | 无（已有能力补录） |
| 优先级 | P1 |
| 目标版本 | API 12 起，范围截图 API 20 |
| SIG 归属 | ArkUI SIG |
| 状态 | Baselined |
| 复杂度 | 标准 |

## 本次变更范围（Delta）

| 类型 | 内容 | 说明 |
|------|------|------|
| ADDED | UIContext 已挂载和范围截图 | 补录服务对象的检索型接口。 |

## 输入文档

- `design.md`
- `interface/sdk-js/api/@ohos.arkui.UIContext.d.ts:4050-4077,4215-4341`
- `frameworks/core/components_ng/render/adapter/component_snapshot.cpp:601-745`

## 用户故事

### US-1: 捕获已挂载节点

作为应用开发者，我想要通过 UIContext 的 ComponentSnapshot 服务按 inspector id 或 uniqueId 捕获节点。

| AC编号 | 验收标准 | 类型 |
|--------|----------|------|
| AC-1.1 | WHEN 调用 `uiContext.getComponentSnapshot()` THEN 得到 API 12 ComponentSnapshot 服务对象。 | 正常 |
| AC-1.2 | WHEN 调用 `get(id, callback|options)` 或 `getSync(id, options)` THEN 使用 id 检索已挂载节点并按异步/同步形态返回 PixelMap。 | 正常 |
| AC-1.3 | WHEN 调用 API 15 `getWithUniqueId/getSyncWithUniqueId` THEN 使用 uniqueId 检索节点。 | 正常 |
| AC-1.4 | WHEN 同步捕获无法在超时内完成 THEN 核心同步回调返回超时结果而非成功 PixelMap。 | 异常 |

### US-2: 捕获节点范围

作为系统应用开发者，我想要按 NodeIdentity 范围截图，以便获取相邻节点限定的区域。

| AC编号 | 验收标准 | 类型 |
|--------|----------|------|
| AC-2.1 | WHEN 调用 API 20 `getWithRange(start,end,isStartRect,options)` THEN 返回 Promise PixelMap。 | 正常 |
| AC-2.2 | WHEN 调用方不具备系统 API 使用条件 THEN 不将该接口作为普通 Public API 使用。 | 边界 |

## 验收追溯

| AC | 关联规则 | 关联 Task | 验证方式 | 证据 |
|----|----------|-----------|----------|------|
| AC-1.1 | R-1 | TASK-2 | SDK 审查 | `UIContext.d.ts:5829-5832` |
| AC-1.2 | R-2 | TASK-2 | SDK/核心审查 | `UIContext.d.ts:4050-4077,4215`; `component_snapshot.cpp:731-745` |
| AC-1.3 | R-3 | TASK-2 | SDK/核心审查 | `UIContext.d.ts:4243-4272`; `component_snapshot.cpp:689-729` |
| AC-1.4 | R-4 | TASK-2 | 源码审查 | `component_snapshot.cpp:601-655` |
| AC-2.1 | R-5 | TASK-2 | SDK 审查 | `UIContext.d.ts:4338-4341` |
| AC-2.2 | R-6 | TASK-2 | SDK 权限审查 | `UIContext.d.ts:4317-4341` |

## 规则定义

| 规则ID | 类型 | 触发条件 | 预期行为 | 边界/约束 | 关联AC |
|--------|------|----------|----------|-----------|--------|
| R-1 | 行为 | 从 UIContext 获取服务 | 返回 ComponentSnapshot | API 12 dynamic | AC-1.1 |
| R-2 | 行为 | id get/getSync | 通过当前容器注册表查找并捕获 FrameNode | 同步调用可能阻塞 UI 线程 | AC-1.2 |
| R-3 | 行为 | uniqueId API 15 | 使用 uniqueId 路径检索 | API 15+ | AC-1.3 |
| R-4 | 异常 | 同步 Rosen 回调超时 | 返回超时错误结果 | `GetPixelMap(SNAPSHOT_TIMEOUT_DURATION)` | AC-1.4 |
| R-5 | 行为 | getWithRange | 按起止 NodeIdentity 和 isStartRect 生成范围捕获 | API 20 | AC-2.1 |
| R-6 | 边界 | 普通应用使用范围接口 | 按 System API 限制处理 | 不扩展权限语义 | AC-2.2 |

## 验证映射

| 编号 | 对应规格项 | 验证方式 | 验证重点 |
|------|------------|----------|----------|
| VM-1 | AC-1.1~1.4 | SDK/核心审查 | id/uniqueId、同步超时、回调形态。 |
| VM-2 | AC-2.1~2.2 | SDK 审查 | System API 边界。 |

## API 变更分析

### 新增 API

| API 名称 | 开放范围 | 入参概要 | 返回值 | 错误码范围 | 功能描述 | 关联 AC |
|----------|----------|----------|--------|-----------|----------|---------|
| `getComponentSnapshot` | Public | 无 | ComponentSnapshot | N/A | 获取服务 | AC-1.1 |
| `get/getSync` | Public | id、options、callback | PixelMap/Promise/void | 超时/内部错误 | id 截图 | AC-1.2, AC-1.4 |
| `getWithUniqueId/getSyncWithUniqueId` | Public | uniqueId、options | PixelMap/Promise | 超时/内部错误 | uniqueId 截图 | AC-1.3 |
| `getWithRange` | System | start/end/isStartRect/options | Promise<PixelMap> | Promise 错误 | 范围截图 | AC-2.1, AC-2.2 |

### 变更/废弃 API

| API 名称 | 变更类型 | 影响场景 | 迁移指引 | 关联 AC |
|----------|----------|----------|----------|---------|
| `getWithUniqueId` | 变更 | API 15 新增 | 低版本使用 inspector id get | AC-1.3 |
| `getWithRange` | 变更 | API 20 System API | 仅满足系统接口条件时使用 | AC-2.2 |

## 接口规格

### 接口定义

**Mounted node retrieval**

| 属性 | 值 |
|------|-----|
| 函数签名 | `get(id, callback|options?)`、`getSync(id, options?)`、`getWithUniqueId`、`getSyncWithUniqueId` |
| 返回值 | void、Promise<PixelMap> 或 PixelMap |
| 开放范围 | Public |
| 错误码 | 同步路径包含超时/内部错误 |
| 关联 AC | AC-1.1~1.4 |

| 参数 | 类型 | 必填 | 默认值 | 约束条件 |
|------|------|------|--------|----------|
| id/uniqueId | string/number | 是 | 无 | 必须对应当前容器中的可捕获节点。 |
| options | SnapshotOptions | 否 | 默认 Options | 详见 Feat-04。 |

**Range retrieval**

| 属性 | 值 |
|------|-----|
| 函数签名 | `getWithRange(start, end, isStartRect, options?)` |
| 返回值 | Promise<PixelMap> |
| 开放范围 | System |
| 错误码 | Promise 错误 |
| 关联 AC | AC-2.1, AC-2.2 |

## 兼容性声明

- **已有 API 行为变更:** 无。
- **配置文件格式变更:** 无。
- **数据存储格式变更:** 无。
- **最低支持版本:** UIContext API 12；uniqueId API 15；range API 20 System API。
- **API 版本号策略:** 旧模块迁移详见 Feat-01；静态返回形态差异详见 Feat-04。

## 架构约束

| 关键约束 | 约束说明 | 影响 AC |
|----------|----------|---------|
| UI 线程 | Core `GetSync` 要求运行于 UI 线程 | AC-1.2, AC-1.4 |
| 节点检索 | id/uniqueId 需解析为 FrameNode | AC-1.2, AC-1.3 |
| 权限边界 | range 为 System API | AC-2.2 |

## 非功能性需求

| 类型 | 指标/阈值 | 验证方式 | 证据 |
|------|-----------|----------|------|
| 性能 | 同步 API 可能阻塞，调用方按 SDK 文档评估 | API/代码审查 | `component_snapshot.cpp:601-655` |
| 可测试性 | id、uniqueId、范围各自可独立验证 | SDK 审查 | 输入文档 |

## 多设备适配声明

| 设备类型 | 行为差异 | 规格/约束 | 验证方式 | 证据 |
|----------|----------|-----------|----------|------|
| 手机/平板/折叠屏 | 同一节点 API，输出随分辨率/scale 变化 | 不承诺像素一致性 | 设备测试 | SnapshotOptions |

## 全局特性影响

| 特性 | 适用 | 结论 | 关联场景 |
|------|------|------|----------|
| 多窗口/分屏 | 是 | 节点查找限定于当前前端上下文 | AC-1.2 |
| 版本升级 | 是 | unique/range 按 since 使用 | AC-1.3, AC-2.1 |
| 深色/HDR | 是 | options 影响输出，详见 Feat-04 | AC-1.2 |

## 行为场景（可选，Gherkin）

L1 规格已由接口定义的行为表覆盖。

## Spec 自审清单

- [x] 无待定、TBD 或 TODO 占位符
- [x] 所有 AC 使用 WHEN/THEN 格式且可测试
- [x] System API 范围截图与 Public 节点截图分界明确
- [x] 所有规则关联 AC

## context-references

```yaml
context-queries:
  - repo: "OpenHarmony/arkui_ace_engine"
    query: "UIContext ComponentSnapshot get sync uniqueId range capture and ComponentSnapshot core timeout"
```
