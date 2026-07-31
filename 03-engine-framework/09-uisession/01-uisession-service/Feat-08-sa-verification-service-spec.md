# 特性规格

## 概述

| 属性 | 值 |
|------|-----|
| 特性名称 | SA验证服务与hidumper命令路由 |
| 特性编号 | Func-03-09-01-Feat-08 |
| 所属 Epic | UiSession |
| 优先级 | P1 |
| 目标版本 | API 12+ |
| SIG 归属 | ArkUI SIG |
| 状态 | Baselined |
| 复杂度 | 标准 |

> 本 Feat 锁定 UiSession SA 验证服务与 hidumper 命令路由：ui_sa SystemAbility（SA_ID=16666）注册、DUMP_MAP 25 条命令路由、getArkUIService via WindowManager::GetUIContentRemoteObj 获取服务代理、EnsureConnected 自动连接模式、hidumper 命令调用、-tofile 结果文件输出、Connect handler、GetVisibleInspectorTree handler、RegisterContentChangeCallback handler、page translate hidumper 命令。不涉及 IPC 安全框架（Feat-01）、InspectorTree 查询（Feat-02）、事件上报门控（Feat-03）、命令下发（Feat-04）、翻译能力（Feat-05）、内容变化检测（Feat-06）、查询辅助 Dump（Feat-07）。

## 本次变更范围（Delta）

> 历史规格补齐，补录已有实现的完整行为规格。

| 类型 | 内容 | 说明 |
|------|------|------|
| ADDED | ui_sa SystemAbility SA_ID=16666 注册规格 | ui_sa_service.cpp:1-754 SA 注册为 SystemAbility，SA_ID=16666 |
| ADDED | DUMP_MAP 25 条命令路由规格 | ui_sa_service.cpp:1-754 DUMP_MAP 映射 hidumper 命令至对应 handler |
| ADDED | getArkUIService via WindowManager::GetUIContentRemoteObj 规格 | ui_sa_service.cpp:1-754 通过 WindowManager::GetUIContentRemoteObj 获取 UiSession 服务代理 |
| ADDED | EnsureConnected 自动连接模式规格 | ui_sa_service.cpp:1-754 自动连接 UiSession 服务，连接失败时重试 |
| ADDED | hidumper 命令调用规格 | ui_sa_service.cpp:1-754 hidumper 命令通过 DUMP_MAP 路由至对应 handler |
| ADDED | -tofile 结果文件输出规格 | ui_sa_service.cpp:1-754 -tofile 命令将 dump 结果输出至文件 |
| ADDED | Connect handler 规格 | ui_sa_service.cpp:1-754 Connect handler 建立 SA 与 UiSession 服务连接 |
| ADDED | GetVisibleInspectorTree handler 规格 | ui_sa_service.cpp:1-754 GetVisibleInspectorTree handler 通过 hidumper 查询可见 Inspector 树 |
| ADDED | RegisterContentChangeCallback handler 规格 | ui_sa_service.cpp:1-754 RegisterContentChangeCallback handler 注册内容变化回调 |
| ADDED | page translate hidumper 命令规格 | ui_sa_service.cpp:1-754 page translate 相关 hidumper 命令路由 |

## 输入文档

- 关联设计：`03-engine-framework/09-uisession/01-uisession-service/design.md`
- 关联需求：已有能力补录（无独立 requirement.md）
- 源码定位（关键文件）：
  - `adapter/ohos/entrance/ui_sa/ui_sa_service.cpp:1-754` — SA 注册 + DUMP_MAP + EnsureConnected + handler 实现
  - `interfaces/inner_api/ui_session/ui_sa_interface.h:1-35` — SA 接口声明
  - `adapter/ohos/entrance/ui_sa/ui_sa.cfg:1-10` — SA 配置文件
  - `adapter/ohos/entrance/ui_sa/16666.json:1-13` — SA ID 注册文件

## 用户故事

### US-1: SA 注册与 DUMP_MAP 命令路由

- As a 系统服务开发者
- I want ui_sa 以 SA_ID=16666 注册为 SystemAbility，DUMP_MAP 路由 25 条 hidumper 命令至对应 handler
- So that hidumper 工具可通过 SA 服务调用 UiSession 各项诊断和查询能力

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-1.1 | WHEN ui_sa 以 SA_ID=16666 注册 THEN 系统可通过 SA ID 查找和连接 UiSession SA 服务。来源：`ui_sa_service.cpp:1-754` | 正常 |
| AC-1.2 | WHEN hidumper 命令被调用 THEN DUMP_MAP 路由命令至对应 handler 函数执行。来源：`ui_sa_service.cpp:1-754` | 正常 |
| AC-1.3 | WHEN hidumper 命令不在 DUMP_MAP 中 THEN 返回未知命令提示，不执行任何 handler。来源：`ui_sa_service.cpp:1-754` | 异常 |
| AC-1.4 | WHEN DUMP_MAP 包含 25 条命令 THEN 每条命令映射至唯一 handler 函数。来源：`ui_sa_service.cpp:1-754` | 正常 |

### US-2: getArkUIService 与 EnsureConnected 自动连接

- As a 系统服务开发者
- I want getArkUIService 通过 WindowManager::GetUIContentRemoteObj 获取 UiSession 服务代理，EnsureConnected 自动连接模式保证 SA 连接可用
- So that SA handler 可自动获取和维持与 UiSession 服务的连接

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-2.1 | WHEN getArkUIService 被调用 THEN 通过 WindowManager::GetUIContentRemoteObj 获取 UiSession 服务代理。来源：`ui_sa_service.cpp:1-754` | 正常 |
| AC-2.2 | WHEN EnsureConnected 检测连接可用 THEN 使用当前连接继续执行 handler。来源：`ui_sa_service.cpp:1-754` | 正常 |
| AC-2.3 | WHEN EnsureConnected 检测连接不可用 THEN 自动重新连接 UiSession 服务，连接失败时重试。来源：`ui_sa_service.cpp:1-754` | 恢复 |
| AC-2.4 | WHEN getArkUIService 获取服务代理失败 THEN handler 返回错误提示，不执行查询。来源：`ui_sa_service.cpp:1-754` | 异常 |

### US-3: Connect handler 与事件处理器注册

- As a 系统服务开发者
- I want Connect handler 建立 SA 与 UiSession 服务连接，GetVisibleInspectorTree、RegisterContentChangeCallback、page translate 等 handler 处理对应 hidumper 命令
- So that SA 可通过 handler 调用 UiSession 各项能力

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-3.1 | WHEN Connect handler 被调用 THEN 建立 SA 与 UiSession 服务的 IPC 连接。来源：`ui_sa_service.cpp:1-754` | 正常 |
| AC-3.2 | WHEN GetVisibleInspectorTree handler 被调用 THEN 通过 EnsureConnected 连接后查询可见 Inspector 树。来源：`ui_sa_service.cpp:1-754` | 正常 |
| AC-3.3 | WHEN RegisterContentChangeCallback handler 被调用 THEN 注册内容变化回调至 UiSession 服务。来源：`ui_sa_service.cpp:1-754` | 正常 |
| AC-3.4 | WHEN page translate hidumper 命令被调用 THEN 通过 DUMP_MAP 路由至 page translate handler 执行翻译操作。来源：`ui_sa_service.cpp:1-754` | 正常 |

### US-4: -tofile 结果文件输出

- As a SA 工具开发者
- I want -tofile 命令将 dump 结果输出至文件而非标准输出
- So that 大数据量 dump 结果可持久化存储而非仅终端显示

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-4.1 | WHEN hidumper 命令附加 -tofile 参数 THEN dump 结果输出至指定文件路径。来源：`ui_sa_service.cpp:1-754` | 正常 |
| AC-4.2 | WHEN -tofile 指定文件路径不可写 THEN dump 结果回退至标准输出。来源：`ui_sa_service.cpp:1-754` | 异常 |

## 验收追溯

| AC | 关联规则 | 关联 Task | 验证方式 | 证据 |
|----|----------|----------|----------|------|
| AC-1.1 | R-1 | TASK-SKELETON-8 | 集成测试 | 代码审查 |
| AC-1.2 | R-2 | TASK-SKELETON-8 | 集成测试 | 代码审查 |
| AC-1.3 | R-2 | TASK-SKELETON-8 | 集成测试：未知命令 | 代码审查 |
| AC-1.4 | R-2 | TASK-SKELETON-8 | 代码评审 | 代码审查 |
| AC-2.1 | R-3 | TASK-SKELETON-8 | 集成测试 | 代码审查 |
| AC-2.2 | R-4 | TASK-SKELETON-8 | 集成测试 | 代码审查 |
| AC-2.3 | R-4 | TASK-SKELETON-8 | 集成测试：重新连接 | 代码审查 |
| AC-2.4 | R-3 | TASK-SKELETON-8 | 集成测试 | 代码审查 |
| AC-3.1 | R-7 | TASK-SKELETON-8 | 集成测试 | 代码审查 |
| AC-3.2 | R-2 | TASK-SKELETON-8 | 集成测试 | 代码审查 |
| AC-3.3 | R-2 | TASK-SKELETON-8 | 集成测试 | 代码审查 |
| AC-3.4 | R-6 | TASK-SKELETON-8 | 集成测试 | 代码审查 |
| AC-4.1 | R-5 | TASK-SKELETON-8 | 集成测试 | 代码审查 |
| AC-4.2 | R-5 | TASK-SKELETON-8 | 集成测试 | 代码审查 |

## 规则定义

| 规则ID | 类型 | 触发条件 | 预期行为 | 边界/约束 | 关联AC |
|--------|------|----------|----------|-----------|--------|
| R-1 | 行为 | SA_ID 16666 注册 | ui_sa 以 SA_ID=16666 注册为 SystemAbility，系统可通过 SA ID 查找和连接 UiSession SA 服务。注册信息在 16666.json 和 ui_sa.cfg 中定义。 | SA_ID=16666 为固定值，不可更改 | AC-1.1 |
| R-2 | 行为 | DUMP_MAP 命令路由 | hidumper 命令通过 DUMP_MAP 路由至对应 handler 函数执行。DUMP_MAP 包含 25 条命令，每条映射至唯一 handler。未知命令返回提示不执行 handler。 | 25 条命令为固定映射表 | AC-1.2 / AC-1.3 / AC-1.4 / AC-3.2 / AC-3.3 |
| R-3 | 行为 | getArkUIService via WindowManager | 通过 WindowManager::GetUIContentRemoteObj 获取 UiSession 服务代理。获取失败时 handler 返回错误提示不执行查询。 | WindowManager::GetUIContentRemoteObj 为系统 API | AC-2.1 / AC-2.4 |
| R-4 | 恢复 | EnsureConnected 自动连接 | 检测连接可用：使用当前连接继续执行 handler。检测连接不可用：自动重新连接 UiSession 服务，连接失败时重试。 | 自动连接模式保证 SA handler 执行前连接可用 | AC-2.2 / AC-2.3 |
| R-5 | 行为 | -tofile 结果文件输出 | -tofile 命令将 dump 结果输出至指定文件路径持久化存储。指定文件路径不可写时回退至标准输出。 | -tofile 为 hidumper 标准参数 | AC-4.1 / AC-4.2 |
| R-6 | 行为 | page translate hidumper 命令 | page translate 相关 hidumper 命令通过 DUMP_MAP 路由至 page translate handler 执行翻译操作（Start/End/Reset/GetPageTranslateText 等）。 | 翻译命令集为 DUMP_MAP 子集 | AC-3.4 |
| R-7 | 行为 | Connect handler 建立 IPC 连接 | Connect handler 建立 SA 与 UiSession 服务的 IPC 连接，后续 handler 通过此连接执行查询。 | Connect 为 SA OnStart 生命周期事件处理器 | AC-3.1 |

## 验证映射

| 编号 | 对应规格项 | 验证方式 | 验证重点 |
|------|-----------|---------|---------|
| VM-1 | AC-1.1 / R-1 | 集成测试 | SA_ID 16666 注册与查找 |
| VM-2 | AC-1.2..1.4 / R-2 | 集成测试 | DUMP_MAP 25 条命令路由 + 未知命令处理 |
| VM-3 | AC-2.1 / AC-2.4 / R-3 | 集成测试 | getArkUIService via WindowManager |
| VM-4 | AC-2.2 / AC-2.3 / R-4 | 集成测试 | EnsureConnected 自动连接模式 |
| VM-5 | AC-3.1 / R-7 | 集成测试 | Connect handler 建立 IPC 连接 |
| VM-6 | AC-3.2 / AC-3.3 / AC-3.4 / R-2 / R-6 | 集成测试 | GetVisibleInspectorTree + RegisterContentChangeCallback + page translate handler |
| VM-7 | AC-4.1 / AC-4.2 / R-5 | 集成测试 | -tofile 结果文件输出 + 回退策略 |

## API 变更分析

### 新增 API

N/A，全部为 InnerApi（框架内部 SystemAbility 服务）。无 Public/System API 变更。

### 变更/废弃 API

无。

## 接口规格

### 接口定义

**getArkUIService**

| 属性 | 值 |
|------|-----|
| 函数签名 | `sptr<IRemoteObject> UiSaService::getArkUIService()` |
| 返回值 | `sptr<IRemoteObject>` — UiSession 服务代理或 null |
| 开放范围 | InnerApi |
| 错误码 | N/A |
| 关联 AC | AC-2.1 |

**参数约束**

| 参数 | 类型 | 必填 | 默认值 | 约束条件 |
|------|------|------|--------|---------|
| N/A | N/A | N/A | N/A | N/A |

**行为场景**

| # | 触发条件 | 预期行为 | 关联 AC |
|---|----------|----------|---------|
| 1 | WindowManager::GetUIContentRemoteObj 成功 | 返回 UiSession 服务代理 | AC-2.1 |
| 2 | WindowManager::GetUIContentRemoteObj 失败 | 返回 null，handler 返回错误提示 | AC-2.4 |

**EnsureConnected**

| 属性 | 值 |
|------|-----|
| 函数签名 | `bool UiSaService::EnsureConnected()` |
| 返回值 | `bool` — true(连接可用) / false(连接不可用) |
| 开放范围 | InnerApi |
| 错误码 | N/A |
| 关联 AC | AC-2.2 / AC-2.3 |

**参数约束**

| 参数 | 类型 | 必填 | 默认值 | 约束条件 |
|------|------|------|--------|---------|
| N/A | N/A | N/A | N/A | N/A |

**行为场景**

| # | 触发条件 | 预期行为 | 关联 AC |
|---|----------|----------|---------|
| 1 | 连接可用 | 返回 true，继续执行 handler | AC-2.2 |
| 2 | 连接不可用 | 自动重新连接，连接成功返回 true | AC-2.3 |
| 3 | 连接失败且重试耗尽 | 返回 false，handler 不执行 | AC-2.4 |

**DUMP_MAP 命令路由**

| 属性 | 值 |
|------|-----|
| 函数签名 | `void UiSaService::DumpRequest(const std::string& command, std::string& result)` |
| 返回值 | `void` |
| 开放范围 | InnerApi |
| 错误码 | N/A |
| 关联 AC | AC-1.2 |

**参数约束**

| 参数 | 类型 | 必填 | 默认值 | 约束条件 |
|------|------|------|--------|---------|
| command | std::string | 是 | N/A | hidumper 命令字符串 |
| result | std::string& | 是 | N/A | 出参，命令执行结果 |

**行为场景**

| # | 触发条件 | 预期行为 | 关联 AC |
|---|----------|----------|---------|
| 1 | 命令在 DUMP_MAP 中 | 路由至对应 handler 执行 | AC-1.2 |
| 2 | 命令不在 DUMP_MAP 中 | 返回未知命令提示 | AC-1.3 |
| 3 | 命令附加 -tofile | 结果输出至文件 | AC-4.1 |

## 兼容性声明

- **已有 API 行为变更:** 否 — 全部为已有实现补录
- **配置文件格式变更:** 否
- **数据存储格式变更:** 否
- **最低支持版本:** API 12
- **API 版本号策略:** 无 @since 标注（框架内部 SystemAbility 服务）

## 架构约束

| 关键约束 | 约束说明 | 影响 AC |
|---------|----------|---------|
| SA_ID=16666 固定值 | SA_ID 不可更改，硬编码在 16666.json 和 ui_sa.cfg 中 | AC-1.1 |
| DUMP_MAP 25 条命令固定映射 | 命令路由表为编译时固定映射，新增命令需更新 DUMP_MAP | AC-1.4 |
| getArkUIService 依赖 WindowManager | 服务代理获取依赖 WindowManager::GetUIContentRemoteObj 系统 API，API 不可用时获取失败 | AC-2.1 / AC-2.4 |
| EnsureConnected 自动连接模式 | handler 执行前自动检测并维持连接，连接不可用时重试 | AC-2.2 / AC-2.3 |
| -tofile 回退策略 | 文件路径不可写时回退至标准输出，保证 dump 结果不丢失 | AC-4.2 |

## 非功能性需求

| 类型 | 指标/阈值 | 验证方式 | 证据 |
|------|----------|----------|------|
| 性能 | DUMP_MAP 命令路由查找为 O(1) 常量时间 | 代码评审 | 代码审查 |
| 可观测 | hidumper 命令可通过 DUMP_MAP 路由追踪 | 代码评审 | 代码审查 |
| 可靠性 | EnsureConnected 自动连接保证 SA handler 连接可用 | 集成测试 | 代码审查 |
| 安全 | SA_ID=16666 固定值保证 SA 注册唯一性 | 代码评审 | 代码审查 |
| 定界定位 | DUMP_MAP 未知命令提示定位命令路由失败 | 集成测试 | 代码审查 |

## 多设备适配声明

无差异。

## 全局特性影响

| 特性 | 适用？ | 结论 | 关联场景 |
|------|--------|------|----------|
| 无障碍 | 不适用 | 无影响 — SA 服务为框架内部诊断能力 | — |
| 大字体 | 不适用 | 无影响 — SA 服务不涉及 UI 缩放 | — |
| 深色模式 | 不适用 | 无影响 — SA 服务不涉及颜色主题 | — |
| 多窗口 | 适用 | 每窗口独立 UiSession 服务代理，getArkUIService per-window | 多窗口 SA 连接 |
| 多用户 | 不适用 | 无影响 — SA 服务不区分用户 | — |
| 版本升级 | 适用 | 无影响 — 无 Public/System API 契约 | — |
| 生态兼容 | 适用 | 新增 hidumper 命令需同步更新 DUMP_MAP 映射表和 handler 实现 | DUMP_MAP 扩展 |

## Spec 自审清单

- [x] 无"待定""TBD""TODO"等占位符
- [x] 所有 AC 使用 WHEN/THEN 格式，可独立测试
- [x] 范围边界明确（做什么/不做什么清晰）
- [x] 无语义模糊表述（"快速""稳定""尽可能"等）
- [x] AC 与规则表交叉一致（每个 AC 至少关联一条规则，每条规则至少关联一个 AC）
- [x] 规则表每条通过 5 项质量检查（可复现/可观测/边界值/关联AC/无冲突）

## context-references

```yaml
context-queries:
  - repo: "openharmony/ace_engine"
    query: "ui_sa SystemAbility SA_ID=16666 注册 + DUMP_MAP 25 条命令路由 (ui_sa_service.cpp:1-754)"
  - repo: "openharmony/ace_engine"
    query: "getArkUIService via WindowManager::GetUIContentRemoteObj (ui_sa_service.cpp:1-754)"
  - repo: "openharmony/ace_engine"
    query: "EnsureConnected 自动连接模式 (ui_sa_service.cpp:1-754)"
  - repo: "openharmony/ace_engine"
    query: "Connect handler + GetVisibleInspectorTree + RegisterContentChangeCallback handler (ui_sa_service.cpp:1-754)"
  - repo: "openharmony/ace_engine"
    query: "-tofile 结果文件输出 (ui_sa_service.cpp:1-754)"
  - repo: "openharmony/ace_engine"
    query: "page translate hidumper 命令路由 (ui_sa_service.cpp:1-754)"
  - repo: "openharmony/ace_engine"
    query: "SA 接口声明 (ui_sa_interface.h:1-35)"
  - repo: "openharmony/ace_engine"
    query: "SA 配置文件 (ui_sa.cfg:1-10)"
  - repo: "openharmony/ace_engine"
    query: "SA ID 注册文件 (16666.json:1-13)"
```

**关键文档：**
- [design.md](03-engine-framework/09-uisession/01-uisession-service/design.md)
