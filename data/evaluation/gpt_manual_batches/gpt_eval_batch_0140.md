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
{"candidate_id": "LLM03476", "doc_id": "NCT02638935_inc", "case_bucket": "or", "source_criterion": "Female Age ≥18 years Patients with a lesion > 0.5 cm in largest diameter size, initially scored BI-RADS® 3, 4a, 4b or 4c in B-mode ultrasound Informed consent about histological examination (core cut biopsy (CCB), vacuum-assisted biopsy (VAB), fine needle aspiration (FNA) or surgery) has already been given in the course of clinical routine Signed informed consent of study participation", "candidate_expression": "((3, 4a, 4b or 4c) AND (> 0.5 cm) AND (Age) AND (B-mode ultrasound) AND (BI-RADS®) AND (Female) AND (Informed consent) AND (Signed informed consent of study participation) AND (histological examination) AND (largest diameter size) AND (lesion) AND (≥18 years) AND ((core cut biopsy (CCB)) OR (fine needle aspiration (FNA)) OR (surgery) OR (vacuum-assisted biopsy (VAB))))"}
{"candidate_id": "LLM03477", "doc_id": "NCT01890759_exc", "case_bucket": "or", "source_criterion": "Participation in the 4 weeks preceding inclusion or planned participation during the present trial period in another clinical trial investigating a vaccine, drug, medical device, or medical procedure. Receipt of any vaccine in the 4 weeks preceding each trial vaccination or planned receipt of any vaccine in the 4 weeks following each trial vaccination, except for: (i) influenza vaccination, which may be received at least 2 weeks before study vaccines. (ii) measles (M) or measles, mumps, rubella (MMR) routine vaccination, which can be administered concomitantly with the first dose of study vaccine as per routine immunization schedule (iii) for subjects enrolled at Indian sites: oral poliomyelitis vaccine (OPV) received during National Immunization Days (NIDs) and supplementary immunization activity days (SIADs) Previous vaccination against meningococcal disease with either the study vaccine or another meningococcal vaccine Receipt of immune globulins, blood or blood-derived products in the past 3 months Known or suspected congenital or acquired immunodeficiency; or receipt of immunosuppressive therapy, such as anti-cancer chemotherapy or radiation therapy, within the preceding 6 months; or long-term systemic corticosteroid therapy (prednisone or equivalent for more than 2 consecutive weeks within the past 3 months) History of meningococcal diseases, confirmed either clinically, serologically, or microbiologically At high risk, in the opinion of the Investigator, for meningococcal disease during the trial Known or suspected systemic hypersensitivity to any of the vaccine components, or history of a life-threatening reaction to the vaccine used in the trial or to a vaccine containing any of the same substances Known thrombocytopenia, contraindicating intramuscular vaccination Bleeding disorder, or receipt of anticoagulants in the 3 weeks preceding inclusion, contraindicating intramuscular vaccination In an emergency setting, or hospitalized involuntarily Chronic illness that, in the opinion of the investigator, is at a stage where it might interfere with trial conduct or completion For subjects enrolled at Indian sites: Moderate or severe acute illness/infection (according to investigator judgment) on the day of vaccination or febrile illness (temperature ≥ 38.0°C). For subjects enrolled at Russian sites: Acute disease of any severity on the day of vaccination or febrile illness (axillary temperature ≥ 37.0°C). A prospective subject should not be included in the study until the condition has resolved or the febrile event has subsided. Receipt of oral or injectable antibiotic therapy within 72 hours prior to the first blood draw Identified as a natural or adopted child of the Investigator or employee with direct involvement in the proposed study Personal history of Guillain-Barré Syndrome.", "candidate_expression": "((Acute disease on the day of vaccination) AND (At high risk, in the opinion of the Investigator, for meningococcal disease during the trial) AND (Chronic illness that, in the opinion of the investigator, is at a stage where it might interfere with trial conduct or completion) AND (Guillain-Barré Syndrome history) AND (Indian sites) AND (Participation in the 4 weeks preceding inclusion or planned participation during the present trial period in another clinical trial investigating a vaccine, drug, medical device, or medical procedure.) AND (Russian sites) AND (according to investigator judgment) AND (another meningococcal vaccine) AND (antibiotic therapy within 72 hours prior to the first blood draw) AND (axillary temperature ≥ 37.0°C) AND (contraindicating) AND (except for) AND (febrile illness) AND (febrile illness on the day of vaccination) AND (history) AND (hospitalized involuntarily) AND (influenza vaccination at least 2 weeks before study vaccines) AND (intramuscular vaccination) AND (life-threatening reaction) AND (meningococcal diseases) AND (microbiologically confirmed) AND (oral poliomyelitis vaccine (OPV) during National Immunization Days (NIDs) during supplementary immunization activity days (SIADs)) AND (planned participation 4 weeks preceding inclusion inclusion) AND (prednisone for more than 2 consecutive weeks within the past 3 months) AND (serologically confirmed) AND (study vaccine) AND (systemic hypersensitivity) AND (temperature ≥ 38.0°C) AND (thrombocytopenia) AND (vaccination against meningococcal disease) AND (vaccine) AND (vaccine components) AND (vaccine in the 4 weeks preceding each trial vaccination) AND (vaccine planned receipt) AND (vaccine used in the trial) AND ((injectable) OR (oral)) AND ((measles (M) vaccination) OR (measles, mumps, rubella (MMR) vaccination)) AND ((blood) OR (blood-derived products) OR (immune globulins)) AND ((acquired immunodeficiency) OR (congenital immunodeficiency)) AND ((immunosuppressive therapy within the preceding 6 months) OR (systemic corticosteroid therapy long-term)) AND ((anti-cancer chemotherapy) OR (radiation therapy)) AND ((Known) OR (suspected)) AND ((Bleeding disorder) OR (anticoagulants)) AND ((emergency setting) OR (hospitalized involuntarily)) AND ((Moderate) OR (severe)) AND ((acute illness) OR (acute infection)))"}
{"candidate_id": "LLM03478", "doc_id": "NCT00599924_inc", "case_bucket": "other", "source_criterion": "Advanced solid tumor malignancy (during expansion at the maximum tolerated dose, entry will be limited to patients wtih adenocarcinoma of the colon or rectum) Eastern Cooperative Oncology Group (ECOG) 0 or 1", "candidate_expression": "((0 or 1) AND (Advanced solid tumor malignancy) AND (Eastern Cooperative Oncology Group (ECOG)))"}
{"candidate_id": "LLM03479", "doc_id": "NCT01866800_inc", "case_bucket": "other", "source_criterion": "Subject is 65 years old who is able and willing to give an informed consent. Patients undergoing planned trans-femoral TAVI. Calculated eGFR below 60ml/min/1.73m2 (MDRD)", "candidate_expression": "((Calculated eGFR below 60ml/min/1.73m2) AND (able and willing to give an informed consent) AND (old 65 years) AND (trans-femoral TAVI undergoing planned))"}
{"candidate_id": "LLM03480", "doc_id": "NCT03073603_exc", "case_bucket": "or", "source_criterion": "Any MS relapse in the last five years, as determined at the screen visit by the PI Any new or definitely enlarging T2/FLAIR lesion or new gadolinium-enhancing lesion within the past three years (at least two scans separated by at least three years must be reviewed) on brain or spine MRI scan. Lesions must be 3mm or larger to be exclusionary. Significant (as defined by the PI) intolerance of presently-used DMT Use of inhaled or topical steroids are not an exclusion criteria. Use of oral steroids for no greater than 14 days given for a non-MS condition is not exclusionary. alemtuzumab, mitoxantrone, cyclophosphamide, methotrexate, cyclosporine, or rituximab Prior use of any experimental agent used as a DMT for MS in the last five years uncontrolled hypertension, uncontrolled diabetes, uncontrolled asthma, or uncontrolled depression Cancers other than basal cell skin cancers within the last 5 years Unable to give informed consent or follow the protocol Unable to undergo brain MRI Unwilling to be randomized per this protocol History of other chronic neurological illnesses that might mimic MS with chronic or intermittent symptoms (i.e. ALS, myasthenia gravis, chronic neuropathy, etc.)", "candidate_expression": "((3mm or larger) AND (Cancers) AND (DMT) AND (History of) AND (Lesions) AND (MS) AND (Significant) AND (Unable to undergo) AND (Unwilling to be randomized per this protocol) AND (alemtuzumab) AND (asthma) AND (at least two) AND (basal cell skin cancers) AND (brain MRI) AND (chronic neurological illnesses) AND (cyclophosphamide) AND (cyclosporine) AND (depression) AND (diabetes) AND (gadolinium) AND (gadolinium-enhancing) AND (hypertension) AND (in the last five years) AND (intolerance) AND (methotrexate) AND (mimic MS) AND (mitoxantrone) AND (no greater than 14 days) AND (non-MS condition) AND (not) AND (oral steroids) AND (other than) AND (presently-used) AND (relapse) AND (rituximab) AND (scans) AND (separated by at least three years) AND (uncontrolled) AND (within the last 5 years) AND (within the past three years) AND ((brain MRI scan) OR (spine MRI scan)) AND ((inhaled steroids) OR (topical steroids)) AND ((T2/FLAIR lesion) OR (lesion)) AND ((ALS) OR (chronic neuropathy) OR (myasthenia gravis)))"}
{"candidate_id": "LLM03481", "doc_id": "NCT03159507_exc", "case_bucket": "or", "source_criterion": "Allergy known to fish Pregnant women who breast-feed or test positive for pregnancy", "candidate_expression": "((Allergy) AND (fish) AND (positive) AND (women) AND ((Pregnant) OR (breast-feed) OR (test for pregnancy)))"}
{"candidate_id": "LLM03482", "doc_id": "NCT02557412_inc", "case_bucket": "or", "source_criterion": "Diagnosis of dyslipidemia: The existence of a previous clinical diagnostic of dyslipidemia associated with lipid-lowering therapy. It is also considered patients who have an altered analytical, using the following cutoffs: total cholesterol = 200 mg / dl, triglycerides = 180 mg / dl, HDL-cholesterol = 40 mg / dl or LDL-cholesterol = 150 mg / dl. Lipid-lowering treatment and diet, stable in the last month. A concentration of LDL-cholesterol above 100 mg / dl, in the month prior to inclusion. An apnea-hypopnea index between 5-30 h-1", "candidate_expression": "((LDL-cholesterol above 100 mg / dl in the month prior to inclusion) AND (Lipid-lowering diet stable) AND (Lipid-lowering treatment) AND (altered analytical) AND (apnea-hypopnea index between 5-30 h-1) AND (dyslipidemia) AND (lipid-lowering therapy) AND ((HDL-cholesterol = 40 mg / dl) OR (LDL-cholesterol = 150 mg / dl) OR (total cholesterol = 200 mg / dl) OR (triglycerides = 180 mg / dl)))"}
{"candidate_id": "LLM03483", "doc_id": "NCT02565277_exc", "case_bucket": "or", "source_criterion": "Have not received influenza vaccination in the past or cannot be vaccinated due to previous severe reaction to influenza vaccine, egg, latex, or thimerosol allergies, or refusal of vaccination Participant has received a community available influenza vaccine within <6 months History of Guillain-Barré syndrome Immunosuppressive disorders or medications (including oral prednisone >10 mg daily, recent chemotherapy treatment) Emergency cases as determined by the investigator or physician", "candidate_expression": "((>10 mg daily) AND (Guillain-Barré syndrome) AND (influenza vaccination) AND (influenza vaccine) AND (not) AND (within <6 months) AND ((chemotherapy) OR (oral prednisone)) AND ((Immunosuppressive disorders) OR (Immunosuppressive medications)))"}
{"candidate_id": "LLM03484", "doc_id": "NCT02256943_inc", "case_bucket": "or", "source_criterion": "Healthy Male >7 Metabolic Equivalents Written informed consent Chronic pain syndrome Drug abuse Alcohol abuse Suspicion of neurologic dysfunction at tested sites Ongoing treatment with antidepressants Ongoing treatment with analgesics Pretreatment with any CYP3A inducers or inhibitors Known allergy to tested drugs Elevated eye pressure Obstructive uropathy Heart disease Pulmonary disease Neurological disease Psychiatric illness", "candidate_expression": "((>7) AND (Alcohol abuse) AND (Chronic pain syndrome) AND (Drug abuse) AND (Elevated eye pressure) AND (Healthy) AND (Heart disease) AND (Male) AND (Metabolic Equivalents) AND (Neurological disease) AND (Obstructive uropathy) AND (Ongoing) AND (Pretreatment) AND (Psychiatric illness) AND (Pulmonary disease) AND (Suspicion) AND (Written informed consent) AND (allergy) AND (analgesics) AND (antidepressants) AND (neurologic dysfunction) AND (tested drugs) AND (tested sites) AND (treatment) AND ((CYP3A inducers) OR (CYP3A inhibitors)))"}
{"candidate_id": "LLM03485", "doc_id": "NCT03164304_inc", "case_bucket": "other", "source_criterion": "Pregnant women admitted to Women health hospital with a diagnosis of severe pre-eclampsia", "candidate_expression": "((Pregnant) AND (Women health hospital) AND (admitted to) AND (pre-eclampsia severe) AND (women))"}
{"candidate_id": "LLM03486", "doc_id": "NCT02509091_exc", "case_bucket": "or", "source_criterion": "Active bleeding without control; Receiving nasal or facial surgery recently; With severe cardio-pulmonary dysfunction, such as left heart failure, unstable arrhythmia, etc. With other respiratory diseases: such as active pulmonary tuberculosis, non-tuberculosis mycobacteria (NTM) pulmonary disease, pulmonary aspergillosis, etc. Be allergic to amikacin", "candidate_expression": "((NTM) AND (allergic) AND (amikacin) AND (bleeding Active) AND (cardio-pulmonary dysfunction severe) AND (respiratory diseases) AND ((non-tuberculosis mycobacteria pulmonary disease) OR (pulmonary aspergillosis) OR (pulmonary tuberculosis active)) AND ((facial surgery) OR (nasal surgery)) AND ((arrhythmia unstable) OR (left heart failure)))"}
{"candidate_id": "LLM03487", "doc_id": "NCT00122070_inc", "case_bucket": "other", "source_criterion": "Provide written informed consent before beginning any study related activities Be between age 18 and 55 years Be able to speak, read and write English and follow simple instructions for completing self-rated scales Meet DSM-IV criteria for BPD as assessed by the Structured Clinical Interview for DSM-IV Personality Disorders (SCID-II).", "candidate_expression": "((BPD) AND (Meet DSM-IV criteria) AND (Structured Clinical Interview for DSM-IV Personality Disorders (SCID-II)) AND (able to follow simple instructions) AND (able to speak, read and write English) AND (age) AND (any study related activities) AND (before beginning any study related activities) AND (between 18 and 55 years) AND (written informed consent))"}
{"candidate_id": "LLM03488", "doc_id": "NCT02350439_exc", "case_bucket": "or", "source_criterion": "1. Left main disease (angiographically> 50%) 2. Cardiogenic shock / hemodynamic instability 3. Previous CABG 4. Increased risk of bradycardia on investigator clinical judgment 5. Severe chronic obstructive pulmonary disease 6. Coronary vessels with tortuosity or extremely calcified 7. Severe left ventricular hypertrophy or severe valvular disease 8. STEMI or non-STEMI within the past five days 9. Previous myocardial infarction in the distribution of the target vessel for the FFR 10. Acute decompensated heart failure.", "candidate_expression": "((> 50%) AND (Acute decompensated heart failure) AND (CABG) AND (Cardiogenic shock) AND (Coronary vessel extremely calcified) AND (Coronary vessel tortuosity) AND (Increased risk) AND (Left main disease) AND (Previous) AND (STEMI) AND (Severe) AND (bradycardia) AND (chronic obstructive pulmonary disease) AND (hemodynamic instability) AND (in the distribution of the target vessel) AND (investigator clinical judgment) AND (left ventricular hypertrophy) AND (myocardial infarction) AND (non-STEMI) AND (severe) AND (valvular disease) AND (within the past five days))"}
{"candidate_id": "LLM03489", "doc_id": "NCT01483118_exc", "case_bucket": "or", "source_criterion": "Current pregnancy or lactation Liver disease or elevated liver enzymes Established diagnosis of diabetes mellitus Abnormal serum glucose levels either at fasting or after the 2-hr oral glucose tolerance test meeting criteria for the diagnosis of diabetes mellitus according to the American Diabetes Association. Insulin sensitizing treatment within 3 months prior to or during the eight week study period. Hormonal treatment involving estrogen or progesterone 3 months prior to or during the study period, with the exception of medroxyprogesterone acetate for withdrawal bleeding. Systemic or inhaled corticosteroids. Known hypersensitive reaction to cinnamon. Patients with seizure disorders, known cardiovascular disease, or cerebrovascular disease. Body mass index (BMI)range 20-50 (excluding all women with BMI under 20 or over 50).", "candidate_expression": "((2-hr oral glucose tolerance test) AND (Abnormal serum glucose levels meeting criteria for the diagnosis of diabetes mellitus according to the American Diabetes Association fasting the 2-hr oral glucose tolerance test) AND (Body mass index (BMI) range 20-50) AND (Insulin sensitizing treatment) AND (Liver disease) AND (Systemic corticosteroids Systemic) AND (cinnamon) AND (criteria for the diagnosis of diabetes mellitus according to the American Diabetes Association meeting) AND (diabetes mellitus) AND (elevated liver enzymes) AND (estrogen) AND (hypersensitive reaction to cinnamon) AND (inhaled corticosteroids inhaled) AND (liver enzymes elevated) AND (progesterone) AND (serum glucose levels Abnormal) AND (withdrawal bleeding) AND NOT (medroxyprogesterone acetate) AND ((after the 2-hr oral glucose tolerance test) OR (at fasting)) AND ((lactation) OR (pregnancy)) AND ((during the eight week study period) OR (within 3 months prior to eight week study period)) AND ((3 months prior to the study period) OR (during the study period)) AND ((cardiovascular disease) OR (cerebrovascular disease) OR (seizure disorders)))"}
{"candidate_id": "LLM03490", "doc_id": "NCT03088280_exc", "case_bucket": "other", "source_criterion": "PRA > 50% DSA > 1500 MFI Retransplantation Patients who are planning to receive mycophenolate instead of everolimus Patients who have planning for follow-up in another center", "candidate_expression": "((DSA > 1500 MFI) AND (PRA > 50%) AND (Retransplantation) AND (another center) AND (follow-up planning for) AND (mycophenolate planning to) AND NOT (everolimus))"}
{"candidate_id": "LLM03491", "doc_id": "NCT02882113_exc", "case_bucket": "or", "source_criterion": "Patients who have Tacrolimus trough level resulted as 2 ng/mg at the baseline. Patients who are on steroid therapy due to positive result of acute rejection test before the baseline. Patients who have received a transplant besides liver. Patients who are allergic to IP or macrolide compounds. Patients who are on cyclosporine, bosentan, or potassium sparing diuretic. Patients with genetic diseases such as galactose intolerance, Lapp lactase deficiency, or glucose-galactose malabsorption. Pregnant or lactating women. Patients not willing to adhere to study procedures/treatments.", "candidate_expression": "((Patients not willing to adhere to study procedures/treatments) AND (Pregnant or lactating women) AND (Tacrolimus 2 ng/mg) AND (acute rejection test positive) AND (allergic) AND (genetic diseases) AND (steroid) AND (transplant liver) AND ((IP) OR (macrolide)) AND ((bosentan) OR (cyclosporine) OR (potassium sparing diuretic)) AND ((Lapp lactase deficiency) OR (galactose intolerance) OR (glucose-galactose malabsorption)))"}
{"candidate_id": "LLM03492", "doc_id": "NCT03506477_exc", "case_bucket": "or", "source_criterion": "Form of diagnosed psoriasis other than chronic plaque psoriasis (i.e. guttate, erythrodermic, pustular) Diagnosis of other active, ongoing skin diseases or skin infections that may interfere with examination of psoriasis lesions Ongoing use of other psoriasis treatment including but not limited to topical or systemic corticosteroids, other topical medications (i.e. coal tar), oral or biologic medications for the treatment of psoriasis, and UV therapy. The following washout periods will be required: 2 weeks for topical therapy; 2 weeks for phototherapy; 12 weeks for biologic or targeted therapies; 4 weeks for other systemic therapies Use of oral estrogen therapy, excluding oral contraceptive pills Women who are pregnant, nursing, or of child-bearing potential who are unwilling to use appropriate method(s) of contraception. Patients unwilling to limit exposure to UV light Current significant medical problems that, in the discretion of the investigator, would put the patient at significant risk Patients with disorders of calcium metabolism and/or hypercalcemia Use of any investigational drug within 4 weeks prior to randomization, or 5 pharmacokinetic/pharmacodynamics half-lives, if known (whichever is longer) History of allergy to any component of the IP", "candidate_expression": "((UV therapy) AND (Use of any investigational drug within 4 weeks prior to randomization, or 5 pharmacokinetic/pharmacodynamics half-lives, if known (whichever is longer)) AND (Women who are pregnant, nursing, or of child-bearing potential who are unwilling to use appropriate method(s) of contraception.) AND (allergy) AND (any component of the IP) AND (biologic medications) AND (coal tar) AND (disorders of calcium metabolism) AND (hypercalcemia) AND (limit exposure to UV light unwilling) AND (oral estrogen therapy) AND (oral medications) AND (psoriasis) AND (skin diseases) AND (skin infections) AND (systemic corticosteroids) AND (topical corticosteroids) AND (topical medications) AND (treatment Ongoing) AND NOT (oral contraceptive pills) AND NOT (chronic plaque psoriasis guttate erythrodermic pustular))"}
{"candidate_id": "LLM03493", "doc_id": "NCT01912677_inc", "case_bucket": "or", "source_criterion": "Pregnant gestational age >= 28 weeks Systolic blood pressure >=160 mm Hg OR a diastolic blood pressure of >=110 mm Hg measured twice more than 15 minutes apart Able to swallow pills >= 18 years", "candidate_expression": "((Able to swallow pills) AND (Systolic blood pressure >=160 mm Hg) AND (diastolic blood pressure >=110 mm Hg) AND (gestational age >= 28 weeks) AND (years >= 18))"}
{"candidate_id": "LLM03494", "doc_id": "NCT02477280_inc", "case_bucket": "other", "source_criterion": "18 years old or older. ADHD is diagnosed according to Diagnostic and Statistical Manual of Mental Disorders, fifth edition (DSM-5 criteria). Substance Use Disorder is diagnosed according to DSM-5 criteria. Qb-score 1.3 or higher on at least one of the weighted summary parameters QbActivity, QbInattention or QbImpulsivity on the QbTest. Participants are given their written informed consent to participate in the study.", "candidate_expression": "((1.3 or higher) AND (18 years or older) AND (ADHD) AND (DSM-5) AND (Participants are given their written informed consent to participate in the study) AND (Qb-score) AND (Substance Use Disorder) AND (old))"}
{"candidate_id": "LLM03495", "doc_id": "NCT03430284_inc", "case_bucket": "other", "source_criterion": "35-75 years old; diagnosed as type 2 diabetes according to the criteria of the World Health Organization in 1999.", "candidate_expression": "((old 35-75 years old) AND (type 2 diabetes criteria of the World Health Organization in 1999))"}
{"candidate_id": "LLM03496", "doc_id": "NCT01313676_inc", "case_bucket": "or", "source_criterion": "Type of subject: outpatient. Informed consent: Subjects must give their signed and dated written informed consent to participate. Gender: Male or female. Female subjects must be post-menopausal or using a highly effective method for avoidance of pregnancy. The decision to include or exclude women of childbearing potential may be made at the discretion of the investigator in accordance with local practice in relation to adequate contraception. Age: >=40 and <=80 years of age at Screening (Visit 1). Tobacco use: Subjects with a current or prior history of >=10 pack-years of cigarette smoking at screening (Visit 1). Previous smokers are defined as those who have stopped smoking for at least 6 months prior to Visit 1. Airflow Obstruction: Subjects with a measured post-albuterol/salbutamol forced expiratory volume in 1 second (FEV1)/(forced vital capacity)FVC ratio of <=0.70 at Screening (Visit 1). Subjects with a measured post-albuterol/salbutamol FEV1 >=50 and <=70% of predicted normal values calculated using NHANES III reference equations [Hankinson, 1999; Hankinson, 2010] at Screening (Visit 1). Post-bronchodilator spirometry will be performed approximately 15 minutes after the subject has self-administered 4 inhalations (i.e., total 400mcg) of albuterol/salbutamol via a metered dose inhaler (MDI )with a valved-holding chamber. The FEV1/FVC ratio and FEV1 percent predicted values will be calculated. Symptoms of COPD: Subjects must score 2 or higher on the modified Medical Research Council Dyspnea scale (Visit 1) Cardiovascular disease: For patients >= 40 years of age: any one of the following: Established (i.e. by clinical signs or imaging studies) coronary artery disease (CAD) Established (i.e. by clinical signs or imaging studies) peripheral vascular disease (PVD) Previous stroke Previous MI Diabetes mellitus with target organ disease OR For patients >=60 years of age: any 2 of the following: Being treated for hypercholesterolemia Being treated for hypertension Being treated for diabetes mellitus Being treated for peripheral vascular disease", "candidate_expression": "((FEV1 post-albuterol/salbutamol >=50 and <=70% of predicted normal values at Screening) AND (Female subjects must be post-menopausal or using a highly effective method for avoidance of pregnancy. The decision to include or exclude women of childbearing potential may be made at the discretion of the investigator in accordance with local practice in relation to adequate contraception.) AND (Informed consent: Subjects must give their signed and dated written informed consent to participate.) AND (Previous smokers) AND (Symptoms of COPD) AND (age >= 40 years) AND (age >=60 years) AND (albuterol) AND (bronchodilator) AND (cigarette smoking history >=10 pack-years at screening) AND (diabetes mellitus) AND (forced expiratory volume in 1 second (FEV1)/(forced vital capacity)FVC ratio post-albuterol/salbutamol <=0.70 at Screening) AND (hypercholesterolemia) AND (hypertension) AND (inhalations self-administered 4 400mcg) AND (metered dose inhaler (MDI ) with a valved-holding chamber) AND (modified Medical Research Council Dyspnea scale score 2 or higher) AND (outpatient) AND (peripheral vascular disease) AND (salbutamol) AND (spirometry Post-bronchodilator approximately 15 minutes after) AND (stopped smoking for at least 6 months prior to Visit 1) AND (target organ disease) AND ((current) OR (prior)) AND ((Male) OR (female)) AND ((Age >=40 and <=80 years at Screening) OR (age >=40 and <=80 years at Screening)) AND ((Diabetes mellitus) OR (MI Previous) OR (coronary artery disease (CAD) Established) OR (peripheral vascular disease (PVD) Established) OR (stroke Previous)) AND ((clinical signs) OR (imaging studies)) AND ((treated for diabetes mellitus) OR (treated for hypercholesterolemia) OR (treated for hypertension) OR (treated for peripheral vascular disease)))"}
{"candidate_id": "LLM03497", "doc_id": "NCT00235170_inc", "case_bucket": "or", "source_criterion": "1. Patients with stable (Canadian Cardiovascular Society 1, 2, 3 or 4) or unstable (Braunwald class IB, IC, IIB, IIC, IIIB, IIIC) angina pectoris and ischemia, or patients with atypical chest pain or even those who are asymptomatic provided they have documented myocardial ischaemia (e.g. treadmill exercise test, radionuclide scintigraphy, stress echocardiography, Holter tape); 2. Patients who are eligible for coronary revascularization (angioplasty or CABG); 3. At least 2 lesions (located in different vessels and in different territories) potentially amenable to stent implantation; 4. de novo native vessels; 5. Multivessel disease with at least one significant stenosis in LAD and with treatment of the lesion in another major epicardial coronary artery. A two-vessel disease or a three-vessel disease may be viewed as a combination of a side branch and a main epicardial vessel provided they supply different territories; left anterior descending, left circumflex and right coronary artery); 6. Total occluded vessels. One total occluded major epicardial vessel or side branch can be included and targeted as long as one other major vessel has a significant stenosis amenable for SA, provided the age of occlusion is less than one month e.g. recent instability, infarction with ECG changes in the area subtended by the occluded vessel. Patients with total occluded vessels of unknown duration or existing longer than one month and a reference over 1.50 mm should not be included, not even as a third or fourth vessel to be dilated; 7. Significant stenosis has been defined as a stenosis of more than 50% in luminal diameter (in at least one view, on visual interpretation or preferably by QCA); 8. Left ventricular ejection fraction should be at least 30%.", "candidate_expression": "((Braunwald class) AND (Canadian Cardiovascular Society 1, 2, 3 or 4 unstable) AND (Left ventricular ejection fraction at least 30%) AND (Multivessel disease at least one) AND (Significant stenosis) AND (Total occluded vessels) AND (angina pectoris stable) AND (asymptomatic documented) AND (atypical chest pain) AND (coronary revascularization eligible for) AND (ischemia) AND (lesions At least 2 potentially amenable located in different vessels located in different territories) AND (myocardial ischaemia) AND (native vessels de novo) AND (reference over 1.50 mm) AND (significant stenosis in LAD) AND (stenosis more than 50% in luminal diameter) AND (stent implantation) AND (total occluded vessels unknown duration longer than one month) AND (treatment of the lesion in another major epicardial coronary artery) AND ((Holter tape) OR (radionuclide scintigraphy) OR (stress echocardiography) OR (treadmill exercise test)) AND ((CABG) OR (angioplasty)) AND ((total occluded major epicardial vessel) OR (total occluded side branch)) AND ((IB) OR (IC) OR (IIB) OR (IIC) OR (IIIB) OR (IIIC)))"}
{"candidate_id": "LLM03498", "doc_id": "NCT02141061_exc", "case_bucket": "or", "source_criterion": "1. Subject is a post-menopausal woman, defined as either; six (6) months or more (immediately prior to screening visit) without a menstrual period, or prior hysterectomy and/or oophorectomy 2. Subject is pregnant or lactating or is attempting or expecting to become pregnant during the study 3. Women with abnormally high liver enzymes or liver disease. (ALT or AST exceeding 2.0 x ULN AND total bilirubin exceeding 1.5 x ULN at screening and confirmed on repeat). 4. Received an investigational drug in the 30 days prior to the screening for this study 5. Women with a history of PCOS 6. Concurrent use of any testosterone, progestin, androgen, estrogen, anabolic steroids, DHEA or hormonal products for at least 2 weeks prior to screening and during the study. 7. Use of oral contraceptives in the preceding 2 weeks. Use of Depo-Provera® in the preceding 10 months. 8. Has an IUD in place 9. Women currently using narcotics 10. Women currently taking spironolactone 11. Infectious disease screen is positive for HIV or Hepatitis A, B or C. 12. Clinically significant abnormal findings on screening examination or any condition which in the opinion of the investigator would interfere with the participant's ability to comply with the study instructions or endanger the participant if she took part in the study", "candidate_expression": "((ALT) AND (AST) AND (DHEA) AND (Depo-Provera® in the preceding 10 months) AND (HIV) AND (Hepatitis A) AND (Hepatitis B) AND (Hepatitis C) AND (IUD) AND (PCOS history) AND (Women) AND (anabolic steroids) AND (androgen) AND (estrogen) AND (hormonal products) AND (hysterectomy prior) AND (investigational drug in the 30 days prior to the screening) AND (is attempting or expecting to become pregnant during the study) AND (lactating) AND (liver disease) AND (liver enzymes high) AND (narcotics) AND (oophorectomy) AND (oral contraceptives in the preceding 2 weeks) AND (post-menopausal) AND (pregnant) AND (progestin) AND (spironolactone) AND (testosterone) AND (total bilirubin exceeding 1.5 x ULN at screening) AND (woman six (6) months or more) AND NOT (menstrual period))"}
{"candidate_id": "LLM03499", "doc_id": "NCT02618057_inc", "case_bucket": "or", "source_criterion": "Evidence of Mycoplasma pneumoniae infection Lobar pneumonia or pneumoniae with pleural effusion", "candidate_expression": "((Mycoplasma pneumoniae infection) AND (pleural effusion) AND ((Lobar pneumonia) OR (pneumoniae)))"}
{"candidate_id": "LLM03500", "doc_id": "NCT02456532_inc", "case_bucket": "other", "source_criterion": "DSM-5 diagnosis of insomnia", "candidate_expression": "(insomnia DSM-5)"}
```
