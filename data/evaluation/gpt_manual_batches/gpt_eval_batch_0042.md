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
{"candidate_id": "LLM01026", "doc_id": "NCT03263481_exc", "case_bucket": "other", "source_criterion": "NA", "candidate_expression": "(EMPTY)"}
{"candidate_id": "LLM01027", "doc_id": "NCT02621541_inc", "case_bucket": "or", "source_criterion": "suspicion of nonfunctional P-NET on primary CT (i.e hypervascularity) or MRI signed informed consent", "candidate_expression": "((MRI) AND (hypervascularity) AND (nonfunctional P-NET) AND (primary CT) AND (signed informed consent) AND (suspicion))"}
{"candidate_id": "LLM01028", "doc_id": "NCT02965443_inc", "case_bucket": "other", "source_criterion": "Type 2 diabetes Age 18 - 75 years Anti-GAD antibodies negative (Glutamic Acid Decarboxylase) C-peptide levels = 1.5 ng/mL Fasting blood glucose > 126 mg/dl HbA1c 8.0 - 10.5 % BMI 25.0 - 45.0 kg/m2 Previous therapy with BBIT (basal insulin and at least once daily bolus insulin)", "candidate_expression": "((18 - 75 years) AND (25.0 - 45.0 kg/m2) AND (8.0 - 10.5 %) AND (= 1.5 ng/mL) AND (> 126 mg/dl) AND (Age) AND (Anti-GAD antibodies (Glutamic Acid Decarboxylase)) AND (BBIT) AND (BMI) AND (C-peptide levels) AND (Fasting blood glucose) AND (HbA1c) AND (Previous) AND (Type 2 diabetes) AND (basal insulin and at least once daily bolus insulin) AND (negative) AND (therapy))"}
{"candidate_id": "LLM01029", "doc_id": "NCT03132259_inc", "case_bucket": "other", "source_criterion": "Age18-65 ASA 1-2 Elective TNTS resection of Pituitary Tumor No narcotic before surgery as premedication Able to Extubate", "candidate_expression": "((1-2) AND (18-65) AND (ASA) AND (Able to) AND (Age) AND (Elective) AND (Extubate) AND (No) AND (Pituitary Tumor) AND (TNTS resection) AND (before surgery) AND (narcotic) AND (surgery))"}
{"candidate_id": "LLM01030", "doc_id": "NCT02295202_inc", "case_bucket": "other", "source_criterion": "Metabolic Syndrome (ATP III) Moderate to severe OSA", "candidate_expression": "((ATP III) AND (Metabolic Syndrome) AND (OSA Moderate to severe))"}
{"candidate_id": "LLM01031", "doc_id": "NCT02968342_inc", "case_bucket": "other", "source_criterion": "Menopausal status Sexually active", "candidate_expression": "((Menopausal) AND (Sexually active))"}
{"candidate_id": "LLM01032", "doc_id": "NCT02744976_inc", "case_bucket": "other", "source_criterion": "age =18 and <75 years; patients with stable coronary artery disease referred to PCI in an artery suitable for IVUS pullback; signed informed consent before PCI.", "candidate_expression": "((=18 and <75 years) AND (PCI) AND (age) AND (artery suitable for IVUS pullback) AND (coronary artery disease) AND (referred to) AND (signed informed consent before PCI) AND (stable))"}
{"candidate_id": "LLM01033", "doc_id": "NCT03335904_inc", "case_bucket": "or", "source_criterion": "normotensive forced expiratory volume in 1s : forced vital capacity ratio > 0.75 no medical history of cardiovascular and respiratory disease not taking medications other than oral contraceptives free from sleep apnea body mass index less than 30 kg/m2", "candidate_expression": "((body mass index less than 30 kg/m2) AND (forced expiratory volume in 1s : forced vital capacity ratio > 0.75) AND (medications) AND (normotensive) AND NOT (oral contraceptives) AND NOT (sleep apnea) AND ((cardiovascular disease) OR (respiratory disease)))"}
{"candidate_id": "LLM01034", "doc_id": "NCT02653131_inc", "case_bucket": "or", "source_criterion": "patients receiving home parenteral nutrition (HPN) because of short bowel syndrome for at least 12 months stable metabolic status benign disease", "candidate_expression": "((benign disease) AND (metabolic status stable) AND ((home parenteral nutrition (HPN)) OR (short bowel syndrome)))"}
{"candidate_id": "LLM01035", "doc_id": "NCT03181984_exc", "case_bucket": "or", "source_criterion": "Allergy to porphyrins and analogues; Photosensitivity; Porphyria; Allergic constitution; Scar diathesis; Pregnancy or unwilling to adopt reliable contraceptive measures during the month after drug application; Be judged not suitable to participate the study by the investigators", "candidate_expression": "((Allergic constitution) AND (Allergy) AND (Be judged not suitable to participate the study by the investigators) AND (Photosensitivity) AND (Porphyria) AND (Pregnancy or unwilling to adopt reliable contraceptive measures during the month after drug application) AND (Scar diathesis) AND (porphyrins) AND (porphyrins analogues))"}
{"candidate_id": "LLM01036", "doc_id": "NCT02101554_exc", "case_bucket": "or", "source_criterion": "Columbia-Suicide Severity Rating Scale (C-SSRS) for suicidal ideation and behavior in past year. Hypersensitivity to morphine, naltrexone. A life expectancy (assessed by investigator) of less than 6 months or is no longer capable of taking medication orally. Undergone surgery within 3 days prior to the first day of dosing.", "candidate_expression": "((C-SSRS) AND (Columbia-Suicide Severity Rating Scale) AND (Hypersensitivity) AND (life expectancy less than 6 months) AND (surgery within 3 days prior to the first day of dosing) AND ((suicidal behavior) OR (suicidal ideation)) AND ((morphine) OR (naltrexone)))"}
{"candidate_id": "LLM01037", "doc_id": "NCT01997580_exc", "case_bucket": "or", "source_criterion": "DSM-IV-TR substance-related disorders (except nicotine) significant medical or neurological conditions mental retardation or organic brain damage", "candidate_expression": "((mental retardation) AND (organic brain damage) AND (significant medical or neurological conditions) AND (substance-related disorders DSM-IV-TR) AND NOT (nicotine))"}
{"candidate_id": "LLM01038", "doc_id": "NCT03278548_exc", "case_bucket": "other", "source_criterion": "NA", "candidate_expression": "(EMPTY)"}
{"candidate_id": "LLM01039", "doc_id": "NCT03328052_inc", "case_bucket": "or", "source_criterion": "Patients with a clinical diagnosis of depression who in the judgement of their physician require medication management may be eligible for enrollment. A score of 10 or more on the PHQ-9 instrument will be required for enrollment. Some practices utilize the PHQ-2 and PHQ-9 are part of routine screening for depression. If the tests are performed routinely, they do not need to be repeated for study eligibility, and may be performed prior to informed consent for this study. If, however, the PHQ-9 is not routinely performed, informed consent must be performed prior to administration. Patients with a score below 10 will be considered screen failures and will not be enrolled or offered the MYnd testing. Patients with non-psychotic comorbid conditions may be included. Patients must be either medication treatment naïve for behavioral illnesses or have no active medication treatments for at least 1 month prior to enrollment. Prohibited medications at the time of enrollment will include stimulants, benzodiazepines and THC. Prior therapy with these agents is permitted with a washout of >30 days. Patients must have private medical insurance coverage through Horizon Blue Cross Blue Shield. This is limited to insured commercial members, including HMO, and excluding, for the avoidance of doubt, members of self-insured customers or Medicare or Medicaid programs.", "candidate_expression": "((PHQ-9) AND (THC) AND (active) AND (behavioral illnesses) AND (benzodiazepines) AND (depression) AND (for at least 1 month prior to enrollment) AND (medication) AND (naïve) AND (no) AND (non-psychotic conditions) AND (score of 10 or more) AND (stimulants))"}
{"candidate_id": "LLM01040", "doc_id": "NCT00502567_exc", "case_bucket": "other", "source_criterion": "Inadequate bone marrow reserve history of poorly controlled hypertension", "candidate_expression": "((Inadequate bone marrow reserve) AND (history) AND (poorly controlled hypertension))"}
{"candidate_id": "LLM01041", "doc_id": "NCT03182114_exc", "case_bucket": "other", "source_criterion": "Cardiac morbidities hypertensive disorders of pregnancy peripartum bleeding baseline systolic blood pressure (SBP) < 100 mmHg body mass index > 35", "candidate_expression": "((Cardiac morbidities) AND (SBP) AND (body mass index > 35) AND (hypertensive disorders of pregnancy) AND (peripartum bleeding) AND (systolic blood pressure baseline < 100 mmHg))"}
{"candidate_id": "LLM01042", "doc_id": "NCT03249311_inc", "case_bucket": "other", "source_criterion": "Male participants between 18 and 40 years-old Written informed consent signed by the participant", "candidate_expression": "((Male) AND (Written informed consent signed by the participant) AND (between 18 and 40 years) AND (old))"}
{"candidate_id": "LLM01043", "doc_id": "NCT00679341_exc", "case_bucket": "or", "source_criterion": "History of any chemotherapy for MBC. An interval of < 6 months from the completion of cytotoxic chemotherapy in the neo-adjuvant or adjuvant setting until the time of metastatic diagnosis. Trastuzumab ≤ 21 days prior to randomization. Hormone therapy < 7 days prior to randomization. Current peripheral neuropathy of Grade ≥ 3. History of other malignancy within the last 5 years, except for appropriately treated carcinoma in situ of the cervix, non-melanoma skin carcinoma, Stage I uterine cancer, or other cancers with a similar outcome as those previously mentioned. Previous radiotherapy for the treatment of unresectable, locally advanced or metastatic breast cancer is not allowed if more than 25% of marrow-bearing bone has been irradiated or the last fraction of radiotherapy has been administered within approximately 3 weeks prior to randomization. Brain metastases that are untreated, symptomatic, or require therapy to control symptoms or any radiation, surgery, or other therapy to control symptoms from brain metastases within 2 months prior to randomization. History of exposure to the following cumulative doses of anthracyclines: Doxorubicin or liposomal doxorubicin > 500 mg/m^2; epirubicin > 900 mg/m^2; mitoxantrone > 120mg/m^2 and idarubicin > 90 mg/m^2. Current unstable angina. History of symptomatic congestive heart failure, or ventricular arrhythmia requiring treatment. History of myocardial infarction within 6 months prior to randomization. Left ventricular ejection fraction (LVEF) below 50% within approximately 28 days prior to randomization. History of decreased LVEF or symptomatic congestive heart failure (CHF) with previous adjuvant trastuzumab treatment. Cardiac troponin I ≥ 0.2 ng/mL within 28 days of randomization. Severe dyspnea at rest because of complications of advanced malignancy or requiring current continuous oxygen therapy. Current severe, uncontrolled systemic disease (eg, clinically significant cardiovascular, pulmonary, or metabolic disease; wound healing disorders; ulcers; or bone fractures). Major surgical procedure or significant traumatic injury within approximately 28 days prior to randomization or anticipation of the need for major surgery during the course of study treatment. Current pregnancy or lactation. History of receiving any investigational treatment within approximately 28 days prior to randomization. Current known infection with human immunodeficiency virus (HIV), active hepatitis B and/or hepatitis C virus. History of intolerance (including Grade 3-4 infusion reaction) or hypersensitivity to trastuzumab, murine proteins, or docetaxel. Known hypersensitivity to any of the study drugs, including the excipients, or any drugs formulated in polysorbate 80. Assessed by the investigator to be unable or unwilling to comply with the requirements of the protocol.", "candidate_expression": "((3-4) AND (< 6 months) AND (< 7 days prior to randomization) AND (> 120mg/m^2) AND (> 500 mg/m^2) AND (> 90 mg/m^2) AND (> 900 mg/m^2) AND (Brain metastases) AND (Cardiac troponin I) AND (Current) AND (Doxorubicin) AND (Grade) AND (Grade ≥ 3) AND (History) AND (History of) AND (Hormone therapy) AND (I) AND (LVEF) AND (Left ventricular ejection fraction (LVEF)) AND (MBC) AND (Major) AND (Previous) AND (Severe) AND (Stage) AND (Trastuzumab) AND (adjuvant) AND (adjuvant setting) AND (advanced malignancy) AND (anthracyclines) AND (anticipation of the need) AND (appropriately treated) AND (below 50%) AND (bone fractures) AND (brain metastases) AND (breast cancer) AND (carcinoma in situ of the cervix) AND (cardiovascular disease) AND (chemotherapy) AND (clinically significant) AND (complications) AND (congestive heart failure) AND (congestive heart failure (CHF)) AND (continuous oxygen therapy) AND (current) AND (cytotoxic chemotherapy) AND (decreased) AND (docetaxel) AND (drugs formulated in polysorbate 80) AND (during the course of study treatment) AND (dyspnea) AND (epirubicin) AND (except for) AND (hepatitis B virus) AND (hepatitis C virus) AND (human immunodeficiency virus (HIV)) AND (hypersensitivity) AND (idarubicin) AND (infusion reaction) AND (intolerance) AND (investigational treatment) AND (lactation) AND (liposomal doxorubicin) AND (locally advanced) AND (major surgery) AND (malignancy) AND (marrow-bearing bone irradiated) AND (metabolic disease) AND (metastatic) AND (metastatic diagnosis) AND (mitoxantrone) AND (more than 25%) AND (murine proteins) AND (myocardial infarction) AND (neo-adjuvant setting) AND (non-melanoma skin carcinoma) AND (other) AND (other therapy to control symptoms) AND (peripheral neuropathy) AND (pregnancy) AND (previous) AND (pulmonary disease) AND (radiation) AND (radiotherapy) AND (randomization) AND (require therapy) AND (requiring current continuous oxygen therapy) AND (requiring treatment) AND (severe) AND (significant) AND (study drugs) AND (study treatment) AND (surgery) AND (surgical procedure) AND (symptomatic) AND (systemic disease) AND (trastuzumab) AND (traumatic injury) AND (treated) AND (treatment) AND (ulcers) AND (unable to comply with the requirements of the protocol) AND (uncontrolled) AND (unresectable) AND (unstable angina) AND (untreated) AND (unwilling to comply with the requirements of the protocol) AND (uterine cancer) AND (ventricular arrhythmia) AND (within 2 months prior to randomization) AND (within 28 days of randomization) AND (within 6 months prior to randomization) AND (within approximately 28 days prior to randomization) AND (within the last 5 years) AND (wound healing disorders) AND (≤ 21 days prior to randomization) AND (≥ 0.2 ng/mL) AND (≥ 3))"}
{"candidate_id": "LLM01044", "doc_id": "NCT03620526_inc", "case_bucket": "or", "source_criterion": "presence of typical HF symptoms and signs LV ejection fraction = 50 elevated levels of NT-proBNP (at least >125 pg/ml) echocardiographic structural (a left atrial volume index > 34 mL/m2 or a left ventricular mass index =115 g/m2 for males and =95 g/m2 for females) or functional alterations (E/e'=13 and a mean e' septal and lateral wall < 9 cm/s).", "candidate_expression": "((< 9 cm/s) AND (= 50) AND (=115 g/m2) AND (=13) AND (=95 g/m2) AND (> 34 mL/m2) AND (E/e') AND (HF signs) AND (HF symptoms) AND (LV ejection fraction) AND (NT-proBNP) AND (at least >125 pg/ml) AND (echocardiographic structural) AND (elevated) AND (females) AND (functional alterations) AND (left atrial volume inde) AND (left ventricular mass index) AND (males) AND (mean e' septal and lateral wall) AND (typical))"}
{"candidate_id": "LLM01045", "doc_id": "NCT02467686_exc", "case_bucket": "or", "source_criterion": "Women did not have breast cancer do not use tamoxifen or aromatase inhibitor not in menopause and not have hot flashes", "candidate_expression": "((aromatase inhibitor) AND (breast cancer) AND (hot flashes) AND (menopause) AND (not) AND (tamoxifen))"}
{"candidate_id": "LLM01046", "doc_id": "NCT02208739_inc", "case_bucket": "or", "source_criterion": "Patients should have at least 12 teeth present Patients with Moderate to Advanced Chronic periodontitis Patients with 2 or more interproximal sites (not on same tooth) with probing pocket depths of 5mm or more and 2 or more interproximal sites (not on same tooth)of probing attachment loss of 4mm or more which bled on probing.", "candidate_expression": "((Chronic periodontitis) AND (interproximal sites of probing attachment loss of 4mm or more 2 or more bled on probing 4mm or more) AND (interproximal sites with probing pocket depths of 5mm or more 2 or more 5mm or more) AND (probing) AND (teeth present at least 12 Moderate Advanced))"}
{"candidate_id": "LLM01047", "doc_id": "NCT02041299_inc", "case_bucket": "or", "source_criterion": "Male or female = 2 years of age; Have sickle cell disease (confirmed by Hb electrophoresis or more specific tests) or other conditions with iron overload from repeated blood transfusions (see exclusion criteria for exceptions); Baseline LIC >7 mg/g dw (measured by MRI); Patients who have received no less than 20 transfusions of RBCs; Patients who have received at least 1 transfusion per year in the last 2 years and who are expected to have a continuing requirement (based on Investigator's judgement) during the duration of the trial", "candidate_expression": "((Baseline LIC >7 mg/g) AND (MRI) AND (age = 2 years) AND (blood transfusions repeated) AND (expected to have a continuing requirement during the duration of the trial) AND (transfusion at least 1 per year in the last 2 years) AND (transfusions of RBCs no less than 20) AND ((Male) OR (female)) AND ((other conditions with iron overload) OR (sickle cell disease)) AND ((Hb electrophoresis) OR (more specific tests)))"}
{"candidate_id": "LLM01048", "doc_id": "NCT01217671_exc", "case_bucket": "or", "source_criterion": "FEV1 >= 80% or FEV1 < 20% of predicted value post-bronchodilator. FEV1/SVC>=70% History of lung transplant. Any lung surgery within the past two years. On any thoracic surgery waiting list. End of last exacerbation less than 6 weeks prior to screening/re-screening visit. Clinically significant intercurrent illnesses (except for respiratory or liver disease secondary to AAT deficiency), including: cardiac, hepatic, renal, endocrine, neurological, hematological, neoplastic, immunological, skeletal or other) that in the opinion of the investigator, could interfere with the safety, compliance or other aspects of this study. Patients with well-controlled, chronic diseases could possibly be included after consultation with the treating physician and the sponsor. Active smoking during the last 12 months from screening date. Pregnancy or lactation. Woman of child-bearing potential not taking adequate contraception deemed reliable by the investigator. Presence of psychiatric/ mental disorder or any other medical disorder which might impair the patient's ability to give informed consent or to comply with the requirements of the study protocol. Evidence of ongoing viral infection with HCV, HBV and/or HIV. Evidence of alcohol abuse or history of alcohol abuse or illegal and/or legally prescribed drugs. IgA Deficiency History of life threatening allergy, anaphylactic reaction, or systemic response to human plasma derived products. Participation in another clinical trial within 30 days prior to baseline visit. Inability to attend scheduled clinic visits and/or comply with the study protocol. Any other factor that, in the opinion of the investigator, would prevent the patient from complying with the requirements of the protocol.", "candidate_expression": "((AAT deficiency) AND (Active smoking Active during the last 12 months from screening date) AND (Any other factor that, in the opinion of the investigator, would prevent the patient from complying with the requirements of the protocol.) AND (Clinically significant) AND (Clinically significant intercurrent illnesses (except for respiratory or liver disease secondary to AAT deficiency), including: cardiac, hepatic, renal, endocrine, neurological, hematological, neoplastic, immunological, skeletal or other) that in the opinion of the investigator, could interfere with the safety, compliance or other aspects of this study. Patients with well-controlled, chronic diseases could possibly be included after consultation with the treating physician and the sponsor.) AND (FEV1/SVC >=70%) AND (IgA Deficiency) AND (Inability to attend scheduled clinic visits and/or comply with the study protocol.) AND (Presence of psychiatric/ mental disorder or any other medical disorder which might impair the patient's ability to give informed consent or to comply with the requirements of the study protocol.) AND (Woman) AND (Woman of child-bearing potential not taking adequate contraception deemed reliable by the investigator.) AND (adequate) AND (alcohol abuse) AND (bronchodilator) AND (cardiac) AND (child-bearing potential) AND (deemed reliable by the investigator) AND (endocrine) AND (exacerbation less than 6 weeks prior to screening/re-screening visit) AND (hematological) AND (hepatic) AND (immunological) AND (in the opinion of the investigator) AND (intercurrent illnesses Clinically significant) AND (lung surgery within the past two years) AND (lung transplant History) AND (neoplastic) AND (neurological) AND (other) AND (products human plasma derived) AND (renal) AND (skeletal) AND (thoracic surgery) AND (thoracic surgery waiting list) AND (viral infection ongoing) AND NOT (contraception adequate deemed reliable by the investigator) AND ((liver disease) OR (respiratory disease)) AND ((FEV1 < 20% of predicted value post-bronchodilator) OR (FEV1 >= 80%)) AND ((Pregnancy) OR (lactation)) AND ((mental disorder) OR (other medical disorder) OR (psychiatric disorder)) AND ((HBV) OR (HCV) OR (HIV)) AND ((abuse illegal drugs) OR (abuse legally prescribed drugs) OR (alcohol abuse)) AND ((anaphylactic reaction) OR (life threatening allergy life threatening) OR (systemic response to human plasma derived products)))"}
{"candidate_id": "LLM01049", "doc_id": "NCT02406495_inc", "case_bucket": "other", "source_criterion": "Is between 18 and 40 years of age (inclusive) Has had a self-reported visual exam in the last two years Is an adapted Avaira sphere contact lens wearer (at least 1 week in Avaira sphere) Has a contact lens spherical prescription between + 2.25 to - 8.00 (inclusive) Has a spectacle cylinder up to 0.75D in each eye. Can achieve best corrected spectacle distance visual acuity of 20/25 (0.10 logMAR) or better in each eye. Can achieve a distance visual acuity of 20/30 (0.18 logMAR) or better in each eye with the study contact lenses. Has clear corneas and no active ocular disease Has read, understood and signed the information consent letter. Patient contact lens refraction should fit within the available parameters of the study lenses. Is willing to comply with the wear schedule (at least 5 days per week, > 8 hours/day assuming there are no contraindications for doing so). Is willing to comply with the visit schedule", "candidate_expression": "((Avaira sphere) AND (Avaira sphere contact lens at least 1 week in Avaira sphere) AND (Has read, understood and signed the information consent letter.) AND (Is willing to comply with the visit schedule) AND (Is willing to comply with the wear schedule (at least 5 days per week, > 8 hours/day assuming there are no contraindications for doing so).) AND (age between 18 and 40 years (inclusive)) AND (best corrected spectacle distance visual acuity 20/25 or better 0.10 logMAR or better) AND (clear corneas) AND (contact lens spherical + 2.25 to - 8.00 (inclusive)) AND (distance visual acuity 20/30 or better 0.18 logMAR or better) AND (self-reported visual exam in the last two years) AND (spectacle cylinder up to 0.75D) AND (study contact lenses) AND NOT (ocular disease active))"}
{"candidate_id": "LLM01050", "doc_id": "NCT03536520_exc", "case_bucket": "or", "source_criterion": "Any active respiratory, cardiovascular or other disease requiring regular treatment or being otherwise relevant for tolerance of hypoxia or altitude exposure. Any condition that may interfere with protocol compliance including current heavy smoking (>20 cigarettes per day or >20 pack-years with active smoking during the last 10 years), regular use of alcohol. Allergy to acetazolamide and other sulfonamides.", "candidate_expression": "((Allergy) AND (tolerance relevant for) AND (treatment regular) AND ((altitude exposure) OR (hypoxia)) AND ((acetazolamide) OR (sulfonamides)) AND ((cardiovascular disease) OR (disease other) OR (respiratory disease)))"}
```
