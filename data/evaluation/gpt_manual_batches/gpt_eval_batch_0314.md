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
{"candidate_id": "LLM07826", "doc_id": "NCT02481518_exc", "case_bucket": "other", "source_criterion": "Prior treatment with cisplatin before randomization Uncontrolled concurrent disease Pregnancy", "candidate_expression": "((Pregnancy) AND (Uncontrolled) AND (before randomization) AND (cisplatin) AND (concurrent disease) AND (randomization))"}
{"candidate_id": "LLM07827", "doc_id": "NCT00319748_inc", "case_bucket": "or", "source_criterion": "Adequate performance status: Breast - Karnofsky score > 50; Ovarian, endometrial or cervical - Gynecologic Oncology Group (GOG) performance score ≤2 If female and of childbearing potential, are willing to use adequate contraception (hormonal, barrier method, abstinence) prior to study entry and for the duration of study participation. Normal organ function within 14 days of study entry Diagnosis of one of the following malignancies: Metastatic breast cancer (BR) Metastatic ovarian cancer (OV) Metastatic endometrial cancer (EM) Metastatic cervical cancer (CX) Measurable metastatic disease (>1cm) in at least one site other than bone-only Progression on or failure to respond to at least one previous chemotherapy regimen for metastatic disease Progression on prior therapy with a hormonal agent if estrogen receptor or progesterone receptor positive, and/or with trastuzumab if HER2-neu positive. If patient has progressed through hormone or trastuzumab therapy only, must have received one chemotherapy regimen. Measurable metastatic disease as defined by Response Evaluation Criteria in Solid Tumors (RECIST) Primary tumor must have been diagnosed histologically as either epithelial ovarian cancer, fallopian tube cancer, or primary peritoneal cancer (not borderline or low malignant potential epithelial carcinoma). Subjects must have failed at least two previous chemotherapy regimens. Paclitaxel must have been a component of one or both regimens and cisplatin or carboplatin must have been a component of one or both regimens. Measurable metastatic disease Histologically proven recurrent or persistent endometrial cancer that is not amenable to curative treatment with surgery and/or radiation therapy AND has failed 2 previous treatment regimens Measurable metastatic disease Histologically proven recurrent or persistent squamous cell carcinoma, adenosquamous carcinoma, or adenocarcinoma of the cervix that is not amenable to curative treatment with surgery and/or radiation therapy AND has failed 2 previous treatment regimens.", "candidate_expression": "((Breast - Karnofsky score > 50 Ovarian endometrial cervical) AND (Gynecologic Oncology Group (GOG) performance score ≤2) AND (HER2-neu positive) AND (Histologically proven recurrent persistent) AND (Metastatic breast cancer) AND (Metastatic cervical cancer) AND (Metastatic endometrial cancer) AND (Metastatic ovarian cancer) AND (Normal organ function within 14 days of study entry) AND (Paclitaxel) AND (Progression on) AND (Response Evaluation Criteria in Solid Tumors (RECIST)) AND (abstinence) AND (adenocarcinoma of the cervix) AND (adenosquamous carcinoma) AND (barrier method) AND (carboplatin) AND (chemotherapy regimen) AND (chemotherapy regimen previous) AND (chemotherapy regimens failed previous) AND (childbearing potential) AND (cisplatin) AND (contraception prior to study entry for the duration of study participation) AND (endometrial cancer) AND (epithelial ovarian cancer) AND (estrogen receptor positive) AND (failure to respond) AND (fallopian tube cancer) AND (female) AND (histologically Primary tumor) AND (hormonal) AND (hormone therapy progressed through) AND (metastatic disease) AND (metastatic disease Measurable) AND (metastatic disease Measurable >1cm at least one) AND (performance status Adequate) AND (primary peritoneal cancer borderline low malignant potential) AND (progesterone receptor positive) AND (radiation therapy 2) AND (squamous cell carcinoma) AND (surgery) AND (therapy with a hormonal agent prior) AND (therapy with trastuzumab prior) AND (trastuzumab therapy progressed through) AND (treatment regimens failed previous) AND (treatment regimens previous) AND NOT (epithelial carcinoma at least two))"}
{"candidate_id": "LLM07828", "doc_id": "NCT01720394_exc", "case_bucket": "other", "source_criterion": "fetal anomalies contra-indications for medical induction of labor placental pathologies St.p. surgery with opening the uterine cavity (incl. caesarean section) PROM multiple gestations < 37-0 weeks of gestation St.p. cervical tear", "candidate_expression": "((< 37-0 weeks) AND (PROM) AND (St.p.) AND (caesarean section) AND (cervical tear) AND (contra-indications) AND (fetal anomalies) AND (gestation) AND (medical induction of labor) AND (multiple gestations) AND (placental pathologies) AND (surgery with opening the uterine cavity))"}
{"candidate_id": "LLM07829", "doc_id": "NCT02077556_inc", "case_bucket": "other", "source_criterion": "De novo kidney transplants 20 - 65 years old aspartate aminotransferase/alanine aminotransferase within 2 times the upper limit of normal range", "candidate_expression": "((alanine aminotransferase) AND (aspartate aminotransferase) AND (kidney transplants De novo) AND (old 20 - 65 years))"}
{"candidate_id": "LLM07830", "doc_id": "NCT02022709_inc", "case_bucket": "or", "source_criterion": "Having been diagnosed with primary OCD as defined by the Diagnostic and Statistical Manual of Mental Disorders (DSM-IV-) criteria;Cleaning or checking as primary OCD symptoms Yale-Brown Obsessive-Compulsive Scale (Y-BOCS) score of = 16 Never receiving adequate treatment or stop receiving treatment for at least 8 weeks Having an education degree of high school or above Accepting to participate in the study", "candidate_expression": "((DSM-IV) AND (Diagnostic and Statistical Manual of Mental Disorders) AND (Y-BOCS score of = 16) AND (Yale-Brown Obsessive-Compulsive Scale) AND (ccepting to participate in the study) AND (degree of high school) AND (primary OCD) AND NOT (treatment for at least 8 weeks) AND NOT (treatment adequate))"}
{"candidate_id": "LLM07831", "doc_id": "NCT00351611_exc", "case_bucket": "or", "source_criterion": "Pre-existing eye diseases (glaucoma). Insufficient response to pregabalin in the treatment of partial seizure, or patients currently receiving pregabalin treatment.", "candidate_expression": "((Insufficient response) AND (Pre-existing) AND (eye diseases) AND (glaucoma) AND (partial seizure) AND (pregabalin))"}
{"candidate_id": "LLM07832", "doc_id": "NCT02796378_exc", "case_bucket": "or", "source_criterion": "Cholesterol-lowering drugs Diabetes Mellitus Cardiovascular disease such as arrythmia, ischaemic heart disease. Musculoskeletal disorders preventing the subject to perform physical training Mental disorders preventing the subject to understand the project description.", "candidate_expression": "((Cardiovascular disease) AND (Cholesterol-lowering drugs) AND (Diabetes Mellitus) AND (Mental disorders) AND (Musculoskeletal disorders) AND (preventing the subject to perform physical training) AND (preventing the subject to understand the project description) AND ((arrythmia) OR (ischaemic heart disease)))"}
{"candidate_id": "LLM07833", "doc_id": "NCT02476461_inc", "case_bucket": "other", "source_criterion": "symptomatic Dupuytrens contracture with palpable cord, involving MCP, total contracture size over 30 degrees", "candidate_expression": "((Dupuytrens contracture symptomatic involving MCP) AND (palpable cord) AND (total contracture size over 30 degrees))"}
{"candidate_id": "LLM07834", "doc_id": "NCT03192020_inc", "case_bucket": "or", "source_criterion": "patients with =20° passive extension deficit (PED) in metacarpophalangeal (MP) or proximal interphalangeal (PIP) joint, or TPED of =30° in MP and PIP joints of finger/fingers II-V age > 18 years palpable cord provision of informed consent ability to fill the Finnish versions of questionnaires.", "candidate_expression": "((TPED =30° MP PIP joints finger/fingers II-V) AND (age > 18 years) AND (palpable cord) AND (passive extension deficit (PED) =20° joint metacarpophalangeal (MP) proximal interphalangeal (PIP) joint) AND (provision of informed consent))"}
{"candidate_id": "LLM07835", "doc_id": "NCT01320579_inc", "case_bucket": "or", "source_criterion": "Informed consent obtained prior to any screening procedure Caucasian male or female patient At least 18 years of age Weight at least 45 kg Patient with moderate or severe chronic atopic dermatitis Good general health ascertained by medical history, physical examination and laboratory determinations, showing no signs of clinically significant findings, except chronic atopic dermatitis Negative pregnancy test (premenopausal female patient) at screening and use of adequate contraceptive measures (both male and female patients) throughout the study and 30 days after the last cis-UCA dose", "candidate_expression": "((At least 18 years) AND (Caucasian) AND (Good general health) AND (Informed consent obtained prior to any screening procedure) AND (Negative) AND (Negative pregnancy test (premenopausal female patient) at screening and use of adequate contraceptive measures (both male and female patients) throughout the study and 30 days after the last cis-UCA dose) AND (Weight) AND (age) AND (ascertained by medical history, physical examination and laboratory determinations) AND (at least 45 kg) AND (chronic atopic dermatitis) AND (clinically significant) AND (except) AND (female) AND (laboratory determinations) AND (medical history) AND (no) AND (physical examination) AND (pregnancy test) AND (premenopausal) AND (signs of clinically significant findings) AND ((moderate) OR (severe)) AND ((female) OR (male)))"}
{"candidate_id": "LLM07836", "doc_id": "NCT02385045_exc", "case_bucket": "or", "source_criterion": "Patients attending for a therapeutic endoscopic procedure e.g. variceal banding, stent insertion, balloon dilatation. Patients with a known diagnosis e.g. upper gastrointestinal cancer Patients previously treated with HP eradication therapy Patients who had taken PPI, H2 receptor antagonists and antibiotics within 4 weeks Patients with acute gastrointestinal bleeding Patients who'd had previous gastric surgery Patients with chronic liver disease Patients with abnormal coagulation or any other contra-indication to use of standard biopsy in routine diagnostic endoscopic procedures Patients who are unable or unwilling to give informed consent Patients under the age of 18 years", "candidate_expression": "((H2 receptor antagonists) AND (HP eradication therapy) AND (PPI) AND (abnormal coagulation) AND (acute) AND (age) AND (antibiotics) AND (balloon dilatation) AND (chronic) AND (contra-indication) AND (diagnostic endoscopic procedures) AND (gastric surgery) AND (gastrointestinal bleeding) AND (known diagnosis) AND (liver disease) AND (previous) AND (standard biopsy) AND (stent insertion) AND (therapeutic endoscopic procedure) AND (under 18 years) AND (upper gastrointestinal cancer) AND (variceal banding) AND (within 4 weeks))"}
{"candidate_id": "LLM07837", "doc_id": "NCT03320057_exc", "case_bucket": "other", "source_criterion": "Not pregnant Not seeking medication abortion Under the age of 15 Contraindications for medication abortion", "candidate_expression": "((Contraindications) AND (age Under 15) AND (medication abortion) AND (pregnant))"}
{"candidate_id": "LLM07838", "doc_id": "NCT02203019_exc", "case_bucket": "or", "source_criterion": "Patients with documented allergies to propofol, dexmedetomidine, fentanyl, eggs or egg products, or soy or soy products. A heart rate less than 50 beats/minute or grade 2 or 3 AV heart block Mean arterial pressure less than 55 mmHg despite appropriate fluid resuscitation and vasopressor support. Current triglyceride level > 400 mg/dl", "candidate_expression": "((Mean arterial pressure less than 55 mmHg) AND (allergies) AND (fluid resuscitation) AND (triglyceride level > 400 mg/dl) AND (vasopressor) AND ((AV heart block) OR (heart rate less than 50 beats/minute)) AND ((grade 2) OR (grade 3)) AND ((dexmedetomidine) OR (egg products) OR (eggs) OR (fentanyl) OR (propofol) OR (soy) OR (soy products)))"}
{"candidate_id": "LLM07839", "doc_id": "NCT02618057_inc", "case_bucket": "or", "source_criterion": "Evidence of Mycoplasma pneumoniae infection Lobar pneumonia or pneumoniae with pleural effusion", "candidate_expression": "((Mycoplasma pneumoniae infection) AND (pleural effusion) AND ((Lobar pneumonia) OR (pneumoniae)))"}
{"candidate_id": "LLM07840", "doc_id": "NCT00461136_inc", "case_bucket": "scope", "source_criterion": "Male and/or female patients from 30-80 years of age with a diagnosis of Type 2 diabetes (WHO criteria). Incipient and established diabetic nephropathy (urinary albumin excretion ≥ 100 mg/day but ≤ 2000 mg/day). Glomerular filtration rate (GFR) ≥ 40 ml/min (estimated using Modification of Diet in Renal Disease (MDRD) formula) in the last 4 months. Female patients must be postmenopausal or must have had a bilateral oophorectomy or must have been surgically sterilized or hysterectomized at least 6 months prior to screening. To be eligible patients must fulfill the following criteria: Patients on ongoing hypertensive therapy must have a blood pressure ≥ 135/85 mm Hg but lower than 170/105 mm Hg at baseline (Day -1) AND patients must be on stable antihypertensive medications for at least 8 weeks prior to baseline (Day -1).; Newly diagnosed hypertensive patients must have a blood pressure ≥ 135/85 mm Hg but lower than 170/105 mm Hg at baseline (Day -1). Patients must be on stable hypoglycemic medications for at least 8 weeks prior to Visit 2 ( Day -1). Patients must be willing and medically able to discontinue all Angiotensin-converting enzyme inhibitor (ACEI), Angiotensin receptor blocker (ARB), aldosterone receptor antagonist and potassium sparing diuretic medications for the duration of the study. Oral body temperature within the range 35.0-37.5 °C Able to provide written informed consent prior to study participation. . Able to communicate well with the investigator and comply with the requirements of the study.", "candidate_expression": "((Able to communicate well) AND (Female) AND (Glomerular filtration rate (GFR) ≥ 40 ml/min Modification of Diet in Renal Disease (MDRD) formula in the last 4 months) AND (Oral body temperature 35.0-37.5 °C) AND (Type 2 diabetes) AND (antihypertensive medications stable at least 8 weeks prior to baseline) AND (bilateral oophorectomy) AND (blood pressure at baseline (Day -1) ≥ 135/85 mm Hg lower than 170/105 mm Hg) AND (blood pressure ≥ 135/85 mm Hg lower than 170/105 mm Hg) AND (comply with the requirements of the study) AND (diabetic nephropathy) AND (hypertensive patients Newly diagnosed) AND (hypertensive therapy) AND (hypoglycemic medications stable at least 8 weeks prior to Visit 2) AND (hysterectomized) AND (of age 30-80 years) AND (postmenopausal) AND (surgically sterilized) AND (urinary albumin excretion ≥ 100 mg/day ≤ 2000 mg/day) AND (written informed consent prior to study participation))"}
{"candidate_id": "LLM07841", "doc_id": "NCT02877485_exc", "case_bucket": "or", "source_criterion": "Intranasal steroid use within the last three months Current systemic steroid use Prior septal surgery Individuals who are pregnant or actively breastfeeding", "candidate_expression": "((Current) AND (Intranasal) AND (Intranasal steroid use) AND (Prior) AND (actively) AND (breastfeeding) AND (pregnant) AND (septal surgery) AND (steroid) AND (systemic) AND (systemic steroid use) AND (within the last three months))"}
{"candidate_id": "LLM07842", "doc_id": "NCT01888965_exc", "case_bucket": "or", "source_criterion": "Women of child-bearing potential, who are biologically able to conceive, not employing two forms of highly effective contraception or who are pregnant. Women who are breast-feeding Fertile males unwilling to use contraception Patients with brain metastases or any history of brain metastases Patients who have undergone major surgery (e.g., intra-thoracic, -abdominal, or -pelvic) </= 4 weeks prior to starting study treatment or who have not recovered from such therapy Patients with a history of pulmonary embolism, or untreated deep vein thrombosis within the past 6 months Impairment of gastrointestinal (GI) function or GI disease that may significantly alter the absorption of dovitinib The subject has had another active malignancy within the past 5 years except for cervical cancer in situ, in situ carcinoma of the bladder or non-melanoma carcinoma of the skin. Patients who have received the last administration of an anticancer therapy including chemotherapy, immunotherapy, hormonal therapy and monoclonal antibodies </= 2 weeks prior to starting the study drug, or who have not recovered from the side effects of such therapy Cirrhosis, chronic active hepatitis or chronic persistent hepatitis Patients who are currently receiving prasugrel No concurrent use of isoniazid, labetolol, trovafloxacin, tolcapone, and felbamate No concurrent use of other investigational drugs or antineoplastic therapies. Patients with impaired cardiac function or clinically significant cardiac diseases.", "candidate_expression": "((Fertile) AND (Fertile males unwilling to use contraception) AND (Women) AND (active malignancy within the past 5 years) AND (biologically able to conceive) AND (breast-feeding) AND (child-bearing potential) AND (clinically significant) AND (major surgery) AND (males) AND (prasugrel) AND (recovered from such therapy) AND (unwilling to use contraception) AND ((brain metastases) OR (brain metastases history)) AND ((major surgery </= 4 weeks prior to starting study treatment) OR NOT (recovered from such therapy)) AND ((intra -abdominal) OR (intra -pelvic) OR (intra-thoracic)) AND ((deep vein thrombosis untreated) OR (pulmonary embolism)) AND ((GI disease) OR (Impairment of gastrointestinal (GI) function)) AND ((cervical cancer in situ) OR (in situ carcinoma of the bladder) OR (non-melanoma carcinoma of the skin)) AND ((anticancer therapy </= 2 weeks prior to starting the study drug) OR (recovered from the side effects of such therapy)) AND ((chemotherapy) OR (hormonal therapy) OR (immunotherapy) OR (monoclonal antibodies)) AND ((Cirrhosis) OR (chronic active hepatitis) OR (chronic persistent hepatitis)) AND ((pregnant) OR NOT (highly effective contraception two)) AND ((felbamate) OR (isoniazid) OR (labetolol) OR (tolcapone) OR (trovafloxacin)) AND ((antineoplastic therapies) OR (other investigational drugs)) AND ((cardiac diseases clinically significant) OR (impaired cardiac function)))"}
{"candidate_id": "LLM07843", "doc_id": "NCT02787863_inc", "case_bucket": "or", "source_criterion": "Individuals of both sexes from 18 years with a diagnosis of community-acquired pneumonia, COPD or Bronchial Asthma; The presence of signed and dated informed consent to participate in a clinical study; The ability to perform the requirements of the Protocol; For women of childbearing age is a negative result of a pregnancy test before vaccination. community-acquired pneumonia: the presence of radiologically confirmed infiltration of the lung tissue; the presence of at least two of the following clinical signs: acute fever early in the disease (temperature > 38.0°C), cough with sputum, the physical signs of pneumonia (focus of crepitate and/or fine bubble rales, bronchial breathing hard, shortening of percussion sounds), leukocytosis > 10*10 9 /l and/or stab shift > 10%; the occurrence of the disease outside the hospital and the organized groups (such as nursing homes, sanatoriums, etc.). COPD: dyspnea: progressive (worsens over time), increases with exertion, persistent; chronic cough (may appear sporadically and may be unproductive); chronic expectoration; the impact of risk factors in the medical history (Smoking, occupational dust pollutants and chemicals); widespread wheeze on auscultation of the chest and/or distant wheezing in the chest; family history of COPD; spirometric data confirming the presence of fixed bronchial obstruction.", "candidate_expression": "((COPD progressive worsens over time increases with exertion persistent) AND (For women of childbearing age is a negative result of a pregnancy test before vaccination.) AND (The ability to perform the requirements of the Protocol;) AND (both sexes) AND (community-acquired pneumonia) AND (fixed bronchial obstruction) AND (from 18 years from 18 years) AND (infiltration of the lung tissue radiologically confirmed) AND (physical signs) AND (pneumonia) AND (radiologically) AND (temperature > 38.0°C) AND ((acute fever early in the disease) OR (cough with sputum)) AND ((bronchial breathing hard) OR (crepitate rales) OR (fine bubble rales) OR (shortening of percussion sounds)) AND ((leukocytosis > 10*10 9 /l) OR (stab shift > 10%)) AND ((Smoking) OR (occupational dust pollutants and chemicals)) AND ((COPD family history) OR (chronic cough) OR (chronic expectoration) OR (distant wheezing in the chest) OR (dyspnea) OR (risk factors) OR (spirometric) OR (wheeze on auscultation of the chest widespread)) AND ((Bronchial Asthma) OR (COPD) OR (community-acquired pneumonia)))"}
{"candidate_id": "LLM07844", "doc_id": "NCT00846703_exc", "case_bucket": "other", "source_criterion": "No Down syndrome No other major disease that prohibits study treatment (e.g., severe congenital heart disease) Not requiring significant therapy modification owing to study therapy associated complications No complications due to other interventions No one with missing data that are needed for the differential diagnosis, or for selection of the proper therapy arm", "candidate_expression": "((Down syndrome) AND (No) AND (Not) AND (complications) AND (congenital heart disease) AND (interventions) AND (major disease) AND (other) AND (severe) AND (study therapy))"}
{"candidate_id": "LLM07845", "doc_id": "NCT00650312_inc", "case_bucket": "or", "source_criterion": "1. Age: 18 years and older. 2. Sex: Male and non-pregnant, non-lactating female 1. Women of childbearing potential must have negative serum (Beta HCG) pregnancy tests performed within 14 days prior to the start of the study and on the evening prior to each dose administration. If dosing is scheduled on Sunday or Monday, the HCG pregnancy test should be given within 48 hours prior to dosing of each study period. An additional serum (Beta HCG) pregnancy test will be performed upon completion of the study. 2. Women of childbearing potential must practice abstinence or be using an acceptable form of contraception throughout the duration of the study. Acceptable forms of contraception include the following: (1) intrauterine device in place for at least 3 months prior to the start of the study and remaining in place during the study period, or (2) barrier methods containing or used in conjunction with a spermicidal agent, or (3) postmenopausal accompanied with a documented postmenopausal course of at least one year or surgical sterility (tubal ligation, oophorectomy or hysterectomy). 3. During the course of the study, from study screen until study exit - including the washout period, women of childbearing potential must use a spermicide containing barrier method of contraception in addition to their current contraceptive device. This advice should be documented in the informed consent form. 3. Weight: At least 60 kg (132 lbs) for man and 48 kg (106 lbs) for women and within 15% of Ideal Body Weight (IBW), as referenced by the Table of \"\"Desirable Weights of Adults\"\" Metropolitan Life Insurance Company, 1999 (See Part II ADMINISTRATIVE ASPECTS OF BIOEQUIVALENCE PROTOCOLS). 4. All subjects should be judged normal and healthy during a pre-study medical evaluation (physical examination, laboratory evaluation, 12-lead ECG, hepatitis B and hepatitis C tests, HIV test, and urine drug screen including amphetamine, barbiturates, benzodiazepine, cannabinoid, cocaine, opiates, phencyclidine, and methadone) performed within 14 days of the initial dose of study medication.", "candidate_expression": "((12-lead ECG) AND (Age 18 years and older) AND (Beta HCG) AND (HIV test) AND (Male) AND (Weight within 15% of Ideal Body Weight (IBW) At least 132 lbs At least 106 lbs) AND (Women) AND (abstinence) AND (barrier methods) AND (childbearing potential) AND (contraception acceptable form) AND (contraceptive device current) AND (female) AND (healthy) AND (hepatitis B tests) AND (hepatitis C tests) AND (hysterectomy) AND (intrauterine device for at least 3 months prior to the start of the study in place during the study period) AND (laboratory evaluation) AND (man At least 60 kg) AND (methadone) AND (normal) AND (oophorectomy) AND (phencyclidine) AND (physical examination) AND (postmenopausal at least one year) AND (pre-study medical evaluation within 14 days of the initial dose of study medication) AND (serum pregnancy tests negative within 14 days prior to the start of the study on the evening prior to each dose administration) AND (spermicidal agent) AND (spermicide containing barrier method of contraception in addition to) AND (surgical sterility) AND (tubal ligation) AND (urine drug screen amphetamine barbiturates benzodiazepine cannabinoid cocaine opiates) AND (women) AND (women At least 48 kg) AND NOT (pregnant) AND NOT (lactating))"}
{"candidate_id": "LLM07846", "doc_id": "NCT02874092_exc", "case_bucket": "or", "source_criterion": "History of sensitivity to study medications or any of their excipients RA cohort: Previous intolerance to MTX Current treatment with antiplatelet therapy Absolute indication for anti-platelet therapy Need for chronic oral anticoagulant therapy Severe hepatic impairment (eg, ascites and/or clinical signs of coagulopathy) Renal failure (eGFR <30 or requiring dialysis) A known bleeding diathesis, hemostatic or coagulation disorder, or prior major bleeding Prior stroke Active pathological bleeding History of intracranial haemorrhage Life expectancy <12 months based on investigator's judgement Patients considered to be at risk of bradycardic events (e.g., known sick sinus syndrome or second or third degree atrioventricular [AV)] block) unless already treated with a permanent pacemaker Anemia (hematocrit < 27%) Platelet count < 100,000/ml Concomitant use of strong CYP 3A inhibitors or inducers History of thrombocytopenia or neutropenia Pregnant or nursing women, or females with a positive pregnancy test at screening Females of child bearing potential not using acceptable method of birth control prior to or during study Concern for inability of the patient to comply with study procedures and/or follow up (eg, alcohol or drug abuse)", "candidate_expression": "((Anemia) AND (Females) AND (Life expectancy <12 months) AND (MTX) AND (Platelet count < 100,000/ml) AND (Pregnant) AND (RA) AND (Renal failure) AND (Severe hepatic impairment) AND (alcohol abuse) AND (anti-platelet therapy Absolute indication for Need for) AND (antiplatelet therapy Current) AND (ascites) AND (bleeding diathesis) AND (bradycardic events at risk of) AND (child bearing potential) AND (chronic oral anticoagulant therapy) AND (coagulation disorder) AND (coagulopathy clinical signs of) AND (dialysis requiring) AND (drug abuse) AND (eGFR <30) AND (females) AND (hematocrit < 27%) AND (hemostatic disorder) AND (inability to comply with follow up) AND (inability to comply with study procedures) AND (intolerance) AND (intracranial haemorrhage History) AND (major bleeding prior) AND (neutropenia) AND (nursing) AND (pathological bleeding Active) AND (pregnancy test positive at screening) AND (second degree atrioventricular [AV)] block) AND (sensitivity) AND (sick sinus syndrome) AND (stroke Prior) AND (strong CYP 3A inducers) AND (strong CYP 3A inhibitors) AND (study medications) AND (third degree atrioventricular [AV)] block) AND (thrombocytopenia) AND (women) AND NOT (permanent pacemaker) AND NOT (method of birth control acceptable prior to study during study))"}
{"candidate_id": "LLM07847", "doc_id": "NCT02273791_inc", "case_bucket": "other", "source_criterion": "Women with PCOS as defined by the Rotterdam criteria. Presence of at least 2 cryopreserved good quality cleavage-stage embryo (good quality cleavage-stage embryos display stage-specific cell division, have blastomeres of fairly equal size with few to no cytoplasmic fragments).", "candidate_expression": "((PCOS) AND (Rotterdam criteria) AND (Women) AND (at least 2) AND (cleavage-stage embryo) AND (cryopreserved) AND (good))"}
{"candidate_id": "LLM07848", "doc_id": "NCT03070847_exc", "case_bucket": "or", "source_criterion": "pregnancy known allergies for tranexamic acid or any other substance in Exacyl deep vein thrombosis Hormone Replacement Therapy or oral contraceptive usage anticoagulants usage obesity - BMI (body mass index) >30 kg/m2 renal disease, as glomerular filtration rate (GFR) <60 ml/min/1,73 m*m seizures or epilepsy in the past", "candidate_expression": "((<60 ml/min/1,73 m*m) AND (>30 kg/m2) AND (BMI) AND (GFR) AND (allergies) AND (anticoagulants) AND (body mass index) AND (deep vein thrombosis) AND (glomerular filtration rate) AND (in the past) AND (obesity) AND (pregnancy) AND (renal disease) AND ((epilepsy) OR (seizures)) AND ((Exacyl) OR (tranexamic acid)) AND ((Hormone Replacement Therapy) OR (oral contraceptive)))"}
{"candidate_id": "LLM07849", "doc_id": "NCT01909934_inc", "case_bucket": "or", "source_criterion": "Male or female patients age 18 years or older, with relapsed or refractory sALCL who have previously received at least 1 multiagent chemotherapy Bidimensional measurable disease An Eastern Cooperative Oncology Group (ECOG) performance status of 0 or 1 Female patients who are postmenopausal for at least 1 year before the screening visit, surgically sterile, or agree to practice 2 effective methods of contraception, at the same time, from the time of signing the informed consent form through 30 days after the last dose of study drug, or agree to practice true abstinence Male patients who agree to practice effective barrier contraception during the entire study treatment period through 6 months after the last dose of study drug or agree to practice true abstinence Clinical laboratory values as specified in the study protocol", "candidate_expression": "((ECOG) AND (Eastern Cooperative Oncology Group performance status 0 or 1) AND (Female patients who are postmenopausal for at least 1 year before the screening visit, surgically sterile, or agree to practice 2 effective methods of contraception, at the same time, from the time of signing the informed consent form through 30 days after the last dose of study drug, or agree to practice true abstinence) AND (Male) AND (Male patients who agree to practice effective barrier contraception during the entire study treatment period through 6 months after the last dose of study drug or agree to practice true abstinence) AND (age 18 years or older relapsed) AND (chemotherapy at least 1) AND (female) AND (sALCL refractory))"}
{"candidate_id": "LLM07850", "doc_id": "NCT03381755_exc", "case_bucket": "or", "source_criterion": "taken adenosine diphosphate (ADP) receptor antagonists within 2 weeks Platelet count <100g/L; A history of bleeding tendency; Aspirin, ticagrelor or clopidogrel allergies; Severe liver injury.", "candidate_expression": "((Aspirin) AND (Platelet count <100g/L) AND (adenosine diphosphate (ADP) receptor antagonists within 2 weeks) AND (allergies) AND (bleeding tendency history) AND (clopidogrel) AND (liver injury Severe) AND (ticagrelor))"}
```
