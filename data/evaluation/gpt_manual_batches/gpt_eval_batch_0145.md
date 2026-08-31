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
{"candidate_id": "LLM03601", "doc_id": "NCT01850147_exc", "case_bucket": "or", "source_criterion": "Pre-existing hemoptysis of a severity > grade 3 by NCI CTCAE criteria within 4 weeks prior to study entry Uncontrolled hypertension CHF, angina or arrhythmias LVEF < 1 UNL Existing a second malignancy within 5 years Infected with HIV", "candidate_expression": "((HIV) AND (LVEF < 1 UNL) AND (NCI CTCAE criteria within 4 weeks prior to study entry) AND (hemoptysis severity) AND (hypertension Uncontrolled) AND (second malignancy within 5 years) AND ((CHF) OR (angina) OR (arrhythmias)))"}
{"candidate_id": "LLM03602", "doc_id": "NCT01483118_exc", "case_bucket": "or", "source_criterion": "Current pregnancy or lactation Liver disease or elevated liver enzymes Established diagnosis of diabetes mellitus Abnormal serum glucose levels either at fasting or after the 2-hr oral glucose tolerance test meeting criteria for the diagnosis of diabetes mellitus according to the American Diabetes Association. Insulin sensitizing treatment within 3 months prior to or during the eight week study period. Hormonal treatment involving estrogen or progesterone 3 months prior to or during the study period, with the exception of medroxyprogesterone acetate for withdrawal bleeding. Systemic or inhaled corticosteroids. Known hypersensitive reaction to cinnamon. Patients with seizure disorders, known cardiovascular disease, or cerebrovascular disease. Body mass index (BMI)range 20-50 (excluding all women with BMI under 20 or over 50).", "candidate_expression": "((2-hr oral glucose tolerance test) AND (Abnormal serum glucose levels meeting criteria for the diagnosis of diabetes mellitus according to the American Diabetes Association at fasting fasting after the 2-hr oral glucose tolerance test the 2-hr oral glucose tolerance test) AND (Body mass index (BMI) range 20-50) AND (Insulin sensitizing treatment within 3 months prior to eight week study period during the eight week study period) AND (Liver disease) AND (Systemic corticosteroids Systemic) AND (cardiovascular disease) AND (cerebrovascular disease) AND (cinnamon) AND (criteria for the diagnosis of diabetes mellitus according to the American Diabetes Association meeting) AND (diabetes mellitus) AND (elevated liver enzymes) AND (estrogen) AND (hypersensitive reaction to cinnamon) AND (inhaled corticosteroids inhaled) AND (lactation) AND (liver enzymes elevated) AND (pregnancy) AND (progesterone 3 months prior to the study period during the study period) AND (seizure disorders) AND (serum glucose levels Abnormal) AND (withdrawal bleeding) AND NOT (medroxyprogesterone acetate))"}
{"candidate_id": "LLM03603", "doc_id": "NCT01664507_inc", "case_bucket": "other", "source_criterion": "croup children between 6 month and 5 years old Westley croup score between 3 and 11", "candidate_expression": "((Westley croup score between 3 and 11) AND (children) AND (old between 6 month and 5 years))"}
{"candidate_id": "LLM03604", "doc_id": "NCT02984228_exc", "case_bucket": "or", "source_criterion": "Non-English speaking/illiterate Painful active, concurrent cervical spine conditions Current non-steroidal anti-inflammatory drug (NSAID) use History of taking coumadin or similar anticoagulant, have a known coagulopathy, bleeding dyscrasia, or platelet count < 150,000/cubic mm Allergic reaction to poultry or previous viscosupplementation Involved in workers' compensation or active litigation involving affected shoulder Inability to refrain from NSAID use for 5 days prior to and 6 weeks after injection History of corticosteroid injection to affected shoulder within the last 3 months History of viscosupplementation or platelet-rich plasma to affected shoulder within the last 6 months Presence of acute fracture History of shoulder tumor Known uncontrolled systemic illness (uncontrolled diabetes, human immunodeficiency virus, vasculitis, autoimmune/inflammatory disease) Psychiatric and somatoform disorders", "candidate_expression": "((Allergic reaction) AND (NSAID) AND (NSAID Inability to refrain from 5 days prior to and 6 weeks after injection) AND (Non-English speaking/illiterate) AND (Painful) AND (Psychiatric disorders) AND (anticoagulant) AND (autoimmune) AND (bleeding dyscrasia) AND (cervical spine conditions) AND (coagulopathy) AND (corticosteroid injection History of shoulder last 3 months) AND (coumadin) AND (diabetes uncontrolled) AND (fracture acute) AND (human immunodeficiency virus) AND (inflammatory disease) AND (non-steroidal anti-inflammatory drug) AND (platelet count < 150,000/cubic mm) AND (platelet-rich plasma) AND (poultry) AND (shoulder tumor History of) AND (somatoform disorders) AND (systemic illness uncontrolled) AND (vasculitis) AND (viscosupplementation))"}
{"candidate_id": "LLM03605", "doc_id": "NCT02137369_exc", "case_bucket": "or", "source_criterion": "Lifetime history of Bipolar Disorder, Dementia, Autism Spectrum Disorder, Schizophrenia, or any other Psychotic Disorder. Psychotic symptoms occurring at any time during the current major depressive episode. Current (past 12 months) diagnosis of Panic disorder, Obsessive Compulsive Disorder, Posttraumatic Stress Disorder, Anorexia Nervosa, or Bulimia Nervosa. Alcohol or Drug Dependence within 12 months or Abuse within 3 months (excluding nicotine and caffeine) of baseline visit, as assessed by history and urine drug screen. Clinical evidence of a severe Personality Disorder, as assessed by the study psychiatrist, which would impede participation or completion of the trial. Known neurological disorders or documented serious head injury. Serious and unstable medical illnesses including cardiovascular disease and cancer. Active medical conditions with known mood changes (endocrine, autoimmune disorders). Current diabetes mellitus. For women, pregnancy, lactation, or unwillingness to comply with birth control requirements. Use of any of the following treatments or any other alternative therapy within 2 weeks of the pre-treatment PET scan that may have beneficial effects on mood, including St John's Wort, S-adenosyl methionine (SAMe), n-3 fatty acids, or light therapy. Use of antidepressant medication within 1 month of the pre-treatment PET scan (within 5 weeks for fluoxetine and protryptyline). Failure to achieve a much improved status (i.e. equivalent to >50% symptom reduction) with any lifetime treatment course of CBT (defined as a minimum of 4 sessions of a specified manual-driven therapy by a CBT-trained therapist) or escitalopram (defined as a minimum of 6 weeks of at least 10 mg/day). Clinically significant active suicidal ideation or self-injurious behavior necessitating immediate treatment, as determined by the investigator. Received electroconvulsive therapy in the past 6 months or during the current depressive episode. Currently responding to medication treatment, without clinical reasons to change. Current treatment with weekly individual or group psychotherapy of any type targeted at depressive symptoms. QTc >500 milliseconds on EKG at screening. Contraindications for MRI, including, but not limited to pacemaker, aneurysm clips, neurostimulators, cochlear implants, metal in eyes, steel worker, intra-uterine devices for birth control. Maintenance or prophylactic therapy for stable medical conditions. Hypnotic medication prescribed or approved by the study physician, (up to a three doses per week) for insomnia, as long if not the night before a PET/MRI or clinic ratings visit. Antipsychotic medications, whether prescribed for sleep or other indications, are prohibited.", "candidate_expression": "((Antipsychotic medications) AND (Contraindications) AND (EKG at screening) AND (For women, pregnancy, lactation, or unwillingness to comply with birth control requirements) AND (MRI) AND (PET scan pre-treatment) AND (Personality Disorder severe) AND (Psychotic symptoms at any time during the current major depressive episode) AND (QTc >500 milliseconds) AND (SAMe) AND (antidepressant medication within 1 month of the pre-treatment PET scan within 5 weeks for fluoxetine and protryptyline) AND (depressive episode current the current depressive episode) AND (depressive symptoms) AND (diabetes mellitus) AND (electroconvulsive therapy) AND (fluoxetine) AND (insomnia) AND (major depressive episode current) AND (medical illnesses Serious unstable) AND (mood) AND (protryptyline) AND (psychotherapy weekly) AND (treatment immediate) AND (urine drug screen) AND NOT (Hypnotic medication the night before a PET/MRI or clinic ratings visit.) AND ((during the current depressive episode) OR (in the past 6 months)) AND ((Anorexia Nervosa) OR (Bulimia Nervosa) OR (Obsessive Compulsive Disorder) OR (Panic disorder) OR (Posttraumatic Stress Disorder)) AND ((Alcohol Dependence within 12 months) OR (Drug Dependence within 12 months)) AND ((Alcohol Abuse within 3 months) OR (Drug Abuse within 3 months)) AND ((caffeine) OR (nicotine)) AND ((head injury serious) OR (neurological disorders)) AND ((Autism Spectrum Disorder) OR (Bipolar Disorder) OR (Dementia) OR (Psychotic Disorder) OR (Schizophrenia)) AND ((cancer) OR (cardiovascular disease)) AND ((autoimmune disorders) OR (endocrine disorders)) AND ((alternative therapy) OR (treatments)) AND ((S-adenosyl methionine) OR (St John's Wort) OR (light therapy) OR (n-3 fatty acids)) AND ((self-injurious behavior) OR (suicidal ideation active)) AND ((group) OR (individual)) AND ((aneurysm clips) OR (cochlear implants) OR (intra-uterine devices) OR (metal eyes) OR (neurostimulators) OR (pacemaker) OR (steel worker)) AND ((PET/MRI) OR (clinic ratings visit.)))"}
{"candidate_id": "LLM03606", "doc_id": "NCT02637453_inc", "case_bucket": "other", "source_criterion": "No response to more than one antiarrhythmic drug, or unwilling to receive long-term drug treatment. Can provide informed consent form expressing willingness to participate in the study and comply with follow-up tests and evaluation procedures. Aged 18-80 years.", "candidate_expression": "((18-80 years) AND (Aged) AND (Can provide informed consent form expressing willingness to participate in the study and comply with follow-up tests and evaluation procedures.) AND (No) AND (antiarrhythmic drug) AND (more than one) AND (response))"}
{"candidate_id": "LLM03607", "doc_id": "NCT00943865_exc", "case_bucket": "or", "source_criterion": "diabetes ischemic heart disease or any abnormality on treadmill stress test inflammatory or chronic disorder pregnancy lactation creatinine level of 1,5 mg/dL or more gastrointestinal problems or musculoskeletal disorders that would prevent them to follow the test diets or exercise interventions liver dysfunction with a factor of at least 3 above the upper limit of normal in AST and ALT levels thyroid dysfunction, with serum TSH out of normal limits use of immunosuppressive drugs, corticosteroids or anorexigen", "candidate_expression": "((ALT levels) AND (AST levels) AND (creatinine level 1,5 mg/dL or more) AND (diabetes) AND (lactation) AND (liver dysfunction) AND (pregnancy) AND (prevent) AND (serum TSH out of normal limits) AND (thyroid dysfunction) AND ((gastrointestinal problems) OR (musculoskeletal disorders)) AND ((exercise interventions) OR (test diets)) AND ((ischemic heart disease) OR (treadmill stress test abnormality)) AND ((anorexigen) OR (corticosteroids) OR (immunosuppressive drugs)) AND ((chronic disorder) OR (disorder inflammatory)))"}
{"candidate_id": "LLM03608", "doc_id": "NCT02560389_exc", "case_bucket": "or", "source_criterion": "Claustrophobia, or the inability to lie still in a confined space Major medical disorders (e.g., HIV, cancer) Magnetic metallic implants (such as screws, pins, shrapnel remnants, aneurysm clips, artificial heart valves, inner ear (cochlear) implants, artificial joints, and vascular stents) Electronic or magnetic implants, such as pacemakers Permanent makeup or tattoos with metallic dyes Currently pregnant A self-reported history of loss of consciousness (greater than 10 minutes) Physical disabilities that prohibit task performance (such as blindness or deafness) Psychotic disorders (e.g., schizophrenia) Any other condition that the investigator believes might put the participant at risk", "candidate_expression": "((Any other condition that the investigator believes might put the participant at risk) AND (Claustrophobia) AND (Magnetic metallic implants) AND (Physical disabilities that prohibit task performance) AND (Psychotic disorders) AND (cochlear implants) AND (history of loss of consciousness self-reported greater than 10 minutes) AND (inability to lie still in a confined space) AND (medical disorders Major) AND (metallic dyes) AND (pacemakers) AND (pregnant) AND (schizophrenia) AND ((aneurysm clips) OR (artificial heart valves) OR (artificial joints) OR (inner ear implants) OR (pins) OR (screws) OR (shrapnel remnants) OR (vascular stents)) AND ((Electronic implants) OR (magnetic implants)) AND ((Permanent makeup) OR (tattoos)) AND ((blindness) OR (deafness)) AND ((HIV) OR (cancer)))"}
{"candidate_id": "LLM03609", "doc_id": "NCT00500500_inc", "case_bucket": "other", "source_criterion": "female or male of 50 to 85 years old with a care giver Mini Mental Status (MMS) test between 16 to 26 inclusive Clinical Dementia Rating (CDR) test inferior or equal to 1 National Institute of Neurological and Communicative Disorders and Stroke / Alzheimer's Disease and Related Disorders Association (NINCDS/ADRDA) test positive for an Alzheimer's disease Diagnostic and Statistical Manual of Mental Disorders, 4th Edition (DSM IV) test positive for dementia", "candidate_expression": "((Clinical Dementia Rating (CDR) test inferior or equal to 1) AND (Diagnostic and Statistical Manual of Mental Disorders, 4th Edition (DSM IV) test positive) AND (Mini Mental Status (MMS) tes between 16 to 26 inclusive) AND (National Institute of Neurological and Communicative Disorders and Stroke / Alzheimer's Disease and Related Disorders Association (NINCDS/ADRDA) test positive) AND (old 50 to 85 years))"}
{"candidate_id": "LLM03610", "doc_id": "NCT03119766_inc", "case_bucket": "or", "source_criterion": "Men and women aged 18-45 years. Diagnosis of functional dyspepsia, based on the Rome IV criteria (2016). GIS score of at least 6. Negative H. pylori test . Availability of a signed patient information sheet (Informed Consent form) for participation in the clinical trial. Patients who agree to use an effective method of contraception throughout the clinical trial.", "candidate_expression": "((18-45 years) AND (Availability of a signed patient information sheet (Informed Consent form) for participation in the clinical trial) AND (GIS score) AND (H. pylori test) AND (Negative) AND (Patients who agree to use an effective method of contraception throughout the clinical trial.) AND (Rome IV criteria (2016)) AND (aged) AND (at least 6) AND (functional dyspepsia) AND ((Men) OR (women)))"}
{"candidate_id": "LLM03611", "doc_id": "NCT02332291_inc", "case_bucket": "or", "source_criterion": "Age 60 years or older. Current diagnosis of major depressive disorder (DSM-IV-TR), single episode, recurrent or chronic, without psychotic features, as detected by MINI and clinical exam. Minimum MADRS score = 15. Mini-Mental State Exam = 24. Fluent in English.", "candidate_expression": "((60 years or older) AND (= 24) AND (Age) AND (DSM-IV-TR) AND (MADRS score) AND (MINI) AND (Mini-Mental State Exam) AND (Minimum = 15) AND (clinical exam) AND (major depressive disorder) AND (psychotic features) AND (without) AND ((chronic) OR (recurrent) OR (single episode)))"}
{"candidate_id": "LLM03612", "doc_id": "NCT03103204_exc", "case_bucket": "or", "source_criterion": "Systemic diseases (diabetes, renal diseases, rheumatic diseases, osteoporosis and cardiovascular diseases) Pregnant and lactating women HIV/ AIDS periodontal treatment in the last year (before baseline appointment) Medication: Immunosuppressive drugs, antibiotics in the past three months (before baseline appointment) ) orthodontic appliance", "candidate_expression": "((AIDS) AND (HIV) AND (Systemic diseases) AND (baseline appointment) AND (before baseline appointment) AND (in the last year) AND (in the past three months) AND (orthodontic appliance) AND (periodontal treatment) AND (women) AND ((Immunosuppressive drugs) OR (antibiotics)) AND ((Pregnant) OR (lactating)))"}
{"candidate_id": "LLM03613", "doc_id": "NCT00806936_exc", "case_bucket": "or", "source_criterion": "Known or suspected allergy to trial product(s) or related products Subjects who are unlikely to comply with protocol requirements, e.g. uncooperative attitude, inability to return for the final visit Subjects who previously enrolled in this study Females of childbearing potential who are pregnant, breast-feeding or intend to become pregnant or are not using adequate contraceptive methods The receipt of any investigational product within 3 months prior to this trial", "candidate_expression": "((Females) AND (Females of childbearing potential who are pregnant, breast-feeding or intend to become pregnant or are not using adequate contraceptive methods) AND (Subjects who are unlikely to comply with protocol requirements, e.g. uncooperative attitude, inability to return for the final visit) AND (Subjects who previously enrolled in this study) AND (adequate) AND (investigational product) AND (not) AND (related products) AND (this trial) AND (trial product(s)) AND (within 3 months prior to this trial) AND ((breast-feeding) OR (childbearing potential) OR (contraceptive methods) OR (intend to become) OR (pregnant)) AND ((allergy related products) OR (allergy to trial product(s))))"}
{"candidate_id": "LLM03614", "doc_id": "NCT02944604_inc", "case_bucket": "or", "source_criterion": "Severe or uncontrolled infection. Sensitive to the product or other genetically engineered biological products from Escherichia coli strains. Mental or nervous system disorders. Severe heart, lung and central nervous system disorders. Pregnant or lactating women. TBIL(total bilirubin ), ALT(alanine aminotransferase),AST(glutamic-oxalacetic transaminase) > 2.5×ULN(upper limit of normal); if it were caused by liver metastases, TBIL, ALT,AST >5×ULN. Cr(creatinine) >1.5×ULN.", "candidate_expression": "((ALT > 2.5×ULN) AND (ALT >5×ULN) AND (AST > 2.5×ULN) AND (AST >5×ULN) AND (Cr >1.5×ULN) AND (Mental disorders) AND (Pregnant) AND (Sensitive) AND (TBIL > 2.5×ULN) AND (TBIL >5×ULN) AND (alanine aminotransferase) AND (creatinine) AND (entral nervous system disorders) AND (genetically engineered biological products Escherichia coli strains) AND (glutamic-oxalacetic transaminase) AND (heart disorders) AND (infection Severe uncontrolled) AND (lactating) AND (liver metastases) AND (lung disorders) AND (nervous system disorders) AND (the product other) AND (total bilirubin) AND (women))"}
{"candidate_id": "LLM03615", "doc_id": "NCT03360981_exc", "case_bucket": "or", "source_criterion": "acute myocardial infarction, heart failure, neoplastic disease, chronic diseases that may affect the inflammatory profile both systemic and epicardial (cancer, chronic intestinal inflammation, hepatitis, AIDS); life expectancy < 6 months, previous CABG and/or other open heart surgery intervention, acute coronary syndrome", "candidate_expression": "((< 6 months) AND (AIDS) AND (CABG) AND (acute coronary syndrome) AND (acute myocardial infarction) AND (cancer) AND (chronic diseases) AND (chronic intestinal inflammation) AND (epicardial) AND (heart failure) AND (hepatitis) AND (life expectancy) AND (may affect the inflammatory profile) AND (neoplastic disease) AND (open heart surgery intervention) AND (other) AND (previous) AND (systemic))"}
{"candidate_id": "LLM03616", "doc_id": "NCT02788045_inc", "case_bucket": "scope", "source_criterion": "Are negative for human immunodeficiency virus (HIV) infection at screening Is healthy on the basis of physical examination, medical history, electrocardiogram (ECG), and vital signs measurement performed at screening Are willing/able to adhere to the prohibitions and restrictions specified in the protocol and study procedures Female participants of childbearing potential must have a negative serum pregnancy test (beta human chorionic gonadotropin [beta hCG]) at the Screening visit, and a negative urine pregnancy test pre-dose on Day 1 Are assessed by the clinic staff as being at low risk for HIV infection", "candidate_expression": "((Are willing/able to adhere to the prohibitions and restrictions specified in the protocol and study procedures) AND (Day 1) AND (Female) AND (HIV infection) AND (Screening visit) AND (at screening) AND (at the Screening visit) AND (beta human chorionic gonadotropin [beta hCG]) AND (childbearing potential) AND (electrocardiogram (ECG)) AND (healthy) AND (human immunodeficiency virus (HIV)) AND (low risk) AND (medical history) AND (negative) AND (physical examination) AND (pre-dose on Day 1) AND (serum pregnancy test) AND (urine pregnancy test) AND (vital signs measurement))"}
{"candidate_id": "LLM03617", "doc_id": "NCT00886158_inc", "case_bucket": "other", "source_criterion": "Age from birth to 21 years All solid organ transplant recipients receiving their care at Seattle Children's Hospital Signed consent, and when age appropriate, signed assent", "candidate_expression": "((Age from birth to 21 years) AND (Seattle Children's Hospital) AND (Signed consent, and when age appropriate, signed assent) AND (solid organ transplant))"}
{"candidate_id": "LLM03618", "doc_id": "NCT01313676_exc", "case_bucket": "or", "source_criterion": "Pregnancy: Women who are pregnant or lactating. Asthma: Subjects with a current diagnosis of asthma. (Subjects with a prior history of asthma are eligible if they also have a current diagnosis of COPD). alpha 1-antitrypsin deficiency: Subjects with known alpha-1 antitrypsin deficiency as the underlying cause of COPD. Other respiratory disorders: Subjects with active tuberculosis, lung cancer, bronchiectasis, sarcoidosis, pulmonary fibrosis, pulmonary hypertension, interstitial lung diseases or other active pulmonary diseases. Lung resection or transplantation: Subjects with lung volume reduction surgery within the 12 months prior to Screening or having had a lung transplant. A moderate/severe COPD exacerbation that has not resolved at least 14 days prior to Visit 1 and at least 30 days following the last dose of oral corticosteroids (if applicable). Current severe heart failure (New York Heart Association class IV). Subjects will also be excluded if they have a known ejection fraction of <30% or if they have an implantable cardioverter defibrillator (ICD). Other diseases/abnormalities: Any life-threatening condition with life expectancy <3 years, other than vascular disease or COPD, that might prevent the subject from completing the study. End stage chronic renal disease: Subjects will be excluded if on renal replacement therapy (hemodialysis or peritoneal). Drug/food allergy: Subjects with a history of hypersensitivity to any of the study medications (e.g. beta-agonists, corticosteroid) or components of the inhalation powder (e.g. lactose, magnesium stearate). In addition, patients with a history of severe milk protein allergy that, in the opinion of the study physician, contraindicates the subject's participation will also be excluded. Drug/alcohol abuse: Subjects with a known or suspected history of alcohol or drug abuse within the last 2 years. Oxygen therapy: Subjects receiving treatment with long-term oxygen therapy (LTOT) or nocturnal oxygen therapy required for greater than 12 hours a day. Oxygen prn use (i.e. <=12 hours per day) is not exclusionary. Questionable validity of consent: Subjects with a history of psychiatric disease, intellectual deficiency, poor motivation or other conditions that will limit the validity of informed consent to participate in the study or the potential compliance to study procedures. Affiliation with investigator site: Study investigators, sub-investigators, study coordinators, employees of a participating investigator or immediate family members of the aforementioned are excluded from participating in this study. Additional medication: Use of the following medications within the following time intervals prior to Visit 1 or during the study (unless otherwise specified): Medication No use within the following time intervals prior to Screening or thereafter at any time during the study (unless otherwise specified) Inhaled Long acting beta-agonists (LABA) 48 hours ICS/LABA combination products 48 hours Inhaled corticosteroids 48 hours Tiotropium 1 week Systemic, Oral, parenteral, intra-articular corticosteroids 30 days (oral and systemic corticosteroids may be used to treat COPD exacerbations during the study) Cytochrome P450 3A4 strong inhibitors including but not limited to antiretrovirals (protease inhibitors) (e.g.Indinavir, Nelfinavir, Ritonavir, Saquinavir); Imidazole and Triazole anti-fungals (e.g. Ketaconazole, Itraconazole); Clarithromycin, Telithromycin, Amiodarone, and Nefazodone 6 weeks Grapefruit is allowed up to Visit 1, then limited to no more than one glass of grapefruit juice (250 mL/ 8 ounces) or one grapefruit per day Any other investigational drug 30 days or 5 half lives whichever is longer.", "candidate_expression": "((1 week) AND (Affiliation with investigator site: Study investigators, sub-investigators, study coordinators, employees of a participating investigator or immediate family members of the aforementioned are excluded from participating in this study.) AND (Asthma current) AND (COPD) AND (COPD exacerbation resolved) AND (COPD exacerbations) AND (End stage chronic renal disease) AND (Grapefruit) AND (Imidazole anti-fungals) AND (New York Heart Association class IV) AND (No) AND (Other respiratory disorders) AND (Pregnancy: Women who are pregnant or lactating.) AND (Questionable validity of consent: Subjects with a history of psychiatric disease, intellectual deficiency, poor motivation or other conditions that will limit the validity of informed consent to participate in the study or the potential compliance to study procedures.) AND (Triazole anti-fungals) AND (alpha 1-antitrypsin deficiency) AND (alpha-1 antitrypsin deficiency) AND (asthma current) AND (asthma prior history) AND (heart failure severe) AND (hypersensitivity) AND (in the opinion of the study physician, contraindicates the subject's participation will also be excluded) AND (investigational drug) AND (life-threatening condition life expectancy) AND (lung transplant) AND (lung volume reduction surgery within the 12 months prior to Screening) AND (milk protein allergy history severe) AND (protease inhibitors) AND (renal replacement therapy) AND (that might prevent the subject from completing the study) AND (treat COPD exacerbations during the study) AND ((Oral) OR (Systemic) OR (intra-articular) OR (parenteral)) AND ((oral) OR (systemic)) AND ((Cytochrome P450 3A4 strong inhibitors 6 weeks) OR (ICS/LABA combination products 48 hours) OR (Inhaled Long acting beta-agonists (LABA) 48 hours) OR (Inhaled corticosteroids 48 hours) OR (Tiotropium) OR (corticosteroids) OR (corticosteroids 30 days)) AND ((Itraconazole) OR (Ketaconazole)) AND ((Amiodarone) OR (Clarithromycin) OR (Nefazodone) OR (Telithromycin) OR (antiretrovirals)) AND ((30 days) OR (5 half lives)) AND ((Indinavir) OR (Nelfinavir) OR (Ritonavir) OR (Saquinavir)) AND ((active pulmonary diseases) OR (bronchiectasis) OR (interstitial lung diseases) OR (lung cancer) OR (pulmonary fibrosis) OR (pulmonary hypertension) OR (sarcoidosis) OR (tuberculosis)) AND ((Lung resection) OR (transplantation)) AND ((having had a lung transplant) OR (with lung volume reduction surgery)) AND ((moderate) OR (severe)) AND ((ejection fraction <30%) OR (implantable cardioverter defibrillator (ICD))) AND ((COPD) OR (vascular disease)) AND ((hemodialysis) OR (peritoneal)) AND ((Drug allergy) OR (food allergy)) AND ((beta-agonists) OR (corticosteroid)) AND ((components of the inhalation powder) OR (study medications)) AND ((lactose) OR (magnesium stearate)) AND ((Drug abuse) OR (alcohol abuse)) AND ((alcohol abuse) OR (drug abuse)) AND ((long-term oxygen therapy (LTOT)) OR (nocturnal oxygen therapy)) AND ((Screening) OR (any time during the study)))"}
{"candidate_id": "LLM03619", "doc_id": "NCT03537924_inc", "case_bucket": "or", "source_criterion": "Healthy men and women, age 40-75 yrs, without any disease and need of medication. Born, raised and currently living at low altitude (<800m). Written informed consent. Kyrgyz ethnicity", "candidate_expression": "((Healthy) AND (Kyrgyz ethnicity) AND (Written informed consent.) AND (age 40-75 yrs) AND (living at <800m) AND (living at low altitude) AND ((men) OR (women)) AND ((any disease) OR (medication need of)))"}
{"candidate_id": "LLM03620", "doc_id": "NCT01742117_exc", "case_bucket": "other", "source_criterion": "NA", "candidate_expression": "(EMPTY)"}
{"candidate_id": "LLM03621", "doc_id": "NCT02281643_inc", "case_bucket": "other", "source_criterion": "M. perstans mg-positive status Good general health without any clinical condition requiring long-term medication. Normal renal and hepatic laboratory profiles", "candidate_expression": "((Good general health) AND (M. perstans mg positive) AND (hepatic laboratory profile Normal) AND (long-term medication) AND (renal laboratory profile Normal) AND NOT (clinical condition requiring long-term medication requiring long-term medication))"}
{"candidate_id": "LLM03622", "doc_id": "NCT02607163_inc", "case_bucket": "or", "source_criterion": "the patients undergoing ascending, arch and/or proximal descending aorta surgery with cardiopulmonary bypass 20 - 100 yrs old", "candidate_expression": "((arch aorta surgery) AND (ascending aorta surgery) AND (cardiopulmonary bypass) AND (old 20 - 100 yrs) AND (proximal descending aorta surgery))"}
{"candidate_id": "LLM03623", "doc_id": "NCT01720394_inc", "case_bucket": "or", "source_criterion": "medical indication for induction of labor 18 years of age signed informed consent cephalic presentation no PROM 37+0 - 42+0 weeks of gestation Bishop-Score = 6 no contra-indication for medical induction of labor no clinical signs of infection", "candidate_expression": "((Bishop-Score = 6) AND (age 18 years) AND (cephalic presentation) AND (induction of labor) AND (medical indication) AND (medical induction of labor) AND (signed informed consent) AND (weeks of gestation) AND NOT (contra-indication) AND NOT (infection clinical signs of) AND NOT (PROM 37+0 42+0))"}
{"candidate_id": "LLM03624", "doc_id": "NCT01803438_inc", "case_bucket": "scope", "source_criterion": "Subject has been diagnosed with symptomatic paroxysmal atrial fibrillation as defined above and at least two symptomatic episodes in the last six months prior to inclusion. At least one episode of AF must be documented during the prior year by any kind of ECG recording. Subject has structural normal heart with an LVEF = 50%, thickness of the inter-ventricular septum =12 mm and left atrium diameters (short axis) < 46 mm obtained by transthoracic echocardiography. Subject has normal ECG parameters (QRS width in the 12 channel surface ECG =120 ms, QTc - interval < 440 ms, PQ - interval = 210 ms; all parameters should be measured at sinus rhythm). Subject is at least 18 and not older than 75years old. Subject is able and willing to give informed consent.", "candidate_expression": "((AF) AND (ECG) AND (ECG normal) AND (LVEF = 50%,) AND (PQ - interval = 210 ms) AND (QRS width 12 channel surface ECG =120 ms) AND (QTc - interval < 440 ms) AND (Subject is able and willing to give informed consent) AND (episode At least one prior year) AND (episodes at least two symptomatic last six months prior to inclusion) AND (heart structural normal) AND (left atrium diameters < 46 mm) AND (old at least 18 and not older than 75years) AND (paroxysmal atrial fibrillation symptomatic) AND (short axis) AND (sinus rhythm) AND (thickness of the inter-ventricular septum =12 mm) AND (transthoracic echocardiography))"}
{"candidate_id": "LLM03625", "doc_id": "NCT00728156_exc", "case_bucket": "or", "source_criterion": "Contraindication to Clopidogrel Smoking (current smokers and patients who quit smoking less than six months) Malignancy(diagnosed or under investigation) Haematological disorders (Anaemia, malignancy, bleeding disorders) Women of child-bearing potential Use of corticosteroids/other antithrombotic agents(warfarin) Chronic liver disease (Cirrhosis, malignancy and patients with more than twice the upper limit of liver function tests) Unable to consent. Use of other investigational study drugs within 1 year prior to study entry Previous participation in this study", "candidate_expression": "((Anaemia) AND (Chronic liver disease) AND (Cirrhosis) AND (Clopidogrel) AND (Contraindication) AND (Haematological disorders) AND (Malignancy diagnosed under investigation) AND (Smoking) AND (Unable to consent.) AND (Women) AND (antithrombotic agents) AND (bleeding disorders) AND (child-bearing potential) AND (corticosteroids) AND (investigational study drugs within 1 year prior to study entry) AND (liver function tests more than twice the upper limit) AND (malignancy) AND (participation in this study Previous) AND (quit smoking less than six months) AND (smokers current) AND (warfarin))"}
```
