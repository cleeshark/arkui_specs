# 特性规格

> Func-07-04-12-Feat-07 CheckboxGroup 扩展交互组件：固化 A2UI 扩展协议交互组件 CheckboxGroup 的属性契约（`group`/`selectAll`）、样式契约（选中色/未选中色/勾选标记/组形状）、组变化事件（`onChange {value:string[], status:'All'|'Part'|'None'}`）与选中名集合语义。基准实现：`@arkui-genius/genui`（A2UIRender），原生 C++ 路径。取值函数 `getCheckboxGroupValues` 关联见 07-04-16，本域只写组件契约。

## 概述

| 属性 | 值 |
|------|-----|
| 特性名称 | CheckboxGroup 扩展交互组件 |
| 特性编号 | Func-07-04-12-Feat-07 |
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
| 协议 Schema | `specification/extended/1.0.0/extended_catalog.json`（`components.CheckboxGroup`） | — |
| 原生组件（C++） | `genui/src/main/cpp/components/extended/ExtendedCheckboxGroupComponent.h/.cpp` | — |
| 文档参考 | `reference/extended-components/checkbox-group.md` | 理解辅助 |

> 需求基线、不涉及项详见 proposal.md。design.md 与本文档并行产出，互不依赖。

---

## 用户故事

### US-1: 组名与全选属性契约

**作为** 生成式 UI 宿主开发者，
**我想要** 通过 `group`/`selectAll` 控制复选框组，
**以便** 统一控制组内全部复选框。

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-1.1 | WHEN `group` 字符串 THEN `SetGroup` 拼装 native 组名 `a2ui:renderId:surfaceId:group`（`ExtendedCheckboxGroupComponent.cpp:700-708`） | 正常 |
| AC-1.2 | WHEN `group` 缺失 THEN 回落 `""`（`fallbackString=""`，`ExtendedCheckboxGroupComponent.cpp:173-182`） | 边界 |
| AC-1.3 | WHEN `selectAll=true` THEN `SetSelectAll(true)` 全选组内复选框（`ExtendedCheckboxGroupComponent.cpp:648-655`） | 正常 |
| AC-1.4 | WHEN `selectAll` 缺失 THEN 回落 `false`（`fallbackBool=false`，`ExtendedCheckboxGroupComponent.cpp:184-191`） | 边界 |
| AC-1.5 | WHEN `selectAll` 移除 THEN `OnPropertyRemoved` 复位 false（`ExtendedCheckboxGroupComponent.cpp:504-507`） | 边界 |

### US-2: 组变化事件契约

**作为** 生成式 UI 宿主开发者，
**我想要** 监听组选择变化，
**以便** 处理全选/部分/无选中三种状态。

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-2.1 | WHEN 组选择变化 THEN 派发 `onChange`，负载 `{value:string[], status}`（`BuildGroupChangeEventContext`，`ExtendedCheckboxGroupComponent.cpp:67-83`） | 正常 |
| AC-2.2 | THEN `status` 映射 `0→All`/`1→Part`/`2→None`（`SelectAllStatusToString`，`ExtendedCheckboxGroupComponent.cpp:53-65`） | 正常 |
| AC-2.3 | THEN `selectAllStatus_` 缺省 `2`(None)（`ExtendedCheckboxGroupComponent.h:168`） | 边界 |
| AC-2.4 | WHEN ArkUI 字符串事件（`Name:...Status:...`） THEN 解析选中名与状态（`HandleNodeEvent`/`ParseNamesFromEventString`/`ParseStatusFromEventString`，`ExtendedCheckboxGroupComponent.cpp:555-621`） | 正常 |
| AC-2.5 | WHEN 无 `onChange` 事件处理 THEN 不注册监听（`UpdateChangeEventRegistration`，`ExtendedCheckboxGroupComponent.cpp:628-646`） | 边界 |

### US-3: 样式契约

**作为** 生成式 UI 宿主开发者，
**我想要** 通过 `styles` 控制组样式，
**以便** 定制颜色/勾选标记/默认形状。

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-3.1 | WHEN `styles.selectedColor`/`unSelectedColor` 合法 THEN 应用（`ExtendedCheckboxGroupComponent.cpp:446-458`） | 正常 |
| AC-3.2 | WHEN `styles.checkboxShape` 为 `circle`/`rounded_square` THEN `SetShape` 应用，缺省 `circle`（`ExtendedCheckboxGroupComponent.cpp:460-468`） | 正常 |
| AC-3.3 | WHEN `styles.mark` 为 `{strokeColor,size,strokeWidth}` 合法 THEN `SetMark` 应用（`ExtendedCheckboxGroupComponent.cpp:470-494`） | 正常 |
| AC-3.4 | WHEN 传入 `styles.unselectedColor`/`styles.shape`（case 与 schema 不符）THEN 告警「undefined for CheckboxGroup」并忽略（`ExtendedCheckboxGroupComponent.cpp:207-215`） | 异常 |
| AC-3.5 | WHEN 颜色/mark 非法 THEN `ValidateStylesSchema` 告警回落默认（`ExtendedCheckboxGroupComponent.cpp:201-238,345-439`） | 异常 |

## 验收追溯

| AC编号 | 关联规则 | 关联 Task | 验证方式 | 证据 |
|----|---------|----------|---------|------|
| AC-1.1,AC-1.2,AC-1.3,AC-1.4,AC-1.5 | R-1 | T-7 | C++ UT（`GetSelectAllForTest`/`GetGroupForTest`） | `ExtendedCheckboxGroupComponent.cpp:648-708` |
| AC-2.1,AC-2.2,AC-2.3,AC-2.4,AC-2.5 | R-2,R-3 | T-7 | C++ UT + ohosTest | `ExtendedCheckboxGroupComponent.cpp:53-83,555-646` |
| AC-3.1,AC-3.2,AC-3.3,AC-3.4,AC-3.5 | R-4 | T-7 | C++ UT + 告警 | `ExtendedCheckboxGroupComponent.cpp:446-494` |

## 规则定义

| 规则ID | 类型 | 触发条件 | 预期行为 | 边界/约束 | 关联AC |
|--------|------|---------|---------|----------|--------|
| R-1 | 行为 | `group`/`selectAll` 设置 | 组名拼装/全选控制 | 缺失回落 ""/false | AC-1.1,AC-1.2,AC-1.3,AC-1.4,AC-1.5 |
| R-2 | 行为 | 组选择变化 | 派发 onChange `{value[],status}` | status 0/1/2 | AC-2.1,AC-2.2,AC-2.3,AC-2.4 |
| R-3 | 边界 | 无 onChange 处理 | 不注册监听 | `HasEventHandler("onChange")` | AC-2.5 |
| R-4 | 异常 | 样式非法/case 不符 | 告警回落默认/忽略 | schema 键 `unSelectedColor`/`checkboxShape` | AC-3.1,AC-3.2,AC-3.3,AC-3.4,AC-3.5 |

## 验证映射

| 编号 | 对应规格项 | 验证方式 | 验证重点 |
|------|----------|---------|---------|
| VM-1 | AC-1.1,AC-1.2,AC-1.3,AC-1.4,AC-1.5 属性 | C++ UT | group/selectAll 契约 |
| VM-2 | AC-2.1,AC-2.2,AC-2.3,AC-2.4,AC-2.5 事件 | C++ UT + ohosTest | status 枚举 + 事件负载 |
| VM-3 | AC-3.1,AC-3.2,AC-3.3,AC-3.4,AC-3.5 样式 | C++ UT + 告警 | checkboxShape/mark 默认 + case 分歧 |

## API 变更分析

> 存量补录，无新增/变更 API。

### 新增 API

N/A。

### 变更/废弃 API

| API 名称 | 变更类型 | 影响场景 | 迁移指引 | 关联 AC |
|----------|---------|---------|---------|--------|
| 扩展协议组件 `CheckboxGroup`（`extended_catalog.json`） | 既有 | 组全选/全不选控制 | 描述符契约，无迁移 | AC-1.1,AC-1.2,AC-1.3,AC-1.4,AC-1.5,AC-2.1,AC-2.2,AC-2.3,AC-2.4,AC-2.5,AC-3.1,AC-3.2,AC-3.3,AC-3.4,AC-3.5 |

> 契约位置：`specification/extended/1.0.0/extended_catalog.json`。Kit：`@arkui-genius/genui`；权限：无。

## 接口规格

### 接口定义

**`CheckboxGroup` 组件描述符（`components.CheckboxGroup`）**

| 属性 | 值 |
|------|-----|
| 函数签名 | 组件描述符（JSON object），`GetType()=="CheckboxGroup"`（`ExtendedCheckboxGroupComponent.cpp:159-162`） |
| 返回值 | 原生 `CHECKBOX_GROUP` 节点 |
| 开放范围 | 扩展协议组件契约（非 ArkTS/C-API） |
| 错误码 | N/A（非法样式经 `ReportExtendedSchemaWarning` 上报告警） |
| 关联 AC | AC-1.1,AC-2.1 |

**参数约束**

| 参数 | 类型 | 必填 | 默认值 | 约束条件 |
|------|------|------|--------|---------|
| group | string | 否 | `""` | 匹配组内 Checkbox group |
| selectAll | boolean | 否 | `false` | 缺失回落 false |

**行为场景**

| # | 触发条件 | 预期行为 | 关联 AC |
|---|----------|----------|---------|
| 1 | selectAll=true | 全选组内复选框 | AC-1.3 |
| 2 | 组选择变化 | 派发 onChange{value[],status} | AC-2.1,AC-2.2 |
| 3 | 传入 unselectedColor | 告警忽略 | AC-3.4 |

## 兼容性声明

- **已有 API 行为变更:** 否（存量补录）。
- **配置文件格式变更:** 否。
- **数据存储格式变更:** 否。
- **最低支持版本:** A2UI 扩展协议 1.0.0。
- **API 版本号策略:** `status` 三态（All/Part/None）为扩展协议独有；`getCheckboxGroupValues` 取值函数归 07-04-16。

## 架构约束

| 关键约束 | 约束说明 | 影响 AC |
|---------|---------|--------|
| 组控制 | 组内 Checkbox 经 group 匹配联动 | AC-1.1,AC-1.3 |
| 状态三态 | status 0/1/2 映射 All/Part/None | AC-2.2,AC-2.3 |
| 取值函数边界 | `getCheckboxGroupValues` 归 07-04-16，本域仅组件契约 | 概述 |

## 非功能性需求

| 类型 | 指标/阈值 | 验证方式 | 证据 |
|------|----------|---------|------|
| 可靠性 | 非法输入不抛异常，告警回落 | C++ UT | `ExtendedCheckboxGroupComponent.cpp:201-238` |
| 性能 | 事件解析 O(名字数) 线性 | C++ UT | `ExtendedCheckboxGroupComponent.cpp:587-610` |

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
| 深色模式 | 是 | 选中/未选中色按主题 | AC-3.1,AC-3.2,AC-3.3,AC-3.4,AC-3.5 |
| 多窗口/分屏 | 否 | 无差异 | — |
| 多用户 | 否 | 无差异 | — |
| 版本升级 | 是 | 扩展协议 1.0.0 | 概述「目标版本」 |
| 生态兼容 | 是 | `checkboxShape` 默认形状覆盖 | AC-3.2 |

## 行为场景（可选，Gherkin）

```gherkin
Feature: CheckboxGroup 扩展交互组件
  作为 生成式 UI 宿主开发者
  我想要 组支持全选与三态变化监听
  以便 统一控制多个复选框

  Scenario: 全选
    Given CheckboxGroup selectAll=true 与两个 Checkbox(group="g")
    When 应用组件描述符
    Then 组内复选框全选中，status="All"

  Scenario Outline: 状态映射
    Given 组内选中集合 <selected>
    When 组选择变化
    Then 派发 onChange status=<status>

    Examples:
      | selected | status |
      | 全部 | All |
      | 部分 | Part |
      | 空 | None |
```

## Spec 自审清单

- [x] 无"待定""TBD""TODO"等占位符
- [x] 所有 AC 使用 WHEN/THEN 格式，可独立测试
- [x] 范围边界明确（Feat-07 做 CheckboxGroup 组件契约；`getCheckboxGroupValues` 归 07-04-16）
- [x] 无语义模糊表述
- [x] AC 与规则表交叉一致
- [x] 规则表每条通过 5 项质量检查（可复现/可观测/边界值/关联AC/无冲突）

## context-references

```yaml
context-queries:
  - repo: "GenerativeUI/A2UIRender"
    query: "ExtendedCheckboxGroupComponent group selectAll onChange status All Part None 事件字符串解析"
  - repo: "GenerativeUI/A2UIRender"
    query: "ExtendedCheckboxGroupComponent selectedColor unSelectedColor mark checkboxShape 样式告警回落"
```

**关键文档：** `specification/extended/1.0.0/extended_catalog.json`、`genui/src/main/cpp/components/extended/ExtendedCheckboxGroupComponent.cpp`、`reference/extended-components/checkbox-group.md`