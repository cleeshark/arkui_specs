# 特性规格

> Func-05-08-01-Feat-04 事件回调：固化 onComplete、onError、onFinish 三个事件回调及 LoadImageSuccessEvent、LoadImageFailEvent 数据结构的行为规格。

## 概述

| 属性 | 值 |
|------|-----|
| 特性名称 | 事件回调 (Event Callbacks) |
| 特性编号 | Func-05-08-01-Feat-04 |
| 所属 Epic | 无（已有能力补录） |
| 优先级 | P1 |
| 目标版本 | API 7 起支持 |
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

### US-1: 监听图片加载完成

**作为** 应用开发者,
**我想要** 通过 onComplete 回调获取图片加载成功后的详细信息,
**以便** 根据图片实际尺寸、组件尺寸、内容区域等信息进行后续处理。

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-1.1 | WHEN 调用 `.onComplete(callback: (event: ImageCompleteEvent) => void)` THEN 注册图片加载完成回调 | 边界 |
| AC-1.2 | WHEN 图片数据就绪完成布局计算（OnDataReady）THEN 触发 onComplete，loadingStatus=0，`image_pattern.cpp:213-244` | 正常 |
| AC-1.3 | WHEN 图片完整解码成功（OnImageLoadSuccess）THEN 触发 onComplete，loadingStatus=1，`image_pattern.cpp:543-549` | 正常 |
| AC-1.4 | WHEN onComplete 触发且 loadingStatus=0 THEN event 包含：width（原始图宽）、height（原始图高）、componentWidth（组件宽）、componentHeight（组件高）、contentWidth/Height（内容尺寸来自 geometryNode） | 正常 |
| AC-1.5 | WHEN onComplete 触发且 loadingStatus=1 THEN event 包含：width（原始图宽）、height（原始图高）、componentWidth（组件宽）、componentHeight（组件高）、contentWidth/Height（来自 CalcImageContentPaintSize）、contentOffsetX/Y（内容偏移） | 正常 |
| AC-1.6 | WHEN onComplete 回调未注册 THEN 不触发任何回调逻辑 | 正常 |

> LoadImageSuccessEvent 定义：`frameworks/core/components/image/image_event.h:24-93`

### US-2: 监听图片加载失败

**作为** 应用开发者,
**我想要** 通过 onError 回调获取图片加载失败的错误信息,
**以便** 处理加载失败场景（如显示错误提示、重试等）。

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-2.1 | WHEN 调用 `.onError(callback: (event: ImageError) => void)` THEN 注册图片加载失败回调 | 异常 |
| AC-2.2 | WHEN 图片加载或解码失败 THEN 触发 onError，传入 LoadImageFailEvent，`image_pattern.cpp:704-724` | 异常 |
| AC-2.3 | WHEN onError 触发 THEN event 包含：componentWidth（组件宽）、componentHeight（组件高）、errorMessage（错误描述字符串） | 异常 |
| AC-2.4 | WHEN onError 触发且存在结构化错误信息 THEN event 额外包含 errorInfo（ImageErrorInfo：errorCode + errorMessage + downloadInfo） | 异常 |
| AC-2.5 | WHEN onError 触发后 THEN Image 尝试进入 alt 降级链（加载 alt 替代图） | 异常 |
| AC-2.6 | WHEN onError 回调未注册 THEN 不触发任何回调逻辑，但降级链仍然执行 | 异常 |

> LoadImageFailEvent 定义：`frameworks/core/components/image/image_event.h:95-135`

### US-3: 监听动画播放完成

**作为** 应用开发者,
**我想要** 通过 onFinish 回调获知动画图片播放完成,
**以便** 在 GIF/WebP 动画播放结束时执行后续操作。

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-3.1 | WHEN 调用 `.onFinish(callback: () => void)` THEN 注册动画播放完成回调 | 边界 |
| AC-3.2 | WHEN 动画图片（GIF/WebP/SVG 动画）播放到最后一帧 THEN 触发 onFinish，`image_pattern.cpp:267-278` | 正常 |
| AC-3.3 | WHEN 图片为静态图片 THEN onFinish 不会被触发 | 正常 |
| AC-3.4 | WHEN onFinish 通过 CanvasImage::SetOnFinishCallback 注册 THEN 回调在动画帧完成时由渲染管道触发 | 正常 |
| AC-3.5 | WHEN onFinish 回调未注册 THEN 动画正常播放但不触发回调 | 正常 |

> onFinish 与 onComplete/onError 独立——onFinish 专属于动画播放完成，不属于图片加载生命周期。

### US-4: 获取加载完成事件数据

**作为** 应用开发者,
**我想要** 在 onComplete 回调中获取完整的图片渲染信息,
**以便** 精确了解图片的原始尺寸、组件尺寸、内容区域和偏移量。

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-4.1 | WHEN LoadImageSuccessEvent 创建 THEN 包含 width（double, 默认 0.0）：图片原始宽度（像素） | 正常 |
| AC-4.2 | WHEN LoadImageSuccessEvent 创建 THEN 包含 height（double, 默认 0.0）：图片原始高度（像素） | 正常 |
| AC-4.3 | WHEN LoadImageSuccessEvent 创建 THEN 包含 componentWidth（double, 默认 0.0）：组件帧宽度 | 正常 |
| AC-4.4 | WHEN LoadImageSuccessEvent 创建 THEN 包含 componentHeight（double, 默认 0.0）：组件帧高度 | 正常 |
| AC-4.5 | WHEN LoadImageSuccessEvent 创建 THEN 包含 loadingStatus（int32_t, 默认 1）：0=布局完成，1=加载成功 | 正常 |
| AC-4.6 | WHEN LoadImageSuccessEvent 创建 THEN 包含 contentWidth（double, 默认 0.0）：绘制内容区域宽度 | 正常 |
| AC-4.7 | WHEN LoadImageSuccessEvent 创建 THEN 包含 contentHeight（double, 默认 0.0）：绘制内容区域高度 | 正常 |
| AC-4.8 | WHEN LoadImageSuccessEvent 创建 THEN 包含 contentOffsetX（double, 默认 0.0）：内容区域 X 偏移 | 正常 |
| AC-4.9 | WHEN LoadImageSuccessEvent 创建 THEN 包含 contentOffsetY（double, 默认 0.0）：内容区域 Y 偏移 | 正常 |

### US-5: 获取加载失败事件数据

**作为** 应用开发者,
**我想要** 在 onError 回调中获取完整的错误信息,
**以便** 精确定位图片加载失败的原因和上下文。

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-5.1 | WHEN LoadImageFailEvent 创建 THEN 包含 componentWidth（double, 默认 0.0）：组件帧宽度 | 正常 |
| AC-5.2 | WHEN LoadImageFailEvent 创建 THEN 包含 componentHeight（double, 默认 0.0）：组件帧高度 | 正常 |
| AC-5.3 | WHEN LoadImageFailEvent 创建 THEN 包含 errorMessage（string, 默认 ""）：错误描述文本 | 异常 |
| AC-5.4 | WHEN LoadImageFailEvent 创建且存在结构化错误 THEN 包含 errorInfo（ImageErrorInfo） | 异常 |
| AC-5.5 | WHEN ImageErrorInfo 存在 THEN 包含 errorCode（ImageErrorCode 枚举）和 errorMessage（详细错误描述） | 异常 |
| AC-5.6 | WHEN ImageErrorInfo 存在且为网络错误 THEN 可能包含 downloadInfo（CppDownloadInfo 指针） | 异常 |

> ImageErrorCode 枚举覆盖：未知源类型(101000)、HTTP/网络错误(102xxx)、解码错误(103xxx)、Canvas图片错误(111xxx)。`frameworks/base/image/image_defines.h:39-64`

---

## 验收追溯

| AC编号 | 关联规则 | 关联 Task | 验证方式 | 证据 |
|-------|----------|-----------|----------|------|
| AC-1.1~1.6 | R-4 | — | 代码审查 | `image_event_hub.h:48-56` |
| AC-2.1~2.6 | R-5, R-6 | — | 代码审查 | `image_pattern.cpp:704-724` |
| AC-3.1~3.5 | R-7 | — | 代码审查 | `image_pattern.cpp:267-278` |
| AC-4.1~4.9 | R-8 | — | 代码审查 | `image_event.h:24-93` |
| AC-5.1~5.6 | R-9 | — | 代码审查 | `image_event.h:95-135` |


## 规则定义

> **统一规则表，取消 FR/BR/EX/RC 四分类。** 类型标签：**行为**（正常路径下的系统行为）、**边界**（输入/状态的临界点）、**异常**（非法输入或异常状态的处理）、**恢复**（系统异常后的恢复策略）。

| 规则ID | 类型 | 触发条件 | 预期行为 | 边界/约束 | 关联AC |
|--------|------|----------|----------|-----------|--------|
| R-1 | 行为 | — | onComplete 在图片加载生命周期中可被触发两次：loadingStatus=0（数据就绪/布局完成）和 loadingStatus=1（完整解码成功） | — | — |
| R-2 | 行为 | — | onFinish 仅适用于动画图片（GIF/WebP/SVG 动画），与图片加载生命周期无关 | — | — |
| R-3 | 行为 | — | onError 触发后会自动进入 alt 降级链，开发者无需手动触发替代图加载 | — | — |
| R-4 | 行为 | — | onComplete 注册在 ImageEventHub，由 ImagePattern 在 OnImageDataReady（loadingStatus=0）和 OnImageLoadSuccess（loadingStatus=1）时触发 | — | — |
| R-5 | 行为 | — | onError 注册在 ImageEventHub，由 ImagePattern 在 OnImageLoadFail 时触发，传入组件尺寸和错误信息 | — | — |
| R-6 | 行为 | — | onError 触发后 ImagePattern 自动尝试加载 alt → altError → altPlaceholder 降级链 | — | — |
| R-7 | 行为 | — | onFinish 注册在 ImageEventHub，通过 CanvasImage::SetOnFinishCallback 在动画帧完成时触发，仅对非静态图片生效 | — | — |
| R-8 | 行为 | — | LoadImageSuccessEvent 包含 9 个字段（width/height/componentWidth/componentHeight/loadingStatus/contentWidth/contentHeight/contentOffsetX/contentOffsetY），全部为 double/int32_t 类型 | — | — |
| R-9 | 行为 | — | LoadImageFailEvent 包含 4 个字段（componentWidth/componentHeight/errorMessage/errorInfo），errorInfo 为可选的 ImageErrorInfo 结构体 | — | — |
| R-10 | 异常 | — | 静态图片不会触发 onFinish 回调，仅动画图片（GIF/WebP/SVG 动画）会触发 | — | — |
| R-11 | 异常 | — | onComplete 的 iOS 平台有防重复注册保护（line 50-54 of image_event_hub.h），其他平台无此限制 | — | — |
| R-12 | 异常 | — | ImageErrorInfo 的 downloadInfo 可能为 nullptr（非网络错误场景） | — | — |
| R-13 | 恢复 | — | — | — | — |
| R-14 | 恢复 | — | — | — | — |
| R-15 | 恢复 | — | — | — | — |

---

## 验证映射

| 编号 | 对应规格项 | 验证方式 | 验证重点 |
|------|-----------|----------|----------|
| VM-1 | AC-1.1~1.6 (onComplete) | XTS | 两次触发（loadingStatus 0 和 1）和事件数据完整性 |
| VM-2 | AC-2.1~2.6 (onError) | XTS | 错误信息内容和降级链触发 |
| VM-3 | AC-3.1~3.5 (onFinish) | XTS | 动画图片 vs 静态图片行为差异 |
| VM-4 | AC-4.1~4.9 (SuccessEvent) | XTS | 9 个字段的值正确性 |
| VM-5 | AC-5.1~5.6 (FailEvent) | XTS | 4 个字段的值和 errorInfo 结构 |

## API 变更分析

### 新增 API

| API 名称 | 类型 | 功能描述 | 关联 AC |
|----------|------|----------|---------|
| `onComplete(callback: ImageOnCompleteCallback)` | Public | 图片加载完成回调（两次触发） | AC-1.1~1.6 |
| `onError(callback: ImageErrorCallback)` | Public | 图片加载失败回调 | AC-2.1~2.6 |
| `onFinish(callback: VoidCallback)` | Public | 动画播放完成回调 | AC-3.1~3.5 |

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
- **最低支持版本:** API 7
- **API 版本号策略:** 三个事件回调从 API 7 起支持

## 架构约束

| 关键约束 | 约束说明 | 影响 AC |
|---------|----------|---------|
| EventHub 模式 | 三个回调统一注册在 ImageEventHub，由 ImagePattern 在对应时机触发 | AC-1~3 |
| CanvasImage 回调 | onFinish 通过 CanvasImage::SetOnFinishCallback 注册，在渲染管道帧完成时回调 | AC-3.4 |
| 事件触发线程 | 所有回调在 UI 线程触发，由 ImagePattern 在加载/渲染回调中调用 | AC-1~3 |

## 非功能性需求

| 类型 | 指标/阈值 | 验证方式 | 证据 |
|------|----------|----------|------|
| 可靠性 | onComplete 两次触发确保开发者可在布局阶段和渲染阶段分别获取状态 | 代码审查 | `image_pattern.cpp:213-244, 543-549` |
| 问题定位 | ImageErrorCode 提供结构化错误码（101000~111xxx），支持精确错误定位 | 代码审查 | `image_defines.h:39-64` |

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
| 无障碍 | 否 | 事件回调不影响无障碍 | — |
| 大字体 | 否 | 事件回调不受大字体影响 | — |
| 深色模式 | 否 | 无特殊处理 | — |
| 多窗口/分屏 | 否 | 无特殊处理 | — |
| 多用户 | 否 | 无特殊处理 | — |
| 版本升级 | 否 | 无版本相关行为变更 | — |
| 生态兼容 | 否 | 无特殊兼容性问题 | — |

## 行为场景（可选，Gherkin）

```gherkin
Feature: Image 事件回调

  Scenario: onComplete 两次触发
    Given 一个 Image 组件，注册了 onComplete 回调
    And 图片源指向一个有效的网络图片
    When 图片数据下载完成并完成布局计算
    Then onComplete 被触发，loadingStatus=0
    And event.width/height 为图片原始尺寸
    When 图片完整解码成功
    Then onComplete 再次被触发，loadingStatus=1
    And event.contentWidth/contentHeight 来自 CalcImageContentPaintSize
    And event.contentOffsetX/contentOffsetY 有实际值

  Scenario: onError 触发后进入降级链
    Given 一个 Image 组件，设置了 alt 占位图
    And 注册了 onError 回调
    When 主图加载失败（如网络错误）
    Then onError 被触发，event.errorMessage 包含错误描述
    And event.errorInfo.errorCode 为对应错误码（如 102xxx 网络错误）
    And 自动尝试加载 alt 占位图

  Scenario: onFinish 仅动画图片触发
    Given 一个 Image 组件，注册了 onFinish 回调
    And 图片源为静态 PNG
    When 图片加载完成
    Then onFinish 不被触发

  Scenario: onFinish 动画播放完成
    Given 一个 Image 组件，注册了 onFinish 回调
    And 图片源为 GIF 动画
    When GIF 动画播放到最后一帧
    Then onFinish 被触发
```

## Spec 自审清单

- [x] 无"待定""TBD""TODO"等占位符
- [x] 所有 AC 使用 WHEN/THEN 格式，可独立测试
- [x] 范围边界明确（3 个事件回调 + 2 个事件数据结构，不含属性类规格）
- [x] 无语义模糊表述
- [x] AC 与业务规则/异常规则/恢复契约交叉一致

## context-references

```yaml
context-queries:
  - repo: "openharmony/arkui_ace_engine"
    query: "Image event hub: onComplete/onError/onFinish callback registration and trigger points in ImagePattern"
```

**关键文档：** `design.md`（同目录）
