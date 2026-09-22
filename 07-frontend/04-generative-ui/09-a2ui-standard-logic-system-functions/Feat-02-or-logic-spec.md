# 特性规格

> Func-07-04-09-Feat-02 `or` 函数：固化 A2UI 标准协议逻辑或运算函数的契约。`or` 为原生内置函数（`isInnerNative: true`），在 C++ `NativeFunctionRegistry` 中执行，对 `values` 布尔数组做逻辑或：任一为 true 即返回 true，全为 false 返回 false。与 `and` 不同，`or` 对非布尔项采用「跳过」而非「当作 false」的回退策略。入参约束 `values` 至少 2 项（schema `minItems: 2`），返回类型 `boolean`。基准实现：`@arkui-genius/genui`（A2UIRender）。

## 概述

| 属性 | 值 |
|------|-----|
| 特性名称 | or 逻辑或函数 |
| 特性编号 | Func-07-04-09-Feat-02 |
| 优先级 | P0 |
| 目标版本 | A2UI 原生协议 v0.9 |
| SIG 归属 | GenUI SIG |
| 状态 | Baselined |
| 复杂度 | 标准 |

## 本次变更范围（Delta）

| 类型 | 内容 | 说明 |
|------|------|------|
| ADDED | 无（存量补录） | 本特性为 Func-07-04-09 第二个 Feat |

## 输入文档

| 文档 | 路径 | 状态 |
|------|------|------|
| Design | `07-frontend/04-generative-ui/09-a2ui-standard-logic-system-functions/design.md` | Baselined |
| 函数声明（ArkTS） | `genui/src/main/ets/core/functions/logic/OrFunction.ets` | — |
| 原生实现（C++） | `genui/src/main/cpp/functions/impl/NativeOrFunction.cpp` | — |
| 原生注册（C++） | `genui/src/main/cpp/functions/NativeFunctionRegistry.cpp` | — |
| Schema | `genui/src/main/resources/rawfile/schema/A2UI/v0.9/functions/or.json` | — |
| 逻辑函数参考（Docs） | `reference/functions/logic.md` | 理解辅助 |

> 需求基线、不涉及项详见 proposal.md。design.md 与本文档并行产出，互不依赖。

---

## 用户故事

### US-1: or 函数声明与注册

**作为** 生成式 UI 宿主开发者,
**我想要** 引擎把 `or` 注册为原生内置逻辑函数,
**以便** DSL 中以 `{ "call": "or", ... }` 触发逻辑或求值。

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-1.1 | WHEN 实例化 `orFunction` THEN `asFunctionItem()` 返回 `{ name:'or', isInnerNative:true, functionCall:undefined }`（`OrFunction.ets:25-32`） | 正常 |
| AC-1.2 | WHEN 汇总标准内置函数 THEN `orFunction` 位于 `standardBuiltinFunctions` 数组（`A2UIBasicFunctions.ets:59`） | 正常 |
| AC-1.3 | WHEN 初始化 native 注册表 THEN `Register("or", NativeOrFunction)` 完成（`NativeFunctionRegistry.cpp:79`） | 正常 |
| AC-1.4 | WHEN 查询函数名 THEN `NativeOrFunction::GetName()` 返回 `"or"`（`NativeOrFunction.cpp:22-25`） | 正常 |

### US-2: 逻辑或语义（任一 true 返回 true）

**作为** 生成式 UI 宿主开发者,
**我想要** `or` 在任一项为 true 时返回 true,
**以便** 表达「至少满足其一」的校验条件（如 hasPhone 或 hasEmail）。

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-2.1 | WHEN `values=[true,false]` THEN 返回 true（`NativeOrFunction.cpp:43-51`） | 正常 |
| AC-2.2 | WHEN `values=[false,true]` THEN 循环至第二项命中 true 返回 true（`NativeOrFunction.cpp:43-51`） | 正常 |
| AC-2.3 | WHEN `values=[true,true]` THEN 返回 true（`NativeOrFunction.cpp:43-51`） | 正常 |

### US-3: 逻辑或短路（全 false 返回 false）

**作为** 生成式 UI 宿主开发者,
**我想要** `or` 在全部为 false 时返回 false,
**以便** 条件组合正确收敛。

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-3.1 | WHEN `values=[false,false]` THEN 返回 false（`NativeOrFunction.cpp:43-53`） | 正常 |
| AC-3.2 | WHEN `values=[false,false,false]` THEN 遍历全部后返回 false（`NativeOrFunction.cpp:43-53`） | 边界 |

### US-4: 非法入参回退

**作为** 生成式 UI 宿主开发者,
**我想要** `or` 对非法入参有确定性回退,
**以便** 结构异常时得到稳定结果。

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-4.1 | WHEN `resolvedArgs` 非对象 THEN 返回 false（`NativeOrFunction.cpp:29-31`） | 异常 |
| AC-4.2 | WHEN `values` 非数组 THEN 返回 false（`NativeOrFunction.cpp:33-36`） | 异常 |
| AC-4.3 | WHEN `values` 数组长度 < 2（0 或 1 项）THEN 返回 false（`NativeOrFunction.cpp:38-41`） | 边界 |
| AC-4.4 | WHEN `values` 含运行时解析为非布尔的项 THEN 该项被跳过（`continue`），不参与或运算（`NativeOrFunction.cpp:45-47`） | 边界 |

### US-5: schema 约束

**作为** 生成式 UI 宿主开发者,
**我想要** `or` 的 DSL 结构受 schema 校验,
**以便** 非法 FunctionCall 在解析期被拦截。

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-5.1 | WHEN `args.values` 缺失或非数组或少于 2 项 THEN schema 校验失败（`or.json` `required:["values"]` + `type:"array"` + `minItems:2`） | 异常 |
| AC-5.2 | WHEN `returnType` 非 `"boolean"` THEN schema 校验失败（`or.json` `returnType: { const:"boolean" }`） | 异常 |

## 验收追溯

| AC编号 | 关联规则 | 关联 Task | 验证方式 | 证据 |
|----|---------|----------|---------|------|
| AC-1.1,AC-1.2,AC-1.3,AC-1.4 | R-1 | T-2 | 静态比对：ArkTS `asFunctionItem` vs C++ `Register` | `OrFunction.ets:25-32`、`NativeFunctionRegistry.cpp:79` |
| AC-2.1,AC-2.2,AC-2.3 | R-2 | T-2 | C++ UT：含 true 数组 | `NativeOrFunction.cpp:43-51` |
| AC-3.1,AC-3.2 | R-3 | T-2 | C++ UT：全 false 数组 | `NativeOrFunction.cpp:43-53` |
| AC-4.1,AC-4.2,AC-4.3,AC-4.4 | R-4,R-5,R-6 | T-2 | C++ UT：非对象/非数组/缺项/非布尔跳过 | `NativeOrFunction.cpp:29-53` |
| AC-5.1,AC-5.2 | R-7 | T-2 | 静态比对：`or.json` | `or.json` |

## 规则定义

| 规则ID | 类型 | 触发条件 | 预期行为 | 边界/约束 | 关联AC |
|--------|------|---------|---------|----------|--------|
| R-1 | 行为 | `or` 作为 FunctionCall 被解析 | 经 `NativeFunctionRegistry` 执行 `NativeOrFunction` | `isInnerNative:true`，functionCall 未定义 | AC-1.1,AC-1.2,AC-1.3,AC-1.4 |
| R-2 | 行为 | `values` 任一项为布尔 true | 返回 true（循环早返回） | 非延迟求值，仅布尔组合早返回 | AC-2.1,AC-2.2,AC-2.3 |
| R-3 | 行为 | `values` 全为 false | 返回 false | 需先通过 schema（minItems 2） | AC-3.1,AC-3.2 |
| R-4 | 异常 | `resolvedArgs` 非对象或 `values` 非数组 | 返回 false | 防御性回退 | AC-4.1,AC-4.2 |
| R-5 | 边界 | `values` 数组长度 < 2 | 返回 false | 与 schema minItems:2 对齐 | AC-4.3 |
| R-6 | 边界 | `values` 含非布尔项 | 跳过该项（`continue`），非当作 false | 与 `and` 回退策略不同 | AC-4.4 |
| R-7 | 异常 | schema 校验（values 结构/returnType） | 解析期拒绝 FunctionCall | returnType 仅 boolean | AC-5.1,AC-5.2 |

## 验证映射

| 编号 | 对应规格项 | 验证方式 | 验证重点 |
|------|----------|---------|---------|
| VM-1 | AC-1.1,AC-1.2,AC-1.3,AC-1.4 声明与注册 | 静态比对 | name/isInnerNative/Register 一致性 |
| VM-2 | AC-2.1,AC-2.2,AC-2.3 任一 true | C++ UT | 返回值 true |
| VM-3 | AC-3.1,AC-3.2 全 false | C++ UT | 返回值 false |
| VM-4 | AC-4.1,AC-4.2,AC-4.3,AC-4.4 非法入参 | C++ UT | 非对象/非数组/缺项/非布尔跳过 |
| VM-5 | AC-5.1,AC-5.2 schema | 静态比对 | or.json 结构约束 |

## API 变更分析

> 存量补录，无新增/变更 Public API。`or` 为内部内置函数（`InnerFunctionItem`）。

### 新增 API

N/A。

### 变更/废弃 API

| API 名称 | 变更类型 | 影响场景 | 迁移指引 | 关联 AC |
|----------|---------|---------|---------|--------|
| 内置函数 `or` | 既有 | DSL 逻辑或求值（多条件任一满足） | 不直接暴露为宿主 API，经 DSL FunctionCall 调用 | AC-1.1 |

> 契约位置：`genui/src/main/ets/core/functions/logic/OrFunction.ets`；执行 `NativeOrFunction.cpp`。Kit：`@arkui-genius/genui`；权限：无。

## 接口规格

### 接口定义

**`or`（FunctionCall 契约，`returnType: "boolean"`）**

| 属性 | 值 |
|------|-----|
| 函数签名 | `FunctionResult NativeOrFunction::Execute(const JsonValue& resolvedArgs)` |
| 返回值 | `boolean` — 任一 true 为 true；全 false/非法入参为 false |
| 开放范围 | InnerApi（内置函数，DSL FunctionCall 触发） |
| 错误码 | N/A（逻辑函数始终返回 boolean，不产生错误码） |
| 关联 AC | AC-1.1,AC-1.2,AC-1.3,AC-1.4,AC-2.1,AC-2.2,AC-2.3,AC-3.1,AC-3.2,AC-4.1,AC-4.2,AC-4.3,AC-4.4 |

**参数约束**

| 参数 | 类型 | 必填 | 默认值 | 约束条件 |
|------|------|------|--------|---------|
| values | boolean[] | 是 | — | DynamicBoolean[]；schema minItems 2；每项可为字面量/路径绑定/嵌套函数调用 |

**行为场景**

| # | 触发条件 | 预期行为 | 关联 AC |
|---|----------|----------|---------|
| 1 | values 任一 true | 返回 true（早返回） | AC-2.1,AC-2.2,AC-2.3 |
| 2 | values 全 false | 返回 false | AC-3.1,AC-3.2 |
| 3 | resolvedArgs 非对象 | 返回 false | AC-4.1 |
| 4 | values 非数组 | 返回 false | AC-4.2 |
| 5 | values 长度 < 2 | 返回 false | AC-4.3 |
| 6 | values 含非布尔项 | 跳过该项继续遍历 | AC-4.4 |

## 兼容性声明

- **已有 API 行为变更:** 否（存量补录）。
- **配置文件格式变更:** 否。
- **数据存储格式变更:** 否。
- **最低支持版本:** A2UI 原生协议 v0.9。
- **API 版本号策略:** 函数语义由 schema（`or.json`）与 `NativeOrFunction` 共同固化；逻辑函数无 @since 标注需求。

## 架构约束

| 关键约束 | 约束说明 | 影响 AC |
|---------|---------|--------|
| 原生内置 | `isInnerNative:true`，在 C++ 执行，避免跨语言往返 | AC-1.1,AC-1.2,AC-1.3,AC-1.4 |
| 非布尔跳过 | `or` 对非布尔项 `continue` 跳过（区别于 `and` 当作 false） | AC-4.4 |
| 返回类型约束 | schema 强制 `returnType: "boolean"` | AC-5.2 |

## 非功能性需求

| 类型 | 指标/阈值 | 验证方式 | 证据 |
|------|----------|---------|------|
| 可靠性 | 非法入参不抛异常，统一回退 | C++ UT | `NativeOrFunction.cpp:29-53` |
| 性能 | 布尔组合 O(n)，遇 true 早返回 | C++ UT | `NativeOrFunction.cpp:43-51` |

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
Feature: or 逻辑或函数
  作为 生成式 UI 宿主开发者
  我想要 or 对 values 布尔数组做逻辑或
  以便 表达至少满足其一的校验条件

  Scenario: 任一 true 返回 true
    Given DSL 片段为 {"call":"or","args":{"values":[{"path":"form.hasPhone"},{"path":"form.hasEmail"}]},"returnType":"boolean"}
    When 引擎解析路径后执行 or
    Then 若任一路径为 true 则返回 true

  Scenario Outline: 全 false 与非法入参回退
    Given values 为 <values>
    When 执行 NativeOrFunction::Execute
    Then 返回 <result>

    Examples:
      | values | result |
      | [false,false] | false |
      | [true,false] | true |
      | [] | false |
      | [true] | false |
```

## Spec 自审清单

- [x] 无"待定""TBD""TODO"等占位符
- [x] 所有 AC 使用 WHEN/THEN 格式，可独立测试
- [x] 范围边界明确（Feat-02 只覆盖 `or`；`and`/`not`/`openUrl` 归 Feat-01/03/04）
- [x] 无语义模糊表述
- [x] AC 与规则表交叉一致
- [x] 规则表每条通过 5 项质量检查（可复现/可观测/边界值/关联AC/无冲突）

## context-references

```yaml
context-queries:
  - repo: "GenerativeUI/A2UIRender"
    query: "NativeOrFunction Execute 逻辑或 短路 values 非布尔 continue 跳过"
  - repo: "GenerativeUI/A2UIRender"
    query: "or.json schema minItems 2 DynamicBoolean returnType boolean"
  - repo: "GenerativeUI/A2UIRender"
    query: "or 与 and 非布尔回退策略差异 NativeFunctionRegistry 注册"
```

**关键文档：** `genui/src/main/ets/core/functions/logic/OrFunction.ets`、`genui/src/main/cpp/functions/impl/NativeOrFunction.cpp`、`genui/src/main/cpp/functions/NativeFunctionRegistry.cpp`、`genui/src/main/resources/rawfile/schema/A2UI/v0.9/functions/or.json`
