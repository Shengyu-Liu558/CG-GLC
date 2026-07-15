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
{"candidate_id": "LLM00451", "doc_id": "NCT03113253_exc", "case_bucket": "or", "source_criterion": "Subjects with a history of hypercoagulopathy, deep vein thrombosis (DVT), pulmonary embolism Renal impairment Subjects with known hypersensitivity to tranexamic acid Consecutive fibrinolytic states to coagulopathy History of convulsions", "candidate_expression": "((DVT) AND (Renal impairment) AND (coagulopathy) AND (convulsions History) AND (fibrinolytic states) AND (history) AND (hypersensitivity) AND (tranexamic acid) AND ((deep vein thrombosis) OR (hypercoagulopathy) OR (pulmonary embolism)))"}
{"candidate_id": "LLM00452", "doc_id": "NCT03530124_exc", "case_bucket": "or", "source_criterion": "Receipt of DTaP, IPV, PCV13, or Hib prior to enrollment. Previous administration of the first dose of HBV is permitted Anticipated receipt of any vaccine other than DTaP, IPV, HBV, PCV13, or Hib during the first 60 hours after randomization History of a severe allergic reaction (e.g. anaphylaxis) to a previous dose of any hepatitis B vaccine History of a severe allergic reaction (e.g. anaphylaxis) to any component of the vaccines used in the study including neomycin, yeast and polymyxin B History of latex allergy History of unstable progressive neurologic disorder of unknown cause Known cause of apnea other than apnea of prematurity Cyanotic heart disease (congenital or acquired) Child or parent/LAR is an immediate relative of study staff or an employee who is supervised by study staff. Any condition that would, in the opinion of the site investigator, place the participant at an unacceptable risk of injury or render the participant unable to meet the requirements of the protocol", "candidate_expression": "((Cyanotic heart disease congenital acquired) AND (DTaP) AND (HBV) AND (Hib) AND (Hib enrollment) AND (IPV) AND (Known cause of apnea) AND (PCV13) AND (allergic reaction severe) AND (allergy History) AND (anaphylaxis) AND (component of the vaccines used in the study) AND (hepatitis B vaccine previous) AND (latex) AND (neomycin) AND (polymyxin B) AND (progressive neurologic disorder History unstable unknown cause) AND (yeast) AND NOT (apnea of prematurity))"}
{"candidate_id": "LLM00453", "doc_id": "NCT03366779_inc", "case_bucket": "or", "source_criterion": "Age 18 to 75 years old (male or female). Patients with posterior or posterolateral disc herniations at one level between L1 and S1 with radiographic confirmation of neural compression using CT and/or MRI. At least six (6) weeks of failed, conservative treatment prior to surgery, or requires immediate surgery to prevent permanent disability. Minimum posterior disc height of 5mm at the index level(s). Lower back pain and/or sciatica with or without spinal claudication. Oswestry Questionnaire score of at least 40/100 at baseline. VAS leg pain of at least 40/100 at baseline. Psychosocially, mentally and physically able to fully comply with the clinical protocol and willing to adhere to follow-up schedule and requirements.", "candidate_expression": "((Age 18 to 75 years old) AND (Oswestry Questionnaire score at least 40/100 at baseline) AND (Psychosocially, mentally and physically able to fully comply with the clinical protocol and willing to adhere to follow-up schedule and requirements.) AND (VAS leg pain at least 40/100 at baseline) AND (disc herniations one level between L1 and S1 radiographic confirmation) AND (neural compression) AND (permanent disability prevent) AND (posterior disc height Minimum of 5mm index level(s)) AND (radiographic) AND (spinal claudication) AND ((CT) OR (MRI)) AND ((surgery immediate) OR (treatment At least six (6) weeks failed conservative prior to surgery)) AND ((Lower back pain) OR (sciatica)) AND ((female) OR (male)) AND ((posterior) OR (posterolateral)))"}
{"candidate_id": "LLM00454", "doc_id": "NCT02593409_inc", "case_bucket": "other", "source_criterion": "age =18 at screening not intending to move away from the clinic's catchment area for the next 2 years HIV-1 antibody negative reports commercial sex work contact information is provided written informed consent", "candidate_expression": "((HIV-1 antibody negative) AND (age =18) AND (commercial sex work) AND (contact information is provided) AND (written informed consent))"}
{"candidate_id": "LLM00455", "doc_id": "NCT02068365_exc", "case_bucket": "or", "source_criterion": "Evidence of decompensated liver disease (Childs B-C), hepato-cellular carcinoma, pre-existing severe depression or other psychiatric disease, significant cardiac disease, significant renal disease, seizure disorders or severe retinopathy. received telbivudine as the antiviral therapy or have received more than one NA in the past. received interferon or peginterferon treatment in the past. received antiviral therapy for any systemic anti-viral, anti-neoplastic or immuno-modulatory treatment (including supraphysiologic doses of steroids and radiation) within the past 6 months. Positive test at screening for anti-HIV, anti-HCV. Patients who are expected to need systemic antiviral therapy other than that provided by the study at any time during their participation in the study are also excluded. Exception: patients who have had a limited (<=7 days) course of acyclovir for herpetic lesions more than 1 month prior to the first administration of test drug are not excluded. Serum total bilirubin > 3 times the upper limit of normal at screening. History or other evidence of bleeding from esophageal varices or other conditions consistent with decompensated liver disease. History or other evidence of a medical condition associated with chronic liver disease other than HBV (e.g., hemochromatosis, autoimmune hepatitis, metabolic liver diseases including Wilson's and alpha1-antitrypsin deficiency, alcoholic liver disease, toxin exposures, thalassemia). Women with ongoing pregnancy or who are breast feeding. Neutrophil count <1500 cells/mm3 or platelet count <90,000 cells/mm3 at screening. Hemoglobin < 11.5 g/dL for females and < 12.5 g/dL for men at screening. Serum creatinine level >120 umol/ml for men and >105 umol/ml for women at screening. History of severe psychiatric disease, especially depression. Severe psychiatric disease is defined as major depression or psychosis, a period of treatment with an antidepressant medication or major tranquilizer at therapeutic doses for depression or psychosis for at least 3 months, a suicidal attempt, hospitalization for psychiatric disease, or a period of disability due to a psychiatric disease. History of immunologically mediated disease (e.g., inflammatory bowel disease, idiopathic thrombocytopenic purpura, lupus erythematosus, autoimmune hemolytic anemia, scleroderma, severe psoriasis, rheumatoid arthritis). History or other evidence of chronic pulmonary disease associated with functional limitation. Severe cardiac disease (e.g., NYHA Functional Class III or IV, myocardial infarction within 6 months, ventricular tachyarrhythmias requiring ongoing treatment, unstable angina or other significant cardiovascular diseases). History of a severe seizure disorder or current anticonvulsant use. Evidence of an active or suspected cancer or a history of malignancy where the risk of recurrence is >=20% within 2 years. Patients with a lesion suspicious of hepatic malignancy on a screening imaging study will only be eligible if the likelihood of carcinoma is <=10% following an appropriate evaluation. History of having received any systemic anti-neoplastic (including radiation) or immunomodulatory treatment (including systemic corticosteroids) <=6 months prior to the first dose of study drug or the expectation that such treatment will be needed at any time during the study. Major organ transplantation. Thyroid disease with thyroid function poorly controlled on prescribed medications. Patients with abnormal thyroid stimulating hormone or T4 concentrations, with elevation of antibodies to thyroid peroxidase and any clinical manifestations of thyroid disease are excluded. History or other evidence of severe retinopathy (e.g. CMV retinitis, macula degeneration) or clinically relevant ophthalmological disorder due to diabetes mellitus or hypertension Inability or unwillingness to provide informed consent or abide by the requirements of the study. History or other evidence of severe illness or any other conditions which would make the patient, in the opinion of the investigator, unsuitable for the study. Patients with a value of alpha-fetoprotein >100 ng/mL are excluded, unless stability (less than 10% increase) has been documented over at least the previous 3 months. Evidence of drug and/or alcohol abuse (20g/day for women & 30g/day for men). Patients included in another trial or having been given investigational drugs within 12 weeks prior to screening Any known history of hypersensitivity to interferon.", "candidate_expression": "((CMV retinitis) AND (Childs B-C) AND (Hemoglobin at screening) AND (History or other evidence of severe illness or any other conditions which would make the patient, in the opinion of the investigator, unsuitable for the study.) AND (Inability or unwillingness to provide informed consent or abide by the requirements of the study.) AND (Major organ transplantation) AND (NA in the past more than one) AND (NYHA Functional Class III or IV) AND (Neutrophil count <1500 cells/mm3) AND (Patients included in another trial or having been given investigational drugs within 12 weeks prior to screening) AND (Serum creatinine level at screening) AND (Serum total bilirubin > 3 times the upper limit of normal at screening) AND (T4 concentrations) AND (Thyroid disease) AND (Wilson's) AND (Women) AND (alcohol abuse) AND (alcoholic liver disease) AND (alpha-fetoprotein >100 ng/mL) AND (alpha1-antitrypsin deficiency) AND (anti-neoplastic treatment) AND (antibodies to thyroid peroxidase elevation) AND (anticonvulsant current active) AND (antidepressant medication) AND (antiviral therapy) AND (autoimmune hemolytic anemia) AND (autoimmune hepatitis) AND (bleeding) AND (breast feeding) AND (cancer suspected) AND (cardiac disease Severe) AND (cardiac disease significant) AND (cardiovascular diseases other significant) AND (chronic liver disease) AND (chronic pulmonary disease) AND (clinical manifestations of thyroid disease) AND (conditions consistent with decompensated liver disease other) AND (corticosteroids systemic) AND (depression) AND (depression Severe) AND (depression severe) AND (diabetes mellitus) AND (disability) AND (drug abuse 20g/day) AND (esophageal varices) AND (females < 11.5 g/dL) AND (functional limitation) AND (hemochromatosis) AND (hepatic malignancy suspicious) AND (hepato-cellular carcinoma) AND (herpetic lesions) AND (hospitalization) AND (hypersensitivity) AND (hypertension) AND (idiopathic thrombocytopenic purpura) AND (immuno-modulatory treatment) AND (immunologically mediated disease) AND (immunomodulatory treatment) AND (increase less than 10%) AND (inflammatory bowel disease) AND (interferon) AND (lesion) AND (likelihood of carcinoma <=10%) AND (liver disease decompensated) AND (lupus erythematosus) AND (macula degeneration clinically relevant) AND (major depression) AND (major tranquilizer) AND (malignancy) AND (medical condition) AND (men) AND (men < 12.5 g/dL) AND (men >120 umol/ml) AND (metabolic liver diseases) AND (myocardial infarction within 6 months) AND (ophthalmological disorder) AND (peginterferon) AND (platelet count <90,000 cells/mm3) AND (pregnancy ongoing) AND (psoriasis severe) AND (psychiatric disease) AND (psychiatric disease other) AND (psychiatric disease severe) AND (psychosis) AND (psychosis for at least 3 months) AND (radiation) AND (radiation supraphysiologic doses) AND (renal disease significant) AND (retinopathy) AND (retinopathy severe) AND (rheumatoid arthritis) AND (risk of recurrence >=20% within 2 years) AND (scleroderma) AND (screening imaging study) AND (seizure disorder severe) AND (seizure disorders severe) AND (steroids supraphysiologic doses) AND (suicidal attempt) AND (systemic anti-viral) AND (systemic antiviral therapy expected to need at any time during their participation in the study) AND (telbivudine) AND (test for anti-HCV) AND (test for anti-HIV) AND (thalassemia) AND (thyroid function poorly controlled on prescribed medications) AND (thyroid stimulating hormone) AND (toxin exposures) AND (treatment) AND (treatment expectation will be needed at any time during the study) AND (treatment in the past) AND (treatment ongoing) AND (unstable angina) AND (ventricular tachyarrhythmias) AND (women 30g/day) AND (women >105 umol/ml) AND NOT (stability at least the previous 3 months) AND NOT (acyclovir limited course more than 1 month prior to the first administration of test drug not excluded <=7 days) AND NOT (HBV))"}
{"candidate_id": "LLM00456", "doc_id": "NCT01491295_exc", "case_bucket": "or", "source_criterion": "HCV, HIV, HDV coinfection. Uncontrolled HCC, malignancy or decompensated liver cirrhosis (CTP score = 7). Uremia patients or Creatinine = 2 mg/dl.", "candidate_expression": "((= 2 mg/dl) AND (= 7) AND (CTP score) AND (Uncontrolled) AND (decompensated) AND ((HCV coinfection) OR (HDV coinfection) OR (coinfection HIV)) AND ((Creatinine) OR (Uremia)) AND ((HCC) OR (liver cirrhosis) OR (malignancy)))"}
{"candidate_id": "LLM00457", "doc_id": "NCT02982577_inc", "case_bucket": "other", "source_criterion": "Age equal or superior to 18 years; Both genders; Lucid and without diagnosis of any psychiatric disorder; Diagnosed with head and neck cancer and treated for a period of up to 5 years with radiotherapy where the major salivary glands (parotid, submandibular and sublingual) were included in the radiation field; Primary Sjögren's syndrome with the diagnosis made by the American-European criteria.", "candidate_expression": "((Age equal or superior to 18 years) AND (Lucid) AND (Primary Sjögren's syndrome American-European criteria) AND (genders) AND (head and neck cancer 5 years) AND (radiotherapy major salivary glands parotid submandibular sublingual) AND NOT (psychiatric disorder))"}
{"candidate_id": "LLM00458", "doc_id": "NCT02548013_exc", "case_bucket": "other", "source_criterion": "1. Patient with equivocal diagnosis of rupture of membranes 2. advanced labor 3. intrauterine infection 4. vaginal bleeding or 5. non reassuring fetal heart rate.", "candidate_expression": "((advanced labor) AND (fetal heart rate non reassuring) AND (intrauterine infection) AND (non reassuring) AND (vaginal bleeding) AND NOT (rupture of membranes))"}
{"candidate_id": "LLM00459", "doc_id": "NCT02701777_exc", "case_bucket": "or", "source_criterion": "Uncontrolled medical problems including pulmonary, cardiovascular or orthopedic disease Any debilitating disease prior to the SCI that caused exercise intolerance Premorbid, ongoing major depression or psychosis, altered cognitive status History of head injury or stroke Metal plate in skull History of seizures Receiving drugs acting primarily on the central nervous system, which lower the seizure threshold (see appendix 2) Pregnant females Ongoing cord compression or a syrinx in the spinal cord or who suffer from a spinal cord disease such as spinal stenosis, spina bifida, MS, or herniated disk Individuals with scalp shrapnel, cochlear implants, or aneurysm clips.", "candidate_expression": "((MS) AND (Metal plate in skull) AND (Pregnant) AND (altered cognitive status) AND (aneurysm clips) AND (cardiovascular disease) AND (cochlear implants) AND (cord compression) AND (debilitating disease prior to the SCI) AND (drugs acting primarily on the central nervous system lower the seizure threshold) AND (exercise intolerance) AND (females) AND (head injury) AND (herniated disk) AND (major depression) AND (medical problems Uncontrolled) AND (orthopedic disease) AND (psychosis) AND (pulmonary disease) AND (scalp shrapnel) AND (seizures History) AND (spina bifida) AND (spinal cord disease) AND (spinal stenosis) AND (stroke) AND (syrinx spinal cord))"}
{"candidate_id": "LLM00460", "doc_id": "NCT01501201_inc", "case_bucket": "or", "source_criterion": "Type 2 diabetes mellitus with HbA1c > 7.5 % Body mass index > 35 and < 50 kg/m2 Candidate for Gastric By-Pass Treatment with GLP1 (glucagon-like peptide) analogue or insulin", "candidate_expression": "((Body mass index > 35 and < 50 kg/m2) AND (GLP1 (glucagon-like peptide) analogue) AND (Gastric By-Pass Candidate) AND (HbA1c > 7.5 %) AND (Treatment) AND (Type 2 diabetes mellitus) AND (insulin))"}
{"candidate_id": "LLM00461", "doc_id": "NCT01850147_exc", "case_bucket": "or", "source_criterion": "Pre-existing hemoptysis of a severity > grade 3 by NCI CTCAE criteria within 4 weeks prior to study entry Uncontrolled hypertension CHF, angina or arrhythmias LVEF < 1 UNL Existing a second malignancy within 5 years Infected with HIV", "candidate_expression": "((CHF) AND (HIV) AND (LVEF < 1 UNL) AND (NCI CTCAE criteria within 4 weeks prior to study entry) AND (angina) AND (arrhythmias) AND (hemoptysis severity) AND (hypertension Uncontrolled) AND (second malignancy within 5 years))"}
{"candidate_id": "LLM00462", "doc_id": "NCT02579200_inc", "case_bucket": "or", "source_criterion": "Previous diagnoses of COPD and HF under optimized clinical treatment as judged by the accompanying physician Reduced left ventricular ejection fraction (<50%) Non-reversible airway obstruction (post-bronchodilator FEV1/FVC < 0.7 and FEV1 < 80 %) Respiratory muscle weakness (Pi,max < 70cmH2O) Persistent dyspnea on daily life (Baseline Dyspnea Index focal score <or= 8).", "candidate_expression": "((Dyspnea Index focal score Baseline <or= 8) AND (FEV1 post-bronchodilator < 80 %) AND (FEV1/FVC post-bronchodilator < 0.7) AND (Pi,max < 70cmH2O) AND (Respiratory muscle weakness) AND (airway obstruction Non-reversible) AND (clinical treatment optimized) AND (dyspnea on daily life Persistent) AND (left ventricular ejection fraction Reduced <50%) AND ((COPD) OR (HF)))"}
{"candidate_id": "LLM00463", "doc_id": "NCT03589105_inc", "case_bucket": "or", "source_criterion": "Age >/=18 years at screening Patients with relapsing forms of multiple sclerosis (RMS) with active disease defined by clinical or imaging features: (i) at least one clinical relapse over a 6-month period prior to screening; (ii) AND/OR at least one T1 gadolinium-enhancing lesion or new and/or enlarging T2 lesion as detected by brain Magnetic Resonance Imaging (MRI) performed over a 3 months period prior to screening with no change of Disease-Modifying Treatment(s) (DMT) compared to a previous MRI performed within 24 months before screening For women of childbearing potential: agreement to use an acceptable birth control method during the treatment period and for at least 12 months after the last dose of ocrelizumab Participants should be beneficiary of healthcare coverage under the social security system", "candidate_expression": "((Age >/=18 years at screening) AND (Disease-Modifying Treatment(s) (DMT) change of) AND (For women of childbearing potential: agreement to use an acceptable birth control method during the treatment period and for at least 12 months after the last dose of ocrelizumab) AND (beneficiary of healthcare coverage) AND (brain Magnetic Resonance Imaging (MRI)) AND (clinical relapse at least one over a 6-month period prior to screening) AND (multiple sclerosis (RMS) relapsing forms active disease) AND ((T1 gadolinium-enhancing lesion) OR (T2 lesion)) AND ((enlarging) OR (new)) AND ((clinical features) OR (imaging features)))"}
{"candidate_id": "LLM00464", "doc_id": "NCT00867958_exc", "case_bucket": "or", "source_criterion": "1. Patient has an allergy to nickel. 2. Patient has a diagnosis of bowel obstruction, bowel strangulation, peritonitis, bowel perforation, local or systemic infection, ischemic bowel, carcinomatosis or extensively spread inflammatory bowel disease. 3. Patient is participating in another clinical trial which may affect this study's outcomes. 4. Patient has been taking regular steroid medication. 5. Patient has contraindications to general anesthesia. 6. Patient has preexisting sphincter problems or evidence of extensive local disease in the pelvis.", "candidate_expression": "((Patient is participating in another clinical trial which may affect this study's outcomes.) AND (allergy to nickel) AND (bowel obstruction) AND (bowel perforation) AND (bowel strangulation) AND (carcinomatosis) AND (contraindications to general anesthesia) AND (general anesthesia) AND (inflammatory bowel disease extensively spread) AND (ischemic bowel) AND (local disease in the pelvis evidence of extensive) AND (local infection) AND (nickel) AND (peritonitis) AND (sphincter problems) AND (steroid medication regular) AND (systemic infection))"}
{"candidate_id": "LLM00465", "doc_id": "NCT01967420_exc", "case_bucket": "other", "source_criterion": "Active substance dependency History of severe head injury", "candidate_expression": "((severe head injury History) AND (substance dependency))"}
{"candidate_id": "LLM00466", "doc_id": "NCT02284737_exc", "case_bucket": "or", "source_criterion": "Pregnancy and breast feeding mother; Estimated life expectancy <12 months; Scheduled major surgery in the next 6 months; Inability to follow the protocol and comply with follow-up requirements or any other reason that the investigator feels would place the patient at increased risk; Previous enrolment in this study or treatment with an investigational drug or device under another study protocol in the past 30 days. WHO group II, III, IV, V PH Severe Renal dysfunction (Ccr<30 ml/min) Blood platelet count<100,000/L Expected life span<6-month Systematical inflammation Malignant cancer(s) Tricuspid valve stenosis, Supra-pulmonary valve stenosis Allergic to studied drugs or metal materials.", "candidate_expression": "((Allergic) AND (Blood platelet count <100,000/L) AND (Ccr <30 ml/min) AND (Estimated life expectancy <12 months) AND (Expected life span <6-month) AND (Inability to comply with follow-up requirements) AND (Inability to follow the protocol) AND (Malignant cancer) AND (PH) AND (Pregnancy) AND (Renal dysfunction Severe) AND (Supra-pulmonary valve stenosis) AND (Systematical inflammation) AND (Tricuspid valve stenosis) AND (WHO group II, III, IV, V) AND (breast feeding) AND (device Previous) AND (enrolment in this study Previous) AND (investigational drug) AND (major surgery Scheduled in the next 6 months) AND (studied drugs) AND (studied metal materials) AND (treatment with an investigational drug Previous))"}
{"candidate_id": "LLM00467", "doc_id": "NCT02295202_exc", "case_bucket": "other", "source_criterion": "Smokers Patients under chronic use of medications Neurological diseases Coronary artery disease Acute heart failure Chronic renal failure (GFR < 30 ml/min) Chronic obstructive pulmonary disease Mild OSA and patients with BMI over 40 kg/m2.", "candidate_expression": "((Acute heart failure) AND (BMI over 40 kg/m2) AND (Coronary artery disease) AND (GFR < 30 ml/min) AND (Mild OSA) AND (Neurological diseases) AND (Smokers) AND (medications chronic use) AND (obstructive pulmonary disease Chronic) AND (renal failure Chronic))"}
{"candidate_id": "LLM00468", "doc_id": "NCT02992938_exc", "case_bucket": "or", "source_criterion": "Patients ASA III y IV Chronic pain history Drug and alcohol abuse Chronic use of opioid and sedatives Neuropsychiatric illness NSAID and other analgesics used the 48 hours previous to the surgery CMI > 30", "candidate_expression": "((ASA III y IV) AND (CMI > 3) AND (Chronic pain) AND (Neuropsychiatric illness) AND ((NSAID) OR (analgesics other)) AND ((Drug abuse) OR (alcohol abuse)) AND ((opioid) OR (sedatives)))"}
{"candidate_id": "LLM00469", "doc_id": "NCT02760459_exc", "case_bucket": "or", "source_criterion": "History of active rheumatic diseases History of previous musculoskeletal injury of the same knee for excluding patients with secondary knee osteoarthritis History of previous surgery on the same knee History of adverse effects from medications to be used in this study Contraindication to spinal anesthesia History of psychiatric disorders or cognitive impairment Contraindication to corticosteroid agents Poorly controlled diabetes mellitus (HbA1C > 7.5) Poorly controlled hypertension History of ischemic heart disease or peripheral arterial disease or cerebrovascular disease Hepatic insufficiency (Child-Pugh score > 5) Renal insufficiency (Creatinine clearance < 30 mL/min) History of cataracts or glaucoma or ocular hypertension History of steroid or immunosuppressive drug use within 6 months of surgery", "candidate_expression": "((Child-Pugh score > 5) AND (Contraindication) AND (Creatinine clearance < 30 mL/min) AND (HbA1C > 7.5) AND (Hepatic insufficiency) AND (Renal insufficiency) AND (cataracts) AND (cerebrovascular disease) AND (cognitive impairment) AND (corticosteroid) AND (diabetes mellitus Poorly controlled) AND (glaucoma) AND (hypertension Poorly controlled) AND (immunosuppressive drug) AND (ischemic heart disease) AND (musculoskeletal injury knee) AND (ocular hypertension) AND (peripheral arterial disease) AND (psychiatric disorders) AND (rheumatic diseases active) AND (secondary knee osteoarthritis) AND (spinal anesthesia) AND (steroid) AND (surgery knee))"}
{"candidate_id": "LLM00470", "doc_id": "NCT01098383_inc", "case_bucket": "or", "source_criterion": "A formal diagnosis of Autism or Pervasive Developmental Disorder not otherwise specified (PDD-NOS), given by a child neurologist. Age: 10-18 years. A signed parental consent form.", "candidate_expression": "((A signed parental consent form) AND (Age 10-18 years) AND (Autism) AND (PDD-NOS) AND (Pervasive Developmental Disorder not otherwise specified))"}
{"candidate_id": "LLM00471", "doc_id": "NCT03461679_inc", "case_bucket": "other", "source_criterion": "Patients undergoing total knee arthroplasty under spinal anaesthesia 45y or older ASA 1-3 BMI 18-35", "candidate_expression": "((ASA 1-3) AND (BMI 18-35) AND (spinal anaesthesia) AND (total knee arthroplasty) AND (y 45 or older))"}
{"candidate_id": "LLM00472", "doc_id": "NCT02649114_exc", "case_bucket": "other", "source_criterion": "current suicidal risk current psychosis ongoing trauma (e.g. current involvement in an abusive relationship).", "candidate_expression": "((current) AND (involvement in an abusive relationship) AND (ongoing) AND (psychosis) AND (suicidal risk) AND (trauma))"}
{"candidate_id": "LLM00473", "doc_id": "NCT01177891_inc", "case_bucket": "or", "source_criterion": "Patients of familial cases of POF : Female subjects between 16 and 40 years or women older than 40 years with a cessation of ovarian function before the age of 40 years with increased levels of FSH Primary or secondary amenorrhea for more than three months with LH and FSH> 30mUI/ml No cases of fragile X syndrome in the family or blepharophimosis syndrome At least two cases in the family Origin Caucasian Patient signing the consent form for at least the blood sample Patient with Social Security Population Index related topics : The presence of cycles until the age of 40 years with proven fertility, at least one child Amenorrhea and FSH> 30mUI/ml according to the criteria of the index subject Men of the family of index case Population control : Women of Caucasian origin Women who had regular cycles until at least age 40 and at least one child Lack of land autoimmune (no history of thyroid disease or diabetes type 1) Woman signing the consent form for at least the blood sample", "candidate_expression": "((Amenorrhea) AND (Caucasian) AND (Caucasian origin) AND (FSH) AND (FSH > 30mUI/ml) AND (Female) AND (LH) AND (Patient signing the consent form for at least the blood sample) AND (The presence of cycles until the age of 40 years with proven fertility, at least one child) AND (Woman signing the consent form for at least the blood sample) AND (Women) AND (age before the age of 40 years) AND (age until at least age 40) AND (age until the age of 40 years) AND (amenorrhea) AND (autoimmune) AND (blepharophimosis syndrome At least two) AND (cessation of ovarian function) AND (diabetes type 1) AND (fragile X syndrome in the family) AND (levels of FSH increased Primary secondary) AND (presence of cycles) AND (regular cycles) AND (thyroid disease) AND (who had regular cycles until at least age 40) AND (women older than 40 years) AND (years between 16 and 40 years))"}
{"candidate_id": "LLM00474", "doc_id": "NCT03132259_inc", "case_bucket": "other", "source_criterion": "Age18-65 ASA 1-2 Elective TNTS resection of Pituitary Tumor No narcotic before surgery as premedication Able to Extubate", "candidate_expression": "((1-2) AND (18-65) AND (ASA) AND (Able to) AND (Age) AND (Elective) AND (Extubate) AND (No) AND (Pituitary Tumor) AND (TNTS resection) AND (before surgery) AND (narcotic) AND (surgery))"}
{"candidate_id": "LLM00475", "doc_id": "NCT00676273_inc", "case_bucket": "other", "source_criterion": "Are at least 18 years of age Demonstrate a positive cough stress test during complex multi-channel urodynamic testing Demonstrate impact of stress urinary incontinence on quality of life questionnaire Are able to comprehend and sign a written informed consent Understand and are willing to comply with the study requirements, including agreeing to be available for the follow-up evaluations Are psychologically stable and suitable for interventions determined by the investigator Are ambulatory and able to use a toilet independently", "candidate_expression": "((Understand the study requirements) AND (able to comprehend a written informed consent) AND (able to sign a written informed consent) AND (able to use a toilet independently) AND (age at least 18 years) AND (ambulatory) AND (complex multi-channel urodynamic testing) AND (cough stress test positive) AND (psychologically stable) AND (quality of life questionnaire) AND (stress urinary incontinence) AND (suitable for interventions) AND (willing to comply with the study requirements))"}
```
