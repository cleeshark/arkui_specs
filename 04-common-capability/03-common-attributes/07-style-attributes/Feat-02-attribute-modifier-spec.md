# 特性规格

> Func-04-03-07-Feat-02 动态属性设置（attributeModifier）：固化 attributeModifier 多态样式相关 API 的行为规格。

## 概述

| 属性 | 值 |
|------|-----|
| 特性名称 | 动态属性设置 (AttributeModifier Polymorphic Style) |
| 特性编号 | Func-04-03-07-Feat-02 |
| 所属 Epic | 无（已有能力补录） |
| 优先级 | P1 |
| 目标版本 | API 10 起支持 |
| SIG 归属 | ArkUI SIG |
| 状态 | Baselined |
| 复杂度 | 复杂 |

## 本次变更范围（Delta）

> 历史规格补齐，补录已有实现的完整行为规格。

| 类型 | 内容 | 说明 |
|------|------|------|
| ADDED | attributeModifier 多态样式 API 行为规格 | 已有实现，补录完整行为规格（仅覆盖多态样式相关 API，不含全部 Modifier 机制） |

## 输入文档

| 文档 | 路径 | 状态 |
|------|------|------|
| Design | `specs/04-common-capability/03-common-attributes/07-style-attributes/design.md` | Baselined |

> 需求基线、不涉及项、受影响子系统与仓库详见 proposal.md，本文档不重复摘录。design.md 与本文档并行产出，互不依赖。

---

## 用户故事

### US-1: 使用 attributeModifier 设置多态样式

**作为** 应用开发者,
**我想要** 通过 `.attributeModifier(AttributeModifier<T>)` 为组件注入按状态切换的样式修改器,
**以便** 用面向对象方式定义 Normal/Pressed/Focused/Disabled/Selected/Hovered 六种状态下的属性修改。

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-1.1 | WHEN 调用 `.attributeModifier(myModifier)` 且 myModifier 实现了 applyNormalAttribute THEN attributeModifierFunc 创建 CommonModifier（ModifierType.STATE），调用 myModifier.applyNormalAttribute(instance)，注册 UI_STATE_NORMAL 到 supportedStates_ | 正常 |
| AC-1.2 | WHEN myModifier 实现了 applyPressedAttribute THEN applyUIAttributesInit 注册 UI_STATE_PRESSED 到 supportedStates_；Pressed 状态激活时调用 applyPressedAttribute | 正常 |
| AC-1.3 | WHEN myModifier 实现了 applyFocusedAttribute THEN 注册 UI_STATE_FOCUSED；Focused 状态激活时调用 applyFocusedAttribute | 正常 |
| AC-1.4 | WHEN myModifier 实现了 applyDisabledAttribute THEN 注册 UI_STATE_DISABLED；Disabled 状态激活时调用 applyDisabledAttribute | 正常 |
| AC-1.5 | WHEN myModifier 实现了 applySelectedAttribute THEN 注册 UI_STATE_SELECTED；Selected 状态激活时调用 applySelectedAttribute | 正常 |
| AC-1.6 | WHEN myModifier 实现了 applyHoveredAttribute THEN 注册 UI_STATE_HOVERED；Hovered 状态激活时调用 applyHoveredAttribute | 正常 |
| AC-1.7 | WHEN myModifier 仅实现 applyNormalAttribute THEN 仅注册 UI_STATE_NORMAL，其他状态不触发回调 | 边界 |
| AC-1.8 | WHEN 在 attributeModifier 上下文中调用 `.stateStyles()` THEN 抛出 BusinessError(100201, 'stateStyles not supportted in attributeModifier scenario.') | 异常 |
| AC-1.9 | WHEN attributeModifier 与 stateStyles 同一组件上使用 THEN ArkTS 层互斥（stateStyles 抛异常）；C++ StateStyleManager 中 attributeModifier 使用 userStateStyleSubscribers_，stateStyles 使用 frontendSubscribers_，两者共享同一 manager | 边界 |

### US-2: 使用 AttributeUpdater 动态更新样式

**作为** 应用开发者,
**我想要** 通过 AttributeUpdater 子类实现样式动态更新,
**以便** 在运行时根据数据变化重新应用属性修改。

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-2.1 | WHEN 使用 AttributeUpdater 且 modifierState === INIT(0) THEN attributeModifierFunc 调用 initializeModifier(instance)，注册 supportedStates_，applyModifierPatch 刷新到 native | 正常 |
| AC-2.2 | WHEN 使用 AttributeUpdater 且 modifierState === UPDATE(1) THEN attributeModifierFunc 调用 onComponentChanged(instance)（如 native pointer 变化），applyNormalAttribute + applyUIAttributes 按当前状态回调，applyModifierPatch 刷新 | 正常 |
| AC-2.3 | WHEN AttributeUpdater.applyNormalAttribute 修改属性值 THEN ModifierUtils.applySetOnChange 检测变化，applyAndMergeModifier 合并属性到 CommonModifier | 正常 |

### US-3: 使用 excludeInner 抑制系统默认状态样式

**作为** C-API 开发者,
**我想要** 通过 OH_ArkUI_AddSupportedUIStates 的 excludeInner 参数抑制系统默认状态样式,
**以便** 仅使用自定义的状态样式效果，避免默认样式叠加。

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-3.1 | WHEN 调用 OH_ArkUI_AddSupportedUIStates(node, state, handler, excludeInner=true) THEN userSubscribersExcludeConfigs_ |= state，HandleStateChangeInternal 对该状态跳过 inner 回调 | 正常 |
| AC-3.2 | WHEN excludeInner=false THEN inner 回调正常执行，效果为 inner + user 回调叠加 | 正常 |
| AC-3.3 | WHEN Button 组件设置 excludeInner=true for PRESSED THEN Button 默认 Pressed 效果被抑制，仅 user 回调效果生效 | 边界 |

---

## 验收追溯

| AC | 关联规则 | 关联 Task | 验证方式 | 证据 |
|----|---------|----------|----------|------|
| AC-1.1~1.6 | R-1 | — | 单测 | attributeModifierFunc 状态注册 |
| AC-1.7 | R-1 | — | 单测 | 仅 Normal 无其他状态回调 |
| AC-1.8 | R-3 | — | 单测 | stateStyles 互斥异常 |
| AC-1.9 | R-4 | — | 单测 | 两条 subscriber 路径并存 |
| AC-2.1~2.3 | R-2 | — | 单测 | AttributeUpdater 生命周期 |
| AC-3.1~3.3 | R-5 | — | 单测 | excludeInner 抑制 inner 回调 |

---

## 规则定义

| 规则ID | 类型 | 触发条件 | 预期行为 | 边界/约束 | 关联AC |
|--------|------|----------|----------|-----------|--------|
| R-1 | 行为 | attributeModifier 设置多态样式 | attributeModifierFunc 创建 CommonModifier(ModifierType.STATE)；applyUIAttributesInit 注册 UI_STATE 位掩码到 supportedStates_；状态激活时 HandleStateChangeInternal 执行 userStateStyleSubscribers_ 回调 | AttributeModifier<T> 接口方法：applyNormalAttribute?/applyPressedAttribute?/applyFocusedAttribute?/applyDisabledAttribute?/applySelectedAttribute?/applyHoveredAttribute?；monitoredStates() 返回位掩码（Arkoala 版本） | AC-1.1~1.7 |
| R-2 | 行为 | AttributeUpdater 动态更新 | modifierState INIT(0) 时调用 initializeModifier → applyNormalAttribute → applyUIAttributes → applyModifierPatch；UPDATE(1) 时调用 onComponentChanged → applyNormalAttribute → applyUIAttributes → applyModifierPatch | AttributeUpdater.StateEnum: INIT=0, UPDATE=1；applyAndMergeModifier 合并属性值 | AC-2.1~2.3 |
| R-3 | 异常 | stateStyles 在 attributeModifier 上下文中调用 | ArkComponent.stateStyles 抛出 BusinessError(100201) | 互斥仅限于 ArkTS 层；C++ StateStyleManager 中两条路径可并存 | AC-1.8 |
| R-4 | 边界 | attributeModifier 与 stateStyles 共享 StateStyleManager | attributeModifier 使用 userStateStyleSubscribers_ 路径；stateStyles 使用 frontendSubscribers_ 路径；HandleStateChangeInternal 按 inner→frontend→user 优先级链执行；user 回调存在时 skipFrontendForcibly=true | frontend 路径跳过不阻止 native 状态注册 | AC-1.9 |
| R-5 | 行为 | excludeInner 抑制系统默认状态样式 | AddSupportedUIStateWithCallback(isInner=false, excludeInner=true) 设置 userSubscribersExcludeConfigs_ |= state；HandleStateChangeInternal 对该状态 IsExcludeInner=true → 跳过 inner 回调 | OH_ArkUI_AddSupportedUIStates @since 20；excludeInner 默认 false | AC-3.1~3.3 |

---

## 验证映射

| 编号 | 对应规格项 | 验证方式 | 验证重点 |
|------|------------|----------|----------|
| VM-1 | R-1, AC-1.1~1.7 | 单测 | attributeModifierFunc 状态注册与回调 |
| VM-2 | R-2, AC-2.1~2.3 | 单测 | AttributeUpdater INIT/UPDATE 生命周期 |
| VM-3 | R-3, AC-1.8 | 单测 | stateStyles 在 modifier 上下文抛异常 |
| VM-4 | R-4, AC-1.9 | 单测 |两条 subscriber 路径优先级链 |
| VM-5 | R-5, AC-3.1~3.3 | 单测 | excludeInner 抑制 inner 回调 |
| VM-6 | 全量 | XTS/集成 | 端到端 attributeModifier 多态样式正确 |

---

## API 变更分析

### 新增 API

| API 签名 | 开放范围 | 入参概要 | 返回值 | 错误码范围 | 功能描述 | 关联 AC |
|----------|---------|---------|--------|-----------|---------|---------|
| `attributeModifier(modifier: AttributeModifier<T>): T` | Public | AttributeModifier<T>{applyNormalAttribute?, applyPressedAttribute?, applyFocusedAttribute?, applyDisabledAttribute?, applySelectedAttribute?, applyHoveredAttribute?} | T | — | 动态属性修改器 | AC-1.1~1.7 |
| `OH_ArkUI_AddSupportedUIStates(node, state, handler, excludeInner, userData)` | Public | ArkUI_UIState bitmask + handler callback + excludeInner bool | int32_t (0=成功) | — | C-API 状态样式注册 | AC-3.1~3.3 |

**关联类型定义：**

| 类型名 | 定义 | 位置 |
|--------|------|------|
| `AttributeModifier<T>` | `{ applyNormalAttribute?(instance: T): void; applyPressedAttribute?; applyFocusedAttribute?; applyDisabledAttribute?; applySelectedAttribute?; applyHoveredAttribute?; initializeModifier?; onComponentChanged? }` | core.d.ts:761-768 / index.d.ts:785-795 |
| `AttributeUpdater<T>` | AttributeModifier 子类，`{ state: INIT|UPDATE; attribute; isAttributeUpdater }` | modifier_utilities.ts:269-319 |
| `ArkUI_UIState` | NORMAL=0, PRESSED=1, FOCUSED=2, DISABLED=4, SELECTED=8, HOVERED=16 | native_type.h:1664-1680 |

### 变更/废弃 API

N/A，已有能力补录，API 行为无变化。

---

## 接口规格

### 接口定义

**attributeModifier**

| 属性 | 值 |
|------|-----|
| 函数签名 | `attributeModifier(modifier: AttributeModifier<T>): T` |
| 返回值 | `T` — 返回组件自身以支持链式调用 |
| 开放范围 | Public |
| 错误码 | N/A |
| 关联 AC | AC-1.1~1.9 |

**参数约束**

| 参数 | 类型 | 必填 | 默认值 | 约束条件 |
|------|------|------|--------|---------|
| modifier | AttributeModifier<T> | 是 | — | 可选方法：applyNormalAttribute/applyPressedAttribute/applyFocusedAttribute/applyDisabledAttribute/applySelectedAttribute/applyHoveredAttribute；在 modifier 上下文中调用 stateStyles 会抛 BusinessError(100201) |

**行为场景**

| # | 触发条件 | 预期行为 | 关联 AC |
|---|----------|----------|---------|
| 1 | attributeModifier(myModifier) 且实现所有 6 个状态方法 | 所有 UI_STATE 注册到 supportedStates_ | AC-1.1~1.6 |
| 2 | attributeModifier(myModifier) 仅实现 applyNormalAttribute | 仅 UI_STATE_NORMAL 注册 | AC-1.7 |
| 3 | 在 attributeModifier 上下文中调用 stateStyles | 抛出 BusinessError(100201) | AC-1.8 |
| 4 | AttributeUpdater(modifierState=INIT) | initializeModifier → applyNormalAttribute → applyModifierPatch | AC-2.1 |
| 5 | AttributeUpdater(modifierState=UPDATE) | onComponentChanged → applyNormalAttribute → applyUIAttributes → applyModifierPatch | AC-2.2 |

---

**OH_ArkUI_AddSupportedUIStates**

| 属性 | 值 |
|------|-----|
| 函数签名 | `int32_t OH_ArkUI_AddSupportedUIStates(ArkUI_NodeHandle node, int32_t state, void* statesChangeHandler, bool isExcludeInner, void* userData)` |
| 返回值 | `int32_t` — 0 表示成功 |
| 开放范围 | Public |
| 错误码 | N/A |
| 关联 AC | AC-3.1~3.3 |

**参数约束**

| 参数 | 类型 | 必填 | 默认值 | 约束条件 |
|------|------|------|--------|---------|
| node | ArkUI_NodeHandle | 是 | — | 有效 FrameNode handle |
| state | int32_t (ArkUI_UIState bitmask) | 是 | — | 可组合多个 UIState |
| statesChangeHandler | void* (function pointer) | 是 | — | 回调接收 currentState uint64_t |
| isExcludeInner | bool | 否 | false | true=抑制系统默认样式 |
| userData | void* | 否 | NULL | 透传到回调 |

**行为场景**

| # | 触发条件 | 预期行为 | 关联 AC |
|---|----------|----------|---------|
| 1 | excludeInner=true | userSubscribersExcludeConfigs_ |= state，inner 回调被跳过 | AC-3.1 |
| 2 | excludeInner=false | inner + user 回调叠加执行 | AC-3.2 |

---

## 兼容性声明

- **已有 API 行为变更:** 否
- **配置文件格式变更:** 否
- **数据存储格式变更:** 否
- **最低支持版本:** API 10 (attributeModifier)，API 20 (OH_ArkUI_AddSupportedUIStates)
- **API 版本号策略:** @since 10 为 attributeModifier ArkTS API，@since 20 为 C-API AddSupportedUIStates

---

## 架构约束

| 关键约束 | 约束说明 | 影响 AC |
|----------|---------|---------|
| attributeModifier 与 stateStyles ArkTS 层互斥 | ArkComponent.stateStyles 在 modifier 上下文抛 BusinessError(100201)；C++ 层两条 subscriber 路径可并存 | AC-1.8, AC-1.9 |
| HandleStateChangeInternal 优先级链 | inner→frontend→user 三级回调；user 回调存在时 skipFrontendForcibly=true | AC-1.9 |
| excludeInner 位掩码控制 | userSubscribersExcludeConfigs_ 为 UIState 位掩码，按状态粒度控制是否跳过 inner | AC-3.1~3.3 |
| AttributeUpdater 生命周期 | StateEnum INIT/UPDATE 控制首次初始化 vs 动态更新流程 | AC-2.1~2.2 |

---

## 非功能性需求

| 类型 | 指标/阈值 | 验证方式 | 证据 |
|------|-----------|----------|------|
| 性能 | attributeModifier 状态切换回调 < 1ms | benchmark | — |

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
| 无障碍 | 是 | attributeModifier 可修改 focused 状态样式增强焦点可见性 | AC-1.3 |
| 大字体 | 是 | attributeModifier 修改的文本属性受大字体缩放影响 | AC-1.1 |
| 深色模式 | 是 | attributeModifier 修改的颜色属性需适配深色模式 | AC-1.1 |
| 多窗口/分屏 | 否 | 属性修改与窗口无关 | — |
| 多用户 | 否 | 无用户级别差异 | — |
| 版本升级 | 是 | OH_ArkUI_AddSupportedUIStates 为 API 20 新增 | AC-3.1 |
| 生态兼容 | 是 | excludeInner 机制仅 C-API 支持，ArkTS attributeModifier 自动抑制 inner | AC-3.1~3.3 |

---

## 风险 / Risks

| 风险ID | 类型 | 描述 | 影响AC | 缓解策略 |
|--------|------|------|--------|----------|
| RK-1 | 行为 | stateStyles 在 attributeModifier 上下文抛异常（ArkTS 层互斥），但 C++ 层两条路径可并存 | AC-1.8 | ArkTS 层严格互斥；C++ 层 user 回调优先级高于 frontend |
| RK-2 | 版本 | OH_ArkUI_AddSupportedUIStates 为 API 20 新增，旧版本无 C-API 状态样式入口 | AC-3.1 | @since 20 版本守护 |
| RK-3 | 行为 | excludeInner=false 时 inner + user 效果叠加（默认 Pressed 效果 + 自定义效果同时生效），开发者可能期望仅自定义效果 | AC-3.2 | C-API 文档已标注 excludeInner 说明；ArkTS attributeModifier 自动处理 |

---

## Spec 自审清单

- [x] 无"待定""TBD""TODO"等占位符
- [x] 所有 AC 使用 WHEN/THEN 格式，可独立测试
- [x] 范围边界明确（做什么/不做什么清晰——仅多态样式相关 API，不含完整 Modifier 机制）
- [x] 无语义模糊表述
- [x] AC 与规则表交叉一致
- [x] 规则表每条通过 5 项质量检查

---

## context-references

```yaml
context-queries:
  - repo: "openharmony/ace_engine"
    query: "AttributeModifier<T> interface definition (ark_modifier/types/core.d.ts:761-768, index.d.ts:785-795)"
  - repo: "openharmony/ace_engine"
    query: "attributeModifierFunc implementation (ark_component/src/ArkComponent.ts:6387-6460)"
  - repo: "openharmony/ace_engine"
    query: "StateStyleManager HandleStateChangeInternal priority chain (state_style_manager.cpp:234-278)"
  - repo: "openharmony/ace_engine"
    query: "excludeInner mechanism (state_style_manager.cpp:183-207, native_node.h:14212-14243)"
  - repo: "openharmony/ace_engine"
    query: "AttributeUpdater lifecycle (modifier_utilities.ts:269-319, AttributeUpdater.ets:21-50)"
```

**关键文档：**
- AttributeModifier interface: `frameworks/bridge/declarative_frontend/ark_modifier/types/core.d.ts:761-768`
- AttributeModifier extended: `frameworks/bridge/declarative_frontend/ark_component/types/index.d.ts:785-795`
- attributeModifierFunc: `frameworks/bridge/declarative_frontend/ark_component/src/ArkComponent.ts:6387-6460`
- StateStyleManager: `frameworks/core/components_ng/event/state_style_manager.h:48`
- excludeInner: `frameworks/core/components_ng/event/state_style_manager.cpp:183-207`
- OH_ArkUI_AddSupportedUIStates docs: `interfaces/native/native_node.h:14212-14243`
- AttributeUpdater: `frameworks/bridge/declarative_frontend/ark_modifier/src/modifier_utilities.ts:269-319`
