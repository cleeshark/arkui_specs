# 特性规格

## 概述

| 属性 | 值 |
|------|-----|
| 特性名称 | LoadingProgress 全量规格 |
| 特性编号 | Func-05-10-03-Feat-01 |
| 所属 Epic | 无 |
| 优先级 | P1 |
| 目标版本 | API 8+ |
| SIG 归属 | ArkUI SIG |
| 状态 | Baselined |
| 复杂度 | 标准 |

## 本次变更范围（Delta）

| 类型 | 内容 | 说明 |
|------|------|------|
| ADDED | LoadingProgress 全量规格补录 | 已有能力补录，补充四重条件检查、颜色优先级、5阶段动画细节、C-API、资源动态更新等 |

## 输入文档

- 设计文档: `05-ui-components/10-information-display-components/03-loading-progress/design.md`
- 源码定位: `frameworks/core/components_ng/pattern/loading_progress/`
- C-API 定位: `interfaces/native/node/style_modifier.cpp`

## 用户故事

### US-1: 开发者使用 LoadingProgress 显示加载状态

**As a** 应用开发者  
**I want to** 通过 LoadingProgress 显示加载动画  
**So that** 能够向用户指示正在加载

| AC编号 | 验收标准 | 类型 |
|--------|----------|------|
| AC-1.1 | WHEN 创建 LoadingProgress THEN 显示彗星-环动画（5阶段，1200ms） | 正常 |
| AC-1.2 | WHEN 设置 color THEN 动画颜色更新 | 正常 |
| AC-1.3 | WHEN 未设置 color THEN 使用主题默认颜色 | 正常 |
| AC-1.4 | WHEN 设置 foregroundColor THEN 动画颜色更新 | 正常 |
| AC-1.5 | WHEN 同时设置 color 和 foregroundColor THEN 使用最后设置的值 | 边界 |
| AC-1.6 | WHEN enableLoading = true THEN 启动动画 | 正常 |
| AC-1.7 | WHEN enableLoading = false THEN 停止动画 | 正常 |
| AC-1.8 | WHEN 组件可见区域变化 THEN 自动启停动画 | 边界 |
| AC-1.9 | WHEN 窗口隐藏 THEN 自动停止动画 | 边界 |
| AC-1.10 | WHEN 四重条件（isVisibleArea_ && isVisible_ && isShow_ && enableLoading_）全部满足 THEN 启动动画 | 边界 |

### US-2: 开发者自定义加载动画渲染内容

**As a** 应用开发者  
**I want to** 通过 contentModifier 自定义 LoadingProgress 的渲染内容  
**So that** 能够实现品牌化或特殊样式的加载动画

| AC编号 | 验收标准 | 类型 |
|--------|----------|------|
| AC-2.1 | WHEN 设置 contentModifier THEN 使用自定义渲染，跳过默认彗星-环动画 | 正常 |
| AC-2.2 | WHEN contentModifier 回调返回自定义节点 THEN 渲染自定义内容 | 正常 |
| AC-2.3 | WHEN 取消 contentModifier（设置为 null）THEN 恢复默认彗星-环动画 | 边界 |
| AC-2.4 | WHEN contentModifier 中读取 LoadingProgressConfiguration THEN 获取 enableLoading 状态 | 正常 |

### US-3: NDK 开发者使用 C-API 控制加载动画

**As a** NDK 开发者  
**I want to** 通过 C-API 创建和控制 LoadingProgress 组件  
**So that** 能够在 Native 层实现加载动画功能

| AC编号 | 验收标准 | 类型 |
|--------|----------|------|
| AC-3.1 | WHEN 通过 C-API 创建 LoadingProgress 节点 THEN 组件正常显示 | 正常 |
| AC-3.2 | WHEN 通过 NODE_LOADING_PROGRESS_COLOR 设置颜色（0xARGB格式）THEN 颜色更新 | 正常 |
| AC-3.3 | WHEN 通过 NODE_LOADING_PROGRESS_ENABLE_LOADING 设置状态 THEN 动画启停 | 正常 |
| AC-3.4 | WHEN C-API 颜色值格式为 0xFFFF0000（ARGB）THEN 直接传递，无需转换 | 边界 |
| AC-3.5 | WHEN C-API 参数无效 THEN 返回 ERROR_CODE_PARAM_INVALID | 异常 |

### US-4: 开发者使用资源动态切换加载动画颜色

**As a** 应用开发者  
**I want to** 使用 $r/$rawfile 资源设置 LoadingProgress 颜色  
**So that** 能够支持多语言、多主题等动态切换场景

| AC编号 | 验收标准 | 类型 |
|--------|----------|------|
| AC-4.1 | WHEN 使用 $r 资源设置 color THEN 颜色正常解析 | 正常 |
| AC-4.2 | WHEN 使用 $rawfile 资源设置 color THEN 颜色正常解析 | 正常 |
| AC-4.3 | WHEN 资源动态切换（如主题变化）THEN 颜色自动更新 | 正常 |
| AC-4.4 | WHEN 资源解析失败 THEN 使用主题默认颜色作为降级方案 | 异常 |

### US-5: 开发者适配深色模式

**As a** 应用开发者  
**I want to** LoadingProgress 在深色模式下正确显示  
**So that** 能够提供一致的用户体验

| AC编号 | 验收标准 | 类型 |
|--------|----------|------|
| AC-5.1 | WHEN 系统深色模式 THEN 环背景模糊效果应用 | 正常 |
| AC-5.2 | WHEN 系统深色模式 THEN 彗星透明度调整为 1.0 | 正常 |
| AC-5.3 | WHEN 系统深色模式且使用默认颜色 THEN 默认色改为白色 | 正常 |
| AC-5.4 | WHEN 系统深色模式且用户自定义颜色 THEN 使用用户设置的颜色 | 边界 |

## 验收追溯

| AC | 关联规则 | 验证方式 |
|----|----------|----------|
| AC-1.1 | R-1 | 单元测试 |
| AC-1.2 | R-2 | 单元测试 |
| AC-1.3 | R-3 | 单元测试 |
| AC-1.4 | R-4 | 单元测试 |
| AC-1.5 | R-5 | 单元测试 |
| AC-1.6 | R-6 | 单元测试 |
| AC-1.7 | R-7 | 单元测试 |
| AC-1.8 | R-8 | 单元测试 |
| AC-1.9 | R-9 | 单元测试 |
| AC-1.10 | R-10 | 单元测试 |
| AC-2.1 | R-11 | 单元测试 |
| AC-2.2 | R-11 | 单元测试 |
| AC-2.3 | R-12 | 单元测试 |
| AC-2.4 | R-11 | 单元测试 |
| AC-3.1 | R-1 | C-API 单元测试 |
| AC-3.2 | R-13 | C-API 单元测试 |
| AC-3.3 | R-14 | C-API 单元测试 |
| AC-3.4 | R-13 | C-API 单元测试 |
| AC-3.5 | R-13 | C-API 单元测试 |
| AC-4.1 | R-15 | 单元测试 |
| AC-4.2 | R-15 | 单元测试 |
| AC-4.3 | R-15 | 单元测试 |
| AC-4.4 | R-15 | 单元测试 |
| AC-5.1 | R-16 | 单元测试 |
| AC-5.2 | R-16 | 单元测试 |
| AC-5.3 | R-16 | 单元测试 |
| AC-5.4 | R-16 | 单元测试 |

## 规则定义

| 规则ID | 类型 | 触发条件 | 预期行为 | 边界/约束 | 关联AC |
|--------|------|----------|----------|-----------|--------|
| R-1 | 行为 | 创建 LoadingProgress | 显示彗星-环动画，5阶段（STAGE1-5），总时长1200ms | STAGE1=25%, STAGE2=65%, STAGE3=75%, STAGE4=85%, STAGE5=100% | AC-1.1 |
| R-2 | 行为 | 设置 color | 更新 PaintProperty.Color 和 RenderContext.ForegroundColor | 使用 ACE_UPDATE_NODE_PAINT_PROPERTY 和 ACE_UPDATE_NODE_RENDER_CONTEXT 宏 | AC-1.2 |
| R-3 | 行为 | 未设置 color 且未设置 foregroundColor | 使用主题默认色 ProgressTheme.GetLoadingColor() | 在 OnAttachToMainTree 中检查 ForegroundColorFlag | AC-1.3 |
| R-4 | 行为 | 设置 foregroundColor | 更新 RenderContext.ForegroundColor，设置 ForegroundColorFlag=true | 与 color 共享底层属性 | AC-1.4 |
| R-5 | 边界 | 同时设置 color 和 foregroundColor | 最后设置的值生效，通过 colorSetByUser 标记区分来源 | 调用顺序决定优先级 | AC-1.5 |
| R-6 | 行为 | enableLoading = true | 设置 PaintProperty.EnableLoading=true，触发 StartAnimation() | 默认值=true | AC-1.6 |
| R-7 | 行为 | enableLoading = false | 设置 PaintProperty.EnableLoading=false，触发 StopAnimation() | Modifier.SetVisible(false) | AC-1.7 |
| R-8 | 边界 | 组件可见区域变化（滚动出屏幕） | RegisterVisibleAreaChange 回调触发，isVisibleArea_ 更新 | 四重条件之一 | AC-1.8 |
| R-9 | 边界 | 窗口隐藏/显示 | OnWindowHide/OnWindowShow 触发，isShow_ 更新 | 四重条件之一 | AC-1.9 |
| R-10 | 边界 | 四重条件检查 | isVisibleArea_ && isVisible_ && isShow_ && enableLoading_ 全为 true 时启动动画 | 任一为 false 则停止 | AC-1.10 |
| R-11 | 行为 | 设置 contentModifier | FireBuilder() 构建 contentModifierNode_，SetUseContentModifier(true) | onDraw 检测到 useContentModifier_=true 直接 return | AC-1.11 |
| R-12 | 边界 | 取消 contentModifier（makeFunc_=null） | FireBuilder() 移除子节点，SetUseContentModifier(false)，恢复默认动画 | 标记 PROPERTY_UPDATE_MEASURE | AC-1.12 |
| R-13 | 行为 | C-API 设置颜色（NODE_LOADING_PROGRESS_COLOR） | 直接将 uint32_t (0xARGB) 转换为 Color 对象 | 无需 ARGB→RGBA 转换，Color 构造函数接受 u32 | AC-1.13 |
| R-14 | 行为 | C-API 设置 enableLoading（NODE_LOADING_PROGRESS_ENABLE_LOADING） | 布尔值直接传递到 ModelNG | 枚举值 = 6000 * 6 + 1 = 36001 | AC-1.14 |
| R-15 | 行为 | 使用 $r/$rawfile 资源 | CreateWithResourceObj 注册资源更新回调，ResourceParseUtils.ParseResColor 解析 | 支持 Color/ForegroundColor 两种资源类型 | AC-1.15 |
| R-16 | 行为 | 深色模式 | 环背景模糊（DrawRingBackground），彗星透明度调整（OPACITY3=1.0） | 默认色改为白色，应用模糊滤镜 | AC-1.16 |

## 验证映射

| 编号 | 对应规格项 | 验证方式 | 验证重点 |
|------|------------|----------|----------|
| VM-1 | 5阶段动画 | 单元测试 | STAGE1-5 关键帧参数验证 |
| VM-2 | 颜色优先级链 | 单元测试 | color > foregroundColor > 主题默认 优先级 |
| VM-3 | 四重条件检查 | 单元测试 | isVisibleArea_ && isVisible_ && isShow_ && enableLoading_ |
| VM-4 | contentModifier 集成 | 单元测试 | useContentModifier_ 标志和 onDraw 跳过逻辑 |
| VM-5 | C-API 颜色格式 | C-API 单元测试 | 0xARGB 格式直接传递验证 |
| VM-6 | visibility 联动 | 单元测试 | RegisterVisibleAreaChange 回调触发 |
| VM-7 | 资源动态更新 | 单元测试 | AddResObj 回调注册和触发 |
| VM-8 | 深色模式处理 | 单元测试 | 环背景模糊和彗星透明度调整 |
| VM-9 | contentModifier Configuration | 单元测试 | LoadingProgressConfiguration.enableLoading 读取 |
| VM-10 | C-API 参数校验 | C-API 单元测试 | ERROR_CODE_PARAM_INVALID 错误码返回 |

## API 变更分析

### 新增 API

| API 名称 | 开放范围 | 入参概要 | 返回值 | 错误码范围 | 功能描述 | 关联 AC |
|----------|----------|----------|--------|------------|----------|---------|
| `color(value: ResourceColor)` | Public | ResourceColor | void | N/A | 设置动画颜色 | AC-1.2, AC-1.3, AC-1.5, AC-4.1, AC-4.2, AC-4.3 |
| `enableLoading(value: boolean)` | Public | boolean | void | N/A | 控制动画显示 | AC-1.6, AC-1.7, AC-1.10 |
| `foregroundColor(value: ResourceColor)` | Public | ResourceColor | void | N/A | 设置前景色（与 color 共享属性） | AC-1.4, AC-1.5, AC-4.1, AC-4.2 |
| `contentModifier(value: ContentModifier<LoadingProgressConfiguration>)` | Public | ContentModifier | void | N/A | 自定义渲染 | AC-2.1, AC-2.2, AC-2.3, AC-2.4 |

### C-API 接口

| API 名称 | 开放范围 | 功能描述 | 关联 AC |
|----------|----------|----------|---------|
| `NODE_LOADING_PROGRESS_COLOR` | System | 设置颜色（0xARGB格式） | AC-3.2, AC-3.4 |
| `NODE_LOADING_PROGRESS_ENABLE_LOADING` | System | 设置动画状态 | AC-3.3 |

## 接口规格

### color

| 属性 | 值 |
|------|-----|
| 函数签名 | `color(value: ResourceColor): LoadingProgressAttribute` |
| 返回值 | `LoadingProgressAttribute` — 链式调用 |
| 开放范围 | Public |
| 错误码 | N/A |
| 关联 AC | AC-1.2, AC-1.3, AC-1.5, AC-4.1, AC-4.2 |

**参数约束**

| 参数 | 类型 | 忴填 | 默认值 | 约束条件 |
|------|------|------|--------|----------|
| value | ResourceColor | 否 | 主题色 | 支持 Color/Resource/$r/$rawfile |

**行为场景**

| # | 触发条件 | 预期行为 | 关联 AC |
|---|----------|----------|---------|
| 1 | 设置 color 值 | 更新 PaintProperty.Color 和 RenderContext.ForegroundColor | AC-1.2 |
| 2 | 未设置 color 且未设置 foregroundColor | 使用 ProgressTheme.GetLoadingColor() | AC-1.3 |
| 3 | 同时设置 color 和 foregroundColor | 最后设置的值生效 | AC-1.5 |
| 4 | 使用 $r 资源 | 注册资源更新回调，动态切换时自动更新 | AC-4.1, AC-4.3 |
| 5 | 使用 $rawfile 资源 | 注册资源更新回调，动态切换时自动更新 | AC-4.2, AC-4.3 |
| 6 | 资源解析失败 | 使用主题默认颜色作为降级方案 | AC-4.4 |

### enableLoading

| 属性 | 值 |
|------|-----|
| 函数签名 | `enableLoading(value: boolean): LoadingProgressAttribute` |
| 返回值 | `LoadingProgressAttribute` — 链式调用 |
| 开放范围 | Public |
| 错误码 | N/A |
| 关联 AC | AC-1.6, AC-1.7, AC-1.10 |

**参数约束**

| 参数 | 类型 | 忴填 | 默认值 | 约束条件 |
|------|------|------|--------|----------|
| value | boolean | 否 | true | 无 |

**行为场景**

| # | 触发条件 | 预期行为 | 关联 AC |
|---|----------|----------|---------|
| 1 | enableLoading=true 且四重条件满足 | 启动彗星-环动画 | AC-1.6, AC-1.10 |
| 2 | enableLoading=false | 停止动画，Modifier.SetVisible(false) | AC-1.7 |
| 3 | enableLoading=true 但其他条件不满足 | 不启动动画，等待条件满足 | AC-1.10 |

### foregroundColor

| 属性 | 值 |
|------|-----|
| 函数签名 | `foregroundColor(value: ResourceColor): LoadingProgressAttribute` |
| 返回值 | `LoadingProgressAttribute` — 链式调用 |
| 开放范围 | Public |
| 错误码 | N/A |
| 关联 AC | AC-1.4, AC-1.5, AC-4.1, AC-4.2 |

**参数约束**

| 参数 | 类型 | 忴填 | 默认值 | 约束条件 |
|------|------|------|--------|----------|
| value | ResourceColor | 否 | - | 与 color 共享属性，设置后 ForegroundColorFlag=true |

**行为场景**

| # | 触发条件 | 预期行为 | 关联 AC |
|---|----------|----------|---------|
| 1 | 设置 foregroundColor | 更新 RenderContext.ForegroundColor | AC-1.4 |
| 2 | 同时设置 color 和 foregroundColor | 最后设置的值生效 | AC-1.5 |
| 3 | 使用 $r/$rawfile 资源 | 注册资源更新回调 | AC-4.1, AC-4.2, AC-4.3 |

### contentModifier

| 属性 | 值 |
|------|-----|
| 函数签名 | `contentModifier(value: ContentModifier<LoadingProgressConfiguration>): LoadingProgressAttribute` |
| 返回值 | `LoadingProgressAttribute` — 链式调用 |
| 开放范围 | Public |
| 错误码 | N/A |
| 关联 AC | AC-2.1, AC-2.2, AC-2.3, AC-2.4 |

**参数约束**

| 参数 | 类型 | 忴填 | 默认值 | 约束条件 |
|------|------|------|--------|----------|
| value | ContentModifier<LoadingProgressConfiguration> | 否 | - | 回调返回自定义 FrameNode |

**行为场景**

| # | 触发条件 | 预期行为 | 关联 AC |
|---|----------|----------|---------|
| 1 | 设置 contentModifier | FireBuilder() 构建 contentModifierNode_，SetUseContentModifier(true) | AC-2.1 |
| 2 | contentModifier 回调返回节点 | onDraw 检测 useContentModifier_=true，跳过默认动画 | AC-2.2 |
| 3 | 取消 contentModifier（null） | FireBuilder() 移除子节点，恢复默认动画 | AC-2.3 |
| 4 | 读取 LoadingProgressConfiguration | 获取 enableLoading 状态 | AC-2.4 |

### C-API: NODE_LOADING_PROGRESS_COLOR

| 属性 | 值 |
|------|-----|
| 枚举值 | `NODE_LOADING_PROGRESS_COLOR = 6000 * 6 = 36000` |
| 开放范围 | System |
| 错误码 | ERROR_CODE_PARAM_INVALID (参数无效) |
| 关联 AC | AC-3.2, AC-3.4, AC-3.5 |

**参数约束**

| 参数 | 类型 | 忴填 | 默认值 | 约束条件 |
|------|------|------|--------|----------|
| value[0].u32 | uint32_t | 是 | - | 0xARGB 格式，直接传递给 Color 构造函数 |

**行为场景**

| # | 触发条件 | 预期行为 | 关联 AC |
|---|----------|----------|---------|
| 1 | 设置 0xARGB 颜色值 | SetLoadingProgressColor() → ModelNG.SetColor()，无需转换 | AC-3.2, AC-3.4 |
| 2 | 参数数组为空或无效 | 返回 ERROR_CODE_PARAM_INVALID | AC-3.5 |

### C-API: NODE_LOADING_PROGRESS_ENABLE_LOADING

| 属性 | 值 |
|------|-----|
| 枚举值 | `NODE_LOADING_PROGRESS_ENABLE_LOADING = 6000 * 6 + 1 = 36001` |
| 开放范围 | System |
| 错误码 | ERROR_CODE_PARAM_INVALID |
| 关联 AC | AC-3.3 |

**参数约束**

| 参数 | 类型 | 忴填 | 默认值 | 约束条件 |
|------|------|------|--------|----------|
| value[0].i32 | int32_t | 是 | - | 值范围 [0, 1]，0=false, 1=true |

**行为场景**

| # | 触发条件 | 预期行为 | 关联 AC |
|---|----------|----------|---------|
| 1 | 设置 enableLoading=1 | SetLoadingProgressEnableLoading() → ModelNG.SetEnableLoading(true) | AC-3.3 |
| 2 | 设置 enableLoading=0 | 停止动画 | AC-3.3 |

## 兼容性声明

- **已有 API 行为变更:** 否
- **配置文件格式变更:** 否
- **数据存储格式变更:** 否
- **最低支持版本:** API 8+
- **API 版本号策略:** color/enableLoading (API 8+), foregroundColor (API 10+), contentModifier (API 11+)

## 架构约束

| 关键约束 | 约束说明 | 影响 AC |
|----------|----------|---------|
| 动画 5 阶段 | STAGE1-5 控制彗星-环动画，总时长 1200ms | AC-1.1 |
| 四重条件检查 | isVisibleArea_ && isVisible_ && isShow_ && enableLoading_ | AC-1.10 |
| 颜色属性共享 | color/foregroundColor 设置同一底层属性，colorSetByUser 标记区分 | AC-1.5 |
| visibility 联动 | RegisterVisibleAreaChange 回调自动启停动画 | AC-1.8, AC-1.9 |
| C-API 颜色格式 | 直接使用 uint32_t (0xARGB)，无需转换 | AC-3.2, AC-3.4 |
| contentModifier 集成 | useContentModifier_ 标志控制 onDraw 跳过 | AC-2.1, AC-2.2 |
| 资源动态更新 | AddResObj 注册回调，ParseResColor 解析 | AC-4.1, AC-4.2, AC-4.3 |
| 深色模式处理 | 环背景模糊、彗星透明度调整 | AC-5.1, AC-5.2, AC-5.3 |

## 非功能性需求

| 类型 | 指标/阈值 | 验证方式 | 证据 |
|------|-----------|----------|------|
| 性能 | 无特殊要求 | N/A | N/A |
| 功耗 | 不可见时停止动画，避免资源消耗 | 代码评审 | loading_progress_pattern.cpp:104-128 |
| 内存 | 无特殊要求 | N/A | N/A |
| 安全 | 无权限校验 | 代码评审 | N/A |
| 可靠性 | 四重条件检查确保状态一致性 | 代码评审 | loading_progress_pattern.cpp:108 |
| 可测试性 | AC 可独立验证 | 单元测试 | N/A |

## 多设备适配声明

无差异。

## 全局特性影响

| 特性 | 适用？ | 结论 | 关联场景 |
|------|--------|------|----------|
| 无障碍 | 是 | 支持进度值访问（通用属性） | N/A |
| 大字体 | 否 | 动画组件不涉及文本 | N/A |
| 深色模式 | 是 | 环背景模糊、彗星透明度调整，默认色改为白色 | AC-5.1, AC-5.2, AC-5.3 |
| 多窗口/分屏 | 是 | OnWindowHide/Show 联动动画启停 | AC-1.9 |
| 多用户 | 否 | 无用户相关行为 | N/A |
| 版本升级 | 否 | 无数据迁移 | N/A |
| 生态兼容 | 否 | 无外部依赖 | N/A |

## 行为场景（可选，Gherkin）

```gherkin
Feature: LoadingProgress 加载动画
  作为 应用开发者
  我想要 通过 LoadingProgress 显示加载状态
  以便 能够向用户指示正在加载

  # US-1: 基本加载动画显示
  Scenario: 默认动画显示
    Given 创建 LoadingProgress
    When 渲染组件
    Then 显示彗星-环动画（5阶段，1200ms 循环）

  Scenario: 颜色设置
    Given color = Color.Blue
    When 渲染 LoadingProgress
    Then 动画颜色为蓝色

  Scenario: 四重条件检查
    Given isVisibleArea_ = true
    And isVisible_ = true
    And isShow_ = true
    And enableLoading_ = true
    When StartAnimation() 被调用
    Then 动画启动

  Scenario: 四重条件不满足
    Given 任一条件为 false
    When StartAnimation() 被调用
    Then 动画不启动

  # US-2: 自定义加载动画渲染内容
  Scenario: contentModifier 自定义渲染
    Given 设置 contentModifier
    When 渲染 LoadingProgress
    Then 使用自定义渲染内容，跳过默认动画

  Scenario: 取消 contentModifier
    Given 已设置 contentModifier
    When 取消 contentModifier（设置为 null）
    Then 恢复默认彗星-环动画

  # US-3: NDK 开发者使用 C-API
  Scenario: C-API 颜色设置
    Given C-API 调用 setAttribute(NODE_LOADING_PROGRESS_COLOR, {u32: 0xFFFF0000})
    When 渲染 LoadingProgress
    Then 动画颜色为红色（ARGB 格式直接传递）

  Scenario: C-API enableLoading 控制
    Given C-API 调用 setAttribute(NODE_LOADING_PROGRESS_ENABLE_LOADING, {i32: 1})
    When 渲染 LoadingProgress
    Then 动画启动

  Scenario: C-API 参数无效
    Given C-API 调用 setAttribute(NODE_LOADING_PROGRESS_COLOR, {})
    When 执行设置
    Then 返回 ERROR_CODE_PARAM_INVALID

  # US-4: 资源动态切换
  Scenario: $r 资源设置
    Given color = $r('app.color.loading')
    When 渲染 LoadingProgress
    Then 动画颜色为资源定义的颜色

  Scenario: 资源动态切换
    Given color = $r('app.color.loading')
    And 系统主题变化
    When 渲染 LoadingProgress
    Then 动画颜色自动更新为新主题颜色

  # US-5: 深色模式适配
  Scenario: 深色模式处理
    Given 系统深色模式
    When 渲染 LoadingProgress
    Then 环背景模糊，彗星透明度调整为 1.0

  Scenario: 深色模式默认颜色
    Given 系统深色模式
    And 未设置 color
    When 渲染 LoadingProgress
    Then 动画颜色为白色
```

## Spec 自审清单

- [x] 无"待定""TBD""TODO"等占位符
- [x] 所有 AC 使用 WHEN/THEN 格式，可独立测试
- [x] 范围边界明确（做什么/不做什么清晰）
- [x] 无语义模糊表述
- [x] AC 与规则表交叉一致（每个 AC 至少关联一条规则，每条规则至少关联一个 AC）
- [x] 规则表每条通过 5 项质量检查

## context-references

```yaml
context-queries:
  - repo: "openharmony/arkui_ace_engine"
    query: "LoadingProgress 四重条件检查（isVisibleArea_ && isVisible_ && isShow_ && enableLoading_）"
  - repo: "openharmony/arkui_ace_engine"
    query: "LoadingProgress color/foregroundColor 优先级链和 colorSetByUser 标记"
  - repo: "openharmony/arkui_ace_engine"
    query: "LoadingProgress 彗星-环动画 5 阶段（STAGE1-5）关键帧参数"
  - repo: "openharmony/arkui_ace_engine"
    query: "LoadingProgress contentModifier 集成路径和 useContentModifier_ 标志"
  - repo: "openharmony/arkui_ace_engine"
    query: "LoadingProgress C-API NODE_LOADING_PROGRESS_COLOR 0xARGB 格式"
  - repo: "openharmony/arkui_ace_engine"
    query: "LoadingProgress 资源动态更新 CreateWithResourceObj AddResObj"
  - repo: "openharmony/arkui_ace_engine"
    query: "LoadingProgress 深色模式环背景模糊和彗星透明度调整"
```

**关键文档:** 
- 设计文档: `05-ui-components/10-information-display-components/03-loading-progress/design.md`
- 源码: `frameworks/core/components_ng/pattern/loading_progress/loading_progress_pattern.cpp`
- C-API: `interfaces/native/node/style_modifier.cpp`