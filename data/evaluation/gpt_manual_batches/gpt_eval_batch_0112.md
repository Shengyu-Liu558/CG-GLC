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
{"candidate_id": "LLM02776", "doc_id": "NCT02973035_exc", "case_bucket": "or", "source_criterion": "Unwillingness or inability to comply with the procedures described in this protocol Planned cardiac surgery or planned major non-cardiac surgery within the study period. Stroke or coronary revascularization in the past 6 months. Clinically significant pulmonary disease. Untreated hyperthyroidism, or hypothyroidism. A diagnosis of cancer (other than superficial squamous or basal cell skin cancer) in the past 3 years or current treatment for the active cancer. Female of child-bearing potential who do not use adequate contraception and women who are pregnant or breast-feeding Any clinically significant abnormality identified at the screening visit, physical examination, laboratory tests, or electrocardiogram which, in the judgment of the Investigator, would preclude safe completion of the study. LV ejection fraction < 50%. Significant renal disease manifested by serum creatinine > 2.5 mg/dL Hepatic disease or biliary tract obstruction, or significant hepatic enzyme elevation (ALT or AST > 3 times upper limit of normal). History of intolerance to ARB or amlodipine. Hypertrophic or restrictive cardiomyopathy. Moderate or severe valvular disease. Constrictive pericarditis Atrial fibrillation with a heart rate > 120/min. Sitting systolic BP < 100 mmHg", "candidate_expression": "((Any clinically significant abnormality identified at the screening visit, physical examination, laboratory tests, or electrocardiogram which, in the judgment of the Investigator, would preclude safe completion of the study) AND (Atrial fibrillation) AND (Constrictive pericarditis) AND (Female of child-bearing potential who do not use adequate contraception and women who are pregnant or breast-feeding) AND (Hypertrophic cardiomyopathy) AND (LV ejection fraction < 50%) AND (Unwillingness or inability to comply with the procedures described in this protocol) AND (cancer) AND (cancer active) AND (heart rate > 120/min) AND (intolerance) AND (pulmonary disease Clinically significant) AND (renal disease Significant) AND (restrictive cardiomyopathy) AND (serum creatinine > 2.5 mg/dL) AND (systolic BP Sitting < 100 mmHg) AND (treatment) AND (valvular disease) AND ((Stroke revascularization) OR (coronary revascularization)) AND ((hyperthyroidism) OR (hypothyroidism)) AND ((basal cell skin cancer) OR (superficial squamous skin cancer)) AND ((Hepatic disease) OR (biliary tract obstruction) OR (hepatic enzyme elevation significant)) AND ((ALT) OR (AST)) AND ((ARB) OR (amlodipine)) AND ((Moderate) OR (severe)) AND ((cardiac surgery Planned) OR (surgery planned major cardiac)))"}
{"candidate_id": "LLM02777", "doc_id": "NCT01218737_exc", "case_bucket": "or", "source_criterion": "Surgery and/or previous ocular pathology (presence of scar/change in the cornea, glaucoma, retinopathies, etc.). Patient has diabetes or is immunodepressed. Any systemic infection during the study. Signs and/or symptoms of ocular inflammation/infection (bacterial, viral, fungal, caused by Chlamydia, by Mycobacterium, Acanthamoeba or of allergic etiology). Have used any systemic or topical antibiotics for ocular infection in the previous 14 days. Patient has known hypersensitivity to any of the components of the formulations used in the study.", "candidate_expression": "((Acanthamoeba) AND (Chlamydia) AND (Mycobacterium) AND (Surgery) AND (allergic etiology) AND (bacterial etiology) AND (caused by Acanthamoeba) AND (caused by Chlamydia) AND (caused by Mycobacterium) AND (change in the cornea) AND (components of the formulations) AND (diabetes) AND (during the study) AND (fungal etiology) AND (glaucoma) AND (hypersensitivity) AND (immunodepressed) AND (in the previous 14 days) AND (infection) AND (ocular infection) AND (ocular inflammation) AND (ocular pathology) AND (previous) AND (retinopathies) AND (scar) AND (systemic) AND (systemic antibiotics) AND (the study) AND (topical) AND (topical antibiotics) AND (viral etiology))"}
{"candidate_id": "LLM02778", "doc_id": "NCT02570321_exc", "case_bucket": "or", "source_criterion": "Evidence of concomitant infection on exam or gram stain (i.e. herpes, both bacteria and acanthamoeba on gram stain) Impending or frank perforation at recruitment Involvement of sclera at presentation Non-infectious or autoimmune keratitis History of corneal transplantation or recent intraocular surgery No light perception in the affected eye Pinhole visual acuity worse than 20/200 in the unaffected eye Participants who are decisionally and/or cognitively impaired", "candidate_expression": "((Involvement of sclera) AND (Pinhole visual acuity worse than 20/200) AND (cognitively impaired) AND (concomitant infection) AND (perforation) AND NOT (light perception) AND ((Non-infectious keratitis) OR (autoimmune keratitis)) AND ((corneal transplantation) OR (intraocular surgery)))"}
{"candidate_id": "LLM02779", "doc_id": "NCT02573909_inc", "case_bucket": "other", "source_criterion": "Planned gynecological lower abdomen surgery with epidural pain treatment Informed consent obtained", "candidate_expression": "((epidural pain treatment) AND (gynecological lower abdomen surgery Planned))"}
{"candidate_id": "LLM02780", "doc_id": "NCT02396732_inc", "case_bucket": "or", "source_criterion": "Age 18 years or older Blunt or penetrating trauma Requires VTE thromboprophylaxis High-risk for VTE", "candidate_expression": "((Age 18 years or older) AND (VTE) AND (VTE High-risk) AND (thromboprophylaxis) AND ((Blunt trauma) OR (penetrating trauma)))"}
{"candidate_id": "LLM02781", "doc_id": "NCT02322203_exc", "case_bucket": "or", "source_criterion": "Subjects taking any lipid modification therapy, including but not limited to statins, fibrates and bile acid sequestrants. Subjects taking fish oil or any other supplements, which in the investigator s opinion may interfere with the study. Subjects with acute liver disease or active peptic ulcer disease. Subjects with elevated uric acid levels greater than 10 mg/dL or gout Pregnancy or women currently breastfeeding. Female subjects taking hormonal contraceptives or hormone replacement therapy may be included in this study only if they have been on a stable dose for at least 3 months. BMI less than 18.5 Subjects with weight that varies greater than 20% over the past 3 months. Subjects taking the following medications for at least six weeks, which may interfere with the study, will be excluded: BAS, antibiotics, anticoagulants, anticonvulsants, antiarrhythmic, Cyclosporine, Mycophenolate and Synthroid. Subjects with chronic diarrhea, gastric bypass or lap band procedures, ostomies, bowel motility problems, or other conditions that could affect intestinal fat absorption. Subjects initiating new medications or patients on multiple medications may also be excluded. Inability to swallow capsules Patients with a history of type I or type II diabetes or HbA1c greater than 6.5%. Volunteers may also be excluded, if in the opinion of the study investigators, they have some other condition or disorder that may adversely affect the outcome of the study or the safety of the volunteer.", "candidate_expression": "((BMI less than 18.5) AND (Female) AND (Inability to swallow capsules) AND (Subjects taking fish oil or any other supplements, which in the investigator s opinion may interfere with the study.) AND (Volunteers may also be excluded, if in the opinion of the study investigators, they have some other condition or disorder that may adversely affect the outcome of the study or the safety of the volunteer.) AND (acute liver disease) AND (fish oil) AND (lipid modification therapy) AND (peptic ulcer disease active greater than 10 mg/dL) AND (weight varies greater than 20%) AND (women) AND ((gout) OR (uric acid levels elevated)) AND ((Pregnancy) OR (breastfeeding)) AND ((hormonal contraceptives) OR (hormone replacement therapy)) AND ((BAS) OR (Cyclosporine) OR (Mycophenolate) OR (Synthroid) OR (antiarrhythmic) OR (antibiotics) OR (anticoagulants) OR (anticonvulsants)) AND ((bile acid sequestrants) OR (fibrates) OR (statins)) AND ((bowel motility problems) OR (chronic diarrhea) OR (conditions that could affect intestinal fat absorption) OR (gastric bypass) OR (lap band procedures) OR (ostomies)) AND ((HbA1c greater than 6.5%) OR (type I diabetes) OR (type II diabetes)))"}
{"candidate_id": "LLM02782", "doc_id": "NCT03234816_exc", "case_bucket": "other", "source_criterion": "Cardiac morbidities Hypertensive disorders of pregnancy, Peripartum bleeding Baseline systolic blood pressure (SBP) < 100 mmHg Body mass index > 35", "candidate_expression": "((Body mass index > 35) AND (Cardiac morbidities) AND (Hypertensive disorders of pregnancy) AND (Peripartum bleeding) AND (SBP) AND (systolic blood pressure Baseline < 100 mmHg))"}
{"candidate_id": "LLM02783", "doc_id": "NCT02781610_exc", "case_bucket": "or", "source_criterion": "Previous randomization in this study Treatment with IV antibiotics in the 6 weeks prior to Visit 1 Admission to the intensive care unit for current pulmonary exacerbation in the two weeks prior to Visit 2, unless admission was due to a desensitization protocol Pneumothorax in the two weeks prior to Visit 2 Primary diagnosis for current hospitalization is unrelated to worsening lower respiratory symptoms (e.g., pulmonary clean out, distal intestinal obstruction syndrome (DIOS), sinusitis) Massive hemoptysis defined as > 250 cc in a 24 hour period or 100 cc/day over 4 consecutive days occurring in the two weeks prior to Visit 2 Current pulmonary exacerbation thought to be due to allergic bronchopulmonary aspergillosis (ABPA) At Visit 1, receiving ongoing treatment with a duration of more than 2 weeks with prednisone equivalent to >10mg/day History of solid organ transplantation Receiving antimicrobial therapy to treat non-tuberculous mycobacterium (e.g., M. abscessus, M. avium complex) in the two weeks prior to Visit 2", "candidate_expression": "((>10mg/day) AND (ABPA) AND (Admission to the intensive care unit) AND (At Visit 1 more than 2 weeks) AND (DIOS) AND (IV antibiotics) AND (M. abscessus) AND (M. avium complex) AND (Massive) AND (Pneumothorax) AND (Primary diagnosis) AND (Visit 1) AND (Visit 2) AND (allergic bronchopulmonary aspergillosis) AND (antimicrobial therapy) AND (current hospitalization) AND (desensitization protocol) AND (hemoptysis) AND (in a 24 hour period) AND (in the 6 weeks prior to Visit 1) AND (in the two weeks prior to Visit 2) AND (intensive care unit) AND (lower respiratory symptoms) AND (non-tuberculous mycobacterium) AND (over 4 consecutive days) AND (prednisone) AND (pulmonary exacerbation) AND (solid organ transplantation) AND (unless) AND (unrelated) AND (worsening) AND ((distal intestinal obstruction syndrome) OR (pulmonary clean out) OR (sinusitis)) AND ((100 cc/day) OR (> 250 cc)))"}
{"candidate_id": "LLM02784", "doc_id": "NCT03059069_exc", "case_bucket": "or", "source_criterion": "Type 1 diabetes, Secondary diabetes, gestational diabetes Ongoing dementia treatment or anti-depressive disorder medication Uncontrolled psychiatric disorder BDI = 30 points Heavy alcoholics Underlying chronic liver disease (hemochromatosis, liver cell carcinoma, autoimmune liver disease, liver cirrhosis, chronic viral hepatitis) Allergy or hypersensitivity to target medication or any of its components Renal failure, moderate or severe renal impairment (estimated glomerular filtration rate < 30 mL/min/1.73 m2), or ongoing dialysis Abnormal liver function (AST/ALT > x3 upper normal limit) History of alcohol or drug abuse in the previous 3 months Premenopausal women who are nursing or pregnant Human immunodeficiency virus (HIV) or human immunodeficiency virus (AIDS) chronic pancreatitis or pancreatic cancer", "candidate_expression": "((< 30 mL/min/1.73 m2) AND (= 30 points) AND (> x3 upper normal limit) AND (AST/ALT) AND (Abnormal) AND (BDI) AND (Heavy) AND (Ongoing) AND (Premenopausal) AND (Uncontrolled) AND (alcoholics) AND (chronic liver disease) AND (dementia) AND (estimated glomerular filtration rate) AND (in the previous 3 months) AND (liver function) AND (ongoing) AND (renal impairment) AND (target medication) AND (women) AND ((autoimmune liver disease) OR (chronic viral hepatitis) OR (hemochromatosis) OR (liver cell carcinoma) OR (liver cirrhosis)) AND ((Secondary diabetes) OR (Type 1 diabetes) OR (gestational diabetes)) AND ((Allergy) OR (hypersensitivity)) AND ((Renal failure) OR (dialysis)) AND ((moderate) OR (severe)) AND ((alcohol abuse) OR (drug abuse)) AND ((nursing) OR (pregnant)) AND ((Human immunodeficiency virus (HIV)) OR (human immunodeficiency virus (AIDS))) AND ((chronic pancreatitis) OR (pancreatic cancer)) AND ((anti-depressive disorder medication) OR (treatment)))"}
{"candidate_id": "LLM02785", "doc_id": "NCT02270970_inc", "case_bucket": "or", "source_criterion": "Patients who meet 1987 ACR criteria for SLE with 1996 modifications SLEDAI >/= 6 at screening visit Positive ANA OR anti-dsDNA within one year of screening In the opinion of the investigator there is intent to treat with a biologic (e.g. patient failed standard of care treatment) however there is no organ threatening disease", "candidate_expression": "((1987 ACR criteria with 1996 modifications) AND (>/= 6) AND (In the opinion of the investigator there is intent to treat with a biologic (e.g. patient failed standard of care treatment) however there is no organ threatening disease) AND (Positive) AND (SLE) AND (SLEDAI) AND (at screening visit) AND (screening) AND (screening visit) AND (within one year of screening) AND ((ANA) OR (anti-dsDNA)))"}
{"candidate_id": "LLM02786", "doc_id": "NCT03100513_exc", "case_bucket": "or", "source_criterion": "Patients with active GIT bleeding. Patients with history of bowel obstruction, perforation. Patients with history of allergy to PEG. Treatment with rifaximin or neomycin in the previous 7 days. Patients with major psychiatric illness. Patients receiving benzodiazepines and narcotics. Patients with compromised renal. Patients receiving medications highly bound to plasma proteins eg. Warfarin. Pregnant or lactating women. Fulminant hepatic failure.", "candidate_expression": "((Fulminant) AND (GIT bleeding) AND (PEG) AND (Warfarin) AND (active) AND (allergy) AND (compromised renal) AND (hepatic failure) AND (history) AND (in the previous 7 days) AND (major psychiatric illness) AND (medications highly bound to plasma proteins) AND (women) AND ((neomycin) OR (rifaximin)) AND ((benzodiazepines) OR (narcotics)) AND ((Pregnant) OR (lactating)) AND ((bowel obstruction) OR (bowel perforation)))"}
{"candidate_id": "LLM02787", "doc_id": "NCT00752310_exc", "case_bucket": "or", "source_criterion": "No positive HIV 1 or HIV 2 test at screening no history of significant skin disease such as, but not limited to rash or eruptions, drug allergies, food allergy, dermatitis, eczema, psoriasis, or urticaria no history of allergy to drugs such as, but not limited to, sulphonamides and penicillins no previously demonstrated clinically significant allergy or hypersensitivity to any of the excipients of the investigational medication administered in this trial no female subject of childbearing potential without use of effective nonhormonal birth control methods, or not willing to continue practicing these birth control methods for at least 30 days after the end of the treatment period no positive pregnancy test or breast feeding at screening", "candidate_expression": "((allergy history) AND (childbearing potential) AND (excipients of the investigational medication) AND (female) AND (skin disease history significant screening) AND ((dermatitis) OR (drug allergies) OR (eczema) OR (eruptions) OR (food allergy) OR (psoriasis) OR (rash) OR (urticaria)) AND ((HIV 1 test) OR (HIV 2 test)) AND ((penicillins) OR (sulphonamides)) AND ((breast feeding) OR (pregnancy test positive)) AND ((allergy) OR (hypersensitivity)) AND ((birth control methods willing to continue practicing for at least 30 days after the end of the treatment period) OR NOT (nonhormonal birth control effective)))"}
{"candidate_id": "LLM02788", "doc_id": "NCT02526823_exc", "case_bucket": "or", "source_criterion": "Patients with severe complications or severe infection; Invasion of central nervous system; Patients with severe heart disease history, including ventricular tachycardia (VT), atrial fibrillation (AF), heart block, myocardial infarction (MI), congestive heart failure (CHF), coronary heart disease patients needed therapy; patients with severe allergic constitution, or those who are allergic to or intolerant of drug composition in chemotherapy regimens; with other malignant tumors in the past 5 years; patients received doxorubicin therapy, total cumulative dose of adriamycin was more than 300 mg/m2, total cumulative dose of epirubicin was more than 450 mg/m2; Patients participate in other clinical studies; Other patients who are not suitable for the study.", "candidate_expression": "((AF) AND (CHF) AND (Invasion) AND (MI) AND (Patients) AND (Patients participate in other clinical studies) AND (VT) AND (central nervous system) AND (chemotherapy regimens) AND (heart disease) AND (more than 300 mg/m2) AND (more than 450 mg/m2) AND (other) AND (past 5 years) AND (severe) AND (total cumulative dose) AND ((complications) OR (infection)) AND ((atrial fibrillation) OR (congestive heart failure) OR (coronary heart disease) OR (heart block) OR (myocardial infarction) OR (ventricular tachycardia)) AND ((allergic) OR (malignant tumors)) AND ((allergic) OR (intolerant)) AND ((adriamycin) OR (doxorubicin) OR (epirubicin)))"}
{"candidate_id": "LLM02789", "doc_id": "NCT03513874_inc", "case_bucket": "or", "source_criterion": "Type 1 diabetes according to ADA criterias <5 years. Age= 18 years and less than 70 years. Non-obese: defined as BMI less than 28 kg/m2 Positive for at least one of the anti-islet autoantibodies: GADA, IA2A, ZnT8A Fasting or postprandial plasma C-peptide more than 100 pmol/L Written informed consent from the patient or family representative.", "candidate_expression": "((Age = 18 years and less than 70 years) AND (BMI less than 28 kg/m2) AND (Type 1 diabetes ADA criterias <5 years) AND (Written informed consent from the patient or family representative.) AND (anti-islet autoantibodies at least one) AND NOT (obese) AND ((GADA) OR (IA2A) OR (ZnT8A)) AND ((Fasting plasma C-peptide) OR (postprandial plasma C-peptide)))"}
{"candidate_id": "LLM02790", "doc_id": "NCT02607163_inc", "case_bucket": "or", "source_criterion": "the patients undergoing ascending, arch and/or proximal descending aorta surgery with cardiopulmonary bypass 20 - 100 yrs old", "candidate_expression": "((20 - 100 yrs) AND (arch aorta surgery) AND (ascending aorta surgery) AND (cardiopulmonary bypass) AND (old) AND (proximal descending aorta surgery))"}
{"candidate_id": "LLM02791", "doc_id": "NCT02765035_exc", "case_bucket": "or", "source_criterion": "Person is under 18 years of age. Person who weighs more than 136kg. Person who weighs less than 50kg. Person who is pregnant. Person has a history of chronic skin breakdown on the residual limb. Person has conditions that would prevent participation and pose increased risk (e.g. unstable cardiovascular conditions that preclude physical activity such as walking). Person falls = once a week due to the reasons that could not be corrected by the new prosthesis (for ex. problems with vestibular system). Person is using under arm axillary crutches or walker. Person in an emergency, life threatening situation. Person is unwilling/unable to follow instructions. Person who is not available to follow the entire study protocol. Person who is participating in another study or intends to participate in another study during this study duration. Person who cannot personally provide their consent. Person who is not wearing prosthesis 8hours/day on average. Person who has a score on 10m walk test less than 3km/h (~0.8m/s) (based on 10m walk test conducted during recruiting). Person who walks on average less than 1km per day. Person who is not able to walk on level ground in a step over step manner.", "candidate_expression": "((10m walk test less than 3km/h 0.8m/s)) AND (Person is unwilling/unable to follow instruction) AND (Person who cannot personally provide their consent) AND (Person who is not available to follow the entire study protocol) AND (Person who is participating in another study or intends to participate in another study during this study duration.) AND (age under 18 years) AND (falls once a week) AND (pregnant) AND (skin breakdown chronic residual limb) AND (walks ess than 1km per day) AND (weighs less than 50kg) AND (weighs more than 136kg) AND NOT (prosthesis 8hours/day) AND ((under arm axillary crutches) OR (walker)) AND ((emergency situation) OR (life threatening situation)))"}
{"candidate_id": "LLM02792", "doc_id": "NCT03213834_inc", "case_bucket": "or", "source_criterion": "CPPE along with evidence of septated pleural effusion on pleural ultrasonography and/or chest CT scan empyema.", "candidate_expression": "((CPPE) AND (empyema) AND (evidence of) AND (septated pleural effusion) AND ((chest CT scan) OR (pleural ultrasonography)))"}
{"candidate_id": "LLM02793", "doc_id": "NCT00440245_exc", "case_bucket": "or", "source_criterion": "asthma and COPD", "candidate_expression": "((COPD) AND (asthma))"}
{"candidate_id": "LLM02794", "doc_id": "NCT02862912_inc", "case_bucket": "or", "source_criterion": "ASA I and II women 18-45 yrs old Singleton pregnancy Cervical cerclage 1st or 2nd trimester of pregnancy undergoing with spinal anesthesia Height 150 - 180 cm BMI = 40 kg/m2.", "candidate_expression": "((150 - 180 cm) AND (18-45 yrs) AND (1st trimester) AND (2nd trimester) AND (= 40 kg/m2) AND (ASA) AND (BMI) AND (Cervical cerclage) AND (Height) AND (I and II) AND (Singleton pregnancy) AND (old) AND (pregnancy) AND (spinal anesthesia) AND (women))"}
{"candidate_id": "LLM02795", "doc_id": "NCT01801072_inc", "case_bucket": "or", "source_criterion": "Adult (=18 years) Presence of intracranial aneurysm (with or without rupture) Treating surgeon has recommended surgical repair of the aneurysm", "candidate_expression": "((=18 years) AND (Adult) AND (Treating surgeon) AND (aneurysm) AND (intracranial aneurysm) AND (recommended) AND (surgical repair) AND (with rupture) AND (without rupture) AND (years))"}
{"candidate_id": "LLM02796", "doc_id": "NCT02164734_inc", "case_bucket": "other", "source_criterion": "Mild-to-moderate RDS; Postnatal age 2 to 48 hours; Gestational age 27 0/7 to 36 6/7 weeks; Treated with nasal CPAP modalities = 5 cm H2O and FiO2 between 0.30 and 0.60 for at least 2 hours to maintain SpO2 90-95%; Informed consent", "candidate_expression": "((2 to 48 hours) AND (27 0/7 to 36 6/7 weeks) AND (90-95%) AND (= 5 cm H2O) AND (FiO2) AND (Gestational age) AND (Informed consent) AND (Mild-to-moderate) AND (Postnatal age) AND (RDS) AND (SpO2) AND (between 0.30 and 0.60) AND (for at least 2 hours) AND (nasal CPAP))"}
{"candidate_id": "LLM02797", "doc_id": "NCT02735902_exc", "case_bucket": "or", "source_criterion": "The patient is participating in another study The patient is in an exclusion period determined by a previous study The patient or his/her representative refuses to sign the consent It is impossible to correctly inform the patient or his/her representative The patient is pregnant or breastfeeding The patient has a contraindication (or an incompatible drug association) for a treatment used in this study The patient had a coronary stent for less than 12 months The patient does not require treatment with aspirin or any other antiplatelet agent The patient has a history of aspirin allergy High bleeding risk; such as platelets <50,000 / mm3 during screening, Hb <8.5 g / dL, history of intracranial hemorrhage or subdural hematoma, major surgery, parenchymal organ biopsy or severe trauma within 30 days before inclusion, active gastrointestinal ulcer in the last 3 months; History of Stroke in the last 3 months; Moderate or severe liver affection associated with coagulopathy Active infectious endocarditis Active tumor treated at the time of inclusion associated with expected survival less than one year", "candidate_expression": "((Hb <8.5 g / dL) AND (It is impossible to correctly inform the patient or his/her representative) AND (Stroke History of in the last 3 months Moderate) AND (The patient is participating in another study) AND (The patient is pregnant or breastfeeding) AND (The patient or his/her representative refuses to sign the consent) AND (allergy history of) AND (antiplatelet agent other) AND (aspirin) AND (bleeding risk High) AND (coagulopathy Active) AND (contraindication) AND (coronary stent less than 12 months) AND (expected survival less than one year) AND (gastrointestinal ulcer active last 3 months) AND (infectious endocarditis Active Active) AND (intracranial hemorrhage) AND (liver affection associated with coagulopathy severe) AND (major surgery,) AND (parenchymal organ biopsy) AND (platelets <50,000 / mm3) AND (subdural hematoma) AND (trauma severe) AND (treated at the time of inclusion) AND (treatment require) AND (tumor Active))"}
{"candidate_id": "LLM02798", "doc_id": "NCT01728194_exc", "case_bucket": "or", "source_criterion": "Psychotic depression by DSM-IV, i.e., presence of delusions with a SCID-R score higher than 2; High suicide risk, i.e. intent or plan to attempt suicide in near future; Presence of any Axis I psychiatric disorder (other than unipolar major depression) or substance abuse; History of psychiatric disorders other than unipolar major depression or generalized anxiety disorder (bipolar disorder, hypomania, and dysthymia are exclusion criteria); Dementia: Diagnosis of dementia by DSM-IV; Mild Cognitive Impairment (MCI); Acute or severe medical illness, i.e., delirium, metastatic cancer, decompensated cardiac, liver or kidney failure, major surgery, stroke or myocardial infarction during the three months prior to entry; or use of drugs known to cause depression, e.g., reserpine, alpha-methyl-dopa, steroids, sympathomimetics withdrawal; Neurological brain disease and/or history of electroconvulsive therapy; History of any use of citalopram or escitalopram during the current episode or need for drugs that may interact with these agents, i.e. drug metabolized by the 2D6 P450 isoenzyme system; Current involvement in psychotherapy; Contraindications to MRI scanning including cardiac pacemaker, metallic objects and metallic implants contraindicating MRI, cardiac stent, claustrophobia; Inability to speak English; Corrected visual acuity < 20/70; Color blindness.", "candidate_expression": "((Contraindications) AND (Dementia DSM-IV) AND (Inability to speak English) AND (MCI) AND (MRI) AND (Mild Cognitive Impairment) AND (Psychotic depression DSM-IV) AND (SCID-R score higher than 2) AND (agents) AND (attempt suicide in near future) AND (delusions) AND (depression entry) AND (drugs) AND (episode current) AND (psychiatric disorder Axis I) AND (psychiatric disorders) AND (psychotherapy) AND (substance abuse) AND (suicide risk High) AND NOT (unipolar major depression) AND ((generalized anxiety disorder) OR (unipolar major depression)) AND ((bipolar disorder) OR (dysthymia) OR (hypomania)) AND ((Acute) OR (severe)) AND ((delirium) OR (major surgery) OR (metastatic cancer) OR (myocardial infarction) OR (stroke)) AND ((cardiac failure) OR (kidney failure) OR (liver failure)) AND ((drugs) OR (medical illness three months prior to entry)) AND ((alpha-methyl-dopa) OR (reserpine) OR (steroids) OR (sympathomimetics withdrawal)) AND ((brain disease Neurological) OR (electroconvulsive therapy)) AND ((citalopram) OR (escitalopram)) AND ((cardiac pacemaker) OR (cardiac stent) OR (claustrophobia) OR (metallic implants) OR (metallic objects)) AND ((intent) OR (plan to)) AND ((Color blindness) OR (visual acuity Corrected < 20/70;)))"}
{"candidate_id": "LLM02799", "doc_id": "NCT02557412_exc", "case_bucket": "or", "source_criterion": "Apnea-hypopnea index of less than 5 h-1 or greater than 30 h-1. Predominance of central apneas and hypopneas, defined as more than 25% of all respiratory events. Professional drivers, risk profession or respiratory failure (according to criteria of the clinical pathway for diagnosis and treatment of sleep-disordered breathing). Very excessive daytime sleepiness (Epworth Sleepiness Scale> 18). Morbid obesity (BMI> 40 kg / m2). Prior treatment with CPAP.", "candidate_expression": "((> 18) AND (> 40 kg / m2) AND (Apnea-hypopnea index) AND (BMI) AND (CPAP) AND (Epworth Sleepiness Scale) AND (Morbid obesity) AND (Predominance) AND (Prior) AND (Very excessive) AND (all respiratory events) AND (central apneas and hypopneas) AND (criteria of the clinical pathway for diagnosis and treatment of sleep-disordered breathing) AND (daytime sleepiness) AND (less than 5 h-1 or greater than 30 h-1) AND (more than 25%) AND ((Professional drivers) OR (respiratory failure) OR (risk profession)))"}
{"candidate_id": "LLM02800", "doc_id": "NCT03424733_inc", "case_bucket": "or", "source_criterion": "diagnosed any form of MS (relapsing remitting, primary progressive, secondary progressive), any EDSS (expanded stability status scale) score", "candidate_expression": "((MS) AND (any) AND (any form) AND (expanded stability status scale) AND (primary progressive) AND (relapsing remitting) AND (score EDSS) AND (secondary progressive))"}
```
