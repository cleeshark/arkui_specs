# 特性规格

## 概述

| 字段 | 内容 |
|------|------|
| 特性名称 | 子窗类型路由与弹窗状态机（SubwindowType 创建路由 / MenuWindowState 状态机 / Toast 双层映射） |
| 特性编号 | Func-03-05-02-Feat-02 |
| FuncID | 03-05-02 |
| 所属 Epic | 无 |
| 优先级 | P0 |
| 目标版本 | API 9 ~ API 26+ |
| SIG 归属 | ArkUI SIG |
| 状态 | Draft |
| 复杂度 | 复杂 |
| lineage | new-on-legacy（已有实现的规格补录，由 Feat-01 拆分） |

## 本次变更范围（Delta）

> 由原 Feat-01 拆分。本 Feat 聚焦七类子窗创建路由、Menu 窗口状态机与 Toast 窗口类型双层映射。

| 类型 | 内容 | 说明 |
|------|------|------|
| ADDED | SubwindowType 枚举（7 种类型） | 框架内部枚举，定义子窗类型路由 |
| ADDED | ToastWindowType 枚举（4 种类型） | 框架内部枚举，定义 Toast 窗口类型路由 |
| ADDED | MenuWindowState 枚举（5 种状态） | 框架内部枚举，定义菜单窗口 attach/detach 状态机 |
| ADDED | GetOrCreateSubWindowByType | 按 SubwindowType 路由创建 Dialog/Menu/Sheet 等 |
| ADDED | GetOrCreateMenuSubWindow | Menu 子窗 DETACHING 重建 |
| ADDED | GetToastWindowType / GetToastRosenType | Toast 容器类型→ToastWindowType→Rosen::WindowType 双层路由 |
| MODIFIED | GetToastRosenType 增加 SelectOverlay 子窗分支 | GetIsSelectOverlaySubWindow 条件判断 |
| MODIFIED | GetOrCreateMenuSubWindow 增加 DETACHING 重建逻辑 | 异步 DestroyWindow + 新建 Subwindow |

## 输入文档

- **需求基线**: 已有能力补录（无独立 requirement.md / proposal.md）
- **设计文档**: `specs/03-engine-framework/05-window-mechanism/02-subwindow-mechanism/design.md`
- **SDK 类型定义**: `<OH_ROOT>/interface/sdk-js/api/@ohos.window.d.ts`

> 需求基线、不涉及项、受影响子系统与仓库详见 proposal.md，本文档不重复摘录。design.md 与本文档并行产出，互不依赖。

## 用户故事

### US-1: 子窗创建路由

**角色**: 框架开发者
**期望**: 我想要通过 SubwindowType 路由到对应的子窗创建函数
**价值**: 以便不同类型子窗有独立的创建/复用策略

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-1.1 | WHEN 创建 Dialog 子窗 THEN `GetOrCreateSubWindowByType(TYPE_DIALOG, isModal)` 构建 SubwindowKey，查找 subwindowMap_，未命中时 CreateSubwindow+InitContainer（`subwindow_manager.cpp:2009-2035`） | 正常 |
| AC-1.2 | WHEN 创建 Menu 子窗 THEN `GetOrCreateMenuSubWindow(instanceId, reuse)` 构建 SubwindowKey（TYPE_MENU），查找或创建（`subwindow_manager.cpp:2037-2070`） | 正常 |
| AC-1.3 | WHEN 创建 Toast 子窗 THEN `GetOrCreateToastWindowNG(containerId, windowType, mainWindowId)` 查找 toastSubwindowMap_，未命中时 CreateSubwindow+SetToastWindowType+InitContainer（`subwindow_manager.cpp:1274-1290`） | 正常 |
| AC-1.4 | WHEN 创建 SelectOverlay 子窗 THEN `GetOrCreateSelectOverlayWindow(containerId, windowType, mainWindowId)` 设置 `SetIsSelectOverlaySubWindow(true)`（`subwindow_manager.cpp:1752-1774`） | 正常 |
| AC-1.5 | WHEN 创建 Sheet 子窗 THEN `ShowBindSheetNG` 中通过 `GetSubwindowByType(TYPE_SHEET)` 查找，未命中时创建+InitContainer+AddSubwindow（`subwindow_manager.cpp:758-766`） | 正常 |
| AC-1.6 | WHEN SubwindowKey 中 TYPE_POPUP 或 TYPE_MENU THEN windowType 统一映射为 TYPE_DIALOG 进行查找（`subwindow_manager.cpp:1673-1675`） | 正常 |

### US-2: Menu 窗口状态机与复用重建

**角色**: 终端用户 / 框架开发者
**期望**: 我想要 Menu 子窗在 attach/detach 状态变化时正确管理窗口生命周期
**价值**: 以便避免菜单关闭后窗口残留或状态不一致

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-2.1 | WHEN ShowMenuNG 调用 THEN MenuWindowState 从 DEFAULT 转为 ATTACHING（`subwindow.h:39-44`，`subwindow_ohos.h:220-238`） | 正常 |
| AC-2.2 | WHEN Rosen 回调 AfterAttached THEN `SetAttachState(MenuWindowState::ATTACHED)`（`subwindow_ohos.h:381-387`） | 正常 |
| AC-2.3 | WHEN GetOrCreateMenuSubWindow 检测到 `GetDetachState() == DETACHING` 或 `reuse == false` THEN 移除旧子窗映射，异步 PostTask DestroyWindow 旧窗，创建新 Subwindow（`subwindow_manager.cpp:2047-2067`） | 正常 |
| AC-2.4 | WHEN Rosen 回调 AfterDetached THEN `SetDetachState(MenuWindowState::DETACHED)`（`subwindow_ohos.h:389-395`） | 正常 |
| AC-2.5 | WHEN 旧窗已显示且触发重建 THEN `SetDestroyInHide(true)` 标记隐藏时销毁（`subwindow_manager.cpp:2051-2052`） | 正常 |
| AC-2.6 | WHEN 旧窗未显示且触发重建 THEN PostTask 到 UI 线程执行 `DestroyWindow()`（`subwindow_manager.cpp:2054-2062`） | 边界 |

### US-3: Toast 窗口类型映射

**角色**: 框架开发者
**期望**: 我想要根据容器类型将 ToastWindowType 正确映射到 Rosen::WindowType
**价值**: 以便 Toast 在不同容器类型下有正确的 Z 序和触摸传递

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-3.1 | WHEN 容器为 SubWindow/MainWindow/DialogWindow THEN `GetToastWindowType` 返回 `TOAST_IN_TYPE_APP_SUB_WINDOW`（`subwindow_manager.cpp:1161-1162`） | 正常 |
| AC-3.2 | WHEN 容器为 SceneBoardWindow THEN `GetToastWindowType` 返回 `TOAST_IN_TYPE_SYSTEM_FLOAT`（`subwindow_manager.cpp:1163-1164`） | 正常 |
| AC-3.3 | WHEN 容器为 SystemWindow THEN `GetToastWindowType` 返回 `TOAST_IN_TYPE_SYSTEM_SUB_WINDOW`（`subwindow_manager.cpp:1165-1166`） | 正常 |
| AC-3.4 | WHEN ToastWindowType 为 TOAST_IN_TYPE_APP_SUB_WINDOW 且 SceneBoardEnabled=false 且非 SelectOverlay THEN `GetToastRosenType` 返回 `WINDOW_TYPE_TOAST`（`subwindow_ohos.cpp:142-145`） | 正常 |
| AC-3.5 | WHEN ToastWindowType 为 TOAST_IN_TYPE_APP_SUB_WINDOW 且 SceneBoardEnabled=true 或为 SelectOverlay THEN `GetToastRosenType` 返回 `WINDOW_TYPE_APP_SUB_WINDOW`（`subwindow_ohos.cpp:146`） | 正常 |
| AC-3.6 | WHEN ToastWindowType 为 TOAST_IN_TYPE_SYSTEM_FLOAT THEN `GetToastRosenType` 返回 `WINDOW_TYPE_SYSTEM_FLOAT`（`subwindow_ohos.cpp:149-150`） | 正常 |
| AC-3.7 | WHEN ToastWindowType 为 TOAST_IN_TYPE_SYSTEM_SUB_WINDOW 或 TOAST_IN_TYPE_TOAST THEN `GetToastRosenType` 返回 `WINDOW_TYPE_TOAST`（`subwindow_ohos.cpp:147-148, 152`） | 正常 |

## 验收追溯

| AC编号 | 关联规则 | 关联 Task | 验证方式 | 证据 |
|-------|----------|-----------|----------|------|
| AC-1.1 ~ AC-1.6 | R-1, R-2, R-3, R-4 | TASK-SUBWINDOW-02 | UT | 子窗创建路由测试 |
| AC-2.1 ~ AC-2.6 | R-5, R-6, R-7 | TASK-SUBWINDOW-02 | UT + 手工 | Menu 状态机测试 |
| AC-3.1 ~ AC-3.7 | R-8, R-9 | TASK-SUBWINDOW-02 | UT | Toast 路由测试 |

## 规则定义

> 类型标签：**行为**（正常路径）、**边界**（输入/状态临界点）、**异常**（非法输入或异常状态）、**恢复**（异常后恢复策略）。

| 规则ID | 类型 | 触发条件 | 预期行为 | 边界/约束 | 关联AC |
|--------|------|----------|----------|-----------|--------|
| R-1 | 行为 | `GetOrCreateSubWindowByType(windowType, isModal)` 调用 | 构建 SubwindowKey → 查找 → 未命中创建 | notReuseFlag = UIExtension && isModal | AC-1.1 |
| R-2 | 行为 | `GetOrCreateMenuSubWindow(instanceId, reuse)` 调用 | 构建 SubwindowKey（TYPE_MENU）→ 查找 → DETACHING/!reuse 时重建 | `subwindow_manager.cpp:2037-2070` | AC-1.2 |
| R-3 | 行为 | `GetOrCreateToastWindowNG(containerId, windowType, mainWindowId)` 调用 | 查找 toastSubwindowMap_ → 未命中创建+SetToastWindowType+InitContainer | `subwindow_manager.cpp:1274-1290` | AC-1.3 |
| R-4 | 行为 | `GetOrCreateSelectOverlayWindow` 调用 | 设置 `SetIsSelectOverlaySubWindow(true)` | `subwindow_manager.cpp:1752-1774` | AC-1.4 |
| R-5 | 行为 | ShowMenuNG 调用 | MenuWindowState 从 DEFAULT 转为 ATTACHING | `subwindow.h:39-44` | AC-2.1 |
| R-6 | 行为 | Rosen 回调 AfterAttached/AfterDetached | SetAttachState(ATTACHED)/SetDetachState(DETACHED) | `subwindow_ohos.h:381-395` | AC-2.2, AC-2.4 |
| R-7 | 恢复 | GetOrCreateMenuSubWindow 检测 DETACHING 或 !reuse | 移除旧映射，异步 DestroyWindow，创建新 Subwindow | 旧窗已显示→SetDestroyInHide；未显示→PostTask DestroyWindow | AC-2.3, AC-2.5, AC-2.6 |
| R-8 | 行为 | GetToastWindowType 按容器类型路由 | SubWindow/MainWindow/DialogWindow→APP_SUB_WINDOW；SceneBoard→SYSTEM_FLOAT；System→SYSTEM_SUB_WINDOW | `subwindow_manager.cpp:1161-1166` | AC-3.1 ~ AC-3.3 |
| R-9 | 行为 | GetToastRosenType 按 ToastWindowType+SceneBoard+SelectOverlay 路由 | APP_SUB_WINDOW+!SceneBoard+!SelectOverlay→WINDOW_TYPE_TOAST；APP_SUB_WINDOW+SceneBoard/SelectOverlay→WINDOW_TYPE_APP_SUB_WINDOW；SYSTEM_FLOAT→WINDOW_TYPE_SYSTEM_FLOAT | `subwindow_ohos.cpp:137-153` | AC-3.4 ~ AC-3.7 |

## 验证映射

| 编号 | 对应规格项 | 验证方式 | 验证重点 |
|------|-----------|----------|----------|
| VM-1 | AC-1.1 ~ AC-1.6 | UT | 七类子窗创建路由 |
| VM-2 | AC-2.1 ~ AC-2.6 | UT + 手工 | MenuWindowState 状态机和重建逻辑 |
| VM-3 | AC-3.1 ~ AC-3.7 | UT | Toast 窗口类型双层路由 |

## API 变更分析

### 新增 API

| API 名称 | 开放范围 | 入参概要 | 返回值 | 错误码范围 | 功能描述 | 关联 AC |
|----------|----------|----------|--------|-----------|----------|---------|
| WindowStage.createSubWindow(name) | Public | name: string | Promise<Window> | 9700001~9700010 | 创建子窗 | AC-1.1 |
| WindowStage.createSubWindowWithOptions(options) | Public | options: SubWindowOptions | Promise<Window> | 同上 | 创建子窗（带选项） | AC-1.1 |
| Window.createSubWindowWithOptions(options) | Public | options: SubWindowOptions | Promise<Window> | 同上 | Window 级别创建子窗 | AC-1.1 |
| Window.on('subWindowClose') | Public | cb: Callback<void> | void | 无 | 子窗关闭事件 | AC-2.4 |

### 变更/废弃 API

| API 名称 | 变更类型 | 影响场景 | 迁移指引 | 关联 AC |
|----------|----------|----------|----------|---------|
| 无 | — | — | — | — |

> 截至当前版本，路由/状态机相关 API 未发现 @deprecated 或 @useinstead 标注。

## 接口规格

### 接口定义

**[SubwindowManager::GetOrCreateSubWindowByType]**

| 属性 | 值 |
|------|-----|
| 函数签名 | `RefPtr<Subwindow> SubwindowManager::GetOrCreateSubWindowByType(SubwindowType windowType, bool isModal)` |
| 返回值 | `RefPtr<Subwindow>` — 子窗实例或 nullptr |
| 开放范围 | InnerApi |
| 错误码 | N/A |
| 关联 AC | AC-1.1 |

**参数约束**

| 参数 | 类型 | 必填 | 默认值 | 约束条件 |
|------|------|------|--------|---------|
| windowType | SubwindowType | 是 | 无 | 0 ~ SUB_WINDOW_TYPE_COUNT-1 |
| isModal | bool | 否 | true | UIExtension 模态时 notReuseFlag=true |

**行为场景**

| # | 触发条件 | 预期行为 | 关联 AC |
|---|----------|----------|---------|
| 1 | 正常容器，未命中缓存 | CreateSubwindow + InitContainer + AddSubwindowBySearchKey | AC-1.1 |
| 2 | UIExtension 模态，notReuseFlag=true | 创建新 Subwindow 但不加入 subwindowMap_ | AC-1.1 |
| 3 | 命中缓存 | 返回已有 Subwindow | AC-1.1 |

**[SubwindowManager::GetOrCreateMenuSubWindow]**

| 属性 | 值 |
|------|-----|
| 函数签名 | `RefPtr<Subwindow> SubwindowManager::GetOrCreateMenuSubWindow(int32_t instanceId, bool reuse)` |
| 返回值 | `RefPtr<Subwindow>` — 菜单子窗实例或 nullptr |
| 开放范围 | InnerApi |
| 错误码 | N/A |
| 关联 AC | AC-1.2, AC-2.3 |

**参数约束**

| 参数 | 类型 | 必填 | 默认值 | 约束条件 |
|------|------|------|--------|---------|
| instanceId | int32_t | 是 | 无 | 有效容器 ID |
| reuse | bool | 否 | true | false 或 DETACHING 时触发重建 |

**行为场景**

| # | 触发条件 | 预期行为 | 关联 AC |
|---|----------|----------|---------|
| 1 | 未命中缓存 | CreateSubwindow + InitContainer + AddSubwindowBySearchKey | AC-1.2 |
| 2 | 命中但 DETACHING 或 !reuse | RemoveSubwindowBySearchKey + 异步 DestroyWindow + 新建 | AC-2.3 |
| 3 | 命中且可复用 | 返回已有 Subwindow | AC-1.2 |

**[SubwindowOhos::GetToastRosenType]**

| 属性 | 值 |
|------|-----|
| 函数签名 | `Rosen::WindowType SubwindowOhos::GetToastRosenType(bool IsSceneBoardEnabled)` |
| 返回值 | `Rosen::WindowType` — Rosen 窗口类型 |
| 开放范围 | InnerApi |
| 错误码 | N/A |
| 关联 AC | AC-3.4 ~ AC-3.7 |

**参数约束**

| 参数 | 类型 | 必填 | 默认值 | 约束条件 |
|------|------|------|--------|---------|
| IsSceneBoardEnabled | bool | 是 | 无 | 父容器 SceneBoard 是否启用 |

**行为场景**

| # | 触发条件 | 预期行为 | 关联 AC |
|---|----------|----------|---------|
| 1 | TOAST_IN_TYPE_APP_SUB_WINDOW + !SceneBoard + !SelectOverlay | WINDOW_TYPE_TOAST | AC-3.4 |
| 2 | TOAST_IN_TYPE_APP_SUB_WINDOW + SceneBoard 或 SelectOverlay | WINDOW_TYPE_APP_SUB_WINDOW | AC-3.5 |
| 3 | TOAST_IN_TYPE_SYSTEM_FLOAT | WINDOW_TYPE_SYSTEM_FLOAT | AC-3.6 |
| 4 | TOAST_IN_TYPE_SYSTEM_SUB_WINDOW 或 TOAST_IN_TYPE_TOAST | WINDOW_TYPE_TOAST | AC-3.7 |

---

## 兼容性声明

- **已有 API 行为变更:** 是
  - GetToastRosenType 增加 SelectOverlay 子窗分支（GetIsSelectOverlaySubWindow 条件判断）
  - GetOrCreateMenuSubWindow 增加 DETACHING 重建逻辑（异步 DestroyWindow + 新建）
- **配置文件格式变更:** 否
- **数据存储格式变更:** 否
- **最低支持版本:** API 9
- **API 版本号策略:** 基础创建 API @since 9，createSubWindowWithOptions @since 11，on('subWindowClose') @since 12

## 架构约束

| 关键约束 | 约束说明 | 影响 AC |
|----------|----------|---------|
| Toast 双层路由 | GetToastWindowType（容器类型→ToastWindowType）+ GetToastRosenType（ToastWindowType→Rosen::WindowType） | AC-3.1 ~ AC-3.7 |
| Menu DETACHING 重建 | DETACHING 状态下不复用窗口，异步销毁并新建 | AC-2.3, AC-2.6 |
| SubwindowType 统一映射 | TYPE_POPUP/TYPE_MENU 查找时统一映射为 TYPE_DIALOG | AC-1.6 |

> 本节列出本特性 AC 验证必须满足的约束。架构规则适用性及设计方案见 design.md。

## 行为场景（Gherkin）

```gherkin
Feature: 子窗类型路由与弹窗状态机
  作为框架开发者
  我想要按 SubwindowType 路由创建子窗，并管理 Menu/Toast 窗口状态
  以便支持 Menu/Dialog/Toast/Popup/Sheet/SelectOverlay/Tips 七类子窗

  Scenario: 创建 Dialog 子窗
    Given 容器 instanceId 有效
    When 调用 GetOrCreateSubWindowByType(TYPE_DIALOG, isModal=true)
    Then 构建 SubwindowKey 并查找 subwindowMap_
    When 未命中缓存
    Then CreateSubwindow + InitContainer + AddSubwindowBySearchKey

  Scenario: Menu 子窗 DETACHING 重建
    Given 已有 Menu 子窗且 GetDetachState() == DETACHING
    When 调用 GetOrCreateMenuSubWindow(instanceId, reuse=true)
    Then RemoveSubwindowBySearchKey 移除旧映射
    And 旧窗未显示时 PostTask DestroyWindow
    And 创建新 Subwindow + InitContainer + AddSubwindowBySearchKey

  Scenario: Toast 窗口类型路由（SceneBoard）
    Given 容器为 SceneBoardWindow
    When 调用 GetToastWindowType(instanceId)
    Then 返回 TOAST_IN_TYPE_SYSTEM_FLOAT
    When GetToastRosenType(IsSceneBoardEnabled=true)
    Then 返回 WINDOW_TYPE_SYSTEM_FLOAT

  Scenario: Toast 窗口类型路由（应用子窗）
    Given 容器为 MainWindow
    When 调用 GetToastWindowType(instanceId)
    Then 返回 TOAST_IN_TYPE_APP_SUB_WINDOW
    When GetToastRosenType(IsSceneBoardEnabled=false)
    Then 返回 WINDOW_TYPE_TOAST
```

## Spec 自审清单

- [x] 无"待定""TBD""TODO"等占位符
- [x] 所有 AC 使用 WHEN/THEN 格式，可独立测试
- [x] 范围边界明确（做什么/不做什么清晰）
- [x] 无语义模糊表述
- [x] AC 与规则表交叉一致（每个 AC 至少关联一条规则，每条规则至少关联一个 AC）
- [x] 规则表每条通过 5 项质量检查（可复现/可观测/边界值/关联AC/无冲突）

## context-references

```yaml
context-queries:
  - repo: "openharmony/ace_engine"
    query: "GetOrCreateSubWindowByType SubwindowType routing TYPE_DIALOG TYPE_MENU TYPE_SHEET"
  - repo: "openharmony/ace_engine"
    query: "GetOrCreateMenuSubWindow DETACHING 状态重建和异步 DestroyWindow"
  - repo: "openharmony/ace_engine"
    query: "GetToastRosenType GetToastWindowType 路由逻辑和 SceneBoard/SelectOverlay 条件分支"
```

**关键文档:**
- 设计文档: `specs/03-engine-framework/05-window-mechanism/02-subwindow-mechanism/design.md`
- 源码入口: `frameworks/base/subwindow/subwindow_manager.cpp`
- 适配实现: `adapter/ohos/entrance/subwindow/subwindow_ohos.cpp`
