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
{"candidate_id": "LLM03051", "doc_id": "NCT03511521_exc", "case_bucket": "or", "source_criterion": "Patients with 2 or more doses of methylprednisolone/prednisone per day Steroids other than methylprednisolone or prednisone Pregnancy estimated glomerular filtration rate (eGFR) < 45 ml/min/1.73m2", "candidate_expression": "((Pregnancy) AND (Steroids) AND (estimated glomerular filtration rate (eGFR) < 45 ml/min/1.73m2) AND (methylprednisolone) AND (prednisone))"}
{"candidate_id": "LLM03052", "doc_id": "NCT01214096_inc", "case_bucket": "or", "source_criterion": "1. Age: 18-75 years old, no limitation in gender; 2. Left ventricular ejection fraction (LVEF) ≤ 40% (ECHO); 3. Patients with chronic heart failure (NYHA class II or III); 4. In the past one month, the clinical condition (including history, clinical symptoms and signs) was relatively stable; 5. Patients on standard treatment of chronic heart failure at the target dose or maximum tolerance dose for over 1 month ,or unchanged dose in last 1 month; 6. Understand and sign the informed consent form;", "candidate_expression": "((18-75 years) AND (Age) AND (ECHO) AND (In the past one month) AND (Left ventricular ejection fraction (LVEF)) AND (NYHA) AND (Understand and sign the informed consent form;) AND (chronic heart failure) AND (class II or III) AND (clinical signs) AND (clinical symptoms) AND (for over 1 month) AND (history) AND (in last 1 month) AND (relatively stable) AND (treatment of chronic heart failure) AND (unchanged dose) AND (≤ 40%) AND ((maximum tolerance dose) OR (target dose)))"}
{"candidate_id": "LLM03053", "doc_id": "NCT00965900_exc", "case_bucket": "or", "source_criterion": "Patients with systolic blood pressure <100 mmHg or basal heart rate <60/min Portal vein thrombosis Uncontrolled ascites or hepatic encephalopathy Severe coagulation disorder: prothrombin time <40% (or INR >1.7) or platelet count <30,000/mm3 Medium or large sized gastric or duodenal varices Coexisting malignancy Severe cardiovascular disorder, renal failure, peritonitis, sepsis Severe erosive esophagitis, severe esophageal stricture, active gastric or duodenal ulcer Contraindication to beta-blocker Pregnancy Refusal to give consent to participate in the trial", "candidate_expression": "((Contraindication) AND (Portal vein thrombosis) AND (Pregnancy) AND (Refusal to give consent to participate in the trial) AND (beta-blocker) AND (coagulation disorder Severe) AND (malignancy Coexisting) AND ((INR >1.7) OR (platelet count <30,000/mm3) OR (prothrombin time <40%)) AND ((duodenal varices) OR (gastric c)) AND ((Medium) OR (large)) AND ((cardiovascular disorder Severe) OR (peritonitis) OR (renal failure) OR (sepsis)) AND ((heart rate basal <60/min) OR (systolic blood pressure <100 mmHg)) AND ((erosive esophagitis Severe) OR (esophageal stricture severe)) AND ((duodenal ulcer) OR (gastric ulcer)) AND ((ascites Uncontrolled) OR (hepatic encephalopathy)))"}
{"candidate_id": "LLM03054", "doc_id": "NCT02686021_exc", "case_bucket": "or", "source_criterion": "simultaneous both sided extraction or only upper third molar extraction general anesthesia known or presumed abnormal coagulation status known or presumed liver or renal dysfunction contraindication against metamizole known or suspected (known or suspected allergy against novalgin or other pyrazolones, anaphylactic reaction against NSAIDS, decreased bone marrow function or hematopoesis, hepatic porphyria, glucose-6-phosphate dehydrogenase deficiency, and pregnancy/breastfeeding) contraindication against ibuprofen (known or suspected allergy against ibuprofen, anaphylactic reaction against Nonsteroidal anti-inflammatory drugs (NSAID), active or recurrent stomach or duodenal ulcera or bleeding, severe liver or renal insufficiency, inflammatory bowel syndrome, and pregnancy/breastfeeding) pregnancy and breast feeding mothers", "candidate_expression": "((NSAIDS) AND (Nonsteroidal anti-inflammatory drugs (NSAID) active recurrent stomach) AND (abnormal coagulation status known presumed) AND (allergy) AND (allergy suspected) AND (anaphylactic reaction) AND (bleeding) AND (bone marrow function) AND (breast feeding) AND (breastfeeding) AND (contraindication) AND (general anesthesia known presumed) AND (glucose-6-phosphate dehydrogenase deficiency) AND (hematopoesis) AND (hepatic porphyria) AND (ibuprofen) AND (ibuprofen known suspected) AND (inflammatory bowel syndrome) AND (liver dysfunction) AND (metamizole known suspected known) AND (molar extraction simultaneous both sided only upper third) AND (novalgin) AND (pregnancy) AND (pyrazolones other) AND (renal dysfunction) AND (severe liver insufficiency) AND (severe renal insufficiency) AND (ulcera duodenal))"}
{"candidate_id": "LLM03055", "doc_id": "NCT02892968_inc", "case_bucket": "other", "source_criterion": "At the cluster level, ED physicians practicing at a participating site will be eligible. At the patient level, all hip fractures seen by a participating ED physician will be eligible", "candidate_expression": "(hip fracture)"}
{"candidate_id": "LLM03056", "doc_id": "NCT01932996_inc", "case_bucket": "other", "source_criterion": "Currently Homeless Smoked at least 100 cigarettes in lifetime AUDIT score of > or equal to 5, < or equal to 26 Aged 18 years or older Willing to attend study sessions and follow other study protocol", "candidate_expression": "((18 years or older) AND (AUDIT) AND (Aged) AND (Homeless) AND (Smoked) AND (Willing to attend study sessions and follow other study protocol) AND (at least 100 cigarettes) AND (score of > or equal to 5, < or equal to 26))"}
{"candidate_id": "LLM03057", "doc_id": "NCT02937779_inc", "case_bucket": "other", "source_criterion": ">= 18 years old the day of inclusion Pregnancy Positive HBs Ag Informed consent obtained with information sheet given and explained and the consent form signed by the participant of the project investigator at the latest the day of the inclusion", "candidate_expression": "((>= 18 years) AND (HBs Ag) AND (Informed consent obtained with information sheet given and explained and the consent form signed by the participant of the project investigator at the latest the day of the inclusio) AND (Positive) AND (Pregnancy) AND (old))"}
{"candidate_id": "LLM03058", "doc_id": "NCT02612181_exc", "case_bucket": "or", "source_criterion": "Age< 18 Pregnancy Bradycardia (HR<55bpm) Systolic Blood Pressure < 80 mmHg / Mean arterial pressure < 50 mmHg on maximal support Death imminent Unlikely to survive 90 days Acute liver failure Dementia High-grade block in the absence of a functioning pacemaker.", "candidate_expression": "((< 18) AND (< 50 mmHg) AND (< 80 mmHg) AND (<55bpm) AND (Acute liver failure) AND (Age) AND (Bradycardia) AND (Death) AND (Dementia) AND (HR) AND (High-grade block) AND (Mean arterial pressure) AND (Pregnancy) AND (Systolic Blood Pressure) AND (functioning) AND (imminent) AND (in the absence of) AND (on maximal support) AND (pacemaker) AND (support))"}
{"candidate_id": "LLM03059", "doc_id": "NCT03099408_exc", "case_bucket": "or", "source_criterion": "Presence of another vaginal infection or STD Allergy to metronidazole Pregnant or nursing Use of oral or intravaginal antibiotics within the past 2 weeks HIV or other chronic disease Inability to keep return appointments Contraindications for Lactobacillus Vaginal Suppositories(those without sexual history)", "candidate_expression": "((Allergy) AND (Contraindications) AND (HIV) AND (Inability to keep return appointments) AND (Lactobacillus Vaginal Suppositories) AND (Pregnant) AND (STD) AND (chronic disease other) AND (intravaginal antibiotics) AND (metronidazole) AND (nursing) AND (oral antibiotics) AND (vaginal infection) AND NOT (sexual history))"}
{"candidate_id": "LLM03060", "doc_id": "NCT03345589_exc", "case_bucket": "other", "source_criterion": "Autoimmune hepatitis Primary sclerosing cholangitis", "candidate_expression": "((Autoimmune hepatitis) AND (Primary sclerosing cholangitis))"}
{"candidate_id": "LLM03061", "doc_id": "NCT03639545_exc", "case_bucket": "or", "source_criterion": "diagnosed advanced heart, kidney or liver failure benign prostatic hyperplasia prostatic carcinoma frequent urinary tract infections non-type 1 diabetes mellitus", "candidate_expression": "((benign prostatic hyperplasia) AND (frequent) AND (non-type 1 diabetes mellitus) AND (prostatic carcinoma) AND (urinary tract infections) AND ((advanced heart failure) OR (kidney failure) OR (liver failure)))"}
{"candidate_id": "LLM03062", "doc_id": "NCT01803828_exc", "case_bucket": "or", "source_criterion": "congenital or valvular cardiomyopathy; ischemic heart disease; endocrine diseases: male hypogonadism, hyperthyroidism, adrenal diseases, pituitary diseases proliferative retinopathy or autonomic neuropathy; contraindications to sildenafil use or CMR imaging;", "candidate_expression": "((cardiomyopathy) AND (contraindications) AND (endocrine diseases) AND (ischemic heart disease) AND ((autonomic neuropathy) OR (proliferative retinopathy)) AND ((CMR imaging) OR (sildenafil)) AND ((congenital) OR (valvular)) AND ((adrenal diseases) OR (hyperthyroidism) OR (male hypogonadism) OR (pituitary diseases)))"}
{"candidate_id": "LLM03063", "doc_id": "NCT01943812_inc", "case_bucket": "or", "source_criterion": "Endometrial thickness = 7 mm after stimulation 18-45 years IVF/ICSI fertilisation BMI > 18,5 <30 kg/m2 cycle length 25-34 days", "candidate_expression": "((18-45) AND (25-34 days) AND (= 7 mm) AND (> 18,5 <30 kg/m2) AND (BMI) AND (Endometrial thickness) AND (ICSI fertilisation) AND (IVF fertilisation) AND (after stimulation) AND (cycle length) AND (stimulation) AND (years))"}
{"candidate_id": "LLM03064", "doc_id": "NCT01078051_exc", "case_bucket": "other", "source_criterion": "NA", "candidate_expression": "(EMPTY)"}
{"candidate_id": "LLM03065", "doc_id": "NCT02713087_exc", "case_bucket": "or", "source_criterion": "Age younger than 18 yrs. or older than 75 yrs. Pregnancy or nursing (negative pregnancy blood test) History of allergic reactions to phenylephrine or ephedrine eGFR < 60ml/min/1.73m2", "candidate_expression": "((Age younger than 18 yrs. or older than 75 yrs.) AND (Pregnancy) AND (allergic reactions History) AND (eGFR < 60ml/min/1.73m2) AND (ephedrine) AND (nursing) AND (phenylephrine) AND (pregnancy blood test negative))"}
{"candidate_id": "LLM03066", "doc_id": "NCT02884115_exc", "case_bucket": "other", "source_criterion": "Human immunodeficiency virus (HIV)-infected Baseline serology showed a nonreactive RPR test follow-up is inadequate Allergic to penicillin Pregnant woman", "candidate_expression": "((Allergic) AND (Human immunodeficiency virus (HIV)-infected) AND (Pregnant) AND (RPR test nonreactive) AND (follow-up is inadequate) AND (penicillin) AND (serology Baseline) AND (woman))"}
{"candidate_id": "LLM03067", "doc_id": "NCT02476461_inc", "case_bucket": "other", "source_criterion": "symptomatic Dupuytrens contracture with palpable cord, involving MCP, total contracture size over 30 degrees", "candidate_expression": "((Dupuytrens contracture) AND (involving MCP) AND (over 30 degrees) AND (palpable cord) AND (symptomatic) AND (total contracture size))"}
{"candidate_id": "LLM03068", "doc_id": "NCT02996916_exc", "case_bucket": "or", "source_criterion": "Secondary hypertension or malignant hypertension Diabetes mellitus History or evidence of a stroke Hepatic or hematologic abnormality Mild Cognitive Impairment or Dementia Serum potassium level = 5.5 mEq/L Serum creatinine level = 3.0 mg/dL Acute or chronic disease Allergy to any drugs Pregnancy", "candidate_expression": "((Acute disease) AND (Allergy) AND (Dementia) AND (Diabetes mellitus) AND (Hepatic abnormality) AND (History evidence) AND (Mild Cognitive Impairment) AND (Pregnancy) AND (Secondary hypertension) AND (Serum creatinine level = 3.0 mg/dL) AND (Serum potassium level = 5.5 mEq/L) AND (any drugs) AND (chronic disease) AND (hematologic abnormality) AND (malignant hypertension) AND (stroke))"}
{"candidate_id": "LLM03069", "doc_id": "NCT03318874_exc", "case_bucket": "or", "source_criterion": "Glaucoma, Ocular allergy Autoimmune disease Contact lens-wear during study Current punctal plugging Pregnant/lactating Candidate for topical anti-inflammatory Cicatricial meibomian gland dysfunction", "candidate_expression": "((Autoimmune disease) AND (Candidate for) AND (Cicatricial) AND (Contact lens-wear) AND (Current) AND (Glaucoma) AND (Ocular allergy) AND (Pregnant) AND (during study) AND (lactating) AND (meibomian gland dysfunction) AND (punctal plugging) AND (topical anti-inflammatory))"}
{"candidate_id": "LLM03070", "doc_id": "NCT00397215_exc", "case_bucket": "or", "source_criterion": "Administration of the licensed MF59-containing vaccines, e.g. Fluad™ or Addigrip™ or virosome-based influenza vaccines such as Inflexal V™, InfectoVac Flu™ or Invivac™ during the 2006-2007 influenza season. Administration of licensed vaccines within 2 weeks (for inactivated vaccines) or 4 weeks (for live vaccines) prior to enrolment in this study. Planned administration of a vaccine not foreseen by the study protocol up to 30 days after the second vaccination with H5N1 vaccine. Chronic administration (defined as more than 14 days) of immunosuppressants or other immune-modifying drugs within six months prior to the first administration of the study vaccine. Any confirmed or suspected immunosuppressive or immunodeficient condition, based on medical history and physical examination (no laboratory testing required). History of chronic alcohol consumption and/or drug abuse. History of hypersensitivity to vaccines. History of allergic disease or reactions likely to be exacerbated by any component of the vaccine (including egg and thiomersal allergy). Acute clinically significant pulmonary, cardiovascular, hepatic or renal functional abnormality, as determined by physical examination or laboratory screening tests. Acute disease at the time of enrolment. Serious chronic disease including any medically significant chronic pulmonary, cardiovascular, renal, neurological, psychiatric or metabolic disorder, as determined by medical history and physical examination. Administration of immunoglobulins and/or any blood products within the three months preceding the first vaccination or during the study. Use of any investigational or non-registered product (drug or vaccine) other than the study vaccine(s) within 30 days prior to the first vaccination, or planned use during the study period. Any condition which, in the opinion of the investigator, prevents the subject from participation in the study.", "candidate_expression": "((Acute disease) AND (Chronic) AND (H5N1 vaccine) AND (History) AND (Serious) AND (at the time of enrolment) AND (chronic disease) AND (condition) AND (during the 2006-2007 influenza season) AND (during the study period) AND (egg allergy) AND (first) AND (hypersensitivity to vaccines) AND (immunosuppressants) AND (licensed vaccines) AND (more than 14 days) AND (other immune-modifying drugs) AND (other than) AND (other than the study vaccine(s)) AND (planned) AND (product) AND (second) AND (study vaccine(s)) AND (the first vaccination) AND (the study) AND (thiomersal allergy) AND (up to 30 days) AND (use) AND (vaccination) AND (vaccine) AND (which prevents the subject from participation in the study) AND (within 2 weeks prior to enrolment in this study) AND (within 30 days prior to the first vaccination) AND (within 4 weeks prior to enrolment in this study) AND (within six months prior) AND ((MF59-containing vaccines) OR (virosome-based influenza vaccines)) AND ((inactivated vaccines) OR (live vaccines)) AND ((foreseen by the study protocol) OR (not)) AND ((Addigrip) OR (Fluad)) AND ((immunodeficient condition) OR (immunosuppressive condition)) AND ((confirmed) OR (suspected)) AND ((chronic alcohol consumption) OR (drug abuse)) AND ((allergic disease) OR (allergic reactions)) AND ((cardiovascular functional abnormality) OR (hepatic functional abnormality) OR (pulmonary functional abnormality) OR (renal functional abnormality)) AND ((chronic cardiovascular disorder) OR (chronic metabolic disorder) OR (chronic neurological disorder) OR (chronic psychiatric disorder) OR (chronic pulmonary disorder) OR (chronic renal disorder)) AND ((InfectoVac Flu) OR (Inflexal V) OR (Invivac)) AND ((any blood products) OR (immunoglobulins)) AND ((investigational) OR (non-registered)) AND ((drug) OR (vaccine)) AND ((during the study) OR (within the three months preceding the first vaccination)))"}
{"candidate_id": "LLM03071", "doc_id": "NCT01715714_exc", "case_bucket": "or", "source_criterion": "Any concomitant cardiovascular procedure to CABG (i.e. valve, aortic or carotid surgery) Acute ST-segment-elevation myocardial infarction (STEMI) NSTE-ACS with cardiogenic shock warranting emergent salvage surgery within 12 hrs from hospital admission History of atrial fibrillation or muscle disease (myopathy) Current renal (creatinine>2x upper limit of normal (ULN), dialysis, kidney transplant) or hepatic dysfunction (AST/ALT>2x ULN, liver transplant or neoplasm) Inability of oral drug intake", "candidate_expression": "((>2x ULN) AND (>2x upper limit of normal (ULN)) AND (Acute ST-segment-elevation myocardial infarction) AND (CABG) AND (Inability) AND (Inability of) AND (NSTE-ACS) AND (STEMI) AND (cardiogenic shock) AND (cardiovascular procedure) AND (concomitant) AND (hospital admission) AND (myopathy) AND (oral drug) AND (oral drug intake) AND (salvage surgery) AND (warranting) AND (within 12 hrs from hospital admission) AND ((atrial fibrillation) OR (muscle disease)) AND ((creatinine) OR (dialysis) OR (kidney transplant)) AND ((hepatic dysfunction) OR (renal dysfunction)) AND ((ALT) OR (AST)) AND ((liver transplant) OR (neoplasm)) AND ((aortic surgery) OR (carotid surgery) OR (valve surgery)))"}
{"candidate_id": "LLM03072", "doc_id": "NCT02985242_exc", "case_bucket": "or", "source_criterion": "Type 1 diabetes uncontrolled diabetes mellitus type 2 with fasting glucose > 13.3 mmol/l confirmed on a second day known or suspected hypersensitivity to empagliflozin, glimepiride, or any excipients; and / or known or suspected hypersensitivity to sulfonylureas, sulfonamides or SGLT2 inhibitors in general history of multiple severe hypoglycemic episodes within the last two years use of Insulin, SGLT2-inhibitor, sulfonylurea derivate or a glinide within past 3 months clinical significant macular edema in both eyes and indication for intravitreal anti-VEGF treatment for both eyes at screening or baseline visit. Eyes with a small amount of intraretinal or subretinal fluid (seen in OCT) but no need for intravitreal treatment as judged by the investigator (according to current practice patterns) may be included. Eyes with a history of intravitreal treatment of macular edema which do not need ongoing intravitreal treatment at the time of screening may be included. eye diseases or pathologies that prevent clear ophthalmoscopy and evaluation of study parameters, thus not allowing study participation according to the investigator´s judgment, such as (but not only) vitreous hemorrhage, mature cataract, macular pathologies other than diabetic maculopathy history of ketoacidosis or metabolic acidosis use of loop diuretics history of > 1 urogenital infection/year any history of stroke, transient ischemic attack (TIA), instable angina pectoris or myocardial infarction within last 3 months prior to baseline visit congestive heart failure New York Heart Association (NYHA) III and IV severe valvular or left ventricular outflow obstruction disease needing intervention; atrial fibrillation/flutter with a mean ventricular response rate at rest >100 beats per minute chronic lower urinary tract infections (but not simple asymptomatic bacteriuria) eGFR < 60 ml/min/1,73 m2 (MDRD-formula, confirmed on a second day) chronic diarrhea, any clinical signs of volume depletion or a hematocrit > 48 % (women) and > 53 % (men) elevated risk for volume depletion, e.g. history of severe volume depletion that required medical therapy chronic liver disease (including known active hepatitis) and/or screening alanine transaminase (ALT) or aspartate transaminase (AST) > 3 x upper limit of normal (ULN) (confirmed on a second day) Subjects with known seropositivity to human immunodeficiency virus. acute illness at screening or randomization according to judgement by the investigator or patient drug or alcohol abuse psychosomatic or psychiatric diseases requiring hospitalization during the last 12 months clinical evidence of current malignancy with exception of basal cell or squamous cell carcinoma of the skin, and cervical intraepithelial neoplasia (5 years prior to randomization) any medical or surgical intervention planned for the next 13 months after randomization not allowing study participation according to the investigator´s judgment current participation in any other clinical trial or participation in another clinical trial within 30 days before screening", "candidate_expression": "((5 years prior to randomization) AND (< 60 ml/min/1,73 m2) AND (> 1 /year) AND (> 13.3 mmol/l) AND (> 3 x upper limit of normal) AND (> 48 %) AND (> 53 %) AND (>100 beats per minute) AND (ALT) AND (AST) AND (III and IV) AND (Insulin) AND (NYHA) AND (New York Heart Association) AND (SGLT2 inhibitors) AND (SGLT2-inhibitor) AND (TIA) AND (Type 1 diabetes) AND (active hepatitis) AND (alanine transaminase) AND (alcohol abuse) AND (angina pectoris) AND (aspartate transaminase) AND (asymptomatic bacteriuria) AND (at rest) AND (atrial fibrillation) AND (atrial flutter) AND (basal cell carcinoma of the skin) AND (baseline visit) AND (both eyes) AND (cervical intraepithelial neoplasia) AND (chronic) AND (chronic diarrhea) AND (chronic liver disease) AND (congestive heart failure) AND (current participation in any other clinical trial or participation in another clinical trial within 30 days before screening) AND (diabetes mellitus type 2) AND (diabetic maculopathy) AND (drug abuse) AND (eGFR) AND (elevated) AND (empagliflozin) AND (exception) AND (fasting glucose) AND (glimepiride) AND (glinide) AND (hematocrit) AND (hospitalization) AND (human immunodeficiency virus) AND (hypersensitivity) AND (hypoglycemic episodes) AND (instable) AND (intervention) AND (intravitreal anti-VEGF treatment) AND (ketoacidosis) AND (last 12 months) AND (last 3 months prior to baseline visit) AND (last two years) AND (left ventricular outflow obstruction) AND (loop diuretics) AND (lower urinary tract infections) AND (macular edema) AND (macular pathologies) AND (malignancy) AND (mature cataract) AND (mean ventricular response rate) AND (men) AND (metabolic acidosis) AND (multiple) AND (myocardial infarction) AND (not) AND (ophthalmoscopy) AND (other) AND (past 3 months) AND (prevent) AND (psychiatric diseases) AND (psychosomatic diseases) AND (randomization) AND (risk for volume depletion,) AND (seropositivity) AND (severe) AND (squamous cell carcinoma of the skin) AND (stroke) AND (sulfonamides) AND (sulfonylurea derivate) AND (sulfonylureas) AND (transient ischemic attack) AND (uncontrolled) AND (urogenital infection) AND (valvular disease) AND (vitreous hemorrhage) AND (volume depletion) AND (women))"}
{"candidate_id": "LLM03073", "doc_id": "NCT03134378_exc", "case_bucket": "or", "source_criterion": "Patients refuse to follow the research Patient has had previous eradication therapy of Helicobacter pylori infection. The patient is pregnant or breastfeeding Patients have a history of allergy to one component of triple therapy regimen (proton pump inhibitor, penicillin, and / or macrolide) before. Patients are known to have impaired liver function, evidenced by ALT values within normal limits, and no previous liver disease. Patients were found to have arrhythmias or obtained QT wave elongation on electrocardiographic", "candidate_expression": "((ALT values within normal limits) AND (Helicobacter pylori infection) AND (QT wave elongation) AND (allergy history) AND (component of triple therapy regimen) AND (eradication therapy previous) AND (liver function impaired) AND (refuse to follow the research) AND NOT (liver disease previous) AND ((macrolide) OR (penicillin) OR (proton pump inhibitor)) AND ((arrhythmias) OR (electrocardiographic)) AND ((breastfeeding) OR (pregnant)))"}
{"candidate_id": "LLM03074", "doc_id": "NCT01908465_exc", "case_bucket": "or", "source_criterion": "IBS subtype with constipation medication: antidepressants or H1-receptor antagonists pregnancy, breast feeding co-morbidity: severe kidney- and/or liver disease or other gastrointestinal diseases", "candidate_expression": "((H1-receptor antagonists) AND (IBS subtype) AND (antidepressants) AND (breast feeding) AND (constipation) AND (gastrointestinal diseases) AND (kidney disease) AND (liver disease) AND (pregnancy))"}
{"candidate_id": "LLM03075", "doc_id": "NCT00182520_exc", "case_bucket": "or", "source_criterion": "Any other primary DSM-IV diagnosis; DSM-IV criteria for body dysmorphic disorder, bipolar affective disorder, schizophrenia, psychotic disorder, current alcohol/substance abuse. A previous adequate trial of topiramate Comorbid major depressive disorder diagnosis which predates OCD diagnosis Cognitive behavioural therapy or additional psychotherapy in past four months Allergy or hypersensitivity to topiramate BMI < 20 History of kidney stones", "candidate_expression": "((< 20) AND (Allergy) AND (BMI) AND (Cognitive behavioural therapy) AND (Comorbid) AND (DSM-IV) AND (DSM-IV criteria) AND (History of) AND (OCD diagnosis) AND (additional) AND (alcohol abuse) AND (bipolar affective disorder) AND (body dysmorphic disorder) AND (diagnosis) AND (hypersensitivity) AND (in past four months) AND (kidney stones) AND (major depressive disorder) AND (predates OCD diagnosis) AND (previous) AND (primary) AND (psychotherapy) AND (psychotic disorder,) AND (schizophrenia) AND (substance abuse) AND (topiramate))"}
```
