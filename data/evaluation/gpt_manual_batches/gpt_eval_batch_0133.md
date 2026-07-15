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
{"candidate_id": "LLM03301", "doc_id": "NCT02281643_inc", "case_bucket": "other", "source_criterion": "M. perstans mg-positive status Good general health without any clinical condition requiring long-term medication. Normal renal and hepatic laboratory profiles", "candidate_expression": "((Good general health) AND (M. perstans mg positive) AND (hepatic laboratory profile Normal) AND (long-term medication) AND (renal laboratory profile Normal) AND NOT (clinical condition requiring long-term medication requiring long-term medication))"}
{"candidate_id": "LLM03302", "doc_id": "NCT02950558_exc", "case_bucket": "or", "source_criterion": "Unable to give informed consent in English Unable to complete surveys in English Unable to understand instructions for using pump in English Unavailable for followup Polytrauma; undergoing other surgeries or having other orthopedic injuries related to the precipitating cause of the ankle fracture Infection Peripheral vascular disease Diabetes Currently undergoing chemotherapy Pregnancy Currently lactating Heart disease or heart rhythm disorder or taking anti-arrhythmic drugs Severe renal impairment (Class 3 or worse kidney disease) Liver disease (cirrhosis or liver failure) Prior allergic reaction to any type of local anesthetic Taking therapeutic doses of anti-coagulants or anti-platelet therapy (prophylactic doses started because of hospital admission are not an exclusion) Currently taking antidepressants or other psychiatric medications Single shot local nerve block prior to surgery was ineffective Selected for neuraxial anesthesia rather than general anesthesia for the open reduction surgery Already receiving chronic analgesic therapy for a separate chronic pain condition", "candidate_expression": "((Currently lactating) AND (Diabetes) AND (Heart disease) AND (Infection) AND (Liver disease) AND (Peripheral vascular disease) AND (Polytrauma) AND (Pregnancy) AND (Severe renal impairment) AND (Single shot) AND (Unable to complete surveys in English) AND (Unable to give informed consent in English) AND (Unable to understand instructions for using pump in English) AND (Unavailable for followup) AND (allergic reaction) AND (analgesic therapy) AND (ankle fracture) AND (anti-arrhythmic drugs) AND (anti-coagulants) AND (anti-platelet therapy) AND (antidepressants) AND (chemotherapy) AND (chronic) AND (chronic pain) AND (cirrhosis) AND (general anesthesia) AND (heart rhythm disorder) AND (liver failure) AND (local anesthetic) AND (local nerve block) AND (neuraxial anesthesia) AND (not) AND (open reduction surgery) AND (other orthopedic injuries) AND (other surgeries) AND (prior to surgery) AND (prophylactic) AND (psychiatric medications) AND (rather than) AND (separate) AND (surgery) AND (therapeutic))"}
{"candidate_id": "LLM03303", "doc_id": "NCT02934269_inc", "case_bucket": "or", "source_criterion": "Healthy male and/or female subjects between the ages of 18 and 55 years, and a body mass index (BMI) of ≥ 18 and ≤ 33 kg/m2 with body weight ≥ 50 and ≤ 90 kg at screening. Females must have been surgically sterilized (hysterectomy, bilateral oophorectomy, or bilateral salpingo-oophorectomy; proper documentation required) at least 6 months before screening, or be postmenopausal (defined as 24 consecutive months without menses before screening, with a follicle-stimulating hormone [FSH] level of > 40 IU/L at screening).", "candidate_expression": "((24 consecutive months) AND (> 40 IU/L) AND (Females) AND (Healthy) AND (ages) AND (at least 6 months before) AND (at screening) AND (before screening) AND (between 18 and 55 years) AND (bilateral oophorectomy) AND (bilateral salpingo-oophorectomy) AND (body mass index (BMI)) AND (body weight) AND (female) AND (follicle-stimulating hormone [FSH]) AND (hysterectomy) AND (male) AND (menses) AND (postmenopausal) AND (screening) AND (surgically sterilized) AND (without) AND (≥ 18 and ≤ 33 kg/m2) AND (≥ 50 and ≤ 90 kg))"}
{"candidate_id": "LLM03304", "doc_id": "NCT02504203_exc", "case_bucket": "other", "source_criterion": "NA", "candidate_expression": "(EMPTY)"}
{"candidate_id": "LLM03305", "doc_id": "NCT03532620_exc", "case_bucket": "or", "source_criterion": "Past history of hypersensitivity to the study drug; Diagnosed diabetes; Severe liver disease (including ALT or AST=2.5-fold the normal upper limit), biliary obstruction; Ongoing treatment with cyclosporine within 2 weeks; Renal dysfunction, including endogenous creatinine clearance male<120ml/min, female<105ml/min, serum creatinine=2mg/dl (186umol/L), Renal function progressive decline, GFR<30ml•min-1•1.73m-2; Diagnosed or past history of ASCVD (including ACS, SCAD, revascularization, ICM, ischemic stroke, TIA, PASD, etc. SBP=180mmHg, or DBP=110mmHg; Ongoing treatment with Beta blockers, Diuretic; Secondary hypertension, including SAS, PA, RAS, pheochromocytoma, Cushing's syndrome, aorta diseases, drug induced hypertension; Ongoing treatment with statins, fibrates, and/or cation exchange resins within 2 weeks; Pancreatic disease; History of gastrectomy, short bowel syndrome; Ongoing hormone replacement therapy; Diagnosed or suspected malignant tumor; Familial hypercholesterolemia; Any diseases may limit the efficacy or safety of the study; Pregnant or possibly pregnant woman, or breastfeeding woman, or woman who wishes to become pregnant during study participation; IFG impaired fast glucose, FPG fasting plasma glucose, IGT impaired glucose tolerance, OGTT oral glucose tolerance test, PG plasma glucose, HbA1C hemoglobin A1C, LDL-C low-density lipoprotein cholesterol, TG triglycerides, SBP systolic blood pressure, DBP diastolic blood pressure, ALT alanine aminotransferase, AST aspartate aminotransferase, GFR glomerular filtration rate, ASCVD arteriosclerotic cardiovascular disease, ACS acute coronary syndrome, SCAD stable coronary artery disease, ICM ischemic cardiomyopathy, TIA transient ischemic attack, PASD peripheral atherosclerotic disease, SAS sleep apnea syndrome, PA primary aldosteronism, RAS renal arterial stenosis", "candidate_expression": "((186umol/L) AND (ASCVD) AND (Familial hypercholesterolemia) AND (Pancreatic disease) AND (Pregnant or possibly pregnant woman, or breastfeeding woman, or woman who wishes to become pregnant during study participation) AND (Renal dysfunction) AND (Secondary hypertension) AND (biliary obstruction) AND (cyclosporine) AND (diabetes) AND (hormone replacement therapy Ongoing) AND (hypersensitivity) AND (liver disease Severe) AND (malignant tumor) AND (study drug) AND (treatment Ongoing) AND (treatment Ongoing within 2 weeks) AND ((female <105ml/min) OR (male <120ml/min)) AND ((GFR <30ml•min-1•1.73m-2) OR (Renal function progressive decline) OR (endogenous creatinine clearance) OR (serum creatinine =2mg/dl)) AND ((ACS) OR (ICM) OR (PASD) OR (SCAD) OR (TIA) OR (ischemic stroke) OR (revascularization)) AND ((DBP =110mmHg) OR (SBP =180mmHg)) AND ((Beta blockers) OR (Diuretic)) AND ((Cushing's syndrome) OR (PA) OR (RAS) OR (SAS) OR (aorta diseases) OR (hypertension drug induced) OR (pheochromocytoma)) AND ((cation exchange resins) OR (fibrates) OR (statins)) AND ((gastrectomy) OR (short bowel syndrome)) AND ((ALT) OR (AST)) AND ((Diagnosed) OR (suspected)))"}
{"candidate_id": "LLM03306", "doc_id": "NCT03164304_inc", "case_bucket": "other", "source_criterion": "Pregnant women admitted to Women health hospital with a diagnosis of severe pre-eclampsia", "candidate_expression": "((Pregnant) AND (Women health hospital) AND (admitted to) AND (pre-eclampsia) AND (severe) AND (women))"}
{"candidate_id": "LLM03307", "doc_id": "NCT03484091_exc", "case_bucket": "or", "source_criterion": "Severe deformity (varus or values from mechanical axis more than 5 degrees Allergy to hyaluronic acid Pain on hip or ankle Post-traumatic or post surgery of lower extremity Post infection of knee Previous hyaluronic acid injection within 6 months Pregnancy or lactation Underlying Rheumatoid arthritis, stroke, malignancy, venous occlusion", "candidate_expression": "((Allergy) AND (Pain) AND (Post) AND (Post-traumatic of lower extremity) AND (Pregnancy) AND (Previous) AND (Rheumatoid arthritis) AND (Severe) AND (Underlying) AND (ankle) AND (deformity) AND (hip) AND (hyaluronic acid) AND (hyaluronic acid injection) AND (infection of knee) AND (lactation) AND (malignancy) AND (more than 5 degrees) AND (post surgery of lower extremity) AND (stroke) AND (values from mechanical axis) AND (varus) AND (venous occlusion) AND (within 6 months))"}
{"candidate_id": "LLM03308", "doc_id": "NCT02339844_inc", "case_bucket": "or", "source_criterion": "Inclusion Criteria Patients: Fulfilling the diagnostic criteria of schizophrenia or schizoaffective disorder according to ICD-10 (International Classification of Diseases version 10) or DSM-IV/V (Diagnostic and Statistical Manual version 4 /5), Age 18-45 years, Never treated with antipsychotic compounds or central nervous system (CNS) stimulants, Legally competent Inclusion criteria controls: Matching patients on age (+/- 2 years), sex and parental socioeconomic status, Age 18-45 years, No psychiatric or physical disease.", "candidate_expression": "((Age 18-45 years) AND (Age 18-45 years DSM-IV/V (Diagnostic and Statistical Manual version 4 /5)) AND (Legally competent) AND (Patients) AND (controls) AND (schizoaffective disorder ICD-10 (International Classification of Diseases version 10)) AND (schizophrenia) AND NOT (antipsychotic compounds) AND NOT (central nervous system (CNS) stimulants) AND NOT (psychiatric disease) AND NOT (physical disease))"}
{"candidate_id": "LLM03309", "doc_id": "NCT00917891_inc", "case_bucket": "or", "source_criterion": "1. Women 18 to 40 years of age inclusive who can give written informed consent 2. Available for all visits and consent to follow all procedures scheduled for the study 3. Agree to daily application of gel and monitoring as per Daily Monitored Adherence (DMA) method 4. Healthy and self-reported sexually active 5. HIV-negative as determined by a HIV rapid test at time of enrollment 6. On a stable form of contraception and willing to continue on this stable method of contraception, OR, Have undergone surgical sterilisation at least 3 months prior to enrollment 7. In the absence of the use of exogenous hormone(s), have a self-reported regular menstrual cycle defined as having a minimum of 21 days and a maximum of 36 days between menses 8. Upon pelvic/speculum examination and colposcopy at the time of enrollment, the cervix and vagina appear normal as determined by the investigator 9. Asymptomatic for genital infections at the time of enrollment 10. Willing to refrain from use of vaginal products or objects within 14 days prior to enrollment and for the duration of the study 11. Willing to answer acceptability and adherence questionnaires throughout the study 12. Willing to refrain from participation in any other research study for the duration of this study 13. Willing to provide adequate locator information for study retention purposes and be reachable per local standard procedures", "candidate_expression": "((18 to 40 years) AND (Agree to daily application of gel and monitoring as per Daily Monitored Adherence (DMA) method) AND (Asymptomatic) AND (Available for all visits and consent to follow all procedures scheduled for the study) AND (HIV) AND (HIV rapid test) AND (HIV-negative) AND (Healthy) AND (On a stable form of contraception and willing to continue on this stable method of contraception, OR, Have undergone surgical sterilisation at least 3 months prior to enrollment) AND (Willing) AND (Willing to answer acceptability and adherence questionnaires throughout the study) AND (Willing to provide adequate locator information for study retention purposes and be reachable per local standard procedures) AND (Willing to refrain from participation in any other research study for the duration of this study) AND (Women) AND (absence) AND (acceptability questionnaires) AND (adherence questionnaires) AND (age) AND (as determined by the investigator) AND (at the time of enrollment) AND (at time of enrollment) AND (can give written informed consent) AND (cervix) AND (colposcopy) AND (daily) AND (enrollment) AND (exogenous hormone) AND (for the duration of the study) AND (gel) AND (genital infections) AND (maximum of 36 days) AND (menstrual cycle) AND (minimum of 21 days) AND (monitoring) AND (negative) AND (normal) AND (objects vaginal) AND (pelvic examination) AND (refrain) AND (regular) AND (regular menstrual cycle) AND (self-reported) AND (sexually active) AND (speculum examination) AND (the study) AND (throughout the study) AND (time of enrollment) AND (vagina) AND (vaginal products) AND (within 14 days prior to enrollment))"}
{"candidate_id": "LLM03310", "doc_id": "NCT03241368_inc", "case_bucket": "or", "source_criterion": "Subject has provided informed consent. Subject is ≥ 18 years of age Subject is willing and able to comply with all aspects of treatment and evaluation schedule. Subject has known CD and a recent history (within last 2 years) of mucosal disease (diagnosis based on radiologic, endoscopic, or histological evidence).", "candidate_expression": "((age ≥ 18 years) AND (mucosal disease recent history) AND ((endoscopic evidence) OR (histological evidence) OR (radiologic evidence)))"}
{"candidate_id": "LLM03311", "doc_id": "NCT03064867_exc", "case_bucket": "or", "source_criterion": "Prior treatment toxicities have not resolved to < Grade 2 according to NCI CTCAE Version 4.0 (except clinically insignificant toxicities such as alopecia). Subjects receiving any other investigational agents. Patients with active tumor lysis syndrome (TLS) either from laboratory or clinical changes. Patients with active central nervous system (CNS) disease defined as symptomatic meningeal lymphoma or known CNS parenchymal lymphoma. History of severe allergic reactions attributed to compounds of similar chemical or biologic composition to rituximab or other agents used in this study. Subjects with uncontrolled intercurrent illness . HIV-positive subjects on combination antiretroviral therapy are ineligible because of the potential for pharmacokinetic interactions with Venetoclax. In addition, these subjects are at increased risk of lethal infections when treated with marrow suppressive therapy. Appropriate studies will be undertaken in subjects receiving combination antiretroviral therapy when indicated. HIV testing prior to enrollment is not required for screening but strongly encouraged for patients with no documented prior HIV assessment. Presence of positive test results for hepatitis B virus (HBV), hepatitis B surface antigen (HBsAg), or hepatitis C (HCV) antibody. Patients who are positive for HCV antibody must be negative for HCV by polymerase chain reaction (PCR) to be eligible for study participation Patients with occult or prior HBV infection (defined as positive total hepatitis B core antibody [HBcAb] and negative HBsAg) may be included if HBV DNA is undetectable. These patients must be willing to undergo monthly DNA testing. Women who are pregnant or lactating Malabsorption syndrome or other condition that precludes enteral route of administration Chemotherapy or radiation within 3 weeks of the first scheduled study treatment. Less than 2-year disease free from another primary malignancy (other than squamous or basal cell carcinoma of the skin, \"in-situ\" carcinoma of the cervix or breast, superficial bladder carcinoma, or previously treated localized prostate cancer with normal prostate specific antigen (PSA) levels). Patients who have had completed all anti-cancer treatment for another primary malignancy more than 2 years prior to screening are eligible if they are not considered to have a \"currently active\" malignancy based on having less than a 30% risk of relapse. Major surgery, other than diagnostic surgery, within 2 weeks. Medical condition requiring chronic use of high dose systemic corticosteroids (i.e., doses of prednisone higher than 10 mg/day or equivalent). Brief (<15 days) treatment with glucocorticoids (prednisone 100 mg by mouth daily, or equivalent) is acceptable. Known allergy to both xanthine oxidase inhibitors and rasburicase. Use of warfarin is prohibited. Anticoagulation with low-molecular weight heparin (i.e. enoxaparin) or direct thrombin inhibitors is permitted. The following concomitant medications are not allowed from 7 days prior to the first dose of study drug and during venetoclax administration: Strong CYP3A4 inhibitors including but not limited to fluconazole, ketoconazole, and clarithromycin or strong CYP3A4 inducers included but not limited to rifampin, carbamazepine. Receipt of live-virus vaccines within 28 days prior to the initiation of study treatment or need for live-virus vaccines at any time during study treatment. Concomitant medications that fall into the categories below could potentially lead to adverse reactions and should be considered cautionary. Moderate/Weak CYP3A inducers such as efavirenz and oxcarbazepine CYP2C8 substrates such as thiazolidinediones (glitazones) and select statins (because of expected inhibition of the metabolism of CYP2C8 substrates) by venetoclax CYP2C9 substrates such as tolbutamide (because of expected inhibition of the metabolism of CYP2C9 substrates by venetoclax. It is recommended to exclude CYP2C9 substrates with a narrow therapeutic index such as phenytoin.", "candidate_expression": "((100 mg daily) AND (<15 days) AND (Anticoagulation) AND (CYP2C9 substrates) AND (HBV DNA) AND (HBV infection) AND (HBsAg) AND (HCV) AND (HCV antibody) AND (HIV-positive) AND (It is recommended to exclude CYP2C9 substrates with a narrow therapeutic index such as phenytoin) AND (Less than 2-year) AND (Major surgery) AND (Medical condition) AND (Women) AND (allergic reactions) AND (allergy) AND (another) AND (anti-cancer treatment) AND (any time during) AND (are eligible) AND (carbamazepine) AND (central nervous system (CNS) disease) AND (chronic) AND (clarithromycin) AND (combination antiretroviral therapy) AND (diagnostic surgery) AND (disease free) AND (enoxaparin) AND (first dose of study drug) AND (fluconazole) AND (glitazones) AND (glucocorticoids) AND (hepatitis B surface antigen (HBsAg)) AND (hepatitis B virus (HBV)) AND (hepatitis C (HCV) antibody) AND (high dose) AND (higher than 10 mg/day) AND (ketoconazole) AND (more than 2 years prior) AND (narrow therapeutic index) AND (need for) AND (negative) AND (normal) AND (other than) AND (phenytoin) AND (polymerase chain reaction (PCR)) AND (positive) AND (prednisone) AND (primary malignancy) AND (prostate specific antigen (PSA) levels) AND (rasburicase) AND (rifampin) AND (screening) AND (select) AND (severe) AND (study treatment) AND (symptomatic) AND (systemic corticosteroids) AND (the first scheduled study treatment) AND (the initiation of study treatment) AND (thiazolidinediones) AND (tolbutamide) AND (total hepatitis B core antibody [HBcAb]) AND (tumor lysis syndrome (TLS)) AND (undetectable) AND (venetoclax) AND (warfarin) AND (within 2 weeks) AND (within 28 days prior) AND (within 3 weeks of the first scheduled study treatment) AND (xanthine oxidase inhibitors) AND ((Strong CYP3A4 inhibitors) OR (strong CYP3A4 inducers)) AND ((compounds of similar chemical or biologic composition to other agents used in this study) OR (compounds of similar chemical or biologic composition to rituximab)) AND ((live-virus vaccines)) AND ((Moderate CYP3A inducers) OR (Weak CYP3A inducers)) AND ((efavirenz) OR (oxcarbazepine)) AND ((CYP2C8 substrates) OR (statins)) AND ((lactating) OR (pregnant)) AND ((Malabsorption syndrome) OR (condition that precludes enteral route of administration)) AND ((Chemotherapy) OR (radiation)) AND ((\"in-situ\" carcinoma of the cervix) OR (\"in-situ\" carcinoma of the cervix breast) OR (localized prostate cancer) OR (squamous or basal cell carcinoma of the skin) OR (superficial bladder carcinoma)) AND ((CNS parenchymal lymphoma) OR (meningeal lymphoma)) AND ((direct thrombin inhibitors) OR (low-molecular weight heparin)) AND ((7 days prior) OR (venetoclax administration)))"}
{"candidate_id": "LLM03312", "doc_id": "NCT02205931_exc", "case_bucket": "or", "source_criterion": "Age <1m or > 24 months of age No secure diagnosis of epilepsy < 4 seizures/week on average in baseline period Trial of < 2 AEDs Continues on corticosteroids in previous 3 months prior to randomisation Metabolic disease contraindicating use of the ketogenic diet e.g. pyruvate carboxylase deficiency, MCAD from previous medical investigation and screening at baseline. Progressive neurological disease Severe gastroesophageal reflux Previous treatment with the ketogenic diet Concurrent participation in another clinical trial of an investigational medicinal product. Patients who are prescribed AEDs not listed in the trial IMPs", "candidate_expression": "((< 2) AND (< 4 /week) AND (<1m or > 24 months of age) AND (AEDs) AND (Age) AND (Concurrent participation in another clinical trial of an investigational medicinal product) AND (MCAD) AND (Metabolic disease) AND (No) AND (Previous) AND (Progressive) AND (Severe) AND (contraindicating) AND (corticosteroids) AND (epilepsy) AND (gastroesophageal reflux) AND (ketogenic diet) AND (neurological disease) AND (previous 3 months prior to randomisation) AND (pyruvate carboxylase deficiency,) AND (randomisation) AND (seizures))"}
{"candidate_id": "LLM03313", "doc_id": "NCT01567605_exc", "case_bucket": "or", "source_criterion": "cauda equina or conus lesion currently use ventilator colostomy, or do not perform regular bowel care for any reason any skin breakdown (pressure sores) do not speak English are under 19 years old are pregnant or think you might be pregnant medical/psychiatric condition or substance abuse that is likely to affect your ability to complete this study currently using medications containing lidocaine allergy to lidocaine", "candidate_expression": "((allergy) AND (cauda equina) AND (colostomy) AND (conus) AND (currently) AND (do not perform) AND (lesion) AND (lidocaine) AND (medical condition) AND (medications containing lidocaine) AND (not) AND (old) AND (pregnant) AND (pressure sores) AND (psychiatric condition) AND (regular bowel care) AND (skin breakdown) AND (speak English) AND (substance abuse) AND (think you might be) AND (under 19 years) AND (ventilator))"}
{"candidate_id": "LLM03314", "doc_id": "NCT03004261_inc", "case_bucket": "or", "source_criterion": "Any allogeneic stem cell transplant recipient = 14 years of age and = 60 years of age Bilirubin/ SGOT/SGPT < 5 × upper normal limits. Creatinine < 2 × upper normal limits. Ejection fraction = 50%, no severe arrhythmia. Estimated life expectancy = 6 months. Patients' CMV-DNA = 1000cp/ml in treatment group and being negative in prophylactic group.", "candidate_expression": "((Bilirubin < 5 × upper normal limits) AND (CMV-DNA) AND (Creatinine < 2 × upper normal limits) AND (Ejection fraction = 50%) AND (Estimated life expectancy = 6 months) AND (SGOT < 5 × upper normal limits) AND (SGPT < 5 × upper normal limits) AND (age = 14 years) AND (age = 60 years) AND (allogeneic stem cell transplant) AND (prophylactic group negative) AND (treatment group = 1000cp/ml) AND NOT (arrhythmia severe))"}
{"candidate_id": "LLM03315", "doc_id": "NCT03208127_exc", "case_bucket": "or", "source_criterion": "Pregnant or nursing (lactating) women HIV positivity Need for dual organ transplant Any contra-indication to liver transplantation per center protocol", "candidate_expression": "((HIV) AND (HIV positivity) AND (Need for) AND (Pregnant) AND (contra-indication) AND (dual organ transplant) AND (lactating) AND (liver transplantation) AND (nursing) AND (positivity) AND (women))"}
{"candidate_id": "LLM03316", "doc_id": "NCT03387059_inc", "case_bucket": "or", "source_criterion": "All infertile women treated with intracytoplasmic sperm injection (ICSI)/Fertilization in Vitro and Embryo Transfer (FIVET) Less than or equal to (<=) 1 previous failed embryo transfer Eumenorrheic normo-gonadotropic women Basal follicle-stimulating hormone (FSH) <=12 International unit per liter (IU/L) Anti-mullerian hormone (AMH) greater than (>) 1.1 nanogram per milliliter (ng/mL) Ovarian Reserve: number of antral follicles 2 millimeter (mm) between 6 <= antral follicle count (AFC) <= 16 Follicles > 16 mm at the triggering day between 5-14 Body Mass Index (BMI) between 18 <= BMI <= 27 kilogram per meter square (kg/m^2) Indication for Fresh Embryo transfer Normal uterine cavity on ultrasound exam (e.g., no presence of hydrosalpinx) Undergoing Assisted Reproductive Technique (ART) and oocyte maturation by human chorionic gonadotropin (HCG) triggering Progesterone (P4) serum level at the HCG triggering day <= 1.5 ng/mL (Day O/Randomization) Estradiol (E2) <= 3000 picogram/milliliter (pg/mL) at the human chorionic gonadotropin (HCG) triggering day (Day 0/Randomization) Subjects must have read and signed the Informed Consent Form prior to study-specific-procedures not part of standard of care Other protocol defined inclusion criteria could apply", "candidate_expression": "((Anti-mullerian hormone (AMH) greater than (>) 1.1 nanogram per milliliter (ng/mL)) AND (Assisted Reproductive Technique (ART)) AND (Basal follicle-stimulating hormone (FSH) <=12 International unit per liter (IU/L)) AND (Body Mass Index (BMI) between 18 <= BMI <= 27 kilogram per meter square (kg/m^2)) AND (Day 0/Randomization) AND (Estradiol (E2) <= 3000 picogram/milliliter (pg/mL) at the human chorionic gonadotropin (HCG) triggering day Day O/Randomization) AND (Eumenorrheic) AND (Fertilization in Vitro and Embryo Transfer (FIVET)) AND (Follicles > 16 mm at the triggering day between 5-14) AND (Fresh Embryo transfer Indication for) AND (Progesterone (P4) serum level at the HCG triggering day) AND (Subjects must have read and signed the Informed Consent Form prior to study-specific-procedures not part of standard of care) AND (human chorionic gonadotropin (HCG) triggering) AND (infertile) AND (intracytoplasmic sperm injection (ICSI)) AND (normo-gonadotropic) AND (number of antral follicles 2 millimeter (mm) between 6 <= antral follicle count (AFC) <= 16) AND (oocyte maturation) AND (previous failed embryo transfer Less than or equal to (<=) 1) AND (ultrasound exam Normal uterine cavity) AND (women) AND NOT (hydrosalpinx))"}
{"candidate_id": "LLM03317", "doc_id": "NCT02680054_inc", "case_bucket": "other", "source_criterion": "Diagnosis of Type 1 diabetes (for at least a year) On multiple daily insulin injections, including basal long-acting insulin and rapid-acting insulin before each meal. HbA1c < 75 mmol/mol (9.0%) Participant and/or parent/legal guardian willing and able to give informed consent for participation in the study. Family have a freezer in which to safely store the test meals. In the Investigator's opinion, is able and willing to comply with all trial requirements.", "candidate_expression": "((HbA1c < 75 mmol/mol 9.0%) AND (In the Investigator's opinion, is able and willing to comply with all trial requirements) AND (Participant and/or parent/legal guardian willing and able to give informed consent for participation in the study) AND (Type 1 diabetes at least a year) AND (insulin basal long-acting) AND (insulin daily) AND (insulin rapid-acting))"}
{"candidate_id": "LLM03318", "doc_id": "NCT02318446_exc", "case_bucket": "or", "source_criterion": "Pregnancy and lactation Patients with diabetes, Ischemic heart disease (IHD), stroke, malignancy and psychiatric diseases are excluded from study. The patients receiving vitamin supplements or who had clinical evidence for an acute illness, renal dysfunction, thyroid dysfunction, chronic inflammatory diseases, inborn errors of homocysteine, cobalamin or folate metabolism, or any other condition known to interfere with homocysteine metabolism will be excluded Patients who are already involved in any other trial. Patients not willing to fill consent/ assent form are also excluded from study.", "candidate_expression": "((Ischemic heart disease (IHD)) AND (Patients not willing to fill consent/ assent form are also excluded from study.) AND (Pregnancy) AND (acute illness) AND (chronic inflammatory diseases) AND (clinical evidence for an acute illness) AND (condition known to interfere with homocysteine metabolism) AND (diabetes) AND (inborn errors of cobalamin metabolism) AND (inborn errors of folate metabolism) AND (inborn errors of homocysteine metabolism) AND (lactation) AND (malignancy) AND (psychiatric diseases) AND (renal dysfunction) AND (stroke) AND (thyroid dysfunction) AND (vitamin supplements))"}
{"candidate_id": "LLM03319", "doc_id": "NCT02656394_exc", "case_bucket": "or", "source_criterion": "1. Comorbidity with other severe or chronic eye conditions that in the judgment of the investigator will interfere with study assessments, such as corneal opacities and scars, dystrophies, epithelial scarring, infections, blood clots, etc. 2. Best corrected visual acuity (BCVA) at baseline <20/200. 3. Has a condition or history that, in the opinion of the investigator, may interfere significantly with the subject's participation in the study. 4. A woman who is pregnant, nursing an infant, or planning a pregnancy. 5. Has a known adverse reaction and/or sensitivity to the study drug or its components. 6. Routine use (more than twice a week) of a chlorinated swimming pool. 7. Unwilling or unable to cease using the following medications during the study period: Topical ocular cyclosporine (e.g. Restasis®), anti-histamines, antipsychotics, or eye gels. 8. Currently enrolled in an investigational drug or device study or have used an investigational drug or device within 30 days prior to Visit 1.", "candidate_expression": "((<20/200) AND (Best corrected visual acuity (BCVA)) AND (Restasis®) AND (Routine use) AND (Topical ocular cyclosporine) AND (Unwilling or unable) AND (Visit 1) AND (adverse reaction to the study drug or its components) AND (anti-histamines) AND (antipsychotics) AND (at baseline) AND (baseline) AND (blood clots) AND (chlorinated swimming pool) AND (corneal opacities) AND (corneal scars) AND (during the study period) AND (dystrophies) AND (epithelial scarring) AND (eye conditions) AND (eye gels) AND (in the judgment of the investigator) AND (in the opinion of the investigator) AND (infections) AND (investigational device) AND (investigational drug) AND (may interfere significantly) AND (more than twice a week) AND (nursing) AND (pregnancy) AND (pregnant) AND (sensitivity to the study drug or its components) AND (study period) AND (will interfere with study assessments) AND (within 30 days prior to Visit 1) AND (woman))"}
{"candidate_id": "LLM03320", "doc_id": "NCT02863120_exc", "case_bucket": "or", "source_criterion": "Revision total knee arthroplasty Bilateral total knee arthroplasty Patients with inflammatory arthritis Patients with a body mass index (BMI) > 40 Allergy to ropivacaine, bupivacaine, or other local anesthetic agents Current use of opioid drugs Patients with a history of total or unicompartmental reconstruction of the affected joint Patients that have had a high tibial osteotomy or femoral osteotomy Patients with neuromuscular or neurosensory deficiency, which would limit the ability to assess pain levels Patients with a systemic or metabolic disorder leading to progressive bone deterioration Patients that are immunologically compromised, or receiving chronic steroids (>30 days), excluding inhalers Patients' bone stock is compromised by disease or infection, which cannot provide adequate support and/or fixation to the prosthesis Patients with knee fusion to the affected joint Patients with an active or suspected latent infection in or about the knee joint Patients that are prisoners", "candidate_expression": "((Allergy) AND (BMI) AND (Bilateral total knee arthroplasty) AND (Revision total knee arthroplasty) AND (body mass index > 40) AND (bone deterioration progressive) AND (bupivacaine) AND (femoral osteotomy) AND (high tibial osteotomy) AND (immunologically compromised) AND (infection knee joint) AND (inflammatory arthritis) AND (knee fusion) AND (local anesthetic agents) AND (metabolic disorder) AND (neuromuscular deficiency) AND (neurosensory deficiency) AND (opioid total) AND (prisoners) AND (reconstruction affected joint unicompartmental) AND (ropivacaine) AND (steroids chronic >30 days) AND (systemic disorder) AND NOT (inhalers))"}
{"candidate_id": "LLM03321", "doc_id": "NCT02260206_inc", "case_bucket": "or", "source_criterion": "Patients needed to pericardiocentesis during RFCA for paroxysmal or persistent atrial fibrillation.", "candidate_expression": "((RFCA) AND (atrial fibrillation) AND (during RFCA) AND (paroxysmal) AND (pericardiocentesis) AND (persistent))"}
{"candidate_id": "LLM03322", "doc_id": "NCT02566226_inc", "case_bucket": "other", "source_criterion": "physical status I - III patients scheduled to undergo hip arthroplasty", "candidate_expression": "((hip arthroplasty scheduled to undergo) AND (physical status I - III))"}
{"candidate_id": "LLM03323", "doc_id": "NCT03481894_exc", "case_bucket": "or", "source_criterion": "Known hypersensitivity to egg, soybean proteins, peanut proteins, corn or corn products, or to any of the active substances or excipients Severe hyperlipidemia or severe disorders of lipid metabolism characterized by hypertriglyceridemia (serum triglyceride concentration >1,000 g/dL). Inborn errors of amino acid metabolism Cardiopulmonary instability (including pulmonary edema, cardiac insufficiency, myocardial infarction, acidosis and hemodynamic instability requiring significant vasopressor support) Hemophagocytic syndrome. PN in the last 7 days prior to study enrollment. Need for chronic PN before study start Liver enzymes (either AST, ALT, GGPT), or direct bilirubin exceeding 2 x upper limit of normal range Pathologically altered level of any serum electrolyte (sodium, potassium, magnesium, calcium, chloride, phosphate) unless corrected prior to the start of study treatment Pathologically altered blood pH, or oxygen saturation, or carbon dioxide unless corrected prior to the start of study treatment Pregnancy or lactation Participation in another clinical study", "candidate_expression": "((>1,000 g/dL) AND (ALT) AND (AST) AND (Cardiopulmonary instability) AND (GGPT) AND (Hemophagocytic syndrome) AND (Inborn errors of amino acid metabolism) AND (Liver enzymes) AND (PN) AND (Participation in another clinical study) AND (Pathologically altered) AND (Pregnancy) AND (Severe) AND (acidosis) AND (active substances) AND (before study start) AND (blood pH) AND (calcium) AND (carbon dioxide) AND (cardiac insufficiency) AND (chloride) AND (chronic PN) AND (corn) AND (corn products) AND (direct bilirubin) AND (disorders of lipid metabolism) AND (egg) AND (exceeding 2 x upper limit of normal range) AND (excipients) AND (hemodynamic instability) AND (hyperlipidemia) AND (hypersensitivity) AND (hypertriglyceridemia) AND (in the last 7 days prior to study enrollment) AND (lactation) AND (level of any serum electrolyte) AND (magnesium) AND (myocardial infarction) AND (oxygen saturation) AND (peanut proteins) AND (phosphate) AND (potassium) AND (pulmonary edema) AND (serum triglyceride concentration) AND (severe) AND (significant) AND (sodium) AND (soybean proteins) AND (study enrollment) AND (study start) AND (vasopressor) AND (vasopressor support))"}
{"candidate_id": "LLM03324", "doc_id": "NCT02557386_inc", "case_bucket": "scope", "source_criterion": "Male sex ASA status I or II BMI between 20 and 34 kg/m2 Cruciate ligament of the knee reconstructive surgery No contraindications to general and regional anesthesia", "candidate_expression": "((ASA status I or II) AND (BMI between 20 and 34 kg/m2) AND (Male) AND (general anesthesia) AND (reconstructive surgery Cruciate ligament of the knee) AND (regional anesthesia) AND NOT (contraindications))"}
{"candidate_id": "LLM03325", "doc_id": "NCT02831166_exc", "case_bucket": "or", "source_criterion": "Less than 18 years of age; Pregnancy; Chronic use of vitamin K antagonists or direct thrombin inhibitors, or oral Xa-factor antagonists; Hypersensitivity to antiplatelet and/or anticoagulant drugs; Active bleeding or high bleeding risk (severe liver failure, active peptic ulcer, creatinine clearance < 30 mL/min, platelets count < 100.000 mm3); Uncontrolled systemic hypertension; Cardiogenic shock; Previous myocardial revascularization surgery with = 1 internal mammary or radial artery graft; Documented chronic peripheral arterial disease preventing the use of the femoral technique; Severe concomitant disease with life expectancy below 12 months; Participation in drug or devices investigative clinical trials in the last 30 days; Medical, geographic or social conditions impairing the participation in the study or inability to understand and sign the informed consent term.", "candidate_expression": "((< 100.000 mm3) AND (< 30 mL/min) AND (= 1) AND (Active) AND (Cardiogenic shock) AND (Chronic) AND (Hypersensitivity) AND (Less than 18 years) AND (Medical, geographic or social conditions impairing the participation in the study or inability to understand and sign the informed consent term.) AND (Pregnancy) AND (Previous) AND (Severe) AND (Uncontrolled) AND (active) AND (age) AND (below 12 months) AND (chronic) AND (concomitant) AND (disease) AND (femoral technique) AND (life expectancy) AND (myocardial revascularization surgery) AND (peripheral arterial disease) AND (preventing) AND (severe) AND (systemic hypertension) AND ((anticoagulant drugs) OR (antiplatelet drugs)) AND ((bleeding) OR (creatinine clearance) OR (high bleeding risk) OR (liver failure) OR (peptic ulcer) OR (platelets count)) AND ((internal mammary graft) OR (radial artery graft)) AND ((direct thrombin inhibitors) OR (oral Xa-factor antagonists) OR (vitamin K antagonists)))"}
```
