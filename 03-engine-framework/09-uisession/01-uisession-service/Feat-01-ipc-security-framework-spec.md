# 特性规格

## 概述

| 属性 | 值 |
|------|-----|
| 特性名称 | IPC安全框架与连接生命周期 |
| 特性编号 | Func-03-09-01-Feat-01 |
| 所属 Epic | UiSession |
| 优先级 | P1 |
| 目标版本 | API 12+ |
| SIG 归属 | ArkUI SIG |
| 状态 | Baselined |
| 复杂度 | 复杂 |

> 本 Feat 锁定 UiSession IPC 安全框架与连接生命周期管理：UiContentStub OnRemoteRequest SA-only 门控（IsSACalling + interface token）、ConnectInner 连接建立（reportStub + handler + isConnected）、SaveReportStub + UiReportProxyRecipient 死亡监听、SendBaseInfo 连接后初始数据推送、UIContentServiceProxy Connect 生命周期与 app 死亡清理（UIContentProxyRecipient）。不涉及 InspectorTree 查询（Feat-02）、事件上报门控（Feat-03）、命令下发与同步请求（Feat-04）。

## 本次变更范围（Delta）

> 历史规格补齐，补录已有实现的完整行为规格。

| 类型 | 内容 | 说明 |
|------|------|------|
| ADDED | OnRemoteRequest SA-only 门控规格 | ui_content_stub.cpp:45-265 IsSACalling + interface token 校验，52 事务码统一 SA-level 门控，无 per-method 权限区分 |
| ADDED | ConnectInner 连接生命周期规格 | ui_session_manager_ohos.cpp:396-449 reportStub 创建 + handler 注册 + isConnected 标记 |
| ADDED | SaveReportStub + UiReportProxyRecipient 死亡监听规格 | ui_session_manager_ohos.cpp SaveReportStub 存储 UiReportProxy remote object，UiReportProxyRecipient 监听 SA 进程死亡触发 ordered cleanup |
| ADDED | SendBaseInfo 连接后初始数据推送规格 | ui_session_manager_ohos.cpp SendBaseInfo 在 Connect 成功后推送基础信息至 SA |
| ADDED | UIContentProxyRecipient app 死亡清理规格 | ui_content_proxy.cpp:134-162 OnRemoteDied ordered locks → state reset → manager calls（ADR-6） |

## 输入文档

- 关联设计：`03-engine-framework/09-uisession/01-uisession-service/design.md`
- 关联需求：已有能力补录（无独立 requirement.md）
- 源码定位（关键文件）：
  - `adapter/ohos/entrance/ui_session/ui_content_stub.cpp:45-265` — OnRemoteRequest 分发 + IsSACalling + interface token 校验
  - `adapter/ohos/entrance/ui_session/ui_session_manager_ohos.cpp:396-449` — ConnectInner / SaveReportStub / SendBaseInfo
  - `adapter/ohos/entrance/ui_session/ui_content_proxy.cpp:134-162` — UIContentProxyRecipient OnRemoteDied ordered cleanup
  - `interfaces/inner_api/ui_session/ui_content_service_interface.h` — IUiContentService 52 IPC 事务码定义
  - `adapter/ohos/entrance/ui_session/ui_content_stub_impl.cpp` — StubImpl 委托转发至 UiSessionManager::GetInstance()

## 用户故事

### US-1: SA-only 访问门控拒绝非 SA 进程

- As a 框架安全维护者
- I want OnRemoteRequest 入口处统一校验调用方为 SA 进程，非 SA 进程 IPC 调用被直接拒绝
- So that UiSession IPC 接口仅对系统 SA 进程开放，防止第三方进程非法访问

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-1.1 | WHEN OnRemoteRequest 收到任意 IPC 事务码 THEN 先调用 IsSACalling() 验证调用方进程为 SA 进程。来源：`ui_content_stub.cpp:45-80` | 正常 |
| AC-1.2 | WHEN IsSACalling() 返回 false THEN OnRemoteRequest 直接返回 IPC_STUB_INVALID_DATA 错误码，不进入事务码分发逻辑。来源：`ui_content_stub.cpp:48-55` | 异常 |
| AC-1.3 | WHEN 52 个 IPC 事务码中任意一个被 SA 进程调用 THEN 统一通过 SA-level 门控，不区分具体方法权限（ADR-1）。来源：`ui_content_stub.cpp:45-265` | 正常 |
| AC-1.4 | WHEN OnRemoteRequest 收到 interface token 与 IUiContentService 定义不匹配 THEN 返回 IPC_STUB_INVALID_DATA 错误码，拒绝本次 IPC 调用。来源：`ui_content_stub.cpp:56-70` | 异常 |

### US-2: Connect 连接生命周期建立

- As a SA 进程开发者
- I want ConnectInner 在 SA 进程首次请求时创建 reportStub、注册 handler、标记 isConnected，完成双向 IPC 通道建立
- So that SA 进程可后续通过 UiReportProxy 接收 app 上报的事件数据

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-2.1 | WHEN ConnectInner 被调用且当前进程未连接 THEN 创建 UiReportProxy remote object 存入 reportObjectMap_，注册 event handler，标记 isConnected_=true。来源：`ui_session_manager_ohos.cpp:396-415` | 正常 |
| AC-2.2 | WHEN ConnectInner 成功完成 THEN SaveReportStub 将 UiReportProxy remote object 按 pid 存入 reportObjectMap_，后续 Report* 方法通过该 proxy 广播上报。来源：`ui_session_manager_ohos.cpp:416-430` | 正常 |
| AC-2.3 | WHEN ConnectInner 被调用且当前进程已连接（isConnected_=true） THEN 不重复创建 reportStub，保持现有连接状态。来源：`ui_session_manager_ohos.cpp:396-415` | 边界 |
| AC-2.4 | WHEN ConnectInner 创建 reportStub 后 THEN SendBaseInfo 被调用，将当前 app 基础信息（页面名、窗口尺寸等）推送至 SA 进程。来源：`ui_session_manager_ohos.cpp:431-449` | 正常 |

### US-3: UiReportProxyRecipient SA 死亡监听与清理

- As a 框架稳定性维护者
- I want UiReportProxyRecipient 监听 SA 进程死亡通知，触发 ordered cleanup 恢复 app 进程侧状态
- So that SA 进程崩溃或退出后 app 进程侧的 IPC 资源和计数器被正确回收，避免悬空引用

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-3.1 | WHEN SA 进程死亡触发 UiReportProxyRecipient::OnRemoteDied THEN 按 ordered locks → state reset → manager calls 顺序执行清理（ADR-6）。来源：`ui_content_proxy.cpp:134-162` | 正常 |
| AC-3.2 | WHEN ordered locks 阶段 THEN 获取 processMapMutex_、webFocusEventMutex_ 等锁，防止并发访问已失效数据。来源：`ui_content_proxy.cpp:134-140` | 正常 |
| AC-3.3 | WHEN state reset 阶段 THEN 执行 EraseProcessId(key, pid) 移除进程映射、reportObjectMap_ erase pid 移除 proxy 对象、fetch_sub 所有 9 个 atomic 事件计数器恢复注册计数、webFocusEventRegistered_ reset false。来源：`ui_content_proxy.cpp:141-152` | 正常 |
| AC-3.4 | WHEN manager calls 阶段且 pageTranslateOwnerPid_ 匹配死亡进程 THEN 调用 ResetTranslate() 和 ResetPageTransition() 清理翻译回调资源。来源：`ui_content_proxy.cpp:153-162` | 正常 |
| AC-3.5 | WHEN SA 死亡清理违反 ordered locks → state reset → manager calls 顺序 THEN 可能导致悬空引用或并发访问已失效数据。来源：`ui_content_proxy.cpp:134-162`（ADR-6 强制要求此顺序） | 异常 |

### US-4: 事件广播模式（所有已连接 SA）

- As a SA 工具开发者
- I want 事件上报广播至所有已连接 SA 进程，不做定向发送
- So that 多个 SA 工具（如 Inspector、HiSysEvent、DFX）可同时接收同一事件

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-4.1 | WHEN Report*Event 方法被调用且对应事件计数器 > 0 THEN 遍历 reportObjectMap_ 中所有已注册 SA 进程的 UiReportProxy，逐一发送 IPC 上报。来源：`ui_session_manager_ohos.cpp:251-394`（ADR-1 广播模式） | 正常 |
| AC-4.2 | WHEN 多个 SA 进程同时注册同一事件 THEN 所有注册进程均收到广播上报，无定向过滤。来源：`ui_session_manager_ohos.cpp:251-394` | 正常 |
| AC-4.3 | WHEN reportObjectMap_ 为空（无 SA 进程注册） THEN 事件上报 IPC 不被发送，atomic 计数器仍递增/递减但不产生 IPC 流量。来源：`ui_session_manager_ohos.cpp:251-280` | 边界 |

## 验收追溯

| AC | 关联规则 | 关联 Task | 验证方式 | 证据 |
|----|----------|----------|----------|------|
| AC-1.1 | R-1 | TASK-SKELETON-1 | 集成测试：mock SA caller | 代码审查 |
| AC-1.2 | R-1 | TASK-SKELETON-1 | 集成测试：mock 非 SA caller | 代码审查 |
| AC-1.3 | R-1 | TASK-SKELETON-1 | 代码评审 | 代码审查 |
| AC-1.4 | R-2 | TASK-SKELETON-1 | 集成测试：发送错误 interface token | 代码审查 |
| AC-2.1 | R-3 | TASK-SKELETON-1 | 集成测试：首次 Connect 调用 | 代码审查 |
| AC-2.2 | R-4 | TASK-SKELETON-1 | 集成测试：Connect 后 Report* 可广播 | 代码审查 |
| AC-2.3 | R-3 | TASK-SKELETON-1 | 集成测试：重复 Connect 调用 | 代码审查 |
| AC-2.4 | R-5 | TASK-SKELETON-1 | 集成测试：Connect 后 SendBaseInfo 推送 | 代码审查 |
| AC-3.1 | R-6 / R-7 | TASK-SKELETON-1 | 集成测试：触发 OnRemoteDied | 代码审查 |
| AC-3.2 | R-6 | TASK-SKELETON-1 | 代码评审 | 代码审查 |
| AC-3.3 | R-7 | TASK-SKELETON-1 | 代码评审 | 代码审查 |
| AC-3.4 | R-7 | TASK-SKELETON-1 | 集成测试：翻译占位进程死亡 | 代码审查 |
| AC-3.5 | R-8 | TASK-SKELETON-1 | 代码评审（ADR-6 约束） | 代码审查 |
| AC-4.1 | R-9 | TASK-SKELETON-1 | 集成测试：2 SA proxy 注册验证均收到事件 | 代码审查 |
| AC-4.2 | R-9 | TASK-SKELETON-1 | 集成测试 | 代码审查 |
| AC-4.3 | R-9 | TASK-SKELETON-1 | 代码评审 | 代码审查 |

## 规则定义

| 规则ID | 类型 | 触发条件 | 预期行为 | 边界/约束 | 关联AC |
|--------|------|----------|----------|-----------|--------|
| R-1 | 行为 | OnRemoteRequest 收到任意 IPC 事务码 | 先调用 IsSACalling() 验证调用方为 SA 进程，返回 false 时直接返回 IPC_STUB_INVALID_DATA 错误码，不进入事务码分发。52 个事务码统一 SA-level 门控，无 per-method 权限区分。 | 无 per-method 权限表（ADR-1），后续若需方法级权限需扩展 OnRemoteRequest | AC-1.1 / AC-1.2 / AC-1.3 |
| R-2 | 行为 | OnRemoteRequest interface token 校验 | 验证 IPC 接口标识与 IUiContentService 定义匹配，不匹配时返回 IPC_STUB_INVALID_DATA 错误码，拒绝本次调用。 | interface token 校验在 IsSACalling 通过之后执行 | AC-1.4 |
| R-3 | 行为 | ConnectInner 首次调用（isConnected_=false） | 创建 UiReportProxy remote object 存入 reportObjectMap_，注册 event handler，标记 isConnected_=true。重复调用（isConnected_=true）时不重复创建。 | isConnected_ 为进程级标志，同一 pid 仅一次 Connect | AC-2.1 / AC-2.3 |
| R-4 | 行为 | SaveReportStub 存储 UiReportProxy | 按 pid 存入 reportObjectMap_，后续所有 Report* 方法通过该 proxy 广播上报至 SA 进程。 | reportObjectMap_ 为 map<int32_t, sptr<IRemoteObject>>，每 pid 一个 slot | AC-2.2 |
| R-5 | 行为 | ConnectInner 成功后 SendBaseInfo 调用 | 将当前 app 基础信息（页面名、窗口尺寸等）通过 UiReportProxy 推送至 SA 进程，确保 SA 在连接建立后立即获得初始状态。 | SendBaseInfo 仅在首次 Connect 后调用一次 | AC-2.4 |
| R-6 | 行为 | SA 进程死亡 OnRemoteDied ordered locks 阶段 | 获取 processMapMutex_、webFocusEventMutex_ 等锁，防止并发访问已失效数据。ordered locks 保证清理序列无并发干扰。 | 锁获取顺序必须固定，违反顺序可能导致死锁 | AC-3.1 / AC-3.2 |
| R-7 | 行为 | SA 进程死亡 OnRemoteDied state reset + manager calls 阶段 | EraseProcessId(key, pid) 移除进程映射 → reportObjectMap_ erase pid → fetch_sub 所有 9 个 atomic 计数器 → webFocusEventRegistered_ reset false → if pageTranslateOwnerPid_ matches: ResetTranslate() + ResetPageTransition()。 | ResetTranslate/ResetPageTransition 仅在 pageTranslateOwnerPid_ 匹配时调用 | AC-3.3 / AC-3.4 |
| R-8 | 异常 | SA 死亡清理违反 ordered locks → state reset → manager calls 顺序 | 可能导致悬空引用或并发访问已失效数据。规格要求严格遵循此顺序（ADR-6）。 | 不允许在 state reset 之前调 manager calls，不允许在 locks 释放后做 state reset | AC-3.5 |
| R-9 | 行为 | Report*Event 方法事件广播 | 遍历 reportObjectMap_ 中所有已注册 SA 进程的 UiReportProxy 逐一发送 IPC 上报，不做定向发送。广播模式保证所有 SA 工具同步收到事件（ADR-1）。 | reportObjectMap_ 为空时不发送 IPC，atomic 计数器仍正确维护 | AC-4.1 / AC-4.2 / AC-4.3 |

## 验证映射

| VM编号 | AC / 规则 | 验证手段 | 位置 / 用例名 |
|-------|----------|---------|---------------|
| VM-1 | AC-1.1 / AC-1.2 / R-1 | 集成测试 | mock SA caller vs mock 非 SA caller，验证 IsSACalling 门控 |
| VM-2 | AC-1.3 / R-1 | 代码评审 | ui_content_stub.cpp:45-265 52 事务码统一门控对照 |
| VM-3 | AC-1.4 / R-2 | 集成测试 | 发送错误 interface token，验证返回 IPC_STUB_INVALID_DATA |
| VM-4 | AC-2.1 / AC-2.3 / R-3 | 集成测试 | 首次 Connect vs 重复 Connect 行为对照 |
| VM-5 | AC-2.2 / R-4 | 集成测试 | Connect 后验证 reportObjectMap_ 存入 proxy |
| VM-6 | AC-2.4 / R-5 | 集成测试 | Connect 后验证 SendBaseInfo 推送 |
| VM-7 | AC-3.1..3.5 / R-6 / R-7 / R-8 | 集成测试 | 触发 OnRemoteDied，验证 ordered cleanup 全序列 |
| VM-8 | AC-4.1..4.3 / R-9 | 集成测试 | 2 SA proxy 注册，触发事件，验证均收到广播 |

## API 变更分析

### 新增 API

N/A，全部为 InnerApi（框架内部 IPC 接口）。无 Public/System API 变更。

### 变更/废弃 API

无。

## 接口规格

### 接口定义

**OnRemoteRequest**

| 属性 | 值 |
|------|-----|
| 函数签名 | `int32_t UiContentStub::OnRemoteRequest(uint32_t code, MessageParcel& data, MessageParcel& reply, MessageOption& option)` |
| 返回值 | `int32_t` — ERR_OK 或 IPC_STUB_INVALID_DATA |
| 开放范围 | InnerApi |
| 错误码 | IPC_STUB_INVALID_DATA（非 SA / token 不匹配） |
| 关联 AC | AC-1.1 / AC-1.2 / AC-1.4 |

**参数约束**

| 参数 | 类型 | 必填 | 默认值 | 约束条件 |
|------|------|------|--------|---------|
| code | uint32_t | 是 | N/A | 0-51（IUiContentService 事务码范围） |
| data | MessageParcel | 是 | N/A | 包含 interface token 和方法参数 |
| reply | MessageParcel | 是 | N/A | 写入返回数据 |
| option | MessageOption | 是 | N/A | IPC 同步/异步选项 |

**行为场景**

| # | 触发条件 | 预期行为 | 关联 AC |
|---|----------|----------|---------|
| 1 | SA 进程发送合法 IPC 请求 | IsSACalling() 返回 true → interface token 匹配 → 进入事务码分发 | AC-1.1 |
| 2 | 非 SA 进程发送 IPC 请求 | IsSACalling() 返回 false → 直接返回 IPC_STUB_INVALID_DATA | AC-1.2 |
| 3 | interface token 不匹配 | 返回 IPC_STUB_INVALID_DATA，不进入分发逻辑 | AC-1.4 |

**ConnectInner**

| 属性 | 值 |
|------|-----|
| 函数签名 | `int32_t UiSessionManagerOhos::ConnectInner(const std::string& key, int32_t pid, const sptr<IRemoteObject>& object)` |
| 返回值 | `int32_t` — ERR_OK 或错误码 |
| 开放范围 | InnerApi |
| 错误码 | N/A |
| 关联 AC | AC-2.1 / AC-2.2 / AC-2.3 |

**行为场景**

| # | 触发条件 | 预期行为 | 关联 AC |
|---|----------|----------|---------|
| 1 | 首次 Connect（isConnected_=false） | 创建 reportStub → 注册 handler → 标记 isConnected_=true → SendBaseInfo | AC-2.1 / AC-2.4 |
| 2 | 重复 Connect（isConnected_=true） | 不重复创建，保持现有连接状态 | AC-2.3 |

**OnRemoteDied (UiReportProxyRecipient / UIContentProxyRecipient)**

| 属性 | 值 |
|------|-----|
| 函数签名 | `void UiReportProxyRecipient::OnRemoteDied(const wptr<IRemoteObject>& remote)` |
| 返回值 | void |
| 开放范围 | InnerApi |
| 错误码 | N/A |
| 关联 AC | AC-3.1..3.5 |

**行为场景**

| # | 触发条件 | 预期行为 | 关联 AC |
|---|----------|----------|---------|
| 1 | SA 进程死亡通知 | ordered locks → state reset → manager calls | AC-3.1 |
| 2 | pageTranslateOwnerPid_ 匹配死亡进程 | ResetTranslate() + ResetPageTransition() | AC-3.4 |

## 兼容性声明

- **已有 API 行为变更:** 否 — 全部为已有实现补录
- **配置文件格式变更:** 否
- **数据存储格式变更:** 否
- **最低支持版本:** API 12
- **API 版本号策略:** 无 @since 标注（框架内部 IPC 能力）

## 架构约束

| 关键约束 | 约束说明 | 影响 AC |
|---------|----------|---------|
| SA-only 门控无 per-method 权限 | OnRemoteRequest 仅做 SA-level 门控（IsSACalling + interface token），不区分具体方法权限。后续若需方法级权限需扩展（ADR-1） | AC-1.3 |
| ordered cleanup 严格顺序 | SA 死亡清理必须遵循 locks → state reset → manager calls 顺序（ADR-6），违反顺序可能导致悬空引用 | AC-3.1 / AC-3.5 |
| 事件广播模式不可定向 | 所有 9 类事件上报均广播至 reportObjectMap_ 中所有已注册 SA 进程，不支持定向发送（ADR-1） | AC-4.1 |
| UiSessionManager Meyers singleton | UiSessionManagerOhos 为 Meyers singleton（static 局部变量），进程内唯一实例 | AC-2.1 |
| StubImpl 委托转发 | UIContentServiceStubImpl 所有方法委托转发至 UiSessionManager::GetInstance()，不持有业务状态 | AC-2.1 |
| IPC 八层调用链 | SA→Proxy→Stub→StubImpl→Hub→Pipeline→Node→Pattern 严格自上而下，不允许跨层（design.md OH-ARCH-LAYERING） | AC-1.1 |

## 非功能性需求

| 类型 | 指标/阈值 | 验证方式 | 证据 |
|------|----------|----------|------|
| 性能 | OnRemoteRequest 门控检查耗时 < 1ms（IsSACalling + token 校验均为系统调用） | hilog 耗时统计 | 代码评审 |
| 可观测 | SA 拒绝事件可通过 hilog 追踪 IsSACalling 返回 false | hilog 抓取 | 集成测试 |
| 可靠性 | SA 死亡清理 ordered sequence 保证无悬空引用 | 代码评审 | 代码审查 |
| 安全 | 非 SA 进程 IPC 调用被 OnRemoteRequest 入口拒绝，无 per-method 权限绕过风险 | 集成测试 | 代码审查 |
| 定界定位 | OnRemoteDied 清理顺序违反时可通过 hilog 异常日志定位 | hilog 抓取 | 代码审查 |

## 多设备适配声明

无差异。

## 全局特性影响

| 特性 | 适用？ | 结论 | 关联场景 |
|------|--------|------|----------|
| 无障碍 | 不适用 | 无影响 — 本 Feat 为框架内部 IPC 安全能力 | — |
| 大字体 | 不适用 | 无影响 — IPC 安全框架不涉及 UI 缩放 | — |
| 深色模式 | 不适用 | 无影响 — IPC 安全框架不涉及颜色主题 | — |
| 多窗口 | 适用 | 每窗口独立 UiSessionManager 连接，reportObjectMap_ 按 pid 管理 | 多 SA 进程连接 |
| 多用户 | 不适用 | 无影响 — IPC 连接不区分用户 | — |
| 版本升级 | 适用 | 无影响 — 无 Public/System API 契约 | — |
| 生态兼容 | 适用 | 新增 IPC 事务码需在 OnRemoteRequest 分发逻辑中注册 | IUiContentService 接口扩展 |

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
    query: "UiContentStub OnRemoteRequest 分发逻辑，IsSACalling + interface token 校验 (ui_content_stub.cpp:45-265)"
  - repo: "openharmony/ace_engine"
    query: "IUiContentService 52 IPC 事务码定义 (ui_content_service_interface.h)"
  - repo: "openharmony/ace_engine"
    query: "UIContentServiceStubImpl 委托转发至 UiSessionManager::GetInstance() (ui_content_stub_impl.h:26)"
  - repo: "openharmony/ace_engine"
    query: "UiSessionManagerOhos ConnectInner / SaveReportStub / SendBaseInfo (ui_session_manager_ohos.cpp:396-449)"
  - repo: "openharmony/ace_engine"
    query: "UiSessionManager Meyers singleton 实现 (ui_session_manager_ohos.cpp:245-249)"
  - repo: "openharmony/ace_engine"
    query: "UIContentProxyRecipient OnRemoteDied ordered cleanup (ui_content_proxy.cpp:134-162)"
  - repo: "openharmony/ace_engine"
    query: "UiReportProxyRecipient 死亡监听与 ordered locks (ui_content_proxy.cpp)"
  - repo: "openharmony/ace_engine"
    query: "reportObjectMap_ map<int32_t, sptr<IRemoteObject>> 进程映射 (ui_session_manager_ohos.h)"
  - repo: "openharmony/ace_engine"
    query: "processMap_ map<string, set<int32_t>> + processMapMutex_ shared_mutex (ui_session_manager.h:310-380)"
```

**关键文档：**
- [design.md](03-engine-framework/09-uisession/01-uisession-service/design.md)
