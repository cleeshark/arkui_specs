# 特性规格

> Func-07-04-22-Feat-02 事件处理链语义：固化鸿蒙扩展协议 EventHandler 链——6 类事件属性（onClick/onAppear/onChange/onSelect/onReachStart/onReachEnd）、handler 四字段（call/args/condition/as）、链式执行（condition 短路 → break 中断 → 三级 dispatcher 派发 → as 局部变量绑定）、内置动作（dispatchEvent/setDataModel/setAttributes）。基准实现：`@arkui-genius/genui`（A2UIRender）。

## 概述

| 属性 | 值 |
|------|-----|
| 特性名称 | 事件处理链语义 |
| 特性编号 | Func-07-04-22-Feat-02 |
| 优先级 | P0 |
| 目标版本 | 鸿蒙扩展协议（`ohos.a2ui.extended.catalog`） |
| SIG 归属 | GenUI SIG |
| 状态 | Baselined |
| 复杂度 | 复杂 |

## 本次变更范围（Delta）

| 类型 | 内容 | 说明 |
|------|------|------|
| ADDED | 无（存量补录） | 本特性为 Func-07-04-22 第二个 Feat，沿用 Feat-01 基线 design.md |

## 输入文档

| 文档 | 路径 | 状态 |
|------|------|------|
| Design | `07-frontend/04-generative-ui/22-interaction-action-chain/design.md` | Baselined |
| 事件链解析（C++） | `genui/src/main/cpp/components/actions/EventHandlerParser.cpp` | — |
| 事件链执行（C++） | `genui/src/main/cpp/components/actions/EventHandlerChainExecutor.cpp` | — |
| 派发器（C++） | `genui/src/main/cpp/components/actions/ActionDispatcher.cpp` | — |
| 动作注册表（C++） | `genui/src/main/cpp/components/actions/NativeActionRegistry.cpp` | — |
| 内置动作（C++） | `genui/src/main/cpp/components/actions/BuiltInActions.cpp` | — |
| 局部变量命名（C++） | `genui/src/main/cpp/utils/LocalVariableNameUtils.cpp` | — |
| 测试（C++） | `genui/src/test/cpp/suites/actions/EventHandlerChainExecutorTest.cpp`、`EventHandlerParserTest.cpp`、`EventHandlerBranchCoverageTest.cpp` | — |
| 概念参考（Docs） | `concepts/actions-and-functions.md`、`reference/functions/extension-functions.md` | 理解辅助 |

> 需求基线、不涉及项详见 proposal.md。design.md 与本文档并行产出，互不依赖。

---

## 用户故事

### US-1: 事件属性识别

**作为** 生成式 UI 宿主开发者,
**我想要** 引擎识别扩展组件的六类事件属性,
**以便** 事件触发时派发对应处理链。

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-1.1 | WHEN descriptor 含 `KNOWN_EVENT_NAMES` 六类之一（onClick/onAppear/onChange/onSelect/onReachStart/onReachEnd）且值为数组 THEN `EventHandlerParser::Parse` 产出对应 `EventListenerInfo`（`EventHandlerParser.cpp:23-24,37-44`） | 正常 |
| AC-1.2 | WHEN 事件键值非数组 THEN 该键被忽略（`EventHandlerParser.cpp:37`） | 异常 |
| AC-1.3 | WHEN 事件键不在六类内 THEN 该键被忽略（`EventHandlerParser.cpp:37`） | 异常 |
| AC-1.4 | WHEN handler 数组为空 THEN 不注册该事件（`EventHandlerParser.cpp:38-44`） | 边界 |

### US-2: handler 字段校验

**作为** 生成式 UI 宿主开发者,
**我想要** 引擎校验 handler 的 call/condition/as 字段,
**以便** 非法 handler 在解析期被拦截。

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-2.1 | WHEN handler 的 `call` 非 string 或为空 THEN 跳过该 handler（`EventHandlerParser.cpp:65-69`） | 异常 |
| AC-2.2 | WHEN handler 非对象 THEN 跳过并打警告（`EventHandlerParser.cpp:58-61`） | 异常 |
| AC-2.3 | WHEN `condition` 为对象（非 string） THEN 跳过该 handler（`EventHandlerParser.cpp:79-82`） | 异常 |
| AC-2.4 | WHEN `as` 非 string 且非 null THEN 跳过该 handler（`EventHandlerParser.cpp:86-89`） | 异常 |
| AC-2.5 | WHEN `as` 非法标识符名 THEN 丢弃绑定但保留 handler（`EventHandlerParser.cpp:90-98`） | 边界 |
| AC-2.6 | WHEN `call` 非空 THEN `IsValidHandler` 返回 true（`EventHandlerParser.cpp:107-110`） | 正常 |

### US-3: 链式执行与 condition 短路

**作为** 生成式 UI 宿主开发者,
**我想要** handler 按数组顺序执行且支持条件跳过,
**以便** 实现多步操作与条件分支。

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-3.1 | WHEN handler 列表非空 THEN `ExecuteChain` 按数组顺序依次执行（`EventHandlerChainExecutor.cpp:388-422`） | 正常 |
| AC-3.2 | WHEN `condition` 为空 THEN 无条件执行（`ResolveCondition` 返回 true，`EventHandlerChainExecutor.cpp:282-284`） | 正常 |
| AC-3.3 | WHEN `condition` 求值为 false THEN 跳过该 handler 且链继续（`EventHandlerChainExecutor.cpp:391-394`） | 边界 |
| AC-3.4 | WHEN `condition` 求值为 true THEN 执行该 handler（`EventHandlerChainExecutor.cpp:391-394`） | 正常 |
| AC-3.5 | WHEN condition 非 `{{ }}` 包裹（无表达式引擎 fallback） THEN 跳过该 handler（`EventHandlerChainExecutor.cpp:309-310`） | 边界 |

### US-4: break 中断

**作为** 生成式 UI 宿主开发者,
**我想要** 通过 `call:"break"` 中断链执行,
**以便** 按条件提前终止后续操作。

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-4.1 | WHEN `call=="break"` 为首 handler THEN 后续 handler 均不执行（`EventHandlerChainExecutor.cpp:396-399`） | 正常 |
| AC-4.2 | WHEN `call=="break"` 在链中间 THEN 之前 handler 执行、之后不执行（`EventHandlerChainExecutor.cpp:396-399`） | 正常 |
| AC-4.3 | WHEN `call=="break"` 为末 handler THEN 不影响前置执行（`EventHandlerChainExecutor.cpp:396-399`） | 边界 |
| AC-4.4 | WHEN `call=="break"` 且 `condition` 为 false THEN 不中断（先 condition 后 break，`EventHandlerChainExecutor.cpp:391-399`） | 边界 |
| AC-4.5 | WHEN 派发过程抛异常 THEN 打错误日志并立即中断链（`EventHandlerChainExecutor.cpp:403-417`） | 异常 |

### US-5: dispatcher 优先级

**作为** 生成式 UI 宿主开发者,
**我想要** 引擎按固定优先级派发 call,
**以便** 内置动作优先于同名函数。

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-5.1 | WHEN `CreateDefaultDispatchers` 构建 THEN 顺序为 NativeActionDispatcher → NativeFunctionDispatcher → BridgeFunctionDispatcher（`ActionDispatcher.cpp:79-86`） | 正常 |
| AC-5.2 | WHEN call 命中 NativeAction THEN 直接执行内置动作，不再落到后续派发器（`ActionDispatcher.cpp:26-35`） | 正常 |
| AC-5.3 | WHEN call 命中 NativeFunction THEN 执行原生函数（`ActionDispatcher.cpp:37-58`） | 正常 |
| AC-5.4 | WHEN call 均未命中 THEN BridgeFunctionDispatcher 兜底调用并打 `unknown call` 警告（`EventHandlerChainExecutor.cpp:374-380`） | 异常 |
| AC-5.5 | WHEN 派发成功且 `as` 非空且结果有效 THEN 绑定到 `localVariables`（`EventHandlerChainExecutor.cpp:419-421`） | 正常 |

### US-6: as 局部变量绑定与作用域

**作为** 生成式 UI 宿主开发者,
**我想要** 用 `as` 把函数返回值绑定为局部变量供后续 handler 引用,
**以便** 实现链内变量传递。

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-6.1 | WHEN `as` 非空且结果有效 THEN 后续 handler 通过 `$变量名` 引用该值（`EventHandlerChainExecutor.cpp:419-421`） | 正常 |
| AC-6.2 | WHEN `as` 为空 THEN 不绑定（`EventHandlerChainExecutor.cpp:419`） | 正常 |
| AC-6.3 | WHEN handler 返回无效值（void/null） THEN 不绑定 `as`（`EventHandlerChainExecutor.cpp:419-421`） | 边界 |
| AC-6.4 | WHEN `as` 名遮蔽 `$context` THEN 后续引用取 as 值（`EventHandlerChainExecutorTest.cpp:739-772`） | 边界 |
| AC-6.5 | WHEN `as` 名遮蔽模板变量 THEN 后续引用取 as 值（`EventHandlerChainExecutorTest.cpp:800-833`） | 边界 |
| AC-6.6 | WHEN `as` 名以 `__` 开头 THEN 被 `IsValidLocalVariableName` 判非法（`LocalVariableNameUtils.cpp:36-38`） | 边界 |
| AC-6.7 | WHEN 单次事件链结束 THEN `localVariables` 不跨链共享（`EventHandlerChainExecutorTest.cpp:674-691`） | 边界 |

### US-7: 内置动作

**作为** 生成式 UI 宿主开发者,
**我想要** 引擎提供 dispatchEvent/setDataModel/setAttributes 三个内置动作,
**以便** 实现实时联动与多步操作。

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-7.1 | WHEN `RegisterBuiltInActions` 执行 THEN 注册 dispatchEvent/setDataModel/setAttributes（`BuiltInActions.cpp:203-208`） | 正常 |
| AC-7.2 | WHEN `setDataModel` 的 `path` 非空 THEN `UpdateByPath`+`NotifyPathUpdate` 生效（`BuiltInActions.cpp:138-160`） | 正常 |
| AC-7.3 | WHEN `setDataModel` 的 `path` 为空 THEN 打警告并返回（`BuiltInActions.cpp:150-154`） | 异常 |
| AC-7.4 | WHEN `setAttributes` 的 `componentId` 为空 THEN 打警告并返回（`BuiltInActions.cpp:164-169`） | 异常 |
| AC-7.5 | WHEN `setAttributes` 的 `value` 非对象 THEN 打警告并返回（`BuiltInActions.cpp:171-176`） | 异常 |
| AC-7.6 | WHEN `setAttributes` 目标组件不存在 THEN 打警告并返回（`BuiltInActions.cpp:186-191`） | 异常 |
| AC-7.7 | WHEN `dispatchEvent` 的 `eventName` 为空 THEN 打警告并返回（`BuiltInActions.cpp:118-125`） | 异常 |
| AC-7.8 | WHEN `setAttributes` 组件存在且 value 为对象 THEN `component->ApplyDescriptor` 生效，扩展组件额外 `ApplyStyleDelta`（`BuiltInActions.cpp:193-197`） | 正常 |

## 验收追溯

| AC编号 | 关联规则 | 关联 Task | 验证方式 | 证据 |
|----|---------|----------|---------|------|
| AC-1.1,AC-1.2,AC-1.3,AC-1.4 | R-1 | T-2 | C++ UT：`EventHandlerParser::Parse` | `EventHandlerParser.cpp:23-50` |
| AC-2.1,AC-2.2,AC-2.3,AC-2.4,AC-2.5,AC-2.6 | R-2,R-3 | T-2 | C++ UT：`ParseHandlerArray`/`IsValidHandler` | `EventHandlerParser.cpp:52-110` |
| AC-3.1,AC-3.2,AC-3.3,AC-3.4,AC-3.5 | R-4 | T-2 | C++ UT：`ExecuteChain`/`ResolveCondition` | `EventHandlerChainExecutor.cpp:280-422` |
| AC-4.1,AC-4.2,AC-4.3,AC-4.4,AC-4.5 | R-5 | T-2 | C++ UT：break/异常短路 | `EventHandlerChainExecutor.cpp:396-417` |
| AC-5.1,AC-5.2,AC-5.3,AC-5.4,AC-5.5 | R-6 | T-2 | C++ UT：dispatcher 优先级 | `ActionDispatcher.cpp:26-86` |
| AC-6.1,AC-6.2,AC-6.3,AC-6.4,AC-6.5,AC-6.6,AC-6.7 | R-7,R-8 | T-2 | C++ UT：as 绑定/遮蔽/作用域 | `EventHandlerChainExecutorTest.cpp:208-888` |
| AC-7.1,AC-7.2,AC-7.3,AC-7.4,AC-7.5,AC-7.6,AC-7.7,AC-7.8 | R-9,R-10,R-11 | T-2 | C++ UT：内置动作 | `BuiltInActions.cpp:118-208` |

## 规则定义

| 规则ID | 类型 | 触发条件 | 预期行为 | 边界/约束 | 关联AC |
|--------|------|---------|---------|----------|--------|
| R-1 | 行为 | 事件键在六类内且值为数组 | 产出 EventListenerInfo | 非数组/未知键忽略 | AC-1.1,AC-1.2,AC-1.3,AC-1.4 |
| R-2 | 异常 | handler `call` 非 string 或空 | 跳过该 handler | 非对象同样跳过 | AC-2.1,AC-2.2 |
| R-3 | 边界 | `condition` 为对象 / `as` 非法 | 跳过 handler / 丢弃绑定 | as 非法名保留 handler | AC-2.3,AC-2.4,AC-2.5 |
| R-4 | 行为 | condition 为空或 true | 执行 handler；false 跳过 | 空=无条件执行 | AC-3.1,AC-3.2,AC-3.3,AC-3.4,AC-3.5 |
| R-5 | 异常 | `call=="break"` 或派发抛异常 | 立即中断链 | break 在 condition 之后判定 | AC-4.1,AC-4.2,AC-4.3,AC-4.4,AC-4.5 |
| R-6 | 行为 | call 派发 | NativeAction→NativeFunction→Bridge 顺序 | 首个命中即执行 | AC-5.1,AC-5.2,AC-5.3,AC-5.4 |
| R-7 | 行为 | `as` 非空且结果有效 | 绑定到 localVariables | 无效值不绑定 | AC-5.5,AC-6.1,AC-6.2,AC-6.3 |
| R-8 | 边界 | as 名遮蔽 $context/模板变量 | 后续引用取 as 值 | `__` 前缀为系统保留 | AC-6.4,AC-6.5,AC-6.6,AC-6.7 |
| R-9 | 行为 | setDataModel path 非空 | 更新 DataModel 并通知刷新 | path 空→告警 | AC-7.2,AC-7.3 |
| R-10 | 异常 | setAttributes 参数非法/组件不存在 | 告警并返回 | value 须对象 | AC-7.4,AC-7.5,AC-7.6 |
| R-11 | 异常 | dispatchEvent eventName 空 | 告警并返回 | — | AC-7.7 |

## 验证映射

| 编号 | 对应规格项 | 验证方式 | 验证重点 |
|------|----------|---------|---------|
| VM-1 | AC-1.1,AC-1.2,AC-1.3,AC-1.4 事件属性识别 | C++ UT | 六类事件、非数组忽略 |
| VM-2 | AC-2.1,AC-2.2,AC-2.3,AC-2.4,AC-2.5,AC-2.6 handler 字段 | C++ UT | call/condition/as 校验 |
| VM-3 | AC-3.1,AC-3.2,AC-3.3,AC-3.4,AC-3.5 condition 短路 | C++ UT | 链式顺序、条件跳过 |
| VM-4 | AC-4.1,AC-4.2,AC-4.3,AC-4.4,AC-4.5 break | C++ UT | 首/中/末 break、异常短路 |
| VM-5 | AC-5.1,AC-5.2,AC-5.3,AC-5.4,AC-5.5 dispatcher | C++ UT | 三级优先级 |
| VM-6 | AC-6.1,AC-6.2,AC-6.3,AC-6.4,AC-6.5,AC-6.6,AC-6.7 as 变量 | C++ UT | 绑定、遮蔽、作用域 |
| VM-7 | AC-7.1,AC-7.2,AC-7.3,AC-7.4,AC-7.5,AC-7.6,AC-7.7,AC-7.8 内置动作 | C++ UT | setDataModel/setAttributes/dispatchEvent |

## API 变更分析

> 存量补录，无新增/变更 API。本节列出受影响公开契约。

### 新增 API

N/A。

### 变更/废弃 API

| API 名称 | 变更类型 | 影响场景 | 迁移指引 | 关联 AC |
|----------|---------|---------|---------|--------|
| `SurfaceController.registerErrorCallback` | 既有 | 接收 LOCAL_FUNCTION(3101)/DYNAMIC_VALUE_RESOLVE_FAILED(3202)/GLOBAL_VARIABLE_NOT_FOUND(3203)/ILLEGAL_EXPRESSION(3204) 错误码 | 错误码数值稳定 | AC-4.5,AC-6.1 |
| 扩展组件事件属性（onClick 等） | 既有 | EventHandler 链挂载 | 仅扩展协议 Catalog | AC-1.1 |

> d.ts 位置：`genui/src/main/ets/interface/*.ets`。Kit：`@arkui-genius/genui`；权限：无。

## 接口规格

### 接口定义

**`EventHandlerParser::Parse(descriptor)`（内部，`EventHandlerParser.cpp:26`）**

| 属性 | 值 |
|------|-----|
| 函数签名 | `static EventHandlerMap Parse(const JsonValue& descriptor)` |
| 返回值 | `EventHandlerMap` — 事件名到 handler 数组的映射 |
| 开放范围 | 内部（framework-internal） |
| 错误码 | N/A |
| 关联 AC | AC-1.1,AC-1.2,AC-1.3,AC-1.4,AC-2.1,AC-2.2,AC-2.3,AC-2.4,AC-2.5,AC-2.6 |

**`EventHandlerChainExecutor::ExecuteChain(handlers, context)`（`EventHandlerChainExecutor.cpp:384`）**

| 属性 | 值 |
|------|-----|
| 函数签名 | `static void ExecuteChain(const std::vector<EventHandlerStep>& handlers, ExecutionContext& context)` |
| 返回值 | `void`（副作用写入 `context.localVariables` / DataModel / 组件属性） |
| 开放范围 | 内部 |
| 错误码 | N/A（异常仅日志，不断上报） |
| 关联 AC | AC-3.1,AC-3.2,AC-3.3,AC-3.4,AC-3.5,AC-4.1,AC-4.2,AC-4.3,AC-4.4,AC-4.5,AC-5.1,AC-5.2,AC-5.3,AC-5.4,AC-5.5,AC-6.1,AC-6.2,AC-6.3 |

**`RegisterBuiltInActions(registry)`（`BuiltInActions.cpp:203`）**

| 属性 | 值 |
|------|-----|
| 函数签名 | `void RegisterBuiltInActions(NativeActionRegistry& registry)` |
| 返回值 | `void`（注册 dispatchEvent/setDataModel/setAttributes） |
| 开放范围 | 内部 |
| 错误码 | N/A |
| 关联 AC | AC-7.1,AC-7.2,AC-7.3,AC-7.4,AC-7.5,AC-7.6,AC-7.7,AC-7.8 |

**参数约束**

| 参数 | 类型 | 必填 | 默认值 | 约束条件 |
|------|------|------|--------|---------|
| handler.call | string | 是 | — | 非空字符串；不支持表达式 |
| handler.args | object | 否 | — | 值支持 `{{ }}` 表达式 |
| handler.condition | string | 否 | — | `{{ }}` 表达式或空；空=无条件 |
| handler.as | string | 否 | — | 合法标识符且非 `__` 前缀 |
| setDataModel.path | string | 是 | — | 非空 |
| setAttributes.value | object | 是 | — | 必须为对象 |

**行为场景**

| # | 触发条件 | 预期行为 | 关联 AC |
|---|----------|----------|---------|
| 1 | handler 按序执行 | 依数组顺序派发 | AC-3.1 |
| 2 | condition false | 跳过，链继续 | AC-3.3 |
| 3 | call==break | 中断链 | AC-4.1,AC-4.2,AC-4.3 |
| 4 | 派发抛异常 | 中断链 | AC-4.5 |
| 5 | as 非空且结果有效 | 绑定局部变量 | AC-6.1 |
| 6 | setDataModel path 空 | 告警，不更新 | AC-7.3 |

## 兼容性声明

- **已有 API 行为变更:** 否（存量补录）。
- **配置文件格式变更:** 否。
- **数据存储格式变更:** 否。
- **最低支持版本:** 鸿蒙扩展协议（`ohos.a2ui.extended.catalog`）；标准组件 action 二模式见 Feat-01。
- **API 版本号策略:** EventHandler 链为鸿蒙扩展协议特有，Basic Catalog 不支持。

## 架构约束

| 关键约束 | 约束说明 | 影响 AC |
|---------|---------|--------|
| 单事件链作用域 | `localVariables` 不跨链共享 | AC-6.7 |
| dispatcher 优先级 | NativeAction 优先于同名函数 | AC-5.1,AC-5.2,AC-5.3,AC-5.4 |
| 系统变量保留 | `__` 前缀为系统全局变量保留 | AC-6.6 |
| 链内同步生效 | setDataModel 通知在同链内同步 | AC-7.2 |

## 非功能性需求

| 类型 | 指标/阈值 | 验证方式 | 证据 |
|------|----------|---------|------|
| 可靠性 | 非法 handler/参数不抛异常，告警降级 | C++ UT | `EventHandlerParser.cpp:58-82`、`BuiltInActions.cpp:150-176` |
| 可测试性 | 派发器可注册 lambda mock | C++ UT | `EventHandlerChainExecutorTest.cpp:119-135` |

## 多设备适配声明

| 设备类型 | 行为差异 | 规格/约束 | 验证方式 | 证据 |
|---------|---------|----------|---------|------|
| 手机 | 无差异 | 事件链语义与设备无关 | C++ UT | — |
| 平板 | 无差异 | 同上 | C++ UT | — |
| 折叠屏 | 无差异 | 同上 | C++ UT | — |

## 全局特性影响

| 特性 | 适用？ | 结论 | 关联场景 |
|------|-------|------|---------|
| 无障碍 | 否 | 事件链层不涉及 | — |
| 大字体 | 否 | 不涉及 | — |
| 深色模式 | 是 | condition 可引用 `$__colorMode` | AC-3.1,AC-3.2,AC-3.3,AC-3.4,AC-3.5（`EventHandlerChainExecutorTest.cpp:310-342`） |
| 多窗口/分屏 | 否 | 多 Surface 见 07-04-01 | — |
| 多用户 | 否 | 无差异 | — |
| 版本升级 | 是 | 扩展协议特有，Basic Catalog 无 EventHandler 链 | 概述「目标版本」 |
| 生态兼容 | 否 | 为鸿蒙扩展能力，不属 A2UI 原生契约 | 概述「目标版本」 |

## 行为场景（可选，Gherkin）

```gherkin
Feature: 事件处理链语义
  作为 生成式 UI 宿主开发者
  我想要 引擎按序执行 handler 链并支持条件/中断/变量
  以便 实现多步操作与条件分支

  Scenario: 链式顺序执行
    Given onClick 为 [{"call":"a"},{"call":"b"},{"call":"c"}]
    When 事件触发
    Then a、b、c 依次执行

  Scenario: condition 短路
    Given onClick 为 [{"call":"a","condition":"{{ false }}"},{"call":"b"}]
    When 事件触发
    Then 跳过 a，执行 b

  Scenario: break 中断
    Given onClick 为 [{"call":"a"},{"call":"break"},{"call":"b"}]
    When 事件触发
    Then 执行 a，中断，不执行 b

  Scenario: as 变量传递
    Given onClick 为 [{"call":"getSelectValue","args":{"componentId":"s"},"as":"v"},{"call":"setDataModel","args":{"path":"/x","value":"{{ $v }}"}}]
    When 事件触发
    Then setDataModel 收到 getSelectValue 的返回值

  Scenario Outline: 内置动作非法参数
    Given onClick 为 [<handler>]
    When 事件触发
    Then 打警告且无副作用

    Examples:
      | handler |
      | {"call":"setDataModel","args":{"path":""}} |
      | {"call":"setAttributes","args":{"componentId":"x","value":"not-object"}} |
      | {"call":"dispatchEvent","args":{"eventName":""}} |
```

## Spec 自审清单

- [x] 无"待定""TBD""TODO"等占位符
- [x] 所有 AC 使用 WHEN/THEN 格式，可独立测试
- [x] 范围边界明确（Feat-02 做事件链执行语义；Action 模型与 event 上报见 Feat-01；函数实现语义归 07-04-16/20）
- [x] 无语义模糊表述
- [x] AC 与规则表交叉一致
- [x] 规则表每条通过 5 项质量检查（可复现/可观测/边界值/关联AC/无冲突）

## context-references

```yaml
context-queries:
  - repo: "GenerativeUI/A2UIRender"
    query: "EventHandlerParser KNOWN_EVENT_NAMES ParseHandlerArray EventHandlerStep call args condition as"
  - repo: "GenerativeUI/A2UIRender"
    query: "EventHandlerChainExecutor ExecuteChain ResolveCondition break as localVariables"
  - repo: "GenerativeUI/A2UIRender"
    query: "ActionDispatcher CreateDefaultDispatchers NativeActionDispatcher NativeFunctionDispatcher BridgeFunctionDispatcher"
  - repo: "GenerativeUI/A2UIRender"
    query: "BuiltInActions RegisterBuiltInActions dispatchEvent setDataModel setAttributes"
```

**关键文档：** `genui/src/main/cpp/components/actions/EventHandlerParser.cpp`、`genui/src/main/cpp/components/actions/EventHandlerChainExecutor.cpp`、`genui/src/main/cpp/components/actions/ActionDispatcher.cpp`、`genui/src/main/cpp/components/actions/NativeActionRegistry.cpp`、`genui/src/main/cpp/components/actions/BuiltInActions.cpp`、`genui/src/main/cpp/utils/LocalVariableNameUtils.cpp`
