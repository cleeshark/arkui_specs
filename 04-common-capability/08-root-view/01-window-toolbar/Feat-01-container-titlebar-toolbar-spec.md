# 特性规格

## 概述

| 字段 | 内容 |
|------|------|
| 特性名称 | 窗口标题栏与工具栏 |
| 特性编号 | Func-04-08-01-Feat-01 |
| 所属 Epic | 无 |
| 优先级 | P2 |
| 目标版本 | ContainerModal 历史能力（多窗口/浮窗） |
| SIG 归属 | ArkUI SIG |
| 状态 | Baselined |
| 复杂度 | 复杂 |

本特性补录系统窗口容器（ContainerModal）顶部标题栏 + 工具栏项（ToolBarItem）排版能力。`ContainerModalPattern`（NG）/`ContainerModalStaticPattern`（静态）承载容器；`ContainerModalToolBar::InitToolBarManager` 把 ToolBarItem 按 placement（TOP_BAR_LEADING/TRAILING 等）装入 SideBar/NavBar/NavDest 行；`ToolBarItemPattern` 承载单项。容器为系统注入 chrome，非应用声明组件。本文档只描述当前实现。

## 本次变更范围（Delta）

| 类型 | 内容 | 说明 |
|------|------|------|
| ADDED | `specs/04-common-capability/08-root-view/01-window-toolbar/design.md` | 新增功能域基线设计。 |
| ADDED | `specs/04-common-capability/08-root-view/01-window-toolbar/Feat-01-container-titlebar-toolbar-spec.md` | 新增窗口标题栏与工具栏规格。 |
| MODIFIED | `specs/index.md` | 链接 design.md，注册 Feat-01。 |
| REMOVED | 无 | — |

## 输入文档

- 设计文档：`specs/04-common-capability/08-root-view/01-window-toolbar/design.md`
- 知识库：`docs/kb/capabilities/window-toolbar.md`
- 主要源码定位：
  - `frameworks/core/components_ng/pattern/container_modal/container_modal_toolbar.cpp` / `.h`（`ContainerModalToolBar`）
  - `frameworks/core/components_ng/pattern/container_modal/container_modal_pattern.cpp` / `.h`
  - `frameworks/core/components_ng/pattern/container_modal/container_modal_view.h`
  - `frameworks/core/components_ng/pattern/container_modal/enhance/container_modal_pattern_enhance.cpp`、`container_modal_view_enhance.h`（手势/按钮样式）
  - `frameworks/core/components_ng/pattern/toolbaritem/toolbaritem_pattern.h`、`toolbaritem_model_ng.h`
  - `frameworks/core/components_ng/manager/toolbar/toolbar_manager.h`
  - `adapter/ohos/entrance/ui_content_impl.cpp` / `.h`（标题可见性/高度/按钮区域/手势）

## 用户故事

### US-1: 工具栏项按 placement 装填

**作为** 窗口框架,
**我想要** 把 ToolBarItem 按 placement 装入对应行（leading/trailing）,
**以便** 多窗口/浮窗顶部工具栏正确排版。

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-1.1 | WHEN `ContainerModalToolBar::InitToolBarManager()` THEN 按 placement 把 ToolBarItem 装入 SideBar/NavBar/NavDest 行 | 正常 |
| AC-1.2 | WHEN placement=`TOP_BAR_LEADING` THEN 装入前导区；`TOP_BAR_TRAILING` 装入尾随区 | 正常 |
| AC-1.3 | WHEN ToolBarItem 经 `DynamicModuleHelper("ToolBarItem")` 动态加载 THEN 独立组件 so 正确加载 | 边界 |

### US-2: 标题栏可见性/高度与按钮区域

**作为** 窗口框架,
**我想要** 查询并控制 ContainerModal 标题栏可见性、高度与按钮区域,
**以便** 应用窗口 chrome 状态可控并可感知按钮区域变化。

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-2.1 | WHEN `SetContainerModalTitleVisible(visible)` THEN 标题栏可见性按值生效 | 正常 |
| AC-2.2 | WHEN `SetContainerModalTitleHeight(h)` THEN 标题高度生效 | 正常 |
| AC-2.3 | WHEN `GetContainerModalButtonsRect()` / `SubscribeContainerModalButtonsRectChange` THEN 返回/订阅按钮区域 | 正常 |

### US-3: 自定义手势与事件派发

**作为** 窗口框架,
**我想要** 开启 ContainerModal 自定义手势并接收容器事件,
**以便** 增强变体可注入手势交互并统一派发窗口 chrome 事件。

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-3.1 | WHEN `EnableContainerModalCustomGesture` 开启 THEN 增强变体（`container_modal_pattern_enhance`）处理自定义手势 | 正常 |
| AC-3.2 | WHEN `OnContainerModalEvent(name, value)` THEN 经 `ContainerModalViewEnhance::OnContainerModalEvent` 派发 | 正常 |

---

## 验收追溯

| AC | 关联规则 | 关联 Task | 验证方式 | 证据 |
|----|----------|-----------|----------|------|
| AC-1.1~1.3 | R-1~R-3 | 已有实现 | 单测 + 代码评审 | `container_modal_toolbar_test_ng.cpp`、`dynamic_module_helper.cpp` |
| AC-2.1~2.3 | R-4~R-6 | 已有实现 | 单测 + 代码评审 | `container_modal_test_ng.cpp`、`ui_content_impl.cpp` |
| AC-3.1~3.2 | R-7, R-8 | 已有实现 | 单测 | `container_modal_pattern_enhance_test_ng.cpp` |

---

## 规则定义

| 规则ID | 类型 | 触发条件 | 预期行为 | 边界/约束 | 关联AC |
|--------|------|----------|----------|-----------|--------|
| R-1 | 行为 | InitToolBarManager | 按 placement 装填 ToolBarItem | — | AC-1.1 |
| R-2 | 行为 | placement LEADING/TRAILING | 装入对应区域 | — | AC-1.2 |
| R-3 | 边界 | ToolBarItem 动态加载 | DynamicModuleHelper 映射 toolbaritem | — | AC-1.3 |
| R-4 | 行为 | SetContainerModalTitleVisible | 标题可见性生效 | — | AC-2.1 |
| R-5 | 行为 | SetContainerModalTitleHeight | 标题高度生效 | — | AC-2.2 |
| R-6 | 行为 | GetContainerModalButtonsRect/Subscribe | 返回/订阅按钮区域 | — | AC-2.3 |
| R-7 | 行为 | EnableContainerModalCustomGesture | 增强变体处理手势 | 产品裁剪相关 | AC-3.1 |
| R-8 | 行为 | OnContainerModalEvent | 经 ViewEnhance 派发 | — | AC-3.2 |

---

## 验证映射

| 编号 | 对应规格项 | 验证方式 | 验证重点 |
|------|------------|----------|----------|
| VM-1 | AC-1.1~1.3, R-1~R-3 | 单测（container_modal_toolbar_*_test_ng.cpp 系列） | placement 装填、动态加载 |
| VM-2 | AC-2.1~2.3, R-4~R-6 | 单测 + 代码评审 | 标题可见性/高度、按钮区域 |
| VM-3 | AC-3.1~3.2, R-7, R-8 | 单测（enhance 测试） | 自定义手势、事件派发 |

---

## API 变更分析

### 新增 API

无新增（补录已有）。已有接口表：

| API | 开放范围 | 入参 | 返回值 | 错误码 |
|-----|----------|------|--------|--------|
| `UIContentImpl::SetContainerModalTitleVisible` | InnerApi | `bool visible` | `void` | 非法参数 |
| `UIContentImpl::SetContainerModalTitleHeight` | InnerApi | `int32_t height` | `void` | 非法参数 |
| `UIContentImpl::GetContainerModalButtonsRect` | InnerApi | 无 | `Rect` | — |
| `UIContentImpl::SubscribeContainerModalButtonsRectChange` | InnerApi | `callback` | `void` | — |
| `UIContentImpl::EnableContainerModalCustomGesture` | InnerApi | `bool enable` | `void` | — |
| `UIContentImpl::OnContainerModalEvent` | InnerApi | `string name, string value` | `void` | — |

### 变更/废弃 API

无。

## 接口规格

### 接口定义

| 接口 | 签名 | 说明 |
|------|------|------|
| inner-API | `UIContentImpl::SetContainerModalTitleVisible/Height`、`GetContainerModalButtonsRect`、`SubscribeContainerModalButtonsRectChange`、`EnableContainerModalGesture/CustomGesture`、`OnContainerModalEvent` | 平台入口 |
| 内部 | `ContainerModalToolBar::InitToolBarManager` | 排版 |

## 兼容性声明

| 维度 | 声明 |
|------|------|
| 向后兼容 | 完全兼容（补录） |
| 系统注入 | ContainerModal/ToolBarItem 非应用 `<Tag>` 组件，不出现在 components.gni |

## 架构约束

| 约束 | 说明 |
|------|------|
| 注入模型 | 由窗口框架注入，非应用声明 |
| 组件化 | ToolBarItem 经 bridge 动态加载 |

## 非功能性需求

| 项 | 要求 |
|----|------|
| 线程安全 | UI 线程 |
| 产品裁剪 | 增强变体（手势/样式）按产品配置 |

## 多设备适配声明

通用窗口/浮窗；多窗口/折叠屏由窗口框架驱动。

## 全局特性影响

无全局影响。

## Spec 自审清单

- [x] 用户故事与 AC 覆盖正常/边界
- [x] AC 可追溯到源码证据
- [x] 系统注入模型明确
- [x] 无占位符
- [x] SDK d.ts 验证：`@ohos.window.titlebar.component.d.ts` 存在于 `interface/sdk-js/api/`，TitleBar/ButtonBar 类型声明已确认

## context-references

```yaml
context-queries:
  - repo: "openharmony/ace_engine"
    query: "ContainerModalToolBar InitToolBarManager ToolBarItem placement TOP_BAR_LEADING TRAILING"
  - repo: "openharmony/ace_engine"
    query: "SetContainerModalTitleVisible Height GetContainerModalButtonsRect EnableContainerModalCustomGesture"
```

**关键文档：** `container_modal_toolbar.cpp/.h`、`container_modal_pattern.cpp`、`container_modal_view_enhance.h`、`toolbaritem_pattern.h`、`ui_content_impl.cpp`
