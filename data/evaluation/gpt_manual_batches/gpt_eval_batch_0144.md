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
{"candidate_id": "LLM03576", "doc_id": "NCT02566928_inc", "case_bucket": "or", "source_criterion": "between 7 to 70 years of age fluent in English or Spanish plans to receive care in the Community Health Center during the next year presents with signs and symptoms of a SSTI willing/able to provide informed consent", "candidate_expression": "((Community Health Center) AND (SSTI) AND (age between 7 to 70 years) AND (fluent in English) AND (fluent in Spanish) AND (receive care plans to during the next year) AND (willing/able to provide informed consent) AND ((signs) OR (symptoms)))"}
{"candidate_id": "LLM03577", "doc_id": "NCT02918851_inc", "case_bucket": "other", "source_criterion": "Habitual exerciser defined as = 30 minutes of at least moderate or high intensity exercise = 3 times per week. After consent, and at the subsequent screening visit, a VO2 max test will be performed, and subjects with a low value (< 35 mL/kg/min) will be excluded (screen failure). Based on our previous experience, we anticipate that <10% of the subjects will fall into this category Men: (0.006012 x H3) + (14.6 x W) + 604 = TBV Women: (0.005835 x H3) + (15 x W) + 183 = TBV [H=height in inches; W=weight in pounds] Has access to transportation to visit the blood collection facility and to return to Stony Brook for all study visits.", "candidate_expression": "(((0.005835 x H3) + (15 x W) + 183) AND ((0.006012 x H3) + (14.6 x W) + 604 =) AND (Men) AND (TBV) AND (Women))"}
{"candidate_id": "LLM03578", "doc_id": "NCT03561753_inc", "case_bucket": "or", "source_criterion": "Newly diagnosed and untreated sputum smear positive tuberculosis patient Pulmonary lesion consistent with TB by radiological examination Positive sputum culture, identification of bacterial type confirmed Mycobacterium tuberculosis. MGIT drug sensitivity test (DST) results are sensitive of the first-line drugs (isoniazid, streptomycin, rifampicin and ethambutol). Age 18 years-65 years old Males or non-pregnant, non-nursing females Serum or plasma aminotransferases (AST, ALT) less than 3 times the upper limit of normal Serum or plasma total bilirubin less than or equal to 2.5 times the upper limit of normal Serum or plasma creatinine level less than or equal to 2 times the upper limit of normal Serum or plasma potassium level greater than or equal to 3.5 meq/L Hemoglobin level of 7.0 g/dL or greater Platelet count of 100,000/mm3 or greater For women of childbearing potential, a negative pregnancy test is required during screening Provides written informed consent Willingness and ability to attend scheduled follow-up visits and undergo study assessments.", "candidate_expression": "((Age 18 years-65 years old) AND (Hemoglobin level 7.0 g/dL or greater) AND (MGIT drug sensitivity test (DST) sensitive of the first-line drugs (isoniazid, streptomycin, rifampicin and ethambutol)) AND (Males) AND (Mycobacterium tuberculosis bacterial type) AND (Platelet count 100,000/mm3 or greater) AND (Pulmonary lesion consistent with TB) AND (TB) AND (ability to attend scheduled follow-up visits) AND (ability to undergo study assessments) AND (childbearing potential) AND (creatinine level less than or equal to 2 times the upper limit of normal) AND (females) AND (first-line drugs) AND (potassium level greater than or equal to 3.5 meq/L) AND (pregnancy test negative during screening) AND (radiological examination) AND (sputum culture Positive) AND (sputum smear positive) AND (to attend scheduled follow-up visits Willingness) AND (to undergo study assessments Willingness) AND (total bilirubin less than or equal to 2.5 times the upper limit of normal) AND (tuberculosis) AND (women) AND (written informed consent) AND NOT (pregnant) AND NOT (nursing) AND ((Newly diagnosed) OR (untreated)) AND ((ethambutol) OR (isoniazid) OR (rifampicin) OR (streptomycin)) AND ((ALT) OR (AST)) AND ((Serum aminotransferases) OR (plasma aminotransferases)) AND ((Serum) OR (plasma)))"}
{"candidate_id": "LLM03579", "doc_id": "NCT01117181_inc", "case_bucket": "or", "source_criterion": "Possible or probable Alzheimer's disease (National Institute of Neurological and Communicative Disorders and Stroke - Alzheimer's Disease and Related Disorders Association (NINCDS-ADRDA) criteria), with Mini-Mental State Exam (MMSE) score of 10-26 inclusive; MMSE scores above 26 in those who nevertheless meet criteria for AD may be allowed with Steering Committee approval on a case by case basis Clinically significant apathy for at least four weeks for which either 1) the frequency of apathy as assessed by the Neuropsychiatric Inventory (NPI) is 'Very frequently', or 2) the frequency of apathy as assessed by the NPI is 'Frequently' or 'Often' AND the severity of apathy as assessed by the NPI is 'Moderate' or 'Marked' A medication for apathy is appropriate, in the opinion of the study physician Provision of informed consent for participation in the study by patient or surrogate (if the patient is unable to provide informed consent) and caregiver Availability of primary caregiver, who spends greater than ten hours a week with the patient and supervises his/her care, to accompany the patient to study visits and to participate in the study Sufficient fluency, of both the patient and caregiver, in written and spoken English to participate in study visits, physical exams, and outcome assessments No change to AD medications within the month preceding randomization, including starting, stopping, or dosage modifications Treatment with stable doses of selective serotonin reuptake inhibitor antidepressants(SSRIs) is appropriate if stable for 3 months prior to randomization. Other psychotropics(with the exclusion of antipsychotics), if stable for 3 months, may be allowed only with Steering Committee approval on a case by case basis.", "candidate_expression": "((A medication for apathy is appropriate, in the opinion of the study physician) AND (AD) AND (AD medications) AND (Alzheimer's disease) AND (Availability of primary caregiver, who spends greater than ten hours a week with the patient and supervises his/her care, to accompany the patient to study visits and to participate in the study) AND (NPI) AND (National Institute of Neurological and Communicative Disorders and Stroke - Alzheimer's Disease and Related Disorders Association (NINCDS-ADRDA) criteria) AND (Neuropsychiatric Inventory (NPI) Very frequently) AND (Provision of informed consent for participation in the study by patient or surrogate (if the patient is unable to provide informed consent) and caregiver) AND (Sufficient fluency, of both the patient and caregiver, in written and spoken English to participate in study visits, physical exams, and outcome assessments) AND (Treatment) AND (apathy) AND (at least four weeks) AND (frequency of apathy) AND (medication for apathy) AND (selective serotonin reuptake inhibitor antidepressants(SSRIs) stable doses) AND (severity of apathy) AND NOT (change to AD medications within the month preceding randomization) AND ((Frequently) OR (Often)) AND ((Marked) OR (Moderate)) AND ((Possible) OR (probable)) AND ((MMSE scores above 26) OR (Mini-Mental State Exam (MMSE) score of 10-26 inclusive)))"}
{"candidate_id": "LLM03580", "doc_id": "NCT01518946_exc", "case_bucket": "or", "source_criterion": "1. The subject is a pregnant or lactating female. 2. The subject has pre-existing sustained supine hypertension greater than 180mmHg systolic and 110mmHg diastolic BP or had these measurements at the Screening Visit. Sustained is defined as persistently greater at 2 separate measurements at least 5 minutes apart with the subject supine and at rest for the 5 minutes. 3. Subjects taking concomitant medications of interest are excluded unless those medications are reviewed and discussed with the Medical Monitor or Study Physician and documented prior to enrolling the subject. If agreement is reached between the Investigator and Sponsor for the subject to continue in the study, all allowed medications should be maintained at a constant dose throughout the study. 4. The Principal Investigator deems any clinical laboratory test (at the Screening Visit) abnormality to be clinically significant 5. The subject has participated in other studies of investigational drugs or devices within 30 days prior to enrollment in this study (other than Study SPD426-406). 6. Current or relevant history of physical or psychiatric illness, any medical disorder that may require treatment or make the subject unlikely to fully comply with the requirements of the study or complete the study, or any condition that presents undue risk from the investigational product or study procedures. 7. The subject has a concurrent chronic or acute illness, disability, or other condition (including significant unexpected laboratory or electrocardiogram [ECG] findings) that might confound the results of the tests and/or measurements administered in this study, or that might have increased the risk to the subject. 8. Known or suspected intolerance or hypersensitivity to the investigational product(s), closely-related compounds, or any of the stated ingredients. 9. Prior enrollment failure or randomization in this study. 10. History of alcohol abuse or other substance abuse within the last year.", "candidate_expression": "((BP greater than 180mmHg systolic 110mmHg diastolic) AND (Current or relevant history of physical or psychiatric illness, any medical disorder that may require treatment or make the subject unlikely to fully comply with the requirements of the study or complete the study, or any condition that presents undue risk from the investigational product or study procedures.) AND (The Principal Investigator deems any clinical laboratory test (at the Screening Visit) abnormality to be clinically significant) AND (The subject has participated in other studies of investigational drugs or devices within 30 days prior to enrollment in this study (other than Study SPD426-406).) AND (electrocardiogram [ECG]) AND (electrocardiogram [ECG] findings) AND (enrollment failure) AND (female) AND (laboratory findings) AND (measurements 2 separate at least 5 minutes apart persistently greater) AND (medications of interest concomitant) AND (supine hypertension pre-existing) AND ((lactating) OR (pregnant)) AND ((acute illness) OR (chronic illness) OR (disability) OR (other condition)) AND ((alcohol abuse) OR (substance abuse)) AND ((at the Screening Visit Screening Visit) OR (sustained)))"}
{"candidate_id": "LLM03581", "doc_id": "NCT03366779_exc", "case_bucket": "or", "source_criterion": "Spondylolisthesis Grade II or higher. Subject requires uni or bilateral facetectomy to treat leg/back pain. Subject has back or non-radicular leg pain of unknown etiology. Prior surgery at the index lumbar level. Subject requiring a spine DEXA (i.e., patients with SCORE of = 6) with a T Score less than -2.0 at the index level. For patients with a herniation at L5/S1, the average T score of L1-L4 shall be used. Subject has clinically compromised vertebral bodies at the index level(s) due to any traumatic, neoplastic, metabolic, or infectious pathology. Subject has sustained pathologic fractures of the vertebra or multiple fractures of the vertebra or hip. Subject has scoliosis of greater than ten (10) degrees (both angular and rotational). Any metabolic disease bone disease that has not been stabilized for at least three months (e.g., Paget's disease, osteomalacia, osteogenesis imperfecta, thyroid and/or parathyroid gland disorder, etc.). Subject has an active infection either systemic or local. Subject has cauda equina syndrome or neurogenic bowel/bladder dysfunction. Subject has severe arterial insufficiency of the legs (Screening on physical examination= patients with diminution or absence of dorsalis pedis or posterior tibialis pulses. If diminished or absent by palpation, then an arterial ultrasound is required with vascular plethysmography. If the absolute arterial pressure is below 50mm of Hg at the calf or ankle level, then the patient is to be excluded) or other peripheral vascular disease). Subject has significant peripheral neuropathy, patient defined as a patient with Type I or Type II diabetes or similar systemic metabolic condition causing decreased sensation in a stocking-like or non-radicular and non-dermatomal distribution in the lower extremities. Subject has insulin-dependent diabetes mellitus. Subject is morbidly obese (defined as a body mass index >40, or weighs more than 100 lbs over ideal body weight). Subject has been diagnosed with active hepatitis, AIDS, or HIV. Subject has been diagnosed with rheumatoid arthritis or other autoimmune disease. Subject has a known allergy to titanium, polyethylene or polyester materials. Subject is pregnant or interested in becoming pregnant in the next two (2) years. Subject has active tuberculosis or has had tuberculosis in the past three (3) years. Subject has a history of active malignancy: A patient with a history of any invasive malignancy (except non-melanoma skin cancer), unless he/she has been treated with curative intent and there have been no signs or symptoms of the malignancy for at least two (2) years. Subject is immunologically suppressed, received steroids >1 month over the past year. Currently taking anticoagulants, other than aspirin, unless the patient can be taken off the anticoagulant for surgery. Subject has a current chemical/alcohol dependency or significant psychosocial disturbance. Subject has a life expectancy of less than three (3) years. Subject is currently involved in another investigational study. Subject is incarcerated.", "candidate_expression": "((Grade II or higher) AND (SCORE = 6) AND (Screening on physical examination) AND (Spondylolisthesis) AND (Subject is currently involved in another investigational study.) AND (T Score less than -2.0 index level) AND (absolute arterial pressure below 50mm of Hg) AND (active malignancy history) AND (allergy) AND (anticoagulants) AND (arterial insufficiency severe legs) AND (arterial ultrasound) AND (average T score L1-L4) AND (clinically compromised vertebral bodies index level(s)) AND (decreased sensation lower extremities) AND (diabetes mellitus insulin-dependent) AND (facetectomy) AND (fractures of the vertebra pathologic) AND (herniation L5/S1) AND (incarcerated) AND (infection active) AND (life expectancy less than three (3) years) AND (malignancy invasive) AND (morbidly obese) AND (palpation) AND (peripheral neuropathy significant) AND (peripheral vascular disease) AND (scoliosis greater than ten (10) degrees) AND (spine DEXA requiring) AND (surgery Prior index lumbar level) AND (treated with curative intent) AND (vascular plethysmography) AND NOT (non-melanoma skin cancer) AND NOT (signs or symptoms of the malignancy for at least two (2) years) AND NOT (aspirin) AND ((non-dermatomal distribution) OR (non-radicular distribution) OR (stocking-like distribution)) AND ((body mass index >40) OR (weighs more than 100 lbs over ideal body weight)) AND ((AIDS) OR (HIV) OR (hepatitis)) AND ((back pain) OR (non-radicular leg pain)) AND ((autoimmune disease other) OR (rheumatoid arthritis)) AND ((polyester) OR (polyethylene) OR (titanium)) AND ((pregnant) OR (pregnant interested in becoming)) AND ((in the past three (3) years) OR (tuberculosis)) AND ((immunologically suppressed) OR (steroids >1 month over the past year)) AND ((alcohol dependency) OR (chemical dependency) OR (psychosocial disturbance significant)) AND ((infectious pathology) OR (metabolic pathology) OR (neoplastic pathology) OR (traumatic pathology)) AND ((bilateral) OR (uni)) AND ((fractures of the hip) OR (fractures of the vertebra)) AND ((angular) OR (rotational)) AND ((Paget's disease) OR (osteogenesis imperfecta) OR (osteomalacia) OR (parathyroid gland disorder) OR (thyroid)) AND ((bone disease) OR (metabolic disease)) AND ((local) OR (systemic)) AND ((cauda equina syndrome) OR (neurogenic bladder dysfunction) OR (neurogenic bowel dysfunction)) AND ((back pain) OR (pain leg)) AND ((diminution or absence of dorsalis pedis) OR (diminution or absence of posterior tibialis pulses)) AND ((ankle level) OR (calf level)) AND ((absent) OR (diminished)) AND ((Type I) OR (Type II)) AND ((diabetes) OR (systemic metabolic condition similar)))"}
{"candidate_id": "LLM03582", "doc_id": "NCT02807857_inc", "case_bucket": "other", "source_criterion": "Willing and able to provide written informed consent and accept study procedures and time schedule. Age = 18 years. Patients suffering from chronic heart failure (the heart failure diagnosis must have been made or confirmed by a cardiologist and/or hospital physician at any time in the patient's medical history). Patients with reduced ejection fraction (= 40%) as confirmed at any time point in the patient's medical history.", "candidate_expression": "((Age = 18 years) AND (Willing and able to provide written informed consent and accept study procedures and time schedule.) AND (chronic heart failure) AND (ejection fraction = 40%))"}
{"candidate_id": "LLM03583", "doc_id": "NCT02903407_exc", "case_bucket": "or", "source_criterion": "Exclusion criteria include patients following resuscitation from cardiac arrest who are treated on the cooling protocol patients who have suffered a neurologic event (seizure, stroke) or who have baseline dementia, both of which could limit delirium assessment patients with child class B and C liver disease patients with known allergy to study medications.", "candidate_expression": "((allergy) AND (child class) AND (cooling protocol) AND (liver disease) AND (resuscitation from cardiac arrest) AND (study medications) AND ((B) OR (C)) AND ((seizure) OR (stroke)) AND ((baseline dementia) OR (neurologic event)))"}
{"candidate_id": "LLM03584", "doc_id": "NCT03639545_inc", "case_bucket": "other", "source_criterion": "diabetes mellitus type 1", "candidate_expression": "(diabetes mellitus type 1)"}
{"candidate_id": "LLM03585", "doc_id": "NCT03025620_exc", "case_bucket": "other", "source_criterion": "Patients unable to understand the objectives of the dietary intervention Patients in paliative care Patients receiving supplement diets", "candidate_expression": "(EMPTY)"}
{"candidate_id": "LLM03586", "doc_id": "NCT02924090_inc", "case_bucket": "or", "source_criterion": "Adults patients aged 18 to 85 years Diagnosed with Major Depressive Disorder, unipolar or bipolar depression Undergoing ECT for treatment of their symptoms Currently residing in Manitoba", "candidate_expression": "((18 to 85 years) AND (Adults) AND (Currently residing) AND (ECT) AND (Major Depressive Disorder) AND (Manitoba) AND (Undergoing) AND (aged) AND (bipolar depression) AND (unipolar depression))"}
{"candidate_id": "LLM03587", "doc_id": "NCT02077556_exc", "case_bucket": "or", "source_criterion": "Pregnancy Tuberculosis Hepatitis B or C carrier status Human immunodeficiency virus-positive status Retransplantation or multiorgan transplantation History of rheumatoid arthritis Use of drugs that might have enhanced or inhibited CYP3A4 or P-gp activity", "candidate_expression": "((Human immunodeficiency virus positive) AND (Pregnancy) AND (Tuberculosis) AND (rheumatoid arthritis) AND ((Hepatitis B carrier) OR (Hepatitis C carrier)) AND ((Retransplantation) OR (transplantation multiorgan)))"}
{"candidate_id": "LLM03588", "doc_id": "NCT02902120_exc", "case_bucket": "or", "source_criterion": "Documented positive hepatitis B (HBV) surface antigen, and/or HBV DNA prior to enrollment Any prior exposure to HCV protease inhibitor therapy HIV co-infection if on a protease inhibitor based regimen Increase in creatinine of 15% or greater within one month (30 days) of the screening visit Evidence of hepatocellular carcinoma at the time of enrollment Liver disease caused by an etiology other than HCV F4 or decompensated cirrhotic patients Child Pugh class B or C AST or ALT >350 within 6 months prior to enrollment Albumin < 3g/dL at the time of enrollment Platelet count < 75 at the time of enrollment History of clinically significant allergy or adverse event with protease inhibitors Evidence of the acquisition of HCV at the time of or after transplantation Pregnant or breastfeeding women Cyclosporine; St. John's Wort; Efavirenz; Phenytoin; Carbamazepine; Bosentan; HIV protease inhibitors; modafinil; ketoconazole; or rifampin use within 7 days of enrollment Coadministration of more than 20 mg atorvastatin; 10 mg rosuvastatin; 20 mg of fluvastatin, lovastatin or simvastatin", "candidate_expression": "((30 days) AND (< 3g/dL) AND (< 75) AND (>350) AND (ALT) AND (AST) AND (Albumin) AND (B or C) AND (Bosentan) AND (Carbamazepine) AND (Child Pugh class) AND (Cyclosporine) AND (Efavirenz) AND (F4) AND (HBV DNA) AND (HCV) AND (HCV protease inhibitor therapy) AND (HIV co-infection) AND (HIV protease inhibitors) AND (Increase of 15% or greater) AND (Liver disease) AND (Phenytoin) AND (Platelet count) AND (Pregnant or breastfeeding women) AND (St. John's Wort) AND (acquisition of HCV) AND (adverse event) AND (allergy) AND (at the time of or after transplantation) AND (atorvastatin) AND (creatinine) AND (decompensated cirrhotic) AND (enrollment) AND (fluvastatin) AND (hepatitis B surface antigen) AND (hepatocellular carcinoma) AND (ketoconazole) AND (lovastatin) AND (modafinil) AND (more than 10 mg) AND (more than 20 mg) AND (other) AND (positive) AND (prior to enrollment) AND (protease inhibitor) AND (protease inhibitors) AND (rifampin) AND (rosuvastatin) AND (simvastatin) AND (transplantation) AND (within 6 months prior to enrollment) AND (within 7 days of enrollment) AND (within one month))"}
{"candidate_id": "LLM03589", "doc_id": "NCT02872935_exc", "case_bucket": "other", "source_criterion": "Non- English speakers Height < 4' 11\" BMI >40 Kg/ mm Antiemetic drug use in the 24 hours prior to cesarean delivery, Hypertensive diseases of pregnancy Chronic hypertension receiving antihypertensive treatment Any other physical or psychiatric condition that may impair their ability to cooperate with study data collection.", "candidate_expression": "((< 4' 11\") AND (>40 Kg/ mm) AND (Antiemetic drug) AND (Any other physical or psychiatric condition that may impair their ability to cooperate with study data collection.) AND (BMI) AND (Chronic hypertension) AND (Height) AND (Hypertensive diseases of pregnancy) AND (Non- English speakers) AND (antihypertensive treatment) AND (cesarean delivery) AND (in the 24 hours prior to cesarean delivery))"}
{"candidate_id": "LLM03590", "doc_id": "NCT02557386_exc", "case_bucket": "other", "source_criterion": "Chronic pain more than 3 months Drug abuse Chronic use of analgesic drugs (more than 3 months) Psychiatric illness Peripheral neuropathy Drug allergy Severe gastroesophageal reflux disease", "candidate_expression": "((Chronic) AND (Chronic pain) AND (Drug) AND (Drug abuse) AND (Peripheral neuropathy) AND (Psychiatric illness) AND (Severe) AND (allergy) AND (analgesic drugs) AND (gastroesophageal reflux disease) AND (more than 3 months))"}
{"candidate_id": "LLM03591", "doc_id": "NCT02209545_inc", "case_bucket": "or", "source_criterion": "Patients presenting for abdominal myomectomy with documented uterine fibroids on pelvic imaging (pelvic ultrasound or MRI) within in last 12 months Age = 18 years and = 50 years Pre-operative hemoglobin >8 g/dl Willing to have buccal administration of misoprostol or a placebo at least one hour pre-procedure. Ability to understand and the willingness to sign a written informed consent. Admissible medical/surgical history Can be previously treated with Depo-Lupron, Depo-Provera, or Oral Contraceptive pills Intraoperative use of vasopressin and uterine tourniquet is permissible Can have had prior Cesarean delivery", "candidate_expression": "((= 18 years and = 50 years) AND (>8 g/dl) AND (Admissible) AND (Age) AND (Pre-operative) AND (Willing to have) AND (abdominal myomectomy) AND (at least one hour pre-procedure) AND (buccal administration) AND (hemoglobin) AND (medical history) AND (operative) AND (pelvic imaging) AND (previously) AND (surgical history) AND (treated) AND (uterine fibroids) AND (within in last 12 months) AND ((misoprostol) OR (placebo)) AND ((Ability to understand a written informed consent) OR (willingness to sign a written informed consent)) AND ((Depo-Lupron) OR (Depo-Provera) OR (Oral Contraceptive pills)) AND ((MRI pelvic) OR (pelvic ultrasound)))"}
{"candidate_id": "LLM03592", "doc_id": "NCT02425774_inc", "case_bucket": "or", "source_criterion": "patients undergoing partial or full resection of the pancreas due to a benign or malignant tumor", "candidate_expression": "((benign tumor) AND (full resection of the pancreas) AND (malignant tumor) AND (partial resection of the pancreas))"}
{"candidate_id": "LLM03593", "doc_id": "NCT02673359_inc", "case_bucket": "or", "source_criterion": "Women with singleton pregnancy. History of preterm labor and/or midtrimester miscarriage in a previous pregnancy. Cervical length of 15-25 mm by transvaginal sonography (TVS) at 16-24 weeks of gestation.", "candidate_expression": "((15-25 mm) AND (16-24 weeks) AND (16-24 weeks of gestation) AND (Cervical length) AND (Women) AND (at 16-24 weeks of gestation) AND (gestation) AND (pregnancy) AND (previous) AND (singleton pregnancy) AND (transvaginal sonography (TVS)) AND ((midtrimester miscarriage) OR (preterm labor)))"}
{"candidate_id": "LLM03594", "doc_id": "NCT00279552_inc", "case_bucket": "other", "source_criterion": "Patients suspected to have vitamin B12 deficiency defined as a plasma vitamin B12 below the reference interval (<200 pmol/L).", "candidate_expression": "((<200 pmol/L) AND (below the reference interval) AND (plasma vitamin B12) AND (suspected) AND (vitamin B12 deficiency))"}
{"candidate_id": "LLM03595", "doc_id": "NCT03539718_exc", "case_bucket": "other", "source_criterion": "Patients with intercurrent infections. Patients with sepsis. Patients receiving drugs affecting immune system like immunosuppressive drugs. Patients on antibiotics.", "candidate_expression": "((antibiotics) AND (drugs affecting immune system) AND (immunosuppressive drugs) AND (intercurrent infections) AND (sepsis))"}
{"candidate_id": "LLM03596", "doc_id": "NCT03140423_exc", "case_bucket": "other", "source_criterion": "Exclusion criteria includes ICUs with an average length of stay of less than 2 days; HCA hospitals that are not able to transfer or merge data into the centralized data warehouse for the baseline and intervention periods of the study are also excluded.", "candidate_expression": "((ICUs) AND (average length of stay) AND (less than 2 days))"}
{"candidate_id": "LLM03597", "doc_id": "NCT00182520_inc", "case_bucket": "or", "source_criterion": "Outpatient with primary DSM- IV OCD Completion of a 14-week open label trial of one the following SRI's: fluoxetine 80 mg/day, paroxetine 60 mg/day, fluvoxamine 300 mg/day, clomipramine 250 mg/day, sertraline 200 mg/day, citalopram 60 mg/day, escitalopram 30 mg/day and demonstrating a non or partial responses to SRI treatment (CGI-I of 3 or 4, Y-BOCS reduction of < 35%) Stable (8 wks or longer) concurrent medications including benzodiazepines, sedative hypnotics, antipsychotics, and antidepressants.", "candidate_expression": "((OCD primary DSM- IV) AND (Outpatient) AND (SRI treatment) AND (medications Stable 8 wks or longer concurrent) AND (responses to) AND ((antidepressants) OR (antipsychotics) OR (benzodiazepines) OR (sedative hypnotics)) AND ((citalopram 60 mg/day) OR (clomipramine 250 mg/day) OR (escitalopram 30 mg/day) OR (fluoxetine 80 mg/day) OR (fluvoxamine 300 mg/day) OR (paroxetine 60 mg/day) OR (sertraline 200 mg/day)) AND ((CGI-I) OR (Y-BOCS reduction of < 35%)) AND ((3) OR (4)))"}
{"candidate_id": "LLM03598", "doc_id": "NCT02643381_inc", "case_bucket": "or", "source_criterion": "Adult patient (male or female) requiring emergency endotracheal intubation.", "candidate_expression": "((Adult) AND (emergency endotracheal intubation) AND ((female) OR (male)))"}
{"candidate_id": "LLM03599", "doc_id": "NCT02894268_exc", "case_bucket": "or", "source_criterion": "Bismuth compounds, acid inhibitor, or antibiotics during 4 weeks before the patient is enrolled Allergic to the medications Upper gastrointestinal surgery history Serious heart insufficiency, liver insufficiency, renal insufficiency and other serious medical problems Evidence of blood dyscrasia Pregnant and lactating women Can't express his complain correctly and can't cooperate with the researcher", "candidate_expression": "((Allergic) AND (Evidence) AND (Serious) AND (Upper gastrointestinal surgery) AND (blood dyscrasia) AND (during 4 weeks before the patient is enrolled) AND (history) AND (medications) AND (other) AND (the patient is enrolled) AND (women) AND ((Bismuth compounds) OR (acid inhibitor) OR (antibiotics)) AND ((heart insufficiency) OR (liver insufficiency) OR (renal insufficiency) OR (serious medical problems)) AND ((Pregnant) OR (lactating)))"}
{"candidate_id": "LLM03600", "doc_id": "NCT01116973_exc", "case_bucket": "or", "source_criterion": "Inability to obtain consent Subjects under 18 years of age Non-English speaking subjects Subjects that are unable to lay flat due to pulmonary complications, increased intracranial pressure (ICP), or unstable spinal cord injuries Subjects with known cardiac abnormalities (atrial septal defects or ventricular septal defects, severe tricuspid valve disease, severe pulmonary hypertension, Ejection fraction < 15%) Prisoners Subjects with known upper extremity deep vein thromboses (subclavian or distal) Subjects with non-functional CICC or PICC distal ports Subjects with femoral CICCs Pregnant women", "candidate_expression": "((Inability to obtain consent) AND (Pregnant) AND (Prisoners) AND (age under 18 years) AND (cardiac abnormalities) AND (femoral CICCs) AND (pulmonary complications) AND (upper extremity deep vein thromboses) AND (women) AND ((Ejection fraction < 15%) OR (atrial septal defects) OR (pulmonary hypertension severe) OR (tricuspid valve disease severe) OR (ventricular septal defects)) AND ((distal) OR (subclavian)) AND ((CICC distal ports) OR (PICC distal ports)) AND ((increased intracranial pressure (ICP)) OR (spinal cord injuries unstable) OR (unable to lay flat due to pulmonary complications)))"}
```
