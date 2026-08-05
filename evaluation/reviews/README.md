# Function参考评价

本目录保存全部已注册Pilot Function的单份参考评价。每个Pilot Function必须且只能保留一个当前评价文件，文件名固定为`<func_id>.yaml`。

当前评价协议为Rubric v0.2，共20个Criterion。v0.1 Review属于待迁移记录；升级时必须重新核验Design完整性并重新确认，不能只机械换版本号或折算旧Design分数。

## 工作流

生成待评价草稿：

```bash
PYTHONPATH=specs/tools python3 -m spec_eval.evaluation_validator \
  --template 03-07-01 \
  --evaluator-id sunfei2021 \
  > specs/evaluation/reviews/03-07-01.yaml
```

评价人完成20个Criterion、Evidence、Finding和精确分数后，填写：

```yaml
status: confirmed
evaluator:
  evaluator_id: sunfei2021
  evaluated_at: '2026-08-04T15:30:00+08:00'
confirmation:
  confirmed_by: sunfei2021
  confirmed_at: '2026-08-04T16:00:00+08:00'
  conclusion: accepted
  notes: []
```

评价人与确认人允许为同一人。`evaluator_id`只用于追溯本次评价，不表示专家、仲裁或团队角色。

Rubric升级后，可以只刷新尚未评价的草稿：

```bash
PYTHONPATH=specs/tools python3 -m spec_eval.evaluation_validator --refresh-drafts
```

该命令不会修改`confirmed`或`superseded`记录；已确认旧版本必须重新评价后再替换。

提交前校验单份文件：

```bash
PYTHONPATH=specs/tools python3 -m spec_eval.evaluation_validator \
  --evaluation specs/evaluation/reviews/03-07-01.yaml
```

校验Pilot清单和本目录全部已注册评价：

```bash
PYTHONPATH=specs/tools python3 -m spec_eval.evaluation_validator
```

## 状态约束

- `draft`：允许Criterion保持`NOT_VERIFIABLE`，分数保持`null`，不得视为质量结论。
- `confirmed`：20个Criterion必须完成，不能全部为`NOT_VERIFIABLE`；五维分和原始分必须与Rubric扣分规则一致；必须有一次`accepted`确认。
- `superseded`：输入指纹或版本变化后保留的历史记录，不再作为当前参考评价。

Critical/Major Finding必须提供冻结revision下可复现的路径和`content_hash`。静态Finding仍然权威；如静态Gate或其他约束要求更严格结论，可以降低`published_score`或`admission`，但不能放宽Rubric封顶。
