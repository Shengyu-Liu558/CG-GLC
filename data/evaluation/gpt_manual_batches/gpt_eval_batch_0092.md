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
{"candidate_id": "LLM02276", "doc_id": "NCT02715466_exc", "case_bucket": "or", "source_criterion": "Administration of HES, dextrane solutions or > 500 ml of Gelatin solutions within the 24 h prior to randomization Death expected within the next 48 h (moribund patients as defined by ASA = class V) Patients whose medical condition does preclude the PLR manoeuvre Patients for whom the need of pressure infusions are expected Requirement for renal support (either continuous or discontinuous techniques, including intermittent haemodialysis, haemofiltration and haemodiafiltration) Patients receiving therapeutic heparin medication due to chronic coagulation disease / anticoagulation medication (i.e. partial thromboplastin time > 60 sec) Acutely burned patients Contraindications according to summary of product characteristics of investigational test and reference product Simultaneous participation in another interventional clinical trial (drugs or medical devices studies)", "candidate_expression": "((= class V) AND (> 500 ml) AND (> 60 sec) AND (ASA) AND (Acutely burned) AND (Death expected) AND (Gelatin solutions) AND (HES) AND (Requirement for) AND (anticoagulation medication) AND (chronic coagulation disease) AND (dextrane solutions) AND (heparin) AND (moribund) AND (partial thromboplastin time) AND (renal support) AND (within the 24 h prior to randomization) AND (within the next 48 h))"}
{"candidate_id": "LLM02277", "doc_id": "NCT02624908_inc", "case_bucket": "other", "source_criterion": "use of basal-bolus insulin onset of diabetes after age 30 BMI less than 35 eGFR at least 60 ml/mn Hb A1c 7.0-10.0% willingness to perform home glucose monitoring willingness to transmit glucose and medication information weekly", "candidate_expression": "((BMI less than 35) AND (Hb A1c 7.0-10.0%) AND (basal-bolus insulin) AND (eGFR at least 60 ml/mn) AND (onset of diabetes after age 30))"}
{"candidate_id": "LLM02278", "doc_id": "NCT02432404_exc", "case_bucket": "or", "source_criterion": "Current pregnancy Desire/intent to become pregnant over the course of the study Women who are less than 6 weeks postpartum Contraindications to hormonal contraceptive use per package insert, including history of deep vein thrombosis, smoking in women older than 35 years Current IUD Unable to comprehend consent material because of language barrier or psychological difficulty", "candidate_expression": "((Contraindications to hormonal contraceptive) AND (Desire/intent to become pregnant) AND (IUD) AND (Unable to comprehend consent material because of language barrier or psychological difficulty) AND (Women) AND (hormonal contraceptive) AND (less than 6 weeks postpartum) AND (older than 35 years) AND (over the course of the study) AND (postpartum) AND (pregnancy) AND (pregnant) AND (smoking) AND ((deep vein thrombosis) OR (women)))"}
{"candidate_id": "LLM02279", "doc_id": "NCT03333655_exc", "case_bucket": "or", "source_criterion": "Participants taking CPI combination therapies with chemotherapy are not permitted. Pregnant, lactating, or intending to become pregnant during the study.", "candidate_expression": "((CPI combination therapies) AND (Pregnant) AND (chemotherapy) AND (lactating) AND (pregnant intending to become during the study))"}
{"candidate_id": "LLM02280", "doc_id": "NCT02950558_inc", "case_bucket": "other", "source_criterion": "Referred for surgery for open reduction and internal fixation for ankle fracture", "candidate_expression": "((ankle fracture) AND (open reduction and internal fixation) AND (surgery))"}
{"candidate_id": "LLM02281", "doc_id": "NCT02284737_exc", "case_bucket": "or", "source_criterion": "Pregnancy and breast feeding mother; Estimated life expectancy <12 months; Scheduled major surgery in the next 6 months; Inability to follow the protocol and comply with follow-up requirements or any other reason that the investigator feels would place the patient at increased risk; Previous enrolment in this study or treatment with an investigational drug or device under another study protocol in the past 30 days. WHO group II, III, IV, V PH Severe Renal dysfunction (Ccr<30 ml/min) Blood platelet count<100,000/L Expected life span<6-month Systematical inflammation Malignant cancer(s) Tricuspid valve stenosis, Supra-pulmonary valve stenosis Allergic to studied drugs or metal materials.", "candidate_expression": "((<100,000/L) AND (<12 months) AND (<30 ml/min) AND (<6-month) AND (Allergic) AND (Blood platelet count) AND (Ccr) AND (Estimated life expectancy) AND (Expected life span) AND (Malignant cancer) AND (PH) AND (Previous) AND (Renal dysfunction) AND (Scheduled) AND (Severe) AND (Systematical inflammation) AND (WHO) AND (group II, III, IV, V) AND (in the next 6 months) AND (investigational drug) AND (major surgery) AND ((Pregnancy) OR (breast feeding)) AND ((Supra-pulmonary valve stenosis) OR (Tricuspid valve stenosis)) AND ((studied drugs) OR (studied metal materials)) AND ((device) OR (enrolment in this study) OR (treatment with an investigational drug)) AND ((Inability to comply with follow-up requirements) OR (Inability to follow the protocol)))"}
{"candidate_id": "LLM02282", "doc_id": "NCT02429765_exc", "case_bucket": "other", "source_criterion": "A diagnosis of sleep disordered breathing; Nocturnal oxygen therapy.", "candidate_expression": "((Nocturnal oxygen therapy) AND (sleep disordered breathing))"}
{"candidate_id": "LLM02283", "doc_id": "NCT02371200_inc", "case_bucket": "or", "source_criterion": "1. Subject has a history of GTC seizures, either primary GTC or partial onset seizures with secondary generalization. 2. Is being admitted to a hospital for routine vEEG monitoring related to seizures. 3. Male or female between the ages of 2-99. 4. Has an upper arm circumference which is adequate for proper fit of the EMG monitor (at least 14cm). 5. If female and of childbearing potential, has a negative pregnancy test. 6. Can understand and sign written informed consent, or will have a parent or a legally authorized representative (LAR) who can do so, prior to the performance of any study assessments. 7. Subject and/or Primary Caregiver must be competent to follow all study procedures. 8. Is able to read, speak, and understand English.", "candidate_expression": "((Can understand and sign written informed consent, or will have a parent or a legally authorized representative (LAR) who can do so, prior to the performance of any study assessments.) AND (GTC seizures history) AND (Male) AND (Subject and/or Primary Caregiver must be competent to follow all study procedures.) AND (admitted to a hospital) AND (childbearing potential) AND (female) AND (female at least 14cm) AND (partial onset seizures) AND (pregnancy test negative) AND (primary GTC) AND (secondary generalization) AND (seizures) AND (the ages between 2-99) AND (upper arm circumference adequate for proper fit of the EMG monitor) AND (vEEG monitoring))"}
{"candidate_id": "LLM02284", "doc_id": "NCT00609531_exc", "case_bucket": "or", "source_criterion": "Age less than 10 years or greater than 55 years, at time of consent Estimated IQ < 70 Uncontrolled epilepsy (seizure within 6 months prior to consent) 4. Presence of medical conditions that might interfere with participation, or where participation would be contraindicated History of neurological injury: head trauma, poorly-controlled seizure disorder (seizure within the preceding six months), stroke, prior neurosurgery, or under the care of a neurologist or neurosurgeon as determined by interview History of claustrophobia Implanted or irremovable metal in the body (including certain tattoos and permanent make-up) Current pregnancy (as verified by testing prior to both initial dose administration of citalopram or placebo and prior to magnetic resonance imaging) due to the risk that may be associated with SSRI treatment and magnetic resonance imaging on fetal health Medical contraindications to SSRI therapy as determined by history (including induction of mania or hypomania during SSRI therapy, or known drug allergy) Concomitant medication that would interfere with study participation Prior history of citalopram treatment failure at appropriate doses and duration Prior history of treatment failure to two previous SSRI trials at appropriate doses and duration Ongoing need for psychoactive medication other than study medication [excepting stable doses (greater than three months duration) of anticonvulsant medication for seizure disorder, or diphenhydramine (Benadryl®)for sleep]", "candidate_expression": "((Age at time of consent) AND (Estimated IQ < 70) AND (SSRI therapy) AND (Uncontrolled epilepsy) AND (citalopram) AND (claustrophobia History) AND (consent) AND (contraindications to SSRI therapy history) AND (drug allergy) AND (history) AND (neurological injury History) AND (pregnancy Current) AND (psychoactive medication) AND (seizure disorder) AND (seizure within 6 months prior to consent) AND (seizure within the preceding six months) AND (stable doses greater than three months) AND (treatment Prior failure) AND NOT (study medication) AND ((head trauma) OR (neurosurgery prior) OR (seizure disorder poorly-controlled) OR (stroke) OR (under the care of a neurologist) OR (under the care of a neurosurgeon)) AND ((Implanted metal in the body) OR (irremovable metal in the body)) AND ((greater than 55 years) OR (less than 10 years)) AND ((hypomania) OR (mania)) AND ((diphenhydramine) OR NOT (anticonvulsant medication)))"}
{"candidate_id": "LLM02285", "doc_id": "NCT02175186_exc", "case_bucket": "or", "source_criterion": "Pregnant or breast feeding History of Stomach or esophagus surgery Peptic ulcer or reflux esophagitis Zollinger-Ellison syndrome or primary esophageal motility disorders Malignant tumor Bleeding tendency or coagulopathy Contraindication of ALBIS Long term use of aspirin or P2Y12 receptor antagonist within 1month Patients who tool medicine such as PPI, APA,H2blocker, Muscarine receptor antagonist, anti-gastic agent, antacid, anticaogulant, Bisphosphonate agents, Cytotoxic drug, NSAID, adrenal cortex hormone agents (topical treatment is allowed) Terminal patient", "candidate_expression": "((ALBIS) AND (Contraindication) AND (Long term) AND (Malignant tumor) AND (Pregnant or breast feeding) AND (Terminal) AND (allowed) AND (patient) AND (topical treatment) AND (within 1month) AND ((P2Y12 receptor antagonist) OR (aspirin)) AND ((APA) OR (Bisphosphonate agents) OR (Cytotoxic drug) OR (H2blocker) OR (Muscarine receptor antagonist) OR (NSAID) OR (PPI) OR (adrenal cortex hormone agents) OR (antacid) OR (anti-gastic agent) OR (anticaogulant)) AND ((Stomach surgery) OR (esophagus surgery)) AND ((Peptic ulcer) OR (reflux esophagitis)) AND ((Zollinger-Ellison syndrome) OR (primary esophageal motility disorders)) AND ((Bleeding tendency) OR (coagulopathy)))"}
{"candidate_id": "LLM02286", "doc_id": "NCT02678377_exc", "case_bucket": "other", "source_criterion": "History of recurrent UTI (defined as three culture proven UTIs within last 12 months) Systemic neuromuscular disease known to affect the lower urinary tract Undergoing concomitant prolapse surgery Previous incontinence surgery Treatment with anticholinergic medication in the last 2 months Previous bladder injection with onabotulinumtoxinA Prisoner Status Pregnancy", "candidate_expression": "((Pregnancy) AND (Prisoner) AND (anticholinergic medication) AND (bladder injection) AND (culture) AND (incontinence surgery) AND (last 2 month) AND (neuromuscular disease) AND (onabotulinumtoxinA) AND (prolapse surgery) AND (recurrent UTI) AND (three) AND (within last 12 months))"}
{"candidate_id": "LLM02287", "doc_id": "NCT03079141_inc", "case_bucket": "other", "source_criterion": "Age of = 18 years of age and able to give written informed consent; Active chronic central serous chorioretinopathy (cCSC); Subjective visual loss > 6 weeks, interpreted as onset of active disease; Foveal subretinal fluid (SRF), on optical coherence tomography (OCT), at Baseline Examination; =1 ill-defined hyperfluorescent leakage areas on fluorescein angiography (FA) with retinal pigment epithelial window defect(s) that are compatible with cCSC; Hyperfluorescent areas on indocyanine green angiography (ICGA).", "candidate_expression": "((= 18 years) AND (=1) AND (> 6 weeks) AND (Active) AND (Age) AND (Baseline Examination) AND (Foveal subretinal fluid (SRF)) AND (Hyperfluorescent areas) AND (Subjective visual loss) AND (able to give written informed consent) AND (at Baseline Examination) AND (central serous chorioretinopathy (cCSC)) AND (chronic) AND (fluorescein angiography (FA)) AND (hyperfluorescent leakage areas) AND (ill-defined) AND (indocyanine green angiography (ICGA)) AND (optical coherence tomography (OCT)) AND (retinal pigment epithelial window defect(s)))"}
{"candidate_id": "LLM02288", "doc_id": "NCT01664507_inc", "case_bucket": "other", "source_criterion": "croup children between 6 month and 5 years old Westley croup score between 3 and 11", "candidate_expression": "((Westley croup score) AND (between 3 and 11) AND (between 6 month and 5 years) AND (children) AND (old))"}
{"candidate_id": "LLM02289", "doc_id": "NCT02068365_exc", "case_bucket": "or", "source_criterion": "Evidence of decompensated liver disease (Childs B-C), hepato-cellular carcinoma, pre-existing severe depression or other psychiatric disease, significant cardiac disease, significant renal disease, seizure disorders or severe retinopathy. received telbivudine as the antiviral therapy or have received more than one NA in the past. received interferon or peginterferon treatment in the past. received antiviral therapy for any systemic anti-viral, anti-neoplastic or immuno-modulatory treatment (including supraphysiologic doses of steroids and radiation) within the past 6 months. Positive test at screening for anti-HIV, anti-HCV. Patients who are expected to need systemic antiviral therapy other than that provided by the study at any time during their participation in the study are also excluded. Exception: patients who have had a limited (<=7 days) course of acyclovir for herpetic lesions more than 1 month prior to the first administration of test drug are not excluded. Serum total bilirubin > 3 times the upper limit of normal at screening. History or other evidence of bleeding from esophageal varices or other conditions consistent with decompensated liver disease. History or other evidence of a medical condition associated with chronic liver disease other than HBV (e.g., hemochromatosis, autoimmune hepatitis, metabolic liver diseases including Wilson's and alpha1-antitrypsin deficiency, alcoholic liver disease, toxin exposures, thalassemia). Women with ongoing pregnancy or who are breast feeding. Neutrophil count <1500 cells/mm3 or platelet count <90,000 cells/mm3 at screening. Hemoglobin < 11.5 g/dL for females and < 12.5 g/dL for men at screening. Serum creatinine level >120 umol/ml for men and >105 umol/ml for women at screening. History of severe psychiatric disease, especially depression. Severe psychiatric disease is defined as major depression or psychosis, a period of treatment with an antidepressant medication or major tranquilizer at therapeutic doses for depression or psychosis for at least 3 months, a suicidal attempt, hospitalization for psychiatric disease, or a period of disability due to a psychiatric disease. History of immunologically mediated disease (e.g., inflammatory bowel disease, idiopathic thrombocytopenic purpura, lupus erythematosus, autoimmune hemolytic anemia, scleroderma, severe psoriasis, rheumatoid arthritis). History or other evidence of chronic pulmonary disease associated with functional limitation. Severe cardiac disease (e.g., NYHA Functional Class III or IV, myocardial infarction within 6 months, ventricular tachyarrhythmias requiring ongoing treatment, unstable angina or other significant cardiovascular diseases). History of a severe seizure disorder or current anticonvulsant use. Evidence of an active or suspected cancer or a history of malignancy where the risk of recurrence is >=20% within 2 years. Patients with a lesion suspicious of hepatic malignancy on a screening imaging study will only be eligible if the likelihood of carcinoma is <=10% following an appropriate evaluation. History of having received any systemic anti-neoplastic (including radiation) or immunomodulatory treatment (including systemic corticosteroids) <=6 months prior to the first dose of study drug or the expectation that such treatment will be needed at any time during the study. Major organ transplantation. Thyroid disease with thyroid function poorly controlled on prescribed medications. Patients with abnormal thyroid stimulating hormone or T4 concentrations, with elevation of antibodies to thyroid peroxidase and any clinical manifestations of thyroid disease are excluded. History or other evidence of severe retinopathy (e.g. CMV retinitis, macula degeneration) or clinically relevant ophthalmological disorder due to diabetes mellitus or hypertension Inability or unwillingness to provide informed consent or abide by the requirements of the study. History or other evidence of severe illness or any other conditions which would make the patient, in the opinion of the investigator, unsuitable for the study. Patients with a value of alpha-fetoprotein >100 ng/mL are excluded, unless stability (less than 10% increase) has been documented over at least the previous 3 months. Evidence of drug and/or alcohol abuse (20g/day for women & 30g/day for men). Patients included in another trial or having been given investigational drugs within 12 weeks prior to screening Any known history of hypersensitivity to interferon.", "candidate_expression": "((20g/day) AND (30g/day) AND (< 11.5 g/dL) AND (< 12.5 g/dL) AND (<1500 cells/mm3) AND (<90,000 cells/mm3) AND (<=10%) AND (<=6 months prior to the first dose of study drug) AND (<=7 days) AND (> 3 times the upper limit of normal) AND (>100 ng/mL) AND (>105 umol/ml) AND (>120 umol/ml) AND (>=20% within 2 years) AND (B-C) AND (CMV retinitis) AND (Childs) AND (Exception) AND (Functional Class III or IV) AND (HBV) AND (Hemoglobin) AND (History or other evidence of severe illness or any other conditions which would make the patient, in the opinion of the investigator, unsuitable for the study.) AND (Inability or unwillingness to provide informed consent or abide by the requirements of the study.) AND (Major organ transplantation) AND (NA) AND (NYHA) AND (Neutrophil count) AND (Patients included in another trial or having been given investigational drugs within 12 weeks prior to screening) AND (Positive) AND (Serum creatinine level) AND (Serum total bilirubin) AND (Severe) AND (T4 concentrations) AND (Thyroid disease) AND (Wilson's) AND (Women) AND (abnormal) AND (active) AND (acyclovir) AND (alcohol abuse) AND (alcoholic liver disease) AND (alpha-fetoprotein) AND (alpha1-antitrypsin deficiency) AND (anti-neoplastic treatment) AND (antibodies to thyroid peroxidase) AND (anticonvulsant) AND (antidepressant medication) AND (antiviral therapy) AND (at any time during the study) AND (at any time during their participation in the study) AND (at least the previous 3 months) AND (at screening) AND (autoimmune hemolytic anemia) AND (autoimmune hepatitis) AND (bleeding) AND (breast feeding) AND (cancer) AND (cardiac disease) AND (cardiovascular diseases) AND (chronic liver disease) AND (chronic pulmonary disease) AND (clinical manifestations of thyroid disease) AND (clinically relevant) AND (conditions consistent with decompensated liver disease) AND (corticosteroids) AND (current) AND (decompensated) AND (depression) AND (diabetes mellitus) AND (disability) AND (drug abuse) AND (elevation) AND (esophageal varices) AND (expectation) AND (expected to need) AND (females) AND (for at least 3 months) AND (functional limitation) AND (hemochromatosis) AND (hepatic malignancy) AND (hepato-cellular carcinoma) AND (herpetic lesions) AND (hospitalization) AND (hypersensitivity) AND (hypertension) AND (idiopathic thrombocytopenic purpura) AND (immuno-modulatory treatment) AND (immunologically mediated disease) AND (immunomodulatory treatment) AND (in the past) AND (increase) AND (inflammatory bowel disease) AND (interferon) AND (lesion) AND (less than 10%) AND (likelihood of carcinoma) AND (limited course) AND (liver disease) AND (lupus erythematosus) AND (macula degeneration) AND (major depression) AND (major tranquilizer) AND (malignancy) AND (medical condition) AND (men) AND (metabolic liver diseases) AND (more than 1 month prior to the first administration of test drug) AND (more than one) AND (myocardial infarction) AND (not excluded) AND (on prescribed medications) AND (ongoing) AND (ophthalmological disorder) AND (other) AND (other than) AND (peginterferon) AND (platelet count) AND (poorly controlled) AND (pre-existing) AND (pregnancy) AND (psoriasis) AND (psychiatric disease) AND (psychosis) AND (radiation) AND (renal disease) AND (retinopathy) AND (rheumatoid arthritis) AND (risk of recurrence) AND (scleroderma) AND (screening imaging study) AND (seizure disorder) AND (seizure disorders) AND (severe) AND (significant) AND (stability) AND (steroids) AND (suicidal attempt) AND (supraphysiologic doses) AND (suspected) AND (suspicious) AND (systemic) AND (systemic anti-viral) AND (systemic antiviral therapy) AND (telbivudine) AND (test for anti-HCV) AND (test for anti-HIV) AND (thalassemia) AND (the first administration of test drug) AND (the first dose of study drug) AND (the previous 3 months) AND (their participation in the study) AND (therapeutic doses) AND (thyroid function) AND (thyroid stimulating hormone) AND (toxin exposures) AND (treatment) AND (unless) AND (unstable angina) AND (ventricular tachyarrhythmias) AND (will be needed) AND (within 6 months) AND (within the past 6 months) AND (women))"}
{"candidate_id": "LLM02290", "doc_id": "NCT02364648_inc", "case_bucket": "other", "source_criterion": "Stage 3 - 5 Chronic Kidney Disease", "candidate_expression": "((Chronic Kidney Disease) AND (Stage 3 - 5))"}
{"candidate_id": "LLM02291", "doc_id": "NCT02707874_inc", "case_bucket": "other", "source_criterion": "Inpatients having major foot and ankle surgery that will benefit from continuous popliteal sciatic nerve block with an indwelling catheter American Society Anesthesiologists (ASA) physical status I-III 18-85 years of age, inclusive 40-120 kg, inclusive 150 cm of height or greater", "candidate_expression": "((ASA) AND (American Society Anesthesiologists physical status I-III) AND (Inpatients) AND (age 18-85 years) AND (height 150 cm or greater) AND (indwelling catheter) AND (kg 40-120) AND (major foot and ankle surgery) AND (popliteal sciatic nerve block continuous))"}
{"candidate_id": "LLM02292", "doc_id": "NCT01909934_exc", "case_bucket": "or", "source_criterion": "Previous treatment with brentuximab vedotin. Previously received an allogeneic transplant. Patients with current diagnosis of primary cutaneous ALCL (patients whose ALCL has transformed to sALCL are eligible). Known cerebral/meningeal disease including signs or symptoms of progressive multifocal leukoencephalopathy (PML) Female patients who are lactating and breastfeeding or pregnant Known human immunodeficiency virus (HIV) positive Known hepatitis B surface antigen-positive, or known or suspected active hepatitis C infection", "candidate_expression": "((Female patients who are lactating and breastfeeding or pregnant) AND (HIV) AND (PML) AND (active) AND (allogeneic transplant) AND (brentuximab) AND (human immunodeficiency virus) AND (positive) AND (progressive multifocal leukoencephalopathy) AND ((hepatitis B surface antigen) OR (hepatitis C infection)) AND ((primary cutaneous ALCL) OR (sALCL)) AND ((cerebral disease) OR (meningeal disease)))"}
{"candidate_id": "LLM02293", "doc_id": "NCT02571179_exc", "case_bucket": "or", "source_criterion": "a disease that might affect hepatic or renal function, contraindications to opioid analgesics, fetal growth retardation, signs of fetal asphyxia by cardiotocography, meconium stained amniotic fluid or placental insufficiency. The subjects should not have received fentanyl during the previous 14 days.", "candidate_expression": "((cardiotocography) AND (during the previous 14 days) AND (fentanyl) AND (not) AND (opioid analgesics) AND (signs of) AND ((affect hepatic function) OR (affect renal function)) AND ((contraindications) OR (disease) OR (fetal asphyxia) OR (fetal growth retardation) OR (meconium stained amniotic fluid) OR (placental insufficiency)))"}
{"candidate_id": "LLM02294", "doc_id": "NCT01218737_inc", "case_bucket": "or", "source_criterion": "Patient is indicated to have an ocular refractive surgery performed (myopia, astigmatism, hypermetropy) by the Lasik method. Patient presents a normal eye fundus. Patient has intraocular pressure (IOP) ≤ 20 mmHg.", "candidate_expression": "((astigmatism) AND (eye fundus normal) AND (hypermetropy) AND (indicated to have an ocular refractive surgery performed) AND (intraocular pressure (IOP) ≤ 20 mmHg) AND (myopia) AND (normal eye fundus) AND (ocular refractive surgery Lasik method))"}
{"candidate_id": "LLM02295", "doc_id": "NCT02515773_exc", "case_bucket": "or", "source_criterion": "Patients will be excluded if they have had exposure to a total daily dose of MET 1000 mg bid for at least 2 weeks in the past 3 months; Patients will be excluded if they could not tolerate MET during the recommended titration schedule outlined in the protocol; Major neurological or medical illnesses that affect weight gain (e.g., unstable thyroid disease) or require a systemic medication that might impact weight or glucose regulation (e.g., diabetes mellitus [insulin], chronic renal failure [steroids]); Fasting glucose = 126 mg/dL on 2 occasions during screening indicating need for prompt treatment; If lab results are available in the last 6 months, then a serum creatinine =1.3 mg/dL on 2 occasions during screening and/or follow-up, indicating potential impairment of renal functioning; Pregnant or breast feeding; Children and caregivers who are unable to complete assessments for any reason;", "candidate_expression": "((Children and caregivers who are unable to complete assessments for any reason) AND (Fasting glucose = 126 mg/dL 2 o) AND (MET) AND (MET 1000 mg bid at least 2 weeks in the past 3 months) AND (Pregnant or breast feeding) AND (chronic renal failure) AND (diabetes mellitus) AND (insulin) AND (not tolerate) AND (serum creatinine =1.3 mg/dL 2) AND (steroids) AND (thyroid disease unstable))"}
{"candidate_id": "LLM02296", "doc_id": "NCT03115320_exc", "case_bucket": "or", "source_criterion": "- Irregular menstrual cycle demanding preparing endometrium with hormones for frozen-thawed embryo No frozen embryos after IVF cycle Allergy to Pregnyl® or some of its ingredients in the medication or other contraindications due to Pregnyl®", "candidate_expression": "((Allergy) AND (IVF cycle) AND (Irregular menstrual cycle) AND (No) AND (Pregnyl) AND (contraindications) AND (frozen embryos) AND (preparing endometrium with hormones for frozen-thawed embryo) AND (some of its ingredients))"}
{"candidate_id": "LLM02297", "doc_id": "NCT03329456_inc", "case_bucket": "other", "source_criterion": ". Inclusion criteria are American Society of Anesthesiologists (ASA) physical status I-III, age between 18 and 70 years and body mass index (BMI) between 20 and 35 kg/m2.", "candidate_expression": "((ASA) AND (American Society of Anesthesiologists physical status I-III) AND (BMI) AND (age between 18 and 70 years) AND (body mass index between 20 and 35 kg/m2))"}
{"candidate_id": "LLM02298", "doc_id": "NCT03099863_inc", "case_bucket": "or", "source_criterion": "Adult women at least 18 years of age Elective Female Pelvic Medicine and Reconstructive Surgery or Gynecologic Minimally Invasive surgeries including hysterectomy, suburethral sling, and pelvic organ prolapse repair that require cystoscopy.", "candidate_expression": "((Adult) AND (Medicine) AND (Reconstructive Surgery) AND (age at least 18 years) AND (cystoscopy require) AND (hysterectomy) AND (pelvic organ prolapse repair) AND (suburethral sling) AND (surgeries Gynecologic Minimally Invasive) AND (women))"}
{"candidate_id": "LLM02299", "doc_id": "NCT02162433_inc", "case_bucket": "or", "source_criterion": "Patients between 3 to 16 years of age undergoing adenotonsillectomy, with or without myringotomy or myringoplasty ASA 1 & 2", "candidate_expression": "((1 & 2) AND (ASA) AND (adenotonsillectomy) AND (age) AND (between 3 to 16 years) AND (myringoplasty) AND (myringotomy) AND (undergoing))"}
{"candidate_id": "LLM02300", "doc_id": "NCT02713087_exc", "case_bucket": "or", "source_criterion": "Age younger than 18 yrs. or older than 75 yrs. Pregnancy or nursing (negative pregnancy blood test) History of allergic reactions to phenylephrine or ephedrine eGFR < 60ml/min/1.73m2", "candidate_expression": "((Age younger than 18 yrs. or older than 75 yrs.) AND (allergic reactions History) AND (eGFR < 60ml/min/1.73m2) AND (pregnancy blood test negative) AND ((ephedrine) OR (phenylephrine)) AND ((Pregnancy) OR (nursing)))"}
```
