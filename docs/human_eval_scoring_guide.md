# 人工评估指南

本指南用于人工评估 CG-GLC 生成的布尔逻辑表达式质量。人工评估不是重新建立完整金标准，而是在固定评分细则下，对本文方法输出进行抽样质量核查，并与 GPT 盲评结果形成互补证据。

## 评估文件

默认生成两份完全相同的人工评估表：

```text
results/human_eval/cgglc_human_eval_1.csv
results/human_eval/cgglc_human_eval_2.csv
```

生成命令为：

```powershell
python src/criteria_boolean/generate_human_eval_sample.py --sample-size 50
```

两份 CSV 的样本、顺序和候选表达式完全一致。评审 1 填写 `cgglc_human_eval_1.csv`，评审 2 填写 `cgglc_human_eval_2.csv`，两人独立评分，不需要互相讨论。

每条样本包含：

- `sample_id`：人工评估样本编号。
- `doc_id`：原始纳排标准编译单元编号。
- `case_bucket`：样本类型，可能为 `or`、`scope` 或 `other`。
- `source_criterion`：原始纳排标准文本。
- `candidate_expression`：CG-GLC 生成的布尔表达式。
- 五个评分字段：见下方评分维度。
- `reviewer_notes`：评审备注，可记录主要错误或不确定点。

评分时只根据 `source_criterion` 和 `candidate_expression` 判断，不需要查看方法内部过程，也不需要查看 GPT 评分结果。

## 抽样设置

当前项目默认随机分层抽取 50 条 CG-GLC 输出，覆盖 OR、scope 和普通标准。抽样脚本会过滤不可评估样本，例如原始文本为 `NA`、`N/A`、空文本，或 CG-GLC 输出为 `(EMPTY)` 的记录。

`case_bucket` 的含义：

- `or`：原始 CHIA 标注中包含 OR 事件，重点考察候选表达式是否保留析取逻辑。
- `scope`：原始 CHIA 标注中包含 `Has_scope` 关系，重点考察修饰成分、数值、时间窗或条件范围是否归属正确。
- `other`：未归入上述两类的普通样本，用于检查整体基础质量。

## 评分维度

每个维度均为 0、1、2 分。

### 1. predicate_completeness

评价关键临床谓词是否完整。

- 2：疾病、药物、检查、数值、时间、限定词、否定等关键信息基本完整，并整合为清晰谓词。
- 1：主要谓词存在，但部分数值、时间、限定词、修饰语或谓词归属缺失或碎片化。
- 0：关键谓词大量缺失、严重碎片化、空输出或不可理解。

### 2. logical_correctness

评价 AND、OR、NOT 是否保留原文逻辑。

- 2：合取、析取和否定关系基本正确。
- 1：主体逻辑部分正确，但至少一个重要 AND、OR 或 NOT 关系错误或模糊。
- 0：布尔逻辑显著改变原文含义。

### 3. grouping_correctness

评价并列项、共享修饰语、局部分组和层级结构。

- 2：替代项、共享修饰语、局部条件组和嵌套结构清晰。
- 1：部分分组正确，但替代项归属或共享修饰语作用范围有错误。
- 0：分组缺失或严重误导。

### 4. faithfulness

评价候选表达式是否忠实于原文。

- 2：没有临床重要的新增条件或遗漏。
- 1：总体忠实，但存在需要人工修正的重要细节。
- 0：新增原文不支持的条件、遗漏核心条件或与原文矛盾。

### 5. downstream_usability

评价是否可作为队列查询或患者筛选的中间表示。

- 2：基本可用于后续查询生成或患者筛选，只需少量人工修正。
- 1：部分可用，但需要明显人工修复。
- 0：难以下游使用。

## 填写规则

所有评分字段只填写整数 `0`、`1` 或 `2`。如果难以判断，优先根据临床含义受影响程度评分：

- 不影响核心临床含义的轻微措辞问题，一般不降到 0 分。
- 遗漏关键疾病、药物、检查、数值、时间窗或否定信息时，应明显扣分。
- OR 被错误改成 AND，或 NOT 作用范围错误时，应在 `logical_correctness` 和 `grouping_correctness` 中扣分。
- 候选表达式新增原文没有支持的临床条件时，应在 `faithfulness` 中扣分。

备注字段建议简短记录关键问题，例如：

```text
misses time window
OR alternatives represented as AND
negation scope unclear
unsupported medication condition
```

## 汇总

两名评审都完成后，直接运行：

```powershell
python src/criteria_boolean/summarize_human_eval.py
```

脚本默认读取：

```text
results/human_eval/cgglc_human_eval_1.csv
results/human_eval/cgglc_human_eval_2.csv
```

并生成：

```text
results/human_eval/cgglc_human_eval_summary.csv
```

`cgglc_human_eval_summary.csv` 用于报告人工评估总体结果，包括五个维度均分、总分均分、两名评审完全一致率和平均绝对差异。`results/human_eval/` 目录只保留两份人工原表和这个人工汇总表。

如果需要生成 GPT 与人工评分的一致性分析，运行：

```powershell
python src/criteria_boolean/compare_gpt_human_eval.py
```

该脚本默认读取两份人工评估表和 `results/llm_eval/llm_judge_per_item.csv`，并生成：

```text
results/llm_eval/gpt_human_agreement_summary.csv
```
