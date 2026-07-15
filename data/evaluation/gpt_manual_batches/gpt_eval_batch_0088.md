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
{"candidate_id": "LLM02176", "doc_id": "NCT03615508_inc", "case_bucket": "or", "source_criterion": "Horner's Syndrome History of taking an alpha blocker (tamsulosin/ terazosin/doxazosin/alfuzosin/silodosin) medication", "candidate_expression": "((Horner's Syndrome) AND (alfuzosin) AND (alpha blocker) AND (doxazosin) AND (silodosin) AND (tamsulosin) AND (terazosin))"}
{"candidate_id": "LLM02177", "doc_id": "NCT01349413_exc", "case_bucket": "or", "source_criterion": "Presence of organic pathology identified by upper endoscopy or other investigations Presence of sliding hiatus hernia as defined by flap valve grade IV disruption of morphology at gastro-esophageal junction Concurrent medications that affect gastrointestinal motility Presence of acid reflux or heartburn symptoms of more than twice a month History of gastric surgery H. pylori infection Use of PPI or NSAID in the past 4 weeks Pregnancy Known hypersensitivity to PPI", "candidate_expression": "((H. pylori infection) AND (PPI) AND (Pregnancy) AND (at gastro-esophageal junction) AND (flap valve disruption of morphology) AND (gastric surgery) AND (gastrointestinal motility) AND (grade IV) AND (hiatus hernia) AND (hypersensitivity) AND (in the past 4 weeks) AND (medications) AND (more than twice a month) AND (organic pathology) AND (sliding) AND ((acid reflux) OR (heartburn symptoms)) AND ((NSAID) OR (PPI)) AND ((investigations) OR (upper endoscopy)))"}
{"candidate_id": "LLM02178", "doc_id": "NCT01349413_exc", "case_bucket": "or", "source_criterion": "Presence of organic pathology identified by upper endoscopy or other investigations Presence of sliding hiatus hernia as defined by flap valve grade IV disruption of morphology at gastro-esophageal junction Concurrent medications that affect gastrointestinal motility Presence of acid reflux or heartburn symptoms of more than twice a month History of gastric surgery H. pylori infection Use of PPI or NSAID in the past 4 weeks Pregnancy Known hypersensitivity to PPI", "candidate_expression": "((H. pylori infection) AND (NSAID) AND (PPI) AND (Pregnancy) AND (acid reflux) AND (flap valve disruption of morphology grade IV) AND (gastric surgery) AND (gastrointestinal motility) AND (heartburn symptoms) AND (hiatus hernia sliding at gastro-esophageal junction) AND (hypersensitivity) AND (investigations) AND (medications) AND (organic pathology) AND (upper endoscopy))"}
{"candidate_id": "LLM02179", "doc_id": "NCT01943812_exc", "case_bucket": "or", "source_criterion": "endometrial thickness < 7 mm or no triple layer endometrium and/or functional follicles Uterine abnormality Chronic medical disease oocyte donation cycles", "candidate_expression": "((Chronic medical disease) AND (Uterine abnormality) AND (endometrial thickness < 7 mm) AND (oocyte donation cycles) AND ((functional follicles) OR (triple layer endometrium)))"}
{"candidate_id": "LLM02180", "doc_id": "NCT03079141_exc", "case_bucket": "or", "source_criterion": "Any previous treatments for active CSC; Previous prescription of mineralocorticoid receptor antagonists, for cCSC or for other diseases; Current treatment with corticosteroids (topical or systemic), corticosteroid use within 3 months before possible start of trial treatment, or anticipated start of corticosteroid treatment within the first 2 years from the start of the trial period; Evidence of another diagnosis that can explain serous SRF or visual loss; Best-corrected visual acuity < 20/200 (Snellen equivalent); Profound chorioretinal atrophy in central macular area on ophthalmoscopy and OCT; Myopia > 6D; Visual loss and/or serous detachment on OCT < 6 weeks; Continuous and/or progressive visual loss > 18 months or serous detachment on OCT > 18 months; No hyperfluorescence on ICGA; Intraretinal edema on OCT; (relative) Contraindications for FA or ICGA; (relative) Contraindications for photodynamic treatment (pregnancy, porphyria, severely disturbed liver function). Pregnancy will not be routinely tested in female patients, but the possibility of pregnancy will be discussed during screening (relative) Known contraindications for initiation of eplerenone treatment (hyperkalemia, abnormal renal clearance, severe hepatic insufficiency (Child-Pugh C), type 2 diabetes mellitus with microalbuminuria, concomitant use of potassium supplements, potassium-sparing diuretics, strong CYP3A4 inhibitors, or the combination of an ACE-inhibitor and an angiotensin receptor blocking agent). Pregnancy will not be routinely tested in female patients, but the possibility of pregnancy will be discussed during screening; Soft drusen in treated eye or fellow eye, signs of choroidal neovascularization on ophthalmoscopy and/or FA/ICGA of the study eye.", "candidate_expression": "((< 20/200) AND (< 6 weeks) AND (> 18 months) AND (> 6D) AND (ACE-inhibitor) AND (Best-corrected visual acuity) AND (C) AND (CSC) AND (Child-Pugh) AND (Contraindications) AND (Current) AND (ICGA) AND (Intraretinal edema) AND (Myopia) AND (No) AND (OCT) AND (Previous) AND (Profound) AND (Soft drusen) AND (abnormal) AND (abnormal renal clearance) AND (active) AND (angiotensin receptor blocking agent) AND (anticipated) AND (central macular area) AND (chorioretinal atrophy) AND (choroidal neovascularization) AND (concomitant) AND (contraindications) AND (eplerenone) AND (hyperfluorescence) AND (microalbuminuria) AND (mineralocorticoid receptor antagonists) AND (ophthalmoscopy) AND (photodynamic treatment) AND (possible start of trial treatment) AND (previous) AND (serous detachment) AND (severely) AND (study eye) AND (systemic) AND (the first 2 years from the start of the trial period) AND (topical) AND (treatments) AND (type 2 diabetes mellitus) AND (within 3 months before possible start of trial treatment) AND (within the first 2 years from the start of the trial period) AND ((corticosteroid treatment) OR (corticosteroid use) OR (corticosteroids)) AND ((Visual loss) OR (serous detachment)) AND ((Continuous) OR (progressive)) AND ((OCT) OR (visual loss)) AND ((FA) OR (ICGA)) AND ((disturbed liver function) OR (porphyria) OR (pregnancy)) AND ((hyperkalemia) OR (renal clearance) OR (severe hepatic insufficiency)) AND ((cCSC) OR (other diseases)) AND ((potassium supplements) OR (potassium-sparing diuretics) OR (strong CYP3A4 inhibitors)) AND ((fellow eye) OR (treated eye)) AND ((FA) OR (ICGA) OR (ophthalmoscopy)))"}
{"candidate_id": "LLM02181", "doc_id": "NCT00886158_exc", "case_bucket": "other", "source_criterion": "Lack of consent", "candidate_expression": "(Lack of consent)"}
{"candidate_id": "LLM02182", "doc_id": "NCT02509091_inc", "case_bucket": "other", "source_criterion": "Age=18 years and =80 years; Patients with non-cystic fibrosis bronchiectasis diagnosed by high-resolution CT; Are sensitive to amikacin; Acute exacerbation of bronchiectasis; Capable of the completion of bronchoscopy, alveolar lavage, pulmonary function testing etc; Willing to join in and sign the informed consent form.", "candidate_expression": "((=18 years and =80 years) AND (Acute exacerbation of bronchiectasis) AND (Age) AND (Capable of the completion of bronchoscopy, alveolar lavage, pulmonary function testing etc) AND (Willing to join in and sign the informed consent form) AND (amikacin) AND (high-resolution CT) AND (non-cystic fibrosis bronchiectasis) AND (sensitive))"}
{"candidate_id": "LLM02183", "doc_id": "NCT02553226_exc", "case_bucket": "or", "source_criterion": "Unable to read and understand the Danish language or to give informed consent Cervical dilatation > 4 cm Non-cephalic presentation Multiple gestation Pathological fetal heart rate pattern (cardiotocogram, CTG) before Syntocinon® initiation Fetal weight estimation > 4500 g (clinical or ultrasonic) Subject declines participation Gestational age less than 37 completed weeks", "candidate_expression": "((CTG) AND (Cervical dilatation > 4 cm) AND (Fetal weight estimation > 4500 g clinical) AND (Gestational age less than 37 completed weeks) AND (Multiple gestation) AND (Non-cephalic presentation) AND (Pathological fetal heart rate pattern before Syntocinon® initiation) AND (Subject declines participation) AND (Syntocinon®) AND (Unable to give informed consent) AND (Unable to read) AND (Unable to understand the Danish language) AND (cardiotocogram) AND (ultrasonic))"}
{"candidate_id": "LLM02184", "doc_id": "NCT03335436_exc", "case_bucket": "or", "source_criterion": "use illicit drugs or relapse during the last trimester of pregnancy positive drug screen at the time of delivery allergies to any medications used in the study taking prescribed gabapentin at the time of admission for CD contraindications to neuraxial anesthesia or require general anesthesia for CD designated ASA physical status 4 or above", "candidate_expression": "((ASA physical status 4 or above) AND (CD) AND (admission) AND (allergies) AND (delivery) AND (drug screen positive at the time of delivery) AND (gabapentin prescribed at the time of admission for CD) AND (medications used in the study) AND (neuraxial anesthesia) AND (pregnancy last trimester) AND ((illicit drugs) OR (relapse)) AND ((contraindications) OR (general anesthesia require)))"}
{"candidate_id": "LLM02185", "doc_id": "NCT03198910_exc", "case_bucket": "other", "source_criterion": "", "candidate_expression": "(EMPTY)"}
{"candidate_id": "LLM02186", "doc_id": "NCT03360981_inc", "case_bucket": "or", "source_criterion": "patients aged >18, <75, left ventricle ejection fraction (LVEF) >50%, multivessel coronary disease detected by coronarography, indication to receive a CABG, stable CAD. All diabetics and non diabetics.", "candidate_expression": "((>18, <75) AND (>50%) AND (CABG) AND (CAD) AND (LVEF) AND (aged) AND (coronarography) AND (diabetics) AND (indication to receive) AND (left ventricle ejection fraction) AND (multivessel coronary disease) AND (non diabetics) AND (stable))"}
{"candidate_id": "LLM02187", "doc_id": "NCT01214096_exc", "case_bucket": "or", "source_criterion": "1. Atrial fibrillation; 2. Subject underwent cardiac pacemaker treatment; 3. Subject underwent metal graft treatment; 4. Claustrophobia; 5. Acute myocardial infarction, cardiac ischemia indicated by 6-minute walk test, hypertrophic cardiomyopathy, constrictive pericarditis, significant valve disease or congenital heart disease, severe pulmonary hypertension; 6. Ischemic heart failure without the revascularization or undergone the revascularization within last 6 months; 7. Subject underwent cardiac surgery or cerebrovascular events within the previous six months; 8. Subjects who plan to have cardiac transplantation; 9. Severe hepatic and renal insufficiency (serum creatinine>2.0 mg /dl, AST or ALT is five times higher than the upper limit of normal range); 10. Subject needs mechanical ventilation; 11. Systolic blood pressure < 90mmHg, or > 160mmHg; 12. Chronic heart failure complicated with acute hemodynamic disturbance or acute decompensation within last 1 month; 13. Mobitz Type II or III° atrial ventricular block，severe ventricular arrhythmia (polymorphic and frequent premature ventricular beats, frequent non-sustained ventricular tachycardia); 14. Serum potassium<3.2mmol/L, or>5.5mmol/L; 15. Female subject is pregnant or plan to become pregnant 16. Childbearing-aged female subject who is unmarried or dose not bear child; 17. Subject with life expectancy less than 6 months as assessed by investigators; 18. Subject participated in any other clinical trial within the previous three months; 19. Subject with previous history of tumor, or current tumor patient, or subject with pre-cancerous disease manifested by pathological examination (such as ductal carcinoma in situ or cervical epithelial dysplasia) 20. Examinations (physical examination, X-ray examination, type-B ultrasonic detection or other methods) reveal that the subject has malignant mass, gland hyperplasia or adenoma with endocrine activity, or impact on heart, or endocrine function (such as pheochromocytoma, thyroid enlargement); 21. The Investigator deemed for whatever reason that the subject is not likely to complete the study or comply with the study procedures (due to administration or any other reason).", "candidate_expression": "((Atrial fibrillation) AND (Chronic heart failure within last 1 month) AND (Claustrophobia) AND (Examinations) AND (Female) AND (Ischemic heart failure) AND (Mobitz Type II or III) AND (Serum potassium) AND (The Investigator deemed for whatever reason that the subject is not likely to complete the study or comply with the study procedures (due to administration or any other reason).) AND (blood pressure) AND (cardiac pacemaker) AND (cardiac pacemaker treatment) AND (cardiac transplantation plan) AND (female) AND (life expectancy less than 6 months) AND (mechanical ventilation) AND (metal graft) AND (metal graft treatment) AND (pathological examination) AND (premature ventricular beats polymorphic frequent) AND (serum creatinine >2.0 mg /dl) AND (unmarried) AND (ventricular tachycardia frequent non-sustained) AND NOT (bear child) AND ((impact on endocrine function) OR (impact on heart)) AND ((revascularization within last 6 months) OR NOT (revascularization)) AND ((cardiac surgery) OR (cerebrovascular events)) AND ((hepatic insufficiency) OR (renal insufficiency)) AND ((ALT) OR (AST)) AND ((< 90mmHg) OR (> 160mmHg)) AND ((acute decompensation) OR (acute hemodynamic disturbance)) AND ((atrial ventricular block) OR (ventricular arrhythmia severe)) AND ((<3.2mmol/L) OR (>5.5mmol/L)) AND ((pregnant) OR (pregnant plan)) AND ((Acute myocardial infarction) OR (cardiac ischemia)) AND ((pre-cancerous disease) OR (tumor current) OR (tumor previous history)) AND ((cervical epithelial dysplasia) OR (ductal carcinoma in situ)) AND ((X-ray examination) OR (other methods) OR (physical examination) OR (type-B ultrasonic detection)) AND ((6-minute walk test) OR (congenital heart disease congenital) OR (constrictive pericarditis) OR (hypertrophic cardiomyopathy) OR (severe pulmonary hypertension severe) OR (valve disease significant)) AND ((adenoma with endocrine activity) OR (endocrine activity) OR (gland hyperplasia) OR (malignant mass)) AND ((pheochromocytoma) OR (thyroid enlargement)))"}
{"candidate_id": "LLM02188", "doc_id": "NCT03344042_inc", "case_bucket": "or", "source_criterion": "parturient in labour without cervical dilation and regular uterine contractions", "candidate_expression": "((labour) AND (parturient) AND ((cervical dilation) OR (regular uterine contractions)))"}
{"candidate_id": "LLM02189", "doc_id": "NCT02117986_inc", "case_bucket": "other", "source_criterion": "patient hospitalized in critical care units patient infected by multi drug resistant Gram negative bacteria susceptibly only to colistin source of infection: blood, respiratory, intra abdominal or urinary", "candidate_expression": "((Gram negative bacteria) AND (colistin) AND (critical care units) AND (hospitalized) AND (multi drug resistant) AND (only) AND (susceptibly))"}
{"candidate_id": "LLM02190", "doc_id": "NCT01757717_exc", "case_bucket": "or", "source_criterion": "Patients who may receive therapeutically effective doses via an external beam approach to the lesion of interest as specified by MSKCC Radiation Oncology Department dose constraint criteria. Patients with kyphoplasty cement or hardware that would preclude effective catheter placement. Patients with paraspinal extension of disease with visceral involvement. Abnormal complete blood count. Any of the following: Platelet count < 75,000/ml Hb level < 9gm/dl WBC < 3.5/ml Abnormal coagulation profile: INR > 2.5 and/or PTT > 80 Patients who are on anticoagulation medication that may not be safely held for the procedure (≥ 5 days for antiplatelet agents and warfarin; ≥ 24 hours for low-molecular weight heparin formulations) will be excluded. Contraindications to general anesthesia", "candidate_expression": "((Abnormal coagulation profile) AND (Abnormal complete blood count) AND (Contraindications to general anesthesia) AND (Hb level < 9gm/dl) AND (MSKCC Radiation Oncology Department dose constraint criteria) AND (Platelet count < 75,000/ml) AND (WBC < 3.5/ml) AND (anticoagulation medication may not be safely held for the procedure) AND (antiplatelet agents ≥ 5 days) AND (coagulation profile Abnormal) AND (complete blood count Abnormal) AND (doses therapeutically effective) AND (external beam) AND (general anesthesia) AND (low-molecular weight heparin ≥ 24 hours) AND (may not be safely held for the procedure) AND (may receive therapeutically effective doses via an external beam approach to the lesion of interest) AND (paraspinal extension of disease) AND (visceral involvement) AND (warfarin ≥ 5 days) AND ((INR > 2.5) OR (PTT > 80)) AND ((kyphoplasty cement) OR (kyphoplasty hardware)))"}
{"candidate_id": "LLM02191", "doc_id": "NCT03164304_inc", "case_bucket": "other", "source_criterion": "Pregnant women admitted to Women health hospital with a diagnosis of severe pre-eclampsia", "candidate_expression": "((Pregnant) AND (Women health hospital) AND (admitted to) AND (pre-eclampsia) AND (severe) AND (women))"}
{"candidate_id": "LLM02192", "doc_id": "NCT03100513_inc", "case_bucket": "other", "source_criterion": "Adult Patients with Overt Hepatic Encephalopathy.", "candidate_expression": "((Adult) AND (Overt Hepatic Encephalopathy))"}
{"candidate_id": "LLM02193", "doc_id": "NCT03247413_exc", "case_bucket": "or", "source_criterion": "patient not previously scheduled for radiofrequency ablation of the cervical, thoracic, or lumbar facets, or sacroiliac joints on anticoagulation have a pacemaker age less than 18 years old non-English speaking", "candidate_expression": "((age less than 18 years old) AND (anticoagulation) AND (pacemaker) AND NOT (English speaking) AND NOT (radiofrequency ablation previously scheduled for) AND ((cervical facets) OR (lumbar facets) OR (sacroiliac joints) OR (thoracic facets)))"}
{"candidate_id": "LLM02194", "doc_id": "NCT02969187_exc", "case_bucket": "or", "source_criterion": "BMI <35 and > 60 kg/m2 Inability to walk (bed-bound or wheelchair dependence) open abdominal surgeries except simple appendectomy and common OB/GYN procedures in the pelvis (hysterectomy, C-section, and oophorectomy, tubal ligation) laparoscopic bowel or solid organ resection except laparoscopic cholecystectomy ventral hernia repair with mesh Preoperative chronic opiate use for chronic pain defined as opiate usage at least 60 mg/day of morphine equivalent for = 3 months (as defined by International Association for the Study of Pain22) in the one year period prior to the bariatric surgery The American Society of Anesthesiologists (ASA) score > 3 History of hypersensitivity or adverse reaction to bupivacaine or narcotics Inability to speak English ventral hernia repair Cholecystectomy hiatal hernia repair with posterior cruroplasty extensive lysis of adhesions other procedures that mandate addition of \"trocar(s)\" or \"feeding tube\" Addition of trocar(s) or conversion of surgery to hand-assisted or open", "candidate_expression": "((American Society of Anesthesiologists (ASA) score > 3) AND (BMI <35 and > 60 kg/m2) AND (C-section) AND (Cholecystectomy) AND (Inability to walk) AND (adverse reaction) AND (bariatric surgery the bariatric surgery) AND (bed-bound) AND (bupivacaine) AND (chronic pain) AND (common OB/GYN procedures pelvis) AND (conversion of surgery) AND (hand-assisted) AND (hiatal hernia) AND (hypersensitivity) AND (hysterectomy) AND (laparoscopic bowel resection) AND (lysis of adhesions extensive) AND (narcotics) AND (oophorectomy) AND (open) AND (open abdominal surgeries) AND (opiate Preoperative chronic) AND (opiate at least 60 mg/day of morphine equivalent for = 3 months in the one year period prior to the bariatric surgery) AND (posterior cruroplasty) AND (repair) AND (repair with mesh) AND (simple appendectomy) AND (solid organ resection) AND (surgery) AND (trocar Addition of) AND (tubal ligation) AND (ventral hernia) AND (wheelchair dependence) AND NOT (laparoscopic cholecystectomy))"}
{"candidate_id": "LLM02195", "doc_id": "NCT02952963_exc", "case_bucket": "or", "source_criterion": "Fasting plasma glucose > 7,0 mM, HbA1c > 48 mmol/mol 3 months after RYGB Dysregulated thyroid diseases, use of antithyroid treatment. Late diabetic complications as retinopathy, renal insufficiency, neuropathy or previous pancreatitis. Complications to RYGB. Documented reactive hypoglycaemia, severe dumping (vomiting, diarrhea, severe abdominal pain after food intake) Cholecystectomy.", "candidate_expression": "((3 months after RYGB) AND (> 48 mmol/mol) AND (> 7,0 mM) AND (Cholecystectomy) AND (Complications) AND (Dysregulated) AND (Late diabetic complications) AND (RYGB) AND (after food intake) AND (dumping) AND (food intake) AND (previous) AND (reactive hypoglycaemia) AND (severe) AND ((Fasting plasma glucose) OR (HbA1c)) AND ((neuropathy) OR (pancreatitis) OR (renal insufficiency) OR (retinopathy)) AND ((abdominal pain) OR (diarrhea) OR (vomiting)) AND ((antithyroid treatment) OR (thyroid diseases)))"}
{"candidate_id": "LLM02196", "doc_id": "NCT02567214_exc", "case_bucket": "or", "source_criterion": "Respiratory exacerbation within the 2 months preceding the study Current diagnostic of asthma Significant O2 desaturation (SpO2 < 85%) at rest or during exercise Presence of another pathology that could influence exercise tolerance Use of home oxygen", "candidate_expression": "((< 85%) AND (Current) AND (O2 desaturation) AND (Respiratory exacerbation) AND (Significant) AND (SpO2) AND (another) AND (diagnostic of asthma) AND (home oxygen) AND (influence exercise tolerance) AND (pathology) AND (the study) AND (within the 2 months preceding the study) AND ((at rest) OR (during exercise)))"}
{"candidate_id": "LLM02197", "doc_id": "NCT02256956_inc", "case_bucket": "or", "source_criterion": "Healthy Male >7 Metabolic Equivalents Written informed consent Chronic pain syndrome Drug abuse Alcohol abuse Suspicion of neurologic dysfunction at tested sites Ongoing treatment with antidepressants Ongoing treatment with analgesics Pretreatment with any CYP3A inducers or inhibitors Known allergy to tested drugs Elevated eye pressure Obstructive uropathy Heart disease Pulmonary disease Neurological disease Psychiatric illness", "candidate_expression": "((>7) AND (Alcohol abuse) AND (Chronic pain syndrome) AND (Drug abuse) AND (Elevated eye pressure) AND (Healthy) AND (Heart disease) AND (Male) AND (Metabolic Equivalents) AND (Neurological disease) AND (Obstructive uropathy) AND (Ongoing) AND (Pretreatment) AND (Psychiatric illness) AND (Pulmonary disease) AND (Suspicion) AND (Written informed consent) AND (allergy) AND (analgesics) AND (antidepressants) AND (neurologic dysfunction) AND (tested drugs) AND (tested sites) AND (treatment) AND ((CYP3A inducers) OR (CYP3A inhibitors)))"}
{"candidate_id": "LLM02198", "doc_id": "NCT02621489_exc", "case_bucket": "or", "source_criterion": "Type 1 diabetes (autoantibody positive). Any history of receiving GLP-1 analogues or dipeptidyl peptidase inhibitors within 6 months Known severe heart failure, classified as NYHA 4. Active myocarditis; malfunctioning artificial heart valve. History of ventricular tachycardia within 3 months before study entry; second- or third-degree atrioventricular block. Supine systolic blood pressure <85 mm Hg or >200 mm Hg at screening. Primary renal impairment, creatinine clearance < 45 ml/min if treated with metformin. Uncorrected hypokalemia or hyperkalemia (potassium <3.5 mmol/l or >5.5 mmol/l). Significant anemia (Hb < 90 g/l) Severe gastrointestinal disease, including gastroparesis. As judged by the Investigator. Body mass index (BMI) > 45 kg/m2. Malignant neoplasm requiring chemotherapy, surgery, radiation or palliative therapy in the previous 5 years. Patients with intraepithelial squamous cell carcinoma of the skin treated with topical 5FU and subjects with basal cell skin cancer are allowed to enter the trial. Females of child bearing potential who are pregnant, breast-feeding or intend to become pregnant. Current drug and alcohol abuse. History of acute or chronic pancreatitis Subjects considered by the Investigator to be unsuitable for the study.", "candidate_expression": "((4) AND (< 45 ml/min) AND (< 90 g/l) AND (<3.5 mmol/l) AND (<85 mm Hg) AND (> 45 kg/m2) AND (>200 mm Hg) AND (>5.5 mmol/l) AND (Active myocarditis) AND (BMI) AND (Body mass index) AND (Females of child bearing potential who are pregnant, breast-feeding or intend to become pregnant) AND (GLP-1 analogues) AND (Hb) AND (Malignant neoplasm) AND (NYHA) AND (Primary renal impairment) AND (Severe) AND (Significant) AND (Supine) AND (Type 1 diabetes) AND (acute pancreatitis) AND (alcohol abuse) AND (allowed) AND (anemia) AND (artificial heart valve) AND (autoantibody) AND (basal cell skin cancer) AND (chemotherapy) AND (chronic pancreatitis) AND (creatinine clearance) AND (dipeptidyl peptidase inhibitors) AND (drug abuse) AND (gastrointestinal disease) AND (gastroparesis) AND (heart failure) AND (hyperkalemia) AND (hypokalemia) AND (intraepithelial squamous cell carcinoma) AND (malfunctioning) AND (metformin) AND (palliative therapy) AND (positive) AND (potassium) AND (previous 5 years.) AND (radiation) AND (second- degree atrioventricular block) AND (severe) AND (skin) AND (surgery) AND (systolic blood pressure) AND (third-degree atrioventricular block) AND (topical 5FU) AND (ventricular tachycardia) AND (within 3 months) AND (within 6 months))"}
{"candidate_id": "LLM02199", "doc_id": "NCT02744976_inc", "case_bucket": "other", "source_criterion": "age =18 and <75 years; patients with stable coronary artery disease referred to PCI in an artery suitable for IVUS pullback; signed informed consent before PCI.", "candidate_expression": "((=18 and <75 years) AND (PCI) AND (age) AND (artery suitable for IVUS pullback) AND (coronary artery disease) AND (referred to) AND (signed informed consent before PCI) AND (stable))"}
{"candidate_id": "LLM02200", "doc_id": "NCT02818816_exc", "case_bucket": "or", "source_criterion": "Patients having had an ophthalmic surgical procedure within 6 months of the beginning of the study. Patients with a diagnosis of glaucoma Any abnormality of the cornea which may prevent reliable applanation tonometry Known allergy/ hypersensitivity reaction to Brimonidine Contra-indication to Brimonidine including patients on monoamine oxidase inhibitors (MOA) Patients unwilling or unable to provide informed consent Patients with anticipated difficult airway management (as this may require medications and/or airway manipulations resulting in increased IOP)", "candidate_expression": "((Brimonidine) AND (Contra-indication) AND (MOA) AND (Patients unwilling or unable to provide informed consen) AND (abnormality cornea) AND (difficult airway management) AND (glaucoma) AND (monoamine oxidase inhibitors) AND (ophthalmic surgical procedure within 6 months of the beginning of the study) AND ((allergy) OR (hypersensitivity)))"}
```
