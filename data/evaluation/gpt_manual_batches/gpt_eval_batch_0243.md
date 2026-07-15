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
{"candidate_id": "LLM06051", "doc_id": "NCT02334722_inc", "case_bucket": "or", "source_criterion": "Adult (>18 years of age and older) patients who have or will have undergone surgical resection or biopsy of a supratentorial brain tumor and are able to consent for themselves. Able to be randomized prior to or up to 48 hours after surgery.", "candidate_expression": "((Adult) AND (age) AND (and older >18 years) AND (are able to consent for themselves) AND (supratentorial brain tumor) AND (will have undergone) AND ((biopsy) OR (surgical resection)))"}
{"candidate_id": "LLM06052", "doc_id": "NCT02537899_exc", "case_bucket": "or", "source_criterion": "Non survivable injury Multiple significant trauma (i.e. significant intracranial and extracranial injuries including limb fractures) that would limit observation of recovery from spinal cord injury Other conditions that would limit clinical assessment of outcomes (e.g. dementia, demyelinating disease, autoimmune disease, etc) Refusal of treatment or contraindication to NeuroAiD", "candidate_expression": "((NeuroAiD) AND (contraindication) AND (extracranial injuries) AND (injury Non survivable) AND (intracranial injuries) AND (limb fractures) AND (trauma Multiple significant) AND ((autoimmune disease) OR (dementia) OR (demyelinating disease)))"}
{"candidate_id": "LLM06053", "doc_id": "NCT02457442_exc", "case_bucket": "other", "source_criterion": "NA", "candidate_expression": "(EMPTY)"}
{"candidate_id": "LLM06054", "doc_id": "NCT02952378_inc", "case_bucket": "scope", "source_criterion": "For healthy individuals: Healthy, without allergies and with the age of 18 years or above. For patients: Burn injury exceeding 6-8 Total Burned Surface Area %", "candidate_expression": "((18 years or above) AND (Burn injury) AND (Healthy) AND (Total Burned Surface Area) AND (age) AND (allergies) AND (exceeding 6-8 %) AND (healthy) AND (patients) AND (without))"}
{"candidate_id": "LLM06055", "doc_id": "NCT02643381_exc", "case_bucket": "or", "source_criterion": "Children (<18 years old). Women who are known to be pregnant. Any patient who has been previously randomized in the EvK Trial. Patients who require endotracheal intubation without sedative medication. For example, patients in full cardiac arrest. Patients with a known allergy to ketamine or etomidate. Any individual wearing a MedAlert bracelet indicating that he/she has formally opted out of the EvK Trial.", "candidate_expression": "((Any individual wearing a MedAlert bracelet indicating that he/she has formally opted out of the EvK Trial) AND (Children) AND (Women) AND (allergy) AND (endotracheal intubation require) AND (full cardiac arrest) AND (old <18 years) AND (pregnant) AND (randomized previously) AND NOT (sedative medication) AND ((etomidate) OR (ketamine)))"}
{"candidate_id": "LLM06056", "doc_id": "NCT01579604_exc", "case_bucket": "or", "source_criterion": "Unstable patient Joint contracture Spasticity Loss of function is expected to be improved by reliable tendon transfer, tenodesis or arthrodesis that is available Evidence of recovering finger/thumb extension at 4-6 months Greater than 12 months from spinal cord injury Subject not fluent in English or an appropriate translator not available", "candidate_expression": "((Greater than 12 months) AND (Joint contracture) AND (Loss of function) AND (Spasticity) AND (Subject not fluent in English or an appropriate translator not available) AND (Unstable) AND (arthrodesis) AND (at 4-6 months) AND (finger) AND (improved by) AND (patient) AND (recovering extension) AND (spinal cord injury) AND (tendon transfer) AND (tenodesis) AND (thumb))"}
{"candidate_id": "LLM06057", "doc_id": "NCT02632318_inc", "case_bucket": "or", "source_criterion": "History of falls or dizziness at exit from bed in the morning (at least two incidents in the past year) At least 20/200 corrected visual acuity Stable health Normal hearing", "candidate_expression": "((At least 20/200) AND (Normal hearing) AND (Stable health) AND (at exit from bed in the morning) AND (at least two) AND (corrected visual acuity) AND (dizziness) AND (falls) AND (in the past year) AND (incidents))"}
{"candidate_id": "LLM06058", "doc_id": "NCT03044093_exc", "case_bucket": "other", "source_criterion": "hematology diseases clotting factor deficiency", "candidate_expression": "((clotting factor deficiency) AND (hematology diseases))"}
{"candidate_id": "LLM06059", "doc_id": "NCT02504203_inc", "case_bucket": "other", "source_criterion": "Children born outside the cluster, and returning more than 72 hours after the delivery Children that the nurse evaluates to die within the next 24 hours.", "candidate_expression": "(EMPTY)"}
{"candidate_id": "LLM06060", "doc_id": "NCT01743755_inc", "case_bucket": "or", "source_criterion": "18 years or older Chest radiograph showing new opacities. Cough Production of sputum Temp >38,0 °C or <36,0 °C Audible abnormalities by chest examination compatible with pneumonia Leukocytosis (>10.000 cells/mm3), leftward shift (>10%) or leucopenia (<4000 cells/mm3) C-reactive protein > 15 mg/l (three fold higher than the upper limit of normal)", "candidate_expression": "((C-reactive protein > 15 mg/l three fold higher than the upper limit of normal) AND (Chest radiograph) AND (Cough) AND (Leukocytosis >10.000 cells/mm3 leftward shift >10%) AND (Temp >38,0 °C <36,0 °C) AND (chest examination Audible abnormalities) AND (leucopenia <4000 cells/mm3) AND (opacities new) AND (pneumonia) AND (sputum) AND (years 18 or older))"}
{"candidate_id": "LLM06061", "doc_id": "NCT02818816_exc", "case_bucket": "or", "source_criterion": "Patients having had an ophthalmic surgical procedure within 6 months of the beginning of the study. Patients with a diagnosis of glaucoma Any abnormality of the cornea which may prevent reliable applanation tonometry Known allergy/ hypersensitivity reaction to Brimonidine Contra-indication to Brimonidine including patients on monoamine oxidase inhibitors (MOA) Patients unwilling or unable to provide informed consent Patients with anticipated difficult airway management (as this may require medications and/or airway manipulations resulting in increased IOP)", "candidate_expression": "((Brimonidine) AND (Contra-indication) AND (MOA) AND (Patients unwilling or unable to provide informed consen) AND (abnormality) AND (cornea) AND (difficult airway management) AND (glaucoma) AND (monoamine oxidase inhibitors) AND (ophthalmic surgical procedure) AND (study) AND (within 6 months of the beginning of the study) AND ((allergy) OR (hypersensitivity)))"}
{"candidate_id": "LLM06062", "doc_id": "NCT01177891_inc", "case_bucket": "or", "source_criterion": "Patients of familial cases of POF : Female subjects between 16 and 40 years or women older than 40 years with a cessation of ovarian function before the age of 40 years with increased levels of FSH Primary or secondary amenorrhea for more than three months with LH and FSH> 30mUI/ml No cases of fragile X syndrome in the family or blepharophimosis syndrome At least two cases in the family Origin Caucasian Patient signing the consent form for at least the blood sample Patient with Social Security Population Index related topics : The presence of cycles until the age of 40 years with proven fertility, at least one child Amenorrhea and FSH> 30mUI/ml according to the criteria of the index subject Men of the family of index case Population control : Women of Caucasian origin Women who had regular cycles until at least age 40 and at least one child Lack of land autoimmune (no history of thyroid disease or diabetes type 1) Woman signing the consent form for at least the blood sample", "candidate_expression": "((> 30mUI/ml) AND (Amenorrhea) AND (At least two) AND (Caucasian) AND (Caucasian origin) AND (FSH) AND (LH) AND (No) AND (Patient signing the consent form for at least the blood sample) AND (The presence of cycles until the age of 40 years with proven fertility, at least one child) AND (Woman signing the consent form for at least the blood sample) AND (Women) AND (age) AND (amenorrhea) AND (autoimmune) AND (before the age of 40 years) AND (between 16 and 40 years) AND (cessation of ovarian function) AND (for more than three months) AND (history) AND (in the family) AND (increased) AND (levels of FSH) AND (no) AND (older) AND (older than 40 years) AND (presence of cycles) AND (regular cycles) AND (until at least age 40) AND (until the age of 40 years) AND (who had regular cycles until at least age 40) AND (years) AND ((Primary) OR (secondary)) AND ((Female) OR (women)) AND ((blepharophimosis syndrome) OR (fragile X syndrome)) AND ((diabetes type 1) OR (thyroid disease)))"}
{"candidate_id": "LLM06063", "doc_id": "NCT00461136_inc", "case_bucket": "scope", "source_criterion": "Male and/or female patients from 30-80 years of age with a diagnosis of Type 2 diabetes (WHO criteria). Incipient and established diabetic nephropathy (urinary albumin excretion ≥ 100 mg/day but ≤ 2000 mg/day). Glomerular filtration rate (GFR) ≥ 40 ml/min (estimated using Modification of Diet in Renal Disease (MDRD) formula) in the last 4 months. Female patients must be postmenopausal or must have had a bilateral oophorectomy or must have been surgically sterilized or hysterectomized at least 6 months prior to screening. To be eligible patients must fulfill the following criteria: Patients on ongoing hypertensive therapy must have a blood pressure ≥ 135/85 mm Hg but lower than 170/105 mm Hg at baseline (Day -1) AND patients must be on stable antihypertensive medications for at least 8 weeks prior to baseline (Day -1).; Newly diagnosed hypertensive patients must have a blood pressure ≥ 135/85 mm Hg but lower than 170/105 mm Hg at baseline (Day -1). Patients must be on stable hypoglycemic medications for at least 8 weeks prior to Visit 2 ( Day -1). Patients must be willing and medically able to discontinue all Angiotensin-converting enzyme inhibitor (ACEI), Angiotensin receptor blocker (ARB), aldosterone receptor antagonist and potassium sparing diuretic medications for the duration of the study. Oral body temperature within the range 35.0-37.5 °C Able to provide written informed consent prior to study participation. . Able to communicate well with the investigator and comply with the requirements of the study.", "candidate_expression": "((30-80 years) AND (35.0-37.5 °C) AND (Able to communicate well) AND (Female) AND (Glomerular filtration rate (GFR)) AND (Modification of Diet in Renal Disease (MDRD) formula) AND (Newly diagnosed) AND (Oral body temperature) AND (Type 2 diabetes) AND (Visit 2) AND (antihypertensive medications) AND (at baseline (Day -1)) AND (at least 6 months prior to screening) AND (at least 8 weeks prior to Visit 2) AND (at least 8 weeks prior to baseline) AND (baseline) AND (baseline (Day -1)) AND (bilateral oophorectomy) AND (blood pressure) AND (comply with the requirements of the study) AND (diabetic nephropathy) AND (hypertensive patients) AND (hypertensive therapy) AND (hypoglycemic medications) AND (hysterectomized) AND (in the last 4 months) AND (lower than 170/105 mm Hg) AND (of age) AND (postmenopausal) AND (prior to study participation) AND (stable) AND (study participation) AND (surgically sterilized) AND (urinary albumin excretion) AND (written informed consent) AND (≤ 2000 mg/day) AND (≥ 100 mg/day) AND (≥ 135/85 mm Hg) AND (≥ 40 ml/min))"}
{"candidate_id": "LLM06064", "doc_id": "NCT02112734_inc", "case_bucket": "other", "source_criterion": "Healthy, term, breastfeeding infants who will be predominately breastfed for at least 6-months. This will be determined by answering yes/no to question 'do you intend to breastfeed until your infant is at least 6 months of age.'", "candidate_expression": "((Healthy) AND (breastfeeding) AND (infants) AND (predominately breastfed for at least 6-months) AND (term))"}
{"candidate_id": "LLM06065", "doc_id": "NCT03413891_inc", "case_bucket": "or", "source_criterion": "Patients scheduled for dental extraction and treated with edoxaban, apixaban, rivaroxaban or dabigatran Not having taken the direct oral anticoagulant on the day of the extraction Provision of signed and dated informed consent form Stated willingness to comply with all study procedures and availability for the duration of the study", "candidate_expression": "((Not) AND (Provision of signed and dated informed consent form) AND (Stated willingness to comply with all study procedures and availability for the duration of the study) AND (anticoagulant) AND (dental extraction) AND (extraction) AND (on the day of the extraction) AND (oral) AND (scheduled for) AND ((apixaban) OR (dabigatran) OR (edoxaban) OR (rivaroxaban)))"}
{"candidate_id": "LLM06066", "doc_id": "NCT03445949_exc", "case_bucket": "or", "source_criterion": "indications to dual antiplatelet therapy other than atrial fibrillation or left atrial appendage occlusion at the time of enrollment or predicted appearance of such indications within the duration of the trial (eg. coronary artery disease) indications to anticoagulation at the time of enrollment or predicted appearance of such indications within the duration of the trial (eg. pulmonary embolism) known allergy to clopidogrel or acetylsalicylic acid precluding its administration as specified by the protocol any known inborn or acquired coagulation disorders poor tolerance of or technical difficulties with performing transesophageal echocardiography peridevice leak >5mm on transesophageal echocardiography study preceding enrollment left atrial thrombus on transesophageal echocardiography study performed after successful left atrial appendage closure but before enrollment life expectancy of less than 18months participation in other clinical studies with experimental therapies at the time of enrollment and preceding 3 months chronic kidney disease stage IV and V women who are pregnant or breast feeding; women of childbearing potential who do not consent to apply at least to methods of contraception. This criterion does not apply to postmenopausal women", "candidate_expression": "((>5mm) AND (after successful left atrial appendage closure) AND (allergy) AND (anticoagulation) AND (at the time of enrollment) AND (before enrollment) AND (chronic kidney disease) AND (coagulation disorders) AND (coronary artery disease) AND (dual antiplatelet therapy) AND (enrollment) AND (indications) AND (left atrial appendage closure) AND (left atrial thrombus) AND (less than 18months) AND (life expectancy) AND (other than) AND (participation in other clinical studies with experimental therapies at the time of enrollment and preceding 3 months) AND (peridevice leak) AND (predicted appearance) AND (pulmonary embolism) AND (successful) AND (successful left atrial appendage closure) AND (transesophageal echocardiography) AND (transesophageal echocardiography study) AND (within the duration of the trial) AND (women) AND (women who are pregnant or breast feeding; women of childbearing potential who do not consent to apply at least to methods of contraception. This criterion does not apply to postmenopausal women) AND ((acetylsalicylic acid) OR (clopidogrel)) AND ((poor tolerance) OR (technical difficulties)) AND ((atrial fibrillation) OR (left atrial appendage occlusion)) AND ((stage IV) OR (stage V)) AND ((breast feeding) OR (pregnant)))"}
{"candidate_id": "LLM06067", "doc_id": "NCT03187639_inc", "case_bucket": "other", "source_criterion": "Aged over 18 Primary symptom of chest pain No contraindication to CTA Willing and able to provide written informed consent", "candidate_expression": "((Aged) AND (CTA) AND (No) AND (Primary symptom) AND (Willing and able to provide written informed consent) AND (chest pain) AND (contraindication) AND (over 18))"}
{"candidate_id": "LLM06068", "doc_id": "NCT02287259_inc", "case_bucket": "or", "source_criterion": "major depressive episode in type2 bipolar disorder or bipolar disorder NOS.(MADRS more than 20 point) 18years to 65years subjects who sign the informed consent document", "candidate_expression": "((MADRS more than 20 point) AND (major depressive episode) AND (sign the informed consent) AND (years 18years to 65years) AND ((bipolar disorder NOS) OR (type2 bipolar disorder)))"}
{"candidate_id": "LLM06069", "doc_id": "NCT00917891_inc", "case_bucket": "or", "source_criterion": "1. Women 18 to 40 years of age inclusive who can give written informed consent 2. Available for all visits and consent to follow all procedures scheduled for the study 3. Agree to daily application of gel and monitoring as per Daily Monitored Adherence (DMA) method 4. Healthy and self-reported sexually active 5. HIV-negative as determined by a HIV rapid test at time of enrollment 6. On a stable form of contraception and willing to continue on this stable method of contraception, OR, Have undergone surgical sterilisation at least 3 months prior to enrollment 7. In the absence of the use of exogenous hormone(s), have a self-reported regular menstrual cycle defined as having a minimum of 21 days and a maximum of 36 days between menses 8. Upon pelvic/speculum examination and colposcopy at the time of enrollment, the cervix and vagina appear normal as determined by the investigator 9. Asymptomatic for genital infections at the time of enrollment 10. Willing to refrain from use of vaginal products or objects within 14 days prior to enrollment and for the duration of the study 11. Willing to answer acceptability and adherence questionnaires throughout the study 12. Willing to refrain from participation in any other research study for the duration of this study 13. Willing to provide adequate locator information for study retention purposes and be reachable per local standard procedures", "candidate_expression": "((Agree to daily application of gel and monitoring as per Daily Monitored Adherence (DMA) method) AND (Available for all visits and consent to follow all procedures scheduled for the study) AND (HIV negative) AND (HIV rapid test at time of enrollment time of enrollment) AND (HIV-negative) AND (Healthy) AND (On a stable form of contraception and willing to continue on this stable method of contraception, OR, Have undergone surgical sterilisation at least 3 months prior to enrollment) AND (Willing to answer acceptability and adherence questionnaires throughout the study) AND (Willing to provide adequate locator information for study retention purposes and be reachable per local standard procedures) AND (Willing to refrain from participation in any other research study for the duration of this study) AND (Women) AND (acceptability questionnaires) AND (adherence questionnaires) AND (age 18 to 40 years) AND (as determined by the investigator) AND (can give written informed consent) AND (cervix normal) AND (colposcopy) AND (gel daily) AND (genital infections Asymptomatic at the time of enrollment) AND (menstrual cycle regular) AND (monitoring daily) AND (objects vaginal enrollment the study) AND (pelvic examination) AND (regular menstrual cycle minimum of 21 days maximum of 36 days) AND (self-reported) AND (sexually active self-reported) AND (speculum examination) AND (vagina normal normal) AND (vaginal products) AND NOT (exogenous hormone))"}
{"candidate_id": "LLM06070", "doc_id": "NCT02322203_inc", "case_bucket": "other", "source_criterion": "Males and females who are at least 18 years of age at time of enrollment. Subject understands the investigational nature of the study and provides written, informed consent.", "candidate_expression": "((Males) AND (Subject understands the investigational nature of the study and provides written, informed consent.) AND (age) AND (at least 18 years) AND (at time of enrollment) AND (females) AND (time of enrollment))"}
{"candidate_id": "LLM06071", "doc_id": "NCT03120533_exc", "case_bucket": "or", "source_criterion": "Healthy Volunteers Treprostinil contraindications: Known hypersensitivity to treprostinil or any of the excipients, Pulmonary arterial hypertension related to veno-occlusive disease, Congestive heart failure due to severe left ventricular dysfunction, Severe hepatic insufficiency (Child-Pugh stage C), Evolving gastrointestinal ulcer, intracranial hemorrhage, recent trauma or other clinical condition that may lead to bleeding, Congenital or acquired valvular abnormalities with cardiac repercussions, Severe ischemic heart disease or unstable angina; Myocardial infarction in the last six months; Decompensated cardiac insufficiency not medically controlled; Severe arrhythmias; Cerebrovascular lesions (such as transient ischemic attack, stroke) that occurred within the last three months. Persons referred to in Articles L1121-5 to L1121-8 of the French Public health Code: pregnant woman, parturient, nursing mother, person deprived of liberty by judicial or administrative decision, person subject to a legal protection measure, can not Be included in clinical trials. Subject in an exclusion period from another study, Subject who would receive more than 4500 euros of compensation due to his participation in other biomedical research in the 12 months preceding this study Systemic sclerosis patients: Iloprost cure carried out in the previous month or planned in the following month. Initiation or change of dosage of bosentan, sildenafil or calcium channel blockers in the previous month or in the following month Digital Sympathectomy or botulinum toxin injection planned in the following month. Clinically superinfected digital ulcers Treprostinil contraindications: Known hypersensitivity to treprostinil or any of the excipients, Pulmonary arterial hypertension related to veno-occlusive disease, Congestive heart failure due to severe left ventricular dysfunction, Severe hepatic insufficiency (Child-Pugh stage C), Evolving gastrointestinal ulcer, intracranial hemorrhage, recent trauma or other clinical condition that may lead to bleeding, Congenital or acquired valvular abnormalities with cardiac repercussions, Severe ischemic heart disease or unstable angina; Myocardial infarction in the last six months; Decompensated cardiac insufficiency not medically controlled; Severe arrhythmias; Cerebrovascular lesions (such as transient ischemic attack, stroke) that occurred within the last three months. Persons referred to in Articles L1121-5 to L1121-8 of the French Public health Code: pregnant woman, parturient, nursing mother, person deprived of liberty by judicial or administrative decision, person subject to a legal protection measure, can not Be included in clinical trials. Subject in an exclusion period from another study, Subject who would receive more than 4500 euros of compensation due to his participation in other biomedical research in the 12 months preceding this study", "candidate_expression": "((Cerebrovascular lesions) AND (Child-Pugh) AND (Congenital valvular abnormalities) AND (Congestive heart failure) AND (Decompensated cardiac insufficiency) AND (Digital Sympathectomy) AND (Evolving) AND (Iloprost) AND (Myocardial infarction) AND (Pulmonary arterial hypertension) AND (Severe) AND (Systemic sclerosis) AND (Treprostinil) AND (acquired valvular abnormalities) AND (any of the excipients) AND (arrhythmias) AND (bosentan) AND (botulinum toxin injection) AND (calcium channel blockers) AND (clinical condition that may lead to bleeding) AND (contraindications) AND (deprived of liberty) AND (digital ulcers) AND (gastrointestinal ulcer) AND (hepatic insufficiency) AND (hypersensitivity) AND (in the following month) AND (in the last six months) AND (in the previous month) AND (intracranial hemorrhage) AND (ischemic heart disease) AND (left ventricular dysfunction) AND (not medically controlled) AND (nursing) AND (parturient) AND (planned) AND (pregnant) AND (recent) AND (severe) AND (sildenafil) AND (stage C) AND (stroke) AND (subject to a legal protection) AND (superinfected) AND (transient ischemic attack) AND (trauma) AND (treprostinil) AND (unstable angina) AND (veno-occlusive disease) AND (with cardiac repercussions) AND (within the last three months) AND (woman))"}
{"candidate_id": "LLM06072", "doc_id": "NCT02390973_exc", "case_bucket": "or", "source_criterion": "pregnancy past esophageal, gastric or bariatric surgery irritable bowel, unexplained intermittent vomiting, severe abdominal pain, chronic diarrhea or constipation history of gastric or duodenal ulcers pre-operatory hypoalbuminemy history of renal, hepatic, cardiac or pulmonary severe disease taken of corticosteroid in the last month evidence of psycological problem that may affect the capacity to understand the project and to comply with the medical recommandations history of drug use or alcool abuse in the last 12 months history of gastro-intestinal inflammatory diseases", "candidate_expression": "((abdominal pain severe) AND (alcool abuse) AND (bariatric surgery) AND (cardiac disease) AND (constipation) AND (corticosteroid last month) AND (diarrhea) AND (drug use) AND (duodenal ulcers) AND (esophageal surgery) AND (gastric surgery) AND (gastric ulcers) AND (gastro-intestinal inflammatory diseases) AND (hepatic disease severe severe severe) AND (hypoalbuminemy pre-operatory) AND (irritable bowel) AND (pregnancy) AND (pulmonary disease severe) AND (renal disease) AND (vomiting intermittent))"}
{"candidate_id": "LLM06073", "doc_id": "NCT02361905_exc", "case_bucket": "other", "source_criterion": "submucosal leiomyoma, endometrial hyperplasia with atypia, history of uterine surgery", "candidate_expression": "((endometrial hyperplasia with atypia) AND (submucosal leiomyoma) AND (uterine surgery history))"}
{"candidate_id": "LLM06074", "doc_id": "NCT02092467_inc", "case_bucket": "or", "source_criterion": "Moderate to severe rheumatoid arthritis Taking methotrexate without adequate control of symptoms Have at least one cardiovascular risk factor (eg, current smoker, high blood pressure, high cholesterol levels, diabetes mellitus, history of heart attack, family history of coronary heart disease, extra-articular RA disease)", "candidate_expression": "((Moderate to severe) AND (RA disease) AND (adequate control of symptoms) AND (at least one) AND (cardiovascular risk factor) AND (coronary heart disease) AND (current) AND (diabetes mellitus) AND (extra-articular) AND (family history) AND (heart attack) AND (high blood pressure) AND (high cholesterol levels) AND (history) AND (methotrexate) AND (rheumatoid arthritis) AND (smoker) AND (without))"}
{"candidate_id": "LLM06075", "doc_id": "NCT02441179_exc", "case_bucket": "or", "source_criterion": "1. Orthopedic injuries that are unstable 2. Osteoporosis with high risk of pathological fracture 3. Cutaneous lesions and/or pressure ulcers 4. Joint contractures 5. Cardiopulmonary diseases 6. Body weight exceeding 150 Kg", "candidate_expression": "((Body weight) AND (Cardiopulmonary diseases) AND (Joint contractures) AND (Orthopedic injuries) AND (Osteoporosis) AND (exceeding 150 Kg) AND (high risk of pathological fracture) AND (unstable) AND ((Cutaneous lesions) OR (pressure ulcers)))"}
```
