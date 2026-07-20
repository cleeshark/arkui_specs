# 特性规格

## 概述

| 字段 | 内容 |
|------|------|
| 特性名称 | Button 组件全量规格 |
| 特性编号 | Func-05-04-01-Feat-01 |
| FuncID | 05-04-01 |
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
| ADDED | Button 组件 + ButtonType 枚举 (Capsule/Circle/Normal) | @since 7 |
| ADDED | labelStyle 复合样式属性 (fontSize/fontWeight/fontFamily/fontColor/fontStyle) | @since 10 |
| ADDED | ControlSize 枚举 (SMALL/NORMAL/LARGE) | @since 11 |
| ADDED | ButtonStyleMode 枚举 (EMPHASIZED/TEXTUAL/FILLED) | @since 11 |
| ADDED | ButtonRole 枚举 (NORMAL/ERROR) | @since 12 |
| ADDED | ContentModifier 自定义渲染 | @since 12 |
| ADDED | ButtonType.ROUNDED_RECTANGLE 新类型 | @since 15 |
| MODIFIED | ButtonType 默认值从 CAPSULE 切换为 ROUNDED_RECTANGLE | API 18 行为变更 |
| ADDED | minFontScale / maxFontScale 字体缩放范围控制 | @since 18 |
| ADDED | C API: NODE_BUTTON_LABEL / NODE_BUTTON_TYPE | NDK 属性 |
| ADDED | C API: NODE_BUTTON_MIN_FONT_SCALE / NODE_BUTTON_MAX_FONT_SCALE | NDK 属性 |
| ADDED | Static API: button.static.d.ets | @since 23 |
| ADDED | ExtendableButton | @since 26 |

## 输入文档

- **需求基线**: 已有能力补录（无独立 requirement.md / proposal.md）
- **设计文档**: `specs/05-ui-components/04-input-form-components/01-button/design.md`
- **KB 路由**: `docs/kb/components/selector/button.md`
- **SDK 类型定义**:
  - Dynamic: `<OH_ROOT>/interface/sdk-js/api/@internal/component/ets/button.d.ts`
  - Static: `<OH_ROOT>/interface/sdk-js/api/arkui/component/button.static.d.ets`
  - Modifier: `<OH_ROOT>/interface/sdk-js/api/arkui/ButtonModifier.d.ts`

> 需求基线、不涉及项、受影响子系统与仓库详见 proposal.md，本文档不重复摘录。design.md 与本文档并行产出，互不依赖。

## 用户故事

### US-1: 基础按钮创建与类型

**角色**: 应用开发者
**期望**: 我想要使用 Button 组件创建不同类型的按钮
**价值**: 以便在不同场景中使用合适的按钮形状

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-1.1 | WHEN 创建 `Button('Click', { type: ButtonType.Capsule })` THEN 显示胶囊形按钮，标签为"Click" | 正常 |
| AC-1.2 | WHEN 创建 `Button({ type: ButtonType.Circle })` THEN 显示圆形按钮 | 正常 |
| AC-1.3 | WHEN 创建 `Button('Submit', { type: ButtonType.Normal })` THEN 显示普通矩形按钮 | 正常 |
| AC-1.4 | WHEN 创建 `Button('Rounded', { type: ButtonType.ROUNDED_RECTANGLE })` THEN 显示圆角矩形按钮 | 正常 |
| AC-1.5 | WHEN 在 API 18+ 创建 `Button('Default')` 未指定 type THEN 默认类型为 ROUNDED_RECTANGLE；API 18 以下默认为 CAPSULE | 边界 |
| AC-1.6 | WHEN 按钮处于 disabled 状态 THEN 点击不触发 onClick 回调，应用 disabledAlpha 透明度 | 正常 |

### US-2: 点击交互与事件

**角色**: 应用开发者
**期望**: 我想要为按钮绑定点击事件
**价值**: 以便在用户点击按钮时执行业务逻辑

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-2.1 | WHEN 用户点击 Button THEN onClick 回调被触发 | 正常 |
| AC-2.2 | WHEN 用户按下 Button THEN 进入 pressed 状态，背景色/缩放变化（`button_pattern.cpp`） | 正常 |
| AC-2.3 | WHEN 用户抬起手指/鼠标 THEN 恢复 normal 状态，触发 onClick | 正常 |
| AC-2.4 | WHEN 鼠标悬停 Button THEN 进入 hover 状态，视觉反馈持续 MOUSE_HOVER_DURATION=250ms | 正常 |
| AC-2.5 | WHEN 触摸动画时长 THEN TOUCH_DURATION=100ms | 正常 |

### US-3: ControlSize 尺寸体系

**角色**: 应用开发者
**期望**: 我想要使用统一的尺寸枚举控制按钮大小
**价值**: 以便在不同场景中快速匹配设计规范

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-3.1 | WHEN 设置 `.controlSize(ControlSize.SMALL)` THEN 按钮高度匹配 SMALL 预设尺寸 | 正常 |
| AC-3.2 | WHEN 设置 `.controlSize(ControlSize.NORMAL)` THEN 按钮高度匹配 NORMAL 预设尺寸 | 正常 |
| AC-3.3 | WHEN 同时设置 `.controlSize()` 和 `.width()`/`.height()` THEN 手动尺寸优先级更高，覆盖 ControlSize | 边界 |

### US-4: ButtonStyleMode 和 ButtonRole

**角色**: 应用开发者
**期望**: 我想要控制按钮的视觉样式层级和功能语义角色
**价值**: 以便匹配应用的交互设计规范

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-4.1 | WHEN 设置 `.buttonStyleMode(ButtonStyleMode.EMPHASIZED)` THEN 按钮使用强调样式（emphasize 颜色） | 正常 |
| AC-4.2 | WHEN 设置 `.buttonStyleMode(ButtonStyleMode.TEXTUAL)` THEN 按钮使用文本样式（透明背景） | 正常 |
| AC-4.3 | WHEN 设置 `.buttonRole(ButtonRole.ERROR)` THEN 按钮使用错误角色颜色 | 正常 |
| AC-4.4 | WHEN 同时设置 ButtonStyleMode 和 ButtonRole THEN 两者正交组合生效（如 EMPHASIZED + ERROR = 强调的错误按钮） | 正常 |

### US-5: 标签字体样式

**角色**: 应用开发者
**期望**: 我想要自定义按钮标签的字体样式
**价值**: 以便匹配应用的设计语言

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-5.1 | WHEN 设置 `.labelStyle({ fontSize: 16, fontWeight: FontWeight.Bold, fontColor: '#FF0000' })` THEN 按钮标签字体大小 16vp、粗体、红色 | 正常 |
| AC-5.2 | WHEN 同时使用 `.labelStyle()` 和独立属性 `.fontSize()` THEN 后设置的生效，两者功能等价（`button_layout_property.h`） | 正常 |
| AC-5.3 | WHEN 未设置字体属性 THEN 使用 ButtonTheme 默认值（fontSize/fontWeight/fontColor 从 `button_theme_wrapper.h` 获取） | 异常 |

### US-6: 字体缩放范围控制

**角色**: 应用开发者
**期望**: 我想要限制按钮标签的字体缩放范围
**价值**: 以避免系统字体过大时按钮文本溢出

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-6.1 | WHEN 设置 `.minFontScale(0.5)` THEN 系统字体缩放低于 0.5 时，实际缩放被限制为 0.5 | 边界 |
| AC-6.2 | WHEN 设置 `.maxFontScale(2.0)` THEN 系统字体缩放高于 2.0 时，实际缩放被限制为 2.0 | 边界 |
| AC-6.3 | WHEN 同时设置 minFontScale=1.0 和 maxFontScale=1.5 THEN 实际缩放 = clamp(systemFontScale, 1.0, 1.5) | 边界 |

### US-7: ContentModifier 自定义渲染

**角色**: 应用开发者
**期望**: 我想要使用 ContentModifier 完全自定义按钮的渲染内容
**价值**: 以便实现超出标准样式的定制化需求

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-7.1 | WHEN 设置 `contentModifier(modifier)` THEN 组件通过 `ButtonConfiguration { label, enabled, triggerChange }` 回调自定义 Builder | 正常 |
| AC-7.2 | WHEN ContentModifier 激活时 THEN 按钮跳过默认文本渲染，使用自定义 Builder 内容替代 | 正常 |
| AC-7.3 | WHEN 调用 `triggerChange('NewLabel')` THEN 按钮标签程序化更新为 'NewLabel' | 正常 |

### US-8: 触摸与悬停动画

**角色**: 终端用户
**期望**: 我想要在按下和悬停按钮时看到视觉反馈
**价值**: 以便感知交互正在进行

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-8.1 | WHEN 触摸按下按钮 THEN 进入 pressed 状态，视觉变化持续 TOUCH_DURATION=100ms（`button_pattern.cpp`） | 正常 |
| AC-8.2 | WHEN 鼠标悬停按钮 THEN 进入 hover 状态，视觉变化持续 MOUSE_HOVER_DURATION=250ms（`button_pattern.cpp`） | 正常 |
| AC-8.3 | WHEN 按钮处于 disabled 状态 THEN 不触发触摸/悬停动画 | 异常 |

### US-9: C API / NDK 支持

**角色**: NDK 开发者
**期望**: 我想要通过 C API 控制按钮的标签、类型和字体缩放
**价值**: 以便在 Native 层集成 Button 组件

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-9.1 | WHEN 通过 `NODE_BUTTON_LABEL` 设置 `.string = "Submit"` THEN 按钮标签文本更新为 "Submit" | 正常 |
| AC-9.2 | WHEN 通过 `NODE_BUTTON_TYPE` 设置 `.value[0].i32 = 1` THEN 按钮类型变更为 Circle (0=Capsule, 1=Circle, 2=Normal, 3=ROUNDED_RECTANGLE) | 正常 |
| AC-9.3 | WHEN 通过 `NODE_BUTTON_MIN_FONT_SCALE` 设置 `.value[0].f = 0.5` THEN 最小字体缩放比例设为 0.5 | 正常 |
| AC-9.4 | WHEN 通过 `NODE_BUTTON_MAX_FONT_SCALE` 设置 `.value[0].f = 2.0` THEN 最大字体缩放比例设为 2.0 | 正常 |

## 验收追溯

| AC编号 | 关联规则 | 关联 Task | 验证方式 | 证据 |
|-------|----------|-----------|----------|------|
| AC-1.1 ~ AC-1.5 | R-1, R-2 | TASK-BUTTON-01 | UT | `test/unittest/core/pattern/button/` |
| AC-1.6 | R-15 | TASK-BUTTON-01 | UT | disabled 状态测试 |
| AC-2.1 ~ AC-2.5 | R-3, R-4, R-5 | TASK-BUTTON-01 | UT | 点击事件和触摸/悬停动画测试 |
| AC-3.1 ~ AC-3.3 | R-6, R-7 | TASK-BUTTON-01 | UT | ControlSize 尺寸测试 |
| AC-4.1 ~ AC-4.4 | R-8, R-9 | TASK-BUTTON-01 | UT | StyleMode 和 Role 测试 |
| AC-5.1 ~ AC-5.3 | R-10, R-11 | TASK-BUTTON-01 | UT | labelStyle 和字体属性测试 |
| AC-6.1 ~ AC-6.3 | R-12 | TASK-BUTTON-01 | UT | 字体缩放范围测试 |
| AC-7.1 ~ AC-7.3 | R-13 | TASK-BUTTON-01 | UT | ContentModifier 测试 |
| AC-8.1 ~ AC-8.3 | R-4, R-5, R-15 | TASK-BUTTON-01 | UT + 手工 | 触摸/悬停动画验证 |
| AC-9.1 ~ AC-9.4 | R-14 | TASK-BUTTON-01 | C API UT | capi_all_modifiers_test |

## 规则定义

> **统一规则表，取消 FR/BR/EX/RC 四分类。** 类型标签：**行为**（正常路径下的系统行为）、**边界**（输入/状态的临界点）、**异常**（非法输入或异常状态的处理）、**恢复**（系统异常后的恢复策略）。

| 规则ID | 类型 | 触发条件 | 预期行为 | 边界/约束 | 关联AC |
|--------|------|----------|----------|-----------|--------|
| R-1 | 行为 | `button_model_ng.cpp` | Button 通过 ButtonModelNG::Create() 创建节点，ButtonType 存入 ButtonLayoutProperty | — | AC-1.1 ~ AC-1.4 |
| R-2 | 行为 | `button_pattern.cpp` | API >= 18 默认 ButtonType 为 ROUNDED_RECTANGLE；API < 18 默认为 CAPSULE | PlatformVersion 分支 | AC-1.5 |
| R-3 | 行为 | `button_pattern.cpp` | 用户点击 Button 时，先进入 pressed 状态，触摸抬起后恢复 normal 并触发 onClick 回调 | — | AC-2.1 ~ AC-2.3 |
| R-4 | 行为 | `button_pattern.cpp` | 触摸按下进入 pressed 状态，视觉变化持续 TOUCH_DURATION=100ms | — | AC-2.2, AC-8.1 |
| R-5 | 行为 | `button_pattern.cpp` | 鼠标悬停进入 hover 状态，视觉变化持续 MOUSE_HOVER_DURATION=250ms | — | AC-2.4, AC-8.2 |
| R-6 | 行为 | `button_layout_algorithm.cpp` | ControlSize (SMALL/NORMAL/LARGE) 在 LayoutAlgorithm 中映射为预设高度 | @since 11 | AC-3.1, AC-3.2 |
| R-7 | 边界 | `button_layout_algorithm.cpp` | 手动 width/height 优先级高于 ControlSize，覆盖预设尺寸 | — | AC-3.3 |
| R-8 | 行为 | `button_pattern.cpp`, `button_theme_wrapper.h` | ButtonStyleMode (EMPHASIZED/TEXTUAL/FILLED) 控制视觉样式层级 | @since 11 | AC-4.1, AC-4.2 |
| R-9 | 行为 | `button_pattern.cpp`, `button_theme_wrapper.h` | ButtonRole (NORMAL/ERROR) 控制功能语义角色，与 ButtonStyleMode 正交组合 | @since 12 | AC-4.3, AC-4.4 |
| R-10 | 行为 | `button_layout_property.h` | labelStyle 复合属性封装 fontSize/fontWeight/fontFamily/fontColor/fontStyle | @since 10 | AC-5.1 |
| R-11 | 行为 | `button_layout_property.h` | labelStyle 与独立字体属性功能等价，后设置的生效 | — | AC-5.2 |
| R-12 | 边界 | `button_layout_algorithm.cpp` | 实际字体缩放 = clamp(systemFontScale, minFontScale, maxFontScale)；minFontScale 默认 0，maxFontScale 默认 Infinity | @since 18 | AC-6.1 ~ AC-6.3 |
| R-13 | 行为 | `button_pattern.cpp` | ContentModifier 激活时，按钮跳过默认文本渲染，使用自定义 Builder 内容替代；通过 ButtonConfiguration 回调 | @since 12 | AC-7.1 ~ AC-7.3 |
| R-14 | 行为 | `node_button_modifier.cpp`, `native_node.h` | C API: NODE_BUTTON_LABEL (.string)、NODE_BUTTON_TYPE (.value[0].i32)、NODE_BUTTON_MIN_FONT_SCALE (.value[0].f)、NODE_BUTTON_MAX_FONT_SCALE (.value[0].f) | ARKUI_NODE_BUTTON=9 | AC-9.1 ~ AC-9.4 |
| R-15 | 异常 | `button_pattern.cpp` | disabled 状态下不响应点击、不触发 onClick、不触发触摸/悬停动画，应用 disabledAlpha 透明度 | — | AC-1.6, AC-8.3 |
| R-16 | 恢复 | `button_theme_wrapper.h` | 字体/颜色属性 Reset 时恢复到 ButtonTheme 默认值 | — | AC-5.3 |

---

## 验证映射

| 编号 | 对应规格项 | 验证方式 | 验证重点 |
|------|-----------|----------|----------|
| VM-1 | AC-1.1 ~ AC-1.5 | UT | 四种 ButtonType 正确创建 + 默认值版本差异 |
| VM-2 | AC-1.6, R-15 | UT | disabled 状态行为 |
| VM-3 | AC-2.1 ~ AC-2.5 | UT | 点击事件 + 触摸/悬停动画 |
| VM-4 | AC-3.1 ~ AC-3.3 | UT | ControlSize 尺寸映射 + 手动覆盖 |
| VM-5 | AC-4.1 ~ AC-4.4 | UT | StyleMode + Role 正交组合 |
| VM-6 | AC-5.1 ~ AC-5.3 | UT | labelStyle 与独立属性等价性 + 默认值 |
| VM-7 | AC-6.1 ~ AC-6.3 | UT | 字体缩放 clamp 行为 |
| VM-8 | AC-7.1 ~ AC-7.3 | UT | ContentModifier 集成行为 |
| VM-9 | AC-8.1 ~ AC-8.3 | UT + 手工 | 触摸/悬停动画时长和 disabled 降级 |
| VM-10 | AC-9.1 ~ AC-9.4 | C API UT | C API 属性设置 |

## API 变更分析

### 新增 API

| API 名称 | 开放范围 | 入参概要 | 返回值 | 错误码范围 | 功能描述 | 关联 AC | @since |
|----------|---------|----------|--------|-----------|----------|---------|--------|
| Button(label?, options?) | Public | label: ResourceStr, type: ButtonType | ButtonAttribute | N/A | 创建 Button 组件 | AC-1.1 ~ AC-1.4 | 7 |
| ButtonAttribute.labelStyle(value) | Public | TextStyle | ButtonAttribute | N/A | 设置标签复合样式 | AC-5.1 | 10 |
| ButtonAttribute.controlSize(value) | Public | ControlSize | ButtonAttribute | N/A | 设置统一尺寸 | AC-3.1 ~ AC-3.3 | 11 |
| ButtonAttribute.buttonStyleMode(value) | Public | ButtonStyleMode | ButtonAttribute | N/A | 设置视觉样式层级 | AC-4.1, AC-4.2 | 11 |
| ButtonAttribute.buttonRole(value) | Public | ButtonRole | ButtonAttribute | N/A | 设置功能语义角色 | AC-4.3, AC-4.4 | 12 |
| ButtonAttribute.contentModifier(modifier) | Public | ContentModifier<ButtonConfiguration> | ButtonAttribute | N/A | 自定义渲染 | AC-7.1 ~ AC-7.3 | 12 |
| ButtonType.ROUNDED_RECTANGLE | Public | — | — | — | 新增圆角矩形类型 | AC-1.4 | 15 |
| ButtonAttribute.minFontScale(value) | Public | number \| Resource | ButtonAttribute | N/A | 最小字体缩放 | AC-6.1, AC-6.3 | 18 |
| ButtonAttribute.maxFontScale(value) | Public | number \| Resource | ButtonAttribute | N/A | 最大字体缩放 | AC-6.2, AC-6.3 | 18 |
| NODE_BUTTON_LABEL | NDK/Public | .string | void | N/A | C API 设置标签 | AC-9.1 | NDK |
| NODE_BUTTON_TYPE | NDK/Public | .value[0].i32 | void | N/A | C API 设置类型 | AC-9.2 | NDK |
| NODE_BUTTON_MIN_FONT_SCALE | NDK/Public | .value[0].f | void | N/A | C API 最小字体缩放 | AC-9.3 | NDK |
| NODE_BUTTON_MAX_FONT_SCALE | NDK/Public | .value[0].f | void | N/A | C API 最大字体缩放 | AC-9.4 | NDK |

### 变更/废弃 API

| API 名称 | 变更类型 | 影响场景 | 迁移指引 | 关联 AC |
|----------|----------|----------|---------|---------|
| ButtonType 默认值 | 变更 | API 18+ 默认从 CAPSULE 变更为 ROUNDED_RECTANGLE | 旧版本通过 PlatformVersion 保持 CAPSULE 默认值；新版本默认 ROUNDED_RECTANGLE | AC-1.5 |

> 截至当前版本，Button 未发现任何 @deprecated 或 @useinstead 标注的 API。

## 接口规格

### 接口定义

> 本特性为已有实现补录，接口行为定义详见上方规则定义和用户故事。

无新增接口规格。

---

## 兼容性声明

- **已有 API 行为变更:** 是
  - API 18+: ButtonType 默认值从 CAPSULE 变更为 ROUNDED_RECTANGLE（AC-1.5）
- **配置文件格式变更:** 否
- **数据存储格式变更:** 否
- **最低支持版本:** API 7
- **API 版本号策略:** 基础 API @since 7，labelStyle @since 10，ControlSize/ButtonStyleMode @since 11，ButtonRole/ContentModifier @since 12，ROUNDED_RECTANGLE @since 15，minFontScale/maxFontScale @since 18，Static API @since 23，ExtendableButton @since 26

## 架构约束

| 关键约束 | 约束说明 | 影响 AC |
|----------|----------|---------|
| 组件化 SO | Button 已组件化为独立 SO（libarkui_button.z.so），通过 ButtonDynamicModule 入口 | AC-1.1 ~ AC-1.4 |
| ToggleButton 继承 | ToggleButtonPattern 继承 ButtonPattern，复用点击/状态逻辑 | AC-2.1 ~ AC-2.3 |
| C API 属性子集 | C API 仅暴露 LABEL/TYPE/MIN_FONT_SCALE/MAX_FONT_SCALE，不含 StyleMode/Role/ControlSize/labelStyle | AC-9.1 ~ AC-9.4 |
| PlatformVersion 分支 | API 18 默认 ButtonType 变更需要 PlatformVersion 条件分支 | AC-1.5 |

> 本节列出本特性 AC 验证必须满足的约束。架构规则适用性及设计方案见 design.md。

## 非功能性需求

| 类型 | 指标/阈值 | 验证方式 | 证据 |
|------|-----------|----------|------|
| 性能 | 触摸动画帧率 ≥ 60fps | 手工 + Trace | Trace 打点 |
| 内存 | ContentModifier 自定义节点在按钮销毁时释放 | UT + Dump | 节点树 Dump |
| 安全 | 无安全相关接口 | N/A | — |
| 可靠性 | ButtonType 切换不崩溃，标签正确更新 | UT | button 单测 |
| 问题定位 | hilog 标签覆盖关键路径（状态切换、点击事件） | 代码审查 | — |

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
| 无障碍 | 是 | Button 实现 AccessibilityProperty，报告 IsButton=true，支持 ActionClick；disabled 状态不响应无障碍点击 | AC-1.6 |
| 大字体 | 是 | minFontScale/maxFontScale 控制字体缩放范围；labelStyle 跟随系统字体缩放 | AC-6.1 ~ AC-6.3 |
| 深色模式 | 是 | 颜色属性通过 ResourceColor 支持主题跟随 | AC-5.3 |
| 多窗口/分屏 | 否 | Button 无窗口相关特殊行为 | — |
| 多用户 | 否 | 无用户相关状态 | — |
| 版本升级 | 是 | API 18 默认 ButtonType 变更需要兼容性处理 | AC-1.5 |
| 生态兼容 | 是 | C API 属性子集限制需在 NDK 文档中明确 | AC-9.1 ~ AC-9.4 |

## 行为场景（Gherkin）

```gherkin
Feature: Button 组件
  作为应用开发者
  我想要使用 Button 组件创建交互按钮
  以便在不同场景中提供点击操作

  Scenario: 创建胶囊按钮
    Given 创建 Button('Click', { type: ButtonType.Capsule })
    Then 显示胶囊形按钮，标签为 "Click"

  Scenario: 创建圆角矩形按钮 (API 18+)
    Given 运行在 API 18+ 环境
    When 创建 Button('Default') 未指定 type
    Then 默认类型为 ROUNDED_RECTANGLE

  Scenario: 创建胶囊按钮 (API 18 以下)
    Given 运行在 API 18 以下环境
    When 创建 Button('Default') 未指定 type
    Then 默认类型为 CAPSULE

  Scenario: 点击按钮
    Given Button 组件已创建
    When 用户点击按钮
    Then 进入 pressed 状态
    And 触摸抬起后恢复 normal 状态
    And onClick 回调被触发

  Scenario: 触摸动画
    Given Button 组件已创建
    When 用户触摸按下按钮
    Then 进入 pressed 状态
    And 视觉变化持续 100ms (TOUCH_DURATION)

  Scenario: 悬停动画
    Given Button 组件已创建
    When 鼠标悬停按钮
    Then 进入 hover 状态
    And 视觉变化持续 250ms (MOUSE_HOVER_DURATION)

  Scenario: Disabled 状态
    Given Button 组件已创建且 enabled=false
    When 用户点击按钮
    Then onClick 不触发
    And 不触发触摸/悬停动画
    And 组件 opacity 应用 disabledAlpha

  Scenario: ControlSize 尺寸
    Given 设置 .controlSize(ControlSize.SMALL)
    Then 按钮高度匹配 SMALL 预设尺寸

  Scenario: 字体缩放范围
    Given 设置 minFontScale=0.5, maxFontScale=2.0
    When 系统字体缩放为 3.0
    Then 实际字体缩放被限制为 2.0

  Scenario: ContentModifier 自定义渲染
    Given Button 设置了 contentModifier
    When ContentModifier 激活
    Then 默认文本渲染被自定义 Builder 替换
    And 通过 ButtonConfiguration 回调获取 label 和 enabled

  Scenario: C API 设置标签
    Given 通过 C API 创建 ARKUI_NODE_BUTTON 节点
    When 设置 NODE_BUTTON_LABEL = "Submit"
    Then 按钮标签文本更新为 "Submit"
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
    query: "Button ButtonType 默认值 PlatformVersion 分支和 API 18 变更"
  - repo: "openharmony/ace_engine"
    query: "Button ControlSize/ButtonStyleMode/ButtonRole 尺寸和样式体系"
  - repo: "openharmony/ace_engine"
    query: "Button minFontScale/maxFontScale 字体缩放 clamp 逻辑"
  - repo: "openharmony/ace_engine"
    query: "Button C API node_button_modifier 属性委托实现"
```

**关键文档:**
- SDK 类型定义: `interface/sdk-js/api/@internal/component/ets/button.d.ts`
- KB 路由: `docs/kb/components/selector/button.md`
- 源码入口: `frameworks/core/components_ng/pattern/button/button_pattern.cpp`
