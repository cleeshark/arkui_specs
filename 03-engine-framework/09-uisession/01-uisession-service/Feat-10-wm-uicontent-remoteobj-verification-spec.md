# 特性规格

## 概述

| 属性 | 值 |
|------|-----|
| 特性名称 | WM UIContentRemoteObj 验证链路 |
| 特性编号 | Func-03-09-01-Feat-10 |
| 所属 Epic | UiSession |
| 优先级 | P2 |
| 目标版本 | API 12+ |
| SIG 归属 | ArkUI SIG |
| 状态 | Draft |
| 复杂度 | 标准 |

> 本 Feat 锁定 UISession SA 验证服务到应用进程的 WindowManager UIContentRemoteObj 获取链路：unified/sceneboard 路径下 WindowSessionImpl fallback 验证逻辑、separated WMS 路径下 WMS Stub/Proxy + Window Stub/Proxy + WindowAgent/WindowImpl GetUIContentRemoteObj IPC 链路、UiSaService 通过 WindowManager::GetUIContentRemoteObj 获取焦点窗口 IUiContentService 远端对象、真机验证步骤和通过判据。本规格为跨仓验证性规格，正式修复需由 window_manager 评估焦点窗口选择和安全边界后决定。不涉及 IPC 安全框架（Feat-01）、InspectorTree 查询（Feat-02）、事件上报（Feat-03）、命令下发（Feat-04）、翻译能力（Feat-05）、内容变化检测（Feat-06）、查询辅助 Dump（Feat-07）、SA 验证服务命令路由（Feat-08）、页面场景规则化感知（Feat-09）。

## 本次变更范围（Delta）

> 跨仓验证性规格补录，补录已有验证补丁和真机验证步骤的完整行为规格。

| 类型 | 内容 | 说明 |
|------|------|------|
| ADDED | unified/sceneboard WindowSessionImpl fallback 验证规格 | 当前窗口 remote object 为空时遍历 windowSessionMap_ 寻找非空 fallback 返回 |
| ADDED | separated WMS IPC 链路规格 | WindowManagerService → WindowRoot → WindowNode → IWindow → WindowAgent → WindowImpl → UIContent::GetRemoteObj 全链路 |
| ADDED | WMS IPC reply 格式规格 | reply 先写 errCode，成功时再写 remote object；客户端读取顺序保持一致 |
| ADDED | GetUIContentRemoteObj 权限校验规格 | WindowManagerService::GetUIContentRemoteObj 仅允许 IsSystemCalling |
| ADDED | WindowImpl GetUIContentRemoteObj 规格 | uiContent 非空时 GetRemoteObj() 返回 IUiContentService stub 实例，uiContent 为空时返回 WS_ERROR_NO_UI_CONTENT_ERROR |
| ADDED | 真机验证步骤与通过判据规格 | hidumper -s 16666 -a Connect 日志验证链路 |

## 输入文档

- 关联设计：`03-engine-framework/09-uisession/01-uisession-service/design.md`
- 关联需求：UISession 端到端验证（无独立 requirement.md）
- 源码定位（关键文件）：
  - `docs/architecture/UISession/WindowManager_UIContentRemoteObj_Verification_CN.md` — 验证补丁文档
  - `docs/architecture/UISession/window_manager_get_ui_content_remote_obj.patch` — 跨仓验证补丁
  - `interfaces/inner_api/ui_session/ui_session_sample/ui_sa_service.cpp:241` — UiSaService::Dump 获取焦点窗口 remote object
  - `interfaces/inner_api/ace/ui_content.h:518` — UIContent::GetRemoteObj 基类默认实现
  - `adapter/ohos/entrance/ui_content_impl.h:383` — UIContentImpl::GetRemoteObj 返回 IUiContentService stub 实例

## 用户故事

### US-1: unified/sceneboard 路径 WindowSessionImpl fallback

- As a 系统验证开发者
- I want 当焦点窗口 UIContent remote object 为空时，WindowSessionImpl 遍历同进程其他窗口寻找非空 remote object 作为 fallback
- So that ui_sa 可获取到至少一个承载 ArkUI 主内容窗口的 IUiContentService 远端对象

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-1.1 | WHEN 当前窗口 GetUIContentSharedPtr()->GetRemoteObj() 返回非空 THEN 直接返回该 remote object，不做 fallback。来源：验证补丁 WindowSessionImpl::GetUIContentRemoteObj | 正常 |
| AC-1.2 | WHEN 当前窗口 GetRemoteObj() 返回空 THEN 遍历 windowSessionMap_ 寻找其他窗口的 GetUIContentSharedPtr()->GetRemoteObj() 非空对象作为 fallback 返回。来源：验证补丁 WindowSessionImpl | 正常 |
| AC-1.3 | WHEN 遍历后所有窗口 remote object 均为空 THEN 返回 WS_ERROR_NO_UI_CONTENT_ERROR，日志输出 "uiContent remote is nullptr, no fallback found"。来源：验证补丁 WindowSessionImpl | 异常 |

### US-2: separated WMS IPC 链路

- As a 系统验证开发者
- I want separated WMS 架构下 ui_sa 通过 WMS IPC 到应用进程 WindowAgent/WindowImpl 获取 UIContentRemoteObj
- So that separated WMS 架构下 ui_sa 也能获取应用进程暴露的 IUiContentService 远端对象

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-2.1 | WHEN ui_sa 调用 WindowManager::GetUIContentRemoteObj(persistentId) THEN WMS IPC 链路：WindowManagerService → WindowRoot::GetWindowNode → WindowNode::GetWindowToken → IWindow::GetUIContentRemoteObj → WindowAgent → WindowImpl → UIContent::GetRemoteObj。来源：验证补丁 WMS 链路 | 正常 |
| AC-2.2 | WHEN WindowManagerService::GetUIContentRemoteObj THEN 仅允许 IsSystemCalling 权限校验，非 System 调用返回 WS_ERROR_INVALID_PERMISSION。来源：验证补丁 WindowManagerService | 异常 |
| AC-2.3 | WHEN WMS IPC reply THEN 先写 errCode (int32_t)，成功(errCode=WS_OK)时再写 remote object；客户端先读 errCode 再读 remote object。来源：验证补丁 Stub/Proxy | 正常 |
| AC-2.4 | WHEN WindowImpl::GetUIContentRemoteObj THEN uiContent 非空时返回 uiContent->GetRemoteObj()，uiContent 为空时返回 WS_ERROR_NO_UI_CONTENT_ERROR。来源：验证补丁 WindowImpl | 正常 |

### US-3: ui_sa 真机验证链路

- As a 系统验证开发者
- I want ui_sa 通过 hidumper -s 16666 -a Connect 验证端到端 IPC 链路连通性
- So that 验证人员可确认 WM → app 进程 UISession IPC 链路正常

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-3.1 | WHEN hidumper -s 16666 -a "Connect" THEN ui_sa 获取焦点窗口 remote object 并建立 IUiContentService 连接。来源：`ui_sa_service.cpp:241` | 正常 |
| AC-3.2 | WHEN Connect 成功 THEN hilog 出现 "through uiSa, connect success, foucs window info = bundleName:..."。来源：真机验证记录 | 正常 |
| AC-3.3 | WHEN GetUIContentRemoteObj 返回 ret=0 但 remote object 为空 THEN hilog 出现 "through uiSa, tempRemoteObj is null"，说明 WM IPC 成功但 app 侧 UIContent::GetRemoteObj() 返回空。来源：KB 调试指南 | 异常 |

## 验收追溯

| AC | 关联规则 | 关联 Task | 验证方式 | 证据 |
|----|----------|----------|----------|------|
| AC-1.1 | R-1 | TASK-10 | 集成测试：当前窗口 remote 非空 | 真机验证 |
| AC-1.2 | R-2 | TASK-10 | 集成测试：当前窗口 remote 空 + fallback | 真机验证 |
| AC-1.3 | R-2 | TASK-10 | 集成测试：全部窗口 remote 空 | 真机验证 |
| AC-2.1 | R-3 | TASK-10 | 集成测试：separated WMS 链路 | 真机验证 |
| AC-2.2 | R-4 | TASK-10 | 集成测试：非 System 调用 | 真机验证 |
| AC-2.3 | R-5 | TASK-10 | 代码评审：reply 格式 | 代码审查 |
| AC-2.4 | R-6 | TASK-10 | 集成测试：WindowImpl GetRemoteObj | 真机验证 |
| AC-3.1 | R-7 | TASK-10 | 真机验证：Connect 成功 | 2026-06-30 实测 |
| AC-3.2 | R-7 | TASK-10 | 真机验证：hilog 确认 | 2026-06-30 实测 |
| AC-3.3 | R-8 | TASK-10 | 真机验证：tempRemoteObj null | 2026-06-30 实测 |

## 规则定义

| 规则ID | 类型 | 触发条件 | 预期行为 | 边界/约束 | 关联AC |
|--------|------|----------|----------|-----------|--------|
| R-1 | 行为 | unified/sceneboard 当前窗口 remote 非空 | 直接返回当前窗口 UIContent::GetRemoteObj()，不做 fallback。 | 当前窗口为焦点窗口 | AC-1.1 |
| R-2 | 行为 | unified/sceneboard 当前窗口 remote 空 | 遍历 windowSessionMap_ 寻找非空 fallback。全部为空时返回 WS_ERROR_NO_UI_CONTENT_ERROR。 | fallback 为验证性逻辑，是否作为正式修复需由 WM 评估 | AC-1.2 / AC-1.3 |
| R-3 | 行为 | separated WMS GetUIContentRemoteObj IPC 链路 | WMS → WindowRoot → WindowNode → IWindow → WindowAgent → WindowImpl → UIContent::GetRemoteObj。 | separated WMS 需补 WMS IPC 和 WMS 到应用进程窗口对象回调 | AC-2.1 |
| R-4 | 行为 | GetUIContentRemoteObj 权限校验 | WindowManagerService 仅允许 IsSystemCalling，非 System 调用返回 WS_ERROR_INVALID_PERMISSION。 | 与 UiContentStub IsSACalling 门控逻辑类似 | AC-2.2 |
| R-5 | 行为 | WMS IPC reply 格式 | 先写 errCode (int32_t)，成功时再写 remote object。客户端读取顺序保持一致。 | reply 格式变更需同步更新 Stub 和 Proxy | AC-2.3 |
| R-6 | 行为 | WindowImpl GetUIContentRemoteObj | uiContent 非空：GetUIContentSharedPtr()->GetRemoteObj() 返回 IUiContentService stub 实例。uiContent 为空：返回 WS_ERROR_NO_UI_CONTENT_ERROR。 | Ace::UIContent 基类默认实现可能返回空 | AC-2.4 |
| R-7 | 行为 | ui_sa Connect 真机验证 | hidumper -s 16666 -a Connect 成功时 hilog 出现 "connect success" 和 bundleName/moduleName/abilityName。 | 验证前需保证目标应用窗口处于焦点 | AC-3.1 / AC-3.2 |
| R-8 | 异常 | ui_sa Connect remote object 为空 | GetUIContentRemoteObj 返回 ret=0 但 remote object 为空，hilog 出现 "tempRemoteObj is null"。 | 问题不在 ui_sa 注册通路而在 WM 返回 UIContent remote 的窗口选择或兜底策略 | AC-3.3 |

## 验证映射

| 编号 | 对应规格项 | 验证方式 | 验证重点 |
|------|-----------|---------|---------|
| VM-1 | AC-1.1..1.3 / R-1 / R-2 | 真机验证 | unified/sceneboard fallback 验证 |
| VM-2 | AC-2.1..2.4 / R-3 / R-4 / R-5 / R-6 | 真机验证 | separated WMS IPC 链路 + reply 格式 |
| VM-3 | AC-3.1..3.3 / R-7 / R-8 | 真机验证 | ui_sa Connect 端到端验证 |

## API 变更分析

### 新增 API

| API 签名 | 类型 | Kit | 说明 | 权限要求 |
|----------|------|-----|------|----------|
| WindowImpl::GetUIContentRemoteObj | InnerApi (WM) | ArkUI | 获取 UIContent remote object | N/A |
| WindowManagerService::GetUIContentRemoteObj | InnerApi (WM) | ArkUI | WMS 获取指定窗口 UIContent remote | IsSystemCalling |

> 注：以上 API 属于 window_manager 仓，本规格仅为跨仓验证性规格记录。

### 变更/废弃 API

无。

## 接口规格

### 接口定义

**WindowManagerService::GetUIContentRemoteObj**

| 属性 | 值 |
|------|-----|
| 函数签名 | `WSError WindowManagerService::GetUIContentRemoteObj(int32_t persistentId, sptr<IRemoteObject>& uiContentRemoteObj)` |
| 返回值 | `WSError` — WS_OK / WS_ERROR_INVALID_PERMISSION / WS_ERROR_NULLPTR / WS_ERROR_INVALID_WINDOW / WS_ERROR_NO_UI_CONTENT_ERROR |
| 开放范围 | InnerApi (WM) |
| 错误码 | WS_ERROR_INVALID_PERMISSION / WS_ERROR_NULLPTR / WS_ERROR_INVALID_WINDOW / WS_ERROR_NO_UI_CONTENT_ERROR |
| 关联 AC | AC-2.1 / AC-2.2 |

**参数约束**

| 参数 | 类型 | 必填 | 默认值 | 约束条件 |
|------|------|------|--------|---------|
| persistentId | int32_t | 是 | N/A | 目标窗口 persistentId |
| uiContentRemoteObj | sptr<IRemoteObject>& | 是 | N/A | 出参，UIContent remote object |

**行为场景**

| # | 触发条件 | 预期行为 | 关联 AC |
|---|----------|----------|---------|
| 1 | IsSystemCalling 权限通过 | 按链路获取 UIContent remote object | AC-2.1 |
| 2 | 非 System 调用 | 返回 WS_ERROR_INVALID_PERMISSION | AC-2.2 |
| 3 | window node / token 为空 | 返回 WS_ERROR_NULLPTR / WS_ERROR_INVALID_WINDOW | AC-2.1 |

**WindowImpl::GetUIContentRemoteObj**

| 属性 | 值 |
|------|-----|
| 函数签名 | `WSError WindowImpl::GetUIContentRemoteObj(sptr<IRemoteObject>& uiContentRemoteObj)` |
| 返回值 | `WSError` — WS_OK / WS_ERROR_NO_UI_CONTENT_ERROR |
| 开放范围 | InnerApi (WM) |
| 关联 AC | AC-2.4 |

**行为场景**

| # | 触发条件 | 预期行为 | 关联 AC |
|---|----------|----------|---------|
| 1 | uiContent 非空 | 返回 uiContent->GetRemoteObj() | AC-2.4 |
| 2 | uiContent 为空 | 返回 WS_ERROR_NO_UI_CONTENT_ERROR | AC-2.4 |

## 兼容性声明

- **已有 API 行为变更:** 否 — 验证性补丁，正式修复需 WM 评估
- **配置文件格式变更:** 否
- **数据存储格式变更:** 否
- **最低支持版本:** API 12
- **API 版本号策略:** 无 @since 标注（框架内部 IPC 能力）

## 架构约束

| 关键约束 | 约束说明 | 影响 AC |
|---------|----------|---------|
| 跨仓验证性规格 | 本规格涉及 window_manager 仓变更，正式修复需由 WM 评估焦点窗口选择和安全边界后决定（ADR-9） | AC-1.2 / AC-2.1 |
| WMS IPC reply 格式一致性 | Stub/Proxy 先写 errCode 再写 remote object，客户端读取顺序必须一致 | AC-2.3 |
| unified vs separated 双架构 | unified/sceneboard 使用 WindowSessionImpl fallback，separated WMS 使用独立 WMS IPC 链路 | AC-1.1 / AC-2.1 |
| GetRemoteObj 基类默认返回空 | Ace::UIContent 基类默认实现 GetRemoteObj() 可能返回空，UIContentImpl::GetRemoteObj() 返回 IUiContentService stub 实例 | AC-2.4 |

## 非功能性需求

| 类型 | 指标/阈值 | 验证方式 | 证据 |
|------|----------|----------|------|
| 性能 | GetUIContentRemoteObj IPC 为同步调用，耗时 < 100ms | 真机验证 | 2026-06-30 实测 |
| 可观测 | hilog 输出固定 tag（GetUIContentRemoteObj from app / WindowAgent GetUIContentRemoteObj / get uiContent remote success / tempRemoteObj is null） | hilog 抓取 | 真机验证 |
| 安全 | IsSystemCalling 权限校验防止非 System 进程获取 UIContent remote object | 代码评审 | 代码审查 |

## 多设备适配声明

| 架构 | 说明 |
|------|------|
| unified/sceneboard | WindowSessionImpl fallback 验证逻辑 |
| separated WMS | 独立 WMS IPC 链路 |

## 全局特性影响

| 特性 | 适用？ | 结论 | 关联场景 |
|------|--------|------|----------|
| 无障碍 | 不适用 | 无影响 — WM 验证链路为框架内部 IPC 能力 | — |
| 多窗口 | 适用 | 焦点窗口选择影响 GetUIContentRemoteObj 返回结果 | 焦点窗口 / 子窗口 |
| 版本升级 | 适用 | 无影响 — 无 Public/System API 契约变更 | — |

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
    query: "UiSaService::Dump 获取焦点窗口 remote object (ui_sa_service.cpp:241)"
  - repo: "openharmony/ace_engine"
    query: "UIContent::GetRemoteObj 基类默认实现 (ui_content.h:518)"
  - repo: "openharmony/ace_engine"
    query: "UIContentImpl::GetRemoteObj 返回 IUiContentService stub 实例 (ui_content_impl.h:383)"
  - repo: "openharmony/window_manager"
    query: "WindowSessionImpl fallback 验证逻辑 (window_session_impl.cpp)"
  - repo: "openharmony/window_manager"
    query: "WindowManagerService::GetUIContentRemoteObj + IsSystemCalling (window_manager_service.cpp)"
  - repo: "openharmony/window_manager"
    query: "WindowImpl::GetUIContentRemoteObj (window_impl.cpp)"
  - repo: "openharmony/window_manager"
    query: "WindowAgent::GetUIContentRemoteObj (window_agent.cpp)"
  - repo: "openharmony/window_manager"
    query: "WindowManagerStub/Proxy GetUIContentRemoteObj IPC (window_manager_stub.cpp / window_manager_proxy.cpp)"
  - repo: "openharmony/window_manager"
    query: "WindowStub/Proxy GetUIContentRemoteObj IPC (window_stub.cpp / window_proxy.cpp)"
```

**关键文档：**
- [design.md](03-engine-framework/09-uisession/01-uisession-service/design.md)
- [WM 验证补丁文档](docs/architecture/UISession/WindowManager_UIContentRemoteObj_Verification_CN.md)
