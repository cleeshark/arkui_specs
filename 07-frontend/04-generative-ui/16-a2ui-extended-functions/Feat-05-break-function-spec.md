# 特性规格

> Func-07-04-16-Feat-05 `break` 函数：固化 A2UI 鸿蒙扩展协议控制流函数 `break` 的语义——在 EventHandler 链中中断当前链，停止执行后续 handler。`break` 是链控制指令，**无 C++ 函数/动作注册**，由 `EventHandlerChainExecutor::ExecuteChain` 在分发前特殊识别（支持 `condition` 条件中断）。ArkTS 目录注册（`isInnerNative: true` + schema `break.json`，声明空 `args`、返回 `void`）。基准实现：`@arkui-genius/genui`（A2UIRender）。

## 概述

| 属性 | 值 |
|------|-----|
| 特性名称 | break 链中断函数 |
| 特性编号 | Func-07-04-16-Feat-05 |
| 优先级 | P0 |
| 目标版本 | A2UI 鸿蒙扩展协议（`ohos.a2ui.extended.catalog`）+ API Version 20 |
| SIG 归属 | GenUI SIG |
| 状态 | Baselined |
| 复杂度 | 标准 |

## 本次变更范围（Delta）

| 类型 | 内容 | 说明 |
|------|------|------|
| ADDED | 无（存量补录） | 本特性为 Func-07-04-16 第五个 Feat |

## 输入文档

| 文档 | 路径 | 状态 |
|------|------|------|
| Design | `07-frontend/04-generative-ui/16-a2ui-extended-functions/design.md` | Baselined |
| 目录注册（ArkTS） | `genui/src/main/ets/core/functions/extended/CatalogActionFunctions.ets` | — |
| 函数聚合（ArkTS） | `genui/src/main/ets/core/functions/A2UIBasicFunctions.ets` | — |
| 链执行（C++） | `genui/src/main/cpp/components/actions/EventHandlerChainExecutor.cpp` | — |
| schema | `genui/src/main/resources/rawfile/schema/Extended/functions/break.json` | — |
| 函数参考（Docs） | `reference/functions/extension-functions.md`、`concepts/actions-and-functions.md` | 理解辅助 |

> 需求基线、不涉及项详见 proposal.md。design.md 与本文档并行产出，互不依赖。

---

## 用户故事

### US-1: 目录注册与 schema 契约

**作为** 生成式 UI 宿主开发者,
**我想要** `break` 注册为扩展协议控制流函数,
**以便** DSL 的 `call="break"` 被引擎识别并受 schema 约束。

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-1.1 | WHEN 构造 THEN `breakFunction = new CatalogActionFunction('break', 'break.json')`（`CatalogActionFunctions.ets:48`） | 正常 |
| AC-1.2 | WHEN 目录项构建 THEN `asFunctionItem()` 返回 `name='break'` 且 `isInnerNative=true`（`CatalogActionFunctions.ets:30-37`） | 正常 |
| AC-1.3 | WHEN schema 加载 THEN `loadExtendedFunctionSchema('break.json')`（`CatalogActionFunctions.ets:39-41`） | 正常 |
| AC-1.4 | WHEN 聚合扩展内置函数 THEN `break` 列入 `extendedCatalogFunctions`（`A2UIBasicFunctions.ets:70`） | 正常 |
| AC-1.5 | WHEN 检测注册表 THEN `break` **不**在 `NativeFunctionRegistry`（`:66-86`）也不在 `NativeActionRegistry`（`BuiltInActions.cpp:203-208`）注册 | 边界 |

### US-2: 链中断（正常/边界）

**作为** 生成式 UI 宿主开发者,
**我想要** `break` 中断当前 EventHandler 链,
**以便** 条件满足时阻止后续 handler 执行。

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-2.1 | WHEN 当前 handler 的 `call == "break"` THEN `ExecuteChain` 立即 `break` 终止循环（`EventHandlerChainExecutor.cpp:396-399`） | 正常 |
| AC-2.2 | WHEN 后续 handler 位于 `break` 之后 THEN 不再执行（中断位于循环内 `break`，`EventHandlerChainExecutor.cpp:388-422`） | 正常 |
| AC-2.3 | WHEN `break` 的 `condition` 求值为 false THEN 该 handler 被 `ResolveCondition` 跳过，链继续（`EventHandlerChainExecutor.cpp:391-394`） | 边界 |
| AC-2.4 | WHEN `break` 未带 `condition` THEN 无条件中断（`ResolveCondition` 对空 condition 返回 true，`EventHandlerChainExecutor.cpp:282-284`） | 边界 |
| AC-2.5 | WHEN `break` 位于链中间且前置 handler 抛出异常 THEN 链在异常处即中断，不等到 break（`EventHandlerChainExecutor.cpp:403-417`） | 异常 |

### US-3: 无返回值与 args 约束

**作为** 生成式 UI 宿主开发者,
**我想要** `break` 不产生返回值、不接受业务 args,
**以便** 明确其纯控制语义。

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-3.1 | WHEN `break` 触发 THEN 不产生 `resolvedArgs` 分发、无 `result` 回填（`ResolveArgs`/`DispatchHandlerCall` 未被调用，`EventHandlerChainExecutor.cpp:396-404`） | 正常 |
| AC-3.2 | WHEN schema 校验 THEN `break.json` 的 `args` 为 `additionalProperties:false` 空对象且 `returnType: const "void"` | 正常 |

## 验收追溯

| AC编号 | 关联规则 | 关联 Task | 验证方式 | 证据 |
|----|---------|----------|---------|------|
| AC-1.1,AC-1.2,AC-1.3,AC-1.4,AC-1.5 | R-1 | T-5 | ArkTS 单测 + 静态比对（注册表不含 break） | `CatalogActionFunctions.ets:30-48`、`A2UIBasicFunctions.ets:70`、`NativeFunctionRegistry.cpp:66-86`、`BuiltInActions.cpp:203-208` |
| AC-2.1,AC-2.2,AC-2.3,AC-2.4,AC-2.5 | R-2 | T-5 | C++ UT：ExecuteChain break 中断/条件跳过 | `EventHandlerChainExecutor.cpp:282-422` |
| AC-3.1,AC-3.2 | R-3 | T-5 | 静态比对 + schema 校验 | `EventHandlerChainExecutor.cpp:396-404`、`break.json` |

## 规则定义

| 规则ID | 类型 | 触发条件 | 预期行为 | 边界/约束 | 关联AC |
|--------|------|---------|---------|----------|--------|
| R-1 | 行为 | 函数注册 | 声明 `name='break'`、`isInnerNative=true`、schema `break.json`；不注册 C++ 函数/动作表 | 链执行器硬编码识别 | AC-1.1,AC-1.2,AC-1.3,AC-1.4,AC-1.5 |
| R-2 | 行为 | 链内命中 `call="break"` | 中断链，停止后续 handler | 条件在 break 判定前求值，故可条件中断；异常先于 break 触发 | AC-2.1,AC-2.2,AC-2.3,AC-2.4,AC-2.5 |
| R-3 | 行为 | break 执行 | 不产生返回值、不接受业务 args | schema 空 args + returnType void | AC-3.1,AC-3.2 |

## 验证映射

| 编号 | 对应规格项 | 验证方式 | 验证重点 |
|------|----------|---------|---------|
| VM-1 | AC-1.1,AC-1.2,AC-1.3,AC-1.4,AC-1.5 目录注册 | ArkTS 单测 | name/isInnerNative/schema 路径 + 无 C++ 注册 |
| VM-2 | AC-2.1,AC-2.2,AC-2.3,AC-2.4,AC-2.5 链中断 | C++ UT | break 中断/条件跳过/异常优先 |
| VM-3 | AC-3.1,AC-3.2 无返回值 | 静态比对 | 不产生 result 分发 |

## API 变更分析

> 存量补录，无新增/变更 ArkTS 公共 API。`break` 以 DSL `call` 暴露（inner-native，链控制指令）。

### 新增 API

N/A。

### 变更/废弃 API

| API 名称 | 变更类型 | 影响场景 | 迁移指引 | 关联 AC |
|----------|---------|---------|---------|--------|
| `break`（DSL 控制流函数） | 既有 | EventHandler 链控制 | 经 `A2UIBasicFunctions.extendedCatalogFunctions` 注册，链执行器识别 | AC-1.1,AC-1.2,AC-1.3,AC-1.4,AC-1.5 |

> d.ts 位置：函数 schema `rawfile/schema/Extended/functions/break.json`。Kit：`@arkui-genius/genui`；权限：无。

## 接口规格

### 接口定义

**`break`（链控制指令，`call="break"`，无 C++ handler）**

| 属性 | 值 |
|------|-----|
| 函数签名 | N/A（由 `EventHandlerChainExecutor::ExecuteChain` 内联识别 `step.call == "break"`，`EventHandlerChainExecutor.cpp:396`） |
| 返回值 | `void`（无结果回填） |
| 开放范围 | DSL 控制流函数（inner-native） |
| 错误码 | N/A |
| 关联 AC | AC-1.1,AC-1.2,AC-1.3,AC-1.4,AC-1.5,AC-2.1,AC-2.2,AC-2.3,AC-2.4,AC-2.5,AC-3.1,AC-3.2 |

**参数约束**

| 参数 | 类型 | 必填 | 默认值 | 约束条件 |
|------|------|------|--------|---------|
| args | object | 否（schema `required` 含 `args`，但须为空对象） | `{}` | `additionalProperties:false`、无属性 |
| condition | string | 否 | 无 | 可选 `{{ }}` 表达式，false 时跳过 break |
| returnType | string | 否 | `"void"` | 须为 `void` |

**行为场景**

| # | 触发条件 | 预期行为 | 关联 AC |
|---|----------|----------|---------|
| 1 | 链内命中 break（无条件） | 中断链 | AC-2.1,AC-2.2,AC-2.4 |
| 2 | 链内命中 break 且 condition false | 跳过该 handler | AC-2.3 |
| 3 | 前置 handler 异常 | 链先异常中断 | AC-2.5 |
| 4 | 非法 args（非空） | schema 校验拒绝 | AC-3.2 |

## 兼容性声明

- **已有 API 行为变更:** 否（存量补录）。
- **配置文件格式变更:** 否。
- **数据存储格式变更:** 否。
- **最低支持版本:** A2UI 鸿蒙扩展协议（`ohos.a2ui.extended.catalog`）+ API Version 20。
- **API 版本号策略:** schema 随版本加载（`schema/Extended/functions/break.json`）。

## 架构约束

| 关键约束 | 约束说明 | 影响 AC |
|---------|---------|--------|
| 链内特殊识别 | `break` 由链执行器硬编码识别，不进入任何 dispatcher | AC-1.5,AC-3.1 |
| 条件先于中断 | `ResolveCondition` 在 break 判定前执行 | AC-2.3 |
| 无副作用 | 不产生返回值、不写数据模型 | AC-3.1 |

## 非功能性需求

| 类型 | 指标/阈值 | 验证方式 | 证据 |
|------|----------|---------|------|
| 可靠性 | 链中断逻辑稳定，异常先于 break 触发不退化为死循环 | C++ UT | `EventHandlerChainExecutor.cpp:388-423` |
| 性能 | 单次字符串比较即命中，无额外开销 | C++ UT | `EventHandlerChainExecutor.cpp:396` |

## 多设备适配声明

| 设备类型 | 行为差异 | 规格/约束 | 验证方式 | 证据 |
|---------|---------|----------|---------|------|
| 手机 | 无差异 | 控制流逻辑设备无关 | ohosTest | — |
| 平板 | 无差异 | 同上 | ohosTest | — |
| 折叠屏 | 无差异 | 同上 | ohosTest | — |

## 全局特性影响

| 特性 | 适用？ | 结论 | 关联场景 |
|------|-------|------|---------|
| 无障碍 | 否 | 纯控制流 | — |
| 大字体 | 否 | 不涉及 | — |
| 深色模式 | 否 | 不涉及 | — |
| 多窗口/分屏 | 否 | 无差异 | — |
| 多用户 | 否 | 无差异 | — |
| 版本升级 | 是 | schema 随版本加载 | AC-1.3 |
| 生态兼容 | 是 | 鸿蒙扩展协议控制流函数 | 概述「目标版本」 |

## 行为场景（可选，Gherkin）

```gherkin
Feature: break 链中断函数
  作为 生成式 UI 宿主开发者
  我想要 break 中断当前 EventHandler 链
  以便 条件满足时阻止后续 handler 执行

  Scenario: 无条件中断
    Given onClick 链为 [setDataModel, break, openUrl]
    When 触发 onClick
    Then setDataModel 执行、openUrl 不执行

  Scenario: 条件中断
    Given onClick 链为 [break(condition={{ $x=='' }}), openUrl]
    When $x 非空导致 condition 为 false
    Then break 被跳过，openUrl 执行

  Scenario: 异常先于 break
    Given onClick 链为 [某抛错函数, break]
    When 触发 onClick
    Then 链在异常处中断
```

## Spec 自审清单

- [x] 无"待定""TBD""TODO"等占位符
- [x] 所有 AC 使用 WHEN/THEN 格式，可独立测试
- [x] 范围边界明确（break 链中断语义；EventHandler 结构归 07-04-19/22）
- [x] 无语义模糊表述
- [x] AC 与规则表交叉一致
- [x] 规则表每条通过 5 项质量检查（可复现/可观测/边界值/关联AC/无冲突）

## context-references

```yaml
context-queries:
  - repo: "GenerativeUI/A2UIRender"
    query: "EventHandlerChainExecutor ExecuteChain break step.call ResolveCondition ResolveArgs DispatchHandlerCall"
  - repo: "GenerativeUI/A2UIRender"
    query: "CatalogActionFunctions breakFunction break.json isInnerNative"
  - repo: "GenerativeUI/A2UIRender"
    query: "NativeFunctionRegistry NativeActionRegistry break 未注册"
  - repo: "GenerativeUI/Docs"
    query: "break 链中断 EventHandler 条件中断"
```

**关键文档：** `genui/src/main/ets/core/functions/extended/CatalogActionFunctions.ets`、`genui/src/main/cpp/components/actions/EventHandlerChainExecutor.cpp`、`genui/src/main/resources/rawfile/schema/Extended/functions/break.json`、`reference/functions/extension-functions.md`