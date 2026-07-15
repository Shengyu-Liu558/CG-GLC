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
{"candidate_id": "LLM04526", "doc_id": "NCT02995291_inc", "case_bucket": "other", "source_criterion": "18 years of age or older capable of providing informed consent", "candidate_expression": "((age 18 years of or older) AND (capable of providing informed consent))"}
{"candidate_id": "LLM04527", "doc_id": "NCT02937779_exc", "case_bucket": "other", "source_criterion": "Women refusing HBs Ag test HIV co-infection HCV co-infection HBV treatment ongoing at the day of inclusion Creatinine clearance < 30 mL/min Severe gravidic disease present at inclusion involving life threatening to the mother and/or the child Evidence of pre-existing fetal anomalies incompatible with the child's life Imminent child's birth defined as cervix dilatation up to 7 centimeters Intention to deliver in a maternity not linked to the study Any concomitant medical condition that, according to the clinical site investigator would contraindicate participation in the study. Concurrent participation in any other clinical trial without written agreement of the two study teams", "candidate_expression": "((7 centimeters) AND (< 30 mL/min) AND (Any concomitant medical condition that, according to the clinical site investigator would contraindicate participation in the study) AND (Concurrent participation in any other clinical trial without written agreement of the two study teams) AND (Creatinine clearance) AND (HBV treatment) AND (HBs Ag test) AND (HCV) AND (HIV) AND (Imminent child's birth) AND (Intention to deliver in a maternity not linked to the study) AND (Severe) AND (cervix dilatation) AND (co-infection) AND (fetal anomalies) AND (gravidic disease) AND (life threatening) AND (refusing))"}
{"candidate_id": "LLM04528", "doc_id": "NCT03131050_exc", "case_bucket": "or", "source_criterion": "Currently enrolled in, or discontinued within the last 30 days from, a clinical trial involving an off-label use of an investigational drug. Current Axis I primary psychiatric diagnosis other than major depressive disorder. Organic mental disease, including mental retardation. History of clinically significant disease, including any cardiovascular, hepatic, renal, respiratory, hematologic, endocrinologic, or neurologic disease, or clinically significant laboratory abnormality that is not stabilized or is anticipated to require treatment during the study. Subjects receiving an investigational agent (including different formulation and generic agents of investigational drug) in the previous 3 months prior to screening. Women in pregnancy or lactation, or female of child bearing potential without appropriate birth control measures. Use of antipsychotics or mood stabilizers within 5 days prior to screening. Has received depot antipsychotic medication within one cycle prior to screening. Known allergy or lack of response to mirtazapine. Has received ECT or MECT within 3 months prior to screening. History of anticholinergic drug allergy or complications (allergic reaction, skin rash, urticaria and other allergic reactions which caused by drugs). Smokers. Significant risk of suicidal and/or self-harm behaviors", "candidate_expression": "((Currently enrolled in, or discontinued within the last 30 days from, a clinical trial involving an off-label use of an investigational drug.) AND (ECT) AND (MECT) AND (Organic mental disease) AND (Smokers) AND (Subjects receiving an investigational agent (including different formulation and generic agents of investigational drug) in the previous 3 months prior to screening.) AND (Women in pregnancy or lactation, or female of child bearing potential without appropriate birth control measures.) AND (allergic reaction) AND (allergic reactions other) AND (allergy) AND (anticholinergic drug) AND (antipsychotics) AND (cardiovascular disease) AND (depot antipsychotic medication within one cycle prior to screening) AND (disease clinically significant) AND (drugs) AND (endocrinologic disease) AND (hematologic disease) AND (hepatic disease) AND (laboratory abnormality clinically significant stabilized) AND (lack of response) AND (mental retardation) AND (mirtazapine) AND (mood stabilizers) AND (neurologic disease) AND (psychiatric diagnosis Axis I primary) AND (renal disease) AND (respiratory disease) AND (self-harm behaviors) AND (skin rash) AND (suicidal behaviors) AND (treatment anticipated to require during the study) AND (urticaria) AND NOT (major depressive disorder))"}
{"candidate_id": "LLM04529", "doc_id": "NCT03404479_exc", "case_bucket": "or", "source_criterion": "Secondary knee osteoarthritis Other inflammatory Knee Osteoarthritis (e.g. gout, rheumatoid arthritis, etc.) Patients presenting with gastroesophageal reflux disease, peptic ulcer. Helicobacter infected patients who have not been treated for eradication (recruitment if negative in re-examination after treatment). Short bowel syndrome that can cause inflammatory bowel disease (ulcerative colitis, Crohn's disease) and drug absorption disorder. Intestinal obstruction syndrome Unexplained abdominal pain ALT(Alanine aminotransferase) level of liver function test exceeded 5 times of reference range Total bilirubin level exceeded 2 mg / dL Serum albumin level less than 2 g / dL Ascites Hepatic encephalopathy Hepatitis B, hepatitis C (excluding healthy carriers) or HIV positive MDRD(Modification of Diet in Renal Disease) Estimated Glomerular filtration rate less than 60 mL / m2 Patients with hyperkalemia (over 5.5 meq / L) history of asthma, acute rhinitis, nasal polyps, angioedema, urticaria or allergic reactions to aspirin or other non-steroidal anti-inflammatory drugs(including COX-2 inhibitors). Malignant tumors other than basal cell or squamous cell carcinoma of the skin, CIN(Cervical Intraepitherial Neoplasia) and CIS(Carcinoma in situ) of the cervix, and intraepithelial carcinoma of other areas Within 5 years of consent date. Medical history of hypersensitivity to the components of the investigational products. (The components of test drug 1 and 2, including the Rhein-based drug) Patients with an allergic reaction to sulfonamide. Patients with galactose intolerance, lapp lactase deficiency or glucose-galactose malabsorption. Subjects who have not reached the prescribed period after receiving contraindicated medication or treatment before participation in this clinical trial. Patients receiving contraindicated medication. Alcohol and other drug abuse cases based on 6 months before screening. Pregnant women or nursing mothers who are not willing to stop breastfeeding. (1) Menopause (non-therapy-induced amenorrhea of more than 12 months) Female (2) Female infertility due to surgery (no ovaries and / or uterus) (3) If you have sexual intercourse with only one male partner who has been confirmed to have no semen after fertilization. (4) Female subjects who agreed to abstinence during the clinical trial period. If the subject is assured of an abstinence throughout the trial period.(e.g. clergy) However, intermittent abstinence (eg, contraception using ovulation period, symptothermal) or coitus interrupts is not a case of consent for abstinence. (5) For women of childbearing age, the following methods or methods of contraception use the effective method of contraception to be used during the period of this clinical trial: Oral contraceptive The contraceptive patch Intra uterine device (IUD) contraceptive implant contraceptive injection intrauterine hormonal apparatus Tubal ligation and infertility surgery If 30 days have not elapsed after the date of signing of the previous clinical trial or currently participating in other clinical trials. Patients who are scheduled for surgery during the clinical trial period or who have difficulties in completing the protocol during this clinical trial due to other reasons. In addition to the above, other diseases that the investigator judges to be inappropriate.", "candidate_expression": "(((5) For women of childbearing age, the following methods or methods of contraception use the effective method of contraception to be used during the period of this clinical trial:) AND (6 months before screening) AND (ALT(Alanine aminotransferase) level) AND (Ascites) AND (COX-2 inhibitors) AND (Estimated Glomerular filtration rate) AND (Female) AND (Female subjects who agreed to abstinence during the clinical trial period) AND (Helicobacter infected) AND (Hepatic encephalopathy) AND (However, intermittent abstinence (eg, contraception using ovulation period, symptothermal) or coitus interrupts is not a case of consent for abstinence) AND (If 30 days have not elapsed after the date of signing of the previous clinical trial or currently participating in other clinical trials.) AND (If the subject is assured of an abstinence throughout the trial period.(e.g. clergy)) AND (If you have sexual intercourse with only one male partner who has been confirmed to have no semen after fertilization.) AND (Intestinal obstruction syndrome) AND (Intra uterine device (IUD)) AND (MDRD(Modification of Diet in Renal Disease)) AND (Menopause) AND (Oral contraceptive) AND (Other) AND (Pregnant women or nursing mothers who are not willing to stop breastfeeding) AND (Secondary) AND (Serum albumin level) AND (Short bowel syndrome) AND (Total bilirubin level) AND (Unexplained) AND (Within 5 years of consent date) AND (abdominal pain) AND (allergic reaction) AND (amenorrhea) AND (can cause) AND (components of the investigational products) AND (consent date) AND (contraceptive implant) AND (contraceptive injection) AND (contraceptive patch) AND (contraindicated medication) AND (drug absorption disorder) AND (due to surgery) AND (ess than 2 g / dL) AND (exceeded 2 mg / dL) AND (exceeded 5 times of reference range) AND (excluding) AND (healthy carriers) AND (hyperkalemia) AND (hypersensitivity) AND (infertility) AND (inflammatory Knee Osteoarthritis) AND (inflammatory bowel disease) AND (intrauterine hormonal apparatus) AND (knee osteoarthritis) AND (less than 60 mL / m2) AND (liver function test) AND (more than 12 months) AND (non-therapy-induced) AND (not) AND (other) AND (other than) AND (over 5.5 meq / L) AND (sulfonamide) AND (that can cause inflammatory bowel disease) AND (treated for eradication) AND ((Tubal ligation) OR (infertility surgery)) AND ((Crohn's disease) OR (ulcerative colitis)) AND ((HIV positive) OR (Hepatitis B) OR (hepatitis C)) AND ((acute rhinitis) OR (allergic reactions) OR (angioedema) OR (asthma) OR (nasal polyps) OR (urticaria)) AND ((gout) OR (rheumatoid arthritis)) AND ((aspirin) OR (non-steroidal anti-inflammatory drugs)) AND ((basal cell carcinoma of the skin) OR (squamous cell carcinoma of the skin)) AND ((CIN(Cervical Intraepitherial Neoplasia)) OR (CIS(Carcinoma in situ) of the cervix) OR (Malignant tumors) OR (intraepithelial carcinoma)) AND ((Rhein-based drug) OR (components of test drug 1) OR (components of test drug 2)) AND ((galactose intolerance) OR (glucose-galactose malabsorption) OR (lapp lactase deficiency)) AND ((Alcohol abuse) OR (drug abuse)) AND ((gastroesophageal reflux disease) OR (peptic ulcer)) AND ((no ovaries) OR (no uterus)))"}
{"candidate_id": "LLM04530", "doc_id": "NCT02431442_exc", "case_bucket": "or", "source_criterion": "Fasting blood glucose >126 mg/dL at screening. Heterozygous subjects will be excluded for a fasting blood glucose >140 mg/dL. Resting heart rate <45 bpm or >90 bpm at screening. Abnormal thyroid stimulating hormone (TSH) or thyroxine (T4) levels on screening. Elevated ALT or serum creatinine on screening or any clinically significant abnormalities on screening laboratory tests as determined by the Investigator. History of medically treated diabetes or of treated or medically diagnosed hypertension. Heterozygous subjects who have diagnosed hypertension and are well controlled on treatment (Refer to Exclusion Criteria 20 below), are eligible. . Presence of a skin lesion suspicious for malignancy, unless excised prior to Day 1. History of malignancy except for treated cervical carcinoma in situ in the past 5 years. Active or history of any clinically significant medical condition including renal, hepatic, pulmonary, gastrointestinal, cardiovascular, genitourinary, endocrine, immunologic, metabolic, neurologic, psychiatric or hematological disease, based on Investigator judgment. Acute illness or history of illness, which in the opinion of the Investigator, could pose a threat or harm to the subject or obscure interpretation of laboratory test results or interpretation of study data. Positive hepatitis B surface antigen, positive hepatitis C antibody or positive HIV test at screening or a history of positive testing (e.g. liver biopsy, serology) suggesting acute or chronic hepatitis. Abnormal 12-lead electrocardiogram (ECG) at screening or pre-dose (Day -1 or Day 1), except minor deviations deemed to be of no clinical significance by the Investigator. Received any experimental drugs or devices within 30 days or 5 half lives, whichever is longer, prior to dosing. Ongoing participation in a prior clinical study at the time of screening. Blood donation within 60 days prior to screening or intent to donate within 60 days after Final Study Visit. Hospitalization for major surgery including but not limited to abdominal, thoracic, or cardiovascular surgery within the past 3 months prior to screening, or for a clinically significant non-surgical illness, based on Investigator judgment, within the past 3 months. Planned elective surgery within 30 days of the Final Study Visit. Poor venous access or inability to tolerate venipuncture. History of significant drug hypersensitivity or anaphylaxis. History of hypersensitivity to proteins (e.g., allergy shots). Use of prescription medications on a regular basis. The last use of any prescription medication must have been greater than 5 half-lives for the specific medication or at least 14 days prior to admission (Day -1), whichever is longer. Hormonal contraception is allowed for female subjects. Heterozygous cohorts: Use of prescription medications on a regular basis is not allowed with the following exceptions: Antihypertensives (<3 medications on a stable dose for ≥ 30 days); Statins (dose must be ≤ half the maximum dose; must be on a stable dose ≥3 months); Fibrates (must be on stable dose for ≥3 months); Niacin (must be on stable dose for ≥3 months); Thyroxin (stable dose for ≥ 30 days); The last use of any other prescription medication will need follow the criteria for all other cohorts, as outlined above. Use of prescription medications not listed above may be allowed at the discretion of the Investigator upon consultation with Rhythm. Use of a non-prescription drug and herbal substances during the study (through the Final Study Visit). The last dose of any non-prescription drug must have been taken greater than 5 half-lives for that drug before receiving study drug. Inability to attend all study visits or to comply with protocol requirements including fasting and restrictions on alcohol, caffeine, nicotine and concomitant medication intake. A significant history of drug/solvent abuse within 5 years of screening or a positive test for drugs of abuse test at screening or on Day -1. Positive alcohol (breath test) or nicotine screen at Screening Visit or Day 1 (positive nicotine screen does not apply to heterozygous cohort). History of alcohol abuse (defined as average intake of three or more units of alcohol per day) within 5 years of the Screening Visit. History of tobacco or tobacco product use unless abstinent for at least one year prior to the Screening Visit. This criterion does not apply to heterozygous subjects. Previously randomized and dosed in this study. This criterion does not apply to heterozygous subjects. Any other reason, which in the opinion of the Investigator would confound proper evaluation of the study.", "candidate_expression": "((12-lead electrocardiogram (ECG) Abnormal at screening at pre-dose) AND (Acute illness or history of illness, which in the opinion of the Investigator, could pose a threat or harm to the subject or obscure interpretation of laboratory test results or interpretation of study data.) AND (Antihypertensives stable dose) AND (Any other reason, which in the opinion of the Investigator would confound proper evaluation of the study.) AND (Blood donation within 60 days prior to screening) AND (Fasting blood glucose >126 mg/dL at screening) AND (Fibrates stable dose) AND (Heterozygous) AND (Hormonal contraception) AND (Niacin stable dose) AND (Resting heart rate at screening) AND (Statins ≤ half the maximum dose stable dose) AND (Thyroxin stable dose) AND (Use of prescription medications not listed above may be allowed at the discretion of the Investigator upon consultation with Rhythm.) AND (alcohol abuse History) AND (alcohol three or more units per day within 5 years of the Screening Visit) AND (any non-prescription drug greater than 5 half-lives before receiving study drug) AND (any prescription medication last use greater than 5 half-lives at least 14 days prior to admission) AND (as determined by the Investigator) AND (based on Investigator judgment) AND (clinically significant) AND (elective surgery Planned within 30 days of the Final Study Visit) AND (excised prior to Day 1) AND (fasting blood glucose >140 mg/dL) AND (female) AND (hematological disease) AND (hypersensitivity to allergy shots History) AND (hypersensitivity to proteins History) AND (hypertension well controlled) AND (intent to donate within 60 days after Final Study Visit) AND (liver biopsy) AND (major) AND (malignancy) AND (malignancy History in the past 5 years) AND (medical condition clinically significant) AND (nicotine screen Positive) AND (prescription medications) AND (prescription medications regular basis) AND (serology) AND (significant) AND (skin lesion suspicious for malignancy) AND (surgery major within the past 3 months prior to screening) AND (testing history positive at screening) AND (treated) AND (treatment) AND (venipuncture) AND NOT (abstinent for at least one year prior to the Screening Visit) AND NOT (cervical carcinoma in situ treated) AND ((acute hepatitis) OR (chronic hepatitis)) AND ((Day -1) OR (Day 1)) AND ((experimental devices) OR (experimental drugs)) AND ((within 30 days) OR (within 5 half lives)) AND ((Hospitalization) OR (non-surgical illness clinically significant within the past 3 months)) AND ((thyroid stimulating hormone (TSH) Abnormal on screening) OR (thyroxine (T4) Abnormal on screening)) AND ((abdominal surgery) OR (cardiovascular surgery) OR (thoracic surgery)) AND ((Poor venous access) OR (inability to tolerate venipuncture)) AND ((drug anaphylaxis History significant) OR (drug hypersensitivity History significant)) AND ((ALT Elevated on screening) OR (laboratory tests abnormalities) OR (serum creatinine Elevated on screening)) AND ((herbal substances during the study) OR (non-prescription drug during the study)) AND ((drug/solvent abuse history within 5 years of screening) OR (drugs of abuse test positive at screening)) AND ((alcohol test) OR (breath test)) AND ((tobacco product use) OR (tobacco use)) AND ((diabetes History medically treated) OR (hypertension History)) AND ((medically) OR (medically treated)) AND ((medically) OR (treated)) AND ((Active) OR (history)) AND ((disease cardiovascular) OR (disease endocrine) OR (disease gastrointestinal) OR (disease genitourinary) OR (disease hepatic) OR (disease immunologic) OR (disease pulmonary) OR (disease renal) OR (metabolic disease) OR (neurologic disease) OR (psychiatric disease)) AND ((<45 bpm) OR (>90 bpm)) AND ((HIV test positive) OR (hepatitis B surface antigen Positive) OR (hepatitis C antibody positive)))"}
{"candidate_id": "LLM04531", "doc_id": "NCT02283996_exc", "case_bucket": "other", "source_criterion": "Non-English speaking patients Pregnant women (women of childbearing potential will be advised to undergo regular pregnancy testing) Patients who had previously undergone operative therapy for the condition", "candidate_expression": "((Patients who had previously undergone operative therapy for the condition) AND (Pregnant women (women of childbearing potential will be advised to undergo regular pregnancy testing)))"}
{"candidate_id": "LLM04532", "doc_id": "NCT00730301_inc", "case_bucket": "or", "source_criterion": "Patient diagnosed by HRCT Core Lab with eligible heterogeneous disease distribution and at least one complete oblique fissure. Age from 40 to 75 years BMI < 32 kg/m2 FEV1 < 40% of predicted value, FEV1/FVC < 70% TLC > 120% predicted, RV > 150% predicted. Stable with < 20 mg prednisone (or equivalent) qd PaCO2 < 50mm Hg PaO2 > 45 mm Hg on room air 6-min walk of > 50m (without rehabilitation) or > 100m (with rehabilitation) Nonsmoking for 4 months prior to initial interview and throughout screening The patient agrees to all protocol required follow-up intervals. The patient has no child bearing potential The patient is willing and able to complete protocol required baseline assessments and procedures", "candidate_expression": "((6-min walk) AND (< 20 mg qd) AND (< 32 kg/m2) AND (< 40% of predicted value) AND (< 50mm Hg) AND (< 70%) AND (> 120% predicted) AND (> 150% predicted) AND (> 45 mm Hg) AND (Age) AND (BMI) AND (FEV1) AND (FEV1/FVC) AND (HRCT Core Lab) AND (Nonsmoking) AND (PaCO2) AND (PaO2) AND (RV) AND (Stable) AND (TLC) AND (agrees to all protocol required follow-up intervals) AND (at least one) AND (baseline assessments) AND (baseline procedures) AND (child bearing potential) AND (complete oblique fissure) AND (follow-up intervals) AND (for 4 months prior to initial interview) AND (from 40 to 75 years) AND (heterogeneous disease distribution) AND (initial interview) AND (no) AND (on room air) AND (prednisone) AND (rehabilitation) AND (screening) AND (throughout screening) AND (willing and able to complete protocol) AND (without) AND ((> 100m) OR (> 50m)))"}
{"candidate_id": "LLM04533", "doc_id": "NCT02686021_exc", "case_bucket": "or", "source_criterion": "simultaneous both sided extraction or only upper third molar extraction general anesthesia known or presumed abnormal coagulation status known or presumed liver or renal dysfunction contraindication against metamizole known or suspected (known or suspected allergy against novalgin or other pyrazolones, anaphylactic reaction against NSAIDS, decreased bone marrow function or hematopoesis, hepatic porphyria, glucose-6-phosphate dehydrogenase deficiency, and pregnancy/breastfeeding) contraindication against ibuprofen (known or suspected allergy against ibuprofen, anaphylactic reaction against Nonsteroidal anti-inflammatory drugs (NSAID), active or recurrent stomach or duodenal ulcera or bleeding, severe liver or renal insufficiency, inflammatory bowel syndrome, and pregnancy/breastfeeding) pregnancy and breast feeding mothers", "candidate_expression": "((NSAIDS) AND (Nonsteroidal anti-inflammatory drugs (NSAID)) AND (abnormal coagulation status) AND (contraindication) AND (general anesthesia) AND (ibuprofen) AND (metamizole) AND (molar extraction simultaneous) AND ((liver dysfunction) OR (renal dysfunction)) AND ((known) OR (suspected)) AND ((both sided) OR (only upper third)) AND ((allergy) OR (anaphylactic reaction)) AND ((novalgin) OR (pyrazolones other)) AND ((bone marrow function) OR (hematopoesis)) AND ((breastfeeding) OR (glucose-6-phosphate dehydrogenase deficiency) OR (hepatic porphyria) OR (pregnancy)) AND ((allergy) OR (anaphylactic reaction) OR (breastfeeding) OR (inflammatory bowel syndrome) OR (pregnancy) OR (severe liver insufficiency) OR (severe renal insufficiency)) AND ((active) OR (recurrent)) AND ((bleeding) OR (ulcera)) AND ((duodenal) OR (stomach)) AND ((breast feeding) OR (pregnancy)) AND ((known) OR (presumed)))"}
{"candidate_id": "LLM04534", "doc_id": "NCT02034019_exc", "case_bucket": "other", "source_criterion": "Any intraocular inflammation in the study eye present during the screening slit lamp examination Score greater than \"0\" on the Ocular Pain Assessment in the study eye at Screening Any intraocular inflammation in the study eye present during the screening slit lamp examination", "candidate_expression": "((Ocular Pain Assessment) AND (at Screening) AND (during the screening slit lamp examination) AND (greater than \"0\") AND (intraocular inflammation) AND (slit lamp examination) AND (the screening slit lamp examination))"}
{"candidate_id": "LLM04535", "doc_id": "NCT02926989_exc", "case_bucket": "other", "source_criterion": "An initial plasma sodium concentration of lower than 130 mmol/L An initial plasma sodium concentration of higher than 150 mmol/L An initial plasma potassium concentration of lower than 3.0 mmol/L Need for 10% glucose solution Diabetes Diabetes insipidus Diabetic ketoacidosis Renal disease that needs dialysis Protocol-determined chemotherapy hydration Severe liver disease Inborn errors of metabolism that need protocol-determined fluid therapy", "candidate_expression": "((10% glucose solution Need for) AND (Diabetes) AND (Diabetes insipidus) AND (Diabetic ketoacidosis) AND (Inborn errors of metabolism) AND (Renal disease) AND (chemotherapy hydration Protocol-determined) AND (dialysis needs) AND (fluid therapy need protocol-determined) AND (liver disease Severe) AND (plasma potassium concentration initial lower than 3.0 mmol/L) AND (plasma sodium concentration initial higher than 150 mmol/L) AND (plasma sodium concentration initial lower than 130 mmol/L))"}
{"candidate_id": "LLM04536", "doc_id": "NCT02678663_exc", "case_bucket": "or", "source_criterion": "Anticoagulant therapy during the past 1 week of the procedure Known coagulopathy History of liver cirrhosis, chronic kidney disease, malignancy, inflammatory bowel disease, significant infectious disease, polyposis syndrome", "candidate_expression": "((Anticoagulant) AND (History) AND (chronic kidney disease) AND (coagulopathy) AND (during the past 1 week) AND (inflammatory bowel disease) AND (liver cirrhosis) AND (malignancy) AND (polyposis syndrome) AND (procedure) AND (significant infectious disease))"}
{"candidate_id": "LLM04537", "doc_id": "NCT02570321_inc", "case_bucket": "or", "source_criterion": "Corneal ulcer that is smear positive for either bacteria or filamentous fungus Pinhole visual acuity worse than 20/70 in the affected eye Not treated already with antimicrobial medications at presentation Age over 18 years Basic understanding of the study as determined by the physician Commitment to return for follow up visits", "candidate_expression": "((Age) AND (Commitment to return for follow up visits) AND (Corneal ulcer) AND (Pinhole visual acuity) AND (antimicrobial medications) AND (bacteria) AND (filamentous fungus) AND (over 18 years) AND (positive) AND (smear) AND (worse than 20/70))"}
{"candidate_id": "LLM04538", "doc_id": "NCT00317148_exc", "case_bucket": "or", "source_criterion": "Body mass index (BMI) of 35 kg/m2 or more. Significant metabolic and endocrine diseases. Diagnosis of cancer. Use of steroids or drugs that interfere with the metabolism of estrogen. Use of any systemic estrogen, progestin, or DHEA in the eight weeks prior to randomization. Use of alternative therapies or natural products to treat postmenopausal symptoms in the four weeks prior to randomization. Palpable fibroids or uterine prolapse: Grade 2 or 3. Cigarette smoking", "candidate_expression": "((2 or 3) AND (35 kg/m2 or more) AND (Body mass index (BMI)) AND (Cigarette smoking) AND (DHEA) AND (Grade) AND (Palpable fibroids) AND (alternative therapies) AND (cancer) AND (drugs that interfere with the metabolism of estrogen) AND (endocrine diseases) AND (in the eight weeks prior to randomization) AND (in the four weeks prior to randomization) AND (metabolic diseases) AND (natural products) AND (postmenopausal symptoms) AND (steroids) AND (systemic estrogen) AND (systemic progestin) AND (uterine prolapse))"}
{"candidate_id": "LLM04539", "doc_id": "NCT02573909_inc", "case_bucket": "other", "source_criterion": "Planned gynecological lower abdomen surgery with epidural pain treatment Informed consent obtained", "candidate_expression": "((Planned) AND (epidural pain treatment) AND (gynecological lower abdomen surgery))"}
{"candidate_id": "LLM04540", "doc_id": "NCT03104816_exc", "case_bucket": "or", "source_criterion": "Patients requiring surgery for neoplastic processes Allergy to acetaminophen Liver dysfunction and elevated Liver Function Tests (LFTs) Alcohol or drug dependency Mental retardation Less than 50 kg of weight regnant women Patients requiring long-acting opioid pain management (including fentanyl patch, oxycontin, etc) for over 3 weeks immediately prior to surgery", "candidate_expression": "((Alcohol dependency) AND (Allergy) AND (LFTs) AND (Liver Function Tests elevated) AND (Liver dysfunction) AND (Mental retardation) AND (acetaminophen) AND (drug dependency) AND (fentanyl patch) AND (long-acting opioid requiring for over 3 weeks immediately prior to surgery) AND (neoplastic processes) AND (oxycontin) AND (regnant) AND (surgery) AND (weight Less than 50 kg) AND (women))"}
{"candidate_id": "LLM04541", "doc_id": "NCT02997215_inc", "case_bucket": "other", "source_criterion": "American Society of Anesthesiologist (ASA) status I-II adult patients undergoing elective laparoscopic cholecystectomy.", "candidate_expression": "((American Society of Anesthesiologist (ASA)) AND (adult) AND (elective) AND (laparoscopic cholecystectomy) AND (status I-II))"}
{"candidate_id": "LLM04542", "doc_id": "NCT02592980_inc", "case_bucket": "other", "source_criterion": "Only patients with atrial fibrillation, above 18 years, and with TTR <50% based on the last three values of INR will be included in this study.", "candidate_expression": "((<50%) AND (TTR) AND (above 18 years) AND (atrial fibrillation) AND (based on the last three values of INR) AND (years))"}
{"candidate_id": "LLM04543", "doc_id": "NCT03247738_exc", "case_bucket": "or", "source_criterion": "Inability to provide written informed consent Known history of prior intracranial bleeding On treatment with a P2Y12 receptor antagonist (ticlopidine, clopidogrel, prasugrel, ticagrelor) in the prior 10 days Known allergies to aspirin, ticagrelor or cangrelor On treatment with oral anticoagulant Treatment with glycoprotein IIb/IIIa inhibitors Fibrinolytics within 24 hours Active bleeding High risk of bleeding Known platelet count <80x106/mL Known hemoglobin <10 g/dL Intubated patients (prior to randomization) Known creatinine clearance <30 mL/minute or on hemodialysis. Known severe hepatic dysfunction Patients with sick sinus syndrome (SSS) or high degree AV block without pacemaker protection Current treatment with drugs interfering with CYP3A4 metabolism (to avoid interaction with ticagrelor): Ketoconazole, itraconazole, voriconazole, clarithromycin, nefazodone, ritonavir, saquinavir, nelfinavir, indinavir, atazanavir, and telithromizycin. Pregnant or lactating females.", "candidate_expression": "((<10 g/dL) AND (<30 mL/minute) AND (<80x106/mL) AND (AV block) AND (Active bleeding) AND (CYP3A4 metabolism) AND (Fibrinolytics) AND (High risk) AND (Inability to provide written informed consent) AND (Intubated) AND (Ketoconazole) AND (P2Y12 receptor antagonist) AND (Pregnant) AND (SSS) AND (allergies) AND (anticoagulant) AND (aspirin) AND (atazanavir) AND (bleeding) AND (cangrelor) AND (clarithromycin) AND (clopidogrel) AND (creatinine clearance) AND (drugs) AND (females) AND (glycoprotein IIb/IIIa inhibitors) AND (hemodialysis) AND (hemoglobin) AND (hepatic dysfunction) AND (high degree) AND (indinavir) AND (interfering with) AND (intracranial bleeding) AND (itraconazole) AND (lactating) AND (nefazodone) AND (nelfinavir) AND (oral) AND (pacemaker) AND (platelet count) AND (prasugrel) AND (prior) AND (prior 10 days) AND (prior to randomization) AND (randomization) AND (ritonavir) AND (saquinavir) AND (severe) AND (sick sinus syndrome) AND (telithromizycin) AND (ticagrelor) AND (ticlopidine) AND (voriconazole) AND (within 24 hours) AND (without))"}
{"candidate_id": "LLM04544", "doc_id": "NCT02765217_inc", "case_bucket": "or", "source_criterion": "Children receiving amoxicilline-clavulanic acid (50-90 mg/kg/day, twice daily) due to acute otitis media or acute sinusitis", "candidate_expression": "((50-90 mg/kg/day) AND (Children) AND (amoxicilline-clavulanic acid) AND (twice daily) AND ((acute otitis media) OR (acute sinusitis)))"}
{"candidate_id": "LLM04545", "doc_id": "NCT01696617_inc", "case_bucket": "or", "source_criterion": "Age : 18-65 Patients with major depressive disorder according to DSM-IV criteria that have lasted >8 weeks MADRS total score of 18 or higher Patients who responded inadequately (a score of >18 on the MADRS) to first-line antidepressant treatment of 4 week duration Current use of standard antidepressant treatment in monotherapy or combination of 2 antidepressants : escitalopram (10 - 20mg/d), fluoxetine(20 - 40mg/d), paroxetine CR(25 - 50mg/d), sertraline(100 - 150mg/d), mirtazapine (15 - 45mg/d), duloxetine (30 - 60mg/d) or venlafaxine ER(150-225mg/d)", "candidate_expression": "((Age 18-65) AND (DSM-IV criteria) AND (MADRS score of 18 or higher) AND (MADRS score of >18) AND (antidepressant first-line of 4 week) AND (antidepressant standard monotherapy) AND (antidepressants 2) AND (duloxetine 30 - 60mg/d) AND (escitalopram 10 - 20mg/d) AND (fluoxetine 20 - 40mg/d) AND (major depressive disorder lasted >8 weeks) AND (mirtazapine 15 - 45mg/d) AND (paroxetine CR 25 - 50mg/d) AND (responded inadequately) AND (sertraline 100 - 150mg/d) AND (venlafaxine ER 150-225mg/d))"}
{"candidate_id": "LLM04546", "doc_id": "NCT02631512_inc", "case_bucket": "or", "source_criterion": "Type I or II diabetes mellitus. Target ulcer area between 0.5 and 5 sqcm, and more than 4 weeks old. Ankle-brachial pressure index above 0.7.", "candidate_expression": "((Ankle-brachial pressure index) AND (Target ulcer area) AND (above 0.7) AND (between 0.5 and 5 sqcm) AND (more than 4 weeks old) AND ((Type I diabetes mellitus) OR (Type II diabetes mellitus)))"}
{"candidate_id": "LLM04547", "doc_id": "NCT03631355_exc", "case_bucket": "or", "source_criterion": "Legally incompetent or mentally impaired (e.g., minors, Alzheimer's subjects, dementia, etc.) Younger than 18 years of age Any patient considered a vulnerable subject Have bleeding or clotting disorder Preoperative anticoagulation therapy Abnormal coagulation profile Renal disorder or insufficiency Sickle cell disease", "candidate_expression": "((Abnormal) AND (Abnormal coagulation profile) AND (Alzheimer's) AND (Legally incompetent) AND (Preoperative) AND (Renal disorder) AND (Renal insufficiency) AND (Sickle cell disease) AND (Younger than 18 years) AND (age) AND (anticoagulation) AND (anticoagulation therapy) AND (bleeding disorder) AND (clotting disorder) AND (coagulation profile) AND (dementia) AND (mentally impaired) AND (minors) AND (vulnerable subject))"}
{"candidate_id": "LLM04548", "doc_id": "NCT02406495_exc", "case_bucket": "or", "source_criterion": "Is not a habitual wearer of Avaira sphere lenses Has a CL prescription outside the range of the available parameters of the study lenses. Has a spectacle cylinder ≥1.00D of cylinder in either eye. Has a history of not achieving comfortable CL wear (5 days per week; > 8 hours/day) Has contact lens best corrected distance vision worse than 20/25 (0.10 logMAR) in either eye. Presence of clinically significant (grade 2-4) anterior segment abnormalities Presence of ocular or systemic disease or need of medications which might interfere with contact lens wear. Slit lamp findings that would contraindicate contact lens wear such as: Pathological dry eye or associated findings Pterygium, pinguecula, or corneal scars within the visual axis Neovascularization > 0.75 mm in from of the limbus Giant papillary conjunctivitis (GCP) worse than grade 1 Anterior uveitis or iritis (past or present) Seborrheic eczema, Seborrheic conjunctivitis History of corneal ulcers or fungal infections Poor personal hygiene Has a known history of corneal hypoesthesia (reduced corneal sensitivity) Has aphakia, keratoconus or a highly irregular cornea. Has Presbyopia or has dependence on spectacles for near work over the contact lenses. Has undergone corneal refractive surgery. Is participating in any other type of eye related clinical or research study", "candidate_expression": "((2-4) AND (5 days per week) AND (> 0.75 mm in from of the limbus) AND (> 8 hours/day) AND (Anterior uveitis) AND (Avaira sphere lenses) AND (CL prescription) AND (Giant papillary conjunctivitis (GCP)) AND (History) AND (Neovascularization) AND (Pathological dry eye) AND (Poor personal hygiene) AND (Presbyopia) AND (Pterygium) AND (Seborrheic conjunctivitis) AND (Seborrheic eczema) AND (Slit lamp) AND (anterior segment abnormalities) AND (aphakia) AND (associated findings) AND (clinically significant) AND (comfortable CL wear) AND (contact lens best corrected distance vision) AND (contraindicate contact lens) AND (corneal hypoesthesia) AND (corneal refractive surgery) AND (corneal scars) AND (corneal ulcers) AND (dependence on spectacles for near work) AND (findings) AND (fungal infections) AND (grade 2-4) AND (highly irregular cornea) AND (history) AND (iritis) AND (keratoconus) AND (might interfere with contact lens wear) AND (need of medications) AND (not) AND (ocular disease) AND (outside the range of the available parameters of the study lenses) AND (past) AND (pinguecula) AND (present) AND (reduced corneal sensitivity) AND (spectacle cylinder) AND (systemic disease) AND (within the visual axis) AND (worse than 0.10 logMAR in either eye) AND (worse than 20/25 in either eye) AND (worse than grade 1) AND (≥1.00D))"}
{"candidate_id": "LLM04549", "doc_id": "NCT03177811_inc", "case_bucket": "or", "source_criterion": "Male and female patients, age 18-75 yrs. COPD diagnosed according to GOLD, FEV1 40-80% predicted, SpO2 =92% at 750 m. Born, raised and currently living at low altitude (<800m). Written informed consent.", "candidate_expression": "((18-75 yrs) AND (40-80% predicted) AND (=92% at 750 m) AND (COPD) AND (FEV1) AND (GOLD) AND (Male) AND (SpO2) AND (Written informed consent) AND (age) AND (female))"}
{"candidate_id": "LLM04550", "doc_id": "NCT02849483_inc", "case_bucket": "other", "source_criterion": "20-70 yrs of age ASA(American Society of Anesthesiologists) physical status class I or II Scheduled for gynecological laparoscopic surgery", "candidate_expression": "((ASA physical status class I or II) AND (American Society of Anesthesiologists) AND (age 20-70 yrs) AND (laparoscopic surgery Scheduled gynecological))"}
```
