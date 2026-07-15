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
{"candidate_id": "LLM04901", "doc_id": "NCT02735902_exc", "case_bucket": "or", "source_criterion": "The patient is participating in another study The patient is in an exclusion period determined by a previous study The patient or his/her representative refuses to sign the consent It is impossible to correctly inform the patient or his/her representative The patient is pregnant or breastfeeding The patient has a contraindication (or an incompatible drug association) for a treatment used in this study The patient had a coronary stent for less than 12 months The patient does not require treatment with aspirin or any other antiplatelet agent The patient has a history of aspirin allergy High bleeding risk; such as platelets <50,000 / mm3 during screening, Hb <8.5 g / dL, history of intracranial hemorrhage or subdural hematoma, major surgery, parenchymal organ biopsy or severe trauma within 30 days before inclusion, active gastrointestinal ulcer in the last 3 months; History of Stroke in the last 3 months; Moderate or severe liver affection associated with coagulopathy Active infectious endocarditis Active tumor treated at the time of inclusion associated with expected survival less than one year", "candidate_expression": "((It is impossible to correctly inform the patient or his/her representative) AND (Stroke History of in the last 3 months) AND (The patient is participating in another study) AND (The patient is pregnant or breastfeeding) AND (The patient or his/her representative refuses to sign the consent) AND (allergy history of) AND (aspirin) AND (bleeding risk High) AND (coagulopathy Active) AND (contraindication) AND (coronary stent less than 12 months) AND (expected survival less than one year) AND (infectious endocarditis Active Active) AND (liver affection associated with coagulopathy) AND (treated at the time of inclusion) AND (treatment require) AND (tumor Active) AND ((Hb <8.5 g / dL) OR (gastrointestinal ulcer active last 3 months) OR (platelets <50,000 / mm3)) AND ((intracranial hemorrhage) OR (major surgery,) OR (parenchymal organ biopsy) OR (subdural hematoma) OR (trauma severe)) AND ((antiplatelet agent other) OR (aspirin)) AND ((Moderate) OR (severe)))"}
{"candidate_id": "LLM04902", "doc_id": "NCT02715518_exc", "case_bucket": "other", "source_criterion": "NA", "candidate_expression": "(EMPTY)"}
{"candidate_id": "LLM04903", "doc_id": "NCT02046395_inc", "case_bucket": "or", "source_criterion": "Type 2 Diabetes Hypertension Estimated glomerular filtration rate (eGFR) > 30 ml/min Use of Ace Inh and ARB for control of blood pressure who are willing to be placed on alternate drug(s) in the washout period for blood pressure control", "candidate_expression": "((Estimated glomerular filtration rate (eGFR) > 30 ml/min) AND (Hypertension) AND (Type 2 Diabetes) AND (control of blood pressure) AND (willing to be placed on alternate drug(s) in the washout period for blood pressure control) AND ((ARB) OR (Ace Inh)))"}
{"candidate_id": "LLM04904", "doc_id": "NCT02462590_inc", "case_bucket": "other", "source_criterion": "Adults = 18 years of age Admitted to any ICU and receiving invasive mechanical ventilation Anticipated ventilation of =72 hours at the time of screening, as per the ICU physician.", "candidate_expression": "((Adults) AND (ICU) AND (age = 18 years) AND (mechanical ventilation invasive) AND (ventilation Anticipated =72 hours))"}
{"candidate_id": "LLM04905", "doc_id": "NCT02825290_inc", "case_bucket": "other", "source_criterion": "20-40 years old women Spontaneously ovulating women Treated in our IVF unit for frozen-thawed embryo transfer At least one top quality embryo", "candidate_expression": "((20-40 years) AND (At least one) AND (Spontaneously ovulating) AND (frozen-thawed embryo transfer) AND (old) AND (our IVF unit) AND (top quality embryo) AND (women))"}
{"candidate_id": "LLM04906", "doc_id": "NCT02944929_inc", "case_bucket": "or", "source_criterion": "Males and females aged between 18 to 75 years. Adult patient under guardianship with consent obtained and the legal guardian's authorisation obtained. Single stroke having occurred more than 6 months before (previous TIA is accepted). Capable of understanding instructions and participating in the definition of a therapeutic goal (Boston Diagnostic Aphasia Examination (BDAE) < 3). Having previously undergone BTI. The last injection must have been performed at least 4 months prior to inclusion. Affiliation to the French social security regime or a similar regime. Patient (or the legal guardian if under guardian adult patient) has signed the informed consent form.", "candidate_expression": "((Adult patient under guardianship with consent obtained and the legal guardian's authorisation obtained) AND (BDAE) AND (BTI) AND (Boston Diagnostic Aphasia Examination < 3) AND (Capable of understanding instructions and participating in the definition of a therapeutic goal) AND (Males) AND (Patient (or the legal guardian if under guardian adult patient) has signed the informed consent form) AND (TIA) AND (aged between 18 to 75 years) AND (females) AND (injection at least 4 months prior to inclusion) AND (stroke Single more than 6 months))"}
{"candidate_id": "LLM04907", "doc_id": "NCT03325023_inc", "case_bucket": "or", "source_criterion": "Written consent for participation in the clinical trial Age 18 to 45 years Irregular menstruation (> 35 days) or secondary amenorrhea> 3 months", "candidate_expression": "((Age 18 to 45 years) AND (Irregular menstruation > 35 days) AND (Written consent for participation in the clinical trial) AND (secondary amenorrhea > 3 months))"}
{"candidate_id": "LLM04908", "doc_id": "NCT03430284_exc", "case_bucket": "or", "source_criterion": "type 1 diabetes,specific types of diabetes,gestational diabetes or pregestational diabetes; acute cardiovascular or cerebrovascular accidents within past 3 months; severe hepatic or renal dysfunction; malignant tumor; allergic history or contraindication for any drugs in trials; taking part in other clinical trials; obviously poor compliance.", "candidate_expression": "((accidents cardiovascular) AND (acute) AND (allergic) AND (any) AND (cerebrovascular accidents) AND (contraindication) AND (diabetes) AND (drugs in trials) AND (gestational diabetes) AND (hepatic dysfunction) AND (history) AND (malignant tumor) AND (obviously) AND (poor compliance) AND (pregestational diabetes) AND (renal dysfunction) AND (severe) AND (specific types) AND (taking part in other clinical trials) AND (type 1 diabetes) AND (within past 3 months))"}
{"candidate_id": "LLM04909", "doc_id": "NCT01816997_exc", "case_bucket": "or", "source_criterion": "A1C >7.0% 2hr glucose during OGTT >200 mg/dL Total cholesterol >280 mg/dL Previous diabetic history, coronary artery disease Allergy to rosuvastatin or parvastatin Baseline ALT more than 3 times UNL Serum Cr > 2.0 mg/dL Pregnancy, breast feeding or plan to be pregnant woman.", "candidate_expression": "((2hr glucose during OGTT) AND (> 2.0 mg/dL) AND (>200 mg/dL) AND (>280 mg/dL) AND (>7.0%) AND (A1C) AND (ALT) AND (Allergy) AND (Baseline) AND (Pregnancy) AND (Previous) AND (Serum Cr) AND (Total cholesterol) AND (breast feeding) AND (coronary artery disease) AND (diabetic) AND (history) AND (more than 3 times UNL) AND (parvastatin) AND (plan to be) AND (pregnant) AND (rosuvastatin) AND (woman))"}
{"candidate_id": "LLM04910", "doc_id": "NCT02260700_exc", "case_bucket": "or", "source_criterion": "Participant has a clinically significant abnormal physical examination, vital signs or 12 lead ECG (including QTc greater than (>) 450msec, Left Bundle Branch Block, permanent pacemaker or implantable cardioverter defibrillator) at Screening or admission Participant has a history of or current liver or renal insufficiency; significant cardiac, vascular, pulmonary, gastrointestinal, endocrine, neurologic, hematologic, rheumatologic, psychiatric, or metabolic disturbances Use of any prescription or over-the-counter medication, herbal medication, vitamins, or mineral supplements within 14 days prior to study drug administration (not including paracetamol). Medication for chronic use in age related disease will be allowed after approval by both the investigator and to the sponsor. No change in dose or regimen will be permitted during the study that is, from the Screening visit until the follow-up visit Participant has a history of spontaneous, prolonged or severe bleeding of unclear origin Participant has a history of epilepsy or fits or unexplained black-outs other than vasovagal collapse", "candidate_expression": "((Medication chronic use) AND (age related disease) AND (approval by both the investigator and to the sponsor) AND (bleeding history unclear origin) AND (significant) AND NOT (paracetamol) AND NOT (vasovagal collapse) AND ((Screening) OR (admission)) AND ((liver insufficiency) OR (renal insufficiency)) AND ((cardiac disturbances) OR (endocrine disturbances) OR (gastrointestinal disturbances) OR (hematologic disturbances) OR (metabolic disturbances) OR (neurologic disturbances) OR (psychiatric disturbances) OR (pulmonary disturbances) OR (rheumatologic disturbances) OR (vascular disturbances)) AND ((any prescription) OR (herbal medication) OR (mineral supplements) OR (over-the-counter medication) OR (vitamins)) AND ((prolonged) OR (severe) OR (spontaneous)) AND ((abnormal 12 lead ECG) OR (abnormal physical examination) OR (abnormal vital signs)) AND ((black-outs unexplained) OR (epilepsy) OR (fits)) AND ((Left Bundle Branch Block) OR (QTc greater than (>) 450msec) OR (implantable cardioverter defibrillator) OR (permanent pacemaker)))"}
{"candidate_id": "LLM04911", "doc_id": "NCT02933671_exc", "case_bucket": "or", "source_criterion": "ASA 4 or 5 revision hip arthroplasty diagnosis of chronic pain daily chronic opioid use (over 3 months of continuous opioid use) inability to communicate pain scores or need for analgesia acute hip fracture Infection at the site of block placement Age under 18 years old or greater than 75 years old Pregnant women Intolerance/allergy to local anesthetics Weight <50 kg Suspected, or known addiction to or abuse of illicit drug(s), prescription medicine(s), or alcohol within the past 2 years. Uncontrolled anxiety, schizophrenia, or other psychiatric disorder that, in the opinion of the investigator, may interfere with study assessments or compliance Current or historical evidence of any clinically significant disease or condition that, in the opinion of the investigator, may increase the risk of surgery or complicate the subject's postoperative course.", "candidate_expression": "((ASA 4 or 5) AND (Age under 18 years old or greater than 75 years old) AND (Infection site of block placement) AND (Intolerance) AND (Pregnant women) AND (Weight <50 kg) AND (abuse illicit drug prescription medicine alcohol) AND (addiction) AND (allergy) AND (anxiety) AND (chronic pain) AND (hip fracture acute) AND (inability to communicate pain scores or need for analgesia) AND (local anesthetics) AND (opioid chronic over 3 months) AND (psychiatric disorder) AND (revision hip arthroplasty) AND (schizophrenia))"}
{"candidate_id": "LLM04912", "doc_id": "NCT00931983_exc", "case_bucket": "other", "source_criterion": "Other neuromuscular disease Contraindication to weight bearing on lower extremities Pressure sores where harness would be applied Uncontrollable hypotension when upright Lower limb contractures impeding range of motion necessary for ambulation Prior enrolment in a BWATT program Unable to commit to intervention for duration of protocol", "candidate_expression": "((Contraindication) AND (Lower limb contractures) AND (Pressure sores) AND (Unable to commit to intervention for duration of protocol) AND (Uncontrollable) AND (harness) AND (hypotension) AND (impeding) AND (neuromuscular disease) AND (range of motion necessary for ambulation) AND (weight bearing on lower extremities) AND (when upright))"}
{"candidate_id": "LLM04913", "doc_id": "NCT02344888_exc", "case_bucket": "or", "source_criterion": "Age < 20 or > 35 years. Body mass index (BMI) < 18.5 kg/m2 or > 25 kg/m2. Presence of any infertility factor other than anovulatory PCOS. Previous history of ovarian surgery or surgical removal of one ovary. Previous exposure to cytotoxic drugs or pelvic irradiation. Oral hypoglycemic or hormonal therapy either currently or in the preceding 3 months. Metabolic or hormonal abnormalities", "candidate_expression": "((Age < 20 or > 35 years) AND (BMI) AND (Body mass index < 18.5 kg/m2 or > 25 kg/m2) AND (Metabolic abnormalities) AND (cytotoxic drugs) AND (exposure) AND (hormonal abnormalities) AND (hormonal therapy) AND (hypoglycemic therapy) AND (infertility factor) AND (ovarian surgery) AND (pelvic irradiation) AND (surgical removal ovary) AND NOT (anovulatory PCOS))"}
{"candidate_id": "LLM04914", "doc_id": "NCT03354572_exc", "case_bucket": "or", "source_criterion": "Pregnancy or lactating Allergy to NAC History of chronic pain Use of opioids or neuropathic analgesics Use of NAC prior to trial (< 1 month of planned surgery) Alcoholism Diabetes Mellitus (insulin therapy) Asthma or Chronic Obstructive pulmonary Disease Known renal function disorders (MDRD <ô0) Known liver failure (bilirubin >1.Sx upper limit of normal) No written lC by patient", "candidate_expression": "((Alcoholism) AND (Allergy) AND (Diabetes Mellitus) AND (MDRD <ô0) AND (NAC) AND (NAC prior to trial) AND (No written lC by patient) AND (bilirubin >1.Sx upper limit of normal) AND (chronic pain History) AND (insulin) AND (liver failure) AND (renal function disorders) AND (surgery < 1 month planned) AND ((Pregnancy) OR (lactating)) AND ((Asthma) OR (Chronic Obstructive pulmonary Disease)) AND ((neuropathic analgesics) OR (opioids)))"}
{"candidate_id": "LLM04915", "doc_id": "NCT02612181_inc", "case_bucket": "other", "source_criterion": "Septic shock patients despite early goal directed therapy Agree to participate this study", "candidate_expression": "((Agree to participate this study) AND (Septic shock) AND (early goal directed therapy))"}
{"candidate_id": "LLM04916", "doc_id": "NCT02621541_inc", "case_bucket": "or", "source_criterion": "suspicion of nonfunctional P-NET on primary CT (i.e hypervascularity) or MRI signed informed consent", "candidate_expression": "((hypervascularity) AND (nonfunctional P-NET suspicion) AND (signed informed consent) AND ((MRI) OR (primary CT)))"}
{"candidate_id": "LLM04917", "doc_id": "NCT03123562_inc", "case_bucket": "other", "source_criterion": "Cerebral palsy of any types caused by Neonatal Jaundice", "candidate_expression": "((Cerebral palsy) AND (Neonatal Jaundice))"}
{"candidate_id": "LLM04918", "doc_id": "NCT02334631_inc", "case_bucket": "other", "source_criterion": "Patients undergoing small bowel video capsule endoscopy", "candidate_expression": "(small bowel video capsule endoscopy)"}
{"candidate_id": "LLM04919", "doc_id": "NCT02796378_inc", "case_bucket": "other", "source_criterion": "Elevated blood-cholesterol", "candidate_expression": "(blood-cholesterol Elevated)"}
{"candidate_id": "LLM04920", "doc_id": "NCT02509091_inc", "case_bucket": "other", "source_criterion": "Age=18 years and =80 years; Patients with non-cystic fibrosis bronchiectasis diagnosed by high-resolution CT; Are sensitive to amikacin; Acute exacerbation of bronchiectasis; Capable of the completion of bronchoscopy, alveolar lavage, pulmonary function testing etc; Willing to join in and sign the informed consent form.", "candidate_expression": "((=18 years and =80 years) AND (Acute exacerbation of bronchiectasis) AND (Age) AND (Capable of the completion of bronchoscopy, alveolar lavage, pulmonary function testing etc) AND (Willing to join in and sign the informed consent form) AND (amikacin) AND (high-resolution CT) AND (non-cystic fibrosis bronchiectasis) AND (sensitive))"}
{"candidate_id": "LLM04921", "doc_id": "NCT03513874_exc", "case_bucket": "or", "source_criterion": "History of any malignancy or other severe diseases Female patients who are pregnant or breastfeeding before or during the three-year follow-up Poor compliance or refusal to participate.", "candidate_expression": "((Female patients who are pregnant or breastfeeding before or during the three-year follow-up) AND (Poor compliance) AND (malignancy) AND (refusal to participate) AND (severe diseases))"}
{"candidate_id": "LLM04922", "doc_id": "NCT02637076_exc", "case_bucket": "or", "source_criterion": "use of any sedative hypnotics, tranquilizers, anticonvulsants, antihistamines (except non-sedating), benzodiazepines, clonidine or any medication known to affect dopamine at start of baseline period significant unstable or uncontrolled medical/psychiatric disease significant history of head trauma/surgery or seizure disorder radiation exposure exceeding 20mSv in last 12 months pregnancy substance abuse/dependence (including alcohol) have sleep apnea, or are shift workers on a sodium-restricted diet has ever taken Xyrem / sodium oxybate / GHB at any time claustrophobia metal implants / objects in the body that may interfere with MRI succinic semialdehyde dehydrogenase deficiency", "candidate_expression": "((GHB) AND (MRI may interfere with) AND (Xyrem) AND (alcohol) AND (anticonvulsants) AND (antihistamines non-sedating) AND (benzodiazepines) AND (claustrophobia) AND (clonidine) AND (head surgery) AND (head trauma) AND (medical disease uncontrolled) AND (medication known to affect dopamine unstable) AND (metal implants) AND (metal objects) AND (pregnancy) AND (psychiatric disease) AND (radiation exposure exceeding 20mSv in last 12 months) AND (sedative hypnotics) AND (seizure disorder) AND (shift workers) AND (sleep apnea) AND (sodium oxybate) AND (sodium-restricted diet) AND (substance abuse) AND (substance dependence) AND (succinic semialdehyde dehydrogenase deficiency) AND (tranquilizers))"}
{"candidate_id": "LLM04923", "doc_id": "NCT03247738_inc", "case_bucket": "other", "source_criterion": "Patients with STEMI undergoing primary PPCI Age > 18 years old", "candidate_expression": "((> 18 years old) AND (Age) AND (STEMI) AND (primary PPCI))"}
{"candidate_id": "LLM04924", "doc_id": "NCT03058835_exc", "case_bucket": "or", "source_criterion": "Active alcohol or drug use or dependence which may interfere with adherence to study requirements HIV-infected at screening or enrollment Estimated CrCl < 60 mL/min Past participation in an HIV vaccine study Positive Hepatitis B surface antigen test Underlying medical condition with survival unlikely during follow-up period Any condition that in the opinion of study staff would make participation in the study unsafe or interfere with achieving study objectives Pregnant or breast feeding Actively trying to achieve pregnancy", "candidate_expression": "((Active alcohol or drug use or dependence which may interfere with adherence to study requirements) AND (Actively trying to achieve pregnanc) AND (Estimated CrCl < 60 mL/min) AND (HIV-infected) AND (Hepatitis B surface antigen test Positive) AND (condition) AND (medical condition) AND (survival unlikely) AND ((Pregnant) OR (breast feeding)) AND ((interfere with achieving study objectives) OR (make participation in the study unsafe)) AND ((at enrollment) OR (at screening)))"}
{"candidate_id": "LLM04925", "doc_id": "NCT01912651_exc", "case_bucket": "or", "source_criterion": "current or recent (within one week of surgery) systemic antibiotic use, intolerance to both clindamycin and cephalexin, discovery of a persistent cutaneous malignancy at the site of the defect following the reconstructive procedure and previous reconstruction at the site of the skin/soft-tissue defect.", "candidate_expression": "((antibiotic current recent within one week of surgery) AND (cephalexin) AND (clindamycin) AND (intolerance) AND (persistent cutaneous malignancy site of the defect following the reconstructive procedure) AND (reconstructive procedure the reconstructive procedure))"}
```
