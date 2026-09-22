# 特性规格

> Func-07-04-07-Feat-02 regex 校验函数：固化 A2UI v0.9 标准协议校验函数 `regex` 的正则匹配语义（`std::regex_match` 完整匹配）、目录注册（`isInnerNative: true` + schema `regex.json`）、非法 pattern 处理（捕获 `std::regex_error` 打 `LOG_ERROR` 并返回 false，**不发 schema 告警 2001**）与 checks 集成。基准实现：`@arkui-genius/genui`（A2UIRender），原生实现 `NativeRegexFunction`。

## 概述

| 属性 | 值 |
|------|-----|
| 特性名称 | regex 校验函数 |
| 特性编号 | Func-07-04-07-Feat-02 |
| 优先级 | P0 |
| 目标版本 | A2UI 原生协议 v0.9（API Version 20） |
| SIG 归属 | GenUI SIG |
| 状态 | Baselined |
| 复杂度 | 标准 |

## 本次变更范围（Delta）

| 类型 | 内容 | 说明 |
|------|------|------|
| ADDED | 无（存量补录） | 存量特性补录 |

## 输入文档

| 文档 | 路径 | 状态 |
|------|------|------|
| Design | `07-frontend/04-generative-ui/07-a2ui-standard-validation-functions/design.md` | Baselined |
| 目录注册（ArkTS） | `genui/src/main/ets/core/functions/validation/RegexFunction.ets` | — |
| 函数聚合（ArkTS） | `genui/src/main/ets/core/functions/A2UIBasicFunctions.ets` | — |
| 原生实现（C++） | `genui/src/main/cpp/functions/impl/NativeRegexFunction.cpp`、`functions/NativeRegexFunction.h` | — |
| 拆分引擎（C++） | `genui/src/main/cpp/checks/ChecksEngine.cpp`、`data/DynamicValueResolver.cpp` | — |
| schema | `genui/src/main/resources/rawfile/schema/A2UI/v0.9/functions/regex.json` | — |
| 函数参考（Docs） | `reference/functions/validation.md` | 理解辅助 |

> 需求基线、不涉及项详见 proposal.md。design.md 与本文档并行产出，互不依赖。

---

## 用户故事

### US-1: 目录注册与 schema 契约

**作为** 生成式 UI 宿主开发者,
**我想要** `regex` 注册为标准协议校验函数,
**以便** DSL 的 `condition.call="regex"` 被引擎正确识别为校验谓词。

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-1.1 | WHEN 函数实例化 THEN `RegexFunction` 构造函数以 `super('regex')` 声明函数名（`RegexFunction.ets:22`） | 正常 |
| AC-1.2 | WHEN 目录项构建 THEN `asFunctionItem()` 返回 `name='regex'` 且 `isInnerNative=true`（`RegexFunction.ets:27-28`） | 正常 |
| AC-1.3 | WHEN schema 加载 THEN `loadFunctionSchema(version, 'regex.json')` 命中 v0.9 schema（`RegexFunction.ets:35`） | 正常 |
| AC-1.4 | WHEN 聚合内置函数 THEN `regex` 列入 `standardBuiltinFunctions`（`A2UIBasicFunctions.ets:49`） | 正常 |
| AC-1.5 | WHEN native 注册表初始化 THEN `Register("regex", NativeRegexFunction)`（`NativeFunctionRegistry.cpp:69`） | 正常 |

### US-2: 正则完整匹配（正常）

**作为** 生成式 UI 宿主开发者,
**我想要** `regex` 用正则完整匹配校验字符串,
**以便** 验证字符串整体符合模式。

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-2.1 | WHEN `value` 与 `pattern` 均为 string 且完整匹配 THEN `Execute` 返回 true（`NativeRegexFunction.cpp:41-50`） | 正常 |
| AC-2.2 | WHEN pattern 为 `^1[3-9]\\d{9}$`、value 为合法手机号 THEN `std::regex_match` 返回 true（`NativeRegexFunction.cpp:48-49`） | 正常 |
| AC-2.3 | WHEN value 仅部分匹配 pattern 前缀 THEN 完整匹配失败返回 false（`std::regex_match` 非 `regex_search`，`NativeRegexFunction.cpp:49`） | 边界 |
| AC-2.4 | WHEN value 匹配但含首尾多余字符 THEN 完整匹配失败返回 false（`NativeRegexFunction.cpp:49`） | 边界 |

### US-3: 非法 pattern 与参数（异常/边界）

**作为** 生成式 UI 宿主开发者,
**我想要** `regex` 对非法 pattern 与非法参数安全返回 false,
**以便** 不会因非法构造而崩溃。

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-3.1 | WHEN `args` 非对象 THEN `Execute` 返回 false（`NativeRegexFunction.cpp:31-33`） | 异常 |
| AC-3.2 | WHEN `value` 或 `pattern` 非 string THEN 返回 false（`NativeRegexFunction.cpp:37-39`） | 异常 |
| AC-3.3 | WHEN `pattern` 为空字符串 THEN 返回 false（`NativeRegexFunction.cpp:43-45`） | 边界 |
| AC-3.4 | WHEN `pattern` 为非法正则（如 `"[invalid"` 抛出 `std::regex_error`） THEN 捕获后打 `LOG_ERROR "invalid regex pattern"` 并返回 false，**不发 schema 告警**（`NativeRegexFunction.cpp:47-53`） | 异常 |

### US-4: checks 集成与失败语义

**作为** 生成式 UI 宿主开发者,
**我想要** `regex` 作为 checks 谓词返回布尔且失败回填消息,
**以便** 组件据此显示错误。

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-4.1 | WHEN `regex` 作为 `condition.call` 且匹配失败 THEN `ChecksEngine::Validate` 返回 false 并回填 `firstFailedMessage`（`ChecksEngine.cpp:172-183,190-205`） | 异常 |
| AC-4.2 | WHEN `returnType` 为 `"boolean"` THEN `NativeFunctionRegistry::Execute` 通过 `ValidateReturnType`（`NativeFunctionBase.cpp:41-43`） | 正常 |
| AC-4.3 | WHEN `pattern` 非法且位于 checks 内 THEN 与 `TextField.validationRegexp` 的 2001 告警路径相区别——此处仅 `LOG_ERROR` 返回 false（`NativeRegexFunction.cpp:51-53`；对照 `TextFieldComponent.cpp:380-391`） | 边界 |

## 验收追溯

| AC编号 | 关联规则 | 关联 Task | 验证方式 | 证据 |
|----|---------|----------|---------|------|
| AC-1.1,AC-1.2,AC-1.3,AC-1.4,AC-1.5 | R-1 | T-2 | ArkTS 单测：目录注册 | `RegexFunction.ets:22-35`、`A2UIBasicFunctions.ets:49`、`NativeFunctionRegistry.cpp:69` |
| AC-2.1,AC-2.2,AC-2.3,AC-2.4 | R-2 | T-2 | C++ UT：完整匹配 | `NativeRegexFunction.cpp:41-50` |
| AC-3.1,AC-3.2,AC-3.3,AC-3.4 | R-3 | T-2 | C++ UT：非法 pattern/参数 | `NativeRegexFunction.cpp:29-55` |
| AC-4.1,AC-4.2,AC-4.3 | R-4 | T-2 | C++ UT：ChecksEngine 集成 | `ChecksEngine.cpp:172-205` |

## 规则定义

| 规则ID | 类型 | 触发条件 | 预期行为 | 边界/约束 | 关联AC |
|--------|------|---------|---------|----------|--------|
| R-1 | 行为 | 函数注册 | 声明 `name='regex'`、`isInnerNative=true`、schema `regex.json` | 双注册一致 | AC-1.1,AC-1.2,AC-1.3,AC-1.4,AC-1.5 |
| R-2 | 行为 | value/pattern string 且完整匹配 | 返回 true | `std::regex_match` 完整匹配 | AC-2.1,AC-2.2,AC-2.3,AC-2.4 |
| R-3 | 异常 | 参数非法或 pattern 非法 | 返回 false | pattern 空/非 string 均 false；非法 pattern 仅 LOG_ERROR | AC-3.1,AC-3.2,AC-3.3,AC-3.4 |
| R-4 | 行为 | checks 失败 | `Validate` 返回 false 并回填 message | returnType 必须 boolean | AC-4.1,AC-4.2,AC-4.3 |

## 验证映射

| 编号 | 对应规格项 | 验证方式 | 验证重点 |
|------|----------|---------|---------|
| VM-1 | AC-1.1,AC-1.2,AC-1.3,AC-1.4,AC-1.5 目录注册 | ArkTS 单测 | name/isInnerNative/schema |
| VM-2 | AC-2.1,AC-2.2,AC-2.3,AC-2.4 完整匹配 | C++ UT | regex_match 语义 |
| VM-3 | AC-3.1,AC-3.2,AC-3.3,AC-3.4 非法参数 | C++ UT | 非法 pattern 无崩溃、无告警 |
| VM-4 | AC-4.1,AC-4.2,AC-4.3 集成语义 | C++ UT | 失败回填、returnType、与 2001 区分 |

## API 变更分析

> 存量补录，无新增/变更 ArkTS 公共 API。

### 新增 API

N/A。

### 变更/废弃 API

| API 名称 | 变更类型 | 影响场景 | 迁移指引 | 关联 AC |
|----------|---------|---------|---------|--------|
| `regex`（DSL 校验函数） | 既有 | `checks` 数组 `condition.call` | 经 `A2UIBasicFunctions.standardBuiltinFunctions` 注册 | AC-1.1,AC-1.2,AC-1.3,AC-1.4,AC-1.5 |

> d.ts 位置：函数 schema `rawfile/schema/A2UI/v0.9/functions/regex.json`。Kit：`@arkui-genius/genui`；权限：无。

## 接口规格

### 接口定义

**`NativeRegexFunction::Execute(resolvedArgs)`（原生，`condition.call="regex"`）**

| 属性 | 值 |
|------|-----|
| 函数签名 | `FunctionResult Execute(const JsonValue& resolvedArgs)`（`NativeRegexFunction.h:22`） |
| 返回值 | `FunctionResult(bool)` — 完整匹配 true / 否则 false |
| 开放范围 | DSL 校验函数（inner-native） |
| 错误码 | N/A（非法 pattern 仅 `LOG_ERROR`，不发 schema 告警） |
| 关联 AC | AC-2.1,AC-2.2,AC-2.3,AC-2.4,AC-3.1,AC-3.2,AC-3.3,AC-3.4 |

**参数约束**

| 参数 | 类型 | 必填 | 默认值 | 约束条件 |
|------|------|------|--------|---------|
| value | string | 是 | 无 | 任意字符串（支持路径绑定） |
| pattern | string | 是 | 无 | 合法正则；空或非法 → false |
| returnType | string | 否 | `"boolean"` | 必须为 `boolean` |

**行为场景**

| # | 触发条件 | 预期行为 | 关联 AC |
|---|----------|----------|---------|
| 1 | value 完整匹配 pattern | 返回 true | AC-2.1,AC-2.2 |
| 2 | value 部分/多余字符 | 返回 false | AC-2.3,AC-2.4 |
| 3 | pattern 空或非法 | 返回 false（非法另打 LOG_ERROR） | AC-3.3,AC-3.4 |
| 4 | value/pattern 非 string | 返回 false | AC-3.2 |
| 5 | checks condition 失败 | 返回 false 并回填 message | AC-4.1 |

## 兼容性声明

- **已有 API 行为变更:** 否（存量补录）。
- **配置文件格式变更:** 否。
- **数据存储格式变更:** 否。
- **最低支持版本:** A2UI 原生协议 v0.9（API Version 20）。
- **API 版本号策略:** schema 随版本加载（`regex.json`）。

## 架构约束

| 关键约束 | 约束说明 | 影响 AC |
|---------|---------|--------|
| 完整匹配 | `std::regex_match` 非子串部分匹配 | AC-2.1,AC-2.2,AC-2.3,AC-2.4 |
| 无告警语义 | 非法 pattern 不发 schema 告警 2001（区别于 validationRegexp） | AC-3.4,AC-4.3 |
| 布尔谓词 | returnType 恒 boolean | AC-4.2 |

## 非功能性需求

| 类型 | 指标/阈值 | 验证方式 | 证据 |
|------|----------|---------|------|
| 可靠性 | 非法 pattern 不崩溃，捕获 `std::regex_error` | C++ UT | `NativeRegexFunction.cpp:47-53` |
| 性能 | 单次 regex_match，无回溯放大保护（pattern 由 DSL 提供） | C++ UT | `NativeRegexFunction.cpp:48-49` |

## 多设备适配声明

| 设备类型 | 行为差异 | 规格/约束 | 验证方式 | 证据 |
|---------|---------|----------|---------|------|
| 手机 | 无差异 | 校验逻辑设备无关 | ohosTest | — |
| 平板 | 无差异 | 同上 | ohosTest | — |
| 折叠屏 | 无差异 | 同上 | ohosTest | — |

## 全局特性影响

| 特性 | 适用？ | 结论 | 关联场景 |
|------|-------|------|---------|
| 无障碍 | 否 | 纯判断逻辑 | — |
| 大字体 | 否 | 不涉及 | — |
| 深色模式 | 否 | 不涉及 | — |
| 多窗口/分屏 | 否 | 无差异 | — |
| 多用户 | 否 | 无差异 | — |
| 版本升级 | 是 | schema 随版本加载 | AC-1.3 |
| 生态兼容 | 是 | A2UI v0.9 regex 兼容 | 概述「目标版本」 |

## 行为场景（可选，Gherkin）

```gherkin
Feature: regex 校验函数
  作为 生成式 UI 宿主开发者
  我想要 regex 完整匹配校验字符串
  以便 验证字符串符合模式

  Scenario: 完整匹配通过
    Given checks condition {"call":"regex","args":{"value":{"path":"phone"},"pattern":"^1[3-9]\\d{9}$"}}
    When 数据模型 phone="13800000000"
    Then 返回 true

  Scenario: 非法 pattern 安全失败
    Given pattern "[invalid"
    When 执行校验
    Then 返回 false 且打 LOG_ERROR，不上报 schema 告警
```

## Spec 自审清单

- [x] 无"待定""TBD""TODO"等占位符
- [x] 所有 AC 使用 WHEN/THEN 格式，可独立测试
- [x] 范围边界明确（regex 函数语义；validationRegexp 归 07-04-04）
- [x] 无语义模糊表述
- [x] AC 与规则表交叉一致
- [x] 规则表每条通过 5 项质量检查（可复现/可观测/边界值/关联AC/无冲突）

## context-references

```yaml
context-queries:
  - repo: "GenerativeUI/A2UIRender"
    query: "NativeRegexFunction Execute std::regex_match 完整匹配 非法 pattern std::regex_error"
  - repo: "GenerativeUI/A2UIRender"
    query: "RegexFunction.ets isInnerNative regex.json"
  - repo: "GenerativeUI/Docs"
    query: "regex 校验函数 value pattern 完整匹配"
```

**关键文档：** `genui/src/main/ets/core/functions/validation/RegexFunction.ets`、`genui/src/main/cpp/functions/impl/NativeRegexFunction.cpp`、`reference/functions/validation.md`