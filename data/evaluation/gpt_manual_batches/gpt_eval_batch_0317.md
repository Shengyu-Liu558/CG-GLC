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
{"candidate_id": "LLM07901", "doc_id": "NCT02529475_exc", "case_bucket": "or", "source_criterion": "Patients minors Patients on a legal protection regime type guardianship Respiratory pathologies, cardiovascular, renal, diabetes Claustrophobia Contraindications to exposure to a magnetic field Contraindications to injecting Dotarem ®", "candidate_expression": "((Claustrophobia) AND (Contraindications) AND (Dotarem) AND (legal protection regime type guardianship) AND (magnetic field) AND (minors) AND ((Respiratory pathologies) OR (cardiovascular) OR (diabetes) OR (renal)))"}
{"candidate_id": "LLM07902", "doc_id": "NCT01581749_exc", "case_bucket": "or", "source_criterion": "implanted hardware or other material that would prohibit treatment planning or delivery chemotherapy for a malignancy within the previous 5 years history of an invasive malignancy (other than this prostate cancer,or basal or squamous skin cancers) within prior 5 years hormone ablation for 2 months prior to treatment or during treatment", "candidate_expression": "((chemotherapy) AND (hormone ablation) AND (invasive malignancy) AND (malignancy) AND (other than) AND (treatment) AND (within prior 5 years) AND (within the previous 5 years) AND ((during treatment) OR (for 2 months prior to treatment)) AND ((basal skin cancers) OR (prostate cancer) OR (squamous skin cancers)))"}
{"candidate_id": "LLM07903", "doc_id": "NCT02141061_exc", "case_bucket": "or", "source_criterion": "1. Subject is a post-menopausal woman, defined as either; six (6) months or more (immediately prior to screening visit) without a menstrual period, or prior hysterectomy and/or oophorectomy 2. Subject is pregnant or lactating or is attempting or expecting to become pregnant during the study 3. Women with abnormally high liver enzymes or liver disease. (ALT or AST exceeding 2.0 x ULN AND total bilirubin exceeding 1.5 x ULN at screening and confirmed on repeat). 4. Received an investigational drug in the 30 days prior to the screening for this study 5. Women with a history of PCOS 6. Concurrent use of any testosterone, progestin, androgen, estrogen, anabolic steroids, DHEA or hormonal products for at least 2 weeks prior to screening and during the study. 7. Use of oral contraceptives in the preceding 2 weeks. Use of Depo-Provera® in the preceding 10 months. 8. Has an IUD in place 9. Women currently using narcotics 10. Women currently taking spironolactone 11. Infectious disease screen is positive for HIV or Hepatitis A, B or C. 12. Clinically significant abnormal findings on screening examination or any condition which in the opinion of the investigator would interfere with the participant's ability to comply with the study instructions or endanger the participant if she took part in the study", "candidate_expression": "((ALT) AND (AST) AND (DHEA) AND (Depo-Provera®) AND (HIV) AND (Hepatitis A) AND (Hepatitis B) AND (Hepatitis C) AND (IUD) AND (PCOS) AND (Women) AND (anabolic steroids) AND (androgen) AND (at screening) AND (during the study) AND (estrogen) AND (exceeding 1.5 x ULN) AND (exceeding 2.0 x ULN) AND (for at least 2 weeks prior to screening) AND (high) AND (history) AND (hormonal products) AND (hysterectomy) AND (immediately prior to screening visit) AND (in the 30 days prior to the screening) AND (in the preceding 10 months) AND (in the preceding 2 weeks) AND (investigational drug) AND (is attempting or expecting to become pregnant during the study) AND (lactating) AND (liver disease) AND (liver enzymes) AND (menstrual period) AND (narcotics) AND (oophorectomy) AND (oral contraceptives) AND (post-menopausal) AND (pregnant) AND (prior) AND (progestin) AND (screening) AND (six (6) months or more) AND (spironolactone) AND (testosterone) AND (the screening) AND (total bilirubin) AND (without) AND (woman))"}
{"candidate_id": "LLM07904", "doc_id": "NCT02609425_exc", "case_bucket": "or", "source_criterion": "Any patient with esophageal cancer who is not deemed a surgical candidate or who is not deemed a candidate for the Ivor Lewis technique of esophagectomy (with intrathoracic anastomosis). Any patient less than 18 years of age", "candidate_expression": "((Ivor Lewis technique) AND (age) AND (candidate) AND (esophageal cancer) AND (esophagectomy) AND (intrathoracic anastomosis) AND (less than 18 years) AND (not) AND (surgical) AND (with intrathoracic anastomosis))"}
{"candidate_id": "LLM07905", "doc_id": "NCT02431442_exc", "case_bucket": "or", "source_criterion": "Fasting blood glucose >126 mg/dL at screening. Heterozygous subjects will be excluded for a fasting blood glucose >140 mg/dL. Resting heart rate <45 bpm or >90 bpm at screening. Abnormal thyroid stimulating hormone (TSH) or thyroxine (T4) levels on screening. Elevated ALT or serum creatinine on screening or any clinically significant abnormalities on screening laboratory tests as determined by the Investigator. History of medically treated diabetes or of treated or medically diagnosed hypertension. Heterozygous subjects who have diagnosed hypertension and are well controlled on treatment (Refer to Exclusion Criteria 20 below), are eligible. . Presence of a skin lesion suspicious for malignancy, unless excised prior to Day 1. History of malignancy except for treated cervical carcinoma in situ in the past 5 years. Active or history of any clinically significant medical condition including renal, hepatic, pulmonary, gastrointestinal, cardiovascular, genitourinary, endocrine, immunologic, metabolic, neurologic, psychiatric or hematological disease, based on Investigator judgment. Acute illness or history of illness, which in the opinion of the Investigator, could pose a threat or harm to the subject or obscure interpretation of laboratory test results or interpretation of study data. Positive hepatitis B surface antigen, positive hepatitis C antibody or positive HIV test at screening or a history of positive testing (e.g. liver biopsy, serology) suggesting acute or chronic hepatitis. Abnormal 12-lead electrocardiogram (ECG) at screening or pre-dose (Day -1 or Day 1), except minor deviations deemed to be of no clinical significance by the Investigator. Received any experimental drugs or devices within 30 days or 5 half lives, whichever is longer, prior to dosing. Ongoing participation in a prior clinical study at the time of screening. Blood donation within 60 days prior to screening or intent to donate within 60 days after Final Study Visit. Hospitalization for major surgery including but not limited to abdominal, thoracic, or cardiovascular surgery within the past 3 months prior to screening, or for a clinically significant non-surgical illness, based on Investigator judgment, within the past 3 months. Planned elective surgery within 30 days of the Final Study Visit. Poor venous access or inability to tolerate venipuncture. History of significant drug hypersensitivity or anaphylaxis. History of hypersensitivity to proteins (e.g., allergy shots). Use of prescription medications on a regular basis. The last use of any prescription medication must have been greater than 5 half-lives for the specific medication or at least 14 days prior to admission (Day -1), whichever is longer. Hormonal contraception is allowed for female subjects. Heterozygous cohorts: Use of prescription medications on a regular basis is not allowed with the following exceptions: Antihypertensives (<3 medications on a stable dose for ≥ 30 days); Statins (dose must be ≤ half the maximum dose; must be on a stable dose ≥3 months); Fibrates (must be on stable dose for ≥3 months); Niacin (must be on stable dose for ≥3 months); Thyroxin (stable dose for ≥ 30 days); The last use of any other prescription medication will need follow the criteria for all other cohorts, as outlined above. Use of prescription medications not listed above may be allowed at the discretion of the Investigator upon consultation with Rhythm. Use of a non-prescription drug and herbal substances during the study (through the Final Study Visit). The last dose of any non-prescription drug must have been taken greater than 5 half-lives for that drug before receiving study drug. Inability to attend all study visits or to comply with protocol requirements including fasting and restrictions on alcohol, caffeine, nicotine and concomitant medication intake. A significant history of drug/solvent abuse within 5 years of screening or a positive test for drugs of abuse test at screening or on Day -1. Positive alcohol (breath test) or nicotine screen at Screening Visit or Day 1 (positive nicotine screen does not apply to heterozygous cohort). History of alcohol abuse (defined as average intake of three or more units of alcohol per day) within 5 years of the Screening Visit. History of tobacco or tobacco product use unless abstinent for at least one year prior to the Screening Visit. This criterion does not apply to heterozygous subjects. Previously randomized and dosed in this study. This criterion does not apply to heterozygous subjects. Any other reason, which in the opinion of the Investigator would confound proper evaluation of the study.", "candidate_expression": "((12-lead electrocardiogram (ECG)) AND (<3 medications) AND (<45 bpm) AND (>126 mg/dL) AND (>140 mg/dL) AND (>90 bpm) AND (ALT) AND (Abnormal) AND (Active) AND (Acute illness or history of illness, which in the opinion of the Investigator, could pose a threat or harm to the subject or obscure interpretation of laboratory test results or interpretation of study data.) AND (Antihypertensives) AND (Any other reason, which in the opinion of the Investigator would confound proper evaluation of the study.) AND (Blood donation) AND (Day -1) AND (Day 1) AND (Elevated) AND (Fasting blood glucose) AND (Fibrates) AND (Final Study Visit) AND (HIV test) AND (Heterozygous) AND (History) AND (Hormonal contraception) AND (Hospitalization) AND (Niacin) AND (Planned) AND (Poor venous access) AND (Positive) AND (Resting heart rate) AND (Screening Visit) AND (Statins) AND (Thyroxin) AND (Use of prescription medications not listed above may be allowed at the discretion of the Investigator upon consultation with Rhythm.) AND (abdominal surgery) AND (abnormalities) AND (abstinent) AND (acute hepatitis) AND (admission) AND (alcohol) AND (alcohol abuse) AND (alcohol test) AND (any non-prescription drug) AND (any prescription medication) AND (as determined by the Investigator) AND (at Screening Visit) AND (at least 14 days prior to admission) AND (at pre-dose) AND (at screening) AND (based on Investigator judgment) AND (breath test) AND (cardiovascular surgery) AND (cervical carcinoma in situ) AND (chronic hepatitis) AND (clinically significant) AND (diabetes) AND (disease cardiovascular) AND (disease endocrine) AND (disease gastrointestinal) AND (disease genitourinary) AND (disease hepatic) AND (disease immunologic) AND (disease pulmonary) AND (disease renal) AND (drug anaphylaxis) AND (drug hypersensitivity) AND (drug/solvent abuse) AND (drugs of abuse test) AND (during the study) AND (elective surgery) AND (except for) AND (excised) AND (experimental devices) AND (experimental drugs) AND (fasting blood glucose) AND (female) AND (for at least one year prior to the Screening Visit) AND (for ≥ 30 days) AND (greater than 5 half-lives before receiving study drug) AND (hematological disease) AND (hepatitis B surface antigen) AND (hepatitis C antibody) AND (herbal substances) AND (history) AND (hypersensitivity to allergy shots) AND (hypersensitivity to proteins) AND (hypertension) AND (in the past 5 years) AND (inability to tolerate venipuncture) AND (intent to donate) AND (laboratory tests) AND (last use greater than 5 half-lives) AND (liver biopsy) AND (major) AND (malignancy) AND (medical condition) AND (medically) AND (medically treated) AND (metabolic disease) AND (neurologic disease) AND (nicotine screen) AND (non-prescription drug) AND (non-surgical illness) AND (on screening) AND (positive) AND (pre-dose) AND (prescription medications) AND (prior to Day 1) AND (psychiatric disease) AND (regular basis) AND (screening) AND (serology) AND (serum creatinine) AND (significant) AND (skin lesion) AND (stable dose) AND (surgery) AND (suspicious for malignancy) AND (testing) AND (the Screening Visit) AND (thoracic surgery) AND (three or more units per day) AND (thyroid stimulating hormone (TSH)) AND (thyroxine (T4)) AND (tobacco product use) AND (tobacco use) AND (treated) AND (treatment) AND (unless) AND (venipuncture) AND (well controlled) AND (within 30 days) AND (within 30 days of the Final Study Visit) AND (within 5 half lives) AND (within 5 years of screening) AND (within 5 years of the Screening Visit) AND (within 60 days after Final Study Visit) AND (within 60 days prior to screening) AND (within the past 3 months) AND (within the past 3 months prior to screening) AND (≤ half the maximum dose) AND (≥ 30 days) AND (≥3 months))"}
{"candidate_id": "LLM07906", "doc_id": "NCT03350815_exc", "case_bucket": "other", "source_criterion": "NA", "candidate_expression": "(EMPTY)"}
{"candidate_id": "LLM07907", "doc_id": "NCT01857167_exc", "case_bucket": "or", "source_criterion": "1. Deny to sign the informed consent; 2. type 1 diabetes; 3. Family history of hypertriglyceridemia or fasting triglyceride>4.56 mmol/L; 4. Have severe liver disease, kidney disease or cancer; 5. Participating in the other clinical trial within 30 days; 6. Other diseases or conditions, for which the doctor of the patients do not agree his or her participating.", "candidate_expression": "((Deny to sign the informed consent;) AND (Other conditions) AND (Other diseases) AND (cancer) AND (fasting triglyceride >4.56 mmol/L) AND (for which the doctor of the patients do not agree his or her participating.) AND (hypertriglyceridemia) AND (kidney disease) AND (liver disease severe) AND (type 1 diabetes))"}
{"candidate_id": "LLM07908", "doc_id": "NCT01770340_exc", "case_bucket": "or", "source_criterion": "IIEF < 21 Operations in the past 6 months which could limit the erectile function Erectile dysfunction in the history or current medication for erectile dysfunction Current involvement in another comparable study.", "candidate_expression": "((Current involvement in another comparable study.) AND (IIEF < 21) AND (Operations in the past 6 months) AND (erectile dysfunction) AND (limit the erectile function) AND ((Erectile dysfunction history) OR (medication current)))"}
{"candidate_id": "LLM07909", "doc_id": "NCT03199560_exc", "case_bucket": "or", "source_criterion": "Women under the age of 18, Clinically positive axillary nodes Neoadjuvant therapy for current breast cancer diagnosis Women with previous SLNBx or axillary node dissection Pregnant women Women with previous radiation above the diaphragm, and below the neck", "candidate_expression": "((Neoadjuvant therapy) AND (Pregnant women) AND (SLNBx) AND (Women) AND (age 18 under) AND (axillary node dissection) AND (axillary nodes positive) AND (breast cancer) AND (radiation previous above the diaphragm below the neck))"}
{"candidate_id": "LLM07910", "doc_id": "NCT02529475_inc", "case_bucket": "other", "source_criterion": "Major subjects of over 40 years (mean age of Meniere's disease 40 to 50 years) Informed consent signed Medical examination performed prior to participation in research Patients without history of inner ear disease Recipient of a French social security scheme", "candidate_expression": "((Medical examination prior to participation in research) AND (years over 40 years) AND NOT (inner ear disease history))"}
{"candidate_id": "LLM07911", "doc_id": "NCT02360631_inc", "case_bucket": "other", "source_criterion": "Self-identified African American Smokes = 1 cigarette per day (cpd) Smoke on = 25 days of the past 30 days Functioning telephone Interested in quitting smoking Interested in taking 3 months of varenicline Willing to complete all study visits", "candidate_expression": "((African American) AND (Interested in quitting smoking) AND (Interested in taking 3 months of varenicline) AND (Smoke = 25 days of the past 30 days) AND (Smokes = 1 cigarette per day) AND (Willing to complete all study visits) AND (quitting smoking Interested))"}
{"candidate_id": "LLM07912", "doc_id": "NCT01665417_inc", "case_bucket": "or", "source_criterion": "Pathologic confirmation of lung adenocarcinoma with measurable disease, defined as at least one lesion that can be accurately measured in at least one dimension (longest diameter to be recorded on CT); Patients must have previously untreated locally advanced or metastatic NSCLC; Patients must have lung cancer with a documented EGFR activating mutation (exon 19 deletion, L858R).", "candidate_expression": "((NSCLC untreated) AND (Pathologic confirmation) AND (lesion at least one can be accurately measured in at least one dimension) AND (lung adenocarcinoma with measurable disease) AND (lung cancer with EGFR activating mutation) AND ((L858R) OR (exon 19 deletion)) AND ((locally advanced) OR (metastatic)))"}
{"candidate_id": "LLM07913", "doc_id": "NCT02649114_exc", "case_bucket": "other", "source_criterion": "current suicidal risk current psychosis ongoing trauma (e.g. current involvement in an abusive relationship).", "candidate_expression": "((involvement in an abusive relationship current) AND (psychosis current) AND (suicidal risk current) AND (trauma ongoing))"}
{"candidate_id": "LLM07914", "doc_id": "NCT02571881_exc", "case_bucket": "or", "source_criterion": "age less than 18 years allergy to study drugs substance misuse other contraindication to used study drugs no informed consent", "candidate_expression": "((age) AND (allergy) AND (contraindication) AND (less than 18 years) AND (study drugs) AND (substance misuse))"}
{"candidate_id": "LLM07915", "doc_id": "NCT03493919_exc", "case_bucket": "or", "source_criterion": "Progressive, unstable or uncontrolled clinical conditions. Hypersensitivity, including allergy, to any component of vaccines, medicinal products or medical equipment whose use is foreseen in this study. Clinical conditions representing a contraindication to intramuscular vaccination and blood draws. Clinical conditions. Systemic administration of corticosteroids (PO/IV/IM) within 90 days prior to informed consent. Administration of antineoplastic and immunomodulating agents or radiotherapy within 90 days prior to informed consent. Received immunoglobulins or any blood products within 180 days prior to informed consent. Received an investigational or non-registered medicinal product within 30 days prior to informed consent. Any other clinical condition that, in the opinion of the investigator, might pose additional risk to the subject due to participation in the study. Any history of meningococcal vaccination or meningococcal and gonorrhoea diseases. Enrolment in any activity requiring a blood donation greater than 50 mL during the period starting 30 days before the first study visit (Day -83, Day -60 or Day -30) or for the duration of the study period. Administration of long-acting immune-modifying drugs at any time during the study period Subjects with blood disorders. Subjects with a history of difficulty in providing blood samples Any antibiotic intake 7 days prior to blood collection. Subjects who donated >450 mL of blood within 60 days prior to any blood collection visits. Subjects who lost >200 mL during a single apheresis or who lost red blood cells on more than one occasion during apheresis within the previous 60 days. Concurrently participating in another clinical study, at any time during the study period, in which the subject has been or will be exposed to an investigational or a non-investigational vaccine/product Ongoing anaemia as indicated by haemoglobin values below the lower limit of the laboratory-specified reference range. If the finger prick method demonstrates an anaemia, no further protocol procedures will be performed, and the subject will be referred for appropriate medical management. The subject may participate in this study following therapy and evidence that the anaemia has been resolved. History of any reaction or hypersensitivity likely to be exacerbated by any component of the vaccines. Pregnant or lactating female. Female planning to become pregnant or planning to discontinue contraceptive precautions. Any confirmed or suspected immunosuppressive or immunodeficiency condition based on medical history and physical examination Family history of congenital or hereditary immunodeficiency. Serious chronic illness. History of chronic alcohol consumption and/or drug abuse.", "candidate_expression": "((Female) AND (anaemia) AND (antibiotic 7 days prior to blood collection) AND (become pregnant planning to) AND (blood disorders) AND (blood donation greater than 50 mL) AND (chronic illness Serious) AND (clinical conditions) AND (component of the vaccines) AND (contraindication) AND (corticosteroids Systemic administration) AND (difficulty in providing blood samples history) AND (donated blood >450 mL within 60 days prior to any blood collection visits) AND (female) AND (haemoglobin below the lower limit of the laboratory-specified reference range) AND (immune-modifying drugs long-acting at any time during the study period) AND (lost red blood cells >200 mL) AND (medicinal product within 30 days prior to informed consent) AND (participating in clinical study Concurrently at any time during the study period) AND ((Pregnant) OR (lactating)) AND ((contraceptive precautions planning to discontinue) OR (planning to become pregnant)) AND ((confirmed) OR (suspected)) AND ((immunodeficiency condition) OR (immunosuppressive condition)) AND ((medical history) OR (physical examination)) AND ((congenital immunodeficiency) OR (hereditary immunodeficiency)) AND ((chronic alcohol consumption) OR (drug abuse)) AND ((blood draws) OR (intramuscular vaccination)) AND ((IM) OR (IV) OR (PO)) AND ((antineoplastic agents) OR (immunomodulating agents) OR (radiotherapy)) AND ((Progressive) OR (uncontrolled) OR (unstable)) AND ((blood products) OR (immunoglobulins)) AND ((investigational) OR (non-registered)) AND ((gonorrhoea diseases) OR (meningococcal diseases) OR (meningococcal vaccination)) AND ((during the period starting 30 days before the first study visit 30 days before the first study visit) OR (for the duration of the study period the study period)) AND ((Hypersensitivity) OR (allergy)) AND ((apheresis more than one occasion within the previous 60 days) OR (apheresis single)) AND ((component of vaccines) OR (medical equipment) OR (medicinal products)) AND ((product) OR (vaccine)) AND ((investigational) OR (non-investigational)) AND ((anaemia Ongoing) OR (finger prick method)) AND ((hypersensitivity) OR (reaction)))"}
{"candidate_id": "LLM07916", "doc_id": "NCT02457442_inc", "case_bucket": "or", "source_criterion": "ASA physical status 1 or 2 Written informed consent Cardiovascular disease Pulmonary disease Liver disease CNS disease Alcohol or drug abuse Chronic intake of CNS active drugs Body mass index > 35 Diabetes mellitus Hypersensitivity or allergy to one of the study drugs", "candidate_expression": "((ASA physical status) AND (Alcohol abuse) AND (Body mass index > 35) AND (CNS active drugs Chronic intake) AND (CNS disease) AND (Cardiovascular disease) AND (Diabetes mellitus) AND (Liver disease) AND (Pulmonary disease) AND (Written informed consent) AND (drug abuse) AND (study drugs) AND ((Hypersensitivity) OR (allergy)) AND ((1) OR (2)))"}
{"candidate_id": "LLM07917", "doc_id": "NCT02456129_inc", "case_bucket": "or", "source_criterion": "Body mass index (BMI): 18 ≤ BMI ≤ 32 kg/m² Postmenopausal state revealed by: Medical history, if applicable (natural menopause at least 12 months prior to first study drug administration; or surgical menopause by bilateral ovariectomy at least 3 months prior to first study drug administration), in addition: in women < 65 years old, follicle stimulating hormone (FSH) > 40 IU/L", "candidate_expression": "((Body mass index (BMI) 18 ≤ BMI ≤ 32 kg/m²) AND (Postmenopausal state) AND (bilateral ovariectomy) AND (follicle stimulating hormone (FSH) > 40 IU/L) AND (natural menopause at least 12 months prior to first study drug administration) AND (surgical menopause at least 3 months prior to first study drug administration) AND (women) AND (years old < 65 years))"}
{"candidate_id": "LLM07918", "doc_id": "NCT02592980_exc", "case_bucket": "or", "source_criterion": "Patients will not be included if they have reached a stable dose of warfarin, liver dysfunction, alcoholism, use of another anticoagulant, use of chemotherapy, or if they do not meet the inclusion criteria", "candidate_expression": "((alcoholism) AND (anticoagulant another) AND (chemotherapy) AND (if they do not meet the inclusion criteria) AND (liver dysfunction) AND (warfarin stable dose))"}
{"candidate_id": "LLM07919", "doc_id": "NCT03208465_exc", "case_bucket": "or", "source_criterion": "Contraindications to empagliflozin, Sitagliptin DPP4 inhibitors or Sodium-glucose cotransporter-2(SGLT2) inhibitors within the previous 4 weeks Insulin requiring diabetes Poor glucose control (HbA1C>10 %) Acute coronary syndrome Stent placement within the previous 6 months Previous coronary artery bypass graft surgery within the previous 6 months Planned revascularization within 6 months Heart failure requiring loop diuretics Severe left ventricular hypertrophy (left ventricular septal wall thickness > 13mm) Significant renal disease manifested by creatinine clearance of < 30 ml/min) Hepatic disease or biliary tract obstruction, or significant hepatic enzyme elevation (alanine transaminase or Aspartate Aminotransferase > 3 times upper limit of normal) Radiopaque material implanted in the chest wall (metal, silicone, etc.) Contraindication to adenosine stress test Any clinically significant abnormality identified at the screening visit, physical examination, laboratory tests, or electrocardiogram which, in the judgment of the Investigator, would preclude safe completion of the study. Patient's pregnant or breast-feeding or child-bearing potential Expected life expectancy < 1 year Unwillingness or inability to comply with the procedures described in this protocol", "candidate_expression": "((< 1 year) AND (< 30 ml/min) AND (> 3 times upper limit of normal) AND (>10 %) AND (Acute coronary syndrome) AND (Any clinically significant abnormality identified at the screening visit, physical examination, laboratory tests, or electrocardiogram which, in the judgment of the Investigator, would preclude safe completion of the study.) AND (Contraindication) AND (Contraindications) AND (Expected life expectancy) AND (HbA1C) AND (Heart failure) AND (Insulin) AND (Planned) AND (Poor glucose control) AND (Previous) AND (Radiopaque material) AND (Severe) AND (Significant) AND (Stent) AND (adenosine stress test) AND (chest wall) AND (coronary artery bypass graft surgery) AND (creatinine clearance) AND (diabetes) AND (left ventricular hypertrophy) AND (loop diuretics) AND (placement) AND (renal disease) AND (revascularization) AND (significant) AND (within 6 months) AND (within the previous 4 weeks) AND (within the previous 6 months) AND ((Sitagliptin) OR (empagliflozin)) AND ((> 13mm) OR (left ventricular septal wall thickness)) AND ((Hepatic disease) OR (biliary tract obstruction) OR (hepatic enzyme elevation)) AND ((Aspartate Aminotransferase) OR (alanine transaminase)) AND ((DPP4 inhibitors) OR (Sodium-glucose cotransporter-2(SGLT2) inhibitors)) AND ((breast-feeding) OR (child-bearing potential) OR (pregnant)))"}
{"candidate_id": "LLM07920", "doc_id": "NCT02056288_exc", "case_bucket": "or", "source_criterion": "Pulseless extremity Compromised neurologic status on exam (specifically assessment of radial, ulnar, and median nerve) Known allergy to local anesthetics (7) Not scheduled for closed reduction with percutaneous pinning under general anesthesia Bleeding diathesis American Society of Anesthesiologist (ASA) status 4 or higher. Sleep apnea by polysomnography", "candidate_expression": "((4 or higher) AND (American Society of Anesthesiologist (ASA) status) AND (Bleeding diathesis) AND (Compromised neurologic status) AND (Not) AND (Pulseless extremity) AND (Sleep apnea) AND (allergy) AND (closed reduction with percutaneous pinning) AND (general anesthesia) AND (local anesthetics) AND (polysomnography) AND (scheduled for) AND ((median nerve) OR (nerve radial) OR (nerve ulnar)))"}
{"candidate_id": "LLM07921", "doc_id": "NCT02562456_exc", "case_bucket": "or", "source_criterion": "severe behavioral issues presence of fistula or abscess near the selected tooth presence of pulp exposure in the selected tooth presence of mobility in the selected tooth", "candidate_expression": "((behavioral issues) AND (mobility) AND (near the selected tooth) AND (pulp exposure) AND (selected tooth) AND (severe) AND ((abscess) OR (fistula)))"}
{"candidate_id": "LLM07922", "doc_id": "NCT02121145_exc", "case_bucket": "or", "source_criterion": "Primary groups: Vaccination against typhoid fever within 5 years before dosing. History of clinical typhoid fever, clinical paratyphoid A or B fever. Immunization with any other vaccine (oral or parenteral) within 4 weeks prior to study start or planned vaccination during the study Current intake of antibiotics or end of antibiotic therapy <8 days before first IMP administration Chronic (longer than 14 days) administration of immunosuppressants or other immune-modifying drugs within 6 months before the first dose of investigational vaccine; oral corticosteroids in dosages of =0.5 mg/kg/d prednisolone or equivalent are excluded; inhaled or topical steroids are allowed Acute or chronic clinically significant gastrointestinal disease", "candidate_expression": "((Immunization with vaccine any other within 4 weeks prior to study start oral parenteral) AND (Primary groups) AND (Vaccination against typhoid fever within 5 years before dosing) AND (antibiotic therapy end of <8 days before first IMP administration longer than 14 days) AND (antibiotics Current) AND (clinical paratyphoid A fever) AND (clinical paratyphoid B fever) AND (clinical typhoid fever) AND (gastrointestinal disease clinically significant Acute chronic) AND (immune-modifying drugs other) AND (immunosuppressants) AND (investigational vaccine) AND (typhoid fever) AND (vaccination planned during the study) AND NOT (oral corticosteroids dosages))"}
{"candidate_id": "LLM07923", "doc_id": "NCT02056301_exc", "case_bucket": "other", "source_criterion": "1) Refusal of epidural catheter 2) Pregnancy 3) Bleeding History 4) Inability to understand how to use the PCA device 5) Medication interfering with blood coagulation 6) Patients allergic to local anesthetics 7) Patient refusal to participate in study 8) Developmental delay", "candidate_expression": "((Bleeding History) AND (Developmental delay) AND (Medication interfering with blood coagulation) AND (Pregnancy) AND (allergic) AND (epidural catheter Refusal) AND (local anesthetics))"}
{"candidate_id": "LLM07924", "doc_id": "NCT01614041_exc", "case_bucket": "or", "source_criterion": "Serious suicidal tendency The score of the sixth item of HAMA =3 The score of HAMD =21 Pregnant or lactating women History of allergic or hypersensitivity to tandospirone Serious or unstable cardiac, renal, neurologic, cerebrovascular, metabolic, or pulmonary disease Secondary anxiety disorders Drug or alcohol dependence within 1 year Patients currently taking benzodiazepine drugs Drivers and dangerous machine operators Participated in other clinical studies in the last 30 days Patients with clinically significant ECG or laboratory abnormalities Patients with a history of epilepsy Patients with abnormal TSH concentration", "candidate_expression": "((=21) AND (=3) AND (Drivers) AND (Drug dependence) AND (ECG) AND (ECG abnormalities) AND (Participated in other clinical studies) AND (Pregnant) AND (Secondary anxiety disorders) AND (Serious) AND (TSH) AND (abnormal) AND (alcohol dependence) AND (allergic) AND (benzodiazepine drugs) AND (cardiac disease) AND (cerebrovascular disease) AND (clinically significant) AND (currently) AND (dangerous machine operators) AND (epilepsy) AND (hypersensitivity) AND (laboratory) AND (laboratory abnormalities) AND (lactating) AND (metabolic disease) AND (neurologic disease) AND (pulmonary disease) AND (renal disease) AND (score of HAMD) AND (score of the sixth item of HAMA) AND (suicidal tendency) AND (tandospirone) AND (the last 30 days) AND (unstable) AND (within 1 year) AND (women))"}
{"candidate_id": "LLM07925", "doc_id": "NCT02546856_inc", "case_bucket": "other", "source_criterion": "Patient with \"de novo\" heart Failure and LVEF <= 40% admitted in hospital, without contraindications for BB prescription with cardiologist up-titration prescription and without having achieved BB target dose previous discharge and signing informed consent.", "candidate_expression": "((<= 40%) AND (BB) AND (LVEF) AND (admitted) AND (contraindications) AND (de novo) AND (heart Failure) AND (hospital) AND (without))"}
```
