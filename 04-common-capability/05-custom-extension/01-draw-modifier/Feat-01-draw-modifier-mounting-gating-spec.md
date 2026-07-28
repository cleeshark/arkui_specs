# 特性规格

> Func-04-05-01-Feat-01 DrawModifier 装配与组件门控：固化 `drawModifier()` 属性方法的装配调用链、Pattern opt-out 门控、API 版本分支移除语义，以及实例唯一性契约的行为规格。

## 概述

| 属性 | 值 |
|------|-----|
| 特性名称 | DrawModifier 装配与组件门控 (DrawModifier Mounting & Component Gating) |
| 特性编号 | Func-04-05-01-Feat-01 |
| 所属 Epic | 无（已有能力补录） |
| 优先级 | P0 |
| 目标版本 | 动态 API 12 起（drawModifier 属性方法），API 20 起支持移除语义；静态 API 23 起 |
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

### US-1: 通过 drawModifier() 装配自定义绘制修饰器

**作为** 应用开发者,
**我想要** 通过 `.drawModifier(modifier)` 将 DrawModifier 绑定到组件 FrameNode,
**以便** 在不修改组件 Pattern 的前提下为组件注入自定义绘制回调。

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-1.1 | WHEN 调用 `.drawModifier(modifier: DrawModifier)` 且组件支持 DrawModifier THEN DrawModifier 绑定到当前组件的 FrameNode（经 ExtensionHandler 中转），自定义绘制仅作用于当前组件 FrameNode，不影响其子节点 | 正常 |
| AC-1.2 | WHEN 装配成功 THEN 立即触发一次刷新（AddInvalidateFunc 内调 InvalidateRender + ForegroundRender，或无 ExtensionHandler 时 MarkDirtyNode(PROPERTY_UPDATE_RENDER)） | 正常 |
| AC-1.3 | WHEN 从 modifier 对象读取 drawBehind/drawContent/drawFront/drawForeground/drawOverlay 方法 THEN 各方法名为函数时包装为 DrawModifierFunc，非函数时对应回调为 nullptr（不触发该层绘制） | 正常 |
| AC-1.4 | WHEN 同一 JS DrawModifier 实例被传给多个组件的 `.drawModifier()` THEN 各组件各自新建独立 NG::DrawModifier 并提取其回调，正常工作不报错——SDK 文档 "Each DrawModifier instance can be set for only one component"（common.d.ts:6241）为纯文档限制，无编译期/运行时校验 | 边界 |
| AC-1.5 | WHEN 对同一组件重复调用 `.drawModifier(modifier)` THEN 后调用覆盖前值（FrameNode::SetDrawModifier 每次新建 ExtensionHandler 仅在首次，drawModifier_ 直接赋值覆盖） | 边界 |
| AC-1.6 | WHEN 装配时组件无 ExtensionHandler THEN 首次调用新建 ExtensionHandler 并 AttachFrameNode(this) | 正常 |

### US-2: 组件门控（opt-out 机制）

**作为** 框架开发者,
**我想要** 通过 Pattern::IsSupportDrawModifier 门控排除自定义渲染组件,
**以便** 避免 DrawModifier 破坏 Canvas/Video 等组件的自有渲染管线。

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-2.1 | WHEN 组件 Pattern 未重写 IsSupportDrawModifier THEN 默认返回 true，组件支持 DrawModifier | 正常 |
| AC-2.2 | WHEN 组件为 Canvas/EffectComponent/DistortionComponent/Video/VideoStateMachine/UnionEffectContainer THEN Pattern 重写 IsSupportDrawModifier 返回 false，不支持 DrawModifier | 正常 |
| AC-2.3 | WHEN 不支持 DrawModifier 的组件调用 `.drawModifier(modifier)` THEN JsDrawModifier 静默 return，不创建 DrawModifier、不挂载、无日志、无错误码 | 异常 |
| AC-2.4 | WHEN 旧（非 NG）模型调用 SetDrawModifier THEN view_abstract_model_impl.h 为空实现 `{}`，不生效 | 异常 |

### US-3: API 版本分支与移除语义

**作为** 应用开发者,
**我想要** 在 API≥20 通过传 undefined 移除已装配的 DrawModifier,
**以便** 动态取消自定义绘制。

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-3.1 | WHEN API≥20 且入参非对象（含 undefined）THEN 执行移除路径：SetDrawModifier(nullptr) + 触发刷新（InvalidateRender + ForegroundRender 或 MarkDirtyNode(PROPERTY_UPDATE_RENDER)） | 正常 |
| AC-3.2 | WHEN API<20 且入参非对象 THEN JsDrawModifier 直接 return，不执行任何操作（旧版本不支持移除） | 异常 |
| AC-3.3 | WHEN API≥20 移除时组件已无 ExtensionHandler THEN 走 MarkDirtyNode(PROPERTY_UPDATE_RENDER) 兜底刷新 | 边界 |

### US-4: invalidate() 挂载（装配侧机制）

**作为** 应用开发者,
**我想要** 装配后在 modifier 对象上获得 invalidate() 方法,
**以便** 主动触发重绘（刷新消费行为见 Feat-03）。

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-4.1 | WHEN 装配成功 THEN 在 JS drawModifier 对象上设置 `invalidate` 函数属性（持有 FrameNode 弱引用 NativeWeakRef） | 正常 |
| AC-4.2 | WHEN invalidate 函数被调用且 FrameNode 弱引用有效 THEN 取 ExtensionHandler 调 InvalidateRender + ForegroundRender；无 ExtensionHandler 则 MarkDirtyNode(PROPERTY_UPDATE_RENDER) | 正常 |
| AC-4.3 | WHEN FrameNode 弱引用已失效（组件销毁）THEN invalidate 调用返回 undefined，无副作用 | 异常 |

## 验收追溯

| AC | 关联规则 | 关联 Task | 验证方式 | 证据 |
|----|----------|-----------|----------|------|
| AC-1.1~1.6 | R-1~R-4, R-7 | 已有实现 | 单测/XTS | `frameworks/core/components_ng/base/frame_node.cpp:958`, `frameworks/bridge/declarative_frontend/jsview/js_view_abstract.cpp:10582` |
| AC-2.1~2.4 | R-5, R-6, R-8 | 已有实现 | 单测 | `frameworks/core/components_ng/pattern/pattern.h:119`, 6 个 opt-out Pattern |
| AC-3.1~3.3 | R-9~R-11 | 已有实现 | 单测 | `js_view_abstract.cpp:10584`, `:10593` |
| AC-4.1~4.3 | R-12~R-14 | 已有实现 | 单测 | `js_view_abstract.cpp:10536` |

## 规则定义

> **统一规则表，取消 FR/BR/EX/RC 四分类。** 类型标签：**行为**（正常路径下的系统行为）、**边界**（输入/状态的临界点）、**异常**（非法输入或异常状态的处理）、**恢复**（系统异常后的恢复策略）。

| 规则ID | 类型 | 触发条件 | 预期行为 | 边界/约束 | 关联AC |
|--------|------|----------|----------|-----------|--------|
| R-1 | 行为 | 调用 `.drawModifier(modifier)` 且 IsSupportDrawModifier=true 且入参为对象 | 经 JsDrawModifier→ViewAbstractModel::SetDrawModifier→ViewAbstract::SetDrawModifier→FrameNode::SetDrawModifier 链路挂载；自定义绘制仅作用于当前组件 FrameNode，不影响子节点 | modifier 非 null 对象 | AC-1.1 |
| R-2 | 行为 | 装配成功 | 立即触发一次刷新：AddInvalidateFunc 内若有 ExtensionHandler 调 InvalidateRender()+ForegroundRender()，否则 MarkDirtyNode(PROPERTY_UPDATE_RENDER) | — | AC-1.2 |
| R-3 | 行为 | 从 modifier 对象读取 5 个方法名 | getDrawModifierFunc/getDrawOverlayModifierFunc 对每个 key 检查 IsFunction，是则包装为 DrawModifierFunc 赋值到对应 *Func，否则 nullptr | key 为 "drawBehind"/"drawContent"/"drawFront"/"drawForeground"/"drawOverlay" | AC-1.3 |
| R-4 | 行为 | FrameNode::SetDrawModifier 时无 extensionHandler_ | MakeRefPtr<ExtensionHandler>() + AttachFrameNode(this)，再 SetDrawModifier(drawModifier) | extensionHandler_ 为 null 时才新建 | AC-1.6 |
| R-5 | 边界 | 对同一组件重复调用 drawModifier | ExtensionHandler 仅首次新建，drawModifier_ 直接赋值覆盖前值；每次新建 NG::DrawModifier 对象 | 不累积多个 DrawModifier | AC-1.5 |
| R-6 | 边界 | SDK 文档声明实例唯一性，但代码无校验 | 文档 "Each DrawModifier instance can be set for only one component"（common.d.ts:6241）；JsDrawModifier 每次调用新建 NG::DrawModifier（js_view_abstract.cpp:10607）从 JS 对象提取回调，ExtensionHandler::SetDrawModifier 仅赋值（extension_handler.h:108）——同一 JS DrawModifier 对象可复用于多组件，无报错。唯一性为纯文档限制，无编译期/运行时强制 | AC-1.4 |
| R-7 | 行为 | DrawModifier 不接管 measure/layout | frame_node.cpp:6189 仅当 extensionHandler_ && !HasDrawModifier() 时注入 InnerMeasure；有 DrawModifier 时走原生 measure | DrawModifier 只接管 draw | AC-1.1 |
| R-8 | 行为 | Pattern::IsSupportDrawModifier 默认实现 | 返回 true（pattern.h:119-122），opt-out 模式 | 默认支持 | AC-2.1 |
| R-9 | 异常 | API<20 且入参非对象 | JsDrawModifier 直接 return（:10584-10586），不创建、不挂载、不刷新 | 旧版本不支持移除 | AC-3.2 |
| R-10 | 异常 | API≥20 且入参非对象（含 undefined） | SetDrawModifier(nullptr) + 触发刷新后 return（:10593-10605） | 入参非 object 即触发移除 | AC-3.1 |
| R-11 | 恢复 | API≥20 移除时组件无 ExtensionHandler | 走 MarkDirtyNode(PROPERTY_UPDATE_RENDER) 兜底（:10601） | 无 handler 兜底 | AC-3.3 |
| R-12 | 行为 | 装配成功 | AddInvalidateFunc 在 JS drawModifier 对象上设置 invalidate 函数属性，持有 FrameNode 的 NativeWeakRef 弱引用 | 弱引用，组件销毁后失效 | AC-4.1 |
| R-13 | 行为 | invalidate() 调用且弱引用有效 | 取 ExtensionHandler 调 InvalidateRender()+ForegroundRender()；无则 MarkDirtyNode(PROPERTY_UPDATE_RENDER) | — | AC-4.2 |
| R-14 | 异常 | invalidate() 调用但弱引用失效（Invalid()） | 返回 undefined，无副作用 | 组件已销毁 | AC-4.3 |
| R-15 | 异常 | 不支持 DrawModifier 的组件调用 drawModifier | JsDrawModifier 取 IsSupportDrawModifier=false 后 return（:10590-10592），静默无操作、无日志、无错误码 | 6 个 opt-out 组件 | AC-2.3 |

## 验证映射

| 编号 | 对应规格项 | 验证方式 | 验证重点 |
|------|------------|----------|----------|
| VM-1 | R-1, R-4, AC-1.1, AC-1.6 | 单测 | 装配链路完整，ExtensionHandler 首次新建 |
| VM-2 | R-2, AC-1.2 | 单测 | 装配后立即触发刷新 |
| VM-3 | R-3, AC-1.3 | 单测 | 5 回调读取，非函数返回 nullptr |
| VM-4 | R-5, AC-1.5 | 单测 | 重复设置覆盖前值 |
| VM-5 | R-8, R-15, AC-2.1~2.3 | 单测/XTS | 默认支持 + 6 个 opt-out 组件静默拒绝 |
| VM-6 | R-9, R-10, R-11, AC-3.1~3.3 | 单测 | API 版本分支移除语义 |
| VM-7 | R-12~R-14, AC-4.1~4.3 | 单测 | invalidate 挂载与弱引用失效处理 |
| VM-8 | R-6, AC-1.4 | XTS/契约 | 实例唯一性契约（源码未强制，验证契约文档） |

---

## API 变更分析

> 补录已有 API，非新增。

### 新增 API

| API 名称 | 开放范围 | 入参概要 | 返回值 | 错误码范围 | 功能描述 | 关联 AC |
|----------|----------|----------|--------|-----------|----------|---------|
| `drawModifier(modifier: DrawModifier \| undefined): T` (动态 @since 12) / `default drawModifier(modifier: DrawModifier \| undefined): this` (静态 @since 23) | Public | modifier: DrawModifier 实例或 undefined | T/this（链式） | 无 | 将 DrawModifier 绑定到当前组件 FrameNode；仅作用于当前组件不波及子节点 | AC-1.1, AC-1.5, AC-3.1, AC-3.2 |

### 变更/废弃 API

无变更或废弃。

> **d.ts 交叉验证：** 签名与 `@internal/component/ets/common.d.ts:19562`（动态）、`arkui/component/common.static.d.ets:11479`（静态）一致。文档注释明确 "A custom modifier applies only to the FrameNode of the currently bound component, not to its subnodes."（common.d.ts:19554）。

---

## 接口规格

### 接口定义

**drawModifier**

| 属性 | 值 |
|------|-----|
| 函数签名 | `drawModifier(modifier: DrawModifier \| undefined): T`（动态）/ `default drawModifier(modifier: DrawModifier \| undefined): this`（静态） |
| 返回值 | `T` / `this` — 返回当前组件类型实例，支持链式调用 |
| 开放范围 | Public |
| 错误码 | 无（不支持组件静默无操作） |
| 关联 AC | AC-1.1, AC-3.1, AC-3.2 |

**参数约束**

| 参数 | 类型 | 必填 | 默认值 | 约束条件 |
|------|------|------|--------|---------|
| modifier | DrawModifier \| undefined | 否 | undefined | DrawModifier 实例：触发装配/覆盖；undefined 或非对象：API≥20 触发移除，API<20 静默忽略 |

**行为场景**

| # | 触发条件 | 预期行为 | 关联 AC |
|---|----------|----------|---------|
| 1 | 组件支持 + modifier 为 DrawModifier 对象 | 经装配链挂载，立即触发刷新 | AC-1.1, AC-1.2 |
| 2 | 组件支持 + modifier 为 undefined（API≥20） | SetDrawModifier(nullptr) + 刷新 | AC-3.1 |
| 3 | 组件支持 + modifier 为非对象（API<20） | 静默 return | AC-3.2 |
| 4 | 组件不支持（opt-out） | 静默 return，无操作无日志 | AC-2.3 |
| 5 | 同组件重复调用 | 覆盖前值 | AC-1.5 |

---

## 兼容性声明

- **已有 API 行为变更:** 否。drawModifier() 自动态 API 12、静态 API 23 起稳定。API 20 引入移除语义（非对象入参执行移除而非忽略），属既有版本演进，非本次变更。
- **配置文件格式变更:** 否
- **数据存储格式变更:** 否
- **最低支持版本:** 动态 API 12，静态 API 23
- **API 版本号策略:** drawModifier 属性方法动态 `@since 12 dynamic`、静态 `@since 23 static`；移除语义以 API 20 为分界（Container::GreatOrEqualAPITargetVersion(VERSION_TWENTY)）

## 架构约束

| 关键约束 | 约束说明 | 影响 AC |
|----------|----------|---------|
| 装配链单向自顶向下 | JS Bridge→Model→ViewAbstract→FrameNode→ExtensionHandler，不回调上层 | AC-1.1 |
| 门控 opt-out | 默认 true，6 个自定义渲染组件重写 false；不支持时静默拒绝 | AC-2.1~2.3 |
| DrawModifier 不接管 measure | 有 DrawModifier 时跳过 InnerMeasure 注入，只接管 draw | AC-1.1 |
| 实例唯一性为契约层 | 源码不强制，靠 SDK 契约约束 | AC-1.4 |

## 非功能性需求

| 类型 | 指标/阈值 | 验证方式 | 证据 |
|------|----------|----------|------|
| 性能 | 装配为同步赋值，无额外帧开销 | 单测 | frame_node.cpp:958 |
| 内存 | 每 DrawModifier 实例 + ExtensionHandler（仅首次） | 单测 | extension_handler.h:156 |
| 可测试性 | IsSupportDrawModifier 门控可单测覆盖 | 单测 | pattern.h:119 |
| 自动化维测 | 不支持组件静默拒绝无日志——维测时需主动检查 opt-out 列表 | 代码评审 | 6 个 opt-out Pattern |

## 多设备适配声明

| 设备类型 | 行为差异 | 规格/约束 | 验证方式 | 证据 |
|----------|----------|----------|----------|------|
| 手机 | 无差异 | — | — | — |
| 平板 | 无差异 | — | — | — |
| 折叠屏 | 无差异 | — | — | — |

## 全局特性影响

| 特性 | 适用？ | 结论 | 关联场景 |
|------|--------|------|----------|
| 无障碍 | 否 | DrawModifier 为绘制层，不影响无障碍语义 | — |
| 大字体 | 否 | DrawModifier 不改变布局尺寸 | — |
| 深色模式 | 否 | 回调内绘制内容由开发者决定，框架不干预 | — |
| 多窗口/分屏 | 否 | 装配链与窗口无关 | — |
| 多用户 | 否 | — | — |
| 版本升级 | 是 | API 20 移除语义分界；静态 API 23 引入、26.0.0 补齐 drawForeground | AC-3.1, AC-3.2 |
| 生态兼容 | 是 | DrawContext/DrawModifier 跨平台标注 @crossplatform | — |

## Spec 自审清单

- [x] 无"待定""TBD""TODO"等占位符
- [x] 所有 AC 使用 WHEN/THEN 格式，可独立测试
- [x] 范围边界明确（装配/门控/移除语义/invalidate 挂载；绘制分发见 Feat-02、刷新消费见 Feat-03）
- [x] 无语义模糊表述
- [x] AC 与规则表交叉一致（每个 AC 至少关联一条规则，每条规则至少关联一个 AC）
- [x] 规则表每条通过 5 项质量检查（可复现/可观测/边界值/关联AC/无冲突）

## context-references

```yaml
context-queries:
  - repo: "openharmony/arkui_ace_engine"
    query: "DrawModifier 装配链 ExtensionHandler 创建与 Pattern IsSupportDrawModifier 门控"
  - repo: "openharmony/interface/sdk-js"
    query: "drawModifier 属性方法与 DrawModifier 类 @since 版本标注"
```

**关键文档：** design.md（DESIGN-Func-04-05-01），SDK `@internal/component/ets/common.d.ts:6249/19562`
