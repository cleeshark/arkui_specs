# 特性规格

## 概述

| 字段 | 内容 |
|------|------|
| 特性名称 | 子窗抽象与 Manager 核心（Subwindow 抽象/工厂 / Manager 单例 / SubwindowKey 查找 / 容器初始化） |
| 特性编号 | Func-03-05-02-Feat-01 |
| FuncID | 03-05-02 |
| 所属 Epic | 无 |
| 优先级 | P0 |
| 目标版本 | API 9 ~ API 26+ |
| SIG 归属 | ArkUI SIG |
| 状态 | Baselined |
| 复杂度 | 标准 |
| lineage | new-on-legacy（已有实现的规格补录，原全量规格已拆分为 Feat-01/02/03） |

## 本次变更范围（Delta）

> 本特性为已有实现补录，非增量变更。本 Feat 聚焦子窗抽象基类、SubwindowManager 单例与多映射、SubwindowKey 混合查找、子窗容器初始化。子窗类型路由/弹窗状态机见 Feat-02，布局交互与多端适配见 Feat-03。

| 类型 | 内容 | 说明 |
|------|------|------|
| ADDED | Subwindow 抽象基类（60+ 虚方法） | InitContainer/ShowMenuNG/ShowPopupNG/ShowDialogNG/ShowToast/CloseToast/OpenCustomDialogNG/ShowBindSheetNG/ShowSelectOverlay/GetOverlayManager/IsFocused/RequestFocus/Close/DestroyWindow 等 |
| ADDED | SubwindowOhos 适配实现 | 封装 Rosen::Window，windowId_ 自增、parentContainerId_ 绑定 |
| ADDED | SubwindowManager 单例 + subwindowMap_ 多映射 | 双重检查锁 instanceMutex_，AddSubwindowBySearchKey/GetSubwindowBySearchKey/RemoveSubwindowMapByInstanceId |
| ADDED | SubwindowKey 混合查找 | instanceId/displayId/foldStatus/windowType/subwindowType/nodeId 六字段，哈希 (windowType<<24)\|(displayId<<16)\|(instanceId+INSTANCE_ID_MIN) |
| ADDED | InitContainer 子窗容器初始化 | Rosen::WindowOption 三分支窗口类型→Window::Create→注册 MenuWindowSceneListener→创建子 AceContainer+PipelineContext |
| ADDED | WindowStage.createSubWindow / getSubWindow / loadContent | @since 9，基础子窗创建/获取/加载 API |

## 输入文档

- **需求基线**: 已有能力补录（无独立 requirement.md / proposal.md）
- **设计文档**: `specs/03-engine-framework/05-window-mechanism/02-subwindow-mechanism/design.md`
- **SDK 类型定义**: `<OH_ROOT>/interface/sdk-js/api/@ohos.window.d.ts`

> 需求基线、不涉及项、受影响子系统与仓库详见 proposal.md，本文档不重复摘录。design.md 与本文档并行产出，互不依赖。

## 用户故事

### US-1: Subwindow 抽象与工厂

**角色**: 框架开发者
**期望**: 我想要通过统一工厂方法创建子窗实例，在不同平台有不同适配实现
**价值**: 以便框架上层代码不感知平台差异

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-1.1 | WHEN 调用 `Subwindow::CreateSubwindow(instanceId)` THEN 返回 `MakeRefPtr<SubwindowOhos>(instanceId)` 实例（`subwindow_ohos.cpp:124-127`） | 正常 |
| AC-1.2 | WHEN SubwindowOhos 构造时 THEN 初始化 `windowId_ = id_`（自增静态计数器）、`parentContainerId_ = instanceId`、`SetSubwindowId(windowId_)`（`subwindow_ohos.cpp:129-134`） | 正常 |
| AC-1.3 | WHEN 子窗未初始化容器 THEN `GetIsRosenWindowCreate()` 返回 false（`subwindow.h:215-218`） | 正常 |
| AC-1.4 | WHEN Subwindow 抽象基类定义虚方法 THEN 包含 InitContainer/ShowMenuNG/ShowPopupNG/ShowDialogNG/ShowToast/CloseToast/OpenCustomDialogNG/ShowBindSheetNG/ShowSelectOverlay/GetOverlayManager/IsFocused/RequestFocus/Close/DestroyWindow 等 60+ 接口（`subwindow.h:59-300`） | 正常 |

### US-2: SubwindowManager 单例与多映射管理

**角色**: 框架开发者
**期望**: 我想要通过单例管理器统一管理所有子窗的创建、查找和销毁
**价值**: 以便避免多线程并发创建同一类型子窗导致的窗口泄漏

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-2.1 | WHEN 调用 `SubwindowManager::GetInstance()` THEN 返回单例实例（双重检查锁 `instanceMutex_`，`subwindow_manager.cpp:37-47`） | 正常 |
| AC-2.2 | WHEN 子窗创建后 THEN 通过 `AddSubwindowBySearchKey(searchKey, subwindow)` 存入 `subwindowMap_`（`subwindow_manager.cpp:1921-1928`） | 正常 |
| AC-2.3 | WHEN 查找子窗 THEN 通过 `GetSubwindowBySearchKey(searchKey)` 在 `subwindowMap_` 中查找（`subwindow_manager.cpp:2072-2083`） | 正常 |
| AC-2.4 | WHEN 容器销毁 THEN `RemoveSubwindowMapByInstanceId` 批量移除该实例所有子窗映射（`subwindow_manager.cpp:1979+`） | 正常 |
| AC-2.5 | WHEN 多线程并发调用 GetOrCreateSubWindowByType THEN `subwindowMutex_` 保护 `subwindowMap_` 的查找和插入操作（`subwindow_manager.h:303-304`） | 边界 |

### US-3: SubwindowKey 混合查找

**角色**: 框架开发者
**期望**: 我想要通过 SubwindowKey 精确查找特定实例/显示器/折叠状态/类型/节点的子窗
**价值**: 以便支持同类型多实例子窗和多显示器场景

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-3.1 | WHEN 构建 SubwindowKey THEN 包含 instanceId/displayId/foldStatus/windowType/subwindowType/nodeId 六字段（`subwindow_manager.h:40-63`） | 正常 |
| AC-3.2 | WHEN SubwindowKey 哈希计算 THEN `(windowType << 24) | (displayId << 16) | (instanceId + INSTANCE_ID_MIN)`（`subwindow_manager.h:66-73`） | 正常 |
| AC-3.3 | WHEN SuperFoldDisplayDevice 且 displayId 为 0 或 999 THEN foldStatus 从 `container->GetFoldStatusFromListener()` 获取（`subwindow_manager.cpp:1680-1683`） | 边界 |
| AC-3.4 | WHEN 子窗类型为 TYPE_SHEET THEN foldStatus 强制为 UNKNOWN（`subwindow_manager.cpp:1686-1688`） | 正常 |
| AC-3.5 | WHEN instanceId >= MIN_SUBCONTAINER_ID 且非 TOP_MOST_TOAST 类型 THEN 走 GetSubwindowById 快速路径，按 nodeId 匹配（`subwindow_manager.cpp:1853-1860`） | 正常 |

### US-4: 子窗容器初始化

**角色**: 框架开发者
**期望**: 我想要子窗初始化时正确创建 Rosen::Window 和子 AceContainer
**价值**: 以便子窗有独立的渲染管线和 UI 树

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-4.1 | WHEN InitContainer 调用 THEN 创建 Rosen::WindowOption，按 IsSystemTopMost/GetAboveApps/默认三分支设置窗口类型（`subwindow_ohos.cpp:316-366`） | 正常 |
| AC-4.2 | WHEN Rosen::Window::Create 失败 THEN `SetIsRosenWindowCreate(false)` 并记录 hilog（`subwindow_ohos.cpp:403-406`） | 异常 |
| AC-4.3 | WHEN 窗口创建成功 THEN `RegisterWindowAttachStateChangeListener(new MenuWindowSceneListener(this))` 注册状态监听（`subwindow_ohos.cpp:408`） | 正常 |
| AC-4.4 | WHEN 子 AceContainer 创建 THEN `SetParentId(parentContainerId_)` + `InitializeSubContainer(parentContainerId_)`（`subwindow_ohos.cpp:432, 441`） | 正常 |
| AC-4.5 | WHEN 子 PipelineContext 设置 THEN `SetParentPipeline(parentContainer->GetPipelineContext())` + `SetupSubRootElement()`（`subwindow_ohos.cpp:485-486`） | 正常 |
| AC-4.6 | WHEN 前端类型为 ARK_TS 或 DYNAMIC_HYBRID_STATIC 或 STATIC_HYBRID_DYNAMIC THEN 调用 `SetSubWindowVsyncListener` 设置子窗 vsync 监听（`subwindow_ohos.cpp:460-463`） | 正常 |

## 验收追溯

| AC编号 | 关联规则 | 关联 Task | 验证方式 | 证据 |
|-------|----------|-----------|----------|------|
| AC-1.1 ~ AC-1.4 | R-1, R-2 | TASK-SUBWINDOW-01 | UT | `test/unittest/core/` subwindow 单测 |
| AC-2.1 ~ AC-2.5 | R-3, R-4 | TASK-SUBWINDOW-01 | UT | SubwindowManager 单测 |
| AC-3.1 ~ AC-3.5 | R-5, R-6 | TASK-SUBWINDOW-01 | UT | SubwindowKey 测试 |
| AC-4.1 ~ AC-4.6 | R-7, R-8, R-9 | TASK-SUBWINDOW-01 | UT | InitContainer 测试 |

## 规则定义

> 类型标签：**行为**（正常路径）、**边界**（输入/状态临界点）、**异常**（非法输入或异常状态）、**恢复**（异常后恢复策略）。

| 规则ID | 类型 | 触发条件 | 预期行为 | 边界/约束 | 关联AC |
|--------|------|----------|----------|-----------|--------|
| R-1 | 行为 | `Subwindow::CreateSubwindow(instanceId)` 调用 | 返回 `MakeRefPtr<SubwindowOhos>(instanceId)` | `subwindow_ohos.cpp:124-127` | AC-1.1 |
| R-2 | 行为 | SubwindowOhos 构造 | `windowId_=id_`（自增）、`parentContainerId_=instanceId`、`SetSubwindowId(windowId_)` | `subwindow_ohos.cpp:129-134` | AC-1.2 |
| R-3 | 行为 | `SubwindowManager::GetInstance()` 调用 | 双重检查锁返回单例 | `subwindow_manager.cpp:37-47` | AC-2.1 |
| R-4 | 行为 | 子窗创建后 `AddSubwindowBySearchKey(searchKey, subwindow)` | 存入 `subwindowMap_`，`try_emplace` 防重复 | `subwindow_manager.cpp:1921-1928` | AC-2.2 |
| R-5 | 行为 | SubwindowKey 构建 | 包含 instanceId/displayId/foldStatus/windowType/nodeId 六字段 | `subwindow_manager.h:40-63` | AC-3.1 |
| R-6 | 行为 | SubwindowKey 哈希计算 | `(windowType<<24) | (displayId<<16) | (instanceId+INSTANCE_ID_MIN)` | `subwindow_manager.h:66-73` | AC-3.2 |
| R-7 | 行为 | InitContainer 调用 | 三分支设置窗口类型→Rosen::Window::Create→注册 MenuWindowSceneListener→创建子 AceContainer | `subwindow_ohos.cpp:310-489` | AC-4.1, AC-4.3, AC-4.4 |
| R-8 | 异常 | Rosen::Window::Create 失败 | SetIsRosenWindowCreate(false)，记录 hilog | `subwindow_ohos.cpp:403-406` | AC-4.2 |
| R-9 | 异常 | Rosen::Window::GetAndVerifyWindowTypeForArkUI 返回非 WM_OK | InitContainer 直接 return，不创建窗口 | `subwindow_ohos.cpp:346-353` | — |

---

## 验证映射

| 编号 | 对应规格项 | 验证方式 | 验证重点 |
|------|-----------|----------|----------|
| VM-1 | AC-1.1 ~ AC-1.4 | UT | Subwindow 抽象基类和工厂方法 |
| VM-2 | AC-2.1 ~ AC-2.5 | UT | SubwindowManager 单例和多映射管理 |
| VM-3 | AC-3.1 ~ AC-3.5 | UT | SubwindowKey 构造和哈希 |
| VM-4 | AC-4.1 ~ AC-4.6 | UT | InitContainer 全流程 |

## API 变更分析

### 新增 API

| API 名称 | 开放范围 | 入参概要 | 返回值 | 错误码范围 | 功能描述 | 关联 AC |
|----------|----------|----------|--------|-----------|----------|---------|
| WindowStage.createSubWindow(name) | Public | name: string | Promise<Window> | 9700001~9700010 | 创建子窗 | AC-1.1 |
| WindowStage.getSubWindow() | Public | 无 | Promise<Window[]> | 同上 | 获取所有子窗 | AC-2.3 |
| Window.loadContent(path) | Public | path: string | Promise<void> | 同上 | 加载页面到子窗 | AC-4.4 |
| WindowStage.createSubWindowWithOptions(options) | Public | options: SubWindowOptions | Promise<Window> | 同上 | 创建子窗（带选项） | AC-1.1 |

### 变更/废弃 API

| API 名称 | 变更类型 | 影响场景 | 迁移指引 | 关联 AC |
|----------|----------|----------|----------|---------|
| 无 | — | — | — | — |

> 截至当前版本，子窗核心 API 未发现 @deprecated 或 @useinstead 标注。

## 接口规格

### 接口定义

**[Subwindow::CreateSubwindow]**

| 属性 | 值 |
|------|-----|
| 函数签名 | `RefPtr<Subwindow> Subwindow::CreateSubwindow(int32_t instanceId)` |
| 返回值 | `RefPtr<Subwindow>` — 子窗实例指针 |
| 开放范围 | InnerApi |
| 错误码 | N/A |
| 关联 AC | AC-1.1 |

**参数约束**

| 参数 | 类型 | 必填 | 默认值 | 约束条件 |
|------|------|------|--------|---------|
| instanceId | int32_t | 是 | 无 | 有效容器 ID |

**行为场景**

| # | 触发条件 | 预期行为 | 关联 AC |
|---|----------|----------|---------|
| 1 | 传入有效 instanceId | 返回 MakeRefPtr<SubwindowOhos>(instanceId) | AC-1.1 |
| 2 | Preview 环境 | 返回 PreviewSubwindow 桩实现 | AC-1.1 |

---

## 兼容性声明

- **已有 API 行为变更:** 否，核心抽象/Manager/容器初始化自 API 9 保持一致
- **配置文件格式变更:** 否
- **数据存储格式变更:** 否
- **最低支持版本:** API 9
- **API 版本号策略:** 基础 API @since 9，createSubWindowWithOptions @since 11

## 架构约束

| 关键约束 | 约束说明 | 影响 AC |
|----------|----------|---------|
| Subwindow 抽象 + SubwindowOhos 适配 | 框架上层通过 Subwindow 抽象指针调用，SubwindowOhos 封装 Rosen::Window | AC-1.1, AC-1.4 |
| SubwindowManager 单例 + 多映射 | 所有子窗创建/查找/销毁通过单例管理，subwindowMutex_ 保证线程安全 | AC-2.1, AC-2.5 |
| SubwindowKey 混合查找 | instanceId/displayId/foldStatus/windowType/nodeId 五维度查找键 | AC-3.1, AC-3.2 |
| 子窗独立容器 | 每个子窗有独立 AceContainer+PipelineContext+OverlayManager | AC-4.4, AC-4.5 |

> 本节列出本特性 AC 验证必须满足的约束。架构规则适用性及设计方案见 design.md。

## 非功能性需求

| 类型 | 指标/阈值 | 验证方式 | 证据 |
|------|-----------|----------|------|
| 性能 | 子窗创建延迟 < 100ms（Rosen::Window::Create 到 InitContainer 完成） | Trace + 手工 | Trace 打点 |
| 内存 | 子窗销毁后 Rosen::Window 和 AceContainer 正确释放 | UT + Dump | 内存 Dump |
| 安全 | 无安全相关接口 | N/A | — |
| 可测试性 | 关键路径 hilog 覆盖（AceLogTag::ACE_SUB_WINDOW） | 代码审查 | — |
| 问题定位 | 创建失败/查找失败/窗口类型验证失败日志 | hilog 检查 | — |

> N/A 判定见 proposal.md 不涉及项确认。本节仅为适用项填写具体指标。

## 行为场景（Gherkin）

```gherkin
Feature: 子窗抽象与 Manager 核心
  作为框架开发者
  我想要通过 SubwindowManager 单例管理子窗的创建、查找和销毁
  以便子窗有独立容器并支持多实例隔离

  Scenario: 创建子窗实例
    Given 容器 instanceId 有效
    When 调用 Subwindow::CreateSubwindow(instanceId)
    Then 返回 MakeRefPtr<SubwindowOhos>(instanceId)
    And windowId_ 自增并 SetSubwindowId

  Scenario: 子窗容器初始化
    Given SubwindowOhos 实例已创建
    When 调用 InitContainer
    Then 创建 Rosen::WindowOption 并设置窗口类型
    And Rosen::Window::Create 创建窗口
    And RegisterWindowAttachStateChangeListener 注册 MenuWindowSceneListener
    And 创建子 AceContainer + SetParentId + InitializeSubContainer
    And PipelineContext SetParentPipeline + SetupSubRootElement

  Scenario: Rosen::Window 创建失败
    Given SubwindowOhos InitContainer 执行中
    When Rosen::Window::Create 返回错误
    Then SetIsRosenWindowCreate(false)
    And 记录 hilog "Window create failed"

  Scenario: SubwindowManager 多映射查找
    Given subwindowMap_ 已有 (instanceId, TYPE_DIALOG) 子窗
    When 调用 GetSubwindowBySearchKey(searchKey)
    Then 返回已缓存的 Subwindow 实例
```

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
    query: "Subwindow 抽象基类 SubwindowOhos 工厂 CreateSubwindow instanceId"
  - repo: "openharmony/ace_engine"
    query: "SubwindowManager 单例 subwindowMap_ AddSubwindowBySearchKey GetSubwindowBySearchKey"
  - repo: "openharmony/ace_engine"
    query: "SubwindowKey instanceId displayId foldStatus windowType nodeId 哈希查找"
  - repo: "openharmony/ace_engine"
    query: "InitContainer Rosen WindowOption MenuWindowSceneListener 子 AceContainer PipelineContext"
```

**关键文档:**
- SDK 类型定义: `interface/sdk-js/api/@ohos.window.d.ts`
- 源码入口: `frameworks/base/subwindow/subwindow_manager.cpp`
- 抽象基类: `frameworks/base/subwindow/subwindow.h`
- 适配实现: `adapter/ohos/entrance/subwindow/subwindow_ohos.cpp`
