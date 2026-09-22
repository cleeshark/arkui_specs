# 特性规格

> Func-07-04-09-Feat-01 `and` 函数：固化 A2UI 标准协议逻辑与运算函数的契约。`and` 为原生内置函数（`isInnerNative: true`），在 C++ `NativeFunctionRegistry` 中执行，对 `values` 布尔数组做逻辑与：全为 true 返回 true，任一为 false 即返回 false。入参约束 `values` 至少 2 项（schema `minItems: 2`），返回类型 `boolean`。基准实现：`@arkui-genius/genui`（A2UIRender）。

## 概述

| 属性 | 值 |
|------|-----|
| 特性名称 | and 逻辑与函数 |
| 特性编号 | Func-07-04-09-Feat-01 |
| 优先级 | P0 |
| 目标版本 | A2UI 原生协议 v0.9 |
| SIG 归属 | GenUI SIG |
| 状态 | Baselined |
| 复杂度 | 标准 |

## 本次变更范围（Delta）

| 类型 | 内容 | 说明 |
|------|------|------|
| ADDED | 无（存量补录） | 本特性为 Func-07-04-09 首个 Feat，作为该功能域 design.md 基线 |

## 输入文档

| 文档 | 路径 | 状态 |
|------|------|------|
| Design | `07-frontend/04-generative-ui/09-a2ui-standard-logic-system-functions/design.md` | Baselined |
| 函数声明（ArkTS） | `genui/src/main/ets/core/functions/logic/AndFunction.ets` | — |
| 原生实现（C++） | `genui/src/main/cpp/functions/impl/NativeAndFunction.cpp` | — |
| 原生注册（C++） | `genui/src/main/cpp/functions/NativeFunctionRegistry.cpp` | — |
| Schema | `genui/src/main/resources/rawfile/schema/A2UI/v0.9/functions/and.json` | — |
| 逻辑函数参考（Docs） | `reference/functions/logic.md` | 理解辅助 |

> 需求基线、不涉及项详见 proposal.md。design.md 与本文档并行产出，互不依赖。

---

## 用户故事

### US-1: and 函数声明与注册

**作为** 生成式 UI 宿主开发者,
**我想要** 引擎把 `and` 注册为原生内置逻辑函数,
**以便** DSL 中以 `{ "call": "and", ... }` 触发逻辑与求值。

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-1.1 | WHEN 实例化 `andFunction` THEN `asFunctionItem()` 返回 `{ name:'and', isInnerNative:true, functionCall:undefined }`（`AndFunction.ets:25-32`） | 正常 |
| AC-1.2 | WHEN 汇总标准内置函数 THEN `andFunction` 位于 `standardBuiltinFunctions` 数组（`A2UIBasicFunctions.ets:58`） | 正常 |
| AC-1.3 | WHEN 初始化 native 注册表 THEN `Register("and", NativeAndFunction)` 完成（`NativeFunctionRegistry.cpp:78`） | 正常 |
| AC-1.4 | WHEN 查询函数名 THEN `NativeAndFunction::GetName()` 返回 `"and"`（`NativeAndFunction.cpp:22-25`） | 正常 |

### US-2: 逻辑与语义（全 true 返回 true）

**作为** 生成式 UI 宿主开发者,
**我想要** `and` 在所有输入均为 true 时返回 true,
**以便** 组合多个验证条件（如 required + email）。

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-2.1 | WHEN `values=[true,true]` THEN `Execute` 返回 true（`NativeAndFunction.cpp:43-49`） | 正常 |
| AC-2.2 | WHEN `values=[true,true,true]`（≥2 项全为布尔 true）THEN 返回 true（`NativeAndFunction.cpp:43-49`） | 正常 |

### US-3: 逻辑与短路（任一 false 返回 false）

**作为** 生成式 UI 宿主开发者,
**我想要** `and` 在任一项为 false 时立即返回 false,
**以便** 校验条件快速失败。

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-3.1 | WHEN `values=[true,false]` THEN 返回 false（`NativeAndFunction.cpp:45-47`） | 正常 |
| AC-3.2 | WHEN `values=[false,true]` THEN 循环首项即命中 false 早返回（不继续后续项组合）（`NativeAndFunction.cpp:43-48`） | 边界 |

### US-4: 非法入参回退

**作为** 生成式 UI 宿主开发者,
**我想要** `and` 对非法入参有确定性回退,
**以便** 结构异常时得到稳定的 false 而非异常。

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-4.1 | WHEN `resolvedArgs` 非对象 THEN 返回 false（`NativeAndFunction.cpp:29-31`） | 异常 |
| AC-4.2 | WHEN `values` 非数组 THEN 返回 false（`NativeAndFunction.cpp:33-36`） | 异常 |
| AC-4.3 | WHEN `values` 数组长度 < 2（0 或 1 项）THEN 返回 false（`NativeAndFunction.cpp:38-41`） | 边界 |
| AC-4.4 | WHEN `values` 含运行时解析为非布尔的项 THEN 返回 false（`NativeAndFunction.cpp:44-47`） | 边界 |

### US-5: schema 约束

**作为** 生成式 UI 宿主开发者,
**我想要** `and` 的 DSL 结构受 schema 校验,
**以便** 非法 FunctionCall 在解析期被拦截。

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-5.1 | WHEN `args.values` 缺失或非数组或少于 2 项 THEN schema 校验失败（`and.json` `required:["values"]` + `type:"array"` + `minItems:2`） | 异常 |
| AC-5.2 | WHEN `returnType` 非 `"boolean"` THEN schema 校验失败（`and.json` `returnType: { const:"boolean" }`） | 异常 |

## 验收追溯

| AC编号 | 关联规则 | 关联 Task | 验证方式 | 证据 |
|----|---------|----------|---------|------|
| AC-1.1,AC-1.2,AC-1.3,AC-1.4 | R-1 | T-1 | 静态比对：ArkTS `asFunctionItem` vs C++ `Register` | `AndFunction.ets:25-32`、`NativeFunctionRegistry.cpp:78` |
| AC-2.1,AC-2.2 | R-2 | T-1 | C++ UT：全 true 数组 | `NativeAndFunction.cpp:43-49` |
| AC-3.1,AC-3.2 | R-3 | T-1 | C++ UT：含 false 数组 | `NativeAndFunction.cpp:43-48` |
| AC-4.1,AC-4.2,AC-4.3,AC-4.4 | R-4,R-5,R-6 | T-1 | C++ UT：非对象/非数组/缺项/非布尔 | `NativeAndFunction.cpp:29-47` |
| AC-5.1,AC-5.2 | R-7 | T-1 | 静态比对：`and.json` | `and.json` |

## 规则定义

| 规则ID | 类型 | 触发条件 | 预期行为 | 边界/约束 | 关联AC |
|--------|------|---------|---------|----------|--------|
| R-1 | 行为 | `and` 作为 FunctionCall 被解析 | 经 `NativeFunctionRegistry` 执行 `NativeAndFunction` | `isInnerNative:true`，functionCall 未定义 | AC-1.1,AC-1.2,AC-1.3,AC-1.4 |
| R-2 | 行为 | `values` 每一项均为布尔 true | 返回 true | 需先通过 schema（minItems 2） | AC-2.1,AC-2.2 |
| R-3 | 行为 | `values` 任一项为 false | 返回 false（循环早返回） | 非延迟求值，仅布尔组合早返回 | AC-3.1,AC-3.2 |
| R-4 | 异常 | `resolvedArgs` 非对象或 `values` 非数组 | 返回 false | 防御性回退 | AC-4.1,AC-4.2 |
| R-5 | 边界 | `values` 数组长度 < 2 | 返回 false | 与 schema minItems:2 对齐 | AC-4.3 |
| R-6 | 边界 | `values` 含非布尔项 | 返回 false | 运行时路径解析为非布尔才触发 | AC-4.4 |
| R-7 | 异常 | schema 校验（values 结构/returnType） | 解析期拒绝 FunctionCall | returnType 仅 boolean | AC-5.1,AC-5.2 |

## 验证映射

| 编号 | 对应规格项 | 验证方式 | 验证重点 |
|------|----------|---------|---------|
| VM-1 | AC-1.1,AC-1.2,AC-1.3,AC-1.4 声明与注册 | 静态比对 | name/isInnerNative/Register 一致性 |
| VM-2 | AC-2.1,AC-2.2 全 true | C++ UT | 返回值 true |
| VM-3 | AC-3.1,AC-3.2 含 false | C++ UT | 早返回 false |
| VM-4 | AC-4.1,AC-4.2,AC-4.3,AC-4.4 非法入参 | C++ UT | 非对象/非数组/缺项/非布尔回退 |
| VM-5 | AC-5.1,AC-5.2 schema | 静态比对 | and.json 结构约束 |

## API 变更分析

> 存量补录，无新增/变更 Public API。`and` 为内部内置函数（`InnerFunctionItem`）。

### 新增 API

N/A。

### 变更/废弃 API

| API 名称 | 变更类型 | 影响场景 | 迁移指引 | 关联 AC |
|----------|---------|---------|---------|--------|
| 内置函数 `and` | 既有 | DSL 逻辑与求值（校验条件组合） | 不直接暴露为宿主 API，经 DSL FunctionCall 调用 | AC-1.1 |

> 契约位置：`genui/src/main/ets/core/functions/logic/AndFunction.ets`；执行 `NativeAndFunction.cpp`。Kit：`@arkui-genius/genui`；权限：无。

## 接口规格

### 接口定义

**`and`（FunctionCall 契约，`returnType: "boolean"`）**

| 属性 | 值 |
|------|-----|
| 函数签名 | `FunctionResult NativeAndFunction::Execute(const JsonValue& resolvedArgs)` |
| 返回值 | `boolean` — 全 true 为 true；任一 false/非法入参为 false |
| 开放范围 | InnerApi（内置函数，DSL FunctionCall 触发） |
| 错误码 | N/A（逻辑函数始终返回 boolean，不产生错误码） |
| 关联 AC | AC-1.1,AC-1.2,AC-1.3,AC-1.4,AC-2.1,AC-2.2,AC-3.1,AC-3.2,AC-4.1,AC-4.2,AC-4.3,AC-4.4 |

**参数约束**

| 参数 | 类型 | 必填 | 默认值 | 约束条件 |
|------|------|------|--------|---------|
| values | boolean[] | 是 | — | DynamicBoolean[]；schema minItems 2；每项可为字面量/路径绑定/嵌套函数调用 |

**行为场景**

| # | 触发条件 | 预期行为 | 关联 AC |
|---|----------|----------|---------|
| 1 | values 全 true | 返回 true | AC-2.1,AC-2.2 |
| 2 | values 任一 false | 返回 false（早返回） | AC-3.1,AC-3.2 |
| 3 | resolvedArgs 非对象 | 返回 false | AC-4.1 |
| 4 | values 非数组 | 返回 false | AC-4.2 |
| 5 | values 长度 < 2 | 返回 false | AC-4.3 |
| 6 | values 含非布尔项 | 返回 false | AC-4.4 |

## 兼容性声明

- **已有 API 行为变更:** 否（存量补录）。
- **配置文件格式变更:** 否。
- **数据存储格式变更:** 否。
- **最低支持版本:** A2UI 原生协议 v0.9。
- **API 版本号策略:** 函数语义由 schema（`and.json`）与 `NativeAndFunction` 共同固化；逻辑函数无 @since 标注需求。

## 架构约束

| 关键约束 | 约束说明 | 影响 AC |
|---------|---------|--------|
| 原生内置 | `isInnerNative:true`，在 C++ 执行，避免跨语言往返 | AC-1.1,AC-1.2,AC-1.3,AC-1.4 |
| 入参全量解析 | 进入 native 前 `values` 已递归解析（含嵌套调用），非延迟求值 | AC-3.2 |
| 返回类型约束 | schema 强制 `returnType: "boolean"` | AC-5.2 |

## 非功能性需求

| 类型 | 指标/阈值 | 验证方式 | 证据 |
|------|----------|---------|------|
| 可靠性 | 非法入参不抛异常，统一回退 false | C++ UT | `NativeAndFunction.cpp:29-47` |
| 性能 | 布尔组合 O(n)，遇 false 早返回 | C++ UT | `NativeAndFunction.cpp:43-48` |

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
| 版本升级 | 是 | 函数语义随协议 v0.9 固化 | AC-5.1,AC-5.2 |
| 生态兼容 | 是 | A2UI 原生协议 v0.9 逻辑函数 | 概述「目标版本」 |

## 行为场景（可选，Gherkin）

```gherkin
Feature: and 逻辑与函数
  作为 生成式 UI 宿主开发者
  我想要 and 对 values 布尔数组做逻辑与
  以便 组合多个验证条件

  Scenario: 全 true 返回 true
    Given DSL 片段为 {"call":"and","args":{"values":[true,true]},"returnType":"boolean"}
    When 引擎解析并执行 and
    Then 返回 true

  Scenario Outline: 非法/非全真输入回退
    Given values 为 <values>
    When 执行 NativeAndFunction::Execute
    Then 返回 <result>

    Examples:
      | values | result |
      | [true,false] | false |
      | [false,true] | false |
      | [] | false |
      | [true] | false |
```

## Spec 自审清单

- [x] 无"待定""TBD""TODO"等占位符
- [x] 所有 AC 使用 WHEN/THEN 格式，可独立测试
- [x] 范围边界明确（Feat-01 只覆盖 `and`；`or`/`not`/`openUrl` 归 Feat-02/03/04）
- [x] 无语义模糊表述
- [x] AC 与规则表交叉一致（每条 AC 至少关联一条规则，每条规则至少关联一个 AC）
- [x] 规则表每条通过 5 项质量检查（可复现/可观测/边界值/关联AC/无冲突）

## context-references

```yaml
context-queries:
  - repo: "GenerativeUI/A2UIRender"
    query: "NativeAndFunction Execute 逻辑与 短路 values 布尔数组"
  - repo: "GenerativeUI/A2UIRender"
    query: "and.json schema minItems 2 DynamicBoolean returnType boolean"
  - repo: "GenerativeUI/A2UIRender"
    query: "DynamicValueResolver ResolveFunctionArgsWithPolicy 参数全量解析 NativeFunctionRegistry 分流"
```

**关键文档：** `genui/src/main/ets/core/functions/logic/AndFunction.ets`、`genui/src/main/cpp/functions/impl/NativeAndFunction.cpp`、`genui/src/main/cpp/functions/NativeFunctionRegistry.cpp`、`genui/src/main/resources/rawfile/schema/A2UI/v0.9/functions/and.json`
