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
{"candidate_id": "LLM01876", "doc_id": "NCT00904202_inc", "case_bucket": "or", "source_criterion": "1. Had a diagnosis of PHN, DN, CRPS, carpal tunnel syndrome, HIV neuropathy, idiopathic sensory neuropathy, or other peripheral neuropathy (upon mutual agreement of the sponsor and investigator) 2. Patients with PHN must have had pain >3 months after rash healing 3. Patients with DN must have had Type I or II diabetes and painful distal symmetric sensorimotor polyneuropathy with or without dynamic allodynia of the lower extremities 4. Patients with CRPS must have met current IASP (International Association for the Study of Pain) diagnostic criteria 5. Patients with carpal tunnel syndrome must have had a diagnosis by combination clinical neurological examination (e.g., Phalen's and Tinel's signs), electrodiagnostic testing, and daily painful symptoms of at least 3 months' duration 6. Patients with HIV neuropathy must have had HIV, subjective symptoms of painful peripheral neuropathy, and daily painful symptoms of at least 3 months' duration 7. Patients with idiopathic sensory neuropathy must have had pain of at least 3 months' duration 8. Reached an average daily pain rating during the baseline week of pain ratings greater than 4 on the 0-to-10 numerical pain rating scale (Question 5 of the BPI) 9. Had never received an analgesic regimen that contained lidocaine or gabapentin", "candidate_expression": "((0-to-10 numerical pain rating scale) AND (CRPS) AND (DN) AND (HIV) AND (HIV neuropathy) AND (IASP (International Association for the Study of Pain) diagnostic criteria met) AND (PHN) AND (Phalen's signs) AND (Tinel's signs) AND (Type I diabetes) AND (Type II diabetes) AND (analgesic regimen) AND (carpal tunnel syndrome) AND (clinical neurological examination) AND (daily pain rating average during the baseline week greater than 4 baseline week) AND (dynamic allodynia) AND (electrodiagnostic) AND (idiopathic sensory neuropathy) AND (neuropathy) AND (pain >3 months after rash healing) AND (pain at least 3 months' duration) AND (painful symptoms daily at least 3 months' duration) AND (peripheral neuropathy painful) AND (rash healing rash healing) AND (sensorimotor polyneuropathy painful distal symmetric) AND (subjective symptoms) AND (upon mutual agreement of the sponsor and investigator) AND ((CRPS) OR (DN) OR (HIV neuropathy) OR (PHN) OR (carpal tunnel syndrome) OR (peripheral neuropathy) OR (sensory neuropathy idiopathic)) AND ((gabapentin) OR (lidocaine)))"}
{"candidate_id": "LLM01877", "doc_id": "NCT02790593_inc", "case_bucket": "or", "source_criterion": "Age >18 years old 1cm squared surface area Venous incompetence confirmed by clinical assessment and duplex ultrasound scan No evidence of arterial disease (Arterial Duplex or Ankle Brachial Pressure Index >0.9) Patients able to complete trial procedures Patients with a life expectancy of greater than 1 year", "candidate_expression": "((Age >18 years old) AND (Ankle Brachial Pressure Index >0.9) AND (Arterial Duplex) AND (Patients able to complete trial procedures) AND (Venous incompetence) AND (clinical assessment) AND (duplex ultrasound scan) AND (life expectancy greater than 1 year) AND (surface area 1cm squared) AND NOT (arterial disease))"}
{"candidate_id": "LLM01878", "doc_id": "NCT01579604_exc", "case_bucket": "or", "source_criterion": "Unstable patient Joint contracture Spasticity Loss of function is expected to be improved by reliable tendon transfer, tenodesis or arthrodesis that is available Evidence of recovering finger/thumb extension at 4-6 months Greater than 12 months from spinal cord injury Subject not fluent in English or an appropriate translator not available", "candidate_expression": "((Greater than 12 months) AND (Joint contracture) AND (Loss of function) AND (Spasticity) AND (Subject not fluent in English or an appropriate translator not available) AND (Unstable) AND (at 4-6 months) AND (improved by) AND (patient) AND (recovering extension) AND (spinal cord injury) AND ((finger) OR (thumb)) AND ((arthrodesis) OR (tendon transfer) OR (tenodesis)))"}
{"candidate_id": "LLM01879", "doc_id": "NCT01943812_inc", "case_bucket": "or", "source_criterion": "Endometrial thickness = 7 mm after stimulation 18-45 years IVF/ICSI fertilisation BMI > 18,5 <30 kg/m2 cycle length 25-34 days", "candidate_expression": "((18-45) AND (25-34 days) AND (= 7 mm) AND (> 18,5 <30 kg/m2) AND (BMI) AND (Endometrial thickness) AND (after stimulation) AND (cycle length) AND (stimulation) AND (years) AND ((ICSI fertilisation) OR (IVF fertilisation)))"}
{"candidate_id": "LLM01880", "doc_id": "NCT03176316_inc", "case_bucket": "other", "source_criterion": "Patients will be included if they are having an in-patient spinal fusion procedure, are 18 years or older, post and post-operative pain control plan includes opioid medications.", "candidate_expression": "((in-patient) AND (opioid) AND (pain control plan post-operative) AND (spinal fusion procedure) AND (years 18 years or older))"}
{"candidate_id": "LLM01881", "doc_id": "NCT02675153_inc", "case_bucket": "other", "source_criterion": "moderate to severe Crohn's Disease (basic HBI = 7) with stenosis", "candidate_expression": "((Crohn's Disease moderate to severe) AND (basic HBI = 7) AND (stenosis))"}
{"candidate_id": "LLM01882", "doc_id": "NCT03026088_inc", "case_bucket": "or", "source_criterion": "18-80 year, male or female. Chronic Heart failure subjects with medical history of cardiac disease or other related cardiovascular disease. Left ventricular ejection fraction (LVEF) less than or equal to (=<) 40 percent (%). New York Heart Association (NYHA) class of II - IV NYHA II : Slight limitation of physical activity. Comfortable at rest, but ordinary physical activity results in undue breathlessness, fatigue or palpitation. NYHA III:Marked limitation of physical activity. Comfortable at rest, but less than ordinary activity causes undue breathlessness, fatigue or palpitation. NYHA IV:Unable to carry on any physical activity without discomfort. Symptoms at rest can be present. If any physical activity is undertaken, discomfort increased. Signed Informed Consent Form (ICF).", "candidate_expression": "((Chronic Heart failure) AND (LVEF) AND (Left ventricular ejection fraction less than or equal to 40 percent) AND (NYHA) AND (New York Heart Association class II - IV) AND (Signed Informed Consent Form (ICF)) AND (year 18-80) AND ((female) OR (male)) AND ((cardiac disease) OR (cardiovascular disease related)))"}
{"candidate_id": "LLM01883", "doc_id": "NCT02678962_exc", "case_bucket": "or", "source_criterion": "Preexisting ocular diseases or conditions other than age related cataracts, have contraindications for cataract surgery; Preexisting systemic diseases or conditions that may confound the results of the study; Previous ocular surgery history or ocular trauma that may confound the results of the study; Require combined surgery that may confound the results of the study; Previous participation in other clinical trial within 30 days of this study start; Systemic or ocular medications that may confound the outcome of the intervention Pregnant, lactating, or planning to become pregnant during the course of the trial;", "candidate_expression": "((Preexisting) AND (Pregnant) AND (Previous) AND (Require) AND (Systemic medications) AND (age related) AND (cataract surgery) AND (cataracts) AND (combined surgery) AND (conditions) AND (contraindications) AND (during the course of the trial) AND (lactating) AND (may confound the outcome of the intervention) AND (may confound the results of the study) AND (ocular diseases) AND (ocular medications) AND (ocular surgery) AND (ocular trauma) AND (other than) AND (planning to become) AND (pregnant) AND (systemic diseases))"}
{"candidate_id": "LLM01884", "doc_id": "NCT03315975_exc", "case_bucket": "or", "source_criterion": "are allergic to influenza vaccination have received influenza vaccination within the past 6 months require prednisone, methotrexate, or other immunosuppressing medications have HIV infection have a history of solid organ or bone marrow transplant require combination immunotherapy are on other studies requiring blood draws that might exceed 450 mL total during the period of the influenza vaccine study", "candidate_expression": "((HIV infection) AND (allergic) AND (are on other studies requiring blood draws that might exceed 450 mL total during the period of the influenza vaccine study) AND (combination immunotherapy require) AND (influenza vaccination) AND (influenza vaccination within the past 6 months) AND ((bone marrow transplant) OR (solid organ transplant)) AND ((immunosuppressing medications other) OR (methotrexate) OR (prednisone)))"}
{"candidate_id": "LLM01885", "doc_id": "NCT03192020_inc", "case_bucket": "or", "source_criterion": "patients with =20° passive extension deficit (PED) in metacarpophalangeal (MP) or proximal interphalangeal (PIP) joint, or TPED of =30° in MP and PIP joints of finger/fingers II-V age > 18 years palpable cord provision of informed consent ability to fill the Finnish versions of questionnaires.", "candidate_expression": "((=20°) AND (=30°) AND (> 18 years) AND (MP) AND (PIP joints) AND (TPED) AND (age) AND (finger/fingers II-V) AND (palpable cord) AND (passive extension deficit (PED)) AND (provision of informed consent) AND ((joint metacarpophalangeal (MP)) OR (proximal interphalangeal (PIP) joint)))"}
{"candidate_id": "LLM01886", "doc_id": "NCT02687724_inc", "case_bucket": "or", "source_criterion": "Patients = 18 years of age Subjects must be able and willing to give written informed consent and to comply with the requirements of this study protocol Established diagnosis of UC and moderate-to-severe disease activity, defined as a Mayo score of 6-12, with an endoscopic subscore =2. Patients had an inadequate response to, or had failed to tolerate, 1 or more of the following conventional therapies: oral 5-aminosalicylates, oral corticosteroids, azathioprine (AZA), and/or 6-mercaptopurine (6MP); or corticosteroid dependent (ie, an inability to taper corticosteroids without recurrence of UC symptoms). Patients concurrently treated with oral 5-aminosalicylates or corticosteroids were to receive a stable dose for at least 2 weeks before baseline, and patients receiving AZA and/or 6MP were to receive a stable dose for at least 4 weeks before baseline. Patients were required to maintain stable doses of their concomitant UC medications during the study. Female subjects of child bearing potential must be willing to ensure that they or their partner use effective contraception during the study and for 6 months thereafter OR Surgical sterilized female patients with documentation of prior hysterectomy, tubal ligation or complete bilateral oophorectomy OR Postmenopausal women with postmenopausal defined as permanent cessation >1 year of previously occurring menses. Female subjects' serum pregnancy test performed at the screening visit and urine pregnancy test performed at the baseline visit must be negative. Subjects have following investigations within 1 month prior to enrolment. Routine bloods including U&E, FBC, LFTs, inflammatory markers (CRP) and albumin will be measured. Medical history, concomitant medications Intradermal reaction to Tuberculin (PPD skin test) or Mycobacterium tuberculosis antigenspecific interferon-gamma release assay (IGRA) TB screening: chest X-Ray unless performed in the last 6 months Stool examination for enteric pathogens including Clostridium difficile Inclusion/exclusion criteria Informed consent Mayo score (including sigmoidoscopy unless performed in previous 3 months) Patient's weight and height and abdominal circumference", "candidate_expression": "((6-mercaptopurine (6MP)) AND (6MP) AND (AZA) AND (FBC) AND (Female subjects of child bearing potential must be willing to ensure that they or their partner use effective contraception during the study and for 6 months thereafter OR) AND (Female subjects' serum pregnancy test performed at the screening visit and urine pregnancy test performed at the baseline visit must be negative.) AND (Intradermal reaction to Tuberculin (PPD skin test)) AND (LFTs) AND (Mayo score) AND (Mayo score 6-12) AND (Mycobacterium tuberculosis antigenspecific interferon-gamma release assay (IGRA)) AND (Postmenopausal women with postmenopausal defined as permanent cessation >1 year of previously occurring menses.) AND (Routine bloods within 1 month prior to enrolment) AND (Stool examination for enteric pathogens including Clostridium difficile) AND (Surgical sterilized female patients with documentation of prior hysterectomy, tubal ligation or complete bilateral oophorectomy OR) AND (TB screening) AND (U&E) AND (UC moderate-to-severe) AND (abdominal circumference) AND (age = 18 years) AND (albumin) AND (azathioprine (AZA)) AND (chest X-Ray) AND (corticosteroid) AND (corticosteroids) AND (dependent) AND (endoscopic subscore =2) AND (failed to tolerate) AND (height) AND (inadequate response) AND (inflammatory markers (CRP)) AND (oral 5-aminosalicylates) AND (oral corticosteroids) AND (sigmoidoscopy) AND (treated) AND (weight))"}
{"candidate_id": "LLM01887", "doc_id": "NCT02673359_inc", "case_bucket": "or", "source_criterion": "Women with singleton pregnancy. History of preterm labor and/or midtrimester miscarriage in a previous pregnancy. Cervical length of 15-25 mm by transvaginal sonography (TVS) at 16-24 weeks of gestation.", "candidate_expression": "((Cervical length 15-25 mm) AND (Women) AND (gestation 16-24 weeks) AND (midtrimester miscarriage) AND (pregnancy previous) AND (preterm labor) AND (singleton pregnancy) AND (transvaginal sonography (TVS) at 16-24 weeks of gestation))"}
{"candidate_id": "LLM01888", "doc_id": "NCT02426034_exc", "case_bucket": "or", "source_criterion": "Subjects with poor-controlled arterial hypertension (systolic blood pressure> 140 mmHg and diastolic blood pressure > 90 mm Hg) despite standard medical management; Coronary heart disease greater than ClassII; II-level arrhythmia (including QT interval prolongation, for man = 450 ms, for woman = 470 ms) together with Class II cardiac dysfunction; Factors that could have an effect on oral medication (such as inability to swallow, chronic diarrhea and intestinal obstruction); Subjects with high gastrointestinal bleeding risk, including the following conditions: local active ulcer lesions with positive fecal occult blood test (++); history of black stool, or vomiting blood in the past 3 months;unresected primary lesion in stomach with positive fecal occult blood test (+), ulcerated gastric carcinoma with massive alimentary tract bleeding risk judged by PIs based on gastric endoscopy result; Abnormal Coagulation (INR>1.5<U+3001>APTT>1.5 UNL), with tendency of bleed; Associated with CNS (central nervous system) metastases; Pregnant or lactating women; Other conditions regimented at investigators' discretion.", "candidate_expression": "((APTT >1.5 UNL) AND (Abnormal Coagulation) AND (Coronary heart disease greater than ClassII) AND (INR >1.5) AND (Pregnant or lactating women) AND (QT interval prolongation) AND (arrhythmia II-level) AND (arterial hypertension poor-controlled Subjects) AND (black stool) AND (cardiac dysfunction Class II) AND (chronic diarrhea) AND (diastolic blood pressure > 90 mm Hg) AND (fecal occult blood test positive +) AND (fecal occult blood test positive ++) AND (gastrointestinal bleeding risk high) AND (inability to swallow) AND (intestinal obstruction) AND (metastases CNS) AND (primary lesion stomach) AND (systolic blood pressure > 140 mmHg) AND (tendency of bleed) AND (ulcer lesions active) AND (ulcerated gastric carcinoma bleeding risk) AND (vomiting blood))"}
{"candidate_id": "LLM01889", "doc_id": "NCT02739295_exc", "case_bucket": "or", "source_criterion": "Toxic epidermal necrolysis with SCORTEN 6 or 7 at admission Hypercoagulable state Cardiac or peripheral arterial disease Active malignancy Myelodysplastic syndrome or hematological malignancy Fructose intolerance Pregnancy Patient refusal", "candidate_expression": "((Fructose) AND (Fructose intolerance) AND (Hypercoagulable state) AND (Myelodysplastic syndrome) AND (Patient refusal) AND (Pregnancy) AND (SCORTEN 6 or 7 at admission) AND (Toxic epidermal necrolysis) AND (disease Cardiac) AND (hematological malignancy) AND (malignancy Active) AND (peripheral arterial disease))"}
{"candidate_id": "LLM01890", "doc_id": "NCT02944929_exc", "case_bucket": "other", "source_criterion": "Patients who are unwilling to participate in the study. For the one under guardianship, the refusal of the patient will be the final decision even if the guardian is willing to participate. Subjects who are unlikely to adhere to the study an/or poor adherence anticipated by the investigator. Un-controlled progressive pathology. Osteoarticular lesion which contraindicates part of the rehabilitation involved in the study. Patients with other interventions planned prior to the end of the study period (orthosis, surgery etc.). Surgery to the treated limb less than 6 months previously. Pregnant woman.", "candidate_expression": "((Osteoarticular lesion) AND (Patients who are unwilling to participate in the study. For the one under guardianship, the refusal of the patient will be the final decision even if the guardian is willing to participate) AND (Pregnant woman) AND (Subjects who are unlikely to adhere to the study an/or poor adherence anticipated by the investigator) AND (Surgery) AND (less than 6 months) AND (treated limb))"}
{"candidate_id": "LLM01891", "doc_id": "NCT03369379_exc", "case_bucket": "or", "source_criterion": "Those subjects with previous use of vitamin D. Known subjects with renal, liver, calcium metabolism disorders, malabsorption disorders, known neoplasms. Subjects with serum calcium levels equal to or greater than 10.2 mg / dl.", "candidate_expression": "((calcium metabolism disorders) AND (disorders liver) AND (disorders renal) AND (malabsorption disorders) AND (neoplasms) AND (serum calcium levels equal to or greater than 10.2 mg / dl) AND (vitamin D previous use))"}
{"candidate_id": "LLM01892", "doc_id": "NCT02884401_inc", "case_bucket": "or", "source_criterion": "Participants must present a diagnosis of osteoporosis based on DXA measurement of the bone mineral density at the femur neck and/or total hip and/or lumbar spine (T value 2.5 SD or more below the young female adult mean) within the past 24 months. Not in treatment with anti-resorptive agents (like bisphosphonates and denosumab) for more than 4 consecutive years, in order to reduce the risk of medication-related osteonecrosis of the jaws (Lo et al., 2010). = 50 years old. In self-reported menopause, defined as the permanent cessation of ovulation, for at least one year (Soules et al., 2001). Edentulous area involving a maximum of two teeth (wisdom teeth and second molars are excluded) and presenting at least one neighbouring tooth (e.g. gap in the area of a second premolar and first molar, with first premolar in place). Residual alveolar width = 4 mm (Milinkovic and Cordaro, 2014), residual alveolar height >8 mm, enough inter-arch space for a crown (at least 5 mm) and a minimum distance of 7 mm from the adjacent teeth (Shah and Lum, 2008). The width and height will be confirmed after x-ray examination in Visit 2. Possibility to restore a functional occlusion with a minimum of four occlusal units (i.e. pairs of occluding posterior teeth). Willingness to replace the missing tooth/teeth with dental implants Registration with a GDP", "candidate_expression": "((2.5 SD or more below the young female adult mean) AND (= 4 mm) AND (= 50 years) AND (>8 mm) AND (DXA) AND (Not) AND (Possibility to restore a functional occlusion with a minimum of four occlusal units (i.e. pairs of occluding posterior teeth)) AND (Residual alveolar width) AND (T value) AND (Willingness to replace the missing tooth/teeth with dental implants) AND (anti-resorptive agents) AND (at least one year) AND (bisphosphonates) AND (bone mineral density) AND (cessation of ovulation) AND (denosumab) AND (femur neck) AND (lumbar spine) AND (menopause) AND (more than 4 consecutive years,) AND (old) AND (osteoporosis) AND (past 24 months) AND (permanent) AND (residual alveolar height) AND (total hip))"}
{"candidate_id": "LLM01893", "doc_id": "NCT01642875_exc", "case_bucket": "or", "source_criterion": "Metastatic tumor Locally unresectable tumor Previous gastric resection ASA IV-V Age under 18 years Preoperative complete parenteral or enteral feeding Immunosuppressive therapy before operation Severe malnutrition Lack of the patient's consent for the trial participation, feeding tube insertion or epidural analgesia", "candidate_expression": "((ASA) AND (Age) AND (IV-V) AND (Immunosuppressive therapy) AND (Lack of the patient's consent for the trial participation, feeding tube insertion or epidural analgesia) AND (Locally unresectable) AND (Metastatic) AND (Preoperative) AND (Previous) AND (Severe) AND (before operation) AND (gastric resection) AND (malnutrition) AND (operation) AND (tumor) AND (under 18 years) AND ((complete enteral feeding) OR (complete parenteral feeding)))"}
{"candidate_id": "LLM01894", "doc_id": "NCT00806936_inc", "case_bucket": "other", "source_criterion": "After the investigator has taken the decision to use human insulin or insulin analogues to treat the subject, any type 2 diabetic previously inadequately controlled with two or more OADs is eligible for the study The selection of the subjects will be at the discretion of the individual investigator", "candidate_expression": "((OADs two or more) AND (type 2 diabetic inadequately controlled))"}
{"candidate_id": "LLM01895", "doc_id": "NCT02678962_exc", "case_bucket": "or", "source_criterion": "Preexisting ocular diseases or conditions other than age related cataracts, have contraindications for cataract surgery; Preexisting systemic diseases or conditions that may confound the results of the study; Previous ocular surgery history or ocular trauma that may confound the results of the study; Require combined surgery that may confound the results of the study; Previous participation in other clinical trial within 30 days of this study start; Systemic or ocular medications that may confound the outcome of the intervention Pregnant, lactating, or planning to become pregnant during the course of the trial;", "candidate_expression": "((Preexisting) AND (Previous) AND (Require) AND (age related) AND (cataract surgery) AND (cataracts) AND (combined surgery) AND (during the course of the trial) AND (may confound the outcome of the intervention) AND (may confound the results of the study) AND (other than) AND (planning to become) AND ((conditions) OR (systemic diseases)) AND ((ocular surgery) OR (ocular trauma)) AND ((Systemic medications) OR (ocular medications)) AND ((Pregnant) OR (lactating) OR (pregnant)) AND ((conditions) OR (contraindications) OR (ocular diseases)))"}
{"candidate_id": "LLM01896", "doc_id": "NCT03062358_exc", "case_bucket": "or", "source_criterion": "Is currently participating or has participated in a study with an investigational agent or using an investigational device within 4 weeks of the first dose of study medication Has received sorafenib or oxaliplatin-based chemotherapy within 14 days of first dose of study medication Has had esophageal or gastric variceal bleeding within the last 6 months Has clinically apparent ascites on physical examination Has portal vein invasion at the main portal branch (Vp4), inferior vena cava, or cardiac involvement of HCC based on imaging Has had clinically diagnosed hepatic encephalopathy in the last 6 months Has had a solid organ or hematologic transplant Has had prior systemic therapy for HCC in the advanced (incurable) setting other than sorafenib or oxaliplatin-based chemotherapy, prior to start of study medication Has an active autoimmune disease that has required systemic treatment in the past 2 years. Replacement therapy is not considered a form of systemic treatment. Has a diagnosis of immunodeficiency or is receiving systemic steroid therapy or any other form of immunosuppressive therapy within 7 days prior to the first dose of study medication Has received locoregional therapy to liver (transcatheter chemoembolization [TACE], transcatheter embolization [TAE], hepatic arterial infusion [HAI], radiation, radioembolization, or ablation) or other site within 4 weeks prior to the first dose of study medication Has had major surgery to liver or other site within 4 weeks prior to the first dose of study medication Has had a minor surgery ≤7 days prior to the first dose of study medication Has not recovered adequately (i.e., Grade ≤1 or baseline) from the toxicity and/or complications from any intervention prior to study start Has a diagnosed additional malignancy within 3 years prior to first dose of study medication with the exception of curatively treated basal cell carcinoma of the skin, squamous cell carcinoma of the skin and/or curatively resected in situ cancers Has a known history of, or any evidence of, central nervous system (CNS) metastases and/or carcinomatous meningitis Has a history of (non-infectious) pneumonitis that required steroids or current pneumonitis Has an active infection requiring systemic therapy Is pregnant or breast feeding or expecting to conceive or father starting from the first dose of study medication, throughout the study period, and for up to 120 days after the last dose of study medication Has received prior immunotherapy with an anti-Programmed Cell Death Receptor 1 (PD-1), Programmed Cell Death Receptor Ligand 1 (anti-PD-L1), or anti- Programmed Cell Death Receptor Ligand 2 (PD-L2) or has previously participated in clinical studies with pembrolizumab Has a known history of human immunodeficiency virus (HIV) Has untreated active Hepatitis B Has hepatitis C in which participants received therapy for HCV <4 weeks prior to receiving pembrolizumab Has received a live vaccine within 30 days prior to the first dose of study therapy", "candidate_expression": "((30 days prior) AND (<4 weeks prior) AND (HCC) AND (Hepatitis B) AND (Programmed Cell Death Receptor Ligand 1 (anti-PD-L1)) AND (ablation) AND (active) AND (additional) AND (anti- Programmed Cell Death Receptor Ligand 2 (PD-L2)) AND (anti-Programmed Cell Death Receptor 1 (PD-1)) AND (ascites) AND (autoimmune disease) AND (basal cell carcinoma of the skin) AND (breast feeding) AND (carcinomatous meningitis) AND (cardiac involvement) AND (central nervous system (CNS) metastases) AND (chemotherapy) AND (curatively) AND (curatively resected) AND (curatively treated) AND (current) AND (esophageal variceal bleeding) AND (evidence) AND (expecting to conceive) AND (expecting to father) AND (first dose of study medication) AND (first dose of study therapy) AND (for up to 120 days after the last dose of study medication) AND (gastric variceal bleeding) AND (hematologic transplant) AND (hepatic arterial infusion [HAI]) AND (hepatic encephalopathy) AND (hepatitis C) AND (history) AND (human immunodeficiency virus (HIV)) AND (imaging) AND (immunodeficiency) AND (immunosuppressive therapy) AND (immunotherapy) AND (in situ cancers) AND (in the last 6 months) AND (in the past 2 years) AND (infection) AND (inferior vena cava) AND (live vaccine) AND (liver) AND (locoregional therapy) AND (main portal branch (Vp4)) AND (major surgery) AND (malignancy) AND (minor surgery) AND (non-infectious) pneumonitis) AND (other site) AND (other than) AND (oxaliplatin) AND (participated in clinical studies with pembrolizumab) AND (pembrolizumab) AND (pneumonitis) AND (portal vein invasion) AND (pregnant) AND (prior) AND (radiation) AND (radioembolization) AND (receiving pembrolizumab) AND (recovered adequately) AND (requiring systemic therapy) AND (resected) AND (solid organ transplant) AND (sorafenib) AND (sorafenib or oxaliplatin-based) AND (squamous cell carcinoma of the skin) AND (start of study medication) AND (starting from the first dose of study medication) AND (steroids) AND (systemic steroid therapy) AND (systemic therapy) AND (systemic treatment) AND (the first dose of study medication) AND (the last dose of study medication) AND (the study period) AND (therapy for HCV) AND (throughout the study period) AND (transcatheter chemoembolization [TACE]) AND (transcatheter embolization [TAE]) AND (treated) AND (untreated) AND (with the exception of) AND (within 14 days) AND (within 3 years prior to first dose of study medication) AND (within 4 weeks prior) AND (within 7 days prior) AND (within the last 6 months) AND (≤7 days prior))"}
{"candidate_id": "LLM01897", "doc_id": "NCT02851888_exc", "case_bucket": "or", "source_criterion": "Current or planned pregnancy History of neuropathic pain, chronic pain syndrome, or preoperative use of narcotic or neuropathic pain medicine Radiographic signs of osteoarthritis (> Tonis grade 1) Inability to attend follow up visits Documented allergy to local anesthetic", "candidate_expression": "((Inability attend follow up visits) AND (Radiographic) AND (Tonis grade > 1) AND (allergy) AND (chronic pain syndrome) AND (local anesthetic) AND (narcotic medicine) AND (neuropathic pain) AND (neuropathic pain medicine) AND (osteoarthritis Radiographic signs) AND (pregnancy Current planned))"}
{"candidate_id": "LLM01898", "doc_id": "NCT03372304_exc", "case_bucket": "other", "source_criterion": "NA", "candidate_expression": "(EMPTY)"}
{"candidate_id": "LLM01899", "doc_id": "NCT03013790_inc", "case_bucket": "other", "source_criterion": "Non-ventilated Patients over the age of 65", "candidate_expression": "((age over 65) AND NOT (ventilated))"}
{"candidate_id": "LLM01900", "doc_id": "NCT03333655_inc", "case_bucket": "or", "source_criterion": "Response assessment of complete response (CR), partial response (PR), long stable disease (SD) for >3 months with a cancer immunotherapy treatment for metastatic cancer or hematologic malignancies either through a marketed CPI or through participation in a Roche/Genentech CPI clinical trial. Availability of tumor biopsy material extracted and preserved by the investigating site.", "candidate_expression": "((Response assessment complete response (CR) partial response (PR) long stable disease (SD)) AND (hematologic malignancies) AND (immunotherapy treatment cancer) AND (marketed CPI) AND (metastatic cancer) AND (participation in a Roche/Genentech CPI clinical trial))"}
```
