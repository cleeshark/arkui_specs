# 特性规格

> Func-07-04-08-Feat-05 pluralize 函数：固化 A2UI 标准协议复数选择函数——目录注册（`name='pluralize'`、`isInnerNative=true`）、基于 CLDR 复数规则族的类别选择（`zero/one/two/few/many/other`，`PLURAL_RULE_MAPPINGS` 22 语言映射）、locale 由 ArkTS i18n provider 回调提供（`CACHE_TTL_MS=1000` 缓存、默认 `"en"`）、缺类别回退 `other`。基准实现：`@arkui-genius/genui`（A2UIRender）。

## 概述

| 属性 | 值 |
|------|-----|
| 特性名称 | pluralize 函数 |
| 特性编号 | Func-07-04-08-Feat-05 |
| 优先级 | P0 |
| 目标版本 | A2UI 原生协议 v0.9 |
| SIG 归属 | GenUI SIG |
| 状态 | Baselined |
| 复杂度 | 标准 |

## 本次变更范围（Delta）

| 类型 | 内容 | 说明 |
|------|------|------|
| ADDED | 无（存量补录） | 本特性为 Func-07-04-08 第五个 Feat |

## 输入文档

| 文档 | 路径 | 状态 |
|------|------|------|
| Design | `07-frontend/04-generative-ui/08-a2ui-standard-format-functions/design.md` | Baselined |
| 目录注册（ArkTS） | `genui/src/main/ets/core/functions/format/PluralizeFunction.ets` | — |
| locale 桥接（ArkTS） | `genui/src/main/ets/core/functions/FunctionBridge.ets` | — |
| 聚合注册（ArkTS） | `genui/src/main/ets/core/functions/A2UIBasicFunctions.ets` | — |
| 函数实现（C++） | `genui/src/main/cpp/functions/impl/NativePluralizeFunction.cpp` | — |
| 函数声明（C++） | `genui/src/main/cpp/functions/NativePluralizeFunction.h` | — |
| locale 注册（C++） | `genui/src/main/cpp/NativeEntry.cpp` | — |
| 函数 Schema | `genui/src/main/resources/rawfile/schema/A2UI/v0.9/functions/pluralize.json` | 契约 |
| 函数参考（Docs） | `reference/functions/format.md` | 理解辅助 |

> 需求基线、不涉及项详见 proposal.md。design.md 与本文档并行产出，互不依赖。

---

## 用户故事

### US-1: pluralize 目录注册与类型识别

**作为** 生成式 UI 宿主开发者,
**我想要** 引擎将 `call: "pluralize"` 识别为标准原生函数,
**以便** 服务端下发的复数选择函数被正确执行。

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-1.1 | WHEN 调用 `pluralizeFunction.asFunctionItem()` THEN 返回 `name='pluralize'`、`isInnerNative=true` 的 `InnerFunctionItem`（`PluralizeFunction.ets:25-31`） | 正常 |
| AC-1.2 | WHEN schemaProvider 被调用 THEN 经 `loadFunctionSchema(version, 'pluralize.json')` 返回 schema（`PluralizeFunction.ets:34-36`） | 正常 |
| AC-1.3 | WHEN `NativeFunctionRegistry` 构造 THEN 经 `Register("pluralize", ...)` 注册（`NativeFunctionRegistry.cpp:77`） | 正常 |

### US-2: locale 获取与缓存

**作为** 生成式 UI 宿主开发者,
**我想要** 引擎根据系统语言选择复数类别,
**以便** 得到符合当前语言习惯的复数形式。

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-2.1 | WHEN `FunctionBridge.install` 执行 THEN 注册 i18n localeProvider 回调（`getSystemLocaleInstance().toString()`）到 native（`FunctionBridge.ets:65-87`） | 正常 |
| AC-2.2 | WHEN native 收到函数类型参数 THEN `RegisterLocale` 走 `RegisterLocaleProvider`；收到字符串则 `SetLocale`（`NativeEntry.cpp:2150-2158`） | 正常 |
| AC-2.3 | WHEN locale 未初始化（providerRef_ 为 null）THEN `CallProvider` 返回 `cachedLocale_`（默认 `"en"`）（`NativePluralizeFunction.cpp:62-64`、`NativePluralizeFunction.h:39`） | 边界 |
| AC-2.4 | WHEN provider 上次调用距今 < 1000ms（`CACHE_TTL_MS`）THEN 直接返回缓存 locale，不再回调（`NativePluralizeFunction.cpp:67-72`、`NativePluralizeFunction.h:41`） | 边界 |

### US-3: 复数类别选择

**作为** 生成式 UI 宿主开发者,
**我想要** 根据数值与语言选择零/单/双/少/多/其他类别,
**以便** 输出正确的复数形式。

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-3.1 | WHEN 语言为 `"en"` 且 value=1 THEN `PluralOneOther` 返回 `"one"`（`NativePluralizeFunction.cpp:122-131`） | 正常 |
| AC-3.2 | WHEN 语言为 `"en"` 且 value=2 THEN 返回 `"other"`（`NativePluralizeFunction.cpp:127-130`） | 正常 |
| AC-3.3 | WHEN 语言为 `"ru"`（俄语族）且 value=2 THEN `PluralOneFewManyOther` 返回 `"few"`（`NativePluralizeFunction.cpp:208-225`） | 正常 |
| AC-3.4 | WHEN 语言未命中映射 THEN `ResolvePluralRule` 回退 `ApplyOneOtherRule`（`NativePluralizeFunction.cpp:559-567`） | 边界 |
| AC-3.5 | WHEN locale 含 `-`（如 `"en-US"`） THEN `GetLanguagePrefix` 提取 `"en"`（`NativePluralizeFunction.cpp:106-113`） | 正常 |

### US-4: 类别文本回退

**作为** 生成式 UI 宿主开发者,
**我想要** 当前类别参数缺失时回退 other,
**以便** 即使未提供完整类别也能输出文本。

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-4.1 | WHEN 当前类别字符串非空 THEN 返回该类别文本（`NativePluralizeFunction.cpp:622-625`） | 正常 |
| AC-4.2 | WHEN 当前类别参数缺失或为空 THEN 回退 `other` 文本（`NativePluralizeFunction.cpp:627-628`） | 边界 |
| AC-4.3 | WHEN other 也缺失/为空 THEN 返回 `""`（`NativePluralizeFunction.cpp:628`） | 边界 |

### US-5: 非法入参处理

**作为** 生成式 UI 宿主开发者,
**我想要** 非法 value/类别参数返回空字符串而非抛异常,
**以便** 渲染过程不崩溃。

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-5.1 | WHEN `resolvedArgs` 非对象 THEN 返回 `FunctionResult("")`（`NativePluralizeFunction.cpp:605-607`） | 异常 |
| AC-5.2 | WHEN value 非 number THEN 返回 `FunctionResult("")`（`NativePluralizeFunction.cpp:609-612`） | 异常 |
| AC-5.3 | WHEN zero/one/two/few/many/other 任一存在但非 string THEN `ValidateOptionalString` 返回 false，`Execute` 返回 `""`（`NativePluralizeFunction.cpp:592-596,613-617`） | 异常 |

## 验收追溯

| AC编号 | 关联规则 | 关联 Task | 验证方式 | 证据 |
|----|---------|----------|---------|------|
| AC-1.1,AC-1.2,AC-1.3 | R-1 | T-5 | ArkTS 单测 + C++ 静态比对：目录注册 | `PluralizeFunction.ets:25-36`、`NativeFunctionRegistry.cpp:77` |
| AC-2.1,AC-2.2,AC-2.3,AC-2.4 | R-2 | T-5 | C++ UT + ohosTest：locale 提供者 | `FunctionBridge.ets:65-87`、`NativePluralizeFunction.cpp:60-104` |
| AC-3.1,AC-3.2,AC-3.3,AC-3.4,AC-3.5 | R-3 | T-5 | C++ UT：复数规则族 | `NativePluralizeFunction.cpp:122-581` |
| AC-4.1,AC-4.2,AC-4.3 | R-4 | T-5 | C++ UT：类别回退 | `NativePluralizeFunction.cpp:622-628` |
| AC-5.1,AC-5.2,AC-5.3 | R-5 | T-5 | C++ UT：非法入参 | `NativePluralizeFunction.cpp:603-629` |

## 规则定义

| 规则ID | 类型 | 触发条件 | 预期行为 | 边界/约束 | 关联AC |
|--------|------|---------|---------|----------|--------|
| R-1 | 行为 | 调用 `asFunctionItem()` | 返回 `name='pluralize'`、`isInnerNative=true` 目录项 | 仅内部注册 | AC-1.1,AC-1.2,AC-1.3 |
| R-2 | 行为 | locale 获取 | 经 i18n provider 回调，TTL 1000ms 缓存，默认 `"en"` | provider 不可用回退缓存 | AC-2.1,AC-2.2,AC-2.3,AC-2.4 |
| R-3 | 行为 | 复数类别判定 | 按语言匹配 `PLURAL_RULE_MAPPINGS`，未命中回退 one/other | 22 语言映射 | AC-3.1,AC-3.2,AC-3.3,AC-3.4,AC-3.5 |
| R-4 | 边界 | 类别文本缺失 | 回退 other；other 也缺返回 `""` | 无异常 | AC-4.1,AC-4.2,AC-4.3 |
| R-5 | 异常 | value 非 number 或类别参数非 string | 返回 `""` | 统一空串 | AC-5.1,AC-5.2,AC-5.3 |

## 验证映射

| 编号 | 对应规格项 | 验证方式 | 验证重点 |
|------|----------|---------|---------|
| VM-1 | AC-1.1,AC-1.2,AC-1.3 目录注册 | ArkTS 单测/静态比对 | name/isInnerNative/schema |
| VM-2 | AC-2.1,AC-2.2,AC-2.3,AC-2.4 locale | C++ UT | provider/缓存 TTL/默认 en |
| VM-3 | AC-3.1,AC-3.2,AC-3.3,AC-3.4,AC-3.5 复数类别 | C++ UT | en/ru/未命中/语言前缀 |
| VM-4 | AC-4.1,AC-4.2,AC-4.3 类别回退 | C++ UT | other 回退/空串 |
| VM-5 | AC-5.1,AC-5.2,AC-5.3 非法入参 | C++ UT | 非 number/非 string |

## API 变更分析

> 存量补录，无新增/变更 Public API。函数经内部 `InnerFunctionItem` 注册。

### 新增 API

N/A。

### 变更/废弃 API

| API 名称 | 变更类型 | 影响场景 | 迁移指引 | 关联 AC |
|----------|---------|---------|---------|--------|
| `pluralizeFunction.asFunctionItem()`（内部） | 既有 | 函数目录项构造 | 不直接暴露给宿主 | AC-1.1,AC-1.2 |
| `NativePluralizeFunction::Execute`（内部） | 既有 | 复数选择 | 框架内部 | AC-3.1,AC-3.2,AC-3.3,AC-3.4,AC-3.5,AC-4.1,AC-4.2,AC-4.3,AC-5.1,AC-5.2,AC-5.3 |
| `PluralLocaleManager::RegisterLocaleProvider/SetLocale/GetLocale`（内部） | 既有 | locale 桥接 | 框架内部，经 `registerLocale` NAPI | AC-2.1,AC-2.2,AC-2.3,AC-2.4 |

> d.ts 位置：`genui/src/main/ets/core/functions/format/PluralizeFunction.ets`。Kit：`@arkui-genius/genui`；权限：无。

## 接口规格

### 接口定义

**`pluralizeFunction.asFunctionItem()`（内部，`PluralizeFunction.ets:25`）**

| 属性 | 值 |
|------|-----|
| 函数签名 | `asFunctionItem(): InnerFunctionItem` |
| 返回值 | `InnerFunctionItem` — name=`pluralize`、isInnerNative=true |
| 开放范围 | 内部（framework-internal） |
| 错误码 | N/A |
| 关联 AC | AC-1.1,AC-1.2 |

**`NativePluralizeFunction::Execute(resolvedArgs)`（`NativePluralizeFunction.cpp:603`）**

| 属性 | 值 |
|------|-----|
| 函数签名 | `FunctionResult Execute(const JsonValue& resolvedArgs)` |
| 返回值 | `FunctionResult` — 选中类别的字符串；非法入参返回 `""` |
| 开放范围 | 内部 |
| 错误码 | N/A |
| 关联 AC | AC-3.1,AC-3.2,AC-3.3,AC-3.4,AC-3.5,AC-4.1,AC-4.2,AC-4.3,AC-5.1,AC-5.2,AC-5.3 |

**`PluralLocaleManager::GetLocale()`（`NativePluralizeFunction.cpp:101`）**

| 属性 | 值 |
|------|-----|
| 函数签名 | `std::string GetLocale()` |
| 返回值 | `std::string` — 缓存的系统 locale（默认 `"en"`） |
| 开放范围 | 内部 |
| 错误码 | N/A |
| 关联 AC | AC-2.1,AC-2.2,AC-2.3,AC-2.4 |

**参数约束**

| 参数 | 类型 | 必填 | 默认值 | 约束条件 |
|------|------|------|--------|---------|
| value | number | 是 | — | 数量值，用于判定复数类别 |
| zero | string | 否 | 无（回退 other） | 非 string 存在则非法 |
| one | string | 否 | 无（回退 other） | 同上 |
| two | string | 否 | 无（回退 other） | 同上 |
| few | string | 否 | 无（回退 other） | 同上 |
| many | string | 否 | 无（回退 other） | 同上 |
| other | string | 否（schema 标 required） | 无 | 回退目标；缺失返回 `""` |

**行为场景**

| # | 触发条件 | 预期行为 | 关联 AC |
|---|----------|----------|---------|
| 1 | locale="en", value=1, one/other 提供 | 返回 one 文本 | AC-3.1,AC-4.1 |
| 2 | locale="en", value=2 | 类别 other，返回 other | AC-3.2 |
| 3 | locale="ru", value=2 | 类别 few，返回 few | AC-3.3 |
| 4 | locale 未命中映射 | 回退 one/other 规则 | AC-3.4 |
| 5 | 当前类别参数缺失 | 回退 other | AC-4.2 |
| 6 | value 非 number | "" | AC-5.2 |

## 兼容性声明

- **已有 API 行为变更:** 否（存量补录）。
- **配置文件格式变更:** 否。
- **数据存储格式变更:** 否。
- **最低支持版本:** A2UI 原生协议 v0.9。
- **API 版本号策略:** schema `pluralize.json:40-43` 声明 `other` 为 required，但代码未强制校验 other 存在，缺 other 时返回空串（RISK-6），以代码为准。

## 架构约束

| 关键约束 | 约束说明 | 影响 AC |
|---------|---------|--------|
| locale 经 NAPI 回传 | 系统 locale 由 ArkTS i18n provider 回调提供 | AC-2.1,AC-2.2,AC-2.3,AC-2.4 |
| 规则表硬编码 | 22 语言 CLDR 规则族 + 未命中回退 | AC-3.1,AC-3.2,AC-3.3,AC-3.4,AC-3.5 |
| 统一空串降级 | 非法入参或缺 other 返回 `""` | AC-4.3,AC-5.1,AC-5.2,AC-5.3 |

## 非功能性需求

| 类型 | 指标/阈值 | 验证方式 | 证据 |
|------|----------|---------|------|
| 可靠性 | 非法类别参数不崩溃 | C++ UT | `NativePluralizeFunction.cpp:613-617` |
| 性能 | locale 缓存 TTL 1000ms，降低跨语言回调频率 | C++ UT | `NativePluralizeFunction.h:41` |
| 可测试性 | 复数规则族为纯函数 | C++ UT | `NativePluralizeFunction.cpp:122-548` |

## 多设备适配声明

| 设备类型 | 行为差异 | 规格/约束 | 验证方式 | 证据 |
|---------|---------|----------|---------|------|
| 手机 | 无差异（随系统语言变化） | 复数选择随系统 locale | ohosTest | — |
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
| 生态兼容 | 是 | A2UI 原生协议 v0.9 pluralize 兼容 | `pluralize.json` |

## 行为场景（可选，Gherkin）

```gherkin
Feature: pluralize 函数
  作为 生成式 UI 宿主开发者
  我想要 基于数值与语言选择复数形式
  以便 生成符合语法的数量文本

  Scenario: 英语单复数
    Given 系统语言为 en, value = 1
    When 调用 pluralize(one: "1 item", other: "N items")
    Then 返回 "1 item"

  Scenario: 类别缺失回退 other
    Given 系统语言为 en, value = 5, 未提供 tiny
    When 调用 pluralize(one: "1", other: "many")
    Then 返回 "many"
```

## Spec 自审清单

- [x] 无"待定""TBD""TODO"等占位符
- [x] 所有 AC 使用 WHEN/THEN 格式，可独立测试
- [x] 范围边界明确（Feat-05 做 pluralize；locale 本地化细节归系统 i18n）
- [x] 无语义模糊表述
- [x] AC 与规则表交叉一致（每个 AC 至少关联一条规则，每条规则至少关联一个 AC）
- [x] 规则表每条通过 5 项质量检查（可复现/可观测/边界值/关联AC/无冲突）

## context-references

```yaml
context-queries:
  - repo: "GenerativeUI/A2UIRender"
    query: "PluralizeFunction asFunctionItem pluralize.json 目录注册"
  - repo: "GenerativeUI/A2UIRender"
    query: "NativePluralizeFunction PluralLocaleManager PLURAL_RULE_MAPPINGS CLDR 复数规则 CACHE_TTL_MS"
  - repo: "GenerativeUI/A2UIRender"
    query: "FunctionBridge install registerLocale i18n.getSystemLocaleInstance pluralize locale provider"
```

**关键文档：** `genui/src/main/ets/core/functions/format/PluralizeFunction.ets`、`genui/src/main/ets/core/functions/FunctionBridge.ets`、`genui/src/main/cpp/functions/impl/NativePluralizeFunction.cpp`、`genui/src/main/cpp/functions/NativePluralizeFunction.h`、`genui/src/main/resources/rawfile/schema/A2UI/v0.9/functions/pluralize.json`