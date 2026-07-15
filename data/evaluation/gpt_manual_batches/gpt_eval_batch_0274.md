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
{"candidate_id": "LLM06826", "doc_id": "NCT01888965_inc", "case_bucket": "or", "source_criterion": "Patients with a confirmed diagnosis of: 1. Stage 4 colon cancer either s/p metastasectomy or post-initial chemotherapy or maintenance \"standard of care\", either involving 5-fluorouracil/leucovorin (5-FU/LV) alone or continual bevacizumab alone. Patients in maintenance cohort must have had 2 consecutive CT scans showing stable disease and not be experiencing significant prior treatment-related toxicity above Grade 1. 2. Pancreas cancer, either s/p resection and adjuvant chemotherapy or locally advanced pancreas cancer s/p chemotherapy and radiation. Initial chemotherapy or radiation therapy may have been stopped between 2 weeks and 2 months prior to study start, and patients must have recovered from prior treatment related toxicity to grade 1 or less. Prior surgery, including tumor resection or metastasectomy must have been performed at least 4 weeks prior to study enrollment. No concomitant anti-cancer treatment is allowed Age >/= 18 years Performance status of 0-1 Adequate hepatic, bone marrow, and renal function Partial thromboplastin time (PTT) must be </= 1.5 x upper normal limit of institution's normal range and INR (International Normalized Ratio) < 1.5. Life expectancy >/= 4 months for maintenance cohorts and >/= 6 months for adjuvant cohorts Women of childbearing potential must have a negative serum pregnancy test within 14 days prior to initiation of treatment and must not be lactating. Subject is capable of understanding and complying with protocol demands and able to sign and date the informed consent", "candidate_expression": "((Age >/= 18 years) AND (CT scans 2) AND (INR (International Normalized Ratio) < 1.5) AND (Life expectancy) AND (No concomitant anti-cancer treatment is allowed) AND (Pancreas cancer) AND (Partial thromboplastin time (PTT) </= 1.5 x upper normal limit) AND (Performance status 0-1) AND (Subject is capable of understanding and complying with protocol demands and able to sign and date the informed consent) AND (Women) AND (adjuvant chemotherapy) AND (bone marrow function Adequate) AND (chemotherapy) AND (childbearing potential) AND (colon cancer Stage 4) AND (disease stable) AND (function hepatic Adequate) AND (metastasectomy) AND (pancreas cancer locally advanced) AND (radiation) AND (recovered from prior treatment) AND (renal function Adequate) AND (resection) AND (s/p adjuvant chemotherapy) AND (s/p chemotherapy) AND (s/p radiation) AND (s/p resection) AND (serum pregnancy test negative within 14 days prior to initiation of treatment) AND (surgery Prior at least 4 weeks prior to study enrollment) AND (treatment prior) AND NOT (treatment-related toxicity prior) AND NOT (lactating) AND ((maintenance \"standard of care\") OR (post-initial chemotherapy) OR (s/p metastasectomy)) AND ((chemotherapy) OR (radiation therapy)) AND ((metastasectomy) OR (tumor resection)) AND ((adjuvant cohorts >/= 6 months) OR (maintenance cohorts >/= 4 months)) AND ((5-fluorouracil/leucovorin (5-FU/LV)) OR (bevacizumab)))"}
{"candidate_id": "LLM06827", "doc_id": "NCT01236417_inc", "case_bucket": "or", "source_criterion": "Post menopausal women with a history of estrogen positive breast cancer who are receiving aromatase inhibitors for at least one month. Patients must complain of mild to moderate arthralgia. Ability to understand and sign informed consent. Patients meet criteria for low to moderate risk for moderate exercise based oon the ACSM guidelines.", "candidate_expression": "((ACSM guidelines) AND (Ability to understand and sign informed consent.) AND (Post menopausal) AND (aromatase inhibitors for at least one month) AND (arthralgia) AND (breast cancer history estrogen positive) AND (risk for moderate exercise) AND (women) AND ((mild) OR (moderate)) AND ((low) OR (moderate)))"}
{"candidate_id": "LLM06828", "doc_id": "NCT03355157_exc", "case_bucket": "other", "source_criterion": "NA", "candidate_expression": "(EMPTY)"}
{"candidate_id": "LLM06829", "doc_id": "NCT00639795_inc", "case_bucket": "other", "source_criterion": "Age greater than 18 Planned thoracoscopy with low probability(by surgeon estimate) of conversion to open procedure", "candidate_expression": "((Age greater than 18) AND (low probability(by surgeon estimate) of conversion to open procedure) AND (thoracoscopy low probability(by surgeon estimate) of conversion to open procedure))"}
{"candidate_id": "LLM06830", "doc_id": "NCT02959801_inc", "case_bucket": "other", "source_criterion": "proven acute deep venous thrombosis, less than 21 days and who were referred to the interventional radiology department.", "candidate_expression": "((deep venous thrombosis proven acute less than 21 days) AND (interventional radiology department referred to))"}
{"candidate_id": "LLM06831", "doc_id": "NCT02270970_inc", "case_bucket": "or", "source_criterion": "Patients who meet 1987 ACR criteria for SLE with 1996 modifications SLEDAI >/= 6 at screening visit Positive ANA OR anti-dsDNA within one year of screening In the opinion of the investigator there is intent to treat with a biologic (e.g. patient failed standard of care treatment) however there is no organ threatening disease", "candidate_expression": "((1987 ACR criteria with 1996 modifications) AND (ANA Positive within one year of screening) AND (In the opinion of the investigator there is intent to treat with a biologic (e.g. patient failed standard of care treatment) however there is no organ threatening disease) AND (SLE) AND (SLEDAI >/= 6 at screening visit) AND (anti-dsDNA Positive within one year of screening))"}
{"candidate_id": "LLM06832", "doc_id": "NCT03208998_exc", "case_bucket": "or", "source_criterion": "Active consumption of alcohol and/or drugs Co-infection with human immunodeficiency virus, hepatitis C virus, or hepatitis D virus History of autoimmune hepatitis Psychiatric disease Evidence of neoplastic diseases of the liver", "candidate_expression": "((Psychiatric disease) AND (autoimmune hepatitis) AND (neoplastic diseases liver) AND ((consumption of alcohol) OR (drugs consumption of)) AND ((hepatitis C virus) OR (hepatitis D virus) OR (human immunodeficiency virus)))"}
{"candidate_id": "LLM06833", "doc_id": "NCT02385448_inc", "case_bucket": "or", "source_criterion": "Good general health Older than the age of legal consent (i.e. 18 years old) Sonographic diagnosis of ovarian endometrioma with diameter at least 4cm on 2 separate scans at least 6 weeks apart No contraindication to use of progesterone or combined oral contraceptive pills Not attempting to conceive either at the time of study entry or for at least 2 years after surgery Willing and able to participate after the study has been explained", "candidate_expression": "((Good general health) AND (Sonographic 2 separate scans) AND (age Older than the age of legal consent 18 years old) AND (combined oral contraceptive pills) AND (conceive attempting at the time of study entry for at least 2 years after surgery) AND (ovarian endometrioma diameter at least 4cm) AND (progesterone) AND NOT (contraindication))"}
{"candidate_id": "LLM06834", "doc_id": "NCT02653131_inc", "case_bucket": "or", "source_criterion": "patients receiving home parenteral nutrition (HPN) because of short bowel syndrome for at least 12 months stable metabolic status benign disease", "candidate_expression": "((benign disease) AND (for at least 12 months) AND (metabolic status) AND (stable) AND ((home parenteral nutrition (HPN)) OR (short bowel syndrome)))"}
{"candidate_id": "LLM06835", "doc_id": "NCT01175044_inc", "case_bucket": "other", "source_criterion": "Scheduled to undergo revision total knee arthroplasty", "candidate_expression": "(revision total knee arthroplasty)"}
{"candidate_id": "LLM06836", "doc_id": "NCT03493919_inc", "case_bucket": "or", "source_criterion": "Subjects who, in the opinion of the investigator, can and will comply with the requirements of the protocol. Written informed consent obtained from the subject prior to performing any study specific procedure. A male or female between, and including, 18 and 50 years of age at the time of the first study visit. Healthy subjects as established by medical history and clinical examination before entering into the study. Healthy subjects with no medical conditions that, in the opinion of the investigator, prevents the subject from participating in the study. Subjects must weigh at least 110 pounds (50 kg), but not to present obesity (BMI < 32kg/m2). Female subjects of non-childbearing potential may be enrolled in the study. Non-childbearing potential is defined as pre-menarche, current bilateral tubal ligation or occlusion, hysterectomy, bilateral ovariectomy or post-menopause. has practiced adequate contraception for 30 days prior to vaccination, and has a negative pregnancy test on the day of vaccination and has agreed to continue adequate contraception during the entire treatment period and for 1 month, after completion of the vaccination series.", "candidate_expression": "((18 and 50 years) AND (30 days prior to vaccination) AND (< 32kg/m2) AND (BMI) AND (Female) AND (Healthy) AND (Written informed consent) AND (adequate) AND (adequate contraception) AND (age) AND (at least 110 pounds) AND (at least 50 kg) AND (at the time of the first study visit) AND (before entering into the study) AND (bilateral ovariectomy) AND (bilateral tubal ligation) AND (bilateral tubal occlusion) AND (childbearing potential) AND (clinical examination) AND (completion of the vaccination series) AND (comply with the requirements of the protocol) AND (continue) AND (contraception) AND (current) AND (during the entire treatment period) AND (entering into the study) AND (female) AND (for 1 month, after completion of the vaccination series) AND (hysterectomy) AND (male) AND (medical history) AND (negative) AND (non-) AND (not to present) AND (obesity) AND (on the day of vaccination) AND (performing any study specific procedure) AND (post-menopause) AND (pre-menarche) AND (pregnancy test) AND (prior to performing any study specific procedure) AND (study specific procedure) AND (the first study visit) AND (vaccination) AND (weigh))"}
{"candidate_id": "LLM06837", "doc_id": "NCT03118232_inc", "case_bucket": "or", "source_criterion": "Nursing homes will be eligible to participate if they meet the following criteria: Licensed nursing home in Orange County or Southern Los Angeles County serving adults Minimal use of chlorhexidine bathing* Minimal use of nasal decolonization* *Minimal use defined as <15% of residents receiving at least one chlorhexidine bath or nasal decolonization treatment during their nursing home stay.", "candidate_expression": "((Licensed nursing home) AND (Nursing homes) AND (Orange County) AND (Southern Los Angeles County) AND (chlorhexidine) AND (chlorhexidine bath at least one) AND (chlorhexidine bathing Minimal use) AND (nasal decolonization Minimal use) AND (nasal decolonization treatment during their nursing home stay) AND (residents receiving at least one chlorhexidine bath <15%))"}
{"candidate_id": "LLM06838", "doc_id": "NCT02969187_inc", "case_bucket": "or", "source_criterion": "Fulfills NIH criteria for bariatric surgery Planned operation of laparoscopic Roux-en Y gastric bypass (LRYGB) or laparoscopic sleeve gastrectomy (LSG) as primary bariatric procedure", "candidate_expression": "((NIH criteria Fulfills) AND (bariatric surgery) AND (laparoscopic Roux-en Y gastric bypass (LRYGB)) AND (laparoscopic sleeve gastrectomy (LSG)))"}
{"candidate_id": "LLM06839", "doc_id": "NCT02056288_inc", "case_bucket": "other", "source_criterion": "Supracondylar fracture Age 2-17 years American Society of Anesthesiologists Status 1 -3 Scheduled for closed reduction with percutaneous pinning under general anesthesia", "candidate_expression": "((Age 2-17 years) AND (American Society of Anesthesiologists Status 1 -3) AND (Supracondylar fracture) AND (closed reduction with percutaneous pinning Scheduled for) AND (general anesthesia))"}
{"candidate_id": "LLM06840", "doc_id": "NCT03506477_exc", "case_bucket": "or", "source_criterion": "Form of diagnosed psoriasis other than chronic plaque psoriasis (i.e. guttate, erythrodermic, pustular) Diagnosis of other active, ongoing skin diseases or skin infections that may interfere with examination of psoriasis lesions Ongoing use of other psoriasis treatment including but not limited to topical or systemic corticosteroids, other topical medications (i.e. coal tar), oral or biologic medications for the treatment of psoriasis, and UV therapy. The following washout periods will be required: 2 weeks for topical therapy; 2 weeks for phototherapy; 12 weeks for biologic or targeted therapies; 4 weeks for other systemic therapies Use of oral estrogen therapy, excluding oral contraceptive pills Women who are pregnant, nursing, or of child-bearing potential who are unwilling to use appropriate method(s) of contraception. Patients unwilling to limit exposure to UV light Current significant medical problems that, in the discretion of the investigator, would put the patient at significant risk Patients with disorders of calcium metabolism and/or hypercalcemia Use of any investigational drug within 4 weeks prior to randomization, or 5 pharmacokinetic/pharmacodynamics half-lives, if known (whichever is longer) History of allergy to any component of the IP", "candidate_expression": "((Use of any investigational drug within 4 weeks prior to randomization, or 5 pharmacokinetic/pharmacodynamics half-lives, if known (whichever is longer)) AND (Women who are pregnant, nursing, or of child-bearing potential who are unwilling to use appropriate method(s) of contraception.) AND (allergy) AND (any component of the IP) AND (coal tar) AND (limit exposure to UV light unwilling) AND (oral estrogen therapy) AND (psoriasis) AND (treatment Ongoing) AND NOT (oral contraceptive pills) AND NOT (chronic plaque psoriasis) AND ((skin diseases) OR (skin infections)) AND ((UV therapy) OR (biologic medications) OR (oral medications) OR (systemic corticosteroids) OR (topical corticosteroids) OR (topical medications)) AND ((disorders of calcium metabolism) OR (hypercalcemia)) AND ((erythrodermic) OR (guttate) OR (pustular)))"}
{"candidate_id": "LLM06841", "doc_id": "NCT02413970_exc", "case_bucket": "or", "source_criterion": "Central + mixed apneas > 25% of the total apnea-hypopnea index (AHI) Any anatomical finding that would compromise the performance of upper airway stimulation, such as the presence of complete concentric collapse of the soft palate Any condition or procedure that has compromised neurological control of the upper airway Patients who are unable or do not have the necessary assistance to operate the patient remote Patients who are pregnant or plan to become pregnant Patients who will require magnetic resonance imaging (MRI) Patients with an implantable device that may be susceptible to unintended interaction with the Inspire system. Body Mass Index (BMI) of > 32 Any chronic medical illness or condition that contraindicates a surgical procedure under general anesthesia, as judged by the clinical study Investigator Has a terminal illness with life expectancy < 12 months Active psychiatric disease (psychotic illness, major depression, or acute anxiety attacks) which prevents subject compliance with the requirements of the investigational study testing Any other reason the investigator deems subject is unfit for participation in the study", "candidate_expression": "((AHI) AND (BMI > 32) AND (Body Mass Index) AND (MRI) AND (Patients who are pregnant or plan to become pregnant) AND (contraindicates) AND (general anesthesia) AND (life expectancy < 12 months) AND (magnetic resonance imaging) AND (psychiatric disease) AND (surgical procedure) AND (total apnea-hypopnea index > 25%) AND ((Central apneas) OR (mixed apneas)) AND ((acute anxiety attacks) OR (major depression) OR (psychotic illness)))"}
{"candidate_id": "LLM06842", "doc_id": "NCT01996436_exc", "case_bucket": "or", "source_criterion": "Inability to obtain consent from patient or patients kin Pregnant women less than 18 years of age of more than 80 years of age Hunt Hess Grade 5 SAH", "candidate_expression": "((Hunt Hess Grade 5) AND (Inability to obtain consent from patient or patients kin) AND (Pregnant women) AND (SAH) AND ((age less than 18 years) OR (age more than 80 years)))"}
{"candidate_id": "LLM06843", "doc_id": "NCT01912677_inc", "case_bucket": "or", "source_criterion": "Pregnant gestational age >= 28 weeks Systolic blood pressure >=160 mm Hg OR a diastolic blood pressure of >=110 mm Hg measured twice more than 15 minutes apart Able to swallow pills >= 18 years", "candidate_expression": "((>= 18) AND (>= 28 weeks) AND (>=110 mm Hg) AND (>=160 mm Hg) AND (Able to swallow pills) AND (Systolic blood pressure) AND (diastolic blood pressure) AND (gestational age) AND (years))"}
{"candidate_id": "LLM06844", "doc_id": "NCT02807857_exc", "case_bucket": "or", "source_criterion": "Use of investigational drugs either within 5 half-lives of enrollment, or within 30 days, or until the expected pharmacodynamic effect has returned to baseline, whichever is longer. Major surgery in the last 3 months prior to baseline or planned major surgery or cardiac intervention during the study. Cancer or other significant co-morbidities implying that the patient's condition is unstable. Comorbidities that can be associated with elevated natriuretic peptide (NP) levels: renal insufficiency, (eGFR < 25 ml/min/1.73 m² calculated according to MDRD formula), recent (less than 3 months) cerebral trauma or recent (less than 3 months) cerebrovascular incident, novel diagnosis or acute exacerbation of COPD within the last 3 months. Patients who are primarily managed and regularly followed-up by a cardiologist for their HF Highly frail patients whose estimated lifespan due to comorbidities by the judgement of the investigator is less than 6 months.", "candidate_expression": "((Cancer) AND (Comorbidities) AND (Major surgery last 3 months prior to baseline or planned major surgery or cardiac intervention during the study) AND (NP) AND (acute exacerbation of COPD last 3 months) AND (cerebral trauma less than 3 months) AND (cerebrovascular incident less than 3 months) AND (co-morbidities) AND (eGFR < 25 ml/min/1.73 m²) AND (lifespan less than 6 months) AND (natriuretic peptide levels elevated) AND (renal insufficiency))"}
{"candidate_id": "LLM06845", "doc_id": "NCT02281643_exc", "case_bucket": "or", "source_criterion": "Known intolerance to the doxycycline Body weight <40 kg Pregnancy or breastfeeding History of severe allergic reaction or anaphylaxis Alcohol or drug abuse", "candidate_expression": "((<40 kg) AND (History of) AND (doxycycline) AND (severe) AND ((Alcohol abuse) OR (drug abuse)) AND ((Body weight) OR (Pregnancy) OR (breastfeeding) OR (intolerance to the doxycycline)) AND ((allergic reaction) OR (anaphylaxis)))"}
{"candidate_id": "LLM06846", "doc_id": "NCT01944800_exc", "case_bucket": "other", "source_criterion": "NA", "candidate_expression": "(EMPTY)"}
{"candidate_id": "LLM06847", "doc_id": "NCT03027115_exc", "case_bucket": "or", "source_criterion": "Intolerability of tamsulosin or related drugs Investigator discretion Unwillingness or inability to comply with protocol procedures and assessments", "candidate_expression": "((Intolerability) AND (Unwillingness or inability to comply with protocol procedures and assessments) AND ((related drugs) OR (tamsulosin)))"}
{"candidate_id": "LLM06848", "doc_id": "NCT03027115_inc", "case_bucket": "other", "source_criterion": "Male 18 years of age Presenting with hernia requiring surgical intervention", "candidate_expression": "((Male) AND (age 18 years) AND (hernia) AND (surgical intervention requiring))"}
{"candidate_id": "LLM06849", "doc_id": "NCT03066440_exc", "case_bucket": "or", "source_criterion": "Age > 18 Years Physician discretion Septic or hypovolemic shock Signs of life-threatening cerebral edema or multi-organ failure upon presentation to the emergency room or pediatric intensive care unit Enrollment time more than 1 hr since arrival to emergency room or PICU Pregnancy", "candidate_expression": "((Age > 18 Years) AND (Enrollment more than 1 hr since arrival to emergency room or PICU) AND (PICU) AND (Pregnancy) AND (Septic shock) AND (cerebral edema) AND (emergency room) AND (hypovolemic shock) AND (multi-organ failure) AND (pediatric intensive care unit))"}
{"candidate_id": "LLM06850", "doc_id": "NCT02924870_exc", "case_bucket": "or", "source_criterion": "osteoarticular, neuromuscular or cognitive limitation that prevents ambulation previous diagnosis of active neoplastic disease institutionalized patients; alcohol consumption >60 g/day patient belonging to another health sector in the Community of Madrid or other community participation in another study within 6 months prior.", "candidate_expression": "((>60 g/day) AND (alcohol consumption) AND (ambulation) AND (cognitive limitation) AND (institutionalized) AND (neoplastic disease) AND (neuromuscular limitation) AND (osteoarticular limitation) AND (participation in another study within 6 months prior.) AND (prevents))"}
```
