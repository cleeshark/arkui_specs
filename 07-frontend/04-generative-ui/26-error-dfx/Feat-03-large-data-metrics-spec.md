# 特性规格

> Func-07-04-26-Feat-03 大数据打点：固化逐消息性能打点（`durationMs` 日志）、消息处理 HiTrace 追踪（`PlatformTraceScope` + `OH_HiTrace_StartTrace/FinishTrace`）、DSL 长度护栏（`MAX_DSL_LENGTH=100*1024`）、以及日志隐私/超长防护（`%{private}` 脱敏、4096 截断加 `[truncated]`）。基准实现：`@arkui-genius/genui`（A2UIRender）。

## 概述

| 属性 | 值 |
|------|-----|
| 特性名称 | 大数据打点 |
| 特性编号 | Func-07-04-26-Feat-03 |
| 优先级 | P1 |
| 目标版本 | A2UI 原生协议 v0.9 |
| SIG 归属 | GenUI SIG |
| 状态 | Baselined |
| 复杂度 | 复杂 |

## 本次变更范围（Delta）

| 类型 | 内容 | 说明 |
|------|------|------|
| ADDED | 无（存量补录） | 本特性为 Func-07-04-26 第 3 个 Feat，与 Feat-01/Feat-02 共享 design.md 基线 |

## 输入文档

| 文档 | 路径 | 状态 |
|------|------|------|
| Design | `07-frontend/04-generative-ui/26-error-dfx/design.md` | Baselined |
| 消息处理/timing（C++） | `genui/src/main/cpp/NativeEntry.cpp` | — |
| 平台 trace（C++） | `genui/src/main/cpp/platform/common/PlatformTrace.cpp`、`platform/ohos/PlatformTrace.cpp` | — |
| 平台日志隐私/截断（C++） | `genui/src/main/cpp/platform/common/PlatformLog.cpp`、`platform/common/PlatformLog.h` | — |
| 性能排查（Docs） | `guides/troubleshooting.md` | 理解辅助 |

> 需求基线、不涉及项详见 proposal.md。design.md 与本文档并行产出，互不依赖。

---

## 用户故事

### US-1: 逐消息性能打点

**作为** 引擎维护者,
**我想要** 每条消息处理耗时以 INFO 日志输出,
**以便** 定位大消息/复杂组件导致的卡顿。

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-1.1 | WHEN `ProcessMessage` 入口解析成功后 THEN 记录 `startTime = steady_clock::now()`（`NativeEntry.cpp:1403`） | 正常 |
| AC-1.2 | WHEN 处理成功 THEN `CreateTimedProcessResultValue` 计算 `durationMs` 并输出 `ProcessMessage timing: messageType=%{public}s, surfaceId=%{public}s, durationMs=%{public}lld`（`NativeEntry.cpp:1149-1158`） | 正常 |
| AC-1.3 | WHEN 处理失败 THEN `result.success===false` 不输出 timing 日志（`NativeEntry.cpp:1152-1159`） | 边界 |
| AC-1.4 | WHEN `messageType` 未知 THEN `DescribeMessageType` 返回 `"UNKNOWN"`（`NativeEntry.cpp:196-197`） | 边界 |

### US-2: 消息处理 HiTrace 追踪

**作为** 引擎维护者,
**我想要** 每种消息类型用 HiTrace 包裹,
**以便** 集成系统 trace 面板分析耗时分布。

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-2.1 | WHEN 分发 `createSurface` 消息 THEN 进入 `PlatformTraceScope("SurfaceController:onReceive:CREATE_SURFACE")`（`NativeEntry.cpp:1079-1082`） | 正常 |
| AC-2.2 | WHEN 分发 `updateComponents`/`updateDataModel`/`deleteSurface` THEN 分别进入对应 trace scope（`NativeEntry.cpp:1084-1094`） | 正常 |
| AC-2.3 | WHEN ohos 平台 `PlatformTraceBegin` 调用 THEN 执行 `OH_HiTrace_StartTrace(name)`（`platform/ohos/PlatformTrace.cpp:27`） | 正常 |
| AC-2.4 | WHEN `PlatformTraceScope` 析构且 active 为真 THEN `OH_HiTrace_FinishTrace()`（`platform/ohos/PlatformTrace.cpp:33`、`platform/common/PlatformTrace.cpp:28-32`） | 正常 |
| AC-2.5 | WHEN trace 名称为空/空指针 THEN 不启用 trace（`platform/common/PlatformTrace.cpp:22-24`） | 边界 |

### US-3: DSL 长度护栏

**作为** 引擎维护者,
**我想要** 超长 DSL 在入口拒绝,
**以便** 防止大负载拖垮解析与渲染。

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-3.1 | WHEN `dsl.size() > 100*1024` THEN `DispatchDslLengthErrorIfNeeded` 返回 `Fail("NATIVE_PROCESS_FAILED", ..., SURFACE_ERROR_NATIVE_PROCESS_FAILED)`（`NativeEntry.cpp:1136-1147`） | 边界 |
| AC-3.2 | WHEN `dsl.size() <= 100*1024` THEN 返回 `Ok()` 继续解析（`NativeEntry.cpp:1139-1141`） | 正常 |
| AC-3.3 | WHEN 超长 DSL THEN 打 `LOG_A2UI(LOG_ERROR)` 含实际长度与上限（`NativeEntry.cpp:1145`） | 正常 |
| AC-3.4 | WHEN DSL 长度检查失败 THEN `ProcessMessage` 直接返回结果，不进 `ParseDslMessage`（`NativeEntry.cpp:1392-1395`） | 正常 |

### US-4: 日志隐私与超长防护

**作为** 引擎维护者,
**我想要** 日志自动脱敏 `%{private}` 并截断超长,
**以便** 不泄漏敏感信息、防止日志爆炸。

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-4.1 | WHEN format 含 `%{private}` 标记 THEN `PlatformLogPrint` 整条输出 `[A2UI log redacted: private format]`（`platform/common/PlatformLog.cpp:177-179`） | 边界 |
| AC-4.2 | WHEN format 为 null/空 THEN 输出 `[A2UI log: empty format]`（`platform/common/PlatformLog.cpp:172-175`） | 边界 |
| AC-4.3 | WHEN 归一化或格式化出错 THEN 输出 `[A2UI log: formatting failed]`（`platform/common/PlatformLog.cpp:184-186,196-198`） | 异常 |
| AC-4.4 | WHEN 消息长度 > `PLATFORM_LOG_MAX_MESSAGE_LENGTH`（4096）THEN 追加 `[truncated]` 后输出（`platform/common/PlatformLog.cpp:202-208`） | 边界 |
| AC-4.5 | WHEN `PLATFORM_LOG_MAX_MESSAGE_LENGTH` 定义 THEN 恒为 4096（`platform/common/PlatformLog.h:24`） | 正常 |

## 验收追溯

| AC编号 | 关联规则 | 关联 Task | 验证方式 | 证据 |
|----|---------|----------|---------|------|
| AC-1.1,AC-1.2,AC-1.3,AC-1.4 | R-1 | T-3 | C++ UT：timing 日志 | `NativeEntry.cpp:1149-1161,1403` |
| AC-2.1,AC-2.2,AC-2.3,AC-2.4,AC-2.5 | R-2 | T-3 | C++ UT + 真机 trace | `NativeEntry.cpp:1078-1101`、`platform/ohos/PlatformTrace.cpp:27-33` |
| AC-3.1,AC-3.2,AC-3.3,AC-3.4 | R-3 | T-3 | C++ UT：超长 DSL 拒绝 | `NativeEntry.cpp:1136-1147` |
| AC-4.1,AC-4.2,AC-4.3,AC-4.4,AC-4.5 | R-4 | T-3 | C++ UT：归一化/截断 | `platform/common/PlatformLog.cpp:170-208` |

## 规则定义

| 规则ID | 类型 | 触发条件 | 预期行为 | 边界/约束 | 关联AC |
|--------|------|---------|---------|----------|--------|
| R-1 | 行为 | 消息处理成功 | 输出 durationMs timing INFO 日志 | 失败路径不输出 | AC-1.1,AC-1.2,AC-1.3,AC-1.4 |
| R-2 | 行为 | 分发四种消息 | 每种消息类型用 HiTrace scope 包裹 | trace 名空则禁用 | AC-2.1,AC-2.2,AC-2.3,AC-2.4,AC-2.5 |
| R-3 | 边界 | dsl.size() > 100*1024 | 拒绝并返回 NATIVE_PROCESS_FAILED(1002) | 护栏优先于解析 | AC-3.1,AC-3.2,AC-3.3,AC-3.4 |
| R-4 | 异常 | 日志含 %{private}/超长/非法 format | 脱敏/截断加 marker/错误占位 | 4096 上限 | AC-4.1,AC-4.2,AC-4.3,AC-4.4,AC-4.5 |

## 验证映射

| 编号 | 对应规格项 | 验证方式 | 验证重点 |
|------|----------|---------|---------|
| VM-1 | AC-1.1,AC-1.2,AC-1.3,AC-1.4 逐消息 timing | C++ UT | durationMs 计算、成功才输出 |
| VM-2 | AC-2.1,AC-2.2,AC-2.3,AC-2.4,AC-2.5 HiTrace | C++ UT + 真机 | scope RAII、四类消息名称 |
| VM-3 | AC-3.1,AC-3.2,AC-3.3,AC-3.4 DSL 长度 | C++ UT | 100KB 边界、NATIVE_PROCESS_FAILED |
| VM-4 | AC-4.1,AC-4.2,AC-4.3,AC-4.4,AC-4.5 日志防护 | C++ UT | 脱敏、截断、错误占位 |

## API 变更分析

> 存量补录，无新增/变更 API。本节为框架内部能力（无公开 API）。

### 新增 API

N/A（framework-internal 打点能力，无公开 API）。

### 变更/废弃 API

| API 名称 | 变更类型 | 影响场景 | 迁移指引 | 关联 AC |
|----------|---------|---------|---------|--------|
| 无 | — | — | 打点对宿主透明 | — |

> d.ts 位置：不适用（内部能力）。Kit：`@arkui-genius/genui`；权限：无。

## 接口规格

### 接口定义

**`ProcessMessage(napi_env, napi_callback_info)`（`NativeEntry.cpp:1384`）**

| 属性 | 值 |
|------|-----|
| 函数签名 | `napi_value ProcessMessage(napi_env env, napi_callback_info info)` |
| 返回值 | `napi_value` — `NativeProcessResult` 对象（`success`/`errorCode`/`errorMessage`/`surfaceId`/`messageType`） |
| 开放范围 | 内部（经 NAPI 暴露给 ArkTS `NativeEngineBridge.processMessage`） |
| 错误码 | 阻断错误码见 Feat-01 |
| 关联 AC | AC-1.1,AC-3.4 |

**`PlatformLogPrint(level, format, ...)`（`platform/common/PlatformLog.cpp:170`）**

| 属性 | 值 |
|------|-----|
| 函数签名 | `void PlatformLogPrint(PlatformLogLevel level, const char* format, ...)` |
| 返回值 | `void` — 经 `PlatformLogWrite` 落盘 |
| 开放范围 | 内部（`LOG_A2UI` 宏底层） |
| 错误码 | N/A |
| 关联 AC | AC-4.1,AC-4.2,AC-4.3,AC-4.4,AC-4.5 |

**参数约束**

| 参数 | 类型 | 必填 | 默认值 | 约束条件 |
|------|------|------|--------|---------|
| dsl | string | 是 | — | 空→SCHEMA_DSL_EMPTY；>100KB→NATIVE_PROCESS_FAILED |
| format | const char* | 是 | — | 无 `%{private}`；超长截断 4096 |
| name（trace） | const char* | 是 | — | 空/空指针禁用 trace |

**行为场景**

| # | 触发条件 | 预期行为 | 关联 AC |
|---|----------|----------|---------|
| 1 | dsl > 100KB | 拒绝返回 NATIVE_PROCESS_FAILED | AC-3.1 |
| 2 | 处理成功 | 输出 durationMs INFO 日志 | AC-1.2 |
| 3 | format 含 `%{private}` | 整条脱敏 | AC-4.1 |
| 4 | 消息 > 4096 | 截断加 `[truncated]` | AC-4.4 |
| 5 | trace name 空 | 不启用 HiTrace | AC-2.5 |

## 兼容性声明

- **已有 API 行为变更:** 否（存量补录）。
- **配置文件格式变更:** 否。
- **数据存储格式变更:** 否。
- **最低支持版本:** A2UI 原生协议 v0.9。
- **API 版本号策略:** 打点对宿主透明，无公开契约变化。

## 架构约束

| 关键约束 | 约束说明 | 影响 AC |
|---------|---------|--------|
| 护栏优先 | DSL 长度检查先于解析 | AC-3.1,AC-3.2,AC-3.3,AC-3.4 |
| trace RAII | scope 构造/析构成对 | AC-2.3,AC-2.4 |
| 隐私优先 | `%{private}` 整条脱敏 | AC-4.1 |
| 长度上限 | 4096 截断 + `[truncated]` | AC-4.4,AC-4.5 |

## 非功能性需求

| 类型 | 指标/阈值 | 验证方式 | 证据 |
|------|----------|---------|------|
| 性能 | 逐消息 durationMs 可观测 | hilog | `NativeEntry.cpp:1155-1158` |
| 自动化维测 | HiTrace 集成系统 trace | 真机 trace 面板 | `platform/ohos/PlatformTrace.cpp:27` |
| 安全 | `%{private}` 脱敏防泄漏 | C++ UT | `platform/common/PlatformLog.cpp:177-179` |
| 定界定位 | 超长 DSL 拒绝含长度与上限 | C++ UT | `NativeEntry.cpp:1143-1146` |

## 多设备适配声明

| 设备类型 | 行为差异 | 规格/约束 | 验证方式 | 证据 |
|---------|---------|----------|---------|------|
| 手机 | 无差异 | 打点/日志/护栏设备无关 | ohosTest | — |
| 平板 | 无差异 | 同上 | ohosTest | — |
| 折叠屏 | 无差异 | 同上 | ohosTest | — |

## 全局特性影响

| 特性 | 适用？ | 结论 | 关联场景 |
|------|-------|------|---------|
| 无障碍 | 否 | 打点层不涉及 | — |
| 大字体 | 否 | 不涉及 | — |
| 深色模式 | 否 | 不涉及 | — |
| 多窗口/分屏 | 否 | 打点设备无关 | — |
| 多用户 | 否 | 无差异 | — |
| 版本升级 | 是 | 打点日志格式向后兼容 | AC-1.1,AC-1.2,AC-1.3,AC-1.4 |
| 生态兼容 | 是 | A2UI 原生协议 v0.9 兼容 | 概述「目标版本」 |

## 行为场景（可选，Gherkin）

```gherkin
Feature: 大数据打点
  作为 引擎维护者
  我想要 逐消息耗时、HiTrace 与日志防护
  以便 定位大消息卡顿且不泄漏隐私

  Scenario: 超长 DSL 被拒绝
    Given 一条 DSL 长度为 200KB
    When 调用 ProcessMessage
    Then 返回 success=false 且 errorCode=NATIVE_PROCESS_FAILED

  Scenario: 成功消息输出耗时
    Given 一条合法 updateComponents 消息
    When ProcessMessage 处理成功
    Then hilog 输出 "ProcessMessage timing: messageType=UPDATE_COMPONENTS, durationMs=<n>"

  Scenario Outline: 日志隐私
    Given format 为 <format>
    When PlatformLogPrint 执行
    Then 输出 <result>

    Examples:
      | format              | result |
      | "pwd=%{private}s"   | "[A2UI log redacted: private format]" |
      | "id=%{public}zu"    | "id=42" |
```

## Spec 自审清单

- [x] 无"待定""TBD""TODO"等占位符
- [x] 所有 AC 使用 WHEN/THEN 格式，可独立测试
- [x] 范围边界明确（打点/护栏/日志防护归本 Feat；错误码归 Feat-01；告警可观测归 Feat-02）
- [x] 无语义模糊表述
- [x] AC 与规则表交叉一致
- [x] 规则表每条通过 5 项质量检查（可复现/可观测/边界值/关联AC/无冲突）

## context-references

```yaml
context-queries:
  - repo: "GenerativeUI/A2UIRender"
    query: "NativeEntry ProcessMessage CreateTimedProcessResultValue durationMs MAX_DSL_LENGTH DispatchV09Message PlatformTraceScope"
  - repo: "GenerativeUI/A2UIRender"
    query: "PlatformTraceScope OH_HiTrace_StartTrace FinishTrace PlatformLogPrint %{private} 4096 truncation"
```

**关键文档：** `genui/src/main/cpp/NativeEntry.cpp`、`genui/src/main/cpp/platform/common/PlatformTrace.cpp`、`genui/src/main/cpp/platform/ohos/PlatformTrace.cpp`、`genui/src/main/cpp/platform/common/PlatformLog.cpp`、`genui/src/main/cpp/platform/common/PlatformLog.h`