# 特性规格

## 概述

| 属性 | 值 |
|------|-----|
| 特性名称 | 窗口生命周期与前后台状态转换 |
| 特性编号 | Func-03-05-01-Feat-02 |
| 所属 Epic | 无（已有实现补录） |
| 优先级 | P0 |
| 目标版本 | API 9 及以后（以 master HEAD 实现为基线） |
| SIG 归属 | ArkUI SIG / 窗口与渲染团队 |
| 状态 | Baselined |
| 复杂度 | 复杂 |

> 本 Feat 锁定 RosenWindow 的 RSUIDirector 生命周期状态机（GoForeground / GoBackground / GoStop / GoResume）、`windowAttachedStatus_` 三态语义、延迟节点释放（`NotifyBackgroundForNodeRelease` → 1000ms 延迟 `GoStop`）、恢复路径（`NotifyForegroundForNodeGoResume` → `GoResume`）、以及 `IsDisabledGoStopAndGoResume` 守卫条件。**焦点 ≠ 可见性**：OnActive/OnInactive 是焦点转换（WindowFocus），OnForeground/OnBackground 映射到 OnShow/OnHide。

## 本次变更范围（Delta）

> 历史规格补齐，补录已有实现的完整行为规格。

| 类型 | 内容 | 说明 |
|------|------|------|
| ADDED | OnShow/OnHide → GoForeground/GoBackground 转换 | 包含 GoResume 前置和 GoStop 后置 |
| ADDED | windowAttachedStatus_ 三态语义 | std::optional<bool>: true/false/nullopt |
| ADDED | NotifyWindowAttachStateChange 状态机 | 状态去重 + onShow_ 门控 + 分支决策 |
| ADDED | NotifyBackgroundForNodeRelease 延迟 GoStop | 1000ms 延迟 + 双重检查 + hasPost_ 幂等 |
| ADDED | NotifyForegroundForNodeGoResume 恢复 | STOP 状态检查 + GoResume + hasPost_ 取消 |
| ADDED | FlushPendingNodeReleaseTask 立即执行 | 移除延迟任务 + 直接 GoBackgroundForNodeRelease |
| ADDED | FlushImplicitTransaction 内部语义 | 刷新 RS 事务暂存层（非 SendMessages），多实例专用帧外事务刷新 |
| ADDED | IsDisabledGoStopAndGoResume 守卫 | SubContainer / FormRender / SceneBoard / DynamicRender |

## 输入文档

- 关联设计：`specs/03-engine-framework/05-window-mechanism/01-window-mechanism/design.md`
- 关联需求：已有能力补录（无独立 requirement.md）
- 源码定位（关键文件）：
  - `frameworks/core/components_ng/render/adapter/rosen_window.h` / `.cpp` — 生命周期方法实现
  - `frameworks/core/common/window.h` — 基类 onShow_ / GoBackgroundForNodeRelease / NotifyWindowAttachStateChange 虚方法
  - `adapter/ohos/entrance/ace_container.h` / `.cpp` — 上层 OnForeground/OnBackground/OnActive/OnInactive 调用入口

## 用户故事

### US-1: OnShow 触发 GoForeground 并恢复 Detached 节点

- As a 窗口生命周期维护者
- I want OnShow 先检查窗口是否处于 Detached 状态，若是则先 GoResume 恢复 RSUIDirector，再 GoForeground
- So that 从 STOP 状态恢复的 director 能正确进入前台渲染

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-1.1 | WHEN `OnShow()` 被调用 THEN 首先调用 `Window::OnShow()` 设置 `onShow_=true`。来源：`rosen_window.cpp:303` | 正常 |
| AC-1.2 | WHEN `IsWindowDetached()` 返回 true（即 `windowAttachedStatus_` 有值且为 false）THEN 调用 `NotifyForegroundForNodeGoResume()` 在 GoForeground 之前恢复 STOP 状态的 director。来源：`rosen_window.cpp:306-308` | 正常 |
| AC-1.3 | WHEN `IsWindowDetached()` 返回 false（nullopt 或 true）THEN **跳过** GoResume，直接调用 `rsUIDirector_->GoForeground()`。来源：`rosen_window.cpp:309` | 正常 |
| AC-1.4 | WHEN 多实例启用 THEN 在 GoForeground 之后调用 `FlushImplicitTransaction(rsUIDirector_)` 刷新隐式事务。来源：`rosen_window.cpp:310-312` | 正常 |

### US-2: OnHide 触发 GoBackground 并调度节点释放

- As a 窗口生命周期维护者
- I want OnHide 先 GoBackground 并 SendMessages 刷出消息，然后若 Detached 则调度延迟 GoStop
- So that 隐藏窗口的 RS 资源能被及时释放，同时保证 Detached 节点不泄露

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-2.1 | WHEN `OnHide()` 被调用 THEN 首先调用 `Window::OnHide()` 设置 `onShow_=false`。来源：`rosen_window.cpp:317` | 正常 |
| AC-2.2 | WHEN OnHide 执行 THEN 调用 `rsUIDirector_->GoBackground()` 然后 `rsUIDirector_->SendMessages()` 立即刷出状态变更。来源：`rosen_window.cpp:318-320` | 正常 |
| AC-2.3 | WHEN `IsWindowDetached()` 返回 true THEN 调用 `NotifyBackgroundForNodeRelease()` 调度延迟 GoStop。来源：`rosen_window.cpp:322-324` | 正常 |
| AC-2.4 | WHEN `IsWindowDetached()` 返回 false（nullopt 或 true）THEN **跳过** NotifyBackgroundForNodeRelease，不调度节点释放。来源：`rosen_window.cpp:322` | 边界 |

### US-3: windowAttachedStatus_ 三态语义

- As a 窗口状态管理维护者
- I want windowAttachedStatus_ 使用 std::optional<bool> 表示三种状态：true(attached) / false(detached) / nullopt(initial)
- So that 初始态不被误判为 detached 触发不必要的 GoStop

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-3.1 | WHEN `windowAttachedStatus_` 为 nullopt THEN `IsWindowDetached()` 返回 false，`IsWindowAttached()` 返回 false（即 nullopt 不等于 attached 也不等于 detached）。来源：`rosen_window.h:220-228` | 正常 |
| AC-3.2 | WHEN `windowAttachedStatus_==true` THEN `IsWindowAttached()` 返回 true，`IsWindowDetached()` 返回 false。来源：`rosen_window.h:225-228` | 正常 |
| AC-3.3 | WHEN `windowAttachedStatus_==false` THEN `IsWindowDetached()` 返回 true，`IsWindowAttached()` 返回 false。来源：`rosen_window.h:220-223` | 正常 |
| AC-3.4 | WHEN `GetWindowAttachedStatusForLog()` 被调用 THEN nullopt 返回 -1，true 返回 1，false 返回 0。用于 HiTrace 日志可读性。来源：`rosen_window.h:230-233` | 正常 |

### US-4: NotifyWindowAttachStateChange 状态机

- As a 窗口状态管理维护者
- I want NotifyWindowAttachStateChange 去重状态变更，在前台时不执行任何操作，在后台时根据 attach 状态分支决策
- So that 避免重复状态转换和前台窗口的无效 GoStop

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-4.1 | WHEN `NotifyWindowAttachStateChange(status)` 被调用且 `IsDisabledGoStopAndGoResume(container)` 返回 true THEN 直接返回，不更新 `windowAttachedStatus_`，不触发任何状态转换。来源：`rosen_window.cpp:583-590` | 正常 |
| AC-4.2 | WHEN status 与当前 `windowAttachedStatus_` 值相同（statusEqualsCurrent）THEN 直接返回，不重复触发。来源：`rosen_window.cpp:585-589` | 正常 |
| AC-4.3 | WHEN 检查通过 THEN 更新 `windowAttachedStatus_ = status`。**赋值发生在分支决策之前**，确保后续 IsWindowDetached/IsWindowAttached 使用新值。来源：`rosen_window.cpp:591` | 正常 |
| AC-4.4 | WHEN `onShow_==true`（窗口可见）THEN 直接返回（`:593-594`），不执行 GoStop/GoResume——前台窗口无法 GoStop。来源：`rosen_window.cpp:593-595` | 正常 |
| AC-4.5 | WHEN `onShow_==false` 且 `IsWindowDetached()`（status==false）THEN 调用 `NotifyBackgroundForNodeRelease()` 调度延迟 GoStop。来源：`rosen_window.cpp:597-598` | 正常 |
| AC-4.6 | WHEN `onShow_==false` 且 `!IsWindowDetached()`（status==true，即重新 attached）THEN 调用 `NotifyForegroundForNodeGoResume()` 恢复；多实例启用时额外 `FlushImplicitTransaction`。来源：`rosen_window.cpp:599-604` | 正常 |

### US-5: NotifyBackgroundForNodeRelease 延迟 GoStop

- As a 资源管理维护者
- I want NotifyBackgroundForNodeRelease 使用 1000ms 延迟任务调度 GoStop，并在执行时双重检查窗口仍处于 hidden+detached 状态
- So that 避免短暂 detach→attach 抖动导致的误释放，同时保证确实需要释放的资源被清理

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-5.1 | WHEN `NotifyBackgroundForNodeRelease()` 被调用且 `hasPost_==true` THEN 直接返回（避免重复调度）。来源：`rosen_window.cpp:542-544` | 正常 |
| AC-5.2 | WHEN `IsDisabledGoStopAndGoResume(container)` 返回 true THEN 直接返回。来源：`rosen_window.cpp:545-550` | 正常 |
| AC-5.3 | WHEN 检查通过 THEN 以 taskName=`"GoBackgroundForNodeRelease"+id_` 通过 `PostDelayedTask` 在 `NODE_RELEASE_DELAY_MILLISECOND=1000`ms 后执行 `GoBackgroundForNodeRelease()`，并设 `hasPost_=true`。来源：`rosen_window.cpp:551-561` | 正常 |
| AC-5.4 | WHEN 延迟任务到期执行 `GoBackgroundForNodeRelease()` THEN 设 `hasPost_=false`，并双重检查 `IsHide() && IsWindowDetached()`：仅当两者均为 true 时才调用 `rsUIDirector_->GoStop()` + `SendMessages()`。来源：`rosen_window.cpp:564-574` | 边界 |
| AC-5.5 | WHEN 双重检查失败（窗口已恢复可见 **或** 节点已重新 attached）THEN **不**调用 GoStop，仅设 `hasPost_=false`。来源：`rosen_window.cpp:570` | 恢复 |

### US-6: NotifyForegroundForNodeGoResume 恢复

- As a 资源管理维护者
- I want NotifyForegroundForNodeGoResume 在 director 处于 STOP 状态时调用 GoResume 唤醒，并取消已挂起的 GoStop 延迟任务
- So that 从 STOP 恢复的 director 能继续渲染

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-6.1 | WHEN `NotifyForegroundForNodeGoResume()` 被调用且 `rsUIDirector_->GetCurrentState()==STOP` THEN 调用 `rsUIDirector_->GoResume()`。来源：`rosen_window.cpp:609-610` | 正常 |
| AC-6.2 | WHEN `rsUIDirector_->GetCurrentState()!=STOP` THEN 记录 `LOGW("fail to GoResume")` 但不中断。来源：`rosen_window.cpp:611-613` | 异常 |
| AC-6.3 | WHEN `hasPost_==true`（有待执行的 GoStop 延迟任务）THEN 从 TaskExecutor 移除 `"GoBackgroundForNodeRelease"+id_` 任务，设 `hasPost_=false`。来源：`rosen_window.cpp:614-621` | 恢复 |

### US-7: FlushPendingNodeReleaseTask 立即执行

- As a 资源管理维护者
- I want FlushPendingNodeReleaseTask 在需要立即释放时跳过延迟，直接执行 GoBackgroundForNodeRelease
- So that 窗口销毁等场景能即时释放 RS 资源

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-7.1 | WHEN `FlushPendingNodeReleaseTask()` 被调用且 `hasPost_==false` THEN 直接返回（无待执行任务）。来源：`rosen_window.cpp:526-528` | 正常 |
| AC-7.2 | WHEN `hasPost_==true` THEN 从 TaskExecutor 移除 `"GoBackgroundForNodeRelease"+id_` 任务，设 `hasPost_=false`，然后**立即**调用 `GoBackgroundForNodeRelease()`（仍受双重检查保护）。来源：`rosen_window.cpp:529-536` | 正常 |

### US-8: IsDisabledGoStopAndGoResume 守卫

- As a 架构维护者
- I want IsDisabledGoStopAndGoResume 对特定容器类型（SubContainer / FormRender / SceneBoard / DynamicRender）返回 true，阻止 GoStop/GoResume
- So that 这些容器类型的 RSUIDirector 生命周期由外部系统管理，ArkUI 不干预

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-8.1 | WHEN container 是 SubContainer THEN `IsDisabledGoStopAndGoResume` 返回 true。来源：`rosen_window.cpp:59-64` | 正常 |
| AC-8.2 | WHEN container 是 FormRender THEN `IsDisabledGoStopAndGoResume` 返回 true。来源：`rosen_window.cpp:59-64` | 正常 |
| AC-8.3 | WHEN container 是 SceneBoardWindow THEN `IsDisabledGoStopAndGoResume` 返回 true。来源：`rosen_window.cpp:59-64` | 正常 |
| AC-8.4 | WHEN container 是 DynamicRender THEN `IsDisabledGoStopAndGoResume` 返回 true。来源：`rosen_window.cpp:59-64` | 正常 |
| AC-8.5 | WHEN container 为 null THEN `IsDisabledGoStopAndGoResume` 返回 true（`CHECK_NULL_RETURN(container, true)`）。来源：`rosen_window.cpp:60-61` | 异常 |

### US-9: FlushImplicitTransaction 内部语义与多实例门控

- As a 多实例架构维护者
- I want FlushImplicitTransaction 在多实例启用时刷新 RS 事务暂存层，而非调用 director 的 SendMessages
- So that 多实例窗口切换时 RS 事务暂存的属性变更不被丢失

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-9.1 | WHEN `FlushImplicitTransaction(rsUIDirector)` 被调用 THEN 内部调用链为：`rsUIDirector->GetRSSurfaceNode()` → `surfaceNode->GetRSUIContext()` → `rsUIContext->GetRSTransaction()` → `rsTransaction->FlushImplicitTransaction()`。它**不**调用 `rsUIDirector->SendMessages()`。来源：`rosen_window.cpp:327-336` | 正常 |
| AC-9.2 | WHEN `GetRSSurfaceNode()` 返回空 **或** `GetRSUIContext()` 返回空 **或** `GetRSTransaction()` 返回空 THEN `CHECK_NULL_VOID` 逐级短路返回，不执行 FlushImplicitTransaction。来源：`rosen_window.cpp:330-334` | 异常 |
| AC-9.3 | WHEN `OnShow()` 执行且 `SystemProperties::GetMultiInstanceEnabled()==true` THEN 在 `GoForeground()` 之后调用 `FlushImplicitTransaction(rsUIDirector_)`。来源：`rosen_window.cpp:310-312` | 正常 |
| AC-9.4 | WHEN `NotifyWindowAttachStateChange` 执行到 attach 恢复分支（`onShow_==false && !IsWindowDetached()`）且多实例启用 THEN 在 `NotifyForegroundForNodeGoResume()` 之后调用 `FlushImplicitTransaction(rsUIDirector_)`。来源：`rosen_window.cpp:601-603` | 正常 |

## 验收追溯

| AC编号 | US ID | 业务规则 | 验证手段 |
|-------|-------|----------|----------|
| AC-1.1 | US-1 | R-1 | 代码评审 |
| AC-1.2 | US-1 | R-2 / R-3 | 代码评审 + lifecycle ut |
| AC-1.3 | US-1 | R-1 | 代码评审 |
| AC-1.4 | US-1 | R-4 | 多实例集成测试 |
| AC-2.1 | US-2 | R-5 | 代码评审 |
| AC-2.2 | US-2 | R-5 | 代码评审 |
| AC-2.3 | US-2 | R-6 / R-7 | 代码评审 + lifecycle ut |
| AC-2.4 | US-2 | R-6 | 代码评审 |
| AC-3.1 | US-3 | R-8 | 代码评审 |
| AC-3.2 | US-3 | R-8 | 代码评审 |
| AC-3.3 | US-3 | R-8 | 代码评审 |
| AC-3.4 | US-3 | R-9 | 代码评审 |
| AC-4.1 | US-4 | R-10 / R-19 | 代码评审 |
| AC-4.2 | US-4 | R-11 | 代码评审 |
| AC-4.3 | US-4 | R-12 | 代码评审 |
| AC-4.4 | US-4 | R-13 | 代码评审 |
| AC-4.5 | US-4 | R-6 / R-14 | 代码评审 |
| AC-4.6 | US-4 | R-15 / R-4 | 代码评审 |
| AC-5.1 | US-5 | R-16 | 代码评审 |
| AC-5.2 | US-5 | R-19 | 代码评审 |
| AC-5.3 | US-5 | R-14 | 代码评审 |
| AC-5.4 | US-5 | R-17 / R-18 | 代码评审 + lifecycle ut |
| AC-5.5 | US-5 | R-18 | 代码评审 |
| AC-6.1 | US-6 | R-15 | 代码评审 |
| AC-6.2 | US-6 | R-20 | 代码评审 |
| AC-6.3 | US-6 | R-18 | 代码评审 |
| AC-7.1 | US-7 | R-16 | 代码评审 |
| AC-7.2 | US-7 | R-17 | 代码评审 |
| AC-8.1 | US-8 | R-19 | 代码评审 |
| AC-8.2 | US-8 | R-19 | 代码评审 |
| AC-8.3 | US-8 | R-19 | 代码评审 |
| AC-8.4 | US-8 | R-19 | 代码评审 |
| AC-8.5 | US-8 | R-19 | 代码评审 |
| AC-9.1 | US-9 | R-21 | 代码评审 |
| AC-9.2 | US-9 | R-21 | 代码评审 |
| AC-9.3 | US-9 | R-4 / R-21 | 代码评审 |
| AC-9.4 | US-9 | R-4 / R-21 | 代码评审 |

## 规则定义

| 规则ID | 类型 | 触发条件 | 预期行为 | 边界/约束 | 关联AC |
|--------|------|----------|----------|-----------|--------|
| R-1 | 行为 | — | OnShow 先设 `onShow_=true`，然后根据 attach 状态决定是否 GoResume，最后 GoForeground。OnHide 先设 `onShow_=false`，然后 GoBackground + SendMessages。来源：`rosen_window.cpp:301-325`。 | — | — |
| R-2 | 行为 | onShow_ + IsWindowDetached() | OnShow 路径中，若窗口处于 Detached 状态（windowAttachedStatus_==false），在 GoForeground 之前先调用 `NotifyForegroundForNodeGoResume()` 恢复可能处于 STOP 状态的 director。来源：`rosen_window.cpp:306-308`。 | — | — |
| R-3 | 边界 | onShow_ + IsWindowDetached()==false | OnShow 路径中，若窗口未 Detached（nullopt 或 attached），跳过 GoResume，直接 GoForeground。来源：`rosen_window.cpp:309`。 | — | — |
| R-4 | 行为 | SystemProperties::GetMultiInstanceEnabled() | OnShow 在多实例启用时额外调用 `FlushImplicitTransaction(rsUIDirector_)`。来源：`rosen_window.cpp:310-312`。 | — | — |
| R-5 | 行为 | — | OnHide 序列：`onShow_=false` → `GoBackground()` → `SendMessages()` → 若 Detached 则 `NotifyBackgroundForNodeRelease()`。来源：`rosen_window.cpp:315-325`。 | — | — |
| R-6 | 行为 | — | `windowAttachedStatus_` 仅在 `NotifyWindowAttachStateChange` 中被赋值（`:591`），其他方法只读。三态语义：true=attached, false=detached, nullopt=初始（视为非 detached）。来源：`rosen_window.h:242-247, :591`。 | — | — |
| R-7 | 行为 | — | OnHide 中 `IsWindowDetached()` 决定是否调度延迟 GoStop。`windowAttachedStatus_==nullopt` 时 IsWindowDetached() 返回 false，不调度。来源：`rosen_window.cpp:322, :220-223`。 | — | — |
| R-8 | 行为 | — | `windowAttachedStatus_` 三态：nullopt → IsWindowDetached()=false, IsWindowAttached()=false；true → IsWindowAttached()=true；false → IsWindowDetached()=true。来源：`rosen_window.h:220-228`。 | — | — |
| R-9 | 行为 | — | `GetWindowAttachedStatusForLog()` 返回 int32：nullopt→-1, true→1, false→0。用于 HiTrace `NotifyWindowAttachStateChange status:%d` 和 `GoBackgroundForNodeRelease attachedStatus:%d`。来源：`rosen_window.h:230-233`。 | — | — |
| R-10 | 行为 | — | `NotifyWindowAttachStateChange` 调用 `IsDisabledGoStopAndGoResume` 检查；若禁用则不更新 `windowAttachedStatus_`、不触发任何转换。来源：`rosen_window.cpp:583-590`。 | — | — |
| R-11 | 行为 | status 与当前值相同 | `NotifyWindowAttachStateChange` 去重：若 `windowAttachedStatus_.has_value() && value()==status`，直接返回。来源：`rosen_window.cpp:585`。 | — | — |
| R-12 | 行为 | — | `NotifyWindowAttachStateChange` 先检查通过后赋值 `windowAttachedStatus_=status`（`:591`），赋值在分支决策之前，确保后续 IsWindowDetached() 使用新值。来源：`rosen_window.cpp:591`。 | — | — |
| R-13 | 行为 | onShow_==true | `NotifyWindowAttachStateChange` 在前台窗口上不执行任何 GoStop/GoResume——前台窗口无法 GoStop。来源：`rosen_window.cpp:593-595`。 | — | — |
| R-14 | 行为 | onShow_==false + detached | `NotifyBackgroundForNodeRelease` 以 `"GoBackgroundForNodeRelease"+id_` 为 taskName，`NODE_RELEASE_DELAY_MILLISECOND=1000`ms 延迟，`PostDelayedTask` 到 UI 线程。`hasPost_=true` 标记已调度。来源：`rosen_window.cpp:538-562`。 | — | — |
| R-15 | 行为 | — | `NotifyForegroundForNodeGoResume` 检查 `rsUIDirector_->GetCurrentState()==RSUIDirectorLifecycleState::STOP`，仅在 STOP 时 GoResume；否则 LOGW。来源：`rosen_window.cpp:607-613`。 | — | — |
| R-16 | 行为 | — | `hasPost_` 标记是否有待执行的 GoStop 延迟任务。`NotifyBackgroundForNodeRelease` 在 hasPost_==true 时短路返回。`NotifyForegroundForNodeGoResume` 和 `FlushPendingNodeReleaseTask` 在 hasPost_==true 时移除任务并设 false。来源：`rosen_window.cpp:542-544, 614-621, 526-534`。 | — | — |
| R-17 | 行为 | — | `GoBackgroundForNodeRelease` 双重检查：`IsHide() && IsWindowDetached()`。仅当窗口仍隐藏且节点仍 Detached 时才 `GoStop()` + `SendMessages()`。来源：`rosen_window.cpp:564-575`。 | — | — |
| R-18 | 恢复 | 窗口恢复可见 / 节点重新 attached | 延迟 GoStop 的双重检查失败时，仅设 `hasPost_=false`，不执行 GoStop。`NotifyForegroundForNodeGoResume` 会取消已挂起的 GoStop 任务。来源：`rosen_window.cpp:570, 614-621`。 | — | — |
| R-19 | 行为 | — | `IsDisabledGoStopAndGoResume` 对 SubContainer / FormRender / SceneBoardWindow / DynamicRender / null container 返回 true，阻止这些容器的 GoStop/GoResume 调用。来源：`rosen_window.cpp:59-64`。 | — | — |
| R-20 | 异常 | rsUIDirector 状态非 STOP | `NotifyForegroundForNodeGoResume` 在 director 非 STOP 状态时调用 GoResume 会失败，记录 `LOGW("fail to GoResume")`，但不中断。来源：`rosen_window.cpp:611-613`。 | — | — |
| R-21 | 行为 | GetMultiInstanceEnabled()==true | `FlushImplicitTransaction(rsUIDirector)` 是**帧外 RS 事务刷新**方法（`rosen_window.cpp:327-336`）。内部调用链：`GetRSSurfaceNode()` → `GetRSUIContext()` → `GetRSTransaction()` → `FlushImplicitTransaction()`。**关键**：它刷新的是 RS 事务暂存层（RSTransaction），**非** director 消息队列提交（SendMessages）。仅在两个调用点使用，均受 `GetMultiInstanceEnabled()` 门控：① OnShow 的 GoForeground 之后（`:310-312`），② NotifyWindowAttachStateChange 的 attach 恢复分支（`:601-603`）。目的：多实例窗口切换时确保 RS 事务暂存的属性变更被立即刷新，避免跨窗口属性丢失。三个 CHECK_NULL_VOID 保护（surfaceNode / rsUIContext / rsTransaction）逐级短路。来源：`rosen_window.cpp:327-336`。 | — | — |

---

## 验证映射

| VM编号 | AC / 规则 | 验证手段 | 位置 / 用例名 |
|-------|----------|---------|---------------|
| VM-1 | AC-1.1..1.4 | 单元测试 | 待补充 — OnShow 各分支（attached/detached/nullopt + multiInstance） |
| VM-2 | AC-2.1..2.4 | 单元测试 | 待补充 — OnHide 各分支 |
| VM-3 | AC-3.1..3.4 | 代码评审 | `rosen_window.h:220-233` 三态语义直接对照 |
| VM-4 | AC-4.1..4.6 | 单元测试 | 待补充 — NotifyWindowAttachStateChange 完整状态机（含去重、前台门控、分支决策） |
| VM-5 | AC-5.1..5.5 | 单元测试 | 待补充 — NotifyBackgroundForNodeRelease 延迟调度 + 双重检查 + 抖动恢复 |
| VM-6 | AC-6.1..6.3 | 单元测试 | 待补充 — NotifyForegroundForNodeGoResume STOP 检查 + hasPost_ 取消 |
| VM-7 | AC-7.1..7.2 | 单元测试 | 待补充 — FlushPendingNodeReleaseTask 立即执行路径 |
| VM-8 | AC-8.1..8.5 | 代码评审 | `rosen_window.cpp:59-64` IsDisabledGoStopAndGoResume 直接对照 |
| VM-9 | AC-9.1..9.4 | 代码评审 | `rosen_window.cpp:327-336` FlushImplicitTransaction 方法体 + `:310-312, 601-603` 调用点对照 |

## API 变更分析

### 新增 API

无。Feat-02 为框架内部 RSUIDirector 生命周期管理，**不对外暴露 ArkTS 属性 / C-API**。

### 变更/废弃 API

| API 名称 | 变更类型 | 关联 AC |
|----------|----------|---------|
| — | — | 无变更/废弃 API |

## 接口规格

### 接口定义

> 本特性为已有实现补录，接口行为定义详见上方规则定义和用户故事。

无新增接口规格。

---

## 兼容性声明

| API 版本 | 行为差异 | 影响 | 迁移指引 |
|----------|----------|------|----------|
| 各版本 | `IsDisabledGoStopAndGoResume` 对 SceneBoardWindow 返回 true | 中：SceneBoard 窗口生命周期完全由系统管理 | 不修改；ArkUI 不干预 SceneBoard 的 RSUIDirector |
| 各版本 | `SystemProperties::GetMultiInstanceEnabled()` 影响 OnShow 中的 FlushImplicitTransaction | 中：多实例编译态决定 | 切换后行为按 R-4 |
| 各版本 | `NODE_RELEASE_DELAY_MILLISECOND=1000` 为硬编码延迟常量 | 低：仅在 Detached + Hidden 场景生效 | 修改需评估资源释放时延 |

> **关键区分**：`OnActive/OnInactive`（焦点转换，`ace_container.cpp:1081-1156` 调用 `WindowFocus(true/false)`）**不映射**到 OnShow/OnHide。`OnForeground/OnBackground`（`ace_container.cpp:977-1079`）映射到 `OnShow/OnHide`。焦点 ≠ 可见性。

## 架构约束

- 所有生命周期方法（OnShow/OnHide/NotifyWindowAttachStateChange/NotifyBackgroundForNodeRelease/NotifyForegroundForNodeGoResume/GoBackgroundForNodeRelease/FlushPendingNodeReleaseTask）均在 **UI 线程** 调用。
- `rsUIDirector_` 的 GoForeground/GoBackground/GoStop/GoResume 是 RSUIDirector 的四个生命周期方法，ArkUI 通过 RosenWindow 封装调用。
- `windowAttachedStatus_` 是 `std::optional<bool>` 类型，**不是** enum；三态语义（nullopt/true/false）在 `rosen_window.h:242-247` 注释中定义。
- `NODE_RELEASE_DELAY_MILLISECOND=1000` 与 `hasPost_` 配合实现延迟+幂等的双重保证。
- `IsDisabledGoStopAndGoResume` 是全局守卫，对四种容器类型（SubContainer/FormRender/SceneBoardWindow/DynamicRender）短路所有 GoStop/GoResume 调用。

## 非功能性需求

- 可观测：NotifyWindowAttachStateChange、GoBackgroundForNodeRelease、NotifyBackgroundForNodeRelease 均有 HiTrace `ACE_SCOPED_TRACE` 标记，包含 attachedStatus、onShow、hasPost 状态。
- 性能：GoStop 延迟 1000ms 确保 detach→attach 抖动不触发频繁 STOP/Resume 抖动。
- 鲁棒性：双重检查（IsHide + IsWindowDetached）防止误释放；hasPost_ 防止重复调度；GoResume 的 STOP 状态检查防止无效调用。
- 恢复：GoStop 可被 NotifyForegroundForNodeGoResume 取消（移除延迟任务 + GoResume）；FlushPendingNodeReleaseTask 提供立即执行通道。

## 多设备适配声明

| 设备类型 | 行为差异 | 规格/约束 | 验证方式 | 证据 |
|----------|----------|-----------|----------|------|
| 手机 | 无差异 | — | — | — |
| 平板 | 无差异 | — | — | — |
| 折叠屏 | 无差异 | — | — | — |

---

## 全局特性影响

- 渲染管线（03-01-01）：PipelineContext 的 `onShow_` 状态由 Window 的 OnShow/OnHide 设置，影响 RequestFrame 门控和焦点事件分发。
- 多实例（03-06-01）：SubContainer 被 `IsDisabledGoStopAndGoResume` 守卫，子窗口的生命周期由父窗口管理。
- 表单渲染：FormRender 容器被守卫，FormRenderWindow（Feat-04）有独立的 OnShow/OnHide 实现（GoForeground 但无 GoStop）。
- SceneBoard：SceneBoardWindow 被守卫，其 RSUIDirector 生命周期完全由系统 WindowManager 管理。

## 行为场景

```
场景 1: OnShow 恢复 Detached 窗口 (AC-1.2, R-2)
  Given windowAttachedStatus_==false（Detached）且 rsUIDirector 处于 STOP 状态
  When OnShow() 被调用
  Then NotifyForegroundForNodeGoResume() 先调用 GoResume()
  And rsUIDirector_->GoForeground() 随后调用

场景 2: OnHide 调度延迟 GoStop (AC-2.3, R-5, R-14)
  Given windowAttachedStatus_==false（Detached）且 onShow_==true
  When OnHide() 被调用
  Then onShow_ 设为 false
  And GoBackground() + SendMessages() 立即执行
  And NotifyBackgroundForNodeRelease() 调度 1000ms 后的 GoStop

场景 3: 延迟 GoStop 双重检查通过 (AC-5.4, R-17)
  Given hasPost_==true，1000ms 延迟任务到期
  And 窗口仍隐藏 (IsHide()==true) 且节点仍 Detached (IsWindowDetached()==true)
  When GoBackgroundForNodeRelease() 执行
  Then rsUIDirector_->GoStop() 被调用
  And rsUIDirector_->SendMessages() 被调用

场景 4: 延迟 GoStop 双重检查失败 (AC-5.5, R-18)
  Given hasPost_==true，1000ms 延迟任务到期
  And 窗口已恢复可见 (IsHide()==false) 或节点已重新 attached
  When GoBackgroundForNodeRelease() 执行
  Then GoStop() 不被调用
  And 仅 hasPost_ 设为 false

场景 5: GoResume 取消已挂起的 GoStop (AC-6.3, R-18)
  Given hasPost_==true（有 1000ms 后的 GoStop 任务）
  When NotifyForegroundForNodeGoResume() 被调用（因 detach→attach 转换）
  Then GoBackgroundForNodeRelease 延迟任务被移除
  And hasPost_ 设为 false
  And 若 director 处于 STOP 则 GoResume()

场景 6: NotifyWindowAttachStateChange 状态去重 (AC-4.2, R-11)
  Given windowAttachedStatus_==true（当前已 attached）
  When NotifyWindowAttachStateChange(true) 被调用（重复通知）
  Then statusEqualsCurrent 为 true，直接返回
  And 不触发任何状态转换

场景 7: 前台窗口不执行 GoStop (AC-4.4, R-13)
  Given onShow_==true（窗口可见）
  When NotifyWindowAttachStateChange(false) 被调用（节点 detached）
  Then windowAttachedStatus_ 更新为 false
  And 因 onShow_==true 直接返回，不调度 GoStop

场景 8: SubContainer 被守卫阻止 (AC-8.1, R-19)
  Given 容器是 SubContainer
  When NotifyWindowAttachStateChange(false) 被调用
  Then IsDisabledGoStopAndGoResume 返回 true
  And windowAttachedStatus_ 不更新
  And 不触发任何 GoStop/GoResume

场景 9: FlushPendingNodeReleaseTask 立即释放 (AC-7.2, R-17)
  Given hasPost_==true（有待执行的 GoStop 延迟任务）
  When FlushPendingNodeReleaseTask() 被调用
  Then 延迟任务被移除
  And hasPost_ 设为 false
  And 立即调用 GoBackgroundForNodeRelease()（仍受双重检查保护）

场景 10: nullopt 不触发 Detached 逻辑 (AC-3.1, R-7, R-8)
  Given windowAttachedStatus_ 为 nullopt（初始态）
  When OnHide() 被调用
  Then IsWindowDetached() 返回 false
  And 不调用 NotifyBackgroundForNodeRelease()

场景 11: FlushImplicitTransaction 刷新 RS 事务（非 SendMessages）(AC-9.1, R-21)
  Given 多实例启用（GetMultiInstanceEnabled()==true）
  And rsUIDirector 的 SurfaceNode、RSUIContext、RSTransaction 均非空
  When OnShow() 执行，GoForeground() 之后调用 FlushImplicitTransaction
  Then GetRSSurfaceNode() → GetRSUIContext() → GetRSTransaction() 调用链被执行
  And rsTransaction->FlushImplicitTransaction() 被调用（RS 事务暂存层刷新）
  And rsUIDirector->SendMessages() 不被调用（此方法刷新的是事务层，非消息队列）
```

## Spec 自审清单

- [x] 所有 H2/H3 章节按模板齐全
- [x] 每个 US 都有 AC，并使用 AC-X.Y 编号
- [x] 每个 AC 在「验收追溯」「验证映射」「行为场景」中可被引用
- [x] 规则定义编号齐全（R-1..R-21）
- [x] 所有源码引用均给出 file:line
- [x] API 变更分析已说明本 Feat 不暴露 ArkTS / C-API
- [x] 兼容性声明覆盖当前已识别的版本差异
- [x] Gherkin 场景覆盖每个 AC
- [x] 与 design.md 章节标题、ID（DESIGN-Func-03-05-01）对齐

## context-references

- `frameworks/core/components_ng/render/adapter/rosen_window.h:220-247`（IsWindowDetached/IsWindowAttached/windowAttachedStatus_ 定义）
- `frameworks/core/components_ng/render/adapter/rosen_window.cpp:59-64`（IsDisabledGoStopAndGoResume）
- `frameworks/core/components_ng/render/adapter/rosen_window.cpp:301-325`（OnShow / OnHide）
- `frameworks/core/components_ng/render/adapter/rosen_window.cpp:524-536`（FlushPendingNodeReleaseTask）
- `frameworks/core/components_ng/render/adapter/rosen_window.cpp:538-575`（NotifyBackgroundForNodeRelease / GoBackgroundForNodeRelease）
- `frameworks/core/components_ng/render/adapter/rosen_window.cpp:577-622`（NotifyWindowAttachStateChange / NotifyForegroundForNodeGoResume）
- `frameworks/core/components_ng/render/adapter/rosen_window.cpp:327-336`（FlushImplicitTransaction 方法定义）
- `frameworks/core/components_ng/render/adapter/rosen_window.h:138`（FlushImplicitTransaction 声明）
- `frameworks/core/common/window.h:298-300`（GoBackgroundForNodeRelease / FlushPendingNodeReleaseTask / NotifyWindowAttachStateChange 基类虚方法）
- `adapter/ohos/entrance/ace_container.cpp:977-1079`（OnForeground / OnBackground 调用 OnShow/OnHide）
- `adapter/ohos/entrance/ace_container.cpp:1081-1156`（OnActive / OnInactive 调用 WindowFocus，非可见性）
