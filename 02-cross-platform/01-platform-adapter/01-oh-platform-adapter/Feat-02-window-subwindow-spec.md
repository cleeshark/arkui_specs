# 特性规格

## 概述

| 属性 | 值 |
|------|-----|
| 特性名称 | 窗口与子窗口适配 |
| 特性编号 | Func-02-01-01-Feat-02 |
| 所属 Epic | 跨平台适配层 |
| 优先级 | P1 |
| 目标版本 | API 9+ |
| SIG 归属 | ArkUI SIG |
| 状态 | Baselined |
| 复杂度 | 关键 |

## 本次变更范围（Delta）

> 全新特性补录，无存量变更。本节跳过。

## 输入文档

- 源码路径：`adapter/ohos/entrance/subwindow/` + `adapter/ohos/entrance/window/` + `frameworks/core/components_ng/render/adapter/rosen_window.h`
- 设计文档：`02-cross-platform/01-platform-adapter/01-oh-platform-adapter/design.md`
- 无独立 requirement.md（已有实现补录）

> 需求基线、不涉及项、受影响子系统与仓库详见 proposal.md，本文档不重复摘录。

## 用户故事

### US-1: RosenWindow 主窗口生命周期与 VSync

作为一个 ACE 引擎开发者，我希望 NG::RosenWindow 正确管理 OHOS Rosen Window 的生命周期，包括初始化、VSync 回调、前后台切换和超时恢复，以便 NG 渲染管线能通过 Rosen 窗口获得稳定的帧驱动。

| AC编号 | 验收标准 | 类型 |
|--------|----------|------|
| AC-1.1 | WHEN RosenWindow 构造 THEN 从 rsWindow_ 获取或创建 RSUIDirector，设置 RSSurfaceNode，配置 UI task runner | 正常 |
| AC-1.2 | WHEN RosenWindow::Init 被调用 THEN 设置 RequestVsyncCallback 为 RequestFrame()，注册子窗口到多实例管理 | 正常 |
| AC-1.3 | WHEN RequestFrame 被调用 THEN 通过 rsWindow_->RequestVsync(vsyncCallback_) 请求 VSync，并提交 VSync 超时 DFX 任务 | 正常 |
| AC-1.4 | WHEN OnVsync(timestamp, frameCount) 被调用 THEN 分发 VSync 到 Window::OnVsync()，移除超时 DFX 任务，post idle task 51ms | 正常 |
| AC-1.5 | WHEN VSync 超时 3s THEN DFX 报告超时事件；RecoverExecutor 500ms 后 ForceFlushVsync(UINT64_MAX frameCount) 恢复管线 | 异常 |
| AC-1.6 | WHEN OnShow 被调用 THEN rsUIDirector_->GoForeground，并处理 detached 节点的 GoResume/GoStop | 正常 |
| AC-1.7 | WHEN OnHide 被调用 THEN rsUIDirector_->GoBackground | 正常 |
| AC-1.8 | WHEN NotifyWindowAttachStateChange(true) 被调用 THEN GoResume 所有 detached 节点 | 正常 |
| AC-1.9 | WHEN NotifyWindowAttachStateChange(false) 被调用 THEN 对 hidden + detached 窗口延迟 1s GoStop | 正常 |
| AC-1.10 | WHEN SetUiDvsyncSwitch(true) THEN 在 rsWindow_ 启用 DVSync | 正常 |
| AC-1.11 | WHEN SetDVSyncUpdate(time) THEN 在 rsUIDirector_ 设置 DVSync 更新时间 | 正常 |
| AC-1.12 | WHEN Destroy 被调用 THEN 置空 rsWindow_，注销子窗口，脱离 RSUIContext，销毁 rsUIDirector_（若 self-owned） | 正常 |
| AC-1.13 | WHEN SetRootFrameNode 被调用 THEN 将 NG FrameNode 设置为 RSRootNode 到 rsUIDirector_ | 正常 |
| AC-1.14 | WHEN FlushFrameRate(rate, expected, type) 被调用 THEN 委托到 rsWindow_->FlushFrameRate | 正常 |
| AC-1.15 | WHEN FlushTasks(callback) 被调用 THEN rsUIDirector_->SendMessages()，可选 callback | 正常 |

### US-2: RSWindow 旧管线兼容

作为一个 ACE 引擎开发者，我希望 Platform::RSWindow 为旧渲染管线提供独立的 VSync 线程回调机制，以便旧管线组件也能获得帧驱动。

| AC编号 | 验收标准 | 类型 |
|--------|----------|------|
| AC-2.1 | WHEN RSWindow::RequestFrame 被调用 THEN 启动独立 VSync 线程（若未启动），向 vsyncRequests_ SemQueue 推送 true | 正常 |
| AC-2.2 | WHEN VsyncThreadMain 运行 THEN 从 vsyncRequests_ 取出请求，swap pendingVsyncCallbacks_，对每个回调 fire(steady_clock timestamp, frameCount=0) | 正常 |
| AC-2.3 | WHEN RegisterVsyncCallback(callback) 被调用 THEN 将回调 swap-transfer 到 pendingVsyncCallbacks_（在 VSync 线程中取用） | 正常 |
| AC-2.4 | WHEN Destroy 被调用 THEN 向 vsyncRequests_ 推送 false 终止线程，join 线程 | 正常 |
| AC-2.5 | WHEN PlatformWindow::Create(AceView*) 被调用 THEN 返回 std::make_unique<RSWindow>() | 正常 |

### US-3: SubwindowOhos 子窗口管理

作为一个 ACE 引擎开发者，我希望 SubwindowOhos 正确创建和管理 OHOS 子窗口及其 AceContainer 子容器，支持多种弹窗类型和 VSync 共享。

| AC编号 | 验收标准 | 类型 |
|--------|----------|------|
| AC-3.1 | WHEN InitContainer 被调用 THEN 创建 Rosen::Window（根据 type 选择 APP_SUB_WINDOW/SYSTEM_TOAST/SYSTEM_FLOAT 等），注册 MenuWindowSceneListener，初始化 AceContainer 子容器 + AceViewOhos，SetSubWindowVsyncListener 共享父管线 VSync | 正常 |
| AC-3.2 | WHEN ShowMenuNG 被调用 THEN 在子窗口中显示菜单 | 正常 |
| AC-3.3 | WHEN ShowPopupNG 被调用 THEN 在子窗口中显示 Popup | 正常 |
| AC-3.4 | WHEN ShowTipsNG 被调用 THEN 在子窗口中显示 Tips 提示 | 正常 |
| AC-3.5 | WHEN ShowDialogNG 被调用 THEN 在子窗口中显示 Dialog | 正常 |
| AC-3.6 | WHEN ShowToast 被调用 THEN 在子窗口中显示 Toast | 正常 |
| AC-3.7 | WHEN ShowBindSheetNG 被调用 THEN 在子窗口中显示 bindSheet 半模态 | 正常 |
| AC-3.8 | WHEN ShowSelectOverlay 被调用 THEN 在子窗口中显示文本选择覆盖层 | 正常 |
| AC-3.9 | WHEN SetSubWindowVsyncListener 被调用 THEN 子管线共享父管线的 VSync 监听器，子窗口不独立请求 VSync | 正常 |
| AC-3.10 | WHEN ResizeWindow 被调用 THEN 调整子窗口尺寸 | 正常 |
| AC-3.11 | WHEN ResizeWindowForFoldStatus 被调用 THEN 根据折叠状态调整子窗口尺寸 | 正常 |
| AC-3.12 | WHEN GetParentWindowRect 被调用 THEN 返回父窗口的 Rect | 正常 |
| AC-3.13 | WHEN SetWindowTouchable(true/false) 被调用 THEN 设置子窗口是否可触摸 | 正常 |
| AC-3.14 | WHEN SetFollowParentWindowLayoutEnabled 被调用 THEN 设置子窗口跟随父窗口布局 | 正常 |
| AC-3.15 | WHEN SetHotAreas/DeleteHotAreas 被调用 THEN 在子窗口上注册/删除触摸热区 | 正常 |
| AC-3.16 | WHEN DestroyWindow 被调用 THEN 销毁子窗口 | 正常 |
| AC-3.17 | WHEN InitContainer 创建 UIExtension 类型子窗口 THEN 设置 UIExtension 标志和 host 窗口 ID | 边界 |
| AC-3.18 | WHEN ShowToastStatic/ShowDialogStatic 被调用（ArkTS 1.2 静态方法） THEN 使用静态路径创建弹窗 | 正常 |

### US-4: SubwindowManager 子窗口注册中心

作为一个 ACE 引擎开发者，我希望 SubwindowManager 作为全局单例管理容器-窗口映射和子窗口注册，并提供弹窗调度入口。

| AC编号 | 验收标准 | 类型 |
|--------|----------|------|
| AC-4.1 | WHEN AddContainerId(windowId, containerId) 被调用 THEN 建立窗口ID到容器ID的映射 | 正常 |
| AC-4.2 | WHEN GetContainerId(windowId) 被调用 THEN 返回对应的容器ID | 正常 |
| AC-4.3 | WHEN AddSubwindow(instanceId, type, subwindow) 被调用 THEN 按多维度键(SubwindowKey) 注册子窗口 | 正常 |
| AC-4.4 | WHEN GetOrCreateSubWindow 被调用 THEN 查找已注册子窗口或创建新子窗口 | 正常 |
| AC-4.5 | WHEN ShowMenuNG/ShowPopupNG/ShowDialogNG/ShowToast/ShowBindSheetNG 等调度方法被调用 THEN 查找/创建对应类型子窗口并委托执行 | 正常 |
| AC-4.6 | WHEN ResizeWindowForFoldStatus 被调用 THEN 对所有相关子窗口执行折叠适配重配 | 正常 |
| AC-4.7 | WHEN IsFreeMultiWindow 被调用 THEN 查询指定实例是否支持自由多窗 | 正常 |

### US-5: 特殊窗口适配

作为一个 ACE 引擎开发者，我希望 DragWindowOhos、FoldableWindowOhos 和 WindowExtensionConnection 适配器各自正确桥接 OHOS 特殊窗口能力。

| AC编号 | 验收标准 | 类型 |
|--------|----------|------|
| AC-5.1 | WHEN DragWindowOhos::MoveTo(x,y) 被调用 THEN 更新拖拽窗口位置 | 正常 |
| AC-5.2 | WHEN DragWindowOhos::DrawPixelMap 被调用 THEN 将 PixelMap 绘制为拖拽预览 | 正常 |
| AC-5.3 | WHEN DragWindowOhos::DrawFrameNode 被调用 THEN 将 NG FrameNode 绘制为拖拽预览 | 正常 |
| AC-5.4 | WHEN DragWindowOhos::DrawImage(drawingImage) 被调用 THEN 将 Drawing API 图像绘制为拖拽预览 | 正常 |
| AC-5.5 | WHEN DragWindowOhos::DrawText/DrawTextNG 被调用 THEN 将文本段落绘制为拖拽预览 | 正常 |
| AC-5.6 | WHEN DragWindowOhos::FlushImplicitTransaction 被调用 THEN 冲刷 RS 隐式事务 | 正常 |
| AC-5.7 | WHEN DragWindowOhos::Destroy 被调用 THEN 销毁拖拽窗口 | 正常 |
| AC-5.8 | WHEN FoldableWindowOhos::IsFoldExpand 被调用 THEN 查询 DisplayManager 返回折叠展开状态 | 正常 |
| AC-5.9 | WHEN WindowExtensionConnectionAdapterOhos::ConnectExtension 被调用 THEN 通过 Rosen::WindowExtensionConnection 连接 UI 扩展（旧版：传 want+rect+node+windowId） | 正常 |
| AC-5.10 | WHEN WindowExtensionConnectionAdapterOhosNG::ConnectExtension 被调用 THEN 通过 Rosen::WindowExtensionConnection 连接 NG UI 扩展（新版：传 node+windowId） | 正常 |
| AC-5.11 | WHEN 旧/新版 WindowExtensionConnection UpdateRect/Show/Hide 被调用 THEN 更新扩展窗口矩形/显示/隐藏 | 正常 |

### US-6: 支撑工具类

作为一个 ACE 引擎开发者，我希望 RsAdapter/AceRosenSyncTask/WindowUtils 等工具类正确提供 RS 初始化、同步任务和窗口方向转换等支撑功能。

| AC编号 | 验收标准 | 类型 |
|--------|----------|------|
| AC-6.1 | WHEN RsUIDirectorInit 被调用 THEN 从 Window 获取 RSUIDirector，设置 SurfaceNode 和 cacheDir | 正常 |
| AC-6.2 | WHEN RsFlushImplicitTransaction 被调用 THEN 冲刷 RS 隐式事务 | 正常 |
| AC-6.3 | WHEN AceRosenSyncTask::Process 被调用 THEN 执行存储的 task_ 函数 | 正常 |
| AC-6.4 | WHEN WindowUtils::GetDeviceOrientation 被调用 THEN 将 Rosen DisplayOrientation 转换为 DeviceOrientation | 正常 |

### US-7: VSync 超时恢复机制

作为一个 ACE 引擎开发者，我希望 RosenWindow 在 VSync 超时时通过 RecoverExecutor 实现管线恢复，避免渲染管线永久卡顿。

| AC编号 | 验收标准 | 类型 |
|--------|----------|------|
| AC-7.1 | WHEN RequestFrame 后 3s 未收到 OnVsync THEN DFX 报告 VSync 超时事件 | 异常 |
| AC-7.2 | WHEN RecoverExecutor 触发 THEN 500ms 后调用 ForceFlushVsync(UINT64_MAX frameCount) 强制恢复管线 | 异常 |
| AC-7.3 | WHEN ForceFlushVsync 被调用 THEN 生成一个 fake VSync 回调驱动管线继续运行 | 正常 |

## 验收追溯

| AC | 关联规则 | 关联 Task | 验证方式 | 证据 |
|----|----------|-----------|----------|------|
| AC-1.1~1.15 | R-1~15 | TASK-F02-01 | 单测 | rosen_window.cpp |
| AC-2.1~2.5 | R-16~20 | TASK-F02-02 | 单测 | rosen_window.cpp(旧) |
| AC-3.1~3.18 | R-21~38 | TASK-F02-03 | 单测+集成测试 | subwindow_ohos.cpp |
| AC-4.1~4.7 | R-39~45 | TASK-F02-04 | 单测 | subwindow_manager.cpp |
| AC-5.1~5.11 | R-46~56 | TASK-F02-05 | 单测 | drag_window_ohos.cpp 等 |
| AC-6.1~6.4 | R-57~60 | TASK-F02-06 | 单测 | rs_adapter.cpp 等 |
| AC-7.1~7.3 | R-61~63 | TASK-F02-07 | 集成测试 | rosen_window.cpp |

## 规则定义

| 规则ID | 类型 | 触发条件 | 预期行为 | 边界/约束 | 关联AC |
|--------|------|----------|----------|-----------|--------|
| R-1 | 行为 | RosenWindow 构造 | 从 rsWindow_ 获取 RSUIDirector，设置 RSSurfaceNode | rsUIDirector_ 可为 self-owned（窗口创建时）或外部传入 | AC-1.1 |
| R-2 | 行为 | RosenWindow::Init | 设置 RequestVsyncCallback→RequestFrame() | VSync 回调闭包绑定到实例 | AC-1.2 |
| R-3 | 行为 | RequestFrame 调用 | rsWindow_->RequestVsync(vsyncCallback_) + DFX 超时任务 | DFX 超时任务 3s 阈值 | AC-1.3 |
| R-4 | 行为 | OnVsync 回调 | 分发到 Window::OnVsync() + 移除超时任务 + post idle 51ms | idle task 用于延迟清理 | AC-1.4 |
| R-5 | 异常 | VSync 超时 3s | DFX 报告 + RecoverExecutor 500ms ForceFlushVsync | UINT64_MAX frameCount 表示 fake VSync | AC-1.5 |
| R-6 | 行为 | OnShow 调用 | rsUIDirector_->GoForeground + detached 节点 GoResume/GoStop | GoResume 仅在 re-attached 时 | AC-1.6 |
| R-7 | 行为 | OnHide 调用 | rsUIDirector_->GoBackground | 无 detached 处理 | AC-1.7 |
| R-8 | 行为 | NotifyWindowAttachStateChange(true) | GoResume 所有 detached 节点 | 仅 re-attached 场景 | AC-1.8 |
| R-9 | 行为 | NotifyWindowAttachStateChange(false) | hidden+detached 窗口延迟 1s GoStop | 延迟避免刚 detach 就 stop 的竞争 | AC-1.9 |
| R-10 | 行为 | SetUiDvsyncSwitch(true) | rsWindow_ 启用 DVSync | DVSync 减少不必要的全帧刷新 | AC-1.10 |
| R-11 | 行为 | SetDVSyncUpdate(time) | rsUIDirector_ 设置 DVSync 更新 | DVSync time 为纳秒时间戳 | AC-1.11 |
| R-12 | 行为 | Destroy 调用 | 置空 rsWindow_，注销子窗口，脱离 RSUIContext | rsUIDirector_ 仅在 self-owned 时销毁 | AC-1.12 |
| R-13 | 行为 | SetRootFrameNode | 将 FrameNode 设为 RSRootNode 到 rsUIDirector_ | RSRootNode 是 RS 管线根节点 | AC-1.13 |
| R-14 | 行为 | FlushFrameRate | rsWindow_->FlushFrameRate(rate, expected, type) | rate/expected/type 三参数 | AC-1.14 |
| R-15 | 行为 | FlushTasks | rsUIDirector_->SendMessages() | 可选 callback 用于同步等待 | AC-1.15 |
| R-16 | 行为 | RSWindow::RequestFrame | 启动 VSync 线程 + push true 到 vsyncRequests_ | VSync 线程为 detachable | AC-2.1 |
| R-17 | 行为 | VsyncThreadMain 循环 | 取出请求 → sleep 1ms → swap callbacks → fire each | 1ms sleep 避免忙等待 | AC-2.2 |
| R-18 | 行为 | RegisterVsyncCallback | swap-transfer 到 pendingVsyncCallbacks_ | swap 保证线程安全 | AC-2.3 |
| R-19 | 行为 | RSWindow::Destroy | push false → join 线程 | false 信号终止线程循环 | AC-2.4 |
| R-20 | 行为 | PlatformWindow::Create(AceView*) | 返回 RSWindow | 工厂静态方法 | AC-2.5 |
| R-21 | 行为 | InitContainer 创建子窗口 | 创建 Rosen::Window + 注册 SceneListener + 初始化 AceContainer + AceViewOhos + VSync 共享 | WindowType 由弹窗类型决定 | AC-3.1 |
| R-22 | 行为 | ShowMenuNG | 在子窗口中显示菜单 | 菜单子窗口类型 | AC-3.2 |
| R-23 | 行为 | ShowPopupNG | 在子窗口中显示 Popup | Popup 子窗口类型 | AC-3.3 |
| R-24 | 行为 | ShowTipsNG | 在子窗口中显示 Tips | Tips 子窗口类型 | AC-3.4 |
| R-25 | 行为 | ShowDialogNG | 在子窗口中显示 Dialog | Dialog 子窗口类型 | AC-3.5 |
| R-26 | 行为 | ShowToast | 在子窗口中显示 Toast | Toast 子窗口类型 | AC-3.6 |
| R-27 | 行为 | ShowBindSheetNG | 在子窗口中显示半模态 | Sheet 子窗口类型 | AC-3.7 |
| R-28 | 行为 | ShowSelectOverlay | 在子窗口中显示选择覆盖层 | SelectOverlay 子窗口类型 | AC-3.8 |
| R-29 | 行为 | SetSubWindowVsyncListener | 子管线共享父管线 VSync 监听器 | 子窗口不独立请求 VSync | AC-3.9 |
| R-30 | 行为 | ResizeWindow | 调整子窗口尺寸 | 新尺寸由弹窗内容决定 | AC-3.10 |
| R-31 | 行为 | ResizeWindowForFoldStatus | 根据折叠状态调整 | 折叠屏适配 | AC-3.11 |
| R-32 | 行为 | GetParentWindowRect | 返回父窗口 Rect | 用于子窗口定位 | AC-3.12 |
| R-33 | 行为 | SetWindowTouchable | 设置子窗口触摸开关 | true→可触摸, false→仅显示 | AC-3.13 |
| R-34 | 行为 | SetFollowParentWindowLayoutEnabled | 子窗口跟随父窗口布局 | 跟随包括位置和大小 | AC-3.14 |
| R-35 | 行为 | SetHotAreas/DeleteHotAreas | 注册/删除触摸热区 | 热区为 Rect 数组 | AC-3.15 |
| R-36 | 行为 | DestroyWindow | 销毁子窗口 | 销毁后子容器也清理 | AC-3.16 |
| R-37 | 边界 | UIExtension 类型子窗口 InitContainer | 设置 UIExtension 标志和 host 窗口 ID | UIExtension 子窗口有特殊生命周期 | AC-3.17 |
| R-38 | 行为 | ShowToastStatic/ShowDialogStatic | ArkTS 1.2 静态路径创建弹窗 | 静态方法不需要实例 | AC-3.18 |
| R-39 | 行为 | AddContainerId | 建立窗口ID→容器ID映射 | 双向映射 | AC-4.1 |
| R-40 | 行为 | GetContainerId | 返回容器ID | 反向查询用 reverseContainerMap_ | AC-4.2 |
| R-41 | 行为 | AddSubwindow | 按多维度键注册 | SubwindowKey = instanceId+displayId+windowType+foldStatus+nodeId | AC-4.3 |
| R-42 | 行为 | GetOrCreateSubWindow | 查找或创建 | 按需创建避免空子窗口浪费 | AC-4.4 |
| R-43 | 行为 | Show*NG 调度方法 | 查找/创建子窗口并委托 | 每种弹窗类型有独立调度入口 | AC-4.5 |
| R-44 | 行为 | ResizeWindowForFoldStatus | 对所有相关子窗口重配 | 折叠状态变化时批量更新 | AC-4.6 |
| R-45 | 行为 | IsFreeMultiWindow | 查询自由多窗状态 | 实例级配置 | AC-4.7 |
| R-46 | 行为 | DragWindowOhos::MoveTo | 更新拖拽窗口位置 | 位置为屏幕坐标 | AC-5.1 |
| R-47 | 行为 | DragWindowOhos::DrawPixelMap | PixelMap→拖拽预览 | PixelMap 由组件截图生成 | AC-5.2 |
| R-48 | 行为 | DragWindowOhos::DrawFrameNode | FrameNode→拖拽预览 | NG 管线支持 | AC-5.3 |
| R-49 | 行为 | DragWindowOhos::DrawImage | DrawingImage→拖拽预览 | Drawing API 图像 | AC-5.4 |
| R-50 | 行为 | DragWindowOhos::DrawText/DrawTextNG | 文本→拖拽预览 | Paragraph 绘制 | AC-5.5 |
| R-51 | 行为 | DragWindowOhos::FlushImplicitTransaction | 冲刷 RS 隐式事务 | 确保拖拽预览立即可见 | AC-5.6 |
| R-52 | 行为 | DragWindowOhos::Destroy | 销毁拖拽窗口 | 销毁后 rsUiDirector_ 也清理 | AC-5.7 |
| R-53 | 行为 | FoldableWindowOhos::IsFoldExpand | 查询 DisplayManager | 返回当前折叠展开状态 | AC-5.8 |
| R-54 | 行为 | 旧版 ConnectExtension | 通过 Rosen::WindowExtensionConnection 连接 | 传 want+rect+node+windowId | AC-5.9 |
| R-55 | 行为 | 新版 ConnectExtension | 通过 Rosen::WindowExtensionConnection 连接 | 传 node+windowId（NG 简化签名） | AC-5.10 |
| R-56 | 行为 | UpdateRect/Show/Hide | 更新/显示/隐藏扩展窗口 | 旧新版相同接口 | AC-5.11 |
| R-57 | 行为 | RsUIDirectorInit | 从 Window 获取 RSUIDirector + 设置 SurfaceNode + cacheDir | 初始化 RS 渲染管线 | AC-6.1 |
| R-58 | 行为 | RsFlushImplicitTransaction | 冲刷 RS 隐式事务 | 用于拖拽窗口场景 | AC-6.2 |
| R-59 | 行为 | AceRosenSyncTask::Process | 执行存储的 task_ 函数 | IPC Parcel stubs (Marshalling/ReadFromParcel) | AC-6.3 |
| R-60 | 行为 | WindowUtils::GetDeviceOrientation | Rosen DisplayOrientation→DeviceOrientation | PORTRAIT/LANDSCAPE 映射 | AC-6.4 |
| R-61 | 异常 | VSync 超时 3s | DFX 报告 VSync 超时事件 | 超时计时从 RequestFrame 开始 | AC-7.1 |
| R-62 | 异常 | RecoverExecutor 触发 | 500ms 后 ForceFlushVsync(UINT64_MAX) | fake VSync 避免管线永久卡顿 | AC-7.2 |
| R-63 | 行为 | ForceFlushVsync | 生成 fake VSync 回调 | UINT64_MAX frameCount 标识 fake | AC-7.3 |

## 验证映射

| 编号 | 对应规格项 | 验证方式 | 验证重点 |
|------|------------|----------|----------|
| VM-1 | AC-1.1~1.15 RosenWindow 生命周期 | 单测 | 初始化、VSync、前后台、DVSync、Destroy |
| VM-2 | AC-2.1~2.5 RSWindow 旧管线兼容 | 单测 | VSync 线程、SemQueue、工厂 |
| VM-3 | AC-3.1~3.18 SubwindowOhos | 单测+集成测试 | 初始化链、弹窗调度、VSync共享、折叠适配 |
| VM-4 | AC-4.1~4.7 SubwindowManager | 单测 | 多维度键索引、双向映射、调度入口 |
| VM-5 | AC-5.1~5.11 特殊窗口 | 单测 | 拖拽预览4类型、折叠检测、UI扩展旧/新 |
| VM-6 | AC-6.1~6.4 工具类 | 单测 | RsAdapter、SyncTask、方向转换 |
| VM-7 | AC-7.1~7.3 VSync 超时恢复 | 集成测试 | 3s DFX报告、500ms ForceFlushVsync |

## API 变更分析

N/A，本特性为框架内部适配层，无 SDK API 变更。

## 接口规格

### 接口定义

**RosenWindow::Init**

| 属性 | 值 |
|------|-----|
| 函数签名 | `void RosenWindow::Init()` |
| 返回值 | `void` |
| 开放范围 | InnerApi |
| 错误码 | N/A |
| 关联 AC | AC-1.2 |

**参数约束**

| 参数 | 类型 | 必填 | 默认值 | 约束条件 |
|------|------|------|--------|---------|
| (无额外参数) | - | - | - | 使用构造时传入的 rsWindow_ + taskExecutor_ |

---

**SubwindowOhos::InitContainer**

| 属性 | 值 |
|------|-----|
| 函数签名 | `void SubwindowOhos::InitContainer()` |
| 返回值 | `void` |
| 开放范围 | InnerApi |
| 错误码 | N/A |
| 关联 AC | AC-3.1 |

**参数约束**

| 参数 | 类型 | 必填 | 默认值 | 约束条件 |
|------|------|------|--------|---------|
| (无额外参数，使用成员变量) | - | - | - | instanceId_、parentWindow_ 等在构造时设置 |

---

**SubwindowManager::GetOrCreateSubWindow**

| 属性 | 值 |
|------|-----|
| 函数签名 | `RefPtr<Subwindow> SubwindowManager::GetOrCreateSubWindow(int32_t instanceId)` |
| 返回值 | `RefPtr<Subwindow>` |
| 开放范围 | InnerApi |
| 错误码 | N/A |
| 关联 AC | AC-4.4 |

**参数约束**

| 参数 | 类型 | 必填 | 默认值 | 约束条件 |
|------|------|------|--------|---------|
| instanceId | int32_t | 是 | 无 | 容器实例ID |

---

**DragWindowOhos::DrawPixelMap**

| 属性 | 值 |
|------|-----|
| 函数签名 | `void DragWindowOhos::DrawPixelMap(RefPtr<PixelMap> pixelMap)` |
| 返回值 | `void` |
| 开放范围 | InnerApi |
| 错误码 | N/A |
| 关联 AC | AC-5.2 |

**参数约束**

| 参数 | 类型 | 必填 | 默认值 | 约束条件 |
|------|------|------|--------|---------|
| pixelMap | RefPtr<PixelMap> | 是 | 无 | 非空 PixelMap |

## 兼容性声明

- **已有 API 行为变更:** 否，本特性为新增框架内部适配层
- **配置文件格式变更:** 否
- **数据存储格式变更:** 否
- **最低支持版本:** API 9
- **API 版本号策略:** InnerApi，无 @since 标注

## 架构约束

| 关键约束 | 约束说明 | 影响 AC |
|----------|----------|---------|
| 双窗口适配层并存 | NG::RosenWindow (NG管线) 和 Platform::RSWindow (旧管线) 使用不同的 VSync 获取机制 | AC-1.3, AC-2.1 |
| SubwindowOhos VSync 共享 | 子管线通过 SetSubWindowVsyncListener 共享父管线 VSync，不独立请求 | AC-3.9 |
| SubwindowKey 多维度索引 | 子窗口按 instanceId+displayId+windowType+foldStatus+nodeId 五维度键索引 | AC-4.3 |
| 窗口 attach/detach 状态 | MenuWindowSceneListener 监听 attach/detach，影响 GoResume/GoStop 生命周期 | AC-1.8, AC-1.9 |
| WindowExtension 旧/新版并存 | 旧版传 want+rect+node+windowId，新版仅传 node+windowId | AC-5.9, AC-5.10 |
| VSync 超时恢复 | 3s 超时 DFX + 500ms RecoverExecutor ForceFlushVsync | AC-7.1~7.3 |

## 非功能性需求

| 类型 | 指标/阈值 | 验证方式 | 证据 |
|------|-----------|----------|------|
| 性能 | RosenWindow::Init ≤5ms | 单测计时 | rosen_window.cpp |
| 可靠性 | VSync 超时恢复 ≤500ms | 集成测试 | rosen_window.cpp |
| 内存 | 每个子窗口额外1个 Rosen::Window + 1个 AceContainer | 内存分析 | subwindow_ohos.cpp |
| 可测试性 | RecoverExecutor 可通过注入超时条件触发 | 单测 | rosen_window.cpp |

## 多设备适配声明

| 设备类型 | 行为差异 | 规格/约束 | 验证方式 | 证据 |
|----------|----------|-----------|----------|------|
| 手机 | 无差异 | - | - | - |
| 平板 | 无差异 | - | - | - |
| 折叠屏 | ResizeWindowForFoldStatus 根据折叠状态调整子窗口尺寸 | SubwindowKey 包含 foldStatus 维度 | 集成测试 | subwindow_ohos.cpp |

## 全局特性影响

| 特性 | 适用？ | 结论 | 关联场景 |
|------|--------|------|----------|
| 无障碍 | 否 | 适配层不直接影响无障碍 | N/A |
| 大字体 | 否 | 适配层不直接影响大字体 | N/A |
| 深色模式 | 否 | 适配层不直接影响深色模式 | N/A |
| 多窗口/分屏 | 是 | SubwindowManager 管理多窗口子容器映射；NotifyWindowAttachStateChange 处理窗口 attach/detach | AC-3.1, AC-1.8~1.9 |
| 多用户 | 否 | 适配层不直接影响多用户 | N/A |
| 版本升级 | 是 | 旧/新版 WindowExtensionConnection 并存，旧版逐步废弃 | AC-5.9~5.10 |
| 生态兼容 | 否 | 适配层为框架内部 | N/A |

## 行为场景（可选，Gherkin）

```gherkin
Feature: 窗口与子窗口适配
  作为 ACE 引擎开发者
  我想要 NG 渲染管线通过 Rosen Window 获得稳定帧驱动并管理子窗口弹窗
  以便组件能在 OHOS 平台上正确显示弹窗和多窗口

  Scenario: RosenWindow 初始化并请求 VSync
    Given 一个 OHOS Rosen Window 实例已创建
    When 调用 RosenWindow::Init
    Then 设置 RequestVsyncCallback 为 RequestFrame()
    And 注册子窗口到多实例管理

  Scenario: SubwindowOhos InitContainer 创建子窗口
    Given 需要创建一个 Toast 类型子窗口
    When 调用 SubwindowOhos::InitContainer
    Then 创建 Rosen::Window（WindowType=SYSTEM_TOAST）
    And 注册 MenuWindowSceneListener 监听 attach/detach
    And 初始化 AceContainer 子容器 + AceViewOhos
    And SetSubWindowVsyncListener 共享父管线 VSync

  Scenario: VSync 超时恢复
    Given RosenWindow 已初始化并 RequestFrame
    When 3s 内未收到 OnVsync 回调
    Then DFX 报告 VSync 超时事件
    And RecoverExecutor 500ms 后调用 ForceFlushVsync(UINT64_MAX)
    And 生成 fake VSync 驱动管线继续运行

  Scenario: 窗口 detach 状态变化
    Given RosenWindow 的 RSUIContext 被脱离
    When NotifyWindowAttachStateChange(false)
    Then 对 hidden + detached 窗口延迟 1s GoStop
    When NotifyWindowAttachStateChange(true)
    Then GoResume 所有 detached 节点

  Scenario: 拖拽窗口四类型预览
    Given 需要为拖拽操作创建预览窗口
    When 组件为 Image → DrawPixelMap
    When 组件为自定义 → DrawFrameNode
    When 组件为 Drawing → DrawImage
    When 组件为 Text → DrawTextNG
    Then 对应类型预览绘制到拖拽窗口
    And FlushImplicitTransaction 确保预览立即可见

  Scenario: UI扩展连接旧/新版并存
    Given 需要连接 UI Extension
    When 使用旧版 → ConnectExtension(want, rect, node, windowId)
    When 使用新版 → ConnectExtension(node, windowId)
    Then 通过 Rosen::WindowExtensionConnection 建立连接
```

## Spec 自审清单

- [x] 无"待定""TBD""TODO"等占位符
- [x] 所有 AC 使用 WHEN/THEN 格式，可独立测试
- [x] 范围边界明确（6个子能力集群，全量覆盖）
- [x] 无语义模糊表述
- [x] AC 与规则表交叉一致
- [x] 规则表每条通过 5 项质量检查

## context-references

```yaml
context-queries:
  - repo: "openharmony/ace_engine"
    query: "NG::RosenWindow 与 Platform::RSWindow 双窗口适配层的并存机制和 VSync 获取差异"
  - repo: "openharmony/ace_engine"
    query: "SubwindowOhos InitContainer 初始化链：Rosen::Window 创建 + AceContainer 子容器 + VSync 共享"
  - repo: "openharmony/ace_engine"
    query: "SubwindowManager SubwindowMixMap 多维度键索引和 containerMap_ 双向映射"
  - repo: "openharmony/ace_engine"
    query: "RosenWindow RecoverExecutor VSync 超时恢复机制（3s DFX + 500ms ForceFlushVsync）"
  - repo: "openharmony/ace_engine"
    query: "WindowExtensionConnectionAdapterOhos 与 OhosNG 旧/新版并存及 ConnectExtension 签名差异"
```

**关键文档：** ace_engine `adapter/ohos/entrance/subwindow/` + `adapter/ohos/entrance/window/` + `frameworks/core/components_ng/render/adapter/rosen_window.h`
