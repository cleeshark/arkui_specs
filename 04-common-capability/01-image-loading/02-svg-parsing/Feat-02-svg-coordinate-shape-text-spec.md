# 特性规格

## 概述

| 字段 | 内容 |
|---|---|
| 特性名称 | SVG 坐标缩放、基础图形与文本绘制 |
| 特性编号 | Func-04-01-02-Feat-02 |
| FuncID | 04-01-02 |
| 所属 Epic | 无 |
| 优先级 | P0 |
| 目标版本 | 现有 SVG 实现（API 7+） |
| SIG 归属 | ArkUI SIG |
| 状态 | Baselined |
| 复杂度 | 复杂 |
| lineage | new-on-legacy（已有实现规格补录） |

## 本次变更范围（Delta）

> 本文档补录现有实现，不修改产品行为。

| 类型 | 内容 | 说明 |
|---|---|---|
| ADDED | viewBox/ImageFit/viewport 缩放 | 存量能力补录 |
| ADDED | 基础图形路径与兼容管线文本绘制 | 存量能力补录 |

## 输入文档

- **设计文档**: `04-common-capability/01-image-loading/02-svg-parsing/design.md`
- **SDK 类型定义**:
  - `interface/sdk-js/api/@internal/component/ets/image.d.ts`
  - `interface/sdk-js/api/arkui/component/image.static.d.ets`
- **实现证据**:
  - `frameworks/core/components_ng/svg/svg_dom.cpp:348`
  - `frameworks/core/components_ng/svg/parse/svg_rect.cpp:29`
  - `frameworks/core/components_ng/svg/parse/svg_circle.cpp:30`
  - `frameworks/core/components_ng/svg/parse/svg_polygon.cpp:36`
  - `frameworks/compatible/components/svg/rosen_render_svg_text.cpp:29`

> 需求基线、不涉及项、受影响子系统与仓库详见 proposal.md；本特性为存量能力补录，无独立 proposal.md。

## 用户故事

### US-1: 适配布局坐标

**角色**: 应用开发者  
**期望**: SVG 按 ImageFit 和 viewBox 映射到组件区域  
**价值**: 在不同尺寸中保持可预测显示

| AC编号 | 验收标准 | 类型 |
|---|---|---|
| AC-1.1 | WHEN 布局尺寸有效 THEN 先裁剪到布局矩形，再按 ImageFit 计算内容尺寸和缩放 | 正常 |
| AC-1.2 | WHEN 根 viewBox 宽或高小于等于 0 且启用 SVG2 THEN 使用当前 viewport 作为长度规则基准 | 边界 |

### US-2: 绘制图形与文本

**角色**: 应用开发者  
**期望**: 绘制 rect/circle/ellipse/line/path/polygon/polyline 及兼容管线文本  
**价值**: 覆盖当前两条 SVG 实现路径

| AC编号 | 验收标准 | 类型 |
|---|---|---|
| AC-2.1 | WHEN NG SvgDom 解析基础图形标签 THEN 对应节点将属性转换为 RSRecordingPath 后绘制 | 正常 |
| AC-2.2 | WHEN使用 compatible SVG text/tspan/textPath 路径 THEN RosenSvgPainter 按文本样式绘制文字 | 正常 |
| AC-2.3 | WHEN在 NG SvgDom 输入 text 标签 THEN 因 TAG_FACTORIES 未注册 text 而不创建 NG SvgNode | 边界 |

## 验收追溯

| AC | 关联规则 | 关联 Task | 验证方式 | 证据 |
|---|---|---|---|---|
| AC-1.1 | R-1 | TASK-040102-02 | 源码审查 + 定向 UT/预览用例 | frameworks/core/components_ng/svg/svg_dom.cpp:348<br>frameworks/core/components_ng/svg/parse/svg_rect.cpp:29<br>frameworks/core/components_ng/svg/parse/svg_circle.cpp:30 |
| AC-1.2 | R-2 | TASK-040102-02 | 源码审查 + 定向 UT/预览用例 | frameworks/core/components_ng/svg/svg_dom.cpp:348<br>frameworks/core/components_ng/svg/parse/svg_rect.cpp:29<br>frameworks/core/components_ng/svg/parse/svg_circle.cpp:30 |
| AC-2.1 | R-3 | TASK-040102-02 | 源码审查 + 定向 UT/预览用例 | frameworks/core/components_ng/svg/svg_dom.cpp:348<br>frameworks/core/components_ng/svg/parse/svg_rect.cpp:29<br>frameworks/core/components_ng/svg/parse/svg_circle.cpp:30 |
| AC-2.2 | R-4 | TASK-040102-02 | 源码审查 + 定向 UT/预览用例 | frameworks/core/components_ng/svg/svg_dom.cpp:348<br>frameworks/core/components_ng/svg/parse/svg_rect.cpp:29<br>frameworks/core/components_ng/svg/parse/svg_circle.cpp:30 |
| AC-2.3 | R-5 | TASK-040102-02 | 源码审查 + 定向 UT/预览用例 | frameworks/core/components_ng/svg/svg_dom.cpp:348<br>frameworks/core/components_ng/svg/parse/svg_rect.cpp:29<br>frameworks/core/components_ng/svg/parse/svg_circle.cpp:30 |

## 规则定义

> 类型标签：行为、边界、异常、恢复。

| 规则ID | 类型 | 触发条件 | 预期行为 | 边界/约束 | 关联AC |
|---|---|---|---|---|---|
| R-1 | 行为 | layout 非空 | 裁剪、计算 SVG 内容尺寸并应用 ImageFit | 布局尺寸作为最终裁剪边界 | AC-1.1 |
| R-2 | 边界 | SVG2 根 viewBox 无有效尺寸 | 回退 SvgContext viewport | 宽或高 <= 0 触发 | AC-1.2 |
| R-3 | 行为 | 基础图形标签已注册 | 按各 Svg*::AsPath 生成路径并绘制 | 属性按 SvgLengthScaleRule 归一化 | AC-2.1 |
| R-4 | 行为 | 走 compatible SVG text 管线 | RosenRenderSvgText/RosenSvgPainter 绘制文本 | 该能力不等同于 NG SvgDom text 支持 | AC-2.2 |
| R-5 | 边界 | NG SvgDom 遇到 text | 不创建节点 | 当前 NG TAG_FACTORIES 无 text | AC-2.3 |

## 验证映射

| 编号 | 对应规格项 | 验证方式 | 验证重点 |
|---|---|---|---|
| VM-1 | AC-1.1 ~ AC-1.2 | 定向 UT/预览用例 + 源码审查 | 适配布局坐标 |
| VM-2 | AC-2.1 ~ AC-2.3 | 定向 UT/预览用例 + 源码审查 | 绘制图形与文本 |

## API 变更分析

### 新增 API

> 本次不新增 API；下表记录本特性的现有开放面。

| API 名称 | 开放范围 | 入参概要 | 返回值 | 错误码范围 | 功能描述 | 关联 AC |
|---|---|---|---|---|---|---|
| Image.objectFit()/公共布局尺寸 | Public | ImageFit 与组件尺寸 | ImageAttribute | N/A | 影响 SVG 适配区域 | AC-1.1 |

### 变更/废弃 API

| API 名称 | 变更类型 | 影响场景 | 迁移指引 | 关联 AC |
|---|---|---|---|---|
| N/A | 无 | 无公开 API 变更 | N/A | AC-1.1 |

## 接口规格

### 接口定义

**SVG 绘制（内部）**

| 属性 | 值 |
|---|---|
| 函数签名 | `void SvgDom::DrawImage(RSCanvas&, ImageFit, Size)` |
| 返回值 | void |
| 开放范围 | InnerApi |
| 错误码 | N/A |
| 关联 AC | AC-1.1 ~ AC-2.3 |

**参数约束**

| 参数 | 类型 | 必填 | 默认值 | 约束条件 |
|---|---|---|---|---|
| canvas | RSCanvas& | 是 | 无 | 有效绘制上下文 |
| imageFit | ImageFit | 是 | 组件配置 | 按现有枚举 |
| layout | Size | 是 | 缓存布局 | 非空时更新布局 |

**行为场景**

| # | 触发条件 | 预期行为 | 关联 AC |
|---|---|---|---|
| 1 | 有效布局 | 裁剪并绘制 | AC-1.1 |
| 2 | SVG2 无有效 viewBox | 回退 viewport | AC-1.2 |
| 3 | NG text 标签 | 忽略 | AC-2.3 |

## 兼容性声明

- **已有 API 行为变更:** 否；明确 NG 与 compatible 文本路径差异
- **配置文件格式变更:** 否
- **数据存储格式变更:** 否
- **最低支持版本:** 随 SVG 既有支持版本
- **API 版本号策略:** 内部实现无独立 @since

## 架构约束

| 关键约束 | 约束说明 | 影响 AC |
|---|---|---|
| 双实现边界 | NG SvgDom 负责当前图像加载路径；compatible 管线保留文本绘制 | AC-2.2, AC-2.3 |
| 坐标归一化 | SvgLengthScaleRule 和 SvgFitConvertor 统一比例换算 | AC-1.1, AC-2.1 |

> 架构规则适用性及调用链见 design.md。

## 非功能性需求

| 类型 | 指标/阈值 | 验证方式 | 证据 |
|---|---|---|---|
| 性能 | 无新增指标；路径复用 RSRecordingPath | 源码审查 | svg_*::AsPath |
| 功耗 | 仅绘制期执行 | 源码审查 | DrawImage |
| 内存 | 无新增缓存格式 | 源码审查 | SvgContext |
| 安全 | N/A | N/A | 无权限 |
| 可靠性 | 无效 viewBox 有回退 | 边界用例 | svg_dom.cpp:369 |
| 可测试性 | 各标签可独立构造 SVG | UT/previewer | SVG 资源用例 |
| 自动化维测 | 沿用 SVG dump | Dump | SvgContext |
| 定界定位 | 绘制缺少 root/context 时日志返回 | 日志检查 | svg_dom.cpp:351 |

## 多设备适配声明

| 设备类型 | 行为差异 | 规格/约束 | 验证方式 | 证据 |
|---|---|---|---|---|
| 手机 | 由布局尺寸和密度换算决定，无额外设备分支 | 沿用现有能力 | 预览/真机 | 对应实现路径 |
| 平板 | 由布局尺寸和密度换算决定，无额外设备分支 | 沿用现有能力 | 预览/真机 | 对应实现路径 |
| 折叠屏 | 由布局尺寸和密度换算决定，无额外设备分支 | 涉及 hover 时按 SDK 配置 | 折叠屏验证 | SDK options 定义 |

## 全局特性影响

| 特性 | 适用？ | 结论 | 关联场景 |
|---|---|---|---|
| 无障碍 | 是 | 沿用组件/图像现有无障碍语义 | 主路径 |
| 大字体 | 是 | 文本和弹窗样式沿用系统字体缩放；固定按钮高度以 SDK 声明为准 | 样式验证 |
| 深色模式 | 是 | ResourceColor/主题资源随主题切换 | 主题验证 |
| 多窗口/分屏 | 是 | 布局受当前窗口约束 | 窗口尺寸变化 |
| 多用户 | 否 | 无用户态持久化 | N/A |
| 版本升级 | 是 | compatible/NG 管线差异保持现状 | 兼容性矩阵 |
| 生态兼容 | 是 | Dynamic/Static 声明按各自 API 版本保持一致 | 双前端审查 |

## 行为场景（可选，Gherkin）

```gherkin
Feature: SVG 坐标缩放、基础图形与文本绘制
  Scenario: 主路径
    Given 当前运行环境满足对应 API、资源和平台前置条件
    When 布局尺寸有效
    Then 先裁剪到布局矩形，再按 ImageFit 计算内容尺寸和缩放
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
    query: "SvgLengthScaleRule 和 ImageFit"
  - repo: "openharmony/ace_engine"
    query: "SVG 基础图形与 compatible 文本绘制"
```

**关键文档:**
- `interface/sdk-js/api/@internal/component/ets/image.d.ts`
- `interface/sdk-js/api/arkui/component/image.static.d.ets`
- `frameworks/core/components_ng/svg/svg_dom.cpp:348`
- `frameworks/core/components_ng/svg/parse/svg_rect.cpp:29`
- `frameworks/core/components_ng/svg/parse/svg_circle.cpp:30`
