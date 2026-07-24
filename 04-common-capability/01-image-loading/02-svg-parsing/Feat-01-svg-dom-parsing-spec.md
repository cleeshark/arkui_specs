# 特性规格

## 概述

| 字段 | 内容 |
|---|---|
| 特性名称 | SVG DOM、标签、属性与样式解析 |
| 特性编号 | Func-04-01-02-Feat-01 |
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
| ADDED | SVG XML 到节点树的解析规则 | 存量能力补录 |
| ADDED | id/class/style/fill 属性处理 | 存量能力补录 |

## 输入文档

- **设计文档**: `04-common-capability/01-image-loading/02-svg-parsing/design.md`
- **SDK 类型定义**:
  - `interface/sdk-js/api/@internal/component/ets/image.d.ts`
  - `interface/sdk-js/api/arkui/component/image.static.d.ets`
- **实现证据**:
  - `frameworks/core/components_ng/svg/svg_dom.cpp:58`
  - `frameworks/core/components_ng/svg/svg_dom.cpp:128`
  - `frameworks/core/components_ng/svg/svg_dom.cpp:184`
  - `frameworks/core/components_ng/svg/svg_dom.cpp:206`

> 需求基线、不涉及项、受影响子系统与仓库详见 proposal.md；本特性为存量能力补录，无独立 proposal.md。

## 用户故事

### US-1: 解析 SVG 节点树

**角色**: 图像框架开发者  
**期望**: 将合法 SVG XML 转换为可绘制节点树  
**价值**: 为后续绘制提供确定的 DOM

| AC编号 | 验收标准 | 类型 |
|---|---|---|
| AC-1.1 | WHEN 输入包含已注册标签的合法 SVG THEN 按 TAG_FACTORIES 创建对应 SvgNode 并保持父子顺序 | 正常 |
| AC-1.2 | WHEN XML 构建失败或根节点不是 svg THEN CreateSvgDom 返回空对象 | 异常 |
| AC-1.3 | WHEN 遇到未注册标签 THEN 该标签不创建 SvgNode，解析流程不伪造节点 | 边界 |

### US-2: 解析样式和引用键

**角色**: 图像框架开发者  
**期望**: 解析 id、class、style 和 fill  
**价值**: 支持引用、继承和绘制样式

| AC编号 | 验收标准 | 类型 |
|---|---|---|
| AC-2.1 | WHEN 节点包含 id THEN 将节点写入 SvgContext 的 ID 映射 | 正常 |
| AC-2.2 | WHEN 节点包含 class 或内联 style THEN 将已解析属性写入节点 | 正常 |
| AC-2.3 | WHEN属性值为空 THEN SetAttrValue 不更新节点属性 | 边界 |

## 验收追溯

| AC | 关联规则 | 关联 Task | 验证方式 | 证据 |
|---|---|---|---|---|
| AC-1.1 | R-1 | TASK-040102-01 | 源码审查 + 定向 UT/预览用例 | frameworks/core/components_ng/svg/svg_dom.cpp:58<br>frameworks/core/components_ng/svg/svg_dom.cpp:128<br>frameworks/core/components_ng/svg/svg_dom.cpp:184 |
| AC-1.2 | R-2 | TASK-040102-01 | 源码审查 + 定向 UT/预览用例 | frameworks/core/components_ng/svg/svg_dom.cpp:58<br>frameworks/core/components_ng/svg/svg_dom.cpp:128<br>frameworks/core/components_ng/svg/svg_dom.cpp:184 |
| AC-1.3 | R-3 | TASK-040102-01 | 源码审查 + 定向 UT/预览用例 | frameworks/core/components_ng/svg/svg_dom.cpp:58<br>frameworks/core/components_ng/svg/svg_dom.cpp:128<br>frameworks/core/components_ng/svg/svg_dom.cpp:184 |
| AC-2.1 | R-4 | TASK-040102-01 | 源码审查 + 定向 UT/预览用例 | frameworks/core/components_ng/svg/svg_dom.cpp:58<br>frameworks/core/components_ng/svg/svg_dom.cpp:128<br>frameworks/core/components_ng/svg/svg_dom.cpp:184 |
| AC-2.2 | R-4 | TASK-040102-01 | 源码审查 + 定向 UT/预览用例 | frameworks/core/components_ng/svg/svg_dom.cpp:58<br>frameworks/core/components_ng/svg/svg_dom.cpp:128<br>frameworks/core/components_ng/svg/svg_dom.cpp:184 |
| AC-2.3 | R-5 | TASK-040102-01 | 源码审查 + 定向 UT/预览用例 | frameworks/core/components_ng/svg/svg_dom.cpp:58<br>frameworks/core/components_ng/svg/svg_dom.cpp:128<br>frameworks/core/components_ng/svg/svg_dom.cpp:184 |

## 规则定义

> 类型标签：行为、边界、异常、恢复。

| 规则ID | 类型 | 触发条件 | 预期行为 | 边界/约束 | 关联AC |
|---|---|---|---|---|---|
| R-1 | 行为 | 合法 XML 且标签存在于 TAG_FACTORIES | 创建节点、设置 Context/ImagePath、解析属性并追加到父节点 | 标签集合以 svg_dom.cpp:58 为准 | AC-1.1 |
| R-2 | 异常 | SkDOM::build 失败或根节点转换失败 | ParseSvg 返回 false，CreateSvgDom 返回 nullptr | 不生成部分可用对象 | AC-1.2 |
| R-3 | 边界 | FindAndCreateNode 未命中 | 返回 nullptr，不创建未知节点 | 不推断未知标签语义 | AC-1.3 |
| R-4 | 行为 | id/class/style/fill 非空 | 按专用分支更新 ID 映射或节点属性 | class 仅应用 SvgContext 已收集样式 | AC-2.1, AC-2.2 |
| R-5 | 边界 | 属性值为空 | 直接返回 | 不覆盖现有属性 | AC-2.3 |

## 验证映射

| 编号 | 对应规格项 | 验证方式 | 验证重点 |
|---|---|---|---|
| VM-1 | AC-1.1 ~ AC-1.3 | 定向 UT/预览用例 + 源码审查 | 解析 SVG 节点树 |
| VM-2 | AC-2.1 ~ AC-2.3 | 定向 UT/预览用例 + 源码审查 | 解析样式和引用键 |

## API 变更分析

### 新增 API

> 本次不新增 API；下表记录本特性的现有开放面。

| API 名称 | 开放范围 | 入参概要 | 返回值 | 错误码范围 | 功能描述 | 关联 AC |
|---|---|---|---|---|---|---|
| Image(src) | Public | ResourceStr/PixelMap/DrawableDescriptor 等图像源 | ImageAttribute | N/A | SVG 通过 Image 加载链路进入解析 | AC-1.1 |

### 变更/废弃 API

| API 名称 | 变更类型 | 影响场景 | 迁移指引 | 关联 AC |
|---|---|---|---|---|
| N/A | 无 | 无公开 SVG 解析 API 变更 | 通过 Image API 使用 | AC-1.1 |

## 接口规格

### 接口定义

**SVG DOM 解析（内部）**

| 属性 | 值 |
|---|---|
| 函数签名 | `RefPtr<SvgDom> SvgDom::CreateSvgDom(SkStream&, const ImageSourceInfo&)` |
| 返回值 | RefPtr<SvgDom>，失败为 nullptr |
| 开放范围 | InnerApi |
| 错误码 | N/A |
| 关联 AC | AC-1.1 ~ AC-2.3 |

**参数约束**

| 参数 | 类型 | 必填 | 默认值 | 约束条件 |
|---|---|---|---|---|
| svgStream | SkStream& | 是 | 无 | 必须可由 SkDOM 构建 |
| src | ImageSourceInfo | 是 | 无 | 提供路径、fillColor、SVG2 开关 |

**行为场景**

| # | 触发条件 | 预期行为 | 关联 AC |
|---|---|---|---|
| 1 | 合法 SVG | 返回完整 SvgDom | AC-1.1 |
| 2 | 非法 XML | 返回 nullptr | AC-1.2 |
| 3 | 空属性 | 忽略该属性 | AC-2.3 |

## 兼容性声明

- **已有 API 行为变更:** 否；补录现有解析行为
- **配置文件格式变更:** 否
- **数据存储格式变更:** 否
- **最低支持版本:** 随 Image/SVG 既有支持版本
- **API 版本号策略:** SVG 解析为内部能力，无独立 @since

## 架构约束

| 关键约束 | 约束说明 | 影响 AC |
|---|---|---|
| DOM 工厂白名单 | 仅 TAG_FACTORIES/TAG_FACTORIES_SVG2 注册标签可实例化 | AC-1.1, AC-1.3 |
| 上下文集中管理 | ID 与 CSS 样式由 SvgContext 保存 | AC-2.1, AC-2.2 |

> 架构规则适用性及调用链见 design.md。

## 非功能性需求

| 类型 | 指标/阈值 | 验证方式 | 证据 |
|---|---|---|---|
| 性能 | 无新增指标；遍历使用显式栈 | 源码审查 | svg_dom.cpp:146 |
| 功耗 | 无后台任务 | 源码审查 | 同步解析路径 |
| 内存 | 节点由 RefPtr 管理 | 源码审查 | SvgNode 树 |
| 安全 | 不执行脚本，仅解析注册标签 | 恶意输入用例 | TAG_FACTORIES 白名单 |
| 可靠性 | 非法 XML 返回空对象 | 异常用例 | svg_dom.cpp:128 |
| 可测试性 | 标签和属性可通过 SVG 资源构造 | UT | test/unittest/core/pattern/image |
| 自动化维测 | 沿用 dump 信息 | Dump | svg_dom.cpp:331 |
| 定界定位 | 解析失败输出 ACE_IMAGE 日志 | 日志检查 | svg_dom.cpp:124 |

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
| 版本升级 | 是 | 无公开 API 迁移；SVG2 差异由 Feat-04 说明 | 兼容性矩阵 |
| 生态兼容 | 是 | Dynamic/Static 声明按各自 API 版本保持一致 | 双前端审查 |

## 行为场景（可选，Gherkin）

```gherkin
Feature: SVG DOM、标签、属性与样式解析
  Scenario: 主路径
    Given 当前运行环境满足对应 API、资源和平台前置条件
    When 输入包含已注册标签的合法 SVG
    Then 按 TAG_FACTORIES 创建对应 SvgNode 并保持父子顺序
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
    query: "SvgDom 标签工厂和属性解析"
  - repo: "openharmony/ace_engine"
    query: "SvgContext ID 与 CSS 样式映射"
```

**关键文档:**
- `interface/sdk-js/api/@internal/component/ets/image.d.ts`
- `interface/sdk-js/api/arkui/component/image.static.d.ets`
- `frameworks/core/components_ng/svg/svg_dom.cpp:58`
- `frameworks/core/components_ng/svg/svg_dom.cpp:128`
- `frameworks/core/components_ng/svg/svg_dom.cpp:184`
