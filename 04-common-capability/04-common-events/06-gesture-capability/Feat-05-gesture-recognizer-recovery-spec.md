# 特性规格

> Func-04-04-06-Feat-05 手势识别异常恢复增强：固化 EventManager、GestureReferee 与 MultiFingersRecognizer 已有的新一轮 DOWN 清理、重复 pointer-id 防御和一次性重分发行为。

## 概述

| 属性 | 值 |
|------|-----|
| 特性名称 | 手势识别异常恢复增强 |
| 特性编号 | Func-04-04-06-Feat-05 |
| 所属 Epic | 无（已有能力补录） |
| 优先级 | P0 |
| 目标版本 | API 26（当前实现基线） |
| SIG 归属 | ArkUI SIG |
| 状态 | Baselined |
| 复杂度 | 复杂 |

## 本次变更范围（Delta）

| 类型 | 内容 | 说明 |
|------|------|------|
| MODIFIED | 新一轮 DOWN 恢复语义 | 按当前 EventManager/GestureReferee 实现重写，删除无源码依据的类型豁免方案 |
| ADDED | 重复 pointer-id 防御 | 补齐合成 CANCEL、全局强清和后续处理 |
| ADDED | 首 DOWN 失败重分发 | 补齐首/唯一 DOWN 新增 FAIL 时的一次强清与一次重分发 |

## 输入文档

| 文档 | 路径 | 状态 |
|------|------|------|
| Design | `04-common-capability/04-common-events/06-gesture-capability/design.md` | Baselined |
| EventManager 实现 | `frameworks/core/common/event_manager.cpp` | Source |
| GestureReferee 实现 | `frameworks/core/components_ng/gestures/gesture_referee.cpp` | Source |

## 用户故事与验收标准

### US-1：正常新一轮 DOWN 清理

作为框架维护者，我需要新一轮触摸开始时只清理可安全回收的上一轮状态，并保留合法的 pending/blocked 竞争。

| AC编号 | 验收标准 |
|--------|----------|
| AC-1 | WHEN 正常 DOWN 到达 THEN EventManager 在 touch test/dispatch 前后按该 touchId 与 scope 成员关系执行清理检查 |
| AC-2 | WHEN recognizer 当前无活动手指且状态为 SUCCEED、FAIL 或 DETECTING THEN 常规清理允许重置该 recognizer |
| AC-3 | WHEN recognizer 处于 PENDING、PENDING_BLOCKED 或 SUCCEED_BLOCKED THEN 不因“新 DOWN”这一条件被无差别强制重置 |
| AC-4 | WHEN recognizer 不属于待清理 scope/事件上下文 THEN 不越过成员约束清理无关 recognizer |

### US-2：重复 pointer-id 防御

作为输入框架，我需要在收到尚未结束的 pointer id 的第二个 DOWN 时终止脏序列并恢复全局一致性。

| AC编号 | 验收标准 |
|--------|----------|
| AC-5 | WHEN DOWN 的 pointer id 已存在于当前触摸集合 THEN 识别为重复 pointer-id 异常 |
| AC-6 | WHEN 发生重复 pointer-id DOWN THEN 为旧序列构造/派发 CANCEL，并执行全局 force-clean 路径 |
| AC-7 | WHEN 强清完成 THEN 清除旧触点与 referee/recognizer 残留，使后续输入不继承冲突状态 |

### US-3：首 DOWN 新失败恢复

作为输入框架，我需要在首个/唯一 DOWN 使 recognizer 新进入 FAIL 的异常情况下尝试一次可控恢复。

| AC编号 | 验收标准 |
|--------|----------|
| AC-8 | WHEN 当前事件是首个/唯一 DOWN 且分发后出现新的 FAIL 条件 THEN EventManager 可进入恢复分支 |
| AC-9 | WHEN 恢复分支成立 THEN 强清相关状态并对该 DOWN 最多重分发一次 |
| AC-10 | WHEN 已经执行过恢复重分发 THEN 不递归或循环重放同一 DOWN |
| AC-11 | WHEN 条件不成立 THEN 保持正常分发结果，不为一般识别失败做全局恢复 |

## 规则定义

| 规则 ID | 规则 |
|---------|------|
| BR-1 | 常规清理的状态条件是 recognizer 无当前活动手指，且处于 SUCCEED、FAIL 或 DETECTING 等实现允许重置的状态。 |
| BR-2 | PENDING 与 BLOCKED 状态自然保留；当前源码未发现“仅双击 Tap 和 Swipe 可以跨新 DOWN pending”的专用类型分支。 |
| BR-3 | 清理按 touchId/scope 和 recognizer 成员关系执行，不能把一次普通 DOWN 等同于全局 Reset。 |
| BR-4 | 重复 pointer-id DOWN 是输入序列不一致；恢复必须先以 CANCEL 终止旧序列，再走全局 force-clean。 |
| BR-5 | `MultiFingersRecognizer` 的重复 id 保护防止同一 pointer 重复加入活动触点集合。 |
| BR-6 | 首/唯一 DOWN 失败恢复只在 EventManager 的特定判定成立时触发，重分发上限为一次。 |
| BR-7 | Force-clean 是内部状态恢复路径；本规格不承诺额外应用成功/取消回调，实际回调由 CANCEL 派发与 recognizer 当时状态决定。 |
| BR-8 | 正常识别失败属于业务状态机结果，不自动触发重复 pointer 的全局异常恢复。 |

## 恢复决策表

| 输入/状态 | 常规 clean | force-clean | 重分发 |
|-----------|------------|-------------|--------|
| 正常 DOWN；无活动手指；SUCCEED/FAIL/DETECTING | 是，受 scope 成员约束 | 否 | 否 |
| 正常 DOWN；PENDING/PENDING_BLOCKED/SUCCEED_BLOCKED | 否，保留竞争 | 否 | 否 |
| 重复 pointer-id DOWN | 不足以恢复 | 是，全局清理 | 不作为首 DOWN 失败重分发描述 |
| 首/唯一 DOWN 新产生可恢复 FAIL | 先按正常流程判断 | 是，相关恢复路径 | 最多一次 |
| 一般 MOVE/UP/CANCEL 导致失败 | 按序列结束清理 | 非本规则触发 | 否 |

## 时序规格

1. EventManager 接收 DOWN 并检查当前触点集合。
2. 若 pointer id 重复，先生成 CANCEL 结束旧序列，再清理 referee/recognizer 和触点状态。
3. 若为正常 DOWN，执行 touch test、scope 注册和事件分发。
4. 清理逻辑仅重置满足状态、无活动手指且属于目标上下文的 recognizer。
5. 若首/唯一 DOWN 分发后满足“新 FAIL 可恢复”条件，强清后以保护标记重分发一次。
6. 第二次分发结束后无论结果如何均不再次递归恢复。

## API 与兼容性

- 本特性没有新增 ArkTS/C API；恢复机制位于 EventManager、GestureReferee 和 recognizer 内部。
- 不改变应用可见的手势参数、事件结构、错误码或 Native ABI。
- 合成 CANCEL 可能触发既有取消路径，但不新增独立“恢复回调”。
- 不采用按手势类型硬编码的双击/Swipe pending 白名单，避免记录当前代码中不存在的设计。

## 验证映射

| VM编号 | 关联 AC/规则 | 验证方式 | 证据 |
|--------|-------------|----------|------|
| VM-1 | AC-1～AC-4, BR-1～BR-3 | scope/状态矩阵单测 | `frameworks/core/components_ng/gestures/gesture_referee.cpp:256-275,455-466` |
| VM-2 | AC-5～AC-7, BR-4～BR-5 | 重复 pointer-id DOWN 单测 | `frameworks/core/common/event_manager.cpp:1024-1067,1197-1205,1234-1236`；`multi_fingers_recognizer.cpp:161-170` |
| VM-3 | AC-8～AC-11, BR-6～BR-8 | 首 DOWN 失败与单次重分发测试 | `frameworks/core/common/event_manager.cpp:1381-1401` |
| VM-4 | AC-5～AC-7 | 回归测试 | `test/unittest/core/event/event_manager_test_ng_three.cpp:707-724`；`event_manager_test_ng_two_issuse.cpp:258-284` |
| VM-5 | BR-5 | recognizer 活动触点测试 | `test/unittest/core/gestures/multi_fingers_recognizer_test_ng.cpp:300-316` |

## 非功能与风险约束

- 恢复路径必须有明确触发条件与一次重分发上限，防止输入线程循环重放。
- force-clean 仅用于序列不一致或特定首 DOWN 失败恢复，不替代正常仲裁。
- 本规格不新增固定时延、内存或吞吐量指标；验证以无死循环、无残留 touchId、状态可继续识别为准。

## context-references

- `docs/common/interaction/Gesture_Knowledge_Base_CN.md`
- `frameworks/core/common/event_manager.cpp:1024-1067,1197-1205,1234-1236,1381-1401`
- `frameworks/core/components_ng/gestures/gesture_referee.cpp:256-275,455-466`
- `frameworks/core/components_ng/gestures/recognizers/multi_fingers_recognizer.cpp:161-170`
- `test/unittest/core/event/event_manager_test_ng_three.cpp:707-724`
- `test/unittest/core/event/event_manager_test_ng_two_issuse.cpp:258-284`
- `test/unittest/core/gestures/multi_fingers_recognizer_test_ng.cpp:300-316`
