# 特性规格

> Func-07-04-04-Feat-02 TextField 交互组件：固化 A2UI v0.9 标准 `TextField` 组件的标签（`label`）、内容（`value`）、样式变体（`variant`：shortText/longText/number/obscured，非法回退 shortText）、正则校验（`validationRegexp`，非法正则上报 schema 告警 2001）、客户端校验（`checks` 失败显示错误文本）与用户输入实时回写绑定数据模型。基准实现：`@arkui-genius/genui`（A2UIRender），原生组件 `TextFieldComponent`（`markInnerNative(true)`）。

## 概述

| 属性 | 值 |
|------|-----|
| 特性名称 | TextField 交互组件 |
| 特性编号 | Func-07-04-04-Feat-02 |
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
| Design | `07-frontend/04-generative-ui/04-a2ui-standard-interaction-components/design.md` | Baselined |
| 目录注册（ArkTS） | `genui/src/main/ets/core/components/A2UI/A2UITextField.ets` | — |
| 原生实现（C++） | `genui/src/main/cpp/components/A2UI/textfield/TextFieldComponent.cpp`、`TextFieldComponent.h` | — |
| 主题（C++） | `genui/src/main/cpp/components/A2UI/textfield/TextFieldTheme.cpp/h` | — |
| 组件参考（Docs） | `reference/standard-components/textfield.md` | 理解辅助 |

> 需求基线、不涉及项详见 proposal.md。design.md 与本文档并行产出，互不依赖。

---

## 用户故事

### US-1: 组件类型与目录注册

**作为** 生成式 UI 宿主开发者,
**我想要** TextField 组件以 `component="TextField"` 注册为标准原生组件,
**以便** DSL 声明被引擎正确实例化。

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-1.1 | WHEN DSL 声明 `"component":"TextField"` THEN `A2UITextField.asCatalogItem()` 注册，`type='TextField'`（`A2UITextField.ets:25,30-35`） | 正常 |
| AC-1.2 | WHEN 目录项构建 THEN `markCategory(A2UI_STANDARD)` 且 `markInnerNative(true)`（`A2UITextField.ets:33`） | 正常 |
| AC-1.3 | WHEN schema 加载 THEN `loadA2UISchema(version,'components/TextField.json')` 命中 v0.9 schema（`A2UITextField.ets:26-28`） | 正常 |

### US-2: 标签与内容

**作为** 生成式 UI 宿主开发者,
**我想要** 通过 `label`/`value` 设置输入框标签与内容,
**以便** 展示输入框文案。

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-2.1 | WHEN 描述符含 `label` THEN `SetLabelText` 写入 `labelText_` 并 `SetNodeTextContent(labelNode_)`（`TextFieldComponent.cpp:254-264`） | 正常 |
| AC-2.2 | WHEN 描述符含 `value` THEN `SetValueText` 写入 `valueText_` 并触发 `ValidationRegexpCheck`，再写 input 节点文本（`TextFieldComponent.cpp:266-284`） | 正常 |
| AC-2.3 | WHEN `label` 缺失 THEN 触发必填告警（`GetComponentDirectRequiredPropertyKeys` 返回 `{"label"}`，`TextFieldComponent.cpp:144-147`） | 异常 |
| AC-2.4 | WHEN `label`/`value` 为 DynamicString 绑定 THEN 属性声明 `allowDynamic=true`，经数据绑定解析（`TextFieldComponent.cpp:112-127`） | 正常 |

### US-3: 样式变体

**作为** 生成式 UI 宿主开发者,
**我想要** 通过 `variant` 切换输入模式,
**以便** 表达单行/多行/数字/密码输入。

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-3.1 | WHEN `variant="shortText"` THEN 输入类型 `NORMAL`（`TextFieldComponent.cpp:521-522`） | 正常 |
| AC-3.2 | WHEN `variant="longText"` THEN 切换 TextArea 模式（`SetInputMode(true)`，`TextFieldComponent.cpp:507-510`） | 正常 |
| AC-3.3 | WHEN `variant="number"` THEN 输入类型 `NUMBER`（`TextFieldComponent.cpp:511-514`） | 正常 |
| AC-3.4 | WHEN `variant="obscured"` THEN 输入类型 `PASSWORD`（`TextFieldComponent.cpp:516-519`） | 正常 |
| AC-3.5 | WHEN `variant` 非法 THEN `ResolveVariant` 回退 `"shortText"`（`TextFieldComponent.cpp:44-52`） | 边界 |
| AC-3.6 | WHEN `SetInputMode` 切换 THEN 目标节点 `VISIBLE`、另一输入节点 `NONE`（`TextFieldComponent.cpp:457-490`） | 正常 |

### US-4: 正则校验（validationRegexp）

**作为** 生成式 UI 宿主开发者,
**我想要** 通过 `validationRegexp` 校验输入内容,
**以便** 拦截非法输入并提示。

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-4.1 | WHEN `validationRegexp` 非空且输入匹配失败 THEN 错误文本设为 `Input does not match validationRegexp`（`TextFieldComponent.cpp:374-396`） | 正常 |
| AC-4.2 | WHEN `validationRegexp` 非空且输入匹配成功 THEN 错误文本清空（`ValidationRegexpCheck` 返回 true，`:392-395`） | 正常 |
| AC-4.3 | WHEN `validationRegexp` 为非法正则 THEN 经 `WarningDispatchBridge` 上报 schema 告警（`SCHEMA_ERROR_CODE_INVALID_VALUE`，code=2001）且仅上报一次（`TextFieldComponent.cpp:380-391`） | 异常 |
| AC-4.4 | WHEN `validationRegexp` 空字符串 THEN 不校验，`isValidationRegexpPass_` 恒 true（`TextFieldComponent.cpp:377`） | 边界 |
| AC-4.5 | WHEN `SetValidationRegexp` 变更 THEN 重置 `hasReportedInvalidValidationRegexpError_` 并重新校验（`TextFieldComponent.cpp:525-533`） | 正常 |

### US-5: 客户端校验与错误呈现

**作为** 生成式 UI 宿主开发者,
**我想要** 通过 `checks` 校验输入,
**以便** 失败时在输入框下方显示错误信息。

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-5.1 | WHEN 描述符含 `checks` THEN `ParseChecks` + `ValidateChecks`（`TextFieldComponent.cpp:535-545,564-574`） | 正常 |
| AC-5.2 | WHEN checks 失败 THEN `SetErrorText(latestValidationMessage_)` 显示用户错误信息（`TextFieldComponent.cpp:572`） | 正常 |
| AC-5.3 | WHEN 绑定路径数据更新且属性名以 `__checks_dep_` 前缀 THEN 重新 `ValidateChecks`（`TextFieldComponent.cpp:594-600`） | 正常 |
| AC-5.4 | WHEN checks 失败且无 regexp 错误 THEN 保留 checks 消息；`SetErrorText` 不覆盖（`TextFieldComponent.cpp:398-413`） | 边界 |

### US-6: 用户输入回写数据模型

**作为** 生成式 UI 宿主开发者,
**我想要** 用户输入实时回写绑定数据模型,
**以便** 模型与 UI 保持一致。

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-6.1 | WHEN 输入变化且 `valueBindingPath_` 非空 THEN `SyncValueToBoundDataModel` 实时回写（`TextFieldComponent.cpp:361-372,330-359`） | 正常 |
| AC-6.2 | WHEN 输入值与当前 `valueText_` 相同 THEN 忽略变更（`TextFieldComponent.cpp:363-365`） | 边界 |
| AC-6.3 | WHEN `valueBindingPath_` 为空 THEN 不回写数据模型（`TextFieldComponent.cpp:332-334`） | 边界 |
| AC-6.4 | WHEN 绑定路径解析 THEN `ApplyPrivateAttributes` 末尾 `ResolveValueBindingPath()` 扫描 `propertyName_=="value"` 的绑定（`TextFieldComponent.cpp:591,319-328`） | 正常 |

## 验收追溯

| AC编号 | 关联规则 | 关联 Task | 验证方式 | 证据 |
|----|---------|----------|---------|------|
| AC-1.1,AC-1.2,AC-1.3 | R-1 | T-2 | ArkTS 单测：目录注册 | `A2UITextField.ets:25-35` |
| AC-2.1,AC-2.2,AC-2.3,AC-2.4 | R-2 | T-2 | C++ UT：SetLabelText/SetValueText | `TextFieldComponent.cpp:254-284` |
| AC-3.1,AC-3.2,AC-3.3,AC-3.4,AC-3.5,AC-3.6 | R-3 | T-2 | C++ UT：SetVariant/SetInputMode | `TextFieldComponent.cpp:457-523` |
| AC-4.1,AC-4.2,AC-4.3,AC-4.4,AC-4.5 | R-4,R-5 | T-2 | C++ UT：ValidationRegexpCheck | `TextFieldComponent.cpp:374-396` |
| AC-5.1,AC-5.2,AC-5.3,AC-5.4 | R-6 | T-2 | C++ UT：ValidateChecks/SetErrorText | `TextFieldComponent.cpp:398-413,564-574` |
| AC-6.1,AC-6.2,AC-6.3,AC-6.4 | R-7 | T-2 | C++ UT：SyncValueToBoundDataModel | `TextFieldComponent.cpp:330-372` |

## 规则定义

| 规则ID | 类型 | 触发条件 | 预期行为 | 边界/约束 | 关联AC |
|--------|------|---------|---------|----------|--------|
| R-1 | 行为 | DSL `component="TextField"` | 注册为标准原生组件 | type 固定 TextField | AC-1.1,AC-1.2,AC-1.3 |
| R-2 | 行为 | label/value 设置 | 写入标签/输入节点文本 | label 必填 | AC-2.1,AC-2.2,AC-2.3,AC-2.4 |
| R-3 | 行为 | variant 设置 | 切换输入类型/TextArea | 枚举 shortText/longText/number/obscured | AC-3.1,AC-3.2,AC-3.3,AC-3.4,AC-3.5,AC-3.6 |
| R-4 | 异常 | validationRegexp 非法正则 | 上报 schema 告警 2001，校验失败 | 仅上报一次 | AC-4.1,AC-4.2,AC-4.3,AC-4.4 |
| R-5 | 行为 | validationRegexp 匹配失败 | 显示错误文本 | 匹配成功清空 | AC-4.1,AC-4.2 |
| R-6 | 异常 | checks 失败 | 显示用户错误信息（错误节点） | 优先保留 checks 消息 | AC-5.1,AC-5.2,AC-5.3,AC-5.4 |
| R-7 | 行为 | value 绑定路径非空 + 输入变化 | 实时回写绑定数据模型 | path 空不回写 | AC-6.1,AC-6.2,AC-6.3,AC-6.4 |

## 验证映射

| 编号 | 对应规格项 | 验证方式 | 验证重点 |
|------|----------|---------|---------|
| VM-1 | AC-1.1,AC-1.2,AC-1.3 目录注册 | ArkTS 单测 | type、markInnerNative |
| VM-2 | AC-2.1,AC-2.2,AC-2.3,AC-2.4 标签内容 | C++ UT | label/value 写节点 |
| VM-3 | AC-3.1,AC-3.2,AC-3.3,AC-3.4,AC-3.5,AC-3.6 变体 | C++ UT | 输入类型/TextArea 切换 |
| VM-4 | AC-4.1,AC-4.2,AC-4.3,AC-4.4,AC-4.5 正则 | C++ UT | 非法正则告警、匹配失败提示 |
| VM-5 | AC-5.1,AC-5.2,AC-5.3,AC-5.4 checks 错误 | C++ UT | 错误文本呈现 |
| VM-6 | AC-6.1,AC-6.2,AC-6.3,AC-6.4 回写 | C++ UT | valueBindingPath 实时回写 |

## API 变更分析

> 存量补录，无新增/变更 ArkTS 公共 API。

### 新增 API

N/A。

### 变更/废弃 API

| API 名称 | 变更类型 | 影响场景 | 迁移指引 | 关联 AC |
|----------|---------|---------|---------|--------|
| `TextField`（DSL 组件） | 既有 | `component` 字段匹配 | 经 `CatalogItem.forComponent` 注册 | AC-1.1,AC-1.2,AC-1.3 |

> d.ts 位置：组件 schema `rawfile/schema/A2UI/v0.9/components/TextField.json`。Kit：`@arkui-genius/genui`；权限：无。

## 接口规格

### 接口定义

**`TextFieldComponent`（原生，`component="TextField"`）**

| 属性 | 值 |
|------|-----|
| 组件签名 | `TextFieldComponent : public A2UIComponent`，`GetType()="TextField"`（`TextFieldComponent.cpp:201-204`） |
| 必填属性 | `label`（`GetComponentDirectRequiredPropertyKeys` 返回 `{"label"}`，`TextFieldComponent.cpp:144-147`） |
| 开放范围 | DSL 标准组件（inner-native） |
| 错误码 | validationRegexp 非法 → schema 告警 2001（`SCHEMA_ERROR_CODE_INVALID_VALUE`） |
| 关联 AC | AC-1.1,AC-1.2,AC-1.3,AC-4.3 |

**属性约束**

| 属性 | 类型 | 必填 | 默认值 | 约束条件 |
|------|------|------|--------|---------|
| label | DynamicString | 是 | "" | 任意字符串 |
| value | DynamicString | 否 | "" | 任意字符串 |
| variant | string | 否 | "shortText" | shortText/longText/number/obscured |
| validationRegexp | string | 否 | "" | 合法正则；空串不校验 |
| checks | CheckRule[] | 否 | [] | required/regex/length/numeric/email |

**行为场景**

| # | 触发条件 | 预期行为 | 关联 AC |
|---|----------|----------|---------|
| 1 | 设置 label/value | 写入标签与输入节点 | AC-2.1,AC-2.2 |
| 2 | variant=longText | 切换 TextArea | AC-3.2 |
| 3 | variant=number/obscured | 设置输入类型 NUMBER/PASSWORD | AC-3.3,AC-3.4 |
| 4 | validationRegexp 非法 | 上报告警 2001，校验失败 | AC-4.3 |
| 5 | 用户输入且 value 绑定 | 实时回写数据模型 | AC-6.1 |

## 兼容性声明

- **已有 API 行为变更:** 否（存量补录）。
- **配置文件格式变更:** 否。
- **数据存储格式变更:** 否（value 经绑定实时回写，模型格式不变）。
- **最低支持版本:** A2UI 原生协议 v0.9（API Version 20）。
- **API 版本号策略:** schema 随版本加载。

## 架构约束

| 关键约束 | 约束说明 | 影响 AC |
|---------|---------|--------|
| 原生实现路径 | TextField 标记 `markInnerNative(true)` | AC-1.2 |
| 变体→输入模式映射 | longText 用 TextArea，number/obscured 用 TextInput+inputType | AC-3.1,AC-3.2,AC-3.3,AC-3.4,AC-3.5,AC-3.6 |
| 实时回写 | 用户输入实时同步绑定数据（非失焦） | AC-6.1,AC-6.2,AC-6.3,AC-6.4 |

## 非功能性需求

| 类型 | 指标/阈值 | 验证方式 | 证据 |
|------|----------|---------|------|
| 可靠性 | 非法正则不崩溃，统一告警 | C++ UT | `TextFieldComponent.cpp:380-391` |
| 性能 | 输入回写在 UI 线程，路径化单值更新 | C++ UT | `TextFieldComponent.cpp:358` |

## 多设备适配声明

| 设备类型 | 行为差异 | 规格/约束 | 验证方式 | 证据 |
|---------|---------|----------|---------|------|
| 手机 | 无差异 | 交互行为设备无关 | ohosTest | — |
| 平板 | 无差异 | 同上 | ohosTest | — |
| 折叠屏 | 无差异 | 同上 | ohosTest | — |

## 全局特性影响

| 特性 | 适用？ | 结论 | 关联场景 |
|------|-------|------|---------|
| 无障碍 | 是 | 依赖底层 TextInput/TextArea 无障碍语义 | AC-1.1,AC-1.2,AC-1.3 |
| 大字体 | 否 | 标签字号由 TextFieldTheme 决定 | — |
| 深色模式 | 是 | `OnConfigChange` 重设标签/错误字体色（`TextFieldComponent.cpp:632-639`） | AC-2.1 |
| 多窗口/分屏 | 否 | 无差异 | — |
| 多用户 | 否 | 无差异 | — |
| 版本升级 | 是 | schema 随版本加载 | AC-1.3 |
| 生态兼容 | 是 | A2UI v0.9 TextField 兼容 | 概述「目标版本」 |

## 行为场景（可选，Gherkin）

```gherkin
Feature: TextField 交互组件
  作为 生成式 UI 宿主开发者
  我想要 TextField 支持变体/校验/回写
  以便 表达文本输入框

  Scenario: 用户输入回写数据模型
    Given TextField 的 value 绑定到 /form/name 且值初始为空
    When 用户输入 "Alice"
    Then 数据模型 /form/name 实时更新为 "Alice"

  Scenario: 非法正则上报告警
    Given TextField validationRegexp 为 "[invalid"
    When 应用校验
    Then 上报 schema 告警 code 2001 且仅上报一次

  Scenario Outline: 变体归一
    Given TextField 声明 variant=<variant>
    When 应用变体
    Then 解析为 <resolved>
    Examples:
      | variant     | resolved   |
      | "longText"  | "longText" |
      | "number"    | "number"   |
      | "obscured"  | "obscured" |
      | "weird"     | "shortText" |
```

## Spec 自审清单

- [x] 无"待定""TBD""TODO"等占位符
- [x] 所有 AC 使用 WHEN/THEN 格式，可独立测试
- [x] 范围边界明确（TextField 组件行为；checks 函数归 07-04-07，绑定归 07-04-21）
- [x] 无语义模糊表述
- [x] AC 与规则表交叉一致
- [x] 规则表每条通过 5 项质量检查（可复现/可观测/边界值/关联AC/无冲突）

## context-references

```yaml
context-queries:
  - repo: "GenerativeUI/A2UIRender"
    query: "TextFieldComponent variant validationRegexp checks SyncValueToBoundDataModel"
  - repo: "GenerativeUI/A2UIRender"
    query: "A2UITextField asCatalogItem markInnerNative schemaProvider"
  - repo: "GenerativeUI/Docs"
    query: "TextField 组件 label value variant validationRegexp checks"
```

**关键文档：** `genui/src/main/ets/core/components/A2UI/A2UITextField.ets`、`genui/src/main/cpp/components/A2UI/textfield/TextFieldComponent.cpp`、`reference/standard-components/textfield.md`