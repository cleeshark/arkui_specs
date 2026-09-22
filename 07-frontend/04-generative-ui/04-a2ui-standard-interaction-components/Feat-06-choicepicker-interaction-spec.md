# 特性规格

> Func-07-04-04-Feat-06 ChoicePicker 交互组件：固化 A2UI v0.9 标准 `ChoicePicker` 组件（固定选择列表）的标签（`label`）、可选项列表（`options`，非空数组，项含 label/value）、选中值列表（`value`）、选择模式（`variant`：mutuallyExclusive/multipleSelection，缺省 mutuallyExclusive）、展示样式（`displayStyle`：checkbox/chips）、搜索框（`filterable`）与客户端校验（`checks` 失败仅提示不阻断）。基准实现：`@arkui-genius/genui`（A2UIRender），ArkTS 自定义组件 `CustomChoicePicker`（`markInnerNative(false)`）。

## 概述

| 属性 | 值 |
|------|-----|
| 特性名称 | ChoicePicker 交互组件 |
| 特性编号 | Func-07-04-04-Feat-06 |
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
| 自定义组件（ArkTS） | `genui/src/main/ets/core/components/A2UI/CustomChoicePicker.ets` | — |
| schema 资源 | `genui/src/main/resources/rawfile/schema/A2UI/v0.9/components/ChoicePicker.json` | — |
| 组件参考（Docs） | `reference/standard-components/choicePicker.md` | 理解辅助 |

> 需求基线、不涉及项详见 proposal.md。design.md 与本文档并行产出，互不依赖。

---

## 用户故事

### US-1: 组件类型与目录注册

**作为** 生成式 UI 宿主开发者,
**我想要** ChoicePicker 组件以 `component="ChoicePicker"` 注册为标准自定义组件,
**以便** DSL 声明被引擎正确实例化。

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-1.1 | WHEN DSL 声明 `"component":"ChoicePicker"` THEN `createChoicePickerDefinition()` 注册，`type='ChoicePicker'`（`CustomChoicePicker.ets:45,960-969`） | 正常 |
| AC-1.2 | WHEN 目录项构建 THEN `markInnerNative(false)`（`CustomChoicePicker.ets:971-978`） | 正常 |
| AC-1.3 | WHEN schema 加载 THEN `loadA2UISchema(version,'components/ChoicePicker.json')` 命中 v0.9 schema（`CustomChoicePicker.ets:961-963`） | 正常 |

### US-2: 可选项列表（options）

**作为** 生成式 UI 宿主开发者,
**我想要** 通过 `options` 提供固定选择列表,
**以便** 展示可选项。

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-2.1 | WHEN `options` 为合法数组 THEN 逐项 `normalizeChoicePickerOption` 保留 label/value（`CustomChoicePicker.ets:812-829,347-363`） | 正常 |
| AC-2.2 | WHEN `options` 为空数组 THEN 丢弃当前 ChoicePicker 组件（`shouldRenderChoicePicker` 返回 false，`CustomChoicePicker.ets:695-698`） | 异常 |
| AC-2.3 | WHEN 项缺少 `label` 或 `value` THEN 丢弃该 option（`normalizeChoicePickerOption` 两者均 required，缺省告警）（`CustomChoicePicker.ets:355-358`） | 异常 |
| AC-2.4 | WHEN `options` 提供为 stringified JSON 数组 THEN 解析并告警 `stringified JSON array has been coerced`（`CustomChoicePicker.ets:283-292`） | 边界 |

### US-3: 选择模式（variant）

**作为** 生成式 UI 宿主开发者,
**我想要** 通过 `variant` 控制单选/多选,
**以便** 表达互斥或多项选择。

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-3.1 | WHEN `variant="multipleSelection"` THEN 多选，`buildNextSelectedValues` 增删选中项（`CustomChoicePicker.ets:557-566`） | 正常 |
| AC-3.2 | WHEN `variant="mutuallyExclusive"` THEN 单选，点击新项替换旧选中，点击已选项取消选中（`CustomChoicePicker.ets:568`） | 正常 |
| AC-3.3 | WHEN `variant` 缺省或非法 THEN 归一为 `mutuallyExclusive`（`CustomChoicePicker.ets:392-400,786-795`） | 边界 |
| AC-3.4 | WHEN 单选 `value` 传入多元素 THEN 仅保留第一个元素（文档契约，见「兼容性声明」风险 RISK-选择） | 边界 |

### US-4: 选中值与回写

**作为** 生成式 UI 宿主开发者,
**我想要** 选择变化回写到绑定数据,
**以便** 模型与 UI 一致。

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-4.1 | WHEN 用户变更选择 THEN `applySelection` 更新状态并 `updateChoicePickerDataModelValue` 回写（`CustomChoicePicker.ets:659-672`） | 正常 |
| AC-4.2 | WHEN `valueBindingMode==='item'` THEN 回写单值字符串（`selectedValues[0] ?? ''`）（`CustomChoicePicker.ets:933-935`） | 正常 |
| AC-4.3 | WHEN `valueBindingMode==='list'` THEN 回写数组（`CustomChoicePicker.ets:933-935`） | 正常 |
| AC-4.4 | WHEN 回写失败 THEN 打 warn 日志（`CustomChoicePicker.ets:944-947`） | 异常 |

### US-5: 展示样式与搜索

**作为** 生成式 UI 宿主开发者,
**我想要** 通过 `displayStyle`/`filterable` 控制展示与搜索,
**以便** 适配不同选择场景。

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-5.1 | WHEN `displayStyle="checkbox"` THEN 分组 Checkbox 样式渲染（`CustomChoicePicker.ets:480-508`） | 正常 |
| AC-5.2 | WHEN `displayStyle="chips"` THEN chips 标签块样式渲染（`CustomChoicePicker.ets:510-540`） | 正常 |
| AC-5.3 | WHEN `displayStyle` 非法 THEN 归一为 `checkbox`（`CustomChoicePicker.ets:796-803`） | 边界 |
| AC-5.4 | WHEN `filterable=true` THEN 显示搜索框，对 option 的 label/value 做不区分大小写包含匹配（`CustomChoicePicker.ets:446-454,546-555`） | 正常 |
| AC-5.5 | WHEN `filterable=false`（缺省） THEN 不显示搜索框（`CustomChoicePicker.ets:446`） | 边界 |

### US-6: 客户端校验（checks）

**作为** 生成式 UI 宿主开发者,
**我想要** 通过 `checks` 校验选择结果,
**以便** 失败时提示但不阻断选择。

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-6.1 | WHEN 用户变更选择 THEN `validateChoicePickerChecks` 校验并返回 message（`CustomChoicePicker.ets:659-664,890-920`） | 正常 |
| AC-6.2 | WHEN checks 失败 THEN 组件下方显示错误信息，但不阻断选择也不回滚（`CustomChoicePicker.ets:664,468-473`） | 正常 |
| AC-6.3 | WHEN checks 通过 THEN 清除错误信息（`resolveValidationMessage` 返回空串）（`CustomChoicePicker.ets:718-726`） | 正常 |
| AC-6.4 | WHEN 组件不渲染（options 空） THEN 清空校验提示（`CustomChoicePicker.ets:585-589`） | 边界 |

## 验收追溯

| AC编号 | 关联规则 | 关联 Task | 验证方式 | 证据 |
|----|---------|----------|---------|------|
| AC-1.1,AC-1.2,AC-1.3 | R-1 | T-6 | ArkTS 单测：目录注册 | `CustomChoicePicker.ets:960-978` |
| AC-2.1,AC-2.2,AC-2.3,AC-2.4 | R-2 | T-6 | ArkTS 单测：options 归一化 | `CustomChoicePicker.ets:812-829,347-363` |
| AC-3.1,AC-3.2,AC-3.3,AC-3.4 | R-3 | T-6 | ArkTS 单测 + ohosTest：variant 逻辑 | `CustomChoicePicker.ets:557-569` |
| AC-4.1,AC-4.2,AC-4.3,AC-4.4 | R-4 | T-6 | ArkTS 单测：value 回写 | `CustomChoicePicker.ets:922-953` |
| AC-5.1,AC-5.2,AC-5.3,AC-5.4,AC-5.5 | R-5 | T-6 | ohosTest：展示样式/搜索 | `CustomChoicePicker.ets:446-555` |
| AC-6.1,AC-6.2,AC-6.3,AC-6.4 | R-6 | T-6 | ArkTS 单测：checks 校验 | `CustomChoicePicker.ets:718-726` |

## 规则定义

| 规则ID | 类型 | 触发条件 | 预期行为 | 边界/约束 | 关联AC |
|--------|------|---------|---------|----------|--------|
| R-1 | 行为 | DSL `component="ChoicePicker"` | 注册为标准自定义组件（markInnerNative=false） | type 固定 ChoicePicker | AC-1.1,AC-1.2,AC-1.3 |
| R-2 | 异常 | options 空/项缺字段 | 空→丢弃组件；缺 label/value→丢弃该项 | options 必填非空 | AC-2.1,AC-2.2,AC-2.3,AC-2.4 |
| R-3 | 行为 | variant 设置 | 决定单选互斥/多选增删 | 缺省/非法→mutuallyExclusive | AC-3.1,AC-3.2,AC-3.3,AC-3.4 |
| R-4 | 行为 | 选择变化 | 回写绑定数据（item 单值/list 数组） | 按 valueBindingMode | AC-4.1,AC-4.2,AC-4.3,AC-4.4 |
| R-5 | 行为 | displayStyle/filterable 设置 | 决定 checkbox/chips 与搜索框 | 非法→checkbox | AC-5.1,AC-5.2,AC-5.3,AC-5.4,AC-5.5 |
| R-6 | 行为 | checks 失败 | 显示错误信息，不阻断不阻断也不回滚 | message 展示于组件下方 | AC-6.1,AC-6.2,AC-6.3,AC-6.4 |

## 验证映射

| 编号 | 对应规格项 | 验证方式 | 验证重点 |
|------|----------|---------|---------|
| VM-1 | AC-1.1,AC-1.2,AC-1.3 目录注册 | ArkTS 单测 | type、markInnerNative=false |
| VM-2 | AC-2.1,AC-2.2,AC-2.3,AC-2.4 options | ArkTS 单测 | 空/缺字段归一 |
| VM-3 | AC-3.1,AC-3.2,AC-3.3,AC-3.4 variant | ohosTest | 单选/多选逻辑 |
| VM-4 | AC-4.1,AC-4.2,AC-4.3,AC-4.4 回写 | ArkTS 单测 | item/list 回写 |
| VM-5 | AC-5.1,AC-5.2,AC-5.3,AC-5.4,AC-5.5 展示/搜索 | ohosTest | checkbox/chips/搜索 |
| VM-6 | AC-6.1,AC-6.2,AC-6.3,AC-6.4 checks | ArkTS 单测 | 提示不阻断 |

## API 变更分析

> 存量补录，无新增/变更 ArkTS 公共 API。

### 新增 API

N/A。

### 变更/废弃 API

| API 名称 | 变更类型 | 影响场景 | 迁移指引 | 关联 AC |
|----------|---------|---------|---------|--------|
| `ChoicePicker`（DSL 组件） | 既有 | `component` 字段匹配 | 经 `CustomComponentDefinition` 注册 | AC-1.1,AC-1.2,AC-1.3 |

> d.ts 位置：组件 schema `rawfile/schema/A2UI/v0.9/components/ChoicePicker.json`。Kit：`@arkui-genius/genui`；权限：无。

## 接口规格

### 接口定义

**`CustomChoicePicker`（自定义，`component="ChoicePicker"`）**

| 属性 | 值 |
|------|-----|
| 组件签名 | `export struct CustomChoicePicker`（`CustomChoicePicker.ets:572-573`） |
| 必填属性 | `options`、`value`（schema `required:["component","options","value"]`） |
| 开放范围 | DSL 标准组件（ArkTS 自定义，inner-native=false） |
| 错误码 | 属性异常经 schema 告警 code 2001（`ERROR_CODE_INVALID_VALUE`） |
| 关联 AC | AC-1.1,AC-1.2,AC-1.3,AC-2.2,AC-2.3 |

**属性约束**

| 属性 | 类型 | 必填 | 默认值 | 约束条件 |
|------|------|------|--------|---------|
| label | DynamicString | 否 | "" | 选项组标题 |
| variant | string | 否 | "mutuallyExclusive" | multipleSelection/mutuallyExclusive |
| options | array<{label,value}> | 是 | — | 非空，label 动态字符串，value 稳定字符串 |
| value | DynamicStringList 或 DynamicString | 是 | [] | 单选最多一项，多选多项 |
| displayStyle | string | 否 | "checkbox" | checkbox/chips |
| filterable | boolean | 否 | false | 是否显示搜索框 |
| checks | CheckRule[] | 否 | [] | required/regex/length/numeric/email |

**行为场景**

| # | 触发条件 | 预期行为 | 关联 AC |
|---|----------|----------|---------|
| 1 | options 为空 | 丢弃组件 | AC-2.2 |
| 2 | multipleSelection 点击项 | 增删选中项 | AC-3.1 |
| 3 | mutuallyExclusive 点击已选项 | 取消选中 | AC-3.2 |
| 4 | 选择变化 | 回写 item 或 list | AC-4.1,AC-4.2,AC-4.3 |
| 5 | filterable 搜索 | 过滤 label/value 匹配项 | AC-5.4 |
| 6 | checks 失败 | 显示提示不阻断 | AC-6.2 |

## 兼容性声明

- **已有 API 行为变更:** 否（存量补录）。
- **配置文件格式变更:** 否。
- **数据存储格式变更:** 否（回写 value 字符串/数组，模型格式不变）。
- **最低支持版本:** A2UI 原生协议 v0.9（API Version 20）。
- **API 版本号策略:** schema 随版本加载。

## 架构约束

| 关键约束 | 约束说明 | 影响 AC |
|---------|---------|--------|
| 自定义实现路径 | ChoicePicker 标记 `markInnerNative(false)` | AC-1.2 |
| 单选/多选语义 | variant 决定回写语义与选中态 | AC-3.1,AC-3.2,AC-3.3,AC-3.4,AC-4.1,AC-4.2,AC-4.3,AC-4.4 |
| 校验不阻断 | checks 失败仅提示，与 Button/CheckBox/Slider 禁用语义不同 | AC-6.2 |

## 非功能性需求

| 类型 | 指标/阈值 | 验证方式 | 证据 |
|------|----------|---------|------|
| 可靠性 | 空 options/缺字段不崩溃，丢弃或归一 | ArkTS 单测 | `CustomChoicePicker.ets:812-829` |
| 性能 | 搜索为内存 filter，选项规模受限可预期 | ohosTest | `CustomChoicePicker.ets:551-554` |

## 多设备适配声明

| 设备类型 | 行为差异 | 规格/约束 | 验证方式 | 证据 |
|---------|---------|----------|---------|------|
| 手机 | 无差异 | 交互行为设备无关 | ohosTest | — |
| 平板 | 无差异 | 同上 | ohosTest | — |
| 折叠屏 | 无差异 | 同上 | ohosTest | — |

## 全局特性影响

| 特性 | 适用？ | 结论 | 关联场景 |
|------|-------|------|---------|
| 无障碍 | 是 | `accessibilityGroup(true)` + 标签/描述（`CustomChoicePicker.ets:618-621`） | AC-1.1,AC-1.2,AC-1.3 |
| 大字体 | 否 | 标签字号由 resource 固定 | — |
| 深色模式 | 是 | chips/文本颜色按 `ThemeMode.DARK` 切换（`CustomChoicePicker.ets:402-425,643`） | AC-5.2 |
| 多窗口/分屏 | 否 | 无差异 | — |
| 多用户 | 否 | 无差异 | — |
| 版本升级 | 是 | schema 随版本加载 | AC-1.3 |
| 生态兼容 | 是 | A2UI v0.9 ChoicePicker 兼容 | 概述「目标版本」 |

## DFX 说明

| 场景 | code值 | warning code | error message | 运行时处理 |
|------|--------|--------------|---------------|------------|
| options 数组为空 | 2001 | ERROR_CODE_INVALID_VALUE | Property options expects a non-empty array, drop current component | 丢弃该组件 |
| option 缺少 label | 2001 | ERROR_CODE_INVALID_VALUE | Property option.label is required, option has been dropped | 丢弃该项 |
| option 缺少 value | 2001 | ERROR_CODE_INVALID_VALUE | Property option.value is required, option has been dropped | 丢弃该项 |
| 多选 value 非数组 | 2001 | ERROR_CODE_INVALID_VALUE | Property value expects array type when variant is multipleSelection, value has been wrapped as single-element array | 转换为单元素数组 |
| 单选 value 多元素 | 2001 | ERROR_CODE_INVALID_VALUE | Property value expects at most one selected item when variant is mutuallyExclusive, only the first element has been retained | 仅保留第一项 |

## 行为场景（可选，Gherkin）

```gherkin
Feature: ChoicePicker 交互组件
  作为 生成式 UI 宿主开发者
  我想要 ChoicePicker 支持单选/多选/搜索/校验
  以便 提供固定选择列表

  Scenario: 单选互斥选择
    Given ChoicePicker variant=mutuallyExclusive options=[red,blue]
    When 用户点击 red 再点击 blue
    Then 选中值仅剩 ["blue"]

  Scenario: 多选增删
    Given ChoicePicker variant=multipleSelection options=[red,blue,green]
    When 用户依次点击 red、green 再点击 red
    Then 选中值变为 ["green"]

  Scenario: 搜索过滤
    Given ChoicePicker filterable=true options=[红色/red,蓝色/blue]
    When 用户输入 "red"
    Then 仅保留 option value 含 "red" 的项

  Scenario: 校验失败不阻断
    Given ChoicePicker checks 限制最多 2 项
    When 用户选择第 3 项
    Then 显示错误信息但不回滚选中状态
```

## Spec 自审清单

- [x] 无"待定""TBD""TODO"等占位符
- [x] 所有 AC 使用 WHEN/THEN 格式，可独立测试
- [x] 范围边界明确（ChoicePicker 组件行为；checks 函数归 07-04-07，动态绑定归 07-04-21）
- [x] 无语义模糊表述
- [x] AC 与规则表交叉一致
- [x] 规则表每条通过 5 项质量检查（可复现/可观测/边界值/关联AC/无冲突）

## context-references

```yaml
context-queries:
  - repo: "GenerativeUI/A2UIRender"
    query: "CustomChoicePicker variant options displayStyle filterable valueBindingMode"
  - repo: "GenerativeUI/A2UIRender"
    query: "ChoicePicker validateCustomComponentChecks syncComponentBoundDataModel createChoicePickerDefinition"
  - repo: "GenerativeUI/Docs"
    query: "ChoicePicker 组件 label options value variant displayStyle filterable DFX"
```

**关键文档：** `genui/src/main/ets/core/components/A2UI/CustomChoicePicker.ets`、`reference/standard-components/choicePicker.md`