# 特性规格

> Func-04-05-02-Feat-02 多状态属性应用与按位分发：固化 `applyUIAttributes` 分发逻辑——`applyNormalAttribute` 始终调用、其余 5 个状态态按 `currentUIState & UI_STATE_*` 位与方法定义双条件调用，静态范式状态变化重应用，以及 `applyHoveredAttribute` 的 API 26.0.0 版本差异。

## 概述

| 属性 | 值 |
|------|-----|
| 特性名称 | 多状态属性应用与按位分发 (Multi-State Attribute Apply & Bitwise Dispatch) |
| 特性编号 | Func-04-05-02-Feat-02 |
| 所属 Epic | 无（已有能力补录） |
| 优先级 | P0 |
| 目标版本 | applyNormal/Pressed/Focused/Disabled/Selected 动态 @since 11/12、静态 @since 23；applyHoveredAttribute 动态/静态 @since 26.0.0 |
| SIG 归属 | ArkUI SIG |
| 状态 | Baselined |
| 复杂度 | 复杂 |

## 本次变更范围（Delta）

> 历史规格补齐，补录已有实现的完整行为规格。

## 输入文档

| 文档 | 路径 | 状态 |
|------|------|------|
| Design | `specs/04-common-capability/05-custom-extension/02-dynamic-attributes/design.md` | Baselined |

---

## 用户故事

### US-1: applyNormalAttribute 始终调用

**作为** 应用开发者,
**我想要** applyNormalAttribute 作为默认态基线始终被调用,
**以便** 建立组件的无状态默认属性。

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-1.1 | WHEN applyUIAttributes 执行且 applyNormalAttribute 已定义 THEN 始终调用 modifier.applyNormalAttribute(component)（ArkComponent.ts:63-65），不受 UI 状态影响 | 正常 |
| AC-1.2 | WHEN applyNormalAttribute 未定义 THEN 跳过，不报错 | 异常 |
| AC-1.3 | WHEN 多个 apply* 定义 THEN applyNormalAttribute 最先调用，先于状态态 apply*（:63 先于 :66-80） | 边界 |

### US-2: 状态态按位条件调用

**作为** 应用开发者,
**我想要** 状态态 apply* 仅在组件处于对应状态且方法已定义时调用,
**以便** 按状态叠加属性。

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-2.1 | WHEN (currentUIState & UI_STATE_HOVERED) 且 applyHoveredAttribute 已定义 THEN 调用 applyHoveredAttribute（:66-68） | 正常 |
| AC-2.2 | WHEN (currentUIState & UI_STATE_PRESSED) 且 applyPressedAttribute 已定义 THEN 调用 applyPressedAttribute（:69-71） | 正常 |
| AC-2.3 | WHEN (currentUIState & UI_STATE_FOCUSED) 且 applyFocusedAttribute 已定义 THEN 调用 applyFocusedAttribute（:72-74） | 正常 |
| AC-2.4 | WHEN (currentUIState & UI_STATE_DISABLED) 且 applyDisabledAttribute 已定义 THEN 调用 applyDisabledAttribute（:75-77） | 正常 |
| AC-2.5 | WHEN (currentUIState & UI_STATE_SELECTED) 且 applySelectedAttribute 已定义 THEN 调用 applySelectedAttribute（:78-80） | 正常 |
| AC-2.6 | WHEN 状态位未命中（currentUIState & 位 == 0）THEN 该态 apply* 不调用，即使已定义 | 边界 |
| AC-2.7 | WHEN 状态位命中但对应 apply* 未定义 THEN 该态不调用（双条件：位命中 && 方法定义） | 边界 |

### US-3: applyHoveredAttribute 版本差异

**作为** 应用开发者,
**我想要** 了解 applyHoveredAttribute 是 API 26.0.0 后增回调,
**以便** 正确处理跨版本兼容。

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-3.1 | WHEN API ≥ 26.0.0 且 modifier 定义 applyHoveredAttribute THEN 悬停态时被调用（动态 common.d.ts:18567 @since 26.0.0 dynamic） | 正常 |
| AC-3.2 | WHEN API < 26.0.0 THEN applyHoveredAttribute 在 SDK 类型中未声明（@since 26.0.0 dynamic），开发者无法声明该方法 → modifier 对象不含 → applyUIAttributesInit 不置 UI_STATE_HOVERED 位。**无运行时 API 版本门控**——applyUIAttributesInit 仅检查 `modifier.applyHoveredAttribute !== undefined`（ArkComponent.ts:40-42），不检查 API 版本；若 modifier 对象含该方法则无论 API 版本都会使用 | 边界 |
| AC-3.3 | WHEN 静态 API ≥ 26.0.0 THEN applyHoveredAttribute @since 26.0.0 static（common.static.d.ets:10846），AttributeModifierState.HOVERED=1<<4（enums.static.d.ets:4835 @since 26.0.0 staticonly） | 正常 |

### US-4: 静态范式状态变化重应用

**作为** 应用开发者,
**我想要** 静态范式在组件状态变化时按新状态位重应用对应 apply*,
**以便** 声明式地随状态变化更新属性。

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-4.1 | WHEN 静态范式首次应用 THEN applyUIAttributes(modifier, attributeSet, state) 调 applyNormalAttribute 后按 state & UI_STATE_* 调状态态（ArkCommonModifier.ets:36） | 正常 |
| AC-4.2 | WHEN 组件状态变化（静态范式）THEN applyUIAttributesUpdate 按新 state 位重应用对应 apply*（:55） | 正常 |
| AC-4.3 | WHEN 静态范式 state=0（monitoredStates 返回 0）THEN 仅 applyNormalAttribute 调用，无状态态 | 边界 |

## 验收追溯

| AC | 关联规则 | 关联 Task | 验证方式 | 证据 |
|----|----------|-----------|----------|------|
| AC-1.1~1.3 | R-1~R-3 | 已有实现 | 单测 | `ArkComponent.ts:63-65` |
| AC-2.1~2.7 | R-4~R-8 | 已有实现 | 单测 | `ArkComponent.ts:66-80` |
| AC-3.1~3.3 | R-9~R-11 | 已有实现 | XTS/契约 | `common.d.ts:18567`, `enums.static.d.ets:4835` |
| AC-4.1~4.3 | R-12~R-14 | 已有实现 | 单测 | `ArkCommonModifier.ets:36/55` |

## 规则定义

> **统一规则表，取消 FR/BR/EX/RC 四分类。** 类型标签：**行为**、**边界**、**异常**、**恢复**。

| 规则ID | 类型 | 触发条件 | 预期行为 | 边界/约束 | 关联AC |
|--------|------|----------|----------|-----------|--------|
| R-1 | 行为 | applyUIAttributes + applyNormalAttribute 已定义 | 始终调用 applyNormalAttribute(component)，不受 UI 状态影响 | 最先调用 | AC-1.1 |
| R-2 | 异常 | applyNormalAttribute 未定义 | 跳过，不报错 | 可选回调（带 ?） | AC-1.2 |
| R-3 | 边界 | 多个 apply* 定义 | applyNormalAttribute 先于状态态 apply* | 调用顺序 :63 → :66-80 | AC-1.3 |
| R-4 | 行为 | currentUIState & UI_STATE_HOVERED && applyHoveredAttribute 定义 | 调用 applyHoveredAttribute | 双条件 | AC-2.1 |
| R-5 | 行为 | currentUIState & UI_STATE_PRESSED && applyPressedAttribute 定义 | 调用 applyPressedAttribute | 双条件 | AC-2.2 |
| R-6 | 行为 | currentUIState & UI_STATE_FOCUSED && applyFocusedAttribute 定义 | 调用 applyFocusedAttribute | 双条件 | AC-2.3 |
| R-7 | 行为 | currentUIState & UI_STATE_DISABLED && applyDisabledAttribute 定义 | 调用 applyDisabledAttribute | 双条件 | AC-2.4 |
| R-8 | 行为 | currentUIState & UI_STATE_SELECTED && applySelectedAttribute 定义 | 调用 applySelectedAttribute | 双条件 | AC-2.5 |
| R-9 | 边界 | 状态位未命中 | 该态 apply* 不调用，即使已定义 | currentUIState & 位 == 0 | AC-2.6 |
| R-10 | 边界 | 状态位命中但 apply* 未定义 | 该态不调用 | 双条件缺一不可 | AC-2.7 |
| R-11 | 行为 | API ≥ 26.0.0 + applyHoveredAttribute 定义 + 悬停态 | 调用 applyHoveredAttribute | @since 26.0.0 dynamic | AC-3.1 |
| R-12 | 边界 | API < 26.0.0 | applyHoveredAttribute 在 SDK 类型未声明（@since 26.0.0），开发者无法声明 → modifier 不含 → 不置 UI_STATE_HOVERED | 类型级约束，非运行时门控（applyUIAttributesInit 仅检查方法存在性，不检查 API 版本） | AC-3.2 |
| R-13 | 行为 | 静态 applyHoveredAttribute | @since 26.0.0 static；HOVERED=1<<4 @since 26.0.0 staticonly | 与动态对齐 | AC-3.3 |
| R-14 | 行为 | 静态 applyUIAttributes(modifier, attributeSet, state) | applyNormalAttribute 后按 state & UI_STATE_* 调状态态 | 与动态同构 | AC-4.1 |
| R-15 | 行为 | 静态状态变化 | applyUIAttributesUpdate 按新 state 重应用对应 apply* | 声明式重应用 | AC-4.2 |
| R-16 | 边界 | 静态 state=0 | 仅 applyNormalAttribute，无状态态 | monitoredStates 返回 0 | AC-4.3 |

## 验证映射

| 编号 | 对应规格项 | 验证方式 | 验证重点 |
|------|------------|----------|----------|
| VM-1 | R-1~R-3, AC-1.1~1.3 | 单测 | applyNormalAttribute 始终先调 |
| VM-2 | R-4~R-10, AC-2.1~2.7 | 单测 | 5 状态态双条件调用 |
| VM-3 | R-11~R-13, AC-3.1~3.3 | XTS/契约 | applyHoveredAttribute 类型级约束（无运行时门控） |
| VM-4 | R-14~R-16, AC-4.1~4.3 | 单测 | 静态状态变化重应用 |
| VM-5 | 全量 | XTS/集成 | 状态驱动属性端到端 |

---

## API 变更分析

> 补录已有 API，非新增。

### 新增 API

| API 名称 | 开放范围 | 入参概要 | 返回值 | 错误码范围 | 功能描述 | 关联 AC |
|----------|----------|----------|--------|-----------|----------|---------|
| `applyNormalAttribute?(instance: T): void` (动态 @since 11/12 / 静态 @since 23) | Public | instance: T | void | 无 | 默认态属性更新，始终调用 | AC-1.1~1.3 |
| `applyPressedAttribute?(instance: T): void` (动态 @since 11/12 / 静态 @since 23) | Public | instance: T | void | 无 | 按下态属性更新 | AC-2.2 |
| `applyFocusedAttribute?(instance: T): void` (动态 @since 11/12 / 静态 @since 23) | Public | instance: T | void | 无 | 聚焦态属性更新 | AC-2.3 |
| `applyDisabledAttribute?(instance: T): void` (动态 @since 11/12 / 静态 @since 23) | Public | instance: T | void | 无 | 禁用态属性更新 | AC-2.4 |
| `applySelectedAttribute?(instance: T): void` (动态 @since 11/12 / 静态 @since 23) | Public | instance: T | void | 无 | 选中态属性更新 | AC-2.5 |
| `applyHoveredAttribute?(instance: T): void` (动态 @since 26.0.0 / 静态 @since 26.0.0) | Public | instance: T | void | 无 | 悬停态属性更新（API 26.0.0 后增） | AC-3.1~3.3 |

### 变更/废弃 API

无。applyHoveredAttribute 为 API 26.0.0 后增，属版本演进。

> **d.ts 交叉验证：** 6 apply 方法签名与 `common.d.ts:18471/18492/18513/18534/18555/18567`、`common.static.d.ets:10796/10806/10816/10826/10836/10846` 一致。

---

## 接口规格

### 接口定义

**apply*Attribute**

| 属性 | 值 |
|------|-----|
| 函数签名 | `applyNormalAttribute?(instance: T): void` 等 6 个（动态可选带 `?`，静态 `default` 默认实现） |
| 返回值 | `void` |
| 开放范围 | Public |
| 错误码 | 无 |
| 关联 AC | AC-1.1~3.3 |

**参数约束**

| 参数 | 类型 | 必填 | 默认值 | 约束条件 |
|------|------|------|--------|---------|
| instance | T | 是 | 无（框架传入） | 组件 Attribute 实例；开发者只读设置属性 |

**行为场景**

| # | 触发条件 | 预期行为 | 关联 AC |
|---|----------|----------|---------|
| 1 | applyNormalAttribute 定义 | 始终调用，先于状态态 | AC-1.1 |
| 2 | 状态位命中 && 方法定义 | 调用对应 apply* | AC-2.1~2.5 |
| 3 | 状态位未命中 | 不调用 | AC-2.6 |
| 4 | API < 26.0.0 | SDK 类型未声明 applyHoveredAttribute，开发者无法声明 → modifier 不含 → 不置位（无运行时 API 门控） | AC-3.2 |
| 5 | 静态状态变化 | applyUIAttributesUpdate 重应用 | AC-4.2 |

---

## 兼容性声明

- **已有 API 行为变更:** 否。6 个 apply 自各自 @since 起稳定。applyHoveredAttribute 为 26.0.0 后增。
- **配置文件格式变更:** 否
- **数据存储格式变更:** 否
- **最低支持版本:** applyNormal/Pressed/Focused/Disabled/Selected 动态 API 11（@atomicservice 12）/静态 23；applyHoveredAttribute 动态/静态 API 26.0.0
- **API 版本号策略:** 5 个基础 apply 动态 @since 11 / @atomicservice 12、静态 @since 23；applyHoveredAttribute 动态/静态 @since 26.0.0

## 架构约束

| 关键约束 | 约束说明 | 影响 AC |
|----------|----------|---------|
| Normal 无条件 | applyNormalAttribute 始终调，先于状态态 | AC-1.1, AC-1.3 |
| 双条件调用 | 状态位命中 && 方法定义 | AC-2.1~2.7 |
| Hovered 类型级约束 | API 26.0.0 后增（类型级，非运行时门控） | AC-3.2 |
| 静态重应用 | applyUIAttributesUpdate 状态变化重应用 | AC-4.2 |

## 非功能性需求

| 类型 | 指标/阈值 | 验证方式 | 证据 |
|------|----------|----------|------|
| 性能 | 分发为同步按位检查，无额外帧 | 单测 | ArkComponent.ts:59-81 |
| 可靠性 | 可选回调（带 ?）未定义即跳过，不报错 | 单测 | ArkComponent.ts:63 |
| 可测试性 | 各状态态可独立单测（mock currentUIState） | 单测 | ArkComponent.ts:66-80 |

## 多设备适配声明

| 设备类型 | 行为差异 | 规格/约束 | 验证方式 | 证据 |
|----------|----------|----------|----------|------|
| 手机 | 无差异 | — | — | — |
| 平板 | 无差异 | — | — | — |
| 折叠屏 | 无差异 | — | — | — |

## 全局特性影响

| 特性 | 适用？ | 结论 | 关联场景 |
|------|--------|------|----------|
| 无障碍 | 是 | Focused/Disabled/Selected 态可能影响无障碍相关属性 | AC-2.3~2.5 |
| 大字体 | 否 | — | — |
| 深色模式 | 否 | — | — |
| 多窗口/分屏 | 否 | — | — |
| 多用户 | 否 | — | — |
| 版本升级 | 是 | applyHoveredAttribute 26.0.0 后增 | AC-3.1~3.3 |
| 生态兼容 | 是 | @crossplatform | — |

## Spec 自审清单

- [x] 无"待定""TBD""TODO"等占位符
- [x] 所有 AC 使用 WHEN/THEN 格式，可独立测试
- [x] 范围边界明确（多状态分发；装配见 Feat-01、命令式类见 04-05-06）
- [x] 无语义模糊表述
- [x] AC 与规则表交叉一致
- [x] 规则表每条通过 5 项质量检查

## context-references

```yaml
context-queries:
  - repo: "openharmony/arkui_ace_engine"
    query: "ArkComponent applyUIAttributes applyNormalAttribute 状态态按位分发 applyUIAttributesUpdate"
  - repo: "openharmony/interface/sdk-js"
    query: "AttributeModifier 6 个 apply 方法 applyHoveredAttribute @since 26.0.0"
```

**关键文档：** design.md（DESIGN-Func-04-05-02），SDK `common.d.ts:18471-18567`、`ArkCommonModifier.ets:36/55`
