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
{"candidate_id": "LLM06976", "doc_id": "NCT03164096_exc", "case_bucket": "or", "source_criterion": "Patients with coagulopathy or under anti-coagulation therapy. Gastrointestinal disease, motion sickness. diabetes mellitus. Patients with preeclampsia,", "candidate_expression": "((Gastrointestinal disease) AND (anti-coagulation therapy) AND (coagulopathy) AND (diabetes mellitus) AND (motion sickness) AND (preeclampsia))"}
{"candidate_id": "LLM06977", "doc_id": "NCT03043495_exc", "case_bucket": "or", "source_criterion": "Coagulopathies (with prothrombin concentration less than 60% or INR more than 1.5) In-ability to postpone anti-coagulation medications. Infection or injury or a lesion at the block site. Suspected cervical vertebral column injury necessitating using a neck collar. A compromised lung on the contralateral side of the block (Pneumothorax, hemothorax or Pneumonectomy). Traumatic vascular injuries or operative interventions (Surgical harvesting) involving arteries of the upper limb on the operative side. Patients with communication difficulties. Hypersensitivity to local anesthetics and/or Dexamethasone. Patients on perioperative intravenous (IV) steroids.", "candidate_expression": "((Coagulopathies) AND (Hypersensitivity) AND (In-ability to postpone) AND (Surgical harvesting) AND (Suspected) AND (anti-coagulation medications) AND (arteries of the upper limb on the operative side) AND (at the block site) AND (cervical vertebral column injury) AND (communication difficulties) AND (compromised lung) AND (contralateral side of the block) AND (intravenous (IV) steroids) AND (less than 60%) AND (more than 1.5) AND (perioperative) AND ((Pneumonectomy) OR (Pneumothorax) OR (hemothorax)) AND ((Traumatic vascular injuries) OR (operative interventions)) AND ((Dexamethasone) OR (local anesthetics)) AND ((INR) OR (prothrombin concentration)) AND ((Infection) OR (injury) OR (lesion)))"}
{"candidate_id": "LLM06978", "doc_id": "NCT03131050_inc", "case_bucket": "or", "source_criterion": "Has given written informed consent. Male or female outpatients aged at least 18 years and not more than 45 years. Has a diagnosis of major depressive disorder by Diagnostic and Statistical Manual of Mental Disorders, Fourth Edition (DSM-IV) criteria. Current HAMD-17 score = 20 and the duration of the index episode is greater than or equal to four weeks.", "candidate_expression": "((Current) AND (Diagnostic and Statistical Manual of Mental Disorders, Fourth Edition (DSM-IV) criteria) AND (HAMD-17) AND (Has given written informed consent.) AND (aged) AND (at least 18 years and not more than 45 years) AND (greater than or equal to four weeks) AND (index episode) AND (major depressive disorder) AND (outpatients) AND (score = 20) AND ((Male) OR (female)))"}
{"candidate_id": "LLM06979", "doc_id": "NCT01799681_inc", "case_bucket": "other", "source_criterion": "diagnosed with PD by a neurologist (Fahn and Elton, 1987); aged 30 to 85 years; at modified Hoehn and Yahr (H&Y) stage 1.5 to 3 (Hoehn and Yahr ,1967; Goetz et al., 2004); able and willing to give written consent for participation in the study; living at home in the community; able to walk independently for 30 metres with or without an assistive device.", "candidate_expression": "((30 to 85 years) AND (PD) AND (able and willing to give written consent for participation in the study;) AND (able to walk independently with or without an assistive device) AND (aged) AND (by a neurologist) AND (for 30 metres) AND (living at home in the community) AND (modified Hoehn and Yahr (H&Y)) AND (stage 1.5 to 3))"}
{"candidate_id": "LLM06980", "doc_id": "NCT02406495_inc", "case_bucket": "other", "source_criterion": "Is between 18 and 40 years of age (inclusive) Has had a self-reported visual exam in the last two years Is an adapted Avaira sphere contact lens wearer (at least 1 week in Avaira sphere) Has a contact lens spherical prescription between + 2.25 to - 8.00 (inclusive) Has a spectacle cylinder up to 0.75D in each eye. Can achieve best corrected spectacle distance visual acuity of 20/25 (0.10 logMAR) or better in each eye. Can achieve a distance visual acuity of 20/30 (0.18 logMAR) or better in each eye with the study contact lenses. Has clear corneas and no active ocular disease Has read, understood and signed the information consent letter. Patient contact lens refraction should fit within the available parameters of the study lenses. Is willing to comply with the wear schedule (at least 5 days per week, > 8 hours/day assuming there are no contraindications for doing so). Is willing to comply with the visit schedule", "candidate_expression": "((+ 2.25 to - 8.00 (inclusive)) AND (0.10 logMAR or better) AND (0.18 logMAR or better) AND (20/25 or better) AND (20/30 or better) AND (Avaira sphere) AND (Avaira sphere contact lens) AND (Has read, understood and signed the information consent letter.) AND (Is willing to comply with the visit schedule) AND (Is willing to comply with the wear schedule (at least 5 days per week, > 8 hours/day assuming there are no contraindications for doing so).) AND (active) AND (age) AND (at least 1 week in Avaira sphere) AND (best corrected spectacle distance visual acuity) AND (between 18 and 40 years (inclusive)) AND (clear corneas) AND (contact lens) AND (distance visual acuity) AND (in the last two years) AND (no) AND (ocular disease) AND (self-reported visual exam) AND (spectacle cylinder) AND (spherical) AND (study contact lenses) AND (up to 0.75D))"}
{"candidate_id": "LLM06981", "doc_id": "NCT03639519_exc", "case_bucket": "or", "source_criterion": "Allergy to ascorbic acid Asthma COPD Allergy to opioids Previous history of chemical dependence Prior cardiac surgery Known hyperoxaluria History of renal calculi History of allergic or hypersensitivity reaction to ascorbic acid products Currently taking 1 g or more of ascorbic acid supplementation daily", "candidate_expression": "((Allergy) AND (Asthma) AND (COPD) AND (ascorbic acid) AND (ascorbic acid 1 g or more) AND (cardiac surgery Prior) AND (chemical dependence Previous history) AND (hyperoxaluria) AND (opioids) AND (renal calculi History) AND ((allergic) OR (hypersensitivity)))"}
{"candidate_id": "LLM06982", "doc_id": "NCT03228498_exc", "case_bucket": "or", "source_criterion": "1. Absence of objectionable cognitive impairment or presence of dementia of severe degree defined by CDR score > 2.0. 2. Unavailability of brain MRI (in case of absolute contraindications, the use of cranial CT is allowed). 3. Expected poor compliance with the study protocol. 4. Past diagnosis of major depression, schizophrenia, major anxiety syndrome, or manic- depressive illness. 5. Diagnosis of degenerative cognitive impairment based on clinical and/or neuroradiological findings (i.e., patients with prevailing memory impairment, or with medial temporal atrophy on brain MRI in absence of evident vascular abnormalities; i.e., Alzheimer disease as defined using the National Institute of Neurological and Communicative Disorders and Stroke/Alzheimer's Disease and Related Disorders Association criteria, Parkinson disease, Huntington disease, frontotemporal dementia). 6. Diagnosis of cognitive impairment from other causes (i.e., vitamine B12 and folic acid deficiency, thyroid disorders, metabolic diseases, head trauma, tumor or infections of the central nervous system, normal pressure hydrocephalus). 7. Medical conditions expected to progress, recur, or change to such a degree to interfere with the assessment of the clinical and mental status. 8. Clinically relevant cardiac or pulmonary insufficiency. 9. Relevant electrocardiograph abnormalities; bradycardia (50 bpm) or tachycardia (120 bpm) under resting conditions. 10. Myocardial infarction within the past 6 months. 11. Stroke still requiring neurological rehabilitation. 12. Severe/untreated blood pressure (systolic 180 mm Hg, diastolic 95 mm Hg). 13. Clinically relevant liver function impairment. 14. Insulin-dependent diabetes mellitus. 15. Idiopathic epilepsy and anti-epileptic treatment. 16. Severe anemia (Hb <10 mg/dL). 17. Severe gastrointestinal disease. 18. Cancer. 19. Known intolerance to study drugs. 20. Coexistent serious illnesses that would imply a drop-out before the end of the trial.", "candidate_expression": "((120 bpm) AND (50 bpm) AND (Alzheimer disease) AND (CDR score > 2.0) AND (Cancer) AND (Clinically relevant) AND (Hb <10 mg/dL) AND (Huntington disease) AND (Idiopathic epilepsy) AND (Insulin-dependent diabetes mellitus) AND (Medical conditions expected to progress, recur, or change to such a degree to interfere with the assessment of the clinical and mental status.) AND (Myocardial infarction within the past 6 months) AND (National Institute of Neurological and Communicative Disorders and Stroke/Alzheimer's Disease and Related Disorders Association criteria) AND (Parkinson disease) AND (Past diagnosis) AND (Severe) AND (Stroke) AND (Unavailability) AND (abnormalities Relevant) AND (absolute contraindications) AND (anemia Severe) AND (anti-epileptic treatment) AND (blood pressure) AND (bradycardia) AND (brain MRI) AND (cardiac insufficiency) AND (clinical and/or neuroradiological findings) AND (cognitive impairment objectionable) AND (cognitive impairment other causes) AND (cranial CT) AND (degenerative cognitive impairment) AND (dementia severe degree) AND (diastolic 95 mm Hg) AND (electrocardiograph) AND (evident) AND (folic acid deficiency) AND (frontotemporal dementia) AND (gastrointestinal disease Severe) AND (head trauma) AND (infections of the central nervous system) AND (intolerance) AND (liver function impairment Clinically relevant) AND (major anxiety syndrome) AND (major depression) AND (manic- depressive illness) AND (medial temporal atrophy) AND (memory impairment) AND (metabolic diseases) AND (neurological rehabilitation requiring Severe untreated) AND (normal pressure hydrocephalus) AND (objectionable) AND (pulmonary insufficiency) AND (requiring) AND (schizophrenia) AND (study drugs) AND (systolic 180 mm Hg) AND (tachycardia) AND (thyroid disorders) AND (tumor of the central nervous system) AND (vitamine B12 deficiency) AND NOT (brain MRI) AND NOT (vascular abnormalities))"}
{"candidate_id": "LLM06983", "doc_id": "NCT02464865_exc", "case_bucket": "or", "source_criterion": "pathological obesity chronic diseases e.g. cerebral palsy, metabolic disease, etc. diseases of red blood cells on medication e.g. steroid, multivitamins, thiamine-containing vitamins, diuretic drugs hemodialysis or peritoneal dialysis bariatric surgery", "candidate_expression": "((bariatric surgery) AND (cerebral palsy) AND (chronic diseases) AND (diseases of red blood cells) AND (diuretic drugs) AND (hemodialysis) AND (metabolic disease) AND (multivitamins) AND (pathological obesity) AND (peritoneal dialysis) AND (steroid) AND (thiamine-containing vitamins))"}
{"candidate_id": "LLM06984", "doc_id": "NCT00586898_exc", "case_bucket": "or", "source_criterion": "Clinically significant cardiac disease (New York Heart Association Class III/IV),or severe debilitating puhnonary disease. Uncontrolled serious active infection. Anticipated survival of less than 3 months. Active CNS or epiduraltumor Inability or unwillingness to comply with the treatment protocol, follow-up, or research tests.", "candidate_expression": "((Anticipated survival) AND (CNS tumor) AND (Class III/IV) AND (Inability) AND (New York Heart Association) AND (Uncontrolled serious) AND (cardiac disease) AND (comply with the treatment protocol) AND (debilitating puhnonary disease) AND (epiduraltumor) AND (follow-up) AND (infection) AND (less than 3 months) AND (research tests) AND (severe) AND (significant) AND (unwillingness))"}
{"candidate_id": "LLM06985", "doc_id": "NCT02701881_exc", "case_bucket": "or", "source_criterion": "Acute critical limb ischemia Severe critical limb ischemia (Rutherford category 6) Major bleeding history within prior 2 months Known hypersensitivity or contraindication to any of the following medications: heparin, aspirin, clopidogrel or contrast agents Age > 85 years Severe hepatic dysfunction (> 3 times normal reference values) Significant renal dysfunction (Serum creatinine > 2.0 mg/dl Significant leucopenia, neutropenia, thrombocytopenia, anemia, or known bleeding diathesis LVEF <40% or clinically overt congestive heart failure Pregnant women or women with potential childbearing Life expectancy <1 year due to comorbidity Previous bypass surgery or stenting of the superficial femoral artery Untreated inflow disease of the ipsilateral pelvic arteries (more than 50%stenosis or or occlusion Popliteal artery stenosis >50% at P2 or P3 segment", "candidate_expression": "((6) AND (<1 year) AND (<40%) AND (> 2.0 mg/dl) AND (> 85 years) AND (>50%) AND (Acute) AND (Age) AND (Life expectancy) AND (Major bleeding history) AND (P2 or P3 segment) AND (Popliteal artery stenosis) AND (Previous) AND (Rutherford category) AND (Serum creatinine) AND (Severe) AND (Significant) AND (Untreated) AND (clinically overt) AND (comorbidity) AND (critical) AND (hepatic dysfunction) AND (inflow disease) AND (ipsilateral pelvic arteries) AND (limb ischemia) AND (renal dysfunction) AND (stenosis) AND (within prior 2 months) AND ((contraindication) OR (hypersensitivity)) AND ((aspirin) OR (clopidogrel) OR (contrast agents) OR (heparin)) AND ((anemia) OR (bleeding diathesis) OR (leucopenia) OR (neutropenia) OR (thrombocytopenia)) AND ((LVEF) OR (congestive heart failure)) AND ((Pregnant) OR (potential childbearing)) AND ((women)) AND ((bypass surgery) OR (stenting of the superficial femoral artery)) AND ((more than 50%) OR (occlusion)))"}
{"candidate_id": "LLM06986", "doc_id": "NCT02106624_inc", "case_bucket": "or", "source_criterion": "need mechanical ventilation for more than 2 days mean blood pressure more than 60mmHg predicted ICU stay more than 7 days tolerance of parenteral or enteral nutrition", "candidate_expression": "((ICU) AND (enteral nutrition) AND (for more than 2 days) AND (mean blood pressure) AND (mechanical ventilation) AND (more than 60mmHg) AND (more than 7 days) AND (need) AND (parenteral nutrition) AND (predicted ICU stay) AND (tolerance))"}
{"candidate_id": "LLM06987", "doc_id": "NCT01709981_inc", "case_bucket": "other", "source_criterion": "Patients must be more than 18 years of age and referred for coronary angiography", "candidate_expression": "((age more than 18 years) AND (coronary angiography referred for))"}
{"candidate_id": "LLM06988", "doc_id": "NCT03059069_exc", "case_bucket": "or", "source_criterion": "Type 1 diabetes, Secondary diabetes, gestational diabetes Ongoing dementia treatment or anti-depressive disorder medication Uncontrolled psychiatric disorder BDI = 30 points Heavy alcoholics Underlying chronic liver disease (hemochromatosis, liver cell carcinoma, autoimmune liver disease, liver cirrhosis, chronic viral hepatitis) Allergy or hypersensitivity to target medication or any of its components Renal failure, moderate or severe renal impairment (estimated glomerular filtration rate < 30 mL/min/1.73 m2), or ongoing dialysis Abnormal liver function (AST/ALT > x3 upper normal limit) History of alcohol or drug abuse in the previous 3 months Premenopausal women who are nursing or pregnant Human immunodeficiency virus (HIV) or human immunodeficiency virus (AIDS) chronic pancreatitis or pancreatic cancer", "candidate_expression": "((AST/ALT > x3 upper normal limit) AND (BDI = 30 points Uncontrolled) AND (Premenopausal) AND (alcoholics Heavy) AND (chronic liver disease) AND (dementia) AND (estimated glomerular filtration rate < 30 mL/min/1.73 m2) AND (liver function Abnormal) AND (renal impairment) AND (target medication) AND (women) AND ((autoimmune liver disease) OR (chronic viral hepatitis) OR (hemochromatosis) OR (liver cell carcinoma) OR (liver cirrhosis)) AND ((Secondary diabetes) OR (Type 1 diabetes) OR (gestational diabetes)) AND ((Allergy) OR (hypersensitivity)) AND ((Renal failure) OR (dialysis ongoing)) AND ((moderate) OR (severe)) AND ((alcohol abuse) OR (drug abuse)) AND ((nursing) OR (pregnant)) AND ((Human immunodeficiency virus (HIV)) OR (human immunodeficiency virus (AIDS))) AND ((chronic pancreatitis) OR (pancreatic cancer)) AND ((anti-depressive disorder medication) OR (treatment Ongoing)))"}
{"candidate_id": "LLM06989", "doc_id": "NCT02368743_inc", "case_bucket": "or", "source_criterion": "Patient aged 18 years or older. Patient suffering from mild to moderate active proctitis or distal proctosigmoiditis (MAYO score ≥ 3 and ≤ 10) at inclusion based on clinical and endoscopic findings within 6 months before study inclusion. Patient with evidence of endoscopic active proctitis or distal proctosigmoiditis (Montreal classification E1 or E2 defined by an involvement not exceeding 25 cm from the anal margin) within 6 months before study inclusion. Treatment of the current flare with Pentasa® to induce a remission initiated by the patient, the general practitioner or the gastroenterologist, during the inclusion visit or during the week before the inclusion visit. Patient having received oral and written information on the study, without any objections for the use of his/her personal data, and having signed a written Informed Consent Form.", "candidate_expression": "((MAYO score ≥ 3 and ≤ 10) AND (Montreal classification E1 or E2 involvement not exceeding 25 cm from the anal margin) AND (Pentasa) AND (Treatment within 6 months before study inclusion) AND (active proctitis) AND (aged 18 years or older) AND (distal proctosigmoiditis) AND (during the inclusion visit inclusion visit) AND (during the week before the inclusion visit the week before the inclusion visit) AND (endoscopic) AND (flare))"}
{"candidate_id": "LLM06990", "doc_id": "NCT03117608_exc", "case_bucket": "or", "source_criterion": "Patients incapable to understanding and will; Patients participating in previous, concurrent or not, trials (ongoing or completed within three months); Patients surgically treated for the same defect within one year; Patients affected by malignancy; Patients affected by metabolic or thyroid disorders; Patients used to alcohol or drug (medication) abuse; Patients affected by synovitis; Varus or valgus misalignment exceeding 15°; Body Mass Index > 40; Patients with trauma within 6 months pre-operative.", "candidate_expression": "((> 40) AND (Body Mass Index) AND (drug abuse) AND (exceeding 15°) AND (malignancy) AND (operative) AND (pre-operative) AND (previous) AND (surgically treated) AND (synovitis) AND (the same defect) AND (trauma) AND (trials participating in) AND (within 6 months pre-operative) AND (within one year) AND (within three months) AND ((incapable to understanding) OR (will incapable to)) AND ((metabolic disorders) OR (thyroid disorders)) AND ((alcohol abuse) OR (medication abuse)) AND ((Varus misalignment) OR (valgus misalignment)) AND ((completed) OR (ongoing)))"}
{"candidate_id": "LLM06991", "doc_id": "NCT03338855_exc", "case_bucket": "or", "source_criterion": "Involvement in the planning and conduct of the study (applies to both AstraZeneca staff and staff at third party vendor or at the investigational sites). Previous enrolment in the present study or participation in another clinical study with an investigational product during the last 3 months or as judged by the Investigator. History of or presence of any clinically significant disease or disorder including a recent (< 3 months) cardiovascular event which, in the opinion of the Investigator, may either put the patient at risk because of participation in the study or influence the results or the patient's ability to participate in the study. Clinical diagnosis of Type 1 diabetes, maturity onset diabetes of the young, secondary diabetes or diabetes insipidus. Unstable/rapidly progressing renal disease or estimated Glomerular Filtration Rate < 60 mL/min (Cockcroft-Gault formula). Clinically significant out of range values of serum levels of either alanine aminotransferase (ALT), aspartate aminotransferase (AST) or alkaline phosphatase (ALP) in the Investigator's opinion. Contraindications to dapagliflozin according to the local label. Use of antidiabetic drugs other than metformin within 3 months prior to screening. Weight gain or loss > 5 kg in the last 3 months, ongoing weight-loss diet (hypocaloric diet) or use of weight loss agents. History of drug abuse or alcohol abuse in the past 12 months. Any clinically significant abnormalities in clinical chemistry, hematology or urinalysis or other condition the Investigator believes would interfere with the patient's ability to provide informed consent, comply with study instructions, or which might confound the interpretation of the study results or put the patient at undue risk. Plasma donation within one month of screening or any blood donation/blood loss > 500 mL within 3 months prior to screening or during the study. Anemia defined as Hemoglobin (Hb) < 115 g/L (7.1 mM) in women and < 120 g/L (7.5 mM) in men. Use of anti-coagulant treatment such as heparin, warfarin, platelet inhibitors, thrombin and factor X inhibitors. Use of medication such as oral glucocorticoids, anti-estrogens or other medications that are known to markedly influence insulin sensitivity. Use of loop diuretics. Regular smoking and other regular nicotine use. Central nervous system aneurysm clip Implanted neural stimulator Implanted cardiac pacemaker of defibrillator Cochlear implant Metal containing corpora aliena in the eye or brain. Patients, who do not want to be informed about unexpected medical findings, or do not wish that their physician be informed about coincidental findings, cannot participate in the study.", "candidate_expression": "((Anemia during the study) AND (Any clinically significant abnormalities in clinical chemistry, hematology or urinalysis or other condition the Investigator believes would interfere with the patient's ability to provide informed consent, comply with study instructions, or which might confound the interpretation of the study results or put the patient at undue risk.) AND (Central nervous system aneurysm clip) AND (Cochlear implant) AND (Contraindications) AND (Hemoglobin (Hb) 7.1 mM) AND (History of or presence of any clinically significant disease or disorder including a recent (< 3 months) cardiovascular event which, in the opinion of the Investigator, may either put the patient at risk because of participation in the study or influence the results or the patient's ability to participate in the study) AND (Implanted neural stimulator) AND (Plasma donation within one month of screening) AND (Previous enrolment in the present study or participation in another clinical study with an investigational product during the last 3 months or as judged by the Investigator.) AND (Type 1 diabetes) AND (Weight gain) AND (Weight loss) AND (alanine aminotransferase (ALT)) AND (alcohol abuse) AND (alkaline phosphatase (ALP)) AND (anti-coagulant treatment) AND (anti-estrogens) AND (antidiabetic drugs within 3 months prior to screening) AND (aspartate aminotransferase (AST)) AND (blood donation) AND (blood loss > 500 mL within 3 months prior to screening) AND (cardiac pacemaker) AND (cardiovascular event) AND (corpora aliena in the brain Metal containing) AND (corpora aliena in the eye Metal containing) AND (dapagliflozin) AND (defibrillator) AND (diabetes insipidus Unstable rapidly progressing) AND (disease clinically significant) AND (disorder recent < 3 months) AND (drug abuse) AND (estimated Glomerular Filtration Rate < 60 mL/min Cockcroft-Gault formula) AND (factor X inhibitors) AND (heparin) AND (hypocaloric diet) AND (loop diuretics) AND (maturity onset diabetes of the young) AND (medications other) AND (men < 120 g/L 7.5 mM) AND (nicotine regular) AND (oral glucocorticoids) AND (platelet inhibitors) AND (renal disease) AND (secondary diabetes) AND (smoking Regular) AND (thrombin) AND (warfarin) AND (weight loss agents) AND (weight-loss diet ongoing) AND (women < 115 g/L) AND NOT (metformin))"}
{"candidate_id": "LLM06992", "doc_id": "NCT03473132_inc", "case_bucket": "other", "source_criterion": "LVAD on warfarin requiring temporary interruption of anticoagulation for procedures", "candidate_expression": "((LVAD) AND (requiring temporary interruption of anticoagulation for procedures) AND (warfarin))"}
{"candidate_id": "LLM06993", "doc_id": "NCT01891513_inc", "case_bucket": "or", "source_criterion": "Age 65 years and older Hypertension - untreated (Systolic Blood Pressure (SBP) ≥ 140 mm Hg or Diastolic Blood Pressure (DBP) ≥ 90 mm Hg) or treated Physical limitations evidenced by either: Score ≤ 10 on the Short Physical Performance Battery OR Walking speed < 1.2 m/sec during 400 m usual-paced test Sedentary lifestyle, defined as <150 min/wk of moderate physical activity as assessed by CHAMPS questionnaire Willingness to participate in all study procedures", "candidate_expression": "((400 m usual-paced test) AND (Age 65 years and older) AND (CHAMPS questionnaire) AND (Diastolic Blood Pressure (DBP) ≥ 90 mm Hg treated) AND (Hypertension untreated) AND (Sedentary lifestyle) AND (Short Physical Performance Battery Score ≤ 10) AND (Systolic Blood Pressure (SBP) ≥ 140 mm Hg) AND (Walking speed < 1.2 m/sec) AND (moderate physical activity <150 min/wk))"}
{"candidate_id": "LLM06994", "doc_id": "NCT01567605_exc", "case_bucket": "or", "source_criterion": "cauda equina or conus lesion currently use ventilator colostomy, or do not perform regular bowel care for any reason any skin breakdown (pressure sores) do not speak English are under 19 years old are pregnant or think you might be pregnant medical/psychiatric condition or substance abuse that is likely to affect your ability to complete this study currently using medications containing lidocaine allergy to lidocaine", "candidate_expression": "((allergy) AND (lesion) AND (lidocaine) AND (medications containing lidocaine currently) AND (old under 19 years) AND (pressure sores) AND (skin breakdown) AND (ventilator currently) AND NOT (speak English) AND ((cauda equina) OR (conus)) AND ((pregnant) OR (pregnant think you might be)) AND ((medical condition) OR (psychiatric condition) OR (substance abuse)) AND ((colostomy) OR NOT (regular bowel care)))"}
{"candidate_id": "LLM06995", "doc_id": "NCT00480129_inc", "case_bucket": "or", "source_criterion": "Clinical diagnosis of allergic rhinitis based on sneeze attacks, runny/blocked/itchy nose in the absence of a common cold during the previous 12 months. History of positive skin prick test or blood radio-allergosorbent test (RAST) to grass and/or ragweed pollen", "candidate_expression": "((absence) AND (allergic rhinitis) AND (blocked nose) AND (blood radio-allergosorbent test (RAST)) AND (common cold) AND (during the previous 12 months) AND (grass) AND (itchy nose) AND (positive) AND (ragweed pollen) AND (runny nose) AND (skin prick test) AND (sneeze attacks))"}
{"candidate_id": "LLM06996", "doc_id": "NCT02734173_exc", "case_bucket": "or", "source_criterion": "<18 years old Evidence of decompensated liver disease HOMA IR< 2.0 HIV seropositivity Chronic HBV/HIV infection Use of immune suppressing medications Active malignancy", "candidate_expression": "((HIV infection Chronic) AND (HIV seropositivity) AND (HOMA IR < 2.0) AND (immune suppressing medications) AND (infection Chronic HBV) AND (liver disease decompensated) AND (malignancy Active) AND (old <18 years))"}
{"candidate_id": "LLM06997", "doc_id": "NCT02315287_inc", "case_bucket": "or", "source_criterion": "HbA1c > 13.0 % No treatment with insulin or oral agents for 6 months 20 = Age < 80 years", "candidate_expression": "((Age 20 = < 80 years) AND (HbA1c > 13.0 %) AND NOT (treatment) AND ((insulin) OR (oral agents)))"}
{"candidate_id": "LLM06998", "doc_id": "NCT00959569_exc", "case_bucket": "other", "source_criterion": "previous unusual response to esmolol inclusion in other randomized studies esmolol administration in the previous 30 days emergency operation", "candidate_expression": "((esmolol) AND (esmolol in the previous 30 days) AND (inclusion in other randomized studies) AND (operation emergency) AND (unusual response))"}
{"candidate_id": "LLM06999", "doc_id": "NCT02905890_inc", "case_bucket": "other", "source_criterion": "BV positive by Nugent score HIV negative Capable of providing written informed consent", "candidate_expression": "((BV) AND (Capable of providing written informed consent) AND (HIV) AND (Nugent score) AND (negative) AND (positive))"}
{"candidate_id": "LLM07000", "doc_id": "NCT00356148_exc", "case_bucket": "or", "source_criterion": "Ductal carcinoma in situ (DCIS; stage 0 cancer), Advanced or distant metastatic stage, Receiving any neoadjuvant therapy, History of receiving any antibiotics within prior 3 months, History of immunodeficiency, Having a remote infection, History of reaction to study antibiotics, Denial of signing the consent form.", "candidate_expression": "((Ductal carcinoma in situ) AND (History) AND (antibiotics within prior 3 months) AND (immunodeficiency) AND (neoadjuvant therapy) AND (reaction) AND (remote infection) AND (stage) AND (stage 0) AND (study antibiotics) AND NOT (signing the consent form) AND ((DCIS) OR (cancer)) AND ((Advanced metastatic) OR (distant metastatic)))"}
```
