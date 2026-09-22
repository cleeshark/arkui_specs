# 特性规格

> Func-07-04-16-Feat-07 `setAttributes` 函数：固化 A2UI 鸿蒙扩展协议属性操作函数 `setAttributes` 的语义——在 EventHandler 链中按 `componentId` 批量覆盖目标组件属性（`value` 对象），扩展组件另支持 `value.styles` 样式增量。ArkTS 目录注册（`isInnerNative: true` + schema `setAttributes.json`），运行时分发走**动作注册表**（`NativeActionDispatcher → NativeActionRegistry` 的 `SetAttributesAction`，`BuiltInActions.cpp`）。`componentId` 空或 `value` 非对象仅 `LOG_WARN` 放弃。Docs 参数名 `id, attributes` 与代码 `componentId`+`value` 不符（以代码为准）。基准实现：`@arkui-genius/genui`（A2UIRender）。

## 概述

| 属性 | 值 |
|------|-----|
| 特性名称 | setAttributes 属性动作函数 |
| 特性编号 | Func-07-04-16-Feat-07 |
| 优先级 | P0 |
| 目标版本 | A2UI 鸿蒙扩展协议（`ohos.a2ui.extended.catalog`）+ API Version 20 |
| SIG 归属 | GenUI SIG |
| 状态 | Baselined |
| 复杂度 | 标准 |

## 本次变更范围（Delta）

| 类型 | 内容 | 说明 |
|------|------|------|
| ADDED | 无（存量补录） | 本特性为 Func-07-04-16 第七个 Feat |

## 输入文档

| 文档 | 路径 | 状态 |
|------|------|------|
| Design | `07-frontend/04-generative-ui/16-a2ui-extended-functions/design.md` | Baselined |
| 目录注册（ArkTS） | `genui/src/main/ets/core/functions/extended/CatalogActionFunctions.ets` | — |
| 函数聚合（ArkTS） | `genui/src/main/ets/core/functions/A2UIBasicFunctions.ets` | — |
| 动作实现（C++） | `genui/src/main/cpp/components/actions/BuiltInActions.cpp` | — |
| 组件属性落地（C++） | `genui/src/main/cpp/components/Component.cpp`、`components/extended/ExtendedComponent.cpp` | — |
| schema | `genui/src/main/resources/rawfile/schema/Extended/functions/setAttributes.json` | — |
| 函数参考（Docs） | `reference/functions/extension-functions.md` | 理解辅助 |

> 需求基线、不涉及项详见 proposal.md。design.md 与本文档并行产出，互不依赖。

---

## 用户故事

### US-1: 目录注册与 schema 契约

**作为** 生成式 UI 宿主开发者,
**我想要** `setAttributes` 注册为扩展协议属性操作函数,
**以便** DSL 的 `call="setAttributes"` 被引擎识别并受 schema 约束。

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-1.1 | WHEN 构造 THEN `setAttributesFunction = new CatalogActionFunction('setAttributes', 'setAttributes.json')`（`CatalogActionFunctions.ets:46-47`） | 正常 |
| AC-1.2 | WHEN 目录项构建 THEN `asFunctionItem()` 返回 `name='setAttributes'` 且 `isInnerNative=true`（`CatalogActionFunctions.ets:30-37`） | 正常 |
| AC-1.3 | WHEN schema 加载 THEN `loadExtendedFunctionSchema('setAttributes.json')`（`CatalogActionFunctions.ets:39-41`） | 正常 |
| AC-1.4 | WHEN 聚合扩展内置函数 THEN `setAttributes` 列入 `extendedCatalogFunctions`（`A2UIBasicFunctions.ets:69`） | 正常 |
| AC-1.5 | WHEN 动作注册 THEN `RegisterBuiltInActions` 注册 `"setAttributes" → SetAttributesAction`（`BuiltInActions.cpp:207`） | 正常 |

### US-2: 属性覆盖（正常）

**作为** 生成式 UI 宿主开发者,
**我想要** `setAttributes` 批量覆盖目标组件属性,
**以便** 动态更新组件外观/内容。

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-2.1 | WHEN `componentId` 非空且组件存在 THEN `component->ApplyDescriptor(value)` 落地属性（`BuiltInActions.cpp:186-193`） | 正常 |
| AC-2.2 | WHEN 组件为 `ExtendedComponent` 且 `value.styles` 存在 THEN 额外 `ApplyStyleDelta(value.GetItem("styles"))` 增量样式（`BuiltInActions.cpp:194-197`） | 正常 |
| AC-2.3 | WHEN `value` 为 object THEN 按 key 覆盖对应属性（schema `additionalProperties:false` 另做解析期约束） | 正常 |

### US-3: 非法入参降级（异常/边界）

**作为** 生成式 UI 宿主开发者,
**我想要** `setAttributes` 在 componentId 空或 value 非法时放弃,
**以便** 非法调用不破坏组件状态。

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-3.1 | WHEN `componentId` 为空 THEN `LOG_WARN` 并返回（`BuiltInActions.cpp:164-169`） | 异常 |
| AC-3.2 | WHEN `value` 非 object THEN `LOG_WARN` 并返回（`BuiltInActions.cpp:171-176`） | 异常 |
| AC-3.3 | WHEN Surface 未找到 THEN `LOG_WARN` 并返回（`BuiltInActions.cpp:178-184`） | 异常 |
| AC-3.4 | WHEN 组件不存在 THEN `LOG_WARN` 并返回（`BuiltInActions.cpp:186-191`） | 异常 |

### US-4: 分发路径与返回值

**作为** 生成式 UI 宿主开发者,
**我想要** `setAttributes` 经动作注册表分发且不产生返回值,
**以便** 明确其副作用动作语义。

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-4.1 | WHEN 链内 `call="setAttributes"` THEN `NativeActionDispatcher::CanDispatch` 命中 `NativeActionRegistry`（`ActionDispatcher.cpp:26-35`） | 正常 |
| AC-4.2 | WHEN `setAttributes` 执行 THEN 返回 `JsonValue()`（无结果）（`BuiltInActions.cpp:198`） | 正常 |
| AC-4.3 | WHEN `setAttributes` 不在 `NativeFunctionRegistry` THEN 不会经函数注册表分发（`NativeFunctionRegistry.cpp:66-86` 未含 setAttributes） | 边界 |

## 验收追溯

| AC编号 | 关联规则 | 关联 Task | 验证方式 | 证据 |
|----|---------|----------|---------|------|
| AC-1.1,AC-1.2,AC-1.3,AC-1.4,AC-1.5 | R-1 | T-7 | ArkTS 单测 + 静态比对 | `CatalogActionFunctions.ets:30-47`、`A2UIBasicFunctions.ets:69`、`BuiltInActions.cpp:207` |
| AC-2.1,AC-2.2,AC-2.3 | R-2 | T-7 | C++ UT：ApplyDescriptor/ApplyStyleDelta | `BuiltInActions.cpp:162-198`、`Component.cpp:638`、`ExtendedComponent.cpp:192` |
| AC-3.1,AC-3.2,AC-3.3,AC-3.4 | R-3 | T-7 | C++ UT：空 componentId/非对象/无组件 | `BuiltInActions.cpp:162-191` |
| AC-4.1,AC-4.2,AC-4.3 | R-4 | T-7 | C++ UT + 静态比对：动作注册表分发 | `ActionDispatcher.cpp:26-35`、`NativeFunctionRegistry.cpp:66-86` |

## 规则定义

| 规则ID | 类型 | 触发条件 | 预期行为 | 边界/约束 | 关联AC |
|--------|------|---------|---------|----------|--------|
| R-1 | 行为 | 函数注册 | 声明 `name='setAttributes'`、`isInnerNative=true`、schema `setAttributes.json`，动作注册表 `Register` | 双注册一致 | AC-1.1,AC-1.2,AC-1.3,AC-1.4,AC-1.5 |
| R-2 | 行为 | componentId 非空且组件存在 | `ApplyDescriptor(value)`；`ExtendedComponent` 另走 `ApplyStyleDelta(value.styles)` | value 须 object | AC-2.1,AC-2.2,AC-2.3 |
| R-3 | 异常 | componentId 空/value 非对象/无 Surface/无组件 | `LOG_WARN` 放弃、不抛错无错误码 | — | AC-3.1,AC-3.2,AC-3.3,AC-3.4 |
| R-4 | 行为 | 分发路径 | 经 `NativeActionRegistry`（非 `NativeFunctionRegistry`），返回空 `JsonValue` | 无返回值 | AC-4.1,AC-4.2,AC-4.3 |

## 验证映射

| 编号 | 对应规格项 | 验证方式 | 验证重点 |
|------|----------|---------|---------|
| VM-1 | AC-1.1,AC-1.2,AC-1.3,AC-1.4,AC-1.5 目录注册 | ArkTS 单测 | name/isInnerNative/schema + 动作注册 |
| VM-2 | AC-2.1,AC-2.2,AC-2.3 属性覆盖 | C++ UT | ApplyDescriptor + ApplyStyleDelta |
| VM-3 | AC-3.1,AC-3.2,AC-3.3,AC-3.4 非法入参 | C++ UT | 空 componentId/非对象/无组件 |
| VM-4 | AC-4.1,AC-4.2,AC-4.3 分发路径 | C++ UT | 动作注册表 vs 函数注册表 |

## API 变更分析

> 存量补录，无新增/变更 ArkTS 公共 API。`setAttributes` 以 DSL `call` 暴露（inner-native，副作用动作）。

### 新增 API

N/A。

### 变更/废弃 API

| API 名称 | 变更类型 | 影响场景 | 迁移指引 | 关联 AC |
|----------|---------|---------|---------|--------|
| `setAttributes`（DSL 属性动作函数） | 既有 | EventHandler 链属性更新 | 经 `A2UIBasicFunctions.extendedCatalogFunctions` 注册 + 动作注册表分发 | AC-1.1,AC-1.2,AC-1.3,AC-1.4,AC-1.5 |

> d.ts 位置：函数 schema `rawfile/schema/Extended/functions/setAttributes.json`。Kit：`@arkui-genius/genui`；权限：无。

## 接口规格

### 接口定义

**`SetAttributesAction(args, ctx)`（动作 handler，`call="setAttributes"`）**

| 属性 | 值 |
|------|-----|
| 函数签名 | `JsonValue SetAttributesAction(const JsonValue& args, EventHandlerChainExecutor::ExecutionContext& ctx)`（`BuiltInActions.cpp:162`） |
| 返回值 | `JsonValue()`（void，无结果） |
| 开放范围 | DSL 属性动作函数（inner-native） |
| 错误码 | N/A（非法入参仅 `LOG_WARN`） |
| 关联 AC | AC-2.1,AC-2.2,AC-2.3,AC-3.1,AC-3.2,AC-3.3,AC-3.4,AC-4.1,AC-4.2,AC-4.3 |

**参数约束**

| 参数 | 类型 | 必填 | 默认值 | 约束条件 |
|------|------|------|--------|---------|
| componentId | string | 是 | — | 非空 string；schema `required:["componentId","value"]` |
| value | object | 是 | — | 非空对象，可选 `value.styles` 子键；schema `additionalProperties:false` |
| returnType | string | 否 | `"void"` | 须为 `void` |

**行为场景**

| # | 触发条件 | 预期行为 | 关联 AC |
|---|----------|----------|---------|
| 1 | componentId 命中组件 | ApplyDescriptor(value) | AC-2.1 |
| 2 | 命中扩展组件且有 styles | ApplyStyleDelta(styles) | AC-2.2 |
| 3 | componentId 空/value 非对象/无组件 | LOG_WARN 放弃 | AC-3.1,AC-3.2,AC-3.3,AC-3.4 |
| 4 | 链内分发 | 经 NativeActionRegistry，返回空 | AC-4.1,AC-4.2,AC-4.3 |

## 兼容性声明

- **已有 API 行为变更:** 否（存量补录）。
- **配置文件格式变更:** 否。
- **数据存储格式变更:** 否。
- **最低支持版本:** A2UI 鸿蒙扩展协议（`ohos.a2ui.extended.catalog`）+ API Version 20。
- **API 版本号策略:** schema 随版本加载（`schema/Extended/functions/setAttributes.json`）。
- **编码期契约分歧:** Docs `extension-functions.md` 描述参数为 `id, attributes`，实际代码/schema 为 `componentId` + `value`（含可选 `styles` 子键），以代码为准（见 RISK）。

## 架构约束

| 关键约束 | 约束说明 | 影响 AC |
|---------|---------|--------|
| 动作注册表分发 | 经 `NativeActionRegistry`，非 `NativeFunctionRegistry` | AC-4.1,AC-4.3 |
| value 对象前置 | value 非对象含严格放弃 | AC-3.2 |
| 双路径落地 | `ApplyDescriptor`（全量属性）+ `ApplyStyleDelta`（扩展样式增量） | AC-2.1,AC-2.2 |

## 非功能性需求

| 类型 | 指标/阈值 | 验证方式 | 证据 |
|------|----------|---------|------|
| 可靠性 | 非法入参不抛异常、不破坏组件状态 | C++ UT | `BuiltInActions.cpp:162-191` |
| 性能 | 单组件查找 + 属性批量覆盖 | C++ UT | `BuiltInActions.cpp:178-197` |

## 多设备适配声明

| 设备类型 | 行为差异 | 规格/约束 | 验证方式 | 证据 |
|---------|---------|----------|---------|------|
| 手机 | 无差异 | 属性覆盖逻辑设备无关 | ohosTest | — |
| 平板 | 无差异 | 同上 | ohosTest | — |
| 折叠屏 | 无差异 | 同上 | ohosTest | — |

## 全局特性影响

| 特性 | 适用？ | 结论 | 关联场景 |
|------|-------|------|---------|
| 无障碍 | 是 | 若覆盖 label 等文本属性可影响无障碍读取 | AC-2.1 |
| 大字体 | 否 | 不直接涉及 | — |
| 深色模式 | 是 | 若覆盖样式属性可能影响主题一致性 | AC-2.2 |
| 多窗口/分屏 | 是 | 按 surfaceId 定位组件 | AC-3.3 |
| 多用户 | 否 | 无差异 | — |
| 版本升级 | 是 | schema 随版本加载 | AC-1.3 |
| 生态兼容 | 是 | 鸿蒙扩展协议属性操作函数 | 概述「目标版本」 |

## 行为场景（可选，Gherkin）

```gherkin
Feature: setAttributes 属性动作函数
  作为 生成式 UI 宿主开发者
  我想要 setAttributes 批量覆盖目标组件属性
  以便 动态更新组件外观/内容

  Scenario: 正常覆盖
    Given Surface 上存在 id="submit_btn" 的 Button
    When 以 {"call":"setAttributes","args":{"componentId":"submit_btn","value":{"label":"加载中..."}}} 执行
    Then submit_btn 的 label 更新为 "加载中..."

  Scenario: 扩展组件样式增量
    Given Surface 上存在 id="card" 的扩展组件
    When 以 {"call":"setAttributes","args":{"componentId":"card","value":{"styles":{"opacity":0.5}}}} 执行
    Then card 经 ApplyStyleDelta 应用 opacity=0.5

  Scenario: componentId 为空放弃
    Given 调用 setAttributes
    When componentId 为空串
    Then 不更新、仅 LOG_WARN
```

## Spec 自审清单

- [x] 无"待定""TBD""TODO"等占位符
- [x] 所有 AC 使用 WHEN/THEN 格式，可独立测试
- [x] 范围边界明确（setAttributes 属性覆盖语义；组件属性定义归 07-04-12/13）
- [x] 无语义模糊表述
- [x] AC 与规则表交叉一致
- [x] 规则表每条通过 5 项质量检查（可复现/可观测/边界值/关联AC/无冲突）

## context-references

```yaml
context-queries:
  - repo: "GenerativeUI/A2UIRender"
    query: "BuiltInActions SetAttributesAction component ApplyDescriptor ApplyStyleDelta styles value"
  - repo: "GenerativeUI/A2UIRender"
    query: "CatalogActionFunctions setAttributesFunction setAttributes.json isInnerNative"
  - repo: "GenerativeUI/A2UIRender"
    query: "Component ApplyDescriptor ExtendedComponent ApplyStyleDelta"
  - repo: "GenerativeUI/Docs"
    query: "setAttributes 属性操作函数 componentId value 动态设置"
```

**关键文档：** `genui/src/main/ets/core/functions/extended/CatalogActionFunctions.ets`、`genui/src/main/cpp/components/actions/BuiltInActions.cpp`、`genui/src/main/cpp/components/Component.cpp`、`genui/src/main/cpp/components/extended/ExtendedComponent.cpp`、`reference/functions/extension-functions.md`