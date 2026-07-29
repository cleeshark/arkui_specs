# 特性规格

> Func-05-09-02-Feat-03 属性字符串模式管理：固化 `RichEditorStyledStringController` 四个核心 API（setStyledString/getStyledString/onContentChanged/setStyledPlaceholder）的行为规格，重点记录 setStyledString 不触发 onContentChanged 的路径差异及占位符优先级。

## 概述

| 属性 | 值 |
|------|-----|
| 特性名称 | 属性字符串模式管理 (Styled String Mode Management) |
| 特性编号 | Func-05-09-02-Feat-03 |
| 所属 Epic | 无（已有能力补录） |
| 优先级 | P1 |
| 目标版本 | API 12+（前三个 API），API 24+（setStyledPlaceholder） |
| SIG 归属 | ArkUI SIG |
| 状态 | Baselined |
| 复杂度 | 标准 |

## 本次变更范围（Delta）

| 类型 | 内容 | 说明 |
|------|------|------|
| MODIFIED | 补齐 `setStyledString` 接口行为规格 | 固化 maxLength 截断、全量替换语义及不触发 onContentChanged 的关键行为 |
| MODIFIED | 补齐 `getStyledString` 接口行为规格 | 固化返回内容副本（非内部引用）的语义 |
| MODIFIED | 补齐 `onContentChanged` 接口行为规格 | 固化 onWillChange/onDidChange 双回调注册及"仅后台程序变更触发"的区分 |
| MODIFIED | 补齐 `setStyledPlaceholder` 接口行为规格 | 固化 API 24+ 约束、优先级高于普通占位符 |

## 输入文档

- Design: `05-ui-components/09-text-components/02-rich-editor/design.md`（已创建）
- Feat-01: `Feat-01-component-init-dual-mode-spec.md`（Baselined）
- Feat-02: `Feat-02-span-content-management-spec.md`（Baselined）

---

## 用户故事

### US-1: 设置属性字符串内容

**作为** 应用开发者, **我想要** 通过 `setStyledString` 一次性替换 RichEditor 全部属性字符串内容, **以便** 以编程方式批量更新富文本。

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-1.1 | WHEN 调用 `setStyledString(value)` THEN 委托 `RichEditorPattern::SetStyledString` 全量替换 `styledString_`（`rich_editor_pattern.cpp:232-258`） | 正常 |
| AC-1.2 | WHEN `GetTextContentLength() > maxLength` THEN 直接返回不替换（`rich_editor_pattern.cpp:237-240`） | 边界 |
| AC-1.3 | WHEN 传入内容超 maxLength THEN `CalculateTruncationLength` 截断，截断为 0 则返回（`rich_editor_pattern.cpp:243-249`） | 边界 |
| AC-1.4 | WHEN 处于预览文本输入态 THEN 先 `NotifyExitTextPreview(true)` 再替换（`rich_editor_pattern.cpp:251`） | 正常 |
| AC-1.5 | WHEN 替换完成 THEN CustomSpan 重添加、光标移至末尾、标记 `PROPERTY_UPDATE_MEASURE`（`rich_editor_pattern.cpp:257-271`） | 正常 |
| AC-1.6 | WHEN setStyledString 完成 THEN 调用 `ReportAfterContentChangeEvent()` 但不调用 `AfterStyledStringChange`，不触发 onContentChanged（`rich_editor_pattern.cpp:274`） | 行为 |

### US-2: 获取当前属性字符串

**作为** 应用开发者, **我想要** 通过 `getStyledString()` 获取当前属性字符串内容, **以便** 读取富文本完整内容及样式。

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-2.1 | WHEN 调用 `getStyledString()` THEN 通过 `GetSubSpanString(0, length)` 创建内容副本返回（`rich_editor_styled_string_controller.cpp:31-42`） | 正常 |
| AC-2.2 | WHEN pattern 或 styledString 为空 THEN 返回空 `MutableSpanString(u"")`（`rich_editor_styled_string_controller.cpp:34-37`） | 异常 |
| AC-2.3 | WHEN 获取内容 THEN 返回值与内部 `styledString_` 不共享引用（`rich_editor_styled_string_controller.cpp:38-41`） | 行为 |

### US-3: 注册内容变更监听器

**作为** 应用开发者, **我想要** 通过 `onContentChanged(listener)` 注册内容变更监听, **以便** 在后台程序（IME 输入、编程式增删）变更内容时获得回调。

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-3.1 | WHEN 调用 `onContentChanged(listener)` THEN 提取 onWillChange/onDidChange 注册到 EventHub（`js_richeditor.cpp:2303-2309`） | 正常 |
| AC-3.2 | WHEN 后台程序导致内容变更 THEN 变更前触发 `FireOnStyledStringWillChange`、变更后触发 `FireOnStyledStringDidChange`（`rich_editor_pattern.cpp:596,612`） | 正常 |
| AC-3.3 | WHEN 调用 `setStyledString` 替换内容 THEN 不触发 `AfterStyledStringChange`，不触发 onContentChanged（`rich_editor_pattern.cpp:274` 对比 `599-616`） | 行为 |
| AC-3.4 | WHEN listener 非对象 THEN 静默返回不注册（`js_richeditor.cpp:2306`） | 异常 |

### US-4: 设置属性占位符

**作为** 应用开发者, **我想要** 通过 `setStyledPlaceholder` 设置带样式占位符, **以便** 内容为空时显示带样式提示文本（API 24+）。

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-4.1 | WHEN 调用 `setStyledPlaceholder(value)` THEN 存入 `styledPlaceholder_` 并标记脏节点（`rich_editor_pattern.cpp:2652-2660`） | 正常 |
| AC-4.2 | WHEN `styledPlaceholder_` 已设置且 `spans_` 为空 THEN 走 `SetStyledPlaceholder` 路径，优先级高于普通占位符（`rich_editor_pattern.cpp:11842`） | 行为 |
| AC-4.3 | WHEN `styledPlaceholder_` 未设置 THEN 走 `SetStringPlaceholder` 普通占位符路径（`rich_editor_pattern.cpp:11842`） | 边界 |
| AC-4.4 | WHEN `spans_` 非空 THEN 不显示占位符（`rich_editor_pattern.cpp:11835-11840`） | 边界 |
| AC-4.5 | WHEN API < 24 THEN `setStyledPlaceholder` 不可用 | 边界 |

## 验收追溯

| AC | 关联规则 | 验证方式 | 证据 |
|----|---------|---------|------|
| AC-1.1 ~ AC-1.6 | R-1, R-2, R-3 | UT + 源码审查 | `rich_editor_pattern.cpp:232-275` |
| AC-2.1 ~ AC-2.3 | R-4, R-5 | UT + 源码审查 | `rich_editor_styled_string_controller.cpp:31-42` |
| AC-3.1 ~ AC-3.4 | R-6, R-7, R-8 | UT + 源码审查 | `js_richeditor.cpp:2303-2309`, `rich_editor_pattern.cpp:596,612` |
| AC-4.1 ~ AC-4.5 | R-9, R-10, R-11 | UT + 源码审查 | `rich_editor_pattern.cpp:2652-2660, 11842` |

## 规则定义

| 规则ID | 类型 | 触发条件 | 预期行为 | 边界/约束 | 关联AC |
|--------|------|---------|---------|----------|--------|
| R-1 | 行为 | `setStyledString(value)` value 非空且 ≤ maxLength | 全量替换 styledString_，光标移末尾 | maxLength 默认 INT_MAX（`rich_editor_pattern.cpp:237,243`） | AC-1.1, AC-1.5 |
| R-2 | 边界 | `GetTextContentLength() > maxLength` | 直接返回不替换 | `maxLength_.value_or(INT_MAX)`（`rich_editor_pattern.cpp:237`） | AC-1.2 |
| R-3 | 边界 | value 长度 > maxLength 且当前 ≤ maxLength | `CalculateTruncationLength` 截断，subLength=0 则返回 | `rich_editor_pattern.cpp:244-249` | AC-1.3 |
| R-4 | 行为 | `getStyledString()` styledString_ 非空 | `GetSubSpanString(0, length)` 创建副本返回 | 返回值不共享内部引用（`rich_editor_styled_string_controller.cpp:38-41`） | AC-2.1, AC-2.3 |
| R-5 | 异常 | `getStyledString()` pattern/styledString_ 为空 | 返回空 `MutableSpanString(u"")` | `CHECK_NULL_RETURN` 保护（`rich_editor_styled_string_controller.cpp:34-37`） | AC-2.2 |
| R-6 | 行为 | `onContentChanged(listener)` listener 为对象 | onWillChange/onDidChange 分别注册到 EventHub | listener 需为 Object（`js_richeditor.cpp:2306`） | AC-3.1 |
| R-7 | 行为 | 后台程序变更 styledString_ | 变更前 `FireOnStyledStringWillChange`，变更后 `FireOnStyledStringDidChange` | 携带 StyledStringChangeValue（`rich_editor_pattern.cpp:596,612`） | AC-3.2 |
| R-8 | 行为 | `setStyledString` 替换内容 | 仅 `ReportAfterContentChangeEvent`，不触发 `AfterStyledStringChange` | 区别于 R-7（`:274` 对比 `599-616`） | AC-3.3 |
| R-9 | 行为 | `setStyledPlaceholder(value)` | `styledPlaceholder_ = value->GetSubSpanString(0, len)`，标记脏节点 | value 为 null 时 CHECK_NULL_VOID 返回（`rich_editor_pattern.cpp:2654-2659`） | AC-4.1 |
| R-10 | 行为 | `spans_` 为空且 `styledPlaceholder_` 已设置 | 走 `SetStyledPlaceholder`，优先于 `SetStringPlaceholder` | 三元分支（`rich_editor_pattern.cpp:11842`） | AC-4.2, AC-4.3 |
| R-11 | 边界 | API < 24 | `setStyledPlaceholder` 不可用 | API 24+ 引入 | AC-4.5 |

## 验证映射

| 编号 | 对应规格项 | 验证方式 | 验证重点 |
|------|----------|---------|---------|
| VM-1 | AC-1.1 ~ AC-1.6 | UT + 源码审查 | 全量替换、maxLength 截断、不触发 onContentChanged |
| VM-2 | AC-2.1 ~ AC-2.3 | UT + 源码审查 | 返回副本、空值降级 |
| VM-3 | AC-3.1 ~ AC-3.4 | UT + 源码审查 | 双回调注册、setStyledString 不触发 |
| VM-4 | AC-4.1 ~ AC-4.5 | UT + 源码审查 | 占位符优先级、API 版本约束 |

## API 变更分析

### 新增 API

N/A，本特性为已有能力补录，无新增 API。

### 变更/废弃 API

| API 名称 | 变更类型 | 影响场景 | 迁移指引 | 关联 AC |
|----------|---------|---------|---------|---------|
| `setStyledString` | 变更（补录规格） | 属性字符串内容设置 | 无破坏性变更 | AC-1.x |
| `getStyledString` | 变更（补录规格） | 属性字符串内容读取 | 无破坏性变更 | AC-2.x |
| `onContentChanged` | 变更（补录规格） | 内容变更监听注册 | 无破坏性变更 | AC-3.x |
| `setStyledPlaceholder` | 变更（补录规格） | 属性占位符设置 | 无破坏性变更，API 24+ | AC-4.x |

## 接口规格

### 接口定义

| API | 函数签名 | 返回值 | 开放范围 | 关联 AC |
|-----|---------|--------|---------|---------|
| setStyledString | `void setStyledString(styledString: StyledString)` | `void` | Public | AC-1.1 ~ AC-1.6 |
| getStyledString | `MutableStyledString getStyledString()` | `MutableStyledString`（内容副本） | Public | AC-2.1 ~ AC-2.3 |
| onContentChanged | `void onContentChanged(listener: StyledStringChangedListener)` | `void` | Public | AC-3.1 ~ AC-3.4 |
| setStyledPlaceholder | `void setStyledPlaceholder(styledString: StyledString)` | `void` | Public（API 24+） | AC-4.1 ~ AC-4.5 |

### 参数约束

| API | 参数 | 类型 | 必填 | 约束条件 |
|-----|------|------|------|---------|
| setStyledString | styledString | StyledString | 是 | 不可为 null；超 maxLength 时截断 |
| getStyledString | 无 | — | — | 无入参 |
| onContentChanged | listener | StyledStringChangedListener | 是 | 需为对象，含 onWillChange/onDidChange |
| setStyledPlaceholder | styledString | StyledString | 是 | 不可为 null；API 24+ |

### 行为场景

> 详细行为场景见"用户故事 → AC 表"与"规则定义"，此处仅列关键行为索引。

| API | 关键行为 | 关联 AC |
|-----|---------|---------|
| setStyledString | 全量替换、maxLength 截断、不触发 onContentChanged（走 ReportAfterContentChangeEvent 而非 AfterStyledStringChange） | AC-1.1 ~ AC-1.6 |
| getStyledString | 返回副本非内部引用、空值降级返回空 MutableSpanString | AC-2.1 ~ AC-2.3 |
| onContentChanged | 双回调注册、仅后台程序变更触发、setStyledString 不触发 | AC-3.1 ~ AC-3.4 |
| setStyledPlaceholder | styledPlaceholder_ 优先于普通占位符、API 24+ 约束 | AC-4.1 ~ AC-4.5 |

## 兼容性声明

- **已有 API 行为变更:** 否。四个 API 行为无变更，仅补录规格。
- **配置文件格式变更:** 否。
- **数据存储格式变更:** 否。
- **最低支持版本:** API 12+（前三个 API），API 24+（`setStyledPlaceholder`）。
- **API 版本号策略:** `setStyledPlaceholder` 标注 `@since 24`。

## 架构约束

| 关键约束 | 约束说明 | 影响 AC |
|---------|---------|--------|
| 模式标志 | `isSpanStringMode_`（`text_pattern.h:669`）构造时 `SetSpanStringMode` 设置（`rich_editor_pattern.cpp:194`） | AC-1.1, AC-2.1 |
| SpanWatcher | Pattern 继承 SpanWatcher（`rich_editor_pattern.h:252`），`CreateStyledString` 中注册（`rich_editor_pattern.cpp:199,229`） | AC-3.2 |
| 事件分流 | setStyledString 走 `ReportAfterContentChangeEvent`（`:274`），后台变更走 `Before/AfterStyledStringChange`（`:580-616`） | AC-1.6, AC-3.3 |
| 占位符优先级 | `styledPlaceholder_` 非空优先 `SetStyledPlaceholder`（`rich_editor_pattern.cpp:11842`） | AC-4.2, AC-4.3 |
| maxLength | setStyledString 受 `maxLength_.value_or(INT_MAX)` 约束（`:237,243`） | AC-1.2, AC-1.3 |

## 非功能性需求

| 类型 | 指标/阈值 | 证据 |
|------|----------|------|
| 性能 | setStyledString 触发一次 PROPERTY_UPDATE_MEASURE | `rich_editor_pattern.cpp:271` |
| 内存 | getStyledString 返回副本不影响内部引用 | `rich_editor_styled_string_controller.cpp:38-41` |
| 可测试性 | `IsStyledStringModeEnabled()` 可查模式状态 | `rich_editor_pattern.cpp:14666-14669` |
| 自动化维测 | SetStyledString 含 TAG_LOGI 日志 | `rich_editor_pattern.cpp:235-236` |

## 多设备适配声明

| 设备类型 | 行为差异 | 验证方式 |
|---------|---------|---------|
| 手机/平板/折叠屏 | 无差异 | UT |

## 全局特性影响

| 特性 | 适用？ | 结论 | 关联场景 |
|------|--------|------|---------|
| 无障碍 | 是 | 内容变更通过 ReportAfterContentChangeEvent 上报 | AC-1.6 |
| 深色模式 | 是 | setStyledString 后调用 OnColorConfigurationUpdate | AC-1.5 |
| 版本升级 | 是 | setStyledPlaceholder 仅 API 24+ | AC-4.5 |

## 行为场景（可选，Gherkin）

> 标准（L1）复杂度，行为场景由"接口规格 → 行为场景"表覆盖，不使用 Gherkin。

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
  - repo: "OpenHarmony/ace_engine"
    query: "RichEditorPattern SpanWatcher 实现与 styledString_ 变更通知机制"
  - repo: "OpenHarmony/ace_engine"
    query: "setStyledString 不触发 onContentChanged 的路径差异"
  - repo: "OpenHarmony/ace_engine"
    query: "styledPlaceholder_ 与普通 placeholder 优先级分支实现"
```

**关键文档:** Design `05-ui-components/09-text-components/02-rich-editor/design.md`；Feat-01/Feat-02 同目录。
