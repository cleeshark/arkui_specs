# 特性规格

> Func-04-03-06-Feat-01 模态属性：固化 bindSheet/bindContentCover 通用属性维度的绑定、双向 isShow、ModalTransition 选择与 attributeModifier 限制行为规格。

## 概述

| 属性 | 值 |
|------|-----|
| 特性名称 | 模态属性 (Modal Attributes) |
| 特性编号 | Func-04-03-06-Feat-01 |
| 所属 Epic | 无（已有能力补录） |
| 优先级 | P0 |
| 目标版本 | API 10 起支持，API 18/20 持续扩展 |
| SIG 归属 | ArkUI SIG |
| 状态 | Baselined |
| 复杂度 | 中等 |

## 本次变更范围（Delta）

> 历史规格补齐，补录已有实现的完整行为规格。

| 类型 | 内容 | 说明 |
|------|------|------|
| ADDED | bindSheet/bindContentCover 通用属性绑定行为 | 补录模态属性绑定行为 |

## 输入文档

| 文档 | 路径 | 状态 |
|------|------|------|
| Design | `specs/04-common-capability/03-common-attributes/06-modal-attributes/design.md` | Baselined |
| SDK API | `interface/sdk-js/api/@internal/component/ets/common.d.ts` | — |
| 关联组件规格 | `specs/05-ui-components/07-modal-components/01-sheet-modal/` (05-07-01) | — |
| 关联组件规格 | `specs/05-ui-components/07-modal-components/02-full-modal/` (05-07-02) | — |

---

## 用户故事

### US-1: 绑定全模态 ContentCover

**作为** 应用开发者,
**我想要** 通过 `bindContentCover(isShow, builder, options?)` 将全模态浮层绑定到任意组件,
**以便** 实现全屏覆盖式内容展示。

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-1.1 | WHEN 调用 `bindContentCover(true, builder)` THEN 通过 ViewAbstractModelNG::BindContentCover 创建 modal 节点挂载到 modalStack_ | 正常 |
| AC-1.2 | WHEN isShow 为 {$value}/!! 对象 THEN ParseSheetIsShow 解析双向绑定，$ since 10，!! since 18 | 正常 |
| AC-1.3 | WHEN options.modalTransition 未设置 THEN 默认 ModalTransition::DEFAULT | 边界 |
| AC-1.4 | WHEN 同时设置 transition 与 modalTransition THEN transition(TransitionEffect) 覆盖 modalTransition | 边界 |
| AC-1.5 | WHEN 在 attributeModifier 中调用 bindContentCover THEN 抛 100201 错误 | 异常 |

### US-2: 绑定半模态 Sheet

**作为** 应用开发者,
**我想要** 通过 `bindSheet(isShow, builder, options?)` 将半模态浮层绑定到任意组件,
**以便** 实现底部弹出式内容展示。

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-2.1 | WHEN 调用 `bindSheet(true, builder, options)` THEN 通过 ViewAbstractModelNG::BindSheet 分发，默认 sheetMode=LARGE | 正常 |
| AC-2.2 | WHEN isShow 为 {$value}/!! 对象 THEN ParseSheetIsShow 解析双向绑定 | 正常 |
| AC-2.3 | WHEN showInSubWindow=true THEN 走 SubwindowManager::ShowBindSheetNG 子窗路径 | 边界 |
| AC-2.4 | WHEN showInPage=true THEN 走 sheetModifier->findPageNodeOverlay 嵌入式路径 | 边界 |
| AC-2.5 | WHEN 在 attributeModifier 中调用 bindSheet THEN 抛 100201 错误 | 异常 |

---

## 验收追溯

| AC编号 | US ID | 关联规则 | 验证手段 |
|-------|-------|----------|----------|
| AC-1.1 | US-1 | R-1 | 代码审查 view_abstract_model_ng.cpp:1125-1156 |
| AC-1.2 | US-1 | R-2 | 代码审查 js_popups.cpp:2491-2510 |
| AC-1.3 | US-1 | R-3 | 代码审查 js_popups.cpp:2408 |
| AC-1.4 | US-1 | R-4 | 代码审查 overlay_manager.cpp:3345-3346 |
| AC-1.5 | US-1 | R-9 | 代码审查 ArkComponent.ts:5826 |
| AC-2.1 | US-2 | R-5 | 代码审查 view_abstract_model_ng.cpp:1226-1283 |
| AC-2.2 | US-2 | R-2 | 代码审查 js_popups.cpp:2491-2510 |
| AC-2.3 | US-2 | R-6 | 代码审查 view_abstract_model_ng.cpp:1264-1275 |
| AC-2.4 | US-2 | R-7 | 代码审查 view_abstract_model_ng.cpp:1256-1258 |
| AC-2.5 | US-2 | R-9 | 代码审查 ArkComponent.ts:5857 |

## 规则定义

| 规则ID | 类型 | 触发条件 | 预期行为 | 边界/约束 | 关联AC |
|--------|------|----------|----------|-----------|--------|
| R-1 | 行为 | bindContentCover(isShow=true, builder) | 创建 modal 节点挂载到 modalStack_，tag=V2::MODAL_PAGE_TAG | `view_abstract_model_ng.cpp:1125-1156` | AC-1.1 |
| R-2 | 行为 | isShow 为 {$value}/!! 对象 | ParseSheetIsShow 解析双向绑定，$ since 10，!! since 18 | `js_popups.cpp:2491-2510` | AC-1.2, AC-2.2 |
| R-3 | 边界 | modalTransition 未设置 | 默认 ModalTransition::DEFAULT | `js_popups.cpp:2408` | AC-1.3 |
| R-4 | 边界 | 同时设置 transition 与 modalTransition | transition(TransitionEffect) 覆盖 modalTransition | `overlay_manager.cpp:3345-3346` | AC-1.4 |
| R-5 | 行为 | bindSheet(isShow=true, builder, options) | ViewAbstractModelNG::BindSheet 分发，默认 sheetMode=LARGE | `view_abstract_model_ng.cpp:1226-1283` | AC-2.1 |
| R-6 | 边界 | showInSubWindow=true | 走 SubwindowManager::ShowBindSheetNG | `view_abstract_model_ng.cpp:1264-1275` | AC-2.3 |
| R-7 | 边界 | showInPage=true | 走 sheetModifier->findPageNodeOverlay 嵌入式 | `view_abstract_model_ng.cpp:1256-1258` | AC-2.4 |
| R-8 | 行为 | bindSheet 执行 | 通过 AddAnimationClosure 延迟到下一帧执行 | `overlay_manager.cpp:3591-3635` | AC-2.1 |
| R-9 | 异常 | 在 attributeModifier 中调用 | 抛 100201 错误 | `ArkComponent.ts:5826/5857` | AC-1.5, AC-2.5 |
| R-10 | 恢复 | 目标组件销毁 | overlayManager->DeleteModal(id) 清理 modal | `view_abstract_model_ng.cpp:1144-1151` | AC-1.1 |
| R-11 | 行为 | bindSheet 更新已有 sheet | 通过 UpdateBindSheetByUIContext 更新 | `overlay_manager.cpp:4039` | AC-2.1 |

---

## 验证映射

| VM编号 | 关联用户故事 | 验证手段 | 验证要点 |
|-------|-------------|---------|---------|
| VM-1 | US-1 bindContentCover (AC-1.1~1.5) | 代码审查 | 双向 isShow；transition 优先级；attributeModifier 限制 |
| VM-2 | US-2 bindSheet (AC-2.1~2.5) | 代码审查 | 子窗/嵌入式路由；延迟执行；attributeModifier 限制 |

### 逐 AC 验证用例

| AC编号 | 验证类型 | 位置/用例 |
|-------|----------|-----------|
| AC-1.1 | 代码审查 | `frameworks/core/components_ng/base/view_abstract_model_ng.cpp:1125-1156` |
| AC-1.2 | 代码审查 | `frameworks/bridge/declarative_frontend/jsview/js_popups.cpp:2491-2510` |
| AC-1.3 | 代码审查 | `frameworks/bridge/declarative_frontend/jsview/js_popups.cpp:2408` |
| AC-1.4 | 代码审查 | `frameworks/core/components_ng/pattern/overlay/overlay_manager.cpp:3345-3346` |
| AC-1.5 | 代码审查 | `frameworks/bridge/declarative_frontend/ark_component/src/ArkComponent.ts:5826` |
| AC-2.1 | 代码审查 | `frameworks/core/components_ng/base/view_abstract_model_ng.cpp:1226-1283` |
| AC-2.2 | 代码审查 | `frameworks/bridge/declarative_frontend/jsview/js_popups.cpp:2491-2510` |
| AC-2.3 | 代码审查 | `frameworks/core/components_ng/base/view_abstract_model_ng.cpp:1264-1275` |
| AC-2.4 | 代码审查 | `frameworks/core/components_ng/base/view_abstract_model_ng.cpp:1256-1258` |
| AC-2.5 | 代码审查 | `frameworks/bridge/declarative_frontend/ark_component/src/ArkComponent.ts:5857` |

---

## API 变更分析

### 新增 API

> SDK 定义来源: `interface/sdk-js/api/@internal/component/ets/common.d.ts`

| API 名称 | 开放范围 | 入参概要 | 返回值 | 错误码范围 | 功能描述 | 关联 AC |
|----------|----------|----------|--------|-----------|----------|---------|
| `bindContentCover(isShow, builder, type?: ModalTransition): T` | Public | isShow: boolean; builder: CustomBuilder; type?: ModalTransition | T | N/A | 绑定全模态(@since 10 legacy) | AC-1.1~1.5 |
| `bindContentCover(isShow, builder, options?: ContentCoverOptions): T` | Public | isShow; builder; options?: ContentCoverOptions | T | N/A | 绑定全模态(@since 10 options) | AC-1.1~1.5 |
| `bindSheet(isShow, builder, options?: SheetOptions): T` | Public | isShow; builder; options?: SheetOptions | T | N/A | 绑定半模态(@since 10) | AC-2.1~2.5 |

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
| API 10 | bindSheet/bindContentCover 初始版本；$ 双向绑定 | — | — |
| API 11 | atomicservice 支持 | — | — |
| API 12 | onWillDismiss/transition 扩展 | — | — |
| API 18 | !! 双向绑定 | $ 仍可用 | — |
| API 20 | enableSafeArea (ContentCover) | — | — |

---

## 架构约束

| 关键约束 | 约束说明 | 影响 AC |
|----------|----------|---------|
| OverlayManager 集中管理 | modalStack_/sheetMap_ 集中存储 | AC-1.1, AC-2.1 |
| 双路径显示 | showInSubWindow 走子窗，showInPage 走嵌入式，否则 Overlay | AC-2.3, AC-2.4 |
| transition 优先级 | transition 覆盖 modalTransition | AC-1.4 |
| attributeModal 禁止 | attributeModifier 场景无 ViewStackProcessor 上下文 | AC-1.5, AC-2.5 |
| 延迟执行 | bindSheet 通过 AddAnimationClosure 延迟到下一帧 | AC-2.1 |

---

## 非功能性需求

| 类型 | 指标/阈值 | 验证方式 | 证据 |
|------|-----------|----------|------|
| 性能 | 绑定注册 O(1) | 代码审查 | view_abstract_model_ng.cpp |
| 可靠性 | 目标销毁清理 modal | 代码审查 | view_abstract_model_ng.cpp:1144-1151 |

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
| 无障碍 | 否 | modal 通过子节点提供无障碍 | — |
| 大字体 | 否 | 无差异 | — |
| 深色模式 | 否 | modal 背景色跟随主题 | — |
| 多窗口/分屏 | 是 | showInSubWindow 跨窗口显示 | AC-2.3 |
| 多用户 | 否 | 无差异 | — |
| 版本升级 | 是 | API 10/18/20 版本差异 | 兼容性声明 |
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
| `frameworks/core/components_ng/base/view_abstract_model_ng.cpp` | BindContentCover/BindSheet Model 层 |
| `frameworks/core/components_ng/pattern/overlay/overlay_manager.cpp` | OnBindContentCover/OnBindSheet 挂载 |
| `frameworks/bridge/declarative_frontend/jsview/js_popups.cpp` | JsBindContentCover/JsBindSheet/ParseSheetIsShow |
| `frameworks/bridge/declarative_frontend/ark_component/src/ArkComponent.ts` | attributeModifier 限制 |

### SDK 文档

| 文件 | 说明 |
|------|------|
| `interface/sdk-js/api/@internal/component/ets/common.d.ts` | bindSheet/bindContentCover SDK 定义 |
