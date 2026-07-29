# 特性规格

## 概述

| 属性 | 值 |
|------|-----|
| 特性名称 | TextInput C-API/NDK Modifier 桥与无障碍 |
| 特性编号 | Func-05-09-08-Feat-10 |
| 所属 Epic | 无 |
| 优先级 | P1 |
| 目标版本 | API 12–26 |
| SIG 归属 | ArkUI SIG |
| 状态 | Baselined |
| 复杂度 | 复杂 |

## 本次变更范围（Delta）
全新特性补录（lineage: new），无 Delta。

## 输入文档
- 设计文档：`08-text-input/design.md`
- 源码定位：`interfaces/native/native_node.h`（ARKUI_NODE_TEXT_INPUT=7 L69；attrs L3733–4463；events L10801–11026）、`interfaces/native/node_attributes/text_input.h`、`frameworks/core/interfaces/native/node/node_text_input_modifier.h`、`text_field_accessibility_property.h`

## 用户故事

### US-1: C-API 节点与属性
作为 NDK 开发者，我希望经 ARKUI_NODE_TEXT_INPUT 创建节点并设置 51 个属性。

| AC编号 | 验收标准 | 类型 |
|--------|----------|------|
| AC-1.1 | WHEN `ArkUI_NodeType.ARKUI_NODE_TEXT_INPUT` 创建节点 THEN 节点类型=7 | 正常 |
| AC-1.2 | WHEN 设置 NODE_TEXT_INPUT_* 属性（51 个，@since 12–26，id 跳号 7032+ 为增量）THEN 经 text_input_dynamic_modifier 派发到 TextFieldModelNG::Set* | 正常 |
| AC-1.3 | WHEN 设置 NODE_TEXT_INPUT_LETTER_SPACING（@since 16）/LINE_HEIGHT（@since 20）/SHOW_COUNTER（@since 22）/DIRECTION（@since 23）/TEXT_OVERFLOW（@since 24）/DECORATION（@since 26）THEN 按版本可用 | 边界 |

### US-2: C-API 事件
作为 NDK 开发者，我希望经 18 个 NODE_TEXT_INPUT_ON_* 事件监听。

| AC编号 | 验收标准 | 类型 |
|--------|----------|------|
| AC-2.1 | WHEN 注册 NODE_TEXT_INPUT_ON_CHANGE/SUBMIT/EDIT_CHANGE/TEXT_SELECTION_CHANGE/CONTENT_SIZE_CHANGE/INPUT_FILTER_ERROR/CONTENT_SCROLL/WILL_INSERT/DID_INSERT/WILL_DELETE/DID_DELETE（@since 12）THEN 经 node_text_input_modifier Set/Reset 派发 | 正常 |
| AC-2.2 | WHEN 注册 ON_CHANGE_WITH_PREVIEW_TEXT（@since 16）/ON_WILL_CHANGE（@since 20）/ON_PASTE/ON_COPY/ON_WILL_COPY/ON_WILL_CUT（@since 26）THEN 按版本可用 | 边界 |

### US-3: 枚举与无障碍
作为开发者，我希望经 C-API 枚举与 userAccessibilityText 获取无障碍。

| AC编号 | 验收标准 | 类型 |
|--------|----------|------|
| AC-3.1 | WHEN 使用 ArkUI_TextInputType（14 值，含 ONE_TIME_CODE @since 20）/ArkUI_TextInputContentType（38 值，含 @since 18 增量）/ArkUI_CancelButtonStyle/ArkUI_TextInputStyle 枚举 THEN 正确解析 | 正常 |
| AC-3.2 | WHEN `userAccessibilityText(value)` THEN 设置无障碍文本 | 正常 |
| AC-3.3 | WHEN text_field_accessibility_property THEN 提供无障碍属性 | 正常 |

## 验收追溯

| AC | 关联规则 | 关联 Task | 验证方式 | 证据 |
|----|----------|-----------|----------|------|
| AC-1.1 | R-1 | TASK-TI-10 | C-API 单测 | native_node.h:69 |
| AC-1.2 | R-2 | TASK-TI-10 | C-API 单测 | text_input_dynamic_modifier.cpp |
| AC-1.3 | R-3 | TASK-TI-10 | C-API 单测 | native_node.h:4156/4223/4260/4342/4370/4383 |
| AC-2.1 | R-4 | TASK-TI-10 | C-API 单测 | node_text_input_modifier.h |
| AC-2.2 | R-5 | TASK-TI-10 | C-API 单测 | native_node.h:10975/10988/10849/11000/11013/11026 |
| AC-3.1 | R-6 | TASK-TI-10 | C-API 单测 | text_input.h:50/95/227 |
| AC-3.2 | R-7 | TASK-TI-10 | 单测 | text_field_model_ng.h:185/451 |
| AC-3.3 | R-7 | TASK-TI-10 | 单测 | text_field_accessibility_property.h |

## 规则定义

| 规则ID | 类型 | 触发条件 | 预期行为 | 边界/约束 | 关联AC |
|--------|------|----------|----------|-----------|-------|
| R-1 | 行为 | ARKUI_NODE_TEXT_INPUT 创建 | 节点类型=7 | — | AC-1.1 |
| R-2 | 行为 | 设置 NODE_TEXT_INPUT_* 属性 | 派发到 TextFieldModelNG::Set* | 51 属性 | AC-1.2 |
| R-3 | 边界 | 增量属性按 @since 可用 | LETTER_SPACING @since 16；LINE_HEIGHT/ENABLE_FILL_ANIMATION @since 20；SHOW_COUNTER/SELECTED_DATA_DETECTOR @since 22；DIRECTION/COMPRESS_LEADING_PUNCTUATION/INCLUDE_FONT_PADDING/FALLBACK_LINE_SPACING/SELECTED_DRAG_PREVIEW_STYLE @since 23；TEXT_OVERFLOW/ELLIPSIS_MODE @since 24；DECORATION/LINEAR_GRADIENT/RADIAL_GRADIENT/PUNCTUATION_OVERFLOW @since 26 | 按版本判定 | AC-1.3 |
| R-4 | 行为 | 注册 ON_* 事件（@since 12） | Set/Reset 派发 | 12 事件基线 | AC-2.1 |
| R-5 | 边界 | 增量事件按 @since | ON_CHANGE_WITH_PREVIEW_TEXT @since 16；ON_WILL_CHANGE @since 20；ON_PASTE/ON_COPY/ON_WILL_COPY/ON_WILL_CUT @since 26 | — | AC-2.2 |
| R-6 | 行为 | C-API 枚举 | 正确解析 | — | AC-3.1 |
| R-7 | 行为 | userAccessibilityText/accessibility_property | 无障碍文本/属性 | — | AC-3.2,3.3 |

## 验证映射

| 编号 | 对应规格项 | 验证方式 | 验证重点 |
|------|-----------|----------|----------|
| VM-1 | R-1/R-2 节点+属性 | C-API 单测 | 派发 Set* |
| VM-2 | R-3/R-5 版本边界 | C-API 单测 | @since 判定 |
| VM-3 | R-7 无障碍 | 单测 | userAccessibilityText |

## API 变更分析

### 新增 API

| API 名称 | 开放范围 | 入参概要 | 返回值 | 错误码范围 | 功能描述 | 关联 AC |
|----------|----------|----------|--------|-----------|----------|---------|
| `ARKUI_NODE_TEXT_INPUT` 节点类型 | System | — | — | 无 | 节点类型 @since 12 | AC-1.1 |
| 51 个 `NODE_TEXT_INPUT_*` 属性 | System | KNode, value | void | 无 | 属性 @since 12–26 | AC-1.2,1.3 |
| 18 个 `NODE_TEXT_INPUT_ON_*` 事件 | System | KNode, callback | void | 无 | 事件 @since 12–26 | AC-2.1,2.2 |
| 枚举 `ArkUI_TextInputType`/`ArkUI_CancelButtonStyle`/`ArkUI_TextInputContentType`/`ArkUI_TextInputStyle` | System | — | — | 无 | 枚举 @since 12–20 | AC-3.1 |
| `userAccessibilityText(value)` | Public | string | this | 无 | 无障碍文本 | AC-3.2 |

## 接口规格

### 接口定义

**ARKUI_NODE_TEXT_INPUT 节点 + NODE_TEXT_INPUT_* 属性**

| 属性 | 值 |
|------|-----|
| 函数签名 | `ArkUI_NodeHandle ArkUI_NodeAdapter_CreateNode(ARKUI_NODE_TEXT_INPUT, ...)` + `setAttribute(NODE_TEXT_INPUT_*, value)` |
| 返回值 | `ArkUI_NodeHandle` / `int` |
| 开放范围 | System |
| 错误码 | ARKUI_ERROR_CODE_* |
| 关联 AC | AC-1.1,1.2 |

**参数约束**

| 参数 | 类型 | 必填 | 默认值 | 约束条件 |
|------|------|------|--------|---------|
| NODE_TEXT_INPUT_* | ArkUI_AttributeItem | 是 | — | 增量属性按 @since |

**行为场景**

| # | 触发条件 | 预期行为 | 关联 AC |
|---|----------|----------|---------|
| 1 | 创建节点 | type=7 | AC-1.1 |
| 2 | 设置属性 | 派发 Set* | AC-1.2 |
| 3 | 增量属性 | @since 判定 | AC-1.3 |

## 兼容性声明
- **已有 API 行为变更:** 否
- **最低支持版本:** C-API 基线 @since 12；增量 @since 15/16/18/20/22/23/24/26
- **API 版本号策略:** 全量 @since 标注；id 跳号 7032+ 为增量，保持 id 稳定不破坏 ABI

## 架构约束
| 关键约束 | 约束说明 | 影响 AC |
|----------|----------|---------|
| dynamic_modifier 派发 | AttributeItem→Set* | AC-1.2 |
| id 跳号稳定 ABI | 增量用 7032+ | AC-1.3 |

## 非功能性需求
| 类型 | 指标/阈值 | 验证方式 | 证据 |
|------|-----------|----------|------|
| 可测试性 | C-API 全覆盖 | C-API 单测 | text_input.h |

## 多设备适配声明
无差异。

## 全局特性影响
| 特性 | 适用？ | 结论 | 关联场景 |
|------|--------|------|----------|
| 无障碍 | 是 | userAccessibilityText + accessibility_property | AC-3.2,3.3 |

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
    query: "TextInput C-API NODE_TEXT_INPUT_* 属性/事件 id 与 @since 映射"
```
**关键文档：** `interfaces/native/native_node.h`、`interfaces/native/node_attributes/text_input.h`
