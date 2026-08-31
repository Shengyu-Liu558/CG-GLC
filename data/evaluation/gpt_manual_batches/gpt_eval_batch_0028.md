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
{"candidate_id": "LLM00676", "doc_id": "NCT02613039_inc", "case_bucket": "other", "source_criterion": "Female subjects aged =/> 18 years and of reproductive age. Capacity to give consent for study participation, after being adequately informed of the aims, benefits, risks, time and motion of the study.", "candidate_expression": "((Female) AND (aged =/> 18 years) AND (reproductive age))"}
{"candidate_id": "LLM00677", "doc_id": "NCT02254668_exc", "case_bucket": "or", "source_criterion": "Renal insufficiency (> 265 µmol/l) Incapability to give informed consent Cardiogenic shock of patient with KILLIP III or IV pregnant or breast feeding females insufficient contraception (only for substudy 3)", "candidate_expression": "((Cardiogenic shock) AND (III or IV) AND (Incapability to give informed consent) AND (KILLIP) AND (Renal insufficiency) AND (contraception) AND (females) AND (insufficient) AND ((breast feeding) OR (pregnant)))"}
{"candidate_id": "LLM00678", "doc_id": "NCT03187639_inc", "case_bucket": "other", "source_criterion": "Aged over 18 Primary symptom of chest pain No contraindication to CTA Willing and able to provide written informed consent", "candidate_expression": "((Aged over 18) AND (CTA) AND (Willing and able to provide written informed consent) AND (chest pain Primary symptom) AND NOT (contraindication))"}
{"candidate_id": "LLM00679", "doc_id": "NCT03209011_inc", "case_bucket": "or", "source_criterion": "HBsAg and HBeAg positive for more than 6 months, HBV DNA detectable with ALT level abnormal lasted for three months and at least time190 IU/L or liver puncture biopsy demonstrated apparent inflammation, never treated before enrolled.", "candidate_expression": "((190 IU/L) AND (ALT level) AND (abnormal) AND (at least time) AND (before enrolled) AND (for more than 6 months) AND (inflammation) AND (lasted for three months) AND (never) AND (treated) AND ((HBeAg positive) OR (HBsAg positive)) AND ((HBV DNA detectable) OR (liver puncture biopsy)))"}
{"candidate_id": "LLM00680", "doc_id": "NCT02863120_exc", "case_bucket": "or", "source_criterion": "Revision total knee arthroplasty Bilateral total knee arthroplasty Patients with inflammatory arthritis Patients with a body mass index (BMI) > 40 Allergy to ropivacaine, bupivacaine, or other local anesthetic agents Current use of opioid drugs Patients with a history of total or unicompartmental reconstruction of the affected joint Patients that have had a high tibial osteotomy or femoral osteotomy Patients with neuromuscular or neurosensory deficiency, which would limit the ability to assess pain levels Patients with a systemic or metabolic disorder leading to progressive bone deterioration Patients that are immunologically compromised, or receiving chronic steroids (>30 days), excluding inhalers Patients' bone stock is compromised by disease or infection, which cannot provide adequate support and/or fixation to the prosthesis Patients with knee fusion to the affected joint Patients with an active or suspected latent infection in or about the knee joint Patients that are prisoners", "candidate_expression": "((Allergy) AND (BMI) AND (Bilateral total knee arthroplasty) AND (Revision total knee arthroplasty) AND (body mass index > 40) AND (bone deterioration progressive) AND (infection knee joint) AND (inflammatory arthritis) AND (knee fusion) AND (opioid) AND (prisoners) AND (reconstruction affected joint) AND NOT (inhalers) AND ((total) OR (unicompartmental)) AND ((femoral osteotomy) OR (high tibial osteotomy)) AND ((neuromuscular deficiency) OR (neurosensory deficiency)) AND ((metabolic disorder) OR (systemic disorder)) AND ((immunologically compromised) OR (steroids chronic >30 days)) AND ((bupivacaine) OR (local anesthetic agents) OR (ropivacaine)))"}
{"candidate_id": "LLM00681", "doc_id": "NCT03518034_inc", "case_bucket": "or", "source_criterion": "Men between 45 and 80 years age Participants with low serum testosterone concentrations (< 300 ng/dL) who exhibit at least one sign or symptom of hypogonadism and have evidence of cardiovascular (CV) disease or are at an increased risk for CV disease.", "candidate_expression": "((Men) AND (age between 45 and 80 years) AND (hypogonadism) AND (serum testosterone concentrations low < 300 ng/dL) AND ((CV disease increased risk) OR (cardiovascular (CV) disease evidence of)) AND ((sign) OR (symptom)))"}
{"candidate_id": "LLM00682", "doc_id": "NCT00639795_exc", "case_bucket": "or", "source_criterion": "Age less than 18 Clinical or laboratory evidence of systemic infection Current pregnancy as assessed by preoperative urine HCG test Serious, uncontrolled, non-malignant illness Malignant illness requiring systemic chemotherapy in the last 6 months Documented allergy to oxycodone, morphine sulfate or acetaminophen Contraindication to peripheral nerve blockade or general anesthesia including: 1. patient refusal 2. active infection at site of planned block 3. documented allergy to any local or general anesthetic medications 4. significant coagulopathy( prothrombin time >15 seconds, INR>1.5 5. pre-existing neuropathy and medical conditions or deformities which would compromise block or anesthetic safety Planned pleurodesis Current use of high dose inhaled or systemic steroids Current use of Amiodarone (Cordarone) Morbid obesity (BMI=40kg/m2) Patients with clinically significant mental health issues such as psychosis requiring treatment with antipsychotic medications. Patients unable to consent Patients with active infections requiring antibiotics within one month of registration Participation in other clinical trials that may interfere with this study", "candidate_expression": "((Age less than 18) AND (Amiodarone Current) AND (BMI 40kg/m2) AND (Contraindication to general anesthesia) AND (Contraindication to peripheral nerve blockade) AND (Cordarone) AND (INR >1.5) AND (Malignant illness) AND (Morbid obesity) AND (acetaminophen) AND (allergy) AND (antibiotics) AND (antipsychotic medications) AND (coagulopathy significant) AND (infections active within one month of registration) AND (mental health issues clinically significant) AND (morphine sulfate) AND (neuropathy pre-existing) AND (non-malignant illness Serious uncontrolled) AND (oxycodone) AND (pleurodesis inhaled) AND (pregnancy preoperative) AND (prothrombin time >15 seconds) AND (psychosis) AND (steroids Current high dose systemic) AND (systemic chemotherapy in the last 6 months) AND (treatment) AND (urine HCG test pregnancy))"}
{"candidate_id": "LLM00683", "doc_id": "NCT03350659_inc", "case_bucket": "or", "source_criterion": "Age >=19 patients who complained of dizziness Orthostatic hypotension after 3-minute standing (systolic blood pressure drop >=20 or diastolic blood pressure drop >=10", "candidate_expression": "((Age >=19) AND (Orthostatic hypotension after 3-minute standing) AND (dizziness) AND ((diastolic blood pressure drop >=10) OR (systolic blood pressure drop >=20)))"}
{"candidate_id": "LLM00684", "doc_id": "NCT02892968_inc", "case_bucket": "other", "source_criterion": "At the cluster level, ED physicians practicing at a participating site will be eligible. At the patient level, all hip fractures seen by a participating ED physician will be eligible", "candidate_expression": "(hip fracture)"}
{"candidate_id": "LLM00685", "doc_id": "NCT02671318_inc", "case_bucket": "or", "source_criterion": "Adult kidney transplant recipients > 18 y.o. Kidney Transplant recipients, after the first episode of cytomegalovirus infection, using the current immunosuppressive regimen: azathioprine or mycophenolate, tacrolimus and prednisone.", "candidate_expression": "((> 18) AND (Adult) AND (cytomegalovirus infection) AND (immunosuppressive regimen) AND (kidney transplant) AND (y.o.) AND ((azathioprine) OR (mycophenolate) OR (prednisone) OR (tacrolimus)))"}
{"candidate_id": "LLM00686", "doc_id": "NCT02609698_exc", "case_bucket": "or", "source_criterion": "Patients with any contraindications or hypersensitivity related to antiplatelet therapy Patients with Acute Myocardial Infarction (ST elevation myocardial infarction, Non ST elevation myocardial infarction) Patients who are anticipated to receive treatment or surgery that may require desisting the administration of antiplatelet therapy for 2 weeks or longer during the period of the clinical trial Chronic total occlusion (CTO) lesions, in-stent restenosis (ISR) Patients experiencing cardiogenic shock Women who are breastfeeding, pregnant, or desiring pregnancy Patients with findings of hemorrhage Patients with a life expectancy of less than 1 year Patients who have received a drug-eluting stent (DES) procedure within the past 6 months Any other patients judged by the investigator to be unsuitable for the trial", "candidate_expression": "((Acute Myocardial Infarction) AND (CTO) AND (DES) AND (ISR) AND (Women who are breastfeeding, pregnant, or desiring pregnancy) AND (anticipated to) AND (antiplatelet therapy) AND (cardiogenic shock) AND (drug-eluting stent procedure) AND (for 2 weeks or longer) AND (hemorrhage) AND (less than 1 year) AND (life expectancy) AND (past 6 months) AND ((contraindications) OR (hypersensitivity)) AND ((surgery) OR (treatment)) AND ((Chronic total occlusion) OR (in-stent restenosis)) AND ((Non ST elevation myocardial infarction) OR (ST elevation myocardial infarction)))"}
{"candidate_id": "LLM00687", "doc_id": "NCT03040024_inc", "case_bucket": "or", "source_criterion": "Current diagnosis of otolaryngeal cancer and undergoing surgery with general anesthesia Competent to provide informed consent", "candidate_expression": "((Competent to provide informed consent) AND (general anesthesia) AND (undergoing) AND ((otolaryngeal cancer) OR (surgery)))"}
{"candidate_id": "LLM00688", "doc_id": "NCT02890719_inc", "case_bucket": "or", "source_criterion": "Age between 18 and 78 year-old. Previous liver transplantation(more than 6 month). Genotype 1 and 4 infection. Hepatitis C recurrence defined by the presence of abnormal liver function test, positive HCV-RNA, histological signs of hepatitis C recurrence. Viral load ≥10000UI/mL. Immunosuppression with tacrolimus and/or mycophenolate (Prednisone use is allowed at low dose, ≤10 mg/d). Treatment naïve or treatment experienced (Peg-RBV or triple therapy).", "candidate_expression": "((1 and 4) AND (Age) AND (Genotype) AND (HCV-RNA) AND (Hepatitis C) AND (Immunosuppression) AND (Peg-RBV) AND (Prednisone) AND (Previous) AND (Treatment naïve) AND (Viral load) AND (abnormal) AND (between 18 and 78 year-old) AND (hepatitis C) AND (histological) AND (histological signs of hepatitis C recurrence) AND (infection) AND (liver function test) AND (liver transplantation) AND (low dose) AND (more than 6 month) AND (mycophenolate) AND (positive) AND (recurrence) AND (tacrolimus) AND (treatment experienced) AND (triple therapy) AND (≤10 mg/d) AND (≥10000UI/mL))"}
{"candidate_id": "LLM00689", "doc_id": "NCT00404495_inc", "case_bucket": "other", "source_criterion": "Cohort 1: Recurrent or refractory medulloblastoma in which current standard treatment approaches have failed; biopsy is not required for recurrent disease. Cohort 2: Newly-diagnosed high-grade glioma (World Health Organization [WHO] grade 3 or 4) Life expectancy ≥ 3 months", "candidate_expression": "((3 or 4) AND (Life expectancy) AND (Recurrent medulloblastoma) AND (World Health Organization [WHO] grade) AND (failed) AND (high-grade glioma) AND (not required) AND (refractory medulloblastoma) AND (standard treatment) AND (≥ 3 months))"}
{"candidate_id": "LLM00690", "doc_id": "NCT02251249_inc", "case_bucket": "or", "source_criterion": "Patient over 18 years weighing between 65 and 85 Kg Referred for STEMI within 6 hours from beginning of chest pain or stable coronary artery disease requiring a loading dose of Prasugrel or Ticagrelor according to the international recommendations. No previous treatment with Clopidogrel, Prasugrel or Ticagrelor. Patient fasting for at least 6 hours. Affiliate or receiving a social security system. Written informed consent.", "candidate_expression": "((Written informed consent) AND (chest pain) AND (fasting for at least 6 hours.) AND (weighing between 65 and 85 Kg) AND (years over 18) AND NOT (treatment previous) AND ((Clopidogrel) OR (Prasugrel) OR (Ticagrelor)) AND ((STEMI within 6 hours from beginning of chest pain) OR (coronary artery disease stable)) AND ((Prasugrel) OR (Ticagrelor)))"}
{"candidate_id": "LLM00691", "doc_id": "NCT02589977_inc", "case_bucket": "or", "source_criterion": "estimated glomerular filtration rate (eGFR) > 60 ml/min preserved left ventricular ejection fraction (>= 50%) on echocardiography HEALTHY: normal cardiac structure and function on echocardiography, BP < 140/90 HYPERTENSIVE: history of BP >140/90, 1 or more antihypertensive medications, LV ejection fraction (LVEF) at least 50%, current BP < 160/90 HFpEF: physician-confirmed diagnosis of HF, symptomatic HF, LVEF at least 50%, elevated LV filling pressure by catheterization, echocardiographic criteria or B-type-natriuretic peptide > 100, current BP < 160/90", "candidate_expression": "((1 or more) AND (< 140/90) AND (< 160/90) AND (> 100) AND (> 60 ml/min) AND (>140/90) AND (>= 50%) AND (B-type-natriuretic peptide) AND (BP) AND (HEALTHY) AND (HF) AND (HFpEF) AND (HYPERTENSIVE) AND (LV ejection fraction (LVEF)) AND (LV filling pressure) AND (LVEF) AND (antihypertensive medications) AND (at least 50%) AND (catheterization) AND (current) AND (current BP) AND (echocardiography) AND (elevated) AND (estimated glomerular filtration rate (eGFR)) AND (history) AND (left ventricular ejection fraction) AND (normal cardiac function) AND (normal cardiac structure) AND (physician-confirmed) AND (preserved) AND (symptomatic))"}
{"candidate_id": "LLM00692", "doc_id": "NCT02675153_inc", "case_bucket": "other", "source_criterion": "moderate to severe Crohn's Disease (basic HBI = 7) with stenosis", "candidate_expression": "((= 7) AND (Crohn's Disease) AND (basic HBI) AND (moderate to severe) AND (stenosis))"}
{"candidate_id": "LLM00693", "doc_id": "NCT02203019_exc", "case_bucket": "or", "source_criterion": "Patients with documented allergies to propofol, dexmedetomidine, fentanyl, eggs or egg products, or soy or soy products. A heart rate less than 50 beats/minute or grade 2 or 3 AV heart block Mean arterial pressure less than 55 mmHg despite appropriate fluid resuscitation and vasopressor support. Current triglyceride level > 400 mg/dl", "candidate_expression": "((AV heart block grade 2 grade 3) AND (Mean arterial pressure less than 55 mmHg) AND (allergies) AND (dexmedetomidine) AND (egg products) AND (eggs) AND (fentanyl) AND (fluid resuscitation) AND (heart rate less than 50 beats/minute) AND (propofol) AND (soy) AND (soy products) AND (triglyceride level > 400 mg/dl) AND (vasopressor))"}
{"candidate_id": "LLM00694", "doc_id": "NCT02200978_inc", "case_bucket": "other", "source_criterion": "Patients less than 16 years old with newly diagnosed PML-RARa positive acute promyelocytic leukemia.", "candidate_expression": "((PML-RARa positive) AND (acute promyelocytic leukemia) AND (old less than 16 years))"}
{"candidate_id": "LLM00695", "doc_id": "NCT00312429_exc", "case_bucket": "or", "source_criterion": "Undergoing Interleukin-2 (IL-2) therapy within 8 weeks of study entry Diagnosed with a medical or psychiatric illness that may interfere with study participation Pregnant", "candidate_expression": "((Interleukin-2 (IL-2) therapy) AND (Pregnant) AND (within 8 weeks of study entry) AND ((illness that may interfere with study participation medical) OR (psychiatric illness that may interfere with study participation)))"}
{"candidate_id": "LLM00696", "doc_id": "NCT02546856_exc", "case_bucket": "or", "source_criterion": "Contraindications for BB. Living in a nursing home. Life expectancy < 6 months. Unable to self-care or mental disease without caregiver. Unable to weight Without phone Unable to go to clinic visit.", "candidate_expression": "((< 6 months) AND (BB) AND (Contraindications) AND (Life expectancy) AND (Living) AND (Unable) AND (Unable to self-care) AND (Without) AND (go to clinic visit) AND (mental disease) AND (nursing home) AND (phone) AND (weight) AND (without caregiver))"}
{"candidate_id": "LLM00697", "doc_id": "NCT00728156_inc", "case_bucket": "or", "source_criterion": "Patients with T2DM and CAS as defined below: Clinical definitions T2DM: Diagnosed according to the WHO criteria [53]. CAD:Presence of any one of the following: Angina plus positive exercise tolerance test, enzyme and/or Q wave positive myocardial infarction, angiographic evidence ( >50% stenosis of one vessel), percutaneous or surgical coronary revascularisation. Aged between 18 and 75 Provided written consent for participation in the trial prior to any study-specific procedures or requirements.", "candidate_expression": "((>50%) AND (Aged) AND (Angina) AND (CAD) AND (CAS) AND (T2DM) AND (WHO criteria) AND (any study-specific procedures or requirements) AND (between 18 and 75) AND (exercise tolerance test) AND (positive) AND (prior to any study-specific procedures or requirements) AND (stenosis of one vessel) AND (written consent for participation in the trial) AND ((Q wave positive) OR (enzyme positive)) AND ((angiographic evidence) OR (coronary revascularisation) OR (myocardial infarction)) AND ((percutaneous) OR (surgical)))"}
{"candidate_id": "LLM00698", "doc_id": "NCT03400735_exc", "case_bucket": "or", "source_criterion": "Pregnancy or breastfeeding Allergy against to penicillin or cephalosporins Renal impairment Active hepatic disease Antibiotic use except study drugs Immunosuppressive therapy before 6 months of study initiation Use of probenecid like drugs", "candidate_expression": "((Active) AND (Allergy) AND (Antibiotic) AND (Immunosuppressive therapy) AND (Pregnancy) AND (Renal impairment) AND (before 6 months of study initiation) AND (breastfeeding) AND (cephalosporins) AND (except) AND (hepatic disease) AND (penicillin) AND (probenecid) AND (probenecid like) AND (probenecid like drugs) AND (study drugs) AND (study initiation))"}
{"candidate_id": "LLM00699", "doc_id": "NCT02632760_exc", "case_bucket": "or", "source_criterion": "Pregnancy Known hypersensitivity to study drug (ferric carboxymaltose or equivalent) or its excipients Known or suspected haemoglobinopathy/thalassaemia Bone marrow disease Haemochromatosis Renal dialysis Erythropoietin or IV iron in the previous 4 weeks", "candidate_expression": "((Bone marrow disease) AND (Haemochromatosis) AND (Pregnancy) AND (Renal dialysis) AND (ferric carboxymaltose) AND (hypersensitivity) AND (in the previous 4 weeks) AND (study drug) AND ((Erythropoietin) OR (IV iron)) AND ((haemoglobinopathy) OR (thalassaemia)) AND ((Known) OR (suspected)))"}
{"candidate_id": "LLM00700", "doc_id": "NCT01943812_exc", "case_bucket": "or", "source_criterion": "endometrial thickness < 7 mm or no triple layer endometrium and/or functional follicles Uterine abnormality Chronic medical disease oocyte donation cycles", "candidate_expression": "((Chronic medical disease) AND (Uterine abnormality) AND (endometrial thickness < 7 mm) AND (functional follicles) AND (oocyte donation cycles) AND (triple layer endometrium))"}
```
