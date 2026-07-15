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
{"candidate_id": "LLM01751", "doc_id": "NCT03168178_exc", "case_bucket": "or", "source_criterion": "Known fetal anomaly Other indication for intrapartum antibiotics (endocarditis prophylaxis, other known maternal infection)", "candidate_expression": "((endocarditis prophylaxis) AND (fetal anomaly) AND (indication) AND (intrapartum antibiotics) AND (maternal infection))"}
{"candidate_id": "LLM01752", "doc_id": "NCT03255044_inc", "case_bucket": "other", "source_criterion": "older than 18 years (of both sexes) diagnosed with stable chronic heart failure NYHA class II-III ejection fraction < 40 % as assessed by 2D echocardiography who have been optimized on Guideline Directed treatment for heart failure for at least a month prior to enrolling.", "candidate_expression": "((2D echocardiography) AND (< 40 %) AND (II-III) AND (NYHA class) AND (both sexes) AND (chronic heart failure) AND (ejection fraction) AND (older than 18) AND (stable) AND (years))"}
{"candidate_id": "LLM01753", "doc_id": "NCT02664558_exc", "case_bucket": "or", "source_criterion": "Exclusions Related to Cardiovascular Disease 1. History of uncontrolled hypertension 2. Persistent hypotension at Screening. 3. Evidence or history of left-sided heart disease and/or clinically significant cardiac disease in which pulmonary hypertension is more likely WHO Group 2. 4. Acute decompensated heart failure within 1 month of Screening. 5. Recent initiation (<8 weeks from Screening) or planned initiation of cardiopulmonary rehabilitation exercise program. Exclusions Related to Pulmonary Disease 6. Newly diagnosed with PAH and not on PAH-specific therapy. 7. Pulmonary hypertension due to: 1. Uncorrected congenital systemic-to-pulmonary shunt. 2. Pulmonary veno-occlusive disease and/or pulmonary capillary hemangiomatosis 3. Persistent pulmonary hypertension of the newborn 4. WHO clinical classification Groups 2-5 8. Evidence of significant airway and/or parenchymal lung disease. 9. Chronic infection related to tuberculosis or fungal or mycobacterial disease. Exclusions Based on Other Medical Conditions 10. Chronic infections including, but not limited to tuberculosis (TB), hepatitis B virus (HBV) or hepatitis C virus (HCV). 11. History of portal hypertension or chronic liver disease, including positive serology for infection with HCV and/or HBV. 12. Evidence of active infection requiring intravenous or oral antibiotics within 4 weeks of Screening. 13. Body mass index ≥35.0 at Screening. 14. History of obstructive sleep apnea. 15. History of malignancy within the last 5 years, except nonmelanoma skin cancer and cervical carcinoma in situ treated with curative intent. 16. Neuropsychiatric disorders/symptoms or psychological conditions. 17. Pregnancy or breast-feeding 18. Prior treatment with B cell or lymphocyte-depleting agents (eg, rituximab, Campath) Exclusions Based on Concomitant Medication Use 19. Concurrent regular use of another leukotriene pathway inhibitor, including over-the-counter medications or herbal remedies. Exclusions Based on Laboratory Values 20. Significant/chronic renal insufficiency. 21. Transaminases (alanine transaminase, aspartate transaminase) levels >3 × upper limit of normal (ULN) and/or bilirubin level >2 × ULN. 22. Absolute neutrophil count <1500 mm3. 23. Hemoglobin concentration <9 g/dL at Screening. 24. Hepatic dysfunction as defined by Child-Pugh Class B or C", "candidate_expression": "((2) AND (<1500 mm3) AND (<8 weeks from Screening) AND (<9 g/dL) AND (>2 × ULN) AND (>3 × upper limit of normal (ULN)) AND (Absolute neutrophil count) AND (Acute) AND (B cell -depleting agents) AND (Body mass index) AND (Campath) AND (Child-Pugh) AND (Chronic) AND (Class B or C) AND (Concurrent) AND (Groups 2-5) AND (Hemoglobin concentration) AND (Hepatic dysfunction) AND (History) AND (Neuropsychiatric disorders) AND (Neuropsychiatric symptoms) AND (Newly diagnosed) AND (PAH) AND (PAH-specific therapy) AND (Persistent) AND (Persistent hypotension) AND (Pregnancy) AND (Prior) AND (Pulmonary veno-occlusive disease) AND (Recent) AND (Screening) AND (Significant) AND (Transaminases levels) AND (Uncorrected) AND (WHO Group) AND (WHO clinical classification) AND (airway disease) AND (alanine transaminase) AND (another) AND (aspartate transaminase) AND (at Screening) AND (bilirubin level) AND (breast-feeding) AND (cardiac disease) AND (cardiopulmonary rehabilitation exercise program) AND (cervical carcinoma in situ) AND (chronic liver disease) AND (chronic renal insufficiency) AND (clinically significant) AND (congenital systemic-to-pulmonary shunt) AND (curative intent) AND (decompensated) AND (except) AND (fungal disease) AND (heart failure) AND (hepatitis B virus (HBV)) AND (hepatitis C virus (HCV)) AND (history) AND (hypertension) AND (infection) AND (infection requiring antibiotics) AND (infections) AND (left-sided heart disease) AND (leukotriene pathway inhibitor) AND (lymphocyte-depleting agents) AND (malignancy) AND (mycobacterial disease) AND (nonmelanoma skin cancer) AND (not) AND (obstructive sleep apnea) AND (parenchymal lung disease) AND (planned) AND (portal hypertension) AND (positive) AND (psychological conditions) AND (pulmonary capillary hemangiomatosis) AND (pulmonary hypertension) AND (pulmonary hypertension of the newborn) AND (regular use) AND (related to) AND (rituximab) AND (serology for infection HBV) AND (serology for infection with HCV) AND (significant) AND (treated) AND (tuberculosis) AND (tuberculosis (TB)) AND (uncontrolled) AND (within 1 month of Screening) AND (within 4 weeks of Screening) AND (within the last 5 years) AND (≥35.0))"}
{"candidate_id": "LLM01754", "doc_id": "NCT02466113_inc", "case_bucket": "other", "source_criterion": "The informed consent has been obtained from the patient. With confirmed diagnosis of stage II colon cancer. With moderate/good ECOG health rating (PS): 0-1 score. The patient receive no anti-cancer treatment before primary surgery. The patient receive radical operation for colon cancer with negative margin.", "candidate_expression": "((0-1 score) AND (ECOG health rating (PS)) AND (The informed consent has been obtained from the patient.) AND (anti-cancer treatment) AND (before primary surgery) AND (colon cancer) AND (moderate/good) AND (no) AND (primary surgery) AND (radical operation negative margin) AND (stage II))"}
{"candidate_id": "LLM01755", "doc_id": "NCT02705222_exc", "case_bucket": "or", "source_criterion": "Age < 45 or > 55 years. Blood disorders or coagulopathy. Diagnosed or suspected local gynecologic lesion (polyp, adenomyosis, myoma, malignancy or cervical pathology). Use intrauterine contraceptive device. Pregnancy related conditions.", "candidate_expression": "((Age < 45 or > 55 years) AND (Pregnancy) AND (conditions Pregnancy related) AND (intrauterine contraceptive device) AND (local gynecologic lesion) AND ((adenomyosis) OR (cervical pathology) OR (malignancy) OR (myoma) OR (polyp)) AND ((Blood disorders) OR (coagulopathy)) AND ((Diagnosed) OR (suspected)))"}
{"candidate_id": "LLM01756", "doc_id": "NCT02766530_exc", "case_bucket": "or", "source_criterion": "Estimated GFR (eGFR) < 60 mL/min/1.73 m2 and blood glucose > 135 mg/dl; Past or present history of acute renal failure, renal dialysis, diabetes mellitus. Women who received metallic fixation, coronary artery stent in recent 3 months; or women who received mechanical valve replacement that is not compatible with MR magnet; or women with aneurysmal clips, pacemakers. Past history of claustrophobia. Women who are pregnant or who are planning to be pregnant, or who are lactating (though the possibility in our target population should be very low) Past history of breast cancer within recent 5 years before the currently diagnosed breast cancer. Women who received chemotherapy for other disease entity in recent 1 year. Women who cannot cooperate with the examinations.", "candidate_expression": "((< 60 mL/min/1.73 m2) AND (> 135 mg/dl) AND (Women who are pregnant or who are planning to be pregnant, or who are lactating (though the possibility in our target population should be very low)) AND (Women who cannot cooperate with the examinations) AND (breast cancer) AND (chemotherapy) AND (claustrophobia) AND (currently diagnosed breast cancer.) AND (eGFR) AND (mechanical valve replacement) AND (recent 1 year) AND (recent 3 months) AND (recent 5 years before the currently diagnosed breast cancer) AND ((Estimated GFR) OR (acute renal failure) OR (blood glucose) OR (diabetes mellitus) OR (renal dialysis)) AND ((coronary artery stent) OR (metallic fixation)) AND ((aneurysmal clips) OR (pacemakers)) AND ((Women) OR (women)))"}
{"candidate_id": "LLM01757", "doc_id": "NCT02714725_exc", "case_bucket": "or", "source_criterion": "Patient refusal. Emergency surgeries Redo surgeries Pregnancy Vasculitis Inflammation or infection at the study site History of allergic reaction to study medications", "candidate_expression": "((Emergency surgeries) AND (Patient refusal) AND (Pregnancy) AND (Redo surgeries) AND (Vasculitis) AND (allergic) AND ((Inflammation) OR (infection)))"}
{"candidate_id": "LLM01758", "doc_id": "NCT02995291_exc", "case_bucket": "or", "source_criterion": "contra-indications for regular dental treatment medical history that contraindicates the use of epinephrine participant taken an opioid or an opioid like analgesic within 24 hours pregnant", "candidate_expression": "((contra-indications) AND (contraindicates) AND (epinephrine) AND (medical history) AND (pregnant) AND (regular dental treatment) AND (within 24 hours) AND ((opioid) OR (opioid like analgesic)))"}
{"candidate_id": "LLM01759", "doc_id": "NCT03472508_exc", "case_bucket": "or", "source_criterion": "(1)Women who are pregnant and/or lactating; or women who intend to conceive within a year; (2)History of allergies to enalapril, folic acid or other components of the compound drug; (3)History of adverse reactions or intolerance to enalapril or other ACE inhibitors, or drugs or supplements containing folic acid; (4)Diagnosis or suspicion of secondary hypertension; (5)Known serious medical conditions, including: Cardiovascular: patients with clinically diagnosed cardiac dysfunction (NYHA class III and above), hypertrophic obstructive cardiomyopathy, clinically significant valvular heart disease, acute coronary syndrome within the last 3 months, or percutaneous coronary intervention (PCI), or coronary artery bypass graft (CABG); or abnormal pre-enrollment ECG test results with clinically significant arrhythmias (atrial flutter, atrial fibrillation, grade II-III atrioventricular block, etc.); Digestive: a previous diagnosis of various types of viral hepatitis that are still in the active phase; abnormal pre-enrollment liver function test results (ALT, AST, GGT, TBIL, or DBIL 3 times higher than normal, ALB = 30g/L); gastrectomy and/or gastrojejunostomy; gastrointestinal dysfunction; Urinary: pre-enrollment serum creatinine greater than 200umol/L; clinical diagnosis of renal artery stenosis, isolated kidney, kidney transplantation and/or other diseases; Endocrine: type 1 diabetes or uncontrolled type 2 diabetes (fasting blood glucose above 11.1 mmol/L at pre-enrollment); previous diagnosis of hyperthyroidism and failure to correct; Respiratory: pulmonary heart disease; chronic obstructive pulmonary disease; Neuropsychiatric: recent transient ischemic attack or stroke (within the last 3 months); peripheral or severe autonomic dysfunction; mental or nervous system dysfunction, inability to express desire; known drug or alcohol dependence; Malignancy, malnutrition, hematopoietic disorders and other serious diseases. (6)Significant signs of abnormalities as seen in laboratory tests or physical characteristics, which, at the discretion of the investigators, indicates that the patient is experiencing a serious illness or, may affect the observation and evaluation of the drug's efficacy or adverse events, or renders the patient unsuitable for participating in this study; (7)Patients currently taking folate, B12, or B6, or any compounds containing them, who express an inability or a refusal to stop usage; (8)Regular usage of folic acid supplements or compounds containing folic acid in the past 3 months; (9)Participation in a clinical trial for a drug that has not yet been officially approved for marketing within one month prior to the first visit.", "candidate_expression": "((ACE inhibitors other) AND (ALB = 30g/L) AND (ALT) AND (AST) AND (B12) AND (B6) AND (DBIL) AND (ECG test abnormal pre-enrollment) AND (GGT) AND (Malignancy) AND (NYHA class III and above) AND (Participation in a clinical trial within one month prior to the first visit) AND (TBIL) AND (Women) AND (acute coronary syndrome within the last 3 months) AND (adverse reactions) AND (alcohol dependence) AND (allergies History) AND (arrhythmias clinically significant) AND (atrial fibrillation grade II grade III) AND (atrial flutter) AND (atrioventricular block) AND (autonomic dysfunction severe) AND (cardiac dysfunction clinically diagnosed) AND (chronic obstructive pulmonary disease recent) AND (components of the compound drug) AND (compounds containing folic acid in the past 3 months) AND (coronary artery bypass graft (CABG)) AND (drug dependence) AND (drug that has not yet been officially approved for marketing) AND (enalapril) AND (fasting blood glucose above 11.1 mmol/L at pre-enrollment) AND (folate) AND (folic acid) AND (folic acid Diagnosis suspicion) AND (folic acid supplements) AND (gastrectomy) AND (gastrointestinal dysfunction) AND (gastrojejunostomy) AND (hematopoietic disorders) AND (hyperthyroidism previous failure to correct) AND (hypertrophic obstructive cardiomyopathy) AND (inability) AND (inability to express desire) AND (intend to conceive within a year) AND (intolerance) AND (isolated kidney) AND (kidney transplantation) AND (laboratory tests) AND (lactating) AND (liver function test abnormal pre-enrollment) AND (malnutrition) AND (medical conditions serious) AND (mental system dysfunction) AND (nervous system dysfunction) AND (percutaneous coronary intervention (PCI)) AND (pregnant) AND (pulmonary heart disease) AND (refusal to stop usage Regular usage) AND (renal artery stenosis clinical diagnosis) AND (secondary hypertension) AND (serum creatinine pre-enrollment greater than 200umol/L) AND (signs of abnormalities Significant) AND (stroke peripheral) AND (transient ischemic attack) AND (type 1 diabetes) AND (type 2 diabetes uncontrolled) AND (valvular heart disease clinically significant) AND (viral hepatitis previous active phase) AND (women))"}
{"candidate_id": "LLM01760", "doc_id": "NCT01631058_exc", "case_bucket": "or", "source_criterion": "Allergy to any of proposed medications Patients with any active infection including HBV, HCV and HIV.", "candidate_expression": "((Allergy) AND (active infection) AND (proposed medications) AND ((HBV) OR (HCV) OR (HIV)))"}
{"candidate_id": "LLM01761", "doc_id": "NCT02760459_inc", "case_bucket": "other", "source_criterion": "Age > 40 years (45) Primary knee osteoarthritis diagnosed using the American College of Rheumatology criteria (46) Undergoing elective, primary and unilateral total knee arthroplasty American Society of Anesthesiology (ASA) physical status class 1-3 BMI < 40 kg/m2", "candidate_expression": "((ASA) AND (Age > 40 years) AND (American Society of Anesthesiology physical status class 1-3) AND (BMI < 40 kg/m2) AND (Primary knee osteoarthritis American College of Rheumatology criteria) AND (total knee arthroplasty elective primary unilateral))"}
{"candidate_id": "LLM01762", "doc_id": "NCT01531257_exc", "case_bucket": "or", "source_criterion": "1. Need for combined organ transplantation with an extra-renal organ and/or islet cell transplant. 2. Recipients of previous non-renal solid organ and/or islet cell transplantation. 3. Infection with HIV. 4. Inability or unwillingness of a participant and/or guardian to provide informed consent", "candidate_expression": "((Inability or unwillingness of a participant and/or guardian to provide informed consent) AND (Infection with HIV) AND (combined organ transplantation) AND (extra-renal organ) AND (islet cell transplant) AND (islet cell transplantation) AND (non-renal solid organ transplantation) AND (previous))"}
{"candidate_id": "LLM01763", "doc_id": "NCT03351608_inc", "case_bucket": "or", "source_criterion": "Be categorized as American Society of Anesthesiologists (ASA) Physical Status Class 1, 2, or 3. Have a planned non-emergent surgical procedure or clinical situation (e.g., intubation) that requires moderate or deep NMB with either rocuronium or vecuronium. Have a planned surgical procedure or clinical situation that would allow objective neuromuscular monitoring techniques to be applied with access to the arm for neuromuscular transmission monitoring. Age between 2 to <17 years at Visit 2. If female, may participate if she is not pregnant, not breastfeeding, and at least one of the following: 1) Not a woman of childbearing potential (WOCBP); or 2) A WOCBP who agrees to follow the study contraceptive guidance during the treatment period and for at least 7 days after the last dose of study treatment.", "candidate_expression": "((Age) AND (American Society of Anesthesiologists (ASA) Physical Status Class) AND (NMB) AND (Not) AND (WOCBP) AND (at Visit 2) AND (at least one) AND (between 2 to <17 years) AND (breastfeeding) AND (clinical situation) AND (contraceptive guidance) AND (female) AND (intubation) AND (non-emergent) AND (not) AND (objective neuromuscular monitoring techniques) AND (planned) AND (pregnant) AND (surgical procedure) AND (that would allow objective neuromuscular monitoring techniques to be applied) AND (the last dose of study treatment) AND (the treatment period) AND (woman of childbearing potential (WOCBP)) AND ((deep) OR (moderate)) AND ((rocuronium) OR (vecuronium)) AND ((1) OR (2) OR (3)) AND ((clinical situation) OR (surgical procedure)) AND ((during the treatment period) OR (for at least 7 days after the last dose of study treatment)))"}
{"candidate_id": "LLM01764", "doc_id": "NCT03373318_exc", "case_bucket": "other", "source_criterion": "Patients who do not meet the inclusion criteria and those who have a history of allergic reactions to human albumin, as well as those who have received iodinated contrast during the 7 days prior to surgery and pregnant women, will be excluded from the study.", "candidate_expression": "((allergic) AND (during the 7 days prior to surgery) AND (history) AND (human albumin) AND (iodinated contrast) AND (meet the inclusion criteria) AND (not) AND (pregnant) AND (surgery) AND (women))"}
{"candidate_id": "LLM01765", "doc_id": "NCT03337503_inc", "case_bucket": "or", "source_criterion": "Written informed consent Adult patients (older than 18 years of age), male and female, with chronic non-cancer and cancer pain (at least 3 months in duration) Patients experiencing an average weekly pain intensity score greater than 4 on a 11 points NRS Subject agreed to follow the protocol Naïve cannabis patients with chronic non-cancer and cancer pain (not used cannabis in any presentation in the last 12 weeks) Patients receiving opioids and other concomitant pain medications should have a stable dose for the last 15 days. Normal cognitive status according to MiniCog Normal liver function (defined as aspartate aminotransferase 10-40 U/L and alanine aminotransferase 7-56 U/L) Normal renal function (defined as serum creatinine level <133 µmol/L and Estimated Glomerular Filtration Rate (eGFR) greater than or equal to 60) Negative result on ßhuman chorionic gonadotropin pregnancy test (if applicable) Ability to read and respond to questions in French or English. A male volunteer with sexual partners who are pregnant, possibly pregnant, or who could become pregnant must be surgically sterile or agrees to use one of the accepted contraceptive regimens from first drug administration until 3 months after the last drug administration.", "candidate_expression": "((A male volunteer with sexual partners who are pregnant, possibly pregnant, or who could become pregnant must be surgically sterile or agrees to use one of the accepted contraceptive regimens from first drug administration until 3 months after the last drug administration.) AND (Adult) AND (Estimated Glomerular Filtration Rate (eGFR) greater than or equal to 60 Negative) AND (MiniCog) AND (Naïve cannabis) AND (Normal cognitive status) AND (Normal liver function) AND (Normal renal function) AND (Subject agreed to follow the protocol) AND (Written informed consent) AND (age older than 18 years) AND (alanine aminotransferase 7-56 U/L) AND (aspartate aminotransferase 10-40 U/L) AND (average weekly pain intensity score on a 11 points NRS greater than 4) AND (cannabis in the last 12 weeks) AND (not) AND (pain chronic) AND (pain chronic at least 3 months in duration) AND (serum creatinine level <133 µmol/L) AND (ßhuman chorionic gonadotropin pregnancy test) AND ((cancer) OR (non-cancer)) AND ((opioids) OR (pain medications other)) AND ((female) OR (male)))"}
{"candidate_id": "LLM01766", "doc_id": "NCT03169127_inc", "case_bucket": "other", "source_criterion": "Need of lower third molar surgeries", "candidate_expression": "((lower third molar) AND (surgeries))"}
{"candidate_id": "LLM01767", "doc_id": "NCT03360214_inc", "case_bucket": "or", "source_criterion": "Subjects must be female Subjects must be 18 years or older Subjects must be undergoing unilateral or bilateral mastectomy with tissue expander reconstruction", "candidate_expression": "((female) AND (mastectomy undergoing bilateral) AND (older 18 years or older unilateral) AND (tissue expander reconstruction))"}
{"candidate_id": "LLM01768", "doc_id": "NCT01349413_exc", "case_bucket": "or", "source_criterion": "Presence of organic pathology identified by upper endoscopy or other investigations Presence of sliding hiatus hernia as defined by flap valve grade IV disruption of morphology at gastro-esophageal junction Concurrent medications that affect gastrointestinal motility Presence of acid reflux or heartburn symptoms of more than twice a month History of gastric surgery H. pylori infection Use of PPI or NSAID in the past 4 weeks Pregnancy Known hypersensitivity to PPI", "candidate_expression": "((H. pylori infection) AND (NSAID) AND (PPI) AND (Pregnancy) AND (acid reflux) AND (at gastro-esophageal junction) AND (flap valve disruption of morphology) AND (gastric surgery) AND (gastrointestinal motility) AND (grade IV) AND (heartburn symptoms) AND (hiatus hernia) AND (hypersensitivity) AND (in the past 4 weeks) AND (investigations) AND (medications) AND (more than twice a month) AND (organic pathology) AND (sliding) AND (upper endoscopy))"}
{"candidate_id": "LLM01769", "doc_id": "NCT02247128_exc", "case_bucket": "or", "source_criterion": "Need for long-term oral anticoagulation; Drug-eluting stent implantation within 3 months prior to TAVI procedure; Bare-metal stent implantation within 1 month prior to TAVI procedure; Allergy or intolerance to aspirin or clopidogrel. Drug-eluting stent implantation within 3 months prior to TAVI procedure; Bare-metal stent implantation within 1 month prior to TAVI procedure; Allergy or intolerance to (N)OAC or clopidogrel.", "candidate_expression": "(((N)OAC) AND (Allergy) AND (Bare-metal stent) AND (Drug-eluting stent) AND (TAVI procedure) AND (TAVI procedure TAVI procedure) AND (aspirin) AND (clopidogrel) AND (implantation within 1 month prior to TAVI procedure) AND (implantation within 3 months prior to TAVI procedure) AND (intolerance) AND (long-term oral anticoagulation Need for))"}
{"candidate_id": "LLM01770", "doc_id": "NCT01349413_exc", "case_bucket": "or", "source_criterion": "Presence of organic pathology identified by upper endoscopy or other investigations Presence of sliding hiatus hernia as defined by flap valve grade IV disruption of morphology at gastro-esophageal junction Concurrent medications that affect gastrointestinal motility Presence of acid reflux or heartburn symptoms of more than twice a month History of gastric surgery H. pylori infection Use of PPI or NSAID in the past 4 weeks Pregnancy Known hypersensitivity to PPI", "candidate_expression": "((H. pylori infection) AND (PPI) AND (Pregnancy) AND (flap valve disruption of morphology grade IV) AND (gastric surgery) AND (gastrointestinal motility) AND (hiatus hernia sliding at gastro-esophageal junction) AND (hypersensitivity) AND (medications) AND (organic pathology) AND ((acid reflux) OR (heartburn symptoms)) AND ((NSAID) OR (PPI)) AND ((investigations) OR (upper endoscopy)))"}
{"candidate_id": "LLM01771", "doc_id": "NCT02821819_inc", "case_bucket": "other", "source_criterion": "Premenopausal women 18-35 years old FSH levels < 10 mIU/ml AFC> 10 Regular cycles BMI < 28 Signed informed consent", "candidate_expression": "((AFC > 10) AND (BMI < 28) AND (FSH levels < 10 mIU/ml) AND (Premenopausal) AND (Regular cycles) AND (Signed informed consent) AND (old 18-35 years) AND (women))"}
{"candidate_id": "LLM01772", "doc_id": "NCT02396420_exc", "case_bucket": "or", "source_criterion": "History of prostate, bladder, or rectal cancer History of transurethral resection of the prostate (TURP), open prostate surgery, or radiofrequency or microwave therapies History of open bladder, rectosigmoid colon, or other pelvic surgery Patient is unwilling to discontinue alpha blockers 1 month after study treatment Patient is unwilling to discontinue 5-alph reductase inhibitors 1 month after study treatment Neurogenic bladder or other neurologic disorder impacting bladder function such as Parkinson's disease, multiple sclerosis, cerebral vascular accident or diabetes Any other confounding bladder or urethral pathology, including urethral stricture, bladder neck contracture, or bladder atonia Active prostatitis or urinary tract infection Cystolithiasis within the past 3 months Serum creatinine > 1.7mg/dL Inability to discontinue oral anticoagulant 2-5 days prior to study treatment Coagulation disturbances not normalized by medical treatment Iodinated contrast allergy that, in the opinion of the Investigator, cannot be adequately premedicated Gelatin allergy Known severe peripheral vascular disease or major iliac arterial occlusive disease Interest in future fertility Clinically significant cardiac arrhythmia or other cardiac disease (including congestive heart failure), uncontrolled diabetes mellitus, clinically significant respiratory disease, or known immunosuppression Other condition that the Investigator believes puts the patient at risk for a complication during the procedure", "candidate_expression": "((5-alph reductase inhibitors 1 month after study treatment) AND (Coagulation disturbances normalized) AND (Cystolithiasis within the past 3 months) AND (Gelatin) AND (Interest in future fertility) AND (Iodinated contrast) AND (Neurogenic bladder) AND (Other condition that the Investigator believes puts the patient at risk for a complication during the procedure) AND (Parkinson's disease) AND (Serum creatinine > 1.7mg/dL) AND (allergy) AND (alpha blockers 1 month after study treatment) AND (bladder atonia) AND (bladder cancer) AND (bladder neck contracture) AND (bladder pathology) AND (cardiac arrhythmia) AND (cardiac disease) AND (cerebral vascular accident) AND (clinically significant) AND (congestive heart failure) AND (diabetes) AND (diabetes mellitus uncontrolled) AND (iliac arterial occlusive disease major) AND (immunosuppression) AND (major) AND (medical treatment) AND (microwave therapies) AND (multiple sclerosis) AND (neurologic disorder impacting bladder function) AND (open bladder surgery) AND (open prostate surgery) AND (oral anticoagulant 2-5 days prior to study treatment) AND (pelvic surgery) AND (peripheral vascular disease severe) AND (prostate cancer) AND (prostatitis Active) AND (radiofrequency) AND (rectal cancer) AND (rectosigmoid colon surgery) AND (respiratory disease clinically significant) AND (severe) AND (transurethral resection of the prostate (TURP)) AND (urethral pathology) AND (urethral stricture) AND (urinary tract infection Active))"}
{"candidate_id": "LLM01773", "doc_id": "NCT03059069_exc", "case_bucket": "or", "source_criterion": "Type 1 diabetes, Secondary diabetes, gestational diabetes Ongoing dementia treatment or anti-depressive disorder medication Uncontrolled psychiatric disorder BDI = 30 points Heavy alcoholics Underlying chronic liver disease (hemochromatosis, liver cell carcinoma, autoimmune liver disease, liver cirrhosis, chronic viral hepatitis) Allergy or hypersensitivity to target medication or any of its components Renal failure, moderate or severe renal impairment (estimated glomerular filtration rate < 30 mL/min/1.73 m2), or ongoing dialysis Abnormal liver function (AST/ALT > x3 upper normal limit) History of alcohol or drug abuse in the previous 3 months Premenopausal women who are nursing or pregnant Human immunodeficiency virus (HIV) or human immunodeficiency virus (AIDS) chronic pancreatitis or pancreatic cancer", "candidate_expression": "((< 30 mL/min/1.73 m2) AND (= 30 points) AND (> x3 upper normal limit) AND (AST/ALT) AND (Abnormal) AND (Allergy) AND (BDI) AND (Heavy) AND (Human immunodeficiency virus (HIV)) AND (Ongoing) AND (Premenopausal) AND (Renal failure) AND (Secondary diabetes) AND (Type 1 diabetes) AND (Uncontrolled) AND (alcohol abuse) AND (alcoholics) AND (anti-depressive disorder medication) AND (autoimmune liver disease) AND (chronic liver disease) AND (chronic pancreatitis) AND (chronic viral hepatitis) AND (dementia) AND (dialysis) AND (drug abuse) AND (estimated glomerular filtration rate) AND (gestational diabetes) AND (hemochromatosis) AND (human immunodeficiency virus (AIDS)) AND (hypersensitivity) AND (in the previous 3 months) AND (liver cell carcinoma) AND (liver cirrhosis) AND (liver function) AND (moderate) AND (nursing) AND (ongoing) AND (pancreatic cancer) AND (pregnant) AND (renal impairment) AND (severe) AND (target medication) AND (treatment) AND (women))"}
{"candidate_id": "LLM01774", "doc_id": "NCT03015818_exc", "case_bucket": "other", "source_criterion": "Inability to give informed consent Pregnancy Concurrent antibiotherapy Certain infectious endocarditis Concurrent anti-inflammatory therapy, including corticosteroid therapy", "candidate_expression": "((Inability to give informed consent) AND (Pregnancy) AND (anti-inflammatory) AND (anti-inflammatory therapy Concurrent) AND (antibiotherapy Concurrent) AND (corticosteroid) AND (corticosteroid therapy) AND (infectious endocarditis Certain))"}
{"candidate_id": "LLM01775", "doc_id": "NCT01320579_inc", "case_bucket": "or", "source_criterion": "Informed consent obtained prior to any screening procedure Caucasian male or female patient At least 18 years of age Weight at least 45 kg Patient with moderate or severe chronic atopic dermatitis Good general health ascertained by medical history, physical examination and laboratory determinations, showing no signs of clinically significant findings, except chronic atopic dermatitis Negative pregnancy test (premenopausal female patient) at screening and use of adequate contraceptive measures (both male and female patients) throughout the study and 30 days after the last cis-UCA dose", "candidate_expression": "((Caucasian) AND (Good general health ascertained by medical history, physical examination and laboratory determinations) AND (Informed consent obtained prior to any screening procedure) AND (Negative pregnancy test (premenopausal female patient) at screening and use of adequate contraceptive measures (both male and female patients) throughout the study and 30 days after the last cis-UCA dose) AND (Weight at least 45 kg) AND (age At least 18 years) AND (chronic atopic dermatitis) AND (clinically significant) AND (female) AND (laboratory determinations) AND (medical history) AND (physical examination) AND (pregnancy test Negative) AND (premenopausal) AND NOT (signs of clinically significant findings clinically significant) AND NOT (chronic atopic dermatitis) AND ((moderate) OR (severe)) AND ((female) OR (male)))"}
```
