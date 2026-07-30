# 特性规格

> Func-05-10-07-Feat-02 TextClock 控制器与更新调度：固化 start/stop、延迟任务、可见区暂停恢复和分钟级更新优化行为。

## 概述

| 属性 | 值 |
|------|----|
| 特性名称 | 控制器与更新调度 |
| 特性编号 | Func-05-10-07-Feat-02 |
| 所属 Epic | 信息展示组件 |
| 优先级 | P1 |
| 目标版本 | API 8-26 |
| SIG 归属 | ArkUI SIG |
| 状态 | Baselined |
| 复杂度 | 标准 |

## 本次变更范围（Delta）

历史规格补齐，记录已有实现，不新增 API 或行为。

## 输入文档

| 文档 | 路径 | 状态 |
|------|------|------|
| Design | `05-ui-components/10-information-display-components/07-text-clock/design.md` | Baselined |
| Pattern | `frameworks/core/components_ng/pattern/text_clock/text_clock_pattern.cpp` | 已实现 |
| Controller | `frameworks/core/components/text_clock/text_clock_controller.h` | 已实现 |

## 用户故事

### US-1: 控制器启动和停止

**作为** 应用开发者  
**我想要** 通过 TextClock controller 控制时钟启动和停止  
**以便** 按页面生命周期或业务状态控制时间刷新。

| AC编号 | 验收标准 | 类型 |
|--------|----------|------|
| AC-1.1 | WHEN 调用 controller.start() THEN TextClock 恢复时间更新 | 正常 |
| AC-1.2 | WHEN 调用 controller.stop() THEN TextClock 停止时间更新 | 正常 |
| AC-1.3 | WHEN controller 未绑定 Pattern THEN start/stop 不产生崩溃 | 边界 |

### US-2: 可见区优化

**作为** 应用开发者  
**我想要** TextClock 在不可见时停止无效刷新  
**以便** 降低不可见场景的刷新开销。

| AC编号 | 验收标准 | 类型 |
|--------|----------|------|
| AC-2.1 | WHEN 组件移出可见区域 THEN 取消延迟任务并停止刷新 | 正常 |
| AC-2.2 | WHEN 组件重新进入可见区域 THEN 重新请求下一次时间更新 | 正常 |

### US-3: 分钟级更新优化

**作为** 应用开发者  
**我想要** TextClock 在分钟级格式下减少秒级更新  
**以便** 在不影响显示结果的前提下降低刷新频率。

| AC编号 | 验收标准 | 类型 |
|--------|----------|------|
| AC-3.1 | WHEN format 不包含秒或毫秒且未启用 ContentModifier THEN 下一次更新对齐到分钟 | 正常 |
| AC-3.2 | WHEN format 包含秒或毫秒 THEN 以秒级粒度更新 | 正常 |

## 验收追溯

| AC编号 | 规则编号 | 验证方式 | 证据 |
|--------|----------|----------|------|
| AC-1.1 | R-1 | 源码审阅/单测 | `text_clock_controller.h`、`text_clock_pattern.cpp` |
| AC-2.1 | R-2 | 源码审阅/单测 | `text_clock_pattern.cpp` |
| AC-3.1 | R-3 | 源码审阅/单测 | `text_clock_pattern.cpp` |

## 规则定义

| R-N | 类型 | 触发条件 | 预期行为 | 边界/约束 | 关联AC |
|-----|------|----------|----------|-----------|--------|
| R-1 | 行为 | controller start/stop | 更新 Pattern 启停状态 | controller 弱绑定 Pattern | AC-1.1 |
| R-2 | 性能 | 可见区变化 | 不可见时取消任务，可见时恢复 | 只影响刷新，不改变时间值 | AC-2.1 |
| R-3 | 性能 | format 粒度变化 | 选择秒级或分钟级更新 | ContentModifier 场景保持自定义刷新边界 | AC-3.1 |

## 验证映射

| VM编号 | 覆盖范围 | 验证方式 | 文件 |
|--------|----------|----------|------|
| VM-1 | 控制器启停 | 源码审阅/单测 | `frameworks/core/components/text_clock/text_clock_controller.h`、`test/unittest/core/pattern/text_clock/` |
| VM-2 | 可见区暂停恢复 | 源码审阅/单测 | `frameworks/core/components_ng/pattern/text_clock/text_clock_pattern.cpp` |
| VM-3 | 更新粒度选择 | 源码审阅/单测 | `frameworks/core/components_ng/pattern/text_clock/text_clock_pattern.cpp` |

## API 变更分析

### 新增 API

无。

### 变更/废弃 API

无。

## 接口规格

| 接口 | 参数 | 返回值 | 行为 | 关联AC |
|------|------|--------|------|--------|
| `TextClockController.start()` | 无 | void | 启动时钟更新 | AC-1.1 |
| `TextClockController.stop()` | 无 | void | 停止时钟更新 | AC-1.2 |

## 兼容性声明

不改变 controller API；仅记录现有调度和可见区优化行为。

## 架构约束

- controller 只转发启停请求，实际状态由 Pattern 维护。
- 可见区优化不得改变组件公开时间格式语义。

## 非功能性需求

| 类型 | 指标/阈值 | 验证方式 |
|------|-----------|----------|
| 性能 | 不可见时停止无效刷新 | VM-2 |
| 功耗 | 分钟格式避免秒级刷新 | VM-3 |

## 多设备适配声明

无组件级设备差异。

## 全局特性影响

| 特性 | 适用 | 说明 |
|------|------|------|
| 多窗口/分屏 | 是 | 可见区变化会触发暂停/恢复。 |
| 后台功耗 | 是 | 不可见时减少刷新。 |

## 行为场景（可选，Gherkin）

```gherkin
Scenario: 不可见时暂停刷新
  Given TextClock 正在显示秒级时间
  When 组件移出可见区域
  Then 延迟刷新任务被取消
```

## Spec 自审清单

- [x] 特性编号符合 `Func-05-10-07-Feat-02`
- [x] AC 使用 WHEN/THEN 表述
- [x] 验证映射指向源码和测试入口
- [x] 无新增 API

## context-references

- `frameworks/core/components_ng/pattern/text_clock/text_clock_pattern.cpp`
- `frameworks/core/components/text_clock/text_clock_controller.h`
- `test/unittest/core/pattern/text_clock/`
