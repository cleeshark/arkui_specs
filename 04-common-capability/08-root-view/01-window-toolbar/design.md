# 架构设计

> 窗口工具栏（04-08-01）功能域的架构设计文档，补录已有实现。本域聚焦系统窗口容器（ContainerModal）顶部标题栏 + 工具栏项（ToolBarItem）能力，由窗口框架注入而非应用声明；元服务 AppBar（04-08-02）与窗口机制为相关独立域。

## 设计元数据

| 字段 | 内容 |
|------|------|
| Design ID | DESIGN-Func-04-08-01 |
| 关联需求 | 已有能力补录（无独立 requirement.md） |
| 关联 Epic | 无 |
| 目标 Feature | Feat-01 窗口标题栏与工具栏(placement)、Feat-02 @ohos.window.titlebar.component 静态组件与平台接口 |
| 复杂度 | 复杂 |
| 目标版本 | ContainerModal 历史能力；@ohos.window.titlebar.component 随静态前端落地 |
| Owner | ArkUI SIG / 窗口与容器 |
| 状态 | Baselined（已有实现补录；Feat-01/02 已补） |

## 需求基线

| 项 | 内容 |
|----|------|
| 问题陈述 | 多窗口/悬浮窗口场景下，系统需在应用窗口顶部注入统一标题栏（标题可见性/高度、关闭/最小化按钮）与可配置工具栏项（ToolBarItem，按 placement 放入 leading/trailing），供窗口管理与开发者定制窗口 chrome |
| 核心目标 | `ContainerModalPattern`（NG）/`ContainerModalStaticPattern`（静态）承载容器；`ContainerModalToolBar` 排版管理器把 ToolBarItem 按 placement 放入 SideBar/NavBar/NavDest 行；`ToolBarItemPattern` 承载单个工具栏项；`@ohos.window.titlebar.component`（TitleBar/ButtonBar）为静态组件入口；平台层 `UIContentImpl` 提供标题可见性/高度/按钮区域/手势接口 |
| P0 AC | （骨架）ToolBarItem 按 placement（TOP_BAR_LEADING/TRAILING）正确装入对应行；`SetContainerModalTitleVisible/Height` 生效；`OnContainerModalEvent` 正确派发；自定义手势经 `EnableContainerModalCustomGesture` 生效；`@ohos.window.titlebar.component` 静态 abc 正确构建 |

## 上下文和现状

### 涉及仓和模块

| 仓库 | 模块/路径 | 当前职责 | 本 Feature 影响 |
|------|-----------|----------|-----------------|
| ace_engine | `frameworks/core/components_ng/pattern/container_modal/container_modal_toolbar.h/.cpp` | `ContainerModalToolBar`：`InitToolBarManager`，把 ToolBarItem 按 placement 放入 SideBar/NavBar/NavDest 行 | 排版核心 |
| ace_engine | `frameworks/core/components_ng/pattern/container_modal/container_modal_pattern.h/.cpp` | `ContainerModalPattern`：标题高度/可见、按钮 | 容器 Pattern |
| ace_engine | `frameworks/core/components_ng/pattern/container_modal/container_modal_view.h/.cpp` | 标题栏/按钮构建 | 容器视图 |
| ace_engine | `frameworks/core/components_ng/pattern/container_modal/enhance/container_modal_pattern_enhance.h/.cpp` | 增强变体：自定义手势、按钮样式 | 增强 |
| ace_engine | `frameworks/core/components_ng/pattern/container_modal/enhance/container_modal_view_enhance.h/.cpp` | `GetContainerModalTitleVisible`、`SetContainerButtonStyle`、`OnContainerModalEvent` | 增强 |
| ace_engine | `frameworks/core/components_ng/pattern/container_modal/static/container_modal_static_pattern.h/.cpp` | `ContainerModalStaticPattern`（ArkTS 1.2） | 静态变体 |
| ace_engine | `frameworks/core/components_ng/pattern/container_modal/static/source/@ohos.window.titlebar.component.defalut.ets` | `@ohos.window.titlebar.component` 默认 ets（TitleBar/ButtonBar + custombutton/customtitle） | 静态组件源 |
| ace_engine | `frameworks/core/components_ng/pattern/container_modal/static/source/BUILD.gn` | `generate_static_abc("window_titlebar_component_abc")` | 静态 abc 构建 |
| ace_engine | `frameworks/core/components_ng/pattern/toolbaritem/toolbaritem_pattern.h` | `TOOLBARITEM_ETS_TAG="ToolBarItem"`、`ToolBarItemPattern` | 工具栏项 |
| ace_engine | `frameworks/core/components_ng/pattern/toolbaritem/toolbaritem_model_ng.h` | 动态创建入口 | 工具栏项 |
| ace_engine | `frameworks/core/components_ng/pattern/toolbaritem/bridge/*` | 组件化 bridge：dynamic_module/dynamic_modifier/static_modifier/arkts_native_bridge | 工具栏项（组件化） |
| ace_engine | `frameworks/core/components_ng/manager/toolbar/toolbar_manager.h` | `ToolbarManager`（ContainerModal 与 Navigation 共用） | 管理器 |
| ace_engine | `adapter/ohos/osal/dynamic_module_helper.cpp` | `{ "ToolBarItem", "toolbaritem" }` 动态加载映射 | 动态加载 |
| ace_engine | `adapter/ohos/entrance/ui_content_impl.h/.cpp` | `SetContainerModalTitleVisible/Height`、`GetContainerModalButtonsRect`、`SubscribeContainerModalButtonsRectChange`、`EnableContainerModalGesture/CustomGesture`、`OnContainerModalEvent` | 平台入口 |
| ace_engine | `frameworks/core/components/container_modal/*` | Legacy 非 NG 容器（历史） | 仅兼容 |
| ace_engine | `frameworks/bridge/arkts_frontend/koala_projects/arkoala-arkts/arkui-ohos/src/XBarProxy.ts` | `@ohos.window.titlebar.component.System__Reserved_$$$__UI__TitleBar/ButtonBar__Component` 反射类名 + create-func 注册 | 静态前端绑定 |
| sdk-js | `interface/sdk-js/api/@ohos.window.titlebar.component.d.ts` | 静态组件 SDK 声明 | SDK 类型定义 |

### 调用链层级分析

| 层 | 模块 | 职责 | 修改类型 |
|----|------|------|----------|
| 静态组件 SDK/源 | `@ohos.window.titlebar.component` + `.defalut.ets` | TitleBar/ButtonBar 入口；custombutton/customtitle | 存量分析 |
| 静态 abc 构建 | `static/source/BUILD.gn` | `generate_static_abc("window_titlebar_component_abc")` | 存量分析 |
| 容器 Pattern（NG/静态） | `container_modal_pattern`/`container_modal_static_pattern` | 标题/按钮、生命周期 | 存量分析 |
| 排版管理器 | `container_modal_toolbar` | `InitToolBarManager` 按 placement 装填 ToolBarItem | 存量分析 |
| 工具栏项 | `toolbaritem_pattern`/`bridge/*` | ToolBarItem 节点与组件化动态加载 | 存量分析 |
| 平台入口 | `ui_content_impl` | 标题可见性/高度、按钮区域、手势、事件派发 | 存量分析 |

检查项：
- [x] 调用链每层覆盖（SDK/静态组件 → 容器 Pattern → 排版 → 工具栏项 → 平台入口）
- [x] 与 04-08-02 元服务 AppBar、窗口机制的边界已标注

### 适用架构规则

| Rule ID | 适用原因 | 设计结论 | 验证方式 |
|---------|----------|----------|----------|
| OH-ARCH-LAYERING | 系统注入 chrome，非应用声明组件 | 由窗口框架驱动；不出现在应用组件树声明（不在 components.gni 注册为公共 Tag） | 代码评审 |
| OH-ARCH-API-LEVEL | 标题/按钮/手势为系统/inner API；titlebar.component 随静态前端 | @since/系统接口标注 | API 评审 |
| OH-ARCH-COMPONENT-BUILD | container_modal 静态 abc；toolbaritem 组件化 so | 无新增 BUILD target | 构建验证 |
| OH-ARCH-ERROR-LOG | 标题/手势非法参数 | 按 inner API 约定 | 单测 |

## 不涉及项承接

| 维度 | 设计结论 |
|------|----------|
| 元服务 AppBar | 不涉及 — 04-08-02 独立域（InstallationFree 触发的菜单栏） |
| 应用级组件声明 | 不涉及 — ContainerModal/ToolBarItem 不作为应用 `<Tag>` 组件 |
| 跨进程 | 不涉及 — 经窗口框架/OSAL 边界 |
| Navigation toolbar | 不涉及 — `ToolbarManager` 与 Navigation 共用，但 Navigation 用法独立 |

## 关键设计决策

| 决策 ID | 问题 | 推荐方案 | 探索过的替代方案 | 取舍理由 | 影响 |
|---------|------|----------|------------------|----------|------|
| ADR-1 | 注入方式：系统注入 vs 应用声明 | 系统注入（窗口框架经 ContainerModal 注入），非应用组件 | A: 应用声明组件 | 窗口 chrome 由系统统一管理，不应进应用组件树 | 骨架 |
| ADR-2 | 静态组件入口 | `@ohos.window.titlebar.component`（TitleBar/ButtonBar）+ `window_titlebar_component_abc` | A: 仅 NG Pattern | 静态前端（ArkTS 1.2）需独立静态组件入口 | 静态前端 |
| ADR-3 | 工具栏项 placement 模型 | `TOP_BAR_LEADING`/`TOP_BAR_TRAILING` 等 placement，由 `ContainerModalToolBar` 装填 | A: 顺序数组 | placement 明确语义位，便于多区域装填 | 骨架 |
| ADR-4 | ToolBarItem 组件化 | 经 bridge（dynamic_module/modifier）+ `DynamicModuleHelper("ToolBarItem")` 动态加载 | A: 静态链接 | 组件化按需加载，减小主 so | 构建 |
| ADR-5 | 增强变体（手势/样式） | `container_modal_pattern_enhance`/`view_enhance` 独立派生 | A: 并入主 Pattern | 增强（自定义手势/按钮样式）按产品裁剪，独立派生降低基线复杂度 | 骨架 |

## 设计骨架

### 骨架范围

| 骨架项 | 目标 | 不包含 | 验证方式 |
|--------|------|--------|----------|
| 标题栏/工具栏排版 | `ContainerModalToolBar::InitToolBarManager` 按 placement 装填 | 按钮具体样式 | 单测 |
| ToolBarItem 注入 | placement + 动态加载 | Navigation 共用场景 | 单测 |
| 平台标题/手势接口 | `UIContentImpl` 标题/按钮/手势 | connect-server 协议 | 集成测试 |
| 静态组件构建 | `@ohos.window.titlebar.component` abc | custombutton/customtitle 细节 | 构建验证 |

### 骨架 Spec 拆分（候选）

| Task ID | 目标 | 受影响文件 | AC |
|---------|------|------------|----|
| TASK-SKELETON-1 | Feat-01 标题栏/工具栏排版 | container_modal_toolbar, container_modal_pattern, ui_content_impl | AC-1.x（待 Feat 补齐） |
| TASK-SKELETON-2 | Feat-02 ToolBarItem 注入与 placement | toolbaritem_pattern, bridge/*, dynamic_module_helper, toolbar_manager | AC-2.x（待 Feat 补齐） |
| TASK-SKELETON-3 | Feat-03 @ohos.window.titlebar.component 静态组件 | static/source/*, BUILD.gn, XBarProxy.ts | AC-3.x（待 Feat 补齐） |

## 后续 Task 拆分

| Task ID | 目标 | 受影响文件 | 依赖 |
|---------|------|------------|------|
| TASK-1 | Feat-01/02 已有实现补录 | container_modal_*, toolbaritem_*, ui_content_impl, static/source/* | 无 |

## API 签名、Kit 与权限

### 新增 API

无新增。补录已有接口（inner-API 级别）：

| 接口 | 类型 | Kit | d.ts 位置 |
|------|------|-----|-----------|
| `UIContentImpl::SetContainerModalTitleVisible/Height` | InnerApi | arkui | `adapter/ohos/entrance/ui_content_impl.h` |
| `UIContentImpl::GetContainerModalButtonsRect/SubscribeContainerModalButtonsRectChange` | InnerApi | arkui | `adapter/ohos/entrance/ui_content_impl.h` |
| `UIContentImpl::EnableContainerModalCustomGesture/OnContainerModalEvent` | InnerApi | arkui | `adapter/ohos/entrance/ui_content_impl.h` |
| `@ohos.window.titlebar.component`（TitleBar/ButtonBar） | Public | ArkUI | `interface/sdk-js/api/@ohos.window.titlebar.component.d.ts` |

### 变更/废弃 API

无。

## 构建系统影响

### BUILD.gn 变更

无新增 BUILD target。静态组件已注册于 `static/source/BUILD.gn`（`generate_static_abc("window_titlebar_component_abc")`）。ToolBarItem 经 `DynamicModuleHelper("ToolBarItem")` 组件化 so 加载。

### bundle.json 变更

无。

## 详细设计

### ContainerModal 排版管理器

`ContainerModalToolBar::InitToolBarManager` 是排版核心入口（`frameworks/core/components_ng/pattern/container_modal/container_modal_toolbar.cpp:56`），从 `pipeline->GetToolbarManager()`（`frameworks/core/pipeline_ng/pipeline_context.h:885`）取回 `ToolbarManager`。容器行由 `ContainerModalView::Create` 构建（`frameworks/core/components_ng/pattern/container_modal/container_modal_view.cpp:69`），其中标题行 `BuildTitleRow` 用 `ToolBarRowPattern`（同文件 `:137`）。

ToolBarItem 的装入位置按 placement 枚举解析：`ParsePlacementType`（`container_modal_toolbar.cpp:154`）经 `GetItemTypeFromTag`（同文件 `:178`）映射为 `SIDE_BAR_START/END`、`NAV_BAR_START/END`、`NAVDEST_START/END`，再由 `AddToolbarItemToRow`（`:317`）/ `AddToolbarItemToSpecificRow`（`:337`）装入对应行：

| placement | 装入目标 |
|-----------|----------|
| `SIDE_BAR_START/END` | SideBar 前导/尾随区 |
| `NAV_BAR_START/END` | NavBar 前导/尾随区 |
| `NAVDEST_START/END` | NavDest 前导/尾随区 |

`ToolBarItem` 由 `DynamicModuleHelper::GetDynamicModule("ToolBarItem")` 动态加载对应组件 so（`frameworks/core/interfaces/native/implementation/tool_bar_item_modifier.cpp:29`），`ToolBarItemPattern` 承接属性更新，模型入口为 `ToolBarItemModelNG::Create`（`frameworks/core/components_ng/pattern/toolbaritem/toolbaritem_model_ng.cpp:26`）。`ToolbarManager` 由 `PipelineContext` 持有（`frameworks/core/pipeline_ng/pipeline_context.h:1539`），为 ContainerModal 与 Navigation 共用。

### 平台标题栏接口

`UIContentImpl`（`adapter/ohos/entrance/ui_content_impl.cpp`）提供 4 组标题栏控制方法，均作用于当前 ContainerModal：

- `SetContainerModalTitleVisible(bool, bool)` — 控制标题栏显示/隐藏（`ui_content_impl.cpp:5681`，转发至 `ContainerModalPattern::SetContainerModalTitleVisible`，`frameworks/core/components_ng/pattern/container_modal/container_modal_pattern.cpp:597`）
- `SetContainerModalTitleHeight(int32_t)` — 设置标题高度（`ui_content_impl.cpp:5707`）
- `GetContainerModalButtonsRect()` / `SubscribeContainerModalButtonsRectChange` — 按钮区域矩形查询与变化订阅（`ui_content_impl.cpp:5760` / `:5775`，按钮区计算在 `frameworks/core/components_ng/manager/avoid_info/avoid_info_manager.cpp:137`）
- `EnableContainerModalCustomGesture` / `OnContainerModalEvent` — 增强变体手势与事件（`ui_content_impl.cpp:6644` / `:6049`）

### 静态组件构建

`@ohos.window.titlebar.component.defalut.ets`（`frameworks/core/components_ng/pattern/container_modal/static/source/@ohos.window.titlebar.component.defalut.ets`）提供 TitleBar/ButtonBar 默认实现，经 `generate_static_abc` 产出 abc 随静态前端加载。`ContainerModalStaticPattern/View/Bridge`（`frameworks/core/components_ng/pattern/container_modal/static/container_modal_static_pattern.cpp`、`container_modal_static_view.cpp`、`container_modal_static_bridge.cpp`）承载静态范式容器。Arkoala 侧 `XBarProxy`（`frameworks/bridge/arkts_frontend/koala_projects/arkoala-arkts/arkui-ohos/src/XBarProxy.ts:43`）经 `frontend->InitXBarProxy()`（`frameworks/core/common/frontend.h:486`）注册 create-func。

## 风险和开放问题

| 项 | 类型 | 影响 | 处理方式 | Owner |
|----|------|------|----------|-------|
| 系统注入 chrome 不在 components.gni | 架构 | 低 — 易被误认为缺失 | 文档标注系统注入模型 | ArkUI SIG |
| 增强变体产品裁剪差异 | 功能 | 中 — 手势/样式按产品不同 | enhance 独立派生 | ArkUI SIG |
| ToolbarManager 与 Navigation 共用 | 边界 | 低 — 共用管理器语义需明确 | Feat 规格标注 | ArkUI SIG |
| 静态组件文件名拼写（.defalut.ets） | 维护 | 低 — 历史拼写 | 保持兼容，不擅自改名 | ArkUI SIG |

## 设计审批

- [x] 需求基线已确认，设计覆盖 P0 骨架 AC
- [x] 不涉及项已承接（元服务 AppBar/应用组件/Navigation）
- [x] 涉及仓和模块职责清楚
- [x] 调用链层级分析完整
- [x] 适用架构规则已识别并形成设计结论
- [x] 关键设计决策有理由和影响说明
- [x] 风险和开放问题有 Owner
- [x] Feat 规格已补齐（Feat-01/02 已 Baselined）

**结论:** Baselined（已有实现补录，Feat-01/02 已补）
