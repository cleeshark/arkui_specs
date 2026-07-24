# 特性规格

> Func-05-14-02-Feat-07 Canvas 图像分析与多范式兼容存量规格。

## 概述

| 属性 | 值 |
|------|-----|
| 特性名称 | Canvas 图像分析与多范式兼容 |
| 特性编号 | Func-05-14-02-Feat-07 |
| 所属 Epic | 无（已有能力补录） |
| 优先级 | P1 |
| 目标版本 | API 26 |
| SIG 归属 | ArkUI SIG |
| 状态 | Baselined |
| 复杂度 | 复杂 |

本特性覆盖 Canvas AI 图像分析的启停、选项和互斥约束，以及 Dynamic、Static、FrameNode/Builder、ArkTS native bridge 与内部 node modifier 的接口映射。内部 modifier/C API 是框架承载路径，不被误记为面向应用的公共 NDK API。

## 本次变更范围（Delta）

| 类型 | 内容 | 说明 |
|------|------|------|
| ADDED | 图像分析 | enableAnalyzer、start/stop、ImageAIOptions 与能力降级 |
| ADDED | 多范式接口 | Dynamic/Static/FrameNode/Builder 的等价与差异 |
| ADDED | 内部桥接边界 | Bridge、Model、node modifier 和 CAPI accessors |

## 输入文档

| 文档 | 路径 | 状态 |
|------|------|------|
| Design | `05-ui-components/14-drawing-components/02-canvas/design.md` | 并行补录 |
| Dynamic SDK | `interface/sdk-js/api/@internal/component/ets/canvas.d.ts:2943-3266,3605-3837` | 已核对 |
| Static SDK | `interface/sdk-js/api/arkui/component/canvas.static.d.ets` | 已核对 |
| Pattern | `frameworks/core/components_ng/pattern/canvas/canvas_pattern.cpp` | 已核对 |
| Bridge/Modifier | `frameworks/core/components_ng/pattern/canvas/bridge/arkts_native_canvas_bridge.cpp` | 已核对 |

## 用户故事

### US-1: 对 Canvas 内容执行设备能力分析

**作为** 应用开发者  
**我想要** 启用并控制画布图像分析  
**以便** 获得主体、文本或对象识别能力

| AC编号 | 验收标准 | 类型 |
|--------|----------|------|
| AC-1.1 | WHEN Canvas 配置 ImageAIOptions、enableAnalyzer(true) 且设备支持分析 THEN startImageAnalyzer 启动当前画布内容分析并通过既有控制器/回调返回状态 | 正常 |
| AC-1.2 | WHEN 调用 stopImageAnalyzer 或关闭 enableAnalyzer THEN 停止分析、释放本轮覆盖层/任务并保持 Canvas 绘制可用 | 边界 |
| AC-1.3 | WHEN 设备不支持、组件未挂载、分析未启用或选项无效 THEN 启动请求按接口约定失败/降级且不影响基础绘制 | 异常 |
| AC-1.4 | WHEN Canvas 同时配置 image analyzer 与 overlay CustomBuilder THEN analyzer 约束优先，overlay 的 CustomBuilder 不生效 | 边界 |

### US-2: 在多种 ArkUI 接入范式中保持核心语义

**作为** 框架维护者  
**我想要** 各公开范式映射到统一 Canvas 模型  
**以便** API 演进时保持兼容且清晰定界

| AC编号 | 验收标准 | 类型 |
|--------|----------|------|
| AC-2.1 | WHEN Dynamic DSL 创建 Canvas THEN JS/ArkTS bridge 将 context、属性和事件写入 CanvasModel/CanvasPattern | 正常 |
| AC-2.2 | WHEN API 23 Static DSL 创建 Canvas THEN 静态构造、属性和独立生命周期注册函数映射到同一核心节点语义 | 正常 |
| AC-2.3 | WHEN API 13+ 通过 FrameNode 或后续 Builder 路径创建/承载 Canvas THEN 仅暴露相应版本声明的能力，且不绕过 context 独占和生命周期约束 | 正常 |
| AC-2.4 | WHEN 内部 ArkUI node modifier 或 CAPI accessor 被框架调用 THEN 其职责限于桥接节点能力，不因此构成公开 NDK 接口承诺 | 边界 |

## 验收追溯

| AC | 关联规则 | 关联 Task | 验证方式 | 证据 |
|----|----------|-----------|----------|------|
| AC-1.1~AC-1.4 | R-1~R-4 | 已有实现 | 源码审查+待补 Analyzer capability/互斥集成测试 | `interface/sdk-js/api/@internal/component/ets/canvas.d.ts:3008-3206,3780-3810`; `frameworks/core/components_ng/pattern/canvas/canvas_pattern.cpp` |
| AC-2.1~AC-2.4 | R-5~R-8 | 已有实现 | Dynamic/Static/Bridge 对照 | `interface/sdk-js/api/arkui/component/canvas.static.d.ets`; `frameworks/core/components_ng/pattern/canvas/bridge/arkts_native_canvas_bridge.cpp` |

## 规则定义

| 规则ID | 类型 | 触发条件 | 预期行为 | 边界/约束 | 关联AC |
|--------|------|----------|----------|-----------|--------|
| R-1 | 行为 | 配置+启用+支持 | 启动分析 | API 12、设备能力依赖 | AC-1.1 |
| R-2 | 恢复 | stop/disable | 停止任务并释放覆盖 | 基础绘制继续 | AC-1.2 |
| R-3 | 异常 | 不支持/状态非法 | 失败或降级 | 不破坏 Canvas | AC-1.3 |
| R-4 | 边界 | analyzer+overlay builder | overlay builder 无效 | SDK 明示互斥约束 | AC-1.4 |
| R-5 | 行为 | Dynamic DSL | Bridge→Model→Pattern | API 8 起 | AC-2.1 |
| R-6 | 行为 | Static DSL | 静态接口映射核心语义 | API 23 起 | AC-2.2 |
| R-7 | 边界 | FrameNode/Builder | 按 since 版本暴露 | 不放宽独占约束 | AC-2.3 |
| R-8 | 边界 | 内部 modifier/CAPI | 仅内部桥接 | 非公共 NDK | AC-2.4 |

## 验证映射

| 编号 | 对应规格项 | 验证方式 | 验证重点 |
|------|------------|----------|----------|
| VM-1 | AC-1.1~AC-1.3 | 源码审查+待补分析能力矩阵集成测试 | 启停、降级、恢复；现有 start/stop accessor 覆盖为 DISABLED |
| VM-2 | AC-1.4 | 待补 overlay 互斥测试 | Builder 不生效，不把禁用用例计作证据 |
| VM-3 | AC-2.1~AC-2.3 | Dynamic/Static/FrameNode 对照 UT | 创建、属性、生命周期 |
| VM-4 | AC-2.4 | API 表面审查 | 内部符号不升格为公共接口 |

## API 变更分析

### 新增 API

N/A；图像分析自 API 12、FrameNode/lifecycle 自 API 13、Static/CanvasParams 自 API 23、Builder 演进至 API 26 均为存量能力。

### 变更/废弃 API

N/A。

## 接口规格

### 接口定义

| 接口组 | 代表接口 | 开放范围 | 关联 AC |
|--------|----------|----------|---------|
| 分析配置 | `Canvas(context, imageAIOptions)`; `Canvas(params)`; `enableAnalyzer` | Public | AC-1.1~AC-1.4 |
| 分析控制 | `startImageAnalyzer`; `stopImageAnalyzer` | Public | AC-1.1~AC-1.3 |
| 多范式 | Dynamic/Static/FrameNode/Builder Canvas | Public、按版本 | AC-2.1~AC-2.3 |
| node modifier/CAPI accessor | 内部节点桥接函数 | Internal | AC-2.4 |

## 兼容性声明

- **最低支持版本:** Canvas API 8；分析 API 12。
- **版本节点:** FrameNode/lifecycle API 13；Static 与 CanvasParams API 23；Builder API 26。
- **范式差异:** Dynamic 生命周期使用 `on/off`，Static 使用成对注册/注销；语义对齐但签名不强求相同。
- **NDK 声明:** 本域没有因内部 node modifier/CAPI accessor 而新增公开 NDK 承诺。

## 架构约束

| 关键约束 | 约束说明 | 影响 AC |
|----------|----------|--------|
| 分析依赖 | 分析由可选设备能力和 UI extension/overlay 设施承载 | AC-1.1~AC-1.3 |
| 核心汇聚 | 各 DSL 最终汇聚至 CanvasModel/CanvasPattern | AC-2.1~AC-2.3 |
| 公私边界 | 内部 native modifier 不等于 SDK 公共 NDK | AC-2.4 |

## 非功能性需求

| 类型 | 指标/阈值 | 验证方式 | 证据 |
|------|-----------|----------|------|
| 性能 | 分析任务不得阻塞 Canvas 帧内绘制主路径 | Trace | VM-1 |
| 功耗 | disable/stop 后无持续分析任务 | 功耗测试 | AC-1.2 |
| 内存 | 分析 overlay/controller 生命周期随组件释放 | 泄漏测试 | VM-1 |
| 安全 | 分析能力失败不暴露越界对象 | Fuzz/集成 | AC-1.3 |
| 可靠性 | 不同范式对相同属性产生一致核心状态 | 对照 UT | VM-3 |
| 可测试性 | 能力开关可注入支持/不支持状态 | UT | VM-1 |
| 定界定位 | Analyzer 与 Canvas 绘制链路可分别 Trace | 审查 | Design |

## 多设备适配声明

| 设备类型 | 行为差异 | 规格/约束 | 验证方式 | 证据 |
|----------|----------|-----------|----------|------|
| 手机 | 分析能力依设备 | 不支持时安全降级 | 能力矩阵 | AC-1.3 |
| 平板 | 更大分析区域 | 启停语义不变 | 性能测试 | AC-1.1 |
| 折叠屏 | 尺寸变化后内容更新 | 按最新表面重新分析 | 折叠测试 | Feat-01 |

## 全局特性影响

| 特性 | 适用？ | 结论 | 关联场景 |
|------|--------|------|----------|
| 无障碍 | 是 | 分析结果可辅助识别但不替代应用语义 | AC-1.1 |
| 大字体 | 否 | 分析不控制字体 | VM-1 |
| 深色模式 | 是 | 分析消费实际绘制内容 | AC-1.1 |
| 多窗口/分屏 | 是 | 尺寸/可见性变化需停止或更新任务 | AC-1.2 |
| 版本升级 | 是 | API 12/13/23/26 接口矩阵需回归 | VM-3 |
| 生态兼容 | 是 | 公私 API 边界保持 | AC-2.4 |

## Spec 自审清单

- [x] 分析启停、降级和 overlay 互斥覆盖
- [x] Dynamic/Static 生命周期接口差异明确
- [x] 内部 modifier 未误记为公共 NDK
- [x] AC、规则、VM 一致

## context-references

```yaml
context-queries:
  - repo: "openharmony/arkui_ace_engine"
    query: "Canvas image analyzer native bridge node modifier"
  - repo: "openharmony/interface_sdk-js"
    query: "Canvas enableAnalyzer startImageAnalyzer static API 23"
```

**关键文档：** `05-ui-components/14-drawing-components/02-canvas/design.md`
