# 特性规格

## 概述

| 字段 | 内容 |
|---|---|
| 特性名称 | Image 分析开关、配置与支持条件 |
| 特性编号 | Func-04-23-01-Feat-01 |
| FuncID | 04-23-01 |
| 所属 Epic | 无 |
| 优先级 | P0 |
| 目标版本 | Dynamic API 11+ / Static API 23+ / Node C API 21+ |
| SIG 归属 | ArkUI SIG |
| 状态 | Baselined |
| 复杂度 | 关键 |
| lineage | new-on-legacy（已有实现规格补录） |

## 本次变更范围（Delta）

> 本文档补录现有实现，不修改产品行为。

| 类型 | 内容 | 说明 |
|---|---|---|
| ADDED | enableAnalyzer/analyzerConfig | 存量能力补录 |
| ADDED | Node C API NODE_IMAGE_ENABLE_ANALYZER | API 21 |

## 输入文档

- **设计文档**: `04-common-capability/23-ai-capability/01-image-analysis/design.md`
- **SDK 类型定义**:
  - `interface/sdk-js/api/@internal/component/ets/image.d.ts`
  - `interface/sdk-js/api/arkui/component/image.static.d.ets`
  - `interfaces/native/native_node.h`
- **实现证据**:
  - `frameworks/core/components_ng/pattern/image/image_pattern.cpp:2575`
  - `frameworks/core/components_ng/pattern/image/image_pattern.cpp:2596`
  - `frameworks/core/components_ng/pattern/image/image_pattern.cpp:2625`
  - `adapter/ohos/osal/image_analyzer_manager.cpp:252`
  - `interfaces/native/node/style_modifier.cpp:15621`

> 需求基线、不涉及项、受影响子系统与仓库详见 proposal.md；本特性为存量能力补录，无独立 proposal.md。

## 用户故事

### US-1: 启用并配置分析

**角色**: 应用开发者  
**期望**: 为 Image 开启 AI 分析并指定分析配置  
**价值**: 按需使用设备分析能力

| AC编号 | 验收标准 | 类型 |
|---|---|---|
| AC-1.1 | WHEN enableAnalyzer(true) 且编译支持分析能力 THEN创建 ImageAnalyzerManager 并注册可见区变化 | 正常 |
| AC-1.2 | WHEN enableAnalyzer(false) THEN销毁现有 Analyzer Overlay | 恢复 |
| AC-1.3 | WHEN analyzerConfig 在未启用分析时设置 THEN配置无操作返回 | 边界 |

### US-2: 判定支持条件

**角色**: 应用开发者  
**期望**: 只在可分析图像和设备状态下创建分析能力  
**价值**: 避免在不支持状态下产生效果

| AC编号 | 验收标准 | 类型 |
|---|---|---|
| AC-2.1 | WHEN已启用、已解码 image 非空、来源非 SVG、frameCount 小于等于 1 且平台支持 THEN支持分析 | 正常 |
| AC-2.2 | WHEN Image 被禁用、obscured 包含 PLACEHOLDER 或 objectRepeat 不是 NoRepeat THEN不支持分析 | 边界 |
| AC-2.3 | WHEN未编译 SUPPORT_IMAGE_ANALYZER THEN IsSupportImageAnalyzerFeature 返回 false | 边界 |
| AC-2.4 | WHEN Node C API item 缺少一个整型参数 THEN返回 ERROR_CODE_PARAM_INVALID | 异常 |

## 验收追溯

| AC | 关联规则 | 关联 Task | 验证方式 | 证据 |
|---|---|---|---|---|
| AC-1.1 | R-1 | TASK-042301-01 | 源码审查 + 定向 UT/预览用例 | frameworks/core/components_ng/pattern/image/image_pattern.cpp:2575<br>frameworks/core/components_ng/pattern/image/image_pattern.cpp:2596<br>frameworks/core/components_ng/pattern/image/image_pattern.cpp:2625 |
| AC-1.2 | R-2 | TASK-042301-01 | 源码审查 + 定向 UT/预览用例 | frameworks/core/components_ng/pattern/image/image_pattern.cpp:2575<br>frameworks/core/components_ng/pattern/image/image_pattern.cpp:2596<br>frameworks/core/components_ng/pattern/image/image_pattern.cpp:2625 |
| AC-1.3 | R-3 | TASK-042301-01 | 源码审查 + 定向 UT/预览用例 | frameworks/core/components_ng/pattern/image/image_pattern.cpp:2575<br>frameworks/core/components_ng/pattern/image/image_pattern.cpp:2596<br>frameworks/core/components_ng/pattern/image/image_pattern.cpp:2625 |
| AC-2.1 | R-4 | TASK-042301-01 | 源码审查 + 定向 UT/预览用例 | frameworks/core/components_ng/pattern/image/image_pattern.cpp:2575<br>frameworks/core/components_ng/pattern/image/image_pattern.cpp:2596<br>frameworks/core/components_ng/pattern/image/image_pattern.cpp:2625 |
| AC-2.2 | R-5 | TASK-042301-01 | 源码审查 + 定向 UT/预览用例 | frameworks/core/components_ng/pattern/image/image_pattern.cpp:2575<br>frameworks/core/components_ng/pattern/image/image_pattern.cpp:2596<br>frameworks/core/components_ng/pattern/image/image_pattern.cpp:2625 |
| AC-2.3 | R-6 | TASK-042301-01 | 源码审查 + 定向 UT/预览用例 | frameworks/core/components_ng/pattern/image/image_pattern.cpp:2575<br>frameworks/core/components_ng/pattern/image/image_pattern.cpp:2596<br>frameworks/core/components_ng/pattern/image/image_pattern.cpp:2625 |
| AC-2.4 | R-7 | TASK-042301-01 | 源码审查 + 定向 UT/预览用例 | frameworks/core/components_ng/pattern/image/image_pattern.cpp:2575<br>frameworks/core/components_ng/pattern/image/image_pattern.cpp:2596<br>frameworks/core/components_ng/pattern/image/image_pattern.cpp:2625 |

## 规则定义

> 类型标签：行为、边界、异常、恢复。

| 规则ID | 类型 | 触发条件 | 预期行为 | 边界/约束 | 关联AC |
|---|---|---|---|---|---|
| R-1 | 行为 | enable=true 且 SUPPORT_IMAGE_ANALYZER | 创建 manager 并注册可见区 | 默认 enable=false | AC-1.1 |
| R-2 | 恢复 | enable=false | DestroyAnalyzerOverlay | 即使未创建 overlay 也可调用 | AC-1.2 |
| R-3 | 边界 | 配置时 isEnableAnalyzer_ 为 false | 配置不下发 | Dynamic config 不可动态修改 | AC-1.3 |
| R-4 | 行为 | 所有图像和平台条件同时满足 | 返回 true | frameCount <= 1，非 SVG | AC-2.1 |
| R-5 | 边界 | 组件禁用/obscured/repeat 非 NoRepeat | 返回 false | 任一条件失败即不支持 | AC-2.2 |
| R-6 | 边界 | 未定义 SUPPORT_IMAGE_ANALYZER | 返回 false | 编译期能力门控 | AC-2.3 |
| R-7 | 异常 | Node C API 参数不足 | PARAM_INVALID | 要求一个参数 | AC-2.4 |

## 验证映射

| 编号 | 对应规格项 | 验证方式 | 验证重点 |
|---|---|---|---|
| VM-1 | AC-1.1 ~ AC-1.3 | 定向 UT/预览用例 + 源码审查 | 启用并配置分析 |
| VM-2 | AC-2.1 ~ AC-2.4 | 定向 UT/预览用例 + 源码审查 | 判定支持条件 |

## API 变更分析

### 新增 API

> 本次不新增 API；下表记录本特性的现有开放面。

| API 名称 | 开放范围 | 入参概要 | 返回值 | 错误码范围 | 功能描述 | 关联 AC |
|---|---|---|---|---|---|---|
| Image.enableAnalyzer | Public | boolean | ImageAttribute/this | N/A | 启停分析 | AC-1.1 |
| Image.analyzerConfig | System | ImageAnalyzerConfig | ImageAttribute/this | N/A | 设置分析类型 | AC-1.3 |
| NODE_IMAGE_ENABLE_ANALYZER | Public C API | ArkUI_AttributeItem.value[0].i32 | error code/attribute | NO_ERROR/PARAM_INVALID | 节点分析开关 | AC-2.4 |

### 变更/废弃 API

| API 名称 | 变更类型 | 影响场景 | 迁移指引 | 关联 AC |
|---|---|---|---|---|
| N/A | 无 | 无本次 API 变更 | N/A | AC-1.1 |

## 接口规格

### 接口定义

**Image.enableAnalyzer**

| 属性 | 值 |
|---|---|
| 函数签名 | `enableAnalyzer(enable: boolean): ImageAttribute` |
| 返回值 | 当前 ImageAttribute |
| 开放范围 | Public |
| 错误码 | N/A |
| 关联 AC | AC-1.1, AC-1.2 |

**参数约束**

| 参数 | 类型 | 必填 | 默认值 | 约束条件 |
|---|---|---|---|---|
| enable | boolean | 是 | false | true 仍受图像和设备条件限制 |

**行为场景**

| # | 触发条件 | 预期行为 | 关联 AC |
|---|---|---|---|
| 1 | true 且平台支持 | 准备分析 manager | AC-1.1 |
| 2 | false | 销毁 overlay | AC-1.2 |

**Image.analyzerConfig**

| 属性 | 值 |
|---|---|
| 函数签名 | `analyzerConfig(config: ImageAnalyzerConfig): ImageAttribute` |
| 返回值 | 当前 ImageAttribute |
| 开放范围 | System |
| 错误码 | N/A |
| 关联 AC | AC-1.3 |

**参数约束**

| 参数 | 类型 | 必填 | 默认值 | 约束条件 |
|---|---|---|---|---|
| config | ImageAnalyzerConfig | 是 | 全部类型 | 类型不可动态修改；仅启用后下发 |

**行为场景**

| # | 触发条件 | 预期行为 | 关联 AC |
|---|---|---|---|
| 1 | 已启用 | 配置下发 manager | AC-1.3 |
| 2 | 未启用 | 无操作 | AC-1.3 |

**NODE_IMAGE_ENABLE_ANALYZER**

| 属性 | 值 |
|---|---|
| 函数签名 | `setAttribute(node, NODE_IMAGE_ENABLE_ANALYZER, item)` |
| 返回值 | ArkUI_ErrorCode |
| 开放范围 | Public C API |
| 错误码 | NO_ERROR/PARAM_INVALID |
| 关联 AC | AC-2.4 |

**参数约束**

| 参数 | 类型 | 必填 | 默认值 | 约束条件 |
|---|---|---|---|---|
| value[0].i32 | int32_t | 是 | 0 | 转换为 bool |

**行为场景**

| # | 触发条件 | 预期行为 | 关联 AC |
|---|---|---|---|
| 1 | 一个参数 | 设置开关 | AC-1.1 |
| 2 | 参数不足 | PARAM_INVALID | AC-2.4 |

## 兼容性声明

- **已有 API 行为变更:** 否；Dynamic API 11，Static API 23，Node C API 21
- **配置文件格式变更:** 是；启用网络分析需声明 ohos.permission.INTERNET
- **数据存储格式变更:** 否
- **最低支持版本:** Dynamic API 11
- **API 版本号策略:** attributeModifier 自 API 12 可调用；Static 自 API 23

## 架构约束

| 关键约束 | 约束说明 | 影响 AC |
|---|---|---|
| 多条件支持判定 | 开关、解码对象、格式、帧数、组件状态和平台能力全部满足 | AC-2.1, AC-2.2 |
| 编译门控 | SUPPORT_IMAGE_ANALYZER 关闭时始终不支持 | AC-2.3 |
| 配置前置 | analyzerConfig 仅在 enable=true 时下发 | AC-1.3 |

> 架构规则适用性及调用链见 design.md。

## 非功能性需求

| 类型 | 指标/阈值 | 验证方式 | 证据 |
|---|---|---|---|
| 性能 | 不支持条件下不创建分析 overlay | 源码审查 | image_pattern.cpp:2625 |
| 功耗 | 仅 enable 且可见条件满足时参与分析 | 源码审查 | 可见区注册 |
| 内存 | manager 按需创建 | 源码审查 | image_pattern.cpp:2583 |
| 安全 | 需 ohos.permission.INTERNET | 权限审查 | image.d.ts:1723 |
| 可靠性 | 不支持状态返回 false | 边界用例 | IsSupportImageAnalyzerFeature |
| 可测试性 | 支持条件可分别注入 | UT/平台 mock | image_pattern_test |
| 自动化维测 | 分析状态由回调可观察 | 回调用例 | ImageAnalyzerState |
| 定界定位 | C API 参数错误可返回 | C API UT | style_modifier.cpp |

## 多设备适配声明

| 设备类型 | 行为差异 | 规格/约束 | 验证方式 | 证据 |
|---|---|---|---|---|
| 手机 | 依赖设备是否支持 ImageAnalyzer | 沿用现有能力 | 预览/真机 | 对应实现路径 |
| 平板 | 依赖设备是否支持 ImageAnalyzer | 沿用现有能力 | 预览/真机 | 对应实现路径 |
| 折叠屏 | 依赖设备是否支持 ImageAnalyzer | 涉及 hover 时按 SDK 配置 | 折叠屏验证 | SDK options 定义 |

## 全局特性影响

| 特性 | 适用？ | 结论 | 关联场景 |
|---|---|---|---|
| 无障碍 | 是 | 沿用组件/图像现有无障碍语义 | 主路径 |
| 大字体 | 是 | 文本和弹窗样式沿用系统字体缩放；固定按钮高度以 SDK 声明为准 | 样式验证 |
| 深色模式 | 是 | ResourceColor/主题资源随主题切换 | 主题验证 |
| 多窗口/分屏 | 是 | 布局受当前窗口约束 | 窗口尺寸变化 |
| 多用户 | 否 | 无用户态持久化 | N/A |
| 版本升级 | 是 | Dynamic/Static/Node C API 版本不同，且依赖设备能力 | 兼容性矩阵 |
| 生态兼容 | 是 | Dynamic/Static 声明按各自 API 版本保持一致 | 双前端审查 |

## 行为场景（可选，Gherkin）

```gherkin
Feature: Image 分析开关、配置与支持条件
  Scenario: 主路径
    Given 当前运行环境满足对应 API、资源和平台前置条件
    When enableAnalyzer(true) 且编译支持分析能力
    Then 创建 ImageAnalyzerManager 并注册可见区变化
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
    query: "ImagePattern IsSupportImageAnalyzerFeature"
  - repo: "openharmony/ace_engine"
    query: "Image enableAnalyzer C API"
```

**关键文档:**
- `interface/sdk-js/api/@internal/component/ets/image.d.ts`
- `interface/sdk-js/api/arkui/component/image.static.d.ets`
- `interfaces/native/native_node.h`
- `frameworks/core/components_ng/pattern/image/image_pattern.cpp:2575`
- `frameworks/core/components_ng/pattern/image/image_pattern.cpp:2596`
- `frameworks/core/components_ng/pattern/image/image_pattern.cpp:2625`
