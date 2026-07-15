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
{"candidate_id": "LLM04626", "doc_id": "NCT03106389_inc", "case_bucket": "other", "source_criterion": "NA", "candidate_expression": "(EMPTY)"}
{"candidate_id": "LLM04627", "doc_id": "NCT03025620_inc", "case_bucket": "or", "source_criterion": "Elderly patients over 65 years old exhibiting clinical indices of cardiovascular disease Male or female Subjects who were hospitalized in the Geriatric Unit of the Emile Roux Hospital (AP-HP) MMSE (Mini Mental State Examination)score > or = 15 Supervision available for study medication Able to ingest oral diet", "candidate_expression": "((Able to ingest oral diet) AND (Elderly) AND (Geriatric Unit of the Emile Roux Hospital (AP-HP)) AND (MMSE (Mini Mental State Examination)) AND (old) AND (over 65 years) AND (score > or = 15) AND ((Male) OR (female)))"}
{"candidate_id": "LLM04628", "doc_id": "NCT01700790_exc", "case_bucket": "or", "source_criterion": "Non-compliance with DOTPlus. Alternatively DOT can be done by telephoning patient on a daily basis 5 times a week and having patient annotate taking drug in a log which would be reviewed by clinic staff History of being treated for tuberculosis in the prior 2 years unless there is DST, including PCR testing, showing sensitivity to rifamycin. Known hypersensitivity to rifampin or rifabutin. Liver enzymes greater than 2 times ULN. Bilirubin greater than 2 times ULN. Serum creatinine greater than 3 times ULN. Hemoglobin less than 7.0 gms even if receiving erythropoietin. Absolute neutrophil count less than 750 cells/mm3 even if receiving G-CSF. Fasting triglycerides greater than 400 mg/dL. Fasting cholesterol > 1.6 upper limits of normal. GI intolerance of tuberculosis medications requiring discontinuation of tuberculosis medications. Fasting glucose greater 150 mg/dL. Pregnant women. Use of one of the prohibited medications Any condition that the investigators feel could compromise the use of the current medication. Have a CD4 cell count of 50 cells/mm3or less Hepatitis B or C infection Alcohol or illicit drug use, which in the investigators opinion may affect participation in study.", "candidate_expression": "((50 cells/mm3or less) AND (> 1.6 upper limits of normal) AND (Absolute neutrophil count) AND (Alcohol use) AND (Any condition that the investigators feel could compromise the use of the current medication.) AND (Bilirubin) AND (CD4 cell count) AND (DOTPlus) AND (DST) AND (Fasting cholesterol) AND (Fasting glucose) AND (Fasting triglycerides) AND (GI intolerance) AND (Hemoglobin) AND (Hepatitis B) AND (Hepatitis C) AND (Liver enzymes) AND (Non-compliance) AND (PCR testing) AND (Pregnant) AND (Serum creatinine) AND (Use of one of the prohibited medications) AND (discontinuation) AND (even if receiving G-CSF) AND (even if receiving erythropoietin) AND (greater 150 mg/dL) AND (greater than 2 times ULN) AND (greater than 3 times ULN) AND (greater than 400 mg/dL) AND (hypersensitivity) AND (illicit drug use) AND (in the prior 2 years) AND (less than 7.0 gms) AND (less than 750 cells/mm3) AND (rifabutin) AND (rifampin) AND (rifamycin) AND (sensitivity) AND (treated) AND (tuberculosis) AND (tuberculosis medications) AND (women))"}
{"candidate_id": "LLM04629", "doc_id": "NCT03117608_exc", "case_bucket": "or", "source_criterion": "Patients incapable to understanding and will; Patients participating in previous, concurrent or not, trials (ongoing or completed within three months); Patients surgically treated for the same defect within one year; Patients affected by malignancy; Patients affected by metabolic or thyroid disorders; Patients used to alcohol or drug (medication) abuse; Patients affected by synovitis; Varus or valgus misalignment exceeding 15°; Body Mass Index > 40; Patients with trauma within 6 months pre-operative.", "candidate_expression": "((Body Mass Index > 40) AND (drug abuse) AND (malignancy) AND (operative) AND (surgically treated within one year) AND (synovitis) AND (the same defect) AND (trauma within 6 months pre-operative) AND (trials participating in previous) AND ((incapable to understanding) OR (will incapable to)) AND ((metabolic disorders) OR (thyroid disorders)) AND ((alcohol abuse) OR (medication abuse)) AND ((Varus misalignment) OR (Varus misalignment exceeding 15°) OR (valgus misalignment) OR (valgus misalignment exceeding 15°)) AND ((completed within three months) OR (ongoing)))"}
{"candidate_id": "LLM04630", "doc_id": "NCT03275584_exc", "case_bucket": "or", "source_criterion": "Pregnant women Claustrophobic patient unable to undergo the examination Breastfeeding women unwilling to temporarily stop breastfeeding Patient with contra-indication to: dipyridamole, aminophylline, dobutamine or exercise stress test (depending on the method of cardiovascular stress test chosen)", "candidate_expression": "((Claustrophobic) AND (Pregnant) AND (aminophylline) AND (contra-indication) AND (dipyridamole) AND (dobutamine) AND (examination) AND (exercise stress test) AND (unable) AND (women))"}
{"candidate_id": "LLM04631", "doc_id": "NCT02467686_exc", "case_bucket": "or", "source_criterion": "Women did not have breast cancer do not use tamoxifen or aromatase inhibitor not in menopause and not have hot flashes", "candidate_expression": "((aromatase inhibitor) AND (tamoxifen) AND NOT (hot flashes) AND NOT (breast cancer) AND NOT (menopause))"}
{"candidate_id": "LLM04632", "doc_id": "NCT03088904_inc", "case_bucket": "other", "source_criterion": "NA", "candidate_expression": "(EMPTY)"}
{"candidate_id": "LLM04633", "doc_id": "NCT03138577_inc", "case_bucket": "other", "source_criterion": "Undergoing right upper extremity surgery with supraclavicular block as the primary anesthetic Age greater than or equal to 18 years of age American Society of Anesthesiologists (ASA) physical status 1 to 3 Able to give informed consent", "candidate_expression": "((Able to give informed consent) AND (Age greater than or equal to 18 years) AND (American Society of Anesthesiologists (ASA) physical status 1 to 3) AND (right upper extremity surgery Undergoing) AND (supraclavicular block primary anesthetic))"}
{"candidate_id": "LLM04634", "doc_id": "NCT03623789_inc", "case_bucket": "or", "source_criterion": "Patients with osteoarthritis of the hip secondary to degeneration, inflammatory arthritis, gouty arthritis, acetabular dysplasia or osteonecrosis of the femoral head, and undergoing primary unilateral minimally invasive THA Age > 18 years and < 90 years Failure of medical treatment or rehabilitation. Hemoglobin > 11g/dl, No use of non-steroid anti-inflammatory agent one week before operation", "candidate_expression": "((< 90 years) AND (> 11g/dl) AND (> 18 years) AND (Age) AND (Failure) AND (Hemoglobin) AND (No) AND (acetabular dysplasia) AND (degeneration) AND (femoral head) AND (gouty arthritis) AND (hip) AND (inflammatory arthritis) AND (medical treatment) AND (minimally invasive THA) AND (non-steroid anti-inflammatory agent) AND (one week before operation) AND (operation) AND (osteoarthritis) AND (osteonecrosis) AND (primary) AND (rehabilitation) AND (secondary to degeneration) AND (undergoing) AND (unilateral))"}
{"candidate_id": "LLM04635", "doc_id": "NCT02589353_exc", "case_bucket": "or", "source_criterion": "adults 61 years old and above smokers pregnant women taking any prescription pain/ insulin medication has a history of taste or smell loss or other oral disorders (e.g., burning mouth syndrome) has current oral lesions, canker sores, or piercings has a history of food allergy", "candidate_expression": "((adults) AND (and above 61 years) AND (burning mouth syndrome) AND (current) AND (food allergy) AND (history) AND (old) AND (oral disorders) AND (other) AND (pregnant) AND (smokers) AND (women) AND ((smell loss) OR (taste loss)) AND ((canker sores) OR (oral lesions) OR (piercings)) AND ((prescription insulin medication) OR (prescription pain medication)))"}
{"candidate_id": "LLM04636", "doc_id": "NCT02653131_exc", "case_bucket": "other", "source_criterion": "HPN < 12 months metabolically unstable cancer as the reason for intestinal failure", "candidate_expression": "((< 12 months) AND (HPN) AND (cancer) AND (intestinal failure) AND (metabolically unstable))"}
{"candidate_id": "LLM04637", "doc_id": "NCT01218737_exc", "case_bucket": "or", "source_criterion": "Surgery and/or previous ocular pathology (presence of scar/change in the cornea, glaucoma, retinopathies, etc.). Patient has diabetes or is immunodepressed. Any systemic infection during the study. Signs and/or symptoms of ocular inflammation/infection (bacterial, viral, fungal, caused by Chlamydia, by Mycobacterium, Acanthamoeba or of allergic etiology). Have used any systemic or topical antibiotics for ocular infection in the previous 14 days. Patient has known hypersensitivity to any of the components of the formulations used in the study.", "candidate_expression": "((Acanthamoeba) AND (Chlamydia) AND (Mycobacterium) AND (components of the formulations) AND (during the study) AND (hypersensitivity) AND (in the previous 14 days) AND (infection) AND (ocular infection) AND (previous) AND (systemic) AND (the study) AND (topical) AND ((Surgery) OR (ocular pathology)) AND ((ocular infection) OR (ocular inflammation)) AND ((allergic etiology) OR (bacterial etiology) OR (caused by Acanthamoeba) OR (caused by Chlamydia) OR (caused by Mycobacterium) OR (fungal etiology) OR (viral etiology)) AND ((systemic antibiotics) OR (topical antibiotics)) AND ((change in the cornea) OR (glaucoma) OR (retinopathies) OR (scar)) AND ((diabetes) OR (immunodepressed)))"}
{"candidate_id": "LLM04638", "doc_id": "NCT02083991_exc", "case_bucket": "or", "source_criterion": "Diabetes mellitus or plasma glucose >11,1 at admission. Receiving steroids at the time of transplantation or likely to need steroids after transplantation. Multiorgan transplants and/or previously transplanted with any other organ than kidney. Panel reacting antibodies(PRA) >25% in most recent test or considered to be of high risk for rejection which requires an enhanced immunosuppression. Renal transplants from HLA-identical sibling. Hypersensitivity to, or disability to take immunosuppressive drugs. Blood group(ABO)-incompatible transplants. Unlikely to comply with the study requirements. Transplant from donor positive for HIV, HBsAg, Hepatitis C. Female of childbearing potential planing/being pregnant or unwilling to use contraception.", "candidate_expression": "((>11,1) AND (>25%) AND (Blood group(ABO)-incompatible) AND (Female of childbearing potential planing/being pregnant or unwilling to use contraception.) AND (HLA-identical sibling) AND (Renal transplants) AND (Transplant) AND (after transplantation) AND (at admission) AND (at the time of transplantation) AND (considered to be of high risk) AND (donor) AND (enhanced immunosuppression) AND (immunosuppressive drugs) AND (likely to need) AND (most recent test) AND (previously) AND (steroids) AND (transplantation) AND (transplants) AND ((Diabetes mellitus) OR (plasma glucose)) AND ((Multiorgan transplants) OR (transplanted with any other organ than kidney)) AND ((Panel reacting antibodies(PRA)) OR (rejection)) AND ((Hypersensitivity) OR (disability)) AND ((positive for HBsAg) OR (positive for HIV) OR (positive for Hepatitis C)) AND ((Receiving) OR (steroids)))"}
{"candidate_id": "LLM04639", "doc_id": "NCT00599924_inc", "case_bucket": "other", "source_criterion": "Advanced solid tumor malignancy (during expansion at the maximum tolerated dose, entry will be limited to patients wtih adenocarcinoma of the colon or rectum) Eastern Cooperative Oncology Group (ECOG) 0 or 1", "candidate_expression": "((Advanced solid tumor malignancy) AND (Eastern Cooperative Oncology Group (ECOG) 0 or 1))"}
{"candidate_id": "LLM04640", "doc_id": "NCT02959580_inc", "case_bucket": "other", "source_criterion": "Idiopathic Granulomatous Mastitis", "candidate_expression": "(Idiopathic Granulomatous Mastitis)"}
{"candidate_id": "LLM04641", "doc_id": "NCT03099863_exc", "case_bucket": "or", "source_criterion": "Surgeries that include: intradetrusor Botox, vaginal mesh excision, and fistula repair Pregnancy History of nephrolithiasis Allergy to study medications Congenital urogenital anomaly Neurogenic bladder", "candidate_expression": "((Allergy) AND (Botox) AND (Congenital) AND (History) AND (Neurogenic bladder) AND (Pregnancy) AND (fistula repair) AND (intradetrusor) AND (nephrolithiasis) AND (study medications) AND (urogenital anomaly) AND (vaginal mesh) AND (vaginal mesh excision))"}
{"candidate_id": "LLM04642", "doc_id": "NCT02907554_inc", "case_bucket": "or", "source_criterion": "Male and females aged 18 to 70 years Brain death Male and females aged 18 to 70 years Indication of kidney transplantation Informed consent", "candidate_expression": "((Brain death) AND (Informed consent) AND (Male) AND (aged 18 to 70 years) AND (females) AND (kidney transplantation Indication))"}
{"candidate_id": "LLM04643", "doc_id": "NCT01846507_exc", "case_bucket": "or", "source_criterion": "1. Active thromboembolic disease, history of thromboembolic disease (including retinal vein or artery occlusion), known inherited thrombophilia, or family history of thrombosis in a first degree relative 2. Subject has a severe medical or psychiatric illness that, in the opinion of the Investigator, would affect subject safety or compliance 3. Clinical evidence of severe bleeding disorder. Patients with mild bleeding disorders such as type 1 von Willebrand disease, mild platelet function defects such as platelet storage pool or release defects, and patients with bleeding due to Ehlers Danlos syndrome WILL be eligible to participate in the study. 4. Pregnancy within the past 6 months and/or breast-feeding 5. Use of hormonal contraception (estrogen and progestin) within 3 months of study entry, or anticipated need to initiate estrogen-containing hormonal contraception during the study period 6. Use of systemic steroids within 1 month of study entry 7. History of subarachnoid hemorrhage 8. History of Hepatitis B, C, or HIV 9. Baseline creatinine >20% above the upper limit of normal for age 10. Severe anemia (hemoglobin <8 g/dL) 11. Systolic blood pressure <85 or diastolic blood pressure <55 12. Heart rate <50 at time of screening 13. Use of intranasal DDAVP during menses will be permitted, but only if the patient has a history of using DDAVP consistently for ≥3 menstrual cycles prior to study enrollment, so that change in menstrual blood loss due to addition of Lysteda can be assessed. Use of one-time DDAVP during a DDAVP/Stimate challenge is also permitted during the study period, as is use of DDAVP in the event of severe epistaxis, trauma, or surgical procedures during the study period.", "candidate_expression": "((Ehlers Danlos syndrome) AND (Heart rate <50 at time of screening) AND (age) AND (anemia Severe) AND (bleeding) AND (bleeding disorder severe) AND (bleeding disorders mild) AND (creatinine Baseline >20% above the upper limit of normal for age) AND (estrogen) AND (estrogen-containing hormonal contraception anticipated need estrogen-containing during the study period) AND (hemoglobin <8 g/dL) AND (hormonal contraception) AND (intranasal DDAVP during menses) AND (medical illness) AND (progestin within 3 months of study entry) AND (psychiatric illness) AND (subarachnoid hemorrhage History) AND (systemic steroids within 1 month of study entry) AND ((mild platelet function defects) OR (type 1 von Willebrand disease)) AND ((platelet release defects) OR (platelet storage pool defects)) AND ((Pregnancy within the past 6 months) OR (breast-feeding within the past 6 months)) AND ((HIV) OR (Hepatitis B) OR (Hepatitis C)) AND ((artery occlusion) OR (retinal vein)) AND ((Systolic blood pressure <85) OR (diastolic blood pressure <55)) AND ((inherited thrombophilia) OR (thromboembolic disease Active) OR (thromboembolic disease history) OR (thrombosis family history)))"}
{"candidate_id": "LLM04644", "doc_id": "NCT03317197_exc", "case_bucket": "or", "source_criterion": "Pregnant women and young children aged <18 years; Patients with underlying disease cases without the possibility of resuscitation (e.g., terminal cancer); Patients with do-not-resuscitate (DNR) status; Death by excessive bleeding (e.g., abdominal main artery rupture); Patients who have experienced in-hospital CA; Patients previously treated with steroid, anti-cancer medicine, or immunosuppression treatment before CA; Patients already been registered with other studies; or Patients from whom informed consent cannot be obtained", "candidate_expression": "((CA) AND (CA in-hospital) AND (Death by excessive bleeding) AND (Patients already been registered with other studies; or) AND (Patients from whom informed consent cannot be obtained) AND (aged <18 years) AND (anti-cancer medicine) AND (do-not-resuscitate (DNR) status) AND (hospital) AND (immunosuppression treatment before CA) AND (main artery rupture abdominal) AND (steroid) AND (terminal cancer) AND (treated previously) AND (underlying disease without the possibility of resuscitation) AND (women) AND (young children))"}
{"candidate_id": "LLM04645", "doc_id": "NCT02779374_inc", "case_bucket": "scope", "source_criterion": "Women with POI: For the purpose of the research women is considered to have POI if she is aged less than 40 years and has amenorrhea of at least 4 month with FSH level above 25 IU/L (repeated twice >4 weeks apart).", "candidate_expression": "((FSH level above 25 IU/L repeated twice) AND (POI) AND (Women) AND (aged less than 40 years) AND (amenorrhea at least 4 month))"}
{"candidate_id": "LLM04646", "doc_id": "NCT02525991_inc", "case_bucket": "or", "source_criterion": "Male and female patients between the ages of 18-65 years, inclusive Patients (or legal representative) willing and able to provide written Informed Consent Form. Psychiatric patients already diagnosed of schizophrenia or bipolar disorder, according to the Diagnostic and Statistical Manual of Mental Disorders- IV, Diagnostic and Statistical Manual of Mental Disorders- V or International Code of Disease criteria. Patients with an on-going agitation episode, or with a previous one within the 6 months prior to screening, attended and managed in the hospital setting. Previously treated with ADASUVE® with a positive outcome (responders) according to (CGI-I) scale (defined as having a CGI-I score of 1 or 2 at 2 hours after administration of the inhalation) Patients free of active respiratory disease such as acute respiratory signs/symptoms (e.g., wheezing) or with active airways disease (asthma, chronic obstructive pulmonary disease or emphysema). Requirement of family or other caregiver support at study investigator criteria (defined as a patient's relative or caregiver (male or female) = 80 year old, who spend = 3 consecutive hours with patient, with good physical and psychological health status and without physical limitations, reading and writing educational level and able to understand and follow the study procedures). Availability of patient's medical records data about the previous treatment with ADASUVE® at hospital setting. If a female is of childbearing potential and sexually active (except if female is surgically sterile or post-menopausal with history of no menses for at least 24 months), patient must be non-lactating and non-pregnant (with a negative pregnancy test result at baseline visit) and have to agree to use a medically acceptable and effective birth control method throughout the study and for one week following the end of the study.", "candidate_expression": "((1 or 2) AND (18-65 years) AND (2 hours after administration of the inhalation)) AND (ADASUVE) AND (CGI-I score) AND (If a female is of childbearing potential and sexually active (except if female is surgically sterile or post-menopausal with history of no menses for at least 24 months), patient must be non-lactating and non-pregnant (with a negative pregnancy test result at baseline visit) and have to agree to use a medically acceptable and effective birth control method throughout the study and for one week following the end of the study) AND (Patients (or legal representative) willing and able to provide written Informed Consent Form) AND (active) AND (administration of the inhalation)) AND (ages) AND (agitation episode) AND (airways disease) AND (free) AND (respiratory disease) AND (screening) AND (wheezing) AND (within the 6 months prior to screening) AND ((Male) OR (female)) AND ((acute respiratory signs) OR (acute respiratory symptoms)) AND ((asthma) OR (chronic obstructive pulmonary disease) OR (emphysema)) AND ((bipolar disorder) OR (schizophrenia)) AND ((Diagnostic and Statistical Manual of Mental Disorders- IV) OR (Diagnostic and Statistical Manual of Mental Disorders- V) OR (International Code of Disease criteria)))"}
{"candidate_id": "LLM04647", "doc_id": "NCT02883400_inc", "case_bucket": "other", "source_criterion": "liver transplant", "candidate_expression": "(liver transplant)"}
{"candidate_id": "LLM04648", "doc_id": "NCT02295202_inc", "case_bucket": "other", "source_criterion": "Metabolic Syndrome (ATP III) Moderate to severe OSA", "candidate_expression": "((ATP III) AND (Metabolic Syndrome) AND (OSA Moderate to severe))"}
{"candidate_id": "LLM04649", "doc_id": "NCT02743598_exc", "case_bucket": "or", "source_criterion": "Personal or family history of pancreatitis Medullary thyroid carcinoma (MTC) or Multiple Endocrine Neoplasia Syndrome Type 2 (MEN 2) Gastroparesis Allergy to liraglutide or any of the active ingredients in liraglutide or other GLP-1 analogue Weight loss drugs other than metformin Type 1 diabetes mellitus or diabetic ketoacidosis Known major cognitive deficit dementia, history of head trauma with loss of consciousness >30 min, history of stroke, current central nervous system (CNS) disorder such as seizures or opportunistic CNS infection Renal insufficiency defined as creatinine clearance < 60 mL/min Active opportunistic infections Pregnancy or breastfeeding Unstable cardiovascular disease with hospitalization within 1 year for acute coronary syndrome Decompensated heart failure Substance abuse Active alcohol or opioid substitution therapy Serious or unstable medical or psychological conditions that would compromise the subject's safety for successful participation", "candidate_expression": "((< 60 mL/min) AND (>30 min) AND (Active) AND (Allergy) AND (Decompensated heart failure) AND (GLP-1 analogue) AND (Gastroparesis) AND (MEN 2) AND (MTC) AND (Medullary thyroid carcinoma) AND (Multiple Endocrine Neoplasia Syndrome Type 2) AND (Pregnancy or breastfeeding) AND (Renal insufficiency) AND (Substance abuse) AND (Type 1 diabetes mellitus) AND (Weight loss) AND (acute coronary syndrome) AND (alcohol) AND (central nervous system disorder) AND (cognitive deficit) AND (creatinine clearance) AND (dementia) AND (diabetic ketoacidosis) AND (head trauma) AND (hospitalization) AND (liraglutide) AND (loss of consciousness) AND (metformin) AND (opioid substitution therapy) AND (opportunistic CNS infection) AND (opportunistic infections) AND (other) AND (pancreatitis) AND (seizures) AND (stroke) AND (within 1 year))"}
{"candidate_id": "LLM04650", "doc_id": "NCT02393287_exc", "case_bucket": "other", "source_criterion": "1. Presence of other neoplasia 2. Man", "candidate_expression": "((Man) AND (neoplasia other))"}
```
