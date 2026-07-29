# 特性规格

> Func-04-05-02-Feat-01 AttributeModifier 装配与状态监听：固化 `.attributeModifier()` 绑定入口、`applyUIAttributesInit` 按方法存在性推断 UI 状态位掩码并经 `setSupportedUIState` 注册监听，以及动态/静态双范式状态声明差异的行为规格。

## 概述

| 属性 | 值 |
|------|-----|
| 特性名称 | AttributeModifier 装配与状态监听 (AttributeModifier Mounting & State Registration) |
| 特性编号 | Func-04-05-02-Feat-01 |
| 所属 Epic | 无（已有能力补录） |
| 优先级 | P0 |
| 目标版本 | 动态 API 11 起（@atomicservice 12）；静态 API 23 起（含 monitoredStates） |
| SIG 归属 | ArkUI SIG |
| 状态 | Baselined |
| 复杂度 | 标准 |

## 本次变更范围（Delta）

> 历史规格补齐，补录已有实现的完整行为规格。

## 输入文档

| 文档 | 路径 | 状态 |
|------|------|------|
| Design | `specs/04-common-capability/05-custom-extension/02-dynamic-attributes/design.md` | Baselined |

---

## 用户故事

### US-1: 通过 attributeModifier 装配

**作为** 应用开发者,
**我想要** 通过 `.attributeModifier(modifier)` 将实现 AttributeModifier<T> 的对象绑定到组件,
**以便** 让框架按组件状态动态应用属性。

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-1.1 | WHEN 调用 `.attributeModifier(modifier)` 且 modifier 实现了 AttributeModifier<T> THEN modifier 绑定到组件 peer，后续渲染时由 applyUIAttributes 分发 | 正常 |
| AC-1.2 | WHEN 动态范式调用 THEN 不经 declarative_frontend C++（js_view_abstract.cpp 无 attributeModifier 绑定），经 ark_component TS peer + 原生模块装配 | 正常 |
| AC-1.3 | WHEN 静态范式调用 THEN 经每组件 static.d.ets 声明的联合类型重载（如 `AttributeModifier<ButtonAttribute> \| AttributeModifier<CommonMethod> \| undefined`）装配 | 正常 |
| AC-1.4 | WHEN 动态范式传入 undefined THEN attributeModifierFunc 检测 `modifier === undefined \|\| modifier === null`（ArkComponent.ts:6391），输出 debug 日志 "custom modifier is undefined" 并 return——静默 no-op，不抛错、不移除已绑 modifier、不设 null、无任何效果（与静态签名 `\| undefined` 暗示的移除语义不同，见风险 R-undefined-noop） | 边界 |

### US-2: UI 状态监听注册

**作为** 框架开发者,
**我想要** applyUIAttributesInit 按 modifier 上已定义的 apply* 方法自动推断需监听的 UI 状态位,
**以便** 仅注册必要状态监听，避免全量监听浪费。

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-2.1 | WHEN applyUIAttributesInit 执行 THEN 依次检查 applyHoveredAttribute/applyPressedAttribute/applyFocusedAttribute/applyDisabledAttribute/applySelectedAttribute 是否 `!== undefined`，已定义者 OR 对应 UI_STATE_* 位（ArkComponent.ts:40-54） | 正常 |
| AC-2.2 | WHEN 状态位掩码计算完成 THEN 调 getUINativeModule().setSupportedUIState(nativeNode, state) 注册需监听的状态集合（:56） | 正常 |
| AC-2.3 | WHEN modifier 未定义任何状态态 apply*（仅 applyNormalAttribute）THEN state=0，不监听任何状态态，仅 applyNormalAttribute 被调用 | 边界 |
| AC-2.4 | WHEN applyNormalAttribute 是否定义 THEN 不参与 setSupportedUIState 状态位（Normal 非状态态） | 正常 |

### US-3: 静态范式状态声明差异

**作为** 应用开发者,
**我想要** 静态范式通过 monitoredStates() 显式声明监听状态,
**以便** 静态可分析地声明状态集，而非依赖方法存在性推断。

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-3.1 | WHEN 静态范式 THEN monitoredStates(): int（common.static.d.ets:10858，@since 23 staticonly）返回监听状态位掩码，作为 state 参数传入 applyUIAttributes | 正常 |
| AC-3.2 | WHEN 静态范式 AttributeModifierState 枚举 THEN 值为位掩码：NORMAL=0/PRESSED=1/FOCUSED=1<<1/DISABLED=1<<2/SELECTED=1<<3/HOVERED=1<<4（enums.static.d.ets:4790-4835） | 正常 |
| AC-3.3 | WHEN 动态范式 THEN 不使用 monitoredStates，改用方法存在性推断（applyUIAttributesInit），两范式枚举值对齐但推断方式不同 | 边界 |

## 验收追溯

| AC | 关联规则 | 关联 Task | 验证方式 | 证据 |
|----|----------|-----------|----------|------|
| AC-1.1~1.4 | R-1~R-4 | 已有实现 | 单测/XTS | `common.d.ts:25179`, `ArkComponent.ts:59` |
| AC-2.1~2.4 | R-5~R-8 | 已有实现 | 单测 | `ArkComponent.ts:40-56` |
| AC-3.1~3.3 | R-9~R-11 | 已有实现 | 单测 | `common.static.d.ets:10858`, `enums.static.d.ets:4781` |

## 规则定义

> **统一规则表，取消 FR/BR/EX/RC 四分类。** 类型标签：**行为**（正常路径下的系统行为）、**边界**（输入/状态的临界点）、**异常**（非法输入或异常状态的处理）、**恢复**（系统异常后的恢复策略）。

| 规则ID | 类型 | 触发条件 | 预期行为 | 边界/约束 | 关联AC |
|--------|------|----------|----------|-----------|--------|
| R-1 | 行为 | 调用 `.attributeModifier(modifier)` 且 modifier 实现 AttributeModifier<T> | modifier 绑定到组件 peer，渲染时由 applyUIAttributes 分发 | modifier 为实现接口的对象 | AC-1.1 |
| R-2 | 行为 | 动态范式装配 | 经 ark_component TS peer + 原生模块，不经 declarative_frontend C++ | js_view_abstract.cpp 无 attributeModifier 绑定 | AC-1.2 |
| R-3 | 行为 | 静态范式装配 | 经每组件 static.d.ets 联合类型重载装配 | 联合含 AttributeModifier<T> \| AttributeModifier<CommonMethod> \| undefined | AC-1.3 |
| R-4 | 边界 | 动态传入 undefined/null | attributeModifierFunc 检测 modifier===undefined\|\|null → debug 日志 "custom modifier is undefined" + return（静默 no-op，不抛错/不移除已绑 modifier/不设 null） | ArkComponent.ts:6391-6394；各组件 attributeModifier 均 call attributeModifierFunc | AC-1.4 |
| R-5 | 行为 | applyUIAttributesInit | 依次检查 5 个状态态 apply* 是否 !== undefined，已定义者 OR UI_STATE_* 位 | Hovered/Pressed/Focused/Disabled/Selected | AC-2.1 |
| R-6 | 行为 | 状态位计算完成 | 调 setSupportedUIState(nativeNode, state) 注册监听 | 经 getUINativeModule 原生桥 | AC-2.2 |
| R-7 | 边界 | modifier 仅定义 applyNormalAttribute | state=0，不监听状态态，仅 applyNormalAttribute 调用 | 无状态态 apply* | AC-2.3 |
| R-8 | 行为 | applyNormalAttribute 是否定义 | 不参与 setSupportedUIState 状态位 | Normal 非状态态 | AC-2.4 |
| R-9 | 行为 | 静态范式 | monitoredStates(): int 返回监听位掩码，作 state 参数传入 applyUIAttributes | @since 23 staticonly | AC-3.1 |
| R-10 | 行为 | AttributeModifierState 枚举 | 位掩码 NORMAL=0/PRESSED=1/FOCUSED=1<<1/DISABLED=1<<2/SELECTED=1<<3/HOVERED=1<<4 | 与动态 UI_STATE_* 对齐 | AC-3.2 |
| R-11 | 边界 | 动态 vs 静态推断方式 | 动态用方法存在性推断（applyUIAttributesInit），静态用 monitoredStates 显式声明；枚举值对齐 | 两范式语义一致 | AC-3.3 |

## 验证映射

| 编号 | 对应规格项 | 验证方式 | 验证重点 |
|------|------------|----------|----------|
| VM-1 | R-1~R-4, AC-1.1~1.4 | 单测/XTS | attributeModifier 装配与双范式路径 |
| VM-2 | R-5~R-8, AC-2.1~2.4 | 单测 | applyUIAttributesInit 状态位推断与 setSupportedUIState |
| VM-3 | R-9~R-11, AC-3.1~3.3 | 单测 | 静态 monitoredStates 与枚举位掩码 |
| VM-4 | 全量 | XTS/集成 | 装配后状态监听端到端生效 |

---

## API 变更分析

> 补录已有 API，非新增。

### 新增 API

| API 名称 | 开放范围 | 入参概要 | 返回值 | 错误码范围 | 功能描述 | 关联 AC |
|----------|----------|----------|--------|-----------|----------|---------|
| `attributeModifier(modifier: AttributeModifier<T>): T` (动态 @since 11, @atomicservice 12) / `default attributeModifier(modifier: AttributeModifier<T> \| undefined): this` (静态 @since 23) | Public | modifier: AttributeModifier<T> 实例（静态可 undefined） | T/this（链式） | 无 | 将 AttributeModifier 绑定到组件 | AC-1.1~1.4 |
| `monitoredStates(): int` (静态 @since 23 staticonly) | Public | 无 | int（状态位掩码） | 无 | 声明需监听的 UI 状态集合 | AC-3.1 |

### 变更/废弃 API

无。

> **d.ts 交叉验证：** attributeModifier 动态 `common.d.ts:25179`、静态 `common.static.d.ets` 各组件文件；monitoredStates `common.static.d.ets:10858`；AttributeModifierState `enums.static.d.ets:4781`。

---

## 接口规格

### 接口定义

**attributeModifier**

| 属性 | 值 |
|------|-----|
| 函数签名 | `attributeModifier(modifier: AttributeModifier<T>): T`（动态）/ `default attributeModifier(modifier: AttributeModifier<T> \| undefined): this`（静态） |
| 返回值 | `T` / `this` — 链式 |
| 开放范围 | Public |
| 错误码 | 无 |
| 关联 AC | AC-1.1, AC-1.3, AC-1.4 |

**参数约束**

| 参数 | 类型 | 必填 | 默认值 | 约束条件 |
|------|------|------|--------|---------|
| modifier | AttributeModifier<T> \| undefined | 否（静态）/ 是（动态） | undefined | 实现 AttributeModifier<T> 接口的对象；动态无 undefined 重载 |

**行为场景**

| # | 触发条件 | 预期行为 | 关联 AC |
|---|----------|----------|---------|
| 1 | modifier 实现 AttributeModifier<T> | 绑定到 peer，渲染时分发 | AC-1.1 |
| 2 | 动态范式 | 经 ark_component TS + 原生模块 | AC-1.2 |
| 3 | 静态范式 | 经组件 static.d.ets 联合重载 | AC-1.3 |
| 4 | 动态 undefined | 静默 no-op（debug 日志 + return，不移除/不设 null） | AC-1.4 |

---

## 兼容性声明

- **已有 API 行为变更:** 否。attributeModifier 自动态 API 11/12、静态 API 23 起稳定。
- **动态 undefined 行为与静态签名不一致:** 动态 attributeModifierFunc 对 undefined/null 静默 no-op（debug 日志 + return，不移除已绑 modifier）；静态签名 `attributeModifier(modifier: AttributeModifier<T> | undefined): this`（common.static.d.ets）含 undefined 暗示移除语义。动态实际为 no-op 而非 removal——开发者不可依赖传 undefined 移除已绑 modifier（见 AC-1.4、R-4）。
- **配置文件格式变更:** 否
- **数据存储格式变更:** 否
- **最低支持版本:** 动态 API 11（@atomicservice 12），静态 API 23
- **API 版本号策略:** 动态 @since 11 / @atomicservice 12；静态 @since 23（monitoredStates staticonly）

## 架构约束

| 关键约束 | 约束说明 | 影响 AC |
|----------|----------|---------|
| 动态不经 C++ | js_view_abstract.cpp 无 attributeModifier，经 ark_component TS | AC-1.2 |
| 状态位按方法存在性推断 | applyUIAttributesInit OR 已定义方法的 UI_STATE_* | AC-2.1 |
| Normal 不入状态位 | applyNormalAttribute 不参与 setSupportedUIState | AC-2.4 |
| 静态显式声明 | monitoredStates() 返回位掩码 | AC-3.1 |

## 非功能性需求

| 类型 | 指标/阈值 | 验证方式 | 证据 |
|------|----------|----------|------|
| 性能 | 装配为 peer 存对象，状态注册为单次原生调用 | 单测 | ArkComponent.ts:56 |
| 内存 | 每 modifier 一个 peer 句柄 | 单测 | arkoala_api_generated.h:307 |
| 可测试性 | 状态位推断可单测覆盖 | 单测 | ArkComponent.ts:40-56 |

## 多设备适配声明

| 设备类型 | 行为差异 | 规格/约束 | 验证方式 | 证据 |
|----------|----------|----------|----------|------|
| 手机 | 无差异 | — | — | — |
| 平板 | 无差异 | — | — | — |
| 折叠屏 | 无差异 | — | — | — |

## 全局特性影响

| 特性 | 适用？ | 结论 | 关联场景 |
|------|--------|------|----------|
| 无障碍 | 否 | 状态监听不改变无障碍语义 | — |
| 大字体 | 否 | — | — |
| 深色模式 | 否 | — | — |
| 多窗口/分屏 | 否 | — | — |
| 多用户 | 否 | — | — |
| 版本升级 | 是 | 动态 11/12、静态 23 引入；applyHoveredAttribute 26.0.0 | AC-3.1, AC-3.2 |
| 生态兼容 | 是 | @crossplatform | — |

## Spec 自审清单

- [x] 无"待定""TBD""TODO"等占位符
- [x] 所有 AC 使用 WHEN/THEN 格式，可独立测试
- [x] 范围边界明确（装配/状态监听；多状态分发见 Feat-02、命令式类见 04-05-06）
- [x] 无语义模糊表述
- [x] AC 与规则表交叉一致
- [x] 规则表每条通过 5 项质量检查

## context-references

```yaml
context-queries:
  - repo: "openharmony/arkui_ace_engine"
    query: "ArkComponent applyUIAttributesInit setSupportedUIState AttributeModifier 状态位注册"
  - repo: "openharmony/interface/sdk-js"
    query: "AttributeModifier 接口 attributeModifier 方法 monitoredStates AttributeModifierState 枚举"
```

**关键文档：** design.md（DESIGN-Func-04-05-02），SDK `common.d.ts:18450/25179`、`common.static.d.ets:10787/10858`、`enums.static.d.ets:4781`
