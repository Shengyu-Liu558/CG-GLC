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
{"candidate_id": "LLM00001", "doc_id": "NCT03620526_inc", "case_bucket": "or", "source_criterion": "presence of typical HF symptoms and signs LV ejection fraction = 50 elevated levels of NT-proBNP (at least >125 pg/ml) echocardiographic structural (a left atrial volume index > 34 mL/m2 or a left ventricular mass index =115 g/m2 for males and =95 g/m2 for females) or functional alterations (E/e'=13 and a mean e' septal and lateral wall < 9 cm/s).", "candidate_expression": "((< 9 cm/s) AND (= 50) AND (=115 g/m2) AND (=13) AND (=95 g/m2) AND (> 34 mL/m2) AND (E/e') AND (HF signs) AND (HF symptoms) AND (LV ejection fraction) AND (NT-proBNP) AND (at least >125 pg/ml) AND (echocardiographic structural) AND (elevated) AND (females) AND (functional alterations) AND (males) AND (mean e' septal and lateral wall) AND (typical) AND ((left atrial volume inde) OR (left ventricular mass index)))"}
{"candidate_id": "LLM00002", "doc_id": "NCT01959425_inc", "case_bucket": "or", "source_criterion": "Successful cardiac ablation for AF Documented freedom from AF recurrence (symptomatic or asymptomatic arrhythmic recurrences lasting longer than 30 seconds) 3 months after successful cardiac ablation (AF recurrence during 3-month blanking period is excluded). Patient must have been on a commercially approved anticoagulation therapy for at least two (2) months prior to randomization in the OAT Study. CHADS2 score = 2 or CHA2DS2-VASc score (=3) Left ventricular ejection fraction > 25% LA size < 65 High risk for thromboembolic events (i.e., CHADS2 score = 2 or CHA2DS2-VASc score = 3) and require OAT before undergoing cardiac ablation Able and willing to comply with all pre- and follow-up testing and requirements Signed informed consent form Age 18 years or older", "candidate_expression": "((AF) AND (Age 18 years or older) AND (LA size < 65) AND (Left ventricular ejection fraction > 25%) AND (OAT before undergoing cardiac ablation) AND (Signed informed consent form) AND (anticoagulation therapy at least two (2) months prior to randomization) AND (arrhythmic recurrences longer than 30 seconds) AND (ble and willing to comply with all pre- and follow-up testing and requirements) AND (cardiac ablation Successful) AND (risk for thromboembolic events High) AND NOT (AF recurrence 3 months after successful cardiac ablation) AND ((CHA2DS2-VASc score =3) OR (CHADS2 score = 2)) AND ((CHA2DS2-VASc score = 3) OR (CHADS2 score = 2)))"}
{"candidate_id": "LLM00003", "doc_id": "NCT02732080_exc", "case_bucket": "or", "source_criterion": "Recanalized (TIMI I-III flow) IRA at coronary angiography. Patients in whom TIMI-3 flow was not able to be established after wire crossing, balloon angioplasty or thrombectomy. STEMI due to bypass-graft occlusion Severe heart failure or cardiogenic shock", "candidate_expression": "((IRA) AND (Recanalized) AND (STEMI) AND (Severe) AND (TIMI I-III flow) AND (bypass-graft) AND (cardiogenic shock) AND (coronary angiography) AND (heart failure) AND (occlusion))"}
{"candidate_id": "LLM00004", "doc_id": "NCT02141061_inc", "case_bucket": "other", "source_criterion": "1. Speak, read, and understand English or Spanish and is willing and able to provide written informed consent on an IRB-approved form prior to the initiation of any study procedures; 2. Healthy, premenopausal female age 18-47; 3. History of menstrual events that occur in regular cycles 4. Agreement not to attempt to become pregnant 5. Agrees to use double-barrier contraception during the study and for 30 days after discontinuation of study medication. Acceptable double-barrier methods are: male condom with spermicide; male condom with diaphragm; diaphragm containing spermicide plus additional intra-vaginal spermicide; 6. Has a negative pregnancy test at the Screening visit. An exception for the pregnancy test requirement will be granted for subjects reporting surgical sterilization in medical history 7. Normal laboratory values or clinically insignificant findings at screening as determined by the Investigator; 8. Subject is willing to remain in the clinic overnight for PK assessment on Days 0 and 8 9. Ability to complete the study procedures in compliance with the protocol.", "candidate_expression": "((Ability to complete the study procedures in compliance with the protocol.) AND (Acceptable double-barrier methods are: male condom with spermicide; male condom with diaphragm; diaphragm containing spermicide plus additional intra-vaginal spermicide;) AND (Agreement not to attempt to become pregnant) AND (Agrees to use double-barrier contraception during the study and for 30 days after discontinuation of study medication.) AND (Healthy) AND (History) AND (Normal laboratory values) AND (age 18-47) AND (as determined by the Investigator) AND (clinically insignificant) AND (female) AND (findings clinically insignificant at screening screening) AND (laboratory) AND (laboratory Normal) AND (menstrual events that occur in regular cycles) AND (pregnancy test negative at the Screening visit) AND (premenopausal))"}
{"candidate_id": "LLM00005", "doc_id": "NCT02579733_inc", "case_bucket": "other", "source_criterion": "Ulcerative colitis patients with moderate to severe activity who achieved a clinical remission by the first course of corticosteroids Newly diagnosed or without steroid use during last 1 year Endoscopic Mayo subscore >0", "candidate_expression": "((Endoscopic Mayo subscore >0) AND (Ulcerative colitis moderate to severe) AND (clinical remission by the first course of corticosteroids) AND (corticosteroids first course) AND NOT (steroid during last 1 year))"}
{"candidate_id": "LLM00006", "doc_id": "NCT01912677_inc", "case_bucket": "or", "source_criterion": "Pregnant gestational age >= 28 weeks Systolic blood pressure >=160 mm Hg OR a diastolic blood pressure of >=110 mm Hg measured twice more than 15 minutes apart Able to swallow pills >= 18 years", "candidate_expression": "((>= 18) AND (>= 28 weeks) AND (>=110 mm Hg) AND (>=160 mm Hg) AND (Able to swallow pills) AND (gestational age) AND (years) AND ((Systolic blood pressure) OR (diastolic blood pressure)))"}
{"candidate_id": "LLM00007", "doc_id": "NCT02689817_inc", "case_bucket": "other", "source_criterion": "Patients undergoing an operation that is scheduled to last more than 2 hours", "candidate_expression": "((last more than 2 hours) AND (operation) AND (scheduled to last more than 2 hours))"}
{"candidate_id": "LLM00008", "doc_id": "NCT01491763_exc", "case_bucket": "or", "source_criterion": "Any other variety of LAL Patients with a history of coronary artery disease, valvular or hypertensive heart disease Patients with chronic liver disease Patients with chronic respiratory failure Renal failure not due to LAL Patients with positive HIV status No serious neurological abnormalities due to LAL Impact on overall severe (grade 3 or 4 of the WHO scale) not attributable to the LAL Pregnant or breastfeeding initial blast crisis CML", "candidate_expression": "((CML) AND (HIV status) AND (LAL) AND (No) AND (Pregnant) AND (Renal failure) AND (blast crisis) AND (breastfeeding) AND (chronic liver disease) AND (chronic respiratory failure) AND (coronary artery disease) AND (due to) AND (heart disease valvular) AND (history) AND (hypertensive heart disease) AND (neurological abnormalities) AND (not) AND (other variety) AND (positive) AND (serious))"}
{"candidate_id": "LLM00009", "doc_id": "NCT02796378_inc", "case_bucket": "other", "source_criterion": "Elevated blood-cholesterol", "candidate_expression": "((Elevated) AND (blood-cholesterol))"}
{"candidate_id": "LLM00010", "doc_id": "NCT00426751_inc", "case_bucket": "or", "source_criterion": "Women must be postmenopausal (i.e.12 months without menstrual period), or surgically sterile, i.e. women of child bearing potential are not allowed to be included into the study. In cases of doubt a pregnancy test should be performed. (NB -post menopausal women currently receiving hormone replacement are permissible) Acute myocardial infarction < 12 h defined as: 1. Angina or equivalent symptoms > 20 min and 2. ST elevation in 2 contiguous ECG leads (= 2 mm precordial lead, = 1 mm limb lead). This ECG recording serves as baseline ECG, i.e. ECG I. Planned primary percutaneous coronary intervention The subject has given written informed, dated consent to participate in the study", "candidate_expression": "((Acute myocardial infarction < 12 h) AND (Angina) AND (Angina symptoms) AND (Planned) AND (ST elevation) AND (Women) AND (child bearing potential) AND (contiguous ECG leads 2) AND (given written informed consent) AND (limb lead 1 mm) AND (postmenopausal) AND (precordial lead 2 mm) AND (pregnancy test doubt) AND (primary percutaneous coronary intervention) AND (surgically sterile) AND (women) AND NOT (menstrual period 12 months))"}
{"candidate_id": "LLM00011", "doc_id": "NCT03480607_exc", "case_bucket": "or", "source_criterion": "known allergy to any of drugs used coagulopathy any wound or infection related to puncture site major illness failure to gain consent of parents.", "candidate_expression": "((allergy) AND (coagulopathy) AND (consent of parents) AND (drugs used) AND (failure to gain) AND (failure to gain consent of parents) AND (illness) AND (infection) AND (major) AND (puncture site) AND (wound))"}
{"candidate_id": "LLM00012", "doc_id": "NCT02957305_inc", "case_bucket": "other", "source_criterion": "All patients admitted at the Gynecological emergency Unit at Hospital de Clínicas de Porto Alegre scheduled for uterine evacuation with <12 weeks of gestation.", "candidate_expression": "((<12 weeks) AND (Gynecological emergency Unit at Hospital de Clínicas de Porto Alegre) AND (gestation) AND (uterine evacuation))"}
{"candidate_id": "LLM00013", "doc_id": "NCT03536520_exc", "case_bucket": "or", "source_criterion": "Any active respiratory, cardiovascular or other disease requiring regular treatment or being otherwise relevant for tolerance of hypoxia or altitude exposure. Any condition that may interfere with protocol compliance including current heavy smoking (>20 cigarettes per day or >20 pack-years with active smoking during the last 10 years), regular use of alcohol. Allergy to acetazolamide and other sulfonamides.", "candidate_expression": "((Allergy) AND (acetazolamide) AND (active) AND (altitude exposure) AND (cardiovascular disease) AND (disease) AND (hypoxia) AND (other) AND (regular) AND (relevant for) AND (respiratory disease) AND (sulfonamides) AND (tolerance) AND (treatment))"}
{"candidate_id": "LLM00014", "doc_id": "NCT01884337_inc", "case_bucket": "or", "source_criterion": "Age =18 years Subjects undergoing elective total knee or hip replacement or a revision of at least one component of a total knee or hip replacement", "candidate_expression": "((Age =18 years) AND ((total hip replacement) OR (total knee replacement)) AND ((a hip replacement revision of) OR (a total knee replacement revision of)))"}
{"candidate_id": "LLM00015", "doc_id": "NCT02900443_inc", "case_bucket": "other", "source_criterion": "Probable or definite diagnosis of autoimmune hepatitis according to the International Autoimmune Hepatitis Study Group criteria First presentation of AIH requiring treatment according to the current EASL guidelines Age = 18 years Must provide informed consent and agree to comply with the trial protocol", "candidate_expression": "((AIH) AND (Age = 18 years) AND (EASL guidelines) AND (International Autoimmune Hepatitis Study Group criteria) AND (Must provide informed consent and agree to comply with the trial protocol) AND (autoimmune hepatitis) AND (treatment))"}
{"candidate_id": "LLM00016", "doc_id": "NCT02368743_exc", "case_bucket": "or", "source_criterion": "Patient included in an interventional study assessing treatment for active proctitis or distal proctosigmoiditis. Patient with left sided, colitis or pancolitis. Patient with severe proctitis (MAYO score ≥ 11 at inclusion). Patient previously treated with biologics. Patient treated with immunosuppressive within 1 month before study inclusion. Patient treated with corticosteroids within 2 weeks before study inclusion.", "candidate_expression": "((MAYO score ≥ 11 at inclusion) AND (biologics) AND (corticosteroids within 2 weeks before study inclusion) AND (immunosuppressive within 1 month before study inclusion) AND (proctitis severe) AND (treated previously) AND (treatment) AND ((active proctitis) OR (distal proctosigmoiditis)) AND ((colitis) OR (pancolitis)))"}
{"candidate_id": "LLM00017", "doc_id": "NCT02627521_inc", "case_bucket": "other", "source_criterion": "Accepted for CABG surgery Treatment with Ticagrelor within 48 hours", "candidate_expression": "((CABG surgery Accepted for) AND (Ticagrelor) AND (Treatment within 48 hours))"}
{"candidate_id": "LLM00018", "doc_id": "NCT00812344_exc", "case_bucket": "or", "source_criterion": "Significant illness, trauma or surgical procedures. Clinically significant laboratory abnormalities. Clinically significant medical history", "candidate_expression": "((Clinically significant) AND (Significant) AND (laboratory) AND (laboratory abnormalities Clinically significant) AND (medical history Clinically significant) AND ((illness) OR (surgical procedures) OR (trauma)))"}
{"candidate_id": "LLM00019", "doc_id": "NCT03264911_inc", "case_bucket": "other", "source_criterion": "3 -15 years old Clinical symptoms suggestive of pharyngitis with MC Isaac score =3 Rapid-antigen detection test (RADT) positive for GAS- Signed informed parental/patient consent form", "candidate_expression": "((MC Isaac score =3) AND (RADT) AND (Rapid-antigen detection test positive) AND (Signed informed parental/patient consent form) AND (old 3 -15 years) AND (pharyngitis Clinical symptoms suggestive of))"}
{"candidate_id": "LLM00020", "doc_id": "NCT03413891_exc", "case_bucket": "other", "source_criterion": "Subjects with any condition that as judged by the Investigator would place the subject at increased risk of harm if he/she participated in the study. Pregnancy or lactation Known allergic reaction to tranexamic acid", "candidate_expression": "((Pregnancy or lactation) AND (allergic) AND (tranexamic acid))"}
{"candidate_id": "LLM00021", "doc_id": "NCT03132259_exc", "case_bucket": "or", "source_criterion": "GCS less than 15 Preoperative Heart Rate less than 50 beat/min No Beta-Blockers Pregnant patients Take any Alpha-Methyldopa, Clonodine, Other Alpha-2 Adrenergic Agonist Hemodynamic unstable Systolic BP more than 160mmHg CAD Renal insuffuciency Allergy in dexmedethomidine and opioid BMI more than 30 Denied consent", "candidate_expression": "((Allergy) AND (Alpha-2 Adrenergic Agonist Other) AND (Alpha-Methyldopa) AND (BMI more than 30) AND (CAD) AND (Clonodine) AND (Denied consent) AND (GCS less than 15) AND (Hemodynamic unstable) AND (Pregnant) AND (Preoperative Heart Rate less than 50 beat/min) AND (Renal insuffuciency) AND (Systolic BP more than 160mmHg) AND (dexmedethomidine) AND (opioid) AND NOT (Beta-Blockers))"}
{"candidate_id": "LLM00022", "doc_id": "NCT02369211_inc", "case_bucket": "other", "source_criterion": "Patients undergoing robotic-assisted laparoscopic prostatectomy =18 years old males ASA class 1-4", "candidate_expression": "((1-4) AND (=18 years old) AND (ASA class) AND (males) AND (obotic-assisted laparoscopic prostatectomy) AND (years))"}
{"candidate_id": "LLM00023", "doc_id": "NCT02323399_inc", "case_bucket": "or", "source_criterion": "Subject's age is between =12 and 16 years, inclusive Subject is scheduled for a procedure that requires general or neuraxial anesthesia Subjects must have normal or clinically acceptable physical exam Subjects with controlled diabetes prior to entry must have a mean systolic/diastolic office blood pressure =128/78 mmHg (sitting, after 5 minutes of rest) Females must have a urine or serum pregnancy test (Human Chorionic Gonadotropin) that is negative at Screening and Day 1 Subject's parent or legal guardian gives informed consent and subject gives assent.", "candidate_expression": "((128 mmHg) AND (78 mmHg) AND (Day 1) AND (Human Chorionic Gonadotropin) AND (Subject's parent or legal guardian gives informed consent and subject gives assent.) AND (after 5 minutes of rest) AND (age) AND (at Screening) AND (between =12 and 16 years) AND (clinically acceptable) AND (controlled) AND (diabetes) AND (entry) AND (general t) AND (mean diastolic blood pressure) AND (mean systolic blood pressure) AND (negative) AND (neuraxial anesthesia) AND (normal) AND (physical exam) AND (prior to entry) AND (procedure) AND (rest) AND (scheduled for a procedure) AND (serum pregnancy test) AND (sitting) AND (urine pregnancy test))"}
{"candidate_id": "LLM00024", "doc_id": "NCT02816762_exc", "case_bucket": "or", "source_criterion": "Non diabetic nephropathy (confirmed by biopsy). Dialysis for acute renal failure within the 6 previous months. Evidence in the clinic history of relevant bilateral stenosis of renal artery (> 75%) Urinary albumin/creatinine ratio higher than 3000 mg/g, at the baseline visit. Systolic blood pressure = 180 mmHg or diastolic blood pressure = 110 mm Hg at the baseline visit. Stroke, transient ischemic attack, acute coronary syndrome, or hospitalization for heart failure worsening, within the previous 30 days. Professional drivers, risk profession or respiratory failure. Severe daytime sleepiness (Epworth sleepiness scale >18) Concomitant treatment with high doses of acetylsalicylic acid (> 500 mg/day) or continuous treatment with non-steroidal anti-inflammatory drugs Previous treatment with CPAP Participation in another clinical trial within the 30 days prior to randomization.", "candidate_expression": "((= 110 mm Hg) AND (= 180 mmHg) AND (> 500 mg/day) AND (> 75%) AND (>18) AND (CPAP) AND (Concomitant) AND (Dialysis) AND (Epworth sleepiness scale) AND (Non diabetic nephropathy) AND (Previous) AND (Professional drivers) AND (Severe) AND (Stroke) AND (Systolic blood pressure) AND (Urinary albumin/creatinine ratio) AND (acetylsalicylic acid) AND (acute coronary syndrome) AND (acute renal failure) AND (at the baseline visit) AND (bilateral) AND (biopsy) AND (confirmed by biopsy) AND (continuous) AND (daytime sleepiness) AND (diastolic blood pressure) AND (heart failure) AND (high doses) AND (higher than 3000 mg/g) AND (hospitalization) AND (non-steroidal anti-inflammatory drugs) AND (relevant) AND (respiratory failure) AND (risk profession) AND (stenosis of renal artery) AND (transient ischemic attack) AND (treatment) AND (within the 6 previous months) AND (within the previous 30 days) AND (worsening))"}
{"candidate_id": "LLM00025", "doc_id": "NCT03325023_inc", "case_bucket": "or", "source_criterion": "Written consent for participation in the clinical trial Age 18 to 45 years Irregular menstruation (> 35 days) or secondary amenorrhea> 3 months", "candidate_expression": "((18 to 45 years) AND (> 3 months) AND (> 35 days) AND (Age) AND (Irregular menstruation) AND (Written consent for participation in the clinical trial) AND (secondary amenorrhea))"}
```
