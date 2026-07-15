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
{"candidate_id": "LLM05351", "doc_id": "NCT03138577_inc", "case_bucket": "other", "source_criterion": "Undergoing right upper extremity surgery with supraclavicular block as the primary anesthetic Age greater than or equal to 18 years of age American Society of Anesthesiologists (ASA) physical status 1 to 3 Able to give informed consent", "candidate_expression": "((Able to give informed consent) AND (Age greater than or equal to 18 years) AND (American Society of Anesthesiologists (ASA) physical status 1 to 3) AND (right upper extremity surgery Undergoing) AND (supraclavicular block primary anesthetic))"}
{"candidate_id": "LLM05352", "doc_id": "NCT03352869_inc", "case_bucket": "or", "source_criterion": "Overweight and obese PCOS patients with newly diagnosed IGR; PCOS diagnosis based on 2003 Rotterdam criteria Overweight / obesity diagnostic criteria according to WHO-WPR Impaired glucose regulation diagnostic criteria according to 1998 WHO diagnostic criteria.", "candidate_expression": "((IGR newly diagnosed) AND (Impaired glucose regulation 1998 WHO diagnostic criteria) AND (Overweight) AND (PCOS) AND (PCOS 2003 Rotterdam criteria) AND (obese) AND (obesity))"}
{"candidate_id": "LLM05353", "doc_id": "NCT02203019_inc", "case_bucket": "or", "source_criterion": "Men and women 18-89 years old with the diagnosis of sepsis (as specified below) within the previous 24 hours who require mechanical ventilation, and provide informed consent either personally or by an authorized representative.", "candidate_expression": "((18-89 years) AND (mechanical ventilation) AND (old) AND (provide informed consent either personally or by an authorized representative) AND (sepsis) AND (within the previous 24 hours) AND ((Men) OR (women)))"}
{"candidate_id": "LLM05354", "doc_id": "NCT03463564_inc", "case_bucket": "or", "source_criterion": "T1DM for at least 12 months persistent HbA1c levels = 7.5% (58 mmol/mol) despite optimized education therapy, recurrent severe hypoglycemic episodes or high glucose variability willingness to wear the insulin pump", "candidate_expression": "((58 mmol/mol) AND (= 7.5%) AND (HbA1c levels) AND (T1DM) AND (for at least 12 months) AND (high glucose variability) AND (hypoglycemic episodes) AND (insulin pump) AND (optimized education therapy) AND (persistent) AND (recurrent) AND (severe) AND (wear the insulin pump) AND (willingness))"}
{"candidate_id": "LLM05355", "doc_id": "NCT02944604_inc", "case_bucket": "or", "source_criterion": "Severe or uncontrolled infection. Sensitive to the product or other genetically engineered biological products from Escherichia coli strains. Mental or nervous system disorders. Severe heart, lung and central nervous system disorders. Pregnant or lactating women. TBIL(total bilirubin ), ALT(alanine aminotransferase),AST(glutamic-oxalacetic transaminase) > 2.5×ULN(upper limit of normal); if it were caused by liver metastases, TBIL, ALT,AST >5×ULN. Cr(creatinine) >1.5×ULN.", "candidate_expression": "((> 2.5×ULN) AND (>1.5×ULN) AND (>5×ULN) AND (Cr) AND (Escherichia coli strains) AND (Sensitive) AND (Severe) AND (alanine aminotransferase) AND (creatinine) AND (genetically engineered biological products) AND (glutamic-oxalacetic transaminase) AND (infection) AND (liver metastases) AND (other) AND (the product) AND (total bilirubin) AND (women) AND ((Severe) OR (uncontrolled)) AND ((Mental disorders) OR (nervous system disorders)) AND ((entral nervous system disorders) OR (heart disorders) OR (lung disorders)) AND ((Pregnant) OR (lactating)) AND ((ALT) OR (AST) OR (TBIL)))"}
{"candidate_id": "LLM05356", "doc_id": "NCT02277041_exc", "case_bucket": "or", "source_criterion": "women undergoing caesarean section at less than 37 weeks of gestation. Hypertension with pregnancy. Cardiac and coronary diseases with pregnancy", "candidate_expression": "((Hypertension) AND (caesarean section undergoing) AND (gestation less than 37 weeks) AND (pregnancy) AND (women) AND ((Cardiac diseases) OR (coronary diseases)))"}
{"candidate_id": "LLM05357", "doc_id": "NCT03249272_exc", "case_bucket": "or", "source_criterion": "Decompensated heart failure or hemodynamic instability Prior coronary revascularization (PCI or CABG) or myocardial infarction (as evidenced by previously elevated CPK-MB or troponin levels) Accelerating angina or unstable angina Inability to physically tolerate MRI or implanted objects that are MRI incompatible Inability to provide written informed consent obtained at time of study enrollment. Severe claustrophobia Advanced heart block or sinus node dysfunction Hypersensitivity or allergic reaction to regadenoson or adenosine Hypotension Active bronchospasm or history of hospitalization due to bronchospasm History of seizures Recent cerebrovascular accident Use of dipyridamole within the last 5 days Contraindication to aminophylline Severe renal insufficiency with estimated glomerular filtration rate <30 ml/min/ 1.73 m2 Pregnant or nursing", "candidate_expression": "((Accelerating angina) AND (CABG) AND (CPK-MB levels) AND (Contraindication) AND (Hypersensitivity) AND (Hypotension) AND (Inability to physically tolerate) AND (Inability to provide written informed consent obtained at time of study enrollment.) AND (MRI) AND (PCI) AND (Pregnant) AND (adenosine) AND (allergic) AND (aminophylline) AND (bronchospasm) AND (bronchospasm Active) AND (cerebrovascular accident Recent) AND (claustrophobia Severe) AND (coronary revascularization Prior) AND (dipyridamole within the last 5 days) AND (estimated glomerular filtration rate <30 ml/min/ 1.73 m2) AND (heart block) AND (heart failure Decompensated) AND (hemodynamic instability) AND (hospitalization history) AND (implanted objects MRI incompatible) AND (myocardial infarction Prior) AND (nursing) AND (regadenoson) AND (renal insufficiency Severe) AND (seizures History) AND (sinus node dysfunction) AND (troponin levels) AND (unstable angina))"}
{"candidate_id": "LLM05358", "doc_id": "NCT00483106_exc", "case_bucket": "other", "source_criterion": "Psychosis Tourette syndrome Intelligence quotient (IQ) < 70 Pervasive developmental disorder (PDD)", "candidate_expression": "((< 70) AND (IQ) AND (Intelligence quotient) AND (PDD) AND (Pervasive developmental disorder) AND (Psychosis) AND (Tourette syndrome))"}
{"candidate_id": "LLM05359", "doc_id": "NCT03089086_exc", "case_bucket": "other", "source_criterion": "Previous anaphylaxis following any component of Bexsero vaccine Previous receipt of meningococcal B vaccine (Bexsero) Known pregnancy", "candidate_expression": "((Bexsero) AND (Bexsero vaccine) AND (anaphylaxis Previous) AND (meningococcal B vaccine Previous) AND (pregnancy))"}
{"candidate_id": "LLM05360", "doc_id": "NCT02560766_inc", "case_bucket": "or", "source_criterion": "Male and female adolescent patients, aged 13 to 17 years, diagnosed with RLS based on the IRLSSG consensus criteria (Allen RP 2014) (Appendix 2). Total RLS severity score of 15 or greater on the IRLS rating scale at Visit 1 (screening) and at Visit 2 (baseline) (Appendix 8). RLS symptoms for at least 4 of 7 consecutive evenings/nights during the screening period. Body weight greater than 33.4 kg and a healthy weight using age-based body mass index (BMI) range 5th-85th percentile at screening and baseline. Appendix 3 contains BMI-for-age charts that can be consulted. Estimated creatinine clearance of at least 60 mL/min (using the Cockcroft-Gault equation) at screening only. Signed patient and parent Institutional Review Board (IRB)-approved informed consent/assent form (as applicable) before any study-related procedures are performed.", "candidate_expression": "((13 to 17 years) AND (15 or greater) AND (5th-85th percentile) AND (BMI) AND (Body weight) AND (Estimated creatinine clearance) AND (IRLSSG consensus criteria) AND (Male) AND (RLS) AND (RLS symptoms) AND (Signed patient and parent Institutional Review Board (IRB)-approved informed consent/assent form (as applicable) before any study-related procedures are performed) AND (Total RLS severity score) AND (adolescent) AND (aged) AND (at least 4 of 7 consecutive evenings/nights) AND (at least 60 mL/min) AND (body mass index) AND (female) AND (greater than 33.4 kg))"}
{"candidate_id": "LLM05361", "doc_id": "NCT03034733_exc", "case_bucket": "or", "source_criterion": "severe coronary artery disease, heart failure, kidney failure insulin-dependent DM (diabetes mellitus), poorly controlled type II DM gastric/duodenal ulcer allergy/contra-indication for any drug used in the study corticosteroid use during last 3 months preoperative use of opioid drugs (excl. codeine, tramadol) neuropathy/sensory impairment of lower limbs lack of co-operation, e.g. inability to use a PCA (patient controlled analgesia)-device", "candidate_expression": "((PCA -device) AND (corticosteroid during last 3 months) AND (diabetes mellitus) AND (drug used in the study) AND (inability to use) AND (insulin-dependent DM) AND (lack of co-operation) AND (opioid drugs preoperative) AND (type II DM poorly controlled) AND ((duodenal ulcer) OR (gastric ulcer)) AND ((allergy) OR (contra-indication)) AND ((coronary artery disease) OR (heart failure) OR (kidney failure)) AND ((codeine) OR (tramadol)) AND ((neuropathy) OR (sensory impairment)))"}
{"candidate_id": "LLM05362", "doc_id": "NCT02780427_exc", "case_bucket": "or", "source_criterion": "Known allergy or hypersensitive reaction to dexmedetomidine Organ dysfunction, and significant developmental delays or behavior problems Cardiac arrhythmia Known. acyanotic congenital heart disease or children after cardiac interventional procedures for follow-up examination.", "candidate_expression": "((Cardiac arrhythmia) AND (children after cardiac interventional procedures cardiac interventional procedures) AND (dexmedetomidine) AND (follow-up examination) AND ((allergy) OR (hypersensitive)) AND ((acyanotic congenital heart disease) OR (cardiac interventional procedures for follow-up examination)) AND ((Organ dysfunction) OR (behavior problems) OR (developmental delays significant)))"}
{"candidate_id": "LLM05363", "doc_id": "NCT03131050_exc", "case_bucket": "or", "source_criterion": "Currently enrolled in, or discontinued within the last 30 days from, a clinical trial involving an off-label use of an investigational drug. Current Axis I primary psychiatric diagnosis other than major depressive disorder. Organic mental disease, including mental retardation. History of clinically significant disease, including any cardiovascular, hepatic, renal, respiratory, hematologic, endocrinologic, or neurologic disease, or clinically significant laboratory abnormality that is not stabilized or is anticipated to require treatment during the study. Subjects receiving an investigational agent (including different formulation and generic agents of investigational drug) in the previous 3 months prior to screening. Women in pregnancy or lactation, or female of child bearing potential without appropriate birth control measures. Use of antipsychotics or mood stabilizers within 5 days prior to screening. Has received depot antipsychotic medication within one cycle prior to screening. Known allergy or lack of response to mirtazapine. Has received ECT or MECT within 3 months prior to screening. History of anticholinergic drug allergy or complications (allergic reaction, skin rash, urticaria and other allergic reactions which caused by drugs). Smokers. Significant risk of suicidal and/or self-harm behaviors", "candidate_expression": "((Currently enrolled in, or discontinued within the last 30 days from, a clinical trial involving an off-label use of an investigational drug.) AND (Organic mental disease) AND (Smokers) AND (Subjects receiving an investigational agent (including different formulation and generic agents of investigational drug) in the previous 3 months prior to screening.) AND (Women in pregnancy or lactation, or female of child bearing potential without appropriate birth control measures.) AND (allergy) AND (anticholinergic drug) AND (depot antipsychotic medication within one cycle prior to screening) AND (drugs) AND (mental retardation) AND (mirtazapine) AND (neurologic disease) AND (psychiatric diagnosis Axis I primary) AND NOT (major depressive disorder) AND ((cardiovascular disease) OR (disease clinically significant) OR (endocrinologic disease) OR (hematologic disease) OR (hepatic disease) OR (laboratory abnormality clinically significant) OR (renal disease) OR (respiratory disease)) AND ((treatment anticipated to require during the study) OR NOT (stabilized)) AND ((antipsychotics) OR (mood stabilizers)) AND ((allergy) OR (lack of response)) AND ((ECT) OR (MECT)) AND ((allergic reaction) OR (allergic reactions other) OR (skin rash) OR (urticaria)) AND ((self-harm behaviors) OR (suicidal behaviors)))"}
{"candidate_id": "LLM05364", "doc_id": "NCT03260790_exc", "case_bucket": "other", "source_criterion": "Research exemption requested History of PCV-13 vaccination History of cochlear implant Cerebrospinal Fluid (CSF) leak Congestive Heart Failure (CHF) Diabetes Mellitus (DM) Chronic Kidney Disease (CKD) Human Immunodeficiency Virus (HIV) Common Variable Immune Deficiency (CVID) Patients who have received the PPSV23 vaccine in the last 5 years Women who are pregnant will also be excluded from the study by performing 2 point of care urine pregnancy tests ( prior to vaccinations)", "candidate_expression": "((2) AND (Cerebrospinal Fluid (CSF) leak) AND (Chronic Kidney Disease (CKD)) AND (Common Variable Immune Deficiency (CVID)) AND (Congestive Heart Failure (CHF)) AND (Diabetes Mellitus (DM)) AND (History) AND (Human Immunodeficiency Virus (HIV)) AND (PCV-13 vaccination) AND (PPSV23 vaccine) AND (Research exemption requested) AND (Women) AND (cochlear implant) AND (in the last 5 years) AND (point of care urine pregnancy tests) AND (pregnant) AND (prior to vaccinations) AND (vaccinations))"}
{"candidate_id": "LLM05365", "doc_id": "NCT02068365_exc", "case_bucket": "or", "source_criterion": "Evidence of decompensated liver disease (Childs B-C), hepato-cellular carcinoma, pre-existing severe depression or other psychiatric disease, significant cardiac disease, significant renal disease, seizure disorders or severe retinopathy. received telbivudine as the antiviral therapy or have received more than one NA in the past. received interferon or peginterferon treatment in the past. received antiviral therapy for any systemic anti-viral, anti-neoplastic or immuno-modulatory treatment (including supraphysiologic doses of steroids and radiation) within the past 6 months. Positive test at screening for anti-HIV, anti-HCV. Patients who are expected to need systemic antiviral therapy other than that provided by the study at any time during their participation in the study are also excluded. Exception: patients who have had a limited (<=7 days) course of acyclovir for herpetic lesions more than 1 month prior to the first administration of test drug are not excluded. Serum total bilirubin > 3 times the upper limit of normal at screening. History or other evidence of bleeding from esophageal varices or other conditions consistent with decompensated liver disease. History or other evidence of a medical condition associated with chronic liver disease other than HBV (e.g., hemochromatosis, autoimmune hepatitis, metabolic liver diseases including Wilson's and alpha1-antitrypsin deficiency, alcoholic liver disease, toxin exposures, thalassemia). Women with ongoing pregnancy or who are breast feeding. Neutrophil count <1500 cells/mm3 or platelet count <90,000 cells/mm3 at screening. Hemoglobin < 11.5 g/dL for females and < 12.5 g/dL for men at screening. Serum creatinine level >120 umol/ml for men and >105 umol/ml for women at screening. History of severe psychiatric disease, especially depression. Severe psychiatric disease is defined as major depression or psychosis, a period of treatment with an antidepressant medication or major tranquilizer at therapeutic doses for depression or psychosis for at least 3 months, a suicidal attempt, hospitalization for psychiatric disease, or a period of disability due to a psychiatric disease. History of immunologically mediated disease (e.g., inflammatory bowel disease, idiopathic thrombocytopenic purpura, lupus erythematosus, autoimmune hemolytic anemia, scleroderma, severe psoriasis, rheumatoid arthritis). History or other evidence of chronic pulmonary disease associated with functional limitation. Severe cardiac disease (e.g., NYHA Functional Class III or IV, myocardial infarction within 6 months, ventricular tachyarrhythmias requiring ongoing treatment, unstable angina or other significant cardiovascular diseases). History of a severe seizure disorder or current anticonvulsant use. Evidence of an active or suspected cancer or a history of malignancy where the risk of recurrence is >=20% within 2 years. Patients with a lesion suspicious of hepatic malignancy on a screening imaging study will only be eligible if the likelihood of carcinoma is <=10% following an appropriate evaluation. History of having received any systemic anti-neoplastic (including radiation) or immunomodulatory treatment (including systemic corticosteroids) <=6 months prior to the first dose of study drug or the expectation that such treatment will be needed at any time during the study. Major organ transplantation. Thyroid disease with thyroid function poorly controlled on prescribed medications. Patients with abnormal thyroid stimulating hormone or T4 concentrations, with elevation of antibodies to thyroid peroxidase and any clinical manifestations of thyroid disease are excluded. History or other evidence of severe retinopathy (e.g. CMV retinitis, macula degeneration) or clinically relevant ophthalmological disorder due to diabetes mellitus or hypertension Inability or unwillingness to provide informed consent or abide by the requirements of the study. History or other evidence of severe illness or any other conditions which would make the patient, in the opinion of the investigator, unsuitable for the study. Patients with a value of alpha-fetoprotein >100 ng/mL are excluded, unless stability (less than 10% increase) has been documented over at least the previous 3 months. Evidence of drug and/or alcohol abuse (20g/day for women & 30g/day for men). Patients included in another trial or having been given investigational drugs within 12 weeks prior to screening Any known history of hypersensitivity to interferon.", "candidate_expression": "((Childs B-C) AND (Hemoglobin at screening) AND (History or other evidence of severe illness or any other conditions which would make the patient, in the opinion of the investigator, unsuitable for the study.) AND (Inability or unwillingness to provide informed consent or abide by the requirements of the study.) AND (Major organ transplantation) AND (Patients included in another trial or having been given investigational drugs within 12 weeks prior to screening) AND (Serum creatinine level at screening) AND (Serum total bilirubin > 3 times the upper limit of normal at screening) AND (Thyroid disease) AND (Women) AND (alpha-fetoprotein >100 ng/mL) AND (cardiac disease Severe) AND (chronic liver disease) AND (chronic pulmonary disease) AND (corticosteroids systemic) AND (depression) AND (esophageal varices) AND (functional limitation) AND (hepatic malignancy suspicious) AND (herpetic lesions) AND (hypersensitivity) AND (immunologically mediated disease) AND (increase less than 10%) AND (interferon) AND (lesion) AND (likelihood of carcinoma <=10%) AND (liver disease decompensated) AND (medical condition) AND (men) AND (men >120 umol/ml) AND (psychiatric disease) AND (psychiatric disease severe) AND (radiation) AND (retinopathy severe) AND (risk of recurrence >=20% within 2 years) AND (screening imaging study) AND (systemic anti-viral) AND (systemic antiviral therapy expected to need at any time during their participation in the study) AND (telbivudine) AND (thyroid function poorly controlled on prescribed medications) AND (treatment expectation will be needed at any time during the study) AND (treatment in the past) AND (treatment ongoing) AND (women) AND (women >105 umol/ml) AND NOT (stability at least the previous 3 months) AND NOT (acyclovir limited course more than 1 month prior to the first administration of test drug not excluded <=7 days) AND NOT (HBV) AND ((depression severe) OR (psychiatric disease other)) AND ((Severe) OR (psychiatric disease)) AND ((antidepressant medication) OR (major tranquilizer)) AND ((disability) OR (hospitalization) OR (major depression) OR (psychosis) OR (psychosis for at least 3 months) OR (suicidal attempt) OR (treatment)) AND ((cardiac disease significant) OR (hepato-cellular carcinoma) OR (renal disease significant) OR (retinopathy) OR (seizure disorders) OR (severe)) AND ((autoimmune hemolytic anemia) OR (idiopathic thrombocytopenic purpura) OR (inflammatory bowel disease) OR (lupus erythematosus) OR (psoriasis severe) OR (rheumatoid arthritis) OR (scleroderma)) AND ((NYHA Functional Class III or IV) OR (cardiovascular diseases other significant) OR (myocardial infarction within 6 months) OR (unstable angina) OR (ventricular tachyarrhythmias)) AND ((anticonvulsant current) OR (seizure disorder severe)) AND ((active) OR (suspected)) AND ((cancer) OR (malignancy)) AND ((anti-neoplastic treatment) OR (immunomodulatory treatment)) AND ((T4 concentrations) OR (thyroid stimulating hormone)) AND ((antibodies to thyroid peroxidase elevation) OR (clinical manifestations of thyroid disease)) AND ((CMV retinitis) OR (macula degeneration)) AND ((clinically relevant) OR (ophthalmological disorder)) AND ((diabetes mellitus) OR (hypertension)) AND ((alcohol abuse) OR (drug abuse)) AND ((20g/day) OR (30g/day)) AND ((NA in the past) OR (antiviral therapy) OR (more than one)) AND ((interferon) OR (peginterferon)) AND ((anti-neoplastic treatment) OR (antiviral therapy) OR (immuno-modulatory treatment)) AND ((radiation supraphysiologic doses) OR (steroids supraphysiologic doses)) AND ((test for anti-HCV) OR (test for anti-HIV)) AND ((bleeding) OR (conditions consistent with decompensated liver disease other)) AND ((autoimmune hepatitis) OR (hemochromatosis) OR (metabolic liver diseases)) AND ((Wilson's) OR (alcoholic liver disease) OR (alpha1-antitrypsin deficiency) OR (thalassemia) OR (toxin exposures)) AND ((breast feeding) OR (pregnancy ongoing)) AND ((Neutrophil count <1500 cells/mm3) OR (platelet count <90,000 cells/mm3)) AND ((females < 11.5 g/dL) OR (men < 12.5 g/dL)))"}
{"candidate_id": "LLM05366", "doc_id": "NCT02946918_exc", "case_bucket": "or", "source_criterion": "AJCC Stage III or greater Undifferentiated, Anaplastic or Medullary Thyroid Cancer Planned postoperative TSH goal other than 0.1-0.5 mU/L History of gastrointestinal malabsorption or gastric bypass surgery Pregnancy Use of medications that alter the absorption or metabolism of levothyroxine Prior use of levothyroxine", "candidate_expression": "((0.1-0.5 mU/L) AND (AJCC) AND (Anaplastic Thyroid Cancer) AND (Medullary Thyroid Cancer) AND (Pregnancy) AND (Prior) AND (Stage III or greater) AND (TSH) AND (Undifferentiated Thyroid Cancer) AND (absorption of levothyroxine) AND (alter) AND (gastric bypass surgery) AND (gastrointestinal malabsorption) AND (levothyroxine) AND (medications) AND (metabolism of levothyroxine) AND (other than) AND (postoperative))"}
{"candidate_id": "LLM05367", "doc_id": "NCT01912677_exc", "case_bucket": "or", "source_criterion": "Indication for emergent cesarean or known fetal anomaly Anti-hypertensive therapy received in the past 12 hours History of eclampsia or other adverse CNS complication (e.g., stroke or PRES) in this pregnancy Actively wheezing at time of enrollment or history of asthma complications Known coronary artery disease or type I DM with microvascular complications or signs of heart failure or clinical dissection of the aorta", "candidate_expression": "((Anti-hypertensive therapy) AND (CNS complication) AND (Indication) AND (PRES) AND (asthma complications) AND (at time of enrollment) AND (coronary artery disease) AND (dissection of the aorta) AND (eclampsia) AND (emergent cesarean) AND (enrollment) AND (fetal anomaly) AND (heart failure) AND (in this pregnancy) AND (microvascular complications) AND (past 12 hours) AND (stroke) AND (type I DM) AND (wheezing))"}
{"candidate_id": "LLM05368", "doc_id": "NCT00391690_inc", "case_bucket": "or", "source_criterion": "Patients with histologically confirmed diagnosis of prostate cancer who have not yet developed bone metastases Prostate cancer patients with a rise in PSA under hormone therapy. PSA criteria: Patients who have undergone prostatectomy: any rise in PSA or Patients without prostatectomy: 2 consecutive rises in PSA levels relative to a previous reference value, separated by one month. The first measurement must occur one month after the reference value and must be above the reference value. The second confirmatory measurement taken one month after the first measurement must be greater than the first measurement. Previous chemotherapy or radiotherapy must have been performed ≥ 8 weeks prior to study entry. Eastern Cooperative Oncology Group (ECOG) score of 0, 1 or 2 (patients that spend less than 50% of time in bed during the day) Adequate liver function - serum total bilirubin concentration less than 1.5 x upper limit of normal value Age: ≥ 18 years Patient has given written informed consent prior to any study-specific procedures. Patients with psychiatric or addictive disorders which prevent them from giving their informed consent must not enter the study.", "candidate_expression": "((0, 1 or 2) AND (2) AND (Adequate) AND (Age) AND (Eastern Cooperative Oncology Group (ECOG) score) AND (PSA) AND (PSA levels) AND (Previous) AND (Prostate cancer) AND (above the reference value) AND (bone metastases) AND (confirmed) AND (consecutive) AND (first) AND (giving informed consent) AND (greater than the first measurement) AND (histologically) AND (hormone therapy) AND (less than 1.5 x upper limit of normal value) AND (less than 50%) AND (liver function) AND (measurement) AND (one month after the first measurement) AND (one month after the reference value) AND (prevent) AND (prostate cancer) AND (prostatectomy) AND (rise) AND (rises) AND (second) AND (separated by one month) AND (serum total bilirubin concentration) AND (spend time in bed during the day) AND (without) AND (≥ 18 years) AND (≥ 8 weeks prior to study entry) AND ((chemotherapy) OR (radiotherapy)) AND ((addictive disorders) OR (psychiatric disorders)))"}
{"candidate_id": "LLM05369", "doc_id": "NCT02796378_inc", "case_bucket": "other", "source_criterion": "Elevated blood-cholesterol", "candidate_expression": "(blood-cholesterol Elevated)"}
{"candidate_id": "LLM05370", "doc_id": "NCT01912651_inc", "case_bucket": "or", "source_criterion": "all adult patients with a nasal or facial skin/soft tissue defect requiring reconstruction limited to or including a full-thickness skin graft", "candidate_expression": "((facial skin/soft tissue defect) AND (full-thickness skin graft) AND (nasal skin/soft tissue defect) AND (reconstruction requiring))"}
{"candidate_id": "LLM05371", "doc_id": "NCT02816164_exc", "case_bucket": "other", "source_criterion": "Contraindication to Filgrastim", "candidate_expression": "((Contraindication) AND (Filgrastim))"}
{"candidate_id": "LLM05372", "doc_id": "NCT03033745_inc", "case_bucket": "or", "source_criterion": "Male or female on stable dose of IgPro20 (Hizentra) therapy. Women of childbearing potential must be using and agree to continue using medically approved contraception (which must be discussed with the study doctor) and must have a negative pregnancy test at screening. Subjects with PID, eg, with a diagnosis of common variable immunodeficiency or X-linked agammaglobulinemia, as defined by the Pan American Group for Immune Deficiency and the European Society of Immune Deficiencies. With infusion parameters as specified below: Experience with pump-assisted infusions of IgPro20 at the tolerated flow rate of 25 mL/h per injection site for at least 1 month prior to Day 1. Total weekly IgPro20 dose of = 50 mL (= 10 g). Experience with pump-assisted infusions of IgPro20 at tolerated volumes of 25 mL/injection site for at least 1 month prior to Day 1. Experience with frequent (2-7 times per week) infusions of IgPro20 at the tolerated flow rate of approximately 0.5 mL/min (equivalent of 25-30 mL/h) per injection site for at least 1 month prior to Day 1. The dose (volume) per injection site should not exceed 25 mL.", "candidate_expression": "((2-7 times per week) AND (25-30 mL/h) AND (= 10 g) AND (= 50 mL) AND (Day 1) AND (European Society of Immune Deficiencies) AND (Hizentra) AND (IgPro20) AND (Male) AND (PID) AND (Pan American Group for Immune Deficiency) AND (Women of childbearing potential must be using and agree to continue using medically approved contraception (which must be discussed with the study doctor) and must have a negative pregnancy test at screening) AND (X-linked agammaglobulinemia) AND (common variable immunodeficiency) AND (exceed 25 mL.) AND (female) AND (flow rate of 25 mL/h per injection site) AND (for at least 1 month prior to Day 1) AND (frequent) AND (not) AND (per injection site flow rate of approximately 0.5 mL/min) AND (pump-assisted infusions) AND (stable dose) AND (tolerated) AND (volumes of 25 mL/injection site) AND (weekly))"}
{"candidate_id": "LLM05373", "doc_id": "NCT02164734_exc", "case_bucket": "or", "source_criterion": "Weight < 800 g; Airway anomalies; Pulmonary air leaks; Craniofacial or cardiothoracic malformations", "candidate_expression": "((Airway anomalies) AND (Pulmonary air leaks) AND (Weight < 800 g) AND ((Craniofacial malformations) OR (cardiothoracic malformations)))"}
{"candidate_id": "LLM05374", "doc_id": "NCT00962364_inc", "case_bucket": "or", "source_criterion": "acute myocardial infarction or ischemic cardiomyopathy with or without previous myocardial infarction or dilated cardiomyopathy due to valvular heart disease, hypertensive heart disease, history of myocarditis (no active myocardial infection present)", "candidate_expression": "((active) AND (acute myocardial infarction) AND (history) AND (ischemic cardiomyopathy) AND (myocardial infarction) AND (myocardial infection) AND (no) AND (previous) AND (valvular heart disease) AND ((dilated cardiomyopathy) OR (hypertensive heart disease) OR (myocarditis)))"}
{"candidate_id": "LLM05375", "doc_id": "NCT02607748_inc", "case_bucket": "or", "source_criterion": "Acute Coronary Syndrome group: 40 patients with type 1 myocardial infarction within 21 days prior to the imaging visit and invasive coronary angiography with angiographic evidence of at least a 50% stenosis in one or more coronary arteries. Only patients undergoing PCI will be included in the study. Stable Ischemic Heart Disease group: 40 patients who have undergone invasive coronary angiography within 21 days prior to the imaging visit, with history of typical angina prior to the angiogram, but no prior myocardial infarction or coronary revascularization. have no prior CAD associated event (no prior myocardial infarction, acute coronary syndrome, coronary angiogram, or PCI), have CAC between 10 to <1000, and match to patients in the ACS group by gender, age by decile, and CAC category (using CAC categories of 10 to <100, 100 to <400, 400 to <1000).", "candidate_expression": "((Acute Coronary Syndrome) AND (CAC between 10 to <1000) AND NOT (CAD) AND ((PCI) OR (acute coronary syndrome) OR (coronary angiogram) OR (myocardial infarction)))"}
```
