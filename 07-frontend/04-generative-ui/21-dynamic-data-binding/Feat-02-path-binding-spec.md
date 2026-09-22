# 特性规格

> Func-07-04-21-Feat-02 路径绑定：固化 DynamicValue 的「路径绑定」形态 `{"path": "..."}`（DataBinding/PathBinding）——JSON Pointer 路径解析、`IsValidDataPath` 合法性校验、`~0/~1` 转义解码、缺失路径上报策略（`MissingPathPolicy`）、以及 `${/path}` 模板字符串内嵌路径解析。基准实现：`@arkui-genius/genui`（A2UIRender）。

## 概述

| 属性 | 值 |
|------|-----|
| 特性名称 | 路径绑定 |
| 特性编号 | Func-07-04-21-Feat-02 |
| 优先级 | P0 |
| 目标版本 | A2UI 原生协议 v0.9 |
| SIG 归属 | GenUI SIG |
| 状态 | Baselined |
| 复杂度 | 复杂 |

## 本次变更范围（Delta）

| 类型 | 内容 | 说明 |
|------|------|------|
| ADDED | 无（存量补录） | Feat-02 承接 design.md 路径绑定章节 |

## 输入文档

| 文档 | 路径 | 状态 |
|------|------|------|
| Design | `07-frontend/04-generative-ui/21-dynamic-data-binding/design.md` | Baselined |
| 动态值解析 | `genui/src/main/cpp/data/DynamicValueResolver.cpp` / `DynamicValueResolver.h` | — |
| 路径校验 | `genui/src/main/cpp/data/PathValidator.cpp` / `PathValidator.h` | — |
| 绑定结构 | `genui/src/main/cpp/data/DataBinding.h` | — |
| 类型契约（ArkTS） | `genui/src/main/ets/core/types/DataBinding.ets`、`runtime/TypeGuards.ets` | — |
| 类型参考（Docs） | `reference/types.md`（DataBinding/PathBinding） | 理解辅助 |

> 需求基线、不涉及项详见 proposal.md。design.md 与本文档并行产出，互不依赖。

---

## 用户故事

### US-1: 路径描述符识别与解析

**作为** 生成式 UI 宿主开发者,
**我想要** 用 `{"path": "..."}` 绑定 DataModel 中的值,
**以便** 组件从数据模型读取内容。

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-1.1 | WHEN 描述符为仅含 `path` 键的对象 THEN `HasOnlyPathDescriptorKey` 判定为纯路径描述符（`DynamicValueResolver.cpp:258-270`） | 正常 |
| AC-1.2 | WHEN 描述符含 `call` 键 THEN 走函数调用解析而非路径解析（`DynamicValueResolver.cpp:1191-1198`） | 正常 |
| AC-1.3 | WHEN `path` 字段非 string THEN 返回 `FailInvalid("path descriptor must contain string field 'path'")`（`DynamicValueResolver.cpp:769-772`） | 异常 |
| AC-1.4 | WHEN ArkTS 侧值为含 `path` string 且无 `call` 的记录 THEN `TypeGuards.isDataBinding` 返回 true（`TypeGuards.ets:23-30`） | 正常 |

### US-2: JSON Pointer 与转义

**作为** 生成式 UI 宿主开发者,
**我想要** 路径支持 JSON Pointer 转义（`~0`/`~1`）与数组索引,
**以便** 定位含特殊字符的键。

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-2.1 | WHEN `ResolvePathValue` 读取节点 THEN 以 `GetNode(path, true)` 解码 JSON Pointer（`DynamicValueResolver.cpp:784`） | 正常 |
| AC-2.2 | WHEN 路径段含 `~0` THEN 解码为 `~`（`DataModel.cpp:52-54`） | 正常 |
| AC-2.3 | WHEN 路径段含 `~1` THEN 解码为 `/`（`DataModel.cpp:47-50`） | 正常 |
| AC-2.4 | WHEN 路径含 `/items/0` 形式数组索引 THEN `GetNode` 按索引取数组元素（`DataModel.cpp:492-504`） | 正常 |

### US-3: 非法路径与缺失上报

**作为** 生成式 UI 宿主开发者,
**我想要** 非法路径被拒绝、缺失路径按策略上报,
**以便** 避免静默错误并可控降级。

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-3.1 | WHEN 路径非法且不含 `~` THEN `ResolvePathValue` 返回 `FailInvalid`（`DynamicValueResolver.cpp:775-777`） | 异常 |
| AC-3.2 | WHEN 路径合法但节点不存在 THEN 走 `DispatchMissingPathError` 并返回 `FailPath`（`DynamicValueResolver.cpp:784-788`） | 异常 |
| AC-3.3 | WHEN `missingPathPolicy=REPORT_ALWAYS` THEN 缺失路径始终上报（`DynamicValueResolver.cpp:62-66`） | 正常 |
| AC-3.4 | WHEN `missingPathPolicy=DEFER_UNTIL_DATA_UPDATE` 且 surface 未收到数据更新 THEN 不上报缺失（`DynamicValueResolver.cpp:62-69`） | 边界 |
| AC-3.5 | WHEN `IsValidDataPath` 收到空串或非 `/` 开头路径 THEN 返回 false（`PathValidator.cpp:31-33`） | 异常 |

### US-4: 模板字符串内嵌路径

**作为** 生成式 UI 宿主开发者,
**我想要** 在字符串中用 `${/path}` 内嵌 DataModel 值,
**以便** 拼接动态文本。

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-4.1 | WHEN 字符串含 `${/user/name}` 且 `allowExpression` 为真 THEN `ResolveJsonPointerTemplateValue` 解析为拼接字符串（`DynamicValueResolver.cpp:312-366`） | 正常 |
| AC-4.2 | WHEN 模板中 `${...}` 内路径为合法 JSON Pointer THEN 取值拼接，否则保留原字符（`DynamicValueResolver.cpp:291-310`） | 边界 |
| AC-4.3 | WHEN `${` 前有转义 `\${` THEN 按字面 `${` 输出不解析（`DynamicValueResolver.cpp:330-335`） | 边界 |

## 验收追溯

| AC编号 | 关联规则 | 关联 Task | 验证方式 | 证据 |
|----|---------|----------|---------|------|
| AC-1.1,AC-1.2,AC-1.3,AC-1.4 | R-1 | T-2 | C++/ArkTS UT：描述符识别 | `DynamicValueResolver.cpp:258-270` |
| AC-2.1,AC-2.2,AC-2.3,AC-2.4 | R-2 | T-2 | C++ UT：JSON Pointer 解码 | `DataModel.cpp:47-54` |
| AC-3.1,AC-3.2,AC-3.3,AC-3.4,AC-3.5 | R-3,R-4 | T-2 | C++ UT：非法/缺失路径 | `DynamicValueResolver.cpp:775-788` |
| AC-4.1,AC-4.2,AC-4.3 | R-5 | T-2 | C++ UT：模板字符串 | `DynamicValueResolver.cpp:312-366` |

## 规则定义

| 规则ID | 类型 | 触发条件 | 预期行为 | 边界/约束 | 关联AC |
|--------|------|---------|---------|----------|--------|
| R-1 | 行为 | 仅含 `path` 键的对象 | 判定为路径绑定，走 `ResolvePathValue` | 含 `call` 键走函数调用 | AC-1.1,AC-1.2,AC-1.3,AC-1.4 |
| R-2 | 行为 | 读取节点 | `GetNode(path, decodePointer=true)` 解码 `~0/~1` 与数组索引 | — | AC-2.1,AC-2.2,AC-2.3,AC-2.4 |
| R-3 | 异常 | 非法路径 | `ResolvePathValue` 返回 `FailInvalid` | 含 `~` 时放行给解码层 | AC-3.1,AC-3.5 |
| R-4 | 行为 | 节点缺失 | 按 `MissingPathPolicy` 上报并返回 `FailPath` | DEFER 策略未收到数据则不报 | AC-3.2,AC-3.3,AC-3.4 |
| R-5 | 行为 | 字符串含 `${/path}` | 拼接解析；非法/转义按字面保留 | 需 `allowExpression` | AC-4.1,AC-4.2,AC-4.3 |

## 验证映射

| 编号 | 对应规格项 | 验证方式 | 验证重点 |
|------|----------|---------|---------|
| VM-1 | AC-1.1,AC-1.2,AC-1.3,AC-1.4 描述符识别 | UT | path/call 判别 |
| VM-2 | AC-2.1,AC-2.2,AC-2.3,AC-2.4 JSON Pointer | UT | ~0/~1 与数组索引 |
| VM-3 | AC-3.1,AC-3.2,AC-3.3,AC-3.4,AC-3.5 非法/缺失 | UT | MissingPathPolicy 分支 |
| VM-4 | AC-4.1,AC-4.2,AC-4.3 模板内嵌 | UT | `${}` 拼接/转义 |

## API 变更分析

> 存量补录，无新增/变更 API。

### 新增 API

N/A。

### 变更/废弃 API

N/A。

## 接口规格

### 接口定义

**`DynamicValueResolver::ResolvePathValue(value, context)`（`DynamicValueResolver.cpp:767`）**

| 属性 | 值 |
|------|-----|
| 函数签名 | `ResolvedValue ResolvePathValue(const JsonValue& value, const DynamicResolveContext& context)` |
| 返回值 | `ResolvedValue` — `OkPath` / `FailPath` / `FailInvalid` |
| 开放范围 | 内部（C++） |
| 错误码 | 3202（`SURFACE_ERROR_DYNAMIC_VALUE_RESOLVE_FAILED`） |
| 关联 AC | AC-1.1,AC-2.1,AC-3.1,AC-3.2 |

**`PathValidator::IsValidDataPath(path)`（`PathValidator.cpp:29`）**

| 属性 | 值 |
|------|-----|
| 函数签名 | `bool IsValidDataPath(const std::string& path)` |
| 返回值 | `bool` — 是否合法 JSON Pointer |
| 开放范围 | 内部（C++） |
| 关联 AC | AC-3.5 |

**参数约束**

| 参数 | 类型 | 必填 | 默认值 | 约束条件 |
|------|------|------|--------|---------|
| value.path | string | 是 | — | JSON Pointer，`required:["path"]` |
| context.allowExpression | bool | 否 | false | 模板字符串 `${}` 需要为真 |
| context.missingPathPolicy | enum | 否 | REPORT_ALWAYS | 决定缺失是否上报 |

**行为场景**

| # | 触发条件 | 预期行为 | 关联 AC |
|---|----------|----------|---------|
| 1 | 合法 path + 节点存在 | `OkPath` 返回值 | AC-1.1,AC-2.1 |
| 2 | 非法 path | `FailInvalid` | AC-3.1 |
| 3 | 合法 path + 节点缺失 | `FailPath` + 上报 | AC-3.2 |
| 4 | 字符串含 `${/path}` | 拼接解析 | AC-4.1 |

## 兼容性声明

- **已有 API 行为变更:** 否（存量补录）。
- **配置文件格式变更:** 否。
- **数据存储格式变更:** 否。
- **最低支持版本:** A2UI 原生协议 v0.9。
- **API 版本号策略:** 无新增 API。

## 架构约束

| 关键约束 | 约束说明 | 影响 AC |
|---------|---------|--------|
| 描述符形态 | 仅含 `path` 键判路径绑定 | AC-1.1,AC-1.2,AC-1.3,AC-1.4 |
| 转义解码 | `~0`/`~1` 在读取层解码 | AC-2.1,AC-2.2,AC-2.3,AC-2.4 |
| 缺失策略 | MissingPathPolicy 双策略 | AC-3.1,AC-3.2,AC-3.3,AC-3.4,AC-3.5 |

## 非功能性需求

| 类型 | 指标/阈值 | 验证方式 | 证据 |
|------|----------|---------|------|
| 安全 | 路径白名单 `[A-Za-z0-9_]` 防注入 | UT | `PathValidator.cpp:22-25` |
| 可靠性 | 缺失路径可控降级不崩溃 | UT | `DynamicValueResolver.cpp:62-76` |

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
| 深色模式 | 否 | — | — |
| 多窗口/分屏 | 否 | — | — |
| 多用户 | 否 | 数据模型内存态 | — |
| 版本升级 | 否 | — | — |
| 生态兼容 | 是 | A2UI v0.9 DataBinding/PathBinding 语义 | AC-1.1,AC-1.2,AC-1.3,AC-1.4 |

## 行为场景（可选，Gherkin）

```gherkin
Feature: 路径绑定
  作为 生成式 UI 宿主开发者
  我想要 用 {"path": "..."} 绑定 DataModel 值
  以便 组件随数据更新自动刷新

  Scenario Outline: 路径解析
    Given 属性值为 <描述符>
    When 引擎解析
    Then <结果>

    Examples:
      | 描述符 | 结果 |
      | {"path": "/user/name"} | OkPath 返回 /user/name 值 |
      | {"path": ""} | 非法路径 FailInvalid |
      | {"path": "/missing"} | FailPath 缺失上报 |
```

## Spec 自审清单

- [x] 无"待定""TBD""TODO"等占位符
- [x] 所有 AC 使用 WHEN/THEN 格式，可独立测试
- [x] 范围边界明确（表达式/变量语义归其余 Feat）
- [x] 无语义模糊表述
- [x] AC 与规则表交叉一致
- [x] 规则表每条通过质量检查

## context-references

```yaml
context-queries:
  - repo: "GenerativeUI/A2UIRender"
    query: "DynamicValueResolver ResolvePathValue HasOnlyPathDescriptorKey JSON Pointer"
  - repo: "GenerativeUI/A2UIRender"
    query: "PathValidator IsValidDataPath MissingPathPolicy DispatchMissingPathError"
  - repo: "GenerativeUI/A2UIRender"
    query: "ResolveJsonPointerTemplateValue ${/path} 模板字符串"
```

**关键文档：** `genui/src/main/cpp/data/DynamicValueResolver.cpp`、`genui/src/main/cpp/data/PathValidator.cpp`、`genui/src/main/ets/core/types/DataBinding.ets`
