# 特性规格

## 概述

| 属性 | 值 |
|------|-----|
| 特性名称 | C-API/NDK/ANI 属性字符串 |
| 特性编号 | Func-05-09-10-Feat-09 |
| 所属 Epic | 无 |
| 优先级 | P1 |
| 目标版本 | API 12–24 |
| SIG 归属 | ArkUI SIG |
| 状态 | Baselined |
| 复杂度 | 复杂 |

## 本次变更范围（Delta）
全新特性补录（lineage: new），无 Delta。

## 输入文档
- 设计文档：`10-attributed-string/design.md`
- 源码定位：`interfaces/native/native_styled_string.h`（drawing-typography）、`native_styled_string_descriptor.{h,cpp}`、`frameworks/core/interfaces/native/implementation/styled_string_accessor.cpp:570`（对象模型 accessor）、`styled_string_peer.h`、`ani/styled_string_ani_modifier.*`、`arkts_frontend/.../styled_string_module.*`、`arkoala_api_generated.h`（Ark_StyledStringKey/Ark_StyleOptions/Ark_SpanStyle）

## 用户故事

### US-1: drawing-typography C-API
作为 NDK 开发者，我希望经 `OH_ArkUI_StyledString_*` 构建排版。

| AC编号 | 验收标准 | 类型 |
|--------|----------|------|
| AC-1.1 | WHEN `OH_ArkUI_StyledString_Create(TypographyStyle, FontCollection)`（@since 12）THEN 创建 | 正常 |
| AC-1.2 | WHEN `PushTextStyle`/`AddText`/`PopTextStyle`/`CreateTypography`/`AddPlaceholder`（@since 12）THEN 构建排版 | 正常 |
| AC-1.3 | WHEN `OH_ArkUI_StyledString_Destroy` THEN 释放 | 正常 |

### US-2: TextLayoutManager
作为 NDK 开发者，我希望经 `ArkUI_TextLayoutManager` 查询布局。

| AC编号 | 验收标准 | 类型 |
|--------|----------|------|
| AC-2.1 | WHEN `ArkUI_TextLayoutManager_GetLineCount`/`GetRectsForRange`/`GetGlyphPositionAtCoordinate`/`GetLineMetrics`（@since 22）THEN 返回行/矩形/字形/度量 | 正常 |
| AC-2.2 | WHEN `GetCharacterPositionAtCoordinate`/`GetGlyphRangeForCharacterRange`/`GetCharacterRangeForGlyphRange`（@since 24）THEN 字符/字形互转 | 正常 |

### US-3: 对象模型 accessor + ANI
作为静态 ArkTS/NDK 开发者，我希望经对象模型 accessor 与 ANI modifier 操作。

| AC编号 | 验收标准 | 类型 |
|--------|----------|------|
| AC-3.1 | WHEN `GetStyledStringAccessor`（对象模型 accessor）THEN 经 Ark_StyleOptions/Ark_SpanStyle/Ark_StyledStringKey 操作 | 正常 |
| AC-3.2 | WHEN `GetStyledStringControllerAccessor`/`RichEditorStyledStringControllerAccessor::GetStyledStringImpl` THEN 控制器 accessor | 正常 |
| AC-3.3 | WHEN ANI `GetStyledStringAniModifier()`（@since 2025）THEN 静态 ArkTS ANI 桥接 | 正常 |
| AC-3.4 | WHEN arkoala `styled_string_module` THEN 静态 ArkTS 模块 | 正常 |

## 验收追溯

| AC | 关联规则 | 关联 Task | 验证方式 | 证据 |
|----|----------|-----------|----------|------|
| AC-1.1 | R-1 | TASK-AS-09 | C-API 单测 | native_styled_string.h |
| AC-1.2 | R-1 | TASK-AS-09 | C-API 单测 | native_styled_string.h |
| AC-2.1 | R-2 | TASK-AS-09 | C-API 单测 | native_styled_string.h @since 22 |
| AC-2.2 | R-2 | TASK-AS-09 | C-API 单测 | native_styled_string.h @since 24 |
| AC-3.1 | R-3 | TASK-AS-09 | C-API 单测 | styled_string_accessor.cpp:570 |
| AC-3.2 | R-3 | TASK-AS-09 | C-API 单测 | styled_string_controller_accessor.cpp |
| AC-3.3 | R-4 | TASK-AS-09 | 单测 | styled_string_ani_modifier.h @since 2025 |
| AC-3.4 | R-4 | TASK-AS-09 | 单测 | styled_string_module.h |

## 觅则定义

| 觅则ID | 类型 | 触发条件 | 预期行为 | 边界/约束 | 关联AC |
|--------|------|----------|----------|-----------|-------|
| R-1 | 行为 | OH_ArkUI_StyledString_*（Create/Push/Add/Pop/CreateTypography/Destroy/AddPlaceholder） | 构建/释放排版（@since 12） | — | AC-1.1..1.3 |
| R-2 | 行为 | ArkUI_TextLayoutManager（GetLineCount/GetRectsForRange/GetGlyphPositionAtCoordinate/GetLineMetrics @since 22；char/glyph 互转 @since 24） | 查询布局 | — | AC-2.1,2.2 |
| R-3 | 行为 | GetStyledStringAccessor/ControllerAccessor | 对象模型 accessor 操作（Ark_StyleOptions/SpanStyle/StyledStringKey） | — | AC-3.1,3.2 |
| R-4 | 行为 | ANI modifier（@since 2025）/arkoala module | 静态 ArkTS 桥接 | — | AC-3.3,3.4 |

## 验证映射

| 编号 | 对应规格项 | 验证方式 | 验证重点 |
|------|-----------|----------|----------|
| VM-1 | R-1 drawing C-API | C-API 单测 | Create/Push/Add |
| VM-2 | R-2 LayoutManager | C-API 单测 | @since 22/24 |
| VM-3 | R-3/R-4 accessor/ANI | C-API 单测 | 对象模型 + ANI |

## API 变更分析

### 新增 API

| API 名称 | 开放范围 | 入参概要 | 返回值 | 错误码范围 | 功能描述 | 关联 AC |
|----------|----------|----------|--------|-----------|----------|---------|
| `OH_ArkUI_StyledString_Create`/`Destroy`/`PushTextStyle`/`AddText`/`PopTextStyle`/`CreateTypography`/`AddPlaceholder` | System | TypographyStyle,FontCollection,... | handle/void | 无 | drawing-typography @since 12 | AC-1.1..1.3 |
| `ArkUI_TextLayoutManager_Dispose`/`GetLineCount`/`GetRectsForRange`/`GetGlyphPositionAtCoordinate`/`GetLineMetrics` | System | handle | count/rect/pos/metrics | 无 | LayoutManager @since 22 | AC-2.1 |
| `ArkUI_TextLayoutManager_GetCharacterPositionAtCoordinate`/`GetGlyphRangeForCharacterRange`/`GetCharacterRangeForGlyphRange` | System | handle,... | pos/range | 无 | char/glyph 互转 @since 24 | AC-2.2 |
| `GetStyledStringAccessor`/`GetStyledStringControllerAccessor`/`RichEditorStyledStringControllerAccessor::GetStyledStringImpl` | System | — | accessor | 无 | 对象模型 accessor | AC-3.1,3.2 |
| ANI `GetStyledStringAniModifier()` | System | — | modifier | 无 | ANI @since 2025 | AC-3.3 |
| arkoala `styled_string_module` | System | — | module | 无 | 静态 ArkTS | AC-3.4 |

## 接口规格

### 接口定义

**OH_ArkUI_StyledString_Create**

| 属性 | 值 |
|------|-----|
| 函数签名 | `ArkUI_StyledString* OH_ArkUI_StyledString_Create(OH_Drawing_TypographyStyle*, OH_Drawing_FontCollection*)` |
| 返回值 | `ArkUI_StyledString*` |
| 开放范围 | System |
| 错误码 | N/A |
| 关联 AC | AC-1.1 |

**参数约束**

| 参数 | 类型 | 必填 | 默认值 | 约束条件 |
|------|------|------|--------|---------|
| TypographyStyle | OH_Drawing_TypographyStyle* | 是 | — | — |
| FontCollection | OH_Drawing_FontCollection* | 是 | — | — |

**行为场景**

| # | 触发条件 | 预期行为 | 关联 AC |
|---|----------|----------|---------|
| 1 | Create | 创建 handle | AC-1.1 |
| 2 | LayoutManager @since 22 | 查询 | AC-2.1 |
| 3 | accessor | 对象模型 | AC-3.1 |

## 兼容性声明
- **已有 API 行为变更:** 否
- **最低支持版本:** drawing-typography C-API @since 12；TextLayoutManager @since 22；char/glyph 互转 @since 24；ANI @since 2025
- **API 版本号策略:** 全量 @since 标注；双 C-API（drawing vs 对象模型）并存记风险

## 架构约束
| 关键约束 | 约束说明 | 影响 AC |
|----------|----------|---------|
| 双 C-API 并存 | drawing-typography 与对象模型 accessor | 全部 |
| ANI modifier | 静态 ArkTS 桥接 | AC-3.3 |

## 非功能性需求
| 类型 | 指标/阈值 | 验证方式 | 证据 |
|------|-----------|----------|------|
| 可测试性 | C-API 全覆盖 | C-API 单测 | native_styled_string_test.cpp / styled_string_accessor_test.cpp |

## 多设备适配声明
无差异。

## 全局特性影响
| 特性 | 适用？ | 结论 | 关联场景 |
|------|--------|------|----------|
| 无障碍 | 是 | LayoutManager 支持无障碍查询 | AC-2.1 |

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
    query: "属性字符串 C-API drawing-typography / 对象模型 accessor / ANI modifier"
```
**关键文档：** `interfaces/native/native_styled_string.h`、`interface/sdk-js/api/@internal/component/ets/styled_string.d.ts`
