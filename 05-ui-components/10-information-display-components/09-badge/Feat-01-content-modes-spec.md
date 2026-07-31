# 特性规格

> Func-05-10-09-Feat-01 Badge 内容模式：固化数字标记、文字标记、圆点标记、maxCount 和可见性决策行为。

## 概述

| 属性 | 值 |
|------|----|
| 特性名称 | 内容模式 |
| 特性编号 | Func-05-10-09-Feat-01 |
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
| Pattern | `frameworks/core/components_ng/pattern/badge/badge_pattern.cpp` | 已实现 |
| Model | `frameworks/core/components_ng/pattern/badge/badge_model_ng.cpp` | 已实现 |
| SDK | `<OH_ROOT>/interface/sdk-js/api/@internal/component/ets/badge.d.ts` | 已发布 |

## 用户故事

### US-1: 数字标记

**作为** 应用开发者  
**我想要** 使用 Badge 显示数字标记  
**以便** 在子组件上提示数量或未读数。

| AC编号 | 验收标准 | 类型 |
|--------|----------|------|
| AC-1.1 | WHEN 设置 `Badge({ count: 5 })` THEN Badge 显示数字 `5` | 正常 |
| AC-1.2 | WHEN count 大于 maxCount THEN Badge 显示上限格式 | 边界 |
| AC-1.3 | WHEN count 小于等于 0 THEN 不显示数字内容 | 边界 |

### US-2: 文字标记

**作为** 应用开发者  
**我想要** 使用 Badge 显示文字标记  
**以便** 在子组件上提示状态或标签文本。

| AC编号 | 验收标准 | 类型 |
|--------|----------|------|
| AC-2.1 | WHEN 设置 `Badge({ value: "NEW" })` THEN Badge 显示文字 `NEW` | 正常 |
| AC-2.2 | WHEN value 为空字符串 THEN Badge 使用安全占位显示路径 | 边界 |

### US-3: 圆点标记

**作为** 应用开发者  
**我想要** 使用 Badge 显示圆点标记  
**以便** 在无需数字或文字时提示状态。

| AC编号 | 验收标准 | 类型 |
|--------|----------|------|
| AC-3.1 | WHEN 只需要状态提示且无数字/文字内容 THEN Badge 可按圆点尺寸展示 | 正常 |
| AC-3.2 | WHEN badgeCircleSize 小于等于 0 THEN Badge 进入零尺寸边界路径 | 边界 |

## 验收追溯

| AC编号 | 规则编号 | 验证方式 | 证据 |
|--------|----------|----------|------|
| AC-1.1 | R-1 | 源码审阅/单测 | `badge_pattern.cpp`、`badge_model_ng.cpp` |
| AC-2.1 | R-2 | 源码审阅/单测 | `badge_pattern.cpp` |
| AC-3.1 | R-3 | 源码审阅/单测 | `badge_pattern.cpp`、`badge_layout_algorithm.cpp` |

## 规则定义

| R-N | 类型 | 触发条件 | 预期行为 | 边界/约束 | 关联AC |
|-----|------|----------|----------|-----------|--------|
| R-1 | 行为 | count 模式 | 显示数字或上限格式 | count <= 0 不显示数字内容 | AC-1.1 |
| R-2 | 行为 | value 模式 | 显示文字内容 | 空字符串走占位路径 | AC-2.1 |
| R-3 | 行为 | 圆点模式 | 使用圆形尺寸展示状态点 | 尺寸 <= 0 进入边界 | AC-3.1 |

## 验证映射

| VM编号 | 覆盖范围 | 验证方式 | 文件 |
|--------|----------|----------|------|
| VM-1 | 数字标记 | 源码审阅/单测 | `frameworks/core/components_ng/pattern/badge/badge_pattern.cpp`、`test/unittest/core/pattern/badge/` |
| VM-2 | 文字标记 | 源码审阅/单测 | `frameworks/core/components_ng/pattern/badge/badge_pattern.cpp` |
| VM-3 | 圆点和零尺寸边界 | 源码审阅/单测 | `frameworks/core/components_ng/pattern/badge/badge_layout_algorithm.cpp` |

## API 变更分析

### 新增 API

无。

### 变更/废弃 API

无。

## 接口规格

| 接口 | 参数 | 返回值 | 行为 | 关联AC |
|------|------|--------|------|--------|
| `Badge(value: BadgeParamWithNumber)` | count/maxCount/style | `BadgeAttribute` | 创建数字标记 | AC-1.1 |
| `Badge(value: BadgeParamWithString)` | value/style | `BadgeAttribute` | 创建文字标记 | AC-2.1 |

## 兼容性声明

不改变 Badge 创建 API。

## 架构约束

- 内容决策由 Pattern 根据 LayoutProperty 中的参数完成。
- Badge 不读取通知数量等外部业务数据。

## 非功能性需求

| 类型 | 指标/阈值 | 验证方式 |
|------|-----------|----------|
| 可靠性 | 空值和越界 count 不崩溃 | VM-1, VM-2 |

## 多设备适配声明

无组件级设备差异。

## 全局特性影响

| 特性 | 适用 | 说明 |
|------|------|------|
| 无障碍 | 是 | 内容会影响无障碍文本。 |

## 行为场景（可选，Gherkin）

```gherkin
Scenario: 数字超过最大值
  Given Badge maxCount 为 99
  When count 为 100
  Then Badge 显示上限格式
```

## Spec 自审清单

- [x] 特性编号符合 `Func-05-10-09-Feat-01`
- [x] AC 使用 WHEN/THEN 表述
- [x] 验证映射指向源码和测试入口
- [x] 无新增 API

## context-references

- `frameworks/core/components_ng/pattern/badge/badge_pattern.cpp`
- `frameworks/core/components_ng/pattern/badge/badge_model_ng.cpp`
- `test/unittest/core/pattern/badge/`
