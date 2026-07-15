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
{"candidate_id": "LLM00776", "doc_id": "NCT02704754_inc", "case_bucket": "other", "source_criterion": "Physically healthy adults age 18-55 who meet DSM-5 criteria for insomnia and Criterion A (exposure to a traumatic event) for PTSD. The index trauma must have occurred within the past 5 years and at least 3 months before enrolling, and insomnia symptoms must have started or worsened after the exposure to the index trauma", "candidate_expression": "((18-55) AND (Criterion A) AND (DSM-5) AND (PTSD) AND (adults) AND (age) AND (healthy) AND (index) AND (insomnia) AND (the past 5 years and at least 3 months) AND (trauma))"}
{"candidate_id": "LLM00777", "doc_id": "NCT03185130_inc", "case_bucket": "or", "source_criterion": "Age 10 to 65 years Temperature less than 100.4 F Normal neurologic exam and normal mental status", "candidate_expression": "((10 to 65 years) AND (Age) AND (Normal) AND (Temperature) AND (less than 100.4 F) AND (neurologic exam) AND ((mental status) OR (normal)))"}
{"candidate_id": "LLM00778", "doc_id": "NCT01531257_inc", "case_bucket": "or", "source_criterion": "1. Male and female recipients of all races, ≥18 years of age. 2. Patients undergoing primary or subsequent deceased-donor or living donor kidney transplantation. 3. Subject and/or guardian must be able to provide informed consent. 4. Subject and/or guardian must be able to comply with the study protocol.", "candidate_expression": "((Subject and/or guardian must be able to comply with the study protocol.) AND (Subject and/or guardian must be able to provide informed consent.) AND (age) AND (≥18 years) AND ((Male) OR (female)) AND ((primary) OR (subsequent)) AND ((deceased-donor kidney transplantation) OR (living donor kidney transplantation)))"}
{"candidate_id": "LLM00779", "doc_id": "NCT02902120_exc", "case_bucket": "or", "source_criterion": "Documented positive hepatitis B (HBV) surface antigen, and/or HBV DNA prior to enrollment Any prior exposure to HCV protease inhibitor therapy HIV co-infection if on a protease inhibitor based regimen Increase in creatinine of 15% or greater within one month (30 days) of the screening visit Evidence of hepatocellular carcinoma at the time of enrollment Liver disease caused by an etiology other than HCV F4 or decompensated cirrhotic patients Child Pugh class B or C AST or ALT >350 within 6 months prior to enrollment Albumin < 3g/dL at the time of enrollment Platelet count < 75 at the time of enrollment History of clinically significant allergy or adverse event with protease inhibitors Evidence of the acquisition of HCV at the time of or after transplantation Pregnant or breastfeeding women Cyclosporine; St. John's Wort; Efavirenz; Phenytoin; Carbamazepine; Bosentan; HIV protease inhibitors; modafinil; ketoconazole; or rifampin use within 7 days of enrollment Coadministration of more than 20 mg atorvastatin; 10 mg rosuvastatin; 20 mg of fluvastatin, lovastatin or simvastatin", "candidate_expression": "((30 days) AND (< 3g/dL) AND (< 75) AND (>350) AND (Albumin) AND (B or C) AND (Child Pugh class) AND (HCV) AND (HCV protease inhibitor therapy) AND (HIV co-infection) AND (Increase of 15% or greater) AND (Liver disease) AND (Platelet count) AND (Pregnant or breastfeeding women) AND (acquisition of HCV) AND (at the time of or after transplantation) AND (creatinine) AND (enrollment) AND (hepatocellular carcinoma) AND (more than 10 mg) AND (more than 20 mg) AND (other) AND (positive) AND (prior to enrollment) AND (protease inhibitor) AND (protease inhibitors) AND (transplantation) AND (within 6 months prior to enrollment) AND (within 7 days of enrollment) AND (within one month) AND ((F4) OR (decompensated cirrhotic)) AND ((ALT) OR (AST)) AND ((HBV DNA) OR (hepatitis B surface antigen)) AND ((adverse event) OR (allergy)) AND ((Bosentan) OR (Carbamazepine) OR (Cyclosporine) OR (Efavirenz) OR (HIV protease inhibitors) OR (Phenytoin) OR (St. John's Wort) OR (ketoconazole) OR (modafinil) OR (rifampin)) AND ((atorvastatin) OR (rosuvastatin)) AND ((fluvastatin) OR (lovastatin) OR (simvastatin)))"}
{"candidate_id": "LLM00780", "doc_id": "NCT03156855_inc", "case_bucket": "or", "source_criterion": "children and teenagers aged less than 20 years, history of gastrectomy, gastric malignancy, including adenocarcinoma and lymphoma, previous allergic reaction to antibiotics (bismuth, amoxicillin, metronidazole, clarithromycin, tetracycline) and PPI (esomeprazole), contraindication to treatment drugs, pregnant or lactating women, severe concurrent disease, concomitant use of clopidogrel, or (9) Unwilling to accept random assignment of subjects", "candidate_expression": "((PPI) AND (Unwilling to accept random assignment of subjects) AND (adenocarcinoma) AND (aged less than 20 years) AND (allergic reaction previous) AND (amoxicillin) AND (antibiotics) AND (bismuth) AND (children) AND (clarithromycin) AND (clopidogrel concomitant) AND (contraindication) AND (disease severe concurrent) AND (esomeprazole) AND (gastrectomy history) AND (gastric malignancy) AND (lactating) AND (lymphoma) AND (metronidazole) AND (pregnant) AND (teenagers) AND (tetracycline) AND (treatment drugs) AND (women))"}
{"candidate_id": "LLM00781", "doc_id": "NCT03355157_exc", "case_bucket": "other", "source_criterion": "NA", "candidate_expression": "(EMPTY)"}
{"candidate_id": "LLM00782", "doc_id": "NCT02933671_exc", "case_bucket": "or", "source_criterion": "ASA 4 or 5 revision hip arthroplasty diagnosis of chronic pain daily chronic opioid use (over 3 months of continuous opioid use) inability to communicate pain scores or need for analgesia acute hip fracture Infection at the site of block placement Age under 18 years old or greater than 75 years old Pregnant women Intolerance/allergy to local anesthetics Weight <50 kg Suspected, or known addiction to or abuse of illicit drug(s), prescription medicine(s), or alcohol within the past 2 years. Uncontrolled anxiety, schizophrenia, or other psychiatric disorder that, in the opinion of the investigator, may interfere with study assessments or compliance Current or historical evidence of any clinically significant disease or condition that, in the opinion of the investigator, may increase the risk of surgery or complicate the subject's postoperative course.", "candidate_expression": "((4 or 5) AND (<50 kg) AND (ASA) AND (Age) AND (Infection) AND (Intolerance) AND (Pregnant women) AND (Weight) AND (abuse) AND (acute) AND (addiction) AND (alcohol) AND (allergy) AND (anxiety) AND (chronic) AND (chronic pain) AND (hip fracture) AND (illicit drug) AND (inability to communicate pain scores or need for analgesia) AND (local anesthetics) AND (opioid) AND (over 3 months) AND (past 2 years) AND (prescription medicine) AND (psychiatric disorder) AND (revision hip arthroplasty) AND (schizophrenia) AND (site of block placement) AND (under 18 years old or greater than 75 years old))"}
{"candidate_id": "LLM00783", "doc_id": "NCT03355469_inc", "case_bucket": "or", "source_criterion": "Male or female >40 and <70 years old. Has a body mass index >27 and <47 kg/m2. Not diagnosed with Type 2 diabetes. Not currently engaged in > 60 min/wk of exercise Meet at least 3 of 5 National Cholesterol Education Adult Treatment Panel III Increased waist circumference (=102 cm in men; =88 cm in women) Elevated triglycerides (=150 mg/dl), or on medication for treating the condition Reduced HDL-cholesterol (<40mg/dl in men, <50 mg/dl in women), or on medication for treating the condition High blood pressure (=130 mmHg systolic or =85mmHg diastolic), or on medication for treating the condition Elevated fasting glucose (=100 mg/dl), or on medication for treating the condition", "candidate_expression": "((<40mg/dl) AND (<50 mg/dl) AND (=100 mg/dl) AND (=102 cm) AND (=130 mmHg systolic) AND (=150 mg/dl) AND (=85mmHg diastolic) AND (=88 cm) AND (> 60 min/wk) AND (>27 and <47 kg/m2) AND (>40 and <70 years) AND (Elevated) AND (Elevated fasting glucose) AND (HDL-cholesterol) AND (High) AND (High blood pressure) AND (Increased) AND (Male) AND (National Cholesterol Education Adult Treatment Panel III) AND (Not) AND (Reduced) AND (Type 2 diabetes) AND (at least 3 of 5) AND (blood pressure) AND (body mass index) AND (currently) AND (engaged in exercise) AND (fasting glucose) AND (female) AND (medication for treating) AND (men) AND (old) AND (triglycerides) AND (waist circumference) AND (women))"}
{"candidate_id": "LLM00784", "doc_id": "NCT03120728_inc", "case_bucket": "or", "source_criterion": "Healthy, women ages 18 to 39yo with BMI <30 Regular menstrual cycles with duration between 24-35 days Completion of screening visit where ovulation will be assessed with blood draw for progesterone level (must be 5ng/mL or greater) Not seeking pregnancy during the study period Use of a non-hormonal form of contraception, such as: sterilization (tubal ligation, Essure), copper IUD (intrauterine device), barrier methods or abstinence Must speak English or Spanish", "candidate_expression": "((18 to 39yo) AND (5ng/mL or greater) AND (<30) AND (BMI) AND (Healthy) AND (Not seeking pregnancy during the study period) AND (Regular menstrual cycles) AND (ages) AND (between 24-35 days) AND (duration) AND (intrauterine device) AND (non-hormonal form of contraception) AND (progesterone level) AND (women) AND ((Essure) OR (tubal ligation)) AND ((abstinence) OR (barrier methods) OR (copper IUD) OR (sterilization)))"}
{"candidate_id": "LLM00785", "doc_id": "NCT03225469_exc", "case_bucket": "or", "source_criterion": "1. History of colorectal surgery 2. Suspected or known digestive tract obstruction, stricture, or perforation 3. Serious status of illness, such as severe renal failure whose creatinine clearance<30 ml/min, New York Heart Association grade III or grade IV congestive heart failure, or hemodynamic instability, etc. 4. Incapable of completing bowel preparation，such as dysphagia, allergy to purgatives, or impaired mental status, etc. 5. Pregnancy or breastfeeding 6. Incomplete colonoscopy due to causes except poor bowel preparation 7. Unable to give informed consent 8. Have participated in the study before.", "candidate_expression": "((<30 ml/min) AND (History) AND (Incapable of completing bowel preparation) AND (Incomplete) AND (New York Heart Association) AND (Serious status of illness) AND (colonoscopy) AND (colorectal surgery) AND (creatinine clearance) AND (except) AND (grade III or grade IV) AND (informed consent) AND (poor bowel preparation) AND (purgatives) AND (severe) AND ((congestive heart failure) OR (hemodynamic instability) OR (renal failure)) AND ((allergy) OR (dysphagia) OR (impaired mental status)) AND ((Pregnancy) OR (breastfeeding)) AND ((digestive tract obstruction) OR (digestive tract perforation) OR (digestive tract stricture)))"}
{"candidate_id": "LLM00786", "doc_id": "NCT03066440_exc", "case_bucket": "or", "source_criterion": "Age > 18 Years Physician discretion Septic or hypovolemic shock Signs of life-threatening cerebral edema or multi-organ failure upon presentation to the emergency room or pediatric intensive care unit Enrollment time more than 1 hr since arrival to emergency room or PICU Pregnancy", "candidate_expression": "((> 18 Years) AND (Age) AND (Enrollment) AND (PICU) AND (Pregnancy) AND (Septic shock) AND (Signs of) AND (arrival to emergency room or PICU) AND (cerebral edema) AND (emergency room) AND (hypovolemic shock) AND (life-threatening) AND (more than 1 hr since arrival to emergency room or PICU) AND (multi-organ failure) AND (pediatric intensive care unit) AND (presentation to the emergency room or pediatric intensive care unit) AND (upon presentation to the emergency room or pediatric intensive care unit))"}
{"candidate_id": "LLM00787", "doc_id": "NCT02042287_inc", "case_bucket": "other", "source_criterion": "> 18 years old Acute symptomatic BV Signed informed consent Insufficient knowledge of German Illiteracy Pregnancy Acute illness Known allergies against ingredients of the investigational products", "candidate_expression": "((18 years) AND (Acute) AND (Acute illness) AND (BV) AND (Illiteracy) AND (Insufficient knowledge of German) AND (Pregnancy) AND (Signed informed consent) AND (allergies) AND (ingredients of the investigational products) AND (old) AND (symptomatic))"}
{"candidate_id": "LLM00788", "doc_id": "NCT03164304_exc", "case_bucket": "or", "source_criterion": "Women with Non-proteinuric hypertension severe renal impairment Myasthenia gravis High amount of magnesium in blood Low or high amount of calcium in blood Myocardial damage, diabetic coma, heart block", "candidate_expression": "((High amount) AND (Myasthenia gravis) AND (Non-proteinuric hypertension) AND (Women) AND (calcium in blood) AND (magnesium in blood) AND (renal impairment) AND (severe) AND ((Myocardial damage) OR (diabetic coma) OR (heart block)) AND ((Low amount) OR (high amount)))"}
{"candidate_id": "LLM00789", "doc_id": "NCT03120728_exc", "case_bucket": "or", "source_criterion": "Currently pregnant or breastfeeding Severe pelvic organ prolapse or prolapse to any degree that may prevent retention of the vaginal ring after insertion Use of oral contraceptive pills, patches, implants or hormonal intrauterine contraception in the month prior to screening Use of depo medroxyprogesterone within 6 months of screening Use of medications that interact with contraceptive steroid hormones: anti-epileptic medications, rifampin, rifabutin, fosamprenavir, etc Medical condition with safety deemed to be category 3 or 4 when using a combined hormonal contraceptive, as determined by the Center for Disease Control Medical Eligibility Criteria: current or past history of breast cancer, severe decompensated cirrhosis, history of deep vein thrombosis or pulmonary embolus, diabetes with nephropathy/retinopathy/neuropathy or other vascular disease diagnosed more than 20 years ago, current symptomatic gallbladder disease, hypertension, ischemic heart disease, known thrombogenic mutations, hepatocellular adenoma, malignant hepatoma, multiple risk factors for atherosclerotic cardiovascular disease, multiple sclerosis with prolonged immobility, history of peripartum cardiomyopathy, cigarette smoking and =35yo, history of complicated solid organ transplant, history of stroke, history of superficial venous thrombosis not associated with catheter, systemic lupus erythematosus with positive antiphospholipid antibodies, valvular heart disease complicated by pulmonary hypertension or atrial fibrillation or bacterial endocarditis, and acute viral hepatitis", "candidate_expression": "((Center for Disease Control Medical Eligibility Criteria) AND (Medical condition) AND (antiphospholipid antibodies positive) AND (breast cancer history) AND (catheter) AND (cigarette smoking) AND (cirrhosis severe decompensated) AND (combined hormonal contraceptive) AND (contraceptive steroid hormones) AND (deep vein thrombosis) AND (depo medroxyprogesterone within 6 months of screening) AND (diabetes) AND (history) AND (medications interact with) AND (prolonged immobility) AND (pulmonary embolus) AND (safety category 3 or 4) AND (valvular heart disease) AND (yo =35yo) AND ((hormonal intrauterine contraception) OR (implants) OR (oral contraceptive pills) OR (patches)) AND ((anti-epileptic medications) OR (fosamprenavir) OR (rifabutin) OR (rifampin)) AND ((current) OR (past)) AND ((breastfeeding) OR (pregnant)) AND ((nephropathy) OR (neuropathy) OR (other) OR (retinopathy) OR (vascular disease)) AND ((gallbladder disease) OR (hypertension) OR (ischemic heart disease)) AND ((pelvic organ prolapse) OR (prolapse)) AND ((atrial fibrillation) OR (bacterial endocarditis) OR (pulmonary hypertension)) AND ((acute viral hepatitis) OR (atherosclerotic cardiovascular disease risk factors) OR (complicated solid organ transplant history) OR (hepatocellular adenoma) OR (malignant hepatoma) OR (multiple sclerosis) OR (peripartum cardiomyopathy history) OR (stroke history) OR (superficial venous thrombosis history not associated) OR (systemic lupus erythematosus) OR (thrombogenic mutations)))"}
{"candidate_id": "LLM00790", "doc_id": "NCT02958072_exc", "case_bucket": "or", "source_criterion": "Hemoglobin concentration under 6.5 mmol/l screening HBA1c more than 108 mmol/l Non-compliant with blood-letting Clinically infected ulcer Patient planned for or has had a revascularization procedure in the affected leg within the last 8 weeks The ulcer have been treated with growth factors in the last 8 weeks History of deep venous insufficiency, chronic venous leg ulcer or stasis dermatitis Breast-feeding women or fertile women not agreeing to use an effective method of contraception Participation in another clinical ulcer-healing study within the last 4 weeks Patient has previously been randomized in this study Judgement by the investigator that the patient is not able to participate in the study", "candidate_expression": "((Breast-feeding) AND (HBA1c) AND (Hemoglobin concentration) AND (History) AND (Judgement by the investigator that the patient is not able to participate in the study) AND (Non-compliant) AND (affected leg) AND (agreeing to use an effective method of contraception) AND (blood-letting) AND (fertile) AND (growth factors) AND (in the last 8 weeks) AND (infected ulcer) AND (more than 108 mmol/l) AND (not) AND (revascularization procedure) AND (treated) AND (ulcer) AND (under 6.5 mmol/l) AND (within the last 8 weeks) AND ((has had) OR (planned)) AND ((chronic venous leg ulcer) OR (deep venous insufficiency) OR (stasis dermatitis)) AND ((women)))"}
{"candidate_id": "LLM00791", "doc_id": "NCT02552459_inc", "case_bucket": "other", "source_criterion": "patients undergoing venous malformation embolization operation through general anesthesia. aged 18-65 years old. operating time varies 1-4h,and extubation after the operation.", "candidate_expression": "((1-4h) AND (18-65 years old) AND (after the operation) AND (aged) AND (extubation) AND (general anesthesia) AND (operating time) AND (operation) AND (the operation) AND (venous malformation embolization operation))"}
{"candidate_id": "LLM00792", "doc_id": "NCT02654912_inc", "case_bucket": "other", "source_criterion": "anyone not excluded and consenting", "candidate_expression": "(anyone not excluded and consenting)"}
{"candidate_id": "LLM00793", "doc_id": "NCT03004261_exc", "case_bucket": "or", "source_criterion": "Patients receiving prednisone = 1mg/kg/d for the treatment of acute GVHD or mild, severe chronic GVHD. Recipient < 14years of age Donor is sero-positive in HBV/HCV/HIV or RPR.", "candidate_expression": "((< 14years) AND (= 1mg/kg/d) AND (GVHD) AND (acute GVHD) AND (age) AND (chronic) AND (mild) AND (prednisone) AND (sero-positive in HBV) AND (sero-positive in HCV) AND (sero-positive in HIV) AND (sero-positive in RPR) AND (severe))"}
{"candidate_id": "LLM00794", "doc_id": "NCT02777580_inc", "case_bucket": "other", "source_criterion": "Age equal or greater than 70 years Onset of symptoms < 3 hours prior to randomisation = 2 mm ST-elevation across 2 contiguous precordial leads (V1-V6) or leads I and aVL for a minimum combined total of = 4 mm ST-elevation or = 2 mm ST-elevation in 2 contiguous inferior leads (II, III, aVF) for a minimum combined total of = 4 mm ST-elevation Informed consent received", "candidate_expression": "((< 3 hours prior to randomisation) AND (Age) AND (Informed consent received) AND (Onset of symptoms) AND (equal or greater than 70 years) AND (randomisation))"}
{"candidate_id": "LLM00795", "doc_id": "NCT03382106_inc", "case_bucket": "other", "source_criterion": "Between the age of 25 to 65 at baseline Be willing to participate in a smoking cessation program Be willing to attend all clinic visits Must be currently smoking at least ½ pack/day at baseline (confirmed with cotinine level and CO Smokerlyzer >5 pack-year history of smoking Global Initiative for Chronic Obstructive Lung Disease (GOLD) 0: FEV1=0.80 and FEV1/FVC>0.70 Forced Expiratory Volume in 1 second (FEV1), Forced Vital Capacity (FVC) GOLD 1: FEV1=0.80 and FEV1/FVC < 0.70 GOLD 2: 0.50=FEV1<0.80 and FEV1/FVC < 0.70 Be willing to abstain from using any nicotine patches, e-cigarettes, or marijuana for the duration of the study.", "candidate_expression": "((CO Smokerlyzer) AND (FEV1 0.50= <0.80) AND (FEV1 =0.80) AND (FEV1/FVC < 0.70) AND (FEV1/FVC >0.70) AND (GOLD 1) AND (GOLD 2) AND (Global Initiative for Chronic Obstructive Lung Disease (GOLD) 0) AND (age Between 25 to 65 at baseline) AND (cotinine level) AND (pack-year >5) AND (pack/day at least ½) AND (smoking) AND (smoking at baseline) AND (smoking cessation program willing to participate))"}
{"candidate_id": "LLM00796", "doc_id": "NCT02707809_exc", "case_bucket": "or", "source_criterion": "allergic history to dexmedetomidine refractory bradycardia < 60 bpm despite treatment severe atrioventricular block (2nd and 3rd degree) previous operation of tongue", "candidate_expression": "((allergic history) AND (atrioventricular block severe 2nd degree 3rd degree) AND (bradycardia refractory < 60 bpm despite treatment) AND (dexmedetomidine) AND (operation of tongue previous) AND (treatment))"}
{"candidate_id": "LLM00797", "doc_id": "NCT03623789_exc", "case_bucket": "or", "source_criterion": "Preoperative Hemoglobin <U+2266>11 g/dl History of infection or intraarticular fracture of the affective hip Renal function deficiency (GFR <30 ml/min/1.73m2) Elevated liver enzyme (aspartate transaminase (AST)/ alanine transaminase(ALT) level are more than twice normal range) , history of liver cirrhosis, impaired liver function(elevated total bilirubin level) and coagulopathy (including long-term use anticoagulant) History of deep vein thrombosis, ischemic heart disease or stroke Contraindications of tranexamic acid, floseal, or rivaroxaban Allergy to tranexamic acid, floseal, rivaroxaban, or the excipients History of heparin-induced thrombocytopenia (HIT) Coagulopathy or bleeding tendency caused by organ dysfunction, such as cirrhosis, bone marrow suppression etc. Patient who have active bleeding disorder, such as intracranial hemorrhage, upper gastrointestinal bleeding, hematuria. Patients with known allergies to materials of bovine origin.", "candidate_expression": "((Allergy) AND (Coagulopathy) AND (Contraindications) AND (GFR <30 ml/min/1.73m2) AND (Hemoglobin Preoperative <U+2266>11 g/dl) AND (Renal function deficiency) AND (allergies) AND (anticoagulant long-term use) AND (aspartate transaminase (AST)/ alanine transaminase(ALT) level more than twice normal range) AND (bleeding disorder active) AND (bleeding tendency) AND (bone marrow suppression) AND (cirrhosis) AND (coagulopathy) AND (deep vein thrombosis) AND (excipients) AND (floseal) AND (hematuria) AND (heparin-induced thrombocytopenia (HIT) History) AND (history) AND (impaired liver function) AND (infection) AND (intraarticular fracture) AND (intracranial hemorrhage) AND (ischemic heart disease) AND (liver cirrhosis) AND (liver enzyme Elevated) AND (materials of bovine origin) AND (organ dysfunction) AND (rivaroxaban) AND (stroke) AND (total bilirubin level elevated) AND (tranexamic acid) AND (upper gastrointestinal bleeding))"}
{"candidate_id": "LLM00798", "doc_id": "NCT02432404_exc", "case_bucket": "or", "source_criterion": "Current pregnancy Desire/intent to become pregnant over the course of the study Women who are less than 6 weeks postpartum Contraindications to hormonal contraceptive use per package insert, including history of deep vein thrombosis, smoking in women older than 35 years Current IUD Unable to comprehend consent material because of language barrier or psychological difficulty", "candidate_expression": "((Contraindications to hormonal contraceptive) AND (Desire/intent to become pregnant) AND (IUD) AND (Unable to comprehend consent material because of language barrier or psychological difficulty) AND (Women) AND (deep vein thrombosis) AND (hormonal contraceptive) AND (less than 6 weeks postpartum) AND (older than 35 years) AND (over the course of the study) AND (postpartum) AND (pregnancy) AND (pregnant) AND (smoking) AND (women))"}
{"candidate_id": "LLM00799", "doc_id": "NCT01959061_exc", "case_bucket": "or", "source_criterion": "Pregnant or lactating women Patients with severe organ dysfunction or failure With severe cardiovascular disease, or mental Extraliver metastases", "candidate_expression": "((Extraliver metastases) AND (metastases Extraliver) AND (women) AND ((Pregnant) OR (lactating)) AND ((organ dysfunction) OR (organ failure)) AND ((cardiovascular disease) OR (disease mental)))"}
{"candidate_id": "LLM00800", "doc_id": "NCT03018171_exc", "case_bucket": "or", "source_criterion": "Suspect or certainty of fetal malformation, Presence of conditions such as preeclampsia, multiparity, preterm labor History of adverse reaction to a-2 adrenergic agonists Nicotine addiction Chronic use of opioid", "candidate_expression": "((Chronic use) AND (Nicotine addiction) AND (Suspect) AND (a-2 adrenergic agonists) AND (adverse reaction) AND (certainty) AND (fetal malformation) AND (multiparity) AND (opioi) AND (preeclampsia) AND (preterm labor))"}
```
