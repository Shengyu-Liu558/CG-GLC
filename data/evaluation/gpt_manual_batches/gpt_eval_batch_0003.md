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
{"candidate_id": "LLM00051", "doc_id": "NCT03338855_inc", "case_bucket": "or", "source_criterion": "Patients are able to provide signed and dated written informed consent prior to any study specific procedures. Women are post-menopausal (defined as at least 1 year post cessation of menses) and aged = 45 and = 70 years. Males are aged = 40 years and = 70 years. Patients should have suitable veins for cannulation or repeated venipuncture. Patients are diagnosed with T2DM for at least the last 6 months. Patients are on no other anti-diabetic drug treatment, or on stable maximum 3000 mg daily dose metformin treatment and/or on stable dose of a DPPIV inhibitor treatment for at least the last 3 months5. HbA1c levels =6.0% (=42 mmol/mol) and =9.0% (75 mmol/mol). Have a body mass index (BMI) = 35 kg/m2.", "candidate_expression": "((HbA1c levels =6.0% =42 mmol/mol =9.0% 75 mmol/mol) AND (Patients are able to provide signed and dated written informed consent prior to any study specific procedures.) AND (T2DM for at least the last 6 months) AND (aged = 40 years and = 70 years) AND (aged = 45 and = 70 years cessation of menses) AND (body mass index (BMI) = 35 kg/m2) AND (post-menopausal as at least 1 year post cessation of menses) AND ((DPPIV inhibitor stable dose for at least the last 3 months) OR (metformin maximum 3000 mg daily dose) OR NOT (anti-diabetic drug treatment other)) AND ((Males) OR (Women)))"}
{"candidate_id": "LLM00052", "doc_id": "NCT02384850_inc", "case_bucket": "or", "source_criterion": "1. Patients with histologically confirmed diagnosis of colorectal cancer presenting with unresectable stage IV (UICC) disease (primary tumor may be present) 2. Patients who are feasible for treatment with FOLFOX (prior adjuvant or palliative treatment is allowed) 3. ECOG Performance status ≤ 1 4. Life expectancy > 3 months 5. Age ≥18 years 6. Haematologic function as follows (5% deviation allowed): ANC ≥ 1.5 x 109/L platelets ≥ 100 x109/L hemoglobin ≥ 9 g/dl or 5.59 mmol/l 7. Adequate liver function as follows (10% deviation allowed) serum alanine transaminase (ALT) ≤ 2.5 x ULN (in case of liver metastases < 5 x ULN) total bilirubin ≤ 1.5 x ULN (patients with Gilbert's syndrome total bilirubin ≤2.5 x ULN) 8. Adequate renal function as follows (10% deviation allowed) · creatinine ≤ 1.5 x ULN 9. Signed written informed consent 10. Women of child-bearing potential must have a negative pregnancy test", "candidate_expression": "((< 5 x ULN) AND (> 3 months) AND (ANC) AND (Adequate) AND (Age) AND (ECOG Performance status) AND (FOLFOX) AND (Gilbert's syndrome) AND (IV) AND (Life expectancy) AND (Signed written informed consent) AND (Women) AND (adjuvant treatment) AND (child-bearing potential) AND (colorectal cancer) AND (confirmed) AND (creatinine) AND (disease) AND (hemoglobin) AND (histologically) AND (liver function) AND (liver metastases) AND (negative) AND (palliative treatment) AND (platelets) AND (pregnancy test) AND (renal function) AND (serum alanine transaminase (ALT)) AND (stage IV (UICC)) AND (total bilirubin) AND (unresectable) AND (≤ 1) AND (≤ 1.5 x ULN) AND (≤ 2.5 x ULN) AND (≤2.5 x ULN) AND (≥ 1.5 x 109/L) AND (≥ 100 x109/L) AND (≥ 5.59 mmol/l) AND (≥ 9 g/dl) AND (≥18 years))"}
{"candidate_id": "LLM00053", "doc_id": "NCT02312076_inc", "case_bucket": "other", "source_criterion": "Women subjected to ICSI through controlled ovarian hyperstimulation (COH) with pituitary downregulation by GnRHa.", "candidate_expression": "((ICSI) AND (Women) AND (controlled ovarian hyperstimulation (COH)) AND (pituitary downregulation by GnRHa))"}
{"candidate_id": "LLM00054", "doc_id": "NCT02600000_exc", "case_bucket": "or", "source_criterion": "Unstable angina; Myocardial infarction and heart surgery up to three months before the survey; Chronic respiratory diseases; Hemodynamic instability; Trauma recent face, nausea and vomiting. Orthopedic and neurological diseases that may preclude the achievement of the cardiopulmonary test and Cardiac Rehabilitation exercises; Psychological and / or cognitive impairments that restrict them to respond to questionnaires;", "candidate_expression": "((Chronic respiratory diseases) AND (Hemodynamic instability) AND (Unstable angina) AND (preclude the achievement of the cardiopulmonary test and Cardiac Rehabilitation exercises) AND (restrict them to respond to questionnaires) AND (up to three months before the survey) AND ((Orthopedic) OR (neurological diseases)) AND ((Psychological impairments) OR (cognitive impairments)) AND ((Myocardial infarction) OR (heart surgery)) AND ((Trauma) OR (nausea) OR (vomiting)))"}
{"candidate_id": "LLM00055", "doc_id": "NCT02802644_exc", "case_bucket": "or", "source_criterion": "Left main disease Known hypersensitivity or contraindication to any of the following medications: Heparin, aspirin, clopidogrel, sirolimus, siptagliptin and statin Congestive heart failure (patients with LVEF <30% or cardiogenic shock) Uncontrolled myocardial ischemia (repeated chest pain or dyspnea after revascularization) Uncontrolled ventricular arrhythmia History of malignancy with chemotherapy Serious hematologic disease (e.g. CML, MDS) Current infectious disease needs antibiotics therapy Creatinine level >1.5 mg/dL or dependence on dialysis Other severe concurrent illness (e.g. active infection, malignancy). Life expectancy of less than one year Pregnancy or women with potential childbearing Type I DM Treatment with insulin History of pancreatitis Who cannot read the informed consent form (e.g. illiteracy, foreigner)", "candidate_expression": "((<30%) AND (>1.5 mg/dL) AND (CML) AND (Congestive heart failure) AND (Creatinine level) AND (Heparin) AND (LVEF) AND (Left main disease) AND (MDS) AND (Pregnancy or women with potential childbearing) AND (Serious) AND (Type I DM) AND (Uncontrolled) AND (Who cannot read the informed consent form (e.g. illiteracy, foreigner)) AND (active infection) AND (after revascularization) AND (antibiotics) AND (aspirin) AND (cardiogenic shock) AND (chemotherapy) AND (chest pain) AND (clopidogrel) AND (concurrent) AND (contraindication) AND (dialysis) AND (dyspnea) AND (hematologic disease) AND (hypersensitivity) AND (ife expectancy) AND (illness) AND (infectious disease) AND (insulin) AND (less than one year) AND (malignancy) AND (myocardial ischemia) AND (pancreatitis) AND (repeated) AND (revascularization) AND (severe) AND (siptagliptin) AND (sirolimus) AND (statin) AND (ventricular arrhythmia))"}
{"candidate_id": "LLM00056", "doc_id": "NCT03372265_exc", "case_bucket": "or", "source_criterion": "Allergy to LA Infection in or near insertion site of the peripheral nerve catheter Anatomical abnormalities preventing successful peripheral catheter insertion Habitual use of opioids Pregnancy or breastfeeding (disproved by a negative pregnancy test before trial inclusion)", "candidate_expression": "((Allergy) AND (Anatomical abnormalities) AND (LA in insertion site near insertion site) AND (Pregnancy) AND (breastfeeding) AND (insertion preventing successful) AND (opioids Habitual use) AND (peripheral catheter) AND (peripheral nerve catheter) AND (preventing) AND NOT (pregnancy test negative before trial inclusion))"}
{"candidate_id": "LLM00057", "doc_id": "NCT02789111_exc", "case_bucket": "other", "source_criterion": "More than three doses of any opioid within one week of surgery Pregnancy Prisoners Unable to provide consent Emergency surgery Chronic kidney disease stage 5 (GFR < 15 ml/min) Severe hepatic impairment Recent myocardial infarction (within the last 3 months)", "candidate_expression": "((Chronic kidney disease stage 5) AND (Emergency surgery) AND (GFR < 15 ml/min)) AND (Pregnancy) AND (Prisoners) AND (Unable to provide consent) AND (hepatic impairment Severe) AND (myocardial infarction the last 3 months) AND (opioid More than three doses within one week of surgery))"}
{"candidate_id": "LLM00058", "doc_id": "NCT02908919_exc", "case_bucket": "or", "source_criterion": "ileus known or suspected bowel obstruction active bowel inflammation pregnancy any presence of serious medical conditions ( esp. cardiac, renal, liver diseases) history of prior colonic or rectal surgery inability to obtain valid data from", "candidate_expression": "((bowel inflammation active) AND (bowel obstruction) AND (ileus) AND (pregnancy) AND (serious medical conditions) AND ((cardiac diseases) OR (liver diseases) OR (renal diseases)) AND ((colonic surgery) OR (rectal surgery)) AND ((known) OR (suspected)))"}
{"candidate_id": "LLM00059", "doc_id": "NCT02687724_inc", "case_bucket": "or", "source_criterion": "Patients = 18 years of age Subjects must be able and willing to give written informed consent and to comply with the requirements of this study protocol Established diagnosis of UC and moderate-to-severe disease activity, defined as a Mayo score of 6-12, with an endoscopic subscore =2. Patients had an inadequate response to, or had failed to tolerate, 1 or more of the following conventional therapies: oral 5-aminosalicylates, oral corticosteroids, azathioprine (AZA), and/or 6-mercaptopurine (6MP); or corticosteroid dependent (ie, an inability to taper corticosteroids without recurrence of UC symptoms). Patients concurrently treated with oral 5-aminosalicylates or corticosteroids were to receive a stable dose for at least 2 weeks before baseline, and patients receiving AZA and/or 6MP were to receive a stable dose for at least 4 weeks before baseline. Patients were required to maintain stable doses of their concomitant UC medications during the study. Female subjects of child bearing potential must be willing to ensure that they or their partner use effective contraception during the study and for 6 months thereafter OR Surgical sterilized female patients with documentation of prior hysterectomy, tubal ligation or complete bilateral oophorectomy OR Postmenopausal women with postmenopausal defined as permanent cessation >1 year of previously occurring menses. Female subjects' serum pregnancy test performed at the screening visit and urine pregnancy test performed at the baseline visit must be negative. Subjects have following investigations within 1 month prior to enrolment. Routine bloods including U&E, FBC, LFTs, inflammatory markers (CRP) and albumin will be measured. Medical history, concomitant medications Intradermal reaction to Tuberculin (PPD skin test) or Mycobacterium tuberculosis antigenspecific interferon-gamma release assay (IGRA) TB screening: chest X-Ray unless performed in the last 6 months Stool examination for enteric pathogens including Clostridium difficile Inclusion/exclusion criteria Informed consent Mayo score (including sigmoidoscopy unless performed in previous 3 months) Patient's weight and height and abdominal circumference", "candidate_expression": "((1 or more) AND (6-12) AND (= 18 years) AND (=2) AND (Female subjects of child bearing potential must be willing to ensure that they or their partner use effective contraception during the study and for 6 months thereafter OR) AND (Female subjects' serum pregnancy test performed at the screening visit and urine pregnancy test performed at the baseline visit must be negative.) AND (Mayo score) AND (Postmenopausal women with postmenopausal defined as permanent cessation >1 year of previously occurring menses.) AND (Routine bloods) AND (Stool examination) AND (Surgical sterilized female patients with documentation of prior hysterectomy, tubal ligation or complete bilateral oophorectomy OR) AND (TB screening) AND (UC) AND (abdominal circumference) AND (age) AND (chest X-Ray) AND (corticosteroid) AND (dependent) AND (endoscopic subscore) AND (for at least 2 weeks before baseline) AND (for at least 4 weeks before baseline) AND (for enteric pathogens including Clostridium difficile) AND (height) AND (moderate-to-severe) AND (sigmoidoscopy) AND (stable dose) AND (treated) AND (weight) AND (within 1 month prior to enrolment) AND ((failed to tolerate) OR (inadequate response)) AND ((6-mercaptopurine (6MP)) OR (azathioprine (AZA)) OR (oral 5-aminosalicylates) OR (oral corticosteroids)) AND ((corticosteroids) OR (oral 5-aminosalicylates)) AND ((6MP) OR (AZA)) AND ((FBC) OR (LFTs) OR (U&E) OR (albumin) OR (inflammatory markers (CRP))) AND ((Intradermal reaction to Tuberculin (PPD skin test)) OR (Mycobacterium tuberculosis antigenspecific interferon-gamma release assay (IGRA))))"}
{"candidate_id": "LLM00060", "doc_id": "NCT02804646_inc", "case_bucket": "or", "source_criterion": "1) histologically confirmed (patients not receiving a single sputum cytology diagnosis) non-small cell lung cancer patients,with wild-type EGFR and ALK-negative; 2) According to IASLC2009 new TNM staging of lung cancer stage <U+2162>B or <U+2163>, previously untreated or relapsed after 1 year of lung cancer resection; 3) have at least one evaluable lesions,according to version 1.1 of the standard in accordance with a judgment RECIST(longest diameter on a spiral CT at least 10mm,on a regular CT longest diameter at least 20mm); 4) Male or female, aged 18 to 75 years; 5) ECOG PS 0 or 1; 6) expected survival at least 3 months; 7) adequate hematological function: absolute neutrophil count (ANC) at least 2×10^9/L and platelet count at least 100×10^9/L and hemoglobin at least 9 g/dL; 8) adequate liver function: total bilirubin less than upper limit of normal (ULN); AST and ALT less than 2.5 times upper limit of normal (ULN); alkaline phosphatase less than 5 times the upper limit of normal (ULN); 9) adequate renal function: serum creatinine less than upper limit of normal (ULN) or calculated creatinine clearance at least 60 mL/min; 10) ECG is normal, there is no non-healing wounds on the body; 11) had not received previous treatment anticancer drugs, or had only received for previous non-metastatic tumors adjuvant or neoadjuvant chemotherapy, but when you start to study treatment has ended more than 6 months; 12) have conducted previous surgery patients required to study treatment was started more than four weeks, and the patient had recovered; 13) have an intact uterus in women prior to enrollment in the study must have a negative pregnancy test result (unless it is already 24 months of amenorrhea) within 28 days. If the pregnancy test from the first administration more than seven days, urine pregnancy test is required for authentication (less than 7 days before the first dose); 14) previous to biological agents, particularly E.coli genetically engineered products without serious allergic reactions; 15) signed informed consent.", "candidate_expression": "((ALT less than 2.5 times upper limit of normal (ULN)) AND (AST less than 2.5 times upper limit of normal (ULN)) AND (ECG normal) AND (ECOG PS 0 or 1) AND (IASLC2009 new TNM staging stage <U+2162>B or <U+2163>) AND (Male) AND (absolute neutrophil count (ANC) at least 2×10^9/L) AND (adequate hematological function) AND (adequate liver function) AND (adequate renal function) AND (aged 18 to 75 years) AND (alkaline phosphatase less than 5 times the upper limit of normal (ULN)) AND (calculated creatinine clearance at least 60 mL/min) AND (chemotherapy ended more than 6 months) AND (evaluable lesions at least one) AND (expected survival at least 3 months) AND (female) AND (have an intact uterus in women prior to enrollment in the study must have a negative pregnancy test result (unless it is already 24 months of amenorrhea) within 28 days. If the pregnancy test from the first administration more than seven days, urine pregnancy test is required for authentication (less than 7 days before the first dose);) AND (hemoglobin at least 9 g/dL) AND (longest diameter at least 10mm) AND (longest diameter at least 20mm) AND (lung cancer after 1 year of lung cancer resection untreated relapsed) AND (non-metastatic tumors previous adjuvant neoadjuvant) AND (non-small cell lung cancer histologically confirmed wild-type EGFR ALK-negative) AND (platelet count at least 100×10^9/L) AND (regular CT) AND (serum creatinine less than upper limit of normal (ULN)) AND (spiral CT) AND (total bilirubin less than upper limit of normal (ULN)) AND NOT (non-healing wounds on the body) AND NOT (anticancer drugs))"}
{"candidate_id": "LLM00061", "doc_id": "NCT02781610_inc", "case_bucket": "or", "source_criterion": "Male or female =18 years of age at Visit 1 Documentation of a CF diagnosis Enrolled in the Cystic Fibrosis Foundation National Patient Registry (CFFNPR) prior to Visit 1 (US sites only) At the time of Visit 1, there is a plan to initiate IV antibiotics for a pulmonary exacerbation Performed spirometry at Visit 1 and Visit 2 and willing to perform spirometry at Visit 3 Completed the CRISS questionnaire at Visit 1 and Visit 2 and willing to complete the Cystic Fibrosis Respiratory Symptoms Diary (CFRSD) questionnaire at Visit 3 Willing to adhere to a specific treatment duration determined by initial response to treatment and subsequent randomization Willing to return for follow up Visit 3 Written informed consent obtained from the subject or subject's legal representative", "candidate_expression": "((=18 years) AND (At the time of Visit 1) AND (CF) AND (CRISS questionnaire) AND (Cystic Fibrosis Respiratory Symptoms Diary (CFRSD) questionnaire) AND (Enrolled in the Cystic Fibrosis Foundation National Patient Registry (CFFNPR)) AND (IV antibiotics) AND (Male) AND (US sites) AND (Visit 1) AND (Visit 2) AND (Visit 3) AND (Willing to) AND (Written informed consent) AND (age) AND (at Visit 1) AND (at Visit 2) AND (at Visit 3) AND (female) AND (follow up Visit 3) AND (from the subject) AND (from the subject's legal representative) AND (prior to Visit 1) AND (pulmonary exacerbation) AND (spirometry) AND (willing to complete) AND (willing to perform))"}
{"candidate_id": "LLM00062", "doc_id": "NCT03369379_inc", "case_bucket": "or", "source_criterion": "Female patients older than 18 years. Patients who agree to participate in the study. Those that meet the ACR 1990 and 2010 criteria for Fibromyalgia. No previous use of vitamin D. Patients diagnosed with primary or secondary fibromyalgia.", "candidate_expression": "((Female) AND (Fibromyalgia ACR 1990 ACR 2010 vitamin D) AND (Patients who agree to participate in the study.) AND (fibromyalgia) AND (years older than 18 years) AND ((primary) OR (secondary)))"}
{"candidate_id": "LLM00063", "doc_id": "NCT03011177_inc", "case_bucket": "other", "source_criterion": "Patients who are 19 years or older on screening Patients with type 2 diabetes mellitus Patients with 7.0% = HbA1c = 11.0% at the screening visit Patients with Fasting Plasma Glucose <15mmol/L(270mg/dL) on screening", "candidate_expression": "((19 or older) AND (270mg/dL) AND (7.0% 11.0%) AND (<15mmol/L) AND (Fasting Plasma Glucose) AND (HbA1c) AND (at the screening visit) AND (on screening) AND (screening) AND (type 2 diabetes mellitus) AND (years))"}
{"candidate_id": "LLM00064", "doc_id": "NCT03373318_exc", "case_bucket": "other", "source_criterion": "Patients who do not meet the inclusion criteria and those who have a history of allergic reactions to human albumin, as well as those who have received iodinated contrast during the 7 days prior to surgery and pregnant women, will be excluded from the study.", "candidate_expression": "((allergic history) AND (human albumin) AND (iodinated contrast during the 7 days prior to surgery) AND (pregnant) AND (surgery) AND (women) AND NOT (meet the inclusion criteria))"}
{"candidate_id": "LLM00065", "doc_id": "NCT01664507_exc", "case_bucket": "or", "source_criterion": "underlying lung or heart disase contra indication to dexamethasone immune deficient state preterm birth previous intubation or apnea history", "candidate_expression": "((apnea) AND (contra indication) AND (dexamethasone) AND (heart disase) AND (immune deficient state) AND (intubation) AND (lung disase) AND (preterm birth))"}
{"candidate_id": "LLM00066", "doc_id": "NCT02102243_inc", "case_bucket": "other", "source_criterion": "Normotensive controls Stage I (140-159/90-99 mmHg) untreated subjects with essential hypertension Patients with PA and stage I (140-159/90-99 mmHg) hypertension", "candidate_expression": "((PA) AND (controls Normotensive) AND (essential hypertension Stage I untreated) AND (hypertension stage I))"}
{"candidate_id": "LLM00067", "doc_id": "NCT02413970_exc", "case_bucket": "or", "source_criterion": "Central + mixed apneas > 25% of the total apnea-hypopnea index (AHI) Any anatomical finding that would compromise the performance of upper airway stimulation, such as the presence of complete concentric collapse of the soft palate Any condition or procedure that has compromised neurological control of the upper airway Patients who are unable or do not have the necessary assistance to operate the patient remote Patients who are pregnant or plan to become pregnant Patients who will require magnetic resonance imaging (MRI) Patients with an implantable device that may be susceptible to unintended interaction with the Inspire system. Body Mass Index (BMI) of > 32 Any chronic medical illness or condition that contraindicates a surgical procedure under general anesthesia, as judged by the clinical study Investigator Has a terminal illness with life expectancy < 12 months Active psychiatric disease (psychotic illness, major depression, or acute anxiety attacks) which prevents subject compliance with the requirements of the investigational study testing Any other reason the investigator deems subject is unfit for participation in the study", "candidate_expression": "((< 12 months) AND (> 25%) AND (> 32) AND (AHI) AND (BMI) AND (Body Mass Index) AND (MRI) AND (Patients who are pregnant or plan to become pregnant) AND (contraindicates) AND (general anesthesia) AND (life expectancy) AND (magnetic resonance imaging) AND (psychiatric disease) AND (surgical procedure) AND (total apnea-hypopnea index) AND ((Central apneas) OR (mixed apneas)) AND ((acute anxiety attacks) OR (major depression) OR (psychotic illness)))"}
{"candidate_id": "LLM00068", "doc_id": "NCT03079141_inc", "case_bucket": "other", "source_criterion": "Age of = 18 years of age and able to give written informed consent; Active chronic central serous chorioretinopathy (cCSC); Subjective visual loss > 6 weeks, interpreted as onset of active disease; Foveal subretinal fluid (SRF), on optical coherence tomography (OCT), at Baseline Examination; =1 ill-defined hyperfluorescent leakage areas on fluorescein angiography (FA) with retinal pigment epithelial window defect(s) that are compatible with cCSC; Hyperfluorescent areas on indocyanine green angiography (ICGA).", "candidate_expression": "((Age = 18 years) AND (Foveal subretinal fluid (SRF)) AND (Hyperfluorescent areas) AND (Subjective visual loss > 6 weeks) AND (able to give written informed consent) AND (central serous chorioretinopathy (cCSC) Active chronic) AND (fluorescein angiography (FA)) AND (hyperfluorescent leakage areas =1 ill-defined) AND (indocyanine green angiography (ICGA)) AND (optical coherence tomography (OCT) at Baseline Examination) AND (retinal pigment epithelial window defect(s)))"}
{"candidate_id": "LLM00069", "doc_id": "NCT03420638_inc", "case_bucket": "other", "source_criterion": "Scheduled to undergo bilateral palatine tonsillectomy as the only procedure", "candidate_expression": "((Scheduled to undergo) AND (bilateral) AND (only procedure) AND (palatine tonsillectomy) AND (procedure))"}
{"candidate_id": "LLM00070", "doc_id": "NCT02312089_inc", "case_bucket": "scope", "source_criterion": "Women subjected to ICSI through controlled ovarian hyperstimulation (COH) with pituitary downregulation by GnRH antagonist.", "candidate_expression": "((COH) AND (GnRH antagonist) AND (ICSI) AND (Women) AND (ovarian hyperstimulation) AND (pituitary downregulation))"}
{"candidate_id": "LLM00071", "doc_id": "NCT02589977_exc", "case_bucket": "or", "source_criterion": "Exclusion Criteria: coronary artery disease, diabetes mellitus, contraindications to cardiac magnetic resonance imaging (CMR), weight >350 lbs, inability to lie flat for imaging, anemia, contraindications to regadenoson or aminophylline HEALTHY: known cardiovascular disease, cardiac risk factors or use of cardiac medications HYPERTENSIVE: known cardiovascular disease or risk factors aside from hypertension or use of cardiac medications HFpEF: prior history of LVEF below 50%, acute decompensated HF, moderate or greater valvular disease, significant cardiac arrhythmias, pericardial disease, congenital heart disease, primary pulmonary hypertension", "candidate_expression": "((HEALTHY) AND (HFpEF) AND (HYPERTENSIVE) AND (cardiac magnetic resonance imaging (CMR)) AND (cardiac medications) AND NOT (cardiovascular risk factors from hypertension) AND ((aminophylline) OR (regadenoson)) AND ((cardiac medications) OR (cardiac risk factors) OR (cardiovascular disease)) AND ((cardiovascular disease) OR (cardiovascular risk factors)) AND ((LVEF prior history of below 50%) OR (cardiac arrhythmias significant) OR (congenital heart disease) OR (decompensated HF acute) OR (pericardial disease) OR (primary pulmonary hypertension) OR (valvular disease)) AND ((greater) OR (moderate)) AND ((anemia) OR (contraindications) OR (coronary artery disease) OR (diabetes mellitus) OR (inability to lie flat for imaging) OR (weight >350 lbs)))"}
{"candidate_id": "LLM00072", "doc_id": "NCT02744976_exc", "case_bucket": "or", "source_criterion": "cardiac or non-cardiac illness with life expectancy of less than two years; failure to advance the IVUS catheter through the culprit lesion; acute coronary syndrome congestive heart failure NYHA III-IV diabetes mellitus chronic kidney disease previous PCI in the target vessel heavily calcified vessels allergy to metformin", "candidate_expression": "((IVUS catheter) AND (NYHA III-IV) AND (PCI previous target vessel target vessel) AND (acute coronary syndrome) AND (advance the IVUS catheter failure culprit lesion) AND (allergy) AND (chronic kidney disease) AND (congestive heart failure) AND (diabetes mellitus) AND (heavily calcified vessels) AND (life expectancy less than two years) AND (metformin) AND ((cardiac illness) OR (non-cardiac illness)))"}
{"candidate_id": "LLM00073", "doc_id": "NCT02644629_exc", "case_bucket": "or", "source_criterion": "Active or past psychotic disorder, including a history of psychotic affective state Mental Retardation or Autistic Spectrum Disorder Prominent personality disorder Cardiac or neurologic active medical condition, including past CVA/TIA (Cardiovascular Accident/Transient Ischemic Attack) or any other unstable medical condition. Chronic nasal congestion Active or recent drug or alcohol abuse Substantial suicidality in a patient requiring admission but refuses to do so, and signs an \"against medical advice\" release form as part of clinical evaluation, and does not answer the terms for involuntary admission.", "candidate_expression": "((Chronic) AND (Prominent personality disorder) AND (Substantial) AND (admission) AND (medical condition) AND (nasal congestion) AND (past) AND (psychotic affective state) AND (psychotic disorder) AND (suicidality) AND (unstable) AND ((Cardiac active medical condition) OR (neurologic active medical condition)) AND ((CVA) OR (TIA)) AND ((Cardiovascular Accident) OR (Transient Ischemic Attack)) AND ((alcohol abuse) OR (drug abuse)) AND ((Active) OR (recent)) AND ((Active) OR (past)) AND ((Autistic Spectrum Disorder) OR (Mental Retardation)))"}
{"candidate_id": "LLM00074", "doc_id": "NCT03460002_exc", "case_bucket": "or", "source_criterion": "the child has temperature > 39.0◦C or a severe acute illness as defined by the examining nurse the child has as a mid upper arm circumference < 110 mm and is older than 6 months (most feasible local indicator of AIDS and chronic immunosuppressive disease) the child has experienced a severe allergic reaction after previous vaccination, drug or food. the child is enrolled in an ongoing study of Bacillus Calmette Guerin vaccine and is < 2 months old For the RECAMP-MV trial: the child is enrolled in RECAMP-OPV", "candidate_expression": "((RECAMP-MV trial enrolled in RECAMP-OPV) AND (acute illness severe as defined by the examining nurse) AND (child) AND (drug) AND (food) AND (mid upper arm circumference < 110 mm) AND (old is older than 6 months) AND (severe allergic reaction after previous vaccination, drug or food) AND (temperature > 39.0◦C) AND (the child is enrolled in an ongoing study of Bacillus Calmette Guerin vaccine and is < 2 months old) AND (vaccination))"}
{"candidate_id": "LLM00075", "doc_id": "NCT02562456_inc", "case_bucket": "or", "source_criterion": "Children aging between 3 and 6 years presenting good health conditions whose parents or legal guardians accept and sign the consent form with at least one occlusal or occlusal proximal caries lesion in primary molars only occlusal and/or occlusal-proximal surfaces with caries lesions with dentin involvement", "candidate_expression": "((Children) AND (aging between 3 and 6 years) AND (caries lesion at least one primary molars) AND (caries lesions) AND (dentin involvement) AND (good health conditions) AND (whose parents or legal guardians accept and sign the consent form) AND ((occlusal surfaces) OR (occlusal-proximal surfaces)) AND ((occlusal) OR (occlusal proximal)))"}
```
