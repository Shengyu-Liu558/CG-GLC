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
{"candidate_id": "LLM07251", "doc_id": "NCT01446094_inc", "case_bucket": "other", "source_criterion": "Aged 18 years or older Scheduled for invasive coronary angiography", "candidate_expression": "((Aged 18 years or older) AND (invasive coronary angiography Scheduled))"}
{"candidate_id": "LLM07252", "doc_id": "NCT00183885_inc", "case_bucket": "other", "source_criterion": "Unresectable, histologically confirmed hepatocellular carcinoma with evident disease limited to liver. Tissue from tumor must be available. This may be paraffin embedded tissue from previous biopsy/resection or if it is not available, a repeat biopsy must be performed. The requirement for biopsy may be waived if alpha-fetoprotein is greater than 500 ng/mL and in the investigators opinion not explained by a concurrent hepatic inflammatory process. Patients must agree to have a 20 cc blood sample drawn in addition to routine labs with each cycle of chemotherapy. Patients must have measurable disease. If prior radiation therapy was administered, measurable disease must be outside the radiation field. Patients must have a Zubrod performance status of 0-2. Patients must have a predicted life expectancy of at least 12 weeks. Patients must have a pre-treatment granulocyte count (i.e., segmented neutrophils + bands) of greater than or equal to 1,500/mm3, a hemoglobin level of greater than or equal to 9 gm/dl, and platelet count greater than or equal to 50,000/mm3. The granulocyte requirement may be waived if in the investigator's opinion the lower count reflects hypersplenism with adequate bone marrow reserves. Patients must have adequate renal function as documented by a calculated creatinine clearance ≥ 60. Patients must have adequate hepatic function as documented by a serum bilirubin less than or equal to 2x the institutional upper limit of normal, regardless of whether patients have liver involvement secondary to tumor. Patients may not have ascites or the ascites must be responsive to diuretics.", "candidate_expression": "((0-2) AND (20 cc) AND (Unresectable) AND (Zubrod performance status) AND (adequate) AND (agree to) AND (alpha-fetoprotein) AND (ascites) AND (at least 12 weeks) AND (biopsy) AND (blood sample drawn) AND (calculated creatinine clearance) AND (confirmed) AND (disease limited to liver) AND (granulocyte count) AND (greater than 500 ng/mL) AND (greater than or equal to 1,500/mm3) AND (greater than or equal to 50,000/mm3) AND (greater than or equal to 9 gm/dl) AND (hemoglobin level) AND (hepatic function) AND (hepatocellular carcinoma) AND (histologically) AND (less than or equal to 2x the institutional upper limit of normal) AND (may not have) AND (measurable disease) AND (outside the radiation field) AND (platelet count) AND (pre-treatment) AND (predicted life expectancy) AND (radiation therapy) AND (renal function) AND (responsive to diuretics) AND (routine labs) AND (segmented neutrophils + bands) AND (serum bilirubin) AND (with each cycle of chemotherapy) AND (≥ 60))"}
{"candidate_id": "LLM07253", "doc_id": "NCT02022709_inc", "case_bucket": "or", "source_criterion": "Having been diagnosed with primary OCD as defined by the Diagnostic and Statistical Manual of Mental Disorders (DSM-IV-) criteria;Cleaning or checking as primary OCD symptoms Yale-Brown Obsessive-Compulsive Scale (Y-BOCS) score of = 16 Never receiving adequate treatment or stop receiving treatment for at least 8 weeks Having an education degree of high school or above Accepting to participate in the study", "candidate_expression": "((DSM-IV) AND (Diagnostic and Statistical Manual of Mental Disorders) AND (Never) AND (Y-BOCS) AND (Yale-Brown Obsessive-Compulsive Scale) AND (adequate) AND (ccepting to participate in the study) AND (degree of high school) AND (for at least 8 weeks) AND (primary OCD) AND (score of = 16) AND (stop) AND ((treatment)))"}
{"candidate_id": "LLM07254", "doc_id": "NCT02678962_inc", "case_bucket": "other", "source_criterion": "Age from 40 to 80 years old, either gender; Patients with bilateral age related cataracts, require bilateral cataract phacoemulsification combined Intraocular Lens implantation; Willing to undergo second eye surgery within 7 days after first eye surgery; The potential postoperative visual acuity of 20/40 or better in both eyes; Preoperative measurement of corneal astigmatism indicate the subjects are suitable for multifocal intraocular lenses implantation; Capability to understand the informed consent and willing and able to attend study", "candidate_expression": "((Age) AND (Capability to understand the informed consent and willing and able to attend study) AND (Intraocular Lens implantation) AND (Preoperative) AND (age related) AND (bilateral) AND (cataract phacoemulsification) AND (cataracts) AND (from 40 to 80 years old) AND (measurement of corneal astigmatism) AND (multifocal intraocular lenses implantation) AND (suitable))"}
{"candidate_id": "LLM07255", "doc_id": "NCT03472846_exc", "case_bucket": "or", "source_criterion": "Diabetes mellitus type 1 renal insufficiency III-V ° Cirrhosis hepatis (Child B or higher) Chronic alcohol abuse rheumatic disease (RA, SpA, SLE) Malignancies (<5 years) Eating Disorder (anorexia nervosa, bulimia) bone-specific pretreatment (DMAB, TPTD, strontium ranelate, SERMs) Bisphosphonate treatment is allowed", "candidate_expression": "((Child B or higher) AND (Cirrhosis hepatis Child B or higher) AND (DMAB) AND (Diabetes mellitus type 1) AND (Eating Disorder) AND (Malignancies <5 years) AND (RA) AND (SERMs) AND (SLE) AND (SpA) AND (TPTD) AND (alcohol abuse Chronic) AND (anorexia nervosa) AND (bone-specific pretreatment) AND (bulimia) AND (renal insufficiency III-V °) AND (rheumatic disease) AND (strontium ranelate))"}
{"candidate_id": "LLM07256", "doc_id": "NCT01980680_inc", "case_bucket": "or", "source_criterion": "Age between 20 and 40 Normal menstrual cycles: 25-34 days Oligomenorrhea/amenorrhea or polycystic syndrome (defined according to the Rotterdam criteria 2004) BMI >18 and <35 kg/m2", "candidate_expression": "((25-34 days) AND (>18 and <35 kg/m2) AND (Age) AND (BMI) AND (Normal menstrual cycles) AND (Rotterdam criteria 2004) AND (between 20 and 40) AND ((Oligomenorrhea) OR (amenorrhea) OR (polycystic syndrome)))"}
{"candidate_id": "LLM07257", "doc_id": "NCT03519568_exc", "case_bucket": "or", "source_criterion": "the history or family history of anaphylaxis, convulsion, epilepsy, encephalopathy and psychosis the history of severe inoculation allergies patients with immunodeficiency and malignant tumors during the treatment period, receiving immunosuppressive therapy (oral steroid) or HIV due to low immunity, or family members have congenital immune disease Nonspecific immunoglobulin was injected within one month temperature=37.1<U+2103> and infectious diseases the history of thrombocytopenia or other thrombocytopenia with a definite diagnosis respiratory disease, acute infection or chronic disease activity period severe cardiovascular disease, liver and kidney disease, and complications of diabetes infectious, suppurative and allergic dermatosis other conditions that may affect the evaluation of the trail any serious adverse events that have a causal relationship with the inoculation of the upper dose of the vaccine the abnormality of 4 levels (local, systemic adverse reactions and vital signs) was judged to be related to vaccination other new standards of exclusion criteria for first needle other conditions that may affect the evaluation of the trail", "candidate_expression": "((HIV) AND (Nonspecific immunoglobulin within one month) AND (acute infection) AND (adverse events serious) AND (allergic dermatosis) AND (anaphylaxis) AND (cardiovascular disease severe) AND (chronic disease activity period) AND (complications) AND (congenital immune disease family members) AND (convulsion) AND (diabetes) AND (encephalopathy) AND (epilepsy) AND (family history) AND (history) AND (immunodeficiency) AND (immunosuppressive therapy) AND (infectious dermatosis) AND (infectious diseases) AND (inoculation allergies history severe) AND (inoculation of the upper dose of the vaccine) AND (kidney disease) AND (liver disease) AND (malignant tumors) AND (oral steroid) AND (psychosis) AND (respiratory disease) AND (suppurative dermatosis) AND (temperature =37.1<U+2103>) AND (thrombocytopenia history) AND (thrombocytopenia other))"}
{"candidate_id": "LLM07258", "doc_id": "NCT02609048_exc", "case_bucket": "or", "source_criterion": "1. A medical condition, other than PBC, that in the investigator's opinion would preclude full participation in the study or confound its results (e.g., cancer on active treatment) 2. AST or ALT > 3 × ULN 3. Total bilirubin > 2 × ULN 4. Auto-immune hepatitis 5. Primary sclerosing cholangitis 6. Known history of alpha-1-Antitrypsin deficiency 7. Known history of chronic viral hepatitis 8. Creatine kinase above ULN 9. Serum creatinine above ULN 10. For females, pregnancy or breast-feeding 11. Use of colchicine, methotrexate, azathioprine, or systemic steroids in the two months preceding screening 12. Current use of fibrates, including fenofibrates, or simvastatin 13. Use of an experimental treatment for PBC 14. Use of experimental or unapproved immunosuppressant 15. Any other condition(s) that would compromise the safety of the subject or compromise the quality of the clinical study, as judged by the Investigator", "candidate_expression": "((> 2 × ULN) AND (> 3 × ULN) AND (A medical condition, other than PBC, that in the investigator's opinion would preclude full participation in the study or confound its results (e.g., cancer on active treatment)) AND (Any other condition(s) that would compromise the safety of the subject or compromise the quality of the clinical study, as judged by the Investigator) AND (Auto-immune hepatitis) AND (Creatine kinase) AND (Current) AND (Primary sclerosing cholangitis) AND (Serum creatinine) AND (Total bilirubin) AND (above ULN) AND (alpha-1-Antitrypsin deficiency) AND (chronic) AND (experimental treatment for PBC) AND (females) AND (history) AND (immunosuppressant) AND (in the investigator's opinion) AND (in the two months preceding screening) AND (medical condition) AND (screening) AND (viral hepatitis) AND ((PBC) OR (other than)) AND ((ALT) OR (AST)) AND ((breast-feeding) OR (pregnancy)) AND ((azathioprine) OR (colchicine) OR (methotrexate) OR (systemic steroids)) AND ((fenofibrates) OR (fibrates) OR (simvastatin)) AND ((experimental) OR (unapproved)))"}
{"candidate_id": "LLM07259", "doc_id": "NCT03631355_exc", "case_bucket": "or", "source_criterion": "Legally incompetent or mentally impaired (e.g., minors, Alzheimer's subjects, dementia, etc.) Younger than 18 years of age Any patient considered a vulnerable subject Have bleeding or clotting disorder Preoperative anticoagulation therapy Abnormal coagulation profile Renal disorder or insufficiency Sickle cell disease", "candidate_expression": "((Abnormal coagulation profile) AND (Alzheimer's) AND (Legally incompetent) AND (Renal disorder) AND (Renal insufficiency) AND (Sickle cell disease) AND (age Younger than 18 years) AND (anticoagulation) AND (anticoagulation therapy Preoperative) AND (bleeding disorder) AND (clotting disorder) AND (coagulation profile Abnormal) AND (dementia) AND (mentally impaired) AND (minors) AND (vulnerable subject))"}
{"candidate_id": "LLM07260", "doc_id": "NCT03337581_inc", "case_bucket": "or", "source_criterion": "selective operation of inguinal hernia repair<U+3001>orthopedics operation or general surgery operation in children aged 3-9 years ASA I - II enter the operating room by himself without parents normal liver and kidney function no history of anesthesia medication allergy.", "candidate_expression": "((3-9 years) AND (ASA) AND (I - II) AND (aged) AND (allergy) AND (anesthesia medication) AND (children) AND (history) AND (no) AND (normal kidney function) AND (normal liver function) AND ((general surgery operation) OR (inguinal hernia repair) OR (orthopedics operation)))"}
{"candidate_id": "LLM07261", "doc_id": "NCT02175186_inc", "case_bucket": "or", "source_criterion": "Age between 20 and 80 years Patients undergoing percutaneous coronary intervention and need to take dual antiplatelet therapy continuously at least 12weeks Modified Lanza Score grade 0-1 measured by upper gastrointestinal endoscopy mild gastrointestinal symptom Creatinen in blood = 3mg/dl BUN = 50mg/dl Birilubin = 3mg/dl AST and ALT = 80U/L", "candidate_expression": "((ALT) AND (AST) AND (Age between 20 and 80 years) AND (BUN = 50mg/dl) AND (Birilubin = 3mg/dl) AND (Creatinen = 3mg/dl) AND (Modified Lanza Score grade 0-1) AND (dual antiplatelet therapy continuously at least 12weeks) AND (gastrointestinal symptom mild) AND (percutaneous coronary intervention) AND (upper gastrointestinal endoscopy))"}
{"candidate_id": "LLM07262", "doc_id": "NCT02466113_inc", "case_bucket": "other", "source_criterion": "The informed consent has been obtained from the patient. With confirmed diagnosis of stage II colon cancer. With moderate/good ECOG health rating (PS): 0-1 score. The patient receive no anti-cancer treatment before primary surgery. The patient receive radical operation for colon cancer with negative margin.", "candidate_expression": "((ECOG health rating (PS) moderate/good 0-1 score) AND (The informed consent has been obtained from the patient.) AND (colon cancer) AND (colon cancer stage II) AND (primary surgery) AND (radical operation negative margin) AND NOT (anti-cancer treatment before primary surgery))"}
{"candidate_id": "LLM07263", "doc_id": "NCT02649114_inc", "case_bucket": "other", "source_criterion": "satisfying DSM-V criteria for ED and for half of the patients in addition have a history of childhood trauma.", "candidate_expression": "((DSM-V criteria satisfying) AND (ED) AND (childhood trauma history))"}
{"candidate_id": "LLM07264", "doc_id": "NCT00198913_exc", "case_bucket": "or", "source_criterion": "type 1 diabetic or non-diabetic", "candidate_expression": "((non-diabetic) AND (type 1 diabetic))"}
{"candidate_id": "LLM07265", "doc_id": "NCT03211741_exc", "case_bucket": "or", "source_criterion": "Women who are pregnant or breastfeeding (pregnancy defined as the state of a female after conception until the termination of gestation, confirmed by a positive human chorionic gonadotropin laboratory test (> 5mIU/mL) Women of child bearing potential must be practicing effective contraception implemented during the trial and for at least 28 days following the last dose of study medication Tromboembolic event (CVA or transient ischemic attack, AMI) less than 3 months prior to the intravitreal injection of bevacizumab History of hypersensitivity for bevacizumab.", "candidate_expression": "((AMI) AND (CVA) AND (Tromboembolic event less than 3 months prior to the intravitreal injection of bevacizumab) AND (Women) AND (bevacizumab) AND (breastfeeding) AND (child bearing potential) AND (contraception effective during the trial for at least 28 days following the last dose of study medication) AND (human chorionic gonadotropin laboratory test > 5mIU/mL) AND (human chorionic gonadotropin positive) AND (hypersensitivity History) AND (intravitreal injection) AND (pregnant) AND (study medication last dose) AND (transient ischemic attack))"}
{"candidate_id": "LLM07266", "doc_id": "NCT02595190_exc", "case_bucket": "or", "source_criterion": "1. Patients with lumbar common diseases(e.g., Lumbar disc, Lumbar spinal stenosis, Lumbar slippage, etc) 2. Researchers think that Patients with disease may be interference results(e.g., Spinal deformity, spine fracture, ankylosing spondylitis, spinal tuberculosis and spinal infection, spinal tumor, pelvic inflammatory disease and other disease of department of gynaecology, etc) 3. Patients with other nervous system diseases(e.g., cerebral tumor, neurinoma, trigeminal neuralgia,etc) 4. Patients with Magnetic resonance imaging contraindication ,including claustrophobic syndrome patients 5. Patients with recent (less than 3 years) use chemical drugs or have obvious psychological problems 6. In the past 2 months involved in other drugs or devices clinical trials", "candidate_expression": "((In the past 2 months involved in other drugs or devices clinical trials) AND (Magnetic resonance imaging) AND (claustrophobic syndrome) AND (contraindication) AND (lumbar diseases) AND (nervous system diseases) AND ((cerebral tumor) OR (neurinoma) OR (trigeminal neuralgia)) AND ((Lumbar disc) OR (Lumbar slippage) OR (Lumbar spinal stenosis)) AND ((Spinal deformity) OR (ankylosing spondylitis) OR (pelvic inflammatory disease) OR (spinal infection) OR (spinal tuberculosis) OR (spinal tumor) OR (spine fracture,)))"}
{"candidate_id": "LLM07267", "doc_id": "NCT03173092_exc", "case_bucket": "or", "source_criterion": "Failure to have fully recovered (that is, less than or equal to [<=] Grade 1 toxicity) from the reversible effects of prior chemotherapy. Major surgery within 14 days before enrollment. Radiotherapy within 14 days before enrollment (if the involved field is small, 7 days will be considered a sufficient interval between treatment and administration of the ixazomib.) Central nervous system involvement. Infection requiring systemic antibiotic therapy or other serious infection within 14 days before study enrollment. Evidence of current uncontrolled cardiovascular conditions, including uncontrolled hypertension, uncontrolled cardiac arrhythmias, symptomatic congestive heart failure, unstable angina, or myocardial infarction within the past 6 months. Systemic treatment, within 14 days before the first dose of ixazomib, with strong cytochrome P450 3A (CYP3A) inducers (rifampin, rifapentine, rifabutin, carbamazepine, phenytoin, phenobarbital), or use of Ginkgo biloba or St. John's wort. Ongoing or active systemic infection, active hepatitis B or C virus infection, or known human immunodeficiency virus positive. Diagnosed or treated for another malignancy within 2 years before study enrollment or previously diagnosed with another malignancy and have any evidence of residual disease. Participants with non-melanoma skin cancer or carcinoma in situ of any type are not excluded if they have undergone complete resection. Has greater than or equal to (>=) Grade 2 peripheral neuropathy, or Grade 1 with pain on clinical examination during the screening period. PD on first-line therapy. Participation in other interventional clinical trials, including those with other investigational agents not included in this trial, within 30 days of the start of this trial and throughout the duration of this trial. Non-interventional trials (that is, observational trials) are permitted at any time point.", "candidate_expression": "((7 days) AND (Central nervous system involvement) AND (Failure) AND (Grade 1) AND (Major surgery) AND (PD) AND (Participation in other interventional clinical trials) AND (Radiotherapy) AND (Systemic treatment) AND (active) AND (another) AND (any evidence of) AND (any type) AND (cardiovascular conditions) AND (chemotherapy) AND (complete resection) AND (current) AND (first-line therapy) AND (fully recovered) AND (greater than or equal to (>=) Grade 2) AND (ixazomib) AND (less than or equal to [<=] Grade 1) AND (not excluded) AND (other) AND (pain) AND (peripheral neuropathy) AND (positive) AND (previously) AND (residual disease) AND (serious) AND (symptomatic) AND (systemic antibiotic therapy) AND (the duration of this trial) AND (the first dose of ixazomib) AND (the start of this trial) AND (toxicity) AND (uncontrolled) AND (within 14 days before enrollment) AND (within 14 days before study enrollment) AND (within 14 days before the first dose of ixazomib) AND (within 2 years before study enrollment) AND (within the past 6 months) AND ((involved field is small) OR (within 14 days before enrollment)) AND ((Infection) OR (infection)) AND ((cardiac arrhythmias) OR (congestive heart failure) OR (hypertension) OR (myocardial infarction) OR (unstable angina)) AND ((carbamazepine) OR (phenobarbital) OR (phenytoin) OR (rifabutin) OR (rifampin) OR (rifapentine)) AND ((Ginkgo biloba) OR (St. John's wort) OR (strong cytochrome P450 3A (CYP3A) inducers)) AND ((Ongoing) OR (active)) AND ((C virus infection) OR (hepatitis B virus infection)) AND ((human immunodeficiency virus) OR (systemic infection)) AND ((malignancy)) AND ((carcinoma in situ) OR (non-melanoma skin cancer)) AND ((throughout the duration of this trial) OR (within 30 days of the start of this trial)))"}
{"candidate_id": "LLM07268", "doc_id": "NCT00344318_inc", "case_bucket": "or", "source_criterion": "Male or female between, and including, 6-12 weeks (42 to 90 days) of age at the time of the first vaccination. Subjects for whom the investigator believes that their parents/guardians can and will comply with the requirements of the protocol Written informed consent obtained from the parent or guardian of the subject. Free of obvious health problems as established by medical history and clinical examination before entering into the study. Born after a gestation period between 36 and 42 weeks.", "candidate_expression": "((Born) AND (Written informed consent parent guardian) AND (gestation period between 36 and 42 weeks) AND (of age between 6-12 weeks at the time of the first vaccination between 42 to 90 days) AND NOT (health problems obvious))"}
{"candidate_id": "LLM07269", "doc_id": "NCT03249311_inc", "case_bucket": "other", "source_criterion": "Male participants between 18 and 40 years-old Written informed consent signed by the participant", "candidate_expression": "((Male) AND (Written informed consent signed by the participant) AND (old between 18 and 40 years))"}
{"candidate_id": "LLM07270", "doc_id": "NCT02425774_inc", "case_bucket": "or", "source_criterion": "patients undergoing partial or full resection of the pancreas due to a benign or malignant tumor", "candidate_expression": "((benign tumor) AND (full resection of the pancreas) AND (malignant tumor) AND (partial resection of the pancreas))"}
{"candidate_id": "LLM07271", "doc_id": "NCT02923700_exc", "case_bucket": "or", "source_criterion": "age > 80 years; Kellgren-Lawrence score at X-ray evaluation > 3; major axial deviation (varus >5° , valgus > 5°), systemic disorders such as diabetes, rheumatoid arthritis, haematological diseases (coagulopathy), severe cardiovascular diseases, infections, immunodepression; patients in therapy with anticoagulants or antiaggregants; use of NSAIDs in the 5 days before blood donation; patients with Hb values < 11 g/dl and platelet values < 150,000/mmc.", "candidate_expression": "((Hb < 11 g/dl) AND (Kellgren-Lawrence score > 3) AND (NSAIDs in the 5 days before blood donation) AND (X-ray evaluation) AND (age > 80 years) AND (antiaggregants) AND (anticoagulants) AND (cardiovascular diseases severe) AND (coagulopathy) AND (diabetes) AND (haematological diseases) AND (immunodepression) AND (infections) AND (major axial deviation) AND (platelet < 150,000/mmc) AND (rheumatoid arthritis) AND (systemic disorders) AND (therapy) AND (valgus > 5°) AND (varus >5°))"}
{"candidate_id": "LLM07272", "doc_id": "NCT01009359_exc", "case_bucket": "or", "source_criterion": "Current unstable medical condition (e.g. unstable angina, myocardial infarction or coronary revascularization in the preceding 12 months, cardiac failure, chronic renal failure, chronic hepatic disease, severe pulmonary disease, blood disorders, poorly controlled diabetes, chronic infection)", "candidate_expression": "((chronic) AND (unstable medical condition Current unstable) AND ((blood disorders) OR (cardiac failure) OR (chronic hepatic disease) OR (chronic infection) OR (chronic renal failure) OR (coronary revascularization in the preceding 12 months) OR (diabetes controlled) OR (myocardial infarction in the preceding 12 months) OR (pulmonary disease severe) OR (unstable angina)))"}
{"candidate_id": "LLM07273", "doc_id": "NCT03089086_inc", "case_bucket": "or", "source_criterion": "South Australian secondary school students in years 10, 11, and 12 in 2017 Written parental consent for those under the age of 18 Written student consent assent for those under the age of 18 (or if 18 years old and older consent for themselves) Available at school for at least the first pharyngeal swab and willing to comply with study procedures", "candidate_expression": "((South Australian) AND (Written parental consent for those under the age of 18) AND (Written student consent assent for those under the age of 18 (or if 18 years old and older consent for themselves)) AND (comply with study procedures willing to) AND (pharyngeal swab first) AND (secondary school students in 2017) AND ((years 10) OR (years 11) OR (years 12)))"}
{"candidate_id": "LLM07274", "doc_id": "NCT02952963_inc", "case_bucket": "or", "source_criterion": "Uncomplicated RYGB performed minimum 3 months prior to the study. Fasting glucose < 7,0 mM, HbA1c < 48 mmol/mol 3 months after RYGB", "candidate_expression": "((3 months after RYGB) AND (< 48 mmol/mol) AND (< 7,0 mM) AND (RYGB) AND (Uncomplicated) AND (minimum 3 months prior to the study) AND (the study) AND ((Fasting glucose) OR (HbA1c)))"}
{"candidate_id": "LLM07275", "doc_id": "NCT03467750_inc", "case_bucket": "or", "source_criterion": "Diagnosis of sleep disordered breathing or obstructive sleep apnea Children undergoing elective tonsillectomy or adenotonsillectomy at Children's Healthcare of Atlanta Egleston location Parent or legal guardian willing to participate, and able to understand and sign the provided informed consent", "candidate_expression": "((Children) AND (Children's Healthcare of Atlanta Egleston) AND (Parent or legal guardian willing to participate, and able to understand and sign the provided informed consent) AND (elective) AND ((obstructive sleep apnea) OR (sleep disordered breathing)) AND ((adenotonsillectomy) OR (tonsillectomy)))"}
```
