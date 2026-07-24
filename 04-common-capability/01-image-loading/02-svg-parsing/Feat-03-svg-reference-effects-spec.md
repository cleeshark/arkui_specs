# 特性规格

## 概述

| 字段 | 内容 |
|---|---|
| 特性名称 | SVG 引用、渐变、裁剪、遮罩与滤镜效果 |
| 特性编号 | Func-04-01-02-Feat-03 |
| FuncID | 04-01-02 |
| 所属 Epic | 无 |
| 优先级 | P0 |
| 目标版本 | 现有 SVG 实现（目标 API 12+ 含滤镜） |
| SIG 归属 | ArkUI SIG |
| 状态 | Baselined |
| 复杂度 | 关键 |
| lineage | new-on-legacy（已有实现规格补录） |

## 本次变更范围（Delta）

> 本文档补录现有实现，不修改产品行为。

| 类型 | 内容 | 说明 |
|---|---|---|
| ADDED | ID 引用和 use/pattern | 存量能力补录 |
| ADDED | 渐变/clip/mask/filter | 存量能力补录 |

## 输入文档

- **设计文档**: `04-common-capability/01-image-loading/02-svg-parsing/design.md`
- **SDK 类型定义**:
  - `interface/sdk-js/api/@internal/component/ets/image.d.ts`
  - `interface/sdk-js/api/arkui/component/image.static.d.ets`
- **实现证据**:
  - `frameworks/core/components_ng/svg/svg_dom.cpp:91`
  - `frameworks/core/components_ng/svg/parse/svg_node.cpp:574`
  - `frameworks/core/components_ng/svg/parse/svg_node.cpp:600`
  - `frameworks/core/components_ng/svg/parse/svg_node.cpp:631`
  - `frameworks/core/components_ng/svg/parse/svg_use.cpp:28`

> 需求基线、不涉及项、受影响子系统与仓库详见 proposal.md；本特性为存量能力补录，无独立 proposal.md。

## 用户故事

### US-1: 解析引用和渐变

**角色**: 应用开发者  
**期望**: 通过 id/href、渐变和 pattern 复用绘制定义  
**价值**: 表达复合 SVG 资源

| AC编号 | 验收标准 | 类型 |
|---|---|---|
| AC-1.1 | WHEN id 已写入 SvgContext 且 href 引用该 id THEN use/clip/mask/filter 能获取对应节点 | 正常 |
| AC-1.2 | WHEN启用 SVG2 THEN linearGradient/radialGradient 使用 SVG2 专用节点实现 | 边界 |

### US-2: 应用视觉效果

**角色**: 应用开发者  
**期望**: 应用裁剪、遮罩和滤镜  
**价值**: 保持版本兼容和无崩溃降级

| AC编号 | 验收标准 | 类型 |
|---|---|---|
| AC-2.1 | WHEN clip-path 引用有效 SvgClipPath THEN 将引用路径与画布求交 | 正常 |
| AC-2.2 | WHEN mask 引用有效节点 THEN 按现有 mask 合成路径绘制 | 正常 |
| AC-2.3 | WHEN legacy 绘制路径的目标 API 小于 12 THEN OnFilter 直接返回且不应用滤镜 | 边界 |
| AC-2.4 | WHEN引用 id 不存在 THEN 对应效果无操作返回 | 异常 |

## 验收追溯

| AC | 关联规则 | 关联 Task | 验证方式 | 证据 |
|---|---|---|---|---|
| AC-1.1 | R-1 | TASK-040102-03 | 源码审查 + 定向 UT/预览用例 | frameworks/core/components_ng/svg/svg_dom.cpp:91<br>frameworks/core/components_ng/svg/parse/svg_node.cpp:574<br>frameworks/core/components_ng/svg/parse/svg_node.cpp:600 |
| AC-1.2 | R-2 | TASK-040102-03 | 源码审查 + 定向 UT/预览用例 | frameworks/core/components_ng/svg/svg_dom.cpp:91<br>frameworks/core/components_ng/svg/parse/svg_node.cpp:574<br>frameworks/core/components_ng/svg/parse/svg_node.cpp:600 |
| AC-2.1 | R-3 | TASK-040102-03 | 源码审查 + 定向 UT/预览用例 | frameworks/core/components_ng/svg/svg_dom.cpp:91<br>frameworks/core/components_ng/svg/parse/svg_node.cpp:574<br>frameworks/core/components_ng/svg/parse/svg_node.cpp:600 |
| AC-2.2 | R-4 | TASK-040102-03 | 源码审查 + 定向 UT/预览用例 | frameworks/core/components_ng/svg/svg_dom.cpp:91<br>frameworks/core/components_ng/svg/parse/svg_node.cpp:574<br>frameworks/core/components_ng/svg/parse/svg_node.cpp:600 |
| AC-2.3 | R-5 | TASK-040102-03 | 源码审查 + 定向 UT/预览用例 | frameworks/core/components_ng/svg/svg_dom.cpp:91<br>frameworks/core/components_ng/svg/parse/svg_node.cpp:574<br>frameworks/core/components_ng/svg/parse/svg_node.cpp:600 |
| AC-2.4 | R-6 | TASK-040102-03 | 源码审查 + 定向 UT/预览用例 | frameworks/core/components_ng/svg/svg_dom.cpp:91<br>frameworks/core/components_ng/svg/parse/svg_node.cpp:574<br>frameworks/core/components_ng/svg/parse/svg_node.cpp:600 |

## 规则定义

> 类型标签：行为、边界、异常、恢复。

| 规则ID | 类型 | 触发条件 | 预期行为 | 边界/约束 | 关联AC |
|---|---|---|---|---|---|
| R-1 | 行为 | href 指向已注册 ID | SvgContext 返回引用节点 | ID 必须在解析阶段注册 | AC-1.1 |
| R-2 | 边界 | src.IsSupportSvg2 为 true | 优先使用 TAG_FACTORIES_SVG2 渐变节点 | 仅覆盖 linear/radialGradient | AC-1.2 |
| R-3 | 行为 | clip-path 引用有效 | ClipPath 与画布 INTERSECT | 空路径记录警告并返回 | AC-2.1 |
| R-4 | 行为 | mask 引用有效 | 执行遮罩绘制 | 无引用节点则无操作 | AC-2.2 |
| R-5 | 边界 | legacy OnFilter 且 target API < 12 | 直接返回 | API 12 为启用边界 | AC-2.3 |
| R-6 | 异常 | 引用 ID 不存在或类型不匹配 | CHECK_NULL/类型校验后无操作返回 | 不抛公开错误 | AC-2.4 |

## 验证映射

| 编号 | 对应规格项 | 验证方式 | 验证重点 |
|---|---|---|---|
| VM-1 | AC-1.1 ~ AC-1.2 | 定向 UT/预览用例 + 源码审查 | 解析引用和渐变 |
| VM-2 | AC-2.1 ~ AC-2.4 | 定向 UT/预览用例 + 源码审查 | 应用视觉效果 |

## API 变更分析

### 新增 API

> 本次不新增 API；下表记录本特性的现有开放面。

| API 名称 | 开放范围 | 入参概要 | 返回值 | 错误码范围 | 功能描述 | 关联 AC |
|---|---|---|---|---|---|---|
| Image(src) | Public | 包含引用和效果的 SVG 资源 | ImageAttribute | N/A | 通过图像加载链路渲染效果 | AC-1.1 |

### 变更/废弃 API

| API 名称 | 变更类型 | 影响场景 | 迁移指引 | 关联 AC |
|---|---|---|---|---|
| N/A | 无 | 无公开 API 变更 | N/A | AC-1.1 |

## 接口规格

### 接口定义

**SVG 效果应用（内部）**

| 属性 | 值 |
|---|---|
| 函数签名 | `SvgNode::OnClipPath/OnMask/OnFilter(RSCanvas&, context)` |
| 返回值 | void |
| 开放范围 | InnerApi |
| 错误码 | N/A |
| 关联 AC | AC-2.1 ~ AC-2.4 |

**参数约束**

| 参数 | 类型 | 必填 | 默认值 | 约束条件 |
|---|---|---|---|---|
| canvas | RSCanvas& | 是 | 无 | 有效画布 |
| context | Size 或 SvgCoordinateSystemContext | 是 | 无 | 由 legacy/SVG2 路径选择 |

**行为场景**

| # | 触发条件 | 预期行为 | 关联 AC |
|---|---|---|---|
| 1 | 有效引用 | 应用效果 | AC-2.1 |
| 2 | 目标 API 11 的 legacy filter | 不应用滤镜 | AC-2.3 |
| 3 | 引用缺失 | 无操作 | AC-2.4 |

## 兼容性声明

- **已有 API 行为变更:** 是；SVG2 切换渐变实现，legacy filter 仅 target API >= 12 生效
- **配置文件格式变更:** 否
- **数据存储格式变更:** 否
- **最低支持版本:** 滤镜边界为目标 API 12
- **API 版本号策略:** 由 target API 和 ImageSourceInfo SVG2 标志选择

## 架构约束

| 关键约束 | 约束说明 | 影响 AC |
|---|---|---|
| 引用集中解析 | 所有效果通过 SvgContext ID 映射获取定义节点 | AC-1.1, AC-2.4 |
| 版本门控 | legacy filter 在 SvgNode 层检查 target API 12 | AC-2.3 |
| SVG2 实现切换 | 渐变工厂和完整绘制上下文随 SVG2 开关切换 | AC-1.2 |

> 架构规则适用性及调用链见 design.md。

## 非功能性需求

| 类型 | 指标/阈值 | 验证方式 | 证据 |
|---|---|---|---|
| 性能 | 效果仅在引用有效时执行 | 源码审查 | CHECK_NULL 路径 |
| 功耗 | 无后台任务 | 源码审查 | 绘制期执行 |
| 内存 | 引用使用 WeakPtr/RefPtr | 源码审查 | SvgContext |
| 安全 | N/A | N/A | 无权限 |
| 可靠性 | 缺失引用无操作 | 异常 SVG 用例 | svg_node.cpp |
| 可测试性 | 按 effect 标签构造资源 | UT/previewer | SVG 用例 |
| 自动化维测 | 日志和 dump 沿用 | Dump | SvgDom |
| 定界定位 | 空 clip path 输出日志 | 日志检查 | svg_node.cpp:582 |

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
| 版本升级 | 是 | 目标 API 12 和 SVG2 是关键兼容维度 | 兼容性矩阵 |
| 生态兼容 | 是 | Dynamic/Static 声明按各自 API 版本保持一致 | 双前端审查 |

## 行为场景（可选，Gherkin）

```gherkin
Feature: SVG 引用、渐变、裁剪、遮罩与滤镜效果
  Scenario: 主路径
    Given 当前运行环境满足对应 API、资源和平台前置条件
    When id 已写入 SvgContext 且 href 引用该 id
    Then use/clip/mask/filter 能获取对应节点
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
    query: "SVG use gradient clip mask filter"
  - repo: "openharmony/ace_engine"
    query: "SVG legacy filter target API 12"
```

**关键文档:**
- `interface/sdk-js/api/@internal/component/ets/image.d.ts`
- `interface/sdk-js/api/arkui/component/image.static.d.ets`
- `frameworks/core/components_ng/svg/svg_dom.cpp:91`
- `frameworks/core/components_ng/svg/parse/svg_node.cpp:574`
- `frameworks/core/components_ng/svg/parse/svg_node.cpp:600`
