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
{"candidate_id": "LLM02451", "doc_id": "NCT01032109_exc", "case_bucket": "or", "source_criterion": "choroidal neovascularization caused by other eye diseases ocular surgery within the past 3 mouths history of uveitis intraocular pressure higher than 25 mmHg, or glaucoma history of systemic or ocular thromboembolic events.", "candidate_expression": "((choroidal neovascularization other) AND (ocular surgery within the past 3 mouths) AND (other eye diseases) AND (thromboembolic events) AND (uveitis history) AND ((glaucoma) OR (intraocular pressure higher than 25 mmHg)) AND ((ocular) OR (systemic)))"}
{"candidate_id": "LLM02452", "doc_id": "NCT02019628_inc", "case_bucket": "or", "source_criterion": "1. Women and men ages 18 years and over. 2. Interest in participating in a novel nutritional supplement program. 3. Willingness to follow recommendations.", "candidate_expression": "((18 years and over) AND (Interest in participating in a novel nutritional supplement program.) AND (Willingness to follow recommendations.) AND (Women) AND (ages) AND (men))"}
{"candidate_id": "LLM02453", "doc_id": "NCT02580630_inc", "case_bucket": "or", "source_criterion": "Midsubstance pain in the achilles tendon Symptoms for at least 3 months Ultrasound scanning at the first visit shows thickness of the achilles tendon above 7 mm or 20% thicker than the contralateral. Patient can read and understand danish", "candidate_expression": "((20% thicker than the contralateral) AND (Midsubstance pain) AND (Symptoms) AND (Ultrasound scanning) AND (above 7 mm) AND (achilles tendon) AND (at the first visit) AND (for at least 3 months) AND (thickness of the achilles tendon))"}
{"candidate_id": "LLM02454", "doc_id": "NCT01816997_exc", "case_bucket": "or", "source_criterion": "A1C >7.0% 2hr glucose during OGTT >200 mg/dL Total cholesterol >280 mg/dL Previous diabetic history, coronary artery disease Allergy to rosuvastatin or parvastatin Baseline ALT more than 3 times UNL Serum Cr > 2.0 mg/dL Pregnancy, breast feeding or plan to be pregnant woman.", "candidate_expression": "((2hr glucose during OGTT) AND (> 2.0 mg/dL) AND (>200 mg/dL) AND (>280 mg/dL) AND (>7.0%) AND (A1C) AND (ALT) AND (Allergy) AND (Baseline) AND (Previous) AND (Serum Cr) AND (Total cholesterol) AND (history) AND (more than 3 times UNL) AND (plan to be) AND (woman) AND ((coronary artery disease) OR (diabetic)) AND ((parvastatin) OR (rosuvastatin)) AND ((Pregnancy) OR (breast feeding) OR (pregnant)))"}
{"candidate_id": "LLM02455", "doc_id": "NCT00785213_exc", "case_bucket": "or", "source_criterion": "Recent participation (within 28 days) in other research studies Recent significant blood donation or plasma donation Pregnant or lactating Test positive at screening for human immunodeficiency virus (HIV), hepatitis B surface antigen (HbsAg), or hepatitis C virus (HCV) Recent (2-year) history or evidence of alcoholism or drug abuse History or presence of significant cardiovascular, pulmonary, hepatic, gallbladder or biliary tract, renal, hematologic, gastrointestinal, endocrine, immunologic, dermatologic, neurologic, or psychiatric disease Subjects who have used any drugs or substances known to inhibit or induce cytochrome (CYP) P450 enzymes and/or P-glycoprotein (P-gp) within 28 days prior to the first dose and throughout the study Drug allergies to quinine sulfate or rosiglitazone", "candidate_expression": "((2-year) AND (History or presence of significant cardiovascular, pulmonary, hepatic, gallbladder or biliary tract, renal, hematologic, gastrointestinal, endocrine, immunologic, dermatologic, neurologic, or psychiatric disease) AND (Recent participation (within 28 days) in other research studies) AND (allergies) AND (drugs known to induce P-glycoprotein (P-gp)) AND (drugs known to inhibit P-glycoprotein (P-gp)) AND (within 28 days) AND ((hepatitis B surface antigen (HbsAg)) OR (hepatitis C virus (HCV)) OR (human immunodeficiency virus (HIV))) AND ((alcoholism) OR (drug abuse)) AND ((evidence) OR (history)) AND ((drugs known to induce cytochrome (CYP) P450 enzymes) OR (drugs known to inhibit cytochrome (CYP) P450 enzymes)) AND ((quinine sulfate) OR (rosiglitazone)) AND ((blood donation) OR (plasma donation)) AND ((Pregnant) OR (lactating)))"}
{"candidate_id": "LLM02456", "doc_id": "NCT02825290_inc", "case_bucket": "other", "source_criterion": "20-40 years old women Spontaneously ovulating women Treated in our IVF unit for frozen-thawed embryo transfer At least one top quality embryo", "candidate_expression": "((Spontaneously ovulating) AND (frozen-thawed embryo transfer) AND (old 20-40 years) AND (our IVF unit) AND (top quality embryo At least one) AND (women))"}
{"candidate_id": "LLM02457", "doc_id": "NCT02624908_exc", "case_bucket": "or", "source_criterion": "Type 1 diabetes Known peripheral artery disease Liver enzymes equal or more than 1.5 times the upper limit of normal Chronic heart failure NYHA class III or IV Current haemodialysis or peritoneal dialysis End stage liver disease, defined as acute or chronic liver disease and recent history of one of the following: ascites, encephalopathy, variceal bleeding, bilirubin equal or greater than 2.0 mg/dL, albumin equal or less than 3.5 g/ dL, prothrombin time greater or equal to 4 seconds, INR greater than or equal to 1.7 or prior liver transplant Known or suspected hypersensitivity to trial products or related products Female of child-bearing potential who is pregnant, breast-feeding or intends to become pregnant or is not using adequate contraceptive methods as required by law or local practice. Expected simultaneous participation in any other clinical trial of an investigational medicinal product. Receipt of any investigational medicinal product within 30 days before randomization Current or past (within the last 5 years) malignant neoplasms (except basal cell and squamous cell skin carcinoma) Any condition that in the investigator's opinion would make the subject unable to adhere to the trial visit schedule and procedures Known history of non-compliance to treatment.", "candidate_expression": "((Any condition that in the investigator's opinion would make the subject unable to adhere to the trial visit schedule and procedures) AND (Chronic heart failure) AND (Current) AND (End stage liver disease) AND (Female of child-bearing potential who is pregnant, breast-feeding or intends to become pregnant or is not using adequate contraceptive methods as required by law or local practice.) AND (Liver enzymes) AND (NYHA) AND (Type 1 diabetes) AND (class III or IV) AND (equal or greater than 2.0 mg/dL) AND (equal or less than 3.5 g/ dL) AND (equal or more than 1.5 times the upper limit of normal) AND (except) AND (greater or equal to 4 seconds) AND (greater than or equal to 1.7) AND (hypersensitivity) AND (malignant neoplasms) AND (peripheral artery disease) AND (prior) AND (recent) AND (within the last 5 years) AND ((acute liver disease) OR (chronic liver disease)) AND ((INR) OR (albumin) OR (ascites) OR (bilirubin) OR (encephalopathy) OR (liver transplant) OR (prothrombin time) OR (variceal bleeding)) AND ((related products) OR (trial products)) AND ((Known) OR (suspected)) AND ((Current) OR (past)) AND ((basal cell carcinoma) OR (squamous cell skin carcinoma)) AND ((haemodialysis) OR (peritoneal dialysis)))"}
{"candidate_id": "LLM02458", "doc_id": "NCT03340740_inc", "case_bucket": "other", "source_criterion": "History of allergic rhinitis Wheezing", "candidate_expression": "((Wheezing) AND (allergic rhinitis))"}
{"candidate_id": "LLM02459", "doc_id": "NCT03299517_exc", "case_bucket": "or", "source_criterion": "Pregnancy Hemodynamic instability Body mass index greater than 40 kg / m2 Use of intravenous amiodarone or lidocaine in the last 24 hours Acute coronary syndrome Presence of tachycardia with irregular or supraventricular RR Contraindications to study drugs", "candidate_expression": "((Acute coronary syndrome) AND (Body mass index) AND (Contraindications) AND (Hemodynamic instability) AND (Pregnancy) AND (greater than 40 kg / m2) AND (in the last 24 hours) AND (intravenous) AND (study drugs) AND (tachycardia) AND ((irregular RR) OR (supraventricular RR)) AND ((amiodarone) OR (lidocaine)))"}
{"candidate_id": "LLM02460", "doc_id": "NCT02416869_inc", "case_bucket": "other", "source_criterion": "Healthy patients (ASA I) Bilateral symmetrically impacted lower third molars according to Pel-Gregory's and Winter's classification", "candidate_expression": "((ASA I) AND (Healthy patients) AND (Pel-Gregory's and Winter's classification Bilateral symmetrically impacted lower third molars))"}
{"candidate_id": "LLM02461", "doc_id": "NCT01082549_inc", "case_bucket": "or", "source_criterion": "Eligible patients must meet the following criteria to be enrolled in the study: 1. Newly diagnosed, stage IV squamous cell lung cancer. This includes patients who present with disseminated metastases, and those with a malignant pleural or pericardial effusion (i.e., formerly stage IIIB in the 6th TNM staging system). 2. Patients who have received prior adjuvant therapy for early-stage lung cancer are eligible if at least 12 months have elapsed from that treatment. 3. Histologically confirmed squamous cell bronchogenic carcinoma. Patients whose tumors contain mixed non-small cell histologies are eligible, as long as squamous carcinoma is the predominant histology. Mixed tumors with small cell anaplastic elements are not eligible. Cytologic specimens obtained by brushings, washings, or needle aspiration of the defined lesion are acceptable. 4. Patients with previous radiotherapy as definitive therapy for locally advanced non-small cell lung cancer are eligible, as long as the recurrence is outside the original radiation therapy port. Radiation therapy must have been completed >4 weeks prior to the initiation of study treatment. Patients who have received chemo/radiation for locally advanced NSCLC are not eligible. Patients who have received palliative radiation therapy for symptomatic metastases must have completed treatment >14 days prior the initiation of the study treatment. 5. Presence of evaluable (measureable or non-measurable) disease. 6. ECOG Performance Status of 0 or 1. 7. Laboratory values as follows: Absolute neutrophil count (ANC) >1,500/microL and platelets >100,000/microL (≤72 hours prior to initial treatment). Hemoglobin >9 g/dL (Note: Patients may be transfused or receive erythropoietin to maintain or exceed this level). Bilirubin < ULN. Alanine aminotransferase (ALT) and aspartate aminotransferase (AST) ≤2.5 times the upper limit of normal if no liver involvement or ≤5 times the upper limit of normal with liver involvement. Creatinine <2.0 mg/dL, or creatinine clearance >40 mL/min (as calculated by the Cockcroft-Gault method. 8. Women of childbearing potential must have a negative serum pregnancy test performed within 7 days prior to start of treatment. Women of childbearing potential or men with partners of childbearing potential must use effective birth control measures during treatment and at least 6 months after the last dose of the study treatment. If a woman becomes pregnant or suspects she is pregnant while participating in this study, she must agree to inform her treating physician immediately. Sexually active men must agree to use a medically acceptable form of birth control during treatment and at least 6 months after the last dose. If a female partner becomes pregnant during the course of the study the treating physician should be informed immediately. 9. >18 years of age. 10. Ability to understand the nature of this study, give written informed consent, and comply with study requirements. 11. Patients entering this study must be willing to provide tissue from a previous tumor biopsy (if available) for correlative testing. An exception to this is when the national/local regulations prohibits some of the key activities of this research like the export of samples to third countries, storage of coded samples or global gene expression profiling without a pre-specified list of target genes. If tissue is not available, a patient will still be eligible for enrollment into the study.", "candidate_expression": "((6th TNM staging system stage IIIB) AND (8. Women of childbearing potential must have a negative serum pregnancy test performed within 7 days prior to start of treatment. Women of childbearing potential or men with partners of childbearing potential must use effective birth control measures during treatment and at least 6 months after the last dose of the study treatment. If a woman becomes pregnant or suspects she is pregnant while participating in this study, she must agree to inform her treating physician immediately. Sexually active men must agree to use a medically acceptable form of birth control during treatment and at least 6 months after the last dose. If a female partner becomes pregnant during the course of the study the treating physician should be informed immediately.) AND (Ability to understand the nature of this study, give written informed consent, and comply with study requirements.) AND (Absolute neutrophil count (ANC) >1,500/microL) AND (Alanine aminotransferase (ALT)) AND (Bilirubin < ULN) AND (Creatinine <2.0 mg/dL Cockcroft-Gault method) AND (ECOG Performance Status 0 or 1) AND (Hemoglobin >9 g/dL initial treatment) AND (Histologically confirmed) AND (Mixed tumors small cell anaplastic elements) AND (NSCLC locally advanced) AND (Patients entering this study must be willing to provide tissue from a previous tumor biopsy (if available) for correlative testing. An exception to this is when the national/local regulations prohibits some of the key activities of this research like the export of samples to third countries, storage of coded samples or global gene expression profiling without a pre-specified list of target genes. If tissue is not available, a patient will still be eligible for enrollment into the study) AND (Radiation therapy >4 weeks prior to the initiation of study treatment the initiation of study treatment) AND (adjuvant therapy) AND (age >18 years) AND (aspartate aminotransferase (AST)) AND (chemo) AND (creatinine clearance >40 mL/min Cockcroft-Gault method) AND (early-stage lung cancer at least 12 months have elapsed from that treatment) AND (liver involvement. ≤5 times the upper limit of normal) AND (metastases disseminated) AND (mixed non-small cell histologies) AND (non-small cell lung cancer locally advanced) AND (palliative radiation therapy symptomatic) AND (pericardial effusion) AND (platelets >100,000/microL) AND (pleural effusion) AND (radiation) AND (radiotherapy previous) AND (small cell anaplastic elements) AND (squamous carcinoma predominant histology) AND (squamous cell bronchogenic carcinoma) AND (squamous cell lung cancer stage IV) AND (stage IV Newly Newly diagnosed) AND (symptomatic metastases >14 days prior the initiation of the study treatment the initiation of the study treatment) AND (treatment that treatment) AND NOT (liver involvement))"}
{"candidate_id": "LLM02462", "doc_id": "NCT02509091_inc", "case_bucket": "other", "source_criterion": "Age=18 years and =80 years; Patients with non-cystic fibrosis bronchiectasis diagnosed by high-resolution CT; Are sensitive to amikacin; Acute exacerbation of bronchiectasis; Capable of the completion of bronchoscopy, alveolar lavage, pulmonary function testing etc; Willing to join in and sign the informed consent form.", "candidate_expression": "((Acute exacerbation of bronchiectasis) AND (Age =18 years and =80 years) AND (Capable of the completion of bronchoscopy, alveolar lavage, pulmonary function testing etc) AND (Willing to join in and sign the informed consent form) AND (amikacin) AND (high-resolution CT) AND (non-cystic fibrosis bronchiectasis) AND (sensitive))"}
{"candidate_id": "LLM02463", "doc_id": "NCT03228017_inc", "case_bucket": "or", "source_criterion": "Subjects with a history of moderate to severe psoriatic disease Group 2: Healthy subjects without known psoriatic disease or cardiovascular disease", "candidate_expression": "((Healthy) AND (history) AND (psoriatic disease) AND (without) AND ((moderate) OR (severe)) AND ((cardiovascular disease) OR (psoriatic disease)))"}
{"candidate_id": "LLM02464", "doc_id": "NCT02420015_exc", "case_bucket": "other", "source_criterion": "Have a history of myocardial infarction in the past 6 months Have a contraindication to NRT with no medical clearance from the primary care provider or study physician Use and unwillingness to stop use of other forms of nicotine such as cigars, pipes, or chewing tobacco Are pregnant Meet criteria for a current manic episode based on structured clinical interview Are currently enrolled in another smoking cessation trial Are currently imprisoned or in psychiatric hospitalization", "candidate_expression": "((Are currently enrolled in another smoking cessation trial) AND (NRT) AND (Use and unwillingness to stop use of other forms of nicotine such as cigars, pipes, or chewing tobacco) AND (contraindication) AND (imprisoned) AND (manic episode) AND (myocardial infarction i) AND (past 6 months) AND (pregnant) AND (psychiatric hospitalization))"}
{"candidate_id": "LLM02465", "doc_id": "NCT02550769_inc", "case_bucket": "or", "source_criterion": "Age over 18 years Patients with rectal cancer stage: cT1-2-3, cN0-1, cM0. Tumor equal or below 10 cm from the anal verge, candidates to (ETM) low anterior resection and anastomosis, with or without preoperative chemo-radiotherapy. Adenocarcinoma of low or moderate differentiation ASA I, II, III.", "candidate_expression": "((0) AND (0-1) AND (1-2-3) AND (ASA) AND (Adenocarcinoma) AND (Age) AND (I, II, III) AND (Tumor) AND (candidates) AND (chemo-radiotherapy) AND (equal or below 10 cm from the anal verge) AND (low or moderate differentiation) AND (over 18 years) AND (preoperative) AND (rectal cancer) AND (stage) AND ((low anterior anastomosis) OR (low anterior resection)) AND ((cM) OR (cN) OR (cT)))"}
{"candidate_id": "LLM02466", "doc_id": "NCT03252249_exc", "case_bucket": "or", "source_criterion": "Clear indication for specific duration of dual anti-platelet therapy Type 2 myocardial infarction Contraindication to aspirin or P2Y12 receptor antagonist Non-resident of Scotland Previous recruitment into the trial Inability or unwilling to give informed consent", "candidate_expression": "((Clear indication for specific duration) AND (Contraindication) AND (Inability or unwilling to give informed consent) AND (Non-resident) AND (P2Y12 receptor antagonist) AND (Previous recruitment into the trial) AND (Scotland) AND (Type 2 myocardial infarction) AND (aspirin) AND (dual anti-platelet therapy))"}
{"candidate_id": "LLM02467", "doc_id": "NCT03044093_inc", "case_bucket": "other", "source_criterion": "healthy no allergy known to these drugs second trimester abortion", "candidate_expression": "((abortion second trimester) AND (healthy) AND (these drugs) AND NOT (allergy))"}
{"candidate_id": "LLM02468", "doc_id": "NCT03209011_exc", "case_bucket": "or", "source_criterion": "Active consumption of alcohol and/or drugs Co-infection with human immunodeficiency virus, hepatitis C virus, or hepatitis D virus History of autoimmune hepatitis Psychiatric disease Evidence of neoplastic diseases of the liver", "candidate_expression": "((Active) AND (Evidence of) AND (History) AND (Psychiatric disease) AND (autoimmune hepatitis) AND (consumption of alcohol) AND (drugs consumption of) AND (hepatitis C virus) AND (hepatitis D virus) AND (human immunodeficiency virus) AND (liver) AND (neoplastic diseases))"}
{"candidate_id": "LLM02469", "doc_id": "NCT01349413_inc", "case_bucket": "other", "source_criterion": "Patients with functional dyspepsia that fulfill Rome III criteria with inadequate relief of dyspeptic symptoms Age >18 Provision of written consent", "candidate_expression": "((>18) AND (Age) AND (Provision of written consent) AND (Rome III criteria) AND (dyspeptic symptoms) AND (functional dyspepsia) AND (inadequate relief))"}
{"candidate_id": "LLM02470", "doc_id": "NCT03208998_inc", "case_bucket": "or", "source_criterion": "HBsAg and HBeAg positive for more than 6 months, HBV DNA detectable with ALT level abnormal lasted for three months and at least time190 IU/L or liver puncture biopsy demonstrated apparent inflammation, never treated before enrolled.", "candidate_expression": "((190 IU/L) AND (ALT level) AND (HBV DNA detectable) AND (HBeAg positive) AND (HBsAg positive) AND (abnormal) AND (at least time) AND (before enrolled) AND (enrolled) AND (for more than 6 months) AND (inflammation) AND (lasted for three months) AND (liver puncture biopsy) AND (never) AND (treated))"}
{"candidate_id": "LLM02471", "doc_id": "NCT03372304_inc", "case_bucket": "other", "source_criterion": "American Society of Anesthesiologists Classification I-III Normal cognitive function in order to sign written, informed consent and to understand trial protocol Agreement to the trial protocol, including the randomized manner", "candidate_expression": "((Agreement to the trial protocol, including the randomized manner) AND (American Society of Anesthesiologists Classification I-III) AND (ormal cognitive function in order to sign written, informed consent and to understand trial protoco))"}
{"candidate_id": "LLM02472", "doc_id": "NCT02570347_inc", "case_bucket": "other", "source_criterion": "Age 18-65 years History of snake bite with features of local envenomation with/without systemic features Less than 24 hours since bite, AND No prior antibiotic treatment", "candidate_expression": "((18-65 years) AND (Age) AND (Less than 24 hours since bite) AND (No) AND (antibiotic treatment) AND (bite) AND (features of) AND (local envenomation) AND (prior) AND (snake bite) AND (systemic features))"}
{"candidate_id": "LLM02473", "doc_id": "NCT02322203_exc", "case_bucket": "or", "source_criterion": "Subjects taking any lipid modification therapy, including but not limited to statins, fibrates and bile acid sequestrants. Subjects taking fish oil or any other supplements, which in the investigator s opinion may interfere with the study. Subjects with acute liver disease or active peptic ulcer disease. Subjects with elevated uric acid levels greater than 10 mg/dL or gout Pregnancy or women currently breastfeeding. Female subjects taking hormonal contraceptives or hormone replacement therapy may be included in this study only if they have been on a stable dose for at least 3 months. BMI less than 18.5 Subjects with weight that varies greater than 20% over the past 3 months. Subjects taking the following medications for at least six weeks, which may interfere with the study, will be excluded: BAS, antibiotics, anticoagulants, anticonvulsants, antiarrhythmic, Cyclosporine, Mycophenolate and Synthroid. Subjects with chronic diarrhea, gastric bypass or lap band procedures, ostomies, bowel motility problems, or other conditions that could affect intestinal fat absorption. Subjects initiating new medications or patients on multiple medications may also be excluded. Inability to swallow capsules Patients with a history of type I or type II diabetes or HbA1c greater than 6.5%. Volunteers may also be excluded, if in the opinion of the study investigators, they have some other condition or disorder that may adversely affect the outcome of the study or the safety of the volunteer.", "candidate_expression": "((BAS) AND (BMI less than 18.5) AND (Cyclosporine) AND (Female) AND (HbA1c greater than 6.5%) AND (Inability to swallow capsules) AND (Mycophenolate) AND (Pregnancy) AND (Subjects taking fish oil or any other supplements, which in the investigator s opinion may interfere with the study.) AND (Synthroid) AND (Volunteers may also be excluded, if in the opinion of the study investigators, they have some other condition or disorder that may adversely affect the outcome of the study or the safety of the volunteer.) AND (acute liver disease) AND (antiarrhythmic) AND (antibiotics) AND (anticoagulants) AND (anticonvulsants) AND (bile acid sequestrants) AND (bowel motility problems) AND (breastfeeding) AND (chronic diarrhea) AND (conditions that could affect intestinal fat absorption) AND (fibrates) AND (fish oil) AND (gastric bypass) AND (gout) AND (hormonal contraceptives) AND (hormone replacement therapy) AND (lap band procedures) AND (lipid modification therapy) AND (ostomies) AND (peptic ulcer disease active) AND (statins) AND (type I diabetes) AND (type II diabetes) AND (uric acid levels elevated greater than 10 mg/dL) AND (weight varies greater than 20%) AND (women))"}
{"candidate_id": "LLM02474", "doc_id": "NCT03624517_exc", "case_bucket": "or", "source_criterion": "Known upper gastrointestinal malignancy Bleeding from gastric varices, with or without esophageal varices Use of any other endoscopic method to stop GI bleeding beyond endoscopic band ligation Variceal bleeding in the last 90 days History of transjugular, intrahepatic, portosystemic shunt (TIPS) or vascular decompression surgery Pregnant females Incarcerated individuals Myocardial infarct, cerebrovascular accident, sepsis, respiratory failure, or severe intercurrent illness within the previous 6 weeks Non-cirrhotic portal hypertension causing esophageal varices Known or suspected allergy to octreotide", "candidate_expression": "((Bleeding) AND (GI bleeding) AND (Incarcerated individuals) AND (Myocardial infarct) AND (Non-cirrhotic portal hypertension) AND (Pregnant) AND (Variceal bleeding in the last 90 days) AND (allergy) AND (cerebrovascular accident) AND (endoscopic method) AND (esophageal varices) AND (esophageal varices Known suspected) AND (females) AND (gastric varices) AND (intercurrent illness severe) AND (octreotide) AND (respiratory failure) AND (sepsis) AND (transjugular, intrahepatic, portosystemic shunt (TIPS)) AND (upper gastrointestinal malignancy) AND (vascular decompression surgery) AND NOT (endoscopic band ligation))"}
{"candidate_id": "LLM02475", "doc_id": "NCT02701777_inc", "case_bucket": "or", "source_criterion": "Male and females between ages 18-85 years Right handed Able to complete precision grips with both hands Able to complete full wrist flexion-extension bilaterally Able to walk unassisted Able to complete full ankle flexion-extension bilaterally Male and females between ages 18-85 years SCI ( 2 months of injury) Spinal Cord injury at or above L5 The ability to produce a visible precision grip force with one hand Able to perform some small wrist flexion and extension The ability to perform a small visible contraction with dorsiflexion and hip flexor muscles No subjects will be excluded based on their race, religion, ethnicity, gender or HIV status. ASIA A,B,C, or D", "candidate_expression": "((ASIA A,B,C, or D) AND (Right handed) AND (SCI 2 months of injury) AND (Spinal Cord injury at or above L5) AND (ages between 18-85 years) AND (complete full ankle flexion-extension bilaterally Able to) AND (complete full wrist flexion-extension bilaterally Able to Able to) AND (complete precision grips with both hands Able to) AND (produce a visible precision grip force with one hand The ability to) AND (small visible contraction with dorsiflexion and hip flexor muscles The ability to) AND (small wrist flexion and extension Able to) AND (walk unassisted) AND ((Male) OR (females)))"}
```
