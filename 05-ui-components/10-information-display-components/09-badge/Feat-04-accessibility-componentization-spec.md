# 特性规格

> Func-05-10-09-Feat-04 Badge 无障碍与组件化：固化无障碍文本、内部 Text 子节点、dynamic/static/custom modifier 和动态模块加载路径。

## 概述

| 属性 | 值 |
|------|----|
| 特性名称 | 无障碍与组件化 |
| 特性编号 | Func-05-10-09-Feat-04 |
| 所属 Epic | 信息展示组件 |
| 优先级 | P2 |
| 目标版本 | API 10-26 |
| SIG 归属 | ArkUI SIG |
| 状态 | Baselined |
| 复杂度 | 标准 |

## 本次变更范围（Delta）

历史规格补齐，记录已有实现，不新增 API 或行为。

## 输入文档

| 文档 | 路径 | 状态 |
|------|------|------|
| Design | `05-ui-components/10-information-display-components/09-badge/design.md` | Baselined |
| Accessibility | `frameworks/core/components_ng/pattern/badge/badge_accessibility_property.cpp` | 已实现 |
| Bridge | `frameworks/core/components_ng/pattern/badge/bridge/` | 已实现 |
| BUILD | `frameworks/core/components_ng/pattern/badge/BUILD.gn` | 已实现 |

## 用户故事

### US-1: 无障碍文本

**作为** 无障碍用户  
**我想要** 通过无障碍服务读取 Badge 内容  
**以便** 理解数字或文字标记传达的状态。

| AC编号 | 验收标准 | 类型 |
|--------|----------|------|
| AC-1.1 | WHEN Badge 设置 count THEN 无障碍文本返回 count 对应字符串 | 正常 |
| AC-1.2 | WHEN Badge 设置 value THEN 无障碍文本返回 value | 正常 |
| AC-1.3 | WHEN Badge 不显示内容 THEN 无障碍文本为空或走安全默认路径 | 边界 |

### US-2: 组件化解析路径

**作为** 框架维护者  
**我想要** Badge 通过组件化 bridge 和 modifier 路径解析 API  
**以便** 保持动态、静态、自定义 modifier 和按需加载管线一致可维护。

| AC编号 | 验收标准 | 类型 |
|--------|----------|------|
| AC-2.1 | WHEN ArkTS 动态 API 创建 Badge THEN 通过 BadgeBridge 解析参数 | 正常 |
| AC-2.2 | WHEN ArkTS 静态 API 设置 Badge 属性 THEN 通过 static modifier 写入 FrameNode | 正常 |
| AC-2.3 | WHEN 组件按需加载 THEN DynamicModule 暴露 Badge 创建入口 | 正常 |
| AC-2.4 | WHEN 使用自定义 modifier THEN custom modifier 路径可被 DynamicModule 返回 | 正常 |

## 验收追溯

| AC编号 | 规则编号 | 验证方式 | 证据 |
|--------|----------|----------|------|
| AC-1.1 | R-1 | 源码审阅/单测 | `badge_accessibility_property.cpp` |
| AC-2.1 | R-2 | 源码审阅 | `frameworks/core/components_ng/pattern/badge/bridge/` |

## 规则定义

| R-N | 类型 | 触发条件 | 预期行为 | 边界/约束 | 关联AC |
|-----|------|----------|----------|-----------|--------|
| R-1 | 行为 | 无障碍读取文本 | 返回 count/value 对应内容 | 内容为空走安全路径 | AC-1.1 |
| R-2 | 架构 | API 属性设置 | 通过组件化 bridge/modifier 路径落状态 | 保持 dynamic/static/custom 差异 | AC-2.1 |

## 验证映射

| VM编号 | 覆盖范围 | 验证方式 | 文件 |
|--------|----------|----------|------|
| VM-1 | 无障碍文本 | 源码审阅/单测 | `frameworks/core/components_ng/pattern/badge/badge_accessibility_property.cpp`、`test/unittest/core/pattern/badge/` |
| VM-2 | 组件化路径 | 源码审阅 | `frameworks/core/components_ng/pattern/badge/bridge/`、`frameworks/core/components_ng/pattern/badge/BUILD.gn` |

## API 变更分析

### 新增 API

无。

### 变更/废弃 API

无。

## 接口规格

| 接口 | 参数 | 返回值 | 行为 | 关联AC |
|------|------|--------|------|--------|
| Accessibility GetText | 无公开参数 | string | 返回 Badge 内容文本 | AC-1.1 |
| DynamicModule 创建入口 | Component name | modifier/model 指针 | 支持组件化加载 | AC-2.3 |

## 兼容性声明

保持 Badge dynamic/static/custom modifier 解析路径兼容。

## 架构约束

- 无障碍文本来源必须与可见内容保持一致。
- 组件化路径不得绕过 Model/Pattern 状态分层。

## 非功能性需求

| 类型 | 指标/阈值 | 验证方式 |
|------|-----------|----------|
| 可访问性 | count/value 可被无障碍读取 | VM-1 |
| 可维护性 | API 解析集中在 bridge/modifier | VM-2 |

## 多设备适配声明

无组件级设备差异。

## 全局特性影响

| 特性 | 适用 | 说明 |
|------|------|------|
| 无障碍 | 是 | 本 Feat 覆盖无障碍文本。 |

## 行为场景（可选，Gherkin）

```gherkin
Scenario: 数字标记可被无障碍读取
  Given Badge count 为 5
  When 无障碍服务读取文本
  Then 返回字符串 5
```

## Spec 自审清单

- [x] 特性编号符合 `Func-05-10-09-Feat-04`
- [x] AC 使用 WHEN/THEN 表述
- [x] 验证映射指向源码和测试入口
- [x] 无新增 API

## context-references

- `frameworks/core/components_ng/pattern/badge/badge_accessibility_property.cpp`
- `frameworks/core/components_ng/pattern/badge/bridge/`
- `frameworks/core/components_ng/pattern/badge/BUILD.gn`
