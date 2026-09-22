# 特性规格

> Func-07-04-16-Feat-03 `getToggleValue` 函数：固化 A2UI 鸿蒙扩展协议组件取值函数 `getToggleValue` 的语义——按 `componentId` 查找 Toggle 组件并返回 `{ isOn, label }` 对象（组件不存在或非 Toggle 返回空对象 `{}`）。ArkTS 目录注册（`isInnerNative: true` + schema `getToggleValue.json`），C++ `NativeGetToggleValueFunction::ExecuteWithContext` 经 `FindComponentById` + `dynamic_pointer_cast<ExtendedToggleComponent>` 封装开关态与标签。基准实现：`@arkui-genius/genui`（A2UIRender）。

## 概述

| 属性 | 值 |
|------|-----|
| 特性名称 | getToggleValue 组件取值函数 |
| 特性编号 | Func-07-04-16-Feat-03 |
| 优先级 | P0 |
| 目标版本 | A2UI 鸿蒙扩展协议（`ohos.a2ui.extended.catalog`）+ API Version 20 |
| SIG 归属 | GenUI SIG |
| 状态 | Baselined |
| 复杂度 | 标准 |

## 本次变更范围（Delta）

| 类型 | 内容 | 说明 |
|------|------|------|
| ADDED | 无（存量补录） | 本特性为 Func-07-04-16 第三个 Feat |

## 输入文档

| 文档 | 路径 | 状态 |
|------|------|------|
| Design | `07-frontend/04-generative-ui/16-a2ui-extended-functions/design.md` | Baselined |
| 目录注册（ArkTS） | `genui/src/main/ets/core/functions/component/GetToggleValueFunction.ets` | — |
| 函数聚合（ArkTS） | `genui/src/main/ets/core/functions/A2UIBasicFunctions.ets` | — |
| 原生实现（C++） | `genui/src/main/cpp/functions/NativeGetToggleValueFunction.cpp`、`functions/NativeGetToggleValueFunction.h` | — |
| 注册表（C++） | `genui/src/main/cpp/functions/NativeFunctionRegistry.cpp` | — |
| schema | `genui/src/main/resources/rawfile/schema/Extended/functions/getToggleValue.json` | — |
| 组件（C++） | `genui/src/main/cpp/components/extended/ExtendedToggleComponent.*` | — |
| 函数参考（Docs） | `reference/functions/component-value.md`、`reference/functions/extension-functions.md` | 理解辅助 |

> 需求基线、不涉及项详见 proposal.md。design.md 与本文档并行产出，互不依赖。

---

## 用户故事

### US-1: 目录注册与 schema 契约

**作为** 生成式 UI 宿主开发者,
**我想要** `getToggleValue` 注册为扩展协议组件取值函数,
**以便** DSL 的 `call="getToggleValue"` 被引擎识别并受 schema 约束。

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-1.1 | WHEN 函数实例化 THEN `GetToggleValueFunction` 构造函数以 `super('getToggleValue')` 声明函数名（`GetToggleValueFunction.ets:22`） | 正常 |
| AC-1.2 | WHEN 目录项构建 THEN `asFunctionItem()` 返回 `name='getToggleValue'` 且 `isInnerNative=true`（`GetToggleValueFunction.ets:27-28`） | 正常 |
| AC-1.3 | WHEN schema 加载 THEN `loadExtendedFunctionSchema('getToggleValue.json')`（`GetToggleValueFunction.ets:35`） | 正常 |
| AC-1.4 | WHEN 聚合扩展内置函数 THEN `getToggleValue` 列入 `extendedCatalogFunctions`（`A2UIBasicFunctions.ets:66`） | 正常 |
| AC-1.5 | WHEN native 注册表初始化 THEN `Register("getToggleValue", ...)`（`NativeFunctionRegistry.cpp:81`） | 正常 |

### US-2: 组件态封装（正常）

**作为** 生成式 UI 宿主开发者,
**我想要** `getToggleValue` 返回指定 Toggle 的开关态与标签,
**以便** 在事件上下文或链中读取开关状态。

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-2.1 | WHEN `componentId` 命中 `ExtendedToggleComponent` THEN 返回对象包含 `isOn = GetIsOn()`（`NativeGetToggleValueFunction.cpp:85-89`） | 正常 |
| AC-2.2 | WHEN `componentId` 命中 `ExtendedToggleComponent` THEN 返回对象包含 `label = GetLabel()`（`NativeGetToggleValueFunction.cpp:85-89`） | 正常 |
| AC-2.3 | WHEN `JsonAdapter::CreateObject` 或 `PutBool`/`PutString` 任一失败 THEN 返回空 `FunctionResult()`（`NativeGetToggleValueFunction.cpp:80-88`） | 异常 |

### US-3: 空值/异常返回

**作为** 生成式 UI 宿主开发者,
**我想要** `getToggleValue` 在缺失入参或非 Toggle 时返回空对象,
**以便** 调用方稳定拿到 object 类型结果。

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-3.1 | WHEN `args` 非对象或 `componentId` 非 string THEN `ResolveComponentId` 返回 `""`（`NativeGetToggleValueFunction.cpp:29-39`） | 异常 |
| AC-3.2 | WHEN `componentId` 为 `""` THEN 返回 `CreateEmptyObjectResult`（`{}`）（`NativeGetToggleValueFunction.cpp:64-67`） | 边界 |
| AC-3.3 | WHEN `FindSurfaceForContext` 返回 nullptr THEN 返回 `{}`（`NativeGetToggleValueFunction.cpp:69-72`） | 异常 |
| AC-3.4 | WHEN `FindComponentById` 结果非 `ExtendedToggleComponent`（null 或类型不符） THEN 返回 `{}`（`NativeGetToggleValueFunction.cpp:74-78`） | 异常 |
| AC-3.5 | WHEN 直接调用无上下文的 `Execute` THEN `LOG_WARN` 并返回 `{}`（`NativeGetToggleValueFunction.cpp:54-59`） | 异常 |

### US-4: 返回值类型约束

**作为** 生成式 UI 宿主开发者,
**我想要** `getToggleValue` 的返回值被校验为 object,
**以便** DSL 中 `returnType:"object"` 的断言成立。

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-4.1 | WHEN 以 DynamicValue 消费且 `returnType` 为 `"object"` THEN `ValidateReturnType` 通过 `resultValue.IsObject()`（`NativeFunctionBase.cpp:43-44`） | 正常 |
| AC-4.2 | WHEN `returnType` 与 object 不符 THEN 返回 `FailFunctionCall("builtin returnType mismatch")`（`NativeFunctionRegistry.cpp:135-140`） | 异常 |

## 验收追溯

| AC编号 | 关联规则 | 关联 Task | 验证方式 | 证据 |
|----|---------|----------|---------|------|
| AC-1.1,AC-1.2,AC-1.3,AC-1.4,AC-1.5 | R-1 | T-3 | ArkTS 单测 + 静态比对 | `GetToggleValueFunction.ets:22-35`、`A2UIBasicFunctions.ets:66`、`NativeFunctionRegistry.cpp:81` |
| AC-2.1,AC-2.2,AC-2.3 | R-2 | T-3 | C++ UT：对象封装 | `NativeGetToggleValueFunction.cpp:80-89` |
| AC-3.1,AC-3.2,AC-3.3,AC-3.4,AC-3.5 | R-3 | T-3 | C++ UT：空 componentId/无 Surface/非 Toggle/direct | `NativeGetToggleValueFunction.cpp:29-78` |
| AC-4.1,AC-4.2 | R-4 | T-3 | C++ UT：`ValidateReturnType` | `NativeFunctionBase.cpp:43-44` |

## 规则定义

| 规则ID | 类型 | 触发条件 | 预期行为 | 边界/约束 | 关联AC |
|--------|------|---------|---------|----------|--------|
| R-1 | 行为 | 函数注册 | 声明 `name='getToggleValue'`、`isInnerNative=true`、schema `getToggleValue.json`，native `Register` | 双注册一致 | AC-1.1,AC-1.2,AC-1.3,AC-1.4,AC-1.5 |
| R-2 | 行为 | componentId 命中 Toggle | 返回 `{ isOn, label }` 对象 | `PutBool`/`PutString` 失败则返空 | AC-2.1,AC-2.2,AC-2.3 |
| R-3 | 异常 | componentId 空/无 Surface/非 Toggle/direct | 返回空对象 `{}` | 不抛错、无错误码 | AC-3.1,AC-3.2,AC-3.3,AC-3.4,AC-3.5 |
| R-4 | 行为 | 返回值校验 | returnType 必须 `object`，mismatch → `FailFunctionCall` | schema `returnType: const "object"` | AC-4.1,AC-4.2 |

## 验证映射

| 编号 | 对应规格项 | 验证方式 | 验证重点 |
|------|----------|---------|---------|
| VM-1 | AC-1.1,AC-1.2,AC-1.3,AC-1.4,AC-1.5 目录注册 | ArkTS 单测 | name/isInnerNative/schema 路径 |
| VM-2 | AC-2.1,AC-2.2,AC-2.3 对象封装 | C++ UT | isOn/label 字段 |
| VM-3 | AC-3.1,AC-3.2,AC-3.3,AC-3.4,AC-3.5 空值返回 | C++ UT | 空 componentId/非 Toggle/direct |
| VM-4 | AC-4.1,AC-4.2 returnType | C++ UT | object 校验 + mismatch |

## API 变更分析

> 存量补录，无新增/变更 ArkTS 公共 API。`getToggleValue` 以 DSL `call` 暴露（inner-native）。

### 新增 API

N/A。

### 变更/废弃 API

| API 名称 | 变更类型 | 影响场景 | 迁移指引 | 关联 AC |
|----------|---------|---------|---------|--------|
| `getToggleValue`（DSL 取值函数） | 既有 | EventHandler 链 / `action.event.context` 动态值 | 经 `A2UIBasicFunctions.extendedCatalogFunctions` 注册 | AC-1.1,AC-1.2,AC-1.3,AC-1.4,AC-1.5 |

> d.ts 位置：函数 schema `rawfile/schema/Extended/functions/getToggleValue.json`。Kit：`@arkui-genius/genui`；权限：无。

## 接口规格

### 接口定义

**`NativeGetToggleValueFunction::ExecuteWithContext(resolvedArgs, context)`（原生，`call="getToggleValue"`）**

| 属性 | 值 |
|------|-----|
| 函数签名 | `FunctionResult ExecuteWithContext(const JsonValue& resolvedArgs, const DynamicResolveContext& context)`（`NativeGetToggleValueFunction.h:29`） |
| 返回值 | `FunctionResult(object)` — `{ isOn: bool, label: string }` / 空对象 `{}` |
| 开放范围 | DSL 取值函数（inner-native） |
| 错误码 | N/A（仅返回对象，故障仅 `LOG_WARN`） |
| 关联 AC | AC-2.1,AC-2.2,AC-2.3,AC-3.1,AC-3.2,AC-3.3,AC-3.4,AC-3.5 |

**参数约束**

| 参数 | 类型 | 必填 | 默认值 | 约束条件 |
|------|------|------|--------|---------|
| componentId | string | 是 | — | 非空 string；schema `required:["componentId"]`、`additionalProperties:false` |
| returnType | string | 否 | `"object"` | 须为 `object` |

**行为场景**

| # | 触发条件 | 预期行为 | 关联 AC |
|---|----------|----------|---------|
| 1 | componentId 命中 Toggle | 返回 `{isOn, label}` | AC-2.1,AC-2.2 |
| 2 | CreateObject/PutBool/PutString 失败 | 返回空 | AC-2.3 |
| 3 | componentId 空/无 Surface/非 Toggle | 返回 `{}` | AC-3.1,AC-3.2,AC-3.3,AC-3.4 |
| 4 | direct Execute（无上下文） | WARN + `{}` | AC-3.5 |

## 兼容性声明

- **已有 API 行为变更:** 否（存量补录）。
- **配置文件格式变更:** 否。
- **数据存储格式变更:** 否。
- **最低支持版本:** A2UI 鸿蒙扩展协议（`ohos.a2ui.extended.catalog`）+ API Version 20。
- **API 版本号策略:** schema 随版本加载（`schema/Extended/functions/getToggleValue.json`）。

## 架构约束

| 关键约束 | 约束说明 | 影响 AC |
|---------|---------|--------|
| 双注册一致 | ArkTS 目录注册与 C++ registry 对齐 | AC-1.1,AC-1.2,AC-1.3,AC-1.4,AC-1.5 |
| 上下文必需 | 取值必须经 `ExecuteWithContext`，direct `Execute` 为降级桩 | AC-3.5 |
| 对象结构 | 返回值固定为 `{isOn,label}`（schema `x-protocolReturnType` 约束） | AC-2.1,AC-2.2 |

## 非功能性需求

| 类型 | 指标/阈值 | 验证方式 | 证据 |
|------|----------|---------|------|
| 可靠性 | 非法入参不抛异常，统一返回空对象 | C++ UT | `NativeGetToggleValueFunction.cpp:29-78` |
| 性能 | 单次 `FindComponentById` 查找 + 对象封装 | C++ UT | `NativeGetToggleValueFunction.cpp:74-89` |

## 多设备适配声明

| 设备类型 | 行为差异 | 规格/约束 | 验证方式 | 证据 |
|---------|---------|----------|---------|------|
| 手机 | 无差异 | 取值逻辑设备无关 | ohosTest | — |
| 平板 | 无差异 | 同上 | ohosTest | — |
| 折叠屏 | 无差异 | 同上 | ohosTest | — |

## 全局特性影响

| 特性 | 适用？ | 结论 | 关联场景 |
|------|-------|------|---------|
| 无障碍 | 是 | `label` 文本可被无障碍读取 | AC-2.2 |
| 大字体 | 否 | 不涉及 | — |
| 深色模式 | 否 | 不涉及 | — |
| 多窗口/分屏 | 是 | 按 surfaceId 隔离 | AC-3.3 |
| 多用户 | 否 | 无差异 | — |
| 版本升级 | 是 | schema 随版本加载 | AC-1.3 |
| 生态兼容 | 是 | 鸿蒙扩展协议取值函数 | 概述「目标版本」 |

## 行为场景（可选，Gherkin）

```gherkin
Feature: getToggleValue 取值函数
  作为 生成式 UI 宿主开发者
  我想要 getToggleValue 返回指定 Toggle 的 isOn 与 label
  以便 在事件上下文或链中读取开关状态

  Scenario: 命中 Toggle
    Given Surface 上存在 id="agree" 的 Toggle(isOn=true, label="同意")
    When 以 {"call":"getToggleValue","args":{"componentId":"agree"}} 调用
    Then 返回 {"isOn":true,"label":"同意"}

  Scenario: 组件不存在
    Given Surface 上无 id="missing" 的 Toggle
    When 以 {"call":"getToggleValue","args":{"componentId":"missing"}} 调用
    Then 返回 {}
```

## Spec 自审清单

- [x] 无"待定""TBD""TODO"等占位符
- [x] 所有 AC 使用 WHEN/THEN 格式，可独立测试
- [x] 范围边界明确（getToggleValue 取值语义；Toggle 组件态归 07-04-12）
- [x] 无语义模糊表述
- [x] AC 与规则表交叉一致
- [x] 规则表每条通过 5 项质量检查（可复现/可观测/边界值/关联AC/无冲突）

## context-references

```yaml
context-queries:
  - repo: "GenerativeUI/A2UIRender"
    query: "NativeGetToggleValueFunction ExecuteWithContext ResolveComponentId FindComponentById ExtendedToggleComponent GetIsOn GetLabel PutBool PutString"
  - repo: "GenerativeUI/A2UIRender"
    query: "GetToggleValueFunction.ets loadExtendedFunctionSchema getToggleValue.json"
  - repo: "GenerativeUI/A2UIRender"
    query: "NativeFunctionRegistry Register getToggleValue"
  - repo: "GenerativeUI/Docs"
    query: "getToggleValue 组件取值函数 componentId isOn label"
```

**关键文档：** `genui/src/main/ets/core/functions/component/GetToggleValueFunction.ets`、`genui/src/main/cpp/functions/NativeGetToggleValueFunction.cpp`、`genui/src/main/cpp/components/extended/ExtendedToggleComponent.h`、`reference/functions/component-value.md`