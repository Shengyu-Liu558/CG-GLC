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
{"candidate_id": "LLM06651", "doc_id": "NCT01997112_exc", "case_bucket": "or", "source_criterion": "History of ischaemic heart disease, cardiac failure, cerebrovascular disease, liver impairment (ALT/AST>50IU/L) or stage 3-5 chronic kidney disease. History of overdose or suicidal ideation Patients weighing <55kgs. Patients with chronic pain requiring treatment, with a known allergy to paracetamol, or concomitant use of non-steroidal anti-inflammatories , oral anticoagulants or corticosteroids.", "candidate_expression": "((3-5) AND (<55kgs) AND (>50IU/L) AND (ALT) AND (AST) AND (cardiac failure) AND (cerebrovascular disease) AND (chronic kidney disease) AND (chronic pain) AND (concomitant) AND (corticosteroids) AND (ischaemic heart disease) AND (known allergy) AND (liver impairment) AND (non-steroidal anti-inflammatories) AND (oral anticoagulants) AND (overdose) AND (paracetamol) AND (requiring treatment) AND (stage) AND (suicidal ideation) AND (weighing))"}
{"candidate_id": "LLM06652", "doc_id": "NCT00650312_exc", "case_bucket": "or", "source_criterion": "1. Institutionalized subjects will not be used. 2 Social Habits: 1. Use of any tobacco products. 2. Ingestion of any alcoholic, caffeine- or xanthine-containing food or beverage within the 48 hours prior to the initial dose of study medication. 3. Ingestion of any vitamins or herbal products within the 48 hours prior to the initial dose of the study medication. 4. Any recent, significant change in dietary or exercise habits. 5. Positive test for any drug included in the urine drug screen. 3. Medications: 1. Use of any medication within the 14 days prior to the initial dose of study medication. 2. Use of any medication known to alter hepatic enzyme activity within 28 days prior to the initial dose of study medication. 3. Use of hormonal contraceptives and hormonal replacement therapy within three months prior to the initial dose of study medication. 4. Diseases: a. History of any significant chronic disease and/or hepatitis. b. History of drug and/or alcohol abuse. c. Acute illness at the time of either the prestudy medical evaluation or dosing. d. Positive HIV, Hepatitis B, or Hepatitis C test. e. Renal disease or renal dysfunction (as suggested by serum creatinine levels greater than or equal to 1.5 mg/dL (for males) and greater than or equal to 1.4 mg/dL (for females) or abnormal creatinine clearance). 5. Abnormal and clinically significant laboratory test results: 1. Clinically significant deviation from the Guide for Clinically Relevant Abnormalities (see Part II ADMINISTRATIVE ASPECTS OF BIOEQUIVALENCE PROTOCOLS). 2. Abnormal and clinically relevant ECG tracing. 6. Donation or loss of a significant volume of blood or plasma (> 450 mL) within 28 days prior to the initial dose of study medication. 7. Subjects who have received an investigational drug within 30 days prior to the initial dose of study medication. 8. Allergy or hypersensitivity to metformin hydrochloride. 9. History of difficulty in swallowing medication, or any gastrointestinal disorder which could affect the drug absorption.", "candidate_expression": "((Abnormal ECG tracing) AND (Abnormal and clinically significant laboratory test results:) AND (Allergy) AND (Clinically significant) AND (HIV test) AND (Hepatitis B test) AND (Hepatitis C test) AND (History) AND (Positive) AND (Renal disease) AND (abnormal creatinine clearance) AND (affect the drug absorption) AND (alcohol abuse) AND (chronic disease) AND (clinically relevant) AND (difficulty in swallowing medication) AND (drug abuse) AND (females) AND (gastrointestinal disorder) AND (greater than or equal to 1.4 mg/dL) AND (greater than or equal to 1.5 mg/dL) AND (hepatitis) AND (hormonal contraceptives) AND (hormonal replacement therapy) AND (hypersensitivity) AND (males) AND (medication) AND (medication known to alter hepatic enzyme activity) AND (metformin hydrochloride) AND (renal dysfunction) AND (serum creatinine levels) AND (significant) AND (the initial dose of study medication) AND (tobacco products) AND (within 28 days prior) AND (within the 14 days prior) AND (within three months prior))"}
{"candidate_id": "LLM06653", "doc_id": "NCT03120728_inc", "case_bucket": "or", "source_criterion": "Healthy, women ages 18 to 39yo with BMI <30 Regular menstrual cycles with duration between 24-35 days Completion of screening visit where ovulation will be assessed with blood draw for progesterone level (must be 5ng/mL or greater) Not seeking pregnancy during the study period Use of a non-hormonal form of contraception, such as: sterilization (tubal ligation, Essure), copper IUD (intrauterine device), barrier methods or abstinence Must speak English or Spanish", "candidate_expression": "((BMI <30) AND (Essure) AND (Healthy) AND (Not seeking pregnancy during the study period) AND (Regular menstrual cycles) AND (abstinence) AND (ages 18 to 39yo) AND (barrier methods) AND (copper IUD) AND (duration between 24-35 days) AND (intrauterine device) AND (non-hormonal form of contraception) AND (progesterone level 5ng/mL or greater) AND (sterilization) AND (tubal ligation) AND (women))"}
{"candidate_id": "LLM06654", "doc_id": "NCT02502734_inc", "case_bucket": "or", "source_criterion": "Aged 5 years to less than 12 years at Visit 1. At least 15 (25%) children of the total study population must be aged 5 to less than 8 years. Male or pre-menarchial female subjects. Subjects must be pre-adolescent without any signs of puberty (Tanner Stage 1). Normal range for their height and weight. Weight and height measurements should fall within the percentile range 3-97% of normal values for age according to Danish growth charts. Have a documented diagnosis of persistent asthma, as defined by the National Institutes of Health for at least 3 months prior to the Screening Visit. A pre-bronchodilatory forced expiratory flow in 1 second (FEV1) at Visit 1 (Screening) >=80% predicted. There should be no Short acting beta-agonist (SABA) use within 4 hours of this measurement. Using one of the following asthma therapies prior to entry into the study: SABA inhaler alone (e.g. salbutamol) on an as required basis and/or Regular non-inhaled corticosteroid (ICS) controller medications for asthma (e.g. cromones or leukotriene receptor antagonists) and/or Previously treated with ICS (equipotent to inhaled budesonide <=400 micrograms (mcg) total daily dose). There must be no ICS use within 2 weeks of Visit 1 (Screening). Able to replace their current SABA treatment with study supplied rescue SABA provided at Visit 1 for use as needed for the duration of the study. Written informed consent from at least one parent/care giver (legal guardian) and accompanying informed assent from the subject (where the subject is able to provide assent) prior to admission to the study: (1) If applicable, subject must be able and willing to give assent to take part in the study according to the local requirement. The study investigator is accountable for determining a child's capacity to assent to participation in a research study, taking into consideration any standards set by the responsible independent ethics committee (IEC). (2) Subject and their legal guardian(s) understand that the study requires them to be treated on an outpatient basis. (3) Subject and their legal guardian(s) understand that they must comply with study medication and study assessments including recording of peak expiratory flow and rescue SABA use, attending scheduled study visits, and being accessible by a telephone call.", "candidate_expression": "(((3) Subject and their legal guardian(s) understand that they must comply with study medication and study assessments including recording of peak expiratory flow and rescue SABA use, attending scheduled study visits, and being accessible by a telephone call.) AND (Able to replace their current SABA treatment with study supplied rescue SABA provided at Visit 1 for use as needed for the duration of the study.) AND (Aged 5 years to less than 12 years) AND (Male) AND (SABA) AND (SABA inhaler) AND (Tanner Stage 1) AND (The study investigator is accountable for determining a child's capacity to assent to participation in a research study, taking into consideration any standards set by the responsible independent ethics committee (IEC).) AND (Weight) AND (Written informed consent from at least one parent/care giver (legal guardian) and accompanying informed assent from the subject (where the subject is able to provide assent) prior to admission to the study: (1) If applicable, subject must be able and willing to give assent to take part in the study according to the local requirement.) AND (asthma therapies prior to entry into the study) AND (budesonide <=400 micrograms (mcg)) AND (female) AND (forced expiratory flow in 1 second (FEV1) pre-bronchodilatory at Visit 1 (Screening) >=80% predicted Visit 1 (Screening)) AND (height Normal range) AND (height within the percentile range 3-97%) AND (persistent asthma as defined by the National Institutes of Health at least 3 months prior to the Screening Visit) AND (pre-adolescent) AND (pre-menarchial) AND (rescue SABA) AND (salbutamol) AND (weight Normal range) AND NOT (signs of puberty) AND NOT (Short acting beta-agonist (SABA) within 4 hours of this measurement) AND NOT (ICS within 2 weeks of Visit 1 (Screening)) AND ((ICS) OR (cromones) OR (leukotriene receptor antagonists)))"}
{"candidate_id": "LLM06655", "doc_id": "NCT02205931_exc", "case_bucket": "or", "source_criterion": "Age <1m or > 24 months of age No secure diagnosis of epilepsy < 4 seizures/week on average in baseline period Trial of < 2 AEDs Continues on corticosteroids in previous 3 months prior to randomisation Metabolic disease contraindicating use of the ketogenic diet e.g. pyruvate carboxylase deficiency, MCAD from previous medical investigation and screening at baseline. Progressive neurological disease Severe gastroesophageal reflux Previous treatment with the ketogenic diet Concurrent participation in another clinical trial of an investigational medicinal product. Patients who are prescribed AEDs not listed in the trial IMPs", "candidate_expression": "((AEDs < 2) AND (Age <1m or > 24 months of age) AND (Concurrent participation in another clinical trial of an investigational medicinal product) AND (MCAD) AND (Metabolic disease) AND (contraindicating) AND (corticosteroids previous 3 months prior to randomisation) AND (gastroesophageal reflux Severe) AND (ketogenic diet) AND (ketogenic diet Previous) AND (neurological disease Progressive) AND (pyruvate carboxylase deficiency,) AND (seizures < 4 /week) AND NOT (epilepsy))"}
{"candidate_id": "LLM06656", "doc_id": "NCT03185130_exc", "case_bucket": "other", "source_criterion": "Pregnant Meningeal signs are present Acute angle closure glaucoma is suspected Head trauma within the previous two weeks Lumbar puncture within the previous two weeks Thunderclap onset of the headache Known allergy to one of the study drugs History of intracranial hypertension Is a prisoner Patient declined informed consent Non-English speaking patient or parent/guardian for pediatric patients Attending provider excludes patient Severe Dehydration", "candidate_expression": "((Acute angle closure glaucoma) AND (Dehydration) AND (Head trauma) AND (History) AND (Lumbar puncture) AND (Meningeal signs) AND (Pregnant) AND (Severe) AND (Thunderclap onset) AND (allergy) AND (declined) AND (headache) AND (informed consent) AND (intracranial hypertension) AND (prisoner) AND (study drugs) AND (suspected) AND (within the previous two weeks))"}
{"candidate_id": "LLM06657", "doc_id": "NCT02687178_exc", "case_bucket": "other", "source_criterion": "diabetes mellitus secondary hypertension pregnancy", "candidate_expression": "((diabetes mellitus) AND (pregnancy) AND (secondary hypertension))"}
{"candidate_id": "LLM06658", "doc_id": "NCT02251249_inc", "case_bucket": "or", "source_criterion": "Patient over 18 years weighing between 65 and 85 Kg Referred for STEMI within 6 hours from beginning of chest pain or stable coronary artery disease requiring a loading dose of Prasugrel or Ticagrelor according to the international recommendations. No previous treatment with Clopidogrel, Prasugrel or Ticagrelor. Patient fasting for at least 6 hours. Affiliate or receiving a social security system. Written informed consent.", "candidate_expression": "((No) AND (Written informed consent) AND (beginning of chest pain) AND (between 65 and 85 Kg) AND (chest pain) AND (fasting) AND (for at least 6 hours.) AND (loading dose) AND (over 18) AND (previous) AND (stable) AND (treatment) AND (weighing) AND (within 6 hours from beginning of chest pain) AND (years) AND ((Clopidogrel) OR (Prasugrel) OR (Ticagrelor)) AND ((STEMI) OR (coronary artery disease)) AND ((Prasugrel) OR (Ticagrelor)))"}
{"candidate_id": "LLM06659", "doc_id": "NCT03034837_exc", "case_bucket": "other", "source_criterion": "Can not cooperate with the treatment Can not obtain the child's parental consent", "candidate_expression": "((Can not obtain the child's parental consent) AND (child's parental consent) AND (cooperate with the treatment) AND (not))"}
{"candidate_id": "LLM06660", "doc_id": "NCT03325023_exc", "case_bucket": "or", "source_criterion": "Ovarian cancer, adrenal gland tumor, endometrial cancer, cervical cancer, breast cancer Congenital adrenal hyperplasia (17-OH-progesterone> 2.5 ng / mL) Clinically diagnosed Cushing's disease, acromegaly, gigantism Type I or II diabetes Unexplained bleeding from the genital tract Hormone treatment within the last 2 months", "candidate_expression": "((17-OH-progesterone) AND (> 2.5 ng / mL) AND (Clinically diagnosed) AND (Congenital adrenal hyperplasia) AND (Cushing's disease) AND (Hormone) AND (Hormone treatment) AND (Ovarian cancer) AND (Type I diabetes) AND (Type II diabetes) AND (Unexplained bleeding) AND (acromegaly) AND (adrenal gland tumor) AND (breast cancer) AND (cervical cancer) AND (endometrial cancer) AND (genital tract) AND (gigantism) AND (within the last 2 months))"}
{"candidate_id": "LLM06661", "doc_id": "NCT03461679_exc", "case_bucket": "other", "source_criterion": "Unable to consent Chronic opioid consumption Allergy to study medication Lower limb surgery preceding year Unable to complete baseline testing, pre-existing neurological deficit Contraindication to spinal anaesthesia", "candidate_expression": "((Allergy) AND (Chronic) AND (Contraindication) AND (Lower limb surgery) AND (Unable to consent) AND (neurological deficit) AND (opioid consumption) AND (pre-existing) AND (spinal anaesthesia) AND (study medication))"}
{"candidate_id": "LLM06662", "doc_id": "NCT00639795_exc", "case_bucket": "or", "source_criterion": "Age less than 18 Clinical or laboratory evidence of systemic infection Current pregnancy as assessed by preoperative urine HCG test Serious, uncontrolled, non-malignant illness Malignant illness requiring systemic chemotherapy in the last 6 months Documented allergy to oxycodone, morphine sulfate or acetaminophen Contraindication to peripheral nerve blockade or general anesthesia including: 1. patient refusal 2. active infection at site of planned block 3. documented allergy to any local or general anesthetic medications 4. significant coagulopathy( prothrombin time >15 seconds, INR>1.5 5. pre-existing neuropathy and medical conditions or deformities which would compromise block or anesthetic safety Planned pleurodesis Current use of high dose inhaled or systemic steroids Current use of Amiodarone (Cordarone) Morbid obesity (BMI=40kg/m2) Patients with clinically significant mental health issues such as psychosis requiring treatment with antipsychotic medications. Patients unable to consent Patients with active infections requiring antibiotics within one month of registration Participation in other clinical trials that may interfere with this study", "candidate_expression": "((40kg/m2) AND (>1.5) AND (>15 seconds) AND (Age) AND (Amiodarone) AND (BMI) AND (Contraindication to general anesthesia) AND (Contraindication to peripheral nerve blockade) AND (Cordarone) AND (Current) AND (INR) AND (Malignant illness) AND (Morbid obesity) AND (Serious) AND (acetaminophen) AND (active) AND (allergy) AND (antibiotics) AND (antipsychotic medications) AND (clinically significant) AND (coagulopathy) AND (high dose) AND (in the last 6 months) AND (infections) AND (inhaled) AND (less than 18) AND (mental health issues) AND (morphine sulfate) AND (neuropathy) AND (non-malignant illness) AND (oxycodone) AND (pleurodesis) AND (pre-existing) AND (pregnancy) AND (preoperative) AND (prothrombin time) AND (psychosis) AND (significant) AND (steroids) AND (systemic) AND (systemic chemotherapy) AND (treatment) AND (uncontrolled) AND (urine HCG test) AND (within one month of registration))"}
{"candidate_id": "LLM06663", "doc_id": "NCT01765231_exc", "case_bucket": "or", "source_criterion": "younger than 18 years old HBsAg positive or HBcAb negative or hepatitis B virus DNA positive at baseline pregnant or lactating women", "candidate_expression": "((at baseline) AND (old) AND (women) AND (younger than 18 years) AND ((HBcAb negative) OR (HBsAg positive) OR (hepatitis B virus DNA positive)) AND ((lactating) OR (pregnant)))"}
{"candidate_id": "LLM06664", "doc_id": "NCT01803828_exc", "case_bucket": "or", "source_criterion": "congenital or valvular cardiomyopathy; ischemic heart disease; endocrine diseases: male hypogonadism, hyperthyroidism, adrenal diseases, pituitary diseases proliferative retinopathy or autonomic neuropathy; contraindications to sildenafil use or CMR imaging;", "candidate_expression": "((cardiomyopathy) AND (contraindications) AND (endocrine diseases) AND (ischemic heart disease) AND ((autonomic neuropathy) OR (proliferative retinopathy)) AND ((CMR imaging) OR (sildenafil)) AND ((congenital) OR (valvular)) AND ((adrenal diseases) OR (hyperthyroidism) OR (male hypogonadism) OR (pituitary diseases)))"}
{"candidate_id": "LLM06665", "doc_id": "NCT02527512_inc", "case_bucket": "other", "source_criterion": "Age 3 to 18 years on day of surgery diagnosis of spinal deformity undergoing elective posterior spine multi-level instrumentation surgery", "candidate_expression": "((Age 3 to 18 years on day of surgery) AND (multi-level instrumentation surgery undergoing elective posterior spine) AND (spinal deformity))"}
{"candidate_id": "LLM06666", "doc_id": "NCT03317197_exc", "case_bucket": "or", "source_criterion": "Pregnant women and young children aged <18 years; Patients with underlying disease cases without the possibility of resuscitation (e.g., terminal cancer); Patients with do-not-resuscitate (DNR) status; Death by excessive bleeding (e.g., abdominal main artery rupture); Patients who have experienced in-hospital CA; Patients previously treated with steroid, anti-cancer medicine, or immunosuppression treatment before CA; Patients already been registered with other studies; or Patients from whom informed consent cannot be obtained", "candidate_expression": "((<18 years) AND (CA) AND (Death by excessive bleeding) AND (Patients already been registered with other studies; or) AND (Patients from whom informed consent cannot be obtained) AND (abdominal) AND (aged) AND (anti-cancer medicine) AND (before CA) AND (do-not-resuscitate (DNR) status) AND (hospital) AND (immunosuppression treatment) AND (in-hospital) AND (main artery rupture) AND (previously) AND (steroid) AND (terminal cancer) AND (treated) AND (underlying disease) AND (without the possibility of resuscitation) AND (women) AND (young children))"}
{"candidate_id": "LLM06667", "doc_id": "NCT02609698_inc", "case_bucket": "other", "source_criterion": "Patients aged 19 or older Patients who have submitted a written consent to participate in the clinical trial De novo lesion Patients scheduled for elective intervention to treat ischemic cardiovascular disease", "candidate_expression": "((De novo lesion) AND (Patients scheduled for elective intervention to treat ischemic cardiovascular disease) AND (Patients who have submitted a written consent to participate in the clinical trial) AND (aged 19 or older))"}
{"candidate_id": "LLM06668", "doc_id": "NCT02918409_exc", "case_bucket": "other", "source_criterion": "NA", "candidate_expression": "(EMPTY)"}
{"candidate_id": "LLM06669", "doc_id": "NCT00959569_exc", "case_bucket": "other", "source_criterion": "previous unusual response to esmolol inclusion in other randomized studies esmolol administration in the previous 30 days emergency operation", "candidate_expression": "((emergency) AND (esmolol) AND (in the previous 30 days) AND (inclusion in other randomized studies) AND (operation) AND (unusual response))"}
{"candidate_id": "LLM06670", "doc_id": "NCT01967420_exc", "case_bucket": "other", "source_criterion": "Active substance dependency History of severe head injury", "candidate_expression": "((severe head injury History) AND (substance dependency))"}
{"candidate_id": "LLM06671", "doc_id": "NCT03404804_inc", "case_bucket": "other", "source_criterion": "Children aged 3-16 with a parent/guardian (hereafter termed parent) reported history of allergy to a penicillin antibiotic in which the reported allergic reaction occurred at least six months prior to the current PED visit. Only children well enough to be discharged to home at the conclusion of the PED visit are eligible.", "candidate_expression": "((3-16) AND (Children) AND (PED) AND (aged) AND (allergic reaction) AND (allergy) AND (at least six months prior to the current PED visit) AND (at the conclusion of the PED visit) AND (penicillin antibiotic) AND (the conclusion of the PED visit) AND (well enough to be discharged to home))"}
{"candidate_id": "LLM06672", "doc_id": "NCT02952963_inc", "case_bucket": "or", "source_criterion": "Uncomplicated RYGB performed minimum 3 months prior to the study. Fasting glucose < 7,0 mM, HbA1c < 48 mmol/mol 3 months after RYGB", "candidate_expression": "((3 months after RYGB) AND (< 48 mmol/mol) AND (< 7,0 mM) AND (Fasting glucose) AND (HbA1c) AND (RYGB) AND (Uncomplicated) AND (minimum 3 months prior to the study) AND (the study))"}
{"candidate_id": "LLM06673", "doc_id": "NCT01994382_exc", "case_bucket": "or", "source_criterion": "Richter's syndrome, Burkitt's lymphoma, or Burkitt-like Lymphoma (transformed DLBCL from Follicular NHL are eligible). Prior transplant with stem cell infusion 90 days or active graft-versus-host treatment within 8 weeks of Day 1. Prior therapy with SYK inhibitors. Chronic treatment with strong CYP3A4 inhibitor/ inducer, acid reducing agent, Proton pump inhibitors Known lymphomatous involvement of the CNS. Persistent, unresolved NCI CTCAE v4.0 ≥ Grade 2, previous drug-related toxicity (except alopecia, erectile impotence, hot flashes, libido, neuropathy). Prior monoclonal antibody, radioimmunoconjugate, antibody drug conjugate, phototherapy, radiotherapy, chemotherapy, immunotherapy, immunosuppressive therapy, or any test agent within 3 weeks or for alemtuzumab 8 weeks of Day 1. For CTCL: (TSEBT) within 12 weeks, or initiation of topical steroid, nitrogen mustard, or topical retinoid within 2 weeks. (Stable topical ≥ 4 weeks prior to Day 1 allowed). Known carrier or infection for HIV/Hep B or C. HCV ab+ must be PCR-. HBV ab+ must be HBsAg- or undetectable DNA Active infection requiring systemic treatment, Significant GI disease, previous major gastric/bowel surgery, difficulty swallowing or malabsorption syndrome. Major surgery within 4 weeks Previous malignancies within 2 yrs. unless relapse risk is small (< 5%). Current use of systemic steroids >20 mg QD prednisone (or equivalent) Breastfeeding or pregnant (intention to become) females or participation in other clinical trials", "candidate_expression": "((CTCL 8 weeks of Day 1) AND (GI disease Significant) AND (Major) AND (NCI CTCAE v4.0 ≥ Grade 2) AND (SYK inhibitors) AND (Significant) AND (TSEBT within 12 weeks) AND (antibody drug conjugate) AND (chemotherapy) AND (drug-related toxicity previous) AND (females) AND (immunosuppressive therapy) AND (immunotherapy) AND (infection requiring systemic treatment) AND (lymphomatous involvement of the CNS) AND (major) AND (malignancies within 2 yrs.) AND (monoclonal antibody) AND (phototherapy) AND (prednisone >20 mg QD) AND (radioimmunoconjugate) AND (radiotherapy) AND (stem cell infusion) AND (surgery Major within 4 weeks) AND (systemic steroids) AND (systemic treatment) AND (therapy Prior) AND (undetectable DNA) AND (unless relapse risk is small (< 5%)) AND (≥ 4 weeks prior to Day 1 Day 1) AND ((graft-versus-host treatment active within 8 weeks of Day 1) OR (transplant Prior 90 days of Day 1)) AND ((Proton pump inhibitors) OR (acid reducing agent) OR (strong CYP3A4 inducer) OR (strong CYP3A4 inhibitor)) AND ((Burkitt's lymphoma) OR (Burkitt-like Lymphoma) OR (DLBCL) OR (Follicular NHL) OR (Richter's syndrome)) AND ((alopecia) OR (erectile impotence) OR (hot flashes) OR (libido) OR (neuropathy)) AND ((alemtuzumab) OR (within 3 weeks of Day 1 Day 1)) AND ((nitrogen mustard) OR (topical retinoid) OR (topical steroid initiation)) AND ((Hep B infection for) OR (Hep C infection for) OR (infection for HIV)) AND ((HBV ab+ HBsAg-) OR (HCV ab+ PCR-)) AND ((bowel surgery) OR (gastric surgery)) AND ((difficulty swallowing) OR (malabsorption syndrome)) AND ((Breastfeeding) OR (pregnant)))"}
{"candidate_id": "LLM06674", "doc_id": "NCT02053246_exc", "case_bucket": "or", "source_criterion": "Other causes of heart failure other than diastolic dysfunction, such as restrictive cardiomyopathy or infiltrative cardiomyopathy Women who are pregnant or nursing Liver cirrhosis, Primary valvular disease Acute coronary syndrome Causes of PH other than that of heart failure, such as: chronic thromboembolic PH, sickle-cell disease, or sarcoidosis Severe bradycardia or greater than 1st degree heart block Decompensated heart failure Current use of a third generation beta-blocker (nebivolol, carvedilol, or labetalol) or high dose of any beta-blockers (greater than 100 mg daily of metoprolol, or equivalent)", "candidate_expression": "((Acute coronary syndrome) AND (Causes of PH) AND (Decompensated) AND (Liver cirrhosis) AND (Primary valvular disease) AND (Severe) AND (Women) AND (any beta-blockers) AND (bradycardia) AND (carvedilol) AND (chronic thromboembolic PH) AND (diastolic dysfunction) AND (greater than 100 mg daily) AND (greater than 1st degree) AND (heart block) AND (heart failure) AND (high dose) AND (infiltrative cardiomyopathy) AND (labetalol) AND (metoprolol) AND (nebivolol) AND (nursing) AND (other than) AND (pregnant) AND (restrictive cardiomyopathy) AND (sarcoidosis) AND (sickle-cell disease) AND (third generation beta-blocker))"}
{"candidate_id": "LLM06675", "doc_id": "NCT02227992_exc", "case_bucket": "or", "source_criterion": "Subjects with known intolerance to blood products or to one of the components of the study product or is unwilling to receive blood products; Female subjects, who are of childbearing age (i.e. adolescent), who are pregnant or nursing; Subject is currently participating or plans to participate in any other investigational device or drug without prior approval from the Sponsor; Subjects who are known, current alcohol and/or drug abusers Subjects admitted for trauma surgery Subjects with any pre or intra-operative findings identified by the surgeon that may preclude conduct of the study procedure. Subject with TBS in an actively infected field (Class III Contaminated or Class IV Dirty or Infected) TBS is from large defects in arteries or veins where the injured vascular wall requires repair with maintenance of vessel patency and which would result in persistent exposure of the EVARREST™ or SURGICEL® to blood flow and pressure during healing and absorption of the product; TBS with major arterial bleeding requiring suture or mechanical ligation; Bleeding site is in, around, or in proximity to foramina in bone, or areas of bony confine.", "candidate_expression": "((Female subjects, who are of childbearing age (i.e. adolescent), who are pregnant or nursing) AND (Subject is currently participating or plans to participate in any other investigational device or drug without prior approval from the Sponsor) AND (TBS) AND (TBS Class III Contaminated Class IV Dirty or Infected) AND (alcohol abusers) AND (blood products) AND (drug abusers) AND (intolerance) AND (major arterial bleeding) AND (mechanical ligation) AND (suture) AND (trauma surgery))"}
```
