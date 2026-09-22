# 特性规格

> Func-07-04-12-Feat-06 Checkbox 扩展交互组件：固化 A2UI 扩展协议交互组件 Checkbox 的属性契约（`label`/`value`/`group`/`select`）、样式契约（选中色/未选中色/勾选标记/形状）、变化事件（`onChange {value}`）、运行时状态恢复与组继承语义、绑定回写。基准实现：`@arkui-genius/genui`（A2UIRender），原生 C++ 路径。

## 概述

| 属性 | 值 |
|------|-----|
| 特性名称 | Checkbox 扩展交互组件 |
| 特性编号 | Func-07-04-12-Feat-06 |
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
| 协议 Schema | `specification/extended/1.0.0/extended_catalog.json`（`components.Checkbox`） | — |
| 原生组件（C++） | `genui/src/main/cpp/components/extended/ExtendedCheckboxComponent.h/.cpp` | — |
| 文档参考 | `reference/extended-components/checkbox.md` | 理解辅助 |

> 需求基线、不涉及项详见 proposal.md。design.md 与本文档并行产出，互不依赖。

---

## 用户故事

### US-1: 标签/值/组/选中属性契约

**作为** 生成式 UI 宿主开发者，
**我想要** 通过 `label`/`value`/`group`/`select` 配置复选框，
**以便** 呈现多选并区分语义值与所属组。

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-1.1 | WHEN `label` 字符串 THEN `SetLabel` 写入 `textNode_` 文本（`ExtendedCheckboxComponent.cpp:830-837`） | 正常 |
| AC-1.2 | WHEN `value` 字符串 THEN `SetValue` 写入 `value_`（语义标识，不渲染）（`ExtendedCheckboxComponent.cpp:783-786`） | 正常 |
| AC-1.3 | WHEN `group` 字符串 THEN `SetGroup` 拼装 native 组名 `a2ui:renderId:surfaceId:group` 并设 `checkboxName`（`ExtendedCheckboxComponent.cpp:839-850`） | 正常 |
| AC-1.4 | WHEN `select=true` THEN `SetSelect(true)` 置选中（`ExtendedCheckboxComponent.cpp:774-781`） | 正常 |
| AC-1.5 | WHEN `select` 缺失 THEN 回落 `false`（`fallbackBool=false`，`ExtendedCheckboxComponent.cpp:333-341`） | 边界 |
| AC-1.6 | THEN `ApplyPrivateAttributes` 记录 `hasExplicitSelect_`（`ExtendedCheckboxComponent.cpp:275-283`） | 正常 |

### US-2: 选中变化事件与绑定回写

**作为** 生成式 UI 宿主开发者，
**我想要** 监听复选框选中变化，
**以便** 处理多选结果并回写绑定。

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-2.1 | WHEN 用户勾选/取消勾选 THEN `HandleCheckboxChange` 派发 `onChange`，负载 `{value:boolean}`（`ExtendedCheckboxComponent.cpp:746-760,60-69`） | 正常 |
| AC-2.2 | WHEN 选中态无变化 THEN 直接返回不派发（`ExtendedCheckboxComponent.cpp:752-754`） | 边界 |
| AC-2.3 | WHEN `select` 有 path 绑定 THEN `SyncSelectToBoundDataModel` 回写（`ExtendedCheckboxComponent.cpp:904-932`） | 正常 |
| AC-2.4 | WHEN 有 `onClick` 事件 THEN 点击派发 `onClick`（`ExtendedCheckboxComponent.cpp:657-663,732-734`） | 正常 |

### US-3: 运行时状态与组继承

**作为** 生成式 UI 宿主开发者，
**我想要** 复选框选中态可恢复且继承组状态，
**以便** 重建组件时保留选中并响应组 selectAll。

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-3.1 | WHEN 选中变化 THEN `SyncRuntimeStateToSurface` 存储 `{group,key,value,select}`（`ExtendedCheckboxComponent.cpp:212-228,878-891`） | 正常 |
| AC-3.2 | WHEN 组件重建且无显式 `select` THEN `ApplyInheritedSelect` 先尝试 runtime state 恢复再继承组值（`ExtendedCheckboxComponent.cpp:256-265`） | 正常 |
| AC-3.3 | WHEN `hasExplicitSelect_` 为真 THEN 不继承、不恢复（`ExtendedCheckboxComponent.cpp:258-260`） | 边界 |
| AC-3.4 | WHEN 无显式 `shape` THEN `ApplyInheritedShape` 从组继承 `checkboxShape`（`ExtendedCheckboxComponent.cpp:267-273`） | 正常 |

### US-4: 样式契约

**作为** 生成式 UI 宿主开发者，
**我想要** 通过 `styles` 控制复选框样式，
**以便** 定制颜色/勾选标记/形状。

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-4.1 | WHEN `styles.selectedColor`/`unSelectedColor` 合法 THEN 应用（`ExtendedCheckboxComponent.cpp:601-618`） | 正常 |
| AC-4.2 | WHEN `styles.mark` 为 `{strokeColor,size,strokeWidth}` 合法 THEN `SetMark` 应用（`ExtendedCheckboxComponent.cpp:630-654`） | 正常 |
| AC-4.3 | WHEN `styles.shape` 为 `circle`/`rounded_square` THEN `SetShape` 应用，缺省 `circle`（`ExtendedCheckboxComponent.cpp:620-628`） | 正常 |
| AC-4.4 | WHEN 样式非法（颜色/mark/shape） THEN `ValidateStylesSchema` 告警回落默认（`ExtendedCheckboxComponent.cpp:372-419,526-572`） | 异常 |
| AC-4.5 | WHEN `mark.size<=0` THEN `SetMark` 仅传 strokeColor（省略 size/width）（`ExtendedCheckboxComponent.cpp:814-818`） | 边界 |

## 验收追溯

| AC编号 | 关联规则 | 关联 Task | 验证方式 | 证据 |
|----|---------|----------|---------|------|
| AC-1.1,AC-1.2,AC-1.3,AC-1.4,AC-1.5,AC-1.6 | R-1,R-2 | T-6 | C++ UT（`GetSelectForTest`/`GetValueForTest`） | `ExtendedCheckboxComponent.cpp:774-850` |
| AC-2.1,AC-2.2,AC-2.3,AC-2.4 | R-3 | T-6 | C++ UT + ohosTest | `ExtendedCheckboxComponent.cpp:746-760` |
| AC-3.1,AC-3.2,AC-3.3,AC-3.4 | R-4,R-5 | T-6 | C++ UT | `ExtendedCheckboxComponent.cpp:256-273,878-891` |
| AC-4.1,AC-4.2,AC-4.3,AC-4.4,AC-4.5 | R-6 | T-6 | C++ UT + 告警 | `ExtendedCheckboxComponent.cpp:372-419,601-654` |

## 规则定义

| 规则ID | 类型 | 触发条件 | 预期行为 | 边界/约束 | 关联AC |
|--------|------|---------|---------|----------|--------|
| R-1 | 行为 | `label`/`value`/`group`/`select` 设置 | 写入内部态 + 呈现/组名 | value 为语义标识不渲染 | AC-1.1,AC-1.2,AC-1.3,AC-1.4,AC-1.5 |
| R-2 | 行为 | 属性解析 | 记录 `hasExplicitSelect_` | 门控继承 | AC-1.6 |
| R-3 | 行为 | 选中变化 | 派发 onChange `{value}` + 回写绑定/运行时态 | 无变化不派发 | AC-2.1,AC-2.2,AC-2.3,AC-2.4 |
| R-4 | 边界 | 无显式 select 重建 | 运行时态恢复 > 组继承 | 显式 select 优先 | AC-3.1,AC-3.2,AC-3.3 |
| R-5 | 行为 | 无显式 shape | 从组继承 checkboxShape | 显式 shape 优先 | AC-3.4 |
| R-6 | 异常 | 样式非法 | 告警回落默认 | mark.size<=0 省略 size/width | AC-4.1,AC-4.2,AC-4.3,AC-4.4,AC-4.5 |

## 验证映射

| 编号 | 对应规格项 | 验证方式 | 验证重点 |
|------|----------|---------|---------|
| VM-1 | AC-1.1,AC-1.2,AC-1.3,AC-1.4,AC-1.5,AC-1.6 属性 | C++ UT | label/value/group/select 契约 |
| VM-2 | AC-2.1,AC-2.2,AC-2.3,AC-2.4 事件 | C++ UT + ohosTest | onChange 负载 + 绑定回写 |
| VM-3 | AC-3.1,AC-3.2,AC-3.3,AC-3.4 状态继承 | C++ UT | runtime state 恢复 + 组继承 |
| VM-4 | AC-4.1,AC-4.2,AC-4.3,AC-4.4,AC-4.5 样式 | C++ UT + 告警 | 颜色/mark/shape 默认值 |

## API 变更分析

> 存量补录，无新增/变更 API。

### 新增 API

N/A。

### 变更/废弃 API

| API 名称 | 变更类型 | 影响场景 | 迁移指引 | 关联 AC |
|----------|---------|---------|---------|--------|
| 扩展协议组件 `Checkbox`（`extended_catalog.json`） | 既有 | 多选渲染 | 描述符契约，无迁移 | AC-1.1,AC-1.2,AC-1.3,AC-1.4,AC-1.5,AC-1.6,AC-2.1,AC-2.2,AC-2.3,AC-2.4,AC-3.1,AC-3.2,AC-3.3,AC-3.4,AC-4.1,AC-4.2,AC-4.3,AC-4.4,AC-4.5 |

> 契约位置：`specification/extended/1.0.0/extended_catalog.json`。Kit：`@arkui-genius/genui`；权限：无。

## 接口规格

### 接口定义

**`Checkbox` 组件描述符（`components.Checkbox`）**

| 属性 | 值 |
|------|-----|
| 函数签名 | 组件描述符（JSON object），`GetType()=="Checkbox"`（`ExtendedCheckboxComponent.cpp:173-176`） |
| 返回值 | 复合 `ROW` 节点（内挂 `CHECKBOX`+`TEXT`） |
| 开放范围 | 扩展协议组件契约（非 ArkTS/C-API） |
| 错误码 | N/A（非法样式经 `ReportExtendedSchemaWarning` 上报告警） |
| 关联 AC | AC-1.1,AC-2.1 |

**参数约束**

| 参数 | 类型 | 必填 | 默认值 | 约束条件 |
|------|------|------|--------|---------|
| label | string | 否 | `""` | 任一字符串 |
| value | string | 否 | `""` | 语义标识，非空时作为 native name |
| group | string | 否 | `""` | 匹配 CheckboxGroup group |
| select | boolean | 否 | `false` | 缺失回落 false |

**行为场景**

| # | 触发条件 | 预期行为 | 关联 AC |
|---|----------|----------|---------|
| 1 | 用户勾选 | 派发 onChange{value:true} + 回写 + 存 runtime state | AC-2.1,AC-3.1 |
| 2 | 重建无显式 select | 恢复 runtime state 或继承组 | AC-3.2 |
| 3 | mark.size<=0 | 仅传 strokeColor | AC-4.5 |

## 兼容性声明

- **已有 API 行为变更:** 否（存量补录）。
- **配置文件格式变更:** 否。
- **数据存储格式变更:** 否（runtime state 为内存态，无持久化）。
- **最低支持版本:** A2UI 扩展协议 1.0.0。
- **API 版本号策略:** `value` 作为组内区分语义标识（经 `getCheckboxGroupValues` 读取，归 07-04-16）。

## 架构约束

| 关键约束 | 约束说明 | 影响 AC |
|---------|---------|--------|
| 组联动 | Checkbox 须与 CheckboxGroup 配对，group 匹配 | AC-1.3,AC-3.1,AC-3.2,AC-3.3,AC-3.4 |
| 继承优先级 | 显式 > runtime state 恢复 > 组继承 | AC-3.1,AC-3.2,AC-3.3,AC-3.4 |
| 绑定回写 | select 绑定变化回写 | AC-2.3 |

## 非功能性需求

| 类型 | 指标/阈值 | 验证方式 | 证据 |
|------|----------|---------|------|
| 可靠性 | 非法输入不抛异常，告警回落 | C++ UT | `ExtendedCheckboxComponent.cpp:372-419` |
| 性能 | mark 动态成员解析 O(members) | C++ UT | `ExtendedCheckboxComponent.cpp:447-483` |

## 多设备适配声明

| 设备类型 | 行为差异 | 规格/约束 | 验证方式 | 证据 |
|---------|---------|----------|---------|------|
| 手机 | 无差异 | 组件契约设备无关 | ohosTest | — |
| 平板 | 无差异 | 同上 | ohosTest | — |
| 折叠屏 | 无差异 | 同上 | ohosTest | — |

## 全局特性影响

| 特性 | 适用？ | 结论 | 关联场景 |
|------|-------|------|---------|
| 无障碍 | 是 | 通用 `accessibility.label/description` | 概述「组件公共结构」 |
| 大字体 | 否 | 无文字字号配置 | — |
| 深色模式 | 是 | 选中/未选中色按主题 | AC-4.1,AC-4.2,AC-4.3,AC-4.4,AC-4.5 |
| 多窗口/分屏 | 否 | 无差异 | — |
| 多用户 | 否 | 无差异 | — |
| 版本升级 | 是 | 扩展协议 1.0.0 | 概述「目标版本」 |
| 生态兼容 | 是 | `shape` circle/rounded_square 扩展行为 | AC-4.3 |

## 行为场景（可选，Gherkin）

```gherkin
Feature: Checkbox 扩展交互组件
  作为 生成式 UI 宿主开发者
  我想要 复选框支持多选/组继承/状态恢复
  以便 提供多选交互

  Scenario: 用户勾选
    Given Checkbox 描述符 select=false
    When 用户勾选
    Then 派发 onChange{value:true} 并存储 runtime state

  Scenario: 组继承
    Given CheckboxGroup selectAll=true 与 Checkbox(group="g", 无显式 select)
    When Checkbox 应用组继承
    Then Checkbox 置选中

  Scenario Outline: 形状映射
    Given Checkbox 描述符 styles.shape=<shape>
    When 渲染
    Then 呈现 <result>

    Examples:
      | shape | result |
      | "circle" | 圆形 |
      | "rounded_square" | 圆角方形 |
```

## Spec 自审清单

- [x] 无"待定""TBD""TODO"等占位符
- [x] 所有 AC 使用 WHEN/THEN 格式，可独立测试
- [x] 范围边界明确（Feat-06 做 Checkbox 组件契约；`getCheckboxGroupValues` 归 07-04-16）
- [x] 无语义模糊表述
- [x] AC 与规则表交叉一致
- [x] 规则表每条通过 5 项质量检查（可复现/可观测/边界值/关联AC/无冲突）

## context-references

```yaml
context-queries:
  - repo: "GenerativeUI/A2UIRender"
    query: "ExtendedCheckboxComponent label value group select onChange 绑定回写 运行时状态恢复"
  - repo: "GenerativeUI/A2UIRender"
    query: "ExtendedCheckboxComponent ApplyInheritedSelect ApplyInheritedShape mark shape 样式告警回落"
```

**关键文档：** `specification/extended/1.0.0/extended_catalog.json`、`genui/src/main/cpp/components/extended/ExtendedCheckboxComponent.cpp`、`reference/extended-components/checkbox.md`