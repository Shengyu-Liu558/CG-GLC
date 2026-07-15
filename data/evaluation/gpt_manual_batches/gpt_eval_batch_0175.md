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
{"candidate_id": "LLM04351", "doc_id": "NCT03532620_inc", "case_bucket": "or", "source_criterion": "Age 18-80 years old; IFG: 5.6mmol/L (100mg/dl)=FPG<7.0mmol/L (126mg/dl), or IGT: 7.8mmol/L (140mg/dl)=OGTT 2-h PG<11.1mmol/L (200mg/dl), or HbA1C 5.7-6.4% (39-47mmol/mol); 2.6mmol/L (100mg/dl)=LDL-C=5.2mmol/L (200mg/dl), and TG<5.7mmol/L (500mg/dl); 130mmHg=SBP<180mmHg, or 80mmHg=DBP<110mmHg or ongoing anti-hypertensive therapy; Patients volunteered for the study and signed informed consent.", "candidate_expression": "((100mg/dl) AND (126mg/dl) AND (130mmHg) AND (140mg/dl) AND (18-80 years old) AND (2.6mmol/L) AND (200mg/dl) AND (39-47mmol/mol) AND (5.2mmol/L) AND (5.6mmol/L) AND (5.7-6.4%) AND (500mg/dl) AND (7.8mmol/L) AND (80mmHg=) AND (<11.1mmol/L) AND (<110mmHg) AND (<180mmHg) AND (<5.7mmol/L) AND (<7.0mmol/L) AND (Age) AND (FPG) AND (LDL-C) AND (OGTT 2-h PG) AND (Patients volunteered for the study and signed informed consent.) AND (TG) AND (ongoing) AND ((HbA1C) OR (IFG) OR (IGT)) AND ((DBP) OR (SBP) OR (anti-hypertensive therapy)))"}
{"candidate_id": "LLM04352", "doc_id": "NCT03465397_exc", "case_bucket": "or", "source_criterion": "Patients with a calculated PRA higher than 0% per solid phase and / or anti-HLA class I and / or class II antibodies detectable by single antigen test (Luminex®). Positive result of Cross Match. Patients who receive a graft from a cadaver donor. Identical HLA patients Patients who have undergone a previous solid organ transplant (including kidney transplant) or who are going to receive another solid organ transplant concomitantly. Glomerular primary focal and segmental sclerosis Atypical hemolytic uremic syndrome (aHUS) / thrombotic thrombocytopenic purpura syndrome. Patients with chronic infection with Hepatitis B virus (HBV) and / or active infection with Hepatitis C virus (positive PCR result) at the time of transplant. Patients with infection with the known Human Immunodeficiency Virus (HIV). Patients with active systemic infection that requires the continued administration of antibiotics. Patients with any neoplasm except localized skin cancer and who is receiving adequate treatment. Patients with severe anemia (hemoglobin <6g / dl), leukopenia (WBC <2500 / mm3) and / or thrombocytopenia (platelets <80,000 / mm3). Patients who are hemodynamically unstable even if they have hemoglobin levels> 6g / dL. Patients with intestinal pathology or severe diarrhea that may decrease absorption according to medical criteria. Patients with known hypersensitivity to any of the drugs used in this study. Patients who have received any investigational drug in the 30 days prior to their inclusion in this study. Potentially fertile women who do not agree to use reliable contraceptive measures during the trial, who are pregnant, breastfeeding or who present a positive pregnancy test at the time of their inclusion in the study. Patients who are legally detained in an official institution.", "candidate_expression": "((Atypical hemolytic uremic syndrome (aHUS)) AND (Cross Match Positive) AND (Glomerular primary focal sclerosis) AND (Glomerular segmental sclerosis) AND (Hepatitis B virus (HBV) chronic) AND (Hepatitis C virus active) AND (Human Immunodeficiency Virus (HIV)) AND (Identical HLA) AND (Luminex) AND (PCR result positive) AND (Patients who have received any investigational drug in the 30 days prior to their inclusion in this study.) AND (Potentially fertile women who do not agree to use reliable contraceptive measures during the trial, who are pregnant, breastfeeding or who present a positive pregnancy test at the time of their inclusion in the study.) AND (WBC <2500 / mm3) AND (anemia severe) AND (antibiotics continued administration) AND (calculated PRA higher than 0% per solid phase anti-HLA class I anti-HLA class II) AND (drugs used in this study) AND (graft from a cadaver donor) AND (hemodynamically unstable) AND (hemoglobin <6g / dl) AND (hemoglobin levels > 6g / dL) AND (hypersensitivity) AND (intestinal pathology) AND (kidney transplant) AND (legally detained) AND (leukopenia) AND (neoplasm) AND (official institution) AND (platelets <80,000 / mm3) AND (severe diarrhea) AND (single antigen test) AND (solid organ transplant another concomitantly) AND (solid organ transplant previous) AND (systemic infection active) AND (thrombocytopenia) AND (thrombotic thrombocytopenic purpura syndrome) AND NOT (localized skin cancer))"}
{"candidate_id": "LLM04353", "doc_id": "NCT03120533_inc", "case_bucket": "other", "source_criterion": "Healthy Volunteers: Age of at least 18 years Existence of a contraceptive method for women of child-bearing age Person affiliated to social security or beneficiary of such a scheme Signed consent form Systemic sclerosis patients: Systemic sclerosis meeting the EULAR criteria. Presence of at least 2 ischemic digital cutaneous ulcerations on two different fingers, with digital ulcers classified as \"active ulcers\" according to the North American working group definition: epithelial denudation is clearly Visible at one place and the bed of de-epithelialized ulcer can be seen; Ulcerations distal to the proximal interphalangeal joint, not associated with calcinosis or bony relief. Ulcers whose major axis measured with the electronic caliper is ≥ 2 mm Age greater than or equal to 18 years Existence of a contraceptive method for women of reproductive age A person who is or is a beneficiary of social security Informed and signed consent signed by the patient or his / her legal representative.", "candidate_expression": "((Age) AND (EULAR criteria) AND (North American working group definition) AND (Systemic sclerosis) AND (Ulcers) AND (active) AND (age) AND (at least 18 years) AND (at least 2 on two different fingers) AND (child-bearing) AND (contraceptive) AND (contraceptive method) AND (digital ulcers) AND (epithelial denudation is clearly Visible at one place and the bed of de-epithelialized ulcer can be seen; Ulcerations distal to the proximal interphalangeal joint, not associated with calcinosis or bony relief) AND (greater than or equal to 18 years) AND (ischemic digital cutaneous ulcerations) AND (major axis) AND (measured with the electronic caliper) AND (meeting) AND (reproductive) AND (women) AND (≥ 2 mm))"}
{"candidate_id": "LLM04354", "doc_id": "NCT02478346_exc", "case_bucket": "other", "source_criterion": "NA", "candidate_expression": "(EMPTY)"}
{"candidate_id": "LLM04355", "doc_id": "NCT02759861_inc", "case_bucket": "or", "source_criterion": "The subject must be willingly and able to provide written informed consent Age 19 years of age or older (The age of consent in Nebraska) HCV treatment-naïve, as defined as no prior exposure to any Interferon (IFN), RBV, or other FDA approved or experimental HCV-specific direct-acting antiviral agent HCV RNA level at most 6 months prior to the Baseline/Day 1 visit. HCV genotyping 1a, 1b, or mixed 1a/ab. Any non-definitive results will exclude the subject from study participation. Alcohol misuse as defined by the Alcohol Use Disorders Identification Test (AUDIT) score subjects must score > 8 (associated with harmful or hazardous drinking) History of a liver biopsy showing cirrhosis (e.g. Metavir score = 4 or Ishak score > 5) Fibroscan showing cirrhosis or results > 12.5 kPa FIBRO Spect II index consistent with F3 or F4 AND an AST : platelet ration index (APRI) of > 2 during Screening Liver biopsy within 2 years of Screening showing absence of cirrhosis Fibroscan within 6 months of Baseline/Day1 with a result of = 12.5 kPa FIBRO Spect II Index consistent with F0- F2 AND APRI of = 1 during Screening Liver imaging within 6 months of Baseline/Day 1 to exclude hepatocellular carcinoma HCC) is required ALT < 10 x the upper limit of normal (ULN) AST < 10 x ULN Direct bilirubin < 2.0 x ULN Platelets > 50,000 HbA1c < 8.5% Creatinine clearance (CLcr) = 60 mL /min, as calculated by the Cockcroft-Gault equation Hemoglobin = 11 g/dL for female subjects; = 12 g/dL for male subjects. Albumin = 2.5 g/dL INR = 1.5 x ULN unless subject has known hemophilia or is stable on an anticoagulant regimen affecting INR. Subject has not been treated with any investigational drug or device within 30 days of the screening visit.", "candidate_expression": "((ALT < 10 x the upper limit of normal (ULN)) AND (APRI = 1) AND (AST < 10 x ULN) AND (Age 19 years of age or older) AND (Albumin = 2.5 g/dL) AND (Alcohol Use Disorders Identification Test (AUDIT) score > 8) AND (Alcohol misuse) AND (Creatinine clearance (CLcr) = 60 mL /min Cockcroft-Gault equation) AND (Direct bilirubin < 2.0 x ULN) AND (FIBRO Spect II Index F0- F2 during Screening) AND (FIBRO Spect II index F3 or F4 AST during Screening) AND (Fibroscan) AND (Fibroscan within 6 months of Baseline/Day1 = 12.5 kPa) AND (HCV) AND (HCV RNA level at most 6 months prior to the Baseline/Day 1 visit) AND (HCV genotyping 1a, 1b, or mixed 1a/ab) AND (HbA1c < 8.5%) AND (Hemoglobin) AND (INR = 1.5 x ULN) AND (Interferon (IFN)) AND (Ishak score > 5) AND (Liver biopsy within 2 years of Screening) AND (Liver imaging within 6 months of Baseline/Day 1) AND (Metavir score = 4) AND (Platelets > 50,000) AND (RBV) AND (The subject must be willingly and able to provide written informed consent) AND (cirrhosis) AND (cirrhosis > 12.5 kPa) AND (female = 11 g/dL) AND (hemophilia) AND (liver biopsy) AND (male = 12 g/dL) AND (platelet ration index (APRI) > 2) AND (stable on an anticoagulant regimen affecting INR) AND NOT (cirrhosis) AND NOT (hepatocellular carcinoma HCC)) AND NOT (treatment))"}
{"candidate_id": "LLM04356", "doc_id": "NCT01581749_inc", "case_bucket": "or", "source_criterion": "histologically proven prostate adenocarcinoma within 1 year of enrollment Low risk: Gleason <or=6 & PSA <or=10 & Clinical Stage T1b-T2a,Nx or N0, Mx or M0 Intermediate risk:Gleason <or=6 & PSA<or=10 & Clinical Stage T2b OR Gleason=7 & PSA<or=10 & Clinical Stage T1b-T2b OR Gleason <or=6 & PSA > 10 & < or =20 & Clinical Stage T1b- T2b, Nx or NO, Mx or M0 ECOG Performance Status 0-1 No prior prostate radiation or other definitive therapy", "candidate_expression": "((Clinical Stage T1b- T2b Nx NO Mx M0) AND (Clinical Stage T1b-T2a Nx N0 Mx) AND (Clinical Stage T1b-T2b) AND (Clinical Stage T2b) AND (ECOG Performance Status 0-1) AND (Gleason <or=6) AND (Gleason =7) AND (Intermediate risk M0) AND (Low risk) AND (PSA <or=10) AND (PSA > 10 & < or =20) AND (definitive therapy) AND (prostate adenocarcinoma histologically proven within 1 year of enrollment) AND (prostate radiation))"}
{"candidate_id": "LLM04357", "doc_id": "NCT00959569_inc", "case_bucket": "or", "source_criterion": "end diastolic diameter >60 mm and/or an ejection fraction <50% written informed consent age >18 years", "candidate_expression": "((age >18 years) AND (written informed consent) AND ((ejection fraction <50%) OR (end diastolic diameter >60 mm)))"}
{"candidate_id": "LLM04358", "doc_id": "NCT03097068_exc", "case_bucket": "or", "source_criterion": "History of anti-vascular endothelial growth factor treatment in the past 12 months Any diabetic macular edema treatment in the past 4 months Heart attack, stroke, transient ischemic attack or acute congestive heart failure within 4 months", "candidate_expression": "((anti-vascular endothelial growth factor) AND (diabetic macular edema) AND (in the past 12 months) AND (in the past 4 months) AND (treatment) AND (within 4 months) AND ((Heart attack) OR (acute congestive heart failure) OR (stroke) OR (transient ischemic attack)))"}
{"candidate_id": "LLM04359", "doc_id": "NCT01963754_inc", "case_bucket": "or", "source_criterion": "Single unit implant rehabilitation Maxilla and mandible Must accept treatment plan Must sign informed consent dental extraction performed at least 3 month prior Must have at least 6 mm of residual bone Absence of oral lesions keratinized tissue must be present", "candidate_expression": "((Must accept treatment plan) AND (Must sign informed consent) AND (Single unit implant rehabilitation Maxilla mandible) AND (dental extraction at least 3 month prior) AND (keratinized tissue must be present) AND (residual bone at least 6 mm) AND NOT (oral lesions))"}
{"candidate_id": "LLM04360", "doc_id": "NCT03252249_exc", "case_bucket": "or", "source_criterion": "Clear indication for specific duration of dual anti-platelet therapy Type 2 myocardial infarction Contraindication to aspirin or P2Y12 receptor antagonist Non-resident of Scotland Previous recruitment into the trial Inability or unwilling to give informed consent", "candidate_expression": "((Clear indication for specific duration) AND (Contraindication) AND (Inability or unwilling to give informed consent) AND (Non-resident) AND (P2Y12 receptor antagonist) AND (Previous recruitment into the trial) AND (Scotland) AND (Type 2 myocardial infarction) AND (aspirin) AND (dual anti-platelet therapy))"}
{"candidate_id": "LLM04361", "doc_id": "NCT03034837_inc", "case_bucket": "other", "source_criterion": "generally healthy grade 1-2 school children with written parental consent with at least 1 sound and fully erupted permanent first molar", "candidate_expression": "((at least 1) AND (children) AND (fully erupted) AND (generally healthy) AND (grade 1-2 school) AND (permanent first molar) AND (sound) AND (with written parental consent))"}
{"candidate_id": "LLM04362", "doc_id": "NCT02416765_inc", "case_bucket": "or", "source_criterion": "1. Males and females ≥ 18 years old. 2. Clinical diagnosis of type 1 diabetes for at least one year. 3. The subject will have been on insulin pump therapy for at least 3 months and currently using a fast actin insulin analog (Lispro, Aspart or Guilisine). 4. Last (less than 3 months) HbA1c ≤ 10%. 5. Currently using carbohydrate counting as the meal insulin dose strategy.", "candidate_expression": "((Currently) AND (HbA1c) AND (Last (less than 3 months)) AND (carbohydrate counting) AND (currently) AND (fast actin insulin analog) AND (for at least 3 months) AND (for at least one year) AND (insulin pump therapy) AND (meal insulin dose strategy) AND (old) AND (type 1 diabetes) AND (≤ 10%) AND (≥ 18 years old) AND ((Aspart) OR (Guilisine) OR (Lispro)) AND ((Males) OR (females)))"}
{"candidate_id": "LLM04363", "doc_id": "NCT02034019_exc", "case_bucket": "other", "source_criterion": "Any intraocular inflammation in the study eye present during the screening slit lamp examination Score greater than \"0\" on the Ocular Pain Assessment in the study eye at Screening Any intraocular inflammation in the study eye present during the screening slit lamp examination", "candidate_expression": "((Ocular Pain Assessment greater than \"0\" at Screening) AND (intraocular inflammation) AND (intraocular inflammation the screening slit lamp examination) AND (slit lamp examination intraocular inflammation during the screening slit lamp examination))"}
{"candidate_id": "LLM04364", "doc_id": "NCT02664558_exc", "case_bucket": "or", "source_criterion": "Exclusions Related to Cardiovascular Disease 1. History of uncontrolled hypertension 2. Persistent hypotension at Screening. 3. Evidence or history of left-sided heart disease and/or clinically significant cardiac disease in which pulmonary hypertension is more likely WHO Group 2. 4. Acute decompensated heart failure within 1 month of Screening. 5. Recent initiation (<8 weeks from Screening) or planned initiation of cardiopulmonary rehabilitation exercise program. Exclusions Related to Pulmonary Disease 6. Newly diagnosed with PAH and not on PAH-specific therapy. 7. Pulmonary hypertension due to: 1. Uncorrected congenital systemic-to-pulmonary shunt. 2. Pulmonary veno-occlusive disease and/or pulmonary capillary hemangiomatosis 3. Persistent pulmonary hypertension of the newborn 4. WHO clinical classification Groups 2-5 8. Evidence of significant airway and/or parenchymal lung disease. 9. Chronic infection related to tuberculosis or fungal or mycobacterial disease. Exclusions Based on Other Medical Conditions 10. Chronic infections including, but not limited to tuberculosis (TB), hepatitis B virus (HBV) or hepatitis C virus (HCV). 11. History of portal hypertension or chronic liver disease, including positive serology for infection with HCV and/or HBV. 12. Evidence of active infection requiring intravenous or oral antibiotics within 4 weeks of Screening. 13. Body mass index ≥35.0 at Screening. 14. History of obstructive sleep apnea. 15. History of malignancy within the last 5 years, except nonmelanoma skin cancer and cervical carcinoma in situ treated with curative intent. 16. Neuropsychiatric disorders/symptoms or psychological conditions. 17. Pregnancy or breast-feeding 18. Prior treatment with B cell or lymphocyte-depleting agents (eg, rituximab, Campath) Exclusions Based on Concomitant Medication Use 19. Concurrent regular use of another leukotriene pathway inhibitor, including over-the-counter medications or herbal remedies. Exclusions Based on Laboratory Values 20. Significant/chronic renal insufficiency. 21. Transaminases (alanine transaminase, aspartate transaminase) levels >3 × upper limit of normal (ULN) and/or bilirubin level >2 × ULN. 22. Absolute neutrophil count <1500 mm3. 23. Hemoglobin concentration <9 g/dL at Screening. 24. Hepatic dysfunction as defined by Child-Pugh Class B or C", "candidate_expression": "((Absolute neutrophil count <1500 mm3) AND (B cell -depleting agents) AND (Body mass index ≥35.0 at Screening) AND (Campath) AND (Child-Pugh Class B or C) AND (Hemoglobin concentration <9 g/dL at Screening) AND (Hepatic dysfunction) AND (Neuropsychiatric disorders) AND (Neuropsychiatric symptoms) AND (PAH Newly diagnosed) AND (PAH-specific therapy) AND (Persistent hypotension at Screening) AND (Pregnancy) AND (Pulmonary veno-occlusive disease) AND (Significant) AND (Transaminases levels >3 × upper limit of normal (ULN)) AND (WHO Group 2) AND (WHO clinical classification Groups 2-5) AND (airway disease) AND (alanine transaminase) AND (aspartate transaminase) AND (bilirubin level >2 × ULN) AND (breast-feeding) AND (cardiac disease clinically significant) AND (cardiopulmonary rehabilitation exercise program planned) AND (chronic liver disease) AND (chronic renal insufficiency Significant) AND (clinically significant) AND (congenital systemic-to-pulmonary shunt Uncorrected) AND (fungal disease) AND (heart failure Acute decompensated within 1 month of Screening Recent <8 weeks from Screening) AND (hepatitis B virus (HBV)) AND (hepatitis C virus (HCV)) AND (hypertension History uncontrolled) AND (infection Chronic) AND (infection requiring antibiotics) AND (infection requiring antibiotics within 4 weeks of Screening) AND (infections Chronic) AND (left-sided heart disease) AND (leukotriene pathway inhibitor Concurrent regular use another) AND (lymphocyte-depleting agents) AND (malignancy History within the last 5 years) AND (mycobacterial disease) AND (not) AND (obstructive sleep apnea History) AND (parenchymal lung disease) AND (portal hypertension) AND (psychological conditions) AND (pulmonary capillary hemangiomatosis) AND (pulmonary hypertension) AND (pulmonary hypertension of the newborn Persistent) AND (rituximab) AND (serology for infection HBV positive) AND (serology for infection with HCV positive) AND (significant) AND (treated curative intent) AND (tuberculosis) AND (tuberculosis (TB)) AND NOT (nonmelanoma skin cancer) AND NOT (cervical carcinoma in situ))"}
{"candidate_id": "LLM04365", "doc_id": "NCT03495609_inc", "case_bucket": "other", "source_criterion": "premenopausal women BRCA1 carrier", "candidate_expression": "((BRCA1 carrier) AND (premenopausal) AND (women))"}
{"candidate_id": "LLM04366", "doc_id": "NCT02624908_inc", "case_bucket": "other", "source_criterion": "use of basal-bolus insulin onset of diabetes after age 30 BMI less than 35 eGFR at least 60 ml/mn Hb A1c 7.0-10.0% willingness to perform home glucose monitoring willingness to transmit glucose and medication information weekly", "candidate_expression": "((7.0-10.0%) AND (BMI) AND (Hb A1c) AND (after age 30) AND (at least 60 ml/mn) AND (basal-bolus insulin) AND (eGFR) AND (less than 35) AND (onset of diabetes))"}
{"candidate_id": "LLM04367", "doc_id": "NCT02787863_exc", "case_bucket": "or", "source_criterion": "Vaccination against pneumococcal infection in anamnesis; Application of preparations of immune globulin or blood transfusion within last three months prior to clinical studies; Prolonged use (more than 14 days) immunosuppressants or other immunosuppressive drugs within 6 months prior to the start of the study; Any confirmed or suspected immunosuppressive or immunodeficient condition, including HIV infection; A history or currently hematologic and other cancers; A positive reaction for HIV infection, viral hepatitis B and hepatitis C; The presence of respiratory, cardio-vascular insufficiency, impaired liver and kidney function, established during a physical examination at visit number 1; Pronounced congenital defects or serious chronic diseases in the acute stage, including any clinically important exacerbation of chronic diseases of the liver, kidney, cardiovascular, nervous system, mental diseases or metabolic disorders, confirmed by the history or objective examination (pulmonary: cystic fibrosis, lung abscess, empyema, active tuberculosis; extra-pulmonary: congestive heart failure, malabsorption, chronic renal and hepatic failure, cirrhosis, malignancy, immunodeficiency, cirrhosis of the liver); Severe allergic reactions in anamnesis of autoimmune disease; The presence of acute infectious and/or communicable illnesses within 1 month prior to study; History of chronic alcohol abuse and/or drug use; Exacerbation of chronic diseases; Breastfeeding; Pregnancy; Participation in any other clinical study within the last 3 months.", "candidate_expression": "((Breastfeeding) AND (Exacerbation) AND (HIV infection) AND (Participation in clinical study) AND (Pregnancy) AND (Prolonged use) AND (Severe) AND (Vaccination) AND (active) AND (acute) AND (acute stage) AND (alcohol abuse) AND (allergic reactions) AND (any other) AND (at visit number 1) AND (blood transfusion) AND (cardio-vascular insufficiency) AND (chronic) AND (chronic diseases) AND (cirrhosis) AND (cirrhosis of the liver) AND (clinically important) AND (communicable illnesses) AND (congenital defects) AND (congestive heart failure) AND (cystic fibrosis) AND (diseases of the cardiovascular system) AND (diseases of the kidney) AND (diseases of the liver) AND (diseases of the nervous system) AND (drug use) AND (empyema) AND (exacerbation) AND (hepatic failure) AND (immunodeficiency) AND (immunodeficient condition) AND (immunosuppressants) AND (immunosuppressive condition) AND (immunosuppressive drugs) AND (impaired kidney function) AND (impaired liver) AND (infectious illnesses) AND (lung abscess) AND (malabsorption) AND (malignancy) AND (mental diseases) AND (metabolic disorders) AND (more than 14 days) AND (other) AND (pneumococcal infection) AND (positive) AND (preparations of immune globulin) AND (reaction for HIV infection) AND (reaction for hepatitis C) AND (reaction for viral hepatitis B) AND (renal failure) AND (respiratory insufficiency) AND (serious) AND (study) AND (tuberculosis) AND (within 1 month prior to study) AND (within 6 months prior to the start of the study) AND (within last three months prior to clinical studies) AND (within the last 3 months))"}
{"candidate_id": "LLM04368", "doc_id": "NCT01815580_inc", "case_bucket": "or", "source_criterion": "Adult men who have sex with men, and transgender women Unaware of HIV status at enrollment in follow-up cohort High risk for HIV infection Willing to test for HIV No prior ART, including prior administration of pre- and post-exposure prophylaxis in the last 30 days Willing to provide informed consent", "candidate_expression": "((ART prior) AND (Adult) AND (HIV infection High risk for) AND (HIV status Unaware at enrollment in follow-up cohort) AND (Unaware of HIV status) AND (administration prior in the last 30 days) AND (informed consent Willing to provide) AND (men who have sex with men) AND (post-exposure prophylaxis) AND (pre- exposure prophylaxis) AND (test for HIV Willing to) AND (transgender women))"}
{"candidate_id": "LLM04369", "doc_id": "NCT03115151_exc", "case_bucket": "or", "source_criterion": "Baseline cognitive deficits sufficient to make objective pain self-assessments unreliable in the estimation of the Study Investigators. Immunocompromised subject Coagulopathy Severe liver and renal dysfunction Preoperative neurological deficits The dura damage during surgery Inability to follow directions or comprehend the English language. Females who are pregnant as determined by positive pregnancy test on or before the day of surgery. Prisoners. Patient refusal to provide informed consent. Allergy to amide local anesthetics (lidocaine, bupivacaine, ropivacaine) or opioid (fentanyl).", "candidate_expression": "((Allergy) AND (Baseline cognitive deficits sufficient to make objective pain self-assessments unreliable in the estimation of the Study Investigators.) AND (Coagulopathy) AND (Females who are pregnant as determined by positive pregnancy test on or before the day of surgery) AND (Immunocompromised) AND (Inability to follow directions or comprehend the English language) AND (Patient refusal to provide informed consent) AND (Prisoners) AND (amide local anesthetics) AND (bupivacaine) AND (fentanyl) AND (lidocaine) AND (liver dysfunction) AND (neurological deficits Preoperative) AND (opioid) AND (renal dysfunction) AND (ropivacaine) AND (surgery dura damage))"}
{"candidate_id": "LLM04370", "doc_id": "NCT02779374_exc", "case_bucket": "or", "source_criterion": "Abnormal karyotype Previous pelvic or abdominal radiotherapy Previous surgical management of ovarian pathology Chronic disease: renal, liver, cardiac, malignancy", "candidate_expression": "((Abnormal karyotype) AND (Chronic disease) AND (ovarian pathology) AND (surgical management Previous) AND ((cardiac malignancy) OR (liver malignancy) OR (renal malignancy)) AND ((abdominal radiotherapy) OR (pelvic radiotherapy)))"}
{"candidate_id": "LLM04371", "doc_id": "NCT00426751_exc", "case_bucket": "or", "source_criterion": "Subjects not able to give informed consent Left Bundle Branch Block Thrombolytic therapy within 24 hours before randomization Oral anticoagulation with International Normalized Ratio (INR) > 2 Known platelets < 100.000/µl or known hemorrhagic diathesis Stroke or Transient Ischemic Attack (TIA) within the past 6 months or any permanent residual neurological defect Evidence of an active gastrointestinal or urogenital bleeding Major surgery within 6 weeks History of allergic reaction to abciximab or eptifibatide or any component used in the study (including contrast media) Known severe renal (creatinine clearance <30ml/min) or hepatic insufficiency as well as Alanine transaminase (ALT)/aspartate transaminase (AST) elevations = 3xUpper limit normal (ULN); isolated AST-elevation is not considered an exclusion criteria from study participation Severe concomitant disease with life expectation < 1 year Subject has participated in any study using an investigational drug or device within 30 days or within 5 half-lives of the investigational drug (whichever is longer) of entry into this study. Subjects who will be inaccessible due to geographic or social factors during treatment or follow-up In France, a subject is neither affiliated with nor a beneficiary of a social security category.", "candidate_expression": "((Alanine transaminase (ALT) elevations) AND (History) AND (International Normalized Ratio (INR) > 2) AND (Left Bundle Branch Block) AND (Major surgery within 6 weeks) AND (Oral anticoagulation) AND (Severe disease concomitant) AND (Thrombolytic therapy within 24 hours before randomization) AND (allergic reaction) AND (aspartate transaminase (AST) elevations 3xUpper limit normal (ULN)) AND (creatinine clearance <30ml/min) AND (inaccessible during treatment or follow-up treatment follow-up) AND (participated in any study) AND (residual neurological defect) AND NOT (give informed consent able to) AND ((Stroke) OR (Transient Ischemic Attack (TIA))) AND ((gastrointestinal bleeding) OR (urogenital bleeding)) AND ((abciximab) OR (component used in the study) OR (contrast media) OR (eptifibatide)) AND ((hepatic insufficiency severe) OR (renal insufficiency severe)) AND ((< 1 year) OR (life expectation)) AND ((device) OR (investigational drug)) AND ((of the investigational drug within 30 days) OR (within 5 half-lives of the investigational drug)) AND ((< 100.000/µl) OR (hemorrhagic diathesis) OR (platelets)))"}
{"candidate_id": "LLM04372", "doc_id": "NCT03199560_inc", "case_bucket": "or", "source_criterion": "Women above 18 years of age with biopsy proven, clinically stage 1 or 2 breast cancer who will be undergoing partial mastectomy with SLNBx at Memorial Health", "candidate_expression": "((SLNBx) AND (Women) AND (above 18 years) AND (age) AND (at Memorial Health) AND (biopsy) AND (breast cancer) AND (partial mastectomy) AND (stage 1) AND (stage 2) AND (will be undergoing))"}
{"candidate_id": "LLM04373", "doc_id": "NCT02704234_inc", "case_bucket": "other", "source_criterion": "women previously diagnosed with generalized vulvodynia women previously diagnosed with localized vestibulodynia,", "candidate_expression": "((generalized vulvodynia) AND (localized vestibulodynia) AND (women))"}
{"candidate_id": "LLM04374", "doc_id": "NCT02590653_inc", "case_bucket": "other", "source_criterion": "Signed Informed Consent Form Patients having physical and mental ability to participate in the study Patients of both sexes aged 35 to 65 years Presence of documented ST-elevation myocardial infarction confirmed by ECG, as well as troponin I and CK-MB levels. Presence of hemodynamically relevant stenosis of one artery (i.e., the infarct-related artery) confirmed by coronary angiography (CAG), with the occlusion of other arteries not exceeding 30%.", "candidate_expression": "((CAG) AND (CK-MB) AND (ECG) AND (Patients having physical and mental ability to participate in the study) AND (ST-elevation myocardial infarction) AND (Signed Informed Consent Form) AND (aged 35 to 65 years) AND (coronary angiography) AND (infarct-related artery) AND (occlusion of other arteries not exceeding 30%) AND (sexes both) AND (stenosis of artery hemodynamically relevant one) AND (troponin I))"}
{"candidate_id": "LLM04375", "doc_id": "NCT02056301_inc", "case_bucket": "other", "source_criterion": "Patients age 8- 18 years 2) Patients undergoing minimally invasive pectus excavatum repair via Nuss procedure 3) American Society of Anesthesiology Status I-III", "candidate_expression": "((American Society of Anesthesiology Status I-III) AND (age 8- 18 years) AND (minimally invasive pectus excavatum repair Nuss procedure))"}
```
