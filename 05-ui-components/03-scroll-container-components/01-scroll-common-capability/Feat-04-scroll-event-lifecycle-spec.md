# 特性规格

## 概述

| 字段 | 内容 |
|---|---|
| 特性名称 | 滚动事件生命周期 |
| 特性编号 | Func-05-03-01-Feat-04 |
| 所属 Epic | 滚动公共能力长期规格补录 |
| 优先级 | P1 |
| 目标版本 | API 9-26 已有能力补录 |
| SIG 归属 | ArkUI SIG |
| 状态 | Baselined |
| 复杂度 | 复杂 |

本特性规定滚动帧前拦截、布局后通知、滚动起止、拖拽/惯性细粒度事件和到达边界事件的触发条件、顺序、参数单位、注销语义与组件差异。

## 本次变更范围（Delta）

| 类型 | 内容 | 说明 |
|---|---|---|
| ADDED | 帧级事件长期规格 | 补录 onScrollFrameBegin、onWillScroll、onDidScroll 与旧 onScroll |
| ADDED | 生命周期长期规格 | 补录 start/stop、drag/fling 和编程滚动/嵌套差异 |
| ADDED | Reach 长期规格 | 补录初始化、短内容、Spring 跨界与组件去重规则 |
| ADDED | Native 事件矩阵 | 补录 Public NativeNode、generated handler、同步返回和单位偏差 |

## 输入文档

- SDK：`/home/leslie/repo/interface_sdk-js/api/@internal/component/ets/common.d.ts:29165-29329,29429-29510`、`scroll.d.ts:1061-1209,1349-1373,1476-1522`
- 静态 SDK：`/home/leslie/repo/interface_sdk-js/api/arkui/component/common.static.d.ets:15450-15557,15641-15686`
- 公共实现：`frameworks/core/components_ng/pattern/scrollable/scrollable_pattern.cpp:3138-3217,3405-3789`、`scrollable.cpp:699-718,925-965`
- 组件触发顺序：`scroll/scroll_pattern.cpp:168-194`、`list/list_pattern.cpp:745-855`、`grid/grid_pattern.cpp:823-860`、`waterflow/water_flow_pattern.cpp:354-430`
- Native 事件：`interfaces/native/native_node.h:11654-12147`、`interfaces/native/node/event_converter.cpp:139-174,327-340`
- 共享设计：`05-ui-components/03-scroll-container-components/01-scroll-common-capability/design.md`

## 用户故事

### US-1: 拦截和观察每帧滚动

作为应用开发者，我希望在布局前调整本帧滚动量并在布局后读取实际位移，以便实现联动和限位效果。

| AC编号 | 验收标准 | 类型 |
|---|---|---|
| AC-1.1 | WHEN onScrollFrameBegin 返回 offsetRemain THEN该值替换本帧候选位移并参与后续嵌套分配 | 正常 |
| AC-1.2 | WHEN同时注册 ArkTS 与 JSFrameNode 帧前回调 THEN按前者后者串行执行，后一回调接收前一回调结果 | 正常 |
| AC-1.3 | WHEN onWillScroll 返回新 offset THEN组件以该值继续布局；Observer 的 will 回调在其后继续调整 | 正常 |
| AC-1.4 | WHEN布局产生非零实际位移 THEN触发旧 onScroll/onDidScroll；WHEN停止且本帧未上报 IDLE THEN补发 0vp+IDLE | 边界 |
| AC-1.5 | WHEN组件为 Scroll THEN will/did 使用 x/y 二维参数；WHEN为 List/Grid/WaterFlow THEN使用单轴参数 | 正常 |
| AC-1.6 | WHEN来源为普通控制器跳转、越界回弹或滚动条拖动 THEN不触发 onScrollFrameBegin；WHEN来源为用户输入、惯性或 Scroller.fling THEN触发 | 边界 |

### US-2: 观察滚动起止和编程滚动

作为应用开发者，我希望 start/stop 与实际动画生命周期一致，以便正确维护交互状态。

| AC编号 | 验收标准 | 类型 |
|---|---|---|
| AC-2.1 | WHEN有效拖动、滚动条拖动或带动画控制器滚动开始 THEN触发 onScrollStart | 正常 |
| AC-2.2 | WHEN滚动与尾随动画全部结束 THEN先完成 IDLE onDidScroll，再触发 onScrollStop | 正常 |
| AC-2.3 | WHEN新 start 前存在尚未结算的旧 stop THEN先结算旧 stop，再触发新 start | 边界 |
| AC-2.4 | WHEN scrollAbort=true THEN抑制该段公开 start/stop，但 stop 收尾仍清除 abort 和闩锁状态 | 恢复 |
| AC-2.5 | WHEN AnimateTo 目标等于当前位置 THEN不触发 start；WHEN立即 ScrollTo 更新偏移 THEN不显式触发 start | 边界 |
| AC-2.6 | WHEN嵌套子容器开始/结束 THEN子节点先处理，再按 NeedParent 或 nestedInterrupt 向父链递归 | 正常 |

### US-3: 观察拖拽与惯性细粒度生命周期

作为应用开发者，我希望区分手指拖拽和惯性阶段，以便准确控制业务状态。

| AC编号 | 验收标准 | 类型 |
|---|---|---|
| AC-3.1 | WHEN拖拽即将开始 THEN onWillStartDragging 先于公共 onScrollStart 触发 | 正常 |
| AC-3.2 | WHEN手指即将抬起 THEN onWillStopDragging 以 vp/s 报告原始手势速度 | 正常 |
| AC-3.3 | WHEN拖拽结束 THEN onDidStopDragging(willFling) 报告惯性是否实际成功启动 | 正常 |
| AC-3.4 | WHEN willFling=true THEN onDidStopDragging 后触发 onWillStartFling；WHEN惯性结束或被替换 THEN触发 onDidStopFling | 正常 |
| AC-3.5 | WHEN动态接口版本低于 API20/21 或静态版本低于 API26 THEN不得假定对应细粒度事件存在 | 边界 |
| AC-3.6 | WHEN静态接口传 undefined 或 Native reset THEN注销对应回调 | 恢复 |

### US-4: 观察到达起止边界

作为应用开发者，我希望准确识别到达内容边界，以便加载数据或更新导航状态。

| AC编号 | 验收标准 | 类型 |
|---|---|---|
| AC-4.1 | WHEN List/Grid 初始化位于首端 THEN触发 onReachStart；WHEN短内容首次布局已到尾端 THEN按组件规则触发 onReachEnd | 边界 |
| AC-4.2 | WHEN List/Grid 使用 Spring 越界并回到边界 THEN越界到达和回边可各触发一次 reach 事件 | 边界 |
| AC-4.3 | WHEN Scroll 前后帧跨越起止边界 THEN触发对应 reach；初始化末端只通知 Observer 的路径不得泛化为公开回调 | 正常 |
| AC-4.4 | WHEN WaterFlow 到达末端且 repeatDifference!=0 THEN不触发公开 onReachEnd | 边界 |
| AC-4.5 | WHEN布局后事件批次执行 THEN顺序为 onScroll/onDidScroll、索引/可见项、reachStart/reachEnd、onScrollStop | 正常 |

## 验收追溯

| AC | 关联规则 | 关联 Task | 验证方式 | 证据 |
|---|---|---|---|---|
| AC-1.1-AC-1.6 | R-1-R-7 | TASK-05-03-01-F4 | 帧前返回值、单位、二维/一维、触发源测试 | `scrollable_pattern.cpp:3138-3159,3771-3789` |
| AC-2.1-AC-2.6 | R-8-R-13 | TASK-05-03-01-F4 | start/stop/abort/programmatic/nested 顺序测试 | `scrollable_pattern.cpp:3405-3713,3161-3217` |
| AC-3.1-AC-3.6 | R-14-R-19 | TASK-05-03-01-F4 | drag/fling 状态机与版本/注销测试 | `scrollable.cpp:699-718,925-965` |
| AC-4.1-AC-4.5 | R-20-R-24 | TASK-05-03-01-F4 | 四组件 reach 与布局后事件顺序测试 | 四组件 Pattern 布局后回调 |

## 规则定义

| 规则ID | 类型 | 触发条件 | 预期行为 | 边界/约束 | 关联AC |
|---|---|---|---|---|---|
| R-1 | 行为 | frameBegin 返回 offsetRemain | 替换候选位移 | 先于嵌套模式分配 | AC-1.1 |
| R-2 | 行为 | 同时存在 ArkTS/JSFrameNode frameBegin | 串行改写，后者接收前者结果 | px↔vp 且符号转换 | AC-1.2 |
| R-3 | 行为 | onWillScroll/Observer will 返回值 | 依次改写组件布局输入 | Scroll 二维、其他一维 | AC-1.3, AC-1.5 |
| R-4 | 行为 | 布局实际 offset!=0 | 上报 onScroll/onDidScroll | 参数为布局确认结果 | AC-1.4 |
| R-5 | 恢复 | stop 且未上报 IDLE | 补发 0 offset + IDLE | 先于 onScrollStop | AC-1.4, AC-2.2 |
| R-6 | 边界 | Scroll vs 其他容器 | 使用二维 x/y 或一维 offset | Native 数据数组亦不同 | AC-1.5 |
| R-7 | 边界 | controller/overscroll/scrollbar 与 input/fling | 前者不触发 frameBegin，后者触发 | 以 SDK 触发源清单为准 | AC-1.6 |
| R-8 | 行为 | 有效滚动开始 | 触发 start 并更新滚动/滚动条状态 | abort 时抑制公开回调 | AC-2.1, AC-2.4 |
| R-9 | 行为 | 所有滚动和尾随动画结束 | IDLE did 后触发 stop | stop 使用延迟闩锁 | AC-2.2 |
| R-10 | 恢复 | 新 start 遇旧 stop | 先结算旧 stop | 避免生命周期交叠 | AC-2.3 |
| R-11 | 恢复 | scrollAbort=true | 不发公开 start/stop，最终清状态 | Observer/内部状态仍按实现收尾 | AC-2.4 |
| R-12 | 边界 | AnimateTo 无位移或立即 ScrollTo | 不显式发 start | 动画实际启动才发 | AC-2.5 |
| R-13 | 行为 | nested start/end | 子先父后递归 | end 支持 nestedInterrupt | AC-2.6 |
| R-14 | 行为 | drag start | willStartDragging 后进入公共 start | isDragging 先置 true | AC-3.1 |
| R-15 | 行为 | drag 即将结束 | willStopDragging(velocity vp/s) | 动态 API20 | AC-3.2 |
| R-16 | 行为 | drag 已结束 | didStopDragging(willFling) | willFling 取实际启动结果 | AC-3.3 |
| R-17 | 行为 | 实际开始/结束 user fling | willStartFling/didStopFling | 与拖拽事件有固定顺序 | AC-3.4 |
| R-18 | 边界 | 动态 API20/21、静态 API26 | 仅在对应版本开放 | 旧版本不得调用 | AC-3.5 |
| R-19 | 恢复 | 静态 undefined/Native reset | 清空 EventHub 回调 | 动态部分接口不接受 undefined | AC-3.6 |
| R-20 | 边界 | List/Grid 初始首端或短内容 | 按组件公开规则触发 reach | WaterFlow 不泛化该说明 | AC-4.1 |
| R-21 | 边界 | List/Grid Spring 越界与回边 | 两个跨界点可各触发一次 | 非简单一次锁 | AC-4.2 |
| R-22 | 行为 | Scroll 前后帧跨边界 | 触发对应 reach | 初始化末端存在 Observer-only 路径 | AC-4.3 |
| R-23 | 边界 | WaterFlow reachEnd | 还需 repeatDifference==0 | 算法/重复布局约束 | AC-4.4 |
| R-24 | 行为 | 布局后事件批次 | did → index/visible → reach → stop | 四组件基本一致 | AC-4.5 |

## 验证映射

| 编号 | 对应规格项 | 验证方式 | 验证重点 |
|---|---|---|---|
| VM-1 | AC-1.1-AC-1.6 | 四组件 frameBegin/will/did 参数化 Host + Native 测试 | 返回值链、单位、一维/二维、触发源 |
| VM-2 | AC-2.1-AC-2.6 | drag、scrollbar、AnimateTo、ScrollTo、abort、nested 测试 | start/IDLE/stop 顺序和去重 |
| VM-3 | AC-3.1-AC-3.6 | API20/21/26 与 drag/fling 状态机测试 | 原始速度、willFling、注销 |
| VM-4 | AC-4.1-AC-4.5 | List/Grid/Scroll/WaterFlow reach 测试 | 初始化、短内容、Spring、repeatDifference、回调批次 |
| VM-5 | 全部 AC | Public NativeNode 事件注册/重复注册/unregister 测试 | 转换矩阵、同步返回、handler 缺失风险 |

## API 变更分析

### 新增 API

本次不新增接口，补录以下现有事件。

| API 名称 | 开放范围 | 入参概要 | 返回值 | 错误码范围 | 功能描述 | 关联 AC |
|---|---|---|---|---|---|---|
| `onScrollFrameBegin` | Public | offset,state | ScrollFrameResult | N/A | 帧前改写位移 | AC-1.1-AC-1.2, AC-1.6 |
| `onWillScroll` | Public | offset(s),state,source | void/ScrollResult/OffsetResult | N/A | 布局前拦截 | AC-1.3, AC-1.5 |
| `onDidScroll` | Public | offset(s),state | void | N/A | 布局后通知 | AC-1.4-AC-1.5 |
| `onScrollStart/Stop` | Public | void callback | void | N/A | 粗粒度起止 | AC-2.1-AC-2.6 |
| `onWill/Did*Dragging/Fling` | Public | void、velocity、willFling | void | N/A | 细粒度拖拽/惯性生命周期 | AC-3.1-AC-3.6 |
| `onReachStart/End` | Public | void callback | void | N/A | 到达内容边界 | AC-4.1-AC-4.5 |
| `NODE_*_EVENT_*` | Public C API | ArkUI_NodeEvent | ArkUI_ErrorCode | 0/401/106102 | 注册、注销 Native 节点事件 | 全部 AC |

### 变更/废弃 API

| API 名称 | 变更类型 | 影响场景 | 迁移指引 | 关联 AC |
|---|---|---|---|---|
| `onScroll` | 废弃 | 公共/List/Grid API12 废弃；Scroll 二维旧事件同样废弃 | 使用 onDidScroll；Scroll 历史注释指向 onWillScroll，保留文档风险 | AC-1.4 |
| `onWillScroll/onDidScroll` | 历史新增 | 动态 API12；静态组件 API23 | 按组件签名使用 | AC-1.3-AC-1.5 |
| `onWillStopDragging` | 历史新增 | 动态 API20、静态 API26 | 读取 vp/s velocity | AC-3.2 |
| 其余 drag/fling 事件 | 历史新增 | 动态 API21、静态 API26 | 低版本不调用 | AC-3.1, AC-3.3-AC-3.6 |

## 接口规格

### 接口定义

**帧级事件**

| 属性 | 值 |
|---|---|
| 函数签名 | `onScrollFrameBegin(offset,state): ScrollFrameResult`；`onWillScroll(...): void|Result`；`onDidScroll(...): void` |
| 返回值 | frameBegin/will 可改写位移；did 无返回值 |
| 开放范围 | Public |
| 错误码 | ArkTS N/A；Native 注册返回 ArkUI_ErrorCode |
| 关联 AC | AC-1.1-AC-1.6 |

**参数约束**

| 参数 | 类型 | 必填 | 默认值 | 约束条件 |
|---|---|---|---|---|
| offset | number/Dimension | 是 | N/A | 单轴 vp；Scroll 为 x/y vp |
| state | ScrollState | 是 | IDLE | SCROLL/FLING/IDLE |
| source | ScrollSource | will 是 | N/A | DRAG/FLING/SCROLLER 等 |
| handler | callback/undefined | 动态按签名、静态否 | 未注册 | undefined 注销仅适用于声明通道 |

**生命周期与 Reach 事件**

| 属性 | 值 |
|---|---|
| 函数签名 | `onScrollStart/Stop`、`onWillStartDragging`、`onWillStopDragging`、`onDidStopDragging`、`onWillStartFling`、`onDidStopFling`、`onReachStart/End` |
| 返回值 | void |
| 开放范围 | Public |
| 错误码 | ArkTS N/A；Native 注册返回 0/401/106102 |
| 关联 AC | AC-2.1-AC-4.5 |

**行为场景索引**

| # | 触发条件 | 预期行为 | 关联 AC |
|---|---|---|---|
| 1 | 拖拽后成功启动惯性 | willDrag → start → willStopDrag → didStopDrag(true) → willFling → didScroll… → didStopFling → IDLE → stop | AC-2.1-AC-3.4 |
| 2 | 布局跨越起止边界 | did/index 后触发 reach，最后 stop | AC-4.1-AC-4.5 |

## 兼容性声明

- **已有 API 行为变更:** 否。本次补录旧事件废弃关系和当前触发顺序。
- **配置文件格式变更:** 否。
- **数据存储格式变更:** 否。
- **最低支持版本:** frameBegin 最早 List/Scroll API9；Grid/WaterFlow API10；公共滚动事件 API11/12；细粒度拖拽/惯性 API20/21；静态对应能力 API23/26。
- **API 版本号策略:** 采用事件方法级和组件级实际 `@since`，不使用公共类单一版本覆盖。
- **组件差异:** Scroll 使用二维事件；其他组件使用一维事件；reach 初始化/短内容/重复触发规则不同。
- **Native 差异:** 四组件 event enum 和 handler 数量不一致；部分转换矩阵缺分支；Grid/WaterFlow PX 返回路径与 Scroll/List 不同。

## 架构约束

| 关键约束 | 约束说明 | 影响 AC |
|---|---|---|
| 前置拦截链 | frameBegin 先于嵌套分配，will 在组件布局前 | AC-1.1-AC-1.3 |
| 布局后通知 | did/reach/stop 使用布局确认后的状态 | AC-1.4, AC-4.1-AC-4.5 |
| 一维/二维分轨 | Scroll 与其他容器不得共用虚构签名 | AC-1.5 |
| 起止闩锁 | start/stop 受 scrollStop/abort 和动画状态控制 | AC-2.1-AC-2.5 |
| 同步 Native 返回 | will/frameBegin 必须在回调返回前读取 data[] 改写值 | AC-1.1-AC-1.3 |

## 非功能性需求

| 类型 | 指标/阈值 | 验证方式 | 证据 |
|---|---|---|---|
| 性能 | 帧级回调每个已注册通道每帧最多按固定链执行，不额外遍历 UI 树 | 高频 Host 测试 | Pattern 直接读取 EventHub |
| 功耗 | 无实际位移时不持续发送 didScroll，停止时最多补发一次 IDLE | 事件计数测试 | `scrollable_pattern.cpp:3466-3484` |
| 内存 | EventHub 持有回调，重复 Native 注册更新元数据而非叠加 | 注册测试 | `node_model.cpp:550-563` |
| 安全 | Native event 对象仅在回调期间有效，不得跨回调保存 | C API 审查 | `native_node.h:13110-13121` |
| 可靠性 | abort、中断和新旧滚动交接必须清理闩锁 | 状态机测试 | `scrollable_pattern.cpp:3405-3713` |
| 可测试性 | 事件顺序、参数、次数和返回值均可观测 | VM-1 至 VM-5 | 本文 |
| 自动化维测 | Dump/Recorder/Observer 记录 start/stop/reach | 源码审查 | Pattern 事件记录路径 |
| 定界定位 | Trace 包含事件名、node id/tag、offset/state/source | Trace 审查 | 公共 Pattern 与组件实现 |

## 多设备适配声明

| 设备类型 | 行为差异 | 规格/约束 | 验证方式 | 证据 |
|---|---|---|---|---|
| 手机 | 触摸拖拽产生完整 drag/fling 生命周期 | 速度单位 vp/s | 手势测试 | `scrollable.cpp:699-965` |
| 平板/PC | 鼠标滚轮可能无 fling，滚动条拖动不触发 frameBegin | 仍产生适用的 start/did/stop | 鼠标/滚动条测试 | SDK 触发源说明 |
| 折叠屏 | 窗口尺寸变化可改变 reach 判定 | 以布局后边界为准 | 尺寸变化测试 | 四组件 Pattern |
| 穿戴设备 | 数字表冠复用拖动链路，但设备构建条件见 Feat-02 | 事件顺序与普通拖动一致 | 表冠测试 | Scrollable 运行时 |

## 全局特性影响

| 特性 | 适用？ | 结论 | 关联场景 |
|---|---|---|---|
| 无障碍 | 是 | start/stop 同步产生无障碍滚动起止事件 | AC-2.1-AC-2.4 |
| 大字体 | 间接 | 内容尺寸变化影响 reachStart/reachEnd | AC-4.1-AC-4.4 |
| 深色模式 | 否 | 不涉及颜色 |
| 多窗口/分屏 | 是 | 布局尺寸变化影响边界和回调时机 | AC-4.1-AC-4.4 |
| 多用户 | 否 | 无用户状态 |
| 版本升级 | 是 | API9-26 的事件演进和废弃关系需兼容 | AC-1.1-AC-3.6 |
| 生态兼容 | 是 | ArkTS 动静态和 Native 事件矩阵/单位存在差异 | 全部 AC |

## 行为场景（可选，Gherkin）

```gherkin
Feature: 滚动事件生命周期
  Scenario: 拖拽后启动惯性
    Given 已注册全部滚动和拖拽惯性事件
    When 用户拖动并以非零有效速度抬手
    Then onWillStartDragging 先于 onScrollStart
    And onDidStopDragging 的 willFling 为 true
    And onWillStartFling 在其后触发
    And 惯性结束后先补发 IDLE onDidScroll 再触发 onScrollStop

  Scenario: 帧前两级回调改写位移
    Given ArkTS frameBegin 返回 8vp 且 JSFrameNode frameBegin 返回 5vp
    When 本帧输入位移进入滚动链
    Then JSFrameNode 接收到 8vp
    And 后续嵌套分配使用 5vp
```

## Spec 自审清单

- [x] 无“待定”“TBD”“TODO”等占位符
- [x] 所有 AC 使用 WHEN/THEN 格式，可独立测试
- [x] 范围边界明确
- [x] 无语义模糊表述
- [x] AC 与规则表交叉一致
- [x] 规则表每条通过 5 项质量检查

## context-references

```yaml
context-queries:
  - repo: "openharmony/arkui_ace_engine"
    query: "scroll event lifecycle frameBegin willScroll didScroll start stop reach drag fling"
  - repo: "openharmony/interface_sdk-js"
    query: "ScrollableCommonMethod scroll callbacks API version"
```

**关键文档：** ArkUI Scroll/List/Grid/WaterFlow SDK 事件声明；ScrollablePattern、Scrollable、组件 Pattern 和 Native node event 实现。
