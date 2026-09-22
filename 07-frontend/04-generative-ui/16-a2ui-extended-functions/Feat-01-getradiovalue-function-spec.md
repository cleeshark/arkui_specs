# 特性规格

> Func-07-04-16-Feat-01 `getRadioValue` 函数：固化 A2UI 鸿蒙扩展协议组件取值函数 `getRadioValue` 的语义——按 `group` 名称查找当前选中 Radio 的 `value` 文本值（无命中返回空串 `""`）。经 `EventHandler` 链或 `action.event.context` 动态值调用，ArkTS 目录注册（`isInnerNative: true` + schema `getRadioValue.json`），C++ `NativeGetRadioValueFunction::ExecuteWithContext` 遍历 Surface 上的 `ExtendedRadioComponent` / `CustomComponent(Radio)` 获取选中值。基准实现：`@arkui-genius/genui`（A2UIRender）。

## 概述

| 属性 | 值 |
|------|-----|
| 特性名称 | getRadioValue 组件取值函数 |
| 特性编号 | Func-07-04-16-Feat-01 |
| 优先级 | P0 |
| 目标版本 | A2UI 鸿蒙扩展协议（`ohos.a2ui.extended.catalog`）+ API Version 20 |
| SIG 归属 | GenUI SIG |
| 状态 | Baselined |
| 复杂度 | 标准 |

## 本次变更范围（Delta）

| 类型 | 内容 | 说明 |
|------|------|------|
| ADDED | 无（存量补录） | 本特性为 Func-07-04-16 首个 Feat，作为该功能域 design.md 基线 |

## 输入文档

| 文档 | 路径 | 状态 |
|------|------|------|
| Design | `07-frontend/04-generative-ui/16-a2ui-extended-functions/design.md` | Baselined |
| 目录注册（ArkTS） | `genui/src/main/ets/core/functions/component/GetRadioValueFunction.ets` | — |
| 函数聚合（ArkTS） | `genui/src/main/ets/core/functions/A2UIBasicFunctions.ets` | — |
| 原生实现（C++） | `genui/src/main/cpp/functions/NativeGetRadioValueFunction.cpp`、`functions/NativeGetRadioValueFunction.h` | — |
| 注册表（C++） | `genui/src/main/cpp/functions/NativeFunctionRegistry.cpp` | — |
| 链执行（C++） | `genui/src/main/cpp/components/actions/EventHandlerChainExecutor.cpp`、`ActionDispatcher.cpp` | — |
| schema | `genui/src/main/resources/rawfile/schema/Extended/functions/getRadioValue.json` | — |
| 组件（C++） | `genui/src/main/cpp/components/extended/ExtendedRadioComponent.*`、`components/custom/CustomComponent.*` | — |
| 函数参考（Docs） | `reference/functions/component-value.md`、`reference/functions/extension-functions.md` | 理解辅助 |

> 需求基线、不涉及项详见 proposal.md。design.md 与本文档并行产出，互不依赖。

---

## 用户故事

### US-1: 目录注册与 schema 契约

**作为** 生成式 UI 宿主开发者,
**我想要** `getRadioValue` 注册为扩展协议组件取值函数,
**以便** DSL 的 `call="getRadioValue"` 被引擎识别并受 schema 约束。

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-1.1 | WHEN 函数实例化 THEN `GetRadioValueFunction` 构造函数以 `super('getRadioValue')` 声明函数名（`GetRadioValueFunction.ets:22`） | 正常 |
| AC-1.2 | WHEN 目录项构建 THEN `asFunctionItem()` 返回 `name='getRadioValue'` 且 `isInnerNative=true`（`GetRadioValueFunction.ets:27-28`） | 正常 |
| AC-1.3 | WHEN schema 加载 THEN `loadExtendedFunctionSchema('getRadioValue.json')` 命中扩展 schema（`GetRadioValueFunction.ets:35`） | 正常 |
| AC-1.4 | WHEN 聚合扩展内置函数 THEN `getRadioValue` 列入 `extendedCatalogFunctions`（`A2UIBasicFunctions.ets:64`） | 正常 |
| AC-1.5 | WHEN native 注册表初始化 THEN `Register("getRadioValue", NativeGetRadioValueFunction)`（`NativeFunctionRegistry.cpp:82`） | 正常 |

### US-2: 组取值（正常）

**作为** 生成式 UI 宿主开发者,
**我想要** `getRadioValue` 返回指定组当前选中 Radio 的 value,
**以便** 在事件上下文或链中读取单选结果。

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-2.1 | WHEN `args.group` 为非空 string 且 Surface 上存在 `ExtendedRadioComponent` 满足 `GetGroup()==group` 且 `GetChecked()` THEN 返回其 `GetValue()`（`NativeGetRadioValueFunction.cpp:75-83`） | 正常 |
| AC-2.2 | WHEN 选中组件的类型为 `CustomComponent` 且 `GetShortType(GetType())=="Radio"`、`group` 匹配、`checked` 为 true THEN 返回其 `value` 属性（`NativeGetRadioValueFunction.cpp:85-105`） | 正常 |
| AC-2.3 | WHEN 相同 group 存在多个选中项 THEN 返回 `ForEachComponent` 先遍历到的第一个命中项（`resolved` 标志短路后续遍历）（`NativeGetRadioValueFunction.cpp:70-106`） | 边界 |

### US-3: 空值/异常返回

**作为** 生成式 UI 宿主开发者,
**我想要** `getRadioValue` 在缺失入参或无命中时返回空串,
**以便** 调用方稳定拿到 string 类型结果。

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-3.1 | WHEN `args` 非对象或 `group` 非 string THEN `ResolveGroupName` 返回 `""`（`NativeGetRadioValueFunction.cpp:30-40`） | 异常 |
| AC-3.2 | WHEN `group` 为 `""` THEN `ExecuteWithContext` 直接返回空 `FunctionResult()`（`NativeGetRadioValueFunction.cpp:59-62`） | 边界 |
| AC-3.3 | WHEN `FindSurfaceForContext` 返回 nullptr THEN 返回 `FunctionResult(std::string(""))`（`NativeGetRadioValueFunction.cpp:64-67`） | 异常 |
| AC-3.4 | WHEN 遍历后无任何命中项 THEN 返回空串 `""`（`FunctionResult(std::move(selectedValue))`，`NativeGetRadioValueFunction.cpp:108`） | 边界 |
| AC-3.5 | WHEN 直接调用无上下文的 `Execute` THEN 打 `LOG_WARN` 并返回空串（`NativeGetRadioValueFunction.cpp:49-54`） | 异常 |

### US-4: 返回值类型约束

**作为** 生成式 UI 宿主开发者,
**我想要** `getRadioValue` 的返回值被校验为 string,
**以便** DSL 中 `returnType:"string"` 的断言成立。

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-4.1 | WHEN 以 DynamicValue 消费且 `returnType` 为 `"string"` THEN `ValidateReturnType` 通过 `resultValue.IsString()`（`NativeFunctionBase.cpp:33-34`） | 正常 |
| AC-4.2 | WHEN `returnType` 与 string 不符 THEN `NativeFunctionRegistry::Execute` 返回 `FailFunctionCall("builtin returnType mismatch")`（`NativeFunctionRegistry.cpp:135-140`） | 异常 |

## 验收追溯

| AC编号 | 关联规则 | 关联 Task | 验证方式 | 证据 |
|----|---------|----------|---------|------|
| AC-1.1,AC-1.2,AC-1.3,AC-1.4,AC-1.5 | R-1 | T-1 | ArkTS 单测 + 静态比对：目录注册/聚合/native 注册 | `GetRadioValueFunction.ets:22-35`、`A2UIBasicFunctions.ets:64`、`NativeFunctionRegistry.cpp:82` |
| AC-2.1,AC-2.2,AC-2.3 | R-2 | T-1 | C++ UT：`ExecuteWithContext` 组匹配 | `NativeGetRadioValueFunction.cpp:56-109` |
| AC-3.1,AC-3.2,AC-3.3,AC-3.4,AC-3.5 | R-3 | T-1 | C++ UT：空 group/无 Surface/direct Execute | `NativeGetRadioValueFunction.cpp:30-67` |
| AC-4.1,AC-4.2 | R-4 | T-1 | C++ UT：`ValidateReturnType` | `NativeFunctionBase.cpp:33-34` |

## 规则定义

| 规则ID | 类型 | 触发条件 | 预期行为 | 边界/约束 | 关联AC |
|--------|------|---------|---------|----------|--------|
| R-1 | 行为 | 函数注册 | 声明 `name='getRadioValue'`、`isInnerNative=true`、schema `getRadioValue.json`，并 native `Register` | 双注册 ArkTS/C++ 一致 | AC-1.1,AC-1.2,AC-1.3,AC-1.4,AC-1.5 |
| R-2 | 行为 | 组内存在选中 Radio | 返回该 Radio 的 `value` 文本 | 首命中短路；支持 `ExtendedRadioComponent` 与 `CustomComponent(Radio)` 两种形态 | AC-2.1,AC-2.2,AC-2.3 |
| R-3 | 异常 | group 空/无 Surface/无命中/direct Execute | 返回空值（`""` 或空 `FunctionResult`） | 不抛错、不产生错误码 | AC-3.1,AC-3.2,AC-3.3,AC-3.4,AC-3.5 |
| R-4 | 行为 | 返回值校验 | returnType 必须 `string`，mismatch → `FailFunctionCall` | schema `returnType: const "string"` | AC-4.1,AC-4.2 |

## 验证映射

| 编号 | 对应规格项 | 验证方式 | 验证重点 |
|------|----------|---------|---------|
| VM-1 | AC-1.1,AC-1.2,AC-1.3,AC-1.4,AC-1.5 目录注册 | ArkTS 单测 | name/isInnerNative/schema 路径 |
| VM-2 | AC-2.1,AC-2.2,AC-2.3 组取值 | C++ UT | Extended/Custom 两形态 + 首命中短路 |
| VM-3 | AC-3.1,AC-3.2,AC-3.3,AC-3.4,AC-3.5 空值返回 | C++ UT | 空 group/无 Surface/无命中/direct |
| VM-4 | AC-4.1,AC-4.2 returnType | C++ UT | string 校验 + mismatch |

## API 变更分析

> 存量补录，无新增/变更 ArkTS 公共 API。`getRadioValue` 以 DSL `call` 暴露（inner-native）。

### 新增 API

N/A。

### 变更/废弃 API

| API 名称 | 变更类型 | 影响场景 | 迁移指引 | 关联 AC |
|----------|---------|---------|---------|--------|
| `getRadioValue`（DSL 取值函数） | 既有 | EventHandler 链 / `action.event.context` 动态值 | 经 `A2UIBasicFunctions.extendedCatalogFunctions` 注册 | AC-1.1,AC-1.2,AC-1.3,AC-1.4,AC-1.5 |

> d.ts 位置：函数 schema `rawfile/schema/Extended/functions/getRadioValue.json`。Kit：`@arkui-genius/genui`；权限：无。

## 接口规格

### 接口定义

**`NativeGetRadioValueFunction::ExecuteWithContext(resolvedArgs, context)`（原生，`call="getRadioValue"`）**

| 属性 | 值 |
|------|-----|
| 函数签名 | `FunctionResult ExecuteWithContext(const JsonValue& resolvedArgs, const DynamicResolveContext& context)`（`NativeGetRadioValueFunction.h:29`） |
| 返回值 | `FunctionResult(std::string)` — 选中 value / 空串 `""` |
| 开放范围 | DSL 取值函数（inner-native） |
| 错误码 | N/A（仅返回空串，故障仅 `LOG_WARN`） |
| 关联 AC | AC-2.1,AC-2.2,AC-2.3,AC-3.1,AC-3.2,AC-3.3,AC-3.4,AC-3.5 |

**参数约束**

| 参数 | 类型 | 必填 | 默认值 | 约束条件 |
|------|------|------|--------|---------|
| group | string | 是 | — | 非空 string；schema `required:["group"]`、`additionalProperties:false` |
| returnType | string | 否 | `"string"` | 须为 `string` |

**行为场景**

| # | 触发条件 | 预期行为 | 关联 AC |
|---|----------|----------|---------|
| 1 | group 命中选中 Radio | 返回其 value | AC-2.1,AC-2.2 |
| 2 | 同组多选中 | 返回首命中项 | AC-2.3 |
| 3 | group 空/无 Surface/无命中 | 返回空串 | AC-3.1,AC-3.2,AC-3.3,AC-3.4 |
| 4 | direct Execute（无上下文） | WARN + 空串 | AC-3.5 |

## 兼容性声明

- **已有 API 行为变更:** 否（存量补录）。
- **配置文件格式变更:** 否。
- **数据存储格式变更:** 否。
- **最低支持版本:** A2UI 鸿蒙扩展协议（`ohos.a2ui.extended.catalog`）+ API Version 20。
- **API 版本号策略:** schema 随版本加载（`schema/Extended/functions/getRadioValue.json`）。

## 架构约束

| 关键约束 | 约束说明 | 影响 AC |
|---------|---------|--------|
| 双注册一致 | ArkTS 目录注册与 C++ registry 函数名/schema 对齐 | AC-1.1,AC-1.2,AC-1.3,AC-1.4,AC-1.5 |
| 上下文必需 | 取值必须经 `ExecuteWithContext`，direct `Execute` 为降级桩 | AC-3.5 |
| 空值语义 | 无命中返回 `""`，不抛错、无错误码 | AC-3.1,AC-3.2,AC-3.3,AC-3.4 |

## 非功能性需求

| 类型 | 指标/阈值 | 验证方式 | 证据 |
|------|----------|---------|------|
| 可靠性 | 非法入参不抛异常，统一返回空串 | C++ UT | `NativeGetRadioValueFunction.cpp:30-67` |
| 性能 | 单次 Surface 全量组件遍历，命中即短路 | C++ UT | `NativeGetRadioValueFunction.cpp:71-106` |

## 多设备适配声明

| 设备类型 | 行为差异 | 规格/约束 | 验证方式 | 证据 |
|---------|---------|----------|---------|------|
| 手机 | 无差异 | 取值逻辑设备无关 | ohosTest | — |
| 平板 | 无差异 | 同上 | ohosTest | — |
| 折叠屏 | 无差异 | 同上 | ohosTest | — |

## 全局特性影响

| 特性 | 适用？ | 结论 | 关联场景 |
|------|-------|------|---------|
| 无障碍 | 否 | 纯取值逻辑，无障碍由组件呈现 | — |
| 大字体 | 否 | 不涉及 | — |
| 深色模式 | 否 | 不涉及 | — |
| 多窗口/分屏 | 是 | 取值按 surfaceId 隔离，不同 Surface 互不影响 | AC-3.3 |
| 多用户 | 否 | 无差异 | — |
| 版本升级 | 是 | schema 随版本加载 | AC-1.3 |
| 生态兼容 | 是 | 鸿蒙扩展协议取值函数 | 概述「目标版本」 |

## 行为场景（可选，Gherkin）

```gherkin
Feature: getRadioValue 取值函数
  作为 生成式 UI 宿主开发者
  我想要 getRadioValue 返回组内选中 Radio 的 value
  以便 在事件上下文或链中读取单选结果

  Scenario: 命中选中项
    Given Surface 上存在 group="plan_type" 且 checked=true 的 Radio(value="pro")
    When 以 {"call":"getRadioValue","args":{"group":"plan_type"}} 调用
    Then 返回 "pro"

  Scenario Outline: 空值返回
    Given 调用 getRadioValue
    When group 为 <group> 或 Surface 无选中项
    Then 返回 ""
    Examples:
      | group |
      | ""    |
      | "nonexistent" |
```

## Spec 自审清单

- [x] 无"待定""TBD""TODO"等占位符
- [x] 所有 AC 使用 WHEN/THEN 格式，可独立测试
- [x] 范围边界明确（getRadioValue 取值语义；Radio 组件态归 07-04-12）
- [x] 无语义模糊表述
- [x] AC 与规则表交叉一致
- [x] 规则表每条通过 5 项质量检查（可复现/可观测/边界值/关联AC/无冲突）

## context-references

```yaml
context-queries:
  - repo: "GenerativeUI/A2UIRender"
    query: "NativeGetRadioValueFunction ExecuteWithContext ResolveGroupName ForEachComponent ExtendedRadioComponent CustomComponent Radio group checked value"
  - repo: "GenerativeUI/A2UIRender"
    query: "GetRadioValueFunction.ets isInnerNative loadExtendedFunctionSchema getRadioValue.json"
  - repo: "GenerativeUI/A2UIRender"
    query: "NativeFunctionRegistry Register getRadioValue NativeFunctionComponentUtils FindSurfaceForContext"
  - repo: "GenerativeUI/Docs"
    query: "getRadioValue 组件取值函数 group 选中 Radio value"
```

**关键文档：** `genui/src/main/ets/core/functions/component/GetRadioValueFunction.ets`、`genui/src/main/cpp/functions/NativeGetRadioValueFunction.cpp`、`genui/src/main/cpp/functions/NativeFunctionRegistry.cpp`、`reference/functions/component-value.md`