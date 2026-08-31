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
{"candidate_id": "LLM04776", "doc_id": "NCT02650388_exc", "case_bucket": "other", "source_criterion": "Died before TAVI Not willing to participate", "candidate_expression": "((Died) AND (Not willing to participate) AND (before TAVI))"}
{"candidate_id": "LLM04777", "doc_id": "NCT02964715_inc", "case_bucket": "or", "source_criterion": "biopsy proven NASH Type 2 DM HbA1c :>6.5% BMI < 45kg/m2 Any anti-diabetic agent except SGLT2 inhibitors, TZDs(thiazolidinediones), DPP4(Dipeptidyl peptidase4) inhibitors and GLP1 RAs(Glucagon-like Peptide 1-Receptor Agonists)", "candidate_expression": "((< 45kg/m2) AND (>6.5%) AND (BMI) AND (DPP4 inhibitors) AND (Dipeptidyl peptidase4 inhibitors) AND (GLP1 RAs) AND (Glucagon-like Peptide 1-Receptor Agonists) AND (HbA1c) AND (NASH) AND (SGLT2 inhibitors) AND (TZDs) AND (Type 2 DM) AND (anti-diabetic agent) AND (biopsy) AND (except) AND (thiazolidinediones))"}
{"candidate_id": "LLM04778", "doc_id": "NCT02511574_exc", "case_bucket": "other", "source_criterion": "no confirmation of the gestational age ruptured membranes painful regular uterine contractions major fetal abnormalities", "candidate_expression": "((fetal abnormalities major) AND (painful regular uterine contractions) AND (ruptured membranes) AND NOT (gestational age))"}
{"candidate_id": "LLM04779", "doc_id": "NCT03250507_exc", "case_bucket": "or", "source_criterion": "Patient with a chronic pain condition, major unexpected surgical complication, unexpected prolonged intubation, patient refusal, local anesthetic allergy, any contraindication to regional anesthesia, greater than 2 attempts by resident and greater than 1 attempt by staff anesthesiologist for TAP block.", "candidate_expression": "((TAP block) AND (allergy) AND (anesthesiologist) AND (chronic pain condition) AND (contraindication) AND (greater than 1) AND (greater than 2) AND (intubation) AND (local anesthetic) AND (major) AND (patient refusal) AND (prolonged) AND (regional anesthesia) AND (resident) AND (unexpected) AND (unexpected surgical complication))"}
{"candidate_id": "LLM04780", "doc_id": "NCT03151603_exc", "case_bucket": "or", "source_criterion": "signs of complicated UTI (e. g. temperature > 38°C, loin tenderness) conditions that may lead to complicated infections (i.e. renal diseases, patients with urinary catheter) pregnancy/ breastfeeding current self-medication with UU preparations e.g. z.B. Cystinol®, Uvalysat®, Arctuvan® antibiotic use in the last 7 days previous UTI in the past 2 weeks history of pyelonephritis contraindications for trial drugs serious diseases inability to understand trial Information current participation in another clinical trial or participation in another clinical trial within the last 4 weeks", "candidate_expression": "((Arctuvan®) AND (UTI past 2 weeks) AND (UU preparations self-medication) AND (Uvalysat®) AND (antibiotic last 7 days) AND (complicated UTI) AND (complicated infections) AND (conditions) AND (diseases serious) AND (drugs contraindications for trial) AND (inability to understand trial Information) AND (loin tenderness) AND (patients) AND (pregnancy/ breastfeeding) AND (pyelonephritis) AND (renal diseases) AND (temperature > 38°C) AND (urinary catheter) AND (z.B. Cystinol®))"}
{"candidate_id": "LLM04781", "doc_id": "NCT03228654_exc", "case_bucket": "or", "source_criterion": "Suspected or known gynecological malignancy. uterine size >12 weeks. Endometriosis Presence of adnexal mass. cervix flushed with the vagina. presence of significant scarring in the pelvic area from previous surgery.", "candidate_expression": "((Endometriosis) AND (adnexal mass) AND (cervix flushed with the vagina) AND (gynecological malignancy) AND (significant scarring pelvic area from previous surgery) AND (surgery previous) AND (uterine size >12 weeks) AND ((Suspected) OR (known)))"}
{"candidate_id": "LLM04782", "doc_id": "NCT03082573_inc", "case_bucket": "other", "source_criterion": "Fluent in reading and writing in English language. = 21 years of age at the time of participation.", "candidate_expression": "((= 21 years) AND (age) AND (at the time of participation) AND (participation))"}
{"candidate_id": "LLM04783", "doc_id": "NCT01803438_exc", "case_bucket": "or", "source_criterion": "Subject has documented typical atrial flutter. Subject has any history of successful or unsuccessful treatment of AF with class I or III antiarrhythmic or sotalol with the intention to prevent an AF recurrence. Patients pretreated with above AAD at maximum 48 hours with the intention to convert an AF episode are allowed. Subject had any previous left atrial ablation. Subject had any previous cardiac surgery, e.g. prosthetic valves. Subject has permanent pacemaker or defibrillator implant. Subject has 2° type II, 3° degree AV-block or left/right bundle branch block pattern. Subject has unstable angina pectoris. Subject has history of previous myocardial infarction or percutaneous intervention during the last three months. Subject has symptomatic carotid stenosis. Subject has chronic obstructive pulmonary disease with detected pulmonary hypertension or any other evidence of significant lung disease. Subject has any contraindication for oral anticoagulation. Subject has any history of previous transient ischemic attack or stroke. Subject has known intra-cardiac thrombus formation. Subject has any significant congenital heart defect corrected or not (except for patent foramen ovale that is allowed). Subject has evidence of congestive heart failure (NYHA class II, III or IV) in sinus rhythm. Subject has hypertrophic cardiomyopathy. Subject has abnormal long or short QT interval, signs of Brugada syndrome, known inheriting ion channel disease on the family, arrhythmogenic right ventricular dysplasia. Subject has sarcoidosis. Subject has pulmonary vein stent. Subject has myxoma. Exclusion criteria based on laboratory abnormalities Subject has thrombocytosis (platelet count > 600,000 / µl) or thrombocytopenia (platelet count <100,000 / µl). Subject has any untreated or uncontrolled hyperthyroidism or hypothyroidism. Subject has renal dysfunction with glomerular filtration rate < 60 ml / min. Subject has known cryoglobulinaemia. General exclusion criteria Subject has a reversible causes for AF like hyperthyroidism and alcoholism. Subject is a pregnant woman or woman of childbearing potential not on adequate birth control: only woman with a highly effective method of contraception [oral contraception or intra-uterine device] (who must have a negative pregnancy test within 1 week of the start of the therapy) or sterile woman can be enrolled. Subject is a breastfeeding woman. Subject has an active systemic infection. Subject is employed by Medtronic or by the department of any of the investigators or is a close relative of any of the investigators. Subject is unwilling or unable to comply fully with study procedures and follow-up due to any disease condition, which can raise doubt about compliance and influencing the study outcome especially any kind of cancer, severe bleeding in history or a suspected pro-coagulant state. Legal incapacity or evidence that a subject cannot understand the purpose and risks of the study or inability to comply fully with study procedures and follow up. Subject has a life expectancy of = 1 year. Subject is currently enrolled or planning to participate in a potentially confounding drug or device trial during the course of this study. Co-enrollment in concurrent trials is only allowed when documented pre-approval is obtained from the Medtronic study manager.", "candidate_expression": "((AF) AND (NYHA class) AND (Subject is a breastfeeding woman) AND (Subject is a pregnant woman or woman of childbearing potential not on adequate birth control: only woman with a highly effective method of contraception [oral contraception or intra-uterine device] (who must have a negative pregnancy test within 1 week of the start of the therapy) or sterile woman can be enrolled) AND (Subject is currently enrolled or planning to participate in a potentially confounding drug or device trial during the course of this study. Co-enrollment in concurrent trials is only allowed when documented pre-approval is obtained from the Medtronic study manager) AND (Subject is employed by Medtronic or by the department of any of the investigators or is a close relative of any of the investigators) AND (Subject is unwilling or unable to comply fully with study procedures and follow-up due to any disease condition, which can raise doubt about compliance and influencing the study outcome especially any kind of cancer, severe bleeding in history or a suspected pro-coagulant state) AND (atrial ablation left) AND (atrial flutter) AND (cardiac surgery) AND (carotid stenosis symptomatic) AND (chronic obstructive pulmonary disease) AND (congenital heart defect significant) AND (congestive heart failure) AND (contraindication) AND (cryoglobulinaemia) AND (egal incapacity or evidence that a subject cannot understand the purpose and risks of the study or inability to comply fully with study procedures and follow up) AND (glomerular filtration rate < 60 ml / min) AND (hypertrophic cardiomyopathy) AND (inheriting ion channel disease) AND (intra-cardiac thrombus) AND (life expectancy = 1 year) AND (myxoma) AND (oral anticoagulation) AND (platelet count <100,000 / µl) AND (platelet count > 600,000 / µl) AND (prosthetic valves) AND (pulmonary vein stent) AND (renal dysfunction) AND (sarcoidosis) AND (sinus rhythm) AND (systemic infection active) AND (unstable angina pectoris) AND NOT (patent foramen ovale) AND ((defibrillator implant) OR (permanent pacemaker)) AND ((2° type II AV-block) OR (3° degree AV-block) OR (left bundle branch block) OR (right bundle branch block)) AND ((myocardial infarction) OR (percutaneous intervention)) AND ((lung disease significant) OR (pulmonary hypertension)) AND ((stroke) OR (transient ischemic attack)) AND ((antiarrhythmic) OR (sotalol)) AND ((II) OR (III) OR (IV)) AND ((long) OR (short)) AND ((Brugada syndrome) OR (QT interval) OR (inheriting ion channel disease on the family) OR (right ventricular dysplasia arrhythmogenic)) AND ((class I) OR (class III)) AND ((thrombocytopenia) OR (thrombocytosis)) AND ((hyperthyroidism) OR (hypothyroidism)) AND ((uncontrolled) OR (untreated)) AND ((alcoholism) OR (hyperthyroidism)))"}
{"candidate_id": "LLM04784", "doc_id": "NCT02415257_inc", "case_bucket": "other", "source_criterion": "Vestibular schwannoma advised to surgical treatment No measurable remaining vestibular function", "candidate_expression": "((No) AND (Vestibular schwannoma) AND (advised) AND (remaining vestibular function) AND (surgical treatment))"}
{"candidate_id": "LLM04785", "doc_id": "NCT00679341_exc", "case_bucket": "or", "source_criterion": "History of any chemotherapy for MBC. An interval of < 6 months from the completion of cytotoxic chemotherapy in the neo-adjuvant or adjuvant setting until the time of metastatic diagnosis. Trastuzumab ≤ 21 days prior to randomization. Hormone therapy < 7 days prior to randomization. Current peripheral neuropathy of Grade ≥ 3. History of other malignancy within the last 5 years, except for appropriately treated carcinoma in situ of the cervix, non-melanoma skin carcinoma, Stage I uterine cancer, or other cancers with a similar outcome as those previously mentioned. Previous radiotherapy for the treatment of unresectable, locally advanced or metastatic breast cancer is not allowed if more than 25% of marrow-bearing bone has been irradiated or the last fraction of radiotherapy has been administered within approximately 3 weeks prior to randomization. Brain metastases that are untreated, symptomatic, or require therapy to control symptoms or any radiation, surgery, or other therapy to control symptoms from brain metastases within 2 months prior to randomization. History of exposure to the following cumulative doses of anthracyclines: Doxorubicin or liposomal doxorubicin > 500 mg/m^2; epirubicin > 900 mg/m^2; mitoxantrone > 120mg/m^2 and idarubicin > 90 mg/m^2. Current unstable angina. History of symptomatic congestive heart failure, or ventricular arrhythmia requiring treatment. History of myocardial infarction within 6 months prior to randomization. Left ventricular ejection fraction (LVEF) below 50% within approximately 28 days prior to randomization. History of decreased LVEF or symptomatic congestive heart failure (CHF) with previous adjuvant trastuzumab treatment. Cardiac troponin I ≥ 0.2 ng/mL within 28 days of randomization. Severe dyspnea at rest because of complications of advanced malignancy or requiring current continuous oxygen therapy. Current severe, uncontrolled systemic disease (eg, clinically significant cardiovascular, pulmonary, or metabolic disease; wound healing disorders; ulcers; or bone fractures). Major surgical procedure or significant traumatic injury within approximately 28 days prior to randomization or anticipation of the need for major surgery during the course of study treatment. Current pregnancy or lactation. History of receiving any investigational treatment within approximately 28 days prior to randomization. Current known infection with human immunodeficiency virus (HIV), active hepatitis B and/or hepatitis C virus. History of intolerance (including Grade 3-4 infusion reaction) or hypersensitivity to trastuzumab, murine proteins, or docetaxel. Known hypersensitivity to any of the study drugs, including the excipients, or any drugs formulated in polysorbate 80. Assessed by the investigator to be unable or unwilling to comply with the requirements of the protocol.", "candidate_expression": "((3-4) AND (< 6 months) AND (< 7 days prior to randomization) AND (> 120mg/m^2) AND (> 500 mg/m^2) AND (> 90 mg/m^2) AND (> 900 mg/m^2) AND (Brain metastases) AND (Cardiac troponin I) AND (Current) AND (Grade) AND (Grade ≥ 3) AND (History) AND (History of) AND (Hormone therapy) AND (I) AND (LVEF) AND (Left ventricular ejection fraction (LVEF)) AND (MBC) AND (Major) AND (Previous) AND (Severe) AND (Stage) AND (Trastuzumab) AND (adjuvant) AND (adjuvant setting) AND (advanced malignancy) AND (anthracyclines) AND (anticipation of the need) AND (appropriately treated) AND (below 50%) AND (brain metastases) AND (breast cancer) AND (chemotherapy) AND (clinically significant) AND (congestive heart failure (CHF)) AND (continuous oxygen therapy) AND (current) AND (cytotoxic chemotherapy) AND (decreased) AND (during the course of study treatment) AND (dyspnea) AND (epirubicin) AND (except for) AND (hypersensitivity) AND (idarubicin) AND (infusion reaction) AND (investigational treatment) AND (major surgery) AND (malignancy) AND (marrow-bearing bone irradiated) AND (metastatic diagnosis) AND (mitoxantrone) AND (more than 25%) AND (myocardial infarction) AND (neo-adjuvant setting) AND (other) AND (peripheral neuropathy) AND (previous) AND (radiotherapy) AND (randomization) AND (requiring treatment) AND (severe) AND (significant) AND (study treatment) AND (symptomatic) AND (systemic disease) AND (trastuzumab) AND (treated) AND (treatment) AND (uncontrolled) AND (unstable angina) AND (within 2 months prior to randomization) AND (within 28 days of randomization) AND (within 6 months prior to randomization) AND (within approximately 28 days prior to randomization) AND (within the last 5 years) AND (≤ 21 days prior to randomization) AND (≥ 0.2 ng/mL) AND (≥ 3) AND ((complications) OR (requiring current continuous oxygen therapy)) AND ((lactation) OR (pregnancy)) AND ((hepatitis B virus) OR (hepatitis C virus) OR (human immunodeficiency virus (HIV))) AND ((hypersensitivity) OR (intolerance)) AND ((docetaxel) OR (murine proteins) OR (trastuzumab)) AND ((cardiovascular disease) OR (metabolic disease) OR (pulmonary disease)) AND ((bone fractures) OR (ulcers) OR (wound healing disorders)) AND ((drugs formulated in polysorbate 80) OR (study drugs)) AND ((unable to comply with the requirements of the protocol) OR (unwilling to comply with the requirements of the protocol)) AND ((surgical procedure) OR (traumatic injury)) AND ((carcinoma in situ of the cervix) OR (non-melanoma skin carcinoma) OR (uterine cancer)) AND ((locally advanced) OR (metastatic) OR (unresectable)) AND ((require therapy) OR (symptomatic) OR (untreated)) AND ((other therapy to control symptoms) OR (radiation) OR (surgery)) AND ((Doxorubicin) OR (liposomal doxorubicin)) AND ((congestive heart failure) OR (ventricular arrhythmia)))"}
{"candidate_id": "LLM04786", "doc_id": "NCT02735577_exc", "case_bucket": "or", "source_criterion": "Risk of severe alcohol withdrawal (e.g. history of seizures or delirium tremens) Current Moderate or Severe Substance Use Disorder, other than Alcohol, Nicotine or Caffeine Use Disorders Lifetime history of Bipolar Disorder, Schizophrenia or Schizoaffective Disorder Any current psychiatric disorder, other than Alcohol Use Disorder, that, in the judgment of the investigator, will require treatment that will interfere with study participation. Current severe depression (HAM-D >24) or anxiety (HAM-A >24) Significant suicide or violence risk Currently taking any psychotropic medications Legally mandated to participate in treatment History of prior treatment with disulfiram Sufficiently socially unstable as to preclude participation (e.g. homeless) Contraindications to disulfiram treatment (liver disease, kidney disease, cardiac disease, seizure disorder, hypothyroidism, diabetes mellitus, pregnancy or lactation, allergy to disulfiram or thiuran derivatives) Neurological or medical conditions that would interfere with MRI scanning (e.g. history of stroke, seizure, brain tumor, brain infection, traumatic brain injury, multiple sclerosis, dementia, metal device in body, pregnancy, claustrophobia, color blindness, severe hearing impairment, weight>300 lbs., wheelchair-bound) Currently taking medications containing alcohol, metronidazole, isoniazid, paraldehyde, phenytoin, warfarin, or theophylline. Significant alcohol withdrawal (CIWA>8) at screening, after confirming a blood alcohol level of zero.", "candidate_expression": "((>24) AND (>300 lbs.) AND (>8) AND (Alcohol Use Disorder) AND (CIWA) AND (Contraindications) AND (Current) AND (Currently) AND (HAM-A) AND (HAM-D) AND (History of prior treatment) AND (Lifetime history) AND (MRI scanning) AND (Risk of) AND (Significant) AND (Substance Use Disorder) AND (Sufficiently) AND (alcohol withdrawal) AND (at screening) AND (blood alcohol level) AND (brain infection) AND (brain tumor) AND (claustrophobia) AND (color blindness) AND (current) AND (dementia) AND (disulfiram) AND (hearing impairment) AND (history) AND (interfere) AND (metal device in body) AND (multiple sclerosis) AND (other than) AND (pregnancy) AND (psychiatric disorder) AND (psychotropic medications) AND (seizure) AND (severe) AND (socially unstable) AND (stroke) AND (traumatic brain injury) AND (weight) AND (wheelchair-bound) AND (zero) AND ((Alcohol Use Disorders) OR (Caffeine Use Disorders) OR (Nicotine Use Disorders)) AND ((Bipolar Disorder) OR (Schizoaffective Disorder) OR (Schizophrenia)) AND ((anxiety) OR (depression)) AND ((suicide risk) OR (violence risk)) AND ((allergy) OR (cardiac disease) OR (diabetes mellitus) OR (hypothyroidism) OR (kidney disease) OR (lactation) OR (liver disease) OR (pregnancy) OR (seizure disorder)) AND ((delirium tremens) OR (seizures)) AND ((disulfiram) OR (thiuran derivatives)) AND ((conditions Neurological) OR (medical conditions)) AND ((alcohol) OR (isoniazid) OR (metronidazole) OR (paraldehyde) OR (phenytoin) OR (theophylline) OR (warfarin)) AND ((Moderate) OR (Severe)))"}
{"candidate_id": "LLM04787", "doc_id": "NCT02954029_exc", "case_bucket": "or", "source_criterion": "congenital or acquired bleeding tendency platelet count <50,000/ µL hypersensitivity to shrimps, lobsters or beetles", "candidate_expression": "((<50,000/ µL) AND (acquired) AND (beetles) AND (bleeding tendency) AND (congenital) AND (hypersensitivity) AND (lobsters) AND (platelet count) AND (shrimps))"}
{"candidate_id": "LLM04788", "doc_id": "NCT02537899_inc", "case_bucket": "or", "source_criterion": "Male or female Age 18 to 65 years Diagnosed with spinal cord injury between 3 days and 4 weeks American Spinal Injury Association Impairment Scale A or B Informed consent for inclusion into the database is obtained", "candidate_expression": "((18 to 65 years) AND (A or B) AND (Age) AND (American Spinal Injury Association Impairment Scale) AND (Informed consent for inclusion into the database is obtained) AND (between 3 days and 4 weeks) AND (spinal cord injury) AND ((Male) OR (female)))"}
{"candidate_id": "LLM04789", "doc_id": "NCT02332291_inc", "case_bucket": "or", "source_criterion": "Age 60 years or older. Current diagnosis of major depressive disorder (DSM-IV-TR), single episode, recurrent or chronic, without psychotic features, as detected by MINI and clinical exam. Minimum MADRS score = 15. Mini-Mental State Exam = 24. Fluent in English.", "candidate_expression": "((Age 60 years or older) AND (DSM-IV-TR) AND (MADRS score Minimum = 15) AND (MINI) AND (Mini-Mental State Exam = 24) AND (clinical exam) AND (major depressive disorder) AND NOT (psychotic features) AND ((chronic) OR (recurrent) OR (single episode)))"}
{"candidate_id": "LLM04790", "doc_id": "NCT02933671_inc", "case_bucket": "other", "source_criterion": "English speaking between 18 and 75 years old American Society of Anesthesiologists (ASA) 1-3 patients undergoing primary total hip arthroplasty", "candidate_expression": "((1-3) AND (ASA) AND (American Society of Anesthesiologists) AND (between 18 and 75 years) AND (old) AND (primary total hip arthroplasty))"}
{"candidate_id": "LLM04791", "doc_id": "NCT02509949_exc", "case_bucket": "or", "source_criterion": "Patients with a history of drug abuse; preoperative history of schizophrenia, epilepsy, parkinsonism, use of cholinesterase inhibitor, inability to communicate in the preoperative period (coma, profound dementia, or language barrier).", "candidate_expression": "((cholinesterase inhibitor) AND (coma) AND (drug abuse history preoperative) AND (epilepsy) AND (history) AND (inability to communicate) AND (language barrier) AND (parkinsonism) AND (profound dementia) AND (schizophrenia))"}
{"candidate_id": "LLM04792", "doc_id": "NCT03067740_exc", "case_bucket": "or", "source_criterion": "The diagnosis of developmental delay, attention deficit disorder, chronic pain, psychiatric illness, previous open abdominal surgery, the presence of a gastrostomy, ventricular-peritoneal shunt or other abdominal prosthesis, immunosuppression, and those allergic to any of the medications.", "candidate_expression": "((abdominal prosthesis) AND (allergic) AND (any of the medications) AND (attention deficit disorder) AND (chronic pain) AND (developmental delay) AND (gastrostomy) AND (immunosuppression) AND (open abdominal surgery previous) AND (psychiatric illness) AND (ventricular-peritoneal shunt))"}
{"candidate_id": "LLM04793", "doc_id": "NCT03106389_exc", "case_bucket": "other", "source_criterion": "NA", "candidate_expression": "(EMPTY)"}
{"candidate_id": "LLM04794", "doc_id": "NCT02527512_inc", "case_bucket": "other", "source_criterion": "Age 3 to 18 years on day of surgery diagnosis of spinal deformity undergoing elective posterior spine multi-level instrumentation surgery", "candidate_expression": "((3 to 18 years) AND (Age) AND (elective) AND (multi-level instrumentation surgery) AND (on day of surgery) AND (posterior spine) AND (spinal deformity) AND (undergoing))"}
{"candidate_id": "LLM04795", "doc_id": "NCT02510404_exc", "case_bucket": "or", "source_criterion": "1. Patients with other uncontrolled infections (see 2.3.2 for definitions) 2. Patients who received ATG, Campath, or other T cell immunosuppressive monoclonal antibodies in the last 28 days 3. Received donor lymphocyte infusion in last 28 days 4. Diagnosis of Omenn's syndrome or MHC class I deficiency 5. Active and uncontrolled malignancy 6. Pregnant or lactating 7. Unable to wean steroids to ≤0.5 mg/kg/day prednisone. 8. Patients with Grade 3 hyperbilirubinemia", "candidate_expression": "((ATG) AND (Campath) AND (MHC class I deficiency) AND (Omenn's syndrome) AND (Pregnant) AND (T cell immunosuppressive monoclonal antibodies) AND (donor lymphocyte infusion in last 28 days) AND (hyperbilirubinemia Grade 3) AND (lactating) AND (malignancy Active uncontrolled) AND (other uncontrolled infections) AND (prednisone ≤0.5 mg/kg/day) AND (steroids) AND NOT (wean))"}
{"candidate_id": "LLM04796", "doc_id": "NCT02106624_exc", "case_bucket": "other", "source_criterion": "irreversible status of primary disease any history of malnutrition before enrollment history of steroid cortisol administration severe liver dysfunction (Child-Pugh Score C) pregnancy refuse to enrollment re-admission to ICU and has been enrolled during former admission to ICU", "candidate_expression": "((Child-Pugh Score C) AND (ICU) AND (liver dysfunction severe) AND (malnutrition before enrollment) AND (pregnancy) AND (primary disease irreversible status) AND (re-admission) AND (refuse to enrollment) AND (steroid cortisol))"}
{"candidate_id": "LLM04797", "doc_id": "NCT01082549_exc", "case_bucket": "or", "source_criterion": "1. Prior treatment with gemcitabine, carboplatin (except in the adjuvant setting), or Iniparib. 2. Past or current history of neoplasm other than the entry diagnosis, with the exception of treated non-melanoma skin cancer or carcinoma in-situ of any primary site, or invasive cancers treated definitively, with treatment ending >5 years previously and no evidence of recurrences. 3. A history of cardiac disease, as defined by: Malignant hypertension Unstable angina Congestive heart failure Myocardial infarction within the previous 6 months Symptomatic, unstable or uncontrolled, cardiac arrhythmias. Patients who have stable, rate-controlled atrial fibrillation are eligible for study enrollment. 4. Active brain metastases. Patients with treated brain metastases are eligible, if (1) radiation therapy was completed at least 2 weeks prior to study entry; (2) follow-up scan shows no disease progression; and (3) patient does not require steroids. 5. Women who are pregnant or lactating. 6. Any serious, active infection (> Grade 2) at the time of treatment. 7. A serious underlying medical condition that would impair the ability of the patient to receive protocol treatment. 8. A major surgical procedure, or significant traumatic injury ≤28 days of beginning treatment, or anticipation of the need for major surgery during the course of the study. 9. Uncontrolled or intercurrent illness including, that in the opinion of the investigator may increase the risks associated with study participation or administration of the investigational products, or that may interfere with the interpretation of the results. 10. History of any medical or psychiatric condition or laboratory abnormality that, in the opinion of the investigator, may increase the risks associated with the study participation or administration of the investigational products, or that may interfere with the interpretation of the results. 11. Known or suspected allergy/hypersensitivity to any agent given in the course of this trial. The above information is not intended to contain all considerations relevant to a patient's potential participation in a clinical trial.", "candidate_expression": "((9. Uncontrolled or intercurrent illness including, that in the opinion of the investigator may increase the risks associated with study participation or administration of the investigational products, or that may interfere with the interpretation of the results.) AND (A serious underlying medical condition that would impair the ability of the patient to receive protocol treatment.) AND (Congestive heart failure) AND (History of any medical or psychiatric condition or laboratory abnormality that, in the opinion of the investigator, may increase the risks associated with the study participation or administration of the investigational products, or that may interfere with the interpretation of the results.) AND (Known or suspected allergy/hypersensitivity to any agent given in the course of this trial) AND (Malignant hypertension) AND (Myocardial infarction within the previous 6 months) AND (Unstable angina) AND (Women) AND (Women who are pregnant or lactating) AND (agent given in the course of this trial) AND (brain metastases Active) AND (brain metastases treated) AND (cardiac arrhythmias) AND (cardiac disease history) AND (entry diagnosis) AND (follow-up scan) AND (illness in the opinion of the investigator may increase the risks the course of the study) AND (impair the ability of the patient to receive protocol treatment would beginning treatment) AND (in the opinion of the investigator may increase the risks) AND (infection serious active > Grade 2 > Grade 2) AND (laboratory) AND (major) AND (medical condition serious) AND (neoplasm history other than the entry diagnosis) AND (radiation therapy at least 2 weeks prior to study entry) AND (serious) AND (significant) AND (treated) AND (treated >5 years previously) AND NOT (evidence of recurrences) AND NOT (atrial fibrillation stable rate-controlled) AND NOT (disease progression) AND NOT (steroids require) AND ((allergy) OR (hypersensitivity)) AND ((Known) OR (suspected)) AND ((cancers invasive treated definitively) OR (carcinoma in-situ) OR (non-melanoma skin cancer treated)) AND ((Past) OR (current)) AND ((Iniparib) OR (carboplatin) OR (gemcitabine)) AND ((Symptomatic) OR (uncontrolled) OR (unstable)) AND ((lactating) OR (pregnant)) AND ((major surgery need for during the course of the study) OR (surgical procedure major) OR (traumatic injury significant ≤28 days of beginning treatment)) AND ((Uncontrolled) OR (intercurrent)) AND ((laboratory abnormality) OR (psychiatric condition)))"}
{"candidate_id": "LLM04798", "doc_id": "NCT03208127_exc", "case_bucket": "or", "source_criterion": "Pregnant or nursing (lactating) women HIV positivity Need for dual organ transplant Any contra-indication to liver transplantation per center protocol", "candidate_expression": "((HIV) AND (HIV positivity) AND (Need for) AND (contra-indication) AND (dual organ transplant) AND (lactating) AND (liver transplantation) AND (positivity) AND (women) AND ((Pregnant) OR (nursing)))"}
{"candidate_id": "LLM04799", "doc_id": "NCT00183885_inc", "case_bucket": "other", "source_criterion": "Unresectable, histologically confirmed hepatocellular carcinoma with evident disease limited to liver. Tissue from tumor must be available. This may be paraffin embedded tissue from previous biopsy/resection or if it is not available, a repeat biopsy must be performed. The requirement for biopsy may be waived if alpha-fetoprotein is greater than 500 ng/mL and in the investigators opinion not explained by a concurrent hepatic inflammatory process. Patients must agree to have a 20 cc blood sample drawn in addition to routine labs with each cycle of chemotherapy. Patients must have measurable disease. If prior radiation therapy was administered, measurable disease must be outside the radiation field. Patients must have a Zubrod performance status of 0-2. Patients must have a predicted life expectancy of at least 12 weeks. Patients must have a pre-treatment granulocyte count (i.e., segmented neutrophils + bands) of greater than or equal to 1,500/mm3, a hemoglobin level of greater than or equal to 9 gm/dl, and platelet count greater than or equal to 50,000/mm3. The granulocyte requirement may be waived if in the investigator's opinion the lower count reflects hypersplenism with adequate bone marrow reserves. Patients must have adequate renal function as documented by a calculated creatinine clearance ≥ 60. Patients must have adequate hepatic function as documented by a serum bilirubin less than or equal to 2x the institutional upper limit of normal, regardless of whether patients have liver involvement secondary to tumor. Patients may not have ascites or the ascites must be responsive to diuretics.", "candidate_expression": "((0-2) AND (20 cc) AND (Unresectable) AND (Zubrod performance status) AND (adequate) AND (agree to) AND (alpha-fetoprotein) AND (ascites) AND (at least 12 weeks) AND (biopsy) AND (blood sample drawn) AND (calculated creatinine clearance) AND (confirmed) AND (disease limited to liver) AND (granulocyte count) AND (greater than 500 ng/mL) AND (greater than or equal to 1,500/mm3) AND (greater than or equal to 50,000/mm3) AND (greater than or equal to 9 gm/dl) AND (hemoglobin level) AND (hepatic function) AND (hepatocellular carcinoma) AND (histologically) AND (less than or equal to 2x the institutional upper limit of normal) AND (may not have) AND (measurable disease) AND (outside the radiation field) AND (platelet count) AND (pre-treatment) AND (predicted life expectancy) AND (radiation therapy) AND (renal function) AND (responsive to diuretics) AND (routine labs) AND (segmented neutrophils + bands) AND (serum bilirubin) AND (with each cycle of chemotherapy) AND (≥ 60))"}
{"candidate_id": "LLM04800", "doc_id": "NCT02573597_inc", "case_bucket": "or", "source_criterion": "ASA I & II, Nulliparous and Multiparous, Spontaneous/Induced/Augmented Labor, Early active labor (cervix <5 cm (if known)), Pain (VPS) > 3, 18-45 years of age", "candidate_expression": "((18-45 years) AND (<5 cm) AND (> 3) AND (ASA) AND (Augmented Labor) AND (Early active labor) AND (I & II) AND (Induced Labor) AND (Multiparous) AND (Nulliparous) AND (Pain (VPS)) AND (Spontaneous Labor) AND (age) AND (cervix))"}
```
