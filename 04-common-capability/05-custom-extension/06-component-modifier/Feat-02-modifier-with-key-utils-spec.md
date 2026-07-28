# 特性规格

> Func-04-05-06-Feat-02 ModifierWithKey 装配与 ModifierUtils：固化命令式 Modifier 的属性装配模式（ModifierWithKey/ModifierMap + stageValue + applyPeer）、ModifierUtils 合并与变更标记（applyAndMergeModifier/applySetOnChange/putDirtyModifier）、原生 setter 落地链，以及 ModifierUtils.isInstanceOf 实例判定（@since 26.0.0 dynamiconly）的行为规格。

## 概述

| 属性 | 值 |
|------|-----|
| 特性名称 | ModifierWithKey 装配与 ModifierUtils (ModifierWithKey Assembly & ModifierUtils) |
| 特性编号 | Func-04-05-06-Feat-02 |
| 所属 Epic | 无（已有能力补录） |
| 优先级 | P0 |
| 目标版本 | ModifierWithKey/applyAndMergeModifier 随命令式类 @since 12 dynamic；ModifierUtils.isInstanceOf @since 26.0.0 dynamiconly |
| SIG 归属 | ArkUI SIG |
| 状态 | Baselined |
| 复杂度 | 复杂 |

## 本次变更范围（Delta）

> 历史规格补齐，补录已有实现的完整行为规格。

## 输入文档

| 文档 | 路径 | 状态 |
|------|------|------|
| Design | `specs/04-common-capability/05-custom-extension/06-component-modifier/design.md` | Baselined |

---

## 用户故事

### US-1: ModifierWithKey 属性装配

**作为** 应用开发者,
**我想要** 命令式 Modifier 的属性设置经 ModifierWithKey 装配,
**以便** 属性名与值+setter 解耦，支持增量变更重应用。

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-1.1 | WHEN 调用 modifier.backgroundColor(v) THEN 经 ArkComponent 属性方法写入 _modifiersWithKeys（ModifierMap：属性名→ModifierWithKey） | 正常 |
| AC-1.2 | WHEN ModifierWithKey 持有数据 THEN 含 stageValue（暂存值）与 applyPeer（调原生 setter 的回调） | 正常 |
| AC-1.3 | WHEN 同一属性多次设置 THEN 覆盖 stageValue，ModifierMap 键不变 | 边界 |

### US-2: applyAndMergeModifier 合并与 applyPeer 落地

**作为** 框架开发者,
**我想要** applyNormalAttribute 经 ModifierUtils.applyAndMergeModifier 把属性 merge 到目标并逐个 applyPeer 调原生 setter,
**以便** 命令式属性落到目标组件节点。

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-2.1 | WHEN applyNormalAttribute(instance) 调用 THEN ModifierUtils.applyAndMergeModifier<T,M,C>(instance, modifier) 把 modifier._modifiersWithKeys merge 到 instance._modifiersWithKeys | 正常 |
| AC-2.2 | WHEN merge 完成 THEN 逐个 attributeModifierWithKey.applyPeer(arkModifier.nativePtr, isUndefined)（arkModifier.js:144-145）调原生 setter | 正常 |
| AC-2.3 | WHEN applyPeer 调用 THEN 命中 *AttributeModifier::SetXxxImpl(node, value)（button_static_modifier.cpp:156 起）转 FrameNode 后调 ButtonModelStatic::SetXxx | 正常 |
| AC-2.4 | WHEN 属性值为 undefined（isUndefined=true）THEN applyPeer 传 isUndefined 标记，触发移除/重置语义 | 边界 |

### US-3: applySetOnChange 与 putDirtyModifier

**作为** 框架开发者,
**我想要** ModifierUtils.applySetOnChange 标记变更、putDirtyModifier 置 stageValue 后调 applyPeer,
**以便** 支持属性变更时自动重应用。

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-3.1 | WHEN applyNormalAttribute 执行 THEN 先 ModifierUtils.applySetOnChange(this) 标记 modifier 已变更（common_modifier.ts:26） | 正常 |
| AC-3.2 | WHEN putDirtyModifier(arkModifier, attributeModifierWithKey, hostInstanceId) 调用 THEN 置 stageValue 后调 applyPeer（arkModifier.js:92） | 正常 |
| AC-3.3 | WHEN 属性变更 THEN 经 applySetOnChange 标记后下次 applyNormalAttribute 重应用 | 恢复 |

### US-4: ModifierUtils.isInstanceOf 实例判定

**作为** 应用开发者,
**我想要** 通过 ModifierUtils.isInstanceOf 判定对象是否为某组件的命令式 Modifier,
**以便** 运行时类型分流。

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-4.1 | WHEN 调用 ModifierUtils.isInstanceOf<T>(instance, componentName) THEN 返回 boolean 表示是否为该组件的命令式 Modifier（ModifierUtils.d.ts:29） | 正常 |
| AC-4.2 | WHEN API < 26.0.0 THEN isInstanceOf 不可用（@since 26.0.0 dynamiconly），仅动态范式 26.0.0 后可用 | 边界 |
| AC-4.3 | WHEN 静态范式 THEN ModifierUtils/isInstanceOf 不可用（dynamiconly） | 边界 |

## 验收追溯

| AC | 关联规则 | 关联 Task | 验证方式 | 证据 |
|----|----------|-----------|----------|------|
| AC-1.1~1.3 | R-1~R-3 | 已有实现 | 单测 | `modifier_utilities.ts`, ArkComponent 属性方法 |
| AC-2.1~2.4 | R-4~R-7 | 已有实现 | 单测 | `modifier_utilities.ts`, `arkModifier.js:144`, `button_static_modifier.cpp:156` |
| AC-3.1~3.3 | R-8~R-10 | 已有实现 | 单测 | `common_modifier.ts:26`, `arkModifier.js:92` |
| AC-4.1~4.3 | R-11~R-13 | 已有实现 | XTS/契约 | `ModifierUtils.d.ts:29` |

## 规则定义

> **统一规则表，取消 FR/BR/EX/RC 四分类。** 类型标签：**行为**、**边界**、**异常**、**恢复**。

| 规则ID | 类型 | 触发条件 | 预期行为 | 边界/约束 | 关联AC |
|--------|------|----------|----------|-----------|--------|
| R-1 | 行为 | modifier.x(v) 设属性 | 经 ArkComponent 属性方法写 _modifiersWithKeys（ModifierMap） | 属性名→ModifierWithKey | AC-1.1 |
| R-2 | 行为 | ModifierWithKey 持有数据 | 含 stageValue（暂存值）+ applyPeer（原生 setter 回调） | 解耦属性名与值+setter | AC-1.2 |
| R-3 | 边界 | 同属性多次设置 | 覆盖 stageValue，ModifierMap 键不变 | 增量变更 | AC-1.3 |
| R-4 | 行为 | applyNormalAttribute | applyAndMergeModifier merge _modifiersWithKeys 到 instance | — | AC-2.1 |
| R-5 | 行为 | merge 完成 | 逐个 applyPeer(nativePtr, isUndefined) 调原生 setter | — | AC-2.2 |
| R-6 | 行为 | applyPeer | 命中 *AttributeModifier::SetXxxImpl(node, value)→ModelStatic::SetXxx | 每属性一个 SetXxxImpl | AC-2.3 |
| R-7 | 边界 | 属性值 undefined | applyPeer 传 isUndefined=true，触发移除/重置 | — | AC-2.4 |
| R-8 | 行为 | applyNormalAttribute | 先 applySetOnChange(this) 标记变更 | — | AC-3.1 |
| R-9 | 行为 | putDirtyModifier | 置 stageValue 后调 applyPeer | arkModifier.js:92 | AC-3.2 |
| R-10 | 恢复 | 属性变更 | applySetOnChange 标记后下次 applyNormalAttribute 重应用 | 自动重应用 | AC-3.3 |
| R-11 | 行为 | isInstanceOf(instance, componentName) | 返回 boolean 判定是否该组件命令式 Modifier | @since 26.0.0 dynamiconly | AC-4.1 |
| R-12 | 边界 | API < 26.0.0 | isInstanceOf 不可用 | 版本门控 | AC-4.2 |
| R-13 | 边界 | 静态范式 | ModifierUtils/isInstanceOf 不可用（dynamiconly） | 仅动态 | AC-4.3 |

## 验证映射

| 编号 | 对应规格项 | 验证方式 | 验证重点 |
|------|------------|----------|----------|
| VM-1 | R-1~R-3, AC-1.1~1.3 | 单测 | ModifierWithKey 装配与 stageValue |
| VM-2 | R-4~R-7, AC-2.1~2.4 | 单测 | applyAndMergeModifier/applyPeer/原生 setter |
| VM-3 | R-8~R-10, AC-3.1~3.3 | 单测 | applySetOnChange/putDirtyModifier 重应用 |
| VM-4 | R-11~R-13, AC-4.1~4.3 | XTS/契约 | isInstanceOf 版本与范式门控 |
| VM-5 | 全量 | XTS/集成 | 命令式属性端到端落地 |

---

## API 变更分析

> 补录已有 API，非新增。

### 新增 API

| API 名称 | 开放范围 | 入参概要 | 返回值 | 错误码范围 | 功能描述 | 关联 AC |
|----------|----------|----------|--------|-----------|----------|---------|
| `class ModifierUtils` (动态 @since 26.0.0 dynamiconly) | Public | — | — | 无 | 命令式 Modifier 工具类 | AC-3.1~3.2, AC-4.1 |
| `static isInstanceOf<T extends CommonMethod<T>>(instance: T, componentName: string): boolean` (动态 @since 26.0.0 dynamiconly) | Public | instance: T, componentName: string | boolean | 无 | 判定实例是否为某组件命令式 Modifier | AC-4.1~4.3 |

### 变更/废弃 API

无。ModifierUtils/isInstanceOf 为 API 26.0.0 后增（dynamiconly）。

> **d.ts 交叉验证：** ModifierUtils `ModifierUtils.d.ts:29`，@since 26.0.0 dynamiconly。

---

## 接口规格

### 接口定义

**ModifierUtils.isInstanceOf**

| 属性 | 值 |
|------|-----|
| 函数签名 | `static isInstanceOf<T extends CommonMethod<T>>(instance: T, componentName: string): boolean` |
| 返回值 | `boolean` — 是否为该组件命令式 Modifier |
| 开放范围 | Public |
| 错误码 | 无 |
| 关联 AC | AC-4.1~4.3 |

**参数约束**

| 参数 | 类型 | 必填 | 默认值 | 约束条件 |
|------|------|------|--------|---------|
| instance | T (extends CommonMethod<T>) | 是 | 无 | 组件实例 |
| componentName | string | 是 | 无 | 组件名 |

**行为场景**

| # | 触发条件 | 预期行为 | 关联 AC |
|---|----------|----------|---------|
| 1 | applyNormalAttribute | applyAndMergeModifier merge + applyPeer | AC-2.1~2.2 |
| 2 | 属性 undefined | applyPeer isUndefined=true | AC-2.4 |
| 3 | isInstanceOf 匹配 | 返回 true | AC-4.1 |
| 4 | API < 26.0.0 | isInstanceOf 不可用 | AC-4.2 |

---

## 兼容性声明

- **已有 API 行为变更:** 否。ModifierWithKey/applyAndMergeModifier 随命令式类自 12 起稳定；ModifierUtils.isInstanceOf 为 26.0.0 后增。
- **配置文件格式变更:** 否
- **数据存储格式变更:** 否
- **最低支持版本:** ModifierWithKey/applyAndMergeModifier 随命令式类动态 @since 12；ModifierUtils.isInstanceOf 动态 @since 26.0.0 dynamiconly
- **API 版本号策略:** ModifierUtils/isInstanceOf @since 26.0.0 dynamiconly（仅动态，静态不可用）

## 架构约束

| 关键约束 | 约束说明 | 影响 AC |
|----------|----------|---------|
| ModifierWithKey 解耦 | 属性名→值+setter，支持增量 | AC-1.1~1.3 |
| applyPeer 统一调原生 setter | 经 *AttributeModifier::SetXxxImpl | AC-2.2~2.3 |
| applySetOnChange 重应用 | 变更标记驱动重应用 | AC-3.1~3.3 |
| isInstanceOf dynamiconly | 仅动态 26.0.0 | AC-4.2~4.3 |

## 非功能性需求

| 类型 | 指标/阈值 | 验证方式 | 证据 |
|------|----------|----------|------|
| 性能 | merge + applyPeer 同步，无额外帧 | 单测 | modifier_utilities.ts |
| 可靠性 | stageValue 覆盖语义明确，增量变更幂等 | 单测 | AC-1.3 |
| 可测试性 | applyPeer/applyAndMergeModifier 可单测（mock nativePtr） | 单测 | modifier_utilities.ts |

## 多设备适配声明

| 设备类型 | 行为差异 | 规格/约束 | 验证方式 | 证据 |
|----------|----------|----------|----------|------|
| 手机 | 无差异 | — | — | — |
| 平板 | 无差异 | — | — | — |
| 折叠屏 | 无差异 | — | — | — |

## 全局特性影响

| 特性 | 适用？ | 结论 | 关联场景 |
|------|--------|------|----------|
| 无障碍 | 否 | — | — |
| 大字体 | 否 | — | — |
| 深色模式 | 否 | — | — |
| 多窗口/分屏 | 否 | — | — |
| 多用户 | 否 | — | — |
| 版本升级 | 是 | ModifierUtils/isInstanceOf @since 26.0.0 dynamiconly | AC-4.2~4.3 |
| 生态兼容 | 是 | dynamiconly 限制：静态范式不可用 | AC-4.3 |

## Spec 自审清单

- [x] 无"待定""TBD""TODO"等占位符
- [x] 所有 AC 使用 WHEN/THEN 格式，可独立测试
- [x] 范围边界明确（ModifierWithKey 装配/ModifierUtils；类体系见 Feat-01、AttributeModifier 通路见 04-05-02）
- [x] 无语义模糊表述
- [x] AC 与规则表交叉一致
- [x] 规则表每条通过 5 项质量检查

## context-references

```yaml
context-queries:
  - repo: "openharmony/arkui_ace_engine"
    query: "modifier_utilities applyAndMergeModifier applyPeer putDirtyModifier applySetOnChange stageValue"
  - repo: "openharmony/arkui_ace_engine"
    query: "button_static_modifier ButtonAttributeModifier SetXxxImpl 原生 setter"
  - repo: "openharmony/interface/sdk-js"
    query: "ModifierUtils isInstanceOf @since 26.0.0 dynamiconly"
```

**关键文档：** design.md（DESIGN-Func-04-05-06），SDK `ModifierUtils.d.ts:29`、`arkModifier.js:92/144`、`button_static_modifier.cpp:156`
