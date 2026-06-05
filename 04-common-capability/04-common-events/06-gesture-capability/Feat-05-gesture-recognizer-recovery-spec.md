# 特性规格

> Draft。当前文档是 Func-04-04-06 / Feat-05 的长期规格草案，占位并承接 Stage 2。

## AC 摘要

- AC-1.1 新一轮首个 down 前恢复非 READY 非豁免残留状态。
- AC-1.2 READY/闭环场景不触发额外恢复和业务回调。
- AC-2.1 双击 pending 豁免。
- AC-2.2 Swipe pending 豁免。
- AC-3.1 恢复行为可测可观测。

## 规则摘要

- 首 down 判定：上一轮无活动手指后的首个 `TouchType::DOWN`。
- 重复同 id down 走既有强清逻辑。
- 多指第二根及后续 down 不触发全局恢复。
- 非豁免 pending 视为未闭环并恢复。

## 验证摘要

- UT：`test/unittest/core/event`、`test/unittest/core/gestures`
- HostPreview：`examples/SpecTest/.../Feat-05-gesture-recognizer-recovery`

