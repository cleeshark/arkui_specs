# 特性规格

## 概述

| 字段 | 内容 |
|---|---|
| 特性名称 | 滚动条与内容视效 |
| 特性编号 | Func-05-03-01-Feat-01 |
| 所属 Epic | 滚动公共能力长期规格补录 |
| 优先级 | P1 |
| 目标版本 | API 11-26 已有能力补录 |
| SIG 归属 | ArkUI SIG |
| 状态 | Baselined |
| 复杂度 | 复杂 |

本特性规定 `List`、`Grid`、`Scroll`、`WaterFlow` 共享的滚动条显示、颜色、宽高、边距、自动边距避让、边缘渐隐和内容裁剪行为。规格以当前 SDK 契约和 ace_engine 实现为准，不改变现有公开接口或运行时语义。

## 本次变更范围（Delta）

| 类型 | 内容 | 说明 |
|---|---|---|
| ADDED | 滚动条显示与样式长期规格 | 补录 `scrollBar`、`scrollBarColor`、`scrollBarWidth`、`scrollBarHeight` 的版本、默认值和重置语义 |
| ADDED | 滚动条边距长期规格 | 补录 `scrollBarMargin`、`autoAdjustScrollBarMargin` 的优先级、RTL、反向布局和避让计算 |
| ADDED | 内容视效长期规格 | 补录 `fadingEdge`、`clipContent` 对绘制、布局、虚拟化和安全区的影响 |
| ADDED | ArkTS 与 C API 兼容性风险 | 记录动态/静态 API 差异、C API 支持矩阵和当前实现偏差 |

## 输入文档

- SDK 动态接口：`/home/leslie/repo/interface_sdk-js/api/@internal/component/ets/common.d.ts:28878-29404`
- SDK 静态接口：`/home/leslie/repo/interface_sdk-js/api/arkui/component/common.static.d.ets:15251-15614`
- NG 公共模型：`frameworks/core/components_ng/pattern/scrollable/scrollable_model_ng.cpp:49-157,354-368,460-508,641-669,852-877`
- NG 公共属性与 Pattern：`frameworks/core/components_ng/pattern/scrollable/scrollable_paint_property.h:73-120`、`frameworks/core/components_ng/pattern/scrollable/scrollable_pattern.cpp:1486-1557`
- Native Node 接口：`interfaces/native/native_node.h:7364-7399,7588-7601,7656-7668,7686-7700,7769-7797`
- 设计文档：`05-ui-components/03-scroll-container-components/01-scroll-common-capability/design.md`

## 用户故事

### US-1: 配置滚动条显示与样式

作为 ArkUI 应用开发者，我希望统一配置滚动容器的滚动条状态、颜色和尺寸，以便在不同滚动组件中获得可预期的视觉结果。

| AC编号 | 验收标准 | 类型 |
|---|---|---|
| AC-1.1 | WHEN 对支持组件设置 `BarState.Off/Auto/On` THEN 滚动条分别不显示、按需显示后消失、持续显示 | 正常 |
| AC-1.2 | WHEN 未显式设置滚动条状态 THEN `Scroll` 使用 `AUTO`、`WaterFlow` 使用 `OFF`，`List/Grid` 按 API 版本采用实现默认值 | 边界 |
| AC-1.3 | WHEN 设置合法颜色值或 Resource THEN 滚动条使用解析后的颜色；WHEN 重置或静态接口传入 `undefined` THEN 恢复主题前景色 | 正常 |
| AC-1.4 | WHEN 宽度或高度等于 `0` THEN 对应滚动条不可见；WHEN值小于 `0` THEN 按调用通道执行默认值恢复或参数错误语义 | 边界 |
| AC-1.5 | WHEN Scroll 使用 `Axis::FREE` THEN 使用 ScrollBar2D，应用 mode、width、color、margin，但不承诺应用 height 和自动边距避让 | 边界 |

### US-2: 配置滚动条边距与自动避让

作为 ArkUI 应用开发者，我希望滚动条避开内容偏移、内边距、安全区和边框，同时允许显式边距覆盖自动计算，以便滚动条不遮挡关键内容。

| AC编号 | 验收标准 | 类型 |
|---|---|---|
| AC-2.1 | WHEN 设置非负 start/end margin THEN 滚动条按主轴首尾应用边距；WHEN C API 输入负值 THEN 对应边距归零 | 正常 |
| AC-2.2 | WHEN 启用自动边距且未显式设置 `scrollBarMargin` THEN 避让值累加 contentStart/EndOffset、padding、safeAreaPadding 和 border | 正常 |
| AC-2.3 | WHEN 同时启用自动边距并显式设置 `scrollBarMargin`，包括 `{0,0}` THEN 显式值优先，自动避让不生效 | 边界 |
| AC-2.4 | WHEN 主轴反向 THEN 自动避让首尾值交换；WHEN 水平布局处于 RTL 且使用 localized start/end THEN 左右映射交换 | 边界 |
| AC-2.5 | WHEN `autoAdjustScrollBarMargin` 为 `undefined` 或重置 THEN 内部状态恢复为 `false` | 恢复 |

### US-3: 配置边缘渐隐

作为 ArkUI 应用开发者，我希望滚动内容边缘显示可配置长度的渐隐效果，以便提示内容仍可继续滚动。

| AC编号 | 验收标准 | 类型 |
|---|---|---|
| AC-3.1 | WHEN `fadingEdge(true)` 且未提供长度 THEN 使用 `32vp` 默认长度 | 正常 |
| AC-3.2 | WHEN `fadingEdge(false)` THEN 不绘制边缘渐隐 | 正常 |
| AC-3.3 | WHEN渐隐长度超过可视主轴尺寸的 50% THEN 渲染长度限制为主轴尺寸的 50% | 边界 |
| AC-3.4 | WHEN负长度从不同前端桥接进入 THEN 保留当前桥接差异：旧 JS 路径回退 `32vp`，ArkTS Native 路径可继续向下传递 | 异常 |

### US-4: 配置内容裁剪区域

作为 ArkUI 应用开发者，我希望选择内容区域、组件边界、安全区或自定义矩形作为裁剪范围，以便控制绘制与虚拟化边界。

| AC编号 | 验收标准 | 类型 |
|---|---|---|
| AC-4.1 | WHEN 设置 `CONTENT_ONLY` THEN 裁剪到内容区域；WHEN 设置 `BOUNDARY` THEN 裁剪到包含 padding 的组件边界 | 正常 |
| AC-4.2 | WHEN 设置 `SAFE_AREA` THEN 绘制侧使用累积系统安全区扩展裁剪区域，布局侧在 List/Grid/WaterFlow 中同步安全区并触发后续布局 | 正常 |
| AC-4.3 | WHEN设置 `RectShape` THEN ArkTS/generated Modifier 使用自定义矩形裁剪；Public NativeNode C 属性仅支持枚举模式 | 正常 |
| AC-4.4 | WHEN重置 `clipContent` THEN `Scroll/Grid` 恢复 `BOUNDARY`，`List/WaterFlow` 恢复 `CONTENT_ONLY` | 恢复 |
| AC-4.5 | WHEN List/Grid/WaterFlow 的裁剪范围扩展 THEN 布局算法可测量裁剪区域内额外 Item，并维持缓存与可见索引一致 | 边界 |
| AC-4.6 | WHEN Public NativeNode C API 输入大于已定义范围的裁剪枚举 THEN 当前实现可能接受并继续下传，规格将其记录为兼容风险 | 异常 |

## 验收追溯

| AC | 关联规则 | 关联 Task | 验证方式 | 证据 |
|---|---|---|---|---|
| AC-1.1-AC-1.5 | R-1-R-6 | TASK-SKELETON-1 | Host 单测、C API 单测、源码审查 | `scrollable_model_ng.cpp:49-157`；`scroll_bar_2d.cpp:142-202` |
| AC-2.1-AC-2.5 | R-7-R-11 | TASK-SKELETON-1 | Host 单测、属性读回、RTL/reverse 场景 | `scrollable_pattern.cpp:1486-1557`；`style_modifier.cpp:8115-8131` |
| AC-3.1-AC-3.4 | R-12-R-15 | TASK-SKELETON-1 | Host 绘制单测、桥接参数单测 | `scrollable_model_ng.cpp:354-368`；`style_modifier.cpp:7878-7894` |
| AC-4.1-AC-4.6 | R-16-R-21 | TASK-SKELETON-1 | Host 布局单测、C API 单测、源码审查 | `scrollable_model_ng.cpp:460-508`；`scrollable_paint_method.cpp:129-142` |

## 规则定义

| 规则ID | 类型 | 触发条件 | 预期行为 | 边界/约束 | 关联AC |
|---|---|---|---|---|---|
| R-1 | 行为 | mode 为 Off/Auto/On | 分别不显示、按需显示、持续显示 | Auto 消失时序由滚动条任务控制 | AC-1.1 |
| R-2 | 边界 | 未设置 mode | 使用组件默认模式 | WaterFlow 为 OFF；其他组件存在版本差异 | AC-1.2 |
| R-3 | 行为 | 颜色解析成功 | 保存显式颜色并更新滚动条前景色 | Resource 在配置更新时重新解析 | AC-1.3 |
| R-4 | 恢复 | 颜色重置或静态 undefined | 清除显式属性并恢复主题前景色 | 深浅色更新时未显式颜色跟随主题 | AC-1.3 |
| R-5 | 边界 | width/height = 0 | 滚动条不可见 | `<0` 的 ArkTS 与 C API 行为分别记录 | AC-1.4 |
| R-6 | 边界 | Scroll 轴为 FREE | 创建双轴滚动条并移除单轴滚动条 | 不应用 height/autoAdjust，默认 margin 为 8vp | AC-1.5 |
| R-7 | 行为 | start/end margin >= 0 | 保存并应用主轴首尾边距 | Public C API 单位为 vp | AC-2.1 |
| R-8 | 异常 | Public C API margin < 0 | 该项归零且调用返回成功 | 与 width/height 的错误码策略不同 | AC-2.1 |
| R-9 | 行为 | autoAdjust=true 且无显式 margin | 累加 content offset、padding、safe area padding、border | 计算值在布局方向映射后应用 | AC-2.2 |
| R-10 | 边界 | paint property 中存在显式 margin | 不采用自动避让值 | `{0,0}` 仍视为显式设置 | AC-2.3 |
| R-11 | 恢复 | autoAdjust undefined/reset | 恢复 false | reset 标记 measure 更新 | AC-2.4, AC-2.5 |
| R-12 | 行为 | fadingEdge=true 且无长度 | 保存 true 和 32vp | 默认长度来自公共常量 | AC-3.1 |
| R-13 | 行为 | fadingEdge=false | 禁止渐隐绘制 | 已存长度不产生可见渐隐 | AC-3.2 |
| R-14 | 边界 | length > 主轴尺寸的 50% | 渲染采用主轴尺寸的 50% | 只限制上界 | AC-3.3 |
| R-15 | 异常 | length < 0 | 保留调用桥接的当前差异 | 不将未统一行为虚构为单一规则 | AC-3.4 |
| R-16 | 行为 | clip=CONTENT_ONLY/BOUNDARY | 使用对应内容区域或组件边界 | 默认值由组件决定 | AC-4.1 |
| R-17 | 行为 | clip=SAFE_AREA | 累积系统安全区并同步布局侧裁剪数据 | List/Grid/WaterFlow 可触发二次布局 | AC-4.2 |
| R-18 | 行为 | clip=RectShape | 使用自定义矩形 | Public NativeNode C 属性不开放 RectShape | AC-4.3 |
| R-19 | 恢复 | clip reset/静态 undefined | 恢复组件默认裁剪模式 | Scroll/Grid=BOUNDARY；List/WaterFlow=CONTENT_ONLY | AC-4.4 |
| R-20 | 边界 | 裁剪范围超出基础视口 | 布局算法扩展测量或缓存范围 | 不得改变 Item 索引顺序 | AC-4.5 |
| R-21 | 异常 | C clip 枚举 > 2 | 当前路径可能将原值下传 | 记录风险，不修改实现 | AC-4.6 |

## 验证映射

| 编号 | 对应规格项 | 验证方式 | 验证重点 |
|---|---|---|---|
| VM-1 | AC-1.1-AC-1.5 | `scrollable_cover_test_ng`、generated modifier test、属性读回 | 四组件默认值、宽高零值、ScrollBar2D 差异 |
| VM-2 | AC-2.1-AC-2.5 | `scroll_inner_layout_test_ng`、NativeNode margin test | 显式 margin 优先级、RTL、reverse、避让累加 |
| VM-3 | AC-3.1-AC-3.4 | `scrollable_test_ng`、`scrollable_cover_test_ng`、桥接源码审查 | 32vp 默认值、50% 上限、负长度差异 |
| VM-4 | AC-4.1-AC-4.6 | `scrollable_pattern_test_ng`、WaterFlow/Grid/List 布局测试、C API clip test | 默认模式、安全区二次布局、虚拟化范围、非法枚举风险 |

## API 变更分析

### 新增 API

本次为已有能力补录，不新增接口。以下为纳入长期规格的现有公开面。

| API 名称 | 开放范围 | 入参概要 | 返回值 | 错误码范围 | 功能描述 | 关联 AC |
|---|---|---|---|---|---|---|
| ArkTS `scrollBar/Color/Width/Height` | Public | BarState、颜色、长度及 Resource/undefined 变体 | 组件属性链 | N/A | 配置滚动条显示和样式 | AC-1.1-AC-1.5 |
| ArkTS `scrollBarMargin/autoAdjustScrollBarMargin` | Public | ScrollBarMargin、boolean/undefined | 组件属性链 | N/A | 配置显式或自动边距 | AC-2.1-AC-2.5 |
| ArkTS `fadingEdge` | Public | Optional<boolean>、FadingEdgeOptions | 组件属性链 | N/A | 配置边缘渐隐 | AC-3.1-AC-3.4 |
| ArkTS `clipContent` | Public | ContentClipMode 或 RectShape | 组件属性链 | N/A | 配置内容裁剪 | AC-4.1-AC-4.6 |
| NativeNode `NODE_SCROLL_BAR_*` | Public C API | ArkUI_AttributeItem | 0/401/106102 | 0、401、106102 | 设置、读取和重置公共滚动属性 | AC-1.1-AC-2.5 |
| NativeNode `NODE_SCROLL_FADING_EDGE/NODE_SCROLL_CLIP_CONTENT` | Public C API | bool/length 或枚举 | 0/401/106102 | 0、401、106102 | 设置、读取和重置公共内容视效 | AC-3.1-AC-4.6 |

### 变更/废弃 API

| API 名称 | 变更类型 | 影响场景 | 迁移指引 | 关联 AC |
|---|---|---|---|---|
| `scrollBarColor` | 历史签名扩展 | API 22 动态接口增加 Resource；静态 API 23 初始即支持 Resource | 按目标 API 使用对应签名 | AC-1.3 |
| `scrollBarWidth` | 历史签名扩展 | API 26 增加 Resource，且新版文档明确 `<0` 与 `0` 的区别 | 对零值隐藏行为进行显式验证 | AC-1.4 |
| `scrollBarMargin` | 历史范式扩展 | 动态 API 20、静态 API 26 | 静态 undefined 恢复 0/0 | AC-2.1, AC-2.5 |
| `scrollBarHeight/autoAdjustScrollBarMargin` | 历史新增 | API 26 | 低版本不得假定接口存在 | AC-1.4, AC-2.5 |
| 废弃 API | 废弃 | 无 | 无迁移要求 | AC-1.1 |

## 接口规格

### 接口定义

**ArkTS 滚动条显示与样式**

| 属性 | 值 |
|---|---|
| 函数签名 | `scrollBar(BarState)`；`scrollBarColor(Color|number|string|Resource)`；`scrollBarWidth(number|string|Resource)`；`scrollBarHeight(LengthMetrics|undefined)` |
| 返回值 | 当前组件属性对象 |
| 开放范围 | Public |
| 错误码 | N/A |
| 关联 AC | AC-1.1-AC-1.5 |

**参数约束**

| 参数 | 类型 | 必填 | 默认值 | 约束条件 |
|---|---|---|---|---|
| barState | BarState | 是 | 组件相关 | Off/Auto/On |
| color | Color/number/string/Resource | 是 | 主题滚动条前景色 | Resource 支持受 API 版本约束 |
| width | number/string/Resource | 是 | 4vp | 0 隐藏；负值按通道恢复或报错 |
| height | LengthMetrics/undefined | 是 | 自适应 | 0 隐藏；负值或 undefined 恢复默认 |

**ArkTS 边距与内容视效**

| 属性 | 值 |
|---|---|
| 函数签名 | `scrollBarMargin(ScrollBarMargin)`；`autoAdjustScrollBarMargin(boolean|undefined)`；`fadingEdge(Optional<boolean>, FadingEdgeOptions?)`；`clipContent(ContentClipMode|RectShape)` |
| 返回值 | 当前组件属性对象 |
| 开放范围 | Public |
| 错误码 | N/A |
| 关联 AC | AC-2.1-AC-4.6 |

**参数约束**

| 参数 | 类型 | 必填 | 默认值 | 约束条件 |
|---|---|---|---|---|
| margin | ScrollBarMargin | 是 | start/end 为 0 | 显式设置优先于自动避让 |
| enable | boolean/undefined | 是 | false | undefined 恢复 false |
| fadingEdgeLength | LengthMetrics | 否 | 32vp | 渲染上限为主轴尺寸 50%；负值存在桥接差异 |
| clip | ContentClipMode/RectShape | 是 | 组件相关 | Public C API 仅支持 0..2 枚举 |

## 兼容性声明

- **已有 API 行为变更:** 否。本次记录 API 11-26 的历史演进和现有差异，不修改行为。
- **配置文件格式变更:** 否。
- **数据存储格式变更:** 否。
- **最低支持版本:** 基础滚动条 API 为 API 11；`fadingEdge/clipContent` 为 API 14；margin 为 API 20；height/auto-adjust 为 API 26。
- **API 版本号策略:** 采用方法级 `@since`，动态与静态 API 分别列示；不使用类级版本覆盖方法级版本。
- **组件差异:** List、Grid、Scroll、WaterFlow 的默认 mode、默认 clip、width reset 和二维滚动支持存在差异。
- **契约风险:** SDK width=0 描述、C auto-adjust 布尔说明、非法 clip 枚举和负 fading length 存在当前契约偏差。

## 架构约束

| 关键约束 | 约束说明 | 影响 AC |
|---|---|---|
| 分层存储 | 公共视效存入 ScrollablePaintProperty；clip 同步 ScrollableLayoutProperty | AC-3.1-AC-4.6 |
| 组件默认值 | 默认 mode 和 clip 由具体 Pattern/PaintProperty 决定 | AC-1.2, AC-4.4 |
| 显式优先 | paint property 中存在显式 margin 时禁止自动避让覆盖 | AC-2.2, AC-2.3 |
| 安全区输入 | SAFE_AREA 必须考虑祖先和系统安全区以及后续布局 | AC-4.2 |
| 实现即规格 | 对当前桥接和 C API 偏差只记录风险，不在文档任务中修改实现 | AC-3.4, AC-4.6 |

## 非功能性需求

| 类型 | 指标/阈值 | 验证方式 | 证据 |
|---|---|---|---|
| 性能 | 属性更新不得引入持续额外布局；仅 clip/safe-area 需要的组件触发测量 | Host 布局测试和 dirty flag 审查 | `scrollable_paint_property.h:73-84` |
| 功耗 | 无新增后台任务 | 源码审查 | 本次仅补录规格 |
| 内存 | 不新增持久对象；沿用 Paint/Layout Property | 源码审查 | `scrollable_paint_property.h:73-84` |
| 安全 | 不处理敏感数据 | 接口审查 | SDK 参数均为 UI 属性 |
| 可靠性 | reset 后恢复组件或主题默认值 | Host 单测、属性读回 | `scrollable_model_ng.cpp:54-155,500-508` |
| 可测试性 | 每个 AC 至少映射一个 Host 或 C API 验证手段 | VM-1 至 VM-4 | 本文验证映射 |
| 自动化维测 | 沿用 Inspector/属性读回和现有直方图 | 源码审查 | `scrollable_model_ng.cpp:354-364,460-491` |
| 定界定位 | 组件默认差异和通道差异必须在失败日志中区分 | 测试用例命名与断言 | 现有组件参数化测试 |

## 多设备适配声明

| 设备类型 | 行为差异 | 规格/约束 | 验证方式 | 证据 |
|---|---|---|---|---|
| 手机 | 支持全部公共能力 | 按 API 版本和组件矩阵执行 | Host 单测 | 公共 NG 实现 |
| 平板 | 与手机一致，多窗口尺寸变化会重新计算 50% 渐隐上限和裁剪范围 | 使用实时视口尺寸 | 尺寸变化测试 | `scrollable_pattern.cpp:291-307` |
| 折叠屏 | 折叠状态导致安全区和视口变化时重新计算裁剪与边距 | SAFE_AREA 使用最新系统输入 | 安全区/窗口变化测试 | `scrollable_paint_method.cpp:129-142` |
| 穿戴设备 | 数值单位按设备密度转换；本 Feat 不规定数字表冠交互 | 不扩展到 Feat-02 交互能力 | 单位转换测试 | Dimension/LengthMetrics 转换链 |

## 全局特性影响

| 特性 | 适用？ | 结论 | 关联场景 |
|---|---|---|---|
| 无障碍 | 是 | 滚动条隐藏不改变滚动容器的可访问性动作 | AC-1.1, AC-1.4 |
| 大字体 | 否 | 本能力不读取字体缩放 |
| 深色模式 | 是 | 未显式设置颜色时跟随 ScrollBarTheme，显式颜色保持 | AC-1.3 |
| 多窗口/分屏 | 是 | 视口变化影响渐隐上限、裁剪范围和二维滚动条 | AC-1.5, AC-3.3, AC-4.5 |
| 多用户 | 否 | 无用户数据或持久状态 |
| 版本升级 | 是 | API 11-26 的签名与默认值差异需保持 | AC-1.2-AC-2.5 |
| 生态兼容 | 是 | ArkTS 动态/静态、Public C API 和 generated Modifier 能力不完全对称 | AC-3.4, AC-4.3, AC-4.6 |

## 行为场景（可选，Gherkin）

```gherkin
Feature: 滚动条与内容视效
  作为 ArkUI 应用开发者
  我想要配置滚动条、边距、渐隐和裁剪
  以便在不同滚动容器和 API 版本中获得可预测行为

  Scenario: 显式零边距覆盖自动避让
    Given Scrollable 组件启用了 autoAdjustScrollBarMargin
    And 组件存在 padding、safeAreaPadding 和 contentStartOffset
    When 开发者显式设置 scrollBarMargin 为 start=0 且 end=0
    Then 滚动条使用 0/0 边距
    And 不叠加自动计算的避让距离

  Scenario Outline: 重置内容裁剪
    Given 组件类型为 <component>
    When 重置 clipContent
    Then 裁剪模式恢复为 <mode>

    Examples:
      | component | mode |
      | Scroll | BOUNDARY |
      | Grid | BOUNDARY |
      | List | CONTENT_ONLY |
      | WaterFlow | CONTENT_ONLY |

  Scenario: SAFE_AREA 触发多阶段更新
    Given 祖先节点或系统窗口提供安全区
    When 组件设置 clipContent 为 SAFE_AREA
    Then 绘制裁剪区域包含累积系统安全区
    And List、Grid 或 WaterFlow 在安全区数据同步后执行后续布局
```

## Spec 自审清单

- [x] 无占位符文本
- [x] 所有 AC 使用 WHEN/THEN 格式，可独立测试
- [x] 范围边界明确，未包含滚动物理、嵌套滚动和事件生命周期
- [x] 无语义模糊表述
- [x] AC 与规则表交叉一致
- [x] 每条规则满足可复现、可观测、边界值、关联 AC 和无冲突要求

## context-references

```yaml
context-queries:
  - repo: "openharmony/arkui_ace_engine"
    query: "ScrollablePaintProperty scrollbar fadingEdge clipContent implementation defaults"
  - repo: "openharmony/arkui_ace_engine"
    query: "autoAdjustScrollBarMargin padding safeAreaPadding RTL reverse"
  - repo: "openharmony/interface_sdk-js"
    query: "ScrollableCommonMethod API 11-26 dynamic static signatures"
```

**关键文档：** `docs/pattern/scroll/Scroll_Knowledge_Base.md`、`interfaces/native/native_node.h`、`frameworks/core/components_ng/pattern/scrollable/`
