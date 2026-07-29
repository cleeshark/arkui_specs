# 特性规格

## 概述

| 字段 | 内容 |
|---|---|
| 特性名称 | 滚动交互与物理效果 |
| 特性编号 | Func-05-03-01-Feat-02 |
| 所属 Epic | 滚动公共能力长期规格补录 |
| 优先级 | P1 |
| 目标版本 | API 7-26 已有能力补录 |
| SIG 归属 | ArkUI SIG |
| 状态 | Baselined |
| 复杂度 | 复杂 |

本特性规定 `List`、`Grid`、`Scroll`、`WaterFlow` 共享的边缘效果、滚动手势开关、摩擦系数、惯性初速度上限、鼠标拖动、数字表冠灵敏度和状态栏回顶行为。规格覆盖 ArkTS 动态/静态、generated Modifier 与 Public NativeNode C API 的现有差异。

## 本次变更范围（Delta）

| 类型 | 内容 | 说明 |
|---|---|---|
| ADDED | 边缘效果长期规格 | 补录 EdgeEffect、alwaysEnabled、effectEdge 和短内容交互行为 |
| ADDED | 滚动物理长期规格 | 补录 friction 默认矩阵、flingSpeedLimit 单位和限速顺序 |
| ADDED | 输入设备长期规格 | 补录手势、鼠标拖动和数字表冠的优先级及生命周期 |
| ADDED | 状态栏回顶长期规格 | 补录 API 18 默认变化、触发守卫和 WaterFlow 算法差异 |

## 输入文档

- SDK 动态接口：`/home/leslie/repo/interface_sdk-js/api/@internal/component/ets/common.d.ts:29043-29117,29151-29163,29331-29388,29633-29717`
- SDK 静态接口：`/home/leslie/repo/interface_sdk-js/api/arkui/component/common.static.d.ets:15365-15425,15505-15601,15816-15854`
- 公共实现：`frameworks/core/components_ng/pattern/scrollable/scrollable_pattern.cpp:2011-2070,3268-3364`、`scrollable.cpp:140-209,319-473,851-885`
- Bridge 与 Model：`frameworks/bridge/declarative_frontend/engine/jsi/nativeModule/arkts_native_scrollable_bridge.cpp:76-109,398-423`、`frameworks/core/components_ng/pattern/scrollable/scrollable_model_ng.cpp:402-457,527-590`
- C API：`interfaces/native/node/style_modifier.cpp:7168-7219,7506-7649,7922-8077`
- 共享设计：`05-ui-components/03-scroll-container-components/01-scroll-common-capability/design.md`

## 用户故事

### US-1: 配置边缘效果

作为 ArkUI 应用开发者，我希望选择 Spring、Fade 或 None 并控制短内容和生效边缘，以便滚动容器在边界处呈现符合场景的反馈。

| AC编号 | 验收标准 | 类型 |
|---|---|---|
| AC-1.1 | WHEN 设置 EdgeEffect.Spring/Fade/None THEN 边界处分别执行弹性、淡出或无效果行为 | 正常 |
| AC-1.2 | WHEN 内容不足一屏且 alwaysEnabled=true THEN 组件仍允许手势滚动并执行边缘效果；WHEN false THEN 不因边缘效果开启滚动 | 边界 |
| AC-1.3 | WHEN effectEdge=START/END THEN 效果仅作用于指定边缘；WHEN内部值为 ALL THEN 两侧均生效 | 正常 |
| AC-1.4 | WHEN Scroll 使用 Axis::FREE THEN effectEdge 约束水平方向，垂直方向保持 ALL 处理 | 边界 |
| AC-1.5 | WHEN省略 options 或执行 reset THEN 按组件和调用通道采用当前默认值，不合并为单一默认 | 恢复 |

### US-2: 控制滚动交互与物理参数

作为 ArkUI 应用开发者，我希望关闭用户手势或配置摩擦系数和惯性上限，以便控制滚动输入和停止距离。

| AC编号 | 验收标准 | 类型 |
|---|---|---|
| AC-2.1 | WHEN enableScrollInteraction=false THEN普通手指/鼠标手势不驱动滚动，但 Scroller 控制接口仍可滚动 | 正常 |
| AC-2.2 | WHEN关联 ScrollBarProxy 将组件判定为 nested scroller THEN运行时允许强制启用 ScrollableEvent，即使属性值为 false | 边界 |
| AC-2.3 | WHEN friction>0 THEN使用该值计算惯性；WHEN值<=0、Resource 解析失败或重置 THEN使用目标 API、设备、主题和系统属性共同确定的默认值 | 边界 |
| AC-2.4 | WHEN非穿戴目标 API 分别为 10、11、12 THEN兼容默认值依次为 0.6、0.7、0.75；WHEN为穿戴设备 THEN默认值为 0.9 | 边界 |
| AC-2.5 | WHEN flingSpeedLimit>0 THEN以 vp/s 接收，按 density 转换为 px/s，并在速度缩放、触控板缩放和增益之后限制最终初速度 | 正常 |
| AC-2.6 | WHEN flingSpeedLimit<=0 或重置 THEN回退当前设备的全局最大速度 | 恢复 |

### US-3: 使用鼠标与数字表冠输入

作为支持多输入设备的应用开发者，我希望控制鼠标拖动和数字表冠灵敏度，以便在 PC 和穿戴设备上获得合适的滚动体验。

| AC编号 | 验收标准 | 类型 |
|---|---|---|
| AC-3.1 | WHEN enableScrollWithMouse=true THEN PanRecognizer 接受鼠标左键拖动；WHEN false/undefined/reset THEN不接受该鼠标拖动 | 正常 |
| AC-3.2 | WHEN List/Grid 注册 Item 拖拽回调 THEN组件强制关闭鼠标滚动，Item 拖拽优先 | 边界 |
| AC-3.3 | WHEN旧 JS 入口收到非 boolean 鼠标开关参数 THEN保持当前属性值，不执行 reset | 异常 |
| AC-3.4 | WHEN构建启用 SUPPORT_DIGITAL_CROWN 且组件获得焦点 THEN表冠 BEGIN/UPDATE/END 复用普通拖动链路；WHEN失焦 THEN取消表冠拖动 | 正常 |
| AC-3.5 | WHEN灵敏度为 LOW/MEDIUM/HIGH THEN表冠位移倍率分别为 0.8/1.0/1.2；WHEN未设置或非法 THEN使用 MEDIUM | 边界 |

### US-4: 使用状态栏回顶

作为移动设备应用开发者，我希望点击状态栏时将可见的垂直滚动容器返回顶部，以便快速回到内容起点。

| AC编号 | 验收标准 | 类型 |
|---|---|---|
| AC-4.1 | WHEN显式 backToTop=true 且状态栏点击守卫满足 THEN中断当前动画并滚动至顶部 | 正常 |
| AC-4.2 | WHEN reset 且组件为纵轴、target API>=18 THEN默认启用；WHEN横轴或 target API<18 THEN默认关闭 | 边界 |
| AC-4.3 | WHEN显式设置后组件轴向改变 THEN保持显式值；WHEN再次 reset THEN重新按当前轴向和 target API 计算默认值 | 恢复 |
| AC-4.4 | WHEN组件已在顶部，或应用/窗口/节点/任一祖先不可见或未激活 THEN状态栏点击不触发回顶 | 边界 |
| AC-4.5 | WHEN WaterFlow 使用 SLIDING_WINDOW 且回顶动画结束后仍需校准 THEN额外执行 ScrollToIndex(0) 收尾 | 正常 |

## 验收追溯

| AC | 关联规则 | 关联 Task | 验证方式 | 证据 |
|---|---|---|---|---|
| AC-1.1-AC-1.5 | R-1-R-6 | TASK-05-03-01-F2 | Host/C API 测试、源码审查 | `scrollable_pattern.cpp:1362-1365,3074-3084` |
| AC-2.1-AC-2.6 | R-7-R-13 | TASK-05-03-01-F2 | Host 物理测试、密度换算、Resource 路径 | `scrollable_pattern.cpp:2011-2070`；`scrollable.cpp:851-885` |
| AC-3.1-AC-3.5 | R-14-R-18 | TASK-05-03-01-F2 | 鼠标/拖拽/表冠 Host 测试 | `scrollable.cpp:196-209,319-473` |
| AC-4.1-AC-4.5 | R-19-R-23 | TASK-05-03-01-F2 | 状态栏点击与嵌套测试 | `scrollable_pattern.cpp:3268-3364` |

## 规则定义

| 规则ID | 类型 | 触发条件 | 预期行为 | 边界/约束 | 关联AC |
|---|---|---|---|---|---|
| R-1 | 行为 | effect=Spring/Fade/None | 执行弹性、淡出或无效果 | 默认 effect 按组件 | AC-1.1 |
| R-2 | 边界 | 内容未溢出且 alwaysEnabled=true | 允许交互并执行效果 | Scroll options 缺省值与其他组件不同 | AC-1.2 |
| R-3 | 边界 | 内容未溢出且 alwaysEnabled=false | 不因 edgeEffect 产生滚动 | List/Grid/WaterFlow 常用缺省 | AC-1.2 |
| R-4 | 行为 | effectEdge=START/END/ALL | 仅首端、仅尾端或两端生效 | Public 枚举仅声明 START/END，内部存在 ALL=3 | AC-1.3 |
| R-5 | 边界 | Axis::FREE | 水平使用 effectEdge，垂直按 ALL | Scroll 特例 | AC-1.4 |
| R-6 | 恢复 | options 省略、undefined 或 reset | 使用入口/组件当前默认 | Public C 与 generated Modifier 缺省 alwaysEnabled 不同 | AC-1.5 |
| R-7 | 行为 | enableScrollInteraction=false | 禁止普通手势，保留控制器调用 | 不等于组件不可滚动 | AC-2.1 |
| R-8 | 边界 | nested ScrollBarProxy 强制可滚动 | ScrollableEvent enabled=true | 属性值仍可为 false | AC-2.2 |
| R-9 | 行为 | friction>0 | 使用显式摩擦系数 | 惯性距离与 friction 成反比 | AC-2.3 |
| R-10 | 恢复 | friction<=0/undefined/reset/资源失败 | 使用版本、设备、主题和系统属性默认值 | 不固化单一常量 | AC-2.3 |
| R-11 | 边界 | 非穿戴 API10/11/12+ 或穿戴 | 采用 0.6/0.7/0.75 或 0.9 基线 | API13+ 可被主题/系统覆盖 | AC-2.4 |
| R-12 | 行为 | flingSpeedLimit>0 | vp/s 转 px/s 后限制最终速度 | 限速晚于其他速度修正 | AC-2.5 |
| R-13 | 恢复 | flingSpeedLimit<=0/reset | 使用 MAX_VELOCITY | 可穿戴/非穿戴全局上限不同 | AC-2.6 |
| R-14 | 行为 | mouse=true 且无 Item drag 冲突 | PanRecognizer 接受鼠标拖动 | 仅鼠标左键拖动 | AC-3.1 |
| R-15 | 边界 | List/Grid 存在 Item drag 回调 | 强制 mouse=false | Item drag 优先 | AC-3.2 |
| R-16 | 异常 | 旧 JS 鼠标参数非 boolean | 忽略调用并保持原值 | 不执行 reset | AC-3.3 |
| R-17 | 行为 | SUPPORT_DIGITAL_CROWN 且已聚焦 | 表冠事件进入拖动链路 | 失焦取消 | AC-3.4 |
| R-18 | 边界 | crown=LOW/MEDIUM/HIGH/非法 | 倍率 0.8/1.0/1.2/1.0 | 默认 MEDIUM | AC-3.5 |
| R-19 | 行为 | 状态栏点击且 backToTop=true | 停止动画并回到顶部 | 需满足完整可见激活守卫 | AC-4.1 |
| R-20 | 边界 | reset、纵轴且 target API>=18 | 默认 true | C 头仍描述默认 false，属于契约偏差 | AC-4.2 |
| R-21 | 边界 | reset、横轴或 target API<18 | 默认 false | 轴向和版本共同决定 | AC-4.2 |
| R-22 | 恢复 | 显式值后再次 reset | 重新按当前轴向/API 计算默认 | 显式值不会随轴自动变化 | AC-4.3 |
| R-23 | 行为 | WaterFlow SLIDING_WINDOW 回顶动画结束 | 必要时 ScrollToIndex(0) 校准 | 其他模式不使用该收尾 | AC-4.4, AC-4.5 |

## 验证映射

| 编号 | 对应规格项 | 验证方式 | 验证重点 |
|---|---|---|---|
| VM-1 | AC-1.1-AC-1.5 | edge effect Host 与 NativeNode C 测试 | 短内容、effectEdge、FREE 模式、通道默认差异 |
| VM-2 | AC-2.1-AC-2.4 | 四组件参数化测试、friction API 版本测试 | 交互例外、设备/API 默认矩阵 |
| VM-3 | AC-2.5-AC-2.6 | max fling Host 测试和 density 断言 | vp/s 转换、限速顺序、非正值恢复 |
| VM-4 | AC-3.1-AC-3.5 | 鼠标、Item drag、digital crown 测试 | 编译条件、焦点、灵敏度倍率 |
| VM-5 | AC-4.1-AC-4.5 | 状态栏点击、嵌套滚动、WaterFlow 模式测试 | API18 默认、祖先可见性、滑动窗口收尾 |

## API 变更分析

### 新增 API

本次不新增接口，以下为补录的现有公开能力。

| API 名称 | 开放范围 | 入参概要 | 返回值 | 错误码范围 | 功能描述 | 关联 AC |
|---|---|---|---|---|---|---|
| `edgeEffect` | Public | EdgeEffect、EdgeEffectOptions | 组件属性链 | N/A | 配置边缘效果、短内容和边缘方向 | AC-1.1-AC-1.5 |
| `enableScrollInteraction` | Public | boolean/静态 undefined | 组件属性链 | N/A | 控制普通滚动手势 | AC-2.1-AC-2.2 |
| `friction` | Public | number/Resource/静态 undefined | 组件属性链 | N/A | 配置惯性摩擦系数 | AC-2.3-AC-2.4 |
| `flingSpeedLimit` | Public | number/静态 undefined | 组件属性链 | N/A | 配置惯性初速度上限 | AC-2.5-AC-2.6 |
| `enableScrollWithMouse` | Public | boolean/undefined | 组件属性链 | N/A | 配置鼠标左键拖动 | AC-3.1-AC-3.3 |
| `digitalCrownSensitivity` | Public ArkTS / generated | CrownSensitivity/undefined | 组件属性链 | N/A | 配置表冠灵敏度 | AC-3.4-AC-3.5 |
| `backToTop` | Public | boolean/静态 undefined | 组件属性链 | N/A | 配置状态栏点击回顶 | AC-4.1-AC-4.5 |
| `NODE_SCROLL_*` 对应属性 | Public C API | ArkUI_AttributeItem | 0/401/106102 | 0、401、106102 | 设置、获取、重置交互物理属性 | 相关全部 AC |

### 变更/废弃 API

| API 名称 | 变更类型 | 影响场景 | 迁移指引 | 关联 AC |
|---|---|---|---|---|
| `edgeEffect` | 历史公共化 | Scroll/List API 7、Grid/四组件重声明 API 10、公共方法 API 11 | 采用组件实际公开历史 | AC-1.1 |
| `EdgeEffectOptions.effectEdge` | 历史扩展 | API 18 增加边缘方向 | 仅使用 START/END；内部 ALL 作为兼容值 | AC-1.3 |
| `digitalCrownSensitivity` | 历史新增 | API 18 动态、API 23 静态 | 仅在支持表冠构建中生效 | AC-3.4 |
| `backToTop` | 历史新增/默认变化 | API 15 声明，target API 18+ reset 默认变化 | 显式设置可消除默认歧义 | AC-4.2 |
| `enableScrollWithMouse` | 历史新增 | API 26 | 低版本不得假定存在 | AC-3.1 |

## 接口规格

### 接口定义

**边缘效果**

| 属性 | 值 |
|---|---|
| 函数签名 | `edgeEffect(edgeEffect: EdgeEffect, options?: EdgeEffectOptions): T` |
| 返回值 | 当前组件属性对象 |
| 开放范围 | Public |
| 错误码 | ArkTS N/A；Public C API 为 0/401/106102 |
| 关联 AC | AC-1.1-AC-1.5 |

**参数约束**

| 参数 | 类型 | 必填 | 默认值 | 约束条件 |
|---|---|---|---|---|
| edgeEffect | EdgeEffect | 是 | 组件相关 | Spring/Fade/None |
| alwaysEnabled | boolean | options 中必填 | Scroll=true；其他主要组件=false | 控制短内容是否仍可交互 |
| effectEdge | number/int | 否 | ALL | SDK 枚举声明 START=1、END=2；内部支持 ALL=3 |

**滚动物理与输入**

| 属性 | 值 |
|---|---|
| 函数签名 | `enableScrollInteraction(boolean)`；`friction(number|Resource)`；`flingSpeedLimit(number)`；`enableScrollWithMouse(boolean|undefined)`；`digitalCrownSensitivity(CrownSensitivity|undefined)`；`backToTop(boolean)` |
| 返回值 | 当前组件属性对象 |
| 开放范围 | Public；数字表冠 Public C 通道不开放通用属性 |
| 错误码 | ArkTS N/A；Public C API 为 0/401/106102 |
| 关联 AC | AC-2.1-AC-4.5 |

**参数约束**

| 参数 | 类型 | 必填 | 默认值 | 约束条件 |
|---|---|---|---|---|
| interaction | boolean | 是 | true | false 不影响 Scroller |
| friction | number/Resource | 是 | 设备/API/主题相关 | >0；否则恢复默认 |
| speedLimit | number | 是 | 非穿戴 9000vp/s、穿戴 5000vp/s 核心基线 | >0；否则 MAX_VELOCITY |
| mouse | boolean/undefined | 是 | false | Item drag 可强制关闭 |
| crown | CrownSensitivity/undefined | 是 | MEDIUM | LOW/MEDIUM/HIGH |
| backToTop | boolean | 是 | reset 按轴/API 计算 | 状态栏与可见激活守卫 |

## 兼容性声明

- **已有 API 行为变更:** 否。本次补录现有历史差异，不修改产品行为。
- **配置文件格式变更:** 否。
- **数据存储格式变更:** 否。
- **最低支持版本:** edgeEffect 组件级最早 API 7；公共滚动交互/物理方法主要为 API 11；backToTop API 15；表冠/effectEdge API 18；鼠标拖动 API 26。
- **API 版本号策略:** 同时记录组件级历史声明和公共方法级 @since。
- **设备差异:** friction、MAX_VELOCITY、表冠能力和状态栏能力随设备变化。
- **通道差异:** Public C、generated Modifier、旧 JS 与 ArkTS Native 的 options、reset 和非法值处理不完全一致。

## 架构约束

| 关键约束 | 约束说明 | 影响 AC |
|---|---|---|
| 手势与控制器分离 | enableScrollInteraction 只约束普通手势，不禁止 Scroller | AC-2.1 |
| 版本/设备输入 | friction 默认值不得脱离 target API、设备、主题和系统属性 | AC-2.3-AC-2.4 |
| 单位边界 | flingSpeedLimit 的 API 单位为 vp/s，核心为 px/s | AC-2.5-AC-2.6 |
| 输入优先级 | List/Grid Item drag 优先于鼠标滚动 | AC-3.2 |
| 编译与焦点 | 数字表冠依赖 SUPPORT_DIGITAL_CROWN 和 FocusHub | AC-3.4-AC-3.5 |
| 生命周期守卫 | backToTop 需检查应用、窗口、节点和祖先状态 | AC-4.1-AC-4.5 |

## 非功能性需求

| 类型 | 指标/阈值 | 验证方式 | 证据 |
|---|---|---|---|
| 性能 | 速度限制与摩擦计算不得额外引入布局 | Host 动画测试 | `scrollable.cpp:851-885` |
| 功耗 | 禁用交互后不启动对应手势动画；表冠仅在焦点和编译支持时注册 | 生命周期测试 | `scrollable_pattern.cpp:5069-5085` |
| 内存 | 不新增持久资源 | 源码审查 | 本次仅文档补录 |
| 安全 | 不涉及敏感数据 | 接口审查 | 输入均为 UI 控制值 |
| 可靠性 | 非正 friction/fling 输入可恢复默认 | 边界测试 | `scrollable_pattern.cpp:2011-2070` |
| 可测试性 | 每个输入通道和组件差异均有验证映射 | VM-1 至 VM-5 | 本文 |
| 自动化维测 | 沿用滚动事件和属性 Dump | 源码审查 | ScrollablePattern Dump 路径 |
| 定界定位 | 失败日志需包含组件、API、设备、轴向和输入通道 | 参数化测试 | generated/Public C 测试 |

## 多设备适配声明

| 设备类型 | 行为差异 | 规格/约束 | 验证方式 | 证据 |
|---|---|---|---|---|
| 手机 | 支持触摸、状态栏回顶和鼠标能力（存在相应输入时） | backToTop 需状态栏事件 | Host/集成测试 | `scrollable_pattern.cpp:3268-3364` |
| 平板/PC | 鼠标拖动适用；Item drag 可覆盖鼠标滚动 | mouse 默认 false | 鼠标与拖拽测试 | `list_pattern.cpp:272-278` |
| 折叠屏 | 与手机相同，窗口和祖先可见性变化影响回顶守卫 | 使用最新窗口状态 | 生命周期测试 | backToTop 守卫链 |
| 穿戴设备 | friction 默认 0.9，MAX_VELOCITY 基线 5000；支持构建可使用数字表冠 | 表冠默认 MEDIUM | 表冠/物理测试 | `scrollable_pattern.h:76-90` |

## 全局特性影响

| 特性 | 适用？ | 结论 | 关联场景 |
|---|---|---|---|
| 无障碍 | 是 | 禁用手势不应移除程序化滚动和无障碍滚动能力 | AC-2.1 |
| 大字体 | 否 | 不读取字体缩放 |
| 深色模式 | 否 | 本 Feat 不配置颜色 |
| 多窗口/分屏 | 是 | 窗口激活和可见状态影响 backToTop | AC-4.4 |
| 多用户 | 否 | 无用户状态 |
| 版本升级 | 是 | friction、backToTop 和 API 开放时间存在版本边界 | AC-2.4, AC-4.2 |
| 生态兼容 | 是 | 多范式和 Public C 通道存在 options/reset 差异 | AC-1.5, AC-3.3 |

## 行为场景（可选，Gherkin）

```gherkin
Feature: 滚动交互与物理效果
  Scenario: 短内容启用边缘效果
    Given Scroll 内容长度小于视口
    When 设置 edgeEffect 为 Spring 且 alwaysEnabled 为 true
    Then 组件仍接受手势位移
    And 在允许的边缘执行 Spring 效果

  Scenario Outline: 摩擦系数默认演进
    Given 非穿戴设备未设置有效 friction
    When target API 为 <api>
    Then 兼容基线摩擦系数为 <value>

    Examples:
      | api | value |
      | 10 | 0.6 |
      | 11 | 0.7 |
      | 12 | 0.75 |

  Scenario: Item 拖拽覆盖鼠标滚动
    Given List 注册了 Item 拖拽回调
    When 设置 enableScrollWithMouse 为 true
    Then List 仍关闭鼠标 Pan 滚动

  Scenario: 状态栏回顶被祖先可见性阻止
    Given backToTop 为 true
    And 任一祖先节点不可见或未激活
    When 用户点击状态栏
    Then 当前滚动容器不执行回顶
```

## Spec 自审清单

- [x] 无占位符文本
- [x] 所有 AC 使用 WHEN/THEN 格式，可独立测试
- [x] 范围不包含嵌套滚动算法和事件回调生命周期
- [x] 无语义模糊表述
- [x] AC 与规则表交叉一致
- [x] 每条规则满足五项质量检查

## context-references

```yaml
context-queries:
  - repo: "openharmony/arkui_ace_engine"
    query: "ScrollablePattern edgeEffect friction flingSpeedLimit backToTop implementation"
  - repo: "openharmony/arkui_ace_engine"
    query: "enableScrollWithMouse item drag digital crown focus lifecycle"
  - repo: "openharmony/interface_sdk-js"
    query: "ScrollableCommonMethod edgeEffect friction crown backToTop API versions"
```

**关键文档：** `frameworks/core/components_ng/pattern/scrollable/`、`interfaces/native/native_node.h`、`docs/pattern/scroll/Scroll_Knowledge_Base.md`
