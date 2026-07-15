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
{"candidate_id": "LLM01126", "doc_id": "NCT02519777_inc", "case_bucket": "or", "source_criterion": "a licensed rapid HIV test or HIV enzyme or chemiluminescence immunoassay (E/CIA) test kit at any time prior to study entry and confirmed by a licensed Western blot or a second antibody test by a method other than the initial rapid HIV and/or E/CIA, or by HIV-1 antigen or plasma HIV-1 RNA viral load. NOTE: The term \"licensed\" refers to a United States Food and Drug Administration (FDA)-approved kit, which is required for all IND studies, or for sites located in countries other than the United States, a kit that has been certified or licensed by an oversight body within that country and validated internally. Non-US sites are encouraged to use US FDA-approved methods for IND studies. WHO (World Health Organization) and CDC (Centers for Disease Control and Prevention) guidelines mandate that confirmation of the initial test result must use a test that is different from the one used for the initial assessment. A reactive initial rapid test should be confirmed by either another type of rapid assay or an E/CIA that is based on a different antigen preparation and/or different test principle (eg, indirect versus competitive), or a Western blot or a plasma HIV-1 RNA. OR Documentation of HIV diagnosis in the medical record by a healthcare provider. Tenofovir disoproxil fumarate (TDF) to tenofovir alafenamide fumarate (TAF)/TAF-containing fixed-dose combination regimens Ritonavir (RTV) to cobicistat (COBI)/COBI-containing fixed-dose combination regimens TDF to TAF/TAF-containing fixed-dose combination regimens RTV to COBI/COBI-containing fixed-dose combination regimens HIV-1 plasma RNA less than 50 copies/mL obtained within 90 days prior to study entry by any FDA-approved assay at any United States laboratory that has a Clinical Laboratory Improvement Amendments (CLIA) certification or its equivalent, or at any network-approved non-US laboratory that operates in accordance with Good Clinical Laboratory Practices (GCLP) and participates in appropriate external quality assurance programs. No more than one HIV-1 plasma RNA greater than or equal to 50 and less than 200 copies/mL (only one \"blip\") in the past 6 months with a subsequent HIV-1 plasma RNA less than 50 copies/mL. NOTE: There should be no plasma HIV-1 RNA greater than 200 copies/mL within the 6 months prior to study entry. HAND diagnosis (ANI, MND, or HAD) within 60 days prior to study entry. HAND is defined as at least mild impairment on neurocognitive testing (more than one standard deviation below appropriate normative data in two domains of functioning) and no severely confounding factors. Absolute neutrophil count (ANC) greater than or equal to 500/mm^3 Hemoglobin greater than or equal to 7.5 g/dL Platelet count greater than or equal to 40,000/mm^3 Creatinine less than or equal to 2.0 x upper limit of normal (ULN) Aspartate transaminase (AST) less than or equal to 5 x ULN Alanine transaminase (ALT) less than 3 x ULN Alkaline phosphatase less than or equal to 5 x ULN Total bilirubin less than 1.5 x ULN. NOTE: If the potential participant is taking an indinavir (IDV)- or atazanavir (ATV)-containing regimen at the time of screening, total bilirubin less than or equal to 5 x ULN is acceptable. Creatinine clearance (CrCl) greater than or equal to 60 mL/min, either measured or estimated by Cockcroft-Gault equation. NOTE: A calculator for estimating the CrCl can be found at www.fstrf.org/ACTG/ccc.html Females of reproductive potential (women who have not been post-menopausal for at least 24 consecutive months, ie, who have had menses within the preceding 24 months, or women who have not undergone surgical sterilization, hysterectomy or bilateral salpingectomy or bilateral oophorectomy or tubal ligation) must have a negative serum or urine pregnancy test by any US clinic or laboratory that has a CLIA certification or its equivalent, or is using a point of care (POC) / CLIA-waived test, or at any network-approved non-US laboratory or clinic that operates in accordance with GCLP and participates in appropriate external quality assurance programs within 48 hours prior to study entry Females of reproductive potential must agree not to participate in the conception process (ie, active attempt to become pregnant, in vitro fertilization), and if participating in sexual activity that could lead to pregnancy, must use at least one reliable form of contraception. Female participants must use contraceptives while receiving study treatment and for 6 weeks after stopping study treatment. More information on this criterion is available in the protocol. Men and women 18 years of age and older who are able to complete the neuropsychological tests Ability and willingness of participant or a legally authorized representative (see protocol for more information) to provide informed consent Ability and willingness to take oral study medications", "candidate_expression": "((Ability and willingness of participant or a legally authorized representative (see protocol for more information) to provide informed consent) AND (Ability and willingness to take oral study medications) AND (Absolute neutrophil count (ANC) greater than or equal to 500/mm^3) AND (Alanine transaminase (ALT) less than 3 x ULN) AND (Alkaline phosphatase less than or equal to 5 x ULN) AND (Aspartate transaminase (AST) less than or equal to 5 x ULN) AND (COBI) AND (COBI-containing fixed-dose combination regimens) AND (Cockcroft-Gault equation) AND (Creatinine clearance (CrCl) greater than or equal to 60 mL/min) AND (Creatinine less than or equal to 2.0 x upper limit of normal (ULN)) AND (Females of reproductive potential (women who have not been post-menopausal for at least 24 consecutive months, ie, who have had menses within the preceding 24 months, or women who have not undergone surgical sterilization, hysterectomy or bilateral salpingectomy or bilateral oophorectomy or tubal ligation) must have a negative serum or urine pregnancy test by any US clinic or laboratory that has a CLIA certification or its equivalent, or is using a point of care (POC) / CLIA-waived test, or at any network-approved non-US laboratory or clinic that operates in accordance with GCLP and participates in appropriate external quality assurance programs within 48 hours prior to study entry) AND (Females of reproductive potential must agree not to participate in the conception process (ie, active attempt to become pregnant, in vitro fertilization), and if participating in sexual activity that could lead to pregnancy, must use at least one reliable form of contraception. Female participants must use contraceptives while receiving study treatment and for 6 weeks after stopping study treatment. More information on this criterion is available in the protocol.) AND (HAND within 60 days prior to study entry) AND (HIV diagnosis) AND (HIV-1 plasma RNA No more than one greater than or equal to 50 and less than 200 copies/mL in the past 6 months) AND (HIV-1 plasma RNA less than 50 copies/mL within 90 days prior to study entry) AND (HIV-1 plasma RNA subsequent less than 50 copies/mL) AND (Hemoglobin greater than or equal to 7.5 g/dL) AND (Platelet count greater than or equal to 40,000/mm^3) AND (RTV) AND (Ritonavir (RTV)) AND (TAF) AND (TAF-containing fixed-dose combination regimens) AND (TDF) AND (Tenofovir disoproxil fumarate (TDF)) AND (Total bilirubin less than 1.5 x ULN) AND (age 18 years and older) AND (cobicistat (COBI)) AND (neurocognitive testing in two domains of functioning impairment more than one standard deviation below appropriate normative data) AND (neuropsychological tests able to complete) AND (regimen at the time of screening) AND (tenofovir alafenamide fumarate (TAF)) AND (total bilirubin less than or equal to 5 x ULN) AND NOT (plasma HIV-1 RNA greater than 200 copies/mL within the 6 months prior to study entry) AND NOT (severely confounding factors) AND ((ANI) OR (HAD) OR (MND)) AND ((atazanavir (ATV)) OR (indinavir (IDV))) AND ((Men) OR (women)))"}
{"candidate_id": "LLM01127", "doc_id": "NCT03211741_inc", "case_bucket": "or", "source_criterion": "Age = 18 years of either gender Written informed consent must be obtained before any intravitreal injection of bevacizumab is performed Visual impairment predominantly due to abnormal new vessel ingrowth and/or macular edema. The presence of fluid (intraretinal, subretinal or sub-RPE) detected clinically or on the ocular coherence tomography.", "candidate_expression": "((= 18 years) AND (Age) AND (Visual impairment) AND (Written informed consent must be obtained before any intravitreal injection of bevacizumab is performed) AND (abnormal new vessel ingrowth) AND (either gender) AND (fluid) AND (intraretinal) AND (macular edema) AND (ocular coherence tomography) AND (sub-RPE) AND (subretinal))"}
{"candidate_id": "LLM01128", "doc_id": "NCT02805504_inc", "case_bucket": "other", "source_criterion": "Patients undergoing urologic surgery.", "candidate_expression": "(urologic surgery)"}
{"candidate_id": "LLM01129", "doc_id": "NCT02944604_exc", "case_bucket": "other", "source_criterion": "NA", "candidate_expression": "(EMPTY)"}
{"candidate_id": "LLM01130", "doc_id": "NCT02647788_inc", "case_bucket": "scope", "source_criterion": "Patients undergoing ambulatory hand surgery for carpal tunnel and trigger finger, under local anesthesia with or without sedation.", "candidate_expression": "((ambulatory) AND (carpal tunnel) AND (hand surgery) AND (local anesthesia) AND (trigger finger))"}
{"candidate_id": "LLM01131", "doc_id": "NCT01809041_inc", "case_bucket": "or", "source_criterion": "major elective gastrointestinal, gynecological, prostate or bladder surgery patients who are = 60 years old. the surgery is laparoscopic surgery and is expected to last for = 2 hours under general anesthesia and the patient will stay in hospital for at least 7 days after surgery. lack of serious hearing and vision impairment and be able to read so that neurobehavioral tests can be performed.", "candidate_expression": "((= 2 hour) AND (= 60 years old) AND (able to read) AND (at least 7 days after surgery) AND (bladder surgery) AND (can be performed) AND (elective) AND (expected) AND (gastrointestinal surgery) AND (gynecological surgery) AND (hearing impairment) AND (lack of) AND (laparoscopic surgery) AND (last) AND (neurobehavioral tests) AND (old) AND (prostate surgery) AND (stay in hospital) AND (under general anesthesia) AND (vision impairment) AND (will))"}
{"candidate_id": "LLM01132", "doc_id": "NCT03381755_inc", "case_bucket": "scope", "source_criterion": "After half-dose ticagrelor (loading dose 90mg, and then 45mg bidpo.) treatment for 3 days, the platelet aggregation is effectively inhibited by light transmission aggregometry method and thromboela-stogram. planned to undergo PCI recently planned to DAPT for 1 year after PCI", "candidate_expression": "((DAPT planned to for 1 year after PCI) AND (PCI) AND (PCI planned to undergo) AND (light transmission aggregometry) AND (loading dose 90mg 45mg bidpo.) AND (platelet aggregation inhibited) AND (thromboela-stogram) AND (ticagrelor half-dose treatment for 3 days))"}
{"candidate_id": "LLM01133", "doc_id": "NCT02592980_inc", "case_bucket": "other", "source_criterion": "Only patients with atrial fibrillation, above 18 years, and with TTR <50% based on the last three values of INR will be included in this study.", "candidate_expression": "((TTR <50% based on the last three values of INR) AND (atrial fibrillation) AND (years above 18 years))"}
{"candidate_id": "LLM01134", "doc_id": "NCT03011476_inc", "case_bucket": "or", "source_criterion": "Parkinson disease diagnosed by United Kingdom Parkinson's disease Society Brain Bank Criteria Postural instability and gait disturbance phenotype Hoehn and Yahr stage = 3 Mini-Mental status examination = 24", "candidate_expression": "((= 2) AND (Hoehn and Yahr) AND (Mini-Mental status examination) AND (Parkinson disease) AND (United Kingdom Parkinson's disease Society Brain Bank Criteria) AND (stage = 3) AND ((Postural instability) OR (gait disturbance)))"}
{"candidate_id": "LLM01135", "doc_id": "NCT03209011_exc", "case_bucket": "or", "source_criterion": "Active consumption of alcohol and/or drugs Co-infection with human immunodeficiency virus, hepatitis C virus, or hepatitis D virus History of autoimmune hepatitis Psychiatric disease Evidence of neoplastic diseases of the liver", "candidate_expression": "((Active) AND (Evidence of) AND (History) AND (Psychiatric disease) AND (autoimmune hepatitis) AND (liver) AND (neoplastic diseases) AND ((consumption of alcohol) OR (drugs consumption of)) AND ((hepatitis C virus) OR (hepatitis D virus) OR (human immunodeficiency virus)))"}
{"candidate_id": "LLM01136", "doc_id": "NCT02849483_inc", "case_bucket": "other", "source_criterion": "20-70 yrs of age ASA(American Society of Anesthesiologists) physical status class I or II Scheduled for gynecological laparoscopic surgery", "candidate_expression": "((20-70 yrs) AND (ASA physical status class) AND (American Society of Anesthesiologists) AND (I or II) AND (Scheduled) AND (age) AND (gynecological) AND (laparoscopic surgery))"}
{"candidate_id": "LLM01137", "doc_id": "NCT00396734_exc", "case_bucket": "or", "source_criterion": "use more than 2g a day; 5 times a week to everyday Subjects who are diagnosed as suffering from psychotic illness according to DSM-IV (Axis 1)22, or with a history of CNS disease, a history of infection that might affect CNS (HIV, syphilis, cytomegalovirus, herpes), or a history of head injury with loss of consciousness,pregnant women.", "candidate_expression": "((5 times a week to everyday) AND (Axis 1) AND (CNS disease) AND (DSM-IV) AND (HIV) AND (affect CNS) AND (cytomegalovirus) AND (head injury) AND (herpes) AND (history) AND (infection) AND (loss of consciousness) AND (more than 2g a day) AND (pregnant) AND (psychotic illness) AND (syphilis))"}
{"candidate_id": "LLM01138", "doc_id": "NCT02754583_exc", "case_bucket": "other", "source_criterion": "School districts that are too difficult to reach (more than a 3-hour walk from the farthest place reachable by a four-wheel drive vehicle) School districts in the 2 urban regions of the study area Refusal of village chief All residents residing near to the well sites that are randomly selected for this study. Refusal of participant [or parent/guardian]", "candidate_expression": "((Refusal of participant [or parent/guardian]) AND (School districts in the 2 urban regions of the study area) AND (School districts that are too difficult to reach) AND (near to the well sites) AND (residing) AND (walk from the farthest place reachable by a four-wheel drive vehicle more than a 3-hour))"}
{"candidate_id": "LLM01139", "doc_id": "NCT03347513_inc", "case_bucket": "other", "source_criterion": "Diagnosed Iron deficiency anemia. H-pylori positive cases. Second trimester pregnancy.", "candidate_expression": "((H-pylori positive) AND (Iron deficiency anemia) AND (Second trimester) AND (pregnancy))"}
{"candidate_id": "LLM01140", "doc_id": "NCT02186600_inc", "case_bucket": "other", "source_criterion": "Women who are in their first 5 years of menopause Have a T score between -1 and -2.49 at the femoral neck, total hip, or L1-L4 spine Be 19 years of age or older Have their health care provider's permission to enroll in the study.", "candidate_expression": "((19 years of age or older) AND (L1-L4 spine) AND (T score) AND (Women) AND (age) AND (between -1 and -2.49) AND (femoral neck) AND (menopause) AND (n their first 5 years of menopause) AND (total hip))"}
{"candidate_id": "LLM01141", "doc_id": "NCT02553226_inc", "case_bucket": "other", "source_criterion": "Women stimulated with Syntocinon® infusion for induction of labour (with or without cervical priming by prostaglandin)", "candidate_expression": "((Syntocinon®) AND (Syntocinon® infusion) AND (Women) AND (cervical priming) AND (induction of labour) AND (prostaglandin))"}
{"candidate_id": "LLM01142", "doc_id": "NCT01491763_exc", "case_bucket": "or", "source_criterion": "Any other variety of LAL Patients with a history of coronary artery disease, valvular or hypertensive heart disease Patients with chronic liver disease Patients with chronic respiratory failure Renal failure not due to LAL Patients with positive HIV status No serious neurological abnormalities due to LAL Impact on overall severe (grade 3 or 4 of the WHO scale) not attributable to the LAL Pregnant or breastfeeding initial blast crisis CML", "candidate_expression": "((CML blast crisis) AND (HIV status positive) AND (LAL due to) AND (LAL other variety) AND (Pregnant) AND (Renal failure) AND (breastfeeding) AND (chronic liver disease) AND (chronic respiratory failure) AND (coronary artery disease) AND (heart disease valvular) AND (hypertensive heart disease) AND NOT (LAL due to) AND NOT (neurological abnormalities serious))"}
{"candidate_id": "LLM01143", "doc_id": "NCT03123562_inc", "case_bucket": "other", "source_criterion": "Cerebral palsy of any types caused by Neonatal Jaundice", "candidate_expression": "((Cerebral palsy) AND (Neonatal Jaundice))"}
{"candidate_id": "LLM01144", "doc_id": "NCT02996916_exc", "case_bucket": "or", "source_criterion": "Secondary hypertension or malignant hypertension Diabetes mellitus History or evidence of a stroke Hepatic or hematologic abnormality Mild Cognitive Impairment or Dementia Serum potassium level = 5.5 mEq/L Serum creatinine level = 3.0 mg/dL Acute or chronic disease Allergy to any drugs Pregnancy", "candidate_expression": "((= 3.0 mg/dL) AND (= 5.5 mEq/L) AND (Allergy) AND (Diabetes mellitus) AND (Pregnancy) AND (Serum creatinine level) AND (Serum potassium level) AND (any drugs) AND (stroke) AND ((Secondary hypertension) OR (malignant hypertension)) AND ((Dementia) OR (Mild Cognitive Impairment)) AND ((Acute disease) OR (chronic disease)) AND ((History) OR (evidence)) AND ((Hepatic abnormality) OR (hematologic abnormality)))"}
{"candidate_id": "LLM01145", "doc_id": "NCT02964715_inc", "case_bucket": "or", "source_criterion": "biopsy proven NASH Type 2 DM HbA1c :>6.5% BMI < 45kg/m2 Any anti-diabetic agent except SGLT2 inhibitors, TZDs(thiazolidinediones), DPP4(Dipeptidyl peptidase4) inhibitors and GLP1 RAs(Glucagon-like Peptide 1-Receptor Agonists)", "candidate_expression": "((BMI < 45kg/m2) AND (DPP4 inhibitors) AND (Dipeptidyl peptidase4 inhibitors) AND (GLP1 RAs) AND (Glucagon-like Peptide 1-Receptor Agonists) AND (HbA1c >6.5%) AND (NASH) AND (SGLT2 inhibitors) AND (TZDs) AND (Type 2 DM) AND (anti-diabetic agent) AND (biopsy) AND (thiazolidinediones))"}
{"candidate_id": "LLM01146", "doc_id": "NCT02499185_exc", "case_bucket": "other", "source_criterion": "Ongoing acute kidney injury Stage 2/3 History of kidney transplant", "candidate_expression": "((2/3) AND (History) AND (Stage) AND (acute kidney injury) AND (kidney transplant))"}
{"candidate_id": "LLM01147", "doc_id": "NCT02618057_exc", "case_bucket": "or", "source_criterion": "Immunosuppresant host Chronic cardiovascular/pulmonary disease Hospital acquired infection", "candidate_expression": "((Hospital acquired infection) AND (Immunosuppresant host) AND (cardiovascular disease) AND (pulmonary disease))"}
{"candidate_id": "LLM01148", "doc_id": "NCT02456129_inc", "case_bucket": "or", "source_criterion": "Body mass index (BMI): 18 ≤ BMI ≤ 32 kg/m² Postmenopausal state revealed by: Medical history, if applicable (natural menopause at least 12 months prior to first study drug administration; or surgical menopause by bilateral ovariectomy at least 3 months prior to first study drug administration), in addition: in women < 65 years old, follicle stimulating hormone (FSH) > 40 IU/L", "candidate_expression": "((18 ≤ BMI ≤ 32 kg/m²) AND (< 65 years) AND (> 40 IU/L) AND (Body mass index (BMI)) AND (Postmenopausal state) AND (at least 12 months prior to first study drug administration) AND (at least 3 months prior to first study drug administration) AND (bilateral ovariectomy) AND (first study drug administration) AND (follicle stimulating hormone (FSH)) AND (women) AND (years old) AND ((natural menopause) OR (surgical menopause)))"}
{"candidate_id": "LLM01149", "doc_id": "NCT03420638_inc", "case_bucket": "other", "source_criterion": "Scheduled to undergo bilateral palatine tonsillectomy as the only procedure", "candidate_expression": "((palatine tonsillectomy Scheduled to undergo bilateral only procedure) AND (procedure))"}
{"candidate_id": "LLM01150", "doc_id": "NCT02469610_exc", "case_bucket": "other", "source_criterion": "Previous thoracic operation in the same side.", "candidate_expression": "((Previous) AND (same side) AND (thoracic operation))"}
```
