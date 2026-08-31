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
{"candidate_id": "LLM06176", "doc_id": "NCT03363295_inc", "case_bucket": "other", "source_criterion": "Any patients that will be submitted to phacoemulsification surgery in the Hospital de Clinicas of State University of Campinas (BRAZIL) Patients over 18 years old Patients who are able to perform SD-OCT Patients who sign the consent form", "candidate_expression": "((Hospital de Clinicas of State University of Campinas (BRAZIL)) AND (Patients who sign the consent form) AND (SD-OCT) AND (able to perform) AND (old) AND (over 18 years) AND (phacoemulsification surgery) AND (will be submitted to))"}
{"candidate_id": "LLM06177", "doc_id": "NCT02726009_inc", "case_bucket": "other", "source_criterion": "Has given written informed consent before any study-related activity is performed Advanced hormone-dependent prostate cancer for which androgen deprivation therapy is indicated, and independently from this trial, Firmagon® is intended to be used for treatment Age greater than or equal to 18 years and less than 80 years Advanced hormone-dependent prostate cancer without any other clinically significant disorder Easten Cooperative Oncology Group score = 2 PSA = 2 ng/mL at screening Life expectancy of at least 12 months as per the investigator's judgement", "candidate_expression": "((Age greater than or equal to 18 years and less than 80 years) AND (Easten Cooperative Oncology Group score = 2) AND (Firmagon intended) AND (Has given written informed consent before any study-related activity is performed) AND (Life expectancy at least 12 months) AND (PSA = 2 ng/mL) AND (androgen deprivation therapy) AND (prostate cancer Advanced hormone-dependent))"}
{"candidate_id": "LLM06178", "doc_id": "NCT00812344_exc", "case_bucket": "or", "source_criterion": "Significant illness, trauma or surgical procedures. Clinically significant laboratory abnormalities. Clinically significant medical history", "candidate_expression": "((Clinically significant) AND (Significant) AND (illness) AND (laboratory) AND (laboratory abnormalities Clinically significant) AND (medical history Clinically significant) AND (surgical procedures) AND (trauma))"}
{"candidate_id": "LLM06179", "doc_id": "NCT02243553_exc", "case_bucket": "or", "source_criterion": "1. History or presence of allergy to the study drugs or their components or drugs of their class, or a history of drug or other allergy that, in the opinion of the physician responsible, contraindicates their participation 2. Any finding of the medical examination (including blood pressure, pulse rate and electrocardiogram) deviating from normal and of clinical relevance 3. History or diagnosis of any significant medical conditions: Including but not limited to gastrointestinal, hepatic, renal, respiratory, cardiovascular, metabolic, immunologic, hematological, psychiatric, neurological, oncological or hormonal disorders 4. Known elevated liver enzymes in past clinical trials with any compound (experimental or marketed) 5. Clinically relevant laboratory abnormalities (e.g. Hgb<11g/dL, Hct<30g/dL, total cholesterol >240mg/dL, triglycerides >500mg/dL, fasting glucose >130mg/dL, liver function tests >2.5x upper limit of normal, baseline international normalized ratio >1.2) 6. History of evidence of clinically significant hepatic, cardiac, pulmonary, endocrine, immunological, gastrointestinal, hematological, vascular or collagen disease 7. History of alcohol abuse or use of any illicit drugs 8. Unable to abstain from more than one beer or alcohol equivalent per day for the duration of the study 9. Use of tobacco products and/or history of smoking within the past 2 months 10. Pregnant or breast feeding 11. Sexually active women of childbearing age who do not use an acceptable barrier method of birth control 12. Hypersensitivity to caffeine, warfarin, vitamin K, omeprazole, dextromethorphan, midazolam, tipranavir, ritonavir or their excipients 13. Concomitant treatment with other experimental compounds 14. Concomitant administration of any prescription or over the counter medications known to alter P450 enzyme or P-gp activity 15. Concomitant administration of any prescription or over the counter medications known to be highly dependent on P450 or P-gp for clearance for which elevated plasma concentrations are known to be associated with serious toxicity 16. Concomitant administration of any food product known to alter P450 enzyme or P-gp activity such as grapefruit juice, Seville oranges 17. Concomitant administration of any drug that could affect bleeding (e.g., aspirin, clopidogrel, ticlopidine, warfarin, heparin, low-molecular weight heparin) 18. Concomitant administration of oral contraceptives (may be included with 7-day washout period) 19. Concomitant administration of any herbal medications 20. Inadequate venous access 21. Renal or hepatic insufficiency 22. Clinically unacceptable result at the screening physical examination 23. Use of investigational medications within 30 days before study entry 24. HIV-positive 25. Body Mass Index (BMI) > 30 kg/m²", "candidate_expression": "((Any finding of the medical examination (including blood pressure, pulse rate and electrocardiogram) deviating from normal and of clinical relevance) AND (Body Mass Index (BMI) > 30 kg/m²) AND (Clinically relevant) AND (Clinically unacceptable) AND (Clinically unacceptable result Clinically unacceptable at the screening physical examination) AND (HIV positive) AND (History or presence of allergy to the study drugs or their components or drugs of their class, or a history of drug or other allergy that, in the opinion of the physician responsible, contraindicates their participation) AND (Hypersensitivity) AND (Sexually active) AND (age childbearing) AND (allergy) AND (clinically significant) AND (drug that could affect bleeding) AND (experimental compounds Concomitant) AND (herbal medications Concomitant) AND (investigational medications within 30 days before study entry) AND (laboratory abnormalities Clinically relevant) AND (liver enzymes elevated) AND (medical conditions significant) AND (oral contraceptives Concomitant) AND (physical examination) AND (plasma concentrations elevated) AND (significant) AND (study drugs) AND (toxicity serious) AND (venous access Inadequate) AND (women) AND NOT (barrier method of birth control acceptable) AND ((Pregnant) OR (breast feeding)) AND ((smoking history within the past 2 months) OR (tobacco products)) AND ((alcohol abuse) OR (use of illicit drugs)) AND ((cardiac disease) OR (collagen disease) OR (endocrine disease) OR (gastrointestinal disease) OR (hematological disease) OR (hepatic disease) OR (immunological disease) OR (pulmonary disease) OR (vascular disease)) AND ((Hct <30g/dL) OR (Hgb <11g/dL) OR (fasting glucose >130mg/dL) OR (international normalized ratio baseline >1.2) OR (liver function tests >2.5x upper limit of normal) OR (total cholesterol >240mg/dL) OR (triglycerides >500mg/dL)) AND ((cardiovascular disorders) OR (gastrointestinal disorders) OR (hematological disorders) OR (hepatic disorders) OR (hormonal disorders) OR (immunologic disorders) OR (metabolic disorders) OR (neurological disorders) OR (oncological disorders) OR (psychiatric disorders) OR (renal disorders) OR (respiratory disorders)) AND ((Renal insufficiency) OR (hepatic insufficiency)) AND ((aspirin) OR (clopidogrel) OR (heparin) OR (low-molecular weight heparin) OR (ticlopidine) OR (warfarin)) AND ((food product known to alter P-gp activity) OR (food product known to alter P450 enzyme activity)) AND ((Seville oranges) OR (grapefruit juice)) AND ((medications known to be highly dependent on P-gp for clearance) OR (medications known to be highly dependent on P450 for clearance)) AND ((medications known to alter P-gp activity) OR (medications known to alter P450 enzyme activity)) AND ((caffeine) OR (dextromethorphan) OR (midazolam) OR (omeprazole) OR (ritonavir) OR (tipranavir) OR (vitamin K) OR (warfarin)))"}
{"candidate_id": "LLM06180", "doc_id": "NCT03623789_inc", "case_bucket": "or", "source_criterion": "Patients with osteoarthritis of the hip secondary to degeneration, inflammatory arthritis, gouty arthritis, acetabular dysplasia or osteonecrosis of the femoral head, and undergoing primary unilateral minimally invasive THA Age > 18 years and < 90 years Failure of medical treatment or rehabilitation. Hemoglobin > 11g/dl, No use of non-steroid anti-inflammatory agent one week before operation", "candidate_expression": "((< 90 years) AND (> 11g/dl) AND (> 18 years) AND (Age) AND (Failure) AND (Hemoglobin) AND (No) AND (degeneration) AND (femoral head) AND (hip) AND (non-steroid anti-inflammatory agent) AND (one week before operation) AND (operation) AND (primary) AND (secondary to degeneration) AND (undergoing) AND (unilateral) AND ((medical treatment) OR (rehabilitation)) AND ((gouty arthritis) OR (inflammatory arthritis) OR (minimally invasive THA) OR (osteoarthritis)) AND ((acetabular dysplasia) OR (osteonecrosis)))"}
{"candidate_id": "LLM06181", "doc_id": "NCT00965900_exc", "case_bucket": "or", "source_criterion": "Patients with systolic blood pressure <100 mmHg or basal heart rate <60/min Portal vein thrombosis Uncontrolled ascites or hepatic encephalopathy Severe coagulation disorder: prothrombin time <40% (or INR >1.7) or platelet count <30,000/mm3 Medium or large sized gastric or duodenal varices Coexisting malignancy Severe cardiovascular disorder, renal failure, peritonitis, sepsis Severe erosive esophagitis, severe esophageal stricture, active gastric or duodenal ulcer Contraindication to beta-blocker Pregnancy Refusal to give consent to participate in the trial", "candidate_expression": "((<100 mmHg) AND (<30,000/mm3) AND (<40%) AND (<60/min) AND (>1.7) AND (Coexisting) AND (Contraindication) AND (Portal vein thrombosis) AND (Pregnancy) AND (Refusal to give consent to participate in the trial) AND (Severe) AND (Uncontrolled) AND (active) AND (basal) AND (beta-blocker) AND (coagulation disorder) AND (malignancy) AND (severe) AND ((INR) OR (platelet count) OR (prothrombin time)) AND ((duodenal varices) OR (gastric c)) AND ((Medium) OR (large)) AND ((cardiovascular disorder) OR (peritonitis) OR (renal failure) OR (sepsis)) AND ((heart rate) OR (systolic blood pressure)) AND ((erosive esophagitis) OR (esophageal stricture)) AND ((duodenal ulcer) OR (gastric ulcer)) AND ((ascites) OR (hepatic encephalopathy)))"}
{"candidate_id": "LLM06182", "doc_id": "NCT02273791_inc", "case_bucket": "other", "source_criterion": "Women with PCOS as defined by the Rotterdam criteria. Presence of at least 2 cryopreserved good quality cleavage-stage embryo (good quality cleavage-stage embryos display stage-specific cell division, have blastomeres of fairly equal size with few to no cytoplasmic fragments).", "candidate_expression": "((PCOS) AND (Rotterdam criteria) AND (Women) AND (cleavage-stage embryo at least 2 cryopreserved good))"}
{"candidate_id": "LLM06183", "doc_id": "NCT03140488_inc", "case_bucket": "other", "source_criterion": "Singleton pregnancy = 37 weeks gestation Patient presented for induction of labor who is determined to be a candidate for oxytocin Cephalic presentation Reassuring fetal health assessment (no abnormal findings in fetal assessment, see below) Meeting one of the following BMI category:", "candidate_expression": "((Cephalic presentation) AND (Singleton pregnancy) AND (candidate for oxytocin) AND (fetal assessment) AND (fetal health assessment Reassuring) AND (gestation = 37 weeks) AND (induction of labor presented for) AND (oxytocin) AND NOT (abnormal findings))"}
{"candidate_id": "LLM06184", "doc_id": "NCT02721017_exc", "case_bucket": "or", "source_criterion": "age less than 13 years at time of procedure use of pain medication prior to procedure pectus carinatum, Poland's syndrome, or any chest wall anomaly other than pectus excavatum previous repair of pectus excavatum by any technique previous thoracic surgery congenital heart disease bleeding dyscrasia major anesthetic risk factors or history of previous problem with anesthesia pregnancy inability to communicate in English", "candidate_expression": "((Poland's syndrome) AND (age less than 13 years at time of procedure) AND (anesthetic risk factors major) AND (bleeding dyscrasia) AND (chest wall anomaly) AND (congenital heart disease) AND (inability to communicate in English) AND (pain medication prior to procedure) AND (pectus carinatum) AND (pregnancy) AND (problem with anesthesia previous) AND (repair of pectus excavatum previous) AND (thoracic surgery previous) AND NOT (pectus excavatum))"}
{"candidate_id": "LLM06185", "doc_id": "NCT02851303_exc", "case_bucket": "other", "source_criterion": "Born prior to 34 weeks Neonatal intensive care unit admission Serious medical comorbidities Primary substance exposure in-utero was buprenorphine, or was not opioids", "candidate_expression": "((Born) AND (Neonatal intensive care unit) AND (Serious) AND (buprenorphine) AND (in-utero) AND (medical comorbidities) AND (not) AND (opioids) AND (prior to 34 weeks) AND (substance exposure))"}
{"candidate_id": "LLM06186", "doc_id": "NCT03067740_exc", "case_bucket": "or", "source_criterion": "The diagnosis of developmental delay, attention deficit disorder, chronic pain, psychiatric illness, previous open abdominal surgery, the presence of a gastrostomy, ventricular-peritoneal shunt or other abdominal prosthesis, immunosuppression, and those allergic to any of the medications.", "candidate_expression": "((any of the medications) AND (previous) AND ((abdominal prosthesis) OR (allergic) OR (attention deficit disorder) OR (chronic pain) OR (developmental delay) OR (gastrostomy) OR (immunosuppression) OR (open abdominal surgery) OR (psychiatric illness) OR (ventricular-peritoneal shunt)))"}
{"candidate_id": "LLM06187", "doc_id": "NCT00586898_inc", "case_bucket": "or", "source_criterion": "-Patients residing in the following clinical states wit! be considered: A. Rising PSA: Patients with a history of localized disease who have undergone definitive radiation or surgery. These patients must demonstrate progression of disease biochemically as outlined below. Patients in this group may not have radiographically evident disease. B. Non-castrate metastatic: Patients must present with radiographic evidence of metastatic disease at the time of diagnosis or after treatment for localized disease. These patients must show newly detected disease or progressing disease in bone or in soft tissue. Biochemical progression is defined as: minimum no. of determinations: 3 Interval: >2 weeks Minimal Baseline PSA value (ng/ml): 2 Minimal % increase in range of values: 50% Diagnosis of prostate adenocarcinoma histologically confirmed at MSKCC. Patient must have level of serum testosterone above the lower limit of normal. Karnofskcy performance status (KPS) >_70%. Patients must have adequate organ function as defined by the following laboratory criteria: WBC >_3500/mm3, platelet count >_100,000/mm3. Bilirubin <2.0 mg/dl or SGOT <3.0 X the upper limit of normal. Creatinine <_1.6 mg/dl or creatinine clearance >_60 cc/min. Prior hormonal therapy is allowed as: 1. Neoadjuvant treatment prior to radiation therapy or radical prostatectomy, provided that the total duration of exposure does not exceed 10 months. 2. One cycle of intermittent therapy up to a maximum exposure of 10 months. Patients must be at least 18 years of age. Patients must have signed an informed consent document stating that they understand the investigational nature of the proposed treatment", "candidate_expression": "((Interval >2 weeks) AND (Karnofskcy performance status (KPS) >_70%) AND (Minimal % increase in range of values 50%) AND (Minimal Baseline PSA value (ng/ml): 2) AND (Neoadjuvant treatment prior to radiation therapy or radical prostatectomy) AND (PSA Rising) AND (WBC >_3500/mm3) AND (adequate organ function) AND (age at least 18 years) AND (disease radiographically evident Non-castrate metastatic) AND (histologically confirmed) AND (hormonal therapy Prior is allowed) AND (intermittent therapy One cycle) AND (level of serum testosterone above the lower limit of normal) AND (localized disease) AND (localized disease history of) AND (maximum exposure 10 months) AND (metastatic disease) AND (minimum no. of determinations 3) AND (organ function adequate) AND (platelet count >_100,000/mm3) AND (progression of disease biochemically) AND (prostate adenocarcinoma histologically confirmed) AND (radiographic radiographic evidence) AND (signed an informed consent document) AND (total duration of exposure does not exceed 10 months) AND (treatment treatment for localized disease) AND ((after treatment for localized disease) OR (at the time of diagnosis the time of diagnosis)) AND ((disease in bone) OR (disease in soft tissue) OR (progressing disease in bone Biochemical progression) OR (progressing disease in soft tissue Biochemical progression)) AND ((Bilirubin <2.0 mg/dl) OR (SGOT <3.0 X the upper limit of normal)) AND ((Creatinine <_1.6 mg/dl) OR (creatinine clearance >_60 cc/min)) AND ((radiation) OR (surgery)) AND ((radiation therapy) OR (radical prostatectomy)))"}
{"candidate_id": "LLM06188", "doc_id": "NCT02939872_exc", "case_bucket": "or", "source_criterion": "Contraindication to antiplatelet therapy Need to continue clopidogrel due to stroke, peripheral disease, significant carotid disease or recent acute coronary syndrome Major bleeding history or bleeding diathesis Pregnancy", "candidate_expression": "((Contraindication) AND (Pregnancy) AND (antiplatelet therapy) AND (clopidogrel continue) AND ((acute coronary syndrome recent) OR (carotid disease significant) OR (peripheral disease) OR (stroke)) AND ((bleeding Major history) OR (bleeding diathesis)))"}
{"candidate_id": "LLM06189", "doc_id": "NCT02734173_inc", "case_bucket": "other", "source_criterion": "HCV RNA evidence of HCV infection Documented history of chronic HCV RNA infection with Genotype 1 Able to provide informed consent Available for ongoing follow-up if required", "candidate_expression": "((Able to provide informed consent) AND (Available for ongoing follow-up if required) AND (HCV RNA) AND (HCV infection) AND (chronic HCV infection Genotype 1))"}
{"candidate_id": "LLM06190", "doc_id": "NCT02627560_inc", "case_bucket": "other", "source_criterion": "breast cancer undergoing unilateral mastectomy with or without axillary node dissection received adequate oral and written information about the study and signed an informed-consent form", "candidate_expression": "((axillary node dissection) AND (breast cancer) AND (received adequate oral and written information about the study and signed an informed-consent form) AND (unilateral mastectomy undergoing))"}
{"candidate_id": "LLM06191", "doc_id": "NCT03338855_inc", "case_bucket": "or", "source_criterion": "Patients are able to provide signed and dated written informed consent prior to any study specific procedures. Women are post-menopausal (defined as at least 1 year post cessation of menses) and aged = 45 and = 70 years. Males are aged = 40 years and = 70 years. Patients should have suitable veins for cannulation or repeated venipuncture. Patients are diagnosed with T2DM for at least the last 6 months. Patients are on no other anti-diabetic drug treatment, or on stable maximum 3000 mg daily dose metformin treatment and/or on stable dose of a DPPIV inhibitor treatment for at least the last 3 months5. HbA1c levels =6.0% (=42 mmol/mol) and =9.0% (75 mmol/mol). Have a body mass index (BMI) = 35 kg/m2.", "candidate_expression": "((DPPIV inhibitor stable dose for at least the last 3 months) AND (HbA1c levels =6.0% =42 mmol/mol =9.0% 75 mmol/mol) AND (Males) AND (Patients are able to provide signed and dated written informed consent prior to any study specific procedures.) AND (T2DM for at least the last 6 months) AND (Women) AND (aged = 40 years and = 70 years) AND (aged = 45 and = 70 years cessation of menses) AND (body mass index (BMI) = 35 kg/m2) AND (metformin maximum 3000 mg daily dose) AND (post-menopausal as at least 1 year post cessation of menses) AND NOT (anti-diabetic drug treatment other))"}
{"candidate_id": "LLM06192", "doc_id": "NCT03296488_inc", "case_bucket": "or", "source_criterion": "Male or female who is among 20 to 80 years of age at screening. Scheduled to electively undergo open-laparotomy. American Society of Anesthesiology Physical Class 1-3. Ability and willingness to provide informed consent", "candidate_expression": "((1-3) AND (20 to 80 years) AND (Ability and willingness to provide informed consent) AND (American Society of Anesthesiology Physical Class) AND (Male) AND (Scheduled) AND (age) AND (at screening) AND (electively) AND (female) AND (open-laparotomy))"}
{"candidate_id": "LLM06193", "doc_id": "NCT01768195_exc", "case_bucket": "or", "source_criterion": "younger than 18 years old HBsAg negative at baseline pregnant or lactating women", "candidate_expression": "((HBsAg negative at baseline) AND (old younger than 18 years) AND (women) AND ((lactating) OR (pregnant)))"}
{"candidate_id": "LLM06194", "doc_id": "NCT03132259_exc", "case_bucket": "or", "source_criterion": "GCS less than 15 Preoperative Heart Rate less than 50 beat/min No Beta-Blockers Pregnant patients Take any Alpha-Methyldopa, Clonodine, Other Alpha-2 Adrenergic Agonist Hemodynamic unstable Systolic BP more than 160mmHg CAD Renal insuffuciency Allergy in dexmedethomidine and opioid BMI more than 30 Denied consent", "candidate_expression": "((Allergy) AND (Alpha-2 Adrenergic Agonist) AND (Alpha-Methyldopa) AND (BMI) AND (Beta-Blockers) AND (CAD) AND (Clonodine) AND (Denied consent) AND (GCS) AND (Hemodynamic unstable) AND (No) AND (Other) AND (Pregnant) AND (Preoperative Heart Rate) AND (Renal insuffuciency) AND (Systolic BP) AND (dexmedethomidine) AND (less than 15) AND (less than 50 beat/min) AND (more than 160mmHg) AND (more than 30) AND (opioid))"}
{"candidate_id": "LLM06195", "doc_id": "NCT03036462_exc", "case_bucket": "or", "source_criterion": "Hypersensitivity to the active substance, to FCM or any of its excipients Known serious hypersensitivity to other parenteral iron products Anaemia not attributed to iron deficiency, e.g. other microcytic anaemia Evidence of iron overload or disturbances in the utilisation of iron", "candidate_expression": "((Anaemia) AND (Hypersensitivity) AND (attributed to) AND (hypersensitivity) AND (iron) AND (iron deficiency) AND (microcytic anaemia) AND (not) AND (other) AND (parenteral iron products) AND (serious) AND ((disturbances in the utilisation of iron) OR (iron overload)) AND ((FCM) OR (active substance) OR (excipients)))"}
{"candidate_id": "LLM06196", "doc_id": "NCT01352598_exc", "case_bucket": "other", "source_criterion": "NA", "candidate_expression": "(EMPTY)"}
{"candidate_id": "LLM06197", "doc_id": "NCT03208465_inc", "case_bucket": "or", "source_criterion": "Men or women at least 19 years of age Type 2 diabetes mellitus Stable coronary artery disease Global myocardial perfusion reserve (MPR) index < 2.5 The patient or guardian agrees to the study protocol and the schedule of clinical and dynamic SPECT follow-up, and provides informed, written consent, as approved by the appropriate Institutional Review Board/Ethical Committee of the respective clinical site.", "candidate_expression": "((Global myocardial perfusion reserve (MPR) index < 2.5) AND (Men) AND (Type 2 diabetes mellitus) AND (age at least 19 years) AND (coronary artery disease Stable) AND (informed, written consent) AND (women))"}
{"candidate_id": "LLM06198", "doc_id": "NCT03126214_inc", "case_bucket": "or", "source_criterion": "Age = 65 years with one additional stroke risk factor (hypertension, diabetes, heart failure history of or left ventricular ejection fraction <0.40), previous stroke or transient ischemic attack). Atrial fibrillation and not on oral anticoagulation (OAC) therapy but eligible Atrial fibrillation on sub-optimal OAC", "candidate_expression": "((Age = 65 years) AND (Atrial fibrillation) AND (OAC sub-optimal) AND (not) AND (oral anticoagulation (OAC) therapy) AND (risk factor) AND (stroke) AND ((stroke) OR (transient ischemic attack)) AND ((diabetes) OR (heart failure) OR (hypertension) OR (left ventricular ejection fraction history <0.40)))"}
{"candidate_id": "LLM06199", "doc_id": "NCT03299517_inc", "case_bucket": "or", "source_criterion": "Adult men and women> 18 years old Presence of sustained ventricular tachycardia with HR> 120 bpm Systolic blood pressure> 90 mmHg No signs of poor peripheral perfusion Absence of dyspnea Absence of severe angina Signed consent form", "candidate_expression": "((Adult) AND (HR > 120 bpm) AND (Signed consent form) AND (Systolic blood pressure > 90 mmHg) AND (old > 18 years old) AND (ventricular tachycardia sustained) AND NOT (poor peripheral perfusion signs of) AND NOT (dyspnea) AND NOT (angina severe) AND ((men) OR (women)))"}
{"candidate_id": "LLM06200", "doc_id": "NCT02821819_inc", "case_bucket": "other", "source_criterion": "Premenopausal women 18-35 years old FSH levels < 10 mIU/ml AFC> 10 Regular cycles BMI < 28 Signed informed consent", "candidate_expression": "((18-35 years) AND (< 10 mIU/ml) AND (< 28) AND (> 10) AND (AFC) AND (BMI) AND (FSH levels) AND (Premenopausal) AND (Regular cycles) AND (Signed informed consent) AND (old) AND (women))"}
```
