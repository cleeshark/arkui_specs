# 特性规格

## 概述

| 属性 | 值 |
|------|-----|
| 特性名称 | 字体样式快捷键 (RichEditor 专属) |
| 特性编号 | Func-04-14-02-Feat-06 |
| 所属 Epic | 无 |
| 优先级 | P2 |
| 目标版本 | API 10+ |
| SIG 归属 | ArkUI SIG |
| 状态 | Baselined |
| 复杂度 | 标准 |

## 本次变更范围（Delta）
全新特性补录（lineage: new），无 Delta。

## 输入文档
- 设计文档：`02-text-shortcuts/design.md`
- 源码定位：`rich_editor_pattern.cpp`(HandleSelectFontStyle/SetSelectSpanStyle/UpdateSelectSpanStyle/UpdateSelectStyledStringStyle)

## 用户故事

### US-1: 粗体/斜体/下划线快捷键
作为开发者，我希望在 RichEditor 经 Ctrl+B/I/U 切换字体样式。

| AC编号 | 验收标准 | 类型 |
|--------|----------|------|
| AC-1.1 | WHEN Ctrl+B THEN HandleSelectFontStyle(KEY_B) 切换粗体 | 正常 |
| AC-1.2 | WHEN Ctrl+I THEN HandleSelectFontStyle(KEY_I) 切换斜体 | 正常 |
| AC-1.3 | WHEN Ctrl+U THEN HandleSelectFontStyle(KEY_U) 切换下划线 | 正常 |
| AC-1.4 | WHEN 有选区 THEN 对选区 span 应用样式 | 正常 |
| AC-1.5 | WHEN 无选区 THEN 切换后续输入样式 | 边界 |
| AC-1.6 | WHEN TextField THEN Ctrl+B/I/U no-op | 边界 |
| AC-1.7 | WHEN Mac Cmd+B/I/U THEN 镜像 | 正常 |

## 验收追溯

| AC | 关联规则 | 关联 Task | 验证方式 | 证据 |
|----|----------|-----------|----------|------|
| AC-1.1 | R-1 | TASK-TS-06 | 单测 | rich_editor_pattern.cpp:13281 |
| AC-1.2 | R-1 | TASK-TS-06 | 单测 | — |
| AC-1.3 | R-1 | TASK-TS-06 | 单测 | — |
| AC-1.4 | R-2 | TASK-TS-06 | 单测 | rich_editor_pattern.cpp:2979 |
| AC-1.5 | R-3 | TASK-TS-06 | 单测 | — |
| AC-1.6 | R-4 | TASK-TS-06 | 单测 | TextField no-op |
| AC-1.7 | R-1 | TASK-TS-06 | 单测 | text_input_client.cpp:39 |

## 规则定义

| 规则ID | 类型 | 触发条件 | 预期行为 | 边界/约束 | 关联AC |
|--------|------|----------|----------|-----------|-------|
| R-1 | 行为 | Ctrl+B/I/U | HandleSelectFontStyle(KEY_B/I/U) 切换；Mac Cmd 镜像 | RichEditor only | AC-1.1..1.3,1.7 |
| R-2 | 行为 | 有选区 | SetSelectSpanStyle/UpdateSelectSpanStyle/UpdateSelectStyledStringStyle 对选区应用 | — | AC-1.4 |
| R-3 | 边界 | 无选区 | 切换后续输入样式 | — | AC-1.5 |
| R-4 | 边界 | TextField | no-op | — | AC-1.6 |

## 验证映射

| 编号 | 对应规格项 | 验证方式 | 验证重点 |
|------|-----------|----------|----------|
| VM-1 | R-1 三键 | 单测 | B/I/U 切换 |
| VM-2 | R-2/R-3 选区/无选区 | 单测 | span 应用 |
| VM-3 | R-4 TextField no-op | 单测 | 不响应 |

## API 变更分析
无公共 API。内部：`HandleSelectFontStyle(KeyCode)`、`SetSelectSpanStyle`、`UpdateSelectSpanStyle`、`UpdateSelectStyledStringStyle`。

## 接口规格

### 接口定义

**HandleSelectFontStyle(keyCode)**

| 属性 | 值 |
|------|-----|
| 函数签名 | `void HandleSelectFontStyle(KeyCode keyCode)` |
| 返回值 | `void` |
| 开放范围 | InnerApi |
| 错误码 | N/A |
| 关联 AC | AC-1.1 |

**参数约束**

| 参数 | 类型 | 必填 | 默认值 | 约束条件 |
|------|------|------|--------|---------|
| keyCode | KeyCode | 是 | — | KEY_B/KEY_I/KEY_U |

**行为场景**

| # | 触发条件 | 预期行为 | 关联 AC |
|---|----------|----------|---------|
| 1 | Ctrl+B 有选区 | 选区加粗 | AC-1.1,1.4 |
| 2 | Ctrl+B 无选区 | 后续加粗 | AC-1.5 |
| 3 | TextField Ctrl+B | no-op | AC-1.6 |

## 兼容性声明
- **已有 API 行为变更:** 否
- **最低支持版本:** API 10+（RichEditor）
- **API 版本号策略:** 框架内部无 @since；Mac Cmd 镜像标注

## 架构约束
| 关键约束 | 约束说明 | 影响 AC |
|----------|----------|---------|
| RichEditor only | TextField no-op | AC-1.6 |
| span/styled-string 更新 | SetSelectSpanStyle/UpdateSelectStyledStringStyle | AC-1.4 |

## 非功能性需求
| 类型 | 指标/阈值 | 验证方式 | 证据 |
|------|-----------|----------|------|
| 可测试性 | 三键可单测 | 单测 | rich_editor_pattern.cpp:13281 |

## 多设备适配声明
| 设备类型 | 行为差异 | 规格/约束 | 验证方式 | 证据 |
|----------|----------|-----------|----------|------|
| Mac | Cmd+B/I/U 镜像 | 单测 | — | text_input_client.cpp:39 |

## 全局特性影响
| 特性 | 适用？ | 结论 | 关联场景 |
|------|--------|------|----------|
| 无障碍 | 是 | 键盘样式切换支持 | 全部 |

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
    query: "RichEditor HandleSelectFontStyle Ctrl+B/I/U"
```
**关键文档：** `frameworks/core/components_ng/pattern/rich_editor/rich_editor_pattern.cpp`
