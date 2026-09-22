# 特性规格

> Func-07-04-16-Feat-02 `getCheckboxGroupValues` 函数：固化 A2UI 鸿蒙扩展协议组件取值函数 `getCheckboxGroupValues` 的语义——按 `group` 名称收集所有选中 Checkbox 的 `value` 文本数组（无选中返回空数组 `[]`）。ArkTS 目录注册（`isInnerNative: true` + schema `getCheckboxGroupValues.json`），C++ `NativeGetCheckboxGroupValuesFunction::ExecuteWithContext` 先读 `ExtendedCheckbox.select` 运行态、再遍历组件态，合并去重后返回选中 value 数组。基准实现：`@arkui-genius/genui`（A2UIRender）。

## 概述

| 属性 | 值 |
|------|-----|
| 特性名称 | getCheckboxGroupValues 组件取值函数 |
| 特性编号 | Func-07-04-16-Feat-02 |
| 优先级 | P0 |
| 目标版本 | A2UI 鸿蒙扩展协议（`ohos.a2ui.extended.catalog`）+ API Version 20 |
| SIG 归属 | GenUI SIG |
| 状态 | Baselined |
| 复杂度 | 标准 |

## 本次变更范围（Delta）

| 类型 | 内容 | 说明 |
|------|------|------|
| ADDED | 无（存量补录） | 本特性为 Func-07-04-16 第二个 Feat |

## 输入文档

| 文档 | 路径 | 状态 |
|------|------|------|
| Design | `07-frontend/04-generative-ui/16-a2ui-extended-functions/design.md` | Baselined |
| 目录注册（ArkTS） | `genui/src/main/ets/core/functions/component/GetCheckboxGroupValuesFunction.ets` | — |
| 函数聚合（ArkTS） | `genui/src/main/ets/core/functions/A2UIBasicFunctions.ets` | — |
| 原生实现（C++） | `genui/src/main/cpp/functions/NativeGetCheckboxGroupValuesFunction.cpp`、`functions/NativeGetCheckboxGroupValuesFunction.h` | — |
| 注册表（C++） | `genui/src/main/cpp/functions/NativeFunctionRegistry.cpp` | — |
| schema | `genui/src/main/resources/rawfile/schema/Extended/functions/getCheckboxGroupValues.json` | — |
| 组件（C++） | `genui/src/main/cpp/components/extended/ExtendedCheckboxComponent.*`、`components/custom/CustomComponent.*` | — |
| 函数参考（Docs） | `reference/functions/component-value.md`、`reference/functions/extension-functions.md` | 理解辅助 |

> 需求基线、不涉及项详见 proposal.md。design.md 与本文档并行产出，互不依赖。

---

## 用户故事

### US-1: 目录注册与 schema 契约

**作为** 生成式 UI 宿主开发者,
**我想要** `getCheckboxGroupValues` 注册为扩展协议组件取值函数,
**以便** DSL 的 `call="getCheckboxGroupValues"` 被引擎识别并受 schema 约束。

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-1.1 | WHEN 函数实例化 THEN `GetCheckboxGroupValuesFunction` 构造函数以 `super('getCheckboxGroupValues')` 声明函数名（`GetCheckboxGroupValuesFunction.ets:22`） | 正常 |
| AC-1.2 | WHEN 目录项构建 THEN `asFunctionItem()` 返回 `name='getCheckboxGroupValues'` 且 `isInnerNative=true`（`GetCheckboxGroupValuesFunction.ets:27-28`） | 正常 |
| AC-1.3 | WHEN schema 加载 THEN `loadExtendedFunctionSchema('getCheckboxGroupValues.json')`（`GetCheckboxGroupValuesFunction.ets:35`） | 正常 |
| AC-1.4 | WHEN 聚合扩展内置函数 THEN `getCheckboxGroupValues` 列入 `extendedCatalogFunctions`（`A2UIBasicFunctions.ets:65`） | 正常 |
| AC-1.5 | WHEN native 注册表初始化 THEN `Register("getCheckboxGroupValues", ...)`（`NativeFunctionRegistry.cpp:84`） | 正常 |

### US-2: 组多选取值（正常）

**作为** 生成式 UI 宿主开发者,
**我想要** `getCheckboxGroupValues` 返回组内所有选中 Checkbox 的 value 数组,
**以便** 在事件上下文或链中读取多选结果。

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-2.1 | WHEN `args.group` 为非空 string 且存在 `ExtendedCheckboxComponent` 满足 `GetGroup()==group` 且未被运行态覆盖 THEN 以 `GetSelect()` 计入其 `GetValue()`（`NativeGetCheckboxGroupValuesFunction.cpp:120-127`） | 正常 |
| AC-2.2 | WHEN 命中 `CustomComponent` 且 `GetShortType(GetType())=="Checkbox"`、`group` 匹配、`select` 为 bool THEN 计入其 `value`（`NativeGetCheckboxGroupValuesFunction.cpp:131-151`） | 正常 |
| AC-2.3 | WHEN 存在 `ExtendedCheckbox.select` 运行态且 group 匹配 THEN 优先以运行态 `select` 值计入（`ReadRuntimeSelections`，`NativeGetCheckboxGroupValuesFunction.cpp:89-108`） | 正常 |
| AC-2.4 | WHEN 运行态与组件态同 value 冲突 THEN 取 `selectedByValue` 的 `||` 合并（`MergeSelectionByValue`，`NativeGetCheckboxGroupValuesFunction.cpp:76-87`） | 边界 |
| AC-2.5 | WHEN 结果组装 THEN 仅返回 `selectedByValue==true` 的 value 数组（`NativeGetCheckboxGroupValuesFunction.cpp:190-200`） | 正常 |

### US-3: 空值/异常返回

**作为** 生成式 UI 宿主开发者,
**我想要** `getCheckboxGroupValues` 在缺失入参或无命中时返回空数组,
**以便** 调用方稳定拿到数组类型结果。

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-3.1 | WHEN `args` 非对象或 `group` 非 string THEN `ResolveGroup` 返回 `""`（`NativeGetCheckboxGroupValuesFunction.cpp:42-52`） | 异常 |
| AC-3.2 | WHEN `group` 为 `""` THEN `LOG_WARN` 并返回空 `FunctionResult()`（`NativeGetCheckboxGroupValuesFunction.cpp:171-175`） | 边界 |
| AC-3.3 | WHEN `FindSurfaceForContext` 返回 nullptr THEN 返回 `BuildEmptyArrayResult`（空数组）（`NativeGetCheckboxGroupValuesFunction.cpp:177-182`） | 异常 |
| AC-3.4 | WHEN 无任何选中项 THEN 返回空数组 `[]`（`BuildArrayResult(空 selectedLabels)`，`NativeGetCheckboxGroupValuesFunction.cpp:190-200`） | 边界 |
| AC-3.5 | WHEN 直接调用无上下文的 `Execute` THEN `LOG_WARN` 并返回空数组（`NativeGetCheckboxGroupValuesFunction.cpp:161-166`） | 异常 |

### US-4: 返回值类型约束

**作为** 生成式 UI 宿主开发者,
**我想要** `getCheckboxGroupValues` 的返回值被校验为数组,
**以便** DSL 中 `returnType:"string[]"`（或 `"array"`）的断言成立。

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-4.1 | WHEN 以 DynamicValue 消费且 `returnType` 为 `"string[]"` 或 `"array"` THEN `ValidateReturnType` 通过 `resultValue.IsArray()`（`NativeFunctionBase.cpp:41-42`） | 正常 |
| AC-4.2 | WHEN `returnType` 与数组不符 THEN 返回 `FailFunctionCall("builtin returnType mismatch")`（`NativeFunctionRegistry.cpp:135-140`） | 异常 |

## 验收追溯

| AC编号 | 关联规则 | 关联 Task | 验证方式 | 证据 |
|----|---------|----------|---------|------|
| AC-1.1,AC-1.2,AC-1.3,AC-1.4,AC-1.5 | R-1 | T-2 | ArkTS 单测 + 静态比对 | `GetCheckboxGroupValuesFunction.ets:22-35`、`A2UIBasicFunctions.ets:65`、`NativeFunctionRegistry.cpp:84` |
| AC-2.1,AC-2.2,AC-2.3,AC-2.4,AC-2.5 | R-2 | T-2 | C++ UT：运行态/组件态合并去重 | `NativeGetCheckboxGroupValuesFunction.cpp:89-200` |
| AC-3.1,AC-3.2,AC-3.3,AC-3.4,AC-3.5 | R-3 | T-2 | C++ UT：空 group/无 Surface/direct | `NativeGetCheckboxGroupValuesFunction.cpp:42-182` |
| AC-4.1,AC-4.2 | R-4 | T-2 | C++ UT：`ValidateReturnType` | `NativeFunctionBase.cpp:41-42` |

## 规则定义

| 规则ID | 类型 | 触发条件 | 预期行为 | 边界/约束 | 关联AC |
|--------|------|---------|---------|----------|--------|
| R-1 | 行为 | 函数注册 | 声明 `name='getCheckboxGroupValues'`、`isInnerNative=true`、schema `getCheckboxGroupValues.json`，native `Register` | 双注册一致 | AC-1.1,AC-1.2,AC-1.3,AC-1.4,AC-1.5 |
| R-2 | 行为 | 组内存在选中 Checkbox | 收集所有选中项 value 组成数组 | 运行态优先、组件态补集、`||` 合并去重 | AC-2.1,AC-2.2,AC-2.3,AC-2.4,AC-2.5 |
| R-3 | 异常 | group 空/无 Surface/无选中/direct | 返回空数组 `[]`（或空 `FunctionResult`） | 不抛错、无错误码 | AC-3.1,AC-3.2,AC-3.3,AC-3.4,AC-3.5 |
| R-4 | 行为 | 返回值校验 | returnType 必须 `string[]`/`array`，mismatch → `FailFunctionCall` | schema `returnType: const "string[]"` | AC-4.1,AC-4.2 |

## 验证映射

| 编号 | 对应规格项 | 验证方式 | 验证重点 |
|------|----------|---------|---------|
| VM-1 | AC-1.1,AC-1.2,AC-1.3,AC-1.4,AC-1.5 目录注册 | ArkTS 单测 | name/isInnerNative/schema 路径 |
| VM-2 | AC-2.1,AC-2.2,AC-2.3,AC-2.4,AC-2.5 多选取值 | C++ UT | 运行态+组件态合并、去重、value 数组 |
| VM-3 | AC-3.1,AC-3.2,AC-3.3,AC-3.4,AC-3.5 空值返回 | C++ UT | 空 group/无 Surface/无选中/direct |
| VM-4 | AC-4.1,AC-4.2 returnType | C++ UT | 数组校验 + mismatch |

## API 变更分析

> 存量补录，无新增/变更 ArkTS 公共 API。`getCheckboxGroupValues` 以 DSL `call` 暴露（inner-native）。

### 新增 API

N/A。

### 变更/废弃 API

| API 名称 | 变更类型 | 影响场景 | 迁移指引 | 关联 AC |
|----------|---------|---------|---------|--------|
| `getCheckboxGroupValues`（DSL 取值函数） | 既有 | EventHandler 链 / `action.event.context` 动态值 | 经 `A2UIBasicFunctions.extendedCatalogFunctions` 注册 | AC-1.1,AC-1.2,AC-1.3,AC-1.4,AC-1.5 |

> d.ts 位置：函数 schema `rawfile/schema/Extended/functions/getCheckboxGroupValues.json`。Kit：`@arkui-genius/genui`；权限：无。

## 接口规格

### 接口定义

**`NativeGetCheckboxGroupValuesFunction::ExecuteWithContext(resolvedArgs, context)`（原生，`call="getCheckboxGroupValues"`）**

| 属性 | 值 |
|------|-----|
| 函数签名 | `FunctionResult ExecuteWithContext(const JsonValue& resolvedArgs, const DynamicResolveContext& context)`（`NativeGetCheckboxGroupValuesFunction.h:27`） |
| 返回值 | `FunctionResult(array)` — 选中 value 文本数组 / 空数组 `[]` |
| 开放范围 | DSL 取值函数（inner-native） |
| 错误码 | N/A（仅返回数组，故障仅 `LOG_WARN`） |
| 关联 AC | AC-2.1,AC-2.2,AC-2.3,AC-2.4,AC-2.5,AC-3.1,AC-3.2,AC-3.3,AC-3.4,AC-3.5 |

**参数约束**

| 参数 | 类型 | 必填 | 默认值 | 约束条件 |
|------|------|------|--------|---------|
| group | string | 是 | — | 非空 string；schema `required:["group"]`、`additionalProperties:false` |
| returnType | string | 否 | `"string[]"` | 须为 `string[]`/`array` |

**行为场景**

| # | 触发条件 | 预期行为 | 关联 AC |
|---|----------|----------|---------|
| 1 | group 命中多个选中 Checkbox | 返回其 value 数组 | AC-2.1,AC-2.2,AC-2.3 |
| 2 | 运行态与组件态同 value | 取 `||` 合并 | AC-2.4 |
| 3 | group 空/无 Surface/无选中 | 返回空数组 | AC-3.1,AC-3.2,AC-3.3,AC-3.4 |
| 4 | direct Execute（无上下文） | WARN + 空数组 | AC-3.5 |

## 兼容性声明

- **已有 API 行为变更:** 否（存量补录）。
- **配置文件格式变更:** 否。
- **数据存储格式变更:** 否。
- **最低支持版本:** A2UI 鸿蒙扩展协议（`ohos.a2ui.extended.catalog`）+ API Version 20。
- **API 版本号策略:** schema 随版本加载（`schema/Extended/functions/getCheckboxGroupValues.json`）。

## 架构约束

| 关键约束 | 约束说明 | 影响 AC |
|---------|---------|--------|
| 双注册一致 | ArkTS 目录注册与 C++ registry 对齐 | AC-1.1,AC-1.2,AC-1.3,AC-1.4,AC-1.5 |
| 上下文必需 | 取值必须经 `ExecuteWithContext`，direct `Execute` 为降级桩 | AC-3.5 |
| 运行态优先 | `ExtendedCheckbox.select` 运行态优先于组件态，避免重复计数 | AC-2.3,AC-2.4 |

## 非功能性需求

| 类型 | 指标/阈值 | 验证方式 | 证据 |
|------|----------|---------|------|
| 可靠性 | 非法入参不抛异常，统一返回空数组 | C++ UT | `NativeGetCheckboxGroupValuesFunction.cpp:42-182` |
| 性能 | 运行态 map + 组件遍历两阶段，去重合并线性 | C++ UT | `NativeGetCheckboxGroupValuesFunction.cpp:89-200` |

## 多设备适配声明

| 设备类型 | 行为差异 | 规格/约束 | 验证方式 | 证据 |
|---------|---------|----------|---------|------|
| 手机 | 无差异 | 取值逻辑设备无关 | ohosTest | — |
| 平板 | 无差异 | 同上 | ohosTest | — |
| 折叠屏 | 无差异 | 同上 | ohosTest | — |

## 全局特性影响

| 特性 | 适用？ | 结论 | 关联场景 |
|------|-------|------|---------|
| 无障碍 | 否 | 纯取值逻辑 | — |
| 大字体 | 否 | 不涉及 | — |
| 深色模式 | 否 | 不涉及 | — |
| 多窗口/分屏 | 是 | 按 surfaceId 隔离运行态 | AC-3.3 |
| 多用户 | 否 | 无差异 | — |
| 版本升级 | 是 | schema 随版本加载 | AC-1.3 |
| 生态兼容 | 是 | 鸿蒙扩展协议取值函数 | 概述「目标版本」 |

## 行为场景（可选，Gherkin）

```gherkin
Feature: getCheckboxGroupValues 取值函数
  作为 生成式 UI 宿主开发者
  我想要 getCheckboxGroupValues 返回组内所有选中 Checkbox 的 value
  以便 在事件上下文或链中读取多选结果

  Scenario: 多选命中
    Given Surface 上 group="hobbies" 存在两个 select=true 的 Checkbox(value="a"/"b")
    When 以 {"call":"getCheckboxGroupValues","args":{"group":"hobbies"}} 调用
    Then 返回 ["a","b"]

  Scenario Outline: 空值返回
    Given 调用 getCheckboxGroupValues
    When group 为 <group> 或 Surface 无选中项
    Then 返回 []
    Examples:
      | group |
      | ""    |
      | "nonexistent" |
```

## Spec 自审清单

- [x] 无"待定""TBD""TODO"等占位符
- [x] 所有 AC 使用 WHEN/THEN 格式，可独立测试
- [x] 范围边界明确（getCheckboxGroupValues 取值语义；Checkbox 组件态归 07-04-12）
- [x] 无语义模糊表述
- [x] AC 与规则表交叉一致
- [x] 规则表每条通过 5 项质量检查（可复现/可观测/边界值/关联AC/无冲突）

## context-references

```yaml
context-queries:
  - repo: "GenerativeUI/A2UIRender"
    query: "NativeGetCheckboxGroupValuesFunction ExecuteWithContext ReadRuntimeSelections CollectCheckboxSelection MergeSelectionByValue BuildArrayResult"
  - repo: "GenerativeUI/A2UIRender"
    query: "ExtendedCheckboxComponent GetRuntimeStateKey ExtendedCheckbox.select runtime state scope"
  - repo: "GenerativeUI/A2UIRender"
    query: "GetCheckboxGroupValuesFunction.ets loadExtendedFunctionSchema getCheckboxGroupValues.json"
  - repo: "GenerativeUI/Docs"
    query: "getCheckboxGroupValues 组件取值函数 group 选中 Checkbox value 数组"
```

**关键文档：** `genui/src/main/ets/core/functions/component/GetCheckboxGroupValuesFunction.ets`、`genui/src/main/cpp/functions/NativeGetCheckboxGroupValuesFunction.cpp`、`genui/src/main/cpp/components/extended/ExtendedCheckboxComponent.cpp`、`reference/functions/component-value.md`