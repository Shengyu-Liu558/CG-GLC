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
{"candidate_id": "LLM07501", "doc_id": "NCT03325023_inc", "case_bucket": "or", "source_criterion": "Written consent for participation in the clinical trial Age 18 to 45 years Irregular menstruation (> 35 days) or secondary amenorrhea> 3 months", "candidate_expression": "((18 to 45 years) AND (> 3 months) AND (> 35 days) AND (Age) AND (Written consent for participation in the clinical trial) AND ((Irregular menstruation) OR (secondary amenorrhea)))"}
{"candidate_id": "LLM07502", "doc_id": "NCT02618057_inc", "case_bucket": "or", "source_criterion": "Evidence of Mycoplasma pneumoniae infection Lobar pneumonia or pneumoniae with pleural effusion", "candidate_expression": "((Lobar pneumonia) AND (Mycoplasma pneumoniae infection) AND (pleural effusion) AND (pneumoniae))"}
{"candidate_id": "LLM07503", "doc_id": "NCT03530124_exc", "case_bucket": "or", "source_criterion": "Receipt of DTaP, IPV, PCV13, or Hib prior to enrollment. Previous administration of the first dose of HBV is permitted Anticipated receipt of any vaccine other than DTaP, IPV, HBV, PCV13, or Hib during the first 60 hours after randomization History of a severe allergic reaction (e.g. anaphylaxis) to a previous dose of any hepatitis B vaccine History of a severe allergic reaction (e.g. anaphylaxis) to any component of the vaccines used in the study including neomycin, yeast and polymyxin B History of latex allergy History of unstable progressive neurologic disorder of unknown cause Known cause of apnea other than apnea of prematurity Cyanotic heart disease (congenital or acquired) Child or parent/LAR is an immediate relative of study staff or an employee who is supervised by study staff. Any condition that would, in the opinion of the site investigator, place the participant at an unacceptable risk of injury or render the participant unable to meet the requirements of the protocol", "candidate_expression": "((Anticipated receipt) AND (Cyanotic heart disease) AND (DTaP) AND (HBV) AND (Hib) AND (History) AND (IPV) AND (Known cause of apnea) AND (PCV13) AND (acquired) AND (allergic reaction) AND (allergy) AND (anaphylaxis) AND (apnea of prematurity) AND (component of the vaccines used in the study) AND (congenital) AND (during the first 60 hours after randomization) AND (enrollment) AND (hepatitis B vaccine) AND (latex) AND (neomycin) AND (other than) AND (polymyxin B) AND (previous) AND (prior to enrollment) AND (progressive neurologic disorder) AND (randomization) AND (severe) AND (unknown cause) AND (unstable) AND (yeast))"}
{"candidate_id": "LLM07504", "doc_id": "NCT03187379_exc", "case_bucket": "other", "source_criterion": "age <18 years previous history of roux-en-y gastric bypass patients undergoing other bariatric procedures pre-operative opioid analgesics", "candidate_expression": "((age <18 years) AND (bariatric procedures undergoing other) AND (opioid analgesics pre-operative) AND (roux-en-y gastric bypass previous history))"}
{"candidate_id": "LLM07505", "doc_id": "NCT02944929_inc", "case_bucket": "or", "source_criterion": "Males and females aged between 18 to 75 years. Adult patient under guardianship with consent obtained and the legal guardian's authorisation obtained. Single stroke having occurred more than 6 months before (previous TIA is accepted). Capable of understanding instructions and participating in the definition of a therapeutic goal (Boston Diagnostic Aphasia Examination (BDAE) < 3). Having previously undergone BTI. The last injection must have been performed at least 4 months prior to inclusion. Affiliation to the French social security regime or a similar regime. Patient (or the legal guardian if under guardian adult patient) has signed the informed consent form.", "candidate_expression": "((Adult patient under guardianship with consent obtained and the legal guardian's authorisation obtained) AND (BDAE) AND (BTI) AND (Boston Diagnostic Aphasia Examination < 3) AND (Capable of understanding instructions and participating in the definition of a therapeutic goal) AND (Patient (or the legal guardian if under guardian adult patient) has signed the informed consent form) AND (TIA) AND (aged between 18 to 75 years) AND (injection at least 4 months prior to inclusion) AND (stroke Single more than 6 months) AND ((Males) OR (females)))"}
{"candidate_id": "LLM07506", "doc_id": "NCT03328052_exc", "case_bucket": "or", "source_criterion": "Diagnosis of a psychotic disorder. History of, or current, open head brain trauma. Candidates with any metal, shrapnel or other similar objects in the head that could affect the QEEG History of: craniotomy, cerebral metastases, cerebrovascular accident; current diagnosis of seizure disorder, schizophrenia, schizo-affective disorder, dementia, mental retardation, or major depression with psychotic features; or use of depot neuroleptics in last 12 months. Uncontrolled thyroid disorders. Known pregnancy and/or lactation, or intent to become pregnant during this study. Chronic or acute pain requiring prescription pain medication(s) (narcotic or synthetic narcotic) Participation in any other therapeutic drug study within 60 days preceding inclusion.", "candidate_expression": "((Chronic) AND (History) AND (Known pregnancy and/or lactation, or intent to become pregnant during this study.) AND (Participation in any other therapeutic drug study within 60 days preceding inclusion.) AND (QEEG) AND (Uncontrolled) AND (acute) AND (affect) AND (cerebral metastases) AND (cerebrovascular accident) AND (craniotomy) AND (current) AND (dementia) AND (depot neuroleptics) AND (in last 12 months) AND (major depression) AND (mental retardation) AND (metal) AND (narcotic) AND (objects in the head) AND (open head brain trauma) AND (pain) AND (prescription pain medication) AND (psychotic disorder) AND (psychotic features) AND (schizo-affective disorder) AND (schizophrenia) AND (seizure disorder) AND (shrapnel) AND (synthetic narcotic) AND (thyroid disorders))"}
{"candidate_id": "LLM07507", "doc_id": "NCT02195024_inc", "case_bucket": "or", "source_criterion": "Approved clinical indication for pectoral pacemaker exchange (e.g. elective replacement indication (ERI), end of service (EOS)) a single or dual chamber MRI conditional pacemaker (BSCI) or Any comparable successor IPG (MRI conditional system, BSCI) compatible with Implanted Fineline-II-leads (BSCI), MRI conditional The ascertained lead impedance is between 200 and 1500 Ohm. All pacing capture thresholds (PCT) do not exceed 2.0 V @0.4 or 0.5 ms in pacemaker dependent patients Male or female 18 years or older Understand the nature of the procedure Give written informed consent Able to complete all testing required by the clinical protocol Ability to measure atrial and/or ventricular pacing threshold(s) at 0.4 or 0.5 ms Patient body height greater or equal to 140 cm Pectoral implanted device Subjects who are able and willing to undergo elective cardiac magnetic resonance (MR) scanning without sedation (MRI-group) Subjects who are geographically stable and available for follow-up at the study center for the length of the study", "candidate_expression": "((18 years or older) AND (Ability to measure atrial and/or ventricular pacing threshold(s) at 0.4 or 0.5 ms) AND (Able to complete all testing required by the clinical protocol) AND (BSCI) AND (Give written informed consent) AND (Implanted Fineline-II-leads) AND (MR) AND (MRI conditional) AND (PCT) AND (Pectoral implanted device) AND (ascertained lead impedance) AND (at the study center) AND (available for follow-up) AND (between 200 and 1500 Ohm) AND (body height) AND (cardiac magnetic resonance scanning) AND (clinical indication) AND (comparable) AND (do not exceed 2.0 V @0.4 or 0.5 ms) AND (elective) AND (for the length of the study) AND (geographically stable) AND (greater or equal to 140 cm) AND (pacemaker) AND (pacemaker dependent) AND (pacing capture thresholds) AND (pectoral pacemaker exchange) AND (successor IPG) AND (willing to undergo) AND (without sedation) AND (years or older) AND ((BSCI) OR (MRI conditional system)) AND ((elective replacement indication (ERI)) OR (end of service (EOS))) AND ((Male) OR (female)) AND ((dual chamber) OR (single chamber)))"}
{"candidate_id": "LLM07508", "doc_id": "NCT02226887_exc", "case_bucket": "or", "source_criterion": "Patients under 18 Pregnancy and Lactation Patients allergic to polyglycolic / trimethylene carbonate Carrier of prosthetic mesh in the ostomy Patients presenting midline hernia. Patients affected by inflammatory bowel disease", "candidate_expression": "((allergic) AND (inflammatory bowel disease) AND (midline hernia) AND (ostomy) AND (polyglycolic carbonate) AND (prosthetic mesh) AND (trimethylene carbonate) AND (under 18) AND ((Lactation) OR (Pregnancy)))"}
{"candidate_id": "LLM07509", "doc_id": "NCT03064568_exc", "case_bucket": "or", "source_criterion": "Patient with contraindication to misoprostol or vasopressin, personal history or cardiac or pulmonary disease, history of prior myomectomy", "candidate_expression": "((contraindication) AND (myomectomy history prior) AND ((misoprostol) OR (vasopressin)) AND ((disease cardiac) OR (pulmonary disease)))"}
{"candidate_id": "LLM07510", "doc_id": "NCT02954029_exc", "case_bucket": "or", "source_criterion": "congenital or acquired bleeding tendency platelet count <50,000/ µL hypersensitivity to shrimps, lobsters or beetles", "candidate_expression": "((bleeding tendency) AND (hypersensitivity) AND (platelet count <50,000/ µL) AND ((acquired) OR (congenital)) AND ((beetles) OR (lobsters) OR (shrimps)))"}
{"candidate_id": "LLM07511", "doc_id": "NCT00324363_inc", "case_bucket": "or", "source_criterion": "Treated with a stable dose of one of the following for at least 3 months prior to screening: * >=1000 mg/day immediate-release metformin; or metformin >=1000 mg/day and sulfonylurea; or sulfonylurea/metformin combination therapy. HbA1c between 7.1% and 11.0%, inclusive. Body Mass Index (BMI) >21 kg/m^2 and <35 kg/m^2.", "candidate_expression": "((>21 kg/m^2 and <35 kg/m^2) AND (>=1000 mg/day) AND (Body Mass Index (BMI)) AND (HbA1c) AND (at least 3 months prior to screening) AND (between 7.1% and 11.0%, inclusive) AND (metformin) AND (one of the following) AND (screening) AND (stable dose) AND (sulfonylurea) AND ((combination therapy) OR (immediate-release metformin)))"}
{"candidate_id": "LLM07512", "doc_id": "NCT02609425_inc", "case_bucket": "other", "source_criterion": "All patients with esophageal cancer who are deemed candidates for minimally invasive robot assisted Ivor Lewis esophagogastrectomy. Patients who provide written informed consent for the study.", "candidate_expression": "((Ivor Lewis) AND (Patients who provide written informed consent for the study.) AND (candidates) AND (esophageal cancer) AND (esophagogastrectomy) AND (minimally invasive) AND (robot assisted))"}
{"candidate_id": "LLM07513", "doc_id": "NCT02735902_inc", "case_bucket": "other", "source_criterion": "The patient or his/her representative must have given free and informed consent and signed the consent The patient must be insured or beneficiary of a health insurance plan The patient is available for 12 months of follow-up The patient underwent a successful transcutaneous implant procedure for an aortic valve within the past 24 hours The patient was receiving anti-vitamin K (AVK) treatment before percutaneous implantation of the aortic valve", "candidate_expression": "((AVK) AND (The patient is available for 12 months of follow-up) AND (The patient or his/her representative must have given free and informed consent and signed the consent) AND (anti-vitamin K) AND (aortic valve) AND (before percutaneous implantation of the aortic valve) AND (past 24 hours) AND (percutaneous implantation of the aortic valve) AND (transcutaneous implant procedure))"}
{"candidate_id": "LLM07514", "doc_id": "NCT02952378_inc", "case_bucket": "scope", "source_criterion": "For healthy individuals: Healthy, without allergies and with the age of 18 years or above. For patients: Burn injury exceeding 6-8 Total Burned Surface Area %", "candidate_expression": "((Burn injury) AND (Healthy) AND (Total Burned Surface Area exceeding 6-8 %) AND (age 18 years or above) AND (healthy) AND (patients) AND NOT (allergies))"}
{"candidate_id": "LLM07515", "doc_id": "NCT03064867_exc", "case_bucket": "or", "source_criterion": "Prior treatment toxicities have not resolved to < Grade 2 according to NCI CTCAE Version 4.0 (except clinically insignificant toxicities such as alopecia). Subjects receiving any other investigational agents. Patients with active tumor lysis syndrome (TLS) either from laboratory or clinical changes. Patients with active central nervous system (CNS) disease defined as symptomatic meningeal lymphoma or known CNS parenchymal lymphoma. History of severe allergic reactions attributed to compounds of similar chemical or biologic composition to rituximab or other agents used in this study. Subjects with uncontrolled intercurrent illness . HIV-positive subjects on combination antiretroviral therapy are ineligible because of the potential for pharmacokinetic interactions with Venetoclax. In addition, these subjects are at increased risk of lethal infections when treated with marrow suppressive therapy. Appropriate studies will be undertaken in subjects receiving combination antiretroviral therapy when indicated. HIV testing prior to enrollment is not required for screening but strongly encouraged for patients with no documented prior HIV assessment. Presence of positive test results for hepatitis B virus (HBV), hepatitis B surface antigen (HBsAg), or hepatitis C (HCV) antibody. Patients who are positive for HCV antibody must be negative for HCV by polymerase chain reaction (PCR) to be eligible for study participation Patients with occult or prior HBV infection (defined as positive total hepatitis B core antibody [HBcAb] and negative HBsAg) may be included if HBV DNA is undetectable. These patients must be willing to undergo monthly DNA testing. Women who are pregnant or lactating Malabsorption syndrome or other condition that precludes enteral route of administration Chemotherapy or radiation within 3 weeks of the first scheduled study treatment. Less than 2-year disease free from another primary malignancy (other than squamous or basal cell carcinoma of the skin, \"in-situ\" carcinoma of the cervix or breast, superficial bladder carcinoma, or previously treated localized prostate cancer with normal prostate specific antigen (PSA) levels). Patients who have had completed all anti-cancer treatment for another primary malignancy more than 2 years prior to screening are eligible if they are not considered to have a \"currently active\" malignancy based on having less than a 30% risk of relapse. Major surgery, other than diagnostic surgery, within 2 weeks. Medical condition requiring chronic use of high dose systemic corticosteroids (i.e., doses of prednisone higher than 10 mg/day or equivalent). Brief (<15 days) treatment with glucocorticoids (prednisone 100 mg by mouth daily, or equivalent) is acceptable. Known allergy to both xanthine oxidase inhibitors and rasburicase. Use of warfarin is prohibited. Anticoagulation with low-molecular weight heparin (i.e. enoxaparin) or direct thrombin inhibitors is permitted. The following concomitant medications are not allowed from 7 days prior to the first dose of study drug and during venetoclax administration: Strong CYP3A4 inhibitors including but not limited to fluconazole, ketoconazole, and clarithromycin or strong CYP3A4 inducers included but not limited to rifampin, carbamazepine. Receipt of live-virus vaccines within 28 days prior to the initiation of study treatment or need for live-virus vaccines at any time during study treatment. Concomitant medications that fall into the categories below could potentially lead to adverse reactions and should be considered cautionary. Moderate/Weak CYP3A inducers such as efavirenz and oxcarbazepine CYP2C8 substrates such as thiazolidinediones (glitazones) and select statins (because of expected inhibition of the metabolism of CYP2C8 substrates) by venetoclax CYP2C9 substrates such as tolbutamide (because of expected inhibition of the metabolism of CYP2C9 substrates by venetoclax. It is recommended to exclude CYP2C9 substrates with a narrow therapeutic index such as phenytoin.", "candidate_expression": "((Anticoagulation) AND (CYP2C9 substrates) AND (CYP2C9 substrates narrow therapeutic index) AND (HBV DNA undetectable) AND (HBV infection) AND (HBsAg negative) AND (HCV antibody positive) AND (HCV negative) AND (HIV-positive) AND (It is recommended to exclude CYP2C9 substrates with a narrow therapeutic index such as phenytoin) AND (Major surgery within 2 weeks) AND (Medical condition) AND (Women) AND (allergic reactions severe) AND (allergy) AND (carbamazepine) AND (central nervous system (CNS) disease) AND (clarithromycin) AND (combination antiretroviral therapy) AND (disease free Less than 2-year) AND (enoxaparin) AND (fluconazole) AND (glitazones) AND (glucocorticoids <15 days) AND (hepatitis B surface antigen (HBsAg) positive) AND (hepatitis B virus (HBV) positive) AND (hepatitis C (HCV) antibody positive) AND (ketoconazole) AND (need for) AND (phenytoin) AND (polymerase chain reaction (PCR)) AND (prednisone 100 mg daily) AND (prednisone higher than 10 mg/day) AND (primary malignancy another) AND (prostate specific antigen (PSA) levels normal) AND (rasburicase) AND (rifampin) AND (systemic corticosteroids chronic high dose) AND (thiazolidinediones) AND (tolbutamide) AND (total hepatitis B core antibody [HBcAb] positive) AND (tumor lysis syndrome (TLS)) AND (venetoclax) AND (warfarin) AND (xanthine oxidase inhibitors) AND NOT (anti-cancer treatment more than 2 years prior) AND NOT (diagnostic surgery) AND ((Strong CYP3A4 inhibitors) OR (strong CYP3A4 inducers)) AND ((compounds of similar chemical or biologic composition to other agents used in this study) OR (compounds of similar chemical or biologic composition to rituximab)) AND ((live-virus vaccines any time during) OR (live-virus vaccines within 28 days prior)) AND ((Moderate CYP3A inducers) OR (Weak CYP3A inducers)) AND ((efavirenz) OR (oxcarbazepine)) AND ((CYP2C8 substrates) OR (statins select)) AND ((lactating) OR (pregnant)) AND ((Malabsorption syndrome) OR (condition that precludes enteral route of administration)) AND ((Chemotherapy within 3 weeks of the first scheduled study treatment) OR (radiation within 3 weeks of the first scheduled study treatment)) AND ((\"in-situ\" carcinoma of the cervix) OR (\"in-situ\" carcinoma of the cervix breast) OR (localized prostate cancer) OR (squamous or basal cell carcinoma of the skin) OR (superficial bladder carcinoma)) AND ((CNS parenchymal lymphoma) OR (meningeal lymphoma symptomatic)) AND ((direct thrombin inhibitors) OR (low-molecular weight heparin)) AND ((7 days prior first dose of study drug) OR (venetoclax administration)))"}
{"candidate_id": "LLM07516", "doc_id": "NCT02478515_inc", "case_bucket": "other", "source_criterion": "Signed informed consent form Macula edema secondary to BRVO BCVA of 77 to 20 letters assessed with the use of ETDRS charts CRT <U+2267>250µm", "candidate_expression": "((250µm) AND (77 to 20 letters) AND (BCVA) AND (BRVO) AND (CRT) AND (Macula edema) AND (Signed informed consent form))"}
{"candidate_id": "LLM07517", "doc_id": "NCT02827526_inc", "case_bucket": "or", "source_criterion": "Patients presenting for elective posterior spinal fusion surgery (lower thoracic, lumbar, sacral) Ages 18-80", "candidate_expression": "((18-80) AND (Ages) AND (elective) AND (lower thoracic) AND (lumbar) AND (posterior spinal fusion surgery) AND (sacral))"}
{"candidate_id": "LLM07518", "doc_id": "NCT02765035_inc", "case_bucket": "other", "source_criterion": "Person is >18 years old. Person is a unilateral transfemoral or knee-disarticulation amputee with stabilized residual limb. Person is a K2, K3 or K4 ambulator based on Medicare Functional Classification Level (MFCL). Person is currently fitted with a prosthesis using a non-microprocessor controlled prosthetic knee for at least 6 months. Person was never fitted with microprocessor controlled prosthetic knee joint. Person is willing and able to independently provide informed consent. Person is willing to comply with study procedures. Person wears prosthesis daily and = 8 hours/day. Person is walking on average 1km/day. Person is walking not slower than 3km/h (~0.8m/s) (based on 10m walk test conducted during recruiting). Person is walking on level ground in a step over step manner.", "candidate_expression": "((1km/day) AND (>18 years) AND (K2, K3 or K4) AND (MFCL) AND (Medicare Functional Classification Level) AND (Person is willing and able to independently provide informed consent) AND (Person is willing to comply with study procedures) AND (at least 6 months) AND (daily and = 8 hours/day) AND (microprocessor controlled) AND (never) AND (non-microprocessor controlled) AND (not slower than 3km/h) AND (old) AND (prosthesis) AND (prosthetic knee) AND (prosthetic knee joint) AND (walking))"}
{"candidate_id": "LLM07519", "doc_id": "NCT02939209_exc", "case_bucket": "or", "source_criterion": "Allergy, sensitivity, or absolute contraindications to any of the medications involved in the study preexisting CNS depression, or taking regularly medication that cause CNS depression preexisting cognitive deficits, dementia, or delirium severe respiratory comorbidities (e.g. chronic obstructive pulmonary disease, pneumonia, respiratory failure) sleep disordered breathing (diagnosed OSA, obesity hypoventilation syndrome) pregnancy and breast feeding history of chronic pain or regular (at least once daily) opioid use preoperatively renal impairment - CrCl =60 mL/minute not fluent in English to be able to participate in the study process, including consent and phone interview Body Mass Index >35 inability to take oral medication.", "candidate_expression": "((Allergy) AND (Body Mass Index >35) AND (CNS depression) AND (CrCl =60 mL/minute) AND (OSA) AND (chronic obstructive pulmonary disease) AND (chronic pain) AND (cognitive deficits) AND (contraindications) AND (delirium) AND (dementia) AND (medication) AND (medications study) AND (not fluent in English to be able to participate in the study process, including consent and phone interview) AND (obesity hypoventilation syndrome) AND (opioid at least once daily preoperatively) AND (oral medication inability) AND (pneumonia) AND (pregnancy and breast feeding) AND (renal impairment) AND (respiratory comorbidities severe) AND (respiratory failure) AND (sensitivity) AND (sleep disordered breathing))"}
{"candidate_id": "LLM07520", "doc_id": "NCT03233880_inc", "case_bucket": "other", "source_criterion": "primigravida, singleton pregnancy, maternal age 18-35 years, and pregnancy duration 16-20 weeks at the time of study inclusion.", "candidate_expression": "((maternal age 18-35 years) AND (pregnancy duration 16-20 weeks at the time of study inclusion) AND (primigravida) AND (singleton pregnancy))"}
{"candidate_id": "LLM07521", "doc_id": "NCT03472508_inc", "case_bucket": "or", "source_criterion": "(1)= 45 years old; (2)A diagnosis or previous diagnosis of essential hypertension, including anyone currently taking antihypertensive drugs; or for those who have not taken antihypertensive drugs within the last 2 weeks, two consecutive examinations were conducted at least one day apart, and both sitting blood pressure (mean value of 3 measurements) met the following criteria: diastolic blood pressure (DBP) =90 mmHg or systolic blood pressure (SBP) =140 mmHg (the second blood pressure was measured at V1); (3)If a study participant is a woman of childbearing age, she agrees to use a reliable contraceptive method during the trial; (4)Voluntarily participates and has signed an informed consent form. (1)Completed MTHFR C677T gene polymorphism detection in run-in period or MTHFR C677T genotype already known in advance; (2)Exhibited good tolerance to enalapril and good overall medication compliance (>80%) in run-in period or previously exhibited good tolerance and adherence to ACEI drugs in previous medication history. (3)Voluntarily continues to participate in this study.", "candidate_expression": "((= 45 years) AND (=140 mmHg) AND (=90 mmHg) AND (>80%) AND (ACEI drugs) AND (MTHFR C677T) AND (Voluntarily) AND (Voluntarily participates) AND (agrees to use) AND (antihypertensive drugs) AND (childbearing age) AND (continues to participate in this study) AND (contraceptive method) AND (currently) AND (diagnosis) AND (diastolic blood pressure (DBP)) AND (during the trial) AND (enalapril) AND (essential hypertension) AND (gene polymorphism detection) AND (genotype already known) AND (good) AND (good adherence to ACEI drugs) AND (good tolerance to ACEI drugs) AND (good tolerance to enalapril) AND (medication history) AND (not) AND (old) AND (overall medication compliance) AND (previous) AND (previously) AND (reliable) AND (signed an informed consent) AND (sitting blood pressure) AND (systolic blood pressure (SBP)) AND (the trial) AND (two consecutive at least one day apart) AND (within the last 2 weeks) AND (woman))"}
{"candidate_id": "LLM07522", "doc_id": "NCT01531257_exc", "case_bucket": "or", "source_criterion": "1. Need for combined organ transplantation with an extra-renal organ and/or islet cell transplant. 2. Recipients of previous non-renal solid organ and/or islet cell transplantation. 3. Infection with HIV. 4. Inability or unwillingness of a participant and/or guardian to provide informed consent", "candidate_expression": "((Inability or unwillingness of a participant and/or guardian to provide informed consent) AND (Infection with HIV) AND (combined organ transplantation) AND (previous) AND ((extra-renal organ) OR (islet cell transplant)) AND ((islet cell transplantation) OR (non-renal solid organ transplantation)))"}
{"candidate_id": "LLM07523", "doc_id": "NCT01491295_exc", "case_bucket": "or", "source_criterion": "HCV, HIV, HDV coinfection. Uncontrolled HCC, malignancy or decompensated liver cirrhosis (CTP score = 7). Uremia patients or Creatinine = 2 mg/dl.", "candidate_expression": "((CTP score = 7) AND (Creatinine = 2 mg/dl) AND (HCC Uncontrolled) AND (HCV coinfection) AND (HDV coinfection) AND (Uremia) AND (coinfection HIV) AND (liver cirrhosis decompensated) AND (malignancy))"}
{"candidate_id": "LLM07524", "doc_id": "NCT01932996_exc", "case_bucket": "or", "source_criterion": "Use of smoking cessation medications or interventions in last 30 days Unstable medical illness that requires immediate medical care AUDIT score of < 5 or > 26 Pregnancy or other Nicotine Replacement Therapy (NRT) contraindications Current history or in past 6 months of psychotic disorder or major depressive disorders that is not stable on treatment for past 3 months Cognitive impairment", "candidate_expression": "((AUDIT score of < 5 or > 26) AND (Cognitive impairment) AND (NRT) AND (Nicotine Replacement Therapy) AND (Pregnancy) AND (contraindications) AND (interventions) AND (major depressive disorders not stable for past 3 months) AND (medications) AND (psychotic disorder past 6 months) AND (smoking cessation))"}
{"candidate_id": "LLM07525", "doc_id": "NCT00970866_inc", "case_bucket": "or", "source_criterion": "At least 18 years of age No more than 20 wk of gestation Given Ante-natal Cards of the Ghana Health Service Completed the initial routine ante-natal examination at the clinics HIV negative or status unknown (as from the Ante-natal card) Free from chronic disease e.g. malignancy requiring frequent medical attention (as from the Ante-natal card) Residing in the Manya Krobo or Yilo Krobo district Prepared to sign an informed consent Living in the area throughout the duration of the study Acceptance of home visitors", "candidate_expression": "((Acceptance of home visitors) AND (At least 18 years) AND (HIV) AND (Living in the area) AND (Manya Krobo district) AND (No more than 20 wk) AND (Prepared to sign an informed consent) AND (Residing) AND (Yilo Krobo district) AND (age) AND (chronic disease) AND (clinics) AND (gestation) AND (malignancy) AND (negative) AND (routine ante-natal examination) AND (status unknown) AND (the study) AND (throughout the duration of the study))"}
```
