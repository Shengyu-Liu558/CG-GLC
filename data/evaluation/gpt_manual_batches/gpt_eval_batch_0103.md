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
{"candidate_id": "LLM02551", "doc_id": "NCT02635893_exc", "case_bucket": "or", "source_criterion": "Uncontrolled medical problems including pulmonary, cardiovascular or orthopedic disease, Any debilitating disease prior to the SCI that caused exercise intolerance Premorbid, ongoing major depression or psychosis, altered cognitive status History of head injury or stroke, Metal plate in skull History of seizures Receiving drugs acting primarily on the central nervous system, which lower the seizure threshold such as antipsychotic drugs (chlorpromazine, clozapine) or tricyclic antidepressants. Pregnant females, and Ongoing cord compression or a syrinx in the spinal cord or who suffer from a spinal cord disease such as spinal stenosis, spina bifida or herniated cervical disk. Uncontrolled medical problems including pulmonary, cardiovascular or orthopedic disease, Any debilitating disease that causes exercise intolerance Premorbid, ongoing major depression or psychosis, altered cognitive status History of head injury or stroke, Metal plate in skull History of seizures Receiving drugs acting primarily on the central nervous system, which lower the seizure threshold such as antipsychotic drugs (chlorpromazine, clozapine) or tricyclic antidepressants. Pregnant females, and Ongoing cord compression or a syrinx in the spinal cord or who suffer from a spinal cord disease such as spinal stenosis, spina bifida or herniated cervical disk.", "candidate_expression": "((History) AND (History of) AND (Metal plate in skull) AND (Pregnant) AND (Premorbid) AND (Uncontrolled) AND (altered cognitive status) AND (debilitating disease) AND (drugs acting primarily on the central nervous system) AND (exercise intolerance) AND (females) AND (lower the seizure threshold) AND (medical problems) AND (ongoing) AND (prior to the SCI) AND (seizures) AND (spinal cord) AND ((major depression) OR (psychosis)) AND ((head injury) OR (stroke)) AND ((antipsychotic drugs) OR (tricyclic antidepressants)) AND ((chlorpromazine) OR (clozapine)) AND ((cord compression) OR (spinal cord disease) OR (syrinx)) AND ((herniated cervical disk) OR (spina bifida) OR (spinal stenosis)) AND ((cardiovascular disease) OR (orthopedic disease) OR (pulmonary disease)))"}
{"candidate_id": "LLM02552", "doc_id": "NCT02952365_inc", "case_bucket": "other", "source_criterion": "Subjects age 21 and older Subjects with healthy eyes Subjects who have previously undergone LASIK surgery Subjects with residual refractive error.", "candidate_expression": "((21 and older) AND (LASIK surgery) AND (age) AND (healthy eyes) AND (previously) AND (residual refractive error))"}
{"candidate_id": "LLM02553", "doc_id": "NCT02330705_exc", "case_bucket": "or", "source_criterion": "Advanced male factor infertility. Polycystic ovary syndrome (PCOS) as defined by the Rotterdam criteria. Endometriosis. Tubal disease. Uterine abnormalities or myoma. Previous uterine surgery. Metabolic or hormonal abnormalities.", "candidate_expression": "((Advanced) AND (Endometriosis) AND (Polycystic ovary syndrome (PCOS)) AND (Previous) AND (Rotterdam criteria) AND (Tubal disease) AND (male factor infertility) AND (uterine surgery) AND ((Metabolic abnormalities) OR (hormonal abnormalities)) AND ((Uterine abnormalities) OR (myoma)))"}
{"candidate_id": "LLM02554", "doc_id": "NCT03044561_exc", "case_bucket": "or", "source_criterion": "(1) Uterine abnormalities (e.g. septate, bicornuate and fibroid uterus, Asherman Syndrome). Concurrent use of organic nitrites and nitrates. Severe hepatic impairment. Severe renal impairment. Hypotension. Recent stroke or heart attack.", "candidate_expression": "((Hypotension) AND (Uterine abnormalities) AND (hepatic impairment Severe) AND (nitrates Concurrent) AND (organic nitrites Concurrent) AND (renal impairment Severe) AND ((heart attack) OR (stroke)) AND ((Asherman Syndrome) OR (bicornuate uterus) OR (fibroid uterus) OR (septate uterus)))"}
{"candidate_id": "LLM02555", "doc_id": "NCT02689024_exc", "case_bucket": "or", "source_criterion": "multiple injuries (polytrauma patients) previous adverse reaction or known allergy to local anaesthetics or opioids or paracetamol skin infection in proximity of injection site delirious state at presentation in the ED", "candidate_expression": "((adverse reaction) AND (allergy) AND (delirious) AND (local anaesthetics) AND (multiple injuries) AND (opioids) AND (paracetamol) AND (polytrauma) AND (skin infection injection site))"}
{"candidate_id": "LLM02556", "doc_id": "NCT02406885_inc", "case_bucket": "or", "source_criterion": "Men or women, 18 to 65 years old with a BMI of 35 kg/m2 or greater who will be undergoing bariatric surgery (VSG and RYGB) Signed written informed consent Women of childbearing potential (WOCBP) must have a negative serum or urine pregnancy test (minimum sensitivity 25 IU/L or equivalent units of HCG) within 24 hours prior to the start of study drug Women must not be breastfeeding", "candidate_expression": "((18 to 65 years) AND (35 kg/m2 or greater) AND (BMI) AND (RYGB) AND (Signed written informed consent) AND (VSG) AND (Women must not be breastfeeding) AND (Women of childbearing potential (WOCBP) must have a negative serum or urine pregnancy test (minimum sensitivity 25 IU/L or equivalent units of HCG) within 24 hours prior to the start of study drug) AND (bariatric surgery) AND (old) AND ((Men) OR (women)))"}
{"candidate_id": "LLM02557", "doc_id": "NCT02912182_inc", "case_bucket": "other", "source_criterion": "definite unilateral vestibulopathy no pathological HINTS (examination criteria in acute vestibular syndrome) capable of making their own decisions", "candidate_expression": "((HINTS) AND (acute vestibular syndrome) AND (capable of making their own decisions) AND (no) AND (pathological) AND (unilateral) AND (vestibulopathy))"}
{"candidate_id": "LLM02558", "doc_id": "NCT02366819_inc", "case_bucket": "or", "source_criterion": "Histologically confirmed locally advanced gastric (primary endpoint includes proximal and mid-body stomach) or esophagogastric adenocarcinoma; distal gastric (antral) adenocarcinomas are eligible for enrolment but will not be included in the primary analysis Locally advanced disease as determined by endoscopic ultrasound (EUS) stage > primary tumor (T) 3 and/or any T, lymph nodes (N)+ disease without metastatic disease (Mx) All patients must have diagnostic laparoscopy with diagnostic washings for cytology; both cytology positive and negative patients are eligible for enrolment, but only cytology negative patients will be included in the primary analyses; gross peritoneal disease is not eligible Eastern Cooperative Oncology Group (ECOG) performance status =< 1 Eligible for surgery with curative intent Absolute neutrophil count (ANC) >= 1250/ul Hemoglobin >= 9 g/dL Platelets >= 100,000/ul Total bilirubin < 1.5 x upper limit of normal Serum glutamic oxaloacetic transaminase (SGOT) and serum glutamate pyruvate transaminase (SGPT) < 2.5 x upper limit of normal for patients without liver metastases OR SGOT and SGPT < 5 x upper limit of normal for patients with liver metastases Creatinine =< 1.5 x upper limit of normal Measurable or non-measurable disease by Response Evaluation Criteria in Solid Tumor (RECIST) 1.1 will be allowed Women of child-bearing potential and men must agree to use adequate contraception (hormonal or barrier method of birth control; abstinence) prior to study entry and for the duration of study participation, up until 30 days after final study treatment; should a woman become pregnant or suspect that she is pregnant while participating in this study, she should inform her treating physician immediately Patients taking substrates, inhibitors, or inducers of cytochrome P450, family 3, subfamily A, polypeptide 4 (CYP3A4) should be encouraged to switch to alternative drugs whenever possible, given the potential for drug-drug interactions with irinotecan Signed informed consent", "candidate_expression": "((1.1) AND (< 1.5 x upper limit of normal) AND (< 2.5 x upper limit of normal) AND (< 5 x upper limit of normal) AND (=< 1) AND (=< 1.5 x upper limit of normal) AND (> primary tumor (T) 3 and/or any T, lymph nodes (N)+ disease without metastatic disease (Mx)) AND (>= 100,000/ul) AND (>= 1250/ul) AND (>= 9 g/dL) AND (ANC) AND (Absolute neutrophil count) AND (Creatinine) AND (ECOG) AND (EUS) AND (Eastern Cooperative Oncology Group performance status) AND (Hemoglobin) AND (Locally advanced) AND (Platelets) AND (RECIST) AND (Response Evaluation Criteria in Solid Tumor) AND (SGOT) AND (SGPT) AND (Serum glutamic oxaloacetic transaminase) AND (Signed informed consent) AND (Total bilirubin) AND (adenocarcinomas) AND (antral) AND (curative) AND (cytology) AND (diagnostic) AND (disease) AND (distal gastric) AND (endoscopic ultrasound) AND (laparoscopy) AND (liver metastases) AND (locally advanced) AND (omen of child-bearing potential and men must agree to use adequate contraception (hormonal or barrier method of birth control; abstinence) prior to study entry and for the duration of study participation, up until 30 days after final study treatment; should a woman become pregnant or suspect that she is pregnant while participating in this study, she should inform her treating physician immediately) AND (serum glutamate pyruvate transaminase) AND (surgery) AND (washings for cytology) AND (without) AND ((adenocarcinoma gastric) OR (esophagogastric adenocarcinoma)) AND ((negative) OR (positive)) AND ((mid-body stomach) OR (proximal stomach)))"}
{"candidate_id": "LLM02559", "doc_id": "NCT00787254_inc", "case_bucket": "or", "source_criterion": "The patient was on nonsteroid anti-inflammatory drug (NSAID) treatment on the day when consent was obtained, and requires the long-term continuous treatment even after treatment with the investigational drug is started. The patient was confirmed to have a history of gastric ulcer or duodenal ulcer.", "candidate_expression": "((consent) AND (history) AND (nonsteroid anti-inflammatory drug (NSAID)) AND (on the day when consent was obtained) AND (the day when consent was obtained) AND ((duodenal ulcer) OR (gastric ulcer)))"}
{"candidate_id": "LLM02560", "doc_id": "NCT03382106_exc", "case_bucket": "or", "source_criterion": "Women only: Cannot be pregnant or nursing at baseline or plan to become pregnant during the course of the study Body Mass Index (BMI) > 32 Weight > 220 pounds Allergies to shell fish, seafood, eggs or iodine Heart disease, kidney disease or diabetes Diagnosis of asthma Any metal in or on the body (that cannot be removed) between the nose and the abdomen Any major organ system disease (by judgment of the study medical team) A glomerular filtration rate of 60 cc per minute or less. Nitroglycerin usage or nitrates and use of phosphodiesterase 5 (PDE5) inhibitors Prior history of hypersensitivity to sildenafil Currently prescribed a phosphodiesterase (PDE) inhibitors medication (ex: Viagra, Cialis, etc) Known Pulmonary Hypertension Has used e-cigarettes and marijuana <1 years", "candidate_expression": "((Allergies) AND (Body Mass Index (BMI) > 32) AND (Cannot be pregnant or nursing at baseline or plan to become pregnant during the course of the study) AND (Nitroglycerin) AND (Pulmonary Hypertension) AND (Weight > 220 pounds) AND (Women) AND (asthma) AND (glomerular filtration rate 60 cc per minute or less) AND (hypersensitivity Prior history) AND (major organ system disease) AND (nitrates) AND (phosphodiesterase (PDE) inhibitors) AND (phosphodiesterase 5 (PDE5) inhibitors) AND (sildenafil) AND ((eggs) OR (iodine) OR (seafood) OR (shell fish)) AND ((Heart disease) OR (diabetes) OR (kidney disease)) AND ((metal in the body) OR (metal on the body)) AND ((Cialis) OR (Viagra)) AND ((used e-cigarettes) OR (used marijuana)))"}
{"candidate_id": "LLM02561", "doc_id": "NCT00235170_inc", "case_bucket": "or", "source_criterion": "1. Patients with stable (Canadian Cardiovascular Society 1, 2, 3 or 4) or unstable (Braunwald class IB, IC, IIB, IIC, IIIB, IIIC) angina pectoris and ischemia, or patients with atypical chest pain or even those who are asymptomatic provided they have documented myocardial ischaemia (e.g. treadmill exercise test, radionuclide scintigraphy, stress echocardiography, Holter tape); 2. Patients who are eligible for coronary revascularization (angioplasty or CABG); 3. At least 2 lesions (located in different vessels and in different territories) potentially amenable to stent implantation; 4. de novo native vessels; 5. Multivessel disease with at least one significant stenosis in LAD and with treatment of the lesion in another major epicardial coronary artery. A two-vessel disease or a three-vessel disease may be viewed as a combination of a side branch and a main epicardial vessel provided they supply different territories; left anterior descending, left circumflex and right coronary artery); 6. Total occluded vessels. One total occluded major epicardial vessel or side branch can be included and targeted as long as one other major vessel has a significant stenosis amenable for SA, provided the age of occlusion is less than one month e.g. recent instability, infarction with ECG changes in the area subtended by the occluded vessel. Patients with total occluded vessels of unknown duration or existing longer than one month and a reference over 1.50 mm should not be included, not even as a third or fourth vessel to be dilated; 7. Significant stenosis has been defined as a stenosis of more than 50% in luminal diameter (in at least one view, on visual interpretation or preferably by QCA); 8. Left ventricular ejection fraction should be at least 30%.", "candidate_expression": "((Braunwald class IB IC IIB IIC IIIB) AND (CABG) AND (Canadian Cardiovascular Society 1, 2, 3 or 4 unstable) AND (Holter tape) AND (Left ventricular ejection fraction at least 30%) AND (Multivessel disease at least one) AND (Significant stenosis) AND (Total occluded vessels) AND (angina pectoris stable IIIC) AND (angioplasty) AND (asymptomatic documented) AND (atypical chest pain) AND (coronary revascularization eligible for) AND (ischemia) AND (lesions At least 2 potentially amenable located in different vessels located in different territories) AND (myocardial ischaemia) AND (native vessels de novo) AND (radionuclide scintigraphy) AND (reference over 1.50 mm) AND (significant stenosis in LAD) AND (stenosis more than 50% in luminal diameter) AND (stent implantation) AND (stress echocardiography) AND (total occluded major epicardial vessel) AND (total occluded side branch) AND (total occluded vessels unknown duration longer than one month) AND (treadmill exercise test) AND (treatment of the lesion in another major epicardial coronary artery))"}
{"candidate_id": "LLM02562", "doc_id": "NCT02777424_inc", "case_bucket": "or", "source_criterion": "Patient with spontaneous intracranial hemorrhage or traumatic intracranial hemorrhage or patient requiring neurological surgery Coagulation disorder defined by PT less than 60%", "candidate_expression": "((Coagulation disorder) AND (PT less than 60%) AND ((neurological surgery requiring) OR (spontaneous intracranial hemorrhage) OR (traumatic intracranial hemorrhage)))"}
{"candidate_id": "LLM02563", "doc_id": "NCT00989261_inc", "case_bucket": "or", "source_criterion": "1. Males and females age ≥18 years in second relapse or refractory. 2. Males and females age ≥60 years in first relapse or refractory. 3. Must have baseline bone marrow sample taken. 4. Morphologically documented primary AML or AML secondary to myelodysplastic syndrome (MDS with ≥20% bone marrow or peripheral blasts), as defined by the World Health Organization (WHO) criteria, confirmed by pathology review at treating institution. 5. Able to swallow the liquid study drug. 6. ECOG performance status of 0 to 2 7. In the absence of rapidly progressing disease, the interval from prior treatment to time of AC220 administration will be at least 2 weeks for cytotoxic agents or at least 5 half-lives for noncytotoxic agents. The use of chemotherapeutic or antileukemic agents other than hydroxyurea is not permitted during the study with the possible exception of intrathecal (IT) therapy at the discretion of the Investigator and with the agreement of the Sponsor. 8. Persistent chronic clinically significant non-hematological toxicities from prior treatment must be ≤Grade 1. 9. Prior therapy with FLT3 inhibitors is permitted, except previous treatment with AC220. 10. Serum creatinine ≤1.5 × ULN and glomerular filtration rate (GFR) > 30 mL/min 11. Serum potassium, magnesium, and calcium levels should be at least within institutional normal limits. 12. Total serum bilirubin ≤1.5 × ULN 13. Serum aspartate transaminase (AST) and/or alanine transaminase (ALT) ≤2.5 × ULN 14. Females of childbearing potential must have a negative pregnancy test (urine β-hCG). 15. Females of childbearing potential and sexually mature males must agree to use a medically accepted method of contraception throughout the study. 16. Written informed consent must be provided.", "candidate_expression": "((0 to 2) AND (> 30 mL/min) AND (AC220) AND (AML) AND (Able to swallow the liquid study drug.) AND (ECOG performance status) AND (FLT3 inhibitors) AND (Females) AND (Females of childbearing potential and sexually mature males must agree to use a medically accepted method of contraception throughout the study.) AND (Females of childbearing potential must have a negative pregnancy test (urine β-hCG).) AND (MDS) AND (Males) AND (Morphologically documented) AND (Serum aspartate transaminase (AST)) AND (Serum calcium) AND (Serum creatinine) AND (Serum magnesium) AND (Serum potassium) AND (Total serum bilirubin) AND (World Health Organization (WHO) criteria) AND (Written informed consent must be provided.) AND (age) AND (alanine transaminase (ALT)) AND (at least within institutional normal limits) AND (baseline) AND (bone marrow) AND (bone marrow sample) AND (childbearing potential) AND (clinically significant) AND (except) AND (females) AND (first) AND (from prior treatment) AND (glomerular filtration rate (GFR)) AND (myelodysplastic syndrome) AND (negative) AND (non-hematological) AND (pathology review) AND (peripheral blasts) AND (permitted) AND (pregnancy test) AND (primary) AND (prior) AND (refractory) AND (relapse) AND (second) AND (therapy) AND (toxicities) AND (treatment) AND (urine β-hCG) AND (≤1.5 × ULN) AND (≤2.5 × ULN) AND (≤Grade 1) AND (≥18 years) AND (≥20%) AND (≥60 years))"}
{"candidate_id": "LLM02564", "doc_id": "NCT03506750_inc", "case_bucket": "or", "source_criterion": "18 years or older Type 1 or 2 diabetes PDR patients requiring surgical intervention for complications of vitreous hemorrhage or traction retinal detachment and pre-operative IVC treatment. women postmenopausal for 12 months before the study, surgically sterile, or not pregnant and on effective contraception.", "candidate_expression": "((18 years or older) AND (IVC treatment) AND (PDR) AND (Type 1 diabetes) AND (Type 2 diabetes) AND (older) AND (pre-operative) AND (requiring) AND (surgical intervention) AND (traction retinal detachment) AND (vitreous hemorrhage) AND (women postmenopausal for 12 months before the study, surgically sterile, or not pregnant and on effective contraception.))"}
{"candidate_id": "LLM02565", "doc_id": "NCT02337764_inc", "case_bucket": "other", "source_criterion": "The participant has a diagnosis of Parkinson's disease according to the diagnostic criteria of the UK Parkinson's Disease Society Brain Bank. The participant has received a levodopa combination drug for >= 1 month and has either of the following. Wearing off phenomenon Decreased response to levodopa combination drugs The participant has received a levodopa combination drug without change in the dose regimen. The participant is an outpatient of either sex aged >= 30 and < 80 years.", "candidate_expression": "((Decreased response) AND (Parkinson's disease) AND (UK Parkinson's Disease Society Brain Bank) AND (Wearing off phenomenon) AND (aged >= 30 and < 80 years) AND (evodopa combination drugs) AND (levodopa combination >= 1 month) AND (levodopa combination drug without change in the dose regimen))"}
{"candidate_id": "LLM02566", "doc_id": "NCT01567605_inc", "case_bucket": "other", "source_criterion": "traumatic spinal cord injury at least one year ago regular bowel care routine (at least four weeks)", "candidate_expression": "((regular bowel care routine at least four weeks) AND (traumatic spinal cord injury at least one year ago))"}
{"candidate_id": "LLM02567", "doc_id": "NCT03208244_exc", "case_bucket": "other", "source_criterion": "Sensitization (i.e. PRA >20%) Any liver disease in recipient Albumin < 3g/dl or platelet count < 75 x 103/mL Need for dual organ transplant", "candidate_expression": "((Albumin < 3g/dl) AND (PRA >20%) AND (Sensitization) AND (dual organ transplant Need for) AND (liver disease) AND (platelet count < 75 x 103/mL))"}
{"candidate_id": "LLM02568", "doc_id": "NCT02456532_exc", "case_bucket": "or", "source_criterion": "acute or unstable medical disease, current or past history of psychiatric disease, alcoholism or drug abuse, and other primary sleep disorders", "candidate_expression": "((acute) AND (alcoholism) AND (drug abuse) AND (medical disease) AND (primary sleep disorders) AND (psychiatric disease) AND (unstable))"}
{"candidate_id": "LLM02569", "doc_id": "NCT03134378_inc", "case_bucket": "or", "source_criterion": "18 years or older patients who are proven to be infected by Helicobacter pylori based on positive in Urea Breath Test or positive in histopathologic examination of biopsy in antrum and corpus of gaster through esophagoduodenoscopy.", "candidate_expression": "((Urea Breath Test positive) AND (esophagoduodenoscopy) AND (histopathologic examination of biopsy positive antrum of gaster corpus of gaster) AND (infected by Helicobacter pylori) AND (old 18 years or older))"}
{"candidate_id": "LLM02570", "doc_id": "NCT02477280_exc", "case_bucket": "or", "source_criterion": "Affected by alcohol or drugs during the last month. Untreated severe comorbid psychiatric or somatic illness. Bloodpressure 150/95 or higher. Irregular pulse, or pulse 100 or higher. No counter indications according to the Medikinet pill. Concurrent clinical diagnosis that significantly could affect test performance. Concurrent prescription of medicines for ADHD or medicines that significantly could affect test performance.", "candidate_expression": "((100 or higher) AND (150/95 or higher) AND (ADHD) AND (Bloodpressure) AND (Irregular) AND (Untreated) AND (comorbid) AND (last month) AND (medicines) AND (severe) AND ((alcohol) OR (drugs)) AND ((pulse)) AND ((illness psychiatric) OR (somatic illness)))"}
{"candidate_id": "LLM02571", "doc_id": "NCT03058835_inc", "case_bucket": "or", "source_criterion": "18 - 64 years old Able to give consent unprotected sex (in past 6 months) with 1 or more men of unknown HIV status evaluated for an STI within 6 months prior to screening sex in last 6 months with an HIV-infected partner IDU with report of using previously used or shared needles in past 6 months or has been in a methadone, buprenorphine, or suboxone treatment program in past 6 months or engaging in high-risk sexual behaviors individuals engaging in transactional sex (i.e sex for money, drugs, or housing) Infrequently uses condoms during sex with 1 or more partners of unknown HIV status who are known to be at substantial risk of HIV infection (IDU or bisexual male partner) CrCl = 60 ml/min HIV- uninfected women desiring PrEP", "candidate_expression": "((1 or more) AND (18 - 64 years) AND (= 60 ml/min) AND (CrCl) AND (HIV- uninfected) AND (HIV-infected partner) AND (IDU) AND (Infrequently uses condoms during sex) AND (PrEP) AND (at substantial risk of HIV infection) AND (desiring) AND (evaluated for an STI) AND (in last 6 months) AND (in past 6 months) AND (men of unknown HIV status) AND (old) AND (partners of unknown HIV status) AND (screening) AND (sex) AND (transactional sex) AND (unprotected sex) AND (within 6 months prior to screening) AND (women) AND ((buprenorphine) OR (methadone) OR (suboxone)) AND ((engaging in high-risk sexual behaviors) OR (treatment program) OR (using previously used or shared needles)) AND ((sex for drugs) OR (sex for housing) OR (sex for money)) AND ((IDU) OR (bisexual male partner)))"}
{"candidate_id": "LLM02572", "doc_id": "NCT02314559_exc", "case_bucket": "other", "source_criterion": "Dementia. Gastroscopy planned at the same time. Allergies to propofol All cases were a 'full stomach' is suspected (gastric banding) Pregnancy", "candidate_expression": "((Allergies) AND (Dementia) AND (Gastroscopy) AND (Pregnancy) AND (at the same time) AND (planned) AND (propofol))"}
{"candidate_id": "LLM02573", "doc_id": "NCT02964416_inc", "case_bucket": "or", "source_criterion": "Patients with craniotomy for supratentorial tumors under general anesthesia American Society of Anaesthesiologists (ASA) 2 and stable ASA 3 patients Elective surgery Patients with Glasgow Coma Scale (GCS) 15/15", "candidate_expression": "((ASA) AND (ASA stable 3) AND (American Society of Anaesthesiologists 2) AND (Elective surgery) AND (GCS) AND (Glasgow Coma Scale 15/15) AND (craniotomy) AND (general anesthesia) AND (supratentorial tumors))"}
{"candidate_id": "LLM02574", "doc_id": "NCT00543712_exc", "case_bucket": "or", "source_criterion": "Systemic therapy or radiotherapy within 4 weeks prior to Day 1 Prior therapy with agents targeting the DR5 apoptosis pathway Major surgical procedure, open biopsy, or significant traumatic injury within 4 weeks prior to Day 1, or anticipation of need for major surgical procedure during the course of the study Other invasive malignancies within 5 years prior to Day 1 Known active brain metastases Uncontrolled intercurrent illness, including but not limited to ongoing or active infection requiring parenteral antibiotics at enrollment Clinically significant, symptomatic cardiovascular disease, New York Heart Association (NYHA) Grade II or greater congestive heart failure, serious cardiac arrhythmia, Grade II or greater peripheral vascular disease, or history of major heart surgery within 6 months of Day 1, or any situation that would likely limit compliance with study requirements Known to be positive for hepatitis C or hepatitis B surface antigen History of other disease, metabolic dysfunction, physical examination finding, or clinical laboratory finding giving reasonable suspicion of a disease or condition that contraindicates use of an investigational drug or that might affect interpretation of the results of the study or render the patient at high risk for treatment complications Use of anticoagulation therapy Participation in clinical trials or undergoing other investigational procedures within 30 days prior to Day 1 Pregnancy or breast feeding Known sensitivity to any of the products administered during the study Any disorder that compromises the ability of the patient to give written informed consent and/or comply with study procedures", "candidate_expression": "((Day 1) AND (New York Heart Association (NYHA) Grade II or greater) AND (anticoagulation) AND (anticoagulation therapy) AND (any of the products administered during the study) AND (brain metastases active active) AND (cardiac arrhythmia serious Grade II or greater) AND (cardiovascular disease Clinically significant symptomatic) AND (clinical laboratory) AND (clinical laboratory finding suspicion of) AND (congestive heart failure) AND (contraindicates) AND (disease History other) AND (infection) AND (intercurrent illness Uncontrolled) AND (invasive malignancies Other within 5 years prior to Day 1) AND (investigational drug) AND (limit compliance) AND (metabolic dysfunction) AND (parenteral antibiotics at enrollment) AND (physical examination) AND (physical examination finding) AND (sensitivity prior to Day 1) AND (surgical procedure anticipation of need major during the course of the study Day 1 the study) AND (treatment complications) AND NOT (disorder) AND ((Systemic therapy) OR (radiotherapy)) AND ((open biopsy) OR (surgical procedure Major) OR (traumatic injury significant)) AND ((active) OR (ongoing)) AND ((heart surgery history of major) OR (peripheral vascular disease)) AND ((hepatitis B surface antigen) OR (hepatitis C)) AND ((Prior) OR (agents targeting the DR5 apoptosis pathway) OR (therapy)) AND ((condition) OR (disease)) AND ((affect interpretation of the results) OR (render the patient at high risk)) AND ((Participation in clinical trials) OR (undergoing other investigational procedures)) AND ((Pregnancy) OR (breast feeding)) AND ((comply with study procedures) OR (give written informed consent)))"}
{"candidate_id": "LLM02575", "doc_id": "NCT02483715_exc", "case_bucket": "or", "source_criterion": "pregnant or nursing woman serious concomitant illness and malignant tumor of any kind history of hypersensitivity to test drugs serious bleeding during the course of the ulcer previous gastric surgery receiving bismuth salts, PPIs, or antibiotics in the previous month.", "candidate_expression": "((bleeding serious during the course of the ulcer) AND (gastric surgery previous) AND (hypersensitivity history of) AND (illness serious concomitant) AND (malignant tumor any kind) AND (test drugs) AND (woman) AND ((PPIs) OR (antibiotics) OR (bismuth salts)) AND ((nursing) OR (pregnant)))"}
```
