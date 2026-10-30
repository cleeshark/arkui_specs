# 架构设计

## 设计元数据

| 字段 | 内容 |
|------|------|
| Design ID | DESIGN-Func-07-01-17 |
| 功能域 | 07-01-17 SegmentButton |
| 目标 Feature | Feat-01：SegmentButton 可配置拖拽交互模式 |
| 关联需求 | 20260807944693 |
| 目标版本 | API 26.1.0 |
| Owner | lixingchi1 |
| 状态 | Draft |

本文件回灌已归档需求的设计和已合入修正规则，行为以[Feat-01规格](Feat-01-segment-button-interaction-mode-spec.md)为准。本PR仅补文档、注册及生成索引。

## 需求基线

V1页签/胶囊单选与V2页签/胶囊单选可配置普通或跟手拖拽。省略参数保留材质相关旧缺省；模式只改变拖拽定位和选中提交时机。材质反馈、点击和多选边界保留。已确认的V2非材质越界释放修正规则适用于动态、静态。

历史输入与审批来源为[已合入需求归档!1224](https://gitcode.com/OpenHarmonyAI/design-docs/merge_requests/1224)。归档的26.2.0是早期记录，本长期规格采用后续确认且已进入公开SDK的26.1.0。

## 上下文和现状

动态组件源位于advanced_ui_component，发布执行文件位于各组件interfaces下；静态实现位于advanced_ui_component_static。V1由Options保存模式，V2的Tab/Capsule单选参数传入共用的SimpleSegmentButtonV2。多选不增加模式合同。

### 代码事实基线

Engine核对版本为5f7584ef3a2e733560b37675371ca3ec226af24d，SDK为33dbfc29d999f1bdd54bc9fd06fa9cb400a96ece。代码引用用于约束实现落点，不代表本次重新执行设备验收。

| 引用 | 已验证事实 | 设计约束 |
|------|------------|----------|
| `advanced_ui_component/segmentbutton/source/segmentbutton.ets:2138` / isFollowingDragEnabled | 0显式跟手；配置系统材质且不是普通模式时使用跟手缺省 | 不能把0当未设置；与材质反馈判断分开 |
| `advanced_ui_component/segmentbuttonv2/source/segmentbuttonv2.ets:305`、`advanced_ui_component/segmentbuttonv2/source/segmentbuttonv2.ets:424` | 两个V2单选入口有可选模式并向内部组件透传 | Tab和Capsule共同覆盖；不扩展多选 |
| `advanced_ui_component/segmentbuttonv2/source/segmentbuttonv2.ets:1034` / isFollowingDragEnabled | 显式模式优先，非法值采用原材质相关缺省 | 动态、静态保持同语义 |
| `advanced_ui_component/segmentbuttonv2/source/segmentbuttonv2.ets:1269` / getIndexByHorizontalPosition | 非材质跟手释放使用实际横向按钮几何，左右外侧归端项 | 忽略Y不等于修改普通或系统材质旧命中；保留内部间隙、禁用和同值保护 |
| `advanced_ui_component_static/assembled_advanced_ui_component/@ohos.arkui.advanced.SegmentButtonV2.ets:1167` / getIndexByHorizontalPosition | 静态V2具有同一释放规则 | 不以动态桩执行代替静态原生运行证据 |
| [V2发布JS的复用重置](https://gitcode.com/openharmony/arkui_ace_engine/blob/5f7584ef3a2e733560b37675371ca3ec226af24d/advanced_ui_component/segmentbuttonv2/interfaces/segmentbuttonv2.js#L1983) / resetStateVarsOnReuse | !90350已补齐followingDragActive=false | 复用实例不得继承上一轮非材质跟手标记；ETS和发布JS保持一致 |
| `interface/sdk-js/api/@ohos.arkui.advanced.SegmentButton.d.ets:864`、`interface/sdk-js/api/@ohos.arkui.advanced.SegmentButton.static.d.ets:578` | V1枚举/可选属性已声明26.1.0 | 使用现有名称、可选性和版本 |
| `interface/sdk-js/api/@ohos.arkui.advanced.SegmentButtonV2.d.ets:1239`、`interface/sdk-js/api/@ohos.arkui.advanced.SegmentButtonV2.static.d.ets:787` | V2公开参数为@Param readonly可选属性 | 动静态按各自声明接入，不混用枚举类型 |

复用同组件已有的Pan、按压/释放动画和选中绑定路径；不引入新服务、IPC或额外材质实例。相邻Popup等高级组件的长期规格采用功能域design加Feat规格的注册方式，本目录沿用该结构。

## 不涉及项承接

无新增安全权限、跨进程协议、部件依赖、存储格式或数据迁移。国际化/无障碍、兼容性和交互反馈涉及，按Feat-01的相应AC验证。未建立额外帧率、时延或内存预算合同。

## 关键设计决策

| 决策 ID | 问题 | 选定方案 | 替代方案与取舍 | 理由 |
|---------|------|----------|----------------|------|
| ADR-1 | 如何选择模式并保留缺省 | 两个数值枚举和可选属性，省略按原材质配置回退 | 单一禁用boolean不能完整表达非材质跟手；强制统一缺省会改变原应用 | 对应AC-1、AC-3、AC-6、AC-7、AC-8 |
| ADR-2 | 模式与材质是否共用开关 | 拖拽定位/提交和原材质反馈分别判断 | 按普通模式关闭材质会同时丢失原光源、形变和回弹 | 对应AC-9、AC-10 |
| ADR-3 | 拖动是否发点击 | 使用原选中绑定请求更新，点击仍只走真实点击事件 | 跨项或释放补发onItemClicked会造成额外业务操作 | 对应AC-12、AC-13、AC-15 |
| ADR-4 | V2非材质越界释放如何恢复 | 按实际按钮横向几何命中并完成拖拽收尾 | 释放依赖Y或累计宽度可能在越界后保留异常拖动状态；统一改材质命中会扩大兼容范围 | 对应AC-18；不扩展历史材质规则 |

## 设计骨架

| 模块 | 职责 | 规格边界 |
|------|------|----------|
| SDK与Kit | 两代枚举、可选属性及原导出 | AC-16、AC-17；没有新权限或错误码 |
| V1 Options / SegmentButton | 保存模式，按模式更新拖拽定位和选中 | 单选适用，多选忽略 |
| V2 Tab/Capsule / SimpleSegmentButtonV2 | 两个单选入口透传，共用交互处理 | 普通与跟手提交时机不同，材质反馈保留 |
| 动态发布JS / 静态ETS | 承载各自运行时实现 | 源/发布物与静态语义一致；证据分开 |

应用通过公开参数进入高级组件；组件继续使用既有动画和材质能力，没有新增跨层调用。

## 后续 Task 拆分

| Task | 范围 | 验证关系 |
|------|------|----------|
| TASK-1 | 本次补齐Feat-01、功能域design、两份注册表及生成索引 | 所有AC的文档追溯，注册路径与站点检查 |
| TASK-2 | 业务实现与SDK接入已由原需求归档及!89916/!36357承接；本PR不重做 | AC-1、AC-2、AC-3、AC-4、AC-5、AC-6、AC-7、AC-8、AC-9、AC-10、AC-11、AC-12、AC-13、AC-14、AC-15、AC-16、AC-17 |
| TASK-3 | 已合入!90287/!90350的越界释放与复用规则回归入口 | AC-18及原交互兼容；不将文档通过当设备验证 |

## API 签名、Kit 与权限

API签名、枚举值和可选性以Feat-01的逐API规格为准：两代各有FOLLOWING_DRAG=0/NORMAL_DRAG=1；V1的CommonSegmentButtonOptions/SegmentButtonOptions及V2的Tab/Capsule单选可配置interactionMode。使用现有ArkUI Kit入口，不新增包或导出协议。版本26.1.0、SysCap Full、仅Stage；动态声明带跨平台/原子化服务标记，静态以自己的声明为准。无新增权限和错误码。

## 构建系统影响

本PR不修改BUILD.gn、bundle.json、生成工具和运行时文件。注册表变更后运行generate_index.py和generate_site.py；站点输入由工具生成。生产实现沿用segmentbutton、segmentbuttonv2及advanced_ui_component_static原目标。

## 可选设计扩展

### 状态归属与不变量

| 状态 | Owner | 初始化与结束 | 不变量/验证 |
|------|-------|--------------|-------------|
| 公开选中值 | 应用父状态 | 按原@Link或V2选中回调传递 | 普通跨项提交，跟手正常释放提交；AC-1、AC-2、AC-3、AC-4 |
| 非材质跟手会话和临时背板位置 | 当前组件实例 | 合法选中项起手建立，正常释放、取消或复用时收尾 | 取消不误选；越界释放后仍能再次拖动；AC-5、AC-18；TASK-3 |
| 系统材质反馈 | 当前组件的既有按压/材质路径 | 沿用原按压、释放及动画回调生命周期 | 模式不关闭材质反馈；AC-9、AC-10；TASK-2 |

非材质跟手的结束缺失触点、间隙/禁用目标及同值释放沿用已合入保护；不补改材质历史异常收尾或同值通知。UI事件处理与既有动画回调维持原线程模型，不新增后台状态或并发资源。

## 详细设计

### 模式解析与四组合

显式0选择跟手，显式1选择普通；其他值采用原材质相关缺省。非材质普通和材质跟手是原缺省组合，非材质跟手和材质普通是新增显式组合。原多选不因参数改变集合行为。

### 定位、提交与释放

普通拖拽使用原目标命中并跨项更新选中；跟手期间背板连续移动，选中值在正常释放时确认。V2非材质跟手按getIndexByHorizontalPosition使用实际按钮位置，纵向移出不否定已开始的横向拖拽；外侧归视觉端项，内部间隙、禁用目标及同值不额外提交。RTL按视觉位置映射逻辑索引。

### 回调与生命周期

拖动不调用onItemClicked。真实点击继续使用原回调和选中更新顺序。V2新增followingDragActive与其他实例状态一起在复用初始化时重置；不从前一次会话继承临时跟手状态。动态JS中的修复已由!90350承接，静态ETS保留原@Local默认初始化。

## 风险和开放问题

- 材质跟手的同值通知、禁用目标和累计宽度命中是历史差异，本规格不将其改成四组合统一规则。
- 清空items崩溃已被需求方暂缓，不恢复此前回退的修复。
- 文字与背板同轮同步由独立!90265推进；本设计不依赖尚未合入的布局方案。
- 真实系统材质、静态原生运行及多设备验收仍按原需求验证，不以本次文档检查推断通过。

## 设计审批

本文件状态为Draft，供本规格仓评审。既有需求归档提供来源，不能代替本PR的人工审批；不填写未发生的审批结论。
