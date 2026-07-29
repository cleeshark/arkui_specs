# 特性规格

> Func-05-10-08-Feat-04 TextTimer 可见区优化与组件化：固化可见区节点管理、dynamic/static modifier 和动态模块加载路径。

## 概述

| 属性 | 值 |
|------|----|
| 特性名称 | 可见区优化与组件化 |
| 特性编号 | Func-05-10-08-Feat-04 |
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
| Design | `05-ui-components/10-information-display-components/08-text-timer/design.md` | Baselined |
| Pattern | `frameworks/core/components_ng/pattern/texttimer/text_timer_pattern.cpp` | 已实现 |
| Bridge | `frameworks/core/components_ng/pattern/texttimer/bridge/` | 已实现 |
| BUILD | `frameworks/core/components_ng/pattern/texttimer/BUILD.gn` | 已实现 |

## 用户故事

### US-1: 可见区优化

**作为** 应用开发者  
**我想要** TextTimer 在不可见时减少默认内容刷新  
**以便** 降低不可见场景的刷新开销。

| AC编号 | 验收标准 | 类型 |
|--------|----------|------|
| AC-1.1 | WHEN TextTimer 离开可见区域 THEN 默认内容更新停止或节点从渲染路径移除 | 正常 |
| AC-1.2 | WHEN TextTimer 重新进入可见区域 THEN 默认内容恢复显示并继续更新 | 正常 |

### US-2: 组件化路径

**作为** 框架维护者  
**我想要** TextTimer 通过组件化 bridge 和 modifier 路径解析 API  
**以便** 保持动态、静态和按需加载管线一致可维护。

| AC编号 | 验收标准 | 类型 |
|--------|----------|------|
| AC-2.1 | WHEN ArkTS 动态 API 设置属性 THEN 通过 TextTimer bridge/dynamic modifier 写入组件状态 | 正常 |
| AC-2.2 | WHEN ArkTS 静态 API 设置属性 THEN 通过 static modifier 写入 FrameNode | 正常 |
| AC-2.3 | WHEN 组件按需加载 THEN DynamicModule 暴露 TextTimer 创建入口 | 正常 |

## 验收追溯

| AC编号 | 规则编号 | 验证方式 | 证据 |
|--------|----------|----------|------|
| AC-1.1 | R-1 | 源码审阅/单测 | `text_timer_pattern.cpp` |
| AC-2.1 | R-2 | 源码审阅 | `frameworks/core/components_ng/pattern/texttimer/bridge/` |

## 规则定义

| R-N | 类型 | 触发条件 | 预期行为 | 边界/约束 | 关联AC |
|-----|------|----------|----------|-----------|--------|
| R-1 | 性能 | 可见区变化 | 暂停/恢复默认内容更新 | 不改变计时配置 | AC-1.1 |
| R-2 | 架构 | API 属性设置 | 通过组件化 bridge/modifier 路径落状态 | 保持 dynamic/static 差异 | AC-2.1 |

## 验证映射

| VM编号 | 覆盖范围 | 验证方式 | 文件 |
|--------|----------|----------|------|
| VM-1 | 可见区行为 | 源码审阅/单测 | `frameworks/core/components_ng/pattern/texttimer/text_timer_pattern.cpp`、`test/unittest/core/pattern/text_timer/` |
| VM-2 | 组件化路径 | 源码审阅 | `frameworks/core/components_ng/pattern/texttimer/bridge/`、`frameworks/core/components_ng/pattern/texttimer/BUILD.gn` |

## API 变更分析

### 新增 API

无。

### 变更/废弃 API

无。

## 接口规格

| 接口 | 参数 | 返回值 | 行为 | 关联AC |
|------|------|--------|------|--------|
| DynamicModule 创建入口 | Component name | modifier/model 指针 | 支持组件化加载 | AC-2.3 |

## 兼容性声明

保持 dynamic/static modifier 解析路径兼容。

## 架构约束

- 组件化路径不得绕过 Model/Pattern 状态分层。
- 可见区优化不得改变公开计时 API 语义。

## 非功能性需求

| 类型 | 指标/阈值 | 验证方式 |
|------|-----------|----------|
| 性能 | 不可见时减少默认内容刷新 | VM-1 |
| 可维护性 | API 解析集中在 bridge/modifier | VM-2 |

## 多设备适配声明

无组件级设备差异。

## 全局特性影响

| 特性 | 适用 | 说明 |
|------|------|------|
| 多窗口/分屏 | 是 | 可见区变化影响更新路径。 |

## 行为场景（可选，Gherkin）

```gherkin
Scenario: 可见区恢复后继续显示
  Given TextTimer 离开可见区域
  When TextTimer 重新进入可见区域
  Then 默认内容恢复显示并继续更新
```

## Spec 自审清单

- [x] 特性编号符合 `Func-05-10-08-Feat-04`
- [x] AC 使用 WHEN/THEN 表述
- [x] 验证映射指向源码和测试入口
- [x] 无新增 API

## context-references

- `frameworks/core/components_ng/pattern/texttimer/text_timer_pattern.cpp`
- `frameworks/core/components_ng/pattern/texttimer/bridge/`
- `frameworks/core/components_ng/pattern/texttimer/BUILD.gn`
