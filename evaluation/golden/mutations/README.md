# Golden Mutation说明

Mutation用于验证Evaluator是否能检出已知语义缺陷，不直接修改正式Function文档。

首批Mutation应从已确认参考评价中的真实Critical/Major模式中选择，例如：

- 将被源码支持的默认值改成相反值，预期`CONTRADICTED`。
- 删除异常或恢复分支，预期`MISSING`或`PARTIALLY_SUPPORTED`。
- 将Public API版本或参数改错，预期SDK契约问题。
- 删除Design关键调用层级，预期实现路径不完整。
- 将有真实设备差异的场景改成N/A，预期`SEM-INVALID-NA-001`。

每个Mutation必须记录源Function、源输入指纹、变更补丁、预期Criterion、严重度和证据。Mutation只作用于临时副本或测试Fixture。
