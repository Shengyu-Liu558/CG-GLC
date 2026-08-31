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
{"candidate_id": "LLM07976", "doc_id": "NCT01997580_exc", "case_bucket": "or", "source_criterion": "DSM-IV-TR substance-related disorders (except nicotine) significant medical or neurological conditions mental retardation or organic brain damage", "candidate_expression": "((DSM-IV-TR) AND (except) AND (nicotine) AND (significant medical or neurological conditions) AND (substance-related disorders) AND ((mental retardation) OR (organic brain damage)))"}
{"candidate_id": "LLM07977", "doc_id": "NCT03288428_inc", "case_bucket": "or", "source_criterion": "elective Laparoscopic myomectomy patients 24hr post-operative patient controlled analgesia analgesia no mild or severe liver or renal disfunction", "candidate_expression": "((liver disfunction) AND (myomectomy elective Laparoscopic 24hr post-operative) AND (patient controlled analgesia mild severe) AND (renal disfunction))"}
{"candidate_id": "LLM07978", "doc_id": "NCT02560389_inc", "case_bucket": "or", "source_criterion": "25-50 years of age PTSD related to physical or sexual assault Medically healthy English speaking", "candidate_expression": "((English speaking) AND (Medically healthy) AND (PTSD) AND (age 25-50 years) AND (physical assault) AND (sexual assault))"}
{"candidate_id": "LLM07979", "doc_id": "NCT02796378_inc", "case_bucket": "other", "source_criterion": "Elevated blood-cholesterol", "candidate_expression": "((Elevated) AND (blood-cholesterol))"}
{"candidate_id": "LLM07980", "doc_id": "NCT02888704_exc", "case_bucket": "or", "source_criterion": "Subjects who have systemic infection Subjects who have human Immunodeficiency virus (HIV), hepatitis B virus (HBV), and hepatitis C virus (HCV) Subjects who need to take the medicine which is prohibited during this study Subjects who have asthma Subjects who can not stop treatment with topical steroids (group 1~5), oral antibiotics, whole body photochemotherapy, immunosuppressive drug within 4 weeks before the treatment visit Pregnant, breast-feeding women or women who plan to become pregnant during this study (Females of childbearing potential must have a negative urine pregnancy test) Subjects who currently participate in other clinical trial or participated in other clinical trial within 30 days Subjects who had a serious adverse events during stem cell therapy Subjects who had a hypersensitivity to antibiotics or antimycotics Subjects who creatinine value is more than two times of the upper limit of the normal range at screening test Subjects who aspartate transaminase/alkaline transaminase (AST/ALT) value is more than three times of the upper limit of the normal range at screening test Subjects who have any other condition which the investigator judges would make patients unsuitable for study participation", "candidate_expression": "((Females) AND (Pregnant) AND (antibiotics) AND (antimycotics) AND (any other condition the investigator judges would make patients unsuitable for study participation) AND (aspartate transaminase/alkaline transaminase (AST/ALT) more than three times of the upper limit of the normal range at screening test) AND (asthma) AND (breast-feeding) AND (childbearing potential) AND (creatinine more than two times of the upper limit of the normal range at screening test) AND (hepatitis B virus (HBV)) AND (hepatitis C virus (HCV)) AND (human Immunodeficiency virus (HIV)) AND (hypersensitivity) AND (immunosuppressive drug) AND (oral antibiotics) AND (pregnant) AND (serious adverse events during) AND (stem cell therapy) AND (systemic infection) AND (the investigator judges would make patients unsuitable for study participation) AND (topical steroids) AND (urine pregnancy test negative) AND (whole body photochemotherapy) AND (women))"}
{"candidate_id": "LLM07981", "doc_id": "NCT03463564_inc", "case_bucket": "or", "source_criterion": "T1DM for at least 12 months persistent HbA1c levels = 7.5% (58 mmol/mol) despite optimized education therapy, recurrent severe hypoglycemic episodes or high glucose variability willingness to wear the insulin pump", "candidate_expression": "((58 mmol/mol) AND (= 7.5%) AND (HbA1c levels) AND (T1DM) AND (for at least 12 months) AND (insulin pump) AND (optimized education therapy) AND (persistent) AND (recurrent) AND (severe) AND (wear the insulin pump) AND (willingness) AND ((high glucose variability) OR (hypoglycemic episodes)))"}
{"candidate_id": "LLM07982", "doc_id": "NCT03481894_exc", "case_bucket": "or", "source_criterion": "Known hypersensitivity to egg, soybean proteins, peanut proteins, corn or corn products, or to any of the active substances or excipients Severe hyperlipidemia or severe disorders of lipid metabolism characterized by hypertriglyceridemia (serum triglyceride concentration >1,000 g/dL). Inborn errors of amino acid metabolism Cardiopulmonary instability (including pulmonary edema, cardiac insufficiency, myocardial infarction, acidosis and hemodynamic instability requiring significant vasopressor support) Hemophagocytic syndrome. PN in the last 7 days prior to study enrollment. Need for chronic PN before study start Liver enzymes (either AST, ALT, GGPT), or direct bilirubin exceeding 2 x upper limit of normal range Pathologically altered level of any serum electrolyte (sodium, potassium, magnesium, calcium, chloride, phosphate) unless corrected prior to the start of study treatment Pathologically altered blood pH, or oxygen saturation, or carbon dioxide unless corrected prior to the start of study treatment Pregnancy or lactation Participation in another clinical study", "candidate_expression": "((>1,000 g/dL) AND (Cardiopulmonary instability) AND (Hemophagocytic syndrome) AND (Inborn errors of amino acid metabolism) AND (PN) AND (Participation in another clinical study) AND (Pathologically altered) AND (Severe) AND (before study start) AND (chronic PN) AND (exceeding 2 x upper limit of normal range) AND (hypersensitivity) AND (in the last 7 days prior to study enrollment) AND (level of any serum electrolyte) AND (serum triglyceride concentration) AND (severe) AND (significant) AND (study enrollment) AND (study start) AND (vasopressor) AND (vasopressor support) AND ((disorders of lipid metabolism) OR (hyperlipidemia) OR (hypertriglyceridemia)) AND ((acidosis) OR (cardiac insufficiency) OR (hemodynamic instability) OR (myocardial infarction) OR (pulmonary edema)) AND ((Liver enzymes) OR (direct bilirubin)) AND ((ALT) OR (AST) OR (GGPT)) AND ((calcium) OR (chloride) OR (magnesium) OR (phosphate) OR (potassium) OR (sodium)) AND ((blood pH) OR (carbon dioxide) OR (oxygen saturation)) AND ((Pregnancy) OR (lactation)) AND ((active substances) OR (corn) OR (corn products) OR (egg) OR (excipients) OR (peanut proteins) OR (soybean proteins)))"}
{"candidate_id": "LLM07983", "doc_id": "NCT02787070_exc", "case_bucket": "other", "source_criterion": "General danger signs or symptoms of severe malaria Anaemia, defined as Hb <9g/dl G6PD deficiency (as determined by FST) Pregnant women as determined by Urine ß-HCG pregnancy test Known hypersensitivity to any of the drugs given", "candidate_expression": "((Anaemia) AND (G6PD deficiency) AND (Hb <9g/dl) AND (Pregnant women as determined by Urine ß-HCG pregnancy test) AND (drugs) AND (hypersensitivity) AND (malaria severe))"}
{"candidate_id": "LLM07984", "doc_id": "NCT02893293_inc", "case_bucket": "other", "source_criterion": "Osteonecrosis planned decompression surgery with autologous stem cell transplant", "candidate_expression": "((Osteonecrosis) AND (autologous stem cell transplant) AND (decompression surgery) AND (planned))"}
{"candidate_id": "LLM07985", "doc_id": "NCT03495609_exc", "case_bucket": "or", "source_criterion": "History of allergic reaction to compounds of similar chemical or biologic composition to hCG receiving medication that could interfere with the study protocol objectives (hormonal contraceptives, androgens, prednisone, thyroid hormones, insulin) previous treatment with follicle stimulating hormone for assisted reproduction uncontrolled intercurrent illness Heart disease Severe cognitive decline Psychiatric desease HIV positive Hepatitis B or C infection", "candidate_expression": "((HIV positive) AND (Heart disease) AND (History) AND (Psychiatric desease) AND (Severe) AND (allergic reaction) AND (assisted reproduction) AND (cognitive decline) AND (compounds of similar chemical or biologic composition to hCG) AND (could interfere with the study protocol objectives) AND (follicle stimulating hormone) AND (hCG) AND (intercurrent illness) AND (medication) AND (previous) AND (receiving) AND (treatment) AND (uncontrolled) AND ((Hepatitis B infection) OR (Hepatitis C infection)) AND ((androgens) OR (hormonal contraceptives) OR (insulin) OR (prednisone) OR (thyroid hormones)))"}
{"candidate_id": "LLM07986", "doc_id": "NCT03217409_inc", "case_bucket": "or", "source_criterion": "Subjects = 19 or = 75 years of age Subjects undergoing treatment for type 2 diabetes Subjects undergoing treatment of statin for hypercholesterolemia Fasting LDL-C = 250mg/dL at the screening visit Fasting LDL-C =70mg/dL or = 160mg/dL at the randomization visit Fasting TG<500mg/dL", "candidate_expression": "((<500mg/dL) AND (= 19 or = 75 years) AND (= 250mg/dL) AND (Fasting LDL-C) AND (Fasting TG) AND (age) AND (at the randomization visit) AND (at the screening visit) AND (hypercholesterolemia) AND (statin) AND (treatment) AND (type 2 diabetes) AND ((= 160mg/dL) OR (=70mg/dL)))"}
{"candidate_id": "LLM07987", "doc_id": "NCT02765217_exc", "case_bucket": "or", "source_criterion": "Receiving antibiotic and/or probiotic, 8 weeks before the study Chronic gastrointestinal system disorders Congenital anomalies Chronic diseases Chemotherapy and radiotherapy Pregnancy", "candidate_expression": "((Chronic diseases) AND (Chronic gastrointestinal system disorders) AND (Congenital anomalies) AND (Pregnancy) AND ((antibiotic) OR (probiotic)) AND ((Chemotherapy) OR (radiotherapy)))"}
{"candidate_id": "LLM07988", "doc_id": "NCT02926989_exc", "case_bucket": "other", "source_criterion": "An initial plasma sodium concentration of lower than 130 mmol/L An initial plasma sodium concentration of higher than 150 mmol/L An initial plasma potassium concentration of lower than 3.0 mmol/L Need for 10% glucose solution Diabetes Diabetes insipidus Diabetic ketoacidosis Renal disease that needs dialysis Protocol-determined chemotherapy hydration Severe liver disease Inborn errors of metabolism that need protocol-determined fluid therapy", "candidate_expression": "((10% glucose solution) AND (Diabetes) AND (Diabetes insipidus) AND (Diabetic ketoacidosis) AND (Inborn errors of metabolism) AND (Need for) AND (Protocol-determined) AND (Renal disease) AND (Severe) AND (chemotherapy hydration) AND (dialysis) AND (fluid therapy) AND (higher than 150 mmol/L) AND (initial) AND (liver disease) AND (lower than 130 mmol/L) AND (lower than 3.0 mmol/L) AND (need) AND (needs) AND (plasma potassium concentration) AND (plasma sodium concentration) AND (protocol-determined))"}
{"candidate_id": "LLM07989", "doc_id": "NCT02420015_inc", "case_bucket": "other", "source_criterion": "Currently smoke at least ten cigarettes a day Have been smoking for at least one year Meet criteria for schizophrenia, schizoaffective disorder, or another psychotic disorder based on structured clinical interview Can speak and write fluent conversational English Are between 18 and 70 years of age Are willing to make a smoking cessation attempt Score 26 or higher on the Montreal Cognitive Assessment", "candidate_expression": "((Are willing to make a smoking cessation attempt) AND (Montreal Cognitive Assessment 26 or higher) AND (age between 18 and 70 years) AND (psychotic disorder) AND (schizoaffective disorder) AND (schizophrenia) AND (smoke at least ten cigarettes a day) AND (smoking at least one year))"}
{"candidate_id": "LLM07990", "doc_id": "NCT02632318_inc", "case_bucket": "or", "source_criterion": "History of falls or dizziness at exit from bed in the morning (at least two incidents in the past year) At least 20/200 corrected visual acuity Stable health Normal hearing", "candidate_expression": "((Normal hearing) AND (Stable health) AND (corrected visual acuity At least 20/200) AND (dizziness) AND (falls) AND (incidents at least two in the past year))"}
{"candidate_id": "LLM07991", "doc_id": "NCT01891383_inc", "case_bucket": "or", "source_criterion": "Cases (with a history of TBI): 1. Ages 50-95 years 2. History of traumatic brain injury of sufficient severity to have resulted in medical attention (ascertained via the Ohio State University TBI Identification Questionnaire—OSU TBI-ID, and based on DoD/VA criteria) 3. Residence in AFRH-Washington D.C. or the Veterans Home of California-Yountville 4. MMSE score ≥ 20 5. Capacity to provide consent to participate in research (assessment made by study physician) 6. Ability to read and write English Controls (without a history of TBI): 1. Ages 50-95 years 2. No history of traumatic brain injury of sufficient severity to have resulted in medical attention (ascertained via the Ohio State University TBI Identification Questionnaire—OSU TBI-ID) 3. Residence in AFRH-Washington or the Veterans Home of California-Yountville 4. MMSE score ≥ 20 5. Capacity to provide consent or assent to participate in research 6. Ability to read and write English -", "candidate_expression": "((50-95 years) AND (Ability to read and write English) AND (Ability to read and write English -) AND (Ages) AND (Capacity to provide consent or assent to participate in research) AND (Capacity to provide consent to participate in research (assessment made by study physician)) AND (History) AND (MMSE) AND (No) AND (Ohio State University TBI Identification Questionnaire—OSU TBI-ID) AND (Residence) AND (history) AND (score ≥ 20) AND (sufficient severity) AND (traumatic brain injury) AND ((AFRH-Washington D.C.) OR (Veterans Home of California-Yountville)) AND ((AFRH-Washington) OR (Veterans Home of California-Yountville)))"}
{"candidate_id": "LLM07992", "doc_id": "NCT03077204_inc", "case_bucket": "or", "source_criterion": "Age>18 years Scheduled 1 or 2-level ACDF spine surgery The capacity to provide informed consent. Degenerative Disc Disease (as defined by neck pain of discogenic origin with degeneration of the disc confirmed by patient history and radiographic studies) Trauma (including fractures) Tumors Deformities or curvatures (including kyphosis, lordosis, or scoliosis) Pseudoarthrosis Failed previous fusion Decompression of the spinal cord following total or partial cervical vertebrectomy Spondylolisthesis Spinal stenosis Patients with current or recent history of malignancy or infectious disease. The inability to provide informed consent. Subject has marked local inflammation Subject has any mental or neuromuscular disorder which would create an unacceptable risk of fixation failure or complications in postoperative care. Subject has a bone stock compromised by disease, infection or prior implantation which cannot provide adequate support and/or fixation to the devices. Subject has bone abnormalities preventing safe screw fixation. Subject has any open wounds. Subject has rapid joint disease, bone absorption, osteopenia, osteomalacia, and/or osteoporosis. Osteoporosis or osteopenia are relative contraindications, since this condition may limit the degree of obtainable correction and/or the amount of mechanical fixation. Subject has a documented or suspected metal sensitivity. Subject is pregnant. Subject has anatomical structures or physiological performance that would interfere with implant utilization. Subject has inadequate tissue coverage over the operative site. Subject has other medical or surgical conditions which would preclude the potential benefit of surgery, such as congenital abnormalities, immunosuppressive disease, elevation of sedimentation rate unexplained by other diseases, elevation of white blood count (WBC), or marked left shift in the WBC differential count. Note: The Aviator Anterior Cervical Plating System is not approved or intended for screw attachment to the posterior elements (pedicles) of the cervical, thoracic, or lumbar spine. The surgeon must consider the levels of implantation, patient weight, patient activity level, and other patient conditions which may impact on the performance of the system.", "candidate_expression": "((>18 years) AND (ACDF spine surgery) AND (Age) AND (Decompression of the spinal cord) AND (Degenerative Disc Disease) AND (Failed) AND (Pseudoarthrosis) AND (Spinal stenosis) AND (Spondylolisthesis) AND (Trauma) AND (Tumors) AND (bone abnormalities) AND (bone stock compromised) AND (cannot) AND (congenital abnormalities) AND (contraindications) AND (current) AND (degeneration of the disc) AND (discogenic origin) AND (elevation) AND (fractures) AND (fusion) AND (history) AND (implant) AND (inadequate tissue coverage) AND (infectious disease) AND (interfere with utilization) AND (left shift) AND (local inflammation) AND (malignancy) AND (marked) AND (medical conditions) AND (metal) AND (neck pain) AND (open wounds) AND (operative site) AND (patient history) AND (preclude) AND (pregnant) AND (preventing) AND (previous) AND (prior) AND (radiographic studies) AND (recent) AND (relative) AND (risk of) AND (safe) AND (screw fixation) AND (sensitivity) AND (surgery) AND (surgical conditions) AND (unacceptable) AND (unexplained by other diseases) AND ((Deformities) OR (curvatures)) AND ((kyphosis) OR (lordosis) OR (scoliosis)) AND ((partial cervical vertebrectomy) OR (total cervical vertebrectomy)) AND ((1 -level) OR (2-level)) AND ((mental disorder) OR (neuromuscular disorder)) AND ((complications) OR (fixation failure)) AND ((disease) OR (implantation) OR (infection)) AND ((adequate support) OR (fixation to the devices)) AND ((bone absorption) OR (osteomalacia) OR (osteopenia) OR (osteoporosis) OR (rapid joint disease)) AND ((Osteoporosis) OR (osteopenia)) AND ((documented) OR (suspected)) AND ((anatomical structures) OR (physiological performance)) AND ((WBC differential count) OR (immunosuppressive disease) OR (sedimentation rate) OR (white blood count (WBC))))"}
{"candidate_id": "LLM07993", "doc_id": "NCT03208998_inc", "case_bucket": "or", "source_criterion": "HBsAg and HBeAg positive for more than 6 months, HBV DNA detectable with ALT level abnormal lasted for three months and at least time190 IU/L or liver puncture biopsy demonstrated apparent inflammation, never treated before enrolled.", "candidate_expression": "((ALT level abnormal 190 IU/L) AND (enrolled) AND (inflammation) AND NOT (treated before enrolled) AND ((HBV DNA detectable) OR (HBeAg positive) OR (HBsAg positive) OR (liver puncture biopsy)))"}
{"candidate_id": "LLM07994", "doc_id": "NCT00250640_inc", "case_bucket": "or", "source_criterion": "The treating physician has chosen Ventavis as a suitable long-term treatment for the patient Patient with primary pulmonary hypertension (i.e. Idiopathic Pulmonary Arterial Hypertension or Familial Pulmonary Arterial Hypertension) and classified as NYHA functional class III (NYHA = New York Heart Association) No prior treatment with Ventavis or other active treatments for primary pulmonary hypertension within 6 weeks of date of study inclusion (unless otherwise advised by Bayer Schering Pharma)", "candidate_expression": "((Familial Pulmonary Arterial Hypertension) AND (Idiopathic Pulmonary Arterial Hypertension) AND (NYHA functional class III) AND (Ventavis long-term) AND (primary pulmonary hypertension) AND (treatment with Ventavis) AND (treatments for primary pulmonary hypertension))"}
{"candidate_id": "LLM07995", "doc_id": "NCT02555163_exc", "case_bucket": "other", "source_criterion": "Non papillary gross features of the tumor Anteriorly located tumor Patients criteria Poor performance status History of BCG sepsis History of bladder irradiation Contracted bladder", "candidate_expression": "((Anteriorly located) AND (BCG) AND (Contracted bladder) AND (History) AND (Non papillary gross features) AND (Poor) AND (bladder irradiation) AND (performance status) AND (sepsis) AND (tumor))"}
{"candidate_id": "LLM07996", "doc_id": "NCT02579733_exc", "case_bucket": "or", "source_criterion": "Patients with azathioprine or biologics therapy", "candidate_expression": "((therapy) AND ((azathioprine) OR (biologics)))"}
{"candidate_id": "LLM07997", "doc_id": "NCT00943865_exc", "case_bucket": "or", "source_criterion": "diabetes ischemic heart disease or any abnormality on treadmill stress test inflammatory or chronic disorder pregnancy lactation creatinine level of 1,5 mg/dL or more gastrointestinal problems or musculoskeletal disorders that would prevent them to follow the test diets or exercise interventions liver dysfunction with a factor of at least 3 above the upper limit of normal in AST and ALT levels thyroid dysfunction, with serum TSH out of normal limits use of immunosuppressive drugs, corticosteroids or anorexigen", "candidate_expression": "((ALT levels) AND (AST levels) AND (anorexigen) AND (chronic disorder) AND (corticosteroids) AND (creatinine level 1,5 mg/dL or more) AND (diabetes) AND (disorder inflammatory) AND (exercise interventions) AND (gastrointestinal problems) AND (immunosuppressive drugs) AND (ischemic heart disease) AND (lactation) AND (liver dysfunction) AND (musculoskeletal disorders prevent) AND (pregnancy) AND (serum TSH out of normal limits) AND (test diets) AND (thyroid dysfunction) AND (treadmill stress test abnormality))"}
{"candidate_id": "LLM07998", "doc_id": "NCT02314559_exc", "case_bucket": "other", "source_criterion": "Dementia. Gastroscopy planned at the same time. Allergies to propofol All cases were a 'full stomach' is suspected (gastric banding) Pregnancy", "candidate_expression": "((Allergies) AND (Dementia) AND (Gastroscopy planned at the same time) AND (Pregnancy) AND (propofol))"}
{"candidate_id": "LLM07999", "doc_id": "NCT02386800_exc", "case_bucket": "other", "source_criterion": "Patient has participated in a combination trial where ruxolitinib was dispensed in combination with another study medication and the patient is still receiving combination therapy. Pregnant or nursing (lactating) women, where pregnancy is defined as the state of a female after conception and until the termination of gestation, confirmed by a positive hCG laboratory test. Women of child-bearing potential, defined as all women physiologically capable of becoming pregnant, unless they are using highly effective methods of contraception throughout the study duration inclusive of the 30-day safety follow up.", "candidate_expression": "((Patient has participated in a combination trial where ruxolitinib was dispensed in combination with another study medication and the patient is still receiving combination therapy) AND (Pregnant or nursing (lactating) women, where pregnancy is defined as the state of a female after conception and until the termination of gestation, confirmed by a positive hCG laboratory test.) AND (Women of child-bearing potential, defined as all women physiologically capable of becoming pregnant, unless they are using highly effective methods of contraception throughout the study duration inclusive of the 30-day safety follow up))"}
{"candidate_id": "LLM08000", "doc_id": "NCT02735577_inc", "case_bucket": "or", "source_criterion": "Between the ages of 21-60 Right-handed Capable of giving informed consent and complying with study procedures Reports drinking a minimum of 5 standard drinks for men or 4 standard drinks for women on at least 4 days per week on average over the past 28 days Meets DSM-V criteria for current Alcohol Use Disorder Seeking treatment for Alcohol Use Disorder Agree to not seek additional treatment, apart from Alcoholics Anonymous Willing to attempt to abstain from alcohol completely for the duration of the study Willing to be hospitalized on a research unit for 24 hours, longer if detoxification is needed.", "candidate_expression": "((4 standard drinks on at least 4 days per week) AND (Alcohol Use Disorder) AND (Between 21-60) AND (DSM-V criteria) AND (Meets) AND (Right-handed) AND (Seeking) AND (Willing) AND (Willing to be hospitalized on a research unit for 24 hours, longer if detoxification is needed) AND (abstain from alcohol) AND (ages) AND (completely) AND (drinking) AND (minimum of 5 standard drinks on at least 4 days per week) AND (over the past 28 days) AND (treatment) AND ((men) OR (women)))"}
```
