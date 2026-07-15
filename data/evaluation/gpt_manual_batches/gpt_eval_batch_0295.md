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
{"candidate_id": "LLM07351", "doc_id": "NCT03397914_exc", "case_bucket": "or", "source_criterion": "Age less than one year or over 18 years Patients with renal impairment Colistin use less than 72 hours", "candidate_expression": "((Age) AND (Colistin) AND (less than 72 hours) AND (renal impairment) AND ((less than one year) OR (over 18 years)))"}
{"candidate_id": "LLM07352", "doc_id": "NCT02137538_exc", "case_bucket": "other", "source_criterion": "Bone age reading more than 14.0 years Follicle stimulating hormone > 20 IU/L", "candidate_expression": "((> 20 IU/L) AND (Bone age) AND (Follicle stimulating hormone) AND (more than 14.0 years))"}
{"candidate_id": "LLM07353", "doc_id": "NCT02321839_exc", "case_bucket": "or", "source_criterion": "Total lesion area of >12 DA or >30.5 mm2 The existence of subretinal hemorrhage area constituting =50% of total lesion area The existence of scar or fibrosis area constituting =50% of total lesion area The existence of RPE tear Prior treatment for wet AMD History of vitrectomy surgery, submacular surgery, or other surgical intervention for AMD The pregnant or lactating woman", "candidate_expression": "((=50% of total lesion area) AND (AMD) AND (Prior) AND (RPE tear) AND (Total lesion area) AND (other) AND (subretinal hemorrhage area) AND (treatment) AND (woman) AND ((submacular surgery) OR (surgical intervention) OR (vitrectomy surgery)) AND ((>12 DA) OR (>30.5 mm2)) AND ((lactating) OR (pregnant)) AND ((fibrosis area) OR (scar area)))"}
{"candidate_id": "LLM07354", "doc_id": "NCT02940912_inc", "case_bucket": "or", "source_criterion": "Idiopathic Parkinson's disease ( Hughes AJ et al. 2001) Patients with motor fluctuations Chronic Insomnia disorder criteria according to the criteria of DMS- V ( American Psychiatric Association, 2013) and insomnia severity index > 15 Able to use independently the device required for treatment by apomorphine Collection of written informed consent (legal obligation for any project under the public health law , bioethics laws and / or CNIL) . Affiliate to social security or beneficiary of such a regime", "candidate_expression": "((> 15) AND (Chronic Insomnia disorder) AND (Idiopathic) AND (Parkinson's disease) AND (apomorphine) AND (criteria of DMS- V) AND (device) AND (insomnia severity index) AND (motor fluctuations) AND ((Affiliate to social security) OR (social security beneficiary)))"}
{"candidate_id": "LLM07355", "doc_id": "NCT00183885_exc", "case_bucket": "or", "source_criterion": "Patients who have received prior chemotherapy for unresectable disease Patients with any active or uncontrolled infection, including known HIV infection. (Patients with active hepatitis B will be placed on lamivudine. Patients with active hepatitis C will be eligible if liver tests qualify (5.1.9) Patients with psychiatric disorders that would interfere with consent or follow-up. Pregnant or lactating women. Men and women of reproductive potential may not participate unless they have agreed to use an effective contraceptive method. Patients with any other severe concurrent disease, which in the judgment of the investigator, would make the patient inappropriate for entry into this study.", "candidate_expression": "((HIV infection) AND (Pregnant) AND (chemotherapy) AND (concurrent disease severe entry into this study) AND (effective contraceptive method) AND (hepatitis B active) AND (hepatitis C active) AND (infection uncontrolled) AND (lactating) AND (lamivudine) AND (liver tests qualify) AND (psychiatric disorders interfere with follow-up interfere with consent) AND (reproductive potential) AND (unresectable disease active) AND (women))"}
{"candidate_id": "LLM07356", "doc_id": "NCT02414399_exc", "case_bucket": "other", "source_criterion": "Contraindication to azithromycin use and other prophylactic antibiotic use", "candidate_expression": "((Contraindication) AND (azithromycin) AND (prophylactic antibiotic use other))"}
{"candidate_id": "LLM07357", "doc_id": "NCT02816164_inc", "case_bucket": "or", "source_criterion": "Histologically confirmed primary breast cancer Planned to start docetaxel component of FEC-D or AC-D, or first cycle of; dose-dense AC-T, TC, FEC-D or TAC chemotherapy =19 years of age Able to provide verbal consent", "candidate_expression": "((Able to provide verbal consent) AND (Histologically) AND (age =19 years) AND (primary breast cancer Histologically confirmed) AND ((FEC-D) OR (TAC chemotherapy) OR (TC) OR (dose-dense AC-T)) AND ((docetaxel) OR (first cycle of)) AND ((AC-D) OR (FEC-D)))"}
{"candidate_id": "LLM07358", "doc_id": "NCT00954850_exc", "case_bucket": "or", "source_criterion": "Malignancy and other significant medical conditions that will impact follow up within this program. Those less than 18 years of age. Concomitant interstitial lung disease, sarcoidosis, other significant lung disease. Those who have had a transplant. Significant travel with work. Unable to make appointments (every three to six months over 2 years). Those residing in another country or planned absence for more than one month.", "candidate_expression": "((Unable to make appointments (every three to six months over 2 years).) AND (age less than 18 years) AND (transplant) AND ((Malignancy) OR (medical conditions significant)) AND ((interstitial lung disease) OR (lung disease) OR (sarcoidosis)))"}
{"candidate_id": "LLM07359", "doc_id": "NCT03280017_inc", "case_bucket": "other", "source_criterion": "American Society of Anesthesiologist physical status 1-3 Scheduled for elective video-assisted thoracic surgery Able to operate a patient-controlled analgesia device (PCA)", "candidate_expression": "((1-3) AND (American Society of Anesthesiologist physical status) AND (PCA) AND (Scheduled for) AND (elective) AND (patient-controlled analgesia device) AND (video-assisted thoracic surgery))"}
{"candidate_id": "LLM07360", "doc_id": "NCT03250507_exc", "case_bucket": "or", "source_criterion": "Patient with a chronic pain condition, major unexpected surgical complication, unexpected prolonged intubation, patient refusal, local anesthetic allergy, any contraindication to regional anesthesia, greater than 2 attempts by resident and greater than 1 attempt by staff anesthesiologist for TAP block.", "candidate_expression": "((TAP block) AND (allergy) AND (anesthesiologist greater than 1) AND (chronic pain condition) AND (contraindication) AND (intubation unexpected prolonged) AND (local anesthetic) AND (patient refusal) AND (regional anesthesia) AND (resident greater than 2) AND (unexpected surgical complication major))"}
{"candidate_id": "LLM07361", "doc_id": "NCT00954850_exc", "case_bucket": "or", "source_criterion": "Malignancy and other significant medical conditions that will impact follow up within this program. Those less than 18 years of age. Concomitant interstitial lung disease, sarcoidosis, other significant lung disease. Those who have had a transplant. Significant travel with work. Unable to make appointments (every three to six months over 2 years). Those residing in another country or planned absence for more than one month.", "candidate_expression": "((Concomitant) AND (Malignancy) AND (Unable to make appointments (every three to six months over 2 years).) AND (age) AND (interstitial lung disease) AND (less than 18 years) AND (lung disease) AND (medical conditions) AND (sarcoidosis) AND (significant) AND (transplant))"}
{"candidate_id": "LLM07362", "doc_id": "NCT02225548_inc", "case_bucket": "other", "source_criterion": "Diagnosis of idiopathic Parkinson's disease that is optimally treated (motor fluctuations <20% of subject's awake time). Subjects may be on levodopa therapy but must be stable at the time of entry into the study Sexually active (i.e. =1 attempt/week) males, 40 - 64 years of age (inclusive) at time of screening Diagnosis of moderate erectile dysfunction (defined according to the NIH Consensus Development Panel on Impotence) for more than 6 months and demonstrating and incomplete response to tadalafil alone Subject demonstrating an IIEF-5 drug-free baseline score that is = 10 but = 16, and an IIEF-5 tadalafil-alone baseline score that is = 18 Subject in a stable heterosexual relationship for at least 6 months. (2) Subject motivated to seek treatment for erectile dysfunction. Subject with a total serum testosterone level = 300 ng/dL, with or without supplementation Hoehn and Yahr Scale score of 1 - 3 Patient able to consent and comply with protocol requirements", "candidate_expression": "((Hoehn and Yahr Scale score 1 - 3) AND (IIEF-5 drug-free baseline score = 10 but = 16) AND (IIEF-5 tadalafil-alone baseline score = 18) AND (Patient able to consent and comply with protocol requirements) AND (Sexually active =1 attempt/week) AND (Subject motivated to seek treatment for erectile dysfunction) AND (age 40 - 64 years) AND (erectile dysfunction) AND (erectile dysfunction moderate for more than 6 months) AND (heterosexual relationship stable at least 6 months) AND (idiopathic Parkinson's disease treated) AND (males) AND (motor fluctuations <20% of subject's awake time) AND (response incomplete) AND (tadalafil) AND (total serum testosterone level = 300 ng/dL) AND (treatment))"}
{"candidate_id": "LLM07363", "doc_id": "NCT03106389_inc", "case_bucket": "other", "source_criterion": "NA", "candidate_expression": "(EMPTY)"}
{"candidate_id": "LLM07364", "doc_id": "NCT03465397_exc", "case_bucket": "or", "source_criterion": "Patients with a calculated PRA higher than 0% per solid phase and / or anti-HLA class I and / or class II antibodies detectable by single antigen test (Luminex®). Positive result of Cross Match. Patients who receive a graft from a cadaver donor. Identical HLA patients Patients who have undergone a previous solid organ transplant (including kidney transplant) or who are going to receive another solid organ transplant concomitantly. Glomerular primary focal and segmental sclerosis Atypical hemolytic uremic syndrome (aHUS) / thrombotic thrombocytopenic purpura syndrome. Patients with chronic infection with Hepatitis B virus (HBV) and / or active infection with Hepatitis C virus (positive PCR result) at the time of transplant. Patients with infection with the known Human Immunodeficiency Virus (HIV). Patients with active systemic infection that requires the continued administration of antibiotics. Patients with any neoplasm except localized skin cancer and who is receiving adequate treatment. Patients with severe anemia (hemoglobin <6g / dl), leukopenia (WBC <2500 / mm3) and / or thrombocytopenia (platelets <80,000 / mm3). Patients who are hemodynamically unstable even if they have hemoglobin levels> 6g / dL. Patients with intestinal pathology or severe diarrhea that may decrease absorption according to medical criteria. Patients with known hypersensitivity to any of the drugs used in this study. Patients who have received any investigational drug in the 30 days prior to their inclusion in this study. Potentially fertile women who do not agree to use reliable contraceptive measures during the trial, who are pregnant, breastfeeding or who present a positive pregnancy test at the time of their inclusion in the study. Patients who are legally detained in an official institution.", "candidate_expression": "((<2500 / mm3) AND (<6g / dl) AND (<80,000 / mm3) AND (> 6g / dL) AND (Atypical hemolytic uremic syndrome (aHUS)) AND (Cross Match) AND (Glomerular primary focal sclerosis) AND (Glomerular segmental sclerosis) AND (Hepatitis B virus (HBV)) AND (Hepatitis C virus) AND (Human Immunodeficiency Virus (HIV)) AND (Identical HLA) AND (Luminex) AND (PCR result) AND (Patients who have received any investigational drug in the 30 days prior to their inclusion in this study.) AND (Positive) AND (Potentially fertile women who do not agree to use reliable contraceptive measures during the trial, who are pregnant, breastfeeding or who present a positive pregnancy test at the time of their inclusion in the study.) AND (WBC) AND (active) AND (anemia) AND (another) AND (anti-HLA class I) AND (anti-HLA class II) AND (antibiotics) AND (at the time of transplant) AND (calculated PRA) AND (chronic) AND (concomitantly) AND (continued administration) AND (drugs used in this study) AND (except) AND (graft from a cadaver donor) AND (hemodynamically unstable) AND (hemoglobin) AND (hemoglobin levels) AND (higher than 0% per solid phase) AND (hypersensitivity) AND (intestinal pathology) AND (kidney transplant) AND (legally detained) AND (leukopenia) AND (localized skin cancer) AND (may decrease absorption) AND (neoplasm) AND (official institution) AND (platelets) AND (positive) AND (previous) AND (severe) AND (severe diarrhea) AND (single antigen test) AND (solid organ transplant) AND (systemic infection) AND (thrombocytopenia) AND (thrombotic thrombocytopenic purpura syndrome))"}
{"candidate_id": "LLM07365", "doc_id": "NCT03465397_exc", "case_bucket": "or", "source_criterion": "Patients with a calculated PRA higher than 0% per solid phase and / or anti-HLA class I and / or class II antibodies detectable by single antigen test (Luminex®). Positive result of Cross Match. Patients who receive a graft from a cadaver donor. Identical HLA patients Patients who have undergone a previous solid organ transplant (including kidney transplant) or who are going to receive another solid organ transplant concomitantly. Glomerular primary focal and segmental sclerosis Atypical hemolytic uremic syndrome (aHUS) / thrombotic thrombocytopenic purpura syndrome. Patients with chronic infection with Hepatitis B virus (HBV) and / or active infection with Hepatitis C virus (positive PCR result) at the time of transplant. Patients with infection with the known Human Immunodeficiency Virus (HIV). Patients with active systemic infection that requires the continued administration of antibiotics. Patients with any neoplasm except localized skin cancer and who is receiving adequate treatment. Patients with severe anemia (hemoglobin <6g / dl), leukopenia (WBC <2500 / mm3) and / or thrombocytopenia (platelets <80,000 / mm3). Patients who are hemodynamically unstable even if they have hemoglobin levels> 6g / dL. Patients with intestinal pathology or severe diarrhea that may decrease absorption according to medical criteria. Patients with known hypersensitivity to any of the drugs used in this study. Patients who have received any investigational drug in the 30 days prior to their inclusion in this study. Potentially fertile women who do not agree to use reliable contraceptive measures during the trial, who are pregnant, breastfeeding or who present a positive pregnancy test at the time of their inclusion in the study. Patients who are legally detained in an official institution.", "candidate_expression": "((Cross Match Positive) AND (Human Immunodeficiency Virus (HIV)) AND (Identical HLA) AND (Luminex) AND (PCR result positive) AND (Patients who have received any investigational drug in the 30 days prior to their inclusion in this study.) AND (Potentially fertile women who do not agree to use reliable contraceptive measures during the trial, who are pregnant, breastfeeding or who present a positive pregnancy test at the time of their inclusion in the study.) AND (WBC <2500 / mm3) AND (anemia severe) AND (antibiotics continued administration) AND (calculated PRA higher than 0% per solid phase) AND (drugs used in this study) AND (graft from a cadaver donor) AND (hemodynamically unstable) AND (hemoglobin <6g / dl) AND (hemoglobin levels > 6g / dL) AND (hypersensitivity) AND (kidney transplant) AND (legally detained) AND (neoplasm) AND (official institution) AND (platelets <80,000 / mm3) AND (single antigen test) AND (solid organ transplant another concomitantly) AND (solid organ transplant previous) AND (systemic infection active) AND NOT (localized skin cancer) AND ((Glomerular primary focal sclerosis) OR (Glomerular segmental sclerosis)) AND ((Atypical hemolytic uremic syndrome (aHUS)) OR (thrombotic thrombocytopenic purpura syndrome)) AND ((Hepatitis B virus (HBV) chronic) OR (Hepatitis C virus active)) AND ((anti-HLA class I) OR (anti-HLA class II)) AND ((leukopenia) OR (thrombocytopenia)) AND ((intestinal pathology) OR (severe diarrhea)))"}
{"candidate_id": "LLM07366", "doc_id": "NCT02519777_inc", "case_bucket": "or", "source_criterion": "a licensed rapid HIV test or HIV enzyme or chemiluminescence immunoassay (E/CIA) test kit at any time prior to study entry and confirmed by a licensed Western blot or a second antibody test by a method other than the initial rapid HIV and/or E/CIA, or by HIV-1 antigen or plasma HIV-1 RNA viral load. NOTE: The term \"licensed\" refers to a United States Food and Drug Administration (FDA)-approved kit, which is required for all IND studies, or for sites located in countries other than the United States, a kit that has been certified or licensed by an oversight body within that country and validated internally. Non-US sites are encouraged to use US FDA-approved methods for IND studies. WHO (World Health Organization) and CDC (Centers for Disease Control and Prevention) guidelines mandate that confirmation of the initial test result must use a test that is different from the one used for the initial assessment. A reactive initial rapid test should be confirmed by either another type of rapid assay or an E/CIA that is based on a different antigen preparation and/or different test principle (eg, indirect versus competitive), or a Western blot or a plasma HIV-1 RNA. OR Documentation of HIV diagnosis in the medical record by a healthcare provider. Tenofovir disoproxil fumarate (TDF) to tenofovir alafenamide fumarate (TAF)/TAF-containing fixed-dose combination regimens Ritonavir (RTV) to cobicistat (COBI)/COBI-containing fixed-dose combination regimens TDF to TAF/TAF-containing fixed-dose combination regimens RTV to COBI/COBI-containing fixed-dose combination regimens HIV-1 plasma RNA less than 50 copies/mL obtained within 90 days prior to study entry by any FDA-approved assay at any United States laboratory that has a Clinical Laboratory Improvement Amendments (CLIA) certification or its equivalent, or at any network-approved non-US laboratory that operates in accordance with Good Clinical Laboratory Practices (GCLP) and participates in appropriate external quality assurance programs. No more than one HIV-1 plasma RNA greater than or equal to 50 and less than 200 copies/mL (only one \"blip\") in the past 6 months with a subsequent HIV-1 plasma RNA less than 50 copies/mL. NOTE: There should be no plasma HIV-1 RNA greater than 200 copies/mL within the 6 months prior to study entry. HAND diagnosis (ANI, MND, or HAD) within 60 days prior to study entry. HAND is defined as at least mild impairment on neurocognitive testing (more than one standard deviation below appropriate normative data in two domains of functioning) and no severely confounding factors. Absolute neutrophil count (ANC) greater than or equal to 500/mm^3 Hemoglobin greater than or equal to 7.5 g/dL Platelet count greater than or equal to 40,000/mm^3 Creatinine less than or equal to 2.0 x upper limit of normal (ULN) Aspartate transaminase (AST) less than or equal to 5 x ULN Alanine transaminase (ALT) less than 3 x ULN Alkaline phosphatase less than or equal to 5 x ULN Total bilirubin less than 1.5 x ULN. NOTE: If the potential participant is taking an indinavir (IDV)- or atazanavir (ATV)-containing regimen at the time of screening, total bilirubin less than or equal to 5 x ULN is acceptable. Creatinine clearance (CrCl) greater than or equal to 60 mL/min, either measured or estimated by Cockcroft-Gault equation. NOTE: A calculator for estimating the CrCl can be found at www.fstrf.org/ACTG/ccc.html Females of reproductive potential (women who have not been post-menopausal for at least 24 consecutive months, ie, who have had menses within the preceding 24 months, or women who have not undergone surgical sterilization, hysterectomy or bilateral salpingectomy or bilateral oophorectomy or tubal ligation) must have a negative serum or urine pregnancy test by any US clinic or laboratory that has a CLIA certification or its equivalent, or is using a point of care (POC) / CLIA-waived test, or at any network-approved non-US laboratory or clinic that operates in accordance with GCLP and participates in appropriate external quality assurance programs within 48 hours prior to study entry Females of reproductive potential must agree not to participate in the conception process (ie, active attempt to become pregnant, in vitro fertilization), and if participating in sexual activity that could lead to pregnancy, must use at least one reliable form of contraception. Female participants must use contraceptives while receiving study treatment and for 6 weeks after stopping study treatment. More information on this criterion is available in the protocol. Men and women 18 years of age and older who are able to complete the neuropsychological tests Ability and willingness of participant or a legally authorized representative (see protocol for more information) to provide informed consent Ability and willingness to take oral study medications", "candidate_expression": "((ANI) AND (Ability and willingness of participant or a legally authorized representative (see protocol for more information) to provide informed consent) AND (Ability and willingness to take oral study medications) AND (Absolute neutrophil count (ANC) greater than or equal to 500/mm^3) AND (Alanine transaminase (ALT) less than 3 x ULN) AND (Alkaline phosphatase less than or equal to 5 x ULN) AND (Aspartate transaminase (AST) less than or equal to 5 x ULN) AND (COBI) AND (COBI-containing fixed-dose combination regimens) AND (Cockcroft-Gault equation) AND (Creatinine clearance (CrCl) greater than or equal to 60 mL/min) AND (Creatinine less than or equal to 2.0 x upper limit of normal (ULN)) AND (Females of reproductive potential (women who have not been post-menopausal for at least 24 consecutive months, ie, who have had menses within the preceding 24 months, or women who have not undergone surgical sterilization, hysterectomy or bilateral salpingectomy or bilateral oophorectomy or tubal ligation) must have a negative serum or urine pregnancy test by any US clinic or laboratory that has a CLIA certification or its equivalent, or is using a point of care (POC) / CLIA-waived test, or at any network-approved non-US laboratory or clinic that operates in accordance with GCLP and participates in appropriate external quality assurance programs within 48 hours prior to study entry) AND (Females of reproductive potential must agree not to participate in the conception process (ie, active attempt to become pregnant, in vitro fertilization), and if participating in sexual activity that could lead to pregnancy, must use at least one reliable form of contraception. Female participants must use contraceptives while receiving study treatment and for 6 weeks after stopping study treatment. More information on this criterion is available in the protocol.) AND (HAD) AND (HAND within 60 days prior to study entry) AND (HIV diagnosis) AND (HIV-1 plasma RNA No more than one greater than or equal to 50 and less than 200 copies/mL in the past 6 months) AND (HIV-1 plasma RNA less than 50 copies/mL within 90 days prior to study entry) AND (HIV-1 plasma RNA subsequent less than 50 copies/mL) AND (Hemoglobin greater than or equal to 7.5 g/dL) AND (MND) AND (Men) AND (Platelet count greater than or equal to 40,000/mm^3) AND (RTV) AND (Ritonavir (RTV)) AND (TAF) AND (TAF-containing fixed-dose combination regimens) AND (TDF) AND (Tenofovir disoproxil fumarate (TDF)) AND (Total bilirubin less than 1.5 x ULN) AND (age 18 years and older) AND (atazanavir (ATV)) AND (cobicistat (COBI)) AND (indinavir (IDV)) AND (neurocognitive testing in two domains of functioning impairment more than one standard deviation below appropriate normative data) AND (neuropsychological tests able to complete) AND (regimen at the time of screening) AND (tenofovir alafenamide fumarate (TAF)) AND (total bilirubin less than or equal to 5 x ULN) AND (women) AND NOT (plasma HIV-1 RNA greater than 200 copies/mL within the 6 months prior to study entry) AND NOT (severely confounding factors))"}
{"candidate_id": "LLM07367", "doc_id": "NCT00917891_inc", "case_bucket": "or", "source_criterion": "1. Women 18 to 40 years of age inclusive who can give written informed consent 2. Available for all visits and consent to follow all procedures scheduled for the study 3. Agree to daily application of gel and monitoring as per Daily Monitored Adherence (DMA) method 4. Healthy and self-reported sexually active 5. HIV-negative as determined by a HIV rapid test at time of enrollment 6. On a stable form of contraception and willing to continue on this stable method of contraception, OR, Have undergone surgical sterilisation at least 3 months prior to enrollment 7. In the absence of the use of exogenous hormone(s), have a self-reported regular menstrual cycle defined as having a minimum of 21 days and a maximum of 36 days between menses 8. Upon pelvic/speculum examination and colposcopy at the time of enrollment, the cervix and vagina appear normal as determined by the investigator 9. Asymptomatic for genital infections at the time of enrollment 10. Willing to refrain from use of vaginal products or objects within 14 days prior to enrollment and for the duration of the study 11. Willing to answer acceptability and adherence questionnaires throughout the study 12. Willing to refrain from participation in any other research study for the duration of this study 13. Willing to provide adequate locator information for study retention purposes and be reachable per local standard procedures", "candidate_expression": "((18 to 40 years) AND (Agree to daily application of gel and monitoring as per Daily Monitored Adherence (DMA) method) AND (Asymptomatic) AND (Available for all visits and consent to follow all procedures scheduled for the study) AND (HIV) AND (HIV rapid test) AND (HIV-negative) AND (Healthy) AND (On a stable form of contraception and willing to continue on this stable method of contraception, OR, Have undergone surgical sterilisation at least 3 months prior to enrollment) AND (Willing) AND (Willing to answer acceptability and adherence questionnaires throughout the study) AND (Willing to provide adequate locator information for study retention purposes and be reachable per local standard procedures) AND (Willing to refrain from participation in any other research study for the duration of this study) AND (Women) AND (absence) AND (acceptability questionnaires) AND (adherence questionnaires) AND (age) AND (as determined by the investigator) AND (at the time of enrollment) AND (at time of enrollment) AND (can give written informed consent) AND (cervix) AND (daily) AND (enrollment) AND (exogenous hormone) AND (for the duration of the study) AND (gel) AND (genital infections) AND (maximum of 36 days) AND (menstrual cycle) AND (minimum of 21 days) AND (monitoring) AND (negative) AND (normal) AND (refrain) AND (regular) AND (regular menstrual cycle) AND (self-reported) AND (sexually active) AND (the study) AND (throughout the study) AND (time of enrollment) AND (vagina) AND (within 14 days prior to enrollment) AND ((colposcopy) OR (pelvic examination) OR (speculum examination)) AND ((objects vaginal) OR (vaginal products)))"}
{"candidate_id": "LLM07368", "doc_id": "NCT03325023_exc", "case_bucket": "or", "source_criterion": "Ovarian cancer, adrenal gland tumor, endometrial cancer, cervical cancer, breast cancer Congenital adrenal hyperplasia (17-OH-progesterone> 2.5 ng / mL) Clinically diagnosed Cushing's disease, acromegaly, gigantism Type I or II diabetes Unexplained bleeding from the genital tract Hormone treatment within the last 2 months", "candidate_expression": "((17-OH-progesterone) AND (> 2.5 ng / mL) AND (Clinically diagnosed) AND (Congenital adrenal hyperplasia) AND (Hormone) AND (Hormone treatment) AND (Unexplained bleeding) AND (genital tract) AND (within the last 2 months) AND ((Ovarian cancer) OR (adrenal gland tumor) OR (breast cancer) OR (cervical cancer) OR (endometrial cancer)) AND ((Cushing's disease) OR (acromegaly) OR (gigantism)) AND ((Type I diabetes) OR (Type II diabetes)))"}
{"candidate_id": "LLM07369", "doc_id": "NCT01912651_exc", "case_bucket": "or", "source_criterion": "current or recent (within one week of surgery) systemic antibiotic use, intolerance to both clindamycin and cephalexin, discovery of a persistent cutaneous malignancy at the site of the defect following the reconstructive procedure and previous reconstruction at the site of the skin/soft-tissue defect.", "candidate_expression": "((cephalexin) AND (clindamycin) AND (reconstructive procedure the reconstructive procedure) AND (within one week of surgery) AND ((antibiotic) OR (intolerance) OR (persistent cutaneous malignancy site of the defect following the reconstructive procedure)) AND ((current) OR (recent)))"}
{"candidate_id": "LLM07370", "doc_id": "NCT02689089_inc", "case_bucket": "or", "source_criterion": "Males or non-pregnant, non-nursing females between the ages of 2-65 years LTBI diagnosis as per Canadian TB Standards using either the Tuberculin Skin Test (TST) or the Interferon Gamma Release Assay (IGRA) Children 2-5 years with negative TSTs who have been in close contact with a case of active TB disease recently Able and willing to provide fully informed consent or parent/guardian able to provide consent", "candidate_expression": "((2-5) AND (2-65 years) AND (Able and willing to provide fully informed consent or parent/guardian able to provide consent) AND (Children) AND (IGRA) AND (LTBI) AND (TST) AND (TSTs) AND (ages) AND (negative) AND (non-pregnant, non-nursing) AND (years) AND ((Males) OR (females)) AND ((Interferon Gamma Release Assay) OR (Tuberculin Skin Test)))"}
{"candidate_id": "LLM07371", "doc_id": "NCT03372304_inc", "case_bucket": "other", "source_criterion": "American Society of Anesthesiologists Classification I-III Normal cognitive function in order to sign written, informed consent and to understand trial protocol Agreement to the trial protocol, including the randomized manner", "candidate_expression": "((Agreement to the trial protocol, including the randomized manner) AND (American Society of Anesthesiologists Classification) AND (I-III) AND (ormal cognitive function in order to sign written, informed consent and to understand trial protoco))"}
{"candidate_id": "LLM07372", "doc_id": "NCT01314898_exc", "case_bucket": "or", "source_criterion": "Subjects with a supine BP >140 mm Hg systolic or >90 mm Hg diastolic or <100 mm Hg systolic or <60 mm Hg diastolic based on the average of the triplicate Serum potassium >=5.1 mmol/L or <3.5 mmol/L at screening, confirmed by a single repeat if deemed necessary. Estimated GFR <60 mL/min/1.73 m2 using the Cockcroft-Gault formula measurement of the individual parameters following at least 5 minutes of rest at Screening.", "candidate_expression": "((<100 mm Hg systolic) AND (<3.5 mmol/L) AND (<60 mL/min/1.73 m2) AND (<60 mm Hg diastolic) AND (>140 mm Hg systolic) AND (>90 mm Hg diastolic) AND (>=5.1 mmol/L) AND (Cockcroft-Gault formula) AND (Estimated GFR) AND (Serum potassium) AND (at screening) AND (supine BP))"}
{"candidate_id": "LLM07373", "doc_id": "NCT03351972_inc", "case_bucket": "other", "source_criterion": "Adult outpatients (18 years or older) routinely referred for small bowel video capsule endoscopy (CE)", "candidate_expression": "((18 years or older) AND (Adult) AND (outpatients) AND (routinely referred) AND (small bowel video capsule endoscopy))"}
{"candidate_id": "LLM07374", "doc_id": "NCT02749617_exc", "case_bucket": "or", "source_criterion": "Concomitant antiplatelet or anticoagulant use Calculated creatinine clearance < 30 mL/min by Cockcroft-Gault formula Alanine aminotransferase (ALT) or aspartate aminotransferase (AST) > 3 times upper limit of normal (ULN) Total bilirubin > 2 x ULN Thrombocytopenia < 50 x 10 gigalitres (Gl) High bleeding risk or spontaneously prolonged prothrombin time or activated partial thromboplastin time > 1.5 x ULN Body weight <50 or >120 kg Concomitant use of CYP3A4 or p-glycoprotein inducers or inhibitors Use of Ginkgo biloba or St. John's Wort within 14 days before first dose of study drug Dexamethasone use within last 3 months Women of Childbearing potential without proper contraceptive measures, pregnancy or breast feeding Life expectancy less than 3 months Inability to swallow or issues with malabsorption Any other medical, social, logistical, geographical or psychological factors, which in the opinion of the investigator, would prohibit follow-up, compliance and study completion", "candidate_expression": "((< 30 mL/min) AND (< 50 x 10 gigalitres (Gl)) AND (<50 kg) AND (> 1.5 x ULN) AND (> 2 x ULN) AND (> 3 times upper limit of normal (ULN)) AND (>120 kg) AND (Alanine aminotransferase (ALT)) AND (Any other medical, social, logistical, geographical or psychological factors, which in the opinion of the investigator, would prohibit follow-up, compliance and study completion) AND (Body weight) AND (CYP3A4) AND (Calculated creatinine clearance) AND (Childbearing potential) AND (Cockcroft-Gault formula) AND (Concomitant) AND (Dexamethasone) AND (Ginkgo biloba) AND (High bleeding risk) AND (Inability to swallow) AND (Life expectancy) AND (St. John's Wort) AND (Thrombocytopenia) AND (Total bilirubin) AND (Women) AND (activated partial thromboplastin time) AND (anticoagulant) AND (antiplatelet) AND (aspartate aminotransferase (AST)) AND (breast feeding) AND (contraceptive measures) AND (first dose) AND (first dose of study drug) AND (issues with malabsorption) AND (less than 3 months) AND (p-glycoprotein inducers) AND (p-glycoprotein inhibitors) AND (pregnancy) AND (prolonged prothrombin time) AND (spontaneously) AND (study drug) AND (within 14 days before first dose of study drug) AND (within last 3 months) AND (without))"}
{"candidate_id": "LLM07375", "doc_id": "NCT01866800_inc", "case_bucket": "other", "source_criterion": "Subject is 65 years old who is able and willing to give an informed consent. Patients undergoing planned trans-femoral TAVI. Calculated eGFR below 60ml/min/1.73m2 (MDRD)", "candidate_expression": "((65 years) AND (Calculated eGFR) AND (able and willing to give an informed consent) AND (below 60ml/min/1.73m2) AND (old) AND (planned) AND (trans-femoral TAVI) AND (undergoing))"}
```
