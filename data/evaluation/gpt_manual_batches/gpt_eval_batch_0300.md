# GPT-5.5 Evaluation Batch

请先阅读并遵循以下评估指南，然后评价本批候选。只输出 JSONL 评分结果。

## Evaluation Guide

# GPT-5.5 评估指南

本指南用于让 GPT-5.5 对临床试验纳排标准的候选布尔表达式进行盲化语义评估。GPT-5.5 评分不是金标准，也不是对隐藏答案的匹配；它只是在固定 rubric 下，根据原始纳排标准文本判断候选表达式的忠实性、完整性和可用性。

## 评估角色

请作为独立评估者，逐条评价候选布尔表达式。每条样本只允许使用以下信息：

- 原始纳排标准文本。
- 一个候选布尔表达式。
- 本指南中的评分细则。

请不要推测候选表达式由哪种方法生成，不要使用任何隐藏参考答案，不要根据表达式长短直接加分或扣分。评价重点是候选表达式是否保留原文临床含义。

## 输入字段

每条候选通常包含：

- `candidate_id`：盲化候选编号。
- `doc_id`：原始纳排标准编译单元编号。
- `case_bucket`：样本类型，可能为 `or`、`scope` 或 `other`。
- `source_criterion`：原始纳排标准文本。
- `candidate_expression`：候选布尔表达式。

`candidate_id` 是唯一需要在输出中保留的样本键。不要输出方法名。

## 评分流程

对每条候选按以下顺序评估：

1. 阅读 `source_criterion`，识别关键临床条件、数值、时间、限定词、否定、并列关系和局部分组。
2. 阅读 `candidate_expression`，判断它是否表达了相同临床含义。
3. 分别给五个维度打 0、1、2 分。
4. 选择适用的 `error_flags`。
5. 写一句非常简短的 `brief_rationale`，说明主要扣分原因或为什么基本正确。

不同候选之间不要相互比较；每条候选都只与自己的原始文本比较。

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

## 错误标签

从以下标签中选择 1 个或多个：

- `missing_key_condition`：遗漏关键条件。
- `extra_condition`：新增原文不支持的条件。
- `wrong_or_logic`：析取条件遗漏或被错误表示为 AND。
- `wrong_and_logic`：必须同时满足的条件遗漏或被错误表示为 OR。
- `wrong_negation`：否定缺失、误加或作用范围错误。
- `wrong_scope_or_grouping`：分组、嵌套或共享修饰语作用范围错误。
- `predicate_fragmentation`：同一临床谓词被拆成混乱片段。
- `overly_verbose`：表达过度冗长并影响可用性。
- `empty_or_unusable`：空输出或不可用。
- `none`：无明显错误标签。

如果没有明显错误，`error_flags` 只能填写 `["none"]`。如果存在其他错误标签，不要同时填写 `none`。

## 输出格式

请严格输出 JSONL。每个候选只输出一行 JSON，不要输出 Markdown 表格，不要输出额外解释文字。

输出字段必须为：

- `candidate_id`
- `predicate_completeness`
- `logical_correctness`
- `grouping_correctness`
- `faithfulness`
- `downstream_usability`
- `total_score`
- `error_flags`
- `brief_rationale`

示例：

```json
{"candidate_id":"EXAMPLE_ID","predicate_completeness":2,"logical_correctness":2,"grouping_correctness":1,"faithfulness":2,"downstream_usability":1,"total_score":8,"error_flags":["wrong_scope_or_grouping"],"brief_rationale":"Main predicates and logic are preserved, but one local grouping is ambiguous."}
```

`total_score` 必须等于五个维度分数之和，范围为 0-10。

## 推荐投喂方式

全量评估约有 8000 个候选，不建议一次性输入。建议每批 20-50 个候选。

可用以下命令导出批次文件：

```powershell
python src/criteria_boolean/export_gpt_eval_batches.py --batch-size 25
```

批次文件位于：

```text
data/evaluation/gpt_manual_batches/
```

每批评估步骤：

1. 粘贴本评估指南。
2. 粘贴一批候选 JSONL。
3. 要求模型只输出同样数量的 JSONL 评分结果。
4. 检查输出行数是否与输入候选数一致。
5. 将输出追加保存到 `results/llm_eval/llm_judge_results.jsonl`。

全部批次保存后运行：

```powershell
python src/criteria_boolean/summarize_llm_judge.py
```

## 给 Codex 或 GPT-5.5 的输入模板

如果使用 Codex 直接读取本项目文件，可以输入：

```text
请按照 docs/gpt_manual_evaluation_guide.md 的评分标准，
评估 data/evaluation/gpt_manual_batches/gpt_eval_batch_0001.md 中的所有候选。

要求：
1. 只根据每条样本的 source_criterion 和 candidate_expression 评分。
2. 不要读取或使用 data/evaluation/llm_judge/llm_eval_key.csv。
3. 不要推测方法名。
4. 每个 candidate_id 输出一行 JSONL。
5. 输出字段必须包含 candidate_id、五个维度分数、total_score、error_flags、brief_rationale。
6. 不输出 Markdown 表格，不输出额外解释文字。
```

如果需要 Codex 直接写入结果文件，可以输入：

```text
请按照 docs/gpt_manual_evaluation_guide.md 的评分标准，
评估 data/evaluation/gpt_manual_batches/gpt_eval_batch_0001.md，
并把 JSONL 结果追加保存到 results/llm_eval/llm_judge_results.jsonl。

注意：
- 不要读取 data/evaluation/llm_judge/llm_eval_key.csv。
- 如果结果文件不存在，请创建它。
- 如果输出行数不是25行，请停止并说明原因。
```

评估下一批时，只需要把文件名改成 `gpt_eval_batch_0002.md`、`gpt_eval_batch_0003.md`，依次类推。所有批次完成后，再运行汇总脚本。

## Candidate Items

```jsonl
{"candidate_id": "LLM07476", "doc_id": "NCT02884115_inc", "case_bucket": "other", "source_criterion": "Early Syphilis Cases Determined to Be Serofast at 6 Months after Initial Treatment", "candidate_expression": "((Early Syphilis Serofast) AND (Treatment Initial))"}
{"candidate_id": "LLM07477", "doc_id": "NCT02457442_inc", "case_bucket": "or", "source_criterion": "ASA physical status 1 or 2 Written informed consent Cardiovascular disease Pulmonary disease Liver disease CNS disease Alcohol or drug abuse Chronic intake of CNS active drugs Body mass index > 35 Diabetes mellitus Hypersensitivity or allergy to one of the study drugs", "candidate_expression": "((1) AND (2) AND (> 35) AND (ASA physical status) AND (Alcohol abuse) AND (Body mass index) AND (CNS active drugs) AND (CNS disease) AND (Cardiovascular disease) AND (Chronic intake) AND (Diabetes mellitus) AND (Hypersensitivity) AND (Liver disease) AND (Pulmonary disease) AND (Written informed consent) AND (allergy) AND (drug abuse) AND (study drugs))"}
{"candidate_id": "LLM07478", "doc_id": "NCT02689817_inc", "case_bucket": "other", "source_criterion": "Patients undergoing an operation that is scheduled to last more than 2 hours", "candidate_expression": "(operation scheduled to last more than 2 hours last more than 2 hours)"}
{"candidate_id": "LLM07479", "doc_id": "NCT03120533_exc", "case_bucket": "or", "source_criterion": "Healthy Volunteers Treprostinil contraindications: Known hypersensitivity to treprostinil or any of the excipients, Pulmonary arterial hypertension related to veno-occlusive disease, Congestive heart failure due to severe left ventricular dysfunction, Severe hepatic insufficiency (Child-Pugh stage C), Evolving gastrointestinal ulcer, intracranial hemorrhage, recent trauma or other clinical condition that may lead to bleeding, Congenital or acquired valvular abnormalities with cardiac repercussions, Severe ischemic heart disease or unstable angina; Myocardial infarction in the last six months; Decompensated cardiac insufficiency not medically controlled; Severe arrhythmias; Cerebrovascular lesions (such as transient ischemic attack, stroke) that occurred within the last three months. Persons referred to in Articles L1121-5 to L1121-8 of the French Public health Code: pregnant woman, parturient, nursing mother, person deprived of liberty by judicial or administrative decision, person subject to a legal protection measure, can not Be included in clinical trials. Subject in an exclusion period from another study, Subject who would receive more than 4500 euros of compensation due to his participation in other biomedical research in the 12 months preceding this study Systemic sclerosis patients: Iloprost cure carried out in the previous month or planned in the following month. Initiation or change of dosage of bosentan, sildenafil or calcium channel blockers in the previous month or in the following month Digital Sympathectomy or botulinum toxin injection planned in the following month. Clinically superinfected digital ulcers Treprostinil contraindications: Known hypersensitivity to treprostinil or any of the excipients, Pulmonary arterial hypertension related to veno-occlusive disease, Congestive heart failure due to severe left ventricular dysfunction, Severe hepatic insufficiency (Child-Pugh stage C), Evolving gastrointestinal ulcer, intracranial hemorrhage, recent trauma or other clinical condition that may lead to bleeding, Congenital or acquired valvular abnormalities with cardiac repercussions, Severe ischemic heart disease or unstable angina; Myocardial infarction in the last six months; Decompensated cardiac insufficiency not medically controlled; Severe arrhythmias; Cerebrovascular lesions (such as transient ischemic attack, stroke) that occurred within the last three months. Persons referred to in Articles L1121-5 to L1121-8 of the French Public health Code: pregnant woman, parturient, nursing mother, person deprived of liberty by judicial or administrative decision, person subject to a legal protection measure, can not Be included in clinical trials. Subject in an exclusion period from another study, Subject who would receive more than 4500 euros of compensation due to his participation in other biomedical research in the 12 months preceding this study", "candidate_expression": "((Child-Pugh stage C) AND (Congestive heart failure) AND (Pulmonary arterial hypertension) AND (Systemic sclerosis) AND (Treprostinil) AND (any of the excipients) AND (arrhythmias Severe) AND (bosentan) AND (calcium channel blockers) AND (contraindications) AND (digital ulcers superinfected) AND (gastrointestinal ulcer Evolving) AND (hypersensitivity) AND (intracranial hemorrhage) AND (pregnant) AND (sildenafil) AND (trauma recent) AND (treprostinil) AND (veno-occlusive disease) AND (woman) AND ((Cerebrovascular lesions within the last three months) OR (Congenital valvular abnormalities with cardiac repercussions) OR (Decompensated cardiac insufficiency) OR (Myocardial infarction in the last six months) OR (acquired valvular abnormalities with cardiac repercussions) OR (arrhythmias Severe) OR (clinical condition that may lead to bleeding) OR (ischemic heart disease Severe) OR (unstable angina)) AND ((hepatic insufficiency Severe) OR (left ventricular dysfunction severe)) AND ((deprived of liberty) OR (nursing) OR (parturient) OR (subject to a legal protection) OR (woman)) AND ((Cerebrovascular lesions within the last three months) OR (Congenital valvular abnormalities with cardiac repercussions) OR (Decompensated cardiac insufficiency not medically controlled) OR (Myocardial infarction in the last six months) OR (acquired valvular abnormalities with cardiac repercussions) OR (clinical condition that may lead to bleeding) OR (ischemic heart disease Severe) OR (unstable angina)) AND ((stroke) OR (transient ischemic attack)) AND ((deprived of liberty) OR (nursing) OR (parturient) OR (pregnant)) AND ((Iloprost in the previous month) OR (Iloprost planned in the following month)) AND ((in the following month) OR (in the previous month)) AND ((Digital Sympathectomy) OR (botulinum toxin injection)) AND ((any of the excipients) OR (treprostinil)) AND ((Congestive heart failure) OR (Pulmonary arterial hypertension) OR (gastrointestinal ulcer) OR (hepatic insufficiency Severe) OR (intracranial hemorrhage) OR (left ventricular dysfunction severe)))"}
{"candidate_id": "LLM07480", "doc_id": "NCT02469610_exc", "case_bucket": "other", "source_criterion": "Previous thoracic operation in the same side.", "candidate_expression": "(thoracic operation Previous same side)"}
{"candidate_id": "LLM07481", "doc_id": "NCT02961582_exc", "case_bucket": "or", "source_criterion": "Obstructed outlet syndrome (objectified by defeacography) Irritable bowel syndrome (Rome-IV criteria for irritable bowel syndrome) Congenital or organic bowel pathology Rectal prolapse Anatomical limitations preventing placement of an electrode Skin and perineal disease with risk of infection Previous large bowel/rectal surgery Stoma Coexisting neurological disease Significant psychological co-morbidity as assessed subjectively by the investigator Being or attempting to become pregnant during study follow-up", "candidate_expression": "((Anatomical limitations) AND (Being or attempting to become pregnant during study follow-up) AND (Congenital bowel pathology) AND (Irritable bowel syndrome) AND (Obstructed outlet syndrome) AND (Rectal prolapse) AND (Rome-IV criteria) AND (Skin disease) AND (Stoma) AND (as assessed subjectively by the investigator) AND (defeacography) AND (irritable bowel syndrome) AND (large bowel surgery) AND (neurological disease) AND (organic bowel pathology) AND (perineal disease) AND (psychological co-morbidity Significant) AND (rectal surgery) AND (risk of infection) AND NOT (placement of an electrode))"}
{"candidate_id": "LLM07482", "doc_id": "NCT03034733_exc", "case_bucket": "or", "source_criterion": "severe coronary artery disease, heart failure, kidney failure insulin-dependent DM (diabetes mellitus), poorly controlled type II DM gastric/duodenal ulcer allergy/contra-indication for any drug used in the study corticosteroid use during last 3 months preoperative use of opioid drugs (excl. codeine, tramadol) neuropathy/sensory impairment of lower limbs lack of co-operation, e.g. inability to use a PCA (patient controlled analgesia)-device", "candidate_expression": "((PCA -device) AND (allergy) AND (codeine) AND (contra-indication) AND (coronary artery disease) AND (corticosteroid during last 3 months) AND (diabetes mellitus) AND (drug used in the study) AND (duodenal ulcer) AND (gastric ulcer) AND (heart failure) AND (inability to use) AND (insulin-dependent DM) AND (kidney failure) AND (lack of co-operation) AND (neuropathy) AND (opioid drugs preoperative) AND (sensory impairment) AND (tramadol) AND (type II DM poorly controlled))"}
{"candidate_id": "LLM07483", "doc_id": "NCT02348918_inc", "case_bucket": "or", "source_criterion": "Male or female, 18 years of age or older. Study eye with clinically significant diabetic macular edema (DME) with central subfield thickness ≥ 350µm on spectral domain OCT Best corrected visual acuity (BCVA) of 20/50 to 20/320 ETDRS equivalent (65 letters to 23 letters) in the study eye, with BCVA decrement primarily attributable to DME. Treatment naïve, i.e., no previous anti-VEGF treatment in the study eye or no anti-VEGF treatment in the 45 days prior to study enrollment. In the investigator's opinion, the subject still has significant intraretinal fluid with room for improvement in both macular edema and BCVA. Intra-Ocular Pressure (IOP) is under control (i.e., IOP ≤ 25 mm in the study eye) and study eye is not receiving any IOP lowering drops. Willing and able to return for all study visits. Able to meet the extensive post-op evaluation regimen. Understands and signs the informed consent form.", "candidate_expression": "((Able to meet the extensive post-op evaluation regimen.) AND (BCVA) AND (Best corrected visual acuity (BCVA) 20/50 to 20/320 ETDRS equivalent in the study eye 65 letters to 23 letters) AND (IOP ≤ 25 mm in the study eye) AND (Intra-Ocular Pressure (IOP) under control) AND (Treatment naïve) AND (Understands and signs the informed consent form.) AND (Willing and able to return for all study visits.) AND (age 18 years or older) AND (central subfield thickness ≥ 350µm) AND (diabetic macular edema (DME) clinically significant) AND (intraretinal fluid significant with room for improvement) AND (macular edema) AND (spectral domain OCT) AND NOT (IOP lowering drops study eye) AND (NOT (anti-VEGF treatment previous in the study eye) OR NOT (anti-VEGF treatment in the 45 days prior to study enrollment)) AND ((Male) OR (female)))"}
{"candidate_id": "LLM07484", "doc_id": "NCT03615508_inc", "case_bucket": "or", "source_criterion": "Horner's Syndrome History of taking an alpha blocker (tamsulosin/ terazosin/doxazosin/alfuzosin/silodosin) medication", "candidate_expression": "((Horner's Syndrome) AND (alpha blocker) AND ((alfuzosin) OR (doxazosin) OR (silodosin) OR (tamsulosin) OR (terazosin)))"}
{"candidate_id": "LLM07485", "doc_id": "NCT02798237_exc", "case_bucket": "or", "source_criterion": "cognitive impairment (Mini-Mental Status Examination score: illiterate 13 points; elementary and middle school 18 points; and high-school 26 points; or inability to respond to verbal command); inability to walk independently for at least 10 minutes, with or without walking devices; pain or other disorders precluding their participation.", "candidate_expression": "((13 points) AND (18 points) AND (26 points) AND (Mini-Mental Status Examination score) AND (at least 10 minutes) AND (cognitive impairment) AND (elementary) AND (high-school) AND (illiterate) AND (inability to respond to verbal command) AND (inability to walk independently) AND (middle school) AND (other disorders) AND (pain) AND (pain or other disorders precluding their participation) AND (precluding their participation) AND (walking devices))"}
{"candidate_id": "LLM07486", "doc_id": "NCT01743755_exc", "case_bucket": "or", "source_criterion": "Immunocompromised patients: Patients with a known congenital or acquired immunodeficiency. Patients who received chemotherapy less than 6 weeks ago. Patients who received corticosteroids in the last 6 weeks. Patients who received immunosuppressive medication in the last 6 weeks (e.g. cyclosporin, cyclophosphamide, azathioprine). Patients with chronic obstructive pulmonary disease who are on systemic corticosteroids. Patients who require intensive care unit treatment. Patients with tropical worm infection. Patients with dexamethasone intolerance. Pregnant and breastfeeding women.", "candidate_expression": "((Immunocompromised) AND (Pregnant and breastfeeding women) AND (acquired) AND (azathioprine) AND (chemotherapy) AND (chronic obstructive pulmonary disease) AND (congenital) AND (corticosteroids) AND (cyclophosphamide) AND (cyclosporin) AND (dexamethasone) AND (immunodeficiency) AND (immunosuppressive medication) AND (in the last 6 weeks) AND (intensive care unit) AND (intolerance) AND (less than 6 weeks ago) AND (systemic corticosteroids) AND (tropical worm infection))"}
{"candidate_id": "LLM07487", "doc_id": "NCT01700790_exc", "case_bucket": "or", "source_criterion": "Non-compliance with DOTPlus. Alternatively DOT can be done by telephoning patient on a daily basis 5 times a week and having patient annotate taking drug in a log which would be reviewed by clinic staff History of being treated for tuberculosis in the prior 2 years unless there is DST, including PCR testing, showing sensitivity to rifamycin. Known hypersensitivity to rifampin or rifabutin. Liver enzymes greater than 2 times ULN. Bilirubin greater than 2 times ULN. Serum creatinine greater than 3 times ULN. Hemoglobin less than 7.0 gms even if receiving erythropoietin. Absolute neutrophil count less than 750 cells/mm3 even if receiving G-CSF. Fasting triglycerides greater than 400 mg/dL. Fasting cholesterol > 1.6 upper limits of normal. GI intolerance of tuberculosis medications requiring discontinuation of tuberculosis medications. Fasting glucose greater 150 mg/dL. Pregnant women. Use of one of the prohibited medications Any condition that the investigators feel could compromise the use of the current medication. Have a CD4 cell count of 50 cells/mm3or less Hepatitis B or C infection Alcohol or illicit drug use, which in the investigators opinion may affect participation in study.", "candidate_expression": "((50 cells/mm3or less) AND (> 1.6 upper limits of normal) AND (Absolute neutrophil count) AND (Any condition that the investigators feel could compromise the use of the current medication.) AND (Bilirubin) AND (CD4 cell count) AND (DOTPlus) AND (Fasting cholesterol) AND (Fasting glucose) AND (Fasting triglycerides) AND (GI intolerance) AND (Hemoglobin) AND (Liver enzymes) AND (Non-compliance) AND (PCR testing) AND (Pregnant) AND (Serum creatinine) AND (Use of one of the prohibited medications) AND (discontinuation) AND (even if receiving G-CSF) AND (even if receiving erythropoietin) AND (greater 150 mg/dL) AND (greater than 2 times ULN) AND (greater than 3 times ULN) AND (greater than 400 mg/dL) AND (hypersensitivity) AND (in the prior 2 years) AND (less than 7.0 gms) AND (less than 750 cells/mm3) AND (rifamycin) AND (sensitivity) AND (tuberculosis) AND (tuberculosis medications) AND (women) AND ((DST) OR (treated)) AND ((rifabutin) OR (rifampin)) AND ((Hepatitis B) OR (Hepatitis C)) AND ((Alcohol use) OR (illicit drug use)))"}
{"candidate_id": "LLM07488", "doc_id": "NCT02634541_inc", "case_bucket": "or", "source_criterion": "Axial spondyloarthritis (ASAS criteria) and radiologic sacroiliitis as detected either by MRI or X-ray.", "candidate_expression": "((ASAS criteria) AND (Axial spondyloarthritis) AND (radiologic) AND (sacroiliitis) AND ((MRI) OR (X-ray)))"}
{"candidate_id": "LLM07489", "doc_id": "NCT01352598_exc", "case_bucket": "other", "source_criterion": "NA", "candidate_expression": "(EMPTY)"}
{"candidate_id": "LLM07490", "doc_id": "NCT02924870_inc", "case_bucket": "or", "source_criterion": "subjects older than 35 years diagnosis of moderate to very severe COPD (FEV1 <80% predicted), according to the GesEPOC criteria, established at least 3 months current or former smoker with an accumulated consumption >10 packs x year hospital admission for COPD exacerbation", "candidate_expression": "((<80% predicted) AND (>10 packs x year) AND (COPD) AND (COPD exacerbation) AND (FEV1) AND (GesEPOC criteria,) AND (admission) AND (at least 3 months) AND (consumption) AND (older than 35) AND (smoker) AND (years) AND ((moderate) OR (very severe)))"}
{"candidate_id": "LLM07491", "doc_id": "NCT03168178_inc", "case_bucket": "other", "source_criterion": "Pregnant women between 34-42 weeks gestation Singleton fetus Admitted for labor management & develops a fever of 100.4 F or greater", "candidate_expression": "((100.4 F or greater) AND (Admitted for) AND (Pregnant) AND (Singleton fetus) AND (between 34-42 weeks) AND (fever) AND (gestation) AND (labor management) AND (women))"}
{"candidate_id": "LLM07492", "doc_id": "NCT02247128_inc", "case_bucket": "other", "source_criterion": "Need for long-term oral anticoagulation; Patient has provided written informed consent.", "candidate_expression": "((Need for) AND (Patient has provided written informed consent) AND (long-term oral anticoagulation))"}
{"candidate_id": "LLM07493", "doc_id": "NCT03263481_exc", "case_bucket": "other", "source_criterion": "NA", "candidate_expression": "(EMPTY)"}
{"candidate_id": "LLM07494", "doc_id": "NCT02765217_exc", "case_bucket": "or", "source_criterion": "Receiving antibiotic and/or probiotic, 8 weeks before the study Chronic gastrointestinal system disorders Congenital anomalies Chronic diseases Chemotherapy and radiotherapy Pregnancy", "candidate_expression": "((Chemotherapy) AND (Chronic diseases) AND (Chronic gastrointestinal system disorders) AND (Congenital anomalies) AND (Pregnancy) AND (antibiotic) AND (probiotic) AND (radiotherapy))"}
{"candidate_id": "LLM07495", "doc_id": "NCT02924870_inc", "case_bucket": "or", "source_criterion": "subjects older than 35 years diagnosis of moderate to very severe COPD (FEV1 <80% predicted), according to the GesEPOC criteria, established at least 3 months current or former smoker with an accumulated consumption >10 packs x year hospital admission for COPD exacerbation", "candidate_expression": "((COPD at least 3 months) AND (COPD exacerbation) AND (FEV1 <80% predicted) AND (GesEPOC criteria,) AND (admission) AND (consumption >10 packs x year) AND (smoker) AND (years older than 35) AND ((moderate) OR (very severe)))"}
{"candidate_id": "LLM07496", "doc_id": "NCT02890719_inc", "case_bucket": "or", "source_criterion": "Age between 18 and 78 year-old. Previous liver transplantation(more than 6 month). Genotype 1 and 4 infection. Hepatitis C recurrence defined by the presence of abnormal liver function test, positive HCV-RNA, histological signs of hepatitis C recurrence. Viral load ≥10000UI/mL. Immunosuppression with tacrolimus and/or mycophenolate (Prednisone use is allowed at low dose, ≤10 mg/d). Treatment naïve or treatment experienced (Peg-RBV or triple therapy).", "candidate_expression": "((1 and 4) AND (Age) AND (Genotype) AND (HCV-RNA) AND (Hepatitis C) AND (Immunosuppression) AND (Previous) AND (Viral load) AND (abnormal) AND (between 18 and 78 year-old) AND (hepatitis C) AND (histological) AND (histological signs of hepatitis C recurrence) AND (infection) AND (liver function test) AND (liver transplantation) AND (low dose) AND (more than 6 month) AND (positive) AND (recurrence) AND (≤10 mg/d) AND (≥10000UI/mL) AND ((Prednisone) OR (mycophenolate) OR (tacrolimus)) AND ((Treatment naïve) OR (treatment experienced)) AND ((Peg-RBV) OR (triple therapy)))"}
{"candidate_id": "LLM07497", "doc_id": "NCT01891383_inc", "case_bucket": "or", "source_criterion": "Cases (with a history of TBI): 1. Ages 50-95 years 2. History of traumatic brain injury of sufficient severity to have resulted in medical attention (ascertained via the Ohio State University TBI Identification Questionnaire—OSU TBI-ID, and based on DoD/VA criteria) 3. Residence in AFRH-Washington D.C. or the Veterans Home of California-Yountville 4. MMSE score ≥ 20 5. Capacity to provide consent to participate in research (assessment made by study physician) 6. Ability to read and write English Controls (without a history of TBI): 1. Ages 50-95 years 2. No history of traumatic brain injury of sufficient severity to have resulted in medical attention (ascertained via the Ohio State University TBI Identification Questionnaire—OSU TBI-ID) 3. Residence in AFRH-Washington or the Veterans Home of California-Yountville 4. MMSE score ≥ 20 5. Capacity to provide consent or assent to participate in research 6. Ability to read and write English -", "candidate_expression": "((50-95 years) AND (AFRH-Washington) AND (AFRH-Washington D.C.) AND (Ability to read and write English) AND (Ability to read and write English -) AND (Ages) AND (Capacity to provide consent or assent to participate in research) AND (Capacity to provide consent to participate in research (assessment made by study physician)) AND (History) AND (MMSE) AND (No) AND (Ohio State University TBI Identification Questionnaire—OSU TBI-ID) AND (Residence) AND (Veterans Home of California-Yountville) AND (history) AND (score ≥ 20) AND (sufficient severity) AND (traumatic brain injury))"}
{"candidate_id": "LLM07498", "doc_id": "NCT03356834_inc", "case_bucket": "other", "source_criterion": "Chronic hepatitis B, Antiviral experienced, Currently on long term TDF anti-HBV treatment, HBV DNA < 6 log IU/ml (LLOD) Able to sign the consent form of anticipating in the study", "candidate_expression": "((Able to sign the consent form of anticipating in the study) AND (Antiviral experienced) AND (Chronic hepatitis B) AND (HBV) AND (HBV DNA < 6 log IU/ml LLOD) AND (TDF anti-HBV treatment) AND (TDF long term) AND (experienced))"}
{"candidate_id": "LLM07499", "doc_id": "NCT03068897_exc", "case_bucket": "or", "source_criterion": "Not available for follow-up Pregnant or breast-feeding Chronic pain syndrome defined as use of any analgesic medication on a daily or near-daily basis Allergic to or intolerant of investigational medications Contra-indications to non-steroidal anti-inflammatory drugs: 1) history of hypersensitivity to NSAIDs or aspirin 2) active or history of peptic ulcer disease, chronic dyspepsia, or active or history of gastrointestinal bleed 3) Severe heart failure (NYHA 2 or worse) 4) hypertension (JNC7 stage 2 or worse) 5) Chronic kidney disease 3 or worse 6) Current use of anti-coagulants 7) Hepatitis 8) Alcoholism Contra-indications to muscle relaxants: 1) Concurrent use of centrally acting opioids; 2) Renal impairment; 3) Liver abnormality including cirrhosis or elevated enzymes 4) Use of any of the following medications: fluvoxamine, fluoroquinolones, amiodarone, mexiletine, propafenone, verapamil, cimetidine, famotidine, acyclovir, ticlopidine, oral contraceptive pills", "candidate_expression": "((Alcoholism) AND (Allergic) AND (Chronic kidney disease) AND (Chronic pain syndrome) AND (Contra-indications) AND (Hepatitis) AND (JNC7 stage 2 or worse) AND (Liver abnormality) AND (NSAIDs) AND (NYHA 2 or worse) AND (Pregnant) AND (Renal impairment) AND (acyclovir) AND (amiodarone) AND (analgesic medication any on a daily basis on a near-daily basis) AND (anti-coagulants Current) AND (aspirin active) AND (breast-feeding) AND (centrally acting opioids Concurrent) AND (chronic dyspepsia active) AND (cimetidine) AND (cirrhosis) AND (elevated enzymes) AND (famotidine) AND (fluoroquinolones) AND (fluvoxamine) AND (gastrointestinal bleed) AND (heart failure Severe) AND (history) AND (hypersensitivity history) AND (hypertension) AND (intolerant) AND (investigational medications) AND (mexiletine) AND (muscle relaxants) AND (non-steroidal anti-inflammatory drugs) AND (oral contraceptive pills) AND (peptic ulcer disease) AND (propafenone) AND (ticlopidine) AND (verapamil))"}
{"candidate_id": "LLM07500", "doc_id": "NCT03234816_inc", "case_bucket": "other", "source_criterion": "full term singleton pregnant women Scheduled for elective Cesarean Delivery Aged between 18 and 40 years", "candidate_expression": "((Aged) AND (Cesarean Delivery) AND (Scheduled for) AND (between 18 and 40 years) AND (elective) AND (full term) AND (pregnant) AND (singleton) AND (women))"}
```
