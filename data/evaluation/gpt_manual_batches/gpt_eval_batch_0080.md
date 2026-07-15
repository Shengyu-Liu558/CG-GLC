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
{"candidate_id": "LLM01976", "doc_id": "NCT02644629_inc", "case_bucket": "other", "source_criterion": "Age 18-65 Diagnosis of MDD (Major Depressive Disorder), made or affirmed by a senior psychiatrist in Shalvata MADRS score > 20 Treated with conventional anti-depressant, administered within a formal psychiatric clinic or by a certified psychiatrist.", "candidate_expression": "((18-65) AND (> 20) AND (Age) AND (MADRS score) AND (MDD) AND (Major Depressive Disorder) AND (Treated) AND (conventional anti-depressant))"}
{"candidate_id": "LLM01977", "doc_id": "NCT01051414_inc", "case_bucket": "other", "source_criterion": "Subjects chronically infected with HCV Genotype 1 HCV RNA viral load of ≥ 10*5* IU/mL (100,000 IU/mL) at screening", "candidate_expression": "((100,000 IU/mL) AND (Genotype 1) AND (HCV) AND (HCV RNA viral load) AND (at screening) AND (chronically) AND (screening) AND (≥ 10*5* IU/mL))"}
{"candidate_id": "LLM01978", "doc_id": "NCT00609531_exc", "case_bucket": "or", "source_criterion": "Age less than 10 years or greater than 55 years, at time of consent Estimated IQ < 70 Uncontrolled epilepsy (seizure within 6 months prior to consent) 4. Presence of medical conditions that might interfere with participation, or where participation would be contraindicated History of neurological injury: head trauma, poorly-controlled seizure disorder (seizure within the preceding six months), stroke, prior neurosurgery, or under the care of a neurologist or neurosurgeon as determined by interview History of claustrophobia Implanted or irremovable metal in the body (including certain tattoos and permanent make-up) Current pregnancy (as verified by testing prior to both initial dose administration of citalopram or placebo and prior to magnetic resonance imaging) due to the risk that may be associated with SSRI treatment and magnetic resonance imaging on fetal health Medical contraindications to SSRI therapy as determined by history (including induction of mania or hypomania during SSRI therapy, or known drug allergy) Concomitant medication that would interfere with study participation Prior history of citalopram treatment failure at appropriate doses and duration Prior history of treatment failure to two previous SSRI trials at appropriate doses and duration Ongoing need for psychoactive medication other than study medication [excepting stable doses (greater than three months duration) of anticonvulsant medication for seizure disorder, or diphenhydramine (Benadryl®)for sleep]", "candidate_expression": "((< 70) AND (Age) AND (Current) AND (Estimated IQ) AND (History) AND (Prior) AND (SSRI therapy) AND (Uncontrolled epilepsy) AND (at time of consent) AND (citalopram) AND (claustrophobia) AND (consent) AND (contraindications to SSRI therapy) AND (drug allergy) AND (during SSRI therapy) AND (excepting) AND (failure) AND (greater than three months) AND (history) AND (neurological injury) AND (other than) AND (poorly-controlled) AND (pregnancy) AND (prior) AND (psychoactive medication) AND (seizure) AND (seizure disorder) AND (stable doses) AND (study medication) AND (treatment) AND (within 6 months prior to consent) AND (within the preceding six months) AND ((head trauma) OR (neurosurgery) OR (seizure disorder) OR (stroke) OR (under the care of a neurologist) OR (under the care of a neurosurgeon)) AND ((Implanted metal in the body) OR (irremovable metal in the body)) AND ((greater than 55 years) OR (less than 10 years)) AND ((hypomania) OR (mania)) AND ((anticonvulsant medication) OR (diphenhydramine)))"}
{"candidate_id": "LLM01979", "doc_id": "NCT02592980_exc", "case_bucket": "or", "source_criterion": "Patients will not be included if they have reached a stable dose of warfarin, liver dysfunction, alcoholism, use of another anticoagulant, use of chemotherapy, or if they do not meet the inclusion criteria", "candidate_expression": "((another) AND (if they do not meet the inclusion criteria) AND (stable dose) AND ((alcoholism) OR (anticoagulant) OR (chemotherapy) OR (liver dysfunction) OR (warfarin)))"}
{"candidate_id": "LLM01980", "doc_id": "NCT02678377_exc", "case_bucket": "other", "source_criterion": "History of recurrent UTI (defined as three culture proven UTIs within last 12 months) Systemic neuromuscular disease known to affect the lower urinary tract Undergoing concomitant prolapse surgery Previous incontinence surgery Treatment with anticholinergic medication in the last 2 months Previous bladder injection with onabotulinumtoxinA Prisoner Status Pregnancy", "candidate_expression": "((Pregnancy) AND (Prisoner) AND (anticholinergic medication last 2 month) AND (culture three) AND (incontinence surgery) AND (neuromuscular disease) AND (onabotulinumtoxinA bladder injection) AND (prolapse surgery) AND (recurrent UTI within last 12 months))"}
{"candidate_id": "LLM01981", "doc_id": "NCT01815580_inc", "case_bucket": "or", "source_criterion": "Adult men who have sex with men, and transgender women Unaware of HIV status at enrollment in follow-up cohort High risk for HIV infection Willing to test for HIV No prior ART, including prior administration of pre- and post-exposure prophylaxis in the last 30 days Willing to provide informed consent", "candidate_expression": "((Adult) AND (HIV infection High risk for) AND (HIV status Unaware at enrollment in follow-up cohort) AND (Unaware of HIV status) AND (informed consent Willing to provide) AND (test for HIV Willing to) AND ((ART prior) OR (administration prior in the last 30 days)) AND ((post-exposure prophylaxis) OR (pre- exposure prophylaxis)) AND ((men who have sex with men) OR (transgender women)))"}
{"candidate_id": "LLM01982", "doc_id": "NCT02034019_inc", "case_bucket": "other", "source_criterion": "Has a cataract and is expected to undergo clear corneal cataract surgery with phacoemulsification and implantation of a posterior chamber intraocular lens Has a potential post-operative pinhole corrected Snellen VA of at least 20/200 or better in both eyes", "candidate_expression": "((at least 20/200 or better) AND (both eyes) AND (cataract) AND (clear corneal cataract surgery) AND (implantation of a posterior chamber intraocular lens) AND (pinhole corrected Snellen VA) AND (with phacoemulsification))"}
{"candidate_id": "LLM01983", "doc_id": "NCT02653131_exc", "case_bucket": "other", "source_criterion": "HPN < 12 months metabolically unstable cancer as the reason for intestinal failure", "candidate_expression": "((HPN < 12 months) AND (cancer) AND (intestinal failure) AND (metabolically unstable))"}
{"candidate_id": "LLM01984", "doc_id": "NCT02348918_inc", "case_bucket": "or", "source_criterion": "Male or female, 18 years of age or older. Study eye with clinically significant diabetic macular edema (DME) with central subfield thickness ≥ 350µm on spectral domain OCT Best corrected visual acuity (BCVA) of 20/50 to 20/320 ETDRS equivalent (65 letters to 23 letters) in the study eye, with BCVA decrement primarily attributable to DME. Treatment naïve, i.e., no previous anti-VEGF treatment in the study eye or no anti-VEGF treatment in the 45 days prior to study enrollment. In the investigator's opinion, the subject still has significant intraretinal fluid with room for improvement in both macular edema and BCVA. Intra-Ocular Pressure (IOP) is under control (i.e., IOP ≤ 25 mm in the study eye) and study eye is not receiving any IOP lowering drops. Willing and able to return for all study visits. Able to meet the extensive post-op evaluation regimen. Understands and signs the informed consent form.", "candidate_expression": "((18 years or older) AND (20/50 to 20/320 ETDRS equivalent) AND (65 letters to 23 letters) AND (Able to meet the extensive post-op evaluation regimen.) AND (BCVA) AND (Best corrected visual acuity (BCVA)) AND (IOP) AND (IOP lowering drops) AND (Intra-Ocular Pressure (IOP)) AND (Male) AND (Treatment naïve) AND (Understands and signs the informed consent form.) AND (Willing and able to return for all study visits.) AND (age) AND (anti-VEGF treatment) AND (central subfield thickness) AND (clinically significant) AND (diabetic macular edema (DME)) AND (female) AND (in the 45 days prior to study enrollment) AND (in the study eye) AND (intraretinal fluid) AND (macular edema) AND (no) AND (not) AND (previous) AND (significant) AND (spectral domain OCT) AND (study enrollment) AND (study eye) AND (under control) AND (with room for improvement) AND (≤ 25 mm) AND (≥ 350µm))"}
{"candidate_id": "LLM01985", "doc_id": "NCT03228238_inc", "case_bucket": "scope", "source_criterion": "Subject must be at least 30 years of age. Subject is able to verbally confirm understandings of risks, benefits and treatment alternatives of receiving the Vitamin C+E or Statin or Dual, and he/she or his/her legally authorized representative provides written informed consent prior to any study related procedure. Subject must have symptoms that are consistent with vasospastic angina with planned Coronary angiography and Provocation test.", "candidate_expression": "((Coronary angiography) AND (Provocation test) AND (Subject is able to verbally confirm understandings of risks, benefits and treatment alternatives of receiving the Vitamin C+E or Statin or Dual, and he/she or his/her legally authorized representative provides written informed consent prior to any study related procedure) AND (age) AND (at least 30 years) AND (planned) AND (symptoms) AND (vasospastic angina))"}
{"candidate_id": "LLM01986", "doc_id": "NCT02550769_exc", "case_bucket": "other", "source_criterion": "Do not sign informed consent Pregnant patients Liver cirrhosis Undifferentiated adenocarcinoma. cT4 Metastatic disease (M1) chronic renal failure on dialysis ASA IV BMI <18 and> 35 kg / m2", "candidate_expression": "((<18 and> 35 kg / m2) AND (ASA) AND (BMI) AND (Do not sign informed consent) AND (IV) AND (Liver cirrhosis) AND (Metastatic disease (M1)) AND (Pregnant) AND (Undifferentiated) AND (adenocarcinoma) AND (cT4) AND (chronic renal failure) AND (dialysis))"}
{"candidate_id": "LLM01987", "doc_id": "NCT01907230_exc", "case_bucket": "or", "source_criterion": "HCV, HIV, or HDV coinfection. HCC or other malignancy within 3 years. Decompensated liver cirrhosis (CTP score = 7). Uremia patients under hemodialysis or continuous ambulatory peritoneal dialysis or patients with Ccr < 50 mL/min Pregnant or breastfeeding women. Women of child-bearing potential (WOCBP) who are unwilling or unable to use an acceptable method of contraception to avoid pregnancy throughout the study and for up to 4 weeks after the last dose of study drug.", "candidate_expression": "((CTP score = 7) AND (Ccr < 50 mL/min) AND (Decompensated liver cirrhosis) AND (HCC) AND (HCV coinfection) AND (HDV coinfection) AND (Pregnant or breastfeeding women) AND (Uremia) AND (Women of child-bearing potential (WOCBP) who are unwilling or unable to use an acceptable method of contraception to avoid pregnancy throughout the study and for up to 4 weeks after the last dose of study drug) AND (coinfection HIV) AND (continuous ambulatory peritoneal dialysis) AND (hemodialysis) AND (malignancy))"}
{"candidate_id": "LLM01988", "doc_id": "NCT02966236_exc", "case_bucket": "or", "source_criterion": "Coronary artery disease - stent Severe chronic renal failure Congenital or acquired thrombophilia/thrombosis event Known or suspected allergy", "candidate_expression": "((Coronary artery disease) AND (allergy) AND (renal failure Severe chronic Congenital acquired) AND (stent) AND (thrombophilia) AND (thrombosis event Known suspected))"}
{"candidate_id": "LLM01989", "doc_id": "NCT02478346_inc", "case_bucket": "or", "source_criterion": "Adult patients (age = 18) Diagnosed by preoperative imaging modalities to have a brain tumor (including metastatic brain tumors) or vascular lesions (aneurysm, arteriovenous malformation or arteriovenous fistula) requiring surgical intervention. The patient is determined by a board certified neurosurgeon to have a tumor or vascular lesion that would take up fluorescein Patient or legally authorized representative provides written informed consent to enroll in this study", "candidate_expression": "((Adult) AND (Patient or legally authorized representative provides written informed consent to enroll in this study) AND (age = 18) AND (aneurysm) AND (arteriovenous fistula) AND (arteriovenous malformation) AND (brain tumor) AND (fluorescein) AND (imaging modalities preoperative) AND (metastatic brain tumors) AND (surgical intervention) AND (vascular lesions) AND ((tumor) OR (vascular lesion)))"}
{"candidate_id": "LLM01990", "doc_id": "NCT02481518_inc", "case_bucket": "or", "source_criterion": "Age > 18 years Eastern Cooperative Oncology Group score 0-2 First Diagnosed Head and neck cancer and plan for treatment with cisplatin Serum creatinine =1.5 mg/dl or eGFR=60(ml/min/1.73 m2)", "candidate_expression": "((=1.5 mg/dl) AND (=60(ml/min/1.73 m2)) AND (> 18 years) AND (Age) AND (Eastern Cooperative Oncology Group) AND (Head and neck cancer) AND (cisplatin) AND (plan) AND (score 0-2) AND ((Serum creatinine) OR (eGFR)))"}
{"candidate_id": "LLM01991", "doc_id": "NCT02952365_inc", "case_bucket": "other", "source_criterion": "Subjects age 21 and older Subjects with healthy eyes Subjects who have previously undergone LASIK surgery Subjects with residual refractive error.", "candidate_expression": "((LASIK surgery previously) AND (age 21 and older) AND (healthy eyes) AND (residual refractive error))"}
{"candidate_id": "LLM01992", "doc_id": "NCT02632266_inc", "case_bucket": "or", "source_criterion": "Inborn preterm infants born between 28 0/7 and 34 0/7 weeks gestation and fed either mother's own milk or donor human milk", "candidate_expression": "((Inborn) AND (between 28 0/7 and 34 0/7 weeks) AND (gestation) AND (infants) AND (preterm) AND ((donor human milk fed) OR (fed mother's own milk)))"}
{"candidate_id": "LLM01993", "doc_id": "NCT02871206_exc", "case_bucket": "or", "source_criterion": "Anaphylactic reaction to a previous dose of influenza vaccine or to any of its components Known Immunoglobulin E (IgE)-mediated hypersensitivity to eggs manifested as hives, swelling of the mouth and throat, difficulty in breathing, hypotension, or shock Guillain- Barré syndrome within eight weeks of a previous influenza vaccine Use of aspirin or salicylate- containing products within 30 days before enrollment Household members of children in Group A", "candidate_expression": "((Anaphylactic reaction) AND (Group A) AND (Guillain- Barré syndrome within eight weeks of a previous influenza vaccine) AND (Household members) AND (Immunoglobulin E (IgE)-mediated hypersensitivity) AND (aspirin) AND (children) AND (difficulty in breathing) AND (eggs) AND (hives) AND (hypotension) AND (influenza vaccine) AND (influenza vaccine previous) AND (its components) AND (salicylate- containing products) AND (shock) AND (swelling of the mouth) AND (swelling of the throat))"}
{"candidate_id": "LLM01994", "doc_id": "NCT02650024_inc", "case_bucket": "or", "source_criterion": "Adult (= 18 years old) subjects with chronic genotype 1 HCV and NCI with a GDS greater than or equal to 0.5 (n=60). Presence of chronic HCV infection based on chart review will be defined as positive for anti-HCV antibody or HCV RNA at least 6 months before screening. For the HIV/HCV co-infected group only, subjects must have HIV. HIV status will be obtained through self report. Self report will be confirmed at screening using a HIV-1 point of care test. In the event that point of care test and self-report are discordant, then HIV status will be confirmed by a licensed Western blot or a second antibody test. HIV/HCV co-infected subjects (n=12) must also have a HIV RNA measurement <50 copies/mL at the pre-treatment visit. Platelets >150,000 Aspartate aminotransferase (AST)/Alanine aminotransferase (ALT) <10x upper limit of normal Creatinine clearance >30 milliliters/minute/1.73 centimeter squared", "candidate_expression": "((Adult) AND (Alanine aminotransferase (ALT) <10x upper limit of normal) AND (Aspartate aminotransferase (AST) <10x upper limit of normal) AND (Creatinine clearance >30 milliliters/minute/1.73 centimeter squared) AND (GDS greater than or equal to 0.5) AND (HCV) AND (HCV infection chronic) AND (HIV) AND (HIV RNA measurement <50 copies/mL at the pre-treatment visit) AND (Platelets >150,000) AND (co-infected) AND (old = 18 years old) AND ((HCV RNA) OR (anti-HCV antibody)) AND ((HCV) OR (NCI)))"}
{"candidate_id": "LLM01995", "doc_id": "NCT02208739_inc", "case_bucket": "or", "source_criterion": "Patients should have at least 12 teeth present Patients with Moderate to Advanced Chronic periodontitis Patients with 2 or more interproximal sites (not on same tooth) with probing pocket depths of 5mm or more and 2 or more interproximal sites (not on same tooth)of probing attachment loss of 4mm or more which bled on probing.", "candidate_expression": "((Chronic periodontitis) AND (interproximal sites of probing attachment loss of 4mm or more 2 or more bled on probing 4mm or more) AND (interproximal sites with probing pocket depths of 5mm or more 2 or more 5mm or more) AND (probing) AND (teeth present at least 12) AND ((Advanced) OR (Moderate)))"}
{"candidate_id": "LLM01996", "doc_id": "NCT03147599_inc", "case_bucket": "other", "source_criterion": "Men 18 years or older ONB within 1 year post-surgery.", "candidate_expression": "((18 years or older) AND (Men) AND (ONB) AND (surgery) AND (within 1 year post-surgery))"}
{"candidate_id": "LLM01997", "doc_id": "NCT01803828_inc", "case_bucket": "or", "source_criterion": "age 35-75 years; Diagnosis of Type 2 Diabetes from at least 3 years; HbA1c < 10%; normal blood pressure or controlled hypertension; BMI < 40;", "candidate_expression": "((35-75 years) AND (< 10%) AND (< 40) AND (BMI) AND (HbA1c) AND (Type 2 Diabetes) AND (age) AND (at least 3 years) AND (controlled hypertension) AND (normal blood pressure))"}
{"candidate_id": "LLM01998", "doc_id": "NCT02689817_exc", "case_bucket": "or", "source_criterion": "Existing sacral pressure ulcer, undergoing a cardiac procedure, or inability to provide informed consent.", "candidate_expression": "((cardiac procedure) AND (inability to provide informed consent) AND (sacral pressure ulcer))"}
{"candidate_id": "LLM01999", "doc_id": "NCT00502567_exc", "case_bucket": "other", "source_criterion": "Inadequate bone marrow reserve history of poorly controlled hypertension", "candidate_expression": "((Inadequate bone marrow reserve) AND (history) AND (poorly controlled hypertension))"}
{"candidate_id": "LLM02000", "doc_id": "NCT01088750_exc", "case_bucket": "other", "source_criterion": "NA", "candidate_expression": "(EMPTY)"}
```
