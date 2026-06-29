# 特性规格

> Func-04-04-06-Feat-02 组合手势：固化 GestureGroup 三种组合模式（Sequential/Parallel/Exclusive）的行为规格。仅 NG 框架，不含 C-API。

## 概述

| 属性 | 值 |
|------|-----|
| 特性名称 | 组合手势 (GestureGroup) |
| 特性编号 | Func-04-04-06-Feat-02 |
| 所属 Epic | 无（已有能力补录） |
| 优先级 | P1 |
| 目标版本 | API 8 |
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

---

## 用户故事

### US-1: 顺序组合手势（Sequential）

**作为** 应用开发者,
**我想要** 通过 GestureGroup(GestureMode.Sequence, ...) 将多个手势按顺序组合,
**以便** 用户必须依次完成所有手势才算成功（如先长按再拖动）。

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-1.1 | WHEN 创建 `GestureGroup(GestureMode.Sequence, gesture1, gesture2, ...)` THEN 手势按顺序识别，第一个手势成功后自动开始第二个 | 正常 |
| AC-1.2 | WHEN 序列中某个手势识别失败 THEN 整个序列立即失败，后续手势不再识别，触发 onCancel 回调 | 异常 |
| AC-1.3 | WHEN 序列中最后一个手势成功 THEN 整个序列成功 | 正常 |
| AC-1.4 | WHEN 两个手势之间间隔超过 SEQUENCE_GESTURE_TIMEOUT(300ms) THEN 序列超时失败，触发 onCancel 回调 | 异常 |
| AC-1.5 | WHEN 前一个手势成功后 THEN 自动向下一个手势发送合成的 TouchDown 事件（事件传递机制） | 正常 |
| AC-1.6 | WHEN 序列中包含两个连续的 LongPressGesture THEN 事件传递时自动调整时间戳（beforeDuration），确保第二个 LongPress 不立即触发 | 正常 |
| AC-1.7 | WHEN 序列处于 PENDING 状态并收到 TouchCancel THEN 整个序列失败 | 异常 |
| AC-1.8 | WHEN 手势序列超时或失败后 THEN currentIndex_ 重置为 0，所有子识别器状态重置为 READY | 异常 |

### US-2: 并行组合手势（Parallel）

**作为** 应用开发者,
**我想要** 通过 GestureGroup(GestureMode.Parallel, ...) 将多个手势并行组合,
**以便** 多个手势可同时独立识别，互不影响。

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-2.1 | WHEN 创建 `GestureGroup(GestureMode.Parallel, gesture1, gesture2, ...)` THEN 所有子手势同时接收触摸事件 | 正常 |
| AC-2.2 | WHEN 一个子手势成功 THEN 不影响其他子手势的识别（多个手势可同时处于 SUCCEED 状态） | 正常 |
| AC-2.3 | WHEN 所有子手势均失败 THEN 整个并行组失败 | 异常 |
| AC-2.4 | WHEN 并行组被外部接受 THEN 当前请求接受的子手势和所有已被阻塞但成功的子手势（succeedBlockRecognizers_）均被接受 | 正常 |
| AC-2.5 | WHEN 并行组被外部拒绝 THEN 所有子手势被拒绝（ForceReject 递归执行） | 正常 |
| AC-2.6 | WHEN 一个子手势成功但并行组整体被阻塞（SUCCEED_BLOCKED）THEN 该子手势被加入 succeedBlockRecognizers_ 等待后续批量接受 | 正常 |

### US-3: 互斥组合手势（Exclusive）

**作为** 应用开发者,
**我想要** 通过 GestureGroup(GestureMode.Exclusive, ...) 将多个手势互斥组合,
**以便** 仅第一个成功的手势生效，其他手势自动失败。

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-3.1 | WHEN 创建 `GestureGroup(GestureMode.Exclusive, gesture1, gesture2, ...)` THEN 所有子手势同时接收初始触摸事件（竞争阶段） | 边界 |
| AC-3.2 | WHEN 一个子手势进入 PENDING 状态 THEN 它成为 activeRecognizer_，其他子手势被阻塞（CheckNeedBlocked） | 正常 |
| AC-3.3 | WHEN activeRecognizer_ 识别成功 THEN 它被接受，所有其他子手势被拒绝（ForceReject） | 正常 |
| AC-3.4 | WHEN activeRecognizer_ 识别失败 THEN 系统尝试解除其他被阻塞的手势（UnBlockGesture）继续竞争 | 异常 |
| AC-3.5 | WHEN 被阻塞的手势中有 SUCCEED_BLOCKED 状态的 THEN 解除阻塞后直接请求组接受，无需重新识别 | 正常 |
| AC-3.6 | WHEN 所有子手势均失败且无可解除阻塞的手势 THEN 整个互斥组失败 | 异常 |
| AC-3.7 | WHEN activeRecognizer_ 已选中后 THEN 后续 MOVE/DOWN 事件仅分发给 activeRecognizer_（不再广播） | 正常 |
| AC-3.8 | WHEN UP/CANCEL 事件到达 THEN 始终分发给所有子手势（用于清理状态） | 正常 |

### US-4: onCancel 回调

**作为** 应用开发者,
**我想要** 通过 .onCancel() 为 GestureGroup 设置取消回调,
**以便** 在手势组合被取消时得到通知。

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-4.1 | WHEN 设置 `.onCancel(() => {...})` THEN 仅在 Sequence 模式中生效（Parallel 和 Exclusive 模式不触发 onCancel） | 边界 |
| AC-4.2 | WHEN 序列中某个手势失败导致整个序列失败 THEN 触发 onCancel 回调 | 异常 |
| AC-4.3 | WHEN 序列超时（300ms）THEN 触发 onCancel 回调 | 边界 |
| AC-4.4 | WHEN 序列在 PENDING 状态被重置（ResetStatusOnFinish）THEN 触发 onCancel 回调 | 正常 |

### US-5: GestureGroup 嵌套

**作为** 应用开发者,
**我想要** 在 GestureGroup 中嵌套包含另一个 GestureGroup,
**以便** 构建复杂的多层手势组合逻辑。

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-5.1 | WHEN 在 GestureGroup 的子手势中包含另一个 GestureGroup THEN 嵌套组合正确工作，子 Group 作为整体参与父 Group 的竞争/协作 | 边界 |
| AC-5.2 | WHEN 对嵌套 Group 执行 RemoveChildrenByTag THEN 递归搜索并删除所有层级中匹配的子手势 | 正常 |
| AC-5.3 | WHEN 父 Group 被拒绝（ForceReject）THEN 递归拒绝所有子 Group 中的手势 | 正常 |
| AC-5.4 | WHEN 嵌套 Group 中的子 Group 请求仲裁 THEN 通过 GroupAdjudicate 向上传递到父 Group | 正常 |

---

## 验收追溯

| AC | 关联规则 | 关联 Task | 验证方式 | 证据 |
|----|----------|-----------|----------|------|
| AC-1.1~1.8 | R-1, R-2, R-7~R-14, R-35~R-37 | 已有实现 | 单测/XTS | `test/unittest/core/gestures/` |
| AC-2.1~2.6 | R-1, R-3, R-15~R-20 | 已有实现 | 单测/XTS | 同上 |
| AC-3.1~3.8 | R-1, R-4, R-21~R-28 | 已有实现 | 单测/XTS | 同上 |
| AC-4.1~4.4 | R-5, R-29~R-31 | 已有实现 | 单测 | 同上 |
| AC-5.1~5.4 | R-6, R-32~R-34 | 已有实现 | 单测/集成 | 同上 |


## 规则定义

> **统一规则表，取消 FR/BR/EX/RC 四分类。** 类型标签：**行为**（正常路径下的系统行为）、**边界**（输入/状态的临界点）、**异常**（非法输入或异常状态的处理）、**恢复**（系统异常后的恢复策略）。

| 规则ID | 类型 | 触发条件 | 预期行为 | 边界/约束 | 关联AC |
|--------|------|----------|----------|-----------|--------|
| R-1 | 行为 | mode_ 参数决定创建哪种识别器 | GestureGroup 创建对应 RecognizerGroup 子类：Sequence→SequencedRecognizer，Parallel→ParallelRecognizer，Exclusive→ExclusiveRecognizer | — | AC-1.1, AC-2.1, AC-3.1 |
| R-2 | 行为 | 序列中手势必须严格按顺序完成 | SequencedRecognizer 使用 currentIndex_ 跟踪当前活跃手势索引（从 0 开始），前一个成功后递增 | — | AC-1.1~1.8 |
| R-3 | 行为 | 无竞争关系 | ParallelRecognizer 中所有子识别器同时接收触摸事件，多个子手势可同时成功 | — | AC-2.1~2.6 |
| R-4 | 行为 | CheckNeedBlocked 确保互斥 | ExclusiveRecognizer 使用 activeRecognizer_ 追踪当前活跃识别器，仅一个可获胜 | — | AC-3.1~3.8 |
| R-5 | 行为 | CreateRecognizer 仅对 Sequence 模式调用 SetOnActionCancel | onCancel 回调仅在 Sequence 模式中被设置和触发，Parallel 和 Exclusive 模式不支持 | — | AC-4.1~4.4 |
| R-6 | 行为 | RemoveChildrenByTag、ForceReject 等均递归 | GestureGroup 支持嵌套，子手势可以是另一个 GestureGroup，操作递归执行 | — | AC-5.1~5.4 |
| R-7 | 行为 | 触摸事件到达 | SequencedRecognizer 在 HandleEvent 中通过 currentIndex_ 获取当前子识别器并分发事件 | SequencedRecognizer | AC-1.1 |
| R-8 | 行为 | 当前手势成功 | SequencedRecognizer.OnAccepted 调用 UpdateCurrentIndex 递增索引并可能发送合成 TouchDown 事件给下一个子识别器 | SequencedRecognizer | AC-1.1, AC-1.5 |
| R-9 | 行为 | 当前手势失败 | SequencedRecognizer.OnRejected 将 currentIndex_ 到末尾的所有子识别器全部拒绝，整个序列失败 | SequencedRecognizer | AC-1.2 |
| R-10 | 行为 | 最后一个手势成功 | SequencedRecognizer.BatchAdjudicate 在 currentIndex_ 指向最后一个手势时接受整个序列 | SequencedRecognizer | AC-1.3 |
| R-11 | 行为 | UP 事件且 PENDING 状态 | SequencedRecognizer.DeadlineTimer 启动 300ms 定时器，超时后 HandleOverdueDeadline 调用 GroupAdjudicate(REJECT) | SequencedRecognizer | AC-1.4 |
| R-12 | 行为 | UpdateCurrentIndex 检测到 isEventHandoverNeeded_ | SequencedRecognizer.SendTouchEventToNextRecognizer 向下一个子识别器发送合成 DOWN 事件（事件传递） | SequencedRecognizer | AC-1.5 |
| R-13 | 行为 | 连续 LongPress 传递事件 | SequencedRecognizer.CheckBetweenTwoLongPressRecognizer 检测连续两个 LongPress，自动调整时间戳 | SequencedRecognizer | AC-1.6 |
| R-14 | 行为 | 序列结束/失败 | SequencedRecognizer.OnResetStatus 将 currentIndex_ 重置为 0，取消 deadlineTimer_ | SequencedRecognizer | AC-1.8 |
| R-15 | 行为 | 触摸事件到达 | ParallelRecognizer.HandleEvent 将触摸事件分发给所有子识别器 | ParallelRecognizer | AC-2.1 |
| R-16 | 行为 | 子手势 ACCEPT | ParallelRecognizer 中一个子手势成功不影响其他子手势 | ParallelRecognizer | AC-2.2 |
| R-17 | 行为 | 子手势 REJECT | ParallelRecognizer.CheckAllFailed 检查是否所有子手势均失败 | ParallelRecognizer | AC-2.3 |
| R-18 | 行为 | 组被外部接受 | ParallelRecognizer.OnAccepted 接受当前子手势并批量接受 succeedBlockRecognizers_ | ParallelRecognizer | AC-2.4 |
| R-19 | 行为 | 组被外部拒绝 | ParallelRecognizer.OnRejected 对所有子手势递归调用 ForceReject | ParallelRecognizer | AC-2.5 |
| R-20 | 行为 | 子手势 ACCEPT 但组 SUCCEED_BLOCKED | ParallelRecognizer 在子手势成功但组整体被阻塞时加入 succeedBlockRecognizers_ | ParallelRecognizer | AC-2.6 |
| R-21 | 行为 | 触摸事件到达且无活跃识别器 | ExclusiveRecognizer 在无 activeRecognizer_ 时将事件广播给所有子手势（竞争阶段） | ExclusiveRecognizer | AC-3.1 |
| R-22 | 行为 | 子手势请求 PENDING/ACCEPT | ExclusiveRecognizer.CheckNeedBlocked 在任何其他子手势 PENDING 时阻塞当前子手势 | ExclusiveRecognizer | AC-3.2 |
| R-23 | 行为 | 组被外部接受 | ExclusiveRecognizer.OnAccepted 接受 activeRecognizer_ 并拒绝所有其他子手势 | ExclusiveRecognizer | AC-3.3 |
| R-24 | 行为 | activeRecognizer_ REJECT | ExclusiveRecognizer.HandleRejectDisposal 在 activeRecognizer_ 失败时调用 UnBlockGesture 尝试解除阻塞 | ExclusiveRecognizer | AC-3.4 |
| R-25 | 行为 | UnBlockGesture 返回 SUCCEED_BLOCKED | ExclusiveRecognizer 解除阻塞时发现 SUCCEED_BLOCKED 子手势直接请求组接受 | ExclusiveRecognizer | AC-3.5 |
| R-26 | 行为 | CheckAllFailed 且 UnBlockGesture 返回 null | ExclusiveRecognizer 在所有子手势失败且无可解除阻塞时拒绝整个组 | ExclusiveRecognizer | AC-3.6 |
| R-27 | 行为 | activeRecognizer_ 非 null | ExclusiveRecognizer 在 activeRecognizer_ 选定后仅向其分发 MOVE/DOWN 事件 | ExclusiveRecognizer | AC-3.7 |
| R-28 | 行为 | 事件类型为 UP/CANCEL | ExclusiveRecognizer 始终将 UP/CANCEL 事件广播给所有子手势 | ExclusiveRecognizer | AC-3.8 |
| R-29 | 行为 | CreateRecognizer | onCancel 回调仅在 GestureMode::Sequence 时通过 SetOnActionCancel 设置 | GestureGroup | AC-4.1 |
| R-30 | 行为 | 序列手势失败 | SequencedRecognizer.OnRejected 中 currentIndex_ != -1 时触发 onCancel | SequencedRecognizer | AC-4.2 |
| R-31 | 行为 | 序列在 PENDING 被重置 | SequencedRecognizer.ResetStatusOnFinish 在 PENDING 状态重置时触发 onCancel | SequencedRecognizer | AC-4.3, AC-4.4 |
| R-32 | 行为 | 创建组合识别器 | GestureGroup.CreateRecognizer 递归调用子手势的 CreateRecognizer | GestureGroup | AC-5.1 |
| R-33 | 行为 | 移除子手势 | GestureGroup.RemoveChildrenByTag 递归搜索子 Group 中匹配标签的手势并删除 | GestureGroup | AC-5.2 |
| R-34 | 行为 | 组被拒绝 | RecognizerGroup.ForceReject 对子 RecognizerGroup 递归执行 | RecognizerGroup | AC-5.3 |
| R-35 | 异常 | 两轮手势间 UP 后超过 300ms | 序列手势间超时 | HandleOverdueDeadline → GroupAdjudicate(REJECT)，整个序列失败 | AC-1.4 |
| R-36 | 异常 | 子识别器返回 REJECT | 序列中某个手势失败 | 从 currentIndex_ 到末尾全部拒绝，触发 onCancel | AC-1.2 |
| R-37 | 异常 | 外部调用 ResetStatusOnFinish | 序列在 PENDING 状态被重置 | 触发 onCancel，currentIndex_ 重置为 0 | AC-1.7, AC-1.8 |
| R-38 | 异常 | 所有子手势均失败且无阻塞手势 | Exclusive 无可用竞争者 | 整个互斥组失败 | AC-3.6 |
| R-39 | 异常 | 创建时无子手势 | 空 GestureGroup | CreateRecognizer 返回空子识别器列表，groupRecognizer 仍被创建 | — |
| R-40 | 异常 | Parallel 模式中子识别器被移除 | 子识别器列表在迭代中被修改 | 安全检查 recognizers_.size() < size 时 break 退出循环 | — |
| R-41 | 恢复 | 序列失败（任一手势 REJECT） | OnResetStatus：currentIndex_=0，取消 deadlineTimer_，所有子识别器状态重置为 READY | 整个序列恢复初始状态，可接受新触摸序列 | — |
| R-42 | 恢复 | 序列超时（300ms） | HandleOverdueDeadline → GroupAdjudicate(REJECT) → OnResetStatus | 同 R-41 | — |
| R-43 | 恢复 | 互斥组 activeRecognizer_ 失败 | UnBlockGesture 尝试解除其他被阻塞的子识别器 | 若找到可解除阻塞的手势则继续竞争，否则组失败 | — |
| R-44 | 恢复 | 并行组被外部拒绝 | ForceReject 递归拒绝所有子手势和子 Group | 所有子识别器恢复 FAIL 状态 | — |
| R-45 | 恢复 | 组件销毁 | GestureEventHub 析构清理所有手势识别器（包括嵌套 Group） | 识别器被释放，不会触发回调 | — |

---

## 验证映射

| 编号 | 对应规格项 | 验证方式 | 验证重点 |
|------|------------|----------|----------|
| VM-1 | R-7~R-14, AC-1.1~1.8 | 单测 | SequencedRecognizer 序列推进、超时、事件传递、LongPress 特殊处理 |
| VM-2 | R-15~R-20, AC-2.1~2.6 | 单测 | ParallelRecognizer 并行分发、多成功、succeedBlockRecognizers_ 批量接受 |
| VM-3 | R-21~R-28, AC-3.1~3.8 | 单测 | ExclusiveRecognizer 互斥竞争、activeRecognizer_ 选择、UnBlockGesture 失败转移 |
| VM-4 | R-29~R-31, AC-4.1~4.4 | 单测 | onCancel 仅限 Sequence、触发条件 |
| VM-5 | R-32~R-34, AC-5.1~5.4 | 单测/集成 | 嵌套 Group、递归操作 |
| VM-6 | 全量 | XTS/集成 | 端到手势组合交互正确 |

---

## API 变更分析

### 新增 API

| API 签名 | 类型 | 功能描述 | 关联 AC |
|----------|------|----------|---------|
| `GestureGroup(mode: GestureMode, ...gesture: GestureType[]): GestureGroupInterface` | Public | 创建组合手势 | AC-1.1, AC-2.1, AC-3.1 |
| `GestureGroupInterface.onCancel(event: () => void): GestureGroupInterface` | Public | 设置取消回调（仅 Sequence 模式生效） | AC-4.1~4.4 |

**关联枚举类型：**

| 类型名 | 定义 | 位置 |
|--------|------|------|
| `GestureMode` | `{ Sequence, Parallel, Exclusive }` | `gesture.d.ts` |
| `GestureType` | `TapGestureInterface \| LongPressGestureInterface \| ... \| GestureGroupInterface` | `gesture.d.ts` |

### 变更/废弃 API

| API 名称 | 变更类型 | 关联 AC |
|----------|----------|---------|
| — | — | 无变更/废弃 API |

---

## 接口规格

### 接口定义

> 本特性为已有实现补录，接口行为定义详见上方规则定义和用户故事。

无新增接口规格。

---

## 兼容性声明

- **已有 API 行为变更:** 否
- **配置文件格式变更:** 否
- **数据存储格式变更:** 否
- **最低支持版本:** API 8
- **API 版本号策略:** @since 8，GestureGroup 和 GestureMode 同版本引入

---

## 架构约束

| 关键约束 | 约束说明 | 影响 AC |
|----------|----------|---------|
| RecognizerGroup 继承 MultiFingersRecognizer | 组合识别器共享多指基础能力 | 全部 |
| GroupAdjudicate 向上传递仲裁 | 子识别器不直接与 GestureReferee 交互，通过 RecognizerGroup 层层上传 | AC-1.1~3.8 |
| UI 线程同步执行 | 组合手势识别在 UI 线程同步执行 | 全部 |
| 单向依赖 | GestureGroup → RecognizerGroup → 子识别器，不可反向 | 全部 |
| 嵌套深度无硬限制 | GestureGroup 可无限嵌套，但过深嵌套可能影响性能 | AC-5.1~5.4 |

> 架构规则适用性及设计方案见 design.md。

---

## 非功能性需求

| 类型 | 指标/阈值 | 验证方式 | 证据 |
|------|-----------|----------|------|
| 性能 | 组合手势事件分发延迟 < 单个子手势分发 × 子手势数量 | benchmark | — |
| 内存 | 每个 RecognizerGroup 对象 < 256 字节（不含子识别器） | hidumper | — |
| 安全 | N/A — 手势 API 无权限要求 | — | — |
| 可靠性 | 序列失败后状态完全重置（currentIndex_=0，子识别器 READY） | 单测 | R-41~R-45 |
| 问题定位 | GestureGroup 事件通过 AddGestureProcedure 记录手势处理过程 | 日志 | — |

---

## 多设备适配声明

| 设备类型 | 行为差异 | 规格/约束 | 验证方式 | 证据 |
|----------|----------|-----------|----------|------|
| 手机 | 无差异 | — | — | — |
| 平板 | 无差异 | — | — | — |
| 折叠屏 | 无差异 | — | — | — |

---

## 全局特性影响

| 特性 | 适用？ | 结论 | 关联场景 |
|------|--------|------|----------|
| 无障碍 | N/A | 手势组合不直接影响无障碍语义 | — |
| 大字体 | N/A | 手势参数不涉及字体 | — |
| 深色模式 | N/A | 手势参数不涉及颜色 | — |
| 多窗口/分屏 | 是 | 分屏后触摸坐标映射正确，组合手势逻辑不受影响 | 多窗口下组合手势正确 |
| 多用户 | N/A | 手势无用户态差异 | — |
| 版本升级 | 是 | GestureGroup 自 API 8 引入，无后续行为变更 | — |
| 生态兼容 | 是 | C-API 提供等效接口（createGroupGesture/addChildGesture/removeChildGesture），本 spec 不覆盖 | — |

---

## 行为场景（可选，Gherkin）

```gherkin
Feature: 组合手势
  作为 应用开发者
  我想要 通过 GestureGroup 将多个手势按不同策略组合
  以便 实现复杂的多步或互斥手势交互

  # ─── Sequence 模式 ──────────────────────────────

  Scenario: 顺序组合-长按后拖动
    Given 一个组件绑定了 GestureGroup(Sequence, LongPressGesture(), PanGesture())
    When 用户长按 500ms（第一个手势成功）
    And 在 300ms 内开始拖动超过 5vp（第二个手势成功）
    Then 整个序列成功

  Scenario: 顺序组合-中间手势失败
    Given 一个组件绑定了 GestureGroup(Sequence, TapGesture(), PanGesture())
    When 用户单击成功（第一个手势成功）
    And 用户长按不动（PanGesture 未满足 distance 阈值，第二个手势失败）
    Then 整个序列失败
    And onCancel 回调触发

  Scenario: 顺序组合-超时
    Given 一个组件绑定了 GestureGroup(Sequence, TapGesture(), PanGesture())
    When 用户单击成功（第一个手势成功）
    And 用户等待 >300ms 不操作
    Then 序列超时失败
    And onCancel 回调触发

  Scenario: 顺序组合-事件传递
    Given 一个组件绑定了 GestureGroup(Sequence, TapGesture(), LongPressGesture())
    When 用户单击成功（第一个手势成功）
    Then 自动向 LongPressRecognizer 发送合成 TouchDown 事件
    And 用户持续按住 500ms 后 LongPress 成功
    Then 整个序列成功

  Scenario: 顺序组合-连续两个 LongPress
    Given 一个组件绑定了 GestureGroup(Sequence, LongPressGesture({duration:500}), LongPressGesture({duration:300}))
    When 用户长按 500ms（第一个成功）
    Then 事件传递时自动调整时间戳（beforeDuration）
    And 第二个 LongPress 不会因继承的时间戳立即触发

  # ─── Parallel 模式 ──────────────────────────────

  Scenario: 并行组合-多手势同时成功
    Given 一个组件绑定了 GestureGroup(Parallel, PanGesture(), PinchGesture())
    When 用户双指同时拖动和捏合
    Then PanGesture 和 PinchGesture 均可独立成功
    And 两个手势的回调均触发

  Scenario: 并行组合-全部失败
    Given 一个组件绑定了 GestureGroup(Parallel, TapGesture(), LongPressGesture())
    When 用户轻触但未长按
    And TapGesture 和 LongPressGesture 均识别失败
    Then 整个并行组失败

  Scenario: 并行组合-被阻塞的手势批量接受
    Given 一个组件绑定了 GestureGroup(Parallel, PanGesture(), PinchGesture())
    When PanGesture 先成功但组整体被外部阻塞（SUCCEED_BLOCKED）
    And 随后 PinchGesture 也成功
    Then 两者均被加入 succeedBlockRecognizers_
    When 组被解除阻塞
    Then 两个手势均被批量接受

  # ─── Exclusive 模式 ─────────────────────────────

  Scenario: 互斥组合-第一个成功的手势获胜
    Given 一个组件绑定了 GestureGroup(Exclusive, TapGesture(), LongPressGesture())
    When 用户轻触（TapGesture 先成功）
    Then TapGesture 被接受（activeRecognizer_）
    And LongPressGesture 被拒绝（ForceReject）

  Scenario: 互斥组合-长按先成功
    Given 一个组件绑定了 GestureGroup(Exclusive, TapGesture(), LongPressGesture())
    When 用户长按 500ms（LongPressGesture 先成功）
    Then LongPressGesture 被接受
    And TapGesture 被拒绝

  Scenario: 互斥组合-活跃识别器失败后转移
    Given 一个组件绑定了 GestureGroup(Exclusive, PanGesture({direction:Horizontal}), PanGesture({direction:Vertical}))
    When 用户开始水平拖动（Horizontal Pan 成为 activeRecognizer_）
    And 随后转向垂直方向（Horizontal Pan 失败）
    Then Vertical Pan 被解除阻塞（UnBlockGesture）
    And Vertical Pan 接替成为 activeRecognizer_

  Scenario: 互斥组-所有手势均失败
    Given 一个组件绑定了 GestureGroup(Exclusive, TapGesture(), PanGesture())
    When 用户轻触但未移动（两个手势均失败）
    And 无被阻塞的手势可解除
    Then 整个互斥组失败

  # ─── onCancel ────────────────────────────────────

  Scenario: onCancel 仅在 Sequence 模式触发
    Given 一个组件绑定了 GestureGroup(Sequence, TapGesture(), PanGesture()).onCancel(() => { ... })
    When 序列中某个手势失败
    Then onCancel 回调触发

  Scenario: onCancel 在 Parallel 模式不触发
    Given 一个组件绑定了 GestureGroup(Parallel, TapGesture(), PanGesture()).onCancel(() => { ... })
    When 并行组失败
    Then onCancel 回调不触发（仅 Sequence 模式支持 onCancel）

  # ─── 嵌套 ────────────────────────────────────────

  Scenario: 嵌套 GestureGroup
    Given 一个组件绑定了 GestureGroup(Sequence,
        GestureGroup(Exclusive, TapGesture(), LongPressGesture()),
        PanGesture())
    When 用户长按成功（嵌套 Exclusive 中 LongPress 获胜）
    And 随后开始拖动
    Then 整个序列成功
```

---

## Spec 自审清单

- [x] 无"待定""TBD""TODO"等占位符
- [x] 所有 AC 使用 WHEN/THEN 格式，可独立测试
- [x] 范围边界明确（3 种组合模式 + onCancel + 嵌套；不含 C-API、GestureReferee 仲裁机制）
- [x] 无语义模糊表述
- [x] AC 与业务规则/异常规则/恢复契约交叉一致

---

## context-references

```yaml
context-queries:
  - repo: "openharmony/ace_engine"
    query: "SequencedRecognizer currentIndex deadlineTimer SEQUENCE_GESTURE_TIMEOUT event handover"
  - repo: "openharmony/ace_engine"
    query: "ParallelRecognizer succeedBlockRecognizers batch accept"
  - repo: "openharmony/ace_engine"
    query: "ExclusiveRecognizer activeRecognizer CheckNeedBlocked UnBlockGesture"
  - repo: "openharmony/ace_engine"
    query: "GestureGroup CreateRecognizer GestureMode nesting RemoveChildrenByTag"
  - repo: "openharmony/ace_engine"
    query: "RecognizerGroup ForceReject GroupAdjudicate"
```

**关键文档：**
- SDK API 类型定义：`interface/sdk-js/api/@internal/component/ets/gesture.d.ts`
- 架构设计：`specs/04-common-capability/04-common-events/06-gesture-capability/design.md`
