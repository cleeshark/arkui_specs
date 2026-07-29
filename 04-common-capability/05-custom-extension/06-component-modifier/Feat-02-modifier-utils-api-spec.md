# 特性规格

> Func-04-05-06-Feat-02 ModifierUtils 对外接口：固化命令式 Modifier 工具类的对外接口行为——applyAndMergeModifier（属性合并）、applySetOnChange/putDirtyModifier（变更标记与重应用）、isInstanceOf（实例判定，@since 26.0.0 dynamiconly）。
>
> 注：ModifierWithKey 装配机制（stageValue/applyPeer/ModifierMap）、原生 setter 落地链（SetXxxImpl→ModelStatic）属框架内部实现，不在本规格固化，方案见 design.md。

## 概述

| 属性 | 值 |
|------|-----|
| 特性名称 | ModifierUtils 对外接口 (ModifierUtils Public API) |
| 特性编号 | Func-04-05-06-Feat-02 |
| 所属 Epic | 无（已有能力补录） |
| 优先级 | P0 |
| 目标版本 | applyAndMergeModifier/applySetOnChange/putDirtyModifier 随命令式类 @since 12 dynamic；ModifierUtils.isInstanceOf @since 26.0.0 dynamiconly |
| SIG 归属 | ArkUI SIG |
| 状态 | Baselined |
| 复杂度 | 标准 |

## 本次变更范围（Delta）

> 历史规格补齐，补录已有实现的完整行为规格。仅固化 ModifierUtils 对外接口；内部装配机制（ModifierWithKey/applyPeer/落地链）见 design.md。

## 输入文档

| 文档 | 路径 | 状态 |
|------|------|------|
| Design | `specs/04-common-capability/05-custom-extension/06-component-modifier/design.md` | Baselined |

---

## 用户故事

### US-1: applyAndMergeModifier 属性合并

**作为** 命令式 Modifier 使用者，
**我想要** 通过 `ModifierUtils.applyAndMergeModifier` 把 Modifier 的属性合并应用到目标组件实例，
**以便** 命令式属性落到目标节点。

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-1.1 | WHEN 调用 `applyAndMergeModifier(instance, modifier)` THEN 将 modifier 的属性合并应用到 instance | 正常 |
| AC-1.2 | WHEN 属性值为 undefined THEN 合并时对该属性触发移除/重置语义 | 边界 |

### US-2: applySetOnChange 与 putDirtyModifier 变更重应用

**作为** 命令式 Modifier 使用者，
**我想要** `applySetOnChange` 标记 Modifier 已变更、`putDirtyModifier` 触发属性重应用，
**以便** 属性变更时自动重应用，无需手动重设。

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-2.1 | WHEN 调用 `applySetOnChange(modifier)` THEN 标记该 modifier 已变更 | 正常 |
| AC-2.2 | WHEN 调用 `putDirtyModifier(...)` THEN 触发属性重应用 | 正常 |
| AC-2.3 | WHEN 属性发生变更 THEN 经 applySetOnChange 标记后，下次属性应用时自动重应用 | 恢复 |

### US-3: ModifierUtils.isInstanceOf 实例判定

**作为** 应用开发者，
**我想要** 通过 `ModifierUtils.isInstanceOf` 判定对象是否为某组件的命令式 Modifier，
**以便** 运行时按组件类型分流处理。

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-3.1 | WHEN 调用 `isInstanceOf(instance, componentName)` THEN 返回 boolean 表示是否为该组件的命令式 Modifier | 正常 |
| AC-3.2 | WHEN API < 26.0.0 THEN SDK 类型未声明 isInstanceOf（@since 26.0.0 dynamiconly），开发者无法调用；无运行时 API 版本门控（纯类型级约束） | 边界 |
| AC-3.3 | WHEN 静态范式 THEN ModifierUtils/isInstanceOf 静态 SDK 类型未声明（dynamiconly），开发者无法调用 | 边界 |

## 验收追溯

| AC | 关联规则 | 关联 Task | 验证方式 | 证据 |
|----|----------|-----------|----------|------|
| AC-1.1~1.2 | R-1~R-2 | 已有实现 | 单测 | `modifier_utilities.ts` |
| AC-2.1~2.3 | R-3~R-5 | 已有实现 | 单测 | `modifier_utilities.ts`, `common_modifier.ts` |
| AC-3.1~3.3 | R-6~R-8 | 已有实现 | XTS/契约 | `ModifierUtils.d.ts` |

## 规则定义

> **统一规则表，取消 FR/BR/EX/RC 四分类。** 类型标签：**行为**、**边界**、**异常**、**恢复**。

| 规则ID | 类型 | 触发条件 | 预期行为 | 边界/约束 | 关联AC |
|--------|------|----------|----------|-----------|--------|
| R-1 | 行为 | `applyAndMergeModifier(instance, modifier)` | 将 modifier 属性合并应用到 instance | 内部装配机制见 design | AC-1.1 |
| R-2 | 边界 | 属性值为 undefined | 合并时触发移除/重置语义 | — | AC-1.2 |
| R-3 | 行为 | `applySetOnChange(modifier)` | 标记 modifier 已变更 | — | AC-2.1 |
| R-4 | 行为 | `putDirtyModifier(...)` | 触发属性重应用 | — | AC-2.2 |
| R-5 | 恢复 | 属性变更 | 经 applySetOnChange 标记后下次属性应用自动重应用 | — | AC-2.3 |
| R-6 | 行为 | `isInstanceOf(instance, componentName)` | 返回 boolean 判定是否该组件命令式 Modifier | @since 26.0.0 dynamiconly | AC-3.1 |
| R-7 | 边界 | API < 26.0.0 | SDK 类型未声明 isInstanceOf，开发者无法调用 | 类型级约束，非运行时门控 | AC-3.2 |
| R-8 | 边界 | 静态范式 | ModifierUtils/isInstanceOf 静态 SDK 类型未声明（dynamiconly） | 类型级约束 | AC-3.3 |

## 验证映射

| 编号 | 对应规格项 | 验证方式 | 验证重点 |
|------|------------|----------|----------|
| VM-1 | R-1~R-2, AC-1.1~1.2 | 单测 | applyAndMergeModifier 合并、undefined 语义 |
| VM-2 | R-3~R-5, AC-2.1~2.3 | 单测 | applySetOnChange/putDirtyModifier 重应用 |
| VM-3 | R-6~R-8, AC-3.1~3.3 | XTS/契约 | isInstanceOf 版本与范式门控 |

---

## API 变更分析

> 补录已有 API，非新增。

### 新增 API

| API 名称 | 开放范围 | 入参概要 | 返回值 | 错误码范围 | 功能描述 | 关联 AC |
|----------|----------|----------|--------|-----------|----------|---------|
| `class ModifierUtils` (动态 @since 26.0.0 dynamiconly) | Public | — | — | 无 | 命令式 Modifier 工具类 | AC-2.1~2.2, AC-3.1 |
| `static isInstanceOf<T extends CommonMethod<T>>(instance: T, componentName: string): boolean` (动态 @since 26.0.0 dynamiconly) | Public | instance: T, componentName: string | boolean | 无 | 判定实例是否为某组件命令式 Modifier | AC-3.1~3.3 |

> 注：`applyAndMergeModifier`/`applySetOnChange`/`putDirtyModifier` 为 ModifierUtils 内部对外方法（随命令式类 @since 12 dynamic），非独立 SDK 声明，行为见规则定义。

### 变更/废弃 API

无。ModifierUtils/isInstanceOf 为 API 26.0.0 后增（dynamiconly）。

> **d.ts 交叉验证：** ModifierUtils 见 `ModifierUtils.d.ts`，@since 26.0.0 dynamiconly。

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
| 关联 AC | AC-3.1~3.3 |

**参数约束**

| 参数 | 类型 | 必填 | 默认值 | 约束条件 |
|------|------|------|--------|---------|
| instance | T (extends CommonMethod<T>) | 是 | 无 | 组件实例 |
| componentName | string | 是 | 无 | 组件名 |

**行为场景**

| # | 触发条件 | 预期行为 | 关联 AC |
|---|----------|----------|---------|
| 1 | isInstanceOf 匹配 | 返回 true | AC-3.1 |
| 2 | API < 26.0.0 | SDK 类型未声明 isInstanceOf，开发者无法调用（无运行时 API 门控） | AC-3.2 |
| 3 | 静态范式 | 静态 SDK 类型未声明（dynamiconly） | AC-3.3 |

**applyAndMergeModifier / applySetOnChange / putDirtyModifier**

| 属性 | 值 |
|------|-----|
| 函数签名 | `applyAndMergeModifier<T,M,C>(instance, modifier): void`; `applySetOnChange(modifier): void`; `putDirtyModifier(...): void` |
| 返回值 | void |
| 开放范围 | Public（随命令式类 @since 12 dynamic，非独立 SDK 声明） |
| 错误码 | 无 |
| 关联 AC | AC-1.1~1.2, AC-2.1~2.3 |

**行为场景**

| # | 触发条件 | 预期行为 | 关联 AC |
|---|----------|----------|---------|
| 1 | applyAndMergeModifier | 合并属性到 instance | AC-1.1 |
| 2 | 属性 undefined | 触发移除/重置 | AC-1.2 |
| 3 | applySetOnChange | 标记变更 | AC-2.1 |
| 4 | putDirtyModifier | 触发重应用 | AC-2.2 |

---

## 兼容性声明

- **已有 API 行为变更:** 否。applyAndMergeModifier/applySetOnChange/putDirtyModifier 随命令式类自 12 起稳定；ModifierUtils.isInstanceOf 为 26.0.0 后增。
- **配置文件格式变更:** 否
- **数据存储格式变更:** 否
- **最低支持版本:** applyAndMergeModifier/applySetOnChange/putDirtyModifier 动态 @since 12；ModifierUtils.isInstanceOf 动态 @since 26.0.0 dynamiconly
- **API 版本号策略:** ModifierUtils/isInstanceOf @since 26.0.0 dynamiconly（静态 SDK 类型未声明，仅动态可用）

## 架构约束

| 关键约束 | 约束说明 | 影响 AC |
|----------|----------|---------|
| applyAndMergeModifier 合并语义 | 属性合并到目标实例 | AC-1.1 |
| applySetOnChange 重应用驱动 | 变更标记驱动重应用 | AC-2.1~2.3 |
| isInstanceOf dynamiconly | 仅动态 26.0.0 | AC-3.2~3.3 |

## 非功能性需求

| 类型 | 指标/阈值 | 验证方式 | 证据 |
|------|----------|----------|------|
| 性能 | 合并/重应用同步，无额外帧 | 单测 | modifier_utilities.ts |
| 可测试性 | applyAndMergeModifier/isInstanceOf 可单测 | 单测 | modifier_utilities.ts |

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
| 版本升级 | 是 | ModifierUtils/isInstanceOf @since 26.0.0 dynamiconly | AC-3.2~3.3 |
| 生态兼容 | 是 | dynamiconly 限制：静态 SDK 类型未声明 | AC-3.3 |

## Spec 自审清单

- [x] 无"待定""TBD""TODO"等占位符
- [x] 所有 AC 使用 WHEN/THEN 格式，可独立测试
- [x] 范围边界明确（仅 ModifierUtils 对外接口；内部装配机制见 design.md、类体系见 Feat-01、AttributeModifier 通路见 04-05-02）
- [x] 无语义模糊表述
- [x] AC 与规则表交叉一致
- [x] 规则表每条通过 5 项质量检查

## context-references

```yaml
context-queries:
  - repo: "openharmony/arkui_ace_engine"
    query: "modifier_utilities applyAndMergeModifier applySetOnChange putDirtyModifier 对外接口行为"
  - repo: "openharmony/interface/sdk-js"
    query: "ModifierUtils isInstanceOf @since 26.0.0 dynamiconly"
```

**关键文档：** design.md（DESIGN-Func-04-05-06，含 ModifierWithKey 装配机制与落地链方案），SDK `ModifierUtils.d.ts`
