# 特性规格

> Func-05-10-09-Feat-03 Badge 样式、主题与老年模式：固化颜色、字体、边框、圆形尺寸、外边框、主题刷新和字体缩放适配行为。

## 概述

| 属性 | 值 |
|------|----|
| 特性名称 | 样式、主题与老年模式 |
| 特性编号 | Func-05-10-09-Feat-03 |
| 所属 Epic | 信息展示组件 |
| 优先级 | P1 |
| 目标版本 | API 7-26 |
| SIG 归属 | ArkUI SIG |
| 状态 | Baselined |
| 复杂度 | 标准 |

## 本次变更范围（Delta）

历史规格补齐，记录已有实现，不新增 API 或行为。

## 输入文档

| 文档 | 路径 | 状态 |
|------|------|------|
| Design | `05-ui-components/10-information-display-components/09-badge/design.md` | Baselined |
| Theme | `frameworks/core/components/badge/badge_theme.h` | 已实现 |
| ThemeWrapper | `frameworks/core/components_ng/pattern/badge/badge_theme_wrapper.h` | 已实现 |
| Pattern/Layout | `frameworks/core/components_ng/pattern/badge/` | 已实现 |

## 用户故事

### US-1: 样式定制

**作为** 应用开发者  
**我想要** 自定义 Badge 的颜色、字体、边框和尺寸  
**以便** 让标记样式符合页面视觉设计。

| AC编号 | 验收标准 | 类型 |
|--------|----------|------|
| AC-1.1 | WHEN 设置 badgeColor THEN Badge 背景色使用指定颜色 | 正常 |
| AC-1.2 | WHEN 设置 badgeTextColor THEN Badge 文本色使用指定颜色 | 正常 |
| AC-1.3 | WHEN 设置 border/outerBorder THEN Badge 绘制对应边框 | 正常 |
| AC-1.4 | WHEN 设置 badgeFontSize/fontWeight THEN 内部 Text 使用指定字体样式 | 正常 |

### US-2: 主题刷新保护

**作为** 应用开发者  
**我想要** Badge 在主题变化时刷新未自定义样式  
**以便** 在深色模式等场景保持默认样式可读。

| AC编号 | 验收标准 | 类型 |
|--------|----------|------|
| AC-2.1 | WHEN 主题变化且属性未被用户设置 THEN Badge 使用新主题默认值 | 正常 |
| AC-2.2 | WHEN 属性已被用户设置 THEN 主题变化保留用户设置值 | 正常 |

### US-3: 老年模式适配

**作为** 应用开发者  
**我想要** Badge 在老年模式下适配默认字体和尺寸  
**以便** 提升大字体场景下的可读性。

| AC编号 | 验收标准 | 类型 |
|--------|----------|------|
| AC-3.1 | WHEN fontSizeScale 达到老年模式阈值且用户未设置 fontSize THEN 使用老年模式字号 | 正常 |
| AC-3.2 | WHEN 用户已设置 fontSize THEN 老年模式保留用户字号 | 正常 |

## 验收追溯

| AC编号 | 规则编号 | 验证方式 | 证据 |
|--------|----------|----------|------|
| AC-1.1 | R-1 | 源码审阅/单测 | `badge_model_ng.cpp`、`badge_pattern.cpp` |
| AC-2.1 | R-2 | 源码审阅/单测 | `badge_theme.h`、`badge_theme_wrapper.h` |
| AC-3.1 | R-3 | 源码审阅/单测 | `badge_layout_algorithm.cpp` |

## 规则定义

| R-N | 类型 | 触发条件 | 预期行为 | 边界/约束 | 关联AC |
|-----|------|----------|----------|-----------|--------|
| R-1 | 行为 | 设置样式属性 | 写入 LayoutProperty 并刷新 Text/RenderContext | 用户设置标记置位 | AC-1.1 |
| R-2 | 行为 | 主题变化 | 未设置项跟随主题 | `*Byuser` 标记保护用户值 | AC-2.1 |
| R-3 | 行为 | 字体缩放达到阈值 | 使用老年模式字体/尺寸 | 用户设置值优先 | AC-3.1 |

## 验证映射

| VM编号 | 覆盖范围 | 验证方式 | 文件 |
|--------|----------|----------|------|
| VM-1 | 样式属性 | 源码审阅/单测 | `frameworks/core/components_ng/pattern/badge/badge_model_ng.cpp`、`test/unittest/core/pattern/badge/` |
| VM-2 | 主题更新 | 源码审阅/单测 | `frameworks/core/components/badge/badge_theme.h`、`badge_withtheme_test_ng.cpp` |
| VM-3 | 老年模式 | 源码审阅/单测 | `frameworks/core/components_ng/pattern/badge/badge_layout_algorithm.cpp` |

## API 变更分析

### 新增 API

无。

### 变更/废弃 API

无。

## 接口规格

| 接口 | 参数 | 返回值 | 行为 | 关联AC |
|------|------|--------|------|--------|
| Badge style options | color/textColor/font/border/size | `BadgeAttribute` | 设置 Badge 样式 | AC-1.1 |
| Theme refresh | 无公开参数 | N/A | 刷新未设置主题项 | AC-2.1 |

## 兼容性声明

不改变 Badge 样式 API 和主题默认值读取方式。

## 架构约束

- 用户设置标记必须优先于主题默认刷新。
- 老年模式只影响默认字号/尺寸，不覆盖用户显式设置。

## 非功能性需求

| 类型 | 指标/阈值 | 验证方式 |
|------|-----------|----------|
| 可访问性 | 老年模式下默认文本尺寸可放大 | VM-3 |
| 可靠性 | 主题变化不丢失用户设置 | VM-2 |

## 多设备适配声明

无组件级设备差异；字体缩放由系统配置驱动。

## 全局特性影响

| 特性 | 适用 | 说明 |
|------|------|------|
| 深色模式 | 是 | 主题刷新影响默认颜色。 |
| 大字体 | 是 | 老年模式影响默认字号和尺寸。 |

## 行为场景（可选，Gherkin）

```gherkin
Scenario: 主题变化保留用户颜色
  Given Badge 已设置 badgeColor
  When 系统主题变化
  Then Badge 保留用户设置的 badgeColor
```

## Spec 自审清单

- [x] 特性编号符合 `Func-05-10-09-Feat-03`
- [x] AC 使用 WHEN/THEN 表述
- [x] 验证映射指向源码和测试入口
- [x] 无新增 API

## context-references

- `frameworks/core/components_ng/pattern/badge/badge_model_ng.cpp`
- `frameworks/core/components_ng/pattern/badge/badge_layout_algorithm.cpp`
- `frameworks/core/components/badge/badge_theme.h`
