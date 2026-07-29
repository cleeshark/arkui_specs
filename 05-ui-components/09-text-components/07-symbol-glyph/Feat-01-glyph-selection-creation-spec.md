# 特性规格

## 概述

| 属性 | 值 |
|------|-----|
| 特性名称 | SymbolGlyph 字形选择与创建 |
| 特性编号 | Func-05-09-07-Feat-01 |
| 所属 Epic | 无 |
| 优先级 | P1 |
| 目标版本 | API 11/12 |
| SIG 归属 | ArkUI SIG |
| 状态 | Baselined |
| 复杂度 | 简单 |

## 本次变更范围（Delta）
全新特性补录（lineage: new），无 Delta。

## 输入文档
- 需求基线：无独立 requirement.md（已有能力补录）
- 设计文档：`05-ui-components/09-text-components/07-symbol-glyph/design.md`
- 源码定位：`frameworks/core/components_ng/pattern/symbol/symbol_model_ng.cpp`、`symbol_source_info.h`、`constants.h`

## 用户故事

### US-1: 系统符号字形渲染
作为开发者，我希望以 `SymbolGlyph(symbolId)` 传入 HMSymbol 矢量资源即可渲染系统符号，以便复用系统符号字体。

| AC编号 | 验收标准 | 类型 |
|--------|----------|------|
| AC-1.1 | WHEN 构造 `SymbolGlyph($r('sys.symbol.ohos_wifi'))` THEN 节点以 "SymbolGlyph" tag 创建并复用 TextPattern，渲染对应矢量符号 | 正常 |
| AC-1.2 | WHEN `symbolId` 为 undefined THEN 按默认空字形创建节点，不崩溃 | 边界 |
| AC-1.3 | WHEN 切换 symbolId 资源 THEN SymbolSourceInfo.unicode 更新并触发 MEASURE 重排 | 正常 |

### US-2: 自定义符号字形
作为开发者，我希望经 `setSymbolGlyphOptions`/自定义 fontFamily 渲染自定义符号字体。

| AC编号 | 验收标准 | 类型 |
|--------|----------|------|
| AC-2.1 | WHEN 经 C-API `setCustomSymbolGlyphInitialize(node, symbolId, fontFamily)` THEN SymbolType=CUSTOM 并用指定 fontFamily 渲染 | 正常 |
| AC-2.2 | WHEN 自定义 fontFamily 未注册 THEN 回退到系统符号字形并记录资源缺失 | 异常 |

## 验收追溯

| AC | 关联规则 | 关联 Task | 验证方式 | 证据 |
|----|----------|-----------|----------|------|
| AC-1.1 | R-1 | TASK-01 | 单测/XTS | symbol_model_ng.cpp:28 |
| AC-1.2 | R-2 | TASK-01 | 单测 | symbol_model_ng.cpp:41 |
| AC-1.3 | R-1 | TASK-01 | 单测 | text_layout_property.h:250 |
| AC-2.1 | R-3 | TASK-01 | C-API 单测 | arkoala_api.h:8523 |
| AC-2.2 | R-4 | TASK-01 | 单测 | symbol_model_ng.cpp:68 |

## 规则定义

| 规则ID | 类型 | 触发条件 | 预期行为 | 边界/约束 | 关联AC |
|--------|------|----------|----------|-----------|-------|
| R-1 | 行为 | 构造 `SymbolGlyph(value?: Resource)` | 经 `SymbolModelNG::Create(unicode)` 创建 "SymbolGlyph" FrameNode（TextPattern），写入 SymbolSourceInfo | value 为 Resource | AC-1.1,AC-1.3 |
| R-2 | 边界 | value 为 undefined/空 | 创建空字形节点，不崩溃 | — | AC-1.2 |
| R-3 | 行为 | C-API setCustomSymbolGlyphInitialize | SymbolType=CUSTOM，设置 SymbolFontFamilies 与 unicode | fontFamily 非空 | AC-2.1 |
| R-4 | 异常 | 自定义 fontFamily 未注册 | 回退系统字形，记录资源缺失 | — | AC-2.2 |

## 验证映射

| 编号 | 对应规格项 | 验证方式 | 验证重点 |
|------|-----------|----------|----------|
| VM-1 | R-1 Create 路径 | 单测 | tag 与 Pattern 复用 |
| VM-2 | R-3 自定义源 | C-API 单测 | SymbolType=CUSTOM |
| VM-3 | R-4 资源回退 | 单测 | 不崩溃 |

## API 变更分析

### 新增 API

| API 名称 | 开放范围 | 入参概要 | 返回值 | 错误码范围 | 功能描述 | 关联 AC |
|----------|----------|----------|--------|-----------|----------|---------|
| `SymbolGlyph(value?: Resource)` | Public | Resource symbolId | SymbolGlyphAttribute | 无 | 构造系统符号节点 | AC-1.1 |
| `setSymbolGlyphOptions(value?: Resource)` (静态 ArkTS) | Public | Resource | this | 无 | 设置字形资源 | AC-1.3 |
| C-API `setSymbolGlyphInitialize(node, symbolId)` | System | KNode, Resource | void | 无 | 设置系统字形 | AC-1.1 |
| C-API `setCustomSymbolGlyphInitialize(node, symbolId, fontFamily)` | System | KNode, Resource, string | void | 无 | 设置自定义字形 | AC-2.1 |
| C-API `setSymbolFontFamilies(node, family)` | System | KNode, string | void | 无 | 设置符号字体族 | AC-2.1 |
| C-API `createFrameNode(symbolId)` | System | Resource | KNode | 无 | 创建独立 FrameNode | AC-1.1 |

### 变更/废弃 API
无。

## 接口规格

### 接口定义

**SymbolGlyph(value?: Resource)**

| 属性 | 值 |
|------|-----|
| 函数签名 | `SymbolGlyph(value?: Resource): SymbolGlyphAttribute` |
| 返回值 | `SymbolGlyphAttribute` — 属性构建器 |
| 开放范围 | Public |
| 错误码 | N/A |
| 关联 AC | AC-1.1 |

**参数约束**

| 参数 | 类型 | 必填 | 默认值 | 约束条件 |
|------|------|------|--------|---------|
| value | Resource | 否 | undefined | HMSymbol 矢量资源；undefined 时创建空字形 |

**行为场景**

| # | 触发条件 | 预期行为 | 关联 AC |
|---|----------|----------|---------|
| 1 | 传入合法 Resource | 创建 SymbolGlyph 节点并渲染 | AC-1.1 |
| 2 | 传入 undefined | 创建空字形节点 | AC-1.2 |

## 兼容性声明
- **已有 API 行为变更:** 否
- **配置文件格式变更:** 否
- **数据存储格式变更:** 否
- **最低支持版本:** API 11（@since 11 基线，@since 12 atomicservice/form）
- **API 版本号策略:** 全量 @since 标注；公共 ArkTS @since 11/12，C-API @since 12

## 架构约束

| 关键约束 | 约束说明 | 影响 AC |
|----------|----------|---------|
| 复用 TextPattern | 不新建独立 Pattern | AC-1.1 |
| Create 经 SymbolModelNG | 统一分发入口 | AC-1.1 |

## 非功能性需求

| 类型 | 指标/阈值 | 验证方式 | 证据 |
|------|-----------|----------|------|
| 可测试性 | Create 路径可单测 | 单测 | symbol_model_ng.cpp |

## 多设备适配声明

| 设备类型 | 行为差异 | 规格/约束 | 验证方式 | 证据 |
|----------|----------|-----------|----------|------|
| 手机/平板/折叠屏 | 无差异 | — | — | — |

## 全局特性影响

| 特性 | 适用？ | 结论 | 关联场景 |
|------|--------|------|----------|
| 无障碍 | 是 | 复用 TextPattern 无障碍 | AC-1.1 |
| 大字体 | 是 | minFontScale/maxFontScale 见 Feat-02 | — |
| 深色模式 | 是 | 颜色随主题见 Feat-03 | — |

## 行为场景（可选，Gherkin）
L1 复杂度，使用接口规格→行为场景表即可，不重复 Gherkin。

## Spec 自审清单
- [x] 无"待定""TBD""TODO"等占位符
- [x] 所有 AC 使用 WHEN/THEN 格式，可独立测试
- [x] 范围边界明确
- [x] 无语义模糊表述
- [x] AC 与规则表交叉一致
- [x] 规则表每条通过 5 项质量检查

## context-references
```yaml
context-queries:
  - repo: "openharmony/arkui_ace_engine"
    query: "SymbolGlyph Create 路径与 SymbolType SYSTEM/CUSTOM 分支"
```
**关键文档：** `interface/sdk-js/api/@internal/component/ets/symbolglyph.d.ts`
