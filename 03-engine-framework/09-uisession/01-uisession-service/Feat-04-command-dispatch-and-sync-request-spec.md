# 特性规格

## 概述

| 属性 | 值 |
|------|-----|
| 特性名称 | 命令下发与同步请求保护 |
| 特性编号 | Func-03-09-01-Feat-04 |
| 所属 Epic | UiSession |
| 优先级 | P1 |
| 目标版本 | API 12+ |
| SIG 归属 | ArkUI SIG |
| 状态 | Baselined |
| 复杂度 | 标准 |

> 本 Feat 锁定 UiSession 命令下发与同步请求保护：SendCommand 三变体（notifySendCommandFunction 同步、notifySendCommandAsyncFunction 异步、sendCommandFunction keycode、relaxedCommandFunction 宽松）、SendCommandAsync 错误码 11/12/13（ADR-5）、SyncRequestGuard RAII CAS atomic_bool 并发门控、GetCurrentAbilityLanguageInfo LAST_UNFINISH 处理。不涉及 IPC 安全框架（Feat-01）、InspectorTree 查询（Feat-02）、事件上报门控（Feat-03）。

## 本次变更范围（Delta）

> 历史规格补齐，补录已有实现的完整行为规格。

| 类型 | 内容 | 说明 |
|------|------|------|
| ADDED | SendCommand notify 同步命令规格 | ui_session_manager_ohos.cpp:1049-1131 notifySendCommandFunction → UI 线程 PostSyncTask 同步执行 |
| ADDED | SendCommandAsync 异步命令规格 | ui_session_manager_ohos.cpp:1049-1131 notifySendCommandAsyncFunction → UI 线程 PostSyncTask 异步执行，返回错误码 11/12/13 |
| ADDED | keycode dispatch via sendCommandFunction_ 规格 | ui_session_manager_ohos.cpp:1785-1813 keycode 通过 sendCommandFunction_ 路由分发 |
| ADDED | relaxedCommandFunction 宽松命令规格 | ui_session_manager_ohos.cpp SaveRelaxedCommandFunction 注册的宽松命令回调，不保证 UI 线程执行 |
| ADDED | SendCommandAsync 错误码 11/12/13 规格 | ui_content_service_interface.h:206-217 Code 11（TaskExecutor null / 回调未注册）、Code 12（自处理错误 / 默认返回值）、Code 13（node null） |
| ADDED | SyncRequestGuard RAII CAS concurrent gate 规格 | ui_session_request_guard.h:23-41 compare_exchange_strong(false, true) 单请求互斥，用于 GetCurrentAbilityLanguageInfo |
| ADDED | LAST_UNFINISH for concurrent language query 规格 | ui_content_proxy.cpp:1402-1434 GetCurrentAbilityLanguageInfo 同一时间仅一个请求执行，第二个请求立即返回 LAST_UNFINISH |

## 输入文档

- 关联设计：`03-engine-framework/09-uisession/01-uisession-service/design.md`
- 关联需求：已有能力补录（无独立 requirement.md）
- 源码定位（关键文件）：
  - `adapter/ohos/entrance/ui_session/ui_session_manager_ohos.cpp:1049-1131` — SendCommand / SendCommandAsync 流程
  - `adapter/ohos/entrance/ui_session/ui_session_manager_ohos.cpp:1785-1813` — keycode dispatch via sendCommandFunction_
  - `adapter/ohos/entrance/ui_session/ui_content_proxy.cpp:1402-1434` — GetCurrentAbilityLanguageInfo + SyncRequestGuard
  - `interfaces/inner_api/ui_session/ui_content_service_interface.h:206-217` — SendCommandAsync 错误码定义
  - `interfaces/inner_api/ui_session/ui_session_request_guard.h:23-41` — SyncRequestGuard RAII CAS 实现
  - `adapter/ohos/entrance/ui_content_impl.cpp:6253-6378` — InitUISessionManagerCallbacks ~25 回调注册

## 用户故事

### US-1: SendCommand notify 同步命令模式

- As a SA 工具开发者
- I want SendCommand 通过 notifySendCommandFunction 在 UI 线程同步执行命令，确保命令在当前帧内完成
- So that SA 工具可同步操控 UI 行为（如触发点击、滚动等），命令结果在当帧生效

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-1.1 | WHEN SendCommand 通过 notifySendCommandFunction 被调用 THEN UI 线程 PostSyncTask 同步执行命令回调，命令在当前帧内完成。来源：`ui_session_manager_ohos.cpp:1049-1131` | 正常 |
| AC-1.2 | WHEN notifySendCommandFunction_ 回调未注册（nullptr） THEN SendCommand 不执行，返回默认值。来源：`ui_session_manager_ohos.cpp:1049-1131` | 异常 |
| AC-1.3 | WHEN SendCommand 通过 sendCommandFunction_ 路由 keycode THEN keycode 事件通过 sendCommandFunction_ 分发至对应组件处理。来源：`ui_session_manager_ohos.cpp:1785-1813` | 正常 |

### US-2: SendCommandAsync 异步命令与错误码

- As a SA 工具开发者
- I want SendCommandAsync 通过 notifySendCommandAsyncFunction 在 UI 线程异步执行命令，返回错误码 11/12/13 标示不同失败类型
- So that SA 工具可异步操控 UI 行为并根据错误码判断失败原因和后续策略

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-2.1 | WHEN SendCommandAsync 通过 notifySendCommandAsyncFunction 被调用 THEN UI 线程 PostSyncTask 异步执行命令回调，命令可能在当前帧或后续帧完成。来源：`ui_session_manager_ohos.cpp:1049-1131` | 正常 |
| AC-2.2 | WHEN notifySendCommandAsyncFunction_ 回调未注册（null callback） THEN SendCommandAsync 返回错误码 11（TaskExecutor null / 回调未注册），表示需要重新初始化。来源：`ui_content_service_interface.h:206-217` | 异常 |
| AC-2.3 | WHEN SendCommandAsync 命令执行的目标 node 为 null THEN 返回错误码 13（node null），表示目标节点已销毁需 UI 更新。来源：`ui_content_service_interface.h:206-217` | 异常 |
| AC-2.4 | WHEN SendCommandAsync 命令执行返回默认结果值 THEN 返回错误码 12（自处理错误），表示组件自处理返回默认值。来源：`ui_content_service_interface.h:206-217` | 边界 |
| AC-2.5 | WHEN Code 10（Pipeline null）在接口注释中文档化 THEN 当前 lambda 实现中 Pipeline 为空时不执行到返回路径，Code 10 实际未被产出。来源：`ui_content_service_interface.h:206-217` | 边界 |

### US-3: relaxedCommandFunction 宽松命令回退

- As a 框架维护者
- I want SaveRelaxedCommandFunction 注册的宽松命令回调不保证 UI 线程执行，作为 SendCommand 的宽松回退路径
- So that 不严格需要 UI 线程同步的命令可走宽松路径，降低 UI 线程负载

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-3.1 | WHEN relaxedCommandFunction_ 回调被调用 THEN 不保证在 UI 线程执行，可能在 binder 线程或其他线程执行。来源：`ui_session_manager_ohos.cpp` | 正常 |
| AC-3.2 | WHEN relaxedCommandFunction_ 回调未注册（nullptr） THEN 宽松命令不执行，返回默认值。来源：`ui_session_manager_ohos.cpp` | 异常 |
| AC-3.3 | WHEN SendCommand 同步路径与 relaxedCommand 宽松路径并存 THEN 严格需要 UI 线程同步的命令走 notifySendCommandFunction，非严格命令走 relaxedCommandFunction。来源：`ui_session_manager_ohos.cpp:1049-1131` | 正常 |

### US-4: SyncRequestGuard 并发门控与语言查询

- As a 框架并发安全维护者
- I want SyncRequestGuard 通过 RAII CAS atomic_bool 保证同一时间仅一个请求执行，GetCurrentAbilityLanguageInfo 第二个并发请求立即返回失败
- So that 防止多个 SA 进程同时发起同步语言查询导致 Pipeline 竞态

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-4.1 | WHEN GetCurrentAbilityLanguageInfo 被调用 THEN SyncRequestGuard 构造时 CAS compare_exchange_strong(false, true)，第一个请求 acquired_=true 成功执行。来源：`ui_session_request_guard.h:23-41` | 正常 |
| AC-4.2 | WHEN 第二个 GetCurrentAbilityLanguageInfo 在第一个请求未完成时被调用 THEN SyncRequestGuard CAS compare_exchange_strong(false, true) 失败（pending_ 已为 true），acquired_=false，立即返回 LAST_UNFINISH。来源：`ui_content_proxy.cpp:1402-1434` | 正常 |
| AC-4.3 | WHEN 第一个请求完成（SyncRequestGuard 析构） THEN pending_.store(false) 释放门控，后续请求可正常获取。来源：`ui_session_request_guard.h:23-41` | 恢复 |
| AC-4.4 | WHEN SyncRequestGuard 构造时 acquired_=false（未获取门控） THEN 析构时不操作 pending_（不执行 pending_.store(false)），避免误释放未持有的门控。来源：`ui_session_request_guard.h:23-41` | 边界 |
| AC-4.5 | WHEN SyncRequestGuard 与 RegisterPageTranslateTextCallback mutex 占位两种并发门控并存 THEN 两者语义不同：SyncRequestGuard CAS 保证"谁先到谁执行"，mutex 占位保证"谁占位谁持有"（ADR-3）。来源：`ui_session_request_guard.h:23-41` | 正常 |

## 验收追溯

| AC | 关联规则 | 关联 Task | 验证方式 | 证据 |
|----|----------|----------|----------|------|
| AC-1.1 | R-1 | TASK-SKELETON-4 | 集成测试 | 代码审查 |
| AC-1.2 | R-2 | TASK-SKELETON-4 | 集成测试：mock null callback | 代码审查 |
| AC-1.3 | R-4 | TASK-SKELETON-4 | 集成测试：keycode 分发 | 代码审查 |
| AC-2.1 | R-1 | TASK-SKELETON-4 | 集成测试 | 代码审查 |
| AC-2.2 | R-2 | TASK-SKELETON-4 | 单元测试：mock null callback | 代码审查 |
| AC-2.3 | R-3 | TASK-SKELETON-4 | 单元测试：mock null node | 代码审查 |
| AC-2.4 | R-2 | TASK-SKELETON-4 | 代码评审 | 代码审查 |
| AC-2.5 | R-2 | TASK-SKELETON-4 | 代码评审（ADR-5 约束） | 代码审查 |
| AC-3.1 | R-5 | TASK-SKELETON-4 | 代码评审 | 代码审查 |
| AC-3.2 | R-5 | TASK-SKELETON-4 | 代码评审 | 代码审查 |
| AC-3.3 | R-5 | TASK-SKELETON-4 | 代码评审 | 代码审查 |
| AC-4.1 | R-6 | TASK-SKELETON-4 | 集成测试：CAS 成功 | 代码审查 |
| AC-4.2 | R-6 / R-7 | TASK-SKELETON-4 | 集成测试：CAS 失败 → LAST_UNFINISH | 代码审查 |
| AC-4.3 | R-6 | TASK-SKELETON-4 | 单元测试 | 代码审查 |
| AC-4.4 | R-6 | TASK-SKELETON-4 | 单元测试 | 代码审查 |
| AC-4.5 | R-6 | TASK-SKELETON-4 | 代码评审（ADR-3） | 代码审查 |

## 规则定义

| 规则ID | 类型 | 触发条件 | 预期行为 | 边界/约束 | 关联AC |
|--------|------|----------|----------|-----------|--------|
| R-1 | 行为 | SendCommand notify 同步命令调用 | notifySendCommandFunction_ → UI 线程 PostSyncTask 同步执行命令回调，命令在当前帧内完成。notifySendCommandAsyncFunction_ → UI 线程 PostSyncTask 异步执行命令回调，命令可能在当前帧或后续帧完成。 | 同步 vs 异步：同步 PostSyncTask 等待完成，异步 PostSyncTask 不等待 | AC-1.1 / AC-2.1 |
| R-2 | 异常 | notifySendCommandAsyncFunction_ 回调未注册（null callback） | SendCommandAsync 返回错误码 11（TaskExecutor null / 回调未注册），表示需要重新初始化。返回错误码 12（自处理错误 / 默认返回值），表示组件自处理返回默认值。 | Code 10 在接口注释中文档化但当前 lambda 未产出（ADR-5）；错误码 11 为默认基类返回值 | AC-1.2 / AC-2.2 / AC-2.4 / AC-2.5 |
| R-3 | 异常 | SendCommandAsync 目标 node 为 null | 返回错误码 13（node null），表示目标节点已销毁需 UI 更新。 | node null 通常发生在节点已析构但命令仍尝试访问的场景 | AC-2.3 |
| R-4 | 行为 | keycode dispatch via sendCommandFunction_ | keycode 事件通过 sendCommandFunction_ 路由分发至对应组件处理，UI 线程执行。 | keycode 与常规命令路径不同，走 sendCommandFunction_ 而非 notifySendCommandFunction_ | AC-1.3 |
| R-5 | 行为 | relaxedCommandFunction 宽松命令 | SaveRelaxedCommandFunction 注册的宽松命令回调不保证 UI 线程执行，可能在 binder 线程或其他线程执行。回调未注册时返回默认值。 | 严格需要 UI 线程同步的命令走 notifySendCommandFunction，非严格命令走 relaxedCommandFunction | AC-3.1 / AC-3.2 / AC-3.3 |
| R-6 | 行为 | SyncRequestGuard RAII CAS concurrent gate | 构造时 compare_exchange_strong(false, true)：第一个请求 acquired_=true 成功执行。第二个请求 acquired_=false 立即返回 LAST_UNFINISH。析构时：若 acquired_=true 则 pending_.store(false) 释放门控；若 acquired_=false 则不操作 pending_。 | CAS 保证同一时间仅一个请求执行；与 RegisterPageTranslateTextCallback mutex 占位语义不同（ADR-3） | AC-4.1 / AC-4.2 / AC-4.3 / AC-4.4 / AC-4.5 |
| R-7 | 边界 | GetCurrentAbilityLanguageInfo LAST_UNFINISH | 第二个并发请求 acquired_=false 时立即返回 LAST_UNFINISH，不等待第一个请求完成。 | LAST_UNFINISH 为特殊返回值，表示"上次请求尚未完成" | AC-4.2 |

## 验证映射

| VM编号 | AC / 规则 | 验证手段 | 位置 / 用例名 |
|-------|----------|---------|---------------|
| VM-1 | AC-1.1 / R-1 | 集成测试 | SendCommand notify 同步命令流程 |
| VM-2 | AC-1.2 / R-2 | 集成测试 | mock null callback 返回错误码 11 |
| VM-3 | AC-1.3 / R-4 | 集成测试 | keycode dispatch via sendCommandFunction_ |
| VM-4 | AC-2.1..2.5 / R-1 / R-2 / R-3 | 单元测试 | SendCommandAsync 错误码 11/12/13 路径 |
| VM-5 | AC-3.1..3.3 / R-5 | 代码评审 | relaxedCommandFunction 宽松路径对照 |
| VM-6 | AC-4.1..4.5 / R-6 / R-7 | 单元测试 | SyncRequestGuard CAS + LAST_UNFINISH |

## API 变更分析

### 新增 API

N/A，全部为 InnerApi（框架内部 IPC 接口）。无 Public/System API 变更。

### 变更/废弃 API

无。

## 接口规格

### 接口定义

**SendCommandAsync**

| 属性 | 值 |
|------|-----|
| 函数签名 | `int32_t IUiContentService::SendCommandAsync(const std::string& command, const std::string& params)` |
| 返回值 | `int32_t` — 0(成功) / 11(回调未注册) / 12(自处理错误) / 13(node null) |
| 开放范围 | InnerApi |
| 错误码 | 0 / 10(接口注释中文档化但当前 lambda 实现不可达，实际不产出) / 11 / 12 / 13 |
| 关联 AC | AC-2.1 / AC-2.2 / AC-2.3 / AC-2.4 |

**参数约束**

| 参数 | 类型 | 必填 | 默认值 | 约束条件 |
|------|------|------|--------|---------|
| command | std::string | 是 | N/A | 命令标识符 |
| params | std::string | 是 | N/A | 命令参数 JSON |

**行为场景**

| # | 触发条件 | 预期行为 | 关联 AC |
|---|----------|----------|---------|
| 1 | notifySendCommandAsyncFunction_ 回调已注册且 node 有效 | 异步执行命令，返回 0（成功） | AC-2.1 |
| 2 | notifySendCommandAsyncFunction_ 回调未注册（null） | 返回错误码 11 | AC-2.2 |
| 3 | 目标 node 为 null | 返回错误码 13 | AC-2.3 |
| 4 | 命令执行返回默认结果值 | 返回错误码 12 | AC-2.4 |

**SyncRequestGuard**

| 属性 | 值 |
|------|-----|
| 函数签名 | `SyncRequestGuard(std::atomic_bool& pending)` |
| 返回值 | N/A（构造函数） |
| 开放范围 | InnerApi |
| 错误码 | N/A |
| 关联 AC | AC-4.1 / AC-4.2 / AC-4.3 |

**参数约束**

| 参数 | 类型 | 必填 | 默认值 | 约束条件 |
|------|------|------|--------|---------|
| pending | std::atomic_bool& | 是 | N/A | CAS 门控标志，初始值 false |

**行为场景**

| # | 触发条件 | 预期行为 | 关联 AC |
|---|----------|----------|---------|
| 1 | CAS compare_exchange_strong(false, true) 成功 | acquired_=true，请求正常执行 | AC-4.1 |
| 2 | CAS compare_exchange_strong(false, true) 失败 | acquired_=false，立即返回 LAST_UNFINISH | AC-4.2 |
| 3 | 析构且 acquired_=true | pending_.store(false) 释放门控 | AC-4.3 |
| 4 | 析构且 acquired_=false | 不操作 pending_ | AC-4.4 |

**GetCurrentAbilityLanguageInfo**

| 属性 | 值 |
|------|-----|
| 函数签名 | `int32_t IUiContentService::GetCurrentAbilityLanguageInfo(AbilityLanguageInfo& info)` |
| 返回值 | `int32_t` — ERR_OK 或 LAST_UNFINISH |
| 开放范围 | InnerApi |
| 错误码 | LAST_UNFINISH（并发请求拒绝） |
| 关联 AC | AC-4.1 / AC-4.2 |

**参数约束**

| 参数 | 类型 | 必填 | 默认值 | 约束条件 |
|------|------|------|--------|---------|
| info | AbilityLanguageInfo& | 是 | N/A | 出参，应用语言信息 |

**行为场景**

| # | 触发条件 | 预期行为 | 关联 AC |
|---|----------|----------|---------|
| 1 | 第一个请求 CAS 成功 | 获取语言信息，返回 ERR_OK | AC-4.1 |
| 2 | 第二个并发请求 CAS 失败 | 立即返回 LAST_UNFINISH | AC-4.2 |
| 3 | 第一个请求完成后 | pending_ 释放，后续请求可正常获取 | AC-4.3 |

## 兼容性声明

- **已有 API 行为变更:** 否 — 全部为已有实现补录
- **配置文件格式变更:** 否
- **数据存储格式变更:** 否
- **最低支持版本:** API 12
- **API 版本号策略:** 无 @since 标注（框架内部 IPC 能力）
- **已知不可达错误码:** SendCommandAsync Code 10（Pipeline null）在接口注释中文档化（ADR-5），但当前 lambda 实现中 Pipeline 为空时不执行到返回路径，Code 10 实际不可达。下游工具不应依赖 Code 10 进行错误处理。

## 架构约束

| 关键约束 | 约束说明 | 影响 AC |
|---------|----------|---------|
| 双并发门控模式差异 | PageTranslate mutex 占位 vs SyncRequestGuard CAS 语义不同：mutex 保护"谁占位"，CAS 保证"谁先到谁执行"（ADR-3） | AC-4.5 |
| SendCommandAsync Code 10 未产出 | 接口注释文档化 Code 10（Pipeline null）但当前 lambda 未产出；下游工具需注意实际可返回 11/12/13（ADR-5） | AC-2.5 |
| SyncRequestGuard RAII 释放 | 析构时仅 acquired_=true 才释放 pending_，acquired_=false 不操作，避免误释放未持有的门控 | AC-4.4 |
| keycode 路径独立 | keycode 事件通过 sendCommandFunction_ 路由而非 notifySendCommandFunction_，与常规命令路径分离 | AC-1.3 |
| 21 个 Save* + 2 个 Set* + 2 个 Register* = 25 个回调注册方法 | InitUISessionManagerCallbacks 注册约 25 个回调至 UiSessionManager，每个回调有对应的 mutex 保护 | AC-1.1 |

## 非功能性需求

| 类型 | 指标/阈值 | 验证方式 | 证据 |
|------|----------|----------|------|
| 性能 | SyncRequestGuard CAS 操作为 lock-free，无互斥开销 | 代码评审 | 代码审查 |
| 可观测 | SendCommandAsync 错误码可通过 IPC 返回值追踪 | IPC 数据抓取 | 集成测试 |
| 可靠性 | SyncRequestGuard RAII 保证门控自动释放 | 单元测试 | 代码审查 |
| 安全 | CAS 门控防止并发语言查询竞态 | 集成测试 | 代码审查 |
| 定界定位 | SendCommandAsync 错误码区分失败类型：11（初始化）/ 12（自处理）/ 13（节点销毁） | 代码评审 | 代码审查 |

## 多设备适配声明

无差异。

## 全局特性影响

| 特性 | 适用？ | 结论 | 关联场景 |
|------|--------|------|----------|
| 无障碍 | 不适用 | 无影响 — 命令下发为框架内部 IPC 能力 | — |
| 大字体 | 不适用 | 无影响 — 命令下发不涉及 UI 缩放 | — |
| 深色模式 | 不适用 | 无影响 — 命令下发不涉及颜色主题 | — |
| 多窗口 | 适用 | 每窗口独立命令分发和 SyncRequestGuard 门控 | 多 SA 进程命令 |
| 多用户 | 不适用 | 无影响 — 命令下发不区分用户 | — |
| 版本升级 | 适用 | 无影响 — 无 Public/System API 契约 | — |
| 生态兼容 | 适用 | 新增命令类型需同步更新 notifySendCommandFunction_ / sendCommandFunction_ 回调注册 | SendCommand 扩展 |

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
    query: "SendCommand / SendCommandAsync 流程 (ui_session_manager_ohos.cpp:1049-1131)"
  - repo: "openharmony/ace_engine"
    query: "keycode dispatch via sendCommandFunction_ (ui_session_manager_ohos.cpp:1785-1813)"
  - repo: "openharmony/ace_engine"
    query: "SendCommandAsync 错误码 11/12/13 定义 (ui_content_service_interface.h:206-217)"
  - repo: "openharmony/ace_engine"
    query: "SyncRequestGuard RAII CAS compare_exchange_strong 实现 (ui_session_request_guard.h:23-41)"
  - repo: "openharmony/ace_engine"
    query: "GetCurrentAbilityLanguageInfo + LAST_UNFINISH (ui_content_proxy.cpp:1402-1434)"
  - repo: "openharmony/ace_engine"
    query: "InitUISessionManagerCallbacks ~25 回调注册 (ui_content_impl.cpp:6253-6378)"
  - repo: "openharmony/ace_engine"
    query: "SaveForSendCommandFunction / SaveForSendCommandAsyncFunction / SaveRelaxedCommandFunction / SaveSendCommandFunction (ui_session_manager.h:130-131,248-249)"
  - repo: "openharmony/ace_engine"
    query: "NotifySendCommandFunction / NotifySendCommandAsyncFunction 签名 (ui_session_manager.h:52-53)"
```

**关键文档：**
- [design.md](03-engine-framework/09-uisession/01-uisession-service/design.md)
