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
{"candidate_id": "LLM00401", "doc_id": "NCT02361892_exc", "case_bucket": "or", "source_criterion": "endometrial hyperplasia with atypia, estrogen-progestin therapy in the 2 months before enrollment, autoimmune diseases, chronic, metabolic, systemic and endocrine disorders, including hyperandrogenism, hyperprolactinemia, diabetes mellitus and thyroid disease, hypogonadotropic hypogonadism, majors clinical conditions", "candidate_expression": "((atypia) AND (autoimmune diseases) AND (chronic disorders) AND (endocrine disorders) AND (endometrial hyperplasia) AND (estrogen-progestin therapy in the 2 months before enrollment) AND (hypogonadotropic hypogonadism) AND (majors clinical conditions) AND (metabolic disorders) AND (systemic disorders) AND ((diabetes mellitus) OR (hyperandrogenism) OR (hyperprolactinemia) OR (thyroid disease)))"}
{"candidate_id": "LLM00402", "doc_id": "NCT01650792_inc", "case_bucket": "other", "source_criterion": "Diagnosis of heart failure according to Framingham criteria Informed consent Age 18 years or above", "candidate_expression": "((18 years or above) AND (Age) AND (Framingham criteria) AND (Informed consent) AND (heart failure))"}
{"candidate_id": "LLM00403", "doc_id": "NCT03034096_exc", "case_bucket": "or", "source_criterion": "Age less than 18 years American Society of Anesthesiologist Class 5 Projected life expectancy less than 30 days Known or suspected hypersensitivity to either propofol, e.g. egg or soy allergy, or volatile general anesthetic agents Known or suspected history of malignant hyperthermia", "candidate_expression": "((Age less than 18 years) AND (American Society of Anesthesiologist Class 5) AND (Projected life expectancy less than 30 days) AND (malignant hyperthermia history) AND ((propofol) OR (volatile general anesthetic agents)) AND ((egg) OR (soy)) AND ((allergy) OR (hypersensitivity)) AND ((Known) OR (suspected)))"}
{"candidate_id": "LLM00404", "doc_id": "NCT02668016_exc", "case_bucket": "or", "source_criterion": "History of neuropathy Regularly taking prescribed analgesia History of a chronic pain condition History of severe mental illness (as their experience of symptoms may already be altered) Current use of fibrates (because of the risk of interaction with statins but will not exclude participants taking ezetimibe). Severe previous reaction or reaction considered immunological, such as anaphylaxis, facial swelling, severe rash, muscle ache with rise in serum creatine kinase, inflammatory myopathy, rhabdomyolysis or liver function abnormalities (aspartate transaminase (AST) or alanine transaminase (ALT) greater than 3 times upper limit or normal). Side-effects taking longer than 2 weeks to develop (because in such participants much longer blocks of treatment would be required, if the present study is positive such studies will be planned for the future)*. History of statin intolerance with drug interaction to antiretroviral drugs. History of statin intolerance to any other drug. Pregnant or breast feeding. Side effects taking longer than 2 weeks to present. In clinical judgement of study doctor, participant should not participate.", "candidate_expression": "((ALT) AND (AST) AND (Pregnant or breast feeding) AND (Regularly) AND (analgesia) AND (antiretroviral drugs) AND (chronic pain) AND (fibrates) AND (greater than 3 times upper limit or normal) AND (intolerance) AND (mental illness) AND (neuropathy) AND (rise) AND (serum creatine kinase) AND (severe) AND (statin) AND ((alanine transaminase) OR (aspartate transaminase)) AND ((anaphylaxis) OR (facial swelling,) OR (inflammatory myopathy) OR (liver function abnormalities) OR (muscle ache) OR (rhabdomyolysis) OR (severe rash)))"}
{"candidate_id": "LLM00405", "doc_id": "NCT02804126_inc", "case_bucket": "other", "source_criterion": "obtained consent singleton pregnancy subarachnoid anaesthesia", "candidate_expression": "((pregnancy) AND (singleton) AND (subarachnoid anaesthesia))"}
{"candidate_id": "LLM00406", "doc_id": "NCT02940912_inc", "case_bucket": "or", "source_criterion": "Idiopathic Parkinson's disease ( Hughes AJ et al. 2001) Patients with motor fluctuations Chronic Insomnia disorder criteria according to the criteria of DMS- V ( American Psychiatric Association, 2013) and insomnia severity index > 15 Able to use independently the device required for treatment by apomorphine Collection of written informed consent (legal obligation for any project under the public health law , bioethics laws and / or CNIL) . Affiliate to social security or beneficiary of such a regime", "candidate_expression": "((Affiliate to social security) AND (Chronic Insomnia disorder criteria of DMS- V) AND (Parkinson's disease Idiopathic) AND (apomorphine) AND (device) AND (insomnia severity index > 15) AND (motor fluctuations) AND (social security beneficiary))"}
{"candidate_id": "LLM00407", "doc_id": "NCT03318874_inc", "case_bucket": "other", "source_criterion": "Meibomian Gland Dysfunction Eligible for heat treatment Ocular Surface Disease Index (OSDI) >12 Quality or expressibility score =20 years old: >1 or >20 years old: =1 Non-invasive tear film break-up time (NITBUT) <10 s in at least one eye Schirmer-1 test >5 mm after 5 min", "candidate_expression": "((Meibomian Gland Dysfunction) AND (Non-invasive tear film break-up time (NITBUT) <10 s eye) AND (OSDI) AND (Ocular Surface Disease Index >12) AND (Schirmer-1 test >5 mm after 5 min) AND (expressibility score) AND (heat treatment Eligible for) AND (score Quality))"}
{"candidate_id": "LLM00408", "doc_id": "NCT01907230_inc", "case_bucket": "or", "source_criterion": "Age : from 20 to 90 y/o. HBsAg-positive for more than 6 months and HBV DNA < 2000 IU/ml (Subgroup 1)or HBsAg-negative but anti-HBc positive with HBV DNA < 2000 IU/ml (Subgroup 2). Inflammatory arthritis patients who plan to treat with biological agents, including Humira or Enbrel or Simponi or Orencia or Mabthera or Actemra; as first line biologic treatment is indicated.", "candidate_expression": "((Age 20 to 90 y/o) AND (HBV DNA < 2000 IU/ml) AND (HBsAg negative) AND (HBsAg positive more than 6 months) AND (Inflammatory arthritis) AND (anti-HBc positive) AND (biological agents) AND ((Actemra) OR (Enbrel) OR (Humira) OR (Mabthera) OR (Orencia) OR (Simponi)))"}
{"candidate_id": "LLM00409", "doc_id": "NCT02802644_inc", "case_bucket": "other", "source_criterion": "Non-ST segement elevation acute coronary syndrome", "candidate_expression": "((Non-ST segement elevation) AND (acute coronary syndrome))"}
{"candidate_id": "LLM00410", "doc_id": "NCT00926523_inc", "case_bucket": "other", "source_criterion": "Subject are at least 18 years of age Subject has confirmed Pulmonary Hypertension and Interstitial Lung Disease Subject are able to complete study procedures, such as spirometry, and Pulmonary Exercise test.", "candidate_expression": "((Interstitial Lung Disease) AND (Pulmonary Exercise test) AND (Pulmonary Hypertension) AND (age) AND (at least 18 years) AND (confirmed) AND (spirometry) AND (study procedures))"}
{"candidate_id": "LLM00411", "doc_id": "NCT03615508_inc", "case_bucket": "or", "source_criterion": "Horner's Syndrome History of taking an alpha blocker (tamsulosin/ terazosin/doxazosin/alfuzosin/silodosin) medication", "candidate_expression": "((Horner's Syndrome) AND (alfuzosin) AND (alpha blocker) AND (doxazosin) AND (silodosin) AND (tamsulosin) AND (terazosin))"}
{"candidate_id": "LLM00412", "doc_id": "NCT02902120_inc", "case_bucket": "or", "source_criterion": "At least 18 years of age at the time of screening Have stable renal function for one month (30 days) prior to enrollment Have Chronic HCV infection prior to transplantation with documented HCV viremia = 1,000 IU/ml at screening and either documented HCV Ab positivity or HCV viremia = 1,000 IU/ml at least 6 months prior to enrollment. Documented genotype 1 HCV infection prior to enrollment and after their transplant in the post-transplantation cohort HCV disease staging within 12 months prior to enrollment by liver biopsy, transient elastography, or biochemical testing Be able to give informed consent and comply with study guidelines Women of childbearing age will be required to have a negative pregnancy test at enrollment and use birth control throughout the duration of treatment. On the transplant waiting list followed by the University of Maryland's nephrology clinic or the Baltimore VA's nephrology clinic On chronic hemodialysis not yet on the transplant list and followed in the University's hemodialysis center or in the University's nephrology clinic Have chronic kidney disease with GFR <50", "candidate_expression": "((Be able to give informed consent and comply with study guidelines) AND (Chronic HCV infection prior to transplantation) AND (GFR <50) AND (HCV Ab positivity) AND (HCV infection genotype 1 prior to enrollment after their transplant i) AND (HCV viremia = 1,000 IU/ml) AND (Women of childbearing age will be required to have a negative pregnancy test at enrollment and use birth control throughout the duration of treatment.) AND (age At least 18 years) AND (biochemical testing) AND (chronic kidney disease) AND (disease staging HCV within 12 months prior to enrollment) AND (hemodialysis chronic) AND (liver biopsy) AND (renal function stable one month (30 days) prior to enrollment) AND (transient elastography))"}
{"candidate_id": "LLM00413", "doc_id": "NCT00785213_exc", "case_bucket": "or", "source_criterion": "Recent participation (within 28 days) in other research studies Recent significant blood donation or plasma donation Pregnant or lactating Test positive at screening for human immunodeficiency virus (HIV), hepatitis B surface antigen (HbsAg), or hepatitis C virus (HCV) Recent (2-year) history or evidence of alcoholism or drug abuse History or presence of significant cardiovascular, pulmonary, hepatic, gallbladder or biliary tract, renal, hematologic, gastrointestinal, endocrine, immunologic, dermatologic, neurologic, or psychiatric disease Subjects who have used any drugs or substances known to inhibit or induce cytochrome (CYP) P450 enzymes and/or P-glycoprotein (P-gp) within 28 days prior to the first dose and throughout the study Drug allergies to quinine sulfate or rosiglitazone", "candidate_expression": "((History or presence of significant cardiovascular, pulmonary, hepatic, gallbladder or biliary tract, renal, hematologic, gastrointestinal, endocrine, immunologic, dermatologic, neurologic, or psychiatric disease) AND (Pregnant) AND (Recent participation (within 28 days) in other research studies) AND (alcoholism) AND (allergies) AND (blood donation within 28 days) AND (drug abuse) AND (drugs known to induce P-glycoprotein (P-gp)) AND (drugs known to induce cytochrome (CYP) P450 enzymes) AND (drugs known to inhibit P-glycoprotein (P-gp)) AND (drugs known to inhibit cytochrome (CYP) P450 enzymes) AND (hepatitis B surface antigen (HbsAg)) AND (hepatitis C virus (HCV) 2-year) AND (history evidence) AND (human immunodeficiency virus (HIV)) AND (lactating) AND (plasma donation) AND (quinine sulfate) AND (rosiglitazone))"}
{"candidate_id": "LLM00414", "doc_id": "NCT02312960_inc", "case_bucket": "other", "source_criterion": "Subject was previously enrolled in a selected company sponsored feeder trial, and has received at least 1 dose of radium 223 dichloride or placebo in the feeder trial", "candidate_expression": "(Subject was previously enrolled in a selected company sponsored feeder trial, and has received at least 1 dose of radium 223 dichloride or placebo in the feeder trial)"}
{"candidate_id": "LLM00415", "doc_id": "NCT02589691_inc", "case_bucket": "other", "source_criterion": "age <2 years indication of general anesthesia with tracheal intubation inhalational induction scheduled written informed consent of both parents", "candidate_expression": "((age <2 years) AND (general anesthesia indication) AND (inhalational induction scheduled) AND (tracheal intubation) AND (written informed consent of both parents))"}
{"candidate_id": "LLM00416", "doc_id": "NCT03465397_exc", "case_bucket": "or", "source_criterion": "Patients with a calculated PRA higher than 0% per solid phase and / or anti-HLA class I and / or class II antibodies detectable by single antigen test (Luminex®). Positive result of Cross Match. Patients who receive a graft from a cadaver donor. Identical HLA patients Patients who have undergone a previous solid organ transplant (including kidney transplant) or who are going to receive another solid organ transplant concomitantly. Glomerular primary focal and segmental sclerosis Atypical hemolytic uremic syndrome (aHUS) / thrombotic thrombocytopenic purpura syndrome. Patients with chronic infection with Hepatitis B virus (HBV) and / or active infection with Hepatitis C virus (positive PCR result) at the time of transplant. Patients with infection with the known Human Immunodeficiency Virus (HIV). Patients with active systemic infection that requires the continued administration of antibiotics. Patients with any neoplasm except localized skin cancer and who is receiving adequate treatment. Patients with severe anemia (hemoglobin <6g / dl), leukopenia (WBC <2500 / mm3) and / or thrombocytopenia (platelets <80,000 / mm3). Patients who are hemodynamically unstable even if they have hemoglobin levels> 6g / dL. Patients with intestinal pathology or severe diarrhea that may decrease absorption according to medical criteria. Patients with known hypersensitivity to any of the drugs used in this study. Patients who have received any investigational drug in the 30 days prior to their inclusion in this study. Potentially fertile women who do not agree to use reliable contraceptive measures during the trial, who are pregnant, breastfeeding or who present a positive pregnancy test at the time of their inclusion in the study. Patients who are legally detained in an official institution.", "candidate_expression": "((<2500 / mm3) AND (<6g / dl) AND (<80,000 / mm3) AND (> 6g / dL) AND (Cross Match) AND (Human Immunodeficiency Virus (HIV)) AND (Identical HLA) AND (Luminex) AND (PCR result) AND (Patients who have received any investigational drug in the 30 days prior to their inclusion in this study.) AND (Positive) AND (Potentially fertile women who do not agree to use reliable contraceptive measures during the trial, who are pregnant, breastfeeding or who present a positive pregnancy test at the time of their inclusion in the study.) AND (WBC) AND (active) AND (anemia) AND (another) AND (antibiotics) AND (at the time of transplant) AND (calculated PRA) AND (chronic) AND (concomitantly) AND (continued administration) AND (drugs used in this study) AND (except) AND (graft from a cadaver donor) AND (hemodynamically unstable) AND (hemoglobin) AND (hemoglobin levels) AND (higher than 0% per solid phase) AND (hypersensitivity) AND (kidney transplant) AND (legally detained) AND (localized skin cancer) AND (may decrease absorption) AND (neoplasm) AND (official institution) AND (platelets) AND (positive) AND (previous) AND (severe) AND (single antigen test) AND (solid organ transplant) AND (systemic infection) AND ((Glomerular primary focal sclerosis) OR (Glomerular segmental sclerosis)) AND ((Atypical hemolytic uremic syndrome (aHUS)) OR (thrombotic thrombocytopenic purpura syndrome)) AND ((Hepatitis B virus (HBV)) OR (Hepatitis C virus)) AND ((anti-HLA class I) OR (anti-HLA class II)) AND ((leukopenia) OR (thrombocytopenia)) AND ((intestinal pathology) OR (severe diarrhea)))"}
{"candidate_id": "LLM00417", "doc_id": "NCT01446094_exc", "case_bucket": "other", "source_criterion": "Inability to give informed consent Possible pregnancy (confirmed by urine test) Women who are breastfeeding Severe claustrophobia Inability to lie flat for 20-30 minutes (the anticipated amount of time to complete the MRI procedure) Individuals with cochlear implants Individuals with non-MRI compatible aneurysm clips Potential contraindications to regadenoson use due to: Contraindication to administration of Gadolinium (Gd) based contrast agents (GBCA):", "candidate_expression": "((20-30 minutes) AND (Contraindication) AND (Gadolinium (Gd) based contrast agents (GBCA)) AND (Inability to give informed consent) AND (Inability to lie flat) AND (MRI compatible) AND (Possible) AND (Severe) AND (Women) AND (amount of time to complete the MRI procedure) AND (aneurysm clips) AND (breastfeeding) AND (claustrophobia) AND (cochlear implants) AND (confirmed) AND (non) AND (pregnancy) AND (urine test))"}
{"candidate_id": "LLM00418", "doc_id": "NCT02643381_exc", "case_bucket": "or", "source_criterion": "Children (<18 years old). Women who are known to be pregnant. Any patient who has been previously randomized in the EvK Trial. Patients who require endotracheal intubation without sedative medication. For example, patients in full cardiac arrest. Patients with a known allergy to ketamine or etomidate. Any individual wearing a MedAlert bracelet indicating that he/she has formally opted out of the EvK Trial.", "candidate_expression": "((<18 years) AND (Any individual wearing a MedAlert bracelet indicating that he/she has formally opted out of the EvK Trial) AND (Children) AND (Women) AND (allergy) AND (endotracheal intubation) AND (etomidate) AND (full cardiac arrest) AND (ketamine) AND (old) AND (pregnant) AND (previously) AND (randomized) AND (require) AND (sedative medication) AND (without))"}
{"candidate_id": "LLM00419", "doc_id": "NCT03424993_exc", "case_bucket": "or", "source_criterion": "Abnormal resting ECG Current abnormal blood panel (assessed by comprehensive metabolic panel, lipid panel and complete blood count). Hypertension (currently taking anti-hypertensive medications or resting blood pressure >140/90 mmHg) Medical history of cardiovascular disease, malignant cancer, diabetes or kidney disease Obesity (Body Mass Index > 30) Current pregnancy Unable to provide consent", "candidate_expression": "((> 30) AND (>140/90 mmHg) AND (Abnormal) AND (Body Mass Index) AND (Current) AND (Hypertension) AND (Obesity) AND (Unable to provide consent) AND (abnormal) AND (blood panel) AND (complete blood count) AND (lipid panel) AND (metabolic panel) AND (pregnancy) AND (resting ECG) AND ((anti-hypertensive medications) OR (resting blood pressure)) AND ((cardiovascular disease) OR (diabetes) OR (kidney disease) OR (malignant cancer)))"}
{"candidate_id": "LLM00420", "doc_id": "NCT01604187_inc", "case_bucket": "other", "source_criterion": "ASA I-III Colonoscopy Written informed consent from participating subject", "candidate_expression": "((ASA) AND (Colonoscopy) AND (I-III) AND (Written informed consent from participating subject))"}
{"candidate_id": "LLM00421", "doc_id": "NCT02823808_inc", "case_bucket": "other", "source_criterion": "Type 2 Diabetes Mellitus patients Patient who had been diagnosed within the previous 12 months with HbA1c levels of 8.0-12.0%, did not have a medical history related to diabetes, and did not display proliferative retinopathy", "candidate_expression": "((8.0-12.0%) AND (HbA1c) AND (Type 2 Diabetes Mellitus) AND (medical history related to diabetes) AND (not) AND (previous 12 months) AND (proliferative retinopathy))"}
{"candidate_id": "LLM00422", "doc_id": "NCT03118232_exc", "case_bucket": "other", "source_criterion": "Nursing homes will not be eligible to participate if they meet the following criteria: Facilities routinely using decolonization Dedicated psychiatric nursing homes Facilities with a resident population with >=20% combative patients Pediatric facilities", "candidate_expression": "((>=20%) AND (Nursing homes) AND (Pediatric facilities) AND (combative patients) AND (decolonization) AND (psychiatric nursing homes) AND (resident population) AND (routinely))"}
{"candidate_id": "LLM00423", "doc_id": "NCT02566863_inc", "case_bucket": "other", "source_criterion": "patients classified with American Society of Anesthesiologists Physical Status Classification System as 1 or 2 status planned eye surgery under sedation", "candidate_expression": "((1 or 2) AND (eye surgery) AND (planned) AND (sedation) AND (status American Society of Anesthesiologists Physical Status Classification System) AND (under sedation))"}
{"candidate_id": "LLM00424", "doc_id": "NCT02019628_exc", "case_bucket": "or", "source_criterion": "1. Currently enrolled in another research trial for investigative nutritional or other therapies thought to have an impact on immune system functioning. 2. Unable to consent to the study. 3. Women who are pregnant or are attempting conception, especially in the presence of a history of recurrent spontaneous abortion. 4. Other medical complications that might preclude one from participating in the study, i.e., recent heart attack or stroke or chronic kidney disease. 5. Currently taking immunomodulatory medication, i.e. interferon. 6. Currently taking other medications thought to have an impact on immune system functioning, i.e., chemotherapeutic agents. 7. Known allergy to rice, rice bran, or related food products. 8. Known allergy to mushrooms or related food products. 9. History of malignancies related to the NK cell line, including: NK cell leukemias and T-cell large granular lymphocyte leukemias, NK-cell lymphoproliferative disease of granular lymphocytes, and NK cell lymphomas, e.g., nasal and nasal-like NK/T-cell lymphomas. 10. Current smoker.", "candidate_expression": "((Current) AND (Currently) AND (Currently enrolled in another research trial for investigative nutritional or other therapies thought to have an impact on immune system functioning.) AND (History) AND (Other) AND (Unable to consent to the study.) AND (Women) AND (allergy to rice) AND (allergy to rice bran) AND (chemotherapeutic agents) AND (immunomodulatory medication) AND (impact on immune system functioning) AND (interferon) AND (medical complications) AND (medications) AND (other) AND (participating in the study) AND (preclude) AND (pregnant) AND (recent) AND (recurrent) AND (rice) AND (rice bran) AND (smoker) AND (spontaneous abortion) AND ((chronic kidney disease) OR (heart attack) OR (stroke)) AND ((malignancies) OR (related to the NK cell line)) AND ((NK cell leukemias) OR (NK cell lymphomas) OR (NK-cell lymphoproliferative disease of granular lymphocytes) OR (T-cell large granular lymphocyte leukemias) OR (nasal NK/T-cell lymphomas) OR (nasal-like NK/T-cell lymphomas)) AND ((allergy to food products) OR (allergy to mushrooms)))"}
{"candidate_id": "LLM00425", "doc_id": "NCT00931983_inc", "case_bucket": "or", "source_criterion": "Children between the ages of 4-18 with incomplete ASIA C or D spinal cord injuries at least 12 months before study enrolment Non-ambulatory or 'exercise only' ambulators with or without assistive devices Normal motor and cognitive development up to time of injury Medical Stability", "candidate_expression": "((ASIA C or D) AND (Children) AND (Medical Stability) AND (ages 4-18) AND (assistive devices) AND (cognitive development) AND (motor development time of injury) AND (spinal cord injuries incomplete at least 12 months before study enrolment study enrolment) AND (('exercise only' ambulators) OR (Non-ambulatory)))"}
```
