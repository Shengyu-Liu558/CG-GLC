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
{"candidate_id": "LLM06926", "doc_id": "NCT01908465_inc", "case_bucket": "or", "source_criterion": "Irritable Bowel Syndrome (IBS) (ROME III criteria): subtype with diarrhea or mixed form age 18-65 years", "candidate_expression": "((Irritable Bowel Syndrome (IBS) ROME III criteria) AND (age 18-65 years) AND ((diarrhea) OR (mixed form)))"}
{"candidate_id": "LLM06927", "doc_id": "NCT02557412_exc", "case_bucket": "or", "source_criterion": "Apnea-hypopnea index of less than 5 h-1 or greater than 30 h-1. Predominance of central apneas and hypopneas, defined as more than 25% of all respiratory events. Professional drivers, risk profession or respiratory failure (according to criteria of the clinical pathway for diagnosis and treatment of sleep-disordered breathing). Very excessive daytime sleepiness (Epworth Sleepiness Scale> 18). Morbid obesity (BMI> 40 kg / m2). Prior treatment with CPAP.", "candidate_expression": "((> 18) AND (> 40 kg / m2) AND (Apnea-hypopnea index) AND (BMI) AND (CPAP) AND (Epworth Sleepiness Scale) AND (Morbid obesity) AND (Predominance) AND (Prior) AND (Professional drivers) AND (Very excessive) AND (all respiratory events) AND (central apneas and hypopneas) AND (criteria of the clinical pathway for diagnosis and treatment of sleep-disordered breathing) AND (daytime sleepiness) AND (less than 5 h-1 or greater than 30 h-1) AND (more than 25%) AND (respiratory failure) AND (risk profession))"}
{"candidate_id": "LLM06928", "doc_id": "NCT02441179_inc", "case_bucket": "or", "source_criterion": "1. Patients ≥ 18 years-old from \"Instituto Teletón Santiago\" and \"Hospital Clínico Mutual de seguridad\". 2. C5 to T12 spinal cord injury, classified as ISNCSCI grades C and D 3. Traumatic and non-traumatic, non-progressive lesions 4. Onset > 6 months 5. Ability to ambulate with or without assistive devices 6. Ability to follow verbal or visual commands 7. Signed informed consent", "candidate_expression": "((ISNCSCI grades C and D) AND (Signed informed consent) AND (lesions Traumatic non-traumatic non-progressive Onset > 6 months) AND (spinal cord injury C5 to T12) AND (years-old ≥ 18 years) AND ((Hospital Clínico Mutual de seguridad) OR (Instituto Teletón Santiago)) AND ((Ability to ambulate with assistive devices) OR (Ability to ambulate without assistive devices)) AND ((Ability to follow verbal commands) OR (Ability to follow visual commands)))"}
{"candidate_id": "LLM06929", "doc_id": "NCT02764476_inc", "case_bucket": "or", "source_criterion": "Adults 18-65 years, who are diagnosed with functional neurologic symptom or conversion disorder. If diagnosis of seizure type then video EEG with diagnosis confirmed by board-certified neurologist with subspecialty training in epilepsy and clinical neurophysiology using the criteria of the International Classification of the Epilepsies is required. If diagnosis of motor type, documented and clinically established levels of diagnostic certainty (Williams,1995) confirmed by 2 neurologists is required. Participants must have at least one symptom per month in the month prior to enrollment Fluency in English spoken language", "candidate_expression": "((18-65 years 18-65 years) AND (Adults) AND (conversion disorder) AND (criteria of the International Classification of the Epilepsies) AND (functional neurologic symptom) AND (motor type) AND (seizure type) AND (symptom at least one per month in the month prior to enrollment) AND (video EEG))"}
{"candidate_id": "LLM06930", "doc_id": "NCT03056391_exc", "case_bucket": "or", "source_criterion": "1. Patient or relatives unable or unwilling to give informed consent 2. Contraindication or allergy to paracetamol or artesunate therapy 3. Known cirrhosis, or >6 standard alcoholic drinks/day 4. Pregnancy", "candidate_expression": "((Patient or relatives unable or unwilling to give informed consent) AND (Pregnancy) AND ((artesunate) OR (paracetamol)) AND ((>6 standard alcoholic drinks/day) OR (cirrhosis)) AND ((Contraindication) OR (allergy)))"}
{"candidate_id": "LLM06931", "doc_id": "NCT03663387_inc", "case_bucket": "or", "source_criterion": "Male and female subjects between 40-85 years old will be enrolled. Younger subjects are not included as the risk for brain amyloid lesions is too low All subjects will speak English as their first language or demonstrate proficiency in English (defined as reaching a scaled score of > 11 on the WAIS vocabulary test). All subjects will have normal cognition at baseline: a Clinical Dementia Rating CDR=0, Global Deterioration Scale GDS<2. All subjects will be in good general health and able to participate in the LP and imaging exams. This determination is made by the study neurologist and reviewed at a consensus meeting for each subject.", "candidate_expression": "((Clinical Dementia Rating CDR =0) AND (Global Deterioration Scale GDS <2) AND (LP) AND (Male) AND (WAIS vocabulary test > 11) AND (able to participate) AND (female) AND (good general health) AND (imaging exams) AND (normal cognition at baseline) AND (old between 40-85 years) AND (proficiency in English) AND (speak English first language))"}
{"candidate_id": "LLM06932", "doc_id": "NCT02321839_exc", "case_bucket": "or", "source_criterion": "Total lesion area of >12 DA or >30.5 mm2 The existence of subretinal hemorrhage area constituting =50% of total lesion area The existence of scar or fibrosis area constituting =50% of total lesion area The existence of RPE tear Prior treatment for wet AMD History of vitrectomy surgery, submacular surgery, or other surgical intervention for AMD The pregnant or lactating woman", "candidate_expression": "((=50% of total lesion area) AND (>12 DA) AND (>30.5 mm2) AND (AMD) AND (Prior) AND (RPE tear) AND (Total lesion area) AND (fibrosis area) AND (lactating) AND (other) AND (pregnant) AND (scar area) AND (submacular surgery) AND (subretinal hemorrhage area) AND (surgical intervention) AND (treatment) AND (vitrectomy surgery) AND (woman))"}
{"candidate_id": "LLM06933", "doc_id": "NCT00609531_inc", "case_bucket": "or", "source_criterion": "Ambulatory status (outpatient) at time of consent Age 10-55 years Clinical diagnosis of Autism Spectrum Disorder IQ greater than or equal to 70 Score greater than 8 on Children's Yale-Brown Obsessive Compulsive Scale Free of psychoactive medication for at least: one month for fluoxetine; two weeks for other SSRIs and neuroleptics; and five days for stimulants prior to MRI scanning [excepting stable doses (greater than three months duration) of anticonvulsant medication for seizure disorder]", "candidate_expression": "((10-55 years) AND (Age) AND (Ambulatory status) AND (Autism Spectrum Disorder) AND (Children's Yale-Brown Obsessive Compulsive Scale) AND (Clinical diagnosis) AND (Free of) AND (IQ) AND (SSRIs) AND (anticonvulsant medication) AND (at least five days) AND (at least one month) AND (at least two weeks) AND (at time of consent) AND (excepting) AND (fluoxetine) AND (greater than 8) AND (greater than or equal to 70) AND (greater than three months) AND (neuroleptics) AND (outpatient) AND (prior to MRI scanning) AND (psychoactive medication) AND (seizure disorder) AND (stable doses) AND (stimulants))"}
{"candidate_id": "LLM06934", "doc_id": "NCT02072811_inc", "case_bucket": "other", "source_criterion": "Adult acute myeloid leukemia Age: ≥18 and ≤ 60 Clinical condition of the patient allows to carry out induction therapy: ECOG performance status: ≤ 2 and the Hematopoietic Cell Transplant-Co-morbidity Index (HCT-I): ≤3 Informed consent to participate in the study (ICF signed) The second early induction start criteria is in addition to the listed above, the percentage of the blasts on the level >10% on 7th day.", "candidate_expression": "((Adult acute myeloid leukemia) AND (Age ≥18 and ≤ 60) AND (ECOG performance status ≤ 2) AND (Hematopoietic Cell Transplant-Co-morbidity Index (HCT-I) ≤3) AND (Informed consent to participate in the study (ICF signed)) AND (percentage of the blasts >10% on 7th day))"}
{"candidate_id": "LLM06935", "doc_id": "NCT03493919_exc", "case_bucket": "or", "source_criterion": "Progressive, unstable or uncontrolled clinical conditions. Hypersensitivity, including allergy, to any component of vaccines, medicinal products or medical equipment whose use is foreseen in this study. Clinical conditions representing a contraindication to intramuscular vaccination and blood draws. Clinical conditions. Systemic administration of corticosteroids (PO/IV/IM) within 90 days prior to informed consent. Administration of antineoplastic and immunomodulating agents or radiotherapy within 90 days prior to informed consent. Received immunoglobulins or any blood products within 180 days prior to informed consent. Received an investigational or non-registered medicinal product within 30 days prior to informed consent. Any other clinical condition that, in the opinion of the investigator, might pose additional risk to the subject due to participation in the study. Any history of meningococcal vaccination or meningococcal and gonorrhoea diseases. Enrolment in any activity requiring a blood donation greater than 50 mL during the period starting 30 days before the first study visit (Day -83, Day -60 or Day -30) or for the duration of the study period. Administration of long-acting immune-modifying drugs at any time during the study period Subjects with blood disorders. Subjects with a history of difficulty in providing blood samples Any antibiotic intake 7 days prior to blood collection. Subjects who donated >450 mL of blood within 60 days prior to any blood collection visits. Subjects who lost >200 mL during a single apheresis or who lost red blood cells on more than one occasion during apheresis within the previous 60 days. Concurrently participating in another clinical study, at any time during the study period, in which the subject has been or will be exposed to an investigational or a non-investigational vaccine/product Ongoing anaemia as indicated by haemoglobin values below the lower limit of the laboratory-specified reference range. If the finger prick method demonstrates an anaemia, no further protocol procedures will be performed, and the subject will be referred for appropriate medical management. The subject may participate in this study following therapy and evidence that the anaemia has been resolved. History of any reaction or hypersensitivity likely to be exacerbated by any component of the vaccines. Pregnant or lactating female. Female planning to become pregnant or planning to discontinue contraceptive precautions. Any confirmed or suspected immunosuppressive or immunodeficiency condition based on medical history and physical examination Family history of congenital or hereditary immunodeficiency. Serious chronic illness. History of chronic alcohol consumption and/or drug abuse.", "candidate_expression": "((30 days before the first study visit) AND (7 days prior to blood collection) AND (>200 mL) AND (>450 mL) AND (Concurrently) AND (Family history) AND (Female) AND (History) AND (Ongoing) AND (Serious) AND (Systemic administration) AND (anaemia) AND (antibiotic) AND (any blood collection visits) AND (at any time during the study period) AND (become pregnant) AND (below the lower limit of the laboratory-specified reference range) AND (blood collection) AND (blood disorders) AND (blood donation) AND (chronic illness) AND (clinical conditions) AND (component of the vaccines) AND (contraindication) AND (corticosteroids) AND (difficulty in providing blood samples) AND (donated blood) AND (female) AND (greater than 50 mL) AND (haemoglobin) AND (history) AND (immune-modifying drugs) AND (informed consent) AND (likely to be exacerbated by any component of the vaccines) AND (long-acting) AND (lost red blood cells) AND (medicinal product) AND (more than one occasion) AND (participating in clinical study) AND (planning to) AND (planning to discontinue) AND (single) AND (the previous 60 days) AND (the study period) AND (whose use is foreseen in this study) AND (within 180 days prior to informed consent) AND (within 30 days prior to informed consent) AND (within 60 days prior to any blood collection visits) AND (within 90 days prior to informed consent) AND (within the previous 60 days) AND ((Pregnant) OR (lactating)) AND ((contraceptive precautions) OR (planning to become pregnant)) AND ((confirmed) OR (suspected)) AND ((immunodeficiency condition) OR (immunosuppressive condition)) AND ((medical history) OR (physical examination)) AND ((congenital immunodeficiency) OR (hereditary immunodeficiency)) AND ((chronic alcohol consumption) OR (drug abuse)) AND ((blood draws) OR (intramuscular vaccination)) AND ((IM) OR (IV) OR (PO)) AND ((antineoplastic agents) OR (immunomodulating agents) OR (radiotherapy)) AND ((Progressive) OR (uncontrolled) OR (unstable)) AND ((blood products) OR (immunoglobulins)) AND ((investigational) OR (non-registered)) AND ((gonorrhoea diseases) OR (meningococcal diseases) OR (meningococcal vaccination)) AND ((during the period starting 30 days before the first study visit) OR (for the duration of the study period)) AND ((Hypersensitivity) OR (allergy)) AND ((apheresis)) AND ((component of vaccines) OR (medical equipment) OR (medicinal products)) AND ((product) OR (vaccine)) AND ((investigational) OR (non-investigational)) AND ((anaemia) OR (finger prick method)) AND ((hypersensitivity) OR (reaction)))"}
{"candidate_id": "LLM06936", "doc_id": "NCT02830360_inc", "case_bucket": "or", "source_criterion": "Prior Myocardial Infarction and Sustained monomorphic VT documented on 12-lead ECG or rhythm strip terminated by pharmacologic means or DC cardioversion =3 episodes of VT treated with antitachycardia pacing (ATP), at least one of which was symptomatic = 5 episodes of VT treated with antitachycardia pacing (ATP) regardless of symptoms =1 appropriate ICD shocks, =3 VT episodes within 24 hours", "candidate_expression": "((12-lead ECG) AND (ATP) AND (DC cardioversion) AND (ICD shocks =1) AND (Myocardial Infarction) AND (VT 3 episodes symptomatic) AND (VT 3 episodes within 24 hours) AND (VT 5 episodes) AND (antitachycardia pacing) AND (monomorphic VT Sustained) AND (pharmacologic means) AND (rhythm strip))"}
{"candidate_id": "LLM06937", "doc_id": "NCT03344887_inc", "case_bucket": "other", "source_criterion": "All patients (excluding neonates) requiring one or more allogeneic RBC transfusions for the treatment of anemia will be included.", "candidate_expression": "((RBC transfusions) AND (allogeneic) AND (anemia) AND (excluding) AND (neonates) AND (one or more) AND (requiring) AND (treatment))"}
{"candidate_id": "LLM06938", "doc_id": "NCT02894372_exc", "case_bucket": "other", "source_criterion": "Purulent infection Refusal to participate Allergy to tested material", "candidate_expression": "((Allergy tested material) AND (Purulent infection) AND (Refusal to participate) AND (tested material))"}
{"candidate_id": "LLM06939", "doc_id": "NCT03260881_inc", "case_bucket": "or", "source_criterion": "T2DM as defined by American Diabetes Association (ADA) criteria Adult patients with T2DM who are indicated to receive liraglutide, not as first-line therapy, in addition to diet and exercise to improve glycemic control Hemoglobin A1c (HbA1c) = 9% Age = 18 years old Body mass index (BMI) = 27 Kg/m2 and/or waist circumference = 102 cm (40 inches) in men and 88 cm (35 inches) in women, respectively. Clinically and angiographically stable CAD who requires CABG as part of the standard medical care, as CAD does not represent a contraindication for using liraglutide. The stability of the CAD further warranties that study patients will not be exposed to higher risk by using liraglutide", "candidate_expression": "((35 inches) AND (40 inches) AND (88 cm) AND (= 102 cm) AND (= 18 years old) AND (= 27 Kg/m2) AND (= 9%) AND (Adult) AND (Age) AND (American Diabetes Association (ADA) criteria) AND (Body mass index (BMI)) AND (CABG) AND (CAD) AND (Clinically stable) AND (Hemoglobin A1c (HbA1c)) AND (T2DM) AND (angiographically stable) AND (first-line therapy) AND (indicated to receive) AND (liraglutide) AND (men) AND (not) AND (requires) AND (waist circumference) AND (women))"}
{"candidate_id": "LLM06940", "doc_id": "NCT00425789_exc", "case_bucket": "or", "source_criterion": "Patients will be excluded if they have known middle ear disease, chronic lung disease or claustrophobia", "candidate_expression": "((chronic lung disease) AND (claustrophobia) AND (middle ear disease))"}
{"candidate_id": "LLM06941", "doc_id": "NCT02968602_inc", "case_bucket": "or", "source_criterion": "DSM-IV or DSM-5 diagnosis of schizophrenia or schizoaffective disorder Male or Female Age: 18 to 65 years Caucasian or Non-Caucasian Smoke at least 10 cigarettes daily Urine cotinine level ? 100 ng/ml (NicAlert(r) reading ? 3) Agrees to wear a head mounted display (HMD) for up to 45 minutes Able to complete the Evaluation to Sign Consent (ESC) with minimum score of 80%", "candidate_expression": "((Age 18 to 65 years) AND (Agrees to wear for up to 45 minutes) AND (Caucasian) AND (Evaluation to Sign Consent (ESC) Able to complete minimum score of 80%) AND (Female) AND (Male) AND (NicAlert(r) ? 3) AND (Non-Caucasian) AND (Smoke at least 10 cigarettes daily) AND (Urine cotinine level ? 100 ng/ml) AND (head mounted display (HMD)) AND (schizoaffective disorder) AND (schizophrenia DSM-IV DSM-5))"}
{"candidate_id": "LLM06942", "doc_id": "NCT02394158_exc", "case_bucket": "or", "source_criterion": "Established pre-existing diabetes (including unrecognised diabetes defined as a fasting plasma glucose = 7.0mmol/L and/ or HbA1c = 48mmol/mol); Contraindications to metformin therapy (creatinine = 130µmol/L/ alanine transaminase = 2.0 x upper limit normal/ previous intolerance to metformin) Planned continued antenatal care/ delivery at centre not included in trial Planned fast for cultural/ religious reasons e.g. Ramadan", "candidate_expression": "((Contraindications) AND (HbA1c = 48mmol/mol)) AND (Planned continued antenatal care/ delivery at centre not included in trial) AND (alanine transaminase = 2.0 x upper limit normal) AND (creatinine = 130µmol/L/) AND (diabetes) AND (fasting plasma glucose = 7.0mmol/L) AND (intolerance) AND (metformin))"}
{"candidate_id": "LLM06943", "doc_id": "NCT02907554_inc", "case_bucket": "or", "source_criterion": "Male and females aged 18 to 70 years Brain death Male and females aged 18 to 70 years Indication of kidney transplantation Informed consent", "candidate_expression": "((Brain death) AND (Informed consent) AND (Male) AND (aged 18 to 70 years) AND (females) AND (kidney transplantation Indication) AND ((Male) OR (females)))"}
{"candidate_id": "LLM06944", "doc_id": "NCT01118871_exc", "case_bucket": "or", "source_criterion": "current alcohol abuse or drug dependence pregnancy active opportunistic infection or significant co-morbidities current prohibited concomitant medication a likelihood of diminished response to any of the study treatment arms, in the opinion of the investigator, based on HIV genotypic resistance testing", "candidate_expression": "((a likelihood of diminished response to any of the study treatment arms, in the opinion of the investigator, based on HIV genotypic resistance testing) AND (alcohol abuse) AND (co-morbidities) AND (drug dependence) AND (medication current prohibited concomitant) AND (opportunistic infection significant) AND (pregnancy))"}
{"candidate_id": "LLM06945", "doc_id": "NCT00867958_inc", "case_bucket": "other", "source_criterion": "1. Patient is over 18 years old. 2. Patient is scheduled for a non-emergency procedure. 3. Subject signs and dates a written informed consent form (ICF) and indicates an understanding of the study procedures.", "candidate_expression": "((3. Subject signs and dates a written informed consent form (ICF) and indicates an understanding of the study procedures.) AND (non-emergency procedure scheduled non-emergency) AND (years old over 18 years old))"}
{"candidate_id": "LLM06946", "doc_id": "NCT01205334_inc", "case_bucket": "or", "source_criterion": "Histopathological verification of glioblastoma multiforme (GBM: WHO grade IV) in remission (Group A) or with active disease (Group B). CMV-positive GBM CMV seropositive Life expectancy 6 weeks or greater Karnofsky/Lansky score 50 or greater Patient or parent/guardian capable of providing informed consent Bilirubin less than 1.5x upper limit of normal, AST less than 3x upper limit of normal, serum creatinine less than 1.5x normal and Hgb 8.0 g/dL or greater Pulse oximetry of 90% or greater on room air Sexually active patients must be willing to utilize one of the more effective birth control methods for 6 months after the CTL infusion. The male partner should use a condom. Patients should have been off other investigational antineoplastic therapy for one month prior to entry in this study. Informed consent explained to, understood by and signed by patient/guardian. Patient/guardian given copy of informed consent.", "candidate_expression": "((AST less than 3x upper limit of normal) AND (Bilirubin less than 1.5x upper limit of normal) AND (CMV active) AND (CMV seropositive) AND (GBM) AND (GBM CMV-positive) AND (Histopathological) AND (Histopathological verification) AND (Informed consent explained to, understood by and signed by patient/guardian. Patient/guardian given copy of informed consent.) AND (Karnofsky/Lansky score 50 or greater) AND (Life expectancy 6 weeks or greater) AND (Patient or parent/guardian capable of providing informed consent) AND (Patients should have been off other investigational antineoplastic therapy for one month prior to entry in this study.) AND (Pulse oximetry 90% or greater on room air) AND (Sexually active patients must be willing to utilize one of the more effective birth control methods for 6 months after the CTL infusion. The male partner should use a condom.) AND (WHO grade IV) AND (glioblastoma multiforme) AND NOT (antineoplastic therapy for one month prior to entry in this study) AND ((Group A in remission) OR (Group B with active disease)))"}
{"candidate_id": "LLM06947", "doc_id": "NCT02888704_inc", "case_bucket": "or", "source_criterion": "Of either gender, aged ≥19 and ≤70 years Atopic dermatitis subjects who are coincident with Hanifin and Rajka diagnosis criteria Subacute and chronic atopic subjects who have atopic dermatitis symptoms continually at least 6 months Subjects with over moderate atopic dermatitis (SCORAD score > 20) Subjects who understand and voluntarily sign an informed consent form", "candidate_expression": "((Atopic dermatitis) AND (Hanifin and Rajka diagnosis criteria Subacute chronic) AND (SCORAD score > 20) AND (Subjects who understand and voluntarily sign an informed consent form) AND (aged ≥19 and ≤70 years) AND (atopic dermatitis over moderate) AND (dermatitis symptoms continually at least 6 months))"}
{"candidate_id": "LLM06948", "doc_id": "NCT03390933_inc", "case_bucket": "other", "source_criterion": "currently on hemodialysis at a CDC dialysis unit English speaking able to provide informed consent", "candidate_expression": "((CDC dialysis unit) AND (English speaking) AND (able to provide informed consent) AND (hemodialysis currently))"}
{"candidate_id": "LLM06949", "doc_id": "NCT02918851_inc", "case_bucket": "other", "source_criterion": "Habitual exerciser defined as = 30 minutes of at least moderate or high intensity exercise = 3 times per week. After consent, and at the subsequent screening visit, a VO2 max test will be performed, and subjects with a low value (< 35 mL/kg/min) will be excluded (screen failure). Based on our previous experience, we anticipate that <10% of the subjects will fall into this category Men: (0.006012 x H3) + (14.6 x W) + 604 = TBV Women: (0.005835 x H3) + (15 x W) + 183 = TBV [H=height in inches; W=weight in pounds] Has access to transportation to visit the blood collection facility and to return to Stony Brook for all study visits.", "candidate_expression": "((Men) AND (TBV (0.005835 x H3) + (15 x W) + 183) AND (TBV (0.006012 x H3) + (14.6 x W) + 604 =) AND (Women))"}
{"candidate_id": "LLM06950", "doc_id": "NCT03194074_exc", "case_bucket": "or", "source_criterion": "Patients with cardiac, pulmonary, hepatic, or renal dysfunction, epilepsy, or uncontrolled hypertension, or those taking medications that influence the central nervous system, are excluded from the study. Patients who show obvious alteration of mental status, or refuse to participate, are also excluded from the study.", "candidate_expression": "((refuse to participate) AND (uncontrolled) AND ((alteration of mental status) OR (cardiac dysfunction) OR (epilepsy) OR (hepatic dysfunction) OR (hypertension) OR (medications that influence the central nervous system) OR (pulmonary dysfunction) OR (refuse to participate) OR (renal dysfunction)))"}
```
