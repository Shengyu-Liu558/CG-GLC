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
{"candidate_id": "LLM05401", "doc_id": "NCT01996436_exc", "case_bucket": "or", "source_criterion": "Inability to obtain consent from patient or patients kin Pregnant women less than 18 years of age of more than 80 years of age Hunt Hess Grade 5 SAH", "candidate_expression": "((Hunt Hess Grade 5) AND (Inability to obtain consent from patient or patients kin) AND (Pregnant women) AND (SAH) AND (age less than 18 years) AND (age more than 80 years))"}
{"candidate_id": "LLM05402", "doc_id": "NCT00122070_exc", "case_bucket": "or", "source_criterion": "Are pregnant or lactating. Have participated in any other studies involving investigational products within 30 days prior to entry into this study. Are undergoing an acute withdrawal syndrome from drugs or alcohol. Have an Axis I diagnosis of Schizophrenia, Schizoaffective Disorder, Schizophreniform Disorder or Bipolar I Disorder as diagnosed by the Structured Clinical Interview for DSM-IV Axis I Disorders (SCID-I), and pertinent subsequent for ruling out exclusionary diagnoses. Have an unstable medical disorder as determined by physical examination or laboratory testing. The primary investigator will be responsible for making this judgment based on the above. Had an unsatisfactory response to a previous adequate trial of quetiapine as judged by a study investigator. Patients cannot begin psychotherapy during the study period, but may continue if started prior to the study. Patients who are currently receiving quetiapine therapy may not undergo a washout period and then restart quetiapine in the study.", "candidate_expression": "((Have participated in any other studies involving investigational products within 30 days prior to entry into this study) AND (Structured Clinical Interview for DSM-IV Axis I Disorders (SCID-I)) AND (acute withdrawal syndrome) AND ((Bipolar I Disorder) OR (Schizoaffective Disorder) OR (Schizophrenia) OR (Schizophreniform Disorder)) AND ((lactating) OR (pregnant)) AND ((alcohol) OR (drugs)))"}
{"candidate_id": "LLM05403", "doc_id": "NCT02589977_exc", "case_bucket": "or", "source_criterion": "Exclusion Criteria: coronary artery disease, diabetes mellitus, contraindications to cardiac magnetic resonance imaging (CMR), weight >350 lbs, inability to lie flat for imaging, anemia, contraindications to regadenoson or aminophylline HEALTHY: known cardiovascular disease, cardiac risk factors or use of cardiac medications HYPERTENSIVE: known cardiovascular disease or risk factors aside from hypertension or use of cardiac medications HFpEF: prior history of LVEF below 50%, acute decompensated HF, moderate or greater valvular disease, significant cardiac arrhythmias, pericardial disease, congenital heart disease, primary pulmonary hypertension", "candidate_expression": "((HEALTHY) AND (HFpEF) AND (HYPERTENSIVE) AND (LVEF prior history of below 50%) AND (aminophylline) AND (anemia) AND (cardiac arrhythmias significant) AND (cardiac magnetic resonance imaging (CMR)) AND (cardiac medications) AND (cardiac risk factors) AND (cardiovascular disease) AND (cardiovascular risk factors) AND (congenital heart disease) AND (contraindications) AND (coronary artery disease) AND (decompensated HF acute moderate greater) AND (diabetes mellitus) AND (inability to lie flat for imaging) AND (pericardial disease) AND (primary pulmonary hypertension) AND (regadenoson) AND (valvular disease) AND (weight >350 lbs) AND NOT (cardiovascular risk factors from hypertension))"}
{"candidate_id": "LLM05404", "doc_id": "NCT02315287_exc", "case_bucket": "or", "source_criterion": "Contraindication to sitagliptin or metformin or thiazolidinedione Pregnant or breast feeding women Type 1 diabetes, gestational diabetes, or secondary forms of diabetes Not appropriate for oral antidiabetic agent Medication which affect glycemic control Disease which affect efficacy and safety of drugs Any major illness (Liver disease, Renal failure, Heart disease, Cancer, etc)", "candidate_expression": "((Contraindication) AND (Disease) AND (Medication) AND (affect glycemic control) AND (major illness) AND (oral antidiabetic agent) AND NOT (appropriate) AND ((affect efficacy) OR (safety of drugs)) AND ((metformin) OR (sitagliptin) OR (thiazolidinedione)) AND ((Cancer) OR (Heart disease) OR (Liver disease) OR (Renal failure)) AND ((Pregnant) OR (breast)) AND ((Type 1 diabetes) OR (gestational diabetes) OR (secondary forms of diabetes)))"}
{"candidate_id": "LLM05405", "doc_id": "NCT03366779_inc", "case_bucket": "or", "source_criterion": "Age 18 to 75 years old (male or female). Patients with posterior or posterolateral disc herniations at one level between L1 and S1 with radiographic confirmation of neural compression using CT and/or MRI. At least six (6) weeks of failed, conservative treatment prior to surgery, or requires immediate surgery to prevent permanent disability. Minimum posterior disc height of 5mm at the index level(s). Lower back pain and/or sciatica with or without spinal claudication. Oswestry Questionnaire score of at least 40/100 at baseline. VAS leg pain of at least 40/100 at baseline. Psychosocially, mentally and physically able to fully comply with the clinical protocol and willing to adhere to follow-up schedule and requirements.", "candidate_expression": "((18 to 75 years old) AND (Age) AND (At least six (6) weeks) AND (Minimum of 5mm) AND (Oswestry Questionnaire score) AND (Psychosocially, mentally and physically able to fully comply with the clinical protocol and willing to adhere to follow-up schedule and requirements.) AND (VAS leg pain) AND (at baseline) AND (at least 40/100) AND (conservative) AND (disc herniations) AND (failed) AND (immediate) AND (index level(s)) AND (neural compression) AND (one level between L1 and S1) AND (permanent disability) AND (posterior disc height) AND (prevent) AND (prior to surgery) AND (radiographic) AND (radiographic confirmation) AND (spinal claudication) AND ((CT) OR (MRI)) AND ((surgery) OR (treatment)) AND ((Lower back pain) OR (sciatica)) AND ((female) OR (male)) AND ((posterior) OR (posterolateral)))"}
{"candidate_id": "LLM05406", "doc_id": "NCT03088280_inc", "case_bucket": "other", "source_criterion": "Primary kidney transplant recipients, adults", "candidate_expression": "((Primary) AND (adults) AND (kidney transplant))"}
{"candidate_id": "LLM05407", "doc_id": "NCT02867618_inc", "case_bucket": "or", "source_criterion": "Phase I: Patients must have histologically confirmed R/R NHL or HL (defined by WHO criteria). Patients with chronic lymphocytic leukemia (CLL) and small lymphocytic lymphoma (SLL) are eligible. In addition, patients with NHL other than diffuse large B cell lymphomas (DLBCL) must have received at least 2 prior therapies. Patients with DLBCL and HL will be eligible if there is no available standard therapy. Phase II: Patients must have histologically confirmed R/R NHL (as defined by WHO criteria). Patients with NHL other than diffuse large B cell lymphomas (DLBCL) must have received at least 2 prior therapies. Patients with DLBCL will be eligible if there is no available standard therapy. Must have received front line chemotherapy. No upper limit for the number of prior therapies Evaluable Disease in the Phase I, and measurable disease in the Phase II Age > 18 years ECOG performance status < 2 Patients must have adequate organ and marrow function Adequate Contraception Ability to understand and the willingness to sign a written informed consent document", "candidate_expression": "((< 2) AND (> 18 years) AND (Ability to understand and the willingness to sign a written informed consent document) AND (Adequate) AND (Age) AND (Contraception) AND (DLBCL) AND (Disease) AND (ECOG performance status) AND (NHL) AND (R/R) AND (WHO criteria) AND (adequate) AND (at least 2) AND (chemotherapy) AND (confirmed) AND (diffuse large B cell lymphomas (DLBCL)) AND (front line) AND (histologically) AND (in the Phase I) AND (in the Phase II) AND (marrow function) AND (no) AND (organ function) AND (other than) AND (prior) AND (standard therapy) AND (therapies) AND ((chronic lymphocytic leukemia (CLL)) OR (small lymphocytic lymphoma (SLL))) AND ((DLBCL) OR (HL)) AND ((HL) OR (NHL)) AND ((Evaluable) OR (measurable)))"}
{"candidate_id": "LLM05408", "doc_id": "NCT02894372_exc", "case_bucket": "other", "source_criterion": "Purulent infection Refusal to participate Allergy to tested material", "candidate_expression": "((Allergy) AND (Purulent infection) AND (Refusal to participate) AND (tested material))"}
{"candidate_id": "LLM05409", "doc_id": "NCT03351608_exc", "case_bucket": "or", "source_criterion": "Has any clinically significant condition or situation (eg, anatomical malformation that complicates intubation) other than the condition being studied that, in the opinion of the investigator, would interfere with the trial evaluations or optimal participation in the trial. Has a neuromuscular disorder that may affect NMB and/or trial assessments. Is dialysis-dependent or has (or is suspected of having) severe renal insufficiency (defined as estimated glomerular filtration rate (eGFR) <30 ml/min). Has or is suspected of having a family or personal history of malignant hyperthermia. Has or is suspected of having an allergy to study treatments or its/their excipients, to opioids/opiates, muscle relaxants or their excipients, or other medication(s) used during general anesthesia. Has received or is planned to receive toremifene and/or fusidic acid via IV administration within 24 hours before or within 24 hours after administration of study treatment. Has been previously treated with sugammadex or has participated in a sugammadex clinical trial. Is currently participating in or has participated in an interventional clinical trial with an investigational compound or device within 30 days of signing the informed consent/assent for this current trial.", "candidate_expression": "((allergy) AND (anatomical malformation) AND (estimated glomerular filtration rate (eGFR) <30 ml/min) AND (general anesthesia) AND (malignant hyperthermia) AND (neuromuscular disorder) AND (sugammadex) AND NOT (the condition being studied) AND ((affect NMB) OR (affect trial assessments)) AND ((dialysis-dependent) OR (severe renal insufficiency)) AND ((condition) OR (situation)) AND ((family) OR (personal history)) AND ((excipients) OR (medication other during general anesthesia) OR (muscle relaxants) OR (opiates) OR (opioids) OR (study treatments)) AND ((fusidic acid) OR (toremifene)) AND ((within 24 hours after administration of study treatment administration of study treatment) OR (within 24 hours before administration of study treatment administration of study treatment)) AND ((participated in clinical trial) OR (sugammadex)) AND ((currently participating in an interventional clinical trial) OR (has participated in an interventional clinical trial)) AND ((device) OR (investigational compound)) AND ((within 30 days of signing the informed assent signing the informed assent) OR (within 30 days of signing the informed consent signing the informed consent)) AND ((interfere with optimal participation) OR (interfere with the trial evaluations)))"}
{"candidate_id": "LLM05410", "doc_id": "NCT03223909_inc", "case_bucket": "or", "source_criterion": ">18 to < 90 years old Both sexes Mild to moderate tear film dysfunction clinical diagnose TBUT > 5 sec. and < 10 sec. Schirmer: > 4 mm and < 14 mm OSDI < 30 points Corneal staining < grade III on the Oxford scale Availability to go to each revision when indicated.", "candidate_expression": "((Availability to go to each revision when indicated.) AND (Both sexes) AND (Corneal staining < grade III) AND (OSDI < 30 points) AND (Schirmer > 4 mm and < 14 mm) AND (TBUT > 5 sec. and < 10 sec) AND (old >18 to < 90 years) AND (tear film dysfunction) AND ((Mild) OR (moderate)))"}
{"candidate_id": "LLM05411", "doc_id": "NCT00862446_inc", "case_bucket": "other", "source_criterion": "Infants in the newborn intensive care unit TPN cholestasis of at least 2.5 mg/dl Anticipated TPN treatment for at least one month signed informed consent", "candidate_expression": "((Infants) AND (TPN cholestasis) AND (TPN treatment) AND (at least 2.5 mg/dl) AND (for at least one month) AND (newborn intensive care unit) AND (signed informed consent))"}
{"candidate_id": "LLM05412", "doc_id": "NCT03493919_exc", "case_bucket": "or", "source_criterion": "Progressive, unstable or uncontrolled clinical conditions. Hypersensitivity, including allergy, to any component of vaccines, medicinal products or medical equipment whose use is foreseen in this study. Clinical conditions representing a contraindication to intramuscular vaccination and blood draws. Clinical conditions. Systemic administration of corticosteroids (PO/IV/IM) within 90 days prior to informed consent. Administration of antineoplastic and immunomodulating agents or radiotherapy within 90 days prior to informed consent. Received immunoglobulins or any blood products within 180 days prior to informed consent. Received an investigational or non-registered medicinal product within 30 days prior to informed consent. Any other clinical condition that, in the opinion of the investigator, might pose additional risk to the subject due to participation in the study. Any history of meningococcal vaccination or meningococcal and gonorrhoea diseases. Enrolment in any activity requiring a blood donation greater than 50 mL during the period starting 30 days before the first study visit (Day -83, Day -60 or Day -30) or for the duration of the study period. Administration of long-acting immune-modifying drugs at any time during the study period Subjects with blood disorders. Subjects with a history of difficulty in providing blood samples Any antibiotic intake 7 days prior to blood collection. Subjects who donated >450 mL of blood within 60 days prior to any blood collection visits. Subjects who lost >200 mL during a single apheresis or who lost red blood cells on more than one occasion during apheresis within the previous 60 days. Concurrently participating in another clinical study, at any time during the study period, in which the subject has been or will be exposed to an investigational or a non-investigational vaccine/product Ongoing anaemia as indicated by haemoglobin values below the lower limit of the laboratory-specified reference range. If the finger prick method demonstrates an anaemia, no further protocol procedures will be performed, and the subject will be referred for appropriate medical management. The subject may participate in this study following therapy and evidence that the anaemia has been resolved. History of any reaction or hypersensitivity likely to be exacerbated by any component of the vaccines. Pregnant or lactating female. Female planning to become pregnant or planning to discontinue contraceptive precautions. Any confirmed or suspected immunosuppressive or immunodeficiency condition based on medical history and physical examination Family history of congenital or hereditary immunodeficiency. Serious chronic illness. History of chronic alcohol consumption and/or drug abuse.", "candidate_expression": "((30 days before the first study visit) AND (7 days prior to blood collection) AND (>200 mL) AND (>450 mL) AND (Concurrently) AND (Family history) AND (Female) AND (History) AND (Hypersensitivity) AND (IM) AND (IV) AND (Ongoing) AND (PO) AND (Pregnant) AND (Progressive) AND (Serious) AND (Systemic administration) AND (allergy) AND (anaemia) AND (antibiotic) AND (antineoplastic agents) AND (any blood collection visits) AND (apheresis) AND (at any time during the study period) AND (become pregnant) AND (below the lower limit of the laboratory-specified reference range) AND (blood collection) AND (blood disorders) AND (blood donation) AND (blood draws) AND (blood products) AND (chronic alcohol consumption) AND (chronic illness) AND (clinical conditions) AND (component of the vaccines) AND (component of vaccines) AND (confirmed) AND (congenital immunodeficiency) AND (contraceptive precautions) AND (contraindication) AND (corticosteroids) AND (difficulty in providing blood samples) AND (donated blood) AND (drug abuse) AND (during the period starting 30 days before the first study visit) AND (female) AND (finger prick method) AND (for the duration of the study period) AND (gonorrhoea diseases) AND (greater than 50 mL) AND (haemoglobin) AND (hereditary immunodeficiency) AND (history) AND (hypersensitivity) AND (immune-modifying drugs) AND (immunodeficiency condition) AND (immunoglobulins) AND (immunomodulating agents) AND (immunosuppressive condition) AND (informed consent) AND (intramuscular vaccination) AND (investigational) AND (lactating) AND (likely to be exacerbated by any component of the vaccines) AND (long-acting) AND (lost red blood cells) AND (medical equipment) AND (medical history) AND (medicinal product) AND (medicinal products) AND (meningococcal diseases) AND (meningococcal vaccination) AND (more than one occasion) AND (non-investigational) AND (non-registered) AND (participating in clinical study) AND (physical examination) AND (planning to) AND (planning to become pregnant) AND (planning to discontinue) AND (product) AND (radiotherapy) AND (reaction) AND (single) AND (suspected) AND (the previous 60 days) AND (the study period) AND (uncontrolled) AND (unstable) AND (vaccine) AND (whose use is foreseen in this study) AND (within 180 days prior to informed consent) AND (within 30 days prior to informed consent) AND (within 60 days prior to any blood collection visits) AND (within 90 days prior to informed consent) AND (within the previous 60 days))"}
{"candidate_id": "LLM05413", "doc_id": "NCT02714725_inc", "case_bucket": "or", "source_criterion": "Adult patients aged (>18), males and females, undergoing elective coronary artery bypass graft (CABG) surgery with cardiopulmonary bypass (CPB).", "candidate_expression": "((CABG) AND (CPB) AND (aged >18) AND (cardiopulmonary bypass) AND (females) AND (males) AND (surgery coronary artery bypass graft elective))"}
{"candidate_id": "LLM05414", "doc_id": "NCT02536976_exc", "case_bucket": "or", "source_criterion": "Known or suspected alcohol or substance abuse in the preceding 12 months. Women who are pregnant or breastfeeding. Women of childbearing potential (WOCP) who are not using at least one method of contraception. Patients with severe renal impairment (CLcr = 29 mL/min, or eGFR = 29 mL/min/1.73 m2), or moderate or severe hepatic impairment (Child-Pugh classes B or C). Patients with bladder outlet obstruction (BOO) that, in the opinion of the study urologist, would expose them to risk of urinary retention during treatment with mirabegron. Patients treated with drugs metabolized by the CYP2D6 pathway. Patients with supine systolic blood pressure (SBP) = 180 mm Hg, or diastolic blood pressure (DBP) = 110 mm Hg. Clinically significant, uncontrolled cardiac arrhythmia, unstable angina, congestive heart failure (NYHA Class 3 or 4), or history of myocardial infarction in the preceding 2 years. History of cancer in the preceding 2 years other than successfully treated, non-metastatic, squamous cell or basal cell carcinoma, or cervical cancer in situ. Any major urological procedure in the preceding 90 days. Any major surgical procedure in the preceding 30 days. Previously treated with mirabegron within 60 days prior to the baseline visit (Visit 2), or previously having failed treatment with mirabegron regardless of duration and timing of treatment. Current or previous, within the 60 days preceding the baseline visit (Visit 2), treatment with antimuscarinic agents for OAB symptoms; and, willingness to not use antimuscarinic agents for the duration of the study. Currently receiving any other investigational drug or having received an investigational drug within the 60 days preceding the baseline visit (Visit 2). Any condition or laboratory test result, which, in the opinion of the Investigator or the Study Urologist, might result in an increased risk to the patient, or would affect their participation in the study. Any patient who, in the opinion of the Investigator, is not a good candidate for the study or will not be able to follow study procedures.", "candidate_expression": "((BOO) AND (CLcr = 29 mL/min) AND (Child-Pugh classes B C) AND (Currently receiving any other investigational drug or having received an investigational drug within the 60 days preceding the baseline visit (Visit 2)) AND (DBP) AND (NYHA Class 3 4) AND (OAB symptoms) AND (SBP) AND (Women of childbearing potential (WOCP) who are not using at least one method of contraception) AND (Women who are pregnant or breastfeeding) AND (alcohol abuse) AND (antimuscarinic agents within the 60 days preceding the baseline visit) AND (basal cell carcinoma) AND (bladder outlet obstruction risk of urinary retention) AND (cancer preceding 2 years) AND (carcinoma squamous cell) AND (cardiac arrhythmia uncontrolled) AND (cervical cancer in situ) AND (congestive heart failure) AND (diastolic blood pressure = 110 mm Hg) AND (eGFR = 29 mL/min/1.73 m2 moderate) AND (hepatic impairment severe) AND (major surgical procedure preceding 30 days) AND (major urological procedure preceding 90 days) AND (mirabegron) AND (mirabegron within 60 days prior to the baseline visit) AND (myocardial infarction preceding 2 years) AND (renal impairment severe) AND (substance abuse) AND (systolic blood pressure supine = 180 mm Hg) AND (unstable angina) AND (willingness to not use antimuscarinic agents for the duration of the study))"}
{"candidate_id": "LLM05415", "doc_id": "NCT02749617_inc", "case_bucket": "other", "source_criterion": "Patients with diagnosis of multiple myeloma according to criteria of the International Myeloma Working Group Patients in whom a LEN-DEX-based treatment regimen is indicated Adult patients ≥ 19 years of age who are able to freely provide informed consent", "candidate_expression": "((Adult) AND (DEX) AND (LEN) AND (LEN-DEX-based) AND (able to freely provide informed consent) AND (age) AND (criteria of the International Myeloma Working Group) AND (is indicated) AND (multiple myeloma) AND (treatment regimen) AND (≥ 19 years))"}
{"candidate_id": "LLM05416", "doc_id": "NCT03325023_exc", "case_bucket": "or", "source_criterion": "Ovarian cancer, adrenal gland tumor, endometrial cancer, cervical cancer, breast cancer Congenital adrenal hyperplasia (17-OH-progesterone> 2.5 ng / mL) Clinically diagnosed Cushing's disease, acromegaly, gigantism Type I or II diabetes Unexplained bleeding from the genital tract Hormone treatment within the last 2 months", "candidate_expression": "((17-OH-progesterone > 2.5 ng / mL) AND (Congenital adrenal hyperplasia) AND (Hormone) AND (Hormone treatment within the last 2 months) AND (Unexplained bleeding genital tract) AND ((Ovarian cancer) OR (adrenal gland tumor) OR (breast cancer) OR (cervical cancer) OR (endometrial cancer)) AND ((Cushing's disease) OR (acromegaly) OR (gigantism)) AND ((Type I diabetes) OR (Type II diabetes)))"}
{"candidate_id": "LLM05417", "doc_id": "NCT02254668_inc", "case_bucket": "other", "source_criterion": "Patients with heart transplantation Patient with coronary artery disease Age between 18 and 80 years", "candidate_expression": "((Age) AND (between 18 and 80 years) AND (coronary artery disease) AND (heart transplantation))"}
{"candidate_id": "LLM05418", "doc_id": "NCT03013790_exc", "case_bucket": "or", "source_criterion": "Patients with head trauma or Neurosurgical intervention Patients <65 years of age Patients with an expected life expectancy <48 hours Blind patients Patients with a seizure history Patients with uncontrolled hypertension Patients with a supratheraputic (>3.0) INR Patients on strong CYP1A2 inhibitors: ciprofloxacin, fluvoxamine, methoxsalen, ofloxacin, primaquine Patients who do not speak English or Spanish", "candidate_expression": "((Blind) AND (INR supratheraputic >3.0) AND (age <65 years) AND (expected life expectancy <48 hours) AND (seizure history) AND (strong CYP1A2 inhibitors) AND (uncontrolled hypertension) AND ((ciprofloxacin) OR (fluvoxamine) OR (methoxsalen) OR (ofloxacin) OR (primaquine)) AND ((Neurosurgical intervention) OR (head trauma)) AND ((speak English) OR (speak Spanish)))"}
{"candidate_id": "LLM05419", "doc_id": "NCT02525991_inc", "case_bucket": "or", "source_criterion": "Male and female patients between the ages of 18-65 years, inclusive Patients (or legal representative) willing and able to provide written Informed Consent Form. Psychiatric patients already diagnosed of schizophrenia or bipolar disorder, according to the Diagnostic and Statistical Manual of Mental Disorders- IV, Diagnostic and Statistical Manual of Mental Disorders- V or International Code of Disease criteria. Patients with an on-going agitation episode, or with a previous one within the 6 months prior to screening, attended and managed in the hospital setting. Previously treated with ADASUVE® with a positive outcome (responders) according to (CGI-I) scale (defined as having a CGI-I score of 1 or 2 at 2 hours after administration of the inhalation) Patients free of active respiratory disease such as acute respiratory signs/symptoms (e.g., wheezing) or with active airways disease (asthma, chronic obstructive pulmonary disease or emphysema). Requirement of family or other caregiver support at study investigator criteria (defined as a patient's relative or caregiver (male or female) = 80 year old, who spend = 3 consecutive hours with patient, with good physical and psychological health status and without physical limitations, reading and writing educational level and able to understand and follow the study procedures). Availability of patient's medical records data about the previous treatment with ADASUVE® at hospital setting. If a female is of childbearing potential and sexually active (except if female is surgically sterile or post-menopausal with history of no menses for at least 24 months), patient must be non-lactating and non-pregnant (with a negative pregnancy test result at baseline visit) and have to agree to use a medically acceptable and effective birth control method throughout the study and for one week following the end of the study.", "candidate_expression": "((1 or 2) AND (18-65 years) AND (2 hours after administration of the inhalation)) AND (ADASUVE) AND (CGI-I score) AND (Diagnostic and Statistical Manual of Mental Disorders- IV) AND (Diagnostic and Statistical Manual of Mental Disorders- V) AND (If a female is of childbearing potential and sexually active (except if female is surgically sterile or post-menopausal with history of no menses for at least 24 months), patient must be non-lactating and non-pregnant (with a negative pregnancy test result at baseline visit) and have to agree to use a medically acceptable and effective birth control method throughout the study and for one week following the end of the study) AND (International Code of Disease criteria) AND (Male) AND (Patients (or legal representative) willing and able to provide written Informed Consent Form) AND (active) AND (acute respiratory signs) AND (acute respiratory symptoms) AND (administration of the inhalation)) AND (ages) AND (agitation episode) AND (airways disease) AND (asthma) AND (bipolar disorder) AND (chronic obstructive pulmonary disease) AND (emphysema) AND (female) AND (free) AND (respiratory disease) AND (schizophrenia) AND (screening) AND (wheezing) AND (within the 6 months prior to screening))"}
{"candidate_id": "LLM05420", "doc_id": "NCT02118467_inc", "case_bucket": "other", "source_criterion": "Age greater than or equal to 18 years old Requirement for vasoactive drugs via a central venous catheter for the treatment of shock. Shock will be defined as mean arterial pressure less than 70 mmHg or systolic blood pressure less than 100 mmHg despite administration of at least 1000 mL of crystalloid or 500 mL of colloid, unless there is an elevation in the central venous pressure to > 12 mmHg or in the pulmonary artery occlusion pressure to > 14 mmHg coupled with signs of tissue hypoperfusion (e.g. altered mental state, mottled skin, urine output < 0.5 mL/kg body weight for one hour, or a serum lactate level of > 2 mmol per liter).", "candidate_expression": "((Age) AND (central venous catheter) AND (greater than or equal to 18 years old) AND (less than 100 mmHg) AND (less than 70 mmHg) AND (mean arterial pressure) AND (shock) AND (systolic blood pressure) AND (vasoactive drugs))"}
{"candidate_id": "LLM05421", "doc_id": "NCT03648021_inc", "case_bucket": "or", "source_criterion": "18-year or older patients Patient hospitalized in neuro-critical care for: Arachnoid hemorrhage Intra parenchymatous hematoma stroke Acute brain Severe injury Post-operative complication of an act of neurosurgery or programmed neuroradiology Sedation and mechanical ventilation planned > 2 days Monitoring of intracranial temperature and pressure by intraparenchymal sensor (Sophysa®) Brain temperature > 38.5°C for more than 30 minutes", "candidate_expression": "((Acute brain Severe injury) AND (Arachnoid hemorrhage) AND (Brain temperature > 38.5°C for more than 30 minutes) AND (Post-operative complication of an act of neurosurgery of an act of programmed neuroradiology) AND (Sedation) AND (Sophysa®) AND (hematoma Intra parenchymatous) AND (hospitalized) AND (intracranial pressure) AND (intracranial temperature) AND (intraparenchymal sensor) AND (mechanical ventilation) AND (neuro-critical care) AND (neuroradiology) AND (neurosurgery) AND (old 18-year or older) AND (stroke))"}
{"candidate_id": "LLM05422", "doc_id": "NCT02789111_inc", "case_bucket": "other", "source_criterion": "Major spine surgery scheduled as part of clinical care 18-80 years", "candidate_expression": "((Major spine surgery) AND (years 18-80))"}
{"candidate_id": "LLM05423", "doc_id": "NCT02019160_exc", "case_bucket": "or", "source_criterion": "Children who are uncooperative and difficult to manage, have major systemic diseases, or are on long-term medication will be excluded.", "candidate_expression": "((difficult to manage) AND (major) AND (medication long-term) AND (systemic diseases major) AND (uncooperative))"}
{"candidate_id": "LLM05424", "doc_id": "NCT02842424_inc", "case_bucket": "or", "source_criterion": "A positive history of chronic claudication, Exercise-limiting claudication established by history and direct observation during a screening walking test administered by the evaluating vascular surgeon, Arterial occlusive disease per ankle Brachial index measurements and/or other imaging modalities, Stable blood pressure regimen, stable lipid regimen, stable diabetes regimen and risk factor control for 6 weeks.", "candidate_expression": "((Arterial occlusive disease) AND (Exercise-limiting claudication) AND (Stable) AND (blood pressure regimen) AND (chronic claudication) AND (diabetes regimen) AND (direct observation) AND (for 6 weeks) AND (history) AND (lipid regimen) AND (positive history) AND (risk factor control) AND (screening walking test) AND (stable) AND ((ankle Brachial index measurements) OR (imaging modalities)))"}
{"candidate_id": "LLM05425", "doc_id": "NCT02203019_inc", "case_bucket": "or", "source_criterion": "Men and women 18-89 years old with the diagnosis of sepsis (as specified below) within the previous 24 hours who require mechanical ventilation, and provide informed consent either personally or by an authorized representative.", "candidate_expression": "((mechanical ventilation) AND (old 18-89 years) AND (provide informed consent either personally or by an authorized representative) AND (sepsis within the previous 24 hours) AND ((Men) OR (women)))"}
```
