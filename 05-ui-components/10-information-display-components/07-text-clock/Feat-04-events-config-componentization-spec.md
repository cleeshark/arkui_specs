# 特性规格

> Func-05-10-07-Feat-04 TextClock 事件、配置变更与组件化：固化 onDateChange、语言/颜色配置变化、多线程挂载和 dynamic module/Modifier 解析路径。

## 概述

| 属性 | 值 |
|------|----|
| 特性名称 | 事件、配置变更与组件化 |
| 特性编号 | Func-05-10-07-Feat-04 |
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
| Design | `05-ui-components/10-information-display-components/07-text-clock/design.md` | Baselined |
| EventHub | `frameworks/core/components_ng/pattern/text_clock/text_clock_event_hub.h` | 已实现 |
| Bridge | `frameworks/core/components_ng/pattern/text_clock/bridge/` | 已实现 |
| BUILD | `frameworks/core/components_ng/pattern/text_clock/BUILD.gn` | 已实现 |

## 用户故事

### US-1: 时间变化事件

**作为** 应用开发者  
**我想要** 监听 TextClock 显示时间变化  
**以便** 在时间变化时执行业务回调。

| AC编号 | 验收标准 | 类型 |
|--------|----------|------|
| AC-1.1 | WHEN 时间文本变化 THEN 触发 onDateChange 回调 | 正常 |
| AC-1.2 | WHEN 时间文本未变化 THEN 不重复触发 onDateChange | 边界 |

### US-2: 系统配置变化

**作为** 应用开发者  
**我想要** TextClock 响应语言和颜色等系统配置变化  
**以便** 配置变化后自动刷新时间文本和默认样式。

| AC编号 | 验收标准 | 类型 |
|--------|----------|------|
| AC-2.1 | WHEN 系统语言变化 THEN TextClock 重新格式化显示文本 | 正常 |
| AC-2.2 | WHEN 系统颜色模式变化且颜色未被用户设置 THEN TextClock 更新主题颜色 | 正常 |

### US-3: 组件化解析路径

**作为** 框架维护者  
**我想要** TextClock 通过组件化 bridge 和 modifier 路径解析 API  
**以便** 保持动态、静态和按需加载管线一致可维护。

| AC编号 | 验收标准 | 类型 |
|--------|----------|------|
| AC-3.1 | WHEN ArkTS 动态 API 设置属性 THEN 通过 TextClock bridge/dynamic modifier 写入组件状态 | 正常 |
| AC-3.2 | WHEN ArkTS 静态 API 设置属性 THEN 通过 static modifier 写入 FrameNode | 正常 |
| AC-3.3 | WHEN 组件按需加载 THEN DynamicModule 暴露 TextClock 创建入口 | 正常 |

## 验收追溯

| AC编号 | 规则编号 | 验证方式 | 证据 |
|--------|----------|----------|------|
| AC-1.1 | R-1 | 源码审阅/单测 | `text_clock_event_hub.h`、`text_clock_pattern.cpp` |
| AC-2.1 | R-2 | 源码审阅/单测 | `text_clock_pattern.cpp` |
| AC-3.1 | R-3 | 源码审阅 | `frameworks/core/components_ng/pattern/text_clock/bridge/` |

## 规则定义

| R-N | 类型 | 触发条件 | 预期行为 | 边界/约束 | 关联AC |
|-----|------|----------|----------|-----------|--------|
| R-1 | 行为 | 时间文本变化 | 触发 onDateChange | 去重避免重复触发 | AC-1.1 |
| R-2 | 行为 | 语言/颜色配置变化 | 重新格式化或刷新主题色 | 用户设置值优先 | AC-2.1 |
| R-3 | 架构 | API 属性设置 | 通过组件化 bridge/modifier 路径落状态 | 保持 dynamic/static 差异 | AC-3.1 |

## 验证映射

| VM编号 | 覆盖范围 | 验证方式 | 文件 |
|--------|----------|----------|------|
| VM-1 | onDateChange | 源码审阅/单测 | `frameworks/core/components_ng/pattern/text_clock/text_clock_event_hub.h`、`test/unittest/core/pattern/text_clock/` |
| VM-2 | 配置变化响应 | 源码审阅/单测 | `frameworks/core/components_ng/pattern/text_clock/text_clock_pattern.cpp` |
| VM-3 | 组件化路径 | 源码审阅 | `frameworks/core/components_ng/pattern/text_clock/bridge/`、`frameworks/core/components_ng/pattern/text_clock/BUILD.gn` |

## API 变更分析

### 新增 API

无。

### 变更/废弃 API

无。

## 接口规格

| 接口 | 参数 | 返回值 | 行为 | 关联AC |
|------|------|--------|------|--------|
| `.onDateChange(callback)` | function | `TextClockAttribute` | 注册时间变化回调 | AC-1.1 |
| DynamicModule 创建入口 | Component name | modifier/model 指针 | 支持组件化加载 | AC-3.3 |

## 兼容性声明

保持 dynamic/static/C API modifier 解析路径兼容，不新增公开能力。

## 架构约束

- EventHub 仅保存和分发事件，不生成时间文本。
- 组件化路径不得绕过 Model/Pattern 状态分层。

## 非功能性需求

| 类型 | 指标/阈值 | 验证方式 |
|------|-----------|----------|
| 可维护性 | API 解析路径集中在 bridge/modifier | VM-3 |
| 可靠性 | 配置变化后刷新不重复创建无效节点 | VM-2 |

## 多设备适配声明

无组件级设备差异。

## 全局特性影响

| 特性 | 适用 | 说明 |
|------|------|------|
| 深色模式 | 是 | 未设置颜色跟随主题。 |
| 本地化 | 是 | 语言变化影响格式化文本。 |

## 行为场景（可选，Gherkin）

```gherkin
Scenario: 时间变化触发事件
  Given 已注册 onDateChange
  When TextClock 显示文本发生变化
  Then 回调被触发一次
```

## Spec 自审清单

- [x] 特性编号符合 `Func-05-10-07-Feat-04`
- [x] AC 使用 WHEN/THEN 表述
- [x] 验证映射指向源码和测试入口
- [x] 无新增 API

## context-references

- `frameworks/core/components_ng/pattern/text_clock/text_clock_event_hub.h`
- `frameworks/core/components_ng/pattern/text_clock/text_clock_pattern.cpp`
- `frameworks/core/components_ng/pattern/text_clock/bridge/`
