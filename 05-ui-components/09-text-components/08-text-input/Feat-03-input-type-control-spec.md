# 特性规格

## 概述

| 属性 | 值 |
|------|-----|
| 特性名称 | TextInput 输入类型与控制 |
| 特性编号 | Func-05-09-08-Feat-03 |
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
- 源码定位：`text_field_model_ng.h`（SetType/SetContentType/SetEnableKeyboardOnFocus/SetSelectAllValue/SetCopyOption/SetSelectionMenuOptions/SetEnablePreviewText）、`text_content_type.h`

## 用户故事

### US-1: 输入类型
作为开发者，我希望经 type 切换 InputType。

| AC编号 | 验收标准 | 类型 |
|--------|----------|------|
| AC-1.1 | WHEN `type(InputType.Normal\|Number\|PhoneNumber\|Email\|Password)` THEN 切换 IME 类型 @since 7/9/10/11 | 正常 |
| AC-1.2 | WHEN `type(NUMBER_PASSWORD)`（@since 11/12）/`SCREEN_LOCK_PASSWORD`（@since 11, system）/`USER_NAME`/`NEW_PASSWORD`/`NUMBER_DECIMAL`/`URL`（@since 12）/`ONE_TIME_CODE`（@since 20）THEN 切换对应模式 | 正常 |

### US-2: 内容类型与自动填充控制
作为开发者，我希望经 contentType 设置自动填充内容类型。

| AC编号 | 验收标准 | 类型 |
|--------|----------|------|
| AC-2.1 | WHEN `contentType(ContentType.USER_NAME..)`（38 值，@since 12，含 @since 18 增量）THEN 设置自动填充内容类型 | 正常 |

### US-3: 编辑控制
作为开发者，我希望控制 enableKeyboardOnFocus/selectAll/copyOption/selectionMenuHidden/editMenuOptions/enablePreviewText/enableSelectedDataDetector。

| AC编号 | 验收标准 | 类型 |
|--------|----------|------|
| AC-3.1 | WHEN `enableKeyboardOnFocus(value)` THEN 控制聚焦时是否拉起键盘 | 正常 |
| AC-3.2 | WHEN `selectAll(true)`（@since 12）THEN 全选 | 正常 |
| AC-3.3 | WHEN `copyOption(value)` THEN 控制复制能力 | 正常 |
| AC-3.4 | WHEN `selectionMenuHidden(true)` THEN 隐藏选择菜单 | 正常 |
| AC-3.5 | WHEN `editMenuOptions(value)` THEN 自定义编辑菜单 | 正常 |
| AC-3.6 | WHEN `enablePreviewText(true)`（@since 16）THEN 启用预览文本 | 正常 |
| AC-3.7 | WHEN `enableSelectedDataDetector(true)`（@since 22）THEN 启用选中数据检测 | 正常 |

## 验收追溯

| AC | 关联规则 | 关联 Task | 验证方式 | 证据 |
|----|----------|-----------|----------|------|
| AC-1.1 | R-1 | TASK-TI-03 | 单测 | text_field_model_ng.h:38 |
| AC-1.2 | R-1 | TASK-TI-03 | 单测 | text_input.d.ts InputType |
| AC-2.1 | R-2 | TASK-TI-03 | 单测 | text_content_type.h |
| AC-3.1 | R-3 | TASK-TI-03 | 单测 | text_field_model_ng.h |
| AC-3.2 | R-3 | TASK-TI-03 | 单测 | text_field_model_ng.h:138 |
| AC-3.6 | R-4 | TASK-TI-03 | 单测 | text_field_model_ng.h:161 |
| AC-3.7 | R-4 | TASK-TI-03 | C-API 单测 | native_node.h:4236 |

## 规则定义

| 规则ID | 类型 | 触发条件 | 预期行为 | 边界/约束 | 关联AC |
|--------|------|----------|----------|-----------|-------|
| R-1 | 行为 | type(InputType) | 切换 IME 类型 | 14 值，含 @since 20 ONE_TIME_CODE | AC-1.1,1.2 |
| R-2 | 行为 | contentType(ContentType) | 设置自动填充内容类型 | 38 值，含 @since 18 增量 | AC-2.1 |
| R-3 | 行为 | enableKeyboardOnFocus/selectAll/copyOption/selectionMenuHidden/editMenuOptions | 控制编辑行为 | — | AC-3.1..3.5 |
| R-4 | 行为 | enablePreviewText（@since 16）/enableSelectedDataDetector（@since 22） | 启用预览/数据检测 | — | AC-3.6,3.7 |

## 验证映射

| 编号 | 对应规格项 | 验证方式 | 验证重点 |
|------|-----------|----------|----------|
| VM-1 | R-1 type 切换 | 单测 | IME 类型 |
| VM-2 | R-2 contentType | 单测 | 38 值 |
| VM-3 | R-4 预览/检测 | 单测+C-API 单测 | @since 16/22 |

## API 变更分析

### 新增 API

| API 名称 | 开放范围 | 入参概要 | 返回值 | 错误码范围 | 功能描述 | 关联 AC |
|----------|----------|----------|--------|-----------|----------|---------|
| `type(value)` | Public | InputType | this | 无 | 输入类型 @since 7–20 | AC-1.1 |
| `contentType(value)` | Public | ContentType | this | 无 | 内容类型 @since 12/18 | AC-2.1 |
| `enableKeyboardOnFocus(value)` | Public | boolean | this | 无 | 聚焦拉键盘 @since 11 | AC-3.1 |
| `selectAll(value)` | Public | boolean | this | 无 | 全选 @since 12 | AC-3.2 |
| `copyOption(value)` | Public | CopyOptions | this | 无 | 复制能力 | AC-3.3 |
| `selectionMenuHidden(value)` | Public | boolean | this | 无 | 隐藏菜单 @since 11 | AC-3.4 |
| `editMenuOptions(value)` | Public | EditMenuOptions | this | 无 | 自定义菜单 @since 12 | AC-3.5 |
| `enablePreviewText(enable)` | Public | boolean | this | 无 | 预览文本 @since 12/16 | AC-3.6 |
| `enableSelectedDataDetector` | Public | boolean | this | 无 | 数据检测 @since 22 | AC-3.7 |
| C-API `NODE_TEXT_INPUT_TYPE`/`CONTENT_TYPE`/`SELECT_ALL`/`SELECTION_MENU_HIDDEN`/`ENABLE_PREVIEW_TEXT`/`ENABLE_SELECTED_DATA_DETECTOR` | System | KNode, ... | void | 无 | C-API 对应 | 全部 |

## 接口规格

### 接口定义

**type(value)**

| 属性 | 值 |
|------|-----|
| 函数签名 | `type(value: InputType): TextInputAttribute` |
| 返回值 | `TextInputAttribute` |
| 开放范围 | Public |
| 错误码 | N/A |
| 关联 AC | AC-1.1 |

**参数约束**

| 参数 | 类型 | 必填 | 默认值 | 约束条件 |
|------|------|------|--------|---------|
| value | InputType | 是 | Normal | 14 枚举值 |

**行为场景**

| # | 触发条件 | 预期行为 | 关联 AC |
|---|----------|----------|---------|
| 1 | Password | 密码模式 IME | AC-1.1 |
| 2 | ONE_TIME_CODE（@since 20） | 验证码模式 | AC-1.2 |

## 兼容性声明
- **已有 API 行为变更:** 否
- **最低支持版本:** type @since 7/9/10/11（URL @since 12，ONE_TIME_CODE @since 20）；contentType @since 12（@since 18 增量）；enablePreviewText @since 16；enableSelectedDataDetector @since 22
- **API 版本号策略:** 全量 @since 标注

## 架构约束
| 关键约束 | 约束说明 | 影响 AC |
|----------|----------|---------|
| InputType 驱动 IME | type→IME 类型 | AC-1.1 |

## 非功能性需求
| 类型 | 指标/阈值 | 验证方式 | 证据 |
|------|-----------|----------|------|
| 可测试性 | type 切换可单测 | 单测 | text_field_model_ng.h:38 |

## 多设备适配声明
无差异。

## 全局特性影响
| 特性 | 适用？ | 结论 | 关联场景 |
|------|--------|------|----------|
| 无障碍 | 是 | type 影响无障碍描述 | AC-1.1 |

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
    query: "TextInput InputType/ContentType 切换路径"
```
**关键文档：** `interface/sdk-js/api/@internal/component/ets/text_input.d.ts`
