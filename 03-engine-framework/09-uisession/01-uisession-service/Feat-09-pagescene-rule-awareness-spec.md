# 特性规格

## 概述

| 属性 | 值 |
|------|-----|
| 特性名称 | 页面场景规则化感知能力 |
| 特性编号 | Func-03-09-01-Feat-09 |
| 所属 Epic | UiSession |
| 优先级 | P2 |
| 目标版本 | API 13+ |
| SIG 归属 | ArkUI SIG |
| 状态 | Draft |
| 复杂度 | 标准 |

> 本 Feat 锁定 UISession 页面场景规则化感知能力：SA 通过 ruleJson 下发页面场景规则、ArkUI 侧按规则检测匹配场景并上报命中/退出事件。首批场景 TEXT_EDITOR（≥2 文本输入类控件上报）、COUNT_GTE 规则运算符、PageSceneRuleInfo / PageSceneRuleSetInfo 数据结构、SavePageSceneDetectFunction 回调注册、RegisterPageSceneRules / UnregisterPageSceneRules atomic 计数器门控、ContentChangeManager::OnVsyncEnd FlushPageSceneNodeChanged 收敛、TEXT_EDITOR_EXIT 退出上报、Web/UIExtension 规则透传预留、与 ContentChange 共用页面级稳定上报点。不涉及 IPC 安全框架（Feat-01）、InspectorTree 查询（Feat-02）、事件上报门控（Feat-03）、命令下发（Feat-04）、翻译能力（Feat-05）、内容变化检测阈值（Feat-06）、查询辅助 Dump（Feat-07）、SA 验证服务（Feat-08）。

## 本次变更范围（Delta）

> 页面场景规则化感知特性分支规格，当前主线可能尚未包含全部实现，核对代码时以特性分支源码为准。

| 类型 | 内容 | 说明 |
|------|------|------|
| ADDED | TEXT_EDITOR 首批场景规则规格 | 当前页面或子内容源中存在 ≥2 文本输入类控件时上报命中事件 |
| ADDED | COUNT_GTE 规则运算符规格 | 规则条件操作符 COUNT Greater Than or Equal，命中节点数量 ≥ 阈值时匹配 |
| ADDED | ruleJson / webRules 预留规格 | ruleJson 由 SA 下发，webRules 为 Web 专用预留字段，宿主原样透传给 Web 控件 |
| ADDED | 上报结果结构规格 | currentPageName + source.type + nodes[].rect/focusable/text(includeText=true) |
| ADDED | TEXT_EDITOR_EXIT 退出上报规格 | 同一规则已上报过命中事件后不再满足规则时上报 TEXT_EDITOR_EXIT（matched=false） |
| ADDED | ContentChangeManager 收敛规格 | OnVsyncEnd FlushPageSceneNodeChanged 收敛检测，滚动/过渡/转场未稳定时延后 |
| ADDED | 与 ContentChange 共用稳定上报点规格 | 页面切换/滚动结束/Swiper切换/弹窗显示隐藏为共用稳定点 |
| ADDED | RegisterPageSceneRules atomic 计数器门控规格 | pageSceneRuleRegisterProcesses_ atomic<int32_t> 门控 |
| ADDED | SavePageSceneDetectFunction 回调注册规格 | UIContentImpl 注册 PageScene 检测回调至 UiSessionManager |

## 输入文档

- 关联设计：`03-engine-framework/09-uisession/01-uisession-service/design.md`
- 关联需求：页面场景规则化感知特性分支 SDD 设计 `.codespec/changes/ui-session-page-scene-awareness/`
- 源码定位（关键文件）：
  - `interfaces/inner_api/ui_session/ui_session_manager.h:277` — pageSceneRuleRegisterProcesses_ atomic 计数器
  - `adapter/ohos/entrance/ui_session/ui_session_manager_ohos.h:181-197` — PageSceneRuleInfo / PageSceneRuleSetInfo 数据结构
  - `adapter/ohos/entrance/ui_session/ui_session_manager_ohos.h:150` — SavePageSceneDetectFunction / RegisterPageSceneRules / UnregisterPageSceneRules
  - `frameworks/core/components_ng/manager/content_change_manager/content_change_manager.cpp` — FlushPageSceneNodeChanged / OnVsyncEnd 收敛
  - `adapter/ohos/entrance/ui_content_impl.cpp:6817` — SetStartContentChangeDetectCallback 投递到 UI 线程

## 用户故事

### US-1: TEXT_EDITOR 场景规则检测

- As a SA 工具开发者
- I want SA 下发 TEXT_EDITOR 规则后，ArkUI 侧检测当前页面是否存在 ≥2 文本输入类控件，命中时上报 TEXT_EDITOR 事件
- So that SA 工具可感知页面编辑场景，自动触发辅助能力（如翻译、输入增强）

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-1.1 | WHEN RegisterPageSceneRules 下发 TEXT_EDITOR 规则（ruleJson 包含 condition: COUNT_GTE, threshold: 2, nodeType: TEXT_INPUT） THEN ArkUI 侧接受规则并在页面稳定点检测匹配。来源：KB 扩展指南设计边界 3 | 正常 |
| AC-1.2 | WHEN 当前页面存在 ≥2 文本输入类控件（TextInput / TextArea / Search / RichEditor） THEN 上报 TEXT_EDITOR 命中事件，包含 currentPageName、source.type=ARKUI、nodes[].rect 和 focusable。来源：KB 扩展指南设计边界 5 | 正常 |
| AC-1.3 | WHEN 当前页面仅存在 0 或 1 个文本输入类控件 THEN 不上报 TEXT_EDITOR 命中事件。来源：KB 扩展指南设计边界 3 | 边界 |
| AC-1.4 | WHEN includeText=true 在 ruleJson 中指定 THEN nodes[] 携带 text 字段，值为用户已输入文本，输入为空时为 placeholder。来源：KB 扩展指南设计边界 5 | 正常 |

### US-2: TEXT_EDITOR_EXIT 退出上报

- As a SA 工具开发者
- I want 同一 TEXT_EDITOR 规则已上报命中后，页面不再满足规则时上报 TEXT_EDITOR_EXIT 退出事件
- So that SA 工具可正确维护场景状态，不再触发不需要的辅助能力

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-2.1 | WHEN 同一 TEXT_EDITOR 规则已上报过命中事件且后续页面稳定点检测发现不再满足规则 THEN 上报 TEXT_EDITOR_EXIT 事件，sceneType=TEXT_EDITOR、matched=false、matchedCount=当前参与统计的输入控件数量。来源：KB 扩展指南设计边界 8 | 正常 |
| AC-2.2 | WHEN 退出事件上报后 THEN 清理命中态，后续连续未命中不重复上报退出事件。来源：KB 扩展指南设计边界 8 | 恢复 |
| AC-2.3 | WHEN 主动 GetPageScene 未命中结果 THEN 使用 eventName=TEXT_EDITOR 而非 TEXT_EDITOR_EXIT。来源：KB 扩展指南设计边界 8 | 边界 |

### US-3: 页面场景规则化感知检测收敛至页面稳定点

- As a 框架稳定性维护者
- I want 页面场景规则化感知检测统一收敛到页面稳定点（OnVsyncEnd FlushPageSceneNodeChanged），滚动/过渡/转场未稳定时延后检测
- So that 页面场景规则化感知检测不影响帧率和渲染性能，且仅在页面内容真正稳定后触发

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-3.1 | WHEN ArkUI 侧输入类节点上下树变化 THEN 先记为待检测规则，真正检测统一收敛到 ContentChangeManager::OnVsyncEnd 调用 FlushPageSceneNodeChanged。来源：KB 扩展指南设计边界 7 | 正常 |
| AC-3.2 | WHEN 滚动、Swiper 滚动或页面转场未稳定 THEN FlushPageSceneNodeChanged 延后执行，直到页面稳定点触发。来源：KB 扩展指南设计边界 7 | 正常 |
| AC-3.3 | WHEN Pipeline 只调用 ContentChangeManager::OnVsyncEnd THEN 不直接依赖页面场景规则化感知规则判断。来源：KB 扩展指南设计边界 7 | 正常 |

### US-4: 页面场景规则化感知与 ContentChange 共用稳定上报点

- As a 框架设计维护者
- I want 页面场景规则化感知复用 ContentChange 的页面级稳定上报点：页面切换结束、滚动结束、Swiper/Tabs 切换结束、弹窗显示隐藏结束
- So that 即使只注册页面场景规则化感知未注册 ContentChange，这些稳定点也会触发待检测规则

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-4.1 | WHEN 只注册页面场景规则化感知未注册 ContentChange THEN 页面切换/滚动结束/Swiper切换/弹窗显示隐藏等稳定点仍触发待检测规则。来源：KB 扩展指南设计边界 9 | 正常 |
| AC-4.2 | WHEN Text/Image 具体控件 ContentChange 事件 THEN 仅在 ContentChange 注册后生效，不作为页面场景规则化感知-only 的检测入口。来源：KB 扩展指南设计边界 9 | 边界 |

### US-5: RegisterPageSceneRules 门控与回调注册

- As a SA 工具开发者
- I want RegisterPageSceneRules 通过 atomic 计数器门控注册，SavePageSceneDetectFunction 注册 UI 线程回调
- So that 多个 SA 进程可同时注册页面场景规则化感知规则，且检测回调在 UI 线程执行避免跨线程直接访问 Pipeline

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-5.1 | WHEN RegisterPageSceneRules 被调用 THEN pageSceneRuleRegisterProcesses_ atomic fetch_add(1)，计数器 > 0 表示需要检测。来源：`ui_session_manager.h:277` | 正常 |
| AC-5.2 | WHEN UnregisterPageSceneRules 被调用 THEN pageSceneRuleRegisterProcesses_ atomic fetch_sub(1)，计数器归零后停止检测。来源：`ui_session_manager.h:277` | 正常 |
| AC-5.3 | WHEN SavePageSceneDetectFunction 注册回调 THEN UIContentImpl 通过 TaskExecutor 投递到 UI 线程，检测回调在 UI 线程执行。来源：`ui_content_impl.cpp:6817` | 正常 |

### US-6: ruleJson 规则下发与 Web/UIExtension 透传预留

- As a SA 工具开发者
- I want 规则由 SA 通过 ruleJson 下发，ruleJson.webRules 为 Web 专用预留字段
- So that SA 可灵活下发不同场景规则，Web 控件接收宿主透传的规则生命周期请求

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-6.1 | WHEN SA 下发 ruleJson THEN 首版条件操作符 COUNT_GTE 表示命中节点数量 ≥ 阈值。来源：KB 扩展指南设计边界 4 | 正常 |
| AC-6.2 | WHEN ruleJson 包含 webRules THEN 为 Web 专用预留字段，宿主原样透传给 Web 控件，具体规格不在当前特性中设计。来源：KB 扩展指南设计边界 4 | 边界 |
| AC-6.3 | WHEN UIExtension 接收宿主透传 THEN 仅作为子来源接收规则生命周期请求，不设计内部匹配、命中回传和 source.type=UI_EXTENSION 上报。来源：KB 扩展指南设计边界 6 | 边界 |

## 验收追溯

| AC | 关联规则 | 关联 Task | 验证方式 | 证据 |
|----|----------|----------|----------|------|
| AC-1.1 | R-1 | TASK-09 | 集成测试：下发 TEXT_EDITOR 规则 | 代码审查 |
| AC-1.2 | R-2 | TASK-09 | 集成测试：≥2 输入控件页面 | 代码审查 |
| AC-1.3 | R-2 | TASK-09 | 集成测试：0-1 输入控件页面 | 代码审查 |
| AC-1.4 | R-3 | TASK-09 | 集成测试：includeText=true | 代码审查 |
| AC-2.1 | R-4 | TASK-09 | 集成测试：命中→退出 | 代码审查 |
| AC-2.2 | R-4 | TASK-09 | 集成测试：退出后不重复上报 | 代码审查 |
| AC-2.3 | R-4 | TASK-09 | 集成测试：主动 GetPageScene | 代码审查 |
| AC-3.1 | R-5 | TASK-09 | 代码评审：OnVsyncEnd 收敛 | 代码审查 |
| AC-3.2 | R-5 | TASK-09 | 集成测试：滚动中延后 | 代码审查 |
| AC-3.3 | R-5 | TASK-09 | 代码评审 | 代码审查 |
| AC-4.1 | R-6 | TASK-09 | 集成测试：仅页面场景规则化感知注册 | 代码审查 |
| AC-4.2 | R-6 | TASK-09 | 代码评审 | 代码审查 |
| AC-5.1 | R-7 | TASK-09 | 单元测试：atomic fetch_add | 代码审查 |
| AC-5.2 | R-7 | TASK-09 | 单元测试：atomic fetch_sub | 代码审查 |
| AC-5.3 | R-8 | TASK-09 | 代码评审 | 代码审查 |
| AC-6.1 | R-9 | TASK-09 | 集成测试 | 代码审查 |
| AC-6.2 | R-9 | TASK-09 | 代码评审（预留） | 代码审查 |
| AC-6.3 | R-10 | TASK-09 | 代码评审（预留） | 代码审查 |

## 规则定义

| 规则ID | 类型 | 触发条件 | 预期行为 | 边界/约束 | 关联AC |
|--------|------|----------|----------|-----------|--------|
| R-1 | 行为 | RegisterPageSceneRules 下发 TEXT_EDITOR 规则 | ArkUI 侧接受 ruleJson 并在页面稳定点检测匹配。ruleJson 包含 condition: COUNT_GTE, threshold: 2, nodeType: TEXT_INPUT。 | 仅首版 COUNT_GTE 操作符，后续版本可能扩展其他操作符 | AC-1.1 |
| R-2 | 行为 | TEXT_EDITOR 规则检测 | ≥2 文本输入类控件命中上报 TEXT_EDITOR 事件，0-1 个控件不上报。文本输入类控件包括 TextInput / TextArea / Search / RichEditor。 | 默认不包含输入文本正文，includeText=true 时携带 text | AC-1.2 / AC-1.3 |
| R-3 | 行为 | 上报结果结构 | currentPageName + source.type + nodes[].rect/focusable + (includeText=true: nodes[].text)。text 值优先为用户已输入文本，输入为空时为 placeholder。 | 不设计完整控件树上报，不提供完整树上报开关 | AC-1.4 |
| R-4 | 行为 | TEXT_EDITOR_EXIT 退出上报 | 同一规则已上报命中后不再满足规则时上报 TEXT_EDITOR_EXIT（matched=false, matchedCount=当前输入控件数）。退出上报后清理命中态，连续未命中不重复上报。 | 主动 GetPageScene 未命中使用 eventName=TEXT_EDITOR 而非 TEXT_EDITOR_EXIT | AC-2.1 / AC-2.2 / AC-2.3 |
| R-5 | 行为 | 页面场景规则化感知检测收敛至页面稳定点 | 输入类节点上下树变化先记为待检测规则，真正检测统一收敛到 ContentChangeManager::OnVsyncEnd FlushPageSceneNodeChanged。滚动/过渡/转场未稳定时延后。 | Pipeline 只调用 OnVsyncEnd，不直接依赖页面场景规则化感知规则判断 | AC-3.1 / AC-3.2 / AC-3.3 |
| R-6 | 行为 | 页面场景规则化感知复用 ContentChange 稳定上报点 | 页面切换结束/滚动结束/Swiper切换结束/弹窗显示隐藏结束为共用稳定点。仅注册页面场景规则化感知未注册 ContentChange 时这些稳定点仍触发检测。 | Text/Image 具体控件 ContentChange 事件仅在 ContentChange 注册后生效 | AC-4.1 / AC-4.2 |
| R-7 | 行为 | RegisterPageSceneRules atomic 门控 | pageSceneRuleRegisterProcesses_ atomic fetch_add/fetch_sub，> 0 时检测，归零后停止。与 9 类事件 atomic 计数器门控模式一致。 | 门控方式与 ContentChange / ComponentChange 注册计数模式一致 | AC-5.1 / AC-5.2 |
| R-8 | 行为 | SavePageSceneDetectFunction UI 线程回调 | UIContentImpl 通过 TaskExecutor 投递到 UI 线程注册回调，检测回调在 UI 线程执行。 | 与 InspectorTree/翻译回调的 UI 线程投递模式一致 | AC-5.3 |
| R-9 | 行为 | ruleJson 规则下发 | SA 通过 ruleJson 下发规则，首版操作符 COUNT_GTE。ruleJson.webRules 为 Web 专用预留字段，宿主原样透传给 Web 控件。 | Web 规则具体规格不在当前特性中设计 | AC-6.1 / AC-6.2 |
| R-10 | 边界 | UIExtension 规则透传 | UIExtension 仅作为子来源接收宿主透传的规则生命周期请求。不设计内部匹配、命中回传和 source.type=UI_EXTENSION 上报。 | 当前特性不验证 UIExtension 子来源 | AC-6.3 |

## 验证映射

| 编号 | 对应规格项 | 验证方式 | 验证重点 |
|------|-----------|---------|---------|
| VM-1 | AC-1.1..1.4 / R-1 / R-2 / R-3 | 集成测试 | TEXT_EDITOR 规则下发、命中检测、上报结果结构 |
| VM-2 | AC-2.1..2.3 / R-4 | 集成测试 | TEXT_EDITOR_EXIT 退出上报、命中态清理 |
| VM-3 | AC-3.1..3.3 / R-5 | 代码评审 | OnVsyncEnd FlushPageSceneNodeChanged 收敛 |
| VM-4 | AC-4.1 / AC-4.2 / R-6 | 集成测试 | 仅页面场景规则化感知注册时稳定点仍触发 |
| VM-5 | AC-5.1..5.3 / R-7 / R-8 | 单元测试 + 代码评审 | atomic 门控 + UI 线程回调注册 |
| VM-6 | AC-6.1..6.3 / R-9 / R-10 | 代码评审 | ruleJson 下发 + Web/UIExtension 预留 |

## API 变更分析

### 新增 API

N/A，全部为 InnerApi（框架内部 IPC 接口）。无 Public/System API 变更。

### 变更/废弃 API

无。

## 接口规格

### 接口定义

**RegisterPageSceneRules**

| 属性 | 值 |
|------|-----|
| 函数签名 | `int32_t IUiContentService::RegisterPageSceneRules(int32_t id, const std::string& ruleJson)` |
| 返回值 | `int32_t` — ERR_OK 或错误码 |
| 开放范围 | InnerApi |
| 错误码 | PARAM_INVALID（ruleJson 格式非法） |
| 关联 AC | AC-1.1 / AC-5.1 |

**参数约束**

| 参数 | 类型 | 必填 | 默认值 | 约束条件 |
|------|------|------|--------|---------|
| id | int32_t | 是 | N/A | SA 请求标识 |
| ruleJson | std::string | 是 | N/A | JSON 格式规则描述，首版支持 COUNT_GTE 操作符 |

**行为场景**

| # | 触发条件 | 预期行为 | 关联 AC |
|---|----------|----------|---------|
| 1 | 合法 TEXT_EDITOR ruleJson | atomic fetch_add(1) + 接受规则 + 页面稳定点检测 | AC-1.1 / AC-5.1 |
| 2 | 非法 ruleJson 格式 | 返回 PARAM_INVALID | AC-1.1 |

**UnregisterPageSceneRules**

| 属性 | 值 |
|------|-----|
| 函数签名 | `int32_t IUiContentService::UnregisterPageSceneRules(int32_t id)` |
| 返回值 | `int32_t` — ERR_OK |
| 开放范围 | InnerApi |
| 关联 AC | AC-5.2 |

**GetPageScene**

| 属性 | 值 |
|------|-----|
| 函数签名 | `int32_t IUiContentService::GetPageScene(int32_t id, const std::string& ruleJson)` |
| 返回值 | `int32_t` — ERR_OK 或 PARAM_INVALID |
| 开放范围 | InnerApi |
| 关联 AC | AC-2.3 |

## 兼容性声明

- **已有 API 行为变更:** 否 — 页面场景规则化感知为新增能力
- **配置文件格式变更:** 否
- **数据存储格式变更:** 否
- **最低支持版本:** API 13
- **API 版本号策略:** 无 @since 标注（框架内部 IPC 能力）

## 架构约束

| 关键约束 | 约束说明 | 影响 AC |
|---------|----------|---------|
| 页面场景规则化感知独立于 ContentChange/ComponentChange | 能力仅匹配时机上参考 ContentChange 模式，不设计/实现 ContentChange 内部检测入口作为页面场景规则化感知-only 入口（ADR-8） | AC-4.1 / AC-4.2 |
| 检测收敛到 OnVsyncEnd | 输入类节点上下树先记为待检测，OnVsyncEnd FlushPageSceneNodeChanged 统一执行 | AC-3.1 / AC-3.2 |
| 不设计完整控件树上报 | 上报结果仅包含命中节点摘要，不提供完整树上报开关 | AC-1.4 |
| Web/UIExtension 仅预留 | 当前特性不设计/不实现/不验证子来源内部匹配和命中回传 | AC-6.2 / AC-6.3 |

## 非功能性需求

| 类型 | 指标/阈值 | 验证方式 | 证据 |
|------|----------|----------|------|
| 性能 | 页面场景规则化感知检测在 OnVsyncEnd 收敛，不额外增加帧调度开销 | 代码评审 | 代码审查 |
| 可观测 | TEXT_EDITOR 命中/退出事件可通过 ReportService IPC 追踪 | 集成测试 | 代码审查 |
| 可靠性 | TEXT_EDITOR_EXIT 上报后清理命中态，避免重复退出上报 | 集成测试 | 代码审查 |
| 安全 | 页面场景规则化感知规则仅通过 SA IPC 下发，非 SA 进程无法注册规则 | 代码评审 | 代码审查 |

## 多设备适配声明

无差异。

## 全局特性影响

| 特性 | 适用？ | 结论 | 关联场景 |
|------|--------|------|----------|
| 无障碍 | 不适用 | 无影响 — 页面场景规则化感知为框架内部 IPC 能力 | — |
| 大字体 | 不适用 | 无影响 — 页面场景规则化感知不涉及 UI 缩放 | — |
| 深色模式 | 不适用 | 无影响 — 页面场景规则化感知不涉及颜色主题 | — |
| 多窗口 | 适用 | 每窗口独立页面场景规则化感知检测和上报 | 多窗口页面场景规则化感知 |
| 多用户 | 不适用 | 无影响 — 页面场景规则化感知不区分用户 | — |
| 版本升级 | 适用 | 无影响 — 无 Public/System API 契约 | — |

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
    query: "PageSceneRuleInfo / PageSceneRuleSetInfo 数据结构 (ui_session_manager_ohos.h:181-197)"
  - repo: "openharmony/ace_engine"
    query: "SavePageSceneDetectFunction / RegisterPageSceneRules / UnregisterPageSceneRules (ui_session_manager_ohos.h:150)"
  - repo: "openharmony/ace_engine"
    query: "pageSceneRuleRegisterProcesses_ atomic 计数器门控 (ui_session_manager.h:277)"
  - repo: "openharmony/ace_engine"
    query: "ContentChangeManager::OnVsyncEnd FlushPageSceneNodeChanged 收敛 (content_change_manager.cpp)"
  - repo: "openharmony/ace_engine"
    query: "UIContentImpl SetStartContentChangeDetectCallback 投递到 UI 线程 (ui_content_impl.cpp:6817)"
  - repo: "openharmony/ace_engine"
    query: "TextInput / TextArea / Search / RichEditor 文本输入类控件定义 (text_field_model_ng.cpp / search_model_ng.cpp / rich_editor_model_ng.cpp)"
```

**关键文档：**
- [design.md](03-engine-framework/09-uisession/01-uisession-service/design.md)
