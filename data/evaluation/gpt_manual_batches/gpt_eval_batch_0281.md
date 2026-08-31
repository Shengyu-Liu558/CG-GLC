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
{"candidate_id": "LLM07001", "doc_id": "NCT03389061_inc", "case_bucket": "other", "source_criterion": "Patients with SOF/VEL treatment for the treatment of chronic HCV genotype 1 through 6. Patient is at least 18 at the day of screening. Patient is able and willing to sign the Informed Consent Form. Patient is able and willing to follow protocol requirements.", "candidate_expression": "((1 through 6) AND (HCV genotype) AND (Patient is able and willing to follow protocol requirements) AND (Patient is able and willing to sign the Informed Consent Form) AND (SOF/VEL treatment) AND (at least 18 at the day of screening) AND (chronic) AND (screening))"}
{"candidate_id": "LLM07002", "doc_id": "NCT02634541_inc", "case_bucket": "or", "source_criterion": "Axial spondyloarthritis (ASAS criteria) and radiologic sacroiliitis as detected either by MRI or X-ray.", "candidate_expression": "((Axial spondyloarthritis ASAS criteria) AND (MRI) AND (X-ray) AND (radiologic) AND (sacroiliitis))"}
{"candidate_id": "LLM07003", "doc_id": "NCT02926235_exc", "case_bucket": "other", "source_criterion": "All patients who were wheelchair bound preoperatively All patients who cannot participate in an outpatient physical therapy program for 3 days per week after surgery", "candidate_expression": "((outpatient) AND (wheelchair bound preoperatively) AND NOT (physical therapy for 3 days per week after surgery))"}
{"candidate_id": "LLM07004", "doc_id": "NCT03259243_exc", "case_bucket": "or", "source_criterion": "Patient with history of allergy in any kind anesthetic drug Patient who pregnant Patient who sign for single port gynecologic laparoscopic surgery or NOTE surgery Patient whom the surgery is withhold or canceled Patient whom the surgery is converted to laparotomy", "candidate_expression": "((allergy) AND (anesthetic drug) AND (any kind) AND (converted to) AND (history) AND (laparotomy) AND (pregnant) AND (single port) AND (surgery) AND ((canceled) OR (withhold)) AND ((NOTE surgery) OR (gynecologic laparoscopic surgery)))"}
{"candidate_id": "LLM07005", "doc_id": "NCT02478515_inc", "case_bucket": "other", "source_criterion": "Signed informed consent form Macula edema secondary to BRVO BCVA of 77 to 20 letters assessed with the use of ETDRS charts CRT <U+2267>250µm", "candidate_expression": "((BCVA 77 to 20 letters) AND (BRVO) AND (CRT 250µm) AND (Macula edema) AND (Signed informed consent form))"}
{"candidate_id": "LLM07006", "doc_id": "NCT02393287_exc", "case_bucket": "other", "source_criterion": "1. Presence of other neoplasia 2. Man", "candidate_expression": "((Man) AND (neoplasia other))"}
{"candidate_id": "LLM07007", "doc_id": "NCT01765231_exc", "case_bucket": "or", "source_criterion": "younger than 18 years old HBsAg positive or HBcAb negative or hepatitis B virus DNA positive at baseline pregnant or lactating women", "candidate_expression": "((HBcAb negative) AND (HBsAg positive) AND (at baseline) AND (hepatitis B virus DNA positive) AND (lactating) AND (old) AND (pregnant) AND (women) AND (younger than 18 years))"}
{"candidate_id": "LLM07008", "doc_id": "NCT03336801_exc", "case_bucket": "or", "source_criterion": "American Association of Anesthesiology class 1-3 American Heart Association class >3 BMI >37 Insulin treated diabetes Pregnancy or breast feeding Sensistivity/allergy against anesthetic agents Inadequate understanding about the study Depressed kidney function and/or AKI Depressed liver function Genetic malignant hyperthermia", "candidate_expression": "((AKI) AND (American Association of Anesthesiology class 1-3) AND (American Heart Association class >3) AND (BMI >37) AND (Depressed kidney function) AND (Depressed liver function) AND (Inadequate understanding about the study) AND (Insulin) AND (Pregnancy) AND (Sensistivity) AND (allergy) AND (anesthetic agents) AND (breast feeding) AND (diabetes Insulin treated) AND (kidney function Depressed) AND (liver function Depressed) AND (malignant hyperthermia Genetic))"}
{"candidate_id": "LLM07009", "doc_id": "NCT02301962_inc", "case_bucket": "or", "source_criterion": "Subject or subject's legally acceptable representative has provided informed consent. Male or female >=18 years of age. Histologically or cytologically confirmed diagnosis of adenocarcinoma of the colon or rectum. Wild-type KRAS (without mutation in exon 2 [codons 12 and 13], exon 3 [codons 59 and 61], and exon 4 [codons 117 and 146]) and wild-type NRAS (without mutation in exon 2 [codons 12 and 13], exon 3 [codons 59 and 61], and exon 4 [codons 117 and 146]) tumor status. Eastern Cooperative Oncology Group (ECOG) performance status of 0, 1 or 2. Measurable or non-measurable disease per RECIST Version 1.1. Must have failed after fluoropyrimidine-, oxaliplatin-, and irinotecan-containing chemotherapy regimens for metastatic disease. Failure is defined as either disease progression (clinical or radiological) or intolerance to the regimen. Metastatic relapse within 6 months after completing adjuvant chemotherapy (with either an irinotecan or oxaliplatin containing regimen) will also be considered as treatment failure of a prior regimen for metastatic disease. Laboratory: Adequate baseline organ function defined by (<=7 days prior to first dose of study treatment). Hematologic function, as follows: Absolute neutrophil count (ANC) >=1.5 x 10^9/Liter (L), Platelet count >=75 x 10^9/L, Hemoglobin >=8.0 gram/deciliter (g/dL). Renal function, as follows: Creatinine <=1.5 x upper limit of normal (ULN). Hepatic function, as follows: Aspartate aminotransferase (AST) <=3 x ULN, Alanine aminotransferase (ALT) <=3 x ULN, Total Bilirubin <=1.5 x ULN. Metabolic function, as follows: Serum Magnesium within normal limits. Serum Calcium within normal limits. Serum Potassium within normal limits. All prior treatment related toxicities common terminology criteria for adverse events (CTCAE) version 4.03 <=Grade 1 at the time of enrollment. Women of childbearing potential must have a negative serum pregnancy test within 7 days of first dose of study treatment and agree to use adequate contraception, during the study and for 2 months following the last dose of study treatment. Men with a female partner of childbearing potential must have either had a prior vasectomy or agree to use adequate contraception, from time of signing informed consent until 5 months after the last dose of study treatment.", "candidate_expression": "((0, 1 or 2) AND (<=1.5 x ULN) AND (<=1.5 x upper limit of normal (ULN)) AND (<=3 x ULN) AND (<=7 days prior to first dose of study treatment) AND (>=1.5 x 10^9/Liter (L)) AND (>=18 years) AND (>=75 x 10^9/L) AND (>=8.0 gram/deciliter (g/dL)) AND (Adequate baseline organ function) AND (Alanine aminotransferase (ALT)) AND (Creatinine) AND (Eastern Cooperative Oncology Group (ECOG) performance status) AND (RECIST Version 1.1) AND (Serum Calcium) AND (Serum Magnesium) AND (Serum Potassium) AND (Subject or subject's legally acceptable representative has provided informed consent.) AND (Total Bilirubin) AND (Women of childbearing potential must have a negative serum pregnancy test within 7 days of first dose of study treatment and agree to use adequate contraception, during the study and for 2 months following the last dose of study treatment. Men with a female partner of childbearing potential must have either had a prior vasectomy or agree to use adequate contraception, from time of signing informed consent until 5 months after the last dose of study treatment.) AND (adenocarcinoma) AND (after completing adjuvant chemotherapy) AND (age) AND (confirmed) AND (failed) AND (first dose of study treatment) AND (metastatic disease) AND (spartate aminotransferase (AST)) AND (the regimen) AND (within 6 months after completing adjuvant chemotherapy) AND (within normal limits) AND ((colon) OR (rectum)) AND ((Measurable disease) OR (non-measurable disease)) AND ((Male) OR (female)) AND ((fluoropyrimidine- containing chemotherapy) OR (irinotecan-containing chemotherapy) OR (oxaliplatin- containing chemotherapy)) AND ((Metastatic relapse) OR (disease progression) OR (intolerance)) AND ((irinotecan containing regimen) OR (oxaliplatin containing regimen)) AND ((Absolute neutrophil count (ANC)) OR (Hemoglobin) OR (Platelet count)) AND ((Histologically) OR (cytologically)))"}
{"candidate_id": "LLM07010", "doc_id": "NCT02689817_exc", "case_bucket": "or", "source_criterion": "Existing sacral pressure ulcer, undergoing a cardiac procedure, or inability to provide informed consent.", "candidate_expression": "((inability to provide informed consent) AND ((cardiac procedure) OR (inability to provide informed consent) OR (sacral pressure ulcer)))"}
{"candidate_id": "LLM07011", "doc_id": "NCT01768195_inc", "case_bucket": "other", "source_criterion": "treatment-naive patients with B-cell lymphoma HBsAg positive at baseline treated with rituximab-based immunochemotherapy life expectancy of more than 3 months", "candidate_expression": "((B-cell lymphoma) AND (HBsAg positive at baseline) AND (immunochemotherapy rituximab-based) AND (life expectancy more than 3 months) AND (rituximab) AND NOT (treatment))"}
{"candidate_id": "LLM07012", "doc_id": "NCT03012984_exc", "case_bucket": "or", "source_criterion": "Preoperative history of schizophrenia, epilepsy, parkinsonism or myasthenia gravis; Preoperative radio- or chemotherapy; Inability to communicate in the preoperative period because of coma, profound dementia or language barrier; Preoperative obstructive sleep apnea (previously diagnosed as obstructive sleep apnea, or a STOP-Bang score >= 3); Brain trauma or neurosurgery; Preoperative left ventricular ejection fraction < 30%, sick sinus syndrome, severe sinus bradycardia (< 50 beats per minute), or second-degree or above atrioventricular block without pacemaker; Severe hepatic dysfunction (Child-Pugh class C) or severe renal dysfunction (requirement of renal replacement therapy before surgery); ASA classification >= IV.", "candidate_expression": "((< 30%) AND (< 50 beats per minute) AND (>= 3) AND (>= IV) AND (ASA classification) AND (Child-Pugh) AND (Inability to communicate) AND (Preoperative) AND (Severe) AND (before surgery) AND (class C) AND (hepatic dysfunction) AND (history) AND (obstructive sleep apnea) AND (pacemaker) AND (preoperative period) AND (profound) AND (renal dysfunction) AND (renal replacement therapy) AND (second-degree or above) AND (severe) AND (surgery) AND (without) AND ((coma) OR (dementia) OR (language barrier)) AND ((epilepsy) OR (myasthenia gravis) OR (parkinsonism) OR (schizophrenia)) AND ((STOP-Bang score) OR (obstructive sleep apnea)) AND ((Brain trauma) OR (neurosurgery)) AND ((atrioventricular block) OR (left ventricular ejection fraction) OR (sick sinus syndrome) OR (sinus bradycardia)) AND ((chemotherapy) OR (therapy radio)))"}
{"candidate_id": "LLM07013", "doc_id": "NCT02431442_exc", "case_bucket": "or", "source_criterion": "Fasting blood glucose >126 mg/dL at screening. Heterozygous subjects will be excluded for a fasting blood glucose >140 mg/dL. Resting heart rate <45 bpm or >90 bpm at screening. Abnormal thyroid stimulating hormone (TSH) or thyroxine (T4) levels on screening. Elevated ALT or serum creatinine on screening or any clinically significant abnormalities on screening laboratory tests as determined by the Investigator. History of medically treated diabetes or of treated or medically diagnosed hypertension. Heterozygous subjects who have diagnosed hypertension and are well controlled on treatment (Refer to Exclusion Criteria 20 below), are eligible. . Presence of a skin lesion suspicious for malignancy, unless excised prior to Day 1. History of malignancy except for treated cervical carcinoma in situ in the past 5 years. Active or history of any clinically significant medical condition including renal, hepatic, pulmonary, gastrointestinal, cardiovascular, genitourinary, endocrine, immunologic, metabolic, neurologic, psychiatric or hematological disease, based on Investigator judgment. Acute illness or history of illness, which in the opinion of the Investigator, could pose a threat or harm to the subject or obscure interpretation of laboratory test results or interpretation of study data. Positive hepatitis B surface antigen, positive hepatitis C antibody or positive HIV test at screening or a history of positive testing (e.g. liver biopsy, serology) suggesting acute or chronic hepatitis. Abnormal 12-lead electrocardiogram (ECG) at screening or pre-dose (Day -1 or Day 1), except minor deviations deemed to be of no clinical significance by the Investigator. Received any experimental drugs or devices within 30 days or 5 half lives, whichever is longer, prior to dosing. Ongoing participation in a prior clinical study at the time of screening. Blood donation within 60 days prior to screening or intent to donate within 60 days after Final Study Visit. Hospitalization for major surgery including but not limited to abdominal, thoracic, or cardiovascular surgery within the past 3 months prior to screening, or for a clinically significant non-surgical illness, based on Investigator judgment, within the past 3 months. Planned elective surgery within 30 days of the Final Study Visit. Poor venous access or inability to tolerate venipuncture. History of significant drug hypersensitivity or anaphylaxis. History of hypersensitivity to proteins (e.g., allergy shots). Use of prescription medications on a regular basis. The last use of any prescription medication must have been greater than 5 half-lives for the specific medication or at least 14 days prior to admission (Day -1), whichever is longer. Hormonal contraception is allowed for female subjects. Heterozygous cohorts: Use of prescription medications on a regular basis is not allowed with the following exceptions: Antihypertensives (<3 medications on a stable dose for ≥ 30 days); Statins (dose must be ≤ half the maximum dose; must be on a stable dose ≥3 months); Fibrates (must be on stable dose for ≥3 months); Niacin (must be on stable dose for ≥3 months); Thyroxin (stable dose for ≥ 30 days); The last use of any other prescription medication will need follow the criteria for all other cohorts, as outlined above. Use of prescription medications not listed above may be allowed at the discretion of the Investigator upon consultation with Rhythm. Use of a non-prescription drug and herbal substances during the study (through the Final Study Visit). The last dose of any non-prescription drug must have been taken greater than 5 half-lives for that drug before receiving study drug. Inability to attend all study visits or to comply with protocol requirements including fasting and restrictions on alcohol, caffeine, nicotine and concomitant medication intake. A significant history of drug/solvent abuse within 5 years of screening or a positive test for drugs of abuse test at screening or on Day -1. Positive alcohol (breath test) or nicotine screen at Screening Visit or Day 1 (positive nicotine screen does not apply to heterozygous cohort). History of alcohol abuse (defined as average intake of three or more units of alcohol per day) within 5 years of the Screening Visit. History of tobacco or tobacco product use unless abstinent for at least one year prior to the Screening Visit. This criterion does not apply to heterozygous subjects. Previously randomized and dosed in this study. This criterion does not apply to heterozygous subjects. Any other reason, which in the opinion of the Investigator would confound proper evaluation of the study.", "candidate_expression": "((12-lead electrocardiogram (ECG) Abnormal at screening at pre-dose Day -1 Day 1) AND (ALT Elevated on screening) AND (Acute illness or history of illness, which in the opinion of the Investigator, could pose a threat or harm to the subject or obscure interpretation of laboratory test results or interpretation of study data.) AND (Antihypertensives stable dose) AND (Any other reason, which in the opinion of the Investigator would confound proper evaluation of the study.) AND (Blood donation within 60 days prior to screening) AND (Fasting blood glucose >126 mg/dL at screening) AND (Fibrates stable dose) AND (HIV test positive at screening) AND (Heterozygous) AND (Hormonal contraception) AND (Hospitalization) AND (Niacin stable dose) AND (Poor venous access) AND (Resting heart rate at screening <45 bpm >90 bpm) AND (Statins ≤ half the maximum dose stable dose) AND (Thyroxin stable dose) AND (Use of prescription medications not listed above may be allowed at the discretion of the Investigator upon consultation with Rhythm.) AND (abdominal surgery) AND (acute hepatitis) AND (alcohol abuse History) AND (alcohol test) AND (alcohol three or more units per day within 5 years of the Screening Visit) AND (any non-prescription drug greater than 5 half-lives before receiving study drug) AND (any prescription medication last use greater than 5 half-lives at least 14 days prior to admission) AND (as determined by the Investigator) AND (based on Investigator judgment) AND (breath test) AND (cardiovascular surgery) AND (chronic hepatitis) AND (clinically significant) AND (diabetes History medically treated treated) AND (disease cardiovascular) AND (disease endocrine) AND (disease gastrointestinal) AND (disease genitourinary) AND (disease hepatic) AND (disease immunologic) AND (disease pulmonary) AND (disease renal) AND (drug anaphylaxis History significant) AND (drug hypersensitivity History significant) AND (drug/solvent abuse history within 5 years of screening) AND (drugs of abuse test positive at screening) AND (elective surgery Planned within 30 days of the Final Study Visit) AND (excised prior to Day 1) AND (experimental devices within 30 days within 5 half lives) AND (experimental drugs) AND (fasting blood glucose >140 mg/dL) AND (female) AND (hematological disease) AND (hepatitis B surface antigen Positive) AND (hepatitis C antibody positive) AND (herbal substances during the study) AND (history Active) AND (hypersensitivity to allergy shots History) AND (hypersensitivity to proteins History) AND (hypertension History) AND (hypertension well controlled) AND (inability to tolerate venipuncture) AND (intent to donate within 60 days after Final Study Visit) AND (laboratory tests abnormalities) AND (liver biopsy) AND (major) AND (malignancy) AND (malignancy History in the past 5 years) AND (medical condition clinically significant) AND (medically) AND (medically treated) AND (metabolic disease) AND (neurologic disease) AND (nicotine screen Positive) AND (non-prescription drug during the study) AND (non-surgical illness clinically significant within the past 3 months) AND (prescription medications) AND (prescription medications regular basis) AND (psychiatric disease) AND (serology) AND (serum creatinine Elevated on screening) AND (significant) AND (skin lesion suspicious for malignancy) AND (surgery major within the past 3 months prior to screening) AND (testing history positive) AND (thoracic surgery) AND (thyroid stimulating hormone (TSH) Abnormal on screening) AND (thyroxine (T4) Abnormal on screening) AND (tobacco product use) AND (tobacco use) AND (treated) AND (treatment) AND (venipuncture) AND NOT (abstinent for at least one year prior to the Screening Visit) AND NOT (cervical carcinoma in situ treated))"}
{"candidate_id": "LLM07014", "doc_id": "NCT02908919_exc", "case_bucket": "or", "source_criterion": "ileus known or suspected bowel obstruction active bowel inflammation pregnancy any presence of serious medical conditions ( esp. cardiac, renal, liver diseases) history of prior colonic or rectal surgery inability to obtain valid data from", "candidate_expression": "((bowel inflammation active) AND (bowel obstruction) AND (cardiac diseases) AND (colonic surgery) AND (ileus known suspected) AND (liver diseases) AND (pregnancy) AND (rectal surgery) AND (renal diseases) AND (serious medical conditions))"}
{"candidate_id": "LLM07015", "doc_id": "NCT02961764_inc", "case_bucket": "other", "source_criterion": "Presents to the Emergency Department (ED) and meets the clinical definition for Acute Bacterial Skin and Skin Structure Infections (ABSSSI) Known or suspected gram-positive infection.", "candidate_expression": "((ABSSSI) AND (Acute Bacterial Skin and Skin Structure Infections) AND (Emergency Department (ED)) AND (infection gram-positive))"}
{"candidate_id": "LLM07016", "doc_id": "NCT02859480_exc", "case_bucket": "or", "source_criterion": "Taking other drugs which can influence the lipid profile (eg. Niacin, Fibrates; Serum creatinine level > 2.0 mg/dL Serum aspartate transaminase > 3 times upper limit of normal Serum alanine transaminase > 3 times upper limit of normal Having anaphylactic reaction for Rosuvastatin; Having the other contraindications for Rosuvastatin; Having plan to be pregnant; Having life expectancy less than 1 year", "candidate_expression": "((Fibrates) AND (Niacin) AND (Rosuvastatin) AND (Serum alanine transaminase > 3 times upper limit of normal) AND (Serum aspartate transaminase > 3 times upper limit of normal) AND (Serum creatinine level > 2.0 mg/dL) AND (anaphylactic reaction) AND (contraindications) AND (drugs other can influence the lipid profile) AND (life expectancy less than 1 year) AND (lipid profile) AND (pregnant plan))"}
{"candidate_id": "LLM07017", "doc_id": "NCT03046108_exc", "case_bucket": "or", "source_criterion": "Contraindication for the use of corticosteroids or local anesthetics Presence of inflammatory arthropathy or neuropathy Skin lesions in the area diabetes mellitus Infiltration or previous surgery in the area Refusal to participate in the study", "candidate_expression": "((Contraindication) AND (Refusal to participate in the stud) AND (Skin lesions) AND (diabetes mellitus) AND ((corticosteroids) OR (local anesthetics)) AND ((Infiltration) OR (previous surgery)) AND ((inflammatory arthropathy) OR (neuropathy inflammatory)))"}
{"candidate_id": "LLM07018", "doc_id": "NCT01064752_inc", "case_bucket": "other", "source_criterion": "1. HIV infection with plasma and CSF HIV RNA concentrations (using Roche Amplicor assay) > 1,000 copies/ mL (available after baseline LP). 2. Off antiretroviral therapy (ART) for > 6 weeks before the study and no plans to begin treatment for the study duration. (The decision of whether or not a subject takes antiretroviral therapy will be made by the subject in consultation with his/her primary care provider prior to screening for this study.) 3. Predicted adherence to the medication. 4. Capable of providing informed consent. 5. > 18 years old 6. CD4 cell counts >150 cells/μL (though likely most, if not all, will be >250 cells/μL). 7. When available, subjects will be screened for stability of blood CD4 and HIV RNA levels.", "candidate_expression": "((18 years) AND (> 1,000 copies/ mL) AND (> 6 weeks before the study) AND (>150 cells/μL) AND (>250 cells/μL) AND (CD4 cell counts) AND (CSF HIV RNA concentration) AND (Capable of providing informed consent.) AND (HIV infection) AND (Off antiretroviral therapy (ART)) AND (Roche Amplicor assay) AND (antiretroviral therapy (ART)) AND (for the study duration) AND (no) AND (old) AND (plans to begin) AND (plasma concentration) AND (study) AND (the study) AND (treatment))"}
{"candidate_id": "LLM07019", "doc_id": "NCT01856491_exc", "case_bucket": "or", "source_criterion": "Known or suspected sensitivity to Dexamethasone Acetate (DXA) Mechanical tricuspid heart valve Subject is enrolled in any other concurrent study without prior written approval from Boston Scientific (BSC), with the exception of local mandatory governmental registries and observational studies/registries that are not in conflict and do not affect the following: Schedule of procedures for the RELIANCE 4-Front Study (i.e. should not cause additional or missed visits); RELIANCE 4-Front Study outcome (i.e. involve medications that could affect the heart rate of the subject); Conduct of the RELIANCE 4-Front Study per Good Clinical Practice (GCP)/ International Organization for Standardization (ISO) 14155:2011/ 21 CFR 812/ local regulations Currently on the active heart transplant list Documented life expectancy of less than 12 months Women of childbearing potential who are or might be pregnant at the time of study enrollment (method of assessment upon physician discretion) Currently requiring chronic dialysis", "candidate_expression": "((Currently) AND (Dexamethasone Acetate (DXA)) AND (Known) AND (Mechanical tricuspid heart valve) AND (Women) AND (active heart transplant list) AND (are or might be) AND (at the time of study enrollment) AND (childbearing potential) AND (chronic dialysis) AND (less than 12 months) AND (life expectancy) AND (pregnant) AND (requiring chronic dialysis) AND (sensitivity to Dexamethasone Acetate (DXA)) AND (suspected))"}
{"candidate_id": "LLM07020", "doc_id": "NCT03402945_exc", "case_bucket": "or", "source_criterion": "On systemic antibiotics or with an active bacterial infection at the time of surgery Patients previously enrolled in this trial Patients known to be colonized with Methicillin-resistant S. aureus (MRSA)(unethical not to administer glycopeptides), beta-lactam or vancomycin allergy precluding the use of cefazolin or vancomycin, respectively, or to silver precluding the use of Prevena Participation in other studies that may interfere with this trial", "candidate_expression": "((Methicillin-resistant S. aureus (MRSA)) AND (Participation in other studies that may interfere with this trial) AND (active) AND (allergy) AND (at the time of surgery) AND (bacterial infection) AND (beta-lactam) AND (cefazolin) AND (colonized) AND (previously enrolled in this trial) AND (silver) AND (surgery) AND (systemic antibiotics) AND (the time of surgery) AND (vancomycin))"}
{"candidate_id": "LLM07021", "doc_id": "NCT03208127_inc", "case_bucket": "other", "source_criterion": "Recipient is Age = 18 years Met MGH transplant center criteria, listed for liver transplant HCV naive Able to sign informed consent", "candidate_expression": "((Able to sign informed consent) AND (Age = 18 years) AND (HCV naive) AND (liver transplant MGH transplant center criteria))"}
{"candidate_id": "LLM07022", "doc_id": "NCT00962364_exc", "case_bucket": "other", "source_criterion": "none, all patients meeting the inclusion criteria will be eligible.", "candidate_expression": "(EMPTY)"}
{"candidate_id": "LLM07023", "doc_id": "NCT01501201_inc", "case_bucket": "or", "source_criterion": "Type 2 diabetes mellitus with HbA1c > 7.5 % Body mass index > 35 and < 50 kg/m2 Candidate for Gastric By-Pass Treatment with GLP1 (glucagon-like peptide) analogue or insulin", "candidate_expression": "((> 35 and < 50 kg/m2) AND (> 7.5 %) AND (Body mass index) AND (Candidate) AND (Gastric By-Pass) AND (HbA1c) AND (Treatment) AND (Type 2 diabetes mellitus) AND ((GLP1 (glucagon-like peptide) analogue) OR (insulin)))"}
{"candidate_id": "LLM07024", "doc_id": "NCT02851303_inc", "case_bucket": "or", "source_criterion": "Born at University of New Mexico Hospital Greater than 34 weeks gestation Primary in-utero drug exposure was opioids other than buprenorphine Maternal or infant urine drug screen positive for methadone and/or opioids on admission", "candidate_expression": "((Born) AND (Greater than 34 weeks) AND (Maternal) AND (University of New Mexico Hospital) AND (buprenorphine) AND (drug exposure) AND (gestation) AND (in-utero) AND (infant) AND (methadone) AND (opioids) AND (other) AND (positive) AND (urine drug screen))"}
{"candidate_id": "LLM07025", "doc_id": "NCT02632760_inc", "case_bucket": "or", "source_criterion": "Patients with anaemia (males Hb <130 g/L, females <120 g/L) undergoing elective cardiac surgery, and available to receive trial drug 1- 10 weeks prior to surgery", "candidate_expression": "((Hb) AND (anaemia) AND (cardiac surgery elective) AND (surgery) AND (trial drug available to receive 1- 10 weeks prior to surgery) AND ((females <120 g/L) OR (males <130 g/L)))"}
```
