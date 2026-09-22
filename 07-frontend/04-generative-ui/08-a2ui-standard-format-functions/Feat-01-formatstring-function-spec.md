# 特性规格

> Func-07-04-08-Feat-01 formatString 函数：固化 A2UI 标准协议模板字符串格式化函数——目录注册（`name='formatString'`、`isInnerNative=true`）、`${expression}` 占位符运行时插值（数据路径 `ResolveDataPathExpression` 与函数调用 `ResolveFunctionCall` 二态）、`\${` 逃逸与字面量原样输出、缺数据路径经 `ReportMissingPath` 上报。基准实现：`@arkui-genius/genui`（A2UIRender）。

## 概述

| 属性 | 值 |
|------|-----|
| 特性名称 | formatString 函数 |
| 特性编号 | Func-07-04-08-Feat-01 |
| 优先级 | P0 |
| 目标版本 | A2UI 原生协议 v0.9 |
| SIG 归属 | GenUI SIG |
| 状态 | Baselined |
| 复杂度 | 标准 |

## 本次变更范围（Delta）

| 类型 | 内容 | 说明 |
|------|------|------|
| ADDED | 无（存量补录） | 本特性为 Func-07-04-08 首个 Feat，作为该功能域 design.md 基线 |

## 输入文档

| 文档 | 路径 | 状态 |
|------|------|------|
| Design | `07-frontend/04-generative-ui/08-a2ui-standard-format-functions/design.md` | Baselined |
| 目录注册（ArkTS） | `genui/src/main/ets/core/functions/format/FormatStringFunction.ets` | — |
| 聚合注册（ArkTS） | `genui/src/main/ets/core/functions/A2UIBasicFunctions.ets` | — |
| 函数实现（C++） | `genui/src/main/cpp/functions/impl/NativeFormatStringFunction.cpp` | — |
| 函数声明（C++） | `genui/src/main/cpp/functions/NativeFormatStringFunction.h` | — |
| 函数 Schema | `genui/src/main/resources/rawfile/schema/A2UI/v0.9/functions/formatString.json` | 契约 |
| 函数参考（Docs） | `reference/functions/format.md` | 理解辅助 |

> 需求基线、不涉及项详见 proposal.md。design.md 与本文档并行产出，互不依赖。

---

## 用户故事

### US-1: formatString 目录注册与类型识别

**作为** 生成式 UI 宿主开发者,
**我想要** 引擎将 `call: "formatString"` 识别为标准原生函数,
**以便** 服务端下发的模板字符串函数被正确执行。

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-1.1 | WHEN 调用 `formatStringFunction.asFunctionItem()` THEN 返回 `InnerFunctionItem`，其 `name='formatString'`、`isInnerNative=true`、`functionCall=undefined`（`FormatStringFunction.ets:25-31`） | 正常 |
| AC-1.2 | WHEN schemaProvider 以 version 参数被调用 THEN 经 `loadFunctionSchema(version, 'formatString.json')` 返回 formatString schema（`FormatStringFunction.ets:34-36`） | 正常 |
| AC-1.3 | WHEN `A2UIBasicFunctions.standardBuiltinFunctions` 被构造 THEN 数组包含 `formatStringFunction`（`A2UIBasicFunctions.ets:53`） | 正常 |
| AC-1.4 | WHEN `NativeFunctionRegistry` 构造 THEN 经 `Register("formatString", ...)` 注册 `NativeFormatStringFunction`（`NativeFunctionRegistry.cpp:73`） | 正常 |

### US-2: 数据路径占位符插值

**作为** 生成式 UI 宿主开发者,
**我想要** 模板中的 `${path}` 替换为数据模型对应路径的值,
**以便** 动态生成绑定数据的文本。

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-2.1 | WHEN 模板含 `${/user/name}` THEN `ResolveTemplate` 识别占位符并调用 `ResolveDataPathExpression`，输出数据模型中 `/user/name` 的值（`NativeFormatStringFunction.cpp:194-202,331-348`） | 正常 |
| AC-2.2 | WHEN 路径为相对路径（如 `${name}`，不以 `/` 开头） THEN `ResolveDataPathExpression` 自动补 `/` 前缀后取节点（`NativeFormatStringFunction.cpp:339-342`） | 正常 |
| AC-2.3 | WHEN 路径节点缺失 THEN 经 `DynamicValueResolver::ReportMissingPath` 上报并返回 `""`（`NativeFormatStringFunction.cpp:344-347`） | 异常 |
| AC-2.4 | WHEN 数据模型不存在（renderSlot/surface 未找到） THEN `GetDataModel` 返回 nullptr，`ResolveDataPathExpression` 返回 `""`（`NativeFormatStringFunction.cpp:334-337`） | 异常 |

### US-3: 函数调用占位符插值

**作为** 生成式 UI 宿主开发者,
**我想要** 模板中的 `${funcName(arg:'val')}` 替换为函数调用返回值,
**以便** 组合其他函数生成文本。

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-3.1 | WHEN 表达式含 `(` 且以 `)` 结尾 THEN `ResolveTemplate` 走 `ResolveFunctionCall` 分支（`NativeFormatStringFunction.cpp:196-200`） | 正常 |
| AC-3.2 | WHEN 函数名未注册（`HasFunction` 为 false） THEN `ResolveFunctionCall` 返回 `""`（`NativeFormatStringFunction.cpp:314-316`） | 异常 |
| AC-3.3 | WHEN 参数解析失败 THEN `ResolveFunctionCall` 返回 `""`（`NativeFormatStringFunction.cpp:320-322`） | 异常 |
| AC-3.4 | WHEN 函数执行失败（`success=false`） THEN `ResolveFunctionCall` 返回 `""`（`NativeFormatStringFunction.cpp:324-327`） | 异常 |
| AC-3.5 | WHEN 函数返回 string THEN `JsonValueToTemplateOutput` 输出其字符串值（`NativeFormatStringFunction.cpp:78-79,328`） | 正常 |

### US-4: 逃逸与字面量输出

**作为** 生成式 UI 宿主开发者,
**我想要** 模板中 `\${` 输出字面 `${`、其余字面字符原样输出,
**以便** 表达非占位符文本。

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-4.1 | WHEN 模板含 `\${` 序列 THEN `ResolveTemplate` 输出字面 `${` 并跳过三个字符（`NativeFormatStringFunction.cpp:174-179`） | 正常 |
| AC-4.2 | WHEN 字符非 `$` 或 `$` 后非 `{` THEN 该字符原样输出（`NativeFormatStringFunction.cpp:181-185`） | 正常 |
| AC-4.3 | WHEN `${` 后无匹配闭合 `}` THEN 输出字面 `${` 并继续扫描（`NativeFormatStringFunction.cpp:187-191`） | 边界 |

### US-5: 非法入参处理

**作为** 生成式 UI 宿主开发者,
**我想要** 引擎对非法入参返回空字符串而非抛异常,
**以便** 渲染过程不因格式错误崩溃。

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-5.1 | WHEN `resolvedArgs` 非对象 THEN `Execute`/`ExecuteWithContext` 返回 `FunctionResult("")`（`NativeFormatStringFunction.cpp:122-124,137-139`） | 异常 |
| AC-5.2 | WHEN `value` 参数非 string THEN 返回 `FunctionResult("")`（`NativeFormatStringFunction.cpp:127-129,141-144`） | 异常 |
| AC-5.3 | WHEN 走 `Execute`（无 context）THEN 仅做类型校验后原样返回 value 字符串，不做插值（`NativeFormatStringFunction.cpp:126-131`） | 正常 |

## 验收追溯

| AC编号 | 关联规则 | 关联 Task | 验证方式 | 证据 |
|----|---------|----------|---------|------|
| AC-1.1,AC-1.2,AC-1.3,AC-1.4 | R-1 | T-1 | ArkTS 单测 + C++ 静态比对：目录注册 | `FormatStringFunction.ets:25-36`、`NativeFunctionRegistry.cpp:73` |
| AC-2.1,AC-2.2,AC-2.3,AC-2.4 | R-2,R-3 | T-1 | C++ UT：`ResolveTemplate`/`ResolveDataPathExpression` | `NativeFormatStringFunction.cpp:167-210,331-349` |
| AC-3.1,AC-3.2,AC-3.3,AC-3.4,AC-3.5 | R-4 | T-1 | C++ UT：`ResolveFunctionCall` | `NativeFormatStringFunction.cpp:311-329` |
| AC-4.1,AC-4.2,AC-4.3 | R-5 | T-1 | C++ UT：逃逸与字面量 | `NativeFormatStringFunction.cpp:174-191` |
| AC-5.1,AC-5.2,AC-5.3 | R-6 | T-1 | C++ UT：非法入参 | `NativeFormatStringFunction.cpp:120-149` |

## 规则定义

| 规则ID | 类型 | 触发条件 | 预期行为 | 边界/约束 | 关联AC |
|--------|------|---------|---------|----------|--------|
| R-1 | 行为 | 调用 `asFunctionItem()` | 返回 `name='formatString'`、`isInnerNative=true` 目录项 | 仅内部注册 | AC-1.1,AC-1.2,AC-1.3,AC-1.4 |
| R-2 | 行为 | 模板含 `${path}` | 替换为数据模型对应节点值 | 相对路径补 `/` | AC-2.1,AC-2.2 |
| R-3 | 异常 | 数据路径缺失或数据模型不存在 | 经 `ReportMissingPath` 上报并返回 `""` | 不抛异常 | AC-2.3,AC-2.4 |
| R-4 | 异常 | 函数调用名未注册/参数非法/执行失败 | `ResolveFunctionCall` 返回 `""` | 失败静默降级 | AC-3.2,AC-3.3,AC-3.4 |
| R-5 | 边界 | 模板含 `\${` 或未闭合 `${` | 原样输出字面 `${` | 逃逸优先于插值 | AC-4.1,AC-4.2,AC-4.3 |
| R-6 | 异常 | `resolvedArgs` 非对象或 value 非 string | 返回 `FunctionResult("")` | 统一空串 | AC-5.1,AC-5.2 |

## 验证映射

| 编号 | 对应规格项 | 验证方式 | 验证重点 |
|------|----------|---------|---------|
| VM-1 | AC-1.1,AC-1.2,AC-1.3,AC-1.4 目录注册 | ArkTS 单测/静态比对 | name/isInnerNative/schema |
| VM-2 | AC-2.1,AC-2.2,AC-2.3,AC-2.4 数据路径插值 | C++ UT | 绝对/相对路径、缺 path 上报 |
| VM-3 | AC-3.1,AC-3.2,AC-3.3,AC-3.4,AC-3.5 函数调用插值 | C++ UT | 函数分发、失败降级 |
| VM-4 | AC-4.1,AC-4.2,AC-4.3 逃逸/字面量 | C++ UT | `\${`、未闭合 `${` |
| VM-5 | AC-5.1,AC-5.2,AC-5.3 非法入参 | C++ UT | 非对象/非 string 空串 |

## API 变更分析

> 存量补录，无新增/变更 Public API。函数经内部 `InnerFunctionItem` 注册。

### 新增 API

N/A。

### 变更/废弃 API

| API 名称 | 变更类型 | 影响场景 | 迁移指引 | 关联 AC |
|----------|---------|---------|---------|--------|
| `formatStringFunction.asFunctionItem()`（内部） | 既有 | 函数目录项构造 | 不直接暴露给宿主 | AC-1.1,AC-1.2,AC-1.3 |
| `NativeFormatStringFunction::ResolveTemplate/ResolveDataPathExpression/ResolveFunctionCall`（内部） | 既有 | 模板解析 | 框架内部 | AC-2.1,AC-2.2,AC-2.3,AC-2.4,AC-3.1,AC-3.2,AC-3.3,AC-3.4 |

> d.ts 位置：`genui/src/main/ets/core/functions/format/FormatStringFunction.ets`。Kit：`@arkui-genius/genui`；权限：无。

## 接口规格

### 接口定义

**`formatStringFunction.asFunctionItem()`（内部，`FormatStringFunction.ets:25`）**

| 属性 | 值 |
|------|-----|
| 函数签名 | `asFunctionItem(): InnerFunctionItem` |
| 返回值 | `InnerFunctionItem` — name=`formatString`、isInnerNative=true、functionCall=undefined |
| 开放范围 | 内部（framework-internal） |
| 错误码 | N/A |
| 关联 AC | AC-1.1,AC-1.2,AC-1.3 |

**`NativeFormatStringFunction::Execute(resolvedArgs)`（`NativeFormatStringFunction.cpp:120`）**

| 属性 | 值 |
|------|-----|
| 函数签名 | `FunctionResult Execute(const JsonValue& resolvedArgs)` |
| 返回值 | `FunctionResult` — value 原样字符串；非法入参返回 `""` |
| 开放范围 | 内部 |
| 错误码 | N/A |
| 关联 AC | AC-5.1,AC-5.2,AC-5.3 |

**`NativeFormatStringFunction::ExecuteWithContext(resolvedArgs, context)`（`NativeFormatStringFunction.cpp:134`）**

| 属性 | 值 |
|------|-----|
| 函数签名 | `FunctionResult ExecuteWithContext(const JsonValue& resolvedArgs, const DynamicResolveContext& context)` |
| 返回值 | `FunctionResult` — 经 `ResolveTemplate` 插值后的字符串；非法入参返回 `""` |
| 开放范围 | 内部 |
| 错误码 | N/A |
| 关联 AC | AC-2.1,AC-2.2,AC-2.3,AC-2.4,AC-3.1,AC-3.2,AC-3.3,AC-3.4,AC-3.5,AC-4.1,AC-4.2,AC-4.3,AC-5.1,AC-5.2 |

**参数约束**

| 参数 | 类型 | 必填 | 默认值 | 约束条件 |
|------|------|------|--------|---------|
| value | string | 是 | — | 含 `${...}` 占位符的模板字符串 |

**行为场景**

| # | 触发条件 | 预期行为 | 关联 AC |
|---|----------|----------|---------|
| 1 | value 含 `${/path}` | 替换为数据模型路径值 | AC-2.1 |
| 2 | value 含相对路径 `${name}` | 补 `/` 后取节点 | AC-2.2 |
| 3 | value 含 `${func(...)}` | 替换为函数返回值 | AC-3.1,AC-3.5 |
| 4 | value 含 `\${` | 输出字面 `${` | AC-4.1 |
| 5 | value 含未闭合 `${` | 原样输出 `${` | AC-4.3 |
| 6 | 路径缺失 | 上报并返回 `""` | AC-2.3 |
| 7 | value 非 string | 返回 `""` | AC-5.2 |

## 兼容性声明

- **已有 API 行为变更:** 否（存量补录）。
- **配置文件格式变更:** 否。
- **数据存储格式变更:** 否。
- **最低支持版本:** A2UI 原生协议 v0.9。
- **API 版本号策略:** 函数 schema 由 `functions/formatString.json` 声明（value 为 `DynamicString`，required）。

## 架构约束

| 关键约束 | 约束说明 | 影响 AC |
|---------|---------|--------|
| 原生函数三层落地 | 注册（ArkTS）→ Schema → 实现（C++） | AC-1.1,AC-1.2,AC-1.3,AC-1.4 |
| 运行时解析 | 模板在 C++ 运行时解析，非 JS 模板语义 | AC-2.1,AC-2.2,AC-2.3,AC-2.4,AC-3.1,AC-3.2,AC-3.3,AC-3.4,AC-3.5,AC-4.1,AC-4.2,AC-4.3 |
| 统一空串降级 | 非法入参/缺路径一律返回 `""`，不抛异常 | AC-5.1,AC-5.2,AC-5.3,AC-2.3,AC-2.4,AC-3.1,AC-3.2,AC-3.3,AC-3.4 |

## 非功能性需求

| 类型 | 指标/阈值 | 验证方式 | 证据 |
|------|----------|---------|------|
| 可靠性 | 非法入参不崩溃，返回空串 | C++ UT | `NativeFormatStringFunction.cpp:120-149` |
| 性能 | 模板单遍扫描（无回溯解析） | C++ UT | `NativeFormatStringFunction.cpp:167-210` |
| 可测试性 | 解析逻辑为纯函数 | C++ UT | `NativeFormatStringFunction.cpp:151-349` |

## 多设备适配声明

| 设备类型 | 行为差异 | 规格/约束 | 验证方式 | 证据 |
|---------|---------|----------|---------|------|
| 手机 | 无差异 | 模板插值与设备无关 | ohosTest | — |
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
| 生态兼容 | 是 | A2UI 原生协议 v0.9 formatString 兼容 | `formatString.json` |

## 行为场景（可选，Gherkin）

```gherkin
Feature: formatString 函数
  作为 生成式 UI 宿主开发者
  我想要 模板占位符运行时插值
  以便 动态生成绑定数据的文本

  Scenario: 数据路径插值
    Given 数据模型 /user/name = "Alice"
    When 调用 formatString(value: "您好，${/user/name}！")
    Then 返回 "您好，Alice！"

  Scenario: 字面量逃逸
    Given 模板为 "转义 \\${literal}"
    When 调用 formatString
    Then 返回 "转义 ${literal}"

  Scenario: 缺路径降级为空串
    Given 数据模型无 /missing 路径
    When 调用 formatString(value: "${/missing}")
    Then 返回 "" 并经 ReportMissingPath 上报
```

## Spec 自审清单

- [x] 无"待定""TBD""TODO"等占位符
- [x] 所有 AC 使用 WHEN/THEN 格式，可独立测试
- [x] 范围边界明确（Feat-01 做 formatString 模板插值；其余格式化函数归 Feat-02~05）
- [x] 无语义模糊表述
- [x] AC 与规则表交叉一致（每个 AC 至少关联一条规则，每条规则至少关联一个 AC）
- [x] 规则表每条通过 5 项质量检查（可复现/可观测/边界值/关联AC/无冲突）

## context-references

```yaml
context-queries:
  - repo: "GenerativeUI/A2UIRender"
    query: "FormatStringFunction asFunctionItem isInnerNative formatString.json 目录注册"
  - repo: "GenerativeUI/A2UIRender"
    query: "NativeFormatStringFunction ResolveTemplate ResolveDataPathExpression ResolveFunctionCall 逃逸"
  - repo: "GenerativeUI/A2UIRender"
    query: "DynamicValueResolver ReportMissingPath formatString 缺数据路径"
```

**关键文档：** `genui/src/main/ets/core/functions/format/FormatStringFunction.ets`、`genui/src/main/cpp/functions/impl/NativeFormatStringFunction.cpp`、`genui/src/main/cpp/functions/NativeFormatStringFunction.h`、`genui/src/main/resources/rawfile/schema/A2UI/v0.9/functions/formatString.json`
