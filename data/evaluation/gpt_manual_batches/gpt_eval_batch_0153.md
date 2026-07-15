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
{"candidate_id": "LLM03801", "doc_id": "NCT02056626_exc", "case_bucket": "or", "source_criterion": "abnormal renal function currently pregnant, or trying to become pregnant being treated with a beta-blocker use of illicit drugs", "candidate_expression": "((abnormal renal function) AND (beta-blocker) AND (currently) AND (illicit drugs) AND (treated) AND (trying to become) AND ((pregnant)))"}
{"candidate_id": "LLM03802", "doc_id": "NCT02621541_exc", "case_bucket": "or", "source_criterion": "vulnerable study subjects such as described in Finnish law concerning clinical studies (disabled, children, pregnant or breast-feeding women, prisoners) will not be included.", "candidate_expression": "((Finnish law concerning clinical studies) AND (breast-feeding) AND (children) AND (disabled) AND (pregnant) AND (prisoners) AND (vulnerable) AND (women))"}
{"candidate_id": "LLM03803", "doc_id": "NCT02256943_inc", "case_bucket": "or", "source_criterion": "Healthy Male >7 Metabolic Equivalents Written informed consent Chronic pain syndrome Drug abuse Alcohol abuse Suspicion of neurologic dysfunction at tested sites Ongoing treatment with antidepressants Ongoing treatment with analgesics Pretreatment with any CYP3A inducers or inhibitors Known allergy to tested drugs Elevated eye pressure Obstructive uropathy Heart disease Pulmonary disease Neurological disease Psychiatric illness", "candidate_expression": "((>7) AND (Alcohol abuse) AND (CYP3A inducers) AND (CYP3A inhibitors) AND (Chronic pain syndrome) AND (Drug abuse) AND (Elevated eye pressure) AND (Healthy) AND (Heart disease) AND (Male) AND (Metabolic Equivalents) AND (Neurological disease) AND (Obstructive uropathy) AND (Ongoing) AND (Pretreatment) AND (Psychiatric illness) AND (Pulmonary disease) AND (Suspicion) AND (Written informed consent) AND (allergy) AND (analgesics) AND (antidepressants) AND (neurologic dysfunction) AND (tested drugs) AND (tested sites) AND (treatment))"}
{"candidate_id": "LLM03804", "doc_id": "NCT02566863_exc", "case_bucket": "or", "source_criterion": "patient's refusal contraindications to dexmedetomidine diseases/drugs that influence on autonomic nervous system activity", "candidate_expression": "((contraindications) AND (dexmedetomidine) AND (influence on autonomic nervous system activity) AND (patient's refusal) AND ((diseases) OR (drugs)))"}
{"candidate_id": "LLM03805", "doc_id": "NCT01912651_exc", "case_bucket": "or", "source_criterion": "current or recent (within one week of surgery) systemic antibiotic use, intolerance to both clindamycin and cephalexin, discovery of a persistent cutaneous malignancy at the site of the defect following the reconstructive procedure and previous reconstruction at the site of the skin/soft-tissue defect.", "candidate_expression": "((cephalexin) AND (clindamycin) AND (following the reconstructive procedure) AND (reconstructive procedure) AND (site of the defect) AND (the reconstructive procedure) AND (within one week of surgery) AND ((antibiotic) OR (intolerance) OR (persistent cutaneous malignancy)) AND ((current) OR (recent)))"}
{"candidate_id": "LLM03806", "doc_id": "NCT02416869_inc", "case_bucket": "other", "source_criterion": "Healthy patients (ASA I) Bilateral symmetrically impacted lower third molars according to Pel-Gregory's and Winter's classification", "candidate_expression": "((ASA) AND (Bilateral symmetrically impacted lower third molars) AND (Healthy patients) AND (I) AND (Pel-Gregory's and Winter's classification))"}
{"candidate_id": "LLM03807", "doc_id": "NCT02015494_inc", "case_bucket": "other", "source_criterion": "Males and females aged 18-40 years of age at the time of vaccination in good health as determined by medical history, physical exam, laboratory assessments and the clinical judgment of the Principal Investigator Able to provide informed consent indicating that they understand the purpose of this study and are willing to adhere to the procedures described in this protocol If the subject is a female of childbearing potential, she must use adequate contraceptive precautions (e.g., intrauterine contraceptive device, oral contraceptives or other equivalent hormonal contraception) for 2 months prior to vaccination and continue to use such precautions for a minimum of three months after vaccination. She must also have a negative urine pregnancy test within 24 hours prior to receiving study vaccine. Women at least one year post-menopausal or surgically sterile will not be considered of childbearing potential. Willing to receive the unlicensed vaccine given as an IM injection Willing to provide multiple blood specimens collected by venipuncture", "candidate_expression": "((IM injection) AND (If the subject is a female of childbearing potential, she must use adequate contraceptive precautions (e.g., intrauterine contraceptive device, oral contraceptives or other equivalent hormonal contraception) for 2 months prior to vaccination and continue to use such precautions for a minimum of three months after vaccination. She must also have a negative urine pregnancy test within 24 hours prior to receiving study vaccine. Women at least one year post-menopausal or surgically sterile will not be considered of childbearing potential.) AND (Males) AND (age 18-40 years) AND (aged 18-40 years) AND (females) AND (good health) AND (laboratory assessments) AND (medical history) AND (physical exam) AND (the clinical judgment of the Principal Investigator) AND (vaccine))"}
{"candidate_id": "LLM03808", "doc_id": "NCT02649114_inc", "case_bucket": "other", "source_criterion": "satisfying DSM-V criteria for ED and for half of the patients in addition have a history of childhood trauma.", "candidate_expression": "((DSM-V criteria) AND (ED) AND (childhood trauma) AND (history) AND (satisfying))"}
{"candidate_id": "LLM03809", "doc_id": "NCT03216447_exc", "case_bucket": "or", "source_criterion": "Patient has previously received or is receiving an organ transplant other than a liver. Patient currently requires dialysis Recipient or donor is known to be seropositive for human immunodeficiency virus (HIV) Patient has received a liver transplant from a non-heart beating donor Patient who is HCV negative has received an HCV positive (HCV RNA by PCR or HCV antibody) donor liver Patient who is HbsAg negative has received an HbsAg positive (HBV DNA by PCR or HBV antibody) donor liver Patient has received a liver transplant from a decrease donor > 70 years of age Patient has a current malignancy or a history of malignancy (within the past 5 years), except hepatocellular carcinoma within UCSF Criteria and basal or non-metastatic squamous cell carcinoma of skin that has been treated successfully. Patient is hemodynamically unstable on POD 15", "candidate_expression": "((HBV DNA) AND (HBV antibody) AND (HCV RNA) AND (HCV antibody) AND (HCV negative) AND (HCV positive) AND (HIV) AND (HbsAg negative) AND (HbsAg positive) AND (PCR) AND (POD 15) AND (Recipient) AND (UCSF Criteria) AND (age > 70 years) AND (basal cell carcinoma of skin) AND (dialysis) AND (donor) AND (donor heart beating) AND (donor liver) AND (hemodynamically unstable) AND (hepatocellular carcinoma) AND (history of malignancy within the past 5 years) AND (human immunodeficiency virus seropositive) AND (liver transplant) AND (malignancy) AND (organ transplant liver) AND (squamous cell carcinoma of skin non-metastatic))"}
{"candidate_id": "LLM03810", "doc_id": "NCT01261832_inc", "case_bucket": "other", "source_criterion": "Acute Myocardial Infarction Undergoing Primary percutaneous coronary intervention.", "candidate_expression": "((Acute Myocardial Infarction) AND (Primary percutaneous coronary intervention))"}
{"candidate_id": "LLM03811", "doc_id": "NCT03464552_exc", "case_bucket": "or", "source_criterion": "A known allergy to Celecoxib, aspirin or another NSAID. Active peptic ulceration or gastrointestinal bleeding. Inflammatory bowel disease. Congestive heart failure (NYHA II-IV). Established ischemic heart disease, peripheral arterial disease and/or cerebrovascular disease. History of neurologic deficit. Known hepatic or renal impairment. Pregnancy. Breast-feeding. Post-hysterectomy. Bleeding disorders. Drug abuse. Cervical and vaginal infection.", "candidate_expression": "((Active) AND (Bleeding disorders) AND (Breast-feeding) AND (Congestive heart failure) AND (Drug abuse) AND (History) AND (II-IV) AND (Inflammatory bowel disease) AND (NYHA) AND (Post) AND (Pregnancy) AND (allergy) AND (another) AND (hysterectomy) AND (neurologic deficit) AND ((cerebrovascular disease) OR (ischemic heart disease) OR (peripheral arterial disease)) AND ((Celecoxib) OR (NSAID) OR (aspirin)) AND ((hepatic impairment) OR (renal impairment)) AND ((Cervical infection) OR (vaginal infection)) AND ((gastrointestinal bleeding) OR (peptic ulceration)))"}
{"candidate_id": "LLM03812", "doc_id": "NCT01735955_exc", "case_bucket": "or", "source_criterion": "Patient has been permanently discontinued from nilotinib treatment in the parent study due to unacceptable toxicity, non-compliance to study procedures, withdrawal of consent or any other reason Patient has participated in a Novartis sponsored combination trial where nilotinib was dispensed in combination with another study medication and patient is still receiving combination therapy Patients who are currently receiving treatment with any medications that have the potential to prolong the QT interval or inducing Torsade de Pointes and the treatment cannot be either safely discontinued at least one week prior to nilotinib treatment or switched to a different medication prior to start of nilotinib treatment and for the duration of the study Pregnant or nursing (lactating) women, where pregnancy is defined as the state of a female after conception and until the termination of gestation, confirmed by a positive hcG laboratory test. Women of child-bearing potential, defined as all women physiologically capable of becoming pregnant, unless they are using highly effective methods of contraception during the study and for 30 days after the final dose of nilotinib.", "candidate_expression": "((Novartis sponsored) AND (Women) AND (any medications) AND (child-bearing potential) AND (contraception) AND (currently) AND (discontinued) AND (during the study) AND (for 30 days after the final dose of nilotinib) AND (hcG laboratory test) AND (highly effective methods) AND (lactating) AND (nilotinib) AND (participated in a combination trial) AND (permanently) AND (physiologically capable of becoming pregnant) AND (positive) AND (study procedures) AND (the final dose of nilotinib) AND (treatment) AND (unless) AND (withdrawal) AND (women) AND ((any other reason) OR (consent) OR (non-compliance) OR (unacceptable toxicity)) AND ((have the potential to prolong the QT interval) OR (inducing Torsade de Pointes)) AND ((Pregnant) OR (nursing)))"}
{"candidate_id": "LLM03813", "doc_id": "NCT03355469_inc", "case_bucket": "or", "source_criterion": "Male or female >40 and <70 years old. Has a body mass index >27 and <47 kg/m2. Not diagnosed with Type 2 diabetes. Not currently engaged in > 60 min/wk of exercise Meet at least 3 of 5 National Cholesterol Education Adult Treatment Panel III Increased waist circumference (=102 cm in men; =88 cm in women) Elevated triglycerides (=150 mg/dl), or on medication for treating the condition Reduced HDL-cholesterol (<40mg/dl in men, <50 mg/dl in women), or on medication for treating the condition High blood pressure (=130 mmHg systolic or =85mmHg diastolic), or on medication for treating the condition Elevated fasting glucose (=100 mg/dl), or on medication for treating the condition", "candidate_expression": "((Elevated fasting glucose =100 mg/dl) AND (HDL-cholesterol Reduced) AND (High blood pressure) AND (National Cholesterol Education Adult Treatment Panel III at least 3 of 5) AND (blood pressure) AND (body mass index >27 and <47 kg/m2) AND (fasting glucose Elevated) AND (medication for treating) AND (medication for treating HDL-cholesterol High) AND (medication for treating triglycerides) AND (old >40 and <70 years) AND (triglycerides Elevated =150 mg/dl) AND (waist circumference Increased) AND NOT (engaged in exercise currently > 60 min/wk) AND NOT (Type 2 diabetes) AND ((Male) OR (female)) AND ((men =102 cm) OR (women =88 cm)) AND ((men <40mg/dl) OR (women <50 mg/dl)) AND ((=130 mmHg systolic) OR (=85mmHg diastolic)))"}
{"candidate_id": "LLM03814", "doc_id": "NCT02303171_exc", "case_bucket": "other", "source_criterion": "Women with systemic lupus erythematosus (SLE) Women with active thromboembolic disorders Women with history of previous thromboembolic disorders", "candidate_expression": "((Women) AND (active) AND (history) AND (previous) AND (systemic lupus erythematosus (SLE)) AND (thromboembolic disorders))"}
{"candidate_id": "LLM03815", "doc_id": "NCT00319748_exc", "case_bucket": "or", "source_criterion": "Had/have the following prior/concurrent therapy: Systemic corticosteroids (oral or injectable) within 7 days of first dose of 852A (topical or inhaled steroids are allowed) Investigational drugs/agents within 14 days of first dose of 852A Immunosuppressive therapy, including cytotoxic agents within 14 days of first dose of 852A (nitrosoureas within 30 days of first dose) Drugs known to induce QT interval prolongation and/or induce Torsades de pointes unless best available drug required to treat life-threatening conditions Radiotherapy within 3 weeks of the first dose of 852A Hematopoietic cell transplantation within 4 weeks of first dose of 852A Evidence of active infection within 3 days of first dose of 852A Active fungal infection or pulmonary infiltrates (prior treated disease stable for 2 weeks is allowable) Cardiac ischemia, cardiac arrhythmias or congestive heart failure uncontrolled by medication History of, or clinical evidence of, a condition which, in the opinion of the investigator, could confound the results of the study or put the subject at undue risk Uncontrolled intercurrent or chronic illness Active autoimmune disease requiring immunosuppressive therapy within 30 days Active coagulation disorder not controlled with medication Pregnant or lactating Concurrent malignancy (if in remission, at least 5 years disease free) except for localized (in-situ) disease, basal carcinomas and cutaneous squamous cell carcinomas that have been adequately treated Any history of brain metastases or any other active central nervous system (CNS) disease", "candidate_expression": "((852A) AND (Active) AND (Concurrent) AND (Drugs known to induce QT interval prolongation) AND (Drugs known to induce Torsades de pointes) AND (Evidence) AND (Hematopoietic cell transplantation) AND (Investigational drugs/agents) AND (Radiotherapy) AND (Systemic corticosteroids) AND (Uncontrolled) AND (active) AND (active infection) AND (adequately treated) AND (are allowed) AND (at least 5 years) AND (coagulation disorder) AND (controlled with medication) AND (could confound the results of the study or put the subject at undue risk a condition which) AND (cytotoxic agents) AND (disease free) AND (except for) AND (for 2 weeks) AND (history of) AND (immunosuppressive therapy) AND (in remission) AND (is allowable) AND (malignancy) AND (not) AND (prior treated disease) AND (stable) AND (uncontrolled by medication) AND (within 14 days of first dose) AND (within 3 days of first dose) AND (within 3 weeks of the first dose) AND (within 30 days) AND (within 30 days of first dose) AND (within 4 weeks of first dose) AND (within 7 days of first dose) AND ((Immunosuppressive therapy) OR (nitrosoureas)) AND ((fungal infection) OR (pulmonary infiltrates)) AND ((Cardiac ischemia) OR (cardiac arrhythmias) OR (congestive heart failure)) AND ((History) OR (clinical evidence)) AND ((chronic illness) OR (intercurrent illness)) AND ((autoimmune disease) OR (requiring)) AND ((inhaled steroids) OR (topical steroids)) AND ((Pregnant) OR (lactating)) AND ((basal carcinomas) OR (cutaneous squamous cell carcinomas) OR (localized (in-situ) disease)) AND ((any other central nervous system (CNS) disease) OR (brain metastases)) AND ((injectable) OR (oral)))"}
{"candidate_id": "LLM03816", "doc_id": "NCT03154931_exc", "case_bucket": "or", "source_criterion": "Suicidal patients and/or severe automutilation behavior and/or psychotic symptoms and/or lack of event memory.", "candidate_expression": "((severe) AND ((Suicidal) OR (automutilation behavior) OR (lack of event memory) OR (psychotic symptoms)))"}
{"candidate_id": "LLM03817", "doc_id": "NCT03275584_inc", "case_bucket": "other", "source_criterion": "Adult patient being referred for clinically indicated positron emission tomography myocardial perfusion imaging at the Centre hospitalier de l'Université de Montréal", "candidate_expression": "((Adult) AND (Centre hospitalier de l'Université de Montréal) AND (positron emission tomography myocardial perfusion imaging clinically indicated))"}
{"candidate_id": "LLM03818", "doc_id": "NCT03026465_exc", "case_bucket": "or", "source_criterion": "Target lesion located in the left main stem STEMI Restenosis Cardiogenic shock Malignancies or other comorbid conditions with life expectancy less than 12 months or that may result in protocol noncompliance Known allergy to the study medications (probucol, sirolimus, zotarolimus) Pregnancy (present, suspected, or planned)", "candidate_expression": "((Cardiogenic shock) AND (Malignancies) AND (Pregnancy) AND (Restenosis) AND (STEMI) AND (Target lesion) AND (allergy) AND (comorbid conditions) AND (left main stem) AND (less than 12 months) AND (life expectancy) AND (may) AND (other) AND (planned) AND (present) AND (probucol) AND (protocol noncompliance) AND (sirolimus) AND (study medications) AND (suspected) AND (zotarolimus))"}
{"candidate_id": "LLM03819", "doc_id": "NCT02162433_exc", "case_bucket": "or", "source_criterion": "Known allergy or hypersensitivity reaction to dexmedetomidine Organ dysfunction (renal/hepatic failure or leukemia) Cardiac disease (congenital or acquired) Airway or thoracic malformation Cerebral palsy Hypotonia Need for premedication Current/recent upper respiratory infection (within four weeks prior to the surgery) Asthma Allergy or intolerance to clonidine Non-English speaking parents/patients.", "candidate_expression": "((Asthma) AND (Cardiac disease) AND (Cerebral palsy) AND (Hypotonia) AND (Organ dysfunction) AND (clonidine) AND (dexmedetomidine) AND (premedication Need for) AND (surgery) AND (upper respiratory infection within four weeks prior to the surgery) AND ((allergy) OR (hypersensitivity)) AND ((acquired) OR (congenital)) AND ((Airway malformation) OR (thoracic malformation)) AND ((Current) OR (recent)) AND ((Allergy) OR (intolerance)) AND ((Non-English speaking parents) OR (Non-English speaking patients)) AND ((hepatic failure) OR (leukemia) OR (renal failure)))"}
{"candidate_id": "LLM03820", "doc_id": "NCT01908465_inc", "case_bucket": "or", "source_criterion": "Irritable Bowel Syndrome (IBS) (ROME III criteria): subtype with diarrhea or mixed form age 18-65 years", "candidate_expression": "((18-65 years) AND (Irritable Bowel Syndrome (IBS)) AND (ROME III criteria) AND (age) AND ((diarrhea) OR (mixed form)))"}
{"candidate_id": "LLM03821", "doc_id": "NCT03615508_exc", "case_bucket": "other", "source_criterion": "NA", "candidate_expression": "(EMPTY)"}
{"candidate_id": "LLM03822", "doc_id": "NCT02167022_inc", "case_bucket": "other", "source_criterion": "1. Age: 12 to 36 months of age (The diagnosis of CP is often uncertain under the age of 12 months. The cutoff at 36 months is to have a population of young children when the brain is most \"plastic\" and most susceptible to reorganization). 2. Diagnosis: Diagnosis of spastic CP confirmed by a pediatric neurologist or pediatric rehabilitation specialist. 3. Etiology: The insult to the central nervous system that caused the motor dysfunction must have occurred during gestation or within one year after birth independent of gestational age. 4. Disease severity level: Gross Motor Function Classification System (GMFCS) levels I, II and III.", "candidate_expression": "((Age 12 to 36 months of age) AND (Gross Motor Function Classification System (GMFCS) levels I, II and III) AND (one year after birth) AND (spastic CP))"}
{"candidate_id": "LLM03823", "doc_id": "NCT02504203_exc", "case_bucket": "other", "source_criterion": "NA", "candidate_expression": "(EMPTY)"}
{"candidate_id": "LLM03824", "doc_id": "NCT02970773_exc", "case_bucket": "or", "source_criterion": "Any anti-coagulation therapy (apart from rivaroxaban for second objective) Hypersensitivity or allergy to factor Xa inhibitors Acute bacterial endocarditis Bleeding disorder Clinically relevant active bleeding Gastrointestinal ulcer or tumor Hepatic dysfunction with increased bleeding risk Renal failure / patients undergoing dialysis Pregnancy and breast feeding Gastrectomy, biliopancreatic diversion, resection or re-routing of small intestines Feeding tube Recent blood donation Abnormalities of laboratory values: alanine-aminotransferase (ALAT), aspartate-aminotransferase (ASAT), gamma-glutamyl transferase (gammaGT), alkalic phosphatase (AP), bilirubin, amylase, lipase, cystatin C, creatinine, white blood cell count, haemoglobin, platelet count, prothrombin time, aPTT, fibrinogen, thrombin time, factors II,V,VII and X Use of therapeutic or recreational drugs influencing plasmatic coagulation", "candidate_expression": "((ALAT) AND (AP) AND (ASAT) AND (Abnormalities) AND (Acute bacterial endocarditis) AND (Bleeding disorder) AND (Feeding tube) AND (Gastrectomy) AND (Gastrointestinal tumor) AND (Gastrointestinal ulcer) AND (Hepatic dysfunction) AND (Hypersensitivity) AND (Pregnancy and breast feeding) AND (Renal failure) AND (aPTT) AND (active bleeding) AND (alanine-aminotransferase) AND (alkalic phosphatase) AND (allergy) AND (amylase) AND (anti-coagulation therapy) AND (apart from) AND (aspartate-aminotransferase) AND (biliopancreatic diversion) AND (bilirubin) AND (bleeding risk) AND (blood donation) AND (creatinine) AND (cystatin C) AND (dialysis) AND (factor Xa inhibitors) AND (factors II) AND (factors V) AND (factors VII) AND (factors X) AND (fibrinogen) AND (gamma-glutamyl transferase) AND (gammaGT) AND (haemoglobin) AND (increased) AND (lipase) AND (platelet count) AND (prothrombin time,) AND (re-routing) AND (resection) AND (rivaroxaban) AND (small intestines) AND (thrombin time) AND (white blood cell count))"}
{"candidate_id": "LLM03825", "doc_id": "NCT00959569_inc", "case_bucket": "or", "source_criterion": "end diastolic diameter >60 mm and/or an ejection fraction <50% written informed consent age >18 years", "candidate_expression": "((<50%) AND (>18 years) AND (>60 mm) AND (age) AND (written informed consent) AND ((ejection fraction) OR (end diastolic diameter)))"}
```
