# 特性规格

## 概述

| 属性 | 值 |
|------|-----|
| 特性名称 | TextInput 键盘/IME/自定义键盘 |
| 特性编号 | Func-05-09-08-Feat-07 |
| 所属 Epic | 无 |
| 优先级 | P1 |
| 目标版本 | API 7–20 |
| SIG 归属 | ArkUI SIG |
| 状态 | Baselined |
| 复杂度 | 复杂 |

## 本次变更范围（Delta）
全新特性补录（lineage: new），无 Delta。

## 输入文档
- 设计文档：`08-text-input/design.md`
- 源码定位：`text_field_model_ng.h`（SetEnterKeyType/SetKeyboardAppearance/SetCustomKeyboard/SetCustomKeyboardWithNode/SetAutoCapitalizationMode/SetEnableFillAnimation/SetBlurOnSubmit）、`js_textfield.cpp`（ParseKeyboardAppearanceConfig/SetKeyboardAppearanceConfig）、`text_keyboard_common_type.h`

## 用户故事

### US-1: 回车键类型
作为开发者，我希望经 enterKeyType 设置软键盘回车键样式。

| AC编号 | 验收标准 | 类型 |
|--------|----------|------|
| AC-1.1 | WHEN `enterKeyType(EnterKeyType.Go/Search/Send/Next/Done/PREVIOUS/NEW_LINE)`（@since 7–12）THEN 设置回车键样式 | 正常 |

### US-2: 键盘外观
作为开发者，我希望经 keyboardAppearance/keyboardAppearanceConfig 定制键盘外观。

| AC编号 | 验收标准 | 类型 |
|--------|----------|------|
| AC-2.1 | WHEN `keyboardAppearance(appearance)`（@since 15）THEN 设置键盘外观 | 正常 |
| AC-2.2 | WHEN `keyboardAppearanceConfig`（gradientMode/fluidLightMode，经 JSTextField::SetKeyboardAppearanceConfig）THEN 定制渐变/流体光 | 正常 |

### US-3: 自定义键盘
作为开发者，我希望经 customKeyboard/customKeyboardWithNode 挂载自定义键盘。

| AC编号 | 验收标准 | 类型 |
|--------|----------|------|
| AC-3.1 | WHEN `customKeyboard(builder, options?)`（@since 12）THEN 挂载自定义 builder 键盘 | 正常 |
| AC-3.2 | WHEN `customKeyboardWithNode`（含 KeyboardOptions supportAvoidance）THEN 挂载节点键盘 | 正常 |

### US-4: 自动大写/填充动画/失焦
作为开发者，我希望经 autoCapitalizationMode/enableFillAnimation/blurOnSubmit 控制。

| AC编号 | 验收标准 | 类型 |
|--------|----------|------|
| AC-4.1 | WHEN `autoCapitalizationMode(mode)`（@since 20）THEN 设置自动大写模式 | 正常 |
| AC-4.2 | WHEN `enableFillAnimation(true)`（@since 20）THEN 启用填充动画 | 正常 |
| AC-4.3 | WHEN `blurOnSubmit(true)` THEN 提交时失焦 | 正常 |

## 验收追溯

| AC | 关联规则 | 关联 Task | 验证方式 | 证据 |
|----|----------|-----------|----------|------|
| AC-1.1 | R-1 | TASK-TI-07 | 单测 | text_field_model_ng.h:43 |
| AC-2.1 | R-2 | TASK-TI-07 | 单测 | text_field_model_ng.h:164 |
| AC-2.2 | R-2 | TASK-TI-07 | 单测 | js_textfield.cpp SetKeyboardAppearanceConfig |
| AC-3.1 | R-3 | TASK-TI-07 | 单测 | text_field_model_ng.h:124 |
| AC-3.2 | R-3 | TASK-TI-07 | 单测 | text_field_model_ng.h:125 |
| AC-4.1 | R-4 | TASK-TI-07 | 单测 | text_input.d.ts autoCapitalizationMode @since 20 |
| AC-4.2 | R-4 | TASK-TI-07 | C-API 单测 | native_node.h:4209 |
| AC-4.3 | R-4 | TASK-TI-07 | 单测 | text_field_model_ng.h:344 |

## 规则定义

| 规则ID | 类型 | 触发条件 | 预期行为 | 边界/约束 | 关联AC |
|--------|------|----------|----------|-----------|-------|
| R-1 | 行为 | enterKeyType | 设置回车键样式 | 7 值枚举 | AC-1.1 |
| R-2 | 行为 | keyboardAppearance（@since 15）/keyboardAppearanceConfig | 设置外观/渐变/流体光 | gradientMode/fluidLightMode | AC-2.1,2.2 |
| R-3 | 行为 | customKeyboard/customKeyboardWithNode（@since 12） | 挂载自定义键盘 + supportAvoidance | CustomBuilder/Node | AC-3.1,3.2 |
| R-4 | 行为 | autoCapitalizationMode（@since 20）/enableFillAnimation（@since 20）/blurOnSubmit | 控制大写/动画/失焦 | — | AC-4.1..4.3 |

## 验证映射

| 编号 | 对应规格项 | 验证方式 | 验证重点 |
|------|-----------|----------|----------|
| VM-1 | R-1 回车键 | 单测 | EnterKeyType |
| VM-2 | R-2 外观配置 | 单测 | gradient/fluid |
| VM-3 | R-3 自定义键盘 | 单测 | supportAvoidance |
| VM-4 | R-4 自动大写/动画 | 单测+C-API | @since 20 |

## API 变更分析

### 新增 API

| API 名称 | 开放范围 | 入参概要 | 返回值 | 错误码范围 | 功能描述 | 关联 AC |
|----------|----------|----------|--------|-----------|----------|---------|
| `enterKeyType(value)` | Public | EnterKeyType | this | 无 | 回车键 @since 7–12 | AC-1.1 |
| `keyboardAppearance(appearance)` | Public | KeyboardAppearance | this | 无 | 键盘外观 @since 15 | AC-2.1 |
| `customKeyboard(value, options?)` | Public | CustomBuilder, KeyboardOptions? | this | 无 | 自定义键盘 @since 12 | AC-3.1 |
| `autoCapitalizationMode(mode)` | Public | AutoCapitalizationMode | this | 无 | 自动大写 @since 20 | AC-4.1 |
| `blurOnSubmit(value)` | Public | boolean | this | 无 | 提交失焦 | AC-4.3 |
| C-API `NODE_TEXT_INPUT_ENTER_KEY_TYPE`/`KEYBOARD_APPEARANCE`/`CUSTOM_KEYBOARD`/`ENABLE_FILL_ANIMATION` | System | KNode, ... | void | 无 | C-API 对应 @since 12/15/20 | 全部 |

## 接口规格

### 接口定义

**customKeyboard(value, options?)**

| 属性 | 值 |
|------|-----|
| 函数签名 | `customKeyboard(value: CustomBuilder, options?: KeyboardOptions): TextInputAttribute` |
| 返回值 | `TextInputAttribute` |
| 开放范围 | Public |
| 错误码 | N/A |
| 关联 AC | AC-3.1 |

**参数约束**

| 参数 | 类型 | 必填 | 默认值 | 约束条件 |
|------|------|------|--------|---------|
| value | CustomBuilder | 是 | — | 自定义键盘 builder |
| options | KeyboardOptions | 否 | — | 含 supportAvoidance |

**行为场景**

| # | 触发条件 | 预期行为 | 关联 AC |
|---|----------|----------|---------|
| 1 | 合法 builder | 挂载自定义键盘 | AC-3.1 |

## 兼容性声明
- **已有 API 行为变更:** 否
- **最低支持版本:** enterKeyType @since 7–12；customKeyboard @since 12；keyboardAppearance @since 15；autoCapitalizationMode/enableFillAnimation @since 20
- **API 版本号策略:** 全量 @since 标注

## 架构约束
| 关键约束 | 约束说明 | 影响 AC |
|----------|----------|---------|
| IME 适配耦合 | keyboardAppearance/Config 跨 IME adapter | AC-2.2 |

## 非功能性需求
| 类型 | 指标/阈值 | 验证方式 | 证据 |
|------|-----------|----------|------|
| 性能 | 键盘起拉无卡顿 | 帧率测试 | — |

## 多设备适配声明
无差异。

## 全局特性影响
| 特性 | 适用？ | 结论 | 关联场景 |
|------|--------|------|----------|
| 多窗口 | 是 | 自定义键盘避让窗口 | AC-3.2 |

## Spec 自审清单
- [x] 无占位符
- [x] AC 用 WHEN/THEN
- [x] 范围明确
- [x] 无模糊表述
- [x] AC 与规则交叉一致
- [x] 规则通过 5 项检查

## context-references
```yaml
context-queries:
  - repo: "openharmony/arkui_ace_engine"
    query: "TextInput keyboardAppearance/Config 与 customKeyboard 避让"
```
**关键文档：** `interface/sdk-js/api/@internal/component/ets/text_input.d.ts`
