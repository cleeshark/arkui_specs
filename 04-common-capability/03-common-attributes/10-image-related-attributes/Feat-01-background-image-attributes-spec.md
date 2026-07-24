# 特性规格

## 概述

| 字段 | 内容 |
|---|---|
| 特性名称 | 背景图片通用属性 |
| 特性编号 | Func-04-03-10-Feat-01 |
| FuncID | 04-03-10 |
| 所属 Epic | 无 |
| 优先级 | P0 |
| 目标版本 | Dynamic API 7+ / Static API 23+ / Node C API |
| SIG 归属 | ArkUI SIG |
| 状态 | Baselined |
| 复杂度 | 复杂 |
| lineage | new-on-legacy（已有实现规格补录） |

## 本次变更范围（Delta）

> 本文档补录现有实现，不修改产品行为。

| 类型 | 内容 | 说明 |
|---|---|---|
| ADDED | backgroundImage/repeat/size/position/resizable | 存量能力补录 |
| MODIFIED | PixelMap 和 options 重载 | Dynamic API 12/18；Static API 23 |

## 输入文档

- **设计文档**: `04-common-capability/03-common-attributes/10-image-related-attributes/design.md`
- **SDK 类型定义**:
  - `interface/sdk-js/api/@internal/component/ets/common.d.ts`
  - `interface/sdk-js/api/arkui/component/common.static.d.ets`
  - `interfaces/native/native_node.h`
- **实现证据**:
  - `frameworks/core/components_ng/base/view_abstract.cpp:838`
  - `frameworks/core/components_ng/base/view_abstract.cpp:853`
  - `frameworks/core/components_ng/base/view_abstract.cpp:993`
  - `frameworks/core/components_ng/base/view_abstract.cpp:1060`
  - `frameworks/core/components_ng/base/view_abstract.cpp:11355`
  - `interfaces/native/node/style_modifier.cpp:1088`

> 需求基线、不涉及项、受影响子系统与仓库详见 proposal.md；本特性为存量能力补录，无独立 proposal.md。

## 用户故事

### US-1: 设置背景图

**角色**: 应用开发者  
**期望**: 为任意通用组件设置资源或 PixelMap 背景图及重复方式  
**价值**: 复用图像作为组件背景

| AC编号 | 验收标准 | 类型 |
|---|---|---|
| AC-1.1 | WHEN backgroundImage 接收有效 ResourceStr 或 PixelMap THEN RenderContext 保存 BackgroundImage 并应用 repeat | 正常 |
| AC-1.2 | WHEN当前不是 visual-state 处理阶段或 Pipeline 禁止更新背景图 THEN设置无操作返回 | 边界 |
| AC-1.3 | WHEN资源对象发生配置变更 THEN重新解析媒体资源并更新 RenderContext | 恢复 |

### US-2: 控制尺寸位置和九宫格

**角色**: 应用开发者  
**期望**: 设置 backgroundImageSize、backgroundImagePosition 和 backgroundImageResizable  
**价值**: 覆盖 Dynamic、Static 和 Node C API

| AC编号 | 验收标准 | 类型 |
|---|---|---|
| AC-2.1 | WHEN设置 SizeOptions/ImageSize THEN按长度、百分比或 Cover/Contain 更新背景图尺寸 | 正常 |
| AC-2.2 | WHEN设置 Position/Alignment THEN更新背景图位置并在资源变更时重载 | 正常 |
| AC-2.3 | WHEN设置 ResizableOptions.slice THEN保存四边 slice 并支持资源重载 | 正常 |
| AC-2.4 | WHEN Node C API 参数数量或类型不合法 THEN返回 ERROR_CODE_PARAM_INVALID | 异常 |

## 验收追溯

| AC | 关联规则 | 关联 Task | 验证方式 | 证据 |
|---|---|---|---|---|
| AC-1.1 | R-1 | TASK-040310-01 | 源码审查 + 定向 UT/预览用例 | frameworks/core/components_ng/base/view_abstract.cpp:838<br>frameworks/core/components_ng/base/view_abstract.cpp:853<br>frameworks/core/components_ng/base/view_abstract.cpp:993 |
| AC-1.2 | R-2 | TASK-040310-01 | 源码审查 + 定向 UT/预览用例 | frameworks/core/components_ng/base/view_abstract.cpp:838<br>frameworks/core/components_ng/base/view_abstract.cpp:853<br>frameworks/core/components_ng/base/view_abstract.cpp:993 |
| AC-1.3 | R-3 | TASK-040310-01 | 源码审查 + 定向 UT/预览用例 | frameworks/core/components_ng/base/view_abstract.cpp:838<br>frameworks/core/components_ng/base/view_abstract.cpp:853<br>frameworks/core/components_ng/base/view_abstract.cpp:993 |
| AC-2.1 | R-4 | TASK-040310-01 | 源码审查 + 定向 UT/预览用例 | frameworks/core/components_ng/base/view_abstract.cpp:838<br>frameworks/core/components_ng/base/view_abstract.cpp:853<br>frameworks/core/components_ng/base/view_abstract.cpp:993 |
| AC-2.2 | R-4 | TASK-040310-01 | 源码审查 + 定向 UT/预览用例 | frameworks/core/components_ng/base/view_abstract.cpp:838<br>frameworks/core/components_ng/base/view_abstract.cpp:853<br>frameworks/core/components_ng/base/view_abstract.cpp:993 |
| AC-2.3 | R-4 | TASK-040310-01 | 源码审查 + 定向 UT/预览用例 | frameworks/core/components_ng/base/view_abstract.cpp:838<br>frameworks/core/components_ng/base/view_abstract.cpp:853<br>frameworks/core/components_ng/base/view_abstract.cpp:993 |
| AC-2.4 | R-5 | TASK-040310-01 | 源码审查 + 定向 UT/预览用例 | frameworks/core/components_ng/base/view_abstract.cpp:838<br>frameworks/core/components_ng/base/view_abstract.cpp:853<br>frameworks/core/components_ng/base/view_abstract.cpp:993 |

## 规则定义

> 类型标签：行为、边界、异常、恢复。

| 规则ID | 类型 | 触发条件 | 预期行为 | 边界/约束 | 关联AC |
|---|---|---|---|---|---|
| R-1 | 行为 | 有效 src 且处于 visual-state | 更新 RenderContext BackgroundImage/Repeat | Dynamic repeat 默认 NoRepeat | AC-1.1 |
| R-2 | 边界 | 非 visual-state 或 Pipeline 禁止背景图更新 | 直接返回 | 不修改旧属性 | AC-1.2 |
| R-3 | 恢复 | ResourceObject 配置变化 | 重新解析资源并触发 OnBackgroundImageUpdate | Pipeline 禁止时仍不更新 | AC-1.3 |
| R-4 | 行为 | 尺寸、位置或 slice 合法 | 更新对应 RenderContext 属性 | 百分比乘 FULL_DIMENSION；slice 四边分别存储 | AC-2.1, AC-2.2, AC-2.3 |
| R-5 | 异常 | Node C API 参数无效 | 返回 ERROR_CODE_PARAM_INVALID | 不调用 modifier | AC-2.4 |

## 验证映射

| 编号 | 对应规格项 | 验证方式 | 验证重点 |
|---|---|---|---|
| VM-1 | AC-1.1 ~ AC-1.3 | 定向 UT/预览用例 + 源码审查 | 设置背景图 |
| VM-2 | AC-2.1 ~ AC-2.4 | 定向 UT/预览用例 + 源码审查 | 控制尺寸位置和九宫格 |

## API 变更分析

### 新增 API

> 本次不新增 API；下表记录本特性的现有开放面。

| API 名称 | 开放范围 | 入参概要 | 返回值 | 错误码范围 | 功能描述 | 关联 AC |
|---|---|---|---|---|---|---|
| backgroundImage | Public | ResourceStr | PixelMap；repeat/options | T/this | N/A | 设置背景图 | AC-1.1 |
| backgroundImageSize | Public | SizeOptions | ImageSize | T/this | N/A | 设置尺寸 | AC-2.1 |
| backgroundImagePosition | Public | Position | Alignment | T/this | N/A | 设置位置 | AC-2.2 |
| backgroundImageResizable | Public | ResizableOptions | T/this | N/A | 设置 slice | AC-2.3 |
| NODE_BACKGROUND_IMAGE* | Public C API | ArkUI_AttributeItem | int32_t/attribute | NO_ERROR/PARAM_INVALID | 节点属性设置/重置/获取 | AC-1.1, AC-2.4 |

### 变更/废弃 API

| API 名称 | 变更类型 | 影响场景 | 迁移指引 | 关联 AC |
|---|---|---|---|---|
| backgroundImage | 变更（重载扩展） | Dynamic API 12 支持 PixelMap，API 18 增加 options | 使用对应重载 | AC-1.1 |
| NODE_BACKGROUND_IMAGE_POSITION | 变更（新增节点属性） | Node C API | API 21+ 使用 | AC-2.2 |

## 接口规格

### 接口定义

**CommonMethod.backgroundImage**

| 属性 | 值 |
|---|---|
| 函数签名 | `backgroundImage(src: ResourceStr | PixelMap, repeat?: ImageRepeat): T; backgroundImage(src, options?: BackgroundImageOptions): T` |
| 返回值 | 当前组件 |
| 开放范围 | Public |
| 错误码 | N/A |
| 关联 AC | AC-1.1 ~ AC-1.3 |

**参数约束**

| 参数 | 类型 | 必填 | 默认值 | 约束条件 |
|---|---|---|---|---|
| src | ResourceStr | PixelMap | 是 | 无 | Static 允许 undefined 重置 |
| repeat/options | ImageRepeat | BackgroundImageOptions | 否 | NoRepeat | options 重载自 API 18 dynamic |

**行为场景**

| # | 触发条件 | 预期行为 | 关联 AC |
|---|---|---|---|
| 1 | 有效资源 | 设置背景图 | AC-1.1 |
| 2 | Pipeline 禁止更新 | 无操作 | AC-1.2 |
| 3 | 资源重载 | 重新解析并更新 | AC-1.3 |

**背景图尺寸/位置/切片**

| 属性 | 值 |
|---|---|
| 函数签名 | `backgroundImageSize(value); backgroundImagePosition(value); backgroundImageResizable(value)` |
| 返回值 | 当前组件 |
| 开放范围 | Public |
| 错误码 | N/A |
| 关联 AC | AC-2.1 ~ AC-2.3 |

**参数约束**

| 参数 | 类型 | 必填 | 默认值 | 约束条件 |
|---|---|---|---|---|
| value | SizeOptions | ImageSize | Position | Alignment | ResizableOptions | 是 | 各 API 默认值 | 按 SDK 类型约束 |

**行为场景**

| # | 触发条件 | 预期行为 | 关联 AC |
|---|---|---|---|
| 1 | 长度/百分比尺寸 | 更新尺寸 | AC-2.1 |
| 2 | 位置或对齐 | 更新位置 | AC-2.2 |
| 3 | slice | 更新九宫格 | AC-2.3 |

**Node C API**

| 属性 | 值 |
|---|---|
| 函数签名 | `ArkUI_NativeNodeAPI_1::setAttribute(node, NODE_BACKGROUND_IMAGE*, item)` |
| 返回值 | ArkUI_ErrorCode |
| 开放范围 | Public C API |
| 错误码 | ERROR_CODE_NO_ERROR / ERROR_CODE_PARAM_INVALID |
| 关联 AC | AC-2.4 |

**参数约束**

| 参数 | 类型 | 必填 | 默认值 | 约束条件 |
|---|---|---|---|---|
| item | ArkUI_AttributeItem | 是 | 无 | 格式见 native_node.h |

**行为场景**

| # | 触发条件 | 预期行为 | 关联 AC |
|---|---|---|---|
| 1 | 参数合法 | 调用 common modifier | AC-1.1 |
| 2 | 数量/类型非法 | PARAM_INVALID | AC-2.4 |

## 兼容性声明

- **已有 API 行为变更:** 是；Dynamic/Static 入参可空性和 @since 不同
- **配置文件格式变更:** 否
- **数据存储格式变更:** 否
- **最低支持版本:** backgroundImage/size/position API 7；resizable API 12；Static API 23
- **API 版本号策略:** 按 SDK @since；Node position API 21、slice API 19

## 架构约束

| 关键约束 | 约束说明 | 影响 AC |
|---|---|---|
| RenderContext 属性 | 背景图不是独立子组件，全部保存在 RenderContext | AC-1.1, AC-2.1 |
| 资源重载 | Pattern ResourceObject 回调重建属性 | AC-1.3, AC-2.2 |
| Pipeline 门控 | CheckNeedDisableUpdateBackgroundImage 可阻止初次和资源更新 | AC-1.2 |

> 架构规则适用性及调用链见 design.md。

## 非功能性需求

| 类型 | 指标/阈值 | 验证方式 | 证据 |
|---|---|---|---|
| 性能 | 无新增指标；沿用 RenderContext 图像绘制 | 源码审查 | view_abstract.cpp |
| 功耗 | 无后台任务 | 源码审查 | 属性更新路径 |
| 内存 | 资源回调使用 WeakClaim | 源码审查 | view_abstract.cpp:868 |
| 安全 | 资源 URI 按现有 ImageSourceInfo 处理 | 既有测试 | 图像加载链 |
| 可靠性 | 资源变更可重载 | 配置变更用例 | ReloadResources |
| 可测试性 | Dynamic/Static/Node C API 可独立验证 | previewer/C API UT | style_modifier.cpp |
| 自动化维测 | RenderContext dump 沿用 | Dump | RenderContext |
| 定界定位 | C API 返回参数错误 | C API UT | style_modifier.cpp |

## 多设备适配声明

| 设备类型 | 行为差异 | 规格/约束 | 验证方式 | 证据 |
|---|---|---|---|---|
| 手机 | 尺寸和位置按当前组件区域换算 | 沿用现有能力 | 预览/真机 | 对应实现路径 |
| 平板 | 尺寸和位置按当前组件区域换算 | 沿用现有能力 | 预览/真机 | 对应实现路径 |
| 折叠屏 | 尺寸和位置按当前组件区域换算 | 涉及 hover 时按 SDK 配置 | 折叠屏验证 | SDK options 定义 |

## 全局特性影响

| 特性 | 适用？ | 结论 | 关联场景 |
|---|---|---|---|
| 无障碍 | 是 | 沿用组件/图像现有无障碍语义 | 主路径 |
| 大字体 | 是 | 文本和弹窗样式沿用系统字体缩放；固定按钮高度以 SDK 声明为准 | 样式验证 |
| 深色模式 | 是 | ResourceColor/主题资源随主题切换 | 主题验证 |
| 多窗口/分屏 | 是 | 布局受当前窗口约束 | 窗口尺寸变化 |
| 多用户 | 否 | 无用户态持久化 | N/A |
| 版本升级 | 是 | Dynamic API 7-18、Static 23、Node C API 19/21 存在版本差异 | 兼容性矩阵 |
| 生态兼容 | 是 | Dynamic/Static 声明按各自 API 版本保持一致 | 双前端审查 |

## 行为场景（可选，Gherkin）

```gherkin
Feature: 背景图片通用属性
  Scenario: 主路径
    Given 当前运行环境满足对应 API、资源和平台前置条件
    When backgroundImage 接收有效 ResourceStr 或 PixelMap
    Then RenderContext 保存 BackgroundImage 并应用 repeat
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
    query: "ViewAbstract background image resource reload"
  - repo: "openharmony/ace_engine"
    query: "NODE_BACKGROUND_IMAGE style modifier"
```

**关键文档:**
- `interface/sdk-js/api/@internal/component/ets/common.d.ts`
- `interface/sdk-js/api/arkui/component/common.static.d.ets`
- `interfaces/native/native_node.h`
- `frameworks/core/components_ng/base/view_abstract.cpp:838`
- `frameworks/core/components_ng/base/view_abstract.cpp:853`
- `frameworks/core/components_ng/base/view_abstract.cpp:993`
