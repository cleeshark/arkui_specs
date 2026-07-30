# 特性规格

> Func-04-03-05-Feat-01 弹窗类属性：固化 bindPopup/bindMenu/bindContextMenu 及其变体的绑定、显示、子窗路由与布局避让行为规格。

## 概述

| 属性 | 值 |
|------|-----|
| 特性名称 | 弹窗类属性 (Popup Attributes) |
| 特性编号 | Func-04-03-05-Feat-01 |
| 所属 Epic | 无（已有能力补录） |
| 优先级 | P0 |
| 目标版本 | API 7 起支持，API 12/23/26 持续扩展 |
| SIG 归属 | ArkUI SIG |
| 状态 | Baselined |
| 复杂度 | 中等 |

## 本次变更范围（Delta）

> 历史规格补齐，补录已有实现的完整行为规格。

| 类型 | 内容 | 说明 |
|------|------|------|
| ADDED | bindPopup/bindMenu/bindContextMenu 全量行为 | 补录通用弹窗属性绑定行为 |

## 输入文档

| 文档 | 路径 | 状态 |
|------|------|------|
| Design | `specs/04-common-capability/03-common-attributes/05-popup-attributes/design.md` | Baselined |
| SDK API | `interface/sdk-js/api/@internal/component/ets/common.d.ts` | — |

---

## 用户故事

### US-1: 绑定 popup 气泡

**作为** 应用开发者,
**我想要** 通过 `bindPopup(show, popup)` 将气泡弹窗绑定到任意组件,
**以便** 在组件附近显示提示信息或自定义内容。

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-1.1 | WHEN 调用 `bindPopup(true, popup)` 且 popup 含 `message` THEN 创建 PopupOptions 类型气泡，通过 OverlayManager::ShowPopup 显示 | 正常 |
| AC-1.2 | WHEN popup 含 `builder` THEN 创建 CustomPopupOptions 类型气泡，通过 ScopedViewStackProcessor 构建自定义节点 | 正常 |
| AC-1.3 | WHEN `show` 为 `{$value}` 对象 THEN 通过 ParseDoubleBindCallback 解析双向绑定 | 正常 |
| AC-1.4 | WHEN `IsShowInSubWindow()` 为 true THEN 走 SubwindowManager::GetSubwindowByType(TYPE_POPUP) 子窗路径 | 边界 |
| AC-1.5 | WHEN 目标组件销毁 THEN PushDestroyCallbackWithTag 清理 popup 节点 | 恢复 |

### US-2: 绑定 menu 菜单

**作为** 应用开发者,
**我想要** 通过 `bindMenu(content, options?)` 将菜单绑定到任意组件,
**以便** 触发时显示菜单项列表。

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-2.1 | WHEN content 为 `Array<MenuElement>` THEN 走 BindMenuWithItems，通过 createWithOptionParams 创建 | 正常 |
| AC-2.2 | WHEN content 为 CustomBuilder THEN 走 BindMenuWithCustomNode，通过 ScopedViewStackProcessor 构建自定义节点 | 正常 |
| AC-2.3 | WHEN API >= 10 THEN 默认 placement 设为 BOTTOM_LEFT | 边界 |
| AC-2.4 | WHEN content 为 boolean(isShow) 双向绑定 THEN 支持命令式显示/隐藏 | 正常 |
| AC-2.5 | WHEN CONTEXT_MENU 类型 THEN 始终走子窗显示 | 边界 |

### US-3: 绑定 contextMenu 上下文菜单

**作为** 应用开发者,
**我想要** 通过 `bindContextMenu` 绑定长按/右键触发的上下文菜单,
**以便** 提供上下文操作菜单。

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-3.1 | WHEN responseType 为 LONG_PRESS THEN 注册 BindContextMenuWithLongPress，鼠标长按不支持 | 正常 |
| AC-3.2 | WHEN responseType 为 RIGHT_CLICK THEN 注册 BindContextMenuWithRightClick | 正常 |
| AC-3.3 | WHEN 使用 isShown 变体(@since 12) THEN contextMenuRegisterType=CUSTOM_TYPE，placement=BOTTOM_LEFT | 边界 |
| AC-3.4 | WHEN 使用 WithResponse 变体(@since 23) THEN 同时注册 RIGHT_CLICK 与 LONG_PRESS | 正常 |
| AC-3.5 | WHEN preview 为 IMAGE/CustomBuilder THEN 即使 enableArrow=true 也不显示箭头 | 边界 |
| AC-3.6 | WHEN 按 KEY_MENU/INTENTION_MENU THEN RegisterContextMenuKeyEvent 触发 BindMenuWithCustomNode | 正常 |

---

## 验收追溯

| AC编号 | US ID | 关联规则 | 验证手段 |
|-------|-------|----------|----------|
| AC-1.1 | US-1 | R-1 | 代码审查 view_abstract.cpp:4615-4772 |
| AC-1.2 | US-1 | R-2 | 代码审查 js_popups.cpp:2021-2072 |
| AC-1.3 | US-1 | R-3 | 代码审查 js_popups.cpp ParseDoubleBindCallback |
| AC-1.4 | US-1 | R-4 | 代码审查 view_abstract.cpp:4639 |
| AC-1.5 | US-1 | R-22 | 代码审查 view_abstract.cpp:4706-4726 |
| AC-2.1 | US-2 | R-5 | 代码审查 view_abstract.cpp:5382-5426 |
| AC-2.2 | US-2 | R-6 | 代码审查 view_abstract.cpp:5428-5478 |
| AC-2.3 | US-2 | R-7 | 代码审查 js_popups.cpp:3357-3362 |
| AC-2.4 | US-2 | R-8 | 代码审查 js_popups.cpp:3293-3355 |
| AC-2.5 | US-2 | R-9 | 代码审查 view_abstract.cpp:5404-5407 |
| AC-3.1 | US-3 | R-10 | 代码审查 view_abstract_model_ng.cpp:530 |
| AC-3.2 | US-3 | R-11 | 代码审查 view_abstract_model_ng.cpp:591 |
| AC-3.3 | US-3 | R-12 | 代码审查 view_abstract_model_ng.cpp:345 |
| AC-3.4 | US-3 | R-13 | 代码审查 view_abstract_model_ng.cpp:936-961 |
| AC-3.5 | US-3 | R-14 | 代码审查 menu_property.h previewMode |
| AC-3.6 | US-3 | R-15 | 代码审查 view_abstract_model_ng.cpp:1158-1182 |

## 规则定义

| 规则ID | 类型 | 触发条件 | 预期行为 | 边界/约束 | 关联AC |
|--------|------|----------|----------|-----------|--------|
| R-1 | 行为 | bindPopup(show=true, PopupOptions) | 通过 OverlayManager::ShowPopup 显示含 message 的气泡 | `view_abstract.cpp:4615-4772` | AC-1.1 |
| R-2 | 行为 | bindPopup(show=true, CustomPopupOptions) | 通过 ScopedViewStackProcessor 构建自定义节点 | `js_popups.cpp:2064-2068` | AC-1.2 |
| R-3 | 行为 | show 为 {$value} 对象 | ParseDoubleBindCallback 解析双向绑定 | `js_popups.cpp:2021-2072` | AC-1.3 |
| R-4 | 边界 | IsShowInSubWindow()=true | 走 SubwindowManager::GetSubwindowByType(TYPE_POPUP) | `view_abstract.cpp:4639` | AC-1.4 |
| R-5 | 行为 | bindMenu(Array<MenuElement>) | BindMenuWithItems → createWithOptionParams | `view_abstract.cpp:5382-5426` | AC-2.1 |
| R-6 | 行为 | bindMenu(CustomBuilder) | BindMenuWithCustomNode → ScopedViewStackProcessor | `view_abstract.cpp:5428-5478` | AC-2.2 |
| R-7 | 边界 | API>=10 | 默认 placement=BOTTOM_LEFT | `js_popups.cpp:3357-3362` | AC-2.3 |
| R-8 | 行为 | bindMenu(isShow boolean) | 支持双向绑定命令式显示/隐藏 | `js_popups.cpp:3293-3355` | AC-2.4 |
| R-9 | 边界 | CONTEXT_MENU 类型 | 始终走子窗显示 | `view_abstract.cpp:5404-5407` | AC-2.5 |
| R-10 | 行为 | responseType=LONG_PRESS | BindContextMenuWithLongPress 注册 | 鼠标长按不支持 `view_abstract_model_ng.cpp:530` | AC-3.1 |
| R-11 | 行为 | responseType=RIGHT_CLICK | BindContextMenuWithRightClick 注册 | `view_abstract_model_ng.cpp:591` | AC-3.2 |
| R-12 | 边界 | isShown 变体(@since 12) | contextMenuRegisterType=CUSTOM_TYPE, placement=BOTTOM_LEFT | `view_abstract_model_ng.cpp:345` | AC-3.3 |
| R-13 | 行为 | WithResponse 变体(@since 23) | 同时注册 RIGHT_CLICK+LONG_PRESS | `view_abstract_model_ng.cpp:936-961` | AC-3.4 |
| R-14 | 边界 | preview=IMAGE/CustomBuilder | 不显示 arrow 即使 enableArrow=true | `menu_property.h:112-226` | AC-3.5 |
| R-15 | 行为 | KEY_MENU/INTENTION_MENU 按键 | RegisterContextMenuKeyEvent → BindMenuWithCustomNode | placement=BOTTOM_LEFT `view_abstract_model_ng.cpp:1158-1182` | AC-3.6 |
| R-16 | 异常 | bindPopup 时 overlayManager 为 null | CHECK_NULL_VOID 直接返回 | `view_abstract.cpp:4619` | AC-1.1 |
| R-17 | 异常 | bindMenu params 为空且 buildFunc 为空 | BindMenuWithCustomNode 直接返回 | `view_abstract.cpp:5431` | AC-2.2 |
| R-18 | 恢复 | 目标组件销毁 | PushDestroyCallbackWithTag 清理 popup/menu 节点 | `view_abstract.cpp:4706-4726` | AC-1.5 |
| R-19 | 边界 | #ifdef PREVIEW | 禁用子窗与 preview，强制 MENU+NONE | `view_abstract.cpp:5434-5438` | AC-2.2 |
| R-20 | 行为 | bindPopup 更新已有 popup | modifier->updatePopupNode + MarkDirtyNode(PROPERTY_UPDATE_MEASURE) | `view_abstract.cpp:4732-4733` | AC-1.1 |
| R-21 | 行为 | bindMenu 创建菜单 | menuWrapperNode->MarkDirtyNode(PROPERTY_UPDATE_MEASURE_SELF_AND_CHILD) | `view_abstract.cpp:5355-5356` | AC-2.1 |
| R-22 | 恢复 | bindPopup 目标销毁 | PushDestroyCallbackWithTag 注册销毁回调 | `view_abstract.cpp:4706-4726` | AC-1.5 |

---

## 验证映射

| VM编号 | 关联用户故事 | 验证手段 | 验证要点 |
|-------|-------------|---------|---------|
| VM-1 | US-1 bindPopup (AC-1.1~1.5) | 代码审查 | 双路径显示；双向绑定；销毁回调 |
| VM-2 | US-2 bindMenu (AC-2.1~2.5) | 代码审查 | items/customNode 分发；placement 默认值 |
| VM-3 | US-3 bindContextMenu (AC-3.1~3.6) | 代码审查 | 双范式；WithResponse；preview/arrow 互斥 |

### 逐 AC 验证用例

| AC编号 | 验证类型 | 位置/用例 |
|-------|----------|-----------|
| AC-1.1 | 代码审查 | `frameworks/core/components_ng/base/view_abstract.cpp:4615-4772` |
| AC-1.2 | 代码审查 | `frameworks/bridge/declarative_frontend/jsview/js_popups.cpp:2064-2068` |
| AC-1.3 | 代码审查 | `frameworks/bridge/declarative_frontend/jsview/js_popups.cpp:2021-2072` |
| AC-1.4 | 代码审查 | `frameworks/core/components_ng/base/view_abstract.cpp:4639` |
| AC-1.5 | 代码审查 | `frameworks/core/components_ng/base/view_abstract.cpp:4706-4726` |
| AC-2.1 | 代码审查 | `frameworks/core/components_ng/base/view_abstract.cpp:5382-5426` |
| AC-2.2 | 代码审查 | `frameworks/core/components_ng/base/view_abstract.cpp:5428-5478` |
| AC-2.3 | 代码审查 | `frameworks/bridge/declarative_frontend/jsview/js_popups.cpp:3357-3362` |
| AC-2.4 | 代码审查 | `frameworks/bridge/declarative_frontend/jsview/js_popups.cpp:3293-3355` |
| AC-2.5 | 代码审查 | `frameworks/core/components_ng/base/view_abstract.cpp:5404-5407` |
| AC-3.1 | 代码审查 | `frameworks/core/components_ng/base/view_abstract_model_ng.cpp:530` |
| AC-3.2 | 代码审查 | `frameworks/core/components_ng/base/view_abstract_model_ng.cpp:591` |
| AC-3.3 | 代码审查 | `frameworks/core/components_ng/base/view_abstract_model_ng.cpp:345` |
| AC-3.4 | 代码审查 | `frameworks/core/components_ng/base/view_abstract_model_ng.cpp:936-961` |
| AC-3.5 | 代码审查 | `frameworks/core/components_ng/property/menu_property.h:112-226` |
| AC-3.6 | 代码审查 | `frameworks/core/components_ng/base/view_abstract_model_ng.cpp:1158-1182` |

---

## API 变更分析

### 新增 API

> SDK 定义来源: `interface/sdk-js/api/@internal/component/ets/common.d.ts`

| API 名称 | 开放范围 | 入参概要 | 返回值 | 错误码范围 | 功能描述 | 关联 AC |
|----------|----------|----------|--------|-----------|----------|---------|
| `bindPopup(show, popup): T` | Public | show: boolean \| {$value}; popup: PopupOptions \| CustomPopupOptions | T | N/A | 绑定气泡弹窗 | AC-1.1~1.5 |
| `bindMenu(content, options?): T` | Public | content: Array<MenuElement> \| CustomBuilder; options?: MenuOptions | T | N/A | 绑定菜单 | AC-2.1~2.5 |
| `bindMenu(isShow, content, options?): T` | Public | isShow: boolean; content; options? | T | N/A | 命令式菜单(@since 11) | AC-2.4 |
| `bindContextMenu(content, responseType, options?): T` | Public | content: CustomBuilder; responseType: ResponseType; options?: ContextMenuOptions | T | N/A | 绑定上下文菜单(@since 8) | AC-3.1~3.6 |
| `bindContextMenu(isShown, content, options?): T` | Public | isShown: boolean; content; options? | T | N/A | 命令式上下文菜单(@since 12) | AC-3.3 |
| `bindContextMenuWithResponse(content, options?): T` | Public | content: CustomBuilderT<ResponseType> \| undefined; options? | T | N/A | 响应类型感知(@since 23) | AC-3.4 |

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
| API 7 | bindPopup/bindMenu 初始版本 | — | — |
| API 8 | bindContextMenu 初始版本(responseType) | — | — |
| API 10 | bindMenu 默认 placement BOTTOM_LEFT；crossplatform | 默认对齐变化 | API<10 无默认 placement |
| API 11 | bindMenu isShow 双向绑定；bindContextMenu isShown；atomicservice | 命令式控制新增 | 旧版本仅手势触发 |
| API 12 | bindContextMenu options 扩展(backgroundColor/blurStyle/transition) | — | — |
| API 23 | bindContextMenuWithResponse(CustomBuilderT<ResponseType>) | 同时注册双触发 | 旧版本需分两次绑定 |
| API 26 | bindContextMenuByResponseType/ByIsShow(Array<MenuElement>) | 支持混合菜单项 | 旧版本仅 CustomBuilder |

---

## 架构约束

| 关键约束 | 约束说明 | 影响 AC |
|----------|----------|---------|
| 双路径显示 | IsShowInSubWindow 走子窗，否则走 OverlayManager | AC-1.4 |
| OverlayManager 集中管理 | popupMap_/customPopupMap_ 集中存储 | AC-1.1 |
| 脏标记分级 | popup 更新 PROPERTY_UPDATE_MEASURE；menu PROPERTY_UPDATE_MEASURE_SELF_AND_CHILD | AC-1.1, AC-2.1 |
| 注册分发 | contextMenuRegisterType(CUSTOM_TYPE/NORMAL_TYPE) 决定注册路径 | AC-3.3 |
| 销毁回调 | PushDestroyCallbackWithTag 绑定目标生命周期 | AC-1.5 |

---

## 非功能性需求

| 类型 | 指标/阈值 | 验证方式 | 证据 |
|------|-----------|----------|------|
| 性能 | 绑定注册 O(1) | 代码审查 | view_abstract.cpp |
| 可调试性 | OverlayManager 提供 popup/menu 诊断 | 代码审查 | overlay_manager.cpp |

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
| 无障碍 | 否 | popup/menu 通过子节点提供无障碍 | — |
| 大字体 | 否 | 无差异 | — |
| 深色模式 | 否 | popup/menu 背景色跟随主题 | — |
| 多窗口/分屏 | 是 | IsShowInSubWindow 跨窗口显示 | AC-1.4 |
| 多用户 | 否 | 无差异 | — |
| 版本升级 | 是 | API 7→26 多版本变体 | 兼容性声明 |
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
| `frameworks/core/components_ng/base/view_abstract.cpp` | BindPopup/BindMenuWithItems/BindMenuWithCustomNode |
| `frameworks/core/components_ng/base/view_abstract_model_ng.cpp` | BindMenu/BindContextMenu 入口与分发 |
| `frameworks/core/components_ng/pattern/overlay/overlay_manager.cpp` | ShowPopup/ShowMenu 挂载与显示 |
| `frameworks/bridge/declarative_frontend/jsview/js_popups.cpp` | JsBindPopup/JsBindMenu/JsBindContextMenu |
| `frameworks/bridge/declarative_frontend/jsview/js_view_abstract.cpp` | 静态方法注册 L10349-10360 |
| `frameworks/core/components_ng/property/menu_property.h` | MenuParam 结构定义 |

### SDK 文档

| 文件 | 说明 |
|------|------|
| `interface/sdk-js/api/@internal/component/ets/common.d.ts` | bindPopup/bindMenu/bindContextMenu SDK 定义 |
