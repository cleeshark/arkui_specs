# 特性规格

## 概述

| 属性 | 值 |
|------|-----|
| 特性名称 | TextInput 取消按钮/响应区域 |
| 特性编号 | Func-05-09-08-Feat-09 |
| 所属 Epic | 无 |
| 优先级 | P2 |
| 目标版本 | API 11–18 |
| SIG 归属 | ArkUI SIG |
| 状态 | Baselined |
| 复杂度 | 简单 |

## 本次变更范围（Delta）
全新特性补录（lineage: new），无 Delta。

## 输入文档
- 设计文档：`08-text-input/design.md`
- 源码定位：`text_field_model_ng.h`（SetCleanNodeStyle + cancel icon setters，cancelButton 重载）

## 用户故事

### US-1: 取消按钮
作为开发者，我希望经 cancelButton 显示清除按钮（含 Symbol 重载）。

| AC编号 | 验收标准 | 类型 |
|--------|----------|------|
| AC-1.1 | WHEN `cancelButton(CancelButtonOptions)`（@since 18）THEN 显示清除按钮 | 正常 |
| AC-1.2 | WHEN `cancelButton(CancelButtonSymbolOptions)`（@since 18）THEN 显示 Symbol 清除按钮 | 正常 |
| AC-1.3 | WHEN C-API `NODE_TEXT_INPUT_CANCEL_BUTTON`（@since 12）THEN 显示清除按钮 | 正常 |

### US-2: 响应区域/语音按钮
作为开发者，我希望经 cleanNodeStyle/isShowCancelButton/isShowVoiceButton 控制响应区域。

| AC编号 | 验收标准 | 类型 |
|--------|----------|------|
| AC-2.1 | WHEN `cleanNodeStyle(value)` THEN 设置清除节点样式 | 正常 |
| AC-2.2 | WHEN isShowCancelButton/isShowVoiceButton THEN 控制按钮显隐 | 正常 |

## 验收追溯

| AC | 关联规则 | 关联 Task | 验证方式 | 证据 |
|----|----------|-----------|----------|------|
| AC-1.1 | R-1 | TASK-TI-09 | 单测 | text_input.d.ts cancelButton @since 18 |
| AC-1.2 | R-1 | TASK-TI-09 | 单测 | text_input.d.ts cancelButton Symbol 重载 |
| AC-1.3 | R-1 | TASK-TI-09 | C-API 单测 | native_node.h:3925 |
| AC-2.1 | R-2 | TASK-TI-09 | 单测 | text_field_model_ng.h:129 |
| AC-2.2 | R-2 | TASK-TI-09 | 单测 | text_field_layout_property.h |

## 规则定义

| 规则ID | 类型 | 触发条件 | 预期行为 | 边界/约束 | 关联AC |
|--------|------|----------|----------|-----------|-------|
| R-1 | 行为 | cancelButton（Options/SymbolOptions，@since 18；C-API @since 12） | 显示清除按钮 | 含 style/响应区域 | AC-1.1..1.3 |
| R-2 | 行为 | cleanNodeStyle/isShowCancelButton/isShowVoiceButton | 控制样式/显隐 | — | AC-2.1,2.2 |

## 验证映射

| 编号 | 对应规格项 | 验证方式 | 验证重点 |
|------|-----------|----------|----------|
| VM-1 | R-1 取消按钮 | 单测+C-API | Symbol 重载 |
| VM-2 | R-2 响应区域 | 单测 | 显隐 |

## API 变更分析

### 新增 API

| API 名称 | 开放范围 | 入参概要 | 返回值 | 错误码范围 | 功能描述 | 关联 AC |
|----------|----------|----------|--------|-----------|----------|---------|
| `cancelButton(options: CancelButtonOptions)` | Public | CancelButtonOptions | this | 无 | 清除按钮 @since 18 | AC-1.1 |
| `cancelButton(symbolOptions: CancelButtonSymbolOptions)` | Public | CancelButtonSymbolOptions | this | 无 | Symbol 清除按钮 @since 18 | AC-1.2 |
| C-API `NODE_TEXT_INPUT_CANCEL_BUTTON` | System | KNode, options | void | 无 | 清除按钮 @since 12 | AC-1.3 |
| `cleanNodeStyle`/`isShowCancelButton`/`isShowVoiceButton` | InnerApi | — | — | 无 | 响应区域 | AC-2.1,2.2 |

## 接口规格

### 接口定义

**cancelButton(options)**

| 属性 | 值 |
|------|-----|
| 函数签名 | `cancelButton(options: CancelButtonOptions): TextInputAttribute` |
| 返回值 | `TextInputAttribute` |
| 开放范围 | Public |
| 错误码 | N/A |
| 关联 AC | AC-1.1 |

**参数约束**

| 参数 | 类型 | 必填 | 默认值 | 约束条件 |
|------|------|------|--------|---------|
| options | CancelButtonOptions | 是 | — | 含 style |

**行为场景**

| # | 触发条件 | 预期行为 | 关联 AC |
|---|----------|----------|---------|
| 1 | Options | 显示清除按钮 | AC-1.1 |
| 2 | SymbolOptions | Symbol 清除按钮 | AC-1.2 |

## 兼容性声明
- **已有 API 行为变更:** 否
- **最低支持版本:** cancelButton（ArkTS）@since 18；C-API NODE_TEXT_INPUT_CANCEL_BUTTON @since 12
- **API 版本号策略:** 全量 @since 标注

## 架构约束
| 关键约束 | 约束说明 | 影响 AC |
|----------|----------|---------|
| 响应区域布局 | cleanNodeStyle 驱动 | AC-2.1 |

## 非功能性需求
| 类型 | 指标/阈值 | 验证方式 | 证据 |
|------|-----------|----------|------|
| 可测试性 | 按钮显隐可单测 | 单测 | text_field_layout_property.h |

## 多设备适配声明
无差异。

## 全局特性影响
| 特性 | 适用？ | 结论 | 关联场景 |
|------|--------|------|----------|
| 无障碍 | 是 | 清除按钮需无障碍标签 | AC-1.1 |

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
    query: "TextInput cancelButton Symbol 重载与响应区域"
```
**关键文档：** `interface/sdk-js/api/@internal/component/ets/text_input.d.ts`
