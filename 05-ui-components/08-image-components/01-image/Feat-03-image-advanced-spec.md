# 特性规格

> Func-05-08-01-Feat-03 高级功能：固化 resizable、enableAnalyzer、copyOption、syncLoad、matchTextDirection、supportSvg2、privacySensitive、enhancedImageQuality 八个高级功能属性的行为规格。

## 概述

| 属性 | 值 |
|------|-----|
| 特性名称 | 高级功能 (Advanced Features) |
| 特性编号 | Func-05-08-01-Feat-03 |
| 所属 Epic | 无（已有能力补录） |
| 优先级 | P2 |
| 目标版本 | API 9 起支持，部分 API 12 增强 |
| SIG 归属 | ArkUI SIG |
| 状态 | Baselined |
| 复杂度 | 标准 |

## 本次变更范围（Delta）

> 历史规格补齐，补录已有实现的完整行为规格。

## 输入文档

| 文档 | 路径 | 状态 |
|------|------|------|
| Design | `specs/05-ui-components/08-image-components/01-image/design.md` | Baselined |

---

## 用户故事

### US-1: 设置图片可拉伸配置

**作为** 应用开发者,
**我想要** 通过 resizable 属性设置图片的九宫格切片或网格拉伸配置,
**以便** 实现图片在不同尺寸下的无损拉伸效果。

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-1.1 | WHEN 调用 `.resizable(value: ResizableOptions)` 传入 slice 配置 THEN 设置九宫格切片（ImageResizableSlice: left/right/top/bottom 四边距） | 正常 |
| AC-1.2 | WHEN 调用 resizable 传入 lattice 配置 THEN 设置网格拉伸（DrawingLattice 对象） | 正常 |
| AC-1.3 | WHEN resizable 设置后 THEN 存储在 RenderProperty 的 ImagePaintStyle 组中，触发 PROPERTY_UPDATE_RENDER | 正常 |
| AC-1.4 | WHEN 存在 resizable 切片配置 THEN 每次 layout wrapper 交换时重新计算拉伸区域，`image_pattern.cpp:1024-1052` | 正常 |
| AC-1.5 | WHEN 存在 resizable 切片或旋转（非 UP）THEN autoResize 被强制关闭，`image_pattern.cpp:880-893` | 正常 |
| AC-1.6 | WHEN resizable slice 值支持 Resource 类型 THEN 通过 ResourceUpdater 支持主题变更动态更新，`image_model_ng.cpp:649-694` | 正常 |

> ImageResizableSlice 定义：`frameworks/base/image/image_resizable_slice.h:36-63`

### US-2: 启用图片分析器

**作为** 应用开发者,
**我想要** 通过 enableAnalyzer 属性启用图片 AI 分析功能,
**以便** 让用户对图片内容进行智能识别和分析。

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-2.1 | WHEN 调用 `.enableAnalyzer(value: boolean)` THEN 启用或关闭图片分析器，默认 false | 正常 |
| AC-2.2 | WHEN enableAnalyzer 设置为 true THEN 创建 ImageAnalyzerManager 实例管理分析功能 | 正常 |
| AC-2.3 | WHEN enableAnalyzer 变更时 THEN 通过 Pattern 成员变量（isEnableAnalyzer_）管理，无 dirty flag 自动触发 | 正常 |
| AC-2.4 | WHEN ImageAnalyzerConfig 配置 THEN 支持设置分析类型集合（types）、标签（tag）、是否显示 AI 按钮（isShowAIButton） | 正常 |

> ImageAnalyzerConfig：`interfaces/inner_api/ace/ai/image_analyzer.h:105-109`

### US-3: 设置复制选项

**作为** 应用开发者,
**我想要** 通过 copyOption 属性设置图片是否可复制及复制范围,
**以便** 控制图片内容的复制行为（应用内/本地/分布式）。

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-3.1 | WHEN 调用 `.copyOption(value: CopyOptions)` THEN 设置复制选项，默认 None | 正常 |
| AC-3.2 | WHEN copyOption 为 None(0) THEN 图片不可复制 | 正常 |
| AC-3.3 | WHEN copyOption 为 InApp(1) THEN 图片仅可在应用内复制 | 正常 |
| AC-3.4 | WHEN copyOption 为 Local(2) THEN 图片可在本设备内复制 | 正常 |
| AC-3.5 | WHEN copyOption 为 Distributed(3) THEN 图片支持跨设备分布式复制 | 正常 |
| AC-3.6 | WHEN 图片被隐私遮盖（obscured by placeholder）THEN 复制功能被禁用，`image_pattern.cpp:1490-1508` | 正常 |
| AC-3.7 | WHEN copyOption 变更时 THEN 通过 Pattern 成员变量（copyOption_）管理，无 dirty flag | 正常 |

> CopyOptions 枚举 4 个值（0-3），`constants.h:727-732`

### US-4: 设置同步加载

**作为** 应用开发者,
**我想要** 通过 syncLoad 属性控制图片加载的同步/异步模式,
**以便** 在需要立即显示图片时使用同步加载避免闪烁。

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-4.1 | WHEN 调用 `.syncLoad(value: boolean)` THEN 设置同步/异步加载模式，默认 false（异步） | 正常 |
| AC-4.2 | WHEN syncLoad 为 false THEN 图片在后台线程加载，UI 线程不阻塞 | 正常 |
| AC-4.3 | WHEN syncLoad 为 true THEN 图片在 UI 线程同步加载，PixelMap 通过 LoadPixelMapDrawableSync() 同步获取，`image_pattern.cpp:1256-1273` | 正常 |
| AC-4.4 | WHEN syncLoad 变更时 THEN 通过 Pattern 成员变量（syncLoad_）管理，传递给 ImageLoadingContext 构造函数 | 正常 |
| AC-4.5 | WHEN syncLoad 设置后对新加载生效 THEN 不影响已加载完成的图片 | 正常 |

> `image_pattern.h:418`：`bool syncLoad_ = false`

### US-5: 匹配文本方向

**作为** 应用开发者,
**我想要** 通过 matchTextDirection 属性让图片在 RTL 布局中自动翻转,
**以便** 支持从右到左的语言环境下的图片显示。

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-5.1 | WHEN 调用 `.matchTextDirection(value: boolean)` THEN 设置是否匹配文本方向，默认 false | 正常 |
| AC-5.2 | WHEN matchTextDirection 为 true 且当前布局为 RTL（isRightToLeft=true）THEN 图片水平翻转（flipHorizontally=true），`image_paint_method.cpp:119-120` | 正常 |
| AC-5.3 | WHEN matchTextDirection 为 false THEN 即使在 RTL 布局中图片也不翻转 | 正常 |
| AC-5.4 | WHEN matchTextDirection 变更时 THEN 触发 PROPERTY_UPDATE_RENDER | 正常 |

> RenderProperty 存储：`image_render_property.h:74`

### US-6: 启用 SVG2 支持

**作为** 应用开发者,
**我想要** 通过 supportSvg2 属性启用 SVG2 规范支持,
**以便** 使用 SVG2 的新特性和元素。

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-6.1 | WHEN 调用 `.supportSvg2(value: boolean)` THEN 启用或关闭 SVG2 支持，默认 false | 正常 |
| AC-6.2 | WHEN supportSvg2 为 true THEN 传递给 ImageLoadingContext（loadingCtx_->SetSupportSvg2(true)），`image_pattern.cpp:1113` | 正常 |
| AC-6.3 | WHEN supportSvg2 变更时 THEN 通过 Pattern 成员变量（supportSvg2_）管理，无 dirty flag | 正常 |

> `image_pattern.h:444`：`bool supportSvg2_ = false`

### US-7: 设置隐私敏感标记

**作为** 应用开发者,
**我想要** 通过 privacySensitive 属性标记图片为隐私敏感内容,
**以便** 在安全显示模式下自动对图片应用模糊遮盖效果。

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-7.1 | WHEN 调用 `.privacySensitive(value: boolean)` THEN 设置隐私敏感标记 | 正常 |
| AC-7.2 | WHEN privacySensitive 为 true 且 isSensitive 为 true THEN 对图片应用模糊背景效果（radius=IMAGE_SENSITIVE_RADIUS, saturation=IMAGE_SENSITIVE_SATURATION, brightness=IMAGE_SENSITIVE_BRIGHTNESS），`image_pattern.cpp:2716-2738` | 正常 |
| AC-7.3 | WHEN privacySensitive 为 false THEN 不应用隐私遮盖效果 | 正常 |
| AC-7.4 | WHEN privacySensitive 属性 THEN 实际存储在 FrameNode 上（host->IsPrivacySensitive()），非 Image 专属属性 | 正常 |

> `image_pattern.cpp:926-931`：通过 host->IsPrivacySensitive() 读取

### US-8: 设置增强图像质量

**作为** 应用开发者,
**我想要** 通过 enhancedImageQuality 属性启用 AI 图像增强,
**以便** 通过 AI 算法提升图片的显示质量。

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-8.1 | WHEN 调用 `.enhancedImageQuality(value: ResolutionQuality)` THEN 设置 AI 图像增强级别，默认 NONE | 正常 |
| AC-8.2 | WHEN enhancedImageQuality 为 NONE(0) THEN 不启用 AI 增强（默认） | 正常 |
| AC-8.3 | WHEN enhancedImageQuality 为 LOW(1) THEN 启用低级别 AI 增强 | 正常 |
| AC-8.4 | WHEN enhancedImageQuality 为 NORMAL(2) THEN 启用中级别 AI 增强 | 正常 |
| AC-8.5 | WHEN enhancedImageQuality 为 HIGH(3) THEN 启用高级别 AI 增强 | 正常 |
| AC-8.6 | WHEN enhancedImageQuality 设置后 THEN 传递给 ImageLoadingContext（loadingCtx_->SetImageQuality()），影响解码质量选择，`image_pattern.cpp:862` | 正常 |

> AIImageQuality 枚举 4 个值（0-3），`constants.h:374-379`。属性名在 API 层为 enhancedImageQuality/ResolutionQuality，内部实现为 AIImageQuality。

---

## 验收追溯

| AC编号 | 关联规则 | 关联 Task | 验证方式 | 证据 |
|-------|----------|-----------|----------|------|
| AC-1.1~1.6 | R-4, R-12 | — | 代码审查 | `image_resizable_slice.h:36-63` |
| AC-2.1~2.4 | R-5 | — | 代码审查 | `image_analyzer.h:105-109` |
| AC-3.1~3.7 | R-6, R-13 | — | 代码审查 | `image_pattern.cpp:1490-1508` |
| AC-4.1~4.5 | R-7 | — | 代码审查 | `image_pattern.cpp:1256-1273` |
| AC-5.1~5.4 | R-8 | — | 代码审查 | `image_paint_method.cpp:119-120` |
| AC-6.1~6.3 | R-9 | — | 代码审查 | `image_pattern.cpp:1113` |
| AC-7.1~7.4 | R-10 | — | 代码审查 | `image_pattern.cpp:2716-2738` |
| AC-8.1~8.6 | R-11 | — | 代码审查 | `image_pattern.cpp:862` |


## 规则定义

> **统一规则表，取消 FR/BR/EX/RC 四分类。** 类型标签：**行为**（正常路径下的系统行为）、**边界**（输入/状态的临界点）、**异常**（非法输入或异常状态的处理）、**恢复**（系统异常后的恢复策略）。

| 规则ID | 类型 | 触发条件 | 预期行为 | 边界/约束 | 关联AC |
|--------|------|----------|----------|-----------|--------|
| R-1 | 行为 | — | 高级功能属性存储位置不统一：resizable/matchTextDirection 存 RenderProperty；enableAnalyzer/copyOption/syncLoad/supportSvg2/privacySensitive/enhancedImageQuality 存 Pattern 成员变量 | — | — |
| R-2 | 行为 | — | Pattern 成员变量没有 dirty flag 机制，需要手动调用 MarkDirty 触发更新 | — | — |
| R-3 | 行为 | — | resizable 的 slice 配置与 autoResize 存在互斥关系：有 slice 配置时 autoResize 被强制关闭 | — | — |
| R-4 | 行为 | — | resizable 支持九宫格切片（ImageResizableSlice）和网格拉伸（DrawingLattice）两种模式，存储在 RenderProperty | — | — |
| R-5 | 行为 | — | enableAnalyzer 通过 ImageAnalyzerManager 管理 AI 分析功能，支持分析类型、标签、AI 按钮配置 | — | — |
| R-6 | 行为 | — | copyOption 控制 4 级复制权限（None/InApp/Local/Distributed），隐私遮盖时强制禁用 | — | — |
| R-7 | 行为 | — | syncLoad 控制同步/异步加载模式，true 时在 UI 线程同步获取 PixelMap | — | — |
| R-8 | 行为 | — | matchTextDirection 在 RTL 布局下自动翻转图片，通过 flipHorizontally 实现 | — | — |
| R-9 | 行为 | — | supportSvg2 传递给 ImageLoadingContext 控制解析器使用 SVG2 规范 | — | — |
| R-10 | 行为 | — | privacySensitive 在 isSensitive 同时为 true 时应用模糊遮盖效果，存储在 FrameNode 而非 Image Pattern | — | — |
| R-11 | 行为 | — | enhancedImageQuality（内部 AIImageQuality）传递给 ImageLoadingContext 影响解码质量选择 | — | — |
| R-12 | 异常 | — | resizable 切片配置存在时 autoResize 被强制关闭，不受用户设置值影响 | — | — |
| R-13 | 异常 | — | 隐私遮盖（obscured）状态下 copyOption 被强制禁用，忽略用户设置 | — | — |
| R-14 | 异常 | — | privacySensitive 需要 isSensitive 同时为 true 才生效，仅设置 privacySensitive 不够 | — | — |
| R-15 | 恢复 | — | — | — | — |
| R-16 | 恢复 | — | — | — | — |
| R-17 | 恢复 | — | — | — | — |

---

## 验证映射

| 编号 | 对应规格项 | 验证方式 | 验证重点 |
|------|-----------|----------|----------|
| VM-1 | AC-1.1~1.6 (resizable) | XTS | slice/lattice 设置和 autoResize 互斥 |
| VM-2 | AC-2.1~2.4 (enableAnalyzer) | XTS | 分析器启用和配置 |
| VM-3 | AC-3.1~3.7 (copyOption) | XTS | 4 级复制权限和隐私禁用 |
| VM-4 | AC-4.1~4.5 (syncLoad) | XTS | 同步/异步加载行为 |
| VM-5 | AC-5.1~5.4 (matchTextDirection) | XTS | RTL 布局下水平翻转 |
| VM-6 | AC-6.1~6.3 (supportSvg2) | XTS | SVG2 解析支持 |
| VM-7 | AC-7.1~7.4 (privacySensitive) | XTS | 隐私遮盖效果 |
| VM-8 | AC-8.1~8.6 (enhancedImageQuality) | XTS | AI 图像增强级别 |

## API 变更分析

### 新增 API

| API 名称 | 类型 | 功能描述 | 关联 AC |
|----------|------|----------|---------|
| `resizable(value: ResizableOptions)` | Public | 设置可拉伸配置（slice/lattice） | AC-1.1~1.6 |
| `enableAnalyzer(value: boolean)` | Public | 启用图片分析器（默认 false） | AC-2.1~2.4 |
| `copyOption(value: CopyOptions)` | Public | 设置复制选项（默认 None） | AC-3.1~3.7 |
| `syncLoad(value: boolean)` | Public | 设置同步加载（默认 false） | AC-4.1~4.5 |
| `matchTextDirection(value: boolean)` | Public | 设置匹配文本方向（默认 false） | AC-5.1~5.4 |
| `supportSvg2(value: boolean)` | Public | 启用 SVG2 支持（默认 false） | AC-6.1~6.3 |
| `privacySensitive(value: boolean)` | Public | 设置隐私敏感标记 | AC-7.1~7.4 |
| `enhancedImageQuality(value: ResolutionQuality)` | Public | 设置增强图像质量（默认 NONE） | AC-8.1~8.6 |

### 变更/废弃 API

无。

## 接口规格

### 接口定义

> 本特性为已有实现补录，接口行为定义详见上方规则定义和用户故事。

无新增接口规格。

---

## 兼容性声明

- **已有 API 行为变更:** 否
- **配置文件格式变更:** 否
- **数据存储格式变更:** 否
- **最低支持版本:** API 9
- **API 版本号策略:** 各属性按 @since 标注版本支持

## 架构约束

| 关键约束 | 约束说明 | 影响 AC |
|---------|----------|---------|
| Pattern 成员无 dirty flag | enableAnalyzer/copyOption/syncLoad/supportSvg2/enhancedImageQuality 存 Pattern 成员，变更不自动触发更新 | AC-2~4, AC-6, AC-8 |
| privacySensitive FrameNode 存储 | 实际存储在 FrameNode 级别，非 Image Pattern 独有 | AC-7 |
| resizable 与 autoResize 互斥 | 有 resizable 配置时 autoResize 被强制关闭 | AC-1.5 |

## 非功能性需求

| 类型 | 指标/阈值 | 验证方式 | 证据 |
|------|----------|----------|------|
| 性能 | syncLoad=true 阻塞 UI 线程，仅建议小图使用 | 代码审查 | `image_pattern.cpp:1256-1273` |
| 安全 | copyOption 隐私遮盖强制禁用复制，防止隐私泄露 | 代码审查 | `image_pattern.cpp:1490-1508` |
| 安全 | privacySensitive 模糊遮盖效果保护敏感图片 | 代码审查 | `image_pattern.cpp:2716-2738` |

## 多设备适配声明

| 设备类型 | 行为差异 | 规格/约束 | 验证方式 | 证据 |
|----------|----------|-----------|----------|------|
| 手机 | 无差异 | — | — | — |
| 平板 | 无差异 | — | — | — |
| 折叠屏 | 无差异 | — | — | — |

---

## 全局特性影响

| 特性 | 适用？ | 结论 | 关联场景 |
|------|--------|------|----------|
| 无障碍 | 否 | 高级功能不影响无障碍 | — |
| 大字体 | 否 | 高级功能不受大字体影响 | — |
| 深色模式 | 否 | 无特殊处理 | — |
| 多窗口/分屏 | 否 | 无特殊处理 | — |
| 多用户 | 是 | privacySensitive 需结合用户安全状态生效 | AC-7 |
| 版本升级 | 否 | 无版本相关行为变更 | — |
| 生态兼容 | 否 | 无特殊兼容性问题 | — |

## 行为场景（可选，Gherkin）

```gherkin
Feature: Image 高级功能属性

  Scenario: resizable 与 autoResize 互斥
    Given 一个 Image 组件，autoResize 已设置
    When 设置 resizable slice 配置（left=10, top=10, right=10, bottom=10）
    Then autoResize 被强制关闭
    And 图片使用原始尺寸进行九宫格拉伸

  Scenario: syncLoad 同步加载
    Given 一个 Image 组件，syncLoad 设置为 true
    When 设置图片源
    Then 图片在 UI 线程同步加载
    And LoadPixelMapDrawableSync() 被调用
    And 加载完成前 UI 线程被阻塞

  Scenario: matchTextDirection RTL 翻转
    Given 一个 Image 组件，matchTextDirection 设置为 true
    And 当前布局为 RTL（isRightToLeft=true）
    When 触发渲染
    Then 图片水平翻转（flipHorizontally=true）

  Scenario: privacySensitive 隐私遮盖
    Given 一个 Image 组件，privacySensitive 设置为 true
    And isSensitive 状态为 true
    When 触发渲染
    Then 图片显示模糊遮盖效果
    And 模糊参数为 IMAGE_SENSITIVE_RADIUS/SATURATION/BRIGHTNESS

  Scenario: copyOption 隐私禁用
    Given 一个 Image 组件，copyOption 设置为 Local
    And 图片被隐私遮盖（obscured）
    When 用户尝试复制图片
    Then 复制功能被禁用
```

## Spec 自审清单

- [x] 无"待定""TBD""TODO"等占位符
- [x] 所有 AC 使用 WHEN/THEN 格式，可独立测试
- [x] 范围边界明确（高级功能 8 个属性，不含核心显示/颜色效果/事件）
- [x] 无语义模糊表述
- [x] AC 与业务规则/异常规则/恢复契约交叉一致

## context-references

```yaml
context-queries:
  - repo: "openharmony/arkui_ace_engine"
    query: "Image advanced properties: resizable slice/lattice, syncLoad, copyOption, privacySensitive, AI image quality"
```

**关键文档：** `design.md`（同目录）
