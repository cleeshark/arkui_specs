# 特性规格

> Func-04-04-06-Feat-03 手势判定：固化 GestureReferee 仲裁机制的行为规格，包括 GestureScope 管理、Adjudicate 流程、优先级解决、阻塞/解除阻塞、Delay 延迟接受和 Bridge Mode。仅 NG 框架，框架内部能力。

## 概述

| 属性 | 值 |
|------|-----|
| 特性名称 | 手势判定 (GestureReferee) |
| 特性编号 | Func-04-04-06-Feat-03 |
| 所属 Epic | 无（已有能力补录） |
| 优先级 | P1 |
| 目标版本 | 框架内部能力（无独立 API 版本） |
| SIG 归属 | ArkUI SIG |
| 状态 | Draft |
| 复杂度 | 复杂 |

## 本次变更范围（Delta）

> 历史规格补齐，补录已有实现的完整行为规格。

## 输入文档

| 文档 | 路径 | 状态 |
|------|------|------|
| Design | `specs/04-common-capability/04-common-events/06-gesture-capability/design.md` | Baselined |
| Feat-01 基础手势 | `specs/04-common-capability/04-common-events/06-gesture-capability/Feat-01-basic-gestures-spec.md` | Baselined |
| Feat-02 组合手势 | `specs/04-common-capability/04-common-events/06-gesture-capability/Feat-02-gesture-group-spec.md` | Baselined |

> GestureReferee 是框架内部仲裁机制，无独立 SDK API。开发者的可观测行为通过 Feat-01（手势挂载 API + GesturePriority/GestureMask）和 Feat-02（组合模式行为）间接体现。

---

## 用户故事

### US-1: 手势竞争仲裁（Adjudicate）

**作为** 手势框架,
**我想要** 通过 GestureReferee 在多个竞争的手势识别器中做出唯一判定,
**以便** 同一触摸事件序列中仅一个手势最终获胜。

**验收标准：**

- **AC-1.1:** WHEN 识别器调用 `Adjudicate(recognizer, ACCEPT)` THEN Referee 检查所有 scope 是否需要阻塞该识别器；若无阻塞则调用 `AboutToAccept()` 并通知所有 scope 执行 `OnAcceptGesture()`
- **AC-1.2:** WHEN `OnAcceptGesture()` 在 scope 中执行 THEN 接受的识别器被标记为 SUCCEED，同一 scope 内所有其他识别器被 `OnRejected()`（winner-takes-all）
- **AC-1.3:** WHEN 识别器调用 `Adjudicate(recognizer, REJECT)` 且该识别器之前为 PENDING 状态 THEN Referee 搜索所有 scope 寻找被阻塞的识别器进行解除阻塞
- **AC-1.4:** WHEN 识别器调用 `Adjudicate(recognizer, PENDING)` THEN Referee 检查所有 scope 的阻塞条件；若无阻塞则调用 `OnPending()`
- **AC-1.5:** WHEN 识别器已被标记为 FAIL 状态 THEN `HandleRejectDisposal` 直接返回，不做处理
- **AC-1.6:** WHEN 识别器已被标记为 SUCCEED 状态 THEN `HandleAcceptDisposal` 直接返回，不做处理

### US-2: GestureScope 管理

**作为** 手势框架,
**我想要** 通过 GestureScope 为每个 touchId 维护独立的竞争识别器集合,
**以便** 多指触摸时各手指的手势判定互不干扰。

**验收标准：**

- **AC-2.1:** WHEN EventManager 调用 `AddGestureToScope(touchId, result)` THEN 为该 touchId 创建或复用 GestureScope，将 hit test 结果中的识别器加入 scope
- **AC-2.2:** WHEN `AddMember()` 发现识别器已存在于 scope THEN 跳过不重复添加（Existed() 检查）
- **AC-2.3:** WHEN 触摸事件为 UP 或 CANCEL THEN EventManager 调用 `CleanGestureScope(touchId)` 关闭并移除该 scope
- **AC-2.4:** WHEN scope 关闭时仍有 PENDING 状态的识别器 THEN 设置 `isDelay_=true`（延迟关闭），不立即移除 scope
- **AC-2.5:** WHEN 多指触摸 THEN 每个 fingerId 对应独立的 GestureScope，各自维护 `recognizers_` 列表和 `hasGestureAccepted_` 标记

### US-3: 阻塞判定（CheckNeedBlocked）

**作为** 手势框架,
**我想要** 通过 CheckNeedBlocked 决定识别器是否应被阻塞,
**以便** 仅一个识别器可以进入 PENDING 或 SUCCEED 状态。

**验收标准：**

- **AC-3.1:** WHEN scope 中已有其他识别器处于 PENDING 状态 THEN 后续请求 ACCEPT/PENDING 的识别器被阻塞（返回 true）
- **AC-3.2:** WHEN scope 中无 PENDING 状态的识别器 THEN 不阻塞（返回 false）
- **AC-3.3:** WHEN 被检查的识别器与 PENDING 识别器处于同一 GestureGroup 层级 THEN 不阻塞（通过 gestureGroup_ 链向上遍历判定）
- **AC-3.4:** WHEN Referee 处理 ACCEPT/PENDING 时 THEN 遍历所有 scope 检查阻塞条件（跨 scope 检查）
- **AC-3.5:** WHEN 识别器被阻塞 THEN 调用 `OnBlocked()` 进入 PENDING_BLOCKED 或 SUCCEED_BLOCKED 状态

### US-4: 解除阻塞（UnBlockGesture）

**作为** 手势框架,
**我想要** 当 PENDING 识别器被拒绝后解除等待中的阻塞识别器,
**以便** 其他识别器有机会继续竞争。

**验收标准：**

- **AC-4.1:** WHEN PENDING 识别器被 REJECT THEN Referee 搜索所有 scope 查找 PENDING_BLOCKED 或 SUCCEED_BLOCKED 的识别器
- **AC-4.2:** WHEN 找到 PENDING_BLOCKED 识别器 THEN 调用 `OnPending()` 将其转为 PENDING
- **AC-4.3:** WHEN 找到 SUCCEED_BLOCKED 识别器 THEN 调用 `AboutToAccept()` 并通知所有 scope 执行 `OnAcceptGesture()`
- **AC-4.4:** WHEN 所有 scope 中无可解除阻塞的识别器 THEN 不做额外操作

### US-5: BatchAdjudicate 分层路由

**作为** 手势框架,
**我想要** 识别器的仲裁请求先经过父 Group 再到达 Referee,
**以便** GestureGroup 内部的仲裁由 Group 自行处理。

**验收标准：**

- **AC-5.1:** WHEN 识别器属于某个 GestureGroup（eventImportGestureGroup_ 或 gestureGroup_ 有效）THEN `BatchAdjudicate` 将仲裁请求路由给父 Group
- **AC-5.2:** WHEN 识别器无父 Group（根级识别器）THEN `BatchAdjudicate` 获取 `GetCurrentGestureReferee()` 将仲裁请求路由给 GestureReferee
- **AC-5.3:** WHEN 无可用 referee THEN `BatchAdjudicate` 直接调用 `OnRejected()` 拒绝该识别器

### US-6: Delay 延迟接受机制

**作为** 手势框架,
**我想要** 通过 RecognizerDelayStatus 延迟内嵌容器中手势的接受判定,
**以便** 外层容器有机会优先处理手势。

**验收标准：**

- **AC-6.1:** WHEN `recognizerDelayStatus_==START` 且识别器位于内嵌容器中 THEN `HandleAcceptDisposal` 不立即接受，存储到 `delayRecognizer_`
- **AC-6.2:** WHEN `SetRecognizerDelayStatus(END)` 被调用 THEN 执行 `RecallOnAcceptGesture()` 处理延迟的识别器
- **AC-6.3:** WHEN delay 状态为 START 且无内嵌容器识别器请求接受 THEN 正常处理外部识别器的接受请求

### US-7: Bridge Mode

**作为** 手势框架,
**我想要** 某些识别器以 Bridge Mode 运行,
**以便** 它们不参与正常竞争且不会被其他手势获胜时拒绝。

**验收标准：**

- **AC-7.1:** WHEN `OnAcceptGesture()` 在 scope 中拒绝其他识别器 THEN 跳过 Bridge Mode 的识别器（不调用 OnRejected）
- **AC-7.2:** WHEN 识别器处于 Bridge Mode THEN `HandleEvent()` 中直接返回 true，不处理触摸事件
- **AC-7.3:** WHEN 识别器设置 Bridge Mode THEN `bridgeMode_` 标志为 true

---

## 验收追溯

| AC | 关联规则 | 关联 Task | 验证方式 | 证据 |
|----|----------|-----------|----------|------|
| AC-1.1~1.6 | BR-1, BR-2, FR-1~FR-6 | 已有实现 | 单测 | `test/unittest/core/gestures/gesture_referee_test_ng.cpp` |
| AC-2.1~2.5 | BR-3, FR-7~FR-11 | 已有实现 | 单测 | 同上 |
| AC-3.1~3.5 | BR-4, FR-12~FR-15 | 已有实现 | 单测 | 同上 |
| AC-4.1~4.4 | BR-5, FR-16~FR-19 | 已有实现 | 单测 | 同上 |
| AC-5.1~5.3 | BR-6, FR-20~FR-22 | 已有实现 | 单测 | 同上 |
| AC-6.1~6.3 | BR-7, FR-23~FR-25 | 已有实现 | 单测 | 同上 |
| AC-7.1~7.3 | BR-8, FR-26~FR-28 | 已有实现 | 单测 | 同上 |

---

## 业务规则

| 编号 | 规则描述 | 约束条件 | 关联 AC |
|------|----------|----------|---------|
| BR-1 | 每个 scope 内仅一个识别器可获胜（winner-takes-all） | `OnAcceptGesture()` 拒绝所有其他识别器 | AC-1.2 |
| BR-2 | Referee 跨所有 scope 检查阻塞条件 | `HandleAcceptDisposal` 和 `HandlePendingDisposal` 遍历 gestureScopes_ | AC-1.1, AC-1.4 |
| BR-3 | 每个 touchId 有独立的 GestureScope | gestureScopes_ 为 unordered_map<touchId, GestureScope> | AC-2.1~2.5 |
| BR-4 | 同一 GestureGroup 内的识别器不互相阻塞 | CheckNeedBlocked 通过 gestureGroup_ 链判定 | AC-3.3 |
| BR-5 | PENDING 识别器拒绝后级联解除阻塞 | HandleRejectDisposal 搜索所有 scope | AC-4.1~4.4 |
| BR-6 | 识别器仲裁请求先路由给父 Group 再到 Referee | BatchAdjudicate 优先检查 eventImportGestureGroup_ | AC-5.1~5.3 |
| BR-7 | Delay 机制仅影响内嵌容器中的识别器 | recognizerDelayStatus_ 和 CheckRecognizerInInnerContainer | AC-6.1~6.3 |
| BR-8 | Bridge Mode 识别器不参与竞争且不被拒绝 | OnAcceptGesture 跳过 bridgeMode_ 识别器 | AC-7.1~7.3 |

---

## 功能规则

| 编号 | 规则描述 | 触发条件 | 作用对象 | 关联 AC |
|------|----------|----------|----------|---------|
| FR-1 | HandleAcceptDisposal 检查 delay 状态，若 START 且识别器在内嵌容器中则存储到 delayRecognizer_ 不立即处理 | ACCEPT 仲裁请求 | GestureReferee | AC-1.1, AC-6.1 |
| FR-2 | HandleAcceptDisposal 遍历所有 scope 调用 CheckNeedBlocked，任一 scope 返回 true 则调用 OnBlocked() | ACCEPT 仲裁请求 | GestureReferee | AC-1.1, AC-3.4 |
| FR-3 | HandleAcceptDisposal 无阻塞时调用 AboutToAccept() 后通知所有 scope 执行 OnAcceptGesture() | ACCEPT 且无阻塞 | GestureReferee | AC-1.1 |
| FR-4 | OnAcceptGesture 标记 hasGestureAccepted_=true，遍历 recognizers_ 调用非自身非 bridge 识别器的 OnRejected() | scope 接受通知 | GestureScope | AC-1.2 |
| FR-5 | HandleRejectDisposal 调用 OnRejected() 后，仅当之前状态为 PENDING 时搜索 UnBlockGesture | REJECT 仲裁请求 | GestureReferee | AC-1.3 |
| FR-6 | HandlePendingDisposal 遍历所有 scope 检查阻塞，无阻塞则调用 OnPending() | PENDING 仲裁请求 | GestureReferee | AC-1.4 |
| FR-7 | AddGestureToScope 为 touchId 查找或创建 GestureScope，将 hit test 结果中的 NGGestureRecognizer 加入 | 触摸测试完成 | GestureReferee | AC-2.1 |
| FR-8 | AddMember 调用 Existed() 检查重复，不存在则 emplace_back | 新识别器注册 | GestureScope | AC-2.2 |
| FR-9 | CleanGestureScope 在 UP/CANCEL 时关闭 scope 并从 gestureScopes_ 移除 | 触摸事件结束 | GestureReferee | AC-2.3 |
| FR-10 | CleanGestureScope 在 scope 仍有 PENDING 时设置 isDelay_=true 不移除 | 延迟关闭 | GestureReferee | AC-2.4 |
| FR-11 | 多指触摸时各 touchId 对应独立的 GestureScope 实例 | 多指触摸 | GestureReferee | AC-2.5 |
| FR-12 | CheckNeedBlocked 遍历 scope 中所有识别器，找到非自身的 PENDING 识别器则返回 true | 阻塞检查 | GestureScope | AC-3.1 |
| FR-13 | CheckNeedBlocked 在无 PENDING 识别器时返回 false | 无竞争 | GestureScope | AC-3.2 |
| FR-14 | CheckNeedBlocked 通过 gestureGroup_ 链向上遍历，若 PENDING 识别器与被检查识别器在同一 group 层级则返回 false | 同组识别器 | GestureScope | AC-3.3 |
| FR-15 | 被阻塞的识别器调用 OnBlocked() 进入 PENDING_BLOCKED 或 SUCCEED_BLOCKED 状态 | 阻塞判定通过 | GestureScope | AC-3.5 |
| FR-16 | HandleRejectDisposal 在 PENDING 识别器拒绝后遍历所有 scope 调用 UnBlockGesture() | PENDING→REJECT | GestureReferee | AC-4.1 |
| FR-17 | UnBlockGesture 返回 PENDING_BLOCKED 识别器时调用 OnPending() | 解除阻塞（PENDING） | GestureReferee | AC-4.2 |
| FR-18 | UnBlockGesture 返回 SUCCEED_BLOCKED 识别器时调用 AboutToAccept() 并通知所有 scope | 解除阻塞（SUCCEED） | GestureReferee | AC-4.3 |
| FR-19 | 所有 scope 中无 PENDING_BLOCKED/SUCCEED_BLOCKED 识别器时 UnBlockGesture 返回 nullptr | 无可解除阻塞 | GestureScope | AC-4.4 |
| FR-20 | BatchAdjudicate 优先检查 eventImportGestureGroup_，有效则路由给父 Group | 有父 Group | NGGestureRecognizer | AC-5.1 |
| FR-21 | BatchAdjudicate 在无父 Group 时获取 GetCurrentGestureReferee() 路由给 Referee | 根级识别器 | NGGestureRecognizer | AC-5.2 |
| FR-22 | BatchAdjudicate 在无可用 referee 时直接调用 OnRejected() | 无 referee | NGGestureRecognizer | AC-5.3 |
| FR-23 | HandleAcceptDisposal 在 recognizerDelayStatus_==START 且识别器在内嵌容器中时存储到 delayRecognizer_ | delay START | GestureReferee | AC-6.1 |
| FR-24 | SetRecognizerDelayStatus(END) 触发 RecallOnAcceptGesture() 处理延迟的识别器 | delay END | GestureReferee | AC-6.2 |
| FR-25 | delay 状态为 START 但无内嵌容器识别器请求时正常处理外部识别器 | delay START 但无内嵌 | GestureReferee | AC-6.3 |
| FR-26 | OnAcceptGesture 在拒绝其他识别器时跳过 bridgeMode_=true 的识别器 | 手势获胜 | GestureScope | AC-7.1 |
| FR-27 | HandleEvent 在 bridgeMode_=true 时直接返回 true | 事件到达 | NGGestureRecognizer | AC-7.2 |
| FR-28 | 设置 Bridge Mode 时 bridgeMode_ 标志为 true | 外部设置 | NGGestureRecognizer | AC-7.3 |

---

## 异常/豁免规则

| 编号 | 规则描述 | 触发条件 | 处理结果 | 关联 AC |
|------|----------|----------|----------|---------|
| EX-1 | 识别器已被 FAIL | HandleRejectDisposal 发现 RefereeState==FAIL | 直接返回，不做处理 | AC-1.5 |
| EX-2 | 识别器已被 SUCCEED | HandleAcceptDisposal 发现 RefereeState==SUCCEED | 直接返回，不做处理 | AC-1.6 |
| EX-3 | Scope 延迟关闭 | CleanGestureScope 时 scope 仍有 PENDING 识别器 | 设置 isDelay_=true，scope 保留在 gestureScopes_ 中 | AC-2.4 |
| EX-4 | 无可用 Referee | BatchAdjudicate 找不到 GetCurrentGestureReferee | 直接 OnRejected() | AC-5.3 |
| EX-5 | Bridge Mode 识别器被跳过 | OnAcceptGesture 拒绝其他识别器 | 不调用 OnRejected，保留识别器状态 | AC-7.1 |

---

## 恢复契约

| 编号 | 触发条件 | 恢复策略 | 恢复结果 | 约束 |
|------|----------|----------|----------|------|
| RC-1 | PENDING 识别器被 REJECT | 搜索所有 scope 的 UnBlockGesture | 解除第一个阻塞识别器的阻塞状态 | 仅当之前为 PENDING |
| RC-2 | Scope 延迟关闭 | 等待识别器完成判定后关闭 | PENDING 识别器最终判定后 scope 被清理 | 由 EventManager 在 UP/CANCEL 时触发 |
| RC-3 | Delay 接受 | SetRecognizerDelayStatus(END) | RecallOnAcceptGesture 处理延迟的识别器 | 需要外部触发 END |
| RC-4 | 无 Referee 可用 | 直接 OnRejected() | 识别器被拒绝，可被新触摸序列重新激活 | 不可逆 |

---

## 验证映射

| 编号 | 对应规格项 | 验证方式 | 验证重点 |
|------|------------|----------|----------|
| VM-1 | FR-1~FR-6, AC-1.1~1.6 | 单测 | Adjudicate 三种 disposal 处理流程 |
| VM-2 | FR-7~FR-11, AC-2.1~2.5 | 单测 | GestureScope 生命周期管理 |
| VM-3 | FR-12~FR-15, AC-3.1~3.5 | 单测 | CheckNeedBlocked 阻塞判定 + Group 豁免 |
| VM-4 | FR-16~FR-19, AC-4.1~4.4 | 单测 | UnBlockGesture 解除阻塞 |
| VM-5 | FR-20~FR-22, AC-5.1~5.3 | 单测 | BatchAdjudicate 分层路由 |
| VM-6 | FR-23~FR-25, AC-6.1~6.3 | 单测 | Delay 延迟接受机制 |
| VM-7 | FR-26~FR-28, AC-7.1~7.3 | 单测 | Bridge Mode 行为 |
| VM-8 | 全量 | 集成测试 | 端到手势竞争场景 |

---

## API 变更分析

### 新增 API

| API 签名 | 类型 | 功能描述 | 关联 AC |
|----------|------|----------|---------|
| `GestureReferee::Adjudicate(recognizer, disposal)` | Internal | 仲裁入口，分发 ACCEPT/PENDING/REJECT | AC-1.1~1.6 |
| `GestureReferee::AddGestureToScope(touchId, result)` | Internal | 注册识别器到 scope | AC-2.1 |
| `GestureReferee::CleanGestureScope(touchId)` | Internal | 关闭并移除 scope | AC-2.3 |
| `GestureScope::CheckNeedBlocked(recognizer)` | Internal | 检查是否需要阻塞 | AC-3.1~3.5 |
| `GestureScope::OnAcceptGesture(recognizer)` | Internal | 接受手势并拒绝其他 | AC-1.2 |
| `GestureScope::UnBlockGesture()` | Internal | 查找可解除阻塞的识别器 | AC-4.1~4.4 |
| `NGGestureRecognizer::BatchAdjudicate(recognizer, disposal)` | Internal | 分层路由仲裁请求 | AC-5.1~5.3 |
| `GestureReferee::SetRecognizerDelayStatus(status)` | Internal | 设置延迟接受状态 | AC-6.1~6.3 |

### 变更/废弃 API

| API 名称 | 变更类型 | 关联 AC |
|----------|----------|---------|
| — | — | 无变更/废弃 API（框架内部能力） |

---

## 兼容性声明

- **已有 API 行为变更:** 否（框架内部能力，无外部 API）
- **配置文件格式变更:** 否
- **数据存储格式变更:** 否
- **最低支持版本:** 框架内部，随 NG 框架引入
- **API 版本号策略:** N/A

---

## 架构约束

| 关键约束 | 约束说明 | 影响 AC |
|----------|----------|---------|
| 无外部 API | GestureReferee 是框架内部能力，开发者通过 GesturePriority/GestureMask 间接控制 | 全部 |
| Scope-per-touchId | 每个 touchId 有独立 scope，但阻塞检查跨所有 scope | AC-2.1~2.5, AC-3.4 |
| BatchAdjudicate 层级路由 | 识别器先找父 Group，Group 内部自行仲裁，仅根级到达 Referee | AC-5.1~5.3 |
| UI 线程同步 | 仲裁在 UI 线程同步执行 | 全部 |
| Group 层级豁免 | 同一 GestureGroup 内的识别器不互相阻塞 | AC-3.3 |

> 架构规则适用性及设计方案见 design.md。

---

## 非功能性需求

| 类型 | 指标/阈值 | 验证方式 | 证据 |
|------|-----------|----------|------|
| 性能 | 单次 Adjudicate 调用（含 scope 遍历）< 10μs | benchmark | — |
| 内存 | 每个 GestureScope < 128 字节（不含识别器列表） | hidumper | — |
| 安全 | N/A — 框架内部能力 | — | — |
| 可靠性 | Scope 延迟关闭确保 PENDING 识别器不丢失 | 单测 | RC-2 |
| 问题定位 | GestureEvent 通过 AddGestureProcedure 记录仲裁过程 | 日志 | — |

---

## 全局特性影响

| 特性 | 适用？ | 结论 | 关联场景 |
|------|--------|------|----------|
| 无障碍 | N/A | 框架内部能力 | — |
| 大字体 | N/A | 框架内部能力 | — |
| 深色模式 | N/A | 框架内部能力 | — |
| 多窗口/分屏 | 是 | 分屏后各窗口有独立 EventManager，仲裁互不干扰 | 多窗口下手势竞争正确 |
| 多用户 | N/A | 框架内部能力 | — |
| 版本升级 | N/A | 框架内部能力，无 API 版本 | — |
| 生态兼容 | N/A | 框架内部能力 | — |

---

## 行为场景（可选，Gherkin）

```gherkin
Feature: 手势判定仲裁
  作为 手势框架
  我想要 通过 GestureReferee 在竞争的手势识别器中做出唯一判定
  以便 同一触摸事件序列中仅一个手势最终获胜

  # ─── Adjudicate 流程 ────────────────────────────

  Scenario: 两个手势竞争-先到先得
    Given 同一 scope 中有 TapGesture 和 LongPressGesture 两个识别器
    When TapGesture 先请求 PENDING
    Then LongPressGesture 请求 PENDING 时被阻塞（CheckNeedBlocked=true）
    And LongPressGesture 进入 PENDING_BLOCKED 状态

  Scenario: 手势获胜-拒绝其他
    Given 同一 scope 中有 TapGesture 和 LongPressGesture
    When TapGesture 请求 ACCEPT
    Then TapGesture 调用 AboutToAccept() 后 scope 执行 OnAcceptGesture
    And LongPressGesture 被 OnRejected()

  Scenario: PENDING 手势拒绝-解除阻塞
    Given 同一 scope 中 PanGesture 为 PENDING，TapGesture 为 PENDING_BLOCKED
    When PanGesture 请求 REJECT
    Then Referee 搜索 scope 调用 UnBlockGesture
    And TapGesture 从 PENDING_BLOCKED 解除为 PENDING

  # ─── GestureScope 管理 ──────────────────────────

  Scenario: 多指触摸独立 scope
    Given 用户使用 3 指触摸
    Then Referee 为 fingerId=0, 1, 2 各创建独立 GestureScope
    And 各 scope 的仲裁互不影响

  Scenario: scope 延迟关闭
    Given touchId=0 的 scope 中 PanGesture 处于 PENDING 状态
    When 用户手指抬起（UP 事件）
    Then scope 设置 isDelay_=true（延迟关闭）
    And scope 保留在 gestureScopes_ 中直到 PanGesture 完成判定

  # ─── Group 层级豁免 ────────────────────────────

  Scenario: 同 Group 内不互相阻塞
    Given ExclusiveRecognizer 内部有 TapGesture 和 LongPressGesture
    When TapGesture 请求 PENDING
    Then LongPressGesture 请求 PENDING 时 CheckNeedBlocked 返回 false
    （因为两者在同一 GestureGroup 层级，通过 gestureGroup_ 链判定豁免）

  Scenario: 不同 Group 互相阻塞
    Given 组件上直接挂载了 TapGesture，同时子组件上挂载了 LongPressGesture
    When TapGesture 请求 PENDING
    Then LongPressGesture 请求 PENDING 时被阻塞（不同 Group）

  # ─── BatchAdjudicate 路由 ────────────────────────

  Scenario: 子识别器路由给父 Group
    Given ExclusiveRecognizer 内的 TapGesture 请求 ACCEPT
    When BatchAdjudicate 检查发现 gestureGroup_ 指向 ExclusiveRecognizer
    Then 仲裁请求路由给 ExclusiveRecognizer.Adjudicate()
    And 不直接到达 GestureReferee

  Scenario: 根级识别器路由给 Referee
    Given 组件上直接挂载的 TapGesture 请求 ACCEPT
    When BatchAdjudicate 检查发现无父 Group
    Then 仲裁请求路由给 GestureReferee.Adjudicate()

  # ─── Delay 延迟接受 ─────────────────────────────

  Scenario: 内嵌容器手势延迟接受
    Given recognizerDelayStatus_=START
    And 内嵌容器中的 PanGesture 请求 ACCEPT
    Then Referee 将 PanGesture 存储到 delayRecognizer_
    And 不立即调用 AboutToAccept()

  Scenario: delay 结束后处理延迟手势
    Given delayRecognizer_ 中存储了 PanGesture
    When SetRecognizerDelayStatus(END) 被调用
    Then RecallOnAcceptGesture() 处理 PanGesture 的延迟接受

  # ─── Bridge Mode ────────────────────────────────

  Scenario: Bridge Mode 识别器不被拒绝
    Given 同一 scope 中有正常 TapGesture 和 Bridge Mode PanGesture
    When TapGesture 请求 ACCEPT 并获胜
    Then PanGesture 不被 OnRejected()（Bridge Mode 被跳过）
```

---

## Spec 自审清单

- [x] 无"待定""TBD""TODO"等占位符
- [x] 所有 AC 使用 WHEN/THEN 格式，可独立测试
- [x] 范围边界明确（GestureReferee 仲裁机制；不含 GestureEventHub 触摸测试收集、组件级手势注册）
- [x] 无语义模糊表述
- [x] AC 与业务规则/异常规则/恢复契约交叉一致

---

## context-references

```yaml
context-queries:
  - repo: "openharmony/ace_engine"
    query: "GestureReferee Adjudicate HandleAcceptDisposal HandleRejectDisposal GestureScope"
  - repo: "openharmony/ace_engine"
    query: "GestureScope CheckNeedBlocked OnAcceptGesture UnBlockGesture gestureGroup hierarchy"
  - repo: "openharmony/ace_engine"
    query: "NGGestureRecognizer BatchAdjudicate gestureGroup eventImportGestureGroup"
  - repo: "openharmony/ace_engine"
    query: "RecognizerDelayStatus delayRecognizer RecallOnAcceptGesture bridgeMode"
  - repo: "openharmony/ace_engine"
    query: "EventManager ProcessTouchTestWithReferee AddGestureToScope CleanGestureScope"
```

**关键文档：**
- 架构设计：`specs/04-common-capability/04-common-events/06-gesture-capability/design.md`
