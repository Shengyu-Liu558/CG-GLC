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
{"candidate_id": "LLM00426", "doc_id": "NCT03420638_exc", "case_bucket": "or", "source_criterion": "Presence of severe systemic disease Presence of coagulation disorders Current or previous history of analgesic dependence Allergy to any of the drugs used in the study Women pregnant or lactating, or women planning to become pregnant Presence of hearing loss Presence of cardiovascular comorbidities Presence of hepatic comorbidities Presence of kidney comorbidities Presence of cognitive disabilities", "candidate_expression": "((Allergy) AND (Women) AND (analgesic) AND (analgesic dependence history) AND (cardiovascular comorbidities) AND (coagulation disorders) AND (cognitive disabilities) AND (drugs used in the study) AND (hearing loss) AND (hepatic comorbidities) AND (kidney comorbidities) AND (systemic disease severe) AND (women) AND ((lactating) OR (pregnant) OR (pregnant planning to become)) AND ((Current) OR (previous)))"}
{"candidate_id": "LLM00427", "doc_id": "NCT02399033_inc", "case_bucket": "or", "source_criterion": "Age: 20-70 years old; Gender: male or female; clinical or pathological diagnosis of hepatocellular carcinoma (HCC) in previously untreated patients; The expected survival> 3 months; Child-Pugh grade in A-level; KPS score with 50-100 points; BCLC stage of 0-B; conform to the indications of hepatectomy; Viable tumor resection confirmed by two highly qualified surgical doctors; No other surgical contraindications. women in the reproductive period must be completely contraception in 28 days before treatment, during the treatment process and in 28 days after treatment; Men must be completely contraception and prohibited donation and sperm donation during the treatment process and in 28 days after treatment; All patients must be prohibited donation during the treatment process and in 28 days after treatment; In addition to the subjects, prohibitting other people taking this product. patients have a good understanding and could coordinate with investigators for the trial. Patients enrolled in the trial should sign an informed consent form, to indicate understanding the purpose and procedure of the trial, and patients volunteering to participate in the trial.", "candidate_expression": "((0-B) AND (20-70 years old) AND (50-100 points) AND (> 3 months) AND (A) AND (Age) AND (BCLC stage) AND (Child-Pugh grade) AND (Gender) AND (HCC) AND (KPS score) AND (Men) AND (No) AND (Patients enrolled in the trial should sign an informed consent form, to indicate understanding the purpose and procedure of the trial, and patients volunteering to participate in the trial) AND (Viable tumor resection confirmed by two highly qualified surgical doctors) AND (clinical or pathological diagnosis) AND (contraception) AND (donation) AND (during the treatment process) AND (expected survival) AND (female) AND (hepatectomy) AND (hepatocellular carcinoma) AND (in 28 days after treatmen) AND (in 28 days after treatment) AND (in 28 days before treatment) AND (indications of hepatectomy) AND (male) AND (other surgical contraindications) AND (patients have a good understanding and could coordinate with investigators for the trial) AND (prohibited) AND (reproductive period) AND (sperm donation) AND (treatment) AND (untreated) AND (women))"}
{"candidate_id": "LLM00428", "doc_id": "NCT02339844_inc", "case_bucket": "or", "source_criterion": "Inclusion Criteria Patients: Fulfilling the diagnostic criteria of schizophrenia or schizoaffective disorder according to ICD-10 (International Classification of Diseases version 10) or DSM-IV/V (Diagnostic and Statistical Manual version 4 /5), Age 18-45 years, Never treated with antipsychotic compounds or central nervous system (CNS) stimulants, Legally competent Inclusion criteria controls: Matching patients on age (+/- 2 years), sex and parental socioeconomic status, Age 18-45 years, No psychiatric or physical disease.", "candidate_expression": "((Age 18-45 years) AND (Legally competent) AND (Patients) AND (controls) AND NOT (antipsychotic compounds) AND NOT (central nervous system (CNS) stimulants) AND (NOT (psychiatric disease) OR NOT (physical disease)) AND ((schizoaffective disorder) OR (schizophrenia)) AND ((DSM-IV/V (Diagnostic and Statistical Manual version 4 /5)) OR (ICD-10 (International Classification of Diseases version 10))))"}
{"candidate_id": "LLM00429", "doc_id": "NCT01401335_exc", "case_bucket": "or", "source_criterion": "Age less than 15 or greater than 25 and not participating in the day care center", "candidate_expression": "((Age less than 15 greater than 25) AND NOT (participating in the day care center))"}
{"candidate_id": "LLM00430", "doc_id": "NCT02416765_inc", "case_bucket": "or", "source_criterion": "1. Males and females ≥ 18 years old. 2. Clinical diagnosis of type 1 diabetes for at least one year. 3. The subject will have been on insulin pump therapy for at least 3 months and currently using a fast actin insulin analog (Lispro, Aspart or Guilisine). 4. Last (less than 3 months) HbA1c ≤ 10%. 5. Currently using carbohydrate counting as the meal insulin dose strategy.", "candidate_expression": "((Aspart) AND (Guilisine) AND (HbA1c Last (less than 3 months) ≤ 10%) AND (Lispro) AND (Males) AND (carbohydrate counting Currently) AND (fast actin insulin analog currently) AND (females) AND (insulin pump therapy for at least 3 months) AND (meal insulin dose strategy) AND (old ≥ 18 years old) AND (type 1 diabetes for at least one year))"}
{"candidate_id": "LLM00431", "doc_id": "NCT02386800_inc", "case_bucket": "other", "source_criterion": "Patient is currently enrolled in a Novartis OGD or GMA-sponsored or Incyte-sponsored clinical study (where Incyte can delegate the sponsorship to a preferred CRO, if applicable) that is approved to enroll into this rollover study, is receiving ruxolitinib and has fulfilled all of the requirements of the parent protocol. Patient is currently benefiting from the treatment with ruxolitinib, as determined by the investigator Patient has demonstrated compliance, as assessed by the investigator, with the parent study protocol requirements Willingness and ability to comply with scheduled visits, treatment plans and any other study procedures Patient currently has no evidence of progressive disease, as determined by the investigator, following previous treatment with ruxolitinib Written informed consent obtained prior to enrolling in roll-over study and receiving study medication. If consent cannot be expressed in writing, it must be formally documented and witnessed, ideally via an independent trusted witness.", "candidate_expression": "((Patient has demonstrated compliance, as assessed by the investigator, with the parent study protocol requirements Willingness and ability to comply with scheduled visits, treatment plans and any other study procedures) AND (Patient is currently enrolled in a Novartis OGD or GMA-sponsored or Incyte-sponsored clinical study (where Incyte can delegate the sponsorship to a preferred CRO, if applicable) that is approved to enroll into this rollover study, is receiving ruxolitinib and has fulfilled all of the requirements of the parent protocol.) AND (Written informed consent obtained prior to enrolling in roll-over study and receiving study medication. If consent cannot be expressed in writing, it must be formally documented and witnessed, ideally via an independent trusted witness) AND (progressive disease) AND (ruxolitinib))"}
{"candidate_id": "LLM00432", "doc_id": "NCT02934269_exc", "case_bucket": "or", "source_criterion": "Exposure/treatment to an investigational (new chemical entity) or marketed drug or biologic within 30 days preceding the first dose administration, or five half-lives of that investigational drug or biologic, if known (whichever is longer). Donation blood or serum within 8 weeks before the first dose administration to a blood bank or blood donation center. History of alcohol or drug abuse (as defined by the current version of the DSM) within 2 years before the first dose administration, or positive alcohol or drug screen. Vaccination within 30 days prior to the first dose administration or has plans to receive a vaccination during the course of the study (including the follow phone call on Day 105).", "candidate_expression": "((current version of the DSM) AND ((alcohol screen positive) OR (drug screen positive)) AND ((Vaccination within 30 days prior) OR (vaccination plans during the course)) AND ((Donation blood within 8 weeks before) OR (Donation serum within 8 weeks before)) AND ((alcohol abuse) OR (drug abuse)))"}
{"candidate_id": "LLM00433", "doc_id": "NCT02992938_inc", "case_bucket": "other", "source_criterion": "Patients scheduled for thyroidectomy with general anesthesia in the University of Chile Clinical Hospital", "candidate_expression": "((University of Chile Clinical Hospita) AND (general anesthesia) AND (scheduled for) AND (thyroidectomy))"}
{"candidate_id": "LLM00434", "doc_id": "NCT03216967_inc", "case_bucket": "other", "source_criterion": "Adult patients Kidney transplant recipients Patients treated by a calcineurin inhibitor and mycophenolic acid Viremia >= 3 log UI/ml Patients who have given written informed consent Negative pregnancy test (blood ß-HCG dosage)", "candidate_expression": "((>= 3 log UI/ml) AND (Adult) AND (Kidney transplant) AND (Negative) AND (Patients who have given written informed consent) AND (Viremia) AND (blood ß-HCG dosage) AND (calcineurin inhibitor) AND (mycophenolic acid) AND (pregnancy test))"}
{"candidate_id": "LLM00435", "doc_id": "NCT01997112_inc", "case_bucket": "or", "source_criterion": "=18 years old, men or post-menopausal women (women with no periods for 12 months or more, or those who have had a surgical menopause) Treated hypertensive patients with an average daytime ambulatory blood pressure measurement (ABPM) <150/95mmHg on stable doses of one or more antihypertensive medication (at least one of which should be; an ACE inhibitor, angiotensin receptor blocker or diuretic) for 3 months, or untreated hypertensive patients with an average daytime ABPM =135/85 but <150/95.", "candidate_expression": "((<150/95mmHg) AND (=135/85 but <150/95) AND (=18) AND (Treated) AND (antihypertensive medication) AND (at least one) AND (average daytime ABPM) AND (average daytime ambulatory blood pressure measurement (ABPM)) AND (for 12 months or more) AND (for 3 months) AND (hypertensive) AND (hypertensive patients) AND (one or more) AND (post-menopausal) AND (stable doses) AND (surgical) AND (untreated) AND (years old) AND ((ACE inhibitor) OR (angiotensin receptor blocker) OR (diuretic)) AND ((men) OR (women)) AND ((menopause) OR (no periods)))"}
{"candidate_id": "LLM00436", "doc_id": "NCT03337581_inc", "case_bucket": "or", "source_criterion": "selective operation of inguinal hernia repair<U+3001>orthopedics operation or general surgery operation in children aged 3-9 years ASA I - II enter the operating room by himself without parents normal liver and kidney function no history of anesthesia medication allergy.", "candidate_expression": "((ASA I - II) AND (aged 3-9 years) AND (anesthesia medication) AND (children) AND (general surgery operation) AND (inguinal hernia repair) AND (normal kidney function) AND (normal liver function) AND (orthopedics operation) AND NOT (allergy history))"}
{"candidate_id": "LLM00437", "doc_id": "NCT03464552_exc", "case_bucket": "or", "source_criterion": "A known allergy to Celecoxib, aspirin or another NSAID. Active peptic ulceration or gastrointestinal bleeding. Inflammatory bowel disease. Congestive heart failure (NYHA II-IV). Established ischemic heart disease, peripheral arterial disease and/or cerebrovascular disease. History of neurologic deficit. Known hepatic or renal impairment. Pregnancy. Breast-feeding. Post-hysterectomy. Bleeding disorders. Drug abuse. Cervical and vaginal infection.", "candidate_expression": "((Bleeding disorders) AND (Breast-feeding) AND (Celecoxib) AND (Cervical infection) AND (Congestive heart failure) AND (Drug abuse) AND (Inflammatory bowel disease) AND (NSAID another) AND (NYHA II-IV) AND (Pregnancy) AND (allergy) AND (aspirin) AND (cerebrovascular disease) AND (gastrointestinal bleeding) AND (hepatic impairment) AND (hysterectomy Post) AND (ischemic heart disease) AND (neurologic deficit History) AND (peptic ulceration) AND (peripheral arterial disease) AND (renal impairment) AND (vaginal infection))"}
{"candidate_id": "LLM00438", "doc_id": "NCT02511574_exc", "case_bucket": "other", "source_criterion": "no confirmation of the gestational age ruptured membranes painful regular uterine contractions major fetal abnormalities", "candidate_expression": "((fetal abnormalities) AND (gestational age) AND (major) AND (no) AND (painful regular uterine contractions) AND (ruptured membranes))"}
{"candidate_id": "LLM00439", "doc_id": "NCT03123562_inc", "case_bucket": "other", "source_criterion": "Cerebral palsy of any types caused by Neonatal Jaundice", "candidate_expression": "((Cerebral palsy) AND (Neonatal Jaundice))"}
{"candidate_id": "LLM00440", "doc_id": "NCT03424993_inc", "case_bucket": "other", "source_criterion": "Habitual dietary sodium intake > 3400mg per day", "candidate_expression": "(dietary sodium intake > 3400mg per day)"}
{"candidate_id": "LLM00441", "doc_id": "NCT02406495_inc", "case_bucket": "other", "source_criterion": "Is between 18 and 40 years of age (inclusive) Has had a self-reported visual exam in the last two years Is an adapted Avaira sphere contact lens wearer (at least 1 week in Avaira sphere) Has a contact lens spherical prescription between + 2.25 to - 8.00 (inclusive) Has a spectacle cylinder up to 0.75D in each eye. Can achieve best corrected spectacle distance visual acuity of 20/25 (0.10 logMAR) or better in each eye. Can achieve a distance visual acuity of 20/30 (0.18 logMAR) or better in each eye with the study contact lenses. Has clear corneas and no active ocular disease Has read, understood and signed the information consent letter. Patient contact lens refraction should fit within the available parameters of the study lenses. Is willing to comply with the wear schedule (at least 5 days per week, > 8 hours/day assuming there are no contraindications for doing so). Is willing to comply with the visit schedule", "candidate_expression": "((+ 2.25 to - 8.00 (inclusive)) AND (0.10 logMAR or better) AND (0.18 logMAR or better) AND (20/25 or better) AND (20/30 or better) AND (Avaira sphere) AND (Avaira sphere contact lens) AND (Has read, understood and signed the information consent letter.) AND (Is willing to comply with the visit schedule) AND (Is willing to comply with the wear schedule (at least 5 days per week, > 8 hours/day assuming there are no contraindications for doing so).) AND (active) AND (age) AND (at least 1 week in Avaira sphere) AND (best corrected spectacle distance visual acuity) AND (between 18 and 40 years (inclusive)) AND (clear corneas) AND (contact lens) AND (distance visual acuity) AND (in the last two years) AND (no) AND (ocular disease) AND (self-reported visual exam) AND (spectacle cylinder) AND (spherical) AND (study contact lenses) AND (up to 0.75D))"}
{"candidate_id": "LLM00442", "doc_id": "NCT03305575_inc", "case_bucket": "other", "source_criterion": "ASA classification II or III females Age: 18-45 years old BMI = 50 kg/m2 Singleton pregnancy Simple prophylactic cervical cerclage Planning neuraxial anesthesia", "candidate_expression": "((ASA classification II or III) AND (Age 18-45 years old) AND (BMI = 50 kg/m2) AND (Singleton pregnancy) AND (cervical cerclage Simple prophylactic) AND (females) AND (neuraxial anesthesia Planning))"}
{"candidate_id": "LLM00443", "doc_id": "NCT02748330_inc", "case_bucket": "or", "source_criterion": "Provision of written informed consent (by patient or appropriate designee according to local regulations) prior to any study specific procedures. Aged 18 years or older, male or female. History of stable angina pectoris with angiographic evidence of CAD (diameter stenosis = 50%) in major, i.e., left main, left anterior descending, left circumflex, and right coronary arteries. History of previous myocardial infarction (MI) History of coronary revascularization, i.e., percutaneous coronary intervention (PCI) or coronary artery bypass graft (CABG), not including the elective PCI during the index hospitalization Documented history of type 2 diabetes mellitus. Post-procedural residual diameter stenosis of the treated lesions < 20% in patients with stent implantation or < 50% in those with balloon angioplasty Post-procedural thrombolysis in myocardial infarction (TIMI) grade 3 flow in treated vessels Negative cardiac troponin test before the index elective PCI. Taking Clopidogrel 75 mg daily dose for at least 7 days or taking Clopidogrel 75 mg daily dose for less than 7 days but with 300 to 600 mg Clopidogrel loading dose before PCI. Taking acetylsalicylic acid (ASA) 100 mg daily treatment for at least 7 days or taking ASA 100 mg daily dose for less than 7 days but with 300 mg ASA loading dose before PCI. have a negative urine or blood pregnancy test at enrolment and prior to randomization; currently be using a hormonal contraceptive and agree to continue its use in addition to using double-barrier local contraception (i.e., intra-uterine device plus spermicidal and condom for male partner) from screening through study completion.", "candidate_expression": "((ASA) AND (ASA 100 mg daily for less than 7 days) AND (ASA 300 mg before PCI) AND (Aged 18 years or older) AND (CABG) AND (CAD angiographic evidence diameter stenosis major coronary arteries) AND (Clopidogrel 300 to 600 mg before PCI) AND (Clopidogrel 75 mg daily for at least 7 days) AND (Clopidogrel 75 mg daily for less than 7 days) AND (MI) AND (PCI) AND (Post-procedural thrombolysis treated vessels) AND (Provision of written informed consent (by patient or appropriate designee according to local regulations) prior to any study specific procedures) AND (TIMI) AND (acetylsalicylic acid 100 mg daily for at least 7 days) AND (balloon angioplasty) AND (cardiac troponin test Negative before the index elective PCI.) AND (coronary revascularization during the index hospitalization) AND (currently be using a hormonal contraceptive and agree to continue its use in addition to using double-barrier local contraception (i.e., intra-uterine device plus spermicidal and condom for male partner) from screening through study completion) AND (have a negative urine or blood pregnancy test at enrolment and prior to randomization;) AND (myocardial infarction) AND (myocardial infarction grade 3) AND (stable angina pectoris) AND (stent implantation) AND (type 2 diabetes mellitus) AND NOT (PCI elective) AND ((left anterior descending coronary arteries) OR (left circumflex coronary arteries) OR (left main coronary arteries) OR (right coronary arteries)) AND ((coronary artery bypass graft) OR (percutaneous coronary intervention)) AND ((lesions Post-procedural residual diameter stenosis treated)) AND ((female) OR (male)))"}
{"candidate_id": "LLM00444", "doc_id": "NCT02596555_inc", "case_bucket": "or", "source_criterion": "Age =18 years Objectively confirmed diagnosis of acute PE by multidetector CT angiography, ventilation/perfusion lung scan, or selective invasive pulmonary angiography, according to established diagnostic criteria, with or without symptomatic deep vein thrombosis Absence of hemodynamic collapse, or decompensation, at presentation; Hemodynamic collapse or decompensation At least one sign of RV pressure overload/dysfunction on CT angiography or echocardiography Signs of myocardial injury as indicated by elevated troponin levels Signs of (RV) failure as indicated by NT-proBNP levels >600 pg/ml at baseline. Ability of the subject to understand the character and individual consequences of the clinical trial; signed and dated informed consent of the subject available before the start of any specific trial procedures", "candidate_expression": "((Ability of the subject to understand the character and individual consequences of the clinical trial; signed and dated informed consent of the subject available before the start of any specific trial procedures) AND (Age =18 years) AND (CT angiography) AND (NT-proBNP levels >600 pg/ml) AND (PE acute) AND (RV) failure) AND (deep vein thrombosis) AND (echocardiography) AND (hemodynamic collapse) AND (hemodynamic decompensation) AND (invasive pulmonary angiography,) AND (myocardial injury) AND (sign of RV pressure dysfunction) AND (sign of RV pressure overload) AND (troponin levels elevated) AND (ventilation/perfusion lung scan))"}
{"candidate_id": "LLM00445", "doc_id": "NCT02903407_inc", "case_bucket": "other", "source_criterion": "All patients admitted to the Duke CICU, who require intubation and sedation for mechanical ventilation that is expected to be >24 hours in duration will be included, unless they meet the specified exclusion criteria. Patients intubated within one hour prior to care transition to the CICU will also be screened for inclusion.", "candidate_expression": "((>24 hours in duration) AND (Duke CICU) AND (admitted) AND (care transition) AND (expected to be) AND (intubated) AND (intubation) AND (mechanical ventilation) AND (sedation) AND (within one hour prior to care transition))"}
{"candidate_id": "LLM00446", "doc_id": "NCT03484091_exc", "case_bucket": "or", "source_criterion": "Severe deformity (varus or values from mechanical axis more than 5 degrees Allergy to hyaluronic acid Pain on hip or ankle Post-traumatic or post surgery of lower extremity Post infection of knee Previous hyaluronic acid injection within 6 months Pregnancy or lactation Underlying Rheumatoid arthritis, stroke, malignancy, venous occlusion", "candidate_expression": "((Allergy) AND (Pain hip ankle Post-traumatic of lower extremity post surgery of lower extremity) AND (Pregnancy) AND (Rheumatoid arthritis) AND (deformity Severe) AND (hyaluronic acid) AND (hyaluronic acid injection Previous within 6 months) AND (infection of knee Post) AND (lactation) AND (malignancy) AND (stroke) AND (values from mechanical axis more than 5 degrees) AND (varus) AND (venous occlusion))"}
{"candidate_id": "LLM00447", "doc_id": "NCT01490034_exc", "case_bucket": "other", "source_criterion": "", "candidate_expression": "(EMPTY)"}
{"candidate_id": "LLM00448", "doc_id": "NCT03017053_inc", "case_bucket": "or", "source_criterion": "Ability to understand and the willingness to sign a written informed consent document Age= 18 and= 75 years Clinical/ Histological/ cytological/ Imaging examination proven Oral/Oropharynx Squamous-cell carcinoma (Tongue, buccal mucosa, mouth floor, hard palate, Molar area), the depth of invasion > 4mm in preoperative assessment In line with clinical stage I / II stage (T1-2 N0 M0; AJCC 2010) and receiving surgical resection KPS= 70 Normal bone marrow reserve function and normal liver, kidney function Expected survival period= 6 months", "candidate_expression": "((Ability to understand and the willingness to sign a written informed consent document) AND (Age = 18 and= 75 years) AND (Clinical examination Oral Oropharynx) AND (Expected survival period = 6 month) AND (Histological examination) AND (Imaging examination) AND (KPS = 70) AND (M 0) AND (N 0) AND (Squamous-cell carcinoma Tongue buccal mucosa mouth floor hard palate) AND (T 1-2) AND (bone marrow reserve function Normal) AND (clinical stage I) AND (clinical stage II) AND (cytological examination) AND (depth of invasion > 4mm Molar area) AND (kidney function normal) AND (liver function normal) AND (preoperative assessment) AND (surgical resection))"}
{"candidate_id": "LLM00449", "doc_id": "NCT03213834_inc", "case_bucket": "or", "source_criterion": "CPPE along with evidence of septated pleural effusion on pleural ultrasonography and/or chest CT scan empyema.", "candidate_expression": "((CPPE) AND (empyema) AND (septated pleural effusion evidence of) AND ((chest CT scan) OR (pleural ultrasonography)))"}
{"candidate_id": "LLM00450", "doc_id": "NCT02579200_exc", "case_bucket": "or", "source_criterion": "Inability to perform exercise tests Diagnosed psychiatric or cognitive disorders Progressive neurological or neuromuscular disorders having a major impact on exercise capacity", "candidate_expression": "((Inability to perform) AND (exercise tests) AND (impact on exercise capacity) AND ((cognitive disorders) OR (psychiatric disorders)) AND ((disorders Progressive neurological) OR (neuromuscular disorders Progressive)))"}
```
