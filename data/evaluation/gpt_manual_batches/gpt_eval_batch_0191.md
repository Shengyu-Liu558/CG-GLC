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
{"candidate_id": "LLM04751", "doc_id": "NCT02386800_exc", "case_bucket": "other", "source_criterion": "Patient has participated in a combination trial where ruxolitinib was dispensed in combination with another study medication and the patient is still receiving combination therapy. Pregnant or nursing (lactating) women, where pregnancy is defined as the state of a female after conception and until the termination of gestation, confirmed by a positive hCG laboratory test. Women of child-bearing potential, defined as all women physiologically capable of becoming pregnant, unless they are using highly effective methods of contraception throughout the study duration inclusive of the 30-day safety follow up.", "candidate_expression": "((Patient has participated in a combination trial where ruxolitinib was dispensed in combination with another study medication and the patient is still receiving combination therapy) AND (Pregnant or nursing (lactating) women, where pregnancy is defined as the state of a female after conception and until the termination of gestation, confirmed by a positive hCG laboratory test.) AND (Women of child-bearing potential, defined as all women physiologically capable of becoming pregnant, unless they are using highly effective methods of contraception throughout the study duration inclusive of the 30-day safety follow up))"}
{"candidate_id": "LLM04752", "doc_id": "NCT03631355_exc", "case_bucket": "or", "source_criterion": "Legally incompetent or mentally impaired (e.g., minors, Alzheimer's subjects, dementia, etc.) Younger than 18 years of age Any patient considered a vulnerable subject Have bleeding or clotting disorder Preoperative anticoagulation therapy Abnormal coagulation profile Renal disorder or insufficiency Sickle cell disease", "candidate_expression": "((Abnormal coagulation profile) AND (Sickle cell disease) AND (age Younger than 18 years) AND (anticoagulation) AND (anticoagulation therapy Preoperative) AND (coagulation profile Abnormal) AND (vulnerable subject) AND ((Legally incompetent) OR (mentally impaired)) AND ((bleeding disorder) OR (clotting disorder)) AND ((Renal disorder) OR (Renal insufficiency)) AND ((Alzheimer's) OR (dementia) OR (minors)))"}
{"candidate_id": "LLM04753", "doc_id": "NCT02609048_inc", "case_bucket": "or", "source_criterion": "1. Must have given written informed consent (signed and dated) and any authorizations required by local law 2. 18 to 75 years old (inclusive) 3. Male or female with a diagnosis of PBC, by at least two of the following criteria: History of AP above ULN for at least six months Positive Anti-Mitochondrial Antibodies (AMA) titers (>1/40 on immunofluorescence or M2 positive by enzyme linked immunosorbent assay (ELISA) or positive PBC-specific antinuclear antibodies Documented liver biopsy result consistent with PBC 4. On a stable and recommended dose of UDCA for the past twelve months 5. AP ≥ 1.67 × ULN 6. For females of reproductive potential, use of at least one barrier contraceptive and a second effective birth control method during the study and for at least two weeks after the last dose. For male subjects, use of appropriate contraception (e.g., condoms), so their female partners of reproductive potential do not become pregnant during the study and for at least two weeks after the last dose", "candidate_expression": "((18 to 75 years old (inclusive)) AND (>1/40) AND (AP) AND (For male subjects, use of appropriate contraception (e.g., condoms), so their female partners of reproductive potential do not become pregnant during the study and for at least two weeks after the last dose) AND (M2 positive) AND (Male) AND (Must have given written informed consent (signed and dated) and any authorizations required by local law) AND (PBC) AND (PBC-specific antinuclear antibodies) AND (Positive Anti-Mitochondrial Antibodies (AMA) titers) AND (UDCA) AND (above ULN) AND (appropriate) AND (at least one) AND (at least two) AND (barrier contraceptive) AND (birth control method) AND (condoms) AND (contraception) AND (during the study) AND (effective) AND (enzyme linked immunosorbent assay (ELISA)) AND (female) AND (females) AND (following criteria) AND (for at least six months) AND (for at least two weeks after the last dose) AND (for the past twelve months) AND (immunofluorescence) AND (liver biopsy) AND (male) AND (not become) AND (positive) AND (pregnant) AND (recommended dose) AND (reproductive potential) AND (second) AND (stable dose) AND (the last dose) AND (years old) AND (≥ 1.67 × ULN))"}
{"candidate_id": "LLM04754", "doc_id": "NCT00279552_exc", "case_bucket": "or", "source_criterion": "Patients who were pregnant, nursing or not able to give written informed consent were excluded.", "candidate_expression": "((able to give written informed consent) AND (not) AND ((nursing) OR (pregnant)))"}
{"candidate_id": "LLM04755", "doc_id": "NCT03623789_inc", "case_bucket": "or", "source_criterion": "Patients with osteoarthritis of the hip secondary to degeneration, inflammatory arthritis, gouty arthritis, acetabular dysplasia or osteonecrosis of the femoral head, and undergoing primary unilateral minimally invasive THA Age > 18 years and < 90 years Failure of medical treatment or rehabilitation. Hemoglobin > 11g/dl, No use of non-steroid anti-inflammatory agent one week before operation", "candidate_expression": "((Age > 18 years < 90 years) AND (Hemoglobin > 11g/dl) AND (acetabular dysplasia) AND (degeneration) AND (gouty arthritis) AND (inflammatory arthritis) AND (medical treatment) AND (minimally invasive THA undergoing primary unilateral) AND (osteoarthritis hip secondary to degeneration) AND (osteonecrosis) AND (rehabilitation) AND NOT (non-steroid anti-inflammatory agent one week before operation))"}
{"candidate_id": "LLM04756", "doc_id": "NCT02330705_exc", "case_bucket": "or", "source_criterion": "Advanced male factor infertility. Polycystic ovary syndrome (PCOS) as defined by the Rotterdam criteria. Endometriosis. Tubal disease. Uterine abnormalities or myoma. Previous uterine surgery. Metabolic or hormonal abnormalities.", "candidate_expression": "((Endometriosis) AND (Metabolic abnormalities) AND (Polycystic ovary syndrome (PCOS) Rotterdam criteria) AND (Tubal disease) AND (Uterine abnormalities) AND (hormonal abnormalities) AND (male factor infertility Advanced) AND (myoma) AND (uterine surgery Previous))"}
{"candidate_id": "LLM04757", "doc_id": "NCT02821819_exc", "case_bucket": "other", "source_criterion": "PCOS patients Allergy to gonadotrophins Concomitant participation in other trial", "candidate_expression": "((Allergy) AND (Concomitant participation in other trial) AND (PCOS) AND (gonadotrophins))"}
{"candidate_id": "LLM04758", "doc_id": "NCT01909934_inc", "case_bucket": "or", "source_criterion": "Male or female patients age 18 years or older, with relapsed or refractory sALCL who have previously received at least 1 multiagent chemotherapy Bidimensional measurable disease An Eastern Cooperative Oncology Group (ECOG) performance status of 0 or 1 Female patients who are postmenopausal for at least 1 year before the screening visit, surgically sterile, or agree to practice 2 effective methods of contraception, at the same time, from the time of signing the informed consent form through 30 days after the last dose of study drug, or agree to practice true abstinence Male patients who agree to practice effective barrier contraception during the entire study treatment period through 6 months after the last dose of study drug or agree to practice true abstinence Clinical laboratory values as specified in the study protocol", "candidate_expression": "((0 or 1) AND (18 years or older) AND (ECOG) AND (Eastern Cooperative Oncology Group performance status) AND (Female patients who are postmenopausal for at least 1 year before the screening visit, surgically sterile, or agree to practice 2 effective methods of contraception, at the same time, from the time of signing the informed consent form through 30 days after the last dose of study drug, or agree to practice true abstinence) AND (Male) AND (Male patients who agree to practice effective barrier contraception during the entire study treatment period through 6 months after the last dose of study drug or agree to practice true abstinence) AND (age) AND (at least 1) AND (chemotherapy) AND (female) AND (refractory) AND (relapsed) AND (sALCL))"}
{"candidate_id": "LLM04759", "doc_id": "NCT02924090_exc", "case_bucket": "or", "source_criterion": "Relative contraindications to ECT therapy (recent MI or CVA, increased intracranial pressure, intracranial mass lesion, intracranial aneurysm, epilepsy, known cardiac arrhythmia, pheochromocytoma, pregnancy) Contraindications to etomidate (sepsis, primary or secondary adrenal insufficiency, porphyria) DSM-V diagnosis of a lifetime history of psychotic spectrum disorder Drug or alcohol dependence, or abuse within the past 3 months, soy-bean oil allergy", "candidate_expression": "((CVA) AND (Contraindications) AND (Drug abuse) AND (Drug dependence) AND (ECT therapy) AND (MI) AND (Relative contraindications) AND (adrenal insufficiency) AND (alcohol abuse) AND (alcohol dependence) AND (cardiac arrhythmia) AND (epilepsy) AND (etomidate) AND (intracranial aneurysm) AND (intracranial mass lesion) AND (intracranial pressure increased) AND (pheochromocytoma) AND (porphyria) AND (pregnancy) AND (psychotic spectrum disorder DSM-V lifetime history) AND (sepsis primary secondary) AND (soy-bean oil allergy))"}
{"candidate_id": "LLM04760", "doc_id": "NCT02584140_exc", "case_bucket": "or", "source_criterion": "Pregnancy at enrollment. Any condition, which in the opinion of the provider, will seriously compromise the participant's ability to comply with the protocol, including adherence to PrEP medication dosing, such as active, untreated or unstable major mental illness (i.e. untreated psychotic disorder). Use of prohibited medications, in particular, agents known to be nephrotoxic or drugs slow in renal excretion. Previous participation in an HIV vaccine trial. Participants that were documented to have received only placebo are not excluded. Signs or symptoms suspicious for Primary HIV Infection (PHI).", "candidate_expression": "((Any condition, which in the opinion of the provider, will seriously compromise the participant's ability to comply with the protocol, including adherence to PrEP medication dosing, such as active, untreated or unstable major mental illness (i.e. untreated psychotic disorder)) AND (HIV vaccine trial) AND (PHI) AND (Participants) AND (Pregnancy) AND (Previous) AND (Primary HIV Infection) AND (at enrollment) AND (enrollment) AND (nephrotoxic) AND (not) AND (participation) AND (placebo) AND (slow in renal excretion) AND ((Signs) OR (symptoms)) AND ((agents) OR (drugs)))"}
{"candidate_id": "LLM04761", "doc_id": "NCT03027115_inc", "case_bucket": "other", "source_criterion": "Male 18 years of age Presenting with hernia requiring surgical intervention", "candidate_expression": "((Male) AND (age 18 years) AND (hernia) AND (surgical intervention requiring))"}
{"candidate_id": "LLM04762", "doc_id": "NCT02269137_exc", "case_bucket": "or", "source_criterion": "hypoglycemia SE;psychogenic SE;any other pseudo-SE", "candidate_expression": "((hypoglycemia SE) OR (pseudo-SE) OR (psychogenic SE))"}
{"candidate_id": "LLM04763", "doc_id": "NCT02645474_exc", "case_bucket": "or", "source_criterion": "patients' refusal contraindication to regional anaesthesia (coagulopathies, concurrent anticoagulant therapy, allergy to local anaesthetics, infection at puncture site)", "candidate_expression": "((contraindication) AND (local anaesthetics) AND (patients' refusal) AND (puncture site) AND (regional anaesthesia () AND ((allergy) OR (anticoagulant therapy) OR (coagulopathies) OR (infection)))"}
{"candidate_id": "LLM04764", "doc_id": "NCT03216447_inc", "case_bucket": "other", "source_criterion": "Patient has been fully informed and has signed an IRB approved informed consent form within 7 days (Day 7-13) prior to POD 15 and is willing and able to follow study procedure Patient is a primary liver transplant recipient Patient is 20 to 70 years of age Patient should be clearly conscious, fully understand and able to answer questionnaire", "candidate_expression": "((20 to 70 years) AND (Patient has been fully informed and has signed an IRB approved informed consent form within 7 days (Day 7-13) prior to POD 15 and is willing and able to follow study procedure) AND (Patient should be clearly conscious, fully understand and able to answer questionnaire) AND (age) AND (primary liver transplant) AND (recipient))"}
{"candidate_id": "LLM04765", "doc_id": "NCT02627560_inc", "case_bucket": "other", "source_criterion": "breast cancer undergoing unilateral mastectomy with or without axillary node dissection received adequate oral and written information about the study and signed an informed-consent form", "candidate_expression": "((axillary node dissection) AND (breast cancer) AND (received adequate oral and written information about the study and signed an informed-consent form) AND (undergoing) AND (unilateral mastectomy))"}
{"candidate_id": "LLM04766", "doc_id": "NCT02858804_exc", "case_bucket": "or", "source_criterion": "with centre neural system involvement serious complications such as uncontrolled diabetes, gastric ulcer or other serious angiocardiopathy determined by the physician HIV positive or active HBV infection or other uncontrolled systematic infection clinical central nervous dysfunction serious surgery within 30 days pregnancy or baby nursing period or un-contracepted child bearing period woman.", "candidate_expression": "((central nervous dysfunction) AND (centre neural system involvement) AND (complications) AND (contracepted) AND (determined by the physician) AND (serious) AND (surgery) AND (un-) AND (uncontrolled) AND (within 30 days) AND (woman) AND ((HIV positive) OR (active HBV infection) OR (systematic infection)) AND ((baby nursing period) OR (child bearing period) OR (pregnancy)) AND ((angiocardiopathy) OR (diabetes) OR (gastric ulcer)))"}
{"candidate_id": "LLM04767", "doc_id": "NCT01177891_exc", "case_bucket": "or", "source_criterion": "Blood donation of more than 450ml in the previous three months. Subject with an abnormal karyotype in favor of Turner syndrome or having a premutation of the FMR1 gene or a syndromic form Subject exclusion period in another study without direct individual benefit Subject refusing to sign the consent form", "candidate_expression": "((Blood donation) AND (Subject exclusion period in another study without direct individual benefit) AND (Subject refusing to sign the consent form) AND (Turner syndrome) AND (abnormal karyotype) AND (in the previous three months) AND (more than 450ml) AND (of more than 450ml) AND (premutation of the FMR1 gene) AND (syndromic form))"}
{"candidate_id": "LLM04768", "doc_id": "NCT02167022_exc", "case_bucket": "other", "source_criterion": "1. Diagnosis: Diagnosis of CP secondary to neuronal migration. 2. Co-morbidities: Medical conditions that may prevent the administration of rehabilitation therapies at the intensity required by the study, or that may compromise the study ability to maintain blindness, or that have a co-morbidity not typically associated with CP (i.e. cancer, cystic fibrosis). 3. Co-interventions: Anticipated pharmacological intervention or procedure or participation in other studies that may interfere with this study.", "candidate_expression": "((CP secondary to neuronal migration) AND (Co-interventions: Anticipated pharmacological intervention or procedure or participation in other studies that may interfere with this study.))"}
{"candidate_id": "LLM04769", "doc_id": "NCT01665417_exc", "case_bucket": "or", "source_criterion": "Prior chemotherapy Prior treatment with gefitinib, erlotinib, or other drugs that target EGFR Patients must not be receiving any other investigational agents Any evidence of interstitial lung disease", "candidate_expression": "((Patients must not be receiving any other investigational agents) AND (Prior) AND (chemotherapy) AND (interstitial lung disease) AND (treatment) AND ((drugs that target EGFR) OR (erlotinib) OR (gefitinib)))"}
{"candidate_id": "LLM04770", "doc_id": "NCT03355469_exc", "case_bucket": "or", "source_criterion": "Morbidly obese patients (BMI >47 kg/m2) and overweight/lean patients (BMI <27 kg/m2) Evidence of type 1 diabetes and diabetics requiring insulin therapy. Subjects who have not been weight stable (>2 kg weight change in past 3 months) Subjects who have been recently active (>30 min of moderate/high intensity exercise, 2 times/week). Subjects who are smokers or who have quit smoking <5 years ago Subjects prescribed metformin or have taken metformin within 1 year. Subjects with abnormal estimated glomerular filtration rate (eGFR). Hypertriglyceridemic (>400 mg/dl) and hypercholesterolemic (>260 mg/dl) subjects Hypertensive (>160/100 mmHg) Subjects currently taking medications that affect heart rate and rhythm (i.e. Ca++ channel blockers, nitrates, alpha- or beta-blockers). Subjects with a history of significant metabolic, cardiac, congestive heart failure, cerebrovascular, hematological, pulmonary, gastrointestinal, liver, renal, or endocrine disease or cancer that in the investigator's opinion would interfere with or alter the outcome measures, or impact subject safety. Pregnant (as evidenced by positive pregnancy test) or nursing women Subjects with contraindications to participation in an exercise training program Currently taking active weight suppression medication (e.g. phentermine,orlistat, lorcaserin, naltrexone-bupropion in combination, liraglutide, benzephetamine, diethylpropion, phendimetrazine) Known hypersensitivity to perflutren (contained in Definity)", "candidate_expression": "((BMI <27 kg/m2) AND (BMI >47 kg/m2) AND (Ca++ channel blockers) AND (Definity) AND (Hypertensive) AND (Hypertensive >160/100 mmHg) AND (Hypertriglyceridemic) AND (Hypertriglyceridemic >400 mg/dl) AND (Morbidly obese) AND (Pregnant) AND (active) AND (active weight suppression medication) AND (alpha- blockers metabolic) AND (benzephetamine) AND (beta-blockers) AND (cancer) AND (cholesterol >260 mg/dl) AND (congestive heart failure cardiac cerebrovascular hematological pulmonary gastrointestinal) AND (contraindications participation in an exercise training program) AND (diabetics requiring insulin therapy) AND (diethylpropion) AND (disease liver renal endocrine) AND (estimated glomerular filtration rate (eGFR) abnormal) AND (hypercholesterolemic) AND (hypersensitivity) AND (insulin) AND (insulin therapy) AND (lean) AND (liraglutide) AND (lorcaserin) AND (medications that affect heart rhythm that affect heart rate) AND (metformin) AND (metformin within 1 year) AND (moderate/high intensity exercise >30 min 2 times/week) AND (naltrexone-bupropion in combination) AND (nitrates) AND (nursing) AND (orlistat) AND (overweight) AND (perflutren) AND (phendimetrazine) AND (phentermine) AND (pregnancy test positive) AND (quit smoking <5 years ago) AND (smokers) AND (type 1 diabetes) AND (weight change >2 kg in past 3 months) AND (women) AND NOT (weight stable))"}
{"candidate_id": "LLM04771", "doc_id": "NCT02893293_inc", "case_bucket": "other", "source_criterion": "Osteonecrosis planned decompression surgery with autologous stem cell transplant", "candidate_expression": "((Osteonecrosis) AND (autologous stem cell transplant) AND (decompression surgery planned))"}
{"candidate_id": "LLM04772", "doc_id": "NCT02807857_exc", "case_bucket": "or", "source_criterion": "Use of investigational drugs either within 5 half-lives of enrollment, or within 30 days, or until the expected pharmacodynamic effect has returned to baseline, whichever is longer. Major surgery in the last 3 months prior to baseline or planned major surgery or cardiac intervention during the study. Cancer or other significant co-morbidities implying that the patient's condition is unstable. Comorbidities that can be associated with elevated natriuretic peptide (NP) levels: renal insufficiency, (eGFR < 25 ml/min/1.73 m² calculated according to MDRD formula), recent (less than 3 months) cerebral trauma or recent (less than 3 months) cerebrovascular incident, novel diagnosis or acute exacerbation of COPD within the last 3 months. Patients who are primarily managed and regularly followed-up by a cardiologist for their HF Highly frail patients whose estimated lifespan due to comorbidities by the judgement of the investigator is less than 6 months.", "candidate_expression": "((Comorbidities) AND (Major surgery last 3 months prior to baseline or planned major surgery or cardiac intervention during the study) AND (NP) AND (eGFR < 25 ml/min/1.73 m²) AND (lifespan less than 6 months) AND (natriuretic peptide levels elevated) AND ((acute exacerbation of COPD last 3 months) OR (cerebral trauma less than 3 months) OR (cerebrovascular incident less than 3 months) OR (renal insufficiency)) AND ((Cancer) OR (co-morbidities)))"}
{"candidate_id": "LLM04773", "doc_id": "NCT00094861_exc", "case_bucket": "or", "source_criterion": "Metastatic disease (M1)/stage 4 NSCLC Pleural or pericardial effusion greater than 100 ml in volume as documented by appropriate imaging (positron emission tomography [PET], computed tomography [CT] scan or ultrasound). If an effusion greater than 100 ml is documented by cytology to be free from malignancy and the investigator feels the patient is capable of receiving chemo/radiotherapy for their primary disease/ NSCLC, the investigator should discuss the patient with the study physician at Amgen. Effusions smaller than 100 ml would be acceptable, unless the investigator suspects that the effusion is malignant, in which case the effusions should be evaluated by cytology. Sponsor approval must be obtained before patient is randomized. Plan to remove the tumor surgically before completing the protocol chemo/radiotherapy course Shielding of any part of the esophagus during radiotherapy (including posterior spinal cord shielding) Prior chemotherapy, radiotherapy, or surgery for NSCLC Prior invasive malignancy during the past 3 years other than non-melanomatous skin cancer. Note: Patients with prior surgically-cured malignancies [eg, stage I breast cancer or prostate cancer, in-situ carcinoma of the cervix, etc] are not excluded; however, sponsor approval must be obtained before patient is randomized. Presence or history of dysphagia or conditions predisposing to dysphagia (eg, uncontrolled gastroesophageal reflux disease [GERD], dyspepsia, etc) History of pancreatitis Four weeks or less since completion of treatment using an investigational product/device in another clinical study or presence of any unresolved toxicity from previous treatment Previous treatment on this study or with a fibroblast growth factor Known to be sero-positive for human immunodeficiency virus (HIV), hepatitis C virus (HCV), or hepatitis B virus (HBV) Pregnant or breastfeeding women Known sensitivity to E. coli derived products Compromised ability of the patient to give written informed consent and/or to comply with study procedures Refusal to sign an informed consent form to participate in this study, and sign the hospital information release form, if applicable Unwilling or unable to complete the patient reported outcome (PRO) questionnaires Psychological, social, familial, or geographical reasons that would prevent regular follow-up", "candidate_expression": "(((M1)/stage 4) AND (CT) AND (Compromised ability) AND (GERD) AND (Metastatic disease NSCLC) AND (NSCLC) AND (PET) AND (Plan to remove the tumor surgically before completing the protocol chemo/radiotherapy course) AND (Pleural effusion) AND (Pregnant) AND (Shielding esophagus) AND (another clinical study) AND (breastfeeding) AND (chemotherapy) AND (computed tomography scan) AND (conditions predisposing to dysphagia) AND (dyspepsia) AND (dysphagia) AND (fibroblast growth factor) AND (gastroesophageal reflux disease uncontrolled) AND (give written informed consent) AND (hepatitis B virus (HBV) sero-positive) AND (hepatitis C virus (HCV) sero-positive) AND (human immunodeficiency virus (HIV) sero-positive) AND (investigational device) AND (investigational product) AND (malignancy Prior invasive during the past 3 years) AND (pancreatitis History of) AND (pericardial effusion) AND (positron emission tomography) AND (posterior spinal cord shielding) AND (products E. coli derived) AND (radiotherapy) AND (sensitivity) AND (sero-positive for hepatitis B virus (HBV)) AND (sero-positive for hepatitis C virus (HCV)) AND (sero-positive for human immunodeficiency virus (HIV)) AND (sign an informed consent form Refusal to) AND (sign the hospital information release form Refusal to) AND (surgery) AND (toxicity unresolved) AND (treatment) AND (treatment Previous) AND (treatment previous) AND (ultrasound) AND (women) AND NOT (non-melanomatous skin cancer) AND NOT (surgically-cured malignancies))"}
{"candidate_id": "LLM04774", "doc_id": "NCT02321202_inc", "case_bucket": "other", "source_criterion": "The cirrhotic malnourished patients who were diagnosed as liver cancer preoperatively and underwent hepatectomy were consecutively enrolled.", "candidate_expression": "((cirrhotic) AND (hepatectomy) AND (liver cancer) AND (malnourished) AND (preoperatively))"}
{"candidate_id": "LLM04775", "doc_id": "NCT02744976_exc", "case_bucket": "or", "source_criterion": "cardiac or non-cardiac illness with life expectancy of less than two years; failure to advance the IVUS catheter through the culprit lesion; acute coronary syndrome congestive heart failure NYHA III-IV diabetes mellitus chronic kidney disease previous PCI in the target vessel heavily calcified vessels allergy to metformin", "candidate_expression": "((III-IV) AND (IVUS catheter) AND (NYHA) AND (PCI) AND (acute coronary syndrome) AND (advance the IVUS catheter) AND (allergy) AND (cardiac illness) AND (chronic kidney disease) AND (congestive heart failure) AND (culprit lesion) AND (diabetes mellitus) AND (failure) AND (heavily calcified vessels) AND (less than two years) AND (life expectancy) AND (metformin) AND (non-cardiac illness) AND (previous) AND (target vessel))"}
```
