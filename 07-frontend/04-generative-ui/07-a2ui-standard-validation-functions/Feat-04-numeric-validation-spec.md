# 特性规格

> Func-07-04-07-Feat-04 numeric 校验函数：固化 A2UI v0.9 标准协议校验函数 `numeric` 的数值范围判定语义（`value` 必须为 JSON number 且有限，`min`/`max` 含边界，至少给其一）、目录注册（`isInnerNative: true` + schema `numeric.json`）、参数合法性（min/max 需有限 number）与 checks 集成。基准实现：`@arkui-genius/genui`（A2UIRender），原生实现 `NativeNumericFunction`。

## 概述

| 属性 | 值 |
|------|-----|
| 特性名称 | numeric 校验函数 |
| 特性编号 | Func-07-04-07-Feat-04 |
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
| 目录注册（ArkTS） | `genui/src/main/ets/core/functions/validation/NumericFunction.ets` | — |
| 函数聚合（ArkTS） | `genui/src/main/ets/core/functions/A2UIBasicFunctions.ets` | — |
| 原生实现（C++） | `genui/src/main/cpp/functions/impl/NativeNumericFunction.cpp`、`functions/NativeNumericFunction.h` | — |
| schema | `genui/src/main/resources/rawfile/schema/A2UI/v0.9/functions/numeric.json` | — |
| 函数参考（Docs） | `reference/functions/validation.md` | 理解辅助 |

> 需求基线、不涉及项详见 proposal.md。design.md 与本文档并行产出，互不依赖。

---

## 用户故事

### US-1: 目录注册与 schema 契约

**作为** 生成式 UI 宿主开发者,
**我想要** `numeric` 注册为标准协议校验函数,
**以便** DSL 的 `condition.call="numeric"` 被引擎正确识别为校验谓词。

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-1.1 | WHEN 函数实例化 THEN `NumericFunction` 构造函数以 `super('numeric')` 声明函数名（`NumericFunction.ets:22`） | 正常 |
| AC-1.2 | WHEN 目录项构建 THEN `asFunctionItem()` 返回 `name='numeric'` 且 `isInnerNative=true`（`NumericFunction.ets:27-28`） | 正常 |
| AC-1.3 | WHEN schema 加载 THEN `loadFunctionSchema(version, 'numeric.json')` 命中 v0.9 schema（`NumericFunction.ets:35`） | 正常 |
| AC-1.4 | WHEN 聚合内置函数 THEN `numeric` 列入 `standardBuiltinFunctions`（`A2UIBasicFunctions.ets:51`） | 正常 |
| AC-1.5 | WHEN native 注册表初始化 THEN `Register("numeric", NativeNumericFunction)`（`NativeFunctionRegistry.cpp:71`） | 正常 |

### US-2: 数值范围判定（正常/边界）

**作为** 生成式 UI 宿主开发者,
**我想要** `numeric` 按 min/max 判定数值范围,
**以便** 校验数值落在含边界的范围内。

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-2.1 | WHEN `value` 为有限 number、落在 `[min,max]`（含边界） THEN 返回 true（`NativeNumericFunction.cpp:39-79`） | 正常 |
| AC-2.2 | WHEN 仅给 `min` 且 `value>=min` THEN 返回 true（`NativeNumericFunction.cpp:53-64`） | 正常 |
| AC-2.3 | WHEN 仅给 `max` 且 `value<=max` THEN 返回 true（`NativeNumericFunction.cpp:66-77`） | 正常 |
| AC-2.4 | WHEN `value==min` 或 `value==max` THEN 边界含，返回 true（`NativeNumericFunction.cpp:61-63,74-76`） | 边界 |
| AC-2.5 | WHEN `value<min` 或 `value>max` THEN 返回 false（`NativeNumericFunction.cpp:61-63,74-76`） | 边界 |

### US-3: 非 number 与非法参数（异常/边界）

**作为** 生成式 UI 宿主开发者,
**我想要** `numeric` 对非 number 与非法参数安全返回 false,
**以便** 非数值输入判为失败。

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-3.1 | WHEN `args` 非对象 THEN 返回 false（`NativeNumericFunction.cpp:30-32`） | 异常 |
| AC-3.2 | WHEN `value` 非 number（如字符串 `"123"`） THEN 返回 false（`NativeNumericFunction.cpp:34-37`） | 异常 |
| AC-3.3 | WHEN `value` 为非有限值（NaN/Infinity） THEN 返回 false（`NativeNumericFunction.cpp:39-42`） | 边界 |
| AC-3.4 | WHEN `min` 与 `max` 均缺失 THEN 返回 false（`NativeNumericFunction.cpp:49-51`） | 异常 |
| AC-3.5 | WHEN `min`/`max` 非 number 或非有限 THEN 返回 false（`NativeNumericFunction.cpp:53-60,66-73`） | 异常 |

### US-4: checks 集成与失败语义

**作为** 生成式 UI 宿主开发者,
**我想要** `numeric` 作为 checks 谓词返回布尔且失败回填消息,
**以便** 组件据此显示错误。

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-4.1 | WHEN `numeric` 作为 `condition.call` 且失败 THEN `ChecksEngine::Validate` 返回 false 并回填 `firstFailedMessage`（`ChecksEngine.cpp:172-183,190-205`） | 异常 |
| AC-4.2 | WHEN `returnType` 为 `"boolean"` THEN `NativeFunctionRegistry::Execute` 通过 `ValidateReturnType`（`NativeFunctionBase.cpp:41-43`） | 正常 |

## 验收追溯

| AC编号 | 关联规则 | 关联 Task | 验证方式 | 证据 |
|----|---------|----------|---------|------|
| AC-1.1,AC-1.2,AC-1.3,AC-1.4,AC-1.5 | R-1 | T-4 | ArkTS 单测：目录注册 | `NumericFunction.ets:22-35`、`A2UIBasicFunctions.ets:51`、`NativeFunctionRegistry.cpp:71` |
| AC-2.1,AC-2.2,AC-2.3,AC-2.4,AC-2.5 | R-2 | T-4 | C++ UT：min/max 范围 | `NativeNumericFunction.cpp:39-79` |
| AC-3.1,AC-3.2,AC-3.3,AC-3.4,AC-3.5 | R-3 | T-4 | C++ UT：非 number/非法参数 | `NativeNumericFunction.cpp:28-80` |
| AC-4.1,AC-4.2 | R-4 | T-4 | C++ UT：ChecksEngine 集成 | `ChecksEngine.cpp:172-205` |

## 规则定义

| 规则ID | 类型 | 触发条件 | 预期行为 | 边界/约束 | 关联AC |
|--------|------|---------|---------|----------|--------|
| R-1 | 行为 | 函数注册 | 声明 `name='numeric'`、`isInnerNative=true`、schema `numeric.json` | 双注册一致 | AC-1.1,AC-1.2,AC-1.3,AC-1.4,AC-1.5 |
| R-2 | 行为 | value 有限 number 且在 `[min,max]` | 返回 true | 边界含；min/max 至少给其一 | AC-2.1,AC-2.2,AC-2.3,AC-2.4,AC-2.5 |
| R-3 | 异常 | value 非 number/非有限，或 min/max 非法/缺失 | 返回 false | 数字字符串 `"123"` 判 false；min/max 需有限 number | AC-3.1,AC-3.2,AC-3.3,AC-3.4,AC-3.5 |
| R-4 | 行为 | checks 失败 | `Validate` 返回 false 并回填 message | returnType 必须 boolean | AC-4.1,AC-4.2 |

## 验证映射

| 编号 | 对应规格项 | 验证方式 | 验证重点 |
|------|----------|---------|---------|
| VM-1 | AC-1.1,AC-1.2,AC-1.3,AC-1.4,AC-1.5 目录注册 | ArkTS 单测 | name/isInnerNative/schema |
| VM-2 | AC-2.1,AC-2.2,AC-2.3,AC-2.4,AC-2.5 范围判定 | C++ UT | 含边界、仅 min/仅 max |
| VM-3 | AC-3.1,AC-3.2,AC-3.3,AC-3.4,AC-3.5 非法参数 | C++ UT | 非 number、非有限、缺范围 |
| VM-4 | AC-4.1,AC-4.2 集成语义 | C++ UT | 失败回填、returnType |

## API 变更分析

> 存量补录，无新增/变更 ArkTS 公共 API。

### 新增 API

N/A。

### 变更/废弃 API

| API 名称 | 变更类型 | 影响场景 | 迁移指引 | 关联 AC |
|----------|---------|---------|---------|--------|
| `numeric`（DSL 校验函数） | 既有 | `checks` 数组 `condition.call` | 经 `A2UIBasicFunctions.standardBuiltinFunctions` 注册 | AC-1.1,AC-1.2,AC-1.3,AC-1.4,AC-1.5 |

> d.ts 位置：函数 schema `rawfile/schema/A2UI/v0.9/functions/numeric.json`。Kit：`@arkui-genius/genui`；权限：无。

## 接口规格

### 接口定义

**`NativeNumericFunction::Execute(resolvedArgs)`（原生，`condition.call="numeric"`）**

| 属性 | 值 |
|------|-----|
| 函数签名 | `FunctionResult Execute(const JsonValue& resolvedArgs)`（`NativeNumericFunction.h:22`） |
| 返回值 | `FunctionResult(bool)` — 数值在范围内 true / 否则 false |
| 开放范围 | DSL 校验函数（inner-native） |
| 错误码 | N/A |
| 关联 AC | AC-2.1,AC-2.2,AC-2.3,AC-2.4,AC-2.5,AC-3.1,AC-3.2,AC-3.3,AC-3.4,AC-3.5 |

**参数约束**

| 参数 | 类型 | 必填 | 默认值 | 约束条件 |
|------|------|------|--------|---------|
| value | number | 是 | 无 | 有限 number；非 number/非有限 → false |
| min | number | 否（与 max 至少其一） | 无 | 有限 number |
| max | number | 否（与 min 至少其一） | 无 | 有限 number |
| returnType | string | 否 | `"boolean"` | 必须为 `boolean` |

**行为场景**

| # | 触发条件 | 预期行为 | 关联 AC |
|---|----------|----------|---------|
| 1 | value 有限且在 [min,max]（含边界） | 返回 true | AC-2.1,AC-2.2,AC-2.3,AC-2.4 |
| 2 | value 越界 | 返回 false | AC-2.5 |
| 3 | value 非 number/非有限 | 返回 false | AC-3.2,AC-3.3 |
| 4 | min/max 均缺或非法 | 返回 false | AC-3.4,AC-3.5 |

## 兼容性声明

- **已有 API 行为变更:** 否（存量补录）。
- **配置文件格式变更:** 否。
- **数据存储格式变更:** 否。
- **最低支持版本:** A2UI 原生协议 v0.9（API Version 20）。
- **API 版本号策略:** schema 随版本加载（`numeric.json`）。

## 架构约束

| 关键约束 | 约束说明 | 影响 AC |
|---------|---------|--------|
| value 必须 number | 数字字符串 `"123"` 判 false | AC-3.2 |
| 有限数约束 | NaN/Infinity 判 false | AC-3.3 |
| 边界含 | `min<=value<=max`，边界值通过 | AC-2.4 |

## 非功能性需求

| 类型 | 指标/阈值 | 验证方式 | 证据 |
|------|----------|---------|------|
| 可靠性 | 非法输入不崩溃，统一返回 false | C++ UT | `NativeNumericFunction.cpp:28-80` |
| 性能 | 单次浮点比较 | C++ UT | `NativeNumericFunction.cpp:61-63,74-76` |

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
| 生态兼容 | 是 | A2UI v0.9 numeric 兼容 | 概述「目标版本」 |

## 行为场景（可选，Gherkin）

```gherkin
Feature: numeric 校验函数
  作为 生成式 UI 宿主开发者
  我想要 numeric 校验数值范围
  以便 约束数值输入

  Scenario: 数值在范围内
    Given checks condition {"call":"numeric","args":{"value":{"path":"age"},"min":0,"max":150}}
    When age=30
    Then 返回 true

  Scenario Outline: 数值越界或非数值
    Given min=0 max=150
    When age=<val>
    Then 返回 false
    Examples:
      | val     |
      | -1      |
      | 151     |
      | "30"    |
```

## Spec 自审清单

- [x] 无"待定""TBD""TODO"等占位符
- [x] 所有 AC 使用 WHEN/THEN 格式，可独立测试
- [x] 范围边界明确（numeric 函数语义；失败呈现归 07-04-04）
- [x] 无语义模糊表述
- [x] AC 与规则表交叉一致
- [x] 规则表每条通过 5 项质量检查（可复现/可观测/边界值/关联AC/无冲突）

## context-references

```yaml
context-queries:
  - repo: "GenerativeUI/A2UIRender"
    query: "NativeNumericFunction Execute min max 有限数 isfinite value 非 number"
  - repo: "GenerativeUI/A2UIRender"
    query: "NumericFunction.ets isInnerNative numeric.json"
  - repo: "GenerativeUI/Docs"
    query: "numeric 校验函数 value min max 数值范围 必须是 number"
```

**关键文档：** `genui/src/main/ets/core/functions/validation/NumericFunction.ets`、`genui/src/main/cpp/functions/impl/NativeNumericFunction.cpp`、`reference/functions/validation.md`