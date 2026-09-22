# 特性规格

> Func-07-04-01-Feat-04 数据模型更新与绑定刷新：固化 `updateDataModel` 的 `path`/`value` 三态语义（带 value 更新、缺 value 删除、path 缺省 `/` 全量替换）、`DataModel` 路径化存储与 `MAX_DATA_MODEL_DEPTH=20` 深度上限、`BindingEngine` 订阅索引（`path→component_id`）与通知刷新。基准实现：`@arkui-genius/genui`（A2UIRender）。

## 概述

| 属性 | 值 |
|------|-----|
| 特性名称 | 数据模型更新与绑定刷新 |
| 特性编号 | Func-07-04-01-Feat-04 |
| 优先级 | P0 |
| 目标版本 | A2UI 原生协议 v0.9 |
| SIG 归属 | GenUI SIG |
| 状态 | Baselined |
| 复杂度 | 复杂 |

## 本次变更范围（Delta）

| 类型 | 内容 | 说明 |
|------|------|------|
| ADDED | 无（存量补录） | Feat-04 承接 design.md 数据模型章节 |

## 输入文档

| 文档 | 路径 | 状态 |
|------|------|------|
| Design | `07-frontend/04-generative-ui/01-protocol-core-message-model/design.md` | Baselined |
| 数据模型 | `genui/src/main/cpp/data/DataModel.cpp` / `DataModel.h` | — |
| 绑定引擎 | `genui/src/main/cpp/data/BindingEngine.cpp` / `BindingEngine.h` | — |
| 路径校验 | `genui/src/main/cpp/data/PathValidator.cpp` / `PathValidator.h` | — |
| 消息格式参考（Docs） | `reference/messages.md` | 理解辅助 |

> 需求基线、不涉及项详见 proposal.md。design.md 与本文档并行产出，互不依赖。

---

## 用户故事

### US-1: updateDataModel 三态语义

**作为** 生成式 UI 宿主开发者,
**我想要** 用 path/value 表达增删改,
**以便** 精确控制数据模型。

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-1.1 | WHEN `updateDataModel` 含 `path` 与 `value` THEN 触发 `UpdateByPath`（按路径更新）（`DataModel.h:67`） | 正常 |
| AC-1.2 | WHEN `updateDataModel` 含 `path` 但缺 `value` THEN 触发 `DeleteByPath`（删除对应 key）（`DataModel.h:68`） | 正常 |
| AC-1.3 | WHEN `updateDataModel` 缺 `path`（默认 `/`）且含 `value` THEN 触发 `ReplaceAll`（全量替换）（`DataModel.h:69`） | 边界 |
| AC-1.4 | WHEN `updateDataModel` 同时缺 `path` 与 `value` THEN 消息体校验失败（`A2UIMessage.ets:132-137`） | 异常 |
| AC-1.5 | WHEN `updateDataModel.value` 未提供（undefined）THEN 按删除语义处理（`messages.md:79`） | 正常 |

### US-2: 路径校验

**作为** 生成式 UI 宿主开发者,
**我想要** 引擎校验路径合法性,
**以便** 非法路径被拒绝。

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-2.1 | WHEN path 为合法 JSON Pointer（如 `/user/name`）THEN `IsValidDataPath` 返回 true（`PathValidator.h:23`） | 正常 |
| AC-2.2 | WHEN path 为非法格式 THEN `IsValidDataPath` 返回 false | 异常 |
| AC-2.3 | WHEN path 缺省 TH以 `/` 为默认路径（根） | 边界 |

### US-3: 深度上限

**作为** 生成式 UI 宿主开发者,
**我想要** 引擎限制数据模型嵌套深度,
**以便** 防止恶意深层嵌套导致栈溢出。

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-3.1 | WHEN 数据模型嵌套深度超过 `MAX_DATA_MODEL_DEPTH`（=20） THEN 超出部分被拒绝/截断（`DataModel.h:53`） | 边界 |
| AC-3.2 | WHEN 数据模型深度 ≤ 20 THEN 正常更新 | 正常 |

### US-4: 绑定订阅与通知

**作为** 生成式 UI 宿主开发者,
**我想要** 数据模型更新后自动刷新绑定组件,
**以便** UI 与数据保持同步。

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-4.1 | WHEN 组件注册对某 path 的兴趣 THEN `RegisterInterest` 建立 `pathToComponents_` 映射（`DataModel.h:78`） | 正常 |
| AC-4.2 | WHEN 数据模型更新 THEN `NotifyPathUpdate` 通知订阅该 path 的组件（`DataModel.h:82`） | 正常 |
| AC-4.3 | WHEN 组件解绑 THEN `UnregisterInterest` 移除订阅（`DataModel.h:79`） | 正常 |
| AC-4.4 | WHEN 更新路径命中组件注册路径（前缀匹配）THEN `IsPathAffected` 判定为受影响（`DataModel.h:112`） | 正常 |
| AC-4.5 | WHEN 订阅组件已失效（weak_ptr 过期）THEN `CollectLiveSubscribers` 过滤（`DataModel.h:114-115`） | 边界 |

## 验收追溯

| AC编号 | 关联规则 | 关联 Task | 验证方式 | 证据 |
|----|---------|----------|---------|------|
| AC-1.1,AC-1.2,AC-1.3,AC-1.4,AC-1.5 | R-1,R-2 | T-4 | C++ UT：ProcessUpdate 三态 | `DataModel.h:67-72` |
| AC-2.1,AC-2.2,AC-2.3 | R-3 | T-4 | C++ UT：IsValidDataPath | `PathValidator.h:23` |
| AC-3.1,AC-3.2 | R-4 | T-4 | C++ UT：深度上限 | `DataModel.h:53` |
| AC-4.1,AC-4.2,AC-4.3,AC-4.4,AC-4.5 | R-5 | T-4 | C++ UT：RegisterInterest/NotifyPathUpdate | `DataModel.h:78-82` |

## 规则定义

| 规则ID | 类型 | 触发条件 | 预期行为 | 边界/约束 | 关联AC |
|--------|------|---------|---------|----------|--------|
| R-1 | 行为 | path+value 双有 | UpdateByPath | — | AC-1.1 |
| R-2 | 行为 | 有 path 缺 value | DeleteByPath；缺 path 有 value→ReplaceAll | 两者都缺→错误 | AC-1.2,AC-1.3,AC-1.4 |
| R-3 | 异常 | 非法 path | IsValidDataPath 拒绝 | path 缺省 `/` | AC-2.1,AC-2.2,AC-2.3 |
| R-4 | 边界 | 嵌套深度>20 | 拒绝/截断 | MAX_DATA_MODEL_DEPTH=20 | AC-3.1 |
| R-5 | 行为 | 数据更新 | 通知订阅组件刷新 | weak_ptr 过期过滤 | AC-4.1,AC-4.2,AC-4.3,AC-4.4,AC-4.5 |

## 验证映射

| 编号 | 对应规格项 | 验证方式 | 验证重点 |
|------|----------|---------|---------|
| VM-1 | AC-1.1,AC-1.2,AC-1.3,AC-1.4,AC-1.5 三态语义 | UT | path/value 组合 |
| VM-2 | AC-2.1,AC-2.2,AC-2.3 路径校验 | UT | JSON Pointer |
| VM-3 | AC-3.1,AC-3.2 深度上限 | UT | 20 层 |
| VM-4 | AC-4.1,AC-4.2,AC-4.3,AC-4.4,AC-4.5 订阅通知 | UT | path 前缀匹配 |

## API 变更分析

> 存量补录，无新增/变更 API。

### 新增 API

N/A。

### 变更/废弃 API

N/A。

## 接口规格

### 接口定义

**`DataModel::ProcessUpdate(updateRequest)`（`DataModel.h:72`）**

| 属性 | 值 |
|------|-----|
| 函数签名 | `void ProcessUpdate(const DataModelUpdate& updateRequest)` |
| 返回值 | `void` |
| 开放范围 | 内部（C++） |
| 错误码 | N/A |
| 关联 AC | AC-1.1,AC-1.2,AC-1.3,AC-1.4,AC-1.5 |

**`DataModel::UpdateByPath(path, value)` / `DeleteByPath(path)` / `ReplaceAll(value)`（`DataModel.h:67-69`）**

| 属性 | 值 |
|------|-----|
| 函数签名 | `bool UpdateByPath(const std::string&, const JsonValue&)` / `bool DeleteByPath(const std::string&)` / `bool ReplaceAll(const JsonValue&)` |
| 返回值 | `bool` — 是否成功 |
| 开放范围 | 内部（C++） |
| 关联 AC | AC-1.1,AC-1.2,AC-1.3 |

**参数约束**

| 参数 | 类型 | 必填 | 默认值 | 约束条件 |
|------|------|------|--------|---------|
| path | string | 否 | `/` | JSON Pointer |
| value | JsonValue | 否 | — | 缺省表达删除 |

**行为场景**

| # | 触发条件 | 预期行为 | 关联 AC |
|---|----------|----------|---------|
| 1 | path+value | 按路径更新 | AC-1.1 |
| 2 | 仅 path | 删除 | AC-1.2 |
| 3 | 仅 value（path 缺省） | 全量替换 | AC-1.3 |

## 兼容性声明

- **已有 API 行为变更:** 否（存量补录）。
- **配置文件格式变更:** 否。
- **数据存储格式变更:** 否（DataModel 内存态）。
- **最低支持版本:** A2UI 原生协议 v0.9。
- **API 版本号策略:** 无新增 API。

## 架构约束

| 关键约束 | 约束说明 | 影响 AC |
|---------|---------|--------|
| 三态语义 | path/value 组合决定增删改 | AC-1.1,AC-1.2,AC-1.3,AC-1.4,AC-1.5 |
| 深度上限 | MAX_DATA_MODEL_DEPTH=20 | AC-3.1,AC-3.2 |
| 订阅索引 | path→component_id | AC-4.1,AC-4.2,AC-4.3,AC-4.4,AC-4.5 |

## 非功能性需求

| 类型 | 指标/阈值 | 验证方式 | 证据 |
|------|----------|---------|------|
| 安全 | 深度上限防栈溢出 | UT | `DataModel.h:53` |
| 性能 | 前缀匹配路径通知 | UT | `DataModel.h:112` |

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
| 多用户 | 否 | 数据模型内存态，无持久化 | — |
| 版本升级 | 否 | — | — |
| 生态兼容 | 是 | A2UI v0.9 updateDataModel 语义 | AC-1.1,AC-1.2,AC-1.3,AC-1.4,AC-1.5 |

## 行为场景（可选，Gherkin）

```gherkin
Feature: 数据模型更新与绑定刷新
  作为 生成式 UI 宿主开发者
  我想要 用 path/value 表达增删改并自动刷新绑定组件
  以便 UI 与数据同步

  Scenario Outline: updateDataModel 三态
    Given updateDataModel 请求
    When 含 <path> 与 <value>
    Then <行为>

    Examples:
      | path | value | 行为 |
      | /user | {"name":"A"} | UpdateByPath 更新 |
      | /user | (缺省) | DeleteByPath 删除 |
      | (缺省) | {"name":"A"} | ReplaceAll 全量替换 |
```

## Spec 自审清单

- [x] 无"待定""TBD""TODO"等占位符
- [x] 所有 AC 使用 WHEN/THEN 格式，可独立测试
- [x] 范围边界明确（表达式/变量语义归 07-04-21）
- [x] 无语义模糊表述
- [x] AC 与规则表交叉一致
- [x] 规则表每条通过质量检查

## context-references

```yaml
context-queries:
  - repo: "GenerativeUI/A2UIRender"
    query: "DataModel UpdateByPath DeleteByPath ReplaceAll ProcessUpdate path value 三态"
  - repo: "GenerativeUI/A2UIRender"
    query: "BindingEngine RegisterInterest NotifyPathUpdate IsPathAffected 绑定订阅通知"
  - repo: "GenerativeUI/A2UIRender"
    query: "MAX_DATA_MODEL_DEPTH PathValidator IsValidDataPath"
```

**关键文档：** `genui/src/main/cpp/data/DataModel.cpp`、`genui/src/main/cpp/data/BindingEngine.cpp`、`genui/src/main/cpp/data/PathValidator.cpp`