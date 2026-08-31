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
{"candidate_id": "LLM02901", "doc_id": "NCT03118232_exc", "case_bucket": "other", "source_criterion": "Nursing homes will not be eligible to participate if they meet the following criteria: Facilities routinely using decolonization Dedicated psychiatric nursing homes Facilities with a resident population with >=20% combative patients Pediatric facilities", "candidate_expression": "((>=20%) AND (Nursing homes) AND (Pediatric facilities) AND (combative patients) AND (decolonization) AND (psychiatric nursing homes) AND (resident population) AND (routinely))"}
{"candidate_id": "LLM02902", "doc_id": "NCT02701777_exc", "case_bucket": "or", "source_criterion": "Uncontrolled medical problems including pulmonary, cardiovascular or orthopedic disease Any debilitating disease prior to the SCI that caused exercise intolerance Premorbid, ongoing major depression or psychosis, altered cognitive status History of head injury or stroke Metal plate in skull History of seizures Receiving drugs acting primarily on the central nervous system, which lower the seizure threshold (see appendix 2) Pregnant females Ongoing cord compression or a syrinx in the spinal cord or who suffer from a spinal cord disease such as spinal stenosis, spina bifida, MS, or herniated disk Individuals with scalp shrapnel, cochlear implants, or aneurysm clips.", "candidate_expression": "((History) AND (Metal plate in skull) AND (Pregnant) AND (Premorbid) AND (Uncontrolled) AND (altered cognitive status) AND (debilitating disease) AND (drugs acting primarily on the central nervous system) AND (exercise intolerance) AND (females) AND (lower the seizure threshold) AND (medical problems) AND (ongoing) AND (prior to the SCI) AND (seizures) AND (spinal cord) AND (the SCI) AND ((major depression) OR (psychosis)) AND ((head injury) OR (stroke)) AND ((cord compression) OR (spinal cord disease) OR (syrinx)) AND ((MS) OR (herniated disk) OR (spina bifida) OR (spinal stenosis)) AND ((aneurysm clips) OR (cochlear implants) OR (scalp shrapnel)) AND ((cardiovascular disease) OR (orthopedic disease) OR (pulmonary disease)))"}
{"candidate_id": "LLM02903", "doc_id": "NCT00344318_inc", "case_bucket": "or", "source_criterion": "Male or female between, and including, 6-12 weeks (42 to 90 days) of age at the time of the first vaccination. Subjects for whom the investigator believes that their parents/guardians can and will comply with the requirements of the protocol Written informed consent obtained from the parent or guardian of the subject. Free of obvious health problems as established by medical history and clinical examination before entering into the study. Born after a gestation period between 36 and 42 weeks.", "candidate_expression": "((Born) AND (Free) AND (Written informed consent) AND (at the time of the first vaccination) AND (between 36 and 42 weeks) AND (between 42 to 90 days) AND (between 6-12 weeks) AND (gestation period) AND (guardian) AND (health problems) AND (obvious) AND (of age) AND (parent))"}
{"candidate_id": "LLM02904", "doc_id": "NCT03460002_inc", "case_bucket": "other", "source_criterion": "Children aged 0-59 months living with families registered in the rural Bandim Health Project Health and Demographic Surveillance Site are included, provided a parent/guardian consent.", "candidate_expression": "((Children) AND (Person Surveillance Site) AND (aged 0-59 months) AND (living with families registered in the rural Bandim Health Project Health))"}
{"candidate_id": "LLM02905", "doc_id": "NCT00886158_exc", "case_bucket": "other", "source_criterion": "Lack of consent", "candidate_expression": "(Lack of consent)"}
{"candidate_id": "LLM02906", "doc_id": "NCT03381755_inc", "case_bucket": "scope", "source_criterion": "After half-dose ticagrelor (loading dose 90mg, and then 45mg bidpo.) treatment for 3 days, the platelet aggregation is effectively inhibited by light transmission aggregometry method and thromboela-stogram. planned to undergo PCI recently planned to DAPT for 1 year after PCI", "candidate_expression": "((45mg bidpo.) AND (90mg) AND (DAPT) AND (PCI) AND (after PCI) AND (effectively) AND (for 1 year) AND (half-dose) AND (inhibited) AND (light transmission aggregometry) AND (loading dose) AND (planned to) AND (planned to undergo) AND (platelet aggregation) AND (recently) AND (thromboela-stogram) AND (ticagrelor) AND (treatment for 3 days))"}
{"candidate_id": "LLM02907", "doc_id": "NCT00445029_inc", "case_bucket": "other", "source_criterion": "For both groups: Patients aged from 18 to 65 years old. Both genders eligible for study. Female participants must use a contraceptive method. Feasibility of patch testing. Participants must be able to understand and sign the Informed Consent, and comply with all aspects of the protocol. Patients must be registered in a social security system or with a health insurance coverage  First group: allergic patients Patients with allergic contact dermatitis to para-phenylenediamine (PPD) based on a history of PPD contact dermatitis and positive PPD patch tests.  Second group : healthy volunteers No history of PPD allergic contact dermatitis, with a negative PPD patch test.", "candidate_expression": "((Both genders) AND (Female) AND (PPD) AND (PPD patch test negative) AND (PPD patch tests positive) AND (aged from 18 to 65 years old) AND (allergic) AND (allergic contact dermatitis) AND (comply with all aspects of the protocol) AND (contact dermatitis) AND (contraceptive method) AND (health insurance coverage) AND (healthy) AND (para-phenylenediamine (PPD)) AND (patch testing Feasibility of) AND (registered in a social security system) AND (understand and sign the Informed Consent) AND NOT (allergic contact dermatitis))"}
{"candidate_id": "LLM02908", "doc_id": "NCT02541955_exc", "case_bucket": "or", "source_criterion": "Prior treatment with Acthar in the past 2mos Meet one of the above RA flare requirements Subjects who have received live or live attenuated vaccines within 6 weeks prior to the first dose of study drug (or the zoster vaccine)", "candidate_expression": "((Acthar) AND (Prior) AND (RA flare requirements) AND (first dose) AND (in the past 2mos) AND (live attenuated vaccines) AND (live vaccines) AND (one of) AND (study drug) AND (the first dose of study drug) AND (treatment) AND (within 6 weeks prior to the first dose of study drug) AND (zoster vaccine))"}
{"candidate_id": "LLM02909", "doc_id": "NCT02416869_exc", "case_bucket": "or", "source_criterion": "Heavy tobacco smokers Drug and / or alcohol abusers", "candidate_expression": "((Drug abusers) AND (Heavy tobacco smokers) AND (alcohol abusers))"}
{"candidate_id": "LLM02910", "doc_id": "NCT02749617_exc", "case_bucket": "or", "source_criterion": "Concomitant antiplatelet or anticoagulant use Calculated creatinine clearance < 30 mL/min by Cockcroft-Gault formula Alanine aminotransferase (ALT) or aspartate aminotransferase (AST) > 3 times upper limit of normal (ULN) Total bilirubin > 2 x ULN Thrombocytopenia < 50 x 10 gigalitres (Gl) High bleeding risk or spontaneously prolonged prothrombin time or activated partial thromboplastin time > 1.5 x ULN Body weight <50 or >120 kg Concomitant use of CYP3A4 or p-glycoprotein inducers or inhibitors Use of Ginkgo biloba or St. John's Wort within 14 days before first dose of study drug Dexamethasone use within last 3 months Women of Childbearing potential without proper contraceptive measures, pregnancy or breast feeding Life expectancy less than 3 months Inability to swallow or issues with malabsorption Any other medical, social, logistical, geographical or psychological factors, which in the opinion of the investigator, would prohibit follow-up, compliance and study completion", "candidate_expression": "((Any other medical, social, logistical, geographical or psychological factors, which in the opinion of the investigator, would prohibit follow-up, compliance and study completion) AND (Body weight) AND (Calculated creatinine clearance < 30 mL/min) AND (Cockcroft-Gault formula) AND (Dexamethasone within last 3 months) AND (Life expectancy less than 3 months) AND (Thrombocytopenia < 50 x 10 gigalitres (Gl)) AND (Total bilirubin > 2 x ULN) AND (Women) AND (study drug first dose) AND NOT (contraceptive measures) AND ((High bleeding risk) OR (activated partial thromboplastin time > 1.5 x ULN) OR (prolonged prothrombin time spontaneously)) AND ((anticoagulant Concomitant) OR (antiplatelet Concomitant)) AND ((<50 kg) OR (>120 kg)) AND ((CYP3A4 Concomitant) OR (p-glycoprotein inducers Concomitant) OR (p-glycoprotein inhibitors Concomitant)) AND ((Ginkgo biloba) OR (St. John's Wort)) AND ((Childbearing potential) OR (breast feeding) OR (pregnancy)) AND ((Inability to swallow) OR (issues with malabsorption)) AND ((Alanine aminotransferase (ALT) > 3 times upper limit of normal (ULN)) OR (aspartate aminotransferase (AST) > 3 times upper limit of normal (ULN))))"}
{"candidate_id": "LLM02911", "doc_id": "NCT02209545_inc", "case_bucket": "or", "source_criterion": "Patients presenting for abdominal myomectomy with documented uterine fibroids on pelvic imaging (pelvic ultrasound or MRI) within in last 12 months Age = 18 years and = 50 years Pre-operative hemoglobin >8 g/dl Willing to have buccal administration of misoprostol or a placebo at least one hour pre-procedure. Ability to understand and the willingness to sign a written informed consent. Admissible medical/surgical history Can be previously treated with Depo-Lupron, Depo-Provera, or Oral Contraceptive pills Intraoperative use of vasopressin and uterine tourniquet is permissible Can have had prior Cesarean delivery", "candidate_expression": "((= 18 years and = 50 years) AND (>8 g/dl) AND (Ability to understand a written informed consent) AND (Admissible) AND (Age) AND (Depo-Lupron) AND (Depo-Provera) AND (MRI pelvic) AND (Oral Contraceptive pills) AND (Pre-operative) AND (Willing to have) AND (abdominal myomectomy) AND (at least one hour pre-procedure) AND (buccal administration) AND (hemoglobin) AND (medical history) AND (misoprostol) AND (operative) AND (pelvic imaging) AND (pelvic ultrasound) AND (placebo) AND (previously) AND (surgical history) AND (treated) AND (uterine fibroids) AND (willingness to sign a written informed consent) AND (within in last 12 months))"}
{"candidate_id": "LLM02912", "doc_id": "NCT00094861_inc", "case_bucket": "or", "source_criterion": "Patients with a histologically or cytologically proven diagnosis of NSCLC Unresectable (locally advanced) stage IIIa or IIIb disease Initial radiotherapy field of treatment to encompass greater than or equal to 30% of the esophagus Life expectancy greater than or equal to 6 months Estimated weight loss less than or equal to 10% in the 3 months before study randomization Measurable disease 18 years of age or older Eastern Cooperative Oncology Group (ECOG) performance status of 0 - 2 Hemoglobin (hgb) greater than or equal to 10 g/dL without transfusional support or growth factor use in the 4 weeks before study randomization Absolute neutrophil count (ANC) greater than or equal to 1.5 x 10^9/L without growth factor use in the 2 weeks before study randomization Platelet count greater than or equal to 100 x 10^9/L Serum bilirubin less than or equal to 1.5 x institutional upper limit of normal (ULN) Serum creatinine less than or equal to 2.0 mg/dL (Note: Patients with a serum creatinine greater than or equal to 1.4 and less than or equal to 2.0 mg/dL must demonstrate a 24-hour urinary creatinine clearance greater than or equal to 50 mL/min) Females of childbearing potential: negative serum or urine pregnancy test Patient must give written informed consent before participating in any study-specific procedure, randomization, or receiving investigational product. Patients with reproductive capability must agree to practice adequate contraception methods.", "candidate_expression": "((24-hour urinary creatinine clearance) AND (ANC) AND (Absolute neutrophil count in the 2 weeks before study randomization) AND (ECOG) AND (Eastern Cooperative Oncology Group performance status 0 - 2) AND (Estimated weight loss 3 months before study randomization) AND (Females) AND (Hemoglobin in the 4 weeks before study randomization) AND (Life expectancy) AND (Measurable disease) AND (NSCLC locally advanced) AND (Platelet count) AND (Serum bilirubin) AND (Serum creatinine less than) AND (age 18 years or older) AND (childbearing potential) AND (contraception methods adequate) AND (hgb) AND (informed consent before participating in any study-specific procedure, randomization, or receiving investigational product participating in any study-specific procedure, randomization, or receiving investigational product) AND (radiotherapy Initial esophagus) AND (reproductive capability) AND (serum creatinine) AND NOT (growth factor use in the 2 weeks before study randomization) AND ((equal to 30%) OR (greater than 30)) AND ((equal to 6 months) OR (greater than 6 months)) AND ((cytologically proven) OR (histologically proven)) AND ((equal to 10%) OR (less than 10%)) AND ((equal to 10 g/dL) OR (greater than 10 g/dL)) AND ((growth factor use) OR (transfusional support)) AND ((equal to 1.5 x 10^9/L) OR (greater than 1.5 x 10^9/L)) AND ((equal to 100 x 10^9/L) OR (greater than 100 x 10^9/L)) AND ((equal to 1.5 x institutional upper limit of normal (ULN)) OR (less than 1.5 x institutional upper limit of normal (ULN))) AND ((stage IIIa disease) OR (stage IIIb disease)) AND ((2.0 mg/dL) OR (equal to 2.0 mg/dL)) AND ((equal to 1.4 mg/dL) OR (greater than 1.4 mg/dL)) AND ((equal to 2.0 mg/dL) OR (less than 2.0 mg/dL)) AND ((equal to 50 mL/min) OR (greater than 50 mL/min)) AND ((serum pregnancy test) OR (urine pregnancy test)) AND ((investigational product) OR (procedure) OR (randomization) OR (study-specific)))"}
{"candidate_id": "LLM02913", "doc_id": "NCT02810704_inc", "case_bucket": "or", "source_criterion": "Males and females 21 years of age or older; Undergoing elective primary, resurfacing arthroplasty, revision, or second stage re-implantation total hip replacement; Undergoing elective primary, revision, or second stage re-implantation total or uni compartmental knee replacement; Patient has necessary mental capacity to participate and is able to comply with study protocol requirements; Patient is willing and able to give informed consent; and Patient is willing to be randomized and participate.", "candidate_expression": "((21 years or older) AND (Patient has necessary mental capacity to participate and is able to comply with study protocol requirements) AND (Patient is willing and able to give informed consent) AND (Patient is willing to be randomized and participate) AND (age) AND (elective) AND (knee replacement) AND (total hip replacement) AND ((Males) OR (females)) AND ((primary) OR (revision) OR (second stage re-implantation total) OR (uni compartmental)) AND ((primary) OR (resurfacing arthroplasty) OR (revision) OR (second stage re-implantation)))"}
{"candidate_id": "LLM02914", "doc_id": "NCT02414399_exc", "case_bucket": "other", "source_criterion": "Contraindication to azithromycin use and other prophylactic antibiotic use", "candidate_expression": "((Contraindication) AND (azithromycin) AND (other) AND (prophylactic antibiotic use))"}
{"candidate_id": "LLM02915", "doc_id": "NCT00650312_exc", "case_bucket": "or", "source_criterion": "1. Institutionalized subjects will not be used. 2 Social Habits: 1. Use of any tobacco products. 2. Ingestion of any alcoholic, caffeine- or xanthine-containing food or beverage within the 48 hours prior to the initial dose of study medication. 3. Ingestion of any vitamins or herbal products within the 48 hours prior to the initial dose of the study medication. 4. Any recent, significant change in dietary or exercise habits. 5. Positive test for any drug included in the urine drug screen. 3. Medications: 1. Use of any medication within the 14 days prior to the initial dose of study medication. 2. Use of any medication known to alter hepatic enzyme activity within 28 days prior to the initial dose of study medication. 3. Use of hormonal contraceptives and hormonal replacement therapy within three months prior to the initial dose of study medication. 4. Diseases: a. History of any significant chronic disease and/or hepatitis. b. History of drug and/or alcohol abuse. c. Acute illness at the time of either the prestudy medical evaluation or dosing. d. Positive HIV, Hepatitis B, or Hepatitis C test. e. Renal disease or renal dysfunction (as suggested by serum creatinine levels greater than or equal to 1.5 mg/dL (for males) and greater than or equal to 1.4 mg/dL (for females) or abnormal creatinine clearance). 5. Abnormal and clinically significant laboratory test results: 1. Clinically significant deviation from the Guide for Clinically Relevant Abnormalities (see Part II ADMINISTRATIVE ASPECTS OF BIOEQUIVALENCE PROTOCOLS). 2. Abnormal and clinically relevant ECG tracing. 6. Donation or loss of a significant volume of blood or plasma (> 450 mL) within 28 days prior to the initial dose of study medication. 7. Subjects who have received an investigational drug within 30 days prior to the initial dose of study medication. 8. Allergy or hypersensitivity to metformin hydrochloride. 9. History of difficulty in swallowing medication, or any gastrointestinal disorder which could affect the drug absorption.", "candidate_expression": "((Abnormal ECG tracing) AND (Abnormal and clinically significant laboratory test results:) AND (Clinically significant) AND (affect the drug absorption) AND (clinically relevant) AND (hormonal contraceptives within three months prior) AND (hormonal replacement therapy within three months prior) AND (medication known to alter hepatic enzyme activity within 28 days prior) AND (medication within the 14 days prior) AND (metformin hydrochloride) AND (significant) AND (tobacco products) AND ((chronic disease significant) OR (hepatitis significant)) AND ((alcohol abuse History) OR (drug abuse History)) AND ((HIV test) OR (Hepatitis B test) OR (Hepatitis C test)) AND ((Renal disease) OR (renal dysfunction)) AND ((females greater than or equal to 1.4 mg/dL) OR (males greater than or equal to 1.5 mg/dL)) AND ((abnormal creatinine clearance) OR (serum creatinine levels)) AND ((Allergy) OR (hypersensitivity)) AND ((difficulty in swallowing medication History) OR (gastrointestinal disorder affect the drug absorption)))"}
{"candidate_id": "LLM02916", "doc_id": "NCT03156855_exc", "case_bucket": "other", "source_criterion": "NA", "candidate_expression": "(EMPTY)"}
{"candidate_id": "LLM02917", "doc_id": "NCT01228279_exc", "case_bucket": "or", "source_criterion": "Diabetes Mellitus Acute coronary syndrome in the past 6 months Cardiac arrhythmias (2nd and 3rd degree heart block or premature ventricular complexes in Lown classes 4 or 5) Symptoms suggestive of obstructive or central sleep apnea (with a score of > 10 on Epworth sleepiness scale) Patients taking Clonidine Body mass index (BMI) > 34 Patients unable to give consent Pregnant women Patients with leg injury involving nerve damage Patients taking anticoagulant medication Patients with significant bleeding disorder or liver disorder Hemoglobin <1.05 g/dl at the time of initiation of therapy patients with unilateral or bilateral nephrectomy Planned kidney transplant in the next 4 months Life expectancy under 6 months Oliguria (urine output less than 400 ml per day)", "candidate_expression": "((2nd degree heart block) AND (3rd degree heart block) AND (Acute coronary syndrome in the past 6 months) AND (BMI) AND (Body mass index > 34) AND (Cardiac arrhythmia) AND (Clonidine) AND (Diabetes Mellitus) AND (Epworth sleepiness scale score of > 10) AND (Hemoglobin <1.05 g/dl at the time of initiation of therapy) AND (Life expectancy under 6 months) AND (Oliguria) AND (Patients unable to give consent) AND (Pregnant women) AND (anticoagulant) AND (bleeding disorder significant) AND (central sleep apnea) AND (kidney transplant Planned in the next 4 months) AND (leg injury) AND (liver disorder) AND (nephrectomy unilateral bilateral) AND (nerve damage) AND (obstructive sleep apnea) AND (premature ventricular complexes Lown classes 4 Lown classes 5) AND (urine output less than 400 ml per day))"}
{"candidate_id": "LLM02918", "doc_id": "NCT03103204_exc", "case_bucket": "or", "source_criterion": "Systemic diseases (diabetes, renal diseases, rheumatic diseases, osteoporosis and cardiovascular diseases) Pregnant and lactating women HIV/ AIDS periodontal treatment in the last year (before baseline appointment) Medication: Immunosuppressive drugs, antibiotics in the past three months (before baseline appointment) ) orthodontic appliance", "candidate_expression": "((AIDS) AND (HIV) AND (Systemic diseases) AND (baseline appointment) AND (orthodontic appliance) AND (periodontal treatment in the last year before baseline appointment) AND (women) AND ((Immunosuppressive drugs) OR (antibiotics)) AND ((Pregnant) OR (lactating)))"}
{"candidate_id": "LLM02919", "doc_id": "NCT02525991_exc", "case_bucket": "or", "source_criterion": "Patient diagnosed with dementia. Patients with serious and unstable illnesses including current hepatic, renal, gastroenterologic, respiratory, cardiovascular (including ischemic heart disease and congestive heart failure), endocrinologic, neurologic (including stroke, transient ischemic attack, subarachnoidal bleeding, brain tumor, encephalopathy, and meningitis). Patients with a history of allergic reactions to loxapine or amoxapine Patients who have received an investigational drug within 30 days prior to the current agitation episode must be excluded. Patients who are considered by the investigator, for any reason, to be unable to self-administer the inhalation device.", "candidate_expression": "((Patients who are considered by the investigator, for any reason, to be unable to self-administer the inhalation device) AND (Patients who have received an investigational drug within 30 days prior to the current agitation episode must be excluded) AND (allergic reactions) AND (dementia) AND (serious) AND (unstable) AND ((congestive heart failure) OR (ischemic heart disease)) AND ((brain tumor) OR (encephalopathy) OR (meningitis) OR (stroke) OR (subarachnoidal bleeding) OR (transient ischemic attack)) AND ((amoxapine) OR (loxapine)) AND ((cardiovascular) OR (endocrinologic) OR (gastroenterologic) OR (hepatic) OR (neurologic) OR (renal) OR (respiratory)))"}
{"candidate_id": "LLM02920", "doc_id": "NCT01567605_inc", "case_bucket": "other", "source_criterion": "traumatic spinal cord injury at least one year ago regular bowel care routine (at least four weeks)", "candidate_expression": "((at least four weeks) AND (at least one year ago) AND (regular bowel care routine) AND (traumatic spinal cord injury))"}
{"candidate_id": "LLM02921", "doc_id": "NCT01701219_exc", "case_bucket": "or", "source_criterion": "1. For subjects in Cohort A: previous therapy for more than 48 hours with any parenteral antibiotic with activity against S. aureus within 72 hours of positive blood culture results. 2. For subjects in Cohort B: previous therapy for more than 48 hours with any parenteral antibiotic with activity against MRSA, except vancomycin and/or daptomycin, within 72 hours of positive blood culture results confirming persistence. 3. Previous episode of S. aureus bacteremia within 3 months. 4. Known left-sided endocarditis or prosthetic heart valve. 5. Osteomyelitis or prosthetic joint infection except new onset nonhardware-associated vertebral osteomyelitis. 6. History of any hypersensitivity or allergic reaction to any β-lactam antibacterial agent. 7. Evidence of significant hepatic, hematologic, or immunologic impairment. 8. Pregnant or nursing females.", "candidate_expression": "((Cohort A) AND (Cohort B) AND (History) AND (MRSA) AND (S. aureus) AND (S. aureus bacteremia) AND (blood culture) AND (daptomycin) AND (except) AND (females) AND (for more than 48 hours) AND (left-sided) AND (new onset) AND (nonhardware-associated) AND (parenteral) AND (parenteral antibiotic with activity against MRSA) AND (parenteral antibiotic with activity against S. aureus) AND (positive blood culture results) AND (positive results) AND (previous) AND (therapy) AND (vancomycin) AND (vertebral osteomyelitis) AND (with activity against MRSA) AND (with activity against S. aureus) AND (within 3 months) AND (within 72 hours of positive blood culture results) AND (β-lactam antibacterial agent) AND ((left-sided endocarditis) OR (prosthetic heart valve)) AND ((Osteomyelitis) OR (prosthetic joint infection)) AND ((allergic reaction) OR (hypersensitivity)) AND ((hematologic impairment) OR (hepatic impairment) OR (immunologic impairment)) AND ((Pregnant) OR (nursing)))"}
{"candidate_id": "LLM02922", "doc_id": "NCT00720031_inc", "case_bucket": "or", "source_criterion": "HLA-A2 melanoma patients with : either loco-regional or lymph node metastasis transit nodules not surgically resectable measurable cutaneous or visceral metastasis Patients' tumor express Melan-A/MART-1 antigen. No chemotherapy treatment (except for Deticene used before the first T cell clones infusion) or radiotherapy or immunotherapy in the last 4 weeks before infusion. No other melanoma treatment during the protocol. Life expectancy should be greater than 6 months. General state with Karnowsky greater than 80, ECOG = 0, 1 or 2. Patient should be negative for HIV and B and C hepatitis. Biological parameters at the beginning of the study: leucocytes ³ 2000 elements per mm3, hemoglobin ³ 10.5g/dl, platelets ³ 100 000 per mm3, phosphatases alcalines transaminases £ 1 time 1/2 compared to the normal. Signed informed consent", "candidate_expression": "((0, 1 or 2) AND (B hepatitis) AND (C hepatitis) AND (Deticene) AND (ECOG) AND (HIV) AND (HLA-A2) AND (Karnowsky) AND (Life expectancy) AND (MART-1 antigen) AND (Melan-A antigen) AND (No) AND (Signed informed consent) AND (at the beginning of the study) AND (before the first T cell clones infusion) AND (during the protocol) AND (except for) AND (greater than 6 months) AND (greater than 80) AND (hemoglobin) AND (in the last 4 weeks before infusion) AND (infusion) AND (leucocytes) AND (measurable) AND (melanoma) AND (negative) AND (not) AND (phosphatases alcalines transaminases) AND (platelets) AND (surgically) AND (surgically resectable) AND (the beginning of the study) AND (the first T cell clones infusion) AND (transit nodules) AND (treatment) AND (£ 1 time 1/2 compared to the normal) AND (³ 10.5g/dl) AND (³ 100 000 per mm3) AND (³ 2000 elements per mm3) AND ((cutaneous metastasis) OR (visceral metastasis)) AND ((chemotherapy) OR (immunotherapy) OR (radiotherapy)) AND ((loco-regional metastasis) OR (lymph node metastasis)))"}
{"candidate_id": "LLM02923", "doc_id": "NCT02707874_inc", "case_bucket": "other", "source_criterion": "Inpatients having major foot and ankle surgery that will benefit from continuous popliteal sciatic nerve block with an indwelling catheter American Society Anesthesiologists (ASA) physical status I-III 18-85 years of age, inclusive 40-120 kg, inclusive 150 cm of height or greater", "candidate_expression": "((150 cm or greater) AND (18-85 years) AND (40-120) AND (ASA) AND (American Society Anesthesiologists physical status) AND (I-III) AND (Inpatients) AND (age) AND (continuous) AND (height) AND (indwelling catheter) AND (kg) AND (major foot and ankle surgery) AND (popliteal sciatic nerve block))"}
{"candidate_id": "LLM02924", "doc_id": "NCT02886962_exc", "case_bucket": "or", "source_criterion": "Formal indication to oral anticoagulation beside atrial fibrillation (mechanic heart valves, recurrent thrombophlebitis, antiphospholipid syndrome) Life expectancy < 6 months (e.g., terminal cancer) Live donor transplantation scheduled within 6 months Pregnancy (ß-HCG blood-based assay)or nursing (lactating) women Women of child bearing potential, unless they are using an effective method of birth control Patient under legal guardianship Patients under law protection Known hypersensibility to coumadin or indoine derivatives or to any excipients (CI to oral AVK) Severe liver failure (CI to oral AVK)", "candidate_expression": "((< 6 months) AND (Life expectancy) AND (Live donor transplantation) AND (Pregnancy (ß-HCG blood-based assay)or nursing (lactating) women) AND (Severe) AND (Women of child bearing potential, unless they are using an effective method of birth control) AND (antiphospholipid syndrome) AND (atrial fibrillation) AND (coumadin) AND (hypersensibility) AND (indication) AND (indoine) AND (liver failure) AND (mechanic heart valves) AND (oral anticoagulation) AND (recurrent thrombophlebitis) AND (scheduled) AND (terminal cancer) AND (within 6 months))"}
{"candidate_id": "LLM02925", "doc_id": "NCT03156855_exc", "case_bucket": "other", "source_criterion": "NA", "candidate_expression": "(EMPTY)"}
```
