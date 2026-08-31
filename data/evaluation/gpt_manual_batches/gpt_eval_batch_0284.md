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
{"candidate_id": "LLM07076", "doc_id": "NCT01700790_inc", "case_bucket": "or", "source_criterion": "Antiretroviral naive Taking Kaletra containing regimen with suppressed viral load. Taking an NNRTI or integrase containing regimen without prior history of use of PI for more than 2 weeks Taking an NNRTI or integrase containing regimen with prior exposure to PI greater than 2 weeks. It must be clearly stated in the source document that PI was switched to another agent for convenience. Taking another PI containing regimens with suppressed viral load. It must be clearly stated in source document that if another PI was used for greater than 2 weeks the regimen was switched to another agent for convenience. Subjects with prior history of PI use may be enrolled, if there is a genotype showing no resistance to Kaletra Other Inclusion criteria Be at least 18 years of age and able to give informed consent. Diagnosed with TB by criteria per Brazilian Ministry of Health Have a good clinical response to TB. Tolerating tuberculosis therapy containing rifampin for the 2 weeks prior to screening,except for persons taking protease inhibitors at time of diagnosis of TB.,. Subjects taking protease inhibitors will be screened and initiate visit 1 within 3 days of starting TB medication HIV positive with documentation present in source document. Have a CD4 cell count greater than 50 cells/mm3if not taking ART. Persons with cd4 < 50 may be enrolled, if it is felt that in the best interest of the patient, that enrollment in the study will allow for quicker initiation of antiretroviral therapy than referral to another treatment center.", "candidate_expression": "((Antiretroviral) AND (CD4 cell count greater than 50 cells/mm3) AND (HIV positive) AND (Kaletra) AND (NNRTI) AND (PI) AND (PI prior greater than 2 weeks) AND (TB) AND (TB criteria per Brazilian Ministry of Health) AND (able to give informed consent) AND (age at least 18 years) AND (good clinical response) AND (integrase) AND (naive) AND (regimen) AND (regimens) AND (rifampin) AND (tuberculosis) AND (tuberculosis therapy for the 2 weeks prior to screening) AND (viral load suppressed) AND NOT (PI prior for more than 2 weeks) AND NOT (protease inhibitors at time of diagnosis of TB) AND NOT (ART))"}
{"candidate_id": "LLM07077", "doc_id": "NCT03461679_exc", "case_bucket": "other", "source_criterion": "Unable to consent Chronic opioid consumption Allergy to study medication Lower limb surgery preceding year Unable to complete baseline testing, pre-existing neurological deficit Contraindication to spinal anaesthesia", "candidate_expression": "((Allergy) AND (Chronic) AND (Contraindication) AND (Lower limb surgery) AND (Unable to consent) AND (neurological deficit) AND (opioid consumption) AND (pre-existing) AND (spinal anaesthesia) AND (study medication))"}
{"candidate_id": "LLM07078", "doc_id": "NCT02986659_exc", "case_bucket": "or", "source_criterion": "eGFR <45 Type 2 diabetes (HbA1c>6.5) or type 1 diabetes Any tobacco or nicotine product use in the past year Low vitamin B12 Levels (< 300 pg/mL) Self-reported severe difficulty or inability to walk 400m or climb 10 steps (from Q 2 and 19 on PAT-D) Self-reported difficulty or inability to perform basic ADL functions (from Q 10, 13, 14, 16 on PAT-D) Excessive alcohol use (>14 drinks/week) Cancer requiring treatment in past year (except skin) Dementia - diagnosed and/or MoCA score <18 Parkinson's or other neurological disease Chronic liver disease or cirrhosis End stage renal disease or on dialysis Rheumatic conditions (Rheumatoid arthritis, lupus, and any other autoimmune disease the -PI deems them to be ineligible for) Thyroid problems the PI deems them to be ineligible for Gout Involved in another interventional study Hemoglobin <8 or diagnosed with anemia Recent unintentional weight change (+/- 10 lbs. in the last 12 months) BMI <18.5 Likely to not follow the protocol PI deems unfit to participate Already taking Metformin or any other drug intended to treat diabetes", "candidate_expression": "((+/- 10 lbs.) AND (< 300 pg/mL) AND (<18) AND (<18.5) AND (<45) AND (<8) AND (>14 drinks/week) AND (>6.5) AND (BMI) AND (Cancer) AND (Dementia) AND (Gout) AND (HbA1c) AND (Involved in another interventional study) AND (Likely to not follow the protocol) AND (MoCA score) AND (Rheumatic conditions) AND (Thyroid problems) AND (alcohol use) AND (diabetes) AND (eGFR) AND (last 12 months) AND (past year) AND (treatment) AND (vitamin B12 Levels) AND (weight) AND ((Parkinson's) OR (neurological disease)) AND ((Chronic liver disease) OR (cirrhosis)) AND ((End stage renal disease) OR (dialysis)) AND ((Type 2 diabetes) OR (type 1 diabetes)) AND ((Rheumatoid arthritis) OR (autoimmune disease) OR (lupus)) AND ((Hemoglobin) OR (anemia)) AND ((Metformin) OR (drug)) AND ((nicotine product use) OR (tobacco)))"}
{"candidate_id": "LLM07079", "doc_id": "NCT02760459_exc", "case_bucket": "or", "source_criterion": "History of active rheumatic diseases History of previous musculoskeletal injury of the same knee for excluding patients with secondary knee osteoarthritis History of previous surgery on the same knee History of adverse effects from medications to be used in this study Contraindication to spinal anesthesia History of psychiatric disorders or cognitive impairment Contraindication to corticosteroid agents Poorly controlled diabetes mellitus (HbA1C > 7.5) Poorly controlled hypertension History of ischemic heart disease or peripheral arterial disease or cerebrovascular disease Hepatic insufficiency (Child-Pugh score > 5) Renal insufficiency (Creatinine clearance < 30 mL/min) History of cataracts or glaucoma or ocular hypertension History of steroid or immunosuppressive drug use within 6 months of surgery", "candidate_expression": "((< 30 mL/min) AND (> 5) AND (> 7.5) AND (Child-Pugh score) AND (Contraindication) AND (Creatinine clearance) AND (HbA1C) AND (Hepatic insufficiency) AND (Poorly controlled) AND (Renal insufficiency) AND (active) AND (cataracts) AND (cerebrovascular disease) AND (cognitive impairment) AND (corticosteroid) AND (diabetes mellitus) AND (glaucoma) AND (hypertension) AND (immunosuppressive drug) AND (ischemic heart disease) AND (knee) AND (musculoskeletal injury) AND (ocular hypertension) AND (peripheral arterial disease) AND (psychiatric disorders) AND (rheumatic diseases) AND (secondary knee osteoarthritis) AND (spinal anesthesia) AND (steroid) AND (surgery) AND (within 6 months of surgery))"}
{"candidate_id": "LLM07080", "doc_id": "NCT03532620_inc", "case_bucket": "or", "source_criterion": "Age 18-80 years old; IFG: 5.6mmol/L (100mg/dl)=FPG<7.0mmol/L (126mg/dl), or IGT: 7.8mmol/L (140mg/dl)=OGTT 2-h PG<11.1mmol/L (200mg/dl), or HbA1C 5.7-6.4% (39-47mmol/mol); 2.6mmol/L (100mg/dl)=LDL-C=5.2mmol/L (200mg/dl), and TG<5.7mmol/L (500mg/dl); 130mmHg=SBP<180mmHg, or 80mmHg=DBP<110mmHg or ongoing anti-hypertensive therapy; Patients volunteered for the study and signed informed consent.", "candidate_expression": "((Age 18-80 years old) AND (FPG 5.6mmol/L <7.0mmol/L 100mg/dl 126mg/dl) AND (LDL-C 2.6mmol/L 5.2mmol/L 100mg/dl 200mg/dl) AND (OGTT 2-h PG 7.8mmol/L <11.1mmol/L 140mg/dl 200mg/dl 39-47mmol/mol) AND (Patients volunteered for the study and signed informed consent.) AND (TG <5.7mmol/L 500mg/dl) AND ((HbA1C 5.7-6.4%) OR (IFG) OR (IGT)) AND ((DBP 80mmHg= <110mmHg) OR (SBP 130mmHg <180mmHg) OR (anti-hypertensive therapy ongoing)))"}
{"candidate_id": "LLM07081", "doc_id": "NCT01118871_exc", "case_bucket": "or", "source_criterion": "current alcohol abuse or drug dependence pregnancy active opportunistic infection or significant co-morbidities current prohibited concomitant medication a likelihood of diminished response to any of the study treatment arms, in the opinion of the investigator, based on HIV genotypic resistance testing", "candidate_expression": "((a likelihood of diminished response to any of the study treatment arms, in the opinion of the investigator, based on HIV genotypic resistance testing) AND (co-morbidities) AND (concomitant) AND (current) AND (medication) AND (opportunistic infection) AND (pregnancy) AND (prohibited) AND (significant) AND ((alcohol abuse) OR (drug dependence)))"}
{"candidate_id": "LLM07082", "doc_id": "NCT00867958_inc", "case_bucket": "other", "source_criterion": "1. Patient is over 18 years old. 2. Patient is scheduled for a non-emergency procedure. 3. Subject signs and dates a written informed consent form (ICF) and indicates an understanding of the study procedures.", "candidate_expression": "((3. Subject signs and dates a written informed consent form (ICF) and indicates an understanding of the study procedures.) AND (non-emergency) AND (non-emergency procedure) AND (over 18 years old) AND (scheduled) AND (years old))"}
{"candidate_id": "LLM07083", "doc_id": "NCT02462317_inc", "case_bucket": "or", "source_criterion": "First single stroke ischaemic or haemorrhagic responsible of an hemiplegia Stoke since less than 2 month A sufficient understood A spasticity : a Tardieu score upper or equal to 2 on at least one of the following muscle-triceps surae, flexors of fingers, of wrist and of elbow A free consent", "candidate_expression": "((A free consent) AND (Stoke since less than 2 month) AND (Tardieu score upper or equal to 2 muscle-triceps surae flexors of fingers) AND (elbow) AND (hemiplegia) AND (spasticity) AND (stroke First single ischaemic haemorrhagic) AND (wrist))"}
{"candidate_id": "LLM07084", "doc_id": "NCT02675153_exc", "case_bucket": "or", "source_criterion": "Allergic to sirolimus or serious side effects Need emergency surgery Accompanied with other severe disease (involve C.diff infection) Follow-up less than 1 year", "candidate_expression": "((Allergic) AND (C.diff infection) AND (Follow-up) AND (Need) AND (emergency surgery) AND (less than 1 year) AND (serious) AND (severe disease) AND (side effects) AND (sirolimus))"}
{"candidate_id": "LLM07085", "doc_id": "NCT02550080_exc", "case_bucket": "or", "source_criterion": "Has previously received Dapsone therapy. The subject or any of their healthcare providers is aware of the subjects HLA type. Has been diagnosed with Glucose-6-phosphate dehydrogenase deficiency or methemoglobin reductase deficiency Satisfies any contraindications or restrictions to Dapsone therapy as listed in the product labels. Current severe illness, including heart, liver and renal failure, major organ allograft, malignancy requiring parenteral chemotherapy that can not be discontinued for the duration of the trial, or any other conditions which, in the opinion of the Investigator, would make the patient unsuitable for the study. Any laboratory abnormality at Screening which, in the opinion of the Investigator, should preclude the subject's participation in the study [alanine aminotransferase (ALT), glutamic oxaloacetic transaminase(ALT), et al). Pregnant women or women who are breastfeeding. Subject is, in the opinion of the Investigator, unable to complete the 6 week Observation period and the EPT assessments as required. A positive result for HLA-B*1301 in those subjects randomised to the genetic screening arm.", "candidate_expression": "((Dapsone) AND (Glucose-6-phosphate dehydrogenase deficiency) AND (HLA-B*1301) AND (chemotherapy) AND (contraindications) AND (heart failure) AND (liver failure) AND (major organ allograft) AND (malignancy) AND (methemoglobin reductase deficiency) AND (positive) AND (regnant women or women who are breastfeeding) AND (renal failure))"}
{"candidate_id": "LLM07086", "doc_id": "NCT02939872_exc", "case_bucket": "or", "source_criterion": "Contraindication to antiplatelet therapy Need to continue clopidogrel due to stroke, peripheral disease, significant carotid disease or recent acute coronary syndrome Major bleeding history or bleeding diathesis Pregnancy", "candidate_expression": "((Contraindication) AND (Major) AND (Need to) AND (Pregnancy) AND (antiplatelet therapy) AND (clopidogrel) AND (continue) AND (history) AND (recent) AND (significant) AND ((acute coronary syndrome) OR (carotid disease) OR (peripheral disease) OR (stroke)) AND ((bleeding) OR (bleeding diathesis)))"}
{"candidate_id": "LLM07087", "doc_id": "NCT02186600_exc", "case_bucket": "or", "source_criterion": "Have osteoporosis Have a 10 yr probability of hip fracture >3% or major fracture >20% based on results of the FRAX tool Currently take bisphosphonates, estrogen replacement therapy, glucocorticosteroids, or other drugs affecting bone Currently participate in a resistance training or high impact weight bearing exercise program two or more times weekly Weigh >300 lbs Have abnormal results for the following laboratory tests: serum 25(OH)D; serum creatinine; serum calcium; PTH; TSH Have Paget's disease, heart disease, uncontrolled hypertension, renal disease, or other concomitant conditions that prohibit participation in exercises, risedronate therapy, or use of CaD supplements.", "candidate_expression": "((10 yr probability of hip fracture >3%) AND (10 yr probability of major fracture >20%) AND (PTH abnormal results) AND (TSH abnormal results) AND (Weigh >300 lbs) AND (hip fracture) AND (major fracture) AND (osteoporosis) AND (serum 25(OH)D abnormal results) AND (serum calcium abnormal results) AND (serum creatinine abnormal results) AND ((participate in a resistance training two or more times weekly) OR (participate in high impact weight bearing exercise two or more times weekly)) AND ((CaD supplements) OR (Paget's disease) OR (heart disease) OR (other concomitant conditions that prohibit participation in exercises) OR (renal disease) OR (risedronate therapy) OR (uncontrolled hypertension)) AND ((bisphosphonates) OR (drugs affecting bone) OR (estrogen replacement therapy) OR (glucocorticosteroids)))"}
{"candidate_id": "LLM07088", "doc_id": "NCT03352869_exc", "case_bucket": "or", "source_criterion": "Except for serious complications (cardiovascular events and recent significant liver, kidney or lung disease within 3 months) high blood pressure (>160/100mmHg) active infection secondary diabetes pregnancy alcohol abuse allergic to GLP-1 receptor agonist", "candidate_expression": "((GLP-1 receptor agonist) AND (active infection) AND (alcohol abuse) AND (allergic) AND (blood pressure >160/100mmHg) AND (cardiovascular events) AND (diabetes secondary) AND (disease kidney) AND (disease liver) AND (high blood pressure) AND (lung disease) AND (pregnancy) AND (serious complications))"}
{"candidate_id": "LLM07089", "doc_id": "NCT02634541_exc", "case_bucket": "or", "source_criterion": "Psoriasis or psoriasis arthropathy Inflammatory bowel disease Unwillingness to participate in the study with additional imaging protocols Expected life-span less than <1 year Diabetes (to improve the PET imaging quality) Probable noncompliance Pregnancy Age <18 years or >75 years Contraindication for adalimumab Methotrexate used within the previous 6 months A biologic medicine used within the previous 6 months", "candidate_expression": "((Age) AND (Contraindication) AND (Diabetes) AND (Expected life-span less than <1 year) AND (Inflammatory bowel disease) AND (Methotrexate within the previous 6 months) AND (PET imaging quality) AND (Pregnancy) AND (Unwillingness to participate in the study with additional imaging protocols) AND (adalimumab) AND (biologic medicine within the previous 6 months) AND (noncompliance Probable) AND ((Psoriasis) OR (psoriasis arthropathy)) AND ((<18 years) OR (>75 years)))"}
{"candidate_id": "LLM07090", "doc_id": "NCT02019160_inc", "case_bucket": "other", "source_criterion": "Kindergarteners who have joined our outreach dental service will be invited to join this study. Preschool children aged 3-4 years who have tooth decay and are attending the first year of kindergarten will be invited to join this study.", "candidate_expression": "((3-4 years) AND (Kindergarteners) AND (Preschool children) AND (aged) AND (tooth decay))"}
{"candidate_id": "LLM07091", "doc_id": "NCT02715466_inc", "case_bucket": "or", "source_criterion": "Male or female patients = 18 and = 85 years of age Women of child bearing potential must test negative on standard pregnancy test (urine or serum) Patients with body weight = 55 kg and = 140 kg and body mass index (BMI) = 18 kg/m2 Patients diagnosed severe sepsis / septic shock at admission on Intensive Care Unit who can be enrolled within 90 min after admission OR patients diagnosed severe sepsis / septic shock during Intensive Care Unit stay who can be enrolled within 90 min after diagnosis Patients where antibiotic therapy has already been started (prior to randomization) Patient who are fluid responsive. Fluid responsiveness is defined as increase of > 10% in mean arterial pressure (MAP) after passive leg raising (PLR) Signed informed consent by patient, legal representative or authorized person or deferred consent", "candidate_expression": "((Male) AND (Signed informed consent by patient, legal representative or authorized person or deferred consent) AND (Women) AND (age = 18 and = 85 years) AND (antibiotic therapy prior to randomization) AND (body mass index (BMI) = 18 kg/m2) AND (body weight = 55 kg and = 140 kg) AND (child bearing potential) AND (female) AND (fluid responsive) AND (mean arterial pressure (MAP) > 10% after passive leg raising (PLR)) AND (septic shock at admission on Intensive Care Unit) AND (serum) AND (severe sepsis at admission on Intensive Care Unit) AND (standard pregnancy test negative) AND (urine))"}
{"candidate_id": "LLM07092", "doc_id": "NCT03011177_inc", "case_bucket": "other", "source_criterion": "Patients who are 19 years or older on screening Patients with type 2 diabetes mellitus Patients with 7.0% = HbA1c = 11.0% at the screening visit Patients with Fasting Plasma Glucose <15mmol/L(270mg/dL) on screening", "candidate_expression": "((Fasting Plasma Glucose <15mmol/L 270mg/dL on screening) AND (HbA1c 7.0% 11.0% at the screening visit) AND (type 2 diabetes mellitus) AND (years 19 or older on screening))"}
{"candidate_id": "LLM07093", "doc_id": "NCT02825290_exc", "case_bucket": "other", "source_criterion": "PGD patients More than 4 previous embryo transfers", "candidate_expression": "((PGD) AND (embryo transfers More than 4 previous))"}
{"candidate_id": "LLM07094", "doc_id": "NCT02072811_inc", "case_bucket": "other", "source_criterion": "Adult acute myeloid leukemia Age: ≥18 and ≤ 60 Clinical condition of the patient allows to carry out induction therapy: ECOG performance status: ≤ 2 and the Hematopoietic Cell Transplant-Co-morbidity Index (HCT-I): ≤3 Informed consent to participate in the study (ICF signed) The second early induction start criteria is in addition to the listed above, the percentage of the blasts on the level >10% on 7th day.", "candidate_expression": "((>10%) AND (Adult acute myeloid leukemia) AND (Age) AND (ECOG performance status) AND (Hematopoietic Cell Transplant-Co-morbidity Index (HCT-I)) AND (Informed consent to participate in the study (ICF signed)) AND (on 7th day) AND (percentage of the blasts) AND (≤ 2) AND (≤3) AND (≥18 and ≤ 60))"}
{"candidate_id": "LLM07095", "doc_id": "NCT02201316_exc", "case_bucket": "or", "source_criterion": "Current or chronic history of liver disease, or known hepatic or biliary abnormalities (with the exception of Gilbert's syndrome or asymptomatic gallstones). History of regular alcohol consumption within 6 months of the study defined as: An average weekly intake of >21 units for males or >14 units for females. One unit is equivalent to 8 gram of alcohol: a half-pint (approximately 240 milliliter [mL]) of beer, 1 glass (100 mL) of wine or 1 (25 mL) measure of spirits. History of sensitivity to heparin or heparin-induced thrombocytopenia. History of sensitivity to any of the study medications, or components thereof or a history of drug or other allergy that, in the opinion of the investigator or GSK Medical Monitor, contraindicates their participation. Gastrointestinal disease or with gastrointestinal surgical history which can affect the absorption of the investigational product. A positive pre-study Hepatitis B surface antigen or positive Hepatitis C antibody result within 3 months of screening Urinary cotinine levels indicative of smoking or history or regular use of tobacco- or nicotine-containing products within 6 months prior to screening. A positive pre-study drug/alcohol screen. A positive test for Human Immunodeficiency Virus (HIV) antibody. Pregnant females as determined by positive serum hCG test at screening or prior to dosing. Where participation in the study would result in donation of blood or blood products in excess of 500 mL within a 90 day period. Lactating females. The subject has participated in a clinical trial and has received an investigational product within the following time period prior to the first dosing day in the current study: 90 days, 5 half-lives or twice the duration of the biological effect of the investigational product (whichever is longer). Exposure to more than four new chemical entities within 12 months prior to the first dosing day.", "candidate_expression": "((>14 units) AND (>21 units) AND (History) AND (Human Immunodeficiency Virus (HIV) antibody) AND (Lactating) AND (Pregnant) AND (The subject has participated in a clinical trial and has received an investigational product within the following time period prior to the first dosing day in the current study: 90 days, 5 half-lives or twice the duration of the biological effect of the investigational product (whichever is longer).) AND (Urinary cotinine levels) AND (affect the absorption of the investigational product) AND (asymptomatic) AND (average weekly intake) AND (contraindicates their participation) AND (dosing) AND (exception) AND (females) AND (gastrointestinal surgical) AND (heparin) AND (heparin-induced) AND (history) AND (in the opinion of the investigator or GSK Medical Monitor) AND (more than four) AND (new chemical entities) AND (positive) AND (pre-study) AND (regular alcohol consumption) AND (screening) AND (serum hCG test) AND (study medications) AND (the first dosing day) AND (the study) AND (within 12 months prior to the first dosing day) AND (within 3 months of screening) AND (within 6 months of the study) AND (within 6 months prior to screening) AND ((Current) OR (chronic)) AND ((females) OR (males)) AND ((heparin-induced thrombocytopenia) OR (sensitivity to heparin)) AND ((allergy) OR (drug allergy) OR (sensitivity to any of the study medications)) AND ((Gastrointestinal disease) OR (gastrointestinal surgical history)) AND ((Hepatitis B surface antigen) OR (Hepatitis C antibody)) AND ((regular use of nicotine-containing products) OR (regular use of tobacco) OR (smoking)) AND ((biliary abnormalities) OR (hepatic abnormalities) OR (liver disease)) AND ((alcohol screen) OR (drug screen)) AND ((at screening) OR (prior to dosing)) AND ((Gilbert's syndrome) OR (gallstones)))"}
{"candidate_id": "LLM07096", "doc_id": "NCT01801072_inc", "case_bucket": "or", "source_criterion": "Adult (=18 years) Presence of intracranial aneurysm (with or without rupture) Treating surgeon has recommended surgical repair of the aneurysm", "candidate_expression": "((Adult) AND (aneurysm) AND (intracranial aneurysm with rupture without rupture) AND (surgical repair recommended) AND (years =18 years))"}
{"candidate_id": "LLM07097", "doc_id": "NCT02773173_exc", "case_bucket": "or", "source_criterion": "Emergency surgery Pregnancy or lactation Immune disorders Kidney or liver disease or advanced-stage cardiopulmonary Patient refusal to participate in the study Patients under 18 years or inability to consent Associated neuromuscular disorders, contraindication for the use of rocuronium/ sugammadex, allergy or hypersensitivity to rocuronium / sugammadex", "candidate_expression": "((Emergency surgery) AND (Immune disorders) AND (Kidney disease) AND (Patient refusal to participate in the study) AND (Pregnancy) AND (advanced-stage cardiopulmonary) AND (allergy) AND (contraindication) AND (hypersensitivity) AND (inability to consent) AND (lactation) AND (liver disease) AND (neuromuscular disorders) AND (rocuronium) AND (sugammadex) AND (under 18) AND (years))"}
{"candidate_id": "LLM07098", "doc_id": "NCT01793519_exc", "case_bucket": "or", "source_criterion": "Had dose increase of anti-TNF agent or DMARD in the last 6 months Had change of anti-TNF agent or DMARD in the last 6 months Treated currently with golimumab or certolizumab Treated with greater than 10 mg of prednisone (or equivalent) daily in the last 6 months Treated with greater than 5 mg of prednisone (or equivalent) daily in the last 3 months Treated with intramuscular or intravenous corticosteroids in the last 6 months for RA activity Treated with anakinra, abatacept, or tocilizumab in the last 6 months Treated with rituximab in the last 12 months Treated with an investigational RA drug in the last 6 months Pregnant (or anticipate pregnancy during the study period) or lactating women Absence of documentation in the medical record of clinical remission for the last 6 months Unwilling to discontinue anti-TNF agent Absence of documentation of negative tuberculin skin test, negative QuantiFERON-TB Gold test, or treatment for latent tuberculosis prior to starting treatment with the anti-TNF agent Treatment of solid malignancy or non-melanoma skin cancer within the past 5 years, or any history of melanoma or hematologic or lymphoproliferative malignancy Absence of documentation of age-appropriate cancer screening at the time of randomization Absence of documentation of negative hepatitis B serologies, absence of completion of treatment for chronic hepatitis B, or absence of suppressive antiviral treatment Unable to provide informed consent Anticipate not being available or able to comply with the schedule of study visits", "candidate_expression": "((Anticipate not being available or able to comply with the schedule of study visits) AND (DMARD) AND (Pregnant) AND (QuantiFERON-TB Gold test negative) AND (RA) AND (RA drug investigational in the last 6 months) AND (Unable to provide informed consent) AND (abatacept) AND (anakinra) AND (anti-TNF agent) AND (cancer screening age-appropriate at the time of randomization) AND (certolizumab) AND (change in the last 6 months) AND (corticosteroids in the last 6 months intramuscular intravenous) AND (discontinue Unwilling) AND (golimumab) AND (hematologic) AND (lactating) AND (lymphoproliferative malignancy) AND (melanoma) AND (non-melanoma skin cancer) AND (prednisone greater than 10 mg daily in the last 6 months) AND (prednisone greater than 5 mg daily in the last 3 months) AND (pregnancy anticipate during the study period) AND (rituximab in the last 12 months) AND (solid malignancy) AND (tocilizumab) AND (treatment) AND (treatment prior to starting treatment with the anti-TNF agent) AND (treatment with the anti-TNF agent) AND (tuberculosis latent) AND (women) AND NOT (clinical remission for the last 6 months) AND NOT (tuberculin skin test negative) AND NOT (hepatitis B serologies negative) AND NOT (chronic hepatitis B) AND NOT (suppressive antiviral treatment))"}
{"candidate_id": "LLM07099", "doc_id": "NCT02536976_inc", "case_bucket": "or", "source_criterion": "Aged 25-80 at screening. Subjects older than 80 will be allowed at the discretion of the PI. Ambulatory (defined as able to ambulate at least 10 meters, with or without assistance). Clinical Diagnosis of PD based on the United Kingdom Brain Bank diagnostic criteria for PD. At least 8 micturitions per 24 hours and At least 3 urgency episodes per 3-day diary. A MoCA score between 19 and 28 (inclusive) at screening. For those on cognitive enhancers (donepezil, rivastigmine, memantine, galantamine) a MoCA score between 19 and 29 (inclusive) at screening. Provide informed consent to participate in the study and understand that they may withdraw their consent at any time without prejudice to their future medical care. Be cognitively capable, in the opinion of investigator, to understand and provide such informed consent. Be cognitively capable to complete the required questionnaires and assessments, OR have a care partner who is willing and capable to assist them in the completion of these tasks. Be on a stable regimen of antiparkinson's medications at least 30 days prior to screening, and be expected to remain on a stable dose for the duration of the study. If taking cognitive enhancers (donepezil, rivastigmine, memantine, galantamine), must be on stable dose at least 30 days prior to screening, and be expected to remain on a stable dose for the duration of the study.", "candidate_expression": "((Aged 25-80) AND (Ambulatory) AND (Be cognitively capable to complete the required questionnaires and assessments, OR have a care partner who is willing and capable to assist them in the completion of these tasks) AND (Be cognitively capable, in the opinion of investigator, to understand and provide such informed consent) AND (MoCA score between 19 and 28) AND (MoCA score between 19 and 29) AND (PD) AND (Provide informed consent to participate in the study and understand that they may withdraw their consent at any time without prejudice to their future medical care) AND (United Kingdom Brain Bank diagnostic criteria) AND (antiparkinson's medications at least 30 days prior to screening) AND (cognitive enhancers) AND (cognitive enhancers stable dose at least 30 days prior to screening) AND (donepezil) AND (galantamine) AND (memantine) AND (micturitions At least 8 per 24 hours) AND (rivastigmine) AND (urgency episodes At least 3 per 3-day diary.))"}
{"candidate_id": "LLM07100", "doc_id": "NCT03185130_inc", "case_bucket": "or", "source_criterion": "Age 10 to 65 years Temperature less than 100.4 F Normal neurologic exam and normal mental status", "candidate_expression": "((Age 10 to 65 years) AND (Temperature less than 100.4 F) AND (mental status) AND (neurologic exam Normal normal))"}
```
