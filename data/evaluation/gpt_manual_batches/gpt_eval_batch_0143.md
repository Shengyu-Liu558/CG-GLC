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
{"candidate_id": "LLM03551", "doc_id": "NCT02209545_exc", "case_bucket": "or", "source_criterion": "Patients who have had a prior abdominal myomectomy Post-menopausal women Patients with known bleeding/clotting disorders Patients with a history of gynecologic malignancy History of allergic reactions attributed to compounds of similar chemical or biologic composition to misoprostol Any cases converted to abdominal hysterectomy or other additional elective surgical procedures performed at time of abdominal myomectomy will be excluded from data analysis Uncontrolled intercurrent illness including, but not limited to, ongoing or active infection, symptomatic congestive heart failure, unstable angina pectoris, cardiac arrhythmia, or psychiatric illness/social situations that would limit compliance with study requirements.", "candidate_expression": "((History) AND (Post-menopausal) AND (Uncontrolled) AND (abdominal myomectomy) AND (additional) AND (allergic reactions) AND (at time of abdominal myomectomy) AND (compounds of similar chemical or biologic composition to misoprostol) AND (converted to) AND (elective) AND (gynecologic malignancy) AND (history) AND (intercurrent illness) AND (misoprostol) AND (other) AND (prior) AND (symptomatic) AND (women) AND ((abdominal hysterectomy) OR (surgical procedures)) AND ((active) OR (ongoing)) AND ((cardiac arrhythmia) OR (congestive heart failure) OR (infection) OR (psychiatric illness) OR (social situations that would limit compliance with study requirements) OR (unstable angina pectoris)) AND ((clotting disorders) OR (disorders bleeding)))"}
{"candidate_id": "LLM03552", "doc_id": "NCT03328052_inc", "case_bucket": "or", "source_criterion": "Patients with a clinical diagnosis of depression who in the judgement of their physician require medication management may be eligible for enrollment. A score of 10 or more on the PHQ-9 instrument will be required for enrollment. Some practices utilize the PHQ-2 and PHQ-9 are part of routine screening for depression. If the tests are performed routinely, they do not need to be repeated for study eligibility, and may be performed prior to informed consent for this study. If, however, the PHQ-9 is not routinely performed, informed consent must be performed prior to administration. Patients with a score below 10 will be considered screen failures and will not be enrolled or offered the MYnd testing. Patients with non-psychotic comorbid conditions may be included. Patients must be either medication treatment naïve for behavioral illnesses or have no active medication treatments for at least 1 month prior to enrollment. Prohibited medications at the time of enrollment will include stimulants, benzodiazepines and THC. Prior therapy with these agents is permitted with a washout of >30 days. Patients must have private medical insurance coverage through Horizon Blue Cross Blue Shield. This is limited to insured commercial members, including HMO, and excluding, for the avoidance of doubt, members of self-insured customers or Medicare or Medicaid programs.", "candidate_expression": "((PHQ-9 score of 10 or more) AND (THC) AND (behavioral illnesses) AND (benzodiazepines) AND (depression) AND (medication) AND (non-psychotic conditions) AND (stimulants) AND NOT (medication active for at least 1 month prior to enrollment) AND NOT (medication))"}
{"candidate_id": "LLM03553", "doc_id": "NCT03323047_exc", "case_bucket": "or", "source_criterion": "Patients Level III or greater on the American Society of Anesthesiologists (ASA) physical status classification system (as determined by the anesthesiologist) Patients with chronic conditions that would limit our ability to develop the study according to objectives, such as neurodevelopmental conditions preventing patients from understanding the Oucher tool Hepatic or renal disease cardiac disease active infection diabetes mellitus sickle cell disease known coagulation disorders pre- operative treatment with anti-emetics, steroids, or analgesics Acetaminophen allergy or already receiving acetaminophen within 24 h of surgery Complicating health factors precluding the use of opioids or acetaminophen any other factors which would interfere with pain assessment and management Patients weighing more than 30 kg that would exceed maximum dexamethasone dose Patients who live without a home telephone patient living without parental supervision.", "candidate_expression": "((Acetaminophen) AND (American Society of Anesthesiologists (ASA) physical status) AND (Complicating health factors) AND (Level III or greater) AND (active) AND (cardiac disease) AND (chronic conditions) AND (coagulation disorders) AND (diabetes mellitus) AND (infection) AND (interfere) AND (limit our ability to develop the study according to objectives) AND (more than 30 kg) AND (neurodevelopmental conditions) AND (other factors) AND (pre- operative) AND (precluding) AND (preventing) AND (sickle cell disease) AND (treatment) AND (understanding the Oucher tool) AND (weighing) AND (within 24 h of surgery) AND ((Hepatic disease) OR (renal disease)) AND ((analgesics) OR (anti-emetics) OR (steroids)) AND ((acetaminophen) OR (allergy)) AND ((acetaminophen) OR (opioids)) AND ((management) OR (pain assessment)))"}
{"candidate_id": "LLM03554", "doc_id": "NCT02062489_inc", "case_bucket": "or", "source_criterion": "The patients signed the written informed consent The patients present with operable unilateral invasive breast cancers without distant metastasis(stage I, II, and III) The breast tumor's positive ER/PR rate is <1%, and positive ER-beta1 rate is =10% by IHC. The patients have no history of neoadjuvant hormone therapy. The patients have normal cardiac functions by echocardiography. The patients' ECOG scores are =0-2. Female patient who is = 18yrs, and = 65yrs. The patients are non-pregnant, and disposed to practice contraception during the whole trial. The patients underwent neoadjuvant chemotherapy plus surgery or directly modified radical mastectomy or breast-conserving surgery (plus sentinel lymph node biopsy or axillary lymph node dissection) after diagnosis of breast cancer. The patients underwent chemotherapy, radiation therapy or targeted therapy(herceptin) after surgery according to the 2013 NCCN guideline. The results of patients' blood tests are as follows:", "candidate_expression": "((2013 NCCN guideline) AND (<1%) AND (= 18yrs) AND (= 65yrs) AND (=0-2) AND (=10%) AND (ECOG scores) AND (Female) AND (I, II, and III) AND (IHC) AND (The patients are non-pregnant, and disposed to practice contraception during the whole trial.) AND (after diagnosis of breast cancer) AND (after surgery) AND (axillary lymph node dissection) AND (breast cancers) AND (breast tumor) AND (breast-conserving surgery) AND (chemotherapy) AND (diagnosis of breast cancer) AND (directly modified) AND (distant metastasis) AND (echocardiography) AND (herceptin) AND (invasive) AND (neoadjuvant chemotherapy) AND (neoadjuvant hormone therapy) AND (no history) AND (normal cardiac functions) AND (operable) AND (positive ER-beta1 rate) AND (positive ER/PR rate) AND (radiation therapy) AND (radical mastectomy) AND (sentinel lymph node biopsy) AND (stage) AND (surgery) AND (targeted therapy) AND (unilateral) AND (without))"}
{"candidate_id": "LLM03555", "doc_id": "NCT02543710_exc", "case_bucket": "or", "source_criterion": "Patients who will not get surgical treatment for their endometrial cancer Patients not suffering from endometrial or epithelial ovarian cancer Patients who do not agree to the proposed treatment or will receive (part of) the treatment in a non-participating centre Patients who cannot or do not want to give informed consent (including language barriers)", "candidate_expression": "((endometrial cancer) AND (non-participating centre) AND (treatment) AND NOT (surgical treatment) AND NOT (agree to the proposed treatment) AND ((give informed consent) OR (language barriers)) AND ((cannot) OR (do not want to)) AND ((endometrial ovarian cancer) OR (epithelial ovarian cancer)))"}
{"candidate_id": "LLM03556", "doc_id": "NCT02526823_inc", "case_bucket": "or", "source_criterion": "Primary B-NHL, PTCL (ALK+ anaplastic large cell lymphoma and NK(natural killer cell )/T cell lymphoma were excluded) or HL patients confirmed by histopathology; Ages =18 years old, < 80 years old; ECOG (Eastern Cooperative Oncology Group)score: 0-2 At least one measurable lesion; Expected survival time=3 months; Liver function: transaminase=2.5× upper limit of normal value,bilirubin=1.5×upper limit of normal value; Renal function: serum creatinine is 44-133 mmol/L; Routine blood test:WBC=3.0×109/L,Neutrophils=1.5×109/L,Hb=100g/L,Platelet=80×109/L; LVEF=50%; New York Heart Association (NYHA) heart function classification is I-II grade signed informed consent.", "candidate_expression": "((Ages =18 years old, < 80 years old) AND (ECOG (Eastern Cooperative Oncology Group)score 0-2) AND (Expected survival time= 3 months) AND (Hb =100g/L) AND (LVEF =50%) AND (NYHA) AND (Neutrophils =1.5×109/L) AND (New York Heart Association heart function classification I-II grade) AND (Platelet =80×109/L) AND (bilirubin =1.5×upper limit of normal value) AND (lesion At least one) AND (serum creatinine 44-133 mmol/L) AND (signed informed consent) AND (test:WBC =3.0×109/L) AND (transaminase =2.5× upper limit of normal value) AND NOT (ALK+ anaplastic large cell lymphoma and NK(natural killer cell )/T cell lymphoma) AND ((HL) OR (PTCL) OR (Primary B-NHL)))"}
{"candidate_id": "LLM03557", "doc_id": "NCT03472846_inc", "case_bucket": "other", "source_criterion": "Postmenopausal women Age 60-80 years T-score according to DXA: <-2.5 indication for osteoporosis therapy according to international guidelines", "candidate_expression": "((60-80 years) AND (<-2.5) AND (Age) AND (DXA) AND (Postmenopausal) AND (T-score) AND (according to DXA) AND (indication for) AND (international guidelines) AND (osteoporosis) AND (osteoporosis therapy) AND (women))"}
{"candidate_id": "LLM03558", "doc_id": "NCT01980680_inc", "case_bucket": "or", "source_criterion": "Age between 20 and 40 Normal menstrual cycles: 25-34 days Oligomenorrhea/amenorrhea or polycystic syndrome (defined according to the Rotterdam criteria 2004) BMI >18 and <35 kg/m2", "candidate_expression": "((25-34 days) AND (>18 and <35 kg/m2) AND (Age) AND (BMI) AND (Normal menstrual cycles) AND (Oligomenorrhea) AND (Rotterdam criteria 2004) AND (amenorrhea) AND (between 20 and 40) AND (polycystic syndrome))"}
{"candidate_id": "LLM03559", "doc_id": "NCT03154931_exc", "case_bucket": "or", "source_criterion": "Suicidal patients and/or severe automutilation behavior and/or psychotic symptoms and/or lack of event memory.", "candidate_expression": "((Suicidal) AND (automutilation behavior) AND (lack of event memory) AND (psychotic symptoms) AND (severe))"}
{"candidate_id": "LLM03560", "doc_id": "NCT03073603_exc", "case_bucket": "or", "source_criterion": "Any MS relapse in the last five years, as determined at the screen visit by the PI Any new or definitely enlarging T2/FLAIR lesion or new gadolinium-enhancing lesion within the past three years (at least two scans separated by at least three years must be reviewed) on brain or spine MRI scan. Lesions must be 3mm or larger to be exclusionary. Significant (as defined by the PI) intolerance of presently-used DMT Use of inhaled or topical steroids are not an exclusion criteria. Use of oral steroids for no greater than 14 days given for a non-MS condition is not exclusionary. alemtuzumab, mitoxantrone, cyclophosphamide, methotrexate, cyclosporine, or rituximab Prior use of any experimental agent used as a DMT for MS in the last five years uncontrolled hypertension, uncontrolled diabetes, uncontrolled asthma, or uncontrolled depression Cancers other than basal cell skin cancers within the last 5 years Unable to give informed consent or follow the protocol Unable to undergo brain MRI Unwilling to be randomized per this protocol History of other chronic neurological illnesses that might mimic MS with chronic or intermittent symptoms (i.e. ALS, myasthenia gravis, chronic neuropathy, etc.)", "candidate_expression": "((3mm or larger) AND (ALS) AND (Cancers) AND (DMT) AND (History of) AND (Lesions) AND (MS) AND (Significant) AND (T2/FLAIR lesion) AND (Unable to undergo) AND (Unwilling to be randomized per this protocol) AND (alemtuzumab) AND (asthma) AND (at least two) AND (basal cell skin cancers) AND (brain MRI) AND (brain MRI scan) AND (chronic neurological illnesses) AND (chronic neuropathy) AND (cyclophosphamide) AND (cyclosporine) AND (depression) AND (diabetes) AND (gadolinium) AND (gadolinium-enhancing) AND (hypertension) AND (in the last five years) AND (inhaled steroids) AND (intolerance) AND (lesion) AND (methotrexate) AND (mimic MS) AND (mitoxantrone) AND (myasthenia gravis) AND (no greater than 14 days) AND (non-MS condition) AND (not) AND (oral steroids) AND (other than) AND (presently-used) AND (relapse) AND (rituximab) AND (scans) AND (separated by at least three years) AND (spine MRI scan) AND (topical steroids) AND (uncontrolled) AND (within the last 5 years) AND (within the past three years))"}
{"candidate_id": "LLM03561", "doc_id": "NCT01929434_inc", "case_bucket": "other", "source_criterion": "Patients with diagnosis of cerebral palsy. Patients' curator must be able to give voluntary consent.", "candidate_expression": "((Patients' curator must be able to give voluntary consent) AND (cerebral palsy))"}
{"candidate_id": "LLM03562", "doc_id": "NCT02798237_inc", "case_bucket": "or", "source_criterion": "= 20years of age; diagnosis of stroke (>6months); sedentary or insufficiently active; have a writing medical permission to participate in the training program.", "candidate_expression": "((= 20years) AND (>6months) AND (age) AND (stroke) AND ((insufficiently active) OR (sedentary)))"}
{"candidate_id": "LLM03563", "doc_id": "NCT01322464_exc", "case_bucket": "or", "source_criterion": "Subjects were not to have a history or presence of significant cardiovascular, pulmonary, hepatic, renal, haematologic, gastrointestinal, endocrine, immunologic, dermatologic, neurologic, or psychiatric disease. Subjects were not to have any history or presence or family history of schizophrenia, other psychotic illness, severe personality disorder, depression, or other significant psychiatric disorder. Subjects were not to have a postural drop of 20 mmHg or more in systolic blood pressure at screening. Subjects were not to have participated in a previous clinical trial within 90 days prior to study initiation. Subjects were not to have donated plasma within 90 days prior to study initiation. Subjects were not to have donated blood within 90 days prior to study initiation. Subjects were not to have had an abnormal diet or substantial changes in eating habits within 30 days prior to study initiation. Subjects were not to have had treatment with any known enzyme-altering agents (barbiturates, phenothiazines, cimetidine etc.) within 30 days prior to or during the study. Subjects were to have no history of known hypersensitivity or idiosyncratic reaction to the study drug or related compounds. Subjects were not to use any prescription medication within 14 days prior to or during the study. Subjects were not to use any over-the-counter medication within 7 days prior to or during the study. Subjects were not to have a history of alcohol or drug abuse within 2 years prior to the study (subjects with a history of previous use of cannabis were not excluded unless they had used cannabis or cannabinoid based medicine within 30 days prior to study drug administration or were unwilling to abstain for the duration of the study).", "candidate_expression": "((abnormal diet) AND (alcohol abuse) AND (barbiturates) AND (changes in eating habits substantial) AND (cimetidine within 30 days prior to or during the study) AND (depression) AND (drug abuse) AND (enzyme-altering agents) AND (family history) AND (history) AND (not excluded) AND (participated in a previous clinical trial 90 days prior to study initiation) AND (phenothiazines) AND (presence) AND (psychiatric disorder significant) AND (psychotic illness) AND (schizophrenia) AND (severe personality disorder) AND (study drug) AND (systolic blood pressure postural drop of 20 mmHg at screening) AND (use of cannabis) AND NOT (donated plasma within 90 days prior to study initiation) AND NOT (donated blood within 90 days prior to study initiation) AND NOT (hypersensitivity) AND NOT (idiosyncratic reaction) AND NOT (prescription medication within 14 days prior to the study during the study) AND NOT (over-the-counter medication within 7 days prior to the study during the study the study))"}
{"candidate_id": "LLM03564", "doc_id": "NCT01822262_inc", "case_bucket": "other", "source_criterion": "Clinical diagnosis of calculous cholecystitis.", "candidate_expression": "((Clinical diagnosis) AND (calculous cholecystitis))"}
{"candidate_id": "LLM03565", "doc_id": "NCT02698969_inc", "case_bucket": "other", "source_criterion": "ASA physical status I-II age between 18-80 years old dNMB with rocuronium during ear nose and throat (ENT) surgery", "candidate_expression": "((ASA physical status I-II) AND (age between 18-80 years) AND (dNMB with rocuronium) AND (ear nose and throat (ENT) surgery))"}
{"candidate_id": "LLM03566", "doc_id": "NCT00182520_inc", "case_bucket": "or", "source_criterion": "Outpatient with primary DSM- IV OCD Completion of a 14-week open label trial of one the following SRI's: fluoxetine 80 mg/day, paroxetine 60 mg/day, fluvoxamine 300 mg/day, clomipramine 250 mg/day, sertraline 200 mg/day, citalopram 60 mg/day, escitalopram 30 mg/day and demonstrating a non or partial responses to SRI treatment (CGI-I of 3 or 4, Y-BOCS reduction of < 35%) Stable (8 wks or longer) concurrent medications including benzodiazepines, sedative hypnotics, antipsychotics, and antidepressants.", "candidate_expression": "((14-week) AND (200 mg/day) AND (250 mg/day) AND (3) AND (30 mg/day) AND (300 mg/day) AND (4) AND (60 mg/day) AND (8 wks or longer) AND (80 mg/day) AND (CGI-I) AND (DSM- IV) AND (OCD) AND (Outpatient) AND (SRI treatment) AND (Stable) AND (Y-BOCS) AND (antidepressants) AND (antipsychotics) AND (benzodiazepines) AND (citalopram) AND (clomipramine) AND (concurrent) AND (escitalopram) AND (fluoxetine) AND (fluvoxamine) AND (medications) AND (one the following) AND (paroxetine) AND (primary) AND (reduction of < 35%) AND (responses to) AND (sedative hypnotics) AND (sertraline))"}
{"candidate_id": "LLM03567", "doc_id": "NCT02973035_inc", "case_bucket": "or", "source_criterion": "Controlled hypertension: systolic BP < 150 and diastolic BP < 90 mmHg in persons aged 60 years or older, systolic BP < 140 and diastolic BP < 90 mmHg in persons 40 through 59 years according to the JNC 8th guideline Evidence of diastolic dysfunction showing E/E' > 10 The patient agrees to the study protocol and the schedule of clinical and echocardiographic follow-up, and provides informed, written consent, as approved by the appropriate Institutional Review Board/Ethical Committee of the respective clinical site", "candidate_expression": "((40 through 59) AND (60 years or older) AND (< 140) AND (< 150) AND (< 90 mmHg) AND (> 10) AND (Controlled) AND (E/E') AND (JNC 8th guideline) AND (The patient agrees to the study protocol and the schedule of clinical and echocardiographic follow-up, and provides informed, written consent, as approved by the appropriate Institutional Review Board/Ethical Committee of the respective clinical site) AND (aged) AND (diastolic BP) AND (diastolic dysfunction) AND (hypertension) AND (systolic BP) AND (years))"}
{"candidate_id": "LLM03568", "doc_id": "NCT02620904_inc", "case_bucket": "other", "source_criterion": "Intrauterine fetal death as confirmed by absence of cardiac motion on ultrasound by Attending physician at the time of admission to the hospital. Estimated gestational age greater than 20 weeks Hemodynamically stable and appropriate for induction of labor as per primary clinical health team in house Women with one prior low transverse cesarean delivery", "candidate_expression": "((Estimated gestational age greater than 20 weeks) AND (Hemodynamically stable) AND (Intrauterine fetal death) AND (Women) AND (absence of cardiac motion) AND (induction of labor) AND (low transverse cesarean delivery one) AND (ultrasound at the time of admission to the hospital))"}
{"candidate_id": "LLM03569", "doc_id": "NCT03063866_exc", "case_bucket": "or", "source_criterion": "Emergent condition like hematemesis. Patients with moderate to severe hepatic encephalopathy. Patients with hepatopulmonary syndrome. Patients with known or suspected hypersensitivity to the used medication were also excluded from the study.", "candidate_expression": "((Emergent condition) AND (hematemesis) AND (hepatic encephalopathy) AND (hepatopulmonary syndrome) AND (hypersensitivity) AND (used medication) AND ((known) OR (suspected)) AND ((moderate) OR (severe)))"}
{"candidate_id": "LLM03570", "doc_id": "NCT02742233_exc", "case_bucket": "or", "source_criterion": "Uncontrolled diabetes Ulcer infection Non-diabetic ulcers Orthopedic or neuromuscular pathologic conditions", "candidate_expression": "((Orthopedic pathologic conditions) AND (Ulcer infection) AND (diabetes Uncontrolled) AND (neuromuscular pathologic conditions) AND (ulcers Non-diabetic))"}
{"candidate_id": "LLM03571", "doc_id": "NCT01794793_exc", "case_bucket": "or", "source_criterion": "Patient has been permanently discontinued from pasireotide study treatment in the parent study due to unacceptable toxicity, non-compliance to study procedures, withdrawal of consent or any other reason Patient has participated in a Novartis sponsored combination trial where pasireotide was dispensed in combination with another study medication and is still receiving combination therapy. (only patients receiving pasireotide monotherapy can be included) Pregnant or nursing (lactating) women, where pregnancy is defined as the state of a female after conception and until the termination of gestation, confirmed by a positive hCG laboratory test Total abstinence (when this is in line with the preferred and usual lifestyle of the subject. Periodic abstinence (e.g., calendar, ovulation, symptothermal, post-ovulation methods) and withdrawal are not acceptable methods of contraception Female sterilization (have had surgical bilateral oophorectomy with or without hysterectomy) or tubal ligation at least six weeks before taking study treatment. In case of oophorectomy alone, only when the reproductive status of the woman has been confirmed by follow up hormone level assessment Male sterilization (at least 6 months prior to screening). For female subjects on the study the vasectomized male partner should be the sole partner for that subject. Use of oral, injected or implanted hormonal methods of contraception or other forms of hormonal contraception that have comparable efficacy (failure rate <1%), for example hormone vaginal ring or transdermal hormone contraception Placement of an intrauterine device (IUD) or intrauterine system (IUS) Barrier methods of contraception: Condom or Occlusive cap diaphragm or cervical/vault caps) with spermicidal foam/gel/film/cream/vaginal suppository In case of use of oral contraception women should have been stable on the same pill for a minimum of 3 months before taking study treatment Sexually active males unless they use a condom during intercourse while taking drug and for 1 months after pasireotide s.c. last dose and 3 months after pasireotide LAR last dose and should not father a child in this period. A condom is required to be used also by vasectomized men in order to prevent delivery of the drug via seminal fluid If a study patient or partner becomes pregnant or suspects being pregnant during the study or within 1 month after the final dose of pasireotide s.c. or 3 months after the final dose of pasireotide LAR, the Study Doctor needs to be informed immediately and ongoing study treatment with pasireotide has to be stopped immediately For patients taking pasireotide LAR, the future dose injections will be cancelled.", "candidate_expression": "((Condom) AND (Female sterilization) AND (IUD) AND (IUS) AND (Male sterilization) AND (Occlusive cap diaphragm) AND (Patient has participated in a Novartis sponsored combination trial where pasireotide was dispensed in combination with another study medication and is still receiving combination therapy. (only patients receiving pasireotide monotherapy can be included)) AND (Total abstinence (when this is in line with the preferred and usual lifestyle of the subject. Periodic abstinence (e.g., calendar, ovulation, symptothermal, post-ovulation methods) and withdrawal are not acceptable methods of contraception) AND (at least 6 months prior to screening) AND (at least six weeks before taking study treatment) AND (bilateral oophorectomy) AND (cervical caps) AND (contraception) AND (hormone vaginal ring) AND (hysterectomy) AND (intrauterine device) AND (intrauterine system) AND (nant or nursing (lactating) women, where pregnancy is defined as the state of a female after conception and until the termination of gestation, confirmed by a positive hCG laboratory test) AND (screening) AND (spermicidal foam) AND (taking study treatment) AND (transdermal hormone contraception) AND (tubal ligation) AND (vault caps))"}
{"candidate_id": "LLM03572", "doc_id": "NCT02563535_inc", "case_bucket": "other", "source_criterion": "age>18 years critical limb ischemia (Rutherford class 4-6) angiographic stenosis>50% or occlusion of at least one tibial vessel of at least 40mm for which an interventional treatment is scheduled", "candidate_expression": "((Rutherford class 4-6) AND (age >18 years) AND (angiographic stenosis >50%) AND (interventional treatment scheduled) AND (limb ischemia critical) AND (occlusion tibial vessel))"}
{"candidate_id": "LLM03573", "doc_id": "NCT00599924_exc", "case_bucket": "other", "source_criterion": "Prior treatment with more than 6 cycles of traditional alkylating agent-based chemotherapy regimens Prior treatment with more than 2 cycles of carboplating-based chemotherapy regimens For colorectal cancer patients in the expanded cohorts, prior treatment with more than 2 systemic chemotherapy regimens in the metastatic setting", "candidate_expression": "((Prior) AND (alkylating agent-based) AND (carboplating-based) AND (chemotherapy regimens) AND (colorectal cancer) AND (metastatic) AND (more than 2) AND (more than 2 cycles) AND (more than 6 cycles) AND (prior) AND (systemic chemotherapy regimens) AND (treatment))"}
{"candidate_id": "LLM03574", "doc_id": "NCT03539718_inc", "case_bucket": "or", "source_criterion": "Patients on regular hemodialysis 3sessions/wk. Recent catheter insertion at beginning of the study. Both males and females. Age group = 18 ys.", "candidate_expression": "((3sessions/wk) AND (= 18 ys) AND (Age group) AND (Recent) AND (at beginning of the study) AND (beginning of the study) AND (catheter insertion) AND (females) AND (males) AND (regular hemodialysis))"}
{"candidate_id": "LLM03575", "doc_id": "NCT03472846_inc", "case_bucket": "other", "source_criterion": "Postmenopausal women Age 60-80 years T-score according to DXA: <-2.5 indication for osteoporosis therapy according to international guidelines", "candidate_expression": "((Age 60-80 years) AND (DXA) AND (Postmenopausal) AND (T-score according to DXA <-2.5) AND (osteoporosis) AND (osteoporosis therapy indication for) AND (women))"}
```
