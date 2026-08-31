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
{"candidate_id": "LLM02576", "doc_id": "NCT02882113_inc", "case_bucket": "other", "source_criterion": "19 years old and above. Patients who previously have received a liver transplant over the last six months and within last three years. Patients who are on Tacrolimus immunosuppressive therapy twice a day for at least two weeks. Patients who have normal liver function and renal function. Patients who have been monitored without complication such as acute rejection. Patients willing to sign his/her consent.", "candidate_expression": "((Patients willing to sign his/her consent) AND (Tacrolimus twice a day at least two weeks) AND (acute rejection) AND (liver function normal) AND (liver transplant last six months and within last three years) AND (old 19 years and above) AND (renal function normal) AND NOT (complication))"}
{"candidate_id": "LLM02577", "doc_id": "NCT02273791_inc", "case_bucket": "other", "source_criterion": "Women with PCOS as defined by the Rotterdam criteria. Presence of at least 2 cryopreserved good quality cleavage-stage embryo (good quality cleavage-stage embryos display stage-specific cell division, have blastomeres of fairly equal size with few to no cytoplasmic fragments).", "candidate_expression": "((PCOS) AND (Rotterdam criteria) AND (Women) AND (at least 2) AND (cleavage-stage embryo) AND (cryopreserved) AND (good))"}
{"candidate_id": "LLM02578", "doc_id": "NCT01909934_exc", "case_bucket": "or", "source_criterion": "Previous treatment with brentuximab vedotin. Previously received an allogeneic transplant. Patients with current diagnosis of primary cutaneous ALCL (patients whose ALCL has transformed to sALCL are eligible). Known cerebral/meningeal disease including signs or symptoms of progressive multifocal leukoencephalopathy (PML) Female patients who are lactating and breastfeeding or pregnant Known human immunodeficiency virus (HIV) positive Known hepatitis B surface antigen-positive, or known or suspected active hepatitis C infection", "candidate_expression": "((Female patients who are lactating and breastfeeding or pregnant) AND (HIV) AND (PML) AND (allogeneic transplant) AND (brentuximab) AND (cerebral disease) AND (hepatitis B surface antigen positive) AND (hepatitis C infection active) AND (human immunodeficiency virus positive) AND (meningeal disease) AND (primary cutaneous ALCL) AND (progressive multifocal leukoencephalopathy) AND (sALCL))"}
{"candidate_id": "LLM02579", "doc_id": "NCT00576173_inc", "case_bucket": "or", "source_criterion": "Patients with a histologically, radiologically or haematologically confirmed malignancy whose pain is judged by the investigator to be caused by the malignancy Patients must have been on a stable daily dose of weak opioids or strong opioids for at least 72 hours prior to the start the study and must remain at the same dosage for the duration of the study Patients must have a VAS (Visual analog scale) >=40mm", "candidate_expression": "((VAS (Visual analog scale) >=40mm) AND (haematologically) AND (histologically) AND (malignancy) AND (pain) AND (radiologically) AND (strong opioids) AND (weak opioids))"}
{"candidate_id": "LLM02580", "doc_id": "NCT03149887_exc", "case_bucket": "or", "source_criterion": "Pregnancy, coagulopathy, allergy to bupivacaine, renal failure, hepatic insufficiency, and/or inappropriate candidate for usual therapy (specifically, if unable to receive the usual preoperative interscalene nerve block: preexisting nerve injury on side of surgery, refusal of nerve block, infection at site of nerve block).", "candidate_expression": "((bupivacaine) AND (nerve injury) AND (preexisting) AND (preoperative interscalene nerve block) AND (side of surgery) AND (site of nerve block) AND (unable to receive) AND (usual therapy) AND ((Pregnancy) OR (allergy) OR (coagulopathy) OR (hepatic insufficiency) OR (inappropriate candidate) OR (renal failure)) AND ((infection) OR (refusal of nerve block)))"}
{"candidate_id": "LLM02581", "doc_id": "NCT02823808_exc", "case_bucket": "or", "source_criterion": "The use of weight-lowering drugs, any investigational blood-glucose or lipid-lowering agent (other than statins or ezetimibe) within the past 3 months Previous treatment with systemic corticosteroids or a change in dosage of thyroid hormones in the previous 6 weeks The use of insulin within the 3 months prior to screening Others", "candidate_expression": "((insulin within the 3 months prior to screening) AND ((ezetimibe) OR (statins)) AND ((systemic corticosteroids) OR (thyroid hormones change in dosage)) AND ((blood-glucose) OR (lipid-lowering)) AND ((agent investigational) OR (drugs weight-lowering)))"}
{"candidate_id": "LLM02582", "doc_id": "NCT03460002_exc", "case_bucket": "or", "source_criterion": "the child has temperature > 39.0◦C or a severe acute illness as defined by the examining nurse the child has as a mid upper arm circumference < 110 mm and is older than 6 months (most feasible local indicator of AIDS and chronic immunosuppressive disease) the child has experienced a severe allergic reaction after previous vaccination, drug or food. the child is enrolled in an ongoing study of Bacillus Calmette Guerin vaccine and is < 2 months old For the RECAMP-MV trial: the child is enrolled in RECAMP-OPV", "candidate_expression": "((RECAMP-MV trial enrolled in RECAMP-OPV) AND (acute illness severe as defined by the examining nurse) AND (child) AND (mid upper arm circumference < 110 mm) AND (old is older than 6 months) AND (severe allergic reaction after previous vaccination, drug or food) AND (temperature > 39.0◦C) AND (the child is enrolled in an ongoing study of Bacillus Calmette Guerin vaccine and is < 2 months old) AND ((drug) OR (food) OR (vaccination)))"}
{"candidate_id": "LLM02583", "doc_id": "NCT02571179_inc", "case_bucket": "other", "source_criterion": "healthy parturients with uncomplicated, single gestation pregnancies, full term (38-42 weeks of gestation) pregnancy, agreed to participate", "candidate_expression": "((agreed to participate) AND (healthy) AND (parturients) AND (pregnancies uncomplicated single gestation) AND (pregnancy full term) AND (weeks of gestation 38-42))"}
{"candidate_id": "LLM02584", "doc_id": "NCT00404495_exc", "case_bucket": "other", "source_criterion": "Diagnosis of brainstem glioma Concurrent administration of any other anti-tumor therapy Pre-existing uncontrolled diarrhea", "candidate_expression": "((anti-tumor therapy Concurrent any other) AND (brainstem glioma) AND (uncontrolled diarrhea))"}
{"candidate_id": "LLM02585", "doc_id": "NCT02992028_exc", "case_bucket": "or", "source_criterion": "age <45 or >80 allergies to medications used in the study history of renal diseases, a coagulation abnormality, a hepatic disease, or drug abuse definite radiographic evidence of osteoarthritis of the glenohumeral joint inflammatory arthritis including rheumatoid arthritis a history of acute trauma systemic conditions associated with chronic pain a history of infection an inability to understand the questionnaires", "candidate_expression": "((<45 or >80) AND (acute trauma) AND (age) AND (allergies) AND (associated with chronic pain) AND (chronic pain) AND (definite) AND (glenohumeral joint) AND (history) AND (inability to understand the questionnaires) AND (infection) AND (inflammatory arthritis) AND (medications) AND (osteoarthritis) AND (radiographic) AND (radiographic evidence) AND (rheumatoid arthritis) AND (systemic conditions) AND (used in the study) AND ((coagulation abnormality) OR (drug abuse) OR (hepatic disease) OR (renal diseases)))"}
{"candidate_id": "LLM02586", "doc_id": "NCT01997112_inc", "case_bucket": "or", "source_criterion": "=18 years old, men or post-menopausal women (women with no periods for 12 months or more, or those who have had a surgical menopause) Treated hypertensive patients with an average daytime ambulatory blood pressure measurement (ABPM) <150/95mmHg on stable doses of one or more antihypertensive medication (at least one of which should be; an ACE inhibitor, angiotensin receptor blocker or diuretic) for 3 months, or untreated hypertensive patients with an average daytime ABPM =135/85 but <150/95.", "candidate_expression": "((ACE inhibitor) AND (angiotensin receptor blocker) AND (antihypertensive medication stable doses one or more) AND (average daytime ABPM =135/85 but <150/95) AND (average daytime ambulatory blood pressure measurement (ABPM) <150/95mmHg) AND (diuretic) AND (hypertensive Treated) AND (hypertensive patients untreated) AND (men) AND (menopause) AND (no periods for 12 months or more) AND (post-menopausal) AND (surgical) AND (women) AND (years old =18))"}
{"candidate_id": "LLM02587", "doc_id": "NCT02678728_exc", "case_bucket": "other", "source_criterion": "Unstable vital sign before surgery Severe pulmonary disease requiring consistent treatment Illiterate Pregnancy", "candidate_expression": "((Illiterate) AND (Pregnancy) AND (Severe) AND (Unstable) AND (before surgery) AND (consistent treatment) AND (pulmonary disease) AND (requiring) AND (surgery) AND (vital sign))"}
{"candidate_id": "LLM02588", "doc_id": "NCT03260881_inc", "case_bucket": "or", "source_criterion": "T2DM as defined by American Diabetes Association (ADA) criteria Adult patients with T2DM who are indicated to receive liraglutide, not as first-line therapy, in addition to diet and exercise to improve glycemic control Hemoglobin A1c (HbA1c) = 9% Age = 18 years old Body mass index (BMI) = 27 Kg/m2 and/or waist circumference = 102 cm (40 inches) in men and 88 cm (35 inches) in women, respectively. Clinically and angiographically stable CAD who requires CABG as part of the standard medical care, as CAD does not represent a contraindication for using liraglutide. The stability of the CAD further warranties that study patients will not be exposed to higher risk by using liraglutide", "candidate_expression": "((Adult) AND (Age = 18 years old) AND (Body mass index (BMI) = 27 Kg/m2) AND (CABG requires) AND (CAD Clinically stable angiographically stable) AND (Hemoglobin A1c (HbA1c) = 9%) AND (T2DM) AND (T2DM American Diabetes Association (ADA) criteria) AND (liraglutide indicated to receive first-line therapy) AND (men = 102 cm 35 inches) AND (waist circumference 40 inches) AND (women 88 cm))"}
{"candidate_id": "LLM02589", "doc_id": "NCT02644629_inc", "case_bucket": "other", "source_criterion": "Age 18-65 Diagnosis of MDD (Major Depressive Disorder), made or affirmed by a senior psychiatrist in Shalvata MADRS score > 20 Treated with conventional anti-depressant, administered within a formal psychiatric clinic or by a certified psychiatrist.", "candidate_expression": "((Age 18-65) AND (MADRS score > 20) AND (MDD) AND (Major Depressive Disorder) AND (Treated) AND (conventional anti-depressant))"}
{"candidate_id": "LLM02590", "doc_id": "NCT03013790_inc", "case_bucket": "other", "source_criterion": "Non-ventilated Patients over the age of 65", "candidate_expression": "((age over 65) AND NOT (ventilated))"}
{"candidate_id": "LLM02591", "doc_id": "NCT02298504_inc", "case_bucket": "other", "source_criterion": "Pediatric patients with deep dental decay in primary molars Teeth with signs and symptoms of reversible pulpitis", "candidate_expression": "((Pediatric) AND (deep dental decay primary molars) AND (reversible pulpitis Teeth))"}
{"candidate_id": "LLM02592", "doc_id": "NCT02961582_inc", "case_bucket": "or", "source_criterion": "An average defecation frequency (DF) of <3 per week based on a 3-week defecation diary (patient-reported) Meet at least one other criterion of the Rome-IV criteria for idiopathic constipation based on the 3-week defecation diary (1) Refractory to conservative treatment Age: 14-80 years Straining during =25% of defecations Lumpy or hard stools in =25% of defecations Sensation of incomplete evacuation for =25% of defecations Sensation of anorectal obstruction/blockage for =25% of defecations Manual manoeuvres to facilitate =25% of defecations", "candidate_expression": "((14-80 years) AND (3-week defecation diary) AND (<3 per week) AND (=25%) AND (Age) AND (DF) AND (Lumpy stools) AND (Manual manoeuvres) AND (Refractory) AND (Rome-IV criteria for idiopathic constipation) AND (Sensation of anorectal blockage) AND (Sensation of anorectal obstruction) AND (Sensation of incomplete evacuation) AND (Straining) AND (at least one) AND (average defecation frequency) AND (conservative treatment) AND (criterion) AND (defecations) AND (hard stools) AND (idiopathic constipation) AND (other) AND (patient-reported))"}
{"candidate_id": "LLM02593", "doc_id": "NCT01604187_inc", "case_bucket": "other", "source_criterion": "ASA I-III Colonoscopy Written informed consent from participating subject", "candidate_expression": "((ASA I-III) AND (Colonoscopy) AND (Written informed consent from participating subject))"}
{"candidate_id": "LLM02594", "doc_id": "NCT03217409_exc", "case_bucket": "or", "source_criterion": "Subjects with hypersensitivity reaction to Statin and Ezetimibe Subjects with severe kidney disease Subjects with HIV positive result at the screening Pregnant or breast-feeding subjects Subjects with taking any medication affecting level of LDL (Fenofibrate, Omega 3 fatty aicd etc.) Insulin-treated Subjects Other exclusions applied", "candidate_expression": "((HIV positive at the screening) AND (Insulin) AND (LDL) AND (affecting) AND (hypersensitivity) AND (kidney disease severe) AND (medication) AND ((Fenofibrate) OR (Omega 3 fatty aicd)) AND ((Ezetimibe) OR (Statin)) AND ((Pregnant) OR (breast-feeding)))"}
{"candidate_id": "LLM02595", "doc_id": "NCT03047538_exc", "case_bucket": "or", "source_criterion": "hypersensitivity to perindopril or to other ACE inhibitors, amlodipine, atorvastatin, dihydropyridines or to or statins angioneurotic edema in medical history (hereditary / idiopathic or associated with prior treatment with ACE inhibitors) severe hypotension, shock, including cardiogenic shock hemodynamically unstable heart failure Active liver disease or unexplained persistent elevations of serum transaminases more than three times normal Women of childbearing age without reliable contraception pregnancy breastfeeding Patients with contraindications listed in the currently valid SP", "candidate_expression": "((ACE inhibitors) AND (Women more than three times normal) AND (angioneurotic edema) AND (breastfeeding) AND (childbearing age) AND (contraindications listed in the currently valid SP) AND (heart failure hemodynamically unstable) AND (hypersensitivity) AND (pregnancy) AND (treatment prior) AND ((associated) OR (hereditary) OR (idiopathic)) AND ((cardiogenic shock) OR (hypotension) OR (shock)) AND ((liver disease) OR (serum transaminases unexplained persistent elevations)) AND ((ACE inhibitors other) OR (amlodipine) OR (atorvastatin) OR (dihydropyridines) OR (perindopril) OR (statins)) AND ((reliable) OR NOT (contraception)))"}
{"candidate_id": "LLM02596", "doc_id": "NCT01312012_inc", "case_bucket": "other", "source_criterion": "pregnant women in 30 to 32 weeks of gestation, with positive HBsAg and HBeAg,serum viral load above 8log10 copies per mL", "candidate_expression": "((HBeAg) AND (HBsAg) AND (gestation 30 to 32 weeks) AND (pregnant) AND (serum viral load above 8log10 copies per mL) AND (women))"}
{"candidate_id": "LLM02597", "doc_id": "NCT02056301_inc", "case_bucket": "other", "source_criterion": "Patients age 8- 18 years 2) Patients undergoing minimally invasive pectus excavatum repair via Nuss procedure 3) American Society of Anesthesiology Status I-III", "candidate_expression": "((8- 18 years) AND (American Society of Anesthesiology Status) AND (I-III) AND (Nuss procedure) AND (age) AND (minimally invasive pectus excavatum repair))"}
{"candidate_id": "LLM02598", "doc_id": "NCT00236340_exc", "case_bucket": "other", "source_criterion": "Multiple pregnancy (more than 3 fetuses) Maternal history of placental abruptio Fetus with IUGR Pregnancy complicated with pre-eclampsia Unability to give informed consent", "candidate_expression": "((Fetus) AND (IUGR) AND (Maternal history of) AND (Multiple pregnancy) AND (Pregnancy) AND (fetuses more than 3) AND (placental abruptio) AND (pre-eclampsia) AND NOT (give informed consent))"}
{"candidate_id": "LLM02599", "doc_id": "NCT02884401_exc", "case_bucket": "or", "source_criterion": "On chronic treatment (i.e., two weeks or more) with any medication severely affecting oral status (e.g. participants with gingival hypertrophy caused by anti-epileptics, calcium antagonists, cyclosporine and other immunosuppressive) or bone metabolism (e.g. anticoagulant medications, long-standing steroid medications -i.e. equal or more 2.5mg of prednisolone a day taken for >3 months -, anticonvulsants, immunosuppressants). Affected by systemic diseases recognized to severely affect bone metabolism (e.g. Cushing's syndrome, Addison's disease, diabetes mellitus type 1, leukaemia, pernicious anaemia, malabsorption syndromes, chronic liver disease, rheumatoid arthritis). Knowingly affected by HIV or Hepatitis. History of local radiation therapy in the last five years. Affected by limited mental capacity or language skills such that study information cannot be understood, informed consent cannot be obtained, or simple instructions cannot be followed. Presenting an acute endodontic/periodontal lesion in the neighboring areas to the implant site. Completely edentulous With evident severe atrophy of the alveolar ridge that could preclude an implant placement (e.g. sharp knife edge ridge) Severe bruxism or clenching habits Smokers of > 5 cigarettes a day. A daily alcohol intake >2 units/day. Other severe acute or chronic medical or psychiatric condition or laboratory abnormality which may increase the risk associated with trial participation or investigational product administration or may interfere with the interpretation of study results and, in the judgment of the investigator, would make the participant inappropriate for entry into this trial. Patients unable or not willing to return for follow-ups.", "candidate_expression": "((Patients unable or not willing to return for follow-ups) AND (Smokers) AND (alcohol >2 units/day) AND (cigarettes > 5 a day) AND (edentulous Completely) AND (ffected by limited mental capacity or language skills such that study information cannot be understood, informed consent cannot be obtained, or simple instructions cannot be followed) AND (local radiation therapy last five years) AND (treatment two weeks or more) AND ((anti-epileptics) OR (calcium antagonists) OR (cyclosporine) OR (immunosuppressive)) AND ((bone metabolism) OR (gingival hypertrophy)) AND ((anticoagulant) OR (anticonvulsants) OR (immunosuppressants) OR (prednisolone equal or more 2.5mg a day >3 months) OR (steroid)) AND ((HIV) OR (Hepatitis)) AND ((lesion endodontic) OR (periodontal lesion)) AND ((bruxism) OR (clenching habits)) AND ((Addison's disease) OR (Cushing's syndrome) OR (chronic liver disease) OR (diabetes mellitus type 1) OR (leukaemia) OR (malabsorption syndromes) OR (pernicious anaemia) OR (rheumatoid arthritis)))"}
{"candidate_id": "LLM02600", "doc_id": "NCT02951832_inc", "case_bucket": "or", "source_criterion": "Women aged 20-49; Having a regular menstrual cycle of which the menstrual period is between day 3-7, and the period between day 25-35; Excluding internal and surgical disease (after having variety of physical examination such as electrocardiogram/hepatic and renal function/blood routine and urine routine).", "candidate_expression": "((20-49) AND (Women) AND (aged) AND (between day 25-35) AND (between day 3-7) AND (internal disease) AND (menstrual period) AND (regular menstrual cycle) AND (surgical disease))"}
```
