# 特性规格

## 概述

| 属性 | 值 |
|------|-----|
| 特性名称 | 平台抽象基类与构建适配 |
| 特性编号 | Func-02-01-01-Feat-04 |
| 所属 Epic | 跨平台适配层 |
| 优先级 | P1 |
| 目标版本 | API 9+ |
| SIG 归属 | ArkUI SIG |
| 状态 | Baselined |
| 复杂度 | 标准 |

## 本次变更范围（Delta）

> 全新特性补录，无存量变更。本节跳过。

## 输入文档

- 源码路径：`adapter/ohos/entrance/` + `adapter/ohos/build/` + `frameworks/core/common/`
- 设计文档：`02-cross-platform/01-platform-adapter/01-oh-platform-adapter/design.md`

## 用户故事

### US-1: Container 抽象基类与 AceContainer 适配

作为一个 ACE 引擎开发者，我希望 Container 抽象基类定义完整的容器生命周期和查询接口，OHOS AceContainer 实现所有接口并集成 Rosen Window 和多实例管理。

| AC编号 | 验收标准 | 类型 |
|--------|----------|------|
| AC-1.1 | WHEN AceContainer(Container+JsMessageDispatcher) 构造 THEN 实现所有 Container 纯虚方法 + JsMessageDispatcher Dispatch/DispatchPluginError | 正常 |
| AC-1.2 | WHEN AceContainer::Initialize THEN 初始化前端、管线、任务执行器、AssetManager 等 | 正常 |
| AC-1.3 | WHEN AceContainer::Destroy THEN 销毁所有资源（顺序：前端→管线→UI→View） | 正常 |
| AC-1.4 | WHEN AceContainer::IsMainWindow/IsSubWindow/IsDialogWindow THEN 返回对应窗口类型标识 | 正常 |
| AC-1.5 | WHEN AceContainer::IsFormRender/IsUseStageModel THEN 返回卡片渲染/Stage模型标识 | 正常 |
| AC-1.6 | WHEN AceContainer::IsFreeMultiWindow/IsSceneBoardWindow THEN 返回自由多窗/场景板标识 | 正常 |
| AC-1.7 | WHEN DialogContainer(AceContainer子类) THEN IsDialogContainer()返回 true | 正常 |
| AC-1.8 | WHEN PaContainer(Container子类) THEN 无 UI 渲染，仅数据/服务能力 | 正常 |
| AC-1.9 | WHEN ContainerScope RAII 构造 THEN 设置当前实例 ID；析构恢复 | 正常 |
| AC-1.10 | WHEN Container::Current() THEN 返回当前线程的 Container 实例 | 正常 |
| AC-1.11 | WHEN ContainerType 枚举 THEN STAGE/FA/PA_SERVICE/PA_DATA/PA_FORM/FA_SUBWINDOW/DC/WINDOW_FREE/COMPONENT_SUBWINDOW/PLUGIN_SUBCONTAINER 分配 ID 范围（每种100000个ID） | 边界 |
| AC-1.12 | WHEN AceContainer::Dispatch/DispatchSync THEN 异步/同步分发 JS 消息 | 正常 |

### US-2: AceApplicationInfo 适配

作为一个 ACE 引擎开发者，我希望 AceApplicationInfoImpl 正确桥接 OHOS 应用信息管理。

| AC编号 | 验收标准 | 类型 |
|--------|----------|------|
| AC-2.1 | WHEN AceApplicationInfo::GetInstance() THEN 返回 OHOS AceApplicationInfoImpl 单例 | 正常 |
| AC-2.2 | WHEN SetLocale THEN 通过 ResourceManager + Localization 设置语言 | 正常 |
| AC-2.3 | WHEN ChangeLocale THEN 调用 OHOS ResourceManager 更新语言 | 正常 |
| AC-2.4 | WHEN GreatOrEqualTargetAPIVersion THEN 比较目标 API 版本 | 正常 |
| AC-2.5 | WHEN IsRightToLeft THEN 判断 RTL 方向 | 正常 |

### US-3: PlatformWindow 抽象与工厂

作为一个 ACE 引擎开发者，我希望 PlatformWindow 抽象基类定义 VSync 和根节点接口，工厂根据构建目标选择实现。

| AC编号 | 验收标准 | 类型 |
|--------|----------|------|
| AC-3.1 | WHEN PlatformWindow::Create(AceView*) THEN 根据构建目标返回 RSWindow 或其他实现 | 正常 |
| AC-3.2 | WHEN RequestFrame/RegisterVsyncCallback THEN 请求/注册 VSync | 正常 |
| AC-3.3 | WHEN SetRootRenderNode THEN 设置根渲染节点 | 正常 |
| AC-3.4 | WHEN PlatformResRegister::OnMethodCall THEN 处理平台方法调用 | 正常 |
| AC-3.5 | WHEN JsMessageDispatcher::Dispatch/DispatchSync THEN 异步/同步分发消息 | 正常 |

### US-4: 构建系统适配（GN 宏体系）

作为一个 ACE 引擎开发者，我希望 ace_config.gni + adapter/ohos/build/ 正确控制平台选择、宏定义和编译变体。

| AC编号 | 验收标准 | 类型 |
|--------|----------|------|
| AC-4.1 | WHEN is_ohos_standard_system=true THEN 启用 OHOS 标准系统变体 | 正常 |
| AC-4.2 | WHEN is_arkui_x=true THEN CROSS_PLATFORM 宏定义，禁用 OHOS 子系统调用 | 正常 |
| AC-4.3 | WHEN enable_rosen_backend=true THEN ENABLE_ROSEN_BACKEND 宏 | 正常 |
| AC-4.4 | WHEN ohos_ng 变体 THEN NG_BUILD 定义，禁用 form/plugin | 正常 |
| AC-4.5 | WHEN platform.gni 迭代 THEN 每个适配器目录注册 platforms 列表 | 正常 |
| AC-4.6 | WHEN #ifndef CROSS_PLATFORM THEN 排除 OHOS 子系统调用(~50+位置) | 边界 |
| AC-4.7 | WHEN #ifdef ENABLE_ROSEN_BACKEND THEN 选择 Rosen 路径(~30+位置) | 边界 |
| AC-4.8 | WHEN Preview 平台构建 THEN 使用 adapter/preview/ 实现 | 正常 |

### US-5: UIContentImpl 入口适配

作为一个 ACE 引擎开发者，我希望 UIContentImpl 作为 OHOS 系统级入口委托到 AceContainer。

| AC编号 | 验收标准 | 类型 |
|--------|----------|------|
| AC-5.1 | WHEN UIContentImpl::Initialize THEN 创建 AceContainer 并初始化 | 正常 |
| AC-5.2 | WHEN RunPage/RunPageByName THEN 运行页面 | 正常 |
| AC-5.3 | WHEN Destroy THEN 销毁 AceContainer | 正常 |
| AC-5.4 | WHEN Foreground/Background THEN 前后台切换 | 正常 |
| AC-5.5 | WHEN OnConfigurationUpdated THEN 配置变更传播 | 正常 |

## 验收追溯

| AC | 关联规则 | 关联 Task | 验证方式 | 证据 |
|----|----------|-----------|----------|------|
| AC-1.1~1.12 | R-1~12 | TASK-F04-01 | 单测 | container.h, ace_container.h |
| AC-2.1~2.5 | R-13~17 | TASK-F04-02 | 单测 | ace_application_info_impl.h |
| AC-3.1~3.5 | R-18~22 | TASK-F04-03 | 单测 | platform_window.h |
| AC-4.1~4.8 | R-23~30 | TASK-F04-04 | 编译检查 | ace_config.gni |
| AC-5.1~5.5 | R-31~35 | TASK-F04-05 | 单测 | ui_content_impl.h |

## 规则定义

| 规则ID | 类型 | 触发条件 | 预期行为 | 边界/约束 | 关联AC |
|--------|------|----------|----------|-----------|--------|
| R-1 | 行为 | AceContainer 构造 | 实现 Container+JsMessageDispatcher | 双继承 | AC-1.1 |
| R-2 | 行为 | Initialize | 初始化前端/管线/任务执行器 | 依赖传入参数 | AC-1.2 |
| R-3 | 行为 | Destroy | 顺序销毁资源 | 前端→管线→UI→View | AC-1.3 |
| R-4 | 行为 | IsMainWindow/IsSubWindow/IsDialogWindow | 返回窗口类型 | ContainerType 决定 | AC-1.4 |
| R-5 | 行为 | IsFormRender/IsUseStageModel | 返回卡片/Stage标识 | form/components_support 标志 | AC-1.5 |
| R-6 | 行为 | IsFreeMultiWindow/IsSceneBoardWindow | 返回自由多窗/场景板 | 多窗和SceneBoard标志 | AC-1.6 |
| R-7 | 行为 | DialogContainer | IsDialogContainer=true | 继承 AceContainer | AC-1.7 |
| R-8 | 行为 | PaContainer | 无UI，仅数据/服务 | 无前端/管线 | AC-1.8 |
| R-9 | 行为 | ContainerScope RAII | 设置/恢复实例ID | ContainerScope 不可拷贝 | AC-1.9 |
| R-10 | 行为 | Container::Current() | 返回当前线程Container | 线程局部存储 | AC-1.10 |
| R-11 | 边界 | ContainerType 枚举 | 每种100000个ID范围 | STAGE=1,FA=2,PA_SERVICE=3... | AC-1.11 |
| R-12 | 行为 | Dispatch/DispatchSync | 异步/同步分发 | UI线程执行 | AC-1.12 |
| R-13 | 行为 | GetInstance() | 返回 OHOS AceApplicationInfoImpl | 静态工厂 | AC-2.1 |
| R-14 | 行为 | SetLocale | ResourceManager+Localization | locale 格式: language-country | AC-2.2 |
| R-15 | 行为 | ChangeLocale | OHOS ResourceManager locale 更新 | 同步更新 | AC-2.3 |
| R-16 | 行为 | GreatOrEqualTargetAPIVersion | 比较目标版本号 | apiTargetVersion_ 字段 | AC-2.4 |
| R-17 | 行为 | IsRightToLeft | 判断 RTL | 基于 locale 语言代码 | AC-2.5 |
| R-18 | 行为 | PlatformWindow::Create | 根据构建返回实现 | OHOS→RSWindow | AC-3.1 |
| R-19 | 行为 | RequestFrame/RegisterVsyncCallback | 请求/注册VSync | 平台特定实现 | AC-3.2 |
| R-20 | 行为 | SetRootRenderNode | 设置根节点 | 旧管线使用 | AC-3.3 |
| R-21 | 行为 | PlatformResRegister::OnMethodCall | 处理平台方法 | Referenced 基类 | AC-3.4 |
| R-22 | 行为 | JsMessageDispatcher::Dispatch/DispatchSync | 异步/同步分发 | AceContainer 实现 | AC-3.5 |
| R-23 | 行为 | is_ohos_standard_system | 启用 OHOS 标准变体 | is_standard_system && !is_arkui_x | AC-4.1 |
| R-24 | 行为 | is_arkui_x | CROSS_PLATFORM 宏 | 禁用50+OHOS子系统调用 | AC-4.2 |
| R-25 | 行为 | enable_rosen_backend | ENABLE_ROSEN_BACKEND 宏 | 30+代码路径选择 | AC-4.3 |
| R-26 | 行为 | ohos_ng 变体 | NG_BUILD+禁用form/plugin | !is_asan && ace_engine_feature_enable_libace | AC-4.4 |
| R-27 | 行为 | platform.gni 迭代 | 注册 platforms 列表 | 搜索 adapter/ 子目录 | AC-4.5 |
| R-28 | 边界 | #ifndef CROSS_PLATFORM | 排除 OHOS 子系统调用 | ~50+位置 | AC-4.6 |
| R-29 | 边界 | #ifdef ENABLE_ROSEN_BACKEND | 选择 Rosen 路径 | ~30+位置 | AC-4.7 |
| R-30 | 行为 | Preview 平台构建 | 使用 adapter/preview/ | mingw/mac/linux 条件 | AC-4.8 |
| R-31 | 行为 | UIContentImpl::Initialize | 创建 AceContainer | OHOS 系统入口 | AC-5.1 |
| R-32 | 行为 | RunPage/RunPageByName | 运行页面 | 通过 AceContainer | AC-5.2 |
| R-33 | 行为 | Destroy | 销毁 AceContainer | 清理所有资源 | AC-5.3 |
| R-34 | 行为 | Foreground/Background | 前后台切换 | 委托 AceContainer | AC-5.4 |
| R-35 | 行为 | OnConfigurationUpdated | 配置变更传播 | 委托 AceContainer | AC-5.5 |

## 验证映射

| 编号 | 对应规格项 | 验证方式 | 验证重点 |
|------|------------|----------|----------|
| VM-1 | AC-1.1~1.12 Container/AceContainer | 单测 | 生命周期、窗口类型、RAII、双继承 |
| VM-2 | AC-2.1~2.5 AceApplicationInfo | 单测 | Locale、API版本、RTL |
| VM-3 | AC-3.1~3.5 PlatformWindow/ResRegister | 单测 | 工厂、VSync、消息分发 |
| VM-4 | AC-4.1~4.8 构建系统 | 编译检查 | 宏定义、变体、跨平台 |
| VM-5 | AC-5.1~5.5 UIContentImpl | 单测+集成测试 | 入口委托、配置变更 |

## API 变更分析

N/A，框架内部适配层，无 SDK API 变更。

## 接口规格

### 接口定义

**Container::Initialize**

| 属性 | 值 |
|------|-----|
| 函数签名 | `void AceContainer::Initialize()` |
| 返回值 | `void` |
| 开放范围 | InnerApi |
| 错误码 | N/A |
| 关联 AC | AC-1.2 |

**UIContentImpl::Initialize**

| 属性 | 值 |
|------|-----|
| 函数签名 | `void UIContentImpl::Initialize(OHOS::AppExecFwk::Ability* ability, ...)` |
| 返回值 | `void` |
| 开放范围 | InnerApi |
| 错误码 | N/A |
| 关联 AC | AC-5.1 |

## 兼容性声明

- **已有 API 行为变更:** 否
- **配置文件格式变更:** 否
- **数据存储格式变更:** 否
- **最低支持版本:** API 9
- **API 版本号策略:** InnerApi

## 架构约束

| 关键约束 | 约束说明 | 影响 AC |
|----------|----------|---------|
| Container+JsMessageDispatcher 双继承 | AceContainer 实现两个抽象基类 | AC-1.1 |
| ContainerType ID 范围分区 | 每种类型100000个ID | AC-1.11 |
| OHOS/Preview 链接时选择 | 同类名不同实现(ace_application_info_impl.h) | AC-2.1 |
| CROSS_PLATFORM 宏 ~50+位置 | 禁用 OHOS 子系统调用 | AC-4.6 |
| ohos/ohos_ng 双变体 | 不同 feature flag 组合 | AC-4.4 |

## 非功能性需求

| 类型 | 指标/阈值 | 验证方式 | 证据 |
|------|-----------|----------|------|
| 可测试性 | AceContainer 可通过 Mock Window/Frontend 测试 | 单测 | ace_container.h |
| 构建验证 | ohos/ohos_ng 双变体均编译通过 | GN 构建 | ace_config.gni |

## 多设备适配声明

无差异。所有设备类型使用相同的构建和容器逻辑。

## 全局特性影响

| 特性 | 适用？ | 结论 | 关联场景 |
|------|--------|------|----------|
| 无障碍 | 否 | 适配层不直接影响 | N/A |
| 大字体 | 否 | 适配层不直接影响 | N/A |
| 深色模式 | 否 | 适配层不直接影响 | N/A |
| 多窗口/分屏 | 是 | ContainerType 支持多窗口类型 | AC-1.4 |
| 版本升级 | 是 | AceApplicationInfo API 版本比较影响行为分支 | AC-2.4 |
| 生态兼容 | 是 | CROSS_PLATFORM 控制 ArkUI-X 跨平台能力 | AC-4.2 |

## Spec 自审清单

- [x] 无"待定""TBD""TODO"等占位符
- [x] 所有 AC 使用 WHEN/THEN 格式
- [x] 范围边界明确
- [x] 无语义模糊表述
- [x] AC 与规则表交叉一致
- [x] 规则表每条通过 5 项质量检查

## context-references

```yaml
context-queries:
  - repo: "openharmony/ace_engine"
    query: "Container+JsMessageDispatcher 双继承模式和 AceContainer/DragContainer/PaContainer 三种容器子类"
  - repo: "openharmony/ace_engine"
    query: "OHOS/Preview 同类名 AceApplicationInfoImpl 链接时选择机制"
  - repo: "openharmony/ace_engine"
    query: "ace_config.gni + adapter/ohos/build/ GN 宏体系和 ohos/ohos_ng 双变体构建"
  - repo: "openharmony/ace_engine"
    query: "UIContentImpl 作为 OHOS 系统级入口委托到 AceContainer 的初始化和生命周期"
```

**关键文档：** ace_engine `adapter/ohos/entrance/` + `adapter/ohos/build/` + `frameworks/core/common/`
