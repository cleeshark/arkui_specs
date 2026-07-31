# 特性规格

## 概述

| 字段 | 内容 |
|------|------|
| 特性名称 | AtomicServiceBar 编程 API |
| 特性编号 | Func-04-08-02-Feat-02 |
| 所属 Epic | 无 |
| 优先级 | P2 |
| 目标版本 | AtomicServiceBar API 随 UIContext 落地 |
| SIG 归属 | ArkUI SIG |
| 状态 | Baselined |
| 复杂度 | 一般 |

本特性补录元服务 AppBar 的对外编程能力。三入口：NAPI 模块 `atomicservicebar`（setVisible/setBackgroundColor/setTitleContent/setTitleFontStyle/setIconColor/getBarRect/onBarRectChange）、C-API `OH_ArkUI_NativeModule_AtomicServiceMenuBarSetVisible`（经 `atomic_service_modifier`，InstallationFree 守卫）、`UIContext.getAtomicServiceBar()` accessor（getBarRect 等）。本文档只描述当前实现。

## 本次变更范围（Delta）

| 类型 | 内容 | 说明 |
|------|------|------|
| ADDED | `specs/04-common-capability/08-root-view/02-atomic-service-appbar/Feat-02-atomic-service-bar-api-spec.md` | 新增 AtomicServiceBar API 规格。 |
| MODIFIED | `specs/index.md` | 注册 Feat-02。 |
| REMOVED | 无 | — |

## 输入文档

- 设计文档：`specs/04-common-capability/08-root-view/02-atomic-service-appbar/design.md`
- 知识库：`docs/kb/capabilities/atomic-service-appbar.md`
- 主要源码定位：
  - `interfaces/napi/kits/atomic_service_bar/js_atomic_service_bar.cpp`（NAPI `atomicservicebar`）
  - `frameworks/core/interfaces/native/node/atomic_service_modifier.h` / `.cpp`、`interfaces/native/node/node_utils.cpp`（C-API `AtomicServiceMenuBarSetVisible`）
  - `frameworks/core/interfaces/native/implementation/ui_context_atomic_service_bar_accessor.cpp`（UIContextAtomicServiceBarAccessor）
  - `frameworks/bridge/declarative_frontend/jsview/js_app_bar_view.cpp`（JSAppBar 动态绑定）
  - `frameworks/bridge/arkts_frontend/.../@ohos.arkui.UIContext.ts`、`UIContextImpl.ets`、`arkui-custom.idl`（静态前端 AtomicServiceBar）

## 用户故事

### US-1: 菜单可见性控制

**作为** 元服务开发者,
**我想要** 控制元服务菜单栏可见性,
**以便** 按需显示/隐藏菜单按钮。

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-1.1 | WHEN NAPI `setVisible(visible)` THEN 菜单栏可见性按值生效 | 正常 |
| AC-1.2 | WHEN C-API `OH_ArkUI_NativeModule_AtomicServiceMenuBarSetVisible` 且 InstallationFree THEN 经 `atomic_service_modifier.setMenuBarVisible` 生效 | 正常 |
| AC-1.3 | WHEN 非 InstallationFree 调 setMenuBarVisible THEN 守卫判定后静默无效 | 边界 |

### US-2: 样式与内容设置

**作为** 元服务开发者,
**我想要** 经编程 API 设置 AppBar 样式与内容,
**以便** 菜单栏视觉与文案可按需定制。

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-2.1 | WHEN `setBackgroundColor/setTitleContent/setTitleFontStyle/setIconColor` THEN 对应样式/内容更新 | 正常 |
| AC-2.2 | WHEN 静态前端经 UIContext.getAtomicServiceBar() THEN 走 `AtomicServiceBarInternal`（UIContextImpl.ets） | 正常 |

### US-3: 区域矩形与回调

**作为** 元服务开发者,
**我想要** 查询 AppBar 区域矩形并订阅其变化,
**以便** 适配布局并响应窗口 chrome 尺寸变化。

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-3.1 | WHEN `getBarRect()` THEN 返回 AppBar 矩形（经 UIContextAtomicServiceBarAccessor / AppBarView::GetAppBarRect） | 正常 |
| AC-3.2 | WHEN `onBarRectChange(cb)` THEN 经 AppBarView rect-change listener 订阅区域变化 | 正常 |
| AC-3.3 | WHEN AppBar 为 null THEN getBarRect accessor 返回默认/空（见 capi accessor 测试 getBarRectTestAppBarNull） | 边界 |

---

## 验收追溯

| AC | 关联规则 | 关联 Task | 验证方式 | 证据 |
|----|----------|-----------|----------|------|
| AC-1.1~1.3 | R-1~R-3 | 已有实现 | 代码评审 | `js_atomic_service_bar.cpp`、`atomic_service_modifier.cpp`、`node_utils.cpp` |
| AC-2.1~2.2 | R-4, R-5 | 已有实现 | 代码评审 | `js_atomic_service_bar.cpp`、`UIContextImpl.ets` |
| AC-3.1~3.3 | R-6~R-8 | 已有实现 | C-API 单测 + 代码评审 | `ui_context_atomic_service_bar_accessor_test.cpp`、`app_bar_view.cpp` |

---

## 规则定义

| 规则ID | 类型 | 触发条件 | 预期行为 | 边界/约束 | 关联AC |
|--------|------|----------|----------|-----------|--------|
| R-1 | 行为 | NAPI setVisible | 菜单可见性生效 | — | AC-1.1 |
| R-2 | 行为 | C-API setMenuBarVisible + InstallationFree | atomic_service_modifier.setMenuBarVisible | — | AC-1.2 |
| R-3 | 边界 | 非 InstallationFree | 守卫后静默无效 | — | AC-1.3 |
| R-4 | 行为 | setBackground/Title/FontStyle/Icon | 样式/内容更新 | — | AC-2.1 |
| R-5 | 行为 | 静态前端 getAtomicServiceBar | AtomicServiceBarInternal | — | AC-2.2 |
| R-6 | 行为 | getBarRect | 返回 AppBar 矩形 | accessor + GetAppBarRect | AC-3.1 |
| R-7 | 行为 | onBarRectChange | rect-change listener 订阅 | — | AC-3.2 |
| R-8 | 边界 | AppBar null | getBarRect 返回默认/空 | — | AC-3.3 |

---

## 验证映射

| 编号 | 对应规格项 | 验证方式 | 验证重点 |
|------|------------|----------|----------|
| VM-1 | AC-1.1~1.3, R-1~R-3 | 代码评审 | NAPI/C-API setVisible 与 InstallationFree 守卫 |
| VM-2 | AC-2.1~2.2, R-4~R-5 | 代码评审 | 样式/内容、静态前端路径 |
| VM-3 | AC-3.1~3.3, R-6~R-8 | C-API 单测（ui_context_atomic_service_bar_accessor_test.cpp） | getBarRect/onBarRectChange/null |

---

## API 变更分析

### 新增 API

无新增（补录已有）。已有接口表：

| API | 开放范围 | 入参 | 返回值 | 错误码 |
|-----|----------|------|--------|--------|
| `atomicservicebar.setVisible` | Public | `boolean` | `void` | — |
| `atomicservicebar.setBackgroundColor` | Public | `Color` | `void` | — |
| `atomicservicebar.setTitleContent` | Public | `string` | `void` | — |
| `atomicservicebar.setTitleFontStyle` | Public | `FontStyle` | `void` | — |
| `atomicservicebar.setIconColor` | Public | `Color` | `void` | — |
| `atomicservicebar.getBarRect` | Public | `void` | `Rect` | — |
| `atomicservicebar.onBarRectChange` | Public | `callback` | `void` | — |
| `OH_ArkUI_NativeModule_AtomicServiceMenuBarSetVisible` | Public NDK | `bool visible` | `int32_t` | 非 InstallationFree 静默 |
| `UIContext.getAtomicServiceBar()` | Public | `void` | `AtomicServiceBar` | — |

### 变更/废弃 API

无。

## 接口规格

### 接口定义

| 接口 | 签名 | 说明 |
|------|------|------|
| NAPI | `atomicservicebar.setVisible/setBackgroundColor/setTitleContent/setTitleFontStyle/setIconColor/getBarRect/onBarRectChange` | 模块 `atomicservicebar` |
| C-API | `OH_ArkUI_NativeModule_AtomicServiceMenuBarSetVisible` | node_utils + atomic_service_modifier |
| UIContext | `getAtomicServiceBar(): AtomicServiceBar` | accessor getBarRect 等 |

## 兼容性声明

| 维度 | 声明 |
|------|------|
| 向后兼容 | 完全兼容（补录） |
| InstallationFree | 非 InstallationFree 调 setMenuBarVisible 静默无效（R-3） |

## 架构约束

| 约束 | 说明 |
|------|------|
| 多入口 | NAPI / C-API / UIContext 三范式 |
| 守卫 | InstallationFree 守卫贯穿 |

## 非功能性需求

| 项 | 要求 |
|----|------|
| 线程安全 | UI 线程 |
| 错误处理 | 非 InstallationFree 静默（不报错） |

## 多设备适配声明

通用；元服务场景驱动。

## 全局特性影响

无全局影响。

## Spec 自审清单

- [x] 用户故事与 AC 覆盖正常/边界
- [x] AC 可追溯到源码证据（含 C-API accessor 单测）
- [x] 非 InstallationFree 静默行为已标注（R-3）
- [x] 无占位符
- [x] SDK d.ts 验证：`@ohos.arkui.UIContext.d.ts` 中 `AtomicServiceBar` 接口及 `getAtomicServiceBar()` 已确认

## context-references

```yaml
context-queries:
  - repo: "openharmony/ace_engine"
    query: "atomicservicebar setVisible setBackgroundColor setTitleContent getBarRect onBarRectChange NAPI"
  - repo: "openharmony/ace_engine"
    query: "OH_ArkUI_NativeModule_AtomicServiceMenuBarSetVisible atomic_service_modifier UIContextAtomicServiceBarAccessor"
```

**关键文档：** `js_atomic_service_bar.cpp`、`atomic_service_modifier.h/.cpp`、`node_utils.cpp`、`ui_context_atomic_service_bar_accessor.cpp`、`js_app_bar_view.cpp`、`UIContextImpl.ets`
