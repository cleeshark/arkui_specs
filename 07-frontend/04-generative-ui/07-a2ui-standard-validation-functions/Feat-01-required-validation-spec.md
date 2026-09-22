# 特性规格

> Func-07-04-07-Feat-01 required 校验函数：固化 A2UI v0.9 标准协议校验函数 `required` 的非空判定语义（null / 空字符串 / 空数组 / 空对象 → false，非空标量/集合 → true）、目录注册（ArkTS `isInnerNative: true` + schema `required.json`）与 checks 集成（作为组件 `checks` 的 `condition.call` 谓词，失败回填 message）。基准实现：`@arkui-genius/genui`（A2UIRender），原生实现 `NativeRequiredFunction`。

## 概述

| 属性 | 值 |
|------|-----|
| 特性名称 | required 校验函数 |
| 特性编号 | Func-07-04-07-Feat-01 |
| 优先级 | P0 |
| 目标版本 | A2UI 原生协议 v0.9（API Version 20） |
| SIG 归属 | GenUI SIG |
| 状态 | Baselined |
| 复杂度 | 标准 |

## 本次变更范围（Delta）

| 类型 | 内容 | 说明 |
|------|------|------|
| ADDED | 无（存量补录） | 本特性为 Func-07-04-07 首个 Feat，作为该功能域 design.md 基线 |

## 输入文档

| 文档 | 路径 | 状态 |
|------|------|------|
| Design | `07-frontend/04-generative-ui/07-a2ui-standard-validation-functions/design.md` | Baselined |
| 目录注册（ArkTS） | `genui/src/main/ets/core/functions/validation/RequiredFunction.ets` | — |
| 函数聚合（ArkTS） | `genui/src/main/ets/core/functions/A2UIBasicFunctions.ets` | — |
| 类型契约（ArkTS） | `genui/src/main/ets/core/types/CheckRule.ets` | — |
| 原生实现（C++） | `genui/src/main/cpp/functions/impl/NativeRequiredFunction.cpp`、`functions/NativeRequiredFunction.h` | — |
| 拆分引擎（C++） | `genui/src/main/cpp/checks/ChecksEngine.cpp`、`data/DynamicValueResolver.cpp`、`functions/NativeFunctionRegistry.cpp` | — |
| schema | `genui/src/main/resources/rawfile/schema/A2UI/v0.9/functions/required.json` | — |
| 函数参考（Docs） | `reference/functions/validation.md`、`functions/overview.md` | 理解辅助 |

> 需求基线、不涉及项详见 proposal.md。design.md 与本文档并行产出，互不依赖。

---

## 用户故事

### US-1: 目录注册与 schema 契约

**作为** 生成式 UI 宿主开发者,
**我想要** `required` 注册为标准协议校验函数,
**以便** DSL 的 `condition.call="required"` 被引擎正确识别为校验谓词。

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-1.1 | WHEN 函数实例化 THEN `RequiredFunction` 构造函数以 `super('required')` 声明函数名（`RequiredFunction.ets:22`） | 正常 |
| AC-1.2 | WHEN 目录项构建 THEN `asFunctionItem()` 返回 `name='required'` 且 `isInnerNative=true`（`RequiredFunction.ets:27-28`） | 正常 |
| AC-1.3 | WHEN schema 加载 THEN `loadFunctionSchema(version, 'required.json')` 命中 v0.9 schema（`RequiredFunction.ets:35`） | 正常 |
| AC-1.4 | WHEN 聚合内置函数 THEN `required` 列入 `standardBuiltinFunctions`（`A2UIBasicFunctions.ets:48`） | 正常 |
| AC-1.5 | WHEN CheckRule schema 声明 `condition.call` 枚举 THEN 枚举含 `"required"`（`CheckRule.ets:34`） | 正常 |
| AC-1.6 | WHEN native 注册表初始化 THEN `Register("required", NativeRequiredFunction)`（`NativeFunctionRegistry.cpp:68`） | 正常 |

### US-2: 非空判定（正常）

**作为** 生成式 UI 宿主开发者,
**我想要** `required` 判定值为空还是非空,
**以便** 拦截未填写字段。

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-2.1 | WHEN `value` 为非空字符串（如 `"abc"`） THEN `IsPresent` 返回 true（`NativeRequiredFunction.cpp:48-50`） | 正常 |
| AC-2.2 | WHEN `value` 为非 null 标量（如数字 `1`、布尔 `false`） THEN `IsPresent` 返回 true（`NativeRequiredFunction.cpp:57`） | 边界 |
| AC-2.3 | WHEN `value` 为非空数组（如 `[1]`） THEN `IsPresent` 返回 true（`NativeRequiredFunction.cpp:51-53`） | 正常 |
| AC-2.4 | WHEN `value` 为非空对象（如 `{"a":1}`） THEN `IsPresent` 返回 true（`NativeRequiredFunction.cpp:54-56`） | 正常 |

### US-3: 空值判定（异常/边界）

**作为** 生成式 UI 宿主开发者,
**我想要** `required` 识别各类空值,
**以便** 空值判为校验失败。

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-3.1 | WHEN `value` 为 null THEN `IsPresent` 返回 false（`NativeRequiredFunction.cpp:45-47`） | 异常 |
| AC-3.2 | WHEN `value` 为空字符串 `""` THEN `IsPresent` 返回 false（`NativeRequiredFunction.cpp:48-50`） | 边界 |
| AC-3.3 | WHEN `value` 为空数组 `[]` THEN `IsPresent` 返回 false（`NativeRequiredFunction.cpp:51-53`） | 边界 |
| AC-3.4 | WHEN `value` 为空对象 `{}` THEN `IsPresent` 返回 false（`NativeRequiredFunction.cpp:54-56`） | 边界 |
| AC-3.5 | WHEN `value` 参数缺失（`GetItem("value")` 无效） THEN `Execute` 返回 false（`NativeRequiredFunction.cpp:35-37`） | 异常 |
| AC-3.6 | WHEN `args` 非对象 THEN `Execute` 打 `LOG_WARN "args is empty"` 并返回 false（`NativeRequiredFunction.cpp:29-32`） | 异常 |

### US-4: checks 集成与失败语义

**作为** 生成式 UI 宿主开发者,
**我想要** `required` 作为 checks 谓词返回布尔且失败时回填消息,
**以便** 组件据此禁用/显示错误。

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-4.1 | WHEN `required` 作为 `condition.call` 且失败 THEN `ChecksEngine::Validate` 返回 false 并回填 `firstFailedMessage`（`ChecksEngine.cpp:172-183,190-205`） | 异常 |
| AC-4.2 | WHEN condition 未显式提供 `args.value` 且组件提供默认目标值 THEN `InjectDefaultTargetValue` 注入组件当前值为 `value`（`ChecksEngine.cpp:52-75`） | 正常 |
| AC-4.3 | WHEN `returnType` 为 `"boolean"` THEN `NativeFunctionRegistry::Execute` 通过 `ValidateReturnType`（`NativeFunctionBase.cpp:41-43`） | 正常 |
| AC-4.4 | WHEN `required` 作为 `action.functionCall` 或普通 `DynamicValue` 表达式（非 checks condition） THEN 不在 `IsLegacyCheckFunction` 白名单外接受——`ParseChecks` 仅认 checks 内白名单（`ChecksEngine.cpp:31-36,158-164`） | 边界 |

## 验收追溯

| AC编号 | 关联规则 | 关联 Task | 验证方式 | 证据 |
|----|---------|----------|---------|------|
| AC-1.1,AC-1.2,AC-1.3,AC-1.4,AC-1.5,AC-1.6 | R-1 | T-1 | ArkTS 单测：目录注册 | `RequiredFunction.ets:22-35`、`A2UIBasicFunctions.ets:48`、`NativeFunctionRegistry.cpp:68` |
| AC-2.1,AC-2.2,AC-2.3,AC-2.4 | R-2 | T-1 | C++ UT：`IsPresent` 非空 | `NativeRequiredFunction.cpp:43-58` |
| AC-3.1,AC-3.2,AC-3.3,AC-3.4,AC-3.5,AC-3.6 | R-3 | T-1 | C++ UT：`IsPresent`/`Execute` 空值 | `NativeRequiredFunction.cpp:27-58` |
| AC-4.1,AC-4.2,AC-4.3,AC-4.4 | R-4 | T-1 | C++ UT：ChecksEngine 集成 | `ChecksEngine.cpp:52-75,172-205` |

## 规则定义

| 规则ID | 类型 | 触发条件 | 预期行为 | 边界/约束 | 关联AC |
|--------|------|---------|---------|----------|--------|
| R-1 | 行为 | 函数注册 | 声明 `name='required'`、`isInnerNative=true`、schema `required.json` | 双注册 ArkTS/C++ 一致 | AC-1.1,AC-1.2,AC-1.3,AC-1.4,AC-1.5,AC-1.6 |
| R-2 | 行为 | value 非空 | `IsPresent` 返回 true | string 非空 / array size>0 / object 有子节点 / 标量恒 true | AC-2.1,AC-2.2,AC-2.3,AC-2.4 |
| R-3 | 异常 | value 空或缺失 | 返回 false | null/空 string/空 array/空 object/缺 value/args 非对象 | AC-3.1,AC-3.2,AC-3.3,AC-3.4,AC-3.5,AC-3.6 |
| R-4 | 行为 | checks 失败 | `Validate` 返回 false 并回填 message | `returnType` 必须 boolean；value 可缺省注入 | AC-4.1,AC-4.2,AC-4.3,AC-4.4 |

## 验证映射

| 编号 | 对应规格项 | 验证方式 | 验证重点 |
|------|----------|---------|---------|
| VM-1 | AC-1.1,AC-1.2,AC-1.3,AC-1.4,AC-1.5,AC-1.6 目录注册 | ArkTS 单测 | name/isInnerNative/schema 路径 |
| VM-2 | AC-2.1,AC-2.2,AC-2.3,AC-2.4 非空判定 | C++ UT | 四类非空值返回 true |
| VM-3 | AC-3.1,AC-3.2,AC-3.3,AC-3.4,AC-3.5,AC-3.6 空值判定 | C++ UT | 四类空值 + 缺参 + args 非对象 |
| VM-4 | AC-4.1,AC-4.2,AC-4.3,AC-4.4 集成语义 | C++ UT | 失败回填、value 注入、returnType |

## API 变更分析

> 存量补录，无新增/变更 ArkTS 公共 API。校验函数以 DSL `condition.call` 暴露（inner-native）。

### 新增 API

N/A。

### 变更/废弃 API

| API 名称 | 变更类型 | 影响场景 | 迁移指引 | 关联 AC |
|----------|---------|---------|---------|--------|
| `required`（DSL 校验函数） | 既有 | `checks` 数组 `condition.call` | 经 `A2UIBasicFunctions.standardBuiltinFunctions` 注册 | AC-1.1,AC-1.2,AC-1.3,AC-1.4,AC-1.5,AC-1.6 |

> d.ts 位置：函数 schema `rawfile/schema/A2UI/v0.9/functions/required.json`。Kit：`@arkui-genius/genui`；权限：无。

## 接口规格

### 接口定义

**`NativeRequiredFunction::Execute(resolvedArgs)`（原生，`condition.call="required"`）**

| 属性 | 值 |
|------|-----|
| 函数签名 | `FunctionResult Execute(const JsonValue& resolvedArgs)`（`NativeRequiredFunction.h:28`） |
| 返回值 | `FunctionResult(bool)` — 非空 true / 空或非法 false |
| 开放范围 | DSL 校验函数（inner-native） |
| 错误码 | N/A（仅返回布尔，故障仅 `LOG_WARN "args is empty"`） |
| 关联 AC | AC-2.1,AC-2.2,AC-2.3,AC-2.4,AC-3.1,AC-3.2,AC-3.3,AC-3.4,AC-3.5,AC-3.6 |

**参数约束**

| 参数 | 类型 | 必填 | 默认值 | 约束条件 |
|------|------|------|--------|---------|
| value | any | 是（或经 `defaultTargetProvider` 注入） | 无 | null/空 string/空 array/空 object → false |
| returnType | string | 否 | `"boolean"` | 必须为 `boolean` |

**行为场景**

| # | 触发条件 | 预期行为 | 关联 AC |
|---|----------|----------|---------|
| 1 | value 为非空 string/array/object/标量 | 返回 true | AC-2.1,AC-2.2,AC-2.3,AC-2.4 |
| 2 | value 为 null/空 string/空 array/空 object | 返回 false | AC-3.1,AC-3.2,AC-3.3,AC-3.4 |
| 3 | value 缺失或 args 非对象 | 返回 false（args 非对象另打 WARN） | AC-3.5,AC-3.6 |
| 4 | checks condition 失败 | 返回 false 并回填 message | AC-4.1 |

## 兼容性声明

- **已有 API 行为变更:** 否（存量补录）。
- **配置文件格式变更:** 否。
- **数据存储格式变更:** 否。
- **最低支持版本:** A2UI 原生协议 v0.9（API Version 20）。
- **API 版本号策略:** schema 随版本加载（`required.json`）。

## 架构约束

| 关键约束 | 约束说明 | 影响 AC |
|---------|---------|--------|
| 双注册一致 | ArkTS 目录注册与 C++ registry 函数名/schema 对齐 | AC-1.1,AC-1.2,AC-1.3,AC-1.4,AC-1.5,AC-1.6 |
| 布尔谓词 | 仅作为 checks `condition`，returnType 恒 boolean | AC-4.3,AC-4.4 |
| 无错误码 | 校验失败不产生错误码/schema 告警 | AC-4.1 |

## 非功能性需求

| 类型 | 指标/阈值 | 验证方式 | 证据 |
|------|----------|---------|------|
| 可靠性 | 非法输入不抛异常，统一返回 false | C++ UT | `NativeRequiredFunction.cpp:27-41` |
| 性能 | 纯函数判定，无 IO/分配热路径 | C++ UT | `NativeRequiredFunction.cpp:43-58` |

## 多设备适配声明

| 设备类型 | 行为差异 | 规格/约束 | 验证方式 | 证据 |
|---------|---------|----------|---------|------|
| 手机 | 无差异 | 校验逻辑设备无关 | ohosTest | — |
| 平板 | 无差异 | 同上 | ohosTest | — |
| 折叠屏 | 无差异 | 同上 | ohosTest | — |

## 全局特性影响

| 特性 | 适用？ | 结论 | 关联场景 |
|------|-------|------|---------|
| 无障碍 | 否 | 纯判断逻辑，无障碍由组件呈现 | — |
| 大字体 | 否 | 不涉及 | — |
| 深色模式 | 否 | 不涉及 | — |
| 多窗口/分屏 | 否 | 无差异 | — |
| 多用户 | 否 | 无差异 | — |
| 版本升级 | 是 | schema 随版本加载 | AC-1.3 |
| 生态兼容 | 是 | A2UI v0.9 required 兼容 | 概述「目标版本」 |

## 行为场景（可选，Gherkin）

```gherkin
Feature: required 校验函数
  作为 生成式 UI 宿主开发者
  我想要 required 判定值是否非空
  以便 拦截未填写字段

  Scenario: 非空值校验通过
    Given checks condition 为 {"call":"required","args":{"value":{"path":"username"}}}
    When 数据模型 username="Alice"
    Then required 返回 true

  Scenario Outline: 空值校验失败
    Given checks condition 为 {"call":"required","args":{"value":<val>}}
    When 执行校验
    Then 返回 false
    Examples:
      | val               |
      | null              |
      | ""                |
      | []                |
      | {}                |
```

## Spec 自审清单

- [x] 无"待定""TBD""TODO"等占位符
- [x] 所有 AC 使用 WHEN/THEN 格式，可独立测试
- [x] 范围边界明确（required 函数语义；失败呈现归 07-04-04）
- [x] 无语义模糊表述
- [x] AC 与规则表交叉一致
- [x] 规则表每条通过 5 项质量检查（可复现/可观测/边界值/关联AC/无冲突）

## context-references

```yaml
context-queries:
  - repo: "GenerativeUI/A2UIRender"
    query: "NativeRequiredFunction Execute IsPresent 空值判定 null 空字符串 空数组 空对象"
  - repo: "GenerativeUI/A2UIRender"
    query: "RequiredFunction.ets isInnerNative schemaProvider required.json"
  - repo: "GenerativeUI/Docs"
    query: "required 校验函数 value 非空 checks"
```

**关键文档：** `genui/src/main/ets/core/functions/validation/RequiredFunction.ets`、`genui/src/main/cpp/functions/impl/NativeRequiredFunction.cpp`、`genui/src/main/cpp/checks/ChecksEngine.cpp`、`reference/functions/validation.md`