# 特性规格

> Func-04-05-01-Feat-03 主动刷新机制：固化 `invalidate()` 触发刷新、InvalidateRender/OverlayRender/ForegroundRender 置位机制、NeedRender API 版本门控、needRerender 帧消费，以及 JS 与 C-API 刷新路径差异的行为规格。

## 概述

| 属性 | 值 |
|------|-----|
| 特性名称 | 主动刷新机制 (Active Invalidate & Refresh) |
| 特性编号 | Func-04-05-01-Feat-03 |
| 所属 Epic | 无（已有能力补录） |
| 优先级 | P0 |
| 目标版本 | invalidate 动态 @since 12、静态 @since 23；NeedRender/needRerender 版本门控以 API 20 为分界 |
| SIG 归属 | ArkUI SIG |
| 状态 | Baselined |
| 复杂度 | 标准 |

## 本次变更范围（Delta）

> 历史规格补齐，补录已有实现的完整行为规格。

## 输入文档

| 文档 | 路径 | 状态 |
|------|------|------|
| Design | `specs/04-common-capability/05-custom-extension/01-draw-modifier/design.md` | Baselined |

---

## 用户故事

### US-1: invalidate() 主动触发刷新

**作为** 应用开发者,
**我想要** 调用 `modifier.invalidate()` 主动触发组件重绘,
**以便** 在自定义绘制状态变化后刷新显示。

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-1.1 | WHEN invalidate() 调用且 FrameNode 弱引用有效且有 ExtensionHandler THEN 调用 InvalidateRender() + ForegroundRender()（js_view_abstract.cpp:10556-10557） | 正常 |
| AC-1.2 | WHEN invalidate() 调用且无 ExtensionHandler THEN 走 MarkDirtyNode(PROPERTY_UPDATE_RENDER) 兜底（:10559） | 边界 |
| AC-1.3 | WHEN invalidate() 调用但 FrameNode 弱引用失效（Invalid()）THEN 返回 undefined，无副作用（:10548-10550） | 异常 |
| AC-1.4 | WHEN drawModifier() 装配成功 THEN AddInvalidateFunc 立即触发一次刷新（InvalidateRender+ForegroundRender 或 MarkDirtyNode）（:10566-10573） | 正常 |

### US-2: InvalidateRender 置位机制

**作为** 框架开发者,
**我想要** InvalidateRender/OverlayRender/ForegroundRender 三段对称置位 needRender_,
**以便** 标记对应绘制段需重画。

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-2.1 | WHEN InvalidateRender() 调用 THEN 有 invalidateRender_ 回调则调用，否则 node_->MarkNeedRenderOnly()（extension_handler.cpp:151-157） | 正常 |
| AC-2.2 | WHEN InvalidateRender/OverlayRender/ForegroundRender 调用 THEN 统一置 needRender_=true（:158, :168, :178） | 正常 |
| AC-2.3 | WHEN OverlayRender() 调用 THEN 有 overlayRender_ 回调则调用，否则 MarkNeedRenderOnly，置 needRender_=true（:161-168） | 正常 |
| AC-2.4 | WHEN ForegroundRender() 调用 THEN 有 foreGroundRender_ 回调则调用，否则 MarkNeedRenderOnly，置 needRender_=true（:171-178） | 正常 |
| AC-2.5 | WHEN Draw/ForegroundDraw/OverlayDraw 入口执行 THEN 各自复位 needRender_=false（:54, :60, :66），表示本段已消费刷新标志 | 恢复 |

### US-3: NeedRender API 版本门控

**作为** 框架开发者,
**我想要** NeedRender() 按 API 版本区分判定逻辑,
**以便** 平衡可见性保证与性能优化。

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-3.1 | WHEN API≥20 THEN NeedRender() 返回 needRender_（extension_handler.cpp:183-184） | 正常 |
| AC-3.2 | WHEN API<20 THEN NeedRender() 返回 drawModifier_ || needRender_（:186），即挂载 DrawModifier 即视为需重画 | 正常 |

### US-4: needRerender 帧消费

**作为** 框架开发者,
**我想要** 帧调度按 NeedRender/HasDrawModifier 判定是否强制重画,
**以便** invalidate 触发的刷新在下一帧实际执行。

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-4.1 | WHEN API≥20 且 extensionHandler_ 存在 THEN needRerender 累加 (NeedRender() || (HasDrawModifier() && !skippedMeasure))（frame_node.cpp:6527-6528） | 正常 |
| AC-4.2 | WHEN API<20 且 extensionHandler_ 存在 THEN needRerender 累加 NeedRender()（:6530） | 正常 |
| AC-4.3 | WHEN needRerender 为 true 或 PaintProperty 有变更 THEN MarkDirtyNode(true, true, PROPERTY_UPDATE_RENDER)（:6532-6533） | 正常 |
| AC-4.4 | WHEN API≥20 且 skippedMeasure=true 且无 DrawModifier THEN 不强制重画（HasDrawModifier()=false 且 skippedMeasure 跳过） | 边界 |

### US-5: C-API 刷新路径差异

**作为** NDK/ANI 开发者,
**我想要** 了解 C-API 刷新路径与 JS 路径的差异,
**以便** 正确预期 C-API invalidate 的刷新范围。

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-5.1 | WHEN Arkoala C-API InvalidateImpl 调用 THEN 仅调 InvalidateRender()（draw_modifier_accessor.cpp:50），不调 ForegroundRender | 正常 |
| AC-5.2 | WHEN ANI C-API Invalidate 调用 THEN 仅调 InvalidateRender()（common_ani_modifier.cpp:1389-1399），不调 ForegroundRender | 正常 |
| AC-5.3 | WHEN 对比 JS 路径 THEN JS 调 InvalidateRender+ForegroundRender，C-API 仅 InvalidateRender——路径行为不一致，标注为风险 | 边界 |

## 验收追溯

| AC | 关联规则 | 关联 Task | 验证方式 | 证据 |
|----|----------|-----------|----------|------|
| AC-1.1~1.4 | R-1~R-4 | 已有实现 | 单测 | `js_view_abstract.cpp:10536-10573` |
| AC-2.1~2.5 | R-5~R-9 | 已有实现 | 单测 | `extension_handler.cpp:48-179` |
| AC-3.1~3.2 | R-10, R-11 | 已有实现 | 单测 | `extension_handler.cpp:181-187` |
| AC-4.1~4.4 | R-12~R-15 | 已有实现 | 单测 | `frame_node.cpp:6521-6534` |
| AC-5.1~5.3 | R-16~R-18 | 已有实现 | 单测/代码评审 | `draw_modifier_accessor.cpp:50`, `common_ani_modifier.cpp:1389` |

## 规则定义

> **统一规则表，取消 FR/BR/EX/RC 四分类。** 类型标签：**行为**（正常路径下的系统行为）、**边界**（输入/状态的临界点）、**异常**（非法输入或异常状态的处理）、**恢复**（系统异常后的恢复策略）。

| 规则ID | 类型 | 触发条件 | 预期行为 | 边界/约束 | 关联AC |
|--------|------|----------|----------|-----------|--------|
| R-1 | 行为 | invalidate() + 弱引用有效 + 有 ExtensionHandler | 调 InvalidateRender() + ForegroundRender() | JS 路径同时刷两段 | AC-1.1 |
| R-2 | 边界 | invalidate() + 无 ExtensionHandler | MarkDirtyNode(PROPERTY_UPDATE_RENDER) 兜底 | 无 handler 兜底 | AC-1.2 |
| R-3 | 异常 | invalidate() + 弱引用失效（Invalid()） | 返回 undefined，无副作用 | 组件已销毁 | AC-1.3 |
| R-4 | 行为 | drawModifier() 装配成功 | AddInvalidateFunc 立即触发一次刷新 | 首次装配即重画 | AC-1.4 |
| R-5 | 行为 | InvalidateRender() | 有 invalidateRender_ 回调则调用，否则 node_->MarkNeedRenderOnly() | 刷新回调可被外部注入 | AC-2.1 |
| R-6 | 行为 | InvalidateRender/OverlayRender/ForegroundRender | 统一置 needRender_=true | 三段对称 | AC-2.2 |
| R-7 | 行为 | OverlayRender() | 有 overlayRender_ 回调则调用，否则 MarkNeedRenderOnly，置 needRender_=true | overlay 段对称 | AC-2.3 |
| R-8 | 行为 | ForegroundRender() | 有 foreGroundRender_ 回调则调用，否则 MarkNeedRenderOnly，置 needRender_=true | foreground 段对称 | AC-2.4 |
| R-9 | 恢复 | Draw/ForegroundDraw/OverlayDraw 入口 | 各自复位 needRender_=false 后调 On* | 表示本段已消费刷新 | AC-2.5 |
| R-10 | 行为 | NeedRender() + API≥20 | 返回 needRender_ | GreatOrEqualTargetAPIVersion(VERSION_TWENTY) | AC-3.1 |
| R-11 | 行为 | NeedRender() + API<20 | 返回 drawModifier_ || needRender_ | 挂载即需重画 | AC-3.2 |
| R-12 | 行为 | 帧调度 + API≥20 + extensionHandler_ 存在 | needRerender 累加 (NeedRender() || (HasDrawModifier() && !skippedMeasure)) | skippedMeasure 优化 | AC-4.1 |
| R-13 | 行为 | 帧调度 + API<20 + extensionHandler_ 存在 | needRerender 累加 NeedRender() | 无 skippedMeasure 判定 | AC-4.2 |
| R-14 | 行为 | needRerender=true 或 PaintProperty 有变更 | MarkDirtyNode(true, true, PROPERTY_UPDATE_RENDER) | 触发重绘 | AC-4.3 |
| R-15 | 边界 | API≥20 + skippedMeasure=true + 无 DrawModifier | 不强制重画（HasDrawModifier()=false 跳过） | 仅 measure 跳过且有 DrawModifier 才强制 | AC-4.4 |
| R-16 | 行为 | Arkoala InvalidateImpl | 仅调 InvalidateRender()，不调 ForegroundRender | C-API 仅 content 段刷新 | AC-5.1 |
| R-17 | 行为 | ANI Invalidate | 仅调 InvalidateRender()，不调 ForegroundRender | C-API 仅 content 段刷新 | AC-5.2 |
| R-18 | 边界 | JS vs C-API 刷新路径 | JS 调 InvalidateRender+ForegroundRender，C-API 仅 InvalidateRender；路径行为不一致 | 见 design.md 风险 R-3 | AC-5.3 |

## 验证映射

| 编号 | 对应规格项 | 验证方式 | 验证重点 |
|------|------------|----------|----------|
| VM-1 | R-1~R-4, AC-1.1~1.4 | 单测 | invalidate JS 路径与装配即刷新 |
| VM-2 | R-5~R-9, AC-2.1~2.5 | 单测 | 三段置位与 Draw 入口复位 |
| VM-3 | R-10, R-11, AC-3.1~3.2 | 单测 | NeedRender API 20 门控 |
| VM-4 | R-12~R-15, AC-4.1~4.4 | 单测 | needRerender 帧消费与 skippedMeasure |
| VM-5 | R-16~R-18, AC-5.1~5.3 | 单测/代码评审 | C-API 与 JS 路径差异 |
| VM-6 | 全量 | XTS/集成 | invalidate 触发下一帧重绘端到端 |

---

## API 变更分析

> 补录已有 API，非新增。

### 新增 API

| API 名称 | 开放范围 | 入参概要 | 返回值 | 错误码范围 | 功能描述 | 关联 AC |
|----------|----------|----------|--------|-----------|----------|---------|
| `invalidate(): void` (动态 @since 12 / 静态 @since 23) | Public | 无 | void | 无 | 使组件失效，触发重渲染；不可重载 | AC-1.1~1.4 |

### 变更/废弃 API

无变更或废弃。

> **d.ts 交叉验证：** invalidate 签名与 `@internal/component/ets/common.d.ts:6328`、`arkui/component/common.static.d.ets:2817` 一致。文档注释 "Invalidate the component, which will cause a re-render of the component. No overloading is allowed or needed."

---

## 接口规格

### 接口定义

**invalidate**

| 属性 | 值 |
|------|-----|
| 函数签名 | `invalidate(): void` |
| 返回值 | `void` |
| 开放范围 | Public |
| 错误码 | 无 |
| 关联 AC | AC-1.1~1.4 |

**参数约束**

| 参数 | 类型 | 必填 | 默认值 | 约束条件 |
|------|------|------|--------|---------|
| 无 | — | — | — | 不可重载/不可继承覆盖（SDK 注释 "No overloading is allowed or needed"） |

**行为场景**

| # | 触发条件 | 预期行为 | 关联 AC |
|---|----------|----------|---------|
| 1 | JS 路径 + 有 ExtensionHandler | InvalidateRender + ForegroundRender，置 needRender_=true | AC-1.1 |
| 2 | JS 路径 + 无 ExtensionHandler | MarkDirtyNode(PROPERTY_UPDATE_RENDER) | AC-1.2 |
| 3 | 组件已销毁 | 返回 undefined | AC-1.3 |
| 4 | 装配时 | 立即触发一次刷新 | AC-1.4 |
| 5 | C-API（Arkoala/ANI） | 仅 InvalidateRender | AC-5.1, AC-5.2 |

---

## 兼容性声明

- **已有 API 行为变更:** 否。invalidate() 自动态 API 12、静态 API 23 起稳定。NeedRender/needRerender 的 API 20 门控为既有版本演进。
- **配置文件格式变更:** 否
- **数据存储格式变更:** 否
- **最低支持版本:** invalidate 动态 API 12、静态 API 23
- **API 版本号策略:** invalidate 动态 `@since 12 dynamic`、静态 `@since 23 static`；NeedRender/needRerender 内部以 `GreatOrEqualTargetAPIVersion(VERSION_TWENTY)` 为分界

## 架构约束

| 关键约束 | 约束说明 | 影响 AC |
|----------|----------|---------|
| 三段对称置位 | InvalidateRender/OverlayRender/ForegroundRender 结构一致 | AC-2.1~2.4 |
| Draw 入口复位 | Draw/ForegroundDraw/OverlayDraw 复位 needRender_=false | AC-2.5 |
| API 20 门控 | NeedRender 与 needRerender 均以 API 20 分界 | AC-3.1~3.2, AC-4.1~4.2 |
| skippedMeasure 优化 | API≥20 仅 measure 跳过且有 DrawModifier 才强制重画 | AC-4.4 |
| JS/C-API 路径差异 | JS 刷两段，C-API 仅 content 段 | AC-5.3 |

## 非功能性需求

| 类型 | 指标/阈值 | 验证方式 | 证据 |
|------|----------|----------|------|
| 性能 | invalidate 为标志位置位，无同步重绘开销；实际重绘延迟到下一帧 | 单测 | extension_handler.cpp:158 |
| 可靠性 | 置位幂等，多次调用等价一次 | 单测 | needRender_=true 赋值 |
| 可测试性 | API 版本门控可单测覆盖 | 单测 | extension_handler.cpp:183 |
| 自动化维测 | JS/C-API 路径差异需代码评审识别 | 代码评审 | draw_modifier_accessor.cpp:50 |

## 多设备适配声明

| 设备类型 | 行为差异 | 规格/约束 | 验证方式 | 证据 |
|----------|----------|----------|----------|------|
| 手机 | 无差异 | — | — | — |
| 平板 | 无差异 | — | — | — |
| 折叠屏 | 无差异 | 刷新机制与设备无关 | — | — |

## 全局特性影响

| 特性 | 适用？ | 结论 | 关联场景 |
|------|--------|------|----------|
| 无障碍 | 否 | 刷新为绘制层，不影响无障碍 | — |
| 大字体 | 否 | — | — |
| 深色模式 | 否 | — | — |
| 多窗口/分屏 | 否 | 帧调度与窗口无关 | — |
| 多用户 | 否 | — | — |
| 版本升级 | 是 | NeedRender/needRerender 以 API 20 为门控分界 | AC-3.1~3.2, AC-4.1~4.2 |
| 生态兼容 | 是 | invalidate @crossplatform | — |

## Spec 自审清单

- [x] 无"待定""TBD""TODO"等占位符
- [x] 所有 AC 使用 WHEN/THEN 格式，可独立测试
- [x] 范围边界明确（invalidate 触发/置位机制/版本门控/帧消费/C-API 差异；装配见 Feat-01、绘制分发见 Feat-02）
- [x] 无语义模糊表述
- [x] AC 与规则表交叉一致
- [x] 规则表每条通过 5 项质量检查

## context-references

```yaml
context-queries:
  - repo: "openharmony/arkui_ace_engine"
    query: "ExtensionHandler InvalidateRender/NeedRender 与 frame_node needRerender 帧消费"
  - repo: "openharmony/arkui_ace_engine"
    query: "draw_modifier_accessor 与 common_ani_modifier Invalidate C-API 路径"
  - repo: "openharmony/interface/sdk-js"
    query: "DrawModifier invalidate @since 与 No overloading 文档"
```

**关键文档：** design.md（DESIGN-Func-04-05-01），SDK `common.d.ts:6328`、`common.static.d.ets:2817`
