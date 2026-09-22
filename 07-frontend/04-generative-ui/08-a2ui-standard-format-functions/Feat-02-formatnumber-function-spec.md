# 特性规格

> Func-07-04-08-Feat-02 formatNumber 函数：固化 A2UI 标准协议数值格式化函数——目录注册（`name='formatNumber'`、`isInnerNative=true`）、`decimals`（默认 2、上限 20、取绝对值）与 `grouping`（默认 false、千分位逗号）参数解析、`FormatDecimal` 舍入、`FormatWithGrouping` 分组。基准实现：`@arkui-genius/genui`（A2UIRender）。

## 概述

| 属性 | 值 |
|------|-----|
| 特性名称 | formatNumber 函数 |
| 特性编号 | Func-07-04-08-Feat-02 |
| 优先级 | P0 |
| 目标版本 | A2UI 原生协议 v0.9 |
| SIG 归属 | GenUI SIG |
| 状态 | Baselined |
| 复杂度 | 标准 |

## 本次变更范围（Delta）

| 类型 | 内容 | 说明 |
|------|------|------|
| ADDED | 无（存量补录） | 本特性为 Func-07-04-08 第二个 Feat |

## 输入文档

| 文档 | 路径 | 状态 |
|------|------|------|
| Design | `07-frontend/04-generative-ui/08-a2ui-standard-format-functions/design.md` | Baselined |
| 目录注册（ArkTS） | `genui/src/main/ets/core/functions/format/FormatNumberFunction.ets` | — |
| 聚合注册（ArkTS） | `genui/src/main/ets/core/functions/A2UIBasicFunctions.ets` | — |
| 函数实现（C++） | `genui/src/main/cpp/functions/impl/NativeFormatNumberFunction.cpp` | — |
| 函数声明（C++） | `genui/src/main/cpp/functions/NativeFormatNumberFunction.h` | — |
| 函数 Schema | `genui/src/main/resources/rawfile/schema/A2UI/v0.9/functions/formatNumber.json` | 契约 |
| 函数参考（Docs） | `reference/functions/format.md` | 理解辅助 |

> 需求基线、不涉及项详见 proposal.md。design.md 与本文档并行产出，互不依赖。

---

## 用户故事

### US-1: formatNumber 目录注册与类型识别

**作为** 生成式 UI 宿主开发者,
**我想要** 引擎将 `call: "formatNumber"` 识别为标准原生函数,
**以便** 服务端下发的数值格式化函数被正确执行。

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-1.1 | WHEN 调用 `formatNumberFunction.asFunctionItem()` THEN 返回 `name='formatNumber'`、`isInnerNative=true` 的 `InnerFunctionItem`（`FormatNumberFunction.ets:25-31`） | 正常 |
| AC-1.2 | WHEN schemaProvider 被调用 THEN 经 `loadFunctionSchema(version, 'formatNumber.json')` 返回 schema（`FormatNumberFunction.ets:34-36`） | 正常 |
| AC-1.3 | WHEN `NativeFunctionRegistry` 构造 THEN 经 `Register("formatNumber", ...)` 注册（`NativeFunctionRegistry.cpp:74`） | 正常 |

### US-2: decimals 参数解析

**作为** 生成式 UI 宿主开发者,
**我想要** 通过 decimals 控制小数位数,
**以便** 得到指定精度的数值字符串。

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-2.1 | WHEN decimals 缺省 THEN 使用默认值 2（`NativeFormatNumberFunction.cpp:65`） | 边界 |
| AC-2.2 | WHEN decimals 为负数（如 -2） THEN `ParseDecimals` 取绝对值（`decimals=|x|`）后返回 true（`NativeFormatNumberFunction.cpp:42`） | 边界 |
| AC-2.3 | WHEN decimals 绝对值 > 20（如 25）或为非有限值（NaN/Infinity） THEN `ParseDecimals` 返回 false，`Execute` 返回 `""`（`NativeFormatNumberFunction.cpp:39-43,67-69`） | 边界 |
| AC-2.4 | WHEN decimals 非 number THEN `ParseDecimals` 返回 false，返回 `""`（`NativeFormatNumberFunction.cpp:34-36,67-69`） | 异常 |

### US-3: grouping 参数解析与千分位

**作为** 生成式 UI 宿主开发者,
**我想要** 通过 grouping 控制千分位分隔,
**以便** 生成 `1,234.56` 或 `1234.56` 格式。

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-3.1 | WHEN grouping 缺省 THEN 使用默认值 false（`NativeFormatNumberFunction.cpp:71`） | 边界 |
| AC-3.2 | WHEN grouping 为 true THEN 走 `FormatWithGrouping`，整数部分每 3 位插逗号（`NativeFormatNumberFunction.cpp:81-85,100-129`） | 正常 |
| AC-3.3 | WHEN grouping 为 false THEN 走 `FormatDecimal`，输出无千分位分隔（`NativeFormatNumberFunction.cpp:83-85`） | 正常 |
| AC-3.4 | WHEN grouping 有效但非 bool THEN 返回 `""`（`NativeFormatNumberFunction.cpp:74-77`） | 异常 |

### US-4: 舍入与负数

**作为** 生成式 UI 宿主开发者,
**我想要** 数值经定点舍入与符号保留,
**以便** 结果可预期。

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-4.1 | WHEN value 为正数 THEN `FormatDecimal` 经 `std::round(value*10^decimals)/10^decimals` 舍入后 `std::fixed`+`setprecision(decimals)` 输出（`NativeFormatNumberFunction.cpp:90-98`） | 正常 |
| AC-4.2 | WHEN value 为负数且 grouping=true THEN `FormatWithGrouping` 取绝对值分组后补 `-` 前缀（`NativeFormatNumberFunction.cpp:102,125-127`） | 正常 |
| AC-4.3 | WHEN value 为负数且 grouping=false THEN `FormatDecimal` 直接输出带 `-` 号的定点数（`NativeFormatNumberFunction.cpp:90-98`） | 正常 |

### US-5: 非法入参处理

**作为** 生成式 UI 宿主开发者,
**我想要** 非法入参返回空字符串而非抛异常,
**以便** 渲染过程不崩溃。

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-5.1 | WHEN `resolvedArgs` 非对象 THEN 返回 `FunctionResult("")`（`NativeFormatNumberFunction.cpp:55-57`） | 异常 |
| AC-5.2 | WHEN value 非 number THEN 返回 `FunctionResult("")`（`NativeFormatNumberFunction.cpp:59-62`） | 异常 |

## 验收追溯

| AC编号 | 关联规则 | 关联 Task | 验证方式 | 证据 |
|----|---------|----------|---------|------|
| AC-1.1,AC-1.2,AC-1.3 | R-1 | T-2 | ArkTS 单测 + C++ 静态比对：目录注册 | `FormatNumberFunction.ets:25-36`、`NativeFunctionRegistry.cpp:74` |
| AC-2.1,AC-2.2,AC-2.3,AC-2.4 | R-2 | T-2 | C++ UT：`ParseDecimals` | `NativeFormatNumberFunction.cpp:29-44` |
| AC-3.1,AC-3.2,AC-3.3,AC-3.4 | R-3 | T-2 | C++ UT：`FormatWithGrouping` | `NativeFormatNumberFunction.cpp:100-129` |
| AC-4.1,AC-4.2,AC-4.3 | R-4 | T-2 | C++ UT：`FormatDecimal` | `NativeFormatNumberFunction.cpp:90-98` |
| AC-5.1,AC-5.2 | R-5 | T-2 | C++ UT：非法入参 | `NativeFormatNumberFunction.cpp:53-88` |

## 规则定义

| 规则ID | 类型 | 触发条件 | 预期行为 | 边界/约束 | 关联AC |
|--------|------|---------|---------|----------|--------|
| R-1 | 行为 | 调用 `asFunctionItem()` | 返回 `name='formatNumber'`、`isInnerNative=true` 目录项 | 仅内部注册 | AC-1.1,AC-1.2,AC-1.3 |
| R-2 | 边界 | decimals 取值 | 缺省 2；负数取绝对值；\|x\|>20 或非有限 → `""` | 上限 20 | AC-2.1,AC-2.2,AC-2.3,AC-2.4 |
| R-3 | 行为 | grouping 取值 | 缺省 false；true 千分位逗号；非 bool → `""` | 千分位固定逗号 | AC-3.1,AC-3.2,AC-3.3,AC-3.4 |
| R-4 | 行为 | 数值舍入 | `std::round` 四舍五入后定点输出 | 负数保留符号 | AC-4.1,AC-4.2,AC-4.3 |
| R-5 | 异常 | args 非对象或 value 非 number | 返回 `""` | 统一空串 | AC-5.1,AC-5.2 |

## 验证映射

| 编号 | 对应规格项 | 验证方式 | 验证重点 |
|------|----------|---------|---------|
| VM-1 | AC-1.1,AC-1.2,AC-1.3 目录注册 | ArkTS 单测/静态比对 | name/isInnerNative/schema |
| VM-2 | AC-2.1,AC-2.2,AC-2.3,AC-2.4 decimals | C++ UT | 默认 2/绝对值/上限 20 |
| VM-3 | AC-3.1,AC-3.2,AC-3.3,AC-3.4 grouping | C++ UT | 千分位/默认 false/非 bool |
| VM-4 | AC-4.1,AC-4.2,AC-4.3 舍入与负数 | C++ UT | std::round/负号 |
| VM-5 | AC-5.1,AC-5.2 非法入参 | C++ UT | 非对象/非 number |

## API 变更分析

> 存量补录，无新增/变更 Public API。函数经内部 `InnerFunctionItem` 注册。

### 新增 API

N/A。

### 变更/废弃 API

| API 名称 | 变更类型 | 影响场景 | 迁移指引 | 关联 AC |
|----------|---------|---------|---------|--------|
| `formatNumberFunction.asFunctionItem()`（内部） | 既有 | 函数目录项构造 | 不直接暴露给宿主 | AC-1.1,AC-1.2 |
| `NativeFormatNumberFunction::FormatDecimal/FormatWithGrouping`（内部） | 既有 | 数值格式化 | 框架内部；formatCurrency 复用 `FormatWithGrouping` | AC-3.1,AC-3.2,AC-3.3,AC-3.4,AC-4.1,AC-4.2,AC-4.3 |

> d.ts 位置：`genui/src/main/ets/core/functions/format/FormatNumberFunction.ets`。Kit：`@arkui-genius/genui`；权限：无。

## 接口规格

### 接口定义

**`formatNumberFunction.asFunctionItem()`（内部，`FormatNumberFunction.ets:25`）**

| 属性 | 值 |
|------|-----|
| 函数签名 | `asFunctionItem(): InnerFunctionItem` |
| 返回值 | `InnerFunctionItem` — name=`formatNumber`、isInnerNative=true |
| 开放范围 | 内部（framework-internal） |
| 错误码 | N/A |
| 关联 AC | AC-1.1,AC-1.2 |

**`NativeFormatNumberFunction::Execute(resolvedArgs)`（`NativeFormatNumberFunction.cpp:53`）**

| 属性 | 值 |
|------|-----|
| 函数签名 | `FunctionResult Execute(const JsonValue& resolvedArgs)` |
| 返回值 | `FunctionResult` — 格式化字符串；非法入参返回 `""` |
| 开放范围 | 内部 |
| 错误码 | N/A |
| 关联 AC | AC-2.1,AC-2.2,AC-2.3,AC-2.4,AC-3.1,AC-3.2,AC-3.3,AC-3.4,AC-4.1,AC-4.2,AC-4.3,AC-5.1,AC-5.2 |

**参数约束**

| 参数 | 类型 | 必填 | 默认值 | 约束条件 |
|------|------|------|--------|---------|
| value | number | 是 | — | 任意有限数值 |
| decimals | number | 否 | 2 | `\|x\|<=20`，负数取绝对值，取整 |
| grouping | boolean | 否 | false | true 启用千分位逗号 |

**行为场景**

| # | 触发条件 | 预期行为 | 关联 AC |
|---|----------|----------|---------|
| 1 | value=1234.567, decimals 缺省 | "1234.57"（舍入到 2 位） | AC-2.1,AC-4.1 |
| 2 | value=1234567.89, grouping=true | "1,234,567.89" | AC-3.2 |
| 3 | value=1234567.89, grouping 缺省 | "1234567.89" | AC-3.3 |
| 4 | decimals=-2 | 等同 decimals=2 | AC-2.2 |
| 5 | decimals=25 | 返回 "" | AC-2.3 |
| 6 | value=-1234.5, grouping=true | "-1,234.50" | AC-4.2 |

## 兼容性声明

- **已有 API 行为变更:** 否（存量补录）。
- **配置文件格式变更:** 否。
- **数据存储格式变更:** 否。
- **最低支持版本:** A2UI 原生协议 v0.9。
- **API 版本号策略:** schema `formatNumber.json:17` 描述 decimals「Defaults to 0 or 2 depending on locale」、`formatNumber.json:21` grouping「Defaults to true」，但代码固定 decimals=2（`.cpp:65`）、grouping=false（`.cpp:71`），以代码为准（RISK-1）。

## 架构约束

| 关键约束 | 约束说明 | 影响 AC |
|---------|---------|--------|
| decimals 上限 20 | 超出或非有限值返回空串 | AC-2.3 |
| 千分位固定逗号 | 不随 locale 本地化（RISK-3） | AC-3.2 |
| 统一空串降级 | 非法入参返回 `""`，不抛异常 | AC-5.1,AC-5.2 |

## 非功能性需求

| 类型 | 指标/阈值 | 验证方式 | 证据 |
|------|----------|---------|------|
| 可靠性 | 非法 decimals/grouping 不崩溃 | C++ UT | `NativeFormatNumberFunction.cpp:29-44,74-77` |
| 性能 | 分组为单遍逆序遍历 | C++ UT | `NativeFormatNumberFunction.cpp:114-122` |
| 可测试性 | `FormatDecimal/FormatWithGrouping` 为静态纯函数 | C++ UT | `NativeFormatNumberFunction.h:30-31` |

## 多设备适配声明

| 设备类型 | 行为差异 | 规格/约束 | 验证方式 | 证据 |
|---------|---------|----------|---------|------|
| 手机 | 无差异 | 数值格式化与设备无关 | ohosTest | — |
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
| 生态兼容 | 是 | A2UI 原生协议 v0.9 formatNumber 兼容 | `formatNumber.json` |

## 行为场景（可选，Gherkin）

```gherkin
Feature: formatNumber 函数
  作为 生成式 UI 宿主开发者
  我想要 数值定点格式化与千分位分隔
  以便 生成可读的数字文本

  Scenario: 缺省精度舍入
    Given value = 1234.567
    When 调用 formatNumber 未指定 decimals
    Then 返回 "1234.57"

  Scenario Outline: decimals 边界
    Given value = 3.14159
    When 调用 formatNumber(decimals: <d>)
    Then 返回 <out>

    Examples:
      | d  | out      |
      | 0  | "3"      |
      | 2  | "3.14"   |
      | 25 | ""       |
```

## Spec 自审清单

- [x] 无"待定""TBD""TODO"等占位符
- [x] 所有 AC 使用 WHEN/THEN 格式，可独立测试
- [x] 范围边界明确（Feat-02 做 formatNumber；货币格式化归 Feat-03）
- [x] 无语义模糊表述
- [x] AC 与规则表交叉一致（每个 AC 至少关联一条规则，每条规则至少关联一个 AC）
- [x] 规则表每条通过 5 项质量检查（可复现/可观测/边界值/关联AC/无冲突）

## context-references

```yaml
context-queries:
  - repo: "GenerativeUI/A2UIRender"
    query: "FormatNumberFunction asFunctionItem formatNumber.json 目录注册"
  - repo: "GenerativeUI/A2UIRender"
    query: "NativeFormatNumberFunction ParseDecimals FormatDecimal FormatWithGrouping decimals grouping 默认值"
```

**关键文档：** `genui/src/main/ets/core/functions/format/FormatNumberFunction.ets`、`genui/src/main/cpp/functions/impl/NativeFormatNumberFunction.cpp`、`genui/src/main/cpp/functions/NativeFormatNumberFunction.h`、`genui/src/main/resources/rawfile/schema/A2UI/v0.9/functions/formatNumber.json`