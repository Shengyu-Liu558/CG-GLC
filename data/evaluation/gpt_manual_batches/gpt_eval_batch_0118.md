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
{"candidate_id": "LLM02926", "doc_id": "NCT03369379_exc", "case_bucket": "or", "source_criterion": "Those subjects with previous use of vitamin D. Known subjects with renal, liver, calcium metabolism disorders, malabsorption disorders, known neoplasms. Subjects with serum calcium levels equal to or greater than 10.2 mg / dl.", "candidate_expression": "((serum calcium levels equal to or greater than 10.2 mg / dl) AND (vitamin D previous use) AND ((calcium metabolism disorders) OR (disorders liver) OR (disorders renal) OR (malabsorption disorders) OR (neoplasms)))"}
{"candidate_id": "LLM02927", "doc_id": "NCT03185130_inc", "case_bucket": "or", "source_criterion": "Age 10 to 65 years Temperature less than 100.4 F Normal neurologic exam and normal mental status", "candidate_expression": "((10 to 65 years) AND (Age) AND (Normal) AND (Temperature) AND (less than 100.4 F) AND (mental status) AND (neurologic exam) AND (normal))"}
{"candidate_id": "LLM02928", "doc_id": "NCT01401335_inc", "case_bucket": "other", "source_criterion": "100 orphans/vulnerable youth aged 15 to 25 will be recruited through their participation at the day care center, on a voluntary basis.", "candidate_expression": "(EMPTY)"}
{"candidate_id": "LLM02929", "doc_id": "NCT02739295_inc", "case_bucket": "other", "source_criterion": "Toxic epidermal necrolysis with SCORTEN 1 to 5 at admission", "candidate_expression": "((SCORTEN 1 to 5 at admission) AND (Toxic epidermal necrolysis))"}
{"candidate_id": "LLM02930", "doc_id": "NCT02406495_exc", "case_bucket": "or", "source_criterion": "Is not a habitual wearer of Avaira sphere lenses Has a CL prescription outside the range of the available parameters of the study lenses. Has a spectacle cylinder ≥1.00D of cylinder in either eye. Has a history of not achieving comfortable CL wear (5 days per week; > 8 hours/day) Has contact lens best corrected distance vision worse than 20/25 (0.10 logMAR) in either eye. Presence of clinically significant (grade 2-4) anterior segment abnormalities Presence of ocular or systemic disease or need of medications which might interfere with contact lens wear. Slit lamp findings that would contraindicate contact lens wear such as: Pathological dry eye or associated findings Pterygium, pinguecula, or corneal scars within the visual axis Neovascularization > 0.75 mm in from of the limbus Giant papillary conjunctivitis (GCP) worse than grade 1 Anterior uveitis or iritis (past or present) Seborrheic eczema, Seborrheic conjunctivitis History of corneal ulcers or fungal infections Poor personal hygiene Has a known history of corneal hypoesthesia (reduced corneal sensitivity) Has aphakia, keratoconus or a highly irregular cornea. Has Presbyopia or has dependence on spectacles for near work over the contact lenses. Has undergone corneal refractive surgery. Is participating in any other type of eye related clinical or research study", "candidate_expression": "((Avaira sphere lenses) AND (CL prescription outside the range of the available parameters of the study lenses) AND (Giant papillary conjunctivitis (GCP) worse than grade 1) AND (Neovascularization > 0.75 mm in from of the limbus) AND (Poor personal hygiene) AND (Seborrheic conjunctivitis) AND (Seborrheic eczema) AND (Slit lamp findings) AND (anterior segment abnormalities clinically significant grade 2-4) AND (clinically significant) AND (contact lens best corrected distance vision worse than 20/25 in either eye worse than 0.10 logMAR in either eye) AND (contraindicate contact lens) AND (corneal hypoesthesia history) AND (corneal refractive surgery) AND (corneal ulcers History) AND (fungal infections History) AND (might interfere with contact lens wear) AND (need of medications) AND (reduced corneal sensitivity) AND (spectacle cylinder ≥1.00D) AND NOT (comfortable CL wear history 5 days per week > 8 hours/day) AND ((need of medications) OR (ocular disease) OR (systemic disease)) AND ((Pathological dry eye) OR (associated findings)) AND ((Pterygium) OR (corneal scars within the visual axis) OR (pinguecula)) AND ((Anterior uveitis) OR (iritis)) AND ((past) OR (present)) AND ((aphakia) OR (highly irregular cornea) OR (keratoconus)) AND ((Presbyopia) OR (dependence on spectacles for near work)))"}
{"candidate_id": "LLM02931", "doc_id": "NCT02481518_exc", "case_bucket": "other", "source_criterion": "Prior treatment with cisplatin before randomization Uncontrolled concurrent disease Pregnancy", "candidate_expression": "((Pregnancy) AND (Uncontrolled) AND (before randomization) AND (cisplatin) AND (concurrent disease) AND (randomization))"}
{"candidate_id": "LLM02932", "doc_id": "NCT02609425_exc", "case_bucket": "or", "source_criterion": "Any patient with esophageal cancer who is not deemed a surgical candidate or who is not deemed a candidate for the Ivor Lewis technique of esophagectomy (with intrathoracic anastomosis). Any patient less than 18 years of age", "candidate_expression": "((age less than 18 years) AND (esophageal cancer) AND (esophagectomy Ivor Lewis technique with intrathoracic anastomosis) AND (intrathoracic anastomosis) AND (surgical) AND (NOT (candidate)))"}
{"candidate_id": "LLM02933", "doc_id": "NCT01000155_exc", "case_bucket": "or", "source_criterion": "Subjects with hemoglobin SC or SB+ thalassemia Subjects on chronic transfusion program Subjects who have received RBC transfusions cannot have >15% adult hemoglobin Known positive status for HIV, active hepatitis B or hepatitis C Pregnant or breast feeding women Individuals with a history of malignancy are ineligible except for the following circumstances. Individuals with a history of malignancy are eligible if they have been disease-free for at least 5 years and are deemed by the investigator to be at low risk for recurrence of that malignancy. Individuals with the following cancer are eligible if diagnosed and adequately treated within the past 5 years: cervical or breast cancer in situ, and basal cell or squamous cell carcinoma of the skin Subjects with a history of thrombosis or other reason (other than sickle cell disease) for enhanced thrombotic risk Subjects with unresolved infections Severe or uncontrolled medical conditions that could compromise study participation Subjects on fetal hemoglobin inducing agents Subjects on any other experimental treatment within 90 days of the first dose of study drug or who have not recovered from the side effects of such therapy Known allergic reaction to a histone deacetylase inhibitor Subjects who have received valproic acid for treatment of epilepsy within 30 days of enrollment Subjects who have received any HDAC inhibitors other than valproic acid", "candidate_expression": "((HDAC inhibitors) AND (HIV) AND (Pregnant) AND (SB+ thalassemia chronic) AND (Severe or uncontrolled medical conditions that could compromise study participation) AND (Subjects on any other experimental treatment within 90 days of the first dose of study drug or who have not recovered from the side effects of such therapy) AND (allergic reaction) AND (are eligible) AND (basal cell carcinoma of the skin) AND (breast cancer in situ) AND (breast feeding) AND (cervical cancer in situ) AND (deemed by the investigator) AND (disease-free for at least 5 years) AND (epilepsy within 30 days of enrollment) AND (fetal hemoglobin inducing agents fetal) AND (hemoglobin SC) AND (hepatitis B active) AND (hepatitis C active) AND (histone deacetylase inhibitor) AND (infections unresolved) AND (malignancy history) AND (medical conditions compromise study participation) AND (recurrence of that malignancy low risk) AND (squamous cell carcinoma of the skin) AND (that malignancy) AND (thrombosis history) AND (thrombotic) AND (thrombotic risk enhanced risk) AND (transfusion program chronic) AND (treated adequately within the past 5 years diagnosed adequately treated) AND (treatment) AND (valproic acid) AND (women) AND NOT (sickle cell disease) AND NOT (RBC transfusions >15% adult hemoglobin) AND NOT (valproic acid))"}
{"candidate_id": "LLM02934", "doc_id": "NCT00305097_exc", "case_bucket": "or", "source_criterion": "Any condition/illness that may affect the study outcomes or would make participation potentially harmful such as pregnancy or breastfeeding, diabetes mellitus, heart disease, stroke, hypertension, malabsorption syndromes, GERD, a history of ulcer, according to a detailed medical history. Abnormal hepatic function (liver function test > twice the normal range), abnormal renal function (creatinine > 1.1 mg/dl), fasting plasma glucose in the diabetic range (>/= 126 mg/dl), or blood pressure > 140/90 mmHg. Present alcoholism or drug abuse or use of medications that could interfere with the treatment including bronchodilators, quinolone antibiotics, monoamine oxidase inhibitors, anxiolytics, ranitidine, corticosteroids, growth hormone, antihypertensives.", "candidate_expression": "((> 1.1 mg/dl) AND (> 140/90 mmHg) AND (> twice the normal range) AND (>/= 126 mg/dl) AND (Abnormal) AND (GERD) AND (abnormal) AND (alcoholism) AND (antihypertensives) AND (anxiolytics) AND (blood pressure) AND (breastfeeding) AND (bronchodilators) AND (corticosteroids) AND (creatinine) AND (diabetes mellitus) AND (drug abuse) AND (fasting plasma glucose) AND (growth hormone) AND (heart disease) AND (hepatic function) AND (history of) AND (hypertension) AND (illness that may affect the study outcomes) AND (illness that would make participation potentially harmful) AND (in the diabetic range) AND (liver function test) AND (malabsorption syndromes) AND (medical history) AND (medications that could interfere with the treatment) AND (monoamine oxidase inhibitors) AND (pregnancy) AND (quinolone antibiotics) AND (ranitidine) AND (renal function) AND (stroke) AND (ulcer))"}
{"candidate_id": "LLM02935", "doc_id": "NCT02940912_exc", "case_bucket": "or", "source_criterion": "Atypical Parkinsonian Syndromes Parkinson's disease with hallucinations Parkinson's disease with impulse Control disorder (ICD) Parkinson's disease already treated with APOMORPHINE pump or justifying the use of the pump continuously day and night Another obvious severe disease explaining insomnia Exclusion for monitoring difficulties (mutation, insufficient motivation, priority associated pathology in care) Patient unwilling to accept a pump Patient not accepting polysomnography and multiple sleep latency test Patient with health problems or a skin disease precluding continuous subcutaneous infusion Female parturient or nursing Cardiac dysrhythmia precluding treatment with domperidone or apomorphine (increased QTc = 440 ms in men, QTc = 450 ms in women) antiemetic neuroleptics Tetrabenazine Excessive alcohol consumption Hypersensitivity to apomorphine or one of the excipients Respiratory Depression Hepatic impairment Intellectual Disability Dementia", "candidate_expression": "((APOMORPHINE) AND (Cardiac dysrhythmia) AND (Dementia) AND (Excessive alcohol consumption) AND (Female) AND (Hepatic impairment) AND (Hypersensitivity) AND (Intellectual Disability) AND (Parkinson's disease) AND (Parkinsonian Syndromes Atypical) AND (QTc = 440 ms) AND (QTc = 450 ms) AND (Respiratory Depression) AND (Tetrabenazine) AND (antiemetic neuroleptics) AND (hallucinations) AND (impulse Control disorder (ICD)) AND (insomnia) AND (multiple sleep latency test not accepting) AND (not) AND (polysomnography not accepting) AND (pump unwilling to accept) AND (severe disease) AND (unwilling) AND NOT (continuous subcutaneous infusion) AND ((health problems) OR (skin disease)) AND ((nursing) OR (parturient)) AND ((apomorphine) OR (domperidone)) AND ((men) OR (women)) AND ((apomorphine) OR (excipients)))"}
{"candidate_id": "LLM02936", "doc_id": "NCT03519568_exc", "case_bucket": "or", "source_criterion": "the history or family history of anaphylaxis, convulsion, epilepsy, encephalopathy and psychosis the history of severe inoculation allergies patients with immunodeficiency and malignant tumors during the treatment period, receiving immunosuppressive therapy (oral steroid) or HIV due to low immunity, or family members have congenital immune disease Nonspecific immunoglobulin was injected within one month temperature=37.1<U+2103> and infectious diseases the history of thrombocytopenia or other thrombocytopenia with a definite diagnosis respiratory disease, acute infection or chronic disease activity period severe cardiovascular disease, liver and kidney disease, and complications of diabetes infectious, suppurative and allergic dermatosis other conditions that may affect the evaluation of the trail any serious adverse events that have a causal relationship with the inoculation of the upper dose of the vaccine the abnormality of 4 levels (local, systemic adverse reactions and vital signs) was judged to be related to vaccination other new standards of exclusion criteria for first needle other conditions that may affect the evaluation of the trail", "candidate_expression": "((=37.1<U+2103>) AND (Nonspecific immunoglobulin) AND (adverse events) AND (diabetes) AND (during the treatment period) AND (family members) AND (history) AND (inoculation allergies) AND (inoculation of the upper dose of the vaccine) AND (oral steroid) AND (other) AND (serious) AND (severe) AND (within one month) AND ((immunodeficiency) OR (malignant tumors)) AND ((HIV) OR (congenital immune disease) OR (immunosuppressive therapy)) AND ((family history) OR (history)) AND ((infectious diseases) OR (temperature)) AND ((thrombocytopenia)) AND ((anaphylaxis) OR (convulsion) OR (encephalopathy) OR (epilepsy) OR (psychosis)) AND ((acute infection) OR (chronic disease activity period) OR (respiratory disease)) AND ((cardiovascular disease) OR (complications) OR (kidney disease) OR (liver disease)) AND ((allergic dermatosis) OR (infectious dermatosis) OR (suppurative dermatosis)))"}
{"candidate_id": "LLM02937", "doc_id": "NCT03373318_inc", "case_bucket": "other", "source_criterion": "Adult patients (> 18 years) scheduled for cardiopulmonary bypass surgery with Glomerular Filtration Rate (GFR) greater than or equal to 60 and left ventricular ejection fraction greater than or equal to 40%", "candidate_expression": "((Adult) AND (Glomerular Filtration Rate (GFR) greater than or equal to 60) AND (cardiopulmonary bypass surgery scheduled for) AND (left ventricular ejection fraction greater than or equal to 40%) AND (years > 18 years))"}
{"candidate_id": "LLM02938", "doc_id": "NCT02427295_exc", "case_bucket": "or", "source_criterion": "Severe co-morbid illness such as untreatable other malignancy and/or active infections. Pregnant or lactating women Hypersensitivity to Sandostatin or any component of the formulation.", "candidate_expression": "((Hypersensitivity) AND (Severe) AND (active) AND (co-morbid illness) AND (other) AND (untreatable) AND (women) AND ((Pregnant) OR (lactating)) AND ((Sandostatin) OR (component of the formulation)) AND ((infections) OR (malignancy)))"}
{"candidate_id": "LLM02939", "doc_id": "NCT01352598_exc", "case_bucket": "other", "source_criterion": "NA", "candidate_expression": "(EMPTY)"}
{"candidate_id": "LLM02940", "doc_id": "NCT02573168_exc", "case_bucket": "or", "source_criterion": "Patients posing a serious suicidal risk and/or violence as judged by the investigator; Delirium Dementia Amnestic and other cognitive disorder; Patients with a history of hypothyroidism unless taking a stable dose of thyroid medication and asymptomatic or euthyroid for 6 months; Patients who meet DSM-IV-TR criteria for any significant current substance abuse; hepatic insufficiency (three times the upper limit of normal (ULN) for aspartate aminotransferase (AST) and/or alanine aminotransferase (ALT)); liver transplant recipient; cirrhosis of the liver; malignancy (except basal cell carcinoma) and/or chemotherapy within 1 year prior to screening; malignancy more than 1 year prior to screening must have been local and without metastasis and/or recurrence, and if treated with chemotherapy, without nervous system complications; significant unstable medical condition or life threatening disease with anticipated survival of less than 6 months; need for therapies that may obscure the results of treatment and/or of the study Participation in another clinical trial within 30 days of the screening visit; Anticipated inability to attend scheduled study visits; Patients who in the judgment of the Investigator may be unreliable or uncooperative with the evaluation procedure outlined in this protocol; Patients with a history of prior pharmacogenomic testing; Any change in psychotropic medication (including change in dosage) between screening and baseline; Patients who are known to be pregnant or lactating; Patients with a history of gastric bypass surgery.", "candidate_expression": "((ALT) AND (AST) AND (Anticipated inability to attend scheduled study visits) AND (DSM-IV-TR) AND (Delirium) AND (Dementia) AND (Participation in another clinical trial within 30 days of the screening visit) AND (Patients who are known to be pregnant or lactating) AND (Patients with a history of prior pharmacogenomic testing) AND (gastric bypass surgery) AND (hypothyroidism) AND (psychotropic medication) AND (substance abuse) AND NOT (basal cell carcinoma) AND NOT (thyroid medication) AND ((suicidal risk) OR (violence)) AND ((alanine aminotransferase) OR (aspartate aminotransferase)) AND ((cirrhosis of the liver) OR (hepatic insufficiency) OR (liver transplant)) AND ((chemotherapy within 1 year prior to screening) OR (malignancy) OR (malignancy more than 1 year local)) AND ((metastasis) OR (recurrence)) AND ((life threatening disease) OR (medical condition unstable)) AND ((Amnestic disorder) OR (cognitive disorder)))"}
{"candidate_id": "LLM02941", "doc_id": "NCT02366819_exc", "case_bucket": "or", "source_criterion": "Previous or concurrent malignancy, except for adequately treated basal cell or squamous cell skin cancer, in situ cervical cancer, or any other cancer for which the patient has been previously treated and the lifetime recurrence risk is less than 30% Inflammatory bowel disease that is uncontrolled or on active treatment (Crohn's disease, ulcerative colitis) Diarrhea, grade 1 or greater by the National Cancer Institute Common Terminology Criteria for Adverse Events (NCI-CTCAE, version [v] 4.0) Neuropathy, grade 2 or greater by NCI-CTCAE, v 4.0 Serious underlying medical or psychiatric illnesses that would, in the opinion of the treating physician, substantially increase the risk for complications related to treatment Active uncontrolled bleeding Pregnancy or breastfeeding Major surgery within 4 weeks Patients with any polymorphism in UGT1A1 other than *1 or *28 (e.g, *6) will be allowed and treated as in the *28/*28 dosing group", "candidate_expression": "((Active) AND (Diarrhea) AND (Inflammatory bowel disease) AND (Major surgery) AND (NCI-CTCAE, v 4.0) AND (NCI-CTCAE, version [v] 4.0) AND (National Cancer Institute Common Terminology Criteria for Adverse Events) AND (Neuropathy) AND (Pregnancy or breastfeeding) AND (adequately treated) AND (bleeding) AND (cervical cancer) AND (except) AND (grade 1 or greater) AND (grade 2 or greater) AND (in situ) AND (malignancy) AND (uncontrolled) AND (within 4 weeks) AND ((treatment) OR (uncontrolled)) AND ((Crohn's disease) OR (ulcerative colitis)) AND ((Previous) OR (concurrent)) AND ((basal cell skin cancer) OR (squamous cell skin cancer)))"}
{"candidate_id": "LLM02942", "doc_id": "NCT01680081_inc", "case_bucket": "or", "source_criterion": "Men and women patients, with age ranging 40-80. Suspected coronary artery disease who are supposed to undergo invasive coronary angiography with appropriate clinical indications Patients who are willing to sign the informed consent form", "candidate_expression": "((Patients who are willing to sign the informed consent form) AND (age ranging 40-80) AND (coronary artery disease Suspected) AND (invasive coronary angiography supposed to undergo) AND ((Men) OR (women)))"}
{"candidate_id": "LLM02943", "doc_id": "NCT02939209_inc", "case_bucket": "scope", "source_criterion": "Age 18-65 scheduled to receive ISB and general anesthesia as a day surgery patient for rotator cuff repair and acromioplasty, as a part of planned routine care", "candidate_expression": "((18-65) AND (Age) AND (ISB) AND (acromioplasty) AND (day surgery) AND (general anesthesia) AND (rotator cuff repair))"}
{"candidate_id": "LLM02944", "doc_id": "NCT02118467_inc", "case_bucket": "other", "source_criterion": "Age greater than or equal to 18 years old Requirement for vasoactive drugs via a central venous catheter for the treatment of shock. Shock will be defined as mean arterial pressure less than 70 mmHg or systolic blood pressure less than 100 mmHg despite administration of at least 1000 mL of crystalloid or 500 mL of colloid, unless there is an elevation in the central venous pressure to > 12 mmHg or in the pulmonary artery occlusion pressure to > 14 mmHg coupled with signs of tissue hypoperfusion (e.g. altered mental state, mottled skin, urine output < 0.5 mL/kg body weight for one hour, or a serum lactate level of > 2 mmol per liter).", "candidate_expression": "((Age greater than or equal to 18 years old) AND (central venous catheter) AND (mean arterial pressure less than 70 mmHg) AND (shock) AND (systolic blood pressure less than 100 mmHg) AND (vasoactive drugs))"}
{"candidate_id": "LLM02945", "doc_id": "NCT03221231_exc", "case_bucket": "or", "source_criterion": "Currently dependent on any substance other than cannabis, alcohol or nicotine; History of any major internal disease (including diabetes, cardiovascular disease, lung disease, liver or kidney disease); An active or any history of neurological disorder, including but not limited to seizure disorder, epilepsy, stroke, neurological disease, cognitive impairment, head trauma with prolonged loss of consciousness (>10 minutes), or migraine headaches; An active or a history of a psychiatric disorder including, but not limited to, depression, schizophrenia, bipolar disorder, anxiety, or other psychiatric disorders; Asthma; Known hypersensitivity or allergy to n-acetylcysteine, or receiving chronic therapy with medication that could interact adversely with n-acetylcysteine within 30 days prior to randomization (i.e., nitroglycerin, ACE inhibitors or antihypertensive drugs, anti-coagulants); Exclusion criteria for MRI: having metal in the body and/or having claustrophobia", "candidate_expression": "((ACE inhibitors) AND (Asthma) AND (Exclusion criteria for MRI) AND (alcohol) AND (allergy) AND (anti-coagulants) AND (antihypertensive drugs) AND (anxiety) AND (bipolar disorder) AND (cannabis) AND (cardiovascular disease) AND (chronic therapy within 30 days prior to randomization) AND (claustrophobia) AND (cognitive impairment) AND (dependent) AND (depression) AND (diabetes) AND (epilepsy) AND (head trauma) AND (history) AND (hypersensitivity) AND (kidney disease) AND (liver disease active) AND (lung disease) AND (major internal disease) AND (metal in the body) AND (migraine headaches active) AND (n-acetylcysteine) AND (neurological disease) AND (neurological disorder) AND (nicotine) AND (nitroglycerin) AND (prolonged loss of consciousness >10 minutes) AND (psychiatric disorder) AND (psychiatric disorders other) AND (schizophrenia) AND (seizure disorder) AND (stroke) AND (substance))"}
{"candidate_id": "LLM02946", "doc_id": "NCT02627521_inc", "case_bucket": "other", "source_criterion": "Accepted for CABG surgery Treatment with Ticagrelor within 48 hours", "candidate_expression": "((Accepted for) AND (CABG surgery) AND (Ticagrelor) AND (Treatment) AND (within 48 hours))"}
{"candidate_id": "LLM02947", "doc_id": "NCT02562456_exc", "case_bucket": "or", "source_criterion": "severe behavioral issues presence of fistula or abscess near the selected tooth presence of pulp exposure in the selected tooth presence of mobility in the selected tooth", "candidate_expression": "((abscess) AND (behavioral issues severe) AND (fistula) AND (mobility selected tooth) AND (pulp exposure selected tooth))"}
{"candidate_id": "LLM02948", "doc_id": "NCT02330705_exc", "case_bucket": "or", "source_criterion": "Advanced male factor infertility. Polycystic ovary syndrome (PCOS) as defined by the Rotterdam criteria. Endometriosis. Tubal disease. Uterine abnormalities or myoma. Previous uterine surgery. Metabolic or hormonal abnormalities.", "candidate_expression": "((Advanced) AND (Endometriosis) AND (Metabolic abnormalities) AND (Polycystic ovary syndrome (PCOS)) AND (Previous) AND (Rotterdam criteria) AND (Tubal disease) AND (Uterine abnormalities) AND (hormonal abnormalities) AND (male factor infertility) AND (myoma) AND (uterine surgery))"}
{"candidate_id": "LLM02949", "doc_id": "NCT03196843_exc", "case_bucket": "or", "source_criterion": "Patients with a history of any other malignancy. Concomitant treatment with any other anticancer therapy. Patient have contraindication to chemotherapy(eg.uncontrolled coronarism and heart failure; History of myocardial infarction within the past 6 months, Chronic obstructive pulmonary, uncontrolled epileptic attack and other disease that investigator consider it unsuitable for the chemotherapy)", "candidate_expression": "((Chronic obstructive pulmonary) AND (Concomitant) AND (History) AND (anticancer therapy) AND (any other) AND (chemotherapy) AND (contraindication) AND (coronarism) AND (disease) AND (epileptic attack) AND (heart failure) AND (history) AND (malignancy) AND (myocardial infarction) AND (other) AND (treatment) AND (uncontrolled) AND (unsuitable for the chemotherapy) AND (within the past 6 months))"}
{"candidate_id": "LLM02950", "doc_id": "NCT01978028_inc", "case_bucket": "or", "source_criterion": "Patients with chronic heart failure of New York Heart Association Class II or III, a left ventricular ejection fraction of = 40% for patients in NYHA class II or = 45% for patients in NYHA class III, a hemoglobin level at the screening visit between 9.5-13.5 g/dl, and iron deficiency, which is defined as serum ferritin level < 100µg/l or between 100 and 299 µg/l, when transferring saturation is < 20%. Age =18 years Obtained informed consent Stable pharmacological therapy during the last 4 weeks (with the exception of diuretics)", "candidate_expression": "((Age =18 years) AND (NYHA class II) AND (NYHA class III) AND (New York Heart Association Class II or III) AND (Obtained informed consent) AND (chronic heart failure) AND (hemoglobin level at the screening visit between 9.5-13.5 g/dl) AND (iron deficiency) AND (left ventricular ejection fraction) AND (pharmacological therapy Stable during the last 4 weeks) AND (serum ferritin level < 100µg/l between 100 and 299 µg/l) AND (transferring saturation < 20%) AND NOT (diuretics))"}
```
