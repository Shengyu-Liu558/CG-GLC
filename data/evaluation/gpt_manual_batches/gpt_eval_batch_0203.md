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
{"candidate_id": "LLM05051", "doc_id": "NCT03518034_inc", "case_bucket": "or", "source_criterion": "Men between 45 and 80 years age Participants with low serum testosterone concentrations (< 300 ng/dL) who exhibit at least one sign or symptom of hypogonadism and have evidence of cardiovascular (CV) disease or are at an increased risk for CV disease.", "candidate_expression": "((< 300 ng/dL) AND (Men) AND (age) AND (at least one) AND (between 45 and 80 years) AND (evidence of) AND (hypogonadism) AND (increased risk) AND (low) AND (serum testosterone concentrations) AND ((CV disease) OR (cardiovascular (CV) disease)) AND ((sign) OR (symptom)))"}
{"candidate_id": "LLM05052", "doc_id": "NCT01177891_exc", "case_bucket": "or", "source_criterion": "Blood donation of more than 450ml in the previous three months. Subject with an abnormal karyotype in favor of Turner syndrome or having a premutation of the FMR1 gene or a syndromic form Subject exclusion period in another study without direct individual benefit Subject refusing to sign the consent form", "candidate_expression": "((Blood donation of more than 450ml in the previous three months) AND (Subject exclusion period in another study without direct individual benefit) AND (Subject refusing to sign the consent form) AND (Turner syndrome) AND ((abnormal karyotype) OR (premutation of the FMR1 gene) OR (syndromic form)))"}
{"candidate_id": "LLM05053", "doc_id": "NCT01770340_inc", "case_bucket": "or", "source_criterion": "Localized intermediate-risk or high-risk prostate cancer cT3 Gleason score = 7 (3+4 and/or 4+3) and/or PSA = 20 ng/ml intact preoperative erectile function with an IIEF = 21 (IIEF-6).", "candidate_expression": "((3+4) AND (4+3) AND (= 20 ng/ml) AND (= 21) AND (= 7) AND (Gleason score) AND (IIEF) AND (IIEF-6) AND (PSA) AND (cT3) AND (high-risk) AND (intact erectile function) AND (intermediate-risk) AND (preoperative) AND (prostate cancer))"}
{"candidate_id": "LLM05054", "doc_id": "NCT02904785_inc", "case_bucket": "or", "source_criterion": "Clinical and radiologic diagnosis of primary knee osteoarthritis (Kellgren & Lawrence I, II or III); Capability to understand the Informed Consent Form; Chronic pain for at least 3 months prior to inclusion, measured by VAS. (VAS 4 or above); Absence of skin injures, infections or tumor in the target knee; Availability to comply with the visits.", "candidate_expression": "((Availability to comply with the visits) AND (Capability to understand the Informed Consent Form;) AND (Chronic pain at least 3 months prior measured by VAS) AND (Kellgren & Lawrence I, II or III) AND (VAS) AND (VAS 4 or above) AND (infections target knee) AND (primary knee osteoarthritis Clinical diagnosis radiologic diagnosis) AND (tumor target knee) AND NOT (skin injures))"}
{"candidate_id": "LLM05055", "doc_id": "NCT02863120_inc", "case_bucket": "or", "source_criterion": "Male or non-pregnant female between the ages of 18-65 Patients willing and able to sign the informed consent Patients able to comply with follow-up requirements including self-evaluations Patients requiring a primary total knee replacement Patients with a diagnosis of osteoarthritis, traumatic arthritis, or avascular necrosis", "candidate_expression": "((18-65) AND (Male) AND (Patients willing and able to sign the informed consent) AND (ages) AND (atients able to comply with follow-up requirements including self-evaluations) AND (avascular necrosis) AND (female) AND (non) AND (osteoarthritis) AND (pregnant) AND (primary total knee replacement) AND (traumatic arthritis))"}
{"candidate_id": "LLM05056", "doc_id": "NCT02627521_inc", "case_bucket": "other", "source_criterion": "Accepted for CABG surgery Treatment with Ticagrelor within 48 hours", "candidate_expression": "((CABG surgery Accepted for) AND (Ticagrelor) AND (Treatment within 48 hours))"}
{"candidate_id": "LLM05057", "doc_id": "NCT02884115_inc", "case_bucket": "other", "source_criterion": "Early Syphilis Cases Determined to Be Serofast at 6 Months after Initial Treatment", "candidate_expression": "((6 Months after Initial Treatment) AND (Early Syphilis) AND (Initial) AND (Initial Treatment) AND (Serofast) AND (Treatment))"}
{"candidate_id": "LLM05058", "doc_id": "NCT02584140_exc", "case_bucket": "or", "source_criterion": "Pregnancy at enrollment. Any condition, which in the opinion of the provider, will seriously compromise the participant's ability to comply with the protocol, including adherence to PrEP medication dosing, such as active, untreated or unstable major mental illness (i.e. untreated psychotic disorder). Use of prohibited medications, in particular, agents known to be nephrotoxic or drugs slow in renal excretion. Previous participation in an HIV vaccine trial. Participants that were documented to have received only placebo are not excluded. Signs or symptoms suspicious for Primary HIV Infection (PHI).", "candidate_expression": "((Any condition, which in the opinion of the provider, will seriously compromise the participant's ability to comply with the protocol, including adherence to PrEP medication dosing, such as active, untreated or unstable major mental illness (i.e. untreated psychotic disorder)) AND (PHI) AND (Participants Previous HIV vaccine trial not) AND (Pregnancy at enrollment) AND (Primary HIV Infection) AND (participation Previous HIV vaccine trial) AND (placebo) AND ((Signs) OR (symptoms)) AND ((agents nephrotoxic) OR (drugs slow in renal excretion)))"}
{"candidate_id": "LLM05059", "doc_id": "NCT03347513_inc", "case_bucket": "other", "source_criterion": "Diagnosed Iron deficiency anemia. H-pylori positive cases. Second trimester pregnancy.", "candidate_expression": "((H-pylori positive Second trimester) AND (Iron deficiency anemia) AND (pregnancy Second trimester))"}
{"candidate_id": "LLM05060", "doc_id": "NCT03461679_inc", "case_bucket": "other", "source_criterion": "Patients undergoing total knee arthroplasty under spinal anaesthesia 45y or older ASA 1-3 BMI 18-35", "candidate_expression": "((ASA 1-3) AND (BMI 18-35) AND (spinal anaesthesia) AND (total knee arthroplasty) AND (y 45 or older))"}
{"candidate_id": "LLM05061", "doc_id": "NCT02299063_inc", "case_bucket": "other", "source_criterion": "aged between 3 - 36 months having primary corrective heart surgery", "candidate_expression": "((aged) AND (between 3 - 36 months) AND (corrective heart surgery) AND (primary))"}
{"candidate_id": "LLM05062", "doc_id": "NCT03318393_exc", "case_bucket": "or", "source_criterion": "Patients with known or suspected heparin induced thrombocytopenia prior to consent Patients with hepatic failure defined as coagulopathy with elevated transaminases more than three times normal values Patients with plan to decannulate from ECMO within 48 hours Known or suspected pregnant women Previous enrollment in this study Primary language spoken that is not English or Spanish", "candidate_expression": "((Previous enrollment in this study) AND (coagulopathy) AND (decannulate from ECMO within 48 hours) AND (heparin) AND (hepatic failure) AND (pregnant) AND (thrombocytopenia heparin induced prior to consent) AND (transaminases elevated more than three times normal values) AND (women) AND ((Known) OR (suspected)) AND ((known) OR (suspected)))"}
{"candidate_id": "LLM05063", "doc_id": "NCT01446094_exc", "case_bucket": "other", "source_criterion": "Inability to give informed consent Possible pregnancy (confirmed by urine test) Women who are breastfeeding Severe claustrophobia Inability to lie flat for 20-30 minutes (the anticipated amount of time to complete the MRI procedure) Individuals with cochlear implants Individuals with non-MRI compatible aneurysm clips Potential contraindications to regadenoson use due to: Contraindication to administration of Gadolinium (Gd) based contrast agents (GBCA):", "candidate_expression": "((Contraindication) AND (Gadolinium (Gd) based contrast agents (GBCA)) AND (Inability to give informed consent) AND (Inability to lie flat 20-30 minutes amount of time to complete the MRI procedure) AND (Women) AND (aneurysm clips MRI compatible) AND (breastfeeding) AND (claustrophobia Severe) AND (cochlear implants) AND (pregnancy Possible) AND (urine test confirmed))"}
{"candidate_id": "LLM05064", "doc_id": "NCT02015494_inc", "case_bucket": "other", "source_criterion": "Males and females aged 18-40 years of age at the time of vaccination in good health as determined by medical history, physical exam, laboratory assessments and the clinical judgment of the Principal Investigator Able to provide informed consent indicating that they understand the purpose of this study and are willing to adhere to the procedures described in this protocol If the subject is a female of childbearing potential, she must use adequate contraceptive precautions (e.g., intrauterine contraceptive device, oral contraceptives or other equivalent hormonal contraception) for 2 months prior to vaccination and continue to use such precautions for a minimum of three months after vaccination. She must also have a negative urine pregnancy test within 24 hours prior to receiving study vaccine. Women at least one year post-menopausal or surgically sterile will not be considered of childbearing potential. Willing to receive the unlicensed vaccine given as an IM injection Willing to provide multiple blood specimens collected by venipuncture", "candidate_expression": "((18-40 years) AND (IM injection) AND (If the subject is a female of childbearing potential, she must use adequate contraceptive precautions (e.g., intrauterine contraceptive device, oral contraceptives or other equivalent hormonal contraception) for 2 months prior to vaccination and continue to use such precautions for a minimum of three months after vaccination. She must also have a negative urine pregnancy test within 24 hours prior to receiving study vaccine. Women at least one year post-menopausal or surgically sterile will not be considered of childbearing potential.) AND (Males) AND (age) AND (aged) AND (at the time of vaccination) AND (females) AND (good health) AND (laboratory assessments) AND (medical history) AND (physical exam) AND (the clinical judgment of the Principal Investigator) AND (time of vaccination) AND (vaccine))"}
{"candidate_id": "LLM05065", "doc_id": "NCT01631058_exc", "case_bucket": "or", "source_criterion": "Allergy to any of proposed medications Patients with any active infection including HBV, HCV and HIV.", "candidate_expression": "((Allergy) AND (active infection) AND (proposed medications) AND ((HBV) OR (HCV) OR (HIV)))"}
{"candidate_id": "LLM05066", "doc_id": "NCT02243553_exc", "case_bucket": "or", "source_criterion": "1. History or presence of allergy to the study drugs or their components or drugs of their class, or a history of drug or other allergy that, in the opinion of the physician responsible, contraindicates their participation 2. Any finding of the medical examination (including blood pressure, pulse rate and electrocardiogram) deviating from normal and of clinical relevance 3. History or diagnosis of any significant medical conditions: Including but not limited to gastrointestinal, hepatic, renal, respiratory, cardiovascular, metabolic, immunologic, hematological, psychiatric, neurological, oncological or hormonal disorders 4. Known elevated liver enzymes in past clinical trials with any compound (experimental or marketed) 5. Clinically relevant laboratory abnormalities (e.g. Hgb<11g/dL, Hct<30g/dL, total cholesterol >240mg/dL, triglycerides >500mg/dL, fasting glucose >130mg/dL, liver function tests >2.5x upper limit of normal, baseline international normalized ratio >1.2) 6. History of evidence of clinically significant hepatic, cardiac, pulmonary, endocrine, immunological, gastrointestinal, hematological, vascular or collagen disease 7. History of alcohol abuse or use of any illicit drugs 8. Unable to abstain from more than one beer or alcohol equivalent per day for the duration of the study 9. Use of tobacco products and/or history of smoking within the past 2 months 10. Pregnant or breast feeding 11. Sexually active women of childbearing age who do not use an acceptable barrier method of birth control 12. Hypersensitivity to caffeine, warfarin, vitamin K, omeprazole, dextromethorphan, midazolam, tipranavir, ritonavir or their excipients 13. Concomitant treatment with other experimental compounds 14. Concomitant administration of any prescription or over the counter medications known to alter P450 enzyme or P-gp activity 15. Concomitant administration of any prescription or over the counter medications known to be highly dependent on P450 or P-gp for clearance for which elevated plasma concentrations are known to be associated with serious toxicity 16. Concomitant administration of any food product known to alter P450 enzyme or P-gp activity such as grapefruit juice, Seville oranges 17. Concomitant administration of any drug that could affect bleeding (e.g., aspirin, clopidogrel, ticlopidine, warfarin, heparin, low-molecular weight heparin) 18. Concomitant administration of oral contraceptives (may be included with 7-day washout period) 19. Concomitant administration of any herbal medications 20. Inadequate venous access 21. Renal or hepatic insufficiency 22. Clinically unacceptable result at the screening physical examination 23. Use of investigational medications within 30 days before study entry 24. HIV-positive 25. Body Mass Index (BMI) > 30 kg/m²", "candidate_expression": "((<11g/dL) AND (<30g/dL) AND (> 30 kg/m²) AND (>1.2) AND (>130mg/dL) AND (>2.5x upper limit of normal) AND (>240mg/dL) AND (>500mg/dL) AND (Any finding of the medical examination (including blood pressure, pulse rate and electrocardiogram) deviating from normal and of clinical relevance) AND (Body Mass Index (BMI)) AND (Clinically relevant) AND (Clinically unacceptable) AND (Clinically unacceptable result) AND (Concomitant) AND (HIV) AND (History) AND (History or presence of allergy to the study drugs or their components or drugs of their class, or a history of drug or other allergy that, in the opinion of the physician responsible, contraindicates their participation) AND (Hypersensitivity) AND (Inadequate) AND (Sexually active) AND (acceptable) AND (age) AND (allergy) AND (at the screening physical examination) AND (barrier method of birth control) AND (baseline) AND (childbearing) AND (clinically significant) AND (drug that could affect bleeding) AND (elevated) AND (experimental compounds) AND (herbal medications) AND (history) AND (investigational medications) AND (laboratory abnormalities) AND (liver enzymes) AND (medical conditions) AND (not) AND (oral contraceptives) AND (physical examination) AND (plasma concentrations) AND (positive) AND (serious) AND (significant) AND (study drugs) AND (study entry) AND (the screening physical examination) AND (toxicity) AND (venous access) AND (within 30 days before study entry) AND (within the past 2 months) AND (women) AND ((Pregnant) OR (breast feeding)) AND ((smoking) OR (tobacco products)) AND ((alcohol abuse) OR (use of illicit drugs)) AND ((cardiac disease) OR (collagen disease) OR (endocrine disease) OR (gastrointestinal disease) OR (hematological disease) OR (hepatic disease) OR (immunological disease) OR (pulmonary disease) OR (vascular disease)) AND ((Hct) OR (Hgb) OR (fasting glucose) OR (international normalized ratio) OR (liver function tests) OR (total cholesterol) OR (triglycerides)) AND ((cardiovascular disorders) OR (gastrointestinal disorders) OR (hematological disorders) OR (hepatic disorders) OR (hormonal disorders) OR (immunologic disorders) OR (metabolic disorders) OR (neurological disorders) OR (oncological disorders) OR (psychiatric disorders) OR (renal disorders) OR (respiratory disorders)) AND ((Renal insufficiency) OR (hepatic insufficiency)) AND ((aspirin) OR (clopidogrel) OR (heparin) OR (low-molecular weight heparin) OR (ticlopidine) OR (warfarin)) AND ((food product known to alter P-gp activity) OR (food product known to alter P450 enzyme activity)) AND ((Seville oranges) OR (grapefruit juice)) AND ((medications known to be highly dependent on P-gp for clearance) OR (medications known to be highly dependent on P450 for clearance)) AND ((medications known to alter P-gp activity) OR (medications known to alter P450 enzyme activity)) AND ((caffeine) OR (dextromethorphan) OR (midazolam) OR (omeprazole) OR (ritonavir) OR (tipranavir) OR (vitamin K) OR (warfarin)))"}
{"candidate_id": "LLM05067", "doc_id": "NCT02934269_inc", "case_bucket": "or", "source_criterion": "Healthy male and/or female subjects between the ages of 18 and 55 years, and a body mass index (BMI) of ≥ 18 and ≤ 33 kg/m2 with body weight ≥ 50 and ≤ 90 kg at screening. Females must have been surgically sterilized (hysterectomy, bilateral oophorectomy, or bilateral salpingo-oophorectomy; proper documentation required) at least 6 months before screening, or be postmenopausal (defined as 24 consecutive months without menses before screening, with a follicle-stimulating hormone [FSH] level of > 40 IU/L at screening).", "candidate_expression": "((Females) AND (Healthy) AND (ages between 18 and 55 years) AND (bilateral oophorectomy) AND (bilateral salpingo-oophorectomy) AND (body mass index (BMI) ≥ 18 and ≤ 33 kg/m2) AND (body weight ≥ 50 and ≤ 90 kg) AND (female) AND (follicle-stimulating hormone [FSH] > 40 IU/L at screening) AND (hysterectomy) AND (male) AND (postmenopausal) AND (surgically sterilized at least 6 months before) AND NOT (menses 24 consecutive months before screening))"}
{"candidate_id": "LLM05068", "doc_id": "NCT02464813_inc", "case_bucket": "or", "source_criterion": "Adolescent (10-21 years) undergoing spinal fusion for idiopathic scoliosis, spondylolisthesis or Scheuermann kyphosis. Posterior spinal fusion No contraindication for Pregabalin use ASA I-III Written informed consent", "candidate_expression": "((10-21 years) AND (ASA) AND (Adolescent) AND (I-III) AND (No) AND (Posterior spinal fusion) AND (Pregabalin) AND (Written informed consent) AND (contraindication) AND (spinal fusion) AND (years) AND ((Scheuermann kyphosis) OR (idiopathic scoliosis) OR (spondylolisthesis)))"}
{"candidate_id": "LLM05069", "doc_id": "NCT02432404_inc", "case_bucket": "or", "source_criterion": "=18-40 year old women BV+ by Amsel criteria and Nugent score OR history of BV in the prior 6 months Willing to use the NuvaRing as directed Not intending or wishing to become pregnant over the course of the study Capable of providing written informed consent", "candidate_expression": "((18-40 year) AND (Amsel criteria) AND (BV) AND (BV+) AND (Not intending or wishing to become pregnant over the course of the study) AND (Nugent score) AND (NuvaRing) AND (Willing to use) AND (in the prior 6 months) AND (old) AND (women) AND ((Capable of providing written informed consent) OR (written informed consent)))"}
{"candidate_id": "LLM05070", "doc_id": "NCT02765035_inc", "case_bucket": "other", "source_criterion": "Person is >18 years old. Person is a unilateral transfemoral or knee-disarticulation amputee with stabilized residual limb. Person is a K2, K3 or K4 ambulator based on Medicare Functional Classification Level (MFCL). Person is currently fitted with a prosthesis using a non-microprocessor controlled prosthetic knee for at least 6 months. Person was never fitted with microprocessor controlled prosthetic knee joint. Person is willing and able to independently provide informed consent. Person is willing to comply with study procedures. Person wears prosthesis daily and = 8 hours/day. Person is walking on average 1km/day. Person is walking not slower than 3km/h (~0.8m/s) (based on 10m walk test conducted during recruiting). Person is walking on level ground in a step over step manner.", "candidate_expression": "((MFCL) AND (Medicare Functional Classification Level K2, K3 or K4) AND (Person is willing and able to independently provide informed consent) AND (Person is willing to comply with study procedures) AND (old >18 years) AND (prosthesis) AND (prosthesis daily and = 8 hours/day) AND (prosthetic knee non-microprocessor controlled at least 6 months) AND (walking) AND (walking 1km/day) AND (walking not slower than 3km/h) AND NOT (prosthetic knee joint microprocessor controlled))"}
{"candidate_id": "LLM05071", "doc_id": "NCT03335436_inc", "case_bucket": "other", "source_criterion": "singleton, term pregnancy currently on buprenorphine maintenance therapy scheduled for elective CD under spinal anesthesia", "candidate_expression": "((CD scheduled for elective) AND (buprenorphine) AND (buprenorphine maintenance therapy currently) AND (pregnancy singleton term) AND (spinal anesthesia))"}
{"candidate_id": "LLM05072", "doc_id": "NCT02777580_exc", "case_bucket": "or", "source_criterion": "1. Expected performance of PCI < 60 minutes from diagnosis (qualifying ECG) or inability to arrive at the catheterisation laboratory within 3 hours Previous CABG Left bundle branch block or ventricular pacing Patients with cardiogenic shock - Killip Class 4 Patients with a body weight < 55 kg (known or estimated) Uncontrolled hypertension, defined as sustained blood pressure = 180/110 mm Hg (systolic BP = 180 mm Hg and/or diastolic BP = 110 mm Hg) prior to randomisation Known prior stroke or TIA Recent administration of any i.v. or s.c. anticoagulation within 12 hours, including unfractionated heparin, enoxaparin, and/or bivalirudin or current use of oral anticoagulation (i.e. warfarin or a NOACs) Active bleeding or known bleeding disorder/diathesis Known history of central nervous system damage (i.e. neoplasm, aneurysm, intracranial or spinal surgery) or recent trauma to the head or cranium (i.e. < 3 months) Major surgery, biopsy of a parenchymal organ, or significant trauma within the past 2 months (this includes any trauma associated with the current myocardial infarction) Clinical diagnosis associated with increased risk of bleeding including known active peptic ulceration and/or neoplasm with increased bleeding risk Prolonged cardiopulmonary resuscitation (> 2 minutes) within the past 2 weeks Known acute pericarditis and/or subacute bacterial endocarditis Known acute pancreatitis or known severe hepatic dysfunction, including hepatic failure, cirrhosis, portal hypertension (oesophageal varices) and active hepatitis Dementia Known severe renal insufficiency Previous enrolment in this study or treatment with an investigational drug or device under another study protocol in the past 7 days Known allergic reactions to tenecteplase, clopidogrel, enoxaparin and aspirin Inability to follow the protocol and comply with follow-up requirements or any other reason that the investigator feels would place the patient at increased risk if the investigational therapy is initiated.", "candidate_expression": "((CABG) AND (Dementia) AND (Inability to follow the protocol and comply with follow-up requirements or any other reason that the investigator feels would place the patient at increased risk if the investigational therapy is initiated) AND (Killip Class 4) AND (PCI < 60 minutes from diagnosis) AND (Previous enrolment in this study or treatment with an investigational drug or device under another study protocol in the past 7 days) AND (allergic reactions) AND (anticoagulation within 12 hours) AND (blood pressure = 180/110 mm Hg) AND (body weight < 55 kg) AND (cardiogenic shock) AND (cardiopulmonary resuscitation Prolonged past 2 weeks) AND (central nervous system damage) AND (hypertension Uncontrolled) AND (myocardial infarction) AND (oesophageal varices) AND (renal insufficiency severe) AND (risk of bleeding increased) AND (trauma < 3 months) AND ((diastolic BP = 110 mm Hg) OR (systolic BP = 180 mm Hg)) AND ((TIA) OR (stroke)) AND ((bivalirudin) OR (enoxaparin) OR (oral anticoagulation) OR (unfractionated heparin)) AND ((NOACs) OR (warfarin)) AND ((Active bleeding) OR (bleeding disorder) OR (diathesis)) AND ((aneurysm) OR (intracranial surgery) OR (neoplasm) OR (spinal surgery)) AND ((cranium) OR (head)) AND ((Major surgery) OR (biopsy parenchymal organ) OR (trauma significant)) AND ((Left bundle branch block) OR (ventricular pacing)) AND ((neoplasm) OR (peptic ulceration active)) AND ((acute pericarditis) OR (subacute bacterial endocarditis)) AND ((acute pancreatitis) OR (hepatic dysfunction severe)) AND ((active hepatitis) OR (cirrhosis) OR (hepatic failure) OR (portal hypertension)) AND ((aspirin) OR (clopidogrel) OR (enoxaparin) OR (tenecteplase)))"}
{"candidate_id": "LLM05073", "doc_id": "NCT02951754_exc", "case_bucket": "or", "source_criterion": "Contraindication for IR-MPH use Current stimulant treatment Evidence of a clinically significant neurological disease that might affect cognition (e.g., delirium, dementia, epilepsy, head trauma, and multiple sclerosis) Current or past history of psychosis Estimated intelligence quotient score lower than 70", "candidate_expression": "((Contraindication) AND (Estimated intelligence quotient score lower than 70) AND (IR-MPH) AND (delirium) AND (dementia) AND (epilepsy) AND (head trauma) AND (multiple sclerosis Current past) AND (neurological disease clinically significant might affect cognition) AND (psychosis history) AND (stimulant treatment Current))"}
{"candidate_id": "LLM05074", "doc_id": "NCT00994786_exc", "case_bucket": "or", "source_criterion": "Patients with any other primary DSM-IV psychiatric diagnosis in addition to Obsessive Compulsive Disorder. Patients who currently fulfil criteria for DSM-IV eating disorder, body dysmorphic disorder, current alcohol or substance abuse, or who have a lifetime history of bipolar disorder. Patients with a history of Schizophrenia and other psychotic disorders, Delirium, Dementia, and Amnestic and other cognitive disorders. Subjects with a concurrent Axis II Cluster A Personality Disorder Borderline or Antisocial Personality Disorder. Subjects who based on history or mental status examination have a significant risk of committing suicide, in the investigator's opinion. Subjects with a history of more than three adequate trials with an SSRI. Subjects who have had an adequate trial of pregabalin. Subjects who have initiated psychotherapy in the last 4 months prior to the first visit. Subjects who, during the course of the study, would be likely to require treatment with prohibited concomitant therapy . Prior use of or a known allergy or hypersensitivity to pregabalin. Subjects who have participated in any clinical trial within 30 days prior to entering the study, or in a clinical trial involving a psychotropic medication within the 6 months prior to entering the study. Any subject who has been taking benzodiazepines before entering the study who: 1) cannot tolerate being free of benzodiazepines for 4 weeks, or 2) has signs or symptoms of benzodiazepine withdrawal or rebound at the end of those 4 weeks. Should a patient entering the study, who is currently on benzodiazepines develop discontinuation symptoms with discontinuation of their benzodiazepine, we will treat these symptoms with a more gradual benzodiazepine taper. Study will be delayed until the patient is able to tolerate the discontinuation for 4 weeks. Patients with a current seizure disorder, organic brain disorder or a history of seizure disorders (except for febrile seizures in childhood). Patients with thyroid pathology, the treatment of which has not been stabilized for at least three months. Patients on neuroleptic drugs in the two months prior to study entry or cognitive behavioural therapy specific to OCD within four weeks of study entry Pregnant or lactating females, or if sexually active and of childbearing potential, not using adequate methods of birth control. Patients with a history or evidence of a medical condition that would expose them to an increased risk of a significant adverse event or interfere with assessments of safety and efficacy during the trial. Patients receiving psychotropics of any kind, including betablockers and other anticonvulsants. Sleep medication such as oral chloral-hydrate or zopiclone are acceptable. Patients using any herbal psychoactive treatments, e.g. St John's Wort, Valerian, Kava Kava, L-tryptophan. Patients with any condition or on any therapy that, in the investigator's opinion, or as indicated in the pregabalin product label, may pose a risk to the subject. Patients who have had a major life event in the past three months, which in the judgement of the investigator is influencing their current condition. Patients having clinically significant abnormal laboratory, or ECG findings not resolved by further examinations.", "candidate_expression": "((Amnestic) AND (Antisocial Personality Disorder) AND (Axis II Cluster A) AND (Borderline Personality Disorder) AND (DSM-IV) AND (Delirium) AND (Dementia) AND (ECG findings) AND (Kava Kava) AND (L-tryptophan) AND (OCD) AND (Obsessive Compulsive Disorder) AND (Personality Disorder) AND (Pregnant or lactating females, or if sexually active and of childbearing potential, not using adequate methods of birth control) AND (Schizophrenia) AND (Sleep medication) AND (St John's Wort) AND (Subjects who have had an adequate trial of pregabalin) AND (Subjects who have participated in any clinical trial within 30 days prior to entering the study, or in a clinical trial involving a psychotropic medication within the 6 months prior to entering the study.) AND (Subjects with a history of more than three adequate trials with an SSRI) AND (Valerian) AND (acceptable) AND (alcohol abuse) AND (allergy) AND (anticonvulsants) AND (any other) AND (at least three months) AND (betablockers) AND (bipolar disorder) AND (body dysmorphic disorder) AND (childhood) AND (chloral-hydrate) AND (cognitive behavioural therapy) AND (cognitive disorders) AND (eating disorder) AND (except) AND (febrile seizures) AND (first visit) AND (herbal psychoactive treatments) AND (history of seizure disorders) AND (hypersensitivity) AND (in addition to) AND (in the last 4 months prior to the first visit) AND (in the two months prior to study entry) AND (laboratory findings) AND (mental status examination) AND (neuroleptic drugs) AND (not) AND (oral) AND (organic brain disorder) AND (other) AND (pregabalin) AND (primary) AND (psychiatric diagnosis) AND (psychotherapy) AND (psychotic disorders) AND (psychotropics) AND (risk of committing suicide) AND (seizure disorder) AND (significant) AND (significant abnormal) AND (stabilized) AND (study entry) AND (substance abuse) AND (thyroid pathology) AND (treatment) AND (within four weeks of study entry) AND (zopiclone))"}
{"candidate_id": "LLM05075", "doc_id": "NCT03624881_exc", "case_bucket": "or", "source_criterion": "Previous surgical or catheter ablation for atrial fibrillation Previous cardiac surgery (including CABG) within the past 6 months (180 days) Valvular cardiac surgical/percutaneous procedure (i.e., ventriculotomy, atriotomy, and valve repair or replacement and presence of a prosthetic valve) Any carotid stenting or endarterectomy Documented LA thrombus on imaging LA size > 50 mm (parasternal long axis view) LVEF < 40% Contraindication to anticoagulation (heparin or warfarin) History of blood clotting or bleeding abnormalities PCI/MI within the past 2 months (60 days) Documented thromboembolic event (including TIA) within the past 12 months (365 days) Rheumatic Heart Disease Uncontrolled heart failure or NYHA function class III or IV Severe mitral regurgitation (Regurgitant volume = 60 mL/beat, Regurgitant fraction = 50%, and/or Effective regurgitant orifice area = 0.40cm2) Awaiting cardiac transplantation or other cardiac surgery within the next 12 months (365 days) Unstable angina Acute illness or active systemic infection or sepsis AF secondary to electrolyte imbalance, thyroid disease, or reversible or non-cardiac cause. Presence of implanted ICD/CRT-D. Significant pulmonary disease, (e.g., restrictive pulmonary disease, constrictive or chronic obstructive pulmonary disease) or any other disease or malfunction of the lungs or respiratory system that produces chronic symptoms. Gastroesophageal Reflux Disease (GERD; active requiring significant intervention not including OTC medication) Significant congenital anomaly or medical problem that in the opinion of the investigator would preclude enrollment in this study. Women who are pregnant (as evidenced by pregnancy test if pre-menopausal) Concurrent enrollment in an investigational study evaluating another device, biologic, or drug. Presence of intracardiac thrombus, myxoma, tumor, interatrial baffle or patch or other abnormality that precludes vascular access, or manipulation of the catheter. Life expectancy less than 12 months", "candidate_expression": "((AF secondary) AND (Acute illness active) AND (CABG) AND (Concurrent enrollment in an investigational study evaluating another device, biologic, or drug.) AND (Contraindication) AND (Effective regurgitant orifice area = 0.40cm2) AND (GERD) AND (Gastroesophageal Reflux Disease) AND (LA size > 50 mm parasternal long axis view) AND (LA thrombus) AND (LVEF < 40%) AND (Life expectancy less than 12 months) AND (MI within the past 2 months within the past 60 days) AND (NYHA function class III IV) AND (PCI) AND (Regurgitant fraction = 50%) AND (Regurgitant volume = 60 mL/beat) AND (Rheumatic Heart Disease) AND (TIA within the past 12 months within the past 365 days) AND (Unstable angina) AND (Valvular cardiac percutaneous procedure) AND (Valvular cardiac surgical procedure) AND (Women) AND (ablation surgical) AND (abnormality other) AND (anticoagulation) AND (atrial fibrillation) AND (atriotomy) AND (bleeding abnormalities) AND (blood clotting) AND (cardiac surgery Previous within the past 6 months (180 days)) AND (cardiac surgery within the next 365 days) AND (cardiac transplantation) AND (carotid stenting) AND (catheter ablation) AND (chronic obstructive pulmonary disease) AND (chronic symptoms) AND (congenital anomaly) AND (constrictive pulmonary disease) AND (disease of the lungs) AND (disease of the respiratory system) AND (electrolyte imbalance) AND (endarterectomy) AND (heart failure Uncontrolled) AND (heparin) AND (imaging) AND (implanted ICD/CRT-D) AND (interatrial baffle) AND (intracardiac thrombus) AND (malfunction of the lungs) AND (manipulation of the catheter) AND (medical problem) AND (mitral regurgitation Severe) AND (myxoma) AND (non-cardiac cause reversible) AND (patch) AND (pre-menopausal) AND (precludes) AND (pregnancy test) AND (pregnant) AND (prosthetic valve) AND (pulmonary disease Significant) AND (restrictive pulmonary disease) AND (sepsis) AND (significant intervention) AND (systemic infection) AND (thromboembolic event) AND (thyroid disease) AND (tumor) AND (valve repair) AND (valve replacement) AND (vascular access) AND (ventriculotomy) AND (warfarin) AND NOT (OTC medication Significant))"}
```
