# 特性规格

> Func-07-04-08-Feat-04 formatDate 函数：固化 A2UI 标准协议日期格式化函数——目录注册（`name='formatDate'`、`isInnerNative=true`）、ISO 8601 解析（`ParseISO8601`）、Unicode TR35 模式子集（y/M/d/E/H/h/m/s/a）run-length 扫描（`ApplyPattern`）、字面量原样输出、月/周名称硬编码英文。基准实现：`@arkui-genius/genui`（A2UIRender）。

## 概述

| 属性 | 值 |
|------|-----|
| 特性名称 | formatDate 函数 |
| 特性编号 | Func-07-04-08-Feat-04 |
| 优先级 | P0 |
| 目标版本 | A2UI 原生协议 v0.9 |
| SIG 归属 | GenUI SIG |
| 状态 | Baselined |
| 复杂度 | 标准 |

## 本次变更范围（Delta）

| 类型 | 内容 | 说明 |
|------|------|------|
| ADDED | 无（存量补录） | 本特性为 Func-07-04-08 第四个 Feat |

## 输入文档

| 文档 | 路径 | 状态 |
|------|------|------|
| Design | `07-frontend/04-generative-ui/08-a2ui-standard-format-functions/design.md` | Baselined |
| 目录注册（ArkTS） | `genui/src/main/ets/core/functions/format/FormatDateFunction.ets` | — |
| 聚合注册（ArkTS） | `genui/src/main/ets/core/functions/A2UIBasicFunctions.ets` | — |
| 函数实现（C++） | `genui/src/main/cpp/functions/impl/NativeFormatDateFunction.cpp` | — |
| 函数声明（C++） | `genui/src/main/cpp/functions/NativeFormatDateFunction.h` | — |
| 函数 Schema | `genui/src/main/resources/rawfile/schema/A2UI/v0.9/functions/formatDate.json` | 契约 |
| 函数参考（Docs） | `reference/functions/format.md` | 理解辅助 |

> 需求基线、不涉及项详见 proposal.md。design.md 与本文档并行产出，互不依赖。

---

## 用户故事

### US-1: formatDate 目录注册与类型识别

**作为** 生成式 UI 宿主开发者,
**我想要** 引擎将 `call: "formatDate"` 识别为标准原生函数,
**以便** 服务端下发的日期格式化函数被正确执行。

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-1.1 | WHEN 调用 `formatDateFunction.asFunctionItem()` THEN 返回 `name='formatDate'`、`isInnerNative=true` 的 `InnerFunctionItem`（`FormatDateFunction.ets:25-31`） | 正常 |
| AC-1.2 | WHEN schemaProvider 被调用 THEN 经 `loadFunctionSchema(version, 'formatDate.json')` 返回 schema（`FormatDateFunction.ets:34-36`） | 正常 |
| AC-1.3 | WHEN `NativeFunctionRegistry` 构造 THEN 经 `Register("formatDate", ...)` 注册（`NativeFunctionRegistry.cpp:76`） | 正常 |

### US-2: ISO 8601 解析

**作为** 生成式 UI 宿主开发者,
**我想要** 引擎解析 ISO 8601 日期字符串,
**以便** 提取年月日（与可选的时分秒）。

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-2.1 | WHEN value 为 `"2026-05-19"` THEN `ParseISO8601` 解析出 year=2026、month=5、day=19（`NativeFormatDateFunction.cpp:200-215`） | 正常 |
| AC-2.2 | WHEN value 为 `"2026-05-19T14:30:00"` THEN 额外解析 hour=14、minute=30、second=0（`NativeFormatDateFunction.cpp:217-226`） | 正常 |
| AC-2.3 | WHEN value 长度 < 10 或 `iso[4]!='-'`/`iso[7]!='-'` THEN `ParseISO8601` 返回 false，`Execute` 返回 `""`（`NativeFormatDateFunction.cpp:200-206,190-192`） | 异常 |
| AC-2.4 | WHEN value 含 `T` 但长度 < 16 THEN 仅解析年月日，不解析时间（`NativeFormatDateFunction.cpp:217-236`） | 边界 |

### US-3: 模式 token 格式化

**作为** 生成式 UI 宿主开发者,
**我想要** 通过 TR35 模式字符格式化日期,
**以便** 控制年月日时分秒与周几的输出形式。

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-3.1 | WHEN pattern 为 `"yyyy"` THEN `AppendYear` 输出四位年份（runLength≥3）（`NativeFormatDateFunction.cpp:65-68`） | 正常 |
| AC-3.2 | WHEN pattern 为 `"yy"` THEN 输出两位年份（`year%100` 补零）（`NativeFormatDateFunction.cpp:67`） | 正常 |
| AC-3.3 | WHEN pattern 为 `"MMMM"`/`"MMM"`/`"MM"`/`"M"` THEN `AppendMonth` 分别输出全称/缩写/两位/单月（`NativeFormatDateFunction.cpp:70-82`） | 正常 |
| AC-3.4 | WHEN pattern 为 `"HH"`/`"hh"`/`"mm"`/`"ss"`/`"a"` THEN 分别输出 24 时/12 时/分钟/秒/AM-PM（`NativeFormatDateFunction.cpp:99-143`） | 正常 |

### US-4: 字面量与未知字符

**作为** 生成式 UI 宿主开发者,
**我想要** 模式中非模式字符（含中文/空格/标点）原样输出,
**以便** 生成自然语言日期文本。

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-4.1 | WHEN pattern 含非模式字符（如 `"yyyy年MM月dd日"` 中的 `年/月/日`） THEN `AppendLiteral` 原样输出（`NativeFormatDateFunction.cpp:159-164,252-256`） | 正常 |
| AC-4.2 | WHEN pattern 为纯字面量（如 `"今天是周几"`） THEN 整串原样输出（`NativeFormatDateFunction.cpp:241-261`） | 正常 |

### US-5: 非法入参处理

**作为** 生成式 UI 宿主开发者,
**我想要** 非法 value/format 返回空字符串而非抛异常,
**以便** 渲染过程不崩溃。

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-5.1 | WHEN `resolvedArgs` 非对象 THEN 返回 `FunctionResult("")`（`NativeFormatDateFunction.cpp:173-175`） | 异常 |
| AC-5.2 | WHEN value 或 format 非 string THEN 返回 `""`（`NativeFormatDateFunction.cpp:177-181`） | 异常 |
| AC-5.3 | WHEN value 或 format 为空字符串 THEN 返回 `""`（`NativeFormatDateFunction.cpp:183-187`） | 边界 |

## 验收追溯

| AC编号 | 关联规则 | 关联 Task | 验证方式 | 证据 |
|----|---------|----------|---------|------|
| AC-1.1,AC-1.2,AC-1.3 | R-1 | T-4 | ArkTS 单测 + C++ 静态比对：目录注册 | `FormatDateFunction.ets:25-36`、`NativeFunctionRegistry.cpp:76` |
| AC-2.1,AC-2.2,AC-2.3,AC-2.4 | R-2 | T-4 | C++ UT：`ParseISO8601` | `NativeFormatDateFunction.cpp:198-239` |
| AC-3.1,AC-3.2,AC-3.3,AC-3.4 | R-3 | T-4 | C++ UT：`ApplyPattern` token | `NativeFormatDateFunction.cpp:65-147` |
| AC-4.1,AC-4.2 | R-4 | T-4 | C++ UT：字面量输出 | `NativeFormatDateFunction.cpp:159-164,241-261` |
| AC-5.1,AC-5.2,AC-5.3 | R-5 | T-4 | C++ UT：非法入参 | `NativeFormatDateFunction.cpp:171-196` |

## 规则定义

| 规则ID | 类型 | 触发条件 | 预期行为 | 边界/约束 | 关联AC |
|--------|------|---------|---------|----------|--------|
| R-1 | 行为 | 调用 `asFunctionItem()` | 返回 `name='formatDate'`、`isInnerNative=true` 目录项 | 仅内部注册 | AC-1.1,AC-1.2,AC-1.3 |
| R-2 | 行为 | value 为 ISO 8601 | 解析年月日（可选时分秒） | 最短 10 字符、`-` 分隔 | AC-2.1,AC-2.2,AC-2.3,AC-2.4 |
| R-3 | 行为 | pattern 含模式 token | run-length 扫描，token 映射到 formatter | token 集 y/M/d/E/H/h/m/s/a | AC-3.1,AC-3.2,AC-3.3,AC-3.4 |
| R-4 | 行为 | pattern 含非模式字符 | 字面量原样输出 | 支持中文/空格/标点 | AC-4.1,AC-4.2 |
| R-5 | 异常 | value/format 非 string 或空/无法解析 | 返回 `""` | 不抛异常 | AC-5.1,AC-5.2,AC-5.3,AC-2.3 |

## 验证映射

| 编号 | 对应规格项 | 验证方式 | 验证重点 |
|------|----------|---------|---------|
| VM-1 | AC-1.1,AC-1.2,AC-1.3 目录注册 | ArkTS 单测/静态比对 | name/isInnerNative/schema |
| VM-2 | AC-2.1,AC-2.2,AC-2.3,AC-2.4 ISO 解析 | C++ UT | 年月日/时分秒/非法格式 |
| VM-3 | AC-3.1,AC-3.2,AC-3.3,AC-3.4 模式 token | C++ UT | y/M/d/E/H/h/m/s/a |
| VM-4 | AC-4.1,AC-4.2 字面量 | C++ UT | 中文/标点原样 |
| VM-5 | AC-5.1,AC-5.2,AC-5.3 非法入参 | C++ UT | 非 string/空串 |

## API 变更分析

> 存量补录，无新增/变更 Public API。函数经内部 `InnerFunctionItem` 注册。

### 新增 API

N/A。

### 变更/废弃 API

| API 名称 | 变更类型 | 影响场景 | 迁移指引 | 关联 AC |
|----------|---------|---------|---------|--------|
| `formatDateFunction.asFunctionItem()`（内部） | 既有 | 函数目录项构造 | 不直接暴露给宿主 | AC-1.1,AC-1.2 |
| `NativeFormatDateFunction::ParseISO8601/ApplyPattern`（内部） | 既有 | 日期解析与格式化 | 框架内部；静态公开方法 | AC-2.1,AC-2.2,AC-2.3,AC-2.4,AC-3.1,AC-3.2,AC-3.3,AC-3.4,AC-4.1,AC-4.2 |

> d.ts 位置：`genui/src/main/ets/core/functions/format/FormatDateFunction.ets`。Kit：`@arkui-genius/genui`；权限：无。

## 接口规格

### 接口定义

**`formatDateFunction.asFunctionItem()`（内部，`FormatDateFunction.ets:25`）**

| 属性 | 值 |
|------|-----|
| 函数签名 | `asFunctionItem(): InnerFunctionItem` |
| 返回值 | `InnerFunctionItem` — name=`formatDate`、isInnerNative=true |
| 开放范围 | 内部（framework-internal） |
| 错误码 | N/A |
| 关联 AC | AC-1.1,AC-1.2 |

**`NativeFormatDateFunction::Execute(resolvedArgs)`（`NativeFormatDateFunction.cpp:171`）**

| 属性 | 值 |
|------|-----|
| 函数签名 | `FunctionResult Execute(const JsonValue& resolvedArgs)` |
| 返回值 | `FunctionResult` — 格式化日期字符串；非法入参返回 `""` |
| 开放范围 | 内部 |
| 错误码 | N/A |
| 关联 AC | AC-2.1,AC-2.2,AC-2.3,AC-2.4,AC-3.1,AC-3.2,AC-3.3,AC-3.4,AC-4.1,AC-4.2,AC-5.1,AC-5.2,AC-5.3 |

**`NativeFormatDateFunction::ParseISO8601(iso, parts)`（`NativeFormatDateFunction.h:39`、`.cpp:198`）**

| 属性 | 值 |
|------|-----|
| 函数签名 | `static bool ParseISO8601(const std::string& iso, DateTimeParts& parts)` |
| 返回值 | `bool` — 解析成功；长度不足/分隔符错误/数字解析异常返回 false |
| 开放范围 | 内部 |
| 错误码 | N/A |
| 关联 AC | AC-2.1,AC-2.2,AC-2.3,AC-2.4 |

**`NativeFormatDateFunction::ApplyPattern(parts, pattern)`（`NativeFormatDateFunction.h:40`、`.cpp:241`）**

| 属性 | 值 |
|------|-----|
| 函数签名 | `static std::string ApplyPattern(const DateTimeParts& parts, const std::string& pattern)` |
| 返回值 | `std::string` — 模式格式化结果 |
| 开放范围 | 内部 |
| 错误码 | N/A |
| 关联 AC | AC-3.1,AC-3.2,AC-3.3,AC-3.4,AC-4.1,AC-4.2 |

**参数约束**

| 参数 | 类型 | 必填 | 默认值 | 约束条件 |
|------|------|------|--------|---------|
| value | string | 是 | — | ISO 8601（`YYYY-MM-DD[THH:MM:SS]`） |
| format | string | 是 | — | 非空 TR35 模式字符串 |

**行为场景**

| # | 触发条件 | 预期行为 | 关联 AC |
|---|----------|----------|---------|
| 1 | value="2026-05-19", format="yyyy-MM-dd" | "2026-05-19" | AC-2.1,AC-3.1 |
| 2 | value="2026-05-19T14:30:00", format="HH:mm" | "14:30" | AC-2.2,AC-3.4 |
| 3 | format="yyyy年MM月dd日 HH:mm" | 中文年月日 + 时分原样输出 | AC-4.1 |
| 4 | value="2026-01" | ""（长度不足） | AC-2.3 |
| 5 | value 非 string | "" | AC-5.2 |

## 兼容性声明

- **已有 API 行为变更:** 否（存量补录）。
- **配置文件格式变更:** 否。
- **数据存储格式变更:** 否。
- **最低支持版本:** A2UI 原生协议 v0.9。
- **API 版本号策略:** 函数 schema 由 `functions/formatDate.json` 声明（value/format 均 required）。月/周名称硬编码英文（RISK-5），不随系统 locale 本地化。

## 架构约束

| 关键约束 | 约束说明 | 影响 AC |
|---------|---------|--------|
| TR35 模式子集 | 仅支持 y/M/d/E/H/h/m/s/a token，其余原样输出 | AC-3.1,AC-3.2,AC-3.3,AC-3.4,AC-4.1,AC-4.2 |
| 英文月/周名 | 硬编码英文数组，不本地化（RISK-5） | AC-3.3 |
| 统一空串降级 | 非法 value/format 返回 `""`，不抛异常 | AC-5.1,AC-5.2,AC-5.3 |

## 非功能性需求

| 类型 | 指标/阈值 | 验证方式 | 证据 |
|------|----------|---------|------|
| 可靠性 | 非法日期格式不崩溃 | C++ UT | `NativeFormatDateFunction.cpp:208-235` |
| 性能 | 模式单遍 run-length 扫描 | C++ UT | `NativeFormatDateFunction.cpp:241-261` |
| 可测试性 | `ParseISO8601/ApplyPattern` 为静态纯函数 | C++ UT | `NativeFormatDateFunction.h:39-40` |

## 多设备适配声明

| 设备类型 | 行为差异 | 规格/约束 | 验证方式 | 证据 |
|---------|---------|----------|---------|------|
| 手机 | 无差异 | 日期格式化与设备无关 | ohosTest | — |
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
| 生态兼容 | 是 | A2UI 原生协议 v0.9 formatDate 兼容 | `formatDate.json` |

## 行为场景（可选，Gherkin）

```gherkin
Feature: formatDate 函数
  作为 生成式 UI 宿主开发者
  我想要 ISO 8601 日期按模式格式化
  以便 生成本地化的日期文本

  Scenario: 中文模式格式化
    Given value = "2026-05-19T14:30:00"
    When 调用 formatDate(format: "yyyy年MM月dd日 HH:mm")
    Then 返回 "2026年05月19日 14:30"

  Scenario Outline: 非法日期降级
    Given value = <iso>
    When 调用 formatDate(format: "yyyy-MM-dd")
    Then 返回 ""

    Examples:
      | iso           |
      | "2026-01"     |
      | "2026/01/16"  |
```

## Spec 自审清单

- [x] 无"待定""TBD""TODO"等占位符
- [x] 所有 AC 使用 WHEN/THEN 格式，可独立测试
- [x] 范围边界明确（Feat-04 做 formatDate；本地化月名未覆盖）
- [x] 无语义模糊表述
- [x] AC 与规则表交叉一致（每个 AC 至少关联一条规则，每条规则至少关联一个 AC）
- [x] 规则表每条通过 5 项质量检查（可复现/可观测/边界值/关联AC/无冲突）

## context-references

```yaml
context-queries:
  - repo: "GenerativeUI/A2UIRender"
    query: "FormatDateFunction asFunctionItem formatDate.json 目录注册"
  - repo: "GenerativeUI/A2UIRender"
    query: "NativeFormatDateFunction ParseISO8601 ApplyPattern PatternTokenHandler TR35 模式 token"
```

**关键文档：** `genui/src/main/ets/core/functions/format/FormatDateFunction.ets`、`genui/src/main/cpp/functions/impl/NativeFormatDateFunction.cpp`、`genui/src/main/cpp/functions/NativeFormatDateFunction.h`、`genui/src/main/resources/rawfile/schema/A2UI/v0.9/functions/formatDate.json`