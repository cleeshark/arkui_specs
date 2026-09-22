# 特性规格

> Func-07-04-21-Feat-04 变量系统：固化鸿蒙扩展协议的变量体系——全局系统变量（`$__widthBreakpoint`、`$__colorMode`）、DataModel 全局变量（`$__dataModel.*` / `${/path}`）、局部变量（循环变量 `$index`/`$item` 与自定义 `indexVar`/`itemVar`、事件链 `as` 变量、事件上下文 `$context`）、`__*` 命名空间边界、以及 `ResolveVariable` 分层解析优先级与全局变量失效刷新。基准实现：`@arkui-genius/genui`（A2UIRender）。

## 概述

| 属性 | 值 |
|------|-----|
| 特性名称 | 变量系统 |
| 特性编号 | Func-07-04-21-Feat-04 |
| 优先级 | P0 |
| 目标版本 | 鸿蒙扩展协议 1.0.0（起始 API Version 20） |
| SIG 归属 | GenUI SIG |
| 状态 | Baselined |
| 复杂度 | 复杂 |

## 本次变更范围（Delta）

| 类型 | 内容 | 说明 |
|------|------|------|
| ADDED | 无（存量补录） | Feat-04 承接 design.md 变量系统章节 |

## 输入文档

| 文档 | 路径 | 状态 |
|------|------|------|
| Design | `07-frontend/04-generative-ui/21-dynamic-data-binding/design.md` | Baselined |
| 求值上下文 | `genui/src/main/cpp/expression/EvaluationContext.cpp` / `.h` | — |
| 主题上下文 | `genui/src/main/cpp/expression/ThemeContextUtils.h` | — |
| 绑定引擎 | `genui/src/main/cpp/data/BindingEngine.cpp` / `.h` | — |
| 依赖收集 | `genui/src/main/cpp/expression/DependencyCollector.cpp` / `.h` | — |
| 变量系统（Docs） | `concepts/variable-system.md` | 理解辅助 |

> 需求基线、不涉及项详见 proposal.md。design.md 与本文档并行产出，互不依赖。

---

## 用户故事

### US-1: 全局系统变量

**作为** 生成式 UI 宿主开发者,
**我想要** 表达式引用断点与深浅色全局变量,
**以便** 实现响应式与深浅色适配。

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-1.1 | WHEN 表达式引用 `$__widthBreakpoint` THEN `ResolveVariable` 返回断点字符串（xs/sm/md/lg/xl）（`EvaluationContext.cpp:28-33`） | 正常 |
| AC-1.2 | WHEN 表达式引用 `$__colorMode` THEN 返回 `light`/`dark`（`EvaluationContext.cpp:34-39`） | 正常 |
| AC-1.3 | WHEN `themeContext_` 为空 THEN `$__widthBreakpoint` 默认 `"sm"`、`$__colorMode` 默认 `"light"`（`EvaluationContext.cpp:30-38`） | 边界 |
| AC-1.4 | WHEN 断点/深浅色映射 THEN `BreakpointToString`/`ColorModeToString` 生成小写字符串（`ThemeContextUtils.h:25-53`） | 正常 |

### US-2: DataModel 全局变量与命名空间

**作为** 生成式 UI 宿主开发者,
**我想要** 用 `$__dataModel.*` 与 `${/path}` 引用数据模型,
**以便** 表达式读取 DataModel 值。

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-2.1 | WHEN 表达式引用 `$__dataModel` THEN `ResolveVariable` 返回根 JSON 或序列化字符串（`EvaluationContext.cpp:40-48`） | 正常 |
| AC-2.2 | WHEN 引用 `$__unknownGlobal`（未注册的 `__*`）THEN 置 `EVAL_NO_GLOBAL_VARIABLE`（`EvaluationContext.cpp:50-57`） | 异常 |
| AC-2.3 | WHEN 局部变量名为 `__` 前缀 THEN `SetLocalVariable` 静默丢弃不覆盖全局（`EvaluationContext.h:71`） | 边界 |
| AC-2.4 | WHEN DataModel 变量通过依赖收集 THEN `DependencyCollector` 产生 `{variableName:"__dataModel", path}`（`DependencyCollector.cpp:37`） | 正常 |

### US-3: 局部变量与作用域

**作为** 生成式 UI 宿主开发者,
**我想要** 循环变量/事件链变量分层可见,
**以便** 模板内就近引用数据项。

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-3.1 | WHEN `ApplyLocalVariables` 注入局部变量 THEN `PushScope` + `SetLocalVariable` 建立作用域（`DynamicValueResolver.cpp:112-125`） | 正常 |
| AC-3.2 | WHEN 解析变量名 THEN 先查 `globalVariables_`，再反向遍历作用域栈（就近优先）（`EvaluationContext.cpp:59-69`） | 正常 |
| AC-3.3 | WHEN 变量不存在于任何作用域 THEN 返回 `Undefined`（`EvaluationContext.cpp:71`） | 边界 |
| AC-3.4 | WHEN 内层模板与外层同名变量 THEN 内层遮蔽外层（就近优先）（`variable-system.md:129`） | 正常 |

### US-4: 全局变量失效刷新

**作为** 生成式 UI 宿主开发者,
**我想要** 全局变量变化时刷新依赖组件,
**以便** 断点/深浅色切换即时生效。

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-4.1 | WHEN 组件依赖某全局变量 THEN `RegisterExpressionBindingPaths` 写入 `globalVarBindingIndex_`（`BindingEngine.cpp:349-354`） | 正常 |
| AC-4.2 | WHEN 全局变量变化 THEN `NotifyGlobalVariableChanged` 按 `globalVarDeps_` 匹配刷新表达式/函数属性（`BindingEngine.cpp:445-482`） | 正常 |
| AC-4.3 | WHEN 组件注销 THEN `UnregisterExpressionBindingPaths` 从索引移除（`BindingEngine.cpp:410-420`） | 正常 |
| AC-4.4 | WHEN `varName` 不在 `globalVarBindingIndex_` 中 THEN `NotifyGlobalVariableChanged` 直接返回（`BindingEngine.cpp:448-451`） | 边界 |

## 验收追溯

| AC编号 | 关联规则 | 关联 Task | 验证方式 | 证据 |
|----|---------|----------|---------|------|
| AC-1.1,AC-1.2,AC-1.3,AC-1.4 | R-1 | T-4 | UT：全局系统变量 | `EvaluationContext.cpp:28-39` |
| AC-2.1,AC-2.2,AC-2.3,AC-2.4 | R-2 | T-4 | UT：DataModel 变量/命名空间 | `EvaluationContext.cpp:40-57` |
| AC-3.1,AC-3.2,AC-3.3,AC-3.4 | R-3 | T-4 | UT：局部作用域 | `EvaluationContext.cpp:59-71` |
| AC-4.1,AC-4.2,AC-4.3,AC-4.4 | R-4 | T-4 | UT：失效刷新 | `BindingEngine.cpp:445-482` |

## 规则定义

| 规则ID | 类型 | 触发条件 | 预期行为 | 边界/约束 | 关联AC |
|--------|------|---------|---------|----------|--------|
| R-1 | 行为 | 引用 `$__widthBreakpoint`/`$__colorMode` | 返回断点/深浅色字符串 | themeContext 为空用默认 | AC-1.1,AC-1.2,AC-1.3,AC-1.4 |
| R-2 | 行为 | 引用 `$__dataModel` | 返回根/序列化值 | `__*` 未注册报错 | AC-2.1,AC-2.2,AC-2.3,AC-2.4 |
| R-3 | 行为 | 解析普通变量 | 全局→作用域栈→Undefined | 就近优先 | AC-3.1,AC-3.2,AC-3.3,AC-3.4 |
| R-4 | 行为 | 全局变量变化 | 按依赖索引刷新 | `__dataModel` 依赖走 bindingIndex_ | AC-4.1,AC-4.2,AC-4.3,AC-4.4 |

## 验证映射

| 编号 | 对应规格项 | 验证方式 | 验证重点 |
|------|----------|---------|---------|
| VM-1 | AC-1.1,AC-1.2,AC-1.3,AC-1.4 全局系统变量 | UT | 断点/深浅色默认值 |
| VM-2 | AC-2.1,AC-2.2,AC-2.3,AC-2.4 DataModel 变量 | UT | `__*` 命名空间 |
| VM-3 | AC-3.1,AC-3.2,AC-3.3,AC-3.4 局部作用域 | UT | 作用域栈就近 |
| VM-4 | AC-4.1,AC-4.2,AC-4.3,AC-4.4 失效刷新 | UT | 依赖索引匹配 |

## API 变更分析

> 存量补录，无新增/变更 API。

### 新增 API

N/A。

### 变更/废弃 API

N/A。

## 接口规格

### 接口定义

**`EvaluationContext::ResolveVariable(name)`（`EvaluationContext.cpp:26`）**

| 属性 | 值 |
|------|-----|
| 函数签名 | `EvalResult ResolveVariable(const std::string& name)` |
| 返回值 | `EvalResult` — 变量值或 `Undefined` |
| 开放范围 | 内部（C++） |
| 错误码 | 3203（`SURFACE_ERROR_GLOBAL_VARIABLE_NOT_FOUND`） |
| 关联 AC | AC-1.1,AC-1.2,AC-1.3,AC-2.1,AC-2.2,AC-3.2,AC-3.3 |

**`BindingEngine::NotifyGlobalVariableChanged(varName)`（`BindingEngine.cpp:445`）**

| 属性 | 值 |
|------|-----|
| 函数签名 | `void NotifyGlobalVariableChanged(const std::string& varName)` |
| 返回值 | `void` |
| 开放范围 | 内部（C++） |
| 关联 AC | AC-4.2,AC-4.4 |

**参数约束**

| 参数 | 类型 | 必填 | 默认值 | 约束条件 |
|------|------|------|--------|---------|
| name | string | 是 | — | `$` 前缀变量名 |
| varName | string | 是 | — | 全局变量名（如 `__widthBreakpoint`） |

**行为场景**

| # | 触发条件 | 预期行为 | 关联 AC |
|---|----------|----------|---------|
| 1 | 解析 `__widthBreakpoint` | 返回断点字符串 | AC-1.1 |
| 2 | 解析未注册 `__*` | `EVAL_NO_GLOBAL_VARIABLE` | AC-2.2 |
| 3 | 解析普通变量 | 全局→作用域栈→Undefined | AC-3.2,AC-3.3 |
| 4 | 全局变量变化 | 刷新依赖组件 | AC-4.2 |

## 兼容性声明

- **已有 API 行为变更:** 否（存量补录）。
- **配置文件格式变更:** 否。
- **数据存储格式变更:** 否。
- **最低支持版本:** 鸿蒙扩展协议 1.0.0（API Version 20）。
- **API 版本号策略:** 无新增 API。

## 架构约束

| 关键约束 | 约束说明 | 影响 AC |
|---------|---------|--------|
| 命名空间 | `__*` 全局命名空间不可被局部遮蔽 | AC-2.3 |
| 作用域栈 | 就近优先分层解析 | AC-3.2,AC-3.4 |
| 依赖索引 | globalVarBindingIndex_ 驱动失效刷新 | AC-4.1,AC-4.2,AC-4.3,AC-4.4 |

## 非功能性需求

| 类型 | 指标/阈值 | 验证方式 | 证据 |
|------|----------|---------|------|
| 可靠性 | 变量未定义不崩溃，返回 Undefined | UT | `EvaluationContext.cpp:71` |
| 性能 | 依赖索引 O(订阅数) 刷新 | UT | `BindingEngine.cpp:445-482` |

## 多设备适配声明

| 设备类型 | 行为差异 | 规格/约束 | 验证方式 | 证据 |
|---------|---------|----------|---------|------|
| 手机 | 无差异（断点值随窗口宽度变化） | xs/sm/md/lg/xl | ohosTest | `ThemeContextUtils.h:25-41` |
| 平板 | 无差异（断点常为 md/lg） | 同上 | ohosTest | 同上 |
| 折叠屏 | 无差异（断点随折叠状态变化） | 同上 | ohosTest | 同上 |

## 全局特性影响

| 特性 | 适用？ | 结论 | 关联场景 |
|------|-------|------|---------|
| 无障碍 | 否 | — | — |
| 大字体 | 否 | — | — |
| 深色模式 | 是 | `$__colorMode` 注入 light/dark | AC-1.2 |
| 多窗口/分屏 | 否 | — | — |
| 多用户 | 否 | — | — |
| 版本升级 | 否 | — | — |
| 生态兼容 | 部分是 | 变量系统为鸿蒙扩展协议专属 | AC-1.1,AC-1.2,AC-1.3,AC-1.4 |

## 行为场景（可选，Gherkin）

```gherkin
Feature: 变量系统
  作为 生成式 UI 宿主开发者
  我想要 分层引用全局/局部变量并随变化刷新
  以便 响应式与深浅色适配

  Scenario Outline: 变量解析
    Given 表达式引用 <变量>
    When 在 <上下文> 求值
    Then 解析为 <结果>

    Examples:
      | 变量 | 上下文 | 结果 |
      | $__widthBreakpoint | 窗口宽度 sm | "sm" |
      | $__colorMode | 深色模式 | "dark" |
      | $__dataModel.user.name | DataModel 含 /user/name | 该字段值 |
      | $item | 循环模板 | 当前项 |
```

## Spec 自审清单

- [x] 无"待定""TBD""TODO"等占位符
- [x] 所有 AC 使用 WHEN/THEN 格式，可独立测试
- [x] 范围边界明确（断点/深浅色阈值归 07-04-23/24）
- [x] 无语义模糊表述
- [x] AC 与规则表交叉一致
- [x] 规则表每条通过质量检查

## context-references

```yaml
context-queries:
  - repo: "GenerativeUI/A2UIRender"
    query: "EvaluationContext ResolveVariable __widthBreakpoint __colorMode __dataModel 作用域栈"
  - repo: "GenerativeUI/A2UIRender"
    query: "ThemeContextUtils BreakpointToString ColorModeToString 断点深浅色"
  - repo: "GenerativeUI/A2UIRender"
    query: "BindingEngine NotifyGlobalVariableChanged globalVarBindingIndex_ globalVarDeps_"
```

**关键文档：** `genui/src/main/cpp/expression/EvaluationContext.cpp`、`genui/src/main/cpp/expression/ThemeContextUtils.h`、`genui/src/main/cpp/data/BindingEngine.cpp`