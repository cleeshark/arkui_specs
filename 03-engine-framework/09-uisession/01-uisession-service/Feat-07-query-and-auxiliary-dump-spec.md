# 特性规格

## 概述

| 属性 | 值 |
|------|-----|
| 特性名称 | 查询能力与辅助Dump |
| 特性编号 | Func-03-09-01-Feat-07 |
| 所属 Epic | UiSession |
| 优先级 | P1 |
| 目标版本 | API 12+ |
| SIG 归属 | ArkUI SIG |
| 状态 | Baselined |
| 复杂度 | 标准 |

> 本 Feat 锁定 UiSession 查询能力与辅助 Dump：HitTest 分段 IPC（ONCE_IPC_SEND_DATA_MAX_SIZE=131072, 128KB 分段）、PixelMap 广播上报、GetMultiImagesById 双错误码（innerErrorCode + errorIndex）、GetCurrentPageName 同步查询、GetStateMgmtInfo 状态管理查询、GetWebInfoByRequest + WebRequestErrorCode、ExeAppAIFunction + AI_CALL 错误码 0-5、GetSpecifiedContentOffsets、HighlightSpecifiedContent、DumpViewData autofill 链。不涉及 IPC 安全框架（Feat-01）、InspectorTree 查询（Feat-02）、事件上报门控（Feat-03）、命令下发（Feat-04）、翻译能力（Feat-05）、内容变化检测（Feat-06）、SA 验证服务（Feat-08）。

## 本次变更范围（Delta）

> 历史规格补齐，补录已有实现的完整行为规格。

| 类型 | 内容 | 说明 |
|------|------|------|
| ADDED | HitTest 分段 IPC 规格 | ui_session_manager_ohos.cpp:1086-1118 数据量超过 ONCE_IPC_SEND_DATA_MAX_SIZE=131072 时分段发送 |
| ADDED | PixelMap 广播上报规格 | ui_session_manager_ohos.cpp:1676-1783 PixelMap 数据广播至所有已注册 SA 进程 |
| ADDED | GetMultiImagesById 双错误码规格 | ui_session_manager_ohos.cpp:1676-1783 innerErrorCode（全局）+ errorIndex（逐图）双错误码 |
| ADDED | GetCurrentPageName 同步查询规格 | ui_session_manager_ohos.cpp:1921-2001 同步查询当前页面名称 |
| ADDED | GetStateMgmtInfo 状态管理查询规格 | ui_session_manager_ohos.cpp:1921-2001 状态管理信息查询 |
| ADDED | GetWebInfoByRequest + WebRequestErrorCode 规格 | ui_session_manager_ohos.cpp:1676-1783 Web 信息查询 + WebRequestErrorCode 错误码 |
| ADDED | ExeAppAIFunction + AI_CALL 错误码 0-5 规格 | ui_session_manager_ohos.cpp:1921-2001 AI 函数执行 + 错误码 0(成功) / 1(参数错误) / 2(不支持) / 3(超时) / 4(内部错误) / 5(权限不足) |
| ADDED | GetSpecifiedContentOffsets 规格 | ui_session_manager_ohos.cpp:1921-2001 查询指定内容偏移量 |
| ADDED | HighlightSpecifiedContent 规格 | ui_session_manager_ohos.cpp:1921-2001 高亮指定内容 |
| ADDED | DumpViewData autofill 链规格 | ui_content_impl.cpp:5321-5373 autofill 数据链路 dump |

## 输入文档

- 关联设计：`03-engine-framework/09-uisession/01-uisession-service/design.md`
- 关联需求：已有能力补录（无独立 requirement.md）
- 源码定位（关键文件）：
  - `adapter/ohos/entrance/ui_session/ui_session_manager_ohos.cpp:1086-1118` — HitTest 分段 IPC
  - `adapter/ohos/entrance/ui_session/ui_session_manager_ohos.cpp:1676-1783` — PixelMap / GetMultiImagesById / GetWebInfoByRequest
  - `adapter/ohos/entrance/ui_session/ui_session_manager_ohos.cpp:1921-2001` — GetCurrentPageName / GetStateMgmtInfo / ExeAppAIFunction / GetSpecifiedContentOffsets / HighlightSpecifiedContent
  - `adapter/ohos/entrance/ui_content_impl.cpp:5321-5373` — DumpViewData autofill 链

## 用户故事

### US-1: HitTest 分段 IPC 查询

- As a SA 工具开发者
- I want HitTest 查询结果数据量超过 ONCE_IPC_SEND_DATA_MAX_SIZE=131072 时分段发送
- So that 大数据量 HitTest 查询结果可通过 IPC 正常传输，不会因单次 IPC 数据量限制而丢失

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-1.1 | WHEN HitTest 查询结果数据量 <= ONCE_IPC_SEND_DATA_MAX_SIZE=131072 THEN 单次 IPC 发送全部结果。来源：`ui_session_manager_ohos.cpp:1086-1118` | 正常 |
| AC-1.2 | WHEN HitTest 查询结果数据量 > ONCE_IPC_SEND_DATA_MAX_SIZE=131072 THEN 分段 IPC 发送结果，每段不超过 131072 字节。来源：`ui_session_manager_ohos.cpp:1086-1118` | 正常 |
| AC-1.3 | WHEN HitTest 分段 IPC 发送中接收端中断 THEN 已发送段数据丢失，未发送段不再发送（无重试机制）。来源：`ui_session_manager_ohos.cpp:1086-1118` | 异常 |

### US-2: PixelMap 广播与 GetMultiImagesById 双错误码

- As a SA 工具开发者
- I want PixelMap 数据广播至所有已注册 SA 进程，GetMultiImagesById 返回双错误码（innerErrorCode 全局错误 + errorIndex 逐图错误）
- So that SA 工具可获取图片数据并精确定位错误来源

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-2.1 | WHEN PixelMap 数据上报 THEN 广播至所有已注册 SA 进程（非定向发送）。来源：`ui_session_manager_ohos.cpp:1676-1783` | 正常 |
| AC-2.2 | WHEN GetMultiImagesById 成功获取所有图片 THEN innerErrorCode=0（全局成功），errorIndex=-1（无逐图错误）。来源：`ui_session_manager_ohos.cpp:1676-1783` | 正常 |
| AC-2.3 | WHEN GetMultiImagesById 全局失败（如未注册回调） THEN innerErrorCode 为全局错误码（非 0），errorIndex=-1（无逐图错误）。来源：`ui_session_manager_ohos.cpp:1676-1783` | 异常 |
| AC-2.4 | WHEN GetMultiImagesById 逐图失败（某图获取失败） THEN innerErrorCode=0（全局成功），errorIndex 为失败图片索引。来源：`ui_session_manager_ohos.cpp:1676-1783` | 异常 |

### US-3: GetCurrentPageName 与 GetStateMgmtInfo 同步查询

- As a SA 工具开发者
- I want GetCurrentPageName 同步查询当前页面名称，GetStateMgmtInfo 查询状态管理信息
- So that SA 工具可同步获取当前页面名称和状态管理信息

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-3.1 | WHEN GetCurrentPageName 被调用 THEN 同步查询并返回当前页面名称。来源：`ui_session_manager_ohos.cpp:1921-2001` | 正常 |
| AC-3.2 | WHEN GetCurrentPageName 页面名称为空 THEN 返回空字符串。来源：`ui_session_manager_ohos.cpp:1921-2001` | 边界 |
| AC-3.3 | WHEN GetStateMgmtInfo 被调用 THEN 同步查询并返回状态管理信息。来源：`ui_session_manager_ohos.cpp:1921-2001` | 正常 |

### US-4: GetWebInfoByRequest 与 ExeAppAIFunction

- As a SA 工具开发者
- I want GetWebInfoByRequest 查询 Web 信息并返回 WebRequestErrorCode，ExeAppAIFunction 执行 AI 函数并返回错误码 0-5
- So that SA 工具可查询 Web 组件信息和执行 AI 函数，错误码区分不同失败类型

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-4.1 | WHEN GetWebInfoByRequest 成功 THEN 返回 Web 信息数据，WebRequestErrorCode=0（成功）。来源：`ui_session_manager_ohos.cpp:1676-1783` | 正常 |
| AC-4.2 | WHEN GetWebInfoByRequest 失败 THEN 返回 WebRequestErrorCode 标示失败类型。来源：`ui_session_manager_ohos.cpp:1676-1783` | 异常 |
| AC-4.3 | WHEN ExeAppAIFunction 成功 THEN 返回 AI 函数执行结果，错误码=0（成功）。来源：`ui_session_manager_ohos.cpp:1921-2001` | 正常 |
| AC-4.4 | WHEN ExeAppAIFunction 参数错误 THEN 返回错误码=1（参数错误）。来源：`ui_session_manager_ohos.cpp:1921-2001` | 异常 |
| AC-4.5 | WHEN ExeAppAIFunction 功能不支持 THEN 返回错误码=2（不支持）。来源：`ui_session_manager_ohos.cpp:1921-2001` | 异常 |
| AC-4.6 | WHEN ExeAppAIFunction 执行超时 THEN 返回错误码=3（超时）。来源：`ui_session_manager_ohos.cpp:1921-2001` | 异常 |
| AC-4.7 | WHEN ExeAppAIFunction 内部错误 THEN 返回错误码=4（内部错误）。来源：`ui_session_manager_ohos.cpp:1921-2001` | 异常 |
| AC-4.8 | WHEN ExeAppAIFunction 权限不足 THEN 返回错误码=5（权限不足）。来源：`ui_session_manager_ohos.cpp:1921-2001` | 异常 |

### US-5: GetSpecifiedContentOffsets 与 HighlightSpecifiedContent

- As a SA 工具开发者
- I want GetSpecifiedContentOffsets 查询指定内容偏移量，HighlightSpecifiedContent 高亮指定内容
- So that SA 工具可定位页面内容位置和执行内容高亮

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-5.1 | WHEN GetSpecifiedContentOffsets 被调用 THEN 返回指定内容的偏移量信息。来源：`ui_session_manager_ohos.cpp:1921-2001` | 正常 |
| AC-5.2 | WHEN GetSpecifiedContentOffsets 内容不存在 THEN 返回空偏移量列表。来源：`ui_session_manager_ohos.cpp:1921-2001` | 边界 |
| AC-5.3 | WHEN HighlightSpecifiedContent 被调用 THEN 高亮指定内容区域。来源：`ui_session_manager_ohos.cpp:1921-2001` | 正常 |
| AC-5.4 | WHEN HighlightSpecifiedContent 内容不存在 THEN 不执行高亮，返回默认值。来源：`ui_session_manager_ohos.cpp:1921-2001` | 边界 |

### US-6: DumpViewData autofill 链

- As a 框架维护者
- I want DumpViewData autofill 链路 dump 支持表单自动填充数据链路追踪
- So that 框架维护者可通过 DumpViewData 追踪 autofill 数据链路

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-6.1 | WHEN DumpViewData autofill 链被触发 THEN 追踪 autofill 数据链路从数据源到 UI 节点的完整路径。来源：`ui_content_impl.cpp:5321-5373` | 正常 |

## 验收追溯

| AC | 关联规则 | 关联 Task | 验证方式 | 证据 |
|----|----------|----------|----------|------|
| AC-1.1 | R-1 | TASK-SKELETON-7 | 集成测试 | 代码审查 |
| AC-1.2 | R-1 | TASK-SKELETON-7 | 集成测试 | 代码审查 |
| AC-1.3 | R-1 | TASK-SKELETON-7 | 代码评审（无重试机制） | 代码审查 |
| AC-2.1 | R-2 | TASK-SKELETON-7 | 集成测试 | 代码审查 |
| AC-2.2 | R-3 | TASK-SKELETON-7 | 集成测试 | 代码审查 |
| AC-2.3 | R-3 | TASK-SKELETON-7 | 集成测试：全局错误 | 代码审查 |
| AC-2.4 | R-3 | TASK-SKELETON-7 | 集成测试：逐图错误 | 代码审查 |
| AC-3.1 | R-4 | TASK-SKELETON-7 | 集成测试 | 代码审查 |
| AC-3.2 | R-4 | TASK-SKELETON-7 | 集成测试 | 代码审查 |
| AC-3.3 | R-5 | TASK-SKELETON-7 | 集成测试 | 代码审查 |
| AC-4.1 | R-6 | TASK-SKELETON-7 | 集成测试 | 代码审查 |
| AC-4.2 | R-6 | TASK-SKELETON-7 | 集成测试 | 代码审查 |
| AC-4.3 | R-7 | TASK-SKELETON-7 | 集成测试 | 代码审查 |
| AC-4.4 | R-7 | TASK-SKELETON-7 | 集成测试 | 代码审查 |
| AC-4.5 | R-7 | TASK-SKELETON-7 | 集成测试 | 代码审查 |
| AC-4.6 | R-7 | TASK-SKELETON-7 | 集成测试 | 代码审查 |
| AC-4.7 | R-7 | TASK-SKELETON-7 | 集成测试 | 代码审查 |
| AC-4.8 | R-7 | TASK-SKELETON-7 | 集成测试 | 代码审查 |
| AC-5.1 | R-8 | TASK-SKELETON-7 | 集成测试 | 代码审查 |
| AC-5.2 | R-8 | TASK-SKELETON-7 | 集成测试 | 代码审查 |
| AC-5.3 | R-9 | TASK-SKELETON-7 | 集成测试 | 代码审查 |
| AC-5.4 | R-9 | TASK-SKELETON-7 | 集成测试 | 代码审查 |
| AC-6.1 | R-10 | TASK-SKELETON-7 | 代码评审 | 代码审查 |

## 规则定义

| 规则ID | 类型 | 触发条件 | 预期行为 | 边界/约束 | 关联AC |
|--------|------|----------|----------|-----------|--------|
| R-1 | 行为 | HitTest 分段 IPC (ONCE_IPC_SEND_DATA_MAX_SIZE=131072) | 数据量 <= 131072：单次 IPC 发送全部结果。数据量 > 131072：分段 IPC 发送，每段不超过 131072 字节。接收端中断时已发送段数据丢失，无重试机制。 | 131072 字节 = 128KB + 8KB 头部空间；分段无重试 | AC-1.1 / AC-1.2 / AC-1.3 |
| R-2 | 行为 | PixelMap 广播上报 | PixelMap 数据广播至所有已注册 SA 进程（非定向发送），遍历 reportObjectMap_ 发送。 | 广播模式，不做定向发送 | AC-2.1 |
| R-3 | 行为 | GetMultiImagesById 双错误码 | innerErrorCode 全局错误码：0=全局成功，非 0=全局失败（如未注册回调）。errorIndex 逐图错误索引：-1=无逐图错误，>=0=失败图片索引。全局成功 + 逐图失败：innerErrorCode=0, errorIndex=失败索引。 | 双错误码设计：全局与逐图错误独立表示 | AC-2.2 / AC-2.3 / AC-2.4 |
| R-4 | 行为 | GetCurrentPageName 同步查询 | 同步查询并返回当前页面名称。页面名称为空时返回空字符串。 | 同步查询，不涉及 SyncRequestGuard 门控 | AC-3.1 / AC-3.2 |
| R-5 | 行为 | GetStateMgmtInfo 状态管理查询 | 同步查询并返回状态管理信息。 | 状态管理信息包含组件状态相关数据 | AC-3.3 |
| R-6 | 异常 | GetWebInfoByRequest + WebRequestErrorCode | 成功：返回 Web 信息数据 + WebRequestErrorCode=0。失败：返回 WebRequestErrorCode 标示失败类型。 | WebRequestErrorCode 定义于 ui_content_service_interface.h | AC-4.1 / AC-4.2 |
| R-7 | 异常 | ExeAppAIFunction + AI_CALL 错误码 0-5 | 0=成功, 1=参数错误, 2=不支持, 3=超时, 4=内部错误, 5=权限不足。成功返回 AI 函数执行结果 + 错误码=0。失败返回对应错误码。 | 6 种错误码覆盖 AI 函数执行全场景 | AC-4.3 / AC-4.4 / AC-4.5 / AC-4.6 / AC-4.7 / AC-4.8 |
| R-8 | 行为 | GetSpecifiedContentOffsets | 返回指定内容的偏移量信息。内容不存在时返回空偏移量列表。 | 偏移量信息包含内容在页面中的位置数据 | AC-5.1 / AC-5.2 |
| R-9 | 行为 | HighlightSpecifiedContent | 高亮指定内容区域。内容不存在时不执行高亮，返回默认值。 | 高亮为 UI 视觉操作，触发后可观测 | AC-5.3 / AC-5.4 |
| R-10 | 行为 | DumpViewData autofill 链 | 追踪 autofill 数据链路从数据源到 UI 节点的完整路径，支持表单自动填充数据追踪。 | autofill 链为调试辅助能力 | AC-6.1 |

## 验证映射

| 编号 | 对应规格项 | 验证方式 | 验证重点 |
|------|-----------|---------|---------|
| VM-1 | AC-1.1..1.3 / R-1 | 集成测试 | HitTest 分段 IPC 128KB 分段 + 无重试机制 |
| VM-2 | AC-2.1 / R-2 | 集成测试 | PixelMap 广播上报至所有 SA 进程 |
| VM-3 | AC-2.2..2.4 / R-3 | 集成测试 | GetMultiImagesById 双错误码（全局 + 逐图） |
| VM-4 | AC-3.1..3.3 / R-4 / R-5 | 集成测试 | GetCurrentPageName + GetStateMgmtInfo 同步查询 |
| VM-5 | AC-4.1 / AC-4.2 / R-6 | 集成测试 | GetWebInfoByRequest + WebRequestErrorCode |
| VM-6 | AC-4.3..4.8 / R-7 | 集成测试 | ExeAppAIFunction 错误码 0-5 |
| VM-7 | AC-5.1..5.4 / R-8 / R-9 | 集成测试 | GetSpecifiedContentOffsets + HighlightSpecifiedContent |
| VM-8 | AC-6.1 / R-10 | 代码评审 | DumpViewData autofill 链路追踪 |

## API 变更分析

### 新增 API

N/A，全部为 InnerApi（框架内部 IPC 接口）。无 Public/System API 变更。

### 变更/废弃 API

无。

## 接口规格

### 接口定义

**HitTest 分段 IPC**

| 属性 | 值 |
|------|-----|
| 函数签名 | `int32_t IUiContentService::GetHitTestTree(PointF point)` |
| 返回值 | `int32_t` — ERR_OK 或错误码 |
| 开放范围 | InnerApi |
| 错误码 | N/A |
| 关联 AC | AC-1.1 / AC-1.2 |

**参数约束**

| 参数 | 类型 | 必填 | 默认值 | 约束条件 |
|------|------|------|--------|---------|
| point | PointF | 是 | N/A | HitTest 查询坐标点 |

**行为场景**

| # | 触发条件 | 预期行为 | 关联 AC |
|---|----------|----------|---------|
| 1 | 数据量 <= 131072 字节 | 单次 IPC 发送全部结果 | AC-1.1 |
| 2 | 数据量 > 131072 字节 | 分段 IPC 发送，每段不超过 131072 字节 | AC-1.2 |
| 3 | 接收端中断 | 已发送段数据丢失，无重试 | AC-1.3 |

**GetMultiImagesById**

| 属性 | 值 |
|------|-----|
| 函数签名 | `int32_t IUiContentService::GetMultiImagesById(const std::vector<int32_t>& ids, std::vector<PixelMap>& images, int32_t& innerErrorCode, int32_t& errorIndex)` |
| 返回值 | `int32_t` — ERR_OK 或错误码 |
| 开放范围 | InnerApi |
| 错误码 | innerErrorCode(全局) + errorIndex(逐图) |
| 关联 AC | AC-2.2 / AC-2.3 / AC-2.4 |

**参数约束**

| 参数 | 类型 | 必填 | 默认值 | 约束条件 |
|------|------|------|--------|---------|
| ids | std::vector<int32_t> | 是 | N/A | 图片 ID 列表 |
| images | std::vector<PixelMap>& | 是 | N/A | 出参，图片数据列表 |
| innerErrorCode | int32_t& | 是 | N/A | 出参，全局错误码：0=成功 |
| errorIndex | int32_t& | 是 | N/A | 出参，逐图错误索引：-1=无逐图错误 |

**行为场景**

| # | 触发条件 | 预期行为 | 关联 AC |
|---|----------|----------|---------|
| 1 | 所有图片获取成功 | innerErrorCode=0, errorIndex=-1 | AC-2.2 |
| 2 | 全局失败（未注册回调） | innerErrorCode 非 0, errorIndex=-1 | AC-2.3 |
| 3 | 逐图失败（某图获取失败） | innerErrorCode=0, errorIndex=失败索引 | AC-2.4 |

**GetCurrentPageName**

| 属性 | 值 |
|------|-----|
| 函数签名 | `int32_t IUiContentService::GetCurrentPageName(std::string& name)` |
| 返回值 | `int32_t` — ERR_OK 或错误码 |
| 开放范围 | InnerApi |
| 错误码 | N/A |
| 关联 AC | AC-3.1 |

**参数约束**

| 参数 | 类型 | 必填 | 默认值 | 约束条件 |
|------|------|------|--------|---------|
| name | std::string& | 是 | N/A | 出参，当前页面名称 |

**行为场景**

| # | 触发条件 | 预期行为 | 关联 AC |
|---|----------|----------|---------|
| 1 | 正常查询 | 返回当前页面名称 | AC-3.1 |
| 2 | 页面名称为空 | 返回空字符串 | AC-3.2 |

**ExeAppAIFunction**

| 属性 | 值 |
|------|-----|
| 函数签名 | `int32_t IUiContentService::ExeAppAIFunction(const std::string& aiFunction, const std::string& params, std::string& result)` |
| 返回值 | `int32_t` — 错误码 0-5 |
| 开放范围 | InnerApi |
| 错误码 | 0(成功) / 1(参数错误) / 2(不支持) / 3(超时) / 4(内部错误) / 5(权限不足) |
| 关联 AC | AC-4.3 / AC-4.4 / AC-4.5 / AC-4.6 / AC-4.7 / AC-4.8 |

**参数约束**

| 参数 | 类型 | 必填 | 默认值 | 约束条件 |
|------|------|------|--------|---------|
| aiFunction | std::string | 是 | N/A | AI 函数名称 |
| params | std::string | 是 | N/A | AI 函数参数 JSON |
| result | std::string& | 是 | N/A | 出参，AI 函数执行结果 |

**行为场景**

| # | 触发条件 | 预期行为 | 关联 AC |
|---|----------|----------|---------|
| 1 | AI 函数执行成功 | 返回结果 + 错误码=0 | AC-4.3 |
| 2 | 参数格式错误 | 错误码=1 | AC-4.4 |
| 3 | AI 函数不支持 | 错误码=2 | AC-4.5 |
| 4 | AI 函数执行超时 | 错误码=3 | AC-4.6 |
| 5 | 内部错误 | 错误码=4 | AC-4.7 |
| 6 | 权限不足 | 错误码=5 | AC-4.8 |

**GetWebInfoByRequest**

| 属性 | 值 |
|------|-----|
| 函数签名 | `int32_t IUiContentService::GetWebInfoByRequest(const std::string& request, std::string& info)` |
| 返回值 | `int32_t` — ERR_OK 或 WebRequestErrorCode |
| 开放范围 | InnerApi |
| 错误码 | WebRequestErrorCode |
| 关联 AC | AC-4.1 / AC-4.2 |

**参数约束**

| 参数 | 类型 | 必填 | 默认值 | 约束条件 |
|------|------|------|--------|---------|
| request | std::string | 是 | N/A | Web 信息请求参数 |
| info | std::string& | 是 | N/A | 出参，Web 信息数据 |

**行为场景**

| # | 触发条件 | 预期行为 | 关联 AC |
|---|----------|----------|---------|
| 1 | Web 信息查询成功 | 返回 Web 信息 + WebRequestErrorCode=0 | AC-4.1 |
| 2 | Web 信息查询失败 | 返回 WebRequestErrorCode 标示失败类型 | AC-4.2 |

**GetSpecifiedContentOffsets**

| 属性 | 值 |
|------|-----|
| 函数签名 | `int32_t IUiContentService::GetSpecifiedContentOffsets(const std::string& content, std::vector<Offset>& offsets)` |
| 返回值 | `int32_t` — ERR_OK 或错误码 |
| 开放范围 | InnerApi |
| 错误码 | N/A |
| 关联 AC | AC-5.1 |

**参数约束**

| 参数 | 类型 | 必填 | 默认值 | 约束条件 |
|------|------|------|--------|---------|
| content | std::string | 是 | N/A | 指定内容标识 |
| offsets | std::vector<Offset>& | 是 | N/A | 出参，偏移量列表 |

**行为场景**

| # | 触发条件 | 预期行为 | 关联 AC |
|---|----------|----------|---------|
| 1 | 内容存在 | 返回偏移量列表 | AC-5.1 |
| 2 | 内容不存在 | 返回空偏移量列表 | AC-5.2 |

**HighlightSpecifiedContent**

| 属性 | 值 |
|------|-----|
| 函数签名 | `int32_t IUiContentService::HighlightSpecifiedContent(const std::string& content)` |
| 返回值 | `int32_t` — ERR_OK 或错误码 |
| 开放范围 | InnerApi |
| 错误码 | N/A |
| 关联 AC | AC-5.3 |

**参数约束**

| 参数 | 类型 | 必填 | 默认值 | 约束条件 |
|------|------|------|--------|---------|
| content | std::string | 是 | N/A | 高亮内容标识 |

**行为场景**

| # | 触发条件 | 预期行为 | 关联 AC |
|---|----------|----------|---------|
| 1 | 内容存在 | 高亮指定内容区域 | AC-5.3 |
| 2 | 内容不存在 | 不执行高亮，返回默认值 | AC-5.4 |

## 兼容性声明

- **已有 API 行为变更:** 否 — 全部为已有实现补录
- **配置文件格式变更:** 否
- **数据存储格式变更:** 否
- **最低支持版本:** API 12
- **API 版本号策略:** 无 @since 标注（框架内部 IPC 能力）

## 架构约束

| 关键约束 | 约束说明 | 影响 AC |
|---------|----------|---------|
| HitTest 分段 IPC 无重试机制 | 接收端中断时已发送段数据丢失，未发送段不再发送（无重试机制），依赖 SA 进程重新发起查询 | AC-1.3 |
| ONCE_IPC_SEND_DATA_MAX_SIZE=131072 | HitTest 分段 IPC 单段最大数据量 131072 字节（128KB + 8KB 头部空间） | AC-1.2 |
| GetMultiImagesById 双错误码独立 | innerErrorCode（全局）与 errorIndex（逐图）独立表示错误来源，全局成功时逐图错误通过 errorIndex 标示 | AC-2.3 / AC-2.4 |
| PixelMap 广播模式 | PixelMap 数据广播至所有已注册 SA 进程，非定向发送 | AC-2.1 |
| ExeAppAIFunction 错误码 0-5 全覆盖 | 6 种错误码覆盖 AI 函数执行全场景：成功/参数错误/不支持/超时/内部错误/权限不足 | AC-4.3..4.8 |

## 非功能性需求

| 类型 | 指标/阈值 | 验证方式 | 证据 |
|------|----------|----------|------|
| 性能 | HitTest 分段 IPC 保证大数据量查询正常传输 | 集成测试 | 代码审查 |
| 可观测 | ExeAppAIFunction 错误码 0-5 区分 AI 函数执行失败类型 | 集成测试 | 代码审查 |
| 可靠性 | GetMultiImagesById 双错误码精确定位错误来源 | 集成测试 | 代码审查 |
| 安全 | HitTest 分段 IPC 无重试机制需 SA 进程重新发起查询 | 代码评审 | 代码审查 |
| 定界定位 | WebRequestErrorCode 标示 Web 信息查询失败类型 | 集成测试 | 代码审查 |

## 多设备适配声明

无差异。

## 全局特性影响

| 特性 | 适用？ | 结论 | 关联场景 |
|------|--------|------|----------|
| 无障碍 | 不适用 | 无影响 — 查询能力为框架内部 IPC 能力 | — |
| 大字体 | 不适用 | 无影响 — 查询能力不涉及 UI 缩放 | — |
| 深色模式 | 不适用 | 无影响 — 查询能力不涉及颜色主题 | — |
| 多窗口 | 适用 | 每窗口独立查询能力，HitTest/PixelMap/GetMultiImagesById per-instance | 多窗口查询 |
| 多用户 | 不适用 | 无影响 — 查询能力不区分用户 | — |
| 版本升级 | 适用 | 无影响 — 无 Public/System API 契约 | — |
| 生态兼容 | 适用 | 新增查询类型需同步更新 IPC 事务码和接口声明 | 查询类型扩展 |

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
    query: "HitTest 分段 IPC + ONCE_IPC_SEND_DATA_MAX_SIZE=131072 (ui_session_manager_ohos.cpp:1086-1118)"
  - repo: "openharmony/ace_engine"
    query: "PixelMap 广播上报 + GetMultiImagesById 双错误码 (ui_session_manager_ohos.cpp:1676-1783)"
  - repo: "openharmony/ace_engine"
    query: "GetWebInfoByRequest + WebRequestErrorCode (ui_session_manager_ohos.cpp:1676-1783)"
  - repo: "openharmony/ace_engine"
    query: "GetCurrentPageName + GetStateMgmtInfo (ui_session_manager_ohos.cpp:1921-2001)"
  - repo: "openharmony/ace_engine"
    query: "ExeAppAIFunction + AI_CALL 错误码 0-5 (ui_session_manager_ohos.cpp:1921-2001)"
  - repo: "openharmony/ace_engine"
    query: "GetSpecifiedContentOffsets + HighlightSpecifiedContent (ui_session_manager_ohos.cpp:1921-2001)"
  - repo: "openharmony/ace_engine"
    query: "DumpViewData autofill 链路追踪 (ui_content_impl.cpp:5321-5373)"
```

**关键文档：**
- [design.md](03-engine-framework/09-uisession/01-uisession-service/design.md)
