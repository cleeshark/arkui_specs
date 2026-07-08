# 特性规格

> Func-05-02-01-Feat-10 NavDestination 生命周期与事件回调：固化 onShown/onHidden/onBackPressed/onResult/onReady/onWillAppear/onWillDisappear/onWillShow/onWillHide/onActive/onInactive/onSaveState/onRestoreState/onNewParam 的行为规格。

## 概述

| 属性 | 值 |
|------|-----|
| 特性名称 | NavDestination 生命周期与事件回调 |
| 特性编号 | Func-05-02-01-Feat-10 |
| 所属 Epic | 无（已有能力补录） |
| 优先级 | P1 |
| 目标版本 | API 10 起支持 onShown/onHidden/onBackPressed；API 11 起支持 onReady；API 12 起支持 onWillAppear/onWillDisappear/onWillShow/onWillHide；API 15 起支持 onResult；API 17 起支持 onActive/onInactive；API 19 起支持 onNewParam；API 21 起支持 VisibilityChangeReason.APP_STATE；API 26 起支持 onSaveState/onRestoreState |
| SIG 归属 | ArkUI SIG |
| 状态 | Baselined |
| 复杂度 | 高 |

## 本次变更范围（Delta）

无新增变更，已有实现补录。

## 输入文档

| 文档 | 路径 | 状态 |
|------|------|------|
| Design | `specs/05-ui-components/02-navigation-components/03-nav-destination/design.md` | Baselined |
| NavDestinationEventHub | `frameworks/core/components_ng/pattern/navrouter/navdestination_event_hub.h` | — |
| NavDestinationEventHub.cpp | `frameworks/core/components_ng/pattern/navrouter/navdestination_event_hub.cpp` | — |
| NavDestinationPattern | `frameworks/core/components_ng/pattern/navrouter/navdestination_pattern.cpp/.h` | — |
| NavDestinationPatternMultiThread | `frameworks/core/components_ng/pattern/navrouter/navdestination_pattern_multi_thread.cpp` | — |
| NavDestinationContext | `frameworks/core/components_ng/pattern/navrouter/navdestination_context.h` | — |
| ObserverHandler (NavDestinationState) | `frameworks/core/components_ng/base/observer_handler.h` | — |
| NavigationDeclaration (enums) | `frameworks/core/components_ng/pattern/navigation/navigation_declaration.h` | — |
| NavigationPattern | `frameworks/core/components_ng/pattern/navigation/navigation_pattern.cpp/.h` | — |
| NavigationGroupNode | `frameworks/core/components_ng/pattern/navigation/navigation_group_node.cpp/.h` | — |
| NavDestinationGroupNode | `frameworks/core/components_ng/pattern/navrouter/navdestination_group_node.cpp/.h` | — |
| JSNavDestination | `frameworks/bridge/declarative_frontend/jsview/js_navdestination.cpp` | — |
| JSNavPathInfo | `frameworks/bridge/declarative_frontend/jsview/js_navdestination_context.h` | — |
| NavDestinationModelNG | `frameworks/core/components_ng/pattern/navrouter/navdestination_model_ng.cpp/.h` | — |
| ArkTS NavDestination Bridge | `frameworks/bridge/declarative_frontend/engine/jsi/nativeModule/arkts_native_nav_destination_bridge.cpp` | — |

---

## 用户故事

### US-1: NavDestination 显示/隐藏生命周期

**作为** 应用开发者,
**我想要** 通过 onShown/onHidden/onWillAppear/onWillDisappear/onWillShow/onWillHide 监听 NavDestination 的显示与隐藏生命周期事件,
**以便** 在页面可见性变化时执行自定义逻辑（如启动/停止动画、加载/释放资源）。

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-1.1 | WHEN 调用 `.onShown(callback: (reason: VisibilityChangeReason) => void)` THEN 注册 onShown 回调，回调参数为 VisibilityChangeReason 枚举值 | 正常 |
| AC-1.2 | WHEN NavDestination 通过 push 转场变为可见 THEN 回调触发，参数 reason 为 VisibilityChangeReason.TRANSITION (0) | 正常 |
| AC-1.3 | WHEN NavDestination 因 ContentCover 被覆盖后恢复可见 THEN 回调触发，参数 reason 为 VisibilityChangeReason.CONTENT_COVER (1) | 正常 |
| AC-1.4 | WHEN NavDestination 因应用从后台恢复前台变为可见 THEN 回调触发，参数 reason 为 VisibilityChangeReason.APP_STATE (2) | 正常 |
| AC-1.5 | WHEN 调用 `.onHidden(callback: (reason: VisibilityChangeReason) => void)` THEN 注册 onHidden 回调，回调参数为 VisibilityChangeReason 枚举值 | 正常 |
| AC-1.6 | WHEN NavDestination 通过 pop 转场变为不可见 THEN 回调触发，参数 reason 为 VisibilityChangeReason.TRANSITION (0) | 正常 |
| AC-1.7 | WHEN NavDestination 因 ContentCover 被覆盖 THEN 回调触发，参数 reason 为 VisibilityChangeReason.CONTENT_COVER (1) | 正常 |
| AC-1.8 | WHEN NavDestination 因应用退入后台 THEN 回调触发，参数 reason 为 VisibilityChangeReason.APP_STATE (2) | 正常 |
| AC-1.9 | WHEN NavDestination 通过 push 进入 THEN 生命周期回调触发顺序为 onWillAppear → onWillShow → onShown | 正常 |
| AC-1.10 | WHEN NavDestination 通过 pop 退出 THEN 生命周期回调触发顺序为 onWillHide → onWillDisappear → onHidden | 正常 |
| AC-1.11 | WHEN 调用 `.onWillAppear(callback: () => void)` THEN 注册 onWillAppear 回调，回调无参数 | 正常 |
| AC-1.12 | WHEN 调用 `.onWillDisappear(callback: () => void)` THEN 注册 onWillDisappear 回调，回调无参数 | 正常 |
| AC-1.13 | WHEN 调用 `.onWillShow(callback: () => void)` THEN 注册 onWillShow 回调，回调无参数 | 正常 |
| AC-1.14 | WHEN 调用 `.onWillHide(callback: () => void)` THEN 注册 onWillHide 回调，回调无参数 | 正常 |
| AC-1.15 | WHEN NavDestination 已处于 onShown 状态且再次触发 ON_SHOW/ON_WILL_SHOW THEN 回调不重复触发 | 边界 |
| AC-1.16 | WHEN NavDestination 已处于 onHidden 状态且再次触发 ON_HIDE/ON_WILL_HIDE THEN 回调不重复触发 | 边界 |
| AC-1.17 | WHEN NavDestination onWillHide 触发 THEN 同时触发自动保存 FireAutoSave（如果 NeedRequestAutoSave） | 正常 |
| AC-1.18 | WHEN NavDestination onHidden 触发 THEN 同时触发 FireOnSaveState 回调（如果已注册 onSaveState） | 正常 |
| AC-1.19 | WHEN 未注册任何生命周期回调 THEN 对应事件不触发回调 | 边界 |

### US-2: NavDestination 激活/非激活状态

**作为** 应用开发者,
**我想要** 通过 onActive/onInactive 监听 NavDestination 在 Navigation 栈中的激活与非激活状态变化，并获知变化原因,
**以便** 在页面交互状态变化时执行相应逻辑（如暂停/恢复交互、记录原因）。

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-2.1 | WHEN 调用 `.onActive(callback?: (reason: NavDestinationActiveReason) => void)` THEN 注册 onActive 回调，回调参数为 NavDestinationActiveReason 枚举值 | 正常 |
| AC-2.2 | WHEN NavDestination 因 push 转场变为激活 THEN 回调触发，参数 reason 为 NavDestinationActiveReason.TRANSITION (0) | 正常 |
| AC-2.3 | WHEN NavDestination 因 ContentCover 关闭恢复激活 THEN 回调触发，参数 reason 为 NavDestinationActiveReason.CONTENT_COVER (1) | 正常 |
| AC-2.4 | WHEN NavDestination 因 Sheet 关闭恢复激活 THEN 回调触发，参数 reason 为 NavDestinationActiveReason.SHEET (2) | 正常 |
| AC-2.5 | WHEN NavDestination 因 Dialog 关闭恢复激活 THEN 回调触发，参数 reason 为 NavDestinationActiveReason.DIALOG (3) | 正常 |
| AC-2.6 | WHEN NavDestination 因 Overlay 关闭恢复激活 THEN 回调触发，参数 reason 为 NavDestinationActiveReason.OVERLAY (4) | 正常 |
| AC-2.7 | WHEN NavDestination 因应用前台恢复激活 THEN 回调触发，参数 reason 为 NavDestinationActiveReason.APP_STATE_CHANGE (5) | 正常 |
| AC-2.8 | WHEN 调用 `.onInactive(callback?: (reason: NavDestinationActiveReason) => void)` THEN 注册 onInactive 回调，回调参数为 NavDestinationActiveReason 枚举值 | 正常 |
| AC-2.9 | WHEN NavDestination 因 pop 转场变为非激活 THEN 回调触发，参数 reason 为 NavDestinationActiveReason.TRANSITION (0) | 正常 |
| AC-2.10 | WHEN NavDestination 因 ContentCover 打开变为非激活 THEN 回调触发，参数 reason 为 NavDestinationActiveReason.CONTENT_COVER (1) | 正常 |
| AC-2.11 | WHEN NavDestination 因 Sheet 打开变为非激活 THEN 回调触发，参数 reason 为 NavDestinationActiveReason.SHEET (2) | 正常 |
| AC-2.12 | WHEN NavDestination 因 Dialog 打开变为非激活 THEN 回调触发，参数 reason 为 NavDestinationActiveReason.DIALOG (3) | 正常 |
| AC-2.13 | WHEN NavDestination 因 Overlay 打开变为非激活 THEN 回调触发，参数 reason 为 NavDestinationActiveReason.OVERLAY (4) | 正常 |
| AC-2.14 | WHEN NavDestination 因应用退入后台变为非激活 THEN 回调触发，参数 reason 为 NavDestinationActiveReason.APP_STATE_CHANGE (5) | 正常 |
| AC-2.15 | WHEN NavDestination 已处于 active 状态且再次触发 ON_ACTIVE THEN 不重复触发回调 | 边界 |
| AC-2.16 | WHEN NavDestination 父级 NavDestination 处于 inactive 状态 THEN 子级 NavDestination 不触发 onActive | 边界 |
| AC-2.17 | WHEN 未注册 onActive/onInactive THEN 激活/非激活变化时不触发回调 | 边界 |

### US-3: NavDestination 返回拦截

**作为** 应用开发者,
**我想要** 通过 onBackPressed 拦截 NavDestination 的返回按键事件，
**以便** 在用户按下返回键时执行自定义逻辑，并决定是否拦截默认返回行为。

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-3.1 | WHEN 调用 `.onBackPressed(callback: () => boolean)` THEN 注册返回拦截回调 | 正常 |
| AC-3.2 | WHEN 用户点击返回按钮且 onBackPressed 回调返回 true THEN 拦截返回事件，不执行默认 pop 行为 | 正常 |
| AC-3.3 | WHEN 用户点击返回按钮且 onBackPressed 回调返回 false THEN 不拦截返回事件，执行默认 pop 行为 | 正常 |
| AC-3.4 | WHEN 用户点击返回按钮且未注册 onBackPressed THEN 执行默认 pop 行为 | 边界 |
| AC-3.5 | WHEN onBackPressed 触发 THEN NavDestinationState 设置为 ON_BACKPRESS (100) | 正常 |
| AC-3.6 | WHEN onBackPressed 触发 THEN UIObserverHandler 通知 NavDestinationState 为 ON_BACKPRESS | 正常 |
| AC-3.7 | WHEN NavDestination 上存在 overlay（如半模态、弹窗） THEN 先检查 overlay 是否可关闭，overlayOnBackPressed 返回 true 时不触发用户 onBackPressed | 正常 |

### US-4: NavDestination 结果与参数回调

**作为** 应用开发者,
**我想要** 通过 onResult/onNewParam/onReady 处理 NavDestination 的结果回调、参数更新与上下文就绪事件,
**以便** 在页面被弹出时接收结果数据、在单例模式下接收参数更新、在页面构建就绪时获取 NavDestinationContext。

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-4.1 | WHEN 调用 `.onResult(callback?: (info: ESObject) => void)` THEN 注册结果回调，回调参数为弹出时携带的结果数据 | 正常 |
| AC-4.2 | WHEN NavDestination 被 pop 弹出且携带结果数据 THEN onResult 回调触发，参数为结果数据 | 正常 |
| AC-4.3 | WHEN onResult 回调注册 THEN 通过 SetOnPop 将 popCallback 存储在 JSNavPathInfo.navDestinationPopCallback_ 中 | 正常 |
| AC-4.4 | WHEN 调用 `.onNewParam(callback?: (param: ESObject) => void)` THEN 注册参数更新回调 | 正常 |
| AC-4.5 | WHEN NavDestination 为单例模式（LaunchMode.SINGLE）且接收新参数 THEN onNewParam 回调触发，参数为新传入的参数 | 正常 |
| AC-4.6 | WHEN NavDestination 非单例模式 THEN onNewParam 回调不触发 | 边界 |
| AC-4.7 | WHEN 调用 `.onReady(callback: (context: NavDestinationContext) => void)` THEN 注册 onReady 回调 | 正常 |
| AC-4.8 | WHEN NavDestination 首次执行 ShallowBuilder 深渲染（ExecuteDeepRender）之前 THEN onReady 回调触发，参数为 NavDestinationContext 对象 | 正常 |
| AC-4.9 | WHEN NavDestinationContext 对象提供 THEN context 包含 pathInfo（NavPathInfo）、pathStack（NavigationStack）、navDestinationId（uint64_t）、mode（NavDestinationMode）属性 | 正常 |
| AC-4.10 | WHEN NavDestination 为缓存节点（isCacheNode_） THEN onReady 不触发 | 边界 |
| AC-4.11 | WHEN onResult 未注册 THEN 弹出时不触发回调 | 边界 |

### US-5: NavDestination 状态保存/恢复

**作为** 应用开发者,
**我想要** 通过 onSaveState/onRestoreState 实现 NavDestination 的自定义状态保存与恢复,
**以便** 在页面被回收或恢复时保持用户状态数据。

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-5.1 | WHEN 调用 `.onSaveState(callback?: () => Record<string, Object> \| null)` THEN 注册状态保存回调 | 正常 |
| AC-5.2 | WHEN NavDestination 隐藏时 FireOnHiddenEvent 触发 THEN 如果已注册 onSaveState 则调用 FireOnSaveState | 正常 |
| AC-5.3 | WHEN onSaveState 回调返回 Record<string, Object> THEN 返回数据通过 CallSavedStateToJS 序列化并存储到 NavigationStack | 正常 |
| AC-5.4 | WHEN onSaveState 回调返回 null THEN 不保存任何状态数据 | 边界 |
| AC-5.5 | WHEN 调用 `.onRestoreState(callback?: (state: Record<string, Object> \| null) => void)` THEN 注册状态恢复回调 | 正常 |
| AC-5.6 | WHEN NavDestination 恢复且存在已保存的状态数据 THEN onRestoreState 回调触发，参数为反序列化后的状态数据 | 正常 |
| AC-5.7 | WHEN NavDestination 恢复但无已保存的状态数据 THEN onRestoreState 回调触发，参数为 null | 边界 |
| AC-5.8 | WHEN NavDestination 隐藏且 onWillHide 触发 THEN FireAutoSave 检查是否 NeedRequestAutoSave，如需要则调用 Container::RequestAutoSave | 正常 |
| AC-5.9 | WHEN onSaveState 内部类型为 NavDestinationSaveStateCallback（std::function\<std::string()\>） THEN CallSavedStateToJS 将 string 结果传递给 NavigationStack.SaveStateToJsCallback 存储 | 正常 |

---

## 验收追溯

| AC编号 | US ID | 关联规则 | 验证手段 |
|-------|-------|----------|----------|
| AC-1.1 | US-1 | R-1 | 单元测试 onShown 注册 |
| AC-1.2 | US-1 | R-1 | 单元测试 onShown TRANSITION |
| AC-1.3 | US-1 | R-1 | 单元测试 onShown CONTENT_COVER |
| AC-1.4 | US-1 | R-1 | 单元测试 onShown APP_STATE |
| AC-1.5 | US-1 | R-2 | 单元测试 onHidden 注册 |
| AC-1.6 | US-1 | R-2 | 单元测试 onHidden TRANSITION |
| AC-1.7 | US-1 | R-2 | 单元测试 onHidden CONTENT_COVER |
| AC-1.8 | US-1 | R-2 | 单元测试 onHidden APP_STATE |
| AC-1.9 | US-1 | R-3 | 单元测试 push 生命周期顺序 |
| AC-1.10 | US-1 | R-3 | 单元测试 pop 生命周期顺序 |
| AC-1.11 | US-1 | R-4 | 单元测试 onWillAppear 注册 |
| AC-1.12 | US-1 | R-5 | 单元测试 onWillDisappear 注册 |
| AC-1.13 | US-1 | R-6 | 单元测试 onWillShow 注册 |
| AC-1.14 | US-1 | R-7 | 单元测试 onWillHide 注册 |
| AC-1.15 | US-1 | R-8 | 单元测试 onShown 防重复触发 |
| AC-1.16 | US-1 | R-8 | 单元测试 onHidden 防重复触发 |
| AC-1.17 | US-1 | R-9 | 代码审查 FireAutoSave 调用链 |
| AC-1.18 | US-1 | R-10 | 代码审查 FireOnSaveState 调用链 |
| AC-1.19 | US-1 | R-1~R-7 | 代码审查 NavDestinationEventHub 默认空回调 |
| AC-2.1 | US-2 | R-11 | 单元测试 onActive 注册 |
| AC-2.2 | US-2 | R-11 | 单元测试 onActive TRANSITION |
| AC-2.3 | US-2 | R-11 | 单元测试 onActive CONTENT_COVER |
| AC-2.4 | US-2 | R-11 | 单元测试 onActive SHEET |
| AC-2.5 | US-2 | R-11 | 单元测试 onActive DIALOG |
| AC-2.6 | US-2 | R-11 | 单元测试 onActive OVERLAY |
| AC-2.7 | US-2 | R-11 | 单元测试 onActive APP_STATE_CHANGE |
| AC-2.8 | US-2 | R-12 | 单元测试 onInactive 注册 |
| AC-2.9 | US-2 | R-12 | 单元测试 onInactive TRANSITION |
| AC-2.10 | US-2 | R-12 | 单元测试 onInactive CONTENT_COVER |
| AC-2.11 | US-2 | R-12 | 单元测试 onInactive SHEET |
| AC-2.12 | US-2 | R-12 | 单元测试 onInactive DIALOG |
| AC-2.13 | US-2 | R-12 | 单元测试 onInactive OVERLAY |
| AC-2.14 | US-2 | R-12 | 单元测试 onInactive APP_STATE_CHANGE |
| AC-2.15 | US-2 | R-13 | 单元测试 onActive 防重复触发 |
| AC-2.16 | US-2 | R-14 | 单元测试父级 inactive 阻止子级 active |
| AC-2.17 | US-2 | R-11, R-12 | 代码审查 NavDestinationEventHub 默认空回调 |
| AC-3.1 | US-3 | R-15 | 单元测试 onBackPressed 注册 |
| AC-3.2 | US-3 | R-15 | 单元测试 onBackPressed 返回 true 拦截 |
| AC-3.3 | US-3 | R-15 | 单元测试 onBackPressed 返回 false 不拦截 |
| AC-3.4 | US-3 | R-15 | 代码审查默认返回 false |
| AC-3.5 | US-3 | R-16 | 代码审查 state 设置为 ON_BACKPRESS |
| AC-3.6 | US-3 | R-16 | 代码审查 UIObserverHandler 通知 |
| AC-3.7 | US-3 | R-17 | 单元测试 overlay 优先处理 |
| AC-4.1 | US-4 | R-18 | 单元测试 onResult 注册 |
| AC-4.2 | US-4 | R-18 | 单元测试 onResult pop 结果回调 |
| AC-4.3 | US-4 | R-19 | 代码审查 JSNavPathInfo.navDestinationPopCallback_ |
| AC-4.4 | US-4 | R-20 | 单元测试 onNewParam 注册 |
| AC-4.5 | US-4 | R-20 | 单元测试单例模式 onNewParam 触发 |
| AC-4.6 | US-4 | R-20 | 单元测试非单例模式不触发 |
| AC-4.7 | US-4 | R-21 | 单元测试 onReady 注册 |
| AC-4.8 | US-4 | R-21 | 单元测试 onReady 触发时机 |
| AC-4.9 | US-4 | R-22 | 单元测试 NavDestinationContext 属性 |
| AC-4.10 | US-4 | R-23 | 代码审查 isCacheNode_ 检查 |
| AC-4.11 | US-4 | R-18 | 代码审查默认无回调 |
| AC-5.1 | US-5 | R-24 | 单元测试 onSaveState 注册 |
| AC-5.2 | US-5 | R-10 | 代码审查 FireOnSaveState 调用链 |
| AC-5.3 | US-5 | R-25 | 单元测试 onSaveState 返回数据 |
| AC-5.4 | US-5 | R-24 | 单元测试 onSaveState 返回 null |
| AC-5.5 | US-5 | R-26 | 单元测试 onRestoreState 注册 |
| AC-5.6 | US-5 | R-26 | 单元测试 onRestoreState 有数据 |
| AC-5.7 | US-5 | R-26 | 单元测试 onRestoreState 无数据 |
| AC-5.8 | US-5 | R-9 | 代码审查 FireAutoSave 调用链 |
| AC-5.9 | US-5 | R-25 | 代码审查 CallSavedStateToJS 存储 |

## 规则定义

| 规则ID | 类型 | 触发条件 | 预期行为 | 边界/约束 | 关联AC |
|--------|------|----------|----------|-----------|--------|
| R-1 | 行为 | NavDestination 变为可见 | onShown 回调触发，参数为 VisibilityChangeReason（TRANSITION=0 / CONTENT_COVER=1 / APP_STATE=2）；回调存储在 onShownEvent_（`navdestination_event_hub.h:253`），触发在 FireOnShownEvent（`navdestination_event_hub.cpp:79-118`）；reason 参数通过 static_cast\<int32_t\>(reason) 转换传递（`navdestination_event_hub.cpp:93`） | 未注册时 onShownEvent_ 为空，不触发 | AC-1.1~AC-1.4, AC-1.19 |
| R-2 | 行为 | NavDestination 变为不可见 | onHidden 回调触发，参数为 VisibilityChangeReason（TRANSITION=0 / CONTENT_COVER=1 / APP_STATE=2）；回调存储在 onHiddenEvent_（`navdestination_event_hub.h:254`），触发在 FireOnHiddenEvent（`navdestination_event_hub.cpp:121-147`）；reason 参数通过 static_cast\<int32_t\>(reason) 转换（`navdestination_event_hub.cpp:133`）；FireOnHiddenEvent 结尾自动调用 FireOnSaveState（`navdestination_event_hub.cpp:146`） | 未注册时 onHiddenEvent_ 为空，不触发 | AC-1.5~AC-1.8, AC-1.19 |
| R-3 | 行为 | NavDestination push 进入 | 生命周期回调按顺序触发：onWillAppear → onWillShow → onShown；onWillAppear 由 NavDestinationPattern.OnDetachFromMainTree 触发 ON_WILL_DISAPPEAR 时（home/related 类型）间接调度（`navdestination_pattern.cpp:574-592`）；onWillShow 由 NotifyDestinationLifecycle ON_WILL_SHOW 分支触发（`navigation_pattern.cpp:5125-5128`）；onShown 由 FireOnShowLifecycle 触发（`navigation_pattern.cpp:5146-5165`） | 顺序由 NavigationPattern.NotifyDestinationLifecycle 控制 | AC-1.9 |
| R-4 | 行为 | NavDestination 即将出现 | onWillAppear 回调触发，无参数；回调存储在 onWillAppear_（`navdestination_event_hub.h:246`），触发在 FireOnWillAppear（`navdestination_event_hub.cpp:197-209`）；state 设置为 NavDestinationState::ON_WILL_APPEAR（`navdestination_event_hub.cpp:204`）；UIObserverHandler 通知 ON_WILL_APPEAR（`navdestination_event_hub.cpp:205-206`） | 回调在 UI 线程执行 | AC-1.11 |
| R-5 | 行为 | NavDestination 即将消失 | onWillDisappear 回调触发，无参数；回调存储在 onWillDisAppear_（`navdestination_event_hub.h:249`），触发在 FireOnWillDisAppear（`navdestination_event_hub.cpp:244-257`）；state 设置为 NavDestinationState::ON_WILL_DISAPPEAR（`navdestination_event_hub.cpp:251`）；UIObserverHandler 通知 ON_WILL_DISAPPEAR（`navdestination_event_hub.cpp:252-253`） | 回调在 UI 线程执行 | AC-1.12 |
| R-6 | 行为 | NavDestination 即将显示 | onWillShow 回调触发，无参数；回调存储在 onWillShow_（`navdestination_event_hub.h:247`），触发在 FireOnWillShow（`navdestination_event_hub.cpp:212-225`）；state 设置为 NavDestinationState::ON_WILL_SHOW（`navdestination_event_hub.cpp:219`）；UIObserverHandler 通知 ON_WILL_SHOW（`navdestination_event_hub.cpp:220-221`） | 回调在 UI 线程执行 | AC-1.13 |
| R-7 | 行为 | NavDestination 即将隐藏 | onWillHide 回调触发，无参数；回调存储在 onWillHide_（`navdestination_event_hub.h:248`），触发在 FireOnWillHide（`navdestination_event_hub.cpp:227-242`）；state 设置为 NavDestinationState::ON_WILL_HIDE（`navdestination_event_hub.cpp:234`）；UIObserverHandler 通知 ON_WILL_HIDE（`navdestination_event_hub.cpp:235-236`）；FireOnWillHide 结尾调用 FireAutoSave（`navdestination_event_hub.cpp:241`） | 回调在 UI 线程执行 | AC-1.14 |
| R-8 | 行为 | NavDestination 已处于 shown/hidden 状态 | 防止重复触发；NotifyDestinationLifecycle 检查 navDestinationPattern->GetIsOnShow()：isOnShow=true 且 lifecycle 为 ON_SHOW 或 ON_WILL_SHOW 则返回（`navigation_pattern.cpp:5119-5123`）；同理 isOnShow=false 且 ON_HIDE 或 ON_WILL_HIDE 则返回 | — | AC-1.15, AC-1.16 |
| R-9 | 行为 | NavDestination onWillHide 触发 | FireOnWillHide 完成回调后调用 FireAutoSave（`navdestination_event_hub.cpp:241`）；FireAutoSave 检查 node->NeedRequestAutoSave()（`navdestination_event_hub.cpp:58-61`），如满足则调用 Container::RequestAutoSave（`navdestination_event_hub.cpp:65`） | — | AC-1.17 |
| R-10 | 行为 | NavDestination onHidden 触发 | FireOnHiddenEvent 完成回调后调用 FireOnSaveState（`navdestination_event_hub.cpp:146`）；FireOnSaveState 检查 onSaveState_ 是否注册（`navdestination_event_hub.cpp:70`），如注册则调用 onSaveState_() 返回 string，通过 pattern->CallSavedStateToJS 存到 NavigationStack（`navdestination_event_hub.cpp:75`）；CallSavedStateToJS 调用 stack->SaveStateToJsCallback（`navdestination_pattern.cpp:1162`） | onSaveState_ 未注册时不触发 | AC-1.18 |
| R-11 | 行为 | NavDestination 变为激活 | onActive 回调触发，参数为 NavDestinationActiveReason（TRANSITION=0 / CONTENT_COVER=1 / SHEET=2 / DIALOG=3 / OVERLAY=4 / APP_STATE_CHANGE=5）；回调存储在 onActive_（`navdestination_event_hub.h:251`），触发在 FireOnActive（`navdestination_event_hub.cpp:272-285`）；state 设置为 NavDestinationState::ON_ACTIVE（`navdestination_event_hub.cpp:279`）；UIObserverHandler 通知 ON_ACTIVE（`navdestination_event_hub.cpp:280-281`）；reason 通过 static_cast\<int32_t\>(reason) 转换（`navdestination_event_hub.cpp:283`）；由 FireOnActiveLifecycle 触发（`navigation_pattern.cpp:5167-5180`），如已 active 则不触发（`navigation_pattern.cpp:5172-5174`） | 回调在 UI 线程执行 | AC-2.1~AC-2.7, AC-2.17 |
| R-12 | 行为 | NavDestination 变为非激活 | onInactive 回调触发，参数为 NavDestinationActiveReason（TRANSITION=0 / CONTENT_COVER=1 / SHEET=2 / DIALOG=3 / OVERLAY=4 / APP_STATE_CHANGE=5）；回调存储在 onInactive_（`navdestination_event_hub.h:252`），触发在 FireOnInactive（`navdestination_event_hub.cpp:287-300`）；state 设置为 NavDestinationState::ON_INACTIVE（`navdestination_event_hub.cpp:294`）；UIObserverHandler 通知 ON_INACTIVE（`navdestination_event_hub.cpp:295-296`）；reason 通过 static_cast\<int32_t\>(reason) 转换（`navdestination_event_hub.cpp:298`）；由 FireOnInactiveLifecycle 触发（`navigation_pattern.cpp:5182-5195`），如已 inactive 则不触发（`navigation_pattern.cpp:5187-5189`） | 回调在 UI 线程执行 | AC-2.8~AC-2.14, AC-2.17 |
| R-13 | 行为 | NavDestination 已 active | FireOnActiveLifecycle 检查 navDestinationPattern->IsActive()（`navigation_pattern.cpp:5172-5174`）：如果 IsActive() 返回 true 则直接返回不触发 onActive | — | AC-2.15 |
| R-14 | 行为 | 父级 NavDestination inactive | FireOnActiveLifecycle 检查 CheckParentDestinationInactive()（`navigation_pattern.cpp:5172-5174`）：如果父级 inactive 则不触发子级 onActive | — | AC-2.16 |
| R-15 | 行为 | 用户点击返回按钮 | onBackPressed 回调触发；回调存储在 onBackPressedEvent_（`navdestination_event_hub.h:250`），触发在 FireOnBackPressedEvent（`navdestination_event_hub.cpp:259-270`）；返回值 bool：true 拦截返回（`navigation_group_node.cpp:658-662`），false 不拦截执行默认 pop；未注册时 FireOnBackPressedEvent 返回 false（`navdestination_event_hub.cpp:269`） | 回调在 UI 线程执行 | AC-3.1~AC-3.4 |
| R-16 | 行为 | onBackPressed 触发 | NavDestinationState 设置为 ON_BACKPRESS（`navigation_group_node.cpp:651`）；UIObserverHandler 通知 NavDestinationState 为 ON_BACKPRESS（`navigation_group_node.cpp:653-654`） | — | AC-3.5, AC-3.6 |
| R-17 | 行为 | NavDestination 上存在 overlay | 返回按钮事件处理中先检查 OverlayOnBackPressed（`navdestination_pattern.cpp:476-483`）：overlayManager_->IsCurrentNodeProcessRemoveOverlay 判断是否有可关闭 overlay，overlayManager_->RemoveOverlay 返回 true 时 overlay 关闭，onBackPressed 不触发 | — | AC-3.7 |
| R-18 | 行为 | NavDestination 被 pop 弹出携带结果 | onResult 回调触发；通过 SetOnPop 注册（`navdestination_model_ng.cpp:1874-1889`），回调存储在 JSNavPathInfo.navDestinationPopCallback_（`js_navdestination_context.h:68-71`）；JS 层通过 JSNavDestination.SetResultCallback 注册（`js_navdestination.cpp:980-998`）；ArkTS 层通过 NavDestinationBridge.SetOnResult 注册（`arkts_native_nav_destination_bridge.cpp:1339-1366`） | 未注册时不触发 | AC-4.1~AC-4.3, AC-4.11 |
| R-19 | 行为 | onResult 注册机制 | JSNavDestination.SetResultCallback 调用 NavDestinationModel.GetInstance().SetOnPop（`js_navdestination.cpp:997`）；SetOnPop 将 popCallback 设置到 JSNavPathInfo.navDestinationPopCallback_（`js_navdestination_context.h:68-71`） | — | AC-4.3 |
| R-20 | 行为 | NavDestination 单例模式参数更新 | onNewParam 回调触发；回调存储在 onNewParamCallback_（`navdestination_event_hub.h:255`），动态版触发 FireOnNewParam（`navdestination_event_hub.h:197-202`）；静态版触发 FireOnNewParamStatic（`navdestination_event_hub.h:209-214`）；由 NavigationPattern.FireOnNewParam 分发（`navigation_pattern.cpp:6250-6269`）：isStatic=true 调用 FireOnNewParamStatic，isStatic=false 调用 FireOnNewParam | 仅单例模式（LaunchMode.SINGLE）触发 | AC-4.4~AC-4.6 |
| R-21 | 行为 | NavDestination 首次深渲染 | onReady 回调触发；回调存储在 onReadyEvent_（`navdestination_event_hub.h:258`），触发在 FireOnReady（`navdestination_event_hub.h:104-110`）；触发时机在 NavDestinationGroupNode.ProcessShallowBuilder 中，shallowBuilder 存在且 IsExecuteDeepRenderDone() 为 false 时触发（`navdestination_group_node.cpp:275-281`） | — | AC-4.7, AC-4.8 |
| R-22 | 行为 | NavDestinationContext 对象属性 | NavDestinationContext 提供 pathInfo（NavPathInfo, `navdestination_context.h:103-106`）、pathStack（NavigationStack, `navdestination_context.h:113-116`）、navDestinationId（uint64_t, `navdestination_context.h:138-141`）、mode（NavDestinationMode, `navdestination_context.h:163-166`） | — | AC-4.9 |
| R-23 | 行为 | NavDestination 缓存节点 | ProcessShallowBuilder 检查 isCacheNode_（`navdestination_group_node.cpp:267-268`）：为缓存节点时直接返回不执行深渲染、不触发 onReady | — | AC-4.10 |
| R-24 | 行为 | onSaveState 注册 | SetOnSaveState 存储 NavDestinationSaveStateCallback（`navdestination_event_hub.h:216-218`）；NavDestinationSaveStateCallback 类型为 std::function\<std::string()\>（`navigation_declaration.h:347`）；回调返回值为序列化状态字符串 | onSaveState_ 为空时不触发 | AC-5.1, AC-5.4 |
| R-25 | 行为 | onSaveState 数据存储 | FireOnSaveState 调用 onSaveState_() 获取 string（`navdestination_event_hub.cpp:70-76`）；pattern->CallSavedStateToJS 将 string 传递给 NavigationStack.SaveStateToJsCallback（`navdestination_pattern.cpp:1153-1163`）；SaveStateToJsCallback 调用 stack->SaveStateToJsCallback(index, name, navDestinationId, savedState) 存储（`navdestination_pattern.cpp:1162`） | — | AC-5.3, AC-5.9 |
| R-26 | 行为 | onRestoreState 回调 | SetOnRestoreState 存储 NavDestinationRestoreStateCallback（`navdestination_event_hub.h:221-223`）；NavDestinationRestoreStateCallback 类型为 std::function\<void(const std::string& state)\>（`navigation_declaration.h:348`）；FireOnRestoreState 接收 string 参数（`navdestination_event_hub.h:228-233`），传递给 onRestoreState_ 回调 | onRestoreState_ 为空时不触发 | AC-5.5~AC-5.7 |

---

## 验证映射

| VM编号 | AC编号 | 验证类型 | 位置/用例 |
|-------|-------|----------|-----------|
| VM-1 | AC-1.1 | 单元测试 | `test/unittest/core/pattern/navrouter/` onShown 注册 |
| VM-2 | AC-1.2 | 单元测试 | `test/unittest/core/pattern/navrouter/` onShown TRANSITION reason |
| VM-3 | AC-1.3 | 单元测试 | `test/unittest/core/pattern/navrouter/` onShown CONTENT_COVER reason |
| VM-4 | AC-1.4 | 单元测试 | `test/unittest/core/pattern/navrouter/` onShown APP_STATE reason |
| VM-5 | AC-1.5 | 单元测试 | `test/unittest/core/pattern/navrouter/` onHidden 注册 |
| VM-6 | AC-1.6 | 单元测试 | `test/unittest/core/pattern/navrouter/` onHidden TRANSITION reason |
| VM-7 | AC-1.7 | 单元测试 | `test/unittest/core/pattern/navrouter/` onHidden CONTENT_COVER reason |
| VM-8 | AC-1.8 | 单元测试 | `test/unittest/core/pattern/navrouter/` onHidden APP_STATE reason |
| VM-9 | AC-1.9 | 单元测试 | `test/unittest/core/pattern/navrouter/` push 生命周期顺序 |
| VM-10 | AC-1.10 | 单元测试 | `test/unittest/core/pattern/navrouter/` pop 生命周期顺序 |
| VM-11 | AC-1.11 | 单元测试 | `test/unittest/core/pattern/navrouter/` onWillAppear 注册 |
| VM-12 | AC-1.12 | 单元测试 | `test/unittest/core/pattern/navrouter/` onWillDisappear 注册 |
| VM-13 | AC-1.13 | 单元测试 | `test/unittest/core/pattern/navrouter/` onWillShow 注册 |
| VM-14 | AC-1.14 | 单元测试 | `test/unittest/core/pattern/navrouter/` onWillHide 注册 |
| VM-15 | AC-1.15 | 单元测试 | `test/unittest/core/pattern/navrouter/` onShown 防重复触发 |
| VM-16 | AC-1.16 | 单元测试 | `test/unittest/core/pattern/navrouter/` onHidden 防重复触发 |
| VM-17 | AC-1.17 | 代码审查 | `navdestination_event_hub.cpp:56-66` FireAutoSave 调用链 |
| VM-18 | AC-1.18 | 代码审查 | `navdestination_event_hub.cpp:68-77` FireOnSaveState 调用链 |
| VM-19 | AC-1.19 | 代码审查 | `navdestination_event_hub.h:246-258` 默认空回调字段 |
| VM-20 | AC-2.1 | 单元测试 | `test/unittest/core/pattern/navrouter/` onActive 注册 |
| VM-21 | AC-2.2 | 单元测试 | `test/unittest/core/pattern/navrouter/` onActive TRANSITION |
| VM-22 | AC-2.3 | 单元测试 | `test/unittest/core/pattern/navrouter/` onActive CONTENT_COVER |
| VM-23 | AC-2.4 | 单元测试 | `test/unittest/core/pattern/navrouter/` onActive SHEET |
| VM-24 | AC-2.5 | 单元测试 | `test/unittest/core/pattern/navrouter/` onActive DIALOG |
| VM-25 | AC-2.6 | 单元测试 | `test/unittest/core/pattern/navrouter/` onActive OVERLAY |
| VM-26 | AC-2.7 | 单元测试 | `test/unittest/core/pattern/navrouter/` onActive APP_STATE_CHANGE |
| VM-27 | AC-2.8 | 单元测试 | `test/unittest/core/pattern/navrouter/` onInactive 注册 |
| VM-28 | AC-2.9 | 单元测试 | `test/unittest/core/pattern/navrouter/` onInactive TRANSITION |
| VM-29 | AC-2.10 | 单元测试 | `test/unittest/core/pattern/navrouter/` onInactive CONTENT_COVER |
| VM-30 | AC-2.11 | 单元测试 | `test/unittest/core/pattern/navrouter/` onInactive SHEET |
| VM-31 | AC-2.12 | 单元测试 | `test/unittest/core/pattern/navrouter/` onInactive DIALOG |
| VM-32 | AC-2.13 | 单元测试 | `test/unittest/core/pattern/navrouter/` onInactive OVERLAY |
| VM-33 | AC-2.14 | 单元测试 | `test/unittest/core/pattern/navrouter/` onInactive APP_STATE_CHANGE |
| VM-34 | AC-2.15 | 代码审查 | `navigation_pattern.cpp:5172-5174` IsActive() 防重复触发 |
| VM-35 | AC-2.16 | 代码审查 | `navigation_pattern.cpp:5172-5174` CheckParentDestinationInactive |
| VM-36 | AC-2.17 | 代码审查 | `navdestination_event_hub.h:251-252` onActive_/onInactive_ 默认空 |
| VM-37 | AC-3.1 | 单元测试 | `test/unittest/core/pattern/navrouter/` onBackPressed 注册 |
| VM-38 | AC-3.2 | 单元测试 | `test/unittest/core/pattern/navrouter/` onBackPressed true 拦截 |
| VM-39 | AC-3.3 | 单元测试 | `test/unittest/core/pattern/navrouter/` onBackPressed false 不拦截 |
| VM-40 | AC-3.4 | 代码审查 | `navdestination_event_hub.cpp:269` 默认返回 false |
| VM-41 | AC-3.5 | 代码审查 | `navigation_group_node.cpp:651` state 设置为 ON_BACKPRESS |
| VM-42 | AC-3.6 | 代码审查 | `navigation_group_node.cpp:653-654` UIObserverHandler 通知 |
| VM-43 | AC-3.7 | 代码审查 | `navdestination_pattern.cpp:476-483` OverlayOnBackPressed |
| VM-44 | AC-4.1 | 单元测试 | `test/unittest/core/pattern/navrouter/` onResult 注册 |
| VM-45 | AC-4.2 | 单元测试 | `test/unittest/core/pattern/navrouter/` onResult pop 结果回调 |
| VM-46 | AC-4.3 | 代码审查 | `js_navdestination_context.h:68-71` navDestinationPopCallback_ |
| VM-47 | AC-4.4 | 单元测试 | `test/unittest/core/pattern/navrouter/` onNewParam 注册 |
| VM-48 | AC-4.5 | 单元测试 | `test/unittest/core/pattern/navrouter/` onNewParam 单例触发 |
| VM-49 | AC-4.6 | 单元测试 | `test/unittest/core/pattern/navrouter/` onNewParam 非单例不触发 |
| VM-50 | AC-4.7 | 单元测试 | `test/unittest/core/pattern/navrouter/` onReady 注册 |
| VM-51 | AC-4.8 | 代码审查 | `navdestination_group_node.cpp:275-281` onReady 触发时机 |
| VM-52 | AC-4.9 | 单元测试 | `test/unittest/core/pattern/navrouter/` NavDestinationContext 属性 |
| VM-53 | AC-4.10 | 代码审查 | `navdestination_group_node.cpp:267-268` isCacheNode_ 检查 |
| VM-54 | AC-4.11 | 代码审查 | `js_navdestination.cpp:980-998` 默认无回调 |
| VM-55 | AC-5.1 | 单元测试 | `test/unittest/core/pattern/navrouter/` onSaveState 注册 |
| VM-56 | AC-5.2 | 代码审查 | `navdestination_event_hub.cpp:146` FireOnSaveState 调用链 |
| VM-57 | AC-5.3 | 单元测试 | `test/unittest/core/pattern/navrouter/` onSaveState 返回数据 |
| VM-58 | AC-5.4 | 单元测试 | `test/unittest/core/pattern/navrouter/` onSaveState 返回 null |
| VM-59 | AC-5.5 | 单元测试 | `test/unittest/core/pattern/navrouter/` onRestoreState 注册 |
| VM-60 | AC-5.6 | 单元测试 | `test/unittest/core/pattern/navrouter/` onRestoreState 有数据 |
| VM-61 | AC-5.7 | 单元测试 | `test/unittest/core/pattern/navrouter/` onRestoreState 无数据 |
| VM-62 | AC-5.8 | 代码审查 | `navdestination_event_hub.cpp:56-66` FireAutoSave 调用链 |
| VM-63 | AC-5.9 | 代码审查 | `navdestination_pattern.cpp:1153-1163` CallSavedStateToJS |

---

## 枚举规格

### NavDestinationState

| 常量 | 值 | 说明 | 来源 |
|------|-----|------|------|
| NONE | -1 | 无状态 | `observer_handler.h:39` |
| ON_SHOWN | 0 | NavDestination 可见 | `observer_handler.h:40` |
| ON_HIDDEN | 1 | NavDestination 不可见 | `observer_handler.h:41` |
| ON_APPEAR | 2 | NavDestination 出现（onAppear） | `observer_handler.h:42` |
| ON_DISAPPEAR | 3 | NavDestination 消失（onDisappear） | `observer_handler.h:43` |
| ON_WILL_SHOW | 4 | NavDestination 即将显示 | `observer_handler.h:44` |
| ON_WILL_HIDE | 5 | NavDestination 即将隐藏 | `observer_handler.h:45` |
| ON_WILL_APPEAR | 6 | NavDestination 即将出现 | `observer_handler.h:46` |
| ON_WILL_DISAPPEAR | 7 | NavDestination 即将消失 | `observer_handler.h:47` |
| ON_ACTIVE | 8 | NavDestination 激活 | `observer_handler.h:48` |
| ON_INACTIVE | 9 | NavDestination 非激活 | `observer_handler.h:49` |
| ON_BACKPRESS | 100 | NavDestination 返回拦截 | `observer_handler.h:50` |

### NavDestinationLifecycle

| 常量 | 值 | 说明 | 来源 |
|------|-----|------|------|
| ON_WILL_APPEAR | 0 | 即将出现 | `navigation_declaration.h:257` |
| ON_APPEAR | 1 | 出现 | `navigation_declaration.h:258` |
| ON_WILL_SHOW | 2 | 即将显示 | `navigation_declaration.h:259` |
| ON_SHOW | 3 | 显示 | `navigation_declaration.h:260` |
| ON_ACTIVE | 4 | 激活 | `navigation_declaration.h:261` |
| ON_WILL_HIDE | 5 | 即将隐藏 | `navigation_declaration.h:262` |
| ON_INACTIVE | 6 | 非激活 | `navigation_declaration.h:263` |
| ON_HIDE | 7 | 隐藏 | `navigation_declaration.h:264` |
| ON_WILL_DISAPPEAR | 8 | 即将消失 | `navigation_declaration.h:265` |
| ON_DISAPPEAR | 9 | 消失 | `navigation_declaration.h:266` |

### NavDestVisibilityChangeReason

| 常量 | 值 | 说明 | 来源 |
|------|-----|------|------|
| TRANSITION | 0 | push/pop 转场 | `navigation_declaration.h:279` |
| CONTENT_COVER | 1 | ContentCover 覆盖/恢复 | `navigation_declaration.h:280` |
| APP_STATE | 2 | 应用前台/后台切换 | `navigation_declaration.h:281` |

### NavDestinationActiveReason

| 常量 | 值 | 说明 | 来源 |
|------|-----|------|------|
| TRANSITION | 0 | push/pop 转场 | `navigation_declaration.h:270` |
| CONTENT_COVER | 1 | ContentCover 覆盖/恢复 | `navigation_declaration.h:271` |
| SHEET | 2 | 半模态覆盖/恢复 | `navigation_declaration.h:272` |
| DIALOG | 3 | 弹窗覆盖/恢复 | `navigation_declaration.h:273` |
| OVERLAY | 4 | Overlay 覆盖/恢复 | `navigation_declaration.h:274` |
| APP_STATE_CHANGE | 5 | 应用前台/后台切换 | `navigation_declaration.h:275` |

### NavDestLifecycleReason

| 字段 | 类型 | 说明 | 来源 |
|------|------|------|------|
| activeReason | NavDestinationActiveReason | 激活/非激活原因 | `navigation_declaration.h:285` |
| visibilityChangeReason | NavDestVisibilityChangeReason | 可见性变化原因 | `navigation_declaration.h:286` |

> NavDestLifecycleReason 为 union 类型（`navigation_declaration.h:284-291`），根据 lifecycle 类型选择使用 activeReason 或 visibilityChangeReason。

---

## 回调类型定义

| 类型名 | 定义 | 说明 | 来源 |
|--------|------|------|------|
| NavDestinationOnNewParamCallback | std::function\<void(napi_value param)\> | onNewParam 动态版回调 | `navigation_declaration.h:346` |
| NavDestinationSaveStateCallback | std::function\<std::string()\> | onSaveState 回调，返回序列化状态字符串 | `navigation_declaration.h:347` |
| NavDestinationRestoreStateCallback | std::function\<void(const std::string& state)\> | onRestoreState 回调，接收序列化状态字符串 | `navigation_declaration.h:348` |
| OnStateChangeEvent | std::function\<void(bool)\> | onStateChange 回调（activated 状态） | `navdestination_event_hub.h:29` |

---

## API 变更分析

### API 清单

| API 签名 | 类型 | @since | 开放范围 | 功能描述 |
|----------|------|--------|----------|----------|
| `onShown(callback: (reason: VisibilityChangeReason) => void): NavDestinationAttribute` | Public | API 10, reason 参数 API 21 | Public | 注册可见回调 |
| `onHidden(callback: (reason: VisibilityChangeReason) => void): NavDestinationAttribute` | Public | API 10, reason 参数 API 21 | Public | 注册不可见回调 |
| `onBackPressed(callback: () => boolean): NavDestinationAttribute` | Public | API 10 | Public | 注册返回拦截回调 |
| `onResult(callback?: (info: ESObject) => void): NavDestinationAttribute` | Public | API 15 | Public | 注册弹出结果回调 |
| `onReady(callback: (context: NavDestinationContext) => void): NavDestinationAttribute` | Public | API 11 | Public | 注册就绪回调 |
| `onWillAppear(callback: () => void): NavDestinationAttribute` | Public | API 12 | Public | 注册即将出现回调 |
| `onWillDisappear(callback: () => void): NavDestinationAttribute` | Public | API 12 | Public | 注册即将消失回调 |
| `onWillShow(callback: () => void): NavDestinationAttribute` | Public | API 12 | Public | 注册即将显示回调 |
| `onWillHide(callback: () => void): NavDestinationAttribute` | Public | API 12 | Public | 注册即将隐藏回调 |
| `onActive(callback?: (reason: NavDestinationActiveReason) => void): NavDestinationAttribute` | Public | API 17 | Public | 注册激活回调 |
| `onInactive(callback?: (reason: NavDestinationActiveReason) => void): NavDestinationAttribute` | Public | API 17 | Public | 注册非激活回调 |
| `onSaveState(callback?: () => Record<string, Object> \| null): NavDestinationAttribute` | Public | API 26 | Public | 注册状态保存回调 |
| `onRestoreState(callback?: (state: Record<string, Object> \| null) => void): NavDestinationAttribute` | Public | API 26 | Public | 注册状态恢复回调 |
| `onNewParam(callback?: (param: ESObject) => void): NavDestinationAttribute` | Public | API 19 | Public | 注册参数更新回调 |

### VisibilityChangeReason 枚举

| 常量 | 值 | @since |
|------|-----|--------|
| TRANSITION | 0 | API 10 |
| CONTENT_COVER | 1 | API 10 |
| APP_STATE | 2 | API 21 |

### NavDestinationActiveReason 枚举

| 常量 | 值 | @since |
|------|-----|--------|
| TRANSITION | 0 | API 17 |
| CONTENT_COVER | 1 | API 17 |
| SHEET | 2 | API 17 |
| DIALOG | 3 | API 17 |
| OVERLAY | 4 | API 17 |
| APP_STATE_CHANGE | 5 | API 17 |

### NavDestinationContext 属性

| 属性 | 类型 | 说明 | 来源 |
|------|------|------|------|
| pathInfo | NavPathInfo | 路由信息 | `navdestination_context.h:103-106` |
| pathStack | NavigationStack | 路由栈 | `navdestination_context.h:113-116` |
| navDestinationId | uint64_t | NavDestination 标识 | `navdestination_context.h:138-141` |
| mode | NavDestinationMode | NavDestination 模式 | `navdestination_context.h:163-166` |
| index | int32_t | 路由栈索引 | `navdestination_context.h:118-126` |
| preIndex | int32_t | 前一个路由栈索引 | `navdestination_context.h:128-136` |
| uniqueId | int32_t | 节点唯一标识 | `navdestination_context.h:168-176` |

---

## 兼容性声明

| API 版本 | 行为差异 | 影响 | 迁移指导 |
|----------|----------|------|----------|
| API 10 → 11 | onReady 新增 | NavDestinationContext 就绪回调 | 无需迁移 |
| API 10 → 12 | onWillAppear/onWillDisappear/onWillShow/onWillHide 新增 | 精细化生命周期回调 | 无需迁移 |
| API 10 → 15 | onResult 新增 | 弹出结果回调 | 无需迁移 |
| API 10 → 17 | onActive/onInactive 新增；NavDestinationActiveReason 新增 | 激活/非激活回调 | 无需迁移 |
| API 10 → 21 | onShown/onHidden 回调参数 VisibilityChangeReason 新增 APP_STATE | 回调参数类型扩展 | 回调签名兼容，仅需处理新增枚举值 |
| API 10 → 19 | onNewParam 新增 | 单例模式参数更新回调 | 无需迁移 |
| API 10 → 26 | onSaveState/onRestoreState 新增 | 自定义状态保存/恢复 | 无需迁移 |

---

## 架构约束

| 约束 | 描述 |
|------|------|
| 事件回调存储 | NavDestinationEventHub 继承 NavBarEventHub（`navdestination_event_hub.h:31`），存储所有生命周期回调字段（`navdestination_event_hub.h:246-258`），NavDestinationPattern 在状态变化时通过 eventHub 触发回调 |
| 回调线程 | 所有事件回调在 UI 线程执行；FireOnAppear 中有 AddNavigationUpdateCallback 机制确保回调在 attach 后执行（`navdestination_event_hub.cpp:182-194`） |
| 状态追踪 | NavDestinationEventHub 维护 state_ 字段（`navdestination_event_hub.h:263`），每次生命周期回调触发更新 state 并通过 UIObserverHandler.NotifyNavigationStateChange 通知 UIObserver（`observer_handler.h:214`） |
| 生命周期触发链 | NavigationPattern.NotifyDestinationLifecycle 为生命周期触发入口（`navigation_pattern.cpp:5096-5144`），根据 lifecycle 类型分发到具体 Fire 方法 |
| 多线程安全 | NavDestinationPattern 提供 OnAttachToMainTreeMultiThread/OnDetachFromMainTreeMultiThread（`navdestination_pattern_multi_thread.cpp:33-81`），在多线程场景下触发生命周期 |
| onResult 存储机制 | onResult 通过 SetOnPop 将回调存储在 JSNavPathInfo.navDestinationPopCallback_（`js_navdestination_context.h:68-71`），而非 NavDestinationEventHub |
| onResult/onNewParam 双版本 | onNewParam 和 onPop 有动态版（napi_value）和静态版（NavPathInfo）两种回调路径（`navdestination_event_hub.h:192-214`） |
| 状态保存调用链 | FireOnHiddenEvent 结尾调用 FireOnSaveState（`navdestination_event_hub.cpp:146`）；FireOnWillHide 结尾调用 FireAutoSave（`navdestination_event_hub.cpp:241`） |
| 返回拦截优先级 | overlay 优先于用户 onBackPressed（`navdestination_pattern.cpp:476-483` OverlayOnBackPressed 先检查） |

---

## 非功能性需求

| 维度 | 要求 |
|------|------|
| 性能 | 生命周期回调注册/触发无额外开销，回调直接在 NavDestinationPattern/NavigationPattern 层触发；FireOnShownEvent 包含 NavigationManager.SequentialRestoreOnShown 检查（`navdestination_event_hub.cpp:116`） |
| 可调试性 | 所有 Fire 方法包含 TAG_LOGI 日志输出（如 `navdestination_event_hub.cpp:84-86`、`navdestination_event_hub.cpp:125-127`），日志包含 name/navDestinationId/navigationId |
| 可观测性 | NavDestinationState 变化通过 UIObserverHandler.NotifyNavigationStateChange 通知 UIObserver，支持路由状态监听 |

---

## 多设备适配声明

| 设备类型 | 行为差异 | 规格/约束 | 验证方式 | 证据 |
|----------|----------|-----------|----------|------|
| 手机 | NavDestination 生命周期在 Stack 模式下 push/pop 触发 | Stack 模式标准生命周期 | 单元测试 | — |
| 平板 | NavDestination 在 Split 模式下 onActive/onInactive 触发；forceSplit 场景 homeDest 生命周期特殊处理 | Split 模式双页生命周期 | 单元测试 | — |
| 折叠屏 | NavDestination 在 Auto 模式折叠/展开时触发 onShown/onHidden/onActive/onInactive | Auto 模式动态切换 | 单元测试 | — |

---

## 全局特性影响

| 影响维度 | 说明 |
|----------|------|
| UIObserver 体系 | NavDestinationState 变化通过 UIObserverHandler.NotifyNavigationStateChange 通知，参与全局 UI 状态观测 |
| Navigation 生命周期链 | NavDestination 生命周期由 NavigationPattern.NotifyDestinationLifecycle 统一调度，与 Navigation 转场动画协同 |
| 状态保存恢复体系 | onSaveState/onRestoreState 参与 NavigationStack 的状态持久化机制 |
| NavDestinationContext 体系 | onReady 提供 NavDestinationContext 对象，与应用层 NavDestination 交互 API（如 pathStack 操作）协同 |
| NavDestinationEventHub 继承 | NavDestinationEventHub 继承 NavBarEventHub（`navdestination_event_hub.h:31`），共享 onAppear/onDisappear 等基础事件 |

---

## Spec 自审清单

- [x] 所有 US 以 "作为/我想要/以便" 格式描述
- [x] 所有 AC 编号格式正确（AC-X.Y），且在验收追溯中引用
- [x] 验证映射覆盖全部 AC，每个 AC 至少有一种验证手段
- [x] 规则编号连续且可追溯到源码
- [x] API 变更分析基于真实 SDK 定义
- [x] 兼容性声明标注 API 版本差异
- [x] 所有源码引用包含 file 信息
- [x] 无 TBD/TODO 占位符
- [x] 变更范围 Delta 明确标注为已有实现补录

---

## context-references

### 源码文件

| 文件 | 说明 |
|------|------|
| `frameworks/core/components_ng/pattern/navrouter/navdestination_event_hub.h:31-264` | 所有生命周期回调字段定义与存储 |
| `frameworks/core/components_ng/pattern/navrouter/navdestination_event_hub.cpp:25-301` | 所有生命周期回调 Fire 方法实现 |
| `frameworks/core/components_ng/pattern/navrouter/navdestination_pattern.cpp:476-483` | OverlayOnBackPressed overlay 优先处理 |
| `frameworks/core/components_ng/pattern/navrouter/navdestination_pattern.cpp:574-592` | OnDetachFromMainTree 触发 ON_WILL_DISAPPEAR |
| `frameworks/core/components_ng/pattern/navrouter/navdestination_pattern.cpp:1153-1163` | CallSavedStateToJS 状态存储 |
| `frameworks/core/components_ng/pattern/navrouter/navdestination_pattern_multi_thread.cpp:33-81` | 多线程场景生命周期触发 |
| `frameworks/core/components_ng/pattern/navrouter/navdestination_context.h:30-201` | NavPathInfo / NavDestinationContext 定义 |
| `frameworks/core/components_ng/base/observer_handler.h:38-51` | NavDestinationState 枚举定义 |
| `frameworks/core/components_ng/pattern/navigation/navigation_declaration.h:256-291` | NavDestinationLifecycle / NavDestinationActiveReason / NavDestVisibilityChangeReason 枚举定义 |
| `frameworks/core/components_ng/pattern/navigation/navigation_declaration.h:346-348` | 回调类型定义 |
| `frameworks/core/components_ng/pattern/navigation/navigation_pattern.cpp:5096-5195` | NotifyDestinationLifecycle / FireOnShowLifecycle / FireOnActiveLifecycle / FireOnInactiveLifecycle |
| `frameworks/core/components_ng/pattern/navigation/navigation_pattern.cpp:2350-2394` | FireNavDestinationStateChange |
| `frameworks/core/components_ng/pattern/navigation/navigation_pattern.cpp:2566-2592` | FireNavigationLifecycleChange |
| `frameworks/core/components_ng/pattern/navigation/navigation_pattern.cpp:6155-6180` | FireNavigationLifecycle (active/inactive 递归分发) |
| `frameworks/core/components_ng/pattern/navigation/navigation_pattern.cpp:6250-6269` | FireOnNewParam |
| `frameworks/core/components_ng/pattern/navigation/navigation_group_node.cpp:644-698` | onBackPressed 事件处理 |
| `frameworks/core/components_ng/pattern/navrouter/navdestination_group_node.cpp:265-287` | ProcessShallowBuilder / onReady 触发 |
| `frameworks/core/components_ng/pattern/navrouter/navdestination_model_ng.cpp:1874-1889` | SetOnPop (onResult) 实现 |
| `frameworks/bridge/declarative_frontend/jsview/js_navdestination.cpp:920-998` | JSNavDestination 静态方法注册与 onResult 实现 |
| `frameworks/bridge/declarative_frontend/jsview/js_navdestination_context.h:37-99` | JSNavPathInfo / navDestinationPopCallback_ |
| `frameworks/bridge/declarative_frontend/engine/jsi/nativeModule/arkts_native_nav_destination_bridge.cpp:1339-1409` | ArkTS NavDestination onResult/onNewParam 桥接 |
| `frameworks/core/components_ng/pattern/navrouter/navdestination_model.h:36-140` | NavDestinationModel 接口定义 |

### 测试文件

| 文件 | 说明 |
|------|------|
| `test/unittest/core/pattern/navrouter/` | NavDestination 单元测试目录 |
| `test/unittest/core/pattern/navigation/` | Navigation 单元测试目录 |
