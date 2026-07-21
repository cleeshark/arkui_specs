# 特性规格

> Func-05-01-11-Feat-03 Stack PointLight 系统光效：补录灯源位置、强度、颜色、照亮类型、边框宽度与 Bloom 到 RenderContext 的映射、重置和环境门控。

## 概述

| 属性 | 值 |
|------|-----|
| 特性名称 | Stack PointLight 系统光效 |
| 特性编号 | Func-05-01-11-Feat-03 |
| 所属 Epic | 无（已有能力补录） |
| 优先级 | P1 |
| 目标版本 | API 11–26 |
| SIG 归属 | ArkUI SIG |
| 状态 | Baselined |
| 复杂度 | 标准 |

`pointLight(value: PointLightStyle)` 是 API 11 起的 Stage 模型 System API。Stack 入口将 `lightSource`、`illuminated` 和 `bloom` 分解为 RenderContext/Rosen 状态；它不写 `StackLayoutProperty`，因此不改变 Stack 或子节点尺寸与位置。native Static 实现受 `POINT_LIGHT_ENABLE` 编译门控，见 `frameworks/core/interfaces/native/implementation/stack_modifier.cpp:74-108`。

## 本次变更范围（Delta）

| 类型 | 内容 | 说明 |
|------|------|------|
| ADDED | PointLightStyle 分项映射规格 | 覆盖位置、强度、颜色、照亮目标、边框宽度与 Bloom |
| ADDED | 渲染状态更新与重置规格 | 固化 RenderContext 边界和增量 modifier 行为 |
| ADDED | 编译/上下文门控规格 | 覆盖能力关闭、主题资源或渲染节点缺失的安全路径 |

## 输入文档

| 文档 | 路径 | 状态 |
|------|------|------|
| Design | `05-ui-components/01-layout-components/11-stack/design.md` | 已补录 |
| Dynamic SDK | `interface/sdk-js/api/@internal/component/ets/stack.d.ts` | 已核对 |
| Static SDK | `interface/sdk-js/api/arkui/component/stack.static.d.ets` | 已核对 |
| Native implementation | `frameworks/core/interfaces/native/implementation/stack_modifier.cpp` | 已核对 |
| ArkTS modifier | `frameworks/bridge/declarative_frontend/ark_component/src/ArkStack.ts` | 已核对 |

> 本文档只补录 Stack 已有 PointLight 能力，不新增光源模型、主题资源或 Rosen 特效。

## 用户故事

### US-1: 为 Stack 配置点光源

**作为** 具备 System API 使用条件的系统应用开发者  
**我想要** 为 Stack 配置点光源的位置、强度和颜色  
**以便** 让叠放内容获得统一的空间照明效果

| AC编号 | 验收标准 | 类型 |
|--------|----------|------|
| AC-1.1 | WHEN 调用 `pointLight` 且提供完整可解析 `lightSource` THEN 将 x/y/z 位置、intensity 和 color 转换并更新到 Stack RenderContext | 正常 |
| AC-1.2 | WHEN 位置 Dimension 使用受支持单位或 Resource THEN 按当前 Pipeline/主题资源完成解析后提交；解析失败的字段不得导致崩溃 | 边界 |
| AC-1.3 | WHEN 多次设置 PointLight 且某分项变化 THEN 增量 modifier 只比较并更新对应分项，最终 RenderContext 反映最新输入 | 正常 |
| AC-1.4 | WHEN PointLightStyle 或 lightSource 缺少可选字段 THEN 未提供字段按入口既有默认/reset 语义处理，不把未初始化值提交给渲染后端 | 异常 |

### US-2: 配置照亮范围与 Bloom

**作为** 系统视觉效果开发者  
**我想要** 控制被照亮类型、照亮边框宽度和 Bloom  
**以便** 在同一灯源下形成目标组件所需的发光效果

| AC编号 | 验收标准 | 类型 |
|--------|----------|------|
| AC-2.1 | WHEN `illuminated` 提供有效类型 THEN RenderContext 更新 LightIlluminated，并结合主题/实现要求更新 illuminated border width | 正常 |
| AC-2.2 | WHEN `bloom` 提供有效数值 THEN RenderContext 更新 Bloom 状态，后续渲染帧由 Rosen 节点消费 | 正常 |
| AC-2.3 | WHEN illuminated 或 bloom 超出入口支持范围/无法解析 THEN 入口执行既有回退、忽略或 reset，且不得改变布局几何 | 异常 |
| AC-2.4 | WHEN 只设置 lightSource、illuminated 或 bloom 中的一个分组 THEN 该分组可独立更新，其他已存在分组不被无关 modifier 覆盖 | 边界 |

### US-3: 在能力不可用时安全降级

**作为** 跨产品构建的系统应用维护者  
**我想要** PointLight 在未编译或渲染环境不完整时安全退化  
**以便** 同一界面在不同产品上仍可创建和布局

| AC编号 | 验收标准 | 类型 |
|--------|----------|------|
| AC-3.1 | WHEN 构建未启用 `POINT_LIGHT_ENABLE` THEN PointLight native 入口安全无操作，Stack 的创建、测量、对齐和子节点顺序不受影响 | 边界 |
| AC-3.2 | WHEN FrameNode、RenderContext、主题常量、ResourceAdapter 或 Rosen 节点在相应路径不可用 THEN 实现短路退出，不解引用空对象 | 异常 |
| AC-3.3 | WHEN Static/Dynamic 执行 PointLight reset THEN 清理该入口负责的光源、照亮和 Bloom 状态，之后不继续使用旧输入 | 边界 |
| AC-3.4 | WHEN PointLight 不可用或被重置 THEN 不产生 Measure/Layout dirty 作为必要副作用，Stack 几何结果与未设置光效相同 | 边界 |

## 验收追溯

| AC | 关联规则 | 关联 Task | 验证方式 | 证据 |
|----|----------|-----------|----------|------|
| AC-1.1~AC-1.4 | R-1~R-4 | 已有实现 | ArkTS/native modifier UT | `frameworks/bridge/declarative_frontend/ark_component/src/ArkStack.ts:39-85`; `frameworks/core/interfaces/native/implementation/stack_modifier.cpp:74-108` |
| AC-2.1~AC-2.4 | R-5~R-8 | 已有实现 | RenderContext/Rosen 集成 UT | `frameworks/core/interfaces/native/implementation/stack_modifier.cpp:74-108` |
| AC-3.1~AC-3.4 | R-9~R-12 | 已有实现 | 开关构建 + 空上下文 + reset UT | `frameworks/core/interfaces/native/implementation/stack_modifier.cpp:74-108`; `frameworks/core/interfaces/native/node/node_stack_modifier.cpp:32-155` |

## 规则定义

| 规则ID | 类型 | 触发条件 | 预期行为 | 边界/约束 | 关联AC |
|--------|------|----------|----------|-----------|--------|
| R-1 | 行为 | 有效 lightSource | 更新 RenderContext 的位置、强度和颜色 | 不写 StackLayoutProperty | AC-1.1 |
| R-2 | 边界 | Dimension/Resource 位置输入 | 通过当前上下文解析后提交 | 解析失败安全退出/回退 | AC-1.2 |
| R-3 | 行为 | PointLightStyle 重复设置 | 分项比较并更新变化项 | 最终状态以最新输入为准 | AC-1.3 |
| R-4 | 异常 | 缺失或非法 lightSource 字段 | 按入口默认、忽略或 reset | 不提交未初始化数据 | AC-1.4 |
| R-5 | 行为 | 有效 illuminated | 更新照亮类型及所需 border width | 依赖既有主题/渲染适配 | AC-2.1 |
| R-6 | 行为 | 有效 bloom | 更新 RenderContext Bloom | 由后续渲染帧消费 | AC-2.2 |
| R-7 | 异常 | illuminated/bloom 非法 | 回退、忽略或 reset | 不改变几何 | AC-2.3 |
| R-8 | 边界 | 仅一个属性分组变化 | 只更新相关分组 | 保留无关已设置状态 | AC-2.4 |
| R-9 | 边界 | `POINT_LIGHT_ENABLE` 关闭 | native 入口安全无操作 | Stack 布局仍完整可用 | AC-3.1 |
| R-10 | 异常 | 必要上下文/资源/节点为空 | 在访问前短路退出 | 不崩溃、不产生悬空访问 | AC-3.2 |
| R-11 | 恢复 | pointLight reset | 清理对应 RenderContext 状态 | Dynamic/Static 按各自 modifier 执行 | AC-3.3 |
| R-12 | 边界 | 光效失效/重置 | Measure/Layout 结果保持不变 | 光效属于 Render 分支 | AC-3.4 |

## 验证映射

| 编号 | 对应规格项 | 验证方式 | 验证重点 |
|------|------------|----------|----------|
| VM-1 | R-1~R-4, AC-1.1~AC-1.4 | ArkTS/native modifier 参数化 UT | x/y/z、intensity、color、Resource 与缺失字段 |
| VM-2 | R-5~R-8, AC-2.1~AC-2.4 | RenderContext/Rosen UT | illuminated、border width、bloom 和增量隔离 |
| VM-3 | R-9~R-10, AC-3.1~AC-3.2 | 编译开关矩阵 + 空对象注入 | 关闭能力和依赖缺失时安全无操作 |
| VM-4 | R-11~R-12, AC-3.3~AC-3.4 | reset + Layout 对照测试 | 状态清理且几何不变 |

## API 变更分析

> 本文档补录已有 System API，不引入新 API 或权限。

### 新增 API

| API 名称 | 开放范围 | 入参概要 | 返回值 | 错误码范围 | 功能描述 | 关联 AC |
|----------|----------|----------|--------|------------|----------|---------|
| `pointLight(value: PointLightStyle)` | System Dynamic | lightSource、illuminated、bloom | `StackAttribute` | N/A | API 11 设置 Stack 点光源效果 | AC-1.1~AC-3.4 |
| Static `pointLight(value?: PointLightStyle)` | System Static | PointLightStyle/undefined | `StackAttribute` | N/A | API 23 Static 设置或重置光效 | AC-1.1~AC-3.4 |

### 变更/废弃 API

| API 名称 | 变更类型 | 影响场景 | 迁移指引 | 关联 AC |
|----------|----------|----------|----------|---------|
| 无 | 无 | 本次仅补录 System API 已有行为 | 无需迁移 | AC-1.1~AC-3.4 |

## 接口规格

### 接口定义

**StackAttribute.pointLight(value)**

| 属性 | 值 |
|------|-----|
| 函数签名 | Dynamic `pointLight(value: PointLightStyle): StackAttribute`；Static `pointLight(value: PointLightStyle \| undefined): StackAttribute` |
| 返回值 | 当前 StackAttribute |
| 开放范围 | System API、Stage 模型；Dynamic API 11，Static API 23 |
| 错误码 | N/A；不支持环境安全降级 |
| 关联 AC | AC-1.1~AC-3.4 |

**参数约束**

| 参数 | 类型 | 必填 | 默认值 | 约束条件 |
|------|------|------|--------|----------|
| value | PointLightStyle | Dynamic 是；Static 可 undefined | 无光效 | System API；字段按 SDK PointLightStyle 定义 |
| value.lightSource | LightSource | 否 | 未设置 | 可含位置、强度、颜色 |
| value.illuminated | IlluminatedType | 否 | 未设置 | 仅接受 SDK 枚举 |
| value.bloom | number | 否 | 未设置 | 由入口校验/转换 |

**行为场景索引**

| # | 触发条件 | 预期行为 | 关联 AC |
|---|----------|----------|---------|
| 1 | 完整 PointLightStyle | 所有分项提交 RenderContext | AC-1.1, AC-2.1, AC-2.2 |
| 2 | 部分/重复设置 | 独立增量更新，不覆盖无关分组 | AC-1.3, AC-2.4 |
| 3 | 非法值/缺少环境 | 安全回退或无操作 | AC-1.4, AC-2.3, AC-3.1, AC-3.2 |
| 4 | reset | 清理光效且布局几何不变 | AC-3.3, AC-3.4 |

## 兼容性声明

- **已有 API 行为变更:** 否；PointLight 保持 System API 和 Stage 模型边界。
- **配置文件格式变更:** 否；只读取既有主题/资源。
- **数据存储格式变更:** 否；状态随 RenderContext 生命周期存在。
- **最低支持版本:** Dynamic API 11；Static API 23。
- **API 版本号策略:** 以 canonical SDK 为准；构建宏表示产品能力，不改变 API 文档版本。

| 版本/环境 | 行为 | 证据 |
|-----------|------|------|
| API 11 Dynamic | 暴露 System `pointLight` | `interface/sdk-js/api/@internal/component/ets/stack.d.ts:114-124` |
| API 23 Static | Static 属性接受 PointLightStyle/undefined | `interface/sdk-js/api/arkui/component/stack.static.d.ets:54-72` |
| 编译开关开启 | native 实现提交分项状态 | `frameworks/core/interfaces/native/implementation/stack_modifier.cpp:74-108` |
| 编译开关关闭 | 入口不应用 PointLight | 同上 `#ifdef POINT_LIGHT_ENABLE` |

## 架构约束

| 关键约束 | 约束说明 | 影响 AC |
|---------|----------|--------|
| 布局/渲染分离 | PointLight 只写 RenderContext，不写 StackLayoutProperty | AC-2.3, AC-3.4 |
| System API 可见性 | 不向普通 Public SDK 扩张权限范围 | AC-1.1 |
| 后端适配边界 | ArkUI 经 RenderContext 连接 Rosen，不直接管理后端资源 | AC-1.1~AC-2.4 |
| 能力门控 | 产品可通过既有宏关闭实现，关闭时必须安全无操作 | AC-3.1 |

## 非功能性需求

| 类型 | 指标/阈值 | 验证方式 | 证据 |
|------|-----------|----------|------|
| 性能 | 属性更新为常数个 RenderContext 分项，不新增布局遍历 | Trace/代码审查 | `frameworks/core/interfaces/native/implementation/stack_modifier.cpp:74-108` |
| 功耗 | 未设置或门控关闭时不产生持续光效任务；实际合成沿用 Rosen | GPU/功耗对照 | VM-2, VM-3 |
| 内存 | 不创建独立长期光源对象树，状态随 RenderContext | 生命周期测试 | VM-4 |
| 安全 | 仅 System API 可见，不接触敏感数据 | SDK/权限审查 | Dynamic/Static d.ts |
| 可靠性 | 缺失资源、上下文、节点或非法字段不得崩溃 | 故障注入/fuzz | AC-1.4, AC-2.3, AC-3.2 |
| 可测试性 | 各分项可在 RenderContext 单独读取或 mock | Modifier/Render UT | VM-1, VM-2 |
| 自动化维测 | 可通过渲染属性 dump/trace 观察是否提交 | Inspector/trace | RenderContext |
| 定界定位 | 区分 SDK 解析、modifier、RenderContext 与 Rosen 四层 | 源码追溯 | `design.md` |

## 多设备适配声明

| 设备类型 | 行为差异 | 规格/约束 | 验证方式 | 证据 |
|----------|----------|-----------|----------|------|
| 手机 | 取决于产品构建是否启用光效 | 关闭时安全无操作 | 开关构建矩阵 | AC-3.1 |
| 平板 | 无接口语义差异 | 像素密度影响位置 Dimension 解析 | 多密度渲染测试 | AC-1.2 |
| 折叠屏 | 无 Stack PointLight 专有折叠语义 | 窗口变化不改变布局/渲染分层 | 折叠前后对照 | AC-3.4 |

## 全局特性影响

| 特性 | 适用？ | 结论 | 关联场景 |
|------|--------|------|----------|
| 无障碍 | 否 | 光效不改变语义树；不能作为唯一信息表达 | AC-3.4 |
| 大字体 | 否 | 不改变字体测量 | N/A |
| 深色模式 | 是 | color/主题资源可随主题解析；不定义新主题策略 | AC-1.1, AC-1.2 |
| 多窗口/分屏 | 是 | RenderContext 随窗口重绘，Stack 几何仍由布局处理 | AC-3.4 |
| 多用户 | 否 | 无用户持久状态 | N/A |
| 版本升级 | 是 | API 11/23 和产品构建门控需回归 | 兼容矩阵 |
| 生态兼容 | 是 | 不支持环境的安全降级不得转为崩溃 | AC-3.1, AC-3.2 |

## 行为场景（可选，Gherkin）

```gherkin
Feature: Stack PointLight 系统光效
  Scenario: 提交完整点光源
    Given POINT_LIGHT_ENABLE 已开启且 Stack 有有效 RenderContext
    When 设置包含位置、强度、颜色、illuminated 和 bloom 的 PointLightStyle
    Then RenderContext 的对应分项全部更新
    And Stack 的测量尺寸和子项偏移保持不变

  Scenario: 只更新 Bloom
    Given Stack 已配置 lightSource
    When 仅 bloom 值发生变化
    Then 更新 Bloom
    And 既有 lightSource 保持

  Scenario: 构建未启用能力
    Given POINT_LIGHT_ENABLE 未开启
    When 调用 pointLight
    Then 调用安全无操作
    And Stack 仍完成正常 Measure 和 Layout
```

## Spec 自审清单

- [x] 无占位文本
- [x] 所有 AC 使用 WHEN/THEN 格式，可独立测试
- [x] 范围边界明确：只覆盖 Stack 已有 PointLight 渲染状态
- [x] 无语义模糊表述
- [x] 每个 AC 至少关联一条规则，每条规则至少关联一个 AC
- [x] 每条规则满足可复现、可观测、边界值、关联 AC、无冲突五项检查
- [x] System API、构建门控、布局无副作用和跨设备差异均已声明

## context-references

```yaml
context-queries:
  - repo: "openharmony/arkui_ace_engine"
    query: "Stack pointLight POINT_LIGHT_ENABLE RenderContext light intensity illuminated bloom"
  - repo: "openharmony/interface_sdk-js"
    query: "StackAttribute pointLight PointLightStyle System API 11 static 23"
```

**关键文档：**

- Dynamic SDK：`interface/sdk-js/api/@internal/component/ets/stack.d.ts`
- Static SDK：`interface/sdk-js/api/arkui/component/stack.static.d.ets`
- 架构设计：`05-ui-components/01-layout-components/11-stack/design.md`
