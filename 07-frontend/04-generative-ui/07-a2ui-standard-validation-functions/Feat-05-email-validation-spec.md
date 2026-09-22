# 特性规格

> Func-07-04-07-Feat-05 email 校验函数：固化 A2UI v0.9 标准协议校验函数 `email` 的邮箱格式判定语义（对 `EMAIL_PATTERN` 做 `std::regex_match`，local-part/domain 为简化 RFC 5322 子集）、目录注册（`isInnerNative: true` + schema `email.json`）、空值/非 string 处理与 checks 集成。基准实现：`@arkui-genius/genui`（A2UIRender），原生实现 `NativeEmailFunction`。

## 概述

| 属性 | 值 |
|------|-----|
| 特性名称 | email 校验函数 |
| 特性编号 | Func-07-04-07-Feat-05 |
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
| 目录注册（ArkTS） | `genui/src/main/ets/core/functions/validation/EmailFunction.ets` | — |
| 函数聚合（ArkTS） | `genui/src/main/ets/core/functions/A2UIBasicFunctions.ets` | — |
| 原生实现（C++） | `genui/src/main/cpp/functions/impl/NativeEmailFunction.cpp`、`functions/NativeEmailFunction.h` | — |
| schema | `genui/src/main/resources/rawfile/schema/A2UI/v0.9/functions/email.json` | — |
| 函数参考（Docs） | `reference/functions/validation.md` | 理解辅助 |

> 需求基线、不涉及项详见 proposal.md。design.md 与本文档并行产出，互不依赖。

---

## 用户故事

### US-1: 目录注册与 schema 契约

**作为** 生成式 UI 宿主开发者,
**我想要** `email` 注册为标准协议校验函数,
**以便** DSL 的 `condition.call="email"` 被引擎正确识别为校验谓词。

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-1.1 | WHEN 函数实例化 THEN `EmailFunction` 构造函数以 `super('email')` 声明函数名（`EmailFunction.ets:22`） | 正常 |
| AC-1.2 | WHEN 目录项构建 THEN `asFunctionItem()` 返回 `name='email'` 且 `isInnerNative=true`（`EmailFunction.ets:27-28`） | 正常 |
| AC-1.3 | WHEN schema 加载 THEN `loadFunctionSchema(version, 'email.json')` 命中 v0.9 schema（`EmailFunction.ets:35`） | 正常 |
| AC-1.4 | WHEN 聚合内置函数 THEN `email` 列入 `standardBuiltinFunctions`（`A2UIBasicFunctions.ets:52`） | 正常 |
| AC-1.5 | WHEN native 注册表初始化 THEN `Register("email", NativeEmailFunction)`（`NativeFunctionRegistry.cpp:72`） | 正常 |

### US-2: 邮箱格式判定（正常/边界）

**作为** 生成式 UI 宿主开发者,
**我想要** `email` 判定字符串是否为合法邮箱地址,
**以便** 校验邮箱格式。

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-2.1 | WHEN `value` 符合 `EMAIL_PATTERN`（如 `user@example.com`） THEN `std::regex_match` 返回 true（`NativeEmailFunction.cpp:24-26,51-54`） | 正常 |
| AC-2.2 | WHEN 邮箱含合法特殊字符 local-part（如 `first.last+tag@example.com`） THEN 返回 true（`NativeEmailFunction.cpp:24-26`） | 正常 |
| AC-2.3 | WHEN 邮箱 domain 为多级（如 `user@sub.domain.com`） THEN 返回 true（`NativeEmailFunction.cpp:24-26`） | 正常 |
| AC-2.4 | WHEN `value` 不含 `@` 或 local-part/domain 非法 THEN 返回 false（`NativeEmailFunction.cpp:51-54`） | 异常 |
| AC-2.5 | WHEN `value` 完整匹配但含首尾多余字符 THEN 完整匹配失败返回 false（`NativeEmailFunction.cpp:53`） | 边界 |

### US-3: 空值与非 string（异常/边界）

**作为** 生成式 UI 宿主开发者,
**我想要** `email` 对空值与非 string 安全返回 false,
**以便** 空/非法输入判为失败。

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-3.1 | WHEN `args` 非对象 THEN 返回 false（`NativeEmailFunction.cpp:37-39`） | 异常 |
| AC-3.2 | WHEN `value` 非 string THEN 返回 false（`NativeEmailFunction.cpp:42-44`） | 异常 |
| AC-3.3 | WHEN `value` 为空字符串 `""` THEN 返回 false（`NativeEmailFunction.cpp:46-49`） | 边界 |

### US-4: checks 集成与失败语义

**作为** 生成式 UI 宿主开发者,
**我想要** `email` 作为 checks 谓词返回布尔且失败回填消息,
**以便** 组件据此显示错误。

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-4.1 | WHEN `email` 作为 `condition.call` 且失败 THEN `ChecksEngine::Validate` 返回 false 并回填 `firstFailedMessage`（`ChecksEngine.cpp:172-183,190-205`） | 异常 |
| AC-4.2 | WHEN `returnType` 为 `"boolean"` THEN `NativeFunctionRegistry::Execute` 通过 `ValidateReturnType`（`NativeFunctionBase.cpp:41-43`） | 正常 |

## 验收追溯

| AC编号 | 关联规则 | 关联 Task | 验证方式 | 证据 |
|----|---------|----------|---------|------|
| AC-1.1,AC-1.2,AC-1.3,AC-1.4,AC-1.5 | R-1 | T-5 | ArkTS 单测：目录注册 | `EmailFunction.ets:22-35`、`A2UIBasicFunctions.ets:52`、`NativeFunctionRegistry.cpp:72` |
| AC-2.1,AC-2.2,AC-2.3,AC-2.4,AC-2.5 | R-2 | T-5 | C++ UT：邮箱格式 | `NativeEmailFunction.cpp:24-26,46-54` |
| AC-3.1,AC-3.2,AC-3.3 | R-3 | T-5 | C++ UT：空值/非 string | `NativeEmailFunction.cpp:35-49` |
| AC-4.1,AC-4.2 | R-4 | T-5 | C++ UT：ChecksEngine 集成 | `ChecksEngine.cpp:172-205` |

## 规则定义

| 规则ID | 类型 | 触发条件 | 预期行为 | 边界/约束 | 关联AC |
|--------|------|---------|---------|----------|--------|
| R-1 | 行为 | 函数注册 | 声明 `name='email'`、`isInnerNative=true`、schema `email.json` | 双注册一致 | AC-1.1,AC-1.2,AC-1.3,AC-1.4,AC-1.5 |
| R-2 | 行为 | value 符合 `EMAIL_PATTERN` | 返回 true | 完整匹配；local-part 允许 `[a-zA-Z0-9.!#$%&'*+/=?^_\`{|}~-]+` | AC-2.1,AC-2.2,AC-2.3,AC-2.4,AC-2.5 |
| R-3 | 异常 | value 非 string 或为空 | 返回 false | 空 string/非 string 均 false | AC-3.1,AC-3.2,AC-3.3 |
| R-4 | 行为 | checks 失败 | `Validate` 返回 false 并回填 message | returnType 必须 boolean | AC-4.1,AC-4.2 |

## 验证映射

| 编号 | 对应规格项 | 验证方式 | 验证重点 |
|------|----------|---------|---------|
| VM-1 | AC-1.1,AC-1.2,AC-1.3,AC-1.4,AC-1.5 目录注册 | ArkTS 单测 | name/isInnerNative/schema |
| VM-2 | AC-2.1,AC-2.2,AC-2.3,AC-2.4,AC-2.5 邮箱格式 | C++ UT | local-part/domain/完整匹配 |
| VM-3 | AC-3.1,AC-3.2,AC-3.3 空值/非 string | C++ UT | 空 string 与非 string |
| VM-4 | AC-4.1,AC-4.2 集成语义 | C++ UT | 失败回填、returnType |

## API 变更分析

> 存量补录，无新增/变更 ArkTS 公共 API。

### 新增 API

N/A。

### 变更/废弃 API

| API 名称 | 变更类型 | 影响场景 | 迁移指引 | 关联 AC |
|----------|---------|---------|---------|--------|
| `email`（DSL 校验函数） | 既有 | `checks` 数组 `condition.call` | 经 `A2UIBasicFunctions.standardBuiltinFunctions` 注册 | AC-1.1,AC-1.2,AC-1.3,AC-1.4,AC-1.5 |

> d.ts 位置：函数 schema `rawfile/schema/A2UI/v0.9/functions/email.json`。Kit：`@arkui-genius/genui`；权限：无。

## 接口规格

### 接口定义

**`NativeEmailFunction::Execute(resolvedArgs)`（原生，`condition.call="email"`）**

| 属性 | 值 |
|------|-----|
| 函数签名 | `FunctionResult Execute(const JsonValue& resolvedArgs)`（`NativeEmailFunction.h:22`） |
| 返回值 | `FunctionResult(bool)` — 邮箱格式合法 true / 否则 false |
| 开放范围 | DSL 校验函数（inner-native） |
| 错误码 | N/A |
| 关联 AC | AC-2.1,AC-2.2,AC-2.3,AC-2.4,AC-2.5,AC-3.1,AC-3.2,AC-3.3 |

**参数约束**

| 参数 | 类型 | 必填 | 默认值 | 约束条件 |
|------|------|------|--------|---------|
| value | string | 是 | 无 | 符合 `EMAIL_PATTERN`；空/非 string → false |
| returnType | string | 否 | `"boolean"` | 必须为 `boolean` |

**行为场景**

| # | 触发条件 | 预期行为 | 关联 AC |
|---|----------|----------|---------|
| 1 | value 符合邮箱格式 | 返回 true | AC-2.1,AC-2.2,AC-2.3 |
| 2 | value 不含 @ 或格式非法 | 返回 false | AC-2.4,AC-2.5 |
| 3 | value 空或非 string | 返回 false | AC-3.1,AC-3.2,AC-3.3 |
| 4 | checks condition 失败 | 返回 false 并回填 message | AC-4.1 |

## 兼容性声明

- **已有 API 行为变更:** 否（存量补录）。
- **配置文件格式变更:** 否。
- **数据存储格式变更:** 否。
- **最低支持版本:** A2UI 原生协议 v0.9（API Version 20）。
- **API 版本号策略:** schema 随版本加载（`email.json`）。
- **格式语义偏差:** Docs 宣称「RFC 5322 兼容」，但 `EMAIL_PATTERN` 为简化子集（不支持带引号 local-part、域名字面量 `[IP]`、国际化邮箱），完整匹配语义以代码 `NativeEmailFunction.cpp:24-26` 为准（见 RISK-3）。

## 架构约束

| 关键约束 | 约束说明 | 影响 AC |
|---------|---------|--------|
| 完整匹配 | `std::regex_match` 非子串匹配 | AC-2.4,AC-2.5 |
| 简化 RFC 子集 | `EMAIL_PATTERN` 不支持 quoted local-part 等 | AC-2.1,AC-2.2,AC-2.3,AC-2.4,AC-2.5 |
| 布尔谓词 | returnType 恒 boolean | AC-4.2 |

## 非功能性需求

| 类型 | 指标/阈值 | 验证方式 | 证据 |
|------|----------|---------|------|
| 可靠性 | 非法输入不崩溃，统一返回 false | C++ UT | `NativeEmailFunction.cpp:35-55` |
| 性能 | 静态编译 regex + 单次 match | C++ UT | `NativeEmailFunction.cpp:51-53` |

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
| 生态兼容 | 是 | A2UI v0.9 email 兼容 | 概述「目标版本」 |

## 行为场景（可选，Gherkin）

```gherkin
Feature: email 校验函数
  作为 生成式 UI 宿主开发者
  我想要 email 校验邮箱格式
  以便 约束邮箱输入

  Scenario: 合法邮箱通过
    Given checks condition {"call":"email","args":{"value":{"path":"email"}}}
    When email="user@example.com"
    Then 返回 true

  Scenario Outline: 非法邮箱失败
    Given email=<val>
    When 执行校验
    Then 返回 false
    Examples:
      | val           |
      | ""            |
      | "user@"       |
      | "user@domain" |
      | "not-an-email"|
```

## Spec 自审清单

- [x] 无"待定""TBD""TODO"等占位符
- [x] 所有 AC 使用 WHEN/THEN 格式，可独立测试
- [x] 范围边界明确（email 函数语义；失败呈现归 07-04-04）
- [x] 无语义模糊表述
- [x] AC 与规则表交叉一致
- [x] 规则表每条通过 5 项质量检查（可复现/可观测/边界值/关联AC/无冲突）

## context-references

```yaml
context-queries:
  - repo: "GenerativeUI/A2UIRender"
    query: "NativeEmailFunction EMAIL_PATTERN std::regex_match 邮箱格式 简化 RFC 5322"
  - repo: "GenerativeUI/A2UIRender"
    query: "EmailFunction.ets isInnerNative email.json"
  - repo: "GenerativeUI/Docs"
    query: "email 校验函数 value 邮箱格式 RFC 5322"
```

**关键文档：** `genui/src/main/ets/core/functions/validation/EmailFunction.ets`、`genui/src/main/cpp/functions/impl/NativeEmailFunction.cpp`、`reference/functions/validation.md`