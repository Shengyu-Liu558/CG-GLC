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
{"candidate_id": "LLM04426", "doc_id": "NCT02287259_inc", "case_bucket": "or", "source_criterion": "major depressive episode in type2 bipolar disorder or bipolar disorder NOS.(MADRS more than 20 point) 18years to 65years subjects who sign the informed consent document", "candidate_expression": "((18years to 65years) AND (MADRS) AND (NOS) AND (bipolar disorder) AND (major depressive episode) AND (more than 20 point) AND (sign the informed consent) AND (type2 bipolar disorder) AND (years))"}
{"candidate_id": "LLM04427", "doc_id": "NCT02476461_inc", "case_bucket": "other", "source_criterion": "symptomatic Dupuytrens contracture with palpable cord, involving MCP, total contracture size over 30 degrees", "candidate_expression": "((Dupuytrens contracture symptomatic involving MCP) AND (palpable cord) AND (total contracture size over 30 degrees))"}
{"candidate_id": "LLM04428", "doc_id": "NCT02590653_exc", "case_bucket": "other", "source_criterion": "NA", "candidate_expression": "(EMPTY)"}
{"candidate_id": "LLM04429", "doc_id": "NCT02952963_exc", "case_bucket": "or", "source_criterion": "Fasting plasma glucose > 7,0 mM, HbA1c > 48 mmol/mol 3 months after RYGB Dysregulated thyroid diseases, use of antithyroid treatment. Late diabetic complications as retinopathy, renal insufficiency, neuropathy or previous pancreatitis. Complications to RYGB. Documented reactive hypoglycaemia, severe dumping (vomiting, diarrhea, severe abdominal pain after food intake) Cholecystectomy.", "candidate_expression": "((Cholecystectomy) AND (Complications) AND (Late diabetic complications) AND (RYGB) AND (dumping severe) AND (reactive hypoglycaemia) AND ((Fasting plasma glucose > 7,0 mM) OR (HbA1c > 48 mmol/mol)) AND ((neuropathy) OR (pancreatitis previous) OR (renal insufficiency) OR (retinopathy)) AND ((abdominal pain severe after food intake) OR (diarrhea) OR (vomiting)) AND ((antithyroid treatment) OR (thyroid diseases Dysregulated)))"}
{"candidate_id": "LLM04430", "doc_id": "NCT00319748_exc", "case_bucket": "or", "source_criterion": "Had/have the following prior/concurrent therapy: Systemic corticosteroids (oral or injectable) within 7 days of first dose of 852A (topical or inhaled steroids are allowed) Investigational drugs/agents within 14 days of first dose of 852A Immunosuppressive therapy, including cytotoxic agents within 14 days of first dose of 852A (nitrosoureas within 30 days of first dose) Drugs known to induce QT interval prolongation and/or induce Torsades de pointes unless best available drug required to treat life-threatening conditions Radiotherapy within 3 weeks of the first dose of 852A Hematopoietic cell transplantation within 4 weeks of first dose of 852A Evidence of active infection within 3 days of first dose of 852A Active fungal infection or pulmonary infiltrates (prior treated disease stable for 2 weeks is allowable) Cardiac ischemia, cardiac arrhythmias or congestive heart failure uncontrolled by medication History of, or clinical evidence of, a condition which, in the opinion of the investigator, could confound the results of the study or put the subject at undue risk Uncontrolled intercurrent or chronic illness Active autoimmune disease requiring immunosuppressive therapy within 30 days Active coagulation disorder not controlled with medication Pregnant or lactating Concurrent malignancy (if in remission, at least 5 years disease free) except for localized (in-situ) disease, basal carcinomas and cutaneous squamous cell carcinomas that have been adequately treated Any history of brain metastases or any other active central nervous system (CNS) disease", "candidate_expression": "((852A) AND (Active) AND (Cardiac ischemia) AND (Concurrent) AND (Drugs known to induce QT interval prolongation) AND (Drugs known to induce Torsades de pointes) AND (Evidence) AND (Hematopoietic cell transplantation) AND (History) AND (Immunosuppressive therapy) AND (Investigational drugs/agents) AND (Pregnant) AND (Radiotherapy) AND (Systemic corticosteroids) AND (Uncontrolled) AND (active) AND (active infection) AND (adequately treated) AND (any other central nervous system (CNS) disease) AND (are allowed) AND (at least 5 years) AND (autoimmune disease) AND (basal carcinomas) AND (brain metastases) AND (cardiac arrhythmias) AND (chronic illness) AND (clinical evidence) AND (coagulation disorder) AND (congestive heart failure) AND (controlled with medication) AND (could confound the results of the study or put the subject at undue risk a condition which) AND (cutaneous squamous cell carcinomas) AND (cytotoxic agents) AND (disease free) AND (except for) AND (for 2 weeks) AND (fungal infection) AND (history of) AND (immunosuppressive therapy) AND (in remission) AND (inhaled steroids) AND (injectable) AND (intercurrent illness) AND (is allowable) AND (lactating) AND (localized (in-situ) disease) AND (malignancy) AND (nitrosoureas) AND (not) AND (oral) AND (prior treated disease) AND (pulmonary infiltrates) AND (requiring) AND (stable) AND (topical steroids) AND (uncontrolled by medication) AND (within 14 days of first dose) AND (within 3 days of first dose) AND (within 3 weeks of the first dose) AND (within 30 days) AND (within 30 days of first dose) AND (within 4 weeks of first dose) AND (within 7 days of first dose))"}
{"candidate_id": "LLM04431", "doc_id": "NCT02675153_exc", "case_bucket": "or", "source_criterion": "Allergic to sirolimus or serious side effects Need emergency surgery Accompanied with other severe disease (involve C.diff infection) Follow-up less than 1 year", "candidate_expression": "((Allergic) AND (C.diff infection) AND (Follow-up less than 1 year) AND (emergency surgery Need) AND (severe disease) AND (side effects serious) AND (sirolimus))"}
{"candidate_id": "LLM04432", "doc_id": "NCT02935855_inc", "case_bucket": "or", "source_criterion": "non-valvular atrial fibrillation nondiabetic patients type 1 and 2 diabetic patients", "candidate_expression": "((atrial fibrillation non-valvular) AND (diabetic) AND NOT (diabetic) AND ((type 1) OR (type 2)))"}
{"candidate_id": "LLM04433", "doc_id": "NCT03280017_inc", "case_bucket": "other", "source_criterion": "American Society of Anesthesiologist physical status 1-3 Scheduled for elective video-assisted thoracic surgery Able to operate a patient-controlled analgesia device (PCA)", "candidate_expression": "((American Society of Anesthesiologist physical status 1-3) AND (PCA) AND (patient-controlled analgesia device) AND (video-assisted thoracic surgery Scheduled for elective))"}
{"candidate_id": "LLM04434", "doc_id": "NCT03211741_inc", "case_bucket": "or", "source_criterion": "Age = 18 years of either gender Written informed consent must be obtained before any intravitreal injection of bevacizumab is performed Visual impairment predominantly due to abnormal new vessel ingrowth and/or macular edema. The presence of fluid (intraretinal, subretinal or sub-RPE) detected clinically or on the ocular coherence tomography.", "candidate_expression": "((Age = 18 years) AND (Visual impairment) AND (Written informed consent must be obtained before any intravitreal injection of bevacizumab is performed) AND (abnormal new vessel ingrowth) AND (either gender) AND (fluid intraretinal subretinal sub-RPE) AND (macular edema) AND (ocular coherence tomography))"}
{"candidate_id": "LLM04435", "doc_id": "NCT03149887_exc", "case_bucket": "or", "source_criterion": "Pregnancy, coagulopathy, allergy to bupivacaine, renal failure, hepatic insufficiency, and/or inappropriate candidate for usual therapy (specifically, if unable to receive the usual preoperative interscalene nerve block: preexisting nerve injury on side of surgery, refusal of nerve block, infection at site of nerve block).", "candidate_expression": "((bupivacaine) AND (nerve injury preexisting side of surgery) AND (preoperative interscalene nerve block unable to receive) AND (usual therapy) AND ((Pregnancy) OR (allergy) OR (coagulopathy) OR (hepatic insufficiency) OR (inappropriate candidate) OR (renal failure)) AND ((infection site of nerve block) OR (refusal of nerve block)))"}
{"candidate_id": "LLM04436", "doc_id": "NCT01669369_exc", "case_bucket": "or", "source_criterion": "a history of non-standard treatment(chemotherapy or surgery) secondary osteosarcoma or well-differentiated parosteal osteosarcoma evident dysfunction of cardia,liver and kidney, or pregnant women or women during lactation", "candidate_expression": "((history) AND (non-standard treatment) AND (well-differentiated) AND ((chemotherapy) OR (surgery)) AND ((parosteal osteosarcoma) OR (secondary osteosarcoma)) AND ((dysfunction of cardia) OR (dysfunction of kidney) OR (dysfunction of liver) OR (lactation) OR (pregnant)))"}
{"candidate_id": "LLM04437", "doc_id": "NCT03506750_inc", "case_bucket": "or", "source_criterion": "18 years or older Type 1 or 2 diabetes PDR patients requiring surgical intervention for complications of vitreous hemorrhage or traction retinal detachment and pre-operative IVC treatment. women postmenopausal for 12 months before the study, surgically sterile, or not pregnant and on effective contraception.", "candidate_expression": "((PDR) AND (older 18 years or older) AND (surgical intervention requiring) AND (women postmenopausal for 12 months before the study, surgically sterile, or not pregnant and on effective contraception.) AND ((IVC treatment pre-operative) OR (traction retinal detachment) OR (vitreous hemorrhage)) AND ((Type 1 diabetes) OR (Type 2 diabetes)))"}
{"candidate_id": "LLM04438", "doc_id": "NCT03297944_inc", "case_bucket": "other", "source_criterion": "valid driver's license english-speaking and literate", "candidate_expression": "((english-speaking) AND (literate) AND (valid driver's license))"}
{"candidate_id": "LLM04439", "doc_id": "NCT02334722_exc", "case_bucket": "or", "source_criterion": "No known history of seizure activity. Pregnant or breastfeeding. Renal dysfunction (CrCl < 30ml/min). Beck's Depression Inventory (BDI) =14 Allergy to levetiracetam.", "candidate_expression": "((< 30ml/min) AND (=14) AND (Allergy) AND (Beck's Depression Inventory (BDI)) AND (CrCl) AND (No) AND (Pregnant) AND (Renal dysfunction) AND (breastfeeding) AND (history) AND (levetiracetam) AND (seizure activity))"}
{"candidate_id": "LLM04440", "doc_id": "NCT03059069_inc", "case_bucket": "other", "source_criterion": "Type 2 diabetic patients Age = 50 Glycemic control: HbA1c = 10.0% 10 = Beck Depression Inventory (BDI) <30 points Participants who can undergo contraception in case of being in childbearing period Understands the study procedure, alternatives, and risks and voluntarily agrees to participate by giving written informed concent", "candidate_expression": "((<30 points) AND (= 10.0%) AND (= 50) AND (Age) AND (Beck Depression Inventory (BDI)) AND (HbA1c) AND (Participants who can undergo contraception in case of being in childbearing period) AND (Type 2 diabetic) AND (Understands the study procedure, alternatives, and risks and voluntarily agrees to participate by giving written informed concent))"}
{"candidate_id": "LLM04441", "doc_id": "NCT02457442_inc", "case_bucket": "or", "source_criterion": "ASA physical status 1 or 2 Written informed consent Cardiovascular disease Pulmonary disease Liver disease CNS disease Alcohol or drug abuse Chronic intake of CNS active drugs Body mass index > 35 Diabetes mellitus Hypersensitivity or allergy to one of the study drugs", "candidate_expression": "((ASA physical status 1 2) AND (Alcohol abuse) AND (Body mass index > 35) AND (CNS active drugs Chronic intake) AND (CNS disease) AND (Cardiovascular disease) AND (Diabetes mellitus) AND (Hypersensitivity) AND (Liver disease) AND (Pulmonary disease) AND (Written informed consent) AND (allergy) AND (drug abuse) AND (study drugs))"}
{"candidate_id": "LLM04442", "doc_id": "NCT03506750_exc", "case_bucket": "or", "source_criterion": "previous retinal vein occlusion. any intraocular surgery within the previous 12 months. myopia of > or = to 8 diopters. active ocular or periocular infection treatment with an investigational agent for any condition 60 days prior to enrollment. evidence of severe cardiac disease. clinically significant peripheral vascular disease (previous surgery, amputation, or symptoms of claudication) uncontrolled hypertension (treated systolic blood pressure > 155 mmHg or diastolic blood pressure > 95 mmHg) stroke within the preceding 12 months.", "candidate_expression": "((amputation) AND (cardiac disease evidence of severe) AND (diastolic blood pressure > 95 mmHg) AND (hypertension uncontrolled) AND (intraocular surgery within the previous 12 months) AND (myopia > or = to 8 diopters) AND (ocular infection) AND (periocular infection) AND (peripheral vascular disease clinically significant) AND (previous surgery) AND (retinal vein occlusion previous) AND (stroke within the preceding 12 months) AND (symptoms of claudication) AND (systolic blood pressure > 155 mmHg) AND (treatment with an investigational agent for any condition 60 days prior to enrollment))"}
{"candidate_id": "LLM04443", "doc_id": "NCT02580630_exc", "case_bucket": "or", "source_criterion": "Earlier operations in the foot and leg, that is judged to complicate training known arthritis. known diabetes Leg ulcerations or infections in the foot. Judged unable to comply with the training protocol. Daily use of pain killers Glucocorticosteroid injection to the diseased achilles tendon within the last 6 months. Earlier allergic reactions to glucocorticosteroid or local anesthetic. Pregnancy or planning to become pregnant BMI above 30.", "candidate_expression": "((BMI) AND (Daily) AND (Earlier) AND (Glucocorticosteroid) AND (Judged unable to comply with the training protocol.) AND (Leg ulcerations) AND (Pregnancy) AND (above 30) AND (allergic reactions) AND (arthritis) AND (diabetes) AND (diseased achilles tendon) AND (glucocorticosteroid) AND (infections in the foot) AND (injection) AND (local anesthetic) AND (pain killers) AND (planning to become) AND (pregnant) AND (within the last 6 months))"}
{"candidate_id": "LLM04444", "doc_id": "NCT03663387_exc", "case_bucket": "or", "source_criterion": "Uncontrolled hypertension or metabolic disease Neurodegenerative disorders (i.e. Parkinson disease. LBD, or FTD). Dementia or Mild cognitive impairment at baseline Long life major depression. Baseline scores =16 on the 17-item Hamilton Depression Scale at baseline. Long-life DSM-IV axis 1 disorders. Mental retardation. Substance abuse. Concurrent medication limiting validity of neuropsychological tests or imaging. Anti-depressants with anti-cholinergic properties Monoamine oxidase inhibitors (MAOi) Regular use of narcotic analgesics (>2 doses per week). Use of neuroleptics Use of anti-dementia medications (Aricept, Exelon, Razadyne) and memantine (Namenda)) or anti-Parkinsonian medications (Sinemet, amantadine, bromocriptine, pergolide, selegeline). Individuals taking over the counter memory enhancing or protecting medications (e.g. ginkgo biloba, vitamins) are not excluded. Implanted medical devices that are incompatible with MRI imaging. Radiation exposures exceeding annual Rad Worker limits. Heart failure stage D as defined by American Heart Association (7). Chronic kidney disease in stages = 4, as defined per National Kidney Foundation (8). Brain tumor and other neoplastic disorders outside the brain where disease itself or its treatment (radiation, chemotherapy) is likely to affect brain structure or function. Stroke when meeting criteria for total anterior, partial anterior or posterior circulation infarct according to the Oxford Community Stroke Project classification. Patients with clinically silent of lacunar strokes and transient ischemic attacks will not be excluded. Significant head trauma. Hydrocephalus. Hostility or refusal to cooperate", "candidate_expression": "((17-item Hamilton Depression Scale =16 at baseline) AND (Anti-depressants anti-cholinergic properties) AND (Baseline scores) AND (Chronic kidney disease) AND (Heart failure) AND (Hydrocephalus) AND (Long life major depression) AND (Long-life DSM-IV axis 1 disorders) AND (MRI imaging) AND (Mental retardation) AND (Monoamine oxidase inhibitors (MAOi)) AND (Namenda) AND (Neurodegenerative disorders) AND (Oxford Community Stroke Project classification) AND (Radiation exposures exceeding annual Rad Worker limits) AND (Stroke) AND (Substance abuse Concurrent) AND (anti-cholinergic) AND (circulation infarct) AND (cognitive impairment Mild) AND (head trauma Significant) AND (medical devices incompatible with MRI imaging) AND (medication) AND (narcotic analgesics Regular use >2 doses per week) AND (neuroleptics) AND (over the counter memory enhancing medications) AND (over the counter memory protecting medications) AND (stage D American Heart Association) AND (stages = 4 National Kidney Foundation) AND ((hypertension) OR (metabolic disease)) AND ((Dementia) OR (Mild cognitive impairment)) AND ((limiting validity of imaging) OR (limiting validity of neuropsychological tests)) AND ((Aricept) OR (Exelon) OR (Razadyne)) AND ((anti-Parkinsonian medications) OR (anti-dementia medications) OR (memantine)) AND ((Sinemet) OR (amantadine) OR (bromocriptine) OR (pergolide) OR (selegeline)) AND ((ginkgo biloba) OR (vitamins)) AND ((Brain tumor) OR (chemotherapy) OR (neoplastic disorders outside the brain) OR (radiation)) AND ((likely to affect brain function) OR (likely to affect brain structure)) AND ((FTD) OR (LBD) OR (Parkinson disease)) AND ((partial anterior) OR (posterior) OR (total anterior)) AND ((Hostility) OR (refusal to cooperate)))"}
{"candidate_id": "LLM04445", "doc_id": "NCT02785549_inc", "case_bucket": "or", "source_criterion": "Patient's written informed consent. Adequate cognitive capacity. Adequate family support No acute diverticulitis episode in the last 3 months mNeff 0 acute diverticulitis (abdominal computed tomography scan) No antibiotic treatment in the last 2 weeks Immunocompetence* No significant comorbidities** Good oral tolerance Good symptom control Maximum one of the following SIRS criteria (* T>38 ºC or <36ºC, L>12,000 or <4000/uL, HR>90 bpm, RR<20 rpm) or CRP>15 mg/dL", "candidate_expression": "((0) AND (<20 rpm) AND (<36ºC) AND (<4000/uL) AND (>12,000 /uL) AND (>15 mg/dL) AND (>38 ºC) AND (>90 bpm) AND (Adequate family support) AND (Good) AND (Immunocompetence) AND (No) AND (Patient's written informed consent. Adequate cognitive capacity) AND (abdominal computed tomography scan) AND (acute) AND (antibiotic treatment) AND (comorbidities) AND (diverticulitis) AND (in the last 2 weeks) AND (in the last 3 months) AND (mNeff) AND (oral tolerance) AND (significant) AND (symptom control) AND ((HR) OR (L) OR (RR) OR (T)) AND ((CRP) OR (SIRS criteria)))"}
{"candidate_id": "LLM04446", "doc_id": "NCT02254668_inc", "case_bucket": "other", "source_criterion": "Patients with heart transplantation Patient with coronary artery disease Age between 18 and 80 years", "candidate_expression": "((Age between 18 and 80 years) AND (coronary artery disease) AND (heart transplantation))"}
{"candidate_id": "LLM04447", "doc_id": "NCT03337581_inc", "case_bucket": "or", "source_criterion": "selective operation of inguinal hernia repair<U+3001>orthopedics operation or general surgery operation in children aged 3-9 years ASA I - II enter the operating room by himself without parents normal liver and kidney function no history of anesthesia medication allergy.", "candidate_expression": "((3-9 years) AND (ASA) AND (I - II) AND (aged) AND (allergy) AND (anesthesia medication) AND (children) AND (general surgery operation) AND (history) AND (inguinal hernia repair) AND (no) AND (normal kidney function) AND (normal liver function) AND (orthopedics operation))"}
{"candidate_id": "LLM04448", "doc_id": "NCT00543712_inc", "case_bucket": "or", "source_criterion": "Ability to understand and willingness to sign a written informed consent document Age ≥ 18 years Histologic diagnosis of chondrosarcoma, verifiable after enrollment Measurable disease Previously treated or incurable disease without options for standard of care therapy ECOG performance status of 0-2 Life expectancy of > 3 months For patients of reproductive potential (males and females), use of reliable means for contraception (e.g., contraceptive pill, intrauterine device [IUD], physical barrier) throughout the trial and for 1 year following their final exposure to study treatment", "candidate_expression": "((Age ≥ 18 years) AND (ECOG performance status 0-2) AND (Histologic) AND (Life expectancy > 3 months) AND (chondrosarcoma) AND (contraception throughout the trial for 1 year following their final exposure) AND (contraceptive pill) AND (intrauterine device [IUD]) AND (physical barrier) AND (reproductive potential))"}
{"candidate_id": "LLM04449", "doc_id": "NCT03275584_inc", "case_bucket": "other", "source_criterion": "Adult patient being referred for clinically indicated positron emission tomography myocardial perfusion imaging at the Centre hospitalier de l'Université de Montréal", "candidate_expression": "((Adult) AND (Centre hospitalier de l'Université de Montréal) AND (positron emission tomography myocardial perfusion imaging clinically indicated))"}
{"candidate_id": "LLM04450", "doc_id": "NCT03168178_exc", "case_bucket": "or", "source_criterion": "Known fetal anomaly Other indication for intrapartum antibiotics (endocarditis prophylaxis, other known maternal infection)", "candidate_expression": "((fetal anomaly) AND (indication) AND (intrapartum antibiotics) AND ((endocarditis prophylaxis) OR (maternal infection)))"}
```
