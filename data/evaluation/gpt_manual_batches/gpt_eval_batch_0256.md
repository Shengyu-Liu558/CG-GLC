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
{"candidate_id": "LLM06376", "doc_id": "NCT02332291_exc", "case_bucket": "or", "source_criterion": "Current or past diagnoses of other Axis I psychiatric disorders, except for generalized anxiety disorder (GAD) symptoms occurring during a depressive episode History of alcohol or drug dependence or abuse in the last three years History of developmental disorder or IQ score < 70 Presence of acute suicidality Acute grief (< 1 month) Current or past psychosis Primary neurological disorder, including but not limited to dementia, stroke, brain tumors, epilepsy, Parkinson's disease, or demyelinating diseases MRI contraindications Any physical or intellectual disability adversely affecting ability to complete assessments Electroconvulsive therapy in last 6 months Use of antidepressant medications or other psychotropic medications in the last 4 weeks (or the last 6 weeks for fluoxetine). Occasional use of benzodiazepines or non-benzodiazepine sedatives (such as zolpidem, eszopiclone, or zaleplon) during this period is allowable. A failed therapeutic trial of escitalopram in the current depressive episode (defined as at least 6 weeks of treatment at a daily dose of 10mg or higher) Known allergy or hypersensitivity to escitalopram or bupropion Current or planned psychotherapy", "candidate_expression": "((< 1 month) AND (< 70) AND (Acute grief) AND (Axis I psychiatric disorders) AND (Electroconvulsive therapy) AND (MRI) AND (Occasional use) AND (Primary neurological disorder) AND (acute suicidality) AND (at least 6 weeks of treatment) AND (contraindications) AND (daily dose of 10mg or higher) AND (depressive episode) AND (during a depressive episode) AND (escitalopram) AND (except for) AND (failed) AND (fluoxetine) AND (generalized anxiety disorder (GAD)) AND (in last 6 months) AND (in the current depressive episode) AND (in the last three years) AND (is allowable) AND (other) AND (psychosis) AND (psychotherapy) AND (therapeutic trial) AND ((alcohol abuse) OR (alcohol dependence) OR (drug abuse) OR (drug dependence)) AND ((IQ score) OR (developmental disorder)) AND ((Current) OR (past)) AND ((Parkinson's disease) OR (brain tumors) OR (dementia) OR (demyelinating diseases) OR (epilepsy) OR (stroke)) AND ((intellectual disability) OR (physical disability)) AND ((antidepressant medications) OR (psychotropic medications)) AND ((in the last 4 weeks) OR (in the last 6 weeks)) AND ((benzodiazepines sedatives) OR (non-benzodiazepine sedatives)) AND ((eszopiclone) OR (zaleplon) OR (zolpidem)) AND ((allergy) OR (hypersensitivity)) AND ((bupropion) OR (escitalopram)) AND ((Current) OR (planned)))"}
{"candidate_id": "LLM06377", "doc_id": "NCT03555526_exc", "case_bucket": "or", "source_criterion": "aged less than 20 years history of gastric resection surgery history of allergy to study drugs pregnancy or lactating women severe underlying illness, such as end stage renal disease, decompensated liver cirrhosis, or non-curative malignancy", "candidate_expression": "((aged less than 20 years) AND (allergy) AND (end stage renal disease) AND (gastric resection surgery) AND (lactating) AND (liver cirrhosis decompensated) AND (malignancy non-curative) AND (pregnancy) AND (severe underlying illness) AND (study drugs) AND (women))"}
{"candidate_id": "LLM06378", "doc_id": "NCT02745704_inc", "case_bucket": "other", "source_criterion": "CHB patients who had received NAs for more than 12 months. Hepatitis B e antigen (HBeAg)-negative and anti-HBeAg positive. Hepatitis B surface antigen (HBsAg) positive and <1500 IU/mL. Hepatitis B virus DNA not detectable(Roche Cobas).", "candidate_expression": "((CHB) AND (HBeAg) AND (HBsAg) AND (Hepatitis B e antigen negative) AND (Hepatitis B surface antigen positive <1500 IU/mL) AND (Hepatitis B virus DNA not detectable) AND (NAs more than 12 months.) AND (anti-HBeAg positive))"}
{"candidate_id": "LLM06379", "doc_id": "NCT02942303_exc", "case_bucket": "or", "source_criterion": "Patients with previous periorbital/forehead surgery Patients who plucked the upper eyebrow margin Patients with eyebrow tatoos Patients with upper face botulinum toxin injection in the past 12 months Patients with resorbable upper face fillers injection in the past 12 months Patients with previous permanent upper face fillers injection Pregnant patients Lactating patients Patients with preexisting neuromuscular conditions (myasthenia gravis, Eaton Lambert syndrome) Patients using medication that could potentiate the effect of botulinum (ex: aminoglycoside antibiotics) Patients with sensitivity to botulinum toxin or human albumin", "candidate_expression": "((Lactating) AND (Pregnant) AND (aminoglycoside antibiotics) AND (botulinum) AND (botulinum toxin injection) AND (eyebrow tatoos) AND (in the past 12 months) AND (medication) AND (neuromuscular conditions) AND (permanent fillers injection) AND (plucked the upper eyebrow margin) AND (potentiate the effect) AND (resorbable fillers injection) AND (sensitivity) AND (upper face) AND ((forehead surgery) OR (periorbital surgery)) AND ((Eaton Lambert syndrome) OR (myasthenia gravis)) AND ((botulinum toxin) OR (human albumin)))"}
{"candidate_id": "LLM06380", "doc_id": "NCT01793519_exc", "case_bucket": "or", "source_criterion": "Had dose increase of anti-TNF agent or DMARD in the last 6 months Had change of anti-TNF agent or DMARD in the last 6 months Treated currently with golimumab or certolizumab Treated with greater than 10 mg of prednisone (or equivalent) daily in the last 6 months Treated with greater than 5 mg of prednisone (or equivalent) daily in the last 3 months Treated with intramuscular or intravenous corticosteroids in the last 6 months for RA activity Treated with anakinra, abatacept, or tocilizumab in the last 6 months Treated with rituximab in the last 12 months Treated with an investigational RA drug in the last 6 months Pregnant (or anticipate pregnancy during the study period) or lactating women Absence of documentation in the medical record of clinical remission for the last 6 months Unwilling to discontinue anti-TNF agent Absence of documentation of negative tuberculin skin test, negative QuantiFERON-TB Gold test, or treatment for latent tuberculosis prior to starting treatment with the anti-TNF agent Treatment of solid malignancy or non-melanoma skin cancer within the past 5 years, or any history of melanoma or hematologic or lymphoproliferative malignancy Absence of documentation of age-appropriate cancer screening at the time of randomization Absence of documentation of negative hepatitis B serologies, absence of completion of treatment for chronic hepatitis B, or absence of suppressive antiviral treatment Unable to provide informed consent Anticipate not being available or able to comply with the schedule of study visits", "candidate_expression": "((Absence of) AND (Anticipate not being available or able to comply with the schedule of study visits) AND (QuantiFERON-TB Gold test) AND (RA) AND (RA drug) AND (Unable to provide informed consent) AND (Unwilling) AND (absence) AND (absence of) AND (age-appropriate) AND (anti-TNF agent) AND (anticipate during the study period) AND (at the time of randomization) AND (cancer screening) AND (change) AND (clinical remission) AND (corticosteroids) AND (daily) AND (discontinue) AND (dose increase) AND (for the last 6 months) AND (greater than 10 mg) AND (greater than 5 mg) AND (in the last 12 months) AND (in the last 3 months) AND (in the last 6 months) AND (investigational) AND (latent) AND (negative) AND (prednisone) AND (pregnancy) AND (prior to starting treatment with the anti-TNF agent) AND (rituximab) AND (starting treatment with the anti-TNF agent) AND (the time of randomization) AND (treatment) AND (treatment with the anti-TNF agent) AND (tuberculin skin test) AND (tuberculosis) AND (within the past 5 years) AND (women) AND ((certolizumab) OR (golimumab)) AND ((DMARD) OR (anti-TNF agent)) AND ((intramuscular) OR (intravenous)) AND ((abatacept) OR (anakinra) OR (tocilizumab)) AND ((Pregnant) OR (lactating)) AND ((non-melanoma skin cancer) OR (solid malignancy)) AND ((hematologic) OR (lymphoproliferative malignancy) OR (melanoma)) AND ((chronic hepatitis B) OR (hepatitis B serologies) OR (suppressive antiviral treatment)))"}
{"candidate_id": "LLM06381", "doc_id": "NCT02953873_exc", "case_bucket": "other", "source_criterion": "NA", "candidate_expression": "(EMPTY)"}
{"candidate_id": "LLM06382", "doc_id": "NCT02607163_exc", "case_bucket": "other", "source_criterion": "NA", "candidate_expression": "(EMPTY)"}
{"candidate_id": "LLM06383", "doc_id": "NCT03275584_inc", "case_bucket": "other", "source_criterion": "Adult patient being referred for clinically indicated positron emission tomography myocardial perfusion imaging at the Centre hospitalier de l'Université de Montréal", "candidate_expression": "((Adult) AND (Centre hospitalier de l'Université de Montréal) AND (clinically indicated) AND (positron emission tomography myocardial perfusion imaging))"}
{"candidate_id": "LLM06384", "doc_id": "NCT01793519_inc", "case_bucket": "or", "source_criterion": "Age greater than or equal to 18 years Have RA, as defined by the 1987 revised American College of Rheumatology criteria In sustained clinical remission for the last 6 months while receiving treatment with either etanercept, infliximab, or adalimumab, and greater than or equal to 1 DMARD (methotrexate, hydroxychloroquine, sulfasalazine, leflunomide, minocycline, cyclosporine, azathioprine, gold, penicillamine). DAS28 should be less than 2.6 on each visit over the preceding 6 months, with at least one visit 2-4 months before enrollment. If there is no visit 6 months before enrollment, the nearest visit in the 6-12 month period before enrollment should be considered and have a DAS28 less than 2.6.", "candidate_expression": "((1987 revised American College of Rheumatology criteria) AND (2-4 months before enrollment) AND (Age) AND (DAS28) AND (DMARD) AND (RA) AND (adalimumab) AND (at least one) AND (azathioprine) AND (cyclosporine) AND (etanercept) AND (for the last 6 months) AND (gold) AND (greater than or equal to 1) AND (greater than or equal to 18 years) AND (hydroxychloroquine) AND (infliximab) AND (leflunomide) AND (less than 2.6) AND (methotrexate) AND (minocycline) AND (on each visit) AND (over the preceding 6 months) AND (penicillamine) AND (sulfasalazine) AND (sustained clinical remission) AND (visit))"}
{"candidate_id": "LLM06385", "doc_id": "NCT01803828_inc", "case_bucket": "or", "source_criterion": "age 35-75 years; Diagnosis of Type 2 Diabetes from at least 3 years; HbA1c < 10%; normal blood pressure or controlled hypertension; BMI < 40;", "candidate_expression": "((35-75 years) AND (< 10%) AND (< 40) AND (BMI) AND (HbA1c) AND (Type 2 Diabetes) AND (age) AND (at least 3 years) AND ((controlled hypertension) OR (normal blood pressure)))"}
{"candidate_id": "LLM06386", "doc_id": "NCT01806558_exc", "case_bucket": "or", "source_criterion": "1. Are unable to understand and sign the consent form 2. Are pregnant or lactating 3. Are physically unable to sit upright and still for 40 minutes 4. Have undergone bilateral mastectomy 5. Are not scheduled to undergo conventional ultrasound", "candidate_expression": "((Are unable to understand and sign the consent form) AND (bilateral mastectomy) AND (lactating) AND (physically unable to sit upright and still for 40 minutes) AND (pregnant) AND NOT (conventional ultrasound scheduled))"}
{"candidate_id": "LLM06387", "doc_id": "NCT02680054_inc", "case_bucket": "other", "source_criterion": "Diagnosis of Type 1 diabetes (for at least a year) On multiple daily insulin injections, including basal long-acting insulin and rapid-acting insulin before each meal. HbA1c < 75 mmol/mol (9.0%) Participant and/or parent/legal guardian willing and able to give informed consent for participation in the study. Family have a freezer in which to safely store the test meals. In the Investigator's opinion, is able and willing to comply with all trial requirements.", "candidate_expression": "((9.0%) AND (< 75 mmol/mol) AND (HbA1c) AND (In the Investigator's opinion, is able and willing to comply with all trial requirements) AND (Participant and/or parent/legal guardian willing and able to give informed consent for participation in the study) AND (Type 1 diabetes) AND (at least a year) AND (basal long-acting) AND (daily) AND (insulin) AND (rapid-acting))"}
{"candidate_id": "LLM06388", "doc_id": "NCT02563535_exc", "case_bucket": "or", "source_criterion": "need for major amputation known before intervention allergy to Paclitaxel contraindication for combined antiplatelet treatment life expectancy <1 year hypersensitivity or contraindication to one of the study drugs lack of consent", "candidate_expression": "((<1 year) AND (Paclitaxel) AND (allergy) AND (combined antiplatelet treatment) AND (contraindication) AND (lack of consent) AND (life expectancy) AND (major amputation) AND (one of) AND (study drugs) AND ((contraindication) OR (hypersensitivity)))"}
{"candidate_id": "LLM06389", "doc_id": "NCT02992028_inc", "case_bucket": "other", "source_criterion": "Rotator cuff tear patients undergoing arthroscopic rotator cuff tear", "candidate_expression": "((Rotator cuff tear) AND (arthroscopic rotator cuff tear))"}
{"candidate_id": "LLM06390", "doc_id": "NCT02940912_exc", "case_bucket": "or", "source_criterion": "Atypical Parkinsonian Syndromes Parkinson's disease with hallucinations Parkinson's disease with impulse Control disorder (ICD) Parkinson's disease already treated with APOMORPHINE pump or justifying the use of the pump continuously day and night Another obvious severe disease explaining insomnia Exclusion for monitoring difficulties (mutation, insufficient motivation, priority associated pathology in care) Patient unwilling to accept a pump Patient not accepting polysomnography and multiple sleep latency test Patient with health problems or a skin disease precluding continuous subcutaneous infusion Female parturient or nursing Cardiac dysrhythmia precluding treatment with domperidone or apomorphine (increased QTc = 440 ms in men, QTc = 450 ms in women) antiemetic neuroleptics Tetrabenazine Excessive alcohol consumption Hypersensitivity to apomorphine or one of the excipients Respiratory Depression Hepatic impairment Intellectual Disability Dementia", "candidate_expression": "((= 440 ms) AND (= 450 ms) AND (APOMORPHINE) AND (Atypical) AND (Cardiac dysrhythmia) AND (Dementia) AND (Excessive alcohol consumption) AND (Female) AND (Hepatic impairment) AND (Hypersensitivity) AND (Intellectual Disability) AND (Parkinson's disease) AND (Parkinsonian Syndromes) AND (QTc) AND (Respiratory Depression) AND (Tetrabenazine) AND (antiemetic neuroleptics) AND (continuous subcutaneous infusion) AND (hallucinations) AND (impulse Control disorder (ICD)) AND (insomnia) AND (multiple sleep latency test) AND (not) AND (not accepting) AND (polysomnography) AND (precluding) AND (pump) AND (severe disease) AND (unwilling) AND (unwilling to accept) AND ((health problems) OR (skin disease)) AND ((nursing) OR (parturient)) AND ((apomorphine) OR (domperidone)) AND ((men) OR (women)) AND ((apomorphine) OR (excipients)))"}
{"candidate_id": "LLM06391", "doc_id": "NCT03198910_inc", "case_bucket": "or", "source_criterion": "Patients with pulmonary arterial hypertension (PAH) Patients with chronic thromboembolic pulmonary hypertension (CTEPH) All prevalent patients (diagnosed >12 month ago) with PAH or distal CTEPH who had a consultation at the PH centre in Zurich between November 2015 and November 2016)", "candidate_expression": "((CTEPH distal) AND (PAH) AND (Zurich) AND (chronic thromboembolic pulmonary hypertension (CTEPH)) AND (consultation at the PH centre) AND (pulmonary arterial hypertension (PAH)))"}
{"candidate_id": "LLM06392", "doc_id": "NCT03305575_inc", "case_bucket": "other", "source_criterion": "ASA classification II or III females Age: 18-45 years old BMI = 50 kg/m2 Singleton pregnancy Simple prophylactic cervical cerclage Planning neuraxial anesthesia", "candidate_expression": "((18-45 years old) AND (= 50 kg/m2) AND (ASA classification) AND (Age) AND (BMI) AND (II or III) AND (Planning) AND (Simple) AND (Singleton pregnancy) AND (cervical cerclage) AND (females) AND (neuraxial anesthesia) AND (prophylactic))"}
{"candidate_id": "LLM06393", "doc_id": "NCT02592980_inc", "case_bucket": "other", "source_criterion": "Only patients with atrial fibrillation, above 18 years, and with TTR <50% based on the last three values of INR will be included in this study.", "candidate_expression": "((<50%) AND (TTR) AND (above 18 years) AND (atrial fibrillation) AND (based on the last three values of INR) AND (years))"}
{"candidate_id": "LLM06394", "doc_id": "NCT01728194_inc", "case_bucket": "or", "source_criterion": "Age: 60-85 years, right-handed; Diagnosis: Major depression, unipolar (by Structured Clinical Interview for Diagnostic and Statistical Manual (DSM)IV (SCID-R) and DSM-IV criteria); Age of onset of first episode = 50 years with up to three depressive episodes; Severity of depression: A 24-Item Hamilton Depression Rating Scale (HDRS) = 20.", "candidate_expression": "((24-Item Hamilton Depression Rating Scale = 20) AND (Age 60-85 years) AND (Age = 50 years) AND (DSM) AND (DSM-IV criteria)) AND (HDRS) AND (IV Structured Clinical Interview for Diagnostic and Statistical Manual) AND (Major depression unipolar) AND (SCID) AND (depression) AND (depressive episodes three) AND (onset of first episode) AND (right-handed))"}
{"candidate_id": "LLM06395", "doc_id": "NCT03506750_exc", "case_bucket": "or", "source_criterion": "previous retinal vein occlusion. any intraocular surgery within the previous 12 months. myopia of > or = to 8 diopters. active ocular or periocular infection treatment with an investigational agent for any condition 60 days prior to enrollment. evidence of severe cardiac disease. clinically significant peripheral vascular disease (previous surgery, amputation, or symptoms of claudication) uncontrolled hypertension (treated systolic blood pressure > 155 mmHg or diastolic blood pressure > 95 mmHg) stroke within the preceding 12 months.", "candidate_expression": "((> 155 mmHg) AND (> 95 mmHg) AND (> or = to 8 diopters) AND (active) AND (amputation) AND (cardiac disease) AND (clinically significant) AND (diastolic blood pressure) AND (evidence of) AND (hypertension) AND (intraocular surgery) AND (myopia) AND (ocular infection) AND (periocular infection) AND (peripheral vascular disease) AND (previous) AND (previous surgery) AND (retinal vein occlusion) AND (severe) AND (stroke) AND (symptoms of claudication) AND (systolic blood pressure) AND (treated) AND (treatment with an investigational agent for any condition 60 days prior to enrollment) AND (uncontrolled) AND (within the preceding 12 months) AND (within the previous 12 months))"}
{"candidate_id": "LLM06396", "doc_id": "NCT03372265_exc", "case_bucket": "or", "source_criterion": "Allergy to LA Infection in or near insertion site of the peripheral nerve catheter Anatomical abnormalities preventing successful peripheral catheter insertion Habitual use of opioids Pregnancy or breastfeeding (disproved by a negative pregnancy test before trial inclusion)", "candidate_expression": "((Allergy) AND (Anatomical abnormalities) AND (Habitual use) AND (LA) AND (Pregnancy) AND (before trial inclusion) AND (breastfeeding) AND (disproved by) AND (in insertion site) AND (insertion) AND (near insertion site) AND (negative) AND (opioids) AND (peripheral catheter) AND (peripheral nerve catheter) AND (pregnancy test) AND (preventing) AND (successful) AND (trial inclusion))"}
{"candidate_id": "LLM06397", "doc_id": "NCT03004209_inc", "case_bucket": "or", "source_criterion": "Clinically diagnosed autoimmune encephalitis Ineffective 1st line treatment (e.g. steroid IV, IVIg) and 2nd line treatment (e.g. Rituximab or cyclophosphamide)", "candidate_expression": "((1st line treatment Ineffective) AND (2nd line treatment Ineffective) AND (IVIg) AND (Rituximab) AND (autoimmune encephalitis Clinically diagnosed) AND (cyclophosphamide) AND (steroid IV))"}
{"candidate_id": "LLM06398", "doc_id": "NCT02068365_inc", "case_bucket": "or", "source_criterion": "Male & female patients >= 18 and < 70 years of age Positive HBeAg before starting NA treatment Treated by a single NA (lamivudine, adefovir, entecavir or tenofovir) for 6 months to 5 years Developed HBeAg seroconversion (HBeAg negative and ant-HBe negative) with undetectable HBV DNA by PCR based assay on NA treatment. Negative urine or serum pregnancy test (for women of childbearing potential) documented within the 24-hour period prior to the first dose of test drug. Additionally, all females must be using reliable contraception during the study and for 3 months after treatment completion", "candidate_expression": "((Additionally, all females must be using reliable contraception during the study and for 3 months after treatment completion) AND (HBV DNA undetectable) AND (HBeAg Positive before starting NA treatment) AND (HBeAg negative) AND (HBeAg seroconversion) AND (Male) AND (NA) AND (NA single) AND (PCR based assay) AND (Treated for 6 months to 5 years) AND (adefovir) AND (age >= 18 and < 70 years) AND (ant-HBe negative) AND (childbearing potential) AND (entecavir) AND (female) AND (lamivudine) AND (serum pregnancy test) AND (tenofovir) AND (treatment) AND (urine pregnancy test) AND (women))"}
{"candidate_id": "LLM06399", "doc_id": "NCT02715466_exc", "case_bucket": "or", "source_criterion": "Administration of HES, dextrane solutions or > 500 ml of Gelatin solutions within the 24 h prior to randomization Death expected within the next 48 h (moribund patients as defined by ASA = class V) Patients whose medical condition does preclude the PLR manoeuvre Patients for whom the need of pressure infusions are expected Requirement for renal support (either continuous or discontinuous techniques, including intermittent haemodialysis, haemofiltration and haemodiafiltration) Patients receiving therapeutic heparin medication due to chronic coagulation disease / anticoagulation medication (i.e. partial thromboplastin time > 60 sec) Acutely burned patients Contraindications according to summary of product characteristics of investigational test and reference product Simultaneous participation in another interventional clinical trial (drugs or medical devices studies)", "candidate_expression": "((ASA = class V) AND (Acutely burned) AND (Death expected within the next 48 h) AND (Gelatin solutions > 500 ml) AND (HES) AND (anticoagulation medication) AND (chronic coagulation disease) AND (dextrane solutions) AND (heparin) AND (moribund) AND (partial thromboplastin time > 60 sec) AND (renal support Requirement for))"}
{"candidate_id": "LLM06400", "doc_id": "NCT02883400_inc", "case_bucket": "other", "source_criterion": "liver transplant", "candidate_expression": "(liver transplant)"}
```
