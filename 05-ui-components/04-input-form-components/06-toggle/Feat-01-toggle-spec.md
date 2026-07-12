# 特性规格

## 概述

| 字段 | 内容 |
|------|------|
| 特性名称 | Toggle 组件全量规格 (Switch/Checkbox/Button 三形态) |
| 特性编号 | Func-05-04-06-Feat-01 |
| FuncID | 05-04-06 |
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
| ADDED | Toggle 组件三形态 (Switch/Checkbox/Button) | @since 8，ToggleType 枚举 |
| ADDED | selectedColor, switchPointColor 属性 | @since 8 |
| ADDED | onChange 事件 | @since 8 |
| ADDED | SwitchStyle 复合样式 (pointRadius/unselectedColor/pointColor/trackBorderRadius) | @since 12 |
| ADDED | ContentModifier 自定义渲染 | @since 12 |
| MODIFIED | Switch 布局: API 12+ 取消 1.8:1 强制宽高比 | API 12 行为变更 |
| MODIFIED | Button 类型: API 18+ 从 CAPSULE 切换为 ROUNDED_RECTANGLE | API 18 行为变更 |
| ADDED | C API: NODE_TOGGLE_SELECTED_COLOR/SWITCH_POINT_COLOR/VALUE/UNSELECTED_COLOR | NDK 属性 |
| ADDED | C API: NODE_TOGGLE_ON_CHANGE 事件 | NDK 事件 |
| ADDED | Static API: ExtendableToggle, setToggleOptions | @since 26 |

## 输入文档

- **需求基线**: 已有能力补录（无独立 requirement.md / proposal.md）
- **设计文档**: `specs/05-ui-components/04-form-components/06-toggle/design.md`
- **KB 路由**: `docs/kb/components/selector/toggle.md`
- **SDK 类型定义**:
  - Dynamic: `<OH_ROOT>/interface/sdk-js/api/@internal/component/ets/toggle.d.ts`
  - Static: `<OH_ROOT>/interface/sdk-js/api/arkui/component/toggle.static.d.ets`
  - Modifier: `<OH_ROOT>/interface/sdk-js/api/arkui/ToggleModifier.d.ts`

> 需求基线、不涉及项、受影响子系统与仓库详见 proposal.md，本文档不重复摘录。design.md 与本文档并行产出，互不依赖。

## 用户故事

### US-1: 基础开关切换

**角色**: 应用开发者
**期望**: 我想要使用 Toggle 组件在三种形态（Switch / Checkbox / Button）间统一地实现开关状态切换
**价值**: 以便用不同的视觉风格满足不同场景的开关交互需求

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-1.1 | WHEN 创建 `Toggle({ type: ToggleType.Switch, isOn: true })` THEN 显示滑块开关样式，初始状态为开 | 正常 |
| AC-1.2 | WHEN 创建 `Toggle({ type: ToggleType.Checkbox, isOn: false })` THEN 显示复选框样式，初始状态为关 | 正常 |
| AC-1.3 | WHEN 创建 `Toggle({ type: ToggleType.Button, isOn: true })` THEN 显示按钮样式，初始状态为开，支持子组件作为按钮内容 | 正常 |
| AC-1.4 | WHEN 点击 Toggle（任意类型）THEN isOn 状态翻转，onChange 回调触发并携带新状态值 | 正常 |
| AC-1.5 | WHEN isOn 使用 `$$` 双向绑定 THEN 组件状态与绑定变量保持同步 | 正常 |
| AC-1.6 | WHEN Toggle 处于 disabled 状态 THEN 点击不改变状态，不触发 onChange，Switch 类型应用 disabledAlpha 透明度（`switch_pattern.cpp:236-237`） | 正常 |

### US-2: Switch 样式定制

**角色**: 应用开发者
**期望**: 我想要自定义 Switch 类型的颜色、滑块大小和轨道圆角
**价值**: 以便匹配应用的设计语言

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-2.1 | WHEN 设置 `selectedColor(Color.Red)` THEN Switch 开启时轨道背景色为红色 | 正常 |
| AC-2.2 | WHEN 设置 `switchPointColor(Color.Blue)` THEN Switch 滑块颜色为蓝色 | 正常 |
| AC-2.3 | WHEN 设置 `switchStyle({ pointRadius: 10, unselectedColor: '#337F7F7F', pointColor: Color.White, trackBorderRadius: 8 })` THEN 滑块半径 10vp、关闭态轨道颜色 0x337F7F7F、滑块颜色白色、轨道圆角 8vp | 正常 |
| AC-2.4 | WHEN `switchPointColor` 和 `switchStyle.pointColor` 同时设置 THEN 两者写入同一个 `SwitchPaintProperty::SwitchPointColor`，后设置的生效（功能等价，`switch_paint_property.h`） | 正常 |
| AC-2.5 | WHEN 未设置任何颜色属性 THEN 使用 SwitchTheme 的默认值（pointColor = `ohos_id_color_foreground_contrary`，unselectedColor = `0x337F7F7F`，selectedColor = `ohos_id_color_emphasize`） | 异常 |

### US-3: Button 样式与交互

**角色**: 应用开发者
**期望**: 我想要定制 Button 类型的选中色和背景色
**价值**: 以便 Toggle Button 的外观与应用风格一致

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-3.1 | WHEN 设置 `selectedColor` 在 Button 类型上 THEN 开启时背景色为指定颜色，关闭时恢复为 `backgroundColor`（`toggle_button_pattern.cpp:89-97`） | 正常 |
| AC-3.2 | WHEN Button 类型运行在 API 18+ THEN 按钮形状为 ROUNDED_RECTANGLE；API 18 以下为 CAPSULE（`toggle_button_pattern.cpp:678-682`） | 正常 |
| AC-3.3 | WHEN Button 类型切换状态 THEN 背景色立即切换（无渐变动画），通过 `RenderContext::UpdateBackgroundColor()` 实现（`toggle_button_pattern.cpp:630`） | 正常 |
| AC-3.4 | WHEN Button 类型接收触摸/悬停事件 THEN 应用 overlay 透明度混合效果，触摸 100ms / 悬停 250ms（`toggle_button_pattern.cpp:31-32`） | 正常 |

### US-4: Switch 拖拽与动画

**角色**: 终端用户
**期望**: 我想要通过拖拽 Switch 滑块来切换状态
**价值**: 以便获得自然的交互体验

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-4.1 | WHEN 水平拖拽 Switch 滑块超过中点 THEN 状态翻转（中点 = `(mainSize + height_) / 2`，`switch_pattern.cpp:843`） | 边界 |
| AC-4.2 | WHEN 拖拽未超过中点 THEN 状态保持不变，滑块弹回原位 | 边界 |
| AC-4.3 | WHEN RTL 布局 THEN 拖拽方向判定反转（`switch_pattern.cpp:844-849`） | 正常 |
| AC-4.4 | WHEN Switch 状态切换 THEN 使用弹簧动画过渡（velocity=0, mass=1, stiffness=305, damping=24，`switch_pattern.cpp:55-58`） | 正常 |
| AC-4.5 | WHEN 颜色/滑块位置变化 THEN 使用 200ms FAST_OUT_SLOW_IN 曲线过渡（`switch_modifier.h:65, 339`） | 正常 |

### US-5: Switch Material 长按效果

**角色**: 终端用户
**期望**: 我想要在长按 Switch 时看到 Material 效果反馈
**价值**: 以便感知交互正在进行

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-5.1 | WHEN 长按 Switch 超过 400ms（`switch_pattern.cpp:68`）且 `HasSystemMaterial()` 返回 true THEN 触发 Material 效果 | 边界 |
| AC-5.2 | WHEN Material 等级为高级（EXQUISITE 或 GENTLE，`switch_pattern.cpp:900-904`）THEN 创建 dragFrameNode_/dragPointNode_/blurCoverNode_ 三层覆盖节点，应用 BrightnessBlender（linearRate=1.048, degree=0.37647, saturation=1.5，`switch_pattern.cpp:1409-1411`） | 正常 |
| AC-5.3 | WHEN Material 等级为低级 THEN 滑块缩放至 0.78 再放大至 1.56（`switch_pattern.cpp:61-62, 675-676`） | 正常 |
| AC-5.4 | WHEN `HasSystemMaterial()` 返回 false THEN 不触发 Material 效果，仅使用普通弹簧动画 | 正常 |

### US-6: API 版本兼容布局

**角色**: 应用开发者
**期望**: 我想要了解 Toggle 在不同 API 版本下的布局行为差异
**价值**: 以便在适配不同版本时预判布局变化

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-6.1 | WHEN API < 12 THEN Switch 布局强制 width = height × 1.8（ratio=1.8f，`switch_layout_algorithm.cpp:120-135`，`checkable_theme.h:285`） | 边界 |
| AC-6.2 | WHEN API >= 12 THEN Switch 布局直接使用设置的 frameWidth/frameHeight，不再强制宽高比（`switch_layout_algorithm.cpp:116-118`） | 边界 |
| AC-6.3 | WHEN API >= 18 且使用 ContentModifier THEN 布局调用 `geometryNode->ResetContent()` 替代 `geometryNode->Reset()`（`switch_layout_algorithm.cpp:35-37`） | 边界 |

### US-7: ContentModifier 自定义渲染

**角色**: 应用开发者
**期望**: 我想要使用 ContentModifier 完全自定义 Toggle 的渲染内容
**价值**: 以便实现超出标准样式的定制化需求

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-7.1 | WHEN 设置 `contentModifier(modifier)` THEN 组件通过 `ToggleConfiguration { isOn, enabled, triggerChange }` 回调自定义 Builder | 正常 |
| AC-7.2 | WHEN ContentModifier 激活时 THEN Switch 类型跳过默认点击/触摸/拖拽事件处理（`switch_pattern.cpp:443, 485, 505`），Button 类型跳过颜色切换和悬停效果（`toggle_button_pattern.cpp:89, 607-609`），背景设为 `Color::TRANSPARENT`（`toggle_button_pattern.cpp:829`） | 正常 |
| AC-7.3 | WHEN 调用 `triggerChange(true/false)` THEN 程序化切换 Toggle 状态 | 正常 |
| AC-7.4 | WHEN ContentModifier 激活时 THEN Switch 的 disabled 状态不再应用 disabledAlpha（`switch_pattern.cpp:221-223`） | 正常 |

### US-8: C API / NDK 支持

**角色**: NDK 开发者
**期望**: 我想要通过 C API 控制 Toggle 状态和样式
**价值**: 以便在 Native 层集成 Toggle 组件

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-8.1 | WHEN 通过 `NODE_TOGGLE_VALUE` 设置 `.value[0].i32 = 1` THEN Toggle 状态为开 | 正常 |
| AC-8.2 | WHEN 通过 `NODE_TOGGLE_SELECTED_COLOR` 设置 `.value[0].u32 = 0xFFFF0000` THEN 开启态背景色为红色 | 正常 |
| AC-8.3 | WHEN 通过 `NODE_TOGGLE_SWITCH_POINT_COLOR` 设置颜色 THEN Switch 滑块颜色更新 | 正常 |
| AC-8.4 | WHEN 通过 `NODE_TOGGLE_UNSELECTED_COLOR` 设置颜色 THEN 关闭态轨道颜色更新 | 正常 |
| AC-8.5 | WHEN 注册 `NODE_TOGGLE_ON_CHANGE` 回调 THEN 状态变化时 `.data[0].i32` 返回 1（开）或 0（关） | 正常 |
| AC-8.6 | WHEN 尝试通过 C API 设置 SwitchStyle 子属性（pointRadius/trackBorderRadius）THEN 无对应 C API 枚举，不可设置（已知差距） | 正常 |

### US-9: 无障碍支持

**角色**: 辅助功能用户
**期望**: 我想要通过无障碍服务操作 Toggle
**价值**: 以便在无法直接触摸屏幕时完成开关操作

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-9.1 | WHEN 无障碍服务查询 Toggle THEN 报告 IsCheckable = true，IsChecked = 当前 isOn 状态 | 正常 |
| AC-9.2 | WHEN 无障碍服务查询 ToggleType THEN Switch 报告 "1"（`switch_accessibility_property.h:23`），Button 报告 "2"（`toggle_button_accessibility_property`），Checkbox 报告 "0"（`toggle_checkbox_accessibility_property`） | 正常 |
| AC-9.3 | WHEN 无障碍服务执行 ActionSelect THEN Toggle 状态设为开 | 正常 |
| AC-9.4 | WHEN 无障碍服务执行 ActionClearSelection THEN Toggle 状态设为关 | 正常 |

## 验收追溯

| AC编号 | 关联规则 | 关联 Task | 验证方式 | 证据 |
|-------|----------|-----------|----------|------|
| AC-1.1 ~ AC-1.3 | R-5, R-6 | TASK-TOGGLE-01 | UT | `test/unittest/core/pattern/toggle/` |
| AC-1.4 | R-7 | TASK-TOGGLE-01 | UT | toggle 单测 onChange 用例 |
| AC-1.5 | R-8 | TASK-TOGGLE-01 | UT | 双向绑定测试 |
| AC-1.6 | R-19 | TASK-TOGGLE-01 | UT | disabled 状态测试 |
| AC-2.1 ~ AC-2.5 | R-9, R-10 | TASK-TOGGLE-01 | UT | Switch 样式属性测试 |
| AC-3.1 ~ AC-3.4 | R-11, R-12 | TASK-TOGGLE-01 | UT | Button 样式与交互测试 |
| AC-4.1 ~ AC-4.5 | R-13, R-14 | TASK-TOGGLE-01 | UT + 手工 | 拖拽和动画测试 |
| AC-5.1 ~ AC-5.4 | R-15 | TASK-TOGGLE-01 | 手工 | Material 效果视觉验证 |
| AC-6.1 ~ AC-6.3 | R-1, R-2 | TASK-TOGGLE-01 | UT | 不同 API 版本布局测试 |
| AC-7.1 ~ AC-7.4 | R-16 | TASK-TOGGLE-01 | UT | ContentModifier 测试 |
| AC-8.1 ~ AC-8.6 | R-17, R-3 | TASK-TOGGLE-01 | C API UT | capi_all_modifiers_test |
| AC-9.1 ~ AC-9.4 | R-18 | TASK-TOGGLE-01 | UT | 无障碍属性测试 |


## 规则定义

> **统一规则表，取消 FR/BR/EX/RC 四分类。** 类型标签：**行为**（正常路径下的系统行为）、**边界**（输入/状态的临界点）、**异常**（非法输入或异常状态的处理）、**恢复**（系统异常后的恢复策略）。

| 规则ID | 类型 | 触发条件 | 预期行为 | 边界/约束 | 关联AC |
|--------|------|----------|----------|-----------|--------|
| R-1 | 行为 | `switch_layout_algorithm.cpp:120-135` | API 12 以下，Switch 类型布局强制 width = height × 1.8 的宽高比约束 | — | — |
| R-2 | 行为 | `toggle_button_pattern.cpp:678-682` | API 18 及以上，Button 类型形状从 CAPSULE 变更为 ROUNDED_RECTANGLE | — | — |
| R-3 | 行为 | `native_node.h:3630-3665, 10196` | C API 仅暴露 4 个属性枚举 + 1 个事件枚举，不包含 SwitchStyle 子属性 | — | — |
| R-4 | 行为 | `toggle_model_ng.cpp` | Toggle(type=Checkbox) 使用 TOGGLE_ETS_TAG 节点标签，与独立 Checkbox (CHECKBOX_ETS_TAG) 区分 | — | — |
| R-5 | 行为 | `toggle_model_ng.cpp:86-101` | Toggle 通过 ToggleType 枚举分发到三种 Pattern：Switch → SwitchPattern, Checkbox → CheckBoxPattern (via ToggleCheckBoxPattern), Button → ToggleButtonPattern | — | — |
| R-6 | 行为 | `toggle_model_ng.cpp:71` | ToggleType 运行时切换时，通过 ReCreateFrameNode 销毁旧节点重建新节点，子节点通过 ReplaceAllChild 迁移 | — | — |
| R-7 | 行为 | 源码 | 点击 Toggle 翻转 isOn 状态并触发 onChange 回调。Switch 通过 OnClick()（`switch_pattern.cpp`），Button 通过 InitEvent()（`toggle_button_pattern.cpp:605-637`） | — | — |
| R-8 | 行为 | SDK toggle.d.ts, toggle.static.d.ets | isOn 支持 `$$` 双向绑定（Dynamic API）和 `Bindable<boolean>`（Static API） | — | — |
| R-9 | 行为 | SDK toggle.d.ts | selectedColor 适用于所有三种类型；switchPointColor 和 switchStyle 仅适用于 Switch 类型 | — | — |
| R-10 | 行为 | `switch_paint_property.h` | switchPointColor 和 switchStyle.pointColor 写入同一个 SwitchPaintProperty::SwitchPointColor，功能等价 | — | — |
| R-11 | 行为 | `toggle_button_pattern.cpp:630` | Button 类型颜色切换为立即更新（无动画），通过 RenderContext::UpdateBackgroundColor() | — | — |
| R-12 | 行为 | `toggle_button_pattern.cpp:31-32` | Button 类型触摸效果使用 overlay 透明度混合：触摸 100ms / 悬停 250ms | — | — |
| R-13 | 行为 | `switch_pattern.cpp:843` | Switch 拖拽为水平方向，超过中点（`(mainSize + height_) / 2`）时翻转状态 | — | — |
| R-14 | 行为 | `switch_pattern.cpp:55-58` | Switch 状态切换使用弹簧动画：velocity=0, mass=1, stiffness=305, damping=24 | — | — |
| R-15 | 行为 | `switch_pattern.cpp:68, 675-676, 900-904` | Switch 长按 400ms 后触发 Material 效果，分高级（BrightnessBlender 覆盖节点）和低级（缩放动画 0.78→1.56）两种 | — | — |
| R-16 | 行为 | `switch_pattern.cpp:443, toggle_button_pattern.cpp:89, 829` | ContentModifier 激活时，Switch 跳过默认事件处理，Button 跳过颜色切换且背景设为 TRANSPARENT | — | — |
| R-17 | 行为 | `native_node.h` | C API 属性格式：颜色用 `.value[0].u32` (0xARGB)，布尔用 `.value[0].i32` (0/1) | — | — |
| R-18 | 行为 | `switch_accessibility_property.h:23` 等 | 三种类型均报告 IsCheckable=true，ToggleType 通过 ExtraElementInfo 区分：Checkbox="0", Switch="1", Button="2" | — | — |
| R-19 | 异常 | — | disabled 状态下点击不改变状态、不触发 onChange；Switch 类型应用 theme 的 disabledAlpha 到 opacity | `switch_pattern.cpp:236-237` | — |
| R-20 | 异常 | — | ContentModifier 激活时，Switch 的 disabled 状态不再应用 disabledAlpha | `switch_pattern.cpp:221-223` | — |
| R-21 | 异常 | — | ToggleType 运行时切换时，ContentModifier 子节点（匹配 GetBuilderId）排除在迁移之外，避免重复 | `switch_pattern.h:325, 335` | — |
| R-22 | 异常 | — | 拖拽未超过中点时，滑块弹回原位，状态不变 | `switch_pattern.cpp` HandleDragEnd 逻辑 | — |
| R-23 | 恢复 | — | ToggleType 切换失败时（Pattern 不匹配），通过 ToggleBasePattern::MountToHolder() 将旧子节点暂存到不可见的 holder 节点 | `toggle_base_pattern.cpp:25-39` | — |
| R-24 | 恢复 | — | SwitchStyle 属性 Reset 时恢复到 theme 默认值（pointColor → switchTheme->GetPointColor()，unselectedColor → switchTheme->GetInactiveColor()） | `toggle_dynamic_modifier.cpp:179-182, 496-498` | — |
| R-25 | 恢复 | — | IsOn Reset 时恢复到 false | `toggle_dynamic_modifier.cpp:547` | — |

---

## 验证映射

| 编号 | 对应规格项 | 验证方式 | 验证重点 |
|------|-----------|----------|----------|
| VM-1 | AC-1.1 ~ AC-1.3 | UT | 三种 ToggleType 正确创建对应 Pattern |
| VM-2 | AC-1.4, AC-1.5 | UT | onChange 触发 + 双向绑定同步 |
| VM-3 | AC-1.6, R-19 | UT | disabled 状态行为 |
| VM-4 | AC-2.1 ~ AC-2.5 | UT | Switch 颜色属性设置与默认值 |
| VM-5 | AC-3.1 ~ AC-3.4 | UT | Button 颜色切换 + 形状版本差异 |
| VM-6 | AC-4.1 ~ AC-4.3 | UT + 手工 | 拖拽方向判定 + RTL 反转 |
| VM-7 | AC-4.4 ~ AC-4.5 | 手工 | 弹簧动画参数验证 |
| VM-8 | AC-5.1 ~ AC-5.4 | 手工 | Material 效果分级验证 |
| VM-9 | AC-6.1 ~ AC-6.3 | UT | 不同 API 版本布局约束 |
| VM-10 | AC-7.1 ~ AC-7.4 | UT | ContentModifier 集成行为 |
| VM-11 | AC-8.1 ~ AC-8.6 | C API UT | C API 属性和事件 |
| VM-12 | AC-9.1 ~ AC-9.4 | UT | 无障碍属性和操作 |

## API 变更分析

### 新增 API

| API 名称 | 类型 | 功能描述 | 关联 AC | @since |
|----------|------|----------|---------|--------|
| Toggle(options: ToggleOptions) | Public | 创建 Toggle 组件 | AC-1.1 ~ AC-1.3 | 8 |
| ToggleAttribute.selectedColor(value: ResourceColor) | Public | 设置开启态背景色 | AC-2.1, AC-3.1 | 8 |
| ToggleAttribute.switchPointColor(color: ResourceColor) | Public | 设置 Switch 滑块颜色 | AC-2.2 | 8 |
| ToggleAttribute.onChange(callback) | Public | 状态变化回调 | AC-1.4 | 8 |
| ToggleAttribute.switchStyle(value: SwitchStyle) | Public | 设置 Switch 复合样式 | AC-2.3 | 12 |
| ToggleAttribute.contentModifier(modifier) | Public | 自定义渲染 | AC-7.1 | 12 |
| NODE_TOGGLE_SELECTED_COLOR | NDK/Public | C API 开启态颜色 | AC-8.2 | NDK |
| NODE_TOGGLE_SWITCH_POINT_COLOR | NDK/Public | C API 滑块颜色 | AC-8.3 | NDK |
| NODE_TOGGLE_VALUE | NDK/Public | C API 状态值 | AC-8.1 | NDK |
| NODE_TOGGLE_UNSELECTED_COLOR | NDK/Public | C API 关闭态颜色 | AC-8.4 | NDK |
| NODE_TOGGLE_ON_CHANGE | NDK/Public | C API 状态变化事件 | AC-8.5 | NDK |

### 变更/废弃 API

| API 名称 | 变更类型 | 关联 AC |
|----------|----------|---------|
| 无 | — | — |

> 截至当前版本，Toggle 未发现任何 @deprecated 或 @useinstead 标注的 API。

## 接口规格

### 接口定义

> 本特性为已有实现补录，接口行为定义详见上方规则定义和用户故事。

无新增接口规格。

---

## 兼容性声明

- **已有 API 行为变更:** 是
  - API 12+: Switch 取消 1.8:1 强制宽高比，允许任意尺寸（AC-6.1, AC-6.2）
  - API 18+: Button 形状从 CAPSULE 变更为 ROUNDED_RECTANGLE（AC-3.2）
  - API 18+: ContentModifier 布局使用 `ResetContent()` 替代 `Reset()`（AC-6.3）
- **配置文件格式变更:** 否
- **数据存储格式变更:** 否
- **最低支持版本:** API 8
- **API 版本号策略:** 基础 API @since 8，SwitchStyle/ContentModifier @since 12，ExtendableToggle @since 26

## 架构约束

| 关键约束 | 约束说明 | 影响 AC |
|----------|----------|---------|
| 单标签多 Pattern | 三种 ToggleType 共用 TOGGLE_ETS_TAG，通过 Model 层分发到不同 Pattern 实现 | AC-1.1 ~ AC-1.3 |
| Checkbox 委托模型 | ToggleCheckBoxPattern 继承 CheckBoxPattern，行为几乎完全委托，仅重写无障碍属性 | AC-9.2 |
| C API 属性子集 | C API 仅暴露 selectedColor/switchPointColor/value/unselectedColor，无 SwitchStyle 子属性 | AC-8.6 |
| Material 效果依赖 | 高级 Material 效果依赖 graphic_2d 的 BrightnessBlender | AC-5.2 |

> 本节列出本特性 AC 验证必须满足的约束。架构规则适用性及设计方案见 design.md。

## 非功能性需求

| 类型 | 指标/阈值 | 验证方式 | 证据 |
|------|-----------|----------|------|
| 性能 | Switch 弹簧动画帧率 ≥ 60fps | 手工 + Trace | Trace 打点 |
| 内存 | Material 高级效果 3 个覆盖节点在长按结束后销毁 | UT + Dump | 节点树 Dump |
| 安全 | 无安全相关接口 | N/A | — |
| 可靠性 | ToggleType 运行时切换不崩溃，子节点正确迁移 | UT | toggle 单测 |
| 问题定位 | hilog 标签覆盖关键路径（状态切换、类型分发） | 代码审查 | — |

> N/A 判定见 proposal.md 不涉及项确认。本节仅为适用项填写具体指标。

## 多设备适配声明

| 设备类型 | 行为差异 | 规格/约束 | 验证方式 | 证据 |
|----------|----------|-----------|----------|------|
| 手机 | 无差异 | — | — | — |
| 平板 | 无差异 | — | — | — |
| 折叠屏 | 无差异 | — | — | — |

---

## 全局特性影响

| 特性 | 适用？ | 结论 | 关联场景 |
|------|--------|------|----------|
| 无障碍 | 是 | 三种类型均实现 IsCheckable/IsChecked/ActionSelect/ActionClearSelection，通过 ExtraElementInfo 区分类型 | AC-9.1 ~ AC-9.4 |
| 大字体 | 是 | Button 类型的 textFontSize 从 ToggleTheme 获取，跟随系统字体缩放 | AC-3.1 |
| 深色模式 | 是 | 颜色属性通过 ResourceColor 支持主题跟随 | AC-2.1, AC-2.5 |
| 多窗口/分屏 | 否 | Toggle 无窗口相关特殊行为 | — |
| 多用户 | 否 | 无用户相关状态 | — |
| 版本升级 | 是 | API 12/18 布局和形状行为变更需要兼容性处理 | AC-6.1, AC-3.2 |
| 生态兼容 | 是 | C API 子集限制需在 NDK 文档中明确 | AC-8.6 |

## 行为场景（Gherkin）

```gherkin
Feature: Toggle 组件
  作为应用开发者
  我想要使用 Toggle 组件实现开关交互
  以便在不同场景中切换状态

  Scenario: Switch 类型创建和点击
    Given Toggle 组件以 type=Switch, isOn=false 创建
    When 用户点击 Toggle
    Then isOn 变为 true
    And onChange 回调被触发，参数为 true
    And Switch 轨道颜色过渡到 selectedColor

  Scenario: Switch 拖拽超过中点
    Given Toggle 组件以 type=Switch, isOn=false 创建
    When 用户水平拖拽滑块超过 (mainSize + height_) / 2 中点
    Then isOn 变为 true
    And 使用弹簧动画（stiffness=305, damping=24）过渡

  Scenario: Switch 拖拽未超过中点
    Given Toggle 组件以 type=Switch, isOn=true 创建
    When 用户水平拖拽滑块但未超过中点
    Then isOn 保持 true
    And 滑块弹回原位

  Scenario: RTL 布局下拖拽
    Given Toggle 组件以 type=Switch 创建且布局方向为 RTL
    When 用户向左拖拽滑块超过中点
    Then 拖拽方向判定反转，状态正确翻转

  Scenario: Switch Material 长按（高级）
    Given Toggle 组件以 type=Switch 创建且 HasSystemMaterial() = true，等级为 EXQUISITE
    When 用户长按 Switch 超过 400ms
    Then 创建 dragFrameNode_/dragPointNode_/blurCoverNode_ 三层覆盖节点
    And 应用 BrightnessBlender（linearRate=1.048, degree=0.37647, saturation=1.5）

  Scenario: Switch Material 长按（低级）
    Given Toggle 组件以 type=Switch 创建且 HasSystemMaterial() = true，等级非 EXQUISITE/GENTLE
    When 用户长按 Switch 超过 400ms
    Then 滑块执行缩放动画（0.78→1.56）

  Scenario: Button 类型 API 18+ 形状
    Given Toggle 组件以 type=Button 创建
    When 运行在 API 18+ 环境
    Then 按钮形状为 ROUNDED_RECTANGLE

  Scenario: Button 类型 API 18 以下形状
    Given Toggle 组件以 type=Button 创建
    When 运行在 API 18 以下环境
    Then 按钮形状为 CAPSULE

  Scenario Outline: Switch API 版本布局差异
    Given Toggle 组件以 type=Switch 创建，设置 width=<width>, height=<height>
    When 运行在 <api_version>
    Then 实际宽度为 <actual_width>

    Examples:
      | width | height | api_version | actual_width |
      | 50    | 30     | API 11      | 54 (30×1.8)  |
      | 50    | 30     | API 12      | 50           |

  Scenario: Disabled 状态
    Given Toggle 组件以 type=Switch 创建且 enabled=false
    When 用户点击 Toggle
    Then isOn 状态不变
    And onChange 不触发
    And 组件 opacity 应用 disabledAlpha

  Scenario: ContentModifier 激活
    Given Toggle 组件设置了 contentModifier
    When ContentModifier 激活
    Then 默认渲染被自定义 Builder 替换
    And 默认事件处理被跳过

  Scenario: C API 状态设置
    Given 通过 C API 创建 ARKUI_NODE_TOGGLE 节点
    When 设置 NODE_TOGGLE_VALUE = 1
    Then Toggle 状态为开
    And NODE_TOGGLE_ON_CHANGE 事件触发

  Scenario: 无障碍操作
    Given Toggle 组件以 type=Switch 创建
    When 无障碍服务执行 ActionSelect
    Then Toggle 状态设为开
    And 无障碍属性报告 IsChecked = true, ToggleType = "1"
```

## Spec 自审清单

- [x] 无"待定""TBD""TODO"等占位符
- [x] 所有 AC 使用 WHEN/THEN 格式，可独立测试
- [x] 范围边界明确（做什么/不做什么清晰）
- [x] 无语义模糊表述（"快速""稳定""尽可能"等）
- [x] AC 与业务规则/异常规则/恢复契约交叉一致

## context-references

```yaml
context-queries:
  - repo: "openharmony/ace_engine"
    query: "Toggle 组件三形态分发机制和 ToggleType 运行时切换"
  - repo: "openharmony/ace_engine"
    query: "Switch Material 长按效果和 BrightnessBlender 集成"
  - repo: "openharmony/ace_engine"
    query: "Toggle C API 属性枚举和 node_toggle_modifier 实现"
```

**关键文档:**
- SDK 类型定义: `interface/sdk-js/api/@internal/component/ets/toggle.d.ts`
- KB 路由: `docs/kb/components/selector/toggle.md`
- 源码入口: `frameworks/core/components_ng/pattern/toggle/toggle_model_ng.cpp`
