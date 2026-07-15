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
{"candidate_id": "LLM05276", "doc_id": "NCT02312089_inc", "case_bucket": "scope", "source_criterion": "Women subjected to ICSI through controlled ovarian hyperstimulation (COH) with pituitary downregulation by GnRH antagonist.", "candidate_expression": "((COH) AND (GnRH antagonist) AND (ICSI) AND (Women) AND (ovarian hyperstimulation) AND (pituitary downregulation))"}
{"candidate_id": "LLM05277", "doc_id": "NCT00989261_exc", "case_bucket": "or", "source_criterion": "1. Patients over the age of 85 years except at the discretion of the Investigator and with agreement of the Sponsor. 2. Diagnosis of acute promyelocytic leukemia 3. Diagnosis of chronic myelogenous leukemia (CML) in blast crisis 4. AML in relapse or refractory after 3 or more previous lines of chemotherapy (and/or HSCT) treatment 5. AML or antecedent MDS secondary to prior chemotherapy 6. Persistent clinically significant non-hematological toxicity that is Grade >1 by NCI CTCAE v4 from prior chemotherapy 7. Patients who have had HSCT and are within 100 days of transplant and/or are still taking immunosuppressive drugs and/or have clinically significant graft-versus-host disease requiring treatment and/or have >Grade 1 persistent non hematological toxicity related to the transplant 8. Clinically active central nervous system (CNS) leukemia. Patients with CNS leukemia, which is controlled, but who are still receiving IT therapy at study entry may be considered eligible and continue receive IT therapy at the discretion of the Investigator and with agreement of the Sponsor. 9. Patients who have previously received AC220 10. Disseminated intravascular coagulation (DIC) (diagnosis by laboratory or clinical assessment) 11. Major surgery within 4 weeks prior to enrollment in the study 12. Radiation therapy within 4 weeks prior to, or concurrent with study 13. Use of concomitant drugs that prolong QT/QTc interval and/or are CYP3A4 inhibitors are prohibited with the exception of antibiotics, antifungals, and other antimicrobials that are used as standard of care to prevent or treat infections and other such drugs that are considered absolutely essential for the care of the patient. 14. Uncontrolled or significant cardiovascular disease 15. Women who are pregnant, lactating, or unwilling to use contraception if of childbearing potential 16. Men who are unwilling to use contraception if their partners are of childbearing potential 17. Active, uncontrolled infection 18. Human immunodeficiency virus positivity 19. Active hepatitis B or C or other active liver disease 20. History of cancer, except Stage 1 cervix or nonmelanotic skin cancer, with the possible exception of patients in complete remission", "candidate_expression": "((AC220) AND (AML) AND (Disseminated intravascular coagulation (DIC)) AND (HSCT have had within 100 days of transplant transplant) AND (Human immunodeficiency virus) AND (Human immunodeficiency virus positivity) AND (Major surgery within 4 weeks prior to enrollment enrollment) AND (Men) AND (NCI CTCAE v4 Grade >1) AND (Patients over the age of 85 years except at the discretion of the Investigator and with agreement of the Sponsor.) AND (Radiation therapy within 4 weeks prior to study concurrent with study study) AND (acute promyelocytic leukemia) AND (age over the age of 85 years) AND (at the discretion of the Investigator) AND (blast crisis) AND (cancer History) AND (cardiovascular disease) AND (central nervous system (CNS) leukemia) AND (chemotherapy prior) AND (chronic myelogenous leukemia (CML)) AND (clinically significant) AND (contraception unwilling) AND (infection Active uncontrolled) AND (lines of chemotherapy 3 or more previous) AND (liver disease active) AND (prolong QT/QTc interval that prolong QT/QTc interval) AND (their partners are of childbearing potential) AND (toxicity clinically significant non-hematological Grade >1 by NCI CTCAE v4) AND (transplant) AND (treatment requiring persistent) AND NOT (skin cancer Stage 1 cervix nonmelanotic) AND ((AML) OR (MDS antecedent)) AND ((graft-versus-host disease clinically significant) OR (immunosuppressive drugs still) OR (toxicity >Grade 1 persistent non hematological) OR (transplant)) AND ((CYP3A4 inhibitors) OR (drugs that prolong QT/QTc interval)) AND ((antibiotics) OR (antifungals) OR (antimicrobials)) AND ((Uncontrolled) OR (significant)) AND ((childbearing potential) OR (lactating) OR (pregnant)) AND ((in relapse) OR (refractory)) AND ((hepatitis B) OR (hepatitis C)))"}
{"candidate_id": "LLM05278", "doc_id": "NCT02432404_inc", "case_bucket": "or", "source_criterion": "=18-40 year old women BV+ by Amsel criteria and Nugent score OR history of BV in the prior 6 months Willing to use the NuvaRing as directed Not intending or wishing to become pregnant over the course of the study Capable of providing written informed consent", "candidate_expression": "((18-40 year) AND (Amsel criteria) AND (BV) AND (BV+) AND (Capable of providing written informed consent) AND (Not intending or wishing to become pregnant over the course of the study) AND (Nugent score) AND (NuvaRing) AND (Willing to use) AND (in the prior 6 months) AND (old) AND (women) AND (written informed consent))"}
{"candidate_id": "LLM05279", "doc_id": "NCT03088904_exc", "case_bucket": "other", "source_criterion": "NA", "candidate_expression": "(EMPTY)"}
{"candidate_id": "LLM05280", "doc_id": "NCT02704234_inc", "case_bucket": "other", "source_criterion": "women previously diagnosed with generalized vulvodynia women previously diagnosed with localized vestibulodynia,", "candidate_expression": "((generalized vulvodynia) AND (localized vestibulodynia) AND (women))"}
{"candidate_id": "LLM05281", "doc_id": "NCT02992028_inc", "case_bucket": "other", "source_criterion": "Rotator cuff tear patients undergoing arthroscopic rotator cuff tear", "candidate_expression": "((Rotator cuff tear) AND (arthroscopic rotator cuff tear))"}
{"candidate_id": "LLM05282", "doc_id": "NCT03047538_inc", "case_bucket": "or", "source_criterion": "a very high cardiovascular risk and LDL-cholesterol> 1.8 mmol / l a high cardiovascular risk and LDL-cholesterol> 2.5 mmol / l Patient with a high or very high cardiovascular risk treated by lipidlowering therapy with statin", "candidate_expression": "((LDL-cholesterol > 1.8 mmol / l) AND (LDL-cholesterol > 2.5 mmol / l high) AND (cardiovascular risk high) AND (cardiovascular risk very high) AND (lipidlowering therapy) AND (stati))"}
{"candidate_id": "LLM05283", "doc_id": "NCT02912182_inc", "case_bucket": "other", "source_criterion": "definite unilateral vestibulopathy no pathological HINTS (examination criteria in acute vestibular syndrome) capable of making their own decisions", "candidate_expression": "((acute vestibular syndrome) AND (capable of making their own decisions) AND (vestibulopathy unilateral) AND NOT (HINTS pathological))"}
{"candidate_id": "LLM05284", "doc_id": "NCT02205931_exc", "case_bucket": "or", "source_criterion": "Age <1m or > 24 months of age No secure diagnosis of epilepsy < 4 seizures/week on average in baseline period Trial of < 2 AEDs Continues on corticosteroids in previous 3 months prior to randomisation Metabolic disease contraindicating use of the ketogenic diet e.g. pyruvate carboxylase deficiency, MCAD from previous medical investigation and screening at baseline. Progressive neurological disease Severe gastroesophageal reflux Previous treatment with the ketogenic diet Concurrent participation in another clinical trial of an investigational medicinal product. Patients who are prescribed AEDs not listed in the trial IMPs", "candidate_expression": "((AEDs < 2) AND (Age <1m or > 24 months of age) AND (Concurrent participation in another clinical trial of an investigational medicinal product) AND (Metabolic disease) AND (contraindicating) AND (corticosteroids previous 3 months prior to randomisation) AND (gastroesophageal reflux Severe) AND (ketogenic diet) AND (ketogenic diet Previous) AND (neurological disease Progressive) AND (seizures < 4 /week) AND NOT (epilepsy) AND ((MCAD) OR (pyruvate carboxylase deficiency,)))"}
{"candidate_id": "LLM05285", "doc_id": "NCT02462590_exc", "case_bucket": "or", "source_criterion": "Invasively mechanically ventilated >72 hours at the time of screening; Patients at potential increased risk of iatrogenic probiotic infection (see Section 2.6 for detailed explanation) including specific immunocompromised populations (HIV <200 CD4 cells/µL, those receiving chronic immunosuppressive medications (e.g., azathioprine, cyclosporine, cyclophosphamide, tacrolimus, methotrexate, mycofenolate, Anti-IL2), previous transplantation (including stem cell) at any time, malignancy requiring chemotherapy in the last 3 months, neutropenia [absolute neutrophil count < 500]). However, patients receiving corticosteroids previously or presently or projected to receive corticosteroids are not excluded; Patients at risk for endovascular infection (previously documented rheumatic heart disease, congenital valve disease, surgically repaired congenital heart disease, unrepaired cyanotic congenital heart disease, any intracardiac repair with prosthetic material [mechanical or bio-prosthetic cardiac valves], previous or current endocarditis, permanent endovascular devices (e.g., endovascular grafts [e.g., aortic aneurysm repair, stents involving large arteries such as aorta, femorals and carotids], inferior vena cava filters, dialysis vascular grafts), tunnelled (not short-term) hemodialysis catheters, pacemakers or defibrillators. Patients with temporary central venous catheters, central venous dialysis catheters or peripherally inserted central catheters (PICCs) are not excluded and patients with coronary artery stents, coronary artery bypass grafts (CABG) or neurovascular coils are not excluded; patients with mitral valve prolapse or bicuspid aortic valve are not excluded providing they have no other exclusion criteria; Patients with a primary diagnosis of severe acute pancreatitis, without reference to a Ranson score [Ranson 1974]). However, patients with mild or moderate pancreatitis are not excluded; Patients with percutaneous gastric or jejunal feeding tubes already in situ as per Health Canada guidance; Strict contraindication or inability to receive enteral medications; Intent to withdraw advanced life support as per the ICU physician; Previous enrolment in this or current enrolment in a potentially confounding tria", "candidate_expression": "((Anti-IL2) AND (CD4 <200 cells/µL) AND (HIV) AND (PICCs) AND (Previous enrolment in this or current enrolment in a potentially confounding tria) AND (absolute neutrophil count < 500]) AND (acute pancreatitis severe) AND (aortic aneurysm repair) AND (azathioprine) AND (bicuspid aortic valve) AND (bio-prosthetic cardiac valves]) AND (central venous catheters) AND (central venous dialysis catheters) AND (chemotherapy last 3 months) AND (congenital heart disease surgically repaired) AND (congenital valve disease) AND (contraindication) AND (coronary artery bypass grafts) AND (coronary artery stents) AND (cyanotic congenital heart disease unrepaired) AND (cyclophosphamide) AND (cyclosporine) AND (dialysis vascular grafts) AND (endocarditis) AND (endovascular devices permanent) AND (endovascular grafts) AND (enteral medications) AND (gastric feeding tubes) AND (hemodialysis catheters) AND (immunocompromised) AND (immunosuppressive medications chronic) AND (inferior vena cava filters) AND (intracardiac repair) AND (jejunal feeding tubes) AND (mechanical cardiac valves) AND (mechanically ventilated >72 hours) AND (methotrexate) AND (mitral valve prolapse) AND (mycofenolate) AND (neurovascular coils) AND (neutropenia) AND (pacemakers) AND (peripherally inserted central catheters) AND (prosthetic material) AND (rheumatic heart disease) AND (risk for endovascular infection) AND (risk of iatrogenic probiotic infection) AND (stents large arteries) AND (tacrolimus) AND (transplantation) AND NOT (Ranson score) AND NOT (pancreatitis mild moderate))"}
{"candidate_id": "LLM05286", "doc_id": "NCT03264911_exc", "case_bucket": "or", "source_criterion": "Hypersensitivity to B-lactams concomitant disease which must be treated with antibiotics chronic disease-Immunocompromised Antibiotics within 72 h history of ARF,scarlet fever,impetigo,acute glomerulonephritis Family history of ARF Complicated pharyngitis", "candidate_expression": "((ARF Family history) AND (Antibiotics within 72 h) AND (B-lactams) AND (Hypersensitivity) AND (Immunocompromised) AND (antibiotics) AND (disease concomitant) AND (pharyngitis Complicated) AND (treated) AND ((ARF) OR (acute glomerulonephritis) OR (impetigo) OR (scarlet fever)))"}
{"candidate_id": "LLM05287", "doc_id": "NCT03369379_inc", "case_bucket": "or", "source_criterion": "Female patients older than 18 years. Patients who agree to participate in the study. Those that meet the ACR 1990 and 2010 criteria for Fibromyalgia. No previous use of vitamin D. Patients diagnosed with primary or secondary fibromyalgia.", "candidate_expression": "((ACR 1990) AND (ACR 2010) AND (Female) AND (Fibromyalgia) AND (No) AND (Patients who agree to participate in the study.) AND (fibromyalgia) AND (older than 18 years) AND (previous) AND (primary) AND (secondary) AND (vitamin D) AND (years))"}
{"candidate_id": "LLM05288", "doc_id": "NCT02951520_exc", "case_bucket": "other", "source_criterion": "BMI > 30 kg.m-2, ASA physical state >II Allergy to the used local anesthetics Infection at the injection site age <18y", "candidate_expression": "((ASA physical state >II) AND (Allergy) AND (BMI > 30 kg.m-2) AND (Infection injection site) AND (age <18y) AND (local anesthetics))"}
{"candidate_id": "LLM05289", "doc_id": "NCT03518034_inc", "case_bucket": "or", "source_criterion": "Men between 45 and 80 years age Participants with low serum testosterone concentrations (< 300 ng/dL) who exhibit at least one sign or symptom of hypogonadism and have evidence of cardiovascular (CV) disease or are at an increased risk for CV disease.", "candidate_expression": "((< 300 ng/dL) AND (CV disease) AND (Men) AND (age) AND (at least one) AND (between 45 and 80 years) AND (cardiovascular (CV) disease) AND (evidence of) AND (hypogonadism) AND (increased risk) AND (low) AND (serum testosterone concentrations) AND (sign) AND (symptom))"}
{"candidate_id": "LLM05290", "doc_id": "NCT03475589_inc", "case_bucket": "or", "source_criterion": "Age of 18 and over, male or female; Patients with histologically confirmed advanced (stage IV) gastric cancer, NSCLC, breast cancer or ovarian cancer, who choose monotherapy of oral vascular targeting drug (apatinib) due to intolerability or inappropriateness of other therapies; Presence of measurable lesions (=10mm on spiral CT scan) subject to RECIST 1.1; Blood pressured controlled at 150/100 mHg following drug administration; An ECOG PS score of between 0 and 1; A life expectancy of at least 3 months; Subjects who volunteer to participate in this study and have signed the Informed Consent Form (ICF), with good compliance with treatment and follow-up.", "candidate_expression": "((150/100 mHg) AND (18 and over) AND (=10mm) AND (Age) AND (Blood pressured) AND (ECOG PS) AND (NSCLC) AND (RECIST 1.1) AND (Subjects who volunteer to participate in this study and have signed the Informed Consent Form (ICF), with good compliance with treatment and follow-up.) AND (advanced) AND (apatinib) AND (at least 3 months) AND (between 0 and 1) AND (breast cancer) AND (controlled) AND (female) AND (gastric cancer) AND (histologically) AND (histologically confirmed) AND (life expectancy) AND (male) AND (measurable lesions) AND (monotherapy) AND (oral vascular targeting drug) AND (ovarian cancer) AND (spiral CT scan) AND (stage IV))"}
{"candidate_id": "LLM05291", "doc_id": "NCT01424020_inc", "case_bucket": "other", "source_criterion": "French Native language 18 years old or older Signed consent Covered by the French social care system", "candidate_expression": "((Covered by the French social care system) AND (French Native language) AND (Signed consent) AND (old 18 years or older))"}
{"candidate_id": "LLM05292", "doc_id": "NCT00962364_inc", "case_bucket": "or", "source_criterion": "acute myocardial infarction or ischemic cardiomyopathy with or without previous myocardial infarction or dilated cardiomyopathy due to valvular heart disease, hypertensive heart disease, history of myocarditis (no active myocardial infection present)", "candidate_expression": "((acute myocardial infarction) AND (ischemic cardiomyopathy) AND (myocardial infarction previous) AND (valvular heart disease) AND NOT (myocardial infection active) AND ((dilated cardiomyopathy) OR (hypertensive heart disease) OR (myocarditis history)))"}
{"candidate_id": "LLM05293", "doc_id": "NCT02609425_inc", "case_bucket": "other", "source_criterion": "All patients with esophageal cancer who are deemed candidates for minimally invasive robot assisted Ivor Lewis esophagogastrectomy. Patients who provide written informed consent for the study.", "candidate_expression": "((Ivor Lewis) AND (Patients who provide written informed consent for the study.) AND (candidates) AND (esophageal cancer) AND (esophagogastrectomy) AND (minimally invasive) AND (robot assisted))"}
{"candidate_id": "LLM05294", "doc_id": "NCT03171987_exc", "case_bucket": "or", "source_criterion": "Known or suspected serious spinal pathology and spinal implants Lumbar spinal surgery within the preceding six months Serious comorbidities preventing prescription of paracetamol Alternative treatment for low back pain in previous two weeks Chronic neurological lesion Chronic musculoskeletal lesion Active cancer Pregnancy Use of pain medication (except paracetamol) within 3 days Treatment site has active skin lesion or inflammation Known allergy to skin patch", "candidate_expression": "((Chronic musculoskeletal lesion) AND (Chronic neurological lesion) AND (Lumbar spinal surgery within the preceding six months) AND (Pregnancy) AND (allergy) AND (cancer Active) AND (comorbidities Serious) AND (inflammation) AND (low back pain in previous two weeks) AND (pain medication within 3 days) AND (paracetamol) AND (preventing) AND (skin lesion) AND (skin patch) AND (spinal implants) AND (spinal pathology serious Known suspected) AND (treatment Alternative) AND NOT (paracetamol))"}
{"candidate_id": "LLM05295", "doc_id": "NCT02918851_exc", "case_bucket": "or", "source_criterion": "Any significant acute or chronic medical illness or problem, including, but not limited to, diabetes, hypertension, cardiac disease, asthma, chronic obstructive lung disease Current or recent (last 60 days) tobacco or nicotine use History of sickle cell trait or disease or any other acquired or hereditary hematological abnormality History of fainting or other significant adverse reaction during phlebotomy or donation of blood Known prolonged QTc (or evidence of such at screening) on electrocardiogram defined as >470 ms Known or suspected illicit drug or alcohol abuse Known or suspected HIV, Hepatitis B, or Hepatitis C infection History of thrombophilia or anticoagulant therapy Pregnancy Obesity defined as BMI>30 Recent history of blood donation: a) Single whole blood unit donation within the past 8 weeks; b) Double RBC donation by apheresis within the past 16 weeks; or c) Plasma donation by apheresis within the past 4 weeks Inadequate RBC mass based on TBV <4500 ml (above) or screening Hb <14 g/dL", "candidate_expression": "((<14 g/dL) AND (<4500 ml) AND (>30) AND (>470 ms) AND (BMI) AND (HIV infection) AND (Hb) AND (Hepatitis B infection) AND (Hepatitis C infection) AND (Inadequate) AND (Obesity) AND (Pregnancy) AND (QTc) AND (RBC mass) AND (TBV) AND (acquired hematological abnormality) AND (acute) AND (adverse reaction) AND (alcohol abuse) AND (anticoagulant therapy) AND (asthma) AND (blood donation) AND (cardiac disease) AND (chronic) AND (chronic obstructive lung disease) AND (diabetes) AND (donation of blood) AND (electrocardiogram) AND (fainting) AND (hereditary hematological abnormality) AND (hypertension) AND (illicit drug abuse) AND (last 60 days) AND (medical illness) AND (nicotine use) AND (phlebotomy) AND (sickle cell disease) AND (sickle cell trait) AND (thrombophilia) AND (tobacco use))"}
{"candidate_id": "LLM05296", "doc_id": "NCT01116973_inc", "case_bucket": "or", "source_criterion": "Subject's ability to lay in a supine position with their hands at their sides during CVP measurements A consent form signed by the patient or patient's representative Subjects that are age 18-90 Subjects that have an indwelling CICC and are transitioning to a PICC for long-term IV access CICC placed in the internal jugular vein or subclavian vein position", "candidate_expression": "((18-90) AND (A consent form signed by the patient or patient's representative) AND (CICC placed) AND (CVP measurements) AND (PICC) AND (ability to lay in a supine position with their hands at their sides) AND (age) AND (during CVP measurements) AND (in the internal jugular vein position) AND (in the subclavian vein position) AND (indwelling CICC) AND (transitioning to a PICC))"}
{"candidate_id": "LLM05297", "doc_id": "NCT03320057_exc", "case_bucket": "other", "source_criterion": "Not pregnant Not seeking medication abortion Under the age of 15 Contraindications for medication abortion", "candidate_expression": "((Contraindications) AND (Under 15) AND (age) AND (medication abortion) AND (pregnant))"}
{"candidate_id": "LLM05298", "doc_id": "NCT02634541_inc", "case_bucket": "or", "source_criterion": "Axial spondyloarthritis (ASAS criteria) and radiologic sacroiliitis as detected either by MRI or X-ray.", "candidate_expression": "((Axial spondyloarthritis ASAS criteria) AND (radiologic) AND (sacroiliitis) AND ((MRI) OR (X-ray)))"}
{"candidate_id": "LLM05299", "doc_id": "NCT02691793_exc", "case_bucket": "or", "source_criterion": "Patients with second primary cancer, except:adequately treated non-melanoma skin cancer, curatively treated in-situ cancer of the cervix, or other solid tumor curatively treated with no evidence of disease for <= 5 years. Has known active central nervous system(CNS) metastases Has an active infection requiring systemic therapy Pregnancy or breast feeding Patients with cardiac problem Any previous treatment with sunitinib", "candidate_expression": "((CNS) AND (Pregnancy or breast feeding) AND (active infection) AND (cardiac problem) AND (central nervous system) AND (except) AND (in-situ cancer of the cervix) AND (metastases) AND (non-melanoma skin cancer) AND (primary cancer,) AND (second) AND (solid tumor) AND (sunitinib) AND (treated))"}
{"candidate_id": "LLM05300", "doc_id": "NCT02950558_inc", "case_bucket": "other", "source_criterion": "Referred for surgery for open reduction and internal fixation for ankle fracture", "candidate_expression": "((ankle fracture) AND (open reduction and internal fixation) AND (surgery))"}
```
