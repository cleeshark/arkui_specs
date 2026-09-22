# 特性规格

> Func-07-04-19-Feat-01 通用事件模型与触发契约：固化事件名白名单（`onClick`/`onAppear`/`onChange`/`onSelect`/`onReachStart`/`onReachEnd`）、标准组件 `action` 契约（`A2UIServerAction`/`A2UILocalFunctionAction` 二选一）、扩展组件 EventHandler 链结构（`call`/`args`/`condition`/`as`）、事件解析与 schema 校验、各组件事件触发注册点与 action 优先级。基准实现：`@arkui-genius/genui`（A2UIRender）。

## 概述

| 属性 | 值 |
|------|-----|
| 特性名称 | 通用事件模型与触发契约 |
| 特性编号 | Func-07-04-19-Feat-01 |
| 优先级 | P0 |
| 目标版本 | A2UI 原生协议 v0.9 + 鸿蒙扩展协议（`ohos.a2ui.extended.catalog`） |
| SIG 归属 | GenUI SIG |
| 状态 | Baselined |
| 复杂度 | 标准 |

## 本次变更范围（Delta）

| 类型 | 内容 | 说明 |
|------|------|------|
| ADDED | 无（存量补录） | 本特性为 Func-07-04-19 首个 Feat，作为该功能域 design.md 基线 |

## 输入文档

| 文档 | 路径 | 状态 |
|------|------|------|
| Design | `07-frontend/04-generative-ui/19-common-events/design.md` | Baselined |
| 事件名/链解析（C++） | `genui/src/main/cpp/components/actions/EventHandlerParser.cpp` | — |
| 动作解析（C++） | `genui/src/main/cpp/functions/ActionParser.cpp`、`ActionInfo.cpp` | — |
| 事件 schema 校验（C++） | `genui/src/main/cpp/SurfaceSlotSchemaValidation.cpp` | — |
| action 契约 schema（ArkTS） | `genui/src/main/ets/core/types/Action.ets`、`FunctionCall.ets` | — |
| 事件注册（C++） | `genui/src/main/cpp/components/extended/ExtendedComponent.cpp`、`components/A2UI/A2UIComponent.cpp` | — |
| 交互概念（Docs） | `concepts/actions-and-functions.md` | 理解辅助 |

> 需求基线、不涉及项详见 proposal.md。design.md 与本文档并行产出，互不依赖。

---

## 用户故事

### US-1: 事件名称白名单识别

**作为** 生成式 UI 宿主开发者,
**我想要** 引擎只识别受支持的事件属性名,
**以便** 未知事件键不产生绑定且能被 schema 校验正确区分。

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-1.1 | WHEN 组件 descriptor 含 `onClick`/`onAppear`/`onChange`/`onSelect`/`onReachStart`/`onReachEnd` 任一键且值为数组 THEN `EventHandlerParser::Parse` 生成对应 `EventListenerInfo`（`EventHandlerParser.cpp:23-24,37-45`） | 正常 |
| AC-1.2 | WHEN 组件 descriptor 事件键值非数组（如对象/标量） THEN `Parse` 不生成 handler（`EventHandlerParser.cpp:37`） | 异常 |
| AC-1.3 | WHEN 事件键不在白名单内 THEN `ExtendedComponent::IsKnownAdditionalDescriptorKey` 不将之视为事件键，`Parse` 不生成 handler（`ExtendedComponent.cpp:580-581`、`EventHandlerParser.cpp:26-50`） | 边界 |
| AC-1.4 | WHEN 事件键值数组为空 THEN `Parse` 不生成 `EventListenerInfo`（`EventHandlerParser.cpp:38-39`） | 边界 |

### US-2: action 属性契约（标准组件）

**作为** 生成式 UI 宿主开发者,
**我想要** 标准组件用单一 `action` 表达服务端事件或本地函数调用,
**以便** 与 A2UI v0.9 标准对齐。

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-2.1 | WHEN `action` 只含 `event` 键且 `event.name` 非空 string THEN `ActionParser::Parse` 返回 `ActionType::EVENT` 的合法 `ActionInfo`（`ActionParser.cpp:185-188,143-144`） | 正常 |
| AC-2.2 | WHEN `action` 只含 `functionCall` 键且 `functionCall.call` 非空 THEN `ActionParser::Parse` 返回 `ActionType::FUNCTION_CALL` 的合法 `ActionInfo`（`ActionParser.cpp:179-184,89-115`） | 正常 |
| AC-2.3 | WHEN `action` 同时含 `event` 与 `functionCall` THEN `Parse` 丢弃并返回 null（`ActionParser.cpp:174-177`） | 异常 |
| AC-2.4 | WHEN `action` 既不含 `event` 也不含 `functionCall` THEN `Parse` 返回 null（`ActionParser.cpp:189`） | 异常 |
| AC-2.5 | WHEN `action.event.name` 缺失或空 string THEN `ParseEventAction` 返回 null（`ActionParser.cpp:124-128`） | 异常 |
| AC-2.6 | WHEN `action.event.context` 存在但非对象 THEN `ParseEventAction` 告警并回落为空 context（`ActionParser.cpp:140-142`） | 异常 |

### US-3: EventHandler 链结构

**作为** 生成式 UI 宿主开发者,
**我想要** 用 handler 数组表达多步事件响应,
**以便** 支持条件跳过、链中断与局部变量绑定。

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-3.1 | WHEN handler 项 `call` 为非空 string THEN 解析为 `EventHandlerStep`（`EventHandlerParser.cpp:65-70,107-110`） | 正常 |
| AC-3.2 | WHEN handler 项非对象或 `call` 非 string THEN 跳过该项，链继续（`EventHandlerParser.cpp:58-61,66-68`） | 异常 |
| AC-3.3 | WHEN `condition` 为 string THEN 记录到 `step.condition`；为对象（非 string）THEN 跳过该项（`EventHandlerParser.cpp:76-82`） | 边界 |
| AC-3.4 | WHEN `as` 为合法局部变量名 THEN 记录到 `step.as`；非法名（`IsValidLocalVariableName` 为 false）THEN 丢弃绑定但保留 handler（`EventHandlerParser.cpp:84-98`） | 边界 |
| AC-3.5 | WHEN `args` 存在 THEN 记录到 `step.args`（`EventHandlerParser.cpp:72-74`） | 正常 |

### US-4: 事件链 schema 校验

**作为** 生成式 UI 宿主开发者,
**我想要** 非法事件链结构在消息处理期被 schema 告警,
**以便** 问题可定位到具体组件与字段。

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-4.1 | WHEN 事件属性值非数组 THEN `ValidateEventHandlerFields` 派发 `SCHEMA_ERROR_CODE_TYPE_MISMATCH` 告警（`SurfaceSlotSchemaValidation.cpp:255-260`） | 异常 |
| AC-4.2 | WHEN handler 项非对象 THEN 派发 `TYPE_MISMATCH` 告警并 continue（`SurfaceSlotSchemaValidation.cpp:268-275`） | 异常 |
| AC-4.3 | WHEN handler `call` 缺非 string 或为空 THEN 派发 `TYPE_MISMATCH`/`REQUIRED_MISS` 或 `INVALID_VALUE` 告警（`SurfaceSlotSchemaValidation.cpp:279-293`） | 异常 |
| AC-4.4 | WHEN handler `as` 非 string 或非法局部变量名 THEN 派发 `TYPE_MISMATCH`/`INVALID_VALUE` 告警（`SurfaceSlotSchemaValidation.cpp:218-236`） | 异常 |

### US-5: 事件触发注册与 action 优先级

**作为** 生成式 UI 宿主开发者,
**我想要** 各组件在恰当时机触发对应事件,
**以便** 事件只在定义了 handler 时注册节点监听。

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-5.1 | WHEN 组件定义了 `onClick` handler THEN `RegisterClickHandler` 调用 `RegisterOnClickWithContext`（`ExtendedComponent.cpp:530-534`） | 正常 |
| AC-5.2 | WHEN 组件定义了 `onAppear` handler THEN `RegisterAppearHandler` 注册 `ON_APPEAR` 节点事件（`ExtendedComponent.cpp:539-543`） | 正常 |
| AC-5.3 | WHEN 组件未定义 `onClick`/`onAppear` handler THEN 注册逻辑回退为 nullptr（`ExtendedComponent.cpp:532-533,541-542`） | 边界 |
| AC-5.4 | WHEN Button 定义了合法 `action` THEN `RegisterOnClick([DispatchAction])` 生效，onClick 事件链不注册（`ButtonComponent.cpp:134-135`） | 正常 |
| AC-5.5 | WHEN Button 未定义合法 `action` THEN 不注册 action 点击（`ButtonComponent.cpp:134` 条件为 false） | 边界 |

### US-6: action 属性 schema 校验

**作为** 生成式 UI 宿主开发者,
**我想要** 非法 action 属性被 schema 告警,
**以便** 字段问题可定位。

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-6.1 | WHEN `action` 非对象 THEN 派发 `SCHEMA_ERROR_CODE_TYPE_MISMATCH` 且忽略字段（`Component.cpp:1746-1750`） | 异常 |
| AC-6.2 | WHEN `action` 同时含 `event` 与 `functionCall` THEN 派发 `SCHEMA_ERROR_CODE_INVALID_VALUE`（`Component.cpp:1755-1758`） | 异常 |
| AC-6.3 | WHEN `action` 缺 `event` 与 `functionCall` THEN 派发 `SCHEMA_ERROR_CODE_REQUIRED_MISS`（`Component.cpp:1760-1763`） | 异常 |
| AC-6.4 | WHEN `event.name` 缺失或非 string THEN 派发 `TYPE_MISMATCH`/`REQUIRED_MISS` 告警（`Component.cpp:1709-1721`） | 异常 |

## 验收追溯

| AC编号 | 关联规则 | 关联 Task | 验证方式 | 证据 |
|----|---------|----------|---------|------|
| AC-1.1,AC-1.2,AC-1.3,AC-1.4 | R-1,R-2 | T-1 | C++ UT：`EventHandlerParser::Parse` | `EventHandlerParser.cpp:23-50`、`ExtendedComponent.cpp:575-584` |
| AC-2.1,AC-2.2,AC-2.3,AC-2.4,AC-2.5,AC-2.6 | R-3,R-4,R-5 | T-1 | C++ UT：`ActionParser::Parse` | `ActionParser.cpp:117-190` |
| AC-3.1,AC-3.2,AC-3.3,AC-3.4,AC-3.5 | R-6,R-7 | T-1 | C++ UT：`ParseHandlerArray` | `EventHandlerParser.cpp:52-110` |
| AC-4.1,AC-4.2,AC-4.3,AC-4.4 | R-8 | T-1 | C++ UT：`ValidateEventHandlerFields` | `SurfaceSlotSchemaValidation.cpp:218-296` |
| AC-5.1,AC-5.2,AC-5.3,AC-5.4,AC-5.5 | R-9,R-10 | T-1 | C++ UT：组件注册逻辑 | `ExtendedComponent.cpp:521-546`、`ButtonComponent.cpp:123-139` |
| AC-6.1,AC-6.2,AC-6.3,AC-6.4 | R-11 | T-1 | C++ UT：`ValidateActionSpecialProperty` | `Component.cpp:1699-1771` |

## 规则定义

| 规则ID | 类型 | 触发条件 | 预期行为 | 边界/约束 | 关联AC |
|--------|------|---------|---------|----------|--------|
| R-1 | 行为 | 组件 descriptor 键属于 6 个白名单事件名且值为数组 | 生成 `EventListenerInfo` | 白名单见 `EventHandlerParser.cpp:23-24` | AC-1.1 |
| R-2 | 边界 | 事件键值非数组或空数组或键不在白名单 | 不生成 handler | 空数组亦不生成 | AC-1.2,AC-1.3,AC-1.4 |
| R-3 | 行为 | action 含 `event` 且 `event.name` 非空 | 返回 `ActionType::EVENT` | `name` 必填 string | AC-2.1 |
| R-4 | 行为 | action 含 `functionCall` 且 `call` 非空 | 返回 `ActionType::FUNCTION_CALL` | `call` 必填 | AC-2.2 |
| R-5 | 异常 | action 同时含 event 与 functionCall、或两者皆缺、或 event.name 空、或 context 非对象 | 解析失败/回落 | 二选一强制 | AC-2.3,AC-2.4,AC-2.5,AC-2.6 |
| R-6 | 行为 | handler 项 call 非空 string | 生成 `EventHandlerStep` | call 必填 | AC-3.1 |
| R-7 | 边界 | handler 异常结构（非对象/call 非 string/condition 对象/as 非法） | 跳过该项或丢弃 as 绑定 | as 丢弃不丢弃 handler | AC-3.2,AC-3.3,AC-3.4 |
| R-8 | 异常 | 事件值非数组、handler 非对象、call 缺/空、as 非法 | 派发 schema 告警 | TYPE_MISMATCH/REQUIRED_MISS/INVALID_VALUE | AC-4.1,AC-4.2,AC-4.3,AC-4.4 |
| R-9 | 行为 | 组件定义 onClick/onAppear handler | 注册对应节点监听；未定义则回退 nullptr | 有 handler 才注册 | AC-5.1,AC-5.2,AC-5.3 |
| R-10 | 行为 | Button 定义合法 action | action 点击生效，onClick 链不注册 | action 优先级 | AC-5.4,AC-5.5 |
| R-11 | 异常 | action 结构非法 | 派发 schema 告警并忽略字段 | 见 `Component.cpp:1744-1771` | AC-6.1,AC-6.2,AC-6.3,AC-6.4 |

## 验证映射

| 编号 | 对应规格项 | 验证方式 | 验证重点 |
|------|----------|---------|---------|
| VM-1 | AC-1.1,AC-1.2,AC-1.3,AC-1.4 事件名白名单 | C++ UT | 6 事件名、非数组/空数组/未知键 |
| VM-2 | AC-2.1,AC-2.2,AC-2.3,AC-2.4,AC-2.5,AC-2.6 action 契约 | C++ UT | event/functionCall 二选一、name 空 |
| VM-3 | AC-3.1,AC-3.2,AC-3.3,AC-3.4,AC-3.5 链结构 | C++ UT | call/condition/as/args |
| VM-4 | AC-4.1,AC-4.2,AC-4.3,AC-4.4 链 schema 校验 | C++ UT | TYPE_MISMATCH 等告警码 |
| VM-5 | AC-5.1,AC-5.2,AC-5.3,AC-5.4,AC-5.5 触发注册 | C++ UT | onClick/onAppear 注册与 action 优先级 |
| VM-6 | AC-6.1,AC-6.2,AC-6.3,AC-6.4 action schema 校验 | C++ UT | 二选一/必填告警 |

## API 变更分析

> 存量补录，无新增/变更 API。本节列出受影响公开契约。

### 新增 API

N/A。

### 变更/废弃 API

| API 名称 | 变更类型 | 影响场景 | 迁移指引 | 关联 AC |
|----------|---------|---------|---------|--------|
| `SurfaceController.registerActionReceiver` | 既有 | action 回传入口 | 宿主注册回调接收 action | AC-5.1,AC-5.2,AC-5.3,AC-5.4,AC-5.5 |
| `A2UIAction`/`A2UIServerAction`/`A2UIEventAction`/`A2UILocalFunctionAction` | 既有 | 组件 `action` 契约 schema | 无 | AC-2.1,AC-2.2,AC-2.3,AC-2.4,AC-2.5,AC-2.6 |

> d.ts 位置：`genui/src/main/ets/core/types/Action.ets`、`genui/src/main/ets/interface/SurfaceController.ets`。Kit：`@arkui-genius/genui`；权限：无。

## 接口规格

### 接口定义

**`EventHandlerParser::Parse(descriptor)`（内部，`EventHandlerParser.cpp:26`）**

| 属性 | 值 |
|------|-----|
| 函数签名 | `static EventHandlerMap Parse(const JsonValue& descriptor)` |
| 返回值 | `EventHandlerMap` — 事件名 → `EventListenerInfo{eventName, handlers}` |
| 开放范围 | 内部（framework-internal） |
| 错误码 | N/A |
| 关联 AC | AC-1.1,AC-1.2,AC-1.3,AC-1.4 |

**`ActionParser::Parse(descriptor[, context])`（内部，`ActionParser.cpp:149/154`）**

| 属性 | 值 |
|------|-----|
| 函数签名 | `static std::shared_ptr<ActionInfo> Parse(const JsonValue& descriptor, const ActionParseContext& context)` |
| 返回值 | `ActionInfo`（EVENT/FUNCTION_CALL）；`nullptr` — 非对象/二选一冲突/name 空/context 超深 |
| 开放范围 | 内部 |
| 错误码 | 解析错误经 `RuntimeErrorDispatchBridge` 派发 `SURFACE_ERROR_ACTION_PARSE_FAILED`（`ActionParser.cpp:31-38`） |
| 关联 AC | AC-2.1,AC-2.2,AC-2.3,AC-2.4,AC-2.5,AC-2.6 |

**参数约束**

| 参数 | 类型 | 必填 | 默认值 | 约束条件 |
|------|------|------|--------|---------|
| descriptor | JsonValue | 是 | — | 对象，含 `action` 键或自身为 action 对象 |
| event.name | string | 是 | — | 非空 string |
| event.context | object | 否 | `{}` | 对象，递归深度 ≤ `MAX_EVENT_CONTEXT_DEPTH=20` |
| handler.call | string | 是 | — | 非空 string，标识符引用（不支持表达式） |
| handler.condition | string | 否 | 无 | `{{ }}` 表达式 string |
| handler.as | string | 否 | 无 | 合法局部变量名 |

**行为场景**

| # | 触发条件 | 预期行为 | 关联 AC |
|---|----------|----------|---------|
| 1 | descriptor 含白名单事件键且值为数组 | 返回含 `EventListenerInfo` 的 map | AC-1.1 |
| 2 | 事件键值非数组/空数组/未知键 | 返回空 map（或不出该键） | AC-1.2,AC-1.3,AC-1.4 |
| 3 | action 只含 event 且 name 非空 | 返回 EVENT 的 ActionInfo | AC-2.1 |
| 4 | action 只含 functionCall | 返回 FUNCTION_CALL 的 ActionInfo | AC-2.2 |
| 5 | event 与 functionCall 并存/皆缺/name 空 | 返回 nullptr | AC-2.3,AC-2.4,AC-2.5 |
| 6 | handler call 非空 string | 生成 valid handler step | AC-3.1 |

## 兼容性声明

- **已有 API 行为变更:** 否（存量补录）。
- **配置文件格式变更:** 否。
- **数据存储格式变更:** 否。
- **最低支持版本:** A2UI 原生协议 v0.9。
- **API 版本号策略:** 事件名白名单与 action schema 均为协议契约的一部分；`A2UIEventAction` schema 要求 `name` 必填，`context` 为可选对象（`Action.ets:19-41`）。

## 架构约束

| 关键约束 | 约束说明 | 影响 AC |
|---------|---------|--------|
| 事件名白名单双处声明 | `EventHandlerParser.cpp:23` 与 `SurfaceSlotSchemaValidation.cpp:34` 需一致 | AC-1.1,AC-1.2,AC-1.3,AC-1.4 |
| action 二选一 | `event`/`functionCall` 禁止并存 | AC-2.3,AC-6.2 |
| 事件上下文深度上限 | `MAX_EVENT_CONTEXT_DEPTH=20` | AC-2.6 |
| 标识符引用不写表达式 | `call`/`as` 为标识符引用 | AC-3.1,AC-3.4 |

## 非功能性需求

| 类型 | 指标/阈值 | 验证方式 | 证据 |
|------|----------|---------|------|
| 可靠性 | 非法事件结构不崩溃，统一跳过/告警 | C++ UT | `EventHandlerParser.cpp:58-103` |
| 性能 | 事件上下文递归深度受 `MAX_EVENT_CONTEXT_DEPTH=20` 约束，防深嵌套爆栈 | C++ UT | `ActionParser.cpp:40-62` |

## 多设备适配声明

| 设备类型 | 行为差异 | 规格/约束 | 验证方式 | 证据 |
|---------|---------|----------|---------|------|
| 手机 | 无差异 | 事件模型设备无关 | ohosTest | — |
| 平板 | 无差异 | 同上 | ohosTest | — |
| 折叠屏 | 无差异 | 同上 | ohosTest | — |

## 全局特性影响

| 特性 | 适用？ | 结论 | 关联场景 |
|------|-------|------|---------|
| 无障碍 | 否 | 事件模型层不涉及 | — |
| 大字体 | 否 | 不涉及 | — |
| 深色模式 | 否 | 不涉及 | — |
| 多窗口/分屏 | 否 | 多 Surface 归 07-04-01 | — |
| 多用户 | 否 | 无差异 | — |
| 版本升级 | 是 | 事件名/action schema 为协议契约 | AC-1.1,AC-1.2,AC-1.3,AC-1.4,AC-2.1,AC-2.2,AC-2.3,AC-2.4,AC-2.5,AC-2.6 |
| 生态兼容 | 是 | A2UI 原生协议 v0.9 `action` 契约兼容 | AC-2.1,AC-2.2,AC-2.3,AC-2.4,AC-2.5,AC-2.6 |

## 行为场景（可选，Gherkin）

```gherkin
Feature: 通用事件模型与触发契约
  作为 生成式 UI 宿主开发者
  我想要 识别事件名并解析 action/EventHandler 链
  以便 非法契约快速失败

  Scenario: 白名单事件名解析成功
    Given 组件 descriptor 含 {"onClick":[{"call":"setDataModel","args":{"path":"/a","value":1}}]}
    When 调用 EventHandlerParser::Parse
    Then 返回 map 含 onClick 的 EventListenerInfo 且 handlers 长度 1

  Scenario Outline: action 契约拒绝
    Given action 为 <action>
    When 调用 ActionParser::Parse
    Then 返回 null

    Examples:
      | action |
      | {"event":{},"functionCall":{"call":"x"}} |
      | {} |
      | {"event":{"name":""}} |
      | {"event":{"name":"ok","context":[1,2]}} |
```

## Spec 自审清单

- [x] 无"待定""TBD""TODO"等占位符
- [x] 所有 AC 使用 WHEN/THEN 格式，可独立测试
- [x] 范围边界明确（Feat-01 做事件模型与触发契约；上下文数据与分发见 Feat-02）
- [x] 无语义模糊表述
- [x] AC 与规则表交叉一致
- [x] 规则表每条通过 5 项质量检查（可复现/可观测/边界值/关联AC/无冲突）

## context-references

```yaml
context-queries:
  - repo: "GenerativeUI/A2UIRender"
    query: "EventHandlerParser KNOWN_EVENT_NAMES 事件名白名单 ParseHandlerArray call condition as"
  - repo: "GenerativeUI/A2UIRender"
    query: "ActionParser ActionInfo ActionType EVENT FUNCTION_CALL MAX_EVENT_CONTEXT_DEPTH"
  - repo: "GenerativeUI/A2UIRender"
    query: "Button action 优先级 RegisterOnClick DispatchAction ExtendedComponent RegisterExtendedListeners"
```

**关键文档：** `genui/src/main/cpp/components/actions/EventHandlerParser.cpp`、`genui/src/main/cpp/functions/ActionParser.cpp`、`genui/src/main/cpp/SurfaceSlotSchemaValidation.cpp`、`genui/src/main/ets/core/types/Action.ets`、`genui/src/main/cpp/components/extended/ExtendedComponent.cpp`