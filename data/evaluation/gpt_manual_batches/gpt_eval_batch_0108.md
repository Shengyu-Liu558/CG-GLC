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
{"candidate_id": "LLM02676", "doc_id": "NCT01932996_exc", "case_bucket": "or", "source_criterion": "Use of smoking cessation medications or interventions in last 30 days Unstable medical illness that requires immediate medical care AUDIT score of < 5 or > 26 Pregnancy or other Nicotine Replacement Therapy (NRT) contraindications Current history or in past 6 months of psychotic disorder or major depressive disorders that is not stable on treatment for past 3 months Cognitive impairment", "candidate_expression": "((AUDIT score of < 5 or > 26) AND (Cognitive impairment) AND (NRT) AND (Nicotine Replacement Therapy) AND (smoking cessation) AND ((major depressive disorders not stable for past 3 months) OR (psychotic disorder past 6 months)) AND ((interventions) OR (medications)) AND ((Pregnancy) OR (contraindications)))"}
{"candidate_id": "LLM02677", "doc_id": "NCT03236246_exc", "case_bucket": "other", "source_criterion": "Serum phosphate <3.0 mg/dL Intravenous (IV) iron administered within 4 weeks prior to Screening Erythropoiesis-stimulating agents (ESA) administered within 4 weeks prior to Screening Blood transfusion within 4 weeks prior to Screening", "candidate_expression": "((<3.0 mg/dL) AND (Blood transfusion) AND (ESA) AND (Erythropoiesis-stimulating agents) AND (IV) AND (Intravenous) AND (Screening) AND (Serum phosphate) AND (iron) AND (within 4 weeks prior to Screening))"}
{"candidate_id": "LLM02678", "doc_id": "NCT02299063_exc", "case_bucket": "or", "source_criterion": "recent surgery (< 3 months) previous chemotherapy previous transfusion of blood products neurodevelopmental disorders (including Trisomy 21) supplemental oxygen requirement (< 3 months) asthma requiring regular therapy obstructive sleep apnea the presence of concurrent infection or inflammation a known allergy to dexmedetomidine hydrochloride", "candidate_expression": "((< 3 months) AND (Trisomy 21) AND (allergy) AND (asthma) AND (chemotherapy) AND (concurrent) AND (dexmedetomidine hydrochloride) AND (infection) AND (inflammation) AND (neurodevelopmental disorders) AND (obstructive sleep apnea) AND (previous) AND (recent) AND (regular therapy) AND (requirement) AND (supplemental oxygen) AND (surgery) AND (transfusion of blood products))"}
{"candidate_id": "LLM02679", "doc_id": "NCT03477851_exc", "case_bucket": "or", "source_criterion": "No consent Spinal anesthesia or sciatic nerve block contraindicated Known intolerance to tramadol or other contraindications for the drug", "candidate_expression": "((No consent) AND (Spinal anesthesia) AND (contraindicated) AND (contraindications other) AND (intolerance) AND (sciatic nerve block) AND (the drug) AND (tramadol) AND NOT (consent))"}
{"candidate_id": "LLM02680", "doc_id": "NCT02498483_exc", "case_bucket": "other", "source_criterion": "Newborns of substance abusing mothers. Newborns with any contraindications to routine circumcision, anatomical or hematologic.", "candidate_expression": "((Newborns) AND (circumcision) AND (contraindications) AND (mothers) AND (substance abusing))"}
{"candidate_id": "LLM02681", "doc_id": "NCT02986659_exc", "case_bucket": "or", "source_criterion": "eGFR <45 Type 2 diabetes (HbA1c>6.5) or type 1 diabetes Any tobacco or nicotine product use in the past year Low vitamin B12 Levels (< 300 pg/mL) Self-reported severe difficulty or inability to walk 400m or climb 10 steps (from Q 2 and 19 on PAT-D) Self-reported difficulty or inability to perform basic ADL functions (from Q 10, 13, 14, 16 on PAT-D) Excessive alcohol use (>14 drinks/week) Cancer requiring treatment in past year (except skin) Dementia - diagnosed and/or MoCA score <18 Parkinson's or other neurological disease Chronic liver disease or cirrhosis End stage renal disease or on dialysis Rheumatic conditions (Rheumatoid arthritis, lupus, and any other autoimmune disease the -PI deems them to be ineligible for) Thyroid problems the PI deems them to be ineligible for Gout Involved in another interventional study Hemoglobin <8 or diagnosed with anemia Recent unintentional weight change (+/- 10 lbs. in the last 12 months) BMI <18.5 Likely to not follow the protocol PI deems unfit to participate Already taking Metformin or any other drug intended to treat diabetes", "candidate_expression": "((+/- 10 lbs.) AND (< 300 pg/mL) AND (<18) AND (<18.5) AND (<45) AND (<8) AND (>14 drinks/week) AND (>6.5) AND (BMI) AND (Cancer) AND (Chronic liver disease) AND (Dementia) AND (End stage renal disease) AND (Gout) AND (HbA1c) AND (Hemoglobin) AND (Involved in another interventional study) AND (Likely to not follow the protocol) AND (Metformin) AND (MoCA score) AND (Parkinson's) AND (Rheumatic conditions) AND (Rheumatoid arthritis) AND (Thyroid problems) AND (Type 2 diabetes) AND (alcohol use) AND (anemia) AND (autoimmune disease) AND (cirrhosis) AND (diabetes) AND (dialysis) AND (drug) AND (eGFR) AND (last 12 months) AND (lupus) AND (neurological disease) AND (nicotine product use) AND (past year) AND (tobacco) AND (treatment) AND (type 1 diabetes) AND (vitamin B12 Levels) AND (weight))"}
{"candidate_id": "LLM02682", "doc_id": "NCT03541980_inc", "case_bucket": "other", "source_criterion": "Any patient age 4-16 years with sickle cell disease who presents the Pediatric ER with acute sickle cell pain crisis with a pain of 6/10 or higher", "candidate_expression": "((4-16 years) AND (6/10 or higher) AND (Pediatric ER) AND (acute sickle cell pain crisis) AND (age) AND (pain) AND (sickle cell disease))"}
{"candidate_id": "LLM02683", "doc_id": "NCT02462590_inc", "case_bucket": "other", "source_criterion": "Adults = 18 years of age Admitted to any ICU and receiving invasive mechanical ventilation Anticipated ventilation of =72 hours at the time of screening, as per the ICU physician.", "candidate_expression": "((= 18 years) AND (=72 hours) AND (Adults) AND (Anticipated) AND (ICU) AND (age) AND (invasive) AND (mechanical ventilation) AND (ventilation))"}
{"candidate_id": "LLM02684", "doc_id": "NCT03431831_inc", "case_bucket": "or", "source_criterion": "Overweight/Obese Adult patients (age 19 years -65) eligible based on WALI screening tool", "candidate_expression": "((Adult) AND (WALI screening tool eligible) AND (age 19 years -65) AND ((Obese) OR (Overweight)))"}
{"candidate_id": "LLM02685", "doc_id": "NCT02959580_exc", "case_bucket": "other", "source_criterion": "Breast Carcinoma", "candidate_expression": "(Breast Carcinoma)"}
{"candidate_id": "LLM02686", "doc_id": "NCT02755701_inc", "case_bucket": "or", "source_criterion": "Age = 19 and = 70 years; Presence of liver cirrhosis Serum albumin level = 3.5g/dl, ultrasound or CT scan confirmed ascites (=Grade 1) No administration of diuretics and BCAA within the past 1 week Voluntary consent to take part in this trial", "candidate_expression": "((= 19 and = 70 years) AND (= 3.5g/dl) AND (Age) AND (Grade 1) AND (No) AND (Serum albumin) AND (Voluntary consent to take part in this trial) AND (ascites) AND (liver cirrhosis) AND (past 1 week) AND ((BCAA) OR (diuretics)) AND ((CT scan) OR (ultrasound)))"}
{"candidate_id": "LLM02687", "doc_id": "NCT03260881_exc", "case_bucket": "or", "source_criterion": "Patients with a personal or family history of medullary thyroid carcinoma or patients with Multiple Endocrine Neoplasia syndrome type 2 Patients with a prior serious hypersensitivity reaction to liraglutide Other contra-indications to liraglutide in accordance with risks and safety information included in the latest updated prescribing information Type 1 diabetes, as defined by ADA criteria Current use of other GLP-1A, dipeptidyl peptidase 4 (DPP4) or Sodium Glucose transporters 2 (SGLT2) inhibitors, thiazolidinediones (TZDs), pramlintide and fixed prandial insulin. Patients with unstable CAD, assessed by the Cardiology team and defined as new onset angina, rest angina, rapidly increasing or crescendo angina History of diabetic ketoacidosis, pancreas or beta-cell transplantation, or diabetes secondary to pancreatitis or pancreatectomy; acute or chronic infective diseases, cancer or chemotherapy, history of pulmonary, renal or liver diseases, and drug abuse Patients with chronic and acute inflammatory conditions such as sepsis, rheumatoid arthritis, ectopic dermatitis, asthma, ulcerative colitis. Current use of systemic corticosteroids in the 3 months prior this study. Pregnant or breast-feeding women Females of childbearing potential who are not using adequate contraceptive methods (as required by local law or practice)", "candidate_expression": "((ADA criteria) AND (Current) AND (Females of childbearing potential who are not using adequate contraceptive methods (as required by local law or practice)) AND (History) AND (Other) AND (Type 1 diabetes) AND (contra-indications) AND (hypersensitivity reaction) AND (in the 3 months prior this study) AND (inflammatory conditions) AND (liraglutide) AND (other) AND (prior) AND (secondary to) AND (serious) AND (systemic corticosteroids) AND (unstable CAD) AND ((GLP-1A) OR (Sodium Glucose transporters 2 (SGLT2) inhibitors) OR (dipeptidyl peptidase 4 (DPP4) inhibitors) OR (pramlintide) OR (prandial insulin) OR (thiazolidinediones (TZDs))) AND ((family history) OR (personal history)) AND ((crescendo angina) OR (new onset angina) OR (rapidly increasing angina) OR (rest angina)) AND ((beta-cell transplantation) OR (cancer) OR (chemotherapy) OR (diabetes) OR (diabetic ketoacidosis) OR (drug abuse) OR (infective diseases) OR (liver diseases) OR (pancreas transplantation) OR (pulmonary diseases) OR (renal diseases)) AND ((pancreatectomy) OR (pancreatitis)) AND ((acute) OR (chronic)) AND ((Multiple Endocrine Neoplasia syndrome type 2) OR (medullary thyroid carcinoma)) AND ((asthma) OR (ectopic dermatitis) OR (rheumatoid arthritis) OR (sepsis) OR (ulcerative colitis)) AND ((Pregnant) OR (breast-feeding women)))"}
{"candidate_id": "LLM02688", "doc_id": "NCT03355157_inc", "case_bucket": "or", "source_criterion": "Written informed consent prior to beginning specific protocol procedures, including expected cooperation of the patients for the treatment and follow-up, willingness and ability to complete collection of data via wearable device and study mobile must be obtained and documented according to the local regulatory requirements. Female or male patients. Age = 18 years old. Metastatic invasive hormone receptor positive and HER2 negative breast cancer (histologically confirmed). Patients who in the opinion of the treating physician are candidates suitable for randomization for mono-chemotherapy treatment, that has either an approved label in Europe and/or is supported by guidelines for the treatment of first-line advanced BC, which are based on evidence on safety and efficacy in this setting. Symptomatic or asymptomatic metastatic breast cancer. Resolution of all acute toxic effects of prior anti-cancer therapy or surgical procedures to NCI CTCAE version 4.0 grade = 1 (except alopecia or other toxicities not considered a safety risk for the patient at investigator's discretion). Life-expectancy > 6 months. For female patients: The patients need to be either A) of non-childbearing potential (documented postmenopausal or post hysterectomy) B) childbearing potential with negative serum or urinary pregnancy test (in this case patients need to use highly effective non-hormonal contraceptive methods).", "candidate_expression": "((Age = 18 years old Metastatic invasive hormone receptor positive) AND (Life-expectancy > 6 months) AND (NCI CTCAE version 4.0 grade = 1) AND (acute toxic effects Resolution) AND (alopecia) AND (breast cancer HER2 negative) AND (except) AND (metastatic breast cancer) AND (or female patients: The patients need to be either A) of non-childbearing potential (documented postmenopausal or post hysterectomy) B) childbearing potential with negative serum or urinary pregnancy test (in this case patients need to use highly effective non-hormonal contraceptive methods).) AND ((Symptomatic) OR (asymptomatic)) AND ((Female) OR (male)) AND ((anti-cancer therapy) OR (surgical procedure)))"}
{"candidate_id": "LLM02689", "doc_id": "NCT02101554_inc", "case_bucket": "or", "source_criterion": "Children 7-17 with moderate to severe pain requiring around the clock treatment with an opioid analgesic. Be an experienced opioid user, defined as any subject treated with opioid therapy, equivalent or equal to >20 mg per day of morphine, for a period of 3 consecutive days immediately prior to first day of dosing.", "candidate_expression": "((Children) AND (around the clock treatment) AND (morphine >20 mg per day) AND (morphine equivalent >20 mg per day) AND (opioid analgesic) AND (opioid therapy 3 consecutive days immediately prior to first day of dosing) AND (pain) AND ((moderate) OR (severe)))"}
{"candidate_id": "LLM02690", "doc_id": "NCT02515773_inc", "case_bucket": "or", "source_criterion": "Inpatient or outpatient age 8-19 years inclusive; participants must live with a parent, guardian, or caregiver; Fluent in English; Diagnosed or told by a clinician that they have any of the following bipolar spectrum disorders (BSD): bipolar I, bipolar II, unspecified bipolar and related disorders, Disruptive Mood Dysregulation Disorder (DMDD), cyclothymic disorder, other specified bipolar and related disorders, as well as mood disorder not otherwise specified (if diagnosed in the past as per DSM-IV); Body mass index >85%ile for age and sex by standard growth charts; Received a new or ongoing prescription for at least one SGA (i.e., olanzapine, clozapine, risperidone, quetiapine, aripiprazole, ziprasidone, iloperidone, lurasidone, paliperidone, brexpiprazole or cariprazine) that is not prescribed as a PRN medication;", "candidate_expression": "((BSD) AND (Body mass index >85%ile) AND (DMDD) AND (Disruptive Mood Dysregulation Disorder) AND (Inpatient) AND (SGA at least one) AND (age 8-19 years) AND (aripiprazole) AND (bipolar I) AND (bipolar II) AND (bipolar spectrum disorders) AND (brexpiprazole) AND (cariprazine) AND (clozapine) AND (cyclothymic disorder) AND (iloperidone) AND (lurasidone) AND (mood disorder not otherwise specified) AND (olanzapine) AND (other specified bipolar and related disorders) AND (outpatient) AND (paliperidone) AND (quetiapine) AND (risperidone) AND (unspecified bipolar and related disorders) AND (ziprasidone))"}
{"candidate_id": "LLM02691", "doc_id": "NCT02823808_exc", "case_bucket": "or", "source_criterion": "The use of weight-lowering drugs, any investigational blood-glucose or lipid-lowering agent (other than statins or ezetimibe) within the past 3 months Previous treatment with systemic corticosteroids or a change in dosage of thyroid hormones in the previous 6 weeks The use of insulin within the 3 months prior to screening Others", "candidate_expression": "((change in dosage) AND (insulin) AND (investigational) AND (other) AND (past 3 months) AND (previous 6 weeks) AND (screening) AND (weight-lowering) AND (within the 3 months prior to screening) AND ((ezetimibe) OR (statins)) AND ((systemic corticosteroids) OR (thyroid hormones)) AND ((blood-glucose) OR (lipid-lowering)) AND ((agent) OR (drugs)))"}
{"candidate_id": "LLM02692", "doc_id": "NCT00752310_inc", "case_bucket": "or", "source_criterion": "Non-smoking, or smoking no more than 10 cigarettes, or 2 cigars, or 2 pipes per day for at least 3 months prior to selection Normal weight as defined by a Body Mass Index (BMI, weight in kg divided by the square of height in meters) of 18.0 to 30.0 kg/m2, extremes included Able to comply with protocol requirements. Healthy on the basis of a medical evaluation that reveals the absence of any clinically relevant abnormality and includes a physical examination, medical history, electrocardiogram (ECG), vital signs, and the results of blood biochemistry, blood coagulation, and hematology tests and a urinalysis carried out at screening.", "candidate_expression": "((Able to comply with protocol requirements) AND (BMI) AND (Body Mass Index 18.0 to 30.0 kg/m2, extremes included) AND (ECG) AND (Healthy) AND (Normal weight selection) AND (blood biochemistry tests) AND (blood coagulation tests) AND (cigarettes no more than 10 per day) AND (cigars no more than 2 per day) AND (electrocardiogram) AND (hematology tests) AND (medical evaluation at screening) AND (medical history) AND (physical examination) AND (pipes no more than 2 per day) AND (smoking for at least 3 months prior to selection) AND (urinalysis) AND (vital signs) AND (weight in kg divided by the square of height in meters) AND NOT (smoking) AND NOT (abnormality clinically relevant))"}
{"candidate_id": "LLM02693", "doc_id": "NCT02015494_inc", "case_bucket": "other", "source_criterion": "Males and females aged 18-40 years of age at the time of vaccination in good health as determined by medical history, physical exam, laboratory assessments and the clinical judgment of the Principal Investigator Able to provide informed consent indicating that they understand the purpose of this study and are willing to adhere to the procedures described in this protocol If the subject is a female of childbearing potential, she must use adequate contraceptive precautions (e.g., intrauterine contraceptive device, oral contraceptives or other equivalent hormonal contraception) for 2 months prior to vaccination and continue to use such precautions for a minimum of three months after vaccination. She must also have a negative urine pregnancy test within 24 hours prior to receiving study vaccine. Women at least one year post-menopausal or surgically sterile will not be considered of childbearing potential. Willing to receive the unlicensed vaccine given as an IM injection Willing to provide multiple blood specimens collected by venipuncture", "candidate_expression": "((IM injection) AND (If the subject is a female of childbearing potential, she must use adequate contraceptive precautions (e.g., intrauterine contraceptive device, oral contraceptives or other equivalent hormonal contraception) for 2 months prior to vaccination and continue to use such precautions for a minimum of three months after vaccination. She must also have a negative urine pregnancy test within 24 hours prior to receiving study vaccine. Women at least one year post-menopausal or surgically sterile will not be considered of childbearing potential.) AND (Males) AND (age 18-40 years) AND (aged 18-40 years) AND (females) AND (good health) AND (laboratory assessments) AND (medical history) AND (physical exam) AND (the clinical judgment of the Principal Investigator) AND (vaccine))"}
{"candidate_id": "LLM02694", "doc_id": "NCT02618057_inc", "case_bucket": "or", "source_criterion": "Evidence of Mycoplasma pneumoniae infection Lobar pneumonia or pneumoniae with pleural effusion", "candidate_expression": "((Lobar pneumonia) AND (Mycoplasma pneumoniae infection) AND (pleural effusion) AND (pneumoniae))"}
{"candidate_id": "LLM02695", "doc_id": "NCT03033745_inc", "case_bucket": "or", "source_criterion": "Male or female on stable dose of IgPro20 (Hizentra) therapy. Women of childbearing potential must be using and agree to continue using medically approved contraception (which must be discussed with the study doctor) and must have a negative pregnancy test at screening. Subjects with PID, eg, with a diagnosis of common variable immunodeficiency or X-linked agammaglobulinemia, as defined by the Pan American Group for Immune Deficiency and the European Society of Immune Deficiencies. With infusion parameters as specified below: Experience with pump-assisted infusions of IgPro20 at the tolerated flow rate of 25 mL/h per injection site for at least 1 month prior to Day 1. Total weekly IgPro20 dose of = 50 mL (= 10 g). Experience with pump-assisted infusions of IgPro20 at tolerated volumes of 25 mL/injection site for at least 1 month prior to Day 1. Experience with frequent (2-7 times per week) infusions of IgPro20 at the tolerated flow rate of approximately 0.5 mL/min (equivalent of 25-30 mL/h) per injection site for at least 1 month prior to Day 1. The dose (volume) per injection site should not exceed 25 mL.", "candidate_expression": "((2-7 times per week) AND (25-30 mL/h) AND (= 10 g) AND (= 50 mL) AND (Day 1) AND (Hizentra) AND (IgPro20) AND (PID) AND (Women of childbearing potential must be using and agree to continue using medically approved contraception (which must be discussed with the study doctor) and must have a negative pregnancy test at screening) AND (exceed 25 mL.) AND (flow rate of 25 mL/h per injection site) AND (for at least 1 month prior to Day 1) AND (frequent) AND (not) AND (per injection site flow rate of approximately 0.5 mL/min) AND (pump-assisted infusions) AND (stable dose) AND (tolerated) AND (volumes of 25 mL/injection site) AND (weekly) AND ((Male) OR (female)) AND ((European Society of Immune Deficiencies) OR (Pan American Group for Immune Deficiency)) AND ((X-linked agammaglobulinemia) OR (common variable immunodeficiency)))"}
{"candidate_id": "LLM02696", "doc_id": "NCT02698969_exc", "case_bucket": "or", "source_criterion": "Clinical diagnosis of hepatic or renal disease Clinical diagnosis of chronic or acute alcoholism History of allergy or hypersensitivity to Sugammadex and/or atropine or Neostigmine Current medications with CNS effects History of neurologic disease Diaphragmatic palsy Pregnancy or nursing History of malignant arrhythmias", "candidate_expression": "((CNS effects) AND (Clinical diagnosis) AND (Diaphragmatic palsy) AND (History) AND (Neostigmine) AND (Pregnancy) AND (Sugammadex) AND (acute) AND (alcoholism) AND (allergy) AND (atropine) AND (chronic) AND (hepatic disease) AND (hypersensitivity) AND (malignant arrhythmias) AND (medications) AND (neurologic disease) AND (nursing) AND (renal disease))"}
{"candidate_id": "LLM02697", "doc_id": "NCT02735577_exc", "case_bucket": "or", "source_criterion": "Risk of severe alcohol withdrawal (e.g. history of seizures or delirium tremens) Current Moderate or Severe Substance Use Disorder, other than Alcohol, Nicotine or Caffeine Use Disorders Lifetime history of Bipolar Disorder, Schizophrenia or Schizoaffective Disorder Any current psychiatric disorder, other than Alcohol Use Disorder, that, in the judgment of the investigator, will require treatment that will interfere with study participation. Current severe depression (HAM-D >24) or anxiety (HAM-A >24) Significant suicide or violence risk Currently taking any psychotropic medications Legally mandated to participate in treatment History of prior treatment with disulfiram Sufficiently socially unstable as to preclude participation (e.g. homeless) Contraindications to disulfiram treatment (liver disease, kidney disease, cardiac disease, seizure disorder, hypothyroidism, diabetes mellitus, pregnancy or lactation, allergy to disulfiram or thiuran derivatives) Neurological or medical conditions that would interfere with MRI scanning (e.g. history of stroke, seizure, brain tumor, brain infection, traumatic brain injury, multiple sclerosis, dementia, metal device in body, pregnancy, claustrophobia, color blindness, severe hearing impairment, weight>300 lbs., wheelchair-bound) Currently taking medications containing alcohol, metronidazole, isoniazid, paraldehyde, phenytoin, warfarin, or theophylline. Significant alcohol withdrawal (CIWA>8) at screening, after confirming a blood alcohol level of zero.", "candidate_expression": "((Alcohol Use Disorders) AND (Bipolar Disorder) AND (CIWA >8) AND (Caffeine Use Disorders) AND (Contraindications) AND (HAM-A >24) AND (HAM-D >24) AND (MRI scanning) AND (Nicotine Use Disorders) AND (Schizoaffective Disorder) AND (Schizophrenia) AND (Substance Use Disorder Current) AND (alcohol) AND (alcohol withdrawal Risk of severe) AND (alcohol withdrawal Significant at screening) AND (allergy) AND (anxiety) AND (blood alcohol level zero) AND (brain infection) AND (brain tumor) AND (cardiac disease) AND (claustrophobia) AND (color blindness) AND (conditions Neurological) AND (delirium tremens Moderate Severe) AND (dementia) AND (depression severe severe) AND (diabetes mellitus) AND (disulfiram) AND (disulfiram History of prior treatment) AND (hearing impairment severe) AND (hypothyroidism) AND (interfere) AND (isoniazid) AND (kidney disease) AND (lactation) AND (liver disease) AND (medical conditions) AND (metal device in body) AND (metronidazole) AND (multiple sclerosis) AND (paraldehyde) AND (phenytoin) AND (pregnancy) AND (psychiatric disorder current) AND (psychotropic medications Currently) AND (seizure) AND (seizure disorder) AND (seizures) AND (socially unstable Sufficiently) AND (stroke) AND (suicide risk) AND (theophylline) AND (thiuran derivatives) AND (traumatic brain injury) AND (violence risk) AND (warfarin) AND (weight >300 lbs.) AND (wheelchair-bound) AND NOT (Alcohol Use Disorder))"}
{"candidate_id": "LLM02698", "doc_id": "NCT00543712_exc", "case_bucket": "or", "source_criterion": "Systemic therapy or radiotherapy within 4 weeks prior to Day 1 Prior therapy with agents targeting the DR5 apoptosis pathway Major surgical procedure, open biopsy, or significant traumatic injury within 4 weeks prior to Day 1, or anticipation of need for major surgical procedure during the course of the study Other invasive malignancies within 5 years prior to Day 1 Known active brain metastases Uncontrolled intercurrent illness, including but not limited to ongoing or active infection requiring parenteral antibiotics at enrollment Clinically significant, symptomatic cardiovascular disease, New York Heart Association (NYHA) Grade II or greater congestive heart failure, serious cardiac arrhythmia, Grade II or greater peripheral vascular disease, or history of major heart surgery within 6 months of Day 1, or any situation that would likely limit compliance with study requirements Known to be positive for hepatitis C or hepatitis B surface antigen History of other disease, metabolic dysfunction, physical examination finding, or clinical laboratory finding giving reasonable suspicion of a disease or condition that contraindicates use of an investigational drug or that might affect interpretation of the results of the study or render the patient at high risk for treatment complications Use of anticoagulation therapy Participation in clinical trials or undergoing other investigational procedures within 30 days prior to Day 1 Pregnancy or breast feeding Known sensitivity to any of the products administered during the study Any disorder that compromises the ability of the patient to give written informed consent and/or comply with study procedures", "candidate_expression": "((New York Heart Association (NYHA) Grade II or greater) AND (Participation in clinical trials) AND (Pregnancy) AND (Systemic therapy) AND (affect interpretation of the results) AND (agents targeting the DR5 apoptosis pathway) AND (anticoagulation) AND (anticoagulation therapy) AND (any of the products administered during the study) AND (brain metastases active active) AND (breast feeding) AND (cardiac arrhythmia serious Grade II or greater) AND (cardiovascular disease Clinically significant symptomatic) AND (clinical laboratory) AND (clinical laboratory finding suspicion of) AND (comply with study procedures) AND (condition) AND (congestive heart failure) AND (contraindicates) AND (disease) AND (disease History other) AND (give written informed consent) AND (heart surgery history of major) AND (hepatitis B surface antigen) AND (hepatitis C) AND (infection ongoing active) AND (intercurrent illness Uncontrolled) AND (invasive malignancies Other within 5 years prior to Day 1) AND (investigational drug) AND (limit compliance) AND (metabolic dysfunction) AND (open biopsy) AND (parenteral antibiotics at enrollment) AND (peripheral vascular disease) AND (physical examination) AND (physical examination finding) AND (radiotherapy) AND (render the patient at high risk) AND (sensitivity) AND (surgical procedure Major) AND (surgical procedure anticipation of need major during the course of the study the study) AND (therapy Day 1 Prior) AND (traumatic injury significant Day 1) AND (treatment complications) AND (undergoing other investigational procedures prior to Day 1) AND NOT (disorder))"}
{"candidate_id": "LLM02699", "doc_id": "NCT02804646_exc", "case_bucket": "or", "source_criterion": "1) pregnancy, breast-feeding women, or female patients of childbearing potential but did not take contraceptive measures;2) existing severe acute infection and is not controlled; or purulent and chronic infection, delayed healing wounds; 3) the original severe heart disease, including congestive heart failure, uncontrolled high-risk arrhythmias, unstable angina, myocardial infarction, severe heart valve disease and resistant hypertension; 4) suffering from neurological and psychiatric diseases or mental disorders is not easy to control, poor compliance, and can not be described with treatment responders; primary brain or central nervous metastasis disease has not been controlled, with significant cranial hypertension or neuropsychiatric symptoms; 5) have bleeding tendencies; 6) other researchers believe that patients should not participate in the present trial.", "candidate_expression": "((acute) AND (arrhythmias) AND (bleeding tendencies) AND (central nervous metastasis disease) AND (chronic) AND (congestive heart failure) AND (controlled) AND (cranial hypertension) AND (delayed healing wounds) AND (heart disease) AND (heart valve disease) AND (high-risk) AND (hypertension) AND (infection) AND (mental disorders) AND (myocardial infarction) AND (neurological diseases) AND (neuropsychiatric symptoms) AND (not) AND (not controlled) AND (poor compliance) AND (pregnancy, breast-feeding women, or female patients of childbearing potential but did not take contraceptive measures;) AND (primary brain disease) AND (psychiatric diseases) AND (purulent) AND (resistant) AND (severe) AND (significant) AND (uncontrolled) AND (unstable angina))"}
{"candidate_id": "LLM02700", "doc_id": "NCT03019562_inc", "case_bucket": "other", "source_criterion": "19-65 years of age ASA physical status classification I or II Scheduled for total hip replacement surgery", "candidate_expression": "((ASA physical status classification I or II) AND (age 19-65 years) AND (total hip replacement surger Scheduled for))"}
```
