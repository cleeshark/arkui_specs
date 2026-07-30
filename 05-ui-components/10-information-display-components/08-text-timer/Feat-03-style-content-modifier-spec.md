# 特性规格

> Func-05-10-08-Feat-03 TextTimer 文本样式与 ContentModifier：固化字体样式、主题刷新和自定义内容接管行为。

## 概述

| 属性 | 值 |
|------|----|
| 特性名称 | 文本样式与 ContentModifier |
| 特性编号 | Func-05-10-08-Feat-03 |
| 所属 Epic | 信息展示组件 |
| 优先级 | P1 |
| 目标版本 | API 10-26 |
| SIG 归属 | ArkUI SIG |
| 状态 | Baselined |
| 复杂度 | 标准 |

## 本次变更范围（Delta）

历史规格补齐，记录已有实现，不新增 API 或行为。

## 输入文档

| 文档 | 路径 | 状态 |
|------|------|------|
| Design | `05-ui-components/10-information-display-components/08-text-timer/design.md` | Baselined |
| Model | `frameworks/core/components_ng/pattern/texttimer/text_timer_model_ng.cpp` | 已实现 |
| Pattern | `frameworks/core/components_ng/pattern/texttimer/text_timer_pattern.cpp` | 已实现 |
| Bridge | `frameworks/core/components_ng/pattern/texttimer/bridge/arkts_native_text_timer_bridge.cpp` | 已实现 |

## 用户故事

### US-1: 设置文本样式

**作为** 应用开发者  
**我想要** 设置 TextTimer 的文本样式  
**以便** 让计时文本符合页面视觉设计。

| AC编号 | 验收标准 | 类型 |
|--------|----------|------|
| AC-1.1 | WHEN 设置 fontColor THEN 文本颜色更新 | 正常 |
| AC-1.2 | WHEN 设置 fontSize THEN 字号更新 | 正常 |
| AC-1.3 | WHEN 设置 fontWeight/fontFamily/fontStyle/textShadow THEN 对应文本样式更新 | 正常 |

### US-2: 主题颜色响应

**作为** 应用开发者  
**我想要** TextTimer 在系统配色变化时刷新默认颜色  
**以便** 在深色模式等场景保持文本可读。

| AC编号 | 验收标准 | 类型 |
|--------|----------|------|
| AC-2.1 | WHEN 系统配色变更且用户未设置 fontColor THEN 使用主题色刷新 | 正常 |
| AC-2.2 | WHEN 用户已设置 fontColor THEN 配色变更保留用户颜色 | 正常 |

### US-3: ContentModifier

**作为** 应用开发者  
**我想要** 通过 ContentModifier 自定义 TextTimer 显示内容  
**以便** 用自定义节点替代默认文本呈现。

| AC编号 | 验收标准 | 类型 |
|--------|----------|------|
| AC-3.1 | WHEN 设置 ContentModifier THEN 自定义节点接管显示内容 | 正常 |
| AC-3.2 | WHEN 清除 ContentModifier THEN 恢复默认 Text 显示路径 | 正常 |

## 验收追溯

| AC编号 | 规则编号 | 验证方式 | 证据 |
|--------|----------|----------|------|
| AC-1.1 | R-1 | 源码审阅/单测 | `text_timer_model_ng.cpp`、`text_timer_pattern.cpp` |
| AC-2.1 | R-2 | 源码审阅/单测 | `text_timer_pattern.cpp` |
| AC-3.1 | R-3 | 源码审阅/单测 | `arkts_native_text_timer_bridge.cpp` |

## 规则定义

| R-N | 类型 | 触发条件 | 预期行为 | 边界/约束 | 关联AC |
|-----|------|----------|----------|-----------|--------|
| R-1 | 行为 | 设置文本样式 | 更新内部 Text 或布局属性 | 复用 Text 样式语义 | AC-1.1 |
| R-2 | 行为 | 配色变化 | 未设置颜色跟随主题 | 用户设置值优先 | AC-2.1 |
| R-3 | 行为 | ContentModifier 设置/清除 | 切换自定义和默认内容路径 | 不改变计时状态 | AC-3.1 |

## 验证映射

| VM编号 | 覆盖范围 | 验证方式 | 文件 |
|--------|----------|----------|------|
| VM-1 | 文本样式 | 源码审阅/单测 | `frameworks/core/components_ng/pattern/texttimer/text_timer_model_ng.cpp`、`test/unittest/core/pattern/text_timer/` |
| VM-2 | 主题颜色响应 | 源码审阅/单测 | `frameworks/core/components_ng/pattern/texttimer/text_timer_pattern.cpp` |
| VM-3 | ContentModifier | 源码审阅/单测 | `frameworks/core/components_ng/pattern/texttimer/bridge/arkts_native_text_timer_bridge.cpp` |

## API 变更分析

### 新增 API

无。

### 变更/废弃 API

无。

## 接口规格

| 接口 | 参数 | 返回值 | 行为 | 关联AC |
|------|------|--------|------|--------|
| `.fontColor(value)` | `ResourceColor` | `TextTimerAttribute` | 设置文本颜色 | AC-1.1 |
| `.fontSize(value)` | `Length/Resource` | `TextTimerAttribute` | 设置字号 | AC-1.2 |
| `.fontWeight(value)` | `FontWeight/number/string` | `TextTimerAttribute` | 设置字重 | AC-1.3 |
| `.contentModifier(value)` | `ContentModifier<TextTimerConfiguration>` | `TextTimerAttribute` | 设置自定义内容 | AC-3.1 |

## 兼容性声明

不改变 TextTimer 文本样式和 ContentModifier API。

## 架构约束

- 文本样式遵循 Text 组件基础语义。
- ContentModifier 只改变呈现，不改变计时状态。

## 非功能性需求

| 类型 | 指标/阈值 | 验证方式 |
|------|-----------|----------|
| 可维护性 | 样式属性集中通过 Model/Pattern 同步 | VM-1 |

## 多设备适配声明

无组件级设备差异。

## 全局特性影响

| 特性 | 适用 | 说明 |
|------|------|------|
| 大字体 | 是 | fontSize 影响内部 Text。 |
| 深色模式 | 是 | 未设置颜色跟随主题。 |

## 行为场景（可选，Gherkin）

```gherkin
Scenario: 配色变化保留用户颜色
  Given TextTimer 已设置 fontColor
  When 系统配色变化
  Then TextTimer 保留用户设置颜色
```

## Spec 自审清单

- [x] 特性编号符合 `Func-05-10-08-Feat-03`
- [x] AC 使用 WHEN/THEN 表述
- [x] 验证映射指向源码和测试入口
- [x] 无新增 API

## context-references

- `frameworks/core/components_ng/pattern/texttimer/text_timer_model_ng.cpp`
- `frameworks/core/components_ng/pattern/texttimer/text_timer_pattern.cpp`
- `frameworks/core/components_ng/pattern/texttimer/bridge/arkts_native_text_timer_bridge.cpp`
