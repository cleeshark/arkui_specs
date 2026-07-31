# 特性规格

## 概述

| 字段 | 内容 |
|------|------|
| 特性名称 | @ohos.window.titlebar.component 静态组件与构建 |
| 特性编号 | Func-04-08-01-Feat-02 |
| 所属 Epic | 无 |
| 优先级 | P2 |
| 目标版本 | ArkTS 1.2 静态前端 |
| SIG 归属 | ArkUI SIG |
| 状态 | Baselined |
| 复杂度 | 一般 |

本特性补录静态前端窗口标题栏组件入口 `@ohos.window.titlebar.component`（TitleBar/ButtonBar）。仓内默认源 `@ohos.window.titlebar.component.defalut.ets` + custombutton/customtitle，经 `generate_static_abc("window_titlebar_component_abc")` 产物 abc；Arkoala 经 `XBarProxy.ts` 反射类名注册 create-func。容器静态变体由 `ContainerModalStaticPattern`/`ContainerModalStaticView` 承载。本文档只描述当前实现。

## 本次变更范围（Delta）

| 类型 | 内容 | 说明 |
|------|------|------|
| ADDED | `specs/04-common-capability/08-root-view/01-window-toolbar/Feat-02-titlebar-static-component-spec.md` | 新增静态组件规格。 |
| MODIFIED | `specs/index.md` | 注册 Feat-02。 |
| REMOVED | 无 | — |

## 输入文档

- 设计文档：`specs/04-common-capability/08-root-view/01-window-toolbar/design.md`
- 知识库：`docs/kb/capabilities/window-toolbar.md`
- 主要源码定位：
  - `frameworks/core/components_ng/pattern/container_modal/static/source/@ohos.window.titlebar.component.defalut.ets`、`custombutton.ets`、`customtitle.ets`
  - `frameworks/core/components_ng/pattern/container_modal/static/source/BUILD.gn`（`generate_static_abc("window_titlebar_component_abc")`）
  - `frameworks/core/components_ng/pattern/container_modal/static/container_modal_static_pattern.cpp`、`container_modal_static_view.cpp`、`container_modal_static_bridge.cpp`
  - `frameworks/bridge/arkts_frontend/koala_projects/arkoala-arkts/arkui-ohos/src/XBarProxy.ts`（反射类名 + create-func）

## 用户故事

### US-1: 静态组件入口与产物

**作为** 静态前端,
**我想要** 经 `@ohos.window.titlebar.component` 获取 TitleBar/ButtonBar,
**以便** 静态范式下统一窗口标题栏渲染。

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-1.1 | WHEN 构建运行 THEN `@ohos.window.titlebar.component.defalut.ets` 提供 TitleBar/ButtonBar 入口 | 正常 |
| AC-1.2 | WHEN `generate_static_abc("window_titlebar_component_abc")` THEN 产出 `window_titlebar_component_abc.abc` | 正常 |
| AC-1.3 | WHEN 支持 custombutton/customtitle THEN 经对应 ets 源提供自定义按钮/标题 | 边界 |

### US-2: Arkoala 反射注册

**作为** 静态前端运行时,
**我想要** 经 Arkoala 反射类名注册 TitleBar/ButtonBar 的 create-func,
**以便** 静态组件在 Arkoala 上下文中可被正确创建与调用。

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-2.1 | WHEN Arkoala 注册 THEN `XBarProxy.ts` 用反射类名（`...TitleBar__Component`/`...ButtonBar__Component`） | 正常 |
| AC-2.2 | WHEN 注册 create-func THEN 经 `_XBar_Set_ComponentCreateFunc` + native bridge `_XBar_Call_Native` | 正常 |

### US-3: 静态容器变体

**作为** 静态前端,
**我想要** 由静态容器变体承载 titlebar 组件树并桥接前后端,
**以便** 静态范式下窗口 chrome 完整可用。

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-3.1 | WHEN 静态范式容器 THEN 由 `ContainerModalStaticPattern`/`ContainerModalStaticView` 承载 | 正常 |
| AC-3.2 | WHEN 经 `container_modal_static_bridge` THEN 桥接静态前后端 | 正常 |

---

## 验收追溯

| AC | 关联规则 | 关联 Task | 验证方式 | 证据 |
|----|----------|-----------|----------|------|
| AC-1.1~1.3 | R-1~R-3 | 已有实现 | 构建验证 + 代码评审 | `static/source/*.ets`、`BUILD.gn` |
| AC-2.1~2.2 | R-4, R-5 | 已有实现 | 代码评审 | `XBarProxy.ts` |
| AC-3.1~3.2 | R-6 | 已有实现 | 单测 | `container_modal_static_pattern_test.cpp`、`container_modal_static_view_test.cpp` |

---

## 规则定义

| 规则ID | 类型 | 触发条件 | 预期行为 | 边界/约束 | 关联AC |
|--------|------|----------|----------|-----------|--------|
| R-1 | 行为 | defalut.ets | 提供 TitleBar/ButtonBar 入口 | 历史拼写 .defalut 保持 | AC-1.1 |
| R-2 | 行为 | generate_static_abc | 产出 window_titlebar_component_abc.abc | — | AC-1.2 |
| R-3 | 边界 | custombutton/customtitle | 自定义按钮/标题源 | — | AC-1.3 |
| R-4 | 行为 | XBarProxy 反射类名 | TitleBar/ButtonBar Component 反射注册 | — | AC-2.1 |
| R-5 | 行为 | create-func 注册 | Set_ComponentCreateFunc + _XBar_Call_Native | — | AC-2.2 |
| R-6 | 行为 | 静态容器 | ContainerModalStaticPattern/View/Bridge 承载 | — | AC-3.1, AC-3.2 |

---

## 验证映射

| 编号 | 对应规格项 | 验证方式 | 验证重点 |
|------|------------|----------|----------|
| VM-1 | AC-1.1~1.3, R-1~R-3 | 构建验证 + 代码评审 | 静态组件入口/abc 产物/自定义源 |
| VM-2 | AC-2.1~2.2, R-4~R-5 | 代码评审 | Arkoala 反射注册 |
| VM-3 | AC-3.1~3.2, R-6 | 单测（static 测试） | 静态容器变体 |

---

## API 变更分析

### 新增 API

无新增（补录已有）。已有接口表：

| API | 开放范围 | 入参 | 返回值 | 错误码 |
|-----|----------|------|--------|--------|
| `@ohos.window.titlebar.component` (TitleBar) | Public | 标准 Component 入参 | `void` | — |
| `@ohos.window.titlebar.component` (ButtonBar) | Public | 标准 Component 入参 | `void` | — |
| CustomButton/CustomTitle | Public | 自定义样式参数 | `void` | — |

### 变更/废弃 API

无。

## 接口规格

### 接口定义

| 接口 | 签名 | 说明 |
|------|------|------|
| 静态组件 | `@ohos.window.titlebar.component`（TitleBar/ButtonBar） | SDK 声明在外部 sdk-js 仓 |
| 仓内源 | `@ohos.window.titlebar.component.defalut.ets` | 默认实现 |
| abc 产物 | `window_titlebar_component_abc.abc` | generate_static_abc |

## 兼容性声明

| 维度 | 声明 |
|------|------|
| 向后兼容 | 完全兼容（补录） |
| 命名 | `.defalut.ets` 为历史拼写，保持不擅自改名 |

## 架构约束

| 约束 | 说明 |
|------|------|
| 静态前端 | Arkoala 反射 + abc 产物 |
| 静态容器 | ContainerModalStatic* 承载 |

## 非功能性需求

| 项 | 要求 |
|----|------|
| 构建 | abc 产物随静态前端构建 |

## 多设备适配声明

通用。

## 全局特性影响

无全局影响。

## Spec 自审清单

- [x] 用户故事与 AC 覆盖正常/边界
- [x] AC 可追溯到源码证据
- [x] 历史拼写（.defalut）已标注不擅自改
- [x] 无占位符
- [x] SDK d.ts 验证：`@ohos.window.titlebar.component.d.ts` 存在于 `interface/sdk-js/api/`，TitleBar/ButtonBar 类型声明已确认

## context-references

```yaml
context-queries:
  - repo: "openharmony/ace_engine"
    query: "@ohos.window.titlebar.component defalut.ets TitleBar ButtonBar generate_static_abc"
  - repo: "openharmony/ace_engine"
    query: "XBarProxy TitleBar ButtonBar ComponentCreateFunc ContainerModalStaticPattern"
```

**关键文档：** `static/source/@ohos.window.titlebar.component.defalut.ets`、`static/source/BUILD.gn`、`container_modal_static_pattern.cpp`、`XBarProxy.ts`
