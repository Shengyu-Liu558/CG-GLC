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
{"candidate_id": "LLM05676", "doc_id": "NCT02462317_inc", "case_bucket": "or", "source_criterion": "First single stroke ischaemic or haemorrhagic responsible of an hemiplegia Stoke since less than 2 month A sufficient understood A spasticity : a Tardieu score upper or equal to 2 on at least one of the following muscle-triceps surae, flexors of fingers, of wrist and of elbow A free consent", "candidate_expression": "((A free consent) AND (First) AND (Stoke) AND (Tardieu score) AND (at least one) AND (hemiplegia) AND (since less than 2 month) AND (single) AND (spasticity) AND (stroke) AND (upper or equal to 2) AND ((elbow) OR (flexors of fingers) OR (muscle-triceps surae) OR (wrist)) AND ((haemorrhagic) OR (ischaemic)))"}
{"candidate_id": "LLM05677", "doc_id": "NCT00954850_inc", "case_bucket": "or", "source_criterion": "Adults (18 and older) with physiologically confirmed SA or mild-moderate asthma and followed by an asthma specialist for at least 6 months. Must agree to have regular clinic visits (minimum 3-4 per year for SA, 1-2 for mild-moderate asthma). Must have good compliance with medications Patients with asthma and COPD.", "candidate_expression": "((18 and older) AND (Adults) AND (Must agree to have regular clinic visits (minimum 3-4 per year for SA, 1-2 for mild-moderate asthma).) AND (SA) AND (asthma) AND (followed by an asthma specialist) AND (for at least 6 months) AND (good compliance) AND (medications) AND ((COPD) OR (asthma)) AND ((mild) OR (moderate)))"}
{"candidate_id": "LLM05678", "doc_id": "NCT00970866_inc", "case_bucket": "or", "source_criterion": "At least 18 years of age No more than 20 wk of gestation Given Ante-natal Cards of the Ghana Health Service Completed the initial routine ante-natal examination at the clinics HIV negative or status unknown (as from the Ante-natal card) Free from chronic disease e.g. malignancy requiring frequent medical attention (as from the Ante-natal card) Residing in the Manya Krobo or Yilo Krobo district Prepared to sign an informed consent Living in the area throughout the duration of the study Acceptance of home visitors", "candidate_expression": "((Acceptance of home visitors) AND (HIV) AND (Living in the area throughout the duration of the study the study) AND (Prepared to sign an informed consent) AND (Residing) AND (age At least 18 years) AND (chronic disease) AND (clinics) AND (gestation) AND (gestation No more than 20 wk) AND (malignancy) AND (routine ante-natal examination) AND ((negative) OR (status unknown)) AND ((Manya Krobo district) OR (Yilo Krobo district)))"}
{"candidate_id": "LLM05679", "doc_id": "NCT01735955_exc", "case_bucket": "or", "source_criterion": "Patient has been permanently discontinued from nilotinib treatment in the parent study due to unacceptable toxicity, non-compliance to study procedures, withdrawal of consent or any other reason Patient has participated in a Novartis sponsored combination trial where nilotinib was dispensed in combination with another study medication and patient is still receiving combination therapy Patients who are currently receiving treatment with any medications that have the potential to prolong the QT interval or inducing Torsade de Pointes and the treatment cannot be either safely discontinued at least one week prior to nilotinib treatment or switched to a different medication prior to start of nilotinib treatment and for the duration of the study Pregnant or nursing (lactating) women, where pregnancy is defined as the state of a female after conception and until the termination of gestation, confirmed by a positive hcG laboratory test. Women of child-bearing potential, defined as all women physiologically capable of becoming pregnant, unless they are using highly effective methods of contraception during the study and for 30 days after the final dose of nilotinib.", "candidate_expression": "((Women) AND (any medications) AND (child-bearing potential) AND (lactating) AND (nilotinib) AND (participated in a combination trial Novartis sponsored) AND (physiologically capable of becoming pregnant) AND (study procedures) AND (treatment currently) AND (women) AND NOT (contraception highly effective methods during the study for 30 days after the final dose of nilotinib) AND NOT (treatment) AND ((any other reason) OR (non-compliance) OR (unacceptable toxicity) OR NOT (consent)) AND ((have the potential to prolong the QT interval) OR (inducing Torsade de Pointes)) AND ((Pregnant hcG laboratory test) OR (nursing)))"}
{"candidate_id": "LLM05680", "doc_id": "NCT02996916_inc", "case_bucket": "or", "source_criterion": "Written informed consent obtained Male and female subjects aged 20 years or older at informed consent Essential hypertension who had never received angiotensin II receptor antagonists and calcium channel blockers", "candidate_expression": "((20 years or older) AND (Essential hypertension) AND (Written informed consent obtained) AND (aged) AND (at informed consent) AND (informed consent) AND (never) AND ((Male) OR (female)) AND ((angiotensin II receptor antagonists) OR (calcium channel blockers)))"}
{"candidate_id": "LLM05681", "doc_id": "NCT01967420_inc", "case_bucket": "or", "source_criterion": "Non-affective psychosis Premorbid IQ of over 70 A service user of the early intervention service Aged 18 or over (up to the age of 35 which is the limit for the early intervention service) Psychiatrically stable enough to attend to completion (no hospitalisations or medication changes in last 4 weeks)", "candidate_expression": "((Aged 18 or over up to the age of 35) AND (Non-affective psychosis) AND (Premorbid IQ over 70) AND (Psychiatrically stable) AND ((hospitalisations) OR (medication changes)))"}
{"candidate_id": "LLM05682", "doc_id": "NCT01891383_exc", "case_bucket": "or", "source_criterion": "Cases (with a history of TBI): 1. History of penetrating brain injury 2. History of disabling neurological or psychiatric condition such as epilepsy (besides posttraumatic epilepsy), multiple sclerosis, cortical stroke, hypoxic-ischemic encephalopathy, encephalitis, or schizophrenia Controls (without a history of TBI): History of disabling neurological or psychiatric condition such as epilepsy, multiple sclerosis, cortical stroke, hypoxic-ischemic encephalopathy, encephalitis, or schizophrenia", "candidate_expression": "((History) AND (condition disabling neurological) AND (cortical stroke) AND (disabling neurological condition) AND (disabling psychiatric condition) AND (encephalitis) AND (epilepsy) AND (hypoxic-ischemic encephalopathy) AND (multiple sclerosis) AND (penetrating brain injury History) AND (psychiatric condition disabling) AND (schizophrenia) AND NOT (posttraumatic epilepsy))"}
{"candidate_id": "LLM05683", "doc_id": "NCT02380118_exc", "case_bucket": "or", "source_criterion": "known hypersensitivity or contraindication to the study drugs reversible aetiology for agitation (e.g. hypotension, hypoxia, hypoglycaemia) known pregnancy acute alcohol withdrawal patients aged>75 years.", "candidate_expression": "((>75 years) AND (acute alcohol withdrawal) AND (aged) AND (agitation) AND (contraindication) AND (hypersensitivity) AND (hypoglycaemia) AND (hypotension) AND (hypoxia) AND (pregnancy) AND (reversible aetiology) AND (study drugs))"}
{"candidate_id": "LLM05684", "doc_id": "NCT02668016_inc", "case_bucket": "or", "source_criterion": "Aged 18 years or older Previously taken one or more statins Withdrawn from statins because of perceived side effects Developed side effects within 2 weeks of initiation Clinical indication for statins for primary or secondary prevention of cardiovascular disease or dyslipidaemia, on either no medication or non-statin lipid lowering therapy (e.g, ezetimibe)", "candidate_expression": "((Aged 18 years or older) AND (indication) AND (side effects within 2 weeks of initiation) AND (statins) AND (statins one or more) AND ((primary) OR (secondary)) AND ((dyslipidaemia) OR (prevention of cardiovascular disease)))"}
{"candidate_id": "LLM05685", "doc_id": "NCT03381755_inc", "case_bucket": "scope", "source_criterion": "After half-dose ticagrelor (loading dose 90mg, and then 45mg bidpo.) treatment for 3 days, the platelet aggregation is effectively inhibited by light transmission aggregometry method and thromboela-stogram. planned to undergo PCI recently planned to DAPT for 1 year after PCI", "candidate_expression": "((45mg bidpo.) AND (90mg) AND (DAPT) AND (PCI) AND (after PCI) AND (effectively) AND (for 1 year) AND (half-dose) AND (inhibited) AND (light transmission aggregometry) AND (loading dose) AND (planned to) AND (planned to undergo) AND (platelet aggregation) AND (recently) AND (thromboela-stogram) AND (ticagrelor) AND (treatment for 3 days))"}
{"candidate_id": "LLM05686", "doc_id": "NCT03305575_exc", "case_bucket": "or", "source_criterion": "Abdominal and complex cervical cerclage (e.g. bulging bag) Contraindication to neuraxial anesthesia Known hypersensitivity to chloroprocaine (a.k.a. Ester allergy), paraaminobenzoic acid (PABA) or bupivacaine (a.k.a. Amide allergy) Pseudocholinesterase deficiency Concomitant use with ergot-type oxytocic drugs", "candidate_expression": "((Abdominal) AND (Amide allergy) AND (Concomitant) AND (Contraindication) AND (Ester allergy) AND (PABA) AND (Pseudocholinesterase deficiency) AND (bulging bag) AND (bupivacaine) AND (cervical cerclage) AND (chloroprocaine) AND (complex) AND (ergot-type oxytocic drugs) AND (hypersensitivity) AND (neuraxial anesthesia) AND (paraaminobenzoic acid))"}
{"candidate_id": "LLM05687", "doc_id": "NCT02570230_exc", "case_bucket": "or", "source_criterion": "allergy to morphine or ketamine contraindicate to ketamine remain intubated in the postoperative period", "candidate_expression": "((allergy) AND (contraindicate) AND (intubated) AND (intubated in the postoperative period) AND (ketamine) AND ((ketamine) OR (morphine)))"}
{"candidate_id": "LLM05688", "doc_id": "NCT01770340_inc", "case_bucket": "or", "source_criterion": "Localized intermediate-risk or high-risk prostate cancer cT3 Gleason score = 7 (3+4 and/or 4+3) and/or PSA = 20 ng/ml intact preoperative erectile function with an IIEF = 21 (IIEF-6).", "candidate_expression": "((Gleason score = 7) AND (IIEF = 21) AND (IIEF-6) AND (PSA = 20 ng/ml) AND (intact erectile function preoperative) AND (prostate cancer cT3) AND ((high-risk) OR (intermediate-risk)) AND ((3+4) OR (4+3)))"}
{"candidate_id": "LLM05689", "doc_id": "NCT02957877_inc", "case_bucket": "other", "source_criterion": "Prevalent NHHD patients who have received >1 year dialysis with unfractionated heparin as anticoagulant Age >= 18 Informed consent available", "candidate_expression": "((>1 year) AND (>= 18) AND (Age) AND (NHHD) AND (anticoagulant) AND (dialysis) AND (unfractionated heparin))"}
{"candidate_id": "LLM05690", "doc_id": "NCT03194074_exc", "case_bucket": "or", "source_criterion": "Patients with cardiac, pulmonary, hepatic, or renal dysfunction, epilepsy, or uncontrolled hypertension, or those taking medications that influence the central nervous system, are excluded from the study. Patients who show obvious alteration of mental status, or refuse to participate, are also excluded from the study.", "candidate_expression": "((refuse to participate) AND ((alteration of mental status) OR (cardiac dysfunction) OR (epilepsy) OR (hepatic dysfunction) OR (hypertension uncontrolled) OR (medications that influence the central nervous system) OR (pulmonary dysfunction) OR (refuse to participate) OR (renal dysfunction)))"}
{"candidate_id": "LLM05691", "doc_id": "NCT03397914_inc", "case_bucket": "or", "source_criterion": "Age between one year and 18 years Sepsis due to MDR or minimally susceptible gram-negative bacteria History of MDR gram-negative infection or sepsis due to organisms sensitive to colistin. Culture result consistent with MDR gram negative for this febrile neutropenic episode. Patient in sepsis and colistin was administered empirically to increase antibiotic coverage.", "candidate_expression": "((Age between one year and 18 years) AND (Sepsis MDR) AND (administered empirically) AND (colistin) AND (gram negative MDR) AND (gram-negative infection) AND (minimally susceptible gram-negative bacteria) AND (organisms sensitive to colistin) AND (sepsis))"}
{"candidate_id": "LLM05692", "doc_id": "NCT03182114_inc", "case_bucket": "other", "source_criterion": "full term singleton pregnant women scheduled for elective cesarean delivery", "candidate_expression": "((cesarean delivery) AND (elective) AND (full term) AND (pregnant) AND (scheduled for) AND (singleton) AND (women))"}
{"candidate_id": "LLM05693", "doc_id": "NCT02573597_inc", "case_bucket": "or", "source_criterion": "ASA I & II, Nulliparous and Multiparous, Spontaneous/Induced/Augmented Labor, Early active labor (cervix <5 cm (if known)), Pain (VPS) > 3, 18-45 years of age", "candidate_expression": "((ASA I & II) AND (Augmented Labor) AND (Early active labor) AND (Induced Labor) AND (Multiparous) AND (Nulliparous) AND (Pain (VPS) > 3) AND (Spontaneous Labor) AND (age 18-45 years) AND (cervix <5 cm))"}
{"candidate_id": "LLM05694", "doc_id": "NCT02777424_exc", "case_bucket": "other", "source_criterion": "Concomitant use with oral anticoagulant drugs Acquired deficiency of coagulation factors whose treatment is established Hypersensitivity to a PCC History of thrombocytopenia induced by heparin Disseminated intravascular coagulation Extracranial active bleeding Hypersensitivity to vitamin K", "candidate_expression": "((Acquired deficiency of coagulation factors whose treatment is established) AND (Disseminated intravascular coagulation) AND (Extracranial bleeding active) AND (Hypersensitivity) AND (PCC) AND (heparin) AND (oral anticoagulant drugs Concomitant) AND (thrombocytopenia) AND (vitamin K))"}
{"candidate_id": "LLM05695", "doc_id": "NCT03460002_inc", "case_bucket": "other", "source_criterion": "Children aged 0-59 months living with families registered in the rural Bandim Health Project Health and Demographic Surveillance Site are included, provided a parent/guardian consent.", "candidate_expression": "((0-59 months) AND (Children) AND (Person Surveillance Site) AND (aged) AND (living with families registered in the rural Bandim Health Project Health))"}
{"candidate_id": "LLM05696", "doc_id": "NCT01491763_exc", "case_bucket": "or", "source_criterion": "Any other variety of LAL Patients with a history of coronary artery disease, valvular or hypertensive heart disease Patients with chronic liver disease Patients with chronic respiratory failure Renal failure not due to LAL Patients with positive HIV status No serious neurological abnormalities due to LAL Impact on overall severe (grade 3 or 4 of the WHO scale) not attributable to the LAL Pregnant or breastfeeding initial blast crisis CML", "candidate_expression": "((CML blast crisis) AND (HIV status positive) AND (LAL due to) AND (LAL other variety) AND (Renal failure) AND (chronic liver disease) AND (chronic respiratory failure) AND NOT (LAL due to) AND NOT (neurological abnormalities serious) AND ((Pregnant) OR (breastfeeding)) AND ((coronary artery disease) OR (heart disease valvular) OR (hypertensive heart disease)))"}
{"candidate_id": "LLM05697", "doc_id": "NCT03034096_exc", "case_bucket": "or", "source_criterion": "Age less than 18 years American Society of Anesthesiologist Class 5 Projected life expectancy less than 30 days Known or suspected hypersensitivity to either propofol, e.g. egg or soy allergy, or volatile general anesthetic agents Known or suspected history of malignant hyperthermia", "candidate_expression": "((5) AND (Age) AND (American Society of Anesthesiologist Class) AND (Known) AND (Projected life expectancy) AND (allergy) AND (egg) AND (history) AND (hypersensitivity) AND (less than 18 years) AND (less than 30 days) AND (malignant hyperthermia) AND (propofol) AND (soy) AND (suspected) AND (volatile general anesthetic agents))"}
{"candidate_id": "LLM05698", "doc_id": "NCT03044093_exc", "case_bucket": "other", "source_criterion": "hematology diseases clotting factor deficiency", "candidate_expression": "((clotting factor deficiency) AND (hematology diseases))"}
{"candidate_id": "LLM05699", "doc_id": "NCT02195024_exc", "case_bucket": "or", "source_criterion": "Pacing threshold(s) (at 0.4 or 0.5 ms) and/or sensing amplitude(s) and/or impedance(s) are not measurable Meet one or more of the contraindications for MRI including Psychiatric disorders, anxiety, claustrophobia Cardiac disorders that represent a contraindication to MRI Cardiac surgery already scheduled in the next three months Have other medical implants that may interact with MRI, e.g. abandoned implantable cardioverter defibrillator (ICD) leads or pacemaker leads other than MRI conditional, lead extensions, other active medical devices, non-MRI compatible devices, mechanical valve Have other metallic artifacts/components in body that may interact with MRI Subjects for whom a single dose of 1.0 milligram (mg) dexamethasone acetate may be contraindicated Subjects who require a legally authorized representative to obtain consent Subjects who are immediate candidates for an ICD Subjects with medical conditions that preclude the testing required by the protocol or limit study participation Subjects who are enrolled or intend to participate in another clinical trial (of an investigational drug or device, new indication for an approved drug or device, or requirement of additional testing beyond standard clinical practice) during this clinical study Being pregnant Have a life expectancy of less than three months Subjects with exclusion criteria required by local law (e.g. age, breastfeeding)", "candidate_expression": "((Cardiac surgery) AND (ICD) AND (MRI) AND (MRI conditional) AND (Subjects with exclusion criteria required by local law (e.g. age, breastfeeding)) AND (at 0.4 or 0.5 ms) AND (candidates for) AND (contraindicated) AND (contraindication) AND (contraindications) AND (dexamethasone acetate) AND (dose of 1.0 milligram (mg)) AND (immediate) AND (in the next three months) AND (interact) AND (interact with MRI) AND (less than three months) AND (life expectancy) AND (medical conditions) AND (medical implants) AND (not measurable) AND (one or more) AND (other) AND (other than) AND (pregnant) AND (scheduled) AND (single) AND (testing required by the protoco) AND (three months) AND ((Pacing threshold) OR (impedance) OR (sensing amplitude)) AND ((Cardiac disorders) OR (Psychiatric disorders) OR (anxiety) OR (claustrophobia)) AND ((abandoned implantable cardioverter defibrillator (ICD) leads) OR (active medical devices) OR (lead extensions) OR (mechanical valve) OR (non-MRI compatible devices) OR (pacemaker leads)) AND ((metallic artifacts) OR (metallic components)) AND ((limit study participation) OR (preclude)))"}
{"candidate_id": "LLM05700", "doc_id": "NCT02970773_inc", "case_bucket": "other", "source_criterion": "Motor complete tetraplegia for at least 3 months Age from 18 to 74 years Body mass index (BMI) from 18 to 35kg/m2 Informed consent as documented by signature", "candidate_expression": "((Age from 18 to 74 years) AND (BMI) AND (Body mass index from 18 to 35kg/m2) AND (nformed consent as documented by signature) AND (tetraplegia complete at least 3 months))"}
```
