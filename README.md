# 临床试验纳排标准布尔逻辑表示方法研究

本项目为论文《面向机器判读的临床试验纳排标准布尔逻辑表示方法研究》的代码、数据、评估材料和实验结果整理版。研究目标是将 CHIA 语料库中的临床试验纳排标准图结构化标注编译为规范化布尔抽象语法树（Boolean AST）和布尔表达式，并评价约束引导的图到逻辑编译方法（Constraint-Guided Graph-to-Logic Compilation，CG-GLC）相对于 Flat、OR-direct 和 Constraint 三种对照方法的表现。

当前项目不包含训练集、验证集和测试集划分，也不包含消融实验。全部实验围绕 2000 个纳排标准编译单元进行整体方法评估。

## 目录结构

```text
.
├── README.md
├── requirements.txt
├── data/
│   ├── raw/
│   │   └── chia_with_scope.zip
│   ├── processed/
│   │   ├── source_criteria.jsonl
│   │   ├── source_stats.json
│   │   └── boolean_outputs/
│   └── evaluation/
│       ├── llm_judge/
│       └── gpt_manual_batches/
├── docs/
│   ├── gpt_manual_evaluation_guide.md
│   └── human_eval_scoring_guide.md
├── results/
│   ├── llm_eval/
│   └── human_eval/
├── scripts/
├── src/
│   └── criteria_boolean/
└── paper/
```

正式提交补充材料时，建议排除 `.git/`、`.agents/`、缓存目录和临时文件。`data/raw/chia_with_scope.zip` 为保留的原始数据压缩包，解压目录不作为最终项目文件保留。

## 数据说明

原始数据为 CHIA brat 格式标注，位于：

```text
data/raw/chia_with_scope.zip
```

CHIA 标注文件由同名 `.txt` 和 `.ann` 文件组成。`.txt` 保存原始入组或排除标准文本，`.ann` 保存实体、关系、事件型线索和属性标注。预处理脚本将其转换为：

```text
data/processed/source_criteria.jsonl
data/processed/source_stats.json
```

当前数据规模为 1000 项 IV 期临床试验，每项包含入组标准和排除标准两个编译单元，共 2000 个纳排标准编译单元。`source_criteria.jsonl` 每条记录主要包括：

- `doc_id`：编译单元编号，如 `NCT00050349_inc` 或 `NCT00050349_exc`。
- `trial_id`：临床试验编号。
- `section`：`inc` 表示入组标准，`exc` 表示排除标准。
- `text`：原始纳排标准文本。
- `entities`：实体标注。
- `relations`：关系标注。
- `events`：事件型线索。
- `attributes`：属性标注。

需要特别区分三类 OR 概念：CHIA 原始标注中的 OR 主要以 `* OR T1 T2 ...` 形式记录多个实体之间的析取线索，本项目在预处理后称为“CHIA OR事件线索”；代码中的 `OR组` 指由这些线索映射得到的候选谓词组合；最终 `boolean_ast` 中的 `OR` 是编译后形成的布尔操作符。

## 方法输出

四种图到逻辑编译方法的输出位于：

```text
data/processed/boolean_outputs/
```

| 文件 | 方法 | 说明 |
|---|---|---|
| `flat.jsonl` | Flat | 最低基线，将候选谓词按默认 AND 关系平铺组装并规范化为 AST。 |
| `or_direct.jsonl` | OR-direct | 直接使用 CHIA OR事件线索生成 OR 组，再与其余谓词按 AND 关系组装。 |
| `constraint.jsonl` | Constraint | 合并数值、时间、限定、否定等修饰成分，但不使用 CHIA OR事件线索恢复析取结构。 |
| `cgglc.jsonl` | CG-GLC | 综合谓词级约束细化、OR 结构恢复、scope 辅助局部分组和 AST 规范化。 |

每个方法均输出 2000 条记录，主要字段包括：

- `doc_id`
- `trial_id`
- `section`
- `text`
- `mode`
- `boolean_expression`
- `boolean_ast`
- 结构统计字段，如 `num_entities`、`num_relations`、`num_scope_groups`、`num_or_events`

`generation_summary.json` 记录四种方法的输出数量和结构统计。

## 评估设计

本项目采用 GPT-5.5 辅助盲评与人工配对抽样评估相结合的评价方案。两类评估均使用同一套五维评分标准：谓词完整性、逻辑正确性、分组正确性、忠实性和下游可用性。每个维度 0-2 分，总分 0-10 分。详细评分规则见：

```text
docs/gpt_manual_evaluation_guide.md
docs/human_eval_scoring_guide.md
```

### GPT-5.5 全量盲评

GPT-5.5 盲评覆盖全部 2000 个纳排标准编译单元及四种方法输出，共 8000 条候选布尔表达式。评估输入包括原始纳排标准文本、入组或排除类别、候选布尔表达式及评分指南，不包含方法名称和方法说明。

盲评输入和解盲映射位于：

```text
data/evaluation/llm_judge/
```

主要文件包括：

- `llm_eval_items.jsonl`：盲化后的 GPT-5.5 评估项。
- `llm_eval_key.csv`：`candidate_id` 与真实方法名的映射表，仅用于评分结束后的解盲汇总。
- `llm_eval_manifest.json`：记录方法列表、样本规模、随机种子和生成方式。

手动分批评估 prompt 位于：

```text
data/evaluation/gpt_manual_batches/
```

当前共 320 个批次文件，每批 25 条候选。

GPT-5.5 评分结果位于：

```text
results/llm_eval/
```

主要文件包括：

- `llm_judge_results.jsonl`：GPT-5.5 原始评分记录。
- `llm_judge_per_item.csv`：解盲后的逐条评分明细。
- `llm_judge_summary_by_method.csv`：四种方法的全量评分均值。
- `llm_judge_paired_vs_cgglc.csv`：CG-GLC 与各对照方法的全量配对比较。

### 人工配对抽样评估

人工评估从 2000 个纳排标准编译单元中随机分层抽取 50 个单元，其中 OR 结构样本 25 条、scope 相关样本 15 条、其他样本 10 条。针对同一批 50 个单元，分别收集 Flat、OR-direct、Constraint 和 CG-GLC 四种方法生成的候选表达式，共 200 份待评估结果。两名评审者独立评分。

原始人工评分表位于：

```text
results/human_eval/
```

```text
flat_human_eval_1.csv
flat_human_eval_2.csv
or_direct_human_eval_1.csv
or_direct_human_eval_2.csv
constraint_human_eval_1.csv
constraint_human_eval_2.csv
cgglc_human_eval_1.csv
cgglc_human_eval_2.csv
```

人工评估汇总结果包括：

- `human_eval_per_item_200.csv`：200 条人工评分明细。
- `human_eval_summary_by_method.csv`：四种方法人工评分均值。
- `human_eval_paired_vs_cgglc.csv`：CG-GLC 相对三种对照方法的配对总分差、胜/平/负数量和单侧精确符号检验 P 值。
- `human_eval_reviewer_agreement.csv`：两名评审者之间的一致性。
- `gpt_human_eval_200.csv`：从全量 GPT-5.5 盲评结果中抽取的同一批 200 条评分。
- `gpt_human_agreement_200.csv`：GPT-5.5 评分与两名人工评审均分的一致性。

## 核心结果

GPT-5.5 全量盲评结果显示，CG-GLC 在四种方法中总分最高：

| 方法 | n | 谓词完整性 | 逻辑正确性 | 分组正确性 | 忠实性 | 下游可用性 | 总分 |
|---|---:|---:|---:|---:|---:|---:|---:|
| Flat | 2000 | 1.112 | 0.846 | 0.652 | 0.958 | 0.649 | 4.216 |
| OR-direct | 2000 | 1.112 | 1.495 | 1.132 | 1.050 | 1.022 | 5.809 |
| Constraint | 2000 | 1.299 | 0.838 | 0.751 | 0.997 | 0.817 | 4.700 |
| CG-GLC | 2000 | 1.266 | 1.585 | 1.352 | 1.144 | 1.156 | 6.502 |

人工配对抽样评估同样显示 CG-GLC 得分最高：

| 方法 | n | 谓词完整性 | 逻辑正确性 | 分组正确性 | 忠实性 | 下游可用性 | 总分 |
|---|---:|---:|---:|---:|---:|---:|---:|
| Flat | 50 | 0.970 | 0.820 | 0.420 | 0.790 | 0.560 | 3.560 |
| OR-direct | 50 | 1.070 | 1.290 | 0.860 | 0.940 | 0.750 | 4.910 |
| Constraint | 50 | 1.470 | 0.990 | 0.780 | 0.930 | 1.000 | 5.170 |
| CG-GLC | 50 | 1.510 | 1.440 | 1.310 | 1.290 | 1.240 | 6.790 |

人工配对比较中，CG-GLC 相对 Flat、OR-direct 和 Constraint 的胜/平/负数量分别为 45/3/2、39/5/6 和 29/19/2；剔除平分样本后的单侧精确符号检验 P 值分别为 `8.02e-12`、`2.71e-7` 和 `2.31e-7`。

一致性分析显示，两名人工评审者在 200 条候选表达式总分上的 Pearson 相关系数为 0.891，Spearman 相关系数为 0.886；GPT-5.5 评分与人工均分在 200 条候选表达式总分上的 Pearson 相关系数为 0.578，Spearman 相关系数为 0.602。

## 复现流程

安装依赖：

```powershell
pip install -r requirements.txt
```

从原始 CHIA brat 标注生成结构化输入：

```powershell
python src/criteria_boolean/prepare_chia_jsonl.py
```

生成四种方法的布尔表达式：

```powershell
python src/criteria_boolean/compile_boolean.py
```

准备 GPT-5.5 盲评输入和分批 prompt：

```powershell
python src/criteria_boolean/prepare_llm_eval_dataset.py --full-dataset
python src/criteria_boolean/export_gpt_eval_batches.py --batch-size 25
```

生成人工评估模板：

```powershell
python src/criteria_boolean/generate_human_eval_sample.py --methods cgglc --sample-size 50 --skip-existing
python src/criteria_boolean/generate_human_eval_sample.py --methods flat or_direct constraint --reference-csv results/human_eval/cgglc_human_eval_1.csv --skip-existing
```

也可以一次性准备评估材料：

```powershell
powershell -ExecutionPolicy Bypass -File scripts/prepare_evaluation_materials.ps1
```

注意：人工评分表已有填写结果时，不建议重新生成模板；如需重新生成，应先备份现有评分表。

GPT-5.5 全部批次评分完成并保存到 `results/llm_eval/llm_judge_results.jsonl` 后，运行：

```powershell
python src/criteria_boolean/summarize_llm_judge.py
```

两名人工评审者完成四种方法评分后，运行：

```powershell
python src/criteria_boolean/compare_human_methods.py
```

该脚本会同时生成四种方法人工评价结果、配对显著性检验结果、评审者间一致性结果，以及同一批 200 条样本上的 GPT-5.5 与人工一致性结果。

## 代码入口

| 文件 | 作用 |
|---|---|
| `src/criteria_boolean/prepare_chia_jsonl.py` | 将 CHIA brat 标注转换为 `source_criteria.jsonl`。 |
| `src/criteria_boolean/compile_boolean.py` | 生成 Flat、OR-direct、Constraint 和 CG-GLC 四种方法的 Boolean AST 与表达式。 |
| `src/criteria_boolean/prepare_llm_eval_dataset.py` | 构建盲化的 GPT-5.5 评估数据集和解盲映射表。 |
| `src/criteria_boolean/export_gpt_eval_batches.py` | 将 GPT-5.5 评估数据导出为分批 Markdown prompt。 |
| `src/criteria_boolean/generate_human_eval_sample.py` | 生成四种方法配对人工评估模板。 |
| `src/criteria_boolean/summarize_llm_judge.py` | 汇总 GPT-5.5 全量盲评结果。 |
| `src/criteria_boolean/compare_human_methods.py` | 汇总四方法人工评估、配对显著性检验、评审者一致性和 GPT-5.5-人工一致性。 |

常用流程脚本：

```text
scripts/run_generation.ps1
scripts/prepare_evaluation_materials.ps1
```

