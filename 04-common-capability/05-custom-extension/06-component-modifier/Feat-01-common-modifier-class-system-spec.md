# 特性规格

> Func-04-05-06-Feat-01 命令式 Modifier 基类与类体系：固化 `CommonModifier` 基类（extends ArkComponent implements AttributeModifier）、60+ 具体组件 Modifier 类（ButtonModifier/TextModifier/…）、`@ohos.arkui.modifier` barrel 导出、静态生成式 *Modifier.ets，以及 applyNormalAttribute 转发 ModifierUtils 的行为规格。

## 概述

| 属性 | 值 |
|------|-----|
| 特性名称 | 命令式 Modifier 基类与类体系 (Command-style Modifier Base & Class System) |
| 特性编号 | Func-04-05-06-Feat-01 |
| 所属 Epic | 无（已有能力补录） |
| 优先级 | P0 |
| 目标版本 | CommonModifier/XxxModifier 动态 @since 12（crossplatform @since 20）、静态 @since 23 |
| SIG 归属 | ArkUI SIG |
| 状态 | Baselined |
| 复杂度 | 标准 |

## 本次变更范围（Delta）

> 历史规格补齐，补录已有实现的完整行为规格。

## 输入文档

| 文档 | 路径 | 状态 |
|------|------|------|
| Design | `specs/04-common-capability/05-custom-extension/06-component-modifier/design.md` | Baselined |

---

## 用户故事

### US-1: CommonModifier 命令式基类

**作为** 应用开发者,
**我想要** 使用 CommonModifier 作为通用命令式属性设置对象,
**以便** 封装一组通用属性并可传给 .attributeModifier() 复用。

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-1.1 | WHEN 实例化 CommonModifier THEN 继承 ArkComponent（持有 nativePtr 组件代理）并实现 AttributeModifier<CommonAttribute>（common_modifier.ts:16） | 正常 |
| AC-1.2 | WHEN 构造 CommonModifier(nativePtr, classType) THEN classType 默认 ModifierType.EXPOSE_MODIFIER，调 super(nativePtr, classType)（:18-23） | 正常 |
| AC-1.3 | WHEN applyNormalAttribute(instance) 调用 THEN 转发 ModifierUtils.applySetOnChange(this) + applyAndMergeModifier(instance, this)（:25-28） | 正常 |
| AC-1.4 | WHEN SDK 声明 THEN CommonModifier.d.ts:44 `extends CommonAttribute implements AttributeModifier<CommonAttribute>`，@since 12 dynamic（crossplatform @since 20），唯一成员 applyNormalAttribute?（:56） | 正常 |

### US-2: 具体组件命令式 Modifier 类

**作为** 应用开发者,
**我想要** 使用 ButtonModifier/TextModifier 等组件专属命令式 Modifier,
**以便** 设置该组件的专属属性。

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-2.1 | WHEN 使用 ButtonModifier THEN `extends LazyArkButtonComponent implements AttributeModifier<ButtonAttribute>`（button_modifier.ts:148），可设该组件专属属性 | 正常 |
| AC-2.2 | WHEN 查看类数量 THEN 60+ 具体组件 Modifier 类（ark_modifier/src/*_modifier.ts），每组件一个 | 正常 |
| AC-2.3 | WHEN 导入 THEN 经 @ohos.arkui.modifier.d.ts barrel 统一 re-export（CommonModifier + 60+ XxxModifier + ModifierUtils） | 正常 |

### US-3: 静态范式命令式类

**作为** 应用开发者,
**我想要** 静态范式也有对应命令式 Modifier 类,
**以便** 静态可分析地使用命令式属性设置。

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-3.1 | WHEN 静态范式 THEN ButtonModifier.ets:31 `extends CommonMethodModifier implements ButtonAttribute, AttributeModifier<ButtonAttribute>` | 正常 |
| AC-3.2 | WHEN 静态 applyNormalAttribute/Pressed/.../Selected THEN 生成式为空实现（ButtonModifier.ets:39-43），真正落属性靠 applyModifierPatch0（:58/65） | 边界 |
| AC-3.3 | WHEN 静态基类 CommonMethodModifier.ets:9340 的 attributeModifier(value) THEN 占位 throw Not implemented，真实挂接由 hooks/peer | 异常 |

### US-4: 与 AttributeModifier 通路边界

**作为** 框架开发者,
**我想要** 明确命令式类与 AttributeModifier 通路的关系,
**以便** 正确定界。

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-4.1 | WHEN 命令式类经 .attributeModifier(modifier) 装配 THEN 装配与 apply* 状态分发属 04-05-02，本域仅覆盖命令式类自身 | 边界 |
| AC-4.2 | WHEN 命令式类设属性（如 modifier.backgroundColor(v)）THEN 经 ArkComponent 属性方法写入 _modifiersWithKeys（ModifierWithKey 装配属 Feat-02） | 边界 |

## 验收追溯

| AC | 关联规则 | 关联 Task | 验证方式 | 证据 |
|----|----------|-----------|----------|------|
| AC-1.1~1.4 | R-1~R-4 | 已有实现 | 单测/XTS | `common_modifier.ts:16-28`, `CommonModifier.d.ts:44/56` |
| AC-2.1~2.3 | R-5~R-7 | 已有实现 | XTS | `button_modifier.ts:148`, `@ohos.arkui.modifier.d.ts` |
| AC-3.1~3.3 | R-8~R-10 | 已有实现 | 单测 | `ButtonModifier.ets:31/39-43/65`, `CommonMethodModifier.ets:9340` |
| AC-4.1~4.2 | R-11~R-12 | 已有实现 | 代码评审 | 边界定界 |

## 规则定义

> **统一规则表，取消 FR/BR/EX/RC 四分类。** 类型标签：**行为**、**边界**、**异常**、**恢复**。

| 规则ID | 类型 | 触发条件 | 预期行为 | 边界/约束 | 关联AC |
|--------|------|----------|----------|-----------|--------|
| R-1 | 行为 | 实例化 CommonModifier | extends ArkComponent（持有 nativePtr）implements AttributeModifier<CommonAttribute> | 既是组件代理又是 AttributeModifier | AC-1.1 |
| R-2 | 行为 | 构造 CommonModifier(nativePtr, classType) | classType 默认 EXPOSE_MODIFIER，调 super | — | AC-1.2 |
| R-3 | 行为 | applyNormalAttribute(instance) | 转发 ModifierUtils.applySetOnChange + applyAndMergeModifier | 属性应用经 Feat-02 | AC-1.3 |
| R-4 | 行为 | SDK 声明 | CommonModifier extends CommonAttribute implements AttributeModifier<CommonAttribute>，@since 12（crossplatform 20） | 唯一成员 applyNormalAttribute? | AC-1.4 |
| R-5 | 行为 | 使用 ButtonModifier | extends 组件 Ark 基类 implements AttributeModifier<对应Attribute> | 可设组件专属属性 | AC-2.1 |
| R-6 | 行为 | 类数量 | 60+ 具体组件 Modifier 类，每组件一个 | 随组件增减 | AC-2.2 |
| R-7 | 行为 | 导入 | @ohos.arkui.modifier.d.ts barrel re-export CommonModifier + 60+ XxxModifier + ModifierUtils | 统一入口 | AC-2.3 |
| R-8 | 行为 | 静态范式 | *Modifier.ets extends CommonMethodModifier implements 对应Attribute | — | AC-3.1 |
| R-9 | 边界 | 静态 apply* | 生成式空实现，落属性靠 applyModifierPatch0 flagArray | 与动态不同 | AC-3.2 |
| R-10 | 异常 | 静态基类 attributeModifier | 占位 throw Not implemented，真实挂接由 hooks/peer | 不在基类 | AC-3.3 |
| R-11 | 边界 | 与 AttributeModifier 通路 | .attributeModifier 装配 + apply* 分发属 04-05-02 | 本域仅覆盖类自身 | AC-4.1 |
| R-12 | 边界 | 命令式类设属性 | 经 ArkComponent 属性方法写入 _modifiersWithKeys | ModifierWithKey 属 Feat-02 | AC-4.2 |

## 验证映射

| 编号 | 对应规格项 | 验证方式 | 验证重点 |
|------|------------|----------|----------|
| VM-1 | R-1~R-4, AC-1.1~1.4 | 单测/XTS | CommonModifier 继承与 applyNormalAttribute 转发 |
| VM-2 | R-5~R-7, AC-2.1~2.3 | XTS | 60+ XxxModifier 与 barrel |
| VM-3 | R-8~R-10, AC-3.1~3.3 | 单测 | 静态生成式类与 flagArray |
| VM-4 | R-11~R-12, AC-4.1~4.2 | 代码评审 | 与 AttributeModifier 通路定界 |
| VM-5 | 全量 | XTS/集成 | 命令式 Modifier 端到端属性设置 |

---

## API 变更分析

> 补录已有 API，非新增。

### 新增 API

| API 名称 | 开放范围 | 入参概要 | 返回值 | 错误码范围 | 功能描述 | 关联 AC |
|----------|----------|----------|--------|-----------|----------|---------|
| `class CommonModifier extends CommonAttribute implements AttributeModifier<CommonAttribute>` (动态 @since 12, crossplatform @since 20 / 静态 @since 23) | Public | — | — | 无 | 通用命令式 Modifier 基类 | AC-1.1~1.4 |
| `applyNormalAttribute?(instance: CommonAttribute): void` (动态 @since 12) | Public | instance: CommonAttribute | void | 无 | 默认态属性更新，转发 ModifierUtils | AC-1.3 |
| `class ButtonModifier`/`TextModifier`/... (60+, 动态 @since 12) | Public | — | — | 无 | 组件专属命令式 Modifier | AC-2.1~2.3 |

### 变更/废弃 API

无。

> **d.ts 交叉验证：** CommonModifier `CommonModifier.d.ts:44/56`；60+ XxxModifier 与 ModifierUtils 经 `@ohos.arkui.modifier.d.ts` barrel。

---

## 接口规格

### 接口定义

**CommonModifier**

| 属性 | 值 |
|------|-----|
| 函数签名 | `class CommonModifier extends CommonAttribute implements AttributeModifier<CommonAttribute>` |
| 返回值 | —（类） |
| 开放范围 | Public |
| 错误码 | 无 |
| 关联 AC | AC-1.1~1.4 |

**参数约束**

| 参数 | 类型 | 必填 | 默认值 | 约束条件 |
|------|------|------|--------|---------|
| nativePtr | KNode | 是 | 无 | 组件节点原生句柄 |
| classType | ModifierType | 否 | EXPOSE_MODIFIER | Modifier 类型 |

**行为场景**

| # | 触发条件 | 预期行为 | 关联 AC |
|---|----------|----------|---------|
| 1 | 实例化 | 继承 ArkComponent + 实现 AttributeModifier | AC-1.1 |
| 2 | applyNormalAttribute | 转发 ModifierUtils | AC-1.3 |
| 3 | 静态基类 attributeModifier | throw Not implemented | AC-3.3 |

---

## 兼容性声明

- **已有 API 行为变更:** 否。CommonModifier/XxxModifier 自动态 12/静态 23 起稳定；crossplatform @since 20 为既有演进。
- **配置文件格式变更:** 否
- **数据存储格式变更:** 否
- **最低支持版本:** 动态 @since 12（crossplatform @since 20），静态 @since 23
- **API 版本号策略:** CommonModifier 动态 @since 12 / crossplatform @since 20 dynamic、静态 @since 23；60+ XxxModifier 动态 @since 12

## 架构约束

| 关键约束 | 约束说明 | 影响 AC |
|----------|----------|---------|
| 继承 ArkComponent | 命令式类是组件代理 + AttributeModifier | AC-1.1 |
| applyNormalAttribute 转发 | 经 ModifierUtils 合并属性 | AC-1.3 |
| 静态 flagArray 模式 | 与动态 ModifierWithKey 不同 | AC-3.2 |
| 通路定界 | 装配/分发属 04-05-02 | AC-4.1 |

## 非功能性需求

| 类型 | 指标/阈值 | 验证方式 | 证据 |
|------|----------|----------|------|
| 性能 | 命令式类持有 nativePtr，属性设置直写 ModifierMap | 单测 | common_modifier.ts:16 |
| 可测试性 | 命令式类可单测（mock nativePtr） | 单测 | button_modifier.ts:148 |

## 多设备适配声明

| 设备类型 | 行为差异 | 规格/约束 | 验证方式 | 证据 |
|----------|----------|----------|----------|------|
| 手机 | 无差异 | — | — | — |
| 平板 | 无差异 | — | — | — |
| 折叠屏 | 无差异 | — | — | — |

## 全局特性影响

| 特性 | 适用？ | 结论 | 关联场景 |
|------|--------|------|----------|
| 无障碍 | 否 | 命令式属性不影响无障碍语义 | — |
| 大字体 | 否 | — | — |
| 深色模式 | 否 | — | — |
| 多窗口/分屏 | 否 | — | — |
| 多用户 | 否 | — | — |
| 版本升级 | 是 | crossplatform @since 20 | AC-1.4 |
| 生态兼容 | 是 | crossplatform @since 20 | — |

## Spec 自审清单

- [x] 无"待定""TBD""TODO"等占位符
- [x] 所有 AC 使用 WHEN/THEN 格式，可独立测试
- [x] 范围边界明确（类体系；ModifierWithKey 装配见 Feat-02、AttributeModifier 通路见 04-05-02）
- [x] 无语义模糊表述
- [x] AC 与规则表交叉一致
- [x] 规则表每条通过 5 项质量检查

## context-references

```yaml
context-queries:
  - repo: "openharmony/arkui_ace_engine"
    query: "common_modifier.ts CommonModifier extends ArkComponent implements AttributeModifier applyNormalAttribute"
  - repo: "openharmony/arkui_ace_engine"
    query: "ark_modifier *_modifier.ts ButtonModifier 60+ 组件 Modifier 类 @ohos.arkui.modifier barrel"
  - repo: "openharmony/interface/sdk-js"
    query: "CommonModifier class @ohos.arkui.modifier barrel ModifierUtils"
```

**关键文档：** design.md（DESIGN-Func-04-05-06），SDK `CommonModifier.d.ts:44/56`、`@ohos.arkui.modifier.d.ts`
