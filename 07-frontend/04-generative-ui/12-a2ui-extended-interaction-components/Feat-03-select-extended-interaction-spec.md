# 特性规格

> Func-07-04-12-Feat-03 Select 扩展交互组件：固化 A2UI 扩展协议交互组件 Select 的属性契约（`options`/`selected`/`value`/`onSelect`）、下拉菜单样式契约（分隔线/字体/颜色/间距/箭头位置/菜单对齐/选项宽高/菜单背景）、选择事件（`onSelect` 同时派发 `onChange`，负载 `{index,value}`）与默认值语义。基准实现：`@arkui-genius/genui`（A2UIRender），ArkTS 自定义组件路径（无 C++ 原生实现）。

## 概述

| 属性 | 值 |
|------|-----|
| 特性名称 | Select 扩展交互组件 |
| 特性编号 | Func-07-04-12-Feat-03 |
| 优先级 | P1 |
| 目标版本 | A2UI 扩展协议 1.0.0 |
| SIG 归属 | GenUI SIG |
| 状态 | Baselined |
| 复杂度 | 标准 |

## 本次变更范围（Delta）

| 类型 | 内容 | 说明 |
|------|------|------|
| ADDED | 无（存量补录） | 存量特性（lineage: new-on-legacy） |

## 输入文档

| 文档 | 路径 | 状态 |
|------|------|------|
| Design | `07-frontend/04-generative-ui/12-a2ui-extended-interaction-components/design.md` | Baselined |
| 协议 Schema | `specification/extended/1.0.0/extended_catalog.json`（`components.Select`） | — |
| 自定义组件（ArkTS） | `genui/src/main/ets/core/components/extended/ExtendedSelect.ets` | — |
| 目录注册（ArkTS） | `genui/src/main/ets/core/components/A2UI/A2UIExtendedComponents.ets` | — |
| 文档参考 | `reference/extended-components/select.md` | 理解辅助 |

> 需求基线、不涉及项详见 proposal.md。design.md 与本文档并行产出，互不依赖。

---

## 用户故事

### US-1: 选项与选中属性契约

**作为** 生成式 UI 宿主开发者，
**我想要** 通过 `options`/`selected`/`value` 配置下拉选项与初始选中，
**以便** 正确呈现下拉菜单。

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-1.1 | WHEN 描述符含 `options` 数组 THEN `buildSelectOptions` 将每项 `{value,icon?,symbolIcon?}` 映射为 `SelectOption`（`ExtendedSelect.ets:1388-1402`） | 正常 |
| AC-1.2 | WHEN `selected` 数值给定 THEN `options.selected` 写入该索引（`ExtendedSelect.ets:1609-1615`） | 正常 |
| AC-1.3 | WHEN `selected` 缺失 THEN 回落 `-1`（`currentSelected=-1`，`ExtendedSelect.ets:1256`） | 边界 |
| AC-1.4 | WHEN `value` 缺失 THEN `resolveDisplayValue` 取 `options[selected].value`，无选中则 `""`（`ExtendedSelect.ets:1365-1373`） | 边界 |
| AC-1.5 | WHEN `options` 缺失/解析失败 THEN 回落默认空选项 `createDefaultSelectOptions`（`ExtendedSelect.ets:1597-1602`） | 边界 |

### US-2: 选择事件契约

**作为** 生成式 UI 宿主开发者，
**我想要** 监听用户选择，
**以便** 通过 `onSelect` 处理选择变化。

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-2.1 | WHEN 用户选择某选项 THEN ArkUI `onSelect` 回调更新 `currentSelected`/`currentValue` 并派发事件（`ExtendedSelect.ets:1338-1344`） | 正常 |
| AC-2.2 | THEN `dispatchSelectChange` 同时派发 `onSelect` 与 `onChange`，负载均为 `{index,value}`（`ExtendedSelect.ets:1470-1477`） | 正常 |
| AC-2.3 | WHEN 用户点击下拉按钮 THEN `dispatchSelectClick` 派发 `onClick`，负载 `{x,y}`（`ExtendedSelect.ets:1479-1485`） | 正常 |

### US-3: 下拉菜单样式契约

**作为** 生成式 UI 宿主开发者，
**我想要** 通过 `styles` 控制下拉菜单样式，
**以便** 定制字体/颜色/间距/对齐。

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-3.1 | WHEN `styles.arrowPosition` 为 `start`/`end` THEN 映射 `ArrowPosition.START/END`，缺省 `end`（`ExtendedSelect.ets:48-55,1547-1551`） | 正常 |
| AC-3.2 | WHEN `styles.menuAlign.alignType` 为 `start`/`center`/`end` THEN 映射 `MenuAlignType`，缺省 `start`（`ExtendedSelect.ets:51-54,1553-1561`） | 正常 |
| AC-3.3 | WHEN `styles.space` 数值 THEN `space<=8` 用默认（忽略），`>8` 应用（`ExtendedSelect.ets:1327`） | 边界 |
| AC-3.4 | WHEN `styles.optionWidth<56vp` THEN 用默认（忽略）；`optionHeight=0` 用默认（`ExtendedSelect.ets:1330-1331`） | 边界 |
| AC-3.5 | WHEN 未指定颜色 THEN 按主题取默认（`resolveThemeColor`，light/dark 双色，`ExtendedSelect.ets:1487-1489`） | 正常 |
| AC-3.6 | WHEN `styles.divider` 为 null THEN 不显示分隔线（`currentDividerNull`，`ExtendedSelect.ets:1336-1337`） | 边界 |

## 验收追溯

| AC编号 | 关联规则 | 关联 Task | 验证方式 | 证据 |
|----|---------|----------|---------|------|
| AC-1.1,AC-1.2,AC-1.3,AC-1.4,AC-1.5 | R-1,R-2 | T-3 | ArkTS 单测 | `ExtendedSelect.ets:1388-1402,1609-1615` |
| AC-2.1,AC-2.2,AC-2.3 | R-3 | T-3 | ArkTS 单测 + ohosTest | `ExtendedSelect.ets:1338-1344,1470-1485` |
| AC-3.1,AC-3.2,AC-3.3,AC-3.4,AC-3.5,AC-3.6 | R-4,R-5 | T-3 | ArkTS 单测 | `ExtendedSelect.ets:1327-1337,1547-1561` |

## 规则定义

| 规则ID | 类型 | 触发条件 | 预期行为 | 边界/约束 | 关联AC |
|--------|------|---------|---------|----------|--------|
| R-1 | 行为 | `options` 数组给定 | 映射 `SelectOption[]` 呈现 | 每项 value 必填，icon/symbolIcon 可选 | AC-1.1 |
| R-2 | 边界 | `selected`/`value` 缺失 | 回落 -1 / 取 options[selected].value | 无选中显示空 | AC-1.3,AC-1.4,AC-1.5 |
| R-3 | 行为 | 用户选择/点击 | 派发 onSelect+onChange / onClick | 负载键 {index,value}/{x,y} | AC-2.1,AC-2.2,AC-2.3 |
| R-4 | 边界 | space/optionWidth/optionHeight 越界 | 用默认值 | space<=8、optionWidth<56、optionHeight=0 | AC-3.3,AC-3.4 |
| R-5 | 行为 | 颜色未指定 | 主题默认（light/dark） | `resolveThemeColor` | AC-3.5,AC-3.6 |

## 验证映射

| 编号 | 对应规格项 | 验证方式 | 验证重点 |
|------|----------|---------|---------|
| VM-1 | AC-1.1,AC-1.2,AC-1.3,AC-1.4,AC-1.5 选项 | ArkTS 单测 | options 映射、selected/value 回落 |
| VM-2 | AC-2.1,AC-2.2,AC-2.3 事件 | ArkTS 单测 | onSelect 双派发、onClick 负载 |
| VM-3 | AC-3.1,AC-3.2,AC-3.3,AC-3.4,AC-3.5,AC-3.6 样式 | ArkTS 单测 | 箭头/对齐/间距/宽度默认值 |

## API 变更分析

> 存量补录，无新增/变更 API。Select 为 ArkTS 自定义组件，无 C++ 原生实现。

### 新增 API

N/A。

### 变更/废弃 API

| API 名称 | 变更类型 | 影响场景 | 迁移指引 | 关联 AC |
|----------|---------|---------|---------|--------|
| 扩展协议组件 `Select`（`extended_catalog.json`） | 既有 | 下拉选择渲染 | 描述符契约，无迁移 | AC-1.1,AC-1.2,AC-1.3,AC-1.4,AC-1.5,AC-2.1,AC-2.2,AC-2.3,AC-3.1,AC-3.2,AC-3.3,AC-3.4,AC-3.5,AC-3.6 |

> 契约位置：`specification/extended/1.0.0/extended_catalog.json`。Kit：`@arkui-genius/genui`；权限：无。

## 接口规格

### 接口定义

**`Select` 组件描述符（`components.Select`）**

| 属性 | 值 |
|------|-----|
| 函数签名 | 组件描述符（JSON object），`EXTENDED_SELECT_TYPE=="Select"`（`ExtendedSelect.ets:47`） |
| 返回值 | ArkUI `Select` 组件（自定义组件 `ExtendedSelect`，`ExtendedSelect.ets:1253`） |
| 开放范围 | 扩展协议组件契约（非 ArkTS/C-API） |
| 错误码 | N/A（`validateExtendedSelectSchemaForWarning` 上报 schema 告警） |
| 关联 AC | AC-1.1,AC-2.2 |

**参数约束**

| 参数 | 类型 | 必填 | 默认值 | 约束条件 |
|------|------|------|--------|---------|
| options | array | 否 | `[]` | 每项 `{value(必填),icon?,symbolIcon?}` |
| selected | number | 否 | `-1` | 选项索引 |
| value | string | 否 | `options[selected].value` | 按钮显示文本 |

**行为场景**

| # | 触发条件 | 预期行为 | 关联 AC |
|---|----------|----------|---------|
| 1 | 含 options + selected | 呈现下拉并定位选中项 | AC-1.1,AC-1.2 |
| 2 | 用户选择 | 派发 onSelect + onChange | AC-2.1,AC-2.2 |
| 3 | optionWidth<56 | 用默认宽度 | AC-3.4 |

## 兼容性声明

- **已有 API 行为变更:** 否（存量补录）。
- **配置文件格式变更:** 否。
- **数据存储格式变更:** 否。
- **最低支持版本:** A2UI 扩展协议 1.0.0。
- **API 版本号策略:** `symbolIcon.src` 枚举由 `getIconSystemSymbolNames()` 限定；`onSelect` 与 `onChange` 双派发为扩展协议 Select 独有行为。

## 架构约束

| 关键约束 | 约束说明 | 影响 AC |
|---------|---------|--------|
| ArkTS 自定义路径 | Select 无 C++ 原生实现，经 `CustomComponentFactory` 注册 | AC-1.1,AC-1.2,AC-1.3,AC-1.4,AC-1.5,AC-2.1,AC-2.2,AC-2.3,AC-3.1,AC-3.2,AC-3.3,AC-3.4,AC-3.5,AC-3.6 |
| onSelect/onChange 双派发 | 选择变化同时派发两个事件 | AC-2.2 |
| schema 告警 | `validateExtendedSelectSchemaForWarning` 前置校验 | AC-3.1,AC-3.2,AC-3.3,AC-3.4,AC-3.5,AC-3.6 |

## 非功能性需求

| 类型 | 指标/阈值 | 验证方式 | 证据 |
|------|----------|---------|------|
| 可靠性 | 解析失败回落默认空选项，不抛异常 | ArkTS 单测 | `ExtendedSelect.ets:1597-1602` |
| 性能 | 选项映射 O(n) 线性 | ArkTS 单测 | `ExtendedSelect.ets:1388-1402` |

## 多设备适配声明

| 设备类型 | 行为差异 | 规格/约束 | 验证方式 | 证据 |
|---------|---------|----------|---------|------|
| 手机 | 无差异 | 组件契约设备无关 | ohosTest | — |
| 平板 | 无差异 | 同上 | ohosTest | — |
| 折叠屏 | 无差异 | 同上 | ohosTest | — |

## 全局特性影响

| 特性 | 适用？ | 结论 | 关联场景 |
|------|-------|------|---------|
| 无障碍 | 是 | `accessibilityText`/`accessibilityDescription`（`ExtendedSelect.ets:1360-1361`） | AC-3.1,AC-3.2,AC-3.3,AC-3.4,AC-3.5,AC-3.6 |
| 大字体 | 是 | `styles.font` 字号 | AC-3.1,AC-3.2,AC-3.3,AC-3.4,AC-3.5,AC-3.6 |
| 深色模式 | 是 | 颜色按主题双色 | AC-3.5 |
| 多窗口/分屏 | 否 | 无差异 | — |
| 多用户 | 否 | 无差异 | — |
| 版本升级 | 是 | 扩展协议 1.0.0 | 概述「目标版本」 |
| 生态兼容 | 是 | 下拉菜单基于 ArkUI `Select` 组件 | AC-1.1,AC-1.2,AC-1.3,AC-1.4,AC-1.5 |

## 行为场景（可选，Gherkin）

```gherkin
Feature: Select 扩展交互组件
  作为 生成式 UI 宿主开发者
  我想要 下拉选择支持选项/选中/样式定制
  以便 提供多选项选择交互

  Scenario: 用户选择选项
    Given Select 描述符 options=[{value:"北京"},{value:"上海"}]
    When 用户选择 "上海"
    Then 派发 onSelect{index:1,value:"上海"} 与 onChange{index:1,value:"上海"}

  Scenario Outline: 菜单样式默认值
    Given Select 描述符 styles=<style>
    When 渲染下拉菜单
    Then 应用 <result>

    Examples:
      | style | result |
      | {"space":4} | 用默认间距 8 |
      | {"optionWidth":40} | 用默认宽度（<56vp） |
      | {"arrowPosition":"start"} | 箭头在文本前 |
```

## Spec 自审清单

- [x] 无"待定""TBD""TODO"等占位符
- [x] 所有 AC 使用 WHEN/THEN 格式，可独立测试
- [x] 范围边界明确（Feat-03 做 Select 组件契约；`getSelectValue` 归 07-04-16）
- [x] 无语义模糊表述
- [x] AC 与规则表交叉一致
- [x] 规则表每条通过 5 项质量检查（可复现/可观测/边界值/关联AC/无冲突）

## context-references

```yaml
context-queries:
  - repo: "GenerativeUI/A2UIRender"
    query: "ExtendedSelect options selected value onSelect onChange 双派发 dispatchSelectChange"
  - repo: "GenerativeUI/A2UIRender"
    query: "ExtendedSelect arrowPosition menuAlign optionWidth optionHeight space divider 主题颜色"
```

**关键文档：** `specification/extended/1.0.0/extended_catalog.json`、`genui/src/main/ets/core/components/extended/ExtendedSelect.ets`、`reference/extended-components/select.md`