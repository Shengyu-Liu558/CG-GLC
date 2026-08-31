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
{"candidate_id": "LLM04076", "doc_id": "NCT02900443_inc", "case_bucket": "other", "source_criterion": "Probable or definite diagnosis of autoimmune hepatitis according to the International Autoimmune Hepatitis Study Group criteria First presentation of AIH requiring treatment according to the current EASL guidelines Age = 18 years Must provide informed consent and agree to comply with the trial protocol", "candidate_expression": "((= 18 years) AND (AIH) AND (Age) AND (EASL guidelines) AND (International Autoimmune Hepatitis Study Group criteria) AND (Must provide informed consent and agree to comply with the trial protocol) AND (autoimmune hepatitis) AND (treatment))"}
{"candidate_id": "LLM04077", "doc_id": "NCT00806936_exc", "case_bucket": "or", "source_criterion": "Known or suspected allergy to trial product(s) or related products Subjects who are unlikely to comply with protocol requirements, e.g. uncooperative attitude, inability to return for the final visit Subjects who previously enrolled in this study Females of childbearing potential who are pregnant, breast-feeding or intend to become pregnant or are not using adequate contraceptive methods The receipt of any investigational product within 3 months prior to this trial", "candidate_expression": "((Females) AND (Females of childbearing potential who are pregnant, breast-feeding or intend to become pregnant or are not using adequate contraceptive methods) AND (Subjects who are unlikely to comply with protocol requirements, e.g. uncooperative attitude, inability to return for the final visit) AND (Subjects who previously enrolled in this study) AND (investigational product within 3 months prior to this trial this trial) AND (related products) AND (trial product(s)) AND ((breast-feeding) OR (childbearing potential) OR (contraceptive methods adequate) OR (intend to become) OR (pregnant)) AND ((allergy related products) OR (allergy to trial product(s))))"}
{"candidate_id": "LLM04078", "doc_id": "NCT01980680_inc", "case_bucket": "or", "source_criterion": "Age between 20 and 40 Normal menstrual cycles: 25-34 days Oligomenorrhea/amenorrhea or polycystic syndrome (defined according to the Rotterdam criteria 2004) BMI >18 and <35 kg/m2", "candidate_expression": "((Age between 20 and 40) AND (BMI >18 and <35 kg/m2) AND (Normal menstrual cycles 25-34 days) AND (Oligomenorrhea) AND (amenorrhea) AND (polycystic syndrome Rotterdam criteria 2004))"}
{"candidate_id": "LLM04079", "doc_id": "NCT02552459_inc", "case_bucket": "other", "source_criterion": "patients undergoing venous malformation embolization operation through general anesthesia. aged 18-65 years old. operating time varies 1-4h,and extubation after the operation.", "candidate_expression": "((aged 18-65 years old) AND (extubation after the operation) AND (general anesthesia) AND (operating time 1-4h) AND (operation) AND (venous malformation embolization operation))"}
{"candidate_id": "LLM04080", "doc_id": "NCT02330757_inc", "case_bucket": "scope", "source_criterion": "Women without PCOS as defined by the Rotterdam criteria. Presence of at least 2 cryopreserved good quality cleavage-stage embryo (good quality cleavage-stage embryos display stage-specific cell division, have blastomeres of fairly equal size with few to no cytoplasmic fragments).", "candidate_expression": "((PCOS) AND (Rotterdam criteria) AND (at least 2) AND (cleavage-stage embryo) AND (cleavage-stage embryos) AND (cryopreserved) AND (few to no cytoplasmic fragments) AND (good quality) AND (have blastomeres of fairly equal size) AND (stage-specific cell division) AND (without))"}
{"candidate_id": "LLM04081", "doc_id": "NCT03382106_exc", "case_bucket": "or", "source_criterion": "Women only: Cannot be pregnant or nursing at baseline or plan to become pregnant during the course of the study Body Mass Index (BMI) > 32 Weight > 220 pounds Allergies to shell fish, seafood, eggs or iodine Heart disease, kidney disease or diabetes Diagnosis of asthma Any metal in or on the body (that cannot be removed) between the nose and the abdomen Any major organ system disease (by judgment of the study medical team) A glomerular filtration rate of 60 cc per minute or less. Nitroglycerin usage or nitrates and use of phosphodiesterase 5 (PDE5) inhibitors Prior history of hypersensitivity to sildenafil Currently prescribed a phosphodiesterase (PDE) inhibitors medication (ex: Viagra, Cialis, etc) Known Pulmonary Hypertension Has used e-cigarettes and marijuana <1 years", "candidate_expression": "((60 cc per minute or less) AND (<1 years) AND (> 220 pounds) AND (> 32) AND (Allergies) AND (Body Mass Index (BMI)) AND (Cannot be pregnant or nursing at baseline or plan to become pregnant during the course of the study) AND (Nitroglycerin) AND (Prior history) AND (Pulmonary Hypertension) AND (Weight) AND (Women) AND (asthma) AND (between the nose and the abdomen) AND (glomerular filtration rate) AND (hypersensitivity) AND (major organ system disease) AND (nitrates) AND (phosphodiesterase (PDE) inhibitors) AND (phosphodiesterase 5 (PDE5) inhibitors) AND (sildenafil) AND ((eggs) OR (iodine) OR (seafood) OR (shell fish)) AND ((Heart disease) OR (diabetes) OR (kidney disease)) AND ((metal in the body) OR (metal on the body)) AND ((Cialis) OR (Viagra)) AND ((used e-cigarettes) OR (used marijuana)))"}
{"candidate_id": "LLM04082", "doc_id": "NCT03044561_inc", "case_bucket": "other", "source_criterion": "(1) cases of infertility, older than 20 years of age and not older than 40 years. (2) Body mass index (BMI):20-29. (3) women have experienced two or more implantation failure attributed to inadequate endometrial development.", "candidate_expression": "((BMI) AND (Body mass index 20-29) AND (age older than 20 years not older than 40 years) AND (implantation two or more failure) AND (inadequate endometrial development attributed to) AND (infertility) AND (women))"}
{"candidate_id": "LLM04083", "doc_id": "NCT02511574_exc", "case_bucket": "other", "source_criterion": "no confirmation of the gestational age ruptured membranes painful regular uterine contractions major fetal abnormalities", "candidate_expression": "((fetal abnormalities major) AND (painful regular uterine contractions) AND (ruptured membranes) AND NOT (gestational age))"}
{"candidate_id": "LLM04084", "doc_id": "NCT02227992_inc", "case_bucket": "or", "source_criterion": "Paediatric subjects aged =28 days (= 1 month) to <18 years, requiring non-emergent open hepatic, abdominal, retroperitoneal, pelvic or thoracic (non-cardiac) surgical procedures. i) The first 36 subjects to be enrolled will be subjects aged =1 years to <18 years. ii) The next 4 subjects to be enrolled will be subjects aged =28 days to <1 year. The subject's parent/legal guardian must be willing to give permission for the subject to participate in the trial, and provide written informed consent for the subject. In addition, assent must be obtained from paediatric subjects who possess the intellectual and emotional ability to comprehend the concepts involved in the trial. If the paediatric subject is not able to provide assent (due to age, maturity and/or inability to intellectually and/or emotionally comprehend the trial), the parent/legal guardian's written Informed Consent for the subject will be acceptable for the subject to be included in the study. Presence of an appropriate mild or moderate bleeding soft tissue or hepatic parenchyma Target Bleeding Site (TBS) identified intra-operatively by the surgeon; Ability to firmly press trial treatment at TBS until 4 minutes after randomisation", "candidate_expression": "((Ability to firmly press trial treatment at TBS until 4 minutes after randomisation) AND (The subject's parent/legal guardian must be willing to give permission for the subject to participate in the trial, and provide written informed consent for the subject. In addition, assent must be obtained from paediatric subjects who possess the intellectual and emotional ability to comprehend the concepts involved in the trial. If the paediatric subject is not able to provide assent (due to age, maturity and/or inability to intellectually and/or emotionally comprehend the trial), the parent/legal guardian's written Informed Consent for the subject will be acceptable for the subject to be included in the study) AND (aged =28 days (= 1 month) to <18 years) AND (surgical procedures non-emergent open) AND ((abdominal) OR (hepatic) OR (non-cardiac) OR (pelvic) OR (retroperitoneal) OR (thoracic)))"}
{"candidate_id": "LLM04085", "doc_id": "NCT01531257_exc", "case_bucket": "or", "source_criterion": "1. Need for combined organ transplantation with an extra-renal organ and/or islet cell transplant. 2. Recipients of previous non-renal solid organ and/or islet cell transplantation. 3. Infection with HIV. 4. Inability or unwillingness of a participant and/or guardian to provide informed consent", "candidate_expression": "((Inability or unwillingness of a participant and/or guardian to provide informed consent) AND (Infection with HIV) AND (combined organ transplantation) AND ((extra-renal organ) OR (islet cell transplant)) AND ((islet cell transplantation) OR (non-renal solid organ transplantation)))"}
{"candidate_id": "LLM04086", "doc_id": "NCT00965900_inc", "case_bucket": "or", "source_criterion": "Liver cirrhosis Age between 18 and 70 years Esophageal varices with high bleeding risk: more than F2 and red color sign No previous history of upper gastrointestinal bleeding No previous history of endoscopic, radiologic, or surgical therapy for varices or ascites Do not take beta-blocker, ACE inhibitor, or nitrate Child-Pugh score <12", "candidate_expression": "((<12) AND (Age) AND (Child-Pugh score) AND (Do not) AND (Esophageal varices) AND (F2) AND (Liver cirrhosis) AND (No) AND (between 18 and 70 years) AND (high bleeding risk) AND (more than) AND (red color sign) AND (upper gastrointestinal bleeding) AND ((ascites) OR (varices)) AND ((endoscopic therapy) OR (radiologic therapy) OR (surgical therapy)) AND ((ACE inhibitor) OR (beta-blocker) OR (nitrate)))"}
{"candidate_id": "LLM04087", "doc_id": "NCT03011476_inc", "case_bucket": "or", "source_criterion": "Parkinson disease diagnosed by United Kingdom Parkinson's disease Society Brain Bank Criteria Postural instability and gait disturbance phenotype Hoehn and Yahr stage = 3 Mini-Mental status examination = 24", "candidate_expression": "((Hoehn and Yahr stage = 3) AND (Mini-Mental status examination = 2) AND (Parkinson disease) AND (Postural instability) AND (United Kingdom Parkinson's disease Society Brain Bank Criteria) AND (gait disturbance))"}
{"candidate_id": "LLM04088", "doc_id": "NCT02785549_inc", "case_bucket": "or", "source_criterion": "Patient's written informed consent. Adequate cognitive capacity. Adequate family support No acute diverticulitis episode in the last 3 months mNeff 0 acute diverticulitis (abdominal computed tomography scan) No antibiotic treatment in the last 2 weeks Immunocompetence* No significant comorbidities** Good oral tolerance Good symptom control Maximum one of the following SIRS criteria (* T>38 ºC or <36ºC, L>12,000 or <4000/uL, HR>90 bpm, RR<20 rpm) or CRP>15 mg/dL", "candidate_expression": "((0) AND (<20 rpm) AND (<36ºC) AND (<4000/uL) AND (>12,000 /uL) AND (>15 mg/dL) AND (>38 ºC) AND (>90 bpm) AND (Adequate family support) AND (CRP) AND (Good) AND (HR) AND (Immunocompetence) AND (L) AND (No) AND (Patient's written informed consent. Adequate cognitive capacity) AND (RR) AND (SIRS criteria) AND (T) AND (abdominal computed tomography scan) AND (acute) AND (antibiotic treatment) AND (comorbidities) AND (diverticulitis) AND (in the last 2 weeks) AND (in the last 3 months) AND (mNeff) AND (oral tolerance) AND (significant) AND (symptom control))"}
{"candidate_id": "LLM04089", "doc_id": "NCT03115320_exc", "case_bucket": "or", "source_criterion": "- Irregular menstrual cycle demanding preparing endometrium with hormones for frozen-thawed embryo No frozen embryos after IVF cycle Allergy to Pregnyl® or some of its ingredients in the medication or other contraindications due to Pregnyl®", "candidate_expression": "((IVF cycle) AND (Irregular menstrual cycle) AND (No) AND (Pregnyl) AND (frozen embryos) AND (preparing endometrium with hormones for frozen-thawed embryo) AND ((Allergy) OR (contraindications)) AND ((Pregnyl) OR (some of its ingredients)))"}
{"candidate_id": "LLM04090", "doc_id": "NCT02951832_exc", "case_bucket": "or", "source_criterion": "Having experienced severe allergies, trauma history and/or operation history within 3 months; With a history of mental illness and/or family history of mental illness; Limb disabled; Taking medicine within one month; Suffering major events or having mood swings.", "candidate_expression": "((Limb disabled) AND (major events) AND (medicine within one month) AND (mental illness family history) AND (mental illness history) AND (mood swings) AND (operation within 3 months) AND (severe allergies within 3 months) AND (trauma within 3 months))"}
{"candidate_id": "LLM04091", "doc_id": "NCT03416413_inc", "case_bucket": "or", "source_criterion": "Adults over 18 years of age Symptomatic GSV or SSV vein reflux > 0.5 seconds on colour Duplex Varicose vein tributary requiring treatment", "candidate_expression": "((Adults) AND (GSV vein reflux) AND (SSV vein reflux) AND (age over 18 years of age) AND (colour Duplex) AND (treatment Varicose vein tributary requiring))"}
{"candidate_id": "LLM04092", "doc_id": "NCT02053246_exc", "case_bucket": "or", "source_criterion": "Other causes of heart failure other than diastolic dysfunction, such as restrictive cardiomyopathy or infiltrative cardiomyopathy Women who are pregnant or nursing Liver cirrhosis, Primary valvular disease Acute coronary syndrome Causes of PH other than that of heart failure, such as: chronic thromboembolic PH, sickle-cell disease, or sarcoidosis Severe bradycardia or greater than 1st degree heart block Decompensated heart failure Current use of a third generation beta-blocker (nebivolol, carvedilol, or labetalol) or high dose of any beta-blockers (greater than 100 mg daily of metoprolol, or equivalent)", "candidate_expression": "((Acute coronary syndrome) AND (Causes of PH) AND (Liver cirrhosis) AND (Primary valvular disease) AND (Women) AND (any beta-blockers high dose) AND (bradycardia Severe) AND (carvedilol) AND (chronic thromboembolic PH) AND (heart block greater than 1st degree) AND (heart failure) AND (heart failure Decompensated) AND (infiltrative cardiomyopathy) AND (labetalol) AND (metoprolol greater than 100 mg daily) AND (nebivolol) AND (nursing) AND (pregnant) AND (restrictive cardiomyopathy) AND (sarcoidosis) AND (sickle-cell disease) AND (third generation beta-blocker) AND NOT (heart failure) AND NOT (diastolic dysfunction))"}
{"candidate_id": "LLM04093", "doc_id": "NCT03337503_exc", "case_bucket": "or", "source_criterion": "Acute pain (less than 3 months in duration) Previous serious adverse event or hypersensitivity to cannabis or cannabinoids Inability to understand and comply with the instructions of the study Presence of significant cardiac disease (history of unstable ischemic heart disease, heart failure, severe and uncontrolled hypertension) that, in the opinion of the investigator, would put the patient at risk of a clinically significant arrhythmia or myocardial infarction Current substance use disorder according to the Diagnostic and Statistical Manual of Mental Disorders Fifth Edition (DSM 5) Life-time history of dependence on cannabis or diagnosis of cannabis use disorder (CUD) according to the DSM 5 Life-time history of DSM 5 schizophrenia, bipolar disorder, or previous psychosis with or intolerance to cannabinoids Current or history of suicidal ideation Pregnant, breast-feeding or female patients of child-bearing potential and male patients whose partner is of child-bearing potential, unless willing to ensure that they or their partner use effective contraception Hepatic impairment (aspartate aminotransferase more than three times normal) or renal function impairment (serum creatinine level >133 µmol/L, Estimated Glomerular Filtration Rate (eGFR) <60) Cognitive impairment according to MiniCog The patient is currently using or has used cannabinoid based medications within 90 days of study entry and is unwilling to abstain for the duration of the study Positive urine drug screen for cannabinoids and other potential abuse substances (e.g. alcohol, cocaine, amphetamines and methamphetamines, unprescribed opioids) Participation in another clinical trial within 30 days of enrolment in our trial", "candidate_expression": "((Cognitive impairment) AND (Estimated Glomerular Filtration Rate (eGFR) <60) AND (Hepatic impairment) AND (MiniCog) AND (Participation in another clinical trial within 30 days of enrolment in our trial) AND (Pregnant, breast-feeding or female patients of child-bearing potential and male patients whose partner is of child-bearing potential, unless willing to ensure that they or their partner use effective contraception) AND (adverse event serious) AND (alcohol) AND (amphetamines) AND (arrhythmia) AND (aspartate aminotransferase more than three times normal) AND (bipolar disorder) AND (cannabinoid based medications within 90 days of study entry) AND (cannabinoids) AND (cannabinoids Current) AND (cannabis) AND (cannabis use disorder (CUD) DSM 5) AND (cardiac disease significant) AND (cocaine) AND (dependence on cannabis) AND (duration less than 3 months) AND (heart failure) AND (history) AND (hypersensitivity) AND (hypertension severe uncontrolled) AND (intolerance) AND (methamphetamines) AND (myocardial infarction) AND (opioids unprescribed) AND (pain Acute) AND (psychosis) AND (renal function impairment) AND (schizophrenia DSM 5) AND (serum creatinine level >133 µmol/L) AND (substance use disorder Diagnostic and Statistical Manual of Mental Disorders Fifth Edition (DSM 5)) AND (suicidal ideation) AND (unstable ischemic heart disease) AND (urine drug screen Positive))"}
{"candidate_id": "LLM04094", "doc_id": "NCT03373318_inc", "case_bucket": "other", "source_criterion": "Adult patients (> 18 years) scheduled for cardiopulmonary bypass surgery with Glomerular Filtration Rate (GFR) greater than or equal to 60 and left ventricular ejection fraction greater than or equal to 40%", "candidate_expression": "((> 18 years) AND (Adult) AND (Glomerular Filtration Rate (GFR)) AND (cardiopulmonary bypass surgery) AND (greater than or equal to 40%) AND (greater than or equal to 60) AND (left ventricular ejection fraction) AND (scheduled for) AND (years))"}
{"candidate_id": "LLM04095", "doc_id": "NCT01715714_inc", "case_bucket": "or", "source_criterion": "Patients on chronic statin treatment (>30 days) scheduled for isolated CABG, including on- or off-pump or repeat (redo's) revascularisation procedures Stable or unstable angina, including non ST-segment-elevation acute coronary syndrome (NSTE-ACS) Age = 18 years Written informed consent", "candidate_expression": "((= 18 years) AND (>30 days) AND (Age) AND (CABG) AND (NSTE-ACS) AND (Stable angina) AND (chronic) AND (isolated) AND (non ST-segment-elevation acute coronary syndrome) AND (on- or off-pump or repeat) AND (redo's) AND (revascularisation procedures) AND (scheduled) AND (statin) AND (treatment) AND (unstable angina))"}
{"candidate_id": "LLM04096", "doc_id": "NCT02564471_inc", "case_bucket": "or", "source_criterion": "Provide signed and dated informed consent form. Willing to comply with all study procedures and be available for the duration of the study. Male or female, aged = 18 to = 60 years on day of inclusion. In good general health based on medical history and physical exam", "candidate_expression": "((= 18 to = 60 years) AND (Willing to comply with all study procedures and be available for the duration of the study.) AND (aged) AND (good general health) AND (medical history) AND (on day of inclusion) AND (physical exam) AND ((Male) OR (female)))"}
{"candidate_id": "LLM04097", "doc_id": "NCT01116973_exc", "case_bucket": "or", "source_criterion": "Inability to obtain consent Subjects under 18 years of age Non-English speaking subjects Subjects that are unable to lay flat due to pulmonary complications, increased intracranial pressure (ICP), or unstable spinal cord injuries Subjects with known cardiac abnormalities (atrial septal defects or ventricular septal defects, severe tricuspid valve disease, severe pulmonary hypertension, Ejection fraction < 15%) Prisoners Subjects with known upper extremity deep vein thromboses (subclavian or distal) Subjects with non-functional CICC or PICC distal ports Subjects with femoral CICCs Pregnant women", "candidate_expression": "((CICC distal ports) AND (Ejection fraction < 15%) AND (Inability to obtain consent) AND (PICC distal ports) AND (Pregnant) AND (Prisoners) AND (age under 18 years) AND (atrial septal defects) AND (cardiac abnormalities) AND (femoral CICCs) AND (increased intracranial pressure (ICP)) AND (pulmonary complications) AND (pulmonary hypertension severe) AND (spinal cord injuries unstable) AND (tricuspid valve disease severe) AND (unable to lay flat due to pulmonary complications) AND (upper extremity deep vein thromboses subclavian distal) AND (ventricular septal defects) AND (women))"}
{"candidate_id": "LLM04098", "doc_id": "NCT02822001_exc", "case_bucket": "or", "source_criterion": "Patients unable to give informed consent. Any patient whose condition will not allow for placement of the electrode PadSet. Patients whose tracheas were not extubated in OR or PACU. Patients with Impaired Renal Function with a have a known estimated CrCl<30 ml/min Patients using oral contraception.", "candidate_expression": "((Impaired Renal Function) AND (Patients unable to give informed consent) AND (condition) AND (electrode PadSet) AND (estimated CrCl <30 ml/min) AND (oral contraception) AND (placement allow) AND NOT (extubated tracheas) AND ((OR) OR (PACU)))"}
{"candidate_id": "LLM04099", "doc_id": "NCT02831166_exc", "case_bucket": "or", "source_criterion": "Less than 18 years of age; Pregnancy; Chronic use of vitamin K antagonists or direct thrombin inhibitors, or oral Xa-factor antagonists; Hypersensitivity to antiplatelet and/or anticoagulant drugs; Active bleeding or high bleeding risk (severe liver failure, active peptic ulcer, creatinine clearance < 30 mL/min, platelets count < 100.000 mm3); Uncontrolled systemic hypertension; Cardiogenic shock; Previous myocardial revascularization surgery with = 1 internal mammary or radial artery graft; Documented chronic peripheral arterial disease preventing the use of the femoral technique; Severe concomitant disease with life expectancy below 12 months; Participation in drug or devices investigative clinical trials in the last 30 days; Medical, geographic or social conditions impairing the participation in the study or inability to understand and sign the informed consent term.", "candidate_expression": "((Cardiogenic shock) AND (Hypersensitivity) AND (Medical, geographic or social conditions impairing the participation in the study or inability to understand and sign the informed consent term.) AND (Pregnancy) AND (age Less than 18 years) AND (disease Severe concomitant life expectancy) AND (myocardial revascularization surgery Previous) AND (peripheral arterial disease chronic) AND (systemic hypertension Uncontrolled) AND NOT (femoral technique) AND ((anticoagulant drugs) OR (antiplatelet drugs)) AND ((bleeding Active) OR (creatinine clearance < 30 mL/min) OR (high bleeding risk) OR (liver failure severe) OR (peptic ulcer active) OR (platelets count < 100.000 mm3)) AND ((internal mammary graft) OR (radial artery graft)) AND ((direct thrombin inhibitors) OR (oral Xa-factor antagonists) OR (vitamin K antagonists)))"}
{"candidate_id": "LLM04100", "doc_id": "NCT02056288_exc", "case_bucket": "or", "source_criterion": "Pulseless extremity Compromised neurologic status on exam (specifically assessment of radial, ulnar, and median nerve) Known allergy to local anesthetics (7) Not scheduled for closed reduction with percutaneous pinning under general anesthesia Bleeding diathesis American Society of Anesthesiologist (ASA) status 4 or higher. Sleep apnea by polysomnography", "candidate_expression": "((American Society of Anesthesiologist (ASA) status 4 or higher) AND (Bleeding diathesis) AND (Compromised neurologic status nerve radial) AND (Pulseless extremity) AND (Sleep apnea) AND (allergy nerve ulnar median nerve) AND (closed reduction with percutaneous pinning scheduled for) AND (general anesthesia) AND (local anesthetics) AND (polysomnography))"}
```
