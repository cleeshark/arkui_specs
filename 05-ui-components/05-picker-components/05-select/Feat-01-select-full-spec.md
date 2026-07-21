# 特性规格

## 概述

| 字段 | 内容 |
|------|------|
| 特性名称 | Select 组件全量规格（下拉选择器、选中管理、菜单布局、样式定制、Modifier 扩展） |
| 特性编号 | Func-05-05-05-Feat-01 |
| FuncID | 05-05-05 |
| 所属 Epic | 无 |
| 优先级 | P0 |
| 目标版本 | API 8 ~ API 26+ |
| SIG 归属 | ArkUI SIG |
| 状态 | Baselined |
| 复杂度 | 标准 |
| lineage | new-on-legacy（已有实现的规格补录） |

## 本次变更范围（Delta）

> 本特性为已有实现补录，非增量变更。以下列出自 API 8 以来的关键变更里程碑。

| 类型 | 内容 | 说明 |
|------|------|------|
| ADDED | Select 组件基础 API（SelectOption/SelectInterface/SelectAttribute） | @since 8 |
| ADDED | selected, value, font, fontColor 属性 | @since 8 |
| ADDED | selectedOptionBgColor, selectedOptionFont, selectedOptionFontColor 属性 | @since 8 |
| ADDED | optionBgColor, optionFont, optionFontColor 属性 | @since 8 |
| ADDED | onSelect 事件 | @since 8 |
| ADDED | space 属性 | @since 10 |
| ADDED | arrowPosition 属性（ArrowPosition: END/START） | @since 10 |
| ADDED | menuAlign 属性（MenuAlignType: START/CENTER/END） | @since 10 |
| ADDED | optionWidth, optionHeight 属性 | @since 11 |
| ADDED | menuBackgroundColor, menuBackgroundBlurStyle 属性 | @since 11 |
| ADDED | controlSize 属性 | @since 12 |
| ADDED | menuItemContentModifier 属性 | @since 12 |
| ADDED | divider 属性 | @since 12 |
| ADDED | SelectOption.symbolIcon 字段 | @since 12 |
| ADDED | dividerStyle 属性 | @since 19 |
| ADDED | avoidance 属性（MenuAvoidance: COVER_TARGET/AVOID_AROUND_TARGET） | @since 19 |
| ADDED | menuOutline 属性 | @since 20 |
| ADDED | showInSubWindow 属性 | @since 20 |
| ADDED | showDefaultSelectedIcon 属性 | @since 20 |
| ADDED | textModifier 属性 | @since 20 |
| ADDED | arrowModifier 属性 | @since 20 |
| ADDED | keyboardAvoidMode 属性 | @since 23 |
| ADDED | menuSystemMaterial 属性 | @since 23 |
| ADDED | Static API（SelectModelStatic） | @since 23 |

## 输入文档

- **需求基线**: 已有能力补录（无独立 requirement.md / proposal.md）
- **设计文档**: `specs/05-ui-components/05-picker-components/05-select/design.md`
- **KB 路由**: `docs/kb/components/overlay/select.md`（待生成）
- **SDK 类型定义**:
  - Dynamic: `<OH_ROOT>/interface/sdk-js/api/@internal/component/ets/select.d.ts`
  - Static: `<OH_ROOT>/interface/sdk-js/api/arkui/component/select.static.d.ets`

> 需求基线、不涉及项、受影响子系统与仓库详见 proposal.md，本文档不重复摘录。design.md 与本文档并行产出，互不依赖。

## 用户故事

### US-1: 基础下拉选择

**角色**: 应用开发者
**期望**: 我想要使用 Select 组件创建下拉选择器，设置选项列表并管理选中状态
**价值**: 以便用户从预定义选项中选择值

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-1.1 | WHEN 创建 `Select([{ value: 'A' }, { value: 'B' }])` THEN 显示包含选项 A、B 的下拉选择器，默认未选中（selected_ = -1） | 正常 |
| AC-1.2 | WHEN 通过 Static API 创建 Select（@since 23）THEN 行为与 Dynamic API 一致，支持编译期类型检查 | 正常 |
| AC-1.3 | WHEN 设置 `selected(0)` THEN 初始化选中第一项（selected_ = 0），显示选项 A 的值 | 正常 |
| AC-1.4 | WHEN 用户点击下拉菜单中的选项 B THEN selected_ 更新为 1，onSelect 回调触发并携带 index=1 和 afford='B' | 正常 |
| AC-1.5 | WHEN selected 设置为越界值（如 999）THEN selected_ 回退到 -1（未选中），不崩溃 | 异常 |

### US-2: 下拉菜单生命周期

**角色**: 终端用户
**期望**: 我想要点击 Select 组件后弹出下拉菜单，选中后菜单关闭
**价值**: 以便获得直观的选择交互体验

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-2.1 | WHEN 用户点击 Select 组件 THEN SelectPattern::OnClick 调用 ShowSelectMenu，OverlayManager 将 SelectContentOverlay 节点挂载到 overlay 树 | 正常 |
| AC-2.2 | WHEN 下拉菜单打开后用户选中选项 THEN OverlayManager::CloseSelectMenu 卸载 overlay 节点，菜单关闭 | 正常 |
| AC-2.3 | WHEN 下拉菜单打开后用户点击菜单外部区域 THEN 菜单关闭（autoCancel 行为） | 正常 |
| AC-2.4 | WHEN 设置 `showInSubWindow(true)`（@since 20）THEN 下拉菜单在独立子窗口中显示，脱离主窗口约束 | 正常 |

### US-3: 菜单样式定制

**角色**: 应用开发者
**期望**: 我想要自定义下拉菜单的背景色、字体、颜色
**价值**: 以便菜单样式与应用设计语言一致

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-3.1 | WHEN 设置 `selectedOptionBgColor(Color.Red)` THEN 选中项的背景色为红色 | 正常 |
| AC-3.2 | WHEN 设置 `selectedOptionFont({ size: 16, weight: FontWeight.Bold })` THEN 选中项字体为 16vp 加粗 | 正常 |
| AC-3.3 | WHEN 设置 `selectedOptionFontColor(Color.White)` THEN 选中项字体颜色为白色 | 正常 |
| AC-3.4 | WHEN 设置 `optionBgColor(Color.Gray)` THEN 所有选项的背景色为灰色 | 正常 |
| AC-3.5 | WHEN 设置 `optionFont({ size: 14 })` THEN 所有选项字体为 14vp | 正常 |
| AC-3.6 | WHEN 设置 `optionFontColor(Color.Black)` THEN 所有选项字体颜色为黑色 | 正常 |
| AC-3.7 | WHEN 设置 `menuBackgroundColor(Color.White)`（@since 11）THEN 菜单整体背景色为白色 | 正常 |
| AC-3.8 | WHEN 设置 `menuBackgroundBlurStyle(BlurStyle.Regular)`（@since 11）THEN 菜单背景应用 Regular 模糊效果 | 正常 |
| AC-3.9 | WHEN 设置 `font({ size: 16 })` 和 `fontColor(Color.Black)` THEN Select 组件文本（非菜单）字体为 16vp、颜色黑色 | 正常 |

### US-4: 菜单布局定制

**角色**: 应用开发者
**期望**: 我想要自定义下拉菜单的间距、箭头位置、对齐方式、宽度和高度
**价值**: 以便菜单布局适应不同场景

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-4.1 | WHEN 设置 `space(10)`（@since 10）THEN 菜单项间距为 10vp | 正常 |
| AC-4.2 | WHEN 设置 `arrowPosition(ArrowPosition.START)`（@since 10）THEN 箭头显示在 Select 组件左侧（默认 END 右侧） | 正常 |
| AC-4.3 | WHEN 设置 `menuAlign(MenuAlignType.CENTER, 0)`（@since 10）THEN 菜单相对 Select 居中对齐，偏移量 0 | 正常 |
| AC-4.4 | WHEN 设置 `optionWidth(200)`（@since 11）THEN 菜单宽度为 200vp | 正常 |
| AC-4.5 | WHEN 设置 `optionHeight(300)`（@since 11）THEN 菜单高度为 300vp，超出时滚动 | 正常 |
| AC-4.6 | WHEN 设置 `optionWidth(OptionWidthMode.FIT_CONTENT)`（@since 11）THEN 菜单宽度自适应内容 | 正常 |
| AC-4.7 | WHEN 设置 `menuOutline({ width: 200, height: 300 })`（@since 20）THEN 菜单轮廓约束为宽 200vp 高 300vp | 正常 |
| AC-4.8 | WHEN 设置 `divider({ strokeWidth: 1, color: Color.Gray, startMargin: 4, endMargin: 4 })`（@since 12）THEN 菜单项间显示分割线 | 正常 |
| AC-4.9 | WHEN 设置 `dividerStyle({ strokeWidth: 1, color: Color.Gray })`（@since 19）THEN 菜单项间显示分割线（dividerStyle 与 divider 功能等价） | 正常 |
| AC-4.10 | WHEN 设置 `controlSize(ControlSize.SMALL)`（@since 12）THEN Select 组件尺寸为 SMALL 档 | 正常 |

### US-5: 菜单避让与键盘交互

**角色**: 应用开发者
**期望**: 我想要控制下拉菜单与目标组件和软键盘的避让行为
**价值**: 以便菜单不被遮挡或遮挡目标内容

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-5.1 | WHEN 设置 `avoidance(MenuAvoidance.COVER_TARGET)`（@since 19）THEN 菜单覆盖目标组件 | 正常 |
| AC-5.2 | WHEN 设置 `avoidance(MenuAvoidance.AVOID_AROUND_TARGET)`（@since 19）THEN 菜单环绕目标组件，避免遮挡 | 正常 |
| AC-5.3 | WHEN 设置 `keyboardAvoidMode(MenuKeyboardAvoidMode.DEFAULT)`（@since 23）THEN 使用默认键盘避让行为 | 正常 |
| AC-5.4 | WHEN 设置 `keyboardAvoidMode(MenuKeyboardAvoidMode.TRANSLATE)`（@since 23）THEN 菜单上移避让软键盘 | 正常 |
| AC-5.5 | WHEN 设置 `keyboardAvoidMode(MenuKeyboardAvoidMode.RESIZE)`（@since 23）THEN 菜单缩小避让软键盘 | 正常 |
| AC-5.6 | WHEN 设置 `menuSystemMaterial(MenuSystemMaterial.DEFAULT)`（@since 23）THEN 菜单使用系统 Material 效果 | 正常 |

### US-6: Modifier 自定义渲染

**角色**: 应用开发者
**期望**: 我想要通过 Modifier 自定义菜单项、文本和箭头的渲染
**价值**: 以便实现超出标准样式的定制化需求

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-6.1 | WHEN 设置 `menuItemContentModifier(modifier)`（@since 12）THEN 菜单项通过 ContentModifier 自定义 Builder 渲染 | 正常 |
| AC-6.2 | WHEN 设置 `textModifier(modifier)`（@since 20）THEN Select 文本区域通过 Modifier 自定义渲染 | 正常 |
| AC-6.3 | WHEN 设置 `arrowModifier(modifier)`（@since 20）THEN Select 箭头通过 Modifier 自定义渲染 | 正常 |
| AC-6.4 | WHEN 设置 `showDefaultSelectedIcon(true)`（@since 20）THEN 菜单中选中项显示默认选中图标 | 正常 |
| AC-6.5 | WHEN 设置 `showDefaultSelectedIcon(false)`（@since 20）THEN 菜单中选中项不显示选中图标 | 正常 |

### US-7: 选项图标

**角色**: 应用开发者
**期望**: 我想要为每个选项设置图标
**价值**: 以便选项更具视觉辨识度

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-7.1 | WHEN 设置 `SelectOption({ value: 'A', icon: $r('app.media.icon') })` THEN 选项 A 显示对应图标 | 正常 |
| AC-7.2 | WHEN 设置 `SelectOption({ value: 'A', symbolIcon: modifier })`（@since 12）THEN 选项 A 显示 SymbolGlyph 动态图标 | 正常 |
| AC-7.3 | WHEN SelectOption 未设置 icon 和 symbolIcon THEN 选项仅显示文本，无图标 | 正常 |

### US-8: API 版本兼容

**角色**: 应用开发者
**期望**: 我想要了解 Select 在不同 API 版本下的行为差异
**价值**: 以便在适配不同版本时预判变化

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-8.1 | WHEN API < 10 THEN space/arrowPosition/menuAlign 属性不可用，设置时无效果 | 边界 |
| AC-8.2 | WHEN API < 11 THEN optionWidth/optionHeight/menuBackgroundColor/menuBackgroundBlurStyle 属性不可用 | 边界 |
| AC-8.3 | WHEN API < 12 THEN controlSize/menuItemContentModifier/divider/symbolIcon 属性不可用 | 边界 |
| AC-8.4 | WHEN API < 19 THEN dividerStyle/avoidance 属性不可用 | 边界 |
| AC-8.5 | WHEN API < 20 THEN menuOutline/showInSubWindow/showDefaultSelectedIcon/textModifier/arrowModifier 属性不可用 | 边界 |
| AC-8.6 | WHEN API < 23 THEN keyboardAvoidMode/menuSystemMaterial/Static API 不可用 | 边界 |
| AC-8.7 | WHEN Select 未暴露为 ArkUI_NodeType 枚举 THEN NDK 开发者无法通过 C API 创建 Select 节点（已知差距，无 C API 支持） | 边界 |

### US-9: 状态恢复

**角色**: 应用开发者
**期望**: 我想要 Select 在状态恢复时保持选中项
**价值**: 以便应用从后台恢复时用户选择不丢失

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-9.1 | WHEN SelectPattern::ProvideRestoreInfo 被调用 THEN 返回 selected_ 的序列化字符串 | 正常 |
| AC-9.2 | WHEN SelectPattern::OnRestoreInfo 被调用 THEN 从序列化字符串反序列化 selected_，恢复选中项 | 正常 |
| AC-9.3 | WHEN selected_ = -1（未选中）时恢复 THEN 恢复后仍为未选中状态 | 正常 |

### US-10: 无障碍支持

**角色**: 辅助功能用户
**期望**: 我想要通过无障碍服务操作 Select 组件
**价值**: 以便在无法直接触摸屏幕时完成选择操作

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-10.1 | WHEN 无障碍服务查询 Select THEN 报告角色为 DropDownMenu | 正常 |
| AC-10.2 | WHEN 无障碍服务执行 ActionSelect THEN 选中指定选项，selected_ 更新 | 正常 |
| AC-10.3 | WHEN 无障碍服务查询选中状态 THEN 报告当前 selected_ 对应的选项值 | 正常 |

## 验收追溯

| AC编号 | 关联规则 | 关联 Task | 验证方式 | 证据 |
|-------|----------|-----------|----------|------|
| AC-1.1 ~ AC-1.5 | R-1, R-2, R-3 | TASK-SELECT-01 | UT | `test/unittest/core/pattern/select/` |
| AC-2.1 ~ AC-2.4 | R-4, R-5, R-6 | TASK-SELECT-01 | UT + 手工 | select 单测 ShowSelectMenu 用例 |
| AC-3.1 ~ AC-3.9 | R-7, R-8 | TASK-SELECT-01 | UT | SelectPaintProperty 测试 |
| AC-4.1 ~ AC-4.10 | R-9, R-10, R-11 | TASK-SELECT-01 | UT | 菜单布局测试 |
| AC-5.1 ~ AC-5.6 | R-12, R-13, R-14 | TASK-SELECT-01 | UT + 手工 | 避让和键盘交互测试 |
| AC-6.1 ~ AC-6.5 | R-15, R-16 | TASK-SELECT-01 | UT | Modifier 集成测试 |
| AC-7.1 ~ AC-7.3 | R-17 | TASK-SELECT-01 | UT | SelectOption icon 测试 |
| AC-8.1 ~ AC-8.7 | R-18, R-19 | TASK-SELECT-01 | UT | API 版本兼容测试 |
| AC-9.1 ~ AC-9.3 | R-20, R-21 | TASK-SELECT-01 | UT | 状态恢复测试 |
| AC-10.1 ~ AC-10.3 | R-22 | TASK-SELECT-01 | UT | 无障碍属性测试 |

## 规则定义

> **统一规则表，取消 FR/BR/EX/RC 四分类。** 类型标签：**行为**（正常路径下的系统行为）、**边界**（输入/状态的临界点）、**异常**（非法输入或异常状态的处理）、**恢复**（系统异常后的恢复策略）。

| 规则ID | 类型 | 触发条件 | 预期行为 | 边界/约束 | 关联AC |
|--------|------|----------|----------|-----------|--------|
| R-1 | 行为 | `select_model_ng.cpp` CreateFrameNode | 创建 SELECT_ETS_TAG 节点，初始化 SelectPattern，selected_ = -1 | — | AC-1.1 |
| R-2 | 行为 | `select_model_static.cpp` Static API 入口 | Static API（@since 23）与 Dynamic API 行为一致，通过 select_static_modifier.cpp 委托 | — | AC-1.2 |
| R-3 | 行为 | `select_pattern.cpp` selected_ 管理 | selected(value) 初始化选中项，selected_ 更新为指定索引 | selected_ 默认 -1（未选中） | AC-1.3 |
| R-4 | 行为 | `select_pattern.cpp` OnClick → ShowSelectMenu | 用户点击 Select 时通过 OverlayManager::ShowSelectMenu 挂载 SelectContentOverlay 节点 | — | AC-2.1 |
| R-5 | 行为 | `overlay_manager.cpp` CloseSelectMenu | 选中选项或点击外部时 OverlayManager::CloseSelectMenu 卸载 overlay 节点 | — | AC-2.2, AC-2.3 |
| R-6 | 行为 | `select_pattern.cpp` showInSubWindow | showInSubWindow(true) 时菜单在独立子窗口显示 | @since 20 | AC-2.4 |
| R-7 | 行为 | `select_paint_property.h` 样式属性 | selectedOptionBgColor/Font/FontColor 控制选中项样式；optionBgColor/Font/FontColor 控制所有选项样式 | — | AC-3.1 ~ AC-3.6 |
| R-8 | 行为 | `select_paint_property.h` 菜单背景 | menuBackgroundColor 控制菜单背景色；menuBackgroundBlurStyle 控制模糊效果 | @since 11 | AC-3.7, AC-3.8 |
| R-9 | 行为 | `select_layout_algorithm.cpp` 布局计算 | space 控制菜单项间距；arrowPosition 控制箭头位置（END/START）；menuAlign 控制菜单对齐 | @since 10 | AC-4.1 ~ AC-4.3 |
| R-10 | 行为 | `select_content_overlay_pattern.cpp` 菜单尺寸 | optionWidth/optionHeight 控制菜单尺寸；OptionWidthMode.FIT_CONTENT 自适应 | @since 11 | AC-4.4 ~ AC-4.6 |
| R-11 | 行为 | `select_paint_property.h` 菜单轮廓 | menuOutline 约束菜单宽高；divider/dividerStyle 控制菜单项分割线；controlSize 控制组件尺寸档 | @since 12/19/20 | AC-4.7 ~ AC-4.10 |
| R-12 | 行为 | `overlay_manager.cpp` avoidance | COVER_TARGET 菜单覆盖目标；AVOID_AROUND_TARGET 菜单环绕避让目标 | @since 19 | AC-5.1, AC-5.2 |
| R-13 | 行为 | `select_pattern.cpp` keyboardAvoidMode | DEFAULT/TRANSLATE/RESIZE 控制菜单与软键盘的避让 | @since 23 | AC-5.3 ~ AC-5.5 |
| R-14 | 行为 | `select_pattern.cpp` menuSystemMaterial | 菜单使用系统 Material 效果 | @since 23 | AC-5.6 |
| R-15 | 行为 | `select_pattern.cpp` Modifier | menuItemContentModifier 自定义菜单项渲染；textModifier 自定义文本；arrowModifier 自定义箭头 | @since 12/20 | AC-6.1 ~ AC-6.3 |
| R-16 | 行为 | `select_pattern.cpp` showDefaultSelectedIcon | true 显示选中图标，false 不显示 | @since 20，默认 true | AC-6.4, AC-6.5 |
| R-17 | 行为 | SelectOption | icon 设置选项图标；symbolIcon 设置 SymbolGlyph 动态图标 | symbolIcon @since 12 | AC-7.1 ~ AC-7.3 |
| R-18 | 边界 | API 版本兼容 | @since 10/11/12/19/20/23 各版本新增属性在旧版本不可用 | — | AC-8.1 ~ AC-8.6 |
| R-19 | 边界 | native_node.h | Select 未暴露为 ArkUI_NodeType 枚举，无 C API 支持 | — | AC-8.7 |
| R-20 | 行为 | `select_pattern.cpp` ProvideRestoreInfo | 序列化 selected_ 为字符串用于状态恢复 | — | AC-9.1 |
| R-21 | 恢复 | `select_pattern.cpp` OnRestoreInfo | 反序列化恢复 selected_，selected_ = -1 时恢复为未选中 | — | AC-9.2, AC-9.3 |
| R-22 | 行为 | `select_accessibility_property.cpp` | 报告角色 DropDownMenu，支持 ActionSelect | — | AC-10.1 ~ AC-10.3 |
| R-23 | 异常 | `select_pattern.cpp` selected 越界 | selected 设置越界值时回退到 -1，不崩溃 | — | AC-1.5 |

## 验证映射

| 编号 | 对应规格项 | 验证方式 | 验证重点 |
|------|-----------|----------|----------|
| VM-1 | AC-1.1 ~ AC-1.5 | UT | Select 创建、选中管理、越界处理 |
| VM-2 | AC-2.1 ~ AC-2.4 | UT + 手工 | 下拉菜单生命周期、子窗口模式 |
| VM-3 | AC-3.1 ~ AC-3.9 | UT | 菜单样式属性 |
| VM-4 | AC-4.1 ~ AC-4.10 | UT | 菜单布局属性 |
| VM-5 | AC-5.1 ~ AC-5.6 | UT + 手工 | 避让策略和键盘交互 |
| VM-6 | AC-6.1 ~ AC-6.5 | UT | Modifier 自定义渲染 |
| VM-7 | AC-7.1 ~ AC-7.3 | UT | 选项图标 |
| VM-8 | AC-8.1 ~ AC-8.7 | UT | API 版本兼容性 |
| VM-9 | AC-9.1 ~ AC-9.3 | UT | 状态恢复 |
| VM-10 | AC-10.1 ~ AC-10.3 | UT | 无障碍属性和操作 |

## API 变更分析

### 新增 API

| API 名称 | 开放范围 | 入参概要 | 返回值 | 错误码范围 | 功能描述 | 关联 AC | @since |
|----------|----------|----------|--------|-----------|----------|---------|--------|
| Select(options: SelectOption[]) | Public | SelectOption[] | SelectAttribute | 无 | 创建下拉选择器 | AC-1.1 | 8 |
| SelectAttribute.selected(value: number) | Public | number | SelectAttribute | 无 | 设置选中项索引 | AC-1.3 | 8 |
| SelectAttribute.value(value: string) | Public | string | SelectAttribute | 无 | 设置显示文本 | AC-1.1 | 8 |
| SelectAttribute.font(value: Font) | Public | Font | SelectAttribute | 无 | 设置字体 | AC-3.9 | 8 |
| SelectAttribute.fontColor(value: ResourceColor) | Public | ResourceColor | SelectAttribute | 无 | 设置字体颜色 | AC-3.9 | 8 |
| SelectAttribute.selectedOptionBgColor(value) | Public | ResourceColor | SelectAttribute | 无 | 选中项背景色 | AC-3.1 | 8 |
| SelectAttribute.selectedOptionFont(value) | Public | Font | SelectAttribute | 无 | 选中项字体 | AC-3.2 | 8 |
| SelectAttribute.selectedOptionFontColor(value) | Public | ResourceColor | SelectAttribute | 无 | 选中项字体颜色 | AC-3.3 | 8 |
| SelectAttribute.optionBgColor(value) | Public | ResourceColor | SelectAttribute | 无 | 选项背景色 | AC-3.4 | 8 |
| SelectAttribute.optionFont(value) | Public | Font | SelectAttribute | 无 | 选项字体 | AC-3.5 | 8 |
| SelectAttribute.optionFontColor(value) | Public | ResourceColor | SelectAttribute | 无 | 选项字体颜色 | AC-3.6 | 8 |
| SelectAttribute.onSelect(callback) | Public | (index, afford) => void | SelectAttribute | 无 | 选中回调 | AC-1.4 | 8 |
| SelectAttribute.space(value: number) | Public | number | SelectAttribute | 无 | 菜单项间距 | AC-4.1 | 10 |
| SelectAttribute.arrowPosition(value) | Public | ArrowPosition | SelectAttribute | 无 | 箭头位置 | AC-4.2 | 10 |
| SelectAttribute.menuAlign(alignType, alignOffset) | Public | MenuAlignType, number | SelectAttribute | 无 | 菜单对齐 | AC-4.3 | 10 |
| SelectAttribute.optionWidth(value) | Public | OptionWidthMode \| Dimension | SelectAttribute | 无 | 菜单宽度 | AC-4.4 | 11 |
| SelectAttribute.optionHeight(value) | Public | number \| string | SelectAttribute | 无 | 菜单高度 | AC-4.5 | 11 |
| SelectAttribute.menuBackgroundColor(value) | Public | ResourceColor | SelectAttribute | 无 | 菜单背景色 | AC-3.7 | 11 |
| SelectAttribute.menuBackgroundBlurStyle(value) | Public | BlurStyle | SelectAttribute | 无 | 菜单背景模糊 | AC-3.8 | 11 |
| SelectAttribute.controlSize(value) | Public | ControlSize | SelectAttribute | 无 | 组件尺寸档 | AC-4.10 | 12 |
| SelectAttribute.menuItemContentModifier(modifier) | Public | ContentModifier | SelectAttribute | 无 | 菜单项自定义渲染 | AC-6.1 | 12 |
| SelectAttribute.divider(value) | Public | DividerStyle \| null | SelectAttribute | 无 | 菜单分割线 | AC-4.8 | 12 |
| SelectAttribute.dividerStyle(value) | Public | DividerStyle | SelectAttribute | 无 | 菜单分割线样式 | AC-4.9 | 19 |
| SelectAttribute.avoidance(value) | Public | MenuAvoidance | SelectAttribute | 无 | 菜单避让策略 | AC-5.1, AC-5.2 | 19 |
| SelectAttribute.menuOutline(value) | Public | SelectMenuOutline | SelectAttribute | 无 | 菜单轮廓约束 | AC-4.7 | 20 |
| SelectAttribute.showInSubWindow(value) | Public | boolean | SelectAttribute | 无 | 子窗口显示 | AC-2.4 | 20 |
| SelectAttribute.showDefaultSelectedIcon(value) | Public | boolean | SelectAttribute | 无 | 显示选中图标 | AC-6.4, AC-6.5 | 20 |
| SelectAttribute.textModifier(modifier) | Public | Modifier | SelectAttribute | 无 | 文本自定义渲染 | AC-6.2 | 20 |
| SelectAttribute.arrowModifier(modifier) | Public | Modifier | SelectAttribute | 无 | 箭头自定义渲染 | AC-6.3 | 20 |
| SelectAttribute.keyboardAvoidMode(value) | Public | MenuKeyboardAvoidMode | SelectAttribute | 无 | 键盘避让模式 | AC-5.3 ~ AC-5.5 | 23 |
| SelectAttribute.menuSystemMaterial(value) | Public | MenuSystemMaterial | SelectAttribute | 无 | 系统Material效果 | AC-5.6 | 23 |
| SelectModelStatic (Static API) | Public | — | — | — | Static API 入口 | AC-1.2 | 23 |

### 变更/废弃 API

| API 名称 | 变更类型 | 影响场景 | 迁移指引 | 关联 AC |
|----------|----------|----------|----------|---------|
| 无 | — | — | — | — |

> 截至当前版本，Select 未发现任何 @deprecated 或 @useinstead 标注的 API。

## 接口规格

### 接口定义

**SelectAttribute.selected**

| 属性 | 值 |
|------|-----|
| 函数签名 | `SelectAttribute::selected(int32_t value)` |
| 返回值 | `SelectAttribute` — 链式调用 |
| 开放范围 | Public |
| 错误码 | N/A |
| 关联 AC | AC-1.3, AC-1.5 |

**参数约束**

| 参数 | 类型 | 必填 | 默认值 | 约束条件 |
|------|------|------|--------|---------|
| value | int32_t | 是 | -1 | 0 ~ options.length-1；越界回退 -1 |

**行为场景**

| # | 触发条件 | 预期行为 | 关联 AC |
|---|----------|----------|---------|
| 1 | value 在合法范围内 | selected_ 更新为 value，显示对应选项文本 | AC-1.3 |
| 2 | value 越界（如 999） | selected_ 回退到 -1，不崩溃 | AC-1.5 |

**SelectAttribute.onSelect**

| 属性 | 值 |
|------|-----|
| 函数签名 | `SelectAttribute::onSelect(Callback<void(int32_t, const std::string&)> callback)` |
| 返回值 | `SelectAttribute` — 链式调用 |
| 开放范围 | Public |
| 错误码 | N/A |
| 关联 AC | AC-1.4 |

**参数约束**

| 参数 | 类型 | 必填 | 默认值 | 约束条件 |
|------|------|------|--------|---------|
| callback | Callback | 是 | 无 | 回调参数: index (选中索引), afford (选项值) |

**行为场景**

| # | 触发条件 | 预期行为 | 关联 AC |
|---|----------|----------|---------|
| 1 | 用户点击选项 | selected_ 更新为 index，回调携带 index 和 afford | AC-1.4 |

## 兼容性声明

- **已有 API 行为变更:** 否（各版本新增属性均为增量，无已有行为变更）
- **配置文件格式变更:** 否
- **数据存储格式变更:** 否
- **最低支持版本:** API 8
- **API 版本号策略:** 基础 API @since 8，space/arrowPosition/menuAlign @since 10，optionWidth/optionHeight/menuBackgroundColor/menuBackgroundBlurStyle @since 11，controlSize/menuItemContentModifier/divider/symbolIcon @since 12，dividerStyle/avoidance @since 19，menuOutline/showInSubWindow/showDefaultSelectedIcon/textModifier/arrowModifier @since 20，keyboardAvoidMode/menuSystemMaterial/Static API @since 23

## 架构约束

| 关键约束 | 约束说明 | 影响 AC |
|----------|----------|---------|
| Overlay 依赖 | Select 通过 OverlayManager 挂载下拉菜单，依赖 overlay 基础设施 | AC-2.1 ~ AC-2.4 |
| SelectionContainer | 下拉菜单选项列表通过 SelectionContainer 渲染 | AC-1.4, AC-2.1 |
| 无 C API | Select 未暴露为 ArkUI_NodeType 枚举 | AC-8.7 |
| 组件化 | 已组件化为 libarkui_select.z.so，通过 DynamicModule 注册 | AC-1.1 |

> 本节列出本特性 AC 验证必须满足的约束。架构规则适用性及设计方案见 design.md。

## 非功能性需求

| 类型 | 指标/阈值 | 验证方式 | 证据 |
|------|-----------|----------|------|
| 性能 | 下拉菜单打开延迟 ≤ 100ms | 手工 + Trace | Trace 打点 |
| 内存 | 下拉菜单关闭后 overlay 节点销毁 | UT + Dump | 节点树 Dump |
| 安全 | 无安全相关接口 | N/A | — |
| 可靠性 | selected 越界不崩溃 | UT | select 单测 |
| 问题定位 | hilog 标签覆盖 ShowSelectMenu/CloseSelectMenu 路径 | 代码审查 | — |

> N/A 判定见 proposal.md 不涉及项确认。本节仅为适用项填写具体指标。

## 多设备适配声明

| 设备类型 | 行为差异 | 规格/约束 | 验证方式 | 证据 |
|----------|----------|-----------|----------|------|
| 手机 | 无差异 | — | — | — |
| 平板 | 无差异 | — | — | — |
| 折叠屏 | showInSubWindow 在折叠态切换时需重新定位菜单 | 子窗口模式需处理窗口尺寸变化 | 手工 | — |

## 全局特性影响

| 特性 | 适用？ | 结论 | 关联场景 |
|------|--------|------|----------|
| 无障碍 | 是 | Select 实现 AccessibilityProperty，报告角色 DropDownMenu，支持 ActionSelect | AC-10.1 ~ AC-10.3 |
| 大字体 | 是 | Select 文本 font 跟随系统字体缩放 | AC-3.9 |
| 深色模式 | 是 | 颜色属性通过 ResourceColor 支持主题跟随 | AC-3.1 ~ AC-3.8 |
| 多窗口/分屏 | 是 | showInSubWindow 支持子窗口模式 | AC-2.4 |
| 多用户 | 否 | 无用户相关状态 | — |
| 版本升级 | 是 | API 10/11/12/19/20/23 各版本新增属性需兼容性处理 | AC-8.1 ~ AC-8.6 |
| 生态兼容 | 是 | 无 C API 支持需在文档中明确 | AC-8.7 |

## 行为场景（Gherkin）

```gherkin
Feature: Select 组件
  作为应用开发者
  我想要使用 Select 组件创建下拉选择器
  以便用户从预定义选项中选择值

  Scenario: 基础创建和选中
    Given Select 组件以 options=[{value:'A'}, {value:'B'}] 创建
    When 用户点击选项 B
    Then selected_ 更新为 1
    And onSelect 回调携带 index=1, afford='B'
    And 下拉菜单关闭

  Scenario: 初始选中项
    Given Select 组件以 selected(0) 创建
    Then selected_ = 0
    And 显示选项 A 的值

  Scenario: selected 越界
    Given Select 组件以 selected(999) 创建
    Then selected_ 回退为 -1
    And 不崩溃

  Scenario: 下拉菜单打开和关闭
    Given Select 组件已创建
    When 用户点击 Select 组件
    Then OverlayManager::ShowSelectMenu 挂载 SelectContentOverlay 节点
    When 用户点击菜单外部
    Then OverlayManager::CloseSelectMenu 卸载 overlay 节点

  Scenario: 子窗口模式
    Given Select 组件以 showInSubWindow(true) 创建
    When 用户点击 Select 打开菜单
    Then 菜单在独立子窗口中显示

  Scenario: 菜单避让策略
    Given Select 组件以 avoidance(AVOID_AROUND_TARGET) 创建
    When 下拉菜单打开
    Then 菜单环绕目标组件，避免遮挡

  Scenario Outline: API 版本兼容
    Given Select 组件在 API <api_version> 环境运行
    When 设置 <property>
    Then 属性<available>

    Examples:
      | api_version | property               | available |
      | 9           | space                  | 不可用     |
      | 10          | space                  | 可用       |
      | 10          | optionWidth            | 不可用     |
      | 11          | optionWidth            | 可用       |
      | 19          | avoidance              | 不可用     |
      | 20          | avoidance              | 可用       |

  Scenario: 状态恢复
    Given Select 组件 selected_ = 2
    When ProvideRestoreInfo 被调用
    Then 返回 selected_ 的序列化字符串
    When OnRestoreInfo 被调用
    Then selected_ 恢复为 2

  Scenario: 无 C API
    Given NDK 开发者尝试通过 C API 创建 Select
    When 查询 ArkUI_NodeType 枚举
    Then Select 未在枚举中暴露
    And 无法通过 C API 创建 Select 节点
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
    query: "Select 组件 ShowSelectMenu 和 OverlayManager 交互机制"
  - repo: "openharmony/ace_engine"
    query: "SelectPattern selected_ 状态管理和 ProvideRestoreInfo/OnRestoreInfo 实现"
  - repo: "openharmony/ace_engine"
    query: "SelectContentOverlayPattern 和 SelectionContainer 下拉菜单渲染"
  - repo: "openharmony/ace_engine"
    query: "SelectModelStatic Static API 入口和 select_static_modifier 实现"
```

**关键文档:**
- SDK 类型定义: `interface/sdk-js/api/@internal/component/ets/select.d.ts`
- KB 路由: `docs/kb/components/overlay/select.md`（待生成）
- 源码入口: `frameworks/core/components_ng/pattern/select/select_pattern.cpp`
