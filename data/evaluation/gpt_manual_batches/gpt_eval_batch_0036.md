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
{"candidate_id": "LLM00876", "doc_id": "NCT02837783_exc", "case_bucket": "or", "source_criterion": "Patient has history of loose or watery stools Patient has both clinically significant findings and unexplained clinically significant alarm symptoms Patient has symptoms of or been diagnosed with a medical condition that may contribute to abdominal pain Patient has any protocol-excluded or clinically significant medical or surgical history that could confound the study assessments", "candidate_expression": "((Patient has any protocol-excluded or clinically significant medical or surgical history that could confound the study assessments) AND (abdominal pain) AND (clinically significant alarm symptoms unexplained) AND (clinically significant findings) AND (medical condition may contribute to abdominal pain) AND ((clinically significant) OR (protocol-excluded)) AND ((medical history) OR (surgical history)) AND ((loose stools) OR (watery stools)))"}
{"candidate_id": "LLM00877", "doc_id": "NCT02652572_inc", "case_bucket": "or", "source_criterion": "1. Age 18 years or older 2. Diagnosis of venous leg ulcer(s), as clinically determined by the investigator by a positive venous reflux test (venous refilling <20 seconds) using Doppler ultrasound for at least 4 weeks prior to screening day, which have not adequately responded to conventional ulcer therapy. 3. Designated venous leg ulcer meets the following criteria at both the screening and baseline visits. If the patient has multiple ulcers, at least one ulcer must meet the following criteria at both the screening and baseline visits: 1. Present for at least 4 weeks 2. CEAP Classification Stage 6 3. Surface ulcer with an area > 15cm2 post debridement 4. Viable, granulating wound (investigator discretion) 4. Ulcers that extend through the epidermis but not through the muscle, tendon, or bone (Stage II or III ulcers as defined by the IAET). 5. Female patients of childbearing potential must have a negative pregnancy test at screening and must agree to use hormonal contraceptive, intrauterine device, diaphragm with spermicide, condom with spermicide, or abstinence throughout until 2 weeks after the last administration of study drug 6. Signed informed consent", "candidate_expression": "((18 years or older) AND (<20 seconds) AND (> 15cm2) AND (Age) AND (CEAP Classification) AND (Doppler ultrasound) AND (Female) AND (IAET) AND (Present) AND (Signed informed consent) AND (Stage 6) AND (Stage II or III) AND (Surface ulcer) AND (Ulcers) AND (Viable) AND (abstinence) AND (adequately) AND (area post debridement) AND (at least 4 weeks) AND (at least 4 weeks prior to screening day) AND (at least one) AND (at screening) AND (childbearing potential) AND (condom with spermicide) AND (conventional ulcer therapy) AND (diaphragm with spermicide) AND (extend through the bone) AND (extend through the epidermis) AND (extend through the muscle) AND (extend through the tendon) AND (granulating) AND (hormonal contraceptive) AND (intrauterine device) AND (investigator discretion) AND (last administration of study drug) AND (multiple) AND (negative) AND (not) AND (positive) AND (pregnancy test) AND (responded) AND (screening) AND (screening day) AND (throughout until 2 weeks after the last administration of study drug) AND (ulcer) AND (ulcers) AND (venous leg ulcer) AND (venous leg ulcer(s)) AND (venous refilling) AND (venous reflux test) AND (wound))"}
{"candidate_id": "LLM00878", "doc_id": "NCT02316886_inc", "case_bucket": "or", "source_criterion": "Age 18 years or older Symptomatic or asymptomatic coronary artery disease patients MLA(minimal luminal area)<4mm2 plaque burden>70% Lipid-rich plaque on NIRS(Intracoronary Near-Infrared Spectroscopy) (defined as maxLCBI4mm>315) 2 target vulnerable lesions Eligible for percutaneous coronary intervention with Absorb Bioresorbable Vascular Scaffold or Everolimus Eluting Stent Willing and able to provide informed written consent Reference vessel diameter 2.75-4.0 Lesion length = 40", "candidate_expression": "((18 years or older) AND (2) AND (2.75-4.0) AND (<4mm2) AND (= 40) AND (>315) AND (>70%) AND (Age) AND (Eligible for) AND (Intracoronary Near-Infrared Spectroscopy) AND (Lesion length) AND (Lipid-rich plaque) AND (MLA) AND (NIRS) AND (Reference vessel diameter) AND (Willing and able to provide informed written consent) AND (coronary artery disease) AND (maxLCBI4mm) AND (minimal luminal area) AND (percutaneous coronary intervention) AND (plaque burden) AND (target vulnerable lesions) AND ((Absorb Bioresorbable Vascular Scaffold) OR (Everolimus Eluting Stent)) AND ((Symptomatic) OR (asymptomatic)))"}
{"candidate_id": "LLM00879", "doc_id": "NCT02596555_exc", "case_bucket": "or", "source_criterion": "Pregnancy (a negative serum or urine pregnancy test should be available for women of child-bearing potential before study inclusion) or lactation Women of childbearing potential who do not practice a medically accepted highly effective contraception during the trial and one month beyond History of hypersensitivity to the investigational medicinal product or to any drug with similar chemical structure or to any excipient present in the pharmaceutical form of the investigational medicinal product Participation in another clinical trial during the present clinical trial or within the last three months Medical or psychological condition that would not permit completion of the trial or signing of informed consent Use of a fibrinolytic agent, surgical thrombectomy, interventional (catheter-directed) thrombus aspiration or lysis, or use of a cava filter to treat the index episode of PE Treatment with any therapeutically dosed anticoagulant for more than 48 hours prior to enrolment Need for long-term treatment with a low molecular weight heparin, vitamin K antagonists or NOAC, for an indication other than the index PE episode, or for antiplatelet agents except acetylsalicylic acid at a dosage =100 mg/day; Active bleeding or known significant bleeding risk (e.g., gastrointestinal ulcer, malignant neoplasms, injuries or recent surgeries of the brain, spinal cord or eyes, recent intracranial bleedings, known or suspected esophagus varices, aneurysms or intraspinal or intracranial vascular abnormalities) Artificial heart valves requiring treatment with an anticoagulant Renal insufficiency with estimated creatinine clearance <30 ml/min/1.73m2 Chronic liver disease with aminotransferase levels two times or more above the local upper limit of normal range Concomitant administration of strong inhibitors of P-glycoprotein like ketoconazole, cyclosporin, itraconazole or dronedarone Unwillingness or inability to adhere to treatment or to the follow-up visits Life expectancy less than 6 months", "candidate_expression": "((Active bleeding) AND (Artificial heart valves) AND (Chronic liver disease) AND (Life expectancy less than 6 months) AND (Medical or psychological condition that would not permit completion of the trial or signing of informed consent) AND (NOAC) AND (PE) AND (Participation in another clinical trial during the present clinical trial or within the last three months) AND (Pregnancy (a negative serum or urine pregnancy test should be available for women of child-bearing potential before study inclusion) or lactation) AND (Renal insufficiency) AND (Unwillingness or inability to adhere to treatment or to the follow-up visits) AND (Women of childbearing potential who do not practice a medically accepted highly effective contraception during the trial and one month beyond) AND (aminotransferase two times or more above the local upper limit of normal range) AND (aneurysms intraspinal intracranial) AND (anticoagulant) AND (anticoagulant therapeutically more than 48 hours prior to enrolment) AND (antiplatelet agents =100 mg/day;) AND (bleeding risk significant) AND (cava filter) AND (cyclosporin) AND (dronedarone) AND (esophagus varices) AND (estimated creatinine clearance <30 ml/min/1.73m2) AND (fibrinolytic agent) AND (gastrointestinal ulcer) AND (inhibitors of P-glycoprotein) AND (injuries) AND (intracranial bleedings) AND (itraconazole) AND (ketoconazole) AND (low molecular weight heparin) AND (malignant neoplasms) AND (surgeries brain spinal cord eyes) AND (surgical thrombectomy,) AND (thrombus aspiration) AND (thrombus lysis) AND (vascular abnormalities)) AND (vitamin K antagonists) AND NOT (PE episode index) AND NOT (acetylsalicylic acid))"}
{"candidate_id": "LLM00880", "doc_id": "NCT01996436_inc", "case_bucket": "other", "source_criterion": "Adult patient, age 18-80 years old, with ruptured aneurysm(s) who experience cerebral vasospasm post operatively within 3-21 days.", "candidate_expression": "((Adult) AND (age 18-80 years old) AND (cerebral vasospasm post operatively within 3-21 days) AND (ruptured aneurysm))"}
{"candidate_id": "LLM00881", "doc_id": "NCT02379156_inc", "case_bucket": "other", "source_criterion": "Duration of SCI =1 year; Level of SCI C3-T1, AIS A & B; Age between 18 and 65 years.", "candidate_expression": "((=1 year) AND (A & B) AND (AIS) AND (Age) AND (C3-T1) AND (Level of SCI) AND (SCI) AND (between 18 and 65 years))"}
{"candidate_id": "LLM00882", "doc_id": "NCT03169127_exc", "case_bucket": "or", "source_criterion": "Presence of systemic diseases; Presence of local inflammation and/or infection; Any history of allergic reaction to local anesthetics, gastrointestinal bleeding or ulceration; Cardiovascular, kidney or hepatic diseases; Patients who are making use of antidepressants, diuretics or anticoagulants; Asthma and allergy to aspirin, ibuprofen or any other nonsteroidal antiinflammatory drug; Regular use of any nonsteroidal antiinflammatory drug, Pregnancy or breast feeding.", "candidate_expression": "((Asthma) AND (Cardiovascular diseases) AND (Pregnancy) AND (Regular use) AND (allergic reaction) AND (allergy) AND (anticoagulants) AND (antidepressants) AND (any other) AND (aspirin) AND (breast feeding) AND (diuretics) AND (gastrointestinal bleeding) AND (gastrointestinal ulceration) AND (hepatic diseases) AND (history) AND (ibuprofen) AND (kidney diseases) AND (local anesthetics) AND (local infection) AND (local inflammation) AND (nonsteroidal antiinflammatory drug) AND (systemic diseases))"}
{"candidate_id": "LLM00883", "doc_id": "NCT02287259_inc", "case_bucket": "or", "source_criterion": "major depressive episode in type2 bipolar disorder or bipolar disorder NOS.(MADRS more than 20 point) 18years to 65years subjects who sign the informed consent document", "candidate_expression": "((MADRS more than 20 point) AND (bipolar disorder NOS) AND (major depressive episode) AND (sign the informed consent) AND (type2 bipolar disorder) AND (years 18years to 65years))"}
{"candidate_id": "LLM00884", "doc_id": "NCT03125057_inc", "case_bucket": "other", "source_criterion": "Children with clinical diagnosis of PWS; Age range: 7 to 14 years-old; Voluntarily participated and Written informed consent signed", "candidate_expression": "((7 to 14 years-old) AND (Age) AND (Children) AND (PWS) AND (Voluntarily participated) AND (Written informed consent signed) AND (clinical diagnosis))"}
{"candidate_id": "LLM00885", "doc_id": "NCT02593409_inc", "case_bucket": "other", "source_criterion": "age =18 at screening not intending to move away from the clinic's catchment area for the next 2 years HIV-1 antibody negative reports commercial sex work contact information is provided written informed consent", "candidate_expression": "((=18) AND (HIV-1 antibody) AND (age) AND (commercial sex work) AND (contact information is provided) AND (negative) AND (written informed consent))"}
{"candidate_id": "LLM00886", "doc_id": "NCT02145026_exc", "case_bucket": "or", "source_criterion": "Contraindications and/or known hypersensitivity to the active substance and/or any of the excipients of epoetin beta treatment Poorly controlled hypertension as assessed by the investigator History of Acute Myeloid Leukemia (AML) or high risk for AML Administration of another investigational drug within 1 month before screening or planned during the study period Previously documented evidence of Pure Red Cell Aplasia (PRCA)", "candidate_expression": "((AML) AND (Acute Myeloid Leukemia) AND (Administration of another investigational drug within 1 month before screening or planned during the study period) AND (Contraindications) AND (PRCA) AND (Pure Red Cell Aplasia) AND (epoetin beta treatment) AND (hypersensitivity) AND (hypertension Poorly controlled) AND (risk for AML high))"}
{"candidate_id": "LLM00887", "doc_id": "NCT02456129_inc", "case_bucket": "or", "source_criterion": "Body mass index (BMI): 18 ≤ BMI ≤ 32 kg/m² Postmenopausal state revealed by: Medical history, if applicable (natural menopause at least 12 months prior to first study drug administration; or surgical menopause by bilateral ovariectomy at least 3 months prior to first study drug administration), in addition: in women < 65 years old, follicle stimulating hormone (FSH) > 40 IU/L", "candidate_expression": "((18 ≤ BMI ≤ 32 kg/m²) AND (< 65 years) AND (> 40 IU/L) AND (Body mass index (BMI)) AND (Postmenopausal state) AND (at least 12 months prior to first study drug administration) AND (at least 3 months prior to first study drug administration) AND (bilateral ovariectomy) AND (first study drug administration) AND (follicle stimulating hormone (FSH)) AND (natural menopause) AND (surgical menopause) AND (women) AND (years old))"}
{"candidate_id": "LLM00888", "doc_id": "NCT02868437_inc", "case_bucket": "other", "source_criterion": "Subject has curettage for retained product after second trimester abortion", "candidate_expression": "((abortion second trimester) AND (curettage) AND (retained product))"}
{"candidate_id": "LLM00889", "doc_id": "NCT03149887_inc", "case_bucket": "other", "source_criterion": "Adult patients up to age 75 years, undergoing elective, ambulatory, arthroscopic rotator cuff repair.", "candidate_expression": "((Adult) AND (age up to 75 years) AND (ambulatory) AND (arthroscopic rotator cuff repair elective))"}
{"candidate_id": "LLM00890", "doc_id": "NCT03228498_inc", "case_bucket": "or", "source_criterion": "1. Cognitive impairment from mild to moderate degree defined by a Clinical Deterioration Rating (CDR) score range between 0.5 and 2.0. 2. Evidence on brain MRI of white matter hyperintensities (leukoaraiosis of moderate or severe degree according to the modified Fazekas visual scale and/or presence of lacunar infarcts). 3. Consent to participation in the study.", "candidate_expression": "((Clinical Deterioration Rating (CDR) score) AND (Cognitive impairment) AND (brain MRI) AND (leukoaraiosis) AND (mild to moderate) AND (moderate or severe degree) AND (range between 0.5 and 2.0) AND (white matter hyperintensities) AND ((lacunar infarcts) OR (modified Fazekas visual scale)))"}
{"candidate_id": "LLM00891", "doc_id": "NCT02600000_exc", "case_bucket": "or", "source_criterion": "Unstable angina; Myocardial infarction and heart surgery up to three months before the survey; Chronic respiratory diseases; Hemodynamic instability; Trauma recent face, nausea and vomiting. Orthopedic and neurological diseases that may preclude the achievement of the cardiopulmonary test and Cardiac Rehabilitation exercises; Psychological and / or cognitive impairments that restrict them to respond to questionnaires;", "candidate_expression": "((Chronic respiratory diseases) AND (Hemodynamic instability) AND (Unstable angina) AND ((Orthopedic preclude the achievement of the cardiopulmonary test and Cardiac Rehabilitation exercises) OR (neurological diseases preclude the achievement of the cardiopulmonary test and Cardiac Rehabilitation exercises)) AND ((Psychological impairments restrict them to respond to questionnaires) OR (cognitive impairments restrict them to respond to questionnaires)) AND ((Myocardial infarction) OR (heart surgery)) AND ((Trauma) OR (nausea) OR (vomiting)))"}
{"candidate_id": "LLM00892", "doc_id": "NCT02456129_exc", "case_bucket": "or", "source_criterion": "Incompletely cured pre-existing diseases for which it can be assumed that the absorption, distribution, metabolism, elimination or effects of the study drugs will not be normal Known or suspected liver diseases Clinically relevant findings(e.g. blood pressure, electrocardiogram(ECG); physical and gynecological examination, laboratory examination)", "candidate_expression": "((Clinically relevant) AND (Incompletely cured) AND (can be assumed) AND (findings) AND (liver diseases) AND (pre-existing diseases) AND (suspected) AND ((blood pressure) OR (electrocardiogram(ECG)) OR (gynecological examination) OR (laboratory examination) OR (physical examination)) AND ((Known) OR (suspected)))"}
{"candidate_id": "LLM00893", "doc_id": "NCT01424020_inc", "case_bucket": "other", "source_criterion": "French Native language 18 years old or older Signed consent Covered by the French social care system", "candidate_expression": "((18 years or older) AND (Covered by the French social care system) AND (French Native language) AND (Signed consent) AND (old))"}
{"candidate_id": "LLM00894", "doc_id": "NCT03404479_exc", "case_bucket": "or", "source_criterion": "Secondary knee osteoarthritis Other inflammatory Knee Osteoarthritis (e.g. gout, rheumatoid arthritis, etc.) Patients presenting with gastroesophageal reflux disease, peptic ulcer. Helicobacter infected patients who have not been treated for eradication (recruitment if negative in re-examination after treatment). Short bowel syndrome that can cause inflammatory bowel disease (ulcerative colitis, Crohn's disease) and drug absorption disorder. Intestinal obstruction syndrome Unexplained abdominal pain ALT(Alanine aminotransferase) level of liver function test exceeded 5 times of reference range Total bilirubin level exceeded 2 mg / dL Serum albumin level less than 2 g / dL Ascites Hepatic encephalopathy Hepatitis B, hepatitis C (excluding healthy carriers) or HIV positive MDRD(Modification of Diet in Renal Disease) Estimated Glomerular filtration rate less than 60 mL / m2 Patients with hyperkalemia (over 5.5 meq / L) history of asthma, acute rhinitis, nasal polyps, angioedema, urticaria or allergic reactions to aspirin or other non-steroidal anti-inflammatory drugs(including COX-2 inhibitors). Malignant tumors other than basal cell or squamous cell carcinoma of the skin, CIN(Cervical Intraepitherial Neoplasia) and CIS(Carcinoma in situ) of the cervix, and intraepithelial carcinoma of other areas Within 5 years of consent date. Medical history of hypersensitivity to the components of the investigational products. (The components of test drug 1 and 2, including the Rhein-based drug) Patients with an allergic reaction to sulfonamide. Patients with galactose intolerance, lapp lactase deficiency or glucose-galactose malabsorption. Subjects who have not reached the prescribed period after receiving contraindicated medication or treatment before participation in this clinical trial. Patients receiving contraindicated medication. Alcohol and other drug abuse cases based on 6 months before screening. Pregnant women or nursing mothers who are not willing to stop breastfeeding. (1) Menopause (non-therapy-induced amenorrhea of more than 12 months) Female (2) Female infertility due to surgery (no ovaries and / or uterus) (3) If you have sexual intercourse with only one male partner who has been confirmed to have no semen after fertilization. (4) Female subjects who agreed to abstinence during the clinical trial period. If the subject is assured of an abstinence throughout the trial period.(e.g. clergy) However, intermittent abstinence (eg, contraception using ovulation period, symptothermal) or coitus interrupts is not a case of consent for abstinence. (5) For women of childbearing age, the following methods or methods of contraception use the effective method of contraception to be used during the period of this clinical trial: Oral contraceptive The contraceptive patch Intra uterine device (IUD) contraceptive implant contraceptive injection intrauterine hormonal apparatus Tubal ligation and infertility surgery If 30 days have not elapsed after the date of signing of the previous clinical trial or currently participating in other clinical trials. Patients who are scheduled for surgery during the clinical trial period or who have difficulties in completing the protocol during this clinical trial due to other reasons. In addition to the above, other diseases that the investigator judges to be inappropriate.", "candidate_expression": "(((5) For women of childbearing age, the following methods or methods of contraception use the effective method of contraception to be used during the period of this clinical trial:) AND (ALT(Alanine aminotransferase) level exceeded 5 times of reference range) AND (Alcohol abuse 6 months before screening) AND (Ascites) AND (CIN(Cervical Intraepitherial Neoplasia)) AND (CIS(Carcinoma in situ) of the cervix) AND (COX-2 inhibitors) AND (Crohn's disease) AND (Estimated Glomerular filtration rate MDRD(Modification of Diet in Renal Disease) less than 60 mL / m2) AND (Female) AND (Female subjects who agreed to abstinence during the clinical trial period) AND (HIV positive) AND (Helicobacter infected) AND (Hepatic encephalopathy) AND (Hepatitis B) AND (However, intermittent abstinence (eg, contraception using ovulation period, symptothermal) or coitus interrupts is not a case of consent for abstinence) AND (If 30 days have not elapsed after the date of signing of the previous clinical trial or currently participating in other clinical trials.) AND (If the subject is assured of an abstinence throughout the trial period.(e.g. clergy)) AND (If you have sexual intercourse with only one male partner who has been confirmed to have no semen after fertilization.) AND (Intestinal obstruction syndrome) AND (Intra uterine device (IUD)) AND (Malignant tumors) AND (Menopause) AND (Oral contraceptive) AND (Pregnant women or nursing mothers who are not willing to stop breastfeeding) AND (Rhein-based drug) AND (Serum albumin level ess than 2 g / dL) AND (Short bowel syndrome that can cause inflammatory bowel disease) AND (Total bilirubin level exceeded 2 mg / dL) AND (Tubal ligation) AND (abdominal pain Unexplained) AND (acute rhinitis) AND (allergic reaction) AND (allergic reactions) AND (amenorrhea non-therapy-induced more than 12 months) AND (angioedema) AND (aspirin) AND (asthma) AND (basal cell carcinoma of the skin) AND (components of test drug 1) AND (components of test drug 2) AND (components of the investigational products) AND (contraceptive implant) AND (contraceptive injection) AND (contraceptive patch) AND (contraindicated medication) AND (drug absorption disorder) AND (drug abuse) AND (galactose intolerance) AND (gastroesophageal reflux disease) AND (glucose-galactose malabsorption) AND (gout) AND (hepatitis C) AND (hyperkalemia over 5.5 meq / L) AND (hypersensitivity) AND (infertility due to surgery) AND (infertility surgery) AND (inflammatory Knee Osteoarthritis Other) AND (inflammatory bowel disease can cause) AND (intraepithelial carcinoma) AND (intrauterine hormonal apparatus) AND (knee osteoarthritis Secondary) AND (lapp lactase deficiency) AND (liver function test) AND (nasal polyps) AND (no ovaries) AND (no uterus) AND (non-steroidal anti-inflammatory drugs other) AND (peptic ulcer) AND (rheumatoid arthritis) AND (squamous cell carcinoma of the skin) AND (sulfonamide) AND (ulcerative colitis) AND (urticaria) AND NOT (treated for eradication) AND NOT (healthy carriers))"}
{"candidate_id": "LLM00895", "doc_id": "NCT03387059_exc", "case_bucket": "or", "source_criterion": "Clinically significant systemic disease (such as diabetes, metabolic syndrome, immunological diseases, diagnosed thrombophilia, porphyria, or any other medical condition requiring the use of low-molecular weight heparin therapy) Polycystic ovary syndrome (PCOS) according to Rotterdam Consensus Criteria (European Society of Human Reproduction and Embryology [ESHRE]/American Society for Reproductive Medicine [ASRM], 2003) Poor ovarian response (POR) according to the European Society of Human Reproduction and Embryology (ESHRE) Criteria RIF (repeated implantation failure), defined as greater than or equals to (>=) 2 previous failed embryo transfers Endometriosis III-IV stage or adenomyosis Clinically significant findings on exam or ultrasound, such as salpingitis, hydrosalpynx or evidence of ovarian cysts Known hypersensitivity to any of the components of the solution Known hypersensitivity to vaginal progesterone or its excipients Other protocol defined exclusion criteria could apply", "candidate_expression": "((Clinically significant) AND (European Society of Human Reproduction and Embryology (ESHRE) Criteria) AND (European Society of Human Reproduction and Embryology [ESHRE]/American Society for Reproductive Medicine [ASRM], 2003) AND (III-IV stage) AND (Polycystic ovary syndrome (PCOS)) AND (Poor ovarian response (POR)) AND (RIF (repeated implantation failure)) AND (Rotterdam Consensus Criteria) AND (components of the solution) AND (evidence) AND (findings) AND (greater than or equals to (>=) 2) AND (hypersensitivity) AND (low-molecular weight heparin) AND (previous failed embryo transfers) AND (systemic disease) AND ((Endometriosis) OR (adenomyosis)) AND ((exam) OR (ultrasound)) AND ((hydrosalpynx) OR (ovarian cysts) OR (salpingitis)) AND ((diabetes) OR (diagnosed thrombophilia) OR (immunological diseases) OR (medical condition) OR (metabolic syndrome) OR (porphyria)) AND ((excipients) OR (vaginal progesterone)))"}
{"candidate_id": "LLM00896", "doc_id": "NCT00752310_inc", "case_bucket": "or", "source_criterion": "Non-smoking, or smoking no more than 10 cigarettes, or 2 cigars, or 2 pipes per day for at least 3 months prior to selection Normal weight as defined by a Body Mass Index (BMI, weight in kg divided by the square of height in meters) of 18.0 to 30.0 kg/m2, extremes included Able to comply with protocol requirements. Healthy on the basis of a medical evaluation that reveals the absence of any clinically relevant abnormality and includes a physical examination, medical history, electrocardiogram (ECG), vital signs, and the results of blood biochemistry, blood coagulation, and hematology tests and a urinalysis carried out at screening.", "candidate_expression": "((18.0 to 30.0 kg/m2, extremes included) AND (Able to comply with protocol requirements) AND (Body Mass Index) AND (ECG) AND (Healthy) AND (Non) AND (Normal weight) AND (abnormality) AND (absence) AND (at screening) AND (blood biochemistry tests) AND (blood coagulation tests) AND (clinically relevant) AND (electrocardiogram) AND (for at least 3 months prior to selection) AND (hematology tests) AND (medical evaluation) AND (medical history) AND (no more than 10 per day) AND (no more than 2 per day) AND (physical examination) AND (screening) AND (selection) AND (urinalysis) AND (vital signs) AND ((smoking)) AND ((BMI) OR (weight in kg divided by the square of height in meters)) AND ((cigarettes) OR (cigars) OR (pipes)))"}
{"candidate_id": "LLM00897", "doc_id": "NCT01483118_inc", "case_bucket": "or", "source_criterion": "Patients aged greater than 18 years of age Ability to understand and willingness to comply with the study protocol Written informed consent Patients meeting the Rotterdam PCOS workshop criteria for polycystic ovary syndrome, defined by oligomenorrhea or amenorrhea and at least one of the following two signs: clinical or biochemical evidence of hyperandrogenism or ultrasound finding of polycystic appearing ovaries.", "candidate_expression": "((Ability to understand and willingness to comply with the study protocol) AND (Rotterdam PCOS workshop criteria for polycystic ovary syndrome meeting) AND (Written informed consent) AND (age greater than 18 years) AND (aged greater than 18 years) AND (amenorrhea at least one) AND (hyperandrogenism) AND (oligomenorrhea) AND (polycystic ovaries) AND (ultrasound))"}
{"candidate_id": "LLM00898", "doc_id": "NCT03211741_exc", "case_bucket": "or", "source_criterion": "Women who are pregnant or breastfeeding (pregnancy defined as the state of a female after conception until the termination of gestation, confirmed by a positive human chorionic gonadotropin laboratory test (> 5mIU/mL) Women of child bearing potential must be practicing effective contraception implemented during the trial and for at least 28 days following the last dose of study medication Tromboembolic event (CVA or transient ischemic attack, AMI) less than 3 months prior to the intravitreal injection of bevacizumab History of hypersensitivity for bevacizumab.", "candidate_expression": "((> 5mIU/mL) AND (History) AND (Tromboembolic event) AND (Women) AND (bevacizumab) AND (child bearing potential) AND (contraception) AND (during the trial) AND (effective) AND (for at least 28 days following the last dose of study medication) AND (human chorionic gonadotropin) AND (human chorionic gonadotropin laboratory test) AND (hypersensitivity) AND (intravitreal injection) AND (last dose) AND (less than 3 months prior to the intravitreal injection of bevacizumab) AND (positive) AND (study medication) AND (the intravitreal injection of bevacizumab) AND (the last dose of study medication) AND ((AMI) OR (CVA) OR (transient ischemic attack)) AND ((breastfeeding) OR (pregnant)))"}
{"candidate_id": "LLM00899", "doc_id": "NCT02312076_exc", "case_bucket": "or", "source_criterion": "Moderate or severe endometriosis. Hydrosalpinx. Uterine abnormalities. Myoma. Previous uterine surgery.", "candidate_expression": "((Hydrosalpinx) AND (Myoma) AND (Previous) AND (Uterine abnormalities) AND (endometriosis) AND (uterine surgery) AND ((Moderate) OR (severe)))"}
{"candidate_id": "LLM00900", "doc_id": "NCT02937779_exc", "case_bucket": "other", "source_criterion": "Women refusing HBs Ag test HIV co-infection HCV co-infection HBV treatment ongoing at the day of inclusion Creatinine clearance < 30 mL/min Severe gravidic disease present at inclusion involving life threatening to the mother and/or the child Evidence of pre-existing fetal anomalies incompatible with the child's life Imminent child's birth defined as cervix dilatation up to 7 centimeters Intention to deliver in a maternity not linked to the study Any concomitant medical condition that, according to the clinical site investigator would contraindicate participation in the study. Concurrent participation in any other clinical trial without written agreement of the two study teams", "candidate_expression": "((7 centimeters) AND (< 30 mL/min) AND (Any concomitant medical condition that, according to the clinical site investigator would contraindicate participation in the study) AND (Concurrent participation in any other clinical trial without written agreement of the two study teams) AND (Creatinine clearance) AND (HBV treatment) AND (HBs Ag test) AND (HCV) AND (HIV) AND (Imminent child's birth) AND (Intention to deliver in a maternity not linked to the study) AND (Severe) AND (cervix dilatation) AND (co-infection) AND (fetal anomalies) AND (gravidic disease) AND (life threatening) AND (refusing))"}
```
