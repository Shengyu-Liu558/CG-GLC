# GPT Evaluation Batch

请先阅读并遵循以下评估指南，然后评价本批候选。只输出 JSONL 评分结果。

## Evaluation Guide

# GPT 评估指南

本指南用于让大模型对临床试验纳排标准的候选布尔表达式进行盲化语义评估。GPT 评分不是金标准，也不是对隐藏答案的匹配；它只是在固定 rubric 下，根据原始纳排标准文本判断候选表达式的忠实性、完整性和可用性。

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

## 给 Codex 或 GPT 的输入模板

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
- 如果输出行数不是 25 行，请停止并说明原因。
```

评估下一批时，只需要把文件名改成 `gpt_eval_batch_0002.md`、`gpt_eval_batch_0003.md`，依次类推。所有批次完成后，再运行汇总脚本。

## Candidate Items

```jsonl
{"candidate_id": "LLM06551", "doc_id": "NCT03062358_inc", "case_bucket": "or", "source_criterion": "Has a HCC diagnosis confirmed by radiology, histology, or cytology (fibrolamellar, and mixed hepatocellular/cholangiocarcinoma subtypes are not eligible) Has Barcelona Clinic Liver Cancer (BCLC) Stage C disease or BCLC Stage B disease not amenable to locoregional therapy or refractory to locoregional therapy and not amenable to a curative treatment approach Has a Child-Pugh A liver score within 7 days prior to first dose of study medication Has a life expectancy of >3 months Has at least one measurable lesion based on RECIST version 1.1 as determined by investigator Has Eastern Cooperative Oncology Group (ECOG) performance status of 0 or 1 performed within 7 days prior to receiving the first dose of study medication Has documented objective radiographic progression during or after treatment with sorafenib or oxaliplatin-based chemotherapy, or else intolerance to sorafenib or oxaliplatin-based chemotherapy Female participants of childbearing potential must have a negative urine or serum pregnancy test within 72 hours prior to receiving the first dose of study therapy Female and male participants of reproductive potential must agree to use adequate contraception starting from the first dose of study medication, throughout the study period, and for up to 120 days after the last dose of study medication", "candidate_expression": "((0 or 1) AND (>3 months) AND (A) AND (BCLC) AND (Barcelona Clinic Liver Cancer (BCLC)) AND (Child-Pugh liver score) AND (Eastern Cooperative Oncology Group (ECOG) performance status) AND (Female) AND (Female and male participants of reproductive potential must agree to use adequate contraception starting from the first dose of study medication, throughout the study period, and for up to 120 days after the last dose of study medication) AND (Female participants of childbearing potential must have a negative urine or serum pregnancy test within 72 hours prior to receiving the first dose of study therapy) AND (HCC) AND (RECIST version 1.1) AND (Stage B) AND (Stage C) AND (adequate contraception) AND (amenable to a curative treatment approach) AND (amenable to locoregional therapy) AND (at least one) AND (chemotherapy) AND (childbearing potential) AND (cytology) AND (disease) AND (during or after) AND (first dose of study medication) AND (histology) AND (intolerance) AND (lesion) AND (life expectancy) AND (male) AND (measurable) AND (mixed hepatocellular/cholangiocarcinoma subtype) AND (negative) AND (not) AND (not eligible) AND (objective progression) AND (oxaliplatin) AND (pregnancy test urine) AND (radiographic) AND (radiology) AND (receiving the first dose of study medication) AND (receiving the first dose of study therapy) AND (refractory to locoregional therapy) AND (reproductive potential) AND (serum pregnancy test) AND (sorafenib) AND (sorafenib or oxaliplatin-based) AND (subtype fibrolamellar) AND (treatment with sorafenib or oxaliplatin-based chemotherapy) AND (within 7 days prior) AND (within 72 hours prior))"}
{"candidate_id": "LLM06552", "doc_id": "NCT02332291_exc", "case_bucket": "or", "source_criterion": "Current or past diagnoses of other Axis I psychiatric disorders, except for generalized anxiety disorder (GAD) symptoms occurring during a depressive episode History of alcohol or drug dependence or abuse in the last three years History of developmental disorder or IQ score < 70 Presence of acute suicidality Acute grief (< 1 month) Current or past psychosis Primary neurological disorder, including but not limited to dementia, stroke, brain tumors, epilepsy, Parkinson's disease, or demyelinating diseases MRI contraindications Any physical or intellectual disability adversely affecting ability to complete assessments Electroconvulsive therapy in last 6 months Use of antidepressant medications or other psychotropic medications in the last 4 weeks (or the last 6 weeks for fluoxetine). Occasional use of benzodiazepines or non-benzodiazepine sedatives (such as zolpidem, eszopiclone, or zaleplon) during this period is allowable. A failed therapeutic trial of escitalopram in the current depressive episode (defined as at least 6 weeks of treatment at a daily dose of 10mg or higher) Known allergy or hypersensitivity to escitalopram or bupropion Current or planned psychotherapy", "candidate_expression": "((Acute grief < 1 month) AND (Axis I psychiatric disorders other) AND (Electroconvulsive therapy in last 6 months) AND (MRI) AND (Primary neurological disorder) AND (acute suicidality) AND (contraindications) AND (depressive episode) AND (depressive episode at least 6 weeks of treatment daily dose of 10mg or higher) AND (escitalopram in the current depressive episode depressive episode) AND (fluoxetine) AND (psychosis) AND (psychotherapy) AND (therapeutic trial failed) AND NOT (generalized anxiety disorder (GAD) during a depressive episode) AND ((alcohol abuse) OR (alcohol dependence) OR (drug abuse) OR (drug dependence)) AND ((IQ score < 70) OR (developmental disorder)) AND ((Current) OR (past)) AND ((Parkinson's disease) OR (brain tumors) OR (dementia) OR (demyelinating diseases) OR (epilepsy) OR (stroke)) AND ((intellectual disability) OR (physical disability)) AND ((antidepressant medications) OR (psychotropic medications other)) AND ((in the last 4 weeks) OR (in the last 6 weeks)) AND ((benzodiazepines sedatives) OR (non-benzodiazepine sedatives)) AND ((eszopiclone) OR (zaleplon) OR (zolpidem)) AND ((allergy) OR (hypersensitivity)) AND ((bupropion) OR (escitalopram)) AND ((Current) OR (planned)))"}
{"candidate_id": "LLM06553", "doc_id": "NCT01765231_inc", "case_bucket": "other", "source_criterion": "treatment-naive patients with lymphoma HBsAg negative/HBcAb positive/hepatitis B virus DNA negative at baseline treated with chemotherapy and/or immunosuppressive therapy life expectancy of more than 3 months", "candidate_expression": "((HBcAb positive) AND (HBsAg negative) AND (chemotherapy) AND (hepatitis B virus DNA negative) AND (immunosuppressive therapy) AND (life expectancy more than 3 months) AND (lymphoma) AND (treatment-naive))"}
{"candidate_id": "LLM06554", "doc_id": "NCT01184638_exc", "case_bucket": "other", "source_criterion": "With the history of cognitive disorders With chronic neurological disorders Cannot communicate with investigators Cannot stand general anesthesia", "candidate_expression": "((Cannot communicate) AND (Cannot stand) AND (chronic neurological disorders) AND (cognitive disorders) AND (general anesthesia))"}
{"candidate_id": "LLM06555", "doc_id": "NCT02884115_exc", "case_bucket": "other", "source_criterion": "Human immunodeficiency virus (HIV)-infected Baseline serology showed a nonreactive RPR test follow-up is inadequate Allergic to penicillin Pregnant woman", "candidate_expression": "((Allergic) AND (Human immunodeficiency virus (HIV)-infected) AND (Pregnant) AND (RPR test nonreactive) AND (follow-up is inadequate) AND (penicillin) AND (serology Baseline) AND (woman))"}
{"candidate_id": "LLM06556", "doc_id": "NCT03091881_exc", "case_bucket": "or", "source_criterion": "Contraindications for spinal anesthesia (like bleeding diathesis or regional infection at site of neuroaxial block) Known allergy to Granisetron or local anaesthetic (heavy bupivacaine, Marcaine Spinal 0.5% Heavy, 5mg/ml, AstraZeneca ampule) Pregnancy induced hypertension Congenital or rheumatic heart diseases Antepartum haemorrhage Fetal destress or gestational age < 36 week", "candidate_expression": "((Antepartum haemorrhage) AND (Contraindications) AND (Marcaine Spinal 0.5% Heavy 5mg/ml AstraZeneca ampule) AND (Pregnancy) AND (allergy) AND (heart diseases) AND (heavy bupivacaine) AND (hypertension Pregnancy induced) AND (spinal anesthesia) AND ((Congenital) OR (rheumatic)) AND ((Fetal destress) OR (gestational age < 36 week)) AND ((bleeding diathesis) OR (regional infection)) AND ((Granisetron) OR (local anaesthetic)))"}
{"candidate_id": "LLM06557", "doc_id": "NCT02607319_inc", "case_bucket": "or", "source_criterion": "History of three or more consecutively failed In Vitro Fertilization (IVF) cycles after embryo transfer. Normal uterine cavity (as assessed by hysteroscopy or HSG). Normal hormonal investigation: TSH, PRL, FBS. Normal acquired/inherited thrombophilia profile: LAC, ACA IgG/IgM, Prot S, Antithrombin III, beta-2 glycoprotein, Factors V, II, MTHFR. Normal semen analysis and mild/moderate male factor (Total motile sperm count > 5 million/ml and/or normal WHO morphology >20%. Patient provides written informed consent.", "candidate_expression": "((> 5 million/ml) AND (>20%) AND (ACA IgG) AND (ACA IgM) AND (Antithrombin III) AND (FBS) AND (Factors II) AND (Factors V) AND (HSG) AND (IVF) AND (In Vitro Fertilization) AND (LAC) AND (MTHFR) AND (Normal) AND (PRL) AND (Patient provides written informed consent) AND (Prot S) AND (TSH) AND (Total motile sperm count) AND (after embryo transfer) AND (beta-2 glycoprotein) AND (consecutively failed) AND (embryo transfer) AND (hormonal investigation:) AND (hysteroscopy) AND (male factor) AND (mild) AND (moderate) AND (normal WHO morphology) AND (semen analysis) AND (three or more) AND (thrombophilia profile) AND (uterine cavity))"}
{"candidate_id": "LLM06558", "doc_id": "NCT00894712_inc", "case_bucket": "or", "source_criterion": "Must have pathologically confirmed invasive adenocarcinoma or ductal carcinoma in situ of the breast. Patients must have undergone segmental mastectomy (i.e., lumpectomy). Patients must not have received prior radiation therapy to the breast. Patients must not have active local-regional disease prior to registration. Patients must not be pregnant because of the potential for fetal harm as a result of radiation treatment. Women of child-bearing age will be given a serum pregnancy test prior to study entry to ensure they are not pregnant. They will also be counseled on the importance of avoiding pregnancy and hormonal contraception while undergoing radiation therapy. Patients must not have a serious medical or psychiatric illness which prevents informed consent or compliance with treatment. All patients must be informed of the investigational nature of this study and give written informed consent in accordance with institutional and federal guidelines.", "candidate_expression": "((All patients must be informed of the investigational nature of this study and give written informed consent in accordance with institutional and federal guidelines.) AND (Patients must not be pregnant because of the potential for fetal harm as a result of radiation treatment. Women of child-bearing age will be given a serum pregnancy test prior to study entry to ensure they are not pregnant. They will also be counseled on the importance of avoiding pregnancy and hormonal contraception while undergoing radiation therapy.) AND (Patients must not have a serious medical or psychiatric illness which prevents informed consent or compliance with treatment.) AND (ductal carcinoma in situ of the breast) AND (invasive adenocarcinoma of the breast) AND (lumpectomy) AND (pathologically confirmed) AND (segmental mastectomy) AND NOT (local-regional disease active) AND NOT (radiation therapy))"}
{"candidate_id": "LLM06559", "doc_id": "NCT03226080_exc", "case_bucket": "or", "source_criterion": "Inability to consent/refusal Allergy to any of the study medications Multiple traumatic injuries Contraindication to neuraxial or general anesthesia Pregnancy", "candidate_expression": "((Allergy) AND (Contraindication) AND (Multiple traumatic injuries) AND (Pregnancy) AND (study medications) AND ((Inability to consent) OR (refusal)) AND ((general anesthesia) OR (neuraxial anesthesia)))"}
{"candidate_id": "LLM06560", "doc_id": "NCT02152696_inc", "case_bucket": "or", "source_criterion": "Female with a persisting pregnancy of unknown location: A pregnancy of unknown location is defined as a pregnancy in a woman with a positive pregnancy test but no definitive signs of pregnancy in the uterus or adnexa on ultrasound imaging. A definitive sign of gestation includes ultrasound visualization of a gestational sac with a yolk sac (with or without an embryo) in the uterus or in the adnexa. Ultrasound must be performed within 7 days prior to randomization. Persistence of hCG is defined as at least 2 serial hCG values (over 2-14 days), showing < 15% rise per day, or < 50% fall between the first and last value. Patient is hemodynamically stable, hemoglobin >10 mg/dL Greater than or 18 years of age", "candidate_expression": "((Female) AND (Persistence of hCG at least 2) AND (Ultrasound within 7 days prior to randomization) AND (age Greater than or 18 years) AND (hCG over 2-14 days < 15% rise per day < 50% fall between the first and last value.) AND (hemodynamically stable) AND (hemoglobin >10 mg/dL) AND (pregnancy) AND (pregnancy test positive) AND (pregnancy unknown location) AND (woman))"}
{"candidate_id": "LLM06561", "doc_id": "NCT01483118_exc", "case_bucket": "or", "source_criterion": "Current pregnancy or lactation Liver disease or elevated liver enzymes Established diagnosis of diabetes mellitus Abnormal serum glucose levels either at fasting or after the 2-hr oral glucose tolerance test meeting criteria for the diagnosis of diabetes mellitus according to the American Diabetes Association. Insulin sensitizing treatment within 3 months prior to or during the eight week study period. Hormonal treatment involving estrogen or progesterone 3 months prior to or during the study period, with the exception of medroxyprogesterone acetate for withdrawal bleeding. Systemic or inhaled corticosteroids. Known hypersensitive reaction to cinnamon. Patients with seizure disorders, known cardiovascular disease, or cerebrovascular disease. Body mass index (BMI)range 20-50 (excluding all women with BMI under 20 or over 50).", "candidate_expression": "((2-hr oral glucose tolerance test) AND (Abnormal) AND (Abnormal serum glucose levels) AND (Body mass index (BMI)) AND (Insulin sensitizing treatment) AND (Liver disease) AND (Systemic) AND (Systemic corticosteroids) AND (cinnamon) AND (criteria for the diagnosis of diabetes mellitus according to the American Diabetes Association) AND (diabetes mellitus) AND (elevated) AND (elevated liver enzymes) AND (estrogen) AND (exception) AND (fasting) AND (hypersensitive reaction to cinnamon) AND (inhaled) AND (inhaled corticosteroids) AND (liver enzymes) AND (medroxyprogesterone acetate) AND (meeting) AND (meeting criteria for the diagnosis of diabetes mellitus according to the American Diabetes Association) AND (progesterone) AND (range 20-50) AND (serum glucose levels) AND (the 2-hr oral glucose tolerance test) AND (withdrawal bleeding) AND ((after the 2-hr oral glucose tolerance test) OR (at fasting)) AND ((lactation) OR (pregnancy)) AND ((during the eight week study period) OR (within 3 months prior to eight week study period)) AND ((3 months prior to the study period) OR (during the study period)) AND ((cardiovascular disease) OR (cerebrovascular disease) OR (seizure disorders)))"}
{"candidate_id": "LLM06562", "doc_id": "NCT03011177_exc", "case_bucket": "other", "source_criterion": "NA", "candidate_expression": "(EMPTY)"}
{"candidate_id": "LLM06563", "doc_id": "NCT02337764_exc", "case_bucket": "or", "source_criterion": "The participant has Modified Hoehn & Yahr stage 5 (or stage 5 at eather on-time or off-time for the participant with wearing off phenomenon). The participant has severe dyskinesia. The participant has unstable systemic disease. The participant has a Mini-Mental State Examinations (MMSE) score of <= 24. psychiatric disease. The participant has a history of clinically significant hypertension or other reactions associated with ingestion of tyramine-rich food. The participant has received neurosurgical intervention for Parkinson's disease (e.g., pallidotomy, thalamotomy, deep brain stimulation). The participant has received transcranial magnetic stimulation within 6 months.The participant has received selegiline, pethidine, tramadol, reserpine or methyldopa within 90 days. The participant has received levodopa monotherapy, any psychoneurotic agent or antiemetic medication of dopamine agonist within 14 days. However, the participant has been receiving quetiapine or domperidone with a stable dose regimen for >= 14 days may be included in the study. The participant is required to take any of the excluded medications or treatments. The participant with laboratory data meeting any of the following: Creatinine >= 2 x upper limit of normal (ULN) Total bilirubin >= 2 x ULN ALT or AST >= 1.5 x ULN ALP >= 3 x ULN The participant has received any of the excluded medications or treatments during.", "candidate_expression": "((<= 24) AND (>= 1.5 x ULN) AND (>= 14 days) AND (>= 2 x ULN) AND (>= 2 x upper limit of normal (ULN)) AND (>= 3 x ULN) AND (ALP) AND (Creatinine) AND (Mini-Mental State Examinations (MMSE)) AND (Modified Hoehn & Yahr) AND (Parkinson's disease) AND (The participant has received any of the excluded medications or treatments during.) AND (The participant is required to take any of the excluded medications or treatments.) AND (Total bilirubin) AND (clinically significant) AND (dyskinesia) AND (levodopa monotherapy) AND (neurosurgical intervention) AND (psychiatric disease) AND (severe) AND (stable dose) AND (stage 5) AND (systemic disease) AND (transcranial magnetic stimulation) AND (unstable) AND (wearing off phenomenon) AND (within 14 days) AND (within 6 months) AND (within 90 days) AND ((hypertension) OR (reactions associated with ingestion of tyramine-rich food)) AND ((deep brain stimulation) OR (pallidotomy) OR (thalamotomy)) AND ((methyldopa) OR (pethidine) OR (reserpine) OR (selegiline) OR (tramadol)) AND ((antiemetic medication of dopamine agonist) OR (levodopa) OR (psychoneurotic agent)) AND ((at off-time) OR (at on-time)) AND ((domperidone) OR (quetiapine)) AND ((ALT) OR (AST)))"}
{"candidate_id": "LLM06564", "doc_id": "NCT02015923_exc", "case_bucket": "or", "source_criterion": "Cases of rectal tumours below 12cm from anal verge, or locally advanced tumours invading blood vessels, nerves or bone. Multiple bone metastasis or central nervous system metastasis Other neoplastic disease in the 5 previous years, except squamous or basal cell skin carcinoma or cervical \"in situ\" carcinoma Significant heart disease (chronic congestive heart failure, symptomatic coronary disease) or myocardial infarction in the previous 6 months Peripheral neuropathy Patients who do not give informed consent", "candidate_expression": "((Multiple bone metastasis) AND (Other) AND (Peripheral neuropathy) AND (Significant) AND (basal cell skin carcinoma) AND (below 12cm from anal verge) AND (bone invading) AND (central nervous system metastasis) AND (cervical \"in situ\" carcinoma) AND (chronic congestive heart failure) AND (except) AND (heart disease) AND (in the 5 previous years) AND (in the previous 6 months) AND (invading blood vessels) AND (locally advanced tumours) AND (myocardial infarction) AND (neoplastic disease) AND (nerves invading) AND (rectal tumours) AND (squamous cell skin carcinoma) AND (symptomatic coronary disease))"}
{"candidate_id": "LLM06565", "doc_id": "NCT02984228_exc", "case_bucket": "or", "source_criterion": "Non-English speaking/illiterate Painful active, concurrent cervical spine conditions Current non-steroidal anti-inflammatory drug (NSAID) use History of taking coumadin or similar anticoagulant, have a known coagulopathy, bleeding dyscrasia, or platelet count < 150,000/cubic mm Allergic reaction to poultry or previous viscosupplementation Involved in workers' compensation or active litigation involving affected shoulder Inability to refrain from NSAID use for 5 days prior to and 6 weeks after injection History of corticosteroid injection to affected shoulder within the last 3 months History of viscosupplementation or platelet-rich plasma to affected shoulder within the last 6 months Presence of acute fracture History of shoulder tumor Known uncontrolled systemic illness (uncontrolled diabetes, human immunodeficiency virus, vasculitis, autoimmune/inflammatory disease) Psychiatric and somatoform disorders", "candidate_expression": "((Allergic reaction) AND (NSAID) AND (NSAID Inability to refrain from 5 days prior to and 6 weeks after injection) AND (Non-English speaking/illiterate) AND (Painful) AND (cervical spine conditions) AND (corticosteroid injection History of shoulder last 3 months) AND (fracture acute) AND (non-steroidal anti-inflammatory drug) AND (shoulder tumor History of) AND (systemic illness uncontrolled) AND ((poultry) OR (viscosupplementation)) AND ((platelet-rich plasma) OR (viscosupplementation)) AND ((autoimmune) OR (diabetes uncontrolled) OR (human immunodeficiency virus) OR (inflammatory disease) OR (vasculitis)) AND ((Psychiatric disorders) OR (somatoform disorders)) AND ((anticoagulant) OR (coumadin)) AND ((bleeding dyscrasia) OR (coagulopathy) OR (platelet count < 150,000/cubic mm)))"}
{"candidate_id": "LLM06566", "doc_id": "NCT01490034_exc", "case_bucket": "other", "source_criterion": "", "candidate_expression": "(EMPTY)"}
{"candidate_id": "LLM06567", "doc_id": "NCT01217671_exc", "case_bucket": "or", "source_criterion": "FEV1 >= 80% or FEV1 < 20% of predicted value post-bronchodilator. FEV1/SVC>=70% History of lung transplant. Any lung surgery within the past two years. On any thoracic surgery waiting list. End of last exacerbation less than 6 weeks prior to screening/re-screening visit. Clinically significant intercurrent illnesses (except for respiratory or liver disease secondary to AAT deficiency), including: cardiac, hepatic, renal, endocrine, neurological, hematological, neoplastic, immunological, skeletal or other) that in the opinion of the investigator, could interfere with the safety, compliance or other aspects of this study. Patients with well-controlled, chronic diseases could possibly be included after consultation with the treating physician and the sponsor. Active smoking during the last 12 months from screening date. Pregnancy or lactation. Woman of child-bearing potential not taking adequate contraception deemed reliable by the investigator. Presence of psychiatric/ mental disorder or any other medical disorder which might impair the patient's ability to give informed consent or to comply with the requirements of the study protocol. Evidence of ongoing viral infection with HCV, HBV and/or HIV. Evidence of alcohol abuse or history of alcohol abuse or illegal and/or legally prescribed drugs. IgA Deficiency History of life threatening allergy, anaphylactic reaction, or systemic response to human plasma derived products. Participation in another clinical trial within 30 days prior to baseline visit. Inability to attend scheduled clinic visits and/or comply with the study protocol. Any other factor that, in the opinion of the investigator, would prevent the patient from complying with the requirements of the protocol.", "candidate_expression": "((< 20% of predicted value) AND (>= 80%) AND (>=70%) AND (AAT deficiency) AND (Active) AND (Active smoking) AND (Any other factor that, in the opinion of the investigator, would prevent the patient from complying with the requirements of the protocol.) AND (Clinically significant) AND (Clinically significant intercurrent illnesses (except for respiratory or liver disease secondary to AAT deficiency), including: cardiac, hepatic, renal, endocrine, neurological, hematological, neoplastic, immunological, skeletal or other) that in the opinion of the investigator, could interfere with the safety, compliance or other aspects of this study. Patients with well-controlled, chronic diseases could possibly be included after consultation with the treating physician and the sponsor.) AND (FEV1/SVC) AND (History) AND (IgA Deficiency) AND (Inability to attend scheduled clinic visits and/or comply with the study protocol.) AND (Presence of psychiatric/ mental disorder or any other medical disorder which might impair the patient's ability to give informed consent or to comply with the requirements of the study protocol.) AND (Woman) AND (Woman of child-bearing potential not taking adequate contraception deemed reliable by the investigator.) AND (adequate) AND (alcohol abuse) AND (bronchodilator) AND (cardiac) AND (child-bearing potential) AND (contraception) AND (deemed reliable by the investigator) AND (during the last 12 months from screening date) AND (endocrine) AND (exacerbation) AND (except for) AND (hematological) AND (hepatic) AND (history) AND (human plasma derived) AND (immunological) AND (impair the patient's ability to give informed consent) AND (in the opinion of the investigator) AND (intercurrent illnesses) AND (less than 6 weeks prior to screening/re-screening visit) AND (life threatening) AND (lung surgery) AND (lung transplant) AND (neoplastic) AND (neurological) AND (not) AND (ongoing) AND (other) AND (post-bronchodilator) AND (products) AND (renal) AND (screening date) AND (screening/re-screening visit) AND (secondary to AAT deficiency) AND (skeletal) AND (thoracic surgery) AND (thoracic surgery waiting list) AND (viral infection) AND (within the past two years) AND ((FEV1)) AND ((liver disease) OR (respiratory disease)) AND ((Pregnancy) OR (lactation)) AND ((mental disorder) OR (other medical disorder) OR (psychiatric disorder)) AND ((HBV) OR (HCV) OR (HIV)) AND ((abuse illegal drugs) OR (abuse legally prescribed drugs) OR (alcohol abuse)) AND ((anaphylactic reaction) OR (life threatening allergy) OR (systemic response to human plasma derived products)))"}
{"candidate_id": "LLM06568", "doc_id": "NCT02912182_exc", "case_bucket": "or", "source_criterion": "tinnitus or hearing loss with same debut as vertigo history of bleeding peptic ulcer glaucoma pregnancy or non-acceptance to use anticonception measures during 13 days after debut high blood pressure >180 systolic, 105, diastolic ketoacidosis with a Base Excess >=2 psychic disorder (not including mild depression) serious infection (neutropenia, tuberculosis) chronic otitis history of vertiginous disease; Ménière, Vertiginous migraine, atypical BPPV", "candidate_expression": "((Base Excess >=2) AND (bleeding) AND (blood pressure diastolic 105) AND (blood pressure systolic >180) AND (chronic otitis) AND (glaucoma) AND (infection serious) AND (ketoacidosis) AND (peptic ulcer) AND (pregnancy or non-acceptance to use anticonception measures during 13 days after debut) AND (psychic disorder) AND (vertigo) AND NOT (mild depression) AND ((hearing loss) OR (tinnitus)) AND ((neutropenia) OR (tuberculosis)) AND ((Ménière) OR (Vertiginous migraine) OR (atypical BPPV) OR (vertiginous disease)))"}
{"candidate_id": "LLM06569", "doc_id": "NCT02952365_exc", "case_bucket": "or", "source_criterion": "Subjects under the age of 21. Subjects with excessively thin corneas. Subjects with topographic evidence of keratoconus. Subjects with ectatic eye disorders. Subjects with autoimmune diseases. Subjects who are pregnant or nursing.", "candidate_expression": "((age) AND (autoimmune diseases) AND (ectatic eye disorders) AND (excessively thin corneas) AND (keratoconus) AND (nursing) AND (pregnant) AND (topographic evidence) AND (under the age of 21))"}
{"candidate_id": "LLM06570", "doc_id": "NCT02277067_exc", "case_bucket": "other", "source_criterion": "Women undergoing cesarean section with general anesthesia will be excluded, because carbetocin is licensed for use with regional anaesthesia only. women undergoing cesarean section at less than 37 weeks of gestation.", "candidate_expression": "((Women) AND (cesarean section) AND (general anesthesia) AND (gestation) AND (less than 37 weeks) AND (women))"}
{"candidate_id": "LLM06571", "doc_id": "NCT02704754_inc", "case_bucket": "other", "source_criterion": "Physically healthy adults age 18-55 who meet DSM-5 criteria for insomnia and Criterion A (exposure to a traumatic event) for PTSD. The index trauma must have occurred within the past 5 years and at least 3 months before enrolling, and insomnia symptoms must have started or worsened after the exposure to the index trauma", "candidate_expression": "((PTSD Criterion A) AND (adults healthy) AND (age 18-55) AND (insomnia DSM-5) AND (trauma index the past 5 years and at least 3 months))"}
{"candidate_id": "LLM06572", "doc_id": "NCT02542956_inc", "case_bucket": "or", "source_criterion": "Undergoing abdominoplasty or TRAM flap breast reconstruction", "candidate_expression": "((TRAM flap breast reconstruction) AND (abdominoplasty))"}
{"candidate_id": "LLM06573", "doc_id": "NCT02926989_exc", "case_bucket": "other", "source_criterion": "An initial plasma sodium concentration of lower than 130 mmol/L An initial plasma sodium concentration of higher than 150 mmol/L An initial plasma potassium concentration of lower than 3.0 mmol/L Need for 10% glucose solution Diabetes Diabetes insipidus Diabetic ketoacidosis Renal disease that needs dialysis Protocol-determined chemotherapy hydration Severe liver disease Inborn errors of metabolism that need protocol-determined fluid therapy", "candidate_expression": "((10% glucose solution Need for) AND (Diabetes) AND (Diabetes insipidus) AND (Diabetic ketoacidosis) AND (Inborn errors of metabolism) AND (Renal disease) AND (chemotherapy hydration Protocol-determined) AND (dialysis needs) AND (fluid therapy need protocol-determined) AND (liver disease Severe) AND (plasma potassium concentration initial lower than 3.0 mmol/L) AND (plasma sodium concentration initial higher than 150 mmol/L) AND (plasma sodium concentration initial lower than 130 mmol/L))"}
{"candidate_id": "LLM06574", "doc_id": "NCT02627521_inc", "case_bucket": "other", "source_criterion": "Accepted for CABG surgery Treatment with Ticagrelor within 48 hours", "candidate_expression": "((Accepted for) AND (CABG surgery) AND (Ticagrelor) AND (Treatment) AND (within 48 hours))"}
{"candidate_id": "LLM06575", "doc_id": "NCT03278548_exc", "case_bucket": "other", "source_criterion": "NA", "candidate_expression": "(EMPTY)"}
```
