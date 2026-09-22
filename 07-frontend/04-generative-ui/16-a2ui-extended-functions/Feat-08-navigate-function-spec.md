# 特性规格

> Func-07-04-16-Feat-08 `navigate` 函数：固化 A2UI 鸿蒙扩展协议导航函数 `navigate` 的语义——按 `componentId`（NavContainer 容器）+ `targetComponentId`（目标子页）调用 `NavigateToTargetComponent` 切换 `currentIndex` 并返回 `bool` 成功态。ArkTS 目录注册（`isInnerNative: true` + schema `navigate.json`），C++ `NativeNavigateFunction::ExecuteWithContext` 经 `FindSurfaceForContext` + `FindComponentById` + `dynamic_pointer_cast<NavContainerComponent>` 执行。注意 schema 声明 `returnType:"void"` 但实现返回 `bool`；Docs 描述 `url, params?` 与实际 `componentId`+`targetComponentId` 不符（均以代码为准）。基准实现：`@arkui-genius/genui`（A2UIRender）。

## 概述

| 属性 | 值 |
|------|-----|
| 特性名称 | navigate 容器内导航函数 |
| 特性编号 | Func-07-04-16-Feat-08 |
| 优先级 | P0 |
| 目标版本 | A2UI 鸿蒙扩展协议（`ohos.a2ui.extended.catalog`）+ API Version 20 |
| SIG 归属 | GenUI SIG |
| 状态 | Baselined |
| 复杂度 | 标准 |

## 本次变更范围（Delta）

| 类型 | 内容 | 说明 |
|------|------|------|
| ADDED | 无（存量补录） | 本特性为 Func-07-04-16 第八个 Feat |

## 输入文档

| 文档 | 路径 | 状态 |
|------|------|------|
| Design | `07-frontend/04-generative-ui/16-a2ui-extended-functions/design.md` | Baselined |
| 目录注册（ArkTS） | `genui/src/main/ets/core/functions/extended/NavigateFunction.ets` | — |
| 函数聚合（ArkTS） | `genui/src/main/ets/core/functions/A2UIBasicFunctions.ets` | — |
| 原生实现（C++） | `genui/src/main/cpp/functions/extended/NativeNavigateFunction.cpp`、`functions/extended/NativeNavigateFunction.h` | — |
| 注册表（C++） | `genui/src/main/cpp/functions/NativeFunctionRegistry.cpp` | — |
| 组件（C++） | `genui/src/main/cpp/components/extended/NavContainerComponent.cpp` | — |
| schema | `genui/src/main/resources/rawfile/schema/Extended/functions/navigate.json` | — |
| 函数参考（Docs） | `reference/functions/extension-functions.md`、`concepts/actions-and-functions.md` | 理解辅助（存在滞后，见风险） |

> 需求基线、不涉及项详见 proposal.md。design.md 与本文档并行产出，互不依赖。

---

## 用户故事

### US-1: 目录注册与 schema 契约

**作为** 生成式 UI 宿主开发者,
**我想要** `navigate` 注册为扩展协议导航函数,
**以便** DSL 的 `call="navigate"` 被引擎识别并受 schema 约束。

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-1.1 | WHEN 函数实例化 THEN `NavigateFunction` 构造函数以 `super('navigate')` 声明函数名（`NavigateFunction.ets:22`） | 正常 |
| AC-1.2 | WHEN 目录项构建 THEN `asFunctionItem()` 返回 `name='navigate'` 且 `isInnerNative=true`（`NavigateFunction.ets:27-28`） | 正常 |
| AC-1.3 | WHEN schema 加载 THEN `loadExtendedFunctionSchema('navigate.json')`（`NavigateFunction.ets:35`） | 正常 |
| AC-1.4 | WHEN 聚合扩展内置函数 THEN `navigate` 列入 `extendedCatalogFunctions`（`A2UIBasicFunctions.ets:71`） | 正常 |
| AC-1.5 | WHEN native 注册表初始化 THEN `Register("navigate", NativeNavigateFunction)`（`NativeFunctionRegistry.cpp:85`） | 正常 |

### US-2: 容器内导航（正常）

**作为** 生成式 UI 宿主开发者,
**我想要** `navigate` 将 NavContainer 切换到目标子页,
**以便** 实现扩展容器内的子页跳转。

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-2.1 | WHEN `componentId` 与 `targetComponentId` 均非空且 `componentId` 命中 `NavContainerComponent` THEN 调用 `NavigateToTargetComponent(targetComponentId)`（`NativeNavigateFunction.cpp:85-95`） | 正常 |
| AC-2.2 | WHEN 目标子组件存在于容器 children THEN `NavigateToTargetComponent` 命中 id、`SetCurrentIndex` + `RefreshChildVisibility` 并返回 true（`NavContainerComponent.cpp:141-164`） | 正常 |
| AC-2.3 | WHEN 目标子组件不存在于容器 children THEN `NavigateToTargetComponent` 返回 false（`NavContainerComponent.cpp:143-157`） | 边界 |

### US-3: 无效入参降级（异常/边界）

**作为** 生成式 UI 宿主开发者,
**我想要** `navigate` 在缺失入参或非容器组件时返回 false,
**以便** 调用方可感知导航失败。

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-3.1 | WHEN `args` 非对象或 `componentId`/`targetComponentId` 非 string THEN `ResolveComponentId`/`ResolveTargetComponentId` 返回 `""`（`NativeNavigateFunction.cpp:29-53`） | 异常 |
| AC-3.2 | WHEN `componentId` 或 `targetComponentId` 为 `""` THEN 返回 `FunctionResult(false)`（`NativeNavigateFunction.cpp:72-76`） | 边界 |
| AC-3.3 | WHEN `FindSurfaceForContext` 返回 nullptr THEN `LOG_WARN` 并返回 false（`NativeNavigateFunction.cpp:78-83`） | 异常 |
| AC-3.4 | WHEN 组件非 `NavContainerComponent` THEN `LOG_WARN` 并返回 false（`NativeNavigateFunction.cpp:85-92`） | 异常 |
| AC-3.5 | WHEN 直接调用无上下文的 `Execute` THEN `LOG_WARN` 并返回 false（`NativeNavigateFunction.cpp:62-67`） | 异常 |

### US-4: 返回值与编码期契约分歧

**作为** 生成式 UI 宿主开发者,
**我想要** 明确 `navigate` 返回 bool 而 schema 声明 void 的分歧,
**以便** 下游正确消费。

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-4.1 | WHEN 导航成功/失败 THEN 返回 `FunctionResult(success)`（bool）（`NativeNavigateFunction.cpp:94-95`） | 正常 |
| AC-4.2 | WHEN schema 校验 THEN `navigate.json` 声明 `returnType: const "void"`（与实现返回 bool 存在分歧，见风险） | 边界 |

## 验收追溯

| AC编号 | 关联规则 | 关联 Task | 验证方式 | 证据 |
|----|---------|----------|---------|------|
| AC-1.1,AC-1.2,AC-1.3,AC-1.4,AC-1.5 | R-1 | T-8 | ArkTS 单测 + 静态比对 | `NavigateFunction.ets:22-35`、`A2UIBasicFunctions.ets:71`、`NativeFunctionRegistry.cpp:85` |
| AC-2.1,AC-2.2,AC-2.3 | R-2 | T-8 | C++ UT：NavigateToTargetComponent 命中/未命中 | `NativeNavigateFunction.cpp:85-95`、`NavContainerComponent.cpp:141-164` |
| AC-3.1,AC-3.2,AC-3.3,AC-3.4,AC-3.5 | R-3 | T-8 | C++ UT：空入参/无 Surface/非容器/direct | `NativeNavigateFunction.cpp:29-92` |
| AC-4.1,AC-4.2 | R-4 | T-8 | 静态比对：返回 bool vs schema void | `NativeNavigateFunction.cpp:94-95`、`navigate.json` |

## 规则定义

| 规则ID | 类型 | 触发条件 | 预期行为 | 边界/约束 | 关联AC |
|--------|------|---------|---------|----------|--------|
| R-1 | 行为 | 函数注册 | 声明 `name='navigate'`、`isInnerNative=true`、schema `navigate.json`，native `Register` | 双注册一致 | AC-1.1,AC-1.2,AC-1.3,AC-1.4,AC-1.5 |
| R-2 | 行为 | componentId 命中 NavContainer | `NavigateToTargetComponent` 切换 currentIndex 返回 bool | 目标必须为容器 children | AC-2.1,AC-2.2,AC-2.3 |
| R-3 | 异常 | componentId/targetComponentId 空/无 Surface/非 NavContainer/direct | 返回 false | 不抛错、无错误码 | AC-3.1,AC-3.2,AC-3.3,AC-3.4,AC-3.5 |
| R-4 | 行为 | 返回值分歧 | 实现返回 `bool`；schema 声明 `void` | 编码期契约不一致（风险） | AC-4.1,AC-4.2 |

## 验证映射

| 编号 | 对应规格项 | 验证方式 | 验证重点 |
|------|----------|---------|---------|
| VM-1 | AC-1.1,AC-1.2,AC-1.3,AC-1.4,AC-1.5 目录注册 | ArkTS 单测 | name/isInnerNative/schema 路径 |
| VM-2 | AC-2.1,AC-2.2,AC-2.3 容器内导航 | C++ UT | currentIndex 切换 + 命中/未命中 |
| VM-3 | AC-3.1,AC-3.2,AC-3.3,AC-3.4,AC-3.5 降级返回 | C++ UT | 空入参/非容器/direct |
| VM-4 | AC-4.1,AC-4.2 返回值分歧 | 静态比对 | bool vs void |

## API 变更分析

> 存量补录，无新增/变更 ArkTS 公共 API。`navigate` 以 DSL `call` 暴露（inner-native）。

### 新增 API

N/A。

### 变更/废弃 API

| API 名称 | 变更类型 | 影响场景 | 迁移指引 | 关联 AC |
|----------|---------|---------|---------|--------|
| `navigate`（DSL 导航函数） | 既有 | EventHandler 链容器内导航 | 经 `A2UIBasicFunctions.extendedCatalogFunctions` 注册 | AC-1.1,AC-1.2,AC-1.3,AC-1.4,AC-1.5 |

> d.ts 位置：函数 schema `rawfile/schema/Extended/functions/navigate.json`。Kit：`@arkui-genius/genui`；权限：无。

## 接口规格

### 接口定义

**`NativeNavigateFunction::ExecuteWithContext(resolvedArgs, context)`（原生，`call="navigate"`）**

| 属性 | 值 |
|------|-----|
| 函数签名 | `FunctionResult ExecuteWithContext(const JsonValue& resolvedArgs, const DynamicResolveContext& context)`（`NativeNavigateFunction.h:27`） |
| 返回值 | `FunctionResult(bool)` — 导航成功 true / 失败 false（schema 声明 `void`） |
| 开放范围 | DSL 导航函数（inner-native） |
| 错误码 | N/A（仅返回 bool，故障仅 `LOG_WARN`） |
| 关联 AC | AC-2.1,AC-2.2,AC-2.3,AC-3.1,AC-3.2,AC-3.3,AC-3.4,AC-3.5,AC-4.1,AC-4.2 |

**参数约束**

| 参数 | 类型 | 必填 | 默认值 | 约束条件 |
|------|------|------|--------|---------|
| componentId | string | 是 | — | 非空 string，须为 NavContainer 的 id |
| targetComponentId | string | 是 | — | 非空 string，须为容器 children 中某子组件 id |
| returnType | string | 否 | schema `"void"` | 实现返回 bool，见风险 |

**行为场景**

| # | 触发条件 | 预期行为 | 关联 AC |
|---|----------|----------|---------|
| 1 | componentId 命中 NavContainer 且 target 存在 | 切换 currentIndex，返回 true | AC-2.1,AC-2.2 |
| 2 | target 不存在 | 返回 false | AC-2.3 |
| 3 | 入参空/无 Surface/非 NavContainer | 返回 false | AC-3.1,AC-3.2,AC-3.3,AC-3.4 |
| 4 | direct Execute（无上下文） | WARN + false | AC-3.5 |

## 兼容性声明

- **已有 API 行为变更:** 否（存量补录）。
- **配置文件格式变更:** 否。
- **数据存储格式变更:** 否。
- **最低支持版本:** A2UI 鸿蒙扩展协议（`ohos.a2ui.extended.catalog`）+ API Version 20。
- **API 版本号策略:** schema 随版本加载（`schema/Extended/functions/navigate.json`）。
- **编码期契约分歧:** ① Docs `extension-functions.md` 描述参数为 `url, params?`（页面路由），实际为 `componentId` + `targetComponentId`（容器内导航）；② Docs `actions-and-functions.md:245` 标「navigate 函数（当前未实现）」，实际已实现；③ schema 声明 `returnType:"void"`，实际返回 `bool`。均以代码为准（见 RISK）。

## 架构约束

| 关键约束 | 约束说明 | 影响 AC |
|---------|---------|--------|
| 双注册一致 | ArkTS 目录注册与 C++ registry 对齐 | AC-1.1,AC-1.2,AC-1.3,AC-1.4,AC-1.5 |
| 上下文必需 | 导航必须经 `ExecuteWithContext`，direct `Execute` 为降级桩 | AC-3.5 |
| 容器作用域 | 仅作用于 NavContainer 子组件，非跨页路由 | AC-2.1,AC-3.4 |

## 非功能性需求

| 类型 | 指标/阈值 | 验证方式 | 证据 |
|------|----------|---------|------|
| 可靠性 | 非法入参不抛异常，稳定返回 false | C++ UT | `NativeNavigateFunction.cpp:29-92` |
| 性能 | 单次容器 children 线性查找 | C++ UT | `NavContainerComponent.cpp:141-160` |

## 多设备适配声明

| 设备类型 | 行为差异 | 规格/约束 | 验证方式 | 证据 |
|---------|---------|----------|---------|------|
| 手机 | 无差异 | 导航逻辑设备无关 | ohosTest | — |
| 平板 | 无差异 | 同上 | ohosTest | — |
| 折叠屏 | 无差异 | 同上 | ohosTest | — |

## 全局特性影响

| 特性 | 适用？ | 结论 | 关联场景 |
|------|-------|------|---------|
| 无障碍 | 否 | 子页切换由 NavContainer 呈现 | — |
| 大字体 | 否 | 不涉及 | — |
| 深色模式 | 否 | 不涉及 | — |
| 多窗口/分屏 | 是 | 按 surfaceId 定位容器 | AC-3.3 |
| 多用户 | 否 | 无差异 | — |
| 版本升级 | 是 | schema 随版本加载 | AC-1.3 |
| 生态兼容 | 是 | 鸿蒙扩展协议导航函数（容器内语义，非官方 url 路由） | 概述「目标版本」 |

## 行为场景（可选，Gherkin）

```gherkin
Feature: navigate 容器内导航函数
  作为 生成式 UI 宿主开发者
  我想要 navigate 将 NavContainer 切换到目标子页
  以便 实现扩展容器内的子页跳转

  Scenario: 命中目标子页
    Given Surface 上存在 id="main_nav" 的 NavContainer，其 children 含 id="settings_page"
    When 以 {"call":"navigate","args":{"componentId":"main_nav","targetComponentId":"settings_page"}} 调用
    Then NavContainer 切换 currentIndex 到 settings_page 并返回 true

  Scenario: 目标不存在
    Given NavContainer 不含 id="missing" 的子组件
    When 以 {"call":"navigate","args":{"componentId":"main_nav","targetComponentId":"missing"}} 调用
    Then 返回 false

  Scenario: 非 NavContainer
    Given componentId 命中非 NavContainer 组件
    When 调用 navigate
    Then 返回 false
```

## Spec 自审清单

- [x] 无"待定""TBD""TODO"等占位符
- [x] 所有 AC 使用 WHEN/THEN 格式，可独立测试
- [x] 范围边界明确（navigate 容器内导航语义；NavContainer 组件归 07-04-13）
- [x] 无语义模糊表述
- [x] AC 与规则表交叉一致
- [x] 规则表每条通过 5 项质量检查（可复现/可观测/边界值/关联AC/无冲突）

## context-references

```yaml
context-queries:
  - repo: "GenerativeUI/A2UIRender"
    query: "NativeNavigateFunction ExecuteWithContext ResolveComponentId ResolveTargetComponentId NavContainerComponent NavigateToTargetComponent"
  - repo: "GenerativeUI/A2UIRender"
    query: "NavigateFunction.ets loadExtendedFunctionSchema navigate.json isInnerNative"
  - repo: "GenerativeUI/A2UIRender"
    query: "NativeFunctionRegistry Register navigate NativeFunctionComponentUtils FindSurfaceForContext"
  - repo: "GenerativeUI/Docs"
    query: "navigate 导航函数 componentId targetComponentId NavContainer url 参数分歧"
```

**关键文档：** `genui/src/main/ets/core/functions/extended/NavigateFunction.ets`、`genui/src/main/cpp/functions/extended/NativeNavigateFunction.cpp`、`genui/src/main/cpp/components/extended/NavContainerComponent.cpp`、`reference/functions/extension-functions.md`