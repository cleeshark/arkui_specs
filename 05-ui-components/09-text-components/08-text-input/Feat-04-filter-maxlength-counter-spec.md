# 特性规格

## 概述

| 属性 | 值 |
|------|-----|
| 特性名称 | TextInput 文本筛选与 maxLength/计数器 |
| 特性编号 | Func-05-09-08-Feat-04 |
| 所属 Epic | 无 |
| 优先级 | P1 |
| 目标版本 | API 7–22 |
| SIG 归属 | ArkUI SIG |
| 状态 | Baselined |
| 复杂度 | 标准 |

## 本次变更范围（Delta）
全新特性补录（lineage: new），无 Delta。

## 输入文档
- 设计文档：`08-text-input/design.md`
- 源码定位：`text_field_model_ng.h`（SetMaxLength/SetInputFilter/SetShowCounter/SetCounterTextColor/SetCounterType/SetShowCounterBorder）、`text_input_layout_algorithm.cpp`（MeasureCounterWithPolicy）

## 用户故事

### US-1: maxLength
作为开发者，我希望限制输入最大长度。

| AC编号 | 验收标准 | 类型 |
|--------|----------|------|
| AC-1.1 | WHEN `maxLength(n)` THEN 超长输入被截断 | 正常 |
| AC-1.2 | WHEN maxLength=0 或负数 THEN 按既有约束处理，不限制或默认值 | 边界 |

### US-2: inputFilter
作为开发者，我希望经正则 inputFilter 过滤输入并回调错误。

| AC编号 | 验收标准 | 类型 |
|--------|----------|------|
| AC-2.1 | WHEN `inputFilter(regex, error?)` THEN 不匹配字符被过滤 | 正常 |
| AC-2.2 | WHEN 过滤触发 THEN error 回调返回被过滤内容（@since 18 Callback<string>） | 正常 |

### US-3: 计数器
作为开发者，我希望经 showCounter 显示输入计数。

| AC编号 | 验收标准 | 类型 |
|--------|----------|------|
| AC-3.1 | WHEN `showCounter(true, options?)` THEN 显示计数（含 InputCounterOptions） | 正常 |
| AC-3.2 | WHEN threshold 百分比达到 THEN 计数高亮（showCounterBorder/counterTextColor） | 正常 |
| AC-3.3 | WHEN C-API `NODE_TEXT_INPUT_SHOW_COUNTER`（@since 22）THEN 显示计数 | 正常 |

## 验收追溯

| AC | 关联规则 | 关联 Task | 验证方式 | 证据 |
|----|----------|-----------|----------|------|
| AC-1.1 | R-1 | TASK-TI-04 | 单测 | text_field_model_ng.h:55 |
| AC-1.2 | R-2 | TASK-TI-04 | 单测 | — |
| AC-2.1 | R-3 | TASK-TI-04 | 单测 | text_field_model_ng.h:64 |
| AC-2.2 | R-3 | TASK-TI-04 | 单测 | text_input.d.ts inputFilter @since 18 |
| AC-3.1 | R-4 | TASK-TI-04 | 单测 | text_field_model_ng.h:109 |
| AC-3.2 | R-4 | TASK-TI-04 | 单测 | MeasureCounterWithPolicy |
| AC-3.3 | R-4 | TASK-TI-04 | C-API 单测 | native_node.h:4260 |

## 规则定义

| 规则ID | 类型 | 触发条件 | 预期行为 | 边界/约束 | 关联AC |
|--------|------|----------|----------|-----------|-------|
| R-1 | 行为 | maxLength(n) | 超长截断 | n≥0 | AC-1.1 |
| R-2 | 边界 | maxLength≤0 | 按既有约束（不限制/默认） | — | AC-1.2 |
| R-3 | 行为 | inputFilter(regex, error?) | 不匹配字符过滤；error 回调（@since 18） | regex ResourceStr | AC-2.1,2.2 |
| R-4 | 行为 | showCounter(true, options?) | 显示计数 + threshold 高亮（@since 22 C-API） | options 含 threshold% | AC-3.1..3.3 |

## 验证映射

| 编号 | 对应规格项 | 验证方式 | 验证重点 |
|------|-----------|----------|----------|
| VM-1 | R-1 maxLength | 单测 | 截断 |
| VM-2 | R-3 过滤 | 单测 | error 回调 |
| VM-3 | R-4 计数器 | 单测+C-API 单测 | MeasureCounterWithPolicy |

## API 变更分析

### 新增 API

| API 名称 | 开放范围 | 入参概要 | 返回值 | 错误码范围 | 功能描述 | 关联 AC |
|----------|----------|----------|--------|-----------|----------|---------|
| `maxLength(value)` | Public | number | this | 无 | 最大长度 @since 7 | AC-1.1 |
| `inputFilter(value, error?)` | Public | ResourceStr, Callback<string>? | this | 无 | 输入过滤 @since 8/18 | AC-2.1 |
| `showCounter(value, options?)` | Public | boolean, InputCounterOptions? | this | 无 | 计数器 @since 11/22 | AC-3.1 |
| C-API `NODE_TEXT_INPUT_MAX_LENGTH`/`INPUT_FILTER`/`SHOW_COUNTER` | System | KNode, ... | void | 无 | C-API 对应 @since 12/22 | 全部 |

## 接口规格

### 接口定义

**maxLength(value)**

| 属性 | 值 |
|------|-----|
| 函数签名 | `maxLength(value: number): TextInputAttribute` |
| 返回值 | `TextInputAttribute` |
| 开放范围 | Public |
| 错误码 | N/A |
| 关联 AC | AC-1.1 |

**参数约束**

| 参数 | 类型 | 必填 | 默认值 | 约束条件 |
|------|------|------|--------|---------|
| value | number | 是 | — | ≤0 触发 R-2 |

**行为场景**

| # | 触发条件 | 预期行为 | 关联 AC |
|---|----------|----------|---------|
| 1 | n>0 | 截断 | AC-1.1 |
| 2 | n≤0 | 按既有约束 | AC-1.2 |

## 兼容性声明
- **已有 API 行为变更:** 否
- **最低支持版本:** maxLength @since 7；inputFilter @since 8（Callback<string> @since 18）；showCounter @since 11（C-API @since 22）
- **API 版本号策略:** 全量 @since 标注

## 架构约束
| 关键约束 | 约束说明 | 影响 AC |
|----------|----------|---------|
| MeasureCounterWithPolicy | 计数器独立布局 | AC-3.2 |

## 非功能性需求
| 类型 | 指标/阈值 | 验证方式 | 证据 |
|------|-----------|----------|------|
| 性能 | 过滤+计数无明显卡顿 | 帧率测试 | — |

## 多设备适配声明
无差异。

## 全局特性影响
| 特性 | 适用？ | 结论 | 关联场景 |
|------|--------|------|----------|
| 大字体 | 是 | 计数器随字体缩放 | AC-3.1 |

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
    query: "TextInput inputFilter/maxLength/showCounter 布局"
```
**关键文档：** `interface/sdk-js/api/@internal/component/ets/text_input.d.ts`
