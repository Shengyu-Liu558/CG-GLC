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
{"candidate_id": "LLM07776", "doc_id": "NCT03495609_inc", "case_bucket": "other", "source_criterion": "premenopausal women BRCA1 carrier", "candidate_expression": "((BRCA1 carrier) AND (premenopausal) AND (women))"}
{"candidate_id": "LLM07777", "doc_id": "NCT03120533_inc", "case_bucket": "other", "source_criterion": "Healthy Volunteers: Age of at least 18 years Existence of a contraceptive method for women of child-bearing age Person affiliated to social security or beneficiary of such a scheme Signed consent form Systemic sclerosis patients: Systemic sclerosis meeting the EULAR criteria. Presence of at least 2 ischemic digital cutaneous ulcerations on two different fingers, with digital ulcers classified as \"active ulcers\" according to the North American working group definition: epithelial denudation is clearly Visible at one place and the bed of de-epithelialized ulcer can be seen; Ulcerations distal to the proximal interphalangeal joint, not associated with calcinosis or bony relief. Ulcers whose major axis measured with the electronic caliper is ≥ 2 mm Age greater than or equal to 18 years Existence of a contraceptive method for women of reproductive age A person who is or is a beneficiary of social security Informed and signed consent signed by the patient or his / her legal representative.", "candidate_expression": "((Age) AND (EULAR criteria) AND (North American working group definition) AND (Systemic sclerosis) AND (Ulcers) AND (active) AND (age) AND (at least 18 years) AND (at least 2 on two different fingers) AND (child-bearing) AND (contraceptive) AND (contraceptive method) AND (digital ulcers) AND (epithelial denudation is clearly Visible at one place and the bed of de-epithelialized ulcer can be seen; Ulcerations distal to the proximal interphalangeal joint, not associated with calcinosis or bony relief) AND (greater than or equal to 18 years) AND (ischemic digital cutaneous ulcerations) AND (major axis) AND (measured with the electronic caliper) AND (meeting) AND (reproductive) AND (women) AND (≥ 2 mm))"}
{"candidate_id": "LLM07778", "doc_id": "NCT03364036_exc", "case_bucket": "or", "source_criterion": "Previous exposure to drugs such as fingolimod, natalizumab, alemtuzumab, mitoxantrone and ocrelizumab. Positive hepatitis C or hepatitis B surface antigen test and/or hepatits B core antibody test for immunoglobulin G (IgG) and/or immunoglobulin M (IgM). Current or previous history of immune deficiency disorders including a positive human immunodeficiency virus (HIV) result. Currently receiving immunosuppressive or myelosuppressive therapy with, for example, monoclonal antibodies, methotrexate, cyclophosphamide, cyclosporine or azathioprine, or chronic use of corticosteroids. History of tuberculosis , presence of active tuberculosis, or latent tuberculosis Evidence or suspect of Progressive Multifocal Leukoencephalopathy (PML) in Magnetic Resonance Imaging (MRI). Active malignancy or history of malignancy. Other protocol defined exclusion criteria could apply.", "candidate_expression": "((Active) AND (Current) AND (Currently) AND (Evidence) AND (History) AND (Magnetic Resonance Imaging (MRI)) AND (Positive) AND (Previous) AND (Progressive Multifocal Leukoencephalopathy (PML)) AND (active) AND (alemtuzumab) AND (azathioprine) AND (chronic use) AND (corticosteroids) AND (cyclophosphamide) AND (cyclosporine) AND (drugs) AND (fingolimod) AND (hepatitis B surface antigen test) AND (hepatitis C surface antigen test) AND (hepatits B core antibody test) AND (history) AND (human immunodeficiency virus (HIV)) AND (immune deficiency disorders) AND (immunoglobulin G (IgG)) AND (immunoglobulin M (IgM)) AND (immunosuppressive therapy) AND (latent) AND (malignancy) AND (methotrexate) AND (mitoxantrone) AND (monoclonal antibodies) AND (myelosuppressive therapy) AND (natalizumab) AND (ocrelizumab) AND (positive) AND (previous history) AND (suspect) AND (tuberculosis))"}
{"candidate_id": "LLM07779", "doc_id": "NCT03212352_exc", "case_bucket": "or", "source_criterion": "Patient does not meet inclusion criteria, discovered after randomization Inability to give informed consent Known clotting disorder or use of anticoagulants Known risk factors for, or presence of, a cardiovascular disease Language barrier", "candidate_expression": "((Inability to give informed consent) AND (Patient does not meet inclusion criteria, discovered after randomization) AND (anticoagulants) AND (clotting disorder) AND ((cardiovascular disease) OR (risk factors cardiovascular disease)))"}
{"candidate_id": "LLM07780", "doc_id": "NCT03173092_inc", "case_bucket": "other", "source_criterion": "Participants must have completed 3 cycles of a bortezomib-based induction regimen (as defined by current NCCN guidelines) and have no evidence of disease progression as defined by IMWG criteria. Participants with light chain and free light chain (FLC) only may be enrolled if they meet all the criteria for a diagnosis of MM. Participants must be considered by their physician eligible to receiving the IRD regimen. Eastern Cooperative Oncology Group (ECOG) performance status and/or other performance status 0, 1, or 2 at time of enrollment.", "candidate_expression": "((Eastern Cooperative Oncology Group (ECOG) performance status 0, 1, or 2 at time of enrollment) AND (IMWG criteria no evidence of disease progression) AND (IRD regimen eligible to) AND (bortezomib) AND (criteria for a diagnosis of MM all) AND (induction regimen 3 cycles NCCN guidelines) AND (light chain and free light chain (FLC)))"}
{"candidate_id": "LLM07781", "doc_id": "NCT03190304_inc", "case_bucket": "or", "source_criterion": "Symptomatic patients with heart failure (men and women) aged >18 years, Functional class II, III or IV by the New York Heart Association (NYHA) Left ventricular ejection fraction <35% Ischemic and nonischemic etiology Type B natriuretic peptide (BNP) >150 pg/ml (or pro-BNP [N-terminal-proBNP] = 600 pg / ml) or if the patient was hospitalized for cardiac decompensation within the preceding 12 months, BNP >100 pg/ml (or N-terminal-proBNP = 400 pg / ml)", "candidate_expression": "((Left ventricular ejection fraction <35%) AND (New York Heart Association (NYHA) Functional class II, III or IV) AND (Symptomatic) AND (aged >18 years) AND (cardiac decompensation) AND (heart failure) AND (hospitalized within the preceding 12 months) AND ((Ischemic etiology) OR (nonischemic etiology)) AND ((Type B natriuretic peptide (BNP) >150 pg/ml) OR (pro-BNP [N-terminal-proBNP] = 600 pg / ml)) AND ((men) OR (women)) AND ((BNP >100 pg/ml) OR (N-terminal-proBNP = 400 pg / ml)))"}
{"candidate_id": "LLM07782", "doc_id": "NCT01312012_exc", "case_bucket": "or", "source_criterion": "major systemic disease Pregnant woman with infection of human immunodeficiency virus or hepatitis C virus Pregnant woman is receiving any drug with antiviral activity or any form of drug therapy for hepatitis B virus Pregnant woman whose ultrasonographic examination reveals congenital anomaly of the fetus Pregnant woman whose amniocentesis reveals any genetic abnormality", "candidate_expression": "((Pregnant) AND (amniocentesis genetic abnormality) AND (drug therapy) AND (drug with antiviral activity) AND (hepatitis B virus) AND (hepatitis C virus) AND (human immunodeficiency virus) AND (major systemic disease) AND (ultrasonographic examination congenital anomaly of the fetus) AND (woman))"}
{"candidate_id": "LLM07783", "doc_id": "NCT03506009_exc", "case_bucket": "or", "source_criterion": "mRS=2; History of stroke within 3 months; History of intracranial hemorrhage; Suspected subarachnoid hemorrhage; Intracranial tumour, vascular malformation or arterial aneurysm; Major surgery within 1 month; Systolic pressure =180 mmHg or diastolic pressure =110 mmHg; Platelet count < 105/mm3; Heparin therapy or oral anticoagulation therapy within 48 hours; Abnormal APTT; Thrombin or Xa factor inhibitor; Severe disease with a life expectancy of less than 3 months; Blood glucose < 50 mg/dL (2.7mmol/L); Patients who have received any other investigational drug or device within 3 months; Pregnancy; Researchers consider patients inappropriate to participate in the registry.", "candidate_expression": "((2.7mmol/L) AND (< 105/mm3) AND (< 50 mg/dL) AND (=110 mmHg) AND (=180 mmHg) AND (=2) AND (APTT) AND (Abnormal) AND (Blood glucose) AND (Heparin) AND (Intracranial tumour) AND (Major surgery) AND (Patients who have received any other investigational drug or device within 3 months;) AND (Platelet count) AND (Pregnancy) AND (Severe) AND (Systolic pressure) AND (Thrombin) AND (Xa factor inhibitor) AND (arterial aneurysm) AND (diastolic pressure) AND (disease) AND (intracranial hemorrhage) AND (less than 3 months) AND (life expectancy) AND (mRS) AND (oral anticoagulation therapy) AND (stroke) AND (subarachnoid hemorrhage) AND (therapy) AND (vascular malformation) AND (within 1 month) AND (within 3 months) AND (within 48 hours))"}
{"candidate_id": "LLM07784", "doc_id": "NCT02137538_inc", "case_bucket": "or", "source_criterion": "Current height less than 5th percentile AND/OR Predicted adult height (based on bone age) more than 10 cm below target height (mid parental height) Evidence of puberty: physical signs and serum luteinizing hormone > 0.3 IU/L and testosterone > 15 ng/dl", "candidate_expression": "((Evidence of puberty) AND (Predicted adult height bone age more than 10 cm below target height) AND (height Current less than 5th percentile) AND (physical signs) AND ((serum luteinizing hormone > 0.3 IU/L) OR (testosterone > 15 ng/dl)))"}
{"candidate_id": "LLM07785", "doc_id": "NCT02807857_exc", "case_bucket": "or", "source_criterion": "Use of investigational drugs either within 5 half-lives of enrollment, or within 30 days, or until the expected pharmacodynamic effect has returned to baseline, whichever is longer. Major surgery in the last 3 months prior to baseline or planned major surgery or cardiac intervention during the study. Cancer or other significant co-morbidities implying that the patient's condition is unstable. Comorbidities that can be associated with elevated natriuretic peptide (NP) levels: renal insufficiency, (eGFR < 25 ml/min/1.73 m² calculated according to MDRD formula), recent (less than 3 months) cerebral trauma or recent (less than 3 months) cerebrovascular incident, novel diagnosis or acute exacerbation of COPD within the last 3 months. Patients who are primarily managed and regularly followed-up by a cardiologist for their HF Highly frail patients whose estimated lifespan due to comorbidities by the judgement of the investigator is less than 6 months.", "candidate_expression": "((< 25 ml/min/1.73 m²) AND (Comorbidities) AND (Major surgery) AND (NP) AND (baseline or planned major surgery or cardiac intervention during the stud) AND (eGFR) AND (elevated) AND (last 3 months) AND (last 3 months prior to baseline or planned major surgery or cardiac intervention during the study) AND (less than 3 months) AND (less than 6 months) AND (lifespan) AND (natriuretic peptide levels) AND ((acute exacerbation of COPD) OR (cerebral trauma) OR (cerebrovascular incident) OR (renal insufficiency)) AND ((Cancer) OR (co-morbidities)))"}
{"candidate_id": "LLM07786", "doc_id": "NCT02748330_exc", "case_bucket": "other", "source_criterion": "NA", "candidate_expression": "(EMPTY)"}
{"candidate_id": "LLM07787", "doc_id": "NCT01579604_exc", "case_bucket": "or", "source_criterion": "Unstable patient Joint contracture Spasticity Loss of function is expected to be improved by reliable tendon transfer, tenodesis or arthrodesis that is available Evidence of recovering finger/thumb extension at 4-6 months Greater than 12 months from spinal cord injury Subject not fluent in English or an appropriate translator not available", "candidate_expression": "((Joint contracture) AND (Loss of function) AND (Spasticity) AND (Subject not fluent in English or an appropriate translator not available) AND (arthrodesis) AND (patient Unstable) AND (recovering extension at 4-6 months finger thumb) AND (spinal cord injury Greater than 12 months) AND (tendon transfer) AND (tenodesis))"}
{"candidate_id": "LLM07788", "doc_id": "NCT02652572_exc", "case_bucket": "or", "source_criterion": "1. Decrease in size of the designated target ulcer(s) by ≥ 30% during the 7-day screening period 2. Cannot tolerate or comply with compression therapy. 3. An ulcer which shows signs of severe clinical infection, defined as pus oozing from the ulcer site 4. An ulcer positive for β-hemolytic streptococci upon culture 5. The ulcer has > 50% slough, significant necrotic tissue, bone, tendon, or capsule exposure or avascular ulcer beds 6. Is highly exuding (i.e. requires daily change of dressing) 7. Ankle brachial pressure index <0.65 8. Patients with active systemic infections 9. Patients with clinically significant medical conditions as determined by the investigator including renal, hepatic, hematologic, neurologic or immune disease. Examples include but are not limited to: 1. Renal insufficiency as an estimated GFR which is < 30 mL/min/1.7m2 2. Abnormal blood biochemistry defined as 3 times that of the upper limit of the normal range. 3. Hepatic insufficiency defined as total bilirubin > 2 mg/dL or serum albumin < 25 g/L 4. HbA1c > 9% 5. Hemoglobin < 10 g/dL 6. Hematocrit < 0.30 7. Platelet count < 100,000 10. Presence of an active systemic or local cancer or tumor of any kind (with the exception of non-melanoma skin cancer) 11. Patients with severe rheumatoid arthritis (with more than 20 persistently inflamed joints, or below lower normal limit blood albumin level, or evidence of bone and cartilage damage on x-ray, or inflammation in tissues other than joints) and other collagen vascular diseases. 12. Patients with active connective tissue disease 13. Treatment with systemic corticosteroids (>15 mg/day), or current immunosuppressive agents 14. Previous or current radiation therapy or likelihood to receive this therapy during study participation 15. Pregnant or nursing patients 16. Known prior inability or unavailability to complete required study visits during study participation 17. Significant peripheral edema as per investigator's discretion 18. A psychiatric condition (e.g., suicidal ideation) or chronic alcohol or drug abuse problem, determined from the patient's medical history, which, in the opinion of the investigator, may pose a threat to patient compliance 19. Use of a platelet-derived growth factor within 28 days before screening 20. Use of any investigational drug or therapy within 28 days before screening 21. Has any other factor which may, in the opinion of the investigator, compromise participation and/or follow-up in the study", "candidate_expression": "((3 times that of the upper limit of the normal range) AND (< 0.30) AND (< 10 g/dL) AND (< 100,000) AND (< 25 g/L) AND (< 30 mL/min/1.7m2) AND (<0.65) AND (> 2 mg/dL) AND (> 50%) AND (> 9%) AND (>15 mg/day) AND (Abnormal) AND (Ankle brachial pressure index) AND (Cannot tolerate or comply with) AND (Decrease in size) AND (Has any other factor which may, in the opinion of the investigator, compromise participation and/or follow-up in the study) AND (HbA1c) AND (Hematocrit) AND (Hemoglobin) AND (Hepatic insufficiency) AND (Platelet count) AND (Pregnant) AND (Previous) AND (Renal insufficiency) AND (Significant) AND (Treatment) AND (active) AND (alcohol abuse problem) AND (as determined by the investigator) AND (as per investigator's discretion) AND (avascular ulcer beds) AND (below lower normal limit) AND (blood albumin level) AND (blood biochemistry) AND (bone and cartilage damage) AND (bone exposure) AND (capsule exposure) AND (change of dressing) AND (clinically significant) AND (collagen vascular diseases) AND (compression therapy) AND (connective tissue disease) AND (current) AND (daily) AND (drug abuse problem) AND (during the 7-day screening period) AND (estimated GFR) AND (hematologic disease) AND (hepatic disease) AND (highly exuding) AND (immune disease) AND (immunosuppressive agents) AND (in the opinion of the investigator) AND (inflamed joints) AND (inflammation in tissues other than joints) AND (investigational drug) AND (investigational therapy) AND (likelihood to) AND (local cancer) AND (may pose a threat to patient compliance) AND (medical conditions) AND (more than 20) AND (necrotic tissue) AND (neurologic disease) AND (non-melanoma skin cancer) AND (nursing) AND (peripheral edema) AND (persistently) AND (platelet-derived growth factor) AND (pose a threat) AND (positive for β-hemolytic streptococci) AND (psychiatric condition) AND (pus) AND (radiation therapy) AND (renal disease) AND (rheumatoid arthritis) AND (screening) AND (serum albumin) AND (severe) AND (severe clinical infection) AND (shows signs of severe clinical infection) AND (slough) AND (suicidal ideation) AND (systemic cancer) AND (systemic corticosteroids) AND (systemic infections) AND (target ulcer) AND (tendon exposure) AND (total bilirubin) AND (tumor of any kind) AND (ulcer) AND (with the exception of) AND (within 28 days before screening) AND (x-ray) AND (≥ 30%))"}
{"candidate_id": "LLM07789", "doc_id": "NCT03387059_inc", "case_bucket": "or", "source_criterion": "All infertile women treated with intracytoplasmic sperm injection (ICSI)/Fertilization in Vitro and Embryo Transfer (FIVET) Less than or equal to (<=) 1 previous failed embryo transfer Eumenorrheic normo-gonadotropic women Basal follicle-stimulating hormone (FSH) <=12 International unit per liter (IU/L) Anti-mullerian hormone (AMH) greater than (>) 1.1 nanogram per milliliter (ng/mL) Ovarian Reserve: number of antral follicles 2 millimeter (mm) between 6 <= antral follicle count (AFC) <= 16 Follicles > 16 mm at the triggering day between 5-14 Body Mass Index (BMI) between 18 <= BMI <= 27 kilogram per meter square (kg/m^2) Indication for Fresh Embryo transfer Normal uterine cavity on ultrasound exam (e.g., no presence of hydrosalpinx) Undergoing Assisted Reproductive Technique (ART) and oocyte maturation by human chorionic gonadotropin (HCG) triggering Progesterone (P4) serum level at the HCG triggering day <= 1.5 ng/mL (Day O/Randomization) Estradiol (E2) <= 3000 picogram/milliliter (pg/mL) at the human chorionic gonadotropin (HCG) triggering day (Day 0/Randomization) Subjects must have read and signed the Informed Consent Form prior to study-specific-procedures not part of standard of care Other protocol defined inclusion criteria could apply", "candidate_expression": "((Anti-mullerian hormone (AMH) greater than (>) 1.1 nanogram per milliliter (ng/mL)) AND (Assisted Reproductive Technique (ART)) AND (Basal follicle-stimulating hormone (FSH) <=12 International unit per liter (IU/L)) AND (Body Mass Index (BMI) between 18 <= BMI <= 27 kilogram per meter square (kg/m^2)) AND (Day 0/Randomization) AND (Estradiol (E2) <= 3000 picogram/milliliter (pg/mL) at the human chorionic gonadotropin (HCG) triggering day Day O/Randomization) AND (Eumenorrheic) AND (Follicles > 16 mm at the triggering day between 5-14) AND (Fresh Embryo transfer Indication for) AND (Progesterone (P4) serum level at the HCG triggering day) AND (Subjects must have read and signed the Informed Consent Form prior to study-specific-procedures not part of standard of care) AND (human chorionic gonadotropin (HCG) triggering) AND (infertile) AND (normo-gonadotropic) AND (number of antral follicles 2 millimeter (mm) between 6 <= antral follicle count (AFC) <= 16) AND (oocyte maturation) AND (previous failed embryo transfer Less than or equal to (<=) 1) AND (ultrasound exam Normal uterine cavity) AND (women) AND NOT (hydrosalpinx) AND ((Fertilization in Vitro and Embryo Transfer (FIVET)) OR (intracytoplasmic sperm injection (ICSI))))"}
{"candidate_id": "LLM07790", "doc_id": "NCT02109081_inc", "case_bucket": "other", "source_criterion": "patients = 70 years of age, undergoing a noncardiac surgical procedure under general anesthesia, with an anticipated duration of postoperative admission of at least 2 days.", "candidate_expression": "((admission postoperative) AND (age = 70 years) AND (duration of postoperative admission anticipated at least 2 days) AND (general anesthesia) AND (noncardiac surgical procedure))"}
{"candidate_id": "LLM07791", "doc_id": "NCT02062489_exc", "case_bucket": "or", "source_criterion": "The patients have other cancers at the same time or have the history of other cancers except controlled skin basal cell carcinoma or skin squamous cell carcinoma or carcinoma in situ of cervix uterus; The patients have active infections that were not suitable for chemotherapy; The patients have severe non-cancerous diseases. The patients have history of neoadjuvant hormone therapy. The patients have bilateral breast cancers or DCIS or metastatic breast cancers. The patients are undergoing current administration of anti-cancer therapies, or are attending other clinical trials. The patients are pregnant or lactational, or they refuse to practice contraception during the whole trial. The patients are in some special conditions that they can't understand the written informed consent, such as they are demented or hawkish. The patients have allergic history or contraindication of tamoxifen.", "candidate_expression": "((DCIS) AND (The patients are in some special conditions that they can't understand the written informed consent, such as they are demented or hawkish.) AND (active) AND (allergic) AND (anti-cancer therapies) AND (at the same time) AND (attending other clinical trials) AND (bilateral breast cancers) AND (carcinoma in situ of cervix uterus) AND (contraception) AND (contraindication) AND (controlled skin basal cell carcinoma) AND (during the whole trial) AND (except) AND (infections) AND (lactational) AND (metastatic breast cancers) AND (neoadjuvant hormone therapy) AND (non-cancerous diseases) AND (not) AND (other cancers) AND (pregnant) AND (refuse to practice) AND (severe) AND (skin squamous cell carcinoma) AND (suitable for chemotherapy) AND (tamoxifen))"}
{"candidate_id": "LLM07792", "doc_id": "NCT03026088_inc", "case_bucket": "or", "source_criterion": "18-80 year, male or female. Chronic Heart failure subjects with medical history of cardiac disease or other related cardiovascular disease. Left ventricular ejection fraction (LVEF) less than or equal to (=<) 40 percent (%). New York Heart Association (NYHA) class of II - IV NYHA II : Slight limitation of physical activity. Comfortable at rest, but ordinary physical activity results in undue breathlessness, fatigue or palpitation. NYHA III:Marked limitation of physical activity. Comfortable at rest, but less than ordinary activity causes undue breathlessness, fatigue or palpitation. NYHA IV:Unable to carry on any physical activity without discomfort. Symptoms at rest can be present. If any physical activity is undertaken, discomfort increased. Signed Informed Consent Form (ICF).", "candidate_expression": "((18-80) AND (=< 40 %) AND (Chronic Heart failure) AND (II - IV) AND (LVEF) AND (Left ventricular ejection fraction) AND (NYHA) AND (New York Heart Association class) AND (Signed Informed Consent Form (ICF)) AND (cardiac disease) AND (cardiovascular disease) AND (female) AND (less than or equal to 40 percent) AND (male) AND (related) AND (year))"}
{"candidate_id": "LLM07793", "doc_id": "NCT03420638_exc", "case_bucket": "or", "source_criterion": "Presence of severe systemic disease Presence of coagulation disorders Current or previous history of analgesic dependence Allergy to any of the drugs used in the study Women pregnant or lactating, or women planning to become pregnant Presence of hearing loss Presence of cardiovascular comorbidities Presence of hepatic comorbidities Presence of kidney comorbidities Presence of cognitive disabilities", "candidate_expression": "((Allergy) AND (Current) AND (Women) AND (analgesic) AND (analgesic dependence) AND (cardiovascular comorbidities) AND (coagulation disorders) AND (cognitive disabilities) AND (drugs used in the study) AND (hearing loss) AND (hepatic comorbidities) AND (history) AND (kidney comorbidities) AND (lactating) AND (planning to become) AND (pregnant) AND (previous) AND (severe) AND (systemic disease) AND (women))"}
{"candidate_id": "LLM07794", "doc_id": "NCT03338855_exc", "case_bucket": "or", "source_criterion": "Involvement in the planning and conduct of the study (applies to both AstraZeneca staff and staff at third party vendor or at the investigational sites). Previous enrolment in the present study or participation in another clinical study with an investigational product during the last 3 months or as judged by the Investigator. History of or presence of any clinically significant disease or disorder including a recent (< 3 months) cardiovascular event which, in the opinion of the Investigator, may either put the patient at risk because of participation in the study or influence the results or the patient's ability to participate in the study. Clinical diagnosis of Type 1 diabetes, maturity onset diabetes of the young, secondary diabetes or diabetes insipidus. Unstable/rapidly progressing renal disease or estimated Glomerular Filtration Rate < 60 mL/min (Cockcroft-Gault formula). Clinically significant out of range values of serum levels of either alanine aminotransferase (ALT), aspartate aminotransferase (AST) or alkaline phosphatase (ALP) in the Investigator's opinion. Contraindications to dapagliflozin according to the local label. Use of antidiabetic drugs other than metformin within 3 months prior to screening. Weight gain or loss > 5 kg in the last 3 months, ongoing weight-loss diet (hypocaloric diet) or use of weight loss agents. History of drug abuse or alcohol abuse in the past 12 months. Any clinically significant abnormalities in clinical chemistry, hematology or urinalysis or other condition the Investigator believes would interfere with the patient's ability to provide informed consent, comply with study instructions, or which might confound the interpretation of the study results or put the patient at undue risk. Plasma donation within one month of screening or any blood donation/blood loss > 500 mL within 3 months prior to screening or during the study. Anemia defined as Hemoglobin (Hb) < 115 g/L (7.1 mM) in women and < 120 g/L (7.5 mM) in men. Use of anti-coagulant treatment such as heparin, warfarin, platelet inhibitors, thrombin and factor X inhibitors. Use of medication such as oral glucocorticoids, anti-estrogens or other medications that are known to markedly influence insulin sensitivity. Use of loop diuretics. Regular smoking and other regular nicotine use. Central nervous system aneurysm clip Implanted neural stimulator Implanted cardiac pacemaker of defibrillator Cochlear implant Metal containing corpora aliena in the eye or brain. Patients, who do not want to be informed about unexpected medical findings, or do not wish that their physician be informed about coincidental findings, cannot participate in the study.", "candidate_expression": "((7.1 mM) AND (7.5 mM) AND (< 115 g/L) AND (< 120 g/L) AND (< 3 months) AND (< 60 mL/min) AND (> 5 kg) AND (> 500 mL) AND (Anemia) AND (Any clinically significant abnormalities in clinical chemistry, hematology or urinalysis or other condition the Investigator believes would interfere with the patient's ability to provide informed consent, comply with study instructions, or which might confound the interpretation of the study results or put the patient at undue risk.) AND (Central nervous system aneurysm clip) AND (Clinically significant) AND (Cochlear implant) AND (Cockcroft-Gault formula) AND (Contraindications) AND (Hemoglobin (Hb)) AND (History) AND (History of or presence of any clinically significant disease or disorder including a recent (< 3 months) cardiovascular event which, in the opinion of the Investigator, may either put the patient at risk because of participation in the study or influence the results or the patient's ability to participate in the study) AND (Implanted neural stimulator) AND (Metal containing) AND (Plasma donation) AND (Previous enrolment in the present study or participation in another clinical study with an investigational product during the last 3 months or as judged by the Investigator.) AND (Regular) AND (Type 1 diabetes) AND (Unstable) AND (Weight gain) AND (Weight loss) AND (alanine aminotransferase (ALT)) AND (alcohol abuse) AND (alkaline phosphatase (ALP)) AND (anti-coagulant treatment) AND (anti-estrogens) AND (antidiabetic drugs) AND (aspartate aminotransferase (AST)) AND (blood donation) AND (blood loss) AND (cardiac pacemaker) AND (cardiovascular event) AND (clinically significant) AND (corpora aliena in the brain) AND (corpora aliena in the eye) AND (dapagliflozin) AND (defibrillator) AND (diabetes insipidus) AND (disease) AND (disorder) AND (drug abuse) AND (during the study) AND (estimated Glomerular Filtration Rate) AND (factor X inhibitors) AND (heparin) AND (hypocaloric diet) AND (in the last 3 months) AND (in the past 12 months) AND (loop diuretics) AND (markedly influence insulin sensitivity) AND (maturity onset diabetes of the young) AND (medications) AND (men) AND (metformin) AND (nicotine) AND (ongoing) AND (oral glucocorticoids) AND (other) AND (other than) AND (out of range values) AND (platelet inhibitors) AND (rapidly progressing) AND (recent) AND (regular) AND (renal disease) AND (screening) AND (secondary diabetes) AND (smoking) AND (thrombin) AND (warfarin) AND (weight loss agents) AND (weight-loss diet) AND (within 3 months prior to screening) AND (within one month of screening) AND (women))"}
{"candidate_id": "LLM07795", "doc_id": "NCT02162433_inc", "case_bucket": "or", "source_criterion": "Patients between 3 to 16 years of age undergoing adenotonsillectomy, with or without myringotomy or myringoplasty ASA 1 & 2", "candidate_expression": "((ASA 1 & 2) AND (adenotonsillectomy undergoing) AND (age between 3 to 16 years) AND ((myringoplasty) OR (myringotomy)))"}
{"candidate_id": "LLM07796", "doc_id": "NCT02413970_inc", "case_bucket": "or", "source_criterion": "Likely suffer moderate-to-severe OSA based on history and physical or have an established diagnosis of OSA (20=AHI=65) based on a prior in-lab Polysomnography Documentation the subject not effectively treated with CPAP therapy. (Examples include non-compliance, discomfort, undesirable side effects, symptoms persist despite use). Subjects who have been prescribed, but refuse to try CPAP would be considered intolerant. Age 22 or above Willing and capable to have stimulation hardware permanently implanted, and to use the patient remote to activate the stimulation Willing and capable to return for all follow-up visits and conduct sleep studies at home, including the evaluation procedures and filling out questionnaires Willing and capable of providing informed consent", "candidate_expression": "((20 =65) AND (22 or above) AND (AHI) AND (Age) AND (CPAP therapy) AND (Willing and capable of providing informed consent) AND (Willing and capable to have stimulation hardware permanently implanted, and to use the patient remote to activate the stimulation) AND (Willing and capable to return for all follow-up visits and conduct sleep studies at home, including the evaluation procedures and filling out questionnaires) AND (not) AND ((OSA)) AND ((moderate) OR (severe)))"}
{"candidate_id": "LLM07797", "doc_id": "NCT03305666_inc", "case_bucket": "other", "source_criterion": "Patients undergoing SSRF at Denver Health Medical Center", "candidate_expression": "((Denver Health Medical Center) AND (SSRF))"}
{"candidate_id": "LLM07798", "doc_id": "NCT02196285_exc", "case_bucket": "or", "source_criterion": "Serious adverse reaction to any vaccination, as respiratory difficulty, angioedema and anaphylaxis; Acute or chronic disease, as diabetes, heart disease, systemic arterial hypertension; Use of anti-allergic with antigen injections in a maximum timeline of 14 days before the vaccination; Use of immunoglobulin in the past 12 months before the study vaccination; Use of blood products within 12 months before the vaccination; Use of any vaccine type within 30 days before the vaccination of the study; Chronic use of any medication, except homeopathy, and trivial ones, as nasal physiologic solution and vitamins; Previous immunosuppressive or cytotoxic medication, in the last 6 months. Individuals who have made use of this kind of medication in non-immunosuppressant doses, as nasal corticosteroid for allergic rhinitis of topic corticosteroid for non-complicated dermatitis, for more than 14 days, are allowed to be included in the study. Use of any kind of medication under investigation within one year before the vaccination. Unstable asthma or which may have required urgent care, hospitalization or intubation within the last 2 years, or which requires use of oral or intravenous corticosteroid. Coagulopathies diagnosed by a physician or report of capillary fragility (ex: bruises or bleedings without justifiable cause; Convulsions, except the ones caused by fever, before 2 years old; Psychiatric disease which difficults the adherence to the protocol, such as psychosis, obsessive-compulsive disorders, bipolar disease under treatment, diseases which require treatment with lithium and suicidal ideas in the last 5 years from the inclusion; Active malignant (p.e. any kind of cancer) or treated disease, to which the individual may relapse during the study; Asplenia (absence of spleen or its removal); Positive HIV in the screening examination of history of any immunosuppressant disease; Positive serology for C hepatitis in the screening evaluation; Positive Antigen HBs in the screening evaluation; Alcoholism (CAGE criteria), used for detection of abusive drinkers or alcoholic, validated in the Brazilian population with sensibility of 88% and specificity of 83%, if two or more answers, among four possible, are afirmative(Mansur and Monteiro, 1983), or according to medical decision; Abuse of illicit drugs, according to medical decision; Acquired or congenital immunodeficiency; Allergy to the vaccine compounds, as egg, neomycin and gelatin.", "candidate_expression": "((Abuse of illicit drugs) AND (Acquired immunodeficiency) AND (Acute disease) AND (Alcoholism) AND (Allergy to the vaccine compounds) AND (Antigen HBs Positive in the screening evaluation screening evaluation) AND (Asplenia the study) AND (CAGE criteria Alcoholism) AND (Coagulopathies) AND (Convulsions caused by fever before 2 years old) AND (HIV Positive in the screening examination screening examination) AND (Psychiatric disease difficults the adherence to the protocol) AND (Unstable asthma required urgent care required hospitalization required intubation) AND (according to medical decision) AND (adverse reaction) AND (anaphylaxis) AND (angioedema) AND (anti-allergic maximum timeline of 14 days before the vaccination) AND (antigen injections) AND (any medication Chronic use) AND (any vaccine type within 30 days before the vaccination of the study) AND (bipolar disease under treatment) AND (bleedings without justifiable cause) AND (blood products within 12 months before the vaccination) AND (bruises without justifiable cause) AND (cancer any kind malignant treated) AND (capillary fragility) AND (chronic disease) AND (congenital immunodeficiency) AND (cytotoxic medication) AND (diabetes) AND (difficults the adherence to the protocol) AND (diseases which require treatment with lithium) AND (egg) AND (fever 2 years old) AND (gelatin) AND (heart disease) AND (homeopathy) AND (hospitalization) AND (immunoglobulin in the past 12 months before the study vaccination) AND (immunosuppressant disease) AND (immunosuppressive medication) AND (intravenous corticosteroid) AND (intubation requires use of oral corticosteroid requires use of intravenous corticosteroid) AND (lithium) AND (malignant disease Active) AND (medication under investigation within one year before the vaccination) AND (nasal physiologic solution) AND (neomycin) AND (obsessive-compulsive disorders) AND (oral corticosteroid) AND (psychosis) AND (respiratory difficulty) AND (serology for C hepatitis Positive in the screening evaluation screening evaluation) AND (spleen removal) AND (suicidal ideas in the last 5 years from the inclusion the inclusion) AND (systemic arterial hypertension) AND (to which the individual may relapse during the study) AND (treated) AND (treated disease) AND (treatment) AND (treatment with lithium) AND (trivial ones) AND (urgent care) AND (vaccination) AND (vaccine compounds) AND (vitamins) AND NOT (spleen))"}
{"candidate_id": "LLM07799", "doc_id": "NCT02884401_exc", "case_bucket": "or", "source_criterion": "On chronic treatment (i.e., two weeks or more) with any medication severely affecting oral status (e.g. participants with gingival hypertrophy caused by anti-epileptics, calcium antagonists, cyclosporine and other immunosuppressive) or bone metabolism (e.g. anticoagulant medications, long-standing steroid medications -i.e. equal or more 2.5mg of prednisolone a day taken for >3 months -, anticonvulsants, immunosuppressants). Affected by systemic diseases recognized to severely affect bone metabolism (e.g. Cushing's syndrome, Addison's disease, diabetes mellitus type 1, leukaemia, pernicious anaemia, malabsorption syndromes, chronic liver disease, rheumatoid arthritis). Knowingly affected by HIV or Hepatitis. History of local radiation therapy in the last five years. Affected by limited mental capacity or language skills such that study information cannot be understood, informed consent cannot be obtained, or simple instructions cannot be followed. Presenting an acute endodontic/periodontal lesion in the neighboring areas to the implant site. Completely edentulous With evident severe atrophy of the alveolar ridge that could preclude an implant placement (e.g. sharp knife edge ridge) Severe bruxism or clenching habits Smokers of > 5 cigarettes a day. A daily alcohol intake >2 units/day. Other severe acute or chronic medical or psychiatric condition or laboratory abnormality which may increase the risk associated with trial participation or investigational product administration or may interfere with the interpretation of study results and, in the judgment of the investigator, would make the participant inappropriate for entry into this trial. Patients unable or not willing to return for follow-ups.", "candidate_expression": "((> 5 a day) AND (>2 units/day) AND (>3 months) AND (Completely) AND (Patients unable or not willing to return for follow-ups) AND (Smokers) AND (alcohol) AND (cigarettes) AND (edentulous) AND (equal or more 2.5mg a day) AND (ffected by limited mental capacity or language skills such that study information cannot be understood, informed consent cannot be obtained, or simple instructions cannot be followed) AND (last five years) AND (local radiation therapy) AND (treatment) AND (two weeks or more) AND ((anti-epileptics) OR (calcium antagonists) OR (cyclosporine) OR (immunosuppressive)) AND ((bone metabolism) OR (gingival hypertrophy)) AND ((anticoagulant) OR (anticonvulsants) OR (immunosuppressants) OR (prednisolone) OR (steroid)) AND ((HIV) OR (Hepatitis)) AND ((lesion endodontic) OR (periodontal lesion)) AND ((bruxism) OR (clenching habits)) AND ((Addison's disease) OR (Cushing's syndrome) OR (chronic liver disease) OR (diabetes mellitus type 1) OR (leukaemia) OR (malabsorption syndromes) OR (pernicious anaemia) OR (rheumatoid arthritis)))"}
{"candidate_id": "LLM07800", "doc_id": "NCT02462317_exc", "case_bucket": "or", "source_criterion": "Previous antispastic drugs Contraindication for baclofen or toxin Antecedent of epileptic seizure Psychiatric antecedent", "candidate_expression": "((Contraindication) AND (Psychiatric antecedent) AND (antispastic drugs Previous) AND (baclofen) AND (epileptic seizure Antecedent) AND (toxin))"}
```
