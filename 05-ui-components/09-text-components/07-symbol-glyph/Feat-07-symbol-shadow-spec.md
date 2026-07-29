# 特性规格

## 概述

| 属性 | 值 |
|------|-----|
| 特性名称 | SymbolGlyph 符号阴影 |
| 特性编号 | Func-05-09-07-Feat-07 |
| 所属 Epic | 无 |
| 优先级 | P2 |
| 目标版本 | API 12 |
| SIG 归属 | ArkUI SIG |
| 状态 | Baselined |
| 复杂度 | 简单 |

## 本次变更范围（Delta）
全新特性补录（lineage: new），无 Delta。

## 输入文档
- 设计文档：`07-symbol-glyph/design.md`
- 源码定位：`symbol_model_ng.cpp:373–390`（SetSymbolShadow/SetSymbolShadowResObj）、`constants.h:123`（SymbolShadow struct）、`text_layout_property.h:259`

## 用户故事

### US-1: 符号阴影设置
作为开发者，我希望经 symbolShadow 为符号施加阴影。

| AC编号 | 验收标准 | 类型 |
|--------|----------|------|
| AC-1.1 | WHEN `symbolShadow(ShadowOptions)` THEN 写 SymbolShadow（color/offset/radius）并 MEASURE_SELF | 正常 |
| AC-1.2 | WHEN 阴影使用 Resource THEN 经 SetSymbolShadowResObj 异步加载 | 正常 |
| AC-1.3 | WHEN C-API `resetSymbolShadow` THEN 清除阴影 | 正常 |
| AC-1.4 | WHEN radius 为负数 THEN 按实现既有约束处理，不崩溃 | 边界 |

## 验收追溯

| AC | 关联规则 | 关联 Task | 验证方式 | 证据 |
|----|----------|-----------|----------|------|
| AC-1.1 | R-1 | TASK-07 | 单测 | text_layout_property.h:259 |
| AC-1.2 | R-2 | TASK-07 | 单测 | symbol_model_ng.cpp:373 |
| AC-1.3 | R-3 | TASK-07 | C-API 单测 | arkoala_api.h:8530 |
| AC-1.4 | R-4 | TASK-07 | 单测 | — |

## 规则定义

| 规则ID | 类型 | 触发条件 | 预期行为 | 边界/约束 | 关联AC |
|--------|------|----------|----------|-----------|-------|
| R-1 | 行为 | symbolShadow(ShadowOptions) | 写 SymbolShadow（color/offset/radius, MEASURE_SELF） | radius≥0 | AC-1.1 |
| R-2 | 行为 | 阴影用 Resource | 经 SetSymbolShadowResObj 异步加载 | 资源失败回退 | AC-1.2 |
| R-3 | 恢复 | C-API resetSymbolShadow | 清除阴影 | — | AC-1.3 |
| R-4 | 边界 | radius<0 | 按既有约束处理，不崩溃 | — | AC-1.4 |

## 验证映射

| 编号 | 对应规格项 | 验证方式 | 验证重点 |
|------|-----------|----------|----------|
| VM-1 | R-1 阴影写入 | 单测 | MEASURE_SELF |
| VM-2 | R-2 资源态 | 单测 | 回退 |
| VM-3 | R-3 reset | C-API 单测 | 清除 |

## API 变更分析

### 新增 API

| API 名称 | 开放范围 | 入参概要 | 返回值 | 错误码范围 | 功能描述 | 关联 AC |
|----------|----------|----------|--------|-----------|----------|---------|
| `symbolShadow(value: ShadowOptions)` | InnerApi/koala | ShadowOptions | this | 无 | 阴影（非公共 .d.ts） | AC-1.1 |
| C-API `setSymbolShadow`/`resetSymbolShadow` | System | KNode, SymbolShadow | void | 无 | 下发/重置 | AC-1.1,1.3 |

## 接口规格

### 接口定义

**symbolShadow(value)**

| 属性 | 值 |
|------|-----|
| 函数签名 | `symbolShadow(value: ShadowOptions): SymbolGlyphAttribute` |
| 返回值 | `SymbolGlyphAttribute` |
| 开放范围 | InnerApi/koala（公共 .d.ts 未含） |
| 错误码 | N/A |
| 关联 AC | AC-1.1 |

**参数约束**

| 参数 | 类型 | 必填 | 默认值 | 约束条件 |
|------|------|------|--------|---------|
| value | ShadowOptions | 是 | — | color/offset/radius；radius<0 触发 R-4 |

**行为场景**

| # | 触发条件 | 预期行为 | 关联 AC |
|---|----------|----------|---------|
| 1 | 合法 options | 写入并重测 | AC-1.1 |
| 2 | Resource | 异步加载 | AC-1.2 |
| 3 | radius<0 | 不崩溃 | AC-1.4 |

## 兼容性声明
- **已有 API 行为变更:** 否
- **最低支持版本:** symbolShadow 不在公共 ArkTS .d.ts，仅 C-API/koala（记风险）
- **API 版本号策略:** 全量 @since 标注；公共缺口记风险

## 架构约束
| 关键约束 | 约束说明 | 影响 AC |
|----------|----------|---------|
| MEASURE_SELF | 阴影变更重测 | 全部 |

## 非功能性需求
| 类型 | 指标/阈值 | 验证方式 | 证据 |
|------|-----------|----------|------|
| 可测试性 | 阴影写入可单测 | 单测 | constants.h:123 |

## 多设备适配声明
无差异。

## 全局特性影响
| 特性 | 适用？ | 结论 | 关联场景 |
|------|--------|------|----------|
| 深色模式 | 是 | 阴影颜色随主题 | — |

## Spec 自审清单
- [x] 无占位符
- [x] AC 用 WHEN/THEN
- [x] 范围明确
- [x] 无模糊表述
- [x] AC 与规则交叉一致
- [x] 规则通过 5 项检查

## context-references
```yaml
context-queries:
  - repo: "openharmony/arkui_ace_engine"
    query: "SymbolGlyph SymbolShadow 资源加载路径"
```
**关键文档：** `interface/sdk-js/api/@internal/component/ets/symbolglyph.d.ts`（注：symbolShadow 不在公共 .d.ts）
