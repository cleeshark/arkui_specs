# 特性规格

## 概述

| 字段 | 内容 |
|------|------|
| 特性名称 | 子窗布局交互与多端适配（UIExtension / 热区 / 折叠屏 / 自由多窗 / Z 序 / Static 变体） |
| 特性编号 | Func-03-05-02-Feat-03 |
| FuncID | 03-05-02 |
| 所属 Epic | 无 |
| 优先级 | P1 |
| 目标版本 | API 9 ~ API 26+ |
| SIG 归属 | ArkUI SIG |
| 状态 | Draft |
| 复杂度 | 标准 |
| lineage | new-on-legacy（已有实现的规格补录，由 Feat-01 拆分） |

## 本次变更范围（Delta）

> 由原 Feat-01 拆分。本 Feat 聚焦 UIExtension 子窗、热区/触摸、折叠屏与自由多窗布局、子窗 Z 序排序、ArkTS 1.2 Static 变体。

| 类型 | 内容 | 说明 |
|------|------|------|
| ADDED | UIExtension 子窗 notReuseFlag 与 SetIsUIExt* 标志 | isModal=true 不复用；SetParentId(hostWindowId) |
| ADDED | SetHotAreas/DeleteHotAreas + hotAreasMap_ | 按 nodeId 管理子窗触摸热区 |
| ADDED | ResizeWindowForFoldStatus + SubwindowKey.foldStatus | 折叠屏子窗尺寸调整与实例区分 |
| ADDED | IsFreeMultiWindow / SwitchFollowParentWindowLayout | 自由多窗模式下跟随/独立父窗布局 |
| ADDED | GetSortSubwindow + NORMAL_SUBWINDOW_TYPE | 子窗按类型与 subwindowId 降序排序 |
| ADDED | ArkTS 1.2 Static 变体 | ShowToastStatic/CloseToastStatic/ShowDialogStatic/ShowActionMenuStatic/OpenCustomDialogStatic |
| ADDED | Window.attachLayoutToParentWindow | @since 24，子窗布局跟随父窗 |
| ADDED | WindowStage.createSubWindowAndBindParent | @since 26，创建并绑定父窗 |
| MODIFIED | Static 变体新增 SetSubWindowVsyncListener 路径 | 子窗独立 vsync 监听 |

## 输入文档

- **需求基线**: 已有能力补录（无独立 requirement.md / proposal.md）
- **设计文档**: `specs/03-engine-framework/05-window-mechanism/02-subwindow-mechanism/design.md`
- **SDK 类型定义**: `<OH_ROOT>/interface/sdk-js/api/@ohos.window.d.ts`

> 需求基线、不涉及项、受影响子系统与仓库详见 proposal.md，本文档不重复摘录。design.md 与本文档并行产出，互不依赖。

## 用户故事

### US-1: UIExtension 子窗

**角色**: 应用开发者
**期望**: 我想要在 UIExtension 窗口下正确创建子窗
**价值**: 以便 UIExtension 场景的子窗功能正常

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-1.1 | WHEN UIExtension 窗口且 isModal=true THEN `notReuseFlag = true`，不复用已有子窗，每次创建新 Subwindow（`subwindow_manager.cpp:2017-2022`） | 正常 |
| AC-1.2 | WHEN UIExtension 窗口且 isModal=false THEN `notReuseFlag = false`，可复用已有子窗（`subwindow_manager.cpp:2017`） | 正常 |
| AC-1.3 | WHEN UIExtension 父窗创建子窗 THEN `windowOption->SetParentId(hostWindowId)` 使用宿主窗口 ID（`subwindow_ohos.cpp:173, 360`） | 正常 |
| AC-1.4 | WHEN UIExtension 首个子窗 THEN `windowOption->SetIsUIExtFirstSubWindow(true)`（`subwindow_ohos.cpp:363`） | 正常 |
| AC-1.5 | WHEN UIExtension 后续子窗且 isAppSubwindow THEN `windowOption->SetIsUIExtAnySubWindow(true)`（`subwindow_ohos.cpp:180-187`） | 正常 |

### US-2: 热区管理与触摸传递

**角色**: 应用开发者
**期望**: 我想要精确控制子窗的触摸热区
**价值**: 以便子窗不遮挡父窗的交互区域

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-2.1 | WHEN 调用 `SetHotAreas(rects, nodeId)` THEN 按 nodeId 存入 `hotAreasMap_`，并调用 `window_->SetTouchHotAreas`（`subwindow_ohos.h:119`，`subwindow_ohos.cpp` SetHotAreas 实现） | 正常 |
| AC-2.2 | WHEN 调用 `DeleteHotAreas(nodeId)` THEN 从 `hotAreasMap_` 移除指定 nodeId，更新窗口热区（`subwindow_ohos.h:120`） | 正常 |
| AC-2.3 | WHEN SelectOverlay 子窗设置热区 THEN 通过 `SetSelectOverlayHotAreas(rects, nodeId, instanceId)` 路由到子窗 SetHotAreas（`subwindow_manager.cpp:1776-1785`） | 正常 |

### US-3: 折叠屏适配

**角色**: 终端用户
**期望**: 我想要子窗在折叠屏状态变化时正确调整尺寸
**价值**: 以便子窗在折叠/展开状态下都有正确的显示

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-3.1 | WHEN 折叠状态变化 THEN `ResizeWindowForFoldStatus(parentContainerId)` 调用，遍历所有 Toast/Dialog 子窗执行 `window->ResizeWindowForFoldStatus(parentContainerId)`（`subwindow_manager.cpp:1484-1507`） | 正常 |
| AC-3.2 | WHEN SuperFoldDisplayDevice THEN SubwindowKey 的 foldStatus 从 `container->GetFoldStatusFromListener()` 获取，区分折叠状态的子窗实例（`subwindow_manager.cpp:1680-1683`） | 正常 |
| AC-3.3 | WHEN 窗口大小变化 THEN `OnWindowSizeChanged(containerId, windowRect, reason)` 调用 `OnHostWindowSizeChanged` 更新子窗 OverlayManager（`subwindow_manager.cpp:828-846`） | 正常 |

### US-4: 自由多窗与跟随父窗布局

**角色**: 应用开发者
**期望**: 我想要子窗在自由多窗模式下正确跟随或独立于父窗布局
**价值**: 以便支持自由多窗场景下的子窗布局

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-4.1 | WHEN 查询自由多窗状态 THEN `IsFreeMultiWindow()` 返回 `parentWindow_->GetFreeMultiWindowModeEnabledState()`（`subwindow_ohos.cpp:2589-2597`） | 正常 |
| AC-4.2 | WHEN `NeedFollowParentWindowLayout()` 为 true 且 `!expandDisplay && !freeMultiWindowEnable` THEN `SetFollowParentWindowLayoutEnabled(true)`（`subwindow_ohos.cpp:2737-2738`） | 正常 |
| AC-4.3 | WHEN 自由多窗模式开启 THEN `SetFollowParentWindowLayoutEnabled(false)` + `ResizeWindow()`（`subwindow_ohos.cpp:2739-2741`） | 正常 |
| AC-4.4 | WHEN 首次添加 FollowParentWindowLayout 节点 THEN 触发 `SwitchFollowParentWindowLayout(IsFreeMultiWindow())`（`subwindow_ohos.cpp:2744-2750`） | 正常 |
| AC-4.5 | WHEN 最后一个 FollowParentWindowLayout 节点移除 THEN 触发 `SwitchFollowParentWindowLayout(IsFreeMultiWindow())`（`subwindow_ohos.cpp:2753-2759`） | 正常 |

### US-5: 子窗 Z 序排序

**角色**: 框架开发者
**期望**: 我想要多个子窗按类型和创建顺序正确排序 Z 序
**价值**: 以便 Dialog 在 Menu 之上，Popup 在 Dialog 之上

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-5.1 | WHEN 获取排序子窗列表 THEN 遍历 `NORMAL_SUBWINDOW_TYPE = {TYPE_MENU, TYPE_DIALOG, TYPE_POPUP, TYPE_SHEET}`（`subwindow_manager.cpp:33-34, 1933-1939`） | 正常 |
| AC-5.2 | WHEN 多个子窗存在 THEN 按 `subwindowId` 降序排序（`subwindow_manager.cpp:1941-1948`） | 正常 |
| AC-5.3 | WHEN 子窗不存在于 subwindowMap_ THEN 返回 null，不加入排序列表（`subwindow_manager.cpp:1936-1938`） | 正常 |

### US-6: ArkTS 1.2 Static 变体

**角色**: 框架开发者
**期望**: 我想要在 ArkTS 1.2 Static 模式下使用子窗的 Static 变体方法
**价值**: 以便 Static 模式有独立的 vsync 监听和容器初始化路径

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-6.1 | WHEN ArkTS 1.2 Static 模式调用 ShowToastStatic THEN 路由到 `GetOrCreateSubWindowByType(TYPE_DIALOG)` 或 `GetOrCreateSubWindow(true)`（`subwindow_manager_static.cpp:141-148, 173-180, 200-207`） | 正常 |
| AC-6.2 | WHEN Static 模式子窗初始化 THEN 调用 `SetSubWindowVsyncListener` 为子窗设置独立 vsync 监听（`subwindow_ohos.cpp:460-463, subwindow_ohos.h:374`） | 正常 |
| AC-6.3 | WHEN Static 变体方法定义 THEN 包含 ShowToastStatic/CloseToastStatic/ShowDialogStatic/ShowActionMenuStatic/OpenCustomDialogStatic（`subwindow.h:293-300`，`subwindow_ohos.h:261-267`） | 正常 |
| AC-6.4 | WHEN Static 变体在 iOS/Android 平台 THEN 不编译（`#if !defined(IOS_PLATFORM) && !defined(ANDROID_PLATFORM)`，`subwindow.h:291`） | 边界 |

## 验收追溯

| AC编号 | 关联规则 | 关联 Task | 验证方式 | 证据 |
|-------|----------|-----------|----------|------|
| AC-1.1 ~ AC-1.5 | R-1, R-2 | TASK-SUBWINDOW-03 | UT | UIExtension 子窗测试 |
| AC-2.1 ~ AC-2.3 | R-3 | TASK-SUBWINDOW-03 | UT | 热区管理测试 |
| AC-3.1 ~ AC-3.3 | R-4, R-5 | TASK-SUBWINDOW-03 | UT + 手工 | 折叠屏适配测试 |
| AC-4.1 ~ AC-4.5 | R-6, R-7 | TASK-SUBWINDOW-03 | UT | 自由多窗测试 |
| AC-5.1 ~ AC-5.3 | R-8 | TASK-SUBWINDOW-03 | UT | Z 序排序测试 |
| AC-6.1 ~ AC-6.4 | R-9, R-10 | TASK-SUBWINDOW-03 | UT | Static 变体测试 |

## 规则定义

> 类型标签：**行为**、**边界**、**异常**、**恢复**。

| 规则ID | 类型 | 触发条件 | 预期行为 | 边界/约束 | 关联AC |
|--------|------|----------|----------|-----------|--------|
| R-1 | 行为 | UIExtension 窗口且 isModal=true | notReuseFlag=true，不复用 | `subwindow_manager.cpp:2017-2022` | AC-1.1 |
| R-2 | 行为 | UIExtension 父窗创建子窗 | SetParentId(hostWindowId)，SetIsUIExtFirstSubWindow/SetIsUIExtAnySubWindow | `subwindow_ohos.cpp:173, 360-365` | AC-1.3 ~ AC-1.5 |
| R-3 | 行为 | SetHotAreas(rects, nodeId) 调用 | 按 nodeId 存入 hotAreasMap_，调用 window_->SetTouchHotAreas | `subwindow_ohos.h:119, subwindow_ohos.cpp:336` | AC-2.1, AC-2.2 |
| R-4 | 行为 | ResizeWindowForFoldStatus(parentContainerId) 调用 | 遍历 Toast/Dialog 子窗执行 ResizeWindowForFoldStatus | `subwindow_manager.cpp:1484-1507` | AC-3.1 |
| R-5 | 行为 | SuperFoldDisplayDevice 下构建 SubwindowKey | foldStatus 从 GetFoldStatusFromListener 获取 | displayId=0 或 999 时触发 | AC-3.2 |
| R-6 | 行为 | IsFreeMultiWindow() 调用 | 返回 parentWindow_->GetFreeMultiWindowModeEnabledState() | parentWindow_ 为 null 时返回 false | AC-4.1 |
| R-7 | 行为 | SwitchFollowParentWindowLayout(freeMultiWindowEnable) | NeedFollow && !expandDisplay && !freeMultiWindow → SetFollowParentWindowLayoutEnabled(true)；否则 false+ResizeWindow | nodeId_ != DEFAULT_NODE_ID 时 UEC 始终跟随 | AC-4.2, AC-4.3 |
| R-8 | 行为 | GetSortSubwindow(instanceId) 调用 | 遍历 NORMAL_SUBWINDOW_TYPE，按 subwindowId 降序排序 | `subwindow_manager.cpp:1931-1950` | AC-5.1 ~ AC-5.3 |
| R-9 | 行为 | ArkTS 1.2 Static 模式调用 ShowToastStatic | 路由到 GetOrCreateSubWindowByType(TYPE_DIALOG) 或 GetOrCreateSubWindow(true) | `subwindow_manager_static.cpp:141-207` | AC-6.1 |
| R-10 | 行为 | Static 模式子窗初始化 | SetSubWindowVsyncListener 设置独立 vsync | 前端类型为 ARK_TS/DYNAMIC_HYBRID_STATIC/STATIC_HYBRID_DYNAMIC | AC-6.2 |

## 验证映射

| 编号 | 对应规格项 | 验证方式 | 验证重点 |
|------|-----------|----------|----------|
| VM-1 | AC-1.1 ~ AC-1.5 | UT | UIExtension 子窗创建和复用策略 |
| VM-2 | AC-2.1 ~ AC-2.3 | UT | 热区管理 |
| VM-3 | AC-3.1 ~ AC-3.3 | UT + 手工 | 折叠屏适配 |
| VM-4 | AC-4.1 ~ AC-4.5 | UT | 自由多窗和跟随父窗布局 |
| VM-5 | AC-5.1 ~ AC-5.3 | UT | 子窗 Z 序排序 |
| VM-6 | AC-6.1 ~ AC-6.4 | UT | ArkTS 1.2 Static 变体 |

## API 变更分析

### 新增 API

| API 名称 | 开放范围 | 入参概要 | 返回值 | 错误码范围 | 功能描述 | 关联 AC |
|----------|----------|----------|--------|-----------|----------|---------|
| Window.setSubWindowModal(modal) | Public | modal: boolean | Promise<void> | 9700001~9700010 | 设置子窗模态 | AC-1.1 |
| Window.getSubWindowZLevel() | Public | 无 | Promise<number> | 同上 | 获取子窗 Z 序 | AC-5.2 |
| Window.setSubWindowZLevel(zLevel) | Public | zLevel: number | Promise<void> | 同上 | 设置子窗 Z 序 | AC-5.2 |
| Window.attachLayoutToParentWindow(options) | Public | options: SubWindowAttachOptions | Promise<void> | 同上 | 子窗布局跟随父窗 | AC-4.2 |
| WindowStage.createSubWindowAndBindParent(parentId, options) | Public | parentId: number, options: SubWindowOptions | Promise<Window> | 同上 | 创建并绑定父窗 | AC-1.3 |

### 变更/废弃 API

| API 名称 | 变更类型 | 影响场景 | 迁移指引 | 关联 AC |
|----------|----------|----------|----------|---------|
| 无 | — | — | — | — |

## 兼容性声明

- **已有 API 行为变更:** 是
  - SubwindowKey 增加 foldStatus 字段用于 SuperFoldDisplayDevice
  - ArkTS 1.2 Static 变体新增 SetSubWindowVsyncListener 路径
- **配置文件格式变更:** 否
- **数据存储格式变更:** 否
- **最低支持版本:** API 9
- **API 版本号策略:** setSubWindowModal @since 12，getSubWindowZLevel/setSubWindowZLevel @since 14，attachLayoutToParentWindow @since 24，createSubWindowAndBindParent @since 26

## 架构约束

| 关键约束 | 约束说明 | 影响 AC |
|----------|----------|---------|
| UIExtension 模态不复用 | notReuseFlag = IsUIExtensionWindow && isModal | AC-1.1, AC-1.2 |
| 热区按 nodeId 隔离 | hotAreasMap_ 按 nodeId 管理多节点热区 | AC-2.1 ~ AC-2.3 |
| 折叠屏实例区分 | SubwindowKey.foldStatus 区分折叠状态实例 | AC-3.2 |
| 自由多窗跟随父窗 | NeedFollowParentWindowLayout + IsFreeMultiWindow 决定跟随/独立 | AC-4.1 ~ AC-4.5 |
| Z 序按 subwindowId 降序 | NORMAL_SUBWINDOW_TYPE 遍历 + subwindowId 降序 | AC-5.1 ~ AC-5.3 |
| Static 变体平台限制 | iOS/Android 平台不编译 Static 变体 | AC-6.4 |

> 本节列出本特性 AC 验证必须满足的约束。架构规则适用性及设计方案见 design.md。

## 多设备适配声明

| 设备类型 | 行为差异 | 规格/约束 | 验证方式 | 证据 |
|----------|----------|-----------|----------|------|
| 手机 | 无差异 | — | — | — |
| 平板 | 无差异 | — | — | — |
| 折叠屏 | SubwindowKey foldStatus 区分折叠状态；ResizeWindowForFoldStatus 调整子窗尺寸 | foldStatus 非 UNKNOWN 时区分实例 | UT + 手工 | 折叠屏子窗测试 |

## 全局特性影响

| 特性 | 适用？ | 结论 | 关联场景 |
|------|--------|------|----------|
| 多窗口/分屏 | 是 | IsFreeMultiWindow/SwitchFollowParentWindowLayout 支持自由多窗模式 | AC-4.1 ~ AC-4.5 |
| 版本升级 | 是 | API 12/14/24/26 多版本 API 兼容 | AC-1.1, AC-4.2 |
| 生态兼容 | 是 | UIExtension 子窗 SetParentId 使用 hostWindowId | AC-1.3 |

## 行为场景（Gherkin）

```gherkin
Feature: 子窗布局交互与多端适配
  作为框架开发者
  我想要管理 UIExtension 子窗、热区、折叠屏、自由多窗、Z 序与 Static 变体
  以便子窗在多场景多设备下正确工作

  Scenario: UIExtension 模态子窗不复用
    Given 容器为 UIExtensionWindow 且 isModal=true
    When 调用 GetOrCreateSubWindowByType(TYPE_DIALOG, isModal=true)
    Then notReuseFlag=true
    And 每次创建新 Subwindow 但不加入 subwindowMap_

  Scenario: 自由多窗跟随父窗布局
    Given 子窗 NeedFollowParentWindowLayout() 为 true
    And IsFreeMultiWindow() 为 false
    And expandDisplay 为 false
    When 调用 SwitchFollowParentWindowLayout(false)
    Then SetFollowParentWindowLayoutEnabled(true)

  Scenario Outline: SubwindowKey foldStatus 获取
    Given SuperFoldDisplayDevice 为 true
    And displayId 为 <display_id>
    When 构建 SubwindowKey
    Then foldStatus 从 GetFoldStatusFromListener 获取

    Examples:
      | display_id |
      | 0          |
      | 999        |

  Scenario: ArkTS 1.2 Static 子窗
    Given 前端类型为 ARK_TS
    When Static 模式调用 ShowToastStatic
    Then 路由到 GetOrCreateSubWindowByType(TYPE_DIALOG)
    And SetSubWindowVsyncListener 设置子窗 vsync

  Scenario: 子窗 Z 序排序
    Given 存在 TYPE_MENU, TYPE_DIALOG, TYPE_POPUP, TYPE_SHEET 四类子窗
    When 调用 GetSortSubwindow(instanceId)
    Then 按 NORMAL_SUBWINDOW_TYPE 顺序遍历
    And 按 subwindowId 降序排序

  Scenario: 子窗热区设置
    Given SelectOverlay 子窗已创建
    When 调用 SetSelectOverlayHotAreas(rects, nodeId, instanceId)
    Then 路由到子窗 SetHotAreas
    And 按 nodeId 存入 hotAreasMap_
    And 调用 window_->SetTouchHotAreas
```

## Spec 自审清单

- [x] 无"待定""TBD""TODO"等占位符
- [x] 所有 AC 使用 WHEN/THEN 格式，可独立测试
- [x] 范围边界明确（做什么/不做什么清晰）
- [x] 无语义模糊表述
- [x] AC 与规则表交叉一致
- [x] 规则表每条通过 5 项质量检查

## context-references

```yaml
context-queries:
  - repo: "openharmony/ace_engine"
    query: "UIExtension 子窗 notReuseFlag SetIsUIExtFirstSubWindow SetIsUIExtAnySubWindow"
  - repo: "openharmony/ace_engine"
    query: "SetHotAreas DeleteHotAreas hotAreasMap_ SelectOverlay 热区"
  - repo: "openharmony/ace_engine"
    query: "ResizeWindowForFoldStatus SubwindowKey foldStatus SuperFoldDisplayDevice"
  - repo: "openharmony/ace_engine"
    query: "IsFreeMultiWindow SwitchFollowParentWindowLayout 自由多窗"
  - repo: "openharmony/ace_engine"
    query: "GetSortSubwindow NORMAL_SUBWINDOW_TYPE 子窗 Z 序排序"
  - repo: "openharmony/ace_engine"
    query: "ArkTS 1.2 Static 变体 ShowToastStatic SetSubWindowVsyncListener"
```

**关键文档:**
- 设计文档: `specs/03-engine-framework/05-window-mechanism/02-subwindow-mechanism/design.md`
- 源码入口: `frameworks/base/subwindow/subwindow_manager.cpp`、`subwindow_manager_static.cpp`
- 适配实现: `adapter/ohos/entrance/subwindow/subwindow_ohos.cpp`
