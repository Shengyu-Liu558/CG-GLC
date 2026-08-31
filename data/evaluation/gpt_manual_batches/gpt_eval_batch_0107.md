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
{"candidate_id": "LLM02651", "doc_id": "NCT02886962_exc", "case_bucket": "or", "source_criterion": "Formal indication to oral anticoagulation beside atrial fibrillation (mechanic heart valves, recurrent thrombophlebitis, antiphospholipid syndrome) Life expectancy < 6 months (e.g., terminal cancer) Live donor transplantation scheduled within 6 months Pregnancy (ß-HCG blood-based assay)or nursing (lactating) women Women of child bearing potential, unless they are using an effective method of birth control Patient under legal guardianship Patients under law protection Known hypersensibility to coumadin or indoine derivatives or to any excipients (CI to oral AVK) Severe liver failure (CI to oral AVK)", "candidate_expression": "((Life expectancy < 6 months) AND (Live donor transplantation scheduled within 6 months) AND (Pregnancy (ß-HCG blood-based assay)or nursing (lactating) women) AND (Women of child bearing potential, unless they are using an effective method of birth control) AND (atrial fibrillation) AND (hypersensibility) AND (indication) AND (liver failure Severe) AND (oral anticoagulation) AND (terminal cancer) AND ((coumadin) OR (indoine)) AND ((antiphospholipid syndrome) OR (mechanic heart valves) OR (recurrent thrombophlebitis)))"}
{"candidate_id": "LLM02652", "doc_id": "NCT01373684_inc", "case_bucket": "other", "source_criterion": "Chronic hepatitis B (HBsAg positive > 6 months) HBeAg negative within six months prior to initiation of peginterferon alfa-2a HBV DNA < 200 IU/ml during nucleos(t)ide analogue (except Telbivudine) treatment within one month prior to initiation of peginterferon alfa-2a Compensated liver disease Age > 18 years Written informed consent", "candidate_expression": "((< 200 IU/ml) AND (> 18 years) AND (> 6 months) AND (Age) AND (Chronic hepatitis B) AND (Compensated) AND (HBV DNA) AND (HBeAg) AND (HBsAg) AND (Telbivudine) AND (Written informed consent) AND (during nucleos(t)ide analogue (except Telbivudine) treatment) AND (except) AND (initiation of peginterferon alfa-2a) AND (liver disease) AND (negative) AND (nucleos(t)ide analogue) AND (nucleos(t)ide analogue (except Telbivudine) treatment) AND (peginterferon alfa-2a) AND (positive) AND (within one month prior to initiation of peginterferon alfa-2a) AND (within six months prior to initiation of peginterferon alfa-2a))"}
{"candidate_id": "LLM02653", "doc_id": "NCT03338296_inc", "case_bucket": "or", "source_criterion": "Healthy male or female adolescents, age 12 to 17 years (inclusive) at Screening, with a body mass index (BMI) that is greater than or equal to the United States-weighted mean of the 95th percentile based on age and sex with a body weight greater than 60 kilograms (kg). Participants with Type 2 diabetes mellitus (T2DM) may have a pre-existing or new diagnosis of T2DM. HbA1c =6.5% fasting plasma glucose (FPG) =126 mg/dL (7.0 mmol/L) Participants and their families not planning to move away from the area for the duration of the study Participants able and willing to comply with all aspects of the study, including a standardized, reduced calorie diet and an age appropriate, increased physical activity program Participants considered in stable health in the opinion of the investigator Able and willing to support and supervise study participation in the opinion of the investigator, including consideration of any existing physical, medical, or mental condition that prevents compliance with the protocol Able and willing to personally comply with and execute all aspects of the study requirements for the caregivers or guardians", "candidate_expression": "((Able to personally comply) AND (HbA1c =6.5%) AND (Healthy) AND (able to comply) AND (adolescents) AND (age 12 to 17 years at Screening) AND (body mass index (BMI) greater than or equal to the United States-weighted mean of the 95th percentile greater than or equal to the 95th percentile) AND (body weight greater than 60 kilograms (kg) based on age based on sex) AND (fasting plasma glucose (FPG) =126 mg/dL 7.0 mmol/L) AND (increased physical activity program age appropriate) AND (reduced calorie diet standardized) AND (stable health) AND (willing to comply) AND (willing to personally comply) AND NOT (planning to move away for the duration of the study) AND ((female) OR (male)) AND ((caregivers) OR (guardians)))"}
{"candidate_id": "LLM02654", "doc_id": "NCT02796378_exc", "case_bucket": "or", "source_criterion": "Cholesterol-lowering drugs Diabetes Mellitus Cardiovascular disease such as arrythmia, ischaemic heart disease. Musculoskeletal disorders preventing the subject to perform physical training Mental disorders preventing the subject to understand the project description.", "candidate_expression": "((Cardiovascular disease) AND (Cholesterol-lowering drugs) AND (Diabetes Mellitus) AND (Mental disorders preventing the subject to understand the project description) AND (Musculoskeletal disorders preventing the subject to perform physical training) AND (arrythmia) AND (ischaemic heart disease))"}
{"candidate_id": "LLM02655", "doc_id": "NCT03262038_inc", "case_bucket": "or", "source_criterion": "3-17 years weight </= 100kg scheduled for urologic or orthopedic procedure necessitating intrathecal morphine ability to use verbal or pictorial pain assessment tools and techniques informed consent and (if applicable) assent", "candidate_expression": "((3-17 years 3-17 years) AND (ability) AND (informed consent and (if applicable) assent) AND (morphine intrathecal) AND (orthopedic procedure) AND (pictorial pain assessment tools and techniques) AND (urologic procedure) AND (verbal pain assessment tools and techniques) AND (weight </= 100kg))"}
{"candidate_id": "LLM02656", "doc_id": "NCT03126214_inc", "case_bucket": "or", "source_criterion": "Age = 65 years with one additional stroke risk factor (hypertension, diabetes, heart failure history of or left ventricular ejection fraction <0.40), previous stroke or transient ischemic attack). Atrial fibrillation and not on oral anticoagulation (OAC) therapy but eligible Atrial fibrillation on sub-optimal OAC", "candidate_expression": "((Age = 65 years) AND (Atrial fibrillation) AND (OAC sub-optimal) AND (diabetes) AND (heart failure) AND (hypertension) AND (left ventricular ejection fraction history <0.40) AND (not) AND (oral anticoagulation (OAC) therapy) AND (risk factor) AND (stroke) AND (transient ischemic attack))"}
{"candidate_id": "LLM02657", "doc_id": "NCT02056626_inc", "case_bucket": "other", "source_criterion": "systolic blood pressure between 140-160 mmHG between 18-80 years old", "candidate_expression": "((old between 18-80 years) AND (systolic blood pressure between 140-160 mmHG))"}
{"candidate_id": "LLM02658", "doc_id": "NCT03480607_inc", "case_bucket": "other", "source_criterion": "American society of anesthesiologist (ASA) physical status I or II", "candidate_expression": "((ASA) AND (American society of anesthesiologist physical status) AND (I or II))"}
{"candidate_id": "LLM02659", "doc_id": "NCT02426034_exc", "case_bucket": "or", "source_criterion": "Subjects with poor-controlled arterial hypertension (systolic blood pressure> 140 mmHg and diastolic blood pressure > 90 mm Hg) despite standard medical management; Coronary heart disease greater than ClassII; II-level arrhythmia (including QT interval prolongation, for man = 450 ms, for woman = 470 ms) together with Class II cardiac dysfunction; Factors that could have an effect on oral medication (such as inability to swallow, chronic diarrhea and intestinal obstruction); Subjects with high gastrointestinal bleeding risk, including the following conditions: local active ulcer lesions with positive fecal occult blood test (++); history of black stool, or vomiting blood in the past 3 months;unresected primary lesion in stomach with positive fecal occult blood test (+), ulcerated gastric carcinoma with massive alimentary tract bleeding risk judged by PIs based on gastric endoscopy result; Abnormal Coagulation (INR>1.5<U+3001>APTT>1.5 UNL), with tendency of bleed; Associated with CNS (central nervous system) metastases; Pregnant or lactating women; Other conditions regimented at investigators' discretion.", "candidate_expression": "((+) AND (++) AND (> 140 mmHg) AND (> 90 mm Hg) AND (>1.5) AND (>1.5 UNL) AND (Abnormal Coagulation) AND (Class II) AND (II-level) AND (Pregnant or lactating women) AND (QT interval prolongation) AND (Subjects) AND (active) AND (alimentary tract) AND (arrhythmia) AND (bleeding risk) AND (cardiac dysfunction) AND (diastolic blood pressure) AND (fecal occult blood test) AND (gastrointestinal bleeding risk) AND (greater than ClassII) AND (high) AND (massive) AND (metastases CNS) AND (past 3 months) AND (poor-controlled) AND (positive) AND (stomach) AND (systolic blood pressure) AND (tendency of bleed) AND ((chronic diarrhea) OR (inability to swallow) OR (intestinal obstruction)) AND ((black stool) OR (vomiting blood)) AND ((primary lesion) OR (ulcer lesions) OR (ulcerated gastric carcinoma)) AND ((APTT) OR (INR)) AND ((Coronary heart disease) OR (arterial hypertension)))"}
{"candidate_id": "LLM02660", "doc_id": "NCT00904202_exc", "case_bucket": "or", "source_criterion": "1. Had a neurological condition other than that associated with their pain diagnosis which, in the opinion of the investigator, would interfere with their ability to participate in the study 2. Were taking a lidocaine-containing product that could not be discontinued while receiving lidocaine 3. Were taking class 1 anti-arrhythmic drugs (e.g., mexiletine, tocainide)", "candidate_expression": "((associated with their pain diagnosis) AND (class 1 anti-arrhythmic drugs) AND (could not be discontinued) AND (lidocaine) AND (lidocaine-containing product) AND (mexiletine) AND (neurological condition) AND (other than) AND (pain diagnosis) AND (receiving lidocaine) AND (tocainide) AND (while receiving lidocaine))"}
{"candidate_id": "LLM02661", "doc_id": "NCT02510404_inc", "case_bucket": "or", "source_criterion": "1. Diagnosis of primary immunodeficiency with established plan to undergo myeloablative or non-myeloablative allogeneic hematopoietic stem cell transplant for treatment thereof or diagnosis of a form of primary immunodeficiency for which hematopoietic stem cell transplantation is not indicated. 2. Active infection with EBV, CMV, and/or Adenovirus, unable to be successfully controlled with standard therapy. 3. Steroids less than 0.5 mg/kg/day prednisone 4. Karnofsky/Lansky score of ≥ 50 5. ANC greater than 500/µL. 6. Bilirubin <2x, AST <3x, Serum creatinine <2x upper limit of normal, Hgb >8.0 7. Pulse oximetry of > 90% on room air 8. Negative pregnancy test (if female of childbearing potential) 9. Patient or parent/guardian capable of providing informed consent.", "candidate_expression": "((ANC greater than 500/µL) AND (AST <3x) AND (Adenovirus) AND (Bilirubin <2x) AND (CMV) AND (EBV) AND (Hgb >8.0) AND (Karnofsky/Lansky score ≥ 50) AND (Patient or parent/guardian capable of providing informed consent) AND (Pulse oximetry on room air > 90%) AND (Serum creatinine <2x upper limit of normal) AND (Steroids) AND (allogeneic hematopoietic stem cell transplant myeloablative) AND (childbearing potential) AND (female) AND (non-myeloablative allogeneic hematopoietic stem cell transplant) AND (prednisone less than 0.5 mg/kg/day) AND (pregnancy test Negative) AND (primary immunodeficiency) AND (standard therapy unable to be controlled) AND NOT (hematopoietic stem cell transplantation))"}
{"candidate_id": "LLM02662", "doc_id": "NCT02260206_inc", "case_bucket": "or", "source_criterion": "Patients needed to pericardiocentesis during RFCA for paroxysmal or persistent atrial fibrillation.", "candidate_expression": "((RFCA) AND (atrial fibrillation) AND (pericardiocentesis during RFCA) AND ((paroxysmal) OR (persistent)))"}
{"candidate_id": "LLM02663", "doc_id": "NCT03040024_inc", "case_bucket": "or", "source_criterion": "Current diagnosis of otolaryngeal cancer and undergoing surgery with general anesthesia Competent to provide informed consent", "candidate_expression": "((Competent to provide informed consent) AND (general anesthesia) AND (otolaryngeal cancer) AND (surgery) AND (undergoing))"}
{"candidate_id": "LLM02664", "doc_id": "NCT01711801_exc", "case_bucket": "or", "source_criterion": "History or presence of any clinically significant disease or disorder Any condition or disease that would render the subject unsuitable for the study, place the subject at undue risk or interfere with the ability of the subject to complete the study in the opinion of the investigator History of clinically significant hypersensitivity or allergic drug reactions Any suspicion or history of alcohol abuse and/or consumption of other drugs of abuse Regular smoker (> 5 cigarettes, > 1 pipeful or > 1 cigar per day) Positive for hepatitis B, hepatitis C or HIV infection Dietary restrictions that would prohibit the consumption of standardized meals Participation in an investigational drug or device study within 90 days prior to screening, as calculated from the follow-up from the previous study", "candidate_expression": "((> 1) AND (> 1 per day) AND (> 5) AND (Any condition or disease that would render the subject unsuitable for the study, place the subject at undue risk or interfere with the ability of the subject to complete the study in the opinion of the investigator) AND (Dietary restrictions) AND (History) AND (Positive) AND (Regular smoker) AND (clinically significant) AND (clinically significant disease or disorder) AND (would prohibit the consumption of standardized meals) AND ((allergic drug reactions) OR (hypersensitivity)) AND ((alcohol abuse) OR (consumption of other drugs of abuse)) AND ((history) OR (suspicion)) AND ((clinically significant disease) OR (clinically significant disorder)) AND ((cigar) OR (cigarettes) OR (pipeful)) AND ((HIV infection) OR (hepatitis B) OR (hepatitis C)))"}
{"candidate_id": "LLM02665", "doc_id": "NCT02334631_exc", "case_bucket": "or", "source_criterion": "Patients with a contraindication to VCE (small bowel strictures, oropharyngeal dysphagia, pregnancy, patients who are not surgical candidates) Endoscopic insertion of video capsule endoscope Inpatient procedures for active GI bleeding Patients with fluid restriction or who are unable to drink up to 900 ml of fluid within 10 minutes prior to the VCE", "candidate_expression": "((Endoscopic insertion) AND (GI bleeding) AND (Inpatient procedures) AND (VCE) AND (active) AND (contraindication) AND (not) AND (prior to the VCE) AND (the VCE) AND (video capsule endoscope) AND ((fluid restriction) OR (unable to drink)) AND ((oropharyngeal dysphagia) OR (pregnancy) OR (small bowel strictures) OR (surgical candidates)))"}
{"candidate_id": "LLM02666", "doc_id": "NCT02680054_inc", "case_bucket": "other", "source_criterion": "Diagnosis of Type 1 diabetes (for at least a year) On multiple daily insulin injections, including basal long-acting insulin and rapid-acting insulin before each meal. HbA1c < 75 mmol/mol (9.0%) Participant and/or parent/legal guardian willing and able to give informed consent for participation in the study. Family have a freezer in which to safely store the test meals. In the Investigator's opinion, is able and willing to comply with all trial requirements.", "candidate_expression": "((HbA1c < 75 mmol/mol 9.0%) AND (In the Investigator's opinion, is able and willing to comply with all trial requirements) AND (Participant and/or parent/legal guardian willing and able to give informed consent for participation in the study) AND (Type 1 diabetes at least a year) AND (insulin basal long-acting) AND (insulin daily) AND (insulin rapid-acting))"}
{"candidate_id": "LLM02667", "doc_id": "NCT01082549_exc", "case_bucket": "or", "source_criterion": "1. Prior treatment with gemcitabine, carboplatin (except in the adjuvant setting), or Iniparib. 2. Past or current history of neoplasm other than the entry diagnosis, with the exception of treated non-melanoma skin cancer or carcinoma in-situ of any primary site, or invasive cancers treated definitively, with treatment ending >5 years previously and no evidence of recurrences. 3. A history of cardiac disease, as defined by: Malignant hypertension Unstable angina Congestive heart failure Myocardial infarction within the previous 6 months Symptomatic, unstable or uncontrolled, cardiac arrhythmias. Patients who have stable, rate-controlled atrial fibrillation are eligible for study enrollment. 4. Active brain metastases. Patients with treated brain metastases are eligible, if (1) radiation therapy was completed at least 2 weeks prior to study entry; (2) follow-up scan shows no disease progression; and (3) patient does not require steroids. 5. Women who are pregnant or lactating. 6. Any serious, active infection (> Grade 2) at the time of treatment. 7. A serious underlying medical condition that would impair the ability of the patient to receive protocol treatment. 8. A major surgical procedure, or significant traumatic injury ≤28 days of beginning treatment, or anticipation of the need for major surgery during the course of the study. 9. Uncontrolled or intercurrent illness including, that in the opinion of the investigator may increase the risks associated with study participation or administration of the investigational products, or that may interfere with the interpretation of the results. 10. History of any medical or psychiatric condition or laboratory abnormality that, in the opinion of the investigator, may increase the risks associated with the study participation or administration of the investigational products, or that may interfere with the interpretation of the results. 11. Known or suspected allergy/hypersensitivity to any agent given in the course of this trial. The above information is not intended to contain all considerations relevant to a patient's potential participation in a clinical trial.", "candidate_expression": "((9. Uncontrolled or intercurrent illness including, that in the opinion of the investigator may increase the risks associated with study participation or administration of the investigational products, or that may interfere with the interpretation of the results.) AND (> Grade 2) AND (>5 years previously) AND (A serious underlying medical condition that would impair the ability of the patient to receive protocol treatment.) AND (Active) AND (Congestive heart failure) AND (History of any medical or psychiatric condition or laboratory abnormality that, in the opinion of the investigator, may increase the risks associated with the study participation or administration of the investigational products, or that may interfere with the interpretation of the results.) AND (Iniparib) AND (Known) AND (Known or suspected allergy/hypersensitivity to any agent given in the course of this trial) AND (Malignant hypertension) AND (Myocardial infarction) AND (Past) AND (Prior) AND (Symptomatic) AND (Uncontrolled) AND (Unstable angina) AND (Women) AND (Women who are pregnant or lactating) AND (active) AND (agent given in the course of this trial) AND (allergy) AND (are eligible) AND (at least 2 weeks prior to study entry) AND (atrial fibrillation) AND (beginning treatment) AND (brain metastases) AND (cancers) AND (carboplatin) AND (carcinoma in-situ) AND (cardiac arrhythmias) AND (cardiac disease) AND (current) AND (disease progression) AND (during the course of the study) AND (entry diagnosis) AND (evidence of recurrences) AND (follow-up scan) AND (gemcitabine) AND (history) AND (hypersensitivity) AND (illness) AND (impair the ability of the patient to receive protocol treatment) AND (in the opinion of the investigator may increase the risks) AND (infection) AND (intercurrent) AND (invasive) AND (laboratory) AND (laboratory abnormality) AND (lactating) AND (major) AND (major surgery) AND (medical condition) AND (need for) AND (neoplasm) AND (no) AND (non-melanoma skin cancer) AND (not) AND (other than the entry diagnosis) AND (pregnant) AND (psychiatric condition) AND (radiation therapy) AND (rate-controlled) AND (require) AND (serious) AND (significant) AND (stable) AND (steroids) AND (study entry) AND (surgical procedure) AND (suspected) AND (the course of the study) AND (traumatic injury) AND (treated) AND (treated definitively) AND (uncontrolled) AND (unstable) AND (with the exception of) AND (within the previous 6 months) AND (would) AND (≤28 days of beginning treatment))"}
{"candidate_id": "LLM02668", "doc_id": "NCT03015818_inc", "case_bucket": "or", "source_criterion": "age > 18 written informed consent SVD defined on echocardiography by an alteration of bioprosthesis leaflets function with a mean transvalvular gradient > 20 mmHg and maximal velocity = 3 m/s and effective orifice area =1.2 cm², and/or an aortic regurgitation more or equal to grade 2 on 4.", "candidate_expression": "((= 3 m/s) AND (=1.2 cm²) AND (> 18) AND (> 20 mmHg) AND (SVD) AND (age) AND (echocardiography) AND (effective orifice area) AND (grade) AND (maximal velocity) AND (mean transvalvular gradient) AND (more or equal to 2 on 4) AND (written informed consent) AND ((alteration of bioprosthesis leaflets function) OR (aortic regurgitation)))"}
{"candidate_id": "LLM02669", "doc_id": "NCT02888704_inc", "case_bucket": "or", "source_criterion": "Of either gender, aged ≥19 and ≤70 years Atopic dermatitis subjects who are coincident with Hanifin and Rajka diagnosis criteria Subacute and chronic atopic subjects who have atopic dermatitis symptoms continually at least 6 months Subjects with over moderate atopic dermatitis (SCORAD score > 20) Subjects who understand and voluntarily sign an informed consent form", "candidate_expression": "((Atopic dermatitis) AND (Hanifin and Rajka diagnosis criteria) AND (SCORAD score > 20) AND (Subjects who understand and voluntarily sign an informed consent form) AND (aged ≥19 and ≤70 years) AND (atopic dermatitis over moderate) AND (dermatitis symptoms continually at least 6 months) AND ((Subacute) OR (chronic)))"}
{"candidate_id": "LLM02670", "doc_id": "NCT02390973_exc", "case_bucket": "or", "source_criterion": "pregnancy past esophageal, gastric or bariatric surgery irritable bowel, unexplained intermittent vomiting, severe abdominal pain, chronic diarrhea or constipation history of gastric or duodenal ulcers pre-operatory hypoalbuminemy history of renal, hepatic, cardiac or pulmonary severe disease taken of corticosteroid in the last month evidence of psycological problem that may affect the capacity to understand the project and to comply with the medical recommandations history of drug use or alcool abuse in the last 12 months history of gastro-intestinal inflammatory diseases", "candidate_expression": "((chronic) AND (corticosteroid) AND (gastro-intestinal inflammatory diseases) AND (hypoalbuminemy) AND (intermittent) AND (last 12 months) AND (last month) AND (pre-operatory) AND (pregnancy) AND (severe) AND ((constipation) OR (diarrhea)) AND ((duodenal ulcers) OR (gastric ulcers)) AND ((cardiac disease) OR (hepatic disease) OR (pulmonary disease) OR (renal disease)) AND ((bariatric surgery) OR (esophageal surgery) OR (gastric surgery)) AND ((alcool abuse) OR (drug use)) AND ((abdominal pain) OR (irritable bowel) OR (vomiting)))"}
{"candidate_id": "LLM02671", "doc_id": "NCT02560766_inc", "case_bucket": "or", "source_criterion": "Male and female adolescent patients, aged 13 to 17 years, diagnosed with RLS based on the IRLSSG consensus criteria (Allen RP 2014) (Appendix 2). Total RLS severity score of 15 or greater on the IRLS rating scale at Visit 1 (screening) and at Visit 2 (baseline) (Appendix 8). RLS symptoms for at least 4 of 7 consecutive evenings/nights during the screening period. Body weight greater than 33.4 kg and a healthy weight using age-based body mass index (BMI) range 5th-85th percentile at screening and baseline. Appendix 3 contains BMI-for-age charts that can be consulted. Estimated creatinine clearance of at least 60 mL/min (using the Cockcroft-Gault equation) at screening only. Signed patient and parent Institutional Review Board (IRB)-approved informed consent/assent form (as applicable) before any study-related procedures are performed.", "candidate_expression": "((BMI) AND (Body weight greater than 33.4 kg) AND (Estimated creatinine clearance at least 60 mL/min) AND (IRLSSG consensus criteria) AND (RLS) AND (RLS symptoms at least 4 of 7 consecutive evenings/nights) AND (Signed patient and parent Institutional Review Board (IRB)-approved informed consent/assent form (as applicable) before any study-related procedures are performed) AND (Total RLS severity score 15 or greater) AND (adolescent) AND (aged 13 to 17 years) AND (body mass index 5th-85th percentile) AND ((Male) OR (female)))"}
{"candidate_id": "LLM02672", "doc_id": "NCT03151603_inc", "case_bucket": "or", "source_criterion": "Women (18-75 years) with suspected UTI at least two symptoms of UTI (dysuria, urgency of micturition, frequency, lower abdominal pain) Written informed consent", "candidate_expression": "((UTI suspected) AND (Women) AND (Written informed consent) AND (dysuria) AND (frequency) AND (lower abdominal pain) AND (symptoms of UTI at least two) AND (urgency of micturition) AND (years 18-75))"}
{"candidate_id": "LLM02673", "doc_id": "NCT02894372_inc", "case_bucket": "or", "source_criterion": "Patients after throat surgeries: tonsillectomy, adenotonsillectomy, uvulopalatoplasty, uvulopalatopharyngoplasty Patients with acute throat diseases: pharyngitis, tonsillitis, pharyngotonsillitis", "candidate_expression": "((acute throat diseases) AND (adenotonsillectomy) AND (pharyngitis) AND (pharyngotonsillitis) AND (throat surgeries) AND (tonsillectomy) AND (tonsillitis) AND (uvulopalatopharyngoplasty) AND (uvulopalatoplasty))"}
{"candidate_id": "LLM02674", "doc_id": "NCT02997215_inc", "case_bucket": "other", "source_criterion": "American Society of Anesthesiologist (ASA) status I-II adult patients undergoing elective laparoscopic cholecystectomy.", "candidate_expression": "((American Society of Anesthesiologist (ASA) status I-II) AND (adult) AND (laparoscopic cholecystectomy elective))"}
{"candidate_id": "LLM02675", "doc_id": "NCT03373669_exc", "case_bucket": "or", "source_criterion": "Presence of a significant medical or psychiatric condition (Examples include: Diagnosis and treatment of tuberculosis (TB) or HIV; renal insufficiency; hepatic disease; oral or parenteral medication known to affect the immune function, such as corticosteroids, other immunosuppressant drugs; or behavioural or memory issues) Ever having received oral cholera vaccine. Receipt of an investigational product (within 30 days before vaccination). History of diarrhoea in 7 days prior to first dose of vaccine (defined as =3 unformed loose stools in 24 hours). History of chronic diarrhea (lasting for more than 2 weeks in the past 6 months) Current use of laxatives, antacids, or other agents to lower stomach acidity? Planning to become pregnant in the next 2 years.", "candidate_expression": "((HIV) AND (Planning to become pregnant in the next 2 years.) AND (Receipt of an investigational product (within 30 days before vaccination).) AND (agents to lower stomach acidity other) AND (antacids) AND (behavioural issues) AND (chronic diarrhea History lasting for more than 2 weeks in the past 6 months) AND (corticosteroids) AND (diarrhoea History in 7 days prior to first dose of vaccine) AND (hepatic disease) AND (immunosuppressant drugs other) AND (laxatives) AND (medical condition) AND (memory issues) AND (oral cholera vaccine) AND (oral medication) AND (parenteral medication) AND (psychiatric condition) AND (renal insufficiency) AND (treatment) AND (tuberculosis (TB)) AND (unformed loose stools in 24 hours =3))"}
```
