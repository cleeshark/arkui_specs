# 特性规格

## 概述

| 属性 | 值 |
|------|-----|
| 特性名称 | 内容变化检测与阈值管理 |
| 特性编号 | Func-03-09-01-Feat-06 |
| 所属 Epic | UiSession |
| 优先级 | P1 |
| 目标版本 | API 12+ |
| SIG 归属 | ArkUI SIG |
| 状态 | Baselined |
| 复杂度 | 标准 |

> 本 Feat 锁定 UiSession 内容变化检测与阈值管理：ContentChangeManager 核心流程、StartContentChangeReport / StopContentChangeReport 启停、ContentChangeConfig 阈值配置与默认值（minReportTime / reportDelayTime / textContentRatio / minWidth / minHeight）、 throttling 限流（minReportTime 间隔、reportDelayTime 过渡抑制、textContentRatio AABB 比率检查）、ChangeType 事件类型（PAGE/SCROLL/SWIPER/TABS/TEXT/DIALOG/IMAGE_LOADED）、vsync 对齐 AABB 收集、image 延迟批量上报、text hash/version 追踪。不涉及 IPC 安全框架（Feat-01）、InspectorTree 查询（Feat-02）、事件上报门控（Feat-03）、命令下发（Feat-04）、翻译能力（Feat-05）、查询辅助 Dump（Feat-07）、SA 验证服务（Feat-08）。

## 本次变更范围（Delta）

> 历史规格补齐，补录已有实现的完整行为规格。

| 类型 | 内容 | 说明 |
|------|------|------|
| ADDED | ContentChangeManager 核心流程规格 | content_change_manager.cpp:246-313 管理内容变化检测全流程 |
| ADDED | StartContentChangeReport / StopContentChangeReport 启停规格 | content_change_manager.cpp:246-313 Start 通知节点注册检测，Stop 清理所有检测状态 |
| ADDED | ContentChangeConfig 阈值配置规格 | param_config.h:49-56 阈值参数定义与默认值：minReportTime / reportDelayTime / textContentRatio / minWidth / minHeight |
| ADDED | ContentChangeConfig 阈值校验 clamp 规格 | content_change_manager.cpp:561-810 无效阈值参数 clamp 至合法范围 |
| ADDED | minReportTime 间隔 throttling 规格 | content_change_manager.cpp:561-810 两次 TEXT/IMAGE 上报最小间隔限流 |
| ADDED | reportDelayTime 过渡抑制规格 | content_change_manager.cpp:949-1038 页面过渡期间延迟上报抑制 |
| ADDED | textContentRatio AABB 比率检查规格 | content_change_manager.cpp:561-810 文本 AABB 占页面面积比率低于阈值时不上报 |
| ADDED | image minWidth/minHeight 阈值规格 | content_change_manager.cpp:561-810 图片尺寸低于阈值时不上报 |
| ADDED | ChangeType 9 类事件规格 | content_change_manager.cpp:561-810 PAGE/SCROLL/SWIPER/TABS/TEXT/DIALOG/ARKWEB_PAGE/ARKWEB_TEXT/IMAGE_LOADED |
| ADDED | vsync 对齐 AABB 收集规格 | content_change_manager.cpp:949-1038 vsync 周期内收集 AABB，vsync 结束时批量上报 |
| ADDED | SCROLL 聚合规格 | content_change_manager.cpp:949-1038 所有滚动节点完成后聚合上报 |
| ADDED | SWIPER/TABS vsync 结束上报规格 | content_change_manager.cpp:949-1038 vsync 结束时上报 Swiper/Tabs 变化 |
| ADDED | PAGE 立即上报规格 | content_change_manager.cpp:561-810 PAGE 变化立即上报不做延迟 |
| ADDED | DIALOG show/hide 规格 | content_change_manager.cpp:561-810 Dialog 显示/隐藏变化上报 |
| ADDED | IMAGE 延迟批量上报规格 | content_change_manager.cpp:949-1038 图片加载完成后延迟批量上报 |
| ADDED | text hash/version 追踪规格 | content_change_manager.cpp:561-810 文本内容 hash 和 version 追踪去重 |
| ADDED | StopContentChangeReport 清理规格 | content_change_manager.cpp:246-313 Stop 清理所有检测状态、回调、定时器 |

## 输入文档

- 关联设计：`03-engine-framework/09-uisession/01-uisession-service/design.md`
- 关联需求：已有能力补录（无独立 requirement.md）
- 源码定位（关键文件）：
  - `adapter/ohos/entrance/ui_session/content_change_manager.cpp:246-313` — ContentChangeManager 核心流程 + Start/Stop
  - `adapter/ohos/entrance/ui_session/content_change_manager.cpp:561-810` — throttling + 阈值检查 + ChangeType 事件 + text hash/version
  - `adapter/ohos/entrance/ui_session/content_change_manager.cpp:949-1038` — vsync AABB 收集 + 过渡抑制 + image 延迟 + 聚合
  - `interfaces/inner_api/ui_session/param_config.h:49-56` — ContentChangeConfig 阈值参数定义与默认值

## 用户故事

### US-1: ContentChangeConfig 阈值配置与校验

- As a SA 工具开发者
- I want ContentChangeConfig 提供阈值参数（minReportTime / reportDelayTime / textContentRatio / minWidth / minHeight），无效参数 clamp 至合法范围
- So that SA 工具可自定义内容变化检测灵敏度，框架保证参数合法性

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-1.1 | WHEN ContentChangeConfig 参数在合法范围内 THEN 使用传入参数值作为检测阈值。来源：`param_config.h:49-56` | 正常 |
| AC-1.2 | WHEN ContentChangeConfig 参数超出合法范围（如 minReportTime < 0） THEN clamp 至合法范围最小值。来源：`content_change_manager.cpp:561-810` | 边界 |
| AC-1.3 | WHEN ContentChangeConfig 参数未传入 THEN 使用默认值：minReportTime=100ms, reportDelayTime=600ms, textContentRatio=0.15, minWidth=100px, minHeight=100px。来源：`param_config.h:49-56` | 正常 |

### US-2: StartContentChangeReport 启动检测与节点通知

- As a SA 工具开发者
- I want StartContentChangeReport 通知节点注册内容变化检测，根据 config 初始化阈值参数
- So that 节点开始追踪内容变化并在变化发生时上报至 SA 进程

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-2.1 | WHEN StartContentChangeReport 被调用 THEN 通知节点注册内容变化检测，初始化 ContentChangeConfig 阈值参数。来源：`content_change_manager.cpp:246-313` | 正常 |
| AC-2.2 | WHEN StartContentChangeReport config 参数 clamp 后 THEN 使用 clamp 后的合法阈值参数初始化检测流程。来源：`content_change_manager.cpp:561-810` | 正常 |

### US-3: minReportTime 间隔 throttling 与 reportDelayTime 过渡抑制

- As a 框架性能维护者
- I want minReportTime 限流两次 TEXT/IMAGE 上报最小间隔，reportDelayTime 抑制页面过渡期间上报延迟
- So that 内容变化上报频率可控，过渡期间避免噪声上报

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-3.1 | WHEN 两次 TEXT 上报间隔 < minReportTime THEN 第二次上报被 throttling 丢弃，等待 minReportTime 间隔后再上报。来源：`content_change_manager.cpp:561-810` | 正常 |
| AC-3.2 | WHEN 两次 IMAGE 上报间隔 < minReportTime THEN 第二次上报被 throttling 丢弃。来源：`content_change_manager.cpp:561-810` | 正常 |
| AC-3.3 | WHEN 页面过渡期间（transition） THEN reportDelayTime 延迟上报抑制，过渡完成后再上报内容变化。来源：`content_change_manager.cpp:949-1038` | 正常 |
| AC-3.4 | WHEN minReportTime=0 THEN 不限流，每次变化立即上报。来源：`content_change_manager.cpp:561-810` | 边界 |

### US-4: textContentRatio AABB 比率与 image 阈值检查

- As a 框架精度维护者
- I want textContentRatio 检查文本 AABB 占页面面积比率低于阈值时不上报，image minWidth/minHeight 检查图片尺寸低于阈值时不上报
- So that 微小内容变化不上报至 SA 进程，减少噪声

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-4.1 | WHEN 文本 AABB 占页面面积比率 >= textContentRatio THEN TEXT 变化上报至 SA 进程。来源：`content_change_manager.cpp:561-810` | 正常 |
| AC-4.2 | WHEN 文本 AABB 占页面面积比率 < textContentRatio THEN TEXT 变化不上报（比率低于阈值）。来源：`content_change_manager.cpp:561-810` | 边界 |
| AC-4.3 | WHEN 图片 width >= minWidth AND height >= minHeight THEN IMAGE_LOADED 变化上报至 SA 进程。来源：`content_change_manager.cpp:561-810` | 正常 |
| AC-4.4 | WHEN 图片 width < minWidth OR height < minHeight THEN IMAGE_LOADED 变化不上报（尺寸低于阈值）。来源：`content_change_manager.cpp:561-810` | 边界 |

### US-5: ChangeType 9 类事件与上报策略

- As a SA 工具开发者
- I want 9 类 ChangeType 事件（PAGE/SCROLL/SWIPER/TABS/TEXT/DIALOG/ARKWEB_PAGE/ARKWEB_TEXT/IMAGE_LOADED）各有不同上报策略
- So that SA 工具可区分不同内容变化类型并选择处理策略

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-5.1 | WHEN PAGE 变化发生 THEN 立即上报，不做延迟或聚合。来源：`content_change_manager.cpp:561-810` | 正常 |
| AC-5.2 | WHEN SCROLL 变化发生 THEN 聚合所有滚动节点完成后统一上报，非逐节点上报。来源：`content_change_manager.cpp:949-1038` | 正常 |
| AC-5.3 | WHEN SWIPER/TABS 变化发生 THEN vsync 结束时上报，vsync 周期内聚合。来源：`content_change_manager.cpp:949-1038` | 正常 |
| AC-5.4 | WHEN DIALOG show 变化发生 THEN 上报 DIALOG show 类型事件。来源：`content_change_manager.cpp:561-810` | 正常 |
| AC-5.5 | WHEN DIALOG hide 变化发生 THEN 上报 DIALOG hide 类型事件。来源：`content_change_manager.cpp:561-810` | 正常 |
| AC-5.6 | WHEN IMAGE_LOADED 变化发生 THEN 延迟批量上报，vsync 结束时批量收集图片变化。来源：`content_change_manager.cpp:949-1038` | 正常 |

### US-6: vsync 对齐 AABB 收集与 text hash/version 追踪

- As a 框架性能维护者
- I want vsync 对齐 AABB 收集保证变化检测与渲染帧同步，text hash/version 追踪去重避免重复上报相同文本内容
- So that 变化检测与渲染帧对齐，文本内容不变时不上报

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-6.1 | WHEN vsync 周期内 AABB 变化被收集 THEN vsync 结束时批量上报收集的 AABB 变化。来源：`content_change_manager.cpp:949-1038` | 正常 |
| AC-6.2 | WHEN text 内容 hash 与上次上报相同 THEN TEXT 变化不上报（去重）。来源：`content_change_manager.cpp:561-810` | 正常 |
| AC-6.3 | WHEN text 内容 version 与上次上报相同 THEN TEXT 变化不上报（version 去重）。来源：`content_change_manager.cpp:561-810` | 正常 |

### US-7: StopContentChangeReport 清理

- As a SA 工具开发者
- I want StopContentChangeReport 清理所有检测状态、回调、定时器
- So that 停止内容变化检测后框架状态完全清理，不留残余检测回调

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-7.1 | WHEN StopContentChangeReport 被调用 THEN 清理所有检测状态、回调、定时器，后续不再上报内容变化。来源：`content_change_manager.cpp:246-313` | 正常 |

## 验收追溯

| AC | 关联规则 | 关联 Task | 验证方式 | 证据 |
|----|----------|----------|----------|------|
| AC-1.1 | R-1 | TASK-SKELETON-6 | 集成测试 | 代码审查 |
| AC-1.2 | R-1 | TASK-SKELETON-6 | 集成测试：clamp 非法参数 | 代码审查 |
| AC-1.3 | R-1 | TASK-SKELETON-6 | 集成测试：默认值 | 代码审查 |
| AC-2.1 | R-2 | TASK-SKELETON-6 | 集成测试 | 代码审查 |
| AC-2.2 | R-2 / R-1 | TASK-SKELETON-6 | 集成测试 | 代码审查 |
| AC-3.1 | R-3 | TASK-SKELETON-6 | 集成测试 | 代码审查 |
| AC-3.2 | R-3 | TASK-SKELETON-6 | 集成测试 | 代码审查 |
| AC-3.3 | R-4 | TASK-SKELETON-6 | 集成测试 | 代码审查 |
| AC-3.4 | R-3 | TASK-SKELETON-6 | 代码评审 | 代码审查 |
| AC-4.1 | R-5 | TASK-SKELETON-6 | 集成测试 | 代码审查 |
| AC-4.2 | R-5 | TASK-SKELETON-6 | 集成测试 | 代码审查 |
| AC-4.3 | R-6 | TASK-SKELETON-6 | 集成测试 | 代码审查 |
| AC-4.4 | R-6 | TASK-SKELETON-6 | 集成测试 | 代码审查 |
| AC-5.1 | R-9 | TASK-SKELETON-6 | 集成测试 | 代码审查 |
| AC-5.2 | R-7 | TASK-SKELETON-6 | 集成测试 | 代码审查 |
| AC-5.3 | R-8 | TASK-SKELETON-6 | 集成测试 | 代码审查 |
| AC-5.4 | R-10 | TASK-SKELETON-6 | 集成测试 | 代码审查 |
| AC-5.5 | R-10 | TASK-SKELETON-6 | 集成测试 | 代码审查 |
| AC-5.6 | R-11 | TASK-SKELETON-6 | 集成测试 | 代码审查 |
| AC-6.1 | R-8 | TASK-SKELETON-6 | 集成测试 | 代码审查 |
| AC-6.2 | R-12 | TASK-SKELETON-6 | 集成测试 | 代码审查 |
| AC-6.3 | R-12 | TASK-SKELETON-6 | 集成测试 | 代码审查 |
| AC-7.1 | R-13 | TASK-SKELETON-6 | 集成测试 | 代码审查 |

## 规则定义

| 规则ID | 类型 | 触发条件 | 预期行为 | 边界/约束 | 关联AC |
|--------|------|----------|----------|-----------|--------|
| R-1 | 行为 | ContentChangeConfig 阈值校验 clamp | 参数在合法范围内：使用传入值。参数超出合法范围：clamp 至合法范围最小值。参数未传入：使用默认值 minReportTime=100ms, reportDelayTime=600ms, textContentRatio=0.15, minWidth=100px, minHeight=100px。 | clamp 保证所有阈值参数为合法值 | AC-1.1 / AC-1.2 / AC-1.3 / AC-2.2 |
| R-2 | 行为 | StartContentChangeReport 节点通知 | 通知节点注册内容变化检测，初始化 ContentChangeConfig clamp 后的阈值参数，启动检测流程。 | Start 后节点开始追踪内容变化 | AC-2.1 / AC-2.2 |
| R-3 | 行为 | minReportTime 间隔 throttling | 两次 TEXT/IMAGE 上报间隔 < minReportTime 时第二次上报被 throttling 丢弃。两次 TEXT/IMAGE 上报间隔 >= minReportTime 时正常上报。minReportTime=0 时不限流。 | TEXT 和 IMAGE 分别独立限流 | AC-3.1 / AC-3.2 / AC-3.4 |
| R-4 | 行为 | reportDelayTime 过渡抑制 | 页面过渡期间（transition）reportDelayTime 延迟上报抑制，过渡完成后再上报内容变化。 | 过渡期间上报延迟至过渡完成 | AC-3.3 |
| R-5 | 边界 | textContentRatio AABB 比率检查 | 文本 AABB 占页面面积比率 >= textContentRatio 时 TEXT 变化上报。比率 < textContentRatio 时不上报。比率=0 时所有文本变化上报（textContentRatio=0 为特殊值）。 | textContentRatio 默认 0.15 | AC-4.1 / AC-4.2 |
| R-6 | 边界 | image minWidth/minHeight 阈值 | 图片 width >= minWidth AND height >= minHeight 时 IMAGE_LOADED 变化上报。width < minWidth OR height < minHeight 时不上报。 | minWidth 默认 100px, minHeight 默认 100px | AC-4.3 / AC-4.4 |
| R-7 | 行为 | SCROLL 聚合（所有滚动节点完成后上报） | SCROLL 变化不逐节点上报，而是聚合所有滚动节点完成后统一上报。 | 多个滚动节点同时变化时仅上报一次聚合事件 | AC-5.2 |
| R-8 | 行为 | SWIPER/TABS vsync 结束上报 + vsync AABB 收集 | SWIPER/TABS 变化 vsync 周期内聚合，vsync 结束时上报。vsync 周期内 AABB 变化被收集，vsync 结束时批量上报。 | vsync 对齐保证变化检测与渲染帧同步 | AC-5.3 / AC-6.1 |
| R-9 | 行为 | PAGE 立即上报 | PAGE 变化立即上报，不做延迟或聚合。 | PAGE 变化不需要 vsync 对齐 | AC-5.1 |
| R-10 | 行为 | DIALOG show/hide | DIALOG show 变化上报 DIALOG show 类型事件。DIALOG hide 变化上报 DIALOG hide 类型事件。 | show 和 hide 为独立事件类型 | AC-5.4 / AC-5.5 |
| R-11 | 行为 | IMAGE 延迟批量上报 | IMAGE_LOADED 变化延迟批量上报，vsync 结束时批量收集图片变化后统一上报。 | 延迟上报避免逐图片频繁上报 | AC-5.6 |
| R-12 | 行为 | text hash/version 追踪去重 | text 内容 hash 与上次上报相同时不上报（去重）。text 内容 version 与上次上报相同时不上报（version 去重）。hash 或 version 不同时上报。 | hash 和 version 双重去重 | AC-6.2 / AC-6.3 |
| R-13 | 恢复 | StopContentChangeReport 清理 | Stop 清理所有检测状态、回调、定时器，后续不再上报内容变化。 | Stop 后框架状态完全清理 | AC-7.1 |

## 验证映射

| 编号 | 对应规格项 | 验证方式 | 验证重点 |
|------|-----------|---------|---------|
| VM-1 | AC-1.1..1.3 / R-1 | 集成测试 | ContentChangeConfig 阈值校验 clamp + 默认值 |
| VM-2 | AC-2.1 / AC-2.2 / R-2 / R-1 | 集成测试 | StartContentChangeReport 节点通知 + 阈值初始化 |
| VM-3 | AC-3.1..3.4 / R-3 / R-4 | 集成测试 | minReportTime throttling + reportDelayTime 过渡抑制 |
| VM-4 | AC-4.1..4.4 / R-5 / R-6 | 集成测试 | textContentRatio AABB + image 阈值检查 |
| VM-5 | AC-5.1..5.6 / R-7..R-11 | 集成测试 | 9 类 ChangeType 事件上报策略 |
| VM-6 | AC-6.1..6.3 / R-8 / R-12 | 集成测试 | vsync AABB 收集 + text hash/version 去重 |
| VM-7 | AC-7.1 / R-13 | 集成测试 | StopContentChangeReport 清理 |

## API 变更分析

### 新增 API

N/A，全部为 InnerApi（框架内部 IPC 接口）。无 Public/System API 变更。

### 变更/废弃 API

无。

## 接口规格

### 接口定义

**StartContentChangeReport**

| 属性 | 值 |
|------|-----|
| 函数签名 | `void ContentChangeManager::StartContentChangeReport(const ContentChangeConfig& config)` |
| 返回值 | `void` |
| 开放范围 | InnerApi |
| 错误码 | N/A |
| 关联 AC | AC-2.1 |

**参数约束**

| 参数 | 类型 | 必填 | 默认值 | 约束条件 |
|------|------|------|--------|---------|
| config | ContentChangeConfig | 是 | N/A | 阈值参数：minReportTime / reportDelayTime / textContentRatio / minWidth / minHeight |

**行为场景**

| # | 触发条件 | 预期行为 | 关联 AC |
|---|----------|----------|---------|
| 1 | config 参数合法 | 通知节点注册检测 + 初始化阈值 | AC-2.1 |
| 2 | config 参数非法 | clamp 至合法范围 + 通知节点注册检测 | AC-2.2 |

**StopContentChangeReport**

| 属性 | 值 |
|------|-----|
| 函数签名 | `void ContentChangeManager::StopContentChangeReport()` |
| 返回值 | `void` |
| 开放范围 | InnerApi |
| 错误码 | N/A |
| 关联 AC | AC-7.1 |

**行为场景**

| # | 触发条件 | 预期行为 | 关联 AC |
|---|----------|----------|---------|
| 1 | 正常调用 | 清理所有检测状态、回调、定时器 | AC-7.1 |

**ContentChangeConfig**

| 属性 | 值 |
|------|-----|
| 函数签名 | `struct ContentChangeConfig { int32_t minReportTime; int32_t reportDelayTime; float textContentRatio; int32_t minWidth; int32_t minHeight; }` |
| 返回值 | N/A（结构体） |
| 开放范围 | InnerApi |
| 错误码 | N/A |
| 关联 AC | AC-1.1 / AC-1.3 |

**参数约束**

| 参数 | 类型 | 必填 | 默认值 | 约束条件 |
|------|------|------|--------|---------|
| minReportTime | int32_t | 否 | 100ms | >= 0；0 表示不限流 |
| reportDelayTime | int32_t | 否 | 600ms | >= 0 |
| textContentRatio | float | 否 | 0.15 | 0.0~1.0；0 表示所有文本变化上报 |
| minWidth | int32_t | 否 | 100px | >= 0 |
| minHeight | int32_t | 否 | 100px | >= 0 |

**行为场景**

| # | 触发条件 | 预期行为 | 关联 AC |
|---|----------|----------|---------|
| 1 | 参数合法范围内 | 使用传入值 | AC-1.1 |
| 2 | 参数超出合法范围 | clamp 至合法范围最小值 | AC-1.2 |
| 3 | 参数未传入 | 使用默认值 | AC-1.3 |

## 兼容性声明

- **已有 API 行为变更:** 否 — 全部为已有实现补录
- **配置文件格式变更:** 否
- **数据存储格式变更:** 否
- **最低支持版本:** API 12
- **API 版本号策略:** 无 @since 标注（框架内部 IPC 能力）

## 架构约束

| 关键约束 | 约束说明 | 影响 AC |
|---------|----------|---------|
| vsync 对齐 AABB 收集 | 变化检测与渲染帧同步，vsync 周期内收集 AABB，vsync 结束时批量上报 | AC-6.1 |
| SCROLL 聚合上报 | 多个滚动节点同时变化时仅上报一次聚合事件，非逐节点上报 | AC-5.2 |
| IMAGE 延迟批量上报 | 图片加载完成后延迟批量上报，vsync 结束时统一上报 | AC-5.6 |
| TEXT/IMAGE 独立限流 | minReportTime 限流 TEXT 和 IMAGE 分别独立计算间隔 | AC-3.1 / AC-3.2 |
| text hash/version 双重去重 | hash 和 version 双重去重保证文本内容不变时不上报 | AC-6.2 / AC-6.3 |

## 非功能性需求

| 类型 | 指标/阈值 | 验证方式 | 证据 |
|------|----------|----------|------|
| 性能 | minReportTime throttling 限流防止频繁上报 | 集成测试 | 代码审查 |
| 可观测 | ChangeType 事件类型区分不同内容变化 | 代码评审 | 代码审查 |
| 可靠性 | StopContentChangeReport 完全清理检测状态 | 集成测试 | 代码审查 |
| 安全 | ContentChangeConfig clamp 保证阈值参数合法性 | 单元测试 | 代码审查 |
| 定界定位 | text hash/version 去重定位重复文本上报 | 代码评审 | 代码审查 |

## 多设备适配声明

无差异。

## 全局特性影响

| 特性 | 适用？ | 结论 | 关联场景 |
|------|--------|------|----------|
| 无障碍 | 不适用 | 无影响 — 内容变化检测为框架内部 IPC 能力 | — |
| 大字体 | 适用 | textContentRatio 阈值检查需考虑大字体模式下 AABB 占比变化 | 大字体文本上报 |
| 深色模式 | 不适用 | 无影响 — 内容变化检测不涉及颜色主题 | — |
| 多窗口 | 适用 | 每窗口独立 ContentChangeManager 和阈值配置 | 多窗口内容变化 |
| 多用户 | 不适用 | 无影响 — 内容变化检测不区分用户 | — |
| 版本升级 | 适用 | 无影响 — 无 Public/System API 契约 | — |
| 生态兼容 | 适用 | 新增 ChangeType 事件类型需同步更新 ContentChangeManager 处理逻辑 | ChangeType 扩展 |

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
    query: "ContentChangeManager 核心流程 + Start/Stop (content_change_manager.cpp:246-313)"
  - repo: "openharmony/ace_engine"
    query: "throttling + 阈值检查 + ChangeType 9 类事件 (content_change_manager.cpp:561-810)"
  - repo: "openharmony/ace_engine"
    query: "vsync AABB 收集 + 过渡抑制 + image 延迟 + 聚合上报 (content_change_manager.cpp:949-1038)"
  - repo: "openharmony/ace_engine"
    query: "ContentChangeConfig 阈值参数定义与默认值 (param_config.h:49-56)"
  - repo: "openharmony/ace_engine"
    query: "text hash/version 追踪去重 (content_change_manager.cpp:561-810)"
```

**关键文档：**
- [design.md](03-engine-framework/09-uisession/01-uisession-service/design.md)
