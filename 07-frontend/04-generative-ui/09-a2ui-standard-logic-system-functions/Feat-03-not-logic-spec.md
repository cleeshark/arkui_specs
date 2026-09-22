# 特性规格

> Func-07-04-09-Feat-03 `not` 函数：固化 A2UI 标准协议逻辑非运算函数的契约。`not` 为原生内置函数（`isInnerNative: true`），在 C++ `NativeFunctionRegistry` 中执行，对单个 `value` 布尔值取反：true→false，false→true。与 `and`/`or` 不同，`not` 对非布尔/缺省入参采用「回退 true」策略。入参约束 `value` 为 DynamicBoolean（schema），返回类型 `boolean`。基准实现：`@arkui-genius/genui`（A2UIRender）。

## 概述

| 属性 | 值 |
|------|-----|
| 特性名称 | not 逻辑非函数 |
| 特性编号 | Func-07-04-09-Feat-03 |
| 优先级 | P0 |
| 目标版本 | A2UI 原生协议 v0.9 |
| SIG 归属 | GenUI SIG |
| 状态 | Baselined |
| 复杂度 | 标准 |

## 本次变更范围（Delta）

| 类型 | 内容 | 说明 |
|------|------|------|
| ADDED | 无（存量补录） | 本特性为 Func-07-04-09 第三个 Feat |

## 输入文档

| 文档 | 路径 | 状态 |
|------|------|------|
| Design | `07-frontend/04-generative-ui/09-a2ui-standard-logic-system-functions/design.md` | Baselined |
| 函数声明（ArkTS） | `genui/src/main/ets/core/functions/logic/NotFunction.ets` | — |
| 原生实现（C++） | `genui/src/main/cpp/functions/impl/NativeNotFunction.cpp` | — |
| 原生注册（C++） | `genui/src/main/cpp/functions/NativeFunctionRegistry.cpp` | — |
| Schema | `genui/src/main/resources/rawfile/schema/A2UI/v0.9/functions/not.json` | — |
| 逻辑函数参考（Docs） | `reference/functions/logic.md` | 理解辅助 |

> 需求基线、不涉及项详见 proposal.md。design.md 与本文档并行产出，互不依赖。

---

## 用户故事

### US-1: not 函数声明与注册

**作为** 生成式 UI 宿主开发者,
**我想要** 引擎把 `not` 注册为原生内置逻辑函数,
**以便** DSL 中以 `{ "call": "not", ... }` 触发逻辑非求值。

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-1.1 | WHEN 实例化 `notFunction` THEN `asFunctionItem()` 返回 `{ name:'not', isInnerNative:true, functionCall:undefined }`（`NotFunction.ets:25-32`） | 正常 |
| AC-1.2 | WHEN 汇总标准内置函数 THEN `notFunction` 位于 `standardBuiltinFunctions` 数组（`A2UIBasicFunctions.ets:60`） | 正常 |
| AC-1.3 | WHEN 初始化 native 注册表 THEN `Register("not", NativeNotFunction)` 完成（`NativeFunctionRegistry.cpp:80`） | 正常 |
| AC-1.4 | WHEN 查询函数名 THEN `NativeNotFunction::GetName()` 返回 `"not"`（`NativeNotFunction.cpp:20-23`） | 正常 |

### US-2: 逻辑非语义（取反）

**作为** 生成式 UI 宿主开发者,
**我想要** `not` 对布尔值取反,
**以便** 表达反向条件（如 isSubmitting 为 false 时按钮可用）。

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-2.1 | WHEN `value=true` THEN 返回 false（`NativeNotFunction.cpp:36`） | 正常 |
| AC-2.2 | WHEN `value=false` THEN 返回 true（`NativeNotFunction.cpp:36`） | 正常 |

### US-3: 非布尔/缺省入参回退

**作为** 生成式 UI 宿主开发者,
**我想要** `not` 对非布尔或缺失入参有确定性回退,
**以便** 结构异常时得到稳定结果。

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-3.1 | WHEN `resolvedArgs` 非对象 THEN 返回 true（`NativeNotFunction.cpp:27-29`） | 异常 |
| AC-3.2 | WHEN `value` 非布尔（运行时路径解析为非布尔）THEN 返回 true（`NativeNotFunction.cpp:31-34`） | 边界 |
| AC-3.3 | WHEN `value` 缺失（`GetItem("value")` 非法）THEN 返回 true（`NativeNotFunction.cpp:31-34`） | 边界 |

### US-4: schema 约束

**作为** 生成式 UI 宿主开发者,
**我想要** `not` 的 DSL 结构受 schema 校验,
**以便** 非法 FunctionCall 在解析期被拦截。

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-4.1 | WHEN `args.value` 缺失 THEN schema 校验失败（`not.json` `required:["value"]`） | 异常 |
| AC-4.2 | WHEN `returnType` 非 `"boolean"` THEN schema 校验失败（`not.json` `returnType: { const:"boolean" }`） | 异常 |

## 验收追溯

| AC编号 | 关联规则 | 关联 Task | 验证方式 | 证据 |
|----|---------|----------|---------|------|
| AC-1.1,AC-1.2,AC-1.3,AC-1.4 | R-1 | T-3 | 静态比对：ArkTS `asFunctionItem` vs C++ `Register` | `NotFunction.ets:25-32`、`NativeFunctionRegistry.cpp:80` |
| AC-2.1,AC-2.2 | R-2 | T-3 | C++ UT：true/false 取反 | `NativeNotFunction.cpp:36` |
| AC-3.1,AC-3.2,AC-3.3 | R-3 | T-3 | C++ UT：非对象/非布尔/缺省回退 true | `NativeNotFunction.cpp:27-34` |
| AC-4.1,AC-4.2 | R-4 | T-3 | 静态比对：`not.json` | `not.json` |

## 规则定义

| 规则ID | 类型 | 触发条件 | 预期行为 | 边界/约束 | 关联AC |
|--------|------|---------|---------|----------|--------|
| R-1 | 行为 | `not` 作为 FunctionCall 被解析 | 经 `NativeFunctionRegistry` 执行 `NativeNotFunction` | `isInnerNative:true`，functionCall 未定义 | AC-1.1,AC-1.2,AC-1.3,AC-1.4 |
| R-2 | 行为 | `value` 为布尔 | 返回 `!value` | true→false，false→true | AC-2.1,AC-2.2 |
| R-3 | 边界 | `resolvedArgs` 非对象或 `value` 非布尔/缺失 | 返回 true | 与 schema 要求 value 必填存在落差 | AC-3.1,AC-3.2,AC-3.3 |
| R-4 | 异常 | schema 校验（value 结构/returnType） | 解析期拒绝 FunctionCall | returnType 仅 boolean | AC-4.1,AC-4.2 |

## 验证映射

| 编号 | 对应规格项 | 验证方式 | 验证重点 |
|------|----------|---------|---------|
| VM-1 | AC-1.1,AC-1.2,AC-1.3,AC-1.4 声明与注册 | 静态比对 | name/isInnerNative/Register 一致性 |
| VM-2 | AC-2.1,AC-2.2 取反 | C++ UT | !value |
| VM-3 | AC-3.1,AC-3.2,AC-3.3 回退 true | C++ UT | 非对象/非布尔/缺省 |
| VM-4 | AC-4.1,AC-4.2 schema | 静态比对 | not.json 结构约束 |

## API 变更分析

> 存量补录，无新增/变更 Public API。`not` 为内部内置函数（`InnerFunctionItem`）。

### 新增 API

N/A。

### 变更/废弃 API

| API 名称 | 变更类型 | 影响场景 | 迁移指引 | 关联 AC |
|----------|---------|---------|---------|--------|
| 内置函数 `not` | 既有 | DSL 逻辑非求值（反向条件） | 不直接暴露为宿主 API，经 DSL FunctionCall 调用 | AC-1.1 |

> 契约位置：`genui/src/main/ets/core/functions/logic/NotFunction.ets`；执行 `NativeNotFunction.cpp`。Kit：`@arkui-genius/genui`；权限：无。

## 接口规格

### 接口定义

**`not`（FunctionCall 契约，`returnType: "boolean"`）**

| 属性 | 值 |
|------|-----|
| 函数签名 | `FunctionResult NativeNotFunction::Execute(const JsonValue& resolvedArgs)` |
| 返回值 | `boolean` — `!value`；非布尔/缺省/非对象回退 true |
| 开放范围 | InnerApi（内置函数，DSL FunctionCall 触发） |
| 错误码 | N/A（逻辑函数始终返回 boolean，不产生错误码） |
| 关联 AC | AC-1.1,AC-1.2,AC-1.3,AC-1.4,AC-2.1,AC-2.2,AC-3.1,AC-3.2,AC-3.3 |

**参数约束**

| 参数 | 类型 | 必填 | 默认值 | 约束条件 |
|------|------|------|--------|---------|
| value | boolean | 是 | — | DynamicBoolean；可为字面量/路径绑定/嵌套函数调用 |

**行为场景**

| # | 触发条件 | 预期行为 | 关联 AC |
|---|----------|----------|---------|
| 1 | value=true | 返回 false | AC-2.1 |
| 2 | value=false | 返回 true | AC-2.2 |
| 3 | resolvedArgs 非对象 | 返回 true | AC-3.1 |
| 4 | value 非布尔/缺失 | 返回 true | AC-3.2,AC-3.3 |

## 兼容性声明

- **已有 API 行为变更:** 否（存量补录）。
- **配置文件格式变更:** 否。
- **数据存储格式变更:** 否。
- **最低支持版本:** A2UI 原生协议 v0.9。
- **API 版本号策略:** 函数语义由 schema（`not.json`）与 `NativeNotFunction` 共同固化；逻辑函数无 @since 标注需求。

## 架构约束

| 关键约束 | 约束说明 | 影响 AC |
|---------|---------|--------|
| 原生内置 | `isInnerNative:true`，在 C++ 执行，避免跨语言往返 | AC-1.1,AC-1.2,AC-1.3,AC-1.4 |
| 非布尔回退 true | `not` 对非布尔/缺省入参回退 true（区别于 `and`/`or`） | AC-3.1,AC-3.2,AC-3.3 |
| 返回类型约束 | schema 强制 `returnType: "boolean"` | AC-4.2 |

## 非功能性需求

| 类型 | 指标/阈值 | 验证方式 | 证据 |
|------|----------|---------|------|
| 可靠性 | 非法入参不抛异常，统一回退 true | C++ UT | `NativeNotFunction.cpp:27-34` |
| 性能 | O(1) 取反 | C++ UT | `NativeNotFunction.cpp:36` |

## 多设备适配声明

| 设备类型 | 行为差异 | 规格/约束 | 验证方式 | 证据 |
|---------|---------|----------|---------|------|
| 手机 | 无差异 | 逻辑求值与设备无关 | C++ UT | — |
| 平板 | 无差异 | 同上 | C++ UT | — |
| 折叠屏 | 无差异 | 同上 | C++ UT | — |

## 全局特性影响

| 特性 | 适用？ | 结论 | 关联场景 |
|------|-------|------|---------|
| 无障碍 | 否 | 逻辑函数不涉及 | — |
| 大字体 | 否 | 不涉及 | — |
| 深色模式 | 否 | 不涉及 | — |
| 多窗口/分屏 | 否 | 不涉及 | — |
| 多用户 | 否 | 无差异 | — |
| 版本升级 | 是 | 函数语义随协议 v0.9 固化 | AC-4.1,AC-4.2 |
| 生态兼容 | 是 | A2UI 原生协议 v0.9 逻辑函数 | 概述「目标版本」 |

## 行为场景（可选，Gherkin）

```gherkin
Feature: not 逻辑非函数
  作为 生成式 UI 宿主开发者
  我想要 not 对布尔值取反
  以便 表达反向条件

  Scenario: 布尔取反
    Given DSL 片段为 {"call":"not","args":{"value":{"path":"form.isSubmitting"}},"returnType":"boolean"}
    When 引擎解析路径后执行 not
    Then 返回 value 的取反值

  Scenario Outline: 取反与回退
    Given value 为 <value>
    When 执行 NativeNotFunction::Execute
    Then 返回 <result>

    Examples:
      | value | result |
      | true | false |
      | false | true |
```

## Spec 自审清单

- [x] 无"待定""TBD""TODO"等占位符
- [x] 所有 AC 使用 WHEN/THEN 格式，可独立测试
- [x] 范围边界明确（Feat-03 只覆盖 `not`；`and`/`or`/`openUrl` 归 Feat-01/02/04）
- [x] 无语义模糊表述
- [x] AC 与规则表交叉一致
- [x] 规则表每条通过 5 项质量检查（可复现/可观测/边界值/关联AC/无冲突）

## context-references

```yaml
context-queries:
  - repo: "GenerativeUI/A2UIRender"
    query: "NativeNotFunction Execute 逻辑非 取反 非布尔回退 true"
  - repo: "GenerativeUI/A2UIRender"
    query: "not.json schema value DynamicBoolean returnType boolean"
  - repo: "GenerativeUI/A2UIRender"
    query: "not 与 and or 非布尔回退策略差异 NativeFunctionRegistry 注册"
```

**关键文档：** `genui/src/main/ets/core/functions/logic/NotFunction.ets`、`genui/src/main/cpp/functions/impl/NativeNotFunction.cpp`、`genui/src/main/cpp/functions/NativeFunctionRegistry.cpp`、`genui/src/main/resources/rawfile/schema/A2UI/v0.9/functions/not.json`