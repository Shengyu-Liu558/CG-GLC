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
{"candidate_id": "LLM02226", "doc_id": "NCT02499185_exc", "case_bucket": "other", "source_criterion": "Ongoing acute kidney injury Stage 2/3 History of kidney transplant", "candidate_expression": "((Stage 2/3) AND (acute kidney injury) AND (kidney transplant History))"}
{"candidate_id": "LLM02227", "doc_id": "NCT01088750_inc", "case_bucket": "other", "source_criterion": "Stage IA or IIA disease Not specified No prior therapy", "candidate_expression": "(EMPTY)"}
{"candidate_id": "LLM02228", "doc_id": "NCT03234816_inc", "case_bucket": "other", "source_criterion": "full term singleton pregnant women Scheduled for elective Cesarean Delivery Aged between 18 and 40 years", "candidate_expression": "((Aged between 18 and 40 years) AND (Cesarean Delivery Scheduled for elective) AND (pregnant full term singleton) AND (women))"}
{"candidate_id": "LLM02229", "doc_id": "NCT02968342_exc", "case_bucket": "or", "source_criterion": "Medical history of chronic psychiatric disease Medical conditions associated with female sexual dysfunction; cardiovascular disease, uncontrolled chronic HT (hypertension) ,DM (diabetes mellitus), History of gynecologic surgery, female gynecological cancer ( breast, ovarian, uterine, cervical) Medications associated with female sexual dysfunction; Antidepressants opiates, beta blockers, Antiepileptics ( gabapentin, topiramate,phenytoin) benzodiazepines", "candidate_expression": "((History) AND (Medical conditions) AND (Medications) AND (associated with female sexual dysfunction) AND (chronic) AND (chronic psychiatric disease) AND (diabetes mellitus) AND (female sexual dysfunction) AND (history) AND (hypertension) AND (uncontrolled) AND ((DM) OR (HT) OR (cardiovascular disease) OR (female gynecological cancer) OR (gynecologic surgery)) AND ((breast) OR (cervical) OR (ovarian) OR (uterine)) AND ((Antidepressants) OR (Antiepileptics) OR (benzodiazepines) OR (beta blockers) OR (opiates)) AND ((gabapentin) OR (phenytoin) OR (topiramate)))"}
{"candidate_id": "LLM02230", "doc_id": "NCT02334722_exc", "case_bucket": "or", "source_criterion": "No known history of seizure activity. Pregnant or breastfeeding. Renal dysfunction (CrCl < 30ml/min). Beck's Depression Inventory (BDI) =14 Allergy to levetiracetam.", "candidate_expression": "((Allergy) AND (Beck's Depression Inventory (BDI) =14) AND (CrCl < 30ml/min) AND (Pregnant) AND (Renal dysfunction) AND (breastfeeding) AND (levetiracetam) AND (seizure activity history))"}
{"candidate_id": "LLM02231", "doc_id": "NCT02777424_inc", "case_bucket": "or", "source_criterion": "Patient with spontaneous intracranial hemorrhage or traumatic intracranial hemorrhage or patient requiring neurological surgery Coagulation disorder defined by PT less than 60%", "candidate_expression": "((Coagulation disorder) AND (PT less than 60%) AND (neurological surgery requiring) AND (spontaneous intracranial hemorrhage) AND (traumatic intracranial hemorrhage))"}
{"candidate_id": "LLM02232", "doc_id": "NCT03066440_exc", "case_bucket": "or", "source_criterion": "Age > 18 Years Physician discretion Septic or hypovolemic shock Signs of life-threatening cerebral edema or multi-organ failure upon presentation to the emergency room or pediatric intensive care unit Enrollment time more than 1 hr since arrival to emergency room or PICU Pregnancy", "candidate_expression": "((Age > 18 Years) AND (Enrollment more than 1 hr since arrival to emergency room or PICU) AND (Pregnancy) AND ((emergency room) OR (pediatric intensive care unit)) AND ((PICU) OR (emergency room)) AND ((Septic shock) OR (hypovolemic shock)) AND ((cerebral edema) OR (multi-organ failure)))"}
{"candidate_id": "LLM02233", "doc_id": "NCT02918409_exc", "case_bucket": "other", "source_criterion": "NA", "candidate_expression": "(EMPTY)"}
{"candidate_id": "LLM02234", "doc_id": "NCT03364036_exc", "case_bucket": "or", "source_criterion": "Previous exposure to drugs such as fingolimod, natalizumab, alemtuzumab, mitoxantrone and ocrelizumab. Positive hepatitis C or hepatitis B surface antigen test and/or hepatits B core antibody test for immunoglobulin G (IgG) and/or immunoglobulin M (IgM). Current or previous history of immune deficiency disorders including a positive human immunodeficiency virus (HIV) result. Currently receiving immunosuppressive or myelosuppressive therapy with, for example, monoclonal antibodies, methotrexate, cyclophosphamide, cyclosporine or azathioprine, or chronic use of corticosteroids. History of tuberculosis , presence of active tuberculosis, or latent tuberculosis Evidence or suspect of Progressive Multifocal Leukoencephalopathy (PML) in Magnetic Resonance Imaging (MRI). Active malignancy or history of malignancy. Other protocol defined exclusion criteria could apply.", "candidate_expression": "((Magnetic Resonance Imaging (MRI)) AND (Progressive Multifocal Leukoencephalopathy (PML)) AND (drugs Previous) AND (human immunodeficiency virus (HIV) positive) AND (immune deficiency disorders) AND ((hepatitis B surface antigen test) OR (hepatitis C surface antigen test) OR (hepatits B core antibody test)) AND ((immunoglobulin G (IgG)) OR (immunoglobulin M (IgM))) AND ((Current) OR (previous history)) AND ((immunosuppressive therapy) OR (myelosuppressive therapy)) AND ((azathioprine) OR (corticosteroids chronic use) OR (cyclophosphamide) OR (cyclosporine) OR (methotrexate) OR (monoclonal antibodies)) AND ((tuberculosis History) OR (tuberculosis active) OR (tuberculosis latent)) AND ((Evidence) OR (suspect)) AND ((malignancy Active) OR (malignancy history)) AND ((alemtuzumab) OR (fingolimod) OR (mitoxantrone) OR (natalizumab) OR (ocrelizumab)))"}
{"candidate_id": "LLM02235", "doc_id": "NCT02314559_inc", "case_bucket": "other", "source_criterion": "All patients subjected to deep sedation in ambulant care, having a colonoscopy ASA 1-3", "candidate_expression": "((1-3) AND (ASA) AND (ambulant) AND (colonoscopy) AND (deep sedation))"}
{"candidate_id": "LLM02236", "doc_id": "NCT02743598_exc", "case_bucket": "or", "source_criterion": "Personal or family history of pancreatitis Medullary thyroid carcinoma (MTC) or Multiple Endocrine Neoplasia Syndrome Type 2 (MEN 2) Gastroparesis Allergy to liraglutide or any of the active ingredients in liraglutide or other GLP-1 analogue Weight loss drugs other than metformin Type 1 diabetes mellitus or diabetic ketoacidosis Known major cognitive deficit dementia, history of head trauma with loss of consciousness >30 min, history of stroke, current central nervous system (CNS) disorder such as seizures or opportunistic CNS infection Renal insufficiency defined as creatinine clearance < 60 mL/min Active opportunistic infections Pregnancy or breastfeeding Unstable cardiovascular disease with hospitalization within 1 year for acute coronary syndrome Decompensated heart failure Substance abuse Active alcohol or opioid substitution therapy Serious or unstable medical or psychological conditions that would compromise the subject's safety for successful participation", "candidate_expression": "((Allergy) AND (Decompensated heart failure) AND (GLP-1 analogue) AND (Gastroparesis) AND (MEN 2) AND (MTC) AND (Medullary thyroid carcinoma) AND (Multiple Endocrine Neoplasia Syndrome Type 2) AND (Pregnancy or breastfeeding) AND (Renal insufficiency) AND (Substance abuse) AND (Type 1 diabetes mellitus) AND (Weight loss) AND (acute coronary syndrome within 1 year) AND (alcohol) AND (central nervous system disorder) AND (cognitive deficit) AND (creatinine clearance < 60 mL/min) AND (dementia) AND (diabetic ketoacidosis) AND (head trauma) AND (hospitalization) AND (liraglutide) AND (loss of consciousness >30 min) AND (opioid substitution therapy) AND (opportunistic CNS infection) AND (opportunistic infections Active) AND (pancreatitis) AND (seizures) AND (stroke) AND NOT (metformin))"}
{"candidate_id": "LLM02237", "doc_id": "NCT02557412_inc", "case_bucket": "or", "source_criterion": "Diagnosis of dyslipidemia: The existence of a previous clinical diagnostic of dyslipidemia associated with lipid-lowering therapy. It is also considered patients who have an altered analytical, using the following cutoffs: total cholesterol = 200 mg / dl, triglycerides = 180 mg / dl, HDL-cholesterol = 40 mg / dl or LDL-cholesterol = 150 mg / dl. Lipid-lowering treatment and diet, stable in the last month. A concentration of LDL-cholesterol above 100 mg / dl, in the month prior to inclusion. An apnea-hypopnea index between 5-30 h-1", "candidate_expression": "((= 150 mg / dl) AND (= 180 mg / dl) AND (= 200 mg / dl) AND (= 40 mg / dl) AND (LDL-cholesterol) AND (Lipid-lowering diet) AND (Lipid-lowering treatment) AND (above 100 mg / dl) AND (altered analytical) AND (apnea-hypopnea index) AND (between 5-30 h-1) AND (dyslipidemia) AND (in the last month) AND (in the month prior to inclusion) AND (inclusion) AND (lipid-lowering therapy) AND (stable) AND ((HDL-cholesterol) OR (LDL-cholesterol) OR (total cholesterol) OR (triglycerides)))"}
{"candidate_id": "LLM02238", "doc_id": "NCT02150590_exc", "case_bucket": "or", "source_criterion": "unstable condition, COPD exacerbation mild (GOLD 1) or very severe COPD (GOLD 4) requirement for oxygen therapy at low altitude residence hypoventilation pulmonary hypertension more than mild or unstable cardiovascular disease use of drugs that affect respiratory center drive internal, neurologic or psychiatric disease that interfere with protocol compliance including current heavy smoking (>20 cigarettes per day), inability to perform 6 min walk test. previous intolerance to moderate altitude (<2600m). exposure to altitudes >1500m for >2 days within the last 4 weeks before the study. pregnant or nursing patients", "candidate_expression": "((COPD exacerbation) AND (COPD mild) AND (COPD very severe) AND (GOLD 1)) AND (GOLD 4) AND (cardiovascular disease) AND (condition unstable) AND (hypoventilation) AND (internal disease) AND (intolerance altitude) AND (neurologic disease) AND (oxygen therapy) AND (pregnant or nursing patients) AND (psychiatric disease) AND (pulmonary hypertension more than mild unstable) AND (smoking heavy >20 cigarettes per day) AND NOT (6 min walk test))"}
{"candidate_id": "LLM02239", "doc_id": "NCT03068897_exc", "case_bucket": "or", "source_criterion": "Not available for follow-up Pregnant or breast-feeding Chronic pain syndrome defined as use of any analgesic medication on a daily or near-daily basis Allergic to or intolerant of investigational medications Contra-indications to non-steroidal anti-inflammatory drugs: 1) history of hypersensitivity to NSAIDs or aspirin 2) active or history of peptic ulcer disease, chronic dyspepsia, or active or history of gastrointestinal bleed 3) Severe heart failure (NYHA 2 or worse) 4) hypertension (JNC7 stage 2 or worse) 5) Chronic kidney disease 3 or worse 6) Current use of anti-coagulants 7) Hepatitis 8) Alcoholism Contra-indications to muscle relaxants: 1) Concurrent use of centrally acting opioids; 2) Renal impairment; 3) Liver abnormality including cirrhosis or elevated enzymes 4) Use of any of the following medications: fluvoxamine, fluoroquinolones, amiodarone, mexiletine, propafenone, verapamil, cimetidine, famotidine, acyclovir, ticlopidine, oral contraceptive pills", "candidate_expression": "((2 or worse) AND (Alcoholism) AND (Allergic) AND (Chronic kidney disease) AND (Chronic pain syndrome) AND (Concurrent) AND (Contra-indications) AND (Current) AND (Hepatitis) AND (JNC7 stage) AND (Liver abnormality) AND (NSAIDs) AND (NYHA) AND (Pregnant) AND (Renal impairment) AND (Severe) AND (active) AND (acyclovir) AND (amiodarone) AND (analgesic medication) AND (anti-coagulants) AND (any) AND (aspirin) AND (breast-feeding) AND (centrally acting opioids) AND (chronic dyspepsia) AND (cimetidine) AND (cirrhosis) AND (elevated enzymes) AND (famotidine) AND (fluoroquinolones) AND (fluvoxamine) AND (gastrointestinal bleed) AND (heart failure) AND (history) AND (hypersensitivity) AND (hypertension) AND (intolerant) AND (investigational medications) AND (mexiletine) AND (muscle relaxants) AND (non-steroidal anti-inflammatory drugs) AND (on a daily basis) AND (on a near-daily basis) AND (oral contraceptive pills) AND (peptic ulcer disease) AND (propafenone) AND (ticlopidine) AND (verapamil))"}
{"candidate_id": "LLM02240", "doc_id": "NCT02437045_inc", "case_bucket": "or", "source_criterion": "Bloodstream infection with Enterobacter spp., Serratia marcescens, Providencia spp., Morganella morganii or Citrobacter freundii (i.e. likely AmpC-producer), and susceptibility to 3rd generation cephalosporins (i.e. ceftriaxone, cefotaxime or ceftazidime), meropenem and piperacillin-tazobactam from at least one blood culture draw. This will be determined in accordance with laboratory methods and susceptibility breakpoints defined by protocols used in the recruiting site laboratories.. No more than 72 hours has elapsed since the first positive blood culture collection. Patient is aged 18 years and over (>=21y in Singapore).", "candidate_expression": "((3rd generation cephalosporins () AND (>=21y) AND (Bloodstream infection) AND (No more than 72 hours since the first positive blood culture collection) AND (aged) AND (at least one) AND (blood culture) AND (blood culture collection) AND (meropenem) AND (piperacillin-tazobactam) AND (positive) AND (the first positive blood culture collection) AND ((cefotaxime) OR (ceftazidime) OR (ceftriaxone)) AND ((18 years and over) OR (Singapore)) AND ((Citrobacter freundii) OR (Enterobacter spp.) OR (Morganella morganii) OR (Providencia spp.) OR (Serratia marcescens)))"}
{"candidate_id": "LLM02241", "doc_id": "NCT02287259_exc", "case_bucket": "or", "source_criterion": "don't have Diabetes and abnormal metabolism of sugar not noticed as bipolar disorder have an organic brain disease pregnant or breastfeeding women don't have heart disease have actively suicidal thought(Suicidal ideation score of MADRS is 6) who are judged by the investigator to should be excluded from the study", "candidate_expression": "((Suicidal ideation score of MADRS 6) AND (actively suicidal thought) AND (judged by the investigator to should be excluded from the study) AND (organic brain disease) AND (women) AND NOT (heart disease) AND NOT (bipolar disorder noticed) AND ((breastfeeding) OR (pregnant)) AND ((Diabetes) OR (abnormal metabolism of sugar)))"}
{"candidate_id": "LLM02242", "doc_id": "NCT02469610_inc", "case_bucket": "other", "source_criterion": "Thoracoscopic surgery candidate. Over 18 years old. No known allergy to Bupivacaine. Patient is able to read understand and singe an inform consent.", "candidate_expression": "((Bupivacaine) AND (Thoracoscopic surgery candidate) AND (able to read) AND (old Over 18 years old) AND (singe) AND (understand) AND NOT (allergy))"}
{"candidate_id": "LLM02243", "doc_id": "NCT03541980_inc", "case_bucket": "other", "source_criterion": "Any patient age 4-16 years with sickle cell disease who presents the Pediatric ER with acute sickle cell pain crisis with a pain of 6/10 or higher", "candidate_expression": "((4-16 years) AND (6/10 or higher) AND (Pediatric ER) AND (acute sickle cell pain crisis) AND (age) AND (pain) AND (sickle cell disease))"}
{"candidate_id": "LLM02244", "doc_id": "NCT00502567_inc", "case_bucket": "or", "source_criterion": "histologically confirmed metastatic cancer that is not amenable to surgery or radiation therapy with curative intent measurable lesion by CT or other techniques according to RECIST", "candidate_expression": "((CT) AND (confirmed) AND (histologically) AND (measurable lesion) AND (metastatic cancer) AND (not amenable) AND ((radiation therapy) OR (surgery)))"}
{"candidate_id": "LLM02245", "doc_id": "NCT02567214_inc", "case_bucket": "other", "source_criterion": "Age > 50 years Smoking history > 10 packs/year FEV1 30 - 79% of predicted and FEV1/FVC < 70% (GOLD 2-3) FRC > 120 % predicted Borg dyspnea score > 3 during the 3-min constant rate shuttle walking test at V3", "candidate_expression": "((2-3) AND (3-min constant rate shuttle walking test) AND (30 - 79% of predicted) AND (< 70%) AND (> 10 packs/year) AND (> 120 % predicted) AND (> 3) AND (> 50 years) AND (Age) AND (Borg dyspnea score) AND (FEV1) AND (FEV1/FVC) AND (FRC) AND (GOLD) AND (Smoking history) AND (V3))"}
{"candidate_id": "LLM02246", "doc_id": "NCT02357654_inc", "case_bucket": "or", "source_criterion": "women undergoing IVF/ICSI or frozen embryo transfers (FET) that less than 40 years old.", "candidate_expression": "((ICSI) AND (IVF) AND (frozen embryo transfers (FET)) AND (old less than 40 years) AND (women))"}
{"candidate_id": "LLM02247", "doc_id": "NCT03278548_exc", "case_bucket": "other", "source_criterion": "NA", "candidate_expression": "(EMPTY)"}
{"candidate_id": "LLM02248", "doc_id": "NCT02970773_exc", "case_bucket": "or", "source_criterion": "Any anti-coagulation therapy (apart from rivaroxaban for second objective) Hypersensitivity or allergy to factor Xa inhibitors Acute bacterial endocarditis Bleeding disorder Clinically relevant active bleeding Gastrointestinal ulcer or tumor Hepatic dysfunction with increased bleeding risk Renal failure / patients undergoing dialysis Pregnancy and breast feeding Gastrectomy, biliopancreatic diversion, resection or re-routing of small intestines Feeding tube Recent blood donation Abnormalities of laboratory values: alanine-aminotransferase (ALAT), aspartate-aminotransferase (ASAT), gamma-glutamyl transferase (gammaGT), alkalic phosphatase (AP), bilirubin, amylase, lipase, cystatin C, creatinine, white blood cell count, haemoglobin, platelet count, prothrombin time, aPTT, fibrinogen, thrombin time, factors II,V,VII and X Use of therapeutic or recreational drugs influencing plasmatic coagulation", "candidate_expression": "((ALAT) AND (AP) AND (ASAT) AND (Abnormalities) AND (Acute bacterial endocarditis) AND (Bleeding disorder) AND (Feeding tube) AND (Hepatic dysfunction) AND (Pregnancy and breast feeding) AND (active bleeding) AND (anti-coagulation therapy) AND (apart from) AND (bleeding risk) AND (blood donation) AND (factor Xa inhibitors) AND (gammaGT) AND (increased) AND (rivaroxaban) AND (small intestines) AND (white blood cell count) AND ((Gastrointestinal tumor) OR (Gastrointestinal ulcer)) AND ((Renal failure) OR (dialysis)) AND ((Gastrectomy) OR (biliopancreatic diversion)) AND ((re-routing) OR (resection)) AND ((Hypersensitivity) OR (allergy)) AND ((aPTT) OR (alanine-aminotransferase) OR (alkalic phosphatase) OR (amylase) OR (aspartate-aminotransferase) OR (bilirubin) OR (creatinine) OR (cystatin C) OR (factors II) OR (factors V) OR (factors VII) OR (factors X) OR (fibrinogen) OR (gamma-glutamyl transferase) OR (haemoglobin) OR (lipase) OR (platelet count) OR (prothrombin time,) OR (thrombin time)))"}
{"candidate_id": "LLM02249", "doc_id": "NCT02379156_inc", "case_bucket": "other", "source_criterion": "Duration of SCI =1 year; Level of SCI C3-T1, AIS A & B; Age between 18 and 65 years.", "candidate_expression": "((AIS A & B) AND (Age between 18 and 65 years) AND (Level of SCI C3-T1) AND (SCI =1 year))"}
{"candidate_id": "LLM02250", "doc_id": "NCT02437084_exc", "case_bucket": "or", "source_criterion": "Less than 30 yrs of age or > 65 yrs of age Any significant co-morbidities, such as active heart, kidney, or liver diseases, accelerated or malignant hypertension, heart failure, severe anemia.", "candidate_expression": "((> 65 yrs) AND (Less than 30 yrs) AND (accelerated) AND (active) AND (age) AND (co-morbidities) AND (diseases heart) AND (diseases kidney) AND (heart failure) AND (hypertension) AND (liver diseases) AND (malignant) AND (severe anemia) AND (significant))"}
```
