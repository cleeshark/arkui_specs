# 特性规格

> Func-07-04-22-Feat-01 交互模型：固化 A2UI Action 抽象——`action` 字段二模式（`functionCall` 本地执行 / `event` 上报 Agent）、`ActionInfo`/`FunctionCallInfo` 数据模型、二模式互斥（同现丢弃）、event context 深度上限（`MAX_EVENT_CONTEXT_DEPTH=20`）、event 经 `ActionDispatchBridge` 上报宿主（`registerActionReceiver`）。基准实现：`@arkui-genius/genui`（A2UIRender）。

## 概述

| 属性 | 值 |
|------|-----|
| 特性名称 | 交互模型 |
| 特性编号 | Func-07-04-22-Feat-01 |
| 优先级 | P0 |
| 目标版本 | A2UI 原生协议 v0.9 |
| SIG 归属 | GenUI SIG |
| 状态 | Baselined |
| 复杂度 | 复杂 |

## 本次变更范围（Delta）

| 类型 | 内容 | 说明 |
|------|------|------|
| ADDED | 无（存量补录） | 本特性为 Func-07-04-22 首个 Feat，作为该功能域 design.md 基线 |

## 输入文档

| 文档 | 路径 | 状态 |
|------|------|------|
| Design | `07-frontend/04-generative-ui/22-interaction-action-chain/design.md` | Baselined |
| 动作解析（C++） | `genui/src/main/cpp/functions/ActionParser.cpp` | — |
| 动作信息（C++） | `genui/src/main/cpp/functions/ActionInfo.cpp` | — |
| 函数调用信息（C++） | `genui/src/main/cpp/functions/FunctionCallInfo.cpp` | — |
| 事件上下文解析（C++） | `genui/src/main/cpp/functions/EventContextResolver.cpp` | — |
| 事件上报桥（C++） | `genui/src/main/cpp/functions/ActionDispatchBridge.cpp` | — |
| 错误码（C++ 权威源） | `genui/src/main/cpp/SurfaceErrorCodes.h` | — |
| 组件接入（C++） | `genui/src/main/cpp/components/A2UI/button/ButtonComponent.cpp`、`components/extended/ExtendedButtonComponent.cpp`、`components/extended/ExtendedComponent.cpp` | — |
| 概念参考（Docs） | `concepts/actions-and-functions.md`、`reference/functions/functioncall.md` | 理解辅助 |

> 需求基线、不涉及项详见 proposal.md。design.md 与本文档并行产出，互不依赖。

---

## 用户故事

### US-1: Action 二模式识别

**作为** 生成式 UI 宿主开发者,
**我想要** 渲染引擎识别 `action` 字段的 `functionCall` 与 `event` 两种模式,
**以便** 交互行为按模式正确派发。

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-1.1 | WHEN descriptor 含 `functionCall`（无 `event`） THEN `ActionParser::Parse` 返回 `ActionInfo`，`GetType()==ActionType::FUNCTION_CALL`（`ActionParser.cpp:179-184`） | 正常 |
| AC-1.2 | WHEN descriptor 含 `event`（无 `functionCall`） THEN `ActionParser::Parse` 返回 `ActionInfo`，`GetType()==ActionType::EVENT`（`ActionParser.cpp:185-187`） | 正常 |
| AC-1.3 | WHEN descriptor 同时含 `functionCall` 与 `event` THEN `ActionParser::Parse` 返回 null 并打 `functionCall and event both exist` 警告（`ActionParser.cpp:174-177`） | 异常 |
| AC-1.4 | WHEN descriptor 非对象（null/数组/标量）或 `action` 值非对象 THEN `ActionParser::Parse` 返回 null（`ActionParser.cpp:161-172`） | 异常 |
| AC-1.5 | WHEN descriptor 为 `{"action": {...}}` 包裹 THEN 取内层 `action` 值解析（`ActionParser.cpp:165-168`） | 正常 |

### US-2: functionCall 解析

**作为** 生成式 UI 宿主开发者,
**我想要** 引擎解析 functionCall 的名称、参数与返回类型,
**以便** 本地函数调用具备完整信息。

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-2.1 | WHEN `functionCall.call` 为合法字符串 THEN `ParseFunctionCall` 返回 `FunctionCallInfo`（`ActionParser.cpp:96-114`） | 正常 |
| AC-2.2 | WHEN `functionCall.call` 为空或非对象 THEN `ParseFunctionCall` 返回 null（`ActionParser.cpp:91-100`） | 异常 |
| AC-2.3 | WHEN `functionCall` 无 `returnType` THEN `returnType` 缺省 `"void"`（`ActionParser.cpp:113`） | 边界 |
| AC-2.4 | WHEN `functionCall.args` 存在 THEN 克隆为 `FunctionCallInfo.args`（`ActionParser.cpp:102-111`） | 正常 |
| AC-2.5 | WHEN `ActionInfo` 为 FUNCTION_CALL 且 `functionCall_` 非空且函数名非空 THEN `IsValid()` 返回 true（`ActionInfo.cpp:53-62`） | 正常 |

### US-3: event 解析与 context 校验

**作为** 生成式 UI 宿主开发者,
**我想要** 引擎校验 event 名称与 context 结构,
**以便** 非法 event 在解析期被拦截。

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-3.1 | WHEN `event.name` 为合法字符串 THEN `ParseEventAction` 返回 `ActionInfo(EVENT)`（`ActionParser.cpp:124-144`） | 正常 |
| AC-3.2 | WHEN `event.name` 为空或非对象 THEN `ParseEventAction` 返回 null（`ActionParser.cpp:119-128`） | 异常 |
| AC-3.3 | WHEN `event.context` 嵌套深度 ≤ 20 THEN 校验通过并保留 context（`ActionParser.cpp:40-62,130-144`） | 正常 |
| AC-3.4 | WHEN `event.context` 嵌套深度 > 20 THEN 派发 `SURFACE_ERROR_ACTION_PARSE_FAILED`(3201) 并丢弃 action（`ActionParser.cpp:45-49,133-138`） | 边界 |
| AC-3.5 | WHEN `event.context` 非对象（但有效） THEN 打警告并回退为 `{}`（`ActionParser.cpp:140-142`） | 异常 |
| AC-3.6 | WHEN `ActionInfo` 为 EVENT 且 `eventName_` 非空 THEN `IsValid()` 返回 true（`ActionInfo.cpp:58-60`） | 正常 |

### US-4: event context 递归解析

**作为** 生成式 UI 宿主开发者,
**我想要** event context 中的 path 与 functionCall 在派发前解析为实际值,
**以便** Agent 收到已解析的上下文数据。

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-4.1 | WHEN context 值为 `{"path": "..."}` THEN `EventContextResolver::Resolve` 解析为 DataModel 实际值（`EventContextResolver.cpp:152-162`） | 正常 |
| AC-4.2 | WHEN context 值为 `{"call": "...", "args": {...}}` THEN 递归求值为函数返回值（`EventContextResolver.cpp:152-162`） | 正常 |
| AC-4.3 | WHEN context 含 `call` 非 string 或空 THEN 派发 schema warning 并跳过该键（`EventContextResolver.cpp:52-82`） | 异常 |
| AC-4.4 | WHEN context 非对象 THEN 回退返回 `{}`（`EventContextResolver.cpp:199-206`） | 边界 |

### US-5: event 上报宿主

**作为** 生成式 UI 宿主开发者,
**我想要** event Action 通过 registerActionReceiver 回调上报,
**以便** Agent 据此生成下一轮响应。

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-5.1 | WHEN `ActionDispatchBridge::Dispatch` 被调用且桥已注册 THEN 回调收到 `{renderId, surfaceId, sourceComponentId, name, context}`（`ActionDispatchBridge.cpp:91-105`） | 正常 |
| AC-5.2 | WHEN 桥未注册（`dispatchActionRef_` 为空） THEN `Dispatch` 返回 false（`ActionDispatchBridge.cpp:68-71`） | 异常 |
| AC-5.3 | WHEN `RegisterDispatchAction` 收到非法回调 THEN 打错误并返回（`ActionDispatchBridge.cpp:44-47`） | 异常 |
| AC-5.4 | WHEN Button 的 `actionInfo_` 合法 THEN 注册 onClick 回调触发 `DispatchAction`（`ButtonComponent.cpp:134-136,298-315`） | 正常 |
| AC-5.5 | WHEN `ActionInfo` 为 EVENT 且宿主未注册 actionReceiver THEN 错误码 `SURFACE_ERROR_ACTION_NOT_REGISTER`(3001)（`SurfaceErrorCodes.h:59`） | 异常 |

## 验收追溯

| AC编号 | 关联规则 | 关联 Task | 验证方式 | 证据 |
|----|---------|----------|---------|------|
| AC-1.1,AC-1.2,AC-1.3,AC-1.4,AC-1.5 | R-1,R-2 | T-1 | C++ UT：`ActionParser::Parse` 二模式 | `ActionParser.cpp:154-190` |
| AC-2.1,AC-2.2,AC-2.3,AC-2.4,AC-2.5 | R-3 | T-1 | C++ UT：`ParseFunctionCall`/`ActionInfo::IsValid` | `ActionParser.cpp:89-115`、`ActionInfo.cpp:53-62` |
| AC-3.1,AC-3.2,AC-3.3,AC-3.4,AC-3.5,AC-3.6 | R-4,R-5 | T-1 | C++ UT：`ParseEventAction` 深度校验 | `ActionParser.cpp:117-145` |
| AC-4.1,AC-4.2,AC-4.3,AC-4.4 | R-6 | T-1 | C++ UT：`EventContextResolver::Resolve` | `EventContextResolver.cpp:191-233` |
| AC-5.1,AC-5.2,AC-5.3,AC-5.4,AC-5.5 | R-7 | T-1 | C++ UT + 静态比对错误码 | `ActionDispatchBridge.cpp:64-117`、`SurfaceErrorCodes.h:59` |

## 规则定义

| 规则ID | 类型 | 触发条件 | 预期行为 | 边界/约束 | 关联AC |
|--------|------|---------|---------|----------|--------|
| R-1 | 行为 | descriptor 含 `functionCall` 或 `event` 之一 | 解析为对应 `ActionType` | 二模式互斥 | AC-1.1,AC-1.2 |
| R-2 | 异常 | `functionCall` 与 `event` 同现 | `Parse` 返回 null | 丢弃整个 action | AC-1.3 |
| R-3 | 边界 | `functionCall.call` 空 / 非对象 | `ParseFunctionCall` 返回 null | `returnType` 缺省 "void" | AC-2.1,AC-2.2,AC-2.3,AC-2.4,AC-2.5 |
| R-4 | 行为 | `event.name` 非空 | `ActionInfo(EVENT)` | name 空→null | AC-3.1,AC-3.2 |
| R-5 | 边界 | `event.context` 深度 > 20 | 派发 3201 并丢弃 | `MAX_EVENT_CONTEXT_DEPTH=20` | AC-3.3,AC-3.4 |
| R-6 | 行为 | context 含 path/functionCall | 递归解析为实际值 | 非对象回退 {} | AC-4.1,AC-4.2,AC-4.3,AC-4.4 |
| R-7 | 行为 | event Action 派发 | 经 ActionDispatchBridge 上报宿主 | 未注册回调→3001 | AC-5.1,AC-5.2,AC-5.3,AC-5.4,AC-5.5 |

## 验证映射

| 编号 | 对应规格项 | 验证方式 | 验证重点 |
|------|----------|---------|---------|
| VM-1 | AC-1.1,AC-1.2,AC-1.3,AC-1.4,AC-1.5 二模式识别 | C++ UT | 二模式、互斥、action 包裹 |
| VM-2 | AC-2.1,AC-2.2,AC-2.3,AC-2.4,AC-2.5 functionCall | C++ UT | call/args/returnType 缺省 |
| VM-3 | AC-3.1,AC-3.2,AC-3.3,AC-3.4,AC-3.5,AC-3.6 event 解析 | C++ UT | name、context 深度 20 上限 |
| VM-4 | AC-4.1,AC-4.2,AC-4.3,AC-4.4 context 解析 | C++ UT | path/functionCall 递归求值 |
| VM-5 | AC-5.1,AC-5.2,AC-5.3,AC-5.4,AC-5.5 event 上报 | C++ UT + 静态比对 | 桥回调 + 错误码 3001 |

## API 变更分析

> 存量补录，无新增/变更 API。本节列出受影响公开契约。

### 新增 API

N/A。

### 变更/废弃 API

| API 名称 | 变更类型 | 影响场景 | 迁移指引 | 关联 AC |
|----------|---------|---------|---------|--------|
| `SurfaceController.registerActionReceiver` | 既有 | 接收 event Action（`action.event` 上报） | 数值稳定，宿主按 `action.name` 分类 | AC-5.1,AC-5.2,AC-5.3,AC-5.4,AC-5.5 |
| `SurfaceController.registerErrorCallback` | 既有 | 接收 3001/3101/3201 等错误码 | 错误码数值稳定 | AC-3.4,AC-5.5 |

> d.ts 位置：`genui/src/main/ets/interface/*.ets`。Kit：`@arkui-genius/genui`；权限：无。

## 接口规格

### 接口定义

**`ActionParser::Parse(descriptor[, context])`（内部，`ActionParser.cpp:154`）**

| 属性 | 值 |
|------|-----|
| 函数签名 | `static std::shared_ptr<ActionInfo> Parse(const JsonValue& descriptor, const ActionParseContext& context = {})` |
| 返回值 | `ActionInfo` — 解析成功；`nullptr` — 非对象/二模式同现/functionCall 或 event 非法 |
| 开放范围 | 内部（framework-internal） |
| 错误码 | `SURFACE_ERROR_ACTION_PARSE_FAILED`(3201)（context 深度超限时） |
| 关联 AC | AC-1.1,AC-1.2,AC-1.3,AC-1.4,AC-1.5,AC-2.1,AC-2.2,AC-2.3,AC-2.4,AC-2.5,AC-3.1,AC-3.2,AC-3.3,AC-3.4,AC-3.5,AC-3.6 |

**`EventContextResolver::Resolve(rawContextDescriptor, context)`（`EventContextResolver.cpp:191`）**

| 属性 | 值 |
|------|-----|
| 函数签名 | `static JsonValue Resolve(const JsonValue& rawContextDescriptor, const EventResolveContext& context)` |
| 返回值 | `JsonValue` — 解析后的 context 对象 |
| 开放范围 | 内部 |
| 错误码 | schema warning（TYPE_MISMATCH/REQUIRED_MISS） |
| 关联 AC | AC-4.1,AC-4.2,AC-4.3,AC-4.4 |

**`ActionDispatchBridge::Dispatch(renderId, surfaceId, sourceComponentId, eventName, context)`（`ActionDispatchBridge.cpp:64`）**

| 属性 | 值 |
|------|-----|
| 函数签名 | `bool Dispatch(int32_t renderId, const std::string& surfaceId, const std::string& sourceComponentId, const std::string& eventName, const JsonValue& context) const` |
| 返回值 | `bool` — 回调是否成功派发 |
| 开放范围 | 内部（经 NAPI `registerDispatchAction` 暴露） |
| 错误码 | N/A（返回 bool） |
| 关联 AC | AC-5.1,AC-5.2,AC-5.3,AC-5.4,AC-5.5 |

**参数约束**

| 参数 | 类型 | 必填 | 默认值 | 约束条件 |
|------|------|------|--------|---------|
| descriptor | JsonValue | 是 | — | 对象或含 `action` 键的对象 |
| functionCall.call | string | 是 | — | 非空字符串 |
| functionCall.returnType | string | 否 | `"void"` | string/number/boolean/array/object/any/void |
| event.name | string | 是 | — | 非空字符串 |
| event.context | object | 否 | `{}` | 深度 ≤ 20 |

**行为场景**

| # | 触发条件 | 预期行为 | 关联 AC |
|---|----------|----------|---------|
| 1 | 仅 functionCall | 返回 FUNCTION_CALL ActionInfo | AC-1.1 |
| 2 | 仅 event | 返回 EVENT ActionInfo | AC-1.2 |
| 3 | 两者同现 | 返回 null | AC-1.3 |
| 4 | context 深度 > 20 | 派发 3201，返回 null | AC-3.4 |
| 5 | event 桥未注册 | Dispatch 返回 false | AC-5.2 |

## 兼容性声明

- **已有 API 行为变更:** 否（存量补录）。
- **配置文件格式变更:** 否。
- **数据存储格式变更:** 否。
- **最低支持版本:** A2UI 原生协议 v0.9（functionCall/event 二模式）+ 鸿蒙扩展协议（EventHandler 链见 Feat-02）。
- **API 版本号策略:** Action 二模式为 A2UI v0.9 原生契约；`returnType` 缺省 "void"。

## 架构约束

| 关键约束 | 约束说明 | 影响 AC |
|---------|---------|--------|
| 二模式互斥 | functionCall 与 event 同现丢弃 | AC-1.3 |
| context 深度上限 | 嵌套 ≤ 20，超限报 3201 | AC-3.3,AC-3.4 |
| 桥回调 | event 上报依赖 registerActionReceiver | AC-5.1,AC-5.2,AC-5.3,AC-5.4,AC-5.5 |

## 非功能性需求

| 类型 | 指标/阈值 | 验证方式 | 证据 |
|------|----------|---------|------|
| 可靠性 | 非法 action 不抛异常，统一返回 null/错误码 | C++ UT | `ActionParser.cpp:161-190` |
| 性能 | context 深度 20 上限防栈溢出 | C++ UT | `ActionParser.cpp:40-62` |

## 多设备适配声明

| 设备类型 | 行为差异 | 规格/约束 | 验证方式 | 证据 |
|---------|---------|----------|---------|------|
| 手机 | 无差异 | Action 模型与设备无关 | C++ UT | — |
| 平板 | 无差异 | 同上 | C++ UT | — |
| 折叠屏 | 无差异 | 同上 | C++ UT | — |

## 全局特性影响

| 特性 | 适用？ | 结论 | 关联场景 |
|------|-------|------|---------|
| 无障碍 | 否 | Action 模型层不涉及 | — |
| 大字体 | 否 | 不涉及 | — |
| 深色模式 | 否 | 不涉及（context 表达式见 07-04-21） | — |
| 多窗口/分屏 | 否 | 多 Surface 见 07-04-01 | — |
| 多用户 | 否 | 无差异 | — |
| 版本升级 | 是 | Action 二模式为 v0.9 原生契约 | 概述「目标版本」 |
| 生态兼容 | 是 | A2UI 原生协议 v0.9 Action 兼容 | 概述「目标版本」 |

## 行为场景（可选，Gherkin）

```gherkin
Feature: 交互模型
  作为 生成式 UI 宿主开发者
  我想要 引擎解析 action 的 functionCall/event 两种模式
  以便 交互行为正确派发

  Scenario: functionCall 模式解析成功
    Given descriptor 为 {"action":{"functionCall":{"call":"openUrl","args":{"url":"https://example.com"}}}}
    When 调用 ActionParser.Parse
    Then 返回 ActionInfo，GetType()=FUNCTION_CALL

  Scenario: event 模式解析成功
    Given descriptor 为 {"action":{"event":{"name":"submit","context":{"email":{"path":"/form/email"}}}}}
    When 调用 ActionParser.Parse
    Then 返回 ActionInfo，GetType()=EVENT

  Scenario Outline: 非法 action 拒绝
    Given descriptor 为 <payload>
    When 调用 ActionParser.Parse
    Then 返回 null

    Examples:
      | payload |
      | {"action":{"functionCall":{},"event":{"name":"x"}}} |
      | {"action":{"functionCall":{"call":""}}} |
      | {"action":{"event":{"name":""}}} |
      | "not-an-object" |
```

## Spec 自审清单

- [x] 无"待定""TBD""TODO"等占位符
- [x] 所有 AC 使用 WHEN/THEN 格式，可独立测试
- [x] 范围边界明确（Feat-01 做 Action 模型与 event 上报；EventHandler 链执行见 Feat-02）
- [x] 无语义模糊表述
- [x] AC 与规则表交叉一致
- [x] 规则表每条通过 5 项质量检查（可复现/可观测/边界值/关联AC/无冲突）

## context-references

```yaml
context-queries:
  - repo: "GenerativeUI/A2UIRender"
    query: "ActionParser::Parse functionCall event 二模式互斥 MAX_EVENT_CONTEXT_DEPTH"
  - repo: "GenerativeUI/A2UIRender"
    query: "ActionInfo ActionType FUNCTION_CALL EVENT IsValid FunctionCallInfo returnType"
  - repo: "GenerativeUI/A2UIRender"
    query: "EventContextResolver::Resolve ActionDispatchBridge::Dispatch registerActionReceiver"
```

**关键文档：** `genui/src/main/cpp/functions/ActionParser.cpp`、`genui/src/main/cpp/functions/ActionInfo.cpp`、`genui/src/main/cpp/functions/FunctionCallInfo.cpp`、`genui/src/main/cpp/functions/EventContextResolver.cpp`、`genui/src/main/cpp/functions/ActionDispatchBridge.cpp`、`genui/src/main/cpp/components/A2UI/button/ButtonComponent.cpp`
