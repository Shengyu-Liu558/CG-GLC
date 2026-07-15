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
{"candidate_id": "LLM02976", "doc_id": "NCT01911650_inc", "case_bucket": "or", "source_criterion": "1. age 18-65 years, inclusive 2. diagnosis of moderate to severe AT, confirmed by Dr. Wilson using clinical symptoms and exam findings consistent with chronic AT (>6 month duration) - which includes pain while palpating the intratendinous swelling part of the Achilles tendon and relief of pain when tendon placed under tension - and pre-procedure US 3. self-reported AT-related pain for at least 6 months and VAS (Visual Analog Scale) pain >5 (0-10 scale) 4. self-reported failure of eccentric exercise protocol (at least 75% completion) 5. self-reported failure of at least 2 of the 3 most common treatments for AT (NSAIDS, rest/ice or taping) 6. patient considered surgery but decided to wait and/or refused surgery -", "candidate_expression": "((AT moderate to severe) AND (AT-related pain for at least 6 months) AND (VAS (Visual Analog Scale) pain >5 0-10 scale) AND (age 18-65 years, inclusive) AND (chronic AT >6 month duration) AND (failure of at least 2 of the 3 most common treatments for AT) AND (failure of eccentric exercise protocol self-reported at least 75%) AND (pain while palpating the intratendinous swelling part of the Achilles tendon) AND (relief of pain when tendon placed under tension) AND (self-reported) AND (surgery) AND ((NSAIDS) OR (ice) OR (rest) OR (taping)))"}
{"candidate_id": "LLM02977", "doc_id": "NCT00182520_exc", "case_bucket": "or", "source_criterion": "Any other primary DSM-IV diagnosis; DSM-IV criteria for body dysmorphic disorder, bipolar affective disorder, schizophrenia, psychotic disorder, current alcohol/substance abuse. A previous adequate trial of topiramate Comorbid major depressive disorder diagnosis which predates OCD diagnosis Cognitive behavioural therapy or additional psychotherapy in past four months Allergy or hypersensitivity to topiramate BMI < 20 History of kidney stones", "candidate_expression": "((Allergy) AND (BMI < 20) AND (Cognitive behavioural therapy) AND (DSM-IV criteria) AND (alcohol abuse) AND (bipolar affective disorder) AND (body dysmorphic disorder) AND (diagnosis primary DSM-IV) AND (hypersensitivity) AND (kidney stones History of) AND (major depressive disorder Comorbid predates OCD diagnosis) AND (psychotherapy additional in past four months) AND (psychotic disorder,) AND (schizophrenia) AND (substance abuse) AND (topiramate) AND (topiramate previous))"}
{"candidate_id": "LLM02978", "doc_id": "NCT00806273_inc", "case_bucket": "other", "source_criterion": "ASA 1 ASA 2 Pts have current treatment plan at OHSU for extraction of some or all of remaining teeth and scheduled for delivery of a removable appliance post extraction Teeth used are able to be isolated with rubber dam Understand and sign consent form", "candidate_expression": "((ASA 1) AND (ASA 2) AND (Understand and sign consent form) AND (treatment plan at OHSU scheduled for))"}
{"candidate_id": "LLM02979", "doc_id": "NCT02364648_exc", "case_bucket": "other", "source_criterion": "History of cardiovascular disease; Current pregnancy; Uncontrolled hypertension; Uncontrolled hyperlipidemia; Current hormone replacement therapy; Current use of tobacco products; Elevated liver enzymes; Current autoimmune disease; Daily use of of antioxidants >300mg", "candidate_expression": "((Elevated liver enzymes) AND (History) AND (antioxidants Daily use >300mg) AND (autoimmune disease Current) AND (cardiovascular disease) AND (hormone replacement therapy Current) AND (hyperlipidemia Uncontrolled) AND (hypertension Uncontrolled) AND (pregnancy Current) AND (use of tobacco products Current))"}
{"candidate_id": "LLM02980", "doc_id": "NCT02766530_inc", "case_bucket": "other", "source_criterion": "Women aged 25-75 years old. Women with recently diagnosed breast cancer and who will receive NAC to reduce tumor burden before surgery. (including locally advanced breast cancer (LABC) according to clinical assessment; or tumor size > 2cm, that is, at least T2 in TNM staging).", "candidate_expression": "((NAC reduce tumor burden before surgery) AND (Women) AND (aged 25-75 years old) AND (breast cancer))"}
{"candidate_id": "LLM02981", "doc_id": "NCT02121145_exc", "case_bucket": "or", "source_criterion": "Primary groups: Vaccination against typhoid fever within 5 years before dosing. History of clinical typhoid fever, clinical paratyphoid A or B fever. Immunization with any other vaccine (oral or parenteral) within 4 weeks prior to study start or planned vaccination during the study Current intake of antibiotics or end of antibiotic therapy <8 days before first IMP administration Chronic (longer than 14 days) administration of immunosuppressants or other immune-modifying drugs within 6 months before the first dose of investigational vaccine; oral corticosteroids in dosages of =0.5 mg/kg/d prednisolone or equivalent are excluded; inhaled or topical steroids are allowed Acute or chronic clinically significant gastrointestinal disease", "candidate_expression": "((<8 days before first IMP administration) AND (=0.5 mg/kg/d) AND (Acute) AND (Chronic administration) AND (Current) AND (History) AND (Immunization with vaccine) AND (Primary groups) AND (Vaccination against typhoid fever) AND (antibiotic therapy) AND (antibiotics) AND (any other) AND (chronic) AND (clinical paratyphoid A fever) AND (clinical paratyphoid B fever) AND (clinical typhoid fever) AND (clinically significant) AND (dosages) AND (dosing) AND (during the study) AND (end of) AND (excluded) AND (first IMP administration) AND (gastrointestinal disease) AND (immune-modifying drugs) AND (immunosuppressants) AND (investigational vaccine) AND (longer than 14 days) AND (oral) AND (oral corticosteroids) AND (other) AND (parenteral) AND (planned) AND (prednisolone or equivalent) AND (study start) AND (the first dose of investigational vaccine) AND (the study) AND (typhoid fever) AND (vaccination) AND (within 4 weeks prior to study start) AND (within 5 years before dosing) AND (within 6 months before the first dose of investigational vaccine))"}
{"candidate_id": "LLM02982", "doc_id": "NCT01884337_exc", "case_bucket": "or", "source_criterion": "Women who are pregnant or breastfeeding Known or suspected, acquired or bleeding or coagulation disorder in the subject or a first degree relative Active bleeding or at high risk for bleeding. Brain, spinal, ophthalmologic, or major surgery or trauma within the past 90 days other than the elective knee/hip surgery Active hepatobiliary disease Hemoglobin <9 g/dL Platelet count <100,000/mm3 Creatinine clearance <30 mL/min", "candidate_expression": "((<100,000/mm3) AND (<30 mL/min) AND (<9 g/dL) AND (Active) AND (Brain) AND (Creatinine clearance) AND (Hemoglobin) AND (Known) AND (Platelet count) AND (Women) AND (acquired disorder) AND (at high risk for) AND (bleeding) AND (bleeding disorder) AND (breastfeeding) AND (coagulation disorder) AND (elective hip surgery) AND (elective knee surgery) AND (first degree relative) AND (hepatobiliary disease) AND (in the subject) AND (major) AND (ophthalmologic) AND (other than) AND (pregnant) AND (spinal) AND (surgery) AND (suspected) AND (trauma) AND (within the past 90 days))"}
{"candidate_id": "LLM02983", "doc_id": "NCT03115320_exc", "case_bucket": "or", "source_criterion": "- Irregular menstrual cycle demanding preparing endometrium with hormones for frozen-thawed embryo No frozen embryos after IVF cycle Allergy to Pregnyl® or some of its ingredients in the medication or other contraindications due to Pregnyl®", "candidate_expression": "((IVF cycle frozen embryos) AND (Irregular menstrual cycle) AND (Pregnyl) AND (preparing endometrium with hormones for frozen-thawed embryo) AND ((Allergy) OR (contraindications)) AND ((Pregnyl) OR (some of its ingredients)))"}
{"candidate_id": "LLM02984", "doc_id": "NCT02612181_inc", "case_bucket": "other", "source_criterion": "Septic shock patients despite early goal directed therapy Agree to participate this study", "candidate_expression": "((Agree to participate this study) AND (Septic shock) AND (early goal directed therapy))"}
{"candidate_id": "LLM02985", "doc_id": "NCT03389061_exc", "case_bucket": "other", "source_criterion": "NA", "candidate_expression": "(EMPTY)"}
{"candidate_id": "LLM02986", "doc_id": "NCT03045562_exc", "case_bucket": "other", "source_criterion": "NA", "candidate_expression": "(EMPTY)"}
{"candidate_id": "LLM02987", "doc_id": "NCT00397215_inc", "case_bucket": "or", "source_criterion": "Subjects who the investigator believes that they can and will comply with the requirements of the protocol should be enrolled in the study. A male or female aged 61 years or above at the time of the first vaccination. Written informed consent obtained from the subject. Healthy subjects or subjects with well controlled underlying disease.", "candidate_expression": "((Written informed consent) AND (aged 61 years or above) AND (can and will comply with the requirements of the protocol) AND ((Healthy) OR (underlying disease well controlled)) AND ((female) OR (male)))"}
{"candidate_id": "LLM02988", "doc_id": "NCT02055053_exc", "case_bucket": "other", "source_criterion": "Conversion from laparoscopic to open surgery History of Chronic pain or ongoing treatment for chronic pain Age less than 18 yrs Allergy to local anesthetics", "candidate_expression": "((Age) AND (Allergy) AND (Chronic pain) AND (History) AND (chronic pain) AND (less than 18 yrs) AND (local anesthetics) AND (ongoing) AND (treatment))"}
{"candidate_id": "LLM02989", "doc_id": "NCT02414399_inc", "case_bucket": "other", "source_criterion": "Age 1-59 months, Plan to remain in study area greater than 6 months Discharged from hospital following non-trauma related admission", "candidate_expression": "((Age 1-59 months) AND (Discharged from hospital) AND (hospital) AND (non-trauma related admission) AND (remain in study area Plan greater than 6 months))"}
{"candidate_id": "LLM02990", "doc_id": "NCT01614041_inc", "case_bucket": "or", "source_criterion": "18-65 years old Male or female Diagnosed with GAD according to DSM-IV HAMA score=17 Provide with written informed consent Agree to be washed-out for two weeks if receiving SSRI, SNRI or NASA.", "candidate_expression": "((18-65) AND (=17) AND (DSM-IV) AND (GAD) AND (HAMA score) AND (Provide with written informed consent) AND (for two weeks) AND (washed-out) AND (years old) AND ((NASA) OR (SNRI) OR (SSRI)) AND ((Male) OR (female)))"}
{"candidate_id": "LLM02991", "doc_id": "NCT02589977_inc", "case_bucket": "or", "source_criterion": "estimated glomerular filtration rate (eGFR) > 60 ml/min preserved left ventricular ejection fraction (>= 50%) on echocardiography HEALTHY: normal cardiac structure and function on echocardiography, BP < 140/90 HYPERTENSIVE: history of BP >140/90, 1 or more antihypertensive medications, LV ejection fraction (LVEF) at least 50%, current BP < 160/90 HFpEF: physician-confirmed diagnosis of HF, symptomatic HF, LVEF at least 50%, elevated LV filling pressure by catheterization, echocardiographic criteria or B-type-natriuretic peptide > 100, current BP < 160/90", "candidate_expression": "((B-type-natriuretic peptide > 100) AND (BP < 140/90) AND (BP >140/90) AND (BP current < 160/90) AND (HEALTHY) AND (HF physician-confirmed) AND (HF symptomatic) AND (HFpEF) AND (HYPERTENSIVE) AND (LV ejection fraction (LVEF) at least 50%) AND (LV filling pressure elevated) AND (LVEF at least 50%) AND (antihypertensive medications 1 or more) AND (catheterization) AND (current BP < 160/90) AND (echocardiography) AND (estimated glomerular filtration rate (eGFR) > 60 ml/min) AND (history) AND (left ventricular ejection fraction preserved >= 50%) AND ((normal cardiac function) OR (normal cardiac structure)))"}
{"candidate_id": "LLM02992", "doc_id": "NCT00894712_exc", "case_bucket": "or", "source_criterion": "Visible skin pathology, excessive freckles, or skin blemishes in the test area. History of skin disease or hypersensitivity and repeated contact allergies. Sarcoma or squamous cell histology. Metastatic disease to the breast. Current tobacco use.", "candidate_expression": "((Metastatic disease to the breast) AND (Sarcoma) AND (contact allergies) AND (freckles excessive) AND (histology) AND (hypersensitivity) AND (skin blemishes) AND (skin disease) AND (skin pathology) AND (squamous cell) AND (tobacco use Current))"}
{"candidate_id": "LLM02993", "doc_id": "NCT02907554_exc", "case_bucket": "or", "source_criterion": "Contra-indication for multiorgan procurement (infections, cancer, etc) Preexistent chronic renal failure. Refusal for organ procurement by the donor (confirmed by the French national register or reported by the next-of-kin). Need for a double kidney transplantation. Need for a multiorgan transplantation", "candidate_expression": "((Contra-indication) AND (Refusal by the donor) AND (chronic renal failure Preexistent) AND (double kidney transplantation Need for) AND (multiorgan procurement) AND (multiorgan transplantation Need for) AND (organ procurement) AND ((French national register) OR (reported by the next-of-kin)) AND ((cancer) OR (infections)))"}
{"candidate_id": "LLM02994", "doc_id": "NCT00404495_exc", "case_bucket": "other", "source_criterion": "Diagnosis of brainstem glioma Concurrent administration of any other anti-tumor therapy Pre-existing uncontrolled diarrhea", "candidate_expression": "((Concurrent) AND (anti-tumor therapy) AND (any other) AND (brainstem glioma) AND (uncontrolled diarrhea))"}
{"candidate_id": "LLM02995", "doc_id": "NCT02863120_inc", "case_bucket": "or", "source_criterion": "Male or non-pregnant female between the ages of 18-65 Patients willing and able to sign the informed consent Patients able to comply with follow-up requirements including self-evaluations Patients requiring a primary total knee replacement Patients with a diagnosis of osteoarthritis, traumatic arthritis, or avascular necrosis", "candidate_expression": "((Male) AND (Patients willing and able to sign the informed consent) AND (ages 18-65) AND (atients able to comply with follow-up requirements including self-evaluations) AND (female pregnant) AND (primary total knee replacement) AND ((avascular necrosis) OR (osteoarthritis) OR (traumatic arthritis)))"}
{"candidate_id": "LLM02996", "doc_id": "NCT03198910_inc", "case_bucket": "or", "source_criterion": "Patients with pulmonary arterial hypertension (PAH) Patients with chronic thromboembolic pulmonary hypertension (CTEPH) All prevalent patients (diagnosed >12 month ago) with PAH or distal CTEPH who had a consultation at the PH centre in Zurich between November 2015 and November 2016)", "candidate_expression": "((Zurich) AND (chronic thromboembolic pulmonary hypertension (CTEPH)) AND (consultation at the PH centre) AND (pulmonary arterial hypertension (PAH)) AND ((CTEPH distal) OR (PAH)))"}
{"candidate_id": "LLM02997", "doc_id": "NCT01684501_inc", "case_bucket": "other", "source_criterion": "weigh more than 200 lbs are high level ambulators corresponding to levels E to F of the Special Interest Group of Amputee Medicine (SIGAM) mobility grade have the ability to follow multi-step commands.", "candidate_expression": "((Special Interest Group of Amputee Medicine (SIGAM) mobility grade) AND (ability to follow multi-step commands) AND (high level ambulators) AND (levels E to F) AND (more than 200 lbs) AND (weigh))"}
{"candidate_id": "LLM02998", "doc_id": "NCT01807897_inc", "case_bucket": "or", "source_criterion": "Veteran receiving care within the Veterans Health Administration healthcare system Age 18 years Physician diagnosis of chronic heart failure, American Heart Association Stage C-D LVEF <45% No change in active cardiac medications for 4 weeks prior to randomization Ability to provide informed consent Moderate to severe central or mixed central and obstructive sleep apnea, defined as an apnea-hypopnea index (AHI) 15 events per hour, with a central AHI >5 events/hour", "candidate_expression": "((15 events per hour,) AND (18 years) AND (<45%) AND (>5 events/hour) AND (AHI) AND (Ability to provide informed consent) AND (Age) AND (American Heart Association Stage) AND (C-D) AND (LVEF) AND (No) AND (Veteran) AND (Veterans Health Administration healthcare system) AND (apnea-hypopnea index) AND (cardiac medications) AND (central AHI) AND (change) AND (chronic heart failure) AND (for 4 weeks prior to randomization) AND (randomization) AND ((central sleep apnea) OR (mixed central sleep apnea) OR (obstructive sleep apnea)) AND ((Moderate) OR (severe)))"}
{"candidate_id": "LLM02999", "doc_id": "NCT01177891_inc", "case_bucket": "or", "source_criterion": "Patients of familial cases of POF : Female subjects between 16 and 40 years or women older than 40 years with a cessation of ovarian function before the age of 40 years with increased levels of FSH Primary or secondary amenorrhea for more than three months with LH and FSH> 30mUI/ml No cases of fragile X syndrome in the family or blepharophimosis syndrome At least two cases in the family Origin Caucasian Patient signing the consent form for at least the blood sample Patient with Social Security Population Index related topics : The presence of cycles until the age of 40 years with proven fertility, at least one child Amenorrhea and FSH> 30mUI/ml according to the criteria of the index subject Men of the family of index case Population control : Women of Caucasian origin Women who had regular cycles until at least age 40 and at least one child Lack of land autoimmune (no history of thyroid disease or diabetes type 1) Woman signing the consent form for at least the blood sample", "candidate_expression": "((Amenorrhea) AND (Caucasian At least two) AND (Caucasian origin) AND (FSH) AND (FSH > 30mUI/ml) AND (LH) AND (Patient signing the consent form for at least the blood sample) AND (The presence of cycles until the age of 40 years with proven fertility, at least one child) AND (Woman signing the consent form for at least the blood sample) AND (Women) AND (age before the age of 40 years) AND (age until at least age 40) AND (age until the age of 40 years) AND (amenorrhea) AND (autoimmune) AND (cessation of ovarian function) AND (levels of FSH increased) AND (presence of cycles) AND (regular cycles) AND (who had regular cycles until at least age 40) AND (years between 16 and 40 years) AND ((Primary) OR (secondary)) AND ((Female) OR (women older than 40 years)) AND ((blepharophimosis syndrome) OR (fragile X syndrome in the family)) AND ((diabetes type 1) OR (thyroid disease)))"}
{"candidate_id": "LLM03000", "doc_id": "NCT02872935_exc", "case_bucket": "other", "source_criterion": "Non- English speakers Height < 4' 11\" BMI >40 Kg/ mm Antiemetic drug use in the 24 hours prior to cesarean delivery, Hypertensive diseases of pregnancy Chronic hypertension receiving antihypertensive treatment Any other physical or psychiatric condition that may impair their ability to cooperate with study data collection.", "candidate_expression": "((< 4' 11\") AND (>40 Kg/ mm) AND (Antiemetic drug) AND (Any other physical or psychiatric condition that may impair their ability to cooperate with study data collection.) AND (BMI) AND (Chronic hypertension) AND (Height) AND (Hypertensive diseases of pregnancy) AND (Non- English speakers) AND (antihypertensive treatment) AND (cesarean delivery) AND (in the 24 hours prior to cesarean delivery))"}
```
