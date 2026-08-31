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
{"candidate_id": "LLM04251", "doc_id": "NCT03013790_exc", "case_bucket": "or", "source_criterion": "Patients with head trauma or Neurosurgical intervention Patients <65 years of age Patients with an expected life expectancy <48 hours Blind patients Patients with a seizure history Patients with uncontrolled hypertension Patients with a supratheraputic (>3.0) INR Patients on strong CYP1A2 inhibitors: ciprofloxacin, fluvoxamine, methoxsalen, ofloxacin, primaquine Patients who do not speak English or Spanish", "candidate_expression": "((<48 hours) AND (<65 years) AND (>3.0) AND (Blind) AND (INR) AND (age) AND (expected life expectancy) AND (history) AND (not) AND (seizure) AND (strong CYP1A2 inhibitors) AND (supratheraputic) AND (uncontrolled hypertension) AND ((ciprofloxacin) OR (fluvoxamine) OR (methoxsalen) OR (ofloxacin) OR (primaquine)) AND ((Neurosurgical intervention) OR (head trauma)) AND ((speak English) OR (speak Spanish)))"}
{"candidate_id": "LLM04252", "doc_id": "NCT02299947_inc", "case_bucket": "other", "source_criterion": "Elective surgery for thoracic aneurysm", "candidate_expression": "((Elective surgery) AND (thoracic aneurysm))"}
{"candidate_id": "LLM04253", "doc_id": "NCT02443623_inc", "case_bucket": "other", "source_criterion": "Signed written informed consent. Age 18 to 65. Normal and healthy (immune competent) as determined by medical history, physical exam, vital signs and clinical laboratory tests during the screening period. If all lab results for quantitative IgA immunoglobulin level are lower than 15% below normal range, the subject may not proceed further in the screening process. Subject must meet all required subject suitability criteria that pertain to normal source plasma donors. Negative HIV serology during screening period. Subject must have been previously immunized for smallpox, at =3 years prior to commencement of screening assessments, and vaccination history must be confirmed by oral or written history and the presence of a visible pathognomonic smallpox vaccination scar. Female subjects of childbearing potential must agree to use highly effective birth control methods.", "candidate_expression": "((Age 18 to 65) AND (Female) AND (HIV serology Negative during screening period) AND (Signed written informed consent) AND (birth control methods) AND (childbearing potential) AND (clinical laboratory tests) AND (immunized 3 years prior to commencement of screening assessments) AND (medical history) AND (physical exam) AND (quantitative IgA immunoglobulin level lower than 15% below normal range) AND (smallpox) AND (vital signs))"}
{"candidate_id": "LLM04254", "doc_id": "NCT02137369_exc", "case_bucket": "or", "source_criterion": "Lifetime history of Bipolar Disorder, Dementia, Autism Spectrum Disorder, Schizophrenia, or any other Psychotic Disorder. Psychotic symptoms occurring at any time during the current major depressive episode. Current (past 12 months) diagnosis of Panic disorder, Obsessive Compulsive Disorder, Posttraumatic Stress Disorder, Anorexia Nervosa, or Bulimia Nervosa. Alcohol or Drug Dependence within 12 months or Abuse within 3 months (excluding nicotine and caffeine) of baseline visit, as assessed by history and urine drug screen. Clinical evidence of a severe Personality Disorder, as assessed by the study psychiatrist, which would impede participation or completion of the trial. Known neurological disorders or documented serious head injury. Serious and unstable medical illnesses including cardiovascular disease and cancer. Active medical conditions with known mood changes (endocrine, autoimmune disorders). Current diabetes mellitus. For women, pregnancy, lactation, or unwillingness to comply with birth control requirements. Use of any of the following treatments or any other alternative therapy within 2 weeks of the pre-treatment PET scan that may have beneficial effects on mood, including St John's Wort, S-adenosyl methionine (SAMe), n-3 fatty acids, or light therapy. Use of antidepressant medication within 1 month of the pre-treatment PET scan (within 5 weeks for fluoxetine and protryptyline). Failure to achieve a much improved status (i.e. equivalent to >50% symptom reduction) with any lifetime treatment course of CBT (defined as a minimum of 4 sessions of a specified manual-driven therapy by a CBT-trained therapist) or escitalopram (defined as a minimum of 6 weeks of at least 10 mg/day). Clinically significant active suicidal ideation or self-injurious behavior necessitating immediate treatment, as determined by the investigator. Received electroconvulsive therapy in the past 6 months or during the current depressive episode. Currently responding to medication treatment, without clinical reasons to change. Current treatment with weekly individual or group psychotherapy of any type targeted at depressive symptoms. QTc >500 milliseconds on EKG at screening. Contraindications for MRI, including, but not limited to pacemaker, aneurysm clips, neurostimulators, cochlear implants, metal in eyes, steel worker, intra-uterine devices for birth control. Maintenance or prophylactic therapy for stable medical conditions. Hypnotic medication prescribed or approved by the study physician, (up to a three doses per week) for insomnia, as long if not the night before a PET/MRI or clinic ratings visit. Antipsychotic medications, whether prescribed for sleep or other indications, are prohibited.", "candidate_expression": "((Alcohol Abuse within 3 months) AND (Alcohol Dependence within 12 months) AND (Anorexia Nervosa) AND (Antipsychotic medications) AND (Autism Spectrum Disorder) AND (Bipolar Disorder) AND (Bulimia Nervosa) AND (Contraindications) AND (Dementia) AND (Drug Abuse within 3 months) AND (Drug Dependence within 12 months) AND (EKG at screening) AND (For women, pregnancy, lactation, or unwillingness to comply with birth control requirements) AND (MRI) AND (Obsessive Compulsive Disorder) AND (PET scan pre-treatment) AND (Panic disorder) AND (Personality Disorder severe) AND (Posttraumatic Stress Disorder) AND (Psychotic Disorder) AND (Psychotic symptoms at any time during the current major depressive episode) AND (QTc >500 milliseconds) AND (S-adenosyl methionine) AND (SAMe) AND (Schizophrenia) AND (St John's Wort) AND (alternative therapy) AND (aneurysm clips) AND (antidepressant medication within 1 month of the pre-treatment PET scan within 5 weeks for fluoxetine and protryptyline) AND (autoimmune disorders) AND (caffeine) AND (cancer) AND (cardiovascular disease) AND (cochlear implants) AND (depressive episode current the current depressive episode) AND (depressive symptoms) AND (diabetes mellitus) AND (electroconvulsive therapy in the past 6 months during the current depressive episode) AND (endocrine disorders) AND (fluoxetine) AND (head injury serious Serious unstable) AND (insomnia PET/MRI clinic ratings visit.) AND (intra-uterine devices) AND (light therapy) AND (major depressive episode current) AND (medical illnesses) AND (metal eyes) AND (mood) AND (n-3 fatty acids) AND (neurological disorders) AND (neurostimulators) AND (nicotine) AND (pacemaker) AND (protryptyline) AND (psychotherapy weekly individual group) AND (self-injurious behavior) AND (steel worker) AND (suicidal ideation active) AND (treatment immediate) AND (treatments) AND (urine drug screen) AND NOT (Hypnotic medication the night before a PET/MRI or clinic ratings visit.))"}
{"candidate_id": "LLM04255", "doc_id": "NCT03329456_inc", "case_bucket": "other", "source_criterion": ". Inclusion criteria are American Society of Anesthesiologists (ASA) physical status I-III, age between 18 and 70 years and body mass index (BMI) between 20 and 35 kg/m2.", "candidate_expression": "((ASA) AND (American Society of Anesthesiologists physical status) AND (BMI) AND (I-III) AND (age) AND (between 18 and 70 years) AND (between 20 and 35 kg/m2) AND (body mass index))"}
{"candidate_id": "LLM04256", "doc_id": "NCT03104816_exc", "case_bucket": "or", "source_criterion": "Patients requiring surgery for neoplastic processes Allergy to acetaminophen Liver dysfunction and elevated Liver Function Tests (LFTs) Alcohol or drug dependency Mental retardation Less than 50 kg of weight regnant women Patients requiring long-acting opioid pain management (including fentanyl patch, oxycontin, etc) for over 3 weeks immediately prior to surgery", "candidate_expression": "((Alcohol dependency) AND (Allergy) AND (LFTs) AND (Less than 50 kg) AND (Liver Function Tests) AND (Liver dysfunction) AND (Mental retardation) AND (acetaminophen) AND (drug dependency) AND (elevated) AND (fentanyl patch) AND (for over 3 weeks) AND (immediately prior to surgery) AND (long-acting opioid) AND (neoplastic processes) AND (oxycontin) AND (regnant) AND (requiring) AND (surgery) AND (weight) AND (women))"}
{"candidate_id": "LLM04257", "doc_id": "NCT02901106_inc", "case_bucket": "or", "source_criterion": "patient 18 years old and more with multiple sclerosis according to the criteria of Mac Donald 2010 : relapsing-remitting (RR), secondary-progressive (SP) or primary-progressive (PP) for which treatment with dimethyl-fumarate has been prescribed followed at the Rothschild Foundation in the Neurology Department having given written consent to participation in the study", "candidate_expression": "((PP) AND (RR) AND (Rothschild Foundation in the Neurology Department) AND (SP) AND (and more 18 years) AND (criteria of Mac Donald 2010) AND (dimethyl-fumarate) AND (having given written consent to participation in the study) AND (multiple sclerosis) AND (old) AND (primary-progressive) AND (relapsing-remitting) AND (secondary-progressive))"}
{"candidate_id": "LLM04258", "doc_id": "NCT03149887_inc", "case_bucket": "other", "source_criterion": "Adult patients up to age 75 years, undergoing elective, ambulatory, arthroscopic rotator cuff repair.", "candidate_expression": "((Adult) AND (age up to 75 years) AND (ambulatory) AND (arthroscopic rotator cuff repair elective))"}
{"candidate_id": "LLM04259", "doc_id": "NCT02632318_exc", "case_bucket": "other", "source_criterion": "Regular cigarette smoker Alcohol abuse Drug abuse", "candidate_expression": "((Alcohol abuse) AND (Drug abuse) AND (Regular cigarette smoker))"}
{"candidate_id": "LLM04260", "doc_id": "NCT02777424_exc", "case_bucket": "other", "source_criterion": "Concomitant use with oral anticoagulant drugs Acquired deficiency of coagulation factors whose treatment is established Hypersensitivity to a PCC History of thrombocytopenia induced by heparin Disseminated intravascular coagulation Extracranial active bleeding Hypersensitivity to vitamin K", "candidate_expression": "((Acquired deficiency of coagulation factors) AND (Concomitant) AND (Disseminated intravascular coagulation) AND (Extracranial bleeding) AND (Hypersensitivity) AND (PCC) AND (active) AND (heparin) AND (oral anticoagulant drugs) AND (thrombocytopenia) AND (vitamin K) AND (whose treatment is established))"}
{"candidate_id": "LLM04261", "doc_id": "NCT02905734_inc", "case_bucket": "other", "source_criterion": "Arrestees examined by a physician during detention in police cells aged 18 or older smoking at least 10 cigarettes per day giving written consent to participate in the study health status compatible with detention in police cells", "candidate_expression": "((Arrestees) AND (aged 18 or older) AND (examined by a physician during detention in police cells) AND (giving written consent to participate in the study) AND (health status compatible with detention in police cells) AND (smoking at least 10 cigarettes per day))"}
{"candidate_id": "LLM04262", "doc_id": "NCT03034733_inc", "case_bucket": "other", "source_criterion": "primary total knee replacement surgery ASA (american society of anesthesiologists) class 1-3", "candidate_expression": "((ASA class 1-3) AND (american society of anesthesiologists) AND (total knee replacement surgery primary))"}
{"candidate_id": "LLM04263", "doc_id": "NCT01602081_exc", "case_bucket": "or", "source_criterion": "Patients with prior fistulotomy, fistulectomy, LIFT, cutting seton or advancement flap procedure Fistula with multiple tracts Recto-vaginal fistula Active infection in the anal fistula Physical allergies or cultural objections to porcine products Patient is not medically fit to undergo the LIFT procedure as judged by the treating physician Previous diagnosis of collagen disorder History of Crohn's Disease, Irritable Bowel Syndrome, radiation therapy in the rectoanal region", "candidate_expression": "((Fistula) AND (History) AND (LIFT) AND (Patient is not medically fit to undergo the LIFT procedure as judged by the treating physician) AND (Recto-vaginal fistula) AND (advancement flap procedure) AND (anal fistula) AND (collagen disorder) AND (cutting seton) AND (fistulectomy) AND (fistulotomy) AND (infection in the anal fistula) AND (multiple tracts) AND (rectoanal region) AND ((Crohn's Disease) OR (Irritable Bowel Syndrome) OR (radiation therapy)))"}
{"candidate_id": "LLM04264", "doc_id": "NCT03260881_inc", "case_bucket": "or", "source_criterion": "T2DM as defined by American Diabetes Association (ADA) criteria Adult patients with T2DM who are indicated to receive liraglutide, not as first-line therapy, in addition to diet and exercise to improve glycemic control Hemoglobin A1c (HbA1c) = 9% Age = 18 years old Body mass index (BMI) = 27 Kg/m2 and/or waist circumference = 102 cm (40 inches) in men and 88 cm (35 inches) in women, respectively. Clinically and angiographically stable CAD who requires CABG as part of the standard medical care, as CAD does not represent a contraindication for using liraglutide. The stability of the CAD further warranties that study patients will not be exposed to higher risk by using liraglutide", "candidate_expression": "((35 inches) AND (40 inches) AND (88 cm) AND (= 102 cm) AND (= 18 years old) AND (= 27 Kg/m2) AND (= 9%) AND (Adult) AND (Age) AND (American Diabetes Association (ADA) criteria) AND (CABG) AND (CAD) AND (Clinically stable) AND (Hemoglobin A1c (HbA1c)) AND (T2DM) AND (angiographically stable) AND (first-line therapy) AND (indicated to receive) AND (liraglutide) AND (not) AND (requires) AND ((Body mass index (BMI)) OR (waist circumference)) AND ((men) OR (women)))"}
{"candidate_id": "LLM04265", "doc_id": "NCT03364036_inc", "case_bucket": "or", "source_criterion": "Highly active RMS as defined by: One relapse in the previous year and at least 1 T1 Gadolinium (Gd)+ lesion or 9 or more T2 lesions, while on therapy with other disease modifying drugs (DMDs) Two or more relapses in the previous year, whether on DMD treatment or not. Expanded Disability Status Scale (EDSS) score less than equals to (<=) 5.0. Other protocol defined inclusion criteria could apply.", "candidate_expression": "((Expanded Disability Status Scale (EDSS) score less than equals to (<=) 5.0) AND (Other protocol defined inclusion criteria could apply.) AND (RMS Highly active) AND (T2 lesions 9 or more) AND (disease modifying drugs (DMDs) other) AND (lesion at least 1 T1 Gadolinium (Gd)+) AND (relapse One in the previous year) AND (relapses Two or more in the previous year) AND (therapy))"}
{"candidate_id": "LLM04266", "doc_id": "NCT03260881_exc", "case_bucket": "or", "source_criterion": "Patients with a personal or family history of medullary thyroid carcinoma or patients with Multiple Endocrine Neoplasia syndrome type 2 Patients with a prior serious hypersensitivity reaction to liraglutide Other contra-indications to liraglutide in accordance with risks and safety information included in the latest updated prescribing information Type 1 diabetes, as defined by ADA criteria Current use of other GLP-1A, dipeptidyl peptidase 4 (DPP4) or Sodium Glucose transporters 2 (SGLT2) inhibitors, thiazolidinediones (TZDs), pramlintide and fixed prandial insulin. Patients with unstable CAD, assessed by the Cardiology team and defined as new onset angina, rest angina, rapidly increasing or crescendo angina History of diabetic ketoacidosis, pancreas or beta-cell transplantation, or diabetes secondary to pancreatitis or pancreatectomy; acute or chronic infective diseases, cancer or chemotherapy, history of pulmonary, renal or liver diseases, and drug abuse Patients with chronic and acute inflammatory conditions such as sepsis, rheumatoid arthritis, ectopic dermatitis, asthma, ulcerative colitis. Current use of systemic corticosteroids in the 3 months prior this study. Pregnant or breast-feeding women Females of childbearing potential who are not using adequate contraceptive methods (as required by local law or practice)", "candidate_expression": "((Females of childbearing potential who are not using adequate contraceptive methods (as required by local law or practice)) AND (Type 1 diabetes ADA criteria) AND (contra-indications Other) AND (hypersensitivity reaction prior serious) AND (inflammatory conditions) AND (liraglutide) AND (systemic corticosteroids Current in the 3 months prior this study) AND (unstable CAD) AND ((GLP-1A other) OR (Sodium Glucose transporters 2 (SGLT2) inhibitors) OR (dipeptidyl peptidase 4 (DPP4) inhibitors) OR (pramlintide) OR (prandial insulin) OR (thiazolidinediones (TZDs))) AND ((family history) OR (personal history)) AND ((crescendo angina) OR (new onset angina) OR (rapidly increasing angina) OR (rest angina)) AND ((beta-cell transplantation) OR (cancer) OR (chemotherapy) OR (diabetes secondary to) OR (diabetic ketoacidosis) OR (drug abuse) OR (infective diseases) OR (liver diseases) OR (pancreas transplantation) OR (pulmonary diseases) OR (renal diseases)) AND ((pancreatectomy) OR (pancreatitis)) AND ((acute) OR (chronic)) AND ((Multiple Endocrine Neoplasia syndrome type 2) OR (medullary thyroid carcinoma)) AND ((asthma) OR (ectopic dermatitis) OR (rheumatoid arthritis) OR (sepsis) OR (ulcerative colitis)) AND ((Pregnant) OR (breast-feeding women)))"}
{"candidate_id": "LLM04267", "doc_id": "NCT01642875_exc", "case_bucket": "or", "source_criterion": "Metastatic tumor Locally unresectable tumor Previous gastric resection ASA IV-V Age under 18 years Preoperative complete parenteral or enteral feeding Immunosuppressive therapy before operation Severe malnutrition Lack of the patient's consent for the trial participation, feeding tube insertion or epidural analgesia", "candidate_expression": "((ASA IV-V) AND (Age under 18 years) AND (Immunosuppressive therapy before operation) AND (Lack of the patient's consent for the trial participation, feeding tube insertion or epidural analgesia) AND (gastric resection Previous) AND (malnutrition Severe) AND (operation) AND (tumor) AND (tumor Metastatic Locally unresectable) AND ((complete enteral feeding) OR (complete parenteral feeding)))"}
{"candidate_id": "LLM04268", "doc_id": "NCT02894645_inc", "case_bucket": "other", "source_criterion": "Confirmed diagnosis of non-Burkitt B-lineage ALL 1 to 17 years of age (before 18th birthday) Renal function within normal range for age Liver function within normal range for age Able to participate in the full 2 years of treatment", "candidate_expression": "((1 to 17 years) AND (Able to participate) AND (Confirmed) AND (Liver function) AND (Renal function) AND (age) AND (full 2 years) AND (non-Burkitt B-lineage ALL) AND (treatment) AND (within normal range for age))"}
{"candidate_id": "LLM04269", "doc_id": "NCT03122119_exc", "case_bucket": "or", "source_criterion": "Patients under the age of 18 (Subjects under the age of 18 will not be included in this study due to the continued growth and development of their joints and unstudied effects on children.) Over the age of 80 Multiple pain sources and multifactorial pain sources that complicated or confound diagnosing the SI joint as the primary and predominant pain generator that may contribute to low back pain (including but not limited to: lumbar diagnosis, lumbar radiculopathy, intra or extra-articular hip pathology to include acetabulum and femoral head, lumbo-sacral joint pathology, intervertebral disk disease, spondylolisthesis/spondylosis/spondylolysis of lumbar vertebra) Immunosuppressed/immune compromised Underlying comorbidities that contraindicate the procedure (including but not limited to polycythemia, coagulation disorder, or malignancy).", "candidate_expression": "((18 under) AND (Immunosuppressed) AND (Multiple pain sources) AND (Over 80) AND (Underlying comorbidities) AND (acetabulum pathology) AND (age) AND (coagulation disorder) AND (contraindicate) AND (contraindicate the procedure) AND (extra-articular hip pathology) AND (femoral head pathology) AND (immune compromised) AND (intervertebral disk disease) AND (intra -articular hip pathology) AND (lumbar diagnosis) AND (lumbar radiculopathy) AND (lumbo-sacral joint pathology) AND (malignancy) AND (multifactorial pain sources) AND (polycythemia) AND (procedure) AND (spondylolisthesis) AND (spondylolysis of lumbar vertebra) AND (spondylosis))"}
{"candidate_id": "LLM04270", "doc_id": "NCT03463564_exc", "case_bucket": "or", "source_criterion": "previous use of insulin pump pregnancy or planning to become pregnant in the next 2 years, lack of ability to use the study devices history of severe chronic diseases recent or concomitant use of corticosteroids drug or alcohol abuse psychiatric complaints that interfere with the correct use of the devices", "candidate_expression": "((alcohol abuse) AND (chronic diseases history severe recent concomitant) AND (corticosteroids) AND (drug abuse) AND (insulin pump) AND (pregnancy) AND (pregnant planning to become) AND (psychiatric complaints correct use of the devices) AND (study devices) AND NOT (ability to use the study devices))"}
{"candidate_id": "LLM04271", "doc_id": "NCT03555526_exc", "case_bucket": "or", "source_criterion": "aged less than 20 years history of gastric resection surgery history of allergy to study drugs pregnancy or lactating women severe underlying illness, such as end stage renal disease, decompensated liver cirrhosis, or non-curative malignancy", "candidate_expression": "((aged) AND (allergy) AND (decompensated) AND (end stage renal disease) AND (gastric resection surgery) AND (lactating) AND (less than 20 years) AND (liver cirrhosis) AND (malignancy) AND (non-curative) AND (pregnancy) AND (severe underlying illness) AND (study drugs) AND (women))"}
{"candidate_id": "LLM04272", "doc_id": "NCT01518946_inc", "case_bucket": "or", "source_criterion": "1. Male and female subjects must be 18 years of age or older and ambulatory. 2. Females of child-bearing potential (FOCP) must have a negative serum beta human chorionic gonadotropin (HCG) pregnancy test. 3. A documented history of severe Symptomatic Orthostatic Hypotension (SOH) that, in the judgment of the treating physician, has required treatment with midodrine HCl , and has been at a stable dose for at least 3 months. 4. The subject has manifested at least 1 of the following symptoms while standing or had a medical history of 1 of the following when not treated for orthostatic hypotension (OH): dizziness, lightheadedness, feeling faint, or feeling like they might black out.", "candidate_expression": "((Females) AND (Symptomatic Orthostatic Hypotension (SOH) severe) AND (age 18 years or older) AND (ambulatory) AND (at least 1) AND (child-bearing potential) AND (dizziness) AND (feeling faint) AND (feeling like they might black out) AND (lightheadedness) AND (midodrine HCl stable dose) AND (orthostatic hypotension (OH)) AND (serum beta human chorionic gonadotropin (HCG) pregnancy test negative) AND NOT (treated) AND ((Male) OR (female)))"}
{"candidate_id": "LLM04273", "doc_id": "NCT02369211_inc", "case_bucket": "other", "source_criterion": "Patients undergoing robotic-assisted laparoscopic prostatectomy =18 years old males ASA class 1-4", "candidate_expression": "((ASA class 1-4) AND (males) AND (obotic-assisted laparoscopic prostatectomy) AND (years =18 years old))"}
{"candidate_id": "LLM04274", "doc_id": "NCT02637453_exc", "case_bucket": "or", "source_criterion": "With acute diseases, such as acute phase after myocardial infarction (within 3 months), within 3 months after acute heart failure or new cerebral infarction; In the list of heart transplantation; Expected survival less than 1 year; With other hemorrhagic diseases and anticoagulant therapy is not allowed; Thrombosis in left atrium; Heart failure, New York Heart Association(NYHA) III/IV or eject fraction(EF)<40%; Patients with uncontrolled cancer; Significant hepatic or renal impairment (and/or alanine transaminase(ALT) or Aspartate transaminase(AST) >2 times upper limit of normal, creatinine clearance rate(CCr)<50%); Previous catheter radiofrequency ablation for AF or cardiac surgery; Pregnant and lactating women, women who plan to become pregnant, or women of child bearing age not using reliable contraceptive measures.", "candidate_expression": "((AF) AND (Aspartate transaminase(AST) >2 times upper limit of normal) AND (Expected survival less than 1 year) AND (Heart failure) AND (New York Heart Association(NYHA) III/IV) AND (Pregnant and lactating women, women who plan to become pregnant, or women of child bearing age not using reliable contraceptive measures.) AND (Thrombosis left atrium) AND (acute diseases) AND (acute heart failure) AND (alanine transaminase(ALT)) AND (anticoagulant therapy) AND (cancer uncontrolled) AND (cardiac surgery) AND (catheter radiofrequency ablation) AND (cerebral infarction) AND (creatinine clearance rate(CCr) <50%) AND (eject fraction(EF) <40%) AND (heart transplantation In the list) AND (hemorrhagic diseases other) AND (hepatic impairment) AND (myocardial infarction acute phase within 3 months) AND (not allowed) AND (renal impairment))"}
{"candidate_id": "LLM04275", "doc_id": "NCT03182114_exc", "case_bucket": "other", "source_criterion": "Cardiac morbidities hypertensive disorders of pregnancy peripartum bleeding baseline systolic blood pressure (SBP) < 100 mmHg body mass index > 35", "candidate_expression": "((< 100 mmHg) AND (> 35) AND (Cardiac morbidities) AND (SBP) AND (baseline) AND (body mass index) AND (hypertensive disorders of pregnancy) AND (peripartum bleeding) AND (systolic blood pressure))"}
```
