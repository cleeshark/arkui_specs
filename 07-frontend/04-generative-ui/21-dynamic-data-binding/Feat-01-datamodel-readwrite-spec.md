# 特性规格

> Func-07-04-21-Feat-01 DataModel 读写契约：固化 `updateDataModel` 消息到 `DataModel` 的三态读写语义（path+value 更新、仅 path 删除、仅 value 全量替换）、`MAX_DATA_MODEL_DEPTH=20` 嵌套深度上限、`BindingEngine` 的 DataModel 创建/更新入口、以及订阅索引（`pathToComponents_`）与失效通知（`NotifyPathUpdate` 前缀匹配）。基准实现：`@arkui-genius/genui`（A2UIRender）。

## 概述

| 属性 | 值 |
|------|-----|
| 特性名称 | DataModel 读写契约 |
| 特性编号 | Func-07-04-21-Feat-01 |
| 优先级 | P0 |
| 目标版本 | A2UI 原生协议 v0.9 |
| SIG 归属 | GenUI SIG |
| 状态 | Baselined |
| 复杂度 | 复杂 |

## 本次变更范围（Delta）

| 类型 | 内容 | 说明 |
|------|------|------|
| ADDED | 无（存量补录） | Feat-01 承接 design.md 数据模型读写章节 |

## 输入文档

| 文档 | 路径 | 状态 |
|------|------|------|
| Design | `07-frontend/04-generative-ui/21-dynamic-data-binding/design.md` | Baselined |
| 数据模型 | `genui/src/main/cpp/data/DataModel.cpp` / `DataModel.h` | — |
| 绑定引擎 | `genui/src/main/cpp/data/BindingEngine.cpp` / `BindingEngine.h` | — |
| 路径校验 | `genui/src/main/cpp/data/PathValidator.cpp` / `PathValidator.h` | — |
| 数据模型概念（Docs） | `concepts/data-model-and-binding.md` | 理解辅助 |

> 需求基线、不涉及项详见 proposal.md。design.md 与本文档并行产出，互不依赖。

---

## 用户故事

### US-1: updateDataModel 三态语义

**作为** 生成式 UI 宿主开发者,
**我想要** 用 path/value 组合表达增删改,
**以便** 精确控制每个 Surface 的 DataModel。

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-1.1 | WHEN `updateDataModel` 同时含 `path` 与 `value` THEN 触发 `UpdateByPath` 按路径更新（`DataModel.cpp:455-457`） | 正常 |
| AC-1.2 | WHEN `updateDataModel` 含 `path` 但缺 `value` THEN 触发 `DeleteByPath` 删除对应 key（`DataModel.cpp:458-460`） | 正常 |
| AC-1.3 | WHEN `updateDataModel` 缺 `path`（空串）且含 `value` THEN 触发 `ReplaceAll` 全量替换（`DataModel.cpp:461-463`） | 边界 |
| AC-1.4 | WHEN `updateDataModel` 同时缺 `path` 与 `value` THEN 判为无效请求并记录 WARN 日志（`DataModel.cpp:464-466`） | 异常 |
| AC-1.5 | WHEN `updateDataModel.surfaceId` 与 DataModel 自身的 surfaceId 不匹配 THEN 忽略本次更新直接返回（`DataModel.cpp:448-452`） | 异常 |

### US-2: 深度上限与路径合法性

**作为** 生成式 UI 宿主开发者,
**我想要** 引擎限制数据嵌套深度并校验路径,
**以便** 防止恶意深层嵌套与非法路径。

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-2.1 | WHEN 数据模型嵌套深度超过 `MAX_DATA_MODEL_DEPTH`（=20） THEN 引擎记录 ERROR 日志（`BindingEngine.cpp:136-141`） | 边界 |
| AC-2.2 | WHEN 路径合法（`/` 或 `/user/name`）THEN `IsValidDataPath` 返回 true（`PathValidator.cpp:29-61`） | 正常 |
| AC-2.3 | WHEN 路径非法（空串、非 `/` 开头、空段、含非法字符）THEN `IsValidDataPath` 返回 false（`PathValidator.cpp:31-33,44-53`） | 异常 |

### US-3: 路径化读取与数组索引

**作为** 生成式 UI 宿主开发者,
**我想要** 引擎按路径读取节点并支持数组索引,
**以便** 绑定组件正确取到值。

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-3.1 | WHEN `GetNode(path)` 的 path 为空或 `/` THEN 返回根节点（`DataModel.cpp:478-480`） | 边界 |
| AC-3.2 | WHEN `GetNode` 遍历遇到数组且段可解析为整数 THEN 按索引取值（`DataModel.cpp:492-504`） | 正常 |
| AC-3.3 | WHEN 数组索引越界或非数字 THEN `GetNode` 返回 `nullopt`（`DataModel.cpp:495-503`） | 异常 |
| AC-3.4 | WHEN 对象属性不存在 THEN `GetNode` 返回 `nullopt`（`DataModel.cpp:506-509`） | 异常 |

### US-4: 订阅索引与失效通知

**作为** 生成式 UI 宿主开发者,
**我想要** 数据更新后精确通知订阅组件,
**以便** UI 与数据同步且不误通知。

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-4.1 | WHEN 组件注册对某 path 的兴趣 THEN `RegisterInterest` 建立 `pathToComponents_[path]` 映射（`DataModel.cpp:527-531`） | 正常 |
| AC-4.2 | WHEN 更新路径命中注册路径（`IsPathAffected` 双向前缀匹配）THEN `NotifyPathUpdate` 推 `OnDataUpdate`（`DataModel.cpp:176-214,624-636`） | 正常 |
| AC-4.3 | WHEN 订阅组件 weak_ptr 已过期 THEN `CollectLiveSubscribers` 过滤掉（`DataModel.cpp:573-585`） | 边界 |
| AC-4.4 | WHEN 组件解绑 THEN `UnregisterInterest` 移除对应订阅（`DataModel.cpp:533-557`） | 正常 |
| AC-4.5 | WHEN 通知路径无任何订阅者 THEN `NotifyPathUpdate` 直接返回（`DataModel.cpp:628-631`） | 边界 |

## 验收追溯

| AC编号 | 关联规则 | 关联 Task | 验证方式 | 证据 |
|----|---------|----------|---------|------|
| AC-1.1,AC-1.2,AC-1.3,AC-1.4,AC-1.5 | R-1,R-2 | T-1 | C++ UT：ProcessUpdate 三态 | `DataModel.cpp:443-467` |
| AC-2.1,AC-2.2,AC-2.3 | R-3,R-4 | T-1 | C++ UT：深度/路径 | `BindingEngine.cpp:136-141`、`PathValidator.cpp:29-61` |
| AC-3.1,AC-3.2,AC-3.3,AC-3.4 | R-5 | T-1 | C++ UT：GetNode | `DataModel.cpp:471-523` |
| AC-4.1,AC-4.2,AC-4.3,AC-4.4,AC-4.5 | R-6,R-7 | T-1 | C++ UT：订阅/通知 | `DataModel.cpp:527-636` |

## 规则定义

| 规则ID | 类型 | 触发条件 | 预期行为 | 边界/约束 | 关联AC |
|--------|------|---------|---------|----------|--------|
| R-1 | 行为 | path+value 双有 | `UpdateByPath` 按路径更新 | path 空回退 `ReplaceAll` | AC-1.1 |
| R-2 | 行为 | 有 path 缺 value → 删除；缺 path 有 value → 替换 | `DeleteByPath` / `ReplaceAll` | 双缺→无效 | AC-1.2,AC-1.3,AC-1.4 |
| R-3 | 行为 | surfaceId 不匹配 | 忽略更新直接返回 | — | AC-1.5 |
| R-4 | 边界 | 嵌套深度 > 20 | 记 ERROR 日志（不拒绝更新） | MAX_DATA_MODEL_DEPTH=20 | AC-2.1 |
| R-5 | 异常 | 非法路径 | `IsValidDataPath` 返回 false | 仅 `[A-Za-z0-9_]`、以 `/` 开头 | AC-2.2,AC-2.3 |
| R-6 | 行为 | GetNode 按路径读取 | 对象/数组逐段取值 | 数组索引越界→nullopt | AC-3.1,AC-3.2,AC-3.3,AC-3.4 |
| R-7 | 行为 | 数据更新 | 前缀匹配通知订阅组件 | weak_ptr 过期过滤 | AC-4.1,AC-4.2,AC-4.3,AC-4.4,AC-4.5 |

## 验证映射

| 编号 | 对应规格项 | 验证方式 | 验证重点 |
|------|----------|---------|---------|
| VM-1 | AC-1.1,AC-1.2,AC-1.3,AC-1.4,AC-1.5 三态语义 | UT | path/value 组合分发 |
| VM-2 | AC-2.1,AC-2.2,AC-2.3 深度/路径 | UT | 20 层、非法路径拒绝 |
| VM-3 | AC-3.1,AC-3.2,AC-3.3,AC-3.4 GetNode | UT | 数组索引/对象遍历 |
| VM-4 | AC-4.1,AC-4.2,AC-4.3,AC-4.4,AC-4.5 订阅通知 | UT | 前缀匹配/过期过滤 |

## API 变更分析

> 存量补录，无新增/变更 API。

### 新增 API

N/A。

### 变更/废弃 API

N/A。

## 接口规格

### 接口定义

**`DataModel::ProcessUpdate(updateRequest)`（`DataModel.cpp:443`）**

| 属性 | 值 |
|------|-----|
| 函数签名 | `void ProcessUpdate(const DataModelUpdate& updateRequest)` |
| 返回值 | `void` |
| 开放范围 | 内部（C++） |
| 错误码 | N/A |
| 关联 AC | AC-1.1,AC-1.2,AC-1.3,AC-1.4,AC-1.5 |

**`DataModel::UpdateByPath / DeleteByPath / ReplaceAll`（`DataModel.h:67-69`）**

| 属性 | 值 |
|------|-----|
| 函数签名 | `bool UpdateByPath(const std::string&, const JsonValue&)` / `bool DeleteByPath(const std::string&)` / `bool ReplaceAll(const JsonValue&)` |
| 返回值 | `bool` — 是否成功 |
| 开放范围 | 内部（C++） |
| 关联 AC | AC-1.1,AC-1.2,AC-1.3 |

**参数约束**

| 参数 | 类型 | 必填 | 默认值 | 约束条件 |
|------|------|------|--------|---------|
| surfaceId | string | 是 | — | 与 DataModel 自身 surfaceId 一致 |
| path | string | 否 | `/` | JSON Pointer；空串表达全量 |
| value | JsonValue | 否 | — | 缺省表达删除 |

**行为场景**

| # | 触发条件 | 预期行为 | 关联 AC |
|---|----------|----------|---------|
| 1 | path+value | 按路径更新 | AC-1.1 |
| 2 | 仅 path | 删除 key | AC-1.2 |
| 3 | 仅 value（path 空） | 全量替换 | AC-1.3 |
| 4 | 双空 | 记 WARN，不更新 | AC-1.4 |
| 5 | surfaceId 不匹配 | 忽略返回 | AC-1.5 |

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
| 深度上限 | MAX_DATA_MODEL_DEPTH=20 | AC-2.1 |
| 订阅索引 | pathToComponents_ 前缀匹配通知 | AC-4.1,AC-4.2,AC-4.3,AC-4.4,AC-4.5 |

## 非功能性需求

| 类型 | 指标/阈值 | 验证方式 | 证据 |
|------|----------|---------|------|
| 安全 | 嵌套深度上限防栈溢出 | UT | `DataModel.h:53` |
| 性能 | 前缀匹配路径通知 O(订阅数) | UT | `DataModel.cpp:176-214` |
| 可靠性 | weak_ptr 过期过滤防悬挂 | UT | `DataModel.cpp:573-585` |

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
| 深色模式 | 否 | DataModel 与颜色无关 | — |
| 多窗口/分屏 | 否 | 数据模型内存态，无持久化 | — |
| 多用户 | 否 | — | — |
| 版本升级 | 否 | — | — |
| 生态兼容 | 是 | A2UI v0.9 updateDataModel 语义 | AC-1.1,AC-1.2,AC-1.3,AC-1.4,AC-1.5 |

## 行为场景（可选，Gherkin）

```gherkin
Feature: DataModel 读写契约
  作为 生成式 UI 宿主开发者
  我想要 用 path/value 表达增删改并精确通知订阅组件
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
      | (缺省) | (缺省) | 判无效，记 WARN |
```

## Spec 自审清单

- [x] 无"待定""TBD""TODO"等占位符
- [x] 所有 AC 使用 WHEN/THEN 格式，可独立测试
- [x] 范围边界明确（路径/表达式/变量语义归其余 Feat）
- [x] 无语义模糊表述
- [x] AC 与规则表交叉一致
- [x] 规则表每条通过质量检查

## context-references

```yaml
context-queries:
  - repo: "GenerativeUI/A2UIRender"
    query: "DataModel ProcessUpdate UpdateByPath DeleteByPath ReplaceAll 三态"
  - repo: "GenerativeUI/A2UIRender"
    query: "MAX_DATA_MODEL_DEPTH MeasureJsonDepth PathValidator IsValidDataPath"
  - repo: "GenerativeUI/A2UIRender"
    query: "RegisterInterest UnregisterInterest NotifyPathUpdate IsPathAffected CollectLiveSubscribers"
```

**关键文档：** `genui/src/main/cpp/data/DataModel.cpp`、`genui/src/main/cpp/data/BindingEngine.cpp`、`genui/src/main/cpp/data/PathValidator.cpp`
