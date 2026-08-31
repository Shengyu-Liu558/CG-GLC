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
{"candidate_id": "LLM06401", "doc_id": "NCT00894712_exc", "case_bucket": "or", "source_criterion": "Visible skin pathology, excessive freckles, or skin blemishes in the test area. History of skin disease or hypersensitivity and repeated contact allergies. Sarcoma or squamous cell histology. Metastatic disease to the breast. Current tobacco use.", "candidate_expression": "((Current) AND (Metastatic disease) AND (Sarcoma) AND (contact allergies) AND (excessive) AND (freckles) AND (histology) AND (hypersensitivity) AND (skin blemishes) AND (skin disease) AND (skin pathology) AND (squamous cell) AND (to the breast) AND (tobacco use))"}
{"candidate_id": "LLM06402", "doc_id": "NCT02368743_inc", "case_bucket": "or", "source_criterion": "Patient aged 18 years or older. Patient suffering from mild to moderate active proctitis or distal proctosigmoiditis (MAYO score ≥ 3 and ≤ 10) at inclusion based on clinical and endoscopic findings within 6 months before study inclusion. Patient with evidence of endoscopic active proctitis or distal proctosigmoiditis (Montreal classification E1 or E2 defined by an involvement not exceeding 25 cm from the anal margin) within 6 months before study inclusion. Treatment of the current flare with Pentasa® to induce a remission initiated by the patient, the general practitioner or the gastroenterologist, during the inclusion visit or during the week before the inclusion visit. Patient having received oral and written information on the study, without any objections for the use of his/her personal data, and having signed a written Informed Consent Form.", "candidate_expression": "((MAYO score ≥ 3 and ≤ 10) AND (Montreal classification E1 or E2 involvement not exceeding 25 cm from the anal margin) AND (Pentasa) AND (Treatment within 6 months before study inclusion) AND (aged 18 years or older) AND (endoscopic) AND (flare) AND ((during the inclusion visit inclusion visit) OR (during the week before the inclusion visit the week before the inclusion visit)) AND ((active proctitis) OR (distal proctosigmoiditis)))"}
{"candidate_id": "LLM06403", "doc_id": "NCT02704754_exc", "case_bucket": "or", "source_criterion": "Psychiatric disorders other than insomnia, PTSD and specific phobias; including bipolar and psychotic disorders and meeting criteria for DSM-5 moderate alcohol or drug use disorders within the past year. Diagnosis of a sleep disorder other than insomnia including PSG findings of apnea/hypopnea or periodic limb movement indices > 10/hour; Medical conditions that require consistent use of medication or compromise sleep; History of moderate to severe traumatic brain injury or mild traumatic brain injury with ongoing post-concussive symptoms; Suicidal ideation with intent to act or with specific plan and intent in the past 6 months (Type 4 - 5 ideation on the Columbia Suicide Severity Rating Scale) or a concerning history of prior suicidal behavior. Caffeine use exceeding 5 cups of coffee per day or its equivalent; Habitual bedtimes after 3 AM, habitual rise times after 10 AM, or habitual napping > 1hour/day; Pregnancy or breastfeeding, or expecting to conceive while in study; Positive urine toxicology.", "candidate_expression": "((> 10/hour) AND (Caffeine) AND (Columbia Suicide Severity Rating Scale) AND (DSM-5) AND (Positive) AND (Pregnancy or breastfeeding, or expecting to conceive while in study) AND (Psychiatric disorders) AND (Suicidal ideation) AND (insomnia) AND (mild) AND (moderate) AND (other) AND (past 6 months) AND (past year) AND (post-concussive symptoms) AND (sleep disorder) AND (suicidal behavior.) AND (urine toxicology) AND ((alcohol use disorders) OR (drug use disorders)) AND ((apnea) OR (hypopnea)) AND ((PSG) OR (periodic limb movement indices)) AND ((traumatic brain injury)) AND ((moderate) OR (severe)) AND ((Type 4 ideation) OR (Type 5 ideation)) AND ((PTSD) OR (insomnia) OR (phobias)) AND ((bipolar) OR (psychotic disorders)))"}
{"candidate_id": "LLM06404", "doc_id": "NCT03073603_inc", "case_bucket": "or", "source_criterion": "Patients with either Relapsing-remitting MS (RRMS), Secondary progressive MS (SPMS), or Primary progressive MS (PPMS) by McDonald 2010 criteria. Patients defined by subtype based on 2013 updated phenotypic criteria. prospectively with an EDSS change of at least 1.0 points over the last two years, or retrospectively, with any significant change in motor function over at least one year, unrelated to relapse. 55 years of age or older at time of randomization; No evidence of recent new inflammatory disease activity (inactive by the Lublin criteria16) with no new relapse for at least five years and no new MRI lesion for at least three years interferon ß-1a, interferon ß-1b, glatiramer acetate, natalizumab, fingolimod, dimethyl fumarate, or teriflunomide; continuously for no less than 5 years. Taking most recent DMT continuously* for no less than two years. Willing to be randomized per this protocol; each patient will be questioned as to their willingness to stay in the trial regardless of the group to which group they are randomized. Willing to follow the protocol Continuously will be defined as no less than 75% of all prescribed doses, with no time of greater than four weeks from last intended dose to have missed a dose (8 weeks for natalizumab, i.e. one missed dose).", "candidate_expression": "((55 years or older) AND (DMT) AND (EDSS change) AND (Lublin criteria) AND (MRI) AND (No) AND (Willing to be randomized per this protocol; each patient will be questioned as to their willingness to stay in the trial regardless of the group to which group they are randomized.) AND (Willing to follow the protocol) AND (age) AND (at least 1.0 points) AND (at time of randomization) AND (change in motor function) AND (continuously) AND (dimethyl fumarate) AND (fingolimod) AND (for at least five years) AND (for at least three years) AND (for no less than 5 years) AND (for no less than two years) AND (glatiramer acetate) AND (inactive) AND (inflammatory disease) AND (interferon ß-1a) AND (interferon ß-1b) AND (lesion) AND (natalizumab) AND (new) AND (no) AND (over at least one year) AND (over the last two years) AND (relapse) AND (significant) AND (teriflunomide) AND (unrelated to relapse) AND ((Primary progressive MS (PPMS)) OR (Relapsing-remitting MS (RRMS)) OR (Secondary progressive MS (SPMS))))"}
{"candidate_id": "LLM06405", "doc_id": "NCT01116882_exc", "case_bucket": "or", "source_criterion": "1. The patient is pregnant or breastfeeding. 2. Evidence of STEMI within 72 hours of the intended treatment on infarct related or non-infarct related artery. 3. Cardiogenic shock on presentation or during current hospitalization. 4. Left ventricular ejection fraction less than 20%. 5. Known allergies to: aspirin, clopidogrel (Plavix) and ticlopidine (Ticlid), heparin, bivalirudin, stainless steel, or contrast agent (which cannot be adequately premedicated). 6. A platelet count less than 75,000 cells/mm3 or greater than 700,000 cells/mm3 or a WBC less than 3,000 cells/mm3. 7. Acute or chronic renal dysfunction (creatinine greater than 2.5 mg/dl or less than 150µmol/L). 8. Subject is currently participating in an investigational drug or device study that has not completed the primary endpoint or that clinically interferes with the current study endpoints. (Note: Trials requiring extended follow-up for products that were investigational, but have since become commercially available, are not considered investigational trials). 9. Prior participation in this study. 10. Within 30 days prior to the index study procedure, the subject has undergone a previous coronary interventional procedure of any kind. Note: This exclusion criterion does not apply to post-STEMI patients. 11. Stroke or transient ischemic attack within the prior 3 months. 12. Active peptic ulcer or upper gastrointestinal bleeding within the prior 3 months. 13. Subject has active sepsis. 14. Unprotected left main coronary artery disease (stenosis greater than 50%). 15. In the investigator's opinion, subject has a co-morbid condition(s) that could limit the life expectancy to less than one year, or limit the subject's ability to participate in the study or comply with follow-up requirements or impact the scientific integrity of the study. 16. Subject has normal or insignificant coronaries (i.e. coronary lesion(s) less than 50% stenosis). 17. Any target vessel has evidence of: excessive thrombus (e.g. requires target vessel thrombectomy) tortuousity (greater than 60 degree angle) that makes it unsuitable for proper stent delivery and deployment, heavy calcification. 18. Any target lesion requires treatment with a device other than percutaneous transluminal coronary angioplasty (PTCA) prior to stent placement (e.g. but not limited to, directional coronary atherectomy, excimer laser, rotational atherectomy, etc.). 19. Any lesion that is located in a saphenous vein graft, however, lesions located within the native vessel but accessed through the graft are eligible. 20. The target vessel is in a \"last remaining\" epicardial vessel (e.g. greater than 2 non-target epicardial vessels and the bypass grafts to these territories [if present] are totally occluded).", "candidate_expression": "((Cardiogenic shock) AND (In the investigator's opinion) AND (In the investigator's opinion, subject has a co-morbid condition(s) that could limit the life expectancy to less than one year, or limit the subject's ability to participate in the study or comply with follow-up requirements or impact the scientific integrity of the study.) AND (Left ventricular ejection fraction less than 20%) AND (STEMI within 72 hours) AND (Subject is currently participating in an investigational drug or device study that has not completed the primary endpoint or that clinically interferes with the current study endpoints. (Note: Trials requiring extended follow-up for products that were investigational, but have since become commercially available, are not considered investigational trials).) AND (allergies) AND (angle greater than 60 degree) AND (calcification heavy) AND (coronary interventional procedure Within 30 days prior to the index study procedure previous) AND (coronary lesion) AND (coronary lesion less than 50% stenosis) AND (creatinine) AND (device other than percutaneous transluminal coronary angioplasty (PTCA) stent placement) AND (hospitalization current) AND (left main coronary artery disease Unprotected) AND (lesion located in a saphenous vein graft) AND (life expectancy) AND (life expectancy less than one year) AND (saphenous vein graft) AND (sepsis active) AND (stenosis) AND (stenosis greater than 50%) AND (stent delivery and deployment unsuitable for proper) AND (stent placement) AND (target lesion) AND (target vessel thrombectomy) AND (the index study procedure) AND (thrombus) AND (tortuousity) AND (treatment) AND (treatment requires prior to stent placement) AND (unsuitable for proper) AND NOT (STEMI) AND NOT (percutaneous transluminal coronary angioplasty (PTCA)) AND ((Plavix) OR (Ticlid) OR (aspirin) OR (bivalirudin) OR (clopidogrel) OR (contrast agent) OR (heparin) OR (stainless steel) OR (ticlopidine)) AND ((breastfeeding) OR (pregnant)) AND ((greater than 700,000 cells/mm3) OR (less than 75,000 cells/mm3)) AND ((WBC less than 3,000 cells/mm3) OR (platelet count)) AND ((Acute renal dysfunction) OR (chronic renal dysfunction)) AND ((greater than 2.5 mg/dl) OR (less than 150µmol/L)) AND ((Stroke) OR (transient ischemic attack)) AND ((infarct related artery) OR (non-infarct related artery)) AND ((peptic ulcer) OR (upper gastrointestinal bleeding)) AND ((directional coronary atherectomy) OR (excimer laser) OR (rotational atherectomy)) AND ((accessed through the graft) OR (within the native vessel)))"}
{"candidate_id": "LLM06406", "doc_id": "NCT02746900_inc", "case_bucket": "other", "source_criterion": "18-50 ages Singleton pregnancy Cervical length <=25mm between 18(0) and 23(6) weeks", "candidate_expression": "((Cervical length <=25mm between 18(0) and 23(6) weeks) AND (Singleton pregnancy) AND (ages 18-50))"}
{"candidate_id": "LLM06407", "doc_id": "NCT02406495_inc", "case_bucket": "other", "source_criterion": "Is between 18 and 40 years of age (inclusive) Has had a self-reported visual exam in the last two years Is an adapted Avaira sphere contact lens wearer (at least 1 week in Avaira sphere) Has a contact lens spherical prescription between + 2.25 to - 8.00 (inclusive) Has a spectacle cylinder up to 0.75D in each eye. Can achieve best corrected spectacle distance visual acuity of 20/25 (0.10 logMAR) or better in each eye. Can achieve a distance visual acuity of 20/30 (0.18 logMAR) or better in each eye with the study contact lenses. Has clear corneas and no active ocular disease Has read, understood and signed the information consent letter. Patient contact lens refraction should fit within the available parameters of the study lenses. Is willing to comply with the wear schedule (at least 5 days per week, > 8 hours/day assuming there are no contraindications for doing so). Is willing to comply with the visit schedule", "candidate_expression": "((Avaira sphere) AND (Avaira sphere contact lens at least 1 week in Avaira sphere) AND (Has read, understood and signed the information consent letter.) AND (Is willing to comply with the visit schedule) AND (Is willing to comply with the wear schedule (at least 5 days per week, > 8 hours/day assuming there are no contraindications for doing so).) AND (age between 18 and 40 years (inclusive)) AND (best corrected spectacle distance visual acuity 20/25 or better 0.10 logMAR or better) AND (clear corneas) AND (contact lens spherical + 2.25 to - 8.00 (inclusive)) AND (distance visual acuity 20/30 or better 0.18 logMAR or better) AND (self-reported visual exam in the last two years) AND (spectacle cylinder up to 0.75D) AND (study contact lenses) AND NOT (ocular disease active))"}
{"candidate_id": "LLM06408", "doc_id": "NCT03115151_exc", "case_bucket": "or", "source_criterion": "Baseline cognitive deficits sufficient to make objective pain self-assessments unreliable in the estimation of the Study Investigators. Immunocompromised subject Coagulopathy Severe liver and renal dysfunction Preoperative neurological deficits The dura damage during surgery Inability to follow directions or comprehend the English language. Females who are pregnant as determined by positive pregnancy test on or before the day of surgery. Prisoners. Patient refusal to provide informed consent. Allergy to amide local anesthetics (lidocaine, bupivacaine, ropivacaine) or opioid (fentanyl).", "candidate_expression": "((Allergy) AND (Baseline cognitive deficits sufficient to make objective pain self-assessments unreliable in the estimation of the Study Investigators.) AND (Coagulopathy) AND (Females who are pregnant as determined by positive pregnancy test on or before the day of surgery) AND (Immunocompromised) AND (Inability to follow directions or comprehend the English language) AND (Patient refusal to provide informed consent) AND (Prisoners) AND (fentanyl) AND (neurological deficits Preoperative) AND (surgery dura damage) AND ((amide local anesthetics) OR (opioid)) AND ((bupivacaine) OR (lidocaine) OR (ropivacaine)) AND ((liver dysfunction) OR (renal dysfunction)))"}
{"candidate_id": "LLM06409", "doc_id": "NCT01424020_exc", "case_bucket": "or", "source_criterion": "Unable to participate for administrative reasons Psychiatric troubles Pain at rest or critical limb ischemia Unable to walk (ex: wheelchair subjects)", "candidate_expression": "((Pain at rest) AND (Psychiatric troubles) AND (Unable to participate administrative reasons) AND (Unable to walk) AND (critical limb ischemia) AND (wheelchair subjects))"}
{"candidate_id": "LLM06410", "doc_id": "NCT02644629_exc", "case_bucket": "or", "source_criterion": "Active or past psychotic disorder, including a history of psychotic affective state Mental Retardation or Autistic Spectrum Disorder Prominent personality disorder Cardiac or neurologic active medical condition, including past CVA/TIA (Cardiovascular Accident/Transient Ischemic Attack) or any other unstable medical condition. Chronic nasal congestion Active or recent drug or alcohol abuse Substantial suicidality in a patient requiring admission but refuses to do so, and signs an \"against medical advice\" release form as part of clinical evaluation, and does not answer the terms for involuntary admission.", "candidate_expression": "((Prominent personality disorder) AND (admission) AND (medical condition unstable) AND (nasal congestion Chronic) AND (psychotic affective state) AND (psychotic disorder) AND (suicidality Substantial) AND ((Cardiac active medical condition) OR (neurologic active medical condition)) AND ((CVA) OR (TIA)) AND ((Cardiovascular Accident) OR (Transient Ischemic Attack)) AND ((alcohol abuse) OR (drug abuse)) AND ((Active) OR (recent)) AND ((Active) OR (past)) AND ((Autistic Spectrum Disorder) OR (Mental Retardation)))"}
{"candidate_id": "LLM06411", "doc_id": "NCT02242188_exc", "case_bucket": "or", "source_criterion": "preterm delivery (<37 weeks of gestation) birth weight < 2500 g multiple pregnancy major illness or congenital anomaly being <50% breastfed at the time of inclusion food allergy anaemia (Hb <105 g/L [10.5 g/dL]) at inclusion, lack of informed consent", "candidate_expression": "((Hb <105 g/L 10.5 g/dL) AND (anaemia at inclusion) AND (birth weight < 2500 g) AND (breastfed <50% at the time of inclusion) AND (food allergy) AND (gestation <37 weeks) AND (lack of informed consent) AND (multiple pregnancy) AND (preterm delivery) AND ((congenital anomaly) OR (major illness)))"}
{"candidate_id": "LLM06412", "doc_id": "NCT02509949_inc", "case_bucket": "other", "source_criterion": "age > 17 and < 60 years; American Society of Anesthesiology (ASA) I-III; admitted for living donor renal transplantation.", "candidate_expression": "((American Society of Anesthesiology (ASA) I-III) AND (age > 17 and < 60 years) AND (living donor renal transplantation admitted for))"}
{"candidate_id": "LLM06413", "doc_id": "NCT02350439_exc", "case_bucket": "or", "source_criterion": "1. Left main disease (angiographically> 50%) 2. Cardiogenic shock / hemodynamic instability 3. Previous CABG 4. Increased risk of bradycardia on investigator clinical judgment 5. Severe chronic obstructive pulmonary disease 6. Coronary vessels with tortuosity or extremely calcified 7. Severe left ventricular hypertrophy or severe valvular disease 8. STEMI or non-STEMI within the past five days 9. Previous myocardial infarction in the distribution of the target vessel for the FFR 10. Acute decompensated heart failure.", "candidate_expression": "((Acute decompensated heart failure) AND (CABG Previous) AND (Cardiogenic shock) AND (Coronary vessel extremely calcified) AND (Coronary vessel tortuosity) AND (Increased risk) AND (Left main disease > 50%) AND (STEMI within the past five days) AND (bradycardia Increased risk) AND (chronic obstructive pulmonary disease Severe) AND (hemodynamic instability) AND (investigator clinical judgment) AND (left ventricular hypertrophy Severe severe) AND (myocardial infarction Previous in the distribution of the target vessel) AND (non-STEMI within the past five days) AND (valvular disease))"}
{"candidate_id": "LLM06414", "doc_id": "NCT02117986_exc", "case_bucket": "or", "source_criterion": "pregnant or breastfeeding patients patient with a history of hypersensitivity to colistin", "candidate_expression": "((breastfeeding) AND (colistin) AND (history of) AND (hypersensitivity) AND (pregnant))"}
{"candidate_id": "LLM06415", "doc_id": "NCT00720031_exc", "case_bucket": "or", "source_criterion": "Cardio-vascular pathologies, evoluting and uncontrolled, (severe HTA), cardiac deficiency, severe angor, severe arrhythmia. Infectious pathologies evoluting and requiring antibiotherapy. Patients HIV+. Transplanted patients or patients suffering from severe auto-immune disease. Psychiatric troubles that do not allow the protocol follow-up. Pregnant or breast-feeding women. No contraception.", "candidate_expression": "((Cardio-vascular pathologies evoluting uncontrolled) AND (HIV +) AND (HIV+) AND (HTA severe) AND (Infectious pathologies evoluting requiring antibiotherapy) AND (Pregnant) AND (Psychiatric troubles do not allow the protocol follow-up) AND (Transplanted) AND (angor severe) AND (antibiotherapy) AND (arrhythmia severe) AND (breast-feeding) AND (cardiac deficiency) AND (severe auto-immune disease) AND (women) AND NOT (contraception))"}
{"candidate_id": "LLM06416", "doc_id": "NCT02933671_exc", "case_bucket": "or", "source_criterion": "ASA 4 or 5 revision hip arthroplasty diagnosis of chronic pain daily chronic opioid use (over 3 months of continuous opioid use) inability to communicate pain scores or need for analgesia acute hip fracture Infection at the site of block placement Age under 18 years old or greater than 75 years old Pregnant women Intolerance/allergy to local anesthetics Weight <50 kg Suspected, or known addiction to or abuse of illicit drug(s), prescription medicine(s), or alcohol within the past 2 years. Uncontrolled anxiety, schizophrenia, or other psychiatric disorder that, in the opinion of the investigator, may interfere with study assessments or compliance Current or historical evidence of any clinically significant disease or condition that, in the opinion of the investigator, may increase the risk of surgery or complicate the subject's postoperative course.", "candidate_expression": "((ASA 4 or 5) AND (Age under 18 years old or greater than 75 years old) AND (Infection site of block placement) AND (Pregnant women) AND (Weight <50 kg) AND (chronic pain) AND (hip fracture acute) AND (inability to communicate pain scores or need for analgesia) AND (local anesthetics) AND (opioid chronic over 3 months) AND (revision hip arthroplasty) AND ((Intolerance) OR (allergy)) AND ((abuse) OR (addiction)) AND ((alcohol) OR (illicit drug) OR (prescription medicine)) AND ((anxiety) OR (psychiatric disorder) OR (schizophrenia)))"}
{"candidate_id": "LLM06417", "doc_id": "NCT03088904_exc", "case_bucket": "other", "source_criterion": "NA", "candidate_expression": "(EMPTY)"}
{"candidate_id": "LLM06418", "doc_id": "NCT03288428_inc", "case_bucket": "or", "source_criterion": "elective Laparoscopic myomectomy patients 24hr post-operative patient controlled analgesia analgesia no mild or severe liver or renal disfunction", "candidate_expression": "((myomectomy elective Laparoscopic 24hr post-operative) AND (patient controlled analgesia) AND ((mild) OR (severe)) AND ((liver disfunction) OR (renal disfunction)))"}
{"candidate_id": "LLM06419", "doc_id": "NCT02995291_exc", "case_bucket": "or", "source_criterion": "contra-indications for regular dental treatment medical history that contraindicates the use of epinephrine participant taken an opioid or an opioid like analgesic within 24 hours pregnant", "candidate_expression": "((contra-indications) AND (contraindicates medical history) AND (epinephrine) AND (opioid) AND (opioid like analgesic) AND (pregnant) AND (regular dental treatment))"}
{"candidate_id": "LLM06420", "doc_id": "NCT02894268_inc", "case_bucket": "other", "source_criterion": "A positive 13 C-urea breath test Formal H.pylori treatment more than two times Age >18 years", "candidate_expression": "((13 C-urea breath test) AND (>18 years) AND (Age) AND (H.pylori treatment) AND (more than two times) AND (positive))"}
{"candidate_id": "LLM06421", "doc_id": "NCT02901106_inc", "case_bucket": "or", "source_criterion": "patient 18 years old and more with multiple sclerosis according to the criteria of Mac Donald 2010 : relapsing-remitting (RR), secondary-progressive (SP) or primary-progressive (PP) for which treatment with dimethyl-fumarate has been prescribed followed at the Rothschild Foundation in the Neurology Department having given written consent to participation in the study", "candidate_expression": "((Rothschild Foundation in the Neurology Department) AND (criteria of Mac Donald 2010 relapsing-remitting RR secondary-progressive SP primary-progressive) AND (dimethyl-fumarate PP) AND (having given written consent to participation in the study) AND (multiple sclerosis) AND (old and more 18 years))"}
{"candidate_id": "LLM06422", "doc_id": "NCT00279552_inc", "case_bucket": "other", "source_criterion": "Patients suspected to have vitamin B12 deficiency defined as a plasma vitamin B12 below the reference interval (<200 pmol/L).", "candidate_expression": "((plasma vitamin B12 below the reference interval <200 pmol/L) AND (vitamin B12 deficiency suspected))"}
{"candidate_id": "LLM06423", "doc_id": "NCT02773173_inc", "case_bucket": "other", "source_criterion": "Patients older than 18 years Classification of the American Society of Anesthesiologists (ASA I-III) No cognitive deficits Signed informed consent prior to surgery", "candidate_expression": "((ASA I-III) AND (Classification of the American Society of Anesthesiologists) AND (Signed informed consent prior to surgery) AND (years older than 18) AND NOT (cognitive deficits))"}
{"candidate_id": "LLM06424", "doc_id": "NCT02830360_exc", "case_bucket": "or", "source_criterion": "Unable or unwilling to provide informed consent. Active ischemia (acute thrombus diagnosed by coronary angiography, or dynamic ST segment changes demonstrated on ECG) or another reversible cause of VT (e.g. drug-induced arrhythmia), had recent acute coronary syndrome within 30 days, coronary revascularization (<90 days bypass surgery, <30 days percutaneous coronary intervention), or have CCS functional class IV angina. Note that biomarker level elevation alone after ventricular arrhythmias does not denote acute coronary syndrome or active ischemia. Are ineligible to take the antiarrhythmic drug to which they would be assigned due to allergy, intolerance or contraindication Are known to have protruding left ventricular thrombus or mechanical aortic and mitral valves Have had a prior catheter ablation procedure for VT Are in renal failure (Creatinine clearance <15 mL/min), have NYHA Functional class IV heart failure, or a systemic illness likely to limit survival to <1 year Have had recent ST elevation myocardial infarction or non-ST elevation MI (< 30 days); note that biomarker elevation alone after ventricular arrhythmias does not denote MI. Are pregnant.", "candidate_expression": "((< 30 days) AND (<1 year) AND (<15 mL/min) AND (<30 days) AND (<90 days) AND (Active) AND (CCS functional class) AND (Creatinine clearance) AND (ECG) AND (IV) AND (NYHA Functional class) AND (ST segment changes) AND (Unable or unwilling to provide informed consent) AND (VT) AND (acute coronary syndrome) AND (acute thrombus) AND (antiarrhythmic drug) AND (bypass surgery) AND (catheter ablation procedure) AND (coronary angiography) AND (coronary revascularization) AND (drug-induced arrhythmia) AND (percutaneous coronary intervention) AND (pregnant) AND (reversible) AND (survival) AND (within 30 days,) AND ((angina) OR (ischemia)) AND ((allergy) OR (contraindication) OR (intolerance)) AND ((left ventricular thrombus) OR (mechanical aortic valves) OR (mechanical mitral valves)) AND ((heart failure) OR (renal failure) OR (systemic illness)) AND ((ST elevation myocardial infarction) OR (non-ST elevation MI)))"}
{"candidate_id": "LLM06425", "doc_id": "NCT03046108_exc", "case_bucket": "or", "source_criterion": "Contraindication for the use of corticosteroids or local anesthetics Presence of inflammatory arthropathy or neuropathy Skin lesions in the area diabetes mellitus Infiltration or previous surgery in the area Refusal to participate in the study", "candidate_expression": "((Contraindication) AND (Infiltration) AND (Refusal to participate in the stud) AND (Skin lesions) AND (corticosteroids) AND (diabetes mellitus) AND (inflammatory arthropathy) AND (local anesthetics) AND (neuropathy inflammatory) AND (previous surgery))"}
```
