# ArkUI 特性规格索引

> 本文件是 ArkUI ace_engine 特性规格（Spec）体系的总入口。所有功能域和特性必须在此注册后才能生成规格文档。

## 功能域层级树

### 一级域（L1）

| 编号 | 目录名（英文 slug） | 中文名 | 说明 |
|------|---------------------|--------|------|
| 01 | `01-architecture` | 架构通用设计 | 编译构建、目录结构、部件化、兼容性设计、架构优化 |
| 02 | `02-cross-platform` | 跨平台适配层 | 多平台适配、平台抽象、渲染后端适配 |
| 03 | `03-engine-framework` | 引擎框架层 | 渲染管线、动效、资源主题、事件框架、窗口、多实例、无障碍、DFX |
| 04 | `04-common-capability` | 通用能力层 | 通用属性、通用事件、自定义扩展、自定义节点、路由、焦点、输入交互等通用能力 |
| 05 | `05-ui-components` | 组件层 | 布局、导航、滚动容器、表单、选择、弹窗、文本、图片、绘制等组件 |
| 06 | `06-common-interface` | 通用接口层 | 前端桥接、Inner 接口、其它范式接入 |
| 07 | `07-frontend` | 前端层 | ArkTS 高级组件、状态管理、自定义组件、渲染控制、响应式环境变量、生成式 UI |
| 08 | `08-ndk` | NDK | Node C-API、XComponent C-API 等 NDK 接口 |
| 09 | `09-developer-tools` | 开发者工具 | 预览器、工具链、开发者文档、Sample、ComponentTest |
| 10 | `10-product-customization` | 产品化定制 | 穿戴等产品化定制能力 |

### 二级域（L2）→ 三级域（L3）→ 功能域

| L1 | L2 | L3 | FuncID | 目录路径 | design.md | 特性数 |
|----|----|----|--------|----------|-----------|--------|
| 01 架构通用设计 | 01 架构设计 | 01 编译构建 | `01-01-01` | `01-architecture/01-architecture-design/01-build-system/` | [design.md](01-architecture/01-architecture-design/01-build-system/design.md) | 1 |
| 01 架构通用设计 | 01 架构设计 | 02 目录结构 | `01-01-02` | `01-architecture/01-architecture-design/02-directory-structure/` | *待补充* | 0 |
| 01 架构通用设计 | 01 架构设计 | 03 部件化 | `01-01-03` | `01-architecture/01-architecture-design/03-modularization/` | *待补充* | 0 |
| 01 架构通用设计 | 02 架构优化 | 01 产品化解耦 | `01-02-01` | `01-architecture/02-architecture-optimization/01-product-decoupling/` | *待补充* | 0 |
| 02 跨平台适配层 | 01 跨平台适配层 | 01 OH平台适配 | `02-01-01` | `02-cross-platform/01-platform-adapter/01-oh-platform-adapter/` | [design.md](02-cross-platform/01-platform-adapter/01-oh-platform-adapter/design.md) | 1 |
| 02 跨平台适配层 | 01 跨平台适配层 | 02 Android平台适配 | `02-01-02` | `02-cross-platform/01-platform-adapter/02-android-platform-adapter/` | *待补充* | 0 |
| 02 跨平台适配层 | 01 跨平台适配层 | 03 iOS平台适配 | `02-01-03` | `02-cross-platform/01-platform-adapter/03-ios-platform-adapter/` | *待补充* | 0 |
| 02 跨平台适配层 | 01 跨平台适配层 | 04 预览器平台适配 | `02-01-04` | `02-cross-platform/01-platform-adapter/04-previewer-platform-adapter/` | [design.md](02-cross-platform/01-platform-adapter/04-previewer-platform-adapter/design.md) | 3 |
| 02 跨平台适配层 | 02 渲染后端适配 | 01 Rosen渲染后端对接 | `02-02-01` | `02-cross-platform/02-render-backend-adapter/01-rosen-render-backend-adapter/` | [design.md](02-cross-platform/02-render-backend-adapter/01-rosen-render-backend-adapter/design.md) | 3 |
| 03 引擎框架层 | 01 渲染管线 | 01 渲染管线 | `03-01-01` | `03-engine-framework/01-render-pipeline/01-basic-render-pipeline/` | [design.md](03-engine-framework/01-render-pipeline/01-basic-render-pipeline/design.md) | 1 |
| 03 引擎框架层 | 01 渲染管线 | 02 多级渲染管线 | `03-01-02` | `03-engine-framework/01-render-pipeline/02-multi-level-render-pipeline/` | [design.md](03-engine-framework/01-render-pipeline/02-multi-level-render-pipeline/design.md) | 1 |
| 03 引擎框架层 | 02 动效能力 | 01 动效框架 | `03-02-01` | `03-engine-framework/02-animation-capability/01-animation-framework/` | [design.md](03-engine-framework/02-animation-capability/01-animation-framework/design.md) | 1 |
| 03 引擎框架层 | 02 动效能力 | 02 属性动画 | `03-02-02` | `03-engine-framework/02-animation-capability/02-property-animation/` | [design.md](03-engine-framework/02-animation-capability/02-property-animation/design.md) | 1 |
| 03 引擎框架层 | 02 动效能力 | 03 显式动画 | `03-02-03` | `03-engine-framework/02-animation-capability/03-explicit-animation/` | [design.md](03-engine-framework/02-animation-capability/03-explicit-animation/design.md) | 1 |
| 03 引擎框架层 | 02 动效能力 | 04 关键帧动画 | `03-02-04` | `03-engine-framework/02-animation-capability/04-keyframe-animation/` | [design.md](03-engine-framework/02-animation-capability/04-keyframe-animation/design.md) | 1 |
| 03 引擎框架层 | 02 动效能力 | 05 转场动画 | `03-02-05` | `03-engine-framework/02-animation-capability/05-transition-animation/` | [design.md](03-engine-framework/02-animation-capability/05-transition-animation/design.md) | 1 |
| 03 引擎框架层 | 02 动效能力 | 06 共享元素动画 | `03-02-06` | `03-engine-framework/02-animation-capability/06-shared-transition/` | [design.md](03-engine-framework/02-animation-capability/06-shared-transition/design.md) | 1 |
| 03 引擎框架层 | 02 动效能力 | 07 组件共享元素动画 | `03-02-07` | `03-engine-framework/02-animation-capability/07-geometry-transition/` | [design.md](03-engine-framework/02-animation-capability/07-geometry-transition/design.md) | 1 |
| 03 引擎框架层 | 02 动效能力 | 08 路径动画 | `03-02-08` | `03-engine-framework/02-animation-capability/08-motion-path/` | [design.md](03-engine-framework/02-animation-capability/08-motion-path/design.md) | 1 |
| 03 引擎框架层 | 02 动效能力 | 09 物理动画 | `03-02-09` | `03-engine-framework/02-animation-capability/09-physics-animation/` | [design.md](03-engine-framework/02-animation-capability/09-physics-animation/design.md) | 1 |
| 03 引擎框架层 | 02 动效能力 | 10 动画接口 | `03-02-10` | `03-engine-framework/02-animation-capability/10-animation-interface/` | [design.md](03-engine-framework/02-animation-capability/10-animation-interface/design.md) | 1 |
| 03 引擎框架层 | 03 资源主题 | 01 资源访问 | `03-03-01` | `03-engine-framework/03-resource-theme/01-resource-access/` | [design.md](03-engine-framework/03-resource-theme/01-resource-access/design.md) | 3 |
| 03 引擎框架层 | 03 资源主题 | 02 主题分层访问 | `03-03-02` | `03-engine-framework/03-resource-theme/02-theme-layered-access/` | [design.md](03-engine-framework/03-resource-theme/02-theme-layered-access/design.md) | 1 |
| 03 引擎框架层 | 03 资源主题 | 03 Theme框架 | `03-03-03` | `03-engine-framework/03-resource-theme/03-theme-framework/` | [design.md](03-engine-framework/03-resource-theme/03-theme-framework/design.md) | 2 |
| 03 引擎框架层 | 03 资源主题 | 04 资源动态切换 | `03-03-04` | `03-engine-framework/03-resource-theme/04-resource-dynamic-switching/` | [design.md](03-engine-framework/03-resource-theme/04-resource-dynamic-switching/design.md) | 1 |
| 03 引擎框架层 | 04 事件框架 | 01 事件基础框架 | `03-04-01` | `03-engine-framework/04-event-framework/01-event-base-framework/` | *待补充* | 0 |
| 03 引擎框架层 | 04 事件框架 | 02 拖拽框架 | `03-04-02` | `03-engine-framework/04-event-framework/02-drag-framework/` | *待补充* | 0 |
| 03 引擎框架层 | 05 窗口机制 | 01 窗口机制 | `03-05-01` | `03-engine-framework/05-window-mechanism/01-window-mechanism/` | [design.md](03-engine-framework/05-window-mechanism/01-window-mechanism/design.md) | 4 |
| 03 引擎框架层 | 05 窗口机制 | 02 子窗机制 | `03-05-02` | `03-engine-framework/05-window-mechanism/02-subwindow-mechanism/` | [design.md](03-engine-framework/05-window-mechanism/02-subwindow-mechanism/design.md) | 3 |
| 03 引擎框架层 | 06 多实例管理 | 01 多实例管理 | `03-06-01` | `03-engine-framework/06-multi-instance-management/01-multi-instance-management/` | [design.md](03-engine-framework/06-multi-instance-management/01-multi-instance-management/design.md) | 1 |
| 03 引擎框架层 | 07 无障碍机制 | 01 无障碍能力 | `03-07-01` | `03-engine-framework/07-accessibility-mechanism/01-accessibility-capability/` | *待补充* | 0 |
| 03 引擎框架层 | 07 无障碍机制 | 02 Inspector | `03-07-02` | `03-engine-framework/07-accessibility-mechanism/02-inspector/` | *待补充* | 0 |
| 03 引擎框架层 | 08 DFX | 01 日志 | `03-08-01` | `03-engine-framework/08-dfx-foundation/01-logging/` | [design.md](03-engine-framework/08-dfx-foundation/01-logging/design.md) | 3 |
| 03 引擎框架层 | 08 DFX | 02 内存管理 | `03-08-02` | `03-engine-framework/08-dfx-foundation/02-memory-management/` | [design.md](03-engine-framework/08-dfx-foundation/02-memory-management/design.md) | 4 |
| 03 引擎框架层 | 08 DFX | 03 Trace打点 | `03-08-03` | `03-engine-framework/08-dfx-foundation/03-trace/` | [design.md](03-engine-framework/08-dfx-foundation/03-trace/design.md) | 3 |
| 03 引擎框架层 | 08 DFX | 04 Dump机制 | `03-08-04` | `03-engine-framework/08-dfx-foundation/04-dump-mechanism/` | [design.md](03-engine-framework/08-dfx-foundation/04-dump-mechanism/design.md) | 4 |
| 03 引擎框架层 | 08 DFX | 05 Benchmark | `03-08-05` | `03-engine-framework/08-dfx-foundation/05-benchmark/` | *待补充* | 0 |
| 03 引擎框架层 | 08 DFX | 06 布局边界显示 | `03-08-06` | `03-engine-framework/08-dfx-foundation/06-layout-boundary-display/` | [design.md](03-engine-framework/08-dfx-foundation/06-layout-boundary-display/design.md) | 1 |
| 04 通用能力层 | 01 图片加载能力 | 01 图片加载机制 | `04-01-01` | `04-common-capability/01-image-loading/01-image-loading-mechanism/` | [design.md](04-common-capability/01-image-loading/01-image-loading-mechanism/design.md) | 1 |
| 04 通用能力层 | 01 图片加载能力 | 02 Svg解析 | `04-01-02` | `04-common-capability/01-image-loading/02-svg-parsing/` | [design.md](04-common-capability/01-image-loading/02-svg-parsing/design.md) | 4 |
| 04 通用能力层 | 01 图片加载能力 | 03 DrawableDescriptor 能力 | `04-01-03` | `04-common-capability/01-image-loading/03-drawable-descriptor/` | [design.md](04-common-capability/01-image-loading/03-drawable-descriptor/design.md) | 1 |
| 04 通用能力层 | 02 安全区机制 | 01 安全区机制 | `04-02-01` | `04-common-capability/02-safe-area/01-safe-area-mechanism/` | [design.md](04-common-capability/02-safe-area/01-safe-area-mechanism/design.md) | 5 |
| 04 通用能力层 | 03 通用属性 | 01 布局属性 | `04-03-01` | `04-common-capability/03-common-attributes/01-layout-attributes/` | [design.md](04-common-capability/03-common-attributes/01-layout-attributes/design.md) | 3 |
| 04 通用能力层 | 03 通用属性 | 02 视效属性 | `04-03-02` | `04-common-capability/03-common-attributes/02-visual-effect-attributes/` | [design.md](04-common-capability/03-common-attributes/02-visual-effect-attributes/design.md) | 1 |
| 04 通用能力层 | 03 通用属性 | 03 基础属性 | `04-03-03` | `04-common-capability/03-common-attributes/03-basic-attributes/` | [design.md](04-common-capability/03-common-attributes/03-basic-attributes/design.md) | 5 |
| 04 通用能力层 | 03 通用属性 | 04 交互属性 | `04-03-04` | `04-common-capability/03-common-attributes/04-interaction-attributes/` | *待补充* | 0 |
| 04 通用能力层 | 03 通用属性 | 05 弹窗类属性 | `04-03-05` | `04-common-capability/03-common-attributes/05-popup-attributes/` | [design.md](04-common-capability/03-common-attributes/05-popup-attributes/design.md) | 1 |
| 04 通用能力层 | 03 通用属性 | 06 模态属性 | `04-03-06` | `04-common-capability/03-common-attributes/06-modal-attributes/` | [design.md](04-common-capability/03-common-attributes/06-modal-attributes/design.md) | 1 |
| 04 通用能力层 | 03 通用属性 | 07 样式属性 | `04-03-07` | `04-common-capability/03-common-attributes/07-style-attributes/` | [design.md](04-common-capability/03-common-attributes/07-style-attributes/design.md) | 2 |
| 04 通用能力层 | 03 通用属性 | 08 基础单位 | `04-03-08` | `04-common-capability/03-common-attributes/08-basic-units/` | [design.md](04-common-capability/03-common-attributes/08-basic-units/design.md) | 1 |
| 04 通用能力层 | 03 通用属性 | 09 无障碍属性 | `04-03-09` | `04-common-capability/03-common-attributes/09-accessibility-attributes/` | *待补充* | 0 |
| 04 通用能力层 | 03 通用属性 | 10 图片相关属性 | `04-03-10` | `04-common-capability/03-common-attributes/10-image-related-attributes/` | [design.md](04-common-capability/03-common-attributes/10-image-related-attributes/design.md) | 1 |
| 04 通用能力层 | 03 通用属性 | 11 文本通用属性 | `04-03-11` | `04-common-capability/03-common-attributes/11-text-common-attributes/` | [design.md](04-common-capability/03-common-attributes/11-text-common-attributes/design.md) | 5 |
| 04 通用能力层 | 04 通用事件 | 01 触摸事件 | `04-04-01` | `04-common-capability/04-common-events/01-touch-events/` | *待补充* | 0 |
| 04 通用能力层 | 04 通用事件 | 02 按键事件 | `04-04-02` | `04-common-capability/04-common-events/02-key-events/` | *待补充* | 0 |
| 04 通用能力层 | 04 通用事件 | 03 事件分发和拦截 | `04-04-03` | `04-common-capability/04-common-events/03-event-dispatch-intercept/` | *待补充* | 0 |
| 04 通用能力层 | 04 通用事件 | 04 组件组合键 | `04-04-04` | `04-common-capability/04-common-events/04-component-shortcuts/` | *待补充* | 0 |
| 04 通用能力层 | 04 通用事件 | 05 鼠标事件 | `04-04-05` | `04-common-capability/04-common-events/05-mouse-events/` | *待补充* | 0 |
| 04 通用能力层 | 04 通用事件 | 06 手势能力 | `04-04-06` | `04-common-capability/04-common-events/06-gesture-capability/` | [design.md](04-common-capability/04-common-events/06-gesture-capability/design.md) | 5 |
| 04 通用能力层 | 04 通用事件 | 07 拖拽能力 | `04-04-07` | `04-common-capability/04-common-events/07-drag-capability/` | *待补充* | 0 |
| 04 通用能力层 | 04 通用事件 | 08 手写笔能力 | `04-04-08` | `04-common-capability/04-common-events/08-stylus-capability/` | *待补充* | 0 |
| 04 通用能力层 | 04 通用事件 | 09 组件相关事件 | `04-04-09` | `04-common-capability/04-common-events/09-component-related-events/` | *待补充* | 0 |
| 04 通用能力层 | 04 通用事件 | 10 可见区域机制 | `04-04-10` | `04-common-capability/04-common-events/10-visible-area-mechanism/` | *待补充* | 0 |
| 04 通用能力层 | 04 通用事件 | 11 交互归一化 | `04-04-11` | `04-common-capability/04-common-events/11-interaction-normalization/` | *待补充* | 0 |
| 04 通用能力层 | 05 自定义扩展能力 | 01 动态绘制属性 | `04-05-01` | `04-common-capability/05-custom-extension/01-draw-modifier/` | [design.md](04-common-capability/05-custom-extension/01-draw-modifier/design.md) | 3 |
| 04 通用能力层 | 05 自定义扩展能力 | 02 动态属性 | `04-05-02` | `04-common-capability/05-custom-extension/02-dynamic-attributes/` | [design.md](04-common-capability/05-custom-extension/02-dynamic-attributes/design.md) | 2 |
| 04 通用能力层 | 05 自定义扩展能力 | 03 自定义内容 -（表单类组件） | `04-05-03` | `04-common-capability/05-custom-extension/03-content-modifier-form/` | [design.md](04-common-capability/05-custom-extension/03-content-modifier-form/design.md) | 1 |
| 04 通用能力层 | 05 自定义扩展能力 | 04 自定义内容 -（信息展示类） | `04-05-04` | `04-common-capability/05-custom-extension/04-content-modifier-display/` | [design.md](04-common-capability/05-custom-extension/04-content-modifier-display/design.md) | 1 |
| 04 通用能力层 | 05 自定义扩展能力 | 05 自定义属性 | `04-05-05` | `04-common-capability/05-custom-extension/05-custom-property/` | [design.md](04-common-capability/05-custom-extension/05-custom-property/design.md) | 1 |
| 04 通用能力层 | 05 自定义扩展能力 | 06 组件Modifier | `04-05-06` | `04-common-capability/05-custom-extension/06-component-modifier/` | [design.md](04-common-capability/05-custom-extension/06-component-modifier/design.md) | 2 |
| 04 通用能力层 | 06 自定义节点能力 | 01 占位组件 | `04-06-01` | `04-common-capability/06-custom-node/01-placeholder-component/` | [design.md](04-common-capability/06-custom-node/01-placeholder-component/design.md) | 1 |
| 04 通用能力层 | 06 自定义节点能力 | 02 FrameNode | `04-06-02` | `04-common-capability/06-custom-node/02-frame-node/` | [design.md](04-common-capability/06-custom-node/02-frame-node/design.md) | 8 |
| 04 通用能力层 | 06 自定义节点能力 | 03 RenderNode | `04-06-03` | `04-common-capability/06-custom-node/03-render-node/` | [design.md](04-common-capability/06-custom-node/03-render-node/design.md) | 1 |
| 04 通用能力层 | 06 自定义节点能力 | 04 BuilderNode | `04-06-04` | `04-common-capability/06-custom-node/04-builder-node/` | [design.md](04-common-capability/06-custom-node/04-builder-node/design.md) | 8 |
| 04 通用能力层 | 06 自定义节点能力 | 05 ComponentContent | `04-06-05` | `04-common-capability/06-custom-node/05-component-content/` | [design.md](04-common-capability/06-custom-node/05-component-content/design.md) | 5 |
| 04 通用能力层 | 06 自定义节点能力 | 06 NodeAdapter | `04-06-06` | `04-common-capability/06-custom-node/06-node-adapter/` | [design.md](04-common-capability/06-custom-node/06-node-adapter/design.md) | 1 |
| 04 通用能力层 | 06 自定义节点能力 | 07 TypedFrameNode | `04-06-07` | `04-common-capability/06-custom-node/07-typed-frame-node/` | [design.md](04-common-capability/06-custom-node/07-typed-frame-node/design.md) | 4 |
| 04 通用能力层 | 07 迁移恢复 | 01 分布式路由迁移能力 | `04-07-01` | `04-common-capability/07-migration-recovery/01-distributed-router-migration/` | *待补充* | 0 |
| 04 通用能力层 | 07 迁移恢复 | 02 路由栈恢复 | `04-07-02` | `04-common-capability/07-migration-recovery/02-router-stack-recovery/` | [design.md](04-common-capability/07-migration-recovery/02-router-stack-recovery/design.md) | 1 |
| 04 通用能力层 | 07 迁移恢复 | 03 组件迁移机制 | `04-07-03` | `04-common-capability/07-migration-recovery/03-component-migration/` | *待补充* | 0 |
| 04 通用能力层 | 08 根视图 | 01 窗口工具栏 | `04-08-01` | `04-common-capability/08-root-view/01-window-toolbar/` | *待补充* | 0 |
| 04 通用能力层 | 08 根视图 | 02 元服务AppBar | `04-08-02` | `04-common-capability/08-root-view/02-atomic-service-appbar/` | *待补充* | 0 |
| 04 通用能力层 | 08 根视图 | 03 浮层能力 | `04-08-03` | `04-common-capability/08-root-view/03-overlay-capability/` | [design.md](04-common-capability/08-root-view/03-overlay-capability/design.md) | 1 |
| 04 通用能力层 | 09 焦点框架 | 01 焦点机制 | `04-09-01` | `04-common-capability/09-focus-framework/01-focus-mechanism/` | *待补充* | 0 |
| 04 通用能力层 | 10 组件截图 | 01 离屏截图 | `04-10-01` | `04-common-capability/10-component-screenshot/01-offscreen-screenshot/` | *待补充* | 0 |
| 04 通用能力层 | 11 组件信息获取 | 01 ComponentUtils | `04-11-01` | `04-common-capability/11-component-info/01-component-utils/` | *待补充* | 0 |
| 04 通用能力层 | 11 组件信息获取 | 02 无感监听（observer） | `04-11-02` | `04-common-capability/11-component-info/02-observer/` | [design.md](04-common-capability/11-component-info/02-observer/design.md) | 2 |
| 04 通用能力层 | 11 组件信息获取 | 03 布局回调（inspector） | `04-11-03` | `04-common-capability/11-component-info/03-inspector-layout-callback/` | *待补充* | 0 |
| 04 通用能力层 | 12 UI上下文 | 01 UIContext接口 | `04-12-01` | `04-common-capability/12-ui-context/01-ui-context-interface/` | [design.md](04-common-capability/12-ui-context/01-ui-context-interface/design.md) | 4 |
| 04 通用能力层 | 12 UI上下文 | 02 Ability上下文 | `04-12-02` | `04-common-capability/12-ui-context/02-ability-context/` | [design.md](04-common-capability/12-ui-context/02-ability-context/design.md) | 1 |
| 04 通用能力层 | 12 UI上下文 | 03 Frame回调接口 | `04-12-03` | `04-common-capability/12-ui-context/03-frame-callback/` | [design.md](04-common-capability/12-ui-context/03-frame-callback/design.md) | 1 |
| 04 通用能力层 | 13 字体文本 | 01 字体注册 | `04-13-01` | `04-common-capability/13-font-text/01-font-registration/` | [design.md](04-common-capability/13-font-text/01-font-registration/design.md) | 1 |
| 04 通用能力层 | 13 字体文本 | 02 文本测量 | `04-13-02` | `04-common-capability/13-font-text/02-text-measurement/` | [design.md](04-common-capability/13-font-text/02-text-measurement/design.md) | 3 |
| 04 通用能力层 | 14 输入交互 | 01 文本选择 | `04-14-01` | `04-common-capability/14-input-interaction/01-text-selection/` | [design.md](04-common-capability/14-input-interaction/01-text-selection/design.md) | 3 |
| 04 通用能力层 | 14 输入交互 | 02 文本快捷键 | `04-14-02` | `04-common-capability/14-input-interaction/02-text-shortcuts/` | *待补充* | 0 |
| 04 通用能力层 | 14 输入交互 | 03 文本交互 | `04-14-03` | `04-common-capability/14-input-interaction/03-text-interaction/` | [design.md](04-common-capability/14-input-interaction/03-text-interaction/design.md) | 6 |
| 04 通用能力层 | 14 输入交互 | 04 键盘控制 | `04-14-04` | `04-common-capability/14-input-interaction/04-keyboard-control/` | *待补充* | 0 |
| 04 通用能力层 | 14 输入交互 | 05 自动补全能力（AutoFill） | `04-14-05` | `04-common-capability/14-input-interaction/05-autofill/` | [design.md](04-common-capability/14-input-interaction/05-autofill/design.md) | 5 |
| 04 通用能力层 | 15 路由机制 | 01 路由管理 | `04-15-01` | `04-common-capability/15-router-mechanism/01-router-management/` | [design.md](04-common-capability/15-router-mechanism/01-router-management/design.md) | 2 |
| 04 通用能力层 | 15 路由机制 | 02 命名路由 | `04-15-02` | `04-common-capability/15-router-mechanism/02-named-router/` | [design.md](04-common-capability/15-router-mechanism/02-named-router/design.md) | 1 |
| 04 通用能力层 | 16 UIAppearance | 01 UIAppearance | `04-16-01` | `04-common-capability/16-ui-appearance/01-ui-appearance/` | [design.md](04-common-capability/16-ui-appearance/01-ui-appearance/design.md) | 1 |
| 04 通用能力层 | 17 嵌入显示能力 | 01 UIExtension机制 | `04-17-01` | `04-common-capability/17-embedded-display/01-ui-extension/` | *待补充* | 0 |
| 04 通用能力层 | 17 嵌入显示能力 | 02 IsolateComponent机制 | `04-17-02` | `04-common-capability/17-embedded-display/02-isolate-component/` | *待补充* | 0 |
| 04 通用能力层 | 17 嵌入显示能力 | 03 From卡片机制 | `04-17-03` | `04-common-capability/17-embedded-display/03-form-card/` | *待补充* | 0 |
| 04 通用能力层 | 17 嵌入显示能力 | 04 PluginComponent机制 | `04-17-04` | `04-common-capability/17-embedded-display/04-plugin-component/` | *待补充* | 0 |
| 04 通用能力层 | 18 端侧渲染 | 01 同层渲染机制 | `04-18-01` | `04-common-capability/18-on-device-rendering/01-same-layer-rendering/` | [design.md](04-common-capability/18-on-device-rendering/01-same-layer-rendering/design.md) | 1 |
| 04 通用能力层 | 19 组件复用 | 01 组件复用框架 | `04-19-01` | `04-common-capability/19-component-reuse/01-component-reuse-framework/` | [design.md](04-common-capability/19-component-reuse/01-component-reuse-framework/design.md) | 4 |
| 04 通用能力层 | 20 媒体查询能力 | 01 MediaQuery | `04-20-01` | `04-common-capability/20-media-query/01-media-query/` | [design.md](04-common-capability/20-media-query/01-media-query/design.md) | 1 |
| 04 通用能力层 | 21 适老化 | 01 大字体 | `04-21-01` | `04-common-capability/21-aging-adaptation/01-large-font/` | *待补充* | 0 |
| 04 通用能力层 | 22 国际化能力 | 01 多语言能力 | `04-22-01` | `04-common-capability/22-internationalization/01-multilingual/` | *待补充* | 0 |
| 04 通用能力层 | 22 国际化能力 | 02 镜像能力 | `04-22-02` | `04-common-capability/22-internationalization/02-mirroring/` | *待补充* | 0 |
| 04 通用能力层 | 23 AI能力 | 01 Image分析能力 | `04-23-01` | `04-common-capability/23-ai-capability/01-image-analysis/` | [design.md](04-common-capability/23-ai-capability/01-image-analysis/design.md) | 2 |
| 04 通用能力层 | 24 布局通用能力 | 01 像素取整能力 | `04-24-01` | `04-common-capability/24-layout-common-capability/01-pixel-rounding/` | [design.md](04-common-capability/24-layout-common-capability/01-pixel-rounding/design.md) | 1 |
| 04 通用能力层 | 25 热重载能力 | 01 热重载机制 | `04-25-01` | `04-common-capability/25-hot-reload/01-hot-reload-mechanism/` | *待补充* | 0 |
| 05 组件层 | 01 布局类组件 | 01 Blank | `05-01-01` | `05-ui-components/01-layout-components/01-blank/` | [design.md](05-ui-components/01-layout-components/01-blank/design.md) | 1 |
| 05 组件层 | 01 布局类组件 | 02 Divider | `05-01-02` | `05-ui-components/01-layout-components/02-divider/` | [design.md](05-ui-components/01-layout-components/02-divider/design.md) | 1 |
| 05 组件层 | 01 布局类组件 | 03 Column | `05-01-03` | `05-ui-components/01-layout-components/03-column/` | [design.md](05-ui-components/01-layout-components/03-column/design.md) | 4 |
| 05 组件层 | 01 布局类组件 | 04 ColumnSplit | `05-01-04` | `05-ui-components/01-layout-components/04-column-split/` | [design.md](05-ui-components/01-layout-components/04-column-split/design.md) | 3 |
| 05 组件层 | 01 布局类组件 | 05 Flex | `05-01-05` | `05-ui-components/01-layout-components/05-flex/` | [design.md](05-ui-components/01-layout-components/05-flex/design.md) | 5 |
| 05 组件层 | 01 布局类组件 | 06 GridCol | `05-01-06` | `05-ui-components/01-layout-components/06-grid-col/` | [design.md](05-ui-components/01-layout-components/06-grid-col/design.md) | 3 |
| 05 组件层 | 01 布局类组件 | 07 GridRow | `05-01-07` | `05-ui-components/01-layout-components/07-grid-row/` | [design.md](05-ui-components/01-layout-components/07-grid-row/design.md) | 4 |
| 05 组件层 | 01 布局类组件 | 08 RelativeContainer | `05-01-08` | `05-ui-components/01-layout-components/08-relative-container/` | [design.md](05-ui-components/01-layout-components/08-relative-container/design.md) | 5 |
| 05 组件层 | 01 布局类组件 | 09 Row | `05-01-09` | `05-ui-components/01-layout-components/09-row/` | [design.md](05-ui-components/01-layout-components/09-row/design.md) | 4 |
| 05 组件层 | 01 布局类组件 | 10 RowSplit | `05-01-10` | `05-ui-components/01-layout-components/10-row-split/` | [design.md](05-ui-components/01-layout-components/10-row-split/design.md) | 2 |
| 05 组件层 | 01 布局类组件 | 11 Stack | `05-01-11` | `05-ui-components/01-layout-components/11-stack/` | [design.md](05-ui-components/01-layout-components/11-stack/design.md) | 3 |
| 05 组件层 | 01 布局类组件 | 12 FolderStack | `05-01-12` | `05-ui-components/01-layout-components/12-folder-stack/` | [design.md](05-ui-components/01-layout-components/12-folder-stack/design.md) | 3 |
| 05 组件层 | 01 布局类组件 | 13 DynamicLayout | `05-01-13` | `05-ui-components/01-layout-components/13-dynamic-layout/` | [design.md](05-ui-components/01-layout-components/13-dynamic-layout/design.md) | 4 |
| 05 组件层 | 02 导航类组件 | 01 Navigation | `05-02-01` | `05-ui-components/02-navigation-components/01-navigation/` | [design.md](05-ui-components/02-navigation-components/01-navigation/design.md) | 7 |
| 05 组件层 | 02 导航类组件 | 02 NavRouter | `05-02-02` | `05-ui-components/02-navigation-components/02-nav-router/` | *待补充* | 0 |
| 05 组件层 | 02 导航类组件 | 03 NavDestination | `05-02-03` | `05-ui-components/02-navigation-components/03-nav-destination/` | [design.md](05-ui-components/02-navigation-components/03-nav-destination/design.md) | 4 |
| 05 组件层 | 02 导航类组件 | 04 Stepper/SetpperItem | `05-02-04` | `05-ui-components/02-navigation-components/04-stepper-stepper-item/` | *待补充* | 0 |
| 05 组件层 | 02 导航类组件 | 05 Navigator | `05-02-05` | `05-ui-components/02-navigation-components/05-navigator/` | *待补充* | 0 |
| 05 组件层 | 02 导航类组件 | 06 SideBarContainer | `05-02-06` | `05-ui-components/02-navigation-components/06-sidebar-container/` | [design.md](05-ui-components/02-navigation-components/06-sidebar-container/design.md) | 1 |
| 05 组件层 | 03 滚动容器类组件 | 01 滚动公共能力 | `05-03-01` | `05-ui-components/03-scroll-container-components/01-scroll-common-capability/` | [design.md](05-ui-components/03-scroll-container-components/01-scroll-common-capability/design.md) | 4 |
| 05 组件层 | 03 滚动容器类组件 | 02 AlaphabetIndexer | `05-03-02` | `05-ui-components/03-scroll-container-components/02-alphabet-indexer/` | [design.md](05-ui-components/03-scroll-container-components/02-alphabet-indexer/design.md) | 2 |
| 05 组件层 | 03 滚动容器类组件 | 03 ScrollBar | `05-03-03` | `05-ui-components/03-scroll-container-components/03-scroll-bar/` | [design.md](05-ui-components/03-scroll-container-components/03-scroll-bar/design.md) | 2 |
| 05 组件层 | 03 滚动容器类组件 | 04 Grid/GridItem | `05-03-04` | `05-ui-components/03-scroll-container-components/04-grid-grid-item/` | [design.md](05-ui-components/03-scroll-container-components/04-grid-grid-item/design.md) | 6 |
| 05 组件层 | 03 滚动容器类组件 | 05 List/ListItem/ListItemGroup | `05-03-05` | `05-ui-components/03-scroll-container-components/05-list-list-item-list-item-group/` | [design.md](05-ui-components/03-scroll-container-components/05-list-list-item-list-item-group/design.md) | 7 |
| 05 组件层 | 03 滚动容器类组件 | 06 Refresh | `05-03-06` | `05-ui-components/03-scroll-container-components/06-refresh/` | [design.md](05-ui-components/03-scroll-container-components/06-refresh/design.md) | 2 |
| 05 组件层 | 03 滚动容器类组件 | 07 Scroll | `05-03-07` | `05-ui-components/03-scroll-container-components/07-scroll/` | [design.md](05-ui-components/03-scroll-container-components/07-scroll/design.md) | 7 |
| 05 组件层 | 03 滚动容器类组件 | 08 Swiper | `05-03-08` | `05-ui-components/03-scroll-container-components/08-swiper/` | [design.md](05-ui-components/03-scroll-container-components/08-swiper/design.md) | 6 |
| 05 组件层 | 03 滚动容器类组件 | 09 Tabs/TabContent | `05-03-09` | `05-ui-components/03-scroll-container-components/09-tabs-tab-content/` | [design.md](05-ui-components/03-scroll-container-components/09-tabs-tab-content/design.md) | 6 |
| 05 组件层 | 03 滚动容器类组件 | 10 WaterFlow/FlowItem | `05-03-10` | `05-ui-components/03-scroll-container-components/10-water-flow-flow-item/` | [design.md](05-ui-components/03-scroll-container-components/10-water-flow-flow-item/design.md) | 6 |
| 05 组件层 | 04 输入表单类 | 01 Button | `05-04-01` | `05-ui-components/04-input-form-components/01-button/` | [design.md](05-ui-components/04-input-form-components/01-button/design.md) | 1 |
| 05 组件层 | 04 输入表单类 | 02 Checkbox/CheckboxGroup | `05-04-02` | `05-ui-components/04-input-form-components/02-checkbox-checkbox-group/` | [design.md](05-ui-components/04-input-form-components/02-checkbox-checkbox-group/design.md) | 1 |
| 05 组件层 | 04 输入表单类 | 03 Rating | `05-04-03` | `05-ui-components/04-input-form-components/03-rating/` | [design.md](05-ui-components/04-input-form-components/03-rating/design.md) | 1 |
| 05 组件层 | 04 输入表单类 | 04 Radio | `05-04-04` | `05-ui-components/04-input-form-components/04-radio/` | [design.md](05-ui-components/04-input-form-components/04-radio/design.md) | 1 |
| 05 组件层 | 04 输入表单类 | 05 Slider | `05-04-05` | `05-ui-components/04-input-form-components/05-slider/` | [design.md](05-ui-components/04-input-form-components/05-slider/design.md) | 4 |
| 05 组件层 | 04 输入表单类 | 06 Toggle | `05-04-06` | `05-ui-components/04-input-form-components/06-toggle/` | [design.md](05-ui-components/04-input-form-components/06-toggle/design.md) | 1 |
| 05 组件层 | 05 选择类组件 | 01 Calendar/CalendarPicker | `05-05-01` | `05-ui-components/05-picker-components/01-calendar-calendar-picker/` | [design.md](05-ui-components/05-picker-components/01-calendar-calendar-picker/design.md) | 1 |
| 05 组件层 | 05 选择类组件 | 02 DatePicker | `05-05-02` | `05-ui-components/05-picker-components/02-date-picker/` | [design.md](05-ui-components/05-picker-components/02-date-picker/design.md) | 1 |
| 05 组件层 | 05 选择类组件 | 03 TextPicker | `05-05-03` | `05-ui-components/05-picker-components/03-text-picker/` | [design.md](05-ui-components/05-picker-components/03-text-picker/design.md) | 1 |
| 05 组件层 | 05 选择类组件 | 04 TimePicker | `05-05-04` | `05-ui-components/05-picker-components/04-time-picker/` | [design.md](05-ui-components/05-picker-components/04-time-picker/design.md) | 1 |
| 05 组件层 | 05 选择类组件 | 05 Select | `05-05-05` | `05-ui-components/05-picker-components/05-select/` | [design.md](05-ui-components/05-picker-components/05-select/design.md) | 1 |
| 05 组件层 | 05 选择类组件 | 06 Picker | `05-05-06` | `05-ui-components/05-picker-components/06-picker/` | [design.md](05-ui-components/05-picker-components/06-picker/design.md) | 1 |
| 05 组件层 | 06 弹窗类组件 | 01 Menu/MenuItem/MenuItemGroup | `05-06-01` | `05-ui-components/06-popup-components/01-menu-menu-item-menu-item-group/` | [design.md](05-ui-components/06-popup-components/01-menu-menu-item-menu-item-group/design.md) | 3 |
| 05 组件层 | 06 弹窗类组件 | 02 警告弹窗 | `05-06-02` | `05-ui-components/06-popup-components/02-alert-dialog/` | [design.md](05-ui-components/06-popup-components/02-alert-dialog/design.md) | 1 |
| 05 组件层 | 06 弹窗类组件 | 03 列表选择弹窗 | `05-06-03` | `05-ui-components/06-popup-components/03-list-selection-dialog/` | [design.md](05-ui-components/06-popup-components/03-list-selection-dialog/design.md) | 1 |
| 05 组件层 | 06 弹窗类组件 | 04 自定义弹窗 | `05-06-04` | `05-ui-components/06-popup-components/04-custom-dialog/` | [design.md](05-ui-components/06-popup-components/04-custom-dialog/design.md) | 3 |
| 05 组件层 | 06 弹窗类组件 | 05 CalendarPickerDialog | `05-06-05` | `05-ui-components/06-popup-components/05-calendar-picker-dialog/` | [design.md](05-ui-components/06-popup-components/05-calendar-picker-dialog/design.md) | 1 |
| 05 组件层 | 06 弹窗类组件 | 06 DatePickerDialog | `05-06-06` | `05-ui-components/06-popup-components/06-date-picker-dialog/` | [design.md](05-ui-components/06-popup-components/06-date-picker-dialog/design.md) | 1 |
| 05 组件层 | 06 弹窗类组件 | 07 TimePickerDialog | `05-06-07` | `05-ui-components/06-popup-components/07-time-picker-dialog/` | [design.md](05-ui-components/06-popup-components/07-time-picker-dialog/design.md) | 1 |
| 05 组件层 | 06 弹窗类组件 | 08 TextPickerDialog | `05-06-08` | `05-ui-components/06-popup-components/08-text-picker-dialog/` | [design.md](05-ui-components/06-popup-components/08-text-picker-dialog/design.md) | 1 |
| 05 组件层 | 06 弹窗类组件 | 09 ContextMenu接口 | `05-06-09` | `05-ui-components/06-popup-components/09-context-menu/` | [design.md](05-ui-components/06-popup-components/09-context-menu/design.md) | 1 |
| 05 组件层 | 06 弹窗类组件 | 10 promptAction接口 | `05-06-10` | `05-ui-components/06-popup-components/10-prompt-action/` | [design.md](05-ui-components/06-popup-components/10-prompt-action/design.md) | 1 |
| 05 组件层 | 06 弹窗类组件 | 11 popup弹窗 | `05-06-11` | `05-ui-components/06-popup-components/11-popup/` | [design.md](05-ui-components/06-popup-components/11-popup/design.md) | 2 |
| 05 组件层 | 07 模态类组件 | 01 半模态弹窗 | `05-07-01` | `05-ui-components/07-modal-components/01-sheet-modal/` | [design.md](05-ui-components/07-modal-components/01-sheet-modal/design.md) | 1 |
| 05 组件层 | 07 模态类组件 | 02 全模态弹窗 | `05-07-02` | `05-ui-components/07-modal-components/02-full-modal/` | [design.md](05-ui-components/07-modal-components/02-full-modal/design.md) | 1 |
| 05 组件层 | 07 模态类组件 | 03 Panel | `05-07-03` | `05-ui-components/07-modal-components/03-panel/` | *待补充* | 0 |
| 05 组件层 | 08 图片类组件 | 01 Image | `05-08-01` | `05-ui-components/08-image-components/01-image/` | [design.md](05-ui-components/08-image-components/01-image/design.md) | 5 |
| 05 组件层 | 08 图片类组件 | 02 ImageAnimator | `05-08-02` | `05-ui-components/08-image-components/02-image-animator/` | [design.md](05-ui-components/08-image-components/02-image-animator/design.md) | 3 |
| 05 组件层 | 08 图片类组件 | 03 MediaCachedImage | `05-08-03` | `05-ui-components/08-image-components/03-media-cached-image/` | *待补充* | 0 |
| 05 组件层 | 09 文本类组件 | 01 Marquee | `05-09-01` | `05-ui-components/09-text-components/01-marquee/` | *待补充* | 0 |
| 05 组件层 | 09 文本类组件 | 02 RichEditor | `05-09-02` | `05-ui-components/09-text-components/02-rich-editor/` | [design.md](05-ui-components/09-text-components/02-rich-editor/design.md) | 9 |
| 05 组件层 | 09 文本类组件 | 03 Search | `05-09-03` | `05-ui-components/09-text-components/03-search/` | *待补充* | 0 |
| 05 组件层 | 09 文本类组件 | 04 Text | `05-09-04` | `05-ui-components/09-text-components/04-text/` | [design.md](05-ui-components/09-text-components/04-text/design.md) | 7 |
| 05 组件层 | 09 文本类组件 | 05 TextArea | `05-09-05` | `05-ui-components/09-text-components/05-text-area/` | *待补充* | 0 |
| 05 组件层 | 09 文本类组件 | 06 Span类 | `05-09-06` | `05-ui-components/09-text-components/06-span-components/` | *待补充* | 0 |
| 05 组件层 | 09 文本类组件 | 07 SymbolGlyph | `05-09-07` | `05-ui-components/09-text-components/07-symbol-glyph/` | [design.md](05-ui-components/09-text-components/07-symbol-glyph/design.md) | 8 |
| 05 组件层 | 09 文本类组件 | 08 TextInput | `05-09-08` | `05-ui-components/09-text-components/08-text-input/` | [design.md](05-ui-components/09-text-components/08-text-input/design.md) | 10 |
| 05 组件层 | 09 文本类组件 | 09 HyperLink | `05-09-09` | `05-ui-components/09-text-components/09-hyperlink/` | [design.md](05-ui-components/09-text-components/09-hyperlink/design.md) | 3 |
| 05 组件层 | 09 文本类组件 | 10 属性字符串 | `05-09-10` | `05-ui-components/09-text-components/10-attributed-string/` | [design.md](05-ui-components/09-text-components/10-attributed-string/design.md) | 9 |
| 05 组件层 | 10 信息展示类组件 | 01 DataPanel | `05-10-01` | `05-ui-components/10-information-display-components/01-data-panel/` | *待补充* | 0 |
| 05 组件层 | 10 信息展示类组件 | 02 Gauge | `05-10-02` | `05-ui-components/10-information-display-components/02-gauge/` | *待补充* | 0 |
| 05 组件层 | 10 信息展示类组件 | 03 LoadingProgress | `05-10-03` | `05-ui-components/10-information-display-components/03-loading-progress/` | *待补充* | 0 |
| 05 组件层 | 10 信息展示类组件 | 04 PatternLock | `05-10-04` | `05-ui-components/10-information-display-components/04-pattern-lock/` | *待补充* | 0 |
| 05 组件层 | 10 信息展示类组件 | 05 Progress | `05-10-05` | `05-ui-components/10-information-display-components/05-progress/` | *待补充* | 0 |
| 05 组件层 | 10 信息展示类组件 | 06 QRCode | `05-10-06` | `05-ui-components/10-information-display-components/06-qr-code/` | *待补充* | 0 |
| 05 组件层 | 10 信息展示类组件 | 07 TextClock | `05-10-07` | `05-ui-components/10-information-display-components/07-text-clock/` | *待补充* | 0 |
| 05 组件层 | 10 信息展示类组件 | 08 TextTimer | `05-10-08` | `05-ui-components/10-information-display-components/08-text-timer/` | *待补充* | 0 |
| 05 组件层 | 10 信息展示类组件 | 09 Badge | `05-10-09` | `05-ui-components/10-information-display-components/09-badge/` | *待补充* | 0 |
| 05 组件层 | 10 信息展示类组件 | 10 Counter | `05-10-10` | `05-ui-components/10-information-display-components/10-counter/` | *待补充* | 0 |
| 05 组件层 | 11 卡片框架组件 | 01 FormComponent | `05-11-01` | `05-ui-components/11-card-framework-components/01-form-component/` | *待补充* | 0 |
| 05 组件层 | 11 卡片框架组件 | 02 FormLink | `05-11-02` | `05-ui-components/11-card-framework-components/02-form-link/` | *待补充* | 0 |
| 05 组件层 | 12 显示嵌入组件 | 01 PluginComponent | `05-12-01` | `05-ui-components/12-embedded-display-components/01-plugin-component/` | *待补充* | 0 |
| 05 组件层 | 12 显示嵌入组件 | 02 AbilityComponent | `05-12-02` | `05-ui-components/12-embedded-display-components/02-ability-component/` | [design.md](05-ui-components/12-embedded-display-components/02-ability-component/design.md) | 1 |
| 05 组件层 | 12 显示嵌入组件 | 03 UIExtensionComponent | `05-12-03` | `05-ui-components/12-embedded-display-components/03-ui-extension-component/` | *待补充* | 0 |
| 05 组件层 | 12 显示嵌入组件 | 04 EmbeddedComponent | `05-12-04` | `05-ui-components/12-embedded-display-components/04-embedded-component/` | *待补充* | 0 |
| 05 组件层 | 12 显示嵌入组件 | 05 IsolatedComponent | `05-12-05` | `05-ui-components/12-embedded-display-components/05-isolated-component/` | *待补充* | 0 |
| 05 组件层 | 12 显示嵌入组件 | 06 SecurityUIExtensionComponent | `05-12-06` | `05-ui-components/12-embedded-display-components/06-security-ui-extension-component/` | *待补充* | 0 |
| 05 组件层 | 12 显示嵌入组件 | 07 DynamicComponent | `05-12-07` | `05-ui-components/12-embedded-display-components/07-dynamic-component/` | *待补充* | 0 |
| 05 组件层 | 13 平台类组件 | 01 XComponent | `05-13-01` | `05-ui-components/13-platform-components/01-xcomponent/` | [design.md](05-ui-components/13-platform-components/01-xcomponent/design.md) | 8 |
| 05 组件层 | 13 平台类组件 | 02 Video | `05-13-02` | `05-ui-components/13-platform-components/02-video/` | [design.md](05-ui-components/13-platform-components/02-video/design.md) | 3 |
| 05 组件层 | 14 绘制类组件 | 01 Shape | `05-14-01` | `05-ui-components/14-drawing-components/01-shape/` | [design.md](05-ui-components/14-drawing-components/01-shape/design.md) | 6 |
| 05 组件层 | 14 绘制类组件 | 02 Canvas | `05-14-02` | `05-ui-components/14-drawing-components/02-canvas/` | [design.md](05-ui-components/14-drawing-components/02-canvas/design.md) | 7 |
| 05 组件层 | 14 绘制类组件 | 03 OffscreenCanvas | `05-14-03` | `05-ui-components/14-drawing-components/03-offscreen-canvas/` | [design.md](05-ui-components/14-drawing-components/03-offscreen-canvas/design.md) | 3 |
| 05 组件层 | 15 主题组件 | 01 WithTheme | `05-15-01` | `05-ui-components/15-theme-components/01-with-theme/` | [design.md](05-ui-components/15-theme-components/01-with-theme/design.md) | 1 |
| 05 组件层 | 16 自定义占位组件 | 01 NodeContainer | `05-16-01` | `05-ui-components/16-custom-placeholder-components/01-node-container/` | [design.md](05-ui-components/16-custom-placeholder-components/01-node-container/design.md) | 3 |
| 05 组件层 | 16 自定义占位组件 | 02 ContentSlot | `05-16-02` | `05-ui-components/16-custom-placeholder-components/02-content-slot/` | [design.md](05-ui-components/16-custom-placeholder-components/02-content-slot/design.md) | 1 |
| 06 通用接口层 | 01 前端桥接 | 01 跨语言封装 | `06-01-01` | `06-common-interface/01-frontend-bridge/01-cross-language-wrapper/` | *待补充* | 0 |
| 06 通用接口层 | 01 前端桥接 | 02 JS引擎管理 | `06-01-02` | `06-common-interface/01-frontend-bridge/02-js-engine-management/` | *待补充* | 0 |
| 06 通用接口层 | 01 前端桥接 | 03 IDL工具 | `06-01-03` | `06-common-interface/01-frontend-bridge/03-idl-tool/` | *待补充* | 0 |
| 06 通用接口层 | 02 Inner接口 | 01 Inner-组件能力接口 | `06-02-01` | `06-common-interface/02-inner-interface/01-inner-component-interface/` | *待补充* | 0 |
| 06 通用接口层 | 02 Inner接口 | 02 Inner-基础能力接口 | `06-02-02` | `06-common-interface/02-inner-interface/02-inner-basic-interface/` | *待补充* | 0 |
| 06 通用接口层 | 03 其它范式接入 | 01 类Web范式 | `06-03-01` | `06-common-interface/03-paradigm-integration/01-web-like-paradigm/` | *待补充* | 0 |
| 06 通用接口层 | 03 其它范式接入 | 02 ArkTS卡片 | `06-03-02` | `06-common-interface/03-paradigm-integration/02-arkts-card/` | *待补充* | 0 |
| 06 通用接口层 | 03 其它范式接入 | 03 JS卡片 | `06-03-03` | `06-common-interface/03-paradigm-integration/03-js-card/` | *待补充* | 0 |
| 06 通用接口层 | 03 其它范式接入 | 04 FA模型 | `06-03-04` | `06-common-interface/03-paradigm-integration/04-fa-model/` | *待补充* | 0 |
| 06 通用接口层 | 03 其它范式接入 | 05 仓颉接入层 | `06-03-05` | `06-common-interface/03-paradigm-integration/05-cangjie-integration/` | *待补充* | 0 |
| 07 前端层 | 01 ArkTS高级组件 | 01 Chip | `07-01-01` | `07-frontend/01-arkts-advanced-components/01-chip/` | *待补充* | 0 |
| 07 前端层 | 01 ArkTS高级组件 | 02 ChipGroup | `07-01-02` | `07-frontend/01-arkts-advanced-components/02-chip-group/` | *待补充* | 0 |
| 07 前端层 | 01 ArkTS高级组件 | 03 ComposeListItem | `07-01-03` | `07-frontend/01-arkts-advanced-components/03-compose-list-item/` | *待补充* | 0 |
| 07 前端层 | 01 ArkTS高级组件 | 04 ComposeTitleBar | `07-01-04` | `07-frontend/01-arkts-advanced-components/04-compose-title-bar/` | *待补充* | 0 |
| 07 前端层 | 01 ArkTS高级组件 | 05 Counter | `07-01-05` | `07-frontend/01-arkts-advanced-components/05-counter/` | *待补充* | 0 |
| 07 前端层 | 01 ArkTS高级组件 | 06 Dialog | `07-01-06` | `07-frontend/01-arkts-advanced-components/06-dialog/` | *待补充* | 0 |
| 07 前端层 | 01 ArkTS高级组件 | 07 DownloadFileButton | `07-01-07` | `07-frontend/01-arkts-advanced-components/07-download-file-button/` | *待补充* | 0 |
| 07 前端层 | 01 ArkTS高级组件 | 08 EditableTitleBar | `07-01-08` | `07-frontend/01-arkts-advanced-components/08-editable-title-bar/` | *待补充* | 0 |
| 07 前端层 | 01 ArkTS高级组件 | 09 ExceptionPrompt | `07-01-09` | `07-frontend/01-arkts-advanced-components/09-exception-prompt/` | *待补充* | 0 |
| 07 前端层 | 01 ArkTS高级组件 | 10 Filter | `07-01-10` | `07-frontend/01-arkts-advanced-components/10-filter/` | *待补充* | 0 |
| 07 前端层 | 01 ArkTS高级组件 | 11 FormMenu | `07-01-11` | `07-frontend/01-arkts-advanced-components/11-form-menu/` | *待补充* | 0 |
| 07 前端层 | 01 ArkTS高级组件 | 12 ProgressButton | `07-01-12` | `07-frontend/01-arkts-advanced-components/12-progress-button/` | *待补充* | 0 |
| 07 前端层 | 01 ArkTS高级组件 | 13 FullScreenLaunchComponent | `07-01-13` | `07-frontend/01-arkts-advanced-components/13-full-screen-launch-component/` | *待补充* | 0 |
| 07 前端层 | 01 ArkTS高级组件 | 14 GridObjectSortComponent | `07-01-14` | `07-frontend/01-arkts-advanced-components/14-grid-object-sort-component/` | *待补充* | 0 |
| 07 前端层 | 01 ArkTS高级组件 | 15 ProgressButton | `07-01-15` | `07-frontend/01-arkts-advanced-components/15-progress-button/` | *待补充* | 0 |
| 07 前端层 | 01 ArkTS高级组件 | 16 Popup | `07-01-16` | `07-frontend/01-arkts-advanced-components/16-popup/` | [design.md](07-frontend/01-arkts-advanced-components/16-popup/design.md) | 1 |
| 07 前端层 | 01 ArkTS高级组件 | 17 SegmentButton | `07-01-17` | `07-frontend/01-arkts-advanced-components/17-segment-button/` | *待补充* | 0 |
| 07 前端层 | 01 ArkTS高级组件 | 18 SelectionMenu | `07-01-18` | `07-frontend/01-arkts-advanced-components/18-selection-menu/` | *待补充* | 0 |
| 07 前端层 | 01 ArkTS高级组件 | 19 SelectTitleBar | `07-01-19` | `07-frontend/01-arkts-advanced-components/19-select-title-bar/` | *待补充* | 0 |
| 07 前端层 | 01 ArkTS高级组件 | 20 SplitLayout | `07-01-20` | `07-frontend/01-arkts-advanced-components/20-split-layout/` | *待补充* | 0 |
| 07 前端层 | 01 ArkTS高级组件 | 21 SubHeader | `07-01-21` | `07-frontend/01-arkts-advanced-components/21-sub-header/` | *待补充* | 0 |
| 07 前端层 | 01 ArkTS高级组件 | 22 SwipeRefresher | `07-01-22` | `07-frontend/01-arkts-advanced-components/22-swipe-refresher/` | *待补充* | 0 |
| 07 前端层 | 01 ArkTS高级组件 | 23 TabTitleBar | `07-01-23` | `07-frontend/01-arkts-advanced-components/23-tab-title-bar/` | *待补充* | 0 |
| 07 前端层 | 01 ArkTS高级组件 | 24 ToolBar | `07-01-24` | `07-frontend/01-arkts-advanced-components/24-tool-bar/` | *待补充* | 0 |
| 07 前端层 | 01 ArkTS高级组件 | 25 TreeView | `07-01-25` | `07-frontend/01-arkts-advanced-components/25-tree-view/` | *待补充* | 0 |
| 07 前端层 | 01 ArkTS高级组件 | 26 FoldSplitContainer | `07-01-26` | `07-frontend/01-arkts-advanced-components/26-fold-split-container/` | *待补充* | 0 |
| 07 前端层 | 02 状态管理框架 | 01 状态管理V1组件内状态管理 | `07-02-01` | `07-frontend/02-state-management/01-v1-component-state/` | [design.md](07-frontend/02-state-management/01-v1-component-state/design.md) | 9 |
| 07 前端层 | 02 状态管理框架 | 02 状态管理V1数据对象内状态管理 | `07-02-02` | `07-frontend/02-state-management/02-v1-data-object-state/` | [design.md](07-frontend/02-state-management/02-v1-data-object-state/design.md) | 1 |
| 07 前端层 | 02 状态管理框架 | 03 状态管理V1应用内状态管理 | `07-02-03` | `07-frontend/02-state-management/03-v1-app-state/` | [design.md](07-frontend/02-state-management/03-v1-app-state/design.md) | 4 |
| 07 前端层 | 02 状态管理框架 | 04 状态管理V2组件内状态管理 | `07-02-04` | `07-frontend/02-state-management/04-v2-component-state/` | [design.md](07-frontend/02-state-management/04-v2-component-state/design.md) | 5 |
| 07 前端层 | 02 状态管理框架 | 05 状态管理V2数据对象内状态管理 | `07-02-05` | `07-frontend/02-state-management/05-v2-data-object-state/` | [design.md](07-frontend/02-state-management/05-v2-data-object-state/design.md) | 2 |
| 07 前端层 | 02 状态管理框架 | 06 状态管理V2应用内状态管理 | `07-02-06` | `07-frontend/02-state-management/06-v2-app-state/` | [design.md](07-frontend/02-state-management/06-v2-app-state/design.md) | 2 |
| 07 前端层 | 02 状态管理框架 | 07 状态管理辅助接口 | `07-02-07` | `07-frontend/02-state-management/07-state-management-utilities/` | [design.md](07-frontend/02-state-management/07-state-management-utilities/design.md) | 2 |
| 07 前端层 | 02 状态管理框架 | 08 静态V1组件内状态管理 | `07-02-08` | `07-frontend/02-state-management/08-static-v1-component-state/` | [design.md](07-frontend/02-state-management/08-static-v1-component-state/design.md) | 6 |
| 07 前端层 | 02 状态管理框架 | 09 静态V1数据对象内状态管理 | `07-02-09` | `07-frontend/02-state-management/09-static-v1-data-object-state/` | [design.md](07-frontend/02-state-management/09-static-v1-data-object-state/design.md) | 2 |
| 07 前端层 | 02 状态管理框架 | 10 静态V1应用内状态管理 | `07-02-10` | `07-frontend/02-state-management/10-static-v1-app-state/` | [design.md](07-frontend/02-state-management/10-static-v1-app-state/design.md) | 5 |
| 07 前端层 | 02 状态管理框架 | 11 静态V2组件内状态管理 | `07-02-11` | `07-frontend/02-state-management/11-static-v2-component-state/` | [design.md](07-frontend/02-state-management/11-static-v2-component-state/design.md) | 4 |
| 07 前端层 | 02 状态管理框架 | 12 静态V2数据对象内状态管理 | `07-02-12` | `07-frontend/02-state-management/12-static-v2-data-object-state/` | [design.md](07-frontend/02-state-management/12-static-v2-data-object-state/design.md) | 1 |
| 07 前端层 | 02 状态管理框架 | 13 静态V2应用内状态管理 | `07-02-13` | `07-frontend/02-state-management/13-static-v2-app-state/` | [design.md](07-frontend/02-state-management/13-static-v2-app-state/design.md) | 2 |
| 07 前端层 | 02 状态管理框架 | 14 状态管理互操作 | `07-02-14` | `07-frontend/02-state-management/14-state-management-interop/` | [design.md](07-frontend/02-state-management/14-state-management-interop/design.md) | 5 |
| 07 前端层 | 03 自定义组件 | 01 组件化 | `07-03-01` | `07-frontend/03-custom-components/01-componentization/` | [design.md](07-frontend/03-custom-components/01-componentization/design.md) | 1 |
| 07 前端层 | 03 自定义组件 | 02 自定义组件生命周期 | `07-03-02` | `07-frontend/03-custom-components/02-component-lifecycle/` | [design.md](07-frontend/03-custom-components/02-component-lifecycle/design.md) | 1 |
| 07 前端层 | 03 自定义组件 | 03 自定义组件复用 | `07-03-03` | `07-frontend/03-custom-components/03-component-reuse/` | [design.md](07-frontend/03-custom-components/03-component-reuse/design.md) | 1 |
| 07 前端层 | 03 自定义组件 | 04 自定义组件冻结 | `07-03-04` | `07-frontend/03-custom-components/04-component-freeze/` | [design.md](07-frontend/03-custom-components/04-component-freeze/design.md) | 1 |
| 07 前端层 | 03 自定义组件 | 05 自定义测量/布局 | `07-03-05` | `07-frontend/03-custom-components/05-custom-measure-layout/` | [design.md](07-frontend/03-custom-components/05-custom-measure-layout/design.md) | 1 |
| 07 前端层 | 03 自定义组件 | 06 组件扩展 | `07-03-06` | `07-frontend/03-custom-components/06-component-extension/` | *待补充* | 0 |
| 07 前端层 | 03 自定义组件 | 07 静态自定义组件状态相关 | `07-03-07` | `07-frontend/03-custom-components/07-static-custom-component-state/` | [design.md](07-frontend/03-custom-components/07-static-custom-component-state/design.md) | 0 |
| 07 前端层 | 04 生成式UI | 01 A2UI标准协议 | `07-04-01` | `07-frontend/04-generative-ui/01-a2ui-standard-protocol/` | *待补充* | 0 |
| 07 前端层 | 04 生成式UI | 02 A2UI扩展协议 | `07-04-02` | `07-frontend/04-generative-ui/02-a2ui-extension-protocol/` | *待补充* | 0 |
| 07 前端层 | 04 生成式UI | 03 A2UI高级垂域组件 | `07-04-03` | `07-frontend/04-generative-ui/03-a2ui-advanced-domain-components/` | *待补充* | 0 |
| 07 前端层 | 05 渲染控制 | 01 渲染控制语法 | `07-05-01` | `07-frontend/05-render-control/01-render-control-syntax/` | [design.md](07-frontend/05-render-control/01-render-control-syntax/design.md) | 3 |
| 07 前端层 | 05 渲染控制 | 02 LazyForEach | `07-05-02` | `07-frontend/05-render-control/02-lazy-foreach/` | [design.md](07-frontend/05-render-control/02-lazy-foreach/design.md) | 5 |
| 07 前端层 | 05 渲染控制 | 03 Repeat | `07-05-03` | `07-frontend/05-render-control/03-repeat/` | [design.md](07-frontend/05-render-control/03-repeat/design.md) | 4 |
| 07 前端层 | 06 响应式环境变量 | 01 系统环境变量 | `07-06-01` | `07-frontend/06-reactive-env/01-system-env/` | *待补充* | 0 |
| 07 前端层 | 06 响应式环境变量 | 02 自定义环境变量 | `07-06-02` | `07-frontend/06-reactive-env/02-custom-env/` | *待补充* | 0 |
| 08 NDK | 01 Node C-API | 01 基础机制NativeModule | `08-01-01` | `08-ndk/01-node-c-api/01-native-module-base/` | *待补充* | 0 |
| 08 NDK | 01 Node C-API | 02 组件API | `08-01-02` | `08-ndk/01-node-c-api/02-component-api/` | *待补充* | 0 |
| 08 NDK | 01 Node C-API | 03 动效NativeAnimate | `08-01-03` | `08-ndk/01-node-c-api/03-native-animate/` | *待补充* | 0 |
| 08 NDK | 01 Node C-API | 04 视效接口 | `08-01-04` | `08-ndk/01-node-c-api/04-visual-effect-api/` | *待补充* | 0 |
| 08 NDK | 01 Node C-API | 05 事件EventModule | `08-01-05` | `08-ndk/01-node-c-api/05-event-module/` | *待补充* | 0 |
| 08 NDK | 01 Node C-API | 06 弹窗NativeDialog | `08-01-06` | `08-ndk/01-node-c-api/06-native-dialog/` | *待补充* | 0 |
| 08 NDK | 01 Node C-API | 07 手势NativeGesture | `08-01-07` | `08-ndk/01-node-c-api/07-native-gesture/` | *待补充* | 0 |
| 08 NDK | 01 Node C-API | 08 文本StyledString | `08-01-08` | `08-ndk/01-node-c-api/08-styled-string/` | *待补充* | 0 |
| 08 NDK | 01 Node C-API | 09 绘制DrawableDescriptor | `08-01-09` | `08-ndk/01-node-c-api/09-drawable-descriptor/` | *待补充* | 0 |
| 08 NDK | 01 Node C-API | 10 组件扩展 | `08-01-10` | `08-ndk/01-node-c-api/10-component-extension/` | *待补充* | 0 |
| 08 NDK | 01 Node C-API | 11 布局接口 | `08-01-11` | `08-ndk/01-node-c-api/11-layout-api/` | *待补充* | 0 |
| 08 NDK | 02 XComponent C-API | 01 Native XComponent | `08-02-01` | `08-ndk/02-xcomponent-c-api/01-native-xcomponent/` | *待补充* | 0 |
| 09 开发者工具 | 01 预览器 | 01 组件预览 | `09-01-01` | `09-developer-tools/01-previewer/01-component-preview/` | *待补充* | 0 |
| 09 开发者工具 | 01 预览器 | 02 基础预览 | `09-01-02` | `09-developer-tools/01-previewer/02-basic-preview/` | *待补充* | 0 |
| 09 开发者工具 | 01 预览器 | 03 动态预览 | `09-01-03` | `09-developer-tools/01-previewer/03-dynamic-preview/` | *待补充* | 0 |
| 09 开发者工具 | 01 预览器 | 04 热加载 | `09-01-04` | `09-developer-tools/01-previewer/04-hot-reload/` | *待补充* | 0 |
| 09 开发者工具 | 02 工具链 | 01 工具链 | `09-02-01` | `09-developer-tools/02-toolchain/01-toolchain/` | *待补充* | 0 |
| 09 开发者工具 | 03 开发者文档 | 01 入门指南文档 | `09-03-01` | `09-developer-tools/03-developer-docs/01-getting-started-docs/` | *待补充* | 0 |
| 09 开发者工具 | 03 开发者文档 | 02 API指南文档 | `09-03-02` | `09-developer-tools/03-developer-docs/02-api-guide-docs/` | *待补充* | 0 |
| 09 开发者工具 | 04 Sample应用 | 01 能力示范sample | `09-04-01` | `09-developer-tools/04-sample-apps/01-capability-sample/` | *待补充* | 0 |
| 09 开发者工具 | 05 ComponnetTest | 01 ComponnetTest测试框架 | `09-05-01` | `09-developer-tools/05-component-test/01-component-test-framework/` | *待补充* | 0 |
| 10 产品化定制 | 01 穿戴 | 01 弧形组件 | `10-01-01` | `10-product-customization/01-wearable/01-arc-component/` | [design.md](10-product-customization/01-wearable/01-arc-component/design.md) | 2 |

> 新增功能域时请在此表中按编号顺序添加行；未创建的设计文档以 `待补充` 标记。

---

## 已注册特性清单

### 01-01-01 编译构建

| FeatID | 特性名称 | Spec 文件 | 状态 |
|--------|----------|-----------|------|
| Feat-01 | BUILD.gn 结构 | [Feat-01-build-gn-structure-spec.md](01-architecture/01-architecture-design/01-build-system/Feat-01-build-gn-structure-spec.md) | Baselined |

### 01-01-02 目录结构

| FeatID | 特性名称 | Spec 文件 | 状态 |
|--------|----------|-----------|------|

### 01-01-03 部件化

| FeatID | 特性名称 | Spec 文件 | 状态 |
|--------|----------|-----------|------|

### 01-02-01 产品化解耦

| FeatID | 特性名称 | Spec 文件 | 状态 |
|--------|----------|-----------|------|

### 02-01-01 OH平台适配

| FeatID | 特性名称 | Spec 文件 | 状态 |
|--------|----------|-----------|------|
| Feat-01 | 平台抽象基类与构建适配 | [Feat-01-platform-abstraction-build-spec.md](02-cross-platform/01-platform-adapter/01-oh-platform-adapter/Feat-01-platform-abstraction-build-spec.md) | Baselined |

### 02-01-02 Android平台适配

| FeatID | 特性名称 | Spec 文件 | 状态 |
|--------|----------|-----------|------|

### 02-01-03 iOS平台适配

| FeatID | 特性名称 | Spec 文件 | 状态 |
|--------|----------|-----------|------|

### 02-01-04 预览器平台适配

| FeatID | 特性名称 | Spec 文件 | 状态 |
|--------|----------|-----------|------|
| Feat-01 | 预览器平台发现与构建配置 | [Feat-01-previewer-platform-build-spec.md](02-cross-platform/01-platform-adapter/04-previewer-platform-adapter/Feat-01-previewer-platform-build-spec.md) | Baselined |
| Feat-02 | 预览器运行入口与平台服务替身 | [Feat-02-previewer-runtime-mock-spec.md](02-cross-platform/01-platform-adapter/04-previewer-platform-adapter/Feat-02-previewer-runtime-mock-spec.md) | Baselined |
| Feat-03 | 预览器 SDK 与资源打包 | [Feat-03-previewer-sdk-packaging-spec.md](02-cross-platform/01-platform-adapter/04-previewer-platform-adapter/Feat-03-previewer-sdk-packaging-spec.md) | Baselined |

### 02-02-01 Rosen渲染后端对接

| FeatID | 特性名称 | Spec 文件 | 状态 |
|--------|----------|-----------|------|
| Feat-01 | 渲染后端核心架构 | [Feat-01-render-backend-core-architecture-spec.md](02-cross-platform/02-render-backend-adapter/01-rosen-render-backend-adapter/Feat-01-render-backend-core-architecture-spec.md) | Baselined |
| Feat-02 | 绘制与视效适配 | [Feat-02-drawing-visual-effect-adapter-spec.md](02-cross-platform/02-render-backend-adapter/01-rosen-render-backend-adapter/Feat-02-drawing-visual-effect-adapter-spec.md) | Baselined |
| Feat-03 | 动画桥接适配 | [Feat-03-animation-bridge-adapter-spec.md](02-cross-platform/02-render-backend-adapter/01-rosen-render-backend-adapter/Feat-03-animation-bridge-adapter-spec.md) | Baselined |

### 03-01-01 渲染管线

| FeatID | 特性名称 | Spec 文件 | 状态 |
|--------|----------|-----------|------|
| Feat-01 | 渲染主流程 | [Feat-01-render-main-flow-spec.md](03-engine-framework/01-render-pipeline/01-basic-render-pipeline/Feat-01-render-main-flow-spec.md) | Baselined |

### 03-01-02 多级渲染管线

| FeatID | 特性名称 | Spec 文件 | 状态 |
|--------|----------|-----------|------|
| Feat-01 | 子管线与多容器 VSync 协调 | [Feat-01-sub-pipeline-multi-container-vsync-coordination-spec.md](03-engine-framework/01-render-pipeline/02-multi-level-render-pipeline/Feat-01-sub-pipeline-multi-container-vsync-coordination-spec.md) | Baselined |

### 03-02-01 动效框架

| FeatID | 特性名称 | Spec 文件 | 状态 |
|--------|----------|-----------|------|
| Feat-01 | 动效框架全量规格 | [Feat-01-animation-framework-spec.md](03-engine-framework/02-animation-capability/01-animation-framework/Feat-01-animation-framework-spec.md) | Baselined |

### 03-02-02 属性动画

| FeatID | 特性名称 | Spec 文件 | 状态 |
|--------|----------|-----------|------|
| Feat-01 | 属性动画全量规格 | [Feat-01-property-animation-spec.md](03-engine-framework/02-animation-capability/02-property-animation/Feat-01-property-animation-spec.md) | Baselined |

### 03-02-03 显式动画

| FeatID | 特性名称 | Spec 文件 | 状态 |
|--------|----------|-----------|------|
| Feat-01 | 显式动画全量规格 | [Feat-01-explicit-animation-spec.md](03-engine-framework/02-animation-capability/03-explicit-animation/Feat-01-explicit-animation-spec.md) | Baselined |

### 03-02-04 关键帧动画

| FeatID | 特性名称 | Spec 文件 | 状态 |
|--------|----------|-----------|------|
| Feat-01 | 关键帧动画全量规格 | [Feat-01-keyframe-animation-spec.md](03-engine-framework/02-animation-capability/04-keyframe-animation/Feat-01-keyframe-animation-spec.md) | Baselined |

### 03-02-05 转场动画

| FeatID | 特性名称 | Spec 文件 | 状态 |
|--------|----------|-----------|------|
| Feat-01 | 转场动画全量规格 | [Feat-01-transition-animation-spec.md](03-engine-framework/02-animation-capability/05-transition-animation/Feat-01-transition-animation-spec.md) | Baselined |

### 03-02-06 共享元素动画

| FeatID | 特性名称 | Spec 文件 | 状态 |
|--------|----------|-----------|------|
| Feat-01 | 共享元素动画全量规格 | [Feat-01-shared-transition-spec.md](03-engine-framework/02-animation-capability/06-shared-transition/Feat-01-shared-transition-spec.md) | Baselined |

### 03-02-07 组件共享元素动画

| FeatID | 特性名称 | Spec 文件 | 状态 |
|--------|----------|-----------|------|
| Feat-01 | 组件共享元素动画全量规格 | [Feat-01-geometry-transition-spec.md](03-engine-framework/02-animation-capability/07-geometry-transition/Feat-01-geometry-transition-spec.md) | Baselined |

### 03-02-08 路径动画

| FeatID | 特性名称 | Spec 文件 | 状态 |
|--------|----------|-----------|------|
| Feat-01 | 路径动画全量规格 | [Feat-01-motion-path-spec.md](03-engine-framework/02-animation-capability/08-motion-path/Feat-01-motion-path-spec.md) | Baselined |

### 03-02-09 物理动画

| FeatID | 特性名称 | Spec 文件 | 状态 |
|--------|----------|-----------|------|
| Feat-01 | 物理动画全量规格 | [Feat-01-physics-animation-spec.md](03-engine-framework/02-animation-capability/09-physics-animation/Feat-01-physics-animation-spec.md) | Baselined |

### 03-02-10 动画接口

| FeatID | 特性名称 | Spec 文件 | 状态 |
|--------|----------|-----------|------|
| Feat-01 | 动画接口全量规格 | [Feat-01-animation-interface-spec.md](03-engine-framework/02-animation-capability/10-animation-interface/Feat-01-animation-interface-spec.md) | Baselined |

### 03-03-01 资源访问

| FeatID | 特性名称 | Spec 文件 | 状态 |
|--------|----------|-----------|------|
| Feat-01 | 资源访问内部机制 | [Feat-01-resource-access-spec.md](03-engine-framework/03-resource-theme/01-resource-access/Feat-01-resource-access-spec.md) | Baselined |
| Feat-02 | 资源访问公开能力（$r/$rawfile 解析层） | [Feat-02-resource-public-access-spec.md](03-engine-framework/03-resource-theme/01-resource-access/Feat-02-resource-public-access-spec.md) | Baselined |
| Feat-03 | 资源分层与 Override 适配器 | [Feat-03-resource-override-layering-spec.md](03-engine-framework/03-resource-theme/01-resource-access/Feat-03-resource-override-layering-spec.md) | Baselined |

### 03-03-02 主题分层访问

| FeatID | 特性名称 | Spec 文件 | 状态 |
|--------|----------|-----------|------|
| Feat-01 | 主题分层访问全量规格 | [Feat-01-theme-layered-access-spec.md](03-engine-framework/03-resource-theme/02-theme-layered-access/Feat-01-theme-layered-access-spec.md) | Baselined |

### 03-03-03 Theme框架

| FeatID | 特性名称 | Spec 文件 | 状态 |
|--------|----------|-----------|------|
| Feat-01 | Theme框架全量规格 | [Feat-01-theme-framework-spec.md](03-engine-framework/03-resource-theme/03-theme-framework/Feat-01-theme-framework-spec.md) | Baselined |
| Feat-02 | @ohos.arkui.theme 公开主题 API | [Feat-02-arkui-theme-public-api-spec.md](03-engine-framework/03-resource-theme/03-theme-framework/Feat-02-arkui-theme-public-api-spec.md) | Baselined |

### 03-03-04 资源动态切换

| FeatID | 特性名称 | Spec 文件 | 状态 |
|--------|----------|-----------|------|
| Feat-01 | 资源动态切换全量规格 | [Feat-01-resource-dynamic-switching-spec.md](03-engine-framework/03-resource-theme/04-resource-dynamic-switching/Feat-01-resource-dynamic-switching-spec.md) | Baselined |

### 03-04-01 事件基础框架

| FeatID | 特性名称 | Spec 文件 | 状态 |
|--------|----------|-----------|------|

### 03-04-02 拖拽框架

| FeatID | 特性名称 | Spec 文件 | 状态 |
|--------|----------|-----------|------|

### 03-05-01 窗口机制

| FeatID | 特性名称 | Spec 文件 | 状态 |
|--------|----------|-----------|------|
| Feat-01 | Window抽象与RosenWindow创建初始化 | [Feat-01-window-abstraction-rosen-window-init-spec.md](03-engine-framework/05-window-mechanism/01-window-mechanism/Feat-01-window-abstraction-rosen-window-init-spec.md) | Baselined |
| Feat-02 | 窗口生命周期与前后台状态转换 | [Feat-02-window-lifecycle-state-transition-spec.md](03-engine-framework/05-window-mechanism/01-window-mechanism/Feat-02-window-lifecycle-state-transition-spec.md) | Baselined |
| Feat-03 | 多实例窗口与全局管线 | [Feat-03-multi-instance-global-pipeline-spec.md](03-engine-framework/05-window-mechanism/01-window-mechanism/Feat-03-multi-instance-global-pipeline-spec.md) | Baselined |
| Feat-04 | 特殊窗口类型 | [Feat-04-special-window-types-spec.md](03-engine-framework/05-window-mechanism/01-window-mechanism/Feat-04-special-window-types-spec.md) | Baselined |

### 03-05-02 子窗机制

| FeatID | 特性名称 | Spec 文件 | 状态 |
|--------|----------|-----------|------|
| Feat-01 | 子窗抽象与 Manager 核心 | [Feat-01-subwindow-mechanism-spec.md](03-engine-framework/05-window-mechanism/02-subwindow-mechanism/Feat-01-subwindow-mechanism-spec.md) | Baselined |
| Feat-02 | 子窗类型路由与弹窗状态机 | [Feat-02-subwindow-routing-state-spec.md](03-engine-framework/05-window-mechanism/02-subwindow-mechanism/Feat-02-subwindow-routing-state-spec.md) | Baselined |
| Feat-03 | 子窗布局交互与多端适配 | [Feat-03-subwindow-layout-adaptation-spec.md](03-engine-framework/05-window-mechanism/02-subwindow-mechanism/Feat-03-subwindow-layout-adaptation-spec.md) | Baselined |

### 03-06-01 多实例管理

| FeatID | 特性名称 | Spec 文件 | 状态 |
|--------|----------|-----------|------|
| Feat-01 | 多实例管理全能力 | [Feat-01-multi-instance-management-spec.md](03-engine-framework/06-multi-instance-management/01-multi-instance-management/Feat-01-multi-instance-management-spec.md) | Baselined |

### 03-07-01 无障碍能力

| FeatID | 特性名称 | Spec 文件 | 状态 |
|--------|----------|-----------|------|

### 03-07-02 Inspector

| FeatID | 特性名称 | Spec 文件 | 状态 |
|--------|----------|-----------|------|

### 03-08-01 日志

| FeatID | 特性名称 | Spec 文件 | 状态 |
|--------|----------|-----------|------|
| Feat-01 | LogWrapper核心框架与HiLog适配 | [Feat-01-log-wrapper-core-spec.md](03-engine-framework/08-dfx-foundation/01-logging/Feat-01-log-wrapper-core-spec.md) | Baselined |
| Feat-02 | 日志控制开关与前端日志桥接 | [Feat-02-log-control-frontend-bridge-spec.md](03-engine-framework/08-dfx-foundation/01-logging/Feat-02-log-control-frontend-bridge-spec.md) | Baselined |
| Feat-03 | HiSysEvent事件上报与异常诊断 | [Feat-03-hisysevent-report-spec.md](03-engine-framework/08-dfx-foundation/01-logging/Feat-03-hisysevent-report-spec.md) | Baselined |

### 03-08-02 内存管理

| FeatID | 特性名称 | Spec 文件 | 状态 |
|--------|----------|-----------|------|
| Feat-01 | RefPtr/WeakPtr/AceType引用计数智能指针 | [Feat-01-refptr-weakptr-ace-type-spec.md](03-engine-framework/08-dfx-foundation/02-memory-management/Feat-01-refptr-weakptr-ace-type-spec.md) | Baselined |
| Feat-02 | MemoryMonitor调试分配监控 | [Feat-02-memory-monitor-spec.md](03-engine-framework/08-dfx-foundation/02-memory-management/Feat-02-memory-monitor-spec.md) | Baselined |
| Feat-03 | NG MemoryManager内存回收管线 | [Feat-03-ng-memory-manager-recycle-spec.md](03-engine-framework/08-dfx-foundation/02-memory-management/Feat-03-ng-memory-manager-recycle-spec.md) | Baselined |
| Feat-04 | 系统内存压力监听与全局GC | [Feat-04-memory-pressure-global-gc-spec.md](03-engine-framework/08-dfx-foundation/02-memory-management/Feat-04-memory-pressure-global-gc-spec.md) | Baselined |

### 03-08-03 Trace打点

| FeatID | 特性名称 | Spec 文件 | 状态 |
|--------|----------|-----------|------|
| Feat-01 | ACE Trace核心框架与FrameTrace适配 | [Feat-01-ace-trace-core-frame-trace-spec.md](03-engine-framework/08-dfx-foundation/03-trace/Feat-01-ace-trace-core-frame-trace-spec.md) | Baselined |
| Feat-02 | 帧调度报告与Jank检测 | [Feat-02-frame-report-jank-spec.md](03-engine-framework/08-dfx-foundation/03-trace/Feat-02-frame-report-jank-spec.md) | Baselined |
| Feat-03 | 性能检查与阈值监控 | [Feat-03-perf-check-threshold-spec.md](03-engine-framework/08-dfx-foundation/03-trace/Feat-03-perf-check-threshold-spec.md) | Baselined |

### 03-08-04 Dump机制

| FeatID | 特性名称 | Spec 文件 | 状态 |
|--------|----------|-----------|------|
| Feat-01 | DumpLog核心引擎与Pipeline命令路由 | [Feat-01-dump-log-pipeline-routing-spec.md](03-engine-framework/08-dfx-foundation/04-dump-mechanism/Feat-01-dump-log-pipeline-routing-spec.md) | Baselined |
| Feat-02 | Inspector树形诊断系统 | [Feat-02-inspector-tree-diagnostic-spec.md](03-engine-framework/08-dfx-foundation/04-dump-mechanism/Feat-02-inspector-tree-diagnostic-spec.md) | Baselined |
| Feat-03 | SimplifiedInspector与简化树 | [Feat-03-simplified-inspector-spec.md](03-engine-framework/08-dfx-foundation/04-dump-mechanism/Feat-03-simplified-inspector-spec.md) | Baselined |
| Feat-04 | 可访问性Dump与事件Dump | [Feat-04-accessibility-event-dump-spec.md](03-engine-framework/08-dfx-foundation/04-dump-mechanism/Feat-04-accessibility-event-dump-spec.md) | Baselined |

### 03-08-05 Benchmark

| FeatID | 特性名称 | Spec 文件 | 状态 |
|--------|----------|-----------|------|

### 03-08-06 布局边界显示

| FeatID | 特性名称 | Spec 文件 | 状态 |
|--------|----------|-----------|------|
| Feat-01 | 布局边界显示调试能力 | [Feat-01-layout-boundary-display-spec.md](03-engine-framework/08-dfx-foundation/06-layout-boundary-display/Feat-01-layout-boundary-display-spec.md) | Baselined |

### 04-01-01 图片加载机制

| FeatID | 特性名称 | Spec 文件 | 状态 |
|--------|----------|-----------|------|
| Feat-01 | 图片加载机制 | [Feat-01-image-loading-mechanism-spec.md](04-common-capability/01-image-loading/01-image-loading-mechanism/Feat-01-image-loading-mechanism-spec.md) | Baselined |

### 04-01-02 Svg解析

| FeatID | 特性名称 | Spec 文件 | 状态 |
|--------|----------|-----------|------|
| Feat-01 | SVG DOM、标签、属性与样式解析 | [Feat-01-svg-dom-parsing-spec.md](04-common-capability/01-image-loading/02-svg-parsing/Feat-01-svg-dom-parsing-spec.md) | Baselined |
| Feat-02 | SVG 坐标缩放、基础图形与文本绘制 | [Feat-02-svg-coordinate-shape-text-spec.md](04-common-capability/01-image-loading/02-svg-parsing/Feat-02-svg-coordinate-shape-text-spec.md) | Baselined |
| Feat-03 | SVG 引用、渐变、裁剪、遮罩与滤镜效果 | [Feat-03-svg-reference-effects-spec.md](04-common-capability/01-image-loading/02-svg-parsing/Feat-03-svg-reference-effects-spec.md) | Baselined |
| Feat-04 | SVG 动画、版本兼容与 Image 集成 | [Feat-04-svg-animation-image-integration-spec.md](04-common-capability/01-image-loading/02-svg-parsing/Feat-04-svg-animation-image-integration-spec.md) | Baselined |

### 04-01-03 DrawableDescriptor 能力

| FeatID | 特性名称 | Spec 文件 | 状态 |
|--------|----------|-----------|------|
| Feat-01 | DrawableDescriptor 能力 (TS + C API) | [Feat-01-drawable-descriptor-spec.md](04-common-capability/01-image-loading/03-drawable-descriptor/Feat-01-drawable-descriptor-spec.md) | Baselined |

### 04-02-01 安全区机制

| FeatID | 特性名称 | Spec 文件 | 状态 |
|--------|----------|-----------|------|
| Feat-01 | 安全区数据源聚合与窗口同步 | [Feat-01-safe-area-source-window-sync-spec.md](04-common-capability/02-safe-area/01-safe-area-mechanism/Feat-01-safe-area-source-window-sync-spec.md) | Baselined |
| Feat-02 | 渲染安全区扩展 | [Feat-02-render-safe-area-expansion-spec.md](04-common-capability/02-safe-area/01-safe-area-mechanism/Feat-02-render-safe-area-expansion-spec.md) | Baselined |
| Feat-03 | 组件级安全区内边距与 SAE 累积 | [Feat-03-safe-area-padding-sae-accumulation-spec.md](04-common-capability/02-safe-area/01-safe-area-mechanism/Feat-03-safe-area-padding-sae-accumulation-spec.md) | Baselined |
| Feat-04 | 布局安全区忽略与多阶段调度 | [Feat-04-ignore-layout-safe-area-scheduling-spec.md](04-common-capability/02-safe-area/01-safe-area-mechanism/Feat-04-ignore-layout-safe-area-scheduling-spec.md) | Baselined |
| Feat-05 | 键盘安全区联动与页面避让 | [Feat-05-keyboard-safe-area-page-avoidance-spec.md](04-common-capability/02-safe-area/01-safe-area-mechanism/Feat-05-keyboard-safe-area-page-avoidance-spec.md) | Baselined |

### 04-03-01 布局属性

| FeatID | 特性名称 | Spec 文件 | 状态 |
|--------|----------|-----------|------|
| Feat-01 | 尺寸属性 (width/height/size/constraintSize/padding/margin) | [Feat-01-size-properties-spec.md](04-common-capability/03-common-attributes/01-layout-attributes/Feat-01-size-properties-spec.md) | Baselined |
| Feat-02 | 位置属性 (position/offset/markAnchor/align/direction) | [Feat-02-position-properties-spec.md](04-common-capability/03-common-attributes/01-layout-attributes/Feat-02-position-properties-spec.md) | Baselined |
| Feat-03 | Flex 相关属性 (flexGrow/flexShrink/flexBasis/alignSelf/layoutWeight/displayPriority) | [Feat-03-flex-properties-spec.md](04-common-capability/03-common-attributes/01-layout-attributes/Feat-03-flex-properties-spec.md) | Baselined |

### 04-03-02 视效属性

| FeatID | 特性名称 | Spec 文件 | 状态 |
|--------|----------|-----------|------|
| Feat-01 | 图像效果 | [Feat-01-image-effects-spec.md](04-common-capability/03-common-attributes/02-visual-effect-attributes/Feat-01-image-effects-spec.md) | Baselined |

### 04-03-03 基础属性

| FeatID | 特性名称 | Spec 文件 | 状态 |
|--------|----------|-----------|------|
| Feat-01 | 组件标识与显隐 | [Feat-01-component-id-visibility-spec.md](04-common-capability/03-common-attributes/03-basic-attributes/Feat-01-component-id-visibility-spec.md) | Baselined |
| Feat-02 | 背景设置 | [Feat-02-background-setting-spec.md](04-common-capability/03-common-attributes/03-basic-attributes/Feat-02-background-setting-spec.md) | Baselined |
| Feat-03 | 渲染与复用 | [Feat-03-render-reuse-spec.md](04-common-capability/03-common-attributes/03-basic-attributes/Feat-03-render-reuse-spec.md) | Baselined |
| Feat-04 | 浮层 | [Feat-04-overlay-spec.md](04-common-capability/03-common-attributes/03-basic-attributes/Feat-04-overlay-spec.md) | Baselined |
| Feat-05 | 焦点属性 | [Feat-05-focus-attribute-spec.md](04-common-capability/03-common-attributes/03-basic-attributes/Feat-05-focus-attribute-spec.md) | Baselined |

### 04-03-04 交互属性

| FeatID | 特性名称 | Spec 文件 | 状态 |
|--------|----------|-----------|------|

### 04-03-05 弹窗类属性

| FeatID | 特性名称 | Spec 文件 | 状态 |
|--------|----------|-----------|------|
| Feat-01 | 弹窗类属性（bindPopup/bindMenu/bindContextMenu） | [Feat-01-popup-attributes-spec.md](04-common-capability/03-common-attributes/05-popup-attributes/Feat-01-popup-attributes-spec.md) | Baselined |

### 04-03-06 模态属性

| FeatID | 特性名称 | Spec 文件 | 状态 |
|--------|----------|-----------|------|
| Feat-01 | 模态属性（bindSheet/bindContentCover） | [Feat-01-modal-attributes-spec.md](04-common-capability/03-common-attributes/06-modal-attributes/Feat-01-modal-attributes-spec.md) | Baselined |

### 04-03-07 样式属性

| FeatID | 特性名称 | Spec 文件 | 状态 |
|--------|----------|-----------|------|
| Feat-01 | 状态效果 | [Feat-01-state-effect-spec.md](04-common-capability/03-common-attributes/07-style-attributes/Feat-01-state-effect-spec.md) | Baselined |
| Feat-02 | 动态属性设置（attributeModifier） | [Feat-02-attribute-modifier-spec.md](04-common-capability/03-common-attributes/07-style-attributes/Feat-02-attribute-modifier-spec.md) | Baselined |

### 04-03-08 基础单位

| FeatID | 特性名称 | Spec 文件 | 状态 |
|--------|----------|-----------|------|
| Feat-01 | 基础单位（vp/fp/px/lpx/percent/Dimension） | [Feat-01-basic-units-spec.md](04-common-capability/03-common-attributes/08-basic-units/Feat-01-basic-units-spec.md) | Baselined |

### 04-03-09 无障碍属性

| FeatID | 特性名称 | Spec 文件 | 状态 |
|--------|----------|-----------|------|

### 04-03-10 图片相关属性

| FeatID | 特性名称 | Spec 文件 | 状态 |
|--------|----------|-----------|------|
| Feat-01 | 背景图片通用属性 | [Feat-01-background-image-attributes-spec.md](04-common-capability/03-common-attributes/10-image-related-attributes/Feat-01-background-image-attributes-spec.md) | Baselined |

### 04-03-11 文本通用属性

| FeatID | 特性名称 | Spec 文件 | 状态 |
|--------|----------|-----------|------|
| Feat-01 | 核心字体属性 (fontSize/fontColor/fontWeight/fontStyle/fontFamily) | [Feat-01-core-font-attributes-spec.md](04-common-capability/03-common-attributes/11-text-common-attributes/Feat-01-core-font-attributes-spec.md) | Baselined |
| Feat-02 | 文本装饰与大小写 (decoration/textCase) | [Feat-02-text-decoration-case-spec.md](04-common-capability/03-common-attributes/11-text-common-attributes/Feat-02-text-decoration-case-spec.md) | Baselined |
| Feat-03 | 文本间距与度量 (letterSpacing/lineHeight/baselineOffset) | [Feat-03-text-spacing-metrics-spec.md](04-common-capability/03-common-attributes/11-text-common-attributes/Feat-03-text-spacing-metrics-spec.md) | Baselined |
| Feat-04 | 文本阴影与 OpenType 特性 (textShadow/fontFeature/fontVariations) | [Feat-04-text-shadow-opentype-spec.md](04-common-capability/03-common-attributes/11-text-common-attributes/Feat-04-text-shadow-opentype-spec.md) | Baselined |
| Feat-05 | 自适应字体缩放 (minFontSize/maxFontSize/minFontScale/maxFontScale) | [Feat-05-adaptive-font-scaling-spec.md](04-common-capability/03-common-attributes/11-text-common-attributes/Feat-05-adaptive-font-scaling-spec.md) | Baselined |

### 04-04-01 触摸事件

| FeatID | 特性名称 | Spec 文件 | 状态 |
|--------|----------|-----------|------|

### 04-04-02 按键事件

| FeatID | 特性名称 | Spec 文件 | 状态 |
|--------|----------|-----------|------|

### 04-04-03 事件分发和拦截

| FeatID | 特性名称 | Spec 文件 | 状态 |
|--------|----------|-----------|------|

### 04-04-04 组件组合键

| FeatID | 特性名称 | Spec 文件 | 状态 |
|--------|----------|-----------|------|

### 04-04-05 鼠标事件

| FeatID | 特性名称 | Spec 文件 | 状态 |
|--------|----------|-----------|------|

### 04-04-06 手势能力

| FeatID | 特性名称 | Spec 文件 | 状态 |
|--------|----------|-----------|------|
| Feat-01 | 基础手势 (Tap/LongPress/Pan/Pinch/Rotation/Swipe) | [Feat-01-basic-gestures-spec.md](04-common-capability/04-common-events/06-gesture-capability/Feat-01-basic-gestures-spec.md) | Baselined |
| Feat-02 | 组合手势 (GestureGroup: Sequential/Parallel/Exclusive) | [Feat-02-gesture-group-spec.md](04-common-capability/04-common-events/06-gesture-capability/Feat-02-gesture-group-spec.md) | Baselined |
| Feat-03 | 手势判定 (GestureReferee: 手势仲裁机制) | [Feat-03-gesture-referee-spec.md](04-common-capability/04-common-events/06-gesture-capability/Feat-03-gesture-referee-spec.md) | Baselined |
| Feat-04 | 手势拦截 (Touch Intercept / responseLink / hitTestBehavior) | [Feat-04-gesture-intercept-spec.md](04-common-capability/04-common-events/06-gesture-capability/Feat-04-gesture-intercept-spec.md) | Baselined |
| Feat-05 | 手势识别异常恢复增强 | [Feat-05-gesture-recognizer-recovery-spec.md](04-common-capability/04-common-events/06-gesture-capability/Feat-05-gesture-recognizer-recovery-spec.md) | Draft |

### 04-04-07 拖拽能力

| FeatID | 特性名称 | Spec 文件 | 状态 |
|--------|----------|-----------|------|

### 04-04-08 手写笔能力

| FeatID | 特性名称 | Spec 文件 | 状态 |
|--------|----------|-----------|------|

### 04-04-09 组件相关事件

| FeatID | 特性名称 | Spec 文件 | 状态 |
|--------|----------|-----------|------|

### 04-04-10 可见区域机制

| FeatID | 特性名称 | Spec 文件 | 状态 |
|--------|----------|-----------|------|

### 04-04-11 交互归一化

| FeatID | 特性名称 | Spec 文件 | 状态 |
|--------|----------|-----------|------|

### 04-05-01 动态绘制属性

| FeatID | 特性名称 | Spec 文件 | 状态 |
|--------|----------|-----------|------|
| Feat-01 | DrawModifier 装配与组件门控 | [Feat-01-draw-modifier-mounting-gating-spec.md](04-common-capability/05-custom-extension/01-draw-modifier/Feat-01-draw-modifier-mounting-gating-spec.md) | Baselined |
| Feat-02 | 分层绘制回调分发 | [Feat-02-draw-modifier-layered-dispatch-spec.md](04-common-capability/05-custom-extension/01-draw-modifier/Feat-02-draw-modifier-layered-dispatch-spec.md) | Baselined |
| Feat-03 | 主动刷新机制 | [Feat-03-draw-modifier-invalidate-refresh-spec.md](04-common-capability/05-custom-extension/01-draw-modifier/Feat-03-draw-modifier-invalidate-refresh-spec.md) | Baselined |

### 04-05-02 动态属性

| FeatID | 特性名称 | Spec 文件 | 状态 |
|--------|----------|-----------|------|
| Feat-01 | AttributeModifier 装配与状态监听 | [Feat-01-attribute-modifier-mounting-state-spec.md](04-common-capability/05-custom-extension/02-dynamic-attributes/Feat-01-attribute-modifier-mounting-state-spec.md) | Baselined |
| Feat-02 | 多状态属性应用与按位分发 | [Feat-02-attribute-modifier-multi-state-dispatch-spec.md](04-common-capability/05-custom-extension/02-dynamic-attributes/Feat-02-attribute-modifier-multi-state-dispatch-spec.md) | Baselined |

### 04-05-03 自定义内容 -（表单类组件）

| FeatID | 特性名称 | Spec 文件 | 状态 |
|--------|----------|-----------|------|
| Feat-01 | 表单类组件自定义内容（ContentModifier） | [Feat-01-content-modifier-form-spec.md](04-common-capability/05-custom-extension/03-content-modifier-form/Feat-01-content-modifier-form-spec.md) | Baselined |

### 04-05-04 自定义内容 -（信息展示类）

| FeatID | 特性名称 | Spec 文件 | 状态 |
|--------|----------|-----------|------|
| Feat-01 | 信息展示类组件自定义内容（ContentModifier） | [Feat-01-content-modifier-display-spec.md](04-common-capability/05-custom-extension/04-content-modifier-display/Feat-01-content-modifier-display-spec.md) | Baselined |

### 04-05-05 自定义属性

| FeatID | 特性名称 | Spec 文件 | 状态 |
|--------|----------|-----------|------|
| Feat-01 | 自定义属性设置读取与双存储 | [Feat-01-custom-property-set-read-storage-spec.md](04-common-capability/05-custom-extension/05-custom-property/Feat-01-custom-property-set-read-storage-spec.md) | Baselined |

### 04-05-06 组件Modifier

| FeatID | 特性名称 | Spec 文件 | 状态 |
|--------|----------|-----------|------|
| Feat-01 | 命令式 Modifier 基类与类体系 | [Feat-01-common-modifier-class-system-spec.md](04-common-capability/05-custom-extension/06-component-modifier/Feat-01-common-modifier-class-system-spec.md) | Baselined |
| Feat-02 | ModifierUtils 对外接口 | [Feat-02-modifier-utils-api-spec.md](04-common-capability/05-custom-extension/06-component-modifier/Feat-02-modifier-utils-api-spec.md) | Baselined |

### 04-06-01 占位组件

| FeatID | 特性名称 | Spec 文件 | 状态 |
|--------|----------|-----------|------|
| Feat-01 | 占位组件交叉引用 | [Feat-01-placeholder-component-cross-reference-spec.md](04-common-capability/06-custom-node/01-placeholder-component/Feat-01-placeholder-component-cross-reference-spec.md) | Baselined |

### 04-06-02 FrameNode

| FeatID | 特性名称 | Spec 文件 | 状态 |
|--------|----------|-----------|------|
| Feat-01 | 节点创建、身份与内省 | [Feat-01-node-creation-identity-introspection-spec.md](04-common-capability/06-custom-node/02-frame-node/Feat-01-node-creation-identity-introspection-spec.md) | Baselined |
| Feat-02 | 树结构与挂载管理 | [Feat-02-tree-structure-mounting-spec.md](04-common-capability/06-custom-node/02-frame-node/Feat-02-tree-structure-mounting-spec.md) | Baselined |
| Feat-03 | 布局与度量 | [Feat-03-layout-measurement-spec.md](04-common-capability/06-custom-node/02-frame-node/Feat-03-layout-measurement-spec.md) | Baselined |
| Feat-04 | 坐标转换与位置查询 | [Feat-04-position-coordinate-conversion-spec.md](04-common-capability/06-custom-node/02-frame-node/Feat-04-position-coordinate-conversion-spec.md) | Baselined |
| Feat-05 | 渲染上下文与视觉状态 | [Feat-05-render-context-visual-state-spec.md](04-common-capability/06-custom-node/02-frame-node/Feat-05-render-context-visual-state-spec.md) | Baselined |
| Feat-06 | 事件交互与 UIState | [Feat-06-event-interaction-ui-state-spec.md](04-common-capability/06-custom-node/02-frame-node/Feat-06-event-interaction-ui-state-spec.md) | Baselined |
| Feat-07 | 节点动画 | [Feat-07-node-animation-spec.md](04-common-capability/06-custom-node/02-frame-node/Feat-07-node-animation-spec.md) | Baselined |
| Feat-08 | 生命周期、回收与跨语言 | [Feat-08-lifecycle-recycle-cross-language-spec.md](04-common-capability/06-custom-node/02-frame-node/Feat-08-lifecycle-recycle-cross-language-spec.md) | Baselined |

### 04-06-03 RenderNode

| FeatID | 特性名称 | Spec 文件 | 状态 |
|--------|----------|-----------|------|
| Feat-01 | RenderNode 全量规格 | [Feat-01-render-node-full-spec.md](04-common-capability/06-custom-node/03-render-node/Feat-01-render-node-full-spec.md) | Baselined |

### 04-06-04 BuilderNode

| FeatID | 特性名称 | Spec 文件 | 状态 |
|--------|----------|-----------|------|
| Feat-01 | 创建、释放与渲染类型 | [Feat-01-creation-dispose-render-type-spec.md](04-common-capability/06-custom-node/04-builder-node/Feat-01-creation-dispose-render-type-spec.md) | Baselined |
| Feat-02 | 构建与更新 | [Feat-02-build-update-spec.md](04-common-capability/06-custom-node/04-builder-node/Feat-02-build-update-spec.md) | Baselined |
| Feat-03 | FrameNode 访问 | [Feat-03-framenode-access-spec.md](04-common-capability/06-custom-node/04-builder-node/Feat-03-framenode-access-spec.md) | Baselined |
| Feat-04 | 渲染类型与纹理 | [Feat-04-render-type-texture-spec.md](04-common-capability/06-custom-node/04-builder-node/Feat-04-render-type-texture-spec.md) | Baselined |
| Feat-05 | 复用与回收 | [Feat-05-reuse-recycle-spec.md](04-common-capability/06-custom-node/04-builder-node/Feat-05-reuse-recycle-spec.md) | Baselined |
| Feat-06 | 输入事件分发 | [Feat-06-input-event-dispatch-spec.md](04-common-capability/06-custom-node/04-builder-node/Feat-06-input-event-dispatch-spec.md) | Baselined |
| Feat-07 | 冻结策略 | [Feat-07-freeze-policy-spec.md](04-common-capability/06-custom-node/04-builder-node/Feat-07-freeze-policy-spec.md) | Baselined |
| Feat-08 | 响应式变体 | [Feat-08-reactive-variant-spec.md](04-common-capability/06-custom-node/04-builder-node/Feat-08-reactive-variant-spec.md) | Baselined |

### 04-06-05 ComponentContent

| FeatID | 特性名称 | Spec 文件 | 状态 |
|--------|----------|-----------|------|
| Feat-01 | 创建与释放 | [Feat-01-creation-dispose-spec.md](04-common-capability/06-custom-node/05-component-content/Feat-01-creation-dispose-spec.md) | Baselined |
| Feat-02 | 更新配置冻结 | [Feat-02-update-config-freeze-spec.md](04-common-capability/06-custom-node/05-component-content/Feat-02-update-config-freeze-spec.md) | Baselined |
| Feat-03 | 复用回收 | [Feat-03-reuse-recycle-spec.md](04-common-capability/06-custom-node/05-component-content/Feat-03-reuse-recycle-spec.md) | Baselined |
| Feat-04 | ReactiveComponentContent | [Feat-04-reactive-component-content-spec.md](04-common-capability/06-custom-node/05-component-content/Feat-04-reactive-component-content-spec.md) | Baselined |
| Feat-05 | Transfer 转换变体 | [Feat-05-transfer-dynamic-static-conversion-spec.md](04-common-capability/06-custom-node/05-component-content/Feat-05-transfer-dynamic-static-conversion-spec.md) | Baselined |

### 04-06-06 NodeAdapter

| FeatID | 特性名称 | Spec 文件 | 状态 |
|--------|----------|-----------|------|
| Feat-01 | NodeAdapter ArkTS 前端规格 | [Feat-01-nodeadapter-arkts-frontend-spec.md](04-common-capability/06-custom-node/06-node-adapter/Feat-01-nodeadapter-arkts-frontend-spec.md) | Baselined |

### 04-06-07 TypedFrameNode

| FeatID | 特性名称 | Spec 文件 | 状态 |
|--------|----------|-----------|------|
| Feat-01 | TypedFrameNode 类型 | [Feat-01-typedframenode-type-spec.md](04-common-capability/06-custom-node/07-typed-frame-node/Feat-01-typedframenode-type-spec.md) | Baselined |
| Feat-02 | typeNode 动态工厂 | [Feat-02-typenode-dynamic-factory-spec.md](04-common-capability/06-custom-node/07-typed-frame-node/Feat-02-typenode-dynamic-factory-spec.md) | Baselined |
| Feat-03 | typeNode 静态工厂 | [Feat-03-typenode-static-factory-spec.md](04-common-capability/06-custom-node/07-typed-frame-node/Feat-03-typenode-static-factory-spec.md) | Baselined |
| Feat-04 | 组件支持矩阵 | [Feat-04-component-matrix-spec.md](04-common-capability/06-custom-node/07-typed-frame-node/Feat-04-component-matrix-spec.md) | Baselined |

### 04-07-01 分布式路由迁移能力

| FeatID | 特性名称 | Spec 文件 | 状态 |
|--------|----------|-----------|------|

### 04-07-02 路由栈恢复

| FeatID | 特性名称 | Spec 文件 | 状态 |
|--------|----------|-----------|------|
| Feat-01 | 路由栈保存与恢复机制 | [Feat-01-router-stack-save-restore-spec.md](04-common-capability/07-migration-recovery/02-router-stack-recovery/Feat-01-router-stack-save-restore-spec.md) | Draft |

### 04-07-03 组件迁移机制

| FeatID | 特性名称 | Spec 文件 | 状态 |
|--------|----------|-----------|------|

### 04-08-01 窗口工具栏

| FeatID | 特性名称 | Spec 文件 | 状态 |
|--------|----------|-----------|------|

### 04-08-02 元服务AppBar

| FeatID | 特性名称 | Spec 文件 | 状态 |
|--------|----------|-----------|------|

### 04-08-03 浮层能力

| FeatID | 特性名称 | Spec 文件 | 状态 |
|--------|----------|-----------|------|
| Feat-01 | 浮层能力（OverlayManager 挂载与管理） | [Feat-01-overlay-capability-spec.md](04-common-capability/08-root-view/03-overlay-capability/Feat-01-overlay-capability-spec.md) | Baselined |

### 04-09-01 焦点机制

| FeatID | 特性名称 | Spec 文件 | 状态 |
|--------|----------|-----------|------|

### 04-10-01 离屏截图

| FeatID | 特性名称 | Spec 文件 | 状态 |
|--------|----------|-----------|------|

### 04-11-01 ComponentUtils

| FeatID | 特性名称 | Spec 文件 | 状态 |
|--------|----------|-----------|------|

### 04-11-02 无感监听（observer）

| FeatID | 特性名称 | Spec 文件 | 状态 |
|--------|----------|-----------|------|
| Feat-01 | 无感监听核心架构 | [Feat-01-observer-core-architecture-spec.md](04-common-capability/11-component-info/02-observer/Feat-01-observer-core-architecture-spec.md) | Baselined |
| Feat-02 | 无感监听接口全覆盖 | [Feat-02-observer-api-full-coverage-spec.md](04-common-capability/11-component-info/02-observer/Feat-02-observer-api-full-coverage-spec.md) | Baselined |

### 04-11-03 布局回调（inspector）

| FeatID | 特性名称 | Spec 文件 | 状态 |
|--------|----------|-----------|------|

### 04-12-01 UIContext接口

| FeatID | 特性名称 | Spec 文件 | 状态 |
|--------|----------|-----------|------|
| Feat-01 | UIContext入口架构与实例路由 | [Feat-01-uicontext-entry-architecture-instance-routing-spec.md](04-common-capability/12-ui-context/01-ui-context-interface/Feat-01-uicontext-entry-architecture-instance-routing-spec.md) | Baselined |
| Feat-02 | UIContext实例解析与作用域调度 | [Feat-02-uicontext-instance-resolution-scoped-task-spec.md](04-common-capability/12-ui-context/01-ui-context-interface/Feat-02-uicontext-instance-resolution-scoped-task-spec.md) | Baselined |
| Feat-03 | 子对象工厂与直接方法 | [Feat-03-uicontext-sub-factory-direct-methods-spec.md](04-common-capability/12-ui-context/01-ui-context-interface/Feat-03-uicontext-sub-factory-direct-methods-spec.md) | Baselined |
| Feat-04 | C-API UIContextHandle接口 | [Feat-04-capi-uicontext-handle-spec.md](04-common-capability/12-ui-context/01-ui-context-interface/Feat-04-capi-uicontext-handle-spec.md) | Baselined |

### 04-12-02 Ability上下文

| FeatID | 特性名称 | Spec 文件 | 状态 |
|--------|----------|-----------|------|
| Feat-01 | Ability上下文与窗口信息 | [Feat-01-ability-context-window-info-spec.md](04-common-capability/12-ui-context/02-ability-context/Feat-01-ability-context-window-info-spec.md) | Baselined |

### 04-12-03 Frame回调接口

| FeatID | 特性名称 | Spec 文件 | 状态 |
|--------|----------|-----------|------|
| Feat-01 | Frame回调与帧调度 | [Feat-01-frame-callback-scheduling-spec.md](04-common-capability/12-ui-context/03-frame-callback/Feat-01-frame-callback-scheduling-spec.md) | Baselined |

### 04-13-01 字体注册

| FeatID | 特性名称 | Spec 文件 | 状态 |
|--------|----------|-----------|------|
| Feat-01 | 字体注册与查询全能力 | [Feat-01-font-registration-full-capability-spec.md](04-common-capability/13-font-text/01-font-registration/Feat-01-font-registration-full-capability-spec.md) | Baselined |

### 04-13-02 文本测量

| FeatID | 特性名称 | Spec 文件 | 状态 |
|--------|----------|-----------|------|
| Feat-01 | 独立文本测量能力 | [Feat-01-standalone-text-measurement-spec.md](04-common-capability/13-font-text/02-text-measurement/Feat-01-standalone-text-measurement-spec.md) | Baselined |
| Feat-02 | 段落级排版测量能力 | *待补充* | Draft |
| Feat-03 | 组件级行级度量查询能力 | *待补充* | Draft |

### 04-14-01 文本选择

| FeatID | 特性名称 | Spec 文件 | 状态 |
|--------|----------|-----------|------|
| Feat-01 | 选区状态模型与编程式选区 | [Feat-01-selection-state-programmatic-spec.md](04-common-capability/14-input-interaction/01-text-selection/Feat-01-selection-state-programmatic-spec.md) | Baselined |
| Feat-02 | 选择手柄、放大镜与选择高亮 | *待补充* | Draft |
| Feat-03 | 触摸/鼠标手势选区 | *待补充* | Draft |

### 04-14-02 文本快捷键

| FeatID | 特性名称 | Spec 文件 | 状态 |
|--------|----------|-----------|------|

### 04-14-03 文本交互

| FeatID | 特性名称 | Spec 文件 | 状态 |
|--------|----------|-----------|------|
| Feat-01 | 光标(Caret)交互 | [Feat-01-caret-interaction-spec.md](04-common-capability/14-input-interaction/03-text-interaction/Feat-01-caret-interaction-spec.md) | Baselined |
| Feat-02 | 文本上下文菜单(Context Menu) | *待补充* | Draft |
| Feat-03 | 拖拽与剪贴板回调 | *待补充* | Draft |
| Feat-04 | 文本编辑拦截钩子 | *待补充* | Draft |
| Feat-05 | 交互触发与状态回调 | *待补充* | Draft |
| Feat-06 | 长按选择与实体识别 | *待补充* | Draft |

### 04-14-04 键盘控制

| FeatID | 特性名称 | Spec 文件 | 状态 |
|--------|----------|-----------|------|

### 04-14-05 自动补全能力（AutoFill）

| FeatID | 特性名称 | Spec 文件 | 状态 |
|--------|----------|-----------|------|
| Feat-01 | TextInput/TextArea AutoFill 基础属性与类型枚举 | [Feat-01-textinput-textarea-base-attributes-spec.md](04-common-capability/14-input-interaction/05-autofill/Feat-01-textinput-textarea-base-attributes-spec.md) | Baselined |
| Feat-02 | TextInput AutoFill 动画与内容修饰 | *待补充* | Draft |
| Feat-03 | AutoFill 标准触发模型与请求管线 | *待补充* | Draft |
| Feat-04 | AutoFill 增强触发路径（MSDP 与 Secure Paste） | *待补充* | Draft |
| Feat-05 | Web AutoFill 管线 | *待补充* | Draft |

### 04-15-01 路由管理

| FeatID | 特性名称 | Spec 文件 | 状态 |
|--------|----------|-----------|------|
| Feat-01 | 路由跳转与替换 | [Feat-01-router-push-replace-back-spec.md](04-common-capability/15-router-mechanism/01-router-management/Feat-01-router-push-replace-back-spec.md) | Baselined |
| Feat-02 | 路由栈查询与弹窗拦截 | [Feat-02-router-stack-query-alert-spec.md](04-common-capability/15-router-mechanism/01-router-management/Feat-02-router-stack-query-alert-spec.md) | Baselined |

### 04-15-02 命名路由

| FeatID | 特性名称 | Spec 文件 | 状态 |
|--------|----------|-----------|------|
| Feat-01 | 命名路由跳转与替换 | [Feat-01-named-router-push-replace-spec.md](04-common-capability/15-router-mechanism/02-named-router/Feat-01-named-router-push-replace-spec.md) | Baselined |

### 04-16-01 UIAppearance

| FeatID | 特性名称 | Spec 文件 | 状态 |
|--------|----------|-----------|------|
| Feat-01 | UIAppearance（深浅色模式与外观管理） | [Feat-01-ui-appearance-spec.md](04-common-capability/16-ui-appearance/01-ui-appearance/Feat-01-ui-appearance-spec.md) | Baselined |

### 04-17-01 UIExtension机制

| FeatID | 特性名称 | Spec 文件 | 状态 |
|--------|----------|-----------|------|

### 04-17-02 IsolateComponent机制

| FeatID | 特性名称 | Spec 文件 | 状态 |
|--------|----------|-----------|------|

### 04-17-03 From卡片机制

| FeatID | 特性名称 | Spec 文件 | 状态 |
|--------|----------|-----------|------|

### 04-17-04 PluginComponent机制

| FeatID | 特性名称 | Spec 文件 | 状态 |
|--------|----------|-----------|------|

### 04-18-01 同层渲染机制

| FeatID | 特性名称 | Spec 文件 | 状态 |
|--------|----------|-----------|------|
| Feat-01 | 同层渲染纹理生产者（ArkUI 子树纹理导出） | [Feat-01-texture-export-producer-spec.md](04-common-capability/18-on-device-rendering/01-same-layer-rendering/Feat-01-texture-export-producer-spec.md) | Baselined |

### 04-19-01 组件复用框架

| FeatID | 特性名称 | Spec 文件 | 状态 |
|--------|----------|-----------|------|
| Feat-01 | UINode 复用生命周期与可复用节点判定 | [Feat-01-uinode-reuse-lifecycle-and-reusable-node-judgment-spec.md](04-common-capability/19-component-reuse/01-component-reuse-framework/Feat-01-uinode-reuse-lifecycle-and-reusable-node-judgment-spec.md) | Baselined |
| Feat-02 | reuseId 节点池与 engine↔TS 桥接 | [Feat-02-reuseid-node-pool-and-engine-ts-bridge-spec.md](04-common-capability/19-component-reuse/01-component-reuse-framework/Feat-02-reuseid-node-pool-and-engine-ts-bridge-spec.md) | Baselined |
| Feat-03 | RecycleDummyNode 与 DisableRecycle 机制 | [Feat-03-recycle-dummy-node-and-disable-recycle-spec.md](04-common-capability/19-component-reuse/01-component-reuse-framework/Feat-03-recycle-dummy-node-and-disable-recycle-spec.md) | Baselined |
| Feat-04 | 公开复用池 API 与内存优化（@since26） | [Feat-04-public-reuse-pool-api-and-memory-optimization-spec.md](04-common-capability/19-component-reuse/01-component-reuse-framework/Feat-04-public-reuse-pool-api-and-memory-optimization-spec.md) | Baselined |

### 04-20-01 MediaQuery

| FeatID | 特性名称 | Spec 文件 | 状态 |
|--------|----------|-----------|------|
| Feat-01 | MediaQuery 媒体条件匹配与监听生命周期 | [Feat-01-media-query-listener-spec.md](04-common-capability/20-media-query/01-media-query/Feat-01-media-query-listener-spec.md) | Baselined |

### 04-21-01 大字体

| FeatID | 特性名称 | Spec 文件 | 状态 |
|--------|----------|-----------|------|

### 04-22-01 多语言能力

| FeatID | 特性名称 | Spec 文件 | 状态 |
|--------|----------|-----------|------|

### 04-22-02 镜像能力

| FeatID | 特性名称 | Spec 文件 | 状态 |
|--------|----------|-----------|------|

### 04-23-01 Image分析能力

| FeatID | 特性名称 | Spec 文件 | 状态 |
|--------|----------|-----------|------|
| Feat-01 | Image 分析开关、配置与支持条件 | [Feat-01-image-analyzer-support-spec.md](04-common-capability/23-ai-capability/01-image-analysis/Feat-01-image-analyzer-support-spec.md) | Baselined |
| Feat-02 | Image Analyzer Overlay 生命周期与跨组件管理 | [Feat-02-image-analyzer-overlay-lifecycle-spec.md](04-common-capability/23-ai-capability/01-image-analysis/Feat-02-image-analyzer-overlay-lifecycle-spec.md) | Baselined |

### 04-24-01 像素取整能力

| FeatID | 特性名称 | Spec 文件 | 状态 |
|--------|----------|-----------|------|
| Feat-01 | 像素取整策略与布局渲染传播 | [Feat-01-pixel-rounding-policy-propagation-spec.md](04-common-capability/24-layout-common-capability/01-pixel-rounding/Feat-01-pixel-rounding-policy-propagation-spec.md) | Baselined |

### 04-25-01 热重载机制

| FeatID | 特性名称 | Spec 文件 | 状态 |
|--------|----------|-----------|------|

### 05-01-01 Blank

| FeatID | 特性名称 | Spec 文件 | 状态 |
|--------|----------|-----------|------|
| Feat-01 | Blank 组件 | [Feat-01-blank-component-spec.md](05-ui-components/01-layout-components/01-blank/Feat-01-blank-component-spec.md) | Baselined |

### 05-01-02 Divider

| FeatID | 特性名称 | Spec 文件 | 状态 |
|--------|----------|-----------|------|
| Feat-01 | Divider 组件全量规格 | [Feat-01-divider-spec.md](05-ui-components/01-layout-components/02-divider/Feat-01-divider-spec.md) | Baselined |

### 05-01-03 Column

| FeatID | 特性名称 | Spec 文件 | 状态 |
|--------|----------|-----------|------|
| Feat-01 | Column 创建、尺寸与子项间距 | [Feat-01-column-creation-size-space-spec.md](05-ui-components/01-layout-components/03-column/Feat-01-column-creation-size-space-spec.md) | Baselined |
| Feat-02 | Column 对齐与反向排列 | [Feat-02-column-alignment-reverse-spec.md](05-ui-components/01-layout-components/03-column/Feat-02-column-alignment-reverse-spec.md) | Baselined |
| Feat-03 | Column 多范式接口与版本兼容 | [Feat-03-column-multi-paradigm-version-spec.md](05-ui-components/01-layout-components/03-column/Feat-03-column-multi-paradigm-version-spec.md) | Baselined |
| Feat-04 | Column PointLight 系统光效 | [Feat-04-column-point-light-spec.md](05-ui-components/01-layout-components/03-column/Feat-04-column-point-light-spec.md) | Baselined |

### 05-01-04 ColumnSplit

| FeatID | 特性名称 | Spec 文件 | 状态 |
|--------|----------|-----------|------|
| Feat-01 | ColumnSplit 垂直分割布局与分隔线绘制 | [Feat-01-column-split-vertical-layout-rendering-spec.md](05-ui-components/01-layout-components/04-column-split/Feat-01-column-split-vertical-layout-rendering-spec.md) | Baselined |
| Feat-02 | ColumnSplit 可拖拽调整与边界约束 | [Feat-02-column-split-resizeable-drag-spec.md](05-ui-components/01-layout-components/04-column-split/Feat-02-column-split-resizeable-drag-spec.md) | Baselined |
| Feat-03 | ColumnSplit 分隔线边距 | [Feat-03-column-split-divider-margin-spec.md](05-ui-components/01-layout-components/04-column-split/Feat-03-column-split-divider-margin-spec.md) | Baselined |

### 05-01-05 Flex

| FeatID | 特性名称 | Spec 文件 | 状态 |
|--------|----------|-----------|------|
| Feat-01 | Flex 单行弹性布局与轴向对齐 | [Feat-01-flex-single-line-axis-layout-spec.md](05-ui-components/01-layout-components/05-flex/Feat-01-flex-single-line-axis-layout-spec.md) | Baselined |
| Feat-02 | Flex 多行换行与内容对齐 | [Feat-02-flex-wrap-content-alignment-spec.md](05-ui-components/01-layout-components/05-flex/Feat-02-flex-wrap-content-alignment-spec.md) | Baselined |
| Feat-03 | Flex 主轴与交叉轴间距 | [Feat-03-flex-main-cross-space-spec.md](05-ui-components/01-layout-components/05-flex/Feat-03-flex-main-cross-space-spec.md) | Baselined |
| Feat-04 | Flex 多范式接口与版本兼容 | [Feat-04-flex-multi-paradigm-version-spec.md](05-ui-components/01-layout-components/05-flex/Feat-04-flex-multi-paradigm-version-spec.md) | Baselined |
| Feat-05 | Flex PointLight 系统光效 | [Feat-05-flex-point-light-spec.md](05-ui-components/01-layout-components/05-flex/Feat-05-flex-point-light-spec.md) | Baselined |

### 05-01-06 GridCol

| FeatID | 特性名称 | Spec 文件 | 状态 |
|--------|----------|-----------|------|
| Feat-01 | GridCol 创建与响应式占列 | [Feat-01-grid-col-creation-responsive-span-spec.md](05-ui-components/01-layout-components/06-grid-col/Feat-01-grid-col-creation-responsive-span-spec.md) | Baselined |
| Feat-02 | GridCol 偏移、排序与协同布局 | [Feat-02-grid-col-offset-order-layout-spec.md](05-ui-components/01-layout-components/06-grid-col/Feat-02-grid-col-offset-order-layout-spec.md) | Baselined |
| Feat-03 | GridCol 多范式接口与版本兼容 | [Feat-03-grid-col-multi-paradigm-version-spec.md](05-ui-components/01-layout-components/06-grid-col/Feat-03-grid-col-multi-paradigm-version-spec.md) | Baselined |

### 05-01-07 GridRow

| FeatID | 特性名称 | Spec 文件 | 状态 |
|--------|----------|-----------|------|
| Feat-01 | GridRow 列系统与间距 | [Feat-01-grid-row-columns-gutter-spec.md](05-ui-components/01-layout-components/07-grid-row/Feat-01-grid-row-columns-gutter-spec.md) | Baselined |
| Feat-02 | GridRow 响应式断点与变更事件 | [Feat-02-grid-row-breakpoints-event-spec.md](05-ui-components/01-layout-components/07-grid-row/Feat-02-grid-row-breakpoints-event-spec.md) | Baselined |
| Feat-03 | GridRow 排列、换行、对齐与 RTL | [Feat-03-grid-row-arrangement-alignment-rtl-spec.md](05-ui-components/01-layout-components/07-grid-row/Feat-03-grid-row-arrangement-alignment-rtl-spec.md) | Baselined |
| Feat-04 | GridRow 多范式接口与版本兼容 | [Feat-04-grid-row-multi-paradigm-version-spec.md](05-ui-components/01-layout-components/07-grid-row/Feat-04-grid-row-multi-paradigm-version-spec.md) | Baselined |

### 05-01-08 RelativeContainer

| FeatID | 特性名称 | Spec 文件 | 状态 |
|--------|----------|-----------|------|
| Feat-01 | RelativeContainer 锚定与自适应尺寸 | [Feat-01-relative-container-anchor-auto-size-spec.md](05-ui-components/01-layout-components/08-relative-container/Feat-01-relative-container-anchor-auto-size-spec.md) | Baselined |
| Feat-02 | RelativeContainer 依赖图、循环检测与偏置 | [Feat-02-relative-container-dependency-bias-spec.md](05-ui-components/01-layout-components/08-relative-container/Feat-02-relative-container-dependency-bias-spec.md) | Baselined |
| Feat-03 | RelativeContainer 辅助线、屏障与 RTL | [Feat-03-relative-container-guideline-barrier-spec.md](05-ui-components/01-layout-components/08-relative-container/Feat-03-relative-container-guideline-barrier-spec.md) | Baselined |
| Feat-04 | RelativeContainer 链式布局与权重 | [Feat-04-relative-container-chain-weight-spec.md](05-ui-components/01-layout-components/08-relative-container/Feat-04-relative-container-chain-weight-spec.md) | Baselined |
| Feat-05 | RelativeContainer 多范式与原生接口兼容 | [Feat-05-relative-container-multi-paradigm-native-spec.md](05-ui-components/01-layout-components/08-relative-container/Feat-05-relative-container-multi-paradigm-native-spec.md) | Baselined |

### 05-01-09 Row

| FeatID | 特性名称 | Spec 文件 | 状态 |
|--------|----------|-----------|------|
| Feat-01 | Row 创建、尺寸与子项间距 | [Feat-01-row-creation-size-space-spec.md](05-ui-components/01-layout-components/09-row/Feat-01-row-creation-size-space-spec.md) | Baselined |
| Feat-02 | Row 对齐与反向排列 | [Feat-02-row-alignment-reverse-spec.md](05-ui-components/01-layout-components/09-row/Feat-02-row-alignment-reverse-spec.md) | Baselined |
| Feat-03 | Row 多范式接口与版本兼容 | [Feat-03-row-multi-paradigm-version-spec.md](05-ui-components/01-layout-components/09-row/Feat-03-row-multi-paradigm-version-spec.md) | Baselined |
| Feat-04 | Row PointLight 系统光效 | [Feat-04-row-point-light-spec.md](05-ui-components/01-layout-components/09-row/Feat-04-row-point-light-spec.md) | Baselined |

### 05-01-10 RowSplit

| FeatID | 特性名称 | Spec 文件 | 状态 |
|--------|----------|-----------|------|
| Feat-01 | RowSplit 水平分割布局与分隔线绘制 | [Feat-01-row-split-horizontal-layout-rendering-spec.md](05-ui-components/01-layout-components/10-row-split/Feat-01-row-split-horizontal-layout-rendering-spec.md) | Baselined |
| Feat-02 | RowSplit 可拖拽调整与边界约束 | [Feat-02-row-split-resizeable-drag-spec.md](05-ui-components/01-layout-components/10-row-split/Feat-02-row-split-resizeable-drag-spec.md) | Baselined |

### 05-01-11 Stack

| FeatID | 特性名称 | Spec 文件 | 状态 |
|--------|----------|-----------|------|
| Feat-01 | Stack 叠放布局、尺寸与对齐 | [Feat-01-stack-overlay-layout-alignment-spec.md](05-ui-components/01-layout-components/11-stack/Feat-01-stack-overlay-layout-alignment-spec.md) | Baselined |
| Feat-02 | Stack 子节点分帧加载与多范式接口 | [Feat-02-stack-sync-load-multi-paradigm-spec.md](05-ui-components/01-layout-components/11-stack/Feat-02-stack-sync-load-multi-paradigm-spec.md) | Baselined |
| Feat-03 | Stack PointLight 系统光效 | [Feat-03-stack-point-light-spec.md](05-ui-components/01-layout-components/11-stack/Feat-03-stack-point-light-spec.md) | Baselined |

### 05-01-12 FolderStack

| FeatID | 特性名称 | Spec 文件 | 状态 |
|--------|----------|-----------|------|
| Feat-01 | FolderStack 创建、分区与折痕避让 | [Feat-01-folder-stack-partition-crease-avoidance-spec.md](05-ui-components/01-layout-components/12-folder-stack/Feat-01-folder-stack-partition-crease-avoidance-spec.md) | Baselined |
| Feat-02 | FolderStack 折叠与悬停状态事件 | [Feat-02-folder-stack-fold-hover-events-spec.md](05-ui-components/01-layout-components/12-folder-stack/Feat-02-folder-stack-fold-hover-events-spec.md) | Baselined |
| Feat-03 | FolderStack 过渡动画、自动旋转与接口兼容 | [Feat-03-folder-stack-animation-auto-rotation-spec.md](05-ui-components/01-layout-components/12-folder-stack/Feat-03-folder-stack-animation-auto-rotation-spec.md) | Baselined |

### 05-01-13 DynamicLayout

| FeatID | 特性名称 | Spec 文件 | 状态 |
|--------|----------|-----------|------|
| Feat-01 | DynamicLayout 容器创建与运行时算法切换 | [Feat-01-dynamic-layout-runtime-switching-spec.md](05-ui-components/01-layout-components/13-dynamic-layout/Feat-01-dynamic-layout-runtime-switching-spec.md) | Baselined |
| Feat-02 | DynamicLayout 行列线性布局算法 | [Feat-02-dynamic-layout-linear-algorithms-spec.md](05-ui-components/01-layout-components/13-dynamic-layout/Feat-02-dynamic-layout-linear-algorithms-spec.md) | Baselined |
| Feat-03 | DynamicLayout 堆叠与网格布局算法 | [Feat-03-dynamic-layout-stack-grid-algorithms-spec.md](05-ui-components/01-layout-components/13-dynamic-layout/Feat-03-dynamic-layout-stack-grid-algorithms-spec.md) | Baselined |
| Feat-04 | DynamicLayout 自定义测量与布局算法 | [Feat-04-dynamic-layout-custom-algorithm-spec.md](05-ui-components/01-layout-components/13-dynamic-layout/Feat-04-dynamic-layout-custom-algorithm-spec.md) | Baselined |

### 05-02-01 Navigation

| FeatID | 特性名称 | Spec 文件 | 状态 |
|--------|----------|-----------|------|
| Feat-01 | 创建与布局模式 | [Feat-01-navigation-creation-layout-mode-spec.md](05-ui-components/02-navigation-components/01-navigation/Feat-01-navigation-creation-layout-mode-spec.md) | Baselined |
| Feat-02 | 标题栏配置 | [Feat-02-navigation-title-bar-spec.md](05-ui-components/02-navigation-components/01-navigation/Feat-02-navigation-title-bar-spec.md) | Baselined |
| Feat-03 | 工具栏配置 | [Feat-03-navigation-toolbar-spec.md](05-ui-components/02-navigation-components/01-navigation/Feat-03-navigation-toolbar-spec.md) | Baselined |
| Feat-04 | 路由栈管理 | [Feat-04-navigation-route-stack-spec.md](05-ui-components/02-navigation-components/01-navigation/Feat-04-navigation-route-stack-spec.md) | Baselined |
| Feat-05 | 转场动画与自定义过渡 | [Feat-05-navigation-transition-spec.md](05-ui-components/02-navigation-components/01-navigation/Feat-05-navigation-transition-spec.md) | Baselined |
| Feat-06 | 系统栏/安全区/分栏/恢复 | [Feat-06-navigation-system-bar-split-recovery-spec.md](05-ui-components/02-navigation-components/01-navigation/Feat-06-navigation-system-bar-split-recovery-spec.md) | Baselined |
| Feat-07 | 事件回调与Modifier | [Feat-07-navigation-events-modifier-spec.md](05-ui-components/02-navigation-components/01-navigation/Feat-07-navigation-events-modifier-spec.md) | Baselined |

### 05-02-02 NavRouter

| FeatID | 特性名称 | Spec 文件 | 状态 |
|--------|----------|-----------|------|

### 05-02-03 NavDestination

| FeatID | 特性名称 | Spec 文件 | 状态 |
|--------|----------|-----------|------|
| Feat-01 | NavDestination 创建与布局模式 | [Feat-01-nav-destination-creation-layout-mode-spec.md](05-ui-components/02-navigation-components/03-nav-destination/Feat-01-nav-destination-creation-layout-mode-spec.md) | Baselined |
| Feat-02 | NavDestination 标题栏与工具栏配置 | [Feat-02-nav-destination-title-toolbar-spec.md](05-ui-components/02-navigation-components/03-nav-destination/Feat-02-nav-destination-title-toolbar-spec.md) | Baselined |
| Feat-03 | NavDestination 生命周期与事件回调 | [Feat-03-nav-destination-lifecycle-events-spec.md](05-ui-components/02-navigation-components/03-nav-destination/Feat-03-nav-destination-lifecycle-events-spec.md) | Baselined |
| Feat-04 | NavDestination 模式/安全区/转场动画/状态恢复 | [Feat-04-nav-destination-mode-safe-area-transition-recovery-spec.md](05-ui-components/02-navigation-components/03-nav-destination/Feat-04-nav-destination-mode-safe-area-transition-recovery-spec.md) | Baselined |

### 05-02-04 Stepper/SetpperItem

| FeatID | 特性名称 | Spec 文件 | 状态 |
|--------|----------|-----------|------|

### 05-02-05 Navigator

| FeatID | 特性名称 | Spec 文件 | 状态 |
|--------|----------|-----------|------|

### 05-02-06 SideBarContainer

| FeatID | 特性名称 | Spec 文件 | 状态 |
|--------|----------|-----------|------|
| Feat-01 | 全量规格 | [Feat-01-side-bar-container-full-spec.md](05-ui-components/02-navigation-components/06-sidebar-container/Feat-01-side-bar-container-full-spec.md) | Baselined |

### 05-03-01 滚动公共能力

| FeatID | 特性名称 | Spec 文件 | 状态 |
|--------|----------|-----------|------|
| Feat-01 | 滚动条与内容视效 | [Feat-01-scrollbar-content-visual-spec.md](05-ui-components/03-scroll-container-components/01-scroll-common-capability/Feat-01-scrollbar-content-visual-spec.md) | Baselined |
| Feat-02 | 滚动交互与物理效果 | [Feat-02-scroll-interaction-physics-spec.md](05-ui-components/03-scroll-container-components/01-scroll-common-capability/Feat-02-scroll-interaction-physics-spec.md) | Baselined |
| Feat-03 | 嵌套滚动与内容边界 | [Feat-03-nested-scroll-content-boundary-spec.md](05-ui-components/03-scroll-container-components/01-scroll-common-capability/Feat-03-nested-scroll-content-boundary-spec.md) | Baselined |
| Feat-04 | 滚动事件生命周期 | [Feat-04-scroll-event-lifecycle-spec.md](05-ui-components/03-scroll-container-components/01-scroll-common-capability/Feat-04-scroll-event-lifecycle-spec.md) | Baselined |

### 05-03-02 AlaphabetIndexer

| FeatID | 特性名称 | Spec 文件 | 状态 |
|--------|----------|-----------|------|
| Feat-01 | AlphabetIndexer 创建与基础样式 | [Feat-01-alphabet-indexer-creation-basic-style-spec.md](05-ui-components/03-scroll-container-components/02-alphabet-indexer/Feat-01-alphabet-indexer-creation-basic-style-spec.md) | Baselined |
| Feat-02 | AlphabetIndexer Popup样式与交互 | [Feat-02-alphabet-indexer-popup-style-interaction-spec.md](05-ui-components/03-scroll-container-components/02-alphabet-indexer/Feat-02-alphabet-indexer-popup-style-interaction-spec.md) | Baselined |

### 05-03-03 ScrollBar

| FeatID | 特性名称 | Spec 文件 | 状态 |
|--------|----------|-----------|------|
| Feat-01 | ScrollBar 核心构造与绑定 | [Feat-01-scroll-bar-core-construction-binding-spec.md](05-ui-components/03-scroll-container-components/03-scroll-bar/Feat-01-scroll-bar-core-construction-binding-spec.md) | Baselined |
| Feat-02 | ScrollBar 行为与视觉扩展 | [Feat-02-scroll-bar-behavior-visual-extensions-spec.md](05-ui-components/03-scroll-container-components/03-scroll-bar/Feat-02-scroll-bar-behavior-visual-extensions-spec.md) | Baselined |

### 05-03-04 Grid/GridItem

| FeatID | 特性名称 | Spec 文件 | 状态 |
|--------|----------|-----------|------|
| Feat-01 | Grid 固定行列与单轴滚动布局 | [Feat-01-grid-fixed-scroll-layout-spec.md](05-ui-components/03-scroll-container-components/04-grid-grid-item/Feat-01-grid-fixed-scroll-layout-spec.md) | Baselined |
| Feat-02 | Grid 不规则、自适应与自定义布局 | [Feat-02-grid-irregular-adaptive-custom-layout-spec.md](05-ui-components/03-scroll-container-components/04-grid-grid-item/Feat-02-grid-irregular-adaptive-custom-layout-spec.md) | Baselined |
| Feat-03 | Grid 滚动控制、滚动条与事件 | [Feat-03-grid-scroll-scrollbar-events-spec.md](05-ui-components/03-scroll-container-components/04-grid-grid-item/Feat-03-grid-scroll-scrollbar-events-spec.md) | Baselined |
| Feat-04 | Grid 编辑模式与拖拽 | [Feat-04-grid-edit-mode-drag-spec.md](05-ui-components/03-scroll-container-components/04-grid-grid-item/Feat-04-grid-edit-mode-drag-spec.md) | Baselined |
| Feat-05 | GridItem 布局与选择 | [Feat-05-grid-item-layout-selection-spec.md](05-ui-components/03-scroll-container-components/04-grid-grid-item/Feat-05-grid-item-layout-selection-spec.md) | Baselined |
| Feat-06 | C API 与多范式接口 | [Feat-06-grid-capi-multi-paradigm-spec.md](05-ui-components/03-scroll-container-components/04-grid-grid-item/Feat-06-grid-capi-multi-paradigm-spec.md) | Baselined |

### 05-03-05 List/ListItem/ListItemGroup

| FeatID | 特性名称 | Spec 文件 | 状态 |
|--------|----------|-----------|------|
| Feat-01 | List 创建与核心布局（含懒加载/缓存） | [Feat-01-list-creation-core-layout-spec.md](05-ui-components/03-scroll-container-components/05-list-list-item-list-item-group/Feat-01-list-creation-core-layout-spec.md) | Baselined |
| Feat-02 | List 滚动运动学与边缘效果 | [Feat-02-list-scroll-kinematics-edge-effects-spec.md](05-ui-components/03-scroll-container-components/05-list-list-item-list-item-group/Feat-02-list-scroll-kinematics-edge-effects-spec.md) | Baselined |
| Feat-03 | List 滚动可观测性与控制器 | [Feat-03-list-scroll-observability-controller-spec.md](05-ui-components/03-scroll-container-components/05-list-list-item-list-item-group/Feat-03-list-scroll-observability-controller-spec.md) | Baselined |
| Feat-04 | List 分组/粘性头尾/Header/Footer | [Feat-04-list-grouping-sticky-header-footer-spec.md](05-ui-components/03-scroll-container-components/05-list-list-item-list-item-group/Feat-04-list-grouping-sticky-header-footer-spec.md) | Baselined |
| Feat-05 | List 选择与编辑模式 | [Feat-05-list-selection-edit-mode-spec.md](05-ui-components/03-scroll-container-components/05-list-list-item-list-item-group/Feat-05-list-selection-edit-mode-spec.md) | Baselined |
| Feat-06 | List 拖拽 | [Feat-06-list-item-drag-drop-spec.md](05-ui-components/03-scroll-container-components/05-list-list-item-list-item-group/Feat-06-list-item-drag-drop-spec.md) | Baselined |
| Feat-07 | ListItem 滑动操作 | [Feat-07-list-item-swipe-action-spec.md](05-ui-components/03-scroll-container-components/05-list-list-item-list-item-group/Feat-07-list-item-swipe-action-spec.md) | Baselined |

### 05-03-06 Refresh

| FeatID | 特性名称 | Spec 文件 | 状态 |
|--------|----------|-----------|------|
| Feat-01 | Refresh 创建、刷新状态生命周期与指示器内容 | [Feat-01-refresh-creation-state-lifecycle-indicator-spec.md](05-ui-components/03-scroll-container-components/06-refresh/Feat-01-refresh-creation-state-lifecycle-indicator-spec.md) | Baselined |
| Feat-02 | Refresh 下拉物理、触发/取消手势与偏移观测 | [Feat-02-refresh-pull-physics-gesture-offset-spec.md](05-ui-components/03-scroll-container-components/06-refresh/Feat-02-refresh-pull-physics-gesture-offset-spec.md) | Baselined |

### 05-03-07 Scroll

| FeatID | 特性名称 | Spec 文件 | 状态 |
|--------|----------|-----------|------|
| Feat-01 | Scroll 核心几何/方向与布局 | [Feat-01-scroll-core-geometry-layout-spec.md](05-ui-components/03-scroll-container-components/07-scroll/Feat-01-scroll-core-geometry-layout-spec.md) | Baselined |
| Feat-02 | Scroll 滚动条与视觉边缘效果 | [Feat-02-scroll-scrollbar-visual-edge-effects-spec.md](05-ui-components/03-scroll-container-components/07-scroll/Feat-02-scroll-scrollbar-visual-edge-effects-spec.md) | Baselined |
| Feat-03 | Scroll 滚动运动控制器 API | [Feat-03-scroll-motion-controller-api-spec.md](05-ui-components/03-scroll-container-components/07-scroll/Feat-03-scroll-motion-controller-api-spec.md) | Baselined |
| Feat-04 | Scroll 交互/手势与嵌套滚动 | [Feat-04-scroll-interaction-gesture-nested-scroll-spec.md](05-ui-components/03-scroll-container-components/07-scroll/Feat-04-scroll-interaction-gesture-nested-scroll-spec.md) | Baselined |
| Feat-05 | Scroll 滚动事件与可观测性 | [Feat-05-scroll-events-observability-spec.md](05-ui-components/03-scroll-container-components/07-scroll/Feat-05-scroll-events-observability-spec.md) | Baselined |
| Feat-06 | Scroll 分页与吸附对齐 | [Feat-06-scroll-paging-snap-alignment-spec.md](05-ui-components/03-scroll-container-components/07-scroll/Feat-06-scroll-paging-snap-alignment-spec.md) | Baselined |
| Feat-07 | Scroll 缩放与二维自由滚动 | [Feat-07-scroll-zoom-2d-free-scroll-spec.md](05-ui-components/03-scroll-container-components/07-scroll/Feat-07-scroll-zoom-2d-free-scroll-spec.md) | Baselined |

### 05-03-08 Swiper

| FeatID | 特性名称 | Spec 文件 | 状态 |
|--------|----------|-----------|------|
| Feat-01 | 创建与布局属性 | [Feat-01-swiper-creation-layout-spec.md](05-ui-components/03-scroll-container-components/08-swiper/Feat-01-swiper-creation-layout-spec.md) | Baselined |
| Feat-02 | 自动播放与指示器 | [Feat-02-swiper-autoplay-indicator-spec.md](05-ui-components/03-scroll-container-components/08-swiper/Feat-02-swiper-autoplay-indicator-spec.md) | Baselined |
| Feat-03 | 动画与过渡 | [Feat-03-swiper-animation-transition-spec.md](05-ui-components/03-scroll-container-components/08-swiper/Feat-03-swiper-animation-transition-spec.md) | Baselined |
| Feat-04 | 交互与控制器 | [Feat-04-swiper-interaction-controller-spec.md](05-ui-components/03-scroll-container-components/08-swiper/Feat-04-swiper-interaction-controller-spec.md) | Baselined |
| Feat-05 | 事件回调 | [Feat-05-swiper-events-spec.md](05-ui-components/03-scroll-container-components/08-swiper/Feat-05-swiper-events-spec.md) | Baselined |
| Feat-06 | C API 全量规格 | [Feat-06-swiper-capi-spec.md](05-ui-components/03-scroll-container-components/08-swiper/Feat-06-swiper-capi-spec.md) | Baselined |

### 05-03-09 Tabs/TabContent

| FeatID | 特性名称 | Spec 文件 | 状态 |
|--------|----------|-----------|------|
| Feat-01 | 创建与基础属性 | [Feat-01-tabs-creation-basic-properties-spec.md](05-ui-components/03-scroll-container-components/09-tabs-tab-content/Feat-01-tabs-creation-basic-properties-spec.md) | Baselined |
| Feat-02 | 标签栏样式 | [Feat-02-tabs-bar-style-spec.md](05-ui-components/03-scroll-container-components/09-tabs-tab-content/Feat-02-tabs-bar-style-spec.md) | Baselined |
| Feat-03 | 侧边栏模式 | [Feat-03-tabs-sidebar-mode-spec.md](05-ui-components/03-scroll-container-components/09-tabs-tab-content/Feat-03-tabs-sidebar-mode-spec.md) | Baselined |
| Feat-04 | 动画与自定义过渡 | [Feat-04-tabs-animation-transition-spec.md](05-ui-components/03-scroll-container-components/09-tabs-tab-content/Feat-04-tabs-animation-transition-spec.md) | Baselined |
| Feat-05 | 事件回调 | [Feat-05-tabs-events-spec.md](05-ui-components/03-scroll-container-components/09-tabs-tab-content/Feat-05-tabs-events-spec.md) | Baselined |
| Feat-06 | 缓存与滚动控制 | [Feat-06-tabs-cache-scroll-spec.md](05-ui-components/03-scroll-container-components/09-tabs-tab-content/Feat-06-tabs-cache-scroll-spec.md) | Baselined |

### 05-03-10 WaterFlow/FlowItem

| FeatID | 特性名称 | Spec 文件 | 状态 |
|--------|----------|-----------|------|
| Feat-01 | 组件创建、Footer 与 FlowItem | [Feat-01-creation-footer-flowitem-spec.md](05-ui-components/03-scroll-container-components/10-water-flow-flow-item/Feat-01-creation-footer-flowitem-spec.md) | Baselined |
| Feat-02 | 公共布局配置与 Item 约束 | [Feat-02-layout-config-item-constraint-spec.md](05-ui-components/03-scroll-container-components/10-water-flow-flow-item/Feat-02-layout-config-item-constraint-spec.md) | Baselined |
| Feat-03 | ALWAYS_TOP_DOWN 布局算法 | [Feat-03-always-top-down-layout-spec.md](05-ui-components/03-scroll-container-components/10-water-flow-flow-item/Feat-03-always-top-down-layout-spec.md) | Baselined |
| Feat-04 | SLIDING_WINDOW 布局算法 | [Feat-04-sliding-window-layout-spec.md](05-ui-components/03-scroll-container-components/10-water-flow-flow-item/Feat-04-sliding-window-layout-spec.md) | Baselined |
| Feat-05 | 滚动控制与事件 | [Feat-05-scroll-control-events-spec.md](05-ui-components/03-scroll-container-components/10-water-flow-flow-item/Feat-05-scroll-control-events-spec.md) | Baselined |
| Feat-06 | 缓存与懒加载 | [Feat-06-cache-lazy-loading-spec.md](05-ui-components/03-scroll-container-components/10-water-flow-flow-item/Feat-06-cache-lazy-loading-spec.md) | Baselined |

### 05-04-01 Button

| FeatID | 特性名称 | Spec 文件 | 状态 |
|--------|----------|-----------|------|
| Feat-01 | Button 组件全量规格 | [Feat-01-button-full-spec.md](05-ui-components/04-input-form-components/01-button/Feat-01-button-full-spec.md) | Baselined |

### 05-04-02 Checkbox/CheckboxGroup

| FeatID | 特性名称 | Spec 文件 | 状态 |
|--------|----------|-----------|------|
| Feat-01 | Checkbox/CheckboxGroup 组件全量规格 | [Feat-01-checkbox-full-spec.md](05-ui-components/04-input-form-components/02-checkbox-checkbox-group/Feat-01-checkbox-full-spec.md) | Baselined |

### 05-04-03 Rating

| FeatID | 特性名称 | Spec 文件 | 状态 |
|--------|----------|-----------|------|
| Feat-01 | Rating 组件全量规格 | [Feat-01-rating-full-spec.md](05-ui-components/04-input-form-components/03-rating/Feat-01-rating-full-spec.md) | Baselined |

### 05-04-04 Radio

| FeatID | 特性名称 | Spec 文件 | 状态 |
|--------|----------|-----------|------|
| Feat-01 | Radio/RadioGroup 组件全量规格 | [Feat-01-radio-full-spec.md](05-ui-components/04-input-form-components/04-radio/Feat-01-radio-full-spec.md) | Baselined |

### 05-04-05 Slider

| FeatID | 特性名称 | Spec 文件 | 状态 |
|--------|----------|-----------|------|
| Feat-01 | 创建、数值范围与布局样式 | [Feat-01-slider-creation-range-layout-spec.md](05-ui-components/04-input-form-components/05-slider/Feat-01-slider-creation-range-layout-spec.md) | Baselined |
| Feat-02 | 轨道、滑块与步点视觉 | [Feat-02-slider-track-block-step-visual-spec.md](05-ui-components/04-input-form-components/05-slider/Feat-02-slider-track-block-step-visual-spec.md) | Baselined |
| Feat-03 | 交互模式、事件与反馈 | [Feat-03-slider-interaction-events-feedback-spec.md](05-ui-components/04-input-form-components/05-slider/Feat-03-slider-interaction-events-feedback-spec.md) | Baselined |
| Feat-04 | 提示、自定义内容与无障碍内容 | [Feat-04-slider-tips-custom-accessibility-spec.md](05-ui-components/04-input-form-components/05-slider/Feat-04-slider-tips-custom-accessibility-spec.md) | Baselined |

### 05-04-06 Toggle

| FeatID | 特性名称 | Spec 文件 | 状态 |
|--------|----------|-----------|------|
| Feat-01 | Toggle 组件全量规格 | [Feat-01-toggle-spec.md](05-ui-components/04-input-form-components/06-toggle/Feat-01-toggle-spec.md) | Baselined |

### 05-05-01 Calendar/CalendarPicker

| FeatID | 特性名称 | Spec 文件 | 状态 |
|--------|----------|-----------|------|
| Feat-01 | CalendarPicker 组件全量规格 | [Feat-01-calendar-picker-full-spec.md](05-ui-components/05-picker-components/01-calendar-calendar-picker/Feat-01-calendar-picker-full-spec.md) | Baselined |

### 05-05-02 DatePicker

| FeatID | 特性名称 | Spec 文件 | 状态 |
|--------|----------|-----------|------|
| Feat-01 | DatePicker 组件全量规格 | [Feat-01-date-picker-full-spec.md](05-ui-components/05-picker-components/02-date-picker/Feat-01-date-picker-full-spec.md) | Baselined |

### 05-05-03 TextPicker

| FeatID | 特性名称 | Spec 文件 | 状态 |
|--------|----------|-----------|------|
| Feat-01 | TextPicker 组件全量规格 | [Feat-01-text-picker-full-spec.md](05-ui-components/05-picker-components/03-text-picker/Feat-01-text-picker-full-spec.md) | Baselined |

### 05-05-04 TimePicker

| FeatID | 特性名称 | Spec 文件 | 状态 |
|--------|----------|-----------|------|
| Feat-01 | TimePicker 组件全量规格 | [Feat-01-time-picker-full-spec.md](05-ui-components/05-picker-components/04-time-picker/Feat-01-time-picker-full-spec.md) | Baselined |

### 05-05-05 Select

| FeatID | 特性名称 | Spec 文件 | 状态 |
|--------|----------|-----------|------|
| Feat-01 | Select 组件全量规格 | [Feat-01-select-full-spec.md](05-ui-components/05-picker-components/05-select/Feat-01-select-full-spec.md) | Baselined |

### 05-05-06 Picker

| FeatID | 特性名称 | Spec 文件 | 状态 |
|--------|----------|-----------|------|
| Feat-01 | UIPickerComponent/Picker 组件全量规格 | [Feat-01-uipicker-component-full-spec.md](05-ui-components/05-picker-components/06-picker/Feat-01-uipicker-component-full-spec.md) | Baselined |

### 05-06-01 Menu/MenuItem/MenuItemGroup

| FeatID | 特性名称 | Spec 文件 | 状态 |
|--------|----------|-----------|------|
| Feat-01 | bindMenu/bindContextMenu 绑定与触发机制 | [Feat-01-bind-menu-trigger-spec.md](05-ui-components/06-popup-components/01-menu-menu-item-menu-item-group/Feat-01-bind-menu-trigger-spec.md) | Baselined |
| Feat-02 | Menu/MenuItem/MenuItemGroup 创建与属性 | [Feat-02-menu-creation-properties-spec.md](05-ui-components/06-popup-components/01-menu-menu-item-menu-item-group/Feat-02-menu-creation-properties-spec.md) | Baselined |
| Feat-03 | 子菜单展开、布局避让、动画与预览 | [Feat-03-submenu-layout-animation-spec.md](05-ui-components/06-popup-components/01-menu-menu-item-menu-item-group/Feat-03-submenu-layout-animation-spec.md) | Baselined |

### 05-06-02 警告弹窗

| FeatID | 特性名称 | Spec 文件 | 状态 |
|--------|----------|-----------|------|
| Feat-01 | AlertDialog 警告弹窗全量规格 | [Feat-01-alert-dialog-full-spec.md](05-ui-components/06-popup-components/02-alert-dialog/Feat-01-alert-dialog-full-spec.md) | Baselined |

### 05-06-03 列表选择弹窗

| FeatID | 特性名称 | Spec 文件 | 状态 |
|--------|----------|-----------|------|
| Feat-01 | ActionSheet 列表选择弹窗全量规格 | [Feat-01-action-sheet-full-spec.md](05-ui-components/06-popup-components/03-list-selection-dialog/Feat-01-action-sheet-full-spec.md) | Baselined |

### 05-06-04 自定义弹窗

| FeatID | 特性名称 | Spec 文件 | 状态 |
|--------|----------|-----------|------|
| Feat-01 | CustomDialogController 生命周期与布局属性及命令式弹窗 API | [Feat-01-custom-dialog-lifecycle-layout-spec.md](05-ui-components/06-popup-components/04-custom-dialog/Feat-01-custom-dialog-lifecycle-layout-spec.md) | Baselined |
| Feat-02 | AlertDialog/ActionSheet 命令式 API | [Feat-02-alert-action-sheet-spec.md](05-ui-components/06-popup-components/04-custom-dialog/Feat-02-alert-action-sheet-spec.md) | Baselined |
| Feat-03 | Dialog C API（ArkUI_NativeDialogAPI_1/2/3、OH_ArkUI_CustomDialog 函数族） | [Feat-03-dialog-capi-spec.md](05-ui-components/06-popup-components/04-custom-dialog/Feat-03-dialog-capi-spec.md) | Baselined |

### 05-06-05 CalendarPickerDialog

| FeatID | 特性名称 | Spec 文件 | 状态 |
|--------|----------|-----------|------|
| Feat-01 | CalendarPickerDialog 完整能力 | [Feat-01-calendar-picker-dialog-spec.md](05-ui-components/06-popup-components/05-calendar-picker-dialog/Feat-01-calendar-picker-dialog-spec.md) | Baselined |

### 05-06-06 DatePickerDialog

| FeatID | 特性名称 | Spec 文件 | 状态 |
|--------|----------|-----------|------|
| Feat-01 | DatePickerDialog 完整能力 | [Feat-01-date-picker-dialog-spec.md](05-ui-components/06-popup-components/06-date-picker-dialog/Feat-01-date-picker-dialog-spec.md) | Baselined |

### 05-06-07 TimePickerDialog

| FeatID | 特性名称 | Spec 文件 | 状态 |
|--------|----------|-----------|------|
| Feat-01 | TimePickerDialog 完整能力 | [Feat-01-time-picker-dialog-spec.md](05-ui-components/06-popup-components/07-time-picker-dialog/Feat-01-time-picker-dialog-spec.md) | Baselined |

### 05-06-08 TextPickerDialog

| FeatID | 特性名称 | Spec 文件 | 状态 |
|--------|----------|-----------|------|
| Feat-01 | TextPickerDialog 完整能力 | [Feat-01-text-picker-dialog-spec.md](05-ui-components/06-popup-components/08-text-picker-dialog/Feat-01-text-picker-dialog-spec.md) | Baselined |

### 05-06-09 ContextMenu接口

| FeatID | 特性名称 | Spec 文件 | 状态 |
|--------|----------|-----------|------|
| Feat-01 | ContextMenu 接口全量规格 | [Feat-01-context-menu-full-spec.md](05-ui-components/06-popup-components/09-context-menu/Feat-01-context-menu-full-spec.md) | Baselined |

### 05-06-10 promptAction接口

| FeatID | 特性名称 | Spec 文件 | 状态 |
|--------|----------|-----------|------|
| Feat-01 | promptAction 接口全量规格 (Toast/Dialog/OpenMenu) | [Feat-01-prompt-action-full-spec.md](05-ui-components/06-popup-components/10-prompt-action/Feat-01-prompt-action-full-spec.md) | Baselined |

### 05-06-11 popup弹窗

| FeatID | 特性名称 | Spec 文件 | 状态 |
|--------|----------|-----------|------|
| Feat-01 | bindPopup 属性绑定与气泡布局 | [Feat-01-bind-popup-bubble-layout-spec.md](05-ui-components/06-popup-components/11-popup/Feat-01-bind-popup-bubble-layout-spec.md) | Baselined |
| Feat-02 | 命令式 Popup API (openPopup / updatePopup / closePopup) | [Feat-02-imperative-popup-api-spec.md](05-ui-components/06-popup-components/11-popup/Feat-02-imperative-popup-api-spec.md) | Baselined |

### 05-07-01 半模态弹窗

| FeatID | 特性名称 | Spec 文件 | 状态 |
|--------|----------|-----------|------|
| Feat-01 | bindSheet 半模态弹窗全量规格 | [Feat-01-sheet-modal-full-spec.md](05-ui-components/07-modal-components/01-sheet-modal/Feat-01-sheet-modal-full-spec.md) | Baselined |

### 05-07-02 全模态弹窗

| FeatID | 特性名称 | Spec 文件 | 状态 |
|--------|----------|-----------|------|
| Feat-01 | bindContentCover 全模态弹窗全量规格 | [Feat-01-full-modal-full-spec.md](05-ui-components/07-modal-components/02-full-modal/Feat-01-full-modal-full-spec.md) | Baselined |

### 05-07-03 Panel

| FeatID | 特性名称 | Spec 文件 | 状态 |
|--------|----------|-----------|------|

### 05-08-01 Image

| FeatID | 特性名称 | Spec 文件 | 状态 |
|--------|----------|-----------|------|
| Feat-01 | 核心显示属性 | [Feat-01-image-core-display-spec.md](05-ui-components/08-image-components/01-image/Feat-01-image-core-display-spec.md) | Baselined |
| Feat-02 | 颜色与效果 | [Feat-02-image-color-effects-spec.md](05-ui-components/08-image-components/01-image/Feat-02-image-color-effects-spec.md) | Baselined |
| Feat-03 | 高级功能 | [Feat-03-image-advanced-spec.md](05-ui-components/08-image-components/01-image/Feat-03-image-advanced-spec.md) | Baselined |
| Feat-04 | 事件回调 | [Feat-04-image-events-spec.md](05-ui-components/08-image-components/01-image/Feat-04-image-events-spec.md) | Baselined |
| Feat-05 | Image 组件基础内存与加载上下文生命周期 | [Feat-05-image-base-memory-opt-spec.md](05-ui-components/08-image-components/01-image/Feat-05-image-base-memory-opt-spec.md) | Baselined |

### 05-08-02 ImageAnimator

| FeatID | 特性名称 | Spec 文件 | 状态 |
|--------|----------|-----------|------|
| Feat-01 | ImageAnimator 帧数据与显示缓存 | [Feat-01-image-animator-frame-data-cache-spec.md](05-ui-components/08-image-components/02-image-animator/Feat-01-image-animator-frame-data-cache-spec.md) | Baselined |
| Feat-02 | ImageAnimator 播放控制与可见性联动 | [Feat-02-image-animator-playback-control-spec.md](05-ui-components/08-image-components/02-image-animator/Feat-02-image-animator-playback-control-spec.md) | Baselined |
| Feat-03 | ImageAnimator 事件回调与多范式接口 | [Feat-03-image-animator-events-interfaces-spec.md](05-ui-components/08-image-components/02-image-animator/Feat-03-image-animator-events-interfaces-spec.md) | Baselined |

### 05-08-03 MediaCachedImage

| FeatID | 特性名称 | Spec 文件 | 状态 |
|--------|----------|-----------|------|

### 05-09-01 Marquee

| FeatID | 特性名称 | Spec 文件 | 状态 |
|--------|----------|-----------|------|

### 05-09-02 RichEditor

| FeatID | 特性名称 | Spec 文件 | 状态 |
|--------|----------|-----------|------|
| Feat-01 | 组件初始化与双模式架构 | [Feat-01-component-init-dual-mode-spec.md](05-ui-components/09-text-components/02-rich-editor/Feat-01-component-init-dual-mode-spec.md) | Baselined |
| Feat-02 | Span内容管理-增删改查与跨模式转换 | [Feat-02-span-content-management-spec.md](05-ui-components/09-text-components/02-rich-editor/Feat-02-span-content-management-spec.md) | Baselined |
| Feat-03 | 属性字符串模式管理 | [Feat-03-styled-string-mode-management-spec.md](05-ui-components/09-text-components/02-rich-editor/Feat-03-styled-string-mode-management-spec.md) | Baselined |
| Feat-04 | 文本排版与显示优化 | [Feat-04-text-layout-display-optimization-spec.md](05-ui-components/09-text-components/02-rich-editor/Feat-04-text-layout-display-optimization-spec.md) | Baselined |
| Feat-05 | 视觉样式与交互反馈 | [Feat-05-visual-style-interaction-feedback-spec.md](05-ui-components/09-text-components/02-rich-editor/Feat-05-visual-style-interaction-feedback-spec.md) | Baselined |
| Feat-06 | 键盘与输入法交互 | [Feat-06-keyboard-ime-interaction-spec.md](05-ui-components/09-text-components/02-rich-editor/Feat-06-keyboard-ime-interaction-spec.md) | Baselined |
| Feat-07 | 编辑生命周期与内容变化事件 | [Feat-07-editing-lifecycle-content-events-spec.md](05-ui-components/09-text-components/02-rich-editor/Feat-07-editing-lifecycle-content-events-spec.md) | Baselined |
| Feat-08 | 光标选择与编辑状态控制 | [Feat-08-cursor-selection-editing-state-spec.md](05-ui-components/09-text-components/02-rich-editor/Feat-08-cursor-selection-editing-state-spec.md) | Baselined |
| Feat-09 | 剪贴板、数据检测与菜单定制 | [Feat-09-clipboard-data-detection-menu-spec.md](05-ui-components/09-text-components/02-rich-editor/Feat-09-clipboard-data-detection-menu-spec.md) | Baselined |

### 05-09-03 Search

| FeatID | 特性名称 | Spec 文件 | 状态 |
|--------|----------|-----------|------|

### 05-09-04 Text

| FeatID | 特性名称 | Spec 文件 | 状态 |
|--------|----------|-----------|------|
| Feat-01 | 字体属性与自适应字体 | [Feat-01-font-properties-spec.md](05-ui-components/09-text-components/04-text/Feat-01-font-properties-spec.md) | Baselined |
| Feat-02 | 行/段落布局 | [Feat-02-line-paragraph-layout-spec.md](05-ui-components/09-text-components/04-text/Feat-02-line-paragraph-layout-spec.md) | Baselined |
| Feat-03 | 溢出与截断 | [Feat-03-overflow-truncation-spec.md](05-ui-components/09-text-components/04-text/Feat-03-overflow-truncation-spec.md) | Baselined |
| Feat-04 | 装饰与样式 (decoration/textShadow/textCase/shaderStyle/contentTransition/marqueeOptions) | [Feat-04-decoration-styles-spec.md](05-ui-components/09-text-components/04-text/Feat-04-decoration-styles-spec.md) | Baselined |
| Feat-05 | 选择与复制 | [Feat-05-selection-copy-spec.md](05-ui-components/09-text-components/04-text/Feat-05-selection-copy-spec.md) | Baselined |
| Feat-06 | 系统能力（数据检测、隐私、震感） | [Feat-06-system-capabilities-spec.md](05-ui-components/09-text-components/04-text/Feat-06-system-capabilities-spec.md) | Baselined |
| Feat-07 | 事件回调 (onCopy/onWillCopy/onTextSelectionChange/onMarqueeStateChange) | [Feat-07-event-callbacks-spec.md](05-ui-components/09-text-components/04-text/Feat-07-event-callbacks-spec.md) | Baselined |

### 05-09-05 TextArea

| FeatID | 特性名称 | Spec 文件 | 状态 |
|--------|----------|-----------|------|

### 05-09-06 Span类

| FeatID | 特性名称 | Spec 文件 | 状态 |
|--------|----------|-----------|------|

### 05-09-07 SymbolGlyph

| FeatID | 特性名称 | Spec 文件 | 状态 |
|--------|----------|-----------|------|
| Feat-01 | 字形选择与创建 (symbolId/SymbolType/fontFamilies/createFrameNode) | [Feat-01-glyph-selection-creation-spec.md](05-ui-components/09-text-components/07-symbol-glyph/Feat-01-glyph-selection-creation-spec.md) | Baselined |
| Feat-02 | 字体属性 (fontSize/fontWeight/可变字体/minFontScale/maxFontScale) | [Feat-02-font-properties-spec.md](05-ui-components/09-text-components/07-symbol-glyph/Feat-02-font-properties-spec.md) | Baselined |
| Feat-03 | 颜色与渐变填充 (fontColor/symbolColor/shaderStyle) | [Feat-03-color-gradient-fill-spec.md](05-ui-components/09-text-components/07-symbol-glyph/Feat-03-color-gradient-fill-spec.md) | Baselined |
| Feat-04 | 渲染策略 (renderingStrategy) | [Feat-04-rendering-strategy-spec.md](05-ui-components/09-text-components/07-symbol-glyph/Feat-04-rendering-strategy-spec.md) | Baselined |
| Feat-05 | 动效策略与选项 (effectStrategy/SymbolEffectOptions/active-trigger) | [Feat-05-effect-strategy-options-spec.md](05-ui-components/09-text-components/07-symbol-glyph/Feat-05-effect-strategy-options-spec.md) | Baselined |
| Feat-06 | SymbolEffect 子类与参数 (7 个 typed effect 对象) | [Feat-06-symbol-effect-subclasses-spec.md](05-ui-components/09-text-components/07-symbol-glyph/Feat-06-symbol-effect-subclasses-spec.md) | Baselined |
| Feat-07 | 符号阴影 (symbolShadow) | [Feat-07-symbol-shadow-spec.md](05-ui-components/09-text-components/07-symbol-glyph/Feat-07-symbol-shadow-spec.md) | Baselined |
| Feat-08 | 多范式接口与通用能力 (attributeModifier/clip/继承通用面/无障碍) | [Feat-08-multi-paradigm-interface-spec.md](05-ui-components/09-text-components/07-symbol-glyph/Feat-08-multi-paradigm-interface-spec.md) | Baselined |

### 05-09-08 TextInput

| FeatID | 特性名称 | Spec 文件 | 状态 |
|--------|----------|-----------|------|
| Feat-01 | 基础显示与字体样式 (type/style/font/textAlign/letterSpacing/lineHeight/overflow/decoration/wordBreak 等) | [Feat-01-base-display-font-style-spec.md](05-ui-components/09-text-components/08-text-input/Feat-01-base-display-font-style-spec.md) | Baselined |
| Feat-02 | Placeholder 与错误提示 (placeholderColor/placeholderFont/showError/showUnit/showUnderline/underlineColor) | [Feat-02-placeholder-error-spec.md](05-ui-components/09-text-components/08-text-input/Feat-02-placeholder-error-spec.md) | Baselined |
| Feat-03 | 输入类型与控制 (type/contentType/enableKeyboardOnFocus/editing/selectAll/copyOption/selectionMenuHidden/editMenuOptions/enablePreviewText) | [Feat-03-input-type-control-spec.md](05-ui-components/09-text-components/08-text-input/Feat-03-input-type-control-spec.md) | Baselined |
| Feat-04 | 文本筛选与 maxLength/计数器 (maxLength/inputFilter/showCounter) | [Feat-04-filter-maxlength-counter-spec.md](05-ui-components/09-text-components/08-text-input/Feat-04-filter-maxlength-counter-spec.md) | Baselined |
| Feat-05 | 光标与选择 (caretColor/caretStyle/caretPosition/selectedBackgroundColor/textSelection/onTextSelectionChange/onContentScroll) | [Feat-05-caret-selection-spec.md](05-ui-components/09-text-components/08-text-input/Feat-05-caret-selection-spec.md) | Baselined |
| Feat-06 | 编辑与内容事件回调 (onChange/onWillChange/onSubmit/onEditChange/onWillInsert/onDidInsert/onWillDelete/onDidDelete/onCopy/onCut/onPaste/onSecurityStateChange) | [Feat-06-editing-content-events-spec.md](05-ui-components/09-text-components/08-text-input/Feat-06-editing-content-events-spec.md) | Baselined |
| Feat-07 | 键盘/IME/自定义键盘 (enterKeyType/keyboardAppearance/customKeyboard/autoCapitalizationMode/enableFillAnimation/blurOnSubmit) | [Feat-07-keyboard-ime-spec.md](05-ui-components/09-text-components/08-text-input/Feat-07-keyboard-ime-spec.md) | Baselined |
| Feat-08 | 密码与自动填充 (passwordIcon/showPasswordIcon/showPassword/passwordRules/enableAutoFill/enableAutoFillAnimation) | [Feat-08-password-autofill-spec.md](05-ui-components/09-text-components/08-text-input/Feat-08-password-autofill-spec.md) | Baselined |
| Feat-09 | 取消按钮/响应区域 (cancelButton/cancelButtonSymbol/cleanNodeStyle/isShowCancelButton/isShowVoiceButton) | [Feat-09-cancel-button-response-area-spec.md](05-ui-components/09-text-components/08-text-input/Feat-09-cancel-button-response-area-spec.md) | Baselined |
| Feat-10 | C-API/NDK Modifier 桥与无障碍 (ARKUI_NODE_TEXT_INPUT + 51 NODE_TEXT_INPUT_* + 18 事件 + 枚举 + userAccessibilityText) | [Feat-10-capi-ndk-bridge-a11y-spec.md](05-ui-components/09-text-components/08-text-input/Feat-10-capi-ndk-bridge-a11y-spec.md) | Baselined |

### 05-09-09 HyperLink

| FeatID | 特性名称 | Spec 文件 | 状态 |
|--------|----------|-----------|------|
| Feat-01 | 链接配置与颜色样式 (构造/address/content 兜底/color + API18 主题色派生 + 继承 Text 样式 + 资源注册) | [Feat-01-link-config-color-style-spec.md](05-ui-components/09-text-components/09-hyperlink/Feat-01-link-config-color-style-spec.md) | Baselined |
| Feat-02 | 拖拽/响应区域/状态视觉/导航 (draggable/responseRegion/hover-press-visited-disabled 视觉/LinkToAddress+preventDefault) | [Feat-02-drag-response-state-navigation-spec.md](05-ui-components/09-text-components/09-hyperlink/Feat-02-drag-response-state-navigation-spec.md) | Baselined |
| Feat-03 | 键盘无障碍与多前端 C-API 桥 (KEY_SPACE/ENTER 激活/focus/OnInjectionEvent/C-API modifier 动态静态CJ/Inspector序列化) | [Feat-03-keyboard-a11y-capi-bridge-spec.md](05-ui-components/09-text-components/09-hyperlink/Feat-03-keyboard-a11y-capi-bridge-spec.md) | Baselined |

### 05-09-10 属性字符串

| FeatID | 特性名称 | Spec 文件 | 状态 |
|--------|----------|-----------|------|
| Feat-01 | 容器与核心操作 (StyledString/MutableStyledString + StyleOptions/SpanStyle/StyledStringKey + TLV序列化 + HTML往返) | [Feat-01-container-core-operations-spec.md](05-ui-components/09-text-components/10-attributed-string/Feat-01-container-core-operations-spec.md) | Baselined |
| Feat-02 | TextStyle 字体属性 (fontColor/fontFamily/fontSize/fontWeight/fontStyle + 桥接扩展) | [Feat-02-textstyle-font-spec.md](05-ui-components/09-text-components/10-attributed-string/Feat-02-textstyle-font-spec.md) | Baselined |
| Feat-03 | 装饰排版 Style (DecorationStyle/BaselineOffsetStyle/LetterSpacingStyle/LineHeightStyle/TextShadowStyle) | [Feat-03-decoration-typography-style-spec.md](05-ui-components/09-text-components/10-attributed-string/Feat-03-decoration-typography-style-spec.md) | Baselined |
| Feat-04 | 背景/超链接 Style (BackgroundColorStyle/UrlStyle) | [Feat-04-background-url-style-spec.md](05-ui-components/09-text-components/10-attributed-string/Feat-04-background-url-style-spec.md) | Baselined |
| Feat-05 | ParagraphStyle 段落属性 (textAlign/textIndent/maxLines/overflow/wordBreak/leadingMargin/paragraphSpacing + 桥接扩展) | [Feat-05-paragraph-style-spec.md](05-ui-components/09-text-components/10-attributed-string/Feat-05-paragraph-style-spec.md) | Baselined |
| Feat-06 | GestureStyle 手势 (onClick/onLongPress + span 级命中) | [Feat-06-gesture-style-spec.md](05-ui-components/09-text-components/10-attributed-string/Feat-06-gesture-style-spec.md) | Baselined |
| Feat-07 | 图片/自定义/UserData Span (ImageAttachment/CustomSpan/UserDataSpan↔ExtSpan) | [Feat-07-image-custom-userdata-span-spec.md](05-ui-components/09-text-components/10-attributed-string/Feat-07-image-custom-userdata-span-spec.md) | Baselined |
| Feat-08 | 宿主集成 (StyledStringController/ChangedListener + Text/RichEditor/TextField + LayoutManager + Undo/Redo) | [Feat-08-host-integration-spec.md](05-ui-components/09-text-components/10-attributed-string/Feat-08-host-integration-spec.md) | Baselined |
| Feat-09 | C-API/NDK/ANI (OH_ArkUI_StyledString_* + 对象模型 accessor + ANI modifier) | [Feat-09-capi-ndk-ani-spec.md](05-ui-components/09-text-components/10-attributed-string/Feat-09-capi-ndk-ani-spec.md) | Baselined |

### 05-10-01 DataPanel

| FeatID | 特性名称 | Spec 文件 | 状态 |
|--------|----------|-----------|------|

### 05-10-02 Gauge

| FeatID | 特性名称 | Spec 文件 | 状态 |
|--------|----------|-----------|------|

### 05-10-03 LoadingProgress

| FeatID | 特性名称 | Spec 文件 | 状态 |
|--------|----------|-----------|------|

### 05-10-04 PatternLock

| FeatID | 特性名称 | Spec 文件 | 状态 |
|--------|----------|-----------|------|

### 05-10-05 Progress

| FeatID | 特性名称 | Spec 文件 | 状态 |
|--------|----------|-----------|------|

### 05-10-06 QRCode

| FeatID | 特性名称 | Spec 文件 | 状态 |
|--------|----------|-----------|------|

### 05-10-07 TextClock

| FeatID | 特性名称 | Spec 文件 | 状态 |
|--------|----------|-----------|------|

### 05-10-08 TextTimer

| FeatID | 特性名称 | Spec 文件 | 状态 |
|--------|----------|-----------|------|

### 05-10-09 Badge

| FeatID | 特性名称 | Spec 文件 | 状态 |
|--------|----------|-----------|------|

### 05-10-10 Counter

| FeatID | 特性名称 | Spec 文件 | 状态 |
|--------|----------|-----------|------|

### 05-11-01 FormComponent

| FeatID | 特性名称 | Spec 文件 | 状态 |
|--------|----------|-----------|------|

### 05-11-02 FormLink

| FeatID | 特性名称 | Spec 文件 | 状态 |
|--------|----------|-----------|------|

### 05-12-01 PluginComponent

| FeatID | 特性名称 | Spec 文件 | 状态 |
|--------|----------|-----------|------|

### 05-12-02 AbilityComponent

| FeatID | 特性名称 | Spec 文件 | 状态 |
|--------|----------|-----------|------|
| Feat-01 | AbilityComponent 跨进程能力嵌入（已废弃） | [Feat-01-ability-component-cross-process-embed-deprecated-spec.md](05-ui-components/12-embedded-display-components/02-ability-component/Feat-01-ability-component-cross-process-embed-deprecated-spec.md) | Baselined |

### 05-12-03 UIExtensionComponent

| FeatID | 特性名称 | Spec 文件 | 状态 |
|--------|----------|-----------|------|

### 05-12-04 EmbeddedComponent

| FeatID | 特性名称 | Spec 文件 | 状态 |
|--------|----------|-----------|------|

### 05-12-05 IsolatedComponent

| FeatID | 特性名称 | Spec 文件 | 状态 |
|--------|----------|-----------|------|

### 05-12-06 SecurityUIExtensionComponent

| FeatID | 特性名称 | Spec 文件 | 状态 |
|--------|----------|-----------|------|

### 05-12-07 DynamicComponent

| FeatID | 特性名称 | Spec 文件 | 状态 |
|--------|----------|-----------|------|

### 05-13-01 XComponent

| FeatID | 特性名称 | Spec 文件 | 状态 |
|--------|----------|-----------|------|
| Feat-01 | 创建、类型与表面生命周期（核心） | [Feat-01-creation-type-surface-lifecycle-spec.md](05-ui-components/13-platform-components/01-xcomponent/Feat-01-creation-type-surface-lifecycle-spec.md) | Baselined |
| Feat-02 | XComponentController 表面与画布控制 | [Feat-02-controller-surface-canvas-spec.md](05-ui-components/13-platform-components/01-xcomponent/Feat-02-controller-surface-canvas-spec.md) | Baselined |
| Feat-03 | 经典 NDK 输入事件（touch/mouse/key/focus/blur/hover） | [Feat-03-ndk-input-events-spec.md](05-ui-components/13-platform-components/01-xcomponent/Feat-03-ndk-input-events-spec.md) | Baselined |
| Feat-04 | SurfaceHolder/SurfaceCallback V2 表面模型 | [Feat-04-surface-holder-v2-spec.md](05-ui-components/13-platform-components/01-xcomponent/Feat-04-surface-holder-v2-spec.md) | Baselined |
| Feat-05 | 帧率与显示同步（DisplaySync） | [Feat-05-frame-rate-display-sync-spec.md](05-ui-components/13-platform-components/01-xcomponent/Feat-05-frame-rate-display-sync-spec.md) | Baselined |
| Feat-06 | HDR 亮度与背景色 | [Feat-06-hdr-brightness-background-spec.md](05-ui-components/13-platform-components/01-xcomponent/Feat-06-hdr-brightness-background-spec.md) | Baselined |
| Feat-07 | AI 图像分析（analyzer） | [Feat-07-ai-image-analyzer-spec.md](05-ui-components/13-platform-components/01-xcomponent/Feat-07-ai-image-analyzer-spec.md) | Baselined |
| Feat-08 | 无障碍 provider | [Feat-08-accessibility-provider-spec.md](05-ui-components/13-platform-components/01-xcomponent/Feat-08-accessibility-provider-spec.md) | Baselined |

### 05-13-02 Video

| FeatID | 特性名称 | Spec 文件 | 状态 |
|--------|----------|-----------|------|
| Feat-01 | 显示、播放与事件 | [Feat-01-video-display-playback-events-spec.md](05-ui-components/13-platform-components/02-video/Feat-01-video-display-playback-events-spec.md) | Baselined |
| Feat-02 | 控制器与全屏 | [Feat-02-video-controller-fullscreen-spec.md](05-ui-components/13-platform-components/02-video/Feat-02-video-controller-fullscreen-spec.md) | Baselined |
| Feat-03 | 高级能力（AI/Poster/快捷键） | [Feat-03-video-advanced-capabilities-spec.md](05-ui-components/13-platform-components/02-video/Feat-03-video-advanced-capabilities-spec.md) | Baselined |

### 05-14-01 Shape

| FeatID | 特性名称 | Spec 文件 | 状态 |
|--------|----------|-----------|------|
| Feat-01 | Shape 容器、视口与 Mesh | [Feat-01-shape-container-viewport-mesh-spec.md](05-ui-components/14-drawing-components/01-shape/Feat-01-shape-container-viewport-mesh-spec.md) | Baselined |
| Feat-02 | Shape 通用绘制样式 | [Feat-02-shape-common-paint-style-spec.md](05-ui-components/14-drawing-components/01-shape/Feat-02-shape-common-paint-style-spec.md) | Baselined |
| Feat-03 | Shape 基础闭合图形 | [Feat-03-shape-basic-closed-geometry-spec.md](05-ui-components/14-drawing-components/01-shape/Feat-03-shape-basic-closed-geometry-spec.md) | Baselined |
| Feat-04 | Shape 点集图形 | [Feat-04-shape-point-geometry-spec.md](05-ui-components/14-drawing-components/01-shape/Feat-04-shape-point-geometry-spec.md) | Baselined |
| Feat-05 | Shape Path 命令绘制 | [Feat-05-shape-path-commands-spec.md](05-ui-components/14-drawing-components/01-shape/Feat-05-shape-path-commands-spec.md) | Baselined |
| Feat-06 | Shape 多范式与 Modifier | [Feat-06-shape-multi-paradigm-modifier-spec.md](05-ui-components/14-drawing-components/01-shape/Feat-06-shape-multi-paradigm-modifier-spec.md) | Baselined |

### 05-14-02 Canvas

| FeatID | 特性名称 | Spec 文件 | 状态 |
|--------|----------|-----------|------|
| Feat-01 | Canvas 组件、上下文与生命周期 | [Feat-01-canvas-component-context-lifecycle-spec.md](05-ui-components/14-drawing-components/02-canvas/Feat-01-canvas-component-context-lifecycle-spec.md) | Baselined |
| Feat-02 | Canvas 路径几何与裁剪 | [Feat-02-canvas-path-geometry-clipping-spec.md](05-ui-components/14-drawing-components/02-canvas/Feat-02-canvas-path-geometry-clipping-spec.md) | Baselined |
| Feat-03 | Canvas 绘制样式与合成 | [Feat-03-canvas-paint-style-composition-spec.md](05-ui-components/14-drawing-components/02-canvas/Feat-03-canvas-paint-style-composition-spec.md) | Baselined |
| Feat-04 | Canvas 状态栈与几何变换 | [Feat-04-canvas-state-transform-spec.md](05-ui-components/14-drawing-components/02-canvas/Feat-04-canvas-state-transform-spec.md) | Baselined |
| Feat-05 | Canvas 文本绘制与度量 | [Feat-05-canvas-text-rendering-metrics-spec.md](05-ui-components/14-drawing-components/02-canvas/Feat-05-canvas-text-rendering-metrics-spec.md) | Baselined |
| Feat-06 | Canvas 图像与像素交换 | [Feat-06-canvas-image-pixel-interchange-spec.md](05-ui-components/14-drawing-components/02-canvas/Feat-06-canvas-image-pixel-interchange-spec.md) | Baselined |
| Feat-07 | Canvas 图像分析与多范式兼容 | [Feat-07-canvas-image-analysis-multi-paradigm-spec.md](05-ui-components/14-drawing-components/02-canvas/Feat-07-canvas-image-analysis-multi-paradigm-spec.md) | Baselined |

### 05-14-03 OffscreenCanvas

| FeatID | 特性名称 | Spec 文件 | 状态 |
|--------|----------|-----------|------|
| Feat-01 | OffscreenCanvas 离屏表面与上下文 | [Feat-01-offscreen-canvas-surface-context-spec.md](05-ui-components/14-drawing-components/03-offscreen-canvas/Feat-01-offscreen-canvas-surface-context-spec.md) | Baselined |
| Feat-02 | OffscreenCanvas 离屏二维绘制上下文 | [Feat-02-offscreen-canvas-rendering-context-spec.md](05-ui-components/14-drawing-components/03-offscreen-canvas/Feat-02-offscreen-canvas-rendering-context-spec.md) | Baselined |
| Feat-03 | OffscreenCanvas 图像导出与转移 | [Feat-03-offscreen-canvas-export-transfer-spec.md](05-ui-components/14-drawing-components/03-offscreen-canvas/Feat-03-offscreen-canvas-export-transfer-spec.md) | Baselined |

### 05-15-01 WithTheme

| FeatID | 特性名称 | Spec 文件 | 状态 |
|--------|----------|-----------|------|
| Feat-01 | WithTheme 主题作用域组件全量规格 | [Feat-01-with-theme-full-spec.md](05-ui-components/15-theme-components/01-with-theme/Feat-01-with-theme-full-spec.md) | Baselined |

### 05-16-01 NodeContainer

| FeatID | 特性名称 | Spec 文件 | 状态 |
|--------|----------|-----------|------|
| Feat-01 | NodeContainer 渲染宿主与 FrameNode 桥接 | [Feat-01-node-container-render-host-and-framenode-bridge-spec.md](05-ui-components/16-custom-placeholder-components/01-node-container/Feat-01-node-container-render-host-and-framenode-bridge-spec.md) | Baselined |
| Feat-02 | NodeController 生命周期回调 | [Feat-02-nodecontroller-lifecycle-callbacks-spec.md](05-ui-components/16-custom-placeholder-components/01-node-container/Feat-02-nodecontroller-lifecycle-callbacks-spec.md) | Baselined |
| Feat-03 | 复用与纹理导出 | [Feat-03-reuse-and-texture-export-spec.md](05-ui-components/16-custom-placeholder-components/01-node-container/Feat-03-reuse-and-texture-export-spec.md) | Baselined |

### 05-16-02 ContentSlot

| FeatID | 特性名称 | Spec 文件 | 状态 |
|--------|----------|-----------|------|
| Feat-01 | ContentSlot 语法节点与 NodeContent 内容管理 | [Feat-01-contentslot-syntax-node-and-nodecontent-management-spec.md](05-ui-components/16-custom-placeholder-components/02-content-slot/Feat-01-contentslot-syntax-node-and-nodecontent-management-spec.md) | Baselined |

### 06-01-01 跨语言封装

| FeatID | 特性名称 | Spec 文件 | 状态 |
|--------|----------|-----------|------|

### 06-01-02 JS引擎管理

| FeatID | 特性名称 | Spec 文件 | 状态 |
|--------|----------|-----------|------|

### 06-01-03 IDL工具

| FeatID | 特性名称 | Spec 文件 | 状态 |
|--------|----------|-----------|------|

### 06-02-01 Inner-组件能力接口

| FeatID | 特性名称 | Spec 文件 | 状态 |
|--------|----------|-----------|------|

### 06-02-02 Inner-基础能力接口

| FeatID | 特性名称 | Spec 文件 | 状态 |
|--------|----------|-----------|------|

### 06-03-01 类Web范式

| FeatID | 特性名称 | Spec 文件 | 状态 |
|--------|----------|-----------|------|

### 06-03-02 ArkTS卡片

| FeatID | 特性名称 | Spec 文件 | 状态 |
|--------|----------|-----------|------|

### 06-03-03 JS卡片

| FeatID | 特性名称 | Spec 文件 | 状态 |
|--------|----------|-----------|------|

### 06-03-04 FA模型

| FeatID | 特性名称 | Spec 文件 | 状态 |
|--------|----------|-----------|------|

### 06-03-05 仓颉接入层

| FeatID | 特性名称 | Spec 文件 | 状态 |
|--------|----------|-----------|------|

### 07-01-01 Chip

| FeatID | 特性名称 | Spec 文件 | 状态 |
|--------|----------|-----------|------|

### 07-01-02 ChipGroup

| FeatID | 特性名称 | Spec 文件 | 状态 |
|--------|----------|-----------|------|

### 07-01-03 ComposeListItem

| FeatID | 特性名称 | Spec 文件 | 状态 |
|--------|----------|-----------|------|

### 07-01-04 ComposeTitleBar

| FeatID | 特性名称 | Spec 文件 | 状态 |
|--------|----------|-----------|------|

### 07-01-05 Counter

| FeatID | 特性名称 | Spec 文件 | 状态 |
|--------|----------|-----------|------|

### 07-01-06 Dialog

| FeatID | 特性名称 | Spec 文件 | 状态 |
|--------|----------|-----------|------|

### 07-01-07 DownloadFileButton

| FeatID | 特性名称 | Spec 文件 | 状态 |
|--------|----------|-----------|------|

### 07-01-08 EditableTitleBar

| FeatID | 特性名称 | Spec 文件 | 状态 |
|--------|----------|-----------|------|

### 07-01-09 ExceptionPrompt

| FeatID | 特性名称 | Spec 文件 | 状态 |
|--------|----------|-----------|------|

### 07-01-10 Filter

| FeatID | 特性名称 | Spec 文件 | 状态 |
|--------|----------|-----------|------|

### 07-01-11 FormMenu

| FeatID | 特性名称 | Spec 文件 | 状态 |
|--------|----------|-----------|------|

### 07-01-12 ProgressButton

| FeatID | 特性名称 | Spec 文件 | 状态 |
|--------|----------|-----------|------|

### 07-01-13 FullScreenLaunchComponent

| FeatID | 特性名称 | Spec 文件 | 状态 |
|--------|----------|-----------|------|

### 07-01-14 GridObjectSortComponent

| FeatID | 特性名称 | Spec 文件 | 状态 |
|--------|----------|-----------|------|

### 07-01-15 ProgressButton

| FeatID | 特性名称 | Spec 文件 | 状态 |
|--------|----------|-----------|------|

### 07-01-16 Popup

| FeatID | 特性名称 | Spec 文件 | 状态 |
|--------|----------|-----------|------|
| Feat-01 | Popup 高级组件全量规格 | [Feat-01-popup-advanced-full-spec.md](07-frontend/01-arkts-advanced-components/16-popup/Feat-01-popup-advanced-full-spec.md) | Baselined |

### 07-01-17 SegmentButton

| FeatID | 特性名称 | Spec 文件 | 状态 |
|--------|----------|-----------|------|

### 07-01-18 SelectionMenu

| FeatID | 特性名称 | Spec 文件 | 状态 |
|--------|----------|-----------|------|

### 07-01-19 SelectTitleBar

| FeatID | 特性名称 | Spec 文件 | 状态 |
|--------|----------|-----------|------|

### 07-01-20 SplitLayout

| FeatID | 特性名称 | Spec 文件 | 状态 |
|--------|----------|-----------|------|

### 07-01-21 SubHeader

| FeatID | 特性名称 | Spec 文件 | 状态 |
|--------|----------|-----------|------|

### 07-01-22 SwipeRefresher

| FeatID | 特性名称 | Spec 文件 | 状态 |
|--------|----------|-----------|------|

### 07-01-23 TabTitleBar

| FeatID | 特性名称 | Spec 文件 | 状态 |
|--------|----------|-----------|------|

### 07-01-24 ToolBar

| FeatID | 特性名称 | Spec 文件 | 状态 |
|--------|----------|-----------|------|

### 07-01-25 TreeView

| FeatID | 特性名称 | Spec 文件 | 状态 |
|--------|----------|-----------|------|

### 07-01-26 FoldSplitContainer

| FeatID | 特性名称 | Spec 文件 | 状态 |
|--------|----------|-----------|------|

### 07-02-01 状态管理V1组件内状态管理

| FeatID | 特性名称 | Spec 文件 | 状态 |
|--------|----------|-----------|------|
| Feat-01 | V1 依赖收集与变更通知核心机制 | [Feat-01-v1-dependency-collection-and-change-notification-spec.md](07-frontend/02-state-management/01-v1-component-state/Feat-01-v1-dependency-collection-and-change-notification-spec.md) | Baselined |
| Feat-02 | @State 组件私有状态 | [Feat-02-state-decorator-spec.md](07-frontend/02-state-management/01-v1-component-state/Feat-02-state-decorator-spec.md) | Baselined |
| Feat-03 | @Prop/@Link 父子单向/双向同步 | [Feat-03-prop-link-decorators-spec.md](07-frontend/02-state-management/01-v1-component-state/Feat-03-prop-link-decorators-spec.md) | Baselined |
| Feat-04 | @Provide/@Consume 跨层级同步 | [Feat-04-provide-consume-decorators-spec.md](07-frontend/02-state-management/01-v1-component-state/Feat-04-provide-consume-decorators-spec.md) | Baselined |
| Feat-05 | @ObjectLink 嵌套对象共享引用 | [Feat-05-objectlink-spec.md](07-frontend/02-state-management/01-v1-component-state/Feat-05-objectlink-spec.md) | Baselined |
| Feat-06 | @Watch 变更回调与组件冻结 | [Feat-06-watch-and-component-freeze-spec.md](07-frontend/02-state-management/01-v1-component-state/Feat-06-watch-and-component-freeze-spec.md) | Baselined |
| Feat-07 | SubscribableAbstract 自定义可观察类型 | [Feat-07-subscribable-abstract-spec.md](07-frontend/02-state-management/01-v1-component-state/Feat-07-subscribable-abstract-spec.md) | Baselined |
| Feat-08 | 状态管理调试与渲染基础设施 | [Feat-08-debug-render-infra-spec.md](07-frontend/02-state-management/01-v1-component-state/Feat-08-debug-render-infra-spec.md) | Baselined |
| Feat-09 | elmtId 全链路同步与 C++ 宿主集成 | [Feat-09-elmtid-sync-cpp-host-spec.md](07-frontend/02-state-management/01-v1-component-state/Feat-09-elmtid-sync-cpp-host-spec.md) | Baselined |

### 07-02-02 状态管理V1数据对象内状态管理

| FeatID | 特性名称 | Spec 文件 | 状态 |
|--------|----------|-----------|------|
| Feat-01 | @Observed/@Track 数据对象观测与属性级追踪 | [Feat-01-observed-track-spec.md](07-frontend/02-state-management/02-v1-data-object-state/Feat-01-observed-track-spec.md) | Baselined |

### 07-02-03 状态管理V1应用内状态管理

| FeatID | 特性名称 | Spec 文件 | 状态 |
|--------|----------|-----------|------|
| Feat-01 | LocalStorage 页面级存储 | [Feat-01-localstorage-spec.md](07-frontend/02-state-management/03-v1-app-state/Feat-01-localstorage-spec.md) | Baselined |
| Feat-02 | AppStorage 全局存储与存储装饰器 | [Feat-02-appstorage-spec.md](07-frontend/02-state-management/03-v1-app-state/Feat-02-appstorage-spec.md) | Baselined |
| Feat-03 | PersistentStorage 磁盘持久化 | [Feat-03-persistent-storage-spec.md](07-frontend/02-state-management/03-v1-app-state/Feat-03-persistent-storage-spec.md) | Baselined |
| Feat-04 | Environment 设备环境变量 | [Feat-04-environment-spec.md](07-frontend/02-state-management/03-v1-app-state/Feat-04-environment-spec.md) | Baselined |

### 07-02-04 状态管理V2组件内状态管理

| FeatID | 特性名称 | Spec 文件 | 状态 |
|--------|----------|-----------|------|
| Feat-01 | ObserveV2 核心机制 | [Feat-01-observev2-core-mechanism-spec.md](07-frontend/02-state-management/04-v2-component-state/Feat-01-observev2-core-mechanism-spec.md) | Baselined |
| Feat-02 | @Local/@Param/@Once/@Event 组件状态输入输出 | [Feat-02-local-param-once-event-decorators-spec.md](07-frontend/02-state-management/04-v2-component-state/Feat-02-local-param-once-event-decorators-spec.md) | Baselined |
| Feat-03 | @Provider/@Consumer V2 跨层同步 | [Feat-03-provider-consumer-decorators-spec.md](07-frontend/02-state-management/04-v2-component-state/Feat-03-provider-consumer-decorators-spec.md) | Baselined |
| Feat-04 | V1↔V2 迁移与混用规则 | [Feat-04-v1-v2-migration-spec.md](07-frontend/02-state-management/04-v2-component-state/Feat-04-v1-v2-migration-spec.md) | Baselined |
| Feat-05 | ConfigureStateMgmt 特性开关 | [Feat-05-configure-state-mgmt-spec.md](07-frontend/02-state-management/04-v2-component-state/Feat-05-configure-state-mgmt-spec.md) | Baselined |

### 07-02-05 状态管理V2数据对象内状态管理

| FeatID | 特性名称 | Spec 文件 | 状态 |
|--------|----------|-----------|------|
| Feat-01 | @ObservedV2/@Trace 可观察数据模型 | [Feat-01-observedv2-trace-decorators-spec.md](07-frontend/02-state-management/05-v2-data-object-state/Feat-01-observedv2-trace-decorators-spec.md) | Baselined |
| Feat-02 | @Computed/@Monitor/@SyncMonitor 计算与监听 | [Feat-02-computed-monitor-syncmonitor-decorators-spec.md](07-frontend/02-state-management/05-v2-data-object-state/Feat-02-computed-monitor-syncmonitor-decorators-spec.md) | Baselined |

### 07-02-06 状态管理V2应用内状态管理

| FeatID | 特性名称 | Spec 文件 | 状态 |
|--------|----------|-----------|------|
| Feat-01 | AppStorageV2 内存全局存储 | [Feat-01-appstoragev2-spec.md](07-frontend/02-state-management/06-v2-app-state/Feat-01-appstoragev2-spec.md) | Baselined |
| Feat-02 | PersistenceV2 磁盘持久化与 @Type/DataCoder | [Feat-02-persistencev2-spec.md](07-frontend/02-state-management/06-v2-app-state/Feat-02-persistencev2-spec.md) | Baselined |

### 07-02-07 状态管理辅助接口

| FeatID | 特性名称 | Spec 文件 | 状态 |
|--------|----------|-----------|------|
| Feat-01 | UIUtils 对象工具 | [Feat-01-uiutils-object-tools-spec.md](07-frontend/02-state-management/07-state-management-utilities/Feat-01-uiutils-object-tools-spec.md) | Baselined |
| Feat-02 | UIUtils 监听与同步刷新 | [Feat-02-uiutils-monitor-flush-spec.md](07-frontend/02-state-management/07-state-management-utilities/Feat-02-uiutils-monitor-flush-spec.md) | Baselined |

### 07-02-08 静态V1组件内状态管理

| FeatID | 特性名称 | Spec 文件 | 状态 |
|--------|----------|-----------|------|
| Feat-01 | V1 核心机制与 IStateMgmtFactory 工厂 | *待补充* | 待补充 |
| Feat-02 | @State/@Prop/@PropRef 组件内与父子单向同步 | *待补充* | 待补充 |
| Feat-03 | @Link 父子双向同步 | *待补充* | 待补充 |
| Feat-04 | @Provide/@Consume 跨层级同步 | *待补充* | 待补充 |
| Feat-05 | @ObjectLink 嵌套对象共享引用 | *待补充* | 待补充 |
| Feat-06 | @Watch 变更回调 | *待补充* | 待补充 |

### 07-02-09 静态V1数据对象内状态管理

| FeatID | 特性名称 | Spec 文件 | 状态 |
|--------|----------|-----------|------|
| Feat-01 | @Observed InterfaceProxyHandler 代理与内置容器观测 | *待补充* | 待补充 |
| Feat-02 | @Track 属性级精确追踪 | *待补充* | 待补充 |

### 07-02-10 静态V1应用内状态管理

| FeatID | 特性名称 | Spec 文件 | 状态 |
|--------|----------|-----------|------|
| Feat-01 | LocalStorage 页面级存储 | *待补充* | 待补充 |
| Feat-02 | AppStorage 全局存储 | *待补充* | 待补充 |
| Feat-03 | PersistentStorage 磁盘持久化 | *待补充* | 待补充 |
| Feat-04 | Environment 设备环境变量 | *待补充* | 待补充 |
| Feat-05 | 存储联动装饰器（@StorageLink/@StorageProp/@StoragePropRef/@LocalStorageLink/@LocalStoragePropRef） | *待补充* | 待补充 |

### 07-02-11 静态V2组件内状态管理

| FeatID | 特性名称 | Spec 文件 | 状态 |
|--------|----------|-----------|------|
| Feat-01 | V2 核心机制（DecoratedV2VariableBase + StateUpdateLoop + autoProxyObject） | *待补充* | 待补充 |
| Feat-02 | @Local/@Param/@ParamOnce/@Provider/@Consumer 组件状态输入输出 | *待补充* | 待补充 |
| Feat-03 | @Monitor/@SyncMonitor 路径感知监听 | *待补充* | 待补充 |
| Feat-04 | @Computed 惰性计算属性 | *待补充* | 待补充 |

### 07-02-12 静态V2数据对象内状态管理

| FeatID | 特性名称 | Spec 文件 | 状态 |
|--------|----------|-----------|------|
| Feat-01 | @ObservedV2/@Trace V2 可观察数据模型（UIPlugin 转换 MutableStateMeta） | *待补充* | 待补充 |

### 07-02-13 静态V2应用内状态管理

| FeatID | 特性名称 | Spec 文件 | 状态 |
|--------|----------|-----------|------|
| Feat-01 | AppStorageV2 内存全局存储 | *待补充* | 待补充 |
| Feat-02 | PersistenceV2 磁盘持久化与 V2CollectionCoder | *待补充* | 待补充 |

### 07-02-14 状态管理互操作

| FeatID | 特性名称 | Spec 文件 | 状态 |
|--------|----------|-----------|------|
| Feat-01 | 互操作核心机制（InteropState + openInterop + register 回调） | *待补充* | 待补充 |
| Feat-02 | 跨前端存储互操作 | *待补充* | 待补充 |
| Feat-03 | 跨前端组件互操作 | *待补充* | 待补充 |
| Feat-04 | 跨前端状态代理 | *待补充* | 待补充 |
| Feat-05 | Builder 与 Binding 互操作 | *待补充* | 待补充 |

### 07-03-01 组件化

| FeatID | 特性名称 | Spec 文件 | 状态 |
|--------|----------|-----------|------|
| Feat-01 | @Component/@ComponentV2 自定义组件声明与创建 | [Feat-01-component-declaration-creation-spec.md](07-frontend/03-custom-components/01-componentization/Feat-01-component-declaration-creation-spec.md) | Baselined |

### 07-03-02 自定义组件生命周期

| FeatID | 特性名称 | Spec 文件 | 状态 |
|--------|----------|-----------|------|
| Feat-01 | 自定义组件生命周期 | [Feat-01-component-lifecycle-spec.md](07-frontend/03-custom-components/02-component-lifecycle/Feat-01-component-lifecycle-spec.md) | Baselined |

### 07-03-03 自定义组件复用

| FeatID | 特性名称 | Spec 文件 | 状态 |
|--------|----------|-----------|------|
| Feat-01 | 自定义组件复用机制 | [Feat-01-component-reuse-spec.md](07-frontend/03-custom-components/03-component-reuse/Feat-01-component-reuse-spec.md) | Baselined |

### 07-03-04 自定义组件冻结

| FeatID | 特性名称 | Spec 文件 | 状态 |
|--------|----------|-----------|------|
| Feat-01 | 自定义组件冻结机制 | [Feat-01-component-freeze-spec.md](07-frontend/03-custom-components/04-component-freeze/Feat-01-component-freeze-spec.md) | Baselined |

### 07-03-05 自定义测量/布局

| FeatID | 特性名称 | Spec 文件 | 状态 |
|--------|----------|-----------|------|
| Feat-01 | 自定义组件测量与子项放置 | [Feat-01-custom-measure-layout-spec.md](07-frontend/03-custom-components/05-custom-measure-layout/Feat-01-custom-measure-layout-spec.md) | Baselined |

### 07-03-06 组件扩展

| FeatID | 特性名称 | Spec 文件 | 状态 |
|--------|----------|-----------|------|

### 07-03-07 静态自定义组件状态相关

| FeatID | 特性名称 | Spec 文件 | 状态 |
|--------|----------|-----------|------|

### 07-04-01 A2UI标准协议

| FeatID | 特性名称 | Spec 文件 | 状态 |
|--------|----------|-----------|------|

### 07-04-02 A2UI扩展协议

| FeatID | 特性名称 | Spec 文件 | 状态 |
|--------|----------|-----------|------|

### 07-04-03 A2UI高级垂域组件

| FeatID | 特性名称 | Spec 文件 | 状态 |
|--------|----------|-----------|------|

### 07-05-01 渲染控制语法

| FeatID | 特性名称 | Spec 文件 | 状态 |
|--------|----------|-----------|------|
| Feat-01 | if/else 条件渲染语法 | [Feat-01-if-else-conditional-rendering-spec.md](07-frontend/05-render-control/01-render-control-syntax/Feat-01-if-else-conditional-rendering-spec.md) | Baselined |
| Feat-02 | ForEach 循环渲染语法 | [Feat-02-foreach-loop-rendering-spec.md](07-frontend/05-render-control/01-render-control-syntax/Feat-02-foreach-loop-rendering-spec.md) | Baselined |
| Feat-03 | 渲染控制语法共享框架 | [Feat-03-shared-syntax-node-framework-spec.md](07-frontend/05-render-control/01-render-control-syntax/Feat-03-shared-syntax-node-framework-spec.md) | Baselined |

### 07-05-02 LazyForEach

| FeatID | 特性名称 | Spec 文件 | 状态 |
|--------|----------|-----------|------|
| Feat-01 | LazyForEach 核心语法与按需渲染 | [Feat-01-lazy-foreach-core-syntax-and-on-demand-rendering-spec.md](07-frontend/05-render-control/02-lazy-foreach/Feat-01-lazy-foreach-core-syntax-and-on-demand-rendering-spec.md) | Baselined |
| Feat-02 | 数据源契约与单条变更通知 | [Feat-02-data-source-contract-and-single-change-notification-spec.md](07-frontend/05-render-control/02-lazy-foreach/Feat-02-data-source-contract-and-single-change-notification-spec.md) | Baselined |
| Feat-03 | 批量数据集变更 onDatasetChange | [Feat-03-ondatasetchange-bulk-operations-spec.md](07-frontend/05-render-control/02-lazy-foreach/Feat-03-ondatasetchange-bulk-operations-spec.md) | Baselined |
| Feat-04 | 选项策略与内存/冻结优化 | [Feat-04-options-strategy-memory-and-freeze-optimization-spec.md](07-frontend/05-render-control/02-lazy-foreach/Feat-04-options-strategy-memory-and-freeze-optimization-spec.md) | Baselined |
| Feat-05 | 拖拽排序 onMove | [Feat-05-onmove-drag-reorder-spec.md](07-frontend/05-render-control/02-lazy-foreach/Feat-05-onmove-drag-reorder-spec.md) | Baselined |

### 07-05-03 Repeat

| FeatID | 特性名称 | Spec 文件 | 状态 |
|--------|----------|-----------|------|
| Feat-01 | Repeat 核心语法与非虚拟渲染 | [Feat-01-repeat-core-syntax-and-non-virtual-rendering-spec.md](07-frontend/05-render-control/03-repeat/Feat-01-repeat-core-syntax-and-non-virtual-rendering-spec.md) | Baselined |
| Feat-02 | Repeat 虚拟滚动（v2；v1 已废弃） | [Feat-02-repeat-virtual-scroll-v1-v2-spec.md](07-frontend/05-render-control/03-repeat/Feat-02-repeat-virtual-scroll-v1-v2-spec.md) | Baselined |
| Feat-03 | Repeat 模板化渲染与复用 | [Feat-03-repeat-template-rendering-and-reuse-spec.md](07-frontend/05-render-control/03-repeat/Feat-03-repeat-template-rendering-and-reuse-spec.md) | Baselined |
| Feat-04 | Repeat 内存优化策略 | [Feat-04-repeat-memory-optimization-strategy-spec.md](07-frontend/05-render-control/03-repeat/Feat-04-repeat-memory-optimization-strategy-spec.md) | Baselined |

### 07-06-01 系统环境变量

| FeatID | 特性名称 | Spec 文件 | 状态 |
|--------|----------|-----------|------|

### 07-06-02 自定义环境变量

| FeatID | 特性名称 | Spec 文件 | 状态 |
|--------|----------|-----------|------|

### 08-01-01 基础机制NativeModule

| FeatID | 特性名称 | Spec 文件 | 状态 |
|--------|----------|-----------|------|

### 08-01-02 组件API

| FeatID | 特性名称 | Spec 文件 | 状态 |
|--------|----------|-----------|------|

### 08-01-03 动效NativeAnimate

| FeatID | 特性名称 | Spec 文件 | 状态 |
|--------|----------|-----------|------|

### 08-01-04 视效接口

| FeatID | 特性名称 | Spec 文件 | 状态 |
|--------|----------|-----------|------|

### 08-01-05 事件EventModule

| FeatID | 特性名称 | Spec 文件 | 状态 |
|--------|----------|-----------|------|

### 08-01-06 弹窗NativeDialog

| FeatID | 特性名称 | Spec 文件 | 状态 |
|--------|----------|-----------|------|

### 08-01-07 手势NativeGesture

| FeatID | 特性名称 | Spec 文件 | 状态 |
|--------|----------|-----------|------|

### 08-01-08 文本StyledString

| FeatID | 特性名称 | Spec 文件 | 状态 |
|--------|----------|-----------|------|

### 08-01-09 绘制DrawableDescriptor

| FeatID | 特性名称 | Spec 文件 | 状态 |
|--------|----------|-----------|------|

### 08-01-10 组件扩展

| FeatID | 特性名称 | Spec 文件 | 状态 |
|--------|----------|-----------|------|

### 08-01-11 布局接口

| FeatID | 特性名称 | Spec 文件 | 状态 |
|--------|----------|-----------|------|

### 08-02-01 Native XComponent

| FeatID | 特性名称 | Spec 文件 | 状态 |
|--------|----------|-----------|------|

### 09-01-01 组件预览

| FeatID | 特性名称 | Spec 文件 | 状态 |
|--------|----------|-----------|------|

### 09-01-02 基础预览

| FeatID | 特性名称 | Spec 文件 | 状态 |
|--------|----------|-----------|------|

### 09-01-03 动态预览

| FeatID | 特性名称 | Spec 文件 | 状态 |
|--------|----------|-----------|------|

### 09-01-04 热加载

| FeatID | 特性名称 | Spec 文件 | 状态 |
|--------|----------|-----------|------|

### 09-02-01 工具链

| FeatID | 特性名称 | Spec 文件 | 状态 |
|--------|----------|-----------|------|

### 09-03-01 入门指南文档

| FeatID | 特性名称 | Spec 文件 | 状态 |
|--------|----------|-----------|------|

### 09-03-02 API指南文档

| FeatID | 特性名称 | Spec 文件 | 状态 |
|--------|----------|-----------|------|

### 09-04-01 能力示范sample

| FeatID | 特性名称 | Spec 文件 | 状态 |
|--------|----------|-----------|------|

### 09-05-01 ComponnetTest测试框架

| FeatID | 特性名称 | Spec 文件 | 状态 |
|--------|----------|-----------|------|

### 10-01-01 弧形组件

| FeatID | 特性名称 | Spec 文件 | 状态 |
|--------|----------|-----------|------|
| Feat-01 | ArcSlider 弧形滑块组件全量规格 | [Feat-01-arc-slider-full-spec.md](10-product-customization/01-wearable/01-arc-component/Feat-01-arc-slider-full-spec.md) | Baselined |
| Feat-02 | ArcButton 弧形按钮组件全量规格 | [Feat-02-arc-button-full-spec.md](10-product-customization/01-wearable/01-arc-component/Feat-02-arc-button-full-spec.md) | Baselined |

---

## 注册规则

1. **新增功能域**：在 `registry/functions.yaml` 中添加 FuncID 记录；如 `design.md` 尚未创建，`design` 字段置空；重新生成 `index.md`。
2. **新增特性**：仅在具体规格补录开始、功能点/特性范围明确后，在 `registry/features.yaml` 中追加 FeatID 记录，包含 FuncID、FeatID、特性名称、Spec 文件、状态（`待补充`/`Draft`/`Baselined`/`Deprecated`）。
3. **排序规则**：功能域按 FuncID 数值升序排列（`03-01-01` < `04-03-01` < `05-01-01`）；同一功能域内 FeatID 按 `Feat-01, Feat-02, ...` 顺序递增。
4. **状态流转**：待补充 → Draft → Baselined（经评审通过后）→ Deprecated（被新特性替代）。
5. **目录命名**：使用英文 slug（小写 + 短横线分隔），编号使用两位数字（`01-`, `02-`, ...）。
6. **FeatID 编号**：同一功能域内从 `Feat-01` 顺序递增；历史功能域导入时不根据 Excel `一级功能点` 自动生成 FeatID。

---

## 术语表

### 规格文档结构

| 缩写 | 全称 | 中文 | 说明 |
|------|------|------|------|
| **US** | User Story | 用户故事 | 以“作为...我想要...以便...”格式描述用户需求。每个 US 包含多个 AC |
| **AC** | Acceptance Criterion | 验收标准 | 每个 US 下的可验证行为描述。编号格式 `AC-<US号>.<序号>`，如 `AC-1.3` |
| **BR** | Business Rule | 业务规则 | 领域语义约束，描述跨多个 US 的业务级规则 |
| **FR** | Functional Rule | 功能规则 | 具体行为规则，描述单个可观察的功能行为 |
| **ER** | Exception/Exemption Rule | 异常/豁免规则 | 边界条件、异常输入的处理规则 |
| **RC** | Recovery Contract | 恢复契约 | 错误恢复路径和重置行为的契约描述 |

### 设计文档结构

| 缩写 | 全称 | 中文 | 说明 |
|------|------|------|------|
| **ADR** | Architecture Decision Record | 架构决策记录 | 记录关键设计决策，包含问题、推荐方案、替代方案、取舍理由、影响。格式：基线用 `ADR-N`（首个特性），后续特性用 `ADR-FX-N`（如 `ADR-F3-1`） |
| **FuncID** | Functional Domain ID | 功能域编号 | 3 段数字标识（如 `04-03-01`），唯一标识一个功能域 |
| **FeatID** | Feature ID | 特性编号 | `Feat-NN` 格式，功能域内唯一 |

### 验证/测试

| 缩写 | 全称 | 中文 | 说明 |
|------|------|------|------|
| **XTS** | X Test Suite | 兼容性测试套件 | OpenHarmony 兼容性测试，位于 `test/xts/` 目录 |
| **Gherkin** | — | Gherkin 语法 | 行为驱动开发（BDD）的场景描述语言：`Given/When/Then` |
| **VM** | Verification Mapping | 验证映射 | 每个 AC 到验证手段的映射表 |

---

## 文件命名规范

| 文件类型 | 命名格式 | 示例 |
|----------|----------|------|
| 设计文档 | `design.md` | `04-common-capability/03-common-attributes/01-layout-attributes/design.md` |
| 特性规格 | `Feat-NN-<name>-spec.md` | `04-common-capability/03-common-attributes/01-layout-attributes/Feat-03-flex-properties-spec.md` |
| 索引文件 | `index.md` | `index.md`（本文件） |

## 流程关联

```
新特性补录流程:
  1. 在 registry/functions.yaml 中确认/创建 FuncID
  2. 具体规格补录开始、功能点/特性范围明确后，在 registry/features.yaml 中追加 FeatID 记录；未生成规格时状态为待补充
  3. 创建 <func-domain>/ 目录（如不存在）
  4. 生成/更新 design.md，并将 functions.yaml 的 design 字段从空值改为路径
  5. 生成 Feat-NN-<name>-spec.md，并将 features.yaml 的 spec 字段从空值改为路径
  6. 更新 features.yaml 特性状态为 Draft 或 Baselined
  7. 运行 tools/generate_index.py 重新生成 index.md
```
