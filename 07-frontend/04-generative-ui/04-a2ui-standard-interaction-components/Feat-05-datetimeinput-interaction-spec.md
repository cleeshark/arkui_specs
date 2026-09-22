# 特性规格

> Func-07-04-04-Feat-05 DateTimeInput 交互组件：固化 A2UI v0.9 标准 `DateTimeInput` 组件的日期/时间选择（`enableDate`/`enableTime`）、选中值（`value`，ISO 8601，24 小时制）、可选边界（`min`/`max`，解析失败丢弃，`min>max` 回退默认边界）、占位文案（`label`）与客户端校验（`checks` 弹窗确认时阻断）。基准实现：`@arkui-genius/genui`（A2UIRender），ArkTS 自定义组件 `CustomDateTimeInput`（`markInnerNative(false)`）。

## 概述

| 属性 | 值 |
|------|-----|
| 特性名称 | DateTimeInput 交互组件 |
| 特性编号 | Func-07-04-04-Feat-05 |
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
| 自定义组件（ArkTS） | `genui/src/main/ets/core/components/A2UI/CustomDateTimeInput.ets` | — |
| schema 资源 | `genui/src/main/resources/rawfile/schema/A2UI/v0.9/components/DateTimeInput.json` | — |
| 组件参考（Docs） | `reference/standard-components/dateTimeInput.md` | 理解辅助 |

> 需求基线、不涉及项详见 proposal.md。design.md 与本文档并行产出，互不依赖。

---

## 用户故事

### US-1: 组件类型与目录注册

**作为** 生成式 UI 宿主开发者,
**我想要** DateTimeInput 组件以 `component="DateTimeInput"` 注册为标准自定义组件,
**以便** DSL 声明被引擎正确实例化。

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-1.1 | WHEN DSL 声明 `"component":"DateTimeInput"` THEN `createDateTimeInputDefinition()` 注册，`type='DateTimeInput'`（`CustomDateTimeInput.ets:43,1434-1443`） | 正常 |
| AC-1.2 | WHEN 目录项构建 THEN `markInnerNative(false)`（`CustomDateTimeInput.ets:1445-1452`） | 正常 |
| AC-1.3 | WHEN schema 加载 THEN `loadA2UISchema(version,'components/DateTimeInput.json')` 命中 v0.9 schema（`CustomDateTimeInput.ets:1435-1437`） | 正常 |

### US-2: 日期/时间模式

**作为** 生成式 UI 宿主开发者,
**我想要** 通过 `enableDate`/`enableTime` 控制日期与时间选择,
**以便** 支持仅日期/仅时间/日期时间组合。

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-2.1 | WHEN `enableDate=true, enableTime=false` THEN 弹窗仅显示日期选择器（`CustomDateTimeInput.ets:864-866,876-881`） | 正常 |
| AC-2.2 | WHEN `enableDate=false, enableTime=true` THEN 弹窗仅显示时间选择器（`CustomDateTimeInput.ets:868-870,883-888`） | 正常 |
| AC-2.3 | WHEN `enableDate=true, enableTime=true` THEN combined 模式，两步确认（先日期后时间，`isDateStep` 切换）（`CustomDateTimeInput.ets:741-775,872-874`） | 正常 |
| AC-2.4 | WHEN `enableDate` 与 `enableTime` 均非 true THEN 上报 schema 告警并保持 disabled（`CustomDateTimeInput.ets:464-470`） | 异常 |
| AC-2.5 | WHEN 时间选择 THEN `useMilitaryTime(true)` 24 小时制（`CustomDateTimeInput.ets:824,836`） | 正常 |

### US-3: 选中值与格式归一化

**作为** 生成式 UI 宿主开发者,
**我想要** `value` 支持字面量/绑定/函数调用且格式归一化,
**以便** 确认后回写统一格式。

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-3.1 | WHEN combined 模式确认 THEN `resolveConfirmedValue` 格式化为 `YYYY-MM-DD HH:mm`（`CustomDateTimeInput.ets:904-915,516-518`） | 正常 |
| AC-3.2 | WHEN 仅日期模式 THEN 格式化 `YYYY-MM-DD`（`CustomDateTimeInput.ets:503-508,908-910`） | 正常 |
| AC-3.3 | WHEN 仅时间模式 THEN 格式化 `HH:mm`（`CustomDateTimeInput.ets:510-514,911-913`） | 正常 |
| AC-3.4 | WHEN `value` 非合法显示值 THEN `normalizeDateTimeInputOptionsForSchemaWarning` 归一化或回退默认并上报告警（`CustomDateTimeInput.ets:487-498`） | 异常 |
| AC-3.5 | WHEN `value` 空串 THEN 输入框显示 placeholder（`CustomDateTimeInput.ets:1214-1221,1239-1245`） | 边界 |

### US-4: 可选边界（min/max）

**作为** 生成式 UI 宿主开发者,
**我想要** 通过 `min`/`max` 限制可选范围,
**以便** 阻止越界选择。

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-4.1 | WHEN `min` 或 `max` 非 ISO 8601 格式 THEN 丢弃该边界并上报告警（`CustomDateTimeInput.ets:425-448`） | 异常 |
| AC-4.2 | WHEN `min > max` THEN 丢弃两者并回退默认边界（`CustomDateTimeInput.ets:475-485`） | 异常 |
| AC-4.3 | WHEN `min`/`max` 缺失 THEN 默认边界 `1970-01-01` / `2100-12-31 23:59`（`CustomDateTimeInput.ets:548-554`） | 边界 |
| AC-4.4 | WHEN 选中值越界 THEN `clampDateValue` 夹取到边界（`CustomDateTimeInput.ets:571-580`） | 边界 |
| AC-4.5 | WHEN 日期范围解析 THEN `resolveDateRangeOrDefault` 保证 start<=end（`CustomDateTimeInput.ets:556-569`） | 正常 |

### US-5: 占位文案（label）

**作为** 生成式 UI 宿主开发者,
**我想要** 通过 `label` 设置占位提示,
**以便** 无有效 value 时展示自定义文案。

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-5.1 | WHEN `label` 非空且无有效 value THEN `resolvePlaceholder` 返回 label（`CustomDateTimeInput.ets:1223-1226`） | 正常 |
| AC-5.2 | WHEN `label` 空 THEN 按模式使用内置占位（date/time/datetime/disabled）（`CustomDateTimeInput.ets:1227-1236`） | 边界 |
| AC-5.3 | WHEN 存在有效 value THEN 显示 value 而非占位（`CustomDateTimeInput.ets:1216-1218`） | 正常 |

### US-6: 客户端校验与数据回写

**作为** 生成式 UI 宿主开发者,
**我想要** 确认选择时执行 checks 校验并回写绑定数据,
**以便** 校验失败阻断、成功回写。

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-6.1 | WHEN 弹窗确认 THEN `validateDateTimeInputChecks` 经 `nativeEngine.validateCustomComponentChecks` 校验（`CustomDateTimeInput.ets:762-767,1348-1377`） | 正常 |
| AC-6.2 | WHEN checks 校验失败 THEN 显示错误信息并保持弹窗打开（不确认）（`CustomDateTimeInput.ets:768-771`） | 异常 |
| AC-6.3 | WHEN 校验通过 THEN `updateDateTimeInputDataModelValue` 经 `syncComponentBoundDataModel` 回写 value（`CustomDateTimeInput.ets:1094-1109,1379-1406`） | 正常 |
| AC-6.4 | WHEN 绑定回写失败且存在 `valuePath` THEN 跳过确认并打 warn 日志（`CustomDateTimeInput.ets:1102-1104`） | 异常 |

## 验收追溯

| AC编号 | 关联规则 | 关联 Task | 验证方式 | 证据 |
|----|---------|----------|---------|------|
| AC-1.1,AC-1.2,AC-1.3 | R-1 | T-5 | ArkTS 单测：目录注册 | `CustomDateTimeInput.ets:1434-1452` |
| AC-2.1,AC-2.2,AC-2.3,AC-2.4,AC-2.5 | R-2 | T-5 | ArkTS 单测 + ohosTest：模式切换 | `CustomDateTimeInput.ets:464-470,741-775` |
| AC-3.1,AC-3.2,AC-3.3,AC-3.4,AC-3.5 | R-3 | T-5 | ArkTS 单测：格式归一化 | `CustomDateTimeInput.ets:487-518,904-915` |
| AC-4.1,AC-4.2,AC-4.3,AC-4.4,AC-4.5 | R-4 | T-5 | ArkTS 单测：边界解析 | `CustomDateTimeInput.ets:425-448,548-580` |
| AC-5.1,AC-5.2,AC-5.3 | R-5 | T-5 | ArkTS 单测：占位 | `CustomDateTimeInput.ets:1214-1236` |
| AC-6.1,AC-6.2,AC-6.3,AC-6.4 | R-6 | T-5 | ohosTest：确认/校验/回写 | `CustomDateTimeInput.ets:1348-1406` |

## 规则定义

| 规则ID | 类型 | 触发条件 | 预期行为 | 边界/约束 | 关联AC |
|--------|------|---------|---------|----------|--------|
| R-1 | 行为 | DSL `component="DateTimeInput"` | 注册为标准自定义组件（markInnerNative=false） | type 固定 DateTimeInput | AC-1.1,AC-1.2,AC-1.3 |
| R-2 | 行为 | enableDate/enableTime 组合 | 决定日期/时间/组合选择模式 | 均 false 上报告警并禁用 | AC-2.1,AC-2.2,AC-2.3,AC-2.4,AC-2.5 |
| R-3 | 行为 | value 确认/解析 | 归一化 ISO 8601，24 小时制 | 非法归一化或回退 | AC-3.1,AC-3.2,AC-3.3,AC-3.4,AC-3.5 |
| R-4 | 异常 | min/max 非法或 min>max | 丢弃边界并回退默认 | 默认 1970-01-01/2100-12-31 23:59 | AC-4.1,AC-4.2,AC-4.3,AC-4.4,AC-4.5 |
| R-5 | 行为 | label 空/非空 | 决定占位文案 | 有效 value 优先显示 | AC-5.1,AC-5.2,AC-5.3 |
| R-6 | 异常 | 确认时 checks 失败 | 显示错误并保持弹窗 | 回写失败跳过确认 | AC-6.1,AC-6.2,AC-6.3,AC-6.4 |

## 验证映射

| 编号 | 对应规格项 | 验证方式 | 验证重点 |
|------|----------|---------|---------|
| VM-1 | AC-1.1,AC-1.2,AC-1.3 目录注册 | ArkTS 单测 | type、markInnerNative=false |
| VM-2 | AC-2.1,AC-2.2,AC-2.3,AC-2.4,AC-2.5 模式 | ohosTest | 日期/时间/组合/禁用 |
| VM-3 | AC-3.1,AC-3.2,AC-3.3,AC-3.4,AC-3.5 归一化 | ArkTS 单测 | ISO 8601 格式 |
| VM-4 | AC-4.1,AC-4.2,AC-4.3,AC-4.4,AC-4.5 边界 | ArkTS 单测 | min/max 丢弃、回退 |
| VM-5 | AC-5.1,AC-5.2,AC-5.3 占位 | ArkTS 单测 | label/内置占位 |
| VM-6 | AC-6.1,AC-6.2,AC-6.3,AC-6.4 校验回写 | ohosTest | 校验阻断、回写 |

## API 变更分析

> 存量补录，无新增/变更 ArkTS 公共 API。

### 新增 API

N/A。

### 变更/废弃 API

| API 名称 | 变更类型 | 影响场景 | 迁移指引 | 关联 AC |
|----------|---------|---------|---------|--------|
| `DateTimeInput`（DSL 组件） | 既有 | `component` 字段匹配 | 经 `CustomComponentDefinition` 注册 | AC-1.1,AC-1.2,AC-1.3 |

> d.ts 位置：组件 schema `rawfile/schema/A2UI/v0.9/components/DateTimeInput.json`。Kit：`@arkui-genius/genui`；权限：无。

## 接口规格

### 接口定义

**`CustomDateTimeInput`（自定义，`component="DateTimeInput"`）**

| 属性 | 值 |
|------|-----|
| 组件签名 | `export struct CustomDateTimeInput`（`CustomDateTimeInput.ets:958-959`） |
| 必填属性 | `value`（schema `required:["component","value"]`） |
| 开放范围 | DSL 标准组件（ArkTS 自定义，inner-native=false） |
| 错误码 | 属性异常经 schema 告警 code 2001（`ERROR_CODE_INVALID_VALUE`） |
| 关联 AC | AC-1.1,AC-1.2,AC-1.3,AC-2.4,AC-3.4,AC-4.1,AC-4.2 |

**属性约束**

| 属性 | 类型 | 必填 | 默认值 | 约束条件 |
|------|------|------|--------|---------|
| value | DynamicString | 是 | "" | ISO 8601：YYYY-MM-DD / HH:mm / YYYY-MM-DD HH:mm |
| enableDate | boolean | 否 | false | 与 enableTime 不可同时 false |
| enableTime | boolean | 否 | false | 同上 |
| min | DynamicString | 否 | "" | ISO 8601，仅字符串字面量 |
| max | DynamicString | 否 | "" | ISO 8601，仅字符串字面量 |
| label | DynamicString | 否 | "" | 占位文案 |
| checks | CheckRule[] | 否 | [] | required/regex/length/numeric/email |

**行为场景**

| # | 触发条件 | 预期行为 | 关联 AC |
|---|----------|----------|---------|
| 1 | 仅日期模式 | 显示 DatePicker | AC-2.1 |
| 2 | 仅时间模式 | 显示 TimePicker（24h） | AC-2.2 |
| 3 | 组合模式确认 | 回写 YYYY-MM-DD HH:mm | AC-2.3,AC-3.1 |
| 4 | min>max | 丢弃边界回退默认 | AC-4.2 |
| 5 | 确认 checks 失败 | 显示错误保持弹窗 | AC-6.2 |

## 兼容性声明

- **已有 API 行为变更:** 否（存量补录）。
- **配置文件格式变更:** 否。
- **数据存储格式变更:** 否（回写 value 字符串，模型格式不变）。
- **最低支持版本:** A2UI 原生协议 v0.9（API Version 20）。
- **API 版本号策略:** schema 随版本加载。

## 架构约束

| 关键约束 | 约束说明 | 影响 AC |
|---------|---------|--------|
| 自定义实现路径 | DateTimeInput 标记 `markInnerNative(false)`，依赖 DatePicker/TimePicker | AC-1.2 |
| 24 小时制 | 时间始终 `useMilitaryTime(true)` | AC-2.5 |
| 弹窗阻断校验 | checks 确认时执行，失败保持弹窗 | AC-6.2 |

## 非功能性需求

| 类型 | 指标/阈值 | 验证方式 | 证据 |
|------|----------|---------|------|
| 可靠性 | 非法 value/min/max 不崩溃，归一化/丢弃/回退 | ArkTS 单测 | `CustomDateTimeInput.ets:425-498` |
| 性能 | 弹窗为惰性创建（ComponentContent），确认时单次校验 | ohosTest | `CustomDateTimeInput.ets:1059-1068` |

## 多设备适配声明

| 设备类型 | 行为差异 | 规格/约束 | 验证方式 | 证据 |
|---------|---------|----------|---------|------|
| 手机 | 无差异 | 弹窗交互设备无关 | ohosTest | — |
| 平板 | 无差异 | 同上 | ohosTest | — |
| 折叠屏 | 无差异 | 同上 | ohosTest | — |

## 全局特性影响

| 特性 | 适用？ | 结论 | 关联场景 |
|------|-------|------|---------|
| 无障碍 | 是 | `accessibilityGroup(true)` + 标签/描述（`CustomDateTimeInput.ets:997-999`） | AC-1.1,AC-1.2,AC-1.3 |
| 大字体 | 否 | 弹窗字号由 resource 固定 | — |
| 深色模式 | 是 | `resolveDateTimeInputDialogBackgroundColorByThemeMode`（`CustomDateTimeInput.ets:659-662`） | AC-2.1,AC-2.2,AC-2.3,AC-2.4,AC-2.5 |
| 多窗口/分屏 | 否 | 弹窗经 UIContext 承载 | — |
| 多用户 | 否 | 无差异 | — |
| 版本升级 | 是 | schema 随版本加载 | AC-1.3 |
| 生态兼容 | 是 | A2UI v0.9 DateTimeInput 兼容 | 概述「目标版本」 |

## DFX 说明

| 场景 | code值 | warning code | error message | 运行时处理 |
|------|--------|--------------|---------------|------------|
| value 非 ISO 8601 | 2001 | ERROR_CODE_INVALID_VALUE | Property value expects ISO 8601 compatible value, fallback to default value / value has been normalized | 归一化或回退默认 |
| min/max 格式不正确 | 2001 | ERROR_CODE_INVALID_VALUE | Property min/max expects ISO 8601 compatible value, field has been ignored | 丢弃该边界 |
| min > max | 2001 | ERROR_CODE_INVALID_VALUE | Property min must not be later than max, min and max have been ignored | 丢弃两者回退默认 |
| enableDate/enableTime 均 false | 2001 | ERROR_CODE_INVALID_VALUE | Properties enableDate and enableTime cannot both be false, DateTimeInput remains disabled | 默认启用 enableDate |

## 行为场景（可选，Gherkin）

```gherkin
Feature: DateTimeInput 交互组件
  作为 生成式 UI 宿主开发者
  我想要 DateTimeInput 支持日期/时间选择与校验
  以便 选择并回写日期时间

  Scenario: 组合模式两步确认
    Given DateTimeInput enableDate=true enableTime=true value="2026-05-07 10:00"
    When 用户依次确认日期与时间
    Then 回写 value 为 "2026-05-07 10:00" 并关闭弹窗

  Scenario: min>max 回退默认边界
    Given DateTimeInput min="2026-12-01" max="2026-01-01"
    When 解析属性
    Then 上报告警并回退默认边界 1970-01-01 / 2100-12-31 23:59

  Scenario: 校验失败保持弹窗
    Given DateTimeInput checks 且 value 为空（required 不满足）
    When 用户点击确认
    Then 显示错误信息并保持弹窗打开

  Scenario Outline: 模式归一
    Given DateTimeInput enableDate=<d> enableTime=<t>
    When 解析模式
    Then 模式为 <mode>
    Examples:
      | d     | t     | mode       |
      | true  | false | 仅日期     |
      | false | true  | 仅时间     |
      | true  | true  | 日期时间组合 |
```

## Spec 自审清单

- [x] 无"待定""TBD""TODO"等占位符
- [x] 所有 AC 使用 WHEN/THEN 格式，可独立测试
- [x] 范围边界明确（DateTimeInput 组件行为；DatePicker/TimePicker 平台语义不展开）
- [x] 无语义模糊表述
- [x] AC 与规则表交叉一致
- [x] 规则表每条通过 5 项质量检查（可复现/可观测/边界值/关联AC/无冲突）

## context-references

```yaml
context-queries:
  - repo: "GenerativeUI/A2UIRender"
    query: "CustomDateTimeInput enableDate enableTime min max normalize ISO8601 military time"
  - repo: "GenerativeUI/A2UIRender"
    query: "DateTimeInput validateCustomComponentChecks syncComponentBoundDataModel createDateTimeInputDefinition"
  - repo: "GenerativeUI/Docs"
    query: "DateTimeInput 组件 value enableDate enableTime min max label DFX"
```

**关键文档：** `genui/src/main/ets/core/components/A2UI/CustomDateTimeInput.ets`、`reference/standard-components/dateTimeInput.md`