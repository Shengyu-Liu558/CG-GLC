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
{"candidate_id": "LLM00576", "doc_id": "NCT03036462_inc", "case_bucket": "other", "source_criterion": "Patients aged at least 18 years Patients with chronic heart failure present for at least 12 months Confirmed presence of iron deficiency Serum haemoglobin of 9.5 to 14.0 g/dL", "candidate_expression": "((9.5 to 14.0 g/dL) AND (Serum haemoglobin) AND (aged) AND (at least 18 years) AND (chronic heart failure) AND (for at least 12 months) AND (iron) AND (iron deficiency))"}
{"candidate_id": "LLM00577", "doc_id": "NCT02965027_inc", "case_bucket": "or", "source_criterion": "Male and female Active-duty SMs or Veterans aged 18 or older who are in good general health. History of blast and/or impact head trauma mTBI meeting Defense and Veterans Brain Injury Center (DVBIC) mTBI criteria, which define mTBI as an injury to the head causing at least one of the following: alteration in consciousness (for up to 24 hours after the injury), loss of consciousness 0-30 minutes, and/or post-traumatic amnesia up to 1 day post-injury. If available, the Glasgow Coma Scale score must be 13-15, and head imaging findings (if imaging was performed) must be negative. Frequent HAs that started within 3months after a head injury. The HAs either 1) must last 4 or more hours a day and reach a moderate to severe intensity at any point during the headache, or 2) may be of any severity or duration if the participant takes a triptan or ergotamine. HAs meeting these criteria must have been present on average at least 8 days per 4-week period, starting within 30 days after head injury and occurring by self-report for at least 3 months prior to the Initial Screening Visit. The 4-week HA frequency/severity criteria must be confirmed during the Preliminary Screening Period. Women of childbearing potential must agree to abstain from sexual relations that could result in pregnancy or use an effective method of birth control acceptable to both participant and the clinician prescriber during the study. Men are not required to use contraception during the study. Participants must have English fluency sufficient to complete study measures.", "candidate_expression": "((Defense and Veterans Brain Injury Center (DVBIC) mTBI criteria meeting) AND (Glasgow Coma Scale 13-15) AND (HAs Frequent within 3months after a head injury) AND (HAs at least 8 days per 4-week period within 30 days after head injury at least 3 months prior to the Initial Screening Visit last 4 or more hours a day moderate to severe intensity) AND (Women of childbearing potential must agree to abstain from sexual relations that could result in pregnancy or use an effective method of birth control acceptable to both participant and the clinician prescriber during the study. Men are not required to use contraception during the study.) AND (aged 18 or older) AND (good general health) AND (head imaging) AND (impact head trauma History of blast) AND NOT (findings) AND ((Male) OR (female)) AND ((alteration in consciousness for up to 24 hours after the injury) OR (loss of consciousness 0-30 minutes) OR (post-traumatic amnesia up to 1 day post-injury)) AND ((Active-duty SMs) OR (Veterans)) AND ((ergotamine) OR (triptan)))"}
{"candidate_id": "LLM00578", "doc_id": "NCT03026465_inc", "case_bucket": "or", "source_criterion": "Patients older than 18 years Ischemic symptoms or evidence of myocardial ischemia (inducible or spontaneous) in the presence of >50% de novo stenosis located in native coronary vessels", "candidate_expression": "((>50%) AND (de novo) AND (evidence) AND (native coronary vessels) AND (older than 18) AND (stenosis) AND (years) AND ((Ischemic symptoms) OR (myocardial ischemia)) AND ((inducible) OR (spontaneous)))"}
{"candidate_id": "LLM00579", "doc_id": "NCT02964416_inc", "case_bucket": "or", "source_criterion": "Patients with craniotomy for supratentorial tumors under general anesthesia American Society of Anaesthesiologists (ASA) 2 and stable ASA 3 patients Elective surgery Patients with Glasgow Coma Scale (GCS) 15/15", "candidate_expression": "((15/15) AND (2) AND (3) AND (ASA) AND (American Society of Anaesthesiologists) AND (Elective surgery) AND (GCS) AND (Glasgow Coma Scale) AND (craniotomy) AND (general anesthesia) AND (stable) AND (supratentorial tumors))"}
{"candidate_id": "LLM00580", "doc_id": "NCT03444142_exc", "case_bucket": "or", "source_criterion": "Women with confirmed or suspected pregnancy Women under lactation and/or puerperium Hypersensibility to ingredients of intervention Physical impossibility for apply the drug Known pancreatic, renal, hepatic, heart or thyroid diseased Hypertension diagnosis Previous treatment for glucose Body Mass Index =39.9 kg/m2 Triglycerides =500 mg/dL Total cholesterol =300 mg/dL Night or rotating shift workers Blood Pressure =140/90 mmHg", "candidate_expression": "((=140/90 mmHg) AND (=300 mg/dL) AND (=39.9 kg/m2) AND (=500 mg/dL) AND (Blood Pressure) AND (Body Mass Index) AND (Hypersensibility) AND (Hypertension) AND (Previous) AND (Total cholesterol) AND (Triglycerides) AND (Women) AND (ingredients of intervention) AND (pregnancy) AND (treatment for glucose) AND ((heart disease) OR (hepatic disease) OR (pancreatic disease) OR (renal disease) OR (thyroid disease)) AND ((Night shift workers) OR (rotating shift workers)) AND ((confirmed) OR (suspected)) AND ((lactation) OR (puerperium)))"}
{"candidate_id": "LLM00581", "doc_id": "NCT03481894_exc", "case_bucket": "or", "source_criterion": "Known hypersensitivity to egg, soybean proteins, peanut proteins, corn or corn products, or to any of the active substances or excipients Severe hyperlipidemia or severe disorders of lipid metabolism characterized by hypertriglyceridemia (serum triglyceride concentration >1,000 g/dL). Inborn errors of amino acid metabolism Cardiopulmonary instability (including pulmonary edema, cardiac insufficiency, myocardial infarction, acidosis and hemodynamic instability requiring significant vasopressor support) Hemophagocytic syndrome. PN in the last 7 days prior to study enrollment. Need for chronic PN before study start Liver enzymes (either AST, ALT, GGPT), or direct bilirubin exceeding 2 x upper limit of normal range Pathologically altered level of any serum electrolyte (sodium, potassium, magnesium, calcium, chloride, phosphate) unless corrected prior to the start of study treatment Pathologically altered blood pH, or oxygen saturation, or carbon dioxide unless corrected prior to the start of study treatment Pregnancy or lactation Participation in another clinical study", "candidate_expression": "((ALT) AND (AST) AND (Cardiopulmonary instability) AND (GGPT) AND (Hemophagocytic syndrome) AND (Inborn errors of amino acid metabolism) AND (Liver enzymes) AND (PN in the last 7 days prior to study enrollment) AND (Participation in another clinical study) AND (Pregnancy) AND (acidosis) AND (active substances) AND (blood pH) AND (calcium) AND (carbon dioxide) AND (cardiac insufficiency) AND (chloride) AND (chronic PN before study start) AND (corn) AND (corn products) AND (direct bilirubin) AND (disorders of lipid metabolism severe) AND (egg) AND (excipients) AND (hemodynamic instability vasopressor support) AND (hyperlipidemia Severe) AND (hypersensitivity) AND (hypertriglyceridemia) AND (lactation) AND (level of any serum electrolyte Pathologically altered) AND (magnesium) AND (myocardial infarction) AND (oxygen saturation) AND (peanut proteins) AND (phosphate) AND (potassium) AND (pulmonary edema) AND (serum triglyceride concentration >1,000 g/dL) AND (sodium) AND (soybean proteins) AND (vasopressor))"}
{"candidate_id": "LLM00582", "doc_id": "NCT02466113_exc", "case_bucket": "or", "source_criterion": "With severe comorbidities, such as cardiovascular disease, chronic obstructive pulmonary disease, diabetes mellitus, and chronic renal dysfunction. With bad compliance or contraindication to enrollment. Pregnant woman or lactating woman. With contraindication to receive adjuvant chemotherapy.", "candidate_expression": "((Pregnant) AND (adjuvant chemotherapy) AND (bad compliance) AND (cardiovascular disease) AND (chronic obstructive pulmonary disease) AND (chronic renal dysfunction) AND (comorbidities) AND (contraindication) AND (contraindication to enrollment) AND (diabetes mellitus) AND (lactating) AND (severe) AND (woman))"}
{"candidate_id": "LLM00583", "doc_id": "NCT02671318_exc", "case_bucket": "or", "source_criterion": "Re-transplant; Patients with any panel reactive antibody (PRA) equal to or above 50%, class I or class II; Acute rejection episode in the last 30 days, or episode > 2A in the Banff criteria; GFR (MDRD) < 40 ml/min; Proteinuria > 0,5 g/l; Hemoglobin < 10 g/l and/or leucocytes < 4000 cels/mm3 and/or platelets < 150.000 cels/mm3; Triglycerides > 500 mg/dl with or without use of fibrate; Cholesterol total > 300 mg/dl with or without use of statin; Hepatic abnormalities; Significant periphery edema; Pulmonary abnormalities or breast x-ray abnormalities; Hyper sensibility to sirolimus formula;", "candidate_expression": "((< 10 g/l) AND (< 150.000 cels/mm3) AND (< 40 ml/min) AND (< 4000 cels/mm3) AND (> 0,5 g/l) AND (> 2A) AND (> 300 mg/dl) AND (> 500 mg/dl) AND (Cholesterol total) AND (GFR) AND (Hepatic abnormalities) AND (Hyper sensibility) AND (PRA) AND (Proteinuria) AND (Pulmonary abnormalities) AND (Re-transplant) AND (Significant) AND (Triglycerides) AND (abnormalities) AND (breast x-ray) AND (fibrate) AND (last 30 days) AND (panel reactive antibody) AND (periphery edema) AND (sirolimus) AND (statin) AND ((Hemoglobin) OR (leucocytes) OR (platelets)) AND ((class I) OR (class II) OR (equal to or above 50%)) AND ((Acute rejection episode) OR (Banff criteria)))"}
{"candidate_id": "LLM00584", "doc_id": "NCT02316886_exc", "case_bucket": "or", "source_criterion": "Patients in whom the preferred treatment is CABG(Coronary artery bypass grafting) Stented lesion Bypass graft lesion The patients who have more than or equal to 3 target lesions 2 target lesions in the same coronary territory Heavily calcified or angulated lesion Bifurcation lesion requiring 2 stenting technique Contraindication to or planned discontinuation of dual antiplatelet therapy within 1 year Life expectancy less than 2 years Planned cardiac surgery or planned major non cardiac surgery Woman who are breastfeeding, pregnant or planning to become pregnant during the course of the study", "candidate_expression": "((2) AND (Bifurcation lesion) AND (Bypass graft) AND (CABG) AND (Contraindication) AND (Coronary artery bypass grafting) AND (Heavily calcified) AND (Life expectancy) AND (Planned) AND (Stented) AND (Woman) AND (angulated) AND (breastfeeding) AND (cardiac surgery) AND (dual antiplatelet therapy) AND (during the course of the study) AND (in the same coronary territory) AND (lesion) AND (less than 2 years) AND (major) AND (more than or equal to 3) AND (non cardiac surgery) AND (planned) AND (planned discontinuation) AND (planning to become) AND (pregnant) AND (stenting technique) AND (target lesions) AND (within 1 year))"}
{"candidate_id": "LLM00585", "doc_id": "NCT01728194_inc", "case_bucket": "or", "source_criterion": "Age: 60-85 years, right-handed; Diagnosis: Major depression, unipolar (by Structured Clinical Interview for Diagnostic and Statistical Manual (DSM)IV (SCID-R) and DSM-IV criteria); Age of onset of first episode = 50 years with up to three depressive episodes; Severity of depression: A 24-Item Hamilton Depression Rating Scale (HDRS) = 20.", "candidate_expression": "((24-Item Hamilton Depression Rating Scale = 20) AND (Age 60-85 years) AND (Age = 50 years) AND (DSM-IV criteria)) AND (HDRS) AND (IV Structured Clinical Interview for Diagnostic and Statistical Manual) AND (Major depression unipolar) AND (depression) AND (depressive episodes three) AND (onset of first episode) AND (right-handed) AND ((DSM) OR (SCID)))"}
{"candidate_id": "LLM00586", "doc_id": "NCT03305666_inc", "case_bucket": "other", "source_criterion": "Patients undergoing SSRF at Denver Health Medical Center", "candidate_expression": "((Denver Health Medical Center) AND (SSRF))"}
{"candidate_id": "LLM00587", "doc_id": "NCT00846703_exc", "case_bucket": "other", "source_criterion": "No Down syndrome No other major disease that prohibits study treatment (e.g., severe congenital heart disease) Not requiring significant therapy modification owing to study therapy associated complications No complications due to other interventions No one with missing data that are needed for the differential diagnosis, or for selection of the proper therapy arm", "candidate_expression": "((No) AND (Not) AND (complications) AND (congenital heart disease severe) AND (interventions other) AND (study therapy) AND NOT (complications) AND NOT (Down syndrome) AND NOT (major disease other))"}
{"candidate_id": "LLM00588", "doc_id": "NCT02419378_inc", "case_bucket": "or", "source_criterion": "Signed informed consent form (ICF) Age 18 to 55 years old (inclusive) as of the date the ICF is signed Diagnosis of MS according to the McDonald criteria 2010 and cranial MRI scan demonstrating white matter lesions attributable to MS within 10 years before Screening Onset of MS symptoms (as determined by a neurologist, either at present or retrospectively) within 10 years of the date the ICF is signed EDSS score 0.0 to 5.0 (inclusive) at Screening Patients with (highly) active RRMS disease course indicated to receive alemtuzumab according to the following conditions (at least 1 out of 3 conditions has to be fulfilled): 1. =2 MS relapses within 24 months, 2. clinical (=1 relapse) or MRI (new gadolinium enhancing lesions) disease activity under therapy with other diseasemodifying therapies, 3. severe relapse with high disease activity (=9 T2 hyperintense Lesions and =1 gadolinium enhancing lesion) on MRI. Completion of all vaccinations required by the applicable immunization guidelines published by \"ständige Impfkommission\" (STIKO) History of chickenpox or positive test for antibodies against varicella zoster virus (VZV)", "candidate_expression": "((0.0 to 5.0) AND (18 to 55 years old () AND (=1) AND (=2) AND (=9) AND (Age) AND (EDSS score) AND (Lesions) AND (MRI) AND (MS) AND (MS relapses) AND (MS symptoms) AND (McDonald criteria 2010) AND (RRMS) AND (Signed informed consent form (ICF)) AND (T2 hyperintense) AND (VZV) AND (active) AND (alemtuzumab) AND (chickenpox) AND (cranial MRI scan) AND (gadolinium enhancing) AND (lesion) AND (lesions) AND (new) AND (positive) AND (relapse) AND (severe) AND (test for antibodies) AND (varicella zoster virus) AND (within 10 years) AND (within 10 years before Screening) AND (within 24 months,))"}
{"candidate_id": "LLM00589", "doc_id": "NCT02952378_exc", "case_bucket": "or", "source_criterion": "Heart failure Signs of kidney injury/failure Severe allergies", "candidate_expression": "((Heart failure) AND (Severe) AND (Signs of) AND (allergies) AND ((kidney failure) OR (kidney injury)))"}
{"candidate_id": "LLM00590", "doc_id": "NCT02196285_inc", "case_bucket": "other", "source_criterion": "Male Age between 18 and 49 years old; Willing to provide name, address, telephone and other contact information in order to be contacted, whenever needed (example: in case of missing any scheduled visit, contact for confirmation of scheduling a visit, urgent safety notifications); Willing to strictly follow the study protocol; Capacity for understanding and signing in the Informed Consent Form; To understand the impossibility of participating in another clinical trial during the time of participation in the study, until 6 months after its conclusion; Intellectual level which allows to filling in the diaries for registering of symptoms at home; Willing to undergo to serological testing to HIV, HBV and HCV; Being in good health, with no significant medical history; Physical examination at screening period without clinically significant changes; Lab examination at screening period within the normal ranges, determined by the laboratory or abnormal values, grading below 1 or 2, according to medical decision.", "candidate_expression": "((Age between 18 and 49 years old) AND (Being in good health, with no significant medical history;) AND (Capacity for understanding and signing in the Informed Consent Form;) AND (Intellectual level which allows to filling in the diaries for registering of symptoms at home;) AND (Lab examination at screening period within the normal ranges, determined by the laboratory or abnormal values, grading below 1 or 2, according to medical decision.) AND (Male) AND (Physical examination at screening period screening period) AND (Physical examination at screening period without clinically significant changes;) AND (To understand the impossibility of participating in another clinical trial during the time of participation in the study, until 6 months after its conclusion;) AND (Willing to provide name, address, telephone and other contact information in order to be contacted, whenever needed (example: in case of missing any scheduled visit, contact for confirmation of scheduling a visit, urgent safety notifications);) AND (Willing to strictly follow the study protocol;) AND (Willing to undergo to serological testing to HIV, HBV and HCV;) AND (good health) AND (serological testing to HBV) AND (serological testing to HCV) AND (serological testing to HIV))"}
{"candidate_id": "LLM00591", "doc_id": "NCT01709981_exc", "case_bucket": "or", "source_criterion": "Plan for diagnostic-only coronary angiography On colchicine chronically History of intolerance to colchicine Glomerular filtration rate <30mL/minute or on dialysis Active malignancy or infection History of myelodysplasia High-dose statin load <24 hours prior to procedure Use of oral steroids or non-steroidal anti-inflammatory agents other than aspirin within 72 hours or 3 times the agent's half-life (whichever is longer) Use of strong CYP3A4/P-glycoprotein inhibitors (specifically ritonavir, ketoconazole, clarithromycin, cyclosporine, diltiazem and verapamil) Unable to consent Participating in a competing study", "candidate_expression": "((3 times the agent's half-life) AND (72 hours) AND (<24 hours prior to procedure) AND (<30mL/minute) AND (Active) AND (High-dose statin) AND (aspirin) AND (chronically) AND (colchicine) AND (coronary angiography) AND (diagnostic-only) AND (intolerance) AND (myelodysplasia) AND (other than) AND (procedure) AND (strong CYP3A4/P-glycoprotein inhibitors) AND ((infection) OR (malignancy)) AND ((non-steroidal anti-inflammatory agents) OR (oral steroids)) AND ((within 3 times the agent's half-life) OR (within 72 hours)) AND ((clarithromycin) OR (cyclosporine) OR (diltiazem) OR (ketoconazole) OR (ritonavir) OR (verapamil)) AND ((Glomerular filtration rate) OR (dialysis)))"}
{"candidate_id": "LLM00592", "doc_id": "NCT02774317_exc", "case_bucket": "or", "source_criterion": "Patients who are being prepared for surgery, or during or after surgery. Patients with congenital anomalies, chromosomal anomalies, or heart defects. Patients whose parents refuse to consent.", "candidate_expression": "((being prepared for) AND ((after surgery) OR (during surgery) OR (surgery)) AND ((chromosomal anomalies) OR (congenital anomalies) OR (heart defects)))"}
{"candidate_id": "LLM00593", "doc_id": "NCT02974660_exc", "case_bucket": "or", "source_criterion": "no consent periprocedural complications requiring continuation of heparin or administration of protamine sulfate alergy to fish, protamine, protamine derivates, history of Humulin N, Novolin N, Novolin NPH, Gensulin N, SciLin N, NPH Iletin II and isophane insulin intake", "candidate_expression": "((no consent) AND (periprocedural complications) AND (requiring) AND ((Gensulin N) OR (Humulin N) OR (NPH Iletin II) OR (Novolin N) OR (Novolin NPH) OR (SciLin N) OR (isophane insulin)) AND ((heparin) OR (protamine sulfate)) AND ((alergy) OR (history)) AND ((fish) OR (protamine) OR (protamine derivates)))"}
{"candidate_id": "LLM00594", "doc_id": "NCT01669369_exc", "case_bucket": "or", "source_criterion": "a history of non-standard treatment(chemotherapy or surgery) secondary osteosarcoma or well-differentiated parosteal osteosarcoma evident dysfunction of cardia,liver and kidney, or pregnant women or women during lactation", "candidate_expression": "((chemotherapy) AND (dysfunction of cardia) AND (dysfunction of kidney) AND (dysfunction of liver) AND (history) AND (lactation) AND (non-standard treatment) AND (parosteal osteosarcoma well-differentiated) AND (pregnant) AND (secondary osteosarcoma) AND (surgery))"}
{"candidate_id": "LLM00595", "doc_id": "NCT01735955_inc", "case_bucket": "other", "source_criterion": "Patient is currently enrolled in a Novartis-sponsored, Oncology Clinical Development & Medical Affairs study receiving nilotinib and has fulfilled all their requirements in the parent study Patient is currently benefiting from the treatment with nilotinib, as determined by the investigator Patient has demonstrated compliance, as assessed by the investigator, with the parent study protocol requirements Willingness and ability to comply with scheduled visits, treatment plans and any other study procedures Written informed consent obtained prior to enrolling in roll-over study", "candidate_expression": "((Novartis-sponsored) AND (Willingness to comply with scheduled visits) AND (Willingness to comply with treatment plans) AND (Written informed consent) AND (ability to comply with scheduled visits) AND (compliance with the parent study protocol requirements) AND (currently) AND (enrolled in a Oncology Clinical Development & Medical Affairs study) AND (enrolling in roll-over study) AND (nilotinib) AND (prior to enrolling in roll-over study) AND (treatment))"}
{"candidate_id": "LLM00596", "doc_id": "NCT01491763_inc", "case_bucket": "or", "source_criterion": "Patients with Ph (BCR/ABL) positive de novo < 55 years old (it is advisable to include patients over 55 years LAL07OPH protocol). Performance status 0-2 (Appendix B) may include patients with performance status > 2 attributable to LAL. Patients without functional impairment of organs: liver function: total bilirubin, AST, ALT, alfa-GT and alkaline phosphatase less than 3 times the upper limit of normal laboratory renal function: serum creatinine < 2 mg/dL or clearance creatinine > 30 ml/min (except renal function attributable to LAL) cardiac function (Appendix B) normal: ventricular EF > 50%, absence of severe chronic respiratory disease. In the event that alterations are secondary to the disease is at the discretion of the investigator to determine if the patient can be included in the trial.", "candidate_expression": "((0-2) AND (< 2 mg/dL) AND (< 55 years) AND (> 30 ml/min) AND (> 50%) AND (ALT) AND (AST) AND (Performance status) AND (Ph (BCR/ABL)) AND (absence of) AND (alfa-GT) AND (alkaline phosphatase) AND (cardiac function) AND (clearance creatinine) AND (de novo) AND (functional impairment of organs) AND (less than 3 times the upper limit of normal) AND (normal) AND (old) AND (positive) AND (serum creatinine) AND (severe chronic respiratory disease) AND (total bilirubin) AND (ventricular EF) AND (without))"}
{"candidate_id": "LLM00597", "doc_id": "NCT01963754_inc", "case_bucket": "or", "source_criterion": "Single unit implant rehabilitation Maxilla and mandible Must accept treatment plan Must sign informed consent dental extraction performed at least 3 month prior Must have at least 6 mm of residual bone Absence of oral lesions keratinized tissue must be present", "candidate_expression": "((Must accept treatment plan) AND (Must sign informed consent) AND (Single unit implant rehabilitation) AND (dental extraction at least 3 month prior) AND (keratinized tissue must be present) AND (residual bone at least 6 mm) AND NOT (oral lesions) AND ((Maxilla) OR (mandible)))"}
{"candidate_id": "LLM00598", "doc_id": "NCT02105090_inc", "case_bucket": "or", "source_criterion": "elective procedure weight over 40 kg American Society of Anesthesiology class I-III first upper GI endoscopy procedure finnish or/and swedish speaking", "candidate_expression": "((American Society of Anesthesiology class I-III) AND (elective procedure) AND (endoscopy procedure first upper GI) AND (weight over 40 kg) AND ((finnish speaking) OR (swedish speaking)))"}
{"candidate_id": "LLM00599", "doc_id": "NCT03164096_inc", "case_bucket": "other", "source_criterion": "adult female partner aged 18 to 40 years. scheduled for elective cesarean section.", "candidate_expression": "((adult) AND (aged 18 to 40 years) AND (cesarean section scheduled for elective) AND (female) AND (female partner))"}
{"candidate_id": "LLM00600", "doc_id": "NCT02634541_inc", "case_bucket": "or", "source_criterion": "Axial spondyloarthritis (ASAS criteria) and radiologic sacroiliitis as detected either by MRI or X-ray.", "candidate_expression": "((ASAS criteria) AND (Axial spondyloarthritis) AND (MRI) AND (X-ray) AND (radiologic) AND (sacroiliitis))"}
```
