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
{"candidate_id": "LLM05526", "doc_id": "NCT02531971_inc", "case_bucket": "or", "source_criterion": "Men or non-pregnant women of any ethnic background between the age of 18 and 45 years old Subjects must be non-smokers (must have refrained from the use of nicotine-containing substances, including tobacco products (e.g. cigarettes, cigars, chewing tobacco, gum, patch or electronic cigarettes) over the previous 2 months and are not currently using tobacco products Provide written informed consent before initiation of any study procedures Available for follow-up for the planned duration of the study Able to communicate well with the investigators Able to adhere to the study protocol schedule, study restrictions and examination schedule Subjects who are within their ideal body weight (BMI between >17 and =28 kg/m2) Subjects deemed to be healthy as judged by the Medically Accountable Investigator (MAI) and determined by medical history, physical examination and medication history Subjects have no history of the following: ongoing acute or intermittent pain, postoperative pain, respiratory compromise, acute or severe asthma, or constipation (less than 1 bowel movement every 2 days) Negative urine drug screening test at the time of screening Have normal screening laboratories for white blood cells (WBC), hemoglobin (Hgb), platelets, sodium, potassium, chloride, bicarbonate, blood urea nitrogen (BUN), creatinine, ALT (liver function), AST (liver function) and bilirubin Have normal screening laboratories for urine protein and urine glucose Female subjects must be of non-childbearing potential (as defined as surgically sterile [i.e. history of hysterectomy or tubal ligation] or postmenopausal for more than 1 year [no bleeding for 12 consecutive months], or if of childbearing potential must be non-pregnant at the time of enrollment and on the morning of the first day of each study session, and must agree to use hormonal or barrier birth control such as implants, injectables, combined oral contraceptives, some intrauterine devices (IUDs), sexual abstinence or a vasectomized parter Agrees not to participate in another clinical study/trial during the study period or to participate in an investigational drug study for at least one month after last study session Agrees not to donate blood to a blood bank throughout participation in the study and for at least 3 months after last study day Have a normal ECG; must not have the following to be acceptable: pathologic Q wave abnormalities, significant ST-T wave changes, left ventricular hypertrophy, right bundle branch block, left bundle branch block. (sinus rhythm is between 55-100 beats per minute) Temperature 35-37.9°C (95-100.3°F) Systolic blood pressure 90-140 mmHg Diastolic blood pressure 60-90 mmHg Heart rate 55-100 beats per minute Respiration rate 12-18 breaths per minute", "candidate_expression": "((ALT) AND (AST) AND (Able to adhere to the study protocol schedule, study restrictions and examination schedule) AND (Agrees not to participate in another clinical study/trial during the study period or to participate in an investigational drug study for at least one month after last study session) AND (Available for follow-up for the planned duration of the study) AND (BMI between >17 and =28 kg/m2) AND (BUN) AND (Diastolic blood pressure 60-90 mmHg) AND (ECG normal) AND (Female subjects must be of non-childbearing potential (as defined as surgically sterile [i.e. history of hysterectomy or tubal ligation] or postmenopausal for more than 1 year [no bleeding for 12 consecutive months], or if of childbearing potential must be non-pregnant at the time of enrollment and on the morning of the first day of each study session, and must agree to use hormonal or barrier birth control such as implants, injectables, combined oral contraceptives, some intrauterine devices (IUDs), sexual abstinence or a vasectomized parte) AND (Heart rate 55-100 beats per minute) AND (Hgb) AND (Men) AND (Provide written informed consent before initiation of any study procedures) AND (Respiration rate 12-18 breaths per minute) AND (ST-T wave changes) AND (Systolic blood pressure 90-140 mmHg) AND (Temperature 35-37.9°C 95-100.3°F) AND (WBC) AND (age 18 and 45 years old) AND (asthma) AND (bicarbonate) AND (bilirubin) AND (blood urea nitrogen) AND (chloride) AND (constipation) AND (creatinine) AND (hemoglobin) AND (left bundle branch block) AND (left ventricular hypertrophy) AND (non-smokers) AND (pain acute intermittent) AND (pain postoperative) AND (pathologic Q wave abnormalities) AND (platelets) AND (potassium) AND (respiratory compromise acute severe) AND (right bundle branch block) AND (sodium) AND (urine drug screening test Negative) AND (urine glucose) AND (urine protein) AND (white blood cells) AND (women non-pregnant))"}
{"candidate_id": "LLM05527", "doc_id": "NCT02224040_exc", "case_bucket": "or", "source_criterion": "Allergy to ceftriaxone or macrolides Major typhoid fever-associated complications Inability to swallow oral medication Underlying illness Pregnancy Lactation Treatment within the past 4 days with an antibiotic that may be effective against typhoid fever", "candidate_expression": "((Allergy) AND (Inability to swallow oral medication) AND (Lactation) AND (Major) AND (Pregnancy) AND (Underlying illness) AND (antibiotic within the past 4 days effective against typhoid fever) AND (ceftriaxone) AND (complications typhoid fever-associated) AND (macrolides Major) AND (oral medication) AND (typhoid fever))"}
{"candidate_id": "LLM05528", "doc_id": "NCT02985710_inc", "case_bucket": "or", "source_criterion": "Males and females with confirmed disease: Fabry (by GLA enzymes and/or DNA testing) naïve and on ERT, Mitochondrial diseases (electron transport chain and/or DNA testing) or connective tissue diseases (clinical criteria and/or DNA testing when available) Consenting adults (18 years and older) who agrees and consents to skin biopsy and QSART procedure", "candidate_expression": "((Consenting adults (18 years and older) who agrees and consents to skin biopsy and QSART procedure) AND (ERT) AND (Fabry naïve) AND (confirmed disease) AND ((Males) OR (females)) AND ((Mitochondrial diseases) OR (connective tissue diseases)) AND ((DNA testing) OR (electron transport chain)) AND ((DNA testing) OR (clinical criteria)) AND ((DNA testing) OR (GLA enzymes)))"}
{"candidate_id": "LLM05529", "doc_id": "NCT03099408_inc", "case_bucket": "or", "source_criterion": "Women be at least 18 years of age Have symptoms of vaginal odor and or/discharge Meet the clinical (Amsel) criteria for BV Willing to participate in research", "candidate_expression": "((Amsel criteria) AND (BV) AND (Willing to) AND (Women) AND (age) AND (at least 18 years) AND (criteria clinical) AND (participate in research) AND (symptoms of) AND ((vaginal discharge) OR (vaginal odor)))"}
{"candidate_id": "LLM05530", "doc_id": "NCT02247128_inc", "case_bucket": "other", "source_criterion": "Need for long-term oral anticoagulation; Patient has provided written informed consent.", "candidate_expression": "((Patient has provided written informed consent) AND (long-term oral anticoagulation Need for))"}
{"candidate_id": "LLM05531", "doc_id": "NCT01082549_inc", "case_bucket": "or", "source_criterion": "Eligible patients must meet the following criteria to be enrolled in the study: 1. Newly diagnosed, stage IV squamous cell lung cancer. This includes patients who present with disseminated metastases, and those with a malignant pleural or pericardial effusion (i.e., formerly stage IIIB in the 6th TNM staging system). 2. Patients who have received prior adjuvant therapy for early-stage lung cancer are eligible if at least 12 months have elapsed from that treatment. 3. Histologically confirmed squamous cell bronchogenic carcinoma. Patients whose tumors contain mixed non-small cell histologies are eligible, as long as squamous carcinoma is the predominant histology. Mixed tumors with small cell anaplastic elements are not eligible. Cytologic specimens obtained by brushings, washings, or needle aspiration of the defined lesion are acceptable. 4. Patients with previous radiotherapy as definitive therapy for locally advanced non-small cell lung cancer are eligible, as long as the recurrence is outside the original radiation therapy port. Radiation therapy must have been completed >4 weeks prior to the initiation of study treatment. Patients who have received chemo/radiation for locally advanced NSCLC are not eligible. Patients who have received palliative radiation therapy for symptomatic metastases must have completed treatment >14 days prior the initiation of the study treatment. 5. Presence of evaluable (measureable or non-measurable) disease. 6. ECOG Performance Status of 0 or 1. 7. Laboratory values as follows: Absolute neutrophil count (ANC) >1,500/microL and platelets >100,000/microL (≤72 hours prior to initial treatment). Hemoglobin >9 g/dL (Note: Patients may be transfused or receive erythropoietin to maintain or exceed this level). Bilirubin < ULN. Alanine aminotransferase (ALT) and aspartate aminotransferase (AST) ≤2.5 times the upper limit of normal if no liver involvement or ≤5 times the upper limit of normal with liver involvement. Creatinine <2.0 mg/dL, or creatinine clearance >40 mL/min (as calculated by the Cockcroft-Gault method. 8. Women of childbearing potential must have a negative serum pregnancy test performed within 7 days prior to start of treatment. Women of childbearing potential or men with partners of childbearing potential must use effective birth control measures during treatment and at least 6 months after the last dose of the study treatment. If a woman becomes pregnant or suspects she is pregnant while participating in this study, she must agree to inform her treating physician immediately. Sexually active men must agree to use a medically acceptable form of birth control during treatment and at least 6 months after the last dose. If a female partner becomes pregnant during the course of the study the treating physician should be informed immediately. 9. >18 years of age. 10. Ability to understand the nature of this study, give written informed consent, and comply with study requirements. 11. Patients entering this study must be willing to provide tissue from a previous tumor biopsy (if available) for correlative testing. An exception to this is when the national/local regulations prohibits some of the key activities of this research like the export of samples to third countries, storage of coded samples or global gene expression profiling without a pre-specified list of target genes. If tissue is not available, a patient will still be eligible for enrollment into the study.", "candidate_expression": "((0 or 1) AND (6th TNM staging system) AND (8. Women of childbearing potential must have a negative serum pregnancy test performed within 7 days prior to start of treatment. Women of childbearing potential or men with partners of childbearing potential must use effective birth control measures during treatment and at least 6 months after the last dose of the study treatment. If a woman becomes pregnant or suspects she is pregnant while participating in this study, she must agree to inform her treating physician immediately. Sexually active men must agree to use a medically acceptable form of birth control during treatment and at least 6 months after the last dose. If a female partner becomes pregnant during the course of the study the treating physician should be informed immediately.) AND (< ULN) AND (<2.0 mg/dL) AND (>1,500/microL) AND (>100,000/microL) AND (>14 days prior the initiation of the study treatment) AND (>18 years) AND (>4 weeks prior to the initiation of study treatment) AND (>40 mL/min) AND (>9 g/dL) AND (Ability to understand the nature of this study, give written informed consent, and comply with study requirements.) AND (Absolute neutrophil count (ANC)) AND (Alanine aminotransferase (ALT)) AND (Bilirubin) AND (Cockcroft-Gault method) AND (Creatinine) AND (ECOG Performance Status) AND (Hemoglobin) AND (Histologically) AND (IV) AND (Mixed tumors) AND (NSCLC) AND (Newly) AND (Newly diagnosed) AND (Patients entering this study must be willing to provide tissue from a previous tumor biopsy (if available) for correlative testing. An exception to this is when the national/local regulations prohibits some of the key activities of this research like the export of samples to third countries, storage of coded samples or global gene expression profiling without a pre-specified list of target genes. If tissue is not available, a patient will still be eligible for enrollment into the study) AND (Radiation therapy) AND (adjuvant therapy) AND (age) AND (aspartate aminotransferase (AST)) AND (at least 12 months have elapsed from that treatment) AND (chemo) AND (confirmed) AND (creatinine clearance) AND (disseminated) AND (early-stage lung cancer) AND (initial treatment) AND (liver involvement) AND (liver involvement.) AND (locally advanced) AND (malignant) AND (metastases) AND (mixed non-small cell histologies) AND (no) AND (non-small cell lung cancer) AND (not) AND (palliative radiation therapy) AND (pericardial effusion) AND (platelets) AND (pleural effusion) AND (predominant histology) AND (previous) AND (radiation) AND (radiotherapy) AND (small cell anaplastic elements) AND (squamous carcinoma) AND (squamous cell bronchogenic carcinoma) AND (squamous cell lung cancer) AND (stage) AND (stage IIIB) AND (stage IV) AND (symptomatic) AND (symptomatic metastases) AND (that treatment) AND (the initiation of study treatment) AND (the initiation of the study treatment) AND (treatment) AND (≤2.5 times the upper limit of normal) AND (≤5 times the upper limit of normal) AND (≤72 hours prior to initial treatment))"}
{"candidate_id": "LLM05532", "doc_id": "NCT01614041_exc", "case_bucket": "or", "source_criterion": "Serious suicidal tendency The score of the sixth item of HAMA =3 The score of HAMD =21 Pregnant or lactating women History of allergic or hypersensitivity to tandospirone Serious or unstable cardiac, renal, neurologic, cerebrovascular, metabolic, or pulmonary disease Secondary anxiety disorders Drug or alcohol dependence within 1 year Patients currently taking benzodiazepine drugs Drivers and dangerous machine operators Participated in other clinical studies in the last 30 days Patients with clinically significant ECG or laboratory abnormalities Patients with a history of epilepsy Patients with abnormal TSH concentration", "candidate_expression": "((=21) AND (=3) AND (ECG) AND (ECG abnormalities) AND (Participated in other clinical studies) AND (Secondary anxiety disorders) AND (Serious) AND (TSH) AND (abnormal) AND (benzodiazepine drugs) AND (clinically significant) AND (currently) AND (epilepsy) AND (laboratory) AND (laboratory abnormalities) AND (score of HAMD) AND (score of the sixth item of HAMA) AND (suicidal tendency) AND (tandospirone) AND (the last 30 days) AND (unstable) AND (within 1 year) AND (women) AND ((allergic) OR (hypersensitivity)) AND ((cardiac disease) OR (cerebrovascular disease) OR (metabolic disease) OR (neurologic disease) OR (pulmonary disease) OR (renal disease)) AND ((Drug dependence) OR (alcohol dependence)) AND ((Drivers) OR (dangerous machine operators)) AND ((Pregnant) OR (lactating)))"}
{"candidate_id": "LLM05533", "doc_id": "NCT02787863_inc", "case_bucket": "or", "source_criterion": "Individuals of both sexes from 18 years with a diagnosis of community-acquired pneumonia, COPD or Bronchial Asthma; The presence of signed and dated informed consent to participate in a clinical study; The ability to perform the requirements of the Protocol; For women of childbearing age is a negative result of a pregnancy test before vaccination. community-acquired pneumonia: the presence of radiologically confirmed infiltration of the lung tissue; the presence of at least two of the following clinical signs: acute fever early in the disease (temperature > 38.0°C), cough with sputum, the physical signs of pneumonia (focus of crepitate and/or fine bubble rales, bronchial breathing hard, shortening of percussion sounds), leukocytosis > 10*10 9 /l and/or stab shift > 10%; the occurrence of the disease outside the hospital and the organized groups (such as nursing homes, sanatoriums, etc.). COPD: dyspnea: progressive (worsens over time), increases with exertion, persistent; chronic cough (may appear sporadically and may be unproductive); chronic expectoration; the impact of risk factors in the medical history (Smoking, occupational dust pollutants and chemicals); widespread wheeze on auscultation of the chest and/or distant wheezing in the chest; family history of COPD; spirometric data confirming the presence of fixed bronchial obstruction.", "candidate_expression": "((> 10%) AND (> 10*10 9 /l) AND (> 38.0°C) AND (Bronchial Asthma) AND (COPD) AND (For women of childbearing age is a negative result of a pregnancy test before vaccination.) AND (Smoking) AND (The ability to perform the requirements of the Protocol;) AND (acute fever) AND (at least two) AND (both sexes) AND (bronchial breathing hard) AND (chronic cough) AND (chronic expectoration) AND (community-acquired pneumonia) AND (cough with sputum) AND (crepitate rales) AND (distant wheezing in the chest) AND (dyspnea) AND (early in the disease) AND (family history) AND (fine bubble rales) AND (fixed bronchial obstruction) AND (from 18 years) AND (increases with exertion) AND (infiltration of the lung tissue) AND (leukocytosis) AND (occupational dust pollutants and chemicals) AND (persistent) AND (physical signs) AND (pneumonia) AND (progressive) AND (radiologically) AND (radiologically confirmed) AND (risk factors) AND (shortening of percussion sounds) AND (spirometric) AND (stab shift) AND (temperature) AND (wheeze on auscultation of the chest) AND (widespread) AND (worsens over time))"}
{"candidate_id": "LLM05534", "doc_id": "NCT00720031_inc", "case_bucket": "or", "source_criterion": "HLA-A2 melanoma patients with : either loco-regional or lymph node metastasis transit nodules not surgically resectable measurable cutaneous or visceral metastasis Patients' tumor express Melan-A/MART-1 antigen. No chemotherapy treatment (except for Deticene used before the first T cell clones infusion) or radiotherapy or immunotherapy in the last 4 weeks before infusion. No other melanoma treatment during the protocol. Life expectancy should be greater than 6 months. General state with Karnowsky greater than 80, ECOG = 0, 1 or 2. Patient should be negative for HIV and B and C hepatitis. Biological parameters at the beginning of the study: leucocytes ³ 2000 elements per mm3, hemoglobin ³ 10.5g/dl, platelets ³ 100 000 per mm3, phosphatases alcalines transaminases £ 1 time 1/2 compared to the normal. Signed informed consent", "candidate_expression": "((B hepatitis) AND (C hepatitis) AND (ECOG 0, 1 or 2) AND (HIV) AND (Karnowsky greater than 80) AND (Life expectancy greater than 6 months) AND (MART-1 antigen) AND (Melan-A antigen) AND (Signed informed consent) AND (hemoglobin ³ 10.5g/dl) AND (leucocytes ³ 2000 elements per mm3) AND (melanoma) AND (melanoma HLA-A2) AND (phosphatases alcalines transaminases £ 1 time 1/2 compared to the normal) AND (platelets ³ 100 000 per mm3) AND (surgically) AND (transit nodules surgically resectable) AND (treatment during the protocol) AND NOT (Deticene before the first T cell clones infusion) AND ((cutaneous metastasis) OR (visceral metastasis)) AND ((chemotherapy) OR (immunotherapy) OR (radiotherapy)) AND ((loco-regional metastasis) OR (lymph node metastasis)))"}
{"candidate_id": "LLM05535", "doc_id": "NCT02992938_inc", "case_bucket": "other", "source_criterion": "Patients scheduled for thyroidectomy with general anesthesia in the University of Chile Clinical Hospital", "candidate_expression": "((University of Chile Clinical Hospita) AND (general anesthesia) AND (scheduled for) AND (thyroidectomy))"}
{"candidate_id": "LLM05536", "doc_id": "NCT02984475_inc", "case_bucket": "scope", "source_criterion": "Diagnosed with Beta-Thalassemia Major and receiving regular blood transfusion and on iron chelating therapy. Weight: equal to or over 35 kg. Normal renal function.", "candidate_expression": "((Beta-Thalassemia Major) AND (Normal) AND (Weight) AND (blood transfusion) AND (equal to or over 35 kg) AND (iron chelating therapy) AND (regular) AND (renal function))"}
{"candidate_id": "LLM05537", "doc_id": "NCT01815580_exc", "case_bucket": "or", "source_criterion": "Prior receipt of investigational anti-HIV vaccine Ongoing therapy with any of the following: Systemic corticosteroids. Short course less than or equal to 21 days of corticosteroids is allowed; Systemic chemotherapeutic agents; Nephrotoxic systemic agents, including aminoglycosides, amphotericin B, cidofovir, cisplatin, foscarnet, pentamidine; Immunomodulatory treatments including Interleukin-2; Investigational agents Known allergy/sensitivity or any hypersensitivity to components of study drugs (ART) or their formulations Active drug or alcohol use or dependence that would interfere with adherence to study requirements Serious medical or psychiatric illness that would interfere with the ability to adhere to study requirements Chronic or acute hepatitis B infection Use of female hormonal products based on estrogen or derivatives", "candidate_expression": "((ART) AND (Active) AND (Chronic hepatitis B infection) AND (Immunomodulatory treatments) AND (Interleukin-2) AND (Investigational agents) AND (Nephrotoxic systemic agents) AND (Ongoing) AND (Prior) AND (Serious) AND (Short course) AND (Systemic chemotherapeutic agents) AND (Systemic corticosteroids) AND (acute hepatitis B infection) AND (alcohol dependence) AND (alcohol use) AND (allergy) AND (aminoglycosides) AND (amphotericin B) AND (anti-HIV vaccine) AND (cidofovir) AND (cisplatin) AND (components of study drugs) AND (corticosteroids) AND (drug dependence) AND (estrogen) AND (estrogen derivatives) AND (female hormonal products) AND (foscarnet) AND (hypersensitivity) AND (investigational) AND (is allowed) AND (less than or equal to 21 days) AND (medical illness) AND (or their formulations) AND (pentamidine) AND (psychiatric illness) AND (sensitivity) AND (therapy) AND (use) AND (would interfere with adherence to study requirements) AND (would interfere with the ability to adhere to study requirements))"}
{"candidate_id": "LLM05538", "doc_id": "NCT01717911_exc", "case_bucket": "or", "source_criterion": "Previous treated with anti-diabetic medication Pregnant or nursing women. Impaired liver function (ALT > 120 U/L) Impaired renal function (Serum creatinine >1.5 mg/dL in male, >1.4 mg/dL in female ) Recently suffered from MI or CVA. Patients are acute intercurrent illness. 2-hour C-peptide level < 1.8 ng/mL.", "candidate_expression": "((2-hour C-peptide level < 1.8 ng/mL) AND (ALT > 120 U/L) AND (CVA) AND (Impaired liver function) AND (Impaired renal function) AND (MI) AND (Pregnant) AND (Serum creatinine) AND (acute intercurrent illness) AND (anti-diabetic medication) AND (female >1.4 mg/dL) AND (male >1.5 mg/dL) AND (nursing) AND (treated Previous) AND (women))"}
{"candidate_id": "LLM05539", "doc_id": "NCT02394158_inc", "case_bucket": "other", "source_criterion": "Singleton pregnancy; 8-22 weeks gestation Previous pregnancy complicated by gestational diabetes", "candidate_expression": "((Singleton pregnancy) AND (gestation 8-22 weeks) AND (gestational diabetes) AND (pregnancy))"}
{"candidate_id": "LLM05540", "doc_id": "NCT02985710_inc", "case_bucket": "or", "source_criterion": "Males and females with confirmed disease: Fabry (by GLA enzymes and/or DNA testing) naïve and on ERT, Mitochondrial diseases (electron transport chain and/or DNA testing) or connective tissue diseases (clinical criteria and/or DNA testing when available) Consenting adults (18 years and older) who agrees and consents to skin biopsy and QSART procedure", "candidate_expression": "((Consenting adults (18 years and older) who agrees and consents to skin biopsy and QSART procedure) AND (DNA testing) AND (ERT) AND (GLA enzymes) AND (Males) AND (Mitochondrial diseases) AND (clinical criteria) AND (confirmed disease Fabry naïve) AND (connective tissue diseases) AND (electron transport chain) AND (females))"}
{"candidate_id": "LLM05541", "doc_id": "NCT02046395_inc", "case_bucket": "or", "source_criterion": "Type 2 Diabetes Hypertension Estimated glomerular filtration rate (eGFR) > 30 ml/min Use of Ace Inh and ARB for control of blood pressure who are willing to be placed on alternate drug(s) in the washout period for blood pressure control", "candidate_expression": "((ARB) AND (Ace Inh) AND (Estimated glomerular filtration rate (eGFR) > 30 ml/min) AND (Hypertension) AND (Type 2 Diabetes) AND (control of blood pressure) AND (willing to be placed on alternate drug(s) in the washout period for blood pressure control))"}
{"candidate_id": "LLM05542", "doc_id": "NCT02816762_exc", "case_bucket": "or", "source_criterion": "Non diabetic nephropathy (confirmed by biopsy). Dialysis for acute renal failure within the 6 previous months. Evidence in the clinic history of relevant bilateral stenosis of renal artery (> 75%) Urinary albumin/creatinine ratio higher than 3000 mg/g, at the baseline visit. Systolic blood pressure = 180 mmHg or diastolic blood pressure = 110 mm Hg at the baseline visit. Stroke, transient ischemic attack, acute coronary syndrome, or hospitalization for heart failure worsening, within the previous 30 days. Professional drivers, risk profession or respiratory failure. Severe daytime sleepiness (Epworth sleepiness scale >18) Concomitant treatment with high doses of acetylsalicylic acid (> 500 mg/day) or continuous treatment with non-steroidal anti-inflammatory drugs Previous treatment with CPAP Participation in another clinical trial within the 30 days prior to randomization.", "candidate_expression": "((CPAP) AND (Dialysis within the 6 previous months) AND (Epworth sleepiness scale >18) AND (Non diabetic nephropathy confirmed by biopsy) AND (Urinary albumin/creatinine ratio higher than 3000 mg/g at the baseline visit) AND (acetylsalicylic acid high doses > 500 mg/day) AND (acute renal failure) AND (biopsy) AND (daytime sleepiness Severe) AND (heart failure worsening) AND (non-steroidal anti-inflammatory drugs) AND (stenosis of renal artery relevant bilateral > 75%) AND (treatment Previous) AND ((Systolic blood pressure = 180 mmHg) OR (diastolic blood pressure = 110 mm Hg)) AND ((Stroke) OR (acute coronary syndrome) OR (hospitalization) OR (transient ischemic attack)) AND ((Professional drivers) OR (respiratory failure) OR (risk profession)) AND ((treatment Concomitant) OR (treatment continuous)))"}
{"candidate_id": "LLM05543", "doc_id": "NCT02579200_exc", "case_bucket": "or", "source_criterion": "Inability to perform exercise tests Diagnosed psychiatric or cognitive disorders Progressive neurological or neuromuscular disorders having a major impact on exercise capacity", "candidate_expression": "((Inability to perform) AND (cognitive disorders) AND (disorders Progressive neurological) AND (exercise tests) AND (impact on exercise capacity) AND (neuromuscular disorders Progressive) AND (psychiatric disorders))"}
{"candidate_id": "LLM05544", "doc_id": "NCT01807897_inc", "case_bucket": "or", "source_criterion": "Veteran receiving care within the Veterans Health Administration healthcare system Age 18 years Physician diagnosis of chronic heart failure, American Heart Association Stage C-D LVEF <45% No change in active cardiac medications for 4 weeks prior to randomization Ability to provide informed consent Moderate to severe central or mixed central and obstructive sleep apnea, defined as an apnea-hypopnea index (AHI) 15 events per hour, with a central AHI >5 events/hour", "candidate_expression": "((15 events per hour,) AND (18 years) AND (<45%) AND (>5 events/hour) AND (AHI) AND (Ability to provide informed consent) AND (Age) AND (American Heart Association Stage) AND (C-D) AND (LVEF) AND (Moderate) AND (No) AND (Veteran) AND (Veterans Health Administration healthcare system) AND (apnea-hypopnea index) AND (cardiac medications) AND (central AHI) AND (central sleep apnea) AND (change) AND (chronic heart failure) AND (for 4 weeks prior to randomization) AND (mixed central sleep apnea) AND (obstructive sleep apnea) AND (randomization) AND (severe))"}
{"candidate_id": "LLM05545", "doc_id": "NCT02782702_exc", "case_bucket": "or", "source_criterion": "Hypersensibility to toxin or excipients Myastheny Deglutition's problems Past medical history of dysphagia or aspiration pneumonia Pregnancy (positive B-HCG test performed a maxima 72h before) or breastfeeding Mental , physical incapacity to fill in the questionnaires Guardianship patients Skin infections at the inclusion visit Application in the last 7 days at the site of injection of local treatments (apart emollients or antiseptics) or injections of botulism toxin or dynamic phototherapy or laser in the last 6 months. Systemic treatment with aminosides in the last 15 days Inclusion in another study in the last 2 months.", "candidate_expression": "((Application of local treatments in the last 7 days) AND (B-HCG test positive a maxima 72h before) AND (Deglutition's problems) AND (Hypersensibility) AND (Inclusion in another study) AND (Inclusion in another study in the last 2 months) AND (Myastheny) AND (Skin infections at the inclusion visit) AND (Systemic treatment in the last 15 days) AND (aminosides) AND (botulism toxin) AND (fill in the questionnaires) AND (inclusion visit) AND ((aspiration pneumonia) OR (dysphagia)) AND ((Pregnancy) OR (breastfeeding)) AND ((Mental incapacity) OR (physical incapacity)) AND ((antiseptics) OR (emollients)) AND ((excipients) OR (toxin)) AND ((dynamic phototherapy) OR (injections) OR (laser)))"}
{"candidate_id": "LLM05546", "doc_id": "NCT03352869_inc", "case_bucket": "or", "source_criterion": "Overweight and obese PCOS patients with newly diagnosed IGR; PCOS diagnosis based on 2003 Rotterdam criteria Overweight / obesity diagnostic criteria according to WHO-WPR Impaired glucose regulation diagnostic criteria according to 1998 WHO diagnostic criteria.", "candidate_expression": "((1998 WHO diagnostic criteria) AND (2003 Rotterdam criteria) AND (IGR) AND (Impaired glucose regulation) AND (PCOS) AND (WHO-WPR) AND (newly diagnosed) AND ((Overweight) OR (obese)) AND ((Overweight) OR (obesity)))"}
{"candidate_id": "LLM05547", "doc_id": "NCT02467686_inc", "case_bucket": "or", "source_criterion": "Menopausal women with breast cancer treated and using tamoxifen or aromatase inhibitor. With hot flashes and with or without active sexual life.", "candidate_expression": "((Menopausal) AND (aromatase inhibitor) AND (breast cancer) AND (hot flashes) AND (tamoxifen) AND (treated) AND (with active sexual life) AND (without active sexual life) AND (women))"}
{"candidate_id": "LLM05548", "doc_id": "NCT00749112_inc", "case_bucket": "or", "source_criterion": "Age: > or = 16 years Weight: more than 40 Kg Autoimmune Hemolytic anemia with clinical and biochemical evidence of hemolysis refractory to treatment, in relapse or steroids dependant Idiopathic thrombocytopenic purpura with platelet counts < 50,000, refractory to treatment, in relapse or steroids dependant", "candidate_expression": "((Age > or = 16 years) AND (Autoimmune Hemolytic anemia) AND (Idiopathic thrombocytopenic purpura) AND (Weight more than 40 Kg) AND (hemolysis evidence clinical biochemical evidence refractory to treatment) AND (platelet counts < 50,000 refractory to treatment) AND (steroids steroids dependant) AND (treatment in relapse))"}
{"candidate_id": "LLM05549", "doc_id": "NCT01446094_inc", "case_bucket": "other", "source_criterion": "Aged 18 years or older Scheduled for invasive coronary angiography", "candidate_expression": "((Aged 18 years or older) AND (invasive coronary angiography Scheduled))"}
{"candidate_id": "LLM05550", "doc_id": "NCT02541955_inc", "case_bucket": "other", "source_criterion": "Patient must meet 1987 ACR criteria Age > 18 years of age Baseline DAS28/Erythrocyte Sedimentation Rate (ESR) >=3.2 Stable concomitant Disease Modifying Anti-Rheumatic Drugs (DMARDs) Stable prednisone <10mg or equivalent Power Doppler score of >=10", "candidate_expression": "((1987 ACR criteria) AND (<10mg) AND (> 18 years of age) AND (>=10) AND (>=3.2) AND (Age) AND (Baseline) AND (DAS28/Erythrocyte Sedimentation Rate (ESR)) AND (Disease Modifying Anti-Rheumatic Drugs (DMARDs)) AND (Power Doppler score) AND (Stable) AND (concomitant) AND (prednisone))"}
```
