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
{"candidate_id": "LLM04826", "doc_id": "NCT02946918_inc", "case_bucket": "or", "source_criterion": "Age > 18 years Presumed AJCC (American Joint Committee on Cancer) tumor Stage I or II Planned total or near-total thyroidectomy Planned goal TSH suppression 0.1-0.5 mU/L for at least 18 weeks postoperatively Normal serum TSH within 12 months preceding surgery", "candidate_expression": "((0.1-0.5 mU/L) AND (> 18 years) AND (AJCC tumor Stage I) AND (Age) AND (American Joint Committee on Cancer) AND (Normal) AND (TSH suppression) AND (at least 18 weeks postoperatively) AND (postoperatively) AND (serum TSH) AND (surgery) AND (thyroidectomy) AND (within 12 months preceding surgery) AND ((near-total) OR (total)) AND ((I) OR (II)))"}
{"candidate_id": "LLM04827", "doc_id": "NCT02954029_exc", "case_bucket": "or", "source_criterion": "congenital or acquired bleeding tendency platelet count <50,000/ µL hypersensitivity to shrimps, lobsters or beetles", "candidate_expression": "((<50,000/ µL) AND (bleeding tendency) AND (hypersensitivity) AND (platelet count) AND ((acquired) OR (congenital)) AND ((beetles) OR (lobsters) OR (shrimps)))"}
{"candidate_id": "LLM04828", "doc_id": "NCT03079141_inc", "case_bucket": "other", "source_criterion": "Age of = 18 years of age and able to give written informed consent; Active chronic central serous chorioretinopathy (cCSC); Subjective visual loss > 6 weeks, interpreted as onset of active disease; Foveal subretinal fluid (SRF), on optical coherence tomography (OCT), at Baseline Examination; =1 ill-defined hyperfluorescent leakage areas on fluorescein angiography (FA) with retinal pigment epithelial window defect(s) that are compatible with cCSC; Hyperfluorescent areas on indocyanine green angiography (ICGA).", "candidate_expression": "((= 18 years) AND (=1) AND (> 6 weeks) AND (Active) AND (Age) AND (Baseline Examination) AND (Foveal subretinal fluid (SRF)) AND (Hyperfluorescent areas) AND (Subjective visual loss) AND (able to give written informed consent) AND (at Baseline Examination) AND (central serous chorioretinopathy (cCSC)) AND (chronic) AND (fluorescein angiography (FA)) AND (hyperfluorescent leakage areas) AND (ill-defined) AND (indocyanine green angiography (ICGA)) AND (optical coherence tomography (OCT)) AND (retinal pigment epithelial window defect(s)))"}
{"candidate_id": "LLM04829", "doc_id": "NCT03252249_exc", "case_bucket": "or", "source_criterion": "Clear indication for specific duration of dual anti-platelet therapy Type 2 myocardial infarction Contraindication to aspirin or P2Y12 receptor antagonist Non-resident of Scotland Previous recruitment into the trial Inability or unwilling to give informed consent", "candidate_expression": "((Clear indication for specific duration) AND (Contraindication) AND (Inability or unwilling to give informed consent) AND (Non-resident) AND (Previous recruitment into the trial) AND (Scotland) AND (Type 2 myocardial infarction) AND (dual anti-platelet therapy) AND ((P2Y12 receptor antagonist) OR (aspirin)))"}
{"candidate_id": "LLM04830", "doc_id": "NCT03381755_exc", "case_bucket": "or", "source_criterion": "taken adenosine diphosphate (ADP) receptor antagonists within 2 weeks Platelet count <100g/L; A history of bleeding tendency; Aspirin, ticagrelor or clopidogrel allergies; Severe liver injury.", "candidate_expression": "((Platelet count <100g/L) AND (adenosine diphosphate (ADP) receptor antagonists within 2 weeks) AND (allergies) AND (bleeding tendency history) AND (liver injury Severe) AND ((Aspirin) OR (clopidogrel) OR (ticagrelor)))"}
{"candidate_id": "LLM04831", "doc_id": "NCT02227992_inc", "case_bucket": "or", "source_criterion": "Paediatric subjects aged =28 days (= 1 month) to <18 years, requiring non-emergent open hepatic, abdominal, retroperitoneal, pelvic or thoracic (non-cardiac) surgical procedures. i) The first 36 subjects to be enrolled will be subjects aged =1 years to <18 years. ii) The next 4 subjects to be enrolled will be subjects aged =28 days to <1 year. The subject's parent/legal guardian must be willing to give permission for the subject to participate in the trial, and provide written informed consent for the subject. In addition, assent must be obtained from paediatric subjects who possess the intellectual and emotional ability to comprehend the concepts involved in the trial. If the paediatric subject is not able to provide assent (due to age, maturity and/or inability to intellectually and/or emotionally comprehend the trial), the parent/legal guardian's written Informed Consent for the subject will be acceptable for the subject to be included in the study. Presence of an appropriate mild or moderate bleeding soft tissue or hepatic parenchyma Target Bleeding Site (TBS) identified intra-operatively by the surgeon; Ability to firmly press trial treatment at TBS until 4 minutes after randomisation", "candidate_expression": "((=28 days (= 1 month) to <18 years) AND (Ability to firmly press trial treatment at TBS until 4 minutes after randomisation) AND (The subject's parent/legal guardian must be willing to give permission for the subject to participate in the trial, and provide written informed consent for the subject. In addition, assent must be obtained from paediatric subjects who possess the intellectual and emotional ability to comprehend the concepts involved in the trial. If the paediatric subject is not able to provide assent (due to age, maturity and/or inability to intellectually and/or emotionally comprehend the trial), the parent/legal guardian's written Informed Consent for the subject will be acceptable for the subject to be included in the study) AND (abdominal) AND (aged) AND (hepatic) AND (non-cardiac) AND (non-emergent) AND (open) AND (pelvic) AND (retroperitoneal) AND (surgical procedures) AND (thoracic))"}
{"candidate_id": "LLM04832", "doc_id": "NCT03497598_inc", "case_bucket": "or", "source_criterion": "Women = 3 UTIs within the last 12 months or = 2 UTIs within the last 6 months; Laboratory urine culture: <103 CFUs Age > 18 years", "candidate_expression": "((Age > 18 years) AND (Laboratory urine culture <103 CFUs) AND (UTIs = 2 within the last 6 months) AND (UTIs = 3 within the last 12 months) AND (Women))"}
{"candidate_id": "LLM04833", "doc_id": "NCT02589353_exc", "case_bucket": "or", "source_criterion": "adults 61 years old and above smokers pregnant women taking any prescription pain/ insulin medication has a history of taste or smell loss or other oral disorders (e.g., burning mouth syndrome) has current oral lesions, canker sores, or piercings has a history of food allergy", "candidate_expression": "((adults) AND (burning mouth syndrome) AND (canker sores) AND (food allergy history) AND (old and above 61 years) AND (oral disorders other) AND (oral lesions) AND (piercings) AND (pregnant) AND (prescription insulin medication) AND (prescription pain medication) AND (smell loss) AND (smokers) AND (taste loss) AND (women))"}
{"candidate_id": "LLM04834", "doc_id": "NCT02637453_exc", "case_bucket": "or", "source_criterion": "With acute diseases, such as acute phase after myocardial infarction (within 3 months), within 3 months after acute heart failure or new cerebral infarction; In the list of heart transplantation; Expected survival less than 1 year; With other hemorrhagic diseases and anticoagulant therapy is not allowed; Thrombosis in left atrium; Heart failure, New York Heart Association(NYHA) III/IV or eject fraction(EF)<40%; Patients with uncontrolled cancer; Significant hepatic or renal impairment (and/or alanine transaminase(ALT) or Aspartate transaminase(AST) >2 times upper limit of normal, creatinine clearance rate(CCr)<50%); Previous catheter radiofrequency ablation for AF or cardiac surgery; Pregnant and lactating women, women who plan to become pregnant, or women of child bearing age not using reliable contraceptive measures.", "candidate_expression": "((AF) AND (Expected survival less than 1 year) AND (Pregnant and lactating women, women who plan to become pregnant, or women of child bearing age not using reliable contraceptive measures.) AND (Thrombosis left atrium) AND (acute diseases) AND (anticoagulant therapy) AND (cancer uncontrolled) AND (heart transplantation In the list) AND (hemorrhagic diseases other) AND (myocardial infarction acute phase within 3 months) AND (not allowed) AND ((Heart failure) OR (New York Heart Association(NYHA) III/IV) OR (eject fraction(EF) <40%)) AND ((hepatic impairment) OR (renal impairment)) AND ((Aspartate transaminase(AST) >2 times upper limit of normal) OR (alanine transaminase(ALT)) OR (creatinine clearance rate(CCr) <50%)) AND ((cardiac surgery) OR (catheter radiofrequency ablation)) AND ((acute heart failure) OR (cerebral infarction)))"}
{"candidate_id": "LLM04835", "doc_id": "NCT03012984_inc", "case_bucket": "other", "source_criterion": "Age >= 65 years, < 90 years; Scheduled to undergo surgery for primary solid organ cancer under general anesthesia, with an expected duration of surgery >=2 hours; Planned to use patient-controlled intravenous analgesia after surgery; Provide written informed consent.", "candidate_expression": "((Age >= 65 years, < 90 years) AND (Provide written informed consent) AND (general anesthesia) AND (intravenous analgesia patient-controlled after surgery) AND (solid organ cancer primary) AND (surgery) AND (surgery Scheduled))"}
{"candidate_id": "LLM04836", "doc_id": "NCT00483106_inc", "case_bucket": "other", "source_criterion": "ADHD", "candidate_expression": "(ADHD)"}
{"candidate_id": "LLM04837", "doc_id": "NCT03463564_inc", "case_bucket": "or", "source_criterion": "T1DM for at least 12 months persistent HbA1c levels = 7.5% (58 mmol/mol) despite optimized education therapy, recurrent severe hypoglycemic episodes or high glucose variability willingness to wear the insulin pump", "candidate_expression": "((HbA1c levels persistent = 7.5% 58 mmol/mol) AND (T1DM for at least 12 months) AND (high glucose variability) AND (hypoglycemic episodes) AND (insulin pump) AND (optimized education therapy) AND (wear the insulin pump willingness))"}
{"candidate_id": "LLM04838", "doc_id": "NCT03171987_inc", "case_bucket": "scope", "source_criterion": "All subjects underwent a detailed history and systemic physical examination including neurologic and musculoskeletal evaluations. To rule out any confounding etiologies, basic diagnostic laboratory tests including complete blood count and acute phase reactants (erythrocyte sedimentation rate and C-reactive protein) were performed. The patients diagnosed as having acute non-specific low back pain according to history and physical examinations were invited to participate and will be informed about the purpose and course of the study. A primary complaint of pain in the area between the 12th rib and buttock crease without leg pain Female or male, 20 - 80 years of age Low back pain of less than six weeks' duration; and at least moderate pain intensity (NRS<U+2267>4)", "candidate_expression": "((20 - 80 years) AND (4) AND (C-reactive protein) AND (Female) AND (Low back pain) AND (NRS) AND (acute) AND (acute phase reactants) AND (age) AND (area between the 12th rib and buttock crease) AND (at least moderate) AND (complete blood count) AND (diagnostic laboratory tests) AND (erythrocyte sedimentation rate) AND (history) AND (leg pain) AND (less than six weeks' duration) AND (male) AND (non-specific low back pain) AND (pain) AND (pain intensity) AND (physical examinations) AND (without))"}
{"candidate_id": "LLM04839", "doc_id": "NCT02150590_exc", "case_bucket": "or", "source_criterion": "unstable condition, COPD exacerbation mild (GOLD 1) or very severe COPD (GOLD 4) requirement for oxygen therapy at low altitude residence hypoventilation pulmonary hypertension more than mild or unstable cardiovascular disease use of drugs that affect respiratory center drive internal, neurologic or psychiatric disease that interfere with protocol compliance including current heavy smoking (>20 cigarettes per day), inability to perform 6 min walk test. previous intolerance to moderate altitude (<2600m). exposure to altitudes >1500m for >2 days within the last 4 weeks before the study. pregnant or nursing patients", "candidate_expression": "((1)) AND (4) AND (6 min walk test) AND (<2600m) AND (>20 cigarettes per day) AND (GOLD) AND (altitude) AND (cardiovascular disease) AND (heavy) AND (hypoventilation) AND (inability) AND (intolerance) AND (mild) AND (moderate) AND (oxygen therapy) AND (pregnant or nursing patients) AND (pulmonary hypertension) AND (smoking) AND (unstable) AND (very severe) AND ((COPD)) AND ((more than mild) OR (unstable)) AND ((internal disease) OR (neurologic disease) OR (psychiatric disease)) AND ((COPD exacerbation) OR (condition)))"}
{"candidate_id": "LLM04840", "doc_id": "NCT02441179_inc", "case_bucket": "or", "source_criterion": "1. Patients ≥ 18 years-old from \"Instituto Teletón Santiago\" and \"Hospital Clínico Mutual de seguridad\". 2. C5 to T12 spinal cord injury, classified as ISNCSCI grades C and D 3. Traumatic and non-traumatic, non-progressive lesions 4. Onset > 6 months 5. Ability to ambulate with or without assistive devices 6. Ability to follow verbal or visual commands 7. Signed informed consent", "candidate_expression": "((C5 to T12) AND (ISNCSCI) AND (Onset > 6 months) AND (Signed informed consent) AND (Traumatic) AND (grades C and D) AND (lesions) AND (non-progressive) AND (non-traumatic) AND (spinal cord injury) AND (years-old) AND (≥ 18 years) AND ((Hospital Clínico Mutual de seguridad) OR (Instituto Teletón Santiago)) AND ((Ability to ambulate with assistive devices) OR (Ability to ambulate without assistive devices)) AND ((Ability to follow verbal commands) OR (Ability to follow visual commands)))"}
{"candidate_id": "LLM04841", "doc_id": "NCT02121145_exc", "case_bucket": "or", "source_criterion": "Primary groups: Vaccination against typhoid fever within 5 years before dosing. History of clinical typhoid fever, clinical paratyphoid A or B fever. Immunization with any other vaccine (oral or parenteral) within 4 weeks prior to study start or planned vaccination during the study Current intake of antibiotics or end of antibiotic therapy <8 days before first IMP administration Chronic (longer than 14 days) administration of immunosuppressants or other immune-modifying drugs within 6 months before the first dose of investigational vaccine; oral corticosteroids in dosages of =0.5 mg/kg/d prednisolone or equivalent are excluded; inhaled or topical steroids are allowed Acute or chronic clinically significant gastrointestinal disease", "candidate_expression": "((Primary groups) AND (Vaccination against typhoid fever within 5 years before dosing) AND (gastrointestinal disease clinically significant) AND (investigational vaccine) AND (longer than 14 days) AND (typhoid fever) AND NOT (oral corticosteroids dosages) AND ((oral) OR (parenteral)) AND ((Immunization with vaccine any other within 4 weeks prior to study start) OR (vaccination planned during the study)) AND ((antibiotic therapy end of <8 days before first IMP administration) OR (antibiotics Current)) AND ((immune-modifying drugs other) OR (immunosuppressants)) AND ((Acute) OR (chronic)) AND ((clinical paratyphoid A fever) OR (clinical paratyphoid B fever) OR (clinical typhoid fever)))"}
{"candidate_id": "LLM04842", "doc_id": "NCT01205334_exc", "case_bucket": "or", "source_criterion": "Severe intercurrent infection Known HIV positivity Pregnant or lactating History of hypersensitivity reactions to murine protein-containing products.", "candidate_expression": "((HIV positivity) AND (Pregnant) AND (Severe) AND (hypersensitivity reactions) AND (infection) AND (intercurrent) AND (lactating) AND (murine) AND (murine protein-containing products))"}
{"candidate_id": "LLM04843", "doc_id": "NCT02504203_inc", "case_bucket": "other", "source_criterion": "Children born outside the cluster, and returning more than 72 hours after the delivery Children that the nurse evaluates to die within the next 24 hours.", "candidate_expression": "(EMPTY)"}
{"candidate_id": "LLM04844", "doc_id": "NCT02477280_inc", "case_bucket": "other", "source_criterion": "18 years old or older. ADHD is diagnosed according to Diagnostic and Statistical Manual of Mental Disorders, fifth edition (DSM-5 criteria). Substance Use Disorder is diagnosed according to DSM-5 criteria. Qb-score 1.3 or higher on at least one of the weighted summary parameters QbActivity, QbInattention or QbImpulsivity on the QbTest. Participants are given their written informed consent to participate in the study.", "candidate_expression": "((ADHD DSM-5) AND (Participants are given their written informed consent to participate in the study) AND (Qb-score 1.3 or higher) AND (Substance Use Disorder DSM-5) AND (old 18 years or older))"}
{"candidate_id": "LLM04845", "doc_id": "NCT02541955_exc", "case_bucket": "or", "source_criterion": "Prior treatment with Acthar in the past 2mos Meet one of the above RA flare requirements Subjects who have received live or live attenuated vaccines within 6 weeks prior to the first dose of study drug (or the zoster vaccine)", "candidate_expression": "((Acthar) AND (Prior) AND (RA flare requirements) AND (first dose) AND (in the past 2mos) AND (one of) AND (study drug) AND (the first dose of study drug) AND (treatment) AND (within 6 weeks prior to the first dose of study drug) AND (zoster vaccine) AND ((live attenuated vaccines) OR (live vaccines)))"}
{"candidate_id": "LLM04846", "doc_id": "NCT01639664_inc", "case_bucket": "other", "source_criterion": "All patients admitted to the ICU in septic shock All patients that develop septic shock while in the ICU", "candidate_expression": "((ICU) AND (admitted) AND (in the ICU) AND (septic shock) AND (while in the ICU))"}
{"candidate_id": "LLM04847", "doc_id": "NCT03589105_exc", "case_bucket": "or", "source_criterion": "Diagnosis of primary progressive MS Inability to complete an MRI (contraindications for MRI include but are not restricted to weight =140 kg, pacemaker, cochlear implants, presence of foreign substances in the eye, intracranial vascular clips, surgery within 6 weeks of entry into the study, coronary stent implanted within 8 weeks prior to the time of the intended MRI, etc…) Gadolinium intolerance History of ischemic cerebrovascular disorders (e.g., stroke, transient ischemic attack) or ischemia of the spinal cord History or known presence of central nervous system (CNS) or spinal cord tumor (e.g., meningioma, glioma) History or known presence of potential metabolic causes of myelopathy (e.g., untreated vitamin B12 deficiency) History or known presence of infectious causes of myelopathy (e.g., syphilis, Lyme disease, human T-lymphotropic virus 1 (HTLV-1), herpes zoster myelopathy) History of genetically inherited progressive CNS degenerative disorder (e.g., hereditary paraparesis; MELAS [mitochondrial myopathy, encephalopathy, lactic acidosis, stroke] syndrome) Neuromyelitis optica History or known presence of systemic autoimmune disorders potentially causing progressive neurologic disease (e.g., lupus, anti-phospholipid antibody syndrome, Sjogren's syndrome, Behçet's disease, sarcoidosis) History of severe, clinically significant brain or spinal cord trauma (e.g., cerebral contusion, spinal cord compression) Vulnerable patients (Patient referred to in Articles L. 1121-5 to L. 1121-8 and L. 1122-1-2 of the French Public Health Code)", "candidate_expression": "((=140 kg) AND (Articles L. 1121-5 to L. 1121-8 and L. 1122-1-2 of the French Public Health Code) AND (Gadolinium) AND (History) AND (Inability to complete) AND (MRI) AND (Neuromyelitis optica) AND (Vulnerable patients) AND (clinically significant) AND (contraindications) AND (coronary stent) AND (encephalopathy) AND (entry into the study) AND (genetically inherited) AND (infectious causes) AND (intended) AND (intolerance) AND (lactic acidosis) AND (metabolic causes) AND (mitochondrial myopathy) AND (myelopathy) AND (potentially causing) AND (primary) AND (progressive CNS degenerative disorder) AND (progressive MS) AND (progressive neurologic disease) AND (severe) AND (stroke) AND (systemic autoimmune disorders) AND (the time of the intended MRI) AND (untreated) AND (vitamin B12 deficiency) AND (within 6 weeks of entry into the study) AND (within 8 weeks prior to the time of the intended MRI) AND ((cochlear implants) OR (foreign substances in the eye) OR (implanted) OR (intracranial vascular clips) OR (pacemaker) OR (surgery) OR (weight)) AND ((stroke) OR (transient ischemic attack)) AND ((ischemia of the spinal cord) OR (ischemic cerebrovascular disorders)) AND ((central nervous system (CNS) tumor) OR (spinal cord tumor)) AND ((glioma) OR (meningioma)) AND ((Lyme disease) OR (herpes zoster myelopathy) OR (human T-lymphotropic virus 1 (HTLV-1)) OR (syphilis)) AND ((MELAS syndrome) OR (hereditary paraparesis)) AND ((Behçet's disease) OR (Sjogren's syndrome) OR (anti-phospholipid antibody syndrome) OR (lupus) OR (sarcoidosis)) AND ((brain trauma) OR (spinal cord trauma)) AND ((cerebral contusion) OR (spinal cord compression)))"}
{"candidate_id": "LLM04848", "doc_id": "NCT03340740_inc", "case_bucket": "other", "source_criterion": "History of allergic rhinitis Wheezing", "candidate_expression": "((Wheezing) AND (allergic rhinitis))"}
{"candidate_id": "LLM04849", "doc_id": "NCT03388840_exc", "case_bucket": "or", "source_criterion": "Patients with Non-androgenetic causes of hair loss. Female patients with androgenetic alopecia. Patients who received anti-hair loss treatment within the past six months. Patients with history of bleeding disorders or on anticoagulant therapy. Patients with history of chronic liver disease, cancer or connective tissue disorders. Patients with current scalp infection.", "candidate_expression": "((Female) AND (Non-androgenetic causes of hair loss) AND (androgenetic alopecia) AND (anti-hair loss treatment) AND (anticoagulant therapy) AND (bleeding disorders) AND (cancer) AND (chronic liver disease) AND (connective tissue disorders) AND (current) AND (history) AND (scalp infection) AND (within the past six months))"}
{"candidate_id": "LLM04850", "doc_id": "NCT02807857_exc", "case_bucket": "or", "source_criterion": "Use of investigational drugs either within 5 half-lives of enrollment, or within 30 days, or until the expected pharmacodynamic effect has returned to baseline, whichever is longer. Major surgery in the last 3 months prior to baseline or planned major surgery or cardiac intervention during the study. Cancer or other significant co-morbidities implying that the patient's condition is unstable. Comorbidities that can be associated with elevated natriuretic peptide (NP) levels: renal insufficiency, (eGFR < 25 ml/min/1.73 m² calculated according to MDRD formula), recent (less than 3 months) cerebral trauma or recent (less than 3 months) cerebrovascular incident, novel diagnosis or acute exacerbation of COPD within the last 3 months. Patients who are primarily managed and regularly followed-up by a cardiologist for their HF Highly frail patients whose estimated lifespan due to comorbidities by the judgement of the investigator is less than 6 months.", "candidate_expression": "((< 25 ml/min/1.73 m²) AND (Cancer) AND (Comorbidities) AND (Major surgery) AND (NP) AND (acute exacerbation of COPD) AND (baseline or planned major surgery or cardiac intervention during the stud) AND (cerebral trauma) AND (cerebrovascular incident) AND (co-morbidities) AND (eGFR) AND (elevated) AND (last 3 months) AND (last 3 months prior to baseline or planned major surgery or cardiac intervention during the study) AND (less than 3 months) AND (less than 6 months) AND (lifespan) AND (natriuretic peptide levels) AND (renal insufficiency))"}
```
