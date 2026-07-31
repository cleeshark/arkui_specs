# 特性规格

## 概述

| 属性 | 值 |
|------|-----|
| 特性名称 | InspectorTree查询与Web子树聚合 |
| 特性编号 | Func-03-09-01-Feat-02 |
| 所属 Epic | UiSession |
| 优先级 | P1 |
| 目标版本 | API 12+ |
| SIG 归属 | ArkUI SIG |
| 状态 | Baselined |
| 复杂度 | 标准 |

> 本 Feat 锁定 InspectorTree 查询与 Web 子树聚合：GetInspectorTree / GetVisibleInspectorTree、ParamConfig 过滤配置、InspectorJsonValue cJSON RAII 包装（isRoot_ 所有权）、webTaskNums_ atomic 计数器异步子树聚合、AddValueForTree Web 子树注入、ReportInspectorTreeValue 单包上报。不涉及 IPC 安全框架（Feat-01）、事件上报门控（Feat-03）、命令下发与同步请求（Feat-04）。

## 本次变更范围（Delta）

> 历史规格补齐，补录已有实现的完整行为规格。

| 类型 | 内容 | 说明 |
|------|------|------|
| ADDED | GetInspectorTree JSON 创建与 ParamConfig 过滤规格 | ui_session_manager_ohos.cpp:939-955 Reset webTaskNums_ → Create jsonValue_ → inspectorFunction_(false, config) → PipelineContext PostSyncTaskTimeout(1500ms) |
| ADDED | GetVisibleInspectorTree 轻量裁剪版规格 | ui_session_manager_ohos.cpp:958-968 不重置 webTaskNums_，不创建 jsonValue_，仅裁剪可见节点 |
| ADDED | webTaskNums_ atomic 计数器异步子树聚合规格 | ui_session_manager_ohos.cpp:1023-1024 Web 子树报告 fetch_sub(1) 递减，归零后合并子树并发送最终 ReportInspectorTreeValue |
| ADDED | InspectorJsonValue cJSON RAII 所有权规格 | ui_session_json_util.h:1-86 isRoot_ 标志控制：root 析构 cJSON_Delete 释放整棵树，child 引用析构不释放 |
| ADDED | ParamConfig 7 字段过滤配置规格 | param_config.h:22-31 InspectorTree 过滤配置，控制节点属性输出范围 |
| ADDED | ReportInspectorTreeValue 单包上报规格 | ui_session_manager_ohos.cpp:939-1030 partNum=1, isLastPart=true，分包接口预留但当前始终单包 |

## 输入文档

- 关联设计：`03-engine-framework/09-uisession/01-uisession-service/design.md`
- 关联需求：已有能力补录（无独立 requirement.md）
- 源码定位（关键文件）：
  - `adapter/ohos/entrance/ui_session/ui_session_manager_ohos.cpp:939-1030` — GetInspectorTree / GetVisibleInspectorTree / webTaskNums_ 聚合
  - `interfaces/inner_api/ui_session/param_config.h:22-31` — ParamConfig 7 字段定义
  - `interfaces/inner_api/ui_session/ui_session_json_util.h:1-86` — InspectorJsonValue RAII + InspectorJsonUtil 工厂
  - `adapter/ohos/entrance/ui_session/ui_session_json_util.cpp` — InspectorJsonValue 实现（isRoot_ 所有权）
  - `frameworks/core/pipeline_ng/pipeline_context.cpp:7510` — GetInspectorTree / SimplifiedInspector 树生成 + 1500ms 超时

## 用户故事

### US-1: GetInspectorTree JSON 创建与 ParamConfig 过滤

- As a SA 工具开发者
- I want GetInspectorTree 根据 ParamConfig 配置过滤节点属性，生成完整 Inspector JSON 树并在 1500ms 超时内返回
- So that SA 工具可按需获取组件树结构信息，控制输出精度和范围

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-1.1 | WHEN GetInspectorTree(config) 被调用 THEN Reset webTaskNums_（atomic counter for Web subtree count），Create jsonValue_（InspectorJsonValue, isRoot_=true），调用 inspectorFunction_(false, config)。来源：`ui_session_manager_ohos.cpp:939-955` | 正常 |
| AC-1.2 | WHEN inspectorFunction_ 回调在 UI 线程执行 THEN PipelineContext::PostSyncTaskTimeout(1500ms) 触发 SimplifiedInspector::DumpSimplifyTreeWithParamConfig 生成过滤后的 Inspector JSON 树。来源：`pipeline_context.cpp:7510` | 正常 |
| AC-1.3 | WHEN ParamConfig 7 字段中任一字段为 true THEN InspectorTree 输出包含对应节点属性；全部为 false 时仅输出节点层级结构。来源：`param_config.h:22-31` | 正常 |
| AC-1.4 | WHEN PostSyncTaskTimeout 1500ms 超时 THEN InspectorTree 查询返回部分结果或空 JSON，SA 侧收到超时通知。来源：`pipeline_context.cpp:7510` | 边界 |

### US-2: GetVisibleInspectorTree 轻量裁剪版

- As a SA 工具开发者
- I want GetVisibleInspectorTree 仅返回当前可见节点（裁剪不可见和超出视口区域的节点），不涉及 Web 子树异步合并
- So that 快速获取当前可见 UI 结构，减少数据量

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-2.1 | WHEN GetVisibleInspectorTree(config) 被调用 THEN 不重置 webTaskNums_，不创建 jsonValue_，调用 inspectorFunction_(true, config)（onlyNeedVisible=true）。来源：`ui_session_manager_ohos.cpp:958-968` | 正常 |
| AC-2.2 | WHEN onlyNeedVisible=true 的 inspectorFunction_ 执行 THEN Pipeline 仅输出 rect 在视口范围内的节点（rect culling），跳过不可见节点。来源：`ui_session_manager_ohos.cpp:958-968` | 正常 |
| AC-2.3 | WHEN GetVisibleInspectorTree 执行 THEN 不等待 Web 子树异步合并，直接返回裁剪后的 Inspector JSON。来源：`ui_session_manager_ohos.cpp:958-968` | 正常 |

### US-3: Web 子树聚合与 AddValueForTree

- As a 框架维护者
- I want webTaskNums_ atomic 计数器控制异步 Web 子树合并时机，所有 Web 子树合并完成后才发送最终 ReportInspectorTreeValue
- So that InspectorTree 输出包含完整的 Web 组件子树信息，不出现缺失或顺序不一致

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-3.1 | WHEN GetInspectorTree 开始 THEN Reset webTaskNums_ 为 0，后续每个 Web 子树被发现时 fetch_add(1) 递增。来源：`ui_session_manager_ohos.cpp:1023-1024` | 正常 |
| AC-3.2 | WHEN Web 子树通过 AddValueForTree 注入 THEN jsonValue_->GetJsonObject(key) 获取目标位置，将 Web 子树 JSON 合入主树，webTaskNums_ fetch_sub(1) 递减。来源：`ui_session_manager_ohos.cpp:1023-1030` | 正常 |
| AC-3.3 | WHEN webTaskNums_ 递减至 0 THEN 所有 Web 子树合并完成，发送最终 ReportInspectorTreeValue(data, partNum=1, isLastPart=true) 至所有已连接 SA 进程。来源：`ui_session_manager_ohos.cpp:1023-1030` | 正常 |
| AC-3.4 | WHEN 无 Web 子树（webTaskNums_ 始终为 0） THEN 主树生成后直接发送 ReportInspectorTreeValue，不等待异步合并。来源：`ui_session_manager_ohos.cpp:939-955` | 边界 |

### US-4: InspectorJsonValue cJSON 所有权与 27 方法

- As a 框架开发者
- I want InspectorJsonValue 通过 isRoot_ 标志控制 cJSON 对象所有权：root 对象析构释放整棵树，child 引用析构不释放
- So that cJSON 内存管理清晰，避免 double-free 或泄漏

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-4.1 | WHEN InspectorJsonUtil::Create / CreateArray / CreateObject 被调用 THEN 创建 InspectorJsonValue（isRoot_=true），析构时调用 cJSON_Delete 释放整棵 cJSON 树。来源：`ui_session_json_util.h:30-70` | 正常 |
| AC-4.2 | WHEN InspectorJsonValue::GetArrayItem 被调用 THEN 返回 InspectorJsonValue（isRoot_=false），析构时不释放 cJSON 对象（非拥有引用）。GetJsonObject 返回 const JsonObject* 原始指针，非 InspectorJsonValue 包装。来源：`ui_session_json_util.h:30-70` | 正常 |
| AC-4.3 | WHEN isRoot_=false 的 child 引用在 root 对象析构后被访问 THEN 为 UB——规格要求 child 引用生命周期不超过 root 对象（ADR-7）。来源：`ui_session_json_util.h:30-70, ui_session_json_util.cpp` | 异常 |
| AC-4.4 | WHEN InspectorJsonValue 27 方法被使用 THEN Put(9 重载) + Replace + ToString + IsXxx(5) + Contains + GetJsonObject + GetString(2) + GetValue + GetArraySize + GetArrayItem + GetInt(2) + GetInt64(2) 均按 cJSON API 映射实现。来源：`ui_session_json_util.h:1-86` | 正常 |
| AC-4.5 | WHEN InspectorJsonUtil 5 静态工厂方法被使用 THEN Create / CreateArray / CreateObject / ParseJsonData / ParseJsonString 返回 isRoot_=true 的 InspectorJsonValue。来源：`ui_session_json_util.h` | 正常 |

## 验收追溯

| AC | 关联规则 | 关联 Task | 验证方式 | 证据 |
|----|----------|----------|----------|------|
| AC-1.1 | R-1 / R-5 | TASK-SKELETON-2 | 集成测试 | 代码审查 |
| AC-1.2 | R-1 / R-7 | TASK-SKELETON-2 | 集成测试：PostSyncTaskTimeout 1500ms | 代码审查 |
| AC-1.3 | R-5 | TASK-SKELETON-2 | 集成测试：ParamConfig 字段对照 | 代码审查 |
| AC-1.4 | R-7 | TASK-SKELETON-2 | 集成测试：超时场景 | 代码审查 |
| AC-2.1 | R-1 | TASK-SKELETON-2 | 集成测试 | 代码审查 |
| AC-2.2 | R-2 | TASK-SKELETON-2 | 集成测试：rect culling | 代码审查 |
| AC-2.3 | R-2 | TASK-SKELETON-2 | 代码评审 | 代码审查 |
| AC-3.1 | R-2 | TASK-SKELETON-2 | 集成测试 | 代码审查 |
| AC-3.2 | R-3 | TASK-SKELETON-2 | 集成测试：AddValueForTree | 代码审查 |
| AC-3.3 | R-4 | TASK-SKELETON-2 | 集成测试：webTaskNums_ 归零后上报 | 代码审查 |
| AC-3.4 | R-4 | TASK-SKELETON-2 | 代码评审 | 代码审查 |
| AC-4.1 | R-6 | TASK-SKELETON-2 | 单元测试 | 代码审查 |
| AC-4.2 | R-6 | TASK-SKELETON-2 | 单元测试 | 代码审查 |
| AC-4.3 | R-8 | TASK-SKELETON-2 | 代码评审（ADR-7 约束） | 代码审查 |
| AC-4.4 | R-6 | TASK-SKELETON-2 | 代码评审 | 代码审查 |
| AC-4.5 | R-6 | TASK-SKELETON-2 | 代码评审 | 代码审查 |

## 规则定义

| 规则ID | 类型 | 触发条件 | 预期行为 | 边界/约束 | 关联AC |
|--------|------|----------|----------|-----------|--------|
| R-1 | 行为 | GetInspectorTree(config) 调用 | Reset webTaskNums_ → Create jsonValue_(isRoot_=true) → inspectorFunction_(false, config) → PipelineContext PostSyncTaskTimeout(1500ms) 生成 SimplifiedInspector 树。 | 1500ms 超时限制（R-7） | AC-1.1 / AC-1.2 / AC-2.1 |
| R-2 | 行为 | GetVisibleInspectorTree(config) 调用 | 不重置 webTaskNums_，不创建 jsonValue_，调用 inspectorFunction_(true, config)（onlyNeedVisible=true），仅裁剪可见节点（rect culling），不等待 Web 子树合并。 | 不涉及 Web 子树异步合并 | AC-2.1 / AC-2.2 / AC-2.3 / AC-3.1 |
| R-3 | 行为 | Web 子树 AddValueForTree 注入 | jsonValue_->GetJsonObject(key) 获取目标位置 → 合入 Web 子树 JSON → webTaskNums_ fetch_sub(1) 递减。 | AddValueForTree 必须在 webTaskNums_ > 0 时调用 | AC-3.2 |
| R-4 | 行为 | webTaskNums_ 递减至 0 | 所有 Web 子树合并完成，发送 ReportInspectorTreeValue(data, partNum=1, isLastPart=true) 至所有已连接 SA 进程。单包上报，分包接口预留（ADR-4）。 | 无 Web 子树时 webTaskNums_ 始终为 0，主树直接上报 | AC-3.3 / AC-3.4 |
| R-5 | 行为 | ParamConfig 7 字段过滤 | ParamConfig 7 字段控制 InspectorTree 输出精度：任一字段为 true 时输出对应属性，全部为 false 时仅输出节点层级结构。 | ParamConfig 默认值需与 PipelineContext SimplifiedInspector 过滤逻辑一致 | AC-1.3 |
| R-6 | 行为 | InspectorJsonValue cJSON 所有权 | isRoot_=true 的 root 对象析构时 cJSON_Delete 释放整棵树；isRoot_=false 的 child 引用析构时不释放（非拥有）。27 方法 + InspectorJsonUtil 5 工厂方法按 cJSON API 映射实现。GetJsonObject 返回 const JsonObject* 原始指针，GetArrayItem 返回 InspectorJsonValue(isRoot_=false)。 | cJSON 库不支持引用计数，isRoot_ 方式最简单且与 cJSON_Delete 语义匹配（ADR-7） | AC-4.1 / AC-4.2 / AC-4.4 / AC-4.5 |
| R-7 | 边界 | PostSyncTaskTimeout 1500ms 超时 | InspectorTree 查询在 1500ms 内必须完成；超时返回部分结果或空 JSON。 | 超时时间由 PipelineContext::PostSyncTaskTimeout 固定参数控制 | AC-1.4 |
| R-8 | 异常 | isRoot_=false child 引用在 root 析构后访问 | 为 UB——规格要求 child 引用生命周期不超过 root 对象（ADR-7）。 | cJSON 库无引用计数，child 必须在 root 存活期间使用 | AC-4.3 |

## 验证映射

| VM编号 | AC / 规则 | 验证手段 | 位置 / 用例名 |
|-------|----------|---------|---------------|
| VM-1 | AC-1.1 / R-1 / R-5 | 集成测试 | GetInspectorTree 流程对照 |
| VM-2 | AC-1.2 / R-1 / R-7 | 集成测试 | PostSyncTaskTimeout 1500ms 超时验证 |
| VM-3 | AC-1.3 / R-5 | 集成测试 | ParamConfig 字段过滤对照 |
| VM-4 | AC-2.1..2.3 / R-2 | 集成测试 | GetVisibleInspectorTree rect culling 验证 |
| VM-5 | AC-3.1..3.4 / R-2 / R-3 / R-4 | 集成测试 | webTaskNums_ 聚合 + AddValueForTree 合入 |
| VM-6 | AC-4.1..4.5 / R-6 / R-8 | 单元测试 | InspectorJsonValue isRoot_ 所有权 + 27 方法 |

## API 变更分析

### 新增 API

N/A，全部为 InnerApi（框架内部 IPC 接口）。无 Public/System API 变更。

### 变更/废弃 API

无。

## 接口规格

### 接口定义

**GetInspectorTree**

| 属性 | 值 |
|------|-----|
| 函数签名 | `int32_t UiSessionManagerOhos::GetInspectorTree(const ParamConfig& config)` |
| 返回值 | `int32_t` — ERR_OK 或错误码 |
| 开放范围 | InnerApi |
| 错误码 | N/A |
| 关联 AC | AC-1.1 / AC-1.2 / AC-1.3 |

**参数约束**

| 参数 | 类型 | 必填 | 默认值 | 约束条件 |
|------|------|------|--------|---------|
| config | ParamConfig | 是 | N/A | 7 字段布尔配置，控制 InspectorTree 输出属性范围 |

**行为场景**

| # | 触发条件 | 预期行为 | 关联 AC |
|---|----------|----------|---------|
| 1 | SA 进程发起 GetInspectorTree(config) | Reset webTaskNums_ → Create jsonValue_ → inspectorFunction_(false, config) → PostSyncTaskTimeout(1500ms) → 等待 Web 子树合并 → ReportInspectorTreeValue | AC-1.1 |
| 2 | PostSyncTaskTimeout 超时 1500ms | 返回部分结果或空 JSON | AC-1.4 |

**GetVisibleInspectorTree**

| 属性 | 值 |
|------|-----|
| 函数签名 | `int32_t UiSessionManagerOhos::GetVisibleInspectorTree(const ParamConfig& config)` |
| 返回值 | `int32_t` — ERR_OK 或错误码 |
| 开放范围 | InnerApi |
| 错误码 | N/A |
| 关联 AC | AC-2.1 / AC-2.2 |

**行为场景**

| # | 触发条件 | 预期行为 | 关联 AC |
|---|----------|----------|---------|
| 1 | SA 进程发起 GetVisibleInspectorTree(config) | inspectorFunction_(true, config) → 仅裁剪可见节点 → 不等待 Web 子树 → 直接返回 | AC-2.1 |
| 2 | 无 Web 子树参与 | 不创建 jsonValue_，不重置 webTaskNums_ | AC-2.3 |

**InspectorJsonValue**

| 属性 | 值 |
|------|-----|
| 函数签名 | `InspectorJsonValue::InspectorJsonValue(cJSON* object, bool isRoot)` |
| 返回值 | N/A（构造函数） |
| 开放范围 | InnerApi |
| 错误码 | N/A |
| 关联 AC | AC-4.1 / AC-4.2 |

**参数约束**

| 参数 | 类型 | 必填 | 默认值 | 约束条件 |
|------|------|------|--------|---------|
| object | cJSON* | 是 | N/A | 非 nullptr |
| isRoot | bool | 是 | false | true 时析构调用 cJSON_Delete；false 时析构不释放 |

**行为场景**

| # | 触发条件 | 预期行为 | 关联 AC |
|---|----------|----------|---------|
| 1 | InspectorJsonUtil::Create 创建 root 对象 | isRoot_=true → 析构时 cJSON_Delete 释放整棵树 | AC-4.1 |
| 2 | GetArrayItem 创建 child 引用 | isRoot_=false → 析构时不释放（非拥有引用） | AC-4.2 |
| 3 | GetJsonObject 返回原始指针 | 返回 const JsonObject*（cJSON 原始指针），非 InspectorJsonValue 包装 | AC-4.2 |
| 4 | child 引用在 root 析构后访问 | UB — 规格要求 child 生命周期不超过 root | AC-4.3 |

## 兼容性声明

- **已有 API 行为变更:** 否 — 全部为已有实现补录
- **配置文件格式变更:** 否
- **数据存储格式变更:** 否
- **最低支持版本:** API 12
- **API 版本号策略:** 无 @since 标注（框架内部 IPC 能力）

## 架构约束

| 关键约束 | 约束说明 | 影响 AC |
|---------|----------|---------|
| InspectorTree 单包上报（分包接口预留） | ReportInspectorTreeValue 接口支持 partNum / isLastPart 参数，但当前 InspectorTree 始终单包发送 (partNum=1, isLastPart=true)。仅 HitTest 实际使用 128KB 分包（ADR-4） | AC-3.3 |
| InspectorJsonValue child 引用生命周期约束 | isRoot_=false 的 child 引用必须在 root 对象存活期间使用，root 析构后访问为 UB（ADR-7） | AC-4.3 |
| inspectorFunction_ mutex 互斥保护 | inspectorFunction_ 回调注册和使用受 inspectorFunctionMutex_ 保护，防止并发注册/调用 | AC-1.1 |
| 1500ms PostSyncTaskTimeout 固定超时 | InspectorTree 查询超时时间由 PipelineContext::PostSyncTaskTimeout 固定 1500ms 参数控制，不可配置 | AC-1.4 |
| cJSON 不支持引用计数 | cJSON 库不支持引用计数机制，isRoot_ 方式是所有权管理的唯一可行方案 | AC-4.1 |

## 非功能性需求

| 类型 | 指标/阈值 | 验证方式 | 证据 |
|------|----------|----------|------|
| 性能 | InspectorTree 查询 1500ms 超时内完成 | PostSyncTaskTimeout 计时 | 集成测试 |
| 可观测 | InspectorTree 输出 JSON 可通过 UiReportProxy 验证 | IPC 数据抓取 | 集成测试 |
| 可靠性 | webTaskNums_ atomic 计数器保证异步子树合并完整性 | atomic 操作验证 | 代码评审 |
| 内存 | InspectorJsonValue isRoot_ root 析构保证 cJSON 整棵树释放 | 单元测试 | 代码审查 |
| 定界定位 | child 引用 UB 风险通过 RAII 设计和 lifetime 约束规避 | 代码评审 | 代码审查 |

## 多设备适配声明

无差异。

## 全局特性影响

| 特性 | 适用？ | 结论 | 关联场景 |
|------|--------|------|----------|
| 无障碍 | 不适用 | 无影响 — InspectorTree 为框架内部调试能力 | — |
| 大字体 | 不适用 | 无影响 — InspectorTree 不涉及 UI 缩放 | — |
| 深色模式 | 不适用 | 无影响 — InspectorTree 不涉及颜色主题 | — |
| 多窗口 | 适用 | 每窗口独立 InspectorTree 查询，webTaskNums_ 每次查询重置 | 多窗口 Inspector |
| 多用户 | 不适用 | 无影响 — InspectorTree 不区分用户 | — |
| 版本升级 | 适用 | 无影响 — 无 Public/System API 契约 | — |
| 生态兼容 | 适用 | ParamConfig 字段扩展需同步更新 SimplifiedInspector 过滤逻辑 | InspectorTree 配置扩展 |

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
    query: "UiSessionManagerOhos GetInspectorTree / GetVisibleInspectorTree 流程 (ui_session_manager_ohos.cpp:939-1030)"
  - repo: "openharmony/ace_engine"
    query: "webTaskNums_ atomic 计数器 + AddValueForTree Web 子树合并 (ui_session_manager_ohos.cpp:1023-1030)"
  - repo: "openharmony/ace_engine"
    query: "ParamConfig 7 字段定义 (param_config.h:22-31)"
  - repo: "openharmony/ace_engine"
    query: "InspectorJsonValue RAII 包装 + isRoot_ 所有权控制 (ui_session_json_util.h:1-86)"
  - repo: "openharmony/ace_engine"
    query: "InspectorJsonValue 实现细节 (ui_session_json_util.cpp)"
  - repo: "openharmony/ace_engine"
    query: "InspectorJsonUtil 5 静态工厂方法 (ui_session_json_util.h)"
  - repo: "openharmony/ace_engine"
    query: "PipelineContext::GetInspectorTree + SimplifiedInspector 树生成 + 1500ms 超时 (pipeline_context.cpp:7510)"
  - repo: "openharmony/ace_engine"
    query: "ReportInspectorTreeValue 单包上报 + 分包接口预留 (ui_session_manager_ohos.cpp:939-1030)"
```

**关键文档：**
- [design.md](03-engine-framework/09-uisession/01-uisession-service/design.md)
