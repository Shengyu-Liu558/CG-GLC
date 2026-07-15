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
{"candidate_id": "LLM01951", "doc_id": "NCT02833623_exc", "case_bucket": "or", "source_criterion": "advanced chronic disease that would not allow the patient to complete the treatment or follow-up or attend visits allergy to any of the drugs used in this study previous Helicobacter Pylori eradication treatment pregnancy or breastfeeding (female participants with childbearing potential were required to use medically accepted contraception for the duration of the study) taking antibiotics or PPIs or bismuth salts within four weeks previous gastrointestinal surgery", "candidate_expression": "((Helicobacter Pylori eradication treatment) AND (gastrointestinal surgery) AND (pregnancy or breastfeeding (female participants with childbearing potential were required to use medically accepted contraception for the duration of the study)) AND ((PPIs) OR (antibiotics) OR (bismuth salts)))"}
{"candidate_id": "LLM01952", "doc_id": "NCT02589353_exc", "case_bucket": "or", "source_criterion": "adults 61 years old and above smokers pregnant women taking any prescription pain/ insulin medication has a history of taste or smell loss or other oral disorders (e.g., burning mouth syndrome) has current oral lesions, canker sores, or piercings has a history of food allergy", "candidate_expression": "((adults) AND (and above 61 years) AND (burning mouth syndrome) AND (canker sores) AND (current) AND (food allergy) AND (history) AND (old) AND (oral disorders) AND (oral lesions) AND (other) AND (piercings) AND (pregnant) AND (prescription insulin medication) AND (prescription pain medication) AND (smell loss) AND (smokers) AND (taste loss) AND (women))"}
{"candidate_id": "LLM01953", "doc_id": "NCT03173092_exc", "case_bucket": "or", "source_criterion": "Failure to have fully recovered (that is, less than or equal to [<=] Grade 1 toxicity) from the reversible effects of prior chemotherapy. Major surgery within 14 days before enrollment. Radiotherapy within 14 days before enrollment (if the involved field is small, 7 days will be considered a sufficient interval between treatment and administration of the ixazomib.) Central nervous system involvement. Infection requiring systemic antibiotic therapy or other serious infection within 14 days before study enrollment. Evidence of current uncontrolled cardiovascular conditions, including uncontrolled hypertension, uncontrolled cardiac arrhythmias, symptomatic congestive heart failure, unstable angina, or myocardial infarction within the past 6 months. Systemic treatment, within 14 days before the first dose of ixazomib, with strong cytochrome P450 3A (CYP3A) inducers (rifampin, rifapentine, rifabutin, carbamazepine, phenytoin, phenobarbital), or use of Ginkgo biloba or St. John's wort. Ongoing or active systemic infection, active hepatitis B or C virus infection, or known human immunodeficiency virus positive. Diagnosed or treated for another malignancy within 2 years before study enrollment or previously diagnosed with another malignancy and have any evidence of residual disease. Participants with non-melanoma skin cancer or carcinoma in situ of any type are not excluded if they have undergone complete resection. Has greater than or equal to (>=) Grade 2 peripheral neuropathy, or Grade 1 with pain on clinical examination during the screening period. PD on first-line therapy. Participation in other interventional clinical trials, including those with other investigational agents not included in this trial, within 30 days of the start of this trial and throughout the duration of this trial. Non-interventional trials (that is, observational trials) are permitted at any time point.", "candidate_expression": "((C virus infection) AND (Central nervous system involvement) AND (Ginkgo biloba) AND (Infection) AND (Major surgery within 14 days before enrollment) AND (PD first-line therapy) AND (Participation in other interventional clinical trials) AND (Radiotherapy within 14 days before enrollment) AND (St. John's wort Ongoing active) AND (Systemic treatment within 14 days before the first dose of ixazomib) AND (carbamazepine) AND (carcinoma in situ any type) AND (cardiac arrhythmias uncontrolled) AND (cardiovascular conditions current uncontrolled) AND (chemotherapy) AND (congestive heart failure symptomatic) AND (hepatitis B virus infection) AND (human immunodeficiency virus positive) AND (hypertension uncontrolled) AND (infection other serious within 14 days before study enrollment) AND (involved field is small 7 days) AND (ixazomib) AND (malignancy previously another) AND (malignancy within 2 years before study enrollment) AND (myocardial infarction within the past 6 months) AND (non-melanoma skin cancer) AND (pain) AND (peripheral neuropathy greater than or equal to (>=) Grade 2 Grade 1) AND (phenobarbital) AND (phenytoin) AND (residual disease any evidence of) AND (rifabutin) AND (rifampin) AND (rifapentine) AND (strong cytochrome P450 3A (CYP3A) inducers) AND (systemic antibiotic therapy) AND (systemic infection) AND (throughout the duration of this trial the duration of this trial) AND (toxicity less than or equal to [<=] Grade 1) AND (unstable angina) AND (within 30 days of the start of this trial the start of this trial) AND NOT (fully recovered) AND NOT (complete resection))"}
{"candidate_id": "LLM01954", "doc_id": "NCT01884337_inc", "case_bucket": "or", "source_criterion": "Age =18 years Subjects undergoing elective total knee or hip replacement or a revision of at least one component of a total knee or hip replacement", "candidate_expression": "((=18 years) AND (Age) AND (a hip replacement revision of) AND (a total knee replacement revision of) AND (at least one component) AND (elective) AND (total hip replacement) AND (total knee replacement) AND (undergoing))"}
{"candidate_id": "LLM01955", "doc_id": "NCT00396734_inc", "case_bucket": "scope", "source_criterion": "Methadone-maintained cocaine-dependent patients use between 1g to 2g a day; 1 to 3 times a week", "candidate_expression": "((Methadone) AND (cocaine-dependent Methadone-maintained 1g to 2g a day 1 to 3 times a week))"}
{"candidate_id": "LLM01956", "doc_id": "NCT03372265_inc", "case_bucket": "or", "source_criterion": "Age = 18 years American Society of Anesthesiologists Classification I-III Normal cognitive function in order to sign written, informed consent and to understand trial protocol Agreement to the trial protocol, including the randomized manner", "candidate_expression": "((= 18 years) AND (Age) AND (American Society of Anesthesiologists Classification) AND (I-III) AND (Normal) AND (cognitive function) AND ((Agreement to the randomized manner) OR (Agreement to the trial protocol)))"}
{"candidate_id": "LLM01957", "doc_id": "NCT02202369_inc", "case_bucket": "other", "source_criterion": "Subjects undergoing a single level lumbar decompression and fusion > 18 years of age and < 70 years of age The subject is willing and able to understand, sign and date the study specific patient informed consent and HIPAA authorization to volunteer participation in the study", "candidate_expression": "((The subject is willing and able to understand, sign and date the study specific patient informed consent and HIPAA authorization to volunteer participation in the study) AND (age > 18 years and < 70 years) AND (lumbar decompression single level) AND (lumbar fusion single level))"}
{"candidate_id": "LLM01958", "doc_id": "NCT03208244_exc", "case_bucket": "other", "source_criterion": "Sensitization (i.e. PRA >20%) Any liver disease in recipient Albumin < 3g/dl or platelet count < 75 x 103/mL Need for dual organ transplant", "candidate_expression": "((< 3g/dl) AND (< 75 x 103/mL) AND (>20%) AND (Albumin) AND (Need for) AND (PRA) AND (Sensitization) AND (dual organ transplant) AND (liver disease) AND (platelet count))"}
{"candidate_id": "LLM01959", "doc_id": "NCT03329456_exc", "case_bucket": "or", "source_criterion": "Exclusion criteria are pregnancy, patients with contraindications to regional anesthesia, allergy to LAs, patients taking opioids regularly due to chronic pain, use of anticoagulation drugs other than acetylsalicylic acid or dipyridamole, atrioventricular block, diabetes.", "candidate_expression": "((LAs) AND (acetylsalicylic acid) AND (allergy) AND (anticoagulation drugs) AND (atrioventricular block) AND (chronic pain) AND (contraindications) AND (diabetes) AND (dipyridamole) AND (opioids regularly) AND (pregnancy) AND (regional anesthesia))"}
{"candidate_id": "LLM01960", "doc_id": "NCT03315975_inc", "case_bucket": "or", "source_criterion": "adults capable of providing consent have a diagnosis of locally advanced or metastatic melanoma", "candidate_expression": "((adults) AND (capable of providing consent) AND (locally advanced) AND (melanoma) AND (metastatic))"}
{"candidate_id": "LLM01961", "doc_id": "NCT02502734_inc", "case_bucket": "or", "source_criterion": "Aged 5 years to less than 12 years at Visit 1. At least 15 (25%) children of the total study population must be aged 5 to less than 8 years. Male or pre-menarchial female subjects. Subjects must be pre-adolescent without any signs of puberty (Tanner Stage 1). Normal range for their height and weight. Weight and height measurements should fall within the percentile range 3-97% of normal values for age according to Danish growth charts. Have a documented diagnosis of persistent asthma, as defined by the National Institutes of Health for at least 3 months prior to the Screening Visit. A pre-bronchodilatory forced expiratory flow in 1 second (FEV1) at Visit 1 (Screening) >=80% predicted. There should be no Short acting beta-agonist (SABA) use within 4 hours of this measurement. Using one of the following asthma therapies prior to entry into the study: SABA inhaler alone (e.g. salbutamol) on an as required basis and/or Regular non-inhaled corticosteroid (ICS) controller medications for asthma (e.g. cromones or leukotriene receptor antagonists) and/or Previously treated with ICS (equipotent to inhaled budesonide <=400 micrograms (mcg) total daily dose). There must be no ICS use within 2 weeks of Visit 1 (Screening). Able to replace their current SABA treatment with study supplied rescue SABA provided at Visit 1 for use as needed for the duration of the study. Written informed consent from at least one parent/care giver (legal guardian) and accompanying informed assent from the subject (where the subject is able to provide assent) prior to admission to the study: (1) If applicable, subject must be able and willing to give assent to take part in the study according to the local requirement. The study investigator is accountable for determining a child's capacity to assent to participation in a research study, taking into consideration any standards set by the responsible independent ethics committee (IEC). (2) Subject and their legal guardian(s) understand that the study requires them to be treated on an outpatient basis. (3) Subject and their legal guardian(s) understand that they must comply with study medication and study assessments including recording of peak expiratory flow and rescue SABA use, attending scheduled study visits, and being accessible by a telephone call.", "candidate_expression": "(((3) Subject and their legal guardian(s) understand that they must comply with study medication and study assessments including recording of peak expiratory flow and rescue SABA use, attending scheduled study visits, and being accessible by a telephone call.) AND (1) AND (5 years to less than 12 years) AND (<=400 micrograms (mcg)) AND (>=80% predicted) AND (Able to replace their current SABA treatment with study supplied rescue SABA provided at Visit 1 for use as needed for the duration of the study.) AND (Aged) AND (ICS) AND (Male) AND (Normal range) AND (SABA) AND (SABA inhaler) AND (Screening Visit) AND (Short acting beta-agonist (SABA)) AND (Tanner Stage) AND (The study investigator is accountable for determining a child's capacity to assent to participation in a research study, taking into consideration any standards set by the responsible independent ethics committee (IEC).) AND (Visit 1) AND (Visit 1 (Screening)) AND (Weight) AND (Written informed consent from at least one parent/care giver (legal guardian) and accompanying informed assent from the subject (where the subject is able to provide assent) prior to admission to the study: (1) If applicable, subject must be able and willing to give assent to take part in the study according to the local requirement.) AND (as defined by the National Institutes of Health) AND (asthma therapies) AND (at Visit 1) AND (at Visit 1 (Screening)) AND (at least 3 months prior to the Screening Visit) AND (budesonide) AND (entry into the study) AND (female) AND (forced expiratory flow in 1 second (FEV1)) AND (height) AND (no) AND (persistent asthma) AND (pre-adolescent) AND (pre-bronchodilatory) AND (pre-menarchial) AND (prior to entry into the study) AND (rescue SABA) AND (salbutamol) AND (signs of puberty) AND (this measurement) AND (weight) AND (within 2 weeks of Visit 1 (Screening)) AND (within 4 hours of this measurement) AND (within the percentile range 3-97%) AND (without any) AND ((ICS) OR (cromones) OR (leukotriene receptor antagonists)))"}
{"candidate_id": "LLM01962", "doc_id": "NCT03471117_inc", "case_bucket": "or", "source_criterion": "CKD patients classified as Stage 3 and 4 of National Kidney Foundation Classification with estimated glomerular filtration rate (GFR) between 15 and 59 mL/min/1.73 m2 according to the Modification of Diet in Renal Disease (MDRD) formula based on serum creatinine, age, gender, and race. Men and women 35 to 70 years of age", "candidate_expression": "((35 to 70 years) AND (CKD) AND (Men) AND (Modification of Diet in Renal Disease (MDRD) formula) AND (National Kidney Foundation Classification) AND (Stage 3) AND (Stage 4) AND (age) AND (between 15 and 59 mL/min/1.73 m2) AND (estimated glomerular filtration rate (GFR)) AND (women))"}
{"candidate_id": "LLM01963", "doc_id": "NCT02321839_exc", "case_bucket": "or", "source_criterion": "Total lesion area of >12 DA or >30.5 mm2 The existence of subretinal hemorrhage area constituting =50% of total lesion area The existence of scar or fibrosis area constituting =50% of total lesion area The existence of RPE tear Prior treatment for wet AMD History of vitrectomy surgery, submacular surgery, or other surgical intervention for AMD The pregnant or lactating woman", "candidate_expression": "((AMD) AND (RPE tear Prior) AND (Total lesion area >12 DA >30.5 mm2) AND (fibrosis area) AND (lactating) AND (pregnant) AND (scar area) AND (submacular surgery) AND (subretinal hemorrhage area =50% of total lesion area) AND (surgical intervention other) AND (treatment) AND (vitrectomy surgery) AND (woman))"}
{"candidate_id": "LLM01964", "doc_id": "NCT02550080_exc", "case_bucket": "or", "source_criterion": "Has previously received Dapsone therapy. The subject or any of their healthcare providers is aware of the subjects HLA type. Has been diagnosed with Glucose-6-phosphate dehydrogenase deficiency or methemoglobin reductase deficiency Satisfies any contraindications or restrictions to Dapsone therapy as listed in the product labels. Current severe illness, including heart, liver and renal failure, major organ allograft, malignancy requiring parenteral chemotherapy that can not be discontinued for the duration of the trial, or any other conditions which, in the opinion of the Investigator, would make the patient unsuitable for the study. Any laboratory abnormality at Screening which, in the opinion of the Investigator, should preclude the subject's participation in the study [alanine aminotransferase (ALT), glutamic oxaloacetic transaminase(ALT), et al). Pregnant women or women who are breastfeeding. Subject is, in the opinion of the Investigator, unable to complete the 6 week Observation period and the EPT assessments as required. A positive result for HLA-B*1301 in those subjects randomised to the genetic screening arm.", "candidate_expression": "((Dapsone) AND (Glucose-6-phosphate dehydrogenase deficiency) AND (HLA-B*1301 positive) AND (chemotherapy) AND (contraindications) AND (heart failure) AND (liver failure) AND (major organ allograft) AND (malignancy) AND (methemoglobin reductase deficiency) AND (regnant women or women who are breastfeeding) AND (renal failure))"}
{"candidate_id": "LLM01965", "doc_id": "NCT01064752_inc", "case_bucket": "other", "source_criterion": "1. HIV infection with plasma and CSF HIV RNA concentrations (using Roche Amplicor assay) > 1,000 copies/ mL (available after baseline LP). 2. Off antiretroviral therapy (ART) for > 6 weeks before the study and no plans to begin treatment for the study duration. (The decision of whether or not a subject takes antiretroviral therapy will be made by the subject in consultation with his/her primary care provider prior to screening for this study.) 3. Predicted adherence to the medication. 4. Capable of providing informed consent. 5. > 18 years old 6. CD4 cell counts >150 cells/μL (though likely most, if not all, will be >250 cells/μL). 7. When available, subjects will be screened for stability of blood CD4 and HIV RNA levels.", "candidate_expression": "((CD4 cell counts >150 cells/μL >250 cells/μL) AND (CSF HIV RNA concentration > 1,000 copies/ mL) AND (Capable of providing informed consent.) AND (HIV infection) AND (Off antiretroviral therapy (ART) > 6 weeks before the study) AND (Roche Amplicor assay) AND (antiretroviral therapy (ART)) AND (old 18 years) AND (plasma concentration > 1,000 copies/ mL) AND (treatment plans to begin for the study duration study))"}
{"candidate_id": "LLM01966", "doc_id": "NCT02393287_exc", "case_bucket": "other", "source_criterion": "1. Presence of other neoplasia 2. Man", "candidate_expression": "((Man) AND (neoplasia) AND (other))"}
{"candidate_id": "LLM01967", "doc_id": "NCT00728156_inc", "case_bucket": "or", "source_criterion": "Patients with T2DM and CAS as defined below: Clinical definitions T2DM: Diagnosed according to the WHO criteria [53]. CAD:Presence of any one of the following: Angina plus positive exercise tolerance test, enzyme and/or Q wave positive myocardial infarction, angiographic evidence ( >50% stenosis of one vessel), percutaneous or surgical coronary revascularisation. Aged between 18 and 75 Provided written consent for participation in the trial prior to any study-specific procedures or requirements.", "candidate_expression": "((>50%) AND (Aged) AND (Angina) AND (CAD) AND (CAS) AND (Q wave positive) AND (T2DM) AND (WHO criteria) AND (angiographic evidence) AND (any study-specific procedures or requirements) AND (between 18 and 75) AND (coronary revascularisation) AND (enzyme positive) AND (exercise tolerance test) AND (myocardial infarction) AND (percutaneous) AND (positive) AND (prior to any study-specific procedures or requirements) AND (stenosis of one vessel) AND (surgical) AND (written consent for participation in the trial))"}
{"candidate_id": "LLM01968", "doc_id": "NCT03297125_inc", "case_bucket": "other", "source_criterion": "Newly diagnosed glioblastoma (GBM), WHO grade IV.", "candidate_expression": "((GBM) AND (WHO grade IV) AND (glioblastoma Newly diagnosed))"}
{"candidate_id": "LLM01969", "doc_id": "NCT02689089_inc", "case_bucket": "or", "source_criterion": "Males or non-pregnant, non-nursing females between the ages of 2-65 years LTBI diagnosis as per Canadian TB Standards using either the Tuberculin Skin Test (TST) or the Interferon Gamma Release Assay (IGRA) Children 2-5 years with negative TSTs who have been in close contact with a case of active TB disease recently Able and willing to provide fully informed consent or parent/guardian able to provide consent", "candidate_expression": "((Able and willing to provide fully informed consent or parent/guardian able to provide consent) AND (Children) AND (IGRA) AND (Interferon Gamma Release Assay) AND (LTBI) AND (Males) AND (TST) AND (TSTs negative) AND (Tuberculin Skin Test) AND (ages 2-65 years) AND (females) AND (non-pregnant, non-nursing) AND (years 2-5))"}
{"candidate_id": "LLM01970", "doc_id": "NCT02777580_exc", "case_bucket": "or", "source_criterion": "1. Expected performance of PCI < 60 minutes from diagnosis (qualifying ECG) or inability to arrive at the catheterisation laboratory within 3 hours Previous CABG Left bundle branch block or ventricular pacing Patients with cardiogenic shock - Killip Class 4 Patients with a body weight < 55 kg (known or estimated) Uncontrolled hypertension, defined as sustained blood pressure = 180/110 mm Hg (systolic BP = 180 mm Hg and/or diastolic BP = 110 mm Hg) prior to randomisation Known prior stroke or TIA Recent administration of any i.v. or s.c. anticoagulation within 12 hours, including unfractionated heparin, enoxaparin, and/or bivalirudin or current use of oral anticoagulation (i.e. warfarin or a NOACs) Active bleeding or known bleeding disorder/diathesis Known history of central nervous system damage (i.e. neoplasm, aneurysm, intracranial or spinal surgery) or recent trauma to the head or cranium (i.e. < 3 months) Major surgery, biopsy of a parenchymal organ, or significant trauma within the past 2 months (this includes any trauma associated with the current myocardial infarction) Clinical diagnosis associated with increased risk of bleeding including known active peptic ulceration and/or neoplasm with increased bleeding risk Prolonged cardiopulmonary resuscitation (> 2 minutes) within the past 2 weeks Known acute pericarditis and/or subacute bacterial endocarditis Known acute pancreatitis or known severe hepatic dysfunction, including hepatic failure, cirrhosis, portal hypertension (oesophageal varices) and active hepatitis Dementia Known severe renal insufficiency Previous enrolment in this study or treatment with an investigational drug or device under another study protocol in the past 7 days Known allergic reactions to tenecteplase, clopidogrel, enoxaparin and aspirin Inability to follow the protocol and comply with follow-up requirements or any other reason that the investigator feels would place the patient at increased risk if the investigational therapy is initiated.", "candidate_expression": "((4) AND (< 3 months) AND (< 55 kg) AND (< 60 minutes from diagnosis) AND (= 110 mm Hg) AND (= 180 mm Hg) AND (= 180/110 mm Hg) AND (CABG) AND (Dementia) AND (Inability to follow the protocol and comply with follow-up requirements or any other reason that the investigator feels would place the patient at increased risk if the investigational therapy is initiated) AND (Killip Class) AND (PCI) AND (Previous enrolment in this study or treatment with an investigational drug or device under another study protocol in the past 7 days) AND (Prolonged) AND (Uncontrolled) AND (active) AND (allergic reactions) AND (anticoagulation) AND (blood pressure) AND (body weight) AND (cardiogenic shock) AND (cardiopulmonary resuscitation) AND (central nervous system damage) AND (diagnosis) AND (hypertension) AND (increased) AND (myocardial infarction) AND (oesophageal varices) AND (parenchymal organ) AND (past 2 months) AND (past 2 weeks) AND (renal insufficiency) AND (risk of bleeding) AND (severe) AND (significant) AND (trauma) AND (within 12 hours) AND ((diastolic BP) OR (systolic BP)) AND ((TIA) OR (stroke)) AND ((bivalirudin) OR (enoxaparin) OR (oral anticoagulation) OR (unfractionated heparin)) AND ((NOACs) OR (warfarin)) AND ((Active bleeding) OR (bleeding disorder) OR (diathesis)) AND ((aneurysm) OR (intracranial surgery) OR (neoplasm) OR (spinal surgery)) AND ((cranium) OR (head)) AND ((Major surgery) OR (biopsy) OR (trauma)) AND ((Left bundle branch block) OR (ventricular pacing)) AND ((neoplasm) OR (peptic ulceration)) AND ((acute pericarditis) OR (subacute bacterial endocarditis)) AND ((acute pancreatitis) OR (hepatic dysfunction)) AND ((active hepatitis) OR (cirrhosis) OR (hepatic failure) OR (portal hypertension)) AND ((aspirin) OR (clopidogrel) OR (enoxaparin) OR (tenecteplase)))"}
{"candidate_id": "LLM01971", "doc_id": "NCT02227992_inc", "case_bucket": "or", "source_criterion": "Paediatric subjects aged =28 days (= 1 month) to <18 years, requiring non-emergent open hepatic, abdominal, retroperitoneal, pelvic or thoracic (non-cardiac) surgical procedures. i) The first 36 subjects to be enrolled will be subjects aged =1 years to <18 years. ii) The next 4 subjects to be enrolled will be subjects aged =28 days to <1 year. The subject's parent/legal guardian must be willing to give permission for the subject to participate in the trial, and provide written informed consent for the subject. In addition, assent must be obtained from paediatric subjects who possess the intellectual and emotional ability to comprehend the concepts involved in the trial. If the paediatric subject is not able to provide assent (due to age, maturity and/or inability to intellectually and/or emotionally comprehend the trial), the parent/legal guardian's written Informed Consent for the subject will be acceptable for the subject to be included in the study. Presence of an appropriate mild or moderate bleeding soft tissue or hepatic parenchyma Target Bleeding Site (TBS) identified intra-operatively by the surgeon; Ability to firmly press trial treatment at TBS until 4 minutes after randomisation", "candidate_expression": "((=28 days (= 1 month) to <18 years) AND (Ability to firmly press trial treatment at TBS until 4 minutes after randomisation) AND (The subject's parent/legal guardian must be willing to give permission for the subject to participate in the trial, and provide written informed consent for the subject. In addition, assent must be obtained from paediatric subjects who possess the intellectual and emotional ability to comprehend the concepts involved in the trial. If the paediatric subject is not able to provide assent (due to age, maturity and/or inability to intellectually and/or emotionally comprehend the trial), the parent/legal guardian's written Informed Consent for the subject will be acceptable for the subject to be included in the study) AND (aged) AND (non-emergent) AND (open) AND (surgical procedures) AND ((abdominal) OR (hepatic) OR (non-cardiac) OR (pelvic) OR (retroperitoneal) OR (thoracic)))"}
{"candidate_id": "LLM01972", "doc_id": "NCT02986659_inc", "case_bucket": "or", "source_criterion": "Age 65 - 79 History of coronary artery disease (MI/heart attack, stroke, heart failure, or peripheral artery disease) Cancer, with no active treatment in the last year MCI (MoCA >18<26 -inclusive of 1 point if <12 years of education Group 2 Decline physical function (walking speed < 1 m/s) Group 3 (Either or both) Abdominal obesity (>88cm women, >102cm men) AND hypertension (treated or resting blood pressure >140/90 Abdominal obesity (>88cm women, >102cm men) AND hyperlipidemia (treated or fasting total cholesterol >240 English literacy Willing to provide informed consent", "candidate_expression": "((65 - 79) AND (< 1 m/s) AND (>102cm) AND (>140/90) AND (>18<26) AND (>240) AND (>88cm) AND (Abdominal) AND (Abdominal obesity) AND (Age) AND (Cancer) AND (Decline physical function) AND (English literacy) AND (History) AND (MCI) AND (MoCA) AND (Willing to) AND (active treatment) AND (coronary artery disease) AND (hyperlipidemia) AND (hypertension) AND (in the last year) AND (no) AND (provide informed consent) AND (walking speed) AND ((men) OR (women)) AND ((resting blood pressure) OR (treated)) AND ((fasting total cholesterol) OR (treated)) AND ((MI) OR (heart attack) OR (heart failure) OR (peripheral artery disease) OR (stroke)))"}
{"candidate_id": "LLM01973", "doc_id": "NCT03663387_inc", "case_bucket": "or", "source_criterion": "Male and female subjects between 40-85 years old will be enrolled. Younger subjects are not included as the risk for brain amyloid lesions is too low All subjects will speak English as their first language or demonstrate proficiency in English (defined as reaching a scaled score of > 11 on the WAIS vocabulary test). All subjects will have normal cognition at baseline: a Clinical Dementia Rating CDR=0, Global Deterioration Scale GDS<2. All subjects will be in good general health and able to participate in the LP and imaging exams. This determination is made by the study neurologist and reviewed at a consensus meeting for each subject.", "candidate_expression": "((<2) AND (=0) AND (> 11) AND (Clinical Dementia Rating CDR) AND (Global Deterioration Scale GDS) AND (LP) AND (WAIS vocabulary test) AND (able to participate) AND (at baseline) AND (between 40-85 years) AND (first language) AND (good general health) AND (imaging exams) AND (normal cognition) AND (old) AND ((Male) OR (female)) AND ((proficiency in English) OR (speak English)))"}
{"candidate_id": "LLM01974", "doc_id": "NCT02419378_exc", "case_bucket": "or", "source_criterion": "Participation in another clinical trial at present or within 4 weeks of study entry. There may be exceptions at the discretion of the Investigator. Has any progressive form of MS Hypersensitivity to the active substance, or to any of the excipients of Lemtrada® Medical, psychiatric, cognitive, or other conditions that, in the Investigator's opinion, compromise the patient's ability to understand the patient information, to give informed consent, to comply with the trial protocol, or to complete the study Any disability acquired from trauma or another illness that could interfere with evaluation of disability due to MS Major systemic disease or other illness that would, in the opinion of the Investigator, compromise patient safety or interfere with the interpretation of study results, e.g., current peptic ulcer disease or other conditions that may predispose to hemorrhage Known bleeding disorder (e.g,. dysfibrinogenemia, factor IX deficiency, hemophilia, Von Willebrand's disease, disseminated intravascular coagulation (DIC), fibrinogen deficiency, or clotting factor deficiency) Significant autoimmune disease including but not limited to immune cytopenias, rheumatoid arthritis, systemic lupus erythematosus, other connective tissue disorders, vasculitis, inflammatory bowel disease, severe psoriasis History of malignancy, except basal skin cell carcinoma Major psychiatric disorder that is not adequately controlled by treatment Epileptic seizures that are not adequately controlled by Treatment Active infection, e.g., deep-tissue infection, that the Investigator considers sufficiently serious to preclude study participation In the Investigator's opinion, is at high risk for infection (e.g., indwelling catheter, dysphagia with aspiration, decubitus ulcer, history of prior aspiration pneumonia or recurrent urinary tract infection) Seropositivity for human immunodeficiency virus (HIV) Infection with hepatitis C Virus Past or present hepatitis B infection (positive hepatitis B serology) Active infection with human cytomegaly virus (HCMV), Epstein-Barr virus (EBV), varicella-zoster virus (VZV) Latent tuberculosis unless effective anti-tuberculosis therapy has been completed, or active tuberculosis. Invasive fungal infections in history and at present Cervical cytology other than PAP I or PAP II (Papanicolaou) or cervical high risk human papillomavirus (HPV) positivity Any other illness or infection (latent or active) that, in the Investigator's opinion, could be exacerbated by study medication Differential blood count < lower limit of normal (LLN) at Screening Confirmed platelet count < the LLN of the evaluating laboratory at Screening or documented at <100,000/µL within the past year on a sample without platelet clumping Presence (i.e., above the ULN) of anti-thyroid stimulating hormone receptor antibodies (anti-TSHR) and anti-thyroid peroxidase antibody (anti-TPO) Vaccination less than 6 weeks prior to treatment with Lemtrada. Treatment with antineoplastic or immunosuppressive drugs within 8 weeks prior to study inclusion Intolerance of pulsed corticosteroids, especially a history of steroid psychosis Inability to undergo MRI with gadolinium administration Of childbearing potential with a positive serum pregnancy test, pregnant or lactating Female patients of childbearing potential: Unwilling to agree to use a reliable and acceptable contraceptive method (Pearl index <1) throughout the study period. These methods include: hormone releasing intrauterine device (IUD), hormonal-based contraception, surgical sterilization, abstinence, or double-barrier contraception (condom and occlusive cap [diaphragm or cervical cap combined with spermicide]).", "candidate_expression": "((Any disability acquired from trauma or another illness that could interfere with evaluation of disability due to MS) AND (Cervical cytology positivity human papillomavirus) AND (DIC) AND (Differential blood count < lower limit of normal (LLN) at Screening) AND (Epileptic seizures adequately controlled) AND (Female) AND (HIV) AND (HPV) AND (Hypersensitivity) AND (Inability to undergo MRI) AND (Infection hepatitis C Virus) AND (Lemtrada) AND (MRI Inability to) AND (MS progressive) AND (Major systemic disease or other illness that would, in the opinion of the Investigator, compromise patient safety or interfere with the interpretation of study results, e.g., current peptic ulcer disease or other conditions that may predispose to hemorrhage) AND (Medical, psychiatric, cognitive, or other conditions that, in the Investigator's opinion, compromise the patient's ability to understand the patient information, to give informed consent, to comply with the trial protocol, or to complete the study) AND (Participation) AND (Unwilling to agree to use a reliable and acceptable contraceptive method (Pearl index <1) throughout the study period. These methods include: hormone releasing intrauterine device (IUD), hormonal-based contraception, surgical sterilization, abstinence, or double-barrier contraception (condom and occlusive cap [diaphragm or cervical cap combined with spermicide])) AND (Vaccination less than 6 weeks prior to treatment with Lemtrada) AND (above the ULN) AND (active) AND (anti-thyroid peroxidase antibody (anti-TPO)) AND (anti-thyroid stimulating hormone receptor antibodies (anti-TSHR)) AND (anti-tuberculosis therapy completed VZV) AND (articipation in another clinical trial at present or within 4 weeks of study entry. There may be exceptions at the discretion of the Investigator) AND (aspiration) AND (autoimmune disease) AND (bleeding disorder) AND (childbearing potential) AND (deep-tissue infection) AND (fungal infections Invasive) AND (gadolinium) AND (hepatitis B infection) AND (hepatitis B serology positive) AND (human immunodeficiency virus Seropositivity) AND (infection Active) AND (infection Active HCMV EBV) AND (malignancy) AND (platelet count Confirmed sample without platelet clumping) AND (psychiatric disorder Major adequately controlled) AND (pulsed corticosteroids) AND (risk for infection high) AND (serum pregnancy test positive) AND (study medication) AND (treatment) AND NOT (basal skin cell carcinoma) AND ((< the LLN of the evaluating laboratory at Screening) OR (<100,000/µL within the past year)) AND ((Treatment) OR (within 8 weeks prior to study inclusion study inclusion)) AND ((antineoplastic drugs) OR (immunosuppressive drugs)) AND ((Intolerance) OR (steroid psychosis history of)) AND ((Von Willebrand's disease) OR (clotting factor deficiency) OR (disseminated intravascular coagulation) OR (dysfibrinogenemia) OR (factor IX deficiency) OR (fibrinogen deficiency) OR (hemophilia)) AND ((childbearing potential) OR (lactating) OR (pregnant)) AND ((connective tissue disorders) OR (immune cytopenias,) OR (inflammatory bowel disease) OR (psoriasis severe) OR (rheumatoid arthritis,) OR (systemic lupus erythematosus) OR (vasculitis)) AND ((aspiration pneumonia) OR (decubitus ulcer) OR (dysphagia) OR (indwelling catheter) OR (urinary tract infection recurrent)) AND ((Epstein-Barr virus) OR (human cytomegaly virus) OR (varicella-zoster virus)) AND ((Latent tuberculosis) OR (active tuberculosis)) AND ((PAP I) OR (PAP II) OR (Papanicolaou)) AND ((illness) OR (infection)) AND ((active) OR (latent)))"}
{"candidate_id": "LLM01975", "doc_id": "NCT02715518_inc", "case_bucket": "or", "source_criterion": "Symptoms of ischaemia. New or presumed new significant ST-T wave changes Development of pathological Q waves on ECG. Imaging evidence of new or presumed new loss of viable myocardium or regional wall motion abnormality.", "candidate_expression": "((ECG) AND (Imaging) AND (ST-T wave changes significant) AND (evidence new presumed new) AND (ischaemia Symptoms New presumed new) AND (loss of viable myocardium) AND (pathological Q waves) AND (regional wall motion abnormality))"}
```
