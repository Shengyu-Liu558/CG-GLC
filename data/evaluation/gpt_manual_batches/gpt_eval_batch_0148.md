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
{"candidate_id": "LLM03676", "doc_id": "NCT00343668_inc", "case_bucket": "or", "source_criterion": "Pathologically proven unresectable adenocarcinoma of stomach With uni-dimensionally measurable disease (at least longest diameter 2 cm on conventional CT scan, x-ray or physical examination, or 1cm on spiral CT scan) Age 18 to 70 years old Estimated life expectancy of more than 3 months ECOG performance status of 2 or lower Adequate bone marrow function(absolute neutrophil count [ANC] ≥1,500/µL, hemoglobin ≥9.0 g/dL,and platelets ≥100,000/µL) Adequate kidney function (serum creatinine < 1.5 mg/dL) Adequate liver function (serum total bilirubin < 2 times the upper normal limit (UNL); serum transaminases levels <3 times [<5 times for patients with liver metastasis] UNL) No prior chemotherapy but prior adjuvant chemotherapy finished at least 6 months before enrollment was allowed. (but, prior adjuvant chemotherapy with capecitabine or S-1 or camptothecin analogues was excluded) No prior radiation therapy for at least 4 weeks before enrollment in the study", "candidate_expression": "((Age 18 to 70 years old) AND (ECOG performance status 2 or lower) AND (Estimated life expectancy more than 3 months) AND (Pathologically proven) AND (adenocarcinoma of stomach unresectable) AND (bone marrow function Adequate) AND (disease uni-dimensionally measurable) AND (kidney function Adequate) AND (liver function Adequate) AND (longest diameter at least 1cm) AND (longest diameter at least 2 cm) AND (serum creatinine < 1.5 mg/dL) AND (serum total bilirubin < 2 times the upper normal limit (UNL)) AND (serum transaminases levels) AND NOT (chemotherapy prior) AND NOT (adjuvant chemotherapy prior at least 6 months before enrollment) AND NOT (adjuvant chemotherapy prior) AND NOT (radiation therapy prior at least 4 weeks before enrollment) AND ((absolute neutrophil count [ANC] ≥1,500/µL) OR (hemoglobin ≥9.0 g/dL) OR (platelets ≥100,000/µL)) AND ((<3 times UNL) OR (liver metastasis <5 times UNL)) AND ((S-1) OR (camptothecin analogues) OR (capecitabine)) AND ((conventional CT scan) OR (physical examination) OR (spiral CT scan) OR (x-ray)))"}
{"candidate_id": "LLM03677", "doc_id": "NCT03519568_exc", "case_bucket": "or", "source_criterion": "the history or family history of anaphylaxis, convulsion, epilepsy, encephalopathy and psychosis the history of severe inoculation allergies patients with immunodeficiency and malignant tumors during the treatment period, receiving immunosuppressive therapy (oral steroid) or HIV due to low immunity, or family members have congenital immune disease Nonspecific immunoglobulin was injected within one month temperature=37.1<U+2103> and infectious diseases the history of thrombocytopenia or other thrombocytopenia with a definite diagnosis respiratory disease, acute infection or chronic disease activity period severe cardiovascular disease, liver and kidney disease, and complications of diabetes infectious, suppurative and allergic dermatosis other conditions that may affect the evaluation of the trail any serious adverse events that have a causal relationship with the inoculation of the upper dose of the vaccine the abnormality of 4 levels (local, systemic adverse reactions and vital signs) was judged to be related to vaccination other new standards of exclusion criteria for first needle other conditions that may affect the evaluation of the trail", "candidate_expression": "((Nonspecific immunoglobulin within one month) AND (adverse events serious) AND (diabetes) AND (inoculation allergies history severe) AND (inoculation of the upper dose of the vaccine) AND (oral steroid) AND ((immunodeficiency) OR (malignant tumors)) AND ((HIV) OR (congenital immune disease family members) OR (immunosuppressive therapy)) AND ((family history) OR (history)) AND ((infectious diseases) OR (temperature =37.1<U+2103>)) AND ((thrombocytopenia history) OR (thrombocytopenia other)) AND ((anaphylaxis) OR (convulsion) OR (encephalopathy) OR (epilepsy) OR (psychosis)) AND ((acute infection) OR (chronic disease activity period) OR (respiratory disease)) AND ((cardiovascular disease severe) OR (complications) OR (kidney disease) OR (liver disease)) AND ((allergic dermatosis) OR (infectious dermatosis) OR (suppurative dermatosis)))"}
{"candidate_id": "LLM03678", "doc_id": "NCT02196285_inc", "case_bucket": "other", "source_criterion": "Male Age between 18 and 49 years old; Willing to provide name, address, telephone and other contact information in order to be contacted, whenever needed (example: in case of missing any scheduled visit, contact for confirmation of scheduling a visit, urgent safety notifications); Willing to strictly follow the study protocol; Capacity for understanding and signing in the Informed Consent Form; To understand the impossibility of participating in another clinical trial during the time of participation in the study, until 6 months after its conclusion; Intellectual level which allows to filling in the diaries for registering of symptoms at home; Willing to undergo to serological testing to HIV, HBV and HCV; Being in good health, with no significant medical history; Physical examination at screening period without clinically significant changes; Lab examination at screening period within the normal ranges, determined by the laboratory or abnormal values, grading below 1 or 2, according to medical decision.", "candidate_expression": "((Age) AND (Being in good health, with no significant medical history;) AND (Capacity for understanding and signing in the Informed Consent Form;) AND (Intellectual level which allows to filling in the diaries for registering of symptoms at home;) AND (Lab examination at screening period within the normal ranges, determined by the laboratory or abnormal values, grading below 1 or 2, according to medical decision.) AND (Male) AND (Physical examination) AND (Physical examination at screening period without clinically significant changes;) AND (To understand the impossibility of participating in another clinical trial during the time of participation in the study, until 6 months after its conclusion;) AND (Willing to provide name, address, telephone and other contact information in order to be contacted, whenever needed (example: in case of missing any scheduled visit, contact for confirmation of scheduling a visit, urgent safety notifications);) AND (Willing to strictly follow the study protocol;) AND (Willing to undergo to serological testing to HIV, HBV and HCV;) AND (at screening period) AND (between 18 and 49 years old) AND (good health) AND (screening period) AND (serological testing to HBV) AND (serological testing to HCV) AND (serological testing to HIV))"}
{"candidate_id": "LLM03679", "doc_id": "NCT00720031_inc", "case_bucket": "or", "source_criterion": "HLA-A2 melanoma patients with : either loco-regional or lymph node metastasis transit nodules not surgically resectable measurable cutaneous or visceral metastasis Patients' tumor express Melan-A/MART-1 antigen. No chemotherapy treatment (except for Deticene used before the first T cell clones infusion) or radiotherapy or immunotherapy in the last 4 weeks before infusion. No other melanoma treatment during the protocol. Life expectancy should be greater than 6 months. General state with Karnowsky greater than 80, ECOG = 0, 1 or 2. Patient should be negative for HIV and B and C hepatitis. Biological parameters at the beginning of the study: leucocytes ³ 2000 elements per mm3, hemoglobin ³ 10.5g/dl, platelets ³ 100 000 per mm3, phosphatases alcalines transaminases £ 1 time 1/2 compared to the normal. Signed informed consent", "candidate_expression": "((0, 1 or 2) AND (B hepatitis) AND (C hepatitis) AND (Deticene) AND (ECOG) AND (HIV) AND (HLA-A2) AND (Karnowsky) AND (Life expectancy) AND (MART-1 antigen) AND (Melan-A antigen) AND (No) AND (Signed informed consent) AND (at the beginning of the study) AND (before the first T cell clones infusion) AND (chemotherapy) AND (cutaneous metastasis) AND (during the protocol) AND (except for) AND (greater than 6 months) AND (greater than 80) AND (hemoglobin) AND (immunotherapy) AND (in the last 4 weeks before infusion) AND (infusion) AND (leucocytes) AND (loco-regional metastasis) AND (lymph node metastasis) AND (measurable) AND (melanoma) AND (negative) AND (not) AND (phosphatases alcalines transaminases) AND (platelets) AND (radiotherapy) AND (surgically) AND (surgically resectable) AND (the beginning of the study) AND (the first T cell clones infusion) AND (transit nodules) AND (treatment) AND (visceral metastasis) AND (£ 1 time 1/2 compared to the normal) AND (³ 10.5g/dl) AND (³ 100 000 per mm3) AND (³ 2000 elements per mm3))"}
{"candidate_id": "LLM03680", "doc_id": "NCT03217409_exc", "case_bucket": "or", "source_criterion": "Subjects with hypersensitivity reaction to Statin and Ezetimibe Subjects with severe kidney disease Subjects with HIV positive result at the screening Pregnant or breast-feeding subjects Subjects with taking any medication affecting level of LDL (Fenofibrate, Omega 3 fatty aicd etc.) Insulin-treated Subjects Other exclusions applied", "candidate_expression": "((Ezetimibe) AND (Fenofibrate) AND (HIV positive) AND (Insulin) AND (LDL) AND (Omega 3 fatty aicd) AND (Pregnant) AND (Statin) AND (affecting) AND (at the screening) AND (breast-feeding) AND (hypersensitivity) AND (kidney disease) AND (medication) AND (severe))"}
{"candidate_id": "LLM03681", "doc_id": "NCT03513874_inc", "case_bucket": "or", "source_criterion": "Type 1 diabetes according to ADA criterias <5 years. Age= 18 years and less than 70 years. Non-obese: defined as BMI less than 28 kg/m2 Positive for at least one of the anti-islet autoantibodies: GADA, IA2A, ZnT8A Fasting or postprandial plasma C-peptide more than 100 pmol/L Written informed consent from the patient or family representative.", "candidate_expression": "((Age = 18 years and less than 70 years) AND (BMI less than 28 kg/m2) AND (Fasting plasma C-peptide) AND (GADA) AND (IA2A) AND (Type 1 diabetes ADA criterias <5 years) AND (Written informed consent from the patient or family representative.) AND (ZnT8A) AND (anti-islet autoantibodies at least one) AND (postprandial plasma C-peptide) AND NOT (obese))"}
{"candidate_id": "LLM03682", "doc_id": "NCT02652572_exc", "case_bucket": "or", "source_criterion": "1. Decrease in size of the designated target ulcer(s) by ≥ 30% during the 7-day screening period 2. Cannot tolerate or comply with compression therapy. 3. An ulcer which shows signs of severe clinical infection, defined as pus oozing from the ulcer site 4. An ulcer positive for β-hemolytic streptococci upon culture 5. The ulcer has > 50% slough, significant necrotic tissue, bone, tendon, or capsule exposure or avascular ulcer beds 6. Is highly exuding (i.e. requires daily change of dressing) 7. Ankle brachial pressure index <0.65 8. Patients with active systemic infections 9. Patients with clinically significant medical conditions as determined by the investigator including renal, hepatic, hematologic, neurologic or immune disease. Examples include but are not limited to: 1. Renal insufficiency as an estimated GFR which is < 30 mL/min/1.7m2 2. Abnormal blood biochemistry defined as 3 times that of the upper limit of the normal range. 3. Hepatic insufficiency defined as total bilirubin > 2 mg/dL or serum albumin < 25 g/L 4. HbA1c > 9% 5. Hemoglobin < 10 g/dL 6. Hematocrit < 0.30 7. Platelet count < 100,000 10. Presence of an active systemic or local cancer or tumor of any kind (with the exception of non-melanoma skin cancer) 11. Patients with severe rheumatoid arthritis (with more than 20 persistently inflamed joints, or below lower normal limit blood albumin level, or evidence of bone and cartilage damage on x-ray, or inflammation in tissues other than joints) and other collagen vascular diseases. 12. Patients with active connective tissue disease 13. Treatment with systemic corticosteroids (>15 mg/day), or current immunosuppressive agents 14. Previous or current radiation therapy or likelihood to receive this therapy during study participation 15. Pregnant or nursing patients 16. Known prior inability or unavailability to complete required study visits during study participation 17. Significant peripheral edema as per investigator's discretion 18. A psychiatric condition (e.g., suicidal ideation) or chronic alcohol or drug abuse problem, determined from the patient's medical history, which, in the opinion of the investigator, may pose a threat to patient compliance 19. Use of a platelet-derived growth factor within 28 days before screening 20. Use of any investigational drug or therapy within 28 days before screening 21. Has any other factor which may, in the opinion of the investigator, compromise participation and/or follow-up in the study", "candidate_expression": "((Ankle brachial pressure index <0.65) AND (Cannot tolerate or comply with) AND (Has any other factor which may, in the opinion of the investigator, compromise participation and/or follow-up in the study) AND (HbA1c > 9%) AND (Hematocrit < 0.30) AND (Hemoglobin < 10 g/dL) AND (Hepatic insufficiency) AND (Platelet count < 100,000) AND (Pregnant) AND (Renal insufficiency) AND (Significant) AND (Treatment) AND (alcohol abuse problem) AND (as determined by the investigator) AND (as per investigator's discretion) AND (avascular ulcer beds highly exuding) AND (blood albumin level below lower normal limit) AND (blood biochemistry Abnormal 3 times that of the upper limit of the normal range) AND (bone and cartilage damage) AND (bone exposure) AND (capsule exposure) AND (change of dressing daily) AND (collagen vascular diseases) AND (compression therapy) AND (connective tissue disease active) AND (drug abuse problem) AND (estimated GFR < 30 mL/min/1.7m2) AND (hematologic disease) AND (hepatic disease) AND (highly exuding) AND (immune disease) AND (immunosuppressive agents current Previous current) AND (in the opinion of the investigator) AND (inflamed joints more than 20 persistently) AND (inflammation in tissues other than joints) AND (investigational drug) AND (investigational therapy within 28 days before screening) AND (likelihood to) AND (local cancer) AND (medical conditions clinically significant) AND (necrotic tissue) AND (neurologic disease) AND (nursing) AND (peripheral edema Significant) AND (platelet-derived growth factor within 28 days before screening) AND (pose a threat) AND (psychiatric condition) AND (pus) AND (radiation therapy) AND (renal disease) AND (rheumatoid arthritis severe) AND (serum albumin < 25 g/L) AND (severe clinical infection) AND (shows signs of severe clinical infection) AND (slough > 50%) AND (suicidal ideation) AND (systemic cancer) AND (systemic corticosteroids >15 mg/day) AND (systemic infections active) AND (target ulcer Decrease in size) AND (tendon exposure) AND (total bilirubin > 2 mg/dL) AND (tumor of any kind) AND (ulcer) AND (ulcer positive for β-hemolytic streptococci) AND (ulcer shows signs of severe clinical infection) AND (x-ray) AND NOT (non-melanoma skin cancer))"}
{"candidate_id": "LLM03683", "doc_id": "NCT02652572_exc", "case_bucket": "or", "source_criterion": "1. Decrease in size of the designated target ulcer(s) by ≥ 30% during the 7-day screening period 2. Cannot tolerate or comply with compression therapy. 3. An ulcer which shows signs of severe clinical infection, defined as pus oozing from the ulcer site 4. An ulcer positive for β-hemolytic streptococci upon culture 5. The ulcer has > 50% slough, significant necrotic tissue, bone, tendon, or capsule exposure or avascular ulcer beds 6. Is highly exuding (i.e. requires daily change of dressing) 7. Ankle brachial pressure index <0.65 8. Patients with active systemic infections 9. Patients with clinically significant medical conditions as determined by the investigator including renal, hepatic, hematologic, neurologic or immune disease. Examples include but are not limited to: 1. Renal insufficiency as an estimated GFR which is < 30 mL/min/1.7m2 2. Abnormal blood biochemistry defined as 3 times that of the upper limit of the normal range. 3. Hepatic insufficiency defined as total bilirubin > 2 mg/dL or serum albumin < 25 g/L 4. HbA1c > 9% 5. Hemoglobin < 10 g/dL 6. Hematocrit < 0.30 7. Platelet count < 100,000 10. Presence of an active systemic or local cancer or tumor of any kind (with the exception of non-melanoma skin cancer) 11. Patients with severe rheumatoid arthritis (with more than 20 persistently inflamed joints, or below lower normal limit blood albumin level, or evidence of bone and cartilage damage on x-ray, or inflammation in tissues other than joints) and other collagen vascular diseases. 12. Patients with active connective tissue disease 13. Treatment with systemic corticosteroids (>15 mg/day), or current immunosuppressive agents 14. Previous or current radiation therapy or likelihood to receive this therapy during study participation 15. Pregnant or nursing patients 16. Known prior inability or unavailability to complete required study visits during study participation 17. Significant peripheral edema as per investigator's discretion 18. A psychiatric condition (e.g., suicidal ideation) or chronic alcohol or drug abuse problem, determined from the patient's medical history, which, in the opinion of the investigator, may pose a threat to patient compliance 19. Use of a platelet-derived growth factor within 28 days before screening 20. Use of any investigational drug or therapy within 28 days before screening 21. Has any other factor which may, in the opinion of the investigator, compromise participation and/or follow-up in the study", "candidate_expression": "((Ankle brachial pressure index <0.65) AND (Cannot tolerate or comply with) AND (Has any other factor which may, in the opinion of the investigator, compromise participation and/or follow-up in the study) AND (HbA1c > 9%) AND (Hematocrit < 0.30) AND (Hemoglobin < 10 g/dL) AND (Hepatic insufficiency) AND (Platelet count < 100,000) AND (Renal insufficiency) AND (Significant) AND (as determined by the investigator) AND (as per investigator's discretion) AND (blood albumin level below lower normal limit) AND (blood biochemistry Abnormal 3 times that of the upper limit of the normal range) AND (bone and cartilage damage) AND (change of dressing daily highly exuding) AND (compression therapy) AND (connective tissue disease active) AND (estimated GFR < 30 mL/min/1.7m2) AND (highly exuding) AND (in the opinion of the investigator) AND (inflamed joints more than 20 persistently) AND (inflammation in tissues other than joints) AND (likelihood to) AND (medical conditions clinically significant) AND (peripheral edema Significant) AND (platelet-derived growth factor within 28 days before screening) AND (pose a threat) AND (pus) AND (radiation therapy) AND (severe clinical infection) AND (shows signs of severe clinical infection) AND (slough > 50%) AND (suicidal ideation) AND (systemic corticosteroids >15 mg/day) AND (systemic infections active) AND (target ulcer Decrease in size) AND (ulcer) AND (ulcer positive for β-hemolytic streptococci) AND (ulcer shows signs of severe clinical infection) AND (within 28 days before screening screening) AND (x-ray) AND NOT (non-melanoma skin cancer) AND ((collagen vascular diseases) OR (rheumatoid arthritis severe)) AND ((Treatment) OR (immunosuppressive agents current)) AND ((Previous) OR (current)) AND ((Pregnant) OR (nursing)) AND ((alcohol abuse problem) OR (drug abuse problem) OR (psychiatric condition)) AND ((investigational drug) OR (investigational therapy)) AND ((avascular ulcer beds) OR (bone exposure) OR (capsule exposure) OR (necrotic tissue) OR (tendon exposure)) AND ((hematologic disease) OR (hepatic disease) OR (immune disease) OR (neurologic disease) OR (renal disease)) AND ((serum albumin < 25 g/L) OR (total bilirubin > 2 mg/dL)) AND ((local cancer) OR (systemic cancer) OR (tumor of any kind)))"}
{"candidate_id": "LLM03684", "doc_id": "NCT03337581_exc", "case_bucket": "or", "source_criterion": "allergic to dexmedetomidine, similar active ingredients or excipients G-6-PD deficiency a history of arrhythmia, bronchial and cardiovascular diseases, abnormal liver function and so on a history of use of alpha 2 receptor agonists or antagonists.", "candidate_expression": "((G-6-PD deficiency) AND (allergic) AND (history) AND ((dexmedetomidine) OR (excipients) OR (similar active ingredients)) AND ((abnormal liver function) OR (arrhythmia) OR (bronchial diseases) OR (cardiovascular diseases)) AND ((alpha 2 receptor agonists) OR (alpha 2 receptor antagonists)))"}
{"candidate_id": "LLM03685", "doc_id": "NCT02607319_exc", "case_bucket": "or", "source_criterion": "Evidence of low ovarian reserve by at least one of the following: AMH = 1,5 ng/mL and/or basal CD 3 FSH = 10 mIU/mL and/or basal CD 3 Estradiol = 60 ng/mL and/or previous egg collection yield = 3 oocytes. Preexisting medical condition (thyroid disease, diabetes mellitus, hypertension, pulmonary conditions, cardiac condition…). Severe male factor infertility (Total motile sperm count < 5 million/ml and/or normal WHO morphology <20%). Hypersensitivity to Heparin or its derivatives. Acquired thrombophilia. Active hemorrhage or increased risk of bleeding due to impairment of homeostasis. Severe impairment of liver or pancreatic function. Severe renal insufficiency (Creatinine Clearance < 30 ml/min). Injuries to or operations on the central nervous system, eyes and ears within the last 2 months. Disseminated Intravascular Coagulation (DIC) attributable to heparin-induced thrombocytopenia. Acute bacterial endocarditis and endocarditis lenta. Any organic lesion with high risk of bleeding (e.g.: active peptic ulcer, hemorrhagic stroke, cerebral aneurysm or cerebral neoplasms).", "candidate_expression": "((< 30 ml/min) AND (< 5 million/ml) AND (<20%) AND (= 1,5 ng/mL) AND (= 10 mIU/mL) AND (= 3 oocytes) AND (= 60 ng/mL) AND (AMH) AND (Acquired) AND (Active hemorrhage) AND (Acute bacterial endocarditis) AND (Creatinine Clearance) AND (DIC) AND (Disseminated Intravascular Coagulation) AND (Heparin) AND (Hypersensitivity) AND (Injuries) AND (Severe) AND (Total motile sperm count) AND (active peptic ulcer) AND (basal CD 3 Estradiol) AND (basal CD 3 FSH) AND (cardiac condition) AND (central nervous system) AND (cerebral aneurysm) AND (cerebral neoplasms) AND (diabetes mellitus) AND (ears) AND (egg collection yield) AND (endocarditis lenta) AND (eyes) AND (hemorrhagic stroke) AND (heparin-induced thrombocytopenia) AND (high) AND (hypertension) AND (impairment of homeostasis) AND (impairment of liver) AND (impairment of pancreatic function) AND (increased) AND (last 2 months) AND (low ovarian reserve) AND (male factor infertility) AND (normal WHO morphology) AND (operations) AND (organic lesion) AND (pulmonary conditions) AND (renal insufficiency) AND (risk of bleeding) AND (thrombophilia) AND (thyroid disease))"}
{"candidate_id": "LLM03686", "doc_id": "NCT01684501_inc", "case_bucket": "other", "source_criterion": "weigh more than 200 lbs are high level ambulators corresponding to levels E to F of the Special Interest Group of Amputee Medicine (SIGAM) mobility grade have the ability to follow multi-step commands.", "candidate_expression": "((Special Interest Group of Amputee Medicine (SIGAM) mobility grade levels E to F) AND (ability to follow multi-step commands) AND (high level ambulators) AND (weigh more than 200 lbs))"}
{"candidate_id": "LLM03687", "doc_id": "NCT02282319_exc", "case_bucket": "other", "source_criterion": "micturition problems, neurological history or previous lower abdominal surgery with an abnormal micturition", "candidate_expression": "((lower abdominal surgery) AND (micturition) AND (micturition abnormal) AND (neurological history))"}
{"candidate_id": "LLM03688", "doc_id": "NCT02260700_inc", "case_bucket": "or", "source_criterion": "Body mass index (BMI; weight [kilogram(kg)]/height^2 [meter square (m^2)]) between 18 and 30 kg/m^2, (inclusive) Be healthy for their age group with or without medication on the basis of physical examination, medical history, vital signs, and 12-lead electrocardiogram (ECG) performed at Screening or admission. Minor deviations in ECG, which are not considered to be of clinical significance to the investigator, are acceptable Be healthy on the basis of clinical laboratory tests performed at Screening. If the results of the serum chemistry panel [including liver enzymes], hematology, or urinalysis are outside the normal reference ranges, the participant may be included only if the investigator judges the abnormalities or deviations from normal to be not clinically significant. This determination must be recorded in the participants' source documents and initialed by the investigator Men who are sexually active with a woman of childbearing potential and have not had a vasectomy must agree to use a barrier method of birth control for example, either condom with spermicidal foam/gel/film/cream/suppository or partner with occlusive cap (diaphragm or cervical/vault caps) with spermicidal foam/gel/film/cream/suppository, and all men must also not donate sperm during the study and for 3 months after receiving the last dose of study drug. In addition, their female partners should also use an appropriate method of birth control for at least the same duration Participants' must have signed an informed consent document indicating that they understand the purpose of and procedures required for the study and are willing to participate in the study", "candidate_expression": "((BMI) AND (Body mass index between 18 and 30 kg/m^2) AND (ECG) AND (Participants' must have signed an informed consent document indicating that they understand the purpose of and procedures required for the study and are willing to participate in the study) AND (clinical laboratory tests performed at Screening) AND (deviations in ECG which are not considered to be of clinical significance to the investigator) AND (healthy) AND (medical history) AND (not clinically significant) AND (physical examination) AND (the investigator judges) AND (vital signs performed at Screening or admission) AND (weight [kilogram(kg)]/height^2 [meter square (m^2)]) AND (which are not considered to be of clinical significance to the investigator) AND ((Screening) OR (admission)) AND ((hematology) OR (liver enzymes) OR (serum chemistry panel) OR (urinalysis)))"}
{"candidate_id": "LLM03689", "doc_id": "NCT01214096_inc", "case_bucket": "or", "source_criterion": "1. Age: 18-75 years old, no limitation in gender; 2. Left ventricular ejection fraction (LVEF) ≤ 40% (ECHO); 3. Patients with chronic heart failure (NYHA class II or III); 4. In the past one month, the clinical condition (including history, clinical symptoms and signs) was relatively stable; 5. Patients on standard treatment of chronic heart failure at the target dose or maximum tolerance dose for over 1 month ,or unchanged dose in last 1 month; 6. Understand and sign the informed consent form;", "candidate_expression": "((Age 18-75 years) AND (ECHO) AND (Left ventricular ejection fraction (LVEF) ≤ 40%) AND (NYHA class II or III) AND (Understand and sign the informed consent form;) AND (chronic heart failure) AND (clinical signs) AND (clinical symptoms) AND (history) AND (treatment of chronic heart failure) AND (unchanged dose in last 1 month) AND ((maximum tolerance dose) OR (target dose)))"}
{"candidate_id": "LLM03690", "doc_id": "NCT03097068_inc", "case_bucket": "other", "source_criterion": "Diagnosis of diabetes mellitus Best corrected visual acuity 20/32 - 20/320 Diabetic macular edema involving the center of the macula Optical coherence tomography central subfield thickness of at least 250 microns", "candidate_expression": "((Best corrected visual acuity 20/32 - 20/320) AND (Diabetic macular edema center of the macula) AND (Optical coherence tomography central subfield thickness at least 250 microns) AND (diabetes mellitus))"}
{"candidate_id": "LLM03691", "doc_id": "NCT02579733_exc", "case_bucket": "or", "source_criterion": "Patients with azathioprine or biologics therapy", "candidate_expression": "((azathioprine) AND (biologics) AND (therapy))"}
{"candidate_id": "LLM03692", "doc_id": "NCT02366819_exc", "case_bucket": "or", "source_criterion": "Previous or concurrent malignancy, except for adequately treated basal cell or squamous cell skin cancer, in situ cervical cancer, or any other cancer for which the patient has been previously treated and the lifetime recurrence risk is less than 30% Inflammatory bowel disease that is uncontrolled or on active treatment (Crohn's disease, ulcerative colitis) Diarrhea, grade 1 or greater by the National Cancer Institute Common Terminology Criteria for Adverse Events (NCI-CTCAE, version [v] 4.0) Neuropathy, grade 2 or greater by NCI-CTCAE, v 4.0 Serious underlying medical or psychiatric illnesses that would, in the opinion of the treating physician, substantially increase the risk for complications related to treatment Active uncontrolled bleeding Pregnancy or breastfeeding Major surgery within 4 weeks Patients with any polymorphism in UGT1A1 other than *1 or *28 (e.g, *6) will be allowed and treated as in the *28/*28 dosing group", "candidate_expression": "((Active) AND (Crohn's disease) AND (Diarrhea) AND (Inflammatory bowel disease) AND (Major surgery) AND (NCI-CTCAE, v 4.0) AND (NCI-CTCAE, version [v] 4.0) AND (National Cancer Institute Common Terminology Criteria for Adverse Events) AND (Neuropathy) AND (Pregnancy or breastfeeding) AND (Previous) AND (adequately treated) AND (basal cell skin cancer) AND (bleeding) AND (cervical cancer) AND (concurrent) AND (except) AND (grade 1 or greater) AND (grade 2 or greater) AND (in situ) AND (malignancy) AND (squamous cell skin cancer) AND (treatment) AND (ulcerative colitis) AND (uncontrolled) AND (within 4 weeks))"}
{"candidate_id": "LLM03693", "doc_id": "NCT03530124_exc", "case_bucket": "or", "source_criterion": "Receipt of DTaP, IPV, PCV13, or Hib prior to enrollment. Previous administration of the first dose of HBV is permitted Anticipated receipt of any vaccine other than DTaP, IPV, HBV, PCV13, or Hib during the first 60 hours after randomization History of a severe allergic reaction (e.g. anaphylaxis) to a previous dose of any hepatitis B vaccine History of a severe allergic reaction (e.g. anaphylaxis) to any component of the vaccines used in the study including neomycin, yeast and polymyxin B History of latex allergy History of unstable progressive neurologic disorder of unknown cause Known cause of apnea other than apnea of prematurity Cyanotic heart disease (congenital or acquired) Child or parent/LAR is an immediate relative of study staff or an employee who is supervised by study staff. Any condition that would, in the opinion of the site investigator, place the participant at an unacceptable risk of injury or render the participant unable to meet the requirements of the protocol", "candidate_expression": "((Anticipated receipt) AND (Cyanotic heart disease) AND (History) AND (Known cause of apnea) AND (allergic reaction) AND (allergy) AND (anaphylaxis) AND (apnea of prematurity) AND (component of the vaccines used in the study) AND (during the first 60 hours after randomization) AND (enrollment) AND (hepatitis B vaccine) AND (latex) AND (other than) AND (previous) AND (prior to enrollment) AND (progressive neurologic disorder) AND (randomization) AND (severe) AND (unknown cause) AND (unstable) AND ((DTaP) OR (Hib) OR (IPV) OR (PCV13)) AND ((neomycin) OR (polymyxin B) OR (yeast)) AND ((acquired) OR (congenital)) AND ((DTaP) OR (HBV) OR (Hib) OR (IPV) OR (PCV13)))"}
{"candidate_id": "LLM03694", "doc_id": "NCT02926235_inc", "case_bucket": "other", "source_criterion": "All patients will be undergoing a primary unilateral total knee arthroplasty for a diagnosis of osteoarthritis", "candidate_expression": "((osteoarthritis) AND (unilateral total knee arthroplasty primary))"}
{"candidate_id": "LLM03695", "doc_id": "NCT01717911_exc", "case_bucket": "or", "source_criterion": "Previous treated with anti-diabetic medication Pregnant or nursing women. Impaired liver function (ALT > 120 U/L) Impaired renal function (Serum creatinine >1.5 mg/dL in male, >1.4 mg/dL in female ) Recently suffered from MI or CVA. Patients are acute intercurrent illness. 2-hour C-peptide level < 1.8 ng/mL.", "candidate_expression": "((2-hour C-peptide level) AND (< 1.8 ng/mL) AND (> 120 U/L) AND (>1.4 mg/dL) AND (>1.5 mg/dL) AND (ALT) AND (CVA) AND (Impaired liver function) AND (Impaired renal function) AND (MI) AND (Pregnant) AND (Previous) AND (Recently) AND (Serum creatinine) AND (acute intercurrent illness) AND (anti-diabetic medication) AND (female) AND (male) AND (nursing) AND (treated) AND (women))"}
{"candidate_id": "LLM03696", "doc_id": "NCT02957877_inc", "case_bucket": "other", "source_criterion": "Prevalent NHHD patients who have received >1 year dialysis with unfractionated heparin as anticoagulant Age >= 18 Informed consent available", "candidate_expression": "((>1 year) AND (>= 18) AND (Age) AND (NHHD) AND (anticoagulant) AND (dialysis) AND (unfractionated heparin))"}
{"candidate_id": "LLM03697", "doc_id": "NCT02083991_inc", "case_bucket": "or", "source_criterion": "First or second single kidney (cadaveric or living donors) transplant recipients. Considered for a standard immunosuppressive protocol. Must be capable of giving written informed connect for participation in the study for 24 months.", "candidate_expression": "((First single kidney transplant cadaveric donors living donors) AND (Must be capable of giving written informed connect for participation in the study for 24 months.) AND (standard immunosuppressive protocol Considered for) AND (transplant second single kidney))"}
{"candidate_id": "LLM03698", "doc_id": "NCT03026465_exc", "case_bucket": "or", "source_criterion": "Target lesion located in the left main stem STEMI Restenosis Cardiogenic shock Malignancies or other comorbid conditions with life expectancy less than 12 months or that may result in protocol noncompliance Known allergy to the study medications (probucol, sirolimus, zotarolimus) Pregnancy (present, suspected, or planned)", "candidate_expression": "((Cardiogenic shock) AND (Pregnancy) AND (Restenosis) AND (STEMI) AND (Target lesion) AND (allergy) AND (left main stem) AND (less than 12 months) AND (may) AND (other) AND (study medications) AND ((probucol) OR (sirolimus) OR (zotarolimus)) AND ((planned) OR (present) OR (suspected)) AND ((Malignancies) OR (comorbid conditions)) AND ((life expectancy) OR (protocol noncompliance)))"}
{"candidate_id": "LLM03699", "doc_id": "NCT00198913_inc", "case_bucket": "other", "source_criterion": "type 2 diabetic, age 18 and over, informed consent,", "candidate_expression": "((18 and over) AND (age) AND (informed consent) AND (type 2 diabetic))"}
{"candidate_id": "LLM03700", "doc_id": "NCT03355326_exc", "case_bucket": "or", "source_criterion": "Neurological Congenital malformations and/or those known to impair intestinal motility Additional congenital gastrointestinal abnormalities requiring surgical intervention Congenital Cyanotic heart disease Surgical Closure of abdominal wall defect with prosthetic material (e.g. prosthetic or bio-prosthetic mesh)", "candidate_expression": "((Additional) AND (Congenital) AND (Cyanotic heart disease) AND (Neurological Congenital malformations) AND (Surgical Closure) AND (abdominal wall defect) AND (bio-prosthetic mesh) AND (congenital) AND (gastrointestinal abnormalities) AND (impair intestinal motility) AND (prosthetic material) AND (prosthetic mesh) AND (requiring) AND (surgical intervention))"}
```
