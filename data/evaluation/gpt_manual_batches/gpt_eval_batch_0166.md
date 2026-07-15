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
{"candidate_id": "LLM04126", "doc_id": "NCT01349413_inc", "case_bucket": "other", "source_criterion": "Patients with functional dyspepsia that fulfill Rome III criteria with inadequate relief of dyspeptic symptoms Age >18 Provision of written consent", "candidate_expression": "((Age >18) AND (Provision of written consent) AND (dyspeptic symptoms inadequate relief) AND (functional dyspepsia Rome III criteria))"}
{"candidate_id": "LLM04127", "doc_id": "NCT02766530_exc", "case_bucket": "or", "source_criterion": "Estimated GFR (eGFR) < 60 mL/min/1.73 m2 and blood glucose > 135 mg/dl; Past or present history of acute renal failure, renal dialysis, diabetes mellitus. Women who received metallic fixation, coronary artery stent in recent 3 months; or women who received mechanical valve replacement that is not compatible with MR magnet; or women with aneurysmal clips, pacemakers. Past history of claustrophobia. Women who are pregnant or who are planning to be pregnant, or who are lactating (though the possibility in our target population should be very low) Past history of breast cancer within recent 5 years before the currently diagnosed breast cancer. Women who received chemotherapy for other disease entity in recent 1 year. Women who cannot cooperate with the examinations.", "candidate_expression": "((Women who are pregnant or who are planning to be pregnant, or who are lactating (though the possibility in our target population should be very low)) AND (Women who cannot cooperate with the examinations) AND (breast cancer recent 5 years before the currently diagnosed breast cancer) AND (chemotherapy recent 1 year) AND (claustrophobia) AND (eGFR) AND (mechanical valve replacement) AND ((Estimated GFR < 60 mL/min/1.73 m2) OR (acute renal failure) OR (blood glucose > 135 mg/dl) OR (diabetes mellitus) OR (renal dialysis)) AND ((coronary artery stent) OR (metallic fixation)) AND ((aneurysmal clips) OR (pacemakers)) AND ((Women) OR (women)))"}
{"candidate_id": "LLM04128", "doc_id": "NCT03083197_inc", "case_bucket": "or", "source_criterion": "Age = 15 years old Hospitalization with acute undifferentiated fever (temperature > 37.5 C, tympanic) =14 days or patients admitted to hospital with a history of fever = 14 days who subsequently develop fever within 24 hours of admission Clinically suspected scrub typhus: defined as acute undifferentiated fever with no clear focus of infection and negative malaria blood smear and/or negative malaria RDT. Patients may have one, none, or a combination of other clinical findings such as eschar, rash, lymphadenopathy, headache, myalgia, cough, nausea and abdominal discomfort. A positive scrub typhus RDT (Scrub Typhus IgM RDT, InBios International, Seattle, WA, USA) and/or positive PCR-based detection of O. tsutsugamushi DNA from the admission blood sample Written informed consent and/or, written informed assent as required Able to take oral medication", "candidate_expression": "((Able to take oral medication) AND (Age = 15 years old) AND (Hospitalization =14 days) AND (Scrub Typhus IgM RDT) AND (acute undifferentiated fever) AND (admitted to hospital) AND (fever history = 14 days) AND (fever within 24 hours of admission) AND (oral medication) AND (scrub typhus) AND (temperature > 37.5 C) AND (tympanic) AND NOT (focus of infection) AND ((malaria RDT negative) OR (malaria blood smear negative)) AND ((a combination of) OR (none) OR (one)) AND ((abdominal discomfort) OR (cough) OR (eschar) OR (headache) OR (lymphadenopathy) OR (myalgia) OR (nausea) OR (rash)) AND ((PCR positive O. tsutsugamushi DNA admission blood sample) OR (scrub typhus RDT positive)) AND ((Written informed consent) OR (written informed assent)))"}
{"candidate_id": "LLM04129", "doc_id": "NCT01959425_inc", "case_bucket": "or", "source_criterion": "Successful cardiac ablation for AF Documented freedom from AF recurrence (symptomatic or asymptomatic arrhythmic recurrences lasting longer than 30 seconds) 3 months after successful cardiac ablation (AF recurrence during 3-month blanking period is excluded). Patient must have been on a commercially approved anticoagulation therapy for at least two (2) months prior to randomization in the OAT Study. CHADS2 score = 2 or CHA2DS2-VASc score (=3) Left ventricular ejection fraction > 25% LA size < 65 High risk for thromboembolic events (i.e., CHADS2 score = 2 or CHA2DS2-VASc score = 3) and require OAT before undergoing cardiac ablation Able and willing to comply with all pre- and follow-up testing and requirements Signed informed consent form Age 18 years or older", "candidate_expression": "((18 years or older) AND (3 months after successful cardiac ablation) AND (< 65) AND (= 2) AND (= 3) AND (=3) AND (> 25%) AND (AF) AND (AF recurrence) AND (Age) AND (High) AND (LA size) AND (Left ventricular ejection fraction) AND (OAT) AND (Signed informed consent form) AND (Successful) AND (anticoagulation therapy) AND (arrhythmic recurrences) AND (at least two (2) months prior to randomization) AND (before undergoing cardiac ablation) AND (ble and willing to comply with all pre- and follow-up testing and requirements) AND (cardiac ablation) AND (freedom) AND (longer than 30 seconds) AND (randomization) AND (risk for thromboembolic events) AND ((CHA2DS2-VASc score) OR (CHADS2 score)))"}
{"candidate_id": "LLM04130", "doc_id": "NCT01856491_exc", "case_bucket": "or", "source_criterion": "Known or suspected sensitivity to Dexamethasone Acetate (DXA) Mechanical tricuspid heart valve Subject is enrolled in any other concurrent study without prior written approval from Boston Scientific (BSC), with the exception of local mandatory governmental registries and observational studies/registries that are not in conflict and do not affect the following: Schedule of procedures for the RELIANCE 4-Front Study (i.e. should not cause additional or missed visits); RELIANCE 4-Front Study outcome (i.e. involve medications that could affect the heart rate of the subject); Conduct of the RELIANCE 4-Front Study per Good Clinical Practice (GCP)/ International Organization for Standardization (ISO) 14155:2011/ 21 CFR 812/ local regulations Currently on the active heart transplant list Documented life expectancy of less than 12 months Women of childbearing potential who are or might be pregnant at the time of study enrollment (method of assessment upon physician discretion) Currently requiring chronic dialysis", "candidate_expression": "((Currently) AND (Dexamethasone Acetate (DXA)) AND (Mechanical tricuspid heart valve) AND (Women) AND (active heart transplant list) AND (are or might be) AND (at the time of study enrollment) AND (childbearing potential) AND (chronic dialysis) AND (less than 12 months) AND (life expectancy) AND (pregnant) AND (requiring chronic dialysis) AND (sensitivity to Dexamethasone Acetate (DXA)) AND ((Known) OR (suspected)))"}
{"candidate_id": "LLM04131", "doc_id": "NCT03260790_inc", "case_bucket": "other", "source_criterion": "Diagnosis of asthma", "candidate_expression": "(asthma)"}
{"candidate_id": "LLM04132", "doc_id": "NCT02573597_inc", "case_bucket": "or", "source_criterion": "ASA I & II, Nulliparous and Multiparous, Spontaneous/Induced/Augmented Labor, Early active labor (cervix <5 cm (if known)), Pain (VPS) > 3, 18-45 years of age", "candidate_expression": "((18-45 years) AND (<5 cm) AND (> 3) AND (ASA) AND (Early active labor) AND (I & II) AND (Multiparous) AND (Nulliparous) AND (Pain (VPS)) AND (age) AND (cervix) AND ((Augmented Labor) OR (Induced Labor) OR (Spontaneous Labor)))"}
{"candidate_id": "LLM04133", "doc_id": "NCT03262038_inc", "case_bucket": "or", "source_criterion": "3-17 years weight </= 100kg scheduled for urologic or orthopedic procedure necessitating intrathecal morphine ability to use verbal or pictorial pain assessment tools and techniques informed consent and (if applicable) assent", "candidate_expression": "((3-17 years 3-17 years) AND (ability) AND (informed consent and (if applicable) assent) AND (morphine intrathecal) AND (weight </= 100kg) AND ((pictorial pain assessment tools and techniques) OR (verbal pain assessment tools and techniques)) AND ((orthopedic procedure) OR (urologic procedure)))"}
{"candidate_id": "LLM04134", "doc_id": "NCT00050349_inc", "case_bucket": "or", "source_criterion": "Patients with biopsy-proven metastatic carcinoid tumors or other neuroendocrine tumors (Islet cell, Gastrinomas and VIPomas) with at least one measurable lesion (other than bone) that has either not been previously irradiated or if previously irradiated has demonstrated progression since the radiation therapy The patient has no major impairment of renal or hepatic function, as defined by the following laboratory parameters: total bilirubin <1.5 X ULN; AST, ALT<2.5X ULN (<5 X ULN if liver metastases are present) Patients on Sandostatin Lar (long acting somatostatin analogue) must be on a stable dose for 30 days prior to study entry and short acting somatostatin analogues must be judged to be on a clinically stable dose by the investigator prior to study entry Must have a life expectancy of greater than three (3) months Karnofsky Performance Status > 60 Female patients must have a negative serum pregnancy test at screening. (Not applicable to patients with bilateral oophorectomy and/or hysterectomy or to those patients who are postmenopausal.)", "candidate_expression": "((ALT <2.5X ULN <5 X ULN) AND (AST <2.5X ULN) AND (Female) AND (Karnofsky Performance Status > 60) AND (Sandostatin Lar stable dose) AND (biopsy proven) AND (life expectancy greater than three (3) months) AND (liver metastases) AND (long acting somatostatin analogue) AND (measurable lesion bone) AND (radiation therapy) AND (serum pregnancy test negative at screening) AND (short acting somatostatin analogues clinically stable dose) AND (total bilirubin <1.5 X ULN) AND ((metastatic carcinoid tumors) OR (other neuroendocrine tumors)) AND ((irradiated progression) OR NOT (irradiated)) AND ((major impairment of hepatic function) OR (major impairment of renal function)) AND ((bilateral oophorectomy) OR (hysterectomy) OR (postmenopausal)) AND ((Gastrinomas) OR (Islet cell) OR (VIPomas)))"}
{"candidate_id": "LLM04135", "doc_id": "NCT03354572_inc", "case_bucket": "other", "source_criterion": "Subjects scheduled for laparoscopic unilateral inguinal hernia repair ASA 1 or2. Age >18 years.", "candidate_expression": "((1 or2) AND (>18 years) AND (ASA) AND (Age) AND (inguinal hernia repair) AND (laparoscopic) AND (scheduled) AND (unilateral))"}
{"candidate_id": "LLM04136", "doc_id": "NCT00061308_inc", "case_bucket": "or", "source_criterion": "Have had one prior platinum-based chemotherapy regimen for the treatment of primary disease. At least 4 weeks since last surgery or radiation therapy. Must have had a treatment-free interval of greater than 6 months following response to platinum. ECOG performance status of 0,1, or 2.", "candidate_expression": "((ECOG performance status 0 0,1 .) AND (a treatment-free interval greater than 6 months following response to platinum) AND (platinum) AND (platinum-based chemotherapy regimen prior) AND (primary disease At least 4 weeks since last surgery or radiation therapy))"}
{"candidate_id": "LLM04137", "doc_id": "NCT03176316_inc", "case_bucket": "other", "source_criterion": "Patients will be included if they are having an in-patient spinal fusion procedure, are 18 years or older, post and post-operative pain control plan includes opioid medications.", "candidate_expression": "((18 years or older) AND (in-patient) AND (opioid) AND (pain control plan) AND (post-operative) AND (spinal fusion procedure) AND (years))"}
{"candidate_id": "LLM04138", "doc_id": "NCT02951754_inc", "case_bucket": "other", "source_criterion": "White Brazilian of European descent Fulfillment of the Diagnostic and Statistical Manual of Mental Disorders, Fourth Edition, (DSM-IV) diagnostic criteria for ADHD Eligibility to immediate-release MPH (IR-MPH) treatment", "candidate_expression": "((ADHD) AND (Brazilian) AND (Diagnostic and Statistical Manual of Mental Disorders, Fourth Edition, (DSM-IV) diagnostic criteria) AND (Eligibility) AND (European descent) AND (White) AND (immediate-release MPH (IR-MPH)))"}
{"candidate_id": "LLM04139", "doc_id": "NCT02804126_exc", "case_bucket": "or", "source_criterion": "coagulopathy allergy to to local anesthetics depression, antidepressant drugs treatment epilepsy usage of painkiller before surgery addiction to alcohol or recreational drugs", "candidate_expression": "((allergy) AND (antidepressant drugs) AND (before surgery) AND (coagulopathy) AND (depression) AND (epilepsy) AND (local anesthetics) AND (painkiller) AND ((addiction to alcohol) OR (addiction to recreational drugs)))"}
{"candidate_id": "LLM04140", "doc_id": "NCT01032109_exc", "case_bucket": "or", "source_criterion": "choroidal neovascularization caused by other eye diseases ocular surgery within the past 3 mouths history of uveitis intraocular pressure higher than 25 mmHg, or glaucoma history of systemic or ocular thromboembolic events.", "candidate_expression": "((choroidal neovascularization other) AND (glaucoma systemic ocular) AND (intraocular pressure higher than 25 mmHg) AND (ocular surgery within the past 3 mouths) AND (other eye diseases) AND (thromboembolic events) AND (uveitis history))"}
{"candidate_id": "LLM04141", "doc_id": "NCT02312076_inc", "case_bucket": "other", "source_criterion": "Women subjected to ICSI through controlled ovarian hyperstimulation (COH) with pituitary downregulation by GnRHa.", "candidate_expression": "((ICSI) AND (Women) AND (controlled ovarian hyperstimulation (COH)) AND (pituitary downregulation by GnRHa))"}
{"candidate_id": "LLM04142", "doc_id": "NCT02627560_inc", "case_bucket": "other", "source_criterion": "breast cancer undergoing unilateral mastectomy with or without axillary node dissection received adequate oral and written information about the study and signed an informed-consent form", "candidate_expression": "((axillary node dissection) AND (breast cancer) AND (received adequate oral and written information about the study and signed an informed-consent form) AND (unilateral mastectomy undergoing))"}
{"candidate_id": "LLM04143", "doc_id": "NCT02414399_exc", "case_bucket": "other", "source_criterion": "Contraindication to azithromycin use and other prophylactic antibiotic use", "candidate_expression": "((Contraindication) AND (azithromycin) AND (prophylactic antibiotic use other))"}
{"candidate_id": "LLM04144", "doc_id": "NCT02675153_inc", "case_bucket": "other", "source_criterion": "moderate to severe Crohn's Disease (basic HBI = 7) with stenosis", "candidate_expression": "((Crohn's Disease moderate to severe) AND (basic HBI = 7) AND (stenosis))"}
{"candidate_id": "LLM04145", "doc_id": "NCT03212352_inc", "case_bucket": "or", "source_criterion": "a crown-rump length = 6mm and no cardiac activity OR a crown-rump length <6mm and no fetal growth at least one week later OR At least one week after diagnosis OR a discrepancy of at least one week between crown-rump length and calendar gestational age Intra-uterine pregnancy Women aged above 16 years Hemodynamic stable patient No signs of infection No signs of incomplete abortion No contraindications for mifepristone or misoprostol", "candidate_expression": "((<6mm) AND (= 6mm) AND (At least one week after diagnosis) AND (Hemodynamic stable) AND (Intra-uterine pregnancy) AND (No) AND (Women) AND (above 16 years) AND (aged) AND (at least one week between crown-rump length and calendar gestational age) AND (at least one week later) AND (calendar gestational age) AND (cardiac activity) AND (contraindications for) AND (crown-rump length) AND (diagnosis) AND (discrepancy) AND (fetal growth) AND (mifepristone) AND (misoprostol) AND (no) AND (signs of incomplete abortion) AND (signs of infection))"}
{"candidate_id": "LLM04146", "doc_id": "NCT02886962_exc", "case_bucket": "or", "source_criterion": "Formal indication to oral anticoagulation beside atrial fibrillation (mechanic heart valves, recurrent thrombophlebitis, antiphospholipid syndrome) Life expectancy < 6 months (e.g., terminal cancer) Live donor transplantation scheduled within 6 months Pregnancy (ß-HCG blood-based assay)or nursing (lactating) women Women of child bearing potential, unless they are using an effective method of birth control Patient under legal guardianship Patients under law protection Known hypersensibility to coumadin or indoine derivatives or to any excipients (CI to oral AVK) Severe liver failure (CI to oral AVK)", "candidate_expression": "((< 6 months) AND (Life expectancy) AND (Live donor transplantation) AND (Pregnancy (ß-HCG blood-based assay)or nursing (lactating) women) AND (Severe) AND (Women of child bearing potential, unless they are using an effective method of birth control) AND (atrial fibrillation) AND (hypersensibility) AND (indication) AND (liver failure) AND (oral anticoagulation) AND (scheduled) AND (terminal cancer) AND (within 6 months) AND ((coumadin) OR (indoine)) AND ((antiphospholipid syndrome) OR (mechanic heart valves) OR (recurrent thrombophlebitis)))"}
{"candidate_id": "LLM04147", "doc_id": "NCT03390933_exc", "case_bucket": "or", "source_criterion": "on hemodialysis for less than 3 months comorbid psychotic, bipolar, substance use dependence, Alzheimer's or dementia", "candidate_expression": "((comorbid) AND (for less than 3 months) AND (hemodialysis) AND ((Alzheimer's) OR (bipolar) OR (dementia) OR (psychotic) OR (substance use dependence)))"}
{"candidate_id": "LLM04148", "doc_id": "NCT03518034_exc", "case_bucket": "or", "source_criterion": "Participants with congenital or acquired hypogonadism for whom long-term therapy with placebo would not be medically appropriate Participants with prostate specific antigen (PSA) > 3.0 ng/mL (or 1.5 if on 5-alpha reductase inhibitors) Participants who have been treated with testosterone in the past 6 months and for whom testosterone therapy is contraindicated Confirmed testosterone < 100 ng/dL Body Mass Index (BMI) > 50 Hemoglobin A1c (HbA1C) > 11% Hematocrit (Hct) > 50% Estimated Glomerular Filtration Rate (eGFR) < 30 ml/min History of deep vein thrombosis or pulmonary embolism or prostate cancer or heart failure (Class III and IV).", "candidate_expression": "((Body Mass Index (BMI) > 50) AND (Confirmed testosterone < 100 ng/dL) AND (Estimated Glomerular Filtration Rate (eGFR) < 30 ml/min) AND (Hematocrit (Hct) > 50%) AND (Hemoglobin A1c (HbA1C) > 11%) AND (contraindicated) AND (prostate specific antigen (PSA)) AND (testosterone) AND (testosterone in the past 6 months) AND (testosterone therapy) AND ((acquired hypogonadism) OR (congenital hypogonadism)) AND ((deep vein thrombosis) OR (heart failure) OR (prostate cancer) OR (pulmonary embolism)) AND ((Class III) OR (Class IV)) AND ((5-alpha reductase inhibitors 1.5) OR (> 3.0 ng/mL)))"}
{"candidate_id": "LLM04149", "doc_id": "NCT02361892_inc", "case_bucket": "other", "source_criterion": "submucosal, intramural or subserosal leiomyomas, symptoms of menometrorrhagia, menstrual disorder, infertility, pelvic pain", "candidate_expression": "((infertility) AND (intramural leiomyomas) AND (menometrorrhagia symptoms) AND (menstrual disorder) AND (pelvic pain) AND (submucosal) AND (subserosal leiomyomas))"}
{"candidate_id": "LLM04150", "doc_id": "NCT02579928_inc", "case_bucket": "or", "source_criterion": "MDD Cohort: Meet DSM-5 criteria for Major Depressive Disorder by structured interview (MINI-KID); CDRS-R score >40; Failure to achieve remission with at least 1 adequate prior antidepressant trial (e.g. SSRI, SNRI, or TCA), meaning at least 8 weeks at therapeutic dosing, including at least 4 weeks of stable dosing. Anxiety Cohort: Meet DSM-5 criteria for any of the following anxiety disorders: Social Anxiety Disorders, Generalized Anxiety Disorder, Separation Anxiety Disorder and/or Panic Disorder by structured interview (MINI-KID); ADIS Clinical Severity Rating ≥4 (moderately severe) for any of the 4 included anxiety disorders; Failure to achieve remission with at least 1 adequate prior anxiolytic medication trial (e.g. SSRI, SNRI, or TCA), meaning at least 8 weeks at therapeutic dosing, including at least 4 weeks of stable dosing; Failure to achieve remission with previous CBT or subject declines current CBT therapy Stable psychiatric medications and doses for the month prior to enrollment. Subjects may continue to engage in any ongoing psychotherapy. Medically and neurologically healthy on the basis of physical examination and medical history. Parents able to provide written informed consent and adolescents must additionally provide assent.", "candidate_expression": "((>40) AND (ADIS Clinical Severity Rating) AND (Anxiety Cohort) AND (CBT therapy) AND (CDRS-R score) AND (DSM-5 criteria) AND (Failure) AND (MDD Cohort) AND (MINI-KID) AND (Major Depressive Disorder) AND (Medically healthy) AND (Parents) AND (Stable) AND (Stable doses) AND (adequate) AND (adolescents) AND (antidepressant) AND (antidepressant trial) AND (anxiety disorders) AND (anxiolytic medication) AND (anxiolytic medication trial) AND (at least 1) AND (at least 4 weeks) AND (at least 8 weeks) AND (current) AND (enrollment) AND (for the month prior to enrollment) AND (medical history) AND (moderately severe) AND (neurologically healthy) AND (physical examination) AND (previous) AND (prior) AND (provide assent) AND (provide written informed consent) AND (psychiatric medications) AND (remission) AND (stable dosing) AND (structured interview) AND (therapeutic dosing) AND (≥4) AND ((SNRI) OR (SSRI) OR (TCA)) AND ((Generalized Anxiety Disorder) OR (Panic Disorder) OR (Separation Anxiety Disorder) OR (Social Anxiety Disorders)) AND ((CBT therapy) OR (subject declines)))"}
```
