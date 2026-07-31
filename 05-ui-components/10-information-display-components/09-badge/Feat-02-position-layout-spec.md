# 特性规格

> Func-05-10-09-Feat-02 Badge 位置与布局：固化 BadgePosition、X/Y 坐标、RTL、自动避让、尺寸测量和内部 Text 子节点布局行为。

## 概述

| 属性 | 值 |
|------|----|
| 特性名称 | 位置与布局 |
| 特性编号 | Func-05-10-09-Feat-02 |
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
| LayoutAlgorithm | `frameworks/core/components_ng/pattern/badge/badge_layout_algorithm.cpp` | 已实现 |
| LayoutProperty | `frameworks/core/components_ng/pattern/badge/badge_layout_property.h` | 已实现 |

## 用户故事

### US-1: 预设位置

**作为** 应用开发者  
**我想要** 使用 BadgePosition 设置 Badge 预设位置  
**以便** 快速将标记放到子组件常见位置。

| AC编号 | 验收标准 | 类型 |
|--------|----------|------|
| AC-1.1 | WHEN position 为 RIGHT_TOP THEN Badge 位于子组件右上角 | 正常 |
| AC-1.2 | WHEN position 为 RIGHT THEN Badge 位于右侧垂直居中 | 正常 |
| AC-1.3 | WHEN position 为 LEFT THEN Badge 位于左侧垂直居中 | 正常 |

### US-2: 坐标定位

**作为** 应用开发者  
**我想要** 使用 positionX 和 positionY 精确控制 Badge 坐标  
**以便** 按页面布局对标记位置做细粒度调整。

| AC编号 | 验收标准 | 类型 |
|--------|----------|------|
| AC-2.1 | WHEN 设置 positionX/positionY THEN Badge 使用坐标定位 | 正常 |
| AC-2.2 | WHEN 同时存在坐标和枚举位置 THEN 坐标路径优先 | 正常 |

### US-3: RTL 和自动避让

**作为** 应用开发者  
**我想要** Badge 在 RTL 和自动避让场景下正确计算位置  
**以便** 在多语言和复杂布局中避免位置错误。

| AC编号 | 验收标准 | 类型 |
|--------|----------|------|
| AC-3.1 | WHEN 布局方向为 RTL THEN 左右位置按 RTL 规则调整 | 正常 |
| AC-3.2 | WHEN enableAutoAvoidance 为 true THEN Badge 偏移进行自动避让 | 正常 |

## 验收追溯

| AC编号 | 规则编号 | 验证方式 | 证据 |
|--------|----------|----------|------|
| AC-1.1 | R-1 | 源码审阅/单测 | `badge_layout_algorithm.cpp` |
| AC-2.1 | R-2 | 源码审阅/单测 | `badge_layout_algorithm.cpp` |
| AC-3.1 | R-3 | 源码审阅/单测 | `badge_layout_algorithm.cpp` |

## 规则定义

| R-N | 类型 | 触发条件 | 预期行为 | 边界/约束 | 关联AC |
|-----|------|----------|----------|-----------|--------|
| R-1 | 行为 | BadgePosition | 按预设位置计算偏移 | RIGHT_TOP 受 RTL 影响 | AC-1.1 |
| R-2 | 行为 | positionX/Y | 使用坐标定位 | 坐标优先于枚举 | AC-2.1 |
| R-3 | 行为 | RTL/自动避让 | 调整偏移避免遮挡 | 依赖布局方向和父尺寸 | AC-3.1 |

## 验证映射

| VM编号 | 覆盖范围 | 验证方式 | 文件 |
|--------|----------|----------|------|
| VM-1 | 预设位置 | 源码审阅/单测 | `frameworks/core/components_ng/pattern/badge/badge_layout_algorithm.cpp`、`test/unittest/core/pattern/badge/` |
| VM-2 | X/Y 坐标 | 源码审阅/单测 | `frameworks/core/components_ng/pattern/badge/badge_layout_property.h` |
| VM-3 | RTL 和自动避让 | 源码审阅/单测 | `frameworks/core/components_ng/pattern/badge/badge_layout_algorithm.cpp` |

## API 变更分析

### 新增 API

无。

### 变更/废弃 API

无。

## 接口规格

| 接口 | 参数 | 返回值 | 行为 | 关联AC |
|------|------|--------|------|--------|
| Badge position options | position/positionX/positionY | `BadgeAttribute` | 设置标记位置 | AC-1.1, AC-2.1 |
| `enableAutoAvoidance` | boolean | `BadgeAttribute` | 设置自动避让 | AC-3.2 |

## 兼容性声明

不改变 Badge 位置相关 API。

## 架构约束

- 位置计算集中在 LayoutAlgorithm。
- 坐标定位和枚举定位不能同时产生冲突布局。

## 非功能性需求

| 类型 | 指标/阈值 | 验证方式 |
|------|-----------|----------|
| 可靠性 | RTL 和坐标组合不产生崩溃 | VM-3 |

## 多设备适配声明

无组件级设备差异；父组件尺寸变化会触发布局重算。

## 全局特性影响

| 特性 | 适用 | 说明 |
|------|------|------|
| RTL | 是 | 左右位置受布局方向影响。 |
| 多窗口 | 是 | 尺寸变化触发布局重算。 |

## 行为场景（可选，Gherkin）

```gherkin
Scenario: 坐标定位优先
  Given Badge 同时设置 position 和 positionX
  When 执行布局
  Then Badge 使用 positionX/positionY 坐标定位
```

## Spec 自审清单

- [x] 特性编号符合 `Func-05-10-09-Feat-02`
- [x] AC 使用 WHEN/THEN 表述
- [x] 验证映射指向源码和测试入口
- [x] 无新增 API

## context-references

- `frameworks/core/components_ng/pattern/badge/badge_layout_algorithm.cpp`
- `frameworks/core/components_ng/pattern/badge/badge_layout_property.h`
- `test/unittest/core/pattern/badge/`
