# 特性规格

## 概述

| 属性 | 值 |
|------|-----|
| 特性名称 | 手势仲裁与响应控制 |
| 特性编号 | Func-03-04-01-Feat-04 |
| 所属 Epic | 无 |
| 优先级 | P0 |
| 目标版本 | 当前主干 |
| SIG 归属 | ArkUI SIG |
| 状态 | Baselined |
| 复杂度 | 关键 |

本规格补录 GestureReferee 的 scope、竞争、阻塞、延迟关闭和 ResponseCtrl 独占响应机制。公开手势 API 细节由手势能力规格承接。

## 本次变更范围（Delta）

| 类型 | 内容 | 说明 |
|------|------|------|
| ADDED | GestureScope 规格 | 固化按 touchId 分组和 recognizer 去重 |
| ADDED | 仲裁状态规格 | 固化 ACCEPT/REJECT/PENDING、blocked 解阻和 delay close |
| ADDED | 响应控制规格 | 固化 monopolize 与 firstResponseNode 的轮次语义 |

## 输入文档

- 共享设计：`specs/03-engine-framework/04-event-framework/01-event-base-framework/design.md`。
- 仲裁声明：`frameworks/core/components_ng/gestures/gesture_referee.h:34-124`。
- 仲裁实现：`frameworks/core/components_ng/gestures/gesture_referee.cpp:45,67,86,288,306,561,610`。
- 响应控制：`frameworks/core/components_ng/event/response_ctrl.cpp:21`。

## 用户故事

### US-1: 在同一触摸域内确定手势胜负

作为手势识别器开发者，我希望 recognizer 按 touchId 进入同一仲裁 scope，并通过 pending、blocked、accept、reject 状态竞争，以便互斥和组合手势获得确定结果。

| AC编号 | 验收标准 | 类型 |
|--------|----------|------|
| AC-1.1 | WHEN命中结果包含 recognizer THEN GestureReferee 按 touchId 加入 scope 且同一 recognizer 不重复加入 | 正常 |
| AC-1.2 | WHEN已有其他 recognizer 处于 PENDING THEN 当前请求可进入 blocked；WHEN阻塞者 REJECT THEN 解阻下一个候选 | 正常 |
| AC-1.3 | WHEN recognizer ACCEPT THEN scope 中其他非 bridge recognizer 被拒绝 | 正常 |
| AC-1.4 | WHEN清理 scope 时仍有 PENDING recognizer THEN设置 delay close 而不立即销毁；WHEN延迟 recognizer 到 END THEN重新处理 accept | 恢复 |

### US-2: 控制一轮事件的独占响应节点

作为组件框架开发者，我希望独占响应由本轮首个响应节点决定，并在轮次结束后重置，以便 monopolizeEvents 不会在节点间随机切换。

| AC编号 | 验收标准 | 类型 |
|--------|----------|------|
| AC-2.1 | WHEN monopolize 状态尚未确定 THEN 第一个请求响应的节点根据自身配置将本轮状态设为 ON 或 OFF | 正常 |
| AC-2.2 | WHEN本轮状态为 ON THEN仅 firstResponseNode 可响应；WHEN状态为 OFF THEN其他节点仍可响应 | 正常 |
| AC-2.3 | WHEN所有 GestureReferee scope 清空 THEN EventManager 调用 ResponseCtrl.Reset 开始新一轮 | 恢复 |

## 验收追溯

| AC | 关联规则 | 关联 Task | 验证方式 | 证据 |
|----|----------|-----------|----------|------|
| AC-1.1 | R-1 | TASK-F4-1 | scope 去重测试 | `gesture_referee.cpp:288` |
| AC-1.2 | R-2, R-4 | TASK-F4-2 | pending/blocked 状态机测试 | `gesture_referee.cpp:45,86,561` |
| AC-1.3 | R-3 | TASK-F4-2 | accept 排他测试 | `gesture_referee.cpp:67` |
| AC-1.4 | R-5 | TASK-F4-2 | delay close/recall 测试 | `gesture_referee.cpp:306,610` |
| AC-2.1, AC-2.2 | R-6, R-7 | TASK-F4-3 | ResponseCtrl 多节点测试 | `response_ctrl.cpp:21` |
| AC-2.3 | R-8 | TASK-F4-3 | 轮次结束重置测试 | `event_manager.cpp:1290` |

## 规则定义

| 规则ID | 类型 | 触发条件 | 预期行为 | 边界/约束 | 关联AC |
|--------|------|----------|----------|-----------|--------|
| R-1 | 行为 | AddGestureToScope(touchId, hitTestResult) | 创建或复用 touchId scope，并去重加入 recognizer | nullptr 和重复 recognizer 不产生新项 | AC-1.1 |
| R-2 | 行为 | recognizer 请求处理且其他候选 PENDING | 当前 recognizer 进入对应 blocked 状态 | 同一 recognizer 或其 recognizer group 允许例外处理 | AC-1.2 |
| R-3 | 行为 | recognizer 被仲裁为 ACCEPT | 拒绝 scope 内其他非 bridge recognizer | bridge recognizer 不按普通候选强制拒绝 | AC-1.3 |
| R-4 | 恢复 | PENDING recognizer REJECT | 从 PENDING_BLOCKED/SUCCEED_BLOCKED 候选中解阻下一个 | 无 blocked 候选时不额外迁移 | AC-1.2 |
| R-5 | 恢复 | CleanGestureScope 遇到 PENDING | 标记 delay close；延迟 recognizer END 后 recall accept/close | scope 在状态完成前保留 | AC-1.4 |
| R-6 | 行为 | ResponseCtrl 状态为 INIT | 首个响应节点决定 ON/OFF 并记录 firstResponseNode | 一轮只确定一次 | AC-2.1 |
| R-7 | 行为 | ResponseCtrl 状态为 ON/OFF | ON 仅允许 firstResponseNode；OFF 允许请求节点响应 | 节点失效按实现的弱引用检查返回 | AC-2.2 |
| R-8 | 恢复 | currentReferee scopes 为空 | 调用 Reset 清除 firstResponseNode 和状态 | 新一轮重新由首节点决定 | AC-2.3 |

## 验证映射

| 编号 | 对应规格项 | 验证方式 | 验证重点 |
|------|------------|----------|----------|
| VM-1 | AC-1.1 | GestureReferee scope 单测 | touchId 分组、去重 |
| VM-2 | AC-1.2, AC-1.3 | recognizer 竞争状态机测试 | blocked、accept 排他、bridge 例外 |
| VM-3 | AC-1.4 | pending 清理测试 | delay close 和 END recall |
| VM-4 | AC-2.1, AC-2.2 | 多 FrameNode 响应测试 | 首节点锁定 ON/OFF |
| VM-5 | AC-2.3 | 完整 DOWN-UP 轮次测试 | scope 清空触发 Reset |

## API 变更分析

### 新增 API

无新增 Public/System API。GestureReferee、GestureScope、ResponseCtrl 为 InnerApi 实现。

### 变更/废弃 API

无变更或废弃 API。

## 接口规格

### 接口定义

**GestureReferee::AddGestureToScope（现有 InnerApi）**

| 属性 | 值 |
|------|-----|
| 函数签名 | `void AddGestureToScope(size_t touchId, const TouchTestResult& hitTestResult)` |
| 返回值 | void |
| 开放范围 | InnerApi |
| 错误码 | N/A |
| 关联 AC | AC-1.1 |

**ResponseCtrl::ShouldResponse（现有 InnerApi）**

| 属性 | 值 |
|------|-----|
| 函数签名 | `bool ShouldResponse(const RefPtr<FrameNode>& node)` |
| 返回值 | 当前节点在本轮是否允许响应 |
| 开放范围 | InnerApi |
| 错误码 | N/A |
| 关联 AC | AC-2.1, AC-2.2 |

**参数约束**

| 参数 | 类型 | 必填 | 默认值 | 约束条件 |
|------|------|------|--------|---------|
| touchId | size_t | 是 | 无 | 同一交互轮次保持稳定 |
| hitTestResult | TouchTestResult | 是 | 空集合 | recognizer 可为空，空集合不创建有效竞争项 |
| node | RefPtr<FrameNode> | 是 | 无 | 节点应仍有效 |

行为索引：GestureReferee 状态机见 VM-1 至 VM-3；ResponseCtrl 见 VM-4/VM-5。

## 兼容性声明

- **已有 API 行为变更:** 否。
- **配置文件格式变更:** 否。
- **数据存储格式变更:** 否。
- **最低支持版本:** InnerApi 随当前引擎主干。
- **API 版本号策略:** 不适用 Public `@since`。

## 架构约束

| 关键约束 | 约束说明 | 影响 AC |
|----------|----------|---------|
| scope 归属 | GestureReferee 只仲裁命中测试提供的 recognizer | AC-1.1 |
| recognizer 自治 | 获胜后其他 recognizer 仍可能收到输入并自行过滤 | AC-1.3 |
| 响应轮次一致性 | ResponseCtrl 不得在 scope 未结束时切换 firstResponseNode | AC-2.1, AC-2.2 |
| 公共 API 边界 | Native Gesture API 细节不在本规格重复定义 | AC-1.1 |

## 非功能性需求

| 类型 | 指标/阈值 | 验证方式 | 证据 |
|------|-----------|----------|------|
| 性能 | scope 按 touchId 查找，重复 recognizer 不重复存储 | 容器单测 | `gesture_referee.cpp:288` |
| 内存 | 完成 scope 被清理，pending scope 延迟到状态结束 | 生命周期测试 | `gesture_referee.cpp:306` |
| 可靠性 | pending reject 后必须解阻候选，避免交互悬挂 | 状态机测试 | `gesture_referee.cpp:561` |
| 可测试性 | disposition 和 referee state 可直接构造 | 单元测试 | gesture_referee_test |
| 定界定位 | EventTree 可记录 recognizer 状态迁移 | Dump 测试 | EventManager gesture snapshot |

## 多设备适配声明

| 设备类型 | 行为差异 | 规格/约束 | 验证方式 | 证据 |
|----------|----------|-----------|----------|------|
| 手机 | 多指触摸产生多个 touchId scope | 各 scope 独立仲裁 | 多指测试 | AC-1.1 |
| 平板 | 鼠标/Axis 转换的手势同样参与 scope | source type 变化时清理旧状态 | 鼠标/滚轮测试 | EventManager |
| 折叠屏 | 无仲裁算法差异 | 窗口变化不改变已建 scope 的 touchId | 折叠交互测试 | AC-1.4 |

## 全局特性影响

| 特性 | 适用？ | 结论 | 关联场景 |
|------|--------|------|----------|
| 无障碍 | 是 | bridge recognizer 例外避免破坏桥接链路 | AC-1.3 |
| 大字体 | 否 | 不改变仲裁规则 | - |
| 深色模式 | 否 | 不影响状态机 | - |
| 多窗口/分屏 | 是 | 各 Container/EventManager 持有自身 referee | AC-1.1 |
| 多用户 | 否 | 无持久化数据 | - |
| 版本升级 | 否 | InnerApi 行为补录 | - |
| 生态兼容 | 是 | 保持已有 recognizer 竞争结果 | AC-1.2 |

## 行为场景（可选，Gherkin）

```gherkin
Feature: 手势仲裁与响应控制
  Scenario: Pending 阻塞与解阻
    Given recognizer A 已处于 PENDING
    When recognizer B 请求 ACCEPT
    Then recognizer B 进入 blocked
    When recognizer A REJECT
    Then recognizer B 被解阻并继续仲裁

  Scenario: 独占响应锁定
    Given ResponseCtrl 尚未确定本轮状态
    When monopolize 节点 A 首先请求响应
    Then 本轮 firstResponseNode 为 A
    And 其他节点在 Reset 前不能响应
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
    query: "GestureReferee GestureScope pending blocked delay close ResponseCtrl monopolize"
```

**关键文档：** `design.md`、`gesture_referee.h`、`gesture_referee.cpp`、`response_ctrl.cpp`。
