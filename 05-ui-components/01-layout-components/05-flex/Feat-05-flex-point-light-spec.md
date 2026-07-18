# 特性规格

> Func-05-01-05-Feat-05 Flex PointLight 系统光效：固化 System API、构建门控、主题资源、RenderContext 状态与 Rosen 提交路径。

## 概述

| 属性 | 值 |
|------|-----|
| 特性名称 | Flex PointLight 系统光效 |
| 特性编号 | Func-05-01-05-Feat-05 |
| 所属 Epic | 无（已有能力补录） |
| 优先级 | P2 |
| 目标版本 | API 11–26 |
| SIG 归属 | ArkUI SIG |
| 状态 | Baselined |
| 复杂度 | 标准 |

Flex 自 API 11 暴露 System API `pointLight(PointLightStyle)`。光源位置、强度、颜色、受光类型、边框宽度和 bloom 写入通用 RenderContext，再由 RosenRenderContext 换算单位并提交 RSNode；该支路不进入 FlexLayoutProperty，不改变测量和子项位置。证据见 `interface/sdk-js/api/@internal/component/ets/flex.d.ts:175-198`、`frameworks/bridge/declarative_frontend/jsview/js_view_abstract.cpp:10045-10203` 和 `frameworks/core/components_ng/render/adapter/rosen_render_context.cpp:6541-6603`。

## 本次变更范围（Delta）

| 类型 | 内容 | 说明 |
|------|------|------|
| ADDED | PointLight 输入与默认规格 | 覆盖 LightSource、illuminated、bloom 和主题补全 |
| ADDED | 构建/上下文门控规格 | 覆盖 `POINT_LIGHT_ENABLE`、PipelineContext、ThemeConstants、ResourceAdapter |
| ADDED | RenderContext/Rosen 规格 | 覆盖状态写入、px 换算、RSNode 提交、reset 和帧请求 |

## 输入文档

| 文档 | 路径 | 状态 |
|------|------|------|
| Design | `05-ui-components/01-layout-components/05-flex/design.md` | 已补录 |
| Flex SDK | `interface/sdk-js/api/@internal/component/ets/flex.d.ts` | 已核对 |
| Common PointLight type | `interface/sdk-js/api/@internal/component/ets/common.d.ts` | 已核对 |
| Render implementation | `frameworks/core/components_ng/render/adapter/rosen_render_context.cpp` | 已核对 |

## 用户故事

### US-1: 为 Flex 设置点光源

**作为** System API 使用者  
**我想要** 为 Flex 配置点光源和受光效果  
**以便** 呈现系统级空间光效

| AC编号 | 验收标准 | 类型 |
|--------|----------|------|
| AC-1.1 | WHEN API 11+ System 应用调用 `pointLight(style)` 且构建宏开启 THEN 解析 lightSource.position/intensity/color、illuminated 与 bloom，并写入当前 Flex 的 RenderContext | 正常 |
| AC-1.2 | WHEN position 使用 vp/px/fp/lpx 等可转换 Dimension THEN Rosen 提交前按当前 PipelineContext 换算为 px | 正常 |
| AC-1.3 | WHEN style 省略可选字段 THEN 使用当前入口的默认/主题补全路径，不把未提供字段当作布局属性 | 边界 |
| AC-1.4 | WHEN pointLight 更新 THEN Flex 的 frame size、子项测量与 Layout offset 不因光效状态改变 | 正常 |

### US-2: 在环境门控下安全应用效果

**作为** 平台集成者  
**我想要** 光效在构建或运行上下文不可用时安全退化  
**以便** 不影响 Flex 基础布局

| AC编号 | 验收标准 | 类型 |
|--------|----------|------|
| AC-2.1 | WHEN `POINT_LIGHT_ENABLE` 关闭 THEN PointLight 路径不提交光效状态，Flex 布局仍按 Feat-01~03 工作 | 边界 |
| AC-2.2 | WHEN PipelineContext、ThemeConstants、ResourceAdapter 或 RenderContext 不可用 THEN 入口按当前保护路径退出，不进入布局属性写入 | 异常 |
| AC-2.3 | WHEN RSNode 不可用 THEN RosenRenderContext 不解引用空节点，已存在 Flex 布局仍可完成 | 异常 |

### US-3: 更新和清除渲染状态

**作为** 动态界面开发者  
**我想要** 更新或移除 PointLight  
**以便** 生命周期变化后不残留旧效果

| AC编号 | 验收标准 | 类型 |
|--------|----------|------|
| AC-3.1 | WHEN style 合法更新 THEN RenderContext 覆盖对应 light/illuminated/bloom 状态并请求后续渲染帧 | 正常 |
| AC-3.2 | WHEN modifier/Static 路径执行 reset THEN 通过通用 ViewAbstract reset 语义清理或恢复主题默认状态 | 边界 |
| AC-3.3 | WHEN Flex FrameNode 销毁 THEN RenderContext 与后端状态随节点生命周期释放，不保留跨节点所有权 | 边界 |

## 验收追溯

| AC | 关联规则 | 关联 Task | 验证方式 | 证据 |
|----|----------|-----------|----------|------|
| AC-1.1~AC-1.4 | R-1~R-4 | 已有实现 | RenderContext/布局隔离 UT | `frameworks/bridge/declarative_frontend/jsview/js_view_abstract.cpp:10045-10203`; `frameworks/core/components_ng/render/render_property.h:191-199` |
| AC-2.1~AC-2.3 | R-5~R-7 | 已有实现 | 构建矩阵 + 空上下文测试 | `ace_config.gni:51-55`; `frameworks/core/components_ng/render/adapter/rosen_render_context.cpp:6541-6603` |
| AC-3.1~AC-3.3 | R-8~R-10 | 已有实现 | set/reset/生命周期测试 | `frameworks/core/interfaces/native/node/node_common_modifier.cpp:6113-6247`; `frameworks/core/components_ng/base/view_abstract_model_static.cpp:1128-1205` |

## 规则定义

| 规则ID | 类型 | 触发条件 | 预期行为 | 边界/约束 | 关联AC |
|--------|------|----------|----------|-----------|--------|
| R-1 | 行为 | 合法 PointLightStyle | 写 LightPosition/Intensity/Color、Illuminated、BorderWidth、Bloom 等 RenderContext 状态 | `frameworks/bridge/declarative_frontend/jsview/js_view_abstract.cpp:10045-10203` | AC-1.1 |
| R-2 | 行为 | Rosen 提交 position | 使用 PipelineContext 将 Dimension 转 px | `frameworks/core/components_ng/render/adapter/rosen_render_context.cpp:6541-6603` | AC-1.2 |
| R-3 | 边界 | 字段省略 | 沿入口默认/主题资源路径补全或保持 | `interface/sdk-js/api/@internal/component/ets/common.d.ts:29678-29792` | AC-1.3 |
| R-4 | 行为 | 光效状态更新 | 只触发渲染状态，不改 FlexLayoutProperty | `frameworks/core/components_ng/render/render_property.h:191-199` | AC-1.4 |
| R-5 | 边界 | 编译宏关闭 | 光效入口无有效提交，布局不受影响 | `ace_config.gni:51-55` | AC-2.1 |
| R-6 | 异常 | Pipeline/theme/resource/render 上下文缺失 | 按保护路径退出 | Dynamic/Static PointLight 入口 | AC-2.2 |
| R-7 | 异常 | RSNode 为空 | Rosen 保护后退出 | `frameworks/core/components_ng/render/adapter/rosen_render_context.cpp:6541-6603` | AC-2.3 |
| R-8 | 行为 | 合法更新 | 覆盖状态并请求后续帧 | 同上 | AC-3.1 |
| R-9 | 恢复 | reset | 按调用通道使用 common/static reset 语义 | `frameworks/core/interfaces/native/node/node_common_modifier.cpp:6113-6247`; `frameworks/core/components_ng/base/view_abstract_model_static.cpp:1128-1205` | AC-3.2 |
| R-10 | 恢复 | FrameNode 销毁 | RenderContext/RSNode 状态随所有者释放 | 既有节点所有权 | AC-3.3 |

## 验证映射

| 编号 | 对应规格项 | 验证方式 | 验证重点 |
|------|------------|----------|----------|
| VM-1 | R-1~R-4, AC-1.1~AC-1.4 | RenderContext + Layout UT | 字段映射、单位换算、默认值、布局隔离 |
| VM-2 | R-5~R-7, AC-2.1~AC-2.3 | 构建矩阵/空上下文 UT | 宏关闭、主题/资源/RSNode 缺失 |
| VM-3 | R-8~R-10, AC-3.1~AC-3.3 | set/reset/生命周期测试 | 帧请求、状态清理、节点销毁 |

## API 变更分析

> 本文补录已有 System API。

### 新增 API

| API 名称 | 开放范围 | 入参概要 | 返回值 | 错误码范围 | 功能描述 | 关联 AC |
|----------|----------|----------|--------|------------|----------|---------|
| `FlexAttribute.pointLight(value: PointLightStyle)` | System | lightSource/illuminated/bloom | FlexAttribute | N/A | API 11 配置 Flex 点光源 | AC-1.1~AC-3.2 |

### 变更/废弃 API

| API 名称 | 变更类型 | 影响场景 | 迁移指引 | 关联 AC |
|----------|----------|----------|----------|---------|
| 无 | 无 | 本次仅补录光效 | 无需迁移 | AC-1.1~AC-3.3 |

## 接口规格

### 接口定义

| 属性 | 值 |
|------|-----|
| 函数签名 | `pointLight(value: PointLightStyle): FlexAttribute` |
| 返回值 | FlexAttribute |
| 开放范围 | System API，API 11+ |
| 错误码 | N/A |
| 关联 AC | AC-1.1~AC-3.3 |

| 参数 | 类型 | 必填 | 默认值 | 约束条件 |
|------|------|------|--------|----------|
| value.lightSource | LightSource | 否 | 入口/主题默认 | position、intensity、color 按 common.d.ts 约束 |
| value.illuminated | IlluminatedType | 否 | 入口/主题默认 | 影响受光类型与边框资源 |
| value.bloom | number | 否 | 入口/主题默认 | 由 validator/converter 按当前范围处理 |

## 兼容性声明

- **已有 API 行为变更:** 否。
- **配置文件格式变更:** 否。
- **数据存储格式变更:** 否。
- **最低支持版本:** API 11，且仅 System API 可见范围。
- **API 版本号策略:** 以 Flex canonical SDK 和 common PointLightStyle 为准。

| 风险 | 当前证据 | 兼容处理 |
|------|----------|----------|
| Dynamic 路径可能在写入部分 lightSource 后因 ResourceAdapter 缺失退出 | `frameworks/bridge/declarative_frontend/jsview/js_view_abstract.cpp:10160-10182` | 仅记录现状风险；增加部分状态回归，不定义为理想公共语义 |
| ArkTS common modifier 对空 ResourceAdapter 的保护不足 | `frameworks/bridge/declarative_frontend/engine/jsi/nativeModule/arkts_native_common_bridge.cpp:7838-7925` | 空上下文稳定性测试跟踪，本次不改实现 |
| Static converter 的 z 坐标条件与 x/y 分支不一致 | `frameworks/core/interfaces/native/utility/converter.cpp:3654-3665` | 用非对称 x/y/z 输入定界 |
| common node reset 与 Static model reset 的主题恢复路径不同 | `frameworks/core/interfaces/native/node/node_common_modifier.cpp:6113-6247`; `frameworks/core/components_ng/base/view_abstract_model_static.cpp:1128-1205` | 按通道验证，不推断统一 reset |

## 架构约束

| 关键约束 | 约束说明 | 影响 AC |
|---------|----------|--------|
| 布局/渲染解耦 | PointLight 只能写 RenderContext，不写 FlexLayoutProperty | AC-1.4 |
| 构建门控 | 能力受 POINT_LIGHT_ENABLE 约束 | AC-2.1 |
| 主题依赖 | 部分效果需要 ThemeConstants/ResourceAdapter | AC-1.3, AC-2.2 |
| 后端隔离 | 只经 RosenRenderContext 访问 RSNode | AC-1.2, AC-2.3 |

## 非功能性需求

| 类型 | 指标/阈值 | 验证方式 | 证据 |
|------|-----------|----------|------|
| 性能 | 不新增布局开销；状态变化按既有渲染帧提交 | Render trace | AC-1.4, AC-3.1 |
| 功耗 | 只在光效更新时请求帧，不新增周期任务 | 帧请求审查 | AC-3.1 |
| 内存 | 光效状态随 RenderContext/RSNode 生命周期释放 | 生命周期测试 | AC-3.3 |
| 安全 | System API 可见性由 SDK 控制，不处理敏感数据 | SDK 编译/代码审查 | AC-1.1 |
| 可靠性 | 宏关闭和上下文缺失不影响 Flex 布局 | 构建/异常测试 | AC-2.1~AC-2.3 |
| 可测试性 | RenderContext 字段、RSNode 状态和布局尺寸可分别断言 | 分层 UT | VM-1~VM-3 |
| 自动化维测 | 沿用渲染属性与 RS 诊断，不新增协议 | Render dump | RosenRenderContext |
| 定界定位 | 区分 parser/theme/RenderContext/Rosen 四层 | 源码定位 | `05-ui-components/01-layout-components/05-flex/design.md` |

## 多设备适配声明

| 设备类型 | 行为差异 | 规格/约束 | 验证方式 | 证据 |
|----------|----------|-----------|----------|------|
| 手机 | 取决于产品构建与渲染后端能力 | Dimension 按设备 density 转 px | 真机渲染测试 | AC-1.2 |
| 平板 | 无 Flex 专有差异 | 相同后端能力使用相同状态映射 | 多密度测试 | AC-1.1~AC-1.3 |
| 折叠屏 | 窗口变化不改变光效接口 | 重布局与渲染状态更新相互独立 | 折叠态测试 | AC-1.4 |

## 全局特性影响

| 特性 | 适用？ | 结论 | 关联场景 |
|------|--------|------|----------|
| 无障碍 | 否 | 光效不改变语义树 | N/A |
| 大字体 | 否 | PointLight 不参与文本测量 | AC-1.4 |
| 深色模式 | 是 | 主题资源可能改变颜色/阴影效果 | AC-1.3, AC-2.2 |
| 多窗口/分屏 | 是 | 窗口上下文影响 px 换算和渲染提交 | AC-1.2 |
| 多用户 | 否 | 无用户持久状态 | N/A |
| 版本升级 | 是 | API 11 与构建宏边界需回归 | AC-1.1, AC-2.1 |
| 生态兼容 | 是 | Dynamic/Static reset 和上下文缺失风险需定界 | AC-2.2, AC-3.2 |

## 行为场景（可选，Gherkin）

```gherkin
Feature: Flex PointLight 系统光效
  Scenario: 光效不改变布局
    Given 一个已完成布局的 Flex
    When 设置合法 PointLightStyle
    Then RenderContext 保存对应光效状态
    And Flex frame size 与子项 offset 保持不变

  Scenario: 构建宏关闭
    Given POINT_LIGHT_ENABLE 关闭
    When 调用 pointLight
    Then 不向 RSNode 提交点光源
    And Flex 仍可完成 Measure 和 Layout
```

## Spec 自审清单

- [x] 无占位文本
- [x] System API、宏、上下文、RenderContext、Rosen 与 reset 均有验收项
- [x] 光效与布局边界明确
- [x] 实现偏差只列兼容风险
- [x] AC、规则和 VM 闭环

## context-references

```yaml
context-queries:
  - repo: "openharmony/arkui_ace_engine"
    query: "Flex pointLight POINT_LIGHT_ENABLE RenderContext RosenRenderContext ResourceAdapter"
  - repo: "openharmony/interface_sdk-js"
    query: "FlexAttribute pointLight PointLightStyle System API 11"
```

**关键文档：**

- Flex SDK：`interface/sdk-js/api/@internal/component/ets/flex.d.ts`
- Common SDK：`interface/sdk-js/api/@internal/component/ets/common.d.ts`
- 架构设计：`05-ui-components/01-layout-components/05-flex/design.md`
