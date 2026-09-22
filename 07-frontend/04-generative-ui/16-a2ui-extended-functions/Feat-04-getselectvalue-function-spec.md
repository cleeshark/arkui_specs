# 特性规格

> Func-07-04-16-Feat-04 `getSelectValue` 函数：固化 A2UI 鸿蒙扩展协议组件取值函数 `getSelectValue` 的语义——按 `componentId` 查找 Select 组件并返回其当前选中值（优先读 `value` 属性，缺省回退到 `selected` 索引 + `options` 数组；组件不存在或非 Select 返回空串 `""`）。ArkTS 目录注册（`isInnerNative: true` + schema `getSelectValue.json`），C++ `NativeGetSelectValueFunction::ExecuteWithContext` 经 `RenderManager::FindSurface` + `FindComponentById` 读取。基准实现：`@arkui-genius/genui`（A2UIRender）。

## 概述

| 属性 | 值 |
|------|-----|
| 特性名称 | getSelectValue 组件取值函数 |
| 特性编号 | Func-07-04-16-Feat-04 |
| 优先级 | P0 |
| 目标版本 | A2UI 鸿蒙扩展协议（`ohos.a2ui.extended.catalog`）+ API Version 20 |
| SIG 归属 | GenUI SIG |
| 状态 | Baselined |
| 复杂度 | 标准 |

## 本次变更范围（Delta）

| 类型 | 内容 | 说明 |
|------|------|------|
| ADDED | 无（存量补录） | 本特性为 Func-07-04-16 第四个 Feat |

## 输入文档

| 文档 | 路径 | 状态 |
|------|------|------|
| Design | `07-frontend/04-generative-ui/16-a2ui-extended-functions/design.md` | Baselined |
| 目录注册（ArkTS） | `genui/src/main/ets/core/functions/component/GetSelectValueFunction.ets` | — |
| 函数聚合（ArkTS） | `genui/src/main/ets/core/functions/A2UIBasicFunctions.ets` | — |
| 原生实现（C++） | `genui/src/main/cpp/functions/NativeGetSelectValueFunction.cpp`、`functions/NativeGetSelectValueFunction.h` | — |
| 注册表（C++） | `genui/src/main/cpp/functions/NativeFunctionRegistry.cpp` | — |
| schema | `genui/src/main/resources/rawfile/schema/Extended/functions/getSelectValue.json` | — |
| 组件（C++） | `genui/src/main/cpp/components/custom/CustomComponent.*`、`components/extended/ExtendedSelectComponent.*` | — |
| 函数参考（Docs） | `reference/functions/component-value.md`、`reference/functions/extension-functions.md` | 理解辅助 |

> 需求基线、不涉及项详见 proposal.md。design.md 与本文档并行产出，互不依赖。

---

## 用户故事

### US-1: 目录注册与 schema 契约

**作为** 生成式 UI 宿主开发者,
**我想要** `getSelectValue` 注册为扩展协议组件取值函数,
**以便** DSL 的 `call="getSelectValue"` 被引擎识别并受 schema 约束。

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-1.1 | WHEN 函数实例化 THEN `GetSelectValueFunction` 构造函数以 `super('getSelectValue')` 声明函数名（`GetSelectValueFunction.ets:22`） | 正常 |
| AC-1.2 | WHEN 目录项构建 THEN `asFunctionItem()` 返回 `name='getSelectValue'` 且 `isInnerNative=true`（`GetSelectValueFunction.ets:27-28`） | 正常 |
| AC-1.3 | WHEN schema 加载 THEN `loadExtendedFunctionSchema('getSelectValue.json')`（`GetSelectValueFunction.ets:35`） | 正常 |
| AC-1.4 | WHEN 聚合扩展内置函数 THEN `getSelectValue` 列入 `extendedCatalogFunctions`（`A2UIBasicFunctions.ets:67`） | 正常 |
| AC-1.5 | WHEN native 注册表初始化 THEN `Register("getSelectValue", ...)`（`NativeFunctionRegistry.cpp:83`） | 正常 |

### US-2: 选中值读取（正常）

**作为** 生成式 UI 宿主开发者,
**我想要** `getSelectValue` 返回 Select 的当前选中值,
**以便** 在事件上下文或链中读取下拉选中结果。

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-2.1 | WHEN 命中 `CustomComponent(Select)` 且 `value` 属性为 string 且非空 THEN 直接返回该 `value`（`NativeGetSelectValueFunction.cpp:150-153`） | 正常 |
| AC-2.2 | WHEN `value` 缺失或空且 `selected` 为非负整数、`options` 为数组 THEN 返回 `options[selected].value`（`ResolveInitialSelectedValue` → `ResolveOptionValueFromArray`，`NativeGetSelectValueFunction.cpp:62-101`） | 正常 |
| AC-2.3 | WHEN `options` 为 JSON 字符串 THEN 解析后再按索引取值（`ResolveOptionValue`，`NativeGetSelectValueFunction.cpp:75-88`） | 边界 |
| AC-2.4 | WHEN `selected` 非 number/非有限/负数/非整数 THEN `TryGetSelectedIndex` 返回 false，回退为空（`NativeGetSelectValueFunction.cpp:44-60`） | 边界 |

### US-3: 空值/异常返回

**作为** 生成式 UI 宿主开发者,
**我想要** `getSelectValue` 在缺失入参或非 Select 时返回空串,
**以便** 调用方稳定拿到 string 类型结果。

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-3.1 | WHEN `args` 非对象或 `componentId` 非 string 或空 THEN `ResolveTargetComponentId` 返回 `""`（`NativeGetSelectValueFunction.cpp:32-42`） | 异常 |
| AC-3.2 | WHEN `surfaceId` 空或 `targetComponentId` 空 THEN `LOG_WARN` 并返回空（`NativeGetSelectValueFunction.cpp:122-125`） | 边界 |
| AC-3.3 | WHEN `RenderManager::FindSurface` 返回 nullptr 或 `FindComponentById` 返回 nullptr THEN 返回空串（`NativeGetSelectValueFunction.cpp:127-137`） | 异常 |
| AC-3.4 | WHEN 组件非 `CustomComponent` 或 `GetShortType(GetType()) != "Select"` THEN 返回空串（`NativeGetSelectValueFunction.cpp:139-148`） | 异常 |
| AC-3.5 | WHEN 直接调用无上下文的 `Execute` THEN `LOG_WARN` 并返回空串（`NativeGetSelectValueFunction.cpp:110-115`） | 异常 |

### US-4: 返回值类型约束

**作为** 生成式 UI 宿主开发者,
**我想要** `getSelectValue` 的返回值被校验为 string,
**以便** DSL 中 `returnType:"string"` 的断言成立。

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-4.1 | WHEN 以 DynamicValue 消费且 `returnType` 为 `"string"` THEN `ValidateReturnType` 通过 `resultValue.IsString()`（`NativeFunctionBase.cpp:33-34`） | 正常 |
| AC-4.2 | WHEN `returnType` 与 string 不符 THEN 返回 `FailFunctionCall("builtin returnType mismatch")`（`NativeFunctionRegistry.cpp:135-140`） | 异常 |

## 验收追溯

| AC编号 | 关联规则 | 关联 Task | 验证方式 | 证据 |
|----|---------|----------|---------|------|
| AC-1.1,AC-1.2,AC-1.3,AC-1.4,AC-1.5 | R-1 | T-4 | ArkTS 单测 + 静态比对 | `GetSelectValueFunction.ets:22-35`、`A2UIBasicFunctions.ets:67`、`NativeFunctionRegistry.cpp:83` |
| AC-2.1,AC-2.2,AC-2.3,AC-2.4 | R-2 | T-4 | C++ UT：value 优先 + selected/options 回退 | `NativeGetSelectValueFunction.cpp:44-101,150-154` |
| AC-3.1,AC-3.2,AC-3.3,AC-3.4,AC-3.5 | R-3 | T-4 | C++ UT：空 componentId/无 Surface/非 Select/direct | `NativeGetSelectValueFunction.cpp:32-148` |
| AC-4.1,AC-4.2 | R-4 | T-4 | C++ UT：`ValidateReturnType` | `NativeFunctionBase.cpp:33-34` |

## 规则定义

| 规则ID | 类型 | 触发条件 | 预期行为 | 边界/约束 | 关联AC |
|--------|------|---------|---------|----------|--------|
| R-1 | 行为 | 函数注册 | 声明 `name='getSelectValue'`、`isInnerNative=true`、schema `getSelectValue.json`，native `Register` | 双注册一致 | AC-1.1,AC-1.2,AC-1.3,AC-1.4,AC-1.5 |
| R-2 | 行为 | componentId 命中 Select | `value` 属性优先；否则 `selected` + `options` 取 `options[selected].value` | options 支持数组/JSON 字符串；selected 须非负整数 | AC-2.1,AC-2.2,AC-2.3,AC-2.4 |
| R-3 | 异常 | componentId 空/无 Surface/无组件/非 Select/direct | 返回空串 `""` | 不抛错、无错误码 | AC-3.1,AC-3.2,AC-3.3,AC-3.4,AC-3.5 |
| R-4 | 行为 | 返回值校验 | returnType 必须 `string`，mismatch → `FailFunctionCall` | schema `returnType: const "string"` | AC-4.1,AC-4.2 |

## 验证映射

| 编号 | 对应规格项 | 验证方式 | 验证重点 |
|------|----------|---------|---------|
| VM-1 | AC-1.1,AC-1.2,AC-1.3,AC-1.4,AC-1.5 目录注册 | ArkTS 单测 | name/isInnerNative/schema 路径 |
| VM-2 | AC-2.1,AC-2.2,AC-2.3,AC-2.4 选中值读取 | C++ UT | value 优先 + selected/options 回退 |
| VM-3 | AC-3.1,AC-3.2,AC-3.3,AC-3.4,AC-3.5 空值返回 | C++ UT | 空 componentId/非 Select/direct |
| VM-4 | AC-4.1,AC-4.2 returnType | C++ UT | string 校验 + mismatch |

## API 变更分析

> 存量补录，无新增/变更 ArkTS 公共 API。`getSelectValue` 以 DSL `call` 暴露（inner-native）。

### 新增 API

N/A。

### 变更/废弃 API

| API 名称 | 变更类型 | 影响场景 | 迁移指引 | 关联 AC |
|----------|---------|---------|---------|--------|
| `getSelectValue`（DSL 取值函数） | 既有 | EventHandler 链 / `action.event.context` 动态值 | 经 `A2UIBasicFunctions.extendedCatalogFunctions` 注册 | AC-1.1,AC-1.2,AC-1.3,AC-1.4,AC-1.5 |

> d.ts 位置：函数 schema `rawfile/schema/Extended/functions/getSelectValue.json`。Kit：`@arkui-genius/genui`；权限：无。

## 接口规格

### 接口定义

**`NativeGetSelectValueFunction::ExecuteWithContext(resolvedArgs, context)`（原生，`call="getSelectValue"`）**

| 属性 | 值 |
|------|-----|
| 函数签名 | `FunctionResult ExecuteWithContext(const JsonValue& resolvedArgs, const DynamicResolveContext& context)`（`NativeGetSelectValueFunction.h:27`） |
| 返回值 | `FunctionResult(std::string)` — 选中值 / 空串 `""` |
| 开放范围 | DSL 取值函数（inner-native） |
| 错误码 | N/A（仅返回空串，故障仅 `LOG_WARN`） |
| 关联 AC | AC-2.1,AC-2.2,AC-2.3,AC-2.4,AC-3.1,AC-3.2,AC-3.3,AC-3.4,AC-3.5 |

**参数约束**

| 参数 | 类型 | 必填 | 默认值 | 约束条件 |
|------|------|------|--------|---------|
| componentId | string | 是 | — | 非空 string；schema `required:["componentId"]`、`additionalProperties:false` |
| returnType | string | 否 | `"string"` | 须为 `string` |

**行为场景**

| # | 触发条件 | 预期行为 | 关联 AC |
|---|----------|----------|---------|
| 1 | Select 且 value 非空 | 返回 value | AC-2.1 |
| 2 | value 缺失且 selected/options 有效 | 返回 `options[selected].value` | AC-2.2,AC-2.3 |
| 3 | selected 非法（非整数/负/非有限） | 返回空串 | AC-2.4 |
| 4 | componentId 空/无 Surface/非 Select | 返回空串 | AC-3.1,AC-3.2,AC-3.3,AC-3.4 |
| 5 | direct Execute（无上下文） | WARN + 空串 | AC-3.5 |

## 兼容性声明

- **已有 API 行为变更:** 否（存量补录）。
- **配置文件格式变更:** 否。
- **数据存储格式变更:** 否。
- **最低支持版本:** A2UI 鸿蒙扩展协议（`ohos.a2ui.extended.catalog`）+ API Version 20。
- **API 版本号策略:** schema 随版本加载（`schema/Extended/functions/getSelectValue.json`）。

## 架构约束

| 关键约束 | 约束说明 | 影响 AC |
|---------|---------|--------|
| 双注册一致 | ArkTS 目录注册与 C++ registry 对齐 | AC-1.1,AC-1.2,AC-1.3,AC-1.4,AC-1.5 |
| 上下文必需 | 取值必须经 `ExecuteWithContext`，direct `Execute` 为降级桩 | AC-3.5 |
| value 优先 | `value` 属性优先于 `selected`/`options` 推导 | AC-2.1,AC-2.2 |

## 非功能性需求

| 类型 | 指标/阈值 | 验证方式 | 证据 |
|------|----------|---------|------|
| 可靠性 | 非法入参不抛异常，统一返回空串 | C++ UT | `NativeGetSelectValueFunction.cpp:32-148` |
| 性能 | `FindSurface` + `FindComponentById` 查找 + 索引取值 | C++ UT | `NativeGetSelectValueFunction.cpp:127-154` |

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
| 多窗口/分屏 | 是 | 按 surfaceId 隔离 | AC-3.3 |
| 多用户 | 否 | 无差异 | — |
| 版本升级 | 是 | schema 随版本加载 | AC-1.3 |
| 生态兼容 | 是 | 鸿蒙扩展协议取值函数 | 概述「目标版本」 |

## 行为场景（可选，Gherkin）

```gherkin
Feature: getSelectValue 取值函数
  作为 生成式 UI 宿主开发者
  我想要 getSelectValue 返回 Select 的当前选中值
  以便 在事件上下文或链中读取下拉选中结果

  Scenario: 命中 Select 且 value 非空
    Given Surface 上存在 id="city" 的 Select，value="上海"
    When 以 {"call":"getSelectValue","args":{"componentId":"city"}} 调用
    Then 返回 "上海"

  Scenario: value 缺失回退 selected+options
    Given Surface 上存在 id="city" 的 Select，options=[{"value":"北京"},{"value":"上海"}]，selected=1
    When 以 {"call":"getSelectValue","args":{"componentId":"city"}} 调用
    Then 返回 "上海"

  Scenario: 组件不存在
    Given Surface 上无 id="missing" 的 Select
    When 以 {"call":"getSelectValue","args":{"componentId":"missing"}} 调用
    Then 返回 ""
```

## Spec 自审清单

- [x] 无"待定""TBD""TODO"等占位符
- [x] 所有 AC 使用 WHEN/THEN 格式，可独立测试
- [x] 范围边界明确（getSelectValue 取值语义；Select 组件态归 07-04-12）
- [x] 无语义模糊表述
- [x] AC 与规则表交叉一致
- [x] 规则表每条通过 5 项质量检查（可复现/可观测/边界值/关联AC/无冲突）

## context-references

```yaml
context-queries:
  - repo: "GenerativeUI/A2UIRender"
    query: "NativeGetSelectValueFunction ExecuteWithContext ResolveTargetComponentId TryGetSelectedIndex ResolveOptionValue ResolveInitialSelectedValue"
  - repo: "GenerativeUI/A2UIRender"
    query: "GetSelectValueFunction.ets loadExtendedFunctionSchema getSelectValue.json"
  - repo: "GenerativeUI/A2UIRender"
    query: "NativeFunctionRegistry Register getSelectValue RenderManager FindSurface"
  - repo: "GenerativeUI/Docs"
    query: "getSelectValue 组件取值函数 componentId selected options value"
```

**关键文档：** `genui/src/main/ets/core/functions/component/GetSelectValueFunction.ets`、`genui/src/main/cpp/functions/NativeGetSelectValueFunction.cpp`、`genui/src/main/cpp/functions/NativeFunctionRegistry.cpp`、`reference/functions/component-value.md`