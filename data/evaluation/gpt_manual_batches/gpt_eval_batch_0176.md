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
{"candidate_id": "LLM04376", "doc_id": "NCT02437045_exc", "case_bucket": "or", "source_criterion": "Patient not expected to survive more than 4 days Patient allergic to a penicillin or a carbapenem Patient with significant polymicrobial bacteraemia (that is, a Gram positive skin contaminant in one set of blood cultures is not regarded as significant polymicrobial bacteraemia). Treatment is not with the intent to cure the infection (that is, palliative care is an exclusion). Pregnancy or breast-feeding. Use of concomitant antimicrobials in the first 4 days after enrolment with known activity against Gram-negative bacilli (except trimethoprim/sulphamethoxazole may be continued as Pneumocystis prophylaxis). Severe acute illness as defined by Pitt bacteraemia score of >4 Likely source to be from (proven or suspected at the time of randomisation) the central nervous system, e.g. brain abscess, post-surgical meningitis, shunt infection (due to concerns over CNS penetration of piperacillin/tazobactam)", "candidate_expression": "((>4) AND (Gram-negative bacilli) AND (Pitt bacteraemia score) AND (Pregnancy or breast-feeding) AND (allergic) AND (antimicrobials) AND (bacteraemia) AND (brain abscess) AND (carbapenem) AND (concomitant) AND (enrolment) AND (except) AND (first 4 days after enrolment) AND (meningitis) AND (more than 4 days) AND (not) AND (penicillin) AND (polymicrobial) AND (post-surgical) AND (rimethoprim/sulphamethoxazole) AND (shunt infection) AND (survive))"}
{"candidate_id": "LLM04377", "doc_id": "NCT03250507_inc", "case_bucket": "other", "source_criterion": "Elective open abdominal hysterectomy with midline incision, age > 18 years, American Society of Anesthesiologist classification score (ASA classification) 1-3.", "candidate_expression": "((1-3) AND (> 18 years) AND (ASA classification) AND (American Society of Anesthesiologist classification score) AND (Elective) AND (age) AND (midline incision) AND (open abdominal hysterectomy))"}
{"candidate_id": "LLM04378", "doc_id": "NCT01352598_inc", "case_bucket": "or", "source_criterion": "Patient age >= 18 years Zubrod performance status of 0-3 T1-3 N0 M0 adenocarcinoma of the prostate Prostate volume = 100 cc Signed study-specific consent form Extension of local tumor to involve adjacent organs other than seminal vesicles (T4) Prostate volume > 100 cc Nodal involvement Metastatic disease Prior pelvic radiotherapy except as part of combination therapy for prostate cancer History of scleroderma Patients with psychiatric or addictive disorder that would preclude obtaining informed consent", "candidate_expression": "((0) AND (0-3) AND (1-3) AND (= 100 cc) AND (> 100 cc) AND (>= 18 years) AND (Extension of local tumor) AND (History) AND (M) AND (Metastatic disease) AND (N) AND (Nodal involvement) AND (Patient age) AND (Prior) AND (Prostate volume) AND (Signed study-specific consent form) AND (T) AND (Zubrod performance status) AND (adenocarcinoma) AND (adjacent organs) AND (combination therapy) AND (except) AND (other than) AND (pelvic) AND (prostate) AND (prostate cancer) AND (radiotherapy) AND (scleroderma) AND (seminal vesicles) AND ((addictive disorder) OR (psychiatric disorder)))"}
{"candidate_id": "LLM04379", "doc_id": "NCT03011177_inc", "case_bucket": "other", "source_criterion": "Patients who are 19 years or older on screening Patients with type 2 diabetes mellitus Patients with 7.0% = HbA1c = 11.0% at the screening visit Patients with Fasting Plasma Glucose <15mmol/L(270mg/dL) on screening", "candidate_expression": "((Fasting Plasma Glucose <15mmol/L 270mg/dL on screening) AND (HbA1c 7.0% 11.0% at the screening visit) AND (type 2 diabetes mellitus) AND (years 19 or older on screening))"}
{"candidate_id": "LLM04380", "doc_id": "NCT02638935_inc", "case_bucket": "or", "source_criterion": "Female Age ≥18 years Patients with a lesion > 0.5 cm in largest diameter size, initially scored BI-RADS® 3, 4a, 4b or 4c in B-mode ultrasound Informed consent about histological examination (core cut biopsy (CCB), vacuum-assisted biopsy (VAB), fine needle aspiration (FNA) or surgery) has already been given in the course of clinical routine Signed informed consent of study participation", "candidate_expression": "((Age ≥18 years) AND (B-mode ultrasound) AND (BI-RADS® 3, 4a, 4b or 4c) AND (Female) AND (Informed consent) AND (Signed informed consent of study participation) AND (histological examination) AND (largest diameter size > 0.5 cm) AND (lesion) AND ((core cut biopsy (CCB)) OR (fine needle aspiration (FNA)) OR (surgery) OR (vacuum-assisted biopsy (VAB))))"}
{"candidate_id": "LLM04381", "doc_id": "NCT03192020_inc", "case_bucket": "or", "source_criterion": "patients with =20° passive extension deficit (PED) in metacarpophalangeal (MP) or proximal interphalangeal (PIP) joint, or TPED of =30° in MP and PIP joints of finger/fingers II-V age > 18 years palpable cord provision of informed consent ability to fill the Finnish versions of questionnaires.", "candidate_expression": "((=20°) AND (=30°) AND (> 18 years) AND (MP) AND (PIP joints) AND (TPED) AND (age) AND (finger/fingers II-V) AND (joint metacarpophalangeal (MP)) AND (palpable cord) AND (passive extension deficit (PED)) AND (provision of informed consent) AND (proximal interphalangeal (PIP) joint))"}
{"candidate_id": "LLM04382", "doc_id": "NCT02526823_exc", "case_bucket": "or", "source_criterion": "Patients with severe complications or severe infection; Invasion of central nervous system; Patients with severe heart disease history, including ventricular tachycardia (VT), atrial fibrillation (AF), heart block, myocardial infarction (MI), congestive heart failure (CHF), coronary heart disease patients needed therapy; patients with severe allergic constitution, or those who are allergic to or intolerant of drug composition in chemotherapy regimens; with other malignant tumors in the past 5 years; patients received doxorubicin therapy, total cumulative dose of adriamycin was more than 300 mg/m2, total cumulative dose of epirubicin was more than 450 mg/m2; Patients participate in other clinical studies; Other patients who are not suitable for the study.", "candidate_expression": "((AF) AND (CHF) AND (Invasion central nervous system) AND (MI) AND (Patients) AND (Patients participate in other clinical studies) AND (VT) AND (chemotherapy regimens) AND (heart disease severe) AND ((complications severe) OR (infection severe)) AND ((atrial fibrillation) OR (congestive heart failure) OR (coronary heart disease) OR (heart block) OR (myocardial infarction) OR (ventricular tachycardia)) AND ((allergic severe) OR (malignant tumors other past 5 years)) AND ((allergic) OR (intolerant)) AND ((adriamycin total cumulative dose more than 300 mg/m2) OR (doxorubicin) OR (epirubicin total cumulative dose more than 450 mg/m2)))"}
{"candidate_id": "LLM04383", "doc_id": "NCT02536976_exc", "case_bucket": "or", "source_criterion": "Known or suspected alcohol or substance abuse in the preceding 12 months. Women who are pregnant or breastfeeding. Women of childbearing potential (WOCP) who are not using at least one method of contraception. Patients with severe renal impairment (CLcr = 29 mL/min, or eGFR = 29 mL/min/1.73 m2), or moderate or severe hepatic impairment (Child-Pugh classes B or C). Patients with bladder outlet obstruction (BOO) that, in the opinion of the study urologist, would expose them to risk of urinary retention during treatment with mirabegron. Patients treated with drugs metabolized by the CYP2D6 pathway. Patients with supine systolic blood pressure (SBP) = 180 mm Hg, or diastolic blood pressure (DBP) = 110 mm Hg. Clinically significant, uncontrolled cardiac arrhythmia, unstable angina, congestive heart failure (NYHA Class 3 or 4), or history of myocardial infarction in the preceding 2 years. History of cancer in the preceding 2 years other than successfully treated, non-metastatic, squamous cell or basal cell carcinoma, or cervical cancer in situ. Any major urological procedure in the preceding 90 days. Any major surgical procedure in the preceding 30 days. Previously treated with mirabegron within 60 days prior to the baseline visit (Visit 2), or previously having failed treatment with mirabegron regardless of duration and timing of treatment. Current or previous, within the 60 days preceding the baseline visit (Visit 2), treatment with antimuscarinic agents for OAB symptoms; and, willingness to not use antimuscarinic agents for the duration of the study. Currently receiving any other investigational drug or having received an investigational drug within the 60 days preceding the baseline visit (Visit 2). Any condition or laboratory test result, which, in the opinion of the Investigator or the Study Urologist, might result in an increased risk to the patient, or would affect their participation in the study. Any patient who, in the opinion of the Investigator, is not a good candidate for the study or will not be able to follow study procedures.", "candidate_expression": "((BOO) AND (Child-Pugh classes) AND (Currently receiving any other investigational drug or having received an investigational drug within the 60 days preceding the baseline visit (Visit 2)) AND (DBP) AND (NYHA Class) AND (OAB symptoms) AND (SBP) AND (Women of childbearing potential (WOCP) who are not using at least one method of contraception) AND (Women who are pregnant or breastfeeding) AND (antimuscarinic agents within the 60 days preceding the baseline visit) AND (bladder outlet obstruction risk of urinary retention) AND (cancer preceding 2 years) AND (major surgical procedure preceding 30 days) AND (major urological procedure preceding 90 days) AND (mirabegron) AND (mirabegron within 60 days prior to the baseline visit) AND (willingness to not use antimuscarinic agents for the duration of the study) AND ((hepatic impairment) OR (renal impairment severe)) AND ((moderate) OR (severe)) AND ((B) OR (C)) AND ((alcohol abuse) OR (substance abuse)) AND ((diastolic blood pressure = 110 mm Hg) OR (systolic blood pressure supine = 180 mm Hg)) AND ((cardiac arrhythmia uncontrolled) OR (congestive heart failure) OR (myocardial infarction preceding 2 years) OR (unstable angina)) AND ((3) OR (4)) AND ((basal cell carcinoma) OR (carcinoma squamous cell) OR (cervical cancer in situ)) AND ((CLcr = 29 mL/min) OR (eGFR = 29 mL/min/1.73 m2)))"}
{"candidate_id": "LLM04384", "doc_id": "NCT02823808_exc", "case_bucket": "or", "source_criterion": "The use of weight-lowering drugs, any investigational blood-glucose or lipid-lowering agent (other than statins or ezetimibe) within the past 3 months Previous treatment with systemic corticosteroids or a change in dosage of thyroid hormones in the previous 6 weeks The use of insulin within the 3 months prior to screening Others", "candidate_expression": "((agent investigational lipid-lowering) AND (drugs weight-lowering blood-glucose) AND (ezetimibe) AND (insulin within the 3 months prior to screening) AND (statins) AND (systemic corticosteroids) AND (thyroid hormones change in dosage))"}
{"candidate_id": "LLM04385", "doc_id": "NCT03113253_exc", "case_bucket": "or", "source_criterion": "Subjects with a history of hypercoagulopathy, deep vein thrombosis (DVT), pulmonary embolism Renal impairment Subjects with known hypersensitivity to tranexamic acid Consecutive fibrinolytic states to coagulopathy History of convulsions", "candidate_expression": "((DVT) AND (Renal impairment) AND (coagulopathy) AND (convulsions History) AND (deep vein thrombosis) AND (fibrinolytic states) AND (history) AND (hypercoagulopathy) AND (hypersensitivity) AND (pulmonary embolism) AND (tranexamic acid))"}
{"candidate_id": "LLM04386", "doc_id": "NCT02393287_inc", "case_bucket": "or", "source_criterion": "1. Age ≥ 18 years 2. Patient with breast cancer, histologically proven, metastatic or locally advanced 3. Patient treated by Eribulin between January and October 2014 (for the retrospective part) or between November 2014 and September 2015 (for the prospective part). 4. Patient with at least an assessment of the response to Eribulin", "candidate_expression": "((Age) AND (Eribulin) AND (assessment of the response) AND (breast cancer) AND (proven) AND (≥ 18 years) AND ((between January and October 2014) OR (between November 2014 and September 2015)) AND ((histologically) OR (locally advanced) OR (metastatic)))"}
{"candidate_id": "LLM04387", "doc_id": "NCT02537899_inc", "case_bucket": "or", "source_criterion": "Male or female Age 18 to 65 years Diagnosed with spinal cord injury between 3 days and 4 weeks American Spinal Injury Association Impairment Scale A or B Informed consent for inclusion into the database is obtained", "candidate_expression": "((Age 18 to 65 years) AND (American Spinal Injury Association Impairment Scale A or B) AND (Informed consent for inclusion into the database is obtained) AND (spinal cord injury between 3 days and 4 weeks) AND ((Male) OR (female)))"}
{"candidate_id": "LLM04388", "doc_id": "NCT03497598_inc", "case_bucket": "or", "source_criterion": "Women = 3 UTIs within the last 12 months or = 2 UTIs within the last 6 months; Laboratory urine culture: <103 CFUs Age > 18 years", "candidate_expression": "((<103 CFUs) AND (= 2) AND (= 3) AND (> 18 years) AND (Age) AND (Laboratory urine culture) AND (Women) AND (within the last 12 months) AND (within the last 6 months) AND ((UTIs)))"}
{"candidate_id": "LLM04389", "doc_id": "NCT00609531_exc", "case_bucket": "or", "source_criterion": "Age less than 10 years or greater than 55 years, at time of consent Estimated IQ < 70 Uncontrolled epilepsy (seizure within 6 months prior to consent) 4. Presence of medical conditions that might interfere with participation, or where participation would be contraindicated History of neurological injury: head trauma, poorly-controlled seizure disorder (seizure within the preceding six months), stroke, prior neurosurgery, or under the care of a neurologist or neurosurgeon as determined by interview History of claustrophobia Implanted or irremovable metal in the body (including certain tattoos and permanent make-up) Current pregnancy (as verified by testing prior to both initial dose administration of citalopram or placebo and prior to magnetic resonance imaging) due to the risk that may be associated with SSRI treatment and magnetic resonance imaging on fetal health Medical contraindications to SSRI therapy as determined by history (including induction of mania or hypomania during SSRI therapy, or known drug allergy) Concomitant medication that would interfere with study participation Prior history of citalopram treatment failure at appropriate doses and duration Prior history of treatment failure to two previous SSRI trials at appropriate doses and duration Ongoing need for psychoactive medication other than study medication [excepting stable doses (greater than three months duration) of anticonvulsant medication for seizure disorder, or diphenhydramine (Benadryl®)for sleep]", "candidate_expression": "((< 70) AND (Age) AND (Current) AND (Estimated IQ) AND (History) AND (Implanted metal in the body) AND (Prior) AND (SSRI therapy) AND (Uncontrolled epilepsy) AND (anticonvulsant medication) AND (at time of consent) AND (citalopram) AND (claustrophobia) AND (consent) AND (contraindications to SSRI therapy) AND (diphenhydramine) AND (drug allergy) AND (during SSRI therapy) AND (excepting) AND (failure) AND (greater than 55 years) AND (greater than three months) AND (head trauma) AND (history) AND (hypomania) AND (irremovable metal in the body) AND (less than 10 years) AND (mania) AND (neurological injury) AND (neurosurgery) AND (other than) AND (poorly-controlled) AND (pregnancy) AND (prior) AND (psychoactive medication) AND (seizure) AND (seizure disorder) AND (stable doses) AND (stroke) AND (study medication) AND (treatment) AND (under the care of a neurologist) AND (under the care of a neurosurgeon) AND (within 6 months prior to consent) AND (within the preceding six months))"}
{"candidate_id": "LLM04390", "doc_id": "NCT02924090_inc", "case_bucket": "or", "source_criterion": "Adults patients aged 18 to 85 years Diagnosed with Major Depressive Disorder, unipolar or bipolar depression Undergoing ECT for treatment of their symptoms Currently residing in Manitoba", "candidate_expression": "((Adults) AND (Currently residing) AND (ECT Undergoing) AND (Manitoba) AND (aged 18 to 85 years) AND ((Major Depressive Disorder) OR (bipolar depression) OR (unipolar depression)))"}
{"candidate_id": "LLM04391", "doc_id": "NCT02647788_exc", "case_bucket": "or", "source_criterion": "ASA> 3; Coagulopathy; Renal disease, Liver disease, History of recent gastro-intestinal bleeding Pregnancy. Diagnosis of chronic pain currently taking opioid pain medication or with a history of drug abuse. Patients with a self-described allergy to ASA, acetaminophen, NSAIDS and codeine. All patients receiving a brachial plexus block for anesthesia and/or analgesia", "candidate_expression": "((ASA > 3) AND (Coagulopathy) AND (Liver disease) AND (Pregnancy) AND (Renal disease) AND (allergy) AND (brachial plexus block) AND (gastro-intestinal bleeding recent) AND (opioid pain medication) AND ((ASA) OR (NSAIDS) OR (acetaminophen) OR (codeine)) AND ((chronic pain) OR (drug abuse history of)))"}
{"candidate_id": "LLM04392", "doc_id": "NCT02715518_exc", "case_bucket": "other", "source_criterion": "NA", "candidate_expression": "(EMPTY)"}
{"candidate_id": "LLM04393", "doc_id": "NCT03648021_exc", "case_bucket": "or", "source_criterion": "Known hypersensitivity to paracetamol or mannitol (excipient with known effect) Severe hepatocellular insufficiency (ASAT or ALAT > 5N, or bilirubin > 2N) Pharmacological intervention (administration of corticosteroids, NSAIDs or paracetamol) or physical intervention (external cooling technique) that may influence temperature in the last 6 hours. Pregnant or breastfeeding women Previous participation in this study", "candidate_expression": "((> 2N) AND (> 5N) AND (Pharmacological) AND (Previous participation in this study) AND (external cooling technique) AND (hepatocellular insufficiency) AND (hypersensitivity) AND (in the last 6 hours) AND (temperature) AND (that may influence temperature) AND (women) AND ((Pharmacological intervention) OR (physical intervention)) AND ((NSAIDs) OR (corticosteroids) OR (paracetamol)) AND ((Pregnant) OR (breastfeeding)) AND ((mannitol) OR (paracetamol)) AND ((ALAT) OR (ASAT) OR (bilirubin)))"}
{"candidate_id": "LLM04394", "doc_id": "NCT00749112_inc", "case_bucket": "or", "source_criterion": "Age: > or = 16 years Weight: more than 40 Kg Autoimmune Hemolytic anemia with clinical and biochemical evidence of hemolysis refractory to treatment, in relapse or steroids dependant Idiopathic thrombocytopenic purpura with platelet counts < 50,000, refractory to treatment, in relapse or steroids dependant", "candidate_expression": "((< 50,000) AND (> or = 16 years) AND (Age) AND (Autoimmune Hemolytic anemia) AND (Idiopathic thrombocytopenic purpura) AND (Weight) AND (biochemical evidence) AND (evidence clinical) AND (hemolysis) AND (more than 40 Kg) AND (platelet counts) AND (refractory to treatment) AND (steroids) AND (treatment) AND ((in relapse) OR (steroids dependant)) AND ((in relapse) OR (refractory to treatment) OR (steroids dependant)))"}
{"candidate_id": "LLM04395", "doc_id": "NCT02337764_exc", "case_bucket": "or", "source_criterion": "The participant has Modified Hoehn & Yahr stage 5 (or stage 5 at eather on-time or off-time for the participant with wearing off phenomenon). The participant has severe dyskinesia. The participant has unstable systemic disease. The participant has a Mini-Mental State Examinations (MMSE) score of <= 24. psychiatric disease. The participant has a history of clinically significant hypertension or other reactions associated with ingestion of tyramine-rich food. The participant has received neurosurgical intervention for Parkinson's disease (e.g., pallidotomy, thalamotomy, deep brain stimulation). The participant has received transcranial magnetic stimulation within 6 months.The participant has received selegiline, pethidine, tramadol, reserpine or methyldopa within 90 days. The participant has received levodopa monotherapy, any psychoneurotic agent or antiemetic medication of dopamine agonist within 14 days. However, the participant has been receiving quetiapine or domperidone with a stable dose regimen for >= 14 days may be included in the study. The participant is required to take any of the excluded medications or treatments. The participant with laboratory data meeting any of the following: Creatinine >= 2 x upper limit of normal (ULN) Total bilirubin >= 2 x ULN ALT or AST >= 1.5 x ULN ALP >= 3 x ULN The participant has received any of the excluded medications or treatments during.", "candidate_expression": "((ALP >= 3 x ULN) AND (Creatinine >= 2 x upper limit of normal (ULN)) AND (Mini-Mental State Examinations (MMSE) <= 24) AND (Modified Hoehn & Yahr stage 5) AND (Parkinson's disease) AND (The participant has received any of the excluded medications or treatments during.) AND (The participant is required to take any of the excluded medications or treatments.) AND (Total bilirubin >= 2 x ULN) AND (clinically significant) AND (dyskinesia severe) AND (levodopa monotherapy) AND (neurosurgical intervention) AND (psychiatric disease) AND (systemic disease unstable) AND (transcranial magnetic stimulation within 6 months) AND (unstable) AND (wearing off phenomenon stage 5) AND ((hypertension clinically significant) OR (reactions associated with ingestion of tyramine-rich food)) AND ((deep brain stimulation) OR (pallidotomy) OR (thalamotomy)) AND ((methyldopa) OR (pethidine) OR (reserpine) OR (selegiline) OR (tramadol)) AND ((antiemetic medication of dopamine agonist) OR (levodopa) OR (psychoneurotic agent)) AND ((at off-time) OR (at on-time)) AND ((domperidone) OR (quetiapine)) AND ((ALT) OR (AST)))"}
{"candidate_id": "LLM04396", "doc_id": "NCT02445339_exc", "case_bucket": "or", "source_criterion": "Active opioid dependence Acute or chronic pain requiring opioid treatment Acute liver injury (liver aminotransferase concentrations >5 times the upper limit of normal) Health condition considered unsafe for inclusion (at discretion of PI and/or attending physician) Lack of capacity or willingness to consent Currently prescribed pharmacotherapy for alcohol dependence (not including treatment of acute alcohol withdrawal syndrome) Previous significant adverse reaction to naltrexone or diluent Pregnant, nursing, or not using effective methods of birth control Prisoners (as defined by Office of Human Research Protection) at the time of enrollment ARE NOT ELIGIBLE for study entry. However, subjects who become prisoners after being enrolled will be included and not be withdrawn from the study. Patients on parole or probation are eligible for enrollment.", "candidate_expression": "((Acute liver injury) AND (Health condition considered unsafe for inclusion) AND (Pregnant) AND (Prisoners Office of Human Research Protection at the time of enrollment) AND (acute alcohol withdrawal syndrome) AND (adverse reaction Previous significant) AND (alcohol dependence) AND (capacity to consent) AND (diluent) AND (liver aminotransferase concentrations >5 times the upper limit of normal) AND (naltrexone) AND (nursing) AND (opioid dependence Active Acute chronic) AND (opioid treatment) AND (pain) AND (pharmacotherapy Currently) AND (willingness to consent) AND NOT (treatment) AND NOT (birth control effective methods))"}
{"candidate_id": "LLM04397", "doc_id": "NCT02810704_inc", "case_bucket": "or", "source_criterion": "Males and females 21 years of age or older; Undergoing elective primary, resurfacing arthroplasty, revision, or second stage re-implantation total hip replacement; Undergoing elective primary, revision, or second stage re-implantation total or uni compartmental knee replacement; Patient has necessary mental capacity to participate and is able to comply with study protocol requirements; Patient is willing and able to give informed consent; and Patient is willing to be randomized and participate.", "candidate_expression": "((Males) AND (Patient has necessary mental capacity to participate and is able to comply with study protocol requirements) AND (Patient is willing and able to give informed consent) AND (Patient is willing to be randomized and participate) AND (age 21 years or older primary resurfacing arthroplasty) AND (females) AND (knee replacement elective uni compartmental) AND (total hip replacement elective revision second stage re-implantation primary revision second stage re-implantation total))"}
{"candidate_id": "LLM04398", "doc_id": "NCT02747940_exc", "case_bucket": "or", "source_criterion": "history of major systemic illness, including uncontrolled hypertension, diabetes, chronic renal insufficiency, autoimmune diseases or malignancies history of neurological disorders which might affect sensation such as previous stroke or peripheral neuropathy history of substance abuse (except painkillers) heavy smokers (with a daily consumption >20 cigarettes) pregnancy or lactation any contraindication for magnetic resonance imaging (MRI) and any obvious infection or inflammation over a period of at least 1 month before the study.", "candidate_expression": "((MRI) AND (affect sensation) AND (at least 1 month before the study) AND (cigarettes) AND (contraindication) AND (daily consumption >20) AND (except) AND (heavy) AND (magnetic resonance imaging) AND (major) AND (neurological disorders) AND (obvious) AND (painkillers) AND (pregnancy or lactation) AND (smokers) AND (study) AND (substance abuse) AND (systemic illness) AND (uncontrolled) AND ((peripheral neuropathy) OR (stroke)) AND ((infection) OR (inflammation)) AND ((autoimmune diseases) OR (chronic renal insufficiency,) OR (diabetes) OR (hypertension) OR (malignancies)))"}
{"candidate_id": "LLM04399", "doc_id": "NCT02996916_inc", "case_bucket": "or", "source_criterion": "Written informed consent obtained Male and female subjects aged 20 years or older at informed consent Essential hypertension who had never received angiotensin II receptor antagonists and calcium channel blockers", "candidate_expression": "((20 years or older) AND (Essential hypertension) AND (Male) AND (Written informed consent obtained) AND (aged) AND (angiotensin II receptor antagonists) AND (at informed consent) AND (calcium channel blockers) AND (female) AND (informed consent) AND (never))"}
{"candidate_id": "LLM04400", "doc_id": "NCT02224040_inc", "case_bucket": "or", "source_criterion": "Blood culture-proven typhoid fever (S. typhi or S. paratyphi) Signed informed consent to participate in the study.", "candidate_expression": "((Blood culture) AND (Signed informed consent to participate in the study.) AND (proven) AND (typhoid fever) AND ((S. paratyphi) OR (S. typhi)))"}
```
