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
{"candidate_id": "LLM03176", "doc_id": "NCT02579928_exc", "case_bucket": "or", "source_criterion": "Current inpatient hospitalization or active suicidal ideation requiring referral for inpatient hospitalization for safety. History of psychotic disorder or manic episode diagnosed by MINI-KID History of substance dependence diagnosis by MINI-KID (excluding tobacco) or positive urine toxicology. Pregnancy (urine pregnancy tests on the day of scans for menstruating girls). Inability to provide written informed consent according to the Yale Human Investigation Committee (HIC) guidelines in English.", "candidate_expression": "((Current) AND (History) AND (Inability to provide) AND (MINI-KID) AND (Pregnancy) AND (Yale Human Investigation Committee (HIC) guidelines) AND (active) AND (excluding) AND (hospitalization) AND (in English) AND (inpatient) AND (inpatient hospitalization) AND (manic episode) AND (menstruating girls) AND (on the day of scans) AND (positive) AND (psychotic disorder) AND (referral) AND (requiring) AND (substance dependence) AND (suicidal ideation) AND (tobacco) AND (urine pregnancy tests) AND (urine toxicology) AND (written informed consent))"}
{"candidate_id": "LLM03177", "doc_id": "NCT00718952_exc", "case_bucket": "or", "source_criterion": "The other types of pulmonary hypertension. Subjects who refuse to subscribe written informed consents or can't cooperate with the trial well. Subjects with serious acute or chronic disease involved liver, kidney, and brain or have to use potent CYP3A4-inhibitor or nitrate to treat the underlying diseases. Subjects who are currently treated with sildenafil for PAH or taking sildenafil or tadalafil. Other contraindications in package insert.", "candidate_expression": "((PAH) AND (contraindications in package insert) AND (pulmonary hypertension other types) AND (underlying diseases) AND ((sildenafil) OR (tadalafil)) AND ((can't cooperate with the trial) OR (refuse to subscribe written informed consents)) AND ((chronic disease involved brain) OR (chronic disease involved kidney) OR (chronic disease involved liver)) AND ((CYP3A4-inhibitor) OR (nitrate)))"}
{"candidate_id": "LLM03178", "doc_id": "NCT03034733_inc", "case_bucket": "other", "source_criterion": "primary total knee replacement surgery ASA (american society of anesthesiologists) class 1-3", "candidate_expression": "((1-3) AND (ASA class) AND (american society of anesthesiologists) AND (primary) AND (total knee replacement surgery))"}
{"candidate_id": "LLM03179", "doc_id": "NCT02827526_inc", "case_bucket": "or", "source_criterion": "Patients presenting for elective posterior spinal fusion surgery (lower thoracic, lumbar, sacral) Ages 18-80", "candidate_expression": "((18-80) AND (Ages) AND (elective) AND (posterior spinal fusion surgery) AND ((lower thoracic) OR (lumbar) OR (sacral)))"}
{"candidate_id": "LLM03180", "doc_id": "NCT03339284_exc", "case_bucket": "or", "source_criterion": "age under 18y or over 85y diabetes type 1 with complications no co-operation or inadequate finnish language skills persistent pain for other reason severe hepatic insufficiency or paracetamol (acetaminophen) is contraindicated for other reason any type of steroid in regular use oxycodone contraindicated medications changing notably paracetamol (acetaminophen) and/or ropivacaine metabolism in regular use", "candidate_expression": "((acetaminophen) AND (age under 18y or over 85y) AND (complications) AND (contraindicated) AND (diabetes type 1) AND (oxycodone) AND (paracetamol) AND (persistent pain other reason) AND (steroid regular use) AND ((contraindicated) OR (hepatic insufficiency severe)) AND ((paracetamol) OR (ropivacaine)) AND ((inadequate finnish language skills) OR NOT (co-operation)))"}
{"candidate_id": "LLM03181", "doc_id": "NCT02689024_exc", "case_bucket": "or", "source_criterion": "multiple injuries (polytrauma patients) previous adverse reaction or known allergy to local anaesthetics or opioids or paracetamol skin infection in proximity of injection site delirious state at presentation in the ED", "candidate_expression": "((delirious) AND (injection site) AND (multiple injuries) AND (polytrauma) AND (skin infection) AND ((adverse reaction) OR (allergy)) AND ((local anaesthetics) OR (opioids) OR (paracetamol)))"}
{"candidate_id": "LLM03182", "doc_id": "NCT03226080_inc", "case_bucket": "other", "source_criterion": "ASA I-IV Age 55 or older Scheduled for operative repair of isolated intertrochanteric hip fracture", "candidate_expression": "((55 or older) AND (ASA) AND (Age) AND (I-IV) AND (Scheduled for) AND (intertrochanteric hip fracture) AND (isolated) AND (operative repair))"}
{"candidate_id": "LLM03183", "doc_id": "NCT03140423_inc", "case_bucket": "other", "source_criterion": "Inclusion criteria includes all U.S. HCA hospitals with an adult ICU; Note: Unit of randomization is the hospital, but the participants are hospital adult ICUs All patients within adult ICUs are included, including rare patients <18 years and >=12 years.", "candidate_expression": "((<18 years and >=12 years) AND (HCA hospitals) AND (U.S.) AND (adult) AND (adult ICU) AND (adult ICUs) AND (rare patients) AND (year))"}
{"candidate_id": "LLM03184", "doc_id": "NCT02202369_exc", "case_bucket": "or", "source_criterion": "Patients with liver disease (documented liver function test abnormality) Patients with renal disease (documented glomerular filtration rate < 60mL/min/1.73m2) Patients with a baseline (pre-operative) opioid use greater than 30 mg of morphine equivalents/day. Patients with active alcohol dependence Patients with active illicit drug dependence Patients < 18 years of age and >70 years of age Patients allergic to any medication given in either arm (list medications) Patients who have a seizure disorder", "candidate_expression": "((< 18 years) AND (< 60mL/min/1.73m2) AND (>70 years) AND (abnormality) AND (age) AND (alcohol dependence) AND (allergic) AND (baseline) AND (glomerular filtration rate) AND (greater than 30 mg of morphine equivalents/day) AND (illicit drug dependence) AND (liver disease) AND (liver function test) AND (medication) AND (opioid) AND (pre-operative) AND (renal disease) AND (seizure disorder))"}
{"candidate_id": "LLM03185", "doc_id": "NCT01929434_exc", "case_bucket": "or", "source_criterion": "Intracranial infection. Severe respiratory and circulatory system diseases. Hematologic malignancies. Positive serological tests such as AIDS, hepatitis B virus, hepatitis C virus and syphilis （antigen or antibody）. Tumors. Genetic and metabolic diseases.", "candidate_expression": "((Hematologic malignancies) AND (Intracranial infection) AND (Tumors) AND ((Genetic diseases) OR (metabolic diseases)) AND ((circulatory system disease) OR (respiratory system disease)) AND ((AIDS) OR (hepatitis B virus) OR (hepatitis C virus) OR (syphilis)))"}
{"candidate_id": "LLM03186", "doc_id": "NCT02483715_exc", "case_bucket": "or", "source_criterion": "pregnant or nursing woman serious concomitant illness and malignant tumor of any kind history of hypersensitivity to test drugs serious bleeding during the course of the ulcer previous gastric surgery receiving bismuth salts, PPIs, or antibiotics in the previous month.", "candidate_expression": "((PPIs) AND (antibiotics) AND (any kind) AND (bismuth salts) AND (bleeding) AND (concomitant) AND (during the course of the ulcer) AND (gastric surgery) AND (history of) AND (hypersensitivity) AND (illness) AND (in the previous month) AND (malignant tumor) AND (nursing) AND (pregnant) AND (previous) AND (serious) AND (test drugs) AND (woman))"}
{"candidate_id": "LLM03187", "doc_id": "NCT01518946_exc", "case_bucket": "or", "source_criterion": "1. The subject is a pregnant or lactating female. 2. The subject has pre-existing sustained supine hypertension greater than 180mmHg systolic and 110mmHg diastolic BP or had these measurements at the Screening Visit. Sustained is defined as persistently greater at 2 separate measurements at least 5 minutes apart with the subject supine and at rest for the 5 minutes. 3. Subjects taking concomitant medications of interest are excluded unless those medications are reviewed and discussed with the Medical Monitor or Study Physician and documented prior to enrolling the subject. If agreement is reached between the Investigator and Sponsor for the subject to continue in the study, all allowed medications should be maintained at a constant dose throughout the study. 4. The Principal Investigator deems any clinical laboratory test (at the Screening Visit) abnormality to be clinically significant 5. The subject has participated in other studies of investigational drugs or devices within 30 days prior to enrollment in this study (other than Study SPD426-406). 6. Current or relevant history of physical or psychiatric illness, any medical disorder that may require treatment or make the subject unlikely to fully comply with the requirements of the study or complete the study, or any condition that presents undue risk from the investigational product or study procedures. 7. The subject has a concurrent chronic or acute illness, disability, or other condition (including significant unexpected laboratory or electrocardiogram [ECG] findings) that might confound the results of the tests and/or measurements administered in this study, or that might have increased the risk to the subject. 8. Known or suspected intolerance or hypersensitivity to the investigational product(s), closely-related compounds, or any of the stated ingredients. 9. Prior enrollment failure or randomization in this study. 10. History of alcohol abuse or other substance abuse within the last year.", "candidate_expression": "((110mmHg diastolic) AND (2 separate at least 5 minutes apart) AND (BP) AND (Current or relevant history of physical or psychiatric illness, any medical disorder that may require treatment or make the subject unlikely to fully comply with the requirements of the study or complete the study, or any condition that presents undue risk from the investigational product or study procedures.) AND (Screening Visit) AND (The Principal Investigator deems any clinical laboratory test (at the Screening Visit) abnormality to be clinically significant) AND (The subject has participated in other studies of investigational drugs or devices within 30 days prior to enrollment in this study (other than Study SPD426-406).) AND (acute illness) AND (alcohol abuse) AND (at the Screening Visit) AND (chronic illness) AND (concomitant) AND (disability) AND (electrocardiogram [ECG]) AND (electrocardiogram [ECG] findings) AND (enrollment failure) AND (female) AND (greater) AND (greater than 180mmHg systolic) AND (laboratory findings) AND (lactating) AND (measurements) AND (medications of interest) AND (other condition) AND (persistently) AND (pre-existing) AND (pregnant) AND (substance abuse) AND (supine hypertension) AND (sustained) AND (within the last year))"}
{"candidate_id": "LLM03188", "doc_id": "NCT03518034_exc", "case_bucket": "or", "source_criterion": "Participants with congenital or acquired hypogonadism for whom long-term therapy with placebo would not be medically appropriate Participants with prostate specific antigen (PSA) > 3.0 ng/mL (or 1.5 if on 5-alpha reductase inhibitors) Participants who have been treated with testosterone in the past 6 months and for whom testosterone therapy is contraindicated Confirmed testosterone < 100 ng/dL Body Mass Index (BMI) > 50 Hemoglobin A1c (HbA1C) > 11% Hematocrit (Hct) > 50% Estimated Glomerular Filtration Rate (eGFR) < 30 ml/min History of deep vein thrombosis or pulmonary embolism or prostate cancer or heart failure (Class III and IV).", "candidate_expression": "((1.5) AND (< 100 ng/dL) AND (< 30 ml/min) AND (> 11%) AND (> 50) AND (> 50%) AND (Body Mass Index (BMI)) AND (Confirmed testosterone) AND (Estimated Glomerular Filtration Rate (eGFR)) AND (Hematocrit (Hct)) AND (Hemoglobin A1c (HbA1C)) AND (contraindicated) AND (in the past 6 months) AND (prostate specific antigen (PSA)) AND (testosterone) AND (testosterone therapy) AND ((acquired hypogonadism) OR (congenital hypogonadism)) AND ((deep vein thrombosis) OR (heart failure) OR (prostate cancer) OR (pulmonary embolism)) AND ((Class III) OR (Class IV)) AND ((5-alpha reductase inhibitors) OR (> 3.0 ng/mL)))"}
{"candidate_id": "LLM03189", "doc_id": "NCT03479502_inc", "case_bucket": "other", "source_criterion": "18 years of age and older, diagnosis of stage II adhesive capsulitis as determined by clinical examination of the treating physician, and absence of abnormal findings on X-ray.", "candidate_expression": "((18 years and older) AND (X-ray) AND (abnormal findings) AND (absence of) AND (adhesive capsulitis) AND (age) AND (as determined by clinical examination) AND (clinical examination) AND (stage II))"}
{"candidate_id": "LLM03190", "doc_id": "NCT02957877_inc", "case_bucket": "other", "source_criterion": "Prevalent NHHD patients who have received >1 year dialysis with unfractionated heparin as anticoagulant Age >= 18 Informed consent available", "candidate_expression": "((Age >= 18) AND (NHHD) AND (anticoagulant) AND (dialysis >1 year) AND (unfractionated heparin))"}
{"candidate_id": "LLM03191", "doc_id": "NCT02804126_exc", "case_bucket": "or", "source_criterion": "coagulopathy allergy to to local anesthetics depression, antidepressant drugs treatment epilepsy usage of painkiller before surgery addiction to alcohol or recreational drugs", "candidate_expression": "((allergy) AND (antidepressant drugs) AND (coagulopathy) AND (depression) AND (epilepsy) AND (local anesthetics) AND (painkiller before surgery) AND ((addiction to alcohol) OR (addiction to recreational drugs)))"}
{"candidate_id": "LLM03192", "doc_id": "NCT02704754_exc", "case_bucket": "or", "source_criterion": "Psychiatric disorders other than insomnia, PTSD and specific phobias; including bipolar and psychotic disorders and meeting criteria for DSM-5 moderate alcohol or drug use disorders within the past year. Diagnosis of a sleep disorder other than insomnia including PSG findings of apnea/hypopnea or periodic limb movement indices > 10/hour; Medical conditions that require consistent use of medication or compromise sleep; History of moderate to severe traumatic brain injury or mild traumatic brain injury with ongoing post-concussive symptoms; Suicidal ideation with intent to act or with specific plan and intent in the past 6 months (Type 4 - 5 ideation on the Columbia Suicide Severity Rating Scale) or a concerning history of prior suicidal behavior. Caffeine use exceeding 5 cups of coffee per day or its equivalent; Habitual bedtimes after 3 AM, habitual rise times after 10 AM, or habitual napping > 1hour/day; Pregnancy or breastfeeding, or expecting to conceive while in study; Positive urine toxicology.", "candidate_expression": "((Caffeine) AND (Columbia Suicide Severity Rating Scale) AND (Pregnancy or breastfeeding, or expecting to conceive while in study) AND (Psychiatric disorders) AND (Suicidal ideation past 6 months) AND (post-concussive symptoms) AND (sleep disorder) AND (suicidal behavior.) AND (urine toxicology Positive) AND NOT (insomnia) AND ((alcohol use disorders) OR (drug use disorders)) AND ((apnea) OR (hypopnea)) AND ((PSG) OR (periodic limb movement indices > 10/hour)) AND ((traumatic brain injury) OR (traumatic brain injury mild)) AND ((moderate) OR (severe)) AND ((Type 4 ideation) OR (Type 5 ideation)) AND ((PTSD) OR (insomnia) OR (phobias)) AND ((bipolar) OR (psychotic disorders)))"}
{"candidate_id": "LLM03193", "doc_id": "NCT02267616_inc", "case_bucket": "other", "source_criterion": "Women age 18-45 Within 6 months of expiration or beyond the end of the FDA-approved duration of use of the levonorgestrel intrauterine device (LNG-IUD = 5 years) OR the etonogestrel-releasing subdermal implant (ENG implant = 3 years) Able to consent in English or Spanish. Not pregnant at the time of enrollment", "candidate_expression": "((Able to consent in English or Spanish) AND (Women) AND (age 18-45) AND NOT (pregnant at the time of enrollment))"}
{"candidate_id": "LLM03194", "doc_id": "NCT02760251_inc", "case_bucket": "or", "source_criterion": "Informed consent as documented by signature (see informed consent form) Primary ITP according to the definition of Rodeghiero et al. (52) and a platelet count of <30x109/l Age range: 18-45 years Previously treated patients, with failure or intolerance to first-line therapy, or relapse after first-line therapy, i.e. corticosteroids, intravenous immunoglobulin (IVIG), or anti-D immunoglobulins", "candidate_expression": "((Age 18-45 years) AND (IVIG) AND (Informed consent as documented by signature (see informed consent form)) AND (Previously treated) AND (Primary ITP) AND (anti-D immunoglobulins) AND (corticosteroids) AND (definition of Rodeghiero) AND (first-line therapy) AND (first-line therapy failure intolerance) AND (intravenous immunoglobulin) AND (platelet count <30x109/l) AND (relapse after first-line therapy))"}
{"candidate_id": "LLM03195", "doc_id": "NCT02510404_exc", "case_bucket": "or", "source_criterion": "1. Patients with other uncontrolled infections (see 2.3.2 for definitions) 2. Patients who received ATG, Campath, or other T cell immunosuppressive monoclonal antibodies in the last 28 days 3. Received donor lymphocyte infusion in last 28 days 4. Diagnosis of Omenn's syndrome or MHC class I deficiency 5. Active and uncontrolled malignancy 6. Pregnant or lactating 7. Unable to wean steroids to ≤0.5 mg/kg/day prednisone. 8. Patients with Grade 3 hyperbilirubinemia", "candidate_expression": "((donor lymphocyte infusion in last 28 days) AND (hyperbilirubinemia Grade 3) AND (malignancy Active uncontrolled) AND (other uncontrolled infections) AND (prednisone ≤0.5 mg/kg/day) AND (steroids) AND NOT (wean) AND ((ATG) OR (Campath) OR (T cell immunosuppressive monoclonal antibodies)) AND ((MHC class I deficiency) OR (Omenn's syndrome)) AND ((Pregnant) OR (lactating)))"}
{"candidate_id": "LLM03196", "doc_id": "NCT03260881_inc", "case_bucket": "or", "source_criterion": "T2DM as defined by American Diabetes Association (ADA) criteria Adult patients with T2DM who are indicated to receive liraglutide, not as first-line therapy, in addition to diet and exercise to improve glycemic control Hemoglobin A1c (HbA1c) = 9% Age = 18 years old Body mass index (BMI) = 27 Kg/m2 and/or waist circumference = 102 cm (40 inches) in men and 88 cm (35 inches) in women, respectively. Clinically and angiographically stable CAD who requires CABG as part of the standard medical care, as CAD does not represent a contraindication for using liraglutide. The stability of the CAD further warranties that study patients will not be exposed to higher risk by using liraglutide", "candidate_expression": "((40 inches) AND (Adult) AND (Age = 18 years old) AND (CABG requires) AND (CAD Clinically stable angiographically stable 35 inches) AND (Hemoglobin A1c (HbA1c) = 9%) AND (T2DM) AND (T2DM American Diabetes Association (ADA) criteria) AND (liraglutide indicated to receive first-line therapy) AND ((Body mass index (BMI) = 27 Kg/m2) OR (waist circumference)) AND ((men = 102 cm) OR (women 88 cm)))"}
{"candidate_id": "LLM03197", "doc_id": "NCT03066440_inc", "case_bucket": "or", "source_criterion": "Age between 0 and 18 years Venous pH less than 7.25 Ketonuria as confirmed on urine point-of-care testing or urinalysis Hyperglycemia (Serum glucose > 200 mg/dl) Serum bicarbonate <15 mmol/L PICU admission", "candidate_expression": "((Age between 0 and 18 years) AND (Hyperglycemia) AND (Ketonuria) AND (PICU) AND (Serum bicarbonate <15 mmol/L) AND (Serum glucose > 200 mg/dl) AND (Venous pH less than 7.25) AND (admission) AND ((urinalysis) OR (urine point-of-care testing)))"}
{"candidate_id": "LLM03198", "doc_id": "NCT02686021_inc", "case_bucket": "scope", "source_criterion": "planned sequential both-sided lower third molar extraction (split-mouth) with osteotomy (with or without upper molar extraction in local anesthesia) able to understand the study and the NRS scale", "candidate_expression": "((able to understand the study) AND (both-sided) AND (local anesthesia) AND (lower third molar extraction) AND (osteotomy) AND (planned) AND (sequential) AND (split-mouth) AND (upper molar extraction))"}
{"candidate_id": "LLM03199", "doc_id": "NCT00122070_inc", "case_bucket": "other", "source_criterion": "Provide written informed consent before beginning any study related activities Be between age 18 and 55 years Be able to speak, read and write English and follow simple instructions for completing self-rated scales Meet DSM-IV criteria for BPD as assessed by the Structured Clinical Interview for DSM-IV Personality Disorders (SCID-II).", "candidate_expression": "((BPD) AND (Meet DSM-IV criteria) AND (Structured Clinical Interview for DSM-IV Personality Disorders (SCID-II)) AND (able to follow simple instructions) AND (able to speak, read and write English) AND (age) AND (any study related activities) AND (before beginning any study related activities) AND (between 18 and 55 years) AND (written informed consent))"}
{"candidate_id": "LLM03200", "doc_id": "NCT02542956_exc", "case_bucket": "other", "source_criterion": "A medical condition that could interfere with study participation Body weight less than 50 kg Participating in another study involving an investigational medication", "candidate_expression": "((Body weight less than 50 kg) AND (Participating in another study involving an investigational medication))"}
```
