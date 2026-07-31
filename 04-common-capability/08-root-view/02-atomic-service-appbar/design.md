# 架构设计

> 元服务 AppBar（04-08-02）功能域的架构设计文档，补录已有实现。本域聚焦免安装元服务（atomic service / installation-free）顶部菜单栏 chrome；窗口工具栏（04-08-01）与窗口机制为相关独立域。

## 设计元数据

| 字段 | 内容 |
|------|------|
| Design ID | DESIGN-Func-04-08-02 |
| 关联需求 | 已有能力补录（无独立 requirement.md） |
| 关联 Epic | 无 |
| 目标 Feature | Feat-01 AppBar 构建与 AtomicServicePattern、Feat-02 AtomicServiceBar API(NAPI/C-API/UIContext) |
| 复杂度 | 复杂 |
| 目标版本 | 元服务（InstallationFree）历史能力；AtomicServiceBar API 随 UIContext 落地 |
| Owner | ArkUI SIG / 窗口与容器 |
| 状态 | Baselined（已有实现补录；Feat-01/02 已补） |

## 需求基线

| 项 | 内容 |
|----|------|
| 问题陈述 | 免安装元服务需在顶部注入统一菜单栏（菜单按钮/分割线/关闭按钮），并提供菜单可见性、标题、图标、背景色、区域矩形及变化回调等编程能力，供元服务管理与 UI 适配 |
| 核心目标 | `AppBarView`（构建工厂：BuildAppbar/RegistAppBarNodeBuilder/OnMenuClick/OnCloseClick/GetAppBarRect/SetMenuBarVisible）+ `AtomicServicePattern`（LinearLayoutPattern 派生，颜色/布局更新、安全区回调、返回按压）+ `AtomicServiceLayoutAlgorithm`（避让/overlay）；由 `pipeline->GetInstallationFree()` 触发自动构建；对外经 NAPI `atomicservicebar`、C-API `OH_ArkUI_NativeModule_AtomicServiceMenuBarSetVisible`、`UIContext.getAtomicServiceBar()` 暴露 |
| P0 AC | （骨架）元服务场景下 AppBar 自动构建；`setVisible/setTitleContent/setBackgroundColor/setIconColor/getBarRect/onBarRectChange` 生效；C-API `AtomicServiceMenuBarSetVisible` 经 InstallationFree 守卫；安全区/避让经 `AtomicServiceLayoutAlgorithm` 正确处理 |

## 上下文和现状

### 涉及仓和模块

| 仓库 | 模块/路径 | 当前职责 | 本 Feature 影响 |
|------|-----------|----------|-----------------|
| ace_engine | `frameworks/core/components_ng/pattern/app_bar/app_bar_view.h/.cpp` | `AppBarView : Referenced`：BuildAppbar、RegistAppBarNodeBuilder、OnMenuClick、OnCloseClick、GetAppBarRect、SetMenuBarVisible、rect-change 监听 | 构建工厂 |
| ace_engine | `frameworks/core/components_ng/pattern/app_bar/atomic_service_pattern.h/.cpp` | `AtomicServicePattern : LinearLayoutPattern`：颜色/布局更新、安全区回调、`SetIsAtomicService(true)`、返回按压、FireAbilityCloseEvent | 容器 Pattern |
| ace_engine | `frameworks/core/components_ng/pattern/app_bar/atomic_service_layout_algorithm.h/.cpp` | `AtomicServiceLayoutAlgorithm`：避让/overlay 布局 | 布局算法 |
| ace_engine | `frameworks/core/components_ng/pattern/app_bar/app_bar_theme.h` | `AppBarTheme` | 主题 |
| ace_engine | `frameworks/core/components_ng/pattern/app_bar/app_bar_utils.h/.cpp` | AppBar 辅助 | 辅助 |
| ace_engine | `frameworks/core/components_ng/pattern/app_bar/source/custom_app_bar.ets` | 自定义 app-bar ArkTS 源 | 自定义 |
| ace_engine | `frameworks/core/components_ng/pattern/custom/custom_app_bar_node.h/.cpp` | `CustomAppBarNode : CustomNode`（ARKUI_APP_BAR_*/ARKUI_MENU_BAR_VISIBLE/ARKUI_ABILITY_CLOSE_EVENT 回调） | 自定义节点 |
| ace_engine | `frameworks/core/common/app_bar_helper.h` | `AppBarHelper::QueryAppGalleryBundleName()` | 平台查询 |
| ace_engine | `adapter/ohos/osal/app_bar_helper_impl.cpp` | OHOS 实现 QueryAppGalleryBundleName | 平台 |
| ace_engine | `interfaces/napi/kits/atomic_service_bar/js_atomic_service_bar.cpp` | NAPI `atomicservicebar`：setVisible/setBackgroundColor/setTitleContent/setTitleFontStyle/setIconColor/getBarRect/onBarRectChange | NAPI |
| ace_engine | `frameworks/core/interfaces/native/node/atomic_service_modifier.h/.cpp` | `GetAtomicServiceModifier`；`.setMenuBarVisible`，`pipeline->GetInstallationFree()` 守卫 | C-API modifier |
| ace_engine | `interfaces/native/node/node_utils.cpp` | `OH_ArkUI_NativeModule_AtomicServiceMenuBarSetVisible` | C-API 入口 |
| ace_engine | `frameworks/core/interfaces/native/implementation/ui_context_atomic_service_bar_accessor.cpp` | `UIContextAtomicServiceBarAccessor`（getBarRect 等） | C-API accessor |
| ace_engine | `frameworks/bridge/declarative_frontend/jsview/js_app_bar_view.cpp/.h` | `JSAppBar`（"ContainerAppBar"）事件：OnMenuClick/OnCloseClick/OnBackPressed/OnDidBuild 等 | 动态前端绑定 |
| ace_engine | `frameworks/core/common/container.h/.cpp` | `Container::GetAppBar()`/`SetAppBar(...)` | 容器 plumbing |
| ace_engine | `frameworks/bridge/declarative_frontend/frontend_delegate_declarative.cpp` | `NG::AppBarView::BuildAppbar(...)` 触发 | 构建触发 |
| ace_engine | `frameworks/bridge/arkts_frontend/.../@ohos.arkui.UIContext.ts` / `UIContextImpl.ets` | `interface AtomicServiceBar`、`getAtomicServiceBar()`、`AtomicServiceBarInternal` | 静态前端 |
| ace_engine | `frameworks/bridge/arkts_frontend/arkoala_generator/arkui_extra_idl/arkui-custom.idl` | `interface UIContextAtomicServiceBar` | IDL |
| ace_engine | `frameworks/bridge/declarative_frontend/engine/jsUIContext.js` | `getAtomicServiceBar()` 动态 shim、`AtomicServiceBar` 类 | 动态 shim |
| sdk-js | `interface/sdk-js/api/@ohos.arkui.UIContext.d.ts` | UIContext.getAtomicServiceBar()/AtomicServiceBar | SDK 类型定义 |

### 调用链层级分析

| 层 | 模块 | 职责 | 修改类型 |
|----|------|------|----------|
| SDK d.ts/d.ets | `@ohos.arkui.UIContext.*` / `atomicservicebar` | AtomicServiceBar 方法签名 + NAPI 模块 | 存量分析 |
| NAPI 模块 | `js_atomic_service_bar.cpp` | setVisible/setTitle*/setBackgroundColor/setIconColor/getBarRect/onBarRectChange | 存量分析 |
| C-API | `node_utils.cpp` + `atomic_service_modifier` | `AtomicServiceMenuBarSetVisible`→modifier.setMenuBarVisible（InstallationFree 守卫） | 存量分析 |
| C-API accessor | `ui_context_atomic_service_bar_accessor.cpp` | UIContextAtomicServiceBarAccessor.getBarRect 等 | 存量分析 |
| 动态前端绑定 | `js_app_bar_view.cpp` | JSAppBar 事件绑定（ContainerAppBar） | 存量分析 |
| 静态前端 | `@ohos.arkui.UIContext.ts` / `UIContextImpl.ets` | AtomicServiceBar 接口与内部实现 | 存量分析 |
| 构建工厂 | `app_bar_view.cpp` | BuildAppbar 组装 AtomicService(Column)>JsView>Stage+MenuBarRow>MenuBar | 存量分析 |
| 容器 Pattern | `atomic_service_pattern.cpp` | 颜色/布局更新、安全区、返回按压、SetIsAtomicService | 存量分析 |
| 布局算法 | `atomic_service_layout_algorithm.cpp` | 避让/overlay | 存量分析 |
| 构建触发 | `frontend_delegate_declarative.cpp` | `AppBarView::BuildAppbar` 触发 | 存量分析 |
| 平台查询 | `app_bar_helper_impl.cpp` | QueryAppGalleryBundleName | 存量分析 |

检查项：
- [x] 调用链每层覆盖（SDK → NAPI/C-API/静态前端 → 构建 → Pattern/布局 → 平台）
- [x] 与 04-08-01 窗口工具栏、窗口机制、安全区边界已标注

### 适用架构规则

| Rule ID | 适用原因 | 设计结论 | 验证方式 |
|---------|----------|----------|----------|
| OH-ARCH-LAYERING | 系统注入 chrome（InstallationFree 触发），非应用声明 | 由 pipeline GetInstallationFree 守卫自动构建；不在 components.gni 注册 | 代码评审 |
| OH-ARCH-API-LEVEL | AtomicServiceBar 为 Public（UIContext）；setMenuBarVisible C-API | @since/系统接口标注 | API 评审/XTS |
| OH-ARCH-COMPONENT-BUILD | NAPI 模块 `atomicservicebar`；C-API modifier/accessor | 无新增 BUILD target | 构建验证 |
| OH-ARCH-ERROR-LOG | 非 InstallationFree 场景 setMenuBarVisible 静默无效 | 守卫判定后静默返回 | 单测 |

## 不涉及项承接

| 维度 | 设计结论 |
|------|----------|
| 窗口工具栏 | 不涉及 — 04-08-01 独立域（ContainerModal 标题栏） |
| 应用级组件声明 | 不涉及 — AppBarView/AtomicServicePattern 非应用 `<Tag>` 组件 |
| AppGallery 集成 | 仅边界 — `AppBarHelper::QueryAppGalleryBundleName` 查询包名，集成在 OSAL 外 |
| 跨进程 | 不涉及 — 元服务关闭经 FireAbilityCloseEvent 回调 |

## 关键设计决策

| 决策 ID | 问题 | 推荐方案 | 探索过的替代方案 | 取舍理由 | 影响 |
|---------|------|----------|------------------|----------|------|
| ADR-1 | 触发条件 | `pipeline->GetInstallationFree()` 守卫：仅元服务场景自动 BuildAppbar | A: 全场景注入 | 非元服务不应出现菜单栏；守卫精确控制 | 骨架 |
| ADR-2 | AppBar 构建主体 | `AppBarView`（Referenced 工厂）+ `AtomicServicePattern`（LinearLayoutPattern）双角色 | A: 单一 Pattern | 构建逻辑（工厂）与状态/布局（Pattern）分离，职责清晰 | 骨架 |
| ADR-3 | 对外能力暴露 | 多入口：NAPI `atomicservicebar` + C-API modifier/accessor + UIContext.getAtomicServiceBar() | A: 仅 NAPI | 不同范式（动态/NDK/静态）需各自入口 | API 矩阵 |
| ADR-4 | 自定义 AppBar | `CustomAppBarNode : CustomNode` + `RegistAppBarNodeBuilder`（CJ/ArkTS builder 注册） | A: 不支持自定义 | 元服务需可注入自定义 AppBar 内容 | 骨架 |
| ADR-5 | 安全区/避让 | `AtomicServiceLayoutAlgorithm` overlay 布局 + `AtomicServicePattern` 安全区回调 + `SetIsAtomicService(true)` | A: 复用通用避让 | 元服务避让规则与普通应用不同，需独立算法 | 骨架 |

## 设计骨架

### 骨架范围

| 骨架项 | 目标 | 不包含 | 验证方式 |
|--------|------|--------|----------|
| AppBar 构建 | BuildAppbar 组装菜单/分割线/关闭 + JS 绑定 | MenuBar 具体样式 | 单测 |
| AtomicServicePattern 状态 | 颜色/安全区/返回按压 | 避让算法细节 | 单测 |
| 避让/overlay | AtomicServiceLayoutAlgorithm | 多窗口叠加 | 单测 |
| API 暴露 | NAPI/C-API/UIContext 三入口 | 各字段单位 | XTS |

### 骨架 Spec 拆分（候选）

| Task ID | 目标 | 受影响文件 | AC |
|---------|------|------------|----|
| TASK-SKELETON-1 | Feat-01 AppBar 构建与生命周期 | app_bar_view, atomic_service_pattern, frontend_delegate_declarative, js_app_bar_view | AC-1.x（待 Feat 补齐） |
| TASK-SKELETON-2 | Feat-02 AtomicServiceBar API | js_atomic_service_bar, atomic_service_modifier, node_utils, ui_context_atomic_service_bar_accessor, UIContext.ts/Impl.ets | AC-2.x（待 Feat 补齐） |
| TASK-SKELETON-3 | Feat-03 安全区/避让与自定义 AppBar | atomic_service_layout_algorithm, custom_app_bar_node, app_bar_helper | AC-3.x（待 Feat 补齐） |

## 后续 Task 拆分

| Task ID | 目标 | 受影响文件 | 依赖 |
|---------|------|------------|------|
| TASK-1 | Feat-01/02 已有实现补录 | app_bar_*, atomic_service_*, js_atomic_service_bar, atomic_service_modifier, ui_context_atomic_service_bar_accessor, UIContext.* | 无 |

## API 签名、Kit 与权限

### 新增 API

无新增。补录已有接口：

| 接口 | 类型 | Kit | d.ts 位置 |
|------|------|-----|-----------|
| `AtomicServiceBar.setVisible/setTitleContent/setBackgroundColor/setIconColor/getBarRect/onBarRectChange` | Public | ArkUI | `interface/sdk-js/api/@ohos.arkui.UIContext.d.ts` |
| `UIContext.getAtomicServiceBar()` | Public | ArkUI | `interface/sdk-js/api/@ohos.arkui.UIContext.d.ts` |
| `OH_ArkUI_NativeModule_AtomicServiceMenuBarSetVisible` | Public NDK | ArkUI | `interfaces/native/node/node_utils.h` |
| `UIContentAtomicServiceBarAccessor` | Public NDK | ArkUI | `frameworks/core/interfaces/native/implementation/ui_context_atomic_service_bar_accessor.h` |

### 变更/废弃 API

无。

## 构建系统影响

### BUILD.gn 变更

无新增 BUILD target。NAPI 模块 `atomicservicebar`、C-API modifier/accessor 均已注册。自定义 AppBar 经 `source/custom_app_bar.ets` 静态资源构建。

### bundle.json 变更

无。

## 详细设计

### AppBar 构建流程

元服务启动时，`pipeline->GetInstallationFree()` 返回 true 触发 `AppBarView::BuildAppbar`（`frameworks/core/components_ng/pattern/app_bar/app_bar_view.cpp:204`，InstallationFree 守卫见同文件 `:571`）。构建树为 `AtomicService(Column) > JsView > Stage+MenuBarRow > MenuBar`：

```
AtomicService (Column, AtomicServicePattern)
  ├── JsView (应用内容)
  └── Stage+MenuBarRow
       └── MenuBar (菜单按钮 | 分割线 | 关闭按钮)
```

`AtomicServicePattern` 继承 `LinearLayoutPattern`（`frameworks/core/components_ng/pattern/app_bar/atomic_service_pattern.h:26`），管理颜色/布局更新、安全区回调、`SetIsAtomicService(true)` 标记（`atomic_service_pattern.cpp:64`）和返回按压 `FireAbilityCloseEvent`（同文件 `:564`）。`AtomicServiceLayoutAlgorithm`（`frameworks/core/components_ng/pattern/app_bar/atomic_service_layout_algorithm.cpp`）实现避让/overlay 布局算法。

### 对外 API 入口

三入口并行：

| 入口 | 模块 | 方法 |
|------|------|------|
| NAPI | `interfaces/napi/kits/atomic_service_bar/js_atomic_service_bar.cpp` | `setVisible/setBackgroundColor/setTitleContent/setTitleFontStyle/setIconColor/getBarRect/onBarRectChange`（注册于同文件 `:306`-`:312`） |
| C-API | `frameworks/core/interfaces/native/node/atomic_service_modifier.cpp`、`interfaces/native/node/node_utils.cpp` | `OH_ArkUI_NativeModule_AtomicServiceMenuBarSetVisible`（`node_utils.cpp:1009`，InstallationFree 守卫） |
| C-API accessor | `frameworks/core/interfaces/native/implementation/ui_context_atomic_service_bar_accessor.cpp` | `getBarRect` 等方法 |
| 静态前端 | `@ohos.arkui.UIContext.ts`, `UIContextImpl.ets` | `AtomicServiceBar` 接口 + `getAtomicServiceBar()` |

`UIContext.getAtomicServiceBar()` 经 `UIContextAtomicServiceBarAccessor` 返回 `AtomicServiceBar` 实例，用于 Query/Event 操作。

### 自定义 AppBar

`CustomAppBarNode : CustomNode`（`frameworks/core/components_ng/pattern/custom/custom_app_bar_node.h`）支持 `AppBarView::RegistAppBarNodeBuilder`（`frameworks/core/components_ng/pattern/app_bar/app_bar_view.cpp:103`）注册 CJ/ArkTS builder，构建自定义菜单栏内容。`AppBarHelper::QueryAppGalleryBundleName`（同文件 `:80`，各平台 OSAL 实现）为平台查询入口。

## 风险和开放问题

| 项 | 类型 | 影响 | 处理方式 | Owner |
|----|------|------|----------|-------|
| 非 InstallationFree 静默无效 | 功能 | 中 — 开发者无感知 | 守卫后静默；建议文档/日志提示 | ArkUI SIG |
| 自定义 AppBar builder 跨前端注册 | 兼容 | 中 — CJ/ArkTS builder 注册点需对齐 | RegistAppBarNodeBuilder 注册审计 | ArkUI SIG |
| 安全区与通用避让差异 | 功能 | 中 — 元服务避让易错 | 独立算法 + SetIsAtomicService 标记 | ArkUI SIG |
| AppBarView 非 Pattern（Referenced） | 架构 | 低 — 双角色易混淆 | 文档标注工厂/Pattern 职责 | ArkUI SIG |

## 设计审批

- [x] 需求基线已确认，设计覆盖 P0 骨架 AC
- [x] 不涉及项已承接（窗口工具栏/应用组件/AppGallery 集成/跨进程）
- [x] 涉及仓和模块职责清楚
- [x] 调用链层级分析完整
- [x] 适用架构规则已识别并形成设计结论
- [x] 关键设计决策有理由和影响说明
- [x] 风险和开放问题有 Owner
- [x] Feat 规格已补齐（Feat-01/02 已 Baselined）

**结论:** Baselined（已有实现补录，Feat-01/02 已补）
