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
{"candidate_id": "LLM01101", "doc_id": "NCT00351611_inc", "case_bucket": "other", "source_criterion": "Epilepsy partial seizure subjects. Currently taking 1 to 3 antiepileptic drugs.", "candidate_expression": "((Epilepsy) AND (antiepileptic drugs 1 to 3) AND (partial seizure))"}
{"candidate_id": "LLM01102", "doc_id": "NCT02689024_exc", "case_bucket": "or", "source_criterion": "multiple injuries (polytrauma patients) previous adverse reaction or known allergy to local anaesthetics or opioids or paracetamol skin infection in proximity of injection site delirious state at presentation in the ED", "candidate_expression": "((adverse reaction) AND (allergy) AND (delirious) AND (injection site) AND (local anaesthetics) AND (multiple injuries) AND (opioids) AND (paracetamol) AND (polytrauma) AND (skin infection))"}
{"candidate_id": "LLM01103", "doc_id": "NCT03106389_inc", "case_bucket": "other", "source_criterion": "NA", "candidate_expression": "(EMPTY)"}
{"candidate_id": "LLM01104", "doc_id": "NCT03344042_inc", "case_bucket": "or", "source_criterion": "parturient in labour without cervical dilation and regular uterine contractions", "candidate_expression": "((labour) AND (parturient) AND (without) AND ((cervical dilation) OR (regular uterine contractions)))"}
{"candidate_id": "LLM01105", "doc_id": "NCT02635893_inc", "case_bucket": "or", "source_criterion": "Male and females between ages 18-85 years of age SCI ( =1 month of injury) ASIA A, B,C and D SCI above L5 Able to perform a visible contraction with dorsiflexor and hip flexor muscles (allowing testing of largely impaired patients) Able to ambulate a few steps with or without an assistive device Male and females between ages 18-85 years of age Able to walk and complete lower-limb tests with both legs", "candidate_expression": "((ASIA A, B,C and D) AND (Able to ambulate a few steps with assistive device without an assistive device) AND (Able to complete lower-limb tests with both legs) AND (Able to walk) AND (Male) AND (SCI =1 month of injury) AND (SCI above L5) AND (ages between 18-85 years of age) AND (females) AND (l))"}
{"candidate_id": "LLM01106", "doc_id": "NCT01650792_inc", "case_bucket": "other", "source_criterion": "Diagnosis of heart failure according to Framingham criteria Informed consent Age 18 years or above", "candidate_expression": "((Age 18 years or above) AND (Informed consent) AND (heart failure Framingham criteria))"}
{"candidate_id": "LLM01107", "doc_id": "NCT01401335_inc", "case_bucket": "other", "source_criterion": "100 orphans/vulnerable youth aged 15 to 25 will be recruited through their participation at the day care center, on a voluntary basis.", "candidate_expression": "(EMPTY)"}
{"candidate_id": "LLM01108", "doc_id": "NCT02965443_exc", "case_bucket": "or", "source_criterion": "Use of any oral antidiabetic treatment except for metformin (i.e., sulphonylureas, DPP-IV inhibitors, thiazolidinediones, SGLT-2 inhibitors (Sodium dependent glucose transporter) or GLP-1 analogues (glucagone like peptide) within the last three months prior to Screening Repeated episodes of severe hypoglycaemia within the last six months prior to Screening History of diabetic ketoacidosis, precoma diabetica, or diabetic coma Treatment with any other investigational drug within the last three months before Screening Acute infections within the last four weeks prior to Screening Recurrent urogenital infections History of pancreatitis Anamnestic history of hypersensitivity to the study drugs or to drugs with similar chemical structures History of severe or multiple allergies Concomitant participation in other clinical trials Type 1 diabetes Cardiovascular disease Clinically relevant ventricular tachycardia or ventricular fibrillation, 3rd degree AV block or Torsades de Pointes or treatment with antiarrhythmic drugs. Percutaneous coronary intervention within the past 6 months. Any of the following within the past 6 months: myocardial infarction (MI), coronary artery bypass surgery; unstable angina; or stroke. Malignancy including leukemia and lymphoma within the last 5y. Liver disease such as cirrhosis or chronic active hepatitis. Significant renal dysfunction (see also exclusion criteria laboratory abnormalities). State after kidney transplantation Endocrine disease: Systolic blood pressure outside the range of 100-160 mmHg or diastolic blood pressure above 95 mmHg at Screening History of active substance abuse (including alcohol > 40g/day) within the past 2 years. Pregnancy or childbearing potential without adequate contraception Present therapy with systemic steroids Presence of psychiatric disorder or intake of anti-depressive or anti-psychotic agents with the exception of benzodiazepines and SSRIs/SNRI's (selective serotonin reuptake inhibitor) Potentially unreliable subjects, and those judged by the investigator to be unsuitable for the study. Contraindications for Magnetic resonance (MR) scanning such as persons with cardiac pacemaker and implants out of metal or claustrophobia", "candidate_expression": "((> 40g/day) AND (Acute infections) AND (Anamnestic history) AND (Cardiovascular disease) AND (Clinically relevant) AND (Concomitant) AND (Contraindications) AND (Endocrine disease) AND (History) AND (Liver disease) AND (Magnetic resonance (MR) scanning) AND (Malignancy) AND (Percutaneous coronary intervention) AND (Present) AND (Recurrent) AND (Repeated) AND (Screening) AND (Significant) AND (State after kidney transplantation) AND (Treatment) AND (Type 1 diabetes) AND (above 95 mmHg) AND (active) AND (adequate) AND (alcohol) AND (allergies) AND (antiarrhythmic drugs) AND (at Screening) AND (contraception) AND (except for) AND (hypersensitivity) AND (investigational drug) AND (kidney transplantation) AND (metformin) AND (oral antidiabetic) AND (oral antidiabetic treatment) AND (outside the range of 100-160 mmHg) AND (pancreatitis) AND (participation in other clinical trials) AND (psychiatric disorder) AND (renal dysfunction) AND (severe hypoglycaemia) AND (substance abuse) AND (systemic steroids) AND (therapy) AND (urogenital infections) AND (with the exception of) AND (within the last 5y) AND (within the last four weeks prior to Screening) AND (within the last six months prior to Screening) AND (within the last three months before Screening) AND (within the last three months prior to Screening) AND (within the past 2 years) AND (within the past 6 months) AND (without) AND ((anti-depressive agents) OR (anti-psychotic agents)) AND ((SNRI's) OR (SSRIs) OR (benzodiazepines)) AND ((unreliable subjects) OR (unsuitable for the study)) AND ((cardiac pacemaker) OR (claustrophobia) OR (implants out of metal)) AND ((diabetic coma) OR (diabetic ketoacidosis) OR (precoma diabetica)) AND ((drugs with similar chemical structures) OR (study drugs)) AND ((multiple) OR (severe)) AND ((3rd degree AV block) OR (Torsades de Pointes) OR (treatment) OR (ventricular fibrillation) OR (ventricular tachycardia)) AND ((DPP-IV inhibitors) OR (GLP-1 analogues) OR (SGLT-2 inhibitors) OR (sulphonylureas) OR (thiazolidinediones)) AND ((coronary artery bypass surgery) OR (myocardial infarction (MI)) OR (stroke) OR (unstable angina)) AND ((leukemia) OR (lymphoma)) AND ((chronic active hepatitis) OR (cirrhosis)) AND ((Systolic blood pressure) OR (diastolic blood pressure)) AND ((Pregnancy) OR (childbearing potential)))"}
{"candidate_id": "LLM01109", "doc_id": "NCT02550080_inc", "case_bucket": "or", "source_criterion": "Diagnosed with cutaneous vasculitis, urticaria, psoriasis, acne, bullous skin diseases, sterile pustulosis, leprosy, pneumocystis pneumonia and any other patients who need dapsone administration. Subjects are dapsone-naive. All subjects must have a clinical need for treatment with dapsone that precedes the decision to participate in the study. All subjects are willing to complete the 6-weeks period clinical trial. All subjects are written informed consent.", "candidate_expression": "((All subjects are willing to complete the 6-weeks period clinical trial) AND (All subjects are written informed consent) AND NOT (dapsone) AND ((acne) OR (bullous skin diseases) OR (cutaneous vasculitis) OR (dapsone) OR (leprosy) OR (pneumocystis pneumonia) OR (psoriasis) OR (sterile pustulosis) OR (urticaria)))"}
{"candidate_id": "LLM01110", "doc_id": "NCT02924090_exc", "case_bucket": "or", "source_criterion": "Relative contraindications to ECT therapy (recent MI or CVA, increased intracranial pressure, intracranial mass lesion, intracranial aneurysm, epilepsy, known cardiac arrhythmia, pheochromocytoma, pregnancy) Contraindications to etomidate (sepsis, primary or secondary adrenal insufficiency, porphyria) DSM-V diagnosis of a lifetime history of psychotic spectrum disorder Drug or alcohol dependence, or abuse within the past 3 months, soy-bean oil allergy", "candidate_expression": "((CVA) AND (Contraindications) AND (DSM-V) AND (Drug abuse) AND (Drug dependence) AND (ECT therapy) AND (MI) AND (Relative contraindications) AND (adrenal insufficiency) AND (alcohol abuse) AND (alcohol dependence) AND (cardiac arrhythmia) AND (epilepsy) AND (etomidate) AND (increased) AND (intracranial aneurysm) AND (intracranial mass lesion) AND (intracranial pressure) AND (lifetime history) AND (pheochromocytoma) AND (porphyria) AND (pregnancy) AND (primary) AND (psychotic spectrum disorder) AND (recent) AND (secondary) AND (sepsis) AND (soy-bean oil allergy) AND (within the past 3 months))"}
{"candidate_id": "LLM01111", "doc_id": "NCT02426034_inc", "case_bucket": "or", "source_criterion": "Age: 18 to75 years old; Pathologically diagnosed with advanced gastric cancer (including adenocarcinoma of the gastroesophageal junction) with measurable metastases outside the stomach (measuring = 10mm on spiral CT scan, satisfying the criteria in RECIST 1.1); Failure of prior therapy (during or after treatment) in patients who have received at least two prior chemotherapy regimens; ECOG PS of 0-2; HB = 90g / L ANC = 1.5 × 109 / L PLT = 80 × 109 / L Bilirubin <1.25 times the upper limit of normal (ULN) ALT and AST <2.5 × ULN; liver metastases, if any, the ALT and AST<5 × ULN Serum Cr = 1 × ULN endogenous creatinine clearance>50ml/min (Cockcroft-Gault formula) An expected survival of = 3 months; Patient received apatinib treatment regimen at investigators' discretion; Patient has to voluntarily join the study and sign the Informed Consent Form for the study; Pregnancy test (serum or urine) has to be performed for woman of childbearing age within 7 days before enrolment and the test result must be negative. They shall take appropriate methods for contraception during the study until the 8th week post the last administration of study drug. For men, (previous surgical sterilization accepted), shall agree to take appropriate methods of contraception during the study until the 8th week post the last administration of study drug.", "candidate_expression": "((0-2) AND (18 to75 years old) AND (<1.25 times the upper limit of normal) AND (<2.5 × ULN) AND (<5 × ULN) AND (= 1 × ULN) AND (= 1.5 × 109 / L) AND (= 3 months) AND (= 80 × 109 / L) AND (= 90g / L) AND (>50ml/min) AND (ALT) AND (ANC) AND (AST) AND (Age) AND (Bilirubin) AND (ECOG PS) AND (Failure) AND (HB) AND (PLT) AND (Patient has to voluntarily join the study and sign the Informed Consent Form for the study;) AND (Pregnancy test (serum or urine) has to be performed for woman of childbearing age within 7 days before enrolment and the test result must be negative. They shall take appropriate methods for contraception during the study until the 8th week post the last administration of study drug. For men, (previous surgical sterilization accepted), shall agree to take appropriate methods of contraception during the study until the 8th week post the last administration of study drug) AND (Serum Cr) AND (adenocarcinoma) AND (advanced gastric cancer) AND (apatinib) AND (at least two) AND (chemotherapy) AND (endogenous creatinine clearance) AND (expected survival) AND (gastroesophageal junction) AND (liver metastases) AND (metastases) AND (outside) AND (stomach))"}
{"candidate_id": "LLM01112", "doc_id": "NCT02984475_exc", "case_bucket": "or", "source_criterion": "Patients with renal impairment (serum creatinine more than twice the upper limit of normal). Patients with heart failure. Patients with sepsis or active infection. Patients with diabetes mellitus (either primary or secondary to thalassemia). regular consumption of medication with potential hepatotoxicity. regular herbal medicine or antioxidant supplementation. patients with gastrointestinal conditions preventing adsorption of oral medication.", "candidate_expression": "((active infection) AND (antioxidant supplementation) AND (diabetes mellitus) AND (heart failure) AND (hepatotoxicity) AND (herbal medicine) AND (medication) AND (more than twice the upper limit of normal) AND (primary) AND (renal impairment) AND (secondary to thalassemia) AND (sepsis) AND (serum creatinine))"}
{"candidate_id": "LLM01113", "doc_id": "NCT02224040_exc", "case_bucket": "or", "source_criterion": "Allergy to ceftriaxone or macrolides Major typhoid fever-associated complications Inability to swallow oral medication Underlying illness Pregnancy Lactation Treatment within the past 4 days with an antibiotic that may be effective against typhoid fever", "candidate_expression": "((Allergy) AND (Inability to swallow oral medication) AND (Lactation) AND (Major) AND (Pregnancy) AND (Underlying illness) AND (antibiotic) AND (ceftriaxone) AND (complications) AND (effective against typhoid fever) AND (macrolides) AND (oral medication) AND (typhoid fever) AND (typhoid fever-associated) AND (within the past 4 days))"}
{"candidate_id": "LLM01114", "doc_id": "NCT02156999_inc", "case_bucket": "other", "source_criterion": "Osteoporosis", "candidate_expression": "(Osteoporosis)"}
{"candidate_id": "LLM01115", "doc_id": "NCT03236246_inc", "case_bucket": "or", "source_criterion": "Estimated glomerular filtration rate =20 mL/min and <60 mL/min Hgb =8.5 g/dL and =11.5 g/dL Serum ferritin =500 ng/mL and transferrin saturation (TSAT) =25% Serum intact parathyroid hormone =600 pg/mL", "candidate_expression": "((Estimated glomerular filtration rate =20 mL/min and <60 mL/min) AND (Hgb =8.5 g/dL and =11.5 g/dL) AND (Serum ferritin =500 ng/mL) AND (Serum intact parathyroid hormone =600 pg/mL) AND (TSAT) AND (transferrin saturation =25%))"}
{"candidate_id": "LLM01116", "doc_id": "NCT02894372_inc", "case_bucket": "or", "source_criterion": "Patients after throat surgeries: tonsillectomy, adenotonsillectomy, uvulopalatoplasty, uvulopalatopharyngoplasty Patients with acute throat diseases: pharyngitis, tonsillitis, pharyngotonsillitis", "candidate_expression": "((acute throat diseases) AND (adenotonsillectomy) AND (throat surgeries) AND (tonsillectomy) AND (uvulopalatopharyngoplasty) AND (uvulopalatoplasty) AND ((pharyngitis) OR (pharyngotonsillitis) OR (tonsillitis)))"}
{"candidate_id": "LLM01117", "doc_id": "NCT02445339_exc", "case_bucket": "or", "source_criterion": "Active opioid dependence Acute or chronic pain requiring opioid treatment Acute liver injury (liver aminotransferase concentrations >5 times the upper limit of normal) Health condition considered unsafe for inclusion (at discretion of PI and/or attending physician) Lack of capacity or willingness to consent Currently prescribed pharmacotherapy for alcohol dependence (not including treatment of acute alcohol withdrawal syndrome) Previous significant adverse reaction to naltrexone or diluent Pregnant, nursing, or not using effective methods of birth control Prisoners (as defined by Office of Human Research Protection) at the time of enrollment ARE NOT ELIGIBLE for study entry. However, subjects who become prisoners after being enrolled will be included and not be withdrawn from the study. Patients on parole or probation are eligible for enrollment.", "candidate_expression": "((>5 times the upper limit of normal) AND (Active) AND (Acute liver injury) AND (Currently) AND (Health condition) AND (Lack of) AND (Office of Human Research Protection) AND (Previous) AND (Prisoners) AND (acute alcohol withdrawal syndrome) AND (adverse reaction) AND (alcohol dependence) AND (at the time of enrollment) AND (considered unsafe for inclusion) AND (effective methods) AND (liver aminotransferase concentrations) AND (not) AND (not including) AND (opioid dependence) AND (opioid treatment) AND (pain) AND (pharmacotherapy) AND (significant) AND (the time of enrollment) AND (treatment) AND ((capacity to consent) OR (willingness to consent)) AND ((diluent) OR (naltrexone)) AND ((Acute) OR (chronic)) AND ((Pregnant) OR (birth control) OR (nursing)))"}
{"candidate_id": "LLM01118", "doc_id": "NCT03011476_inc", "case_bucket": "or", "source_criterion": "Parkinson disease diagnosed by United Kingdom Parkinson's disease Society Brain Bank Criteria Postural instability and gait disturbance phenotype Hoehn and Yahr stage = 3 Mini-Mental status examination = 24", "candidate_expression": "((= 2) AND (Hoehn and Yahr) AND (Mini-Mental status examination) AND (Parkinson disease) AND (Postural instability) AND (United Kingdom Parkinson's disease Society Brain Bank Criteria) AND (gait disturbance) AND (stage = 3))"}
{"candidate_id": "LLM01119", "doc_id": "NCT02734173_exc", "case_bucket": "or", "source_criterion": "<18 years old Evidence of decompensated liver disease HOMA IR< 2.0 HIV seropositivity Chronic HBV/HIV infection Use of immune suppressing medications Active malignancy", "candidate_expression": "((< 2.0) AND (<18 years) AND (Active) AND (HIV) AND (HOMA IR) AND (decompensated) AND (immune suppressing medications) AND (liver disease) AND (malignancy) AND (old) AND (seropositivity) AND ((HIV infection Chronic) OR (infection Chronic HBV)))"}
{"candidate_id": "LLM01120", "doc_id": "NCT03011177_exc", "case_bucket": "other", "source_criterion": "NA", "candidate_expression": "(EMPTY)"}
{"candidate_id": "LLM01121", "doc_id": "NCT02243553_inc", "case_bucket": "other", "source_criterion": "1. Signed informed consent 2. Healthy subjects aged between 18 years and 45 years inclusive 3. Weighing at least 50 kg 4. Volunteers must be hospitalized on Days 1-4, 7-9, and 17-20 for pharmacokinetic assessments for each biomarker and TPV/r (Days 7-9 and 17-20) 5. Volunteers must be willing to complete all study-related activities 6. Each volunteer must have a valid social security number 7. Each volunteer must have acceptable medical history, physical examination and laboratory test", "candidate_expression": "((Each volunteer must have a valid social security number) AND (Each volunteer must have acceptable medical history, physical examination and laboratory test) AND (Healthy) AND (Signed informed consent) AND (Volunteers must be hospitalized on Days 1-4, 7-9, and 17-20 for pharmacokinetic assessments for each biomarker and TPV/r (Days 7-9 and 17-20)) AND (Volunteers must be willing to complete all study-related activities) AND (Weighing at least 50 kg) AND (aged between 18 years and 45 years inclusive) AND (laboratory test) AND (medical history) AND (physical examination))"}
{"candidate_id": "LLM01122", "doc_id": "NCT02872090_exc", "case_bucket": "other", "source_criterion": "beta blocker supraventricular rhythm disorder previous history of respiratory disease other than COPD diabetes autonomic dysfunction dysautonomia renal failure long-term oxygen therapy history of psychiatric illness", "candidate_expression": "((autonomic dysfunction) AND (beta blocker) AND (diabetes) AND (dysautonomia) AND (long-term oxygen therapy) AND (psychiatric illness history) AND (renal failure) AND (respiratory disease previous history) AND (supraventricular rhythm disorder) AND NOT (COPD))"}
{"candidate_id": "LLM01123", "doc_id": "NCT02957877_exc", "case_bucket": "or", "source_criterion": "History of intolerance to LMWHs during HD Receiving warfarin or other oral anticoagulant Pregnant patients", "candidate_expression": "((HD) AND (LMWHs) AND (Pregnant) AND (during HD) AND (intolerance) AND (other) AND ((oral anticoagulant) OR (warfarin)))"}
{"candidate_id": "LLM01124", "doc_id": "NCT02632266_inc", "case_bucket": "or", "source_criterion": "Inborn preterm infants born between 28 0/7 and 34 0/7 weeks gestation and fed either mother's own milk or donor human milk", "candidate_expression": "((Inborn) AND (donor human milk fed) AND (fed mother's own milk) AND (gestation between 28 0/7 and 34 0/7 weeks) AND (infants) AND (preterm))"}
{"candidate_id": "LLM01125", "doc_id": "NCT02573597_exc", "case_bucket": "or", "source_criterion": "<37 weeks gestation, H/o Cesarean Section, Multiple Gestation, Pre-eclampsia, Narcotics within 3 hours prior to labor epidural placement, Chronic Pain (as defined by chronic opiate consumption), Women who are participating in another study that will impact protocol", "candidate_expression": "((<37 weeks) AND (Cesarean Section) AND (Chronic Pain) AND (H/o) AND (Multiple Gestation) AND (Narcotics) AND (Pre-eclampsia) AND (Women who are participating in another study that will impact protocol) AND (chronic) AND (gestation) AND (labor epidural placement) AND (opiate) AND (within 3 hours prior to labor epidural placement))"}
```
