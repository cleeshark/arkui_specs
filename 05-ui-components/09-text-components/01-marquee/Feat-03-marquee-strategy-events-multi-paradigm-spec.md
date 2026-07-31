# 特性规格

> Func-05-09-01-Feat-03 滚动策略、事件回调与多范式：固化 marqueeUpdateStrategy 滚动策略、onStart/onBounce/onFinish/onStop 四个事件回调，以及 MarqueeModifier/attributeModifier/setMarqueeOptions 多范式入口与 Cangjie FFI（无公开 NDK C-API）的行为规格。

## 概述

| 属性 | 值 |
|------|-----|
| 特性名称 | 滚动策略、事件回调与多范式 (Scroll Strategy, Events & Multi-Paradigm) |
| 特性编号 | Func-05-09-01-Feat-03 |
| 所属 Epic | 无（已有能力补录） |
| 优先级 | P0 |
| 目标版本 | API 8 起支持 onStart/onBounce/onFinish，API 12 新增 marqueeUpdateStrategy/MarqueeModifier，API 26 新增 onStop/setMarqueeOptions |
| SIG 归属 | ArkUI SIG |
| 状态 | Baselined |
| 复杂度 | 标准 |

## 本次变更范围（Delta）

> 历史规格补齐，补录已有实现的完整行为规格。

| 类型 | 内容 | 说明 |
|------|------|------|
| ADDED | marqueeUpdateStrategy 滚动策略行为规格 | API 12 起，DEFAULT/PRESERVE_POSITION |
| ADDED | onStart/onBounce/onFinish 事件行为规格 | API 8 起 |
| ADDED | onStop 事件行为规格 | API 26 起 |
| ADDED | MarqueeModifier/attributeModifier 多范式行为规格 | API 12/23 |
| ADDED | setMarqueeOptions 静态 API 行为规格 | API 26.1 起，unpublished |
| ADDED | Cangjie FFI 与 NDK 差异说明 | 已知缺口 |

## 输入文档

| 文档 | 路径 | 状态 |
|------|------|------|
| Design | `specs/05-ui-components/09-text-components/01-marquee/design.md` | Baselined |

---

## 用户故事

### US-1: 设置滚动策略

**作为** 应用开发者,
**我想要** 通过 `.marqueeUpdateStrategy()` 设置文本更新后的滚动策略,
**以便** 控制文本变更时是否保留当前位置。

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-1.1 | WHEN 调用 `.marqueeUpdateStrategy(MarqueeUpdateStrategy.DEFAULT)` 且属性变更 THEN 动画停止并从头重启（`marquee_pattern.cpp:160-172`） | 正常 |
| AC-1.2 | WHEN 调用 `.marqueeUpdateStrategy(MarqueeUpdateStrategy.PRESERVE_POSITION)` 且 spacing/delay 已设置且无其他动画参数变更 THEN 保留当前滚动位置继续运行（`marquee_pattern.cpp:485-497` GetTextOffset） | 正常 |
| AC-1.3 | WHEN 策略为 PRESERVE_POSITION 但未设置 spacing/delay（NeedSecondChild=false）THEN 仍走 DEFAULT 停止重启路径（`marquee_pattern.cpp:166` `!NeedSecondChild()`） | 边界 |
| AC-1.4 | WHEN 策略为 PRESERVE_POSITION 且动画参数（step/loop/direction/delay）变更（AnimationParamChange）THEN 走 StopMarqueeAnimation 重启，不保留位置（`marquee_pattern.cpp:166`） | 边界 |
| AC-1.5 | WHEN 未设置策略 THEN 默认 MarqueeUpdateStrategy::DEFAULT（`marquee_pattern.cpp:160` value_or(DEFAULT)） | 边界 |
| AC-1.6 | WHEN reset 策略 THEN dirty flag 为 PROPERTY_UPDATE_NORMAL（`marquee_model_ng.cpp:149,285`） | 正常 |
| AC-1.7 | WHEN 桥接解析策略字符串 THEN "default"→DEFAULT，"preserve_position"→PRESERVE_POSITION（`arkts_native_marquee_bridge.cpp:441-462`） | 正常 |

### US-2: onStart 事件

**作为** 应用开发者,
**我想要** 监听跑马灯开始滚动的事件,
**以便** 在滚动启动时执行逻辑。

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-2.1 | WHEN start=true 且 IsRunMarquee()=true THEN 触发 onStart（`marquee_pattern.cpp:194-195` FireStartEvent） | 正常 |
| AC-2.2 | WHEN 文本未超出组件宽度（IsRunMarquee()=false）THEN 不触发 onStart（`marquee_pattern.cpp:181-185` 提前返回） | 边界 |
| AC-2.3 | WHEN 重复滚动 THEN onStart 仅在首次启动触发一次（hasStart_ 置位），后续轮次不重复触发 | 正常 |
| AC-2.4 | WHEN 设置 onStart 为 undefined THEN 解绑当前回调（`arkts_native_marquee_bridge.cpp:475-503`） | 异常 |

### US-3: onBounce 事件

**作为** 应用开发者,
**我想要** 监听跑马灯到达终点的中途事件,
**以便** 在每轮滚动到达边界时执行逻辑。

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-3.1 | WHEN 单文本滚动每轮到达终点 THEN 触发 onBounce（`marquee_pattern.cpp:301` ActionAnimation alt-callback） | 正常 |
| AC-3.2 | WHEN 双文本滚动每轮到达中间零位 THEN 触发 onBounce（`marquee_pattern.cpp:1219` ActionDoubleAnimation alt-callback） | 正常 |
| AC-3.3 | WHEN loop 不为 1 THEN onBounce 在多轮中多次触发（SDK 注释 marquee.d.ts:309-311） | 边界 |
| AC-3.4 | WHEN loop=1（needSecondPlay=false）THEN onBounce 仍按动画中间关键帧触发一次 | 边界 |

### US-4: onFinish 事件

**作为** 应用开发者,
**我想要** 监听跑马灯完成全部循环次数的事件,
**以便** 在滚动结束时执行逻辑。

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-4.1 | WHEN 有限 loop 完成 N 轮 THEN 触发 onFinish（`marquee_pattern.cpp:307` OnAnimationFinish FireFinishEvent） | 正常 |
| AC-4.2 | WHEN 双文本有限 loop 完成且 !isFirst THEN 触发 onFinish（`marquee_pattern.cpp:314` OnDoubleAnimationFinish） | 正常 |
| AC-4.3 | WHEN loop=-1 无限循环 THEN 永不触发 onFinish | 边界 |
| AC-4.4 | WHEN 终态顺序 THEN onStop 先于 onFinish 触发（`marquee_pattern.cpp:276-277` ExecuteStopMarquee 后 OnAnimationFinish） | 正常 |
| AC-4.5 | WHEN 有限多轮动画倒数第二轮完成且 newPlayCount 减为 0 THEN 提前返回不触发 onStop/onFinish（`marquee_pattern.cpp:280-283` 已知边界） | 异常 |

### US-5: onStop 事件

**作为** 应用开发者,
**我想要** 监听跑马灯停止滚动的事件 (@since 26),
**以便** 在滚动停止（非完成）时执行逻辑。

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-5.1 | WHEN 滚动停止且 hasStart_=true 且 GetTextOffset()==0 THEN 触发 onStop（`marquee_pattern.cpp:392-399` ExecuteStopMarquee） | 正常 |
| AC-5.2 | WHEN hasStart_ 为 false（未触发过 onStart）THEN 不触发 onStop（`marquee_pattern.cpp:395`） | 边界 |
| AC-5.3 | WHEN 策略为 DEFAULT 且 GetTextOffset()==0 THEN onStop 可触发（offset 检查通过） | 正常 |
| AC-5.4 | WHEN 策略为 PRESERVE_POSITION 且保留 offset 非 0 THEN onStop 不触发（GetTextOffset()!=0） | 边界 |
| AC-5.5 | WHEN 设置 onStop 为 undefined THEN 解绑当前回调（`marquee.d.ts:336-352`） | 异常 |
| AC-5.6 | WHEN onStop 是 API 26 新增 THEN 旧版本（API 8-25）不支持，需 @since 26 标注 | 边界 |

### US-6: 使用 MarqueeModifier 与 attributeModifier

**作为** 应用开发者,
**我想要** 通过 MarqueeModifier 动态修改跑马灯属性,
**以便** 声明式地动态更新样式与事件。

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-6.1 | WHEN 使用 MarqueeModifier (@since 12) THEN 暴露 fontSize/fontColor/allowScale/fontWeight/fontFamily/onStart/onBounce/onFinish/marqueeUpdateStrategy（`marquee_modifier.ts:16-73`，`MarqueeModifier.d.ts`） | 正常 |
| AC-6.2 | WHEN MarqueeModifier 未暴露 onStop THEN TS Modifier 层不支持 onStop（需走 Marquee 属性 API，`marquee_modifier.ts`） | 边界 |
| AC-6.3 | WHEN 调用 `.attributeModifier(modifier)` (@since 23 静态) THEN 接受 AttributeModifier<MarqueeAttribute> 或 AttributeModifier<CommonMethod>（`marquee.static.d.ets` attributeModifier） | 正常 |
| AC-6.4 | WHEN MarqueeModifier.applyNormalAttribute 调用 THEN 通过 ModifierUtils.applyAndMergeModifier 合并属性（`marquee_modifier.ts:82-85`） | 正常 |
| AC-6.5 | WHEN 旧版非 NG pipeline 使用 MarqueeModifier THEN onStop/resetOnStop 为 nullptr 不支持（`marquee_dynamic_modifier.cpp:656-657` legacy 路径） | 边界 |

### US-7: 静态 setMarqueeOptions 与 Cangjie FFI / NDK 差异

**作为** 跨语言开发者,
**我想要** 了解各范式入口的差异与缺口,
**以便** 选择合适的接入方式。

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-7.1 | WHEN 使用静态 setMarqueeOptions (@since 26.1) THEN 解析 step/loop/src/start/direction 并 apply（`marquee_static_modifier.cpp:84-116`） | 正常 |
| AC-7.2 | WHEN setMarqueeOptions 解析 spacing/delay THEN 解析但未 apply（无 SetMarqueeSpacing/SetMarqueeDelay 调用，`marquee_static_modifier.cpp:84-116`） | 异常 |
| AC-7.3 | WHEN 使用静态双签名 Marquee(style: CustomBuilderT) (@since 26.1) THEN 通过 Builder 风格构造（`marquee.static.d.ets`） | 正常 |
| AC-7.4 | WHEN Cangjie FFI 调用 FfiOHOSAceFrameworkMarqueeCreate THEN 支持 start/src/step/loop/fromStart 五参数（`cj_marquee_ffi.h:26`） | 正常 |
| AC-7.5 | WHEN Cangjie FFI 设置事件 THEN 仅支持 onStart/onBounce/onFinish，不支持 onStop（`cj_marquee_ffi.h:33-35`） | 边界 |
| AC-7.6 | WHEN Cangjie FFI 设置 spacing/delay/direction THEN 不支持（无对应 FFI 函数，`cj_marquee_ffi.h:26-35`） | 边界 |
| AC-7.7 | WHEN 通过公开 NDK Node C-API 访问独立 Marquee THEN 不存在（NDK 仅有 Text 组件的 ArkUI_TextMarqueeOptions，`interfaces/native/node_attributes/text.h:130`） | 边界 |
| AC-7.8 | WHEN Cangjie FFI 内部 THEN 直调 MarqueeModelNG 实例方法，绕过 CJUIMarqueeModifier（`cj_marquee_ffi.cpp:28` 注释标注待切换至 CJUIModifier） | 边界 |

## 验收追溯

| AC | 关联规则 | 关联 Task | 验证方式 | 证据 |
|----|----------|----------|----------|------|
| AC-1.1 | R-1 | TASK-03 | UI 测试 | marquee_pattern.cpp:160-172 |
| AC-1.2 | R-2 | TASK-03 | UI 测试 | marquee_pattern.cpp:485-497 |
| AC-1.3 | R-3 | TASK-03 | 边界测试 | marquee_pattern.cpp:166 |
| AC-1.4 | R-3 | TASK-03 | 边界测试 | marquee_pattern.cpp:166 |
| AC-1.5 | R-4 | TASK-03 | 单测 | marquee_pattern.cpp:160 |
| AC-1.6 | R-5 | TASK-03 | 单测 | marquee_model_ng.cpp:149,285 |
| AC-1.7 | R-6 | TASK-03 | 桥接测试 | arkts_native_marquee_bridge.cpp:441-462 |
| AC-2.1 | R-7 | TASK-03 | UI 测试 | marquee_pattern.cpp:194-195 |
| AC-2.2 | R-8 | TASK-03 | UI 测试 | marquee_pattern.cpp:181-185 |
| AC-2.3 | R-7 | TASK-03 | UI 测试 | marquee_pattern.cpp:194 |
| AC-2.4 | R-9 | TASK-03 | 异常测试 | arkts_native_marquee_bridge.cpp:475-503 |
| AC-3.1 | R-10 | TASK-03 | UI 测试 | marquee_pattern.cpp:301 |
| AC-3.2 | R-10 | TASK-03 | UI 测试 | marquee_pattern.cpp:1219 |
| AC-3.3 | R-11 | TASK-03 | 边界测试 | marquee.d.ts:309-311 |
| AC-3.4 | R-11 | TASK-03 | 边界测试 | marquee_pattern.cpp:301 |
| AC-4.1 | R-12 | TASK-03 | UI 测试 | marquee_pattern.cpp:307 |
| AC-4.2 | R-12 | TASK-03 | UI 测试 | marquee_pattern.cpp:314 |
| AC-4.3 | R-13 | TASK-03 | 边界测试 | marquee_pattern.cpp:280 |
| AC-4.4 | R-14 | TASK-03 | 顺序测试 | marquee_pattern.cpp:276-277 |
| AC-4.5 | R-15 | TASK-03 | 边界测试 | marquee_pattern.cpp:280-283 |
| AC-5.1 | R-16 | TASK-03 | UI 测试 | marquee_pattern.cpp:392-399 |
| AC-5.2 | R-17 | TASK-03 | 边界测试 | marquee_pattern.cpp:395 |
| AC-5.3 | R-18 | TASK-03 | UI 测试 | marquee_pattern.cpp:485-497 |
| AC-5.4 | R-18 | TASK-03 | 边界测试 | marquee_pattern.cpp:489-491 |
| AC-5.5 | R-9 | TASK-03 | 异常测试 | marquee.d.ts:336-352 |
| AC-5.6 | R-19 | TASK-03 | 版本测试 | marquee.d.ts:347-352 |
| AC-6.1 | R-20 | TASK-03 | 多范式测试 | marquee_modifier.ts:16-73 |
| AC-6.2 | R-21 | TASK-03 | 边界测试 | marquee_modifier.ts |
| AC-6.3 | R-22 | TASK-03 | 多范式测试 | marquee.static.d.ets |
| AC-6.4 | R-23 | TASK-03 | 单测 | marquee_modifier.ts:82-85 |
| AC-6.5 | R-24 | TASK-03 | 兼容测试 | marquee_dynamic_modifier.cpp:656-657 |
| AC-7.1 | R-25 | TASK-03 | 静态测试 | marquee_static_modifier.cpp:84-116 |
| AC-7.2 | R-26 | TASK-03 | 异常测试 | marquee_static_modifier.cpp:84-116 |
| AC-7.3 | R-27 | TASK-03 | 静态测试 | marquee.static.d.ets |
| AC-7.4 | R-28 | TASK-03 | Cangjie 测试 | cj_marquee_ffi.h:26 |
| AC-7.5 | R-29 | TASK-03 | Cangjie 测试 | cj_marquee_ffi.h:33-35 |
| AC-7.6 | R-30 | TASK-03 | Cangjie 测试 | cj_marquee_ffi.h:26-35 |
| AC-7.7 | R-31 | TASK-03 | NDK 测试 | interfaces/native/node_attributes/text.h:130 |
| AC-7.8 | R-32 | TASK-03 | Cangjie 测试 | cj_marquee_ffi.cpp:28 |

## 规则定义

| 规则ID | 类型 | 触发条件 | 预期行为 | 边界/约束 | 关联AC |
|--------|------|----------|----------|----------|--------|
| R-1 | 行为 | 策略=DEFAULT 且属性变更 | StopMarqueeAnimation 从头重启 | marquee_pattern.cpp:166-172 | AC-1.1 |
| R-2 | 行为 | 策略=PRESERVE_POSITION 且 spacing/delay 设置且无参数变更 | 保留 lastAnimationOffset 续播 | GetTextOffset 返回保留 offset | AC-1.2 |
| R-3 | 边界 | PRESERVE_POSITION 但 NeedSecondChild=false 或参数变更 | 仍走 DEFAULT 重启 | marquee_pattern.cpp:166 | AC-1.3, AC-1.4 |
| R-4 | 边界 | 未设置策略 | 默认 DEFAULT | value_or(DEFAULT) | AC-1.5 |
| R-5 | 行为 | reset 策略 | dirty flag PROPERTY_UPDATE_NORMAL | marquee_model_ng.cpp:149,285 | AC-1.6 |
| R-6 | 行为 | 桥接解析策略字符串 | "default"→DEFAULT；"preserve_position"→PRESERVE_POSITION | BinarySearchFindIndex | AC-1.7 |
| R-7 | 行为 | start=true 且 IsRunMarquee()=true | hasStart_=true，FireStartEvent | 仅首次触发 | AC-2.1, AC-2.3 |
| R-8 | 边界 | 文本未超出组件宽度 | 不触发 onStart | IsRunMarquee()=false | AC-2.2 |
| R-9 | 异常 | 事件设为 undefined | 解绑当前回调 | bridge reset | AC-2.4, AC-5.5 |
| R-10 | 行为 | 每轮到达终点/零位 | FireBounceEvent | 单/双文本不同触发点 | AC-3.1, AC-3.2 |
| R-11 | 边界 | loop 多轮 | onBounce 多次触发 | loop!=1 时 | AC-3.3, AC-3.4 |
| R-12 | 行为 | 有限 loop 完成 | FireFinishEvent | 单/双路径 | AC-4.1, AC-4.2 |
| R-13 | 边界 | loop=-1 无限 | 永不触发 onFinish | newPlayCount 不减为 0 | AC-4.3 |
| R-14 | 行为 | 终态顺序 | onStop 先于 onFinish | ExecuteStopMarquee→OnAnimationFinish | AC-4.4 |
| R-15 | 异常 | 倒数第二轮 newPlayCount 减为 0 | 提前返回不触发 onStop/onFinish | marquee_pattern.cpp:280-283 | AC-4.5 |
| R-16 | 行为 | 停止且 hasStart_ 且 GetTextOffset()==0 | FireStopEvent | ExecuteStopMarquee | AC-5.1 |
| R-17 | 边界 | hasStart_ 为 false | 不触发 onStop | 未触发过 onStart | AC-5.2 |
| R-18 | 边界 | 策略影响 onStop | DEFAULT offset=0 可触发；PRESERVE_POSITION offset!=0 不触发 | GetTextOffset | AC-5.3, AC-5.4 |
| R-19 | 边界 | onStop @since 26 | API 8-25 不支持 | marquee.d.ts:347-352 | AC-5.6 |
| R-20 | 行为 | MarqueeModifier (@since 12) | 暴露 9 属性/事件（无 onStop） | marquee_modifier.ts | AC-6.1 |
| R-21 | 边界 | TS Modifier 无 onStop | 需走 Marquee 属性 API | marquee_modifier.ts | AC-6.2 |
| R-22 | 行为 | attributeModifier (@since 23 静态) | 接受 AttributeModifier<MarqueeAttribute> 或 <CommonMethod> | marquee.static.d.ets | AC-6.3 |
| R-23 | 行为 | applyNormalAttribute | ModifierUtils.applyAndMergeModifier 合并 | marquee_modifier.ts:82-85 | AC-6.4 |
| R-24 | 边界 | 旧版非 NG MarqueeModifier | onStop/resetOnStop 为 nullptr | legacy 路径 | AC-6.5 |
| R-25 | 行为 | setMarqueeOptions (@since 26.1) | apply step/loop/src/start/direction | marquee_static_modifier.cpp:84-116 | AC-7.1 |
| R-26 | 异常 | setMarqueeOptions 解析 spacing/delay 但未 apply | 无 SetMarqueeSpacing/SetMarqueeDelay 调用 | 已知缺口 | AC-7.2 |
| R-27 | 行为 | 静态双签名 Marquee(style) (@since 26.1) | Builder 风格构造 | marquee.static.d.ets | AC-7.3 |
| R-28 | 行为 | Cangjie FFI Create | 支持 start/src/step/loop/fromStart 五参 | cj_marquee_ffi.h:26 | AC-7.4 |
| R-29 | 边界 | Cangjie FFI 事件 | 仅 onStart/onBounce/onFinish，无 onStop | cj_marquee_ffi.h:33-35 | AC-7.5 |
| R-30 | 边界 | Cangjie FFI 缺 spacing/delay/direction setter | 无对应函数 | cj_marquee_ffi.h:26-35 | AC-7.6 |
| R-31 | 边界 | 公开 NDK 无独立 Marquee | 仅 Text 的 ArkUI_TextMarqueeOptions | interfaces/native/node_attributes/text.h:130 | AC-7.7 |
| R-32 | 边界 | Cangjie FFI 绕过 CJUIMarqueeModifier | 直调 ModelNG 实例 | cj_marquee_ffi.cpp:28 注释待切换 | AC-7.8 |

## 验证映射

| 编号 | 对应规格项 | 验证方式 | 验证重点 |
|------|----------|----------|----------|
| VM-1 | AC-1.1 ~ AC-1.7 | UI 测试 + 边界测试 | 策略 DEFAULT/PRESERVE_POSITION 与触发条件 |
| VM-2 | AC-2.1 ~ AC-2.4 | UI 测试 + 异常测试 | onStart 触发条件与解绑 |
| VM-3 | AC-3.1 ~ AC-3.4 | UI 测试 | onBounce 单/双文本触发点 |
| VM-4 | AC-4.1 ~ AC-4.5 | UI 测试 + 顺序测试 | onFinish 与终态顺序 |
| VM-5 | AC-5.1 ~ AC-5.6 | UI 测试 + 版本测试 | onStop 触发条件与版本 |
| VM-6 | AC-6.1 ~ AC-6.5 | 多范式测试 + 兼容测试 | MarqueeModifier 与 attributeModifier |
| VM-7 | AC-7.1 ~ AC-7.8 | 静态/Cangjie/NDK 测试 | 多范式入口差异与缺口 |

## API 变更分析

### 新增 API

| API 名称 | 开放范围 | 入参概要 | 返回值 | 错误码范围 | 功能描述 | 关联 AC |
|----------|----------|----------|--------|----------|----------|---------|
| `.marqueeUpdateStrategy(value)` (动态, @since 12) | Public | MarqueeUpdateStrategy | MarqueeAttribute | 无 | 滚动策略 | AC-1.1 |
| `.onStart(event)` (动态, @since 8) | Public | () => void | MarqueeAttribute | 无 | 开始回调 | AC-2.1 |
| `.onBounce(event)` (动态, @since 8) | Public | () => void | MarqueeAttribute | 无 | 到达终点回调 | AC-3.1 |
| `.onFinish(event)` (动态, @since 8) | Public | () => void | MarqueeAttribute | 无 | 完成回调 | AC-4.1 |
| `.onStop(event)` (动态, @since 26) | Public | Callback<void>\|undefined | MarqueeAttribute | 无 | 停止回调 | AC-5.1 |
| `MarqueeModifier` (动态, @since 12) | Public | AttributeModifier | — | 无 | 动态 Modifier | AC-6.1 |
| `.attributeModifier(modifier)` (静态, @since 23) | Public | AttributeModifier<MarqueeAttribute>\|<CommonMethod> | MarqueeAttribute | 无 | 属性修饰器 | AC-6.3 |
| `setMarqueeOptions(options)` (静态, @since 26.1) | InnerApi | Ark_MarqueeOptions | this | 无 | 整体构造（unpublished） | AC-7.1 |
| `FfiOHOSAceFrameworkMarqueeCreate(...)` (Cangjie FFI) | InnerApi | start/src/step/loop/fromStart | handle | 无 | Cangjie 创建 | AC-7.4 |

### 变更/废弃 API

| API 名称 | 变更类型 | 影响场景 | 迁移指引 | 关联 AC |
|----------|----------|----------|----------|---------|
| onStop | 新增 (@since 26) | 旧版本无 onStop | 需 API 26+ | AC-5.6 |
| setMarqueeOptions | 新增 (@since 26.1, unpublished) | 静态整体构造 | spacing/delay 未 apply，需单独 setter | AC-7.2 |

> API 签名、d.ts 位置见 design.md。SDK 声明 `api/@internal/component/ets/marquee.d.ts:280-353`（动态）、`api/arkui/component/marquee.static.d.ets`（静态）、`api/arkui/MarqueeModifier.d.ts`（Modifier）。

## 接口规格

### 接口定义

**marqueeUpdateStrategy / onStart / onBounce / onFinish / onStop**

| 属性 | 值 |
|------|-----|
| 函数签名 | `marqueeUpdateStrategy(value: MarqueeUpdateStrategy): MarqueeAttribute` 等 5 个 |
| 返回值 | `MarqueeAttribute` — 属性链 |
| 开放范围 | Public |
| 错误码 | N/A |
| 关联 AC | AC-1.1 ~ AC-5.6 |

**参数约束**

| 参数 | 类型 | 必填 | 默认值 | 约束条件 |
|------|------|------|--------|---------|
| marqueeUpdateStrategy | MarqueeUpdateStrategy | 否 | DEFAULT | DEFAULT=重启；PRESERVE_POSITION=保留（需 spacing/delay） |
| onStart | (() => void)\|undefined | 否 | 无 | undefined 解绑 |
| onBounce | (() => void)\|undefined | 否 | 无 | loop!=1 多次触发 |
| onFinish | (() => void)\|undefined | 否 | 无 | 有限 loop 完成触发 |
| onStop | (Callback<void>)\|undefined | 否 | 无 | @since 26；需 hasStart_ 且 offset==0 |

**行为场景**

| # | 触发条件 | 预期行为 | 关联 AC |
|---|----------|----------|---------|
| 1 | 策略 DEFAULT + 属性变更 | 从头重启 | AC-1.1 |
| 2 | 策略 PRESERVE_POSITION + spacing/delay + 无参数变更 | 保留位置续播 | AC-1.2 |
| 3 | start=true 且文本超出 | onStart | AC-2.1 |
| 4 | 终态 | onStop→onFinish | AC-4.4 |
| 5 | 停止 + hasStart_ + offset==0 | onStop | AC-5.1 |

## 兼容性声明

- **已有 API 行为变更:** 是。onStop 为 API 26 新增，旧版本无此回调；setMarqueeOptions (@since 26.1) 解析 spacing/delay 但未 apply（已知缺口）；Cangjie FFI 缺 onStop/spacing/delay/direction setter；无公开 NDK C-API（仅 Text 的 ArkUI_TextMarqueeOptions）。
- **配置文件格式变更:** 否
- **数据存储格式变更:** 否
- **最低支持版本:** onStart/onBounce/onFinish API 8；marqueeUpdateStrategy/MarqueeModifier API 12；attributeModifier 静态 API 23；onStop/setMarqueeOptions API 26/26.1
- **API 版本号策略:** 全量 @since 标注。终态顺序 onStop→onFinish 为既有行为不变更。

## 架构约束

| 关键约束 | 约束说明 | 影响 AC |
|----------|----------|---------|
| PRESERVE_POSITION 生效条件 | 需 spacing/delay 设置且无动画参数变更 | AC-1.2, AC-1.3 |
| onStop 触发双条件 | hasStart_=true 且 GetTextOffset()==0 | AC-5.1, AC-5.4 |
| 终态顺序 | onStop 先于 onFinish | AC-4.4 |
| 多范式缺口 | Cangjie 缺 onStop/spacing/delay；静态 setMarqueeOptions 缺 spacing/delay apply；无公开 NDK | AC-7.2, AC-7.5, AC-7.6, AC-7.7 |

## 非功能性需求

| 类型 | 指标/阈值 | 验证方式 | 证据 |
|------|----------|----------|------|
| 可靠性 | 帧率动态场景支持 MarqueeDynamicSyncScene 帧率范围 | 帧率测试 | marquee_pattern.h:124-127 |
| 可测试性 | DumpInfo 暴露 play status/loop/step | Dump 测试 | marquee_pattern.cpp:730-748 |

## 多设备适配声明

| 设备类型 | 行为差异 | 规格/约束 | 验证方式 | 证据 |
|----------|----------|----------|----------|------|
| 手机 | 全部事件与策略支持 | — | UI 测试 | — |
| 卡片 | loop 强制 1，onFinish 触发；onBounce 单次 | IsFormRenderExceptDynamicComponent | 卡片测试 | marquee_pattern.cpp:191-193 |

## 全局特性影响

| 特性 | 适用？ | 结论 | 关联场景 |
|------|--------|------|----------|
| 无障碍 | 否 | 仅暴露文本内容，不暴露滚动/事件状态 | marquee_accessibility_property.cpp |
| 大字体 | 否 | 无事件相关差异 | — |
| 深色模式 | 否 | 无事件相关差异 | — |
| 多窗口/分屏 | 是 | OnWindowHide→Pause；OnWindowShow→Resume 影响播放状态 | marquee_pattern.cpp:86-100 |
| 多用户 | 否 | 无差异 | — |
| 版本升级 | 是 | onStop 需 API 26；setMarqueeOptions 需 API 26.1 | SDK 声明 |
| 生态兼容 | 是 | Cangjie FFI 子集；无公开 NDK | cj_marquee_ffi.h |

## Spec 自审清单

- [x] 无"待定""TBD""TODO"等占位符
- [x] 所有 AC 使用 WHEN/THEN 格式，可独立测试
- [x] 范围边界明确（做什么/不做什么清晰）
- [x] 无语义模糊表述
- [x] AC 与规则表交叉一致
- [x] 规则表每条通过 5 项质量检查

## context-references

```yaml
context-queries:
  - repo: "openharmony/arkui_ace_engine"
    query: "Marquee onStop 为何需要 hasStart_ 且 GetTextOffset()==0 双条件，PRESERVE_POSITION 下 offset 非 0 不触发"
  - repo: "openharmony/arkui_ace_engine"
    query: "Marquee setMarqueeOptions 静态 API 为何解析 spacing/delay 但未 apply"
  - repo: "openharmony/arkui_ace_engine"
    query: "Marquee Cangjie FFI 为何绕过 CJUIMarqueeModifier 直调 ModelNG，缺 onStop/spacing/delay"
```

**关键文档：** design.md（`specs/05-ui-components/09-text-components/01-marquee/design.md`）；SDK 声明 `api/@internal/component/ets/marquee.d.ts:280-353`、`api/arkui/component/marquee.static.d.ets`、`api/arkui/MarqueeModifier.d.ts`
