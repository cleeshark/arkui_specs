# 特性规格

> Func-04-03-03-Feat-05 状态效果与自定义：固化 stateStyles/hoverEffect/clickEffect/attributeModifier/customProperty/drawModifier 六个核心状态效果与自定义属性的行为规格。

## 概述

| 属性 | 值 |
|------|-----|
| 特性名称 | 状态效果与自定义 (State Effect & Custom) |
| 特性编号 | Func-04-03-03-Feat-05 |
| 所属 Epic | 无（已有能力补录） |
| 优先级 | P1 |
| 目标版本 | API 8 起支持，API 12/14 有行为变更 |
| SIG 归属 | ArkUI SIG |
| 状态 | Baselined |
| 复杂度 | 复杂 |

## 本次变更范围（Delta）

> 历史规格补齐，补录已有实现的完整行为规格。

| 类型 | 内容 | 说明 |
|------|------|------|
| ADDED | stateStyles/hoverEffect/clickEffect/attributeModifier/customProperty/drawModifier 行为规格 | 已有实现，补录完整行为规格 |

## 输入文档

| 文档 | 路径 | 状态 |
|------|------|------|
| Design | `specs/04-common-capability/03-common-attributes/03-basic-attributes/design.md` | Draft |

> 需求基线、不涉及项、受影响子系统与仓库详见 proposal.md，本文档不重复摘录。design.md 与本文档并行产出，互不依赖。

---

## 用户故事

### US-1: 设置 stateStyles 实现多状态样式

**作为** 应用开发者,
**我想要** 通过 `.stateStyles(StateStyles)` 为组件在不同交互状态下定义不同样式,
**以便** 组件在 Normal/Pressed/Disabled/Focused/Selected 状态下呈现不同的视觉表现。

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-1.1 | WHEN 调用 `.stateStyles({ normal: { ... }, pressed: { ... } })` THEN 组件注册对应的 UI_STATE_NORMAL 和 UI_STATE_PRESSED 到 supportedStates_ | 正常 |
| AC-1.2 | WHEN 组件处于 Normal 状态（currentState_ == UI_STATE_NORMAL）THEN 应用 normal 中定义的属性 | 正常 |
| AC-1.3 | WHEN 组件进入 Pressed 状态（触摸按下）THEN Pressed 状态属性覆盖 Normal 状态属性（currentState_ |= UI_STATE_PRESSED） | 正常 |
| AC-1.4 | WHEN 组件进入 Disabled 状态 THEN Disabled 状态属性覆盖 Normal 状态属性 | 正常 |
| AC-1.5 | WHEN 组件进入 Focused 状态 THEN Focused 状态属性覆盖 Normal 状态属性 | 正常 |
| AC-1.6 | WHEN 组件进入 Selected 状态 THEN Selected 状态属性覆盖 Normal 状态属性 | 正常 |
| AC-1.7 | WHEN 多个状态同时激活（如 Pressed + Focused）THEN 后应用的状态属性覆盖先应用的，同一属性以最后覆盖的为准 | 边界 |
| AC-1.8 | WHEN stateStyles 中某状态未定义属性 THEN 该状态不注册到 supportedStates_，状态变化时不触发样式刷新 | 异常 |

### US-2: 设置 hoverEffect 实现悬停反馈

**作为** 应用开发者,
**我想要** 通过 `.hoverEffect(HoverEffectType)` 设置组件悬停时的视觉反馈类型,
**以便** 用户在鼠标悬停时获得明确的交互提示。

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-2.1 | WHEN 调用 `.hoverEffect(HoverEffectType.AUTO)` THEN 框架根据组件类型自动选择最佳悬停效果 | 正常 |
| AC-2.2 | WHEN 调用 `.hoverEffect(HoverEffectType.SCALE)` THEN 鼠标悬停时组件产生均匀缩放效果 | 正常 |
| AC-2.3 | WHEN 调用 `.hoverEffect(HoverEffectType.HIGHLIGHT)` THEN 鼠标悬停时组件背景亮度发生变化 | 正常 |
| AC-2.4 | WHEN 调用 `.hoverEffect(HoverEffectType.NONE)` THEN 鼠标悬停时不产生任何视觉效果 | 正常 |
| AC-2.5 | WHEN hoverEffect 未设置 THEN 默认为 HoverEffectType::UNKNOWN（无悬停效果） | 异常 |
| AC-2.6 | WHEN 同时设置 SetHoverEffect 和 SetHoverEffectAuto THEN SetHoverEffect 存储到 hoverEffectType_，SetHoverEffectAuto 存储到 hoverEffectAuto_，两者独立管理 | 边界 |

### US-3: 设置 clickEffect 实现点击反馈

**作为** 应用开发者,
**我想要** 通过 `.clickEffect(ClickEffect)` 设置组件点击时的视觉反馈,
**以便** 用户在点击组件时获得触觉级别的视觉确认。

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-3.1 | WHEN 调用 `.clickEffect({ level: ClickEffectLevel.LIGHT })` THEN 点击时组件产生轻微缩放动画（spring 参数：velocity=ANIMATION_CURVE_VELOCITY_LIGHT_OR_MIDDLE, mass=ANIMATION_CURVE_MASS, stiffness=ANIMATION_CURVE_STIFFNESS_LIGHT, damping=ANIMATION_CURVE_DAMPING_LIGHT） | 正常 |
| AC-3.2 | WHEN 调用 `.clickEffect({ level: ClickEffectLevel.MIDDLE })` THEN 点击时组件产生中等缩放动画（spring 参数：velocity=ANIMATION_CURVE_VELOCITY_LIGHT_OR_MIDDLE, mass=ANIMATION_CURVE_MASS, stiffness=ANIMATION_CURVE_STIFFNESS_MIDDLE, damping=ANIMATION_CURVE_DAMPING_MIDDLE） | 正常 |
| AC-3.3 | WHEN 调用 `.clickEffect({ level: ClickEffectLevel.HEAVY })` THEN 点击时组件产生较强缩放动画（spring 参数：velocity=ANIMATION_CURVE_VELOCITY_HEAVY, mass=ANIMATION_CURVE_MASS, stiffness=ANIMATION_CURVE_STIFFNESS_HEAVY, damping=ANIMATION_CURVE_DAMPING_HEAVY） | 正常 |
| AC-3.4 | WHEN 调用 `.clickEffect({ level: ClickEffectLevel.UNDEFINED })` THEN 点击效果重置为未定义（等同取消 clickEffect） | 异常 |
| AC-3.5 | WHEN clickEffect 的 level 值超出 LIGHT~HEAVY 范围 THEN level 被纠正为 0（LIGHT） | 异常 |
| AC-3.6 | WHEN clickEffect 中 scale 值在 [0, 1] 范围内 THEN scaleValue = sqrt(scale) | 正常 |
| AC-3.7 | WHEN clickEffect 中 scale 值不在 [0, 1] 范围内 THEN LIGHT 使用 DEFAULT_SCALE_LIGHT，MIDDLE/HEAVY 使用 DEFAULT_SCALE_MIDDLE_OR_HEAVY | 边界 |
| AC-3.8 | WHEN clickEffect 传入 null/undefined THEN level 重置为 UNDEFINED，scaleValue 重置为 DEFAULT_SCALE_LIGHT | 异常 |

### US-4: 使用 attributeModifier 实现动态属性修改

**作为** 应用开发者,
**我想要** 通过 `.attributeModifier(AttributeModifier)` 动态修改组件属性,
**以便** 在状态变化时以编程方式灵活控制组件外观。

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-4.1 | WHEN 调用 `.attributeModifier(modifier)` 且 modifier 定义了 applyNormalAttribute THEN modifier.applyNormalAttribute(instance) 在 Normal 状态下被调用，设置属性到 instance | 正常 |
| AC-4.2 | WHEN modifier 定义了 applyPressedAttribute THEN 状态进入 Pressed 时 modifier.applyPressedAttribute(instance) 被调用 | 正常 |
| AC-4.3 | WHEN modifier 定义了 applyDisabledAttribute THEN 状态进入 Disabled 时 modifier.applyDisabledAttribute(instance) 被调用 | 正常 |
| AC-4.4 | WHEN modifier 定义了 applyFocusedAttribute THEN 状态进入 Focused 时 modifier.applyFocusedAttribute(instance) 被调用 | 正常 |
| AC-4.5 | WHEN modifier 定义了 applySelectedAttribute THEN 状态进入 Selected 时 modifier.applySelectedAttribute(instance) 被调用 | 正常 |
| AC-4.6 | WHEN modifier 定义了 applyHoveredAttribute THEN 状态进入 Hovered 时 modifier.applyHoveredAttribute(instance) 被调用 | 正常 |
| AC-4.7 | WHEN 同时设置 stateStyles 和 attributeModifier THEN attributeModifier 设置的属性优先级高于 stateStyles 设置的同一属性（attributeModifier 覆盖 stateStyles） | 边界 |
| AC-4.8 | WHEN 状态发生转换 THEN modifier 对应状态的 apply 方法被重新调用，属性重新应用到 Modifiable 对象 | 正常 |
| AC-4.9 | WHEN modifier 中某状态方法未定义 THEN 该状态下不调用任何方法（不触发属性变更） | 异常 |

### US-5: 设置 customProperty 存储用户自定义数据

**作为** 应用开发者,
**我想要** 通过 `.customProperty(key, value)` 在组件上存储自定义键值对数据,
**以便** 在组件节点上挂载业务数据供后续查询使用。

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-5.1 | WHEN 调用 `.customProperty("myKey", "myValue")` THEN key-value 存入 FrameNode 的 customPropertyMap_ | 正常 |
| AC-5.2 | WHEN 通过 GetJSCustomProperty("myKey") 查询 THEN 返回 "myValue" | 正常 |
| AC-5.3 | WHEN 调用 `.customProperty(key, undefined)` THEN 该 key 从 customPropertyMap_ 中移除（RemoveCustomProperty） | 异常 |
| AC-5.4 | WHEN 查询不存在的 key THEN 返回 false/空 | 异常 |
| AC-5.5 | WHEN 使用 AddExtraCustomProperty(key, void* extraData) THEN 存入 extraCustomPropertyMap_，可通过 GetExtraCustomProperty(key) 查询 | 正常 |

### US-6: 使用 drawModifier 实现自定义绘制

**作为** 应用开发者,
**我想要** 通过 `.drawModifier(DrawModifier)` 在组件的不同绘制阶段执行自定义渲染逻辑,
**以便** 在组件的内容/前景/背景层叠加自定义图形。

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-6.1 | WHEN 调用 `.drawModifier(modifier)` 且 modifier 定义了 drawBehind THEN drawBehindFunc 在组件内容绘制之前被调用 | 正常 |
| AC-6.2 | WHEN modifier 定义了 drawContent THEN drawContentFunc 在组件内容绘制时被调用 | 正常 |
| AC-6.3 | WHEN modifier 定义了 drawFront THEN drawFrontFunc 在组件内容绘制之后被调用 | 正常 |
| AC-6.4 | WHEN modifier 定义了 drawForeground THEN drawForegroundFunc 在组件前景绘制时被调用 | 正常 |
| AC-6.5 | WHEN modifier 定义了 drawOverlay THEN drawOverlayFunc 在组件最上层绘制时被调用 | 正常 |
| AC-6.6 | WHEN Draw() 方法被调用 THEN 接收 DrawingContext（包含 canvas: RSCanvas&、width: float、height: float），自定义绘制在 canvas 上执行 | 正常 |
| AC-6.7 | WHEN 组件不支持 DrawModifier（IsSupportDrawModifier 返回 false）THEN drawModifier 设置被忽略 | 异常 |
| AC-6.8 | WHEN drawModifier 传入 null/undefined 且 API ≥ 20 THEN 清除当前 drawModifier（SetDrawModifier(nullptr）），并触发 MarkDirtyNode(PROPERTY_UPDATE_RENDER) | 异常 |
| AC-6.9 | WHEN drawModifier 传入 null/undefined 且 API < 20 THEN 设置被忽略（不执行任何操作） | 边界 |

---

## 验收追溯

| AC | 关联规则 | 关联 Task | 验证方式 | 证据 |
|----|---------|----------|----------|------|
| AC-1.1~1.6 | R-1 | — | 单测 | StateStyleManager 单测 |
| AC-1.7 | R-1, R-9 | — | 单测 | 多状态合并覆盖 |
| AC-1.8 | R-1 | — | 单测 | 未注册状态不刷新 |
| AC-2.1~2.4 | R-3 | — | 单测 | InputEventHub hover 效果 |
| AC-2.5~2.6 | R-3 | — | 单测 | 默认值与双重设置 |
| AC-3.1~3.3 | R-4 | — | 单测 | ClickEffect spring 参数 |
| AC-3.4~3.8 | R-4 | — | 单测 | 边界与异常处理 |
| AC-4.1~4.6 | R-5 | — | 单测 | attributeModifier 各状态 |
| AC-4.7 | R-2, R-5 | — | 单测 | attributeModifier vs stateStyles |
| AC-4.8 | R-6 | — | 单测 | 状态转换重新应用 |
| AC-4.9 | R-5 | — | 单测 | 未定义方法不调用 |
| AC-5.1~5.5 | R-8 | — | 单测 | customProperty 存取 |
| AC-6.1~6.5 | R-7 | — | 单测 | DrawModifier 各阶段 |
| AC-6.6 | R-7 | — | 单测 | DrawingContext 参数 |
| AC-6.7~6.9 | R-7 | — | 单测 | 不支持/null 处理 |

---

## 规则定义

| 规则ID | 类型 | 触发条件 | 预期行为 | 边界/约束 | 关联AC |
|--------|------|----------|----------|-----------|--------|
| R-1 | 行为 | stateStyles 设置多状态样式 | 属性按 Normal→Pressed→Disabled→Focused→Selected 顺序应用；当状态激活时，对应状态的属性覆盖 Normal 状态属性 | UI_STATE 常量：NORMAL=0, PRESSED=1, FOCUSED=2, DISABLED=4, SELECTED=8, HOVERED=16 | AC-1.1~1.6 |
| R-2 | 边界 | 同一属性同时通过 stateStyles 和 attributeModifier 设置 | attributeModifier 的属性值优先级高于 stateStyles；attributeModifier 设置的属性覆盖 stateStyles 设置的同一属性 | override 链：stateStyles → attributeModifier（后者优先） | AC-4.7 |
| R-3 | 行为 | hoverEffect 设置悬停效果 | AUTO=框架决定最佳效果；SCALE=均匀缩放；HIGHLIGHT=背景亮度变化；NONE=无效果 | 内部枚举：NONE=0, OPACITY=1, SCALE=2, BOARD=3, AUTO=4, UNKNOWN=5；C-API 映射：AUTO=0, SCALE=1, HIGHLIGHT=2, NONE=3 | AC-2.1~2.4 |
| R-4 | 行为 | clickEffect 设置点击反馈 | LIGHT=轻微缩放 spring 动画；MIDDLE=中等缩放 spring 动画；HEAVY=较强缩放 spring 动画 | spring 参数见 rosen_render_context.cpp:7623；scale 值范围 [0,1]，超出范围使用默认值；UNDEFINED=-1 用于重置 | AC-3.1~3.3 |
| R-5 | 行为 | attributeModifier 设置动态属性 | 各 apply 方法（applyNormal/Pressed/Disabled/Focused/Selected/Hovered）接收 Modifiable 对象作为参数；设置属性到 Modifiable 对象即应用到组件节点 | AttributeModifier 接口定义见 ark_component/types/index.d.ts:785；各方法可选（? 标记），未定义的方法不触发属性变更 | AC-4.1~4.6, AC-4.9 |
| R-6 | 行为 | 状态转换触发 attributeModifier 重新应用 | 当组件状态发生变化时（如从 Normal 进入 Pressed），StateStyleManager 的 UpdateCurrentUIState/ResetCurrentUIState 被调用，触发 FireStateFunc，attributeModifier 对应状态的 apply 方法被重新执行 | StateStyleManager 管理状态生命周期 | AC-4.8 |
| R-7 | 行为 | drawModifier 自定义绘制 | DrawModifier 提供 drawBehindFunc/drawContentFunc/drawFrontFunc/drawForegroundFunc/drawOverlayFunc 五个绘制回调；每个回调接收 DrawingContext{canvas: RSCanvas&, width, height} | DrawingContext 定义见 modifier.h:82；不支持 DrawModifier 的组件（IsSupportDrawModifier 返回 false）忽略设置；API < 20 时 null 输入不执行清除 | AC-6.1~6.5, AC-6.6 |
| R-8 | 行为 | customProperty 存储自定义键值对 | AddCustomProperty(key, value) 存入 customPropertyMap_；RemoveCustomProperty(key) 移除；GetCustomPropertyByKey(key) 查询；GetJSCustomProperty/GetCapiCustomProperty 区分前端和 C-API 查询路径 | key: string, value: string（JS 侧通过 SetJSCustomProperty 绑定 getter/setter 函数）；C-API 侧：addCustomProperty/removeCustomProperty/getCustomProperty | AC-5.1~5.5 |
| R-9 | 边界 | stateStyles 中多个状态同时激活 | 多个 UI_STATE 通过位运算合并（currentState_ |= state），属性覆盖顺序由状态注册和刷新流程决定；同一属性最终值取决于最后被应用的状态 | UI_STATE 使用 uint64_t 位掩码管理；STATE_NORMAL=0 表示无特殊状态激活 | AC-1.7 |

---

## 验证映射

| 编号 | 对应规格项 | 验证方式 | 验证重点 |
|------|------------|----------|----------|
| VM-1 | R-1, AC-1.1~1.6 | 单测 | StateStyleManager 状态注册与刷新 |
| VM-2 | R-2, AC-4.7 | 单测 | attributeModifier 优先级高于 stateStyles |
| VM-3 | R-3, AC-2.1~2.4 | 单测 | hoverEffect 四种效果类型行为 |
| VM-4 | R-4, AC-3.1~3.3 | 单测 | clickEffect spring 参数和 scale 计算 |
| VM-5 | R-5, R-6, AC-4.1~4.8 | 单测 | attributeModifier 各状态方法调用与状态转换重新应用 |
| VM-6 | R-7, AC-6.1~6.9 | 单测 | drawModifier 五阶段绘制与 DrawingContext 参数传递 |
| VM-7 | R-8, AC-5.1~5.5 | 单测 | customProperty 存取与移除 |
| VM-8 | R-9, AC-1.7 | 单测 | 多状态合并覆盖行为 |
| VM-9 | 全量 | XTS/集成 | 端到端状态效果与自定义渲染正确 |

---

## API 变更分析

### 新增 API

| API 签名 | 开放范围 | 入参概要 | 返回值 | 错误码范围 | 功能描述 | 关联 AC |
|----------|---------|---------|--------|-----------|---------|---------|
| `stateStyles(value: StateStyles): T` | Public | StateStyles{normal?, pressed?, disabled?, focused?, selected?} | T | — | 多状态样式定义 | AC-1.1~1.8 |
| `hoverEffect(value: HoverEffectType): T` | Public | HoverEffectType(Auto/Scale/Highlight/None) | T | — | 悬停效果类型 | AC-2.1~2.6 |
| `clickEffect(value: ClickEffect \| null): T` | Public | ClickEffect{level: ClickEffectLevel, scale?: number} | T | — | 点击反馈效果 | AC-3.1~3.8 |
| `attributeModifier(modifier: AttributeModifier\<T\>): T` | Public | AttributeModifier{applyNormal?, applyPressed?, applyDisabled?, applyFocused?, applySelected?, applyHovered?} | T | — | 动态属性修改 | AC-4.1~4.9 |
| `customProperty(name: string, value: Optional\<Object\>): T` | Public | key: string, value: Object | T | — | 自定义键值存储 | AC-5.1~5.5 |
| `drawModifier(modifier: DrawModifier): T` | Public | DrawModifier{drawBehind?, drawContent?, drawFront?, drawForeground?, drawOverlay?} | T | — | 自定义绘制 | AC-6.1~6.9 |

**C-API (NDK) 接口：**

| 属性枚举 | 值格式 | 功能 | @since |
|----------|--------|------|--------|
| `NODE_HOVER_EFFECT` | `.value[0].i32` (ArkUI_HoverEffect) | 设置悬停效果 | 12 |
| `NODE_CLICK_EFFECT` | `.value[0].i32` (level), `.value[1].f32` (scale) | 设置点击效果 | 12 |
| `addCustomProperty` | key: ArkUI_CharPtr, value: ArkUI_CharPtr | 添加自定义属性 | 12 |
| `removeCustomProperty` | key: ArkUI_CharPtr | 移除自定义属性 | 12 |
| `getCustomProperty` | key: ArkUI_CharPtr → char** value | 查询自定义属性 | 12 |
| `ArkUIAniDrawModifier.setDrawModifier` | ptr, flag, drawBehind, drawContent, drawFront, drawForeground, drawOverlay | 设置自定义绘制 | 14 |

**关联类型定义：**

| 类型名 | 定义 | 位置 |
|--------|------|------|
| `StateStyles` | `{ normal?: any; pressed?: any; disabled?: any; focused?: any; clicked?: any; selected?: object }` | index.d.ts:990 |
| `HoverEffectType` | Auto/Scale/Highlight/None | native_type.h:1328 (C-API) |
| `ClickEffect` | `{ level: number; scale?: number }` | index.d.ts:782 |
| `ClickEffectLevel` | UNDEFINED=-1, LIGHT=0, MIDDLE=1, HEAVY=2 | effect_option.h:28 |
| `AttributeModifier\<T\>` | `{ applyNormal?(instance: T); applyPressed?(instance: T); ... }` | index.d.ts:785 |
| `DrawingContext` | `{ canvas: RSCanvas&; width: float; height: float }` | modifier.h:82 |

### 变更/废弃 API

N/A，已有能力补录，API 行为无变化。

---

## 接口规格

### 接口定义

**stateStyles**

| 属性 | 值 |
|------|-----|
| 函数签名 | `stateStyles(value: StateStyles): T` |
| 返回值 | `T` — 返回组件自身以支持链式调用 |
| 开放范围 | Public |
| 错误码 | N/A |
| 关联 AC | AC-1.1~1.8 |

**参数约束**

| 参数 | 类型 | 必填 | 默认值 | 约束条件 |
|------|------|------|--------|---------|
| value.normal | StateStyleAttribute | 否 | undefined | 未定义则不注册 UI_STATE_NORMAL |
| value.pressed | StateStyleAttribute | 否 | undefined | 未定义则不注册 UI_STATE_PRESSED |
| value.disabled | StateStyleAttribute | 否 | undefined | 未定义则不注册 UI_STATE_DISABLED |
| value.focused | StateStyleAttribute | 否 | undefined | 未定义则不注册 UI_STATE_FOCUSED |
| value.selected | StateStyleAttribute | 否 | undefined | 未定义则不注册 UI_STATE_SELECTED |

**行为场景**

| # | 触发条件 | 预期行为 | 关联 AC |
|---|----------|----------|---------|
| 1 | 设置 stateStyles 且所有状态均已定义 | 所有状态注册到 supportedStates_，状态变化时触发样式刷新 | AC-1.1 |
| 2 | 组件从 Normal 进入 Pressed 状态 | currentState_ |= UI_STATE_PRESSED，Pressed 属性覆盖 Normal | AC-1.3 |
| 3 | Pressed + Focused 同时激活 | 属性按覆盖链合并，同一属性以最后应用的为准 | AC-1.7 |
| 4 | stateStyles 中某状态为 undefined | 该状态不注册，不触发样式刷新 | AC-1.8 |

---

**attributeModifier**

| 属性 | 值 |
|------|-----|
| 函数签名 | `attributeModifier(modifier: AttributeModifier<T>): T` |
| 返回值 | `T` — 返回组件自身以支持链式调用 |
| 开放范围 | Public |
| 错误码 | N/A |
| 关联 AC | AC-4.1~4.9 |

**参数约束**

| 参数 | 类型 | 必填 | 默认值 | 约束条件 |
|------|------|------|--------|---------|
| modifier.applyNormalAttribute | (instance: T) => void | 否 | undefined | 未定义则 Normal 状态不调用 |
| modifier.applyPressedAttribute | (instance: T) => void | 否 | undefined | 未定义则 Pressed 状态不调用 |
| modifier.applyDisabledAttribute | (instance: T) => void | 否 | undefined | 未定义则 Disabled 状态不调用 |
| modifier.applyFocusedAttribute | (instance: T) => void | 否 | undefined | 未定义则 Focused 状态不调用 |
| modifier.applySelectedAttribute | (instance: T) => void | 否 | undefined | 未定义则 Selected 状态不调用 |
| modifier.applyHoveredAttribute | (instance: T) => void | 否 | undefined | 未定义则 Hovered 状态不调用 |

**行为场景**

| # | 触发条件 | 预期行为 | 关联 AC |
|---|----------|----------|---------|
| 1 | 设置 attributeModifier 且定义了 applyNormalAttribute | Normal 状态下调用 applyNormalAttribute，属性应用到 Modifiable 对象 | AC-4.1 |
| 2 | 状态进入 Pressed 且定义了 applyPressedAttribute | 调用 applyPressedAttribute，属性覆盖 Normal 状态属性 | AC-4.2 |
| 3 | 同时设置 stateStyles 和 attributeModifier，同一属性两者均设置 | attributeModifier 的属性值生效（优先级高于 stateStyles） | AC-4.7 |
| 4 | 状态发生转换 | modifier 对应状态的 apply 方法被重新调用 | AC-4.8 |
| 5 | modifier 中某状态方法为 undefined | 该状态不触发任何属性变更 | AC-4.9 |

---

**drawModifier**

| 属性 | 值 |
|------|-----|
| 函数签名 | `drawModifier(modifier: DrawModifier): T` |
| 返回值 | `T` — 返回组件自身以支持链式调用 |
| 开放范围 | Public |
| 错误码 | N/A |
| 关联 AC | AC-6.1~6.9 |

**参数约束**

| 参数 | 类型 | 必填 | 默认值 | 约束条件 |
|------|------|------|--------|---------|
| modifier.drawBehind | (DrawingContext) => void | 否 | undefined | 绘制在组件内容之前 |
| modifier.drawContent | (DrawingContext) => void | 否 | undefined | 绘制在组件内容时 |
| modifier.drawFront | (DrawingContext) => void | 否 | undefined | 绘制在组件内容之后 |
| modifier.drawForeground | (DrawingContext) => void | 否 | undefined | 绘制在组件前景时 |
| modifier.drawOverlay | (DrawingContext) => void | 否 | undefined | 绘制在组件最上层 |
| DrawingContext.canvas | RSCanvas& | — | — | 绘制画布，由框架提供 |
| DrawingContext.width | float | — | 0 | 组件渲染区域宽度 |
| DrawingContext.height | float | — | 0 | 组件渲染区域高度 |

**行为场景**

| # | 触发条件 | 预期行为 | 关联 AC |
|---|----------|----------|---------|
| 1 | 设置 drawModifier 且定义了 drawBehind | drawBehindFunc 在渲染 pass 中组件内容绘制前被调用 | AC-6.1 |
| 2 | 设置 drawModifier 且定义了 drawOverlay | drawOverlayFunc 在组件最上层被调用 | AC-6.5 |
| 3 | Draw() 方法被调用 | 接收 DrawingContext{canvas, width, height}，自定义绘制在 canvas 上执行 | AC-6.6 |
| 4 | 组件不支持 DrawModifier | 设置被忽略，IsSupportDrawModifier 返回 false | AC-6.7 |
| 5 | drawModifier 传入 null 且 API ≥ 20 | 清除当前 drawModifier，触发 PROPERTY_UPDATE_RENDER | AC-6.8 |
| 6 | drawModifier 传入 null 且 API < 20 | 设置被忽略 | AC-6.9 |

---

**hoverEffect**

| 属性 | 值 |
|------|-----|
| 函数签名 | `hoverEffect(value: HoverEffectType): T` |
| 返回值 | `T` — 返回组件自身以支持链式调用 |
| 开放范围 | Public |
| 错误码 | N/A |
| 关联 AC | AC-2.1~2.6 |

**参数约束**

| 参数 | 类型 | 必填 | 默认值 | 约束条件 |
|------|------|------|--------|---------|
| value | HoverEffectType | 是 | — | 枚举值：Auto=0, Scale=1, Highlight=2, None=3 (C-API)；内部枚举：NONE=0, OPACITY=1, SCALE=2, BOARD=3, AUTO=4, UNKNOWN=5 |

**行为场景**

| # | 触发条件 | 预期行为 | 关联 AC |
|---|----------|----------|---------|
| 1 | hoverEffect(AUTO) | 框架根据组件类型选择最佳悬停效果 | AC-2.1 |
| 2 | hoverEffect(SCALE) | 鼠标悬停时组件产生均匀缩放 | AC-2.2 |
| 3 | hoverEffect(HIGHLIGHT) | 鼠标悬停时组件背景亮度变化 | AC-2.3 |
| 4 | hoverEffect(NONE) | 无悬停视觉效果 | AC-2.4 |

---

**clickEffect**

| 属性 | 值 |
|------|-----|
| 函数签名 | `clickEffect(value: ClickEffect \| null): T` |
| 返回值 | `T` — 返回组件自身以支持链式调用 |
| 开放范围 | Public |
| 错误码 | N/A |
| 关联 AC | AC-3.1~3.8 |

**参数约束**

| 参数 | 类型 | 必填 | 默认值 | 约束条件 |
|------|------|------|--------|---------|
| value.level | ClickEffectLevel | 是 | — | LIGHT=0, MIDDLE=1, HEAVY=2, UNDEFINED=-1 |
| value.scale | number | 否 | DEFAULT_SCALE_LIGHT(LIGHT)/DEFAULT_SCALE_MIDDLE_OR_HEAVY(MIDDLE/HEAVY) | 范围 [0, 1]；超出范围使用默认值 |

**行为场景**

| # | 触发条件 | 预期行为 | 关联 AC |
|---|----------|----------|---------|
| 1 | clickEffect({ level: LIGHT }) | 轻微缩放 spring 动画 | AC-3.1 |
| 2 | clickEffect({ level: MIDDLE }) | 中等缩放 spring 动画 | AC-3.2 |
| 3 | clickEffect({ level: HEAVY }) | 较强缩放 spring 动画 | AC-3.3 |
| 4 | clickEffect(null) | 重置 clickEffect 为 UNDEFINED | AC-3.4 |
| 5 | scale 值超出 [0,1] 范围 | 使用默认值 | AC-3.7 |

---

**customProperty**

| 属性 | 值 |
|------|-----|
| 函数签名 | `customProperty(name: string, value: Optional<Object>): T` |
| 返回值 | `T` — 返回组件自身以支持链式调用 |
| 开放范围 | Public |
| 错误码 | N/A |
| 关联 AC | AC-5.1~5.5 |

**参数约束**

| 参数 | 类型 | 必填 | 默认值 | 约束条件 |
|------|------|------|--------|---------|
| name | string | 是 | — | 键名 |
| value | Object | 是 | — | 值对象；undefined 触发移除 |

**行为场景**

| # | 触发条件 | 预期行为 | 关联 AC |
|---|----------|----------|---------|
| 1 | customProperty("key", "value") | key-value 存入 FrameNode.customPropertyMap_ | AC-5.1 |
| 2 | 查询已存储的 key | 返回对应值 | AC-5.2 |
| 3 | customProperty("key", undefined) | key 从 customPropertyMap_ 中移除 | AC-5.3 |
| 4 | 查询不存在的 key | 返回 false/空 | AC-5.4 |

---

## 兼容性声明

- **已有 API 行为变更:**
  - **API 12**: attributeModifier 新增 applySelectedAttribute/applyHoveredAttribute 方法（新增，不影响旧调用）
  - **API 12**: ClickEffect 新增 MIDDLE 等级（ClickEffectLevel::MIDDLE = 1，新增枚举值）
  - **API 20**: drawModifier 传入 null/undefined 时行为变更：API < 20 忽略设置，API ≥ 20 清除 drawModifier 并触发 PROPERTY_UPDATE_RENDER
  - 内部 HoverEffectType 枚举映射差异：内部 NONE=0/OPACITY=1/SCALE=2/BOARD=3/AUTO=4/UNKNOWN=5，C-API AUTO=0/SCALE=1/HIGHLIGHT=2/NONE=3，二者枚举值不同但行为一致
- **配置文件格式变更:** 否
- **数据存储格式变更:** 否
- **最低支持版本:** API 8
- **API 版本号策略:** @since 8 为 stateStyles/hoverEffect 基础，@since 12 为 attributeModifier/clickEffect/customProperty，@since 14 为 drawModifier

---

## 架构约束

| 关键约束 | 约束说明 | 影响 AC |
|----------|---------|---------|
| UI_STATE 位掩码管理 | StateStyleManager 使用 uint64_t 位掩码管理多状态，通过 |= 和 ^= 操作合并/移除状态 | AC-1.3~1.7 |
| attributeModifier 覆盖链 | attributeModifier 优先级高于 stateStyles；同一属性被两者设置时以 attributeModifier 为准 | AC-4.7 |
| DrawModifier 组件支持限制 | 仅 IsSupportDrawModifier 返回 true 的组件支持 drawModifier；Canvas/XComponent/Video 等组件不支持 | AC-6.7 |
| Spring 动画参数固化 | clickEffect 的 spring 参数（velocity/mass/stiffness/damping）为引擎内部常量，不可由开发者自定义 | AC-3.1~3.3 |
| ExtensionHandler 中转 | drawModifier 通过 ExtensionHandler 中转到 FrameNode；ExtensionHandler.AttachFrameNode 建立 host 关联 | AC-6.1~6.5 |

---

## 非功能性需求

| 类型 | 指标/阈值 | 验证方式 | 证据 |
|------|-----------|----------|------|
| 性能 | stateStyles 状态切换（FireStateFunc）< 1ms | benchmark | — |
| 性能 | drawModifier 单次 Draw() 绘制 < 5ms | benchmark | — |
| 内存 | DrawModifier 五个回调函数指针 + DrawingContext 栈上对象 | hidumper | — |

---

## 多设备适配声明

| 设备类型 | 行为差异 | 规格/约束 | 验证方式 | 证据 |
|----------|----------|-----------|----------|------|
| 手机 | hoverEffect 在触屏设备上无鼠标悬停事件，不触发 | 鼠标类设备才触发 hover | 交互测试 | — |
| 平板 | hoverEffect 在鼠标连接时触发 | 外接鼠标支持 | 交互测试 | — |
| 折叠屏 | 行为与手机一致 | — | — | — |

---

## 全局特性影响

| 特性 | 适用？ | 结论 | 关联场景 |
|------|--------|------|----------|
| 无障碍 | 是 | stateStyles 中 focused 状态样式可增强焦点可见性；clickEffect 缩放动画不影响无障碍语义 | AC-1.5, AC-3.1 |
| 大字体 | 是 | stateStyles 和 attributeModifier 中设置的文本属性受大字体缩放影响 | AC-1.1, AC-4.1 |
| 深色模式 | 是 | stateStyles/attributeModifier 中颜色属性需适配深色模式 | AC-1.1, AC-4.1 |
| 多窗口/分屏 | 否 | 状态效果与窗口无关 | — |
| 多用户 | 否 | 无用户级别差异 | — |
| 版本升级 | 是 | API 12 新增 attributeModifier/clickEffect 方法；API 20 drawModifier null 处理变更 | AC-4.7, AC-6.8~6.9 |
| 生态兼容 | 是 | HoverEffectType 内部枚举与 C-API 枚举映射不同（值不同但语义一致），跨前端需注意映射 | AC-2.1~2.4 |

---

## 行为场景（可选，Gherkin）

Feature: 状态效果与自定义属性
  作为 应用开发者
  我想要 为组件设置多状态样式和自定义绘制能力
  以便 实现丰富的交互视觉反馈和自定义渲染

  Scenario: stateStyles 多状态样式切换
    Given 组件设置了 stateStyles({ normal: { backgroundColor: '#FFFFFF' }, pressed: { backgroundColor: '#DDDDDD' } })
    When 用户触摸按下该组件
    Then 组件背景色变为 '#DDDDDD'（Pressed 覆盖 Normal）
    When 用户触摸抬起
    Then 组件背景色恢复为 '#FFFFFF'（回退到 Normal）

  Scenario: attributeModifier 覆盖 stateStyles
    Given 组件同时设置了 stateStyles({ pressed: { backgroundColor: '#DDDDDD' } }) 和 attributeModifier({ applyPressedAttribute: (inst) => inst.backgroundColor('#BBBBBB') })
    When 用户触摸按下该组件
    Then 组件背景色为 '#BBBBBB'（attributeModifier 优先于 stateStyles）

  Scenario: hoverEffect 悬停反馈类型
    Given 组件设置了 hoverEffect(HoverEffectType.SCALE)
    When 用户鼠标悬停到该组件
    Then 组件产生均匀缩放效果
    When 用户鼠标离开该组件
    Then 缩放效果取消

  Scenario: clickEffect 点击反馈
    Given 组件设置了 clickEffect({ level: ClickEffectLevel.LIGHT, scale: 0.9 })
    When 用户点击该组件（触摸按下）
    Then 组件产生 spring 缩放动画（scaleValue = sqrt(0.9)）
    When 用户触摸抬起
    Then 缩放动画恢复

  Scenario: drawModifier 自定义绘制
    Given 组件设置了 drawModifier({ drawBehind: (ctx) => ctx.canvas.drawRect(...), drawOverlay: (ctx) => ctx.canvas.drawText(...) })
    When 组件进入渲染 pass
    Then drawBehind 在内容绘制前执行，drawOverlay 在最上层执行
    And DrawingContext 的 canvas 为组件渲染画布，width/height 为组件渲染区域尺寸

---

## Spec 自审清单

- [x] 无"待定""TBD""TODO"等占位符
- [x] 所有 AC 使用 WHEN/THEN 格式，可独立测试
- [x] 范围边界明确（做什么/不做什么清晰）
- [x] 无语义模糊表述（"快速""稳定""尽可能"等）
- [x] AC 与规则表交叉一致（每个 AC 至少关联一条规则，每条规则至少关联一个 AC）
- [x] 规则表每条通过 5 项质量检查（可复现/可观测/边界值/关联AC/无冲突）

---

## context-references

```yaml
context-queries:
  - repo: "openharmony/ace_engine"
    query: "StateStyleManager UI_STATE 位掩码管理与状态刷新流程 (state_style_manager.h:48, state_style_manager.cpp:234)"
  - repo: "openharmony/ace_engine"
    query: "HoverEffectType 内部枚举与 C-API 枚举映射 (mouse_constants.h:48, native_type.h:1328)"
  - repo: "openharmony/ace_engine"
    query: "ClickEffect spring 动画参数与 scale 计算 (rosen_render_context.cpp:7623)"
  - repo: "openharmony/ace_engine"
    query: "AttributeModifier 接口定义与各状态 apply 方法 (ark_component/types/index.d.ts:785)"
  - repo: "openharmony/ace_engine"
    query: "DrawModifier 五阶段绘制与 DrawingContext 定义 (modifier.h:82-99)"
  - repo: "openharmony/ace_engine"
    query: "customProperty 存储与查询路径 (frame_node.h:1445-1459)"
  - repo: "openharmony/ace_engine"
    query: "attributeModifier vs stateStyles 优先级覆盖链"
```

**关键文档：**
- StateStyleManager: `frameworks/core/components_ng/event/state_style_manager.h:48`
- HoverEffectType 枚举: `frameworks/core/event/mouse_constants.h:48`
- ClickEffectLevel: `frameworks/core/components/common/properties/effect_option.h:28`
- AttributeModifier 接口: `frameworks/bridge/declarative_frontend/ark_component/types/index.d.ts:785`
- DrawModifier/DrawingContext: `frameworks/core/components_ng/base/modifier.h:82-99`
- customProperty: `frameworks/core/components_ng/base/frame_node.h:1445-1459`
- C-API HoverEffect: `interfaces/native/native_type.h:1328`
