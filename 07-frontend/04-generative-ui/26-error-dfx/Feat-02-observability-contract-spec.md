# 特性规格

> Func-07-04-26-Feat-02 维测可观测契约：固化 `SchemaErrorInfoManager` 单例的 schema 告警收集/门控/路由机制、`SurfaceControllerImpl` 的 `setTimeout(0)` 批次冲刷（native 告警与 reported 告警两类队列）、`enableSchemaWarningReport` 开关、`SCHEMA_WARNING` 聚合 JSON 负载、以及 hilog 日志输出契约（`LOG_A2UI` 宏 + `OH_LOG_Print` domain/tag/level + `%{public}`/`%{private}` 归一化）。基准实现：`@arkui-genius/genui`（A2UIRender）。

## 概述

| 属性 | 值 |
|------|-----|
| 特性名称 | 维测可观测契约 |
| 特性编号 | Func-07-04-26-Feat-02 |
| 优先级 | P0 |
| 目标版本 | A2UI 原生协议 v0.9 |
| SIG 归属 | GenUI SIG |
| 状态 | Baselined |
| 复杂度 | 复杂 |

## 本次变更范围（Delta）

| 类型 | 内容 | 说明 |
|------|------|------|
| ADDED | 无（存量补录） | 本特性为 Func-07-04-26 第 2 个 Feat，与 Feat-01 共享 design.md 基线 |

## 输入文档

| 文档 | 路径 | 状态 |
|------|------|------|
| Design | `07-frontend/04-generative-ui/26-error-dfx/design.md` | Baselined |
| 告警管理（ArkTS） | `genui/src/main/ets/core/schema/SchemaErrorInfoManager.ets` | — |
| 告警冲刷/开关（ArkTS） | `genui/src/main/ets/core/base/SurfaceControllerImpl.ets` | — |
| 告警分发桥（C++） | `genui/src/main/cpp/functions/WarningDispatchBridge.cpp` | — |
| 日志宏/平台日志（C++） | `genui/src/main/cpp/utils/LogA2UI.h`、`platform/ohos/PlatformLog.cpp`、`platform/common/PlatformLog.cpp` | — |
| schema 校验（Docs） | `reference/schema-validation.md` | 理解辅助 |

> 需求基线、不涉及项详见 proposal.md。design.md 与本文档并行产出，互不依赖。

---

## 用户故事

### US-1: schema 告警收集与上下文

**作为** 引擎维护者,
**我想要** `SchemaErrorInfoManager` 单例按 renderId/surfaceId 上下文收集告警,
**以便** 告警归属到正确的渲染控制器。

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-1.1 | WHEN `recordSchemaWarning` 被调用 THEN 构造 `SchemaErrorInfo{code, message, path, itemType, itemName, timestamp}`，`timestamp` 取 `new Date().toISOString()`（`SchemaErrorInfoManager.ets:204-211`） | 正常 |
| AC-1.2 | WHEN 存在 warning capture 栈 THEN 告警同时入 capture 态；否则入全局 `warnings`（`SchemaErrorInfoManager.ets:212-218`） | 正常 |
| AC-1.3 | WHEN 记录告警 THEN 打印 `[SchemaError] ${code}: ${message}` 并拼接 path/item 的 `console.warn`（`SchemaErrorInfoManager.ets:220-227`） | 正常 |
| AC-1.4 | WHEN `withSchemaWarningContext(renderId, surfaceId, task)` 执行 THEN 压栈上下文并在 finally 出栈（`SchemaErrorInfoManager.ets:130-141`） | 正常 |

### US-2: 告警门控与 surface 路由

**作为** 引擎维护者,
**我想要** 告警可开关并按 surface 路由,
**以便** 多 Surface 独立上报、关闭时零开销。

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-2.1 | WHEN `registerWarningGate(renderId, enabled)` 调用 THEN 写入 `schemaWarningEnabledByRenderId`（`SchemaErrorInfoManager.ets:74-76`） | 正常 |
| AC-2.2 | WHEN 门控 disabled THEN `recordSchemaWarning` 直接 return，不产生告警（`SchemaErrorInfoManager.ets:200-203`） | 边界 |
| AC-2.3 | WHEN `isSchemaWarningEnabled` 且 renderId 未注册门控 THEN 缺省返回 true（`SchemaErrorInfoManager.ets:185-191`） | 边界 |
| AC-2.4 | WHEN `bindSurface(renderId, surfaceId)`/`unbindSurface` 调用 THEN 维护 `surfaceIdToRenderIds` 映射（`SchemaErrorInfoManager.ets:90-114`） | 正常 |
| AC-2.5 | WHEN `registerWarningEmitter(surfaceId, emitter)`/`unregisterWarningEmitter` 调用 THEN 维护 `surfaceWarningEmitters`（`SchemaErrorInfoManager.ets:116-128`） | 正常 |

### US-3: setTimeout 批次冲刷

**作为** 引擎维护者,
**我想要** 同帧告警合并为一次回调,
**以便** 降低跨语言回调频次并保证消息处理完成后再上报。

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-3.1 | WHEN `enqueueNativeSchemaWarnings(warnings)` 入队 THEN 首次调用置 `nativeSchemaWarningFlushScheduled=true` 并 `setTimeout(0)` 调 `flushPendingNativeSchemaWarnings`（`SurfaceControllerImpl.ets:500-518`） | 正常 |
| AC-3.2 | WHEN 已调度冲刷 THEN 后续入队只 push 不重复调度（`SurfaceControllerImpl.ets:507-509`） | 边界 |
| AC-3.3 | WHEN `flushPendingNativeSchemaWarnings` 执行 THEN 清空 `pendingNativeSchemaWarnings` 并一次性 `emitSchemaWarnings`（`SurfaceControllerImpl.ets:520-528`） | 正常 |
| AC-3.4 | WHEN `enqueueReportedSchemaWarning(schemaWarningInfo)` 入队 THEN 复用 `reportedSchemaWarningFlushScheduled` 的 `setTimeout(0)` 冲刷（`SurfaceControllerImpl.ets:530-546`） | 正常 |
| AC-3.5 | WHEN `flushPendingReportedSchemaWarnings` 且 `checkSchema` 为 false/已销毁/无回调 THEN 直接 return 不上报（`SurfaceControllerImpl.ets:548-561`） | 边界 |

### US-4: SCHEMA_WARNING 聚合负载

**作为** 生成式 UI 宿主开发者,
**我想要** 告警以结构化 JSON 一次性上报,
**以便** 宿主解析告警类型与路径。

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-4.1 | WHEN `emitSchemaWarnings` 触发 THEN `onError(SurfaceErrorCode.SCHEMA_WARNING, payloadJson)`（`SurfaceControllerImpl.ets:485-491`） | 正常 |
| AC-4.2 | WHEN 构建负载 THEN `buildSchemaWarningPayloadFromWarnings` 生成 `{type:'schemaWarning', warningCount, warnings:[{code,message,path?,itemType?,itemName?}]}`（`SurfaceControllerImpl.ets:473-483`） | 正常 |
| AC-4.3 | WHEN path 空/缺省 THEN 不写入 payload 的 path 字段（`SurfaceControllerImpl.ets:461-463`） | 边界 |
| AC-4.4 | WHEN 原生告警分发 `dispatchNativeSchemaWarning` THEN 归一化 `itemType` 后 `withSchemaWarningContext` + `recordSchemaWarning`，非消息收集态下 `enqueueNativeSchemaWarnings`（`SurfaceControllerImpl.ets:373-403`） | 正常 |
| AC-4.5 | WHEN 消息处理入口 THEN `handleMessage` 包裹 `withMessageWarningCollection`（`SurfaceControllerImpl.ets:696-698`） | 正常 |

### US-5: 日志输出契约

**作为** 引擎维护者,
**我想要** C++ 日志统一经 hilog 输出并归一化隐私标记,
**以便** 日志可检索且不泄漏敏感信息。

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-5.1 | WHEN `LOG_A2UI(LOG_ERROR, ...)` 调用 THEN 经 `PlatformLogPrint` 输出；`NDEBUG` 下过滤 DEBUG 级（`LogA2UI.h:29-38`） | 正常 |
| AC-5.2 | WHEN ohos 平台写日志 THEN `OH_LOG_Print(LOG_APP, level, 0xFF00, "A2UI@"+commit, "%{public}s")`（`PlatformLog.cpp:28-29,54`） | 正常 |
| AC-5.3 | WHEN format 含 `%{private}` THEN 整条脱敏为 `[A2UI log redacted: private format]`（`platform/common/PlatformLog.cpp:177-179`） | 边界 |
| AC-5.4 | WHEN format 含 `%{public}` 标记 THEN 归一化去除标记再格式化（`platform/common/PlatformLog.cpp:130`） | 正常 |
| AC-5.5 | WHEN 消息超长（>4096）THEN 截断并追加 `[truncated]`（`platform/common/PlatformLog.cpp:156-164,207-208`） | 边界 |

## 验收追溯

| AC编号 | 关联规则 | 关联 Task | 验证方式 | 证据 |
|----|---------|----------|---------|------|
| AC-1.1,AC-1.2,AC-1.3,AC-1.4 | R-1,R-2 | T-2 | ArkTS 单测：`SchemaErrorInfoManager` | `SchemaErrorInfoManager.ets:130-228` |
| AC-2.1,AC-2.2,AC-2.3,AC-2.4,AC-2.5 | R-3,R-4 | T-2 | ArkTS 单测：门控/路由 | `SchemaErrorInfoManager.ets:74-128,185-191` |
| AC-3.1,AC-3.2,AC-3.3,AC-3.4,AC-3.5 | R-5 | T-2 | ArkTS 单测：setTimeout 冲刷 | `SurfaceControllerImpl.ets:500-561` |
| AC-4.1,AC-4.2,AC-4.3,AC-4.4,AC-4.5 | R-5,R-6 | T-2 | ArkTS 单测：聚合负载 | `SurfaceControllerImpl.ets:373-403,473-491` |
| AC-5.1,AC-5.2,AC-5.3,AC-5.4,AC-5.5 | R-7 | T-2 | C++ UT：日志归一化 | `platform/common/PlatformLog.cpp:170-208` |

## 规则定义

| 规则ID | 类型 | 触发条件 | 预期行为 | 边界/约束 | 关联AC |
|--------|------|---------|---------|----------|--------|
| R-1 | 行为 | recordSchemaWarning 被调用 | 构造带 ISO timestamp 的告警并入队 | 有 capture 态入 capture，否则全局 | AC-1.1,AC-1.2 |
| R-2 | 行为 | 记录告警 | `console.warn` 打 `[SchemaError]` 日志 | path/item 存在才拼接 | AC-1.3 |
| R-3 | 行为 | registerWarningGate | 写 `schemaWarningEnabledByRenderId` | disabled 时 record 直接 return | AC-2.1,AC-2.2 |
| R-4 | 行为 | bindSurface/registerWarningEmitter | 维护 surfaceId→renderIds / emitter 映射 | 空 surfaceId 忽略 | AC-2.4,AC-2.5 |
| R-5 | 边界 | setTimeout(0) 冲刷 | 首次入队调度，后续合并 | 两套独立 flush 状态（native/reported） | AC-3.1,AC-3.2,AC-3.3,AC-3.4,AC-3.5,AC-4.4 |
| R-6 | 行为 | emitSchemaWarnings | `onError(SCHEMA_WARNING, 聚合JSON)` | checkSchema/destroyed/无回调/空告警时不发 | AC-4.1,AC-4.2,AC-4.3,AC-4.4,AC-4.5 |
| R-7 | 异常 | 日志隐私/超长 | `%{private}` 脱敏；>4096 截断加 marker | hilog domain 0xFF00 | AC-5.1,AC-5.2,AC-5.3,AC-5.4,AC-5.5 |

## 验证映射

| 编号 | 对应规格项 | 验证方式 | 验证重点 |
|------|----------|---------|---------|
| VM-1 | AC-1.1,AC-1.2,AC-1.3,AC-1.4 告警收集 | ArkTS 单测 | SchemaErrorInfo 字段、capture/全局分流 |
| VM-2 | AC-2.1,AC-2.2,AC-2.3,AC-2.4,AC-2.5 门控路由 | ArkTS 单测 | gate 开关、surface emitter 路由 |
| VM-3 | AC-3.1,AC-3.2,AC-3.3,AC-3.4,AC-3.5 批次冲刷 | ArkTS 单测 | setTimeout 0 合并、两套队列 |
| VM-4 | AC-4.1,AC-4.2,AC-4.3,AC-4.4,AC-4.5 聚合负载 | ArkTS 单测 | payload JSON 结构、可选字段 |
| VM-5 | AC-5.1,AC-5.2,AC-5.3,AC-5.4,AC-5.5 日志契约 | C++ UT | %{public}/%{private}/截断 |

## API 变更分析

> 存量补录，无新增/变更 API。本节列出受影响公开契约。

### 新增 API

N/A。

### 变更/废弃 API

| API 名称 | 变更类型 | 影响场景 | 迁移指引 | 关联 AC |
|----------|---------|---------|---------|--------|
| `SurfaceController.enableSchemaWarningReport(enable)` | 既有 | 告警开关 | 缺省 true，宿主可关闭 | AC-2.1,AC-2.2 |
| `SurfaceController.reportSchemaWarning(schemaWarningInfo)` | 既有 | 自定义组件告警上报 | 经 `enqueueReportedSchemaWarning` 冲刷 | AC-3.4 |
| `SchemaWarningInfo`（`{code, errorMsg}`） | 既有 | 告警负载 | code 为 `SurfaceErrorCode` | AC-4.1 |

> d.ts 位置：`genui/src/main/ets/interface/SurfaceController.ets`。Kit：`@arkui-genius/genui`；权限：无。

## 接口规格

### 接口定义

**`SchemaErrorInfoManager.recordSchemaWarning(code, message, path?, itemType?, itemName?)`（`SchemaErrorInfoManager.ets:193`）**

| 属性 | 值 |
|------|-----|
| 函数签名 | `public recordSchemaWarning(code: SchemaErrorCode | string, message: string, path?: string, itemType?: SchemaItemType, itemName?: string): void` |
| 返回值 | `void` — 门控后入队 |
| 开放范围 | 内部（framework-internal） |
| 错误码 | N/A（告警非阻断） |
| 关联 AC | AC-1.1,AC-1.2,AC-1.3,AC-1.4,AC-2.2 |

**`SurfaceController.enableSchemaWarningReport(enable)`（`SurfaceControllerImpl.ets:895`）**

| 属性 | 值 |
|------|-----|
| 函数签名 | `public enableSchemaWarningReport(enableSchemaWarningReport: boolean): void` |
| 返回值 | `void` — 写 `checkSchema` 并 `registerWarningGate` |
| 开放范围 | Public |
| 错误码 | N/A |
| 关联 AC | AC-2.1,AC-2.2 |

**参数约束**

| 参数 | 类型 | 必填 | 默认值 | 约束条件 |
|------|------|------|--------|---------|
| enableSchemaWarningReport | boolean | 是 | `true`（构造时 `checkSchema=true`） | destroyed 时忽略 |
| code | string | 是 | — | `SchemaErrorCode` 枚举或任意字符串 |
| surfaceId | string | 否 | — | 空串时 bind/unbind 忽略 |

**行为场景**

| # | 触发条件 | 预期行为 | 关联 AC |
|---|----------|----------|---------|
| 1 | `enableSchemaWarningReport(false)` | gate 置 false，后续 record 直接 return | AC-2.2 |
| 2 | 同帧多次 native 告警 | 合并为一次 `onError(SCHEMA_WARNING, json)` | AC-3.1,AC-3.2,AC-3.3 |
| 3 | 消息处理完成 | `emitSchemaWarningsIfNeeded` 冲刷全局告警 | AC-4.5 |
| 4 | format 含 `%{private}` | 整条脱敏输出 | AC-5.3 |
| 5 | 消息 > 4096 | 截断加 `[truncated]` | AC-5.5 |

## 兼容性声明

- **已有 API 行为变更:** 否（存量补录）。
- **配置文件格式变更:** 否。
- **数据存储格式变更:** 否。
- **最低支持版本:** A2UI 原生协议 v0.9。
- **API 版本号策略:** `SCHEMA_WARNING` 聚合 JSON 负载结构 `{type, warningCount, warnings[]}` 稳定。

## 架构约束

| 关键约束 | 约束说明 | 影响 AC |
|---------|---------|--------|
| 单例状态 | `SchemaErrorInfoManager` 全局单例，跨控制器共享 | AC-1.1,AC-1.2,AC-1.3,AC-1.4,AC-2.1,AC-2.2,AC-2.3,AC-2.4,AC-2.5 |
| 批次合并 | setTimeout 0 合并同帧告警 | AC-3.1,AC-3.2,AC-3.3,AC-3.4,AC-3.5 |
| 门控优先 | disabled 时零告警零日志 | AC-2.2 |
| 日志归一化 | `%{public}`/`%{private}` 统一处理 | AC-5.1,AC-5.2,AC-5.3,AC-5.4,AC-5.5 |

## 非功能性需求

| 类型 | 指标/阈值 | 验证方式 | 证据 |
|------|----------|---------|------|
| 性能 | 告警批次合并降低跨语言回调频次 | ArkTS 单测 | `SurfaceControllerImpl.ets:500-518` |
| 可测试性 | 告警收集/冲刷/门控可独立单测 | ArkTS 单测 | `SchemaErrorInfoManager.ets:51-283` |
| 定界定位 | 告警携带 path/itemType/itemName 定位 | ArkTS 单测 | `SchemaErrorInfoManager.ets:204-211` |

## 多设备适配声明

| 设备类型 | 行为差异 | 规格/约束 | 验证方式 | 证据 |
|---------|---------|----------|---------|------|
| 手机 | 无差异 | 告警/日志契约设备无关 | ohosTest | — |
| 平板 | 无差异 | 同上 | ohosTest | — |
| 折叠屏 | 无差异 | 同上 | ohosTest | — |

## 全局特性影响

| 特性 | 适用？ | 结论 | 关联场景 |
|------|-------|------|---------|
| 无障碍 | 否 | 可观测性契约不涉及 | — |
| 大字体 | 否 | 不涉及 | — |
| 深色模式 | 否 | 不涉及 | — |
| 多窗口/分屏 | 是 | 多 Surface 告警路由独立（emitter 按 surfaceId） | AC-2.4,AC-2.5 |
| 多用户 | 否 | 无差异 | — |
| 版本升级 | 是 | 日志/告警契约向后兼容 | AC-4.1,AC-4.2,AC-4.3,AC-4.4,AC-4.5 |
| 生态兼容 | 是 | A2UI 原生协议 v0.9 兼容 | 概述「目标版本」 |

## 行为场景（可选，Gherkin）

```gherkin
Feature: 维测可观测契约
  作为 引擎维护者
  我想要 告警收集、门控、冲刷与日志统一契约
  以便 告警归属正确且同帧合并上报

  Scenario: 关闭告警后零开销
    Given 控制器 enableSchemaWarningReport(false)
    When 触发 recordSchemaWarning
    Then 不产生告警且不打印告警日志

  Scenario: 同帧多告警合并
    Given 控制器 checkSchema=true 且已 registerErrorCallback
    When 一次消息处理产生 3 条 schema 告警
    Then onError 仅收到 1 次 SCHEMA_WARNING，warningCount=3

  Scenario Outline: 日志归一化
    Given 日志 format 为 <format>
    When PlatformLogPrint 执行
    Then 输出 <result>

    Examples:
      | format                    | result |
      | "count=%{public}zu"       | "count=5"（去除 %{public}） |
      | "token=%{private}s"       | "[A2UI log redacted: private format]" |
```

## Spec 自审清单

- [x] 无"待定""TBD""TODO"等占位符
- [x] 所有 AC 使用 WHEN/THEN 格式，可独立测试
- [x] 范围边界明确（告警可观测归本 Feat；错误码归 Feat-01；打点归 Feat-03）
- [x] 无语义模糊表述
- [x] AC 与规则表交叉一致
- [x] 规则表每条通过 5 项质量检查（可复现/可观测/边界值/关联AC/无冲突）

## context-references

```yaml
context-queries:
  - repo: "GenerativeUI/A2UIRender"
    query: "SchemaErrorInfoManager 告警收集 registerWarningGate bindSurface registerWarningEmitter setTimeout 冲刷"
  - repo: "GenerativeUI/A2UIRender"
    query: "SurfaceControllerImpl enqueueNativeSchemaWarnings flushPendingNativeSchemaWarnings emitSchemaWarnings buildSchemaWarningPayloadFromWarnings"
  - repo: "GenerativeUI/A2UIRender"
    query: "LOG_A2UI OH_LOG_Print PlatformLogPrint %{public} %{private} 4096 截断"
```

**关键文档：** `genui/src/main/ets/core/schema/SchemaErrorInfoManager.ets`、`genui/src/main/ets/core/base/SurfaceControllerImpl.ets`、`genui/src/main/cpp/functions/WarningDispatchBridge.cpp`、`genui/src/main/cpp/utils/LogA2UI.h`、`genui/src/main/cpp/platform/ohos/PlatformLog.cpp`、`genui/src/main/cpp/platform/common/PlatformLog.cpp`