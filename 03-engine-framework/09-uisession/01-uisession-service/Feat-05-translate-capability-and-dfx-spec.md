# 特性规格

## 概述

| 属性 | 值 |
|------|-----|
| 特性名称 | 翻译能力与DFX并发保护 |
| 特性编号 | Func-03-09-01-Feat-05 |
| 所属 Epic | UiSession |
| 优先级 | P1 |
| 目标版本 | API 12+ |
| SIG 归属 | ArkUI SIG |
| 状态 | Baselined |
| 复杂度 | 复杂 |

> 本 Feat 锁定 UiSession 翻译能力与DFX并发保护：Page translate 全流程（GetPageTranslateText 单次 / StartPageTranslateText 连续 / EndPageTranslateText / ResetPageTranslateText）、web translate (PageTranslateNode ArkWeb 集成)、翻译结果回写（SendPageTranslateResult + CancelWatchdog + Finish）、并发门控 RegisterPageTranslateTextCallback mutex 占位模式（ADR-3）、超时清理 HandlePageTranslateCallbackTimeout requestId 过期检查、结果看门狗 PostPageTranslateResultWatchdogTask、FinishPageTranslateTextRequest 连续 vs 单次回调生命周期、SyncRequestGuard 语言信息查询 CAS 门控、死亡清理翻译会话、translateManagerMap_ per-instance 路由。不涉及 IPC 安全框架（Feat-01）、InspectorTree 查询（Feat-02）、事件上报门控（Feat-03）、命令下发与同步请求（Feat-04）、内容变化检测（Feat-06）、查询辅助 Dump（Feat-07）、SA 验证服务（Feat-08）。

## 本次变更范围（Delta）

> 历史规格补齐，补录已有实现的完整行为规格。

| 类型 | 内容 | 说明 |
|------|------|------|
| ADDED | GetPageTranslateText 单次翻译流程规格 | ui_session_manager_ohos.cpp:1458-1578 单次获取页面翻译文本，requestId 关联回调 |
| ADDED | StartPageTranslateText 连续翻译流程规格 | ui_session_manager_ohos.cpp:1458-1578 连续翻译模式，回调持续触发直到 EndPageTranslateText |
| ADDED | RegisterPageTranslateTextCallback 并发门控 mutex 占位规格 | ui_session_manager_ohos.cpp:1458-1578 mutex 保护 callback 注册，占位模式（ADR-3） |
| ADDED | HandlePageTranslateCallbackTimeout requestId 过期检查规格 | ui_session_manager_ohos.cpp:1458-1578 超时回调清理，requestId staleness 检查丢弃过期结果 |
| ADDED | PostPageTranslateResultWatchdogTask 结果看门狗规格 | ui_session_manager_ohos.cpp:1458-1578 翻译结果看门狗定时检查，超时触发回调清理 |
| ADDED | FinishPageTranslateTextRequest 连续 vs 单次规格 | ui_session_manager_ohos.cpp:1458-1578 连续翻译 Finish 标记结束并清理回调；单次翻译 Finish 仅标记完成 |
| ADDED | EndPageTranslateText / ResetPageTranslateText 会话清理规格 | ui_session_manager_ohos.cpp:1458-1578 End 停止翻译会话、Reset 清理 per-node 或全量 |
| ADDED | SendPageTranslateResult + CancelWatchdog + Finish 翻译结果回写规格 | ui_session_manager_ohos.cpp:1458-1578 回写翻译结果时取消看门狗并 Finish 请求 |
| ADDED | SyncRequestGuard 语言信息 CAS 门控规格 | ui_session_request_guard.h:23-41 GetCurrentAbilityLanguageInfo 同步门控 |
| ADDED | LAST_UNFINISH 并发语言查询规格 | ui_content_proxy.cpp:782-848 第二并发请求立即返回 LAST_UNFINISH |
| ADDED | 翻译会话死亡清理规格 | ui_session_manager_ohos.cpp:1458-1578 SA 进程死亡时清理 translateManagerMap_ |
| ADDED | translateManagerMap_ per-instance 路由规格 | ui_session_manager_ohos.cpp:1458-1578 per-instance 翻译管理器路由 |
| ADDED | PageTranslateNode ArkWeb 集成规格 | ui_session_manager_ohos.cpp:1458-1578 ArkWeb 翻译节点集成处理 |

## 输入文档

- 关联设计：`03-engine-framework/09-uisession/01-uisession-service/design.md`
- 关联需求：已有能力补录（无独立 requirement.md）
- 源码定位（关键文件）：
  - `adapter/ohos/entrance/ui_session/ui_session_manager_ohos.cpp:1458-1578` — Page translate 全流程 + 并发门控 + 超时清理 + 看门狗 + 回写
  - `adapter/ohos/entrance/ui_session/ui_content_proxy.cpp:782-848` — GetCurrentAbilityLanguageInfo + SyncRequestGuard
  - `adapter/ohos/entrance/ui_session/ui_report_stub.cpp:556-653` — UiReportStub translate IPC 事务码处理
  - `interfaces/inner_api/ui_session/ui_content_service_interface.h:43-51` — Page translate 接口声明
  - `interfaces/inner_api/ui_session/ui_translate_type.h` — PageTranslateData / PageTranslateResult 类型定义

## 用户故事

### US-1: Page translate 单次翻译模式

- As a SA 翻译工具开发者
- I want GetPageTranslateText 单次获取页面翻译文本，requestId 关联回调，FinishPageTranslateTextRequest 单次标记完成
- So that SA 翻译工具可单次请求页面翻译文本并在完成后标记结束

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-1.1 | WHEN GetPageTranslateText 被调用 THEN 分配 requestId，注册回调至 translateManagerMap_，触发 PageTranslateText 单次请求流程。来源：`ui_session_manager_ohos.cpp:1458-1578` | 正常 |
| AC-1.2 | WHEN FinishPageTranslateTextRequest 单次模式 THEN 标记 requestId 完成，清理 translateManagerMap_ 中对应回调，不触发后续连续翻译。来源：`ui_session_manager_ohos.cpp:1458-1578` | 正常 |
| AC-1.3 | WHEN GetPageTranslateText requestId 对应回调已被清理（过期或已完成）THEN 丢弃该 requestId 的后续翻译结果，不回调至 SA 进程。来源：`ui_session_manager_ohos.cpp:1458-1578` | 边界 |

### US-2: Page translate 连续翻译模式

- As a SA 翻译工具开发者
- I want StartPageTranslateText 启动连续翻译模式，回调持续触发直到 EndPageTranslateText
- So that SA 翻译工具可连续接收页面翻译文本，支持实时翻译场景

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-2.1 | WHEN StartPageTranslateText 被调用 THEN 注册连续翻译回调至 translateManagerMap_，回调持续触发翻译文本直到 EndPageTranslateText。来源：`ui_session_manager_ohos.cpp:1458-1578` | 正常 |
| AC-2.2 | WHEN FinishPageTranslateTextRequest 连续模式 THEN 仅标记当前 requestId 完成，不清理回调，后续 requestId 继续触发连续翻译。来源：`ui_session_manager_ohos.cpp:1458-1578` | 正常 |
| AC-2.3 | WHEN EndPageTranslateText 被调用 THEN 停止连续翻译会话，清理 translateManagerMap_ 中对应回调，后续不再触发翻译。来源：`ui_session_manager_ohos.cpp:1458-1578` | 正常 |

### US-3: RegisterPageTranslateTextCallback 并发门控

- As a 框架并发安全维护者
- I want RegisterPageTranslateTextCallback 使用 mutex 占位模式保护回调注册（ADR-3），同一时间仅一个翻译回调有效
- So that 防止多个 SA 进程同时注册翻译回调导致回调竞态和结果混乱

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-3.1 | WHEN RegisterPageTranslateTextCallback 被调用 THEN mutex lock 保护下注册回调至 translateManagerMap_，占位模式保证当前回调持有者独占翻译结果。来源：`ui_session_manager_ohos.cpp:1458-1578` | 正常 |
| AC-3.2 | WHEN 第二个 SA 进程尝试 RegisterPageTranslateTextCallback THEN mutex lock 下新回调替换旧回调（占位模式），旧回调持有者不再接收翻译结果。来源：`ui_session_manager_ohos.cpp:1458-1578` | 正常 |
| AC-3.3 | WHEN RegisterPageTranslateTextCallback mutex 占位与 SyncRequestGuard CAS 模式并存 THEN 两种门控语义不同：mutex 占位保证"谁占位谁持有"，CAS 保证"谁先到谁执行"（ADR-3）。来源：`ui_session_request_guard.h:23-41` | 正常 |

### US-4: HandlePageTranslateCallbackTimeout 超时清理与 requestId 过期

- As a 框架可靠性维护者
- I want HandlePageTranslateCallbackTimeout 通过 requestId staleness 检查丢弃过期翻译结果，超时触发回调清理
- So that 翻译请求超时后不会回调过期结果至 SA 进程，防止陈旧翻译数据干扰

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-4.1 | WHEN HandlePageTranslateCallbackTimeout 触发 THEN 检查 requestId 是否过期（stale），若过期则丢弃该 requestId 的翻译结果，不回调至 SA 进程。来源：`ui_session_manager_ohos.cpp:1458-1578` | 正常 |
| AC-4.2 | WHEN HandlePageTranslateCallbackTimeout requestId 未过期 THEN 保留 requestId 对应回调，后续翻译结果可正常回写。来源：`ui_session_manager_ohos.cpp:1458-1578` | 边界 |
| AC-4.3 | WHEN 超时回调清理完成后 THEN requestId 对应回调从 translateManagerMap_ 中移除，后续翻译结果不再回调至 SA 进程。来源：`ui_session_manager_ohos.cpp:1458-1578` | 恢复 |

### US-5: PostPageTranslateResultWatchdogTask 结果看门狗

- As a 框架可靠性维护者
- I want PostPageTranslateResultWatchdogTask 定时检查翻译结果回写状态，超时触发回调清理
- So that 翻译结果回写超时后自动清理 requestId 和回调，防止翻译请求永久挂起

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-5.1 | WHEN PostPageTranslateResultWatchdogTask 被调度 THEN 启动看门狗定时器，等待翻译结果回写。来源：`ui_session_manager_ohos.cpp:1458-1578` | 正常 |
| AC-5.2 | WHEN 看门狗定时器超时且翻译结果未回写 THEN 触发 HandlePageTranslateCallbackTimeout 清理 requestId 和回调。来源：`ui_session_manager_ohos.cpp:1458-1578` | 异常 |
| AC-5.3 | WHEN SendPageTranslateResult 成功回写 THEN CancelWatchdog 取消看门狗定时器，避免不必要的超时清理。来源：`ui_session_manager_ohos.cpp:1458-1578` | 恢复 |

### US-6: SendPageTranslateResult 翻译结果回写

- As a SA 翻译工具开发者
- I want SendPageTranslateResult 回写翻译结果时 CancelWatchdog 取消看门狗并 Finish 请求
- So that 翻译结果回写成功后看门狗不再触发超时清理，请求正常标记完成

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-6.1 | WHEN SendPageTranslateResult 被调用 THEN CancelWatchdog 取消看门狗定时器 + FinishPageTranslateTextRequest 标记完成，翻译结果回写至 requestId 对应回调。来源：`ui_session_manager_ohos.cpp:1458-1578` | 正常 |
| AC-6.2 | WHEN SendPageTranslateResult requestId 已过期（stale）THEN 丢弃翻译结果，不回调至 SA 进程。来源：`ui_session_manager_ohos.cpp:1458-1578` | 异常 |

### US-7: ResetPageTranslateText per-node 或全量清理

- As a SA 翻译工具开发者
- I want ResetPageTranslateText 支持 per-node 单节点翻译重置或全量页面翻译重置
- So that SA 翻译工具可选择重置单个节点的翻译状态或重置整个页面的翻译状态

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-7.1 | WHEN ResetPageTranslateText 指定 node id THEN 仅重置该节点的翻译状态，其他节点翻译状态不变。来源：`ui_session_manager_ohos.cpp:1458-1578` | 正常 |
| AC-7.2 | WHEN ResetPageTranslateText 不指定 node id（全量模式）THEN 重置所有节点的翻译状态，整个页面恢复原始文本。来源：`ui_session_manager_ohos.cpp:1458-1578` | 正常 |

### US-8: GetCurrentAbilityLanguageInfo SyncRequestGuard CAS 门控

> 本 US 与 Feat-04 US-4（命令下发与同步请求保护）定义相同，完整 AC/规则/接口规格见 Feat-04。以下仅列出要点引用。

- As a 框架并发安全维护者
- I want GetCurrentAbilityLanguageInfo 通过 SyncRequestGuard RAII CAS atomic_bool 保证同一时间仅一个语言查询请求执行
- So that 防止多个 SA 进程同时发起同步语言查询导致 Pipeline 竞态

| AC编号 | 验收标准 | 类型 | Feat-04 引用 |
|--------|---------|------|-------------|
| AC-8.1 | SyncRequestGuard CAS compare_exchange_strong(false, true) 成功 → acquired_=true 正常执行 | 正常 | 同 AC-4.1 |
| AC-8.2 | 第二并发请求 CAS 失败 → acquired_=false → 立即返回 LAST_UNFINISH | 正常 | 同 AC-4.2 |
| AC-8.3 | 第一个请求完成 → SyncRequestGuard 析构 → pending_.store(false) 释放门控 | 恢复 | 同 AC-4.3 |

### US-9: 翻译会话死亡清理与 per-instance 路由

- As a 框架可靠性维护者
- I want SA 进程死亡时清理 translateManagerMap_ 中对应翻译会话，translateManagerMap_ per-instance 路由翻译回调
- So that 翻译会话不会因 SA 进程死亡而永久挂起，per-instance 路由保证翻译结果回写至正确的 UiContent 实例

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-9.1 | WHEN SA 进程死亡触发 OnRemoteDied THEN 清理 translateManagerMap_ 中该进程对应的翻译回调，看门狗定时器取消。来源：`ui_session_manager_ohos.cpp:1458-1578` | 恢复 |
| AC-9.2 | WHEN translateManagerMap_ per-instance 路由翻译回调 THEN 翻译结果回写至 requestId 对应的 UiContent 实例，非广播模式。来源：`ui_session_manager_ohos.cpp:1458-1578` | 正常 |

## 验收追溯

| AC | 关联规则 | 关联 Task | 验证方式 | 证据 |
|----|----------|----------|----------|------|
| AC-1.1 | R-1 | TASK-SKELETON-5 | 集成测试 | 代码审查 |
| AC-1.2 | R-6 | TASK-SKELETON-5 | 集成测试 | 代码审查 |
| AC-1.3 | R-4 | TASK-SKELETON-5 | 集成测试：过期 requestId 丢弃 | 代码审查 |
| AC-2.1 | R-2 | TASK-SKELETON-5 | 集成测试 | 代码审查 |
| AC-2.2 | R-6 | TASK-SKELETON-5 | 集成测试 | 代码审查 |
| AC-2.3 | R-7 | TASK-SKELETON-5 | 集成测试 | 代码审查 |
| AC-3.1 | R-3 | TASK-SKELETON-5 | 集成测试 | 代码审查 |
| AC-3.2 | R-3 | TASK-SKELETON-5 | 集成测试：回调替换 | 代码审查 |
| AC-3.3 | R-3 / R-10 | TASK-SKELETON-5 | 代码评审（ADR-3） | 代码审查 |
| AC-4.1 | R-4 | TASK-SKELETON-5 | 集成测试：requestId 过期检查 | 代码审查 |
| AC-4.2 | R-4 | TASK-SKELETON-5 | 代码评审 | 代码审查 |
| AC-4.3 | R-4 | TASK-SKELETON-5 | 集成测试 | 代码审查 |
| AC-5.1 | R-5 | TASK-SKELETON-5 | 集成测试 | 代码审查 |
| AC-5.2 | R-5 | TASK-SKELETON-5 | 集成测试：看门狗超时清理 | 代码审查 |
| AC-5.3 | R-9 | TASK-SKELETON-5 | 集成测试 | 代码审查 |
| AC-6.1 | R-9 | TASK-SKELETON-5 | 集成测试 | 代码审查 |
| AC-6.2 | R-4 | TASK-SKELETON-5 | 集成测试：过期回写丢弃 | 代码审查 |
| AC-7.1 | R-8 | TASK-SKELETON-5 | 集成测试 | 代码审查 |
| AC-7.2 | R-8 | TASK-SKELETON-5 | 集成测试 | 代码审查 |
| AC-8.1 | R-10 | TASK-SKELETON-5 | 集成测试：CAS 成功 | 代码审查 |
| AC-8.2 | R-11 | TASK-SKELETON-5 | 集成测试：CAS 失败 → LAST_UNFINISH | 代码审查 |
| AC-8.3 | R-10 | TASK-SKELETON-5 | 单元测试 | 代码审查 |
| AC-9.1 | R-12 | TASK-SKELETON-5 | 集成测试：触发 OnRemoteDied | 代码审查 |
| AC-9.2 | R-13 | TASK-SKELETON-5 | 代码评审 | 代码审查 |

## 规则定义

| 规则ID | 类型 | 触发条件 | 预期行为 | 边界/约束 | 关联AC |
|--------|------|----------|----------|-----------|--------|
| R-1 | 行为 | GetPageTranslateText 单次翻译请求 | 分配 requestId，注册回调至 translateManagerMap_，触发 PageTranslateText 单次请求流程。翻译结果回写通过 requestId 关联回调。 | 单次模式：FinishPageTranslateTextRequest 标记完成并清理回调 | AC-1.1 |
| R-2 | 行为 | StartPageTranslateText 连续翻译请求 | 注册连续翻译回调至 translateManagerMap_，回调持续触发翻译文本直到 EndPageTranslateText。 | 连续模式：FinishPageTranslateTextRequest 仅标记当前 requestId 完成，不清理回调 | AC-2.1 / AC-2.2 |
| R-3 | 行为 | RegisterPageTranslateTextCallback mutex 占位并发门控 | mutex lock 保护下注册回调至 translateManagerMap_。占位模式：当前回调持有者独占翻译结果。第二个 SA 进程注册时新回调替换旧回调。 | mutex 占位 vs CAS：mutex 保证"谁占位谁持有"，CAS 保证"谁先到谁执行"（ADR-3） | AC-3.1 / AC-3.2 / AC-3.3 |
| R-4 | 行为 | HandlePageTranslateCallbackTimeout requestId staleness 检查 | 超时触发时检查 requestId 是否过期：若过期则丢弃翻译结果并移除回调；若未过期则保留回调。清理完成后 requestId 对应回调从 translateManagerMap_ 中移除。 | requestId 过期判定基于 staleness 检查（当前 requestId 与存储 requestId 不匹配） | AC-1.3 / AC-4.1 / AC-4.2 / AC-4.3 / AC-6.2 |
| R-5 | 异常 | PostPageTranslateResultWatchdogTask 看门狗超时 | 看门狗定时器启动后等待翻译结果回写。超时且未回写时触发 HandlePageTranslateCallbackTimeout 清理 requestId 和回调。 | 看门狗定时器时长由框架内部配置决定 | AC-5.1 / AC-5.2 |
| R-6 | 行为 | FinishPageTranslateTextRequest 连续 vs 单次模式 | 单次模式：标记 requestId 完成 + 清理回调。连续模式：仅标记当前 requestId 完成，不清理回调，后续 requestId 继续触发翻译。 | 单次 vs 连续模式切换由 StartPageTranslateText / GetPageTranslateText 入口决定 | AC-1.2 / AC-2.2 |
| R-7 | 恢复 | EndPageTranslateText 会话停止 | 停止连续翻译会话，清理 translateManagerMap_ 中对应回调，后续不再触发翻译。 | End 与 Reset 区别：End 停止会话但不恢复文本，Reset 恢复文本 | AC-2.3 |
| R-8 | 行为 | ResetPageTranslateText per-node 或全量重置 | 指定 node id：仅重置该节点的翻译状态。不指定 node id：重置所有节点的翻译状态，整个页面恢复原始文本。 | Reset 与 End 区别：Reset 恢复文本，End 仅停止会话 | AC-7.1 / AC-7.2 |
| R-9 | 行为 | SendPageTranslateResult + CancelWatchdog + Finish 回写三步 | SendPageTranslateResult 回写翻译结果至 requestId 对应回调 → CancelWatchdog 取消看门狗定时器 → FinishPageTranslateTextRequest 标记完成。requestId 过期时丢弃结果不回写。 | CancelWatchdog 必须在回写成功后调用，避免看门狗误触发超时清理 | AC-5.3 / AC-6.1 |
| R-10 | 行为 | SyncRequestGuard RAII CAS concurrent gate（同 Feat-04 R-6） | 构造时 CAS compare_exchange_strong(false, true)：第一个请求 acquired_=true 成功执行。析构时：若 acquired_=true 则 pending_.store(false) 释放门控；若 acquired_=false 则不操作 pending_。完整规格见 Feat-04。 | CAS 保证同一时间仅一个请求执行；与 mutex 占位语义不同（ADR-3） | AC-8.1 / AC-8.3 / AC-3.3 |
| R-11 | 边界 | GetCurrentAbilityLanguageInfo LAST_UNFINISH（同 Feat-04 R-7） | 第二个并发请求 CAS 失败时 acquired_=false，立即返回 LAST_UNFINISH，不等待第一个请求完成。完整规格见 Feat-04。 | LAST_UNFINISH 为特殊返回值，表示"上次请求尚未完成" | AC-8.2 |
| R-12 | 恢复 | 翻译会话死亡清理 | SA 进程死亡触发 OnRemoteDied 时清理 translateManagerMap_ 中该进程对应的翻译回调，看门狗定时器取消。 | 死亡清理保证翻译会话不会永久挂起 | AC-9.1 |
| R-13 | 行为 | translateManagerMap_ per-instance 路由 | 翻译结果通过 translateManagerMap_ 路由至 requestId 对应的 UiContent 实例，非广播模式。 | per-instance 路由 vs 广播模式：翻译结果定向发送而非广播至所有 SA 进程 | AC-9.2 |
| R-14 | 行为 | PageTranslateNode ArkWeb 集成 | PageTranslateNode 集成 ArkWeb 翻译能力，web 页面翻译通过 ArkWeb 内部翻译节点处理，翻译文本来源与普通节点不同。 | ArkWeb 翻译节点与普通翻译节点处理路径不同，R-1/R-2 翻译请求触发时 ArkWeb 节点走独立分支 | AC-1.1 / AC-2.1 |

## 验证映射

| 编号 | 对应规格项 | 验证方式 | 验证重点 |
|------|-----------|---------|---------|
| VM-1 | AC-1.1 / R-1 | 集成测试 | GetPageTranslateText 单次翻译流程 + requestId 关联 |
| VM-2 | AC-1.2 / AC-2.2 / R-6 | 集成测试 | FinishPageTranslateTextRequest 单次 vs 连续模式切换 |
| VM-3 | AC-1.3 / AC-4.1 / AC-6.2 / R-4 | 集成测试 | requestId staleness 过期检查丢弃 |
| VM-4 | AC-2.1 / R-2 | 集成测试 | StartPageTranslateText 连续翻译持续回调 |
| VM-5 | AC-2.3 / AC-7.1 / AC-7.2 / R-7 / R-8 | 集成测试 | End 会话停止 vs Reset 文本恢复 |
| VM-6 | AC-3.1 / AC-3.2 / R-3 | 集成测试 | RegisterPageTranslateTextCallback mutex 占位并发门控 |
| VM-7 | AC-4.1..4.3 / R-4 | 集成测试 | HandlePageTranslateCallbackTimeout 超时清理 + requestId 过期 |
| VM-8 | AC-5.1 / AC-5.2 / R-5 | 集成测试 | PostPageTranslateResultWatchdogTask 看门狗超时清理 |
| VM-9 | AC-5.3 / AC-6.1 / R-9 | 集成测试 | SendPageTranslateResult + CancelWatchdog + Finish 三步回写 |
| VM-10 | AC-8.1..8.3 / R-10 / R-11 | 单元测试 | SyncRequestGuard CAS + LAST_UNFINISH |
| VM-11 | AC-9.1 / R-12 | 集成测试 | 翻译会话死亡清理 OnRemoteDied |
| VM-12 | AC-9.2 / R-13 | 代码评审 | translateManagerMap_ per-instance 路由 |
| VM-13 | R-14 | 代码评审 | PageTranslateNode ArkWeb 集成路径 |

## API 变更分析

### 新增 API

N/A，全部为 InnerApi（框架内部 IPC 接口）。无 Public/System API 变更。

### 变更/废弃 API

无。

## 接口规格

### 接口定义

**GetPageTranslateText**

| 属性 | 值 |
|------|-----|
| 函数签名 | `int32_t IUiContentService::GetPageTranslateText(int32_t id, const std::string& src, const std::string& dst)` |
| 返回值 | `int32_t` — ERR_OK 或错误码 |
| 开放范围 | InnerApi |
| 错误码 | N/A |
| 关联 AC | AC-1.1 |

**参数约束**

| 参数 | 类型 | 必填 | 默认值 | 约束条件 |
|------|------|------|--------|---------|
| id | int32_t | 是 | N/A | requestId，翻译请求标识 |
| src | std::string | 是 | N/A | 源语言代码 |
| dst | std::string | 是 | N/A | 目标语言代码 |

**行为场景**

| # | 触发条件 | 预期行为 | 关联 AC |
|---|----------|----------|---------|
| 1 | 正常调用 | 分配 requestId + 注册回调 + 触发单次翻译 | AC-1.1 |

**StartPageTranslateText**

| 属性 | 值 |
|------|-----|
| 函数签名 | `int32_t IUiContentService::StartPageTranslateText(int32_t id, const std::string& src, const std::string& dst)` |
| 返回值 | `int32_t` — ERR_OK 或错误码 |
| 开放范围 | InnerApi |
| 错误码 | N/A |
| 关联 AC | AC-2.1 |

**参数约束**

| 参数 | 类型 | 必填 | 默认值 | 约束条件 |
|------|------|------|--------|---------|
| id | int32_t | 是 | N/A | requestId，翻译请求标识 |
| src | std::string | 是 | N/A | 源语言代码 |
| dst | std::string | 是 | N/A | 目标语言代码 |

**行为场景**

| # | 触发条件 | 预期行为 | 关联 AC |
|---|----------|----------|---------|
| 1 | 正常调用 | 注册连续翻译回调 + 回调持续触发 | AC-2.1 |

**RegisterPageTranslateTextCallback**

| 属性 | 值 |
|------|-----|
| 函数签名 | `int32_t UiSessionManagerOhos::RegisterPageTranslateTextCallback(int32_t pid, const sptr<IRemoteObject>& object)` |
| 返回值 | `int32_t` — ERR_OK 或错误码 |
| 开放范围 | InnerApi |
| 错误码 | N/A |
| 关联 AC | AC-3.1 |

**参数约束**

| 参数 | 类型 | 必填 | 默认值 | 约束条件 |
|------|------|------|--------|---------|
| pid | int32_t | 是 | N/A | SA 进程 pid |
| object | sptr<IRemoteObject> | 是 | N/A | UiReportProxy remote object |

**行为场景**

| # | 触发条件 | 预期行为 | 关联 AC |
|---|----------|----------|---------|
| 1 | 首次注册翻译回调 | mutex lock → 注册回调至 translateManagerMap_ | AC-3.1 |
| 2 | 第二个 SA 进程注册翻译回调 | mutex lock → 新回调替换旧回调（占位模式） | AC-3.2 |

**HandlePageTranslateCallbackTimeout**

| 属性 | 值 |
|------|-----|
| 函数签名 | `void UiSessionManagerOhos::HandlePageTranslateCallbackTimeout(int32_t requestId)` |
| 返回值 | `void` |
| 开放范围 | InnerApi |
| 错误码 | N/A |
| 关联 AC | AC-4.1 |

**参数约束**

| 参数 | 类型 | 必填 | 默认值 | 约束条件 |
|------|------|------|--------|---------|
| requestId | int32_t | 是 | N/A | 翻译请求标识 |

**行为场景**

| # | 触发条件 | 预期行为 | 关联 AC |
|---|----------|----------|---------|
| 1 | requestId 过期（stale） | 丢弃翻译结果 + 移除回调 | AC-4.1 |
| 2 | requestId 未过期 | 保留回调 | AC-4.2 |

**PostPageTranslateResultWatchdogTask**

| 属性 | 值 |
|------|-----|
| 函数签名 | `void UiSessionManagerOhos::PostPageTranslateResultWatchdogTask(int32_t requestId)` |
| 返回值 | `void` |
| 开放范围 | InnerApi |
| 错误码 | N/A |
| 关联 AC | AC-5.1 |

**参数约束**

| 参数 | 类型 | 必填 | 默认值 | 约束条件 |
|------|------|------|--------|---------|
| requestId | int32_t | 是 | N/A | 翻译请求标识 |

**行为场景**

| # | 触发条件 | 预期行为 | 关联 AC |
|---|----------|----------|---------|
| 1 | 正常调度看门狗 | 启动看门狗定时器等待回写 | AC-5.1 |
| 2 | 看门狗超时 | 触发 HandlePageTranslateCallbackTimeout 清理 | AC-5.2 |

**SendPageTranslateResult**

| 属性 | 值 |
|------|-----|
| 函数签名 | `int32_t IUiContentService::SendPageTranslateResult(int32_t id, const PageTranslateResult& result)` |
| 返回值 | `int32_t` — ERR_OK 或错误码 |
| 开放范围 | InnerApi |
| 错误码 | N/A |
| 关联 AC | AC-6.1 |

**参数约束**

| 参数 | 类型 | 必填 | 默认值 | 约束条件 |
|------|------|------|--------|---------|
| id | int32_t | 是 | N/A | requestId |
| result | PageTranslateResult | 是 | N/A | 翻译结果数据 |

**行为场景**

| # | 触发条件 | 预期行为 | 关联 AC |
|---|----------|----------|---------|
| 1 | requestId 有效 | CancelWatchdog + Finish + 回写翻译结果至回调 | AC-6.1 |
| 2 | requestId 过期（stale） | 丢弃结果不回写 | AC-6.2 |

**EndPageTranslateText**

| 属性 | 值 |
|------|-----|
| 函数签名 | `int32_t IUiContentService::EndPageTranslateText(int32_t id)` |
| 返回值 | `int32_t` — ERR_OK 或错误码 |
| 开放范围 | InnerApi |
| 错误码 | N/A |
| 关联 AC | AC-2.3 |

**ResetPageTranslateText**

| 属性 | 值 |
|------|-----|
| 函数签名 | `int32_t IUiContentService::ResetPageTranslateText(int32_t id)` |
| 返回值 | `int32_t` — ERR_OK 或错误码 |
| 开放范围 | InnerApi |
| 错误码 | N/A |
| 关联 AC | AC-7.1 |

**GetCurrentAbilityLanguageInfo**

| 属性 | 值 |
|------|-----|
| 函数签名 | `int32_t IUiContentService::GetCurrentAbilityLanguageInfo(AbilityLanguageInfo& info)` |
| 返回值 | `int32_t` — ERR_OK 或 LAST_UNFINISH |
| 开放范围 | InnerApi |
| 错误码 | LAST_UNFINISH（并发请求拒绝） |
| 关联 AC | AC-8.1 / AC-8.2 |

**参数约束**

| 参数 | 类型 | 必填 | 默认值 | 约束条件 |
|------|------|------|--------|---------|
| info | AbilityLanguageInfo& | 是 | N/A | 出参，应用语言信息 |

**行为场景**

| # | 触发条件 | 预期行为 | 关联 AC |
|---|----------|----------|---------|
| 1 | CAS 成功 | 获取语言信息，返回 ERR_OK | AC-8.1 |
| 2 | CAS 失败（并发请求） | 立即返回 LAST_UNFINISH | AC-8.2 |
| 3 | 第一个请求完成后 | pending_ 释放，后续请求正常 | AC-8.3 |

## 兼容性声明

- **已有 API 行为变更:** 否 — 全部为已有实现补录
- **配置文件格式变更:** 否
- **数据存储格式变更:** 否
- **最低支持版本:** API 12
- **API 版本号策略:** 无 @since 标注（框架内部 IPC 能力）

## 架构约束

| 关键约束 | 约束说明 | 影响 AC |
|---------|----------|---------|
| 双并发门控模式差异 | RegisterPageTranslateTextCallback mutex 占位 vs SyncRequestGuard CAS 语义不同：mutex 保证"谁占位谁持有"，CAS 保证"谁先到谁执行"（ADR-3） | AC-3.3 |
| requestId staleness 过期检查 | HandlePageTranslateCallbackTimeout 通过 requestId staleness 检查丢弃过期结果，防止陈旧翻译数据回调至 SA 进程 | AC-4.1 / AC-6.2 |
| 看门狗 + 回写三步耦合 | SendPageTranslateResult 回写必须 CancelWatchdog + Finish 三步联动，回写成功后看门狗不再触发超时清理 | AC-5.3 / AC-6.1 |
| 单次 vs 连续模式切换 | FinishPageTranslateTextRequest 行为取决于翻译模式：单次清理回调，连续仅标记完成 | AC-1.2 / AC-2.2 |
| 翻译回调非广播模式 | translateManagerMap_ per-instance 路由翻译结果至 requestId 对应 UiContent 实例，非广播至所有 SA 进程 | AC-9.2 |

## 非功能性需求

| 类型 | 指标/阈值 | 验证方式 | 证据 |
|------|----------|----------|------|
| 性能 | SyncRequestGuard CAS 操作为 lock-free，无互斥开销 | 代码评审 | 代码审查 |
| 可观测 | 翻译结果回写可通过 requestId + 看门狗定时器状态追踪 | 代码评审 | 代码审查 |
| 可靠性 | 看门狗超时清理 + requestId 过期检查保证翻译请求不会永久挂起 | 集成测试 | 代码审查 |
| 安全 | mutex 占位并发门控防止翻译回调竞态 | 集成测试 | 代码审查 |
| 定界定位 | requestId staleness 检查区分过期 vs 有效翻译结果 | 代码评审 | 代码审查 |

## 多设备适配声明

无差异。

## 全局特性影响

| 特性 | 适用？ | 结论 | 关联场景 |
|------|--------|------|----------|
| 无障碍 | 不适用 | 无影响 — 翻译能力为框架内部 IPC 能力 | — |
| 大字体 | 不适用 | 无影响 — 翻译能力不涉及 UI 缩放 | — |
| 深色模式 | 不适用 | 无影响 — 翻译能力不涉及颜色主题 | — |
| 多窗口 | 适用 | 每窗口独立翻译会话和 translateManagerMap_ per-instance 路由 | 多窗口翻译 |
| 多用户 | 不适用 | 无影响 — 翻译能力不区分用户 | — |
| 版本升级 | 适用 | 无影响 — 无 Public/System API 契约 | — |
| 生态兼容 | 适用 | 新增翻译类型需同步更新 PageTranslateData / PageTranslateResult 类型定义 | 翻译类型扩展 |

## 行为场景（可选，Gherkin）

Feature: 翻译能力与DFX并发保护
  作为 SA 翻译工具开发者
  我想要 翻译能力与并发门控保护
  以便 安全可靠地进行页面翻译和语言查询

  Scenario: GetPageTranslateText 单次翻译完整流程
    Given SA 进程已连接 UiSession 服务
    And RegisterPageTranslateTextCallback 已注册翻译回调
    When GetPageTranslateText 被调用（requestId=1, src="zh", dst="en")
    Then requestId=1 注册至 translateManagerMap_
    And PostPageTranslateResultWatchdogTask(requestId=1) 启动看门狗
    When SendPageTranslateResult(requestId=1, result) 回写翻译结果
    Then CancelWatchdog 取消看门狗定时器
    And FinishPageTranslateTextRequest 单次模式标记完成并清理回调
    And requestId=1 对应回调从 translateManagerMap_ 移除

  Scenario: StartPageTranslateText 连续翻译回调持续触发
    Given SA 进程已连接 UiSession 服务
    And RegisterPageTranslateTextCallback 已注册翻译回调
    When StartPageTranslateText 被调用（requestId=1, src="zh", dst="en")
    Then 连续翻译回调注册至 translateManagerMap_
    When 第一个 requestId=1 翻译结果回写
    Then FinishPageTranslateTextRequest 连续模式仅标记 requestId=1 完成
    And 回调不清理，后续 requestId=2 继续触发翻译
    When EndPageTranslateText(requestId=2) 被调用
    Then 停止连续翻译会话
    And translateManagerMap_ 中回调清理

  Scenario: RegisterPageTranslateTextCallback mutex 占位并发门控
    Given SA 进程 A 已注册翻译回调（占位）
    When SA 进程 B RegisterPageTranslateTextCallback 注册新回调
    Then mutex lock 保护下新回调替换旧回调（进程 A 回调）
    And 进程 A 不再接收翻译结果
    And 进程 B 成为当前回调持有者（占位模式）

  Scenario Outline: HandlePageTranslateCallbackTimeout requestId 过期检查
    Given 翻译回调注册至 translateManagerMap_
    When HandlePageTranslateCallbackTimeout 触发超时检查
    And requestId <stale_status>
    Then <expected_behavior>

    Examples:
      | stale_status | expected_behavior |
      | 过期（当前 requestId 与存储 requestId 不匹配） | 丢弃翻译结果 + 移除回调 |
      | 未过期（当前 requestId 与存储 requestId 匹配） | 保留回调，后续结果可正常回写 |

  Scenario: PostPageTranslateResultWatchdogTask 超时触发清理
    Given GetPageTranslateText(requestId=1) 已发起
    And PostPageTranslateResultWatchdogTask(requestId=1) 看门狗已启动
    When 看门狗定时器超时且 SendPageTranslateResult 未回写
    Then HandlePageTranslateCallbackTimeout(requestId=1) 清理 requestId=1 和回调
    And requestId=1 从 translateManagerMap_ 移除

  Scenario: SendPageTranslateResult 回写三步联动
    Given GetPageTranslateText(requestId=1) 已发起
    And 看门狗已启动
    When SendPageTranslateResult(requestId=1, result) 成功回写
    Then CancelWatchdog 取消看门狗定时器
    And FinishPageTranslateTextRequest 标记 requestId=1 完成
    And 翻译结果回写至 requestId=1 对应回调

  Scenario: GetCurrentAbilityLanguageInfo LAST_UNFINISH 并发拒绝
    Given GetCurrentAbilityLanguageInfo 请求 1 正在执行（SyncRequestGuard CAS 成功）
    When GetCurrentAbilityLanguageInfo 请求 2 被调用
    Then CAS compare_exchange_strong(false, true) 失败（pending_ 已为 true）
    And acquired_=false
    And 立即返回 LAST_UNFINISH
    When 请求 1 完成（SyncRequestGuard 析构）
    Then pending_.store(false) 释放门控

  Scenario: ResetPageTranslateText per-node 重置
    Given 页面节点 A 已翻译为英文、节点 B 已翻译为英文
    When ResetPageTranslateText(nodeId=A) 指定 node id
    Then 节点 A 翻译状态重置恢复原始文本
    And 节点 B 翻译状态不变（仍为英文）

  Scenario: ResetPageTranslateText 全量重置
    Given 页面所有节点已翻译为英文
    When ResetPageTranslateText() 不指定 node id（全量模式）
    Then 所有节点翻译状态重置恢复原始文本

  Scenario: 翻译会话死亡清理
    Given SA 进程已注册翻译回调并发起翻译请求
    And 看门狗定时器已启动
    When SA 进程死亡触发 OnRemoteDied
    Then translateManagerMap_ 中该进程对应翻译回调被清理
    And 看门狗定时器取消

## Spec 自审清单

- [x] 无"待定""TBD""TODO"等占位符
- [x] 所有 AC 使用 WHEN/THEN 格式，可独立测试
- [x] 范围边界明确（做什么/不做什么清晰）
- [x] 无语义模糊表述（"快速""稳定""尽可能"等）
- [x] AC 与规则表交叉一致（每个 AC 至少关联一条规则，每条规则至少关联一个 AC）
- [x] 规则表每条通过 5 项质量检查（可复现/可观测/边界值/关联AC/无冲突）

## context-references

```yaml
context-queries:
  - repo: "openharmony/ace_engine"
    query: "Page translate 全流程 (ui_session_manager_ohos.cpp:1458-1578)"
  - repo: "openharmony/ace_engine"
    query: "RegisterPageTranslateTextCallback mutex 占位并发门控 (ui_session_manager_ohos.cpp:1458-1578)"
  - repo: "openharmony/ace_engine"
    query: "HandlePageTranslateCallbackTimeout requestId staleness 检查 (ui_session_manager_ohos.cpp:1458-1578)"
  - repo: "openharmony/ace_engine"
    query: "PostPageTranslateResultWatchdogTask 看门狗定时器 (ui_session_manager_ohos.cpp:1458-1578)"
  - repo: "openharmony/ace_engine"
    query: "FinishPageTranslateTextRequest 连续 vs 单次模式 (ui_session_manager_ohos.cpp:1458-1578)"
  - repo: "openharmony/ace_engine"
    query: "SendPageTranslateResult + CancelWatchdog + Finish 三步回写 (ui_session_manager_ohos.cpp:1458-1578)"
  - repo: "openharmony/ace_engine"
    query: "GetCurrentAbilityLanguageInfo + SyncRequestGuard + LAST_UNFINISH (ui_content_proxy.cpp:782-848)"
  - repo: "openharmony/ace_engine"
    query: "SyncRequestGuard RAII CAS compare_exchange_strong 实现 (ui_session_request_guard.h:23-41)"
  - repo: "openharmony/ace_engine"
    query: "UiReportStub translate IPC 事务码处理 (ui_report_stub.cpp:556-653)"
  - repo: "openharmony/ace_engine"
    query: "PageTranslateData / PageTranslateResult 类型定义 (ui_translate_type.h)"
  - repo: "openharmony/ace_engine"
    query: "translateManagerMap_ per-instance 路由 (ui_session_manager_ohos.cpp:1458-1578)"
  - repo: "openharmony/ace_engine"
    query: "PageTranslateNode ArkWeb 集成 (ui_session_manager_ohos.cpp:1458-1578)"
```

**关键文档：**
- [design.md](03-engine-framework/09-uisession/01-uisession-service/design.md)
