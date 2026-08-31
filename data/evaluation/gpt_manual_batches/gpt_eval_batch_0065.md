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
{"candidate_id": "LLM01601", "doc_id": "NCT02365870_exc", "case_bucket": "other", "source_criterion": "Unstable medical disease of comorbid psychiatric disease Dementia Subjects with less than one year duration of Parkinson's Current treatment with a dopamine agonist", "candidate_expression": "((Dementia) AND (Parkinson's less than one year duration) AND (Unstable medical disease) AND (comorbid psychiatric disease) AND (dopamine agonist Current))"}
{"candidate_id": "LLM01602", "doc_id": "NCT01909934_inc", "case_bucket": "or", "source_criterion": "Male or female patients age 18 years or older, with relapsed or refractory sALCL who have previously received at least 1 multiagent chemotherapy Bidimensional measurable disease An Eastern Cooperative Oncology Group (ECOG) performance status of 0 or 1 Female patients who are postmenopausal for at least 1 year before the screening visit, surgically sterile, or agree to practice 2 effective methods of contraception, at the same time, from the time of signing the informed consent form through 30 days after the last dose of study drug, or agree to practice true abstinence Male patients who agree to practice effective barrier contraception during the entire study treatment period through 6 months after the last dose of study drug or agree to practice true abstinence Clinical laboratory values as specified in the study protocol", "candidate_expression": "((ECOG) AND (Eastern Cooperative Oncology Group performance status 0 or 1) AND (Female patients who are postmenopausal for at least 1 year before the screening visit, surgically sterile, or agree to practice 2 effective methods of contraception, at the same time, from the time of signing the informed consent form through 30 days after the last dose of study drug, or agree to practice true abstinence) AND (Male patients who agree to practice effective barrier contraception during the entire study treatment period through 6 months after the last dose of study drug or agree to practice true abstinence) AND (age 18 years or older) AND (chemotherapy at least 1) AND (sALCL) AND ((Male) OR (female)) AND ((refractory) OR (relapsed)))"}
{"candidate_id": "LLM01603", "doc_id": "NCT02946892_inc", "case_bucket": "or", "source_criterion": "Informed consent of parent(s) or legal guardian; informed consent or assent of subject as applicable. Male or female children between the ages of 10 and 35 years with congenital heart disease that has been palliated with a Fontan circulation. Ability of perform a maximal exercise test as defined by a respiratory exchange ratio (RER) greater than 1.0 at the time of maximal exercise", "candidate_expression": "((Ability of perform) AND (Fontan circulation) AND (Informed consent of legal guardian) AND (Informed consent of parent) AND (Male) AND (ages) AND (at the time of maximal exercise) AND (between 10 and 35 years) AND (children) AND (congenital heart disease) AND (female) AND (greater than 1.0) AND (informed assent of subject) AND (informed consent of subject) AND (maximal exercise test) AND (respiratory exchange ratio (RER)))"}
{"candidate_id": "LLM01604", "doc_id": "NCT02137369_exc", "case_bucket": "or", "source_criterion": "Lifetime history of Bipolar Disorder, Dementia, Autism Spectrum Disorder, Schizophrenia, or any other Psychotic Disorder. Psychotic symptoms occurring at any time during the current major depressive episode. Current (past 12 months) diagnosis of Panic disorder, Obsessive Compulsive Disorder, Posttraumatic Stress Disorder, Anorexia Nervosa, or Bulimia Nervosa. Alcohol or Drug Dependence within 12 months or Abuse within 3 months (excluding nicotine and caffeine) of baseline visit, as assessed by history and urine drug screen. Clinical evidence of a severe Personality Disorder, as assessed by the study psychiatrist, which would impede participation or completion of the trial. Known neurological disorders or documented serious head injury. Serious and unstable medical illnesses including cardiovascular disease and cancer. Active medical conditions with known mood changes (endocrine, autoimmune disorders). Current diabetes mellitus. For women, pregnancy, lactation, or unwillingness to comply with birth control requirements. Use of any of the following treatments or any other alternative therapy within 2 weeks of the pre-treatment PET scan that may have beneficial effects on mood, including St John's Wort, S-adenosyl methionine (SAMe), n-3 fatty acids, or light therapy. Use of antidepressant medication within 1 month of the pre-treatment PET scan (within 5 weeks for fluoxetine and protryptyline). Failure to achieve a much improved status (i.e. equivalent to >50% symptom reduction) with any lifetime treatment course of CBT (defined as a minimum of 4 sessions of a specified manual-driven therapy by a CBT-trained therapist) or escitalopram (defined as a minimum of 6 weeks of at least 10 mg/day). Clinically significant active suicidal ideation or self-injurious behavior necessitating immediate treatment, as determined by the investigator. Received electroconvulsive therapy in the past 6 months or during the current depressive episode. Currently responding to medication treatment, without clinical reasons to change. Current treatment with weekly individual or group psychotherapy of any type targeted at depressive symptoms. QTc >500 milliseconds on EKG at screening. Contraindications for MRI, including, but not limited to pacemaker, aneurysm clips, neurostimulators, cochlear implants, metal in eyes, steel worker, intra-uterine devices for birth control. Maintenance or prophylactic therapy for stable medical conditions. Hypnotic medication prescribed or approved by the study physician, (up to a three doses per week) for insomnia, as long if not the night before a PET/MRI or clinic ratings visit. Antipsychotic medications, whether prescribed for sleep or other indications, are prohibited.", "candidate_expression": "((>500 milliseconds) AND (Antipsychotic medications) AND (Contraindications) AND (EKG) AND (For women, pregnancy, lactation, or unwillingness to comply with birth control requirements) AND (Hypnotic medication) AND (MRI) AND (PET scan) AND (Personality Disorder) AND (Psychotic symptoms) AND (QTc) AND (SAMe) AND (Serious) AND (active) AND (antidepressant medication) AND (at any time during the current major depressive episode) AND (at screening) AND (current) AND (depressive episode) AND (depressive symptoms) AND (diabetes mellitus) AND (electroconvulsive therapy) AND (eyes) AND (fluoxetine) AND (fluoxetine and protryptyline) AND (immediate) AND (insomnia) AND (major depressive episode) AND (medical illnesses) AND (mood) AND (not) AND (past 12 months) AND (pre-treatment) AND (pre-treatment PET scan) AND (protryptyline) AND (psychotherapy) AND (screening) AND (serious) AND (severe) AND (the current depressive episode) AND (the current major depressive episode) AND (the night before a PET/MRI or clinic ratings visit.) AND (treatment) AND (unstable) AND (urine drug screen) AND (weekly) AND (within 1 month of the pre-treatment PET scan) AND (within 12 months) AND (within 2 weeks of the pre-treatment PET scan) AND (within 3 months) AND (within 5 weeks for fluoxetine and protryptyline) AND ((during the current depressive episode) OR (in the past 6 months)) AND ((Anorexia Nervosa) OR (Bulimia Nervosa) OR (Obsessive Compulsive Disorder) OR (Panic disorder) OR (Posttraumatic Stress Disorder)) AND ((Alcohol Dependence) OR (Drug Dependence)) AND ((Alcohol Abuse) OR (Drug Abuse)) AND ((caffeine) OR (nicotine)) AND ((head injury) OR (neurological disorders)) AND ((Autism Spectrum Disorder) OR (Bipolar Disorder) OR (Dementia) OR (Psychotic Disorder) OR (Schizophrenia)) AND ((cancer) OR (cardiovascular disease)) AND ((autoimmune disorders) OR (endocrine disorders)) AND ((alternative therapy) OR (treatments)) AND ((S-adenosyl methionine) OR (St John's Wort) OR (light therapy) OR (n-3 fatty acids)) AND ((self-injurious behavior) OR (suicidal ideation)) AND ((group) OR (individual)) AND ((aneurysm clips) OR (cochlear implants) OR (intra-uterine devices) OR (metal) OR (neurostimulators) OR (pacemaker) OR (steel worker)) AND ((PET/MRI) OR (clinic ratings visit.)))"}
{"candidate_id": "LLM01605", "doc_id": "NCT02590315_inc", "case_bucket": "other", "source_criterion": "Asymptomatic women 45-68 years, residents in the Piedmont Region, attending the regional breast cancer screening program", "candidate_expression": "((45-68 years) AND (Asymptomatic) AND (Piedmont Region) AND (regional breast cancer screening program) AND (women))"}
{"candidate_id": "LLM01606", "doc_id": "NCT03373669_exc", "case_bucket": "or", "source_criterion": "Presence of a significant medical or psychiatric condition (Examples include: Diagnosis and treatment of tuberculosis (TB) or HIV; renal insufficiency; hepatic disease; oral or parenteral medication known to affect the immune function, such as corticosteroids, other immunosuppressant drugs; or behavioural or memory issues) Ever having received oral cholera vaccine. Receipt of an investigational product (within 30 days before vaccination). History of diarrhoea in 7 days prior to first dose of vaccine (defined as =3 unformed loose stools in 24 hours). History of chronic diarrhea (lasting for more than 2 weeks in the past 6 months) Current use of laxatives, antacids, or other agents to lower stomach acidity? Planning to become pregnant in the next 2 years.", "candidate_expression": "((Planning to become pregnant in the next 2 years.) AND (Receipt of an investigational product (within 30 days before vaccination).) AND (chronic diarrhea History lasting for more than 2 weeks in the past 6 months) AND (diarrhoea History in 7 days prior to first dose of vaccine) AND (oral cholera vaccine) AND (unformed loose stools in 24 hours =3) AND ((oral medication) OR (parenteral medication)) AND ((corticosteroids) OR (immunosuppressant drugs other)) AND ((behavioural issues) OR (memory issues)) AND ((medical condition) OR (psychiatric condition)) AND ((agents to lower stomach acidity other) OR (antacids) OR (laxatives)) AND ((HIV) OR (hepatic disease) OR (renal insufficiency) OR (treatment) OR (tuberculosis (TB))))"}
{"candidate_id": "LLM01607", "doc_id": "NCT02827526_exc", "case_bucket": "or", "source_criterion": "Preoperative renal failure (defined as a serum creatinine > 2.0 mg/dL.) American Society of Anesthesiologists Physical Status IV or V Pulmonary disease necessitating home oxygen therapy Allergy to methadone, hydromorphone, or ketamine Preoperative recent history of opioid or alcohol abuse Significant liver disease Inability to use a PCA device or speak the English language", "candidate_expression": "((American Society of Anesthesiologists Physical Status IV or V) AND (PCA device) AND (Pulmonary disease) AND (home oxygen therapy) AND (hydromorphone) AND (ketamine) AND (liver disease Significant) AND (methadone) AND (renal failure Preoperative) AND (serum creatinine > 2.0 mg/dL) AND ((alcohol abuse) OR (opioid abuse)) AND ((Inability to speak the English language) OR (Inability to use)))"}
{"candidate_id": "LLM01608", "doc_id": "NCT02872935_inc", "case_bucket": "other", "source_criterion": "Pregnant American Society of Anesthesiologists risk classification I and II Age > 18 years Non-laboring Patients with elective cesarean sections", "candidate_expression": "((Age > 18 years Non-laboring) AND (American Society of Anesthesiologists risk classification I and II) AND (Pregnant) AND (cesarean sections elective))"}
{"candidate_id": "LLM01609", "doc_id": "NCT01768195_inc", "case_bucket": "other", "source_criterion": "treatment-naive patients with B-cell lymphoma HBsAg positive at baseline treated with rituximab-based immunochemotherapy life expectancy of more than 3 months", "candidate_expression": "((B-cell lymphoma) AND (HBsAg positive) AND (at baseline) AND (immunochemotherapy) AND (life expectancy) AND (more than 3 months) AND (naive) AND (rituximab) AND (rituximab-based) AND (treatment))"}
{"candidate_id": "LLM01610", "doc_id": "NCT02478346_exc", "case_bucket": "other", "source_criterion": "NA", "candidate_expression": "(EMPTY)"}
{"candidate_id": "LLM01611", "doc_id": "NCT03068897_exc", "case_bucket": "or", "source_criterion": "Not available for follow-up Pregnant or breast-feeding Chronic pain syndrome defined as use of any analgesic medication on a daily or near-daily basis Allergic to or intolerant of investigational medications Contra-indications to non-steroidal anti-inflammatory drugs: 1) history of hypersensitivity to NSAIDs or aspirin 2) active or history of peptic ulcer disease, chronic dyspepsia, or active or history of gastrointestinal bleed 3) Severe heart failure (NYHA 2 or worse) 4) hypertension (JNC7 stage 2 or worse) 5) Chronic kidney disease 3 or worse 6) Current use of anti-coagulants 7) Hepatitis 8) Alcoholism Contra-indications to muscle relaxants: 1) Concurrent use of centrally acting opioids; 2) Renal impairment; 3) Liver abnormality including cirrhosis or elevated enzymes 4) Use of any of the following medications: fluvoxamine, fluoroquinolones, amiodarone, mexiletine, propafenone, verapamil, cimetidine, famotidine, acyclovir, ticlopidine, oral contraceptive pills", "candidate_expression": "((Chronic pain syndrome) AND (Contra-indications) AND (JNC7 stage 2 or worse) AND (NYHA 2 or worse) AND (analgesic medication any) AND (investigational medications) AND (muscle relaxants) AND (non-steroidal anti-inflammatory drugs) AND ((Allergic) OR (intolerant)) AND ((NSAIDs) OR (aspirin)) AND ((Pregnant) OR (breast-feeding)) AND ((active) OR (history)) AND ((chronic dyspepsia) OR (peptic ulcer disease)) AND ((Alcoholism) OR (Chronic kidney disease) OR (Hepatitis) OR (anti-coagulants Current) OR (gastrointestinal bleed) OR (heart failure Severe) OR (hypersensitivity history) OR (hypertension)) AND ((Liver abnormality) OR (Renal impairment) OR (centrally acting opioids Concurrent)) AND ((cirrhosis) OR (elevated enzymes)) AND ((acyclovir) OR (amiodarone) OR (cimetidine) OR (famotidine) OR (fluoroquinolones) OR (fluvoxamine) OR (mexiletine) OR (oral contraceptive pills) OR (propafenone) OR (ticlopidine) OR (verapamil)) AND ((on a daily basis) OR (on a near-daily basis)))"}
{"candidate_id": "LLM01612", "doc_id": "NCT03407625_inc", "case_bucket": "or", "source_criterion": "37 weeks gestation or greater Living, singleton fetus No major fetal malformations Cephalic presentation No prior uterine scar Intact fetal membranes Qualifies for prostaglandin administration according to current Parkland protocol Have a cervical dilation of 2 centimeters or less, measured at the level of the internal os Have an indication for induction or attempted induction of labor according to Parkland protocol", "candidate_expression": "((2 centimeters or less) AND (37 weeks greater) AND (Cephalic presentation) AND (Intact) AND (Living) AND (No) AND (Parkland protocol) AND (attempted) AND (cervical dilation) AND (fetal membranes) AND (gestation) AND (indication) AND (induction) AND (induction of labor) AND (internal os) AND (major fetal malformations) AND (prostaglandin administration) AND (singleton fetus) AND (uterine scar))"}
{"candidate_id": "LLM01613", "doc_id": "NCT03132259_inc", "case_bucket": "other", "source_criterion": "Age18-65 ASA 1-2 Elective TNTS resection of Pituitary Tumor No narcotic before surgery as premedication Able to Extubate", "candidate_expression": "((ASA 1-2) AND (Age 18-65) AND (Extubate Able to) AND (Pituitary Tumor) AND (TNTS resection Elective) AND (surgery) AND NOT (narcotic before surgery))"}
{"candidate_id": "LLM01614", "doc_id": "NCT02926235_inc", "case_bucket": "other", "source_criterion": "All patients will be undergoing a primary unilateral total knee arthroplasty for a diagnosis of osteoarthritis", "candidate_expression": "((osteoarthritis) AND (primary) AND (unilateral total knee arthroplasty))"}
{"candidate_id": "LLM01615", "doc_id": "NCT01774019_inc", "case_bucket": "or", "source_criterion": "Age 18 or older Willing and able to comply with the study procedures and provide written informed consent to participate in the study Diagnosis of probable pancreatic cancer, distal common bile duct (CBD) cholangiocarcinoma and other periampullary cancers (histology not required) Biliary obstructive symptoms or signs Bilirubin level at/above 100 umol per liter (5.8 mg/dL) Distal biliary obstruction consistent with pancreatic cancer, distal CBD cholangiocarcinoma or other periampullary malignancy Location of distal biliary obstruction is such that it would allow the proximal end of a stent to be positioned at least 2cm from the hilum Patients deemed as resectable by pancreatic protocol CT or MRI Surgical candidate per pancreatobiliary surgeon after multi-disciplinary discussion Surgery intent within 4 weeks Endoscopic and surgical treatment to be provided by same team", "candidate_expression": "((Age 18 or older) AND (Biliary obstructive signs) AND (Biliary obstructive symptoms) AND (Bilirubin level at/above 100 umol per liter at/above 5.8 mg/dL) AND (Distal biliary obstruction) AND (Endoscopic treatment) AND (Surgery intent within 4 weeks) AND (Surgical candidate per pancreatobiliary surgeon) AND (deemed as resectable) AND (distal CBD cholangiocarcinoma) AND (distal biliary obstruction) AND (distal common bile duct (CBD) cholangiocarcinoma) AND (pancreatic cancer) AND (pancreatic protocol CT) AND (pancreatic protocol MRI) AND (periampullary cancers other) AND (periampullary malignancy other) AND (stent would allow at least 2cm from the hilum) AND (surgical treatment))"}
{"candidate_id": "LLM01616", "doc_id": "NCT02944292_exc", "case_bucket": "other", "source_criterion": "Contraindication for propofol administration Contraindication for IAP measurement in supine position with head-of-bed at 0° Other intervention for reduction of IAP planned Previous propofol infusion rate >4 mg/kg/h", "candidate_expression": "((>4 mg/kg/h) AND (Contraindication) AND (IAP measurement) AND (Other) AND (Previous) AND (head-of-bed at 0°) AND (intervention for reduction of IAP) AND (planned) AND (propofol) AND (propofol infusion rate) AND (supine position))"}
{"candidate_id": "LLM01617", "doc_id": "NCT03476850_inc", "case_bucket": "other", "source_criterion": "Patients undergoing laparoscopic assisted donor nephrectomy Patients that have elected to have a nerve block 18 years of age or older Patients of ASA status I - III", "candidate_expression": "((18 years or older) AND (ASA status) AND (I - III) AND (age) AND (elected to have) AND (laparoscopic assisted donor nephrectomy) AND (nerve block))"}
{"candidate_id": "LLM01618", "doc_id": "NCT03228238_exc", "case_bucket": "other", "source_criterion": "NA", "candidate_expression": "(EMPTY)"}
{"candidate_id": "LLM01619", "doc_id": "NCT02789111_inc", "case_bucket": "other", "source_criterion": "Major spine surgery scheduled as part of clinical care 18-80 years", "candidate_expression": "((Major spine surgery) AND (years 18-80))"}
{"candidate_id": "LLM01620", "doc_id": "NCT03479502_inc", "case_bucket": "other", "source_criterion": "18 years of age and older, diagnosis of stage II adhesive capsulitis as determined by clinical examination of the treating physician, and absence of abnormal findings on X-ray.", "candidate_expression": "((X-ray) AND (adhesive capsulitis stage II as determined by clinical examination) AND (age 18 years and older) AND (clinical examination) AND NOT (abnormal findings))"}
{"candidate_id": "LLM01621", "doc_id": "NCT03373318_exc", "case_bucket": "other", "source_criterion": "Patients who do not meet the inclusion criteria and those who have a history of allergic reactions to human albumin, as well as those who have received iodinated contrast during the 7 days prior to surgery and pregnant women, will be excluded from the study.", "candidate_expression": "((allergic) AND (during the 7 days prior to surgery) AND (history) AND (human albumin) AND (iodinated contrast) AND (meet the inclusion criteria) AND (not) AND (pregnant) AND (surgery) AND (women))"}
{"candidate_id": "LLM01622", "doc_id": "NCT02526823_inc", "case_bucket": "or", "source_criterion": "Primary B-NHL, PTCL (ALK+ anaplastic large cell lymphoma and NK(natural killer cell )/T cell lymphoma were excluded) or HL patients confirmed by histopathology; Ages =18 years old, < 80 years old; ECOG (Eastern Cooperative Oncology Group)score: 0-2 At least one measurable lesion; Expected survival time=3 months; Liver function: transaminase=2.5× upper limit of normal value,bilirubin=1.5×upper limit of normal value; Renal function: serum creatinine is 44-133 mmol/L; Routine blood test:WBC=3.0×109/L,Neutrophils=1.5×109/L,Hb=100g/L,Platelet=80×109/L; LVEF=50%; New York Heart Association (NYHA) heart function classification is I-II grade signed informed consent.", "candidate_expression": "((0-2) AND (3 months) AND (44-133 mmol/L) AND (=1.5×109/L) AND (=1.5×upper limit of normal value) AND (=100g/L) AND (=18 years old, < 80 years old) AND (=2.5× upper limit of normal value) AND (=3.0×109/L) AND (=50%) AND (=80×109/L) AND (ALK+ anaplastic large cell lymphoma and NK(natural killer cell )/T cell lymphoma) AND (Ages) AND (At least one) AND (ECOG (Eastern Cooperative Oncology Group)score) AND (Expected survival time=) AND (Hb) AND (I-II grade) AND (LVEF) AND (NYHA) AND (Neutrophils) AND (New York Heart Association heart function classification) AND (Platelet) AND (bilirubin) AND (excluded) AND (lesion) AND (serum creatinine) AND (signed informed consent) AND (test:WBC) AND (transaminase) AND ((HL) OR (PTCL) OR (Primary B-NHL)))"}
{"candidate_id": "LLM01623", "doc_id": "NCT02877485_inc", "case_bucket": "other", "source_criterion": "Age greater than 18 NOSE score greater than 55 Nasal septal deviation on exam", "candidate_expression": "((Age greater than 18) AND (NOSE score greater than 55) AND (Nasal septal deviation))"}
{"candidate_id": "LLM01624", "doc_id": "NCT03249311_inc", "case_bucket": "other", "source_criterion": "Male participants between 18 and 40 years-old Written informed consent signed by the participant", "candidate_expression": "((Male) AND (Written informed consent signed by the participant) AND (between 18 and 40 years) AND (old))"}
{"candidate_id": "LLM01625", "doc_id": "NCT03113253_inc", "case_bucket": "or", "source_criterion": "Subjects undergoing burn excision surgery for standard of care purposes Male or female >= 18 years of age Subject or subject's medical decision maker agrees to participate in this study and provides informed consent", "candidate_expression": "((>= 18 years) AND (Male) AND (Subject or subject's medical decision maker agrees to participate in this study and provides informed consent) AND (age) AND (burn excision surgery) AND (female) AND (undergoing))"}
```
