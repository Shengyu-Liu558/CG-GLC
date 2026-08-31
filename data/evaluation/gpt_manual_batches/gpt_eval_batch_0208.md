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
{"candidate_id": "LLM05176", "doc_id": "NCT02766530_inc", "case_bucket": "other", "source_criterion": "Women aged 25-75 years old. Women with recently diagnosed breast cancer and who will receive NAC to reduce tumor burden before surgery. (including locally advanced breast cancer (LABC) according to clinical assessment; or tumor size > 2cm, that is, at least T2 in TNM staging).", "candidate_expression": "((NAC reduce tumor burden before surgery) AND (Women) AND (aged 25-75 years old) AND (breast cancer))"}
{"candidate_id": "LLM05177", "doc_id": "NCT03623789_inc", "case_bucket": "or", "source_criterion": "Patients with osteoarthritis of the hip secondary to degeneration, inflammatory arthritis, gouty arthritis, acetabular dysplasia or osteonecrosis of the femoral head, and undergoing primary unilateral minimally invasive THA Age > 18 years and < 90 years Failure of medical treatment or rehabilitation. Hemoglobin > 11g/dl, No use of non-steroid anti-inflammatory agent one week before operation", "candidate_expression": "((Age > 18 years < 90 years) AND (Hemoglobin > 11g/dl) AND (degeneration) AND NOT (non-steroid anti-inflammatory agent one week before operation) AND ((medical treatment) OR (rehabilitation)) AND ((gouty arthritis) OR (inflammatory arthritis) OR (minimally invasive THA undergoing primary unilateral) OR (osteoarthritis hip secondary to degeneration)) AND ((acetabular dysplasia) OR (osteonecrosis)))"}
{"candidate_id": "LLM05178", "doc_id": "NCT00401245_inc", "case_bucket": "or", "source_criterion": "Generally healthy, postmenopausal woman who seeks treatment for hot flushes. Meets 1 of the following: At least 12 months of spontaneous amenorrhea; At least 6 months of spontaneous amenorrhea with serum follicle-stimulating hormone (FSH) levels > 40 mIU/mL; At least 6 weeks postsurgical bilateral oophorectomy (with or without hysterectomy). Hysterectomized without bilateral oophorectomy and with serum FSH levels >40 mIU/mL.", "candidate_expression": "((> 40 mIU/mL) AND (>40 mIU/mL) AND (At least 12 months) AND (At least 6 months) AND (At least 6 weeks postsurgical) AND (Hysterectomized) AND (Meets 1 of the following) AND (bilateral oophorectomy) AND (healthy) AND (hot flushes) AND (postmenopausal) AND (serum FSH levels) AND (serum follicle-stimulating hormone (FSH) levels) AND (spontaneous amenorrhea) AND (without) AND (woman) AND ((bilateral oophorectomy with hysterectomy) OR (bilateral oophorectomy without hysterectomy)))"}
{"candidate_id": "LLM05179", "doc_id": "NCT02330757_exc", "case_bucket": "or", "source_criterion": "PCOS or polycystic ovary on ultrasound scan. Moderate or severe endometriosis. Hydrosalpinx. Uterine abnormalities or myoma. Previous uterine surgery.", "candidate_expression": "((Hydrosalpinx) AND (PCOS) AND (Uterine abnormalities) AND (endometriosis) AND (myoma) AND (polycystic ovary) AND (ultrasound scan Moderate severe) AND (uterine surgery Previous))"}
{"candidate_id": "LLM05180", "doc_id": "NCT03369379_exc", "case_bucket": "or", "source_criterion": "Those subjects with previous use of vitamin D. Known subjects with renal, liver, calcium metabolism disorders, malabsorption disorders, known neoplasms. Subjects with serum calcium levels equal to or greater than 10.2 mg / dl.", "candidate_expression": "((equal to or greater than 10.2 mg / dl) AND (previous use) AND (serum calcium levels) AND (vitamin D) AND ((calcium metabolism disorders) OR (disorders liver) OR (disorders renal) OR (malabsorption disorders) OR (neoplasms)))"}
{"candidate_id": "LLM05181", "doc_id": "NCT03149887_inc", "case_bucket": "other", "source_criterion": "Adult patients up to age 75 years, undergoing elective, ambulatory, arthroscopic rotator cuff repair.", "candidate_expression": "((Adult) AND (age) AND (ambulatory) AND (arthroscopic rotator cuff repair) AND (elective) AND (up to 75 years))"}
{"candidate_id": "LLM05182", "doc_id": "NCT03140423_exc", "case_bucket": "other", "source_criterion": "Exclusion criteria includes ICUs with an average length of stay of less than 2 days; HCA hospitals that are not able to transfer or merge data into the centralized data warehouse for the baseline and intervention periods of the study are also excluded.", "candidate_expression": "((ICUs) AND (average length of stay less than 2 days))"}
{"candidate_id": "LLM05183", "doc_id": "NCT02894372_exc", "case_bucket": "other", "source_criterion": "Purulent infection Refusal to participate Allergy to tested material", "candidate_expression": "((Allergy) AND (Purulent infection) AND (Refusal to participate) AND (tested material))"}
{"candidate_id": "LLM05184", "doc_id": "NCT03252249_exc", "case_bucket": "or", "source_criterion": "Clear indication for specific duration of dual anti-platelet therapy Type 2 myocardial infarction Contraindication to aspirin or P2Y12 receptor antagonist Non-resident of Scotland Previous recruitment into the trial Inability or unwilling to give informed consent", "candidate_expression": "((Clear indication for specific duration) AND (Contraindication) AND (Inability or unwilling to give informed consent) AND (Non-resident) AND (Previous recruitment into the trial) AND (Scotland) AND (Type 2 myocardial infarction) AND (dual anti-platelet therapy) AND ((P2Y12 receptor antagonist) OR (aspirin)))"}
{"candidate_id": "LLM05185", "doc_id": "NCT03366779_exc", "case_bucket": "or", "source_criterion": "Spondylolisthesis Grade II or higher. Subject requires uni or bilateral facetectomy to treat leg/back pain. Subject has back or non-radicular leg pain of unknown etiology. Prior surgery at the index lumbar level. Subject requiring a spine DEXA (i.e., patients with SCORE of = 6) with a T Score less than -2.0 at the index level. For patients with a herniation at L5/S1, the average T score of L1-L4 shall be used. Subject has clinically compromised vertebral bodies at the index level(s) due to any traumatic, neoplastic, metabolic, or infectious pathology. Subject has sustained pathologic fractures of the vertebra or multiple fractures of the vertebra or hip. Subject has scoliosis of greater than ten (10) degrees (both angular and rotational). Any metabolic disease bone disease that has not been stabilized for at least three months (e.g., Paget's disease, osteomalacia, osteogenesis imperfecta, thyroid and/or parathyroid gland disorder, etc.). Subject has an active infection either systemic or local. Subject has cauda equina syndrome or neurogenic bowel/bladder dysfunction. Subject has severe arterial insufficiency of the legs (Screening on physical examination= patients with diminution or absence of dorsalis pedis or posterior tibialis pulses. If diminished or absent by palpation, then an arterial ultrasound is required with vascular plethysmography. If the absolute arterial pressure is below 50mm of Hg at the calf or ankle level, then the patient is to be excluded) or other peripheral vascular disease). Subject has significant peripheral neuropathy, patient defined as a patient with Type I or Type II diabetes or similar systemic metabolic condition causing decreased sensation in a stocking-like or non-radicular and non-dermatomal distribution in the lower extremities. Subject has insulin-dependent diabetes mellitus. Subject is morbidly obese (defined as a body mass index >40, or weighs more than 100 lbs over ideal body weight). Subject has been diagnosed with active hepatitis, AIDS, or HIV. Subject has been diagnosed with rheumatoid arthritis or other autoimmune disease. Subject has a known allergy to titanium, polyethylene or polyester materials. Subject is pregnant or interested in becoming pregnant in the next two (2) years. Subject has active tuberculosis or has had tuberculosis in the past three (3) years. Subject has a history of active malignancy: A patient with a history of any invasive malignancy (except non-melanoma skin cancer), unless he/she has been treated with curative intent and there have been no signs or symptoms of the malignancy for at least two (2) years. Subject is immunologically suppressed, received steroids >1 month over the past year. Currently taking anticoagulants, other than aspirin, unless the patient can be taken off the anticoagulant for surgery. Subject has a current chemical/alcohol dependency or significant psychosocial disturbance. Subject has a life expectancy of less than three (3) years. Subject is currently involved in another investigational study. Subject is incarcerated.", "candidate_expression": "((= 6) AND (>1 month) AND (>40) AND (AIDS) AND (Grade) AND (HIV) AND (II or higher) AND (L1-L4) AND (L5/S1) AND (Paget's disease) AND (Prior) AND (SCORE) AND (Screening on physical examination) AND (Spondylolisthesis) AND (Subject is currently involved in another investigational study.) AND (T Score) AND (Type I) AND (Type II) AND (absent) AND (absolute arterial pressure) AND (active) AND (active malignancy) AND (alcohol dependency) AND (allergy) AND (angular) AND (ankle level) AND (anticoagulants) AND (arterial insufficiency) AND (arterial ultrasound) AND (aspirin) AND (autoimmune disease) AND (average T score) AND (back pain) AND (been stabilized) AND (below 50mm of Hg) AND (bilateral) AND (body mass index) AND (bone disease) AND (calf level) AND (cauda equina syndrome) AND (chemical dependency) AND (clinically compromised vertebral bodies) AND (decreased sensation) AND (diabetes) AND (diabetes mellitus) AND (diminished) AND (diminution or absence of dorsalis pedis) AND (diminution or absence of posterior tibialis pulses) AND (except) AND (excluded) AND (facetectomy) AND (for at least three months) AND (for at least two (2) years) AND (fractures of the hip) AND (fractures of the vertebra) AND (greater than ten (10) degrees) AND (hepatitis) AND (herniation) AND (history) AND (immunologically suppressed) AND (in the next two (2) years) AND (in the past three (3) years) AND (incarcerated) AND (index level) AND (index level(s)) AND (index lumbar level) AND (infection) AND (infectious pathology) AND (insulin-dependent) AND (interested in becoming) AND (invasive) AND (legs) AND (less than -2.0) AND (less than three (3) years) AND (life expectancy) AND (local) AND (lower extremities) AND (malignancy) AND (metabolic disease) AND (metabolic pathology) AND (morbidly obese) AND (more than 100 lbs over ideal body weight) AND (multiple) AND (neoplastic pathology) AND (neurogenic bladder dysfunction) AND (neurogenic bowel dysfunction) AND (no) AND (non-dermatomal distribution) AND (non-melanoma skin cancer) AND (non-radicular distribution) AND (non-radicular leg pain) AND (not) AND (osteogenesis imperfecta) AND (osteomalacia) AND (other) AND (other than) AND (over the past year) AND (pain leg) AND (palpation) AND (parathyroid gland disorder) AND (pathologic) AND (peripheral neuropathy) AND (peripheral vascular disease) AND (polyester) AND (polyethylene) AND (pregnant) AND (psychosocial disturbance) AND (requiring) AND (rheumatoid arthritis) AND (rotational) AND (scoliosis) AND (severe) AND (significant) AND (signs or symptoms of the malignancy) AND (similar) AND (spine DEXA) AND (steroids) AND (stocking-like distribution) AND (surgery) AND (systemic) AND (systemic metabolic condition) AND (thyroid) AND (titanium) AND (traumatic pathology) AND (treated with curative intent) AND (tuberculosis) AND (uni) AND (unknown etiology) AND (vascular plethysmography) AND (weighs))"}
{"candidate_id": "LLM05186", "doc_id": "NCT03209687_inc", "case_bucket": "other", "source_criterion": "Females undergoing Intra-Cytoplasmic Sperm Injection (ICSI) cycles Age between 20 and 40 years", "candidate_expression": "((Age) AND (Females) AND (Intra-Cytoplasmic Sperm Injection (ICSI) cycles) AND (between 20 and 40 years) AND (undergoing))"}
{"candidate_id": "LLM05187", "doc_id": "NCT03475589_exc", "case_bucket": "or", "source_criterion": "Confirmed allergy to apatinin and or its excipients; Hypertension (high blood pressure) that can not be controlled by drugs; A history of active hemorragge, ulcer, intestinal perforation, intestinal obstruction, or major surgery no older than 30 days; NYHA III-IV heart function, or severe hepatic or renal insufficiency (Grade 4); Presence of multiple factors that affect oral medications, such as difficulty swallowing, nausea, vomiting, chronic diarrhea and intestinal obstruction; Pregnant or lactating women, or women of child-bearing potential who have planned a pregnancy, or male and female patients who do not agree to practice adequate contraception during this study; Patients who have a history of psychotropics abuse and can not quit, or who have mental disorders; Participation in other drug clinical trial within the last 4 weeks; Prior therapy with VEGFR inhibitors such as sorafenib and sunitinib; Presence of comorbidities that seriously affect the patient's safety or ability to complete the study, in the investigator's judgment; Patients who can not tolerate apatinib treatment as judged by the investigator depending on the their medical history; Patients that are considered ineligible for this study by the investigator.", "candidate_expression": "((Grade 4) AND (Hypertension) AND (III-IV) AND (NYHA) AND (Participation in other drug clinical trial within the last 4 weeks;) AND (Pregnant or lactating women, or women of child-bearing potential who have planned a pregnancy, or male and female patients who do not agree to practice adequate contraception during this study;) AND (VEGFR inhibitors) AND (active) AND (allergy) AND (apatinib) AND (controlled by drugs) AND (drugs) AND (factors that affect oral medications) AND (heart function) AND (hepatic insufficiency) AND (high blood pressure) AND (history) AND (no older than 30 days) AND (not) AND (psychotropics) AND (renal insufficiency) AND (severe) AND (tolerate) AND ((hemorragge) OR (intestinal obstruction) OR (intestinal perforation) OR (major surgery) OR (ulcer)) AND ((apatinin) OR (excipients)) AND ((chronic diarrhea) OR (difficulty swallowing) OR (intestinal obstruction) OR (nausea) OR (vomiting)) AND ((abuse) OR (mental disorders)) AND ((sorafenib) OR (sunitinib)))"}
{"candidate_id": "LLM05188", "doc_id": "NCT02273791_exc", "case_bucket": "or", "source_criterion": "Moderate or severe endometriosis. Hydrosalpinx. Uterine abnormalities or myoma. Previous uterine surgery.", "candidate_expression": "((Hydrosalpinx) AND (Uterine abnormalities) AND (endometriosis Moderate severe) AND (myoma) AND (uterine surgery))"}
{"candidate_id": "LLM05189", "doc_id": "NCT02035904_exc", "case_bucket": "or", "source_criterion": "preexisting pectoral, axillar, thoracic homolateral pain habitual opioid consumption; drug-alcoholics addiction ; ICU postoperative recovery; kidney failure (creatinin > 2 g/dl, creatinin <clearance 30 ml/h) and/or hepatic failure (cholinesterase < 2000 UI); cardiac arrhythmias o; Epilepsy; Psychiatric, cognitive disorders, mental retardation; Coagulopathies (INR > 2, activated partial thromboplastin time - aPTT>44 sec); platelet count less than 100.000/mm3; BMI > 30; Allergies to study drugs.", "candidate_expression": "((30 ml/h) AND (< 2000 UI) AND (> 2) AND (> 2 g/dl) AND (> 30) AND (>44 sec) AND (Allergies) AND (BMI) AND (Coagulopathies) AND (Epilepsy) AND (ICU postoperative recovery) AND (cardiac arrhythmias) AND (cholinesterase) AND (habitual) AND (homolateral) AND (less than 100.000/mm3) AND (opioid consumption) AND (platelet count) AND (study drugs) AND ((creatinin) OR (creatinin <clearance)) AND ((hepatic failure) OR (kidney failure)) AND ((Psychiatric, cognitive disorders) OR (mental retardation)) AND ((INR) OR (activated partial thromboplastin time - aPTT)) AND ((axillar pain) OR (pectoral pain) OR (thoracic pain)) AND ((addiction drug) OR (alcoholics addiction)))"}
{"candidate_id": "LLM05190", "doc_id": "NCT02416765_inc", "case_bucket": "or", "source_criterion": "1. Males and females ≥ 18 years old. 2. Clinical diagnosis of type 1 diabetes for at least one year. 3. The subject will have been on insulin pump therapy for at least 3 months and currently using a fast actin insulin analog (Lispro, Aspart or Guilisine). 4. Last (less than 3 months) HbA1c ≤ 10%. 5. Currently using carbohydrate counting as the meal insulin dose strategy.", "candidate_expression": "((HbA1c Last (less than 3 months) ≤ 10%) AND (carbohydrate counting Currently) AND (fast actin insulin analog currently) AND (insulin pump therapy for at least 3 months) AND (meal insulin dose strategy) AND (old ≥ 18 years old) AND (type 1 diabetes for at least one year) AND ((Aspart) OR (Guilisine) OR (Lispro)) AND ((Males) OR (females)))"}
{"candidate_id": "LLM05191", "doc_id": "NCT00396734_exc", "case_bucket": "or", "source_criterion": "use more than 2g a day; 5 times a week to everyday Subjects who are diagnosed as suffering from psychotic illness according to DSM-IV (Axis 1)22, or with a history of CNS disease, a history of infection that might affect CNS (HIV, syphilis, cytomegalovirus, herpes), or a history of head injury with loss of consciousness,pregnant women.", "candidate_expression": "((CNS disease) AND (DSM-IV Axis 1) AND (head injury) AND (infection affect CNS) AND (loss of consciousness) AND (more than 2g a day 5 times a week to everyday) AND ((HIV) OR (cytomegalovirus) OR (herpes) OR (syphilis)) AND ((history) OR (pregnant) OR (psychotic illness)))"}
{"candidate_id": "LLM05192", "doc_id": "NCT02566226_exc", "case_bucket": "other", "source_criterion": "planned surgical duration more than 3 hours contraindication to spinal anaesthesia severe respiratory disease patient known and treated for sleep apnea syndrome", "candidate_expression": "((contraindication) AND (more than 3 hours) AND (planned surgical duration) AND (respiratory disease) AND (severe) AND (sleep apnea syndrome) AND (spinal anaesthesia) AND (treated))"}
{"candidate_id": "LLM05193", "doc_id": "NCT00894712_exc", "case_bucket": "or", "source_criterion": "Visible skin pathology, excessive freckles, or skin blemishes in the test area. History of skin disease or hypersensitivity and repeated contact allergies. Sarcoma or squamous cell histology. Metastatic disease to the breast. Current tobacco use.", "candidate_expression": "((Current) AND (Metastatic disease) AND (contact allergies) AND (excessive) AND (histology) AND (hypersensitivity) AND (skin disease) AND (to the breast) AND (tobacco use) AND ((freckles) OR (skin blemishes) OR (skin pathology)) AND ((Sarcoma) OR (squamous cell)))"}
{"candidate_id": "LLM05194", "doc_id": "NCT02754583_inc", "case_bucket": "other", "source_criterion": "Community in a school district that is within the study area Area within each school district that is in need of a well", "candidate_expression": "((school district that is in need of a well) AND (school district that is within the study area))"}
{"candidate_id": "LLM05195", "doc_id": "NCT03195153_exc", "case_bucket": "other", "source_criterion": "not diabetic patient; patients in dual antiplatelet therapy; patient with severe renal failure; patient poor responders", "candidate_expression": "((diabetic) AND (dual antiplatelet therapy) AND (not) AND (poor responders) AND (renal failure) AND (severe))"}
{"candidate_id": "LLM05196", "doc_id": "NCT03046108_inc", "case_bucket": "other", "source_criterion": "Clinical suspicion of Morton neuroma confirmed in ultrasound scan Symptoms present more than six months The thickness of the nerve must be at least 2 mm in short axis and at least 5 mm in the longitudinal axis.", "candidate_expression": "((Clinical suspicion) AND (Morton neuroma) AND (Symptoms) AND (at least 2 mm) AND (at least 5 mm) AND (more than six months) AND (thickness of the nerve in short axis) AND (thickness of the nerve in the longitudinal axis) AND (ultrasound scan))"}
{"candidate_id": "LLM05197", "doc_id": "NCT02764476_inc", "case_bucket": "or", "source_criterion": "Adults 18-65 years, who are diagnosed with functional neurologic symptom or conversion disorder. If diagnosis of seizure type then video EEG with diagnosis confirmed by board-certified neurologist with subspecialty training in epilepsy and clinical neurophysiology using the criteria of the International Classification of the Epilepsies is required. If diagnosis of motor type, documented and clinically established levels of diagnostic certainty (Williams,1995) confirmed by 2 neurologists is required. Participants must have at least one symptom per month in the month prior to enrollment Fluency in English spoken language", "candidate_expression": "((18-65 years) AND (Adults) AND (at least one per month) AND (conversion disorder) AND (criteria of the International Classification of the Epilepsies) AND (functional neurologic symptom) AND (in the month prior to enrollment) AND (motor type) AND (seizure type) AND (symptom) AND (to enrollment) AND (video EEG))"}
{"candidate_id": "LLM05198", "doc_id": "NCT01205334_inc", "case_bucket": "or", "source_criterion": "Histopathological verification of glioblastoma multiforme (GBM: WHO grade IV) in remission (Group A) or with active disease (Group B). CMV-positive GBM CMV seropositive Life expectancy 6 weeks or greater Karnofsky/Lansky score 50 or greater Patient or parent/guardian capable of providing informed consent Bilirubin less than 1.5x upper limit of normal, AST less than 3x upper limit of normal, serum creatinine less than 1.5x normal and Hgb 8.0 g/dL or greater Pulse oximetry of 90% or greater on room air Sexually active patients must be willing to utilize one of the more effective birth control methods for 6 months after the CTL infusion. The male partner should use a condom. Patients should have been off other investigational antineoplastic therapy for one month prior to entry in this study. Informed consent explained to, understood by and signed by patient/guardian. Patient/guardian given copy of informed consent.", "candidate_expression": "((6 weeks or greater) AND (90% or greater) AND (AST) AND (Bilirubin) AND (CMV) AND (CMV seropositive) AND (CMV-positive) AND (GBM) AND (Histopathological) AND (Histopathological verification) AND (Informed consent explained to, understood by and signed by patient/guardian. Patient/guardian given copy of informed consent.) AND (Karnofsky/Lansky) AND (Life expectancy) AND (Patient or parent/guardian capable of providing informed consent) AND (Patients should have been off other investigational antineoplastic therapy for one month prior to entry in this study.) AND (Pulse oximetry) AND (Sexually active patients must be willing to utilize one of the more effective birth control methods for 6 months after the CTL infusion. The male partner should use a condom.) AND (WHO) AND (active) AND (antineoplastic therapy) AND (been off) AND (entry in this study) AND (for one month prior to entry in this study) AND (glioblastoma multiforme) AND (grade IV) AND (in remission) AND (less than 1.5x upper limit of normal) AND (less than 3x upper limit of normal) AND (on room air) AND (score 50 or greater) AND (with active disease) AND ((Group A) OR (Group B)))"}
{"candidate_id": "LLM05199", "doc_id": "NCT02944929_inc", "case_bucket": "or", "source_criterion": "Males and females aged between 18 to 75 years. Adult patient under guardianship with consent obtained and the legal guardian's authorisation obtained. Single stroke having occurred more than 6 months before (previous TIA is accepted). Capable of understanding instructions and participating in the definition of a therapeutic goal (Boston Diagnostic Aphasia Examination (BDAE) < 3). Having previously undergone BTI. The last injection must have been performed at least 4 months prior to inclusion. Affiliation to the French social security regime or a similar regime. Patient (or the legal guardian if under guardian adult patient) has signed the informed consent form.", "candidate_expression": "((< 3) AND (Adult patient under guardianship with consent obtained and the legal guardian's authorisation obtained) AND (BDAE) AND (BTI) AND (Boston Diagnostic Aphasia Examination) AND (Capable of understanding instructions and participating in the definition of a therapeutic goal) AND (Males) AND (Patient (or the legal guardian if under guardian adult patient) has signed the informed consent form) AND (Single) AND (TIA) AND (aged) AND (at least 4 months prior to inclusion) AND (between 18 to 75 years) AND (females) AND (inclusion) AND (injection) AND (more than 6 months) AND (stroke))"}
{"candidate_id": "LLM05200", "doc_id": "NCT00343668_inc", "case_bucket": "or", "source_criterion": "Pathologically proven unresectable adenocarcinoma of stomach With uni-dimensionally measurable disease (at least longest diameter 2 cm on conventional CT scan, x-ray or physical examination, or 1cm on spiral CT scan) Age 18 to 70 years old Estimated life expectancy of more than 3 months ECOG performance status of 2 or lower Adequate bone marrow function(absolute neutrophil count [ANC] ≥1,500/µL, hemoglobin ≥9.0 g/dL,and platelets ≥100,000/µL) Adequate kidney function (serum creatinine < 1.5 mg/dL) Adequate liver function (serum total bilirubin < 2 times the upper normal limit (UNL); serum transaminases levels <3 times [<5 times for patients with liver metastasis] UNL) No prior chemotherapy but prior adjuvant chemotherapy finished at least 6 months before enrollment was allowed. (but, prior adjuvant chemotherapy with capecitabine or S-1 or camptothecin analogues was excluded) No prior radiation therapy for at least 4 weeks before enrollment in the study", "candidate_expression": "((Age 18 to 70 years old) AND (ECOG performance status 2 or lower) AND (Estimated life expectancy more than 3 months) AND (Pathologically proven) AND (S-1) AND (absolute neutrophil count [ANC] ≥1,500/µL) AND (adenocarcinoma of stomach unresectable) AND (bone marrow function Adequate) AND (camptothecin analogues) AND (capecitabine) AND (conventional CT scan) AND (disease uni-dimensionally measurable) AND (hemoglobin ≥9.0 g/dL) AND (kidney function Adequate) AND (liver function Adequate) AND (liver metastasis <5 times UNL) AND (longest diameter at least 1cm) AND (longest diameter at least 2 cm) AND (physical examination) AND (platelets ≥100,000/µL) AND (serum creatinine < 1.5 mg/dL) AND (serum total bilirubin < 2 times the upper normal limit (UNL)) AND (serum transaminases levels <3 times UNL) AND (spiral CT scan) AND (x-ray) AND NOT (chemotherapy prior) AND NOT (adjuvant chemotherapy prior at least 6 months before enrollment) AND NOT (adjuvant chemotherapy prior) AND NOT (radiation therapy prior at least 4 weeks before enrollment))"}
```
