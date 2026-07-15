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
{"candidate_id": "LLM00926", "doc_id": "NCT02511574_exc", "case_bucket": "other", "source_criterion": "no confirmation of the gestational age ruptured membranes painful regular uterine contractions major fetal abnormalities", "candidate_expression": "((fetal abnormalities) AND (gestational age) AND (major) AND (no) AND (painful regular uterine contractions) AND (ruptured membranes))"}
{"candidate_id": "LLM00927", "doc_id": "NCT02247128_inc", "case_bucket": "other", "source_criterion": "Need for long-term oral anticoagulation; Patient has provided written informed consent.", "candidate_expression": "((Patient has provided written informed consent) AND (long-term oral anticoagulation Need for))"}
{"candidate_id": "LLM00928", "doc_id": "NCT02579928_inc", "case_bucket": "or", "source_criterion": "MDD Cohort: Meet DSM-5 criteria for Major Depressive Disorder by structured interview (MINI-KID); CDRS-R score >40; Failure to achieve remission with at least 1 adequate prior antidepressant trial (e.g. SSRI, SNRI, or TCA), meaning at least 8 weeks at therapeutic dosing, including at least 4 weeks of stable dosing. Anxiety Cohort: Meet DSM-5 criteria for any of the following anxiety disorders: Social Anxiety Disorders, Generalized Anxiety Disorder, Separation Anxiety Disorder and/or Panic Disorder by structured interview (MINI-KID); ADIS Clinical Severity Rating ≥4 (moderately severe) for any of the 4 included anxiety disorders; Failure to achieve remission with at least 1 adequate prior anxiolytic medication trial (e.g. SSRI, SNRI, or TCA), meaning at least 8 weeks at therapeutic dosing, including at least 4 weeks of stable dosing; Failure to achieve remission with previous CBT or subject declines current CBT therapy Stable psychiatric medications and doses for the month prior to enrollment. Subjects may continue to engage in any ongoing psychotherapy. Medically and neurologically healthy on the basis of physical examination and medical history. Parents able to provide written informed consent and adolescents must additionally provide assent.", "candidate_expression": "((>40) AND (ADIS Clinical Severity Rating) AND (Anxiety Cohort) AND (CBT therapy) AND (CDRS-R score) AND (DSM-5 criteria) AND (Failure) AND (Generalized Anxiety Disorder) AND (MDD Cohort) AND (MINI-KID) AND (Major Depressive Disorder) AND (Medically healthy) AND (Panic Disorder) AND (Parents) AND (SNRI) AND (SSRI) AND (Separation Anxiety Disorder) AND (Social Anxiety Disorders) AND (Stable) AND (Stable doses) AND (TCA) AND (adequate) AND (adolescents) AND (antidepressant) AND (antidepressant trial) AND (anxiety disorders) AND (anxiolytic medication) AND (anxiolytic medication trial) AND (at least 1) AND (at least 4 weeks) AND (at least 8 weeks) AND (current) AND (enrollment) AND (for the month prior to enrollment) AND (medical history) AND (moderately severe) AND (neurologically healthy) AND (physical examination) AND (previous) AND (prior) AND (provide assent) AND (provide written informed consent) AND (psychiatric medications) AND (remission) AND (stable dosing) AND (structured interview) AND (subject declines) AND (therapeutic dosing) AND (≥4))"}
{"candidate_id": "LLM00929", "doc_id": "NCT02478346_inc", "case_bucket": "or", "source_criterion": "Adult patients (age = 18) Diagnosed by preoperative imaging modalities to have a brain tumor (including metastatic brain tumors) or vascular lesions (aneurysm, arteriovenous malformation or arteriovenous fistula) requiring surgical intervention. The patient is determined by a board certified neurosurgeon to have a tumor or vascular lesion that would take up fluorescein Patient or legally authorized representative provides written informed consent to enroll in this study", "candidate_expression": "((= 18) AND (Adult) AND (Patient or legally authorized representative provides written informed consent to enroll in this study) AND (age) AND (aneurysm) AND (arteriovenous fistula) AND (arteriovenous malformation) AND (brain tumor) AND (fluorescein) AND (imaging modalities) AND (metastatic brain tumors) AND (preoperative) AND (surgical intervention) AND (vascular lesions) AND (would take up fluorescein) AND ((tumor) OR (vascular lesion)))"}
{"candidate_id": "LLM00930", "doc_id": "NCT01765231_inc", "case_bucket": "other", "source_criterion": "treatment-naive patients with lymphoma HBsAg negative/HBcAb positive/hepatitis B virus DNA negative at baseline treated with chemotherapy and/or immunosuppressive therapy life expectancy of more than 3 months", "candidate_expression": "((HBcAb positive) AND (HBsAg negative) AND (chemotherapy) AND (hepatitis B virus DNA negative) AND (immunosuppressive therapy) AND (life expectancy more than 3 months) AND (lymphoma) AND (treatment-naive))"}
{"candidate_id": "LLM00931", "doc_id": "NCT00787254_exc", "case_bucket": "or", "source_criterion": "Endoscopically confirmed gastric and/or duodenal ulcers on Day 1. Endoscopically confirmed active upper gastrointestinal hemorrhage on Day 1. Current or past history of aspirin-induced asthma or hypersensitivity to NSAIDs. Past or planned surgery affecting gastric acid secretion. Clinically significant hepatic or renal disorder. Serious cardiac dysfunction, hypertension, or hematological disorder.", "candidate_expression": "((Clinically significant) AND (Endoscopically) AND (Endoscopically Day 1) AND (NSAIDs Past planned) AND (Serious) AND (aspirin) AND (surgery affecting gastric acid secretion) AND (upper gastrointestinal hemorrhage Endoscopically confirmed active on Day 1 Day 1) AND ((duodenal ulcers) OR (gastric)) AND ((asthma aspirin-induced) OR (hypersensitivity to NSAIDs)) AND ((Current) OR (past history)) AND ((hepatic disorder) OR (renal disorder)) AND ((cardiac dysfunction) OR (hematological disorder) OR (hypertension)))"}
{"candidate_id": "LLM00932", "doc_id": "NCT03029078_exc", "case_bucket": "or", "source_criterion": "Pregnant woman or breastfeeding immunosuppression including AIDS, corticosteroids over 60mg/day ongoing antibiotic treatment at the day of inclusion impossibility to obtain a signed consent form.", "candidate_expression": "((antibiotic) AND (at the day of inclusion) AND (day of inclusion) AND (immunosuppression) AND (impossibility to obtain) AND (over 60mg/day) AND (signed consent form) AND (treatment) AND (woman) AND ((Pregnant) OR (breastfeeding)) AND ((AIDS) OR (corticosteroids)))"}
{"candidate_id": "LLM00933", "doc_id": "NCT02222272_exc", "case_bucket": "other", "source_criterion": "", "candidate_expression": "(EMPTY)"}
{"candidate_id": "LLM00934", "doc_id": "NCT03193684_exc", "case_bucket": "or", "source_criterion": "eGFR <60 T2DM patients on insulin, GLP-1 RA or SGLT2 treatment Major organ disease type 1 diabetes", "candidate_expression": "((GLP-1) AND (Major organ disease) AND (RA) AND (SGLT2) AND (T2DM) AND (eGFR <60) AND (insulin) AND (type 1 diabetes))"}
{"candidate_id": "LLM00935", "doc_id": "NCT02872935_exc", "case_bucket": "other", "source_criterion": "Non- English speakers Height < 4' 11\" BMI >40 Kg/ mm Antiemetic drug use in the 24 hours prior to cesarean delivery, Hypertensive diseases of pregnancy Chronic hypertension receiving antihypertensive treatment Any other physical or psychiatric condition that may impair their ability to cooperate with study data collection.", "candidate_expression": "((Antiemetic drug in the 24 hours prior to cesarean delivery) AND (Any other physical or psychiatric condition that may impair their ability to cooperate with study data collection.) AND (BMI >40 Kg/ mm) AND (Chronic hypertension) AND (Height < 4' 11\") AND (Hypertensive diseases of pregnancy) AND (Non- English speakers) AND (antihypertensive treatment) AND (cesarean delivery))"}
{"candidate_id": "LLM00936", "doc_id": "NCT01997580_inc", "case_bucket": "or", "source_criterion": "DSM-IV-TR major depressive disorder aged between 20 and 80 durg-naive or drug-free", "candidate_expression": "((DSM-IV-TR) AND (aged) AND (between 20 and 80) AND (drug) AND (durg) AND (free) AND (major depressive disorder) AND (naive))"}
{"candidate_id": "LLM00937", "doc_id": "NCT02777424_exc", "case_bucket": "other", "source_criterion": "Concomitant use with oral anticoagulant drugs Acquired deficiency of coagulation factors whose treatment is established Hypersensitivity to a PCC History of thrombocytopenia induced by heparin Disseminated intravascular coagulation Extracranial active bleeding Hypersensitivity to vitamin K", "candidate_expression": "((Acquired deficiency of coagulation factors) AND (Concomitant) AND (Disseminated intravascular coagulation) AND (Extracranial bleeding) AND (Hypersensitivity) AND (PCC) AND (active) AND (heparin) AND (oral anticoagulant drugs) AND (thrombocytopenia) AND (vitamin K) AND (whose treatment is established))"}
{"candidate_id": "LLM00938", "doc_id": "NCT02321202_exc", "case_bucket": "or", "source_criterion": "Contraindication for hepatectomy, including gastrointestinal hemorrhage, severe hemorrhagic disorders, explicit acute nonspecific infectious lesion, overt ascites, Child-Pugh Score C, indocyanine green retention rate at 15min (ICGR15)＞30%(12), serum hepatitis B virus (HBV)-DNA＞126 copies/ml and serum alanine aminotransferase (ALT) ＞ 2×ULN, serum triglycerides＞2.0 mmol/L, circulatory shock, stroke, acute myocardial infarction, renal failure, coma of unknown cause Pregnancy Age of＜18y or＞75y Performed intraoperative ablation Unresectable tumor during operation Allergic reactions against fish or egg proteins", "candidate_expression": "((Age ＜18y or＞75y) AND (Allergic reactions) AND (Contraindication for hepatectomy) AND (Pregnancy) AND (Unresectable tumor) AND (hepatectomy) AND (intraoperative ablation) AND ((Child-Pugh Score C) OR (acute myocardial infarction) OR (ascites overt) OR (circulatory shock) OR (coma unknown cause) OR (gastrointestinal hemorrhage) OR (hemorrhagic disorders severe) OR (indocyanine green retention rate at 15min (ICGR15) ＞30%) OR (infectious lesion acute nonspecific) OR (renal failure) OR (serum alanine aminotransferase (ALT) ＞ 2×ULN) OR (serum hepatitis B virus (HBV)-DNA ＞126 copies/ml) OR (serum triglycerides ＞2.0 mmol/L) OR (stroke)) AND ((egg proteins) OR (fish proteins)))"}
{"candidate_id": "LLM00939", "doc_id": "NCT02996916_inc", "case_bucket": "or", "source_criterion": "Written informed consent obtained Male and female subjects aged 20 years or older at informed consent Essential hypertension who had never received angiotensin II receptor antagonists and calcium channel blockers", "candidate_expression": "((Essential hypertension) AND (Written informed consent obtained) AND (aged 20 years or older at informed consent) AND ((Male) OR (female)) AND ((angiotensin II receptor antagonists) OR (calcium channel blockers)))"}
{"candidate_id": "LLM00940", "doc_id": "NCT02680054_exc", "case_bucket": "other", "source_criterion": "HbA1c greater than 75 mmol/mol (9.0%) Child unwilling to agree to second insulin injection at a meal-time Untreated coeliac disease or other concomitant condition likely to affect BG control Food allergies (other than controlled Coeliac Disease) Vegetarians, vegans or patients with religious dietary restrictions (as the standard meal contains meat) Participant taking any glucose-containing medication concurrently", "candidate_expression": "((9.0%) AND (Child unwilling to agree to second insulin injection at a meal-time) AND (Coeliac Disease) AND (Food allergies) AND (HbA1c) AND (Untreated) AND (Vegetarians) AND (coeliac disease) AND (glucose-containing medication) AND (greater than 75 mmol/mol) AND (other))"}
{"candidate_id": "LLM00941", "doc_id": "NCT02226887_exc", "case_bucket": "or", "source_criterion": "Patients under 18 Pregnancy and Lactation Patients allergic to polyglycolic / trimethylene carbonate Carrier of prosthetic mesh in the ostomy Patients presenting midline hernia. Patients affected by inflammatory bowel disease", "candidate_expression": "((Lactation) AND (Pregnancy) AND (allergic) AND (inflammatory bowel disease) AND (midline hernia) AND (ostomy) AND (polyglycolic carbonate) AND (prosthetic mesh) AND (trimethylene carbonate) AND (under 18))"}
{"candidate_id": "LLM00942", "doc_id": "NCT03091881_exc", "case_bucket": "or", "source_criterion": "Contraindications for spinal anesthesia (like bleeding diathesis or regional infection at site of neuroaxial block) Known allergy to Granisetron or local anaesthetic (heavy bupivacaine, Marcaine Spinal 0.5% Heavy, 5mg/ml, AstraZeneca ampule) Pregnancy induced hypertension Congenital or rheumatic heart diseases Antepartum haemorrhage Fetal destress or gestational age < 36 week", "candidate_expression": "((5mg/ml) AND (< 36 week) AND (Antepartum haemorrhage) AND (AstraZeneca ampule) AND (Contraindications) AND (Marcaine Spinal 0.5% Heavy) AND (Pregnancy) AND (Pregnancy induced) AND (allergy) AND (heart diseases) AND (heavy bupivacaine) AND (hypertension) AND (site of neuroaxial block) AND (spinal anesthesia) AND ((Congenital) OR (rheumatic)) AND ((Fetal destress) OR (gestational age)) AND ((bleeding diathesis) OR (regional infection)) AND ((Granisetron) OR (local anaesthetic)))"}
{"candidate_id": "LLM00943", "doc_id": "NCT00806936_exc", "case_bucket": "or", "source_criterion": "Known or suspected allergy to trial product(s) or related products Subjects who are unlikely to comply with protocol requirements, e.g. uncooperative attitude, inability to return for the final visit Subjects who previously enrolled in this study Females of childbearing potential who are pregnant, breast-feeding or intend to become pregnant or are not using adequate contraceptive methods The receipt of any investigational product within 3 months prior to this trial", "candidate_expression": "((Females) AND (Females of childbearing potential who are pregnant, breast-feeding or intend to become pregnant or are not using adequate contraceptive methods) AND (Subjects who are unlikely to comply with protocol requirements, e.g. uncooperative attitude, inability to return for the final visit) AND (Subjects who previously enrolled in this study) AND (allergy related products) AND (allergy to trial product(s)) AND (breast-feeding intend to become) AND (childbearing potential) AND (contraceptive methods adequate) AND (investigational product within 3 months prior to this trial this trial) AND (pregnant) AND (related products) AND (trial product(s)))"}
{"candidate_id": "LLM00944", "doc_id": "NCT02990403_inc", "case_bucket": "other", "source_criterion": "Woman who had 2 miscarriage before 12(th) week of gestation.The patient who is diagnosed as thrombophilia with recurrent pregnancy loss. Signed consent form.", "candidate_expression": "((12(th) week of gestation) AND (2) AND (Signed consent form.) AND (Woman) AND (before 12(th) week of gestation) AND (miscarriage) AND (pregnancy loss) AND (recurrent) AND (thrombophilia))"}
{"candidate_id": "LLM00945", "doc_id": "NCT03495609_inc", "case_bucket": "other", "source_criterion": "premenopausal women BRCA1 carrier", "candidate_expression": "((BRCA1 carrier) AND (premenopausal) AND (women))"}
{"candidate_id": "LLM00946", "doc_id": "NCT03335904_exc", "case_bucket": "other", "source_criterion": "history of hypertension known impaired renal function liver disease heart failure myocardial infarction coronary artery disease smoked within the past year apnea hypopnea index > 5 events per hour", "candidate_expression": "((> 5 events per hour) AND (apnea hypopnea index) AND (coronary artery disease) AND (heart failure) AND (history) AND (hypertension) AND (impaired renal function) AND (liver disease) AND (myocardial infarction) AND (smoked) AND (within the past year))"}
{"candidate_id": "LLM00947", "doc_id": "NCT02019628_exc", "case_bucket": "or", "source_criterion": "1. Currently enrolled in another research trial for investigative nutritional or other therapies thought to have an impact on immune system functioning. 2. Unable to consent to the study. 3. Women who are pregnant or are attempting conception, especially in the presence of a history of recurrent spontaneous abortion. 4. Other medical complications that might preclude one from participating in the study, i.e., recent heart attack or stroke or chronic kidney disease. 5. Currently taking immunomodulatory medication, i.e. interferon. 6. Currently taking other medications thought to have an impact on immune system functioning, i.e., chemotherapeutic agents. 7. Known allergy to rice, rice bran, or related food products. 8. Known allergy to mushrooms or related food products. 9. History of malignancies related to the NK cell line, including: NK cell leukemias and T-cell large granular lymphocyte leukemias, NK-cell lymphoproliferative disease of granular lymphocytes, and NK cell lymphomas, e.g., nasal and nasal-like NK/T-cell lymphomas. 10. Current smoker.", "candidate_expression": "((Currently enrolled in another research trial for investigative nutritional or other therapies thought to have an impact on immune system functioning.) AND (NK cell leukemias) AND (NK cell lymphomas) AND (NK-cell lymphoproliferative disease of granular lymphocytes) AND (T-cell large granular lymphocyte leukemias) AND (Unable to consent to the study.) AND (Women) AND (allergy to food products) AND (allergy to mushrooms) AND (allergy to rice) AND (allergy to rice bran) AND (chemotherapeutic agents) AND (chronic kidney disease) AND (heart attack recent) AND (immunomodulatory medication) AND (interferon) AND (malignancies related to the NK cell line) AND (medical complications Other) AND (medications other impact on immune system functioning) AND (nasal NK/T-cell lymphomas) AND (nasal-like NK/T-cell lymphomas) AND (pregnant) AND (rice) AND (rice bran) AND (smoker Current) AND (spontaneous abortion recurrent) AND (stroke) AND NOT (participating in the study))"}
{"candidate_id": "LLM00948", "doc_id": "NCT02613039_inc", "case_bucket": "other", "source_criterion": "Female subjects aged =/> 18 years and of reproductive age. Capacity to give consent for study participation, after being adequately informed of the aims, benefits, risks, time and motion of the study.", "candidate_expression": "((Female) AND (aged =/> 18 years) AND (reproductive age))"}
{"candidate_id": "LLM00949", "doc_id": "NCT03477851_inc", "case_bucket": "other", "source_criterion": "Patients with foot fracture scheduled for surgical repair in spinal anesthesia Informed consent", "candidate_expression": "((Informed consent) AND (foot fracture) AND (scheduled for) AND (spinal anesthesia) AND (surgical repair))"}
{"candidate_id": "LLM00950", "doc_id": "NCT03473132_exc", "case_bucket": "other", "source_criterion": "recent thrombotic event", "candidate_expression": "(thrombotic event recent)"}
```
