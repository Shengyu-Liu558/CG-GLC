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
{"candidate_id": "LLM03201", "doc_id": "NCT03363295_exc", "case_bucket": "or", "source_criterion": "Diabetic patients Patients with any macular changes prior to the surgery (epiretinal membranes, age macular disease, macular edema...) Patients who had any complication during phacoemulsification surgery", "candidate_expression": "((Diabetic) AND (complication any during phacoemulsification surgery) AND (macular changes any prior to the surgery) AND (phacoemulsification surgery) AND (surgery) AND ((age macular disease) OR (epiretinal membranes) OR (macular edema)))"}
{"candidate_id": "LLM03202", "doc_id": "NCT02984228_exc", "case_bucket": "or", "source_criterion": "Non-English speaking/illiterate Painful active, concurrent cervical spine conditions Current non-steroidal anti-inflammatory drug (NSAID) use History of taking coumadin or similar anticoagulant, have a known coagulopathy, bleeding dyscrasia, or platelet count < 150,000/cubic mm Allergic reaction to poultry or previous viscosupplementation Involved in workers' compensation or active litigation involving affected shoulder Inability to refrain from NSAID use for 5 days prior to and 6 weeks after injection History of corticosteroid injection to affected shoulder within the last 3 months History of viscosupplementation or platelet-rich plasma to affected shoulder within the last 6 months Presence of acute fracture History of shoulder tumor Known uncontrolled systemic illness (uncontrolled diabetes, human immunodeficiency virus, vasculitis, autoimmune/inflammatory disease) Psychiatric and somatoform disorders", "candidate_expression": "((5 days prior to and 6 weeks after injection) AND (< 150,000/cubic mm) AND (Allergic reaction) AND (History of) AND (Inability to refrain from) AND (NSAID) AND (Non-English speaking/illiterate) AND (Painful) AND (Psychiatric disorders) AND (acute) AND (anticoagulant) AND (autoimmune) AND (bleeding dyscrasia) AND (cervical spine conditions) AND (coagulopathy) AND (corticosteroid injection) AND (coumadin) AND (diabetes) AND (fracture) AND (human immunodeficiency virus) AND (inflammatory disease) AND (injection) AND (last 3 months) AND (last 6 months) AND (non-steroidal anti-inflammatory drug) AND (platelet count) AND (platelet-rich plasma) AND (poultry) AND (shoulder) AND (shoulder tumor) AND (somatoform disorders) AND (systemic illness) AND (uncontrolled) AND (vasculitis) AND (viscosupplementation))"}
{"candidate_id": "LLM03203", "doc_id": "NCT02777580_inc", "case_bucket": "other", "source_criterion": "Age equal or greater than 70 years Onset of symptoms < 3 hours prior to randomisation = 2 mm ST-elevation across 2 contiguous precordial leads (V1-V6) or leads I and aVL for a minimum combined total of = 4 mm ST-elevation or = 2 mm ST-elevation in 2 contiguous inferior leads (II, III, aVF) for a minimum combined total of = 4 mm ST-elevation Informed consent received", "candidate_expression": "((Age equal or greater than 70 years) AND (Informed consent received) AND (Onset of symptoms < 3 hours prior to randomisation))"}
{"candidate_id": "LLM03204", "doc_id": "NCT02644629_exc", "case_bucket": "or", "source_criterion": "Active or past psychotic disorder, including a history of psychotic affective state Mental Retardation or Autistic Spectrum Disorder Prominent personality disorder Cardiac or neurologic active medical condition, including past CVA/TIA (Cardiovascular Accident/Transient Ischemic Attack) or any other unstable medical condition. Chronic nasal congestion Active or recent drug or alcohol abuse Substantial suicidality in a patient requiring admission but refuses to do so, and signs an \"against medical advice\" release form as part of clinical evaluation, and does not answer the terms for involuntary admission.", "candidate_expression": "((Active) AND (Autistic Spectrum Disorder) AND (CVA) AND (Cardiac active medical condition) AND (Cardiovascular Accident) AND (Chronic) AND (Mental Retardation) AND (Prominent personality disorder) AND (Substantial) AND (TIA) AND (Transient Ischemic Attack) AND (admission) AND (alcohol abuse) AND (drug abuse) AND (medical condition) AND (nasal congestion) AND (neurologic active medical condition) AND (past) AND (psychotic affective state) AND (psychotic disorder) AND (recent) AND (suicidality) AND (unstable))"}
{"candidate_id": "LLM03205", "doc_id": "NCT03499639_exc", "case_bucket": "or", "source_criterion": "Patients with combined HCV/HBV co-infection hepatocellular carcinoma (HCC) decompensated liver cirrhosis (Child-Pugh score above 6) non-genotype 4", "candidate_expression": "((Child-Pugh score above 6) AND (HBV infection) AND (HCV infection) AND (hepatocellular carcinoma (HCC)) AND (liver cirrhosis decompensated) AND NOT (genotype 4))"}
{"candidate_id": "LLM03206", "doc_id": "NCT02068365_exc", "case_bucket": "or", "source_criterion": "Evidence of decompensated liver disease (Childs B-C), hepato-cellular carcinoma, pre-existing severe depression or other psychiatric disease, significant cardiac disease, significant renal disease, seizure disorders or severe retinopathy. received telbivudine as the antiviral therapy or have received more than one NA in the past. received interferon or peginterferon treatment in the past. received antiviral therapy for any systemic anti-viral, anti-neoplastic or immuno-modulatory treatment (including supraphysiologic doses of steroids and radiation) within the past 6 months. Positive test at screening for anti-HIV, anti-HCV. Patients who are expected to need systemic antiviral therapy other than that provided by the study at any time during their participation in the study are also excluded. Exception: patients who have had a limited (<=7 days) course of acyclovir for herpetic lesions more than 1 month prior to the first administration of test drug are not excluded. Serum total bilirubin > 3 times the upper limit of normal at screening. History or other evidence of bleeding from esophageal varices or other conditions consistent with decompensated liver disease. History or other evidence of a medical condition associated with chronic liver disease other than HBV (e.g., hemochromatosis, autoimmune hepatitis, metabolic liver diseases including Wilson's and alpha1-antitrypsin deficiency, alcoholic liver disease, toxin exposures, thalassemia). Women with ongoing pregnancy or who are breast feeding. Neutrophil count <1500 cells/mm3 or platelet count <90,000 cells/mm3 at screening. Hemoglobin < 11.5 g/dL for females and < 12.5 g/dL for men at screening. Serum creatinine level >120 umol/ml for men and >105 umol/ml for women at screening. History of severe psychiatric disease, especially depression. Severe psychiatric disease is defined as major depression or psychosis, a period of treatment with an antidepressant medication or major tranquilizer at therapeutic doses for depression or psychosis for at least 3 months, a suicidal attempt, hospitalization for psychiatric disease, or a period of disability due to a psychiatric disease. History of immunologically mediated disease (e.g., inflammatory bowel disease, idiopathic thrombocytopenic purpura, lupus erythematosus, autoimmune hemolytic anemia, scleroderma, severe psoriasis, rheumatoid arthritis). History or other evidence of chronic pulmonary disease associated with functional limitation. Severe cardiac disease (e.g., NYHA Functional Class III or IV, myocardial infarction within 6 months, ventricular tachyarrhythmias requiring ongoing treatment, unstable angina or other significant cardiovascular diseases). History of a severe seizure disorder or current anticonvulsant use. Evidence of an active or suspected cancer or a history of malignancy where the risk of recurrence is >=20% within 2 years. Patients with a lesion suspicious of hepatic malignancy on a screening imaging study will only be eligible if the likelihood of carcinoma is <=10% following an appropriate evaluation. History of having received any systemic anti-neoplastic (including radiation) or immunomodulatory treatment (including systemic corticosteroids) <=6 months prior to the first dose of study drug or the expectation that such treatment will be needed at any time during the study. Major organ transplantation. Thyroid disease with thyroid function poorly controlled on prescribed medications. Patients with abnormal thyroid stimulating hormone or T4 concentrations, with elevation of antibodies to thyroid peroxidase and any clinical manifestations of thyroid disease are excluded. History or other evidence of severe retinopathy (e.g. CMV retinitis, macula degeneration) or clinically relevant ophthalmological disorder due to diabetes mellitus or hypertension Inability or unwillingness to provide informed consent or abide by the requirements of the study. History or other evidence of severe illness or any other conditions which would make the patient, in the opinion of the investigator, unsuitable for the study. Patients with a value of alpha-fetoprotein >100 ng/mL are excluded, unless stability (less than 10% increase) has been documented over at least the previous 3 months. Evidence of drug and/or alcohol abuse (20g/day for women & 30g/day for men). Patients included in another trial or having been given investigational drugs within 12 weeks prior to screening Any known history of hypersensitivity to interferon.", "candidate_expression": "((< 11.5 g/dL) AND (< 12.5 g/dL) AND (<1500 cells/mm3) AND (<90,000 cells/mm3) AND (<=10%) AND (<=6 months prior to the first dose of study drug) AND (<=7 days) AND (> 3 times the upper limit of normal) AND (>100 ng/mL) AND (>105 umol/ml) AND (>120 umol/ml) AND (>=20% within 2 years) AND (B-C) AND (Childs) AND (Exception) AND (Functional Class III or IV) AND (HBV) AND (Hemoglobin) AND (History or other evidence of severe illness or any other conditions which would make the patient, in the opinion of the investigator, unsuitable for the study.) AND (Inability or unwillingness to provide informed consent or abide by the requirements of the study.) AND (Major organ transplantation) AND (Patients included in another trial or having been given investigational drugs within 12 weeks prior to screening) AND (Positive) AND (Serum creatinine level) AND (Serum total bilirubin) AND (Severe) AND (Thyroid disease) AND (Women) AND (abnormal) AND (acyclovir) AND (alpha-fetoprotein) AND (at any time during the study) AND (at any time during their participation in the study) AND (at least the previous 3 months) AND (at screening) AND (cardiac disease) AND (chronic liver disease) AND (chronic pulmonary disease) AND (corticosteroids) AND (current) AND (decompensated) AND (depression) AND (elevation) AND (esophageal varices) AND (expectation) AND (expected to need) AND (for at least 3 months) AND (functional limitation) AND (hepatic malignancy) AND (herpetic lesions) AND (hypersensitivity) AND (immunologically mediated disease) AND (in the past) AND (increase) AND (interferon) AND (lesion) AND (less than 10%) AND (likelihood of carcinoma) AND (limited course) AND (liver disease) AND (medical condition) AND (men) AND (more than 1 month prior to the first administration of test drug) AND (not excluded) AND (on prescribed medications) AND (ongoing) AND (other) AND (other than) AND (poorly controlled) AND (pre-existing) AND (psychiatric disease) AND (radiation) AND (retinopathy) AND (risk of recurrence) AND (screening imaging study) AND (severe) AND (significant) AND (stability) AND (supraphysiologic doses) AND (suspicious) AND (systemic) AND (systemic anti-viral) AND (systemic antiviral therapy) AND (telbivudine) AND (the first administration of test drug) AND (the first dose of study drug) AND (the previous 3 months) AND (their participation in the study) AND (therapeutic doses) AND (thyroid function) AND (treatment) AND (unless) AND (will be needed) AND (within 6 months) AND (within the past 6 months) AND (women) AND ((depression) OR (psychiatric disease)) AND ((Severe) OR (psychiatric disease)) AND ((antidepressant medication) OR (major tranquilizer)) AND ((disability) OR (hospitalization) OR (major depression) OR (psychosis) OR (suicidal attempt) OR (treatment)) AND ((cardiac disease) OR (hepato-cellular carcinoma) OR (renal disease) OR (retinopathy) OR (seizure disorders) OR (severe)) AND ((autoimmune hemolytic anemia) OR (idiopathic thrombocytopenic purpura) OR (inflammatory bowel disease) OR (lupus erythematosus) OR (psoriasis) OR (rheumatoid arthritis) OR (scleroderma)) AND ((NYHA) OR (cardiovascular diseases) OR (myocardial infarction) OR (unstable angina) OR (ventricular tachyarrhythmias)) AND ((anticonvulsant) OR (seizure disorder)) AND ((active) OR (suspected)) AND ((cancer) OR (malignancy)) AND ((anti-neoplastic treatment) OR (immunomodulatory treatment)) AND ((T4 concentrations) OR (thyroid stimulating hormone)) AND ((antibodies to thyroid peroxidase) OR (clinical manifestations of thyroid disease)) AND ((CMV retinitis) OR (macula degeneration)) AND ((clinically relevant) OR (ophthalmological disorder)) AND ((diabetes mellitus) OR (hypertension)) AND ((alcohol abuse) OR (drug abuse)) AND ((20g/day) OR (30g/day)) AND ((NA) OR (antiviral therapy) OR (more than one)) AND ((interferon) OR (peginterferon)) AND ((anti-neoplastic treatment) OR (antiviral therapy) OR (immuno-modulatory treatment)) AND ((radiation) OR (steroids)) AND ((test for anti-HCV) OR (test for anti-HIV)) AND ((bleeding) OR (conditions consistent with decompensated liver disease)) AND ((autoimmune hepatitis) OR (hemochromatosis) OR (metabolic liver diseases)) AND ((Wilson's) OR (alcoholic liver disease) OR (alpha1-antitrypsin deficiency) OR (thalassemia) OR (toxin exposures)) AND ((breast feeding) OR (pregnancy)) AND ((Neutrophil count) OR (platelet count)) AND ((females) OR (men)))"}
{"candidate_id": "LLM03207", "doc_id": "NCT01943409_inc", "case_bucket": "or", "source_criterion": "Patients with PN during their hospitalization Patients hospitalized in medical, surgical or ICU wards Signed informed consent either from the patient, their legally authorized representative or a direct family member", "candidate_expression": "((PN during their hospitalization) AND (Signed informed consent either from the patient, their legally authorized representative or a direct family member) AND (hospitalization) AND (hospitalized) AND ((ICU wards) OR (medical wards) OR (surgical wards)))"}
{"candidate_id": "LLM03208", "doc_id": "NCT03328052_exc", "case_bucket": "or", "source_criterion": "Diagnosis of a psychotic disorder. History of, or current, open head brain trauma. Candidates with any metal, shrapnel or other similar objects in the head that could affect the QEEG History of: craniotomy, cerebral metastases, cerebrovascular accident; current diagnosis of seizure disorder, schizophrenia, schizo-affective disorder, dementia, mental retardation, or major depression with psychotic features; or use of depot neuroleptics in last 12 months. Uncontrolled thyroid disorders. Known pregnancy and/or lactation, or intent to become pregnant during this study. Chronic or acute pain requiring prescription pain medication(s) (narcotic or synthetic narcotic) Participation in any other therapeutic drug study within 60 days preceding inclusion.", "candidate_expression": "((History current) AND (Known pregnancy and/or lactation, or intent to become pregnant during this study.) AND (Participation in any other therapeutic drug study within 60 days preceding inclusion.) AND (QEEG) AND (affect) AND (cerebral metastases) AND (cerebrovascular accident) AND (craniotomy) AND (dementia) AND (depot neuroleptics in last 12 months) AND (major depression) AND (mental retardation) AND (metal) AND (narcotic) AND (objects in the head) AND (open head brain trauma) AND (pain Chronic acute) AND (prescription pain medication) AND (psychotic disorder) AND (psychotic features) AND (schizo-affective disorder) AND (schizophrenia) AND (seizure disorder) AND (shrapnel) AND (synthetic narcotic) AND (thyroid disorders Uncontrolled))"}
{"candidate_id": "LLM03209", "doc_id": "NCT03226080_exc", "case_bucket": "or", "source_criterion": "Inability to consent/refusal Allergy to any of the study medications Multiple traumatic injuries Contraindication to neuraxial or general anesthesia Pregnancy", "candidate_expression": "((Allergy) AND (Contraindication) AND (Inability to consent) AND (Multiple traumatic injuries) AND (Pregnancy) AND (general anesthesia) AND (neuraxial anesthesia) AND (refusal) AND (study medications))"}
{"candidate_id": "LLM03210", "doc_id": "NCT01175044_exc", "case_bucket": "other", "source_criterion": "Inability to provide informed consent or to comply with study assessments (e.g. due to cognitive impairment or geographic distance). Age = 17. Allergy to povidone iodine. Any condition requiring antibiotics 14 days prior to arriving for surgery. Patients with chronic immunosuppression (such as HIV/AIDS). Unable to adhere to follow up schedule and treatment. Patients scheduled to undergo revision total knee arthroplasty for infectious reasons.", "candidate_expression": "((14 days prior to arriving for surgery) AND (= 17) AND (Age) AND (Allergy) AND (HIV/AIDS) AND (Inability to provide informed consent or to comply with study assessments (e.g. due to cognitive impairment or geographic distance).) AND (Unable to adhere to follow up schedule and treatment.) AND (antibiotics) AND (arriving for surgery) AND (chronic) AND (immunosuppression) AND (infectious reasons) AND (povidone iodine) AND (revision total knee arthroplasty) AND (surgery))"}
{"candidate_id": "LLM03211", "doc_id": "NCT00122070_exc", "case_bucket": "or", "source_criterion": "Are pregnant or lactating. Have participated in any other studies involving investigational products within 30 days prior to entry into this study. Are undergoing an acute withdrawal syndrome from drugs or alcohol. Have an Axis I diagnosis of Schizophrenia, Schizoaffective Disorder, Schizophreniform Disorder or Bipolar I Disorder as diagnosed by the Structured Clinical Interview for DSM-IV Axis I Disorders (SCID-I), and pertinent subsequent for ruling out exclusionary diagnoses. Have an unstable medical disorder as determined by physical examination or laboratory testing. The primary investigator will be responsible for making this judgment based on the above. Had an unsatisfactory response to a previous adequate trial of quetiapine as judged by a study investigator. Patients cannot begin psychotherapy during the study period, but may continue if started prior to the study. Patients who are currently receiving quetiapine therapy may not undergo a washout period and then restart quetiapine in the study.", "candidate_expression": "((Bipolar I Disorder) AND (Have participated in any other studies involving investigational products within 30 days prior to entry into this study) AND (Schizoaffective Disorder) AND (Schizophrenia) AND (Schizophreniform Disorder) AND (Structured Clinical Interview for DSM-IV Axis I Disorders (SCID-I)) AND (acute withdrawal syndrome) AND (alcohol) AND (drugs) AND (lactating) AND (pregnant))"}
{"candidate_id": "LLM03212", "doc_id": "NCT03350815_exc", "case_bucket": "other", "source_criterion": "NA", "candidate_expression": "(EMPTY)"}
{"candidate_id": "LLM03213", "doc_id": "NCT00543712_inc", "case_bucket": "or", "source_criterion": "Ability to understand and willingness to sign a written informed consent document Age ≥ 18 years Histologic diagnosis of chondrosarcoma, verifiable after enrollment Measurable disease Previously treated or incurable disease without options for standard of care therapy ECOG performance status of 0-2 Life expectancy of > 3 months For patients of reproductive potential (males and females), use of reliable means for contraception (e.g., contraceptive pill, intrauterine device [IUD], physical barrier) throughout the trial and for 1 year following their final exposure to study treatment", "candidate_expression": "((Age ≥ 18 years) AND (ECOG performance status 0-2) AND (Histologic) AND (Life expectancy > 3 months) AND (chondrosarcoma) AND (contraception throughout the trial for 1 year following their final exposure) AND (reproductive potential) AND ((contraceptive pill) OR (intrauterine device [IUD]) OR (physical barrier)))"}
{"candidate_id": "LLM03214", "doc_id": "NCT02062489_exc", "case_bucket": "or", "source_criterion": "The patients have other cancers at the same time or have the history of other cancers except controlled skin basal cell carcinoma or skin squamous cell carcinoma or carcinoma in situ of cervix uterus; The patients have active infections that were not suitable for chemotherapy; The patients have severe non-cancerous diseases. The patients have history of neoadjuvant hormone therapy. The patients have bilateral breast cancers or DCIS or metastatic breast cancers. The patients are undergoing current administration of anti-cancer therapies, or are attending other clinical trials. The patients are pregnant or lactational, or they refuse to practice contraception during the whole trial. The patients are in some special conditions that they can't understand the written informed consent, such as they are demented or hawkish. The patients have allergic history or contraindication of tamoxifen.", "candidate_expression": "((The patients are in some special conditions that they can't understand the written informed consent, such as they are demented or hawkish.) AND (active) AND (at the same time) AND (during the whole trial) AND (except) AND (infections) AND (neoadjuvant hormone therapy) AND (non-cancerous diseases) AND (not) AND (refuse to practice) AND (severe) AND (suitable for chemotherapy) AND (tamoxifen) AND ((other cancers)) AND ((DCIS) OR (bilateral breast cancers) OR (metastatic breast cancers)) AND ((anti-cancer therapies) OR (attending other clinical trials)) AND ((contraception) OR (lactational) OR (pregnant)) AND ((allergic) OR (contraindication)) AND ((carcinoma in situ of cervix uterus) OR (controlled skin basal cell carcinoma) OR (skin squamous cell carcinoma)))"}
{"candidate_id": "LLM03215", "doc_id": "NCT03249272_inc", "case_bucket": "or", "source_criterion": "Men or women aged 18 years or older Patients presenting for CMR with the clinical diagnosis of hypertrophic cardiomyopathy based on left ventricular wall thickness of at least =15 mm in the absence of any other cardiac or systemic cause of hypertrophy Patients presenting for CMR with the clinical diagnosis of idiopathic dilated cardiomyopathy based upon left ventricular ejection fraction =40%, LV end-diastolic diameter =55 mm or left ventricular end-systolic diameter =45 mm, and the absence of coronary stenoses on angiography. Patients presenting for CMR evaluation of chest pain but without evidence of obstructive coronary artery disease either by coronary angiography or stress testing.", "candidate_expression": "((LV end-diastolic diameter =55 mm) AND (Men) AND (aged 18 years or older) AND (angiography) AND (cardiac cause of hypertrophy) AND (chest pain) AND (coronary angiography) AND (hypertrophic cardiomyopathy) AND (idiopathic dilated cardiomyopathy) AND (left ventricular ejection fraction =40%) AND (left ventricular end-systolic diameter =45 mm) AND (left ventricular wall thickness at least =15 mm) AND (stress testing) AND (systemic cause of hypertrophy) AND (women) AND NOT (coronary stenoses) AND NOT (obstructive coronary artery disease))"}
{"candidate_id": "LLM03216", "doc_id": "NCT02816762_exc", "case_bucket": "or", "source_criterion": "Non diabetic nephropathy (confirmed by biopsy). Dialysis for acute renal failure within the 6 previous months. Evidence in the clinic history of relevant bilateral stenosis of renal artery (> 75%) Urinary albumin/creatinine ratio higher than 3000 mg/g, at the baseline visit. Systolic blood pressure = 180 mmHg or diastolic blood pressure = 110 mm Hg at the baseline visit. Stroke, transient ischemic attack, acute coronary syndrome, or hospitalization for heart failure worsening, within the previous 30 days. Professional drivers, risk profession or respiratory failure. Severe daytime sleepiness (Epworth sleepiness scale >18) Concomitant treatment with high doses of acetylsalicylic acid (> 500 mg/day) or continuous treatment with non-steroidal anti-inflammatory drugs Previous treatment with CPAP Participation in another clinical trial within the 30 days prior to randomization.", "candidate_expression": "((= 110 mm Hg) AND (= 180 mmHg) AND (> 500 mg/day) AND (> 75%) AND (>18) AND (CPAP) AND (Concomitant) AND (Dialysis) AND (Epworth sleepiness scale) AND (Non diabetic nephropathy) AND (Previous) AND (Severe) AND (Urinary albumin/creatinine ratio) AND (acetylsalicylic acid) AND (acute renal failure) AND (at the baseline visit) AND (bilateral) AND (biopsy) AND (confirmed by biopsy) AND (continuous) AND (daytime sleepiness) AND (heart failure) AND (high doses) AND (higher than 3000 mg/g) AND (non-steroidal anti-inflammatory drugs) AND (relevant) AND (stenosis of renal artery) AND (treatment) AND (within the 6 previous months) AND (within the previous 30 days) AND (worsening) AND ((Systolic blood pressure) OR (diastolic blood pressure)) AND ((Stroke) OR (acute coronary syndrome) OR (hospitalization) OR (transient ischemic attack)) AND ((Professional drivers) OR (respiratory failure) OR (risk profession)) AND ((treatment)))"}
{"candidate_id": "LLM03217", "doc_id": "NCT02156999_exc", "case_bucket": "or", "source_criterion": "Kidney, parathyroid, congenital bone metabolic disease", "candidate_expression": "((disease) AND ((Kidney) OR (bone) OR (congenital) OR (metabolic) OR (parathyroid)))"}
{"candidate_id": "LLM03218", "doc_id": "NCT00599924_exc", "case_bucket": "other", "source_criterion": "Prior treatment with more than 6 cycles of traditional alkylating agent-based chemotherapy regimens Prior treatment with more than 2 cycles of carboplating-based chemotherapy regimens For colorectal cancer patients in the expanded cohorts, prior treatment with more than 2 systemic chemotherapy regimens in the metastatic setting", "candidate_expression": "((chemotherapy regimens Prior alkylating agent-based) AND (chemotherapy regimens Prior carboplating-based) AND (colorectal cancer) AND (systemic chemotherapy regimens prior metastatic) AND (treatment more than 2) AND (treatment more than 2 cycles) AND (treatment more than 6 cycles))"}
{"candidate_id": "LLM03219", "doc_id": "NCT02394158_inc", "case_bucket": "other", "source_criterion": "Singleton pregnancy; 8-22 weeks gestation Previous pregnancy complicated by gestational diabetes", "candidate_expression": "((Singleton pregnancy) AND (gestation 8-22 weeks) AND (gestational diabetes) AND (pregnancy))"}
{"candidate_id": "LLM03220", "doc_id": "NCT00356148_exc", "case_bucket": "or", "source_criterion": "Ductal carcinoma in situ (DCIS; stage 0 cancer), Advanced or distant metastatic stage, Receiving any neoadjuvant therapy, History of receiving any antibiotics within prior 3 months, History of immunodeficiency, Having a remote infection, History of reaction to study antibiotics, Denial of signing the consent form.", "candidate_expression": "((DCIS) AND (Ductal carcinoma in situ) AND (History) AND (antibiotics within prior 3 months) AND (cancer Advanced metastatic distant metastatic) AND (immunodeficiency) AND (neoadjuvant therapy) AND (reaction) AND (remote infection) AND (stage) AND (stage 0) AND (study antibiotics) AND NOT (signing the consent form))"}
{"candidate_id": "LLM03221", "doc_id": "NCT03040024_inc", "case_bucket": "or", "source_criterion": "Current diagnosis of otolaryngeal cancer and undergoing surgery with general anesthesia Competent to provide informed consent", "candidate_expression": "((Competent to provide informed consent) AND (general anesthesia) AND ((otolaryngeal cancer) OR (surgery undergoing)))"}
{"candidate_id": "LLM03222", "doc_id": "NCT03084588_exc", "case_bucket": "or", "source_criterion": "Preoperative renal failure requiring dialysis Poorly controlled pulmonary disease (severe asthma or COPD) -Contraindication to regional anesthesia (recent anticoagulant use) Sleep apnea or morbid obesity with possible sleep apnea Allergy to methadone Significant preoperative pain requiring treatment with high doses of opioids (more than 6-8 Norco tablets or equivalence per day) or recent history of opioid abuse", "candidate_expression": "((Allergy) AND (Contraindication) AND (Norco tablets more than 6-8 per day) AND (anticoagulant recent) AND (dialysis requiring) AND (equivalence) AND (methadone) AND (opioids requiring high doses) AND (pulmonary disease Poorly controlled) AND (regional anesthesia) AND (renal failure Preoperative) AND (sleep apnea possible) AND ((Sleep apnea) OR (morbid obesity)) AND ((opioid abuse recent history) OR (preoperative pain Significant)) AND ((COPD) OR (asthma)))"}
{"candidate_id": "LLM03223", "doc_id": "NCT01531257_inc", "case_bucket": "or", "source_criterion": "1. Male and female recipients of all races, ≥18 years of age. 2. Patients undergoing primary or subsequent deceased-donor or living donor kidney transplantation. 3. Subject and/or guardian must be able to provide informed consent. 4. Subject and/or guardian must be able to comply with the study protocol.", "candidate_expression": "((Male) AND (Subject and/or guardian must be able to comply with the study protocol.) AND (Subject and/or guardian must be able to provide informed consent.) AND (age ≥18 years primary subsequent) AND (deceased-donor kidney transplantation) AND (female) AND (living donor kidney transplantation))"}
{"candidate_id": "LLM03224", "doc_id": "NCT03339284_exc", "case_bucket": "or", "source_criterion": "age under 18y or over 85y diabetes type 1 with complications no co-operation or inadequate finnish language skills persistent pain for other reason severe hepatic insufficiency or paracetamol (acetaminophen) is contraindicated for other reason any type of steroid in regular use oxycodone contraindicated medications changing notably paracetamol (acetaminophen) and/or ropivacaine metabolism in regular use", "candidate_expression": "((acetaminophen) AND (age) AND (co-operation) AND (complications) AND (contraindicated) AND (diabetes type 1) AND (hepatic insufficiency) AND (inadequate finnish language skills) AND (no) AND (other reason) AND (oxycodone) AND (paracetamol) AND (persistent pain) AND (regular use) AND (ropivacaine) AND (severe) AND (steroid) AND (under 18y or over 85y))"}
{"candidate_id": "LLM03225", "doc_id": "NCT02564471_inc", "case_bucket": "or", "source_criterion": "Provide signed and dated informed consent form. Willing to comply with all study procedures and be available for the duration of the study. Male or female, aged = 18 to = 60 years on day of inclusion. In good general health based on medical history and physical exam", "candidate_expression": "((Willing to comply with all study procedures and be available for the duration of the study.) AND (aged = 18 to = 60 years) AND (good general health medical history) AND (physical exam) AND ((Male) OR (female)))"}
```
