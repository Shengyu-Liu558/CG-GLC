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
{"candidate_id": "LLM00226", "doc_id": "NCT02951832_inc", "case_bucket": "or", "source_criterion": "Women aged 20-49; Having a regular menstrual cycle of which the menstrual period is between day 3-7, and the period between day 25-35; Excluding internal and surgical disease (after having variety of physical examination such as electrocardiogram/hepatic and renal function/blood routine and urine routine).", "candidate_expression": "((20-49) AND (Women) AND (aged) AND (internal disease) AND (menstrual period) AND (regular menstrual cycle) AND (surgical disease) AND ((between day 25-35) OR (between day 3-7)))"}
{"candidate_id": "LLM00227", "doc_id": "NCT01314898_inc", "case_bucket": "or", "source_criterion": "Male and/or female healthy volunteers, age 18 to 55 years. Females must be of non-childbearing potential. Body Mass Index (BMI) of 17.5 to 30.5 kg/m2; and a total body weight >50 kg (110 lbs). Subjects who are willing and able to comply with scheduled visits, treatment plan, laboratory tests, diet restrictions and other trial procedures.", "candidate_expression": "((Body Mass Index (BMI) 17.5 to 30.5 kg/m2) AND (Females) AND (Subjects who are willing and able to comply with scheduled visits, treatment plan, laboratory tests, diet restrictions and other trial procedures.) AND (age 18 to 55 years) AND (healthy) AND (total body weight >50 kg (110 lbs)) AND NOT (childbearing potential) AND ((Male) OR (female)))"}
{"candidate_id": "LLM00228", "doc_id": "NCT01346436_exc", "case_bucket": "other", "source_criterion": "Age <18 years old Patient unable to communicate or to understand the study Patient refusing to participate to the study contraindication to laparoscopy", "candidate_expression": "((Age <18 years old) AND (Patient refusing to participate to the study) AND (Patient unable to communicate or to understand the study) AND (contraindication) AND (laparoscopy))"}
{"candidate_id": "LLM00229", "doc_id": "NCT00576173_inc", "case_bucket": "or", "source_criterion": "Patients with a histologically, radiologically or haematologically confirmed malignancy whose pain is judged by the investigator to be caused by the malignancy Patients must have been on a stable daily dose of weak opioids or strong opioids for at least 72 hours prior to the start the study and must remain at the same dosage for the duration of the study Patients must have a VAS (Visual analog scale) >=40mm", "candidate_expression": "((>=40mm) AND (VAS (Visual analog scale)) AND (at least 72 hours prior to the start the study) AND (confirmed) AND (malignancy) AND (pain) AND ((haematologically) OR (histologically) OR (radiologically)) AND ((strong opioids) OR (weak opioids)))"}
{"candidate_id": "LLM00230", "doc_id": "NCT01051414_exc", "case_bucket": "or", "source_criterion": "Subjects with evidence of liver cirrhosis Evidence of HCC Co-infection with hepatitis B virus, HIV", "candidate_expression": "((Evidence) AND (HCC) AND (HIV) AND (evidence) AND (hepatitis B virus) AND (liver cirrhosis))"}
{"candidate_id": "LLM00231", "doc_id": "NCT00943865_inc", "case_bucket": "or", "source_criterion": "men and women 30-55 years with BMI 30-40 and waist 95 cm or more normal OGTT normal treadmill stress test plus 2 of 4: 1. low serum levels of HDL cholesterol (<40 mg⁄dL for men or < 50 mg ⁄dL for women); 2. hypertriglyceridemia (triglyceride levels of 150 mg⁄dL or greater); 3. impaired glucose homeostasis (fasting plasma glucose concentration of 110 mg⁄dL or greater or glucose of 140 mg⁄dL or greater after OGTT or 4. hypertension (systolic blood pressure ≥ 140 or diastolic blood pressure ≥90 mmHg or treatment with antihypertensive drugs).", "candidate_expression": "((30-55 years 30-55 years) AND (BMI 30-40) AND (OGTT after OGTT OGTT) AND (OGTT normal) AND (antihypertensive drugs) AND (hypertension) AND (hypertriglyceridemia) AND (impaired glucose homeostasis) AND (men <40 mg⁄dL) AND (serum levels of HDL cholesterol low) AND (treadmill stress test normal 2 of 4) AND (triglyceride levels 150 mg⁄dL or greater) AND (waist 95 cm or more) AND (women < 50 mg ⁄dL) AND ((men) OR (women)) AND ((fasting plasma glucose concentration 110 mg⁄dL or greater) OR (glucose 140 mg⁄dL or greater after OGTT)) AND ((diastolic blood pressure ≥90 mmHg) OR (systolic blood pressure ≥ 140) OR (treatment)))"}
{"candidate_id": "LLM00232", "doc_id": "NCT03077204_exc", "case_bucket": "other", "source_criterion": "NA", "candidate_expression": "(EMPTY)"}
{"candidate_id": "LLM00233", "doc_id": "NCT02332291_inc", "case_bucket": "or", "source_criterion": "Age 60 years or older. Current diagnosis of major depressive disorder (DSM-IV-TR), single episode, recurrent or chronic, without psychotic features, as detected by MINI and clinical exam. Minimum MADRS score = 15. Mini-Mental State Exam = 24. Fluent in English.", "candidate_expression": "((60 years or older) AND (= 24) AND (Age) AND (DSM-IV-TR) AND (MADRS score) AND (MINI) AND (Mini-Mental State Exam) AND (Minimum = 15) AND (chronic) AND (clinical exam) AND (major depressive disorder) AND (psychotic features) AND (recurrent) AND (single episode) AND (without))"}
{"candidate_id": "LLM00234", "doc_id": "NCT02940912_exc", "case_bucket": "or", "source_criterion": "Atypical Parkinsonian Syndromes Parkinson's disease with hallucinations Parkinson's disease with impulse Control disorder (ICD) Parkinson's disease already treated with APOMORPHINE pump or justifying the use of the pump continuously day and night Another obvious severe disease explaining insomnia Exclusion for monitoring difficulties (mutation, insufficient motivation, priority associated pathology in care) Patient unwilling to accept a pump Patient not accepting polysomnography and multiple sleep latency test Patient with health problems or a skin disease precluding continuous subcutaneous infusion Female parturient or nursing Cardiac dysrhythmia precluding treatment with domperidone or apomorphine (increased QTc = 440 ms in men, QTc = 450 ms in women) antiemetic neuroleptics Tetrabenazine Excessive alcohol consumption Hypersensitivity to apomorphine or one of the excipients Respiratory Depression Hepatic impairment Intellectual Disability Dementia", "candidate_expression": "((APOMORPHINE) AND (Cardiac dysrhythmia) AND (Dementia) AND (Excessive alcohol consumption) AND (Female) AND (Hepatic impairment) AND (Hypersensitivity) AND (Intellectual Disability) AND (Parkinson's disease) AND (Parkinsonian Syndromes Atypical) AND (QTc = 440 ms) AND (QTc = 450 ms) AND (Respiratory Depression) AND (Tetrabenazine) AND (antiemetic neuroleptics) AND (apomorphine) AND (domperidone) AND (excipients) AND (hallucinations) AND (health problems) AND (impulse Control disorder (ICD)) AND (insomnia) AND (men) AND (multiple sleep latency test not accepting) AND (not) AND (nursing) AND (parturient) AND (polysomnography not accepting) AND (pump unwilling to accept) AND (severe disease) AND (skin disease) AND (unwilling) AND (women) AND NOT (continuous subcutaneous infusion))"}
{"candidate_id": "LLM00235", "doc_id": "NCT03481894_inc", "case_bucket": "or", "source_criterion": "Male or female patients 2 to 16 years of age Patients who require at least 80% of their caloric intake as PN at study start, and in whom an indication for PN is expected for at least 5 days Patients who require a central venous line to receive PN or already have a central venous line in place for other reasons Written informed consent from legal representative(s)", "candidate_expression": "((PN) AND (PN at least 80% of caloric intake at study start) AND (Written informed consent from legal representative(s)) AND (age 2 to 16 years) AND (indication for at least 5 days) AND ((Male) OR (female)) AND ((central venous line) OR (central venous line other reasons)))"}
{"candidate_id": "LLM00236", "doc_id": "NCT01518946_inc", "case_bucket": "or", "source_criterion": "1. Male and female subjects must be 18 years of age or older and ambulatory. 2. Females of child-bearing potential (FOCP) must have a negative serum beta human chorionic gonadotropin (HCG) pregnancy test. 3. A documented history of severe Symptomatic Orthostatic Hypotension (SOH) that, in the judgment of the treating physician, has required treatment with midodrine HCl , and has been at a stable dose for at least 3 months. 4. The subject has manifested at least 1 of the following symptoms while standing or had a medical history of 1 of the following when not treated for orthostatic hypotension (OH): dizziness, lightheadedness, feeling faint, or feeling like they might black out.", "candidate_expression": "((1) AND (18 years or older) AND (Females) AND (Symptomatic Orthostatic Hypotension (SOH)) AND (age) AND (ambulatory) AND (at least 1) AND (child-bearing potential) AND (dizziness) AND (feeling faint) AND (feeling like they might black out) AND (for at least 3 months) AND (lightheadedness) AND (midodrine HCl) AND (negative) AND (not) AND (orthostatic hypotension (OH)) AND (serum beta human chorionic gonadotropin (HCG) pregnancy test) AND (severe) AND (stable dose) AND (treated) AND ((Male) OR (female)))"}
{"candidate_id": "LLM00237", "doc_id": "NCT01793831_exc", "case_bucket": "or", "source_criterion": "Diagnosis as CD first time or first year. No history of using 5-ASA, biological or immunomodulatory therapy", "candidate_expression": "((5-ASA) AND (CD) AND (No) AND (first time) AND (first year) AND (history) AND (immunomodulatory therapy) AND (therapy biological))"}
{"candidate_id": "LLM00238", "doc_id": "NCT02101554_inc", "case_bucket": "or", "source_criterion": "Children 7-17 with moderate to severe pain requiring around the clock treatment with an opioid analgesic. Be an experienced opioid user, defined as any subject treated with opioid therapy, equivalent or equal to >20 mg per day of morphine, for a period of 3 consecutive days immediately prior to first day of dosing.", "candidate_expression": "((3 consecutive days immediately prior to first day of dosing) AND (>20 mg per day) AND (Children) AND (around the clock treatment) AND (equivalent) AND (first day of dosing) AND (morphine) AND (opioid analgesic) AND (opioid therapy) AND (pain) AND ((moderate) OR (severe)))"}
{"candidate_id": "LLM00239", "doc_id": "NCT03033745_exc", "case_bucket": "other", "source_criterion": "Ongoing serious bacterial infections at the time of screening. Other significant medical conditions that could increase the risk to the subject. Females who are pregnant, breast feeding, or planning a pregnancy during the course study. Participation in a study with an Investigational Medicinal Product (IMP) other than IgPro20 within three months prior to enrollment.", "candidate_expression": "((Females who are pregnant, breast feeding, or planning a pregnancy during the course study.) AND (bacterial infections serious at the time of screening))"}
{"candidate_id": "LLM00240", "doc_id": "NCT02742233_exc", "case_bucket": "or", "source_criterion": "Uncontrolled diabetes Ulcer infection Non-diabetic ulcers Orthopedic or neuromuscular pathologic conditions", "candidate_expression": "((Non-diabetic) AND (Ulcer infection) AND (Uncontrolled) AND (diabetes) AND (ulcers) AND ((Orthopedic pathologic conditions) OR (neuromuscular pathologic conditions)))"}
{"candidate_id": "LLM00241", "doc_id": "NCT02680054_inc", "case_bucket": "other", "source_criterion": "Diagnosis of Type 1 diabetes (for at least a year) On multiple daily insulin injections, including basal long-acting insulin and rapid-acting insulin before each meal. HbA1c < 75 mmol/mol (9.0%) Participant and/or parent/legal guardian willing and able to give informed consent for participation in the study. Family have a freezer in which to safely store the test meals. In the Investigator's opinion, is able and willing to comply with all trial requirements.", "candidate_expression": "((9.0%) AND (< 75 mmol/mol) AND (HbA1c) AND (In the Investigator's opinion, is able and willing to comply with all trial requirements) AND (Participant and/or parent/legal guardian willing and able to give informed consent for participation in the study) AND (Type 1 diabetes) AND (at least a year) AND (basal long-acting) AND (daily) AND (insulin) AND (rapid-acting))"}
{"candidate_id": "LLM00242", "doc_id": "NCT01631058_inc", "case_bucket": "or", "source_criterion": "All renal (only) male and female recipients aged = 60, years undergoing kidney transplantation from a living or deceased donor, including Expanded Criteria Donors (ECD). Panel Reactive Antibody (PRA) < 30%. Patients who consented to participate in the study by signing the informed consent form before the transplant surgery to the 1st post-operative day).", "candidate_expression": "((Panel Reactive Antibody (PRA) < 30%) AND (Patients who consented to participate in the study by signing the informed consent form before the transplant surgery to the 1st post-operative day)) AND (aged = 60) AND (kidney transplantation Expanded Criteria Donors (ECD)) AND (recipients renal) AND ((female) OR (male)) AND ((deceased donor) OR (living donor)))"}
{"candidate_id": "LLM00243", "doc_id": "NCT01614041_exc", "case_bucket": "or", "source_criterion": "Serious suicidal tendency The score of the sixth item of HAMA =3 The score of HAMD =21 Pregnant or lactating women History of allergic or hypersensitivity to tandospirone Serious or unstable cardiac, renal, neurologic, cerebrovascular, metabolic, or pulmonary disease Secondary anxiety disorders Drug or alcohol dependence within 1 year Patients currently taking benzodiazepine drugs Drivers and dangerous machine operators Participated in other clinical studies in the last 30 days Patients with clinically significant ECG or laboratory abnormalities Patients with a history of epilepsy Patients with abnormal TSH concentration", "candidate_expression": "((ECG) AND (ECG abnormalities) AND (Participated in other clinical studies the last 30 days) AND (Secondary anxiety disorders) AND (TSH abnormal) AND (benzodiazepine drugs currently) AND (epilepsy) AND (laboratory) AND (laboratory abnormalities) AND (score of HAMD =21) AND (score of the sixth item of HAMA =3) AND (suicidal tendency) AND (tandospirone Serious unstable) AND (women) AND ((allergic) OR (hypersensitivity)) AND ((cardiac disease) OR (cerebrovascular disease) OR (metabolic disease) OR (neurologic disease) OR (pulmonary disease) OR (renal disease)) AND ((Drug dependence) OR (alcohol dependence)) AND ((Drivers) OR (dangerous machine operators)) AND ((Pregnant) OR (lactating)))"}
{"candidate_id": "LLM00244", "doc_id": "NCT02946892_exc", "case_bucket": "or", "source_criterion": "The use of beta blockers within 2 months of randomization Patients actively listed for transplantation at time of entry into the study or anticipated to undergo heart transplantation, interventional catheterization, or corrective cardiac surgery during the 7 months following entry into the study Sustained or symptomatic ventricular dysrhythmias uncontrolled by drug therapy or the use of an implantable defibrillator, and/or significant cardiac conduction defects, e.g., 2nd degree or 3rd degree AV block, or sick sinus syndrome, unless a functioning pacemaker is in place Uncorrected obstructive or severe regurgitant valve disease, nondilated cardiomyopathy, or significant systemic ventricular outflow obstruction Known renovascular hypertension or evidence of pulmonary hypertension (pulmonary vascular resistance > 6 Wood units) unresponsive to vasodilator agents such as oxygen, nitroprusside, or nitric oxide History or current clinical evidence of moderate-to-severe fixed obstructive pulmonary disease or severe reactive airway diseases (e.g., asthma) requiring hospitalization within the past 2 years or patient currently using long-term inhaled bronchodilators Renal, hepatic, gastrointestinal, or biliary disorder that could impair absorption, metabolism or excretion of orally administered medication Concurrent terminal illness or other severe disease (e.g., active neoplasm) or other significant laboratory value(s) which, in the opinion of the investigator, could preclude participation or survival Endocrine disorders such as primary aldosteronism, pheochromocytoma, hyper- or hypothyroidism, insulin-dependent diabetes mellitus Unwillingness or inability to cooperate, or for the parents or guardians to give consent, or for the child to give assent, or any condition of sufficient severity to impair cooperation in the study Pregnancy or possible pregnancy at time of randomization, or female of child bearing potential who are lactating, or sexually active and not taking adequate contraceptive precautions (e.g., intrauterine device or oral contraceptives for 3 months prior to entry into the study) Use of an investigational drug within 30 days of randomization, or within 5 half-lives of the investigational drug (the longer period will apply) History of drug sensitivity or allergic reaction to alpha-blockers or beta-blockers Use of any of the following medications within two weeks of randomization: MAO inhibitors, Calcium channel blockers, alpha blockers, beta blockers, disopyramide, flecainide, encainide, moricizine, propafenone, sotalol, or beta adrenergic agonists Hospital admission for protein losing enteropathy or plastic bronchitis within 3 months of randomization Active and/or chronic protein losing enteropathy or plastic bronchitis (on inhaled medication to control the plastic bronchitis). Hypoalbuminemia defined as serum albumin <2.0g/dL Renal dysfunction defined as serum creatinine >2.0mg/dL Hepatic dysfunction defined as serum AST and/or ALT> 3 times upper limit of normal (approximately 120 IU/L however, will vary depending on age), Significant anemia or polycythemia defined as hemoglobin >18gm/dL or hemoglobin <7gm/dL Severely elevated serum BNP defined as BNP>300pg/ml", "candidate_expression": "((2nd degree AV block) AND (3rd degree AV block) AND (<2.0g/dL) AND (<7gm/dL) AND (> 3 times upper limit of normal) AND (> 6 Wood units) AND (>18gm/dL) AND (>2.0mg/dL) AND (>300pg/ml) AND (Active) AND (BNP) AND (Calcium channel blockers) AND (Concurrent) AND (Endocrine disorders) AND (Hepatic dysfunction) AND (History) AND (Hospital admission) AND (Hypoalbuminemia) AND (MAO inhibitors) AND (Pregnancy) AND (Renal) AND (Renal dysfunction) AND (Severely elevated) AND (Significant) AND (Sustained) AND (Uncorrected) AND (Unwillingness for the guardians to give consent) AND (Unwillingness for the parents to give consent) AND (Unwillingness to cooperate) AND (active) AND (adequate) AND (allergic reaction) AND (alpha blockers) AND (alpha-blockers) AND (anemia) AND (anticipated to undergo) AND (approximately 120 IU/L) AND (asthma) AND (at time of entry into the study) AND (at time of randomization) AND (beta adrenergic agonists) AND (beta blockers) AND (beta-blockers) AND (biliary) AND (cardiac conduction defects) AND (child bearing potential) AND (chronic) AND (clinical evidence of) AND (contraceptive precautions) AND (corrective cardiac surgery) AND (current) AND (currently) AND (diabetes mellitus) AND (disopyramide) AND (disorder) AND (drug) AND (drug sensitivity) AND (drug therapy) AND (during the 7 months following entry into the study) AND (encainide) AND (entry into the study) AND (evidence of) AND (female) AND (fixed) AND (flecainide) AND (for 3 months prior to entry into the study) AND (functioning) AND (gastrointestinal) AND (heart transplantation) AND (hemoglobin) AND (hepatic) AND (hospitalization) AND (hyper thyroidism) AND (hypothyroidism) AND (impair absorption) AND (impair excretion) AND (impair metabolism) AND (implantable defibrillator) AND (inability for the guardians to give consent) AND (inability for the parents to give consent) AND (inability to cooperate) AND (inhaled medication) AND (insulin-dependent) AND (interventional catheterization) AND (intrauterine device) AND (investigational drug) AND (laboratory) AND (lactating) AND (listed for transplantation) AND (long-term inhaled bronchodilators) AND (moderate-to-severe) AND (moricizine) AND (neoplasm) AND (nitric oxide) AND (nitroprusside) AND (nondilated cardiomyopathy) AND (not) AND (obstructive pulmonary disease) AND (obstructive valve disease) AND (oral contraceptives) AND (orally administered medication) AND (other) AND (oxygen) AND (pacemaker) AND (pheochromocytoma) AND (plastic bronchitis) AND (polycythemia) AND (possible) AND (pregnancy) AND (primary aldosteronism) AND (propafenone) AND (protein losing enteropathy) AND (pulmonary hypertension) AND (pulmonary vascular resistance) AND (randomization) AND (reactive airway diseases) AND (regurgitant valve disease) AND (renovascular hypertension) AND (requiring) AND (serum ALT) AND (serum AST) AND (serum BNP) AND (serum albumin) AND (serum creatinine) AND (severe) AND (severe disease) AND (sexually active) AND (sick sinus syndrome) AND (significant) AND (significant laboratory value(s)) AND (sotalol) AND (symptomatic) AND (systemic ventricular outflow obstruction) AND (terminal illness) AND (the past 2 years) AND (time of randomization) AND (transplantation) AND (uncontrolled by drug therapy) AND (uncontrolled by the use of an implantable defibrillator) AND (unless) AND (unresponsive to vasodilator agents) AND (vasodilator agents) AND (ventricular dysrhythmias) AND (within 2 months of randomization) AND (within 3 months of randomization) AND (within 30 days of randomization) AND (within 5 half-lives of the investigational drug) AND (within the past 2 years) AND (within two weeks of randomization))"}
{"candidate_id": "LLM00245", "doc_id": "NCT03004209_exc", "case_bucket": "or", "source_criterion": "Hemoglobin > 12g/dL Hematochrit >36% Thrombocytosis > 750K AST or ALT > 120 HIV (+) Allergic reaction upon erythropoietin Uncontrolled hypertension mRS before the autoimmune encephalitis > 3 Breast feeding or pregnancy History of ischemic stroke or pulmonary thrombosis Refuse to be enrolled", "candidate_expression": "((ALT) AND (AST) AND (Allergic) AND (Breast feeding) AND (HIV (+)) AND (Hematochrit >36%) AND (Hemoglobin > 12g/dL) AND (Refuse to be enrolled) AND (Thrombocytosis > 750K) AND (Uncontrolled hypertension) AND (autoimmune encephalitis) AND (erythropoietin) AND (ischemic stroke) AND (mRS before the autoimmune encephalitis > 3) AND (pregnancy) AND (pulmonary thrombosis))"}
{"candidate_id": "LLM00246", "doc_id": "NCT01218737_inc", "case_bucket": "or", "source_criterion": "Patient is indicated to have an ocular refractive surgery performed (myopia, astigmatism, hypermetropy) by the Lasik method. Patient presents a normal eye fundus. Patient has intraocular pressure (IOP) ≤ 20 mmHg.", "candidate_expression": "((eye fundus normal) AND (indicated to have an ocular refractive surgery performed) AND (intraocular pressure (IOP) ≤ 20 mmHg) AND (normal eye fundus) AND (ocular refractive surgery Lasik method) AND ((astigmatism) OR (hypermetropy) OR (myopia)))"}
{"candidate_id": "LLM00247", "doc_id": "NCT01932996_exc", "case_bucket": "or", "source_criterion": "Use of smoking cessation medications or interventions in last 30 days Unstable medical illness that requires immediate medical care AUDIT score of < 5 or > 26 Pregnancy or other Nicotine Replacement Therapy (NRT) contraindications Current history or in past 6 months of psychotic disorder or major depressive disorders that is not stable on treatment for past 3 months Cognitive impairment", "candidate_expression": "((AUDIT) AND (Cognitive impairment) AND (NRT) AND (Nicotine Replacement Therapy) AND (Pregnancy) AND (contraindications) AND (for past 3 months) AND (in last 30 days) AND (interventions) AND (major depressive disorders) AND (medications) AND (not stable) AND (past 6 months) AND (psychotic disorder) AND (score of < 5 or > 26) AND (smoking cessation))"}
{"candidate_id": "LLM00248", "doc_id": "NCT03373318_inc", "case_bucket": "other", "source_criterion": "Adult patients (> 18 years) scheduled for cardiopulmonary bypass surgery with Glomerular Filtration Rate (GFR) greater than or equal to 60 and left ventricular ejection fraction greater than or equal to 40%", "candidate_expression": "((> 18 years) AND (Adult) AND (Glomerular Filtration Rate (GFR)) AND (cardiopulmonary bypass surgery) AND (greater than or equal to 40%) AND (greater than or equal to 60) AND (left ventricular ejection fraction) AND (scheduled for) AND (years))"}
{"candidate_id": "LLM00249", "doc_id": "NCT00904202_exc", "case_bucket": "or", "source_criterion": "1. Had a neurological condition other than that associated with their pain diagnosis which, in the opinion of the investigator, would interfere with their ability to participate in the study 2. Were taking a lidocaine-containing product that could not be discontinued while receiving lidocaine 3. Were taking class 1 anti-arrhythmic drugs (e.g., mexiletine, tocainide)", "candidate_expression": "((class 1 anti-arrhythmic drugs) AND (lidocaine while receiving lidocaine receiving lidocaine) AND (lidocaine-containing product could not be discontinued) AND (neurological condition associated with their pain diagnosis) AND (other than associated with their pain diagnosis) AND (pain diagnosis) AND ((mexiletine) OR (tocainide)))"}
{"candidate_id": "LLM00250", "doc_id": "NCT01809041_inc", "case_bucket": "or", "source_criterion": "major elective gastrointestinal, gynecological, prostate or bladder surgery patients who are = 60 years old. the surgery is laparoscopic surgery and is expected to last for = 2 hours under general anesthesia and the patient will stay in hospital for at least 7 days after surgery. lack of serious hearing and vision impairment and be able to read so that neurobehavioral tests can be performed.", "candidate_expression": "((= 2 hour) AND (= 60 years old) AND (able to read) AND (at least 7 days after surgery) AND (can be performed) AND (elective) AND (expected) AND (lack of) AND (laparoscopic surgery) AND (last) AND (neurobehavioral tests) AND (old) AND (stay in hospital) AND (under general anesthesia) AND (will) AND ((hearing impairment) OR (vision impairment)) AND ((bladder surgery) OR (gastrointestinal surgery) OR (gynecological surgery) OR (prostate surgery)))"}
```
