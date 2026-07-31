# 特性规格

## 概述

| 属性 | 值 |
|------|-----|
| 特性名称 | 输入事件分发与采样管线 |
| 特性编号 | Func-03-04-01-Feat-03 |
| 所属 Epic | 无 |
| 优先级 | P0 |
| 目标版本 | API 8-23，当前主干 |
| SIG 归属 | ArkUI SIG |
| 状态 | Baselined |
| 复杂度 | 关键 |

本规格补录 Touch、Mouse、Axis、Key 的统一分发、输入监控、批处理、历史采样与重采样行为，并记录鼠标 API 13 兼容分支。

## 本次变更范围（Delta）

| 类型 | 内容 | 说明 |
|------|------|------|
| ADDED | 多输入分发规格 | 固化 Touch/Mouse/Axis/Key 进入 EventManager 后的处理边界 |
| ADDED | 监控链规格 | 固化 BLOCK、已透传 DOWN 和补发 CANCEL 的恢复语义 |
| ADDED | 采样规格 | 固化 FlushTouchEvents、history 和 touch/mouse resample |
| ADDED | 版本差异 | 固化 API 13 前后鼠标按压目标保存方式 |

## 输入文档

- 共享设计：`specs/03-engine-framework/04-event-framework/01-event-base-framework/design.md`。
- 分发实现：`frameworks/core/common/event_manager.cpp:966,1208,1650,2048,2067,2406`。
- 监控实现：`frameworks/core/common/input_event_monitor_manager.cpp:46-181`。
- 重采样实现：`frameworks/core/common/event_manager.cpp:2809-2945`。
- Native 历史数据：`interfaces/native/ui_input_event.h:850-1065`。

## 用户故事

### US-1: 稳定分发多种输入事件

作为输入框架开发者，我希望不同输入类型进入匹配的目标链和兼容分支，以便组件获得连续且可停止传播的事件序列。

| AC编号 | 验收标准 | 类型 |
|--------|----------|------|
| AC-1.1 | WHEN Touch 事件存在 pointer 命中缓存 THEN 先执行多容器分发，再向 NG recognizer/touch target 和 Legacy 管线分发 | 正常 |
| AC-1.2 | WHEN Axis BEGIN 命中 recognizer 且不是旋转事件 THEN 将目标加入对应 referee scope 后分发 | 正常 |
| AC-1.3 | WHEN Mouse 在 API 13 及以上按下不同 button THEN 按 event.id 与 button 分别保存 press 目标；WHEN API 13 以下 THEN 仅对左键使用单一 press 结果 | 边界 |
| AC-1.4 | WHEN目标处理返回停止传播 THEN 后续同阶段目标不再收到该事件，但已获胜 recognizer 自行过滤额外事件 | 正常 |

### US-2: 监控、批处理和恢复输入序列

作为系统输入监控和渲染管线开发者，我希望监控器可以阻断事件，并在必要时形成 CANCEL，同时批量刷新和重采样连续点，以便上下游状态机不会悬挂。

| AC编号 | 验收标准 | 类型 |
|--------|----------|------|
| AC-2.1 | WHEN Monitor 对 DOWN 返回 BLOCK THEN 记录 DOWN_BLOCKED 且该交互后续事件继续被监控链处理 | 正常 |
| AC-2.2 | WHEN DOWN 已透传而 Mouse/Touch/Key 后续事件首次被 BLOCK THEN 将该事件改写为 CANCEL 并继续下发以结束交互 | 恢复 |
| AC-2.3 | WHEN FlushTouchEvents 开始和结束 THEN 目标按批处理边界接收 flush begin/end，history 按当前批次维护 | 正常 |
| AC-2.4 | WHEN 存在至少两个有效样本且目标显示屏一致 THEN 基于最近两个样本计算重采样坐标；WHEN显示屏不同或样本不足 THEN 保持原事件 | 边界 |

## 验收追溯

| AC | 关联规则 | 关联 Task | 验证方式 | 证据 |
|----|----------|-----------|----------|------|
| AC-1.1, AC-1.4 | R-1, R-4 | TASK-F3-1 | EventManager 分发顺序测试 | `event_manager.cpp:1208-1259` |
| AC-1.2 | R-2 | TASK-F3-1 | Axis BEGIN/rotation 参数化测试 | `event_manager.cpp:1650-1674` |
| AC-1.3 | R-3 | TASK-F3-2 | API 12/13 鼠标回归 | `event_manager.cpp:2067-2108` |
| AC-2.1, AC-2.2 | R-5, R-6 | TASK-F3-3 | Monitor 阻断序列测试 | `input_event_monitor_manager.cpp:70-181` |
| AC-2.3 | R-7 | TASK-F3-4 | 批处理和 history 测试 | `event_manager.cpp:966-1000` |
| AC-2.4 | R-8 | TASK-F3-4 | 重采样边界测试 | `event_manager.cpp:2809-2945` |

## 规则定义

| 规则ID | 类型 | 触发条件 | 预期行为 | 边界/约束 | 关联AC |
|--------|------|----------|----------|-----------|--------|
| R-1 | 行为 | touchTestResults_ 存在 event.id | 执行多容器分发、NG 分发、Legacy 分发和结束清理 | 结果不存在时返回 false 并更新结束状态 | AC-1.1 |
| R-2 | 行为 | AxisAction::BEGIN 且非 rotation | 将命中 recognizer 加入当前 referee scope | rotation 事件不加入 touch scope | AC-1.2 |
| R-3 | 边界 | 分发有效 MouseAction | API >=13 使用 `{id, button}` 键保存 press 结果并处理 CANCEL；API <13 仅左键使用单一结果且 RELEASE 清理 | 目标 API 版本以 AceApplicationInfo 判定 | AC-1.3 |
| R-4 | 行为 | target 返回停止传播 | 停止普通目标的后续处理；recognizer 仍收到事件并自行过滤 | 不回滚已处理目标 | AC-1.4 |
| R-5 | 行为 | monitor chain 对 DOWN 返回 BLOCK | 标记该 interaction 为 DOWN_BLOCKED | interaction key 按输入类型和标识构造 | AC-2.1 |
| R-6 | 恢复 | DOWN 未阻断而后续事件返回 BLOCK | Mouse 改为 CANCEL、Touch 改为 CANCEL、Key 改为 CANCEL 后继续下发 | 每轮交互仅用于结束已开始状态，不产生新的 DOWN | AC-2.2 |
| R-7 | 行为 | 批量 Touch flush | 在分发批次前后调用 flush begin/end，批次历史点可由公开 C API 查询 | historyIndex 必须小于 GetHistorySize 返回值 | AC-2.3 |
| R-8 | 边界 | 尝试 Touch/Mouse resample | 合并历史和当前样本，最多取末尾两个有效样本插值；目标显示屏不一致或样本不足时不替换原坐标 | x/y、screen、globalDisplay 坐标分别计算 | AC-2.4 |

## 验证映射

| 编号 | 对应规格项 | 验证方式 | 验证重点 |
|------|------------|----------|----------|
| VM-1 | AC-1.1, AC-1.2, AC-1.4 | Touch/Axis 分发单测 | 顺序、停止传播、scope |
| VM-2 | AC-1.3 | API 12/13 双版本测试 | 多按键 press 结果和 CANCEL 清理 |
| VM-3 | AC-2.1, AC-2.2 | Mouse/Touch/Key monitor 序列测试 | DOWN_BLOCKED 与补发 CANCEL |
| VM-4 | AC-2.3 | flush/history 单测和 C API 测试 | 批处理边界、historyIndex |
| VM-5 | AC-2.4 | 重采样参数化测试 | 两样本、跨显示屏、坐标系 |

## API 变更分析

### 新增 API

无新增 API。Native 历史样本 getter 为既有接口。

### 变更/废弃 API

无变更或废弃 API。

## 接口规格

### 接口定义

**历史 Pointer Event getter（现有 C API）**

| 属性 | 值 |
|------|-----|
| 函数签名 | `OH_ArkUI_PointerEvent_GetHistorySize/GetHistoryEventTime/GetHistoryX/GetHistoryY(...)` |
| 返回值 | 历史样本数量、时间和坐标 |
| 开放范围 | Public |
| 错误码 | 越界或不支持场景返回接口定义的无效值 |
| 关联 AC | AC-2.3 |

**参数约束**

| 参数 | 类型 | 必填 | 默认值 | 约束条件 |
|------|------|------|--------|---------|
| event | `const ArkUI_UIInputEvent*` | 是 | 无 | 必须是支持 history 的 Pointer Event |
| historyIndex | uint32_t | 是 | 无 | `0 <= historyIndex < GetHistorySize(event)` |
| pointerIndex | uint32_t | 是 | 无 | 小于对应历史样本的 pointer count |

行为索引：输入分发见 VM-1/VM-2；监控恢复见 VM-3；history 和 resample 见 VM-4/VM-5。

## 兼容性声明

- **已有 API 行为变更:** 否；鼠标内部兼容分支以目标 API 13 为界。
- **配置文件格式变更:** 否。
- **数据存储格式变更:** 否。
- **最低支持版本:** 基础事件 API 8；历史 getter 按 Native SDK 现有版本标注。
- **API 版本号策略:** 不新增 `@since`，保持现有声明。

## 架构约束

| 关键约束 | 约束说明 | 影响 AC |
|----------|----------|---------|
| 输入入口归一 | 平台输入先转换为 Ace 事件，再由 EventManager 分流 | AC-1.1, AC-1.2 |
| Monitor 在目标分发前 | BLOCK/CANCEL 恢复必须先于组件状态机处理 | AC-2.1, AC-2.2 |
| NG/Legacy 共存 | NG 处理完成后仍按条件进入旧管线 | AC-1.1 |
| 采样不跨显示屏 | resample 不混合 targetDisplay 不同的样本 | AC-2.4 |

## 非功能性需求

| 类型 | 指标/阈值 | 验证方式 | 证据 |
|------|-----------|----------|------|
| 性能 | resample 仅保留最近两个计算样本 | 样本容器测试 | `event_manager.cpp:2827` |
| 功耗 | 批量 flush 合并同帧输入处理 | 帧输入跟踪 | `event_manager.cpp:966` |
| 内存 | history 和 press 目标在交互结束时清理 | 长序列测试 | EventManager 清理路径 |
| 可靠性 | 已透传 DOWN 的阻断序列必须形成 CANCEL | Monitor 单测 | `input_event_monitor_manager.cpp:94,117,169` |
| 可测试性 | API 版本、输入类型、显示屏可参数化 | 单元测试 | VM-2/VM-5 |
| 定界定位 | sensor/process/dispatch 时间可进入输入跟踪 | 日志测试 | EventManager 输入时间回调 |

## 多设备适配声明

| 设备类型 | 行为差异 | 规格/约束 | 验证方式 | 证据 |
|----------|----------|-----------|----------|------|
| 手机 | Touch 为主要输入 | 支持多指 history/resample | 触摸滑动测试 | AC-2.4 |
| 平板 | 鼠标、多按键和触摸并存 | API 13+ 按 id/button 保存 press 目标 | 鼠标组合测试 | AC-1.3 |
| 折叠屏 | 可能产生跨显示区域坐标变化 | targetDisplay 不一致时禁止重采样 | 跨屏测试 | AC-2.4 |

## 全局特性影响

| 特性 | 适用？ | 结论 | 关联场景 |
|------|--------|------|----------|
| 无障碍 | 是 | 输入监控不得破坏无障碍交互结束状态 | AC-2.2 |
| 大字体 | 否 | 不改变分发规则 | - |
| 深色模式 | 否 | 不影响输入管线 | - |
| 多窗口/分屏 | 是 | 坐标、容器和 targetDisplay 必须对应 | AC-1.1, AC-2.4 |
| 多用户 | 否 | 无持久化数据 | - |
| 版本升级 | 是 | 鼠标 API 13 分支保持兼容 | AC-1.3 |
| 生态兼容 | 是 | 保持 NG/Legacy 双管线 | AC-1.1 |

## 行为场景（可选，Gherkin）

```gherkin
Feature: 输入事件分发与采样管线
  Scenario Outline: 监控器阻断已开始交互
    Given <类型> 的 DOWN 已透传至组件
    When 同一交互的后续事件被 monitor BLOCK
    Then 框架向下游发送 <类型> CANCEL

    Examples:
      | 类型 |
      | Touch |
      | Mouse |
      | Key |

  Scenario: 跨显示屏样本不重采样
    Given 最近两个输入样本的 targetDisplayId 不同
    When EventManager 尝试重采样
    Then 保持当前事件坐标
```

## Spec 自审清单

- [x] 无占位符
- [x] 所有 AC 使用 WHEN/THEN 格式
- [x] 范围边界明确
- [x] 无语义模糊表述
- [x] AC 与规则表交叉一致
- [x] 规则满足 5 项质量检查

## context-references

```yaml
context-queries:
  - repo: "openharmony/arkui_ace_engine"
    query: "EventManager input dispatch monitor BLOCK CANCEL FlushTouchEvents history resample API13 mouse"
```

**关键文档：** `design.md`、`event_manager.cpp`、`input_event_monitor_manager.cpp`、`ui_input_event.h`。
