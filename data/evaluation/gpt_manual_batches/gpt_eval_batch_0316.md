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
{"candidate_id": "LLM07876", "doc_id": "NCT02979561_inc", "case_bucket": "or", "source_criterion": "Men and women aged > 18 years Angiographically confirmed acute massive pulmonary embolism with involvement of Central pulmonary arteries. endovascular mechanical thrombus fragmentation + thrombolytic therapy (using recombinant tissue activator of plasminogen), performed for treatment of the above-mentioned pulmonary embolism in less than 48 hours before randomization. The patient should be randomized no earlier than 24 hours after procedures endovascular mechanical thrombus fragmentation + thrombolytic therapy Written informed consent signed by patient.", "candidate_expression": "((Angiographically) AND (aged > 18 years) AND (endovascular mechanical thrombus fragmentation) AND (involvement of Central pulmonary arteries) AND (pulmonary embolism) AND (pulmonary embolism Angiographically confirmed acute massive) AND (recombinant tissue activator of plasminogen) AND (ritten informed consent signed by patient) AND (thrombolytic therapy) AND (treatment in less than 48 hours before randomization) AND ((Men) OR (women)))"}
{"candidate_id": "LLM07877", "doc_id": "NCT01803438_exc", "case_bucket": "or", "source_criterion": "Subject has documented typical atrial flutter. Subject has any history of successful or unsuccessful treatment of AF with class I or III antiarrhythmic or sotalol with the intention to prevent an AF recurrence. Patients pretreated with above AAD at maximum 48 hours with the intention to convert an AF episode are allowed. Subject had any previous left atrial ablation. Subject had any previous cardiac surgery, e.g. prosthetic valves. Subject has permanent pacemaker or defibrillator implant. Subject has 2° type II, 3° degree AV-block or left/right bundle branch block pattern. Subject has unstable angina pectoris. Subject has history of previous myocardial infarction or percutaneous intervention during the last three months. Subject has symptomatic carotid stenosis. Subject has chronic obstructive pulmonary disease with detected pulmonary hypertension or any other evidence of significant lung disease. Subject has any contraindication for oral anticoagulation. Subject has any history of previous transient ischemic attack or stroke. Subject has known intra-cardiac thrombus formation. Subject has any significant congenital heart defect corrected or not (except for patent foramen ovale that is allowed). Subject has evidence of congestive heart failure (NYHA class II, III or IV) in sinus rhythm. Subject has hypertrophic cardiomyopathy. Subject has abnormal long or short QT interval, signs of Brugada syndrome, known inheriting ion channel disease on the family, arrhythmogenic right ventricular dysplasia. Subject has sarcoidosis. Subject has pulmonary vein stent. Subject has myxoma. Exclusion criteria based on laboratory abnormalities Subject has thrombocytosis (platelet count > 600,000 / µl) or thrombocytopenia (platelet count <100,000 / µl). Subject has any untreated or uncontrolled hyperthyroidism or hypothyroidism. Subject has renal dysfunction with glomerular filtration rate < 60 ml / min. Subject has known cryoglobulinaemia. General exclusion criteria Subject has a reversible causes for AF like hyperthyroidism and alcoholism. Subject is a pregnant woman or woman of childbearing potential not on adequate birth control: only woman with a highly effective method of contraception [oral contraception or intra-uterine device] (who must have a negative pregnancy test within 1 week of the start of the therapy) or sterile woman can be enrolled. Subject is a breastfeeding woman. Subject has an active systemic infection. Subject is employed by Medtronic or by the department of any of the investigators or is a close relative of any of the investigators. Subject is unwilling or unable to comply fully with study procedures and follow-up due to any disease condition, which can raise doubt about compliance and influencing the study outcome especially any kind of cancer, severe bleeding in history or a suspected pro-coagulant state. Legal incapacity or evidence that a subject cannot understand the purpose and risks of the study or inability to comply fully with study procedures and follow up. Subject has a life expectancy of = 1 year. Subject is currently enrolled or planning to participate in a potentially confounding drug or device trial during the course of this study. Co-enrollment in concurrent trials is only allowed when documented pre-approval is obtained from the Medtronic study manager.", "candidate_expression": "((< 60 ml / min) AND (<100,000 / µl) AND (= 1 year) AND (> 600,000 / µl) AND (AF) AND (NYHA class) AND (Subject is a breastfeeding woman) AND (Subject is a pregnant woman or woman of childbearing potential not on adequate birth control: only woman with a highly effective method of contraception [oral contraception or intra-uterine device] (who must have a negative pregnancy test within 1 week of the start of the therapy) or sterile woman can be enrolled) AND (Subject is currently enrolled or planning to participate in a potentially confounding drug or device trial during the course of this study. Co-enrollment in concurrent trials is only allowed when documented pre-approval is obtained from the Medtronic study manager) AND (Subject is employed by Medtronic or by the department of any of the investigators or is a close relative of any of the investigators) AND (Subject is unwilling or unable to comply fully with study procedures and follow-up due to any disease condition, which can raise doubt about compliance and influencing the study outcome especially any kind of cancer, severe bleeding in history or a suspected pro-coagulant state) AND (abnormal) AND (active) AND (arrhythmogenic) AND (atrial ablation) AND (atrial flutter) AND (cardiac surgery) AND (carotid stenosis) AND (chronic obstructive pulmonary disease) AND (congenital heart defect) AND (congestive heart failure) AND (contraindication) AND (cryoglobulinaemia) AND (egal incapacity or evidence that a subject cannot understand the purpose and risks of the study or inability to comply fully with study procedures and follow up) AND (except) AND (glomerular filtration rate) AND (hypertrophic cardiomyopathy) AND (inheriting ion channel disease) AND (intra-cardiac thrombus) AND (last three months) AND (left) AND (life expectancy) AND (myxoma) AND (oral anticoagulation) AND (patent foramen ovale) AND (platelet count) AND (prosthetic valves) AND (pulmonary vein stent) AND (renal dysfunction) AND (sarcoidosis) AND (significant) AND (sinus rhythm) AND (symptomatic) AND (systemic infection) AND (unstable angina pectoris) AND ((defibrillator implant) OR (permanent pacemaker)) AND ((2° type II AV-block) OR (3° degree AV-block) OR (left bundle branch block) OR (right bundle branch block)) AND ((myocardial infarction) OR (percutaneous intervention)) AND ((lung disease) OR (pulmonary hypertension)) AND ((stroke) OR (transient ischemic attack)) AND ((antiarrhythmic) OR (sotalol)) AND ((II) OR (III) OR (IV)) AND ((long) OR (short)) AND ((Brugada syndrome) OR (QT interval) OR (inheriting ion channel disease on the family) OR (right ventricular dysplasia)) AND ((class I) OR (class III)) AND ((thrombocytopenia) OR (thrombocytosis)) AND ((hyperthyroidism) OR (hypothyroidism)) AND ((uncontrolled) OR (untreated)) AND ((alcoholism) OR (hyperthyroidism)))"}
{"candidate_id": "LLM07878", "doc_id": "NCT01051414_inc", "case_bucket": "other", "source_criterion": "Subjects chronically infected with HCV Genotype 1 HCV RNA viral load of ≥ 10*5* IU/mL (100,000 IU/mL) at screening", "candidate_expression": "((100,000 IU/mL) AND (Genotype 1) AND (HCV) AND (HCV RNA viral load) AND (at screening) AND (chronically) AND (screening) AND (≥ 10*5* IU/mL))"}
{"candidate_id": "LLM07879", "doc_id": "NCT02531724_inc", "case_bucket": "other", "source_criterion": "Patients in the cardiothoracic intensive care after cardiac surgery with cardiopulmonary bypass Acute kidney injury, defined as increase in S-creatinine 50% or 27 mol/L Normal S-creatinine before surgery", "candidate_expression": "((Acute kidney injury) AND (S-creatinine Normal before surgery) AND (cardiac surgery) AND (cardiopulmonary bypass) AND (cardiothoracic intensive care after cardiac surgery with cardiopulmonary bypass) AND (increase in S-creatinine 50% or 27 mol/L) AND (surgery))"}
{"candidate_id": "LLM07880", "doc_id": "NCT02687178_exc", "case_bucket": "other", "source_criterion": "diabetes mellitus secondary hypertension pregnancy", "candidate_expression": "((diabetes mellitus) AND (pregnancy) AND (secondary hypertension))"}
{"candidate_id": "LLM07881", "doc_id": "NCT02525991_exc", "case_bucket": "or", "source_criterion": "Patient diagnosed with dementia. Patients with serious and unstable illnesses including current hepatic, renal, gastroenterologic, respiratory, cardiovascular (including ischemic heart disease and congestive heart failure), endocrinologic, neurologic (including stroke, transient ischemic attack, subarachnoidal bleeding, brain tumor, encephalopathy, and meningitis). Patients with a history of allergic reactions to loxapine or amoxapine Patients who have received an investigational drug within 30 days prior to the current agitation episode must be excluded. Patients who are considered by the investigator, for any reason, to be unable to self-administer the inhalation device.", "candidate_expression": "((Patients who are considered by the investigator, for any reason, to be unable to self-administer the inhalation device) AND (Patients who have received an investigational drug within 30 days prior to the current agitation episode must be excluded) AND (allergic reactions) AND (amoxapine) AND (brain tumor) AND (cardiovascular) AND (congestive heart failure) AND (dementia serious unstable) AND (encephalopathy) AND (endocrinologic) AND (gastroenterologic) AND (hepatic) AND (ischemic heart disease) AND (loxapine) AND (meningitis) AND (neurologic) AND (renal) AND (respiratory) AND (stroke) AND (subarachnoidal bleeding) AND (transient ischemic attack))"}
{"candidate_id": "LLM07882", "doc_id": "NCT02462590_inc", "case_bucket": "other", "source_criterion": "Adults = 18 years of age Admitted to any ICU and receiving invasive mechanical ventilation Anticipated ventilation of =72 hours at the time of screening, as per the ICU physician.", "candidate_expression": "((= 18 years) AND (=72 hours) AND (Adults) AND (Anticipated) AND (ICU) AND (age) AND (invasive) AND (mechanical ventilation) AND (ventilation))"}
{"candidate_id": "LLM07883", "doc_id": "NCT02219880_exc", "case_bucket": "other", "source_criterion": "NA", "candidate_expression": "(EMPTY)"}
{"candidate_id": "LLM07884", "doc_id": "NCT03221231_exc", "case_bucket": "or", "source_criterion": "Currently dependent on any substance other than cannabis, alcohol or nicotine; History of any major internal disease (including diabetes, cardiovascular disease, lung disease, liver or kidney disease); An active or any history of neurological disorder, including but not limited to seizure disorder, epilepsy, stroke, neurological disease, cognitive impairment, head trauma with prolonged loss of consciousness (>10 minutes), or migraine headaches; An active or a history of a psychiatric disorder including, but not limited to, depression, schizophrenia, bipolar disorder, anxiety, or other psychiatric disorders; Asthma; Known hypersensitivity or allergy to n-acetylcysteine, or receiving chronic therapy with medication that could interact adversely with n-acetylcysteine within 30 days prior to randomization (i.e., nitroglycerin, ACE inhibitors or antihypertensive drugs, anti-coagulants); Exclusion criteria for MRI: having metal in the body and/or having claustrophobia", "candidate_expression": "((Asthma) AND (Exclusion criteria for MRI) AND (chronic therapy within 30 days prior to randomization) AND (dependent) AND (major internal disease) AND (n-acetylcysteine) AND (neurological disorder) AND (prolonged loss of consciousness >10 minutes) AND (psychiatric disorder) AND (substance) AND ((cardiovascular disease) OR (diabetes) OR (kidney disease) OR (liver disease) OR (lung disease)) AND ((active) OR (history)) AND ((cognitive impairment) OR (epilepsy) OR (head trauma) OR (migraine headaches) OR (neurological disease) OR (seizure disorder) OR (stroke)) AND ((anxiety) OR (bipolar disorder) OR (depression) OR (psychiatric disorders other) OR (schizophrenia)) AND ((allergy) OR (hypersensitivity)) AND ((ACE inhibitors) OR (anti-coagulants) OR (antihypertensive drugs) OR (nitroglycerin)) AND ((alcohol) OR (cannabis) OR (nicotine)) AND ((claustrophobia) OR (metal in the body)))"}
{"candidate_id": "LLM07885", "doc_id": "NCT03019562_inc", "case_bucket": "other", "source_criterion": "19-65 years of age ASA physical status classification I or II Scheduled for total hip replacement surgery", "candidate_expression": "((ASA physical status classification I or II) AND (age 19-65 years) AND (total hip replacement surger Scheduled for))"}
{"candidate_id": "LLM07886", "doc_id": "NCT03506750_inc", "case_bucket": "or", "source_criterion": "18 years or older Type 1 or 2 diabetes PDR patients requiring surgical intervention for complications of vitreous hemorrhage or traction retinal detachment and pre-operative IVC treatment. women postmenopausal for 12 months before the study, surgically sterile, or not pregnant and on effective contraception.", "candidate_expression": "((IVC treatment pre-operative) AND (PDR) AND (Type 1 diabetes) AND (Type 2 diabetes) AND (older 18 years or older) AND (surgical intervention requiring) AND (traction retinal detachment) AND (vitreous hemorrhage) AND (women postmenopausal for 12 months before the study, surgically sterile, or not pregnant and on effective contraception.))"}
{"candidate_id": "LLM07887", "doc_id": "NCT02845427_exc", "case_bucket": "other", "source_criterion": "Revision cases Uncontrolled bleeding tendency (prothrombin conc. Less than 70%) History of deep venous thrombosis Sever liver impairment (liver failure) Sever renal impairment (S. creatinine more than 3)", "candidate_expression": "((History) AND (Less than 70%) AND (Revision cases) AND (Sever) AND (Uncontrolled) AND (bleeding tendency) AND (creatinine) AND (deep venous thrombosis) AND (liver failure) AND (liver impairment) AND (more than 3) AND (prothrombin) AND (renal impairment))"}
{"candidate_id": "LLM07888", "doc_id": "NCT02612181_inc", "case_bucket": "other", "source_criterion": "Septic shock patients despite early goal directed therapy Agree to participate this study", "candidate_expression": "((Agree to participate this study) AND (Septic shock) AND (early goal directed therapy))"}
{"candidate_id": "LLM07889", "doc_id": "NCT01614041_inc", "case_bucket": "or", "source_criterion": "18-65 years old Male or female Diagnosed with GAD according to DSM-IV HAMA score=17 Provide with written informed consent Agree to be washed-out for two weeks if receiving SSRI, SNRI or NASA.", "candidate_expression": "((DSM-IV) AND (GAD) AND (HAMA score =17) AND (Provide with written informed consent) AND (washed-out for two weeks) AND (years old 18-65) AND ((NASA) OR (SNRI) OR (SSRI)) AND ((Male) OR (female)))"}
{"candidate_id": "LLM07890", "doc_id": "NCT03382106_inc", "case_bucket": "other", "source_criterion": "Between the age of 25 to 65 at baseline Be willing to participate in a smoking cessation program Be willing to attend all clinic visits Must be currently smoking at least ½ pack/day at baseline (confirmed with cotinine level and CO Smokerlyzer >5 pack-year history of smoking Global Initiative for Chronic Obstructive Lung Disease (GOLD) 0: FEV1=0.80 and FEV1/FVC>0.70 Forced Expiratory Volume in 1 second (FEV1), Forced Vital Capacity (FVC) GOLD 1: FEV1=0.80 and FEV1/FVC < 0.70 GOLD 2: 0.50=FEV1<0.80 and FEV1/FVC < 0.70 Be willing to abstain from using any nicotine patches, e-cigarettes, or marijuana for the duration of the study.", "candidate_expression": "((CO Smokerlyzer) AND (FEV1 0.50= <0.80) AND (FEV1 =0.80) AND (FEV1/FVC < 0.70) AND (FEV1/FVC >0.70) AND (GOLD 1) AND (GOLD 2) AND (Global Initiative for Chronic Obstructive Lung Disease (GOLD) 0) AND (age Between 25 to 65 at baseline) AND (cotinine level) AND (pack-year >5) AND (pack/day at least ½) AND (smoking) AND (smoking at baseline) AND (smoking cessation program willing to participate))"}
{"candidate_id": "LLM07891", "doc_id": "NCT03387059_exc", "case_bucket": "or", "source_criterion": "Clinically significant systemic disease (such as diabetes, metabolic syndrome, immunological diseases, diagnosed thrombophilia, porphyria, or any other medical condition requiring the use of low-molecular weight heparin therapy) Polycystic ovary syndrome (PCOS) according to Rotterdam Consensus Criteria (European Society of Human Reproduction and Embryology [ESHRE]/American Society for Reproductive Medicine [ASRM], 2003) Poor ovarian response (POR) according to the European Society of Human Reproduction and Embryology (ESHRE) Criteria RIF (repeated implantation failure), defined as greater than or equals to (>=) 2 previous failed embryo transfers Endometriosis III-IV stage or adenomyosis Clinically significant findings on exam or ultrasound, such as salpingitis, hydrosalpynx or evidence of ovarian cysts Known hypersensitivity to any of the components of the solution Known hypersensitivity to vaginal progesterone or its excipients Other protocol defined exclusion criteria could apply", "candidate_expression": "((Endometriosis III-IV stage) AND (Polycystic ovary syndrome (PCOS) Rotterdam Consensus Criteria European Society of Human Reproduction and Embryology [ESHRE]/American Society for Reproductive Medicine [ASRM], 2003) AND (Poor ovarian response (POR) European Society of Human Reproduction and Embryology (ESHRE) Criteria) AND (RIF (repeated implantation failure)) AND (adenomyosis) AND (components of the solution) AND (diabetes) AND (diagnosed thrombophilia) AND (exam) AND (excipients) AND (hydrosalpynx) AND (hypersensitivity) AND (immunological diseases) AND (low-molecular weight heparin) AND (medical condition) AND (metabolic syndrome) AND (ovarian cysts evidence) AND (porphyria) AND (previous failed embryo transfers greater than or equals to (>=) 2) AND (salpingitis) AND (systemic disease Clinically significant) AND (ultrasound) AND (vaginal progesterone))"}
{"candidate_id": "LLM07892", "doc_id": "NCT02046395_inc", "case_bucket": "or", "source_criterion": "Type 2 Diabetes Hypertension Estimated glomerular filtration rate (eGFR) > 30 ml/min Use of Ace Inh and ARB for control of blood pressure who are willing to be placed on alternate drug(s) in the washout period for blood pressure control", "candidate_expression": "((> 30 ml/min) AND (ARB) AND (Ace Inh) AND (Estimated glomerular filtration rate (eGFR)) AND (Hypertension) AND (Type 2 Diabetes) AND (control of blood pressure) AND (willing to be placed on alternate drug(s) in the washout period for blood pressure control))"}
{"candidate_id": "LLM07893", "doc_id": "NCT02992028_inc", "case_bucket": "other", "source_criterion": "Rotator cuff tear patients undergoing arthroscopic rotator cuff tear", "candidate_expression": "((Rotator cuff tear) AND (arthroscopic rotator cuff tear))"}
{"candidate_id": "LLM07894", "doc_id": "NCT03013790_inc", "case_bucket": "other", "source_criterion": "Non-ventilated Patients over the age of 65", "candidate_expression": "((Non) AND (age) AND (over 65) AND (ventilated))"}
{"candidate_id": "LLM07895", "doc_id": "NCT02739295_exc", "case_bucket": "or", "source_criterion": "Toxic epidermal necrolysis with SCORTEN 6 or 7 at admission Hypercoagulable state Cardiac or peripheral arterial disease Active malignancy Myelodysplastic syndrome or hematological malignancy Fructose intolerance Pregnancy Patient refusal", "candidate_expression": "((6 or 7) AND (Active) AND (Fructose) AND (Fructose intolerance) AND (Hypercoagulable state) AND (Patient refusal) AND (Pregnancy) AND (SCORTEN) AND (Toxic epidermal necrolysis) AND (admission) AND (at admission) AND (malignancy) AND ((Myelodysplastic syndrome) OR (hematological malignancy)) AND ((disease Cardiac) OR (peripheral arterial disease)))"}
{"candidate_id": "LLM07896", "doc_id": "NCT02951754_exc", "case_bucket": "or", "source_criterion": "Contraindication for IR-MPH use Current stimulant treatment Evidence of a clinically significant neurological disease that might affect cognition (e.g., delirium, dementia, epilepsy, head trauma, and multiple sclerosis) Current or past history of psychosis Estimated intelligence quotient score lower than 70", "candidate_expression": "((Contraindication) AND (Estimated intelligence quotient score lower than 70) AND (IR-MPH) AND (neurological disease clinically significant might affect cognition) AND (psychosis history) AND (stimulant treatment Current) AND ((Current) OR (past)) AND ((delirium) OR (dementia) OR (epilepsy) OR (head trauma) OR (multiple sclerosis)))"}
{"candidate_id": "LLM07897", "doc_id": "NCT03164096_inc", "case_bucket": "other", "source_criterion": "adult female partner aged 18 to 40 years. scheduled for elective cesarean section.", "candidate_expression": "((18 to 40 years) AND (adult) AND (aged) AND (cesarean section) AND (elective) AND (female) AND (female partner) AND (scheduled for))"}
{"candidate_id": "LLM07898", "doc_id": "NCT02667730_exc", "case_bucket": "or", "source_criterion": "Diagnosis of ankle fracture or ligament rupture Has planned release from the Canadian Armed Forces within one year; Documented restrictions on military duties Has known intolerance or documented adverse reaction to acetaminophen or naproxen or celecoxib Documented history of liver or kidney problems pregnant or breastfeeding", "candidate_expression": "((release from the Canadian Armed Forces within one year) AND (restrictions on military duties) AND ((ankle fracture) OR (ligament rupture)) AND ((kidney problems) OR (liver problems)) AND ((breastfeeding) OR (pregnant)) AND ((acetaminophen) OR (celecoxib) OR (naproxen)) AND ((adverse reaction) OR (intolerance)))"}
{"candidate_id": "LLM07899", "doc_id": "NCT02735902_inc", "case_bucket": "other", "source_criterion": "The patient or his/her representative must have given free and informed consent and signed the consent The patient must be insured or beneficiary of a health insurance plan The patient is available for 12 months of follow-up The patient underwent a successful transcutaneous implant procedure for an aortic valve within the past 24 hours The patient was receiving anti-vitamin K (AVK) treatment before percutaneous implantation of the aortic valve", "candidate_expression": "((AVK) AND (The patient is available for 12 months of follow-up) AND (The patient or his/her representative must have given free and informed consent and signed the consent) AND (anti-vitamin K before percutaneous implantation of the aortic valve) AND (aortic valve) AND (transcutaneous implant procedure past 24 hours))"}
{"candidate_id": "LLM07900", "doc_id": "NCT02445339_exc", "case_bucket": "or", "source_criterion": "Active opioid dependence Acute or chronic pain requiring opioid treatment Acute liver injury (liver aminotransferase concentrations >5 times the upper limit of normal) Health condition considered unsafe for inclusion (at discretion of PI and/or attending physician) Lack of capacity or willingness to consent Currently prescribed pharmacotherapy for alcohol dependence (not including treatment of acute alcohol withdrawal syndrome) Previous significant adverse reaction to naltrexone or diluent Pregnant, nursing, or not using effective methods of birth control Prisoners (as defined by Office of Human Research Protection) at the time of enrollment ARE NOT ELIGIBLE for study entry. However, subjects who become prisoners after being enrolled will be included and not be withdrawn from the study. Patients on parole or probation are eligible for enrollment.", "candidate_expression": "((Acute liver injury) AND (Health condition considered unsafe for inclusion) AND (Prisoners Office of Human Research Protection at the time of enrollment) AND (acute alcohol withdrawal syndrome) AND (adverse reaction Previous significant) AND (alcohol dependence) AND (liver aminotransferase concentrations >5 times the upper limit of normal) AND (opioid dependence Active) AND (opioid treatment) AND (pain) AND (pharmacotherapy Currently) AND NOT (treatment) AND ((capacity to consent) OR (willingness to consent)) AND ((diluent) OR (naltrexone)) AND ((Acute) OR (chronic)) AND ((Pregnant) OR (nursing) OR NOT (birth control effective methods)))"}
```
