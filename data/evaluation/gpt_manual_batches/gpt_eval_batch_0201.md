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
{"candidate_id": "LLM05001", "doc_id": "NCT02385045_exc", "case_bucket": "or", "source_criterion": "Patients attending for a therapeutic endoscopic procedure e.g. variceal banding, stent insertion, balloon dilatation. Patients with a known diagnosis e.g. upper gastrointestinal cancer Patients previously treated with HP eradication therapy Patients who had taken PPI, H2 receptor antagonists and antibiotics within 4 weeks Patients with acute gastrointestinal bleeding Patients who'd had previous gastric surgery Patients with chronic liver disease Patients with abnormal coagulation or any other contra-indication to use of standard biopsy in routine diagnostic endoscopic procedures Patients who are unable or unwilling to give informed consent Patients under the age of 18 years", "candidate_expression": "((HP eradication therapy) AND (acute) AND (age) AND (chronic) AND (diagnostic endoscopic procedures) AND (gastric surgery) AND (gastrointestinal bleeding) AND (known diagnosis) AND (liver disease) AND (previous) AND (standard biopsy) AND (therapeutic endoscopic procedure) AND (under 18 years) AND (upper gastrointestinal cancer) AND (within 4 weeks) AND ((H2 receptor antagonists) OR (PPI) OR (antibiotics)) AND ((abnormal coagulation) OR (contra-indication)) AND ((balloon dilatation) OR (stent insertion) OR (variceal banding)))"}
{"candidate_id": "LLM05002", "doc_id": "NCT02528136_exc", "case_bucket": "or", "source_criterion": "Patients with placenta pathology such as praevia, acreta, pre-eclampsia Patients with bleeding disorders including vonWillebrand disease type I. Known intolerance to one of the two drugs. Patients with prolonged QT-time or other serious cardiac diseases. Liver or kidney failure. Epilepsy. Any medical reason why, in the opinion of the investigator, the patient should not participate", "candidate_expression": "((Any medical reason why, in the opinion of the investigator, the patient should not participate) AND (Epilepsy) AND (Liver failure) AND (acreta) AND (bleeding disorders) AND (drugs one of the two) AND (intolerance) AND (kidney failure) AND (placenta pathology) AND (praevia) AND (pre-eclampsia) AND (prolonged QT-time) AND (serious cardiac diseases other) AND (vonWillebrand disease type I))"}
{"candidate_id": "LLM05003", "doc_id": "NCT03253796_inc", "case_bucket": "or", "source_criterion": "Is not of reproductive potential, or is of reproductive potential and agrees to avoid becoming pregnant or impregnating a partner while receiving trial medication or within 6 months after the last dose of trial medication Has chronic back pain of =3 months duration by history Has physician-diagnosed active nr-axSpA with disease duration <= 5 years • Inflammatory back pain • Arthritis (physician-diagnosed) • Enthesitis (heel) physician-diagnosed (spontaneous pain or tenderness at examination of the site of the insertion of the Achilles tendon or plantar fascia) • Dactylitis (physician-diagnosed) • Psoriasis (physician-diagnosed) • History of physician-diagnosed inflammatory bowel disease (IBD) • History of uveitis confirmed by an ophthalmologist • Good response to nonsteroidal anti-inflammatory drugs (NSAID) • Family history of SpA (presence of ankylosing spondylitis, psoriasis, acute uveitis, reactive arthritis, or IBD) • Elevated CRP • Human leukocyte antigen B27 (HLA-B27)+ gene Has a HLA-B27+ gene and 2 or more of the SpA characteristics listed above Has elevated CRP at Screening or evidence of active inflammation in the sacroiliac joints on MRI Has an ASDAS >= 2.1 at Screening Shows high disease activity at Screening and Baseline of both a Total Back Pain score of =4 and a Bath Ankylosing Spondylitis Disease Activity Index (BASDAI) score of >= 4 Has an acceptable history of NSAID use Has no history of untreated latent or active tuberculosis (TB) prior to Screening Has had no recent close contact with a person with active TB or, if there has been such contact, will undergo additional evaluations and receive appropriate treatment for latent TB", "candidate_expression": "(((HLA-B27)+) AND (2 or more) AND (<= 5 years) AND (=3 months) AND (=3 months duration) AND (=4) AND (>= 2.1) AND (>= 4) AND (ASDAS) AND (Arthritis) AND (Bath Ankylosing Spondylitis Disease Activity Index (BASDAI) score) AND (CRP) AND (Dactylitis) AND (Elevated) AND (Enthesitis) AND (Family history) AND (Good response) AND (HLA-B27+) AND (History) AND (IBD) AND (Inflammatory back pain) AND (Is not of reproductive potential, or is of reproductive potential and agrees to avoid becoming pregnant or impregnating a partner while receiving trial medication or within 6 months after the last dose of trial medication) AND (MRI) AND (NSAID) AND (Psoriasis) AND (Screening) AND (SpA) AND (Total Back Pain score) AND (acceptable) AND (active) AND (acute uveitis) AND (ankylosing spondylitis) AND (at Screening) AND (at Screening and Baseline) AND (chronic back pain) AND (close contact) AND (disease duration) AND (disease duration <= 5 years) AND (duration) AND (elevated) AND (gene Human leukocyte antigen B27) AND (heel) AND (high disease activity) AND (history) AND (inflammation) AND (inflammatory bowel disease (IBD)) AND (latent) AND (no) AND (nonsteroidal anti-inflammatory drugs (NSAID)) AND (nr-axSpA) AND (pain) AND (person with active TB) AND (plantar fascia) AND (prior to Screening) AND (psoriasis) AND (reactive arthritis) AND (recent) AND (sacroiliac joints) AND (site of the insertion of the Achilles tendon) AND (tenderness) AND (tuberculosis (TB)) AND (untreated) AND (uveitis))"}
{"candidate_id": "LLM05004", "doc_id": "NCT02053246_inc", "case_bucket": "other", "source_criterion": "Adults (= 18 years of age) with World Health Organization Group 2 Pulmonary Hypertension (Mean pulmonary artery pressure = 25 mmHg and pulmonary capillary wedge pressure = 15 mmHg) New York Heart Association class II-IV symptoms Left ventricular ejection fraction (LVEF) = 45%", "candidate_expression": "(((Mean pulmonary artery pressure = 25 mmHg) AND (Adults) AND (Left ventricular ejection fraction (LVEF) = 45%) AND (New York Heart Association class II-IV) AND (Pulmonary Hypertension World Health Organization Group 2) AND (age = 18 years) AND (pulmonary capillary wedge pressure = 15 mmHg) AND (symptoms))"}
{"candidate_id": "LLM05005", "doc_id": "NCT02283905_exc", "case_bucket": "other", "source_criterion": "The patient's data will be excluded if they die within 3 days of hospital admission.", "candidate_expression": "((die) AND (hospital admission) AND (within 3 days of hospital admission))"}
{"candidate_id": "LLM05006", "doc_id": "NCT00730301_inc", "case_bucket": "or", "source_criterion": "Patient diagnosed by HRCT Core Lab with eligible heterogeneous disease distribution and at least one complete oblique fissure. Age from 40 to 75 years BMI < 32 kg/m2 FEV1 < 40% of predicted value, FEV1/FVC < 70% TLC > 120% predicted, RV > 150% predicted. Stable with < 20 mg prednisone (or equivalent) qd PaCO2 < 50mm Hg PaO2 > 45 mm Hg on room air 6-min walk of > 50m (without rehabilitation) or > 100m (with rehabilitation) Nonsmoking for 4 months prior to initial interview and throughout screening The patient agrees to all protocol required follow-up intervals. The patient has no child bearing potential The patient is willing and able to complete protocol required baseline assessments and procedures", "candidate_expression": "((6-min walk) AND (Age from 40 to 75 years) AND (BMI < 32 kg/m2) AND (FEV1 < 40% of predicted value) AND (FEV1/FVC < 70%) AND (HRCT Core Lab) AND (Nonsmoking for 4 months prior to initial interview throughout screening initial interview) AND (PaCO2 < 50mm Hg) AND (PaO2 > 45 mm Hg) AND (RV > 150% predicted) AND (Stable) AND (TLC > 120% predicted) AND (agrees to all protocol required follow-up intervals) AND (baseline assessments) AND (baseline procedures) AND (complete oblique fissure at least one) AND (follow-up intervals) AND (heterogeneous disease distribution) AND (prednisone < 20 mg qd) AND (willing and able to complete protocol) AND NOT (child bearing potential) AND ((> 100m rehabilitation) OR (> 50m rehabilitation)))"}
{"candidate_id": "LLM05007", "doc_id": "NCT02851303_exc", "case_bucket": "other", "source_criterion": "Born prior to 34 weeks Neonatal intensive care unit admission Serious medical comorbidities Primary substance exposure in-utero was buprenorphine, or was not opioids", "candidate_expression": "((Born prior to 34 weeks) AND (Neonatal intensive care unit) AND (medical comorbidities Serious) AND (substance exposure in-utero buprenorphine) AND NOT (opioids))"}
{"candidate_id": "LLM05008", "doc_id": "NCT00917891_exc", "case_bucket": "or", "source_criterion": "1. Currently pregnant or last pregnancy outcome within 3 months prior to enrolment 2. Currently breast-feeding 3. Participated in any other research study within 60 days prior to screening 4. Previously participated in any HIV vaccine study 5. Untreated urogenital infections (either symptomatic or asymptomatic) within 2 weeks prior to enrollment 6. Presence of abnormal physical finding on the vulva, vaginal walls or cervix during pelvic/speculum examination and/or colposcopy 7. History of significant urogenital or uterine prolapse, undiagnosed vaginal bleeding, urethral obstruction 8. Pap smear result at screening that requires cryotherapy, biopsy, treatment (other than for infection), or further evaluation 9. Any Grade 2, 3 or 4 baseline haematology, chemistry or urinalysis laboratory abnormality according to the DAIDS Table for Grading Adverse Experiences 10. Unexplained, undiagnosed abnormal bleeding per vagina, bleeding per vagina during or following vaginal intercourse, or gynaecologic surgery within 90 days prior to enrollment 11. Any history of anaphylaxis or severe allergy resulting in angioedema; or a history of sensitivity/allergy to latex 12. Any serious acute, chronic or progressive disease 13. Any condition(s) that, in the opinion of the investigator, might interfere with adherence to study requirements or evaluation of the study objectives", "candidate_expression": "((Any condition(s) that, in the opinion of the investigator, might interfere with adherence to study requirements or evaluation of the study objectives) AND (Any serious acute, chronic or progressive disease) AND (Currently) AND (DAIDS Table for Grading Adverse Experiences) AND (Grade 2, 3 or 4) AND (History) AND (Pap smear) AND (Unexplained) AND (Untreated) AND (abnormal) AND (angioedema) AND (at screening) AND (baseline) AND (biopsy) AND (breast-feeding) AND (chemistry) AND (cryotherapy) AND (disease) AND (enrollment) AND (enrolment) AND (further evaluation) AND (haematology) AND (history) AND (laboratory) AND (laboratory abnormality) AND (last) AND (severe) AND (significant) AND (treatment) AND (undiagnosed) AND (urinalysis) AND (urogenital infections) AND (within 2 weeks prior to enrollment) AND (within 3 months prior to enrolment) AND (within 90 days prior to enrollment) AND ((asymptomatic) OR (symptomatic)) AND ((pregnancy outcome) OR (pregnant)) AND ((abnormal physical finding on the cervix) OR (abnormal physical finding on the vaginal walls) OR (abnormal physical finding on the vulva)) AND ((colposcopy) OR (pelvic examination) OR (speculum examination)) AND ((urogenital prolapse) OR (uterine prolapse)) AND ((urethral obstruction) OR (vaginal bleeding)) AND ((requires biopsy) OR (requires cryotherapy) OR (requires further evaluation) OR (requires treatment)) AND ((chemistry abnormality) OR (haematology abnormality) OR (urinalysis abnormality)) AND ((bleeding per vagina) OR (gynaecologic surgery)) AND ((during vaginal intercourse) OR (following vaginal intercourse)) AND ((allergy) OR (anaphylaxis)) AND ((allergy to latex) OR (sensitivity to latex)) AND ((acute) OR (chronic) OR (progressive) OR (serious)))"}
{"candidate_id": "LLM05009", "doc_id": "NCT01942915_exc", "case_bucket": "other", "source_criterion": "1. Patients with C class by child-pugh score 2. Patients in the acute phase of severe hepatitis 3. Patients have been diagnosed with cancer of the liver 4. Patients with severe cardiopulmonary cerebral disease, and in the failure state 5. Patients in Highly allergic constitution 6. Patients with moderately severe mental disease", "candidate_expression": "((Highly allergic constitution) AND (cancer of the liver) AND (cardiopulmonary cerebral disease severe) AND (child-pugh score C class) AND (mental disease moderately severe) AND (severe hepatitis acute phase))"}
{"candidate_id": "LLM05010", "doc_id": "NCT02106598_exc", "case_bucket": "or", "source_criterion": "Known pregnancy or breast-feeding. Medical illness unrelated to the tumor which in the opinion of the attending physician and principal investigator will preclude administration of the agent. This includes patients with uncontrolled infection, chronic renal insufficiency, myocardial infarction within the past 6 months, unstable angina, cardiac arrhythmias other than chronic atrial fibrillation and chronic active or persistent hepatitis, or New York Heart Association Classification III or IV heart disease.", "candidate_expression": "((Classification III or IV) AND (Medical illness unrelated to the tumor) AND (New York Heart Association) AND (breast-feeding) AND (cardiac arrhythmias) AND (chronic active hepatitis) AND (chronic atrial fibrillation) AND (chronic renal insufficiency) AND (heart disease) AND (myocardial infarction) AND (other than) AND (persistent hepatitis) AND (pregnancy) AND (uncontrolled infection) AND (unstable angina) AND (which in the opinion of the attending physician and principal investigator will preclude administration of the agent) AND (within the past 6 months))"}
{"candidate_id": "LLM05011", "doc_id": "NCT02046395_exc", "case_bucket": "or", "source_criterion": "Pregnancy Patients with chronic kidney disease stage with eGFR < 30 ml/min (CKD stage IV and V) Nephrotic range proteinuria (urinary protein > 3.5 gm/day) History or renal transplantation History of multiple myeloma Known history of hypersensitivity reaction or intolerability to Ace Inh or ARB.", "candidate_expression": "((CKD) AND (Pregnancy) AND (chronic kidney disease) AND (eGFR < 30 ml/min) AND (multiple myeloma History) AND (proteinuria Nephrotic range) AND (renal transplantation History) AND (urinary protein > 3.5 gm/day) AND ((hypersensitivity reaction) OR (intolerability)) AND ((ARB) OR (Ace Inh)) AND ((stage IV) OR (stage V)))"}
{"candidate_id": "LLM05012", "doc_id": "NCT00344318_exc", "case_bucket": "or", "source_criterion": "Use of any investigational or non-registered product (drug or vaccine) other than the study vaccine(s) within 30 days preceding the first dose of study vaccine, or planned use during the study period Chronic administration (defined as more than 14 days) of immunosuppressants or other immune-modifying drugs within six months prior to the first vaccine dose. Planned administration/ administration of a vaccine not foreseen by the study protocol during the period starting one month before each dose of vaccine(s) and ending 7 days after dose 1 and dose 2 or 1 month after dose 3. Previous vaccination against diphtheria, tetanus, pertussis, polio, hepatitis B, Haemophilus influenzae type b, and/or S. pneumoniae with the exception of vaccines where the first dose can be given within the first two weeks of life according to the national recommendations History of or intercurrent diphtheria, tetanus, pertussis, hepatitis B, polio, and Haemophilus influenzae type b diseases. History of allergic disease or reactions likely to be exacerbated by any component of the vaccines. History of seizures (this criterion does not apply to subjects who have had a single, uncomplicated febrile convulsion in the past) or neurological disease. Acute disease at the time of enrolment Any confirmed or suspected immunosuppressive or immunodeficient condition based on medical history and physical A family history of congenital or hereditary immunodeficiency. Major congenital defects or serious chronic illness. Administration of immunoglobulins and/or any blood products since birth or planned administration during the active phase of the study.", "candidate_expression": "((1 month after dose 3) AND (Acute disease) AND (Chronic) AND (Haemophilus influenzae type b) AND (History) AND (Major congenital defects) AND (Planned) AND (S. pneumoniae) AND (active phase of the study) AND (allergic disease) AND (any blood products) AND (at the time of enrolment) AND (birth) AND (congenital immunodeficiency) AND (diphtheria) AND (does not apply) AND (dose 1) AND (dose 1 and dose 2) AND (dose 2) AND (dose 3) AND (drug) AND (during the active phase of the study) AND (during the study period) AND (each dose of vaccine(s)) AND (ending 7 days after dose 1 and dose 2) AND (enrolment) AND (exacerbated) AND (family history) AND (febrile convulsion) AND (first dose can be given) AND (hepatitis B) AND (hereditary immunodeficiency) AND (immunodeficient condition) AND (immunoglobulins) AND (immunosuppressants) AND (immunosuppressive condition) AND (more than 14 days) AND (neurological disease) AND (non-registered product any other than the study vaccine(s)) AND (not foreseen by the study protocol) AND (other immune-modifying drugs) AND (period starting one month before each dose of vaccine(s)) AND (pertussis) AND (planned) AND (planned use) AND (polio) AND (product any investigational other than the study vaccine(s)) AND (reactions allergic) AND (seizures) AND (serious chronic illness) AND (since birth) AND (single) AND (tetanus) AND (the first two weeks of life) AND (uncomplicated) AND (vaccination) AND (vaccine) AND (vaccines) AND (with the exception of) AND (within 30 days) AND (within six months) AND (within the first two weeks of life))"}
{"candidate_id": "LLM05013", "doc_id": "NCT02370069_inc", "case_bucket": "or", "source_criterion": "Males and females of 18 years of age or older at the time of the vaccination Severe chronic kidney disease (Stage 4 and 5)", "candidate_expression": "((18 years or older) AND (Males) AND (Severe) AND (Stage 4 chronic kidney disease) AND (Stage 5 chronic kidney disease) AND (age) AND (at the time of the vaccination) AND (chronic kidney disease) AND (females) AND (vaccination))"}
{"candidate_id": "LLM05014", "doc_id": "NCT02634541_exc", "case_bucket": "or", "source_criterion": "Psoriasis or psoriasis arthropathy Inflammatory bowel disease Unwillingness to participate in the study with additional imaging protocols Expected life-span less than <1 year Diabetes (to improve the PET imaging quality) Probable noncompliance Pregnancy Age <18 years or >75 years Contraindication for adalimumab Methotrexate used within the previous 6 months A biologic medicine used within the previous 6 months", "candidate_expression": "((Age) AND (Contraindication) AND (Diabetes) AND (Expected life-span) AND (Inflammatory bowel disease) AND (Methotrexate) AND (PET imaging quality) AND (Pregnancy) AND (Probable) AND (Unwillingness to participate in the study with additional imaging protocols) AND (adalimumab) AND (biologic medicine) AND (less than <1 year) AND (noncompliance) AND (within the previous 6 months) AND ((Psoriasis) OR (psoriasis arthropathy)) AND ((<18 years) OR (>75 years)))"}
{"candidate_id": "LLM05015", "doc_id": "NCT02332291_exc", "case_bucket": "or", "source_criterion": "Current or past diagnoses of other Axis I psychiatric disorders, except for generalized anxiety disorder (GAD) symptoms occurring during a depressive episode History of alcohol or drug dependence or abuse in the last three years History of developmental disorder or IQ score < 70 Presence of acute suicidality Acute grief (< 1 month) Current or past psychosis Primary neurological disorder, including but not limited to dementia, stroke, brain tumors, epilepsy, Parkinson's disease, or demyelinating diseases MRI contraindications Any physical or intellectual disability adversely affecting ability to complete assessments Electroconvulsive therapy in last 6 months Use of antidepressant medications or other psychotropic medications in the last 4 weeks (or the last 6 weeks for fluoxetine). Occasional use of benzodiazepines or non-benzodiazepine sedatives (such as zolpidem, eszopiclone, or zaleplon) during this period is allowable. A failed therapeutic trial of escitalopram in the current depressive episode (defined as at least 6 weeks of treatment at a daily dose of 10mg or higher) Known allergy or hypersensitivity to escitalopram or bupropion Current or planned psychotherapy", "candidate_expression": "((Acute grief < 1 month Current) AND (Axis I psychiatric disorders other) AND (Electroconvulsive therapy in last 6 months) AND (IQ score < 70) AND (MRI) AND (Parkinson's disease) AND (Primary neurological disorder) AND (acute suicidality) AND (alcohol abuse) AND (alcohol dependence) AND (allergy daily dose of 10mg or higher) AND (antidepressant medications) AND (benzodiazepines sedatives) AND (brain tumors) AND (bupropion Current planned) AND (contraindications) AND (dementia) AND (demyelinating diseases) AND (depressive episode) AND (depressive episode at least 6 weeks of treatment) AND (developmental disorder) AND (drug abuse) AND (drug dependence) AND (epilepsy) AND (escitalopram) AND (escitalopram in the current depressive episode depressive episode) AND (eszopiclone) AND (fluoxetine) AND (hypersensitivity) AND (intellectual disability) AND (non-benzodiazepine sedatives) AND (physical disability) AND (psychosis past) AND (psychotherapy) AND (psychotropic medications other in the last 4 weeks in the last 6 weeks) AND (stroke) AND (therapeutic trial failed) AND (zaleplon) AND (zolpidem) AND NOT (generalized anxiety disorder (GAD) during a depressive episode))"}
{"candidate_id": "LLM05016", "doc_id": "NCT03364036_inc", "case_bucket": "or", "source_criterion": "Highly active RMS as defined by: One relapse in the previous year and at least 1 T1 Gadolinium (Gd)+ lesion or 9 or more T2 lesions, while on therapy with other disease modifying drugs (DMDs) Two or more relapses in the previous year, whether on DMD treatment or not. Expanded Disability Status Scale (EDSS) score less than equals to (<=) 5.0. Other protocol defined inclusion criteria could apply.", "candidate_expression": "((Expanded Disability Status Scale (EDSS) score less than equals to (<=) 5.0) AND (Other protocol defined inclusion criteria could apply.) AND (RMS Highly active) AND (disease modifying drugs (DMDs) other) AND (relapse One in the previous year) AND (relapses Two or more in the previous year) AND (therapy) AND ((T2 lesions 9 or more) OR (lesion at least 1 T1 Gadolinium (Gd)+)))"}
{"candidate_id": "LLM05017", "doc_id": "NCT02431442_inc", "case_bucket": "or", "source_criterion": "Able to provide voluntary, written informed consent with comprehension of all aspects of the protocol, prior to any study procedures. Healthy obese male and female volunteers aged 18 to 55 years, inclusive. Heterozygous subjects may be 18 to 65 years inclusive. In good general health, without significant medical history, physical examination findings, or clinical laboratory abnormalities. Body Mass Index of 30-40 kg/m2, inclusive. Heterozygous subjects may have a broader BMI range; to be eligible heterozygous subjects may have a BMI 27 -55 kg/ m2, inclusive. Stable body weight during the previous 6 months, based on Investigator judgment. Blood pressure <140/90 mmHg at Screening and D-1. Measurement may be repeated within 24 hours, based on Investigator judgment. Females must not be pregnant and must have a negative serum pregnancy test result at the Screening Visit and Day -1. Females of childbearing potential must agree to be abstinent or else use any two of the following medically acceptable forms of contraception from the Screening Period through the Final Study Visit: hormonal, condom with spermicidal jelly, diaphragm or cervical cap with spermicidal jelly, or IUD. Hormonal contraception must have started at least 3 months prior to screening. A female whose male partner has had a vasectomy must agree to use one additional form of medically acceptable contraception. Subjects must agree to practice the above birth control methods for 30 days from the final visit as a safety precaution. Females of non-childbearing potential, defined as surgically sterile (status post hysterectomy, bilateral oophorectomy, or bilateral tubal ligation) or post-menopausal for at least 12 months (and confirmed with a screening FSH level in the post-menopausal range), do not require contraception during the study. Males with female partners of childbearing potential must agree to use two medically acceptable forms of contraception as described above, with one of the two forms being condom with spermicide, from the Screening Period through the Final Study Visit. Males with female partners of childbearing potential who themselves are surgically sterile (status post vasectomy) must agree to use condoms with spermicide over the same period of time. Male subjects must agree to practice the above birth control methods for 30 days from the final visit as a safety precaution.", "candidate_expression": "((A female whose male partner has had a vasectomy must agree to use one additional form of medically acceptable contraception.) AND (Able to provide voluntary, written informed consent with comprehension of all aspects of the protocol, prior to any study procedures.) AND (BMI 27 -55 kg/ m2, inclusive) AND (Blood pressure <140/90 mmHg at Screening and D-1) AND (Body Mass Index 30-40 kg/m2, inclusive) AND (Females) AND (Females must not be pregnant and must have a negative serum pregnancy test result at the Screening Visit and Day -1.) AND (Females of childbearing potential must agree to be abstinent or else use any two of the following medically acceptable forms of contraception from the Screening Period through the Final Study Visit: hormonal, condom with spermicidal jelly, diaphragm or cervical cap with spermicidal jelly, or IUD.) AND (Females of non-childbearing potential, defined as surgically sterile (status post hysterectomy, bilateral oophorectomy, or bilateral tubal ligation) or post-menopausal for at least 12 months (and confirmed with a screening FSH level in the post-menopausal range), do not require contraception during the study.) AND (Healthy) AND (Heterozygous) AND (Heterozygous 18 to 65 years inclusive) AND (Hormonal contraception at least 3 months prior to screening) AND (In good general health, without significant medical history, physical examination findings, or clinical laboratory abnormalities.) AND (Male subjects must agree to practice the above birth control methods for 30 days from the final visit as a safety precaution.) AND (Males with female partners of childbearing potential must agree to use two medically acceptable forms of contraception as described above, with one of the two forms being condom with spermicide, from the Screening Period through the Final Study Visit.) AND (Males with female partners of childbearing potential who themselves are surgically sterile (status post vasectomy) must agree to use condoms with spermicide over the same period of time.) AND (Measurement may be repeated within 24 hours, based on Investigator judgment.) AND (Subjects must agree to practice the above birth control methods for 30 days from the final visit as a safety precaution.) AND (aged 18 to 55 years, inclusive) AND (based on Investigator judgment) AND (body weight Stable during the previous 6 months) AND (childbearing potential) AND (good general health) AND (heterozygous) AND (obese) AND (serum pregnancy test negative at the Screening Visit and Day -1) AND NOT (pregnant) AND ((female) OR (male)))"}
{"candidate_id": "LLM05018", "doc_id": "NCT03115151_exc", "case_bucket": "or", "source_criterion": "Baseline cognitive deficits sufficient to make objective pain self-assessments unreliable in the estimation of the Study Investigators. Immunocompromised subject Coagulopathy Severe liver and renal dysfunction Preoperative neurological deficits The dura damage during surgery Inability to follow directions or comprehend the English language. Females who are pregnant as determined by positive pregnancy test on or before the day of surgery. Prisoners. Patient refusal to provide informed consent. Allergy to amide local anesthetics (lidocaine, bupivacaine, ropivacaine) or opioid (fentanyl).", "candidate_expression": "((Allergy) AND (Baseline cognitive deficits sufficient to make objective pain self-assessments unreliable in the estimation of the Study Investigators.) AND (Coagulopathy) AND (Females who are pregnant as determined by positive pregnancy test on or before the day of surgery) AND (Immunocompromised) AND (Inability to follow directions or comprehend the English language) AND (Patient refusal to provide informed consent) AND (Preoperative) AND (Prisoners) AND (Severe) AND (dura damage) AND (fentanyl) AND (neurological deficits) AND (surgery) AND ((amide local anesthetics) OR (opioid)) AND ((bupivacaine) OR (lidocaine) OR (ropivacaine)) AND ((liver dysfunction) OR (renal dysfunction)))"}
{"candidate_id": "LLM05019", "doc_id": "NCT00445029_exc", "case_bucket": "or", "source_criterion": "Pregnant or lactating women. Evolutive skin disease on the testing zone (lower back). Patients with a clinically significant disease (chronic, recurrent or active). Systemic corticotherapy or immunosuppressive treatment during the previous month, or local corticoid treatment the week before the patch testing. Local or systemic drug use which interacts with the outcome measures. Exposure to sun or UV radiations, 15 days before the patch testing. Patients deprived of their civic rights, in custody, or subject to a tutorial, judiciary or administrative decision. Patients subject to a protection measure. Patients in a critical medical situation. Patients with a personal situation judged by the investigator as unlikely to be compatible with optimal participation in the study, or which could constitute a risk for the patient. Linguistic barrier or psychological profile preventing the patient from signing the consent form. Patient still in an exclusion period following the participation in another clinical trial. Patients having earned more than 4500€ in indemnities for participation in clinical trials during the previous 12 months, including this study.", "candidate_expression": "((Evolutive skin disease testing zone lower back) AND (Exposure to UV radiations) AND (Exposure to sun) AND (Linguistic barrier) AND (Pregnant) AND (Systemic corticotherapy) AND (critical medical situation) AND (deprived of their civic rights) AND (disease clinically significant chronic recurrent active) AND (drug interacts with the outcome measures Local systemic) AND (earned more than 4500€ in indemnities) AND (immunosuppressive treatment) AND (in custody) AND (lactating) AND (local corticoid treatment the week before) AND (participation in another clinical trial still in an exclusion period following) AND (participation in clinical trials during the previous 12 months) AND (personal situation) AND (psychological profile) AND (subject to a judiciary decision) AND (subject to a protection measure) AND (subject to a tutorial) AND (subject to administrative decision) AND (women) AND NOT (signing the consent form))"}
{"candidate_id": "LLM05020", "doc_id": "NCT02590822_inc", "case_bucket": "or", "source_criterion": "Capacity to provide informed consent before any trial-related activities Established T2DM (=3months) HbA1c = 9% if on triple therapy or = 10% on diet & exercise or monotherapy or dual therapy Current glucose lowering therapy either mono, dual or triple of any combination of metformin, sulphonylurea, DPP-IV inhibitor, GLP-1 therapy or an SGLT2 +/- diet and exercise Poorly managed diet controlled diabetes (with HbA1c > 6.5% , not currently taking any glucose lowering therapy, meeting BMI inclusion range) Body mass index > 30Kg/m2 or > 27.5 Kg/m2 (South Asian), Diagnosis of T2DM before the age of 60 years of age Age =18 and = 65 years", "candidate_expression": "((Age =18 and = 65 years) AND (Body mass index > 30Kg/m2 > 27.5 Kg/m2) AND (Capacity to provide informed consent before any trial-related activities) AND (Capacity to provide informed consent before any trial-related activities = 9% = 10%) AND (DPP-IV inhibitor,) AND (GLP-1 therapy) AND (HbA1c) AND (HbA1c > 6.5%) AND (SGLT2) AND (T2DM) AND (T2DM =3months) AND (age before 60 years of age) AND (diabetes) AND (diet) AND (exercise) AND (glucose lowering therapy) AND (metformin) AND (sulphonylurea) AND NOT (glucose lowering therapy))"}
{"candidate_id": "LLM05021", "doc_id": "NCT03034096_exc", "case_bucket": "or", "source_criterion": "Age less than 18 years American Society of Anesthesiologist Class 5 Projected life expectancy less than 30 days Known or suspected hypersensitivity to either propofol, e.g. egg or soy allergy, or volatile general anesthetic agents Known or suspected history of malignant hyperthermia", "candidate_expression": "((Age less than 18 years) AND (American Society of Anesthesiologist Class 5) AND (Projected life expectancy less than 30 days Known) AND (allergy) AND (egg) AND (hypersensitivity suspected) AND (malignant hyperthermia history) AND (propofol) AND (soy) AND (volatile general anesthetic agents Known suspected))"}
{"candidate_id": "LLM05022", "doc_id": "NCT02348918_exc", "case_bucket": "or", "source_criterion": "Active proliferative diabetic retinopathy (PDR) in the study eye such as NVE, NVD, vitreous hemorrhage, or neovascular glaucoma. Uncontrolled hypertension defined as systolic >180 mmHg or > 160 mmHg on 2 consecutive measurements or diastolic > 100 mmHg on optimal medical regimen Screening HgA1c blood test > 10.0 Focal laser photocoagulation or intravitreal/periocular steroids of any type in the study eye within the last 90 days prior to study enrollment. A history of intravitreal anti-VEGF injection of any type in the study eye within the last 45 days prior to study enrollment. History of rhegmatogenous retinal detachment, retinal tear(s), or traction retinal detachments in the study eye. Epiretinal membrane and/or vitreomacular traction in the study eye as determined by the central reading center. Previous pars plana vitrectomy in the study eye Any intraocular surgery in the study eye within the last 90 days prior to study enrollment. YAG laser treatment in the study eye in last 30 days prior to study enrollment. High myopia in the study eye, with a spherical equivalent of >8.00D at screening Other ocular pathologies that in the investigator's opinion would interfere with the subject's vision in the study eye. Chronic or recurrent uveitis. Ongoing ocular infection or inflammation in either eye. A history of cataract surgery complications/vitreous loss in the study eye. Congenital eye malformations in the study eye. A history of penetrating ocular trauma in the study eye. Mentally handicapped. Pregnant female, as determined for women less than 60 years old by a positive urine pregnancy test during the screening window. Nursing female. Currently participating in any other clinical research study. Contraindication to the study medication.", "candidate_expression": "((Active proliferative diabetic retinopathy (PDR) in the study eye) AND (Congenital eye malformations in the study eye) AND (Contraindication) AND (Currently participating in any other clinical research study.) AND (HgA1c blood test Screening > 10.0) AND (High myopia in the study eye at screening) AND (Mentally handicapped) AND (Nursing) AND (Pregnant) AND (Uncontrolled hypertension) AND (YAG laser treatment in the study eye in last 30 days prior to study enrollment) AND (anti-VEGF injection history of intravitreal in the study eye within the last 45 days prior to study enrollment) AND (cataract surgery) AND (female) AND (intraocular surgery in the study eye within the last 90 days prior to study enrollment) AND (ocular pathologies Other would interfere with the subject's vision in the study eye) AND (old less than 60 years) AND (optimal medical regimen) AND (pars plana vitrectomy Previous in the study eye) AND (penetrating ocular trauma history of in the study eye) AND (spherical equivalent >8.00D) AND (study medication) AND (urine pregnancy test positive during the screening window) AND (uveitis Ongoing in either eye) AND (women) AND ((> 160 mmHg on 2 consecutive measurements) OR (>180 mmHg)) AND ((diastolic > 100 mmHg on optimal medical regimen) OR (systolic)) AND ((Focal laser photocoagulation) OR (intravitreal/periocular steroids)) AND ((retinal tear(s)) OR (rhegmatogenous retinal detachment) OR (traction retinal detachments)) AND ((NVD) OR (NVE) OR (neovascular glaucoma) OR (vitreous hemorrhage)) AND ((Epiretinal membrane traction) OR (vitreomacular traction)) AND ((Chronic) OR (recurrent)) AND ((ocular infection) OR (ocular inflammation)) AND ((cataract surgery complications) OR (vitreous loss)))"}
{"candidate_id": "LLM05023", "doc_id": "NCT00500500_exc", "case_bucket": "or", "source_criterion": "patient already treated by medicines which could interfere with the study low level of vitamin B12 and folate which are considered as clinically relevant clinically relevant pathologies (eg: pulmonary illness, cardiovascular illness; evolutive cancer, neurological illness, blood illness….)", "candidate_expression": "((blood illness) AND (cardiovascular illness) AND (evolutive cancer) AND (folate level of) AND (level of vitamin B12) AND (low) AND (neurological illness) AND (pulmonary illness))"}
{"candidate_id": "LLM05024", "doc_id": "NCT02912182_inc", "case_bucket": "other", "source_criterion": "definite unilateral vestibulopathy no pathological HINTS (examination criteria in acute vestibular syndrome) capable of making their own decisions", "candidate_expression": "((HINTS) AND (acute vestibular syndrome) AND (capable of making their own decisions) AND (no) AND (pathological) AND (unilateral) AND (vestibulopathy))"}
{"candidate_id": "LLM05025", "doc_id": "NCT01809041_exc", "case_bucket": "or", "source_criterion": "Patients are not expected to be alive for longer than 3 months. Mini-mental State Examination (MMSE) [18] score = 23. history of dementia, psychiatric illness or any diseases of central nervous system. current use of sedatives or antidepressant. alcoholism and drug dependence. patients previously included in this study (for patients who have second intra-abdominal surgery during the study period). difficult to follow up or patients with poor compliance. uncontrolled hypertension (> 180/100 mmHg)", "candidate_expression": "((Mini-mental State Examination (MMSE) = 23) AND (alcoholism) AND (antidepressant) AND (dementia) AND (diseases of central nervous system) AND (drug dependence) AND (psychiatric illness) AND (sedatives) AND (uncontrolled hypertension > 180/100 mmHg) AND NOT (expected to be alive longer than 3 months))"}
```
