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
{"candidate_id": "LLM04151", "doc_id": "NCT02849483_inc", "case_bucket": "other", "source_criterion": "20-70 yrs of age ASA(American Society of Anesthesiologists) physical status class I or II Scheduled for gynecological laparoscopic surgery", "candidate_expression": "((20-70 yrs) AND (ASA physical status class) AND (American Society of Anesthesiologists) AND (I or II) AND (Scheduled) AND (age) AND (gynecological) AND (laparoscopic surgery))"}
{"candidate_id": "LLM04152", "doc_id": "NCT01728194_exc", "case_bucket": "or", "source_criterion": "Psychotic depression by DSM-IV, i.e., presence of delusions with a SCID-R score higher than 2; High suicide risk, i.e. intent or plan to attempt suicide in near future; Presence of any Axis I psychiatric disorder (other than unipolar major depression) or substance abuse; History of psychiatric disorders other than unipolar major depression or generalized anxiety disorder (bipolar disorder, hypomania, and dysthymia are exclusion criteria); Dementia: Diagnosis of dementia by DSM-IV; Mild Cognitive Impairment (MCI); Acute or severe medical illness, i.e., delirium, metastatic cancer, decompensated cardiac, liver or kidney failure, major surgery, stroke or myocardial infarction during the three months prior to entry; or use of drugs known to cause depression, e.g., reserpine, alpha-methyl-dopa, steroids, sympathomimetics withdrawal; Neurological brain disease and/or history of electroconvulsive therapy; History of any use of citalopram or escitalopram during the current episode or need for drugs that may interact with these agents, i.e. drug metabolized by the 2D6 P450 isoenzyme system; Current involvement in psychotherapy; Contraindications to MRI scanning including cardiac pacemaker, metallic objects and metallic implants contraindicating MRI, cardiac stent, claustrophobia; Inability to speak English; Corrected visual acuity < 20/70; Color blindness.", "candidate_expression": "((< 20/70;) AND (Acute) AND (Axis I) AND (Color blindness) AND (Contraindications) AND (Corrected) AND (DSM-IV) AND (Dementia) AND (High) AND (Inability to speak English) AND (MCI) AND (MRI) AND (Mild Cognitive Impairment) AND (Neurological) AND (Psychotic depression) AND (SCID-R score) AND (agents) AND (alpha-methyl-dopa) AND (attempt suicide) AND (bipolar disorder) AND (brain disease) AND (cardiac failure) AND (cardiac pacemaker) AND (cardiac stent) AND (citalopram) AND (claustrophobia) AND (current) AND (decompensated) AND (delirium) AND (delusions) AND (depression) AND (drugs) AND (dysthymia) AND (electroconvulsive therapy) AND (entry) AND (episode) AND (escitalopram) AND (generalized anxiety disorder) AND (higher than 2) AND (hypomania) AND (in near future) AND (intent) AND (kidney failure) AND (liver failure) AND (major surgery) AND (medical illness) AND (metallic implants) AND (metallic objects) AND (metastatic cancer) AND (myocardial infarction) AND (other than) AND (plan to) AND (psychiatric disorder) AND (psychiatric disorders) AND (psychotherapy) AND (reserpine) AND (severe) AND (steroids) AND (stroke) AND (substance abuse) AND (suicide risk) AND (sympathomimetics withdrawal) AND (three months prior to entry) AND (unipolar major depression) AND (visual acuity))"}
{"candidate_id": "LLM04153", "doc_id": "NCT03477851_exc", "case_bucket": "or", "source_criterion": "No consent Spinal anesthesia or sciatic nerve block contraindicated Known intolerance to tramadol or other contraindications for the drug", "candidate_expression": "((No) AND (No consent) AND (Spinal anesthesia) AND (consent) AND (contraindicated) AND (contraindications) AND (intolerance) AND (other) AND (sciatic nerve block) AND (the drug) AND (tramadol))"}
{"candidate_id": "LLM04154", "doc_id": "NCT03380429_exc", "case_bucket": "or", "source_criterion": "Subjects with a known or suspected alcohol or drug abuse which in the opinion of the investigator could interfere with the subject's proper completion of the protocol requirement. History of life threatening asthma: Defined as an asthma episode that required intubation and/or was associated with hypercapnea, respiratory arrest or hypoxic seizures within the last 6 months. A lower respiratory tract infection within 7 days of the screening visit. Concurrent diagnosis of chronic obstructive pulmonary disease (COPD) or other respiratory disorders including active tuberculosis, lung cancer, bronchiectasis, sarcoidosis, lung fibrosis, pulmonary hypertension, interstitial lung diseases or other active pulmonary diseases. History of hypersensitivity/intolerance to any components of the study inhalers (example, lactose, magnesium stearate). In addition, subjects with a history of severe milk protein allergy that, in the opinion of the study physician, contraindicates participation will also be excluded. Historical or current evidence of clinically significant or rapidly progressing or unstable cardiovascular, neurological, cardiovascular, neurological, renal, hepatic, immunological, endocrine (including uncontrolled diabetes or thyroid disease) or hematological abnormalities that are uncontrolled. Significant is defined as any disease that, in the opinion of the investigator, would put the safety of the subject at risk through participation, or which would affect the analysis if the disease/condition exacerbated during the study. Subjects who have ever received treatment with biological based therapy example, omalizumab, mepolizumab, for asthma. Subjects who have received an investigational drug and/or medical device within 30 days of entry into this study (Screening), or within five drug half-lives of the investigational drug, whichever is longer. A subject will not be eligible for this study if he/she is an immediate family member of the participating investigator, sub-investigator, study coordinator, employee of the participating investigator, or any family member of a Propeller Health employee.", "candidate_expression": "((Historical current clinically significant rapidly progressing unstable) AND (Subjects who have received an investigational drug and/or medical device within 30 days of entry into this study (Screening), or within five drug half-lives of the investigational drug, whichever is longer.) AND (Subjects with a known or suspected alcohol or drug abuse which in the opinion of the investigator could interfere with the subject's proper completion of the protocol requirement.) AND (allergy history severe) AND (asthma) AND (asthma episode required intubation) AND (asthma life threatening) AND (bronchiectasis) AND (cardiovascular abnormalities) AND (chronic obstructive pulmonary disease (COPD)) AND (components of the study inhalers) AND (contraindicates participation) AND (diabetes) AND (endocrine abnormalities) AND (hematological abnormalities) AND (hepatic abnormalities) AND (hypercapnea) AND (hypersensitivity) AND (hypoxic seizures) AND (immunological abnormalities) AND (interstitial lung diseases) AND (intolerance) AND (intubation) AND (lactose) AND (lower respiratory tract infection within 7 days of the screening visit screening visit) AND (lung cancer) AND (lung fibrosis) AND (magnesium stearate) AND (mepolizumab) AND (milk protein) AND (neurological abnormalities) AND (omalizumab) AND (pulmonary diseases other active) AND (pulmonary hypertension) AND (renal abnormalities) AND (respiratory arrest) AND (respiratory disorders other) AND (sarcoidosis) AND (thyroid disease) AND (treatment) AND (tuberculosis active))"}
{"candidate_id": "LLM04155", "doc_id": "NCT02490839_inc", "case_bucket": "other", "source_criterion": "Participants having H. pylori related chronic gastritis with/without peptic ulcers who are aged greater than 20 years old and are willing to received eradication therapy.", "candidate_expression": "((aged greater than 20 years old) AND (chronic gastritis H. pylori related) AND (eradication therapy willing to received) AND (peptic ulcers))"}
{"candidate_id": "LLM04156", "doc_id": "NCT03062358_exc", "case_bucket": "or", "source_criterion": "Is currently participating or has participated in a study with an investigational agent or using an investigational device within 4 weeks of the first dose of study medication Has received sorafenib or oxaliplatin-based chemotherapy within 14 days of first dose of study medication Has had esophageal or gastric variceal bleeding within the last 6 months Has clinically apparent ascites on physical examination Has portal vein invasion at the main portal branch (Vp4), inferior vena cava, or cardiac involvement of HCC based on imaging Has had clinically diagnosed hepatic encephalopathy in the last 6 months Has had a solid organ or hematologic transplant Has had prior systemic therapy for HCC in the advanced (incurable) setting other than sorafenib or oxaliplatin-based chemotherapy, prior to start of study medication Has an active autoimmune disease that has required systemic treatment in the past 2 years. Replacement therapy is not considered a form of systemic treatment. Has a diagnosis of immunodeficiency or is receiving systemic steroid therapy or any other form of immunosuppressive therapy within 7 days prior to the first dose of study medication Has received locoregional therapy to liver (transcatheter chemoembolization [TACE], transcatheter embolization [TAE], hepatic arterial infusion [HAI], radiation, radioembolization, or ablation) or other site within 4 weeks prior to the first dose of study medication Has had major surgery to liver or other site within 4 weeks prior to the first dose of study medication Has had a minor surgery ≤7 days prior to the first dose of study medication Has not recovered adequately (i.e., Grade ≤1 or baseline) from the toxicity and/or complications from any intervention prior to study start Has a diagnosed additional malignancy within 3 years prior to first dose of study medication with the exception of curatively treated basal cell carcinoma of the skin, squamous cell carcinoma of the skin and/or curatively resected in situ cancers Has a known history of, or any evidence of, central nervous system (CNS) metastases and/or carcinomatous meningitis Has a history of (non-infectious) pneumonitis that required steroids or current pneumonitis Has an active infection requiring systemic therapy Is pregnant or breast feeding or expecting to conceive or father starting from the first dose of study medication, throughout the study period, and for up to 120 days after the last dose of study medication Has received prior immunotherapy with an anti-Programmed Cell Death Receptor 1 (PD-1), Programmed Cell Death Receptor Ligand 1 (anti-PD-L1), or anti- Programmed Cell Death Receptor Ligand 2 (PD-L2) or has previously participated in clinical studies with pembrolizumab Has a known history of human immunodeficiency virus (HIV) Has untreated active Hepatitis B Has hepatitis C in which participants received therapy for HCV <4 weeks prior to receiving pembrolizumab Has received a live vaccine within 30 days prior to the first dose of study therapy", "candidate_expression": "((30 days prior) AND (<4 weeks prior) AND (HCC) AND (Hepatitis B) AND (ablation) AND (active) AND (additional) AND (ascites) AND (autoimmune disease) AND (chemotherapy) AND (curatively) AND (curatively resected) AND (curatively treated) AND (current) AND (evidence) AND (first dose of study medication) AND (first dose of study therapy) AND (for up to 120 days after the last dose of study medication) AND (hepatic arterial infusion [HAI]) AND (hepatic encephalopathy) AND (hepatitis C) AND (history) AND (human immunodeficiency virus (HIV)) AND (imaging) AND (immunodeficiency) AND (in the last 6 months) AND (in the past 2 years) AND (infection) AND (live vaccine) AND (locoregional therapy) AND (major surgery) AND (malignancy) AND (minor surgery) AND (non-infectious) pneumonitis) AND (other than) AND (oxaliplatin) AND (pembrolizumab) AND (prior) AND (radiation) AND (radioembolization) AND (receiving pembrolizumab) AND (recovered adequately) AND (requiring systemic therapy) AND (resected) AND (sorafenib) AND (sorafenib or oxaliplatin-based) AND (start of study medication) AND (starting from the first dose of study medication) AND (systemic therapy) AND (systemic treatment) AND (the first dose of study medication) AND (the last dose of study medication) AND (the study period) AND (therapy for HCV) AND (throughout the study period) AND (transcatheter chemoembolization [TACE]) AND (transcatheter embolization [TAE]) AND (treated) AND (untreated) AND (with the exception of) AND (within 14 days) AND (within 3 years prior to first dose of study medication) AND (within 4 weeks prior) AND (within 7 days prior) AND (within the last 6 months) AND (≤7 days prior) AND ((Programmed Cell Death Receptor Ligand 1 (anti-PD-L1)) OR (anti- Programmed Cell Death Receptor Ligand 2 (PD-L2)) OR (anti-Programmed Cell Death Receptor 1 (PD-1))) AND ((inferior vena cava) OR (main portal branch (Vp4))) AND ((cardiac involvement) OR (portal vein invasion)) AND ((hematologic transplant) OR (solid organ transplant)) AND ((immunosuppressive therapy) OR (systemic steroid therapy)) AND ((liver) OR (other site)) AND ((basal cell carcinoma of the skin) OR (in situ cancers) OR (squamous cell carcinoma of the skin)) AND ((esophageal variceal bleeding) OR (gastric variceal bleeding)) AND ((carcinomatous meningitis) OR (central nervous system (CNS) metastases)) AND ((pneumonitis) OR (steroids)) AND ((breast feeding) OR (expecting to conceive) OR (expecting to father) OR (pregnant)) AND ((immunotherapy) OR (participated in clinical studies with pembrolizumab)))"}
{"candidate_id": "LLM04157", "doc_id": "NCT01824537_exc", "case_bucket": "or", "source_criterion": "Volunteers must not have been vaccinated against HPV-Gardasil-9 (both partners) Any history of cervical, penile, oral or anal cancers Being pregnant or plan on immediately becoming pregnant", "candidate_expression": "((Any history) AND (HPV-Gardasil-9) AND (anal cancers) AND (cancers cervical) AND (oral cancers) AND (penile cancers) AND (pregnant) AND (pregnant plan on immediately becoming) AND NOT (vaccinated have been))"}
{"candidate_id": "LLM04158", "doc_id": "NCT03518034_exc", "case_bucket": "or", "source_criterion": "Participants with congenital or acquired hypogonadism for whom long-term therapy with placebo would not be medically appropriate Participants with prostate specific antigen (PSA) > 3.0 ng/mL (or 1.5 if on 5-alpha reductase inhibitors) Participants who have been treated with testosterone in the past 6 months and for whom testosterone therapy is contraindicated Confirmed testosterone < 100 ng/dL Body Mass Index (BMI) > 50 Hemoglobin A1c (HbA1C) > 11% Hematocrit (Hct) > 50% Estimated Glomerular Filtration Rate (eGFR) < 30 ml/min History of deep vein thrombosis or pulmonary embolism or prostate cancer or heart failure (Class III and IV).", "candidate_expression": "((5-alpha reductase inhibitors 1.5) AND (Body Mass Index (BMI) > 50) AND (Confirmed testosterone < 100 ng/dL) AND (Estimated Glomerular Filtration Rate (eGFR) < 30 ml/min) AND (Hematocrit (Hct) > 50%) AND (Hemoglobin A1c (HbA1C) > 11%) AND (acquired hypogonadism) AND (congenital hypogonadism) AND (contraindicated) AND (deep vein thrombosis) AND (heart failure Class III Class IV) AND (prostate cancer) AND (prostate specific antigen (PSA) > 3.0 ng/mL) AND (pulmonary embolism) AND (testosterone) AND (testosterone in the past 6 months) AND (testosterone therapy))"}
{"candidate_id": "LLM04159", "doc_id": "NCT00351611_inc", "case_bucket": "other", "source_criterion": "Epilepsy partial seizure subjects. Currently taking 1 to 3 antiepileptic drugs.", "candidate_expression": "((Epilepsy) AND (antiepileptic drugs 1 to 3) AND (partial seizure))"}
{"candidate_id": "LLM04160", "doc_id": "NCT03530124_inc", "case_bucket": "other", "source_criterion": "=32 weeks gestational age at birth =6 weeks postnatal age at randomization Remains hospitalized after birth (has never been discharged home) Treating clinician deems infant eligible to receive 2-month vaccines English- or Spanish-speaking parent(s)/legally authorized representative(s) (LAR(s)) Not planned for discharge within 60 hours of study entry The parent/guardian must be willing and capable of providing permission for their child to participate through the written informed consent process", "candidate_expression": "((2-month vaccines eligible) AND (Not) AND (The parent/guardian must be willing and capable of providing permission for their child to participate through the written informed consent process) AND (discharge planned within 60 hours of study entry study entry) AND (gestational age at birth =32 weeks) AND (hospitalized after birth) AND (postnatal age =6 weeks at randomization))"}
{"candidate_id": "LLM04161", "doc_id": "NCT02334631_exc", "case_bucket": "or", "source_criterion": "Patients with a contraindication to VCE (small bowel strictures, oropharyngeal dysphagia, pregnancy, patients who are not surgical candidates) Endoscopic insertion of video capsule endoscope Inpatient procedures for active GI bleeding Patients with fluid restriction or who are unable to drink up to 900 ml of fluid within 10 minutes prior to the VCE", "candidate_expression": "((Endoscopic insertion) AND (GI bleeding active) AND (Inpatient procedures) AND (VCE) AND (contraindication) AND (video capsule endoscope) AND ((fluid restriction) OR (unable to drink)) AND ((oropharyngeal dysphagia) OR (pregnancy) OR (small bowel strictures) OR NOT (surgical candidates)))"}
{"candidate_id": "LLM04162", "doc_id": "NCT02624908_exc", "case_bucket": "or", "source_criterion": "Type 1 diabetes Known peripheral artery disease Liver enzymes equal or more than 1.5 times the upper limit of normal Chronic heart failure NYHA class III or IV Current haemodialysis or peritoneal dialysis End stage liver disease, defined as acute or chronic liver disease and recent history of one of the following: ascites, encephalopathy, variceal bleeding, bilirubin equal or greater than 2.0 mg/dL, albumin equal or less than 3.5 g/ dL, prothrombin time greater or equal to 4 seconds, INR greater than or equal to 1.7 or prior liver transplant Known or suspected hypersensitivity to trial products or related products Female of child-bearing potential who is pregnant, breast-feeding or intends to become pregnant or is not using adequate contraceptive methods as required by law or local practice. Expected simultaneous participation in any other clinical trial of an investigational medicinal product. Receipt of any investigational medicinal product within 30 days before randomization Current or past (within the last 5 years) malignant neoplasms (except basal cell and squamous cell skin carcinoma) Any condition that in the investigator's opinion would make the subject unable to adhere to the trial visit schedule and procedures Known history of non-compliance to treatment.", "candidate_expression": "((Any condition that in the investigator's opinion would make the subject unable to adhere to the trial visit schedule and procedures) AND (Chronic heart failure) AND (End stage liver disease) AND (Female of child-bearing potential who is pregnant, breast-feeding or intends to become pregnant or is not using adequate contraceptive methods as required by law or local practice.) AND (Liver enzymes equal or more than 1.5 times the upper limit of normal) AND (NYHA class III or IV) AND (Type 1 diabetes) AND (hypersensitivity) AND (malignant neoplasms within the last 5 years) AND (peripheral artery disease) AND ((acute liver disease) OR (chronic liver disease)) AND ((INR greater than or equal to 1.7) OR (albumin equal or less than 3.5 g/ dL) OR (ascites) OR (bilirubin equal or greater than 2.0 mg/dL) OR (encephalopathy) OR (liver transplant prior) OR (prothrombin time greater or equal to 4 seconds) OR (variceal bleeding)) AND ((related products) OR (trial products)) AND ((Known) OR (suspected)) AND ((Current) OR (past)) AND ((basal cell carcinoma) OR (squamous cell skin carcinoma)) AND ((haemodialysis) OR (peritoneal dialysis)))"}
{"candidate_id": "LLM04163", "doc_id": "NCT03187639_inc", "case_bucket": "other", "source_criterion": "Aged over 18 Primary symptom of chest pain No contraindication to CTA Willing and able to provide written informed consent", "candidate_expression": "((Aged) AND (CTA) AND (No) AND (Primary symptom) AND (Willing and able to provide written informed consent) AND (chest pain) AND (contraindication) AND (over 18))"}
{"candidate_id": "LLM04164", "doc_id": "NCT00749112_inc", "case_bucket": "or", "source_criterion": "Age: > or = 16 years Weight: more than 40 Kg Autoimmune Hemolytic anemia with clinical and biochemical evidence of hemolysis refractory to treatment, in relapse or steroids dependant Idiopathic thrombocytopenic purpura with platelet counts < 50,000, refractory to treatment, in relapse or steroids dependant", "candidate_expression": "((Age > or = 16 years) AND (Autoimmune Hemolytic anemia) AND (Idiopathic thrombocytopenic purpura) AND (Weight more than 40 Kg) AND (hemolysis evidence clinical biochemical evidence refractory to treatment) AND (platelet counts < 50,000) AND (steroids) AND (treatment) AND ((in relapse) OR (steroids dependant)) AND ((in relapse) OR (refractory to treatment) OR (steroids dependant)))"}
{"candidate_id": "LLM04165", "doc_id": "NCT02797548_exc", "case_bucket": "or", "source_criterion": "Acute coronary syndrome within 1 month Heart failure NYHA III to IV Contraindication to Aspirin On anticoagulant therapy Emergent surgery Cardiac surgery High bleeding risk surgeries, e.g., Intra-cranial surgery, Intra-spinal surgery, Retinal surgery Pregnancy or breast-feeding Life expectancy less than 1year", "candidate_expression": "((Acute coronary syndrome) AND (Aspirin) AND (Cardiac surgery) AND (Contraindication) AND (Emergent surgery) AND (Heart failure) AND (High bleeding risk surgeries) AND (III to IV) AND (Life expectancy) AND (NYHA) AND (anticoagulant therapy) AND (less than 1year) AND (within 1 month) AND ((Intra-cranial surgery) OR (Intra-spinal surgery) OR (Retinal surgery)) AND ((Pregnancy) OR (breast-feeding)))"}
{"candidate_id": "LLM04166", "doc_id": "NCT02580630_inc", "case_bucket": "or", "source_criterion": "Midsubstance pain in the achilles tendon Symptoms for at least 3 months Ultrasound scanning at the first visit shows thickness of the achilles tendon above 7 mm or 20% thicker than the contralateral. Patient can read and understand danish", "candidate_expression": "((Midsubstance pain achilles tendon) AND (Symptoms for at least 3 months) AND (Ultrasound scanning at the first visit) AND (thickness of the achilles tendon above 7 mm 20% thicker than the contralateral))"}
{"candidate_id": "LLM04167", "doc_id": "NCT03089086_exc", "case_bucket": "other", "source_criterion": "Previous anaphylaxis following any component of Bexsero vaccine Previous receipt of meningococcal B vaccine (Bexsero) Known pregnancy", "candidate_expression": "((Bexsero) AND (Bexsero vaccine) AND (Previous) AND (anaphylaxis) AND (meningococcal B vaccine) AND (pregnancy))"}
{"candidate_id": "LLM04168", "doc_id": "NCT02979561_exc", "case_bucket": "or", "source_criterion": "Signs of hemodynamic instability (i.e. systolic blood pressure <100 mm Hg.St. or episode of systolic blood pressure fall for =40 mm Hg. / or heart rate > 110 lasting more than 15 min) or need for ventilatory support within 12 hours prior to randomisation. The indication for oral anticoagulation, associated with others disease. malignant neoplasm of any location Contraindications to warfarin or pradaxa according to Russian Instructions for medical use of these drugs Indications for concomitant treatment with antiplatelet agents Any stroke within 6 months before randomization Intracranial hemorrhage in anamnesis Active bleeding, bleeding diathesis. Clinically significant bleeding within the last 30 days. Trauma or extensive surgery within 1 month before randomization or surgery planned in the next 6 months after randomization. Intracranial pathology: tumor, arteriovenous fistula or aneurysm. Gastrointestinal bleeding in the previous 3 months. Gastric ulcer or duodenal ulcer with clinical manifestations or endoscopically identified acute ulcer without signs of scarring during previous 30 days. Uncontrolled hypertension (systolic blood pressure> 180 mm Hg. and / or diastolic blood pressure> 100 mm.hg in patients receiving antihypertensive drugs). Pregnancy, lactation. Life expectancy <6 months. Clinically significant liver disease. Creatinine clearance (estimated by Cockcroft-Gault) <30 ml / min. hemoglobin level <90 g/l), thrombocytopenia <100x10^9 / L. Patients who, in the opinion of the researcher, are not suitable for inclusion in the study, for example, due to the low likelihood of doctor's recommendations following. Long-term use of NSAIDs Current participation in another clinical study. Allergic to contrast substance or radioisotope drugs used in procedures to assess endpoints of the study, which according to researchers, may be a contraindication to the implementation of these research methods.", "candidate_expression": "((<100 mm Hg.St.) AND (<100x10^9 / L) AND (<30 ml / min) AND (<6 months) AND (<90 g/l) AND (=40 mm Hg) AND (> 100 mm.hg) AND (> 110) AND (> 180 mm Hg) AND (Active) AND (Allergic) AND (Clinically significant) AND (Cockcroft-Gault) AND (Contraindications) AND (Creatinine clearance) AND (Gastrointestinal bleeding) AND (Indications) AND (Intracranial hemorrhage) AND (Intracranial pathology) AND (Life expectancy) AND (Long-term use) AND (NSAIDs) AND (Pregnancy) AND (Russian Instructions for medical use) AND (Uncontrolled) AND (anamnesis) AND (antihypertensive drugs) AND (antiplatelet agents) AND (bleeding) AND (clinical manifestations) AND (concomitant) AND (during previous 30 days) AND (endoscopically) AND (endoscopically identified) AND (hemoglobin level) AND (hypertension) AND (in the next 6 months after randomization) AND (in the previous 3 months) AND (indication for) AND (lactation) AND (lasting more than 15 min) AND (liver disease) AND (malignant) AND (need for) AND (neoplasm) AND (oral anticoagulation) AND (planned) AND (signs of scarring) AND (stroke) AND (surgery) AND (thrombocytopenia) AND (within 1 month before randomization) AND (within 12 hours prior to randomisation) AND (within 6 months before randomization) AND (within the last 30 days) AND (without) AND ((hemodynamic instability) OR (ventilatory support)) AND ((pradaxa) OR (warfarin)) AND ((bleeding) OR (bleeding diathesis)) AND ((Trauma) OR (extensive surgery)) AND ((aneurysm) OR (arteriovenous fistula) OR (tumor)) AND ((Gastric ulcer) OR (acute ulcer) OR (duodenal ulcer)) AND ((heart rate) OR (systolic blood pressure) OR (systolic blood pressure fall)) AND ((diastolic blood pressure) OR (systolic blood pressure)) AND ((contrast substance) OR (radioisotope drugs)))"}
{"candidate_id": "LLM04169", "doc_id": "NCT02900443_exc", "case_bucket": "or", "source_criterion": "Overlap syndrome with Primary Sclerosing Cholangitis (PSC) or Primary Biliary Cholangitis (PBC) (Paris criteria, strong positive Anti-Mitochondrial Antibodies (AMA), past liver biopsy or cholangiographic findings compatible with PBC or PSC). Presentation with acute liver failure, defined as presence of hepatic encephalopathy and coagulopathy (INR > 1.5) Current treatment with prednisone/prednisolone and/or immunosuppressive medication for an indication other than autoimmune hepatitis Current systemic infection Other clinically significant medical conditions that could interfere with the trial If female of childbearing potential: known pregnancy, or unwilling to practice anticontraceptive measures. History of noncompliance with medical regimens, or patients who are considered to be potentially unreliable or unable to participate Mental instability or incompetence, such that the validity of informed consent or compliance with the trial is uncertain", "candidate_expression": "((AMA) AND (Anti-Mitochondrial Antibodies strong positive) AND (History of noncompliance with medical regimens, or patients who are considered to be potentially unreliable or unable to participate) AND (INR > 1.5) AND (Mental instability or incompetence, such that the validity of informed consent or compliance with the trial is uncertain) AND (Overlap syndrome) AND (PBC) AND (PSC) AND (Paris criteria,) AND (Primary Biliary Cholangitis) AND (Primary Sclerosing Cholangitis) AND (acute liver failure) AND (cholangiographic findings) AND (coagulopathy) AND (f female of childbearing potential: known pregnancy, or unwilling to practice anticontraceptive measures) AND (hepatic encephalopathy) AND (immunosuppressive medication) AND (indication) AND (liver biopsy) AND (prednisolone) AND (prednisone) AND (systemic infection) AND NOT (autoimmune hepatitis))"}
{"candidate_id": "LLM04170", "doc_id": "NCT03097068_inc", "case_bucket": "other", "source_criterion": "Diagnosis of diabetes mellitus Best corrected visual acuity 20/32 - 20/320 Diabetic macular edema involving the center of the macula Optical coherence tomography central subfield thickness of at least 250 microns", "candidate_expression": "((20/32 - 20/320) AND (Best corrected visual acuity) AND (Diabetic macular edema) AND (Optical coherence tomography central subfield thickness) AND (at least 250 microns) AND (center of the macula) AND (diabetes mellitus))"}
{"candidate_id": "LLM04171", "doc_id": "NCT02894645_inc", "case_bucket": "other", "source_criterion": "Confirmed diagnosis of non-Burkitt B-lineage ALL 1 to 17 years of age (before 18th birthday) Renal function within normal range for age Liver function within normal range for age Able to participate in the full 2 years of treatment", "candidate_expression": "((Able to participate) AND (Liver function within normal range for age) AND (Renal function within normal range for age) AND (age 1 to 17 years) AND (non-Burkitt B-lineage ALL Confirmed) AND (treatment full 2 years))"}
{"candidate_id": "LLM04172", "doc_id": "NCT03034096_inc", "case_bucket": "or", "source_criterion": "Lobectomy or pneumonectomy Esophagectomy Radical (total) cystectomy Pancreatectomy Partial hepatectomy Hyperthermic intraperitoneal chemotherapy (HIPEC) Gastrectomy (subtotal or total) Cholecystectomy or bile duct resection", "candidate_expression": "((Cholecystectomy) AND (Esophagectomy) AND (Gastrectomy) AND (HIPEC) AND (Hyperthermic intraperitoneal chemotherapy) AND (Lobectomy) AND (Pancreatectomy) AND (Partial hepatectomy) AND (Radical cystectomy) AND (bile duct resection) AND (pneumonectomy) AND (subtotal) AND (total) AND (total cystectomy))"}
{"candidate_id": "LLM04173", "doc_id": "NCT02942303_exc", "case_bucket": "or", "source_criterion": "Patients with previous periorbital/forehead surgery Patients who plucked the upper eyebrow margin Patients with eyebrow tatoos Patients with upper face botulinum toxin injection in the past 12 months Patients with resorbable upper face fillers injection in the past 12 months Patients with previous permanent upper face fillers injection Pregnant patients Lactating patients Patients with preexisting neuromuscular conditions (myasthenia gravis, Eaton Lambert syndrome) Patients using medication that could potentiate the effect of botulinum (ex: aminoglycoside antibiotics) Patients with sensitivity to botulinum toxin or human albumin", "candidate_expression": "((Lactating) AND (Pregnant) AND (aminoglycoside antibiotics) AND (botulinum) AND (botulinum toxin injection upper face in the past 12 months) AND (eyebrow tatoos) AND (medication) AND (neuromuscular conditions) AND (permanent fillers injection upper face) AND (plucked the upper eyebrow margin) AND (potentiate the effect) AND (resorbable fillers injection upper face in the past 12 months) AND (sensitivity) AND ((forehead surgery) OR (periorbital surgery)) AND ((Eaton Lambert syndrome) OR (myasthenia gravis)) AND ((botulinum toxin) OR (human albumin)))"}
{"candidate_id": "LLM04174", "doc_id": "NCT03008005_inc", "case_bucket": "other", "source_criterion": "Able to give informed consent Right-handed Age between 18-50 years old, Physically and neurologically healthy [confirmed by a comprehensive medical history] Current PTSD diagnosis", "candidate_expression": "((Able to give informed consent) AND (Age) AND (Current) AND (PTSD) AND (Right-handed) AND (between 18-50 years old) AND (comprehensive medical history) AND (healthy Physically) AND (neurologically healthy))"}
{"candidate_id": "LLM04175", "doc_id": "NCT01491763_exc", "case_bucket": "or", "source_criterion": "Any other variety of LAL Patients with a history of coronary artery disease, valvular or hypertensive heart disease Patients with chronic liver disease Patients with chronic respiratory failure Renal failure not due to LAL Patients with positive HIV status No serious neurological abnormalities due to LAL Impact on overall severe (grade 3 or 4 of the WHO scale) not attributable to the LAL Pregnant or breastfeeding initial blast crisis CML", "candidate_expression": "((CML) AND (HIV status) AND (LAL) AND (No) AND (Renal failure) AND (blast crisis) AND (chronic liver disease) AND (chronic respiratory failure) AND (due to) AND (history) AND (neurological abnormalities) AND (not) AND (other variety) AND (positive) AND (serious) AND ((Pregnant) OR (breastfeeding)) AND ((coronary artery disease) OR (heart disease valvular) OR (hypertensive heart disease)))"}
```
