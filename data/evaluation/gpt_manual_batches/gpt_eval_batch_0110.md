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
{"candidate_id": "LLM02726", "doc_id": "NCT01743755_inc", "case_bucket": "or", "source_criterion": "18 years or older Chest radiograph showing new opacities. Cough Production of sputum Temp >38,0 °C or <36,0 °C Audible abnormalities by chest examination compatible with pneumonia Leukocytosis (>10.000 cells/mm3), leftward shift (>10%) or leucopenia (<4000 cells/mm3) C-reactive protein > 15 mg/l (three fold higher than the upper limit of normal)", "candidate_expression": "((C-reactive protein > 15 mg/l three fold higher than the upper limit of normal) AND (Chest radiograph) AND (Cough) AND (Temp) AND (chest examination Audible abnormalities) AND (opacities new) AND (pneumonia >10.000 cells/mm3 leftward shift >10%) AND (sputum) AND (years 18 or older) AND ((<36,0 °C) OR (>38,0 °C)) AND ((Leukocytosis) OR (leucopenia <4000 cells/mm3)))"}
{"candidate_id": "LLM02727", "doc_id": "NCT02205502_inc", "case_bucket": "other", "source_criterion": "patients who need suturing for laceration under procedural anesthesia using ketamine", "candidate_expression": "((ketamine) AND (laceration) AND (procedural anesthesia) AND (suturing))"}
{"candidate_id": "LLM02728", "doc_id": "NCT03059069_inc", "case_bucket": "other", "source_criterion": "Type 2 diabetic patients Age = 50 Glycemic control: HbA1c = 10.0% 10 = Beck Depression Inventory (BDI) <30 points Participants who can undergo contraception in case of being in childbearing period Understands the study procedure, alternatives, and risks and voluntarily agrees to participate by giving written informed concent", "candidate_expression": "((Age = 50) AND (Beck Depression Inventory (BDI) <30 points) AND (HbA1c = 10.0%) AND (Participants who can undergo contraception in case of being in childbearing period) AND (Type 2 diabetic) AND (Understands the study procedure, alternatives, and risks and voluntarily agrees to participate by giving written informed concent))"}
{"candidate_id": "LLM02729", "doc_id": "NCT02765035_inc", "case_bucket": "other", "source_criterion": "Person is >18 years old. Person is a unilateral transfemoral or knee-disarticulation amputee with stabilized residual limb. Person is a K2, K3 or K4 ambulator based on Medicare Functional Classification Level (MFCL). Person is currently fitted with a prosthesis using a non-microprocessor controlled prosthetic knee for at least 6 months. Person was never fitted with microprocessor controlled prosthetic knee joint. Person is willing and able to independently provide informed consent. Person is willing to comply with study procedures. Person wears prosthesis daily and = 8 hours/day. Person is walking on average 1km/day. Person is walking not slower than 3km/h (~0.8m/s) (based on 10m walk test conducted during recruiting). Person is walking on level ground in a step over step manner.", "candidate_expression": "((1km/day) AND (>18 years) AND (K2, K3 or K4) AND (MFCL) AND (Medicare Functional Classification Level) AND (Person is willing and able to independently provide informed consent) AND (Person is willing to comply with study procedures) AND (at least 6 months) AND (daily and = 8 hours/day) AND (microprocessor controlled) AND (never) AND (non-microprocessor controlled) AND (not slower than 3km/h) AND (old) AND (prosthesis) AND (prosthetic knee) AND (prosthetic knee joint) AND (walking))"}
{"candidate_id": "LLM02730", "doc_id": "NCT02933671_inc", "case_bucket": "other", "source_criterion": "English speaking between 18 and 75 years old American Society of Anesthesiologists (ASA) 1-3 patients undergoing primary total hip arthroplasty", "candidate_expression": "((ASA) AND (American Society of Anesthesiologists 1-3) AND (old between 18 and 75 years) AND (primary total hip arthroplasty))"}
{"candidate_id": "LLM02731", "doc_id": "NCT03026088_exc", "case_bucket": "or", "source_criterion": "Acute coronary syndrome (ACS) within 3 months. Under beta-blocker treatment for the last 2 weeks. Under other medicine treatment which may affect heart rate, like Non-dihydropyridine calcium channel blockers (NDHP-CCBs) or ivabradine for the last 2 weeks; Under Digoxin treatment [more than (>) 0.125 milligram (mg)]. Uncontrolled Diabetes [hemoglobin A1c, (HbA1c) >7.5%]. Severe or uncontrolled hypertension [resting Systolic Blood Pressure (SBP) >180 millimeters of mercury (mmHg), or resting Diastolic Blood Pressure (DBP) >110mmHg at screening period]. Severe hypotension [resting SBP less than (<) 90mmHg, or resting DBP<50mmHg]. Resting heart rate <60 beat per minute (bpm). Any contradiction to Bisoprolol according to label, including: Acute heart failure or during episodes of heart failure decompensation requiring intravenous inotropic therapy. Cardiogenic shock. Atrioventricular block of second or third degree (without a pacemaker). Sick sinus syndrome. Sinoatrial block. Slowed heart rate, causing symptoms (symptomatic bradycardia), Decreased blood pressure, causing symptoms (symptomatic hypotension), Severe bronchial asthma or severe chronic obstructive pulmonary disease. Sever forms of peripheral arterial occlusive disease and Raynaud's syndrome. Untreated phaeochromocytoma. Metabolic acidosis. Hypersensitivity to bisoprolol or to any of the excipients. Severe Arrhythmia including atrial fibrillation, atrial flutter, ventricular fibrillation, ventricular flutter or ventricular tachycardia. Significant valvular heart disease, congenital heart disease, pulmonary heart disease or perinatal heart disease. Acute pulmonary edema. Severe hepatic dysfunction, defined as: Serum Alanine Aminotransferase (ALT) > triple the upper limit of the normal range; and/or Serum Aspartate Aminotransferase (AST) > triple the upper limit of the normal value range and/or Severe renal dysfunction, defined as: Serum creatinine > twice the upper limit of the normal range Chronic Kidney Disease (glomerular filtration rate <45 Milliliter per minute). Hyperthyroidism or hypothyroidism. Severe infectious disease, example (eg) Human Immunodeficiency Virus positive or active tuberculosis. Severe autoimmune disease, e.g. lupus erythematosus, multiple sclerosis. Severe respiratory, digestive, hematological disease (including Anemia of Hb < 100 gram per litre) or tumor. Known to be hypersensitivity to Bisoprolol, or any of the excipient. Substance or alcohol abuse. Received heart transplantation or pacemaker implantation; revascularization treatment within 3 months; or plan to receive above treatment in 6 months. Currently undertaking other treatment that may affect the safety and/or efficacy evaluation, e.g. beta receptors agonists, et cetera. No legal ability or legal ability is limited. Subjects unlikely to cooperate in the study or with inability or unwillingness to give informed consent. Child-bearing period women without effective contraceptive measures, pregnancy and lactation. Participation in another clinical trial within the past 90 days. Other significant condition that in the Investigator's opinion would exclude the subject from the trial.", "candidate_expression": "((< 100 gram per litre) AND (<45 Milliliter per minute) AND (<50mmHg) AND (<60 beat per minute) AND (<60 bpm) AND (> 0.125 mg) AND (> triple the upper limit of the normal range) AND (> triple the upper limit of the normal value range) AND (> twice the upper limit of the normal range) AND (>110mmHg) AND (>180 millimeters of mercury) AND (>180 mmHg) AND (>7.5%) AND (ACS) AND (ALT) AND (AST) AND (Acute coronary syndrome) AND (Acute pulmonary edema) AND (Anemia) AND (Arrhythmia) AND (Bisoprolol) AND (Cardiogenic shock) AND (Child-bearing period women without effective contraceptive measures, pregnancy and lactation) AND (Chronic Kidney Disease) AND (DBP) AND (Decreased) AND (Diabetes) AND (Digoxin) AND (Hb) AND (HbA1c) AND (Hypersensitivity) AND (Metabolic acidosis) AND (NDHP-CCBs) AND (No legal ability or legal ability is limited) AND (Other significant condition that in the Investigator's opinion would exclude the subject from the trial) AND (Resting) AND (SBP) AND (Serum creatinine) AND (Sever) AND (Severe) AND (Sick sinus syndrome) AND (Significant) AND (Sinoatrial block) AND (Slowed) AND (Uncontrolled) AND (Untreated) AND (active) AND (any) AND (at screening period) AND (autoimmune disease) AND (beta receptors agonists) AND (beta-blocker) AND (blood pressure) AND (bradycardia) AND (contradiction) AND (for the last 2 weeks) AND (glomerular filtration rate) AND (heart rate) AND (hemoglobin A1c) AND (hepatic dysfunction) AND (hypersensitivity) AND (hypertension) AND (hypotension) AND (in 6 months) AND (infectious disease) AND (intravenous inotropic therapy) AND (less than 90mmHg) AND (more than 0.125 milligram) AND (pacemaker) AND (phaeochromocytoma) AND (plan to) AND (renal dysfunction) AND (resting) AND (screening) AND (severe) AND (symptomatic) AND (symptoms) AND (tumor) AND (ubjects unlikely to cooperate in the study or with inability or unwillingness to give informed consent) AND (within 3 months) AND (without) AND ((Serum Alanine Aminotransferase) OR (Serum Aspartate Aminotransferase)) AND ((Hyperthyroidism) OR (hypothyroidism)) AND ((Human Immunodeficiency Virus positive) OR (tuberculosis)) AND ((lupus erythematosus) OR (multiple sclerosis)) AND ((digestive disease) OR (hematological disease) OR (respiratory disease)) AND ((Bisoprolol) OR (excipient)) AND ((Substance abuse) OR (alcohol abuse)) AND ((heart transplantation) OR (pacemaker implantation) OR (revascularization)) AND ((heart transplantation) OR (pacemaker implantation)) AND ((Severe) OR (uncontrolled)) AND ((Diastolic Blood Pressure) OR (Systolic Blood Pressure)) AND ((DBP) OR (SBP)) AND ((Acute heart failure) OR (heart failure decompensation)) AND ((Atrioventricular block of second degree) OR (Atrioventricular block of third degree)) AND ((Non-dihydropyridine calcium channel blockers) OR (ivabradine)) AND ((bronchial asthma) OR (chronic obstructive pulmonary disease)) AND ((Raynaud's syndrome) OR (peripheral arterial occlusive disease)) AND ((bisoprolol) OR (excipients)) AND ((atrial fibrillation) OR (atrial flutter) OR (ventricular fibrillation) OR (ventricular flutter) OR (ventricular tachycardia)) AND ((congenital heart disease) OR (perinatal heart disease) OR (pulmonary heart disease) OR (valvular heart disease)))"}
{"candidate_id": "LLM02732", "doc_id": "NCT02200978_exc", "case_bucket": "or", "source_criterion": "Patients who have coma, convulsion or paralysis due to intracranial hemorrhage or central nervous system leukemia at diagnosis.", "candidate_expression": "((coma) AND (convulsion) AND (intracranial hemorrhage) AND (leukemia central nervous system) AND (paralysis))"}
{"candidate_id": "LLM02733", "doc_id": "NCT03323047_inc", "case_bucket": "or", "source_criterion": "Healthy patients aged 3-13 years Level I or level II on the American Society of Anesthesiologists (ASA) physical status classification system (as determined by the anesthesiologist) obstructive sleep apnea or recurrent throat infections undergoing elective tonsillectomy with or without adenoidectomy Parents who agree to complete documentation and follow up at 14 days post-operation.", "candidate_expression": "((American Society of Anesthesiologists (ASA) physical status Level I or level II) AND (Healthy) AND (Parents who agree to complete documentation and follow up at 14 days post-operation.) AND (adenoidectomy) AND (aged 3-13 years) AND (obstructive sleep apnea) AND (throat infections recurrent) AND (tonsillectomy elective))"}
{"candidate_id": "LLM02734", "doc_id": "NCT03472508_exc", "case_bucket": "or", "source_criterion": "(1)Women who are pregnant and/or lactating; or women who intend to conceive within a year; (2)History of allergies to enalapril, folic acid or other components of the compound drug; (3)History of adverse reactions or intolerance to enalapril or other ACE inhibitors, or drugs or supplements containing folic acid; (4)Diagnosis or suspicion of secondary hypertension; (5)Known serious medical conditions, including: Cardiovascular: patients with clinically diagnosed cardiac dysfunction (NYHA class III and above), hypertrophic obstructive cardiomyopathy, clinically significant valvular heart disease, acute coronary syndrome within the last 3 months, or percutaneous coronary intervention (PCI), or coronary artery bypass graft (CABG); or abnormal pre-enrollment ECG test results with clinically significant arrhythmias (atrial flutter, atrial fibrillation, grade II-III atrioventricular block, etc.); Digestive: a previous diagnosis of various types of viral hepatitis that are still in the active phase; abnormal pre-enrollment liver function test results (ALT, AST, GGT, TBIL, or DBIL 3 times higher than normal, ALB = 30g/L); gastrectomy and/or gastrojejunostomy; gastrointestinal dysfunction; Urinary: pre-enrollment serum creatinine greater than 200umol/L; clinical diagnosis of renal artery stenosis, isolated kidney, kidney transplantation and/or other diseases; Endocrine: type 1 diabetes or uncontrolled type 2 diabetes (fasting blood glucose above 11.1 mmol/L at pre-enrollment); previous diagnosis of hyperthyroidism and failure to correct; Respiratory: pulmonary heart disease; chronic obstructive pulmonary disease; Neuropsychiatric: recent transient ischemic attack or stroke (within the last 3 months); peripheral or severe autonomic dysfunction; mental or nervous system dysfunction, inability to express desire; known drug or alcohol dependence; Malignancy, malnutrition, hematopoietic disorders and other serious diseases. (6)Significant signs of abnormalities as seen in laboratory tests or physical characteristics, which, at the discretion of the investigators, indicates that the patient is experiencing a serious illness or, may affect the observation and evaluation of the drug's efficacy or adverse events, or renders the patient unsuitable for participating in this study; (7)Patients currently taking folate, B12, or B6, or any compounds containing them, who express an inability or a refusal to stop usage; (8)Regular usage of folic acid supplements or compounds containing folic acid in the past 3 months; (9)Participation in a clinical trial for a drug that has not yet been officially approved for marketing within one month prior to the first visit.", "candidate_expression": "((3 times higher than normal) AND (= 30g/L) AND (ACE inhibitors) AND (ALB) AND (ALT) AND (AST) AND (B12) AND (B6) AND (DBIL) AND (Diagnosis) AND (ECG test) AND (GGT) AND (History) AND (III and above) AND (Malignancy) AND (NYHA class) AND (Participation in a clinical trial) AND (Regular usage) AND (Significant) AND (TBIL) AND (Women) AND (abnormal) AND (above 11.1 mmol/L) AND (active phase) AND (acute coronary syndrome) AND (adverse reactions) AND (alcohol dependence) AND (allergies) AND (arrhythmias) AND (at pre-enrollment) AND (atrial fibrillation) AND (atrial flutter) AND (atrioventricular block) AND (autonomic dysfunction) AND (cardiac dysfunction) AND (chronic obstructive pulmonary disease) AND (clinical diagnosis) AND (clinically diagnosed) AND (clinically significant) AND (components of the compound drug) AND (compounds containing folic acid) AND (coronary artery bypass graft (CABG)) AND (currently) AND (drug dependence) AND (drug that has not yet been officially approved for marketing) AND (enalapril) AND (failure to correct) AND (fasting blood glucose) AND (folate) AND (folic acid) AND (folic acid supplements) AND (gastrectomy) AND (gastrointestinal dysfunction) AND (gastrojejunostomy) AND (grade II) AND (grade III) AND (greater than 200umol/L) AND (hematopoietic disorders) AND (hyperthyroidism) AND (hypertrophic obstructive cardiomyopathy) AND (in the past 3 months) AND (inability) AND (inability to express desire) AND (intend to conceive) AND (intolerance) AND (isolated kidney) AND (kidney transplantation) AND (laboratory tests) AND (lactating) AND (liver function test) AND (malnutrition) AND (medical conditions) AND (mental system dysfunction) AND (nervous system dysfunction) AND (other) AND (percutaneous coronary intervention (PCI)) AND (peripheral) AND (pre-enrollment) AND (pregnant) AND (previous) AND (pulmonary heart disease) AND (recent) AND (refusal to stop usage) AND (renal artery stenosis) AND (secondary hypertension) AND (serious) AND (serum creatinine) AND (severe) AND (signs of abnormalities) AND (stroke) AND (suspicion) AND (the first visit) AND (transient ischemic attack) AND (type 1 diabetes) AND (type 2 diabetes) AND (uncontrolled) AND (valvular heart disease) AND (viral hepatitis) AND (within a year) AND (within one month prior to the first visit) AND (within the last 3 months) AND (women))"}
{"candidate_id": "LLM02735", "doc_id": "NCT02316886_exc", "case_bucket": "or", "source_criterion": "Patients in whom the preferred treatment is CABG(Coronary artery bypass grafting) Stented lesion Bypass graft lesion The patients who have more than or equal to 3 target lesions 2 target lesions in the same coronary territory Heavily calcified or angulated lesion Bifurcation lesion requiring 2 stenting technique Contraindication to or planned discontinuation of dual antiplatelet therapy within 1 year Life expectancy less than 2 years Planned cardiac surgery or planned major non cardiac surgery Woman who are breastfeeding, pregnant or planning to become pregnant during the course of the study", "candidate_expression": "((2) AND (Bifurcation lesion) AND (Bypass graft) AND (CABG) AND (Coronary artery bypass grafting) AND (Life expectancy) AND (Planned) AND (Stented) AND (Woman) AND (dual antiplatelet therapy) AND (during the course of the study) AND (in the same coronary territory) AND (lesion) AND (less than 2 years) AND (major) AND (more than or equal to 3) AND (planned) AND (planning to become) AND (stenting technique) AND (target lesions) AND (within 1 year) AND ((Heavily calcified) OR (angulated)) AND ((Contraindication) OR (planned discontinuation)) AND ((cardiac surgery) OR (non cardiac surgery)) AND ((breastfeeding) OR (pregnant)))"}
{"candidate_id": "LLM02736", "doc_id": "NCT01715584_inc", "case_bucket": "other", "source_criterion": "age over 40 composite head and neck tumor resection treated hypertension hypertension medications taken on morning of surgery (except diuretics)", "candidate_expression": "((age) AND (composite head and neck tumor resection) AND (diuretics) AND (except) AND (hypertension) AND (hypertension medications) AND (on morning of surgery) AND (over 40) AND (treated))"}
{"candidate_id": "LLM02737", "doc_id": "NCT01942915_exc", "case_bucket": "other", "source_criterion": "1. Patients with C class by child-pugh score 2. Patients in the acute phase of severe hepatitis 3. Patients have been diagnosed with cancer of the liver 4. Patients with severe cardiopulmonary cerebral disease, and in the failure state 5. Patients in Highly allergic constitution 6. Patients with moderately severe mental disease", "candidate_expression": "((C class) AND (Highly allergic constitution) AND (acute phase) AND (cancer of the liver) AND (cardiopulmonary cerebral disease) AND (child-pugh score) AND (mental disease) AND (moderately severe) AND (severe) AND (severe hepatitis))"}
{"candidate_id": "LLM02738", "doc_id": "NCT01664507_exc", "case_bucket": "or", "source_criterion": "underlying lung or heart disase contra indication to dexamethasone immune deficient state preterm birth previous intubation or apnea history", "candidate_expression": "((contra indication) AND (dexamethasone) AND (immune deficient state) AND (preterm birth) AND ((heart disase) OR (lung disase)) AND ((apnea) OR (intubation)))"}
{"candidate_id": "LLM02739", "doc_id": "NCT01943409_inc", "case_bucket": "or", "source_criterion": "Patients with PN during their hospitalization Patients hospitalized in medical, surgical or ICU wards Signed informed consent either from the patient, their legally authorized representative or a direct family member", "candidate_expression": "((ICU wards) AND (PN during their hospitalization) AND (Signed informed consent either from the patient, their legally authorized representative or a direct family member) AND (hospitalization) AND (hospitalized) AND (medical wards) AND (surgical wards))"}
{"candidate_id": "LLM02740", "doc_id": "NCT01320579_inc", "case_bucket": "or", "source_criterion": "Informed consent obtained prior to any screening procedure Caucasian male or female patient At least 18 years of age Weight at least 45 kg Patient with moderate or severe chronic atopic dermatitis Good general health ascertained by medical history, physical examination and laboratory determinations, showing no signs of clinically significant findings, except chronic atopic dermatitis Negative pregnancy test (premenopausal female patient) at screening and use of adequate contraceptive measures (both male and female patients) throughout the study and 30 days after the last cis-UCA dose", "candidate_expression": "((Caucasian) AND (Good general health ascertained by medical history, physical examination and laboratory determinations) AND (Informed consent obtained prior to any screening procedure) AND (Negative pregnancy test (premenopausal female patient) at screening and use of adequate contraceptive measures (both male and female patients) throughout the study and 30 days after the last cis-UCA dose) AND (Weight at least 45 kg moderate) AND (age At least 18 years) AND (chronic atopic dermatitis severe) AND (clinically significant) AND (female) AND (laboratory determinations) AND (male) AND (medical history) AND (physical examination) AND (pregnancy test Negative) AND (premenopausal) AND NOT (signs of clinically significant findings clinically significant) AND NOT (chronic atopic dermatitis))"}
{"candidate_id": "LLM02741", "doc_id": "NCT02567214_exc", "case_bucket": "or", "source_criterion": "Respiratory exacerbation within the 2 months preceding the study Current diagnostic of asthma Significant O2 desaturation (SpO2 < 85%) at rest or during exercise Presence of another pathology that could influence exercise tolerance Use of home oxygen", "candidate_expression": "((O2 desaturation Significant) AND (Respiratory exacerbation within the 2 months preceding the study) AND (SpO2 < 85%) AND (diagnostic of asthma Current) AND (home oxygen) AND (pathology another influence exercise tolerance) AND ((at rest) OR (during exercise)))"}
{"candidate_id": "LLM02742", "doc_id": "NCT01440296_exc", "case_bucket": "other", "source_criterion": "any condition that would contra-indicate Magnetic Resonance Imaging or administration of contrast agent", "candidate_expression": "(EMPTY)"}
{"candidate_id": "LLM02743", "doc_id": "NCT01088750_exc", "case_bucket": "other", "source_criterion": "NA", "candidate_expression": "(EMPTY)"}
{"candidate_id": "LLM02744", "doc_id": "NCT02939872_inc", "case_bucket": "or", "source_criterion": "Age 19 and more On dual or triple antiplatelet therapy and between 12months and 14months from Bioresorbable Vascular Scaffold implantation No history of death, serious myocardial infarction, stroke, repeat revascularization, or major bleeding", "candidate_expression": "((Age 19 and more) AND (Bioresorbable Vascular Scaffold) AND (bleeding major) AND (death) AND (dual antiplatelet therapy) AND (implantation) AND (myocardial infarction serious) AND (revascularization repeat) AND (stroke) AND (triple antiplatelet therapy))"}
{"candidate_id": "LLM02745", "doc_id": "NCT00862446_exc", "case_bucket": "other", "source_criterion": "Enrollment in another trial Lack of consent", "candidate_expression": "((Enrollment in another trial) AND (Lack of consent))"}
{"candidate_id": "LLM02746", "doc_id": "NCT03639519_inc", "case_bucket": "other", "source_criterion": "Elective Cardiac surgery American Society of Anesthesiologists physical status class I-III", "candidate_expression": "((American Society of Anesthesiologists physical status) AND (Elective Cardiac surgery) AND (class I-III))"}
{"candidate_id": "LLM02747", "doc_id": "NCT03345589_inc", "case_bucket": "other", "source_criterion": "Patients diagnosed with primary biliary cholangitis Treated with Ursodeoxycholic Acid in West China Hospital for at least 6 month and suboptimal response to Ursodeoxycholic Acid", "candidate_expression": "((Ursodeoxycholic Acid) AND (West China Hospital) AND (for at least 6 month) AND (primary biliary cholangitis) AND (suboptimal response))"}
{"candidate_id": "LLM02748", "doc_id": "NCT01801072_inc", "case_bucket": "or", "source_criterion": "Adult (=18 years) Presence of intracranial aneurysm (with or without rupture) Treating surgeon has recommended surgical repair of the aneurysm", "candidate_expression": "((=18 years) AND (Adult) AND (Treating surgeon) AND (aneurysm) AND (intracranial aneurysm) AND (recommended) AND (surgical repair) AND (years) AND ((with rupture) OR (without rupture)))"}
{"candidate_id": "LLM02749", "doc_id": "NCT02330757_inc", "case_bucket": "scope", "source_criterion": "Women without PCOS as defined by the Rotterdam criteria. Presence of at least 2 cryopreserved good quality cleavage-stage embryo (good quality cleavage-stage embryos display stage-specific cell division, have blastomeres of fairly equal size with few to no cytoplasmic fragments).", "candidate_expression": "((cleavage-stage embryo at least 2 cryopreserved good quality) AND (cleavage-stage embryos good quality stage-specific cell division have blastomeres of fairly equal size) AND (few to no cytoplasmic fragments) AND NOT (PCOS Rotterdam criteria))"}
{"candidate_id": "LLM02750", "doc_id": "NCT02558504_inc", "case_bucket": "or", "source_criterion": "Age over 18 years, General Condition WHO 0, 1 or 2, ASA Class I and II, eligible for endoscopic or surgical treatment with curative intent, Histological diagnosis of high grade glandular epithelial neoplasia (Vienna 4-1 to 4-46), possibly multifocal or stage 0 (Tis, N0, M0), Endoscopic and histological confirmed diagnosis of intestinal metaplasia, Histological diagnosis confirmed by two endoscopies with biopsies and two pathological readings; biopsies should be carried out according to the protocol of the SFED (four-quadrant biopsies every cm) with at least once acetic acid for staining. Operators describe Barrett's esophagus using he SFED planimetric model. The final exam will be no more than two months before the date of treatment and should have been achieved in investigator establishment, Minimum 1 cm, Maximum 12 cm. the resected lesion must have been well differentiated and confined to the mucosa (m2 maximum) on histological analysis, resection should be more than two months, resection must have been macroscopically complete laterally, resection must have been histologically complete in depth, resection must have been histologically complete laterally with regard to the microinvasive cancer, that is to say with a clear margin of safety (margin may be high-grade dysplasia provided that the latter has not macroscopic translation), At least one endoscopic and histologic follow-up should be conducted with dye in a period of less than two months before the date of treatment, and at the investigator establishment. Patient may take an inhibitor of proton pump equivalent to 2 times 40 mg of esomeprazole, No mediastinal or celiac, or suspected metastatic lymph nodes by EUS, Affiliation to a social security system or similar, Lack of participation in another clinical study, Informed consent signed.", "candidate_expression": "((ASA Class) AND (Affiliation to a social security system) AND (Age over 18 years) AND (EUS) AND (Endoscopic) AND (General Condition WHO) AND (Histological) AND (Histological diagnosis) AND (Informed consent signed) AND (M 0) AND (N 0) AND (T is) AND (Vienna 4-1 to 4-46) AND (biopsies) AND (diagnosis Histological) AND (endoscopies two) AND (glandular epithelial neoplasia high grade multifocal) AND (histological) AND (histological analysis m2 maximum) AND (histologically) AND (intestinal metaplasia) AND (microinvasive cancer) AND (pathological readings two) AND (resected lesion well differentiated confined to the mucosa) AND (resection complete in depth) AND (resection complete laterally) AND (resection macroscopically complete laterally) AND (resection more than two months) AND (stage 0) AND NOT (lymph nodes mediastinal celiac metastatic) AND NOT (participation in clinical study another) AND ((surgical treatment) OR (treatment endoscopic)) AND ((Endoscopic confirmed) OR (histological confirmed)) AND ((0) OR (1) OR (2)) AND ((I) OR (II)))"}
```
