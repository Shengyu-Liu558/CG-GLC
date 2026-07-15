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
{"candidate_id": "LLM00126", "doc_id": "NCT02570347_exc", "case_bucket": "or", "source_criterion": "Upper limb bites Multiple (> 1) bites Wound manipulation Extensive local necrosis or blebs Seriously-ill patients with hypotension/capillary leak/life threatening bleeding. Suspected cobra bite, OR Pregnant/breast-feeding women", "candidate_expression": "((Extensive local blebs) AND (Extensive local necrosis) AND (Pregnant) AND (Seriously-ill) AND (Wound manipulation) AND (bites Multiple > 1) AND (bites Upper limb) AND (bleeding life threatening) AND (breast-feeding) AND (capillary leak) AND (cobra bite Suspected) AND (hypotension) AND (women))"}
{"candidate_id": "LLM00127", "doc_id": "NCT00319748_inc", "case_bucket": "or", "source_criterion": "Adequate performance status: Breast - Karnofsky score > 50; Ovarian, endometrial or cervical - Gynecologic Oncology Group (GOG) performance score ≤2 If female and of childbearing potential, are willing to use adequate contraception (hormonal, barrier method, abstinence) prior to study entry and for the duration of study participation. Normal organ function within 14 days of study entry Diagnosis of one of the following malignancies: Metastatic breast cancer (BR) Metastatic ovarian cancer (OV) Metastatic endometrial cancer (EM) Metastatic cervical cancer (CX) Measurable metastatic disease (>1cm) in at least one site other than bone-only Progression on or failure to respond to at least one previous chemotherapy regimen for metastatic disease Progression on prior therapy with a hormonal agent if estrogen receptor or progesterone receptor positive, and/or with trastuzumab if HER2-neu positive. If patient has progressed through hormone or trastuzumab therapy only, must have received one chemotherapy regimen. Measurable metastatic disease as defined by Response Evaluation Criteria in Solid Tumors (RECIST) Primary tumor must have been diagnosed histologically as either epithelial ovarian cancer, fallopian tube cancer, or primary peritoneal cancer (not borderline or low malignant potential epithelial carcinoma). Subjects must have failed at least two previous chemotherapy regimens. Paclitaxel must have been a component of one or both regimens and cisplatin or carboplatin must have been a component of one or both regimens. Measurable metastatic disease Histologically proven recurrent or persistent endometrial cancer that is not amenable to curative treatment with surgery and/or radiation therapy AND has failed 2 previous treatment regimens Measurable metastatic disease Histologically proven recurrent or persistent squamous cell carcinoma, adenosquamous carcinoma, or adenocarcinoma of the cervix that is not amenable to curative treatment with surgery and/or radiation therapy AND has failed 2 previous treatment regimens.", "candidate_expression": "((2) AND (> 50) AND (Adequate) AND (Breast - Karnofsky score) AND (Gynecologic Oncology Group (GOG) performance score) AND (HER2-neu positive) AND (Histologically) AND (Measurable) AND (Metastatic breast cancer) AND (Metastatic cervical cancer) AND (Metastatic endometrial cancer) AND (Metastatic ovarian cancer) AND (Normal organ function) AND (Paclitaxel) AND (Primary tumor) AND (Progression on) AND (Response Evaluation Criteria in Solid Tumors (RECIST)) AND (adenocarcinoma of the cervix) AND (adenosquamous carcinoma) AND (amenable to curative treatment) AND (at least one) AND (at least two) AND (chemotherapy regimen) AND (chemotherapy regimens) AND (childbearing potential) AND (contraception) AND (endometrial cancer) AND (epithelial carcinoma) AND (failed) AND (female) AND (for the duration of study participation) AND (histologically) AND (metastatic disease) AND (not) AND (performance status) AND (previous) AND (prior) AND (prior to study entry) AND (progressed through) AND (proven) AND (site other than bone-only) AND (squamous cell carcinoma) AND (study entry) AND (study participation) AND (therapy with a hormonal agent) AND (therapy with trastuzumab) AND (treatment regimens) AND (willing to) AND (within 14 days of study entry) AND (≤2) AND ((Ovarian) OR (cervical) OR (endometrial)) AND ((abstinence) OR (barrier method) OR (hormonal)) AND ((>1cm) OR (Measurable)) AND ((Progression on) OR (failure to respond)) AND ((estrogen receptor positive) OR (progesterone receptor positive)) AND ((hormone therapy) OR (trastuzumab therapy)) AND ((epithelial ovarian cancer) OR (fallopian tube cancer) OR (primary peritoneal cancer)) AND ((borderline) OR (low malignant potential)) AND ((carboplatin) OR (cisplatin)) AND ((radiation therapy) OR (surgery)) AND ((persistent) OR (recurrent)))"}
{"candidate_id": "LLM00128", "doc_id": "NCT00461136_exc", "case_bucket": "or", "source_criterion": "Severe Hypertension Grade 3 WHO classification (Mean Sitting Diastolic Blood Pressure (MSDBP) 110 mmHg and/or Mean Sitting Systolic Blood Pressure MSSBP 180 mmHg) Acetylsalicyclic acid (ASA) treatment >1g/day or regular use of Non steroidal anti-inflammatory drug (NSAIDs) Kidney disease not caused by diabetes or hypertension Serum potassium < 3.5 or > 5.1 mEq/L GFR < 40 ml/min/1.73m2 as measured by the MDRD formula Serum albumin < 2.0mg/dL History of hypertensive encephalopathy or cerebrovascular accident at any time prior to Visit1. Current diagnosis of heart failure (New York Heart Association (NYHA) Class II-IV) History of myocardial infarction, unstable angina pectoris, coronary bypass surgery, or any percutaneous coronary intervention (PCI) during the 6 months prior to Visit 1 Second or third degree heart block without a pacemaker Concurrent potentially life threatening arrhythmia or symptomatic arrhythmia Clinically significant valvular heart disease Type 1 diabetes mellitus Uncontrolled Type II diabetes mellitus (Hemaglobin subtype A1C (HbA1C) >11 %) History of malignancy including leukemia and lymphoma (but not basal cell skin carcinoma) within the past five years Participation in any clinical investigation within 4 weeks prior to dosing or longer if required by local regulation. Donation or loss of 400 mL or more of blood within 8 weeks prior to dosing. Significant illness within the two weeks prior to dosing. Any surgical or medical condition which might significantly alter the absorption, distribution, metabolism, or excretion of study drugs including, but not limited to, any of the following: History of major gastrointestinal tract surgery such as gastrectomy, gastroenterostomy, or bowel resection -Currently active or previously active inflammatory bowel disease during the 12 months prior to Visit 1 Currently active gastritis, duodenal or gastric ulcers, or gastrointestinal/rectal bleeding during the 3 months prior to Visit 1. Any history of pancreatic injury, pancreatitis or evidence of impaired pancreatic function/injury as indicated by abnormal lipase or amylase Evidence of hepatic disease, a history of hepatic encephalopathy, a history of esophageal varices, or a history of portocaval shunt Current treatment with cholestyramine or cholestipol resins History of immunocompromise, including a positive HIV test result. History of a positive Hepatitis B surface antigen (HBsAg) or Hepatitis C test result. History of drug or alcohol abuse within the 12 months prior to dosing. Persons directly involved in the execution of this protocol. Any condition that in the opinion of the investigator or the Novartis medical monitor would jeopardize the evaluation of efficacy or safety History of noncompliance to medical regimens or unwillingness to comply with the study protocol Known or suspected contraindications to the study medications, including history of allergy to Angiotensin converting enzyme (ACE) inhibitors and/or to thiazide diuretics or other sulfonamide derived drug Any surgical or medical condition, which in the opinion of the investigator, may place the patient at higher risk from his/her participation in the study, or is likely to prevent the patient from complying with the requirements of the study or completing the study Use of any prescription drug or over-the-counter (OTC) medication which is prohibited by the protocol. Patients who previously participated in any Aliskiren study. Pregnant or nursing woman. Other protocol-defined inclusion/exclusion criteria may apply", "candidate_expression": "((110 mmHg) AND (180 mmHg) AND (3) AND (400 mL or more) AND (< 2.0mg/dL) AND (< 3.5) AND (< 40 ml/min/1.73m2) AND (> 5.1 mEq/L) AND (>11 %) AND (>1g/day) AND (Acetylsalicyclic acid (ASA) treatment) AND (Aliskiren) AND (Aliskiren study) AND (Angiotensin converting enzyme (ACE) inhibitors) AND (Current) AND (Currently active) AND (Donation of blood) AND (GFR) AND (Grade WHO classification) AND (HIV test) AND (Hemaglobin subtype A1C (HbA1C)) AND (Hepatitis B surface antigen (HBsAg) test) AND (Hepatitis C test) AND (History) AND (History of) AND (II-IV) AND (Kidney disease) AND (MDRD formula) AND (Mean Sitting Diastolic Blood Pressure (MSDBP)) AND (Mean Sitting Systolic Blood Pressure MSSBP) AND (New York Heart Association (NYHA) Class) AND (Non steroidal anti-inflammatory drug (NSAIDs)) AND (Other) AND (Pregnant) AND (Second degree heart block) AND (Serum albumin) AND (Serum potassium) AND (Severe Hypertension) AND (Significant illness) AND (Type 1 diabetes mellitus) AND (Type II diabetes mellitus) AND (Uncontrolled) AND (abnormal) AND (alcohol abuse) AND (allergy) AND (alter the absorption, distribution, metabolism, or excretion of study drugs) AND (amylase) AND (any clinical investigation) AND (any time prior) AND (arrhythmia) AND (basal cell skin carcinoma) AND (bowel resection) AND (cerebrovascular accident) AND (cholestipol resins) AND (cholestyramine) AND (comply with the study protocol) AND (complying with the requirements of the study) AND (condition) AND (contraindications) AND (coronary bypass surgery) AND (diabetes) AND (dosing) AND (drug abuse) AND (duodenal) AND (during the 12 months prior) AND (during the 3 months prior) AND (during the 6 months prior) AND (esophageal varices) AND (gastrectomy) AND (gastric ulcers) AND (gastritis) AND (gastroenterostomy) AND (gastrointestinal bleeding) AND (heart failure) AND (hepatic disease) AND (hepatic encephalopathy) AND (history) AND (history of) AND (hypertension) AND (hypertensive encephalopathy) AND (immunocompromise) AND (impaired) AND (inflammatory bowel disease) AND (leukemia) AND (likely to prevent the patient from) AND (lipase) AND (loss of blood) AND (lymphoma) AND (major gastrointestinal tract surgery) AND (malignancy) AND (medical condition) AND (myocardial infarction) AND (noncompliance to medical regimens) AND (nursing) AND (other) AND (over-the-counter (OTC) medication) AND (pacemaker) AND (pancreatic function) AND (pancreatic injury) AND (pancreatitis) AND (percutaneous coronary intervention (PCI)) AND (place the patient at higher risk from his/her participation in the study) AND (portocaval shunt) AND (positive) AND (potentially life threatening) AND (prescription drug) AND (prevent) AND (previously) AND (previously active) AND (prohibited by the protocol) AND (protocol-defined) AND (rectal bleeding) AND (study medications) AND (sulfonamide derived drug) AND (surgical condition) AND (symptomatic) AND (that would jeopardize safety) AND (that would jeopardize the evaluation of efficacy) AND (thiazide diuretics) AND (third degree heart block) AND (unstable angina pectoris) AND (unwillingness to) AND (valvular heart disease) AND (within 4 weeks prior to dosing) AND (within 8 weeks prior) AND (within the 12 months prior) AND (within the past five years) AND (within the two weeks prior) AND (without) AND (woman))"}
{"candidate_id": "LLM00129", "doc_id": "NCT03297021_inc", "case_bucket": "or", "source_criterion": "ASA I, II, III presenting for ambulatory surgery to be performed under general anesthesia", "candidate_expression": "((ASA I II III) AND (ambulatory surgery under general anesthesia) AND (general anesthesia))"}
{"candidate_id": "LLM00130", "doc_id": "NCT03173092_inc", "case_bucket": "other", "source_criterion": "Participants must have completed 3 cycles of a bortezomib-based induction regimen (as defined by current NCCN guidelines) and have no evidence of disease progression as defined by IMWG criteria. Participants with light chain and free light chain (FLC) only may be enrolled if they meet all the criteria for a diagnosis of MM. Participants must be considered by their physician eligible to receiving the IRD regimen. Eastern Cooperative Oncology Group (ECOG) performance status and/or other performance status 0, 1, or 2 at time of enrollment.", "candidate_expression": "((Eastern Cooperative Oncology Group (ECOG) performance status 0, 1, or 2 at time of enrollment) AND (IMWG criteria no evidence of disease progression) AND (IRD regimen eligible to) AND (bortezomib) AND (criteria for a diagnosis of MM all) AND (induction regimen 3 cycles NCCN guidelines) AND (light chain and free light chain (FLC)))"}
{"candidate_id": "LLM00131", "doc_id": "NCT03036462_inc", "case_bucket": "other", "source_criterion": "Patients aged at least 18 years Patients with chronic heart failure present for at least 12 months Confirmed presence of iron deficiency Serum haemoglobin of 9.5 to 14.0 g/dL", "candidate_expression": "((9.5 to 14.0 g/dL) AND (Serum haemoglobin) AND (aged) AND (at least 18 years) AND (chronic heart failure) AND (for at least 12 months) AND (iron) AND (iron deficiency))"}
{"candidate_id": "LLM00132", "doc_id": "NCT02186600_exc", "case_bucket": "or", "source_criterion": "Have osteoporosis Have a 10 yr probability of hip fracture >3% or major fracture >20% based on results of the FRAX tool Currently take bisphosphonates, estrogen replacement therapy, glucocorticosteroids, or other drugs affecting bone Currently participate in a resistance training or high impact weight bearing exercise program two or more times weekly Weigh >300 lbs Have abnormal results for the following laboratory tests: serum 25(OH)D; serum creatinine; serum calcium; PTH; TSH Have Paget's disease, heart disease, uncontrolled hypertension, renal disease, or other concomitant conditions that prohibit participation in exercises, risedronate therapy, or use of CaD supplements.", "candidate_expression": "((10 yr probability of hip fracture) AND (10 yr probability of major fracture) AND (>20%) AND (>3%) AND (>300 lbs) AND (PTH) AND (TSH) AND (Weigh) AND (abnormal results) AND (hip fracture) AND (major fracture) AND (osteoporosis) AND (serum 25(OH)D) AND (serum calcium) AND (serum creatinine) AND (two or more times weekly) AND ((participate in a resistance training) OR (participate in high impact weight bearing exercise)) AND ((CaD supplements) OR (Paget's disease) OR (heart disease) OR (other concomitant conditions that prohibit participation in exercises) OR (renal disease) OR (risedronate therapy) OR (uncontrolled hypertension)) AND ((bisphosphonates) OR (drugs affecting bone) OR (estrogen replacement therapy) OR (glucocorticosteroids)))"}
{"candidate_id": "LLM00133", "doc_id": "NCT02202369_inc", "case_bucket": "other", "source_criterion": "Subjects undergoing a single level lumbar decompression and fusion > 18 years of age and < 70 years of age The subject is willing and able to understand, sign and date the study specific patient informed consent and HIPAA authorization to volunteer participation in the study", "candidate_expression": "((The subject is willing and able to understand, sign and date the study specific patient informed consent and HIPAA authorization to volunteer participation in the study) AND (age > 18 years and < 70 years) AND (lumbar decompression single level) AND (lumbar fusion single level))"}
{"candidate_id": "LLM00134", "doc_id": "NCT02121145_inc", "case_bucket": "or", "source_criterion": "Male or female subjects aged =18 to =65 years General good health as established by medical history and physical examination Written informed consent Females of childbearing potential must agree to use an efficacious hormonal or barrier method of birth control during the study. Abstinence is acceptable. Available for all visits scheduled in this study.", "candidate_expression": "((Abstinence) AND (Available for all visits scheduled in this study) AND (Females) AND (General good health established by medical history) AND (Male) AND (Written informed consent) AND (aged =18 to =65 years) AND (birth control agree to use efficacious during the study barrier method) AND (childbearing potential hormonal method) AND (female) AND (physical examination))"}
{"candidate_id": "LLM00135", "doc_id": "NCT02469610_exc", "case_bucket": "other", "source_criterion": "Previous thoracic operation in the same side.", "candidate_expression": "(thoracic operation Previous same side)"}
{"candidate_id": "LLM00136", "doc_id": "NCT00198913_inc", "case_bucket": "other", "source_criterion": "type 2 diabetic, age 18 and over, informed consent,", "candidate_expression": "((18 and over) AND (age) AND (informed consent) AND (type 2 diabetic))"}
{"candidate_id": "LLM00137", "doc_id": "NCT02916342_inc", "case_bucket": "other", "source_criterion": "ASA physical status I-III; 18-85 years of age, inclusive; surgery less than 3 hours.", "candidate_expression": "((18-85 years , inclusive) AND (ASA physical status) AND (I-III) AND (age) AND (less than 3 hours) AND (surgery))"}
{"candidate_id": "LLM00138", "doc_id": "NCT02567214_inc", "case_bucket": "other", "source_criterion": "Age > 50 years Smoking history > 10 packs/year FEV1 30 - 79% of predicted and FEV1/FVC < 70% (GOLD 2-3) FRC > 120 % predicted Borg dyspnea score > 3 during the 3-min constant rate shuttle walking test at V3", "candidate_expression": "((Age > 50 years) AND (Borg dyspnea score > 3 3-min constant rate shuttle walking test) AND (FEV1 30 - 79% of predicted) AND (FEV1/FVC < 70%) AND (FRC > 120 % predicted) AND (GOLD 2-3) AND (Smoking history > 10 packs/year))"}
{"candidate_id": "LLM00139", "doc_id": "NCT03380429_exc", "case_bucket": "or", "source_criterion": "Subjects with a known or suspected alcohol or drug abuse which in the opinion of the investigator could interfere with the subject's proper completion of the protocol requirement. History of life threatening asthma: Defined as an asthma episode that required intubation and/or was associated with hypercapnea, respiratory arrest or hypoxic seizures within the last 6 months. A lower respiratory tract infection within 7 days of the screening visit. Concurrent diagnosis of chronic obstructive pulmonary disease (COPD) or other respiratory disorders including active tuberculosis, lung cancer, bronchiectasis, sarcoidosis, lung fibrosis, pulmonary hypertension, interstitial lung diseases or other active pulmonary diseases. History of hypersensitivity/intolerance to any components of the study inhalers (example, lactose, magnesium stearate). In addition, subjects with a history of severe milk protein allergy that, in the opinion of the study physician, contraindicates participation will also be excluded. Historical or current evidence of clinically significant or rapidly progressing or unstable cardiovascular, neurological, cardiovascular, neurological, renal, hepatic, immunological, endocrine (including uncontrolled diabetes or thyroid disease) or hematological abnormalities that are uncontrolled. Significant is defined as any disease that, in the opinion of the investigator, would put the safety of the subject at risk through participation, or which would affect the analysis if the disease/condition exacerbated during the study. Subjects who have ever received treatment with biological based therapy example, omalizumab, mepolizumab, for asthma. Subjects who have received an investigational drug and/or medical device within 30 days of entry into this study (Screening), or within five drug half-lives of the investigational drug, whichever is longer. A subject will not be eligible for this study if he/she is an immediate family member of the participating investigator, sub-investigator, study coordinator, employee of the participating investigator, or any family member of a Propeller Health employee.", "candidate_expression": "((Subjects who have received an investigational drug and/or medical device within 30 days of entry into this study (Screening), or within five drug half-lives of the investigational drug, whichever is longer.) AND (Subjects with a known or suspected alcohol or drug abuse which in the opinion of the investigator could interfere with the subject's proper completion of the protocol requirement.) AND (allergy history severe) AND (asthma episode required intubation) AND (asthma life threatening) AND (components of the study inhalers) AND (contraindicates participation) AND (intubation) AND (lower respiratory tract infection within 7 days of the screening visit screening visit) AND (lung cancer) AND (milk protein) AND (treatment) AND (tuberculosis active) AND ((chronic obstructive pulmonary disease (COPD)) OR (respiratory disorders other)) AND ((bronchiectasis) OR (interstitial lung diseases) OR (lung fibrosis) OR (pulmonary diseases other active) OR (pulmonary hypertension) OR (sarcoidosis)) AND ((hypersensitivity) OR (intolerance)) AND ((lactose) OR (magnesium stearate)) AND ((clinically significant) OR (rapidly progressing) OR (unstable)) AND ((cardiovascular abnormalities) OR (endocrine abnormalities) OR (hematological abnormalities) OR (hepatic abnormalities) OR (immunological abnormalities) OR (neurological abnormalities) OR (renal abnormalities)) AND ((diabetes) OR (thyroid disease)) AND ((Historical) OR (current)) AND ((hypercapnea) OR (hypoxic seizures) OR (respiratory arrest)) AND ((asthma) OR (mepolizumab) OR (omalizumab)))"}
{"candidate_id": "LLM00140", "doc_id": "NCT02825290_inc", "case_bucket": "other", "source_criterion": "20-40 years old women Spontaneously ovulating women Treated in our IVF unit for frozen-thawed embryo transfer At least one top quality embryo", "candidate_expression": "((Spontaneously ovulating) AND (frozen-thawed embryo transfer) AND (old 20-40 years) AND (our IVF unit) AND (top quality embryo At least one) AND (women))"}
{"candidate_id": "LLM00141", "doc_id": "NCT03118232_exc", "case_bucket": "other", "source_criterion": "Nursing homes will not be eligible to participate if they meet the following criteria: Facilities routinely using decolonization Dedicated psychiatric nursing homes Facilities with a resident population with >=20% combative patients Pediatric facilities", "candidate_expression": "((Nursing homes) AND (Pediatric facilities) AND (combative patients) AND (decolonization routinely) AND (psychiatric nursing homes) AND (resident population >=20%))"}
{"candidate_id": "LLM00142", "doc_id": "NCT02897856_exc", "case_bucket": "or", "source_criterion": "Cardiac arrest Head trauma Drowning Congenital heart disease Inborn errors of metabolism Electrolyte imbalance (hypocalcaemia, hyponatremia and hypoglycemia) Hemodynamic instability Allergy to benzodiazepines Focal seizures with preserved level of consciousness", "candidate_expression": "((Allergy) AND (Cardiac arrest) AND (Congenital heart disease) AND (Drowning) AND (Electrolyte imbalance) AND (Focal seizures) AND (Head trauma) AND (Hemodynamic instability) AND (Inborn errors of metabolism) AND (benzodiazepines) AND (preserved level of consciousness) AND ((hypocalcaemia) OR (hypoglycemia) OR (hyponatremia)))"}
{"candidate_id": "LLM00143", "doc_id": "NCT01911650_exc", "case_bucket": "or", "source_criterion": "1. bilateral AT 2. insertional AT 3. local steroid injection within 6 weeks or physical therapy within 4 weeks 4. inability to comply with follow-up criteria 5. history of surgery on the Achilles tendon or systemic diseases (general inflammatory diseases such as rheumatologic disorders and diabetes) 6. daily use of opioids for pain 7. anticoagulation or immunosuppressive therapy 8. intent to use NSAIDs or steroids 9. self-reported pregnancy", "candidate_expression": "((bilateral AT) AND (general inflammatory diseases) AND (inability to comply with follow-up criteria) AND (insertional AT) AND (opioids daily) AND (pain) AND (pregnancy) AND (surgery on the Achilles tendon history) AND (systemic diseases) AND ((diabetes) OR (rheumatologic disorders)) AND ((anticoagulation therapy) OR (immunosuppressive therapy)) AND ((NSAIDs) OR (steroids)) AND ((local steroid injection within 6 weeks) OR (physical therapy within 4 weeks)))"}
{"candidate_id": "LLM00144", "doc_id": "NCT02833116_inc", "case_bucket": "or", "source_criterion": "Unilateral leg pain secondary to lateral stenosis, disc protrusion or herniated disc. Age between 18 and 80 years. Moderate to severe pain (NVS>4). Right proficient oral and written language.", "candidate_expression": "((>4)) AND (Age) AND (NVS) AND (Right proficient oral and written language) AND (Unilateral leg pain) AND (between 18 and 80 years) AND (pain) AND ((Moderate) OR (severe)) AND ((disc protrusion) OR (herniated disc) OR (lateral stenosis)))"}
{"candidate_id": "LLM00145", "doc_id": "NCT00752310_exc", "case_bucket": "or", "source_criterion": "No positive HIV 1 or HIV 2 test at screening no history of significant skin disease such as, but not limited to rash or eruptions, drug allergies, food allergy, dermatitis, eczema, psoriasis, or urticaria no history of allergy to drugs such as, but not limited to, sulphonamides and penicillins no previously demonstrated clinically significant allergy or hypersensitivity to any of the excipients of the investigational medication administered in this trial no female subject of childbearing potential without use of effective nonhormonal birth control methods, or not willing to continue practicing these birth control methods for at least 30 days after the end of the treatment period no positive pregnancy test or breast feeding at screening", "candidate_expression": "((allergy) AND (at screening) AND (childbearing potential) AND (clinically significant) AND (effective) AND (excipients of the investigational medication) AND (female) AND (for at least 30 days after the end of the treatment period) AND (history) AND (not) AND (positive) AND (previously) AND (screening) AND (significant) AND (skin disease) AND (the end of the treatment period) AND (willing to continue practicing) AND (without) AND ((dermatitis) OR (drug allergies) OR (eczema) OR (eruptions) OR (food allergy) OR (psoriasis) OR (rash) OR (urticaria)) AND ((HIV 1 test) OR (HIV 2 test)) AND ((penicillins) OR (sulphonamides)) AND ((breast feeding) OR (pregnancy test)) AND ((allergy) OR (hypersensitivity)) AND ((birth control methods) OR (nonhormonal birth control)))"}
{"candidate_id": "LLM00146", "doc_id": "NCT01175044_exc", "case_bucket": "other", "source_criterion": "Inability to provide informed consent or to comply with study assessments (e.g. due to cognitive impairment or geographic distance). Age = 17. Allergy to povidone iodine. Any condition requiring antibiotics 14 days prior to arriving for surgery. Patients with chronic immunosuppression (such as HIV/AIDS). Unable to adhere to follow up schedule and treatment. Patients scheduled to undergo revision total knee arthroplasty for infectious reasons.", "candidate_expression": "((Age = 17) AND (Allergy) AND (HIV/AIDS) AND (Inability to provide informed consent or to comply with study assessments (e.g. due to cognitive impairment or geographic distance).) AND (Unable to adhere to follow up schedule and treatment.) AND (antibiotics 14 days prior to arriving for surgery) AND (immunosuppression chronic) AND (infectious reasons) AND (povidone iodine) AND (revision total knee arthroplasty) AND (surgery))"}
{"candidate_id": "LLM00147", "doc_id": "NCT01483118_inc", "case_bucket": "or", "source_criterion": "Patients aged greater than 18 years of age Ability to understand and willingness to comply with the study protocol Written informed consent Patients meeting the Rotterdam PCOS workshop criteria for polycystic ovary syndrome, defined by oligomenorrhea or amenorrhea and at least one of the following two signs: clinical or biochemical evidence of hyperandrogenism or ultrasound finding of polycystic appearing ovaries.", "candidate_expression": "((Ability to understand and willingness to comply with the study protocol) AND (Rotterdam PCOS workshop criteria for polycystic ovary syndrome meeting at least one) AND (Written informed consent) AND (polycystic ovaries) AND ((amenorrhea) OR (oligomenorrhea)) AND ((hyperandrogenism) OR (ultrasound)) AND ((age greater than 18 years) OR (aged greater than 18 years)))"}
{"candidate_id": "LLM00148", "doc_id": "NCT03015818_exc", "case_bucket": "other", "source_criterion": "Inability to give informed consent Pregnancy Concurrent antibiotherapy Certain infectious endocarditis Concurrent anti-inflammatory therapy, including corticosteroid therapy", "candidate_expression": "((Certain) AND (Concurrent) AND (Inability to give informed consent) AND (Pregnancy) AND (anti-inflammatory) AND (anti-inflammatory therapy) AND (antibiotherapy) AND (corticosteroid) AND (corticosteroid therapy) AND (infectious endocarditis))"}
{"candidate_id": "LLM00149", "doc_id": "NCT01116882_exc", "case_bucket": "or", "source_criterion": "1. The patient is pregnant or breastfeeding. 2. Evidence of STEMI within 72 hours of the intended treatment on infarct related or non-infarct related artery. 3. Cardiogenic shock on presentation or during current hospitalization. 4. Left ventricular ejection fraction less than 20%. 5. Known allergies to: aspirin, clopidogrel (Plavix) and ticlopidine (Ticlid), heparin, bivalirudin, stainless steel, or contrast agent (which cannot be adequately premedicated). 6. A platelet count less than 75,000 cells/mm3 or greater than 700,000 cells/mm3 or a WBC less than 3,000 cells/mm3. 7. Acute or chronic renal dysfunction (creatinine greater than 2.5 mg/dl or less than 150µmol/L). 8. Subject is currently participating in an investigational drug or device study that has not completed the primary endpoint or that clinically interferes with the current study endpoints. (Note: Trials requiring extended follow-up for products that were investigational, but have since become commercially available, are not considered investigational trials). 9. Prior participation in this study. 10. Within 30 days prior to the index study procedure, the subject has undergone a previous coronary interventional procedure of any kind. Note: This exclusion criterion does not apply to post-STEMI patients. 11. Stroke or transient ischemic attack within the prior 3 months. 12. Active peptic ulcer or upper gastrointestinal bleeding within the prior 3 months. 13. Subject has active sepsis. 14. Unprotected left main coronary artery disease (stenosis greater than 50%). 15. In the investigator's opinion, subject has a co-morbid condition(s) that could limit the life expectancy to less than one year, or limit the subject's ability to participate in the study or comply with follow-up requirements or impact the scientific integrity of the study. 16. Subject has normal or insignificant coronaries (i.e. coronary lesion(s) less than 50% stenosis). 17. Any target vessel has evidence of: excessive thrombus (e.g. requires target vessel thrombectomy) tortuousity (greater than 60 degree angle) that makes it unsuitable for proper stent delivery and deployment, heavy calcification. 18. Any target lesion requires treatment with a device other than percutaneous transluminal coronary angioplasty (PTCA) prior to stent placement (e.g. but not limited to, directional coronary atherectomy, excimer laser, rotational atherectomy, etc.). 19. Any lesion that is located in a saphenous vein graft, however, lesions located within the native vessel but accessed through the graft are eligible. 20. The target vessel is in a \"last remaining\" epicardial vessel (e.g. greater than 2 non-target epicardial vessels and the bypass grafts to these territories [if present] are totally occluded).", "candidate_expression": "((Active) AND (Cardiogenic shock) AND (In the investigator's opinion) AND (In the investigator's opinion, subject has a co-morbid condition(s) that could limit the life expectancy to less than one year, or limit the subject's ability to participate in the study or comply with follow-up requirements or impact the scientific integrity of the study.) AND (Left ventricular ejection fraction) AND (STEMI) AND (Subject is currently participating in an investigational drug or device study that has not completed the primary endpoint or that clinically interferes with the current study endpoints. (Note: Trials requiring extended follow-up for products that were investigational, but have since become commercially available, are not considered investigational trials).) AND (Unprotected) AND (Within 30 days prior to the index study procedure) AND (active) AND (allergies) AND (angle) AND (calcification) AND (coronary interventional procedure) AND (coronary lesion) AND (creatinine) AND (current) AND (device other than percutaneous transluminal coronary angioplasty (PTCA)) AND (greater than 50%) AND (greater than 60 degree) AND (heavy) AND (hospitalization) AND (left main coronary artery disease) AND (lesion) AND (less than 20%) AND (less than 3,000 cells/mm3) AND (less than 50% stenosis) AND (less than one year) AND (life expectancy) AND (located in a saphenous vein graft) AND (not) AND (other than) AND (percutaneous transluminal coronary angioplasty (PTCA)) AND (previous) AND (prior to stent placement) AND (requires) AND (saphenous vein graft) AND (sepsis) AND (stenosis) AND (stent delivery and deployment) AND (stent placement) AND (target lesion) AND (target vessel thrombectomy) AND (the index study procedure) AND (thrombus) AND (tortuousity) AND (treatment) AND (unsuitable for proper) AND (within 72 hours) AND (within the prior 3 months) AND ((Plavix) OR (Ticlid) OR (aspirin) OR (bivalirudin) OR (clopidogrel) OR (contrast agent) OR (heparin) OR (stainless steel) OR (ticlopidine)) AND ((breastfeeding) OR (pregnant)) AND ((greater than 700,000 cells/mm3) OR (less than 75,000 cells/mm3)) AND ((WBC) OR (platelet count)) AND ((Acute renal dysfunction) OR (chronic renal dysfunction)) AND ((greater than 2.5 mg/dl) OR (less than 150µmol/L)) AND ((Stroke) OR (transient ischemic attack)) AND ((infarct related artery) OR (non-infarct related artery)) AND ((peptic ulcer) OR (upper gastrointestinal bleeding)) AND ((directional coronary atherectomy) OR (excimer laser) OR (rotational atherectomy)) AND ((accessed through the graft) OR (within the native vessel)))"}
{"candidate_id": "LLM00150", "doc_id": "NCT01929434_inc", "case_bucket": "other", "source_criterion": "Patients with diagnosis of cerebral palsy. Patients' curator must be able to give voluntary consent.", "candidate_expression": "((Patients' curator must be able to give voluntary consent) AND (cerebral palsy))"}
```
