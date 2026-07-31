# 特性规格

## 概述

| 属性 | 值 |
|------|-----|
| 特性名称 | 输入框避让显示 |
| 特性编号 | Func-04-14-04-Feat-02 |
| 所属 Epic | 无 |
| 优先级 | P1 |
| 目标版本 | API 11+（UIContext.setKeyboardAvoidMode @since 11） |
| SIG 归属 | ArkUI SIG |
| 状态 | Baselined |
| 复杂度 | 复杂 |

## 本次变更范围（Delta）
重定范围补录。本 Feat 覆盖输入框侧键盘避让显示（caret-anchored 与自定义键盘 supportAvoidance）。

## 输入文档
- 设计文档：`04-input-method-interaction/design.md`
- 源码定位：`frameworks/core/components/common/layout/constants.h`(KeyBoardAvoidMode)、`frameworks/core/components_ng/manager/safe_area/safe_area_manager.h`、`text_field_pattern.cpp`(TriggerAvoidOnCaretChange/SetCustomKeyboardOption)、`rich_editor_pattern.cpp`(ForceTriggerAvoidOnCaretChange)

## 用户故事

### US-1: 避让模式
作为开发者，我希望经 KeyBoardAvoidMode 选择避让方式。

| AC编号 | 验收标准 | 类型 |
|--------|----------|------|
| AC-1.1 | WHEN KeyBoardAvoidMode=OFFSET THEN 页面上偏移 | 正常 |
| AC-1.2 | WHEN =RESIZE THEN 页面 resize | 正常 |
| AC-1.3 | WHEN =OFFSET_WITH_CARET/RESIZE_WITH_CARET THEN caret 锚定避让 | 正常 |
| AC-1.4 | WHEN =NONE THEN GetKeyboardInset 返回空（不避让） | 边界 |
| AC-1.5 | WHEN 默认 THEN OFFSET | 边界 |

### US-2: 输入框 caret 锚定避让
作为开发者，我希望光标移动时触发 caret 锚定避让。

| AC编号 | 验收标准 | 类型 |
|--------|----------|------|
| AC-2.1 | WHEN caret 移动 THEN TextFieldPattern::TriggerAvoidOnCaretChange→textFieldManager→TriggerAvoidOnCaretChange | 正常 |
| AC-2.2 | WHEN RichEditor caret 变化 THEN ForceTriggerAvoidOnCaretChange | 正常 |

### US-3: 自定义键盘避让
作为开发者，我希望经 customKeyboard KeyboardOptions.supportAvoidance 控制自定义键盘避让。

| AC编号 | 验收标准 | 类型 |
|--------|----------|------|
| AC-3.1 | WHEN SetCustomKeyboardOption(supportAvoidance=true) THEN keyboardAvoidance_=true | 正常 |
| AC-3.2 | WHEN supportAvoidance=false THEN 自定义键盘不避让 | 边界 |

### US-4: 公共避让 API
作为开发者，我希望经 UIContext/Window.setKeyboardAvoidMode 设置避让模式。

| AC编号 | 验收标准 | 类型 |
|--------|----------|------|
| AC-4.1 | WHEN setKeyboardAvoidMode(mode) THEN 设置 KeyBoardAvoidMode（@since 11） | 正常 |
| AC-4.2 | WHEN C-API setKeyboardAvoidMode/resetKeyboardAvoidMode THEN arkoala/ani/cjui 镜像 | 正常 |

## 验收追溯

| AC | 关联规则 | 关联 Task | 验证方式 | 证据 |
|----|----------|-----------|----------|------|
| AC-1.1 | R-1 | TASK-KC-02 | 单测 | constants.h:891 |
| AC-1.4 | R-2 | TASK-KC-02 | 单测 | safe_area_manager.h:188/420 |
| AC-2.1 | R-3 | TASK-KC-02 | 单测 | text_field_pattern.cpp:11106/11138 |
| AC-2.2 | R-3 | TASK-KC-02 | 单测 | rich_editor_pattern.cpp ForceTriggerAvoidOnCaretChange |
| AC-3.1 | R-4 | TASK-KC-02 | 单测 | text_field_pattern.cpp:6210 |
| AC-4.1 | R-5 | TASK-KC-02 | 单测 | UIContext.d.ts/arkoala_api.h:6869 |

## 规则定义

| 规则ID | 类型 | 触发条件 | 预期行为 | 边界/约束 | 关联AC |
|--------|------|----------|----------|-----------|-------|
| R-1 | 行为 | KeyBoardAvoidMode | OFFSET/RESIZE/*_WITH_CARET/NONE 决定避让 | 默认 OFFSET | AC-1.1..1.3,1.5 |
| R-2 | 边界 | =NONE | GetKeyboardInset 返回空 | — | AC-1.4 |
| R-3 | 行为 | caret 变化 | TriggerAvoidOnCaretChange/ForceTriggerAvoidOnCaretChange | *_WITH_CARET | AC-2.1,2.2 |
| R-4 | 行为 | 自定义键盘 supportAvoidance | SetCustomKeyboardOption→keyboardAvoidance_ | — | AC-3.1,3.2 |
| R-5 | 行为 | setKeyboardAvoidMode | 设置模式（@since 11） | C-API 镜像 | AC-4.1,4.2 |

## 验证映射

| 编号 | 对应规格项 | 验证方式 | 验证重点 |
|------|-----------|----------|----------|
| VM-1 | R-1/R-2 模式 | 单测 | 5 模式 + NONE |
| VM-2 | R-3 caret 锚定 | 单测 | TriggerAvoidOnCaretChange |
| VM-3 | R-4/R-5 自定义/公共 API | 单测 | supportAvoidance/setKeyboardAvoidMode |

## API 变更分析
公共 API：`UIContext/Window.setKeyboardAvoidMode`+`KeyboardAvoidMode`（@since 11，外部 SDK 仓；C-API arkoala_api.h:6869/ani/cjui 镜像）、`customKeyboard KeyboardOptions.supportAvoidance`。内部：KeyBoardAvoidMode、SafeAreaManager::UpdateKeyboardSafeArea/GetKeyboardInset、TriggerAvoidOnCaretChange、SetCustomKeyboardOption。边界：避让机制（inset 同步/Page offset/resize/RESIZE+expand 例外/OverlayManager）归 04-02-01 Feat-05。

## 接口规格

### 接口定义

**setKeyboardAvoidMode(mode)**

| 属性 | 值 |
|------|-----|
| 函数签名 | `setKeyboardAvoidMode(mode: KeyboardAvoidMode): void` |
| 返回值 | `void` |
| 开放范围 | Public |
| 错误码 | N/A |
| 关联 AC | AC-4.1 |

**参数约束**

| 参数 | 类型 | 必填 | 默认值 | 约束条件 |
|------|------|------|--------|---------|
| mode | KeyboardAvoidMode | 是 | — | OFFSET/RESIZE/*_WITH_CARET/NONE |

**行为场景**

| # | 触发条件 | 预期行为 | 关联 AC |
|---|----------|----------|---------|
| 1 | OFFSET_WITH_CARET | caret 锚定 | AC-1.3 |
| 2 | NONE | 不避让 | AC-1.4 |

## 兼容性声明
- **已有 API 行为变更:** 否
- **最低支持版本:** setKeyboardAvoidMode @since 11；customKeyboard supportAvoidance @since 10/23
- **API 版本号策略:** 公共 API 全量 @since 标注

## 架构约束
| 关键约束 | 约束说明 | 影响 AC |
|----------|----------|---------|
| 机制归 04-02-01 Feat-05 | 本域只覆盖输入框侧响应 | 全部 |
| *_WITH_CARET 输入框专属 | caret 锚定 | AC-1.3 |

## 非功能性需求
| 类型 | 指标/阈值 | 验证方式 | 证据 |
|------|-----------|----------|------|
| 性能 | caret 避让无卡顿 | 帧率测试 | TriggerAvoidOnCaretChange |

## 多设备适配声明
| 设备类型 | 行为差异 | 规格/约束 | 验证方式 | 证据 |
|----------|----------|-----------|----------|------|
| 折叠屏 | 屏幕高度变化影响避让 | 单测 | — | — |

## 全局特性影响
| 特性 | 适用？ | 结论 | 关联场景 |
|------|--------|------|----------|
| 多窗口 | 是 | 窗口避让独立 | AC-1.1 |

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
    query: "KeyBoardAvoidMode/TriggerAvoidOnCaretChange/自定义键盘 supportAvoidance"
```
**关键文档：** `frameworks/core/components/common/layout/constants.h`、`frameworks/core/components_ng/manager/safe_area/safe_area_manager.h`
