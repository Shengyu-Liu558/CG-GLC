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
{"candidate_id": "LLM02526", "doc_id": "NCT03213834_exc", "case_bucket": "or", "source_criterion": "age <18 years; Pregnancy inability to give informed written consent; previous thoracic surgery or thrombolytic therapy for pleural infection; medical thoracoscopy cannot be performed within 48 hours; inability to tolerate procedure due to hemodynamic instability or severe hypoxemia; inability to correct coagulopathy; presence of a homogeneously echogenic effusion on pleural US27 -", "candidate_expression": "((Pregnancy) AND (age <18 years) AND (cannot) AND (coagulopathy) AND (correct inability to) AND (homogeneously echogenic effusion) AND (inability to give informed written consent;) AND (inability to tolerate) AND (medical thoracoscopy cannot be performed within 48 hours) AND (pleural US) AND (pleural infection) AND (procedure) AND ((hemodynamic instability) OR (hypoxemia severe)) AND ((thoracic surgery) OR (thrombolytic therapy)))"}
{"candidate_id": "LLM02527", "doc_id": "NCT03119766_exc", "case_bucket": "or", "source_criterion": "Organic diseases of the digestive system (gastro-oesophageal reflux disease (GERD), ulcer, chronic pancreatitis, cholelithiasis, fatty liver disease, hepatitis, cirrhosis of liver, etc.) . Diagnosis of other functional diseases of the digestive system, such as dyskinesia of cystic duct or gallbladder, irritable bowel syndrome, etc. Discontinuation of proton pump inhibitors, propulsives, antispasmodics, antacids, or bismuth preparations less than 7 days prior to randomization. H. Pylori eradication within 2 months before study entry. Intestinal infection within 2 months before study entry. Known history of/suspected malignant neoplasm of various sites. Prior diagnosis of a class IV cardiovascular disease (according to the New York Heart Association, 1964), hypothyroidism, diabetes mellitus, chronic kidney disease (С3-5), or disease of liver with portal hypertension and/or severe decompensation (Child-Pugh score > 6). Other severe coexisting morbidity which, in the investigator's opinion, can prevent the patient from participating in the study. Allergy/intolerance to any of the components of medications used in the treatment. Pregnancy, breast-feeding. Patients who, from investigator's point of view, will fail to comply with the observation requirements of the trial or with the dosing regimen of the investigational drugs. Planned hospitalization during the study period, for any diagnostic or treatment procedures. Drug addiction, alcohol use in the amount over 2 units of alcohol a day, mental diseases. Intake of medicines listed in the section 'Prohibited concomitant treatment' for 1 month prior to the enrollment in the trial. Participation in other clinical trials within 3 months to the enrollment in this study. Patient is related to the research staff of the clinical investigative site who are directly involved in the trial or is the immediate family member of the investigator. The immediate family members include husband/wife, parents, children or brothers (or sisters), regardless of whether they are natural or adopted. Patient works for OOO \"NPF \"MATERIA MEDICA HOLDING\" (i.e., is the company's employee, temporary contract worker or appointed official responsible for carrying out the research or their immediate family).", "candidate_expression": "((Child-Pugh score > 6) AND (Discontinuation less than 7 days prior to randomization) AND (H. Pylori eradication within 2 months before study entry) AND (Intestinal infection within 2 months before study entry) AND (New York Heart Association class IV) AND (Organic diseases digestive system) AND (Participation in other clinical trials within 3 months to the enrollment in this study.) AND (components of medications used in the treatment) AND (disease of liver) AND (functional diseases digestive system) AND (hospitalization Planned during the study period) AND (malignant neoplasm various sites) AND (medicines listed in the section 'Prohibited concomitant treatment' 1 month prior to the enrollment in the trial) AND (morbidity coexisting) AND (portal hypertension) AND (works for OOO \"NPF \"MATERIA MEDICA HOLDING\") AND (С 3-5) AND ((dyskinesia of cystic duct) OR (dyskinesia of gallbladder) OR (irritable bowel syndrome)) AND ((antacids) OR (antispasmodics) OR (bismuth preparations) OR (propulsives) OR (proton pump inhibitors)) AND ((history of) OR (suspected)) AND ((cardiovascular disease) OR (chronic kidney disease) OR (diabetes mellitus) OR (hypothyroidism) OR (severe decompensation)) AND ((Allergy) OR (intolerance)) AND ((cholelithiasis) OR (chronic pancreatitis) OR (cirrhosis of liver) OR (fatty liver disease) OR (gastro-oesophageal reflux disease (GERD)) OR (hepatitis) OR (ulcer)) AND ((Pregnancy) OR (breast-feeding)) AND ((diagnostic procedures) OR (treatment procedures)) AND ((Drug addiction) OR (alcohol use over 2 units of alcohol a day) OR (mental diseases)) AND ((appointed official responsible for carrying out the research or their immediate family) OR (company's employee) OR (temporary contract worker)))"}
{"candidate_id": "LLM02528", "doc_id": "NCT02744976_exc", "case_bucket": "or", "source_criterion": "cardiac or non-cardiac illness with life expectancy of less than two years; failure to advance the IVUS catheter through the culprit lesion; acute coronary syndrome congestive heart failure NYHA III-IV diabetes mellitus chronic kidney disease previous PCI in the target vessel heavily calcified vessels allergy to metformin", "candidate_expression": "((III-IV) AND (IVUS catheter) AND (NYHA) AND (PCI) AND (acute coronary syndrome) AND (advance the IVUS catheter) AND (allergy) AND (chronic kidney disease) AND (congestive heart failure) AND (culprit lesion) AND (diabetes mellitus) AND (failure) AND (heavily calcified vessels) AND (less than two years) AND (life expectancy) AND (metformin) AND (previous) AND (target vessel) AND ((cardiac illness) OR (non-cardiac illness)))"}
{"candidate_id": "LLM02529", "doc_id": "NCT02536976_inc", "case_bucket": "or", "source_criterion": "Aged 25-80 at screening. Subjects older than 80 will be allowed at the discretion of the PI. Ambulatory (defined as able to ambulate at least 10 meters, with or without assistance). Clinical Diagnosis of PD based on the United Kingdom Brain Bank diagnostic criteria for PD. At least 8 micturitions per 24 hours and At least 3 urgency episodes per 3-day diary. A MoCA score between 19 and 28 (inclusive) at screening. For those on cognitive enhancers (donepezil, rivastigmine, memantine, galantamine) a MoCA score between 19 and 29 (inclusive) at screening. Provide informed consent to participate in the study and understand that they may withdraw their consent at any time without prejudice to their future medical care. Be cognitively capable, in the opinion of investigator, to understand and provide such informed consent. Be cognitively capable to complete the required questionnaires and assessments, OR have a care partner who is willing and capable to assist them in the completion of these tasks. Be on a stable regimen of antiparkinson's medications at least 30 days prior to screening, and be expected to remain on a stable dose for the duration of the study. If taking cognitive enhancers (donepezil, rivastigmine, memantine, galantamine), must be on stable dose at least 30 days prior to screening, and be expected to remain on a stable dose for the duration of the study.", "candidate_expression": "((25-80) AND (Aged) AND (Ambulatory) AND (At least 3 per 3-day diary.) AND (At least 8 per 24 hours) AND (Be cognitively capable to complete the required questionnaires and assessments, OR have a care partner who is willing and capable to assist them in the completion of these tasks) AND (Be cognitively capable, in the opinion of investigator, to understand and provide such informed consent) AND (MoCA score) AND (PD) AND (Provide informed consent to participate in the study and understand that they may withdraw their consent at any time without prejudice to their future medical care) AND (United Kingdom Brain Bank diagnostic criteria) AND (antiparkinson's medications) AND (at least 30 days prior to screening) AND (between 19 and 28) AND (between 19 and 29) AND (cognitive enhancers) AND (donepezil) AND (galantamine) AND (memantine) AND (micturitions) AND (rivastigmine) AND (screening) AND (stable dose) AND (urgency episodes))"}
{"candidate_id": "LLM02530", "doc_id": "NCT03495557_inc", "case_bucket": "or", "source_criterion": "Age = 18 years Laparoscopic cholecystectomy Emergent/elective =2 risk factors: diabetes mellitus, age =70 years, BMI =30, fascial enlargement", "candidate_expression": "((Age = 18 years) AND (cholecystectomy Laparoscopic) AND (risk factors =2) AND ((BMI =30) OR (age =70 years) OR (diabetes mellitus) OR (fascial enlargement)) AND ((Emergent) OR (elective)))"}
{"candidate_id": "LLM02531", "doc_id": "NCT02455921_inc", "case_bucket": "other", "source_criterion": "Children undergoing ENT surgery under general anaesthesia.", "candidate_expression": "((Children) AND (ENT surgery undergoing) AND (general anaesthesia))"}
{"candidate_id": "LLM02532", "doc_id": "NCT01824537_inc", "case_bucket": "other", "source_criterion": "Couple must have been in a new relationship that started no more than six months prior to study entry Both partners plan on remaining in Montreal for at least 1 year Plan on having continued sexual contact with partner Be willing to comply with study procedures", "candidate_expression": "((Be willing to comply with study procedures) AND (Plan on) AND (for at least 1 year) AND (having continued sexual contact with partner) AND (new relationship) AND (no more than six months prior to study entry) AND (plan on) AND (remaining in Montreal))"}
{"candidate_id": "LLM02533", "doc_id": "NCT03147599_inc", "case_bucket": "other", "source_criterion": "Men 18 years or older ONB within 1 year post-surgery.", "candidate_expression": "((18 years or older 18 years or older) AND (Men) AND (ONB within 1 year post-surgery) AND (surgery))"}
{"candidate_id": "LLM02534", "doc_id": "NCT02705222_inc", "case_bucket": "or", "source_criterion": "Perimenopausal women complaining of abnormal uterine bleeding (menorrhagia, metrorrhagia, polymenorrhoea or polymenorrhagia) without local gynecological cause. Failure of medical treatment for at least 3 months.", "candidate_expression": "((Failure) AND (Perimenopausal) AND (abnormal uterine bleeding) AND (for at least 3 months) AND (local gynecological cause) AND (medical treatment) AND (menorrhagia) AND (metrorrhagia) AND (polymenorrhagia) AND (polymenorrhoea) AND (without) AND (women))"}
{"candidate_id": "LLM02535", "doc_id": "NCT03320057_inc", "case_bucket": "or", "source_criterion": "Women seeking medication abortion through 70 days gestation Eligible for Mifeprex(r) at a study clinical site English or Spanish speaking Willing and able to participate in the study, including willing to go to the study pharmacy to obtain mifepristone", "candidate_expression": "((Mifeprex(r) Eligible for) AND (Willing and able to participate in the study) AND (Women) AND (medication abortion through 70 days gestation) AND (mifepristone to obtain) AND (study clinical site) AND (willing to go to the study pharmacy) AND ((English speaking) OR (Spanish speaking)))"}
{"candidate_id": "LLM02536", "doc_id": "NCT02200978_inc", "case_bucket": "other", "source_criterion": "Patients less than 16 years old with newly diagnosed PML-RARa positive acute promyelocytic leukemia.", "candidate_expression": "((PML-RARa) AND (acute promyelocytic leukemia) AND (less than 16 years) AND (old) AND (positive))"}
{"candidate_id": "LLM02537", "doc_id": "NCT00599924_inc", "case_bucket": "other", "source_criterion": "Advanced solid tumor malignancy (during expansion at the maximum tolerated dose, entry will be limited to patients wtih adenocarcinoma of the colon or rectum) Eastern Cooperative Oncology Group (ECOG) 0 or 1", "candidate_expression": "((0 or 1) AND (Advanced solid tumor malignancy) AND (Eastern Cooperative Oncology Group (ECOG)))"}
{"candidate_id": "LLM02538", "doc_id": "NCT02056301_inc", "case_bucket": "other", "source_criterion": "Patients age 8- 18 years 2) Patients undergoing minimally invasive pectus excavatum repair via Nuss procedure 3) American Society of Anesthesiology Status I-III", "candidate_expression": "((American Society of Anesthesiology Status I-III) AND (age 8- 18 years) AND (minimally invasive pectus excavatum repair Nuss procedure))"}
{"candidate_id": "LLM02539", "doc_id": "NCT00625742_inc", "case_bucket": "other", "source_criterion": "1. Are referred to the Cachexia Clinic with involuntary weight loss of >5% of their premorbid weight within the previous 6 months. 2. Are 18 years of age or older 3. Have a Karnofsky performance score of 60 or higher. 4. Can maintain oral food intake during the study 5. Can understand the study procedures and can sign an informed consent form. 6. Are not currently taking melatonin. 7. Are taking megestrol acetate and continue to lose weight despite at least 2 weeks of therapy. 8. Have a calculated creatinine clearance of >/= 60 cc/min.", "candidate_expression": "((Cachexia Clinic) AND (Karnofsky performance score 60 or higher) AND (calculated creatinine clearance >/= 60 cc/min) AND (involuntary weight loss >5% of their premorbid weight within the previous 6 months) AND (lose weight continue) AND (megestrol acetate Are taking) AND (of age 18 years or older) AND (therapy at least 2 weeks) AND NOT (melatonin currently))"}
{"candidate_id": "LLM02540", "doc_id": "NCT02705222_inc", "case_bucket": "or", "source_criterion": "Perimenopausal women complaining of abnormal uterine bleeding (menorrhagia, metrorrhagia, polymenorrhoea or polymenorrhagia) without local gynecological cause. Failure of medical treatment for at least 3 months.", "candidate_expression": "((Perimenopausal) AND (abnormal uterine bleeding) AND (medical treatment Failure) AND (menorrhagia) AND (metrorrhagia) AND (polymenorrhagia) AND (polymenorrhoea) AND (women) AND NOT (local gynecological cause))"}
{"candidate_id": "LLM02541", "doc_id": "NCT02827487_exc", "case_bucket": "other", "source_criterion": "Previous vaginal delivery. Submucous myoma. Uterine anomalies. Undiagnosed vaginal bleeding. Pelvic inflammatory disease.", "candidate_expression": "((Pelvic inflammatory disease) AND (Previous) AND (Submucous myoma) AND (Undiagnosed) AND (Uterine anomalies) AND (vaginal bleeding) AND (vaginal delivery))"}
{"candidate_id": "LLM02542", "doc_id": "NCT02200978_inc", "case_bucket": "other", "source_criterion": "Patients less than 16 years old with newly diagnosed PML-RARa positive acute promyelocytic leukemia.", "candidate_expression": "((PML-RARa positive) AND (acute promyelocytic leukemia) AND (old less than 16 years))"}
{"candidate_id": "LLM02543", "doc_id": "NCT03088280_inc", "case_bucket": "other", "source_criterion": "Primary kidney transplant recipients, adults", "candidate_expression": "((adults) AND (kidney transplant Primary))"}
{"candidate_id": "LLM02544", "doc_id": "NCT03363295_exc", "case_bucket": "or", "source_criterion": "Diabetic patients Patients with any macular changes prior to the surgery (epiretinal membranes, age macular disease, macular edema...) Patients who had any complication during phacoemulsification surgery", "candidate_expression": "((Diabetic) AND (age macular disease) AND (any) AND (complication) AND (during phacoemulsification surgery) AND (epiretinal membranes) AND (macular changes) AND (macular edema) AND (phacoemulsification surgery) AND (prior to the surgery) AND (surgery) AND (the surgery))"}
{"candidate_id": "LLM02545", "doc_id": "NCT03025620_exc", "case_bucket": "other", "source_criterion": "Patients unable to understand the objectives of the dietary intervention Patients in paliative care Patients receiving supplement diets", "candidate_expression": "(EMPTY)"}
{"candidate_id": "LLM02546", "doc_id": "NCT01665417_inc", "case_bucket": "or", "source_criterion": "Pathologic confirmation of lung adenocarcinoma with measurable disease, defined as at least one lesion that can be accurately measured in at least one dimension (longest diameter to be recorded on CT); Patients must have previously untreated locally advanced or metastatic NSCLC; Patients must have lung cancer with a documented EGFR activating mutation (exon 19 deletion, L858R).", "candidate_expression": "((L858R) AND (NSCLC untreated locally advanced metastatic) AND (Pathologic confirmation) AND (exon 19 deletion) AND (lesion at least one can be accurately measured in at least one dimension) AND (lung adenocarcinoma with measurable disease) AND (lung cancer with EGFR activating mutation))"}
{"candidate_id": "LLM02547", "doc_id": "NCT03034733_inc", "case_bucket": "other", "source_criterion": "primary total knee replacement surgery ASA (american society of anesthesiologists) class 1-3", "candidate_expression": "((ASA class 1-3) AND (american society of anesthesiologists) AND (total knee replacement surgery primary))"}
{"candidate_id": "LLM02548", "doc_id": "NCT02897856_inc", "case_bucket": "or", "source_criterion": "Children 6 month to 14 years who will be presented to the pediatric emergency or attended by emergency medical service who have active seizure and had no intravenous access would be eligible for the study.", "candidate_expression": "((6 month to 14 years) AND (Children) AND (active) AND (attended by emergency medical service) AND (intravenous access) AND (no) AND (pediatric emergency) AND (seizure) AND (years))"}
{"candidate_id": "LLM02549", "doc_id": "NCT03288428_inc", "case_bucket": "or", "source_criterion": "elective Laparoscopic myomectomy patients 24hr post-operative patient controlled analgesia analgesia no mild or severe liver or renal disfunction", "candidate_expression": "((24hr post-operative) AND (Laparoscopic) AND (elective) AND (myomectomy) AND (no) AND (patient controlled analgesia) AND ((mild) OR (severe)) AND ((liver disfunction) OR (renal disfunction)))"}
{"candidate_id": "LLM02550", "doc_id": "NCT02260700_inc", "case_bucket": "or", "source_criterion": "Body mass index (BMI; weight [kilogram(kg)]/height^2 [meter square (m^2)]) between 18 and 30 kg/m^2, (inclusive) Be healthy for their age group with or without medication on the basis of physical examination, medical history, vital signs, and 12-lead electrocardiogram (ECG) performed at Screening or admission. Minor deviations in ECG, which are not considered to be of clinical significance to the investigator, are acceptable Be healthy on the basis of clinical laboratory tests performed at Screening. If the results of the serum chemistry panel [including liver enzymes], hematology, or urinalysis are outside the normal reference ranges, the participant may be included only if the investigator judges the abnormalities or deviations from normal to be not clinically significant. This determination must be recorded in the participants' source documents and initialed by the investigator Men who are sexually active with a woman of childbearing potential and have not had a vasectomy must agree to use a barrier method of birth control for example, either condom with spermicidal foam/gel/film/cream/suppository or partner with occlusive cap (diaphragm or cervical/vault caps) with spermicidal foam/gel/film/cream/suppository, and all men must also not donate sperm during the study and for 3 months after receiving the last dose of study drug. In addition, their female partners should also use an appropriate method of birth control for at least the same duration Participants' must have signed an informed consent document indicating that they understand the purpose of and procedures required for the study and are willing to participate in the study", "candidate_expression": "((BMI) AND (Body mass index) AND (ECG) AND (Participants' must have signed an informed consent document indicating that they understand the purpose of and procedures required for the study and are willing to participate in the study) AND (Screening) AND (admission) AND (at Screening) AND (between 18 and 30 kg/m^2) AND (clinical laboratory tests) AND (deviations in ECG) AND (healthy) AND (hematology) AND (liver enzymes) AND (medical history) AND (not clinically significant) AND (outside the normal reference range) AND (performed at Screening) AND (performed at Screening or admission) AND (physical examination) AND (serum chemistry panel) AND (the investigator judges) AND (urinalysis) AND (vital signs) AND (weight [kilogram(kg)]/height^2 [meter square (m^2)]) AND (which are not considered to be of clinical significance to the investigator))"}
```
