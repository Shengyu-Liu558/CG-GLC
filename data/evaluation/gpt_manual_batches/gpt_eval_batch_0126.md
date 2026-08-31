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
{"candidate_id": "LLM03126", "doc_id": "NCT03117608_exc", "case_bucket": "or", "source_criterion": "Patients incapable to understanding and will; Patients participating in previous, concurrent or not, trials (ongoing or completed within three months); Patients surgically treated for the same defect within one year; Patients affected by malignancy; Patients affected by metabolic or thyroid disorders; Patients used to alcohol or drug (medication) abuse; Patients affected by synovitis; Varus or valgus misalignment exceeding 15°; Body Mass Index > 40; Patients with trauma within 6 months pre-operative.", "candidate_expression": "((Body Mass Index > 40) AND (Varus misalignment) AND (Varus misalignment exceeding 15°) AND (alcohol abuse) AND (drug abuse) AND (incapable to understanding) AND (malignancy) AND (medication abuse) AND (metabolic disorders) AND (operative) AND (surgically treated within one year) AND (synovitis) AND (the same defect) AND (thyroid disorders) AND (trauma within 6 months pre-operative) AND (trials participating in previous ongoing completed) AND (valgus misalignment) AND (valgus misalignment exceeding 15°) AND (will incapable to))"}
{"candidate_id": "LLM03127", "doc_id": "NCT02256943_exc", "case_bucket": "other", "source_criterion": "NA", "candidate_expression": "(EMPTY)"}
{"candidate_id": "LLM03128", "doc_id": "NCT02118467_inc", "case_bucket": "other", "source_criterion": "Age greater than or equal to 18 years old Requirement for vasoactive drugs via a central venous catheter for the treatment of shock. Shock will be defined as mean arterial pressure less than 70 mmHg or systolic blood pressure less than 100 mmHg despite administration of at least 1000 mL of crystalloid or 500 mL of colloid, unless there is an elevation in the central venous pressure to > 12 mmHg or in the pulmonary artery occlusion pressure to > 14 mmHg coupled with signs of tissue hypoperfusion (e.g. altered mental state, mottled skin, urine output < 0.5 mL/kg body weight for one hour, or a serum lactate level of > 2 mmol per liter).", "candidate_expression": "((Age greater than or equal to 18 years old) AND (central venous catheter) AND (mean arterial pressure less than 70 mmHg) AND (shock) AND (systolic blood pressure less than 100 mmHg) AND (vasoactive drugs))"}
{"candidate_id": "LLM03129", "doc_id": "NCT02600000_exc", "case_bucket": "or", "source_criterion": "Unstable angina; Myocardial infarction and heart surgery up to three months before the survey; Chronic respiratory diseases; Hemodynamic instability; Trauma recent face, nausea and vomiting. Orthopedic and neurological diseases that may preclude the achievement of the cardiopulmonary test and Cardiac Rehabilitation exercises; Psychological and / or cognitive impairments that restrict them to respond to questionnaires;", "candidate_expression": "((Chronic respiratory diseases) AND (Hemodynamic instability) AND (Myocardial infarction) AND (Orthopedic preclude the achievement of the cardiopulmonary test and Cardiac Rehabilitation exercises) AND (Psychological impairments restrict them to respond to questionnaires) AND (Trauma) AND (Unstable angina) AND (cognitive impairments restrict them to respond to questionnaires) AND (heart surgery) AND (nausea) AND (neurological diseases preclude the achievement of the cardiopulmonary test and Cardiac Rehabilitation exercises) AND (vomiting))"}
{"candidate_id": "LLM03130", "doc_id": "NCT03164304_exc", "case_bucket": "or", "source_criterion": "Women with Non-proteinuric hypertension severe renal impairment Myasthenia gravis High amount of magnesium in blood Low or high amount of calcium in blood Myocardial damage, diabetic coma, heart block", "candidate_expression": "((Myasthenia gravis) AND (Non-proteinuric hypertension) AND (Women) AND (calcium in blood) AND (magnesium in blood High amount) AND (renal impairment severe) AND ((Myocardial damage) OR (diabetic coma) OR (heart block)) AND ((Low amount) OR (high amount)))"}
{"candidate_id": "LLM03131", "doc_id": "NCT02607319_inc", "case_bucket": "or", "source_criterion": "History of three or more consecutively failed In Vitro Fertilization (IVF) cycles after embryo transfer. Normal uterine cavity (as assessed by hysteroscopy or HSG). Normal hormonal investigation: TSH, PRL, FBS. Normal acquired/inherited thrombophilia profile: LAC, ACA IgG/IgM, Prot S, Antithrombin III, beta-2 glycoprotein, Factors V, II, MTHFR. Normal semen analysis and mild/moderate male factor (Total motile sperm count > 5 million/ml and/or normal WHO morphology >20%. Patient provides written informed consent.", "candidate_expression": "((> 5 million/ml) AND (>20%) AND (ACA IgG) AND (ACA IgM) AND (Antithrombin III) AND (FBS) AND (Factors II) AND (Factors V) AND (IVF) AND (In Vitro Fertilization) AND (LAC) AND (MTHFR) AND (Normal) AND (PRL) AND (Patient provides written informed consent) AND (Prot S) AND (TSH) AND (after embryo transfer) AND (beta-2 glycoprotein) AND (consecutively failed) AND (embryo transfer) AND (hormonal investigation:) AND (male factor) AND (semen analysis) AND (three or more) AND (thrombophilia profile) AND (uterine cavity) AND ((HSG) OR (hysteroscopy)) AND ((mild) OR (moderate)) AND ((Total motile sperm count) OR (normal WHO morphology)))"}
{"candidate_id": "LLM03132", "doc_id": "NCT02621541_inc", "case_bucket": "or", "source_criterion": "suspicion of nonfunctional P-NET on primary CT (i.e hypervascularity) or MRI signed informed consent", "candidate_expression": "((MRI) AND (hypervascularity) AND (nonfunctional P-NET suspicion) AND (primary CT) AND (signed informed consent))"}
{"candidate_id": "LLM03133", "doc_id": "NCT03561753_inc", "case_bucket": "or", "source_criterion": "Newly diagnosed and untreated sputum smear positive tuberculosis patient Pulmonary lesion consistent with TB by radiological examination Positive sputum culture, identification of bacterial type confirmed Mycobacterium tuberculosis. MGIT drug sensitivity test (DST) results are sensitive of the first-line drugs (isoniazid, streptomycin, rifampicin and ethambutol). Age 18 years-65 years old Males or non-pregnant, non-nursing females Serum or plasma aminotransferases (AST, ALT) less than 3 times the upper limit of normal Serum or plasma total bilirubin less than or equal to 2.5 times the upper limit of normal Serum or plasma creatinine level less than or equal to 2 times the upper limit of normal Serum or plasma potassium level greater than or equal to 3.5 meq/L Hemoglobin level of 7.0 g/dL or greater Platelet count of 100,000/mm3 or greater For women of childbearing potential, a negative pregnancy test is required during screening Provides written informed consent Willingness and ability to attend scheduled follow-up visits and undergo study assessments.", "candidate_expression": "((ALT) AND (AST) AND (Age 18 years-65 years old) AND (Hemoglobin level 7.0 g/dL or greater) AND (MGIT drug sensitivity test (DST) sensitive of the first-line drugs (isoniazid, streptomycin, rifampicin and ethambutol)) AND (Males) AND (Mycobacterium tuberculosis bacterial type) AND (Platelet count 100,000/mm3 or greater) AND (Pulmonary lesion consistent with TB) AND (Serum aminotransferases) AND (TB) AND (ability to attend scheduled follow-up visits) AND (ability to undergo study assessments) AND (childbearing potential) AND (creatinine level less than or equal to 2 times the upper limit of normal Serum plasma) AND (ethambutol) AND (females) AND (first-line drugs) AND (isoniazid) AND (plasma aminotransferases) AND (potassium level greater than or equal to 3.5 meq/L Serum plasma) AND (pregnancy test negative during screening) AND (radiological examination) AND (rifampicin) AND (sputum culture Positive) AND (sputum smear positive Newly diagnosed untreated) AND (streptomycin) AND (to attend scheduled follow-up visits Willingness) AND (to undergo study assessments Willingness) AND (total bilirubin less than or equal to 2.5 times the upper limit of normal Serum plasma) AND (tuberculosis) AND (women) AND (written informed consent) AND NOT (pregnant) AND NOT (nursing))"}
{"candidate_id": "LLM03134", "doc_id": "NCT03511521_inc", "case_bucket": "or", "source_criterion": "Patients receiving once daily dosing of methylprednisolone or prednisone in a dose of 10 mg/day or greater Hyperglycemic (Glucose level > 126 mg/dL) Diabetic and nondiabetic patients Expected duration of hospital stay and time on steroids >= 3 days Patient of appropriate caregiver able to give Informed Consent", "candidate_expression": "((Diabetic) AND (Expected duration of hospital stay >= 3 days) AND (Glucose level > 126 mg/dL) AND (Hyperglycemic) AND (Patient of appropriate caregiver able to give Informed Consent) AND (methylprednisolone) AND (nondiabetic) AND (prednisone) AND (time on steroids >= 3 days))"}
{"candidate_id": "LLM03135", "doc_id": "NCT02944292_inc", "case_bucket": "other", "source_criterion": "Age 18 years or older Mechanical ventilation IAP between 12 and 20 mmHg in at least two consecutive measurements within 1-12 h Spontaneous breathing activity of at least 6 breaths/minute RASS score between 0 and -4 Physician-led sedation (if sedated; as opposed to nurse-led protocol)", "candidate_expression": "((Age 18 years or older) AND (IAP between 12 and 20 mmHg at least two consecutive measurements) AND (Mechanical ventilation) AND (RASS score between 0 and -4) AND (Spontaneous breathing activity at least 6 breaths/minute) AND (sedation Physician-led))"}
{"candidate_id": "LLM03136", "doc_id": "NCT03016741_inc", "case_bucket": "or", "source_criterion": "Have diagnosis of prostate cancer and have received treatment with GnRH agonist or antagonist therapy for at least 1 month prior to enrollment. Willing and able to complete survey questionnaires in English without assistance through the duration of the study. This stipulation is in place because not all of the proposed quality of life or cognitive tests are available or validated in other languages. Age = 18 years. Ability to understand and the willingness to sign a written informed consent document written in English that is approved by an institutional review board. Have either newly diagnosed metastatic hormone sensitive prostate cancer (mHSPC) or castration-resistant metastatic prostate cancer (mCRPC) and eligible to undergo treatment with abiraterone acetate (mHSPC or mCRPC) or enzalutamide (mCRPC) Patients may have received the following prior AR directed therapy prior to enrollment: bicalutamide, ketoconazole. Prior to enrollment, patients may have received treatment with abiraterone acetate or enzalutamide for no more than 14 days before completing baseline studies. Patients may have received chemotherapy for hormone-sensitive metastatic prostate cancer only, but it must not have lasted for more than 6 months. At least 12 months must have elapsed since completion of chemotherapy. Patients may have received prior definitive radiation therapy or surgery. At least 60 days must have elapsed since completion of definitive radiation therapy or surgery and patient must have only grade 2 or less adverse effects at the time of registration. Enrollment during palliative radiation of = 10 days, or radiation of = 10 days during the duration of the study is allowed. Patients must be able to take oral medication.", "candidate_expression": "((Age = 18 years) AND (abiraterone acetate) AND (adverse effects grade 2 or less at the time of registration) AND (chemotherapy) AND (chemotherapy lasted for more than 6 months At least 12 months must have elapsed since completion of chemotherapy) AND (definitive) AND (enzalutamide) AND (mCRPC) AND (mHSPC) AND (prostate cancer) AND (prostate cancer castration-resistant metastatic) AND (prostate cancer hormone-sensitive metastatic) AND (prostate cancer metastatic hormone sensitive) AND (treatment) AND (treatment for at least 1 month prior to enrollment) AND ((GnRH agonist) OR (GnRH antagonist)) AND ((mCRPC) OR (mHSPC)) AND ((radiation therapy) OR (surgery)))"}
{"candidate_id": "LLM03137", "doc_id": "NCT02667730_exc", "case_bucket": "or", "source_criterion": "Diagnosis of ankle fracture or ligament rupture Has planned release from the Canadian Armed Forces within one year; Documented restrictions on military duties Has known intolerance or documented adverse reaction to acetaminophen or naproxen or celecoxib Documented history of liver or kidney problems pregnant or breastfeeding", "candidate_expression": "((acetaminophen) AND (adverse reaction) AND (ankle fracture) AND (breastfeeding) AND (celecoxib) AND (intolerance) AND (kidney problems) AND (ligament rupture) AND (liver problems) AND (naproxen) AND (pregnant) AND (release from the Canadian Armed Forces within one year) AND (restrictions on military duties))"}
{"candidate_id": "LLM03138", "doc_id": "NCT02701881_inc", "case_bucket": "or", "source_criterion": "Age 19 years of older Moderate or severe claudication (Rutherford category 2 or 3) Critical limb ischemia (Rutherford category 4 or 5) Patients with signed informed consent Target lesion length =150 mm by angiographic estimation Stenosis of more than 50% in femoropopliteal artery At least one patent (less than 50 percent stenosed) tibioperoneal runoff vessel.", "candidate_expression": "((Age 19 years of older Moderate) AND (Rutherford category 2 or 3) AND (Rutherford category 4 or 5) AND (Stenosis more than 50% femoropopliteal artery) AND (Target lesion) AND (angiographic) AND (claudication severe) AND (length =150 mm) AND (limb ischemia Critical) AND (patent tibioperoneal runoff vessel At least one))"}
{"candidate_id": "LLM03139", "doc_id": "NCT02872935_exc", "case_bucket": "other", "source_criterion": "Non- English speakers Height < 4' 11\" BMI >40 Kg/ mm Antiemetic drug use in the 24 hours prior to cesarean delivery, Hypertensive diseases of pregnancy Chronic hypertension receiving antihypertensive treatment Any other physical or psychiatric condition that may impair their ability to cooperate with study data collection.", "candidate_expression": "((Antiemetic drug in the 24 hours prior to cesarean delivery) AND (Any other physical or psychiatric condition that may impair their ability to cooperate with study data collection.) AND (BMI >40 Kg/ mm) AND (Chronic hypertension) AND (Height < 4' 11\") AND (Hypertensive diseases of pregnancy) AND (Non- English speakers) AND (antihypertensive treatment) AND (cesarean delivery))"}
{"candidate_id": "LLM03140", "doc_id": "NCT03387059_exc", "case_bucket": "or", "source_criterion": "Clinically significant systemic disease (such as diabetes, metabolic syndrome, immunological diseases, diagnosed thrombophilia, porphyria, or any other medical condition requiring the use of low-molecular weight heparin therapy) Polycystic ovary syndrome (PCOS) according to Rotterdam Consensus Criteria (European Society of Human Reproduction and Embryology [ESHRE]/American Society for Reproductive Medicine [ASRM], 2003) Poor ovarian response (POR) according to the European Society of Human Reproduction and Embryology (ESHRE) Criteria RIF (repeated implantation failure), defined as greater than or equals to (>=) 2 previous failed embryo transfers Endometriosis III-IV stage or adenomyosis Clinically significant findings on exam or ultrasound, such as salpingitis, hydrosalpynx or evidence of ovarian cysts Known hypersensitivity to any of the components of the solution Known hypersensitivity to vaginal progesterone or its excipients Other protocol defined exclusion criteria could apply", "candidate_expression": "((Polycystic ovary syndrome (PCOS) Rotterdam Consensus Criteria European Society of Human Reproduction and Embryology [ESHRE]/American Society for Reproductive Medicine [ASRM], 2003) AND (Poor ovarian response (POR) European Society of Human Reproduction and Embryology (ESHRE) Criteria) AND (RIF (repeated implantation failure)) AND (components of the solution) AND (hypersensitivity) AND (low-molecular weight heparin) AND (previous failed embryo transfers greater than or equals to (>=) 2 III-IV stage) AND (systemic disease Clinically significant) AND ((Endometriosis) OR (adenomyosis)) AND ((exam) OR (ultrasound)) AND ((hydrosalpynx) OR (ovarian cysts evidence) OR (salpingitis)) AND ((diabetes) OR (diagnosed thrombophilia) OR (immunological diseases) OR (medical condition) OR (metabolic syndrome) OR (porphyria)) AND ((excipients) OR (vaginal progesterone)))"}
{"candidate_id": "LLM03141", "doc_id": "NCT03511521_exc", "case_bucket": "or", "source_criterion": "Patients with 2 or more doses of methylprednisolone/prednisone per day Steroids other than methylprednisolone or prednisone Pregnancy estimated glomerular filtration rate (eGFR) < 45 ml/min/1.73m2", "candidate_expression": "((Pregnancy) AND (Steroids) AND (estimated glomerular filtration rate (eGFR) < 45 ml/min/1.73m2) AND ((methylprednisolone) OR (prednisone)))"}
{"candidate_id": "LLM03142", "doc_id": "NCT02162433_exc", "case_bucket": "or", "source_criterion": "Known allergy or hypersensitivity reaction to dexmedetomidine Organ dysfunction (renal/hepatic failure or leukemia) Cardiac disease (congenital or acquired) Airway or thoracic malformation Cerebral palsy Hypotonia Need for premedication Current/recent upper respiratory infection (within four weeks prior to the surgery) Asthma Allergy or intolerance to clonidine Non-English speaking parents/patients.", "candidate_expression": "((Airway malformation) AND (Allergy) AND (Asthma) AND (Cardiac disease congenital acquired) AND (Cerebral palsy) AND (Hypotonia) AND (Non-English speaking parents) AND (Non-English speaking patients) AND (Organ dysfunction) AND (allergy) AND (clonidine) AND (dexmedetomidine) AND (hepatic failure) AND (hypersensitivity) AND (intolerance) AND (leukemia) AND (premedication Need for Current recent) AND (renal failure) AND (surgery) AND (thoracic malformation) AND (upper respiratory infection within four weeks prior to the surgery))"}
{"candidate_id": "LLM03143", "doc_id": "NCT02416765_exc", "case_bucket": "or", "source_criterion": "1. Clinically significant microvascular complications: nephropathy (estimated glomerular filtration rate below 40 ml/min), neuropathy (especially diagnosed gastroparesis) or severe proliferative retinopathy as judged by the investigator. 2. Recent (< 3 months) acute macrovascular event e.g. acute coronary syndrome or cardiac surgery. 3. Ongoing pregnancy. 4. Severe hypoglycemic episode within 1 month of screening. 5. Agents affecting gastric emptying (Motilium®, Prandase®, Victoza®, Byetta® and Symlin®) as well as oral anti-diabetic agents (Metformin, SGLT-2 inhibitors and DPP-4 inhibitors) if not at a stable dose for 3 months. Otherwise, these medications are acceptable and will be kept stable during the entire protocol. 6. Oral steroids unless patients present a low stable dose (e.g. 10 mg or less of prednisone per day or physiological doses, less than 35 mg/day, of hydrocortisone Cortef®). Inhale steroids at stable dose in the last month are acceptable. 7. Other serious medical illness likely to interfere with study participation or with the ability to complete the trial by the judgment of the investigator (e.g. unstable psychiatric condition). 8. Failure to comply with team's recommendations (e.g. not willing to change pump parameters, follow algorithm's suggestions, etc). 9. Living or planned travel outside Montreal (> 1h of driving) area during closed-loop procedures.", "candidate_expression": "((10 mg or less per day) AND (< 3 months) AND (Cortef) AND (Inhale steroids) AND (Ongoing) AND (Oral steroids) AND (Other medical illness) AND (Recent) AND (Severe) AND (acute macrovascular event) AND (as judged by the investigator) AND (below 40 ml/min) AND (by the judgment of the investigator) AND (closed-loop procedures) AND (during closed-loop procedures) AND (estimated glomerular filtration rate) AND (for 3 months) AND (gastroparesis) AND (hypoglycemic episode) AND (in the last month) AND (less than 35 mg/day) AND (low dose) AND (microvascular complications) AND (not) AND (physiological doses) AND (pregnancy) AND (psychiatric condition) AND (serious) AND (stable dose) AND (unless) AND (unstable) AND (within 1 month of screening) AND ((nephropathy) OR (neuropathy) OR (severe proliferative retinopathy)) AND ((acute coronary syndrome) OR (cardiac surgery)) AND ((Agents affecting gastric emptying) OR (oral anti-diabetic agents)) AND ((Byetta) OR (Motilium) OR (Prandase) OR (Symlin) OR (Victoza)) AND ((DPP-4 inhibitors) OR (Metformin) OR (SGLT-2 inhibitors)) AND ((hydrocortisone) OR (prednisone)))"}
{"candidate_id": "LLM03144", "doc_id": "NCT03187639_exc", "case_bucket": "or", "source_criterion": "Atrial fibrillation of new onset or when rate control has been difficult Known bigemini/trigeminy Prior CABG surgery Allergic to contrast Advanced renal impairment Significant valve disease (severe aortic stenosis or regurgitation; severe mitral regurgitation) Life expectancy <12 months Inclusion in another trial without prior agreement with CI", "candidate_expression": "((<12 months) AND (Advanced renal impairment) AND (Allergic) AND (CABG surgery) AND (Inclusion in another trial without prior agreement with CI) AND (Life expectancy) AND (Prior) AND (contrast) AND (mitral regurgitation) AND (new onset) AND (severe) AND (valve disease) AND ((Atrial fibrillation) OR (rate control has been difficult)) AND ((aortic stenosis) OR (regurgitation)) AND ((bigemini) OR (trigeminy)))"}
{"candidate_id": "LLM03145", "doc_id": "NCT01888965_exc", "case_bucket": "or", "source_criterion": "Women of child-bearing potential, who are biologically able to conceive, not employing two forms of highly effective contraception or who are pregnant. Women who are breast-feeding Fertile males unwilling to use contraception Patients with brain metastases or any history of brain metastases Patients who have undergone major surgery (e.g., intra-thoracic, -abdominal, or -pelvic) </= 4 weeks prior to starting study treatment or who have not recovered from such therapy Patients with a history of pulmonary embolism, or untreated deep vein thrombosis within the past 6 months Impairment of gastrointestinal (GI) function or GI disease that may significantly alter the absorption of dovitinib The subject has had another active malignancy within the past 5 years except for cervical cancer in situ, in situ carcinoma of the bladder or non-melanoma carcinoma of the skin. Patients who have received the last administration of an anticancer therapy including chemotherapy, immunotherapy, hormonal therapy and monoclonal antibodies </= 2 weeks prior to starting the study drug, or who have not recovered from the side effects of such therapy Cirrhosis, chronic active hepatitis or chronic persistent hepatitis Patients who are currently receiving prasugrel No concurrent use of isoniazid, labetolol, trovafloxacin, tolcapone, and felbamate No concurrent use of other investigational drugs or antineoplastic therapies. Patients with impaired cardiac function or clinically significant cardiac diseases.", "candidate_expression": "((</= 2 weeks prior to starting the study drug) AND (</= 4 weeks prior to starting study treatment) AND (Fertile) AND (Fertile males unwilling to use contraception) AND (No) AND (Women) AND (active malignancy) AND (biologically able to conceive) AND (breast-feeding) AND (child-bearing potential) AND (clinically significant) AND (except) AND (history) AND (major surgery) AND (males) AND (may significantly alter the absorption of dovitinib) AND (not) AND (prasugrel) AND (recovered from such therapy) AND (starting study treatment) AND (starting the study drug) AND (two) AND (untreated) AND (unwilling to use contraception) AND (within the past 5 years) AND (within the past 6 months) AND ((brain metastases)) AND ((major surgery) OR (recovered from such therapy)) AND ((intra -abdominal) OR (intra -pelvic) OR (intra-thoracic)) AND ((deep vein thrombosis) OR (pulmonary embolism)) AND ((GI disease) OR (Impairment of gastrointestinal (GI) function)) AND ((cervical cancer in situ) OR (in situ carcinoma of the bladder) OR (non-melanoma carcinoma of the skin)) AND ((anticancer therapy) OR (recovered from the side effects of such therapy)) AND ((chemotherapy) OR (hormonal therapy) OR (immunotherapy) OR (monoclonal antibodies)) AND ((highly effective contraception) OR (pregnant)) AND ((Cirrhosis) OR (chronic active hepatitis) OR (chronic persistent hepatitis)) AND ((felbamate) OR (isoniazid) OR (labetolol) OR (tolcapone) OR (trovafloxacin)) AND ((antineoplastic therapies) OR (other investigational drugs)) AND ((cardiac diseases) OR (impaired cardiac function)))"}
{"candidate_id": "LLM03146", "doc_id": "NCT02473809_inc", "case_bucket": "other", "source_criterion": "Informed consent Diagnosis of type 2 diabetes (HbA1c > 48 mmol/mol) Age older than 30 years", "candidate_expression": "((> 48 mmol/mol) AND (Age) AND (HbA1c) AND (Informed consent) AND (older than 30 years) AND (type 2 diabetes))"}
{"candidate_id": "LLM03147", "doc_id": "NCT03199560_exc", "case_bucket": "or", "source_criterion": "Women under the age of 18, Clinically positive axillary nodes Neoadjuvant therapy for current breast cancer diagnosis Women with previous SLNBx or axillary node dissection Pregnant women Women with previous radiation above the diaphragm, and below the neck", "candidate_expression": "((18 under) AND (Neoadjuvant therapy) AND (Pregnant women) AND (Women) AND (above the diaphragm) AND (age) AND (axillary nodes) AND (below the neck) AND (breast cancer) AND (positive) AND (previous) AND (radiation) AND ((SLNBx) OR (axillary node dissection)))"}
{"candidate_id": "LLM03148", "doc_id": "NCT03056391_inc", "case_bucket": "other", "source_criterion": "1. Patient age ≥ 12 years 2. Presence of P. knowlesi malaria, confirmed by positive blood smear with asexual forms of P. knowlesi. 3. Temperature >38C on admission or fever during the preceding 48 hours 4. Enrolled within 18 hours of commencing antimalarial treatment 5. Written informed consent from patient or attending relative able to and willing to give informed consent. Consent form and information sheets will be translated into Malay and copies provided to the patient.", "candidate_expression": "((>38C) AND (Enrolled) AND (P. knowlesi malaria) AND (Temperature) AND (Written informed consent from patient or attending relative able to and willing to give informed consent.) AND (age) AND (antimalarial treatment) AND (blood smear) AND (commencing antimalarial treatment) AND (positive) AND (with asexual forms of P. knowlesi) AND (within 18 hours) AND (≥ 12 years))"}
{"candidate_id": "LLM03149", "doc_id": "NCT02529475_inc", "case_bucket": "other", "source_criterion": "Major subjects of over 40 years (mean age of Meniere's disease 40 to 50 years) Informed consent signed Medical examination performed prior to participation in research Patients without history of inner ear disease Recipient of a French social security scheme", "candidate_expression": "((Medical examination) AND (history) AND (inner ear disease) AND (over 40 years) AND (prior to participation in research) AND (without) AND (years))"}
{"candidate_id": "LLM03150", "doc_id": "NCT03079141_exc", "case_bucket": "or", "source_criterion": "Any previous treatments for active CSC; Previous prescription of mineralocorticoid receptor antagonists, for cCSC or for other diseases; Current treatment with corticosteroids (topical or systemic), corticosteroid use within 3 months before possible start of trial treatment, or anticipated start of corticosteroid treatment within the first 2 years from the start of the trial period; Evidence of another diagnosis that can explain serous SRF or visual loss; Best-corrected visual acuity < 20/200 (Snellen equivalent); Profound chorioretinal atrophy in central macular area on ophthalmoscopy and OCT; Myopia > 6D; Visual loss and/or serous detachment on OCT < 6 weeks; Continuous and/or progressive visual loss > 18 months or serous detachment on OCT > 18 months; No hyperfluorescence on ICGA; Intraretinal edema on OCT; (relative) Contraindications for FA or ICGA; (relative) Contraindications for photodynamic treatment (pregnancy, porphyria, severely disturbed liver function). Pregnancy will not be routinely tested in female patients, but the possibility of pregnancy will be discussed during screening (relative) Known contraindications for initiation of eplerenone treatment (hyperkalemia, abnormal renal clearance, severe hepatic insufficiency (Child-Pugh C), type 2 diabetes mellitus with microalbuminuria, concomitant use of potassium supplements, potassium-sparing diuretics, strong CYP3A4 inhibitors, or the combination of an ACE-inhibitor and an angiotensin receptor blocking agent). Pregnancy will not be routinely tested in female patients, but the possibility of pregnancy will be discussed during screening; Soft drusen in treated eye or fellow eye, signs of choroidal neovascularization on ophthalmoscopy and/or FA/ICGA of the study eye.", "candidate_expression": "((< 20/200) AND (< 6 weeks) AND (> 18 months) AND (> 6D) AND (ACE-inhibitor) AND (Best-corrected visual acuity) AND (C) AND (CSC) AND (Child-Pugh) AND (Continuous) AND (Contraindications) AND (Current) AND (FA) AND (ICGA) AND (Intraretinal edema) AND (Myopia) AND (No) AND (OCT) AND (Previous) AND (Profound) AND (Soft drusen) AND (Visual loss) AND (abnormal) AND (abnormal renal clearance) AND (active) AND (angiotensin receptor blocking agent) AND (anticipated) AND (cCSC) AND (central macular area) AND (chorioretinal atrophy) AND (choroidal neovascularization) AND (concomitant) AND (contraindications) AND (corticosteroid treatment) AND (corticosteroid use) AND (corticosteroids) AND (disturbed liver function) AND (eplerenone) AND (fellow eye) AND (hyperfluorescence) AND (hyperkalemia) AND (microalbuminuria) AND (mineralocorticoid receptor antagonists) AND (ophthalmoscopy) AND (other diseases) AND (photodynamic treatment) AND (porphyria) AND (possible start of trial treatment) AND (potassium supplements) AND (potassium-sparing diuretics) AND (pregnancy) AND (previous) AND (progressive) AND (renal clearance) AND (serous detachment) AND (severe hepatic insufficiency) AND (severely) AND (strong CYP3A4 inhibitors) AND (study eye) AND (systemic) AND (the first 2 years from the start of the trial period) AND (topical) AND (treated eye) AND (treatments) AND (type 2 diabetes mellitus) AND (visual loss) AND (within 3 months before possible start of trial treatment) AND (within the first 2 years from the start of the trial period))"}
```
