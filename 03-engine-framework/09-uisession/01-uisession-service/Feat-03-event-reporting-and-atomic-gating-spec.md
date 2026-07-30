# 特性规格

## 概述

| 属性 | 值 |
|------|-----|
| 特性名称 | 事件上报与注册计数门控 |
| 特性编号 | Func-03-09-01-Feat-03 |
| 所属 Epic | UiSession |
| 优先级 | P1 |
| 目标版本 | API 12+ |
| SIG 归属 | ArkUI SIG |
| 状态 | Baselined |
| 复杂度 | 标准 |

> 本 Feat 锁定 UiSession 事件上报与注册计数门控：9 类事件 atomic<int32_t> 注册计数模式、webFocusEvent bool+mutex 全局开关异常（ADR-2）、ComponentEventType bitmask 过滤、Register/Unregister 流程、广播至所有已连接 SA 进程、SelectTextEvent 立即上报、WebUnfocus NotifyAllWebPattern 广播。不涉及 IPC 安全框架（Feat-01）、InspectorTree 查询（Feat-02）、命令下发与同步请求（Feat-04）。

## 本次变更范围（Delta）

> 历史规格补齐，补录已有实现的完整行为规格。

| 类型 | 内容 | 说明 |
|------|------|------|
| ADDED | 9 类 atomic<int32_t> 事件注册计数门控规格 | ui_session_manager.h:310-380 click/search/textChange/router/componentChange/scroll/lifeCycle/selectText/pageSceneRule per-process 引用计数 fetch_add/fetch_sub |
| ADDED | webFocusEvent bool+mutex 全局开关规格 | ui_session_manager.h:310-380 webFocusEventRegistered_ bool + webFocusEventMutex_ mutex，全局开关而非 per-process 计数器（ADR-2） |
| ADDED | ComponentEventType bitmask 过滤规格 | param_config.h:58-78 16 位掩码 + NONE + ALL，ComponentChange 事件上报时双重过滤（计数器门控 + mask 检查） |
| ADDED | Register/Unregister 流程规格 | ui_session_manager_ohos.cpp:251-394 RegisterCallback fetch_add(1) + processMap_[key].insert(pid) + reportObjectMap_[pid] = proxy；UnregisterCallback fetch_sub(1) + processMap_[key].erase(pid) |
| ADDED | SelectTextEvent 立即上报规格 | ui_session_manager_ohos.cpp:815-937 RegisterSelectTextEventCallback 后立即触发一次 SelectTextEvent 上报 |
| ADDED | WebUnfocus NotifyAllWebPattern 广播规格 | ui_session_manager_ohos.cpp WebUnfocus 触发 notifyWebFunction_ 广播至所有 Web Pattern |

## 输入文档

- 关联设计：`03-engine-framework/09-uisession/01-uisession-service/design.md`
- 关联需求：已有能力补录（无独立 requirement.md）
- 源码定位（关键文件）：
  - `adapter/ohos/entrance/ui_session/ui_session_manager_ohos.cpp:251-394` — Register/Unregister 流程 + atomic 计数器
  - `adapter/ohos/entrance/ui_session/ui_session_manager_ohos.cpp:815-937` — Report*Event 方法 + 广播模式
  - `interfaces/inner_api/ui_session/ui_session_manager.h:310-380` — 9 atomic 计数器 + webFocusEvent bool+mutex + componentChangeEventMask_
  - `interfaces/inner_api/ui_session/param_config.h:58-78` — ComponentEventType 16 位掩码定义
  - `adapter/ohos/entrance/ui_session/ui_report_stub.cpp` — UiReportStub OnRemoteRequest + Register*Callback 管理
  - `adapter/ohos/entrance/ui_session/ui_content_proxy.cpp` — UIContentServiceProxy Register/Unregister IPC 代理

## 用户故事

### US-1: atomic 计数器事件注册门控

- As a SA 工具开发者
- I want 9 类事件使用 atomic<int32_t> per-process 引用计数，Register 时递增、Unregister 和 SA 死亡时递减
- So that 多 SA 进程可同时注册同一事件类型，计数器归零时停止上报 IPC 流量

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-1.1 | WHEN RegisterClickEventCallback 被调用 THEN clickEventRegisteredProcesses_ fetch_add(1)，processMap_[key].insert(pid)，reportObjectMap_[pid] = callback proxy。来源：`ui_session_manager_ohos.cpp:251-280` | 正常 |
| AC-1.2 | WHEN UnregisterClickEventCallback 被调用 THEN clickEventRegisteredProcesses_ fetch_sub(1)，processMap_[key].erase(pid)。来源：`ui_session_manager_ohos.cpp:281-300` | 正常 |
| AC-1.3 | WHEN SA 进程死亡触发 OnRemoteDied THEN fetch_sub(clickEventRegisteredProcesses_, 该进程注册计数)，同时 fetch_sub 所有 9 个 atomic 计数器恢复对应注册数。来源：`ui_content_proxy.cpp:134-162` | 正常 |
| AC-1.4 | WHEN 9 类 atomic 计数器中任意一个 > 0 THEN 对应 Report*Event 方法遍历 reportObjectMap_ 发送 IPC 上报至所有已注册 SA 进程。来源：`ui_session_manager_ohos.cpp:815-937` | 正常 |
| AC-1.5 | WHEN 9 类 atomic 计数器归零（值为 0） THEN 对应事件类型不发送 IPC 上报，节省流量。来源：`ui_session_manager_ohos.cpp:815-937` | 边界 |

### US-2: webFocusEvent bool+mutex 门控异常

- As a 框架维护者
- I want webFocusEvent 使用 bool + mutex 全局开关而非 per-process atomic 计数器（ADR-2 不一致性），规格标注此差异
- So that WebFocus 事件门控行为明确，后续统一为 atomic 计数器为可选改进

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-2.1 | WHEN RegisterWebFocusEventCallback 被调用 THEN webFocusEventRegistered_ 设为 true（mutex 保护下），所有进程共享此全局开关。来源：`ui_session_manager.h:310-380` | 正常 |
| AC-2.2 | WHEN UnregisterWebFocusEventCallback 或 SA 进程死亡 THEN webFocusEventRegistered_ reset false（mutex 保护下），全局开关关闭，所有进程不再收到 WebFocus 事件。来源：`ui_session_manager_ohos.cpp:251-394` | 正常 |
| AC-2.3 | WHEN webFocusEventRegistered_==true THEN ReportWebFocusEvent 遍历 reportObjectMap_ 发送 IPC 上报至所有已连接 SA 进程。来源：`ui_session_manager_ohos.cpp:815-937` | 正常 |
| AC-2.4 | WHEN webFocusEventRegistered_==false THEN ReportWebFocusEvent 不发送 IPC 上报。来源：`ui_session_manager_ohos.cpp:815-937` | 边界 |
| AC-2.5 | WHEN webFocusEventRegistered_ 被 reset false THEN 即使有其他 SA 进程仍希望接收 WebFocus 事件，全局开关关闭导致所有进程不再收到（ADR-2 不一致性）。来源：`ui_session_manager.h:310-380` | 异常 |

### US-3: ComponentEventType bitmask 双重过滤

- As a SA 工具开发者
- I want ComponentChange 事件在上报时通过 atomic 计数器门控 + ComponentEventType bitmask 双重过滤
- So that SA 工具可精确控制仅接收感兴趣的组件变更类型，减少无关事件通知

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-3.1 | WHEN RegisterComponentChangeEventCallback 被调用 THEN componentChangeEventRegisteredProcesses_ fetch_add(1)，同时传入 ComponentEventType mask 存入 componentChangeEventMask_。来源：`ui_session_manager_ohos.cpp:251-394` | 正常 |
| AC-3.2 | WHEN ReportComponentChangeEvent 被调用 THEN 先检查 componentChangeEventRegisteredProcesses_ > 0（计数器门控），再检查事件类型是否在 componentChangeEventMask_ 中（bitmask 过滤），双重过滤通过才发送 IPC 上报。来源：`ui_session_manager_ohos.cpp:815-937` | 正常 |
| AC-3.3 | WHEN ComponentEventType 包含 16 位掩码值 + NONE + ALL THEN NONE(0) 表示不接收任何变更类型，ALL(~0) 表示接收所有变更类型。来源：`param_config.h:58-78` | 正常 |
| AC-3.4 | WHEN ComponentEventType mask 中事件类型位未被设置 THEN 该类型 ComponentChange 事件不上报至 SA 进程，即使 atomic 计数器 > 0。来源：`ui_session_manager_ohos.cpp:815-937` | 边界 |

### US-4: SelectTextEvent 立即上报与 WebUnfocus 广播

- As a SA 工具开发者
- I want RegisterSelectTextEventCallback 后立即触发一次 SelectTextEvent 上报（提供当前选中文本状态），WebUnfocus 触发 NotifyAllWebPattern 广播
- So that SA 工具注册后立即获取当前选中文本，Web 失焦时通知所有 Web Pattern 处理

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-4.1 | WHEN RegisterSelectTextEventCallback 被调用 THEN selectTextEventRegisteredProcesses_ fetch_add(1)，并立即触发一次 SelectTextEvent 上报，将当前选中文本信息推送至 SA 进程。来源：`ui_session_manager_ohos.cpp:815-937` | 正常 |
| AC-4.2 | WHEN WebUnfocus 事件触发 THEN 调用 notifyWebFunction_（即 NotifyAllWebPattern），广播至所有 Web Pattern 通知失焦状态。来源：`ui_session_manager_ohos.cpp:815-937` | 正常 |
| AC-4.3 | WHEN UnregisterSelectTextEventCallback 被调用 THEN selectTextEventRegisteredProcesses_ fetch_sub(1)，后续不再上报 SelectText 事件。来源：`ui_session_manager_ohos.cpp:281-300` | 正常 |

## 验收追溯

| AC | 关联规则 | 关联 Task | 验证方式 | 证据 |
|----|----------|----------|----------|------|
| AC-1.1 | R-1 | TASK-SKELETON-3 | 集成测试 | 代码审查 |
| AC-1.2 | R-1 | TASK-SKELETON-3 | 集成测试 | 代码审查 |
| AC-1.3 | R-1 | TASK-SKELETON-3 | 集成测试：触发 OnRemoteDied | 代码审查 |
| AC-1.4 | R-4 | TASK-SKELETON-3 | 集成测试：2 SA proxy 注册 | 代码审查 |
| AC-1.5 | R-4 | TASK-SKELETON-3 | 代码评审 | 代码审查 |
| AC-2.1 | R-2 | TASK-SKELETON-3 | 集成测试 | 代码审查 |
| AC-2.2 | R-2 | TASK-SKELETON-3 | 集成测试 | 代码审查 |
| AC-2.3 | R-4 | TASK-SKELETON-3 | 集成测试 | 代码审查 |
| AC-2.4 | R-4 | TASK-SKELETON-3 | 代码评审 | 代码审查 |
| AC-2.5 | R-7 | TASK-SKELETON-3 | 代码评审（ADR-2 约束） | 代码审查 |
| AC-3.1 | R-3 | TASK-SKELETON-3 | 集成测试 | 代码审查 |
| AC-3.2 | R-3 / R-4 | TASK-SKELETON-3 | 集成测试：双重过滤 | 代码审查 |
| AC-3.3 | R-3 | TASK-SKELETON-3 | 代码评审 | 代码审查 |
| AC-3.4 | R-3 / R-4 | TASK-SKELETON-3 | 代码评审 | 代码审查 |
| AC-4.1 | R-5 | TASK-SKELETON-3 | 集成测试 | 代码审查 |
| AC-4.2 | R-6 | TASK-SKELETON-3 | 集成测试 | 代码审查 |
| AC-4.3 | R-1 | TASK-SKELETON-3 | 集成测试 | 代码审查 |

## 规则定义

| 规则ID | 类型 | 触发条件 | 预期行为 | 边界/约束 | 关联AC |
|--------|------|----------|----------|-----------|--------|
| R-1 | 行为 | 9 类 atomic 计数器事件 Register/Unregister | RegisterCallback: fetch_add(1) + processMap_[key].insert(pid) + reportObjectMap_[pid] = proxy。UnregisterCallback: fetch_sub(1) + processMap_[key].erase(pid)。SA 死亡: fetch_sub(该进程注册计数) + EraseProcessId。 | 9 类事件：click/search/textChange/router/componentChange/scroll/lifeCycle/selectText/pageSceneRule | AC-1.1 / AC-1.2 / AC-1.3 / AC-4.3 |
| R-2 | 行为 | webFocusEvent bool+mutex 门控 | Register: mutex lock → webFocusEventRegistered_=true。Unregister 或 SA 死亡: mutex lock → webFocusEventRegistered_=false。全局开关，所有进程共享，非 per-process。 | webFocusEvent bool+mutex 与其他 9 类 atomic 计数器不一致（ADR-2） | AC-2.1 / AC-2.2 |
| R-3 | 行为 | ComponentEventType bitmask 双重过滤 | RegisterComponentChangeEventCallback: fetch_add(1) + 传入 mask 存入 componentChangeEventMask_。ReportComponentChangeEvent: 计数器 > 0（门控） + 事件类型在 mask 中（bitmask 过滤），双重过滤通过才上报。 | NONE(0) 不接收任何类型，ALL(~0) 接收所有类型 | AC-3.1 / AC-3.2 / AC-3.3 / AC-3.4 |
| R-4 | 行为 | 事件广播至所有已连接 SA 进程 | 9 类 atomic 计数器事件：计数器 > 0 时遍历 reportObjectMap_ 发送 IPC。webFocusEvent：registered_==true 时遍历发送。广播模式，不做定向发送。 | 计数器归零（值为 0）时不发送 IPC | AC-1.4 / AC-1.5 / AC-2.3 / AC-2.4 / AC-3.2 / AC-3.4 |
| R-5 | 行为 | RegisterSelectTextEventCallback 立即上报 | Register 后立即触发一次 SelectTextEvent 上报，将当前选中文本信息推送至 SA 进程。 | 立即上报仅在 Register 时触发一次，后续上报由 selectTextFunction_ 回调驱动 | AC-4.1 |
| R-6 | 行为 | WebUnfocus NotifyAllWebPattern 广播 | WebUnfocus 事件触发 notifyWebFunction_（NotifyAllWebPattern），广播至所有 Web Pattern 通知失焦状态。 | notifyWebFunction_ 为 SaveRegisterForWebFunction 注册的回调 | AC-4.2 |
| R-7 | 异常 | webFocusEventRegistered_ reset false 导致其他 SA 进程丢失事件 | 全局开关关闭后所有进程不再收到 WebFocus 事件，即使其他 SA 进程仍希望接收（ADR-2 不一致性）。后续统一为 atomic 计数器为可选改进。 | 当前实现为全局 bool，非 per-process 计数器 | AC-2.5 |

## 验证映射

| VM编号 | AC / 规则 | 验证手段 | 位置 / 用例名 |
|-------|----------|---------|---------------|
| VM-1 | AC-1.1..1.5 / R-1 / R-4 | 集成测试 | Register/Unregister + atomic 计数器门控 + SA 死亡计数恢复 |
| VM-2 | AC-2.1..2.5 / R-2 / R-4 / R-7 | 集成测试 | webFocusEvent bool+mutex 门控 + 全局开关不一致性 |
| VM-3 | AC-3.1..3.4 / R-3 / R-4 | 集成测试 | ComponentEventType bitmask 双重过滤 |
| VM-4 | AC-4.1 / R-5 | 集成测试 | SelectTextEvent 立即上报 |
| VM-5 | AC-4.2 / R-6 | 集成测试 | WebUnfocus NotifyAllWebPattern 广播 |

## API 变更分析

### 新增 API

N/A，全部为 InnerApi（框架内部 IPC 接口）。无 Public/System API 变更。

### 变更/废弃 API

无。

## 接口规格

### 接口定义

**RegisterClickEventCallback**

| 属性 | 值 |
|------|-----|
| 函数签名 | `int32_t UiSessionManagerOhos::RegisterClickEventCallback(int32_t pid, const sptr<IRemoteObject>& object)` |
| 返回值 | `int32_t` — ERR_OK 或错误码 |
| 开放范围 | InnerApi |
| 错误码 | N/A |
| 关联 AC | AC-1.1 |

**行为场景**

| # | 触发条件 | 预期行为 | 关联 AC |
|---|----------|----------|---------|
| 1 | SA 进程首次 RegisterClickEventCallback | fetch_add(1) + processMap_[key].insert(pid) + reportObjectMap_[pid] = proxy | AC-1.1 |
| 2 | SA 进程 UnregisterClickEventCallback | fetch_sub(1) + processMap_[key].erase(pid) | AC-1.2 |

**RegisterWebFocusEventCallback**

| 属性 | 值 |
|------|-----|
| 函数签名 | `int32_t UiSessionManagerOhos::RegisterWebFocusEventCallback(int32_t pid, const sptr<IRemoteObject>& object)` |
| 返回值 | `int32_t` — ERR_OK 或错误码 |
| 开放范围 | InnerApi |
| 错误码 | N/A |
| 关联 AC | AC-2.1 |

**行为场景**

| # | 触发条件 | 预期行为 | 关联 AC |
|---|----------|----------|---------|
| 1 | RegisterWebFocusEventCallback | mutex lock → webFocusEventRegistered_=true（全局开关） | AC-2.1 |
| 2 | Unregister 或 SA 死亡 | mutex lock → webFocusEventRegistered_=false | AC-2.2 |
| 3 | 其他 SA 进程仍需 WebFocus 事件但全局开关被 reset | 所有进程不再收到事件（ADR-2 不一致性） | AC-2.5 |

**RegisterComponentChangeEventCallback**

| 属性 | 值 |
|------|-----|
| 函数签名 | `int32_t UiSessionManagerOhos::RegisterComponentChangeEventCallback(int32_t pid, const sptr<IRemoteObject>& object, uint32_t mask)` |
| 返回值 | `int32_t` — ERR_OK 或错误码 |
| 开放范围 | InnerApi |
| 错误码 | N/A |
| 关联 AC | AC-3.1 |

**参数约束**

| 参数 | 类型 | 必填 | 默认值 | 约束条件 |
|------|------|------|--------|---------|
| pid | int32_t | 是 | N/A | SA 进程 pid |
| object | sptr<IRemoteObject> | 是 | N/A | UiReportProxy remote object |
| mask | uint32_t | 是 | N/A | ComponentEventType bitmask (NONE=0, ALL=~0, 16 位掩码值) |

**行为场景**

| # | 触发条件 | 预期行为 | 关联 AC |
|---|----------|----------|---------|
| 1 | RegisterComponentChangeEventCallback(mask) | fetch_add(1) + 存入 mask | AC-3.1 |
| 2 | ReportComponentChangeEvent（事件类型在 mask 中） | 计数器 > 0 + mask 匹配 → 发送 IPC 上报 | AC-3.2 |
| 3 | ReportComponentChangeEvent（事件类型不在 mask 中） | mask 不匹配 → 不上报 | AC-3.4 |

**RegisterSelectTextEventCallback**

| 属性 | 值 |
|------|-----|
| 函数签名 | `int32_t UiSessionManagerOhos::RegisterSelectTextEventCallback(int32_t pid, const sptr<IRemoteObject>& object)` |
| 返回值 | `int32_t` — ERR_OK 或错误码 |
| 开放范围 | InnerApi |
| 错误码 | N/A |
| 关联 AC | AC-4.1 |

**行为场景**

| # | 触发条件 | 预期行为 | 关联 AC |
|---|----------|----------|---------|
| 1 | RegisterSelectTextEventCallback | fetch_add(1) + 立即触发一次 SelectTextEvent 上报 | AC-4.1 |

## 兼容性声明

- **已有 API 行为变更:** 否 — 全部为已有实现补录
- **配置文件格式变更:** 否
- **数据存储格式变更:** 否
- **最低支持版本:** API 12
- **API 版本号策略:** 无 @since 标注（框架内部 IPC 能力）
- **已知不一致性:** webFocusEvent 使用 bool+mutex 全局开关而非 per-process atomic 计数器（ADR-2），Unregister 或 SA 死亡时全局开关 reset false 导致所有进程丢失事件。后续统一为 atomic 计数器为可选改进，当前行为已确认并锁定。

## 架构约束

| 关键约束 | 约束说明 | 影响 AC |
|---------|----------|---------|
| atomic 计数器与 bool+mutex 不一致性 | 9 类事件使用 atomic<int32_t> per-process 引用计数，webFocusEvent 使用 bool+mutex 全局开关（ADR-2）。后续统一为 atomic 计数器为可选改进。 | AC-2.5 |
| 事件广播不可定向 | 所有事件上报均广播至 reportObjectMap_ 中所有已注册 SA 进程，不支持定向发送（ADR-1）。 | AC-1.4 |
| ComponentEventType mask 双重过滤 | ComponentChange 事件需要 atomic 计数器门控 + bitmask mask 双重过滤通过才上报，单一条件不满足即不上报。 | AC-3.2 / AC-3.4 |
| SelectTextEvent 立即上报仅 Register 时触发 | Register 后立即触发一次上报，后续上报由 selectTextFunction_ 回调驱动。 | AC-4.1 |
| SA 死亡时所有计数器批量恢复 | OnRemoteDied 需 fetch_sub 所有 9 个 atomic 计数器恢复对应注册数，webFocusEventRegistered_ reset false。 | AC-1.3 |

## 非功能性需求

| 类型 | 指标/阈值 | 验证方式 | 证据 |
|------|----------|----------|------|
| 性能 | atomic 计数器 fetch_add/fetch_sub 操作为 lock-free，无互斥开销 | 代码评审 | 代码审查 |
| 可观测 | 事件注册状态可通过 atomic 计数器值查询 | 代码评审 | 代码审查 |
| 可靠性 | atomic 计数器保证并发 Register/Unregister 正确性 | 单元测试 | 代码审查 |
| 安全 | webFocusEvent bool+mutex 全局开关可能影响多 SA 进程事件接收（ADR-2） | 代码评审 | 代码审查 |
| 定界定位 | 事件丢失可通过 atomic 计数器值与 reportObjectMap_ 条目数对比定位 | 代码评审 | 代码审查 |

## 多设备适配声明

无差异。

## 全局特性影响

| 特性 | 适用？ | 结论 | 关联场景 |
|------|--------|------|----------|
| 无障碍 | 不适用 | 无影响 — 事件上报为框架内部 IPC 能力 | — |
| 大字体 | 不适用 | 无影响 — 事件上报不涉及 UI 缩放 | — |
| 深色模式 | 不适用 | 无影响 — 事件上报不涉及颜色主题 | — |
| 多窗口 | 适用 | 每窗口独立事件注册计数，processMap_ 按 key 区分 | 多 SA 进程注册 |
| 多用户 | 不适用 | 无影响 — 事件上报不区分用户 | — |
| 版本升级 | 适用 | 无影响 — 无 Public/System API 契约 | — |
| 生态兼容 | 适用 | 新增事件类型需同步更新 atomic 计数器、Report 方法、UiReportProxy IPC 事务码 | 事件类型扩展 |

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
    query: "9 atomic<int32_t> 事件计数器定义 (ui_session_manager.h:310-380)"
  - repo: "openharmony/ace_engine"
    query: "webFocusEventRegistered_ bool + webFocusEventMutex_ mutex (ui_session_manager.h:310-380)"
  - repo: "openharmony/ace_engine"
    query: "componentChangeEventMask_ uint32_t bitmask (ui_session_manager.h:310-380)"
  - repo: "openharmony/ace_engine"
    query: "ComponentEventType 16 位掩码 + NONE + ALL 定义 (param_config.h:58-78)"
  - repo: "openharmony/ace_engine"
    query: "Register/Unregister 流程 + fetch_add/fetch_sub (ui_session_manager_ohos.cpp:251-394)"
  - repo: "openharmony/ace_engine"
    query: "Report*Event 方法 + 广播至所有 SA 进程 (ui_session_manager_ohos.cpp:815-937)"
  - repo: "openharmony/ace_engine"
    query: "SelectTextEvent 立即上报 on Register (ui_session_manager_ohos.cpp:815-937)"
  - repo: "openharmony/ace_engine"
    query: "WebUnfocus NotifyAllWebPattern broadcast (ui_session_manager_ohos.cpp)"
  - repo: "openharmony/ace_engine"
    query: "UiReportStub OnRemoteRequest + Register*Callback 管理 (ui_report_stub.cpp)"
  - repo: "openharmony/ace_engine"
    query: "UIContentServiceProxy Register/Unregister IPC 代理 (ui_content_proxy.cpp)"
```

**关键文档：**
- [design.md](03-engine-framework/09-uisession/01-uisession-service/design.md)
