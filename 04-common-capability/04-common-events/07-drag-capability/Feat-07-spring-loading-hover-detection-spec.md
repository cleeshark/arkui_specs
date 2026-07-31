# 特性规格

## 概述

| 字段 | 内容 |
|---|---|
| 特性名称 | 弹簧加载与拖拽悬停检测 |
| 特性编号 | Func-04-04-07-Feat-07 |
| 所属 Epic | 04-common-capability / 04-common-events / 07-drag-capability |
| 优先级 | P1 |
| 目标版本 | 动态 ArkTS API 20；静态 ArkTS API 26.0.0 |
| SIG 归属 | ArkUI SIG |
| 状态 | Baselined |
| 复杂度 | 关键 |

## 本次变更范围（Delta）

| 类型 | 内容 | 说明 |
|---|---|---|
| ADDED | `onDragSpringLoading`、状态/配置/上下文、悬停计时与中断 | 对已有动态/静态 ArkTS 公共合同及 ArkUI 状态机行为补录，不改变实现。 |

## 输入文档

- `specs/04-common-capability/04-common-events/07-drag-capability/design.md`
- `<OH_ROOT>/interface_sdk-js/api/@internal/component/ets/common.d.ts:24612-24632`
- `<OH_ROOT>/interface_sdk-js/api/arkui/component/common.static.d.ets:13180-13184`
- `<OH_ROOT>/interface_sdk-js/api/@ohos.arkui.dragController.d.ts:569-812`
- `<OH_ROOT>/interface_sdk-js/api/@ohos.arkui.dragController.static.d.ets:373-566`
- `frameworks/core/components_ng/manager/drag_drop/drag_drop_spring_loading/drag_drop_spring_loading_detector.cpp:31-149`
- `frameworks/core/components_ng/manager/drag_drop/drag_drop_spring_loading/drag_drop_spring_loading_state_idle.cpp:22-40`
- `frameworks/core/components_ng/manager/drag_drop/drag_drop_spring_loading/drag_drop_spring_loading_state_begin.cpp:22-70`
- `frameworks/core/components_ng/manager/drag_drop/drag_drop_spring_loading/drag_drop_spring_loading_state_update.cpp:22-68`

## 用户故事

### US-1: 注册可配置的通用拖拽悬停响应

作为拖拽目标开发者，我希望绑定 `onDragSpringLoading` 和时序配置，以便在拖拽物在目标内稳定停留时显示反馈或准备后续导航。

| AC编号 | 验收标准 | 类型 |
|---|---|---|
| AC-1.1 | WHEN 动态 ArkTS API 20 为组件绑定非空 `onDragSpringLoading(callback, configuration?)`，THEN 该组件可成为悬停响应目标，同一时刻仅一个目标响应且子组件优先。 | 正常 |
| AC-1.2 | WHEN 动态 API 20 传入 `null` 回调，THEN 关闭该组件的悬停检测；WHEN 未提供 configuration，THEN 使用既有默认配置。 | 边界 |
| AC-1.3 | WHEN 动态 API 20 配置四项时序字段，THEN 接受 `[0, 2^31-1]` 整数并截断浮点；负数、null、undefined、NaN 分别回退到默认 500ms、100ms、3、100ms。 | 异常 |
| AC-1.4 | WHEN 静态 ArkTS API 26.0.0 调用同名方法，THEN 使用 `Callback<SpringLoadingContext> \| null \| undefined` 和可选 `int` 配置，不以动态 API 20 的类型或版本替代。 | 兼容 |

### US-2: 接收稳定悬停的状态与上下文

作为拖拽目标开发者，我希望收到 BEGIN、UPDATE、END 或 CANCEL 上下文及数据摘要，以便区分准备、持续反馈、完成和清理。

| AC编号 | 验收标准 | 类型 |
|---|---|---|
| AC-2.1 | WHEN 拖拽物进入有回调的目标并在 `stillTimeLimit` 内未超过移动阈值，THEN 状态机在该时限后通知 BEGIN，通知序号从 0 开始。 | 正常 |
| AC-2.2 | WHEN BEGIN 后 `updateNotifyCount` 大于 0 且未中断，THEN 每隔 `updateInterval` 通知 UPDATE，达到次数后等待 `updateToFinishInterval` 并通知 END；WHEN count 为 0，THEN BEGIN 后直接按 finish interval 进入 END。 | 正常 |
| AC-2.3 | WHEN 回调状态为 BEGIN、UPDATE 或 END，THEN `SpringLoadingContext` 提供状态、零起始序号、当前配置及拖拽数据摘要/extraInfos。 | 正常 |
| AC-2.4 | WHEN 离开、释放、窗口切换、进入子组件或移动速度超过阈值而中断，THEN 在 END 前进入 CANCEL 并通知清理；CANCEL 的 `dragInfos` 与 `currentConfig` 可缺失。 | 异常 |

### US-3: 控制当前检测周期

作为需要按数据类型调整 UX 的开发者，我希望在 BEGIN 回调中修改本周期时序，或终止后续检测，以便控制既有悬停反馈而不改写绑定配置。

| AC编号 | 验收标准 | 类型 |
|---|---|---|
| AC-3.1 | WHEN 在 BEGIN 回调调用 `updateConfiguration(config)`，THEN 后续 UPDATE/END 使用动态配置，绑定时保存的原始 configuration 不被改写。 | 正常 |
| AC-3.2 | WHEN 在 UPDATE、END 或 CANCEL 回调调用 `updateConfiguration(config)`，THEN 该调用不具有更新当前周期配置的公开效果。 | 边界 |
| AC-3.3 | WHEN 在任一回调调用 `abort()`，THEN 终止后续检测；公开合同不发送由 abort 引起的 CANCEL，应用自行清理 UI 状态。 | 恢复 |
| AC-3.4 | WHEN 需要 NDK 等价入口，THEN `interface_sdk_c/.../drag_and_drop.h` 中未找到此通用 SpringLoading 能力的 C API，调用方不得推断 C 入口。 | 边界 |

## 验收追溯

| AC | 关联规则 | 关联 Task | 验证方式 | 证据 |
|---|---|---|---|---|
| AC-1.1~AC-1.4 | R-1、R-2 | Feat-07 | SDK 类型检查/组件回调测试 | `common.d.ts:24612-24632`; `common.static.d.ets:13180-13184`; `dragController.d.ts:636-688` |
| AC-2.1~AC-2.4 | R-3~R-6 | Feat-07 | DragDropManager/状态机 Host 单测 | `detector.cpp:48-123`; `state_idle.cpp:22-40`; `state_begin.cpp:22-70`; `state_update.cpp:22-68` |
| AC-3.1~AC-3.4 | R-7~R-9 | Feat-07 | SDK 合同和状态机回调测试 | `dragController.d.ts:785-812`; `state_base.cpp:41-62`; `state_begin.cpp:39-47` |

## 规则定义

| 规则ID | 类型 | 触发条件 | 预期行为 | 边界/约束 | 关联AC |
|---|---|---|---|---|---|
| R-1 | 行为 | 组件绑定非空 spring-loading 回调 | 目标参与悬停响应；子节点优先，任一时刻仅一个目标响应 | null 关闭；不存在 C API 等价入口 | AC-1.1、AC-1.2、AC-3.4 |
| R-2 | 边界 | 提供四项时间/次数配置 | 动态 API 20 按 SDK 的整数范围、截断和默认值解释；静态 API 26.0.0 按 `int` 合同解释 | 默认值为 500ms、100ms、3、100ms | AC-1.3、AC-1.4 |
| R-3 | 行为 | 新目标进入且稳定停留至 `stillTimeLimit` | IDLE 延迟任务转换为 BEGIN，当前通知序号从 0 开始 | 切换目标会复位并从新目标重新开始 | AC-2.1 |
| R-4 | 行为 | BEGIN/UPDATE 周期未中断 | count=0 按 finish interval 进入 END；否则按 update interval 递增 UPDATE，达到 count 后进入 END | 只允许既有状态转换图 | AC-2.2 |
| R-5 | 行为 | 产生 BEGIN、UPDATE 或 END 回调 | 上下文携带状态、递增序号、用户配置、摘要和 extraInfos | 不重新定义 UDMF/MSDP 会话 | AC-2.3 |
| R-6 | 异常 | 离开、结束、窗口/子目标变化，或速度达到 0.0225 vp/ms | 未到 END 的周期转 CANCEL 并回调，随后复位 | 已到 END 时拦截不再发 CANCEL | AC-2.4 |
| R-7 | 行为 | BEGIN 回调调用 `updateConfiguration` | 状态机以 context 中的新配置安排后续任务 | 仅当前周期，不写回节点绑定配置 | AC-3.1 |
| R-8 | 边界 | 非 BEGIN 回调调用 `updateConfiguration` | 公开 API 不承诺更新效果 | 不将内部 context 可写对象描述成全状态可配置接口 | AC-3.2 |
| R-9 | 恢复 | 回调调用 `abort()` | 终止后续检测；应用清理 UI，abort 本身不发送 CANCEL | 不等同系统拖拽结束 | AC-3.3 |

## 验证映射

| 编号 | 对应规格项 | 验证方式 | 验证重点 |
|---|---|---|---|
| VM-1 | R-1、R-2 | 动态/静态 ArkTS 编译和回调测试 | 可空 callback、默认配置、动态数值边界、版本差异。 |
| VM-2 | R-3~R-5 | DragDropManager 状态机 Host 单测 | 停留、序号、count=0、UPDATE 次数、END 延迟、上下文数据。 |
| VM-3 | R-6 | 事件路由/状态机 Host 单测 | leave/end/intercept、速度阈值、已 END 的抑制。 |
| VM-4 | R-7~R-9 | callback 行为测试 | BEGIN-only 重配置、abort 后无额外 CANCEL、原始配置不变。 |

## API 变更分析

### 新增 API

| API 名称 | 开放范围 | 入参概要 | 返回值 | 错误码范围 | 功能描述 | 关联 AC |
|---|---|---|---|---|---|---|
| `onDragSpringLoading` | Public ArkTS | callback、可选配置 | 当前组件 `this` | N/A | 绑定或关闭通用拖拽悬停检测。 | AC-1.1、AC-1.2、AC-1.4 |
| `DragSpringLoadingState`、`DragSpringLoadingConfiguration`、`SpringLoadingDragInfos` | Public ArkTS | 状态、四项时序配置、摘要/附加信息 | N/A | 描述悬停周期与输入数据。 | AC-1.3、AC-2.1~AC-2.4 |
| `SpringLoadingContext.abort/updateConfiguration` | Public ArkTS | 无 / 新配置 | void | N/A | 终止后续周期或在 BEGIN 中调整本周期。 | AC-3.1~AC-3.3 |

### 变更/废弃 API

| API 名称 | 变更类型 | 影响场景 | 迁移指引 | 关联 AC |
|---|---|---|---|---|
| 动态与静态 spring-loading API | 变更 | 动态自 API 20 提供，静态自 API 26.0.0 提供，callback 可空性不同 | 按所属前端的 canonical SDK 和最低版本调用。 | AC-1.4 |
| C API | 变更 | `drag_and_drop.h` 未声明此能力 | NDK 调用方不可期待 C API；不从内部状态机推断 ABI。 | AC-3.4 |

## 接口规格

### 接口定义

**`CommonMethod.onDragSpringLoading`**

| 属性 | 值 |
|---|---|
| 函数签名 | 动态：`onDragSpringLoading(callback: Callback<SpringLoadingContext> \| null, configuration?: DragSpringLoadingConfiguration): T`；静态：`onDragSpringLoading(callback: Callback<SpringLoadingContext> \| null \| undefined, configuration?: DragSpringLoadingConfiguration): this` |
| 返回值 | 当前组件，用于链式调用 |
| 开放范围 | Public ArkTS |
| 错误码 | N/A |
| 关联 AC | AC-1.1~AC-1.4 |

**参数约束**

| 参数 | 类型 | 必填 | 默认值 | 约束条件 |
|---|---|---|---|---|
| callback | `Callback<SpringLoadingContext> \| null`（静态额外接受 undefined） | 是 | N/A | null 关闭动态回调；仅一个目标响应，子组件优先。 |
| configuration | `DragSpringLoadingConfiguration` | 否 | 500ms、100ms、3、100ms | 动态 API 20 采用整数范围和无效值回退；静态 API 26.0.0 使用 `int` 合同。 |

**行为场景**

| # | 触发条件 | 预期行为 | 关联 AC |
|---|---|---|---|
| 1 | 目标稳定停留到 stillTimeLimit | 通知 BEGIN；随后按配置通知 UPDATE/END。 | AC-2.1、AC-2.2 |
| 2 | callback 为 null 或被中断 | 关闭检测，或通知 CANCEL 后复位。 | AC-1.2、AC-2.4 |

**`SpringLoadingContext` 控制组**

| 属性 | 值 |
|---|---|
| 函数签名 | `abort(): void`；`updateConfiguration(config: DragSpringLoadingConfiguration): void` |
| 返回值 | void |
| 开放范围 | Public ArkTS |
| 错误码 | N/A |
| 关联 AC | AC-3.1~AC-3.3 |

**参数约束**

| 参数 | 类型 | 必填 | 默认值 | 约束条件 |
|---|---|---|---|---|
| config | `DragSpringLoadingConfiguration` | update 时是 | N/A | 仅 BEGIN 有效；仅更新当前周期，不改绑定原始配置。 |

**行为场景**

| # | 触发条件 | 预期行为 | 关联 AC |
|---|---|---|---|
| 1 | BEGIN 回调调用 updateConfiguration | 后续本周期按新配置调度。 | AC-3.1 |
| 2 | 任一回调调用 abort | 停止后续检测且不由 abort 触发 CANCEL。 | AC-3.3 |

## 兼容性声明

- **已有 API 行为变更:** 否；补录动态 ArkTS API 20 和静态 ArkTS API 26.0.0 的既有能力。
- **配置文件格式变更:** 否；配置保存在既有节点 `DragDropRelatedConfigurations` 中。
- **数据存储格式变更:** 否；上下文仅承载当前周期状态和 DragDropManager 摘要。
- **最低支持版本:** 动态 ArkTS API 20；静态 ArkTS API 26.0.0；C API 不涉及。
- **API 版本号策略:** 分别以 canonical SDK 的 `@since` 为准；不把动态 API 20 与静态 API 26.0.0 视为同一范围。

## 架构约束

| 关键约束 | 约束说明 | 影响 AC |
|---|---|---|
| 单响应目标 | 回调目标由当前命中节点决定，子组件优先；目标切换会复位周期。 | AC-1.1、AC-2.1 |
| UI 任务时序 | IDLE、UPDATE、END 的延迟任务在 UI task executor 调度。 | AC-1.3、AC-2.1、AC-2.2 |
| 系统拖拽边界 | ArkUI 只提供目标端检测/回调；真实会话由 InteractionInterface/MSDP 协作。 | AC-2.3、AC-3.3 |
| 无 C API | 公开 C header 未提供 SpringLoading 声明。 | AC-3.4 |

## 非功能性需求

| 类型 | 指标/阈值 | 验证方式 | 证据 |
|---|---|---|---|
| 性能 | 移动速度以 `0.0225 vp/ms` 判定中断，避免快速移动持续触发悬停。 | 状态机 Host 单测 | `drag_drop_spring_loading_detector.cpp:125-142` |
| 可靠性 | Reset 取消 timer、清零序号/次数和动态配置。 | 状态机 Host 单测 | `drag_drop_spring_loading_state_machine.cpp:64-72` |
| 可测试性 | 四种状态、序号、配置和 abort 均由 callback 上下文观察。 | ArkTS/Host 回调测试 | `drag_drop_spring_loading_state_base.cpp:41-62` |

## 多设备适配声明

| 设备类型 | 行为差异 | 规格/约束 | 验证方式 | 证据 |
|---|---|---|---|---|
| 手机 | 无本 Feat 特有差异 | 按当前节点和运动速度执行同一状态机。 | 设备/Host 集成测试 | `drag_drop_spring_loading_detector.cpp:48-142` |
| 平板 | 无本 Feat 特有差异 | 窗口切换属于 CANCEL 条件。 | 多窗口集成测试 | `dragController.d.ts:610-613` |
| 折叠屏 | 无本 Feat 特有差异 | 显示形态不改变配置/状态合同。 | 多窗口/多显示器集成测试 | `drag_drop_manager.cpp:1934-1943` |

## 全局特性影响

| 特性 | 适用？ | 结论 | 关联场景 |
|---|---|---|---|
| 无障碍 | 否 | 未新增 accessibility 公共接口或语义。 | N/A |
| 大字体 | 否 | 计时/状态机不依赖字体缩放。 | N/A |
| 深色模式 | 否 | 回调只提供状态和数据，不定义视觉配色。 | N/A |
| 多窗口/分屏 | 是 | 窗口切换可中断并进入 CANCEL；不重定义系统会话路由。 | AC-2.4 |
| 版本升级 | 是 | 动态 API 20 与静态 API 26.0.0 必须分别守护。 | AC-1.4 |
| 生态兼容 | 是 | 不为缺失 C API 创造 ABI 承诺。 | AC-3.4 |

## 行为场景（可选，Gherkin）

```gherkin
Feature: 弹簧加载与拖拽悬停检测
  Scenario: 稳定悬停完成一个检测周期
    Given 拖拽物进入已绑定 onDragSpringLoading 的目标
    When 在 stillTimeLimit 内未超过移动阈值并保持停留
    Then 首先通知 BEGIN
    And 按 updateNotifyCount 和两个 interval 通知 UPDATE 或 END

  Scenario: 悬停中断
    Given 当前周期尚未进入 END
    When 拖拽物离开目标或移动速度达到阈值
    Then 通知 CANCEL
    And 状态机复位到 IDLE

  Scenario: BEGIN 内动态调整
    Given 已收到 BEGIN 上下文
    When 回调调用 updateConfiguration
    Then 后续本周期按新配置调度
    And 绑定时的原始配置保持不变
```

## Spec 自审清单

- [x] 无 TBD、TODO 或占位符。
- [x] 所有 AC 使用 WHEN/THEN，且可独立验证。
- [x] 覆盖动态/静态 ArkTS、配置、悬停计时、状态机、系统事件、中断和 C API 缺失边界。
- [x] 每个 AC 至少关联一条规则和一种验证方式。
- [x] 每条规则满足可复现、可观测、边界明确、关联 AC 和不冲突要求。

## context-references

```yaml
context-queries:
  - repo: "OpenHarmony/arkui_ace_engine"
    query: "Drag spring loading hover detection state machine configuration callback abort and target interception"
```
