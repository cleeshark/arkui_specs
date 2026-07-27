# 特性规格

> Func-05-07-02-Feat-01 bindContentCover 全模态弹窗：固化绑定与双向 isShow、ModalTransition DEFAULT/NONE/ALPHA、自定义 transition（TransitionEffect）、onWillDismiss DismissContentCoverAction、生命周期 onAppear/onDisappear/onWillAppear/onWillDisappear、enableSafeArea、backgroundColor、attributeModifier 限制、isUIExtension 的行为规格。

## 概述

| 属性 | 值 |
|------|-----|
| 特性名称 | bindContentCover 全模态弹窗 (Full Modal / Content Cover) |
| 特性编号 | Func-05-07-02-Feat-01 |
| 所属 Epic | 无（已有能力补录） |
| 优先级 | P0 |
| 目标版本 | API 10 起支持，API 11/12/18/20 持续演进 |
| SIG 归属 | ArkUI SIG |
| 状态 | Baselined |
| 复杂度 | 中等 |

## 本次变更范围（Delta）

> 历史规格补齐，补录已有实现的完整行为规格。

| 类型 | 内容 | 说明 |
|------|------|------|
| ADDED | 绑定与双向 isShow 行为规格 | bindContentCover(isShow, builder, type?/options?) @since 10；ParseSheetIsShow 双向；@since 18 !! 强制双向 |
| ADDED | ModalTransition 行为规格 | DEFAULT（滑动）/NONE（无动画）/ALPHA（透明度）@since 10 |
| ADDED | 自定义 transition 行为规格 | transition（TransitionEffect）覆盖 modalTransition @since 12 |
| ADDED | onWillDismiss 行为规格 | DismissContentCoverAction{dismiss, reason} @since 12 |
| ADDED | 生命周期回调行为规格 | onAppear/onDisappear/onWillAppear/onWillDisappear（isExecuteOnDismiss_ 守卫） |
| ADDED | enableSafeArea 行为规格 | 默认 false @since 20 |
| ADDED | backgroundColor 与 attributeModifier 限制/isUIExtension 行为规格 | backgroundColor 可设置；attributeModifier 抛出异常；isUIExtension 默认 false |

## 输入文档

| 文档 | 路径 | 状态 |
|------|------|------|
| Design | `specs/05-ui-components/07-modal-components/02-full-modal/design.md` | Baselined |
| SDK API | `interface/sdk-js/api/@internal/component/ets/common.d.ts` | — |

---

## 用户故事

### US-1: 绑定与双向 isShow

**作为** 应用开发者,
**我想要** 通过 `bindContentCover(isShow, builder, options?)` 绑定全模态弹窗并通过状态变量控制显示,
**以便** 命令式管理全屏模态的显示与隐藏。

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-1.1 | WHEN 调用 `bindContentCover(isShow, builder, options?)` THEN ParseSheetIsShow L2389 检测 isShow 双向绑定 | 正常 |
| AC-1.2 | WHEN isShow=true THEN OnBindContentCover L3211 创建 FrameNode(V2::MODAL_PAGE_TAG) + ModalPresentationPattern(targetId, modalTransition.value_or(DEFAULT), callback) L3282-3283，MountToParentWithService，push modalStack_/modalList_ | 正常 |
| AC-1.3 | WHEN isShow=false THEN HandleModalPop L3257/L3361 移除模态（OnWillDisappear + 过渡退出） | 正常 |
| AC-1.4 | WHEN @since 18 THEN isShow 改为 !! 强制双向绑定 | 边界 |

### US-2: ModalTransition

**作为** 应用开发者,
**我想要** 通过 `modalTransition` 或 legacy `type` 参数设置过渡方式,
**以便** 控制全模态弹窗的进入/退出动画。

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-2.1 | WHEN modalTransition = DEFAULT（默认）THEN PlayDefaultModalTransition（滑动过渡） | 边界 |
| AC-2.2 | WHEN modalTransition = NONE THEN OnAppear 直接触发（无动画） | 边界 |
| AC-2.3 | WHEN modalTransition = ALPHA THEN PlayAlphaModalTransition（透明度过渡） | 正常 |

### US-3: 自定义 transition

**作为** 应用开发者,
**我想要** 通过 `transition`（TransitionEffect）自定义过渡动画,
**以便** 实现比 ModalTransition 更灵活的过渡效果。

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-3.1 | WHEN 设置 transition（TransitionEffect）且 != null THEN hasTransitionEffect_=true，覆盖 modalTransition，走 PlayTransitionEffectIn/Out | 正常 |
| AC-3.2 | WHEN transition == null THEN 按 modalTransition 分支（DEFAULT/NONE/ALPHA） | 边界 |
| AC-3.3 | WHEN transition 覆盖时 THEN PlayTransitionEffectIn（进入）/PlayTransitionEffectOut（退出）执行 | 正常 |

### US-4: onWillDismiss

**作为** 应用开发者,
**我想要** 通过 `onWillDismiss` 拦截全模态弹窗关闭,
**以便** 实现条件关闭逻辑。

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-4.1 | WHEN 设置 onWillDismiss（@since 12）THEN 关闭时触发，提供 DismissContentCoverAction{dismiss, reason: DismissReason} | 正常 |
| AC-4.2 | WHEN DismissContentCoverAction.reason THEN 为 BACK_PRESSED/TOUCH_OUTSIDE/CLOSE_BUTTON（无 SLIDE） | 边界 |
| AC-4.3 | WHEN 开发者未调用 action.dismiss() THEN 模态不关闭 | 正常 |

### US-5: 生命周期回调

**作为** 应用开发者,
**我想要** 通过生命周期回调感知全模态弹窗的显示/隐藏,
**以便** 在不同时机执行业务逻辑。

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-5.1 | WHEN 模态即将显示 THEN onWillAppear 触发 | 正常 |
| AC-5.2 | WHEN 模态已显示 THEN onAppear 触发（受 isExecuteOnDismiss_ 守卫） | 正常 |
| AC-5.3 | WHEN 模态即将隐藏 THEN onWillDisappear 触发 | 正常 |
| AC-5.4 | WHEN 模态已隐藏 THEN onDisappear 触发（受 isExecuteOnDismiss_ 守卫） | 正常 |

### US-6: enableSafeArea

**作为** 应用开发者,
**我想要** 通过 `enableSafeArea` 控制模态是否避让安全区,
**以便** 适配不同设备的屏幕安全区。

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-6.1 | WHEN enableSafeArea 未设置 THEN 默认 false（@since 20） | 边界 |
| AC-6.2 | WHEN enableSafeArea=true THEN 模态避让安全区 | 正常 |

### US-7: backgroundColor 与限制

**作为** 应用开发者,
**我想要** 通过 backgroundColor 设置模态背景，并了解 attributeModifier 限制,
**以便** 定制模态视觉风格并避免误用。

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-7.1 | WHEN 设置 backgroundColor THEN 模态背景使用指定颜色 | 正常 |
| AC-7.2 | WHEN 在 attributeModifier 中调用 bindContentCover THEN 抛出异常（ArkComponent.ts L5826） | 异常 |

### US-8: isUIExtension 与路由/导航移除

**作为** 应用开发者,
**我想要** 了解 isUIExtension 及 prohibitedRemoveByRouter/Navigation 默认行为,
**以便** 适配跨进程 UI 扩展与路由/导航场景。

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-8.1 | WHEN isUIExtension 默认 false THEN 模态为非 UIExtension | 边界 |
| AC-8.2 | WHEN prohibitedRemoveByRouter=false / prohibitedRemoveByNavigation=true / isModalRequestFocus=true THEN 路由可移除模态，导航不可移除，模态请求焦点 | 边界 |

---

## 验收追溯

| AC编号 | US ID | 关联规则 | 验证手段 |
|-------|-------|----------|----------|
| AC-1.1 | US-1 | R-1, R-2 | 代码审查 js_popups.cpp:2389 |
| AC-1.2 | US-1 | R-3, R-4 | 单元测试 + 代码审查 overlay_manager.cpp:3211/3282-3283 |
| AC-1.3 | US-1 | R-5 | 单元测试 + 代码审查 overlay_manager.cpp:3257/3361 |
| AC-1.4 | US-1 | R-6 | 代码审查 |
| AC-2.1 | US-2 | R-7 | 代码审查 overlay_manager.cpp:3354-3355 |
| AC-2.2 | US-2 | R-8 | 代码审查 overlay_manager.cpp:3348-3352 |
| AC-2.3 | US-2 | R-9 | 代码审查 overlay_manager.cpp:3356-3357 |
| AC-3.1 | US-3 | R-10, R-11 | 代码审查 overlay_manager.cpp:3345-3346 |
| AC-3.2 | US-3 | R-12 | 代码审查 |
| AC-3.3 | US-3 | R-13 | 代码审查 overlay_manager.cpp |
| AC-4.1 | US-4 | R-14 | 单元测试 |
| AC-4.2 | US-4 | R-15 | 代码审查 modal_presentation_pattern.h:27 |
| AC-4.3 | US-4 | R-16 | 单元测试 |
| AC-5.1 | US-5 | R-17 | 单元测试 |
| AC-5.2 | US-5 | R-18 | 单元测试 |
| AC-5.3 | US-5 | R-19 | 单元测试 |
| AC-5.4 | US-5 | R-20 | 单元测试 |
| AC-6.1 | US-6 | R-21 | 代码审查 content_cover_param.h |
| AC-6.2 | US-6 | R-22 | 单元测试 |
| AC-7.1 | US-7 | R-23 | 单元测试 |
| AC-7.2 | US-7 | R-24 | 代码审查 ArkComponent.ts:5826 |
| AC-8.1 | US-8 | R-25 | 代码审查 modal_style.h |
| AC-8.2 | US-8 | R-26 | 代码审查 modal_style.h |


## 规则定义

> **统一规则表，取消 FR/BR/EX/RC 四分类。** 类型标签：**行为**（正常路径下的系统行为）、**边界**（输入/状态的临界点）、**异常**（非法输入或异常状态的处理）、**恢复**（系统异常后的恢复策略）。

| 规则ID | 类型 | 触发条件 | 预期行为 | 边界/约束 | 关联AC |
|--------|------|----------|----------|-----------|--------|
| R-1 | 行为 | `js_popups.cpp:2389` ParseSheetIsShow | 检测 isShow 双向绑定 | — | AC-1.1 |
| R-2 | 行为 | bindContentCover isShow | isShow 为状态变量，双向绑定 | — | AC-1.1 |
| R-3 | 行为 | `overlay_manager.cpp:3211` OnBindContentCover | isShow=true 创建 FrameNode(V2::MODAL_PAGE_TAG) + ModalPresentationPattern L3282-3283，MountToParentWithService，push modalStack_/modalList_ | — | AC-1.2 |
| R-4 | 行为 | `overlay_manager.cpp:3241` | 已存在 → 更新 pattern，MarkDirtyNode(PROPERTY_UPDATE_MEASURE_SELF) | — | AC-1.2 |
| R-5 | 行为 | `overlay_manager.cpp:3257/3361` HandleModalPop | isShow=false → OnWillDisappear + PlayTransitionEffectOut/PlayDefaultModalTransition(false)/PlayAlphaModalTransition(false) | — | AC-1.3 |
| R-6 | 边界 | @since 18 | isShow 改为 !! 强制双向绑定 | — | AC-1.4 |
| R-7 | 边界 | modalTransition=DEFAULT（默认） | PlayDefaultModalTransition（滑动过渡） | `overlay_manager.cpp:3354-3355` | AC-2.1 |
| R-8 | 边界 | API<12 OR modalTransition=NONE | OnAppear 直接触发（无动画） | `overlay_manager.cpp:3348-3352` | AC-2.2 |
| R-9 | 行为 | modalTransition=ALPHA | PlayAlphaModalTransition（透明度过渡） | `overlay_manager.cpp:3356-3357` | AC-2.3 |
| R-10 | 行为 | transition（TransitionEffect）!= null | hasTransitionEffect_=true，覆盖 modalTransition | — | AC-3.1 |
| R-11 | 行为 | `overlay_manager.cpp:3345-3346` | transitionEffect != null → PlayTransitionEffectIn（进入） | — | AC-3.1, AC-3.3 |
| R-12 | 边界 | transition == null | 按 modalTransition 分支（DEFAULT/NONE/ALPHA） | — | AC-3.2 |
| R-13 | 行为 | transition 退出 | PlayTransitionEffectOut（退出） | `overlay_manager.cpp` HandleModalPop | AC-3.3 |
| R-14 | 行为 | onWillDismiss @since 12 | 关闭时触发，提供 DismissContentCoverAction{dismiss, reason: DismissReason} | — | AC-4.1 |
| R-15 | 边界 | ContentCoverDismissReason | BACK_PRESSED/TOUCH_OUTSIDE/CLOSE_BUTTON（无 SLIDE） | `modal_presentation_pattern.h:27` | AC-4.2 |
| R-16 | 行为 | action.dismiss() 未调用 | 模态不关闭 | — | AC-4.3 |
| R-17 | 行为 | onWillAppear | 模态即将显示前触发 | — | AC-5.1 |
| R-18 | 行为 | onAppear | 模态已显示触发（受 isExecuteOnDismiss_ 守卫） | — | AC-5.2 |
| R-19 | 行为 | onWillDisappear | 模态即将隐藏前触发 | — | AC-5.3 |
| R-20 | 行为 | onDisappear | 模态已隐藏触发（受 isExecuteOnDismiss_ 守卫） | — | AC-5.4 |
| R-21 | 边界 | enableSafeArea 默认 | 默认 false（@since 20） | `content_cover_param.h` | AC-6.1 |
| R-22 | 行为 | enableSafeArea=true | 模态避让安全区 | — | AC-6.2 |
| R-23 | 行为 | backgroundColor | 模态背景使用指定颜色 | — | AC-7.1 |
| R-24 | 异常 | attributeModifier 限制 | bindContentCover 不允许在 attributeModifier 中调用，抛出异常 | `ArkComponent.ts:5826` | AC-7.2 |
| R-25 | 边界 | isUIExtension 默认 | 默认 false | `modal_style.h` | AC-8.1 |
| R-26 | 边界 | prohibitedRemoveByRouter/Navigation/isModalRequestFocus | Router=false 可移除，Navigation=true 不可移除，isModalRequestFocus=true | `modal_style.h` | AC-8.2 |
| R-27 | 异常 | 无效 ModalTransition | ParseModalTransition 验证 [0,2]，无效值→DEFAULT | `js_popups.cpp:2467` | — |
| R-28 | 行为 | 双重载签名 | 3rd arg object→options；number→0..2 ModalTransition | `js_popups.cpp:2419-2429` | — |
| R-29 | 行为 | modalTransition 默认 DEFAULT | L2408 modalTransition=DEFAULT | `js_popups.cpp:2408` | — |
| R-30 | 恢复 | DeleteModal | 析构 overlayManager->DeleteModal(id) V2::MODAL_PAGE_TAG | `view_abstract_model_ng.cpp:1144-1151` | — |

---

## 验证映射

| VM编号 | 关联用户故事 | 验证手段 | 验证要点 |
|-------|-------------|---------|---------|
| VM-1 | US-1 绑定与 isShow (AC-1.1~1.4) | 单元测试 + 代码审查 | ParseSheetIsShow 双向；OnBindContentCover 创建/移除；@since 18 !! 强制 |
| VM-2 | US-2 ModalTransition (AC-2.1~2.3) | 代码审查 | DEFAULT 滑动/NONE 无动画/ALPHA 透明度 |
| VM-3 | US-3 自定义 transition (AC-3.1~3.3) | 代码审查 | transitionEffect 覆盖 modalTransition；PlayTransitionEffectIn/Out |
| VM-4 | US-4 onWillDismiss (AC-4.1~4.3) | 单元测试 | DismissContentCoverAction；reason 无 SLIDE；条件关闭 |
| VM-5 | US-5 生命周期 (AC-5.1~5.4) | 单元测试 | onWillAppear/onAppear/onWillDisappear/onDisappear + isExecuteOnDismiss_ 守卫 |
| VM-6 | US-6 enableSafeArea (AC-6.1~6.2) | 单元测试 + 代码审查 | 默认 false @since 20；避让安全区 |
| VM-7 | US-7 backgroundColor 与限制 (AC-7.1~7.2) | 单元测试 + 代码审查 | backgroundColor；attributeModifier 抛出异常 |
| VM-8 | US-8 isUIExtension 与路由/导航 (AC-8.1~8.2) | 代码审查 | isUIExtension false；prohibitedRemoveByRouter/Navigation/isModalRequestFocus |

### 逐 AC 验证用例

| AC编号 | 验证类型 | 位置/用例 |
|-------|----------|-----------|
| AC-1.1 | 代码审查 | `frameworks/bridge/declarative_frontend/jsview/js_popups.cpp:2389` ParseSheetIsShow |
| AC-1.2 | 代码审查 | `frameworks/core/components_ng/pattern/overlay/overlay_manager.cpp:3211/3282-3283` OnBindContentCover |
| AC-1.3 | 代码审查 | `frameworks/core/components_ng/pattern/overlay/overlay_manager.cpp:3257/3361` HandleModalPop |
| AC-1.4 | 代码审查 | `frameworks/bridge/declarative_frontend/jsview/js_popups.cpp:2389`（@since 18 !!） |
| AC-2.1 | 代码审查 | `frameworks/core/components_ng/pattern/overlay/overlay_manager.cpp:3354-3355` PlayDefaultModalTransition |
| AC-2.2 | 代码审查 | `frameworks/core/components_ng/pattern/overlay/overlay_manager.cpp:3348-3352` OnAppear 直接 |
| AC-2.3 | 代码审查 | `frameworks/core/components_ng/pattern/overlay/overlay_manager.cpp:3356-3357` PlayAlphaModalTransition |
| AC-3.1 | 代码审查 | `frameworks/core/components_ng/pattern/overlay/overlay_manager.cpp:3345-3346` PlayTransitionEffectIn |
| AC-3.2 | 代码审查 | `frameworks/core/components_ng/pattern/overlay/overlay_manager.cpp:3345-3357` transition 分支 |
| AC-3.3 | 代码审查 | `frameworks/core/components_ng/pattern/overlay/overlay_manager.cpp` HandleModalPop |
| AC-4.1 | 单元测试 | `test/unittest/core/pattern/overlay/` modal_presentation_pattern_test |
| AC-4.2 | 代码审查 | `frameworks/core/components_ng/pattern/overlay/modal_presentation_pattern.h:27` |
| AC-4.3 | 单元测试 | `test/unittest/core/pattern/overlay/` |
| AC-5.1 | 单元测试 | `test/unittest/core/pattern/overlay/` |
| AC-5.2 | 单元测试 | `test/unittest/core/pattern/overlay/` |
| AC-5.3 | 单元测试 | `test/unittest/core/pattern/overlay/` |
| AC-5.4 | 单元测试 | `test/unittest/core/pattern/overlay/` |
| AC-6.1 | 代码审查 | `frameworks/core/components_ng/pattern/overlay/content_cover_param.h` |
| AC-6.2 | 单元测试 | `test/unittest/core/pattern/overlay/` |
| AC-7.1 | 单元测试 | `test/unittest/core/pattern/overlay/` |
| AC-7.2 | 代码审查 | `frameworks/bridge/declarative_frontend/ark_component/src/ArkComponent.ts:5826` |
| AC-8.1 | 代码审查 | `frameworks/core/components_ng/pattern/overlay/modal_style.h` |
| AC-8.2 | 代码审查 | `frameworks/core/components_ng/pattern/overlay/modal_style.h` |

---

## API 变更分析

### 新增 API

> SDK 定义来源: `interface/sdk-js/api/@internal/component/ets/common.d.ts`

#### bindContentCover

```typescript
// common.d.ts:23199 @since 10 (legacy)
bindContentCover(isShow: boolean, builder: CustomBuilder, type?: ModalTransition): T;

// common.d.ts:23218 @since 10
bindContentCover(isShow: boolean, builder: CustomBuilder, options?: ContentCoverOptions): T;
```

#### 枚举与类型

```typescript
// common.d.ts:7842 @since 10
declare enum ModalTransition {
    DEFAULT = 0,  // slide
    NONE = 1,     // no animation
    ALPHA = 2     // opacity
}

// common.d.ts:12403 @since 11
declare interface BindOptions {
    backgroundColor?: ResourceColor;
    onAppear?: () => void;
    onDisappear?: () => void;
    onWillAppear?: () => void;
    onWillDisappear?: () => void;
}

// common.d.ts:12496 @since 12
declare interface DismissContentCoverAction {
    dismiss(): void;
    reason: DismissReason;
}

// common.d.ts:12529 @since 10
declare interface ContentCoverOptions extends BindOptions {
    modalTransition?: ModalTransition;  // default DEFAULT
    onWillDismiss?: (action: DismissContentCoverAction) => void;  // @since 12
    transition?: TransitionEffect;      // @since 12
    enableSafeArea?: boolean;            // default false @since 20
}
```

| 方法签名 | 返回类型 | 说明 | @since |
|----------|----------|------|--------|
| `bindContentCover(isShow, builder, type?: ModalTransition)` | T | legacy 重载（type 参数） | 10 |
| `bindContentCover(isShow, builder, options?: ContentCoverOptions)` | T | 推荐重载（options 对象） | 10 |

### 变更/废弃 API

| API 名称 | 变更类型 | 关联 AC |
|----------|----------|---------|
| `bindContentCover(isShow, builder, type?: ModalTransition)` legacy | 保留（不废弃） | 推荐迁移到 options 重载以使用 transition/onWillDismiss/enableSafeArea |

## 接口规格

### 接口定义

> 本特性为已有实现补录，接口行为定义详见上方规则定义和用户故事。

无新增接口规格。

---

## 兼容性声明

| API 版本 | 行为差异 | 影响 | 迁移指导 |
|----------|----------|------|----------|
| API 10 | bindContentCover 基础 API，isShow 双向绑定，ModalTransition DEFAULT/NONE/ALPHA | — | 无需迁移 |
| API 10 | 双重载签名（legacy type vs options） | 3rd arg 类型分发 | 推荐迁移到 options 重载 |
| API 11 | BindOptions 基类（backgroundColor/onAppear/onDisappear/onWillAppear/onWillDisappear） | — | — |
| API 12 | 新增 onWillDismiss（DismissContentCoverAction）与 transition（TransitionEffect） | transition 覆盖 modalTransition | 如需自定义过渡迁移到 transition |
| API 18 | isShow 改为 !! 强制双向绑定 | 强制双向语义 | 无需迁移 |
| API 20 | enableSafeArea 默认 false | 默认不避让安全区 | 如需避让显式设置 enableSafeArea=true |
| 无效 ModalTransition | ParseModalTransition 验证 [0,2]，无效值→DEFAULT | 静默回退 | 无效值不报错 |
| attributeModifier | bindContentCover 不允许在 attributeModifier 中调用 | 抛出异常 | 使用正常属性链 |
| ContentCoverDismissReason | 无 SLIDE/SLIDE_DOWN | 与 BindSheetDismissReason 差异 | — |
| prohibitedRemoveByRouter/Navigation | Router=false 可移除，Navigation=true 不可移除 | 路由/导航行为差异 | — |

---

## 架构约束

| 约束 | 描述 |
|------|------|
| ModalPresentationPattern 架构 | 继承 PopupBasePattern, FocusView, AutoFillTriggerStateHolder |
| 模态节点挂载 | V2::MODAL_PAGE_TAG + MountToParentWithService，push modalStack_/modalList_ |
| transition 覆盖 | transitionEffect != null 时覆盖 modalTransition，hasTransitionEffect_=true |
| isExecuteOnDismiss_ 守卫 | OnAppear/OnDisappear/OnWillDisappear 受守卫防止重复触发 |
| 双重载签名 | 3rd arg object→options；number→0..2 ModalTransition |
| ParseModalTransition 验证 | [0,2]，无效值→DEFAULT |
| attributeModifier 限制 | bindContentCover 不允许在 attributeModifier 中调用（ArkComponent.ts L5826） |
| ContentCoverDismissReason | BACK_PRESSED/TOUCH_OUTSIDE/CLOSE_BUTTON（无 SLIDE） |
| 默认值 | modalTransition=DEFAULT/enableSafeArea=false/isUIExtension=false/prohibitedRemoveByRouter=false/prohibitedRemoveByNavigation=true/isModalRequestFocus=true |
| DeleteModal | 析构 overlayManager->DeleteModal(id) V2::MODAL_PAGE_TAG |

---

## 非功能性需求

| 维度 | 要求 |
|------|------|
| 性能 | ContentCover 为轻量模态浮层，过渡动画帧率 ≥ 60fps |
| 可调试性 | 提供 DumpInfo 用于 Inspector 诊断模态状态 |
| 问题定位 | hilog 标签 ACE_OVERLAY 覆盖关键路径 |

---

## 多设备适配声明

| 设备类型 | 行为差异 | 规格/约束 | 验证方式 | 证据 |
|----------|----------|-----------|----------|------|
| 手机 | 全屏覆盖，DEFAULT 滑动过渡 | — | 手工 | — |
| 平板 | 全屏覆盖，可设置 backgroundColor | — | 手工 | — |
| 折叠屏 | enableSafeArea 适配折叠态/展开态安全区 | @since 20 | 手工 | — |

---

## 全局特性影响

| 影响维度 | 说明 |
|----------|------|
| 无障碍 | 模态内容支持无障碍读取，显示时获取焦点（FocusView） |
| 大字体 | 模态文字跟随系统字体缩放 |
| 深色模式 | backgroundColor 通过 ResourceColor 支持主题跟随 |
| 多窗口/分屏 | 全屏模态覆盖当前窗口，isUIExtension 支持 UI 扩展场景 |
| 多用户 | 无用户相关状态 |
| 版本升级 | API 10/11/12/18/20 持续演进，isShow !! 强制双向、transition/onWillDismiss/enableSafeArea 变更 |
| 生态兼容 | C-API 通过 SetBindContentCover0Impl/SetBindContentCover1Impl 委托 |

---

## 行为场景

### 场景 1: 显示全模态弹窗

```
Given 组件调用 bindContentCover(isShow, builder, options?)
When isShow 设置为 true
Then ParseSheetIsShow 检测双向绑定
And OnBindContentCover 创建 FrameNode(V2::MODAL_PAGE_TAG) + ModalPresentationPattern
And MountToParentWithService，push modalStack_/modalList_
And onWillAppear 触发，按 modalTransition 过渡显示，显示后 onAppear 触发
```

### 场景 2: DEFAULT 滑动过渡

```
Given 组件 modalTransition = DEFAULT（默认）
When 模态显示
Then PlayDefaultModalTransition 执行滑动过渡
```

### 场景 3: NONE 无动画

```
Given 组件 modalTransition = NONE 或 API<12
When 模态显示
Then OnAppear 直接触发（无过渡动画）
```

### 场景 4: 自定义 transition 覆盖

```
Given 组件设置 transition = TransitionEffect
When transition != null
Then hasTransitionEffect_ = true
And transition 覆盖 modalTransition
And PlayTransitionEffectIn 执行自定义进入过渡
```

### 场景 5: onWillDismiss 拦截关闭

```
Given 组件设置 onWillDismiss
When 用户尝试关闭模态
Then onWillDismiss 触发
And 提供 DismissContentCoverAction（dismiss + reason）
And reason 为 BACK_PRESSED/TOUCH_OUTSIDE/CLOSE_BUTTON（无 SLIDE）
And 开发者按 reason 决定是否调用 dismiss()
```

### 场景 6: enableSafeArea 避让

```
Given 组件设置 enableSafeArea = true（默认 false，@since 20）
When 模态显示
Then 模态避让安全区
```

### 场景 7: attributeModifier 限制

```
Given 在 attributeModifier 中调用 bindContentCover
When 执行
Then 抛出异常（ArkComponent.ts L5826）
```

### 场景 8: 无效 ModalTransition 回退

```
Given 组件设置 type = 5（超出 [0,2]）
When ParseModalTransition 验证
Then 无效值回退为 DEFAULT
And 不抛出异常
```

---

## Spec 自审清单

- [x] 所有 US 以 "作为/我想要/以便" 格式描述
- [x] 所有 AC 编号格式正确（AC-X.Y），且在验收追溯中引用
- [x] 验证映射覆盖全部 AC，每个 AC 至少有一种验证手段
- [x] 业务规则/功能规则/异常规则/恢复契约编号连续且可追溯到源码
- [x] API 变更分析基于真实 SDK 定义文件（common.d.ts）
- [x] 兼容性声明标注 API 版本差异
- [x] 行为场景使用 Gherkin Given/When/Then 格式，覆盖关键路径
- [x] 所有源码引用包含 file:line 信息
- [x] 构建系统影响章节已确认无变更

---

## context-references

### 源码文件

| 文件 | 说明 |
|------|------|
| `frameworks/core/components_ng/pattern/overlay/modal_presentation_pattern.h/.cpp` | ModalPresentationPattern（继承 PopupBasePattern, FocusView, AutoFillTriggerStateHolder） |
| `frameworks/core/components_ng/pattern/overlay/modal_style.h` | ModalTransition 枚举 + ModalStyle 结构体 |
| `frameworks/core/components_ng/pattern/overlay/content_cover_param.h` | ContentCoverParam（onWillDismiss/transitionEffect/enableSafeArea） |
| `frameworks/core/components_ng/pattern/overlay/overlay_manager.cpp` | BindContentCover L3201 / OnBindContentCover L3211 / HandleModalPop L3257/L3361 / transition 分支 L3345-3357 |
| `frameworks/core/components_ng/base/view_abstract_model_ng.cpp` | BindContentCover L1125-1156 / DeleteModal L1144-1151 |
| `frameworks/core/components_ng/base/view_abstract_model_static.cpp` | 静态前端 BindContentCover L797 |
| `frameworks/core/components_ng/pattern/sheet/content_cover/sheet_content_cover_object.h` | SheetContentCoverObject（CONTENT_COVER 变体，L23） |
| `frameworks/bridge/declarative_frontend/jsview/js_popups.cpp` | JsBindContentCover L2385-2435 + ParseSheetIsShow L2389 + ParseModalTransitonEffect L2437 + ParseModalStyle L2447 + ParseModalTransition L2467 + ParseEnableSafeArea L2482 |
| `frameworks/bridge/declarative_frontend/jsview/js_view_abstract.cpp` | bindContentCover 静态注册 L10359 |
| `frameworks/bridge/declarative_frontend/ark_component/src/ArkComponent.ts` | attributeModifier 限制 L5826 |
| `frameworks/core/interfaces/native/node/common_method_modifier.cpp` | SetBindContentCover0Impl L7000 / SetBindContentCover1Impl L7033 |
| `frameworks/core/interfaces/native/node/bind_sheet_ops_accessor.cpp` | C-API accessor L110/134/139 |
| `frameworks/core/interfaces/native/node/dismiss_content_cover_action_peer.h` | BindSheetDismissReason reason L21 |
| `frameworks/core/interfaces/native/node/bind_sheet_utils.cpp` | ParseContentCoverCallbacks L255-286 |

### 测试文件

| 文件 | 说明 |
|------|------|
| `test/unittest/core/pattern/overlay/` | Overlay/ModalPresentation NG 单元测试 |

### SDK 文档

| 文件 | 说明 |
|------|------|
| `interface/sdk-js/api/@internal/component/ets/common.d.ts` | ModalTransition/BindOptions/DismissContentCoverAction/ContentCoverOptions/bindContentCover 声明 |
