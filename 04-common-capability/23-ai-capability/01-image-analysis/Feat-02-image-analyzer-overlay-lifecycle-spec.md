# 特性规格

## 概述

| 字段 | 内容 |
|---|---|
| 特性名称 | Image Analyzer Overlay 生命周期与跨组件管理 |
| 特性编号 | Func-04-23-01-Feat-02 |
| FuncID | 04-23-01 |
| 所属 Epic | 无 |
| 优先级 | P0 |
| 目标版本 | 现有 Image Analyzer 平台实现 |
| SIG 归属 | ArkUI SIG |
| 状态 | Baselined |
| 复杂度 | 关键 |
| lineage | new-on-legacy（已有实现规格补录） |

## 本次变更范围（Delta）

> 本文档补录现有实现，不修改产品行为。

| 类型 | 内容 | 说明 |
|---|---|---|
| ADDED | Analyzer Overlay 创建/更新/销毁 | 存量能力补录 |
| ADDED | 布局、层级、焦点和状态回调 | 存量能力补录 |

## 输入文档

- **设计文档**: `04-common-capability/23-ai-capability/01-image-analysis/design.md`
- **SDK 类型定义**:
  - `interface/sdk-js/api/@internal/component/ets/image.d.ts`
  - `interface/sdk-js/api/@internal/component/ets/image_common.d.ts`
- **实现证据**:
  - `frameworks/core/components_ng/pattern/image/image_pattern.cpp:2636`
  - `frameworks/core/components_ng/pattern/image/image_pattern.cpp:2651`
  - `adapter/ohos/osal/image_analyzer_manager.cpp:56`
  - `adapter/ohos/osal/image_analyzer_manager.cpp:229`
  - `adapter/ohos/osal/image_analyzer_manager.cpp:289`

> 需求基线、不涉及项、受影响子系统与仓库详见 proposal.md；本特性为存量能力补录，无独立 proposal.md。

## 用户故事

### US-1: 创建和更新 Overlay

**角色**: 应用开发者  
**期望**: 在可分析图像上显示分析交互层  
**价值**: 让分析结果覆盖在图像之上

| AC编号 | 验收标准 | 类型 |
|---|---|---|
| AC-1.1 | WHEN支持分析且 overlay 尚未创建并可取得 PixelMap THEN创建 Analyzer Overlay 并挂到 Image 节点 | 正常 |
| AC-1.2 | WHEN overlay 创建完成 THEN设置 ZIndex 为 INT32_MAX、不可聚焦并回调 FINISHED | 正常 |
| AC-1.3 | WHEN scene 未变化或 overlay 未创建 THEN更新请求无操作返回 | 边界 |

### US-2: 同步布局并销毁

**角色**: 框架开发者  
**期望**: 让 overlay 跟随宿主几何并在禁用时释放  
**价值**: 避免残留节点和错误焦点

| AC编号 | 验收标准 | 类型 |
|---|---|---|
| AC-2.1 | WHEN宿主 padding/geometry 更新 THEN overlay 使用 MATCH_PARENT、TOP_LEFT 并按需要校正偏移 | 正常 |
| AC-2.2 | WHEN销毁 overlay THEN解除宿主 OverlayNode、清除分析配置并回调 STOPPED | 恢复 |
| AC-2.3 | WHEN overlay 尚未创建 THEN DestroyAnalyzerOverlay 在释放 analyzer 后无操作返回 | 边界 |

## 验收追溯

| AC | 关联规则 | 关联 Task | 验证方式 | 证据 |
|---|---|---|---|---|
| AC-1.1 | R-1 | TASK-042301-02 | 源码审查 + 定向 UT/预览用例 | frameworks/core/components_ng/pattern/image/image_pattern.cpp:2636<br>frameworks/core/components_ng/pattern/image/image_pattern.cpp:2651<br>adapter/ohos/osal/image_analyzer_manager.cpp:56 |
| AC-1.2 | R-2 | TASK-042301-02 | 源码审查 + 定向 UT/预览用例 | frameworks/core/components_ng/pattern/image/image_pattern.cpp:2636<br>frameworks/core/components_ng/pattern/image/image_pattern.cpp:2651<br>adapter/ohos/osal/image_analyzer_manager.cpp:56 |
| AC-1.3 | R-3 | TASK-042301-02 | 源码审查 + 定向 UT/预览用例 | frameworks/core/components_ng/pattern/image/image_pattern.cpp:2636<br>frameworks/core/components_ng/pattern/image/image_pattern.cpp:2651<br>adapter/ohos/osal/image_analyzer_manager.cpp:56 |
| AC-2.1 | R-4 | TASK-042301-02 | 源码审查 + 定向 UT/预览用例 | frameworks/core/components_ng/pattern/image/image_pattern.cpp:2636<br>frameworks/core/components_ng/pattern/image/image_pattern.cpp:2651<br>adapter/ohos/osal/image_analyzer_manager.cpp:56 |
| AC-2.2 | R-5 | TASK-042301-02 | 源码审查 + 定向 UT/预览用例 | frameworks/core/components_ng/pattern/image/image_pattern.cpp:2636<br>frameworks/core/components_ng/pattern/image/image_pattern.cpp:2651<br>adapter/ohos/osal/image_analyzer_manager.cpp:56 |
| AC-2.3 | R-6 | TASK-042301-02 | 源码审查 + 定向 UT/预览用例 | frameworks/core/components_ng/pattern/image/image_pattern.cpp:2636<br>frameworks/core/components_ng/pattern/image/image_pattern.cpp:2651<br>adapter/ohos/osal/image_analyzer_manager.cpp:56 |

## 规则定义

> 类型标签：行为、边界、异常、恢复。

| 规则ID | 类型 | 触发条件 | 预期行为 | 边界/约束 | 关联AC |
|---|---|---|---|---|---|
| R-1 | 行为 | overlay 未创建且 PixelMap 有效 | 构建节点并 SetOverlayNode | 创建使用 NAPI handle scope | AC-1.1 |
| R-2 | 行为 | overlay 构建完成 | ZIndex=INT32_MAX、Focusable=false、FINISHED | FINISHED 回调后清空回调 | AC-1.2 |
| R-3 | 边界 | overlay 未创建或 scene 未变化 | 不更新 | 避免重复构建/刷新 | AC-1.3 |
| R-4 | 行为 | 布局更新 | MATCH_PARENT/TOP_LEFT 并处理 padding offset | Image holder 额外设置负 render offset | AC-2.1 |
| R-5 | 恢复 | 销毁已创建 overlay | 解绑节点、状态置 false、STOPPED、配置置空 | 先 ReleaseImageAnalyzer | AC-2.2 |
| R-6 | 边界 | 未创建 overlay | 释放 analyzer 后返回 | 不触发 STOPPED | AC-2.3 |

## 验证映射

| 编号 | 对应规格项 | 验证方式 | 验证重点 |
|---|---|---|---|
| VM-1 | AC-1.1 ~ AC-1.3 | 定向 UT/预览用例 + 源码审查 | 创建和更新 Overlay |
| VM-2 | AC-2.1 ~ AC-2.3 | 定向 UT/预览用例 + 源码审查 | 同步布局并销毁 |

## API 变更分析

### 新增 API

> 本次不新增 API；下表记录本特性的现有开放面。

| API 名称 | 开放范围 | 入参概要 | 返回值 | 错误码范围 | 功能描述 | 关联 AC |
|---|---|---|---|---|---|---|
| Image.enableAnalyzer(false) | Public | boolean | ImageAttribute | N/A | 触发 overlay 销毁 | AC-2.2 |
| ImageAnalyzerConfig.onAnalyzed | System | ImageAnalyzerState callback | void | N/A | 报告 FINISHED/STOPPED | AC-1.2, AC-2.2 |

### 变更/废弃 API

| API 名称 | 变更类型 | 影响场景 | 迁移指引 | 关联 AC |
|---|---|---|---|---|
| N/A | 无 | 无公开 API 变更 | N/A | AC-1.1 |

## 接口规格

### 接口定义

**Analyzer Overlay 生命周期（内部）**

| 属性 | 值 |
|---|---|
| 函数签名 | `CreateAnalyzerOverlay / UpdateAnalyzerOverlay / DestroyAnalyzerOverlay / UpdateAnalyzerOverlayLayout` |
| 返回值 | void |
| 开放范围 | InnerApi |
| 错误码 | N/A |
| 关联 AC | AC-1.1 ~ AC-2.3 |

**参数约束**

| 参数 | 类型 | 必填 | 默认值 | 约束条件 |
|---|---|---|---|---|
| pixelMap | RefPtr<PixelMap> | 创建/更新时是 | 无 | 空值无操作 |
| geometryNode | GeometryNode | 布局更新时是 | 无 | 用于 UIConfig |

**行为场景**

| # | 触发条件 | 预期行为 | 关联 AC |
|---|---|---|---|
| 1 | 首次创建 | 挂载 overlay | AC-1.1 |
| 2 | 布局变化 | 同步 offset | AC-2.1 |
| 3 | 禁用 | 解绑并 STOPPED | AC-2.2 |

## 兼容性声明

- **已有 API 行为变更:** 否；生命周期为 enableAnalyzer 的现有实现
- **配置文件格式变更:** 否
- **数据存储格式变更:** 否
- **最低支持版本:** 随 enableAnalyzer API 11
- **API 版本号策略:** 平台实现受 SUPPORT_IMAGE_ANALYZER 控制

## 架构约束

| 关键约束 | 约束说明 | 影响 AC |
|---|---|---|
| 最高叠放层 | Analyzer overlay 使用 INT32_MAX ZIndex | AC-1.2 |
| 焦点隔离 | overlay 不可聚焦 | AC-1.2 |
| 状态闭环 | 创建成功 FINISHED，销毁 STOPPED | AC-1.2, AC-2.2 |
| 禁用即销毁 | EnableAnalyzer(false) 直接 DestroyAnalyzerOverlay | AC-2.2 |

> 架构规则适用性及调用链见 design.md。

## 非功能性需求

| 类型 | 指标/阈值 | 验证方式 | 证据 |
|---|---|---|---|
| 性能 | scene 未变化时不更新 | 源码审查 | image_analyzer_manager.cpp:152 |
| 功耗 | 销毁时 ReleaseImageAnalyzer | 源码审查 | image_analyzer_manager.cpp:229 |
| 内存 | 解绑 OverlayNode 并清空配置 | 生命周期用例 | image_analyzer_manager.cpp:240 |
| 安全 | NAPI scope 显式关闭 | 源码审查 | image_analyzer_manager.cpp:58 |
| 可靠性 | 空节点/PixelMap 无操作 | 异常用例 | CHECK_NULL |
| 可测试性 | 状态回调可观测 | mock analyzer | FINISHED/STOPPED |
| 自动化维测 | overlay build 状态可查询 | UT | IsOverlayCreated |
| 定界定位 | 节点树可见 OverlayNode | Dump | FrameNode |

## 多设备适配声明

| 设备类型 | 行为差异 | 规格/约束 | 验证方式 | 证据 |
|---|---|---|---|---|
| 手机 | 平台支持条件不同；布局始终跟随宿主 | 沿用现有能力 | 预览/真机 | 对应实现路径 |
| 平板 | 平台支持条件不同；布局始终跟随宿主 | 沿用现有能力 | 预览/真机 | 对应实现路径 |
| 折叠屏 | 平台支持条件不同；布局始终跟随宿主 | 涉及 hover 时按 SDK 配置 | 折叠屏验证 | SDK options 定义 |

## 全局特性影响

| 特性 | 适用？ | 结论 | 关联场景 |
|---|---|---|---|
| 无障碍 | 是 | 沿用组件/图像现有无障碍语义 | 主路径 |
| 大字体 | 是 | 文本和弹窗样式沿用系统字体缩放；固定按钮高度以 SDK 声明为准 | 样式验证 |
| 深色模式 | 是 | ResourceColor/主题资源随主题切换 | 主题验证 |
| 多窗口/分屏 | 是 | 布局受当前窗口约束 | 窗口尺寸变化 |
| 多用户 | 否 | 无用户态持久化 | N/A |
| 版本升级 | 是 | overlay 层级、焦点和状态回调为兼容约束 | 兼容性矩阵 |
| 生态兼容 | 是 | Dynamic/Static 声明按各自 API 版本保持一致 | 双前端审查 |

## 行为场景（可选，Gherkin）

```gherkin
Feature: Image Analyzer Overlay 生命周期与跨组件管理
  Scenario: 主路径
    Given 当前运行环境满足对应 API、资源和平台前置条件
    When 支持分析且 overlay 尚未创建并可取得 PixelMap
    Then 创建 Analyzer Overlay 并挂到 Image 节点
```

## Spec 自审清单

- [x] 无"待定""TBD""TODO"等占位符
- [x] 所有 AC 使用 WHEN/THEN 格式，可独立测试
- [x] 范围边界明确
- [x] 无语义模糊表述
- [x] AC 与规则表交叉一致
- [x] 规则表每条通过可复现、可观测、边界值、关联 AC、无冲突检查

## context-references

```yaml
context-queries:
  - repo: "openharmony/ace_engine"
    query: "ImageAnalyzerManager overlay lifecycle"
  - repo: "openharmony/ace_engine"
    query: "Analyzer overlay layout zIndex focus"
```

**关键文档:**
- `interface/sdk-js/api/@internal/component/ets/image.d.ts`
- `interface/sdk-js/api/@internal/component/ets/image_common.d.ts`
- `frameworks/core/components_ng/pattern/image/image_pattern.cpp:2636`
- `frameworks/core/components_ng/pattern/image/image_pattern.cpp:2651`
- `adapter/ohos/osal/image_analyzer_manager.cpp:56`
