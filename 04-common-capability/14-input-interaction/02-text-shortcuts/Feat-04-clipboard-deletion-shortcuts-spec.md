# 特性规格

## 概述

| 属性 | 值 |
|------|-----|
| 特性名称 | 剪贴板与删除快捷键 |
| 特性编号 | Func-04-14-02-Feat-04 |
| 所属 Epic | 无 |
| 优先级 | P1 |
| 目标版本 | API 8+（含 PREVIEW 反转/Mac 分支） |
| SIG 归属 | ArkUI SIG |
| 状态 | Baselined |
| 复杂度 | 标准 |

## 本次变更范围（Delta）
全新特性补录（lineage: new），无 Delta。

## 输入文档
- 设计文档：`02-text-shortcuts/design.md`
- 源码定位：`text_field_pattern.cpp`(HandleOnCopy/Paste/Cut/Delete/DeleteComb)、`rich_editor_pattern.cpp`(同+preventDefault)、`text_input_client.cpp`(加速表)

## 用户故事

### US-1: 剪贴板快捷键
作为开发者，我希望经 Ctrl+C/X/V 等操作剪贴板。

| AC编号 | 验收标准 | 类型 |
|--------|----------|------|
| AC-1.1 | WHEN Ctrl+C/Ctrl+Insert/Ctrl+Numpad0 THEN HandleOnCopy(true) | 正常 |
| AC-1.2 | WHEN Ctrl+X THEN HandleOnCut | 正常 |
| AC-1.3 | WHEN Ctrl+V/Shift+Insert/Shift+Numpad0/PASTE THEN HandleOnPaste | 正常 |
| AC-1.4 | WHEN IsInPasswordMode THEN 禁止 copy/cut | 边界 |
| AC-1.5 | WHEN copyOption=None THEN 禁止 copy/cut | 边界 |
| AC-1.6 | WHEN RichEditor onPaste preventDefault THEN 不粘贴 | 正常 |

### US-2: 删除快捷键
作为开发者，我希望经 DEL/Backspace/Ctrl+Del 删除字符/词。

| AC编号 | 验收标准 | 类型 |
|--------|----------|------|
| AC-2.1 | WHEN DEL THEN HandleOnDelete(backward=true) | 正常 |
| AC-2.2 | WHEN FORWARD_DEL THEN HandleOnDelete(backward=false) | 正常 |
| AC-2.3 | WHEN Ctrl+DEL THEN HandleOnDeleteComb(backward) 删前词 | 正常 |
| AC-2.4 | WHEN Ctrl+FORWARD_DEL/Ctrl+NumpadDot THEN HandleOnDeleteComb(forward) 删后词 | 正常 |
| AC-2.5 | WHEN Ctrl+D THEN HandleOnDelete(true) | 正常 |
| AC-2.6 | WHEN Shift+Backspace THEN 走 DEL→HandleOnDelete(backward=true)（无特殊处理） | 边界 |

### US-3: 平台分支
作为开发者，我希望 PREVIEW 反转与 RTL 删词方向正确。

| AC编号 | 验收标准 | 类型 |
|--------|----------|------|
| AC-3.1 | WHEN PREVIEW 平台 THEN HandleOnDelete 前向/后向反转 | 正常 |
| AC-3.2 | WHEN RTL THEN 删词方向交换（LTR=左词/RTL=右词） | 正常 |

## 验收追溯

| AC | 关联规则 | 关联 Task | 验证方式 | 证据 |
|----|----------|-----------|----------|------|
| AC-1.1 | R-1 | TASK-TS-04 | 单测 | text_field_pattern.cpp:2361 |
| AC-1.3 | R-1 | TASK-TS-04 | 单测 | text_field_pattern.cpp:2473 |
| AC-1.4 | R-2 | TASK-TS-04 | 单测 | text_field_pattern.cpp IsInPasswordMode |
| AC-1.5 | R-2 | TASK-TS-04 | 单测 | copyOption 门控 |
| AC-1.6 | R-3 | TASK-TS-04 | 单测 | rich_editor_pattern.cpp:9679 |
| AC-2.1 | R-4 | TASK-TS-04 | 单测 | text_field_pattern.cpp:7788 |
| AC-2.3 | R-5 | TASK-TS-04 | 单测 | text_field_pattern.cpp:7805 |
| AC-2.6 | R-6 | TASK-TS-04 | 单测 | text_input_client.cpp DEL 路径 |
| AC-3.1 | R-7 | TASK-TS-04 | 单测 | text_field_pattern.cpp:7788 PREVIEW |
| AC-3.2 | R-7 | TASK-TS-04 | 单测 | DeleteBackwardWord RTL |

## 规则定义

| 规则ID | 类型 | 触发条件 | 预期行为 | 边界/约束 | 关联AC |
|--------|------|----------|----------|-----------|-------|
| R-1 | 行为 | Ctrl+C/X/V/Insert/PASTE | HandleOnCopy/Cut/Paste | Mac Cmd 镜像 | AC-1.1..1.3 |
| R-2 | 边界 | IsInPasswordMode/copyOption=None | 禁止 copy/cut | — | AC-1.4,1.5 |
| R-3 | 行为 | RichEditor onPaste preventDefault | 不粘贴 | — | AC-1.6 |
| R-4 | 行为 | DEL/FORWARD_DEL | HandleOnDelete(backward/forward) | — | AC-2.1,2.2 |
| R-5 | 行为 | Ctrl+DEL/FORWARD_DEL/NumpadDot | HandleOnDeleteComb 删词 | GetWordLength | AC-2.3,2.4 |
| R-6 | 边界 | Shift+Backspace | 走 DEL→HandleOnDelete(backward=true) 无特殊处理 | — | AC-2.6 |
| R-7 | 行为 | PREVIEW 反转 / RTL 删词方向交换 | 前后向反转；LTR=左词 RTL=右词 | 平台分支 | AC-3.1,3.2 |

## 验证映射

| 编号 | 对应规格项 | 验证方式 | 验证重点 |
|------|-----------|----------|----------|
| VM-1 | R-1 剪贴板 | 单测 | Ctrl+C/X/V |
| VM-2 | R-2 门控 | 单测 | password/copyOption |
| VM-3 | R-4/R-5 删除/删词 | 单测 | HandleOnDelete/DeleteComb |
| VM-4 | R-7 平台分支 | 单测 | PREVIEW/RTL |

## API 变更分析
无公共 API。内部：`HandleOnCopy/Cut/Paste`、`HandleOnDelete(backward)`、`HandleOnDeleteComb(backward)`、`DeleteBackwardWord/DeleteForwardWord`、`GetWordLength`。边界：onCopy/onWillCopy/onCut/onPaste/onWillDelete/onDidDelete 回调归 04-14-03。

## 接口规格

### 接口定义

**HandleOnDelete(backward)**

| 属性 | 值 |
|------|-----|
| 函数签名 | `void HandleOnDelete(bool backward)` |
| 返回值 | `void` |
| 开放范围 | InnerApi |
| 错误码 | N/A |
| 关联 AC | AC-2.1 |

**参数约束**

| 参数 | 类型 | 必填 | 默认值 | 约束条件 |
|------|------|------|--------|---------|
| backward | bool | 是 | — | true=后向删(Backspace) false=前向删 |

**行为场景**

| # | 触发条件 | 预期行为 | 关联 AC |
|---|----------|----------|---------|
| 1 | DEL | 后向删 | AC-2.1 |
| 2 | Ctrl+DEL | 删前词 | AC-2.3 |
| 3 | PREVIEW | 前后向反转 | AC-3.1 |

## 兼容性声明
- **已有 API 行为变更:** 否
- **最低支持版本:** API 8+
- **API 版本号策略:** 框架内部无 @since；PREVIEW/RTL 分支标注

## 架构约束
| 关键约束 | 约束说明 | 影响 AC |
|----------|----------|---------|
| 回调归 04-14-03 | 本域只覆盖快捷键→handler | 全部 |
| 平台分支 | PREVIEW/RTL | AC-3.1,3.2 |

## 非功能性需求
| 类型 | 指标/阈值 | 验证方式 | 证据 |
|------|-----------|----------|------|
| 安全 | 密码模式禁止 copy/cut | 安全扫描 | IsInPasswordMode |

## 多设备适配声明
| 设备类型 | 行为差异 | 规格/约束 | 验证方式 | 证据 |
|----------|----------|-----------|----------|------|
| Mac | Cmd+C/X/V 镜像 | 单测 | — | text_input_client.cpp:39 |
| RTL 语言 | 删词方向交换 | 单测 | — | DeleteBackwardWord |

## 全局特性影响
| 特性 | 适用？ | 结论 | 关联场景 |
|------|--------|------|----------|
| 安全 | 是 | 密码模式剪贴板门控 | AC-1.4 |

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
    query: "HandleOnCopy/Paste/Delete/DeleteComb 与 password/copyOption 门控"
```
**关键文档：** `frameworks/core/components_ng/pattern/text_field/text_field_pattern.cpp`
