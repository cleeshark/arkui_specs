# 特性规格

> Func-04-02-01-Feat-01 安全区数据源聚合与窗口同步存量规格。

## 概述

| 属性 | 值 |
|------|-----|
| 特性名称 | 安全区数据源聚合与窗口同步 |
| 特性编号 | Func-04-02-01-Feat-01 |
| 所属 Epic | 无（已有能力补录） |
| 优先级 | P0 |
| 目标版本 | API 26 |
| SIG 归属 | ArkUI SIG |
| 状态 | Baselined |
| 复杂度 | 复杂 |

本特性定义 SafeAreaInsets 四向区间模型，以及系统栏、刘海、导航指示器、浮动导航和键盘等外部输入如何在窗口初始化、尺寸变化、旋转、SceneBoard、UIExtension 与动态组件场景同步到 SafeAreaManager。

## 本次变更范围（Delta）

| 类型 | 内容 | 说明 |
|------|------|------|
| ADDED | 安全区数据模型 | 补录四向区间、类型/边掩码与有效性 |
| ADDED | 窗口数据同步 | 补录 AvoidArea 转换、初始化和 viewport 更新 |
| ADDED | 聚合与门控 | 补录全屏、cutout、导航区、SceneBoard 和全局忽略条件 |

## 输入文档

| 文档 | 路径 | 状态 |
|------|------|------|
| Design | `04-common-capability/02-safe-area/01-safe-area-mechanism/design.md` | 并行补录 |
| Insets model | `interfaces/inner_api/ace_kit/include/ui/properties/safe_area_insets.h` | 已核对 |
| Manager | `frameworks/core/components_ng/manager/safe_area/safe_area_manager.cpp` | 已核对 |
| Window adapter | `adapter/ohos/entrance/ui_content_impl.cpp` | 已核对 |
| Pipeline | `frameworks/core/pipeline_ng/pipeline_context.cpp` | 已核对 |

## 用户故事

### US-1: 将窗口避让区域转换为安全区

**作为** ArkUI 布局与渲染管线  
**我想要** 获得统一的四向安全区数据  
**以便** 后续组件使用一致的系统边界

| AC编号 | 验收标准 | 类型 |
|--------|----------|------|
| AC-1.1 | WHEN Window 返回合法 AvoidArea Rect THEN adapter 将其转换为 top/bottom/left/right 区间并写入对应安全区类型 | 正常 |
| AC-1.2 | WHEN 转换后的边区间 start>=end THEN 该边无效；WHEN SYSTEM/NAVIGATION 区间 start<end 但超出 rootSize THEN 当前实现仍保存该区间；CUTOUT/FLOAT_NAVIGATION 只按贴边条件归一端点，不执行统一根边界裁剪 | 边界 |
| AC-1.3 | WHEN 同一类型多边存在有效区间 THEN SafeAreaInsets 保留各边区间并按类型/边掩码查询 | 正常 |
| AC-1.4 | WHEN 根尺寸、方向或 surface 变化 THEN Pipeline 使用新根尺寸刷新窗口避让区及键盘 bottom inset | 正常 |

### US-2: 聚合系统、刘海和导航输入

**作为** 框架维护者  
**我想要** 按当前窗口模式聚合安全区  
**以便** SceneBoard、UIExtension 和普通窗口各自保持存量行为

| AC编号 | 验收标准 | 类型 |
|--------|----------|------|
| AC-2.1 | WHEN UIContent 初始化且平台版本满足门槛 THEN 读取 SYSTEM、CUTOUT、NAVIGATION_INDICATOR、FLOAT_NAVIGATION 四类窗口避让区 | 正常 |
| AC-2.2 | WHEN窗口非全屏、未要求避让或开启全局 ignore-safe-area THEN SafeAreaManager 判定通用安全区无效 | 边界 |
| AC-2.3 | WHEN useCutout=false THEN CUTOUT 不进入组合结果；SYSTEM 仍可合并导航与浮动导航区 | 正常 |
| AC-2.4 | WHEN SceneBoard 或 UIExtension 使用独立缓存/宿主输入 THEN 读取对应缓存路径，不把普通窗口的 processed 值强制套用 | 边界 |

## 验收追溯

| AC | 关联规则 | 关联 Task | 验证方式 | 证据 |
|----|----------|-----------|----------|------|
| AC-1.1~AC-1.3 | R-1~R-3 | 已有实现 | Insets/adapter 边界测试 | `interfaces/inner_api/ace_kit/include/ui/properties/safe_area_insets.h:38-49`; `adapter/ohos/entrance/utils.cpp:130-152`; `frameworks/core/components_ng/manager/safe_area/safe_area_manager.cpp:23-42,78-100` |
| AC-1.4~AC-2.1 | R-4~R-5 | 已有实现 | Window/Pipeline UT | `adapter/ohos/entrance/ui_content_impl.cpp:2876-2902`; `frameworks/core/pipeline_ng/pipeline_context.cpp:2360-2383` |
| AC-2.2~AC-2.4 | R-6~R-8 | 已有实现 | Manager/SceneBoard UT | `frameworks/core/components_ng/manager/safe_area/safe_area_manager.cpp:157-177,210-217,285-353` |

## 规则定义

| 规则ID | 类型 | 触发条件 | 预期行为 | 边界/约束 | 关联AC |
|--------|------|----------|----------|-----------|--------|
| R-1 | 行为 | AvoidArea Rect 可转换 | 将 Rect 转换为四向区间 | adapter 不做统一根边界裁剪 | AC-1.1 |
| R-2 | 边界 | start>=end 或区间超出根尺寸 | start>=end 无效；SYSTEM/NAVIGATION 的根外有效区间仍保存；CUTOUT/FLOAT_NAVIGATION 仅归一贴边端点 | 有效性的统一条件仅为 start<end | AC-1.2 |
| R-3 | 行为 | 类型与边掩码匹配 | 返回对应区间 | 未匹配边为空 | AC-1.3 |
| R-4 | 行为 | viewport/旋转变化 | 刷新四类输入和键盘底边 | 使用新根尺寸 | AC-1.4 |
| R-5 | 行为 | 初始化且版本满足 | 拉取四类 AvoidArea | 最低平台门槛 10 | AC-2.1 |
| R-6 | 边界 | 非全屏/不避让/全局忽略 | 通用 safe area 无效 | 键盘独立路径除外 | AC-2.2 |
| R-7 | 行为 | useCutout=false | 排除 cutout 并合并其余系统区 | nav/float-nav 可参与 | AC-2.3 |
| R-8 | 边界 | SceneBoard/UIExtension | 使用对应缓存或宿主输入 | processed/without-process 不混用 | AC-2.4 |

## 验证映射

| 编号 | 对应规格项 | 验证方式 | 验证重点 |
|------|------------|----------|----------|
| VM-1 | AC-1.1~AC-1.3 | Manager/adapter 边界测试 | `start<end`、根外 SYSTEM/NAVIGATION 区间及 CUTOUT/FLOAT_NAVIGATION 端点归一 |
| VM-2 | AC-1.4~AC-2.1 | viewport/window 模拟 UT | 初始化、旋转、根尺寸 |
| VM-3 | AC-2.2~AC-2.4 | Manager/SceneBoard UT | 门控和缓存路径 |

## API 变更分析

### 新增 API

N/A，本 Feat 描述框架内部数据聚合，不新增公开 API。

### 变更/废弃 API

N/A。

## 接口规格

### 接口定义

**SafeAreaManager 数据更新（InnerApi）**

| 属性 | 值 |
|------|-----|
| 函数签名 | `UpdateSystemSafeArea / UpdateCutoutSafeArea / UpdateNavSafeArea / UpdateKeyboardSafeArea` |
| 返回值 | void — 更新当前 Pipeline 安全区状态 |
| 开放范围 | InnerApi |
| 错误码 | N/A |
| 关联 AC | AC-1.1~AC-2.4 |

**参数约束**

| 参数 | 类型 | 必填 | 默认值 | 约束条件 |
|------|------|------|--------|----------|
| insets | SafeAreaInsets | 是 | 空区间 | 每边仅在 start<end 时有效；SYSTEM/NAVIGATION 不统一校验根边界 |
| rootSize | SizeF | 是 | 当前 Pipeline 根尺寸 | 用于 CUTOUT/FLOAT_NAVIGATION 贴边端点归一和键盘重算，不构成所有类型的通用裁剪条件 |

**行为场景**

| # | 触发条件 | 预期行为 | 关联 AC |
|---|----------|----------|---------|
| 1 | 窗口 AvoidArea 更新 | 转换并写对应类型 | AC-1.1, AC-1.4 |
| 2 | 安全区门控关闭 | 查询结果不参与通用布局 | AC-2.2 |

## 兼容性声明

- **已有 API 行为变更:** 是；平台 10 起初始化窗口避让区，系统窗口另有 API target 18 门控。
- **配置文件格式变更:** 否；CUTOUT 是否生效仍受既有 metadata/useCutout 控制。
- **数据存储格式变更:** 否。
- **最低支持版本:** 平台 API 10 的窗口安全区同步路径。
- **API 版本号策略:** 内部能力按源代码门控记录，不将 Window API 重复归入本 FuncID。

## 架构约束

| 关键约束 | 约束说明 | 影响 AC |
|----------|----------|--------|
| 外部输入归属 | Window AvoidArea 属窗口机制，本 Feat 只定义消费与聚合 | AC-1.1 |
| 单一 Manager | Pipeline 内安全区状态集中在 SafeAreaManager | AC-1.3 |
| 双读取路径 | processed、without-process、SceneBoard 缓存不得混为单值 | AC-2.4 |

## 非功能性需求

| 类型 | 指标/阈值 | 验证方式 | 证据 |
|------|-----------|----------|------|
| 性能 | 每次窗口更新按固定类型和四条边合并 | Trace | `frameworks/core/components_ng/manager/safe_area/safe_area_manager.cpp:285-353` |
| 功耗 | 仅响应窗口/viewport 事件，无轮询 | 审查 | VM-2 |
| 内存 | 安全区状态为固定数量 Insets 与缓存 | 内存审查 | VM-3 |
| 安全 | 不存储窗口内容或用户数据 | API 审查 | VM-1 |
| 可靠性 | start>=end 的区间不进入组合结果；根外区间是否保留取决于 Window 类型与输入 | 边界测试 | VM-1 |
| 可测试性 | 各数据源可独立注入 | 单元测试 | VM-1~VM-3 |
| 自动化维测 | Manager Dump 可定位每类 inset | Dump/日志 | AC-2.3 |
| 定界定位 | Window→adapter→Pipeline→Manager 分层 | 代码审查 | Design |

## 多设备适配声明

| 设备类型 | 行为差异 | 规格/约束 | 验证方式 | 证据 |
|----------|----------|-----------|----------|------|
| 手机 | 状态栏、导航栏、刘海常见 | 聚合对应输入 | 真机矩阵 | AC-2.1 |
| 平板 | 浮动导航和多窗口常见 | 按窗口输入更新 | 多窗口测试 | AC-2.3 |
| 折叠屏 | 旋转/展开改变根尺寸与 cutout | 每次 viewport 变化重算 | 折叠态测试 | AC-1.4 |

## 全局特性影响

| 特性 | 适用？ | 结论 | 关联场景 |
|------|--------|------|----------|
| 无障碍 | 否 | 仅提供几何输入 | VM-1 |
| 大字体 | 否 | 不改变 inset 来源 | VM-1 |
| 深色模式 | 否 | 不涉及颜色 | VM-1 |
| 多窗口/分屏 | 是 | 每个窗口独立安全区 | AC-1.4 |
| 多用户 | 否 | 无用户数据 | VM-1 |
| 版本升级 | 是 | 平台/API target 门控需回归 | AC-2.1 |
| 生态兼容 | 是 | 外部输入差异必须可追溯 | AC-2.4 |

## 行为场景（可选，Gherkin）

```gherkin
Feature: 安全区窗口同步
  Scenario: 折叠展开后刷新安全区
    Given 窗口已注册系统栏和刘海避让区
    When 根尺寸与方向发生变化
    Then Pipeline 重新读取避让区并更新四向安全区和键盘底边
```

## Spec 自审清单

- [x] 无占位文本
- [x] AC 使用 WHEN/THEN
- [x] 数据源、门控、缓存和窗口边界明确
- [x] Window API 仅作为外部输入引用
- [x] AC、规则、VM 一致

## context-references

```yaml
context-queries:
  - repo: "openharmony/arkui_ace_engine"
    query: "SafeAreaManager AvoidArea SceneBoard viewport cutout navigation"
  - repo: "openharmony/interface_sdk-js"
    query: "window AvoidArea safe area"
```

**关键文档：** `04-common-capability/02-safe-area/01-safe-area-mechanism/design.md`
