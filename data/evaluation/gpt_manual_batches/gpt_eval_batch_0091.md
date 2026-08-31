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
{"candidate_id": "LLM02251", "doc_id": "NCT03250507_exc", "case_bucket": "or", "source_criterion": "Patient with a chronic pain condition, major unexpected surgical complication, unexpected prolonged intubation, patient refusal, local anesthetic allergy, any contraindication to regional anesthesia, greater than 2 attempts by resident and greater than 1 attempt by staff anesthesiologist for TAP block.", "candidate_expression": "((anesthesiologist greater than 1) AND (local anesthetic) AND (regional anesthesia) AND (resident greater than 2) AND ((TAP block) OR (allergy) OR (chronic pain condition) OR (contraindication) OR (intubation unexpected prolonged) OR (patient refusal) OR (unexpected surgical complication major)))"}
{"candidate_id": "LLM02252", "doc_id": "NCT02284737_inc", "case_bucket": "or", "source_criterion": "Provision of informed consent prior to any study specific procedures; Men and women 18 years and older; Group I PAH, defined as a mPAP=25mmHg, PCWP<15mmHg and PVR[The PVR =(mPAP-PCWP)/CO]>3.0 Woods unit.", "candidate_expression": "(((mPAP-PCWP)/CO) AND (18 years and older) AND (<15mmHg) AND (=25mmHg) AND (>3.0 Woods unit) AND (Group I) AND (PAH) AND (PCWP) AND (PVR) AND (mPAP) AND (years) AND ((Men) OR (women)))"}
{"candidate_id": "LLM02253", "doc_id": "NCT03208244_exc", "case_bucket": "other", "source_criterion": "Sensitization (i.e. PRA >20%) Any liver disease in recipient Albumin < 3g/dl or platelet count < 75 x 103/mL Need for dual organ transplant", "candidate_expression": "((< 3g/dl) AND (< 75 x 103/mL) AND (>20%) AND (Albumin) AND (Need for) AND (PRA) AND (Sensitization) AND (dual organ transplant) AND (liver disease) AND (platelet count))"}
{"candidate_id": "LLM02254", "doc_id": "NCT00926523_inc", "case_bucket": "other", "source_criterion": "Subject are at least 18 years of age Subject has confirmed Pulmonary Hypertension and Interstitial Lung Disease Subject are able to complete study procedures, such as spirometry, and Pulmonary Exercise test.", "candidate_expression": "((Interstitial Lung Disease confirmed) AND (Pulmonary Exercise test) AND (Pulmonary Hypertension confirmed) AND (age at least 18 years) AND (spirometry) AND (study procedures))"}
{"candidate_id": "LLM02255", "doc_id": "NCT02892968_exc", "case_bucket": "or", "source_criterion": "ED physicians who work casually (less than 0.25 Full Time Equivalent) ED Physicians who are routinely using U/S guided RA for hip fracture patients, or decline participation in the trial. Patients' age less than 65 years; Patients who are delirious on initial assessment by ED physician or severe dementia Patients with communication problems (critically ill, unconscious, language barrier despite use of secure telephone-based translation service) Patients with allergies to narcotics or local anesthetic; or anticoagulant use (e.g. warfarin, dabigatran, rivaroxaban). Patients with hip fractures not requiring surgery (e.g. greater trochanter avulsion) will also be excluded.", "candidate_expression": "((age) AND (allergies) AND (anticoagulant) AND (communication problems) AND (critically ill) AND (dabigatran) AND (delirious) AND (dementia) AND (greater trochanter avulsion) AND (hip fractures) AND (initial assessment) AND (language barrier) AND (less than 65 years) AND (local anesthetic) AND (narcotics) AND (not) AND (on initial assessment) AND (requiring surgery) AND (rivaroxaban) AND (severe) AND (surgery) AND (unconscious) AND (warfarin))"}
{"candidate_id": "LLM02256", "doc_id": "NCT02548013_exc", "case_bucket": "other", "source_criterion": "1. Patient with equivocal diagnosis of rupture of membranes 2. advanced labor 3. intrauterine infection 4. vaginal bleeding or 5. non reassuring fetal heart rate.", "candidate_expression": "((advanced labor) AND (equivocal) AND (fetal heart rate) AND (intrauterine infection) AND (non reassuring) AND (rupture of membranes) AND (vaginal bleeding))"}
{"candidate_id": "LLM02257", "doc_id": "NCT02788045_exc", "case_bucket": "or", "source_criterion": "Has chronic hepatitis B (measured by hepatitis B surface antigen test) or active hepatitis C (measured by hepatitis C virus [HCV] Ab test; if positive, HCV ribonucleic acid [RNA] PCR test will be used to confirm active versus past HCV infection), active syphilis infection, chlamydia, gonorrhea, or trichomonas . Active syphilis documented by serology unless positive serology is due to past treated infection Has had a thyroidectomy or active thyroid disease requiring medication during the last 12 months (not excluded: a stable thyroid supplementation) Has had major psychiatric illness and/or substance abuse problems during the past 12 months (including hospitalization or periods of work disability) that in the opinion of the investigator would preclude participation Has been in receipt of any licensed vaccine within 14 days prior to the first dose of study vaccine/placebo, plans to receive within 14 days after the first study vaccination, or plans to receive within 14 days before or after the second, third or fourth vaccination Is a recipient of a prophylactic or therapeutic HIV vaccine candidate at any time, or a recipient of other experimental vaccine(s) within the last 12 months. For participants who received an experimental vaccine (except HIV vaccine) more than 12 months ago, documentation of the identity of the experimental vaccine must be provided to the sponsor, who will determine eligibility on a case-by-case basis", "candidate_expression": "((HCV ribonucleic acid [RNA] PCR test) AND (HIV vaccine candidate at any time therapeutic) AND (active hepatitis C) AND (case-by-case basis) AND (chlamydia) AND (chronic hepatitis B) AND (experimental vaccine more than 12 months ago) AND (gonorrhea) AND (hepatitis B surface antigen test) AND (hepatitis C virus [HCV] Ab test positive) AND (hospitalization) AND (in the opinion of the investigator) AND (licensed vaccine within 14 days prior) AND (medication during the last 12 months) AND (other experimental vaccine(s) within the last 12 months) AND (placebo within 14 days after) AND (psychiatric illness major) AND (serology) AND (study vaccination first study vaccination within 14 days before or after) AND (study vaccine) AND (substance abuse) AND (syphilis Active) AND (syphilis infection active) AND (thyroid disease active) AND (thyroidectomy) AND (treated infection) AND (trichomonas) AND (vaccination prophylactic) AND (work disability) AND NOT (serology positive) AND NOT (thyroid supplementation stable) AND NOT (HIV vaccine))"}
{"candidate_id": "LLM02258", "doc_id": "NCT03372265_exc", "case_bucket": "or", "source_criterion": "Allergy to LA Infection in or near insertion site of the peripheral nerve catheter Anatomical abnormalities preventing successful peripheral catheter insertion Habitual use of opioids Pregnancy or breastfeeding (disproved by a negative pregnancy test before trial inclusion)", "candidate_expression": "((Allergy) AND (Anatomical abnormalities) AND (Habitual use) AND (LA) AND (before trial inclusion) AND (disproved by) AND (insertion) AND (negative) AND (opioids) AND (peripheral catheter) AND (peripheral nerve catheter) AND (pregnancy test) AND (preventing) AND (successful) AND (trial inclusion) AND ((Pregnancy) OR (breastfeeding)) AND ((in insertion site) OR (near insertion site)))"}
{"candidate_id": "LLM02259", "doc_id": "NCT00609531_inc", "case_bucket": "or", "source_criterion": "Ambulatory status (outpatient) at time of consent Age 10-55 years Clinical diagnosis of Autism Spectrum Disorder IQ greater than or equal to 70 Score greater than 8 on Children's Yale-Brown Obsessive Compulsive Scale Free of psychoactive medication for at least: one month for fluoxetine; two weeks for other SSRIs and neuroleptics; and five days for stimulants prior to MRI scanning [excepting stable doses (greater than three months duration) of anticonvulsant medication for seizure disorder]", "candidate_expression": "((10-55 years) AND (Age) AND (Ambulatory status) AND (Autism Spectrum Disorder) AND (Children's Yale-Brown Obsessive Compulsive Scale) AND (Clinical diagnosis) AND (Free of) AND (IQ) AND (anticonvulsant medication) AND (at least five days) AND (at least one month) AND (at least two weeks) AND (at time of consent) AND (excepting) AND (greater than 8) AND (greater than or equal to 70) AND (greater than three months) AND (outpatient) AND (prior to MRI scanning) AND (psychoactive medication) AND (seizure disorder) AND (stable doses) AND ((fluoxetine) OR (stimulants)) AND ((SSRIs) OR (neuroleptics)))"}
{"candidate_id": "LLM02260", "doc_id": "NCT01856491_inc", "case_bucket": "or", "source_criterion": "Willing and capable of providing informed consent Has an indication for implantation of a single or dual chamber ICD or CRT-D system in their respective geography Subjects planned to be implanted with the RELIANCE 4-FRONT Passive Fixation Lead Willing and capable of participating in all testing/ visits associated with this clinical study at an approved clinical study center and at the intervals defined by this protocol Age 18 or above, or of legal age to give informed consent specific to state and national law", "candidate_expression": "((18 or above) AND (Age) AND (CRT-D system implantation of a) AND (RELIANCE 4-FRONT Passive Fixation Lead) AND (Willing and capable of providing informed consent) AND (chamber ICD implantation of a single) AND (dual chamber ICD implantation of a) AND (implanted with the RELIANCE 4-FRONT Passive Fixation Lead) AND (indication) AND (of legal age) AND (planned))"}
{"candidate_id": "LLM02261", "doc_id": "NCT03345589_inc", "case_bucket": "other", "source_criterion": "Patients diagnosed with primary biliary cholangitis Treated with Ursodeoxycholic Acid in West China Hospital for at least 6 month and suboptimal response to Ursodeoxycholic Acid", "candidate_expression": "((Ursodeoxycholic Acid) AND (Ursodeoxycholic Acid for at least 6 month) AND (West China Hospital) AND (primary biliary cholangitis) AND (suboptimal response))"}
{"candidate_id": "LLM02262", "doc_id": "NCT01943409_exc", "case_bucket": "other", "source_criterion": "• Patients without PN during their hospitalization", "candidate_expression": "((PN) AND (during their hospitalization) AND (hospitalization) AND (their hospitalization) AND (without))"}
{"candidate_id": "LLM02263", "doc_id": "NCT03099863_exc", "case_bucket": "or", "source_criterion": "Surgeries that include: intradetrusor Botox, vaginal mesh excision, and fistula repair Pregnancy History of nephrolithiasis Allergy to study medications Congenital urogenital anomaly Neurogenic bladder", "candidate_expression": "((Allergy) AND (Botox intradetrusor) AND (Neurogenic bladder) AND (Pregnancy) AND (fistula repair) AND (nephrolithiasis History) AND (study medications) AND (urogenital anomaly Congenital) AND (vaginal mesh) AND (vaginal mesh excision))"}
{"candidate_id": "LLM02264", "doc_id": "NCT00846703_inc", "case_bucket": "or", "source_criterion": "Cytologically proven acute lymphoblastic leukemia (ALL) No relapse of a previously unrecognized ALL Patients must meet one of the following risk criteria: Standard-risk (SR) group meeting all of the following criteria: Blasts < 1,000/µL in peripheral blood (PB) on day 8 Aged 1 to < 6 years Initial WBC < 20,000/µL M1 (5%) or M2 (= 5% to < 25%) blasts in bone marrow on day 15; M1 marrow on day 33. Aged < 1 or = 6 years and/or WBC = 20,000/µL Blasts < 1,000/µL in PB on day 8 M1 or M2 marrow on day 15 M3 (= 25%) marrow on day 15 OR meets SR criteria but M3 marrow on day 15 and *M1 marrow on day 33. Meets IR criteria and M3 marrow on day 15 (not SR and M3 on day 15) Blasts = 1,000/µL in PB on day 8 M2 or M3 marrow on day 33 Translocation t(9;22) [BCR/ABL+] (Philadelphia chromosome-positive) or t(4;11) [MLL/AF4+].", "candidate_expression": "(((5%) AND (+) AND (1 to < 6 years) AND (< 1 or = 6 years) AND (< 1,000/µL) AND (< 20,000/µL) AND (= 1,000/µL) AND (= 20,000/µL) AND (= 25%) AND (= 5% to < 25%) AND (ALL) AND (Aged) AND (BCR/ABL) AND (Blasts) AND (Cytologically proven) AND (IR criteria) AND (Initial) AND (M1 blasts) AND (M1 marrow) AND (M2 blasts) AND (M2 marrow) AND (M3) AND (M3 marrow) AND (MLL/AF4) AND (Meets) AND (No) AND (PB) AND (Philadelphia chromosome) AND (SR) AND (SR criteria) AND (Standard-risk) AND (Translocation t(9;22)) AND (WBC) AND (acute lymphoblastic leukemia) AND (all) AND (bone marrow) AND (criteria) AND (meets) AND (not) AND (on day 15) AND (on day 33) AND (on day 8) AND (peripheral blood) AND (positive) AND (previously unrecognized) AND (relapse) AND (t(4;11)))"}
{"candidate_id": "LLM02265", "doc_id": "NCT02416869_exc", "case_bucket": "or", "source_criterion": "Heavy tobacco smokers Drug and / or alcohol abusers", "candidate_expression": "((Heavy tobacco smokers) AND ((Drug abusers) OR (alcohol abusers)))"}
{"candidate_id": "LLM02266", "doc_id": "NCT02570230_inc", "case_bucket": "other", "source_criterion": "ASA physical status 1-3 elective thoracotomy can operate patient-controlled analgesia (PCA) machine", "candidate_expression": "((ASA physical status 1-3) AND (thoracotomy elective))"}
{"candidate_id": "LLM02267", "doc_id": "NCT02379156_exc", "case_bucket": "or", "source_criterion": "Evidence of sympathetic integrity below the lesion level by the skin axon-reflex vasodilatation (SkARV) test; Known allergies to midodrine hydrochloride; PMH of diagnosed heart, kidney, peripheral vascular, or cerebral vascular disease, or diabetes mellitus; Hypertension (BP>140/90 mmHg); Untreated thyroid disease; Acute illness or infection; Current smoker; Pregnancy.", "candidate_expression": "((BP >140/90 mmHg) AND (Hypertension) AND (Pregnancy) AND (SkARV) AND (allergies) AND (midodrine hydrochloride) AND (smoker) AND (test skin axon-reflex vasodilatation sympathetic integrity) AND (thyroid disease Untreated) AND ((illness) OR (infection)) AND ((cerebral vascular disease) OR (diabetes mellitus) OR (heart disease) OR (kidney disease) OR (peripheral vascular, disease)))"}
{"candidate_id": "LLM02268", "doc_id": "NCT01117181_exc", "case_bucket": "or", "source_criterion": "Meets criteria for Major Depressive Episode, by Diagnostic Statistical Manual of Mental Disorder - IV (TR) criteria Clinically significant agitation /aggression for which either 1) the frequency of agitation /aggression as assessed by the NPI is 'Very frequently', or 2) the frequency of agitation /aggression as assessed by the NPI is 'Frequently' AND the severity of the agitation as assessed by the NPI is 'Moderate', or 'Marked' Clinically significant delusions for which either 1) the frequency of delusions as assessed by the NPI is 'Very frequently', or 2) the frequency of delusions as assessed by the NPI is 'Frequently' AND the severity of the delusions as assessed by the NPI is 'Moderate', or 'Marked' Clinically significant hallucinations for which either 1) the frequency of hallucinations as assessed by the NPI is 'Very frequently', or 2) the frequency of hallucinations as assessed by the NPI is 'Frequently' AND the severity of the hallucinations as assessed by the NPI is 'Moderate', or 'Marked' Treatment with psychotropic medications in the 2 weeks prior to randomization with the exception of approved treatments for dementia (ChEIs and memantine), selective serotonin reuptake inhibitor antidepressants, and trazodone (if used as an aid to facilitate sleep and not as an antidepressant); other psychotropics (with the exclusion of antipsychotics), if stable for 3 months, may be allowed only with Steering Committee approval on a case by case basis. Note that antipsychotics are expressly prohibited. Treatment with methylphenidate is contraindicated in the opinion of the study physician Failure of treatment with methylphenidate in the past for apathy after convincing evidence of an adequate trial as judged by study physician Treatment with a medication that would prohibit the safe concurrent use of methylphenidate such as monoamine oxidase inhibitors and tricyclic antidepressants Need for acute psychiatric hospitalization or is suicidal Uncontrolled hypertension (medication non-compliance or past 3 months with a diastolic reading of 105 as verified by compartment pressure of the rectus sheath (CPRS)) Symptomatic coronary artery disease deemed to be significant by study physician at the time of screening Lack of appetite that results in significant unintentional weight loss as determined by the study physician in the last three months Significant communicative impairments Current participation in a clinical trial or in any study that may add significant burden or affect study outcomes Hyperthyroidism, advanced arteriosclerosis, symptomatic cardiovascular disease, serious structural cardiac abnormalities, cardiomyopathy, serious heart rhythm abnormalities, or a family history of sudden death or death related to heart problems Glaucoma, pheochromocytoma, or known or suspected hypersensitivity to methylphenidate or its excipients Central Nervous System (CNS) abnormalities (e.g., cerebral aneurysm) and/or other vascular abnormalities such as vasculitis or pre-existing stroke, motor tics or a family history or diagnosis of Tourette's syndrome, seizures (convulsions, epilepsy), or abnormal EEGs Any condition that, in the opinion of the study physician, makes it medically inappropriate or risky for the patient to enroll in the trial", "candidate_expression": "((105) AND (Any condition that, in the opinion of the study physician, makes it medically inappropriate or risky for the patient to enroll in the trial) AND (ChEIs) AND (Clinically significant) AND (Current participation in a clinical trial or in any study that may add significant burden or affect study outcomes) AND (Diagnostic Statistical Manual of Mental Disorder - IV (TR) criteria) AND (Frequently) AND (Lack of appetite) AND (Major Depressive Episode) AND (Meets) AND (NPI) AND (Need for) AND (Significant) AND (Symptomatic) AND (Uncontrolled) AND (Uncontrolled hypertension) AND (Very frequently) AND (abnormal) AND (acute) AND (advanced) AND (agitation) AND (agitation /aggression) AND (antipsychotics) AND (as determined by the study physician) AND (as judged by study physician) AND (as verified by compartment pressure of the rectus sheath (CPRS)) AND (at the time of screening) AND (cerebral aneurysm) AND (communicative impairments) AND (compartment pressure of the rectus sheath (CPRS)) AND (concurrent) AND (coronary artery disease) AND (delusions) AND (dementia) AND (diastolic reading) AND (family history) AND (for 3 months) AND (frequency of hallucinations) AND (hallucinations) AND (in the 2 weeks prior to randomization) AND (in the last three months) AND (medication non-compliance) AND (medication that would prohibit the safe concurrent use of methylphenidate) AND (memantine) AND (methylphenidate) AND (past 3 months) AND (pre-existing) AND (prohibit) AND (randomization) AND (related to heart problems) AND (serious) AND (significant) AND (stable) AND (symptomatic) AND (time of screening) AND (unintentional weight loss) AND (vasculitis) AND (with the exception of) AND (with the exclusion of) AND ((Hyperthyroidism) OR (arteriosclerosis) OR (cardiomyopathy) OR (cardiovascular disease) OR (heart rhythm abnormalities) OR (structural cardiac abnormalities)) AND ((death related to heart problems) OR (sudden death)) AND ((Glaucoma) OR (hypersensitivity) OR (pheochromocytoma)) AND ((its excipients) OR (methylphenidate or its excipients)) AND ((known) OR (suspected)) AND ((Central Nervous System (CNS) abnormalities) OR (EEGs) OR (Tourette's syndrome) OR (motor tics) OR (seizures) OR (stroke) OR (vascular abnormalities)) AND ((convulsions) OR (epilepsy)) AND ((diagnosis) OR (family history)) AND ((Marked) OR (Moderate)) AND ((frequency of delusions) OR (severity of the delusions)) AND ((frequency of hallucinations) OR (severity of the hallucinations)) AND ((selective serotonin reuptake inhibitor antidepressants) OR (trazodone) OR (treatments for dementia)) AND ((other psychotropics) OR (psychotropic medications)) AND ((frequency of agitation /aggression) OR (severity of the agitation)) AND ((monoamine oxidase inhibitors) OR (tricyclic antidepressants)) AND ((psychiatric hospitalization) OR (suicidal)))"}
{"candidate_id": "LLM02269", "doc_id": "NCT02406885_exc", "case_bucket": "or", "source_criterion": "History of documented clotting/coagulation disorder History of cancer (within the last year) Any diagnosis requiring anti-coagulation History of hypersensitivity reaction to apixaban Active clinically significant bleeding Creatinine > 1.5 mg/dL Participants currently receiving any type of anticoagulation or blood thinning medications, including heparin, low molecular weight heparins, Plavix, aspirin, NSAIDS Combined P-glycoprotein and strong cytochrome P450 (CYP) 3A4 inhibitor Combined P-glycoprotein and moderate CYP 3A4 inhibitor Combined P-glycoprotein inducer and strong CYP 3A4 inducer Inducers of p-glycoprotein Strong inducers of CYP 3A4", "candidate_expression": "((CYP 3A4 inducer strong) AND (CYP 3A4 inhibitor moderate) AND (Creatinine > 1.5 mg/dL) AND (Inducers of p-glycoprotein) AND (P-glycoprotein inducer) AND (P-glycoprotein inhibitor) AND (anti-coagulation) AND (apixaban) AND (bleeding Active significant) AND (cancer last year) AND (cytochrome P450 3A4 inhibitor strong) AND (hypersensitivity) AND (inducers of CYP 3A4 Strong) AND ((anticoagulation) OR (blood thinning medications)) AND ((NSAIDS) OR (Plavix) OR (aspirin) OR (heparin) OR (low molecular weight heparins)) AND ((clotting disorder) OR (coagulation disorder)))"}
{"candidate_id": "LLM02270", "doc_id": "NCT02473809_inc", "case_bucket": "other", "source_criterion": "Informed consent Diagnosis of type 2 diabetes (HbA1c > 48 mmol/mol) Age older than 30 years", "candidate_expression": "((> 48 mmol/mol) AND (Age) AND (HbA1c) AND (Informed consent) AND (older than 30 years) AND (type 2 diabetes))"}
{"candidate_id": "LLM02271", "doc_id": "NCT02903407_inc", "case_bucket": "other", "source_criterion": "All patients admitted to the Duke CICU, who require intubation and sedation for mechanical ventilation that is expected to be >24 hours in duration will be included, unless they meet the specified exclusion criteria. Patients intubated within one hour prior to care transition to the CICU will also be screened for inclusion.", "candidate_expression": "((Duke CICU) AND (admitted) AND (care transition) AND (intubated within one hour prior to care transition) AND (intubation) AND (mechanical ventilation >24 hours in duration) AND (sedation))"}
{"candidate_id": "LLM02272", "doc_id": "NCT03467750_inc", "case_bucket": "or", "source_criterion": "Diagnosis of sleep disordered breathing or obstructive sleep apnea Children undergoing elective tonsillectomy or adenotonsillectomy at Children's Healthcare of Atlanta Egleston location Parent or legal guardian willing to participate, and able to understand and sign the provided informed consent", "candidate_expression": "((Children) AND (Children's Healthcare of Atlanta Egleston) AND (Parent or legal guardian willing to participate, and able to understand and sign the provided informed consent) AND (adenotonsillectomy) AND (obstructive sleep apnea) AND (sleep disordered breathing) AND (tonsillectomy))"}
{"candidate_id": "LLM02273", "doc_id": "NCT02893228_exc", "case_bucket": "or", "source_criterion": "Patient refusal Allergy to local anaesthesia Severe coagulopathy Contralateral phrenic nerve palsy Local infection Moderate to severe pulmonary dysfunction (GOLD II, II, IV)", "candidate_expression": "((Allergy) AND (GOLD II, II, IV) AND (Local infection Moderate severe) AND (Patient refusal) AND (coagulopathy Severe) AND (local anaesthesia) AND (phrenic nerve palsy Contralateral) AND (pulmonary dysfunction))"}
{"candidate_id": "LLM02274", "doc_id": "NCT03404804_exc", "case_bucket": "or", "source_criterion": "Children will be excluded if they have a history of developmental delay or inability to communicate the effects of an allergic reaction (non-verbal). Any contraindication to allergy testing will also result in exclusion (i.e. history of a severe allergic reaction to skin tests,, anaphylaxis in the past six weeks, pregnancy, child took any antihistamine in the past three days [including diphenhydramine (Benadryl®), cetirizine (Zyrtec®), loratadine (Claritin®), fexofenadine (Allegra®), levocetirizine (Xyzal®), and desloratadine (Clarinex®)] or child has a history of a condition that requires a beta blocker medicine for cardiac conditions, high blood pressure, migraine headaches, or eye drops for glaucoma (e.g. propranolol, metoprolol, atenolol and Timoptic®, or Betoptic® eye drops). Children who present to the PED with a rash, vomiting or current asthma symptoms including coughing, wheezing or breathing problems will also be excluded to ensure these do not mask reactions to an oral challenge. Patients being admitted to the hospital or those who are deemed too acutely ill for participation (triage level 1 or 2 or as determined by the ED patient care team) will be excluded from the study. During this pilot study, we will exclude non-English speaking families. However, in subsequent studies we will include the non-English speaking population. Children who are wards of the state, in foster care or police custody or detention will be excluded. Children with any basal condition (trauma, infection, minor accidents, etc..) will be able to participate in the study provided they and their family are willing and do not meet the above-mentioned exclusion criteria.", "candidate_expression": "((Allegra) AND (Benadryl) AND (Betoptic) AND (Children) AND (Clarinex) AND (Claritin) AND (PED) AND (Timoptic) AND (Xyzal) AND (Zyrtec) AND (allergic reaction) AND (allergy testing) AND (anaphylaxis in the past six weeks) AND (antihistamine in the past three days) AND (asthma symptoms current) AND (atenolol) AND (basal condition) AND (beta blocker medicine) AND (breathing problems) AND (cardiac conditions) AND (cetirizine) AND (contraindication) AND (coughing) AND (desloratadine) AND (detention) AND (developmental delay) AND (diphenhydramine) AND (eye drops) AND (fexofenadine) AND (foster care) AND (glaucoma) AND (high blood pressure) AND (inability to communicate the effects non-verbal) AND (infection) AND (levocetirizine) AND (loratadine) AND (metoprolol) AND (migraine headaches) AND (minor accidents) AND (non-English speaking) AND (police custody) AND (pregnancy) AND (propranolol) AND (rash) AND (severe allergic reaction history) AND (skin tests) AND (trauma) AND (vomiting) AND (wards of the state) AND (wheezing))"}
{"candidate_id": "LLM02275", "doc_id": "NCT02466113_exc", "case_bucket": "or", "source_criterion": "With severe comorbidities, such as cardiovascular disease, chronic obstructive pulmonary disease, diabetes mellitus, and chronic renal dysfunction. With bad compliance or contraindication to enrollment. Pregnant woman or lactating woman. With contraindication to receive adjuvant chemotherapy.", "candidate_expression": "((Pregnant) AND (adjuvant chemotherapy) AND (bad compliance) AND (cardiovascular disease) AND (chronic obstructive pulmonary disease) AND (chronic renal dysfunction) AND (comorbidities severe) AND (contraindication) AND (contraindication to enrollment) AND (diabetes mellitus) AND (lactating) AND (woman))"}
```
