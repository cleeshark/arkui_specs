# 特性规格

> Func-05-04-03-Feat-01 Rating 组件：固化星级评分组件的构造参数、stars/stepSize/starStyle 属性、onChange 回调、指示器模式、RTL 布局、键盘导航、无障碍和内容修饰器的行为规格。

## 概述

| 属性 | 值 |
|------|-----|
| 特性名称 | Rating 评分组件 (Rating Component) |
| 特性编号 | Func-05-04-03-Feat-01 |
| 所属 Epic | 无（已有能力补录） |
| 优先级 | P0 |
| 目标版本 | API 7 起支持，API 12 contentModifier，API 18 Optional 重载，API 20 ResourceStr，API 23 静态版本 |
| SIG 归属 | ArkUI SIG |
| 状态 | Baselined |
| 复杂度 | 中等 |

## 本次变更范围（Delta）

> 历史规格补齐，补录已有实现的完整行为规格。

| 类型 | 内容 | 说明 |
|------|------|------|
| ADDED | Rating 组件完整行为规格 | 补录构造参数、stars/stepSize/starStyle/onChange、指示器模式、RTL、键盘导航、无障碍、contentModifier |

## 输入文档

| 文档 | 路径 | 状态 |
|------|------|------|
| Design | `specs/05-ui-components/04-input-form-components/03-rating/design.md` | Baselined |
| SDK API | `docs/sdk/ArkUI_SDK_API_Knowledge_Base.md` | — |
| SDK 组件 | `docs/sdk/Component_API_Knowledge_Base_CN.md` | — |

---

## 用户故事

### US-1: 创建评分组件

**作为** 应用开发者,
**我想要** 使用 `Rating(options?)` 创建一个星级评分组件并设置初始评分和模式,
**以便** 在应用中展示交互式或只读的评分控件。

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-1.1 | WHEN 调用 `Rating(options?: RatingOptions)` 无参数 THEN 创建一个默认 rating=0.0、indicator=false 的评分组件 | 正常 |
| AC-1.2 | WHEN 传入 `{rating: 3.5, indicator: true}` THEN 组件创建为指示器模式，评分值初始为 3.5 | 正常 |
| AC-1.3 | WHEN stars<=0 THEN ConstrainsRatingScore 将 stars 重置为 DEFAULT_RATING_STAR_NUMBER(5) | 异常 |
| AC-1.4 | WHEN ratingScore<=0 THEN ConstrainsRatingScore 将 ratingScore 重置为 DEFAULT_RATING_SCORE_VALUE(0.0) | 异常 |

### US-2: 设置星星数量

**作为** 应用开发者,
**我想要** 通过 `.stars()` 设置评分组件的星星数量,
**以便** 控制评分的最大范围。

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-2.1 | WHEN 调用 `.stars(value)` THEN 星星数量被设置为 value，默认值为 5 | 正常 |
| AC-2.2 | WHEN stars<0 THEN 值被重置为默认值 5，不报错 | 异常 |
| AC-2.3 | WHEN stars 变更 THEN 触发 PROPERTY_UPDATE_MEASURE 重新测量 | 边界 |

### US-3: 设置步长

**作为** 应用开发者,
**我想要** 通过 `.stepSize()` 设置评分步长,
**以便** 控制评分的精度。

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-3.1 | WHEN 调用 `.stepSize(value)` THEN 步长被设置为 value，默认值为 0.5 | 正常 |
| AC-3.2 | WHEN stepSize<0.1 THEN 值被重置为默认值 0.5 | 异常 |
| AC-3.3 | WHEN stepSize>stars THEN 值被重置为默认值 0.5 | 异常 |
| AC-3.4 | WHEN 评分值变更 THEN drawScore=Round(ratingScore/stepSize)*stepSize，再钳位到 [0,stars] | 边界 |

### US-4: 设置星星样式图片

**作为** 应用开发者,
**我想要** 通过 `.starStyle()` 自定义星星的前景、次级和背景图片,
**以便** 实现个性化的评分外观。

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-4.1 | WHEN 调用 `.starStyle({backgroundUri, foregroundUri})` THEN 背景和前景图片来源被设置 | 正常 |
| AC-4.2 | WHEN secondaryUri 缺失 THEN 次级图片回退使用 backgroundUri | 异常 |
| AC-4.3 | WHEN 三张图片全部加载成功 THEN RATING_IMAGE_SUCCESS_CODE=0b111，使用自定义图片渲染 | 边界 |

### US-5: 评分变化回调

**作为** 应用开发者,
**我想要** 通过 `.onChange()` 监听评分变化,
**以便** 在用户设置评分时执行业务逻辑。

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-5.1 | WHEN 用户触摸/键盘操作导致评分变化 THEN onChange 回调被触发，参数为新的 ratingScore | 正常 |
| AC-5.2 | WHEN 触摸事件发生 THEN RecalculatedRatingScoreBasedOnEventPoint 计算触摸坐标对应的评分值 | 正常 |

### US-6: 指示器模式

**作为** 应用开发者,
**我想要** 设置 `indicator: true` 使 Rating 进入只读模式,
**以便** 仅展示评分而不允许交互。

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-6.1 | WHEN indicator=true THEN 组件高度默认为 12vp | 边界 |
| AC-6.2 | WHEN indicator=false THEN 组件高度默认为 28vp | 边界 |
| AC-6.3 | WHEN indicator=true THEN FocusType::DISABLE，禁用触摸/点击/拖拽/键盘 | 正常 |

### US-7: RTL 布局

**作为** 应用开发者,
**我想要** Rating 在 RTL（从右到左）语言环境下镜像布局,
**以便** 适配阿拉伯语等 RTL 语言。

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-7.1 | WHEN RTL 模式下触摸 THEN X 坐标反转：x = width - x | 边界 |
| AC-7.2 | WHEN RTL 模式 THEN touchStarIndex = starNum - wholeStarNum - 1 | 边界 |

### US-8: 键盘导航

**作为** 应用开发者,
**我想要** 通过键盘方向键和功能键操作 Rating 评分,
**以便** 在无障碍和外接键盘场景下使用。

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-8.1 | WHEN 按下 DPAD_LEFT/Left THEN 评分减少 stepSize | 正常 |
| AC-8.2 | WHEN 按下 DPAD_RIGHT/Right THEN 评分增加 stepSize | 正常 |
| AC-8.3 | WHEN 按下 HOME THEN 评分设为 0；WHEN 按下 END THEN 评分设为 stars | 正常 |
| AC-8.4 | WHEN 按下 ENTER/SPACE THEN 触发 onChange 回调 | 正常 |

### US-9: 无障碍与内容修饰器

**作为** 应用开发者,
**我想要** Rating 支持无障碍属性和内容修饰器,
**以便** 满足无障碍合规要求和自定义渲染需求。

| AC编号 | 验收标准 | 类型 |
|--------|---------|------|
| AC-9.1 | WHEN 无障碍查询 THEN HasRange=true，GetAccessibilityValue 返回 max=stars/current=ratingScore/min=0 | 正常 |
| AC-9.2 | WHEN 调用 `.contentModifier(modifier)` (API 12+) THEN RatingConfiguration 传递 rating/indicator/stars/stepSize/triggerChange 给自定义渲染 | 正常 |

---

## 验收追溯

| AC编号 | US ID | 关联规则 | 验证手段 |
|-------|-------|----------|----------|
| AC-1.1 | US-1 | R-1, R-2 | 代码审查 rating_model_ng.cpp:61-72 |
| AC-1.2 | US-1 | R-2, R-3 | 代码审查 rating_model_ng.cpp:105-121 |
| AC-1.3 | US-1 | R-4 | 代码审查 rating_pattern.cpp:303-341 |
| AC-1.4 | US-1 | R-4 | 代码审查 rating_pattern.cpp:303-341 |
| AC-2.1 | US-2 | R-5 | 代码审查 rating_model_ng.cpp:123-126 |
| AC-2.2 | US-2 | R-6 | 代码审查 rating_pattern.cpp:303-341 |
| AC-2.3 | US-2 | R-7 | 代码审查 rating_layout_property.h:59 |
| AC-3.1 | US-3 | R-8 | 代码审查 rating_model_ng.cpp:128-131 |
| AC-3.2 | US-3 | R-9 | 代码审查 rating_pattern.cpp:303-341 |
| AC-3.3 | US-3 | R-9 | 代码审查 rating_pattern.cpp:303-341 |
| AC-3.4 | US-3 | R-10 | 代码审查 rating_pattern.cpp:303-341 |
| AC-4.1 | US-4 | R-11 | 代码审查 rating_model_ng.cpp:133-185 |
| AC-4.2 | US-4 | R-12 | 代码审查 rating_pattern.cpp:967-1001 |
| AC-4.3 | US-4 | R-13 | 代码审查 rating_pattern.cpp:967-1001 |
| AC-5.1 | US-5 | R-14 | 代码审查 rating_event_hub.h:39-47 |
| AC-5.2 | US-5 | R-15 | 代码审查 rating_pattern.cpp:343-393 |
| AC-6.1 | US-6 | R-16 | 代码审查 rating_layout_algorithm.cpp:22-78 |
| AC-6.2 | US-6 | R-16 | 代码审查 rating_layout_algorithm.cpp:22-78 |
| AC-6.3 | US-6 | R-17 | 代码审查 rating_pattern.cpp:82-87 |
| AC-7.1 | US-7 | R-18 | 代码审查 rating_pattern.cpp:343-393 |
| AC-7.2 | US-7 | R-18 | 代码审查 rating_pattern.cpp:343-393 |
| AC-8.1 | US-8 | R-19 | 代码审查 rating_pattern.cpp:642-679 |
| AC-8.2 | US-8 | R-19 | 代码审查 rating_pattern.cpp:642-679 |
| AC-8.3 | US-8 | R-19 | 代码审查 rating_pattern.cpp:642-679 |
| AC-8.4 | US-8 | R-19 | 代码审查 rating_pattern.cpp:642-679 |
| AC-9.1 | US-9 | R-20 | 代码审查 rating_accessibility_property.cpp:31-34 |
| AC-9.2 | US-9 | R-21 | 代码审查 rating_modifier.h:37, rating_paint_method.h:43-68 |

---

## 规则定义

> **统一规则表。** 类型标签：**行为**（正常路径下的系统行为）、**边界**（输入/状态的临界点）、**异常**（非法输入或异常状态的处理）、**恢复**（系统异常后的恢复策略）。

| 规则ID | 类型 | 触发条件 | 预期行为 | 边界/约束 | 关联AC |
|--------|------|----------|----------|-----------|--------|
| R-1 | 行为 | `rating_model_ng.cpp:61-72` | Rating 创建时使用 RATING_ETS_TAG 创建 FrameNode，默认 rating=0.0、indicator=false | — | AC-1.1 |
| R-2 | 行为 | `rating_model_ng.cpp:105-121` | SetRatingScore 和 SetIndicator 在创建时设置初始评分值和指示器模式 | — | AC-1.1, AC-1.2 |
| R-3 | 行为 | `rating_model_ng.cpp:105-116` | ratingScore 通过 SetRatingScore 存入 RatingRenderProperty | — | AC-1.2 |
| R-4 | 行为 | `rating_pattern.cpp:303-341` | ConstrainsRatingScore 约束：stars<=0→5, ratingScore<=0→0.0, stepSize>stars→0.5 | — | AC-1.3, AC-1.4 |
| R-5 | 行为 | `rating_model_ng.cpp:123-126` | stars 通过 SetStars 存入 RatingLayoutProperty，默认值 DEFAULT_RATING_STAR_NUMBER=5 | — | AC-2.1 |
| R-6 | 异常 | `rating_pattern.cpp:303-341` | stars<0 时重置为默认值 5，不抛出异常 | — | AC-2.2 |
| R-7 | 边界 | `rating_layout_property.h:59` | stars 变更触发 PROPERTY_UPDATE_MEASURE | — | AC-2.3 |
| R-8 | 行为 | `rating_model_ng.cpp:128-131` | stepSize 通过 SetStepSize 存入 RatingRenderProperty，默认值 DEFAULT_RATING_STEP_SIZE_VALUE=0.5 | — | AC-3.1 |
| R-9 | 异常 | `rating_pattern.cpp:303-341` | stepSize<0.1 或 stepSize>stars 时重置为默认值 0.5 | — | AC-3.2, AC-3.3 |
| R-10 | 边界 | `rating_pattern.cpp:303-341` | drawScore=Round(ratingScore/stepSize)*stepSize，钳位到 [0,stars] | — | AC-3.4 |
| R-11 | 行为 | `rating_model_ng.cpp:133-185` | SetForegroundSrc/SetSecondarySrc/SetBackgroundSrc 设置三张图片来源到 RatingLayoutProperty | — | AC-4.1 |
| R-12 | 异常 | `rating_pattern.cpp:967-1001` | secondaryUri 缺失时次级图片回退使用 backgroundUri | — | AC-4.2 |
| R-13 | 边界 | `rating_pattern.cpp:967-1001` | RATING_IMAGE_SUCCESS_CODE=0b111 表示三张图片全部加载成功 | — | AC-4.3 |
| R-14 | 行为 | `rating_event_hub.h:39-47` | FireChangeEvent 在评分变化时触发 onChange 回调 | — | AC-5.1 |
| R-15 | 行为 | `rating_pattern.cpp:343-393` | RecalculatedRatingScoreBasedOnEventPoint 计算触摸坐标对应的评分值 | — | AC-5.2 |
| R-16 | 边界 | `rating_layout_algorithm.cpp:22-78` | MeasureContent：指示器 12vp，非指示器 28vp；width-only→height=width/stars | — | AC-6.1, AC-6.2 |
| R-17 | 行为 | `rating_pattern.cpp:82-87` | indicator=true 时 GetFocusPattern 返回 FocusType::DISABLE | — | AC-6.3 |
| R-18 | 边界 | `rating_pattern.cpp:343-393` | RTL 下 X 坐标反转，touchStarIndex=starNum-wholeStarNum-1 | — | AC-7.1, AC-7.2 |
| R-19 | 行为 | `rating_pattern.cpp:642-679` | OnKeyEvent 处理 DPAD/HOME/END/ENTER/SPACE | — | AC-8.1~8.4 |
| R-20 | 行为 | `rating_accessibility_property.cpp:31-34` | HasRange=true，GetAccessibilityValue 返回 max=stars/current=ratingScore/min=0；IsEditable=!indicator | — | AC-9.1 |
| R-21 | 行为 | `rating_modifier.h:37`, `rating_paint_method.h:43-68` | RatingModifier 继承 ContentModifier，RatingConfiguration 传递 rating/indicator/stars/stepSize/triggerChange | — | AC-9.2 |

---

## 验证映射

| VM编号 | 关联用户故事 | 验证手段 | 验证要点 |
|-------|-------------|---------|---------|
| VM-1 | US-1 创建评分组件 (AC-1.1~1.4) | 代码审查 | FrameNode 创建；评分约束逻辑 |
| VM-2 | US-2 星星数量 (AC-2.1~2.3) | 代码审查 | stars 默认值和非法值重置；脏标记 |
| VM-3 | US-3 步长 (AC-3.1~3.4) | 代码审查 | stepSize 默认值和约束；drawScore 计算 |
| VM-4 | US-4 星星样式 (AC-4.1~4.3) | 代码审查 | 三张图片设置；回退逻辑；成功码 |
| VM-5 | US-5 评分回调 (AC-5.1~5.2) | 代码审查 | onChange 触发；触摸计算 |
| VM-6 | US-6 指示器模式 (AC-6.1~6.3) | 代码审查 | 尺寸差异；FocusType::DISABLE |
| VM-7 | US-7 RTL (AC-7.1~7.2) | 代码审查 | X 反转；touchStarIndex |
| VM-8 | US-8 键盘导航 (AC-8.1~8.4) | 代码审查 | 方向键/HOME/END/ENTER/SPACE |
| VM-9 | US-9 无障碍与修饰器 (AC-9.1~9.2) | 代码审查 | HasRange；RatingConfiguration |

### 逐 AC 验证用例

| AC编号 | 验证类型 | 位置/用例 |
|-------|----------|-----------|
| AC-1.1 | 代码审查 | `frameworks/core/components_ng/pattern/rating/rating_model_ng.cpp:61-72` |
| AC-1.2 | 代码审查 | `frameworks/core/components_ng/pattern/rating/rating_model_ng.cpp:105-121` |
| AC-1.3 | 代码审查 | `frameworks/core/components_ng/pattern/rating/rating_pattern.cpp:303-341` |
| AC-1.4 | 代码审查 | `frameworks/core/components_ng/pattern/rating/rating_pattern.cpp:303-341` |
| AC-2.1 | 代码审查 | `frameworks/core/components_ng/pattern/rating/rating_model_ng.cpp:123-126` |
| AC-2.2 | 代码审查 | `frameworks/core/components_ng/pattern/rating/rating_pattern.cpp:303-341` |
| AC-2.3 | 代码审查 | `frameworks/core/components_ng/pattern/rating/rating_layout_property.h:59` |
| AC-3.1 | 代码审查 | `frameworks/core/components_ng/pattern/rating/rating_model_ng.cpp:128-131` |
| AC-3.2 | 代码审查 | `frameworks/core/components_ng/pattern/rating/rating_pattern.cpp:303-341` |
| AC-3.3 | 代码审查 | `frameworks/core/components_ng/pattern/rating/rating_pattern.cpp:303-341` |
| AC-3.4 | 代码审查 | `frameworks/core/components_ng/pattern/rating/rating_pattern.cpp:303-341` |
| AC-4.1 | 代码审查 | `frameworks/core/components_ng/pattern/rating/rating_model_ng.cpp:133-185` |
| AC-4.2 | 代码审查 | `frameworks/core/components_ng/pattern/rating/rating_pattern.cpp:967-1001` |
| AC-4.3 | 代码审查 | `frameworks/core/components_ng/pattern/rating/rating_pattern.cpp:967-1001` |
| AC-5.1 | 代码审查 | `frameworks/core/components_ng/pattern/rating/rating_event_hub.h:39-47` |
| AC-5.2 | 代码审查 | `frameworks/core/components_ng/pattern/rating/rating_pattern.cpp:343-393` |
| AC-6.1 | 代码审查 | `frameworks/core/components_ng/pattern/rating/rating_layout_algorithm.cpp:22-78` |
| AC-6.2 | 代码审查 | `frameworks/core/components_ng/pattern/rating/rating_layout_algorithm.cpp:22-78` |
| AC-6.3 | 代码审查 | `frameworks/core/components_ng/pattern/rating/rating_pattern.cpp:82-87` |
| AC-7.1 | 代码审查 | `frameworks/core/components_ng/pattern/rating/rating_pattern.cpp:343-393` |
| AC-7.2 | 代码审查 | `frameworks/core/components_ng/pattern/rating/rating_pattern.cpp:343-393` |
| AC-8.1 | 代码审查 | `frameworks/core/components_ng/pattern/rating/rating_pattern.cpp:642-679` |
| AC-8.2 | 代码审查 | `frameworks/core/components_ng/pattern/rating/rating_pattern.cpp:642-679` |
| AC-8.3 | 代码审查 | `frameworks/core/components_ng/pattern/rating/rating_pattern.cpp:642-679` |
| AC-8.4 | 代码审查 | `frameworks/core/components_ng/pattern/rating/rating_pattern.cpp:642-679` |
| AC-9.1 | 代码审查 | `frameworks/core/components_ng/pattern/rating/rating_accessibility_property.cpp:31-34` |
| AC-9.2 | 代码审查 | `frameworks/core/components_ng/pattern/rating/rating_modifier.h:37`, `rating_paint_method.h:43-68` |

---

## API 变更分析

### 新增 API

> SDK 定义来源: `interface/sdk-js/api/@internal/component/ets/rating.d.ts`

#### 组件构造（RatingInterface）

```typescript
// rating.d.ts
interface RatingOptions {
  rating: number;
  indicator?: boolean;
}
interface RatingInterface {
  (options?: RatingOptions): RatingAttribute;
}
declare const Rating: RatingInterface;
```

- **@since**: API 7（基础）、API 9（@form）、API 10（@crossplatform）、API 11（@atomicservice）、API 18（Optional 重载）

#### RatingAttribute 属性方法

| 方法签名 | 返回类型 | 说明 | @since |
|----------|----------|------|--------|
| `stars(value: number)` | RatingAttribute | 设置星星数量，默认 5 | API 7 / API 18(Optional) |
| `stepSize(value: number)` | RatingAttribute | 设置步长，默认 0.5 | API 7 / API 18(Optional) |
| `starStyle(value: StarStyleOptions)` | RatingAttribute | 设置星星样式图片 | API 7 / API 20(ResourceStr) |
| `onChange(handler: OnRatingChangeCallback)` | RatingAttribute | 评分变化回调 | API 7 |
| `contentModifier(modifier: ContentModifier<RatingConfiguration>)` | RatingAttribute | 内容修饰器 | API 12 |

#### 关联类型

| 类型 | 定义 | 用途 |
|------|------|------|
| `StarStyleOptions` | `{backgroundUri, foregroundUri, secondaryUri?}` | 星星样式图片源 |
| `RatingConfiguration` | `{rating, indicator, stars, stepSize, triggerChange}` | contentModifier 上下文 |
| `OnRatingChangeCallback` | `(value: number) => void` | onChange 回调签名 |

---

### 变更/废弃 API

| API 名称 | 变更类型 | 关联 AC |
|----------|----------|---------|
| `Rating(rating: number, indicator?: boolean)` | 变更(API 18 Optional 重载) | AC-1.1 |
| `starStyle(value: string)` | 变更(API 20 ResourceStr) | AC-4.1 |
| `rating.static.d.ets` | 新增(API 23 静态版本) | — |

## 接口规格

### 接口定义

> 本特性为已有实现补录，接口行为定义详见上方规则定义和用户故事。

无新增接口规格。

---

## 兼容性声明

| API 版本 | 行为差异 | 影响 | 迁移指导 |
|----------|----------|------|----------|
| API 7 | starStyle 参数为 string 类型 | 仅支持 URI 字符串 | API 20 起支持 ResourceStr |
| API < 18 | Rating 构造参数为必填 `Rating(rating, indicator?)` | 必须传入 rating | API 18 起参数 Optional，可不传 |
| API 12+ | 新增 contentModifier | 可自定义渲染 | 不影响已有使用 |
| API 20 | starStyle 参数类型从 string 改为 ResourceStr | 兼容 string，新增 Resource | 旧代码无需修改 |
| API 23 | 新增静态版本 rating.static.d.ets | 静态编译支持 | 动态版本不受影响 |

---

## 架构约束

| 约束 | 描述 |
|------|------|
| 属性分层 | 布局属性（Indicator/Stars/图片来源）存入 RatingLayoutProperty；渲染属性（RatingScore/StepSize/TouchStar）存入 RatingRenderProperty |
| 脏标记 | 布局属性变更触发 PROPERTY_UPDATE_MEASURE；渲染属性变更触发 PROPERTY_UPDATE_RENDER |
| 焦点模式 | 非指示器模式 FocusType::NODE；指示器模式 FocusType::DISABLE |
| 评分约束 | ConstrainsRatingScore 在每次评分变更时执行约束检查 |
| 图片加载 | OnModifyDone 中加载前景/次级/背景图片，成功码 RATING_IMAGE_SUCCESS_CODE=0b111 |

---

## 非功能性需求

| 维度 | 要求 |
|------|------|
| 性能 | ConstrainsRatingScore 和 RecalculatedRatingScoreBasedOnEventPoint 开销应保持 O(1) |
| 可调试性 | 提供 DumpInfo（ratingScore/stars/stepSize）用于 Inspector 诊断 |
| 无障碍 | HasRange=true，IsEditable=!indicator，支持辅助技术读取评分范围 |

---

## 多设备适配声明

| 设备类型 | 行为差异 | 规格/约束 | 验证方式 | 证据 |
|----------|----------|-----------|----------|------|
| 手机 | 无差异 | — | — | — |
| 平板 | 无差异 | — | — | — |
| 折叠屏 | 无差异 | — | — | — |

---

## 全局特性影响

| 影响维度 | 说明 |
|----------|------|
| 无障碍 | 是 — HasRange=true，GetAccessibilityValue 暴露 max=stars/current=ratingScore/min=0；IsEditable=!indicator；支持键盘导航 |
| 大字体 | 需关注 — 指示器 12vp 和非指示器 28vp 为固定尺寸，大字体场景需开发者显式设置尺寸 |
| 深色模式 | 需关注 — 图片来源需适配深色模式资源；主题默认图片通过 rating_theme.h 资源 ID 加载 |
| 多窗口分屏 | 无差异 |
| 多用户 | 无差异 |
| 版本升级 | 需关注 — API 7→18→20→23 有参数 Optional 重载、starStyle 类型变更和静态版本 |
| 生态兼容 | 需关注 — contentModifier (API 12+) 为自定义渲染提供生态扩展点 |

---

## Spec 自审清单

- [x] 所有 US 以 "作为/我想要/以便" 格式描述
- [x] 所有 AC 编号格式正确（AC-X.Y），且在验收追溯中引用
- [x] 验证映射覆盖全部 AC，每个 AC 至少有一种验证手段
- [x] 规则编号连续且可追溯到源码
- [x] API 变更分析基于真实 SDK 定义文件（rating.d.ts）
- [x] 兼容性声明标注 API 版本差异
- [x] 所有源码引用包含 file:line 信息
- [x] 构建系统影响章节已确认无变更

---

## context-references

### 源码文件

| 文件 | 说明 |
|------|------|
| `frameworks/core/components_ng/pattern/rating/rating_pattern.cpp/.h` | Pattern 层，评分约束、事件计算、键盘处理 |
| `frameworks/core/components_ng/pattern/rating/rating_layout_property.h` | 布局属性定义（Indicator/Stars/图片来源） |
| `frameworks/core/components_ng/pattern/rating/rating_render_property.h` | 渲染属性定义（RatingScore/StepSize/TouchStar） |
| `frameworks/core/components_ng/pattern/rating/rating_layout_algorithm.cpp` | 尺寸计算 MeasureContent |
| `frameworks/core/components_ng/pattern/rating/rating_model_ng.cpp/.h` | NG Model 层 |
| `frameworks/core/components_ng/pattern/rating/rating_modifier.h` | ContentModifier 渲染 |
| `frameworks/core/components_ng/pattern/rating/rating_event_hub.h` | 事件 Hub（ChangeEvent/FireChangeEvent） |
| `frameworks/core/components_ng/pattern/rating/rating_accessibility_property.cpp/.h` | 无障碍属性 |
| `frameworks/bridge/declarative_frontend/ark_component/src/ArkRating.ts` | ArkTS 组件定义 |
| `frameworks/core/components_ng/pattern/rating/rating_ops_accessor.cpp` | C-API 回调注册 |
| `interface/sdk-js/api/@internal/component/ets/rating.d.ts` | SDK 公开 API 定义 |

### 测试文件

| 文件 | 说明 |
|------|------|
| `test/unittest/core/pattern/rating/rating_test_ng.cpp` | NG 单元测试 |

### SDK 文档

| 文件 | 说明 |
|------|------|
| `docs/sdk/ArkUI_SDK_API_Knowledge_Base.md` | SDK API 知识库 |
| `docs/sdk/Component_API_Knowledge_Base_CN.md` | 组件 API 知识库 |
