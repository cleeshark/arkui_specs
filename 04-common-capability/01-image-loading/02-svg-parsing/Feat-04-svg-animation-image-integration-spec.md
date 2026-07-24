# 特性规格

## 概述

| 字段 | 内容 |
|---|---|
| 特性名称 | SVG 动画、版本兼容与 Image 集成 |
| 特性编号 | Func-04-01-02-Feat-04 |
| FuncID | 04-01-02 |
| 所属 Epic | 无 |
| 优先级 | P0 |
| 目标版本 | 现有 SVG/Image 实现 |
| SIG 归属 | ArkUI SIG |
| 状态 | Baselined |
| 复杂度 | 关键 |
| lineage | new-on-legacy（已有实现规格补录） |

## 本次变更范围（Delta）

> 本文档补录现有实现，不修改产品行为。

| 类型 | 内容 | 说明 |
|---|---|---|
| ADDED | animate/animateMotion/animateTransform 生命周期 | 存量能力补录 |
| ADDED | SVG2 完整绘制路径和 Image CanvasImage 集成 | 存量能力补录 |

## 输入文档

- **设计文档**: `04-common-capability/01-image-loading/02-svg-parsing/design.md`
- **SDK 类型定义**:
  - `interface/sdk-js/api/@internal/component/ets/image.d.ts`
  - `interface/sdk-js/api/arkui/component/image.static.d.ets`
- **实现证据**:
  - `frameworks/core/components_ng/svg/svg_dom.cpp:58`
  - `frameworks/core/components_ng/svg/svg_dom.cpp:308`
  - `frameworks/core/components_ng/svg/svg_dom.cpp:348`
  - `frameworks/core/components_ng/image_provider/svg_image_object.cpp:45`
  - `frameworks/core/components_ng/render/adapter/svg_canvas_image.cpp:26`

> 需求基线、不涉及项、受影响子系统与仓库详见 proposal.md；本特性为存量能力补录，无独立 proposal.md。

## 用户故事

### US-1: 控制 SVG 动画

**角色**: 应用开发者  
**期望**: 让动画 SVG 触发刷新、播放/暂停和完成回调  
**价值**: 支持 Image 动画生命周期

| AC编号 | 验收标准 | 类型 |
|---|---|---|
| AC-1.1 | WHEN解析到 animate/animateMotion/animateTransform 节点 THEN SvgDom 标记为非静态 | 正常 |
| AC-1.2 | WHEN CanvasImage 注册 redraw 或 finish 回调 THEN 回调转交 SvgContext | 正常 |
| AC-1.3 | WHEN调用 ControlAnimation(true/false) THEN SvgContext 控制已登记 Animator 播放或暂停 | 正常 |

### US-2: 接入 Image 绘制链

**角色**: 图像框架开发者  
**期望**: 把 SvgDom 封装为 SvgCanvasImage 并按版本路径绘制  
**价值**: 维持 Image 加载与渲染契约

| AC编号 | 验收标准 | 类型 |
|---|---|---|
| AC-2.1 | WHEN SvgImageObject 已创建 SvgDom THEN MakeCanvasImage 返回持有该 DOM 的 SvgCanvasImage | 正常 |
| AC-2.2 | WHEN未启用 SVG2 THEN调用 legacy root Draw；WHEN启用 SVG2 THEN使用 SvgLengthScaleRule 完整绘制路径 | 边界 |
| AC-2.3 | WHEN SvgDom 已释放或为空 THEN CanvasImage 绘制无操作返回 | 异常 |

## 验收追溯

| AC | 关联规则 | 关联 Task | 验证方式 | 证据 |
|---|---|---|---|---|
| AC-1.1 | R-1 | TASK-040102-04 | 源码审查 + 定向 UT/预览用例 | frameworks/core/components_ng/svg/svg_dom.cpp:58<br>frameworks/core/components_ng/svg/svg_dom.cpp:308<br>frameworks/core/components_ng/svg/svg_dom.cpp:348 |
| AC-1.2 | R-2 | TASK-040102-04 | 源码审查 + 定向 UT/预览用例 | frameworks/core/components_ng/svg/svg_dom.cpp:58<br>frameworks/core/components_ng/svg/svg_dom.cpp:308<br>frameworks/core/components_ng/svg/svg_dom.cpp:348 |
| AC-1.3 | R-3 | TASK-040102-04 | 源码审查 + 定向 UT/预览用例 | frameworks/core/components_ng/svg/svg_dom.cpp:58<br>frameworks/core/components_ng/svg/svg_dom.cpp:308<br>frameworks/core/components_ng/svg/svg_dom.cpp:348 |
| AC-2.1 | R-4 | TASK-040102-04 | 源码审查 + 定向 UT/预览用例 | frameworks/core/components_ng/svg/svg_dom.cpp:58<br>frameworks/core/components_ng/svg/svg_dom.cpp:308<br>frameworks/core/components_ng/svg/svg_dom.cpp:348 |
| AC-2.2 | R-5 | TASK-040102-04 | 源码审查 + 定向 UT/预览用例 | frameworks/core/components_ng/svg/svg_dom.cpp:58<br>frameworks/core/components_ng/svg/svg_dom.cpp:308<br>frameworks/core/components_ng/svg/svg_dom.cpp:348 |
| AC-2.3 | R-6 | TASK-040102-04 | 源码审查 + 定向 UT/预览用例 | frameworks/core/components_ng/svg/svg_dom.cpp:58<br>frameworks/core/components_ng/svg/svg_dom.cpp:308<br>frameworks/core/components_ng/svg/svg_dom.cpp:348 |

## 规则定义

> 类型标签：行为、边界、异常、恢复。

| 规则ID | 类型 | 触发条件 | 预期行为 | 边界/约束 | 关联AC |
|---|---|---|---|---|---|
| R-1 | 行为 | 解析到 SvgAnimation 实例 | isStatic_ 置 false | 任一动画节点即为动态资源 | AC-1.1 |
| R-2 | 行为 | SvgCanvasImage 注册回调 | 转交 SvgDom/SvgContext | 回调由 WeakClaim 关联 CanvasImage | AC-1.2 |
| R-3 | 行为 | ControlAnimation 接收布尔值 | 控制 SvgContext 中 Animator | 无 Context 时无操作 | AC-1.3 |
| R-4 | 行为 | SvgImageObject 持有有效 SvgDom | 创建 SvgCanvasImage 并 SuccessCallback | 不执行位图 resize | AC-2.1 |
| R-5 | 边界 | SVG2 feature flag | 在 legacy Draw 与 SvgLengthScaleRule Draw 间选择 | 开关来自 ImageSourceInfo | AC-2.2 |
| R-6 | 异常 | SvgDom 为空 | CHECK_NULL 后返回 | 不崩溃、不回调成功 | AC-2.3 |

## 验证映射

| 编号 | 对应规格项 | 验证方式 | 验证重点 |
|---|---|---|---|
| VM-1 | AC-1.1 ~ AC-1.3 | 定向 UT/预览用例 + 源码审查 | 控制 SVG 动画 |
| VM-2 | AC-2.1 ~ AC-2.3 | 定向 UT/预览用例 + 源码审查 | 接入 Image 绘制链 |

## API 变更分析

### 新增 API

> 本次不新增 API；下表记录本特性的现有开放面。

| API 名称 | 开放范围 | 入参概要 | 返回值 | 错误码范围 | 功能描述 | 关联 AC |
|---|---|---|---|---|---|---|
| Image(src) | Public | SVG ResourceStr | ImageAttribute | N/A | 加载静态或动画 SVG | AC-2.1 |
| Image.onFinish() | Public | VoidCallback | ImageAttribute | N/A | 动画完成事件由 CanvasImage 转接 | AC-1.2 |

### 变更/废弃 API

| API 名称 | 变更类型 | 影响场景 | 迁移指引 | 关联 AC |
|---|---|---|---|---|
| N/A | 无 | 无公开 API 变更 | N/A | AC-2.1 |

## 接口规格

### 接口定义

**SvgCanvasImage**

| 属性 | 值 |
|---|---|
| 函数签名 | `DrawToRSCanvas / SetRedrawCallback / SetOnFinishCallback / ControlAnimation` |
| 返回值 | void/bool |
| 开放范围 | InnerApi |
| 错误码 | N/A |
| 关联 AC | AC-1.1 ~ AC-2.3 |

**参数约束**

| 参数 | 类型 | 必填 | 默认值 | 约束条件 |
|---|---|---|---|---|
| callback | std::function<void()> | 按方法 | 空 | 由 SvgContext 保存 |
| play | bool | 是 | 无 | true 播放，false 暂停 |

**行为场景**

| # | 触发条件 | 预期行为 | 关联 AC |
|---|---|---|---|
| 1 | 动画 SVG | 非静态并可刷新 | AC-1.1 |
| 2 | SVG2 开启 | 走新长度规则路径 | AC-2.2 |
| 3 | DOM 为空 | 无操作 | AC-2.3 |

## 兼容性声明

- **已有 API 行为变更:** 是；SVG2 同时切换渐变工厂和根节点完整绘制路径
- **配置文件格式变更:** 否
- **数据存储格式变更:** 否
- **最低支持版本:** 随 Image/SVG 既有版本
- **API 版本号策略:** 由 ImageSourceInfo::IsSupportSvg2 选择

## 架构约束

| 关键约束 | 约束说明 | 影响 AC |
|---|---|---|
| Image 集成 | SvgImageObject 仅封装 DOM，SvgCanvasImage 负责绘制和动画桥接 | AC-1.2, AC-2.1 |
| SVG2 完整切换 | 不是单一渐变替换，根绘制签名和长度上下文同时变化 | AC-2.2 |

> 架构规则适用性及调用链见 design.md。

## 非功能性需求

| 类型 | 指标/阈值 | 验证方式 | 证据 |
|---|---|---|---|
| 性能 | 不对 SVG 做位图 resize | 源码审查 | svg_image_object.cpp:45 |
| 功耗 | 动画刷新由回调驱动 | Trace/源码审查 | svg_canvas_image.cpp:52 |
| 内存 | CanvasImage 持有 RefPtr<SvgDomBase> | 源码审查 | svg_canvas_image.h |
| 安全 | N/A | N/A | 无权限 |
| 可靠性 | 空 DOM 无操作 | 异常用例 | CHECK_NULL |
| 可测试性 | 静态/动画/SVG2 资源可分别验证 | previewer | SVG 资源用例 |
| 自动化维测 | IsStatic 和 dump 可观测 | Dump | SvgDom |
| 定界定位 | 创建/绘制失败沿用 ACE_IMAGE 日志 | 日志检查 | SvgDom |

## 多设备适配声明

| 设备类型 | 行为差异 | 规格/约束 | 验证方式 | 证据 |
|---|---|---|---|---|
| 手机 | 无差异 | 沿用现有能力 | 预览/真机 | 对应实现路径 |
| 平板 | 无差异 | 沿用现有能力 | 预览/真机 | 对应实现路径 |
| 折叠屏 | 无差异 | 涉及 hover 时按 SDK 配置 | 折叠屏验证 | SDK options 定义 |

## 全局特性影响

| 特性 | 适用？ | 结论 | 关联场景 |
|---|---|---|---|
| 无障碍 | 是 | 沿用组件/图像现有无障碍语义 | 主路径 |
| 大字体 | 是 | 文本和弹窗样式沿用系统字体缩放；固定按钮高度以 SDK 声明为准 | 样式验证 |
| 深色模式 | 是 | ResourceColor/主题资源随主题切换 | 主题验证 |
| 多窗口/分屏 | 是 | 布局受当前窗口约束 | 窗口尺寸变化 |
| 多用户 | 否 | 无用户态持久化 | N/A |
| 版本升级 | 是 | SVG2 开关影响完整绘制路径 | 兼容性矩阵 |
| 生态兼容 | 是 | Dynamic/Static 声明按各自 API 版本保持一致 | 双前端审查 |

## 行为场景（可选，Gherkin）

```gherkin
Feature: SVG 动画、版本兼容与 Image 集成
  Scenario: 主路径
    Given 当前运行环境满足对应 API、资源和平台前置条件
    When 解析到 animate/animateMotion/animateTransform 节点
    Then SvgDom 标记为非静态
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
    query: "SvgCanvasImage animation callback"
  - repo: "openharmony/ace_engine"
    query: "SVG2 ImageSourceInfo integration"
```

**关键文档:**
- `interface/sdk-js/api/@internal/component/ets/image.d.ts`
- `interface/sdk-js/api/arkui/component/image.static.d.ets`
- `frameworks/core/components_ng/svg/svg_dom.cpp:58`
- `frameworks/core/components_ng/svg/svg_dom.cpp:308`
- `frameworks/core/components_ng/svg/svg_dom.cpp:348`
