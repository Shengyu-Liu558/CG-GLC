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
{"candidate_id": "LLM06201", "doc_id": "NCT02858180_exc", "case_bucket": "or", "source_criterion": "Chronic HCV Infection with Genotype 2 or 3 Amiodarone. Subjects previously treated with amiodarone must have stopped the amiodarone at least 60 days prior to day 1 of SOF/LDV FDC Carbamazepine, phenytoin, phenobarbital, oxcarbazepine Rifabutin, rifampin or rifapentine HIV regimens containing tenofovir or tipranavir/ritonavir St. John's wort Rosuvastatin Have any serious or active medical or psychiatric illness which, in the opinion of the investigator, would interfere with subject treatment, assessment, or compliance History of hepatic encephalopathy or variceal hemorrhage Hepatitis B surface antigen positive Hemoglobin (Hb) < 8 g/dL Platelets = 50,000/mm3 alanine aminotransferase (ALT), aspartase aminotransferase (AST), or alkaline phosphatase = 10 times upper limit of normal(ULN) Total bilirubin > 3 mg/dl Severe renal impairment creatinine clearance (CrCl), i.e. < 30 mL/min. History of major organ transplantation with an existing functional graft. History of clinically-significant drug allergy to nucleoside/nucleotide analogs. Pregnant women or women planning to become pregnant Women who are breastfeeding Active or recent history (= 1 year) of drug or alcohol abuse", "candidate_expression": "((ALT) AND (AST) AND (Amiodarone at least 60 days prior to day 1 of SOF/LDV FDC) AND (Chronic HCV Infection) AND (CrCl) AND (Have any serious or active medical or psychiatric illness which, in the opinion of the investigator, would interfere with subject treatment, assessment, or compliance) AND (Hb) AND (Hemoglobin < 8 g/dL) AND (Hepatitis B surface antigen positive) AND (Platelets = 50,000/mm3) AND (Pregnant women or women planning to become pregnant) AND (Rosuvastatin) AND (St. John's wort) AND (Total bilirubin > 3 mg/dl) AND (Women who are breastfeeding) AND (creatinine clearance < 30 mL/min) AND (drug allergy clinically-significant) AND (major organ transplantation existing functional graft) AND (renal impairment Severe) AND ((Rifabutin) OR (rifampin) OR (rifapentine)) AND ((tenofovir) OR (tipranavir/ritonavir)) AND ((Genotype 2) OR (Genotype 3)) AND ((hepatic encephalopathy) OR (variceal hemorrhage)) AND ((alanine aminotransferase) OR (alkaline phosphatase) OR (aspartase aminotransferase)) AND ((nucleoside) OR (nucleotide analogs)) AND ((alcohol abuse) OR (drug abuse)) AND ((Carbamazepine) OR (oxcarbazepine) OR (phenobarbital) OR (phenytoin)))"}
{"candidate_id": "LLM06202", "doc_id": "NCT02257580_exc", "case_bucket": "or", "source_criterion": "Preoperative use of an anticoagulant (Plavix, warfarin, lovenox, etc.) History of hypersensitivity to EACA History of thromboembolic event (e.g., PE or DVT) History of renal insufficiency or failure Congenital or acquired coagulopathy as evidence by INR >1.4 or PTT > 1.4 times normal, or Platelets <150,000/mm3 on preoperative laboratory testing Use of hormone replacement therapy or hormonal contraceptive agents within days prior to surgery Use of acetylsalicylic acid (ASA), antiplatelet agents within 7 days prior to surgery Pregnant Breastfeeding Not received neuraxial anesthesia", "candidate_expression": "((ASA) AND (Breastfeeding) AND (EACA) AND (Pregnant) AND (anticoagulant Preoperative) AND (hypersensitivity) AND (preoperative laboratory testing) AND (thromboembolic event) AND NOT (neuraxial anesthesia) AND ((DVT) OR (PE)) AND ((renal failure) OR (renal insufficiency)) AND ((Congenital) OR (acquired)) AND ((INR >1.4 times normal) OR (PTT > 1.4 times normal)) AND ((Platelets <150,000/mm3) OR (coagulopathy)) AND ((hormonal contraceptive agents) OR (hormone replacement therapy)) AND ((Plavix) OR (lovenox) OR (warfarin)) AND ((acetylsalicylic acid) OR (antiplatelet agents)))"}
{"candidate_id": "LLM06203", "doc_id": "NCT02312089_inc", "case_bucket": "scope", "source_criterion": "Women subjected to ICSI through controlled ovarian hyperstimulation (COH) with pituitary downregulation by GnRH antagonist.", "candidate_expression": "((COH) AND (GnRH antagonist) AND (ICSI) AND (Women) AND (ovarian hyperstimulation) AND (pituitary downregulation))"}
{"candidate_id": "LLM06204", "doc_id": "NCT03256864_inc", "case_bucket": "other", "source_criterion": "Liver Transplant Recipients have received liver transplantations for at least 6+1 months prior to enrollment Liver Transplant Recipients have no acute rejection episodes within 3 months prior to the enrollment and are clinically stable Liver Transplant Recipients have been treated with twice-daily regimen of tacrolimus(TAC) plus everolimus(EVR) and TAC and EVR trough levels have stayed within targeted ranges for at least 6 weeks prior to enrollment Provide written informed consent prior to inclusion. Liver transplant recipients who are 18-65 years of age of a primary liver transplant Allograft functioning at an acceptable level as defined by the AST, ALT, Total Bilirubin levels =3 times ULN prior to enrollment. Abbreviated MDRD eGFR = 30 mL/min/1.73m2.", "candidate_expression": "((18-65 years) AND (= 30 mL/min/1.73m2) AND (=3 times ULN) AND (ALT) AND (AST) AND (Allograft functioning) AND (EVR trough levels) AND (Liver Transplant Recipients) AND (Liver transplant recipients) AND (MDRD eGFR) AND (TAC trough levels) AND (Total Bilirubin) AND (acceptable level) AND (acute) AND (age) AND (clinically stable) AND (enrollment) AND (everolimus(EVR)) AND (for at least 6 weeks prior to enrollment) AND (for at least 6+1 months prior to enrollment) AND (inclusion) AND (liver transplantations) AND (no) AND (primary liver transplant) AND (prior to enrollment) AND (prior to inclusion) AND (rejection episodes) AND (tacrolimus(TAC)) AND (the enrollment) AND (twice-daily) AND (within 3 months prior to the enrollment) AND (within targeted ranges) AND (written informed consent))"}
{"candidate_id": "LLM06205", "doc_id": "NCT02607748_inc", "case_bucket": "or", "source_criterion": "Acute Coronary Syndrome group: 40 patients with type 1 myocardial infarction within 21 days prior to the imaging visit and invasive coronary angiography with angiographic evidence of at least a 50% stenosis in one or more coronary arteries. Only patients undergoing PCI will be included in the study. Stable Ischemic Heart Disease group: 40 patients who have undergone invasive coronary angiography within 21 days prior to the imaging visit, with history of typical angina prior to the angiogram, but no prior myocardial infarction or coronary revascularization. have no prior CAD associated event (no prior myocardial infarction, acute coronary syndrome, coronary angiogram, or PCI), have CAC between 10 to <1000, and match to patients in the ACS group by gender, age by decile, and CAC category (using CAC categories of 10 to <100, 100 to <400, 400 to <1000).", "candidate_expression": "((Acute Coronary Syndrome) AND (CAC) AND (CAD) AND (PCI) AND (acute coronary syndrome) AND (between 10 to <1000) AND (coronary angiogram) AND (myocardial infarction) AND (no))"}
{"candidate_id": "LLM06206", "doc_id": "NCT02299063_inc", "case_bucket": "other", "source_criterion": "aged between 3 - 36 months having primary corrective heart surgery", "candidate_expression": "((aged) AND (between 3 - 36 months) AND (corrective heart surgery) AND (primary))"}
{"candidate_id": "LLM06207", "doc_id": "NCT02360631_exc", "case_bucket": "or", "source_criterion": "Renal impairment Evidence or history of clinically significant allergic reactions to varenicline A cardiovascular event in the past month History of alcohol or drug dependence in the past year Major depressive disorder in the last year requiring treatment History of panic disorder, psychosis, bipolar disorder, or eating disorders Use of tobacco products other than cigarettes in past 30 days Use of pharmacotherapy in the month prior to enrollment, including prior use of varenicline Pregnant, contemplating getting pregnant, or breastfeeding Plans to move from Kansas City during the treatment and follow-up phase Another household member enrolled in the study Evidence of current severe major depressive disorder or suicidal ideation", "candidate_expression": "((Major depressive disorder last year) AND (Pregnant, contemplating getting pregnant, or breastfeeding) AND (Renal impairment) AND (Use of tobacco past 30 days) AND (alcohol dependence) AND (allergic) AND (bipolar disorder) AND (cardiovascular event in the past month) AND (drug dependence) AND (eating disorders) AND (major depressive disorder severe) AND (other than cigarettes) AND (panic disorder) AND (pharmacotherapy month prior to enrollment) AND (psychosis) AND (suicidal ideation) AND (treatment) AND (varenicline))"}
{"candidate_id": "LLM06208", "doc_id": "NCT00785213_inc", "case_bucket": "or", "source_criterion": "Healthy adults 18-45 years of age Non-smoking Non-pregnant (post-menopausal, surgically sterile or using effective contraceptive measures) Body mass index (BMI) less than or equal to 32 Medically healthy on the basis of medical history and physical examination Hemoglobin > or = to 11.5g/dL Completion of the screening process within 28 days prior to dosing Provision of voluntary written informed consent", "candidate_expression": "((Body mass index (BMI) less than or equal to 32) AND (Healthy) AND (Hemoglobin > or = to 11.5g/dL) AND (Medically healthy) AND (Provision of voluntary written informed consent) AND (adults) AND (medical history) AND (of age 18-45 years of age) AND (physical examination) AND (screening process within 28 days prior to dosing) AND (surgically) AND NOT (smoking) AND NOT (pregnant) AND ((contraceptive measures effective) OR (post-menopausal) OR (surgically sterile)))"}
{"candidate_id": "LLM06209", "doc_id": "NCT02042287_exc", "case_bucket": "other", "source_criterion": "NA", "candidate_expression": "(EMPTY)"}
{"candidate_id": "LLM06210", "doc_id": "NCT02553226_inc", "case_bucket": "other", "source_criterion": "Women stimulated with Syntocinon® infusion for induction of labour (with or without cervical priming by prostaglandin)", "candidate_expression": "((Syntocinon®) AND (Syntocinon® infusion) AND (Women) AND (cervical priming) AND (induction of labour) AND (prostaglandin))"}
{"candidate_id": "LLM06211", "doc_id": "NCT03077204_inc", "case_bucket": "or", "source_criterion": "Age>18 years Scheduled 1 or 2-level ACDF spine surgery The capacity to provide informed consent. Degenerative Disc Disease (as defined by neck pain of discogenic origin with degeneration of the disc confirmed by patient history and radiographic studies) Trauma (including fractures) Tumors Deformities or curvatures (including kyphosis, lordosis, or scoliosis) Pseudoarthrosis Failed previous fusion Decompression of the spinal cord following total or partial cervical vertebrectomy Spondylolisthesis Spinal stenosis Patients with current or recent history of malignancy or infectious disease. The inability to provide informed consent. Subject has marked local inflammation Subject has any mental or neuromuscular disorder which would create an unacceptable risk of fixation failure or complications in postoperative care. Subject has a bone stock compromised by disease, infection or prior implantation which cannot provide adequate support and/or fixation to the devices. Subject has bone abnormalities preventing safe screw fixation. Subject has any open wounds. Subject has rapid joint disease, bone absorption, osteopenia, osteomalacia, and/or osteoporosis. Osteoporosis or osteopenia are relative contraindications, since this condition may limit the degree of obtainable correction and/or the amount of mechanical fixation. Subject has a documented or suspected metal sensitivity. Subject is pregnant. Subject has anatomical structures or physiological performance that would interfere with implant utilization. Subject has inadequate tissue coverage over the operative site. Subject has other medical or surgical conditions which would preclude the potential benefit of surgery, such as congenital abnormalities, immunosuppressive disease, elevation of sedimentation rate unexplained by other diseases, elevation of white blood count (WBC), or marked left shift in the WBC differential count. Note: The Aviator Anterior Cervical Plating System is not approved or intended for screw attachment to the posterior elements (pedicles) of the cervical, thoracic, or lumbar spine. The surgeon must consider the levels of implantation, patient weight, patient activity level, and other patient conditions which may impact on the performance of the system.", "candidate_expression": "((ACDF spine surgery) AND (Age >18 years 1 -level 2-level) AND (Decompression of the spinal cord) AND (Deformities) AND (Degenerative Disc Disease) AND (Osteoporosis) AND (Pseudoarthrosis) AND (Spinal stenosis current) AND (Spondylolisthesis) AND (Trauma) AND (Tumors) AND (WBC differential count left shift) AND (adequate support) AND (anatomical structures) AND (bone abnormalities) AND (bone absorption) AND (bone stock compromised) AND (cannot) AND (complications) AND (congenital abnormalities) AND (contraindications relative) AND (curvatures) AND (degeneration of the disc patient history) AND (disease) AND (fixation failure) AND (fixation to the devices) AND (fractures) AND (fusion Failed previous) AND (history recent) AND (immunosuppressive disease) AND (implant) AND (implantation prior) AND (inadequate tissue coverage operative site) AND (infection) AND (infectious disease) AND (kyphosis) AND (local inflammation marked) AND (lordosis) AND (malignancy) AND (medical conditions) AND (mental disorder) AND (metal documented suspected) AND (neck pain discogenic origin) AND (neuromuscular disorder) AND (open wounds) AND (osteomalacia) AND (osteopenia) AND (osteoporosis) AND (partial cervical vertebrectomy) AND (physiological performance) AND (preclude) AND (pregnant) AND (radiographic studies) AND (rapid joint disease) AND (scoliosis) AND (sedimentation rate elevation unexplained by other diseases) AND (sensitivity) AND (surgery) AND (surgical conditions) AND (total cervical vertebrectomy) AND (white blood count (WBC) elevation) AND NOT (screw fixation safe))"}
{"candidate_id": "LLM06212", "doc_id": "NCT02934269_inc", "case_bucket": "or", "source_criterion": "Healthy male and/or female subjects between the ages of 18 and 55 years, and a body mass index (BMI) of ≥ 18 and ≤ 33 kg/m2 with body weight ≥ 50 and ≤ 90 kg at screening. Females must have been surgically sterilized (hysterectomy, bilateral oophorectomy, or bilateral salpingo-oophorectomy; proper documentation required) at least 6 months before screening, or be postmenopausal (defined as 24 consecutive months without menses before screening, with a follicle-stimulating hormone [FSH] level of > 40 IU/L at screening).", "candidate_expression": "((Females) AND (Healthy) AND (ages between 18 and 55 years) AND (body mass index (BMI) ≥ 18 and ≤ 33 kg/m2) AND (body weight ≥ 50 and ≤ 90 kg) AND (follicle-stimulating hormone [FSH] > 40 IU/L at screening) AND NOT (menses 24 consecutive months before screening) AND ((bilateral oophorectomy) OR (bilateral salpingo-oophorectomy) OR (hysterectomy)) AND ((postmenopausal) OR (surgically sterilized at least 6 months before)) AND ((female) OR (male)))"}
{"candidate_id": "LLM06213", "doc_id": "NCT02560389_exc", "case_bucket": "or", "source_criterion": "Claustrophobia, or the inability to lie still in a confined space Major medical disorders (e.g., HIV, cancer) Magnetic metallic implants (such as screws, pins, shrapnel remnants, aneurysm clips, artificial heart valves, inner ear (cochlear) implants, artificial joints, and vascular stents) Electronic or magnetic implants, such as pacemakers Permanent makeup or tattoos with metallic dyes Currently pregnant A self-reported history of loss of consciousness (greater than 10 minutes) Physical disabilities that prohibit task performance (such as blindness or deafness) Psychotic disorders (e.g., schizophrenia) Any other condition that the investigator believes might put the participant at risk", "candidate_expression": "((Any other condition that the investigator believes might put the participant at risk) AND (Claustrophobia) AND (Electronic implants) AND (HIV) AND (Magnetic metallic implants) AND (Permanent makeup) AND (Physical disabilities that prohibit task performance) AND (Psychotic disorders) AND (aneurysm clips) AND (artificial heart valves) AND (artificial joints) AND (blindness) AND (cancer) AND (cochlear implants) AND (deafness) AND (history of loss of consciousness self-reported greater than 10 minutes) AND (inability to lie still in a confined space) AND (inner ear implants) AND (magnetic implants) AND (medical disorders Major) AND (metallic dyes) AND (pacemakers) AND (pins) AND (pregnant) AND (schizophrenia) AND (screws) AND (shrapnel remnants) AND (tattoos) AND (vascular stents))"}
{"candidate_id": "LLM06214", "doc_id": "NCT03122119_inc", "case_bucket": "other", "source_criterion": "Diagnosis of sacroiliitis Age 18 to 80 years old Chronic low back pain SI joint pathology is the predominant source of pain Positive Fortin Finger Test (PMT) Joint anatomy is identifiable using ultrasonography Patient has no other comorbidities that contraindicate the procedure Patient has attempted physical therapy and corticosteroid injections with local anesthetic -Previous injections of lidocaine and corticosteroid provided at least minor immediate relief Patient must not have had a corticosteroid injection in the SI joint within the last three months Patient must consent to the procedure", "candidate_expression": "((Age 18 to 80 years) AND (Chronic low back pain) AND (Fortin Finger Test (PMT) Positive) AND (SI joint pathology) AND (consent to the procedure) AND (corticosteroid injections) AND (ocal anesthetic) AND (physical therapy) AND (sacroiliitis) AND NOT (comorbidities that contraindicate the procedure other) AND NOT (corticosteroid injection SI joint within the last three months))"}
{"candidate_id": "LLM06215", "doc_id": "NCT03168555_inc", "case_bucket": "other", "source_criterion": "planned elective cholecystectomy", "candidate_expression": "(cholecystectomy planned elective)"}
{"candidate_id": "LLM06216", "doc_id": "NCT02668978_exc", "case_bucket": "or", "source_criterion": "Traumatic pulmonary contusion or laceration Lung reduction surgery Planned removal of more than 10 lung lesions Pneumonectomy Known hypersensitivity to bovine protein Known hypersensitivity to Brilliant Blue FCF (E133) Presence of active infection", "candidate_expression": "((Brilliant Blue FCF (E133)) AND (Lung reduction surgery Planned) AND (Pneumonectomy) AND (active infection) AND (bovine protein) AND (hypersensitivity) AND (laceration) AND (lung lesions more than 10) AND (pulmonary contusion) AND (removal))"}
{"candidate_id": "LLM06217", "doc_id": "NCT03471117_inc", "case_bucket": "or", "source_criterion": "CKD patients classified as Stage 3 and 4 of National Kidney Foundation Classification with estimated glomerular filtration rate (GFR) between 15 and 59 mL/min/1.73 m2 according to the Modification of Diet in Renal Disease (MDRD) formula based on serum creatinine, age, gender, and race. Men and women 35 to 70 years of age", "candidate_expression": "((35 to 70 years) AND (CKD) AND (Modification of Diet in Renal Disease (MDRD) formula) AND (National Kidney Foundation Classification) AND (age) AND (between 15 and 59 mL/min/1.73 m2) AND (estimated glomerular filtration rate (GFR)) AND ((Stage 3) OR (Stage 4)) AND ((Men) OR (women)))"}
{"candidate_id": "LLM06218", "doc_id": "NCT02077556_inc", "case_bucket": "other", "source_criterion": "De novo kidney transplants 20 - 65 years old aspartate aminotransferase/alanine aminotransferase within 2 times the upper limit of normal range", "candidate_expression": "((20 - 65 years) AND (De novo) AND (alanine aminotransferase) AND (aspartate aminotransferase) AND (kidney transplants) AND (old) AND (within 2 times the upper limit of normal range))"}
{"candidate_id": "LLM06219", "doc_id": "NCT03059069_inc", "case_bucket": "other", "source_criterion": "Type 2 diabetic patients Age = 50 Glycemic control: HbA1c = 10.0% 10 = Beck Depression Inventory (BDI) <30 points Participants who can undergo contraception in case of being in childbearing period Understands the study procedure, alternatives, and risks and voluntarily agrees to participate by giving written informed concent", "candidate_expression": "((<30 points) AND (= 10.0%) AND (= 50) AND (Age) AND (Beck Depression Inventory (BDI)) AND (HbA1c) AND (Participants who can undergo contraception in case of being in childbearing period) AND (Type 2 diabetic) AND (Understands the study procedure, alternatives, and risks and voluntarily agrees to participate by giving written informed concent))"}
{"candidate_id": "LLM06220", "doc_id": "NCT01352598_inc", "case_bucket": "or", "source_criterion": "Patient age >= 18 years Zubrod performance status of 0-3 T1-3 N0 M0 adenocarcinoma of the prostate Prostate volume = 100 cc Signed study-specific consent form Extension of local tumor to involve adjacent organs other than seminal vesicles (T4) Prostate volume > 100 cc Nodal involvement Metastatic disease Prior pelvic radiotherapy except as part of combination therapy for prostate cancer History of scleroderma Patients with psychiatric or addictive disorder that would preclude obtaining informed consent", "candidate_expression": "((Extension of local tumor adjacent organs) AND (M 0) AND (Metastatic disease) AND (N 0) AND (Nodal involvement) AND (Patient age >= 18 years) AND (Prostate volume = 100 cc) AND (Prostate volume > 100 cc seminal vesicles) AND (Signed study-specific consent form) AND (T 1-3) AND (Zubrod performance status 0-3) AND (adenocarcinoma prostate) AND (prostate cancer) AND (radiotherapy Prior pelvic) AND (scleroderma History) AND NOT (combination therapy) AND ((addictive disorder) OR (psychiatric disorder)))"}
{"candidate_id": "LLM06221", "doc_id": "NCT01401335_exc", "case_bucket": "or", "source_criterion": "Age less than 15 or greater than 25 and not participating in the day care center", "candidate_expression": "((Age) AND (not) AND (participating in the day care center) AND ((greater than 25) OR (less than 15)))"}
{"candidate_id": "LLM06222", "doc_id": "NCT03151603_inc", "case_bucket": "or", "source_criterion": "Women (18-75 years) with suspected UTI at least two symptoms of UTI (dysuria, urgency of micturition, frequency, lower abdominal pain) Written informed consent", "candidate_expression": "((18-75) AND (UTI) AND (Women) AND (Written informed consent) AND (at least two) AND (dysuria) AND (frequency) AND (lower abdominal pain) AND (suspected) AND (symptoms of UTI) AND (urgency of micturition) AND (years))"}
{"candidate_id": "LLM06223", "doc_id": "NCT01501201_exc", "case_bucket": "other", "source_criterion": "Contraindication to bariatric surgery Pregnancy Affiliation of health care assurance Psychiatric disorders", "candidate_expression": "((Affiliation of health care assurance) AND (Contraindication) AND (Pregnancy) AND (Psychiatric disorders) AND (bariatric surgery))"}
{"candidate_id": "LLM06224", "doc_id": "NCT02413970_inc", "case_bucket": "or", "source_criterion": "Likely suffer moderate-to-severe OSA based on history and physical or have an established diagnosis of OSA (20=AHI=65) based on a prior in-lab Polysomnography Documentation the subject not effectively treated with CPAP therapy. (Examples include non-compliance, discomfort, undesirable side effects, symptoms persist despite use). Subjects who have been prescribed, but refuse to try CPAP would be considered intolerant. Age 22 or above Willing and capable to have stimulation hardware permanently implanted, and to use the patient remote to activate the stimulation Willing and capable to return for all follow-up visits and conduct sleep studies at home, including the evaluation procedures and filling out questionnaires Willing and capable of providing informed consent", "candidate_expression": "((AHI 20 =65) AND (Age 22 or above) AND (Willing and capable of providing informed consent) AND (Willing and capable to have stimulation hardware permanently implanted, and to use the patient remote to activate the stimulation) AND (Willing and capable to return for all follow-up visits and conduct sleep studies at home, including the evaluation procedures and filling out questionnaires) AND NOT (CPAP therapy) AND ((OSA)) AND ((moderate) OR (severe)))"}
{"candidate_id": "LLM06225", "doc_id": "NCT00904202_inc", "case_bucket": "or", "source_criterion": "1. Had a diagnosis of PHN, DN, CRPS, carpal tunnel syndrome, HIV neuropathy, idiopathic sensory neuropathy, or other peripheral neuropathy (upon mutual agreement of the sponsor and investigator) 2. Patients with PHN must have had pain >3 months after rash healing 3. Patients with DN must have had Type I or II diabetes and painful distal symmetric sensorimotor polyneuropathy with or without dynamic allodynia of the lower extremities 4. Patients with CRPS must have met current IASP (International Association for the Study of Pain) diagnostic criteria 5. Patients with carpal tunnel syndrome must have had a diagnosis by combination clinical neurological examination (e.g., Phalen's and Tinel's signs), electrodiagnostic testing, and daily painful symptoms of at least 3 months' duration 6. Patients with HIV neuropathy must have had HIV, subjective symptoms of painful peripheral neuropathy, and daily painful symptoms of at least 3 months' duration 7. Patients with idiopathic sensory neuropathy must have had pain of at least 3 months' duration 8. Reached an average daily pain rating during the baseline week of pain ratings greater than 4 on the 0-to-10 numerical pain rating scale (Question 5 of the BPI) 9. Had never received an analgesic regimen that contained lidocaine or gabapentin", "candidate_expression": "((0-to-10 numerical pain rating scale) AND (CRPS) AND (DN) AND (HIV) AND (HIV neuropathy) AND (IASP (International Association for the Study of Pain) diagnostic criteria met) AND (PHN) AND (Phalen's signs) AND (Tinel's signs) AND (Type I diabetes) AND (Type II diabetes) AND (analgesic regimen) AND (carpal tunnel syndrome) AND (clinical neurological examination) AND (daily pain rating average during the baseline week greater than 4 baseline week) AND (dynamic allodynia) AND (electrodiagnostic) AND (gabapentin) AND (idiopathic sensory neuropathy) AND (lidocaine) AND (neuropathy) AND (pain >3 months after rash healing) AND (pain at least 3 months' duration) AND (painful symptoms daily at least 3 months' duration) AND (peripheral neuropathy) AND (peripheral neuropathy painful) AND (rash healing rash healing) AND (sensorimotor polyneuropathy painful distal symmetric) AND (sensory neuropathy idiopathic) AND (subjective symptoms) AND (upon mutual agreement of the sponsor and investigator))"}
```
