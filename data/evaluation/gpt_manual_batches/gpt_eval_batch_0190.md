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
{"candidate_id": "LLM04726", "doc_id": "NCT00379366_inc", "case_bucket": "other", "source_criterion": "over 18 years successful angioplasty (residual stenosis < 30%) on a significant stenosis (maximal systolic speed 3 times > from basal maximal systolic speed, stenosis > 70% on angiography) on the venous-prosthesis anastomosis or on the venous segment 5 cm after the anastomosis of a prosthetic haemodialysis vascular access (at least 1 month old) social security affiliation signed informed consent", "candidate_expression": "((3 times > from basal) AND (< 30%) AND (> 70%) AND (angiography) AND (maximal systolic speed) AND (on the venous segment 5 cm after the anastomosis angioplasty) AND (on the venous-prosthesis anastomosis angioplasty) AND (over 18 years) AND (residual stenosis) AND (signed informed consent) AND (significant) AND (social security affiliation) AND (stenosis) AND (successful))"}
{"candidate_id": "LLM04727", "doc_id": "NCT02273791_exc", "case_bucket": "or", "source_criterion": "Moderate or severe endometriosis. Hydrosalpinx. Uterine abnormalities or myoma. Previous uterine surgery.", "candidate_expression": "((Hydrosalpinx) AND (endometriosis) AND (uterine surgery) AND ((Moderate) OR (severe)) AND ((Uterine abnormalities) OR (myoma)))"}
{"candidate_id": "LLM04728", "doc_id": "NCT02969187_exc", "case_bucket": "or", "source_criterion": "BMI <35 and > 60 kg/m2 Inability to walk (bed-bound or wheelchair dependence) open abdominal surgeries except simple appendectomy and common OB/GYN procedures in the pelvis (hysterectomy, C-section, and oophorectomy, tubal ligation) laparoscopic bowel or solid organ resection except laparoscopic cholecystectomy ventral hernia repair with mesh Preoperative chronic opiate use for chronic pain defined as opiate usage at least 60 mg/day of morphine equivalent for = 3 months (as defined by International Association for the Study of Pain22) in the one year period prior to the bariatric surgery The American Society of Anesthesiologists (ASA) score > 3 History of hypersensitivity or adverse reaction to bupivacaine or narcotics Inability to speak English ventral hernia repair Cholecystectomy hiatal hernia repair with posterior cruroplasty extensive lysis of adhesions other procedures that mandate addition of \"trocar(s)\" or \"feeding tube\" Addition of trocar(s) or conversion of surgery to hand-assisted or open", "candidate_expression": "((<35 and > 60 kg/m2) AND (> 3) AND (Addition of) AND (American Society of Anesthesiologists (ASA) score) AND (BMI) AND (C-section) AND (Cholecystectomy) AND (Inability to walk) AND (Preoperative) AND (adverse reaction) AND (at least 60 mg/day of morphine equivalent) AND (bariatric surgery) AND (bed-bound) AND (bupivacaine) AND (chronic) AND (chronic pain) AND (common OB/GYN procedures) AND (conversion of surgery) AND (except) AND (extensive) AND (for = 3 months) AND (hand-assisted) AND (hiatal hernia) AND (hypersensitivity) AND (hysterectomy) AND (in the one year period prior to the bariatric surgery) AND (laparoscopic bowel resection) AND (laparoscopic cholecystectomy) AND (lysis of adhesions) AND (narcotics) AND (oophorectomy) AND (open) AND (open abdominal surgeries) AND (opiate) AND (pelvis) AND (posterior cruroplasty) AND (repair) AND (repair with mesh) AND (simple appendectomy) AND (solid organ resection) AND (surgery) AND (the bariatric surgery) AND (trocar) AND (tubal ligation) AND (ventral hernia) AND (wheelchair dependence))"}
{"candidate_id": "LLM04729", "doc_id": "NCT02692651_inc", "case_bucket": "other", "source_criterion": "Patients 18 years of age or older with >3 unformed stools/24 hours with positive stool test for C. difficile. Patients receiving = 1 high or medium risk antibiotic for treatment of an infection other than CDI, for an anticipated duration of = 5 days from the time of enrollment.", "candidate_expression": "((age or older 18 years) AND (stool test positive C. difficile) AND (unformed stools >3 24 hours))"}
{"candidate_id": "LLM04730", "doc_id": "NCT01770340_inc", "case_bucket": "or", "source_criterion": "Localized intermediate-risk or high-risk prostate cancer cT3 Gleason score = 7 (3+4 and/or 4+3) and/or PSA = 20 ng/ml intact preoperative erectile function with an IIEF = 21 (IIEF-6).", "candidate_expression": "((= 20 ng/ml) AND (= 21) AND (= 7) AND (Gleason score) AND (IIEF) AND (IIEF-6) AND (PSA) AND (cT3) AND (intact erectile function) AND (preoperative) AND (prostate cancer) AND ((high-risk) OR (intermediate-risk)) AND ((3+4) OR (4+3)))"}
{"candidate_id": "LLM04731", "doc_id": "NCT03099863_inc", "case_bucket": "or", "source_criterion": "Adult women at least 18 years of age Elective Female Pelvic Medicine and Reconstructive Surgery or Gynecologic Minimally Invasive surgeries including hysterectomy, suburethral sling, and pelvic organ prolapse repair that require cystoscopy.", "candidate_expression": "((Adult) AND (age at least 18 years) AND (cystoscopy require) AND (surgeries Gynecologic Minimally Invasive) AND (women) AND ((hysterectomy) OR (pelvic organ prolapse repair) OR (suburethral sling)) AND ((Medicine) OR (Reconstructive Surgery)))"}
{"candidate_id": "LLM04732", "doc_id": "NCT01932996_inc", "case_bucket": "other", "source_criterion": "Currently Homeless Smoked at least 100 cigarettes in lifetime AUDIT score of > or equal to 5, < or equal to 26 Aged 18 years or older Willing to attend study sessions and follow other study protocol", "candidate_expression": "((AUDIT score of > or equal to 5, < or equal to 26) AND (Aged 18 years or older) AND (Homeless) AND (Smoked at least 100 cigarettes) AND (Willing to attend study sessions and follow other study protocol))"}
{"candidate_id": "LLM04733", "doc_id": "NCT02607163_inc", "case_bucket": "or", "source_criterion": "the patients undergoing ascending, arch and/or proximal descending aorta surgery with cardiopulmonary bypass 20 - 100 yrs old", "candidate_expression": "((20 - 100 yrs) AND (cardiopulmonary bypass) AND (old) AND ((arch aorta surgery) OR (ascending aorta surgery) OR (proximal descending aorta surgery)))"}
{"candidate_id": "LLM04734", "doc_id": "NCT01895946_exc", "case_bucket": "or", "source_criterion": "Clinically significant abnormalities of glucose metabolism Spinal cord compression or brain metastases unless asymptomatic, treated and stable (not requiring steroids) Evidence of severe or uncontrolled systemic diseases, including active bleeding diatheses or active infections including hepatitis B, C and Human Immunodeficiency Virus (HIV) Evidence of clinically significant cardiac abnormalities, uncontrolled hypotension, left ventricular ejection fraction below the lower limit of normal for the site or experience of significant cardiac interventional procedures A bad reaction to AZD5363 or any drugs similar to it in structure or class", "candidate_expression": "((AZD5363) AND (Clinically significant) AND (abnormalities of glucose metabolism) AND (asymptomatic) AND (bad reaction to AZD5363) AND (below the lower limit of normal) AND (clinically significant) AND (not) AND (significant) AND (stable) AND (steroids) AND (systemic diseases) AND (treated) AND (unless) AND ((severe) OR (uncontrolled)) AND ((active bleeding diatheses) OR (active infections)) AND ((Human Immunodeficiency Virus (HIV)) OR (hepatitis B) OR (hepatitis C)) AND ((cardiac abnormalities) OR (cardiac interventional procedures) OR (left ventricular ejection fraction) OR (uncontrolled hypotension)) AND ((Spinal cord compression) OR (brain metastases)))"}
{"candidate_id": "LLM04735", "doc_id": "NCT03464552_exc", "case_bucket": "or", "source_criterion": "A known allergy to Celecoxib, aspirin or another NSAID. Active peptic ulceration or gastrointestinal bleeding. Inflammatory bowel disease. Congestive heart failure (NYHA II-IV). Established ischemic heart disease, peripheral arterial disease and/or cerebrovascular disease. History of neurologic deficit. Known hepatic or renal impairment. Pregnancy. Breast-feeding. Post-hysterectomy. Bleeding disorders. Drug abuse. Cervical and vaginal infection.", "candidate_expression": "((Bleeding disorders) AND (Breast-feeding) AND (Congestive heart failure) AND (Drug abuse) AND (Inflammatory bowel disease) AND (NYHA II-IV) AND (Pregnancy) AND (allergy) AND (hysterectomy Post) AND (neurologic deficit History) AND ((cerebrovascular disease) OR (ischemic heart disease) OR (peripheral arterial disease)) AND ((Celecoxib) OR (NSAID another) OR (aspirin)) AND ((hepatic impairment) OR (renal impairment)) AND ((Cervical infection) OR (vaginal infection)) AND ((gastrointestinal bleeding) OR (peptic ulceration)))"}
{"candidate_id": "LLM04736", "doc_id": "NCT03499639_inc", "case_bucket": "other", "source_criterion": "patients were 18 years old or more, naive to HCV treatment, HCV genotype 4, compensated liver disease.", "candidate_expression": "((HCV genotype 4) AND (liver disease compensated) AND (old 18 years old or more) AND NOT (HCV treatment))"}
{"candidate_id": "LLM04737", "doc_id": "NCT02225548_inc", "case_bucket": "other", "source_criterion": "Diagnosis of idiopathic Parkinson's disease that is optimally treated (motor fluctuations <20% of subject's awake time). Subjects may be on levodopa therapy but must be stable at the time of entry into the study Sexually active (i.e. =1 attempt/week) males, 40 - 64 years of age (inclusive) at time of screening Diagnosis of moderate erectile dysfunction (defined according to the NIH Consensus Development Panel on Impotence) for more than 6 months and demonstrating and incomplete response to tadalafil alone Subject demonstrating an IIEF-5 drug-free baseline score that is = 10 but = 16, and an IIEF-5 tadalafil-alone baseline score that is = 18 Subject in a stable heterosexual relationship for at least 6 months. (2) Subject motivated to seek treatment for erectile dysfunction. Subject with a total serum testosterone level = 300 ng/dL, with or without supplementation Hoehn and Yahr Scale score of 1 - 3 Patient able to consent and comply with protocol requirements", "candidate_expression": "((1 - 3) AND (40 - 64 years) AND (<20% of subject's awake time) AND (= 10 but = 16) AND (= 18) AND (= 300 ng/dL) AND (=1 attempt/week) AND (Hoehn and Yahr Scale score) AND (IIEF-5 drug-free baseline score) AND (IIEF-5 tadalafil-alone baseline score) AND (Patient able to consent and comply with protocol requirements) AND (Sexually active) AND (Subject motivated to seek treatment for erectile dysfunction) AND (age) AND (at least 6 months) AND (erectile dysfunction) AND (for more than 6 months) AND (heterosexual relationship) AND (idiopathic Parkinson's disease) AND (incomplete) AND (males) AND (moderate) AND (motor fluctuations) AND (response) AND (stable) AND (tadalafil) AND (total serum testosterone level) AND (treated) AND (treatment))"}
{"candidate_id": "LLM04738", "doc_id": "NCT02481518_exc", "case_bucket": "other", "source_criterion": "Prior treatment with cisplatin before randomization Uncontrolled concurrent disease Pregnancy", "candidate_expression": "((Pregnancy) AND (cisplatin before randomization) AND (concurrent disease Uncontrolled))"}
{"candidate_id": "LLM04739", "doc_id": "NCT02429765_exc", "case_bucket": "other", "source_criterion": "A diagnosis of sleep disordered breathing; Nocturnal oxygen therapy.", "candidate_expression": "((Nocturnal oxygen therapy) AND (sleep disordered breathing))"}
{"candidate_id": "LLM04740", "doc_id": "NCT03106389_exc", "case_bucket": "other", "source_criterion": "NA", "candidate_expression": "(EMPTY)"}
{"candidate_id": "LLM04741", "doc_id": "NCT02668978_exc", "case_bucket": "or", "source_criterion": "Traumatic pulmonary contusion or laceration Lung reduction surgery Planned removal of more than 10 lung lesions Pneumonectomy Known hypersensitivity to bovine protein Known hypersensitivity to Brilliant Blue FCF (E133) Presence of active infection", "candidate_expression": "((Brilliant Blue FCF (E133)) AND (Lung reduction surgery) AND (Planned) AND (Pneumonectomy) AND (Traumatic) AND (active infection) AND (bovine protein) AND (hypersensitivity) AND (lung lesions) AND (more than 10) AND (removal) AND ((laceration) OR (pulmonary contusion)))"}
{"candidate_id": "LLM04742", "doc_id": "NCT03067740_inc", "case_bucket": "other", "source_criterion": "Patients are of American Society of Anesthesiologists (ASA) physical status I and II, aged 8-14 years old, of both gender, with suspected acute appendicitis scheduled for laparoscopic appendicectomy.", "candidate_expression": "((8-14 years old) AND (ASA) AND (American Society of Anesthesiologists physical status) AND (I and II) AND (acute appendicitis) AND (aged) AND (both gender) AND (laparoscopic appendicectomy) AND (scheduled for) AND (suspected))"}
{"candidate_id": "LLM04743", "doc_id": "NCT02283996_exc", "case_bucket": "other", "source_criterion": "Non-English speaking patients Pregnant women (women of childbearing potential will be advised to undergo regular pregnancy testing) Patients who had previously undergone operative therapy for the condition", "candidate_expression": "((Patients who had previously undergone operative therapy for the condition) AND (Pregnant women (women of childbearing potential will be advised to undergo regular pregnancy testing)))"}
{"candidate_id": "LLM04744", "doc_id": "NCT02892968_exc", "case_bucket": "or", "source_criterion": "ED physicians who work casually (less than 0.25 Full Time Equivalent) ED Physicians who are routinely using U/S guided RA for hip fracture patients, or decline participation in the trial. Patients' age less than 65 years; Patients who are delirious on initial assessment by ED physician or severe dementia Patients with communication problems (critically ill, unconscious, language barrier despite use of secure telephone-based translation service) Patients with allergies to narcotics or local anesthetic; or anticoagulant use (e.g. warfarin, dabigatran, rivaroxaban). Patients with hip fractures not requiring surgery (e.g. greater trochanter avulsion) will also be excluded.", "candidate_expression": "((age less than 65 years) AND (communication problems) AND (greater trochanter avulsion) AND (hip fractures requiring surgery) AND (local anesthetic) AND (narcotics) AND (surgery) AND ((critically ill) OR (language barrier) OR (unconscious)) AND ((allergies) OR (anticoagulant)) AND ((dabigatran) OR (rivaroxaban) OR (warfarin)) AND ((delirious on initial assessment) OR (dementia severe)))"}
{"candidate_id": "LLM04745", "doc_id": "NCT03097068_inc", "case_bucket": "other", "source_criterion": "Diagnosis of diabetes mellitus Best corrected visual acuity 20/32 - 20/320 Diabetic macular edema involving the center of the macula Optical coherence tomography central subfield thickness of at least 250 microns", "candidate_expression": "((Best corrected visual acuity 20/32 - 20/320) AND (Diabetic macular edema center of the macula) AND (Optical coherence tomography central subfield thickness at least 250 microns) AND (diabetes mellitus))"}
{"candidate_id": "LLM04746", "doc_id": "NCT02437084_exc", "case_bucket": "or", "source_criterion": "Less than 30 yrs of age or > 65 yrs of age Any significant co-morbidities, such as active heart, kidney, or liver diseases, accelerated or malignant hypertension, heart failure, severe anemia.", "candidate_expression": "((> 65 yrs) AND (Less than 30 yrs) AND (active) AND (age) AND (co-morbidities) AND (significant) AND ((accelerated) OR (malignant)) AND ((diseases heart) OR (diseases kidney) OR (heart failure) OR (hypertension) OR (liver diseases) OR (severe anemia)))"}
{"candidate_id": "LLM04747", "doc_id": "NCT02782702_inc", "case_bucket": "or", "source_criterion": "Confirmed diagnosis (clinical and histological features) of Hailey Hailey or Darier diseases. Moderate to very severe lesions located in large folds Patient aged 18 ans or more Patient with health coverage Patient who have signed the consent form Patient proficient into filling out the questionnaires.", "candidate_expression": "((18 ans or more) AND (Darier disease) AND (Hailey Hailey disease) AND (Patient proficient into filling out the questionnaires.) AND (Patient who have signed the consent form) AND (aged) AND (health coverage) AND (histological) AND (lesions) AND (very severe))"}
{"candidate_id": "LLM04748", "doc_id": "NCT01884337_exc", "case_bucket": "or", "source_criterion": "Women who are pregnant or breastfeeding Known or suspected, acquired or bleeding or coagulation disorder in the subject or a first degree relative Active bleeding or at high risk for bleeding. Brain, spinal, ophthalmologic, or major surgery or trauma within the past 90 days other than the elective knee/hip surgery Active hepatobiliary disease Hemoglobin <9 g/dL Platelet count <100,000/mm3 Creatinine clearance <30 mL/min", "candidate_expression": "((<100,000/mm3) AND (<30 mL/min) AND (<9 g/dL) AND (Active) AND (Creatinine clearance) AND (Hemoglobin) AND (Platelet count) AND (Women) AND (at high risk for) AND (hepatobiliary disease) AND (other than) AND (within the past 90 days) AND ((first degree relative) OR (in the subject)) AND ((bleeding)) AND ((surgery) OR (trauma)) AND ((Brain) OR (major) OR (ophthalmologic) OR (spinal)) AND ((elective hip surgery) OR (elective knee surgery)) AND ((breastfeeding) OR (pregnant)) AND ((Known) OR (suspected)) AND ((acquired disorder) OR (bleeding disorder) OR (coagulation disorder)))"}
{"candidate_id": "LLM04749", "doc_id": "NCT00401245_exc", "case_bucket": "or", "source_criterion": "History of a seizure disorder other than a single childhood febrile seizure. History or presence of clinically important hepatic or renal disease or other medical disease. Presence or recent history of major depressive disorder, bipolar disorder, psychotic disorder, or generalized anxiety disorder requiring therapy.", "candidate_expression": "((History) AND (bipolar disorder) AND (childhood febrile seizure) AND (clinically important hepatic disease) AND (clinically important other medical disease) AND (clinically important renal disease) AND (generalized anxiety disorder) AND (history) AND (major depressive disorder) AND (other than) AND (psychotic disorder) AND (requiring therapy) AND (seizure disorder) AND (single))"}
{"candidate_id": "LLM04750", "doc_id": "NCT03536520_inc", "case_bucket": "or", "source_criterion": "Healthy men and women, age 40-75 yrs, without any disease and need of medication. Born, raised and currently living at low altitude (<800m). Written informed consent. Kyrgyz ethnicity", "candidate_expression": "((Written informed consent) AND (age 40-75 yr 40-75 yr) AND (men) AND (women) AND NOT (disease any) AND NOT (medication))"}
```
