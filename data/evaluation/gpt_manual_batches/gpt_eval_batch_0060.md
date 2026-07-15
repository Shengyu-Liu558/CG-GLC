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
{"candidate_id": "LLM01476", "doc_id": "NCT03149887_inc", "case_bucket": "other", "source_criterion": "Adult patients up to age 75 years, undergoing elective, ambulatory, arthroscopic rotator cuff repair.", "candidate_expression": "((Adult) AND (age) AND (ambulatory) AND (arthroscopic rotator cuff repair) AND (elective) AND (up to 75 years))"}
{"candidate_id": "LLM01477", "doc_id": "NCT01846507_inc", "case_bucket": "or", "source_criterion": "1. Menstruating females 10-19 years of age 2. Non-smoker 3. Physician and patient have agreed to initiate Lysteda 4. Diagnosis of HMB based on the medical judgment of the principal or site investigator 5. Subjects must report menstrual periods occurring within 21-60 days from the start of one period to the start of the next menstrual period 6. Negative pregnancy test 7. Informed consent obtained and signed 8. Informed assent obtained and signed 9. Understanding of study procedures 10. Ability to comply with study procedures for the entire length of the study 11. Subjects should be either sexually inactive (abstinent) or agree to use a barrier method with spermicide in the event of sexual activity throughout the study period", "candidate_expression": "((10-19 years) AND (Ability to comply with study procedures for the entire length of the study) AND (HMB) AND (Informed assent obtained and signed) AND (Informed consent obtained and signed) AND (Lysteda) AND (Menstruating) AND (Negative) AND (Non-smoker) AND (Understanding of study procedures) AND (age) AND (agree to use) AND (barrier method with spermicide) AND (based on the medical judgment of the principal or site investigator) AND (females) AND (menstrual periods) AND (pregnancy test) AND (sexually abstinent) AND (sexually inactive) AND (the start of one period) AND (within 21-60 days from the start of one period))"}
{"candidate_id": "LLM01478", "doc_id": "NCT02618057_exc", "case_bucket": "or", "source_criterion": "Immunosuppresant host Chronic cardiovascular/pulmonary disease Hospital acquired infection", "candidate_expression": "((Chronic) AND (Hospital acquired infection) AND (Immunosuppresant host) AND (cardiovascular disease) AND (pulmonary disease))"}
{"candidate_id": "LLM01479", "doc_id": "NCT02344888_inc", "case_bucket": "other", "source_criterion": "Infertile lean women with PCOS as defined by the Rotterdam criteria. CC resistance (defined as failure of ovulation after receiving 150 mg/day of CC for 5 consecutive days per cycle, for at least 3 consecutive cycles).", "candidate_expression": "((CC) AND (Infertile Rotterdam criteria) AND (PCOS) AND (resistance) AND (women))"}
{"candidate_id": "LLM01480", "doc_id": "NCT02739295_exc", "case_bucket": "or", "source_criterion": "Toxic epidermal necrolysis with SCORTEN 6 or 7 at admission Hypercoagulable state Cardiac or peripheral arterial disease Active malignancy Myelodysplastic syndrome or hematological malignancy Fructose intolerance Pregnancy Patient refusal", "candidate_expression": "((6 or 7) AND (Active) AND (Fructose) AND (Fructose intolerance) AND (Hypercoagulable state) AND (Myelodysplastic syndrome) AND (Patient refusal) AND (Pregnancy) AND (SCORTEN) AND (Toxic epidermal necrolysis) AND (admission) AND (at admission) AND (disease Cardiac) AND (hematological malignancy) AND (malignancy) AND (peripheral arterial disease))"}
{"candidate_id": "LLM01481", "doc_id": "NCT02528136_inc", "case_bucket": "other", "source_criterion": "Healthy pregnant women age 18 to 50 Singleton pregnancy at gestational age 36 weeks or more Able to read and understand Norwegian.", "candidate_expression": "((18 to 50) AND (36 weeks or more) AND (Able to read and understand Norwegian) AND (Healthy) AND (Singleton pregnancy) AND (age) AND (gestational age) AND (pregnant) AND (women))"}
{"candidate_id": "LLM01482", "doc_id": "NCT02868437_inc", "case_bucket": "other", "source_criterion": "Subject has curettage for retained product after second trimester abortion", "candidate_expression": "((abortion) AND (curettage) AND (retained product) AND (second trimester))"}
{"candidate_id": "LLM01483", "doc_id": "NCT02862314_inc", "case_bucket": "other", "source_criterion": "aged 18 or older, have undergone oro-tracheal intubation for a coma (Glasgow Coma Score below or equal to 8), with mechanical ventilation initiated in the first 48 hours following hospital admission", "candidate_expression": "((18 or older) AND (Glasgow Coma Score) AND (aged) AND (below or equal to 8)) AND (coma) AND (first 48 hours following hospital admission) AND (hospital admission) AND (mechanical ventilation) AND (oro-tracheal intubation))"}
{"candidate_id": "LLM01484", "doc_id": "NCT02973035_exc", "case_bucket": "or", "source_criterion": "Unwillingness or inability to comply with the procedures described in this protocol Planned cardiac surgery or planned major non-cardiac surgery within the study period. Stroke or coronary revascularization in the past 6 months. Clinically significant pulmonary disease. Untreated hyperthyroidism, or hypothyroidism. A diagnosis of cancer (other than superficial squamous or basal cell skin cancer) in the past 3 years or current treatment for the active cancer. Female of child-bearing potential who do not use adequate contraception and women who are pregnant or breast-feeding Any clinically significant abnormality identified at the screening visit, physical examination, laboratory tests, or electrocardiogram which, in the judgment of the Investigator, would preclude safe completion of the study. LV ejection fraction < 50%. Significant renal disease manifested by serum creatinine > 2.5 mg/dL Hepatic disease or biliary tract obstruction, or significant hepatic enzyme elevation (ALT or AST > 3 times upper limit of normal). History of intolerance to ARB or amlodipine. Hypertrophic or restrictive cardiomyopathy. Moderate or severe valvular disease. Constrictive pericarditis Atrial fibrillation with a heart rate > 120/min. Sitting systolic BP < 100 mmHg", "candidate_expression": "((< 100 mmHg) AND (< 50%) AND (> 120/min) AND (> 2.5 mg/dL) AND (> 3 times upper limit of normal) AND (Any clinically significant abnormality identified at the screening visit, physical examination, laboratory tests, or electrocardiogram which, in the judgment of the Investigator, would preclude safe completion of the study) AND (Atrial fibrillation) AND (Clinically significant) AND (Constrictive pericarditis) AND (Female of child-bearing potential who do not use adequate contraception and women who are pregnant or breast-feeding) AND (Hypertrophic cardiomyopathy) AND (LV ejection fraction) AND (Planned) AND (Significant) AND (Sitting) AND (Untreated) AND (Unwillingness or inability to comply with the procedures described in this protocol) AND (active) AND (cancer) AND (cardiac) AND (heart rate) AND (in the past 3 years) AND (in the past 6 months) AND (intolerance) AND (major) AND (non) AND (other than) AND (planned) AND (pulmonary disease) AND (renal disease) AND (restrictive cardiomyopathy) AND (serum creatinine) AND (significant) AND (study period) AND (systolic BP) AND (treatment) AND (valvular disease) AND (within the study period) AND ((Stroke revascularization) OR (coronary revascularization)) AND ((hyperthyroidism) OR (hypothyroidism)) AND ((basal cell skin cancer) OR (superficial squamous skin cancer)) AND ((Hepatic disease) OR (biliary tract obstruction) OR (hepatic enzyme elevation)) AND ((ALT) OR (AST)) AND ((ARB) OR (amlodipine)) AND ((Moderate) OR (severe)) AND ((cardiac surgery) OR (surgery)))"}
{"candidate_id": "LLM01485", "doc_id": "NCT02743598_exc", "case_bucket": "or", "source_criterion": "Personal or family history of pancreatitis Medullary thyroid carcinoma (MTC) or Multiple Endocrine Neoplasia Syndrome Type 2 (MEN 2) Gastroparesis Allergy to liraglutide or any of the active ingredients in liraglutide or other GLP-1 analogue Weight loss drugs other than metformin Type 1 diabetes mellitus or diabetic ketoacidosis Known major cognitive deficit dementia, history of head trauma with loss of consciousness >30 min, history of stroke, current central nervous system (CNS) disorder such as seizures or opportunistic CNS infection Renal insufficiency defined as creatinine clearance < 60 mL/min Active opportunistic infections Pregnancy or breastfeeding Unstable cardiovascular disease with hospitalization within 1 year for acute coronary syndrome Decompensated heart failure Substance abuse Active alcohol or opioid substitution therapy Serious or unstable medical or psychological conditions that would compromise the subject's safety for successful participation", "candidate_expression": "((Allergy) AND (Decompensated heart failure) AND (Gastroparesis) AND (MEN 2) AND (MTC) AND (Pregnancy or breastfeeding) AND (Renal insufficiency) AND (Substance abuse) AND (Weight loss) AND (acute coronary syndrome within 1 year) AND (cognitive deficit) AND (creatinine clearance < 60 mL/min) AND (hospitalization) AND (loss of consciousness >30 min) AND (opportunistic infections Active) AND (pancreatitis) AND NOT (metformin) AND ((Type 1 diabetes mellitus) OR (diabetic ketoacidosis)) AND ((Medullary thyroid carcinoma) OR (Multiple Endocrine Neoplasia Syndrome Type 2)) AND ((central nervous system disorder) OR (dementia) OR (head trauma) OR (stroke)) AND ((opportunistic CNS infection) OR (seizures)) AND ((alcohol) OR (opioid substitution therapy)) AND ((GLP-1 analogue) OR (liraglutide)))"}
{"candidate_id": "LLM01486", "doc_id": "NCT03169127_inc", "case_bucket": "other", "source_criterion": "Need of lower third molar surgeries", "candidate_expression": "(surgeries lower third molar)"}
{"candidate_id": "LLM01487", "doc_id": "NCT03169127_exc", "case_bucket": "or", "source_criterion": "Presence of systemic diseases; Presence of local inflammation and/or infection; Any history of allergic reaction to local anesthetics, gastrointestinal bleeding or ulceration; Cardiovascular, kidney or hepatic diseases; Patients who are making use of antidepressants, diuretics or anticoagulants; Asthma and allergy to aspirin, ibuprofen or any other nonsteroidal antiinflammatory drug; Regular use of any nonsteroidal antiinflammatory drug, Pregnancy or breast feeding.", "candidate_expression": "((Asthma) AND (Cardiovascular diseases) AND (Pregnancy) AND (allergic reaction) AND (allergy) AND (anticoagulants) AND (antidepressants) AND (aspirin) AND (breast feeding) AND (diuretics) AND (gastrointestinal bleeding) AND (gastrointestinal ulceration) AND (hepatic diseases) AND (ibuprofen) AND (kidney diseases) AND (local anesthetics) AND (local infection) AND (local inflammation) AND (nonsteroidal antiinflammatory drug Regular use) AND (nonsteroidal antiinflammatory drug any other) AND (systemic diseases))"}
{"candidate_id": "LLM01488", "doc_id": "NCT03480607_exc", "case_bucket": "or", "source_criterion": "known allergy to any of drugs used coagulopathy any wound or infection related to puncture site major illness failure to gain consent of parents.", "candidate_expression": "((allergy) AND (coagulopathy) AND (drugs used) AND (failure to gain consent of parents) AND (illness major) AND NOT (consent of parents) AND ((infection) OR (wound)))"}
{"candidate_id": "LLM01489", "doc_id": "NCT01993836_exc", "case_bucket": "or", "source_criterion": "Inmate of a correctional facility (i.e. prisoners). Pregnancy Documented or suspected family or personal history of malignant hyperthermia. Patient unable to receive either propofol or isoflurane due to allergy or other specific contraindication.", "candidate_expression": "((Inmate of a correctional facility) AND (Pregnancy) AND (allergy) AND (malignant hyperthermia) AND (prisoners) AND (unable to receive) AND ((history family) OR (personal history)) AND ((isoflurane) OR (propofol)))"}
{"candidate_id": "LLM01490", "doc_id": "NCT02818816_exc", "case_bucket": "or", "source_criterion": "Patients having had an ophthalmic surgical procedure within 6 months of the beginning of the study. Patients with a diagnosis of glaucoma Any abnormality of the cornea which may prevent reliable applanation tonometry Known allergy/ hypersensitivity reaction to Brimonidine Contra-indication to Brimonidine including patients on monoamine oxidase inhibitors (MOA) Patients unwilling or unable to provide informed consent Patients with anticipated difficult airway management (as this may require medications and/or airway manipulations resulting in increased IOP)", "candidate_expression": "((Brimonidine) AND (Contra-indication) AND (MOA) AND (Patients unwilling or unable to provide informed consen) AND (abnormality cornea) AND (allergy) AND (difficult airway management) AND (glaucoma) AND (hypersensitivity) AND (monoamine oxidase inhibitors) AND (ophthalmic surgical procedure within 6 months of the beginning of the study))"}
{"candidate_id": "LLM01491", "doc_id": "NCT02894645_exc", "case_bucket": "or", "source_criterion": "Age less than one year or age greater than/equals to 18 years Previous treatment with cytotoxic agents or high-dose steroids Mixed phenotype acute leukemia (MPAL) ALL as secondary malignancy Abnormal renal or liver function Doubtful compliance or unable to afford full course of therapy", "candidate_expression": "((ALL) AND (MPAL) AND (Mixed phenotype acute leukemia) AND (Previous) AND (greater than/equals to 18 years) AND (less than one year) AND (malignancy) AND (secondary) AND (treatment) AND ((Age) OR (age)) AND ((Abnormal liver function) OR (Abnormal renal function)) AND ((Doubtful compliance) OR (unable to afford full course of therapy)) AND ((cytotoxic agents) OR (high-dose steroids)))"}
{"candidate_id": "LLM01492", "doc_id": "NCT02550028_inc", "case_bucket": "or", "source_criterion": "Male or female term baby with gestational >37 weeks and postnatal age < or= 28 days Birthweight >2500g Written informed consent of parent or guardian", "candidate_expression": "((Birthweight >2500g) AND (Written informed consent of parent or guardian) AND (baby) AND (gestational >37 weeks) AND (postnatal age < or= 28 days) AND (term) AND ((Male) OR (female)))"}
{"candidate_id": "LLM01493", "doc_id": "NCT00862446_inc", "case_bucket": "other", "source_criterion": "Infants in the newborn intensive care unit TPN cholestasis of at least 2.5 mg/dl Anticipated TPN treatment for at least one month signed informed consent", "candidate_expression": "((Infants) AND (TPN cholestasis at least 2.5 mg/dl) AND (TPN treatment for at least one month) AND (newborn intensive care unit) AND (signed informed consent))"}
{"candidate_id": "LLM01494", "doc_id": "NCT01630954_inc", "case_bucket": "other", "source_criterion": "Ultrasound confirmed complete mole", "candidate_expression": "((Ultrasound) AND (complete mole))"}
{"candidate_id": "LLM01495", "doc_id": "NCT02652637_exc", "case_bucket": "or", "source_criterion": "Emergency surgery needed Bowel obstruction Colonoscopy scheduled to be undertaken peroperatively Other reason indicating mechanical preparation or contradicting it Allergy to used drugs (PEG, neomycin, metronidazole)", "candidate_expression": "((Allergy) AND (Bowel obstruction) AND (Colonoscopy) AND (Emergency surgery needed) AND (contradicting) AND (drugs) AND (mechanical preparation) AND (undertaken scheduled peroperatively) AND ((PEG) OR (metronidazole) OR (neomycin)))"}
{"candidate_id": "LLM01496", "doc_id": "NCT02687724_inc", "case_bucket": "or", "source_criterion": "Patients = 18 years of age Subjects must be able and willing to give written informed consent and to comply with the requirements of this study protocol Established diagnosis of UC and moderate-to-severe disease activity, defined as a Mayo score of 6-12, with an endoscopic subscore =2. Patients had an inadequate response to, or had failed to tolerate, 1 or more of the following conventional therapies: oral 5-aminosalicylates, oral corticosteroids, azathioprine (AZA), and/or 6-mercaptopurine (6MP); or corticosteroid dependent (ie, an inability to taper corticosteroids without recurrence of UC symptoms). Patients concurrently treated with oral 5-aminosalicylates or corticosteroids were to receive a stable dose for at least 2 weeks before baseline, and patients receiving AZA and/or 6MP were to receive a stable dose for at least 4 weeks before baseline. Patients were required to maintain stable doses of their concomitant UC medications during the study. Female subjects of child bearing potential must be willing to ensure that they or their partner use effective contraception during the study and for 6 months thereafter OR Surgical sterilized female patients with documentation of prior hysterectomy, tubal ligation or complete bilateral oophorectomy OR Postmenopausal women with postmenopausal defined as permanent cessation >1 year of previously occurring menses. Female subjects' serum pregnancy test performed at the screening visit and urine pregnancy test performed at the baseline visit must be negative. Subjects have following investigations within 1 month prior to enrolment. Routine bloods including U&E, FBC, LFTs, inflammatory markers (CRP) and albumin will be measured. Medical history, concomitant medications Intradermal reaction to Tuberculin (PPD skin test) or Mycobacterium tuberculosis antigenspecific interferon-gamma release assay (IGRA) TB screening: chest X-Ray unless performed in the last 6 months Stool examination for enteric pathogens including Clostridium difficile Inclusion/exclusion criteria Informed consent Mayo score (including sigmoidoscopy unless performed in previous 3 months) Patient's weight and height and abdominal circumference", "candidate_expression": "((Female subjects of child bearing potential must be willing to ensure that they or their partner use effective contraception during the study and for 6 months thereafter OR) AND (Female subjects' serum pregnancy test performed at the screening visit and urine pregnancy test performed at the baseline visit must be negative.) AND (Mayo score) AND (Mayo score 6-12) AND (Postmenopausal women with postmenopausal defined as permanent cessation >1 year of previously occurring menses.) AND (Routine bloods within 1 month prior to enrolment) AND (Stool examination for enteric pathogens including Clostridium difficile) AND (Surgical sterilized female patients with documentation of prior hysterectomy, tubal ligation or complete bilateral oophorectomy OR) AND (TB screening) AND (UC moderate-to-severe) AND (abdominal circumference) AND (age = 18 years) AND (chest X-Ray) AND (corticosteroid) AND (dependent) AND (endoscopic subscore =2) AND (height) AND (sigmoidoscopy) AND (treated) AND (weight) AND ((failed to tolerate) OR (inadequate response)) AND ((6-mercaptopurine (6MP)) OR (azathioprine (AZA)) OR (oral 5-aminosalicylates) OR (oral corticosteroids)) AND ((corticosteroids) OR (oral 5-aminosalicylates)) AND ((6MP) OR (AZA)) AND ((FBC) OR (LFTs) OR (U&E) OR (albumin) OR (inflammatory markers (CRP))) AND ((Intradermal reaction to Tuberculin (PPD skin test)) OR (Mycobacterium tuberculosis antigenspecific interferon-gamma release assay (IGRA))))"}
{"candidate_id": "LLM01497", "doc_id": "NCT03011476_exc", "case_bucket": "other", "source_criterion": "Significant motor complication affecting daily activities Drugs related to acetylcholine metabolism", "candidate_expression": "((Drugs related to acetylcholine metabolis) AND (acetylcholine) AND (motor complication Significant))"}
{"candidate_id": "LLM01498", "doc_id": "NCT02175186_inc", "case_bucket": "or", "source_criterion": "Age between 20 and 80 years Patients undergoing percutaneous coronary intervention and need to take dual antiplatelet therapy continuously at least 12weeks Modified Lanza Score grade 0-1 measured by upper gastrointestinal endoscopy mild gastrointestinal symptom Creatinen in blood = 3mg/dl BUN = 50mg/dl Birilubin = 3mg/dl AST and ALT = 80U/L", "candidate_expression": "((0-1) AND (= 3mg/dl) AND (= 50mg/dl) AND (= 80U/L) AND (ALT) AND (AST) AND (Age) AND (BUN) AND (Birilubin) AND (Creatinen) AND (Modified Lanza Score grade) AND (at least 12weeks) AND (between 20 and 80 years) AND (continuously) AND (dual antiplatelet therapy) AND (gastrointestinal symptom) AND (mild) AND (percutaneous coronary intervention) AND (upper gastrointestinal endoscopy))"}
{"candidate_id": "LLM01499", "doc_id": "NCT03304496_inc", "case_bucket": "or", "source_criterion": "Men and women older than 18 years, scheduled consecutively to perform a coronary procedure in the department of hemodynamics of the National Institute of Cardiology \"Ignacio Chavez\". Patients may have any of the following indications for cardiac catheterization: Thoracic pain under study. Stable chronic coronary disease. Acute myocardial infarction with ST segment elevation, not perfused (without timely reperfusion therapy) with less than 4 weeks of evolution. Acute myocardial infarction with ST-segment elevation, successful thrombolytic therapy, which will undergo drug-invasive therapy. Acute myocardial infarction without ST segment elevation. Unstable angina. Any acute coronary syndrome, to intervene non-infarct-related artery. Disease of any heart valve. Myocarditis or pericarditis. Dilated cardiomyopathy. Patients in renal or cardiac transplantation protocol for any etiology. Congenital heart disease that requires knowing the coronary anatomy prior to surgical correction. The planned procedure can be any of the following: For diagnostic purposes (coronary angiography only, left catheterization, left and right catheterization). For therapeutic purposes: percutaneous coronary intervention (PCI), with or without stent placement. A priori access must be right or left radial artery. Radial arterial pulse may be present or absent by palpation. Modified Allen or Barbeau test should be positive (presence of collateral palmar flow).", "candidate_expression": "((PCI) AND (ST segment elevation) AND (ST-segment elevation) AND (access priori) AND (cardiac catheterization) AND (collateral palmar flow presence) AND (coronary procedure scheduled) AND (department of hemodynamics) AND (drug-invasive therapy will undergo) AND (indications) AND (intervene artery) AND (left catheterization) AND (palpation) AND (percutaneous coronary intervention therapeutic) AND (procedure) AND (pulse Radial arterial) AND (right catheterization) AND (stent placement) AND (the National Institute of Cardiology \"Ignacio Chavez\") AND (thrombolytic therapy successful) AND (years older than 18) AND NOT (reperfusion therapy timely with less than 4 weeks of evolution) AND NOT (ST segment elevation) AND ((Men) OR (women)) AND ((Acute myocardial infarction) OR (Congenital heart disease knowing the coronary anatomy prior to surgical correction.) OR (Disease heart valve) OR (Myocarditis) OR (Thoracic pain) OR (Unstable angina) OR (acute coronary syndrome) OR (cardiac transplantation) OR (cardiomyopathy Dilated) OR (chronic coronary disease Stable) OR (pericarditis) OR (renal transplantation)) AND ((coronary angiography) OR (coronary angiography only)) AND ((left radial artery) OR (right radial artery)) AND ((absent) OR (present)) AND ((Barbeau test) OR (Modified Allen test)))"}
{"candidate_id": "LLM01500", "doc_id": "NCT03344042_exc", "case_bucket": "scope", "source_criterion": "no consent known allergy to administered opioid contraindications to epidural analgesia coagulopathies including platelet count of less than 100,000 spine surgery in past", "candidate_expression": "((allergy) AND (coagulopathies) AND (contraindications) AND (epidural analgesia) AND (in past) AND (less than 100,000) AND (no consent) AND (opioid) AND (platelet count) AND (spine surgery))"}
```
