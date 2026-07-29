# 特性规格

> Func-05-10-08-Feat-02 TextTimer 控制器与事件：固化 start/pause/reset 控制器行为、Scheduler 驱动和 onTimer 回调。

## 概述

| 属性 | 值 |
|------|----|
| 特性名称 | 控制器与事件 |
| 特性编号 | Func-05-10-08-Feat-02 |
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
| Design | `05-ui-components/10-information-display-components/08-text-timer/design.md` | Baselined |
| Pattern | `frameworks/core/components_ng/pattern/texttimer/text_timer_pattern.cpp` | 已实现 |
| EventHub | `frameworks/core/components_ng/pattern/texttimer/text_timer_event_hub.h` | 已实现 |
| Controller | `frameworks/core/components/texttimer/texttimer_controller.h` | 已实现 |

## 用户故事

### US-1: 控制计时状态

**作为** 应用开发者  
**我想要** 通过 TextTimerController 控制计时启动、暂停和重置  
**以便** 按业务交互控制计时状态。

| AC编号 | 验收标准 | 类型 |
|--------|----------|------|
| AC-1.1 | WHEN 调用 controller.start() THEN Scheduler 启动并刷新计时文本 | 正常 |
| AC-1.2 | WHEN 调用 controller.pause() THEN Scheduler 暂停计时更新 | 正常 |
| AC-1.3 | WHEN 调用 controller.reset() THEN 计时值恢复到初始状态 | 正常 |

### US-2: onTimer 回调

**作为** 应用开发者  
**我想要** 监听 TextTimer 的计时回调  
**以便** 在计时变化时同步业务状态。

| AC编号 | 验收标准 | 类型 |
|--------|----------|------|
| AC-2.1 | WHEN 计时运行且到达回调触发条件 THEN 触发 onTimer | 正常 |
| AC-2.2 | WHEN 未注册 onTimer THEN 计时运行不触发回调 | 边界 |

## 验收追溯

| AC编号 | 规则编号 | 验证方式 | 证据 |
|--------|----------|----------|------|
| AC-1.1 | R-1 | 源码审阅/单测 | `texttimer_controller.h`、`text_timer_pattern.cpp` |
| AC-2.1 | R-2 | 源码审阅/单测 | `text_timer_event_hub.h`、`text_timer_pattern.cpp` |

## 规则定义

| R-N | 类型 | 触发条件 | 预期行为 | 边界/约束 | 关联AC |
|-----|------|----------|----------|-----------|--------|
| R-1 | 行为 | controller start/pause/reset | 修改 Pattern 计时状态 | 未绑定 Pattern 不崩溃 | AC-1.1 |
| R-2 | 行为 | 计时 tick | 满足条件时分发 onTimer | 未注册回调不触发 | AC-2.1 |

## 验证映射

| VM编号 | 覆盖范围 | 验证方式 | 文件 |
|--------|----------|----------|------|
| VM-1 | controller 行为 | 源码审阅/单测 | `frameworks/core/components/texttimer/texttimer_controller.h`、`test/unittest/core/pattern/text_timer/` |
| VM-2 | Scheduler 和 onTimer | 源码审阅/单测 | `frameworks/core/components_ng/pattern/texttimer/text_timer_pattern.cpp`、`text_timer_event_hub.h` |

## API 变更分析

### 新增 API

无。

### 变更/废弃 API

无。

## 接口规格

| 接口 | 参数 | 返回值 | 行为 | 关联AC |
|------|------|--------|------|--------|
| `TextTimerController.start()` | 无 | void | 启动计时 | AC-1.1 |
| `TextTimerController.pause()` | 无 | void | 暂停计时 | AC-1.2 |
| `TextTimerController.reset()` | 无 | void | 重置计时 | AC-1.3 |
| `.onTimer(callback)` | function | `TextTimerAttribute` | 注册计时回调 | AC-2.1 |

## 兼容性声明

不改变 controller 和事件 API。

## 架构约束

- controller 不直接操作 UI 文本，状态变更由 Pattern 消费。
- EventHub 只负责回调保存和分发。

## 非功能性需求

| 类型 | 指标/阈值 | 验证方式 |
|------|-----------|----------|
| 可靠性 | 未注册回调不影响计时 | VM-2 |

## 多设备适配声明

无组件级设备差异。

## 全局特性影响

| 特性 | 适用 | 说明 |
|------|------|------|
| 后台功耗 | 是 | Scheduler 运行状态影响刷新频率。 |

## 行为场景（可选，Gherkin）

```gherkin
Scenario: controller 暂停计时
  Given TextTimer 正在运行
  When 调用 pause
  Then 计时更新暂停
```

## Spec 自审清单

- [x] 特性编号符合 `Func-05-10-08-Feat-02`
- [x] AC 使用 WHEN/THEN 表述
- [x] 验证映射指向源码和测试入口
- [x] 无新增 API

## context-references

- `frameworks/core/components/texttimer/texttimer_controller.h`
- `frameworks/core/components_ng/pattern/texttimer/text_timer_pattern.cpp`
- `frameworks/core/components_ng/pattern/texttimer/text_timer_event_hub.h`
