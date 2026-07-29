# 特性规格

> Func-04-08-03-Feat-01 浮层能力：固化 OverlayManager 的浮层挂载、popup/modal/sheet 生命周期、LevelMode OVERLAY/EMBEDDED 路由、子窗分发与 NAPI overlayManager API 行为规格。

## 概述

| 属性 | 值 |
|------|-----|
| 特性名称 | 浮层能力 (Overlay Capability) |
| 特性编号 | Func-04-08-03-Feat-01 |
| 所属 Epic | 无（已有能力补录） |
| 优先级 | P0 |
| 目标版本 | API 7 起支持，API 12 引入 overlayManager NAPI 模块 |
| SIG 归属 | ArkUI SIG |
| 状态 | Baselined |
| 复杂度 | 高 |

## 本次变更范围（Delta）

> 历史规格补齐，补录已有实现的完整行为规格。

| 类型 | 内容 | 说明 |
|------|------|------|
| ADDED | OverlayManager 浮层挂载与生命周期管理全量行为 | 补录浮层能力行为 |

## 输入文档

| 文档 | 路径 | 状态 |
|------|------|------|
| Design | `specs/04-common-capability/08-root-view/03-overlay-capability/design.md` | Baselined |
| SDK API | `interfaces/napi/kits/overlay/js_overlay.cpp` | — |

---

## 用户故事

### US-1: OverlayManager 创建与挂载

**作为** 系统开发者,
**我想要** 在 PipelineContext 初始化时创建 OverlayManager 并绑定到根节点,
**以便** 为所有浮层提供统一的挂载点与生命周期管理。

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-1.1 | WHEN PipelineContext::SetupRootElement 执行 THEN 创建 rootNode(ROOT_ETS_TAG) + stageNode(STAGE_ETS_TAG) | 正常 |
| AC-1.2 | WHEN OverlayManager 构造 THEN 绑定到 stage 节点的父节点（frameNode），非绝对根节点 | 正常 |
| AC-1.3 | WHEN 原子服务(installationFree_) THEN OverlayManager 绑定到 atomicService 父节点 | 边界 |
| AC-1.4 | WHEN CreateOverlayNode 执行 THEN 创建 OVERLAY_ETS_TAG 透明全尺寸容器，HitTestMode=HTMTRANSPARENT_SELF，插入到 stage 之后 | 正常 |
| AC-1.5 | WHEN 子窗创建 THEN 子窗拥有独立 OverlayManager（Subwindow::GetOverlayManager） | 边界 |

### US-2: Popup 生命周期

**作为** 应用开发者,
**我想要** 通过 bindPopup 绑定的气泡在 OverlayManager 中管理显示/隐藏/销毁,
**以便** popup 节点正确挂载到根节点并响应生命周期。

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-2.1 | WHEN ShowPopup 执行 THEN UpdatePopupMap 存储 PopupInfo 到 popupMap_，MountPopup 挂载到根节点 | 正常 |
| AC-2.2 | WHEN MountPopup 执行 THEN MountToParentWithService 挂载，MarkDirtyNode(PROPERTY_UPDATE_MEASURE_SELF)，isCurrentOnShow=true | 正常 |
| AC-2.3 | WHEN HidePopup 执行 THEN checkAndSetExitingStatus → HidePopupAnimation 动画后 ErasePopup 移除 | 正常 |
| AC-2.4 | WHEN 目标组件销毁 THEN PushDestroyCallbackWithTag 注册的回调调用 ErasePopup 清理 | 恢复 |

### US-3: Modal/Sheet 生命周期

**作为** 应用开发者,
**我想要** bindContentCover/bindSheet 创建的模态/半模态浮层在 OverlayManager modalStack_ 中管理,
**以便** 支持返回键 LIFO 弹出与批量清理。

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-3.1 | WHEN HandleModalShow 执行 THEN 创建 MODAL_PAGE_TAG 节点 + ModalPresentationPattern，MountToParentWithService，modalStack_.push + modalList_.emplace_back | 正常 |
| AC-3.2 | WHEN HandleModalPop 执行 THEN ModalPageLostFocus → onWillDisappear → transition out → RemoveChildWithService → RemoveModal | 正常 |
| AC-3.3 | WHEN SaveSheetPageNode 执行 THEN sheetMap_.emplace(sheetKey, sheetNode)，modalStack_/modalList_ 同步注册，sheetSetOverlay 设置 overlay 弱引用 | 正常 |

### US-4: LevelMode 路由与 z-index

**作为** 应用开发者,
**我想要** 通过 LevelMode(OVERLAY/EMBEDDED) 控制浮层挂载到全局根或页面级,
**以便** 支持在 NavDestination 内嵌入浮层。

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-4.1 | WHEN LevelMode=OVERLAY THEN 浮层挂载到 OverlayManager 全局根节点 | 正常 |
| AC-4.2 | WHEN LevelMode=EMBEDDED THEN DialogManager::GetEmbeddedOverlay(uniqueId) 查找页面级 OverlayManager，popupInfo.embeddedOveraly 路由 | 正常 |
| AC-4.3 | WHEN SceneBoard 窗口模式 THEN FindWindowScene 遍历父节点找 WINDOW_SCENE_ETS_TAG，浮层挂载到 WindowScene 而非全局根 | 边界 |
| AC-4.4 | WHEN MountToParentWithOrder 执行 THEN GetNextNodeWithOrder 查找插入位置，PutLevelOrder 注册到 nodeIdOrderMap_ + orderNodesMap_ | 正常 |

### US-5: NAPI overlayManager API

**作为** 应用开发者,
**我想要** 通过 `@ohos.overlayManager` NAPI 模块操作浮层节点,
**以便** 以编程方式添加/移除/显示/隐藏浮层节点并控制 z-index。

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-5.1 | WHEN 调用 addFrameNode(node) THEN 通过 delegate->AddFrameNodeToOverlay 将节点挂载到 overlay 容器 | 正常 |
| AC-5.2 | WHEN 调用 openOrderOverlay(node, options) THEN 通过 delegate->OpenOrderOverlay 打开有序浮层，options 含 levelOrder/levelMode/levelUniqueId | 正常 |
| AC-5.3 | WHEN 调用 showNode/hideNode/showAllFrameNodes/hideAllFrameNodes THEN 通过 delegate 对应方法控制浮层节点可见性 | 正常 |
| AC-5.4 | WHEN 调用 setOverlayManagerOptions(options) THEN 设置 OverlayManagerInfo(renderRootOverlay/enableBackPressedEvent/onBackPress) | 正常 |

### US-6: 子窗路由与返回键拦截

**作为** 系统开发者,
**我想要** 浮层在子窗与 Overlay 间正确路由，并通过返回键逐层弹出,
**以便** 支持跨窗口浮层与一致的返回体验。

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-6.1 | WHEN ViewAbstract::BindPopup 检测 IsShowInSubWindow=true THEN 走 SubwindowManager::ShowPopupNG 子窗路径，否则走 OverlayManager::ShowPopup | 边界 |
| AC-6.2 | WHEN 返回键触发 THEN RemoveOverlay 按 LIFO 从 modalStack_ 弹出栈顶 modal/sheet，或 RemoveOverlayCommon 清理 dialog/menu/bubble | 正常 |
| AC-6.3 | WHEN onBackPress 回调存在且 enableBackPressedEvent=true THEN 调用回调，若拦截则停止后续返回处理 | 边界 |

---

## 验收追溯

| AC编号 | US ID | 关联规则 | 验证手段 |
|-------|-------|----------|----------|
| AC-1.1 | US-1 | R-1 | 代码审查 pipeline_context.cpp:2097-2193 |
| AC-1.2 | US-1 | R-2 | 代码审查 pipeline_context.cpp:2155 |
| AC-1.3 | US-1 | R-3 | 代码审查 pipeline_context.cpp:2154 |
| AC-1.4 | US-1 | R-4 | 代码审查 overlay_manager.cpp:6016-6045 |
| AC-1.5 | US-1 | R-5 | 代码审查 subwindow.h:244 |
| AC-2.1 | US-2 | R-6 | 代码审查 overlay_manager.cpp:946-974 |
| AC-2.2 | US-2 | R-7 | 代码审查 overlay_manager.cpp:1264-1339 |
| AC-2.3 | US-2 | R-8 | 代码审查 overlay_manager.cpp:1369-1436 |
| AC-2.4 | US-2 | R-9 | 代码审查 view_abstract.cpp:4714,4726 |
| AC-3.1 | US-3 | R-10 | 代码审查 overlay_manager.cpp:3268-3359 |
| AC-3.2 | US-3 | R-11 | 代码审查 overlay_manager.cpp:3361-3416 |
| AC-3.3 | US-3 | R-12 | 代码审查 overlay_manager.cpp:4480-4502 |
| AC-4.1 | US-4 | R-13 | 代码审查 overlay_manager.h:800 |
| AC-4.2 | US-4 | R-14 | 代码审查 overlay_manager.cpp:938-944 |
| AC-4.3 | US-4 | R-15 | 代码审查 overlay_manager.cpp:5324-5338 |
| AC-4.4 | US-4 | R-16 | 代码审查 overlay_manager.cpp:6938-6975,1980-1991 |
| AC-5.1 | US-5 | R-17 | 代码审查 js_overlay.cpp:46 |
| AC-5.2 | US-5 | R-18 | 代码审查 js_overlay.cpp:204 |
| AC-5.3 | US-5 | R-19 | 代码审查 js_overlay.cpp:256-305 |
| AC-5.4 | US-5 | R-20 | 代码审查 js_overlay.cpp:320 |
| AC-6.1 | US-6 | R-21 | 代码审查 view_abstract.cpp:4627-4772 |
| AC-6.2 | US-6 | R-22 | 代码审查 overlay_manager.cpp:2491-2552 |
| AC-6.3 | US-6 | R-23 | 代码审查 overlay_manager.cpp:2491-2552 |

## 规则定义

> **统一规则表。** 类型标签：**行为**、**边界**、**异常**、**恢复**。

| 规则ID | 类型 | 触发条件 | 预期行为 | 边界/约束 | 关联AC |
|--------|------|----------|----------|-----------|--------|
| R-1 | 行为 | SetupRootElement | 创建 rootNode(ROOT_ETS_TAG) + stageNode(STAGE_ETS_TAG) | `pipeline_context.cpp:2097-2193` | AC-1.1 |
| R-2 | 行为 | OverlayManager 构造 | 绑定到 stage 父节点，非绝对根 | `pipeline_context.cpp:2155` | AC-1.2 |
| R-3 | 边界 | installationFree_=true | 绑定到 atomicService 父节点 | `pipeline_context.cpp:2154` | AC-1.3 |
| R-4 | 行为 | CreateOverlayNode | 创建 OVERLAY_ETS_TAG 透明容器，HitTestMode=HTMTRANSPARENT_SELF，插入 stage 之后 | `overlay_manager.cpp:6016-6045` | AC-1.4 |
| R-5 | 边界 | 子窗创建 | 子窗拥有独立 OverlayManager | `subwindow.h:244` | AC-1.5 |
| R-6 | 行为 | ShowPopup | UpdatePopupMap → MountPopup 挂载到根 | `overlay_manager.cpp:946-974` | AC-2.1 |
| R-7 | 行为 | MountPopup | MountToParentWithService + MarkDirtyNode(MEASURE_SELF) + isCurrentOnShow=true | `overlay_manager.cpp:1264-1339` | AC-2.2 |
| R-8 | 行为 | HidePopup | checkAndSetExitingStatus → HidePopupAnimation → ErasePopup | `overlay_manager.cpp:1369-1436` | AC-2.3 |
| R-9 | 恢复 | 目标销毁 | PushDestroyCallbackWithTag 注册 ErasePopup 回调 | `view_abstract.cpp:4714,4726` | AC-2.4 |
| R-10 | 行为 | HandleModalShow | 创建 MODAL_PAGE_TAG + ModalPresentationPattern → MountToParentWithService → modalStack_/modalList_ 注册 | `overlay_manager.cpp:3268-3359` | AC-3.1 |
| R-11 | 行为 | HandleModalPop | ModalPageLostFocus → onWillDisappear → transition out → RemoveChildWithService → RemoveModal | `overlay_manager.cpp:3361-3416` | AC-3.2 |
| R-12 | 行为 | SaveSheetPageNode | sheetMap_.emplace + modalStack_/modalList_ 注册 + sheetSetOverlay | `overlay_manager.cpp:4480-4502` | AC-3.3 |
| R-13 | 行为 | LevelMode=OVERLAY | 挂载到 OverlayManager 全局根 | `overlay_manager.h:800 rootNodeWeak_` | AC-4.1 |
| R-14 | 行为 | LevelMode=EMBEDDED | DialogManager::GetEmbeddedOverlay 查找页面级 OverlayManager，embeddedOveraly 路由 | `overlay_manager.cpp:938-944` | AC-4.2 |
| R-15 | 边界 | SceneBoard 窗口模式 | FindWindowScene 遍历父节点找 WINDOW_SCENE_ETS_TAG | 非 SceneBoard 返回 rootNodeWeak_ `overlay_manager.cpp:5324-5338` | AC-4.3 |
| R-16 | 行为 | MountToParentWithOrder | GetNextNodeWithOrder 查找插入位置 → PutLevelOrder 注册双 map | `overlay_manager.cpp:6938-6975,1980-1991` | AC-4.4 |
| R-17 | 行为 | addFrameNode(node) | delegate->AddFrameNodeToOverlay 挂载到 overlay 容器 | `js_overlay.cpp:46` | AC-5.1 |
| R-18 | 行为 | openOrderOverlay(node, options) | delegate->OpenOrderOverlay 打开有序浮层 | options 含 levelOrder/levelMode/levelUniqueId `js_overlay.cpp:204` | AC-5.2 |
| R-19 | 行为 | showNode/hideNode/showAll/hideAll | delegate 控制浮层节点可见性 | `js_overlay.cpp:256-305` | AC-5.3 |
| R-20 | 行为 | setOverlayManagerOptions | 设置 OverlayManagerInfo(renderRootOverlay/enableBackPressedEvent/onBackPress) | `js_overlay.cpp:320` | AC-5.4 |
| R-21 | 边界 | IsShowInSubWindow=true | 走 SubwindowManager::ShowPopupNG 子窗路径 | 否则走 OverlayManager::ShowPopup `view_abstract.cpp:4627-4772` | AC-6.1 |
| R-22 | 行为 | 返回键触发 | RemoveOverlay 按 LIFO 弹出 modalStack_ 或清理 dialog/menu/bubble | `overlay_manager.cpp:2491-2552` | AC-6.2 |
| R-23 | 边界 | onBackPress 存在且 enableBackPressedEvent=true | 调用回调，若拦截停止后续返回 | `overlay_manager.cpp:2491-2552` | AC-6.3 |
| R-24 | 异常 | popup 节点已在主树 | MountPopup 直接返回不重复挂载 | `overlay_manager.cpp:1264` | AC-2.2 |
| R-25 | 恢复 | modalList_ 遍历删除后 | 从 modalList_ 重建 modalStack_ | `overlay_manager.cpp:4932-4973` | AC-3.1 |

---

## 验证映射

| VM编号 | 关联用户故事 | 验证手段 | 验证要点 |
|-------|-------------|---------|---------|
| VM-1 | US-1 OverlayManager 创建 (AC-1.1~1.5) | 代码审查 | 根节点绑定；overlay 容器；子窗独立 |
| VM-2 | US-2 Popup 生命周期 (AC-2.1~2.4) | 代码审查 | ShowPopup/MountPopup/HidePopup/ErasePopup |
| VM-3 | US-3 Modal/Sheet 生命周期 (AC-3.1~3.3) | 代码审查 | HandleModalShow/Pop；SaveSheetPageNode |
| VM-4 | US-4 LevelMode 与 z-index (AC-4.1~4.4) | 代码审查 | OVERLAY/EMBEDDED 路由；FindWindowScene；z-index 双 map |
| VM-5 | US-5 NAPI overlayManager (AC-5.1~5.4) | 代码审查 | 10 个 NAPI 导出函数 |
| VM-6 | US-6 子窗路由与返回键 (AC-6.1~6.3) | 代码审查 | 双路径分发；RemoveOverlay LIFO |

### 逐 AC 验证用例

| AC编号 | 验证类型 | 位置/用例 |
|-------|----------|-----------|
| AC-1.1 | 代码审查 | `frameworks/core/pipeline_ng/pipeline_context.cpp:2097-2193` |
| AC-1.2 | 代码审查 | `frameworks/core/pipeline_ng/pipeline_context.cpp:2155` |
| AC-1.3 | 代码审查 | `frameworks/core/pipeline_ng/pipeline_context.cpp:2154` |
| AC-1.4 | 代码审查 | `frameworks/core/components_ng/pattern/overlay/overlay_manager.cpp:6016-6045` |
| AC-1.5 | 代码审查 | `frameworks/base/subwindow/subwindow.h:244` |
| AC-2.1 | 代码审查 | `frameworks/core/components_ng/pattern/overlay/overlay_manager.cpp:946-974` |
| AC-2.2 | 代码审查 | `frameworks/core/components_ng/pattern/overlay/overlay_manager.cpp:1264-1339` |
| AC-2.3 | 代码审查 | `frameworks/core/components_ng/pattern/overlay/overlay_manager.cpp:1369-1436` |
| AC-2.4 | 代码审查 | `frameworks/core/components_ng/base/view_abstract.cpp:4714,4726` |
| AC-3.1 | 代码审查 | `frameworks/core/components_ng/pattern/overlay/overlay_manager.cpp:3268-3359` |
| AC-3.2 | 代码审查 | `frameworks/core/components_ng/pattern/overlay/overlay_manager.cpp:3361-3416` |
| AC-3.3 | 代码审查 | `frameworks/core/components_ng/pattern/overlay/overlay_manager.cpp:4480-4502` |
| AC-4.1 | 代码审查 | `frameworks/core/components_ng/pattern/overlay/overlay_manager.h:800` |
| AC-4.2 | 代码审查 | `frameworks/core/components_ng/pattern/overlay/overlay_manager.cpp:938-944` |
| AC-4.3 | 代码审查 | `frameworks/core/components_ng/pattern/overlay/overlay_manager.cpp:5324-5338` |
| AC-4.4 | 代码审查 | `frameworks/core/components_ng/pattern/overlay/overlay_manager.cpp:6938-6975,1980-1991` |
| AC-5.1 | 代码审查 | `interfaces/napi/kits/overlay/js_overlay.cpp:46` |
| AC-5.2 | 代码审查 | `interfaces/napi/kits/overlay/js_overlay.cpp:204` |
| AC-5.3 | 代码审查 | `interfaces/napi/kits/overlay/js_overlay.cpp:256-305` |
| AC-5.4 | 代码审查 | `interfaces/napi/kits/overlay/js_overlay.cpp:320` |
| AC-6.1 | 代码审查 | `frameworks/core/components_ng/base/view_abstract.cpp:4627-4772` |
| AC-6.2 | 代码审查 | `frameworks/core/components_ng/pattern/overlay/overlay_manager.cpp:2491-2552` |
| AC-6.3 | 代码审查 | `frameworks/core/components_ng/pattern/overlay/overlay_manager.cpp:2491-2552` |

---

## API 变更分析

### 新增 API

> SDK 定义来源: `interfaces/napi/kits/overlay/js_overlay.cpp` (NAPI `@ohos.overlayManager` 模块)

| API 名称 | 开放范围 | 入参概要 | 返回值 | 错误码范围 | 功能描述 | 关联 AC |
|----------|----------|----------|--------|-----------|----------|---------|
| `addFrameNode(node, index?)` | Public | node: FrameNode; index?: number | void | N/A | 添加节点到 overlay 容器 | AC-5.1 |
| `addFrameNodeWithOrder(node, levelOrder)` | Public | node; levelOrder: LevelOrder | void | N/A | 添加有序节点 | AC-5.2 |
| `openOrderOverlay(node, options)` | Public | node; options: OrderOverlayOptions | Promise\<void\> | N/A | 打开有序浮层 | AC-5.2 |
| `removeFrameNode(node)` | Public | node | void | N/A | 移除节点 | AC-5.3 |
| `showNode(node)` / `hideNode(node)` | Public | node | void | N/A | 显示/隐藏节点 | AC-5.3 |
| `showAllFrameNodes()` / `hideAllFrameNodes()` | Public | — | void | N/A | 显示/隐藏全部 | AC-5.3 |
| `setOverlayManagerOptions(options)` | Public | OverlayManagerInfo | void | N/A | 设置选项 | AC-5.4 |
| `getOverlayManagerOptions()` | Public | — | OverlayManagerInfo | N/A | 获取选项 | AC-5.4 |

### 变更/废弃 API

| API 名称 | 变更类型 | 影响场景 | 迁移指引 | 关联 AC |
|----------|----------|----------|----------|---------|
| — | — | — | 无变更/废弃 API | — |

## 接口规格

### 接口定义

> 本特性为已有实现补录，接口行为定义详见上方规则定义和用户故事。

无新增接口规格。

---

## 兼容性声明

| API 版本 | 行为差异 | 影响 | 迁移指导 |
|----------|----------|------|----------|
| API 7 | OverlayManager 初始版本，popup/modal 基础生命周期 | — | — |
| API 11 | popup 动画 NG 路径（VERSION_ELEVEN 门控 ShowPopupAnimation vs ShowPopupAnimationNG） | — | — |
| API 12 | modal transition 门控（VERSION_TWELVE：< 12 或 NONE 立即 fire OnAppear）；overlayManager NAPI 模块引入 | — | — |
| API 26 | sheet ThemeScopeId 注册（VERSION_TWENTY_SIX 门控 RegisterOnThemeScopeUpdate/SetThemeScopeId） | — | — |

---

## 架构约束

| 关键约束 | 约束说明 | 影响 AC |
|----------|----------|---------|
| OverlayManager 绑定 stage 父节点 | 浮层作为 stage 兄弟节点，不被 stage 裁剪 | AC-1.2 |
| 子窗独立 OverlayManager | 每个子窗有自己的 OverlayManager，子窗浮层独立管理 | AC-1.5 |
| modalStack_ + modalList_ 双结构 | stack 支持 LIFO 返回键弹出，list 支持遍历清理 | AC-3.1 |
| nodeIdOrderMap_ + orderNodesMap_ | std::map 有序 z-index 管理，O(log n) 查找 | AC-4.4 |
| embeddedOveraly 路由 | PopupInfo.embeddedOveraly 非 null 时走页面级 OverlayManager | AC-4.2 |
| FindWindowScene 逐窗口隔离 | SceneBoard 模式下浮层挂载到 WindowScene | AC-4.3 |

---

## 非功能性需求

| 类型 | 指标/阈值 | 验证方式 | 证据 |
|------|-----------|----------|------|
| 性能 | 浮层挂载 O(1)；z-index 查找 O(log n) | 代码审查 | overlay_manager.cpp |
| 可靠性 | 目标销毁清理 popup/modal/sheet | 代码审查 | PushDestroyCallbackWithTag |
| 可调试性 | MarkDirtyNode 触发重新布局 | 代码审查 | overlay_manager.cpp |

---

## 多设备适配声明

| 设备类型 | 行为差异 | 规格/约束 | 验证方式 | 证据 |
|----------|----------|-----------|----------|------|
| 手机 | 无差异 | — | — | — |
| 平板 | 无差异 | — | — | — |
| 折叠屏 | 无差异 | — | — | — |

---

## 全局特性影响

| 特性 | 适用？ | 结论 | 关联场景 |
|------|--------|------|----------|
| 无障碍 | 是 | 浮层 show/hide 触发 PAGE_OPEN/PAGE_CLOSE 无障碍事件 | AC-2.2, AC-3.1 |
| 大字体 | 否 | 无差异 | — |
| 深色模式 | 否 | 浮层背景色跟随主题 | — |
| 多窗口/分屏 | 是 | SceneBoard 模式 FindWindowScene 逐窗口隔离 | AC-4.3 |
| 多用户 | 否 | 无差异 | — |
| 版本升级 | 是 | API 11/12/26 版本门控 | 兼容性声明 |
| 生态兼容 | 否 | 无差异 | — |

---

## Spec 自审清单

- [x] 无"待定""TBD""TODO"等占位符
- [x] 所有 AC 使用 WHEN/THEN 格式，可独立测试
- [x] 范围边界明确
- [x] 无语义模糊表述
- [x] AC 与规则表交叉一致
- [x] 规则表每条通过 5 项质量检查

---

## context-references

### 源码文件

| 文件 | 说明 |
|------|------|
| `frameworks/core/components_ng/pattern/overlay/overlay_manager.h` | OverlayManager 类 + PopupInfo/DismissTarget/OverlayManagerInfo 结构 |
| `frameworks/core/components_ng/pattern/overlay/overlay_manager.cpp` | OverlayManager 全量实现（7514 行） |
| `frameworks/core/components_ng/pattern/overlay/overlay_options.h` | OrderOverlayOptions |
| `frameworks/core/components_ng/pattern/overlay/level_mode.h` | LevelMode 枚举（OVERLAY/EMBEDDED） |
| `frameworks/core/components_ng/pattern/overlay/level_order.h` | LevelOrder 类 |
| `frameworks/core/components_ng/pattern/overlay/overlay_container_pattern.h` | OverlayContainerPattern |
| `frameworks/core/components_ng/pattern/overlay/dialog_manager.h/.cpp` | DialogManager 单例（嵌入式路由） |
| `frameworks/core/pipeline_ng/pipeline_context.h/.cpp` | 拥有 overlayManager_ + rootNode_ |
| `frameworks/base/subwindow/subwindow_manager.h/.cpp` | 子窗路由 |
| `frameworks/core/components_ng/base/view_abstract.cpp` | BindPopup/BindSheet/BindContentCover 桥接 |
| `interfaces/napi/kits/overlay/js_overlay.cpp` | NAPI @ohos.overlayManager 导出 |
| `interfaces/inner_api/ace_kit/include/ui/view/overlay/overlay_manager.h` | Inner API Kit 抽象 |

### SDK 文档

| 文件 | 说明 |
|------|------|
| `interfaces/napi/kits/overlay/js_overlay.cpp` | @ohos.overlayManager NAPI 模块（10 个导出函数） |
