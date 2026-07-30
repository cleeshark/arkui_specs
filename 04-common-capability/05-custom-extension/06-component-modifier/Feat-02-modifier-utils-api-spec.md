# 特性规格

> Func-04-05-06-Feat-02 ModifierUtils.isInstanceOf：固化 SDK 公开 API `ModifierUtils.isInstanceOf`（实例判定，@since 26.0.0 dynamiconly）的行为规格。
>
> 注：`applyAndMergeModifier`/`applySetOnChange`/`putDirtyModifier` 为框架内部方法（非 SDK 声明的 public API），不在本规格固化，方案见 design.md。ModifierWithKey 装配机制与原生 setter 落地链同属内部实现，方案见 design.md。

## 概述

| 属性 | 值 |
|------|-----|
| 特性名称 | ModifierUtils.isInstanceOf 实例判定 (ModifierUtils.isInstanceOf) |
| 特性编号 | Func-04-05-06-Feat-02 |
| 所属 Epic | 无（已有能力补录） |
| 优先级 | P1 |
| 目标版本 | ModifierUtils.isInstanceOf 动态 @since 26.0.0 dynamiconly |
| SIG 归属 | ArkUI SIG |
| 状态 | Baselined |
| 复杂度 | 简单（L1） |

## 本次变更范围（Delta）

> 历史规格补齐，补录已有 SDK public API 的行为规格。

## 输入文档

| 文档 | 路径 | 状态 |
|------|------|------|
| Design | `specs/04-common-capability/05-custom-extension/06-component-modifier/design.md` | Baselined |
| SDK 声明 | `interface/sdk-js/api/arkui/ModifierUtils.d.ts` | — |

---

## 用户故事

### US-1: ModifierUtils.isInstanceOf 实例判定

**作为** 应用开发者，
**我想要** 通过 `ModifierUtils.isInstanceOf` 判定对象是否为某组件的命令式 Modifier，
**以便** 运行时按组件类型分流处理。

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-1.1 | WHEN 调用 `ModifierUtils.isInstanceOf<T>(instance, componentName)` THEN 返回 boolean 表示是否为该组件的命令式 Modifier | 正常 |
| AC-1.2 | WHEN API < 26.0.0 THEN SDK 类型未声明 isInstanceOf（@since 26.0.0 dynamiconly），开发者无法调用；无运行时 API 版本门控（纯类型级约束） | 边界 |
| AC-1.3 | WHEN 静态范式 THEN ModifierUtils/isInstanceOf 静态 SDK 类型未声明（dynamiconly），开发者无法调用 | 边界 |

## 验收追溯

| AC | 关联规则 | 关联 Task | 验证方式 | 证据 |
|----|----------|-----------|----------|------|
| AC-1.1~1.3 | R-1~R-3 | 已有实现 | XTS/契约 | `ModifierUtils.d.ts` |

## 规则定义

> **统一规则表，取消 FR/BR/EX/RC 四分类。** 类型标签：**行为**、**边界**、**异常**、**恢复**。

| 规则ID | 类型 | 触发条件 | 预期行为 | 边界/约束 | 关联AC |
|--------|------|----------|----------|-----------|--------|
| R-1 | 行为 | `isInstanceOf(instance, componentName)` | 返回 boolean 判定是否该组件命令式 Modifier | @since 26.0.0 dynamiconly | AC-1.1 |
| R-2 | 边界 | API < 26.0.0 | SDK 类型未声明 isInstanceOf，开发者无法调用 | 类型级约束，非运行时门控 | AC-1.2 |
| R-3 | 边界 | 静态范式 | ModifierUtils/isInstanceOf 静态 SDK 类型未声明（dynamiconly） | 类型级约束 | AC-1.3 |

## 验证映射

| 编号 | 对应规格项 | 验证方式 | 验证重点 |
|------|------------|----------|----------|
| VM-1 | R-1~R-3, AC-1.1~1.3 | XTS/契约 | isInstanceOf 版本与范式门控 |

---

## API 变更分析

> 补录已有 API，非新增。

### 新增 API

| API 名称 | 开放范围 | 入参概要 | 返回值 | 错误码范围 | 功能描述 | 关联 AC |
|----------|----------|----------|--------|-----------|----------|---------|
| `class ModifierUtils` (动态 @since 26.0.0 dynamiconly) | Public | — | — | 无 | 命令式 Modifier 工具类 | AC-1.1 |
| `static isInstanceOf<T extends CommonMethod<T>>(instance: T, componentName: string): boolean` (动态 @since 26.0.0 dynamiconly) | Public | instance: T, componentName: string | boolean | 无 | 判定实例是否为某组件命令式 Modifier | AC-1.1~1.3 |

### 变更/废弃 API

无。ModifierUtils/isInstanceOf 为 API 26.0.0 后增（dynamiconly）。

> **d.ts 交叉验证：** ModifierUtils 见 `interface/sdk-js/api/arkui/ModifierUtils.d.ts`，仅声明 `isInstanceOf`，@since 26.0.0 dynamiconly。

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
| 关联 AC | AC-1.1~1.3 |

**参数约束**

| 参数 | 类型 | 必填 | 默认值 | 约束条件 |
|------|------|------|--------|---------|
| instance | T (extends CommonMethod<T>) | 是 | 无 | 组件实例 |
| componentName | string | 是 | 无 | 组件名 |

**行为场景**

| # | 触发条件 | 预期行为 | 关联 AC |
|---|----------|----------|---------|
| 1 | isInstanceOf 匹配 | 返回 true | AC-1.1 |
| 2 | API < 26.0.0 | SDK 类型未声明 isInstanceOf，开发者无法调用（无运行时 API 门控） | AC-1.2 |
| 3 | 静态范式 | 静态 SDK 类型未声明（dynamiconly） | AC-1.3 |

---

## 兼容性声明

- **已有 API 行为变更:** 否。ModifierUtils.isInstanceOf 为 26.0.0 后增。
- **配置文件格式变更:** 否
- **数据存储格式变更:** 否
- **最低支持版本:** ModifierUtils.isInstanceOf 动态 @since 26.0.0 dynamiconly
- **API 版本号策略:** ModifierUtils/isInstanceOf @since 26.0.0 dynamiconly（静态 SDK 类型未声明，仅动态可用）

## 架构约束

| 关键约束 | 约束说明 | 影响 AC |
|----------|----------|---------|
| isInstanceOf dynamiconly | 仅动态 26.0.0 | AC-1.2~1.3 |

## 非功能性需求

| 类型 | 指标/阈值 | 验证方式 | 证据 |
|------|----------|----------|------|
| 可测试性 | isInstanceOf 可单测（mock instance/componentName） | 单测 | modifier_utilities.ts |

## 多设备适配声明

| 设备类型 | 行为差异 | 规格/约束 | 验证方式 | 证据 |
|----------|----------|----------|----------|------|
| 手机 | 无差异 | — | — | — |
| 平板 | 无差异 | — | — | — |
| 折叠屏 | 无差异 | — | — | — |

## 全局特性影响

| 特性 | 适用？ | 结论 | 关联场景 |
|------|--------|------|----------|
| 版本升级 | 是 | ModifierUtils/isInstanceOf @since 26.0.0 dynamiconly | AC-1.2~1.3 |
| 生态兼容 | 是 | dynamiconly 限制：静态 SDK 类型未声明 | AC-1.3 |

## Spec 自审清单

- [x] 无"待定""TBD""TODO"等占位符
- [x] 所有 AC 使用 WHEN/THEN 格式，可独立测试
- [x] 范围边界明确（仅 SDK public API isInstanceOf；内部方法 applyAndMergeModifier/applySetOnChange/putDirtyModifier 见 design.md）
- [x] 无语义模糊表述
- [x] AC 与规则表交叉一致
- [x] 规则表每条通过 5 项质量检查

## context-references

```yaml
context-queries:
  - repo: "openharmony/interface_sdk-js"
    query: "ModifierUtils.d.ts isInstanceOf @since 26.0.0 dynamiconly public 声明"
  - repo: "openharmony/arkui_ace_engine"
    query: "modifier_utilities.ts ModifierUtils.isInstanceOf 实现（内部方法 applyAndMergeModifier/applySetOnChange/putDirtyModifier 非 SDK public）"
```

**关键文档：** design.md（DESIGN-Func-04-05-06，含 ModifierWithKey 装配机制与内部方法方案），SDK `ModifierUtils.d.ts`
