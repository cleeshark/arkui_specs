# 特性规格

> Func-05-10-07-Feat-03 TextClock 文本样式与 ContentModifier：固化 fontColor/fontSize/fontWeight/fontFamily/fontStyle/textShadow/fontFeature 等文本样式同步，以及自定义内容接管行为。

## 概述

| 属性 | 值 |
|------|----|
| 特性名称 | 文本样式与 ContentModifier |
| 特性编号 | Func-05-10-07-Feat-03 |
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
| Design | `05-ui-components/10-information-display-components/07-text-clock/design.md` | Baselined |
| Model | `frameworks/core/components_ng/pattern/text_clock/text_clock_model_ng.cpp` | 已实现 |
| Pattern | `frameworks/core/components_ng/pattern/text_clock/text_clock_pattern.cpp` | 已实现 |
| Bridge | `frameworks/core/components_ng/pattern/text_clock/bridge/arkts_native_text_clock_bridge.cpp` | 已实现 |

## 用户故事

### US-1: 设置文本样式

**作为** 应用开发者  
**我想要** 设置 TextClock 的字体颜色、字号、字重、字体族和扩展文本样式  
**以便** 让时钟文本符合页面视觉设计。

| AC编号 | 验收标准 | 类型 |
|--------|----------|------|
| AC-1.1 | WHEN 设置 fontColor THEN 内部 Text 的文本颜色更新 | 正常 |
| AC-1.2 | WHEN 设置 fontSize THEN 内部 Text 的字号更新 | 正常 |
| AC-1.3 | WHEN 设置 fontWeight/fontFamily/fontStyle THEN 内部 Text 的对应文本样式更新 | 正常 |
| AC-1.4 | WHEN 设置 textShadow/fontFeature THEN 内部 Text 的扩展文本样式更新 | 正常 |

### US-2: 资源对象刷新

**作为** 应用开发者  
**我想要** 让 TextClock 的资源对象随配置变化刷新  
**以便** 在资源、语言或主题变化后保持显示正确。

| AC编号 | 验收标准 | 类型 |
|--------|----------|------|
| AC-2.1 | WHEN fontColor/fontSize/fontFamily/fontWeight/format 资源变化 THEN TextClock 重新解析并刷新 | 正常 |
| AC-2.2 | WHEN 资源解析失败 THEN 保留默认或已有安全值 | 边界 |

### US-3: ContentModifier 自定义内容

**作为** 应用开发者  
**我想要** 通过 ContentModifier 自定义 TextClock 显示内容  
**以便** 用自定义节点替代默认文本呈现。

| AC编号 | 验收标准 | 类型 |
|--------|----------|------|
| AC-3.1 | WHEN 设置 ContentModifier THEN TextClock 创建或更新自定义内容节点 | 正常 |
| AC-3.2 | WHEN ContentModifier 生效 THEN 默认 Text 显示内容不再作为最终视觉输出 | 正常 |
| AC-3.3 | WHEN 清除 ContentModifier THEN 恢复默认 Text 内容显示路径 | 正常 |

## 验收追溯

| AC编号 | 规则编号 | 验证方式 | 证据 |
|--------|----------|----------|------|
| AC-1.1 | R-1 | 源码审阅/单测 | `text_clock_model_ng.cpp`、`text_clock_pattern.cpp` |
| AC-2.1 | R-2 | 源码审阅/单测 | `text_clock_layout_property.h`、`text_clock_pattern.cpp` |
| AC-3.1 | R-3 | 源码审阅/单测 | `arkts_native_text_clock_bridge.cpp`、`text_clock_pattern.cpp` |

## 规则定义

| R-N | 类型 | 触发条件 | 预期行为 | 边界/约束 | 关联AC |
|-----|------|----------|----------|-----------|--------|
| R-1 | 行为 | 设置文本样式属性 | 属性同步到内部 Text 子节点 | 复用 Text 样式语义 | AC-1.1 |
| R-2 | 行为 | 资源对象变化 | 重新解析资源并刷新显示 | 失败时不崩溃 | AC-2.1 |
| R-3 | 行为 | 设置 ContentModifier | 自定义节点接管视觉内容 | 清除后恢复默认路径 | AC-3.1 |

## 验证映射

| VM编号 | 覆盖范围 | 验证方式 | 文件 |
|--------|----------|----------|------|
| VM-1 | 文本样式同步 | 源码审阅/单测 | `frameworks/core/components_ng/pattern/text_clock/text_clock_model_ng.cpp`、`test/unittest/core/pattern/text_clock/` |
| VM-2 | 资源对象刷新 | 源码审阅/单测 | `frameworks/core/components_ng/pattern/text_clock/text_clock_layout_property.h` |
| VM-3 | ContentModifier | 源码审阅/单测 | `frameworks/core/components_ng/pattern/text_clock/bridge/arkts_native_text_clock_bridge.cpp`、`frameworks/core/components_ng/pattern/text_clock/text_clock_pattern.cpp` |

## API 变更分析

### 新增 API

无。

### 变更/废弃 API

无。

## 接口规格

| 接口 | 参数 | 返回值 | 行为 | 关联AC |
|------|------|--------|------|--------|
| `.fontColor(value)` | `ResourceColor` | `TextClockAttribute` | 设置文本颜色 | AC-1.1 |
| `.fontSize(value)` | `Length/Resource` | `TextClockAttribute` | 设置字号 | AC-1.2 |
| `.fontWeight(value)` | `FontWeight/number/string` | `TextClockAttribute` | 设置字重 | AC-1.3 |
| `.fontFamily(value)` | `string/Resource` | `TextClockAttribute` | 设置字体族 | AC-1.3 |
| `.contentModifier(value)` | `ContentModifier<TextClockConfiguration>` | `TextClockAttribute` | 设置自定义内容 | AC-3.1 |

## 兼容性声明

不改变 TextClock 文本样式 API；默认 Text 与 ContentModifier 的现有兼容行为保持不变。

## 架构约束

- TextClock 文本样式以 Text 组件属性语义为基础。
- ContentModifier 不改变计时状态，只改变内容呈现方式。

## 非功能性需求

| 类型 | 指标/阈值 | 验证方式 |
|------|-----------|----------|
| 可维护性 | 文本样式统一通过 Model/LayoutProperty 同步 | VM-1 |
| 可靠性 | 资源解析失败不崩溃 | VM-2 |

## 多设备适配声明

无组件级设备差异；字体缩放和资源由公共 Text/Theme 机制处理。

## 全局特性影响

| 特性 | 适用 | 说明 |
|------|------|------|
| 大字体 | 是 | fontSize 和资源对象影响内部 Text。 |
| 深色模式 | 是 | 未设置颜色时可跟随主题更新。 |

## 行为场景（可选，Gherkin）

```gherkin
Scenario: 设置 ContentModifier 后自定义显示
  Given TextClock 已创建
  When 设置 contentModifier
  Then 自定义节点接管显示内容
```

## Spec 自审清单

- [x] 特性编号符合 `Func-05-10-07-Feat-03`
- [x] AC 使用 WHEN/THEN 表述
- [x] 验证映射指向源码和测试入口
- [x] 无新增 API

## context-references

- `frameworks/core/components_ng/pattern/text_clock/text_clock_model_ng.cpp`
- `frameworks/core/components_ng/pattern/text_clock/text_clock_pattern.cpp`
- `frameworks/core/components_ng/pattern/text_clock/bridge/arkts_native_text_clock_bridge.cpp`
