# 特性规格

## 概述

| 字段 | 内容 |
|------|------|
| 特性名称 | AlertDialog/ActionSheet 命令式 API（AlertDialog、ActionSheet） |
| 特性编号 | Func-05-06-04-Feat-02 |
| FuncID | 05-06-04 |
| 所属 Epic | 无 |
| 优先级 | P0 |
| 目标版本 | API 7 ~ API 26+ |
| SIG 归属 | ArkUI SIG |
| 状态 | Baselined |
| 复杂度 | 标准 |
| lineage | new-on-legacy（已有实现的规格补录） |

## 本次变更范围（Delta）

> 本特性为已有实现补录，非增量变更。以下列出自 API 7 以来的关键变更里程碑。

| 类型 | 内容 | 说明 |
|------|------|------|
| ADDED | AlertDialog.show() | @since 7 |
| ADDED | ActionSheet.show() | @since 8 |
| ADDED | AlertDialog subtitle, primaryButton, secondaryButton, buttons, buttonDirection 属性 | @since 10 |
| MODIFIED | AlertDialog.show() | @since 26 标记废弃，推荐使用 UIContext.showAlertDialog |
| MODIFIED | ActionSheet.show() | @since 26 标记废弃，推荐使用 UIContext.showActionSheet |

## 输入文档

- **需求基线**: 已有能力补录（无独立 requirement.md / proposal.md）
- **设计文档**: `specs/05-ui-components/06-popup-components/04-custom-dialog/design.md`
- **KB 路由**: `docs/kb/components/overlay/dialog.md`
- **SDK 类型定义**:
  - Dynamic API (AlertDialog): `interface/sdk-js/api/@internal/component/ets/alert_dialog.d.ts`
  - Dynamic API (ActionSheet): `interface/sdk-js/api/@internal/component/ets/action_sheet.d.ts`

> 需求基线、不涉及项、受影响子系统与仓库详见 proposal.md，本文档不重复摘录。design.md 与本文档并行产出，互不依赖。

## 用户故事

### US-1: AlertDialog

**角色**: 应用开发者
**期望**: 我想要使用 AlertDialog.show() 显示告警对话框
**价值**: 以便快速显示标准化的告警信息

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-1.1 | WHEN 调用 `AlertDialog.show({ title: 'Title', message: 'Message', confirm: { value: 'OK' } })` THEN 显示告警对话框，含标题、消息和确认按钮 | 正常 |
| AC-1.2 | WHEN 设置 `subtitle`（@since 10）THEN 对话框显示副标题 | 正常 |
| AC-1.3 | WHEN 设置 `primaryButton` 和 `secondaryButton`（@since 10）THEN 对话框显示主/次两个按钮 | 正常 |
| AC-1.4 | WHEN 设置 `buttons` 数组（@since 10）THEN 对话框显示多个按钮 | 正常 |
| AC-1.5 | WHEN 设置 `buttonDirection: DialogButtonDirection.HORIZONTAL`（@since 10）THEN 按钮水平排列 | 正常 |
| AC-1.6 | WHEN 设置 `buttonDirection: DialogButtonDirection.VERTICAL`（@since 10）THEN 按钮垂直排列 | 正常 |
| AC-1.7 | WHEN API >= 26 调用 AlertDialog.show() THEN 标记为 @deprecated，推荐使用 CustomDialogController | 边界 |

### US-2: ActionSheet

**角色**: 应用开发者
**期望**: 我想要使用 ActionSheet.show() 显示选择列表对话框
**价值**: 以便用户从多个选项中选择

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-2.1 | WHEN 调用 `ActionSheet.show({ title: 'Title', message: 'Message', sheets: [{ title: 'A', action: () => {} }], confirm: { value: 'Cancel' } })` THEN 显示选择列表对话框 | 正常 |
| AC-2.2 | WHEN 设置 `subtitle` THEN 对话框显示副标题 | 正常 |
| AC-2.3 | WHEN 用户点击 sheets 中的选项 THEN 执行对应 action 回调，对话框关闭 | 正常 |
| AC-2.4 | WHEN 设置 `autoCancel: false` THEN 点击遮罩不关闭对话框 | 正常 |
| AC-2.5 | WHEN API >= 26 调用 ActionSheet.show() THEN 标记为 @deprecated，推荐使用 CustomDialogController | 边界 |

## 验收追溯

| AC编号 | 关联规则 | 关联 Task | 验证方式 | 证据 |
|-------|----------|-----------|----------|------|
| AC-1.1 ~ AC-1.7 | R-1, R-2 | TASK-DIALOG-01 | UT | alert_dialog 单测 |
| AC-2.1 ~ AC-2.5 | R-3, R-4 | TASK-DIALOG-01 | UT | action_sheet 单测 |

## 规则定义

> **统一规则表，取消 FR/BR/EX/RC 四分类。** 类型标签：**行为**（正常路径下的系统行为）、**边界**（输入/状态的临界点）、**异常**（非法输入或异常状态的处理）、**恢复**（系统异常后的恢复策略）。

| 规则ID | 类型 | 触发条件 | 预期行为 | 边界/约束 | 关联AC |
|--------|------|----------|----------|-----------|--------|
| R-1 | 行为 | `alert_dialog_model_ng.cpp` AlertDialog.show | 创建告警对话框，含 title/message/confirm/primaryButton/secondaryButton/buttons/buttonDirection | subtitle/buttons/buttonDirection @since 10 | AC-1.1 ~ AC-1.6 |
| R-2 | 边界 | `alert_dialog_model_ng.cpp` API 26 废弃 | AlertDialog.show() 在 API 26 标记 @deprecated | 推荐 CustomDialogController | AC-1.7 |
| R-3 | 行为 | `action_sheet_model_ng.cpp` ActionSheet.show | 创建选择列表对话框，含 title/message/sheets/confirm/autoCancel | @since 8 | AC-2.1 ~ AC-2.4 |
| R-4 | 边界 | `action_sheet_model_ng.cpp` API 26 废弃 | ActionSheet.show() 在 API 26 标记 @deprecated | 推荐 CustomDialogController | AC-2.5 |

## 验证映射

| 编号 | 对应规格项 | 验证方式 | 验证重点 |
|------|-----------|----------|----------|
| VM-1 | AC-1.1 ~ AC-1.7 | UT | AlertDialog 创建和属性 |
| VM-2 | AC-2.1 ~ AC-2.5 | UT | ActionSheet 创建和属性 |

## API 变更分析

### 新增 API

| API 名称 | 开放范围 | 入参概要 | 返回值 | 错误码范围 | 功能描述 | 关联 AC | @since |
|----------|----------|----------|--------|-----------|----------|---------|--------|
| AlertDialog.show(options) | Public | AlertDialogParamObject | void | 无 | 显示告警对话框 | AC-1.1 | 7 |
| ActionSheet.show(options) | Public | ActionSheetOptions | void | 无 | 显示选择列表对话框 | AC-2.1 | 8 |

### 变更/废弃 API

| API 名称 | 变更类型 | 影响场景 | 迁移指引 | 关联 AC |
|----------|----------|----------|----------|---------|
| AlertDialog.show() | 废弃（@since 26） | 告警对话框 | 使用 CustomDialogController 替代，自定义 builder 实现 | AC-1.7 |
| ActionSheet.show() | 废弃（@since 26） | 选择列表对话框 | 使用 CustomDialogController 替代，自定义 builder 实现 | AC-2.5 |

## 接口规格

### 接口定义

**AlertDialog.show**

| 属性 | 值 |
|------|-----|
| 函数签名 | `void AlertDialog.show(AlertDialogParamObject options)` |
| 返回值 | `void` |
| 开放范围 | Public |
| 错误码 | N/A |
| 关联 AC | AC-1.1 |

**参数约束**

| 参数 | 类型 | 必填 | 默认值 | 约束条件 |
|------|------|------|--------|---------|
| title | ResourceStr | 否 | — | 标题文本 |
| message | ResourceStr | 否 | — | 消息文本 |
| subtitle | ResourceStr | 否 | — | 副标题（@since 10） |
| confirm | AlertDialogConfirmOptions | 否 | — | 确认按钮配置 |
| primaryButton | AlertDialogButtonOptions | 否 | — | 主按钮（@since 10），与 secondaryButton 配合使用 |
| secondaryButton | AlertDialogButtonOptions | 否 | — | 次按钮（@since 10），与 primaryButton 配合使用 |
| buttons | AlertDialogButtonOptions[] | 否 | — | 按钮数组（@since 10），与 confirm/primaryButton/secondaryButton 互斥 |
| buttonDirection | DialogButtonDirection | 否 | AUTO | 按钮排列方向（@since 10） |

**行为场景**

| # | 触发条件 | 预期行为 | 关联 AC |
|---|----------|----------|---------|
| 1 | 传入 title/message/confirm | 显示含标题、消息和确认按钮的告警对话框 | AC-1.1 |
| 2 | 设置 subtitle（@since 10） | 对话框显示副标题 | AC-1.2 |
| 3 | 设置 primaryButton 和 secondaryButton（@since 10） | 对话框显示主/次两个按钮 | AC-1.3 |
| 4 | 设置 buttons 数组（@since 10） | 对话框显示多个按钮 | AC-1.4 |
| 5 | 设置 buttonDirection: HORIZONTAL（@since 10） | 按钮水平排列 | AC-1.5 |
| 6 | 设置 buttonDirection: VERTICAL（@since 10） | 按钮垂直排列 | AC-1.6 |
| 7 | API >= 26 调用 | 标记为 @deprecated，推荐使用 CustomDialogController | AC-1.7 |

**ActionSheet.show**

| 属性 | 值 |
|------|-----|
| 函数签名 | `void ActionSheet.show(ActionSheetOptions options)` |
| 返回值 | `void` |
| 开放范围 | Public |
| 错误码 | N/A |
| 关联 AC | AC-2.1 |

**参数约束**

| 参数 | 类型 | 必填 | 默认值 | 约束条件 |
|------|------|------|--------|---------|
| title | ResourceStr | 否 | — | 标题文本 |
| message | ResourceStr | 否 | — | 消息文本 |
| subtitle | ResourceStr | 否 | — | 副标题 |
| sheets | SheetInfo[] | 是 | — | 选项列表，每项含 title 和 action |
| confirm | ActionSheetConfirmOptions | 否 | — | 确认按钮配置 |
| autoCancel | boolean | 否 | true | 点击遮罩是否关闭 |

**行为场景**

| # | 触发条件 | 预期行为 | 关联 AC |
|---|----------|----------|---------|
| 1 | 传入 title/message/sheets/confirm | 显示含标题、消息、选项列表和确认按钮的选择列表对话框 | AC-2.1 |
| 2 | 设置 subtitle | 对话框显示副标题 | AC-2.2 |
| 3 | 用户点击 sheets 中的选项 | 执行对应 action 回调，对话框关闭 | AC-2.3 |
| 4 | 设置 autoCancel: false | 点击遮罩不关闭对话框 | AC-2.4 |
| 5 | API >= 26 调用 | 标记为 @deprecated，推荐使用 CustomDialogController | AC-2.5 |

## 兼容性声明

- **已有 API 行为变更:** 是
  - API 26+: AlertDialog.show() 和 ActionSheet.show() 标记为 @deprecated，推荐使用 CustomDialogController（AC-1.7, AC-2.5）
- **配置文件格式变更:** 否
- **数据存储格式变更:** 否
- **最低支持版本:** API 7
- **API 版本号策略:** AlertDialog.show @since 7，ActionSheet.show @since 8，AlertDialog subtitle/primaryButton/secondaryButton/buttons/buttonDirection @since 10，废弃标记 @since 26

## 架构约束

| 关键约束 | 约束说明 | 影响 AC |
|----------|----------|---------|
| 共享 Pattern | AlertDialog/ActionSheet 共享 DialogPattern 底层实现 | AC-1.1, AC-2.1 |
| 组件化不完全 | 基础 Pattern 已组件化（libarkui_dialog.z.so），但 AlertDialog/ActionSheet 仍有 JSView Bridge | AC-1.1, AC-2.1 |

> 本节列出本特性 AC 验证必须满足的约束。架构规则适用性及设计方案见 design.md。

## 非功能性需求

| 类型 | 指标/阈值 | 验证方式 | 证据 |
|------|-----------|----------|------|
| 性能 | AlertDialog/ActionSheet 显示帧率 ≥ 60fps | 手工 + Trace | Trace 打点 |
| 内存 | 对话框关闭后 overlay 节点销毁 | UT + Dump | 节点树 Dump |
| 安全 | 无安全相关接口 | N/A | — |
| 问题定位 | hilog 标签覆盖 AlertDialog/ActionSheet 创建 | 代码审查 | — |

> N/A 判定见 proposal.md 不涉及项确认。本节仅为适用项填写具体指标。

## 多设备适配声明

| 设备类型 | 行为差异 | 规格/约束 | 验证方式 | 证据 |
|----------|----------|-----------|----------|------|
| 手机 | 无差异 | — | — | — |
| 平板 | 无差异 | — | — | — |
| 折叠屏 | 无差异 | — | — | — |

## 全局特性影响

| 特性 | 适用？ | 结论 | 关联场景 |
|------|--------|------|----------|
| 无障碍 | 否 | AlertDialog/ActionSheet 无独立无障碍逻辑（共享 DialogPattern 无障碍实现，见 Feat-01） | — |
| 大字体 | 是 | 对话框内容跟随系统字体缩放 | AC-1.1 |
| 深色模式 | 是 | 颜色属性通过 ResourceColor 支持主题跟随 | AC-1.1 |
| 多窗口/分屏 | 否 | 命令式 API 无子窗口选项 | — |
| 多用户 | 否 | 无用户相关状态 | — |
| 版本升级 | 是 | API 26 废弃标记需兼容性处理 | AC-1.7, AC-2.5 |

## 行为场景（Gherkin）

```gherkin
Feature: AlertDialog/ActionSheet 命令式 API
  作为应用开发者
  我想要使用 AlertDialog/ActionSheet 显示命令式对话框
  以便快速显示标准化告警和选择列表

  Scenario: AlertDialog 创建
    Given 调用 AlertDialog.show({ title, message, confirm })
    Then 显示告警对话框含标题、消息和确认按钮

  Scenario: ActionSheet 创建
    Given 调用 ActionSheet.show({ title, sheets, confirm })
    Then 显示选择列表对话框

  Scenario: AlertDialog 废弃
    Given API >= 26 环境
    When 调用 AlertDialog.show()
    Then 标记为 @deprecated
    And 推荐使用 CustomDialogController

  Scenario: ActionSheet 废弃
    Given API >= 26 环境
    When 调用 ActionSheet.show()
    Then 标记为 @deprecated
    And 推荐使用 CustomDialogController
```

## Spec 自审清单

- [x] 无"待定""TBD""TODO"等占位符
- [x] 所有 AC 使用 WHEN/THEN 格式，可独立测试
- [x] 范围边界明确（做什么/不做什么清晰）
- [x] 无语义模糊表述（"快速""稳定""尽可能"等）
- [x] AC 与规则表交叉一致（每个 AC 至少关联一条规则，每条规则至少关联一个 AC）
- [x] 规则表每条通过 5 项质量检查（可复现/可观测/边界值/关联AC/无冲突）

## context-references

```yaml
context-queries:
  - repo: "openharmony/ace_engine"
    query: "AlertDialog/ActionSheet Model 和 promptAction NAPI 绑定"
  - repo: "openharmony/ace_engine"
    query: "DialogView CreateDialogNode 和 OverlayManager ShowDialog/CloseDialog 交互"
```

**关键文档:**
- SDK 类型定义 (AlertDialog): `interface/sdk-js/api/@internal/component/ets/alert_dialog.d.ts`
- SDK 类型定义 (ActionSheet): `interface/sdk-js/api/@internal/component/ets/action_sheet.d.ts`
- KB 路由: `docs/kb/components/overlay/dialog.md`
- 源码入口: `frameworks/core/components_ng/pattern/dialog/alert_dialog_model_ng.cpp`
