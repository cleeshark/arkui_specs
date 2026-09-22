# 特性规格

> Func-07-04-23-Feat-03 条件组件与断点重渲染：固化 `If` 条件组件（`condition` 表达式 + `childrenIf`/`childrenElse` 分支）、条件求值（`EvaluateConditionWithExpressionEngine`）、依赖收集（`CollectConditionDependencies`→`SyncConditionExpressionBinding`）、断点变化双通道重求值（主题 `OnConfigChange` + `__widthBreakpoint` `NotifyGlobalVariableChanged`→`OnDataUpdate`）与分支切换（`ReevaluateAndSwitch`→`SelectBranch`/`ReconcileBranchChildren`）。基准实现：`@arkui-genius/genui`（A2UIRender）。

## 概述

| 属性 | 值 |
|------|-----|
| 特性名称 | 条件组件与断点重渲染 |
| 特性编号 | Func-07-04-23-Feat-03 |
| 优先级 | P0 |
| 目标版本 | OpenHarmony API Version 20 |
| SIG 归属 | GenUI SIG |
| 状态 | Baselined |
| 复杂度 | 复杂 |

## 本次变更范围（Delta）

| 类型 | 内容 | 说明 |
|------|------|------|
| ADDED | 无（存量补录） | 本特性承接 Feat-01 断点基线，固化 If 条件组件与断点触发的分支重渲染 |

## 输入文档

| 文档 | 路径 | 状态 |
|------|------|------|
| Design | `07-frontend/04-generative-ui/23-multi-device-adaptation/design.md` | Baselined |
| If 组件（C++） | `genui/src/main/cpp/components/extended/if/IfComponent.cpp`、`IfComponent.h` | — |
| If 注册（C++） | `genui/src/main/cpp/components/extended/ExtendedComponentFactory.cpp` | — |
| 全局变量解析（C++） | `genui/src/main/cpp/expression/EvaluationContext.cpp`、`expression/ThemeContextUtils.h` | — |
| 绑定通知（C++） | `genui/src/main/cpp/data/BindingEngine.cpp` | — |
| 断点传播（C++） | `genui/src/main/cpp/SurfaceManager.cpp` | — |
| 概念参考（Docs） | `concepts/multi-device-adaptation.md` | 理解辅助 |

> 需求基线、不涉及项详见 proposal.md。design.md 与本文档并行产出，互不依赖。

---

## 用户故事

### US-1: If 组件定义与属性解析

**作为** 生成式 UI 宿主开发者,
**我想要** 用 If 组件声明条件分支,
**以便** 根据表达式动态显示/隐藏 UI 分支。

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-1.1 | WHEN 组件类型为 `"If"` THEN 注册到 `IfComponent`（`ExtendedComponentFactory.cpp:126`） | 正常 |
| AC-1.2 | WHEN descriptor 含 `condition`（字符串） THEN 记录 `conditionExpression_`（`IfComponent.cpp:260-286`） | 正常 |
| AC-1.3 | WHEN `condition` 为 number THEN 经 `NumberToConditionExpression` 转换并打 TYPE_MISMATCH 警告（`IfComponent.cpp:269-272`） | 边界 |
| AC-1.4 | WHEN `condition` 缺失 THEN 打 REQUIRED_MISS 警告并回落到 childrenElse（`IfComponent.cpp:282-285`） | 异常 |
| AC-1.5 | WHEN `childrenIf`/`childrenElse` 非法（非字符串数组） THEN `ParseStringArray` 回退空数组（`IfComponent.cpp:437-462`） | 异常 |
| AC-1.6 | WHEN 初始化 THEN `EvaluateCondition(initial=true)`+`SyncConditionExpressionBinding`+`SelectBranch` 且 `initialized_=true`（`IfComponent.cpp:295-299`） | 正常 |
| AC-1.7 | WHEN `condition` 属性声明 THEN `PropertyDeclaration` 为 BOOLEAN/allowDynamic/allowExpression/fallbackBool=false（`IfComponent.cpp:312-322`） | 正常 |

### US-2: 条件表达式求值

**作为** 生成式 UI 宿主开发者,
**我想要** If 组件正确求值 condition 表达式,
**以便** true 渲染 childrenIf、false 渲染 childrenElse。

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-2.1 | WHEN condition 表达式求值为 true THEN `EvaluateConditionWithExpressionEngine` 返回 `AsBool()=true`（`IfComponent.cpp:509-510`） | 正常 |
| AC-2.2 | WHEN 表达式求值返回 undefined THEN 返回 false 保持现状（`IfComponent.cpp:491-497`） | 边界 |
| AC-2.3 | WHEN 结果 deferred（等数据可用） THEN 返回 false 保持现状（`IfComponent.cpp:498-504`） | 边界 |
| AC-2.4 | WHEN 结果为非法 falsy 非布尔（空串/0/NaN/null） THEN 打 INVALID_VALUE 警告并回落到 childrenElse（`IfComponent.cpp:505-508` + `ShouldReportInvalidFalsyConditionResult:163-175`） | 异常 |
| AC-2.5 | WHEN condition 表达式为空 THEN `EvaluateCondition` 直接返回 false（`IfComponent.cpp:518-519`） | 边界 |
| AC-2.6 | WHEN 表达式引擎未启用（`ENABLE_EXPRESSION_ENGINE` 未定义） THEN 打 warn 并落回 childrenElse（`IfComponent.cpp:524-531`） | 异常 |

### US-3: 依赖收集与绑定

**作为** 渲染引擎开发者,
**我想要** If 组件注册 condition 依赖（含 `__widthBreakpoint`）,
**以便** 依赖变化时精准重求值。

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-3.1 | WHEN condition 表达式含 `$__widthBreakpoint` THEN `CollectConditionDependencies` 收集到该变量（`IfComponent.cpp:51-62`） | 正常 |
| AC-3.2 | WHEN `SyncConditionExpressionBinding` 执行 THEN 按依赖为 `condition` 建立 DataBinding（`IfComponent.cpp:535-567`） | 正常 |
| AC-3.3 | WHEN 依赖依赖 `__dataModel.<path>` THEN 额外记录 dataPath（`IfComponent.cpp:548-565`） | 正常 |
| AC-3.4 | WHEN 依赖为空 THEN `SyncConditionExpressionBinding` 不建立绑定直接返回（`IfComponent.cpp:554-556`） | 边界 |
| AC-3.5 | WHEN `InjectGlobalVariables` 执行且 themeContext 有效 THEN 注入 ThemeContext（`IfComponent.cpp:569-593`） | 正常 |

### US-4: 断点变化重求值与分支切换

**作为** 宿主开发者,
**我想要** 断点档位变化自动切换 If 分支,
**以便** 实现响应式布局。

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-4.1 | WHEN 断点传播触发 `NotifyGlobalExpressionVariableChanged("__widthBreakpoint")` THEN 经 `BindingEngine::NotifyGlobalVariableChanged` 重求值依赖组件（`SurfaceManager.cpp:323`、`BindingEngine.cpp:445-482`） | 正常 |
| AC-4.2 | WHEN `IfComponent::OnConfigChange` 且 `initialized_` 且 condition 非空 THEN 调 `ReevaluateAndSwitch`（`IfComponent.cpp:332-339`） | 正常 |
| AC-4.3 | WHEN `IfComponent::OnDataUpdate("condition")` THEN 调 `ReevaluateAndSwitch`（`IfComponent.cpp:344-349`） | 正常 |
| AC-4.4 | WHEN `ReevaluateAndSwitch` 求值失败且已初始化 THEN 保持当前分支（`IfComponent.cpp:421-422`） | 恢复 |
| AC-4.5 | WHEN `ReevaluateAndSwitch` 结果与当前分支相同 THEN 不切换（`IfComponent.cpp:424-425`） | 边界 |
| AC-4.6 | WHEN 结果变化 THEN `SelectBranch` 在 `childrenIfIds_`/`childrenElseIds_` 间切换并 `ReconcileBranchChildren`（`IfComponent.cpp:427-433,595-607,653-657`） | 正常 |
| AC-4.7 | WHEN 分支引用的子组件 id 未定义 THEN 打 UNDEFINED_FIELD 警告并跳过（`IfComponent.cpp:638-651`） | 异常 |

### US-5: 全局变量落回

**作为** 宿主开发者,
**我想要** `__widthBreakpoint` 无 themeContext 时有稳定默认值,
**以便** 避免表达式求值异常。

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-5.1 | WHEN `__widthBreakpoint` 且 themeContext 为 null THEN 返回 `"sm"`（`EvaluationContext.cpp:32`） | 边界 |
| AC-5.2 | WHEN `__colorMode` 且 themeContext 为 null THEN 返回 `"light"`（`EvaluationContext.cpp:38`） | 边界 |
| AC-5.3 | WHEN `__dataModel` 且数据模型缺失 THEN 返回空串（`EvaluationContext.cpp:47`） | 边界 |
| AC-5.4 | WHEN 引用未定义的 `__` 前缀全局变量 THEN 设置 `EVAL_NO_GLOBAL_VARIABLE` 错误并返回空串（`EvaluationContext.cpp:50-57`） | 异常 |

## 验收追溯

| AC编号 | 关联规则 | 关联 Task | 验证方式 | 证据 |
|----|---------|----------|---------|------|
| AC-1.1,AC-1.2,AC-1.3,AC-1.4,AC-1.5,AC-1.6,AC-1.7 | R-1,R-2 | T-3 | C++ UT：If 属性解析 | `IfComponent.cpp:254-322,437-462` |
| AC-2.1,AC-2.2,AC-2.3,AC-2.4,AC-2.5,AC-2.6 | R-3,R-4 | T-3 | C++ UT：表达式求值 | `IfComponent.cpp:163-175,482-533` |
| AC-3.1,AC-3.2,AC-3.3,AC-3.4,AC-3.5 | R-5 | T-3 | C++ UT：依赖收集与绑定 | `IfComponent.cpp:51-62,535-593` |
| AC-4.1,AC-4.2,AC-4.3,AC-4.4,AC-4.5,AC-4.6,AC-4.7 | R-6,R-7,R-8 | T-3 | C++ UT：断点重求值与分支切换 | `BindingEngine.cpp:445-482`、`IfComponent.cpp:332-369,417-435,595-657` |
| AC-5.1,AC-5.2,AC-5.3,AC-5.4 | R-9 | T-3 | C++ UT：全局变量落回 | `EvaluationContext.cpp:26-57` |

## 规则定义

| 规则ID | 类型 | 触发条件 | 预期行为 | 边界/约束 | 关联AC |
|--------|------|---------|---------|----------|--------|
| R-1 | 行为 | descriptor 含 condition | 记录 conditionExpression_ 并分支初始化 | 空 condition 回落 childrenElse | AC-1.2,AC-1.3,AC-1.4,AC-1.5,AC-1.6 |
| R-2 | 异常 | condition 缺失/非字符串数字 | 警告并回落 childrenElse | — | AC-1.3,AC-1.4 |
| R-3 | 行为 | 表达式求值 | true→childrenIf、false→childrenElse | undefined/deferred 保持现状 | AC-2.1,AC-2.2,AC-2.3 |
| R-4 | 异常 | 非法 falsy 结果/引擎未启用 | 警告并回落 childrenElse | 空串/0/NaN/null | AC-2.4,AC-2.5,AC-2.6 |
| R-5 | 行为 | 依赖收集 | 按 `__widthBreakpoint`/`__dataModel` 注册绑定 | 空依赖不建绑定 | AC-3.1,AC-3.2,AC-3.3,AC-3.4 |
| R-6 | 行为 | 断点变化 | 双通道（OnConfigChange + OnDataUpdate）触发 ReevaluateAndSwitch | 仅依赖组件重求值 | AC-4.1,AC-4.2,AC-4.3 |
| R-7 | 恢复 | 求值失败 | 保持当前分支 | 仅已初始化时 | AC-4.4 |
| R-8 | 边界 | 分支未变化 | 不切换 | 无多余重建 | AC-4.5,AC-4.6 |
| R-9 | 边界 | 全局变量 themeContext 缺失 | `__widthBreakpoint`→sm、`__colorMode`→light、`__dataModel`→空 | — | AC-5.1,AC-5.2,AC-5.3,AC-5.4 |

## 验证映射

| 编号 | 对应规格项 | 验证方式 | 验证重点 |
|------|----------|---------|---------|
| VM-1 | AC-1.1,AC-1.2,AC-1.3,AC-1.4,AC-1.5,AC-1.6,AC-1.7 If 属性解析 | C++ UT | condition/childrenIf/childrenElse 解析与回落 |
| VM-2 | AC-2.1,AC-2.2,AC-2.3,AC-2.4,AC-2.5,AC-2.6 表达式求值 | C++ UT | true/false/undefined/deferred/非法 |
| VM-3 | AC-3.1,AC-3.2,AC-3.3,AC-3.4,AC-3.5 依赖绑定 | C++ UT | `__widthBreakpoint` 依赖收集 |
| VM-4 | AC-4.1,AC-4.2,AC-4.3,AC-4.4,AC-4.5,AC-4.6,AC-4.7 断点重求值 | C++ UT | 双通道 + 分支切换 |
| VM-5 | AC-5.1,AC-5.2,AC-5.3,AC-5.4 全局变量落回 | C++ UT | themeContext 缺省回落 |

## API 变更分析

> 存量补录，无新增/变更公开 API。If 组件为鸿蒙扩展协议组件，经 Catalog 注册，无 SDL 独立公开接口。

### 新增 API

N/A。

### 变更/废弃 API

| API 名称 | 变更类型 | 影响场景 | 迁移指引 | 关联 AC |
|----------|---------|---------|---------|--------|
| `If` 组件（扩展协议组件） | 既有 | 条件渲染 | `condition`/`childrenIf`/`childrenElse` 属性契约 | AC-1.1,AC-1.2,AC-1.3,AC-1.4,AC-1.5,AC-1.6,AC-1.7 |
| `$__widthBreakpoint`（全局变量） | 既有 | 表达式断点引用 | 字符串档位 xs..xl | AC-3.1,AC-5.1 |

> d.ts 位置：不适用（扩展协议组件，非 ArkTS 公开接口）。Kit：`@arkui-genius/genui`；权限：无。

## 接口规格

### 接口定义

**`IfComponent::ApplyComponentSpecificAttributes(descriptor)`（`IfComponent.cpp:254`）**

| 属性 | 值 |
|------|-----|
| 函数签名 | `void ApplyComponentSpecificAttributes(const JsonValue& normalizedDescriptor) override` |
| 返回值 | `void` |
| 开放范围 | 内部（C++） |
| 错误码 | N/A（schema warning） |
| 关联 AC | AC-1.2,AC-1.3,AC-1.4,AC-1.5,AC-1.6 |

**`IfComponent::ReevaluateAndSwitch()`（`IfComponent.cpp:417`）**

| 属性 | 值 |
|------|-----|
| 函数签名 | `bool ReevaluateAndSwitch()` |
| 返回值 | `bool` — 求值后的分支结果 |
| 开放范围 | 内部（C++） |
| 错误码 | N/A |
| 关联 AC | AC-4.4,AC-4.5,AC-4.6 |

**`BindingEngine::NotifyGlobalVariableChanged(varName)`（`BindingEngine.cpp:445`）**

| 属性 | 值 |
|------|-----|
| 函数签名 | `void NotifyGlobalVariableChanged(const std::string& varName)` |
| 返回值 | `void` |
| 开放范围 | 内部（C++） |
| 错误码 | N/A |
| 关联 AC | AC-4.1 |

**参数约束**

| 参数 | 类型 | 必填 | 默认值 | 约束条件 |
|------|------|------|--------|---------|
| condition | string（或 number 强制转换） | 是 | 缺失回落 childrenElse | 空串回落 childrenElse |
| childrenIf/childrenElse | string[] | 否 | 空数组 | 非字符串元素跳过 |
| varName | string | 是 | — | `__widthBreakpoint`/`__colorMode` |

**行为场景**

| # | 触发条件 | 预期行为 | 关联 AC |
|---|----------|----------|---------|
| 1 | condition=`"true"` 表达式 | 渲染 childrenIf | AC-2.1 |
| 2 | condition 缺失 | 回落 childrenElse | AC-1.4 |
| 3 | 断点变档 | 依赖 `__widthBreakpoint` 重求值切分支 | AC-4.1 |
| 4 | 求值结果与当前相同 | 不切换 | AC-4.5 |
| 5 | 分支子组件 id 未定义 | 打警告跳过 | AC-4.7 |

## 兼容性声明

- **已有 API 行为变更:** 否（存量补录）。
- **配置文件格式变更:** 否。
- **数据存储格式变更:** 否。
- **最低支持版本:** OpenHarmony API Version 20（If 组件为鸿蒙扩展协议新增组件）。
- **API 版本号策略:** If 组件经 `ohos.a2ui.extended.catalog` 提供，无独立 `@since` 标注。

## 架构约束

| 关键约束 | 约束说明 | 影响 AC |
|---------|---------|--------|
| 双通道重求值 | 断点变化同时走主题 OnConfigChange 与 `__widthBreakpoint` 通知 | AC-4.1,AC-4.2,AC-4.3 |
| 表达式引擎门控 | `NotifyGlobalVariableChanged` 仅在 `ENABLE_EXPRESSION_ENGINE` 下生效 | AC-2.6 |
| 无变化不重建 | 分支未变化短路，避免多余子树重建 | AC-4.5 |

## 非功能性需求

| 类型 | 指标/阈值 | 验证方式 | 证据 |
|------|----------|---------|------|
| 可靠性 | 依赖未定义/求值失败不崩溃，回落或保持分支 | C++ UT | `IfComponent.cpp:491-504,638-651` |
| 性能 | 分支无变化短路，避免重建 | C++ UT | `IfComponent.cpp:424-425` |

## 多设备适配声明

| 设备类型 | 行为差异 | 规格/约束 | 验证方式 | 证据 |
|---------|---------|----------|---------|------|
| 手机 | 竖屏 sm/md 触发窄屏分支 | 无差异 | ohosTest | `IfComponent.cpp:417-435` |
| 平板 | md/lg 触发宽屏分支 | 无差异 | ohosTest | 同上 |
| 折叠屏 | 展开/折叠动态切分支 | 断点变化驱动 | ohosTest | `BindingEngine.cpp:445-482` |

## 全局特性影响

| 特性 | 适用？ | 结论 | 关联场景 |
|------|-------|------|---------|
| 无障碍 | 否 | 条件分支不涉及 | — |
| 大字体 | 否 | 字体见 Feat-02 | — |
| 深色模式 | 是 | `__colorMode` 同构重求值（`SurfaceManager::UpdateThemeMode`） | AC-5.2 |
| 多窗口/分屏 | 是 | 断点变化触发分支切换 | AC-4.1 |
| 多用户 | 否 | 无差异 | — |
| 版本升级 | 是 | API 20 起 | 兼容性 |
| 生态兼容 | 是 | 扩展协议 If 组件 | 概述 |

## 行为场景（可选，Gherkin）

```gherkin
Feature: 条件组件与断点重渲染
  作为 宿主开发者
  我想要 断点变化自动切换 If 分支
  以便 实现响应式布局

  Scenario: 断点切换分支
    Given If 组件 condition="{{ $__widthBreakpoint == 'xl' }}"
    And 当前分支为 childrenElse（非 xl）
    When 容器宽度变化触发断点由 lg 变为 xl
    Then ReevaluateAndSwitch 求值为 true 并切换到 childrenIf

  Scenario: 求值失败保持分支
    Given If 组件已初始化且当前分支为 childrenIf
    When 断点变化导致表达式求值失败
    Then 保持 childrenIf 分支不切换

  Scenario Outline: 全局变量落回
    Given themeContext 缺失
    When 解析 <变量>
    Then 返回 <默认值>

    Examples:
      | 变量              | 默认值 |
      | __widthBreakpoint | sm     |
      | __colorMode       | light  |
      | __dataModel       | ""     |
```

## Spec 自审清单

- [x] 无"待定""TBD""TODO"等占位符
- [x] 所有 AC 使用 WHEN/THEN 格式，可独立测试
- [x] 范围边界明确（Feat-03 做 If 组件与断点重渲染；断点定义见 Feat-01，单位见 Feat-02）
- [x] 无语义模糊表述
- [x] AC 与规则表交叉一致
- [x] 规则表每条通过 5 项质量检查（可复现/可观测/边界值/关联AC/无冲突）

## context-references

```yaml
context-queries:
  - repo: "GenerativeUI/A2UIRender"
    query: "IfComponent condition childrenIf childrenElse ApplyComponentSpecificAttributes SelectBranch"
  - repo: "GenerativeUI/A2UIRender"
    query: "IfComponent ReevaluateAndSwitch EvaluateConditionWithExpressionEngine OnConfigChange OnDataUpdate"
  - repo: "GenerativeUI/A2UIRender"
    query: "IfComponent SyncConditionExpressionBinding CollectConditionDependencies InjectGlobalVariables __widthBreakpoint"
  - repo: "GenerativeUI/A2UIRender"
    query: "BindingEngine NotifyGlobalVariableChanged globalVarBindingIndex ENABLE_EXPRESSION_ENGINE"
  - repo: "GenerativeUI/A2UIRender"
    query: "EvaluationContext ResolveVariable __widthBreakpoint __colorMode __dataModel 回落"
```

**关键文档：** `genui/src/main/cpp/components/extended/if/IfComponent.cpp`、`genui/src/main/cpp/expression/EvaluationContext.cpp`、`genui/src/main/cpp/data/BindingEngine.cpp`、`genui/src/main/cpp/SurfaceManager.cpp`、`genui/src/main/cpp/components/extended/ExtendedComponentFactory.cpp`