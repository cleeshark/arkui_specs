# 特性规格

## 概述

| 字段 | 内容 |
|------|------|
| 特性名称 | AppBar 构建与 AtomicServicePattern |
| 特性编号 | Func-04-08-02-Feat-01 |
| 所属 Epic | 无 |
| 优先级 | P2 |
| 目标版本 | 元服务（InstallationFree）历史能力 |
| SIG 归属 | ArkUI SIG |
| 状态 | Baselined |
| 复杂度 | 复杂 |

本特性补录元服务顶部菜单栏 chrome 的构建与状态管理。`AppBarView`（Referenced 工厂）`BuildAppbar` 组装 `AtomicService(Column) > JsView > Stage + MenuBarRow > MenuBar(menuButton/divider/closeButton)`；`AtomicServicePattern`（LinearLayoutPattern 派生）处理颜色/布局更新、安全区回调、返回按压、`SetIsAtomicService(true)`；`AtomicServiceLayoutAlgorithm` 处理避让/overlay。由 `pipeline->GetInstallationFree()` 守卫触发自动构建。本文档只描述当前实现。

## 本次变更范围（Delta）

| 类型 | 内容 | 说明 |
|------|------|------|
| ADDED | `specs/04-common-capability/08-root-view/02-atomic-service-appbar/design.md` | 新增功能域基线设计。 |
| ADDED | `specs/04-common-capability/08-root-view/02-atomic-service-appbar/Feat-01-appbar-build-pattern-spec.md` | 新增 AppBar 构建与 Pattern 规格。 |
| MODIFIED | `specs/index.md` | 链接 design.md，注册 Feat-01。 |
| REMOVED | 无 | — |

## 输入文档

- 设计文档：`specs/04-common-capability/08-root-view/02-atomic-service-appbar/design.md`
- 知识库：`docs/kb/capabilities/atomic-service-appbar.md`
- 主要源码定位：
  - `frameworks/core/components_ng/pattern/app_bar/app_bar_view.cpp` / `.h`（`AppBarView`：BuildAppbar/RegistAppBarNodeBuilder/OnMenuClick/OnCloseClick/GetAppBarRect/SetMenuBarVisible）
  - `frameworks/core/components_ng/pattern/app_bar/atomic_service_pattern.cpp` / `.h`（`AtomicServicePattern`）
  - `frameworks/core/components_ng/pattern/app_bar/atomic_service_layout_algorithm.cpp` / `.h`
  - `frameworks/core/components_ng/pattern/custom/custom_app_bar_node.h` / `.cpp`（`CustomAppBarNode`）
  - `frameworks/core/common/app_bar_helper.h`、`adapter/ohos/osal/app_bar_helper_impl.cpp`（QueryAppGalleryBundleName）
  - `frameworks/bridge/declarative_frontend/frontend_delegate_declarative.cpp`（`AppBarView::BuildAppbar` 触发）

## 用户故事

### US-1: 元服务 AppBar 自动构建

**作为** 元服务,
**我想要** 在 InstallationFree 场景自动获得顶部菜单栏,
**以便** 统一元服务窗口 chrome（菜单/分割线/关闭）。

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-1.1 | WHEN `pipeline->GetInstallationFree()` 为真 THEN 触发 `AppBarView::BuildAppbar` 自动构建 | 正常 |
| AC-1.2 | WHEN 非 InstallationFree THEN 不构建 AppBar | 边界 |
| AC-1.3 | WHEN BuildAppbar THEN 组装 AtomicService(Column)>JsView>Stage+MenuBarRow>MenuBar(menuButton/divider/closeButton) | 正常 |
| AC-1.4 | WHEN `RegistAppBarNodeBuilder` 注册 builder THEN 支持 CJ/ArkTS 自定义 AppBar 节点构建 | 边界 |

### US-2: 状态、安全区与关闭流程

**作为** 元服务运行时,
**我想要** AppBar 状态、安全区与关闭流程按元服务规则管理,
**以便** 元服务窗口 chrome 正确避让、刷新并响应关闭/菜单操作。

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-2.1 | WHEN `AtomicServicePattern` 初始化 THEN `SetIsAtomicService(true)` 标记，颜色/布局按元服务规则更新 | 正常 |
| AC-2.2 | WHEN 安全区变化 THEN 经 `AtomicServicePattern` 安全区回调 + `AtomicServiceLayoutAlgorithm` overlay/避让 | 正常 |
| AC-2.3 | WHEN 点关闭/菜单 THEN `OnCloseClick`/`OnMenuClick` 触发，`RequestAtomicServiceTerminate`/`FireAbilityCloseEvent`（ARKUI_ABILITY_CLOSE_EVENT） | 正常 |
| AC-2.4 | WHEN `AppBgColorCallBack` THEN 按元服务背景色规则更新 | 正常 |

---

## 验收追溯

| AC | 关联规则 | 关联 Task | 验证方式 | 证据 |
|----|----------|-----------|----------|------|
| AC-1.1~1.4 | R-1~R-4 | 已有实现 | 单测 + 代码评审 | `app_bar_test_ng.cpp`、`frontend_delegate_declarative.cpp`、`app_bar_view.cpp` |
| AC-2.1~2.4 | R-5~R-8 | 已有实现 | 单测 | `atomic_service_pattern_*_test.cpp`、`app_bar_layout_algorithm_test.cpp` |

---

## 规则定义

| 规则ID | 类型 | 触发条件 | 预期行为 | 边界/约束 | 关联AC |
|--------|------|----------|----------|-----------|--------|
| R-1 | 行为 | GetInstallationFree=true | 触发 BuildAppbar | — | AC-1.1 |
| R-2 | 边界 | 非 InstallationFree | 不构建 | — | AC-1.2 |
| R-3 | 行为 | BuildAppbar | 组装 menuButton/divider/closeButton 树 | — | AC-1.3 |
| R-4 | 边界 | RegistAppBarNodeBuilder | 支持自定义 AppBar 节点 | — | AC-1.4 |
| R-5 | 行为 | AtomicServicePattern 初始化 | SetIsAtomicService(true)，颜色/布局更新 | — | AC-2.1 |
| R-6 | 行为 | 安全区变化 | 安全区回调 + LayoutAlgorithm overlay | — | AC-2.2 |
| R-7 | 行为 | OnCloseClick/OnMenuClick | RequestAtomicServiceTerminate/FireAbilityCloseEvent | ARKUI_ABILITY_CLOSE_EVENT | AC-2.3 |
| R-8 | 行为 | AppBgColorCallBack | 背景色更新 | — | AC-2.4 |

---

## 验证映射

| 编号 | 对应规格项 | 验证方式 | 验证重点 |
|------|------------|----------|----------|
| VM-1 | AC-1.1~1.4, R-1~R-4 | 单测（app_bar_test_ng.cpp）+ 代码评审 | InstallationFree 触发、构建树、自定义 builder |
| VM-2 | AC-2.1~2.4, R-5~R-8 | 单测（atomic_service_pattern_*_test.cpp、layout_algorithm_test） | 状态/安全区/关闭/颜色 |

---

## API 变更分析

### 新增 API

无新增（补录已有内部能力）。已有接口表：

| API | 开放范围 | 入参 | 返回值 | 错误码 |
|-----|----------|------|--------|--------|
| `AppBarView::BuildAppbar` | 内部 | `pipeline context` | `void` | — |
| `AppBarView::OnMenuClick` | 内部 | `void` | `void` | — |
| `AppBarView::OnCloseClick` | 内部 | `void` | `void` | — |
| `AtomicServicePattern` | 内部 | — | — | — |
| `AtomicServiceLayoutAlgorithm` | 内部 | — | — | — |

### 变更/废弃 API

无。

## 接口规格

### 接口定义

| 接口 | 签名 | 说明 |
|------|------|------|
| 内部 | `AppBarView::BuildAppbar(...)` | 构建工厂 |
| 内部 | `AtomicServicePattern : LinearLayoutPattern` | 状态/布局 |
| 内部 | `AtomicServiceLayoutAlgorithm` | 避让/overlay |
| 外部依赖 | `AppBarHelper::QueryAppGalleryBundleName()` | 经 IBundleMgr IPC（见 design.md 外部依赖入口） |

## 兼容性声明

| 维度 | 声明 |
|------|------|
| 向后兼容 | 完全兼容（补录） |
| 系统注入 | AppBarView/AtomicServicePattern 非应用 `<Tag>` 组件，不在 components.gni |

## 架构约束

| 约束 | 说明 |
|------|------|
| 注入模型 | InstallationFree 守卫自动构建 |
| 双角色 | AppBarView（工厂）+ AtomicServicePattern（状态） |
| 外部依赖 | AppGallery 包名经 bundle_framework IBundleMgr（IPC） |

## 非功能性需求

| 项 | 要求 |
|----|------|
| 线程安全 | UI 线程 |
| 避让 | 元服务独立避让规则（非通用） |

## 多设备适配声明

通用；元服务场景由 InstallationFree 标记驱动。

## 全局特性影响

无全局影响。

## Spec 自审清单

- [x] 用户故事与 AC 覆盖正常/边界
- [x] AC 可追溯到源码证据
- [x] 系统注入模型与外部依赖（AppGallery/bundle）明确
- [x] 无占位符
- [x] SDK d.ts 验证：`@ohos.arkui.UIContext.d.ts` 中 `AtomicServiceBar` 接口及 `getAtomicServiceBar()` 已确认

## context-references

```yaml
context-queries:
  - repo: "openharmony/ace_engine"
    query: "AppBarView BuildAppbar AtomicServicePattern InstallationFree SetIsAtomicService"
  - repo: "openharmony/ace_engine"
    query: "AtomicServiceLayoutAlgorithm OnCloseClick RequestAtomicServiceTerminate FireAbilityCloseEvent AppBgColorCallBack"
```

**关键文档：** `app_bar_view.cpp/.h`、`atomic_service_pattern.cpp/.h`、`atomic_service_layout_algorithm.cpp`、`custom_app_bar_node.h`、`app_bar_helper_impl.cpp`
