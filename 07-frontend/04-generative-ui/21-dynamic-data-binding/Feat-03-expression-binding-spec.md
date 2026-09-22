# 特性规格

> Func-07-04-21-Feat-03 表达式绑定：固化鸿蒙扩展协议的 `{{ }}` 表达式——识别与门控（`IsExpression`/`allowExpression`）、词法/解析/求值流水线、11 级优先级与类型转换、`size()` 内置函数、`$__dataModel.*` 成员访问、沙箱四阶段安全校验（长度/深度/Token/AST 上限）、以及依赖收集与失效刷新。基准实现：`@arkui-genius/genui`（A2UIRender）。

## 概述

| 属性 | 值 |
|------|-----|
| 特性名称 | 表达式绑定 |
| 特性编号 | Func-07-04-21-Feat-03 |
| 优先级 | P0 |
| 目标版本 | 鸿蒙扩展协议 1.0.0（起始 API Version 20） |
| SIG 归属 | GenUI SIG |
| 状态 | Baselined |
| 复杂度 | 复杂 |

## 本次变更范围（Delta）

| 类型 | 内容 | 说明 |
|------|------|------|
| ADDED | 无（存量补录） | Feat-03 承接 design.md 表达式绑定章节 |

## 输入文档

| 文档 | 路径 | 状态 |
|------|------|------|
| Design | `07-frontend/04-generative-ui/21-dynamic-data-binding/design.md` | Baselined |
| 表达式引擎 | `genui/src/main/cpp/expression/ExpressionEngine.cpp` / `.h` | — |
| 求值/上下文 | `genui/src/main/cpp/expression/Evaluator.cpp`、`EvaluationContext.cpp/.h` | — |
| 沙箱 | `genui/src/main/cpp/expression/Sandbox.cpp/.h` | — |
| 依赖收集 | `genui/src/main/cpp/expression/DependencyCollector.cpp/.h`、`DataModelPathUtils.h` | — |
| 表达式语言（Docs） | `concepts/expression-language.md` | 理解辅助 |

> 需求基线、不涉及项详见 proposal.md。design.md 与本文档并行产出，互不依赖。

---

## 用户故事

### US-1: 表达式识别与门控

**作为** 生成式 UI 宿主开发者,
**我想要** 引擎识别 `{{ }}` 表达式并仅在扩展协议下求值,
**以便** 标准协议下 `{{ }}` 按普通字符串。

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-1.1 | WHEN 属性值为完整 `{{ ... }}` 且内部无额外 `{`/`}` THEN `IsExpression` 返回 true（`ExpressionEngine.cpp:429-452`） | 正常 |
| AC-1.2 | WHEN 属性值为「前后含普通文本」或内部含 `{}` THEN `IsExpression` 返回 false，按字面字符串（`ExpressionEngine.cpp:446-447`） | 异常 |
| AC-1.3 | WHEN `context.allowExpression=false` THEN 表达式不被求值，按字面量处理（`DynamicValueResolver.cpp:580-587`） | 边界 |
| AC-1.4 | WHEN 表达式字符串含 `${...}` 占位符 THEN 求值前经 `RewriteExpressionPlaceholders` 改写（`ExpressionEngine.cpp:515`） | 正常 |

### US-2: 运算符与类型转换

**作为** 生成式 UI 宿主开发者,
**我想要** 表达式支持算术/比较/逻辑/三元/一元等运算,
**以便** 在 DSL 内完成动态计算。

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-2.1 | WHEN `+` 任一侧为字符串 THEN 拼接；否则数值加法（`Evaluator` 类型转换，`expression-language.md:75`） | 正常 |
| AC-2.2 | WHEN `/` 或 `%` 右操作数为 0 THEN 求值失败、属性值无效（`expression-language.md:85`） | 异常 |
| AC-2.3 | WHEN `&&`/`||` 表达式 THEN 短路求值且结果归一化为布尔值（`expression-language.md:121-127`） | 边界 |
| AC-2.4 | WHEN `?:` 条件为假值（0/""/false）THEN 返回假值分支（`expression-language.md:146-152`） | 边界 |
| AC-2.5 | WHEN `size(array)` 参数非数组 THEN 返回 0 并报 `size() expects an array argument`（`ExpressionEngine.cpp:402-415`） | 异常 |

### US-3: 数据模型成员访问

**作为** 生成式 UI 宿主开发者,
**我想要** 表达式内访问 `$__dataModel.*` 路径,
**以便** 读取数据模型字段参与计算。

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-3.1 | WHEN 表达式含 `$__dataModel.user.name` THEN `DataModelPathUtils::TryExtractDataModelPath` 提取 `/user/name`（`DataModelPathUtils.h:57-98`） | 正常 |
| AC-3.2 | WHEN 提取的路径在 DataModel 不存在 THEN 置 `EVAL_PATH_NOT_FOUND` 并返回空串（`Evaluator.cpp:594-618`） | 异常 |
| AC-3.3 | WHEN `$__dataModel` 路径语法非法 THEN 置 `PARSE_UNEXPECTED_TOKEN`（`Evaluator.cpp:689-693`） | 异常 |

### US-4: 沙箱与错误传播

**作为** 生成式 UI 宿主开发者,
**我想要** 表达式受安全沙箱限制且失败不崩溃,
**以便** 防 DoS 且属性降级可控。

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-4.1 | WHEN 表达式长度超 2048 THEN 置 `SANDBOX_LENGTH_EXCEEDED` 且求值失败（`ExpressionEngine.cpp:502-505`） | 边界 |
| AC-4.2 | WHEN 嵌套深度超 20 THEN 置 `SANDBOX_DEPTH_EXCEEDED`（`Sandbox.cpp` + `EvaluationContext.h:133`） | 边界 |
| AC-4.3 | WHEN Token 数超 100 或 AST 节点超 100 THEN 置 `SANDBOX_TOKEN_COUNT_EXCEEDED` / `SANDBOX_AST_TOO_LARGE`（`ExpressionEngine.cpp:532-535`、`Sandbox.cpp`） | 边界 |
| AC-4.4 | WHEN 求值失败 THEN 属性值无效、不抛异常、不影响其他组件（`expression-language.md:501-514`） | 异常 |

## 验收追溯

| AC编号 | 关联规则 | 关联 Task | 验证方式 | 证据 |
|----|---------|----------|---------|------|
| AC-1.1,AC-1.2,AC-1.3,AC-1.4 | R-1,R-2 | T-3 | UT：IsExpression/门控 | `ExpressionEngine.cpp:429-452` |
| AC-2.1,AC-2.2,AC-2.3,AC-2.4,AC-2.5 | R-3,R-4 | T-3 | UT：运算符/类型转换 | `expression-language.md` + `Evaluator.cpp` |
| AC-3.1,AC-3.2,AC-3.3 | R-5 | T-3 | UT：成员访问 | `DataModelPathUtils.h:57-98` |
| AC-4.1,AC-4.2,AC-4.3,AC-4.4 | R-6 | T-3 | UT：沙箱/错误 | `Sandbox.cpp`、`ExpressionEngine.cpp` |

## 规则定义

| 规则ID | 类型 | 触发条件 | 预期行为 | 边界/约束 | 关联AC |
|--------|------|---------|---------|----------|--------|
| R-1 | 行为 | 完整 `{{...}}` 值 | 识别为表达式 | 内部禁 `{}` | AC-1.1,AC-1.2 |
| R-2 | 行为 | 非扩展协议 | 表达式按字面字符串 | `allowExpression` 门控 | AC-1.3 |
| R-3 | 行为 | 运算所需的类型对齐 | 按 AsString/AsNumber/AsBool 转换 | 除零→无效 | AC-2.1,AC-2.2,AC-2.3,AC-2.4 |
| R-4 | 行为 | `size()` 调用 | 数组返回长度、非数组返回 0 | 需单参 | AC-2.5 |
| R-5 | 行为 | `$__dataModel.*` 成员访问 | 提取路径并读取 | 非法语法→错误 | AC-3.1,AC-3.2,AC-3.3 |
| R-6 | 边界 | 超过沙箱上限 | 置 `SANDBOX_*` 错误、属性无效 | 2048/20/100/100 | AC-4.1,AC-4.2,AC-4.3,AC-4.4 |

## 验证映射

| 编号 | 对应规格项 | 验证方式 | 验证重点 |
|------|----------|---------|---------|
| VM-1 | AC-1.1,AC-1.2,AC-1.3,AC-1.4 识别/门控 | UT | `{{}}` 判定 |
| VM-2 | AC-2.1,AC-2.2,AC-2.3,AC-2.4,AC-2.5 运算/转换 | UT | 非数字转 0、除零 |
| VM-3 | AC-3.1,AC-3.2,AC-3.3 成员访问 | UT | `$__dataModel` 路径 |
| VM-4 | AC-4.1,AC-4.2,AC-4.3,AC-4.4 沙箱 | UT | 四阶段上限 |

## API 变更分析

> 存量补录，无新增/变更 API。

### 新增 API

N/A。

### 变更/废弃 API

N/A。

## 接口规格

### 接口定义

**`ExpressionEngine::EvaluateAsJsonValue(exprStr, context, preserveNullResult)`（`ExpressionEngine.h:61`）**

| 属性 | 值 |
|------|-----|
| 函数签名 | `JsonValue EvaluateAsJsonValue(const std::string&, EvaluationContext&, bool)` |
| 返回值 | `JsonValue` — 求值结果 |
| 开放范围 | 内部（C++） |
| 错误码 | 3204（`SURFACE_ERROR_ILLEGAL_EXPRESSION`） |
| 关联 AC | AC-2.1,AC-2.2,AC-2.3,AC-2.4,AC-2.5,AC-3.1 |

**`ExpressionEngine::IsExpression / ExtractExpression`（`ExpressionEngine.h:68-69`）**

| 属性 | 值 |
|------|-----|
| 函数签名 | `static bool IsExpression(const std::string&)` / `static std::string ExtractExpression(const std::string&)` |
| 返回值 | `bool` / `std::string` |
| 开放范围 | 内部（C++） |
| 关联 AC | AC-1.1,AC-1.2 |

**参数约束**

| 参数 | 类型 | 必填 | 默认值 | 约束条件 |
|------|------|------|--------|---------|
| exprStr | string | 是 | — | `{{...}}`，≤2048 字符 |
| context.maxExprLength | size_t | 否 | 2048 | 表达式长度上限 |
| context.maxNestingDepth | size_t | 否 | 20 | 嵌套深度上限 |

**行为场景**

| # | 触发条件 | 预期行为 | 关联 AC |
|---|----------|----------|---------|
| 1 | 合法表达式求值 | 返回求值结果 | AC-2.1 |
| 2 | 除零 | 属性值无效 | AC-2.2 |
| 3 | 未定义变量 | 属性值无效 + EVAL_UNDEFINED_VARIABLE | AC-3.2 |
| 4 | 超沙箱上限 | 属性值无效 | AC-4.1,AC-4.2,AC-4.3 |

## 兼容性声明

- **已有 API 行为变更:** 否（存量补录）。
- **配置文件格式变更:** 否。
- **数据存储格式变更:** 否。
- **最低支持版本:** 鸿蒙扩展协议 1.0.0（API Version 20）。
- **API 版本号策略:** 无新增 API；表达式受 `ENABLE_EXPRESSION_ENGINE` 宏控制。

## 架构约束

| 关键约束 | 约束说明 | 影响 AC |
|---------|---------|--------|
| 协议门控 | 仅扩展协议 + updateComponents 生效 | AC-1.3 |
| 沙箱约束 | 长度/深度/Token/AST 上限 | AC-4.1,AC-4.2,AC-4.3,AC-4.4 |
| 类型转换 | 运算前按目标类型转换 | AC-2.1,AC-2.2,AC-2.3,AC-2.4,AC-2.5 |

## 非功能性需求

| 类型 | 指标/阈值 | 验证方式 | 证据 |
|------|----------|---------|------|
| 安全 | 沙箱 4 阶段校验防 DoS | UT | `Sandbox.cpp` |
| 性能 | 表达式长度 ≤2048、Token ≤100 | UT | `EvaluationContext.h:131-134` |
| 可靠性 | 求值失败属性降级不崩溃 | UT | `expression-language.md:501-514` |

## 多设备适配声明

| 设备类型 | 行为差异 | 规格/约束 | 验证方式 | 证据 |
|---------|---------|----------|---------|------|
| 手机 | 无差异 | — | ohosTest | — |
| 平板 | 无差异 | — | ohosTest | — |
| 折叠屏 | 无差异 | — | ohosTest | — |

## 全局特性影响

| 特性 | 适用？ | 结论 | 关联场景 |
|------|-------|------|---------|
| 无障碍 | 否 | — | — |
| 大字体 | 否 | — | — |
| 深色模式 | 是 | `$__colorMode` 参与表达式求值（Feat-04） | AC-3.1,AC-3.2,AC-3.3 |
| 多窗口/分屏 | 否 | — | — |
| 多用户 | 否 | — | — |
| 版本升级 | 否 | — | — |
| 生态兼容 | 部分是 | 表达式为鸿蒙扩展协议专属，A2UI 标准协议不支持 | AC-1.3 |

## 行为场景（可选，Gherkin）

```gherkin
Feature: 表达式绑定
  作为 生成式 UI 宿主开发者
  我想要 用 {{ }} 表达式动态计算属性值
  以便 DSL 内完成拼接/条件/算术

  Scenario Outline: 表达式求值
    Given 属性值为 "{{ <expr> }}"
    When 扩展协议下求值
    Then 结果为 <result>

    Examples:
      | expr | result |
      | 'Hello' + ' World' | "Hello World" |
      | 10 / 0 | 属性值无效 |
      | $__dataModel.count > 0 ? '有库存' : '已售罄' | 依 /count 值 |
      | size($__dataModel.items) | 数组长度或 0 |
```

## Spec 自审清单

- [x] 无"待定""TBD""TODO"等占位符
- [x] 所有 AC 使用 WHEN/THEN 格式，可独立测试
- [x] 范围边界明确（变量语义归 Feat-04）
- [x] 无语义模糊表述
- [x] AC 与规则表交叉一致
- [x] 规则表每条通过质量检查

## context-references

```yaml
context-queries:
  - repo: "GenerativeUI/A2UIRender"
    query: "ExpressionEngine IsExpression ExtractExpression EvaluateAsJsonValue 沙箱"
  - repo: "GenerativeUI/A2UIRender"
    query: "Evaluator 类型转换 除零 $__dataModel 成员访问 size()"
  - repo: "GenerativeUI/A2UIRender"
    query: "Sandbox maxExprLength maxNestingDepth maxTokenCount maxAstNodes"
```

**关键文档：** `genui/src/main/cpp/expression/ExpressionEngine.cpp`、`genui/src/main/cpp/expression/Evaluator.cpp`、`genui/src/main/cpp/expression/Sandbox.cpp`