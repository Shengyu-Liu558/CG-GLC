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
{"candidate_id": "LLM07676", "doc_id": "NCT02951832_inc", "case_bucket": "or", "source_criterion": "Women aged 20-49; Having a regular menstrual cycle of which the menstrual period is between day 3-7, and the period between day 25-35; Excluding internal and surgical disease (after having variety of physical examination such as electrocardiogram/hepatic and renal function/blood routine and urine routine).", "candidate_expression": "((Women) AND (aged 20-49) AND (internal disease) AND (menstrual period) AND (regular menstrual cycle) AND (surgical disease) AND ((between day 25-35) OR (between day 3-7)))"}
{"candidate_id": "LLM07677", "doc_id": "NCT01391780_exc", "case_bucket": "or", "source_criterion": "neurological diseases previous pelvic surgeries diabetes cognitive difficulties vaginal and urinary infection", "candidate_expression": "((cognitive difficulties) AND (diabetes) AND (neurological diseases) AND (pelvic surgeries previous) AND ((infection vaginal) OR (urinary infection)))"}
{"candidate_id": "LLM07678", "doc_id": "NCT03225469_exc", "case_bucket": "or", "source_criterion": "1. History of colorectal surgery 2. Suspected or known digestive tract obstruction, stricture, or perforation 3. Serious status of illness, such as severe renal failure whose creatinine clearance<30 ml/min, New York Heart Association grade III or grade IV congestive heart failure, or hemodynamic instability, etc. 4. Incapable of completing bowel preparation，such as dysphagia, allergy to purgatives, or impaired mental status, etc. 5. Pregnancy or breastfeeding 6. Incomplete colonoscopy due to causes except poor bowel preparation 7. Unable to give informed consent 8. Have participated in the study before.", "candidate_expression": "((<30 ml/min) AND (History) AND (Incapable of completing bowel preparation) AND (Incomplete) AND (New York Heart Association) AND (Pregnancy) AND (Serious status of illness) AND (allergy) AND (breastfeeding) AND (colonoscopy) AND (colorectal surgery) AND (congestive heart failure) AND (creatinine clearance) AND (digestive tract obstruction) AND (digestive tract perforation) AND (digestive tract stricture) AND (dysphagia) AND (except) AND (grade III or grade IV) AND (hemodynamic instability) AND (impaired mental status) AND (informed consent) AND (poor bowel preparation) AND (purgatives) AND (renal failure) AND (severe))"}
{"candidate_id": "LLM07679", "doc_id": "NCT03260790_inc", "case_bucket": "other", "source_criterion": "Diagnosis of asthma", "candidate_expression": "(asthma)"}
{"candidate_id": "LLM07680", "doc_id": "NCT03241368_exc", "case_bucket": "or", "source_criterion": "Subject has indeterminate, ulcerative, antibiotic-associated colitis. Subject has stool positive for ova and parasite and for Clostridium difficule toxins within 3 months prior to enrollment. Subject with other known infectious cause of abdominal symptoms. Subject with clinical evidence of renal disease with the past 6 months, defined as estimated glomerular filtration rate (GFR) outside the normal reference range. Subject with known history of intestinal obstruction or current obstructive symptoms, such as severe abdominal pain with accompanying nausea or vomiting, based on investigator judgment. Subject with a diagnosis of gastroparesis or small bowel or large bowel dysmotility. Subjects with a history of small bowel or colonic resection. Subject with any current condition believed to have an increased risk of capsule retention such as suspected or known bowel obstruction, stricture, or fistula. Subject has used non-steroidal anti-inflammatory drugs including aspirin, two times per week, during the 4 weeks preceding enrollment. Low dose aspirin regimens (< 100 mg daily) are acceptable and not exclusionary. Subject suffers from any condition, such as swallowing problems, that precludes compliance with study and/or device instructions. Subject with cardiac pacemaker or other implanted electromedical device. Subject has an allergy or other known contraindication to the medications used in the study. Subject is pregnant (documented by a positive pregnancy test) or is actively breast-feeding. Subject is considered to be a part of a vulnerable population (eg. prisoners or those without sufficient mental capacity). Subject has a known contraindication to MRE or IC. Subject has participated in a drug or device research study within 30 days of enrollment that may interfere with the subject's safety or ability to participate in the study. Subject has any medical condition that would make it unsafe for them to participate, per Investigator's descretion", "candidate_expression": "((Subject has participated in a drug or device research study within 30 days of enrollment that may interfere with the subject's safety or ability to participate in the study.) AND (aspirin) AND (aspirin Low dose) AND (colitis indeterminate ulcerative antibiotic-associated) AND (condition) AND (contraindication) AND (estimated glomerular filtration rate (GFR) outside) AND (history) AND (medications used in the study) AND (non-steroidal anti-inflammatory drugs two times per week during the 4 weeks preceding) AND (part of a vulnerable population) AND (pregnancy test positive actively) AND (renal disease with the past 6 months) AND (severe abdominal pain) AND (stool positive for ova parasite positive for Clostridium difficule toxins positive for within 3 months prior) AND (swallowing problems) AND ((intestinal obstruction history) OR (obstructive symptoms current)) AND ((nausea) OR (vomiting)) AND ((gastroparesis) OR (large bowel dysmotility) OR (small bowel)) AND ((colonic resection) OR (small bowel resection)) AND ((compliance with device instructions) OR (compliance with study)) AND ((cardiac pacemaker) OR (implanted electromedical device)) AND ((allergy) OR (contraindication)) AND ((breast-feeding actively) OR (pregnant)) AND ((prisoners) OR (without sufficient mental capacity)) AND ((IC) OR (MRE)))"}
{"candidate_id": "LLM07681", "doc_id": "NCT03360981_inc", "case_bucket": "or", "source_criterion": "patients aged >18, <75, left ventricle ejection fraction (LVEF) >50%, multivessel coronary disease detected by coronarography, indication to receive a CABG, stable CAD. All diabetics and non diabetics.", "candidate_expression": "((LVEF) AND (multivessel coronary disease) AND ((CABG indication to receive) OR (CAD stable) OR (aged >18, <75) OR (coronarography) OR (diabetics) OR (left ventricle ejection fraction >50%) OR (non diabetics)))"}
{"candidate_id": "LLM07682", "doc_id": "NCT02973035_inc", "case_bucket": "or", "source_criterion": "Controlled hypertension: systolic BP < 150 and diastolic BP < 90 mmHg in persons aged 60 years or older, systolic BP < 140 and diastolic BP < 90 mmHg in persons 40 through 59 years according to the JNC 8th guideline Evidence of diastolic dysfunction showing E/E' > 10 The patient agrees to the study protocol and the schedule of clinical and echocardiographic follow-up, and provides informed, written consent, as approved by the appropriate Institutional Review Board/Ethical Committee of the respective clinical site", "candidate_expression": "((E/E' > 10) AND (The patient agrees to the study protocol and the schedule of clinical and echocardiographic follow-up, and provides informed, written consent, as approved by the appropriate Institutional Review Board/Ethical Committee of the respective clinical site) AND (aged 60 years or older) AND (diastolic BP < 90 mmHg) AND (diastolic dysfunction) AND (hypertension Controlled JNC 8th guideline) AND (systolic BP < 140) AND (systolic BP < 150) AND (years 40 through 59))"}
{"candidate_id": "LLM07683", "doc_id": "NCT03241368_inc", "case_bucket": "or", "source_criterion": "Subject has provided informed consent. Subject is ≥ 18 years of age Subject is willing and able to comply with all aspects of treatment and evaluation schedule. Subject has known CD and a recent history (within last 2 years) of mucosal disease (diagnosis based on radiologic, endoscopic, or histological evidence).", "candidate_expression": "((age ≥ 18 years) AND (endoscopic evidence) AND (histological evidence) AND (mucosal disease recent history) AND (radiologic evidence))"}
{"candidate_id": "LLM07684", "doc_id": "NCT03208998_inc", "case_bucket": "or", "source_criterion": "HBsAg and HBeAg positive for more than 6 months, HBV DNA detectable with ALT level abnormal lasted for three months and at least time190 IU/L or liver puncture biopsy demonstrated apparent inflammation, never treated before enrolled.", "candidate_expression": "((190 IU/L) AND (ALT level) AND (abnormal) AND (at least time) AND (before enrolled) AND (enrolled) AND (for more than 6 months) AND (inflammation) AND (lasted for three months) AND (never) AND (treated) AND ((HBV DNA detectable) OR (HBeAg positive) OR (HBsAg positive) OR (liver puncture biopsy)))"}
{"candidate_id": "LLM07685", "doc_id": "NCT02205931_exc", "case_bucket": "or", "source_criterion": "Age <1m or > 24 months of age No secure diagnosis of epilepsy < 4 seizures/week on average in baseline period Trial of < 2 AEDs Continues on corticosteroids in previous 3 months prior to randomisation Metabolic disease contraindicating use of the ketogenic diet e.g. pyruvate carboxylase deficiency, MCAD from previous medical investigation and screening at baseline. Progressive neurological disease Severe gastroesophageal reflux Previous treatment with the ketogenic diet Concurrent participation in another clinical trial of an investigational medicinal product. Patients who are prescribed AEDs not listed in the trial IMPs", "candidate_expression": "((< 2) AND (< 4 /week) AND (<1m or > 24 months of age) AND (AEDs) AND (Age) AND (Concurrent participation in another clinical trial of an investigational medicinal product) AND (Metabolic disease) AND (No) AND (Previous) AND (Progressive) AND (Severe) AND (contraindicating) AND (corticosteroids) AND (epilepsy) AND (gastroesophageal reflux) AND (ketogenic diet) AND (neurological disease) AND (previous 3 months prior to randomisation) AND (randomisation) AND (seizures) AND ((MCAD) OR (pyruvate carboxylase deficiency,)))"}
{"candidate_id": "LLM07686", "doc_id": "NCT02613039_exc", "case_bucket": "or", "source_criterion": "Participation in another clinical trial. Known or suspected (or history of) malignancy or chronic illness. Serious organic or mental disease diagnosed by a psychiatrist (e.g., major depression currently treated with antidepressant medication) suspected on the basis of the medical history and/or clinical examination. Conditions that may affect the compliance to the study. Contraindications to therapy with the study drug or hypersensitivity to the study drug (active ingredient or excipients of the formulation).", "candidate_expression": "((Conditions that may affect the compliance to the study.) AND (Contraindications to therapy with the study drug or hypersensitivity to the study drug (active ingredient or excipients of the formulation).) AND (antidepressant medication) AND (chronic illness) AND (clinical examination) AND (history of Known suspected) AND (major depression suspected) AND (malignancy) AND (medical history) AND (mental disease) AND (organic disease) AND (treated currently))"}
{"candidate_id": "LLM07687", "doc_id": "NCT03355157_inc", "case_bucket": "or", "source_criterion": "Written informed consent prior to beginning specific protocol procedures, including expected cooperation of the patients for the treatment and follow-up, willingness and ability to complete collection of data via wearable device and study mobile must be obtained and documented according to the local regulatory requirements. Female or male patients. Age = 18 years old. Metastatic invasive hormone receptor positive and HER2 negative breast cancer (histologically confirmed). Patients who in the opinion of the treating physician are candidates suitable for randomization for mono-chemotherapy treatment, that has either an approved label in Europe and/or is supported by guidelines for the treatment of first-line advanced BC, which are based on evidence on safety and efficacy in this setting. Symptomatic or asymptomatic metastatic breast cancer. Resolution of all acute toxic effects of prior anti-cancer therapy or surgical procedures to NCI CTCAE version 4.0 grade = 1 (except alopecia or other toxicities not considered a safety risk for the patient at investigator's discretion). Life-expectancy > 6 months. For female patients: The patients need to be either A) of non-childbearing potential (documented postmenopausal or post hysterectomy) B) childbearing potential with negative serum or urinary pregnancy test (in this case patients need to use highly effective non-hormonal contraceptive methods).", "candidate_expression": "((= 18 years old) AND (> 6 months) AND (Age) AND (HER2 negative) AND (Life-expectancy) AND (Metastatic) AND (NCI CTCAE version 4.0) AND (Resolution) AND (acute toxic effects) AND (alopecia) AND (breast cancer) AND (except) AND (grade = 1) AND (hormone receptor positive) AND (invasive) AND (metastatic breast cancer) AND (or female patients: The patients need to be either A) of non-childbearing potential (documented postmenopausal or post hysterectomy) B) childbearing potential with negative serum or urinary pregnancy test (in this case patients need to use highly effective non-hormonal contraceptive methods).) AND (prior) AND ((Symptomatic) OR (asymptomatic)) AND ((Female) OR (male)) AND ((anti-cancer therapy) OR (surgical procedure)))"}
{"candidate_id": "LLM07688", "doc_id": "NCT02862314_inc", "case_bucket": "other", "source_criterion": "aged 18 or older, have undergone oro-tracheal intubation for a coma (Glasgow Coma Score below or equal to 8), with mechanical ventilation initiated in the first 48 hours following hospital admission", "candidate_expression": "((Glasgow Coma Score below or equal to 8)) AND (aged 18 or older) AND (coma) AND (mechanical ventilation first 48 hours following hospital admission) AND (oro-tracheal intubation))"}
{"candidate_id": "LLM07689", "doc_id": "NCT02678663_inc", "case_bucket": "other", "source_criterion": "Subjects over the age of 18 years who agree informed consent and who have at least one polyp of eligible size (6-10mm)", "candidate_expression": "((age 18 years over) AND (agree informed consent) AND (polyp at least one eligible size 6-10mm))"}
{"candidate_id": "LLM07690", "doc_id": "NCT01410890_inc", "case_bucket": "or", "source_criterion": "The patient and/or the patient's parent/legal guardian is willing and able to provide signed informed consent. The patient has a confirmed GAA enzyme deficiency from skin, blood, or muscle tissue and/or 2 confirmed GAA gene mutations. Infant and toddler Pompe disease patients can be included in the study only under condition (minimal body weight) that the trial-related blood loss (including any losses in the maneuver) will not exceed 3 percent of the total blood volume during a period of 4 weeks and will not exceed 1 percent at any single time. The patient, if female and of childbearing potential, must have a negative pregnancy test (urine beta-human chorionic gonadotropin) at screening. Note: All female patients of childbearing potential and sexually mature males must agree to use a medically accepted method of contraception throughout the study. For patients previously treated with alglucosidase alfa the patient has received alglucosidase alfa for at least 6 months.", "candidate_expression": "((GAA enzyme deficiency) AND (GAA gene mutations 2) AND (Pompe disease) AND (The patient and/or the patient's parent/legal guardian is willing and able to provide signed informed consent) AND (The patient, if female and of childbearing potential, must have a negative pregnancy test (urine beta-human chorionic gonadotropin) at screening. Note: All female patients of childbearing potential and sexually mature males must agree to use a medically accepted method of contraception throughout the study) AND (alglucosidase alfa for at least 6 months) AND ((Infant) OR (toddler)) AND ((blood) OR (muscle tissue) OR (skin)))"}
{"candidate_id": "LLM07691", "doc_id": "NCT01911650_inc", "case_bucket": "or", "source_criterion": "1. age 18-65 years, inclusive 2. diagnosis of moderate to severe AT, confirmed by Dr. Wilson using clinical symptoms and exam findings consistent with chronic AT (>6 month duration) - which includes pain while palpating the intratendinous swelling part of the Achilles tendon and relief of pain when tendon placed under tension - and pre-procedure US 3. self-reported AT-related pain for at least 6 months and VAS (Visual Analog Scale) pain >5 (0-10 scale) 4. self-reported failure of eccentric exercise protocol (at least 75% completion) 5. self-reported failure of at least 2 of the 3 most common treatments for AT (NSAIDS, rest/ice or taping) 6. patient considered surgery but decided to wait and/or refused surgery -", "candidate_expression": "((0-10 scale) AND (18-65 years, inclusive) AND (>5) AND (>6 month duration) AND (AT) AND (AT-related pain) AND (NSAIDS) AND (VAS (Visual Analog Scale) pain) AND (age) AND (at least 75%) AND (chronic AT) AND (failure of at least 2 of the 3 most common treatments for AT) AND (failure of eccentric exercise protocol) AND (for at least 6 months) AND (ice) AND (moderate to severe) AND (pain while palpating the intratendinous swelling part of the Achilles tendon) AND (relief of pain when tendon placed under tension) AND (rest) AND (self-reported) AND (surgery) AND (taping))"}
{"candidate_id": "LLM07692", "doc_id": "NCT01942915_exc", "case_bucket": "other", "source_criterion": "1. Patients with C class by child-pugh score 2. Patients in the acute phase of severe hepatitis 3. Patients have been diagnosed with cancer of the liver 4. Patients with severe cardiopulmonary cerebral disease, and in the failure state 5. Patients in Highly allergic constitution 6. Patients with moderately severe mental disease", "candidate_expression": "((Highly allergic constitution) AND (cancer of the liver) AND (cardiopulmonary cerebral disease severe) AND (child-pugh score C class) AND (mental disease moderately severe) AND (severe hepatitis acute phase))"}
{"candidate_id": "LLM07693", "doc_id": "NCT03138577_exc", "case_bucket": "or", "source_criterion": "Patient refusal for supraclavicular block Inability to give informed consent Allergy to local anesthetics Hemidiaphragmatic dysfunction, suspected or known PNP Neuromuscular disease Obstructive or restrictive pulmonary disease Medical or anatomic contraindication to supraclavicular blockade as judged by clinician Pregnancy", "candidate_expression": "((Allergy) AND (Hemidiaphragmatic dysfunction suspected) AND (Inability to give informed consent) AND (Neuromuscular disease) AND (Obstructive pulmonary disease Medical anatomic) AND (PNP known) AND (Patient refusal) AND (Pregnancy) AND (contraindication) AND (local anesthetics) AND (restrictive pulmonary disease) AND (supraclavicular block) AND (supraclavicular blockade))"}
{"candidate_id": "LLM07694", "doc_id": "NCT02543710_inc", "case_bucket": "or", "source_criterion": "All patients referred to a participating research centre with suspicion of or confirmed endometrial cancer. Patients with endometrial or epithelial ovarian cancer who following routine clinical guidelines are offered weekly taxane (paclitaxel) treatment. This will often be a third or fourth line treatment, i.e. patients with advanced disease. Technical possibility to obtain a new tissue biopsy to determine stathmin level in the tumour recurrence.", "candidate_expression": "((endometrial cancer) AND (endometrial ovarian cancer) AND (epithelial ovarian cancer) AND (paclitaxel) AND (participating research centre suspicion of confirmed) AND (taxane weekly) AND (tissue biopsy Technical possibility to obtain) AND (treatment) AND (tumour recurrence))"}
{"candidate_id": "LLM07695", "doc_id": "NCT02430740_exc", "case_bucket": "other", "source_criterion": "polycystic ovaries untreated thyroid pathology hypogonadotropic hypogonadism untreaed hyperprolactinemia study drug hypersensitivity previous OHSS unilateral ovariectomy genital malformation BMI>40", "candidate_expression": "((>40) AND (BMI) AND (OHSS) AND (genital malformation) AND (hyperprolactinemia) AND (hypersensitivity) AND (hypogonadotropic hypogonadism) AND (ovariectomy) AND (polycystic ovaries) AND (previous) AND (study drug) AND (thyroid pathology) AND (unilateral) AND (untreaed) AND (untreated))"}
{"candidate_id": "LLM07696", "doc_id": "NCT02156999_inc", "case_bucket": "other", "source_criterion": "Osteoporosis", "candidate_expression": "(Osteoporosis)"}
{"candidate_id": "LLM07697", "doc_id": "NCT02802644_exc", "case_bucket": "or", "source_criterion": "Left main disease Known hypersensitivity or contraindication to any of the following medications: Heparin, aspirin, clopidogrel, sirolimus, siptagliptin and statin Congestive heart failure (patients with LVEF <30% or cardiogenic shock) Uncontrolled myocardial ischemia (repeated chest pain or dyspnea after revascularization) Uncontrolled ventricular arrhythmia History of malignancy with chemotherapy Serious hematologic disease (e.g. CML, MDS) Current infectious disease needs antibiotics therapy Creatinine level >1.5 mg/dL or dependence on dialysis Other severe concurrent illness (e.g. active infection, malignancy). Life expectancy of less than one year Pregnancy or women with potential childbearing Type I DM Treatment with insulin History of pancreatitis Who cannot read the informed consent form (e.g. illiteracy, foreigner)", "candidate_expression": "((<30%) AND (>1.5 mg/dL) AND (Congestive heart failure) AND (Left main disease) AND (Pregnancy or women with potential childbearing) AND (Serious) AND (Type I DM) AND (Uncontrolled) AND (Who cannot read the informed consent form (e.g. illiteracy, foreigner)) AND (after revascularization) AND (antibiotics) AND (chemotherapy) AND (concurrent) AND (hematologic disease) AND (ife expectancy) AND (illness) AND (infectious disease) AND (insulin) AND (less than one year) AND (malignancy) AND (myocardial ischemia) AND (pancreatitis) AND (repeated) AND (revascularization) AND (severe) AND (ventricular arrhythmia) AND ((LVEF) OR (cardiogenic shock)) AND ((chest pain) OR (dyspnea)) AND ((contraindication) OR (hypersensitivity)) AND ((CML) OR (MDS)) AND ((Creatinine level) OR (dialysis)) AND ((Heparin) OR (aspirin) OR (clopidogrel) OR (siptagliptin) OR (sirolimus) OR (statin)) AND ((active infection) OR (malignancy)))"}
{"candidate_id": "LLM07698", "doc_id": "NCT02256943_inc", "case_bucket": "or", "source_criterion": "Healthy Male >7 Metabolic Equivalents Written informed consent Chronic pain syndrome Drug abuse Alcohol abuse Suspicion of neurologic dysfunction at tested sites Ongoing treatment with antidepressants Ongoing treatment with analgesics Pretreatment with any CYP3A inducers or inhibitors Known allergy to tested drugs Elevated eye pressure Obstructive uropathy Heart disease Pulmonary disease Neurological disease Psychiatric illness", "candidate_expression": "((Alcohol abuse) AND (Chronic pain syndrome) AND (Drug abuse) AND (Elevated eye pressure) AND (Healthy) AND (Heart disease) AND (Male) AND (Metabolic Equivalents >7) AND (Neurological disease) AND (Obstructive uropathy) AND (Pretreatment) AND (Psychiatric illness) AND (Pulmonary disease) AND (Written informed consent) AND (allergy) AND (analgesics) AND (antidepressants) AND (neurologic dysfunction Suspicion tested sites) AND (tested drugs) AND (treatment Ongoing) AND ((CYP3A inducers) OR (CYP3A inhibitors)))"}
{"candidate_id": "LLM07699", "doc_id": "NCT02957877_inc", "case_bucket": "other", "source_criterion": "Prevalent NHHD patients who have received >1 year dialysis with unfractionated heparin as anticoagulant Age >= 18 Informed consent available", "candidate_expression": "((Age >= 18) AND (NHHD) AND (anticoagulant) AND (dialysis >1 year) AND (unfractionated heparin))"}
{"candidate_id": "LLM07700", "doc_id": "NCT02590653_exc", "case_bucket": "other", "source_criterion": "NA", "candidate_expression": "(EMPTY)"}
```
