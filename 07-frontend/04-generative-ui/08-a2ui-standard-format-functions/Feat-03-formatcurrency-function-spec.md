# 特性规格

> Func-07-04-08-Feat-03 formatCurrency 函数：固化 A2UI 标准协议货币格式化函数——目录注册（`name='formatCurrency'`、`isInnerNative=true`）、`value`+`currency` 必填、`decimals`/`grouping` 复用 formatNumber 解析、输出 `"{currency} {formatted}"`、分组路径复用 `NativeFormatNumberFunction::FormatWithGrouping`。基准实现：`@arkui-genius/genui`（A2UIRender）。

## 概述

| 属性 | 值 |
|------|-----|
| 特性名称 | formatCurrency 函数 |
| 特性编号 | Func-07-04-08-Feat-03 |
| 优先级 | P0 |
| 目标版本 | A2UI 原生协议 v0.9 |
| SIG 归属 | GenUI SIG |
| 状态 | Baselined |
| 复杂度 | 标准 |

## 本次变更范围（Delta）

| 类型 | 内容 | 说明 |
|------|------|------|
| ADDED | 无（存量补录） | 本特性为 Func-07-04-08 第三个 Feat |

## 输入文档

| 文档 | 路径 | 状态 |
|------|------|------|
| Design | `07-frontend/04-generative-ui/08-a2ui-standard-format-functions/design.md` | Baselined |
| 目录注册（ArkTS） | `genui/src/main/ets/core/functions/format/FormatCurrencyFunction.ets` | — |
| 聚合注册（ArkTS） | `genui/src/main/ets/core/functions/A2UIBasicFunctions.ets` | — |
| 函数实现（C++） | `genui/src/main/cpp/functions/impl/NativeFormatCurrencyFunction.cpp` | — |
| 函数声明（C++） | `genui/src/main/cpp/functions/NativeFormatCurrencyFunction.h` | — |
| 复用（C++） | `genui/src/main/cpp/functions/NativeFormatNumberFunction.{h,cpp}` | — |
| 函数 Schema | `genui/src/main/resources/rawfile/schema/A2UI/v0.9/functions/formatCurrency.json` | 契约 |
| 函数参考（Docs） | `reference/functions/format.md` | 理解辅助 |

> 需求基线、不涉及项详见 proposal.md。design.md 与本文档并行产出，互不依赖。

---

## 用户故事

### US-1: formatCurrency 目录注册与类型识别

**作为** 生成式 UI 宿主开发者,
**我想要** 引擎将 `call: "formatCurrency"` 识别为标准原生函数,
**以便** 服务端下发的货币格式化函数被正确执行。

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-1.1 | WHEN 调用 `formatCurrencyFunction.asFunctionItem()` THEN 返回 `name='formatCurrency'`、`isInnerNative=true` 的 `InnerFunctionItem`（`FormatCurrencyFunction.ets:25-31`） | 正常 |
| AC-1.2 | WHEN schemaProvider 被调用 THEN 经 `loadFunctionSchema(version, 'formatCurrency.json')` 返回 schema（`FormatCurrencyFunction.ets:34-36`） | 正常 |
| AC-1.3 | WHEN `NativeFunctionRegistry` 构造 THEN 经 `Register("formatCurrency", ...)` 注册（`NativeFunctionRegistry.cpp:75`） | 正常 |

### US-2: value 与 currency 参数解析

**作为** 生成式 UI 宿主开发者,
**我想要** 通过 value 与 currency 指定金额与货币代码,
**以便** 输出带货币代码的金额字符串。

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-2.1 | WHEN value 非 number 或 currency 非 string THEN 返回 `FunctionResult("")`（`NativeFormatCurrencyFunction.cpp:62-65`） | 异常 |
| AC-2.2 | WHEN currency 为空字符串 THEN 返回 `FunctionResult("")`（`NativeFormatCurrencyFunction.cpp:69-71`） | 边界 |
| AC-2.3 | WHEN value 与 currency 均合法 THEN 结果拼装为 `currency + " " + formatted`（`NativeFormatCurrencyFunction.cpp:97`） | 正常 |

### US-3: decimals 与 grouping 解析（复用 formatNumber）

**作为** 生成式 UI 宿主开发者,
**我想要** 通过 decimals/grouping 控制金额精度与千分位,
**以便** 得到一致的数字格式。

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-3.1 | WHEN decimals 缺省 THEN 使用默认值 2（`NativeFormatCurrencyFunction.cpp:73`） | 边界 |
| AC-3.2 | WHEN decimals 非法（非 number/越界/非有限） THEN `ParseDecimals` 返回 false，返回 `""`（`NativeFormatCurrencyFunction.cpp:31-46,74-77`） | 异常 |
| AC-3.3 | WHEN grouping 缺省 THEN 使用默认值 false（`NativeFormatCurrencyFunction.cpp:79`） | 边界 |
| AC-3.4 | WHEN grouping 有效但非 bool THEN 返回 `""`（`NativeFormatCurrencyFunction.cpp:82-86`） | 异常 |

### US-4: 货币格式化输出

**作为** 生成式 UI 宿主开发者,
**我想要** grouping 开启时走千分位分组、关闭时定点输出,
**以便** 两种数字格式均可用。

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-4.1 | WHEN grouping=true THEN 复用 `NativeFormatNumberFunction::FormatWithGrouping` 输出（`NativeFormatCurrencyFunction.cpp:89-91`） | 正常 |
| AC-4.2 | WHEN grouping=false THEN `std::fixed`+`setprecision(decimals)` 直接输出（`NativeFormatCurrencyFunction.cpp:92-95`） | 正常 |
| AC-4.3 | WHEN 完成格式化 THEN 前缀拼接 currency 与空格，如 `"CNY 1,234.56"` | 正常 |

### US-5: 非法入参处理

**作为** 生成式 UI 宿主开发者,
**我想要** 非法入参返回空字符串而非抛异常,
**以便** 渲染过程不崩溃。

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-5.1 | WHEN `resolvedArgs` 非对象 THEN 返回 `FunctionResult("")`（`NativeFormatCurrencyFunction.cpp:57-59`） | 异常 |

## 验收追溯

| AC编号 | 关联规则 | 关联 Task | 验证方式 | 证据 |
|----|---------|----------|---------|------|
| AC-1.1,AC-1.2,AC-1.3 | R-1 | T-3 | ArkTS 单测 + C++ 静态比对：目录注册 | `FormatCurrencyFunction.ets:25-36`、`NativeFunctionRegistry.cpp:75` |
| AC-2.1,AC-2.2,AC-2.3 | R-2 | T-3 | C++ UT：value/currency 校验 | `NativeFormatCurrencyFunction.cpp:62-71,97` |
| AC-3.1,AC-3.2,AC-3.3,AC-3.4 | R-3 | T-3 | C++ UT：`ParseDecimals`/grouping | `NativeFormatCurrencyFunction.cpp:31-46,73-86` |
| AC-4.1,AC-4.2,AC-4.3 | R-4 | T-3 | C++ UT：分组/定点输出 | `NativeFormatCurrencyFunction.cpp:88-99` |
| AC-5.1 | R-5 | T-3 | C++ UT：非法入参 | `NativeFormatCurrencyFunction.cpp:55-99` |

## 规则定义

| 规则ID | 类型 | 触发条件 | 预期行为 | 边界/约束 | 关联AC |
|--------|------|---------|---------|----------|--------|
| R-1 | 行为 | 调用 `asFunctionItem()` | 返回 `name='formatCurrency'`、`isInnerNative=true` 目录项 | 仅内部注册 | AC-1.1,AC-1.2,AC-1.3 |
| R-2 | 异常 | value 非 number 或 currency 非 string/空 | 返回 `""` | currency 不校验 ISO 4217 | AC-2.1,AC-2.2 |
| R-3 | 边界 | decimals/grouping 取值 | decimals 缺省 2、grouping 缺省 false；非法返回 `""` | 复用 formatNumber 规则 | AC-3.1,AC-3.2,AC-3.3,AC-3.4 |
| R-4 | 行为 | 货币格式化 | 输出 `currency + " " + formatted`；grouping 复用 `FormatWithGrouping` | 符号硬编码前置 | AC-2.3,AC-4.1,AC-4.2,AC-4.3 |
| R-5 | 异常 | args 非对象 | 返回 `""` | 统一空串 | AC-5.1 |

## 验证映射

| 编号 | 对应规格项 | 验证方式 | 验证重点 |
|------|----------|---------|---------|
| VM-1 | AC-1.1,AC-1.2,AC-1.3 目录注册 | ArkTS 单测/静态比对 | name/isInnerNative/schema |
| VM-2 | AC-2.1,AC-2.2,AC-2.3 value/currency | C++ UT | 必填/空 currency |
| VM-3 | AC-3.1,AC-3.2,AC-3.3,AC-3.4 decimals/grouping | C++ UT | 默认值/非法降级 |
| VM-4 | AC-4.1,AC-4.2,AC-4.3 输出格式 | C++ UT | `{currency} {formatted}` |
| VM-5 | AC-5.1 非法入参 | C++ UT | 非对象空串 |

## API 变更分析

> 存量补录，无新增/变更 Public API。函数经内部 `InnerFunctionItem` 注册。

### 新增 API

N/A。

### 变更/废弃 API

| API 名称 | 变更类型 | 影响场景 | 迁移指引 | 关联 AC |
|----------|---------|---------|---------|--------|
| `formatCurrencyFunction.asFunctionItem()`（内部） | 既有 | 函数目录项构造 | 不直接暴露给宿主 | AC-1.1,AC-1.2 |
| `NativeFormatCurrencyFunction::Execute`（内部） | 既有 | 货币格式化 | 框架内部；复用 `NativeFormatNumberFunction::FormatWithGrouping` | AC-4.1 |

> d.ts 位置：`genui/src/main/ets/core/functions/format/FormatCurrencyFunction.ets`。Kit：`@arkui-genius/genui`；权限：无。

## 接口规格

### 接口定义

**`formatCurrencyFunction.asFunctionItem()`（内部，`FormatCurrencyFunction.ets:25`）**

| 属性 | 值 |
|------|-----|
| 函数签名 | `asFunctionItem(): InnerFunctionItem` |
| 返回值 | `InnerFunctionItem` — name=`formatCurrency`、isInnerNative=true |
| 开放范围 | 内部（framework-internal） |
| 错误码 | N/A |
| 关联 AC | AC-1.1,AC-1.2 |

**`NativeFormatCurrencyFunction::Execute(resolvedArgs)`（`NativeFormatCurrencyFunction.cpp:55`）**

| 属性 | 值 |
|------|-----|
| 函数签名 | `FunctionResult Execute(const JsonValue& resolvedArgs)` |
| 返回值 | `FunctionResult` — `"{currency} {formatted}"`；非法入参返回 `""` |
| 开放范围 | 内部 |
| 错误码 | N/A |
| 关联 AC | AC-2.1,AC-2.2,AC-2.3,AC-3.1,AC-3.2,AC-3.3,AC-3.4,AC-4.1,AC-4.2,AC-4.3,AC-5.1 |

**参数约束**

| 参数 | 类型 | 必填 | 默认值 | 约束条件 |
|------|------|------|--------|---------|
| value | number | 是 | — | 任意有限数值 |
| currency | string | 是 | — | 非空字符串，不校验 ISO 4217 |
| decimals | number | 否 | 2 | `\|x\|<=20`，负数取绝对值 |
| grouping | boolean | 否 | false | true 启用千分位逗号 |

**行为场景**

| # | 触发条件 | 预期行为 | 关联 AC |
|---|----------|----------|---------|
| 1 | value=1234.56, currency="CNY", grouping=true | "CNY 1,234.56" | AC-2.3,AC-4.1 |
| 2 | value=1234.56, currency="CNY", grouping 缺省 | "CNY 1234.56" | AC-4.2 |
| 3 | currency="" | "" | AC-2.2 |
| 4 | value 非 number | "" | AC-2.1 |
| 5 | decimals=25 | "" | AC-3.2 |

## 兼容性声明

- **已有 API 行为变更:** 否（存量补录）。
- **配置文件格式变更:** 否。
- **数据存储格式变更:** 否。
- **最低支持版本:** A2UI 原生协议 v0.9。
- **API 版本号策略:** schema `formatCurrency.json:21` 描述 decimals「Defaults to 0 or 2 depending on locale」、grouping「Defaults to true」，但代码固定 decimals=2（`.cpp:73`）、grouping=false（`.cpp:79`），以代码为准（RISK-1）。

## 架构约束

| 关键约束 | 约束说明 | 影响 AC |
|---------|---------|--------|
| 货币代码不校验 | currency 仅作字符串前缀，不校验 ISO 4217、不按 locale 映射符号（RISK-4） | AC-2.2 |
| 复用 formatNumber | grouping 路径复用 `FormatWithGrouping`，舍入行为一致 | AC-4.1 |
| 统一空串降级 | 非法入参返回 `""`，不抛异常 | AC-5.1 |

## 非功能性需求

| 类型 | 指标/阈值 | 验证方式 | 证据 |
|------|----------|---------|------|
| 可靠性 | 非法 currency/decimals 不崩溃 | C++ UT | `NativeFormatCurrencyFunction.cpp:62-86` |
| 可测试性 | `Execute` 纯函数（无上下文依赖） | C++ UT | `NativeFormatCurrencyFunction.h:27-28` |

## 多设备适配声明

| 设备类型 | 行为差异 | 规格/约束 | 验证方式 | 证据 |
|---------|---------|----------|---------|------|
| 手机 | 无差异 | 货币格式化与设备无关 | ohosTest | — |
| 平板 | 无差异 | 同上 | ohosTest | — |
| 折叠屏 | 无差异 | 同上 | ohosTest | — |

## 全局特性影响

| 特性 | 适用？ | 结论 | 关联场景 |
|------|-------|------|---------|
| 无障碍 | 否 | 函数层不涉及 | — |
| 大字体 | 否 | 不涉及 | — |
| 深色模式 | 否 | 不涉及 | — |
| 多窗口/分屏 | 否 | 无差异 | — |
| 多用户 | 否 | 无差异 | — |
| 版本升级 | 是 | 协议 v0.9 函数 schema | 概述「目标版本」 |
| 生态兼容 | 是 | A2UI 原生协议 v0.9 formatCurrency 兼容 | `formatCurrency.json` |

## 行为场景（可选，Gherkin）

```gherkin
Feature: formatCurrency 函数
  作为 生成式 UI 宿主开发者
  我想要 金额与货币代码组合格式化
  以便 生成带货币代码的金额文本

  Scenario: 千分位金额
    Given value = 1234.56, currency = "CNY", grouping = true
    When 调用 formatCurrency
    Then 返回 "CNY 1,234.56"

  Scenario: 空货币代码降级
    Given currency = ""
    When 调用 formatCurrency
    Then 返回 ""
```

## Spec 自审清单

- [x] 无"待定""TBD""TODO"等占位符
- [x] 所有 AC 使用 WHEN/THEN 格式，可独立测试
- [x] 范围边界明确（Feat-03 做 formatCurrency；数值舍入语义归 Feat-02）
- [x] 无语义模糊表述
- [x] AC 与规则表交叉一致（每个 AC 至少关联一条规则，每条规则至少关联一个 AC）
- [x] 规则表每条通过 5 项质量检查（可复现/可观测/边界值/关联AC/无冲突）

## context-references

```yaml
context-queries:
  - repo: "GenerativeUI/A2UIRender"
    query: "FormatCurrencyFunction asFunctionItem formatCurrency.json 目录注册"
  - repo: "GenerativeUI/A2UIRender"
    query: "NativeFormatCurrencyFunction Execute currency 拼接 FormatWithGrouping 复用"
```

**关键文档：** `genui/src/main/ets/core/functions/format/FormatCurrencyFunction.ets`、`genui/src/main/cpp/functions/impl/NativeFormatCurrencyFunction.cpp`、`genui/src/main/cpp/functions/NativeFormatCurrencyFunction.h`、`genui/src/main/resources/rawfile/schema/A2UI/v0.9/functions/formatCurrency.json`