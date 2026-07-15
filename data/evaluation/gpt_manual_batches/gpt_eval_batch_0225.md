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
{"candidate_id": "LLM05601", "doc_id": "NCT02015923_exc", "case_bucket": "or", "source_criterion": "Cases of rectal tumours below 12cm from anal verge, or locally advanced tumours invading blood vessels, nerves or bone. Multiple bone metastasis or central nervous system metastasis Other neoplastic disease in the 5 previous years, except squamous or basal cell skin carcinoma or cervical \"in situ\" carcinoma Significant heart disease (chronic congestive heart failure, symptomatic coronary disease) or myocardial infarction in the previous 6 months Peripheral neuropathy Patients who do not give informed consent", "candidate_expression": "((Multiple bone metastasis) AND (Peripheral neuropathy) AND (basal cell skin carcinoma) AND (bone invading) AND (central nervous system metastasis) AND (cervical \"in situ\" carcinoma) AND (chronic congestive heart failure) AND (heart disease Significant) AND (invading blood vessels) AND (locally advanced tumours) AND (myocardial infarction in the previous 6 months) AND (neoplastic disease Other in the 5 previous years) AND (nerves invading) AND (rectal tumours below 12cm from anal verge) AND (squamous cell skin carcinoma) AND (symptomatic coronary disease))"}
{"candidate_id": "LLM05602", "doc_id": "NCT03012984_inc", "case_bucket": "other", "source_criterion": "Age >= 65 years, < 90 years; Scheduled to undergo surgery for primary solid organ cancer under general anesthesia, with an expected duration of surgery >=2 hours; Planned to use patient-controlled intravenous analgesia after surgery; Provide written informed consent.", "candidate_expression": "((>= 65 years, < 90 years) AND (Age) AND (Provide written informed consent) AND (Scheduled) AND (after surgery) AND (general anesthesia) AND (intravenous analgesia) AND (patient-controlled) AND (primary) AND (solid organ cancer) AND (surgery))"}
{"candidate_id": "LLM05603", "doc_id": "NCT01098383_inc", "case_bucket": "or", "source_criterion": "A formal diagnosis of Autism or Pervasive Developmental Disorder not otherwise specified (PDD-NOS), given by a child neurologist. Age: 10-18 years. A signed parental consent form.", "candidate_expression": "((10-18 years) AND (A signed parental consent form) AND (Age) AND (Autism) AND (PDD-NOS) AND (Pervasive Developmental Disorder not otherwise specified))"}
{"candidate_id": "LLM05604", "doc_id": "NCT01715584_inc", "case_bucket": "other", "source_criterion": "age over 40 composite head and neck tumor resection treated hypertension hypertension medications taken on morning of surgery (except diuretics)", "candidate_expression": "((age) AND (composite head and neck tumor resection) AND (diuretics) AND (except) AND (hypertension) AND (hypertension medications) AND (on morning of surgery) AND (over 40) AND (treated))"}
{"candidate_id": "LLM05605", "doc_id": "NCT02322203_inc", "case_bucket": "other", "source_criterion": "Males and females who are at least 18 years of age at time of enrollment. Subject understands the investigational nature of the study and provides written, informed consent.", "candidate_expression": "((Males) AND (Subject understands the investigational nature of the study and provides written, informed consent.) AND (age at time of enrollment) AND (females at least 18 years))"}
{"candidate_id": "LLM05606", "doc_id": "NCT02360631_exc", "case_bucket": "or", "source_criterion": "Renal impairment Evidence or history of clinically significant allergic reactions to varenicline A cardiovascular event in the past month History of alcohol or drug dependence in the past year Major depressive disorder in the last year requiring treatment History of panic disorder, psychosis, bipolar disorder, or eating disorders Use of tobacco products other than cigarettes in past 30 days Use of pharmacotherapy in the month prior to enrollment, including prior use of varenicline Pregnant, contemplating getting pregnant, or breastfeeding Plans to move from Kansas City during the treatment and follow-up phase Another household member enrolled in the study Evidence of current severe major depressive disorder or suicidal ideation", "candidate_expression": "((Major depressive disorder) AND (Pregnant, contemplating getting pregnant, or breastfeeding) AND (Renal impairment) AND (Use of tobacco) AND (allergic) AND (cardiovascular event) AND (cigarettes) AND (enrollment) AND (in the past month) AND (last year) AND (month prior to enrollment) AND (other than) AND (past 30 days) AND (pharmacotherapy) AND (severe) AND (the past year) AND (treatment) AND (varenicline) AND ((bipolar disorder) OR (eating disorders) OR (panic disorder) OR (psychosis)) AND ((major depressive disorder) OR (suicidal ideation)) AND ((alcohol dependence) OR (drug dependence)))"}
{"candidate_id": "LLM05607", "doc_id": "NCT02590822_exc", "case_bucket": "or", "source_criterion": "• Diabetes duration >12 years Currently taking more than three glucose lowering therapies Weight-loss of >5kg in the preceding 6 months Stage 4 or 5 chronic kidney disease (eGFR< 30ml/min/1.73m2), Current therapy with Insulin, thiazolidinediones, steroids or atypical antipsychotic medication Untreated thyroid disease Known macrovascular disease including coronary artery disease, stroke/TIA or peripheral vascular disease Presence of arrhythmia (including atrial fibrillation, atrial flutter, or 2nd or 3rd degree atrioventricular block) Known heart failure Other clinically relevant heart disease Inability to exercise or undertake a MRP Absolute contraindication to CMR Cardiovascular symptoms (angina, limiting dyspnoea during normal physical activity) Inflammatory condition e.g. Connective tissue disorder, Rheumatoid arthritis", "candidate_expression": "((CMR) AND (Cardiovascular symptoms) AND (Diabetes >12 years) AND (Inflammatory) AND (Weight-loss >5kg preceding 6 months) AND (arrhythmia) AND (chronic kidney disease Stage 4 or 5) AND (contraindication) AND (eGFR < 30ml/min/1.73m2) AND (glucose lowering therapies more than three) AND (heart disease) AND (heart failure) AND (macrovascular disease) AND (thyroid disease Untreated) AND ((Insulin) OR (atypical antipsychotic medication) OR (steroids) OR (thiazolidinediones)) AND ((TIA) OR (coronary artery disease) OR (peripheral vascular disease) OR (stroke)) AND ((2nd degree atrioventricular block) OR (3rd degree atrioventricular block) OR (atrial fibrillation) OR (atrial flutter)) AND ((MRP) OR (exercise)) AND ((angina) OR (dyspnoea)) AND ((Connective tissue disorder,) OR (Rheumatoid arthritis)))"}
{"candidate_id": "LLM05608", "doc_id": "NCT02946892_inc", "case_bucket": "or", "source_criterion": "Informed consent of parent(s) or legal guardian; informed consent or assent of subject as applicable. Male or female children between the ages of 10 and 35 years with congenital heart disease that has been palliated with a Fontan circulation. Ability of perform a maximal exercise test as defined by a respiratory exchange ratio (RER) greater than 1.0 at the time of maximal exercise", "candidate_expression": "((Ability of perform) AND (Fontan circulation) AND (ages) AND (at the time of maximal exercise) AND (between 10 and 35 years) AND (children) AND (congenital heart disease) AND (greater than 1.0) AND (maximal exercise test) AND (respiratory exchange ratio (RER)) AND ((Informed consent of legal guardian) OR (Informed consent of parent) OR (informed assent of subject) OR (informed consent of subject)) AND ((Male) OR (female)))"}
{"candidate_id": "LLM05609", "doc_id": "NCT02273791_exc", "case_bucket": "or", "source_criterion": "Moderate or severe endometriosis. Hydrosalpinx. Uterine abnormalities or myoma. Previous uterine surgery.", "candidate_expression": "((Hydrosalpinx) AND (Moderate) AND (Uterine abnormalities) AND (endometriosis) AND (myoma) AND (severe) AND (uterine surgery))"}
{"candidate_id": "LLM05610", "doc_id": "NCT03355326_inc", "case_bucket": "other", "source_criterion": "Diagnosis of uncomplicated gastroschisis Gestational age >33 weeks at time of delivery Weight >1900g at time of delivery Transfer of patient to Riley Hospital for Children prior to any abdominal surgery", "candidate_expression": "((>1900g) AND (>33 weeks) AND (Gestational age) AND (Riley Hospital for Children) AND (Transfer) AND (Weight) AND (abdominal surgery) AND (any abdominal surgery) AND (at time of delivery) AND (gastroschisis) AND (prior to any abdominal surgery) AND (uncomplicated))"}
{"candidate_id": "LLM05611", "doc_id": "NCT02488057_inc", "case_bucket": "other", "source_criterion": "Mexican-american Female BMI 30-42 willingness to complete protocol pre-diabetic English or Spanish literate", "candidate_expression": "((BMI 30-42) AND (Female) AND (Mexican-american) AND (pre-diabetic) AND (willingness to complete protocol))"}
{"candidate_id": "LLM05612", "doc_id": "NCT02678663_exc", "case_bucket": "or", "source_criterion": "Anticoagulant therapy during the past 1 week of the procedure Known coagulopathy History of liver cirrhosis, chronic kidney disease, malignancy, inflammatory bowel disease, significant infectious disease, polyposis syndrome", "candidate_expression": "((Anticoagulant during the past 1 week) AND (chronic kidney disease) AND (coagulopathy) AND (inflammatory bowel disease) AND (liver cirrhosis) AND (malignancy) AND (polyposis syndrome) AND (procedure) AND (significant infectious disease))"}
{"candidate_id": "LLM05613", "doc_id": "NCT00543712_inc", "case_bucket": "or", "source_criterion": "Ability to understand and willingness to sign a written informed consent document Age ≥ 18 years Histologic diagnosis of chondrosarcoma, verifiable after enrollment Measurable disease Previously treated or incurable disease without options for standard of care therapy ECOG performance status of 0-2 Life expectancy of > 3 months For patients of reproductive potential (males and females), use of reliable means for contraception (e.g., contraceptive pill, intrauterine device [IUD], physical barrier) throughout the trial and for 1 year following their final exposure to study treatment", "candidate_expression": "((0-2) AND (> 3 months) AND (Age) AND (ECOG performance status) AND (Histologic) AND (Life expectancy) AND (chondrosarcoma) AND (contraception) AND (for 1 year following their final exposure) AND (reproductive potential) AND (throughout the trial) AND (≥ 18 years) AND ((contraceptive pill) OR (intrauterine device [IUD]) OR (physical barrier)))"}
{"candidate_id": "LLM05614", "doc_id": "NCT01809041_inc", "case_bucket": "or", "source_criterion": "major elective gastrointestinal, gynecological, prostate or bladder surgery patients who are = 60 years old. the surgery is laparoscopic surgery and is expected to last for = 2 hours under general anesthesia and the patient will stay in hospital for at least 7 days after surgery. lack of serious hearing and vision impairment and be able to read so that neurobehavioral tests can be performed.", "candidate_expression": "((able to read) AND (bladder surgery) AND (gastrointestinal surgery) AND (gynecological surgery) AND (hearing impairment) AND (laparoscopic surgery) AND (last expected = 2 hour under general anesthesia) AND (neurobehavioral tests can be performed) AND (old = 60 years old) AND (prostate surgery) AND (stay in hospital will at least 7 days after surgery) AND (vision impairment))"}
{"candidate_id": "LLM05615", "doc_id": "NCT01822262_exc", "case_bucket": "or", "source_criterion": "Gallbladder's wall >3mm, atrophied gallbladder,gallstone obstruct the Hartmann's pouch. Abdominal ultrasound display the contractibility of gallbladder is poor. The aged patients with bad heart and lung function. Patients who has acute cholecystitis,pancreatitis,pancreaticobiliary diseases, especially choledocholithiasis. Pregnant or lactational women.", "candidate_expression": "((Abdominal ultrasound) AND (aged) AND (contractibility of gallbladder poor) AND (women) AND ((Gallbladder's wall >3mm) OR (atrophied gallbladder) OR (gallstone obstruct Hartmann's pouch)) AND ((bad heart function) OR (bad lung function)) AND ((acute cholecystitis) OR (choledocholithiasis) OR (pancreaticobiliary diseases) OR (pancreatitis)) AND ((Pregnant) OR (lactational)))"}
{"candidate_id": "LLM05616", "doc_id": "NCT02478346_exc", "case_bucket": "other", "source_criterion": "NA", "candidate_expression": "(EMPTY)"}
{"candidate_id": "LLM05617", "doc_id": "NCT03479502_exc", "case_bucket": "or", "source_criterion": "allergy to Doxycycline or Methylprednisolone, pregnancy, diagnosis, Inflammatory arthritis or diabetes, secondary adhesive capsulitis (history of significant trauma, rotator cuff tear injury, stroke) evidence of arthritis on x-ray, current infectious disease, and any previous treatment for the for adhesive capsulitis of the affected shoulder.", "candidate_expression": "((adhesive capsulitis) AND (affected shoulder) AND (allergy) AND (any) AND (arthritis) AND (current) AND (diagnosis) AND (evidence of) AND (history) AND (infectious disease) AND (pregnancy) AND (previous) AND (secondary) AND (significant) AND (treatment) AND (x-ray) AND ((Doxycycline) OR (Methylprednisolone)) AND ((rotator cuff tear injury) OR (stroke) OR (trauma)) AND ((Inflammatory arthritis) OR (diabetes)))"}
{"candidate_id": "LLM05618", "doc_id": "NCT02734173_exc", "case_bucket": "or", "source_criterion": "<18 years old Evidence of decompensated liver disease HOMA IR< 2.0 HIV seropositivity Chronic HBV/HIV infection Use of immune suppressing medications Active malignancy", "candidate_expression": "((HIV seropositivity) AND (HOMA IR < 2.0) AND (immune suppressing medications) AND (liver disease decompensated) AND (malignancy Active) AND (old <18 years) AND ((HIV infection Chronic) OR (infection Chronic HBV)))"}
{"candidate_id": "LLM05619", "doc_id": "NCT03140488_inc", "case_bucket": "other", "source_criterion": "Singleton pregnancy = 37 weeks gestation Patient presented for induction of labor who is determined to be a candidate for oxytocin Cephalic presentation Reassuring fetal health assessment (no abnormal findings in fetal assessment, see below) Meeting one of the following BMI category:", "candidate_expression": "((= 37 weeks) AND (Cephalic presentation) AND (Reassuring) AND (Singleton pregnancy) AND (abnormal findings) AND (candidate for oxytocin) AND (fetal assessment) AND (fetal health assessment) AND (gestation) AND (induction of labor) AND (no) AND (oxytocin) AND (presented for))"}
{"candidate_id": "LLM05620", "doc_id": "NCT02566928_exc", "case_bucket": "or", "source_criterion": "The patient is unwilling to provide informed consent acutely sick (for example, crying, wheezing, bleeding, screaming or shaken) unable to participate in a discussion about the study", "candidate_expression": "((The patient is unwilling to provide informed consent) AND (acutely sick) AND ((bleeding) OR (crying) OR (screaming) OR (shaken) OR (wheezing)))"}
{"candidate_id": "LLM05621", "doc_id": "NCT00749112_inc", "case_bucket": "or", "source_criterion": "Age: > or = 16 years Weight: more than 40 Kg Autoimmune Hemolytic anemia with clinical and biochemical evidence of hemolysis refractory to treatment, in relapse or steroids dependant Idiopathic thrombocytopenic purpura with platelet counts < 50,000, refractory to treatment, in relapse or steroids dependant", "candidate_expression": "((< 50,000) AND (> or = 16 years) AND (Age) AND (Autoimmune Hemolytic anemia) AND (Idiopathic thrombocytopenic purpura) AND (Weight) AND (biochemical evidence) AND (evidence clinical) AND (hemolysis) AND (in relapse) AND (more than 40 Kg) AND (platelet counts) AND (refractory to treatment) AND (steroids) AND (steroids dependant) AND (treatment))"}
{"candidate_id": "LLM05622", "doc_id": "NCT03491059_inc", "case_bucket": "or", "source_criterion": "males and females greater than or equal to 18 years of age current regular user of e-cigarettes (use at least once daily for the past 30 days) with nicotine strength > 6mg/ml health medical history abstinent from any tobacco/nicotine use for 4 hours prior to imaging", "candidate_expression": "((abstinent for 4 hours prior to imaging) AND (age greater than or equal to 18 years) AND (medical history health) AND (nicotine strength > 6mg/ml) AND (user regular e-cigarettes) AND ((nicotine) OR (tobacco)) AND ((females) OR (males)))"}
{"candidate_id": "LLM05623", "doc_id": "NCT03351972_inc", "case_bucket": "other", "source_criterion": "Adult outpatients (18 years or older) routinely referred for small bowel video capsule endoscopy (CE)", "candidate_expression": "((Adult 18 years or older) AND (outpatients) AND (small bowel video capsule endoscopy routinely referred))"}
{"candidate_id": "LLM05624", "doc_id": "NCT02686021_inc", "case_bucket": "scope", "source_criterion": "planned sequential both-sided lower third molar extraction (split-mouth) with osteotomy (with or without upper molar extraction in local anesthesia) able to understand the study and the NRS scale", "candidate_expression": "((able to understand the study) AND (both-sided) AND (local anesthesia) AND (lower third molar extraction) AND (osteotomy) AND (planned) AND (sequential) AND (split-mouth) AND (upper molar extraction))"}
{"candidate_id": "LLM05625", "doc_id": "NCT02441179_inc", "case_bucket": "or", "source_criterion": "1. Patients ≥ 18 years-old from \"Instituto Teletón Santiago\" and \"Hospital Clínico Mutual de seguridad\". 2. C5 to T12 spinal cord injury, classified as ISNCSCI grades C and D 3. Traumatic and non-traumatic, non-progressive lesions 4. Onset > 6 months 5. Ability to ambulate with or without assistive devices 6. Ability to follow verbal or visual commands 7. Signed informed consent", "candidate_expression": "((Ability to ambulate with assistive devices) AND (Ability to ambulate without assistive devices) AND (Ability to follow verbal commands) AND (Ability to follow visual commands) AND (C5 to T12) AND (Hospital Clínico Mutual de seguridad) AND (ISNCSCI) AND (Instituto Teletón Santiago) AND (Onset > 6 months) AND (Signed informed consent) AND (Traumatic) AND (grades C and D) AND (lesions) AND (non-progressive) AND (non-traumatic) AND (spinal cord injury) AND (years-old) AND (≥ 18 years))"}
```
