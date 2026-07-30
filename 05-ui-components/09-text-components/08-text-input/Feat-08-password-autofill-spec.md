# 特性规格

## 概述

| 属性 | 值 |
|------|-----|
| 特性名称 | TextInput 密码与自动填充 |
| 特性编号 | Func-05-09-08-Feat-08 |
| 所属 Epic | 无 |
| 优先级 | P1 |
| 目标版本 | API 10–12 |
| SIG 归属 | ArkUI SIG |
| 状态 | Baselined |
| 复杂度 | 标准 |

## 本次变更范围（Delta）
全新特性补录（lineage: new），无 Delta。

## 输入文档
- 设计文档：`08-text-input/design.md`
- 源码定位：`text_field_model_ng.h`（SetPasswordIcon/SetShowPasswordIcon/SetShowPasswordText/SetPasswordRules/SetEnableAutoFill/SetEnableAutoFillAnimation/SetOnSecurityStateChange）、`text_input_layout_algorithm.cpp`（MeasureAutoFillIcon/LayoutAutoFillIcon）

## 用户故事

### US-1: 密码图标
作为开发者，我希望经 passwordIcon/showPasswordIcon 自定义密码可见图标。

| AC编号 | 验收标准 | 类型 |
|--------|----------|------|
| AC-1.1 | WHEN `passwordIcon({onIconSrc, offIconSrc})`（@since 10/11）THEN 自定义密码可见/隐藏图标 | 正常 |
| AC-1.2 | WHEN `showPasswordIcon(true)` THEN 显示密码图标 | 正常 |

### US-2: 密码显示/规则
作为开发者，我希望经 showPassword/passwordRules 控制密码可见与生成规则。

| AC编号 | 验收标准 | 类型 |
|--------|----------|------|
| AC-2.1 | WHEN `showPassword(true)`（@since 12）THEN 显示密码明文 | 正常 |
| AC-2.2 | WHEN `passwordRules(rules)`（@since 12）THEN 设置密码生成规则 | 正常 |
| AC-2.3 | WHEN 密码可见切换 THEN `onSecurityStateChange` 回调（@since 12，见 Feat-06） | 正常 |

### US-3: 自动填充
作为开发者，我希望经 enableAutoFill/enableAutoFillAnimation 启用自动填充。

| AC编号 | 验收标准 | 类型 |
|--------|----------|------|
| AC-3.1 | WHEN `enableAutoFill(true)`（@since 12）THEN 启用自动填充 | 正常 |
| AC-3.2 | WHEN `enableAutoFillAnimation(true)` THEN 启用自动填充动画 | 正常 |
| AC-3.3 | WHEN 自动填充图标 THEN 经 MeasureAutoFillIcon/LayoutAutoFillIcon 布局图标 | 正常 |

## 验收追溯

| AC | 关联规则 | 关联 Task | 验证方式 | 证据 |
|----|----------|-----------|----------|------|
| AC-1.1 | R-1 | TASK-TI-08 | 单测 | text_field_model_ng.h SetPasswordIcon |
| AC-1.2 | R-1 | TASK-TI-08 | 单测 | text_field_model_ng.h SetShowPasswordIcon |
| AC-2.1 | R-2 | TASK-TI-08 | 单测 | text_field_model_ng.h SetShowPasswordText |
| AC-2.2 | R-3 | TASK-TI-08 | 单测 | text_field_model_ng.h:126 |
| AC-3.1 | R-4 | TASK-TI-08 | 单测 | text_field_model_ng.h:127 |
| AC-3.2 | R-4 | TASK-TI-08 | 单测 | text_field_model_ng.h:128 |
| AC-3.3 | R-5 | TASK-TI-08 | 单测 | text_input_layout_algorithm.cpp |

## 规则定义

| 规则ID | 类型 | 触发条件 | 预期行为 | 边界/约束 | 关联AC |
|--------|------|----------|----------|-----------|-------|
| R-1 | 行为 | passwordIcon/showPasswordIcon（@since 10/11） | 自定义/显示密码图标 | onIconSrc/offIconSrc | AC-1.1,1.2 |
| R-2 | 行为 | showPassword(true)（@since 12） | 显示明文 | — | AC-2.1 |
| R-3 | 行为 | passwordRules(rules)（@since 12） | 设置密码生成规则 | rules string | AC-2.2 |
| R-4 | 行为 | enableAutoFill/enableAutoFillAnimation（@since 12） | 启用自动填充/动画 | — | AC-3.1,3.2 |
| R-5 | 行为 | 自动填充图标 | MeasureAutoFillIcon/LayoutAutoFillIcon | — | AC-3.3 |

## 验证映射

| 编号 | 对应规格项 | 验证方式 | 验证重点 |
|------|-----------|----------|----------|
| VM-1 | R-1 图标 | 单测 | on/off icon |
| VM-2 | R-4 自动填充 | 单测 | enable flag |
| VM-3 | R-5 图标布局 | 单测 | MeasureAutoFillIcon |

## API 变更分析

### 新增 API

| API 名称 | 开放范围 | 入参概要 | 返回值 | 错误码范围 | 功能描述 | 关联 AC |
|----------|----------|----------|--------|-----------|----------|---------|
| `passwordIcon(value)` | Public | PasswordIcon | this | 无 | 密码图标 @since 10/11 | AC-1.1 |
| `showPasswordIcon(value)` | Public | boolean | this | 无 | 显示图标 @since 11 | AC-1.2 |
| `showPassword(visible)` | Public | boolean | this | 无 | 显示明文 @since 12 | AC-2.1 |
| `passwordRules(value)` | Public | string | this | 无 | 密码规则 @since 12 | AC-2.2 |
| `enableAutoFill(value)` | Public | boolean | this | 无 | 自动填充 @since 12 | AC-3.1 |
| C-API `NODE_TEXT_INPUT_SHOW_PASSWORD_ICON`/`PASSWORD_RULES`/`ENABLE_AUTO_FILL` | System | KNode, ... | void | 无 | C-API 对应 @since 12 | 全部 |

## 接口规格

### 接口定义

**passwordIcon(value)**

| 属性 | 值 |
|------|-----|
| 函数签名 | `passwordIcon(value: PasswordIcon): TextInputAttribute` |
| 返回值 | `TextInputAttribute` |
| 开放范围 | Public |
| 错误码 | N/A |
| 关联 AC | AC-1.1 |

**参数约束**

| 参数 | 类型 | 必填 | 默认值 | 约束条件 |
|------|------|------|--------|---------|
| value | PasswordIcon | 是 | — | onIconSrc/offIconSrc 可选 string\|Resource |

**行为场景**

| # | 触发条件 | 预期行为 | 关联 AC |
|---|----------|----------|---------|
| 1 | 设置图标 | 自定义显示 | AC-1.1 |

## 兼容性声明
- **已有 API 行为变更:** 否
- **最低支持版本:** passwordIcon/showPasswordIcon @since 10/11；showPassword/passwordRules/enableAutoFill @since 12
- **API 版本号策略:** 全量 @since 标注

## 架构约束
| 关键约束 | 约束说明 | 影响 AC |
|----------|----------|---------|
| 自动填充图标独立布局 | MeasureAutoFillIcon | AC-3.3 |

## 非功能性需求
| 类型 | 指标/阈值 | 验证方式 | 证据 |
|------|-----------|----------|------|
| 安全 | 密码不明文泄漏 | 安全扫描 | — |

## 多设备适配声明
无差异。

## 全局特性影响
| 特性 | 适用？ | 结论 | 关联场景 |
|------|--------|------|----------|
| 无障碍 | 是 | 密码图标需无障碍标签 | AC-1.1 |

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
    query: "TextInput 密码图标与自动填充图标布局"
```
**关键文档：** `interface/sdk-js/api/@internal/component/ets/text_input.d.ts`
