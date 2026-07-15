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
{"candidate_id": "LLM04701", "doc_id": "NCT03305666_exc", "case_bucket": "or", "source_criterion": "Allergy or hypersensitivity to bupivacaine Pregnancy Incarceration Age < 18 years Indwelling continuous thoracic epidural analgesia", "candidate_expression": "((Age < 18 years) AND (Allergy) AND (Incarceration) AND (Pregnancy) AND (bupivacaine) AND (hypersensitivity) AND (thoracic epidural analgesia Indwelling continuous))"}
{"candidate_id": "LLM04702", "doc_id": "NCT02390973_inc", "case_bucket": "or", "source_criterion": "BMI = 35 type 2 diabetes HbA1c = 6,5 % or fasting glycemia =7mmol/l or non-fasting glycemia =11mmol/l able to consent", "candidate_expression": "((= 35) AND (= 6,5 %) AND (=11mmol/l) AND (=7mmol/l) AND (BMI) AND (able to consent) AND (type 2 diabetes) AND ((HbA1c) OR (fasting glycemia) OR (non-fasting glycemia)))"}
{"candidate_id": "LLM04703", "doc_id": "NCT02408120_inc", "case_bucket": "or", "source_criterion": "Subjects admitted to the hospital with acute or chronic medical illnesses or for elective and emergency surgical illness or trauma Known history of Type 2 diabetes mellitus for >3 months Treated with either diet alone, any combination of oral antidiabetic agents, non-insulin injectables or insulin therapy Blood glucose levels between >140 mg and <400 mg/dL without laboratory evidence of diabetic ketoacidosis", "candidate_expression": "((Blood glucose levels >140 mg and <400 mg/dL) AND (Type 2 diabetes mellitus >3 months) AND (admitted to the hospital acute chronic) AND (diet) AND (insulin) AND (medical illnesses elective emergency) AND (non-insulin injectables therapy) AND (oral antidiabetic agents) AND (surgical illness) AND (trauma) AND NOT (diabetic ketoacidosis laboratory evidence))"}
{"candidate_id": "LLM04704", "doc_id": "NCT01700790_inc", "case_bucket": "or", "source_criterion": "Antiretroviral naive Taking Kaletra containing regimen with suppressed viral load. Taking an NNRTI or integrase containing regimen without prior history of use of PI for more than 2 weeks Taking an NNRTI or integrase containing regimen with prior exposure to PI greater than 2 weeks. It must be clearly stated in the source document that PI was switched to another agent for convenience. Taking another PI containing regimens with suppressed viral load. It must be clearly stated in source document that if another PI was used for greater than 2 weeks the regimen was switched to another agent for convenience. Subjects with prior history of PI use may be enrolled, if there is a genotype showing no resistance to Kaletra Other Inclusion criteria Be at least 18 years of age and able to give informed consent. Diagnosed with TB by criteria per Brazilian Ministry of Health Have a good clinical response to TB. Tolerating tuberculosis therapy containing rifampin for the 2 weeks prior to screening,except for persons taking protease inhibitors at time of diagnosis of TB.,. Subjects taking protease inhibitors will be screened and initiate visit 1 within 3 days of starting TB medication HIV positive with documentation present in source document. Have a CD4 cell count greater than 50 cells/mm3if not taking ART. Persons with cd4 < 50 may be enrolled, if it is felt that in the best interest of the patient, that enrollment in the study will allow for quicker initiation of antiretroviral therapy than referral to another treatment center.", "candidate_expression": "((Antiretroviral) AND (CD4 cell count greater than 50 cells/mm3) AND (HIV positive) AND (Kaletra) AND (PI) AND (PI prior greater than 2 weeks) AND (TB) AND (TB criteria per Brazilian Ministry of Health) AND (able to give informed consent) AND (age at least 18 years) AND (good clinical response) AND (naive) AND (regimen) AND (regimens) AND (rifampin) AND (tuberculosis) AND (tuberculosis therapy for the 2 weeks prior to screening) AND (viral load suppressed) AND NOT (PI prior for more than 2 weeks) AND NOT (protease inhibitors at time of diagnosis of TB) AND NOT (ART) AND ((NNRTI) OR (integrase)))"}
{"candidate_id": "LLM04705", "doc_id": "NCT00455663_inc", "case_bucket": "or", "source_criterion": "Diagnosis of schizophrenia or schizoaffective disorder If entering the study as an inpatient, hospitalization was recent Currently receiving treatment with an atypical antipsychotic and continuation on the medication has been recommended Assumes primary responsibility for taking medication Currently living in a stable environment", "candidate_expression": "((Currently) AND (atypical antipsychotic) AND (continuation on the medication) AND (hospitalization) AND (inpatient) AND (living in a stable environment) AND (recent) AND (recommended) AND (schizoaffective disorder) AND (schizophrenia) AND (treatment))"}
{"candidate_id": "LLM04706", "doc_id": "NCT02312076_inc", "case_bucket": "other", "source_criterion": "Women subjected to ICSI through controlled ovarian hyperstimulation (COH) with pituitary downregulation by GnRHa.", "candidate_expression": "((ICSI) AND (Women) AND (controlled ovarian hyperstimulation (COH)) AND (pituitary downregulation by GnRHa))"}
{"candidate_id": "LLM04707", "doc_id": "NCT03068897_inc", "case_bucket": "or", "source_criterion": "Present to ED primary for management of LBP, defined as pain originating between the lower border of the scapulae and the upper gluteal folds. Flank pain, that is pain originating from tissues lateral to the paraspinal muscles, will not be included. Musculoskeletal etiology of low back. Patients with non-musculoskeletal etiologies such as urinary tract infection, ovarian cysts, or influenza like illness will be excluded. The primary clinical diagnosis, at the conclusion of the ED visit, must be a diagnosis consistent with non-traumatic, non-radicular, musculoskeletal LBP. Patient is to be discharged home. Patients admitted to the hospital are more likely to be treated with parenteral medication and therefore are not appropriate for this study. Age 18-64 Enrollment will be limited to adults younger than 65 years because of the increased risk of adverse medication effects in the elderly. Non-radicular pain. Patients will be excluded if the pain radiates below the gluteal folds in a radicular pattern. Pain duration <2 weeks (336 hours). Patients with more than two weeks of pain are at increased risk of poor pain and functional outcomes.(9) Prior to the acute attack of LBP, back pain cannot occur more frequently than once per month. Patients with more frequent back pain are at increased risk of poor pain and functional outcomes.(9) Non-traumatic LBP: no substantial and direct trauma to the back within the previous month Functionally impairing back pain: A baseline score of > 5 on the Roland-Morris Disability Questionnaire", "candidate_expression": "((Age 18-64) AND (ED) AND (LBP) AND (LBP Non-traumatic substantial) AND (LBP non-traumatic non-radicular musculoskeletal) AND (Pain duration <2 weeks duration 336 hours) AND (Present) AND (Roland-Morris Disability Questionnaire baseline score of > 5) AND (adults younger than 65 years) AND (adverse effects increased risk) AND (attack of LBP acute) AND (back pain Functionally impairing) AND (back pain Prior to the acute attack of LBP more frequently than once per month) AND (elderly) AND (etiologies musculoskeletal) AND (etiology Musculoskeletal low back) AND (influenza like illness) AND (medication) AND (no) AND (ovarian cysts) AND (pain between the lower border of the scapulae and the upper gluteal folds) AND (pain radicular) AND (pain tissues lateral to the paraspinal muscles) AND (trauma back within the previous month direct) AND (urinary tract infection) AND NOT (pain below the gluteal folds in a radicular pattern) AND NOT (Flank pain))"}
{"candidate_id": "LLM04708", "doc_id": "NCT02997215_inc", "case_bucket": "other", "source_criterion": "American Society of Anesthesiologist (ASA) status I-II adult patients undergoing elective laparoscopic cholecystectomy.", "candidate_expression": "((American Society of Anesthesiologist (ASA)) AND (adult) AND (elective) AND (laparoscopic cholecystectomy) AND (status I-II))"}
{"candidate_id": "LLM04709", "doc_id": "NCT03299517_inc", "case_bucket": "or", "source_criterion": "Adult men and women> 18 years old Presence of sustained ventricular tachycardia with HR> 120 bpm Systolic blood pressure> 90 mmHg No signs of poor peripheral perfusion Absence of dyspnea Absence of severe angina Signed consent form", "candidate_expression": "((> 120 bpm) AND (> 18 years old) AND (> 90 mmHg) AND (Absence of) AND (Adult) AND (HR) AND (No) AND (Signed consent form) AND (Systolic blood pressure) AND (angina) AND (dyspnea) AND (old) AND (poor peripheral perfusion) AND (severe) AND (signs of) AND (sustained) AND (ventricular tachycardia) AND ((men) OR (women)))"}
{"candidate_id": "LLM04710", "doc_id": "NCT03117608_inc", "case_bucket": "or", "source_criterion": "Patients provided written informed consent; Patients aged between 18 and 75 years; Knee symptomatic OA (Kellgren-Lawrence grade 1-4) Failure of conservative treatment for at least 3 months; Patients agreed to actively participate in the rehabilitation protocol and follow-up program; Male or female patients; Women of childbearing age had to use a proven method to prevent pregnancy, before the surgical treatment.", "candidate_expression": "((1-4) AND (Failure) AND (Kellgren-Lawrence grade) AND (OA Knee) AND (Women) AND (aged) AND (agreed to actively participate in the follow-up program) AND (agreed to actively participate in the rehabilitation protocol) AND (before the surgical treatment) AND (between 18 and 75 years) AND (childbearing age) AND (conservative treatment) AND (for at least 3 months) AND (method to prevent pregnancy) AND (provided written informed consent) AND (surgical treatment) AND (symptomatic) AND (the surgical treatment) AND ((Male) OR (female)))"}
{"candidate_id": "LLM04711", "doc_id": "NCT02781610_inc", "case_bucket": "or", "source_criterion": "Male or female =18 years of age at Visit 1 Documentation of a CF diagnosis Enrolled in the Cystic Fibrosis Foundation National Patient Registry (CFFNPR) prior to Visit 1 (US sites only) At the time of Visit 1, there is a plan to initiate IV antibiotics for a pulmonary exacerbation Performed spirometry at Visit 1 and Visit 2 and willing to perform spirometry at Visit 3 Completed the CRISS questionnaire at Visit 1 and Visit 2 and willing to complete the Cystic Fibrosis Respiratory Symptoms Diary (CFRSD) questionnaire at Visit 3 Willing to adhere to a specific treatment duration determined by initial response to treatment and subsequent randomization Willing to return for follow up Visit 3 Written informed consent obtained from the subject or subject's legal representative", "candidate_expression": "((CF) AND (CRISS questionnaire at Visit 1 at Visit 2 Visit 2) AND (Cystic Fibrosis Respiratory Symptoms Diary (CFRSD) questionnaire willing to complete at Visit 3 Willing to) AND (IV antibiotics At the time of Visit 1) AND (Male) AND (US sites Enrolled in the Cystic Fibrosis Foundation National Patient Registry (CFFNPR)) AND (Written informed consent from the subject from the subject's legal representative) AND (age =18 years at Visit 1) AND (female) AND (follow up Visit 3 Willing to) AND (pulmonary exacerbation) AND (spirometry at Visit 1 at Visit 2) AND (spirometry willing to perform at Visit 3))"}
{"candidate_id": "LLM04712", "doc_id": "NCT01963754_inc", "case_bucket": "or", "source_criterion": "Single unit implant rehabilitation Maxilla and mandible Must accept treatment plan Must sign informed consent dental extraction performed at least 3 month prior Must have at least 6 mm of residual bone Absence of oral lesions keratinized tissue must be present", "candidate_expression": "((Absence) AND (Must accept treatment plan) AND (Must sign informed consent) AND (Single unit implant rehabilitation) AND (at least 3 month prior) AND (at least 6 mm) AND (dental extraction) AND (keratinized tissue must be present) AND (oral lesions) AND (residual bone) AND ((Maxilla) OR (mandible)))"}
{"candidate_id": "LLM04713", "doc_id": "NCT03088904_inc", "case_bucket": "other", "source_criterion": "NA", "candidate_expression": "(EMPTY)"}
{"candidate_id": "LLM04714", "doc_id": "NCT02509091_exc", "case_bucket": "or", "source_criterion": "Active bleeding without control; Receiving nasal or facial surgery recently; With severe cardio-pulmonary dysfunction, such as left heart failure, unstable arrhythmia, etc. With other respiratory diseases: such as active pulmonary tuberculosis, non-tuberculosis mycobacteria (NTM) pulmonary disease, pulmonary aspergillosis, etc. Be allergic to amikacin", "candidate_expression": "((NTM) AND (allergic) AND (amikacin) AND (arrhythmia unstable) AND (bleeding Active) AND (cardio-pulmonary dysfunction severe) AND (facial surgery) AND (left heart failure) AND (nasal surgery) AND (non-tuberculosis mycobacteria pulmonary disease) AND (pulmonary aspergillosis) AND (pulmonary tuberculosis active) AND (respiratory diseases))"}
{"candidate_id": "LLM04715", "doc_id": "NCT00970866_inc", "case_bucket": "or", "source_criterion": "At least 18 years of age No more than 20 wk of gestation Given Ante-natal Cards of the Ghana Health Service Completed the initial routine ante-natal examination at the clinics HIV negative or status unknown (as from the Ante-natal card) Free from chronic disease e.g. malignancy requiring frequent medical attention (as from the Ante-natal card) Residing in the Manya Krobo or Yilo Krobo district Prepared to sign an informed consent Living in the area throughout the duration of the study Acceptance of home visitors", "candidate_expression": "((Acceptance of home visitors) AND (At least 18 years) AND (HIV) AND (Living in the area) AND (No more than 20 wk) AND (Prepared to sign an informed consent) AND (Residing) AND (age) AND (chronic disease) AND (clinics) AND (gestation) AND (malignancy) AND (routine ante-natal examination) AND (the study) AND (throughout the duration of the study) AND ((negative) OR (status unknown)) AND ((Manya Krobo district) OR (Yilo Krobo district)))"}
{"candidate_id": "LLM04716", "doc_id": "NCT02650388_inc", "case_bucket": "or", "source_criterion": "Age = 75 years, Severe, symptomatic aortic stenosis, High risk for cardiac surgery (STS and logistic Euroscore ), According multidisciplinary (heart) team decision TAVI is preferable, Willing to participate", "candidate_expression": "((= 75 years) AND (Age) AND (High risk) AND (Severe) AND (Willing to participate) AND (aortic stenosis) AND (cardiac surgery) AND (symptomatic) AND ((STS) OR (logistic Euroscore)))"}
{"candidate_id": "LLM04717", "doc_id": "NCT02695992_exc", "case_bucket": "or", "source_criterion": "Congestive heart failure Ischemic heart disease Hypotension (Systolic blood pressure <100 mmHg) Treatment with class I or III antiarrhythmic drugs Severe hepatic or renal failure Pregnancy or lactation Hypersensitivity or contradictions to study drugs Atrio-ventricular conduction disturbances Thyrotoxicosis Life limiting disease or substance abuse which may affect participation", "candidate_expression": "((Atrio-ventricular conduction disturbances) AND (Congestive heart failure) AND (Hypotension) AND (Ischemic heart disease) AND (Systolic blood pressure <100 mmHg) AND (Thyrotoxicosis) AND (antiarrhythmic drugs) AND (study drugs) AND ((hepatic failure) OR (renal failure)) AND ((Pregnancy) OR (lactation)) AND ((Hypersensitivity) OR (contradictions)) AND ((Life limiting disease) OR (substance abuse)) AND ((class I) OR (class III)))"}
{"candidate_id": "LLM04718", "doc_id": "NCT02543710_exc", "case_bucket": "or", "source_criterion": "Patients who will not get surgical treatment for their endometrial cancer Patients not suffering from endometrial or epithelial ovarian cancer Patients who do not agree to the proposed treatment or will receive (part of) the treatment in a non-participating centre Patients who cannot or do not want to give informed consent (including language barriers)", "candidate_expression": "((cannot) AND (do not want to) AND (endometrial cancer) AND (endometrial ovarian cancer) AND (epithelial ovarian cancer) AND (give informed consent) AND (language barriers) AND (non-participating centre) AND (treatment) AND NOT (surgical treatment) AND NOT (agree to the proposed treatment))"}
{"candidate_id": "LLM04719", "doc_id": "NCT03318393_inc", "case_bucket": "or", "source_criterion": "Age 1 day to less than 18 years Cared for in the pediatric intensive care unit or pediatric cardiac intensive care unit receiving venovenous or venoarterial ECMO", "candidate_expression": "((Age 1 day to less than 18 years) AND ((pediatric cardiac intensive care unit) OR (pediatric intensive care unit)) AND ((venoarterial ECMO) OR (venovenous ECMO)))"}
{"candidate_id": "LLM04720", "doc_id": "NCT03247738_inc", "case_bucket": "other", "source_criterion": "Patients with STEMI undergoing primary PPCI Age > 18 years old", "candidate_expression": "((Age > 18 years old) AND (STEMI) AND (primary PPCI))"}
{"candidate_id": "LLM04721", "doc_id": "NCT03194074_inc", "case_bucket": "or", "source_criterion": "Patients scheduled for laser laryngeal surgery under general anesthesia with either Propofol or desflurane based technique.", "candidate_expression": "((general anesthesia) AND (laser laryngeal surgery) AND (scheduled) AND ((Propofol) OR (desflurane)))"}
{"candidate_id": "LLM04722", "doc_id": "NCT02384850_inc", "case_bucket": "or", "source_criterion": "1. Patients with histologically confirmed diagnosis of colorectal cancer presenting with unresectable stage IV (UICC) disease (primary tumor may be present) 2. Patients who are feasible for treatment with FOLFOX (prior adjuvant or palliative treatment is allowed) 3. ECOG Performance status ≤ 1 4. Life expectancy > 3 months 5. Age ≥18 years 6. Haematologic function as follows (5% deviation allowed): ANC ≥ 1.5 x 109/L platelets ≥ 100 x109/L hemoglobin ≥ 9 g/dl or 5.59 mmol/l 7. Adequate liver function as follows (10% deviation allowed) serum alanine transaminase (ALT) ≤ 2.5 x ULN (in case of liver metastases < 5 x ULN) total bilirubin ≤ 1.5 x ULN (patients with Gilbert's syndrome total bilirubin ≤2.5 x ULN) 8. Adequate renal function as follows (10% deviation allowed) · creatinine ≤ 1.5 x ULN 9. Signed written informed consent 10. Women of child-bearing potential must have a negative pregnancy test", "candidate_expression": "((< 5 x ULN) AND (> 3 months) AND (ANC) AND (Adequate) AND (Age) AND (ECOG Performance status) AND (FOLFOX) AND (IV) AND (Life expectancy) AND (Signed written informed consent) AND (Women) AND (child-bearing potential) AND (colorectal cancer) AND (creatinine) AND (disease) AND (hemoglobin) AND (liver function) AND (liver metastases) AND (negative) AND (platelets) AND (pregnancy test) AND (renal function) AND (serum alanine transaminase (ALT)) AND (stage IV (UICC)) AND (total bilirubin) AND (unresectable) AND (≤ 1) AND (≤ 1.5 x ULN) AND (≤ 2.5 x ULN) AND (≤2.5 x ULN) AND (≥ 1.5 x 109/L) AND (≥ 100 x109/L) AND (≥18 years) AND ((confirmed) OR (histologically)) AND ((adjuvant treatment) OR (palliative treatment)) AND ((≥ 5.59 mmol/l) OR (≥ 9 g/dl)) AND ((Gilbert's syndrome) OR (total bilirubin)))"}
{"candidate_id": "LLM04723", "doc_id": "NCT02519777_exc", "case_bucket": "or", "source_criterion": "Major depressive disorder with psychotic features Traumatic Brain Injury (TBI) with a clear impact on activities of daily living Developmental delay, intellectual deficit, and/or severe educational disability resulting in some dependence for activities of daily living Ongoing substance use disorder with significant impact on activities of daily living. Difficult or impossible to determine whether cognitive or functional decline is due to substance use or HIV, or both Evidence of intoxication or withdrawal during the screening evaluation Central nervous system (CNS) infections or opportunistic conditions: brain abscess (bacterial, mycobacterial, fungal or Toxoplasma), meningitis with persistent neurologic impairment, primary CNS lymphoma, progressive multifocal leukoencephalopathy (PML), or another structural brain lesion with neurological sequelae Other CNS conditions: non-opportunistic primary or metastatic brain tumors, uncontrolled seizure disorder, progressive multiple sclerosis, stroke with neurological sequelae, or dementia due to causes other than HIV (eg, Alzheimer's disease) Constitutional illness (eg, persistent unexplained fever, diarrhea, significant weight loss, disabling weakness) within 30 days of screening Known untreated B12 deficiency or malnutrition (body mass index [BMI] less than 18) at screening Evidence of current hepatitis C virus infection (HCV) (ie, HCV antibody [Ab] positive within 90 days prior to study entry unless also shown to be plasma HCV RNA negative within the same time period) Unstable and advanced liver disease (as defined by the presence of at least one of the following: ascites, encephalopathy, coagulopathy, hypoalbuminemia, esophageal or gastric varices, or persistent jaundice) Prior or current use of any CCR5 antagonist (such as MVC and cenicriviroc [CVC]) and integrase inhibitor (such as RAL, DTG, and elvitegravir [EVG]) Current use of any medication, including antiretrovirals, prohibited in the study (refer to the A5324 protocol-specific web page [PSWP] for the prohibited medications) Breastfeeding Presence of an AIDS-defining opportunistic infection within 6 months prior to entry. Note: Refer to the A5324 Manual of Operations (MOPS) for the list of AIDS-defining opportunistic infections. Active syphilis or treatment for syphilis within 90 days prior to study entry. NOTE: Active syphilis is defined as four-fold increase in serum rapid plasma reagin (RPR) or venereal disease research laboratory (VDRL) tests in an individual with past syphilis, or newly reactive serum RPR or VDRL with a reactive confirmatory test (enzyme immunoassays [EIA] or chemiluminescent assay [CIA], T. pallidum particle agglutination [TP-PA], or fluorescent treponemal antibody absorbed [FTA-ABS]). Known allergy/sensitivity or any hypersensitivity to components of study drugs or their formulation", "candidate_expression": "((AIDS-defining opportunistic infection) AND (Active) AND (Alzheimer's disease) AND (B12 deficiency) AND (Breastfeeding) AND (CCR5 antagonist) AND (CNS conditions) AND (CNS lymphoma) AND (Central nervous system (CNS) infections) AND (Central nervous system (CNS) opportunistic conditions) AND (Constitutional illness) AND (Current) AND (DTG) AND (Developmental delay) AND (Evidence) AND (HCV antibody [Ab]) AND (HIV) AND (MVC) AND (Major depressive disorder) AND (Ongoing) AND (Other) AND (Prior) AND (RAL) AND (T. pallidum particle agglutination [TP-PA]) AND (Toxoplasma) AND (Traumatic Brain Injury (TBI)) AND (Unstable) AND (VDRL) AND (advanced) AND (allergy) AND (another) AND (antiretrovirals) AND (ascites) AND (at least one) AND (at screening) AND (bacterial) AND (body mass index [BMI]) AND (brain abscess) AND (brain tumors) AND (cenicriviroc [CVC]) AND (chemiluminescent assay [CIA]) AND (coagulopathy) AND (components of study drugs) AND (current) AND (dementia) AND (dependence for activities of daily living) AND (diarrhea) AND (disabling weakness) AND (elvitegravir [EVG]) AND (encephalopathy) AND (enzyme immunoassays [EIA]) AND (esophageal varices) AND (evere educational disability) AND (fluorescent treponemal antibody absorbed [FTA-ABS]) AND (four-fold increase) AND (fungal) AND (gastric varices) AND (hepatitis C virus infection (HCV)) AND (hypersensitivity) AND (hypoalbuminemia) AND (impact on activities of daily living) AND (integrase inhibitor) AND (intellectual deficit) AND (intoxication) AND (jaundice) AND (less than 18) AND (liver disease) AND (malnutrition) AND (medication) AND (meningitis) AND (metastatic) AND (mycobacterial) AND (negative) AND (neurologic impairment) AND (neurological sequelae) AND (newly) AND (non-opportunistic) AND (other than) AND (past) AND (persistent) AND (plasma HCV RNA) AND (positive) AND (primary) AND (progressive multifocal leukoencephalopathy (PML)) AND (progressive multiple sclerosis) AND (prohibited in the study) AND (reactive) AND (reactive confirmatory test) AND (seizure disorder) AND (sensitivity) AND (serum RPR) AND (serum rapid plasma reagin (RPR)) AND (significant) AND (stroke) AND (structural brain lesion) AND (study entry) AND (substance use disorder) AND (syphilis) AND (treatment) AND (uncontrolled) AND (unexplained fever) AND (untreated) AND (venereal disease research laboratory (VDRL)) AND (weight loss) AND (withdrawal) AND (within 30 days of screening) AND (within 6 months prior to entry) AND (within 90 days prior to study entry) AND (within the same time period))"}
{"candidate_id": "LLM04724", "doc_id": "NCT03067740_inc", "case_bucket": "other", "source_criterion": "Patients are of American Society of Anesthesiologists (ASA) physical status I and II, aged 8-14 years old, of both gender, with suspected acute appendicitis scheduled for laparoscopic appendicectomy.", "candidate_expression": "((8-14 years old) AND (ASA) AND (American Society of Anesthesiologists physical status) AND (I and II) AND (acute appendicitis) AND (aged) AND (both gender) AND (laparoscopic appendicectomy) AND (scheduled for) AND (suspected))"}
{"candidate_id": "LLM04725", "doc_id": "NCT02810704_exc", "case_bucket": "or", "source_criterion": "Patients undergoing bilateral hip or knee replacement; Patients undergoing total hip or knee replacement who have been enrolled in this study for a prior hip or knee replacement; Patients who are concurrently enrolled in another active interventional clinical trial testing a drug or intervention known or believed to interact with aspirin, warfarin, or rivaroxaban; Patients who have a contraindication to two or more of the three study prophylaxis regimens; Women who are pregnant or breastfeeding, as well as those of reproductive potential unless there is a negative urine pregnancy test on the day of surgery; Patients on chronic (longer than the prior 6 months) anticoagulation other than with antiplatelet medications; Patients with documented gastrointestinal, cerebral, or other hemorrhage within 3 months of the operation; Patients with a known diagnosis of defective hemostasis and past history of clinical bleeding requiring transfusion and treatment; Patients who have had an operative procedure involving the eye, ear, or central nervous system within one month; Patients with severe uncontrolled hypertension with systolic BP > 220mmHg or diastolic BP > 120mmHg; Patients with an absolute body weight of less than 41 kilograms (90.4 lbs) at baseline visit; Vulnerable patient populations including prisoners and institutionalized individuals.", "candidate_expression": "((Patients who are concurrently enrolled in another active interventional clinical trial testing a drug or intervention known or believed to interact with aspirin, warfarin, or rivaroxaban) AND (Women who are pregnant or breastfeeding, as well as those of reproductive potential unless there is a negative urine pregnancy test on the day of surgery) AND (anticoagulation longer than the prior 6 months) AND (atients undergoing total hip or knee replacement who have been enrolled in this study for a prior hip or knee replacement;) AND (bleeding) AND (body weight less than 41 kilograms 90.4 lbs) AND (contraindication) AND (hemostasis defective) AND (hypertension severe uncontrolled) AND (operative procedure within one month) AND (transfusion) AND (treatment) AND NOT (antiplatelet) AND ((cerebral hemorrhage) OR (gastrointestinal hemorrhage) OR (hemorrhage)) AND ((hip replacement) OR (knee replacement)) AND ((central nervous system) OR (ear) OR (eye)) AND ((diastolic BP > 120mmHg) OR (systolic BP > 220mmHg)) AND ((institutionalized) OR (prisoners)) AND ((total hip replacement) OR (total knee replacement)))"}
```
