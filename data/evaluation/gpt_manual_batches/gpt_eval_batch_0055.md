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
{"candidate_id": "LLM01351", "doc_id": "NCT02844907_exc", "case_bucket": "or", "source_criterion": "Rheumatoid arthritis Diabetes or immediate family history of diabetes Coronary artery disease Congestive heart failure Pulmonary disorders, including COPD and asthma Malabsorptive GI disease, such as celiac disease, or gastric bypass Significant hepatic disease Renal insufficiency (eGFR < 60 mL/kg/min) Anemia (hematocrit < 34%) as measured at screening visit Pregnant females Consumption of daily medications that alter glucose metabolism of GI function (glucocorticoids, psychotropics, narcotics, metoclopramide) Consumption or injection of insulin Apparent sensitivity to any of the study peptides as determined by the skin test Diagnosis or h/o PTSD, depression, substance use, mental health problems, sleep disorders, HPA disruption and/or TBI", "candidate_expression": "((Anemia) AND (Congestive heart failure) AND (Coronary artery disease) AND (Malabsorptive GI disease) AND (Pregnant) AND (Pulmonary disorders) AND (Renal insufficiency) AND (Rheumatoid arthritis) AND (eGFR < 60 mL/kg/min) AND (females) AND (hematocrit < 34%) AND (hepatic disease Significant) AND (injection) AND (medications daily that alter glucose metabolism of GI function) AND (screening visit) AND (sensitivity) AND (skin test) AND (study peptides) AND ((celiac disease) OR (gastric bypass)) AND ((Diabetes) OR (diabetes immediate family history)) AND ((glucocorticoids) OR (metoclopramide) OR (narcotics) OR (psychotropics)) AND ((insulin)) AND ((HPA disruption) OR (PTSD) OR (TBI) OR (depression) OR (mental health problems) OR (sleep disorders) OR (substance use)) AND ((COPD) OR (asthma)))"}
{"candidate_id": "LLM01352", "doc_id": "NCT03318874_exc", "case_bucket": "or", "source_criterion": "Glaucoma, Ocular allergy Autoimmune disease Contact lens-wear during study Current punctal plugging Pregnant/lactating Candidate for topical anti-inflammatory Cicatricial meibomian gland dysfunction", "candidate_expression": "((Autoimmune disease) AND (Contact lens-wear during study) AND (Glaucoma) AND (Ocular allergy) AND (Pregnant) AND (lactating) AND (meibomian gland dysfunction Cicatricial) AND (punctal plugging Current) AND (topical anti-inflammatory Candidate for))"}
{"candidate_id": "LLM01353", "doc_id": "NCT02961764_inc", "case_bucket": "other", "source_criterion": "Presents to the Emergency Department (ED) and meets the clinical definition for Acute Bacterial Skin and Skin Structure Infections (ABSSSI) Known or suspected gram-positive infection.", "candidate_expression": "((ABSSSI) AND (Acute Bacterial Skin and Skin Structure Infections) AND (Emergency Department (ED)) AND (infection gram-positive))"}
{"candidate_id": "LLM01354", "doc_id": "NCT03491059_exc", "case_bucket": "or", "source_criterion": "not a regular user of e-cigarettes pregnant or lactating (only excluded from imaging study) prisoner incapable of giving informed consent unable to lie flat on the scanner for extended periods of time unstable medical condition like heart disease, uncontrolled hypertension, thyroid disease, diabetes, renal or liver impairment, or glaucoma prostatic hypertrophy, stroke, or ulcer in past year psychiatric conditions such as schizophrenia, adult ADHD, or bipolar disorder current or regular use of psychiatric medications such as tranquilizers, antipsychotics, and/or antidepressants use of medications that are inducers of CYP2A6 (a nicotine metabolizing enzyme) such as rifampicin, dexamethasone, phenobarbital, and other anti-convulsant drugs unable to communicate in English current use of smokeless tobacco, tobacco cigarettes (5 and fewer a day) occasional use of pipes is permitted if subject abstains for the week prior to the study older than 80 years", "candidate_expression": "((5 and fewer a day) AND (e-cigarettes) AND (incapable of giving informed consent) AND (inducers of CYP2A6) AND (medical condition) AND (medications) AND (nicotine metabolizing enzyme) AND (not) AND (older than 80) AND (pregnant or lactating (only excluded from imaging study)) AND (prisoner) AND (psychiatric conditions) AND (psychiatric medications) AND (regular user) AND (unable to lie flat on the scanner for extended periods of time) AND (uncontrolled) AND (unstable) AND (years) AND ((diabetes) OR (glaucoma) OR (heart disease) OR (hypertension) OR (liver impairment) OR (renal impairment) OR (thyroid disease)) AND ((prostatic hypertrophy) OR (stroke) OR (ulcer)) AND ((adult ADHD) OR (bipolar disorder) OR (schizophrenia)) AND ((antidepressants) OR (antipsychotics) OR (tranquilizers)) AND ((anti-convulsant drugs) OR (dexamethasone) OR (phenobarbital) OR (rifampicin)) AND ((smokeless tobacco) OR (tobacco cigarettes)))"}
{"candidate_id": "LLM01355", "doc_id": "NCT02515773_exc", "case_bucket": "or", "source_criterion": "Patients will be excluded if they have had exposure to a total daily dose of MET 1000 mg bid for at least 2 weeks in the past 3 months; Patients will be excluded if they could not tolerate MET during the recommended titration schedule outlined in the protocol; Major neurological or medical illnesses that affect weight gain (e.g., unstable thyroid disease) or require a systemic medication that might impact weight or glucose regulation (e.g., diabetes mellitus [insulin], chronic renal failure [steroids]); Fasting glucose = 126 mg/dL on 2 occasions during screening indicating need for prompt treatment; If lab results are available in the last 6 months, then a serum creatinine =1.3 mg/dL on 2 occasions during screening and/or follow-up, indicating potential impairment of renal functioning; Pregnant or breast feeding; Children and caregivers who are unable to complete assessments for any reason;", "candidate_expression": "((1000 mg bid) AND (2) AND (2 o) AND (= 126 mg/dL) AND (=1.3 mg/dL) AND (Children and caregivers who are unable to complete assessments for any reason) AND (Fasting glucose) AND (MET) AND (Pregnant or breast feeding) AND (at least 2 weeks in the past 3 months) AND (chronic renal failure) AND (diabetes mellitus) AND (insulin) AND (not tolerate) AND (serum creatinine) AND (steroids) AND (thyroid disease) AND (unstable))"}
{"candidate_id": "LLM01356", "doc_id": "NCT03187379_inc", "case_bucket": "other", "source_criterion": "bariatric surgery patients laparoscopic roux-en-y gastric bypass use of EEA stapler anastomosis", "candidate_expression": "((EEA stapler anastomosis) AND (bariatric surgery) AND (roux-en-y gastric bypass laparoscopic))"}
{"candidate_id": "LLM01357", "doc_id": "NCT01757717_exc", "case_bucket": "or", "source_criterion": "Patients who may receive therapeutically effective doses via an external beam approach to the lesion of interest as specified by MSKCC Radiation Oncology Department dose constraint criteria. Patients with kyphoplasty cement or hardware that would preclude effective catheter placement. Patients with paraspinal extension of disease with visceral involvement. Abnormal complete blood count. Any of the following: Platelet count < 75,000/ml Hb level < 9gm/dl WBC < 3.5/ml Abnormal coagulation profile: INR > 2.5 and/or PTT > 80 Patients who are on anticoagulation medication that may not be safely held for the procedure (≥ 5 days for antiplatelet agents and warfarin; ≥ 24 hours for low-molecular weight heparin formulations) will be excluded. Contraindications to general anesthesia", "candidate_expression": "((Abnormal coagulation profile) AND (Abnormal complete blood count) AND (Contraindications to general anesthesia) AND (Hb level < 9gm/dl) AND (INR > 2.5) AND (MSKCC Radiation Oncology Department dose constraint criteria) AND (PTT > 80) AND (Platelet count < 75,000/ml) AND (WBC < 3.5/ml) AND (anticoagulation medication may not be safely held for the procedure) AND (antiplatelet agents ≥ 5 days) AND (coagulation profile Abnormal) AND (complete blood count Abnormal) AND (doses therapeutically effective) AND (external beam) AND (general anesthesia) AND (kyphoplasty cement) AND (kyphoplasty hardware) AND (low-molecular weight heparin ≥ 24 hours) AND (may not be safely held for the procedure) AND (may receive therapeutically effective doses via an external beam approach to the lesion of interest) AND (paraspinal extension of disease) AND (visceral involvement) AND (warfarin ≥ 5 days))"}
{"candidate_id": "LLM01358", "doc_id": "NCT02735577_inc", "case_bucket": "or", "source_criterion": "Between the ages of 21-60 Right-handed Capable of giving informed consent and complying with study procedures Reports drinking a minimum of 5 standard drinks for men or 4 standard drinks for women on at least 4 days per week on average over the past 28 days Meets DSM-V criteria for current Alcohol Use Disorder Seeking treatment for Alcohol Use Disorder Agree to not seek additional treatment, apart from Alcoholics Anonymous Willing to attempt to abstain from alcohol completely for the duration of the study Willing to be hospitalized on a research unit for 24 hours, longer if detoxification is needed.", "candidate_expression": "((4 standard drinks on at least 4 days per week) AND (Alcohol Use Disorder) AND (Between 21-60) AND (DSM-V criteria) AND (Meets) AND (Right-handed) AND (Seeking) AND (Willing) AND (Willing to be hospitalized on a research unit for 24 hours, longer if detoxification is needed) AND (abstain from alcohol) AND (ages) AND (completely) AND (drinking) AND (men) AND (minimum of 5 standard drinks on at least 4 days per week) AND (over the past 28 days) AND (treatment) AND (women))"}
{"candidate_id": "LLM01359", "doc_id": "NCT02783859_exc", "case_bucket": "or", "source_criterion": "Current wheeze Underlying chronic illness other than asthma (e.g. bronchiectasis, cyanotic congenital heart disease or cardiac failure, neuromuscular disorders, immunodeficiency) that could potentially influence the current illness Severe malnutrition (weight-for-height Z-score <-3) Complicated (effusion, empyema or abscess) pneumonia, including tuberculosis Extra-pulmonary infection requiring antibiotic therapy (e.g. meningitis) Beta-lactam allergy Previously enrolled Lack a mobile phone and/or unable to return for follow-up clinic visits during the next 24 months", "candidate_expression": "((<-3) AND (Beta-lactam) AND (Complicated pneumonia) AND (Extra-pulmonary) AND (Lack a mobile phone and/or unable to return for follow-up clinic visits during the next 24 months) AND (Previously enrolled) AND (Severe) AND (abscess) AND (allergy) AND (antibiotic therapy) AND (asthma) AND (bronchiectasis) AND (cardiac failure) AND (chronic illness) AND (cyanotic congenital heart disease) AND (effusion) AND (empyema) AND (immunodeficiency) AND (infection) AND (malnutrition) AND (meningitis) AND (neuromuscular disorders) AND (other) AND (tuberculosis) AND (weight-for-height Z-score) AND (wheeze))"}
{"candidate_id": "LLM01360", "doc_id": "NCT03182114_exc", "case_bucket": "other", "source_criterion": "Cardiac morbidities hypertensive disorders of pregnancy peripartum bleeding baseline systolic blood pressure (SBP) < 100 mmHg body mass index > 35", "candidate_expression": "((Cardiac morbidities) AND (SBP) AND (body mass index > 35) AND (hypertensive disorders of pregnancy) AND (peripartum bleeding) AND (systolic blood pressure baseline < 100 mmHg))"}
{"candidate_id": "LLM01361", "doc_id": "NCT01650792_exc", "case_bucket": "or", "source_criterion": "Patients with a history of an untreated malignancy (except local skin cancers) Ischemic stroke (determined using the Questionnaire for Verifying Stroke-Free Status (QVSFS) Patients on renal dialysis or with end-stage hepatic dysfunction Acute infection/inflammation (Temperature > 101.5 F, and/or WBC> 15, 000) Inability to obtain informed consent from patient or next of kin Anticoagulant use (warfarin or heparin)", "candidate_expression": "((> 101.5 F) AND (> 15, 000) AND (Acute) AND (Anticoagulant) AND (Inability to obtain informed consent from patient or next of kin) AND (Ischemic stroke) AND (Questionnaire for Verifying Stroke-Free Status (QVSFS)) AND (Temperature) AND (WBC) AND (end-stage hepatic dysfunction) AND (except) AND (heparin) AND (infection) AND (inflammation) AND (local skin cancers) AND (malignancy) AND (renal dialysis) AND (untreated) AND (warfarin))"}
{"candidate_id": "LLM01362", "doc_id": "NCT02766530_inc", "case_bucket": "other", "source_criterion": "Women aged 25-75 years old. Women with recently diagnosed breast cancer and who will receive NAC to reduce tumor burden before surgery. (including locally advanced breast cancer (LABC) according to clinical assessment; or tumor size > 2cm, that is, at least T2 in TNM staging).", "candidate_expression": "((25-75 years old) AND (NAC) AND (Women) AND (aged) AND (before surgery) AND (breast cancer) AND (reduce tumor burden) AND (surgery))"}
{"candidate_id": "LLM01363", "doc_id": "NCT02406885_inc", "case_bucket": "or", "source_criterion": "Men or women, 18 to 65 years old with a BMI of 35 kg/m2 or greater who will be undergoing bariatric surgery (VSG and RYGB) Signed written informed consent Women of childbearing potential (WOCBP) must have a negative serum or urine pregnancy test (minimum sensitivity 25 IU/L or equivalent units of HCG) within 24 hours prior to the start of study drug Women must not be breastfeeding", "candidate_expression": "((18 to 65 years) AND (35 kg/m2 or greater) AND (BMI) AND (Men) AND (RYGB) AND (Signed written informed consent) AND (VSG) AND (Women must not be breastfeeding) AND (Women of childbearing potential (WOCBP) must have a negative serum or urine pregnancy test (minimum sensitivity 25 IU/L or equivalent units of HCG) within 24 hours prior to the start of study drug) AND (bariatric surgery) AND (old) AND (women))"}
{"candidate_id": "LLM01364", "doc_id": "NCT00720031_inc", "case_bucket": "or", "source_criterion": "HLA-A2 melanoma patients with : either loco-regional or lymph node metastasis transit nodules not surgically resectable measurable cutaneous or visceral metastasis Patients' tumor express Melan-A/MART-1 antigen. No chemotherapy treatment (except for Deticene used before the first T cell clones infusion) or radiotherapy or immunotherapy in the last 4 weeks before infusion. No other melanoma treatment during the protocol. Life expectancy should be greater than 6 months. General state with Karnowsky greater than 80, ECOG = 0, 1 or 2. Patient should be negative for HIV and B and C hepatitis. Biological parameters at the beginning of the study: leucocytes ³ 2000 elements per mm3, hemoglobin ³ 10.5g/dl, platelets ³ 100 000 per mm3, phosphatases alcalines transaminases £ 1 time 1/2 compared to the normal. Signed informed consent", "candidate_expression": "((B hepatitis) AND (C hepatitis) AND (ECOG 0, 1 or 2) AND (HIV) AND (Karnowsky greater than 80) AND (Life expectancy greater than 6 months) AND (MART-1 antigen) AND (Melan-A antigen) AND (Signed informed consent) AND (chemotherapy) AND (cutaneous metastasis) AND (hemoglobin ³ 10.5g/dl) AND (immunotherapy) AND (leucocytes ³ 2000 elements per mm3) AND (loco-regional metastasis) AND (lymph node metastasis) AND (melanoma) AND (melanoma HLA-A2) AND (phosphatases alcalines transaminases £ 1 time 1/2 compared to the normal) AND (platelets ³ 100 000 per mm3) AND (radiotherapy) AND (surgically) AND (transit nodules surgically resectable) AND (treatment during the protocol) AND (visceral metastasis) AND NOT (Deticene before the first T cell clones infusion))"}
{"candidate_id": "LLM01365", "doc_id": "NCT03140423_exc", "case_bucket": "other", "source_criterion": "Exclusion criteria includes ICUs with an average length of stay of less than 2 days; HCA hospitals that are not able to transfer or merge data into the centralized data warehouse for the baseline and intervention periods of the study are also excluded.", "candidate_expression": "((ICUs) AND (average length of stay less than 2 days))"}
{"candidate_id": "LLM01366", "doc_id": "NCT02773173_inc", "case_bucket": "other", "source_criterion": "Patients older than 18 years Classification of the American Society of Anesthesiologists (ASA I-III) No cognitive deficits Signed informed consent prior to surgery", "candidate_expression": "((ASA I-III) AND (Classification of the American Society of Anesthesiologists) AND (Signed informed consent prior to surgery) AND (years older than 18) AND NOT (cognitive deficits))"}
{"candidate_id": "LLM01367", "doc_id": "NCT03472495_exc", "case_bucket": "or", "source_criterion": "Limited English proficiency (LEP) Pregnant Prisoners Wolff Parkinson White syndrome Administration of electrical or chemical cardioversion before screening Administration of other antiarrhythmics for acute heart rate control (excluding adenosine) History of allergy or idiosyncratic reaction to diltiazem Unable to take oral medications Heart rate <60 beats/min", "candidate_expression": "((<60 beats/min) AND (Heart rate) AND (LEP) AND (Limited English proficiency) AND (Pregnant) AND (Prisoners) AND (Unable to take) AND (Wolff Parkinson White syndrome) AND (acute) AND (adenosine) AND (antiarrhythmics) AND (before screening) AND (diltiazem) AND (excluding) AND (heart rate control) AND (oral medications) AND (screening) AND ((allergy) OR (idiosyncratic reaction)) AND ((chemical cardioversion) OR (electrical cardioversion)))"}
{"candidate_id": "LLM01368", "doc_id": "NCT02003339_inc", "case_bucket": "or", "source_criterion": "Early, intermediate, advanced, non metastatic Hepatocellular Carcinoma. Indication for radioembolization validated after pluridisciplinary committee meeting. Isolated target on initial imagery (invasive hepatocellular carcinoma excluded) WHO (World Health organization) Performance status: 0, 1 or 2 If cirrhosis, Child A score with total bilirubin less than 30 micromoles per liter Creatinine clearance more or equal to 30 mL/min Patient informed and consent signature obtained", "candidate_expression": "((0, 1 or 2) AND (A) AND (Child score) AND (Creatinine clearance) AND (Early) AND (Hepatocellular Carcinoma) AND (Indication) AND (Patient informed and consent signature obtained) AND (WHO (World Health organization) Performance status) AND (advanced) AND (cirrhosis) AND (intermediate) AND (less than 30 micromoles per liter) AND (metastatic) AND (more or equal to 30 mL/min) AND (non) AND (radioembolization) AND (total bilirubin))"}
{"candidate_id": "LLM01369", "doc_id": "NCT01118871_inc", "case_bucket": "or", "source_criterion": "HIV-1 infected males or females over 18 years of age signed informed consent currently receiving a stable antiretroviral regimen comprising of: two or more licensed NRTIs one licensed NNRTI or boosted protease inhibitor no previous protease inhibitor resistance documented on HIV-1 genotypic resistance testing failure of current antiretroviral regimen due to: toxicity, intolerance or virological failure if receiving an NNRTI containing regimen at screening toxicity or intolerance if receiving a boosted-protease inhibitor regimen at screening (with plasma HIV RNA < 400 copies/mL at screening) willing to modify antiretroviral therapy, in accordance with the randomisation assignment no previous exposure to etravirine subjects in good health upon medical history, physical exam, and laboratory testing in the opinion of the investigator have no serologic evidence of active HBV infection evidenced by negative hepatitis B surface antigen female subjects who are heterosexually active and of childbearing potential (i.e., not surgically sterile or at least two years post menopausal) must practice contraception as follows from screening through completion of the study: barrier contraceptives (condom, diaphragm with spermicide) IUD or Depo PLUS a barrier contraceptive female subjects of childbearing potential must have a negative pregnancy test.", "candidate_expression": "((HBV infection) AND (HIV-1) AND (HIV-1 genotypic resistance) AND (HIV-1 genotypic resistance testing) AND (HIV-1 infected) AND (NNRTI) AND (NNRTI containing regimen at screening) AND (NRTI two or more licensed) AND (age over 18 years) AND (antiretroviral regimen) AND (antiretroviral regimen current) AND (antiretroviral therapy willing) AND (barrier contraceptive) AND (barrier contraceptives) AND (boosted-protease inhibitor regimen at screening) AND (childbearing potential) AND (contraception) AND (failure of current antiretroviral regimen) AND (female) AND (female subjects who are heterosexually active and of childbearing potential (i.e., not surgically sterile or at least two years post menopausal) must practice contraception as follows from screening through completion of the study:) AND (good health) AND (hepatitis B surface antigen negative) AND (heterosexually active) AND (laboratory testing) AND (medical history) AND (physical exam) AND (plasma HIV RNA < 400 copies/mL at screening) AND (pregnancy test negative) AND (protease inhibitor) AND (protease inhibitor resistance) AND (serologic evidence of active HBV infection) AND (signed informed consent) AND (surgically) AND NOT (etravirine previous) AND (NOT (surgically sterile) OR NOT (post menopausal at least two years)) AND ((NNRTI) OR (boosted protease inhibitor)) AND ((intolerance) OR (toxicity) OR (virological failure)) AND ((females) OR (males)) AND ((intolerance) OR (toxicity)) AND ((condom) OR (diaphragm with spermicide)) AND ((Depo) OR (IUD)))"}
{"candidate_id": "LLM01370", "doc_id": "NCT02510404_inc", "case_bucket": "or", "source_criterion": "1. Diagnosis of primary immunodeficiency with established plan to undergo myeloablative or non-myeloablative allogeneic hematopoietic stem cell transplant for treatment thereof or diagnosis of a form of primary immunodeficiency for which hematopoietic stem cell transplantation is not indicated. 2. Active infection with EBV, CMV, and/or Adenovirus, unable to be successfully controlled with standard therapy. 3. Steroids less than 0.5 mg/kg/day prednisone 4. Karnofsky/Lansky score of ≥ 50 5. ANC greater than 500/µL. 6. Bilirubin <2x, AST <3x, Serum creatinine <2x upper limit of normal, Hgb >8.0 7. Pulse oximetry of > 90% on room air 8. Negative pregnancy test (if female of childbearing potential) 9. Patient or parent/guardian capable of providing informed consent.", "candidate_expression": "((<2x) AND (<2x upper limit of normal) AND (<3x) AND (> 90%) AND (>8.0) AND (ANC) AND (AST) AND (Bilirubin) AND (Hgb) AND (Karnofsky/Lansky score) AND (Negative) AND (Patient or parent/guardian capable of providing informed consent) AND (Pulse oximetry on room air) AND (Serum creatinine) AND (Steroids) AND (childbearing potential) AND (female) AND (greater than 500/µL) AND (hematopoietic stem cell transplantation) AND (less than 0.5 mg/kg/day) AND (not indicated) AND (prednisone) AND (pregnancy test) AND (standard therapy) AND (unable to be controlled) AND (≥ 50) AND ((primary immunodeficiency)) AND ((allogeneic hematopoietic stem cell transplant myeloablative) OR (non-myeloablative allogeneic hematopoietic stem cell transplant)) AND ((Adenovirus) OR (CMV) OR (EBV)))"}
{"candidate_id": "LLM01371", "doc_id": "NCT03187379_exc", "case_bucket": "other", "source_criterion": "age <18 years previous history of roux-en-y gastric bypass patients undergoing other bariatric procedures pre-operative opioid analgesics", "candidate_expression": "((<18 years) AND (age) AND (bariatric procedures) AND (history) AND (opioid analgesics) AND (other) AND (pre-operative) AND (previous) AND (roux-en-y gastric bypass) AND (undergoing))"}
{"candidate_id": "LLM01372", "doc_id": "NCT03364036_exc", "case_bucket": "or", "source_criterion": "Previous exposure to drugs such as fingolimod, natalizumab, alemtuzumab, mitoxantrone and ocrelizumab. Positive hepatitis C or hepatitis B surface antigen test and/or hepatits B core antibody test for immunoglobulin G (IgG) and/or immunoglobulin M (IgM). Current or previous history of immune deficiency disorders including a positive human immunodeficiency virus (HIV) result. Currently receiving immunosuppressive or myelosuppressive therapy with, for example, monoclonal antibodies, methotrexate, cyclophosphamide, cyclosporine or azathioprine, or chronic use of corticosteroids. History of tuberculosis , presence of active tuberculosis, or latent tuberculosis Evidence or suspect of Progressive Multifocal Leukoencephalopathy (PML) in Magnetic Resonance Imaging (MRI). Active malignancy or history of malignancy. Other protocol defined exclusion criteria could apply.", "candidate_expression": "((Active) AND (Currently) AND (History) AND (Magnetic Resonance Imaging (MRI)) AND (Positive) AND (Previous) AND (Progressive Multifocal Leukoencephalopathy (PML)) AND (active) AND (chronic use) AND (drugs) AND (history) AND (human immunodeficiency virus (HIV)) AND (immune deficiency disorders) AND (latent) AND (positive) AND ((hepatitis B surface antigen test) OR (hepatitis C surface antigen test) OR (hepatits B core antibody test)) AND ((immunoglobulin G (IgG)) OR (immunoglobulin M (IgM))) AND ((Current) OR (previous history)) AND ((immunosuppressive therapy) OR (myelosuppressive therapy)) AND ((azathioprine) OR (corticosteroids) OR (cyclophosphamide) OR (cyclosporine) OR (methotrexate) OR (monoclonal antibodies)) AND ((tuberculosis)) AND ((Evidence) OR (suspect)) AND ((malignancy)) AND ((alemtuzumab) OR (fingolimod) OR (mitoxantrone) OR (natalizumab) OR (ocrelizumab)))"}
{"candidate_id": "LLM01373", "doc_id": "NCT02707874_exc", "case_bucket": "or", "source_criterion": "Patients who undergo iliac crest bone graft harvesting as part of their surgery Preexisting neurological deficits or peripheral neuropathy in the distribution of the sciatic nerve Local infection Contraindication to regional anesthesia e.g. bleeding diathesis, coagulopathy Chronic pain disorders History of use of over 30mg oxycodone or equivalent per day Allergy to local anesthetics History of significant psychiatric conditions that may affect patient assessment Pregnancy Inability to provide informed consent", "candidate_expression": "((Allergy) AND (Chronic pain) AND (Contraindication) AND (Inability to provide informed consent) AND (Local infection) AND (Pregnancy) AND (iliac crest bone graft harvesting) AND (local anesthetics) AND (regional anesthesia) AND ((oxycodone) OR (oxycodone equivalent)) AND ((neurological deficits) OR (peripheral neuropathy)) AND ((bleeding diathesis) OR (coagulopathy)))"}
{"candidate_id": "LLM01374", "doc_id": "NCT02958566_inc", "case_bucket": "or", "source_criterion": "Males or females above the age of 18 Patients undergoing laparoscopic or robotic colorectal resections", "candidate_expression": "((above the age of 18) AND (age) AND (colorectal resections) AND ((Males) OR (females)) AND ((laparoscopic) OR (robotic)))"}
{"candidate_id": "LLM01375", "doc_id": "NCT03216447_inc", "case_bucket": "other", "source_criterion": "Patient has been fully informed and has signed an IRB approved informed consent form within 7 days (Day 7-13) prior to POD 15 and is willing and able to follow study procedure Patient is a primary liver transplant recipient Patient is 20 to 70 years of age Patient should be clearly conscious, fully understand and able to answer questionnaire", "candidate_expression": "((Patient has been fully informed and has signed an IRB approved informed consent form within 7 days (Day 7-13) prior to POD 15 and is willing and able to follow study procedure) AND (Patient should be clearly conscious, fully understand and able to answer questionnaire) AND (age 20 to 70 years) AND (primary liver transplant) AND (recipient))"}
```
