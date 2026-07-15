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
{"candidate_id": "LLM00201", "doc_id": "NCT02985710_inc", "case_bucket": "or", "source_criterion": "Males and females with confirmed disease: Fabry (by GLA enzymes and/or DNA testing) naïve and on ERT, Mitochondrial diseases (electron transport chain and/or DNA testing) or connective tissue diseases (clinical criteria and/or DNA testing when available) Consenting adults (18 years and older) who agrees and consents to skin biopsy and QSART procedure", "candidate_expression": "((Consenting adults (18 years and older) who agrees and consents to skin biopsy and QSART procedure) AND (DNA testing) AND (ERT) AND (Fabry naïve) AND (GLA enzymes) AND (Males) AND (Mitochondrial diseases) AND (clinical criteria) AND (confirmed disease) AND (connective tissue diseases) AND (electron transport chain) AND (females))"}
{"candidate_id": "LLM00202", "doc_id": "NCT03019562_exc", "case_bucket": "or", "source_criterion": "Allergic to study drugs Patient with asthma or COPD, patient who is severely respiratory depressed Renal of hepatic insufficiency Epileptic status Intracranial lesion associated with increased intracranial pressure Acute abdomen, patient who has diagnosed paralytic ileus or suspicious ileus Pregnant or lactating women", "candidate_expression": "((Acute abdomen) AND (Allergic) AND (COPD) AND (Epileptic status) AND (Intracranial lesion) AND (Pregnant) AND (Renal insufficiency) AND (asthma) AND (hepatic insufficiency) AND (increased) AND (intracranial pressure) AND (lactating) AND (paralytic ileus) AND (respiratory depressed) AND (severely) AND (study drugs) AND (suspicious ileus) AND (wome))"}
{"candidate_id": "LLM00203", "doc_id": "NCT02321202_inc", "case_bucket": "other", "source_criterion": "The cirrhotic malnourished patients who were diagnosed as liver cancer preoperatively and underwent hepatectomy were consecutively enrolled.", "candidate_expression": "((cirrhotic) AND (hepatectomy) AND (liver cancer preoperatively) AND (malnourished))"}
{"candidate_id": "LLM00204", "doc_id": "NCT02137538_exc", "case_bucket": "other", "source_criterion": "Bone age reading more than 14.0 years Follicle stimulating hormone > 20 IU/L", "candidate_expression": "((Bone age more than 14.0 years) AND (Follicle stimulating hormone > 20 IU/L))"}
{"candidate_id": "LLM00205", "doc_id": "NCT02595190_exc", "case_bucket": "or", "source_criterion": "1. Patients with lumbar common diseases(e.g., Lumbar disc, Lumbar spinal stenosis, Lumbar slippage, etc) 2. Researchers think that Patients with disease may be interference results(e.g., Spinal deformity, spine fracture, ankylosing spondylitis, spinal tuberculosis and spinal infection, spinal tumor, pelvic inflammatory disease and other disease of department of gynaecology, etc) 3. Patients with other nervous system diseases(e.g., cerebral tumor, neurinoma, trigeminal neuralgia,etc) 4. Patients with Magnetic resonance imaging contraindication ,including claustrophobic syndrome patients 5. Patients with recent (less than 3 years) use chemical drugs or have obvious psychological problems 6. In the past 2 months involved in other drugs or devices clinical trials", "candidate_expression": "((In the past 2 months involved in other drugs or devices clinical trials) AND (Lumbar disc) AND (Lumbar slippage) AND (Lumbar spinal stenosis) AND (Magnetic resonance imaging) AND (Spinal deformity) AND (ankylosing spondylitis) AND (cerebral tumor) AND (claustrophobic syndrome) AND (contraindication) AND (lumbar diseases) AND (nervous system diseases) AND (neurinoma) AND (pelvic inflammatory disease) AND (spinal infection) AND (spinal tuberculosis) AND (spinal tumor) AND (spine fracture,) AND (trigeminal neuralgia))"}
{"candidate_id": "LLM00206", "doc_id": "NCT02312076_inc", "case_bucket": "other", "source_criterion": "Women subjected to ICSI through controlled ovarian hyperstimulation (COH) with pituitary downregulation by GnRHa.", "candidate_expression": "((ICSI) AND (Women) AND (controlled ovarian hyperstimulation (COH)) AND (pituitary downregulation by GnRHa))"}
{"candidate_id": "LLM00207", "doc_id": "NCT02186782_exc", "case_bucket": "or", "source_criterion": "Age < 20 or > 35 years. Body mass index (BMI) < 18.5 kg/m2 or > 25 kg/m2. Presence of any infertility factor other than anovulation/oligoovulation. Previous history of ovarian surgery or surgical removal of one ovary. Previous exposure to cytotoxic drugs or pelvic irradiation. Metabolic or hormonal abnormalities.", "candidate_expression": "((Age < 20 > 35 years) AND (BMI < 18.5 kg/m2 > 25 kg/m2) AND (Body mass index) AND (Metabolic abnormalities) AND (anovulation) AND (cytotoxic drugs) AND (hormonal abnormalities) AND (infertility factor) AND (oligoovulation) AND (ovarian surgery) AND (pelvic irradiation) AND (surgical removal ovary))"}
{"candidate_id": "LLM00208", "doc_id": "NCT01630954_inc", "case_bucket": "other", "source_criterion": "Ultrasound confirmed complete mole", "candidate_expression": "((Ultrasound) AND (complete mole))"}
{"candidate_id": "LLM00209", "doc_id": "NCT02589691_inc", "case_bucket": "other", "source_criterion": "age <2 years indication of general anesthesia with tracheal intubation inhalational induction scheduled written informed consent of both parents", "candidate_expression": "((<2 years) AND (age) AND (general anesthesia) AND (indication) AND (inhalational induction) AND (scheduled) AND (tracheal intubation) AND (written informed consent of both parents))"}
{"candidate_id": "LLM00210", "doc_id": "NCT02550080_exc", "case_bucket": "or", "source_criterion": "Has previously received Dapsone therapy. The subject or any of their healthcare providers is aware of the subjects HLA type. Has been diagnosed with Glucose-6-phosphate dehydrogenase deficiency or methemoglobin reductase deficiency Satisfies any contraindications or restrictions to Dapsone therapy as listed in the product labels. Current severe illness, including heart, liver and renal failure, major organ allograft, malignancy requiring parenteral chemotherapy that can not be discontinued for the duration of the trial, or any other conditions which, in the opinion of the Investigator, would make the patient unsuitable for the study. Any laboratory abnormality at Screening which, in the opinion of the Investigator, should preclude the subject's participation in the study [alanine aminotransferase (ALT), glutamic oxaloacetic transaminase(ALT), et al). Pregnant women or women who are breastfeeding. Subject is, in the opinion of the Investigator, unable to complete the 6 week Observation period and the EPT assessments as required. A positive result for HLA-B*1301 in those subjects randomised to the genetic screening arm.", "candidate_expression": "((Dapsone) AND (HLA-B*1301 positive) AND (chemotherapy) AND (contraindications) AND (regnant women or women who are breastfeeding) AND ((Glucose-6-phosphate dehydrogenase deficiency) OR (methemoglobin reductase deficiency)) AND ((heart failure) OR (liver failure) OR (major organ allograft) OR (malignancy) OR (renal failure)))"}
{"candidate_id": "LLM00211", "doc_id": "NCT02537899_inc", "case_bucket": "or", "source_criterion": "Male or female Age 18 to 65 years Diagnosed with spinal cord injury between 3 days and 4 weeks American Spinal Injury Association Impairment Scale A or B Informed consent for inclusion into the database is obtained", "candidate_expression": "((18 to 65 years) AND (A or B) AND (Age) AND (American Spinal Injury Association Impairment Scale) AND (Informed consent for inclusion into the database is obtained) AND (Male) AND (between 3 days and 4 weeks) AND (female) AND (spinal cord injury))"}
{"candidate_id": "LLM00212", "doc_id": "NCT03413891_exc", "case_bucket": "other", "source_criterion": "Subjects with any condition that as judged by the Investigator would place the subject at increased risk of harm if he/she participated in the study. Pregnancy or lactation Known allergic reaction to tranexamic acid", "candidate_expression": "((Pregnancy or lactation) AND (allergic) AND (tranexamic acid))"}
{"candidate_id": "LLM00213", "doc_id": "NCT02902120_inc", "case_bucket": "or", "source_criterion": "At least 18 years of age at the time of screening Have stable renal function for one month (30 days) prior to enrollment Have Chronic HCV infection prior to transplantation with documented HCV viremia = 1,000 IU/ml at screening and either documented HCV Ab positivity or HCV viremia = 1,000 IU/ml at least 6 months prior to enrollment. Documented genotype 1 HCV infection prior to enrollment and after their transplant in the post-transplantation cohort HCV disease staging within 12 months prior to enrollment by liver biopsy, transient elastography, or biochemical testing Be able to give informed consent and comply with study guidelines Women of childbearing age will be required to have a negative pregnancy test at enrollment and use birth control throughout the duration of treatment. On the transplant waiting list followed by the University of Maryland's nephrology clinic or the Baltimore VA's nephrology clinic On chronic hemodialysis not yet on the transplant list and followed in the University's hemodialysis center or in the University's nephrology clinic Have chronic kidney disease with GFR <50", "candidate_expression": "((<50) AND (= 1,000 IU/ml) AND (At least 18 years) AND (Be able to give informed consent and comply with study guidelines) AND (Chronic HCV infection) AND (GFR) AND (HCV) AND (HCV infection) AND (HCV viremia) AND (Women of childbearing age will be required to have a negative pregnancy test at enrollment and use birth control throughout the duration of treatment.) AND (after their transplant i) AND (age) AND (at least 6 months prior to enrollment.) AND (chronic) AND (chronic kidney disease) AND (disease staging) AND (enrollment) AND (genotype 1) AND (hemodialysis) AND (one month (30 days) prior to enrollment) AND (positivity) AND (prior to enrollment) AND (prior to transplantation) AND (renal function) AND (stable) AND (transplant) AND (transplantation) AND (within 12 months prior to enrollment) AND ((HCV Ab) OR (HCV viremia)) AND ((biochemical testing) OR (liver biopsy) OR (transient elastography)))"}
{"candidate_id": "LLM00214", "doc_id": "NCT03363295_inc", "case_bucket": "other", "source_criterion": "Any patients that will be submitted to phacoemulsification surgery in the Hospital de Clinicas of State University of Campinas (BRAZIL) Patients over 18 years old Patients who are able to perform SD-OCT Patients who sign the consent form", "candidate_expression": "((Hospital de Clinicas of State University of Campinas (BRAZIL)) AND (Patients who sign the consent form) AND (SD-OCT) AND (able to perform) AND (old) AND (over 18 years) AND (phacoemulsification surgery) AND (will be submitted to))"}
{"candidate_id": "LLM00215", "doc_id": "NCT02281643_inc", "case_bucket": "other", "source_criterion": "M. perstans mg-positive status Good general health without any clinical condition requiring long-term medication. Normal renal and hepatic laboratory profiles", "candidate_expression": "((Good general health) AND (M. perstans mg) AND (Normal) AND (clinical condition requiring long-term medication) AND (hepatic laboratory profile) AND (long-term medication) AND (positive) AND (renal laboratory profile) AND (requiring long-term medication) AND (without))"}
{"candidate_id": "LLM00216", "doc_id": "NCT02935855_inc", "case_bucket": "or", "source_criterion": "non-valvular atrial fibrillation nondiabetic patients type 1 and 2 diabetic patients", "candidate_expression": "((atrial fibrillation non-valvular) AND (diabetic) AND NOT (diabetic type 1 type 2))"}
{"candidate_id": "LLM00217", "doc_id": "NCT03561753_inc", "case_bucket": "or", "source_criterion": "Newly diagnosed and untreated sputum smear positive tuberculosis patient Pulmonary lesion consistent with TB by radiological examination Positive sputum culture, identification of bacterial type confirmed Mycobacterium tuberculosis. MGIT drug sensitivity test (DST) results are sensitive of the first-line drugs (isoniazid, streptomycin, rifampicin and ethambutol). Age 18 years-65 years old Males or non-pregnant, non-nursing females Serum or plasma aminotransferases (AST, ALT) less than 3 times the upper limit of normal Serum or plasma total bilirubin less than or equal to 2.5 times the upper limit of normal Serum or plasma creatinine level less than or equal to 2 times the upper limit of normal Serum or plasma potassium level greater than or equal to 3.5 meq/L Hemoglobin level of 7.0 g/dL or greater Platelet count of 100,000/mm3 or greater For women of childbearing potential, a negative pregnancy test is required during screening Provides written informed consent Willingness and ability to attend scheduled follow-up visits and undergo study assessments.", "candidate_expression": "((100,000/mm3 or greater) AND (18 years-65 years old) AND (7.0 g/dL or greater) AND (Age) AND (Hemoglobin level) AND (MGIT drug sensitivity test (DST)) AND (Males) AND (Mycobacterium tuberculosis) AND (Platelet count) AND (Positive) AND (Pulmonary lesion) AND (TB) AND (ability to attend scheduled follow-up visits) AND (ability to undergo study assessments) AND (bacterial type) AND (childbearing potential) AND (consistent with TB) AND (creatinine level) AND (during screening) AND (females) AND (first-line drugs) AND (greater than or equal to 3.5 meq/L) AND (less than 3 times the upper limit of normal) AND (less than or equal to 2 times the upper limit of normal) AND (less than or equal to 2.5 times the upper limit of normal) AND (negative) AND (non-) AND (nursing) AND (positive) AND (potassium level) AND (pregnancy test) AND (pregnant) AND (radiological examination) AND (screening) AND (sensitive of the first-line drugs (isoniazid, streptomycin, rifampicin and ethambutol)) AND (sputum culture) AND (sputum smear) AND (to attend scheduled follow-up visits Willingness) AND (to undergo study assessments Willingness) AND (total bilirubin) AND (tuberculosis) AND (women) AND (written informed consent) AND ((Newly diagnosed) OR (untreated)) AND ((ethambutol) OR (isoniazid) OR (rifampicin) OR (streptomycin)) AND ((ALT) OR (AST)) AND ((Serum aminotransferases) OR (plasma aminotransferases)) AND ((Serum) OR (plasma)))"}
{"candidate_id": "LLM00218", "doc_id": "NCT02298504_exc", "case_bucket": "or", "source_criterion": "Teeth with clinical symptoms of irriversible pulpitis or pulp necrosis or acute dental infection Children with systemic illness that contraindicated vital pulp treatment such a sickle cell disease Teeth that are not restorable", "candidate_expression": "((Teeth) AND (Teeth that are not restorable) AND (contraindicated) AND (sickle cell disease) AND (systemic illness) AND (vital pulp treatment) AND ((acute dental infection) OR (irriversible pulpitis) OR (pulp necrosis)))"}
{"candidate_id": "LLM00219", "doc_id": "NCT02251249_inc", "case_bucket": "or", "source_criterion": "Patient over 18 years weighing between 65 and 85 Kg Referred for STEMI within 6 hours from beginning of chest pain or stable coronary artery disease requiring a loading dose of Prasugrel or Ticagrelor according to the international recommendations. No previous treatment with Clopidogrel, Prasugrel or Ticagrelor. Patient fasting for at least 6 hours. Affiliate or receiving a social security system. Written informed consent.", "candidate_expression": "((Clopidogrel) AND (No) AND (Prasugrel) AND (STEMI) AND (Ticagrelor) AND (Written informed consent) AND (beginning of chest pain) AND (between 65 and 85 Kg) AND (chest pain) AND (coronary artery disease) AND (fasting) AND (for at least 6 hours.) AND (loading dose) AND (over 18) AND (previous) AND (stable) AND (treatment) AND (weighing) AND (within 6 hours from beginning of chest pain) AND (years))"}
{"candidate_id": "LLM00220", "doc_id": "NCT01967420_inc", "case_bucket": "or", "source_criterion": "Non-affective psychosis Premorbid IQ of over 70 A service user of the early intervention service Aged 18 or over (up to the age of 35 which is the limit for the early intervention service) Psychiatrically stable enough to attend to completion (no hospitalisations or medication changes in last 4 weeks)", "candidate_expression": "((18 or over) AND (Aged) AND (Non-affective psychosis) AND (Premorbid IQ) AND (Psychiatrically stable) AND (hospitalisations) AND (in last 4 weeks) AND (medication changes) AND (no) AND (over 70) AND (up to the age of 35))"}
{"candidate_id": "LLM00221", "doc_id": "NCT03151603_exc", "case_bucket": "or", "source_criterion": "signs of complicated UTI (e. g. temperature > 38°C, loin tenderness) conditions that may lead to complicated infections (i.e. renal diseases, patients with urinary catheter) pregnancy/ breastfeeding current self-medication with UU preparations e.g. z.B. Cystinol®, Uvalysat®, Arctuvan® antibiotic use in the last 7 days previous UTI in the past 2 weeks history of pyelonephritis contraindications for trial drugs serious diseases inability to understand trial Information current participation in another clinical trial or participation in another clinical trial within the last 4 weeks", "candidate_expression": "((UTI past 2 weeks) AND (UU preparations self-medication) AND (antibiotic last 7 days) AND (complicated UTI) AND (complicated infections) AND (conditions) AND (diseases serious) AND (drugs contraindications for trial) AND (inability to understand trial Information) AND (pregnancy/ breastfeeding) AND (pyelonephritis) AND (urinary catheter) AND ((patients) OR (renal diseases)) AND ((Arctuvan®) OR (Uvalysat®) OR (z.B. Cystinol®)) AND ((loin tenderness) OR (temperature > 38°C)))"}
{"candidate_id": "LLM00222", "doc_id": "NCT02117986_exc", "case_bucket": "or", "source_criterion": "pregnant or breastfeeding patients patient with a history of hypersensitivity to colistin", "candidate_expression": "((colistin) AND (history of) AND (hypersensitivity) AND ((breastfeeding) OR (pregnant)))"}
{"candidate_id": "LLM00223", "doc_id": "NCT03471117_exc", "case_bucket": "or", "source_criterion": "Allergy to Glitazones Myocardial infarction Heart failure Angina History of kidney stones Liver disease (abnormal liver enzymes) Anemia (hemoglobin <8 g/dl) Cancer with current treatment Previous organ transplantation Immunosuppressant therapy Human immunodeficiency virus infection Pregnancy or lactating Current tobacco use Dilantin and oral contraceptive usage due to potential drug interaction with glitazones Self-identified history of hypoglycemia", "candidate_expression": "((Allergy) AND (Anemia) AND (Angina) AND (Cancer) AND (Glitazones) AND (Heart failure) AND (Human immunodeficiency virus infection) AND (Immunosuppressant therapy) AND (Liver disease) AND (Myocardial infarction) AND (drug interaction potential) AND (glitazones) AND (hemoglobin <8 g/dl) AND (hypoglycemia Self-identified history) AND (kidney stones History) AND (liver enzymes abnormal) AND (organ transplantation Previous) AND (tobacco use Current) AND (treatment current) AND ((Pregnancy) OR (lactating)) AND ((Dilantin) OR (oral contraceptive)))"}
{"candidate_id": "LLM00224", "doc_id": "NCT03019562_exc", "case_bucket": "or", "source_criterion": "Allergic to study drugs Patient with asthma or COPD, patient who is severely respiratory depressed Renal of hepatic insufficiency Epileptic status Intracranial lesion associated with increased intracranial pressure Acute abdomen, patient who has diagnosed paralytic ileus or suspicious ileus Pregnant or lactating women", "candidate_expression": "((Allergic) AND (Epileptic status) AND (Intracranial lesion) AND (Renal insufficiency) AND (hepatic insufficiency) AND (increased) AND (intracranial pressure) AND (severely) AND (study drugs) AND (wome) AND ((Acute abdomen) OR (paralytic ileus) OR (suspicious ileus)) AND ((Pregnant) OR (lactating)) AND ((COPD) OR (asthma) OR (respiratory depressed)))"}
{"candidate_id": "LLM00225", "doc_id": "NCT03123562_exc", "case_bucket": "or", "source_criterion": "Epilepsy Hydrocephalus with ventricular drain Coagulation disorders Allergy to anesthetic agents Severe health conditions such as cancer, failure of heart, lung, liver or kidney Active infections", "candidate_expression": "((Allergy) AND (Coagulation disorders) AND (Epilepsy) AND (Hydrocephalus) AND (Severe health conditions) AND (anesthetic agents) AND (infections Active) AND (ventricular drain) AND ((cancer) OR (failure of heart) OR (failure of kidney) OR (failure of liver) OR (failure of lung)))"}
```
